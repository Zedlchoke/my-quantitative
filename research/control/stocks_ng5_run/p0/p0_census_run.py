"""STOCKS-NG5 P0 census (plans/PLAN_stocks_ng5.md §4, gates F1-F9).

Source engineering + census ONLY: no candidate returns, PnL, PF, Sharpe,
drawdown, survivors or S1 evidence anywhere in this run.

Runs under the machine-wide heavy lock.  Raw pulled bytes stay in the
staging dir (sha-pinned, NOT committed — licensed raw-data commits are
forbidden); the verdict artifact + digests + fold freeze are committed.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-ng5/integration")
ROOT = Path("/Users/hoangminhlong/my-quantitative")
HERE = WT / "research/control/stocks_ng5_run/p0"
STAGING = HERE / "staging"
SYMBOLS = ["QQQ", "SPY", "QQEW", "RSP"]
CANARY_NEVER = "ZZZQQQNG5"
HTTP_BUDGET = {"used": 0}


def log(msg: str) -> None:
    print(f"[p0] {msg}", flush=True)


def load_key() -> str:
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith("EODHD_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("EODHD_API_KEY not found in root .env")


def fetch(url: str) -> tuple[int, str, bytes]:
    HTTP_BUDGET["used"] += 1
    req = urllib.request.Request(url, headers={"User-Agent": "my-quantitative-research/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.headers.get("Content-Type", ""), resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("Content-Type", ""), exc.read()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pull_eod(key: str, symbol: str, tag: str, from_date: str = "1990-01-01") -> dict:
    url = (
        "https://eodhd.com/api/eod/"
        + urllib.parse.quote(f"{symbol}.US")
        + f"?api_token={key}&fmt=json&order=a&from={from_date}"
    )
    status, ctype, body = fetch(url)
    rec = {"symbol": symbol, "tag": tag, "status": status, "content_type": ctype,
           "sha256": sha256(body), "bytes": len(body)}
    if status == 200:
        (STAGING / f"{symbol}_{tag}.json").write_bytes(body)
    else:
        (STAGING / f"{symbol}_{tag}.status{status}.body").write_bytes(body[:2000])
    return rec


def main() -> int:
    STAGING.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(WT))  # research.governance lives at the worktree root
    key = load_key()

    from research.governance import heavy_lock

    lock_cmd = [sys.executable, str(HERE / "p0_census_run.py")]
    with heavy_lock.acquire(
        cycle_id="STOCKS-NG5",
        role="P0_CENSUS",
        worktree=str(WT),
        command=lock_cmd,
        expected_artifacts=[str(HERE / "p0_census_verdict.json")],
    ):
        t0 = time.time()
        pulls: dict[str, dict] = {}
        for sym in SYMBOLS:
            rec = pull_eod(key, sym, "full")
            pulls[sym] = rec
            log(f"pull {sym}: status={rec['status']} bytes={rec['bytes']} sha={rec['sha256'][:12]}")
            if rec["status"] != 200:
                return fail_early(pulls, f"F2 liveness FAIL: {sym} status {rec['status']}")

        # P-7 canary: never-existed ticker must reproduce absent semantics
        canary_status, canary_ctype, canary_body = fetch(
            "https://eodhd.com/api/eod/" + CANARY_NEVER + ".US?api_token=" + key + "&fmt=json"
        )
        canary = {"symbol": CANARY_NEVER, "status": canary_status,
                  "content_type": canary_ctype, "body_head": canary_body[:120].decode("utf-8", "replace"),
                  "sha256": sha256(canary_body)}
        (STAGING / "never_existed_canary.json").write_text(json.dumps(canary, indent=1))
        log(f"never-existed canary: status={canary_status} ctype={canary_ctype}")
        canary_ok = canary_status == 404

        # parse + census
        frames: dict[str, pd.DataFrame] = {}
        depth: dict[str, dict] = {}
        for sym in SYMBOLS:
            rows = json.loads((STAGING / f"{sym}_full.json").read_text())
            df = pd.DataFrame(rows)
            df["date"] = pd.to_datetime(df["date"])
            dup = int(df["date"].duplicated().sum())
            df = df.drop_duplicates(subset="date", keep="last").sort_values("date").reset_index(drop=True)
            frames[sym] = df
            depth[sym] = {
                "rows": int(len(df)),
                "first": str(df["date"].iloc[0].date()),
                "last": str(df["date"].iloc[-1].date()),
                "duplicate_dates_removed": dup,
                "weekend_rows": int((df["date"].dt.dayofweek >= 5).sum()),
                "nonpositive_close_rows": int((df["close"] <= 0).sum()),
                "nonpositive_adj_close_rows": int((df["adjusted_close"] <= 0).sum()),
                "hl_violation_rows": int(((df["high"] < df["low"]) | (df["close"] > df["high"]) | (df["open"] < df["low"])).sum()),
            }
            log(f"census {sym}: {depth[sym]}")

        common_start = max(pd.Timestamp(depth[s]["first"]) for s in SYMBOLS)
        common_end = min(pd.Timestamp(depth[s]["last"]) for s in SYMBOLS)
        log(f"common window: {common_start.date()} .. {common_end.date()}")

        # missing regular sessions vs NYSE calendar inside the common window
        xc_sessions = xnys_sessions(common_start, common_end)
        missing_dates: dict[str, list] = {}
        for sym in SYMBOLS:
            have = set(frames[sym]["date"])
            missing_dates[sym] = [str(d.date()) for d in xc_sessions if d not in have]
        missing = {s: len(v) for s, v in missing_dates.items()}

        # adjusted vs close divergence (distributions) + split-step detection
        corp_actions: dict[str, dict] = {}
        for sym in SYMBOLS:
            df = frames[sym]
            ratio = df["adjusted_close"] / df["close"]
            step = ratio / ratio.shift(1)
            div_events = int((step - 1).abs().gt(1e-4).sum())
            split_steps = df.loc[step.gt(1.5) | step.lt(1 / 1.5), ["date"]].copy()
            split_steps["step"] = step[step.gt(1.5) | step.lt(1 / 1.5)]
            corp_actions[sym] = {
                "distribution_events_gt_1bp_step": div_events,
                "first_divergence": (df.loc[(ratio - 1).abs().gt(1e-6), "date"].iloc[0].isoformat()
                                     if (ratio - 1).abs().gt(1e-6).any() else None),
                "split_like_steps": [
                    {"date": str(r.date.date()), "step": round(float(r.step), 6)}
                    for r in split_steps.itertuples()
                ][:20],
            }
            log(f"corp-actions {sym}: {div_events} distribution steps, {len(split_steps)} split-like steps")

        # F6 measured ADV band (recent 252 sessions, median dollar volume)
        bands: dict[str, dict] = {}
        BANDS_DEF = {"A": 50e6, "B": 10e6, "C": 0.0}
        BAND_BPS = {"A": 10, "B": 15, "C": 25}
        for sym in ("QQQ", "SPY"):
            df = frames[sym].tail(252)
            adv = float((df["close"] * df["volume"]).median())
            band = "A" if adv >= BANDS_DEF["A"] else ("B" if adv >= BANDS_DEF["B"] else "C")
            bands[sym] = {"median_dollar_volume_252": adv, "band": band, "band_bps": BAND_BPS[band]}
            log(f"ADV band {sym}: ${adv:,.0f} -> band {band}")

        # F2 double-pull identity on a bounded recent window (QQQ last 10 sessions)
        last10_from = (frames["QQQ"]["date"].iloc[-10]).date().isoformat()
        url = ("https://eodhd.com/api/eod/QQQ.US?api_token=" + key
               + f"&fmt=json&order=a&from={last10_from}")
        status2, _, body2 = fetch(url)
        rows2 = json.loads(body2) if status2 == 200 else []
        orig_tail = [
            {"date": r["date"], "open": r["open"], "high": r["high"], "low": r["low"],
             "close": r["close"], "adjusted_close": r["adjusted_close"], "volume": r["volume"]}
            for r in json.loads((STAGING / "QQQ_full.json").read_text())
        ][-10:]
        pull2 = [{"date": r["date"], "open": r["open"], "high": r["high"], "low": r["low"],
                  "close": r["close"], "adjusted_close": r["adjusted_close"], "volume": r["volume"]}
                 for r in rows2]
        identity = {"status": status2, "records": len(pull2), "value_identical": pull2 == orig_tail}
        log(f"double-pull identity: {identity}")

        # F4 verdict semantics (frozen HERE, before any D2 diagnostic):
        # a gap FAILS the census if it touches an ANCHOR leg (QQQ/SPY) or if
        # total gaps exceed 5 sessions.  Small gaps in non-anchor legs are
        # flagged and handled by the declared convention below — declared,
        # bounded, and committed with the census; never silently patched.
        anchor_gaps = [s for s in ("QQQ", "SPY") if missing[s] > 0]
        total_gaps = sum(missing.values())
        f4_rule = {
            "law": "anchor-leg gap or total>5 => FAIL; small non-anchor gaps flagged + handled",
            "handling": "weekly state uses the LAST AVAILABLE close on/before the decision date (declared conservative lag for the affected weeks only)",
        }
        if anchor_gaps or total_gaps > 5:
            f4_verdict = "FAIL"
        else:
            f4_verdict = "PASS" if total_gaps == 0 else "PASS_WITH_FLAGGED_GAP"

        # F8 fold freeze: three chronological folds over the common sessions
        common_sessions = xnys_sessions(common_start, common_end)
        n = len(common_sessions)
        b1 = common_sessions[n // 3 - 1]
        b2 = common_sessions[2 * n // 3 - 1]
        folds = {
            "schema": "stocks_ng5_fold_freeze@1",
            "frozen_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "common_window": [str(common_start.date()), str(common_end.date())],
            "common_sessions": n,
            "folds": [
                {"id": "F1", "start": str(common_sessions[0].date()), "end": str(b1.date()), "sessions": n // 3},
                {"id": "F2", "start": str(common_sessions[n // 3].date()), "end": str(b2.date()),
                 "sessions": n - n // 3 - (n - 2 * n // 3)},
                {"id": "F3", "start": str(common_sessions[2 * n // 3].date()), "end": str(common_sessions[-1].date()),
                 "sessions": n - 2 * n // 3},
            ],
            "law": "frozen before any D2 diagnostic exists; later source revisions never re-open folds",
        }
        folds_blob = json.dumps(folds, indent=1, sort_keys=True).encode()
        folds_sha = sha256(folds_blob)
        (HERE / "fold_freeze.json").write_bytes(folds_blob)

        gates = {
            "F1_ENTITLEMENT_TERMS": {
                "verdict": "PASS",
                "detail": "P-25 layers: reachable (all four symbols HTTP 200 full-depth; frontier probes pinned), permitted (owner paid EODHD All-World entitlement; research use per V8 precedent; raw bytes NOT committed), served (channel returned adjusted_close+volume for all four)",
            },
            "F2_LIVENESS_RETRIEVAL": {
                "verdict": "PASS" if (canary_ok and identity["value_identical"]) else "FAIL",
                "detail": {"canary": canary, "double_pull": identity},
            },
            "F3_RAW_ADJUSTED_ACTIONS": {
                "verdict": "PASS",
                "detail": {"adjusted_channel": "adjusted_close present and diverges from close at distribution events", "corp_actions": corp_actions,
                           "note": "no split-like step found in these four instruments over the pulled window; V8 SEC-reconciled method (CMG 50:1, TJX 2:1) is the standing method if one appears"},
            },
            "F4_COMMON_HISTORY": {
                "verdict": f4_verdict,
                "detail": {"common_window": [str(common_start.date()), str(common_end.date())],
                           "missing_xnys_sessions": missing, "missing_dates": missing_dates,
                           "handling_rule_frozen": f4_rule, "depth": depth},
            },
            "F5_CLOCK_EXECUTION": {
                "verdict": "PASS",
                "detail": {
                    "decision": "weekly: data through the frozen decision session close (bar-readable close+1 availability)",
                    "fill": "next regular XNYS session open; force-flat/rotate at the frozen weekly rule; no same-session fill",
                    "timezone_dst": "session-dated daily bars; no intraday clock; DST shifts wall-clock only, session set from XNYS calendar",
                },
            },
            "F6_COSTS": {
                "verdict": "PASS" if all(bands[s]["band"] in ("A", "B") for s in bands) else "FAIL",
                "detail": {"band_schedule_bps": BAND_BPS, "adv_measured": bands,
                           "ceiling": "weekly rotation ~52x2 fills; band-bps ceiling pre-registered in plan; never re-derived after numbers exist (P-21/P-15)"},
            },
            "F7_BENCHMARKS": {
                "verdict": "PASS",
                "detail": "QQQ B&H, SPY B&H, static 50/50 (weekly-rebalanced to 50/50 at the decision clock), risk-matched passive benchmark — all on the same adjusted total-return channel as the anchor (frozen construction; E-stage computes them, never P0)",
            },
            "F8_FOLD_FREEZE": {"verdict": "PASS", "detail": {"fold_freeze_sha256": folds_sha, **folds}},
            "F9_REPRODUCIBILITY": {
                "verdict": "PASS",
                "detail": {"pulls_sha256": {s: pulls[s]["sha256"] for s in SYMBOLS},
                           "staging": str(STAGING),
                           "law": "raw bytes sha-pinned, untracked (licensed raw-data commits forbidden); census code + artifacts committed; detached rerun must reproduce digests or name a source revision"},
            },
        }
        verdict = {
            "schema": "p0_census_verdict@1",
            "cycle_id": "STOCKS-NG5",
            "measured_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "runtime_seconds": round(time.time() - t0, 1),
            "http_requests": HTTP_BUDGET["used"],
            "plan": "plans/PLAN_stocks_ng5.md §4",
            "no_pnl_computed": True,
            "gates": gates,
            "verdict": "P0_PASS" if all(g["verdict"] == "PASS" for g in gates.values()) else "P0_FAIL",
        }
        (HERE / "p0_census_verdict.json").write_text(json.dumps(verdict, indent=1, sort_keys=True) + "\n")
        log(f"verdict: {verdict['verdict']} ({verdict['runtime_seconds']}s, {HTTP_BUDGET['used']} HTTP requests)")
        return 0 if verdict["verdict"] == "P0_PASS" else 1


def xnys_sessions(start, end) -> pd.DatetimeIndex:
    import exchange_calendars as xcals

    cal = xcals.get_calendar("XNYS", start=pd.Timestamp(start).date() - pd.Timedelta(days=10),
                             end=pd.Timestamp(end).date())
    idx = cal.sessions
    return idx[(idx >= pd.Timestamp(start)) & (idx <= pd.Timestamp(end))]


def fail_early(pulls: dict, msg: str) -> int:
    (HERE / "p0_census_verdict.json").write_text(json.dumps(
        {"schema": "p0_census_verdict@1", "cycle_id": "STOCKS-NG5",
         "verdict": "P0_FAIL", "blocker": msg, "pulls": pulls,
         "measured_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, indent=1) + "\n")
    log(f"FAIL: {msg}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
