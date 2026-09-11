#!/usr/bin/env python
"""FOREX-NG3 D2 measurement runner (novelty / feasibility /
identifiability).  NO expectancy, PnL or profit factor is computed
anywhere in this runner; the only cross-book quantities are Spearman
rho between signed exposure schedules, event/decision counts, and cost
ceilings under the REFERENCED proxy ladder (1.5 bps/side, tier 2.0 --
Q-8 measured constants NOT_YET_MEASURED by this cycle's P1 kernel lane,
so the proposal-law cost verdict stays NOT_RUN fail-closed).

Measured (P-12: code AND representation commit together, before any
number is cited):

1. NOVELTY -- pooled max |rho| of each proposal's anchor schedule vs a
   27-shape veto panel: the ng1 25-shape panel rebuilt verbatim from
   the ng1 D2 builders (8 committed FXFV8 shapes + V4 commodity bloc +
   2 committed FXFV7 books + 2 spillover rebuilds + 4 lead-lag rebuilds
   + 8 generics) PLUS the 2 kill-candidate shapes declared by the ng3
   proposals: the FXNG1-A5-P1 release-order shadow and the FXNG1-A4-P2
   acceleration shadow, rebuilt from the committed ng1 D1 proposal
   identities on the pinned ng1 census.  Bar 0.20, margins recorded
   (P-2).  Intra-ng3 cross-proposal collapse (A4-P1 vs A4-P2, A5-P1 vs
   A5-P2) measured and disclosed for the S selection rubric.
2. FEASIBILITY -- Q-6 recent (last 24 calendar months of S0): A4 floor
   >= 15 restricted CA events; A5-P1 floor >= 6 differential months;
   A5-P2 floor >= 2 transfer events; A4-P2 R0 empty-book rule of its
   own proposal (material |R| >= 1e-4 count; 0 in-window fires => lane
   dies pre-score).  Totals re-measured against the D1 declarations;
   turnover/cost ceilings referenced (proxy ladder).
3. IDENTIFIABILITY -- CTL-V7NODIFF vs the A5 anchors (pooled
   max |rho| >= 0.98 => kill pre-score; Q-11 null-validity recorded)
   and A4 nominal separability vs the committed FXFV8 DGS10-level
   shapes PLUS the exact-spec CTL-DGS10LEVEL z252 shape built from the
   pinned DGS10 vintaged bytes (P-13 chain verified at P0).

Outputs (committed with the code):
- research/control/forex_ng3_run/d2/d2_novelty_panel_ng3.json
- research/control/forex_ng3_run/d2/d2_feasibility_ng3.json
- research/control/forex_ng3_run/d1/feasibility/feasibility_summary.json

Usage:
    .venv/bin/python research/control/forex_ng3_run/d2/d2_run.py
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import date, datetime, timezone

WORKTREE = "/Users/hoangminhlong/my-quantitative/.worktrees/forex-ng3/d2"
if WORKTREE not in sys.path:
    sys.path.insert(0, WORKTREE)

from research.assets.forex_ng1 import plane_adapter as pa   # noqa: E402
from research.assets.forex_ng1 import spot_series as ss     # noqa: E402
from research.assets.forex_ng1.d2 import books as B         # noqa: E402
from research.assets.forex_ng1.d2 import events as E        # noqa: E402
from research.assets.forex_ng1.d2 import rho as R           # noqa: E402
from research.assets.forex_ng1.d2.series import (           # noqa: E402
    ECONOMY_SERIES, VintagedSeries, parse_realtime_observations,
)
from research.assets.forex_ng2 import revision_series as ng2  # noqa: E402
from research.assets.forex_ng3 import revision_series as rs   # noqa: E402
from research.assets.forex_ng3.d2 import books as N3         # noqa: E402

# --------------------------------------------------------------------------- #
# pinned inputs (READ-ONLY; every digest recorded in the outputs)
# --------------------------------------------------------------------------- #

CADS_ROOT = pa.DEFAULT_CADS_STORE_ROOT
US_RT_CADS_ADDRESS = (
    "7f18ec982374ce4dfb235f53f001327793df8e1c0077d31206de25aa3455ac94")
V9_ROOT = ("/Users/hoangminhlong/my-quantitative/.worktrees/"
           "forex-free-v9/integration")            # READ-ONLY inheritance
VINTAGED_DIR = os.path.join(V9_ROOT, "data_raw/forex_free_v9_cpi")
V8_EVIDENCE_PATH = os.path.join(
    V9_ROOT, "research/control/forex_free_v8_run/d2/evidence/"
             "schedule_cells_proposals_v8.json")
V7_ANCESTORS_PATH = os.path.join(
    V9_ROOT, "research/control/forex_free_v7_run/d2/a7_novelty/"
             "evidence/schedule_cells_ancestors.json")
V7_PROPOSALS_PATH = os.path.join(
    V9_ROOT, "research/control/forex_free_v7_run/"
             "a7_prelaunch_evidence_r2/novelty_rerun_evidence/"
             "schedule_cells_proposals_v7.json")

NG1_CENSUS_PATH = os.path.join(
    WORKTREE, "research/control/forex_ng1_run/p0_announcement_census.json")
NG3_CENSUS_PATH = os.path.join(
    WORKTREE, "research/control/forex_ng3_run/p0_revision_census.json")
NG3_CENSUS_SHA_PIN = ("0fc108631e6b4bb2111c3528b873e68505ab2b46247d5e39cb"
                      "a24a12ff35017f")
SPOT_MANIFEST_PATH = os.path.join(
    WORKTREE, "research/control/forex_ng1_run/p1_spot/spot_pin_manifest.json")
GRID_LAW_DAYS = 1842
S0_WINDOW = (date(2018, 4, 4), date(2025, 4, 30))

DGS10_SOURCE_PATH = (
    "/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v8/"
    "integration/research/control/forex_free_v8_run/staged_vintaged/"
    "DGS10.json")
DGS10_SHA_PIN = ("03dde429ba022e6d011ae3a61323124e38c5a3fac888b492823406a"
                 "51c4c4aa0")

#: The four ng3 D1 proposals are the frozen P-12 measurement contracts.
#: A5 lives in this worktree; A4 was committed on the d1-a4 lane branch
#: (substance commit fde6228) and is read from the git object store
#: (read-only; sha256-of-bytes pinned, fail-closed on drift).
PROPOSAL_SPECS = {
    "FXNG3-A4-P1": {
        "git_show": ("fde62283299413b15d5a042d173f829638350677:"
                     "research/control/forex_ng3_run/d1/proposals/"
                     "proposal_A4_P1.json"),
        "sha256": ("6fe38d85468c1326c746327d94a2fa02b954b6cf92ab945f6bf43"
                   "37e6d4562d6"),
    },
    "FXNG3-A4-P2": {
        "git_show": ("fde62283299413b15d5a042d173f829638350677:"
                     "research/control/forex_ng3_run/d1/proposals/"
                     "proposal_A4_P2.json"),
        "sha256": ("f987575b081ab51463d5faf162487897aeb38566afdd5e0b3095c"
                   "c01a73f4456"),
    },
    "FXNG3-A5-P1": {
        "path": "research/control/forex_ng3_run/d1/proposals/"
                "proposal_A5_P1.json",
    },
    "FXNG3-A5-P2": {
        "path": "research/control/forex_ng3_run/d1/proposals/"
                "proposal_A5_P2.json",
    },
}

OUT_NOVELTY = os.path.join(
    WORKTREE, "research/control/forex_ng3_run/d2/d2_novelty_panel_ng3.json")
OUT_FEAS = os.path.join(
    WORKTREE, "research/control/forex_ng3_run/d2/d2_feasibility_ng3.json")
OUT_FEAS_SUMMARY = os.path.join(
    WORKTREE, "research/control/forex_ng3_run/d1/feasibility/"
              "feasibility_summary.json")

CODE_FILES = [
    "research/assets/forex_ng3/d2/__init__.py",
    "research/assets/forex_ng3/d2/books.py",
    "research/control/forex_ng3_run/d2/d2_run.py",
    "tests/test_forex_ng3_d2.py",
]

#: D1-declared counts (re-measured and compared; declared values cite
#: the committed proposals, sha256-pinned in the novelty output).
DECLARED = {
    "FXNG3-A4-P1": {
        "restricted_events": 72, "recent_24m_events": 17,
        "v2_year_clusters": {"2018": 8, "2022": 47, "2024": 17},
    },
    "FXNG3-A4-P2": {
        "restricted_events": 72, "recent_24m_events": 17,
        "material_fired_count": "BLIND_BY_DECLARATION (R0 measured here)",
    },
    "FXNG3-A5-P1": {
        "differential_months": 72,
        "non_anchor_months_without_ca": 15,
        "active_leg_month_counts": {"US": 70, "AU": 22, "NZ": 22, "GB": 8},
        "month_composition": {"US": 44, "GB": 2, "GB,US": 4,
                              "AU,GB,NZ,US": 2, "AU,NZ,US": 20},
        "q6_months_obs_basis": 7,
    },
    "FXNG3-A5-P2": {
        "transfer_events_total": 52,
        "transfer_events_by_leg": {"GB": 8, "AU": 22, "NZ": 22},
        "transfer_events_by_year": {"2017": 2, "2018": 12, "2019": 8,
                                    "2020": 8, "2021": 8, "2022": 8,
                                    "2023": 6},
        "q6_transfer_events_obs_basis": 2,
    },
}


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json(path: str, payload: dict) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1)
        fh.write("\n")
    return sha256_file(path)


def load_proposal(pid: str) -> tuple[dict, str]:
    """Load one ng3 D1 proposal (tree path or git object store) + sha."""
    spec = PROPOSAL_SPECS[pid]
    if "path" in spec:
        path = os.path.join(WORKTREE, spec["path"])
        with open(path, "rb") as fh:
            raw = fh.read()
    else:
        commit, rel = spec["git_show"].split(":", 1)
        raw = subprocess.run(
            ["git", "-C", WORKTREE, "show", f"{commit}:{rel}"],
            capture_output=True, check=True).stdout
    digest = hashlib.sha256(raw).hexdigest()
    if spec.get("sha256") and digest != spec["sha256"]:
        raise SystemExit(f"proposal {pid} sha drift: {digest}")
    return json.loads(raw.decode("utf-8")), digest


# --------------------------------------------------------------------------- #
# 1. pinned inputs
# --------------------------------------------------------------------------- #

def load_pinned_inputs() -> dict:
    prov: dict = {}

    # ng3 P0 restricted census artifact (verify-on-read sha pin)
    ng3_sha = sha256_file(NG3_CENSUS_PATH)
    if ng3_sha != NG3_CENSUS_SHA_PIN:
        raise SystemExit(f"ng3 census sha drift: {ng3_sha}")
    ng3_census = json.load(open(NG3_CENSUS_PATH, encoding="utf-8"))
    prov["ng3_census"] = {"path": NG3_CENSUS_PATH, "sha256": ng3_sha}

    # ng1 announcement census (kill shadows + V7 rebuilds input)
    ng1_census = E.load_census(NG1_CENSUS_PATH)
    prov["ng1_census"] = {"path": NG1_CENSUS_PATH,
                          "sha256": E.CENSUS_SHA256_PIN}

    # spot: verify-on-read resolve + grid 1842 recompute (P0 law)
    manifest = ss.load_pin_manifest(SPOT_MANIFEST_PATH)
    first_entry = next(iter(manifest["files"].values()))
    spot_data_dir = os.path.dirname(first_entry["copy_path_absolute"])
    serieses = ss.resolve_all_pairs(SPOT_MANIFEST_PATH, spot_data_dir)
    grid = ss.common_weekday_grid(serieses, S0_WINDOW[0], S0_WINDOW[1])
    if len(grid) != GRID_LAW_DAYS:
        raise SystemExit(f"grid recompute mismatch: {len(grid)}")
    prov["spot"] = {
        "manifest_path": SPOT_MANIFEST_PATH,
        "data_dir": spot_data_dir,
        "resolved_sha256": {p: s.sha256 for p, s in serieses.items()},
        "bars": {p: s.bars for p, s in serieses.items()},
        "grid_days": len(grid),
        "verify_on_read": "PASS (SpotIntegrityError would have raised)",
    }

    # vintaged CPI legs: S2 manifest via CADS (GRANTED gate), staging
    # bytes verified against the manifest pins (P0 pattern)
    registry = pa.load_registry()
    ga4 = pa.ga4_granted()
    s2_manifest = pa.consume_s2_manifest(CADS_ROOT, registry, ga4)
    us_object = os.path.join(CADS_ROOT, "objects",
                             US_RT_CADS_ADDRESS[:2], US_RT_CADS_ADDRESS)
    local_paths = {
        rec["file"]: os.path.join(VINTAGED_DIR, name)
        for name, rec in s2_manifest["series"].items()
        if rec["file"].startswith("fred_vintaged/")
        for name in [rec["file"]]
    }
    local_paths["US/fred_cpiaucsl_rt.json"] = us_object
    verify = pa.verify_s2_files(s2_manifest, local_paths)
    failed = [k for k, v in verify.items() if not v["match"]]
    if failed:
        raise SystemExit(f"vintaged leg sha mismatch: {failed}")
    prov["vintaged"] = {
        "s2_manifest_address": pa.S2_PINNED_ADDRESS,
        "staging_root": VINTAGED_DIR,
        "verify": {k: {"file": v["file"], "pinned_sha256": v["pinned_sha256"],
                       "match": v["match"]}
                   for k, v in verify.items()},
    }

    # ng2 VintageRow streams (restricted builders) + ng1 VintagedSeries
    # legs (kill shadows / V7 rebuilds) from the SAME pinned bytes
    rows_by_eco: dict[str, list] = {}
    series_by_eco: dict[str, VintagedSeries] = {}
    for eco, series_id in ECONOMY_SERIES.items():
        rel = s2_manifest["series"][series_id]["file"]
        path = (us_object if rel.startswith("US/")
                else os.path.join(VINTAGED_DIR, rel))
        payload = json.load(open(path, "rb"))
        observations = (payload["observations"]
                        if isinstance(payload, dict) else payload)
        rows_by_eco[eco] = pa.parse_fred_vintaged(observations)
        series_by_eco[eco] = VintagedSeries(
            series_id=series_id,
            rows=parse_realtime_observations(observations))
    prov["vintaged"]["spacing"] = {
        eco: vs.spacing for eco, vs in series_by_eco.items()}

    # DGS10 pinned bytes (P-13 chain verified at P0; re-hash here)
    dgs10_sha = sha256_file(DGS10_SOURCE_PATH)
    if dgs10_sha != DGS10_SHA_PIN:
        raise SystemExit(f"DGS10 bytes sha drift: {dgs10_sha}")
    dgs10_payload = json.load(open(DGS10_SOURCE_PATH, "rb"))
    dgs10_rows = pa.parse_fred_vintaged(dgs10_payload)
    prov["dgs10"] = {"path": DGS10_SOURCE_PATH, "sha256": dgs10_sha,
                     "rows": len(dgs10_rows),
                     "note": "P-13 pin chain (V8 run-contract -> staged "
                             "manifest -> DGS10.json) verified at ng3 P0; "
                             "bytes re-hashed here (verify-on-read)"}

    # committed ancestor evidence (READ-ONLY inheritance)
    v8_books, v8_prov = B.load_committed_cells(V8_EVIDENCE_PATH)
    v7a_books, v7a_prov = B.load_committed_cells(V7_ANCESTORS_PATH)
    v7p_books, v7p_prov = B.load_committed_cells(V7_PROPOSALS_PATH)
    prov["committed_evidence"] = {
        "v8_proposals": v8_prov, "v7_ancestors": v7a_prov,
        "v7_proposals_rerun": v7p_prov,
    }

    # the four D1 proposals (frozen P-12 representation identities)
    proposals = {}
    for pid in PROPOSAL_SPECS:
        prop, digest = load_proposal(pid)
        proposals[pid] = {
            "hypothesis_id": prop["hypothesis_id"],
            "representation_id":
                prop["representation_identity"]["representation_id"],
            "identity_fields": prop["representation_identity"][
                "identity_fields"],
            "source": PROPOSAL_SPECS[pid].get(
                "path",
                "git:" + PROPOSAL_SPECS[pid].get("git_show", "?")),
            "sha256": digest,
        }
    prov["proposals"] = proposals

    return {"ng3_census": ng3_census, "ng1_census": ng1_census,
            "grid": grid, "serieses": serieses,
            "rows_by_eco": rows_by_eco, "series_by_eco": series_by_eco,
            "dgs10_rows": dgs10_rows, "provenance": prov,
            "committed": {"v8": v8_books, "v7a": v7a_books,
                          "v7p": v7p_books}}


# --------------------------------------------------------------------------- #
# 2. restricted streams + join (re-measured, census-reconciled)
# --------------------------------------------------------------------------- #

def build_streams(env: dict) -> dict:
    streams = {}
    for eco, rows in env["rows_by_eco"].items():
        streams[eco] = rs.build_restricted_stream(eco, rows)
    restricted = {e: s["restricted"] for e, s in streams.items()}
    census_counts = env["ng3_census"]["legs"]
    recon = {}
    for eco in sorted(restricted):
        declared = census_counts[eco]["restricted_events"]
        recon[eco] = {"census": declared, "d2_rebuild": len(restricted[eco]),
                      "match": declared == len(restricted[eco])}
        if not recon[eco]["match"]:
            raise SystemExit(f"restricted rebuild != P0 census for {eco}: "
                             f"{recon[eco]}")
    diff = rs.restricted_differential_months(restricted)
    lookup = N3.month_event_lookup(restricted)
    transfer_events = [(m, leg) for m in diff["sorted_month_keys"]
                       for leg in diff["months"][m][1:] if leg in N3.LEG_PAIR]
    return {"restricted": restricted, "diff": diff, "lookup": lookup,
            "transfer_events": transfer_events, "reconciliation": recon}


# --------------------------------------------------------------------------- #
# 3. books (anchors, controls, veto panel)
# --------------------------------------------------------------------------- #

def build_all_books(env: dict, streams: dict) -> dict:
    grid = env["grid"]
    grid_index = {d: i for i, d in enumerate(grid)}
    grid_iso = [d.isoformat() for d in grid]
    window_end = S0_WINDOW[1]
    restricted = streams["restricted"]
    diff = streams["diff"]
    lookup = streams["lookup"]

    a4p1 = N3.build_ng3_a4_book("FXNG3-A4-P1-ANCHOR", "sign",
                                restricted["CA"], grid, grid_index,
                                window_end, hold=5)
    a4p2 = N3.build_ng3_a4_book("FXNG3-A4-P2-ANCHOR", "material",
                                restricted["CA"], grid, grid_index,
                                window_end, material_threshold=1e-4,
                                hold=10)
    a5p1 = N3.build_ng3_a5p1_book("FXNG3-A5-P1-ANCHOR", "anchor",
                                  diff["months"], lookup, grid, grid_index,
                                  window_end, gate_pp=0.02, hold=5)
    a5p1_ctl = N3.build_ng3_a5p1_book("FXNG3-A5-P1-CTL-V7NODIFF",
                                      "v7nodiff", diff["months"], lookup,
                                      grid, grid_index, window_end,
                                      gate_pp=0.02, hold=5)
    a5p2 = N3.build_ng3_a5p2_book("FXNG3-A5-P2-ANCHOR", "anchor",
                                  streams["transfer_events"], lookup,
                                  grid, grid_index, window_end,
                                  gate_pp=0.02, hold=5)
    a5p2_ctl = N3.build_ng3_a5p2_book("FXNG3-A5-P2-CTL-V7NODIFF",
                                      "v7nodiff", streams["transfer_events"],
                                      lookup, grid, grid_index, window_end,
                                      gate_pp=0.02, hold=5)

    # A4 exact-spec CTL-DGS10LEVEL shapes on each anchor's fired days
    levels = N3.dgs10_grid_levels(env["dgs10_rows"], grid)
    dgs10_a4p1 = N3.dgs10_z252_book("FXNG3-A4-P1-CTL-DGS10LEVEL-EXACT",
                                    a4p1, levels, grid, grid_index, hold=5)
    dgs10_a4p2 = N3.dgs10_z252_book("FXNG3-A4-P2-CTL-DGS10LEVEL-EXACT",
                                    a4p2, levels, grid, grid_index, hold=10)

    # ng1 kill shadows (declared kill candidates): rebuilt VERBATIM from
    # the committed ng1 D1 proposal identities + the pinned ng1 census
    ng1_events = E.first_release_events(env["ng1_census"])
    state = E.order_state(ng1_events)
    kill_a5p1 = B.build_a5p1_book("FXNG1-A5-P1-release-order-shadow",
                                  "anchor", state, env["series_by_eco"],
                                  grid, grid_index, window_end,
                                  threshold=0.10, hold=5)
    kill_a4p2 = B.build_a4_book("FXNG1-A4-P2-acceleration-shadow",
                                "s2_trailing_yoy", 0.15, ng1_events,
                                env["series_by_eco"], grid, grid_index,
                                window_end, hold=5)

    # the ng1 25-shape panel, rebuilt with the ng1 builders unmodified
    closes = {p: s.closes for p, s in env["serieses"].items()}
    v8_names = ["FXFV8-A5-P1-anchor", "FXFV8-A5-P1-neighbour-z504",
                "FXFV8-A5-P1-control-dgs10",
                "FXFV8-A4-P2-neighbour-sham7d", "FXFV8-A4-P2-anchor",
                "FXFV8-A4-P2-control-dgs10", "FXFV8-A4-P1-anchor",
                "FXFV8-A4-P1-control-dgs10"]
    panel: dict[str, dict] = {}
    for n in v8_names:
        if n in env["committed"]["v8"]:
            panel[n] = env["committed"]["v8"][n]
    panel["V4_commodity_bloc_exposure"] = env["committed"]["v7a"][
        "V4_commodity_bloc_exposure"]
    panel["FXFV7-A4-P1_anchor_k4_committed"] = env["committed"]["v7p"][
        "FXFV7-A4-P1_anchor_k4"]
    panel["FXFV7-A6-P2_anchor_q80_committed"] = env["committed"]["v7p"][
        "FXFV7-A6-P2_anchor_q80"]
    panel.update(B.build_v7_spillover_shadows(
        ng1_events, env["series_by_eco"], grid, grid_index, window_end))
    panel.update(B.build_v7_leadlag_shadows(closes, grid, grid_index))
    panel.update(B.build_generic_shapes(closes, grid, grid_index))
    ng1_panel_names = sorted(panel)
    panel["FXNG1-A5-P1-release-order-shadow"] = kill_a5p1
    panel["FXNG1-A4-P2-acceleration-shadow"] = kill_a4p2

    return {"anchors": {"FXNG3-A4-P1": a4p1, "FXNG3-A4-P2": a4p2,
                        "FXNG3-A5-P1": a5p1, "FXNG3-A5-P2": a5p2},
            "ident_controls": {"FXNG3-A5-P1": a5p1_ctl,
                               "FXNG3-A5-P2": a5p2_ctl},
            "dgs10_exact": {"FXNG3-A4-P1": dgs10_a4p1,
                            "FXNG3-A4-P2": dgs10_a4p2},
            "kill_shadows": {"FXNG1-A5-P1-release-order-shadow": kill_a5p1,
                             "FXNG1-A4-P2-acceleration-shadow": kill_a4p2},
            "panel": panel, "ng1_panel_names": ng1_panel_names,
            "grid_iso": grid_iso, "state": state}


# --------------------------------------------------------------------------- #
# 4. novelty panel
# --------------------------------------------------------------------------- #

def novelty_panel(env: dict, built: dict) -> dict:
    anchors = built["anchors"]
    grid_iso = built["grid_iso"]
    panel = built["panel"]
    results = {}
    for pid, anchor in anchors.items():
        comparisons = {}
        for vname, veto in panel.items():
            comparisons[vname] = R.compare_schedules(
                anchor["cells"], veto["cells"], grid_iso,
                list(B.FUNDED_PAIRS))
        pooled = R.pooled_max_abs_rho(comparisons)
        margins = {}
        for row in pooled["rows"]:
            r = row["max_abs_rho"]
            margins[row["veto"]] = (None if r is None
                                    else round(N3.NOVELTY_BAR - r, 4))
        kill_rows = {k: comparisons[k] for k in built["kill_shadows"]}
        results[pid] = {
            "anchor_active_cells": anchor["meta"]["active_cells"],
            "pooled": pooled,
            "margins_to_bar": margins,
            "kill_candidate_shapes": {
                k: {"max_abs_rho": v.get("max_abs_rho"),
                    "verdict": v.get("verdict")} for k, v in kill_rows.items()},
            "per_veto": comparisons,
        }

    # intra-ng3 cross-proposal collapse (disclosure for the S rubric)
    cross = {}
    for pid_a, pid_b in (("FXNG3-A4-P1", "FXNG3-A4-P2"),
                         ("FXNG3-A5-P1", "FXNG3-A5-P2")):
        cmp = R.compare_schedules(anchors[pid_a]["cells"],
                                  anchors[pid_b]["cells"], grid_iso,
                                  list(B.FUNDED_PAIRS))
        cross[f"{pid_a}_vs_{pid_b}"] = cmp

    return {"bar": N3.NOVELTY_BAR,
            "panel_names": sorted(panel),
            "ng1_panel_names": built["ng1_panel_names"],
            "added_kill_candidate_shapes": sorted(built["kill_shadows"]),
            "results": results,
            "cross_proposal_collapse": cross,
            "method": {
                "representation": "signed exposure cells date|pair on the "
                                  "frozen daily 16:00-NY common grid (1842 "
                                  "days 2018-04-04..2025-04-30); exposure "
                                  "cells i..i+H-1; netting sign-of-sum",
                "variants": ["cellwise_signed_full_grid",
                             "cellwise_union_active",
                             "netsigned_union_dates_shared_pairs"],
                "rho": "Spearman, average-tie ranks, |rho| pooled max "
                       "over panel x variants; global sign flips of a "
                       "shape leave |rho| unchanged",
                "shared_pairs": list(B.FUNDED_PAIRS),
                "panel_composition": "25 ng1 shapes rebuilt with the ng1 "
                                     "D2 builders unmodified (8 committed "
                                     "FXFV8 + V4 commodity bloc + 2 "
                                     "committed FXFV7 + 2 spillover "
                                     "rebuilds + 4 lead-lag rebuilds + 8 "
                                     "generics) + 2 declared kill "
                                     "candidates (FXNG1-A5-P1 release "
                                     "order, FXNG1-A4-P2 acceleration) "
                                     "rebuilt from the committed ng1 D1 "
                                     "proposal identities",
            }}


# --------------------------------------------------------------------------- #
# 5. feasibility + identifiability + verdicts
# --------------------------------------------------------------------------- #

COST_BPS_PER_SIDE = 1.5
COST_TIER = 2.0


def a9f_ceiling(book: dict, years: float, hold_key: str = "fired_events"
                ) -> dict:
    m = book["meta"]
    if hold_key in m:
        fired = m[hold_key]
    else:
        fired = m.get("events_gate_passed", 0)
    fills = 2 * fired
    per_side = COST_BPS_PER_SIDE * COST_TIER
    return {
        "ladder": "REFERENCED proxy 1.5 bps/side, stress tier 2.0 "
                  "(V2/V8 precedent; Q-8 measured constants "
                  "NOT_YET_MEASURED by the P1 kernel lane -> the "
                  "proposal-law cost verdict stays NOT_RUN fail-closed)",
        "fired_positions": fired,
        "total_fills": fills,
        "cost_bps_per_side_referenced": per_side,
        "cost_bps_round_trip_per_position": 2 * per_side,
        "total_cost_ceiling_bps_per_unit_notional": fills * per_side,
        "fired_positions_per_year": (round(fired / years, 3)
                                     if years else None),
        "holds_grid_days": m.get("hold_grid_days"),
    }


def identifiability(built: dict) -> dict:
    grid_iso = built["grid_iso"]
    out = {"kill_bar": N3.IDENTIFIABILITY_KILL, "results": {}}
    for pid, control in built["ident_controls"].items():
        anchor = built["anchors"][pid]
        cmp = R.compare_schedules(anchor["cells"], control["cells"],
                                  grid_iso, list(B.FUNDED_PAIRS))
        r = cmp.get("max_abs_rho")
        anchor_signs = {s: list(anchor["cells"].values()).count(s)
                        for s in (1, -1)}
        ctl_signs = {s: list(control["cells"].values()).count(s)
                     for s in (1, -1)}
        if r is None:
            validity = (
                "UNMEASURABLE (Spearman undefined: a constant vector -- "
                f"anchor signs {anchor_signs}, control signs {ctl_signs}, "
                f"verdict {cmp.get('verdict')}): the D2 identifiability "
                "kill CANNOT fire on an unmeasurable rho (NOT_RUN "
                "semantics, never an inferred PASS); the scored-phase R2 "
                "falsification (CTL-V7NODIFF same-sign expectancy >= 0.5x "
                "anchor) remains fully binding")
        elif r >= N3.IDENTIFIABILITY_KILL:
            validity = (
                "control null INVALID for differential-state inference at "
                f"rho={round(r, 4)} >= {N3.IDENTIFIABILITY_KILL}: the "
                "absolute-revision form reproduces the anchor schedule, "
                "so a scored null on the anchor could not be attributed "
                "to the differential construction")
        else:
            validity = (f"control null valid at rho={round(r, 4)} < "
                        f"{N3.IDENTIFIABILITY_KILL}: anchor and "
                        "no-differential form are schedule-separable")
        entry = {"control": "CTL-V7NODIFF", "comparison": cmp,
                 "control_vs_anchor_max_abs_rho": r,
                 "anchor_sign_counts": anchor_signs,
                 "control_sign_counts": ctl_signs,
                 "kill_pre_score": bool(r is not None
                                        and r >= N3.IDENTIFIABILITY_KILL),
                 "q11_null_validity": validity}
        out["results"][pid] = entry

    committed_dgs10 = [
        ("FXFV8-A5-P1-control-dgs10", built["panel"][
            "FXFV8-A5-P1-control-dgs10"]),
        ("FXFV8-A4-P1-control-dgs10", built["panel"][
            "FXFV8-A4-P1-control-dgs10"]),
        ("FXFV8-A4-P2-control-dgs10", built["panel"][
            "FXFV8-A4-P2-control-dgs10"]),
    ]
    for pid in ("FXNG3-A4-P1", "FXNG3-A4-P2"):
        anchor = built["anchors"][pid]
        entry = {"nominal_separability": {}, "exact_spec_ctl_dgs10": {}}
        worst = None
        for name, shape in committed_dgs10:
            cmp = R.compare_schedules(anchor["cells"], shape["cells"],
                                      grid_iso, list(B.FUNDED_PAIRS))
            entry["nominal_separability"][name] = {
                "max_abs_rho": cmp.get("max_abs_rho"),
                "verdict": cmp.get("verdict")}
            r = cmp.get("max_abs_rho")
            if r is not None and (worst is None or r > worst):
                worst = r
        entry["nominal_separability_max_abs_rho"] = worst
        exact = built["dgs10_exact"][pid]
        cmp = R.compare_schedules(anchor["cells"], exact["cells"],
                                  grid_iso, list(B.FUNDED_PAIRS))
        entry["exact_spec_ctl_dgs10"] = {
            "comparison": cmp,
            "meta": exact["meta"],
            "note": "exact-spec CTL-DGS10LEVEL (trailing 252-grid-day "
                    "median of the pinned vintaged DGS10 level, as-of "
                    "reads, sign = +1 long USDCAD iff below median) on "
                    "the anchor's own fired days; P-13 chain bytes "
                    "(03dde429...) re-hashed by this runner",
        }
        out["results"][pid] = entry
    return out


def feasibility(env, streams, built, novelty) -> dict:
    anchors = built["anchors"]
    grid = env["grid"]
    s0_years = (S0_WINDOW[1] - S0_WINDOW[0]).days / 365.25
    restricted = streams["restricted"]
    diff = streams["diff"]

    ca_events = restricted["CA"]
    ca_recent = rs.restricted_recent_events(ca_events)
    a4_q6 = N3.evaluate_q6_floor(ca_recent["count"], N3.A4_Q6_FLOOR)
    a5p1_meta = anchors["FXNG3-A5-P1"]["meta"]
    a5p2_meta = anchors["FXNG3-A5-P2"]["meta"]
    a5p1_q6 = N3.evaluate_q6_floor(a5p1_meta["recent_months_obs_basis"],
                                   N3.A5P1_Q6_FLOOR)
    a5p2_q6 = N3.evaluate_q6_floor(a5p2_meta["recent_events_obs_basis"],
                                   N3.A5P2_Q6_FLOOR)

    a4p1_meta = anchors["FXNG3-A4-P1"]["meta"]
    a4p2_meta = anchors["FXNG3-A4-P2"]["meta"]
    v2_year_counts: Counter = Counter(
        e.v2_realtime_start[:4] for e in ca_events)
    material_recent = a4p2_meta["recent_material_fired"]

    # measured composition: leg-set -> month count (declared labels map
    # disclosed: "CA_plus_X_only"/"CA_plus_A_B" proposal strings)
    comp: Counter = Counter()
    for mth in diff["sorted_month_keys"]:
        comp[",".join(sorted(diff["months"][mth][1:]))] += 1
    transfer_by_leg: Counter = Counter(
        leg for _, leg in streams["transfer_events"])
    transfer_by_year: Counter = Counter(
        m[:4] for m, _ in streams["transfer_events"])

    measured_totals = {
        "FXNG3-A4-P1": {
            "restricted_events": len(ca_events),
            "recent_24m_events": ca_recent["count"],
            "v2_year_clusters": dict(sorted(v2_year_counts.items())),
            "fired_events": a4p1_meta["fired_events"],
            "events_in_window": a4p1_meta["events_in_window"],
            "dropped_tail_entries": a4p1_meta["dropped_tail_entries"],
        },
        "FXNG3-A4-P2": {
            "restricted_events": len(ca_events),
            "recent_24m_events": ca_recent["count"],
            "material_fired_events": a4p2_meta["fired_events"],
            "material_below_threshold": a4p2_meta[
                "below_material_threshold"],
            "material_recent_fired": material_recent,
            "material_fired_v2_year_counts": a4p2_meta[
                "fired_v2_year_counts"],
            "dropped_tail_entries": a4p2_meta["dropped_tail_entries"],
        },
        "FXNG3-A5-P1": {
            "differential_months": diff["total"],
            "non_anchor_months_without_ca":
                diff["non_anchor_months_without_anchor_count"],
            "active_leg_month_counts": a5p1_meta[
                "active_leg_month_counts"],
            "month_composition": dict(sorted(comp.items())),
            "q6_months_obs_basis": a5p1_meta["recent_months_obs_basis"],
            "months_gate_passed": a5p1_meta["months_gate_passed"],
            "months_gate_failed": a5p1_meta["months_gate_failed"],
            "months_failed_closed": a5p1_meta["months_failed_closed"],
            "dropped_tail_entries": a5p1_meta["dropped_tail_entries"],
        },
        "FXNG3-A5-P2": {
            "transfer_events_total": len(streams["transfer_events"]),
            "transfer_events_by_leg": dict(sorted(
                transfer_by_leg.items())),
            "transfer_events_by_year": dict(sorted(
                transfer_by_year.items())),
            "q6_transfer_events_obs_basis": a5p2_meta[
                "recent_events_obs_basis"],
            "events_gate_passed": a5p2_meta["events_gate_passed"],
            "events_gate_failed": a5p2_meta["events_gate_failed"],
            "events_failed_closed": a5p2_meta["events_failed_closed"],
            "dropped_tail_entries": a5p2_meta["dropped_tail_entries"],
        },
    }
    declared_checks = {}
    for pid, dec in DECLARED.items():
        got = measured_totals[pid]
        match = {}
        for k, dv in dec.items():
            if isinstance(dv, str):        # BLIND declarations stay blind
                match[k] = "BLIND_BY_DECLARATION_measured_now"
            elif k == "v2_year_clusters":
                match[k] = dv == got.get(k)
            elif k == "month_composition":
                match[k] = dv == got.get(k)
            elif k == "active_leg_month_counts":
                match[k] = dv == got.get(k)
            elif k == "transfer_events_by_leg":
                match[k] = dv == got.get(k)
            else:
                match[k] = dv == got.get(k)
        declared_checks[pid] = {"declared": dec, "measured": got,
                                "match": match,
                                "note": "declared values cite the "
                                        "committed D1 proposals "
                                        "(sha256-pinned in the novelty "
                                        "output); month_composition keys "
                                        "are sorted leg sets (proposal "
                                        "labels 'CA_plus_*' mapped "
                                        "1:1 by set)"}

    r0_empty = a4p2_meta["fired_events"] == 0
    ident = identifiability(built)
    a5p1_entry_recent = a5p1_meta["recent_months_eligible_entry_basis"]
    a5p2_entry_recent = a5p2_meta["recent_events_eligible_entry_basis"]

    # structural disclosure: the restricted stream's v2 availability
    # days cluster in vintage-pull bursts (D1 declared concentration
    # risk), so the books stack onto few distinct entry grid days
    struct = {}
    for pid, book in anchors.items():
        cells = book["cells"]
        struct[pid] = {
            "distinct_active_grid_days": len({k.split("|")[0]
                                              for k in cells}),
            "active_cells": len(cells),
            "sign_counts": {s: list(cells.values()).count(s)
                            for s in (1, -1)},
            "fired_events": book["meta"].get(
                "fired_events",
                book["meta"].get("months_gate_passed",
                                 book["meta"].get("events_gate_passed"))),
        }
    structural_disclosures = {
        "books": struct,
        "note": "the CA restricted stream's v2 availability days arrive "
                "in vintage-pull bursts (2018/2022/2024, D1 declared "
                "concentration risk), so 72 events stack onto a handful "
                "of distinct entry grid days and same-day positions net "
                "sign-of-sum (P-12 cell law); rho over such stacked "
                "books is measured exactly as the frozen machinery "
                "defines it, with per-variant sample sizes recorded in "
                "the novelty panel",
    }

    verdicts = {}
    for pid in anchors:
        nov = novelty["results"][pid]["pooled"]["max_pooled_abs_rho"]
        if pid.startswith("FXNG3-A4"):
            q6 = a4_q6
        elif pid == "FXNG3-A5-P1":
            q6 = a5p1_q6
        else:
            q6 = a5p2_q6
        kill = None
        if pid in ident["results"]:
            kill_rho = ident["results"][pid].get(
                "control_vs_anchor_max_abs_rho")
            if kill_rho is not None and kill_rho >= N3.IDENTIFIABILITY_KILL:
                kill = kill_rho
        verdicts[pid] = N3.proposal_verdict(
            novelty_max_abs_rho=nov, q6_row=q6,
            r0_empty_book=(r0_empty if pid == "FXNG3-A4-P2" else None),
            identifiability_kill=kill)

    return {
        "schema": "forex_ng3_run/d2_feasibility@1",
        "q6_recent_window": {
            "window": [N3.RECENT_WINDOW_START.isoformat(),
                       N3.RECENT_WINDOW_END.isoformat()],
            "FXNG3-A4-P1": {**a4_q6, "basis": ca_recent["law"]},
            "FXNG3-A4-P2": {**a4_q6,
                            "basis": ca_recent["law"],
                            "material_subset_recent_fired": material_recent,
                            "material_subset_note":
                                "the plan-section-3 A4 floor is frozen on "
                                "the FULL restricted stream (17 measured, "
                                "floor 15); the material subset's recent "
                                "count is BLIND by D1 declaration and is "
                                "disclosed here, never floor-swapped"},
            "FXNG3-A5-P1": {**a5p1_q6,
                            "basis": "differential obs months with "
                                     "month_key in 2023-05..2025-04 "
                                     "(D1 declared basis; entry-day "
                                     f"basis measured {a5p1_entry_recent} "
                                     "disclosed)"},
            "FXNG3-A5-P2": {**a5p2_q6,
                            "basis": "transfer events (m, L), L in "
                                     "{GB, AU, NZ}, obs month in "
                                     "2023-05..2025-04 (D1 declared "
                                     "basis; entry-day basis measured "
                                     f"{a5p2_entry_recent} disclosed)"},
        },
        "totals_vs_declared": declared_checks,
        "restricted_rebuild_vs_p0_census": streams["reconciliation"],
        "structural_disclosures": structural_disclosures,
        "a4p2_r0_material_count": {
            "rule": "A4-P2 R0 (frozen): the material regime |R| >= 1e-4 "
                    "fires 0 in-window events => EMPTY BOOK, lane dies "
                    "at D2 feasibility; the 1e-4 threshold NEVER moves "
                    "(P-15)",
            "material_fired_events": a4p2_meta["fired_events"],
            "empty_book": r0_empty,
        },
        "a9f_cost_ceiling_referenced": {
            "FXNG3-A4-P1": a9f_ceiling(anchors["FXNG3-A4-P1"], s0_years),
            "FXNG3-A4-P2": a9f_ceiling(anchors["FXNG3-A4-P2"], s0_years),
            "FXNG3-A5-P1": a9f_ceiling(anchors["FXNG3-A5-P1"], s0_years,
                                       hold_key="months_gate_passed"),
            "FXNG3-A5-P2": a9f_ceiling(anchors["FXNG3-A5-P2"], s0_years,
                                       hold_key="events_gate_passed"),
        },
        "identifiability": ident,
        "verdicts": verdicts,
    }


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #

def main() -> int:
    started = utcnow_iso()
    env = load_pinned_inputs()
    streams = build_streams(env)
    built = build_all_books(env, streams)

    novelty = {
        "schema": "forex_ng3_run/d2_novelty_panel@1",
        "cycle_id": "FOREX-NG3",
        "task_id": "forex-ng3-d2-measurement",
        "measured_utc": started,
        "no_expectancy_law": "NO expectancy/PnL/PF computed in this "
                             "lane; rho is measured between signal "
                             "schedules only",
        "proposal_representation_identities": {
            pid: {"hypothesis_id": p["hypothesis_id"],
                  "representation_id": p["representation_id"],
                  "source": p["source"], "sha256": p["sha256"]}
            for pid, p in env["provenance"]["proposals"].items()},
        "restricted_rebuild_vs_p0_census": streams["reconciliation"],
        "representation_identity": {
            "grid": "daily 16:00 America/New_York common weekday grid, "
                    f"{GRID_LAW_DAYS} days "
                    f"{S0_WINDOW[0].isoformat()}..{S0_WINDOW[1].isoformat()} "
                    "(recomputed from the pinned spot bytes; P0 spot "
                    "repin law)",
            "cells": "signed exposure date|pair, entry i..i+H-1, "
                     "netting sign-of-sum (identical to the ng1 D2 "
                     "convention, reused via import)",
            "entry_clock": "D(e) = first common-grid day strictly after "
                           "EOD(v2.realtime_start) (A4) / after "
                           "EOD(max v2 day over CA + active legs) "
                           "(A5-P1) / after EOD(max(v2_CA, v2_L)) "
                           "(A5-P2 per transfer event)",
            "differential": "D = 100 * (R_CA - mean R_L) in pp; "
                            "R_X = 100 * (I_v2/I_v1 - 1) on restricted "
                            "events; gate |D| >= 0.02 pp; A4 sign law "
                            "R < 0 -> long USDCAD; A4-P2 material "
                            "|R| >= 1e-4 fraction",
        },
        "provenance": env["provenance"],
    }
    panel = novelty_panel(env, built)
    novelty.update(panel)

    feas = feasibility(env, streams, built, panel)
    feas["measured_utc"] = started
    feas["cycle_id"] = "FOREX-NG3"
    feas["task_id"] = "forex-ng3-d2-measurement"

    summary = {
        "schema": "forex_ng3_run/d1_feasibility_summary@1",
        "cycle_id": "FOREX-NG3",
        "task_id": "forex-ng3-d2-measurement",
        "measured_utc": started,
        "source": "research/control/forex_ng3_run/d2/"
                  "d2_feasibility_ng3.json + d2_novelty_panel_ng3.json",
        "recent_window": [N3.RECENT_WINDOW_START.isoformat(),
                          N3.RECENT_WINDOW_END.isoformat()],
        "floors": {"FXNG3-A4-P1": N3.A4_Q6_FLOOR,
                   "FXNG3-A4-P2": N3.A4_Q6_FLOOR,
                   "FXNG3-A5-P1": N3.A5P1_Q6_FLOOR,
                   "FXNG3-A5-P2": N3.A5P2_Q6_FLOOR},
        "proposals": {},
    }
    for pid, anchor in built["anchors"].items():
        q = feas["q6_recent_window"][pid]
        nov = panel["results"][pid]["pooled"]
        ident_ctl = feas["identifiability"]["results"].get(pid, {})
        summary["proposals"][pid] = {
            "recent_measured": q["measured"], "floor": q["floor"],
            "floor_pass": q["verdict"] == "PASS",
            "novelty_max_pooled_abs_rho": nov["max_pooled_abs_rho"],
            "novelty_worst": nov["worst"],
            "novelty_pass": (nov["max_pooled_abs_rho"] is not None
                             and nov["max_pooled_abs_rho"]
                             <= N3.NOVELTY_BAR),
            "kill_candidate_shape_rho": {
                k: v["max_abs_rho"]
                for k, v in panel["results"][pid][
                    "kill_candidate_shapes"].items()},
            "identifiability_control_vs_anchor":
                ident_ctl.get("control_vs_anchor_max_abs_rho"),
            "a9f_cost_ceiling_bps_total":
                feas["a9f_cost_ceiling_referenced"][pid][
                    "total_cost_ceiling_bps_per_unit_notional"],
            "verdict": feas["verdicts"][pid],
        }
    cross = panel["cross_proposal_collapse"]
    summary["cross_proposal_collapse"] = {
        k: v.get("max_abs_rho") for k, v in cross.items()}

    code_shas = {rel: sha256_file(os.path.join(WORKTREE, rel))
                 for rel in CODE_FILES}
    novelty["code_sha256"] = code_shas
    feas["code_sha256"] = code_shas
    summary["code_sha256"] = code_shas

    p1 = write_json(OUT_NOVELTY, novelty)
    p2 = write_json(OUT_FEAS, feas)
    p3 = write_json(OUT_FEAS_SUMMARY, summary)
    print("novelty  ->", OUT_NOVELTY, p1[:16])
    print("feas    ->", OUT_FEAS, p2[:16])
    print("summary ->", OUT_FEAS_SUMMARY, p3[:16])
    for pid, verdict in feas["verdicts"].items():
        nov = panel["results"][pid]["pooled"]
        print(f"{pid}: {verdict}  (novelty max|rho|="
              f"{nov['max_pooled_abs_rho']} worst={nov['worst']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
