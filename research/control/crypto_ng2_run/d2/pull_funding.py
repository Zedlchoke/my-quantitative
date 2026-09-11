"""CRYPTO-NG2 D2 funding-settlement pull (lane A5 data_dependency).

Keyless GET fapi/v1/fundingRate for BTCUSDT/ETHUSDT/SOLUSDT over the FULL
frozen panel window (2025-08-22T00:00Z .. 2026-08-21T23:59:59.999Z),
paginated by startTime (observed per-response cap 500 rows against a
requested limit of 1000), retrieval etiquette <= 1 request / 0.5 s with
bounded backoff (3 retries, 5s x attempt).  Fail-closed: exhausted retries
abort with a nonzero exit and NOTHING is written.

Pins the verbatim rows under data_raw/cng2_funding/ (UNTRACKED -- the raw
bytes never enter git) together with a sha256 manifest; the committed D2
artifacts quote the manifest sha256 (P-12: code + numbers in the commit,
data pinned content-addressed outside it).
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve()
_WORKTREE = _HERE.parents[4]
sys.path.insert(0, str(_WORKTREE))

from research.assets.crypto_ng2.d2 import measure as M   # noqa: E402

PIN_DIR = _WORKTREE / "data_raw" / "cng2_funding"
OUT_DATA = PIN_DIR / "funding_history.json"
OUT_MANIFEST = PIN_DIR / "manifest.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    generated = datetime.now(timezone.utc).isoformat()
    PIN_DIR.mkdir(parents=True, exist_ok=True)
    funding, reports = M.pull_funding_all()
    blob = json.dumps(funding, sort_keys=True) + "\n"
    OUT_DATA.write_text(blob)
    data_sha = sha256_bytes(blob.encode())

    ev_reports = {}
    for sym, rows in funding.items():
        ev = M.build_funding_evidence(sym, rows)
        ev_reports[sym] = ev.report()

    manifest = {
        "schema": "crypto_ng2_run/d2_funding_pull_manifest@1",
        "task_id": "crypto-ng2-d2-measurement",
        "cycle_id": "CRYPTO-NG2",
        "lane": "d2",
        "generated_utc": generated,
        "endpoint": M.FUNDING_URL,
        "window": {
            "start_ms": int(M.PANEL_WINDOW_START.timestamp() * 1000),
            "end_ms": int((M.PANEL_WINDOW_END
                           + __import__("datetime").timedelta(hours=1))
                          .timestamp() * 1000) - 1,
            "start_utc": "2025-08-22T00:00:00Z",
            "end_utc": "2026-08-21T23:59:59.999Z",
        },
        "etiquette": {
            "min_request_interval_s": M.FUNDING_ETIQUETTE_SLEEP_S,
            "retries": M.FUNDING_RETRIES,
            "backoff_s_per_attempt": M.FUNDING_BACKOFF_S,
            "requested_limit": M.FUNDING_REQUEST_LIMIT,
            "observed_per_response_cap": M.FUNDING_OBSERVED_CAP,
        },
        "data_file": {
            "path": "data_raw/cng2_funding/funding_history.json",
            "sha256": data_sha,
            "bytes": len(blob.encode()),
            "untracked": True,
        },
        "per_symbol": reports,
        "evidence_fold": ev_reports,
        "grid_hypothesis_1094_per_symbol": all(
            r["eligible_grid_instants"] == 1094
            for r in ev_reports.values()),
    }
    OUT_MANIFEST.write_text(json.dumps(manifest, indent=1) + "\n")
    mani_sha = sha256_bytes(OUT_MANIFEST.read_bytes())

    print(f"funding pull pinned: {OUT_DATA}")
    print(f"  data sha256     : {data_sha}")
    print(f"  manifest sha256 : {mani_sha}")
    for sym, r in ev_reports.items():
        print(f"  {sym}: rows={r['rows_in_window']} "
              f"evidenced={r['evidenced_grid_instants']}/1094 "
              f"off_grid={r['off_grid_rows']} "
              f"dups={r['duplicate_grid_hours']} "
              f"non_increasing={r['non_increasing_pairs']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
