#!/usr/bin/env python3
"""verify_probe.py — deterministic verifier for forex_mt5_cost_probe_2026-09.

Computes VERDICT INPUTS ONLY (schema, dedupe, gaps, coverage arithmetic vs
the preregistered floors in probe_contract.json, spec-snapshot hashes).
It NEVER issues a verdict: only the independent A7 audit concludes whether
the collected data suffices to unlock a FOREX successor cycle.

Usage:
  python3 verify_probe.py <path-to-extracted-forex_mt5_cost_probe-folder> \
      [--window-days 7] [--out verdict_inputs.json]
"""
import csv
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path

EXPECTED_SYMBOLS = ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCAD"]
BUCKET_SECONDS = 300          # 5-minute buckets (contract F1)
PRESENCE_FLOOR = 0.95         # contract F1
# minimum expected fields per row (tick/heartbeat/spec rows carry a 7-field
# account-context tail; csv module handles the quoted fields)
MIN_COLUMNS = {
    "tick_samples.csv": 17,
    "heartbeat.csv": 13,
    "spec_snapshot.csv": 28,
    "events.csv": 10,
}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_utc(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    root = Path(sys.argv[1]).expanduser().resolve()
    window_days = int(sys.argv[sys.argv.index("--window-days") + 1]) if "--window-days" in sys.argv else 7
    out_path = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else root / "verdict_inputs.json"

    inputs = {
        "schema": "forex_mt5_cost_probe_verdict_inputs@1",
        "probe_id": "forex_mt5_cost_probe_2026-09",
        "root": str(root),
        "note": "VERDICT INPUTS ONLY - the A7 audit alone concludes data sufficiency",
        "files": {},
        "parse": {},
        "dedupe": {},
        "coverage": {},
        "spec_snapshots": {},
        "commission_inputs": {},
        "floors": {},
    }

    # ---- files + parse validation (csv-aware, quoted fields OK) ----
    for name, mincols in MIN_COLUMNS.items():
        p = root / name
        if not p.exists():
            inputs["files"][name] = {"present": False}
            continue
        rows, bad, widths = [], 0, set()
        for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
            if not ln.strip():
                continue
            parts = next(csv.reader([ln]))
            widths.add(len(parts))
            if len(parts) >= mincols:
                rows.append(parts)
            else:
                bad += 1
        inputs["files"][name] = {
            "present": True,
            "sha256": sha256_file(p),
            "rows": len(rows),
            "malformed_rows": bad,
            "observed_field_widths": sorted(widths),
            "minimum_expected_fields": mincols,
        }
        inputs["parse"][name] = rows

    if not (root / "tick_samples.csv").exists():
        out_path.write_text(json.dumps(inputs, indent=1))
        print(f"verdict inputs written (tick file missing): {out_path}")
        return 0

    ticks = inputs["parse"]["tick_samples.csv"]

    # ---- dedupe (contract F5) ----
    seen, dups = set(), 0
    uniq = []
    for r in ticks:
        key = (r[1], r[8], r[2], r[3])  # symbol, venue_time_msc, bid, ask
        if key in seen:
            dups += 1
            continue
        seen.add(key)
        uniq.append(r)
    inputs["dedupe"] = {"raw_rows": len(ticks), "duplicates_dropped": dups, "unique_rows": len(uniq)}

    # ---- coverage (contract F1/F2): raw counts only, A7 does floor arithmetic ----
    times = [parse_utc(r[0]) for r in uniq if r[0].endswith("Z")]
    if times:
        t0, t1 = min(times), max(times)
        span_days = (t1 - t0).total_seconds() / 86400.0
        per_symbol_day_buckets = defaultdict(lambda: defaultdict(set))
        for r in uniq:
            t = parse_utc(r[0])
            b = t.replace(minute=(t.minute // 5) * 5, second=0, microsecond=0)
            per_symbol_day_buckets[r[1]][b.date().isoformat()].add(b)
        inputs["coverage"] = {
            "first_sample_utc": t0.isoformat(),
            "last_sample_utc": t1.isoformat(),
            "span_days": round(span_days, 3),
            "window_days_preregistered": window_days,
            "expected_5min_buckets_per_full_day": 86400 // BUCKET_SECONDS,
            "per_symbol_per_day_distinct_5min_buckets": {
                s: {d: len(b) for d, b in sorted(days.items())}
                for s, days in sorted(per_symbol_day_buckets.items())
            },
            "note": "raw counts only; the 95% presence floor and session coverage are A7's arithmetic",
        }
        inputs["floors"] = {
            "F1_presence_floor": PRESENCE_FLOOR,
            "F3_rollover_note": "20:55-01:05 UTC window sampling checked by A7 from tick rows",
        }

    # ---- spec snapshots: hash each (kind, symbol) snapshot block ----
    specs = inputs["parse"].get("spec_snapshot.csv", [])
    blocks = defaultdict(list)
    for r in specs:
        blocks[(r[1], r[2])].append(",".join(r))
    inputs["spec_snapshots"] = {
        f"{kind}/{sym}": hashlib.sha256("\n".join(rows).encode()).hexdigest()
        for (kind, sym), rows in sorted(blocks.items())
    }
    syms = {s for _, s in blocks}
    inputs["spec_snapshots"]["all_expected_symbols_present"] = sorted(syms) == sorted(EXPECTED_SYMBOLS)

    # ---- heartbeat summary (columns: 0 recv, 1 connected, 2 ok, 3 stale,
    # 4 rows_total, 5 parse_errors, then context: 6 company, 7 server,
    # 8 trade_mode, 9 currency, 10 login-redacted, 11 trade_allowed, 12 connected2) ----
    beats = inputs["parse"].get("heartbeat.csv", [])
    if beats:
        inputs["heartbeat_summary"] = {
            "rows": len(beats),
            "trade_allowed_flag_values_seen": sorted({r[11] for r in beats if len(r) > 11}),
            "connected_values_seen": sorted({r[1] for r in beats}),
            "parse_errors_max": max(int(r[5]) for r in beats),
        }

    # ---- commission inputs (from the events/startup rows only; never a verdict) ----
    evs = inputs["parse"].get("events.csv", [])
    if evs:
        startup = next((r for r in evs if r[1] == "startup"), None)
        if startup:
            inputs["commission_inputs"] = {
                "account_context_from_startup": ",".join(startup[3:]),
                "posture": "UNKNOWN until A7 adjudicates; commission is never inferred as 0 (contract)",
            }

    out_path.write_text(json.dumps(inputs, indent=1))
    print(f"verdict inputs written: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
