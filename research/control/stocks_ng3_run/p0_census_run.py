#!/usr/bin/env python
"""STOCKS-NG3 P0 census (PLAN_stocks_ng3 sec3, floors frozen in-plan).

Measures E1-E6 fail-closed BEFORE any proposal lane exists. E1/E2/E3 are
kill tests (any miss => BLOCKED verdict). E5 is NOT_RUN at census by
construction (implementation-phase PIT battery; semantics pinned here via
E4). Never prints the API key. Bulk operation -> machine-wide heavy lock.
"""
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

WORKTREE = Path(__file__).resolve().parents[3]
ROOT = Path("/Users/hoangminhlong/my-quantitative")
OUT_DIR = WORKTREE / "research/control/stocks_ng3_run"
STAGING = WORKTREE / ".staging_stocks_ng3"
S0_START, S0_END = "2019-01-01", "2026-08-31"
PULL_FROM = "2016-01-01"
FOLDS = [("F1", "2019-01-01", "2021-08-31"),
         ("F2", "2021-09-01", "2024-01-31"),
         ("F3", "2024-02-01", "2026-08-31")]
RECENT_24M_START = "2024-09-01"
LIVING_SAMPLE, DEAD_SAMPLE = 250, 40
LIVING_CANARIES = ["KO.US", "GE.US", "AAPL.US"]
DEAD_CANARIES = ["TWTR.US", "SIVB.US"]
DEAD_CANARY_LAST_SESSION = {"TWTR.US": "2022-10-27", "SIVB.US": "2023-03-09"}
NEVER_CONTROLS = ["ZZZZZ.US", "NOTREAL.US", "FAKESVB.US"]
E2_FLOOR_EVENTS, E2_FLOOR_ENTITIES = 400, 150
E3_FLOOR_CANARIES = 2

sys.path.insert(0, str(WORKTREE))
from research.governance import heavy_lock  # noqa: E402


def load_key():
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith("EODHD_API_KEY="):
            k = line.split("=", 1)[1].strip()
            if k:
                return k
    raise SystemExit("EODHD_API_KEY missing from root .env")


def get(url, retries=3):
    for a in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.loads(r.read().decode()), r.status
        except urllib.error.HTTPError as e:
            if e.code in (401, 402, 403, 404):
                return None, e.code
            time.sleep(1 + a)
        except Exception:
            time.sleep(1 + a)
    return None, 0


def usable_map(events):
    """code -> {report_date: event} for events with epsActual + date."""
    keyed = {}
    for e in events:
        if e.get("epsActual") is None:
            continue
        rd = str(e.get("reportDate") or e.get("date") or "")[:10]
        if len(rd) == 10 and rd not in keyed:
            keyed[rd] = e
    return keyed


def main():
    key = load_key()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    STAGING.mkdir(parents=True, exist_ok=True)
    handle = heavy_lock.acquire(
        cycle_id="STOCKS-NG3", role="P0_CENSUS", worktree=str(WORKTREE),
        command=[sys.executable, str(Path(__file__))],
        expected_artifacts=[str(OUT_DIR / "p0_census.json")])
    findings, killed = [], []
    try:
        _census(key, findings, killed, handle)
    except Exception as e:  # noqa: BLE001 — honest TECHABORT, never a silent hold
        handle.release(status="TECHABORT", note=f"p0_census crash: {e!r}")
        raise


def _census(key, findings, killed, handle):
    def tok():
        return f"api_token={key}"

    # --- E1 entitlement: per-ticker earnings-history channel (fundamentals) ---
    # Channel map measured 2026-09-15 (probe_endpoints.py): /api/eod 200 (token
    # alive), /api/fundamentals/{code} 403 Forbidden, /api/calendar/earnings 403,
    # /api/earnings 404-html. The fundamentals endpoint is EODHD's only
    # per-ticker earnings-history channel.
    e1 = {"verdict": "PASS", "canaries": {}, "channel_map": {
        "api_eod_price": "200 OK (token alive, measured via probe_endpoints.py raw-eod)",
        "api_fundamentals": "403 Forbidden (plan does not include)",
        "api_calendar_earnings": "403 Forbidden (plan does not include)",
        "api_earnings_legacy": "404 html (endpoint absent)"}}
    for c in LIVING_CANARIES:
        data, status = get(f"https://eodhd.com/api/fundamentals/{c}?{tok()}&filter=Earnings")
        n = len(data.get("Earnings", {}).get("History", {}) or {}) if isinstance(data, dict) else 0
        e1["canaries"][c] = {"status": status, "history_items": n}
        if status != 200 or n == 0:
            e1["verdict"] = "FAIL_ENTITLEMENT"
            killed.append(f"E1 canary {c} fundamentals status={status} history={n}")
    findings.append(("E1", e1))
    if e1["verdict"] != "PASS":
        write_out(findings, killed, handle, None)
        return
    print("E1 PASS", flush=True)

    # --- universe sample from exchange symbol list ---
    uni, status = get(f"https://eodhd.com/api/exchange-symbol-list/US?{tok()}")
    if status != 200 or not isinstance(uni, list):
        killed.append(f"symbol-list status={status}")
        write_out(findings, killed, handle, None)
        return
    common = [u for u in uni if (u.get("Type") or "").lower().startswith("common")]
    living = sorted([u for u in common if not int(u.get("IsDelisted") or 0)],
                    key=lambda u: u["Code"])[::5][:LIVING_SAMPLE]
    dead_pool = sorted([u for u in common if int(u.get("IsDelisted") or 0)
                        and f"{u['Code']}.US" not in DEAD_CANARIES],
                       key=lambda u: u["Code"])[::5][:DEAD_SAMPLE]
    sample_codes = [f"{u['Code']}.US" for u in living] + [f"{u['Code']}.US" for u in dead_pool]
    print(f"universe: {len(uni)} symbols, living sample {len(living)}, dead sample {len(dead_pool)}", flush=True)

    # --- E3 dead canaries + never-existed controls ---
    e3 = {"verdict": "PASS", "canaries": {}, "controls": {}}
    dead_ok = 0
    for c in DEAD_CANARIES:
        data, status = get(f"https://eodhd.com/api/earnings/?{tok()}&symbols={c}&from={PULL_FROM}&to={S0_END}")
        last_rd = max((str(e.get("reportDate") or e.get("date") or "")[:10] for e in data),
                      default="") if isinstance(data, list) else ""
        ok = (status == 200 and isinstance(data, list) and len(data) > 0
              and last_rd and last_rd < DEAD_CANARY_LAST_SESSION[c])
        e3["canaries"][c] = {"status": status, "events": len(data) if isinstance(data, list) else 0,
                             "last_report": last_rd, "pre_death_ok": bool(ok)}
        dead_ok += int(ok)
    for c in NEVER_CONTROLS:
        data, status = get(f"https://eodhd.com/api/earnings/?{tok()}&symbols={c}&from={PULL_FROM}&to={S0_END}")
        empty = (status == 200 and data == []) or status == 404
        e3["controls"][c] = {"status": status, "empty_ok": bool(empty)}
    e3["verdict"] = ("PASS" if dead_ok >= E3_FLOOR_CANARIES
                     and all(v["empty_ok"] for v in e3["controls"].values()) else "FAIL")
    if e3["verdict"] != "PASS":
        killed.append(f"E3 dead_ok={dead_ok} controls={e3['controls']}")
    findings.append(("E3", e3))
    if e3["verdict"] != "PASS":
        write_out(findings, killed, handle, None)
        return
    print("E3 PASS", flush=True)

    # --- pull earnings for the sample; count usable SUE numerators ---
    raw_path = STAGING / "earnings_sample.jsonl"
    entities, usable_recent, timing_ev, timing_tot = {}, 0, 0, 0
    with raw_path.open("w") as fh:
        for i, code in enumerate(sample_codes):
            data, status = get(f"https://eodhd.com/api/earnings/?{tok()}&symbols={code}&from={PULL_FROM}&to={S0_END}")
            rec = {"code": code, "status": status, "events": data if isinstance(data, list) else []}
            fh.write(json.dumps(rec) + "\n")
            keyed = usable_map(rec["events"])
            for rd, e in keyed.items():
                py = f"{int(rd[:4]) - 1}{rd[4:]}"  # same calendar quarter, prior year
                if py in keyed:
                    entities[code] = entities.get(code, 0) + 1
                    if rd >= RECENT_24M_START:
                        usable_recent += 1
                    timing_tot += 1
                    if str(e.get("reportTime") or ""):
                        timing_ev += 1
            if (i + 1) % 50 == 0:
                handle.heartbeat({"progress": f"{i + 1}/{len(sample_codes)}"})
                print(f"pull {i + 1}/{len(sample_codes)} usable_recent={usable_recent} "
                      f"entities={len(entities)}", flush=True)
            time.sleep(0.12)

    # --- E2 floors ---
    e2 = {"usable_recent_24m": usable_recent, "unique_entities": len(entities),
          "floor_events": E2_FLOOR_EVENTS, "floor_entities": E2_FLOOR_ENTITIES,
          "verdict": ("PASS" if usable_recent >= E2_FLOOR_EVENTS
                      and len(entities) >= E2_FLOOR_ENTITIES else "FAIL")}
    if e2["verdict"] != "PASS":
        killed.append(f"E2 events={usable_recent} entities={len(entities)}")
    findings.append(("E2", e2))

    # --- E4 timing coverage (pinned: uniform fallback unless share==1.0) ---
    e4 = {"timing_evidenced": timing_ev, "timing_total": timing_tot,
          "share": round(timing_ev / timing_tot, 4) if timing_tot else 0.0,
          "fallback_rule": "UNIFORM next-open-after-report-date (all events) unless share==1.0",
          "verdict": "PINNED"}
    findings.append(("E4", e4))

    # --- exact per-fold populations over the full usable set ---
    per_fold = {name: 0 for name, _, _ in FOLDS}
    with raw_path.open() as fh:
        for line in fh:
            rec = json.loads(line)
            keyed = usable_map(rec["events"])
            for rd in keyed:
                py = f"{int(rd[:4]) - 1}{rd[4:]}"
                if py in keyed and S0_START <= rd <= S0_END:
                    for name, a, b in FOLDS:
                        if a <= rd <= b:
                            per_fold[name] += 1
    raw_sha = hashlib.sha256(raw_path.read_bytes()).hexdigest()

    verdict = "P0_CENSUS_PASS" if not killed else "P0_CENSUS_BLOCKED"
    write_out(findings, killed, handle,
              {"verdict": verdict, "sample": {"living": len(living), "dead": len(dead_pool)},
               "per_fold": per_fold, "raw_sha256": raw_sha})


def write_out(findings, killed, handle, extra):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    doc = {
        "schema": "stocks_ng3_run/p0_census@1",
        "cycle_id": "STOCKS-NG3",
        "measured_at_utc": now,
        "s0_window": [S0_START, S0_END],
        "pull_from": PULL_FROM,
        "folds_frozen": [{"fold": n, "start": a, "end": b} for n, a, b in FOLDS],
        "floors": {k: v for k, v in findings},
        "killed": killed,
        "verdict": (extra or {}).get("verdict", "P0_CENSUS_BLOCKED"),
        "extra": extra or {},
        "e5_note": "NOT_RUN at census by construction (implementation-phase PIT battery); availability semantics pinned by E4",
        "key_provenance": "root .env EODHD_API_KEY, programmatic load, never echoed",
    }
    (OUT_DIR / "p0_census.json").write_text(json.dumps(doc, indent=1))
    handle.release(status="FINISHED" if not killed else "FAILED",
                   note=f"p0_census verdict={doc['verdict']} killed={killed}")
    print("VERDICT:", doc["verdict"], "killed:", killed)
    for k, v in findings:
        print(k, json.dumps(v)[:240])


if __name__ == "__main__":
    main()
