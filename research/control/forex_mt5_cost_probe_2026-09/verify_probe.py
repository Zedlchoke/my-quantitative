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
# tick: 10 data + 7 context = 17 | heartbeat: 7 + 7 = 14
# spec: 19 data + 7 context = 26 | events: 3 + 7 = 10
MIN_COLUMNS = {
    "tick_samples.csv": 17,
    "heartbeat.csv": 14,
    "spec_snapshot.csv": 26,
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


def argval(flag: str):
    """--flag value extractor that never raises (A7 F-14)."""
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else None


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    root = Path(sys.argv[1]).expanduser().resolve()
    window_days = int(argval("--window-days") or 7)
    out_path = Path(argval("--out") or (root / "verdict_inputs.json"))

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
    raw_lines = {}  # raw text per valid row for spec/events hashing (A7 F-15)
    for name, mincols in MIN_COLUMNS.items():
        p = root / name
        if not p.exists():
            inputs["files"][name] = {"present": False}
            continue
        rows, raws, bad, widths = [], [], 0, set()
        for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
            if not ln.strip():
                continue
            parts = next(csv.reader([ln]))
            widths.add(len(parts))
            if len(parts) >= mincols:
                rows.append(parts)
                raws.append(ln)
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
        if name in ("spec_snapshot.csv", "events.csv"):
            raw_lines[name] = raws

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

    # ---- spec snapshots: sha256 over the RAW csv lines (never re-serialized) ----
    specs = inputs["parse"].get("spec_snapshot.csv", [])
    raws = raw_lines.get("spec_snapshot.csv", [])
    blocks = defaultdict(list)
    for raw, r in zip(raws, specs):
        blocks[(r[1], r[2])].append(raw)
    inputs["spec_snapshots"] = {
        f"{kind}/{sym}": hashlib.sha256("\n".join(rows).encode()).hexdigest()
        for (kind, sym), rows in sorted(blocks.items())
    }
    syms = {s for _, s in blocks}
    inputs["spec_snapshots"]["all_expected_symbols_present"] = sorted(syms) == sorted(EXPECTED_SYMBOLS)

    # ---- heartbeat summary (columns: 0 recv, 1 connected, 2 ok, 3 stale,
    # 4 rows_total, 5 file_errors, 6 tick_errors, then context: 7 company,
    # 8 server, 9 trade_mode, 10 currency, 11 login-redacted, 12 trade_allowed,
    # 13 connected2) ----
    beats = inputs["parse"].get("heartbeat.csv", [])
    if beats:
        def _int(r, i):
            try:
                return int(r[i])
            except (ValueError, IndexError):
                return -1
        inputs["heartbeat_summary"] = {
            "rows": len(beats),
            "trade_allowed_flag_values_seen": sorted({r[12] for r in beats if len(r) > 12}),
            "connected_values_seen": sorted({r[1] for r in beats}),
            "file_errors_max": max(_int(r, 5) for r in beats),
            "tick_errors_max": max(_int(r, 6) for r in beats),
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
