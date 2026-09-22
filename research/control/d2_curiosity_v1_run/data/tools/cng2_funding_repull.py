"""DATA-GATE lane D2-CURIOSITY-V1: CNG2-A5-P1 funding re-pull (binding, no outcomes).

Re-pulls the keyless fapi/v1/fundingRate settlement series for BTC/ETH/SOL
over the frozen panel window by IMPORTING the source cycle's own code from
the read-only reconstruction tree (/tmp/d2c_sources/crypto_ng2) -- the exact
module the pinned bytes were produced with (research.assets.crypto_ng2.d2.measure,
sha b8968b5f...).  Output is redirected to THIS lane's data dir.

Binding law (source_identity_freeze.json): step 2 digest match vs pin
38ad6faf... -> BOUND_DIGEST; else recorded invariants -> BOUND_CONTENT/BLOCKED.

NO outcome computation anywhere: this writes the settlement series and
construction-invariant reports only.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

RECON = "/tmp/d2c_sources/crypto_ng2"
OUT_DIR = Path(__file__).resolve().parents[1] / "cng2"

sys.path.insert(0, RECON)
from research.assets.crypto_ng2.d2 import measure as M  # noqa: E402

PINS = {
    "funding_history.json": "38ad6faf2fcbf6c80f31241d426afc61837d5886cccccb8c1cd4f566ac0cdab1",
    "manifest.json": "a3634d6ef4c74bd2e14a6d1bcbff0a1deb388695e9030d02ac31682563d374ec",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    generated = datetime.now(timezone.utc).isoformat()
    funding, reports = M.pull_funding_all()
    blob = json.dumps(funding, sort_keys=True) + "\n"
    (OUT_DIR / "funding_history.json").write_text(blob)
    data_sha = sha256_bytes(blob.encode())

    ev_reports = {}
    for sym, rows in funding.items():
        ev = M.build_funding_evidence(sym, rows)
        ev_reports[sym] = ev.report()

    manifest = {
        "schema": "crypto_ng2_run/d2_funding_pull_manifest@1 (DATA-GATE lane re-pull, output redirected)",
        "task_id": "d2-curiosity-v1-data-gate",
        "cycle_id": "D2-CURIOSITY-V1",
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
            "path": "research/control/d2_curiosity_v1_run/data/cng2/funding_history.json",
            "sha256": data_sha,
            "bytes": len(blob.encode()),
        },
        "per_symbol": reports,
        "evidence_fold": ev_reports,
        "grid_hypothesis_1094_per_symbol": all(
            r["eligible_grid_instants"] == 1094 and r["evidenced_grid_instants"] == 1094
            and r["off_grid_rows"] == 0 and r["duplicate_grid_hours"] == 0
            and r["non_increasing_pairs"] == 0
            for r in ev_reports.values()),
        "pins_compared": PINS,
        "digest_match": {
            "funding_history.json": data_sha == PINS["funding_history.json"],
            "manifest.json": False,  # manifest embeds generated_utc; never byte-reproducible
        },
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")

    print("data sha256 :", data_sha)
    print("pin         :", PINS["funding_history.json"])
    print("MATCH       :", data_sha == PINS["funding_history.json"])
    for sym, r in ev_reports.items():
        print(f"  {sym}: rows={r['rows_in_window']} span={r['span_ms']} "
              f"evidenced={r['evidenced_grid_instants']}/{r['eligible_grid_instants']} "
              f"off_grid={r['off_grid_rows']} dups={r['duplicate_grid_hours']} "
              f"non_increasing={r['non_increasing_pairs']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
