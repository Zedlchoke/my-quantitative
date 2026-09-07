"""PLAN_stocks_v10 P0 build driver (A1).

Runs the timing/revision observable build against the hash-verified V9
panel. Fail-closed: aborts before any output if the panel sha256 does not
match the frozen pin. Streams both observable files (memory flat), computes
the coverage census (overall + per cohort class + per eff-year), and writes
the committed manifest with all hashes.

Usage (from the cycle worktree root):
  .venv/bin/python -m research.assets.stocks.p0_v10_build_driver
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

from research.assets.stocks.p0_v10_observables import (
    MIN_HIST_COHORT,
    MIN_HIST_OWN,
    SCHEMA,
    compute_observables,
    scan_groups,
    sha256_file,
)

V10 = Path(__file__).resolve().parents[3]  # this cycle's worktree root
PANEL = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v9/"
    "integration/.staging_sec_v9/multivintage_panel.jsonl"
)
PANEL_PIN = "67591464ee49acc159886143a379bda5890b1df602818b600d7938df92af1447"
COHORT = V10 / "research/control/stocks_free_v9_run/cohort_v9.json"
OUT_DIR = V10 / ".staging_sec_v10"
TIMING_OUT = OUT_DIR / "v10_timing_observables.jsonl"
REVISION_OUT = OUT_DIR / "v10_revision_observables.jsonl"
MANIFEST = V10 / "research/control/stocks_free_v10_run/p0_v10_observable_manifest.json"


def _class_map():
    d = json.loads(COHORT.read_text())
    m = {}
    for cls in ("ALIVE_EVIDENCED", "DEAD_EVIDENCED", "GAP_COVERAGE"):
        for mem in d["members"][cls]:
            m[mem["cik"]] = cls
    return m


def main() -> int:
    t0 = time.time()
    print(f"[p0] verifying panel sha256 before any output...", flush=True)
    measured = sha256_file(str(PANEL))
    if measured != PANEL_PIN:
        print(f"[p0] PANEL_SHA_MISMATCH measured={measured} pin={PANEL_PIN}")
        return 2
    print(f"[p0] panel pin MATCH ({measured[:16]}...), streaming...", flush=True)

    groups, sector, rows = scan_groups(str(PANEL))
    print(f"[p0] scan done rows={rows} groups={len(groups)} "
          f"({time.time()-t0:.0f}s)", flush=True)

    cls_map = _class_map()
    t_hash = hashlib.sha256()
    r_hash = hashlib.sha256()
    t_n = r_n = 0
    per_class_timing = Counter()
    per_class_own = Counter()
    per_class_cohort = Counter()
    per_class_revision = Counter()
    year_timing = Counter()
    year_revision = Counter()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tfh = open(TIMING_OUT, "wb", buffering=1 << 20)
    rfh = open(REVISION_OUT, "wb", buffering=1 << 20)

    def on_timing(row):
        nonlocal t_n
        b = (json.dumps(row, separators=(",", ":")) + "\n").encode()
        t_hash.update(b)
        tfh.write(b)
        t_n += 1
        cls = cls_map.get(row["e"], "UNCLASSIFIED")
        per_class_timing[cls] += 1
        if row["own_z"] is not None:
            per_class_own[cls] += 1
        if row["cohort_z"] is not None:
            per_class_cohort[cls] += 1
        year_timing[row["eff"][:4]] += 1

    def on_revision(row):
        nonlocal r_n
        b = (json.dumps(row, separators=(",", ":")) + "\n").encode()
        r_hash.update(b)
        rfh.write(b)
        r_n += 1
        cls = cls_map.get(row["e"], "UNCLASSIFIED")
        per_class_revision[cls] += 1
        year_revision[row["eff"][:4]] += 1

    census = compute_observables(
        groups, sector, on_timing=on_timing, on_revision=on_revision
    )
    tfh.close()
    rfh.close()
    print(f"[p0] compute done timing={t_n} revision={r_n} "
          f"({time.time()-t0:.0f}s)", flush=True)

    manifest = {
        "schema": SCHEMA,
        "built_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "producer_role": "A1 (PLAN_stocks_v10 sec3 P0)",
        "inputs": {
            "panel_path": str(PANEL),
            "panel_sha256_pin": PANEL_PIN,
            "panel_sha256_measured": measured,
            "panel_pin_verified": True,
            "cohort_path": str(COHORT.relative_to(V10)),
            "cohort_sha256": sha256_file(str(COHORT)),
        },
        "frozen_parameters": {
            "min_hist_own": MIN_HIST_OWN,
            "min_hist_cohort": MIN_HIST_COHORT,
            "scale": "1.4826 * MAD",
            "own_norm_rule": "median over same-filer same-period-type groups "
                             "with eff' < eff AND first_avail' <= first_avail_E",
            "cohort_norm_rule": "median over same-sector same-period-type "
                                "groups with first_avail' < first_avail_E "
                                "(strict; same-day excluded fail-closed)",
            "row_order": "panel insertion order (deterministic)",
        },
        "outputs": {
            "timing_path": str(TIMING_OUT.relative_to(V10)),
            "timing_rows": t_n,
            "timing_sha256": t_hash.hexdigest(),
            "revision_path": str(REVISION_OUT.relative_to(V10)),
            "revision_rows": r_n,
            "revision_sha256": r_hash.hexdigest(),
            "committed": False,
            "commit_rule": "derived artifacts stay gitignored; only hashes "
                           "and the census are committed",
        },
        "census": census,
        "coverage_census": {
            "per_class_timing_rows": dict(sorted(per_class_timing.items())),
            "per_class_own_z_computable": dict(sorted(per_class_own.items())),
            "per_class_cohort_z_computable": dict(sorted(per_class_cohort.items())),
            "per_class_revision_rows": dict(sorted(per_class_revision.items())),
            "timing_rows_by_eff_year": dict(sorted(year_timing.items())),
            "revision_rows_by_eff_year": dict(sorted(year_revision.items())),
        },
        "deadline_distance": {
            "status": "DATA_BLOCKED_VALID",
            "note": "no sourced filer-category deadline evidence exists in "
                    "the staged data; never asserted (P-1). Any deadline-"
                    "distance proposal must first wire sourced evidence.",
        },
        "taxonomy_appendix": {
            "carried_from": "stocks_free_v9_run p0a death census v4 class "
                            "table (12B/12G union span) — unchanged per plan",
            "authority": "research/control/stocks_free_v9_run/"
                         "p0a_v9_death_census_raw_manifest.json",
        },
    }
    MANIFEST.write_text(json.dumps(manifest, indent=1) + "\n")
    print(f"[p0] manifest written {MANIFEST} total {time.time()-t0:.0f}s",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
