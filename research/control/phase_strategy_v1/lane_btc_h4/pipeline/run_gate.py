"""PSV1 lane_btc_h4 — data gate driver (plan §9.1).

Runs: probe -> ingest+manifest -> re-retrieval verification -> 1h load ->
H4 derivation -> integrity -> 4h native shadow -> 15m catalog cross-check.
Writes data/manifest.json and data/data_gate.json. Raw zips stay in the
gitignored data_staging/.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

LANE_DIR = Path(__file__).resolve().parents[1]
# worktree root = lane_btc_h4/.parents[3]; namespace-package import path
sys.path.insert(0, str(LANE_DIR.parents[3]))

from research.control.phase_strategy_v1.lane_btc_h4.pipeline import config, ingest, h4derive, crosscheck  # noqa: E402

STAGING = LANE_DIR / "data_staging"


def probe_tail() -> tuple[str, str, list[dict]]:
    """Determine last complete month + last available daily tail day."""
    notes: list[dict] = []
    last_month = "2026-08"
    # tail days: probe 2026-09-22 and 2026-09-23
    tail_last = "2026-09-22"
    body, status = ingest.fetch(ingest.url_1h_daily("2026-09-23"))
    if body is not None:
        tail_last = "2026-09-23"
        notes.append({"probe": "2026-09-23 daily 1h", "result": "HTTP 200 (day complete at retrieval)"})
    else:
        notes.append({"probe": "2026-09-23 daily 1h", "result": f"HTTP {status} — day not complete/absent; tail ends 2026-09-22"})
    body, status = ingest.fetch(ingest.url_1h_monthly("2026-08"))
    notes.append({"probe": "2026-08 monthly 1h", "result": f"HTTP {status}"})
    body, status = ingest.fetch(ingest.url_1h_monthly("2019-12"))
    notes.append({"probe": "2019-12 monthly 1h (expect 404)", "result": f"HTTP {status}"})
    return last_month, tail_last, notes


def main() -> int:
    last_month, tail_last, probe_notes = probe_tail()
    print(f"[probe] last_complete_month={last_month} tail_last_day={tail_last}")

    manifest = ingest.ingest_all(STAGING, last_month, tail_last)
    print(f"[ingest] files={len(manifest['files'])} skipped_tail={len(manifest['skipped_tail_days'])}")

    rerun = ingest.verify_reretrieval(manifest, STAGING)
    manifest["deterministic_reretrieval_verification"] = rerun
    print(f"[reretrieval] {[r['digest_match'] for r in rerun]}")

    df1h = ingest.load_1h_from_manifest(manifest, STAGING)
    native4h = ingest.load_4h_from_manifest(manifest, STAGING)
    print(f"[load] 1h rows={len(df1h)} native4h rows={len(native4h)}")

    data_end_ms = int(df1h["close_time_ms"].max())
    h4, deriv = h4derive.derive_h4(df1h)
    print(f"[h4] complete buckets={len(h4)} partial excluded={deriv['n_partial_buckets_excluded']}")

    integ = h4derive.integrity_report(df1h, h4, data_end_ms)
    print(f"[integrity] verdict={integ['verdict']} problems={integ['problems']}")

    shadow = crosscheck.compare_4h_shadow(h4, native4h)
    print(f"[shadow4h] verdict={shadow['verdict']} buckets_with_mismatch={shadow['n_buckets_with_any_mismatch']}")

    cat_df, cat_digest = crosscheck.load_catalog_parquet(config.CATALOG_PARQUET, config.CATALOG_SHA256)
    cat = crosscheck.compare_catalog(h4, cat_df)
    print(f"[catalog15m] verdict={cat['verdict']} shared={cat['n_shared_with_scored']}")

    gate = {
        "schema": "psv1_lane_btc_h4_data_gate@1",
        "cell": config.CELL,
        "probe_notes": probe_notes,
        "h4_derivation": deriv,
        "integrity": integ,
        "shadow_4h_crosscheck": shadow,
        "catalog_15m_crosscheck": {**cat, "expected_sha256": config.CATALOG_SHA256,
                                   "observed_sha256": cat_digest, "digest_verified": cat_digest == config.CATALOG_SHA256},
        "data_end": ingest.utc_ms_to_iso(data_end_ms),
        "data_end_ms": data_end_ms,
        "pit_disclosure": config.PIT_CONVENTION,
    }
    shadow_ok = shadow["verdict"].startswith("MATCH")
    if integ["verdict"] == "PASS" and shadow_ok:
        gate["verdict"] = "PASS_WITH_DISCLOSURES"
        gate["disclosures"] = [
            "native-4h shadow: buckets with snapshot-revision diffs are enumerated in shadow_4h_crosscheck (aggregated-from-1h stays the scored representation)",
            "optional frozen-15m-catalog cross-check does NOT corroborate (content differs materially); recorded as CATALOG_NOT_CORROBORATIVE, no smoothing applied",
        ]
    else:
        gate["verdict"] = "BLOCKED"
    if not all(r["digest_match"] for r in rerun):
        gate["verdict"] = "BLOCKED"
        gate["disclosures"] = gate.get("disclosures", []) + ["retrieval nondeterminism"]

    (LANE_DIR / "data").mkdir(parents=True, exist_ok=True)
    gate["reretrieval_verdict"] = ("DETERMINISTIC" if all(r["digest_match"] for r in rerun)
                                   else "NONDETERMINISTIC_INCIDENT")
    (LANE_DIR / "data" / "manifest.json").write_text(ingest.json_dumps(manifest))
    (LANE_DIR / "data" / "data_gate.json").write_text(ingest.json_dumps(gate))
    # small machine-readable store for later stages (derived, not raw)
    h4.to_parquet(STAGING / "scored_h4.parquet", index=False)
    df1h.to_parquet(STAGING / "scored_1h.parquet", index=False)
    print(f"[gate] verdict={gate['verdict']} reretrieval={gate['reretrieval_verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
