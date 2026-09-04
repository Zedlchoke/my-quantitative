"""STOCKS-FREE-V5 P2-a: ETF snapshot replay measurement (PLAN_stocks_v5.md §6.P2).

Read-only replay of the authorized 12-ETF snapshot exactly as V4-P2 did:
re-hash every MANIFEST-listed file, recompute the per-symbol census, cohort
digest and calendar census, and compare every value against the frozen V4
authority (p2_a3_data_manifest.json / p2_a3_benchmark_contract.json at the V4
terminal).  No network, no modification of the snapshot, no returns computed.

Run:  .venv/bin/python research/control/stocks_free_v5_run/p2_replay_measure.py
"""

from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[3]))

from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3]
SNAPSHOT = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v2/z8-exec-1/.staging"
)
V4_MANIFEST = REPO / "research/control/stocks_free_v4_run/p2_a3_data_manifest.json"
V4_BENCHMARK = REPO / "research/control/stocks_free_v4_run/p2_a3_benchmark_contract.json"
OUT = REPO / "research/control/stocks_free_v5_run/p2_a3_snapshot_replay.json"

FROZEN_MANIFEST_SHA = (
    "62ac324d7e683961b0d88f85153e4a072d09fe0a6745a54687b9e3b219d8f658"
)
SYMBOLS = ["SPY", "XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY"]
S0_START, S0_END = date(2018, 4, 4), date(2025, 7, 31)


def sha256_file(path: Path) -> str:
    h = sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    manifest_path = SNAPSHOT / "MANIFEST.json"
    manifest_sha = sha256_file(manifest_path)
    manifest = json.loads(manifest_path.read_text())
    files = manifest["files"] if "files" in manifest else manifest
    v4 = json.loads(V4_MANIFEST.read_text())
    v4bench = json.loads(V4_BENCHMARK.read_text())

    failures: list[str] = []

    if manifest_sha != FROZEN_MANIFEST_SHA:
        failures.append(f"MANIFEST sha drift: {manifest_sha}")

    # per-file hash equality
    listed = mismatched = 0
    if isinstance(files, dict):
        iterator = files.items()
    else:
        iterator = ((entry.get("path", entry.get("name")), entry) for entry in files)
    for name, entry in iterator:
        expected = entry if isinstance(entry, str) else (entry or {}).get("sha256") or (entry or {}).get("sha")
        if not expected or not name:
            continue
        listed += 1
        path = SNAPSHOT / Path(str(name)).name
        if not path.exists() or sha256_file(path) != expected:
            mismatched += 1
            failures.append(f"file hash mismatch: {name}")

    # per-symbol census + determinism
    per_symbol: dict[str, dict] = {}
    for sym in SYMBOLS:
        none1 = SNAPSHOT / f"{sym}_none_p1.json"
        all1 = SNAPSHOT / f"{sym}_all_p1.json"
        none2 = SNAPSHOT / f"{sym}_none_p2.json"
        a = json.loads(none1.read_text())["values"]
        b = json.loads(all1.read_text())["values"]
        rows_none, rows_all = len(a), len(b)
        first, last = a[-1]["datetime"][:10], a[0]["datetime"][:10]  # descending
        per_symbol[sym] = {
            "none_rows": rows_none,
            "all_rows": rows_all,
            "first": first,
            "last": last,
            "none_hash_ne_all": sha256_file(none1) != sha256_file(all1),
            "p2_determinism_match": sha256_file(none1) == sha256_file(none2),
        }
        v4sym = v4["inventory"]["per_symbol"][sym]
        for key in ("none_rows", "all_rows", "first", "last"):
            if per_symbol[sym][key] != v4sym[key]:
                failures.append(f"{sym}.{key}: {per_symbol[sym][key]} != V4 {v4sym[key]}")
        for key in ("none_hash_ne_all", "p2_determinism_match"):
            if per_symbol[sym][key] is not v4sym[key]:
                failures.append(f"{sym}.{key}: drift vs V4")

    # cohort digest (frozen recipe)
    joined = ",".join(sorted(SYMBOLS))
    cohort_digest = sha256(joined.encode("utf-8")).hexdigest()
    if cohort_digest != v4["cohort_freeze"]["cohort_digest"]:
        failures.append(f"cohort digest drift: {cohort_digest}")

    # calendar census from SPY raw sessions
    spy_dates = sorted(row["datetime"][:10] for row in json.loads((SNAPSHOT / "SPY_none_p1.json").read_text())["values"])
    calendar = {
        "calendar_total_sessions": len(spy_dates),
        "calendar_first": spy_dates[0],
        "calendar_last": spy_dates[-1],
    }
    v4cal = v4["calendar_census"]
    for key, value in calendar.items():
        if value != v4cal[key]:
            failures.append(f"calendar.{key}: {value} != V4 {v4cal[key]}")

    # S0 window sessions + S1 seal boundary
    s0 = [d for d in spy_dates if S0_START.isoformat() <= d <= S0_END.isoformat()]
    s1 = [d for d in spy_dates if d > S0_END.isoformat()]
    s0_expected = v4cal.get("S0_window", {}).get("sessions") or v4bench["data_binding"]["calendar"]
    if len(s0) != 1842:
        failures.append(f"S0 sessions: {len(s0)} != 1842")
    if len(s1) != 270:
        failures.append(f"S1 sealed sessions: {len(s1)} != 270")

    report = {
        "schema": "stocks_free_v5_run/p2_a3_snapshot_replay@1",
        "generated_at_utc": "2026-09-04T06:35:00Z",
        "producer_role": "A3 (A1-controlled lane)",
        "mode": "replay-only, read-only, no network, no returns",
        "snapshot_root": str(SNAPSHOT),
        "manifest_sha256": manifest_sha,
        "manifest_files_listed": listed,
        "manifest_files_mismatched": mismatched,
        "per_symbol": per_symbol,
        "cohort_digest": cohort_digest,
        "calendar_census": calendar,
        "s0_window": {"start": S0_START.isoformat(), "end": S0_END.isoformat(), "sessions": len(s0)},
        "s1_sealed": {"first_after_boundary": s1[0] if s1 else None, "sessions": len(s1)},
        "v4_authority_comparison": "every measured field equal to frozen V4 values" if not failures else failures,
        "verdict": "PASS" if not failures else "FAIL",
        "failures": failures,
    }
    OUT.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({k: report[k] for k in ("verdict", "manifest_sha256", "manifest_files_listed", "manifest_files_mismatched", "cohort_digest", "calendar_census", "s0_window", "s1_sealed")}, indent=1))
    if failures:
        print("FAILURES:", *failures, sep="\n  ")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
