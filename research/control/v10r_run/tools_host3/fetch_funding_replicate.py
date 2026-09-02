"""Host-3 bootstrap: funding bundle re-fetch with replicated request ranges.

The old bundle's per-symbol `captured_at` (recorded in d2_stage_report.json)
bounds the original `--days 730` request: requested_end = captured_at,
requested_start = captured_at - 730d. Re-issuing the same range through
research/download_funding.py's own functions yields the same immutable
settlement rows (funding.json bytes still differ via `captured_at` -> recorded
as machine-local divergence; cross-checked against D2's n_rows /
last_settlement numbers instead).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(r"C:\Users\ROYAL\my-quantitative")
sys.path.insert(0, str(REPO))
D2 = REPO / "research/control/v10r_run/d2_stage_report.json"
OUT = REPO / "research/control/v10r_run/staging/funding_data/scan_2026"

from data.derivatives import fetch_funding_history, write_funding_history


def main() -> int:
    d2 = json.loads(D2.read_text())["funding"]["per_symbol"]
    report: dict = {"artifact": "host3_fetch_funding_replicate", "producer_role": "A1",
                    "symbols": {}, "divergences": []}
    ok = bad = 0
    for sym, exp in sorted(d2.items()):
        cap = datetime.fromisoformat(exp["captured_at"])
        start = cap - timedelta(days=730)
        rows = fetch_funding_history(
            sym, start_ms=int(start.timestamp() * 1000), end_ms=int(cap.timestamp() * 1000)
        )
        path = write_funding_history(
            str(OUT), sym, requested_start_ms=int(start.timestamp() * 1000),
            requested_end_ms=int(cap.timestamp() * 1000), rows=rows,
        )
        payload = json.loads(Path(path).read_text())
        last = max(r["fundingTime"] for r in rows) if rows else None
        last_iso = (
            datetime.fromtimestamp(last / 1000, tz=timezone.utc).isoformat() if last else None
        )
        match = len(rows) == exp["n_rows"] and last_iso is not None
        got = {
            "n_rows": len(rows),
            "last_settlement_utc": last_iso,
            "expected_n_rows": exp["n_rows"],
            "expected_last": exp["last_settlement_utc"],
            "rows_match_d2": len(rows) == exp["n_rows"]
            and last_iso == exp["last_settlement_utc"],
        }
        report["symbols"][sym] = got
        if got["rows_match_d2"]:
            ok += 1
        else:
            bad += 1
            report["divergences"].append(sym)
        print(f"[{'OK' if got['rows_match_d2'] else 'DIVERGE'}] {sym}: "
              f"n={len(rows)} (exp {exp['n_rows']}) last={last_iso}", flush=True)
    report["summary"] = {
        "symbols_ok": ok,
        "symbols_diverged": bad,
        "total": len(d2),
        "output_dir": str(OUT),
        "byte_divergence_note": "captured_at differs by construction; settlement rows "
        "cross-checked vs D2 recorded counts/timestamps",
    }
    (REPO / "research/control/v10r_run/host3_fetch_funding_report.json").write_text(
        json.dumps(report, indent=1)
    )
    print("SUMMARY:", report["summary"])
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
