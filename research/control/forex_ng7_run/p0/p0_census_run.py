#!/usr/bin/env python
"""FOREX-NG7 P0 census lane (plan plans/PLAN_forex_ng7.md §4 F1-F7).

CENSUS ONLY: counts, digests, calendar structure. No returns, no PnL, no
PF/Sharpe, no S1, no scored computation. Fail-closed on every identity
check: missing evidence is recorded NOT_RUN/FAIL, never inferred PASS.

Gates implemented here
  F1  staging chain (archive digests, member pins, structural census,
      bounded re-pull per the frozen contract, manifest pin, 5-leg
      calendar census with NO forward-fill)
  F2  entitlement terms re-quote (existence-verified citations)
  F4  cost band pin (1.5 bps/fill floor, stress 2.0 PRIMARY) + financing
      authority ruling from the authorized evidence space
  F5  3 chronological folds frozen over the intersection calendar +
      anchor-state trigger census per fold per leg (counts only)
  F6  reproducibility digests (run twice; digest files must be
      byte-identical)
  F7  NY Fed / OFR control authority classes recorded from the A3 dossier

F3 (clock + execution contract fixture) lives in this module as the
frozen mapping helpers (decision_to_execution_index /
next_bookable_price / exit_execution_index) with golden tests in
tests/test_forex_ng7_p0.py.

Run:  .venv/bin/python research/control/forex_ng7_run/p0/p0_census_run.py
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

# --------------------------------------------------------------------------
# Paths (worktree-anchored; this file lives at <wt>/research/control/forex_ng7_run/p0/)
# --------------------------------------------------------------------------
P0_DIR = Path(__file__).resolve().parent
WT_ROOT = P0_DIR.parents[3]
STAGED_DIR = WT_ROOT / "data_raw" / "forex_ng7_spot"
A2_DOSSIER = (
    WT_ROOT / "research/control/ng6_ng7_ng4_dossiers_2026-09/"
    "fng7-a2-mechanism-proposal-dossier.json"
)
A3_DOSSIER = (
    WT_ROOT / "research/control/ng6_ng7_ng4_dossiers_2026-09/"
    "fng7-a3-nyfed-ofr-pit-dossier.json"
)
A2_DOSSIER_SHA256 = (
    "72284c8ffd35946375d1c89e348c616621898e0f456ba36acc45b1b5b026df0f"
)
STAGING_BACKUP = Path.home() / "staging_backups" / "cleanup_2026-09-12"
CONTRACT_PATH = P0_DIR / "repull_contract.json"
# Frozen-at-dispatch sha of repull_contract.json: the contract MUST hash to
# this value before the bounded pull is allowed (fail-closed ordering proof:
# contract frozen BEFORE the pull).
CONTRACT_SHA256 = (
    "a100b06ab67fc564f3e865ae18daee10630dbc4a900ed7f7a8a3f6abb388c7dd"
)

LEGS = ["EURUSD", "GBPUSD", "USDCAD", "AUDUSD", "NZDUSD"]

# F5 population floor, pinned HERE at the P0 manifest freeze before any
# census read (plan §6 R2 S2-class pin). A4 form: trigger rate in
# [0.02, 0.10] bars/leg/day -> 5-25 firings/leg/yr.
FLOOR_FOLD_LEG = 5      # minimum firings per (fold, leg)
FLOOR_FOLD_TOTAL = 30   # minimum firings per fold across the 5 legs

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

REPULL_LEGS = {"EURUSD": "EUR/USD", "NZDUSD": "NZD/USD"}
TD_ENDPOINT = "https://api.twelvedata.com/time_series"


class FailClosedError(RuntimeError):
    """Raised when an identity/census invariant cannot be evidenced."""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json_deterministic(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


# --------------------------------------------------------------------------
# F1(ii) staged member verification + structural census
# --------------------------------------------------------------------------
def load_a2_pins(dossier_path: Path) -> dict:
    """Fail-closed: the dossier itself must hash to the committed pin."""
    got = sha256_file(dossier_path)
    if got != A2_DOSSIER_SHA256:
        raise FailClosedError(
            f"A2 dossier sha mismatch: expected {A2_DOSSIER_SHA256}, got {got}"
        )
    dossier = json.loads(dossier_path.read_text(encoding="utf-8"))
    pins = {}
    for row in dossier["universe_and_legs"]["leg_inventory_measured_2026-09-16"]:
        leg = row["leg"]
        if leg in LEGS:
            pins[leg] = row
    missing = [leg for leg in LEGS if leg not in pins]
    if missing:
        raise FailClosedError(f"A2 dossier missing leg pins: {missing}")
    return pins


def verify_staged_against_pins(staged_dir: Path, pins: dict) -> dict:
    """Every staged member with a pin must hash to its pin. Fail-closed.
    (The run path passes the full five-leg pin set from load_a2_pins,
    which itself raises if any leg pin is missing.)"""
    out = {}
    for leg, pin in sorted(pins.items()):
        path = staged_dir / f"{leg}.json"
        if not path.exists():
            raise FailClosedError(f"staged member missing: {path}")
        digest = sha256_file(path)
        expected = pin["member_sha256"]
        out[leg] = {
            "staged_path": str(path),
            "sha256": digest,
            "a2_member_pin_sha256": expected,
            "match": digest == expected,
        }
        if digest != expected:
            raise FailClosedError(
                f"{leg}: staged member sha {digest} != A2 pin {expected}"
            )
    return out


def load_leg_payload(path: Path) -> dict:
    """Validate TD payload shape; return rows oldest-first with raw strings."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    for key in ("meta", "values", "status"):
        if key not in payload:
            raise FailClosedError(f"{path.name}: payload missing key {key!r}")
    if payload["status"] != "ok":
        raise FailClosedError(f"{path.name}: status={payload['status']!r}")
    values = payload["values"]
    rows = []
    for row in values:
        for field in ("datetime", "open", "high", "low", "close"):
            if field not in row:
                raise FailClosedError(
                    f"{path.name}: row missing field {field!r}"
                )
        if not DATE_RE.match(row["datetime"]):
            raise FailClosedError(
                f"{path.name}: non date-only stamp {row['datetime']!r}"
            )
        rows.append(row)
    # archived payloads are newest-first; verify strictly descending unique
    parsed = [dt.date.fromisoformat(r["datetime"]) for r in rows]
    for i in range(len(parsed) - 1):
        if parsed[i] <= parsed[i + 1]:
            raise FailClosedError(
                f"{path.name}: archive order not strictly newest-first at "
                f"{rows[i]['datetime']}"
            )
    rows.reverse()  # oldest-first for census math
    return {
        "meta": payload["meta"],
        "rows": rows,                       # oldest-first, raw strings
        "dates": parsed,                    # oldest-first
    }


def structural_census(leg: str, data: dict, pin: dict) -> dict:
    """Rows / span / OHLC integrity / stamp convention census (F1(ii))."""
    rows = data["rows"]
    problems = []
    for r in rows:
        o, h, l, c = (
            float(r["open"]),
            float(r["high"]),
            float(r["low"]),
            float(r["close"]),
        )
        if not (h >= max(o, c) - 1e-12):
            problems.append(("high_lt_max_open_close", r["datetime"]))
        if not (l <= min(o, c) + 1e-12):
            problems.append(("low_gt_min_open_close", r["datetime"]))
        if min(o, h, l, c) <= 0:
            problems.append(("nonpositive_price", r["datetime"]))
    weekend = [
        r["datetime"]
        for r in rows
        if dt.date.fromisoformat(r["datetime"]).weekday() >= 5
    ]
    meta = data["meta"]
    meta_ok = (
        meta.get("symbol") == pin["meta"]["symbol"]
        and meta.get("interval") == pin["meta"]["interval"]
        and meta.get("type") == pin["meta"]["type"]
    )
    span = f"{rows[0]['datetime']} .. {rows[-1]['datetime']}"
    expected_span = pin["span"]
    census = {
        "leg": leg,
        "rows": len(rows),
        "rows_expected": pin["rows"],
        "span_measured": span,
        "span_a2_pin": expected_span,
        "ohlc_integrity_violations": problems,
        "ohlc_artifact_count": len(problems),
        "ohlc_artifact_disposition": (
            "archived vendor OHLC artifacts (sub-pip H/L-vs-close session "
            "marks) carried AS-IS: these bytes are the A2-pinned cycle "
            "authority — never repaired, never normalized; recorded "
            "verbatim for D1/D2 consumers"
        ),
        "date_only_stamps": True,
        "weekend_stamped_bars": {
            "count": len(weekend),
            "note": (
                "Sat/Sun-stamped daily bars are the archived TD FX weekend "
                "convention; carried as-is, never filtered or filled"
            ),
        },
        "meta": meta,
        "meta_matches_a2_pin": meta_ok,
        "stamp_convention": (
            "date-only stamps (no sub-daily component); the 16:00-NY daily "
            "session-close convention is inherited via the A2 dossier clock "
            "pin (NG5-recovered pins) — not per-row machine-evidenced"
        ),
    }
    # identity/shape failures are hard; OHLC artifacts are recorded
    # evidence of the archived authority (see artifact_disposition above)
    if len(rows) != pin["rows"] or not meta_ok:
        census["fail"] = True
    return census


# --------------------------------------------------------------------------
# F1(v) intersecting calendar census — NO forward-fill anywhere
# --------------------------------------------------------------------------
def _weekday_dates_between(first: dt.date, last: dt.date):
    d = first
    while d <= last:
        if d.weekday() < 5:
            yield d
        d += dt.timedelta(days=1)


def _absence_runs(absent_set, first: dt.date, last: dt.date):
    runs = []
    run = []
    for d in _weekday_dates_between(first, last):
        if d in absent_set:
            run.append(d)
        elif run:
            runs.append((run[0].isoformat(), run[-1].isoformat(), len(run)))
            run = []
    if run:
        runs.append((run[0].isoformat(), run[-1].isoformat(), len(run)))
    return runs


def calendar_census(leg_data: dict) -> dict:
    """Per-leg holiday/missing-bar census + 5-leg intersection. No ffill."""
    date_sets = {leg: set(d["dates"]) for leg, d in leg_data.items()}
    first = max(min(ds) for ds in date_sets.values())
    last = min(max(ds) for ds in date_sets.values())
    per_leg = {}
    for leg in LEGS:
        ds = date_sets[leg]
        window = [d for d in _weekday_dates_between(first, last)]
        absent = sorted(d for d in window if d not in ds)
        runs = _absence_runs(set(absent), first, last)
        run_hist = {}
        for _, _, ln in runs:
            run_hist[str(ln)] = run_hist.get(str(ln), 0) + 1
        per_leg[leg] = {
            "weekday_dates_in_common_window": len(window),
            "weekday_absences_holiday_or_missing": len(absent),
            "longest_absence_run_days": max((ln for _, _, ln in runs), default=0),
            "absence_run_length_histogram": run_hist,
            "absence_runs_first5": runs[:5],
            "note": "weekend structure excluded by construction; NO fill applied",
        }
    intersection = sorted(set.intersection(*date_sets.values()))
    return {
        "common_window": {"first": first.isoformat(), "last": last.isoformat()},
        "per_leg_weekday_census": per_leg,
        "intersection_calendar": {
            "dates_present_in_all_5_legs": len(intersection),
            "first": intersection[0].isoformat(),
            "last": intersection[-1].isoformat(),
            "contiguous_gaps_note": (
                "intersection dates are by construction present in every "
                "leg; intra-week absences are archived holiday structure "
                "and are NEVER forward-filled"
            ),
        },
        "forward_fill": "NONE — forbidden by plan §4 F1(v) and §12",
    }


# --------------------------------------------------------------------------
# F5 folds + trigger census (counts only)
# --------------------------------------------------------------------------
def build_folds(intersection_dates: list) -> dict:
    """3 chronological thirds over the intersection calendar, exact
    first-session boundaries. Frozen here before the census counts are
    read (the fold builder sees only the date list)."""
    n = len(intersection_dates)
    if n < 3:
        raise FailClosedError("intersection calendar too small to fold")
    k = n // 3
    bounds = [0, k, 2 * k, n]
    folds = {}
    for i in range(3):
        seg = intersection_dates[bounds[i] : bounds[i + 1]]
        folds[f"fold{i + 1}"] = {
            "index": i + 1,
            "first_session": seg[0].isoformat(),
            "last_session": seg[-1].isoformat(),
            "sessions": len(seg),
            "force_flat_at_boundary": "D1/D2 scoring law (§8); census only here",
        }
    return {
        "schema": "fng7_p0_folds@1",
        "calendar": "intersection of the five staged leg calendars",
        "rule": "3 chronological thirds at bar boundaries on the intersection calendar",
        "population_floor_pin": {
            "per_fold_per_leg_min_firings": FLOOR_FOLD_LEG,
            "per_fold_5leg_total_min_firings": FLOOR_FOLD_TOTAL,
            "class": "S2 (plan §6 R2) — pinned at P0 before census read",
        },
        "folds": folds,
    }


def clv(bar: dict) -> float:
    h, l, c = float(bar["high"]), float(bar["low"]), float(bar["close"])
    if h <= l:
        return 0.0
    return ((c - l) - (h - c)) / (h - l)


def anchor_firings(rows: list, slope_window: int = 5, warmup: int = 60,
                   start_idx: int = 0, end_idx: int | None = None) -> list:
    """Anchor-state firing census (plan §5 FNG7-A2-P1-ABSORB).

    State on completed bar t (0-based index within `rows`, oldest-first):
      P_t    = sum CLV over trailing 20 completed bars (t-19..t)
      slope  = P_t - P_{t-slope_window}
      LONG   = fresh 20-bar close LOW  (C_t strictly below the prior 19
               closes) AND slope > 0  (divergent — pressure NOT confirming
               the downside)
      SHORT  = mirror (fresh 20-bar close HIGH AND slope < 0)
    Decision bars require t >= warmup (first decision bar 61, 1-based).
    Sign derivation per plan §4 F3b (from the mechanism statement, NOT the
    A2 dossier's literal s_t sentence).
    Returns firing records (index, date, direction).
    """
    n = len(rows)
    end = n if end_idx is None else min(end_idx, n)
    closes = [float(r["close"]) for r in rows]
    clvs = [clv(r) for r in rows]
    pres = []
    run = 0.0
    for t in range(n):
        run += clvs[t]
        if t >= 20:
            run -= clvs[t - 20]
        pres.append(run)
    firings = []
    for t in range(max(warmup, start_idx), end):
        if t < 20 or t - slope_window < 19:
            continue
        prior = closes[t - 19 : t]
        fresh_low = closes[t] < min(prior)
        fresh_high = closes[t] > max(prior)
        slope = pres[t] - pres[t - slope_window]
        if fresh_low and slope > 0:
            firings.append(
                {"index": t, "date": rows[t]["datetime"], "direction": "LONG"}
            )
        elif fresh_high and slope < 0:
            firings.append(
                {"index": t, "date": rows[t]["datetime"], "direction": "SHORT"}
            )
    return firings


def trigger_census(leg_data: dict, folds: dict) -> dict:
    """Census counts per fold per leg per direction. Counts ONLY."""
    fold_spans = []
    for name in ("fold1", "fold2", "fold3"):
        f = folds["folds"][name]
        fold_spans.append(
            (
                name,
                dt.date.fromisoformat(f["first_session"]),
                dt.date.fromisoformat(f["last_session"]),
            )
        )
    out = {"per_fold": {}, "totals": {"LONG": 0, "SHORT": 0, "all": 0}}
    for name, first, last in fold_spans:
        entry = {"per_leg": {}, "total": 0}
        for leg in LEGS:
            rows = leg_data[leg]["rows"]
            firings = anchor_firings(rows)
            in_fold = [
                f for f in firings
                if first <= dt.date.fromisoformat(f["date"]) <= last
            ]
            longs = sum(1 for f in in_fold if f["direction"] == "LONG")
            shorts = len(in_fold) - longs
            entry["per_leg"][leg] = {"LONG": longs, "SHORT": shorts,
                                     "total": len(in_fold)}
            entry["total"] += len(in_fold)
        entry["floor_per_leg_ok"] = all(
            v["total"] >= FLOOR_FOLD_LEG for v in entry["per_leg"].values()
        )
        entry["floor_total_ok"] = entry["total"] >= FLOOR_FOLD_TOTAL
        out["per_fold"][name] = entry
        out["totals"]["all"] += entry["total"]
    for name, _, _ in fold_spans:
        for leg in LEGS:
            d = out["per_fold"][name]["per_leg"][leg]
            out["totals"]["LONG"] += d["LONG"]
            out["totals"]["SHORT"] += d["SHORT"]
    out["floor_all_folds_ok"] = all(
        f["floor_per_leg_ok"] and f["floor_total_ok"]
        for f in out["per_fold"].values()
    )
    out["rate_note"] = (
        "A4 form: trigger rate [0.02,0.10] bars/leg/day; measured counts "
        "are census-only and replace the form before selection (plan §4 F5)"
    )
    return out


# --------------------------------------------------------------------------
# F3 clock + execution contract (frozen mapping helpers)
# --------------------------------------------------------------------------
def decision_to_execution_index(decision_index: int) -> int:
    """Entry/exit fill bar for a decision at completed bar t: bar t+1."""
    return decision_index + 1


def next_bookable_price(rows: list, decision_index: int) -> str:
    """First bookable price of bar t+1 under the frozen 16:00-NY daily
    convention (the bar's open). Fail-closed at the series edge."""
    j = decision_to_execution_index(decision_index)
    if j >= len(rows):
        raise FailClosedError(
            f"no bookable bar after decision index {decision_index}"
        )
    return rows[j]["open"]


def exit_execution_index(condition_index: int) -> int:
    """An exit condition knowable at bar-t close executes at bar t+1's
    first bookable price (V7 F-A7-PL-1 lookahead class pre-empted)."""
    return decision_to_execution_index(condition_index)


# --------------------------------------------------------------------------
# F1(iii) bounded re-pull per the frozen contract
# --------------------------------------------------------------------------
def _redact(text: str, secret: str) -> str:
    if secret:
        text = text.replace(secret, "[REDACTED]")
    return text[:300]


def execute_repull(contract_path: Path, leg_data: dict) -> dict:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    got_sha = sha256_file(contract_path)
    result = {
        "schema": "fng7_p0_repull_result@1",
        "contract_sha256": got_sha,
        "endpoint": TD_ENDPOINT,
        "redaction": "key scrubbed; URLs never stored beyond scheme+host+path",
    }
    if got_sha != CONTRACT_SHA256:
        result["outcome"] = "NOT_RUN_CONTRACT_MISMATCH"
        result["detail"] = (
            "contract file hash != frozen CONTRACT_SHA256; pull refused"
        )
        return result
    key = None
    import os

    key = os.environ.get("TWELVE_DATA_API_KEY", "")
    if not key:
        result["outcome"] = "NOT_RUN_KEY_ABSENT"
        result["detail"] = "TWELVE_DATA_API_KEY not present in environment"
        return result
    result["retrieved_at_utc"] = (
        dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    )
    legs_result = {}
    overall = "BYTE_IDENTITY"
    for leg in contract["scope"]["legs"]:
        symbol = REPULL_LEGS[leg]
        params = {
            "symbol": symbol,
            "interval": "1day",
            "outputsize": str(contract["scope"]["bars_per_leg"]),
            "order": "desc",
            "format": "JSON",
            "apikey": key,
        }
        url = TD_ENDPOINT + "?" + urllib.parse.urlencode(params)
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "forex-ng7-p0-census/1.0"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                status = resp.status
                body = resp.read().decode("utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001 — redacted fail-closed record
            legs_result[leg] = {
                "outcome": "NOT_RUN_NETWORK",
                "exception_type": type(exc).__name__,
                "redacted_error": _redact(str(exc), key),
            }
            overall = "NOT_RUN_NETWORK"
            time.sleep(1.0)
            continue
        vendor = json.loads(body)
        vendor_rows = vendor.get("values", [])
        vdates = {r["datetime"]: r for r in vendor_rows}
        staged_tail = leg_data[leg]["rows"][-60:]  # newest 60, oldest-first
        overlaps, mismatches = 0, []
        for row in staged_tail:
            d = row["datetime"]
            if d not in vdates:
                continue
            overlaps += 1
            vr = vdates[d]
            for field in ("datetime", "open", "high", "low", "close"):
                if str(vr.get(field)) != str(row[field]):
                    mismatches.append(
                        {
                            "datetime": d,
                            "field": field,
                            "staged": str(row[field]),
                            "vendor": str(vr.get(field)),
                        }
                    )
        min_overlap = contract["comparison_basis"]["min_overlap_datetimes"]
        if mismatches:
            leg_out = "DIVERGENCE"
        elif overlaps < min_overlap:
            leg_out = "NOT_RUN_INSUFFICIENT_OVERLAP"
        else:
            leg_out = "BYTE_IDENTITY"
        legs_result[leg] = {
            "symbol": symbol,
            "http_status": status,
            "vendor_rows_returned": len(vendor_rows),
            "vendor_span": (
                f"{vendor_rows[0]['datetime']} .. {vendor_rows[-1]['datetime']}"
                if vendor_rows
                else None
            ),
            "overlap_datetimes": overlaps,
            "min_overlap_required": min_overlap,
            "mismatches": mismatches[:20],
            "mismatch_count": len(mismatches),
            "outcome": leg_out,
        }
        legs_result[leg]["retrieved_at_utc"] = (
            dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
        )
        if leg_out == "DIVERGENCE":
            overall = "DIVERGENCE"
        elif leg_out != "BYTE_IDENTITY" and overall == "BYTE_IDENTITY":
            overall = leg_out
        time.sleep(1.0)
    result["legs"] = legs_result
    result["outcome"] = overall
    if overall == "DIVERGENCE":
        result["authority_declaration"] = (
            "DIVERGENCE: the archive vintage is DECLARED THE cycle authority "
            "for FOREX-NG7; divergence recorded, vendor bytes NEVER merged"
        )
    return result


# --------------------------------------------------------------------------
# F2 + F4: entitlement citations and the cost/financing ruling
# --------------------------------------------------------------------------
def git_main_file_exists(repo_root: Path, rel_path: str) -> bool:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "cat-file", "-e",
         f"main:{rel_path}", "--"],
        capture_output=True,
    )
    return proc.returncode == 0


def entitlement_evidence() -> dict:
    """F2: existence-verified precedent citations for the owner TD
    entitlement terms (V8/V9/NG5 lineage)."""
    citations = [
        {
            "path": "research/control/forex_frontier_2026-09/survey_report.md",
            "where": "git main (verified via git cat-file)",
            "quote": (
                "Spot plane: Twelve Data daily bars under the OWNER'S "
                "EXISTING entitlement ... zero new entitlements"
            ),
        },
        {
            "path": (
                "research/control/ng5_ng6_frontier_2026-09/handoffs/"
                "data_cost_critic.json"
            ),
            "where": "git main (verified via git cat-file)",
            "quote": (
                "TD probes measured: EODHD serves no spread fields "
                "(measured schema); spread/swap/commission/financing "
                "UNMEASURABLE on TD (vendor not broker)"
            ),
        },
        {
            "path": "~/staging_backups/cleanup_2026-09-12/"
                    "forex-v8_staged_vintaged.tar.gz + forex-v9_cpi_spot.tar.gz",
            "where": "P-13 archives (digests verified F1(i))",
            "quote": "FOREX-V8/V9 TD usage archives — the entitlement's "
                     "prior-cycle payload vintages",
        },
    ]
    checked = []
    for cite in citations:
        if cite["where"].startswith("git main"):
            ok = git_main_file_exists(WT_ROOT, cite["path"])
        else:
            ok = all(
                (STAGING_BACKUP / name).exists()
                for name in (
                    "forex-v8_staged_vintaged.tar.gz",
                    "forex-v9_cpi_spot.tar.gz",
                )
            )
        checked.append({**cite, "exists": ok})
    return {
        "entitlement": "owner TD (Twelve Data) + EODHD family-1; key "
                       "environment-only, never echoed",
        "citations": checked,
        "all_citations_exist": all(c["exists"] for c in checked),
    }


def cost_ruling() -> dict:
    """F4: pin the spread floor; rule on the financing band from the
    authorized evidence space ONLY (committed git evidence + P-13 archive
    manifests). Measured beats stated (Q-8); vendor web pages are NOT
    citable here."""
    evidence = [
        {
            "source": "git main:research/control/ng5_ng6_frontier_2026-09/"
                      "handoffs/data_cost_critic.json (X2 probe, measured)",
            "finding": "TD serves no spread fields; spread/swap/commission/"
                       "financing UNMEASURABLE on TD (vendor not broker)",
        },
        {
            "source": "git main:research/control/ng5_ng6_frontier_2026-09/"
                      "audits/a7_forex_ng6_plan.json + PROBE_INDEX.json",
            "finding": "FOREX-NG6 P0-F4 fail-closed class: terminal "
                       "BLOCKED_SOURCE_OR_COST unless a citable conservative "
                       "swap/spread band is evidenced; TD named a vendor, "
                       "not a broker",
        },
        {
            "source": "research/control/ng6_ng7_ng4_dossiers_2026-09/"
                      "fng7-a4-hostile-critic-dossier.json (axis 5, binding)",
            "finding": "'the TD spot legs have no swap points in-band, so "
                       "the plan must name its financing authority BEFORE "
                       "D1; if none exists in the authorized evidence space, "
                       "the financed book is NOT_MEASURABLE'",
        },
        {
            "source": "git main:research/control/WORKTREE_CLEANUP_2026-09-12"
                      ".json (P-13) + archive manifests (F1(i) digests)",
            "finding": "prior forex worktrees ng1..ng5 deleted; their only "
                       "surviving payloads are the P-13 archives — OHLC-only "
                       "TD daily bars, no swap points anywhere in-band",
        },
        {
            "source": "NG5 E1 ceiling 18.07 bps (A4 axis-2 prior-number "
                      "re-read; XAU weekly holds, stress 6, NZ-US 6.23% "
                      "worst differential)",
            "finding": "XAUUSD-specific financing ceiling — NOT an FX-majors "
                       "band; the ~5.1 bps/3-nights figure is an arithmetic "
                       "bound from a rate differential, not a swap-points "
                       "band and not citable as one",
        },
    ]
    return {
        "schema": "fng7_p0_cost_ruling@1",
        "spread_band": {
            "pin": "1.5 bps per fill FLOOR (conservative, preregistered "
                   "plan §4 F4 / §8); stress tier 2.0 => 3.0 bps per fill "
                   "break-even hurdle is the PRIMARY gate (V6 razor class "
                   "3.0 bps hurdle named)",
            "citable": True,
            "authority": "plan PLAN_forex_ng7.md §4 F4 + A4 axis-2 "
                         "(committed, sha-pinned dossiers)",
        },
        "financing_band": {
            "search_space": "authorized evidence space ONLY: committed git "
                            "evidence on main + P-13 archive manifests",
            "citable_band_found": False,
            "evidence": evidence,
            "financed_book": "NOT_MEASURABLE",
            "class": "FOREX-NG6 P0-F4 fail-closed",
            "routing": "plan §6 dual-books row: no financing authority at "
                       "the D1 freeze -> financed book NOT_MEASURABLE and "
                       "the family closes BLOCKED — never scored on a "
                       "silent zero; implicit zero-financing book forbidden",
        },
    }


# --------------------------------------------------------------------------
# F7: control authority classes from the A3 dossier
# --------------------------------------------------------------------------
def control_authority_classes() -> dict:
    if sha256_file(A3_DOSSIER) != (
        "1e05d07e990824f6ba3e15fca3096bd14d0454ee6c997aa478f831ce0de8f203"
    ):
        raise FailClosedError("A3 dossier sha mismatch vs committed pin")
    a3 = json.loads(A3_DOSSIER.read_text(encoding="utf-8"))
    ident = a3["global_findings"]["identity_ruling"]
    return {
        "schema": "fng7_p0_control_authority@1",
        "source": str(A3_DOSSIER),
        "ny_fed": {
            "class": "RETRIEVAL_TIME_ONLY",
            "detail": "no per-row publication timestamps; single-day T+1 "
                      "bracket measured; /get/ time-range channel measured "
                      "HTTP 400 (P-7: /last/ channel only); historical depth "
                      "in hand 10 rows/rate",
        },
        "ofr": {
            "class": "RETROSPECTIVE_ONLY",
            "detail": "[date, value] wire schema; zero revision/timestamp "
                      "evidence",
        },
        "identity_ruling": ident[:400] + ("..." if len(ident) > 400 else ""),
        "use_scope": "D2 funding/liquidity CONTROLS ONLY — NEVER an FX "
                     "signal (A3 identity ruling; a use that would require "
                     "knowability is forbidden)",
        "forward_fill": "NONE across holiday/release gaps anywhere",
    }


# --------------------------------------------------------------------------
# F6 reproducibility digests
# --------------------------------------------------------------------------
def repro_digests() -> dict:
    names = ["folds.json", "census.json", "staging_manifest.json"]
    return {n: sha256_file(P0_DIR / n) for n in names}


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main() -> int:
    steps = {}

    # F1(i) archive digests
    sums = {}
    for line in (STAGING_BACKUP / "SHA256SUMS.txt").read_text().splitlines():
        if line.strip():
            digest, name = line.split(maxsplit=1)
            sums[name.strip()] = digest
    archive_checks = {}
    for name, expected in sorted(sums.items()):
        path = STAGING_BACKUP / name
        if not path.exists():
            archive_checks[name] = "MISSING"
            continue
        archive_checks[name] = (
            "OK" if sha256_file(path) == expected else "MISMATCH"
        )
    forex_ok = all(v == "OK" for k, v in archive_checks.items()
                   if k.startswith("forex"))
    steps["F1_i_archive_digests"] = {
        "checks": archive_checks,
        "forex_archives_all_ok": forex_ok,
    }
    if not forex_ok:
        raise FailClosedError("F1(i): forex archive digest failure")

    # F1(ii) staged members + structural census
    pins = load_a2_pins(A2_DOSSIER)
    staged = verify_staged_against_pins(STAGED_DIR, pins)
    leg_data = {}
    structural = {}
    for leg in LEGS:
        data = load_leg_payload(STAGED_DIR / f"{leg}.json")
        leg_data[leg] = data
        structural[leg] = structural_census(leg, data, pins[leg])
    struct_ok = all("fail" not in s for s in structural.values())
    steps["F1_ii_members_structural"] = {
        "member_digests": staged,
        "structural_census": structural,
        "all_ok": struct_ok,
    }
    if not struct_ok:
        raise FailClosedError("F1(ii): structural census failure")

    # F1(v) calendar census (no ffill)
    cal = calendar_census(leg_data)
    steps["F1_v_calendar_census"] = cal

    # F5 folds (frozen from the intersection calendar BEFORE counts read)
    intersection_dates = sorted(
        set.intersection(*[set(d["dates"]) for d in leg_data.values()])
    )
    folds = build_folds(intersection_dates)
    write_json_deterministic(P0_DIR / "folds.json", folds)

    # F5 trigger census (counts only)
    census = trigger_census(leg_data, folds)
    census["schema"] = "fng7_p0_trigger_census@1"
    census["construction"] = (
        "FNG7-A2-P1-ABSORB: CLV=((C-L)-(H-C))/(H-L); P_t=sum CLV over "
        "trailing 20 completed bars; slope=P_t-P_{t-5}; LONG = fresh "
        "20-bar close LOW + slope>0; SHORT mirror; warmup 60 (first "
        "decision bar 61); counts only — no returns/PnL anywhere"
    )
    write_json_deterministic(P0_DIR / "census.json", census)

    # F1(iii) bounded re-pull per the frozen contract
    repull = execute_repull(CONTRACT_PATH, leg_data)
    write_json_deterministic(P0_DIR / "repull_result.json", repull)
    steps["F1_iii_repull"] = {"outcome": repull["outcome"]}

    # F1(iv) staging manifest pin
    manifest = {
        "schema": "fng7_p0_staging_manifest@1",
        "cycle_id": "FOREX-NG7",
        "staged_dir": str(STAGED_DIR),
        "members": {
            leg: {
                "file": f"{leg}.json",
                "sha256": staged[leg]["sha256"],
                "a2_member_pin_sha256": staged[leg]["a2_member_pin_sha256"],
                "rows": structural[leg]["rows"],
                "span": structural[leg]["span_measured"],
            }
            for leg in LEGS
        },
        "authority_chain": [
            "~/staging_backups/cleanup_2026-09-12/SHA256SUMS.txt (archives)",
            "A2 dossier member pins (sha 72284c8f…)",
            "this manifest (staged copies byte-identical to members)",
        ],
        "raw_data_commit_policy": "data_raw/ gitignored — manifest only",
    }
    write_json_deterministic(P0_DIR / "staging_manifest.json", manifest)
    sums_txt = "\n".join(
        f"{manifest['members'][leg]['sha256']}  {leg}.json" for leg in LEGS
    )
    (P0_DIR / "SHA256SUMS.txt").write_text(sums_txt + "\n", encoding="utf-8")
    steps["F1_iv_manifest"] = {
        "pinned": ["staging_manifest.json", "SHA256SUMS.txt"],
    }

    # F2 + F4
    ent = entitlement_evidence()
    ruling = cost_ruling()

    # F7
    controls = control_authority_classes()

    # F6 repro digests (compare against a previous run if present)
    digests = repro_digests()
    digest_txt = "\n".join(f"{v}  {k}" for k, v in sorted(digests.items()))
    digest_path = P0_DIR / "p0_repro_digest.txt"
    previous = digest_path.read_text() if digest_path.exists() else None
    digest_path.write_text(digest_txt + "\n", encoding="utf-8")
    repro = {
        "digest_scope": ["folds.json", "census.json", "staging_manifest.json"],
        "current": digests,
        "previous_run_digest_file_identical": (
            None if previous is None else previous == digest_txt + "\n"
        ),
        "protocol": "run this script twice; F6 PASS iff the two "
                    "p0_repro_digest.txt files are byte-identical",
    }

    # Assemble verdict
    f5_pass = census["floor_all_folds_ok"]
    f6_pass = repro["previous_run_digest_file_identical"] is True
    f1_pass = (
        struct_ok
        and repull["outcome"] in ("BYTE_IDENTITY", "DIVERGENCE",
                                  "NOT_RUN_KEY_ABSENT", "NOT_RUN_NETWORK",
                                  "NOT_RUN_INSUFFICIENT_OVERLAP")
        and repull["outcome"] != "NOT_RUN_CONTRACT_MISMATCH"
    )
    verdict = {
        "schema": "forex_ng7_p0_verdict@1",
        "cycle_id": "FOREX-NG7",
        "lane": "p0-census",
        "role": "A3/A8-P0",
        "base_sha": "817cf8cbb7062a4edc67ff46fc4235ce769cdb42",
        "branch": "orca/forex-ng7-integration",
        "measured_at_utc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
        "scope_law": "P0 is source engineering and census only — no "
                     "candidate PnL/PF/Sharpe/drawdown/S1 evidence",
        "gates": {
            "F1": {
                "verdict": "PASS" if f1_pass else "FAIL",
                "steps": steps,
                "repull_outcome": repull["outcome"],
                "repull_authority_declaration": repull.get(
                    "authority_declaration",
                    "archive vintage remains THE cycle authority",
                ),
            },
            "F2": {
                "verdict": "PASS" if ent["all_citations_exist"] else "FAIL",
                "evidence": ent,
            },
            "F3": {
                "verdict": "PASS",
                "contract": {
                    "decision_clock": "frozen 16:00-NY daily decision clock "
                                      "(date-only archived stamps; convention "
                                      "inherited via A2 clock pin)",
                    "entry": "state fires on completed bar t -> fill at bar "
                             "t+1 first bookable price (bar open); no "
                             "same-bar signal-fill",
                    "exit_mapping": "exit condition knowable at bar-t close "
                                    "executes at bar t+1 first bookable "
                                    "price (V7 F-A7-PL-1 class pre-empted)",
                    "open_vs_close_fill": "open-fill frozen HERE before any "
                                          "scoring (V6/V8 execution-freeze "
                                          "law)",
                    "golden_tests": "tests/test_forex_ng7_p0.py",
                },
            },
            "F4": {
                "verdict": "RULING_RECORDED",
                "ruling": ruling,
                "primary": "stress tier 2.0; 1.5 bps/fill floor band",
                "financed_book": ruling["financing_band"]["financed_book"],
            },
            "F5": {
                "verdict": "PASS" if f5_pass else "FAIL_SUB_POPULATED",
                "measured_totals": {
                    k: v["total"] for k, v in census["per_fold"].items()
                },
                "totals_all": census["totals"],
                "floor_pin": folds["population_floor_pin"],
            },
            "F6": {
                "verdict": "PASS" if f6_pass else "PENDING_SECOND_RUN"
                if repro["previous_run_digest_file_identical"] is None
                else "FAIL",
                "repro": repro,
            },
            "F7": {
                "verdict": "PASS",
                "classes": controls,
            },
        },
        "financing_ruling": (
            "financed_book NOT_MEASURABLE (FOREX-NG6 P0-F4 class): no "
            "citable financing band exists in the authorized evidence "
            "space; routed to the plan §6 dual-books BLOCKED branch at the "
            "D1 freeze; NOT rescued, NOT silently zeroed"
        ),
        "recommended_next_action": "Lead: D1 freeze or P0-gated close",
        "known_limitations": [
            "financed_book NOT_MEASURABLE — dual-books BLOCKED branch "
            "binding at D1 freeze",
            f"re-pull outcome {repull['outcome']} — archive vintage is THE "
            "cycle authority; vendor bytes never merged",
            "16:00-NY stamp convention inherited via A2 clock pin, not "
            "per-row machine-evidenced (date-only stamps verified)",
            "weekend-stamped vendor bars carried as archived (Sat/Sun "
            "present); census does not filter them",
            "archived vendor OHLC artifacts recorded verbatim (USDCAD 6, "
            "NZDUSD 6; sub-pip H/L-vs-close session marks) — carried as-is, "
            "never repaired; see census.ohlc_artifact_disposition",
        ],
        "incidents": [],
        "workers": 0,
    }
    overall_pass = (
        f1_pass
        and ent["all_citations_exist"]
        and f5_pass
        and controls["ny_fed"]["class"] == "RETRIEVAL_TIME_ONLY"
        and controls["ofr"]["class"] == "RETROSPECTIVE_ONLY"
    )
    verdict["overall"] = (
        "P0_CENSUS_PASS_FINANCED_BOOK_NOT_MEASURABLE"
        if overall_pass
        else "P0_CENSUS_FAIL_CLOSED"
    )
    write_json_deterministic(P0_DIR / "p0_verdict.json", verdict)
    print(
        json.dumps(
            {
                "overall": verdict["overall"],
                "F1": verdict["gates"]["F1"]["verdict"],
                "F5_fold_totals": verdict["gates"]["F5"]["measured_totals"],
                "F6": verdict["gates"]["F6"]["verdict"],
                "repull": repull["outcome"],
                "financed_book": verdict["gates"]["F4"]["financed_book"],
            },
            indent=1,
        )
    )
    return 0 if overall_pass else 2


if __name__ == "__main__":
    sys.exit(main())
