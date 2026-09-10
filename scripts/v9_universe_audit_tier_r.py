#!/usr/bin/env python
"""Tier-R reproduction CLI for the V9 universe + data audit (MDP-V2R1 A3).

Fully offline availability-aware wrapper around
``scripts.v9_universe_audit.run_real_historical_audit``:

  * PROBE  -- checks the REAL v8x host data roots
              (CATALOG_ROOT / FUNDING_ROOT, env-overridable via
              V8X_CATALOG_ROOT / V8X_FUNDING_ROOT) without reading network or
              calling any provider;
  * ABSENT -- writes the availability artifact (expected inputs + paths,
              availability census, invocation provenance, exact blocker,
              offline assertion, read-only hashes of any existing legacy
              states) with verdict NOT_RUN_DATA_UNAVAILABLE;
  * PRESENT -- runs the real audit and compares the fresh outputs
               BYTE-FOR-BYTE against the committed historical artifacts
               (data/v9_manifests/universe_selection_v9.json,
               research/audits/v9p/data_audit_v9.json,
               research/audits/v9p/t02_gate_v9.json).

Exit codes (documented contract):
  0  PASS    -- data present, audit ran, all three artifacts byte-reproduced
  1  FAIL    -- data present, audit ran, at least one artifact differs
  2  USAGE   -- bad arguments / unexpected internal error
  3  NOT_RUN_DATA_UNAVAILABLE -- expected host data absent (never a fake PASS)

Usage:
  python scripts/v9_universe_audit_tier_r.py [--out-dir DIR]

Output defaults to research/audits/v9_tier_r/ (never written into the
immutable historical locations).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.v9_universe_audit import (  # noqa: E402
    DEFAULT_TIER_R_OUT,
    real_descriptor,
    run_real_historical_audit,
)

EXIT_CODES = {"PASS": 0, "FAIL": 1, "NOT_RUN_DATA_UNAVAILABLE": 3}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Tier-R availability check + byte-reproduction of the V9 "
                    "universe audit (offline).")
    parser.add_argument(
        "--out-dir", default=str(DEFAULT_TIER_R_OUT),
        help="directory for run outputs / availability artifact "
             "(default: %(default)s)")
    args = parser.parse_args(argv)

    try:
        outcome = run_real_historical_audit(
            real_descriptor(repo_root=REPO_ROOT), out_dir=Path(args.out_dir))
    except Exception as exc:  # noqa: BLE001 - CLI boundary: report, exit 2
        print(f"Tier-R internal error: {type(exc).__name__}: {exc}",
              file=sys.stderr)
        return 2

    print("verdict:", outcome["verdict"])
    print("out_dir:", outcome["out_dir"])
    if outcome.get("availability_artifact_path"):
        print("availability_artifact:", outcome["availability_artifact_path"])
    for c in outcome.get("comparison", []):
        print(f"  {c['name']}: match={c['match']} "
              f"committed={c['committed_sha256']} run={c['run_sha256']}")
    return EXIT_CODES[outcome["verdict"]]


if __name__ == "__main__":
    raise SystemExit(main())
