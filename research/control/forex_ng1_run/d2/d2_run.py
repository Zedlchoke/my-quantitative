"""FOREX-NG1 D2 measurement runner (novelty / feasibility /
identifiability).  NO expectancy, PnL or profit factor is computed
anywhere in this runner; the only cross-book quantities are Spearman
rho between signed exposure schedules, event/decision counts, and cost
ceilings under the REFERENCED proxy ladder (1.5 bps/side, tier 2.0).

Outputs (committed with the code, P-12):

- research/control/forex_ng1_run/d2/d2_novelty_panel_ng1.json
- research/control/forex_ng1_run/d2/d2_feasibility_ng1.json
- research/control/forex_ng1_run/d1/feasibility/feasibility_summary.json

Usage:
    .venv/bin/python research/control/forex_ng1_run/d2/d2_run.py
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import date, datetime, timezone

WORKTREE = "/Users/hoangminhlong/my-quantitative/.worktrees/forex-ng1/d2"
if WORKTREE not in sys.path:
    sys.path.insert(0, WORKTREE)

from research.assets.forex_ng1 import plane_adapter as pa  # noqa: E402
from research.assets.forex_ng1.d2 import books as B        # noqa: E402
from research.assets.forex_ng1.d2 import events as E       # noqa: E402
from research.assets.forex_ng1.d2 import rho as R          # noqa: E402
from research.assets.forex_ng1.d2.series import (          # noqa: E402
    ECONOMY_SERIES, VintagedSeries, parse_realtime_observations,
)
from research.assets.forex_ng1.spot_series import (        # noqa: E402
    S0_WINDOW_END, S0_WINDOW_START, common_weekday_grid,
    load_pin_manifest, resolve_all_pairs,
)

# --------------------------------------------------------------------------- #
# pinned inputs (READ-ONLY; every digest recorded in the outputs)
# --------------------------------------------------------------------------- #

CENSUS_PATH = os.path.join(
    WORKTREE, "research/control/forex_ng1_run/p0_announcement_census.json")
GRID_CENSUS_PATH = os.path.join(
    WORKTREE, "research/control/forex_ng1_run/p1_spot/"
              "spot_grid_census.json")
GRID_CENSUS_SHA_PIN = ("42612576fb5aeb16416f36f0eb042605854f68bb2"
                       "68cd1bbedabfeafe5886ed6")
SPOT_MANIFEST_PATH = os.path.join(
    WORKTREE, "research/control/forex_ng1_run/p1_spot/"
              "spot_pin_manifest.json")

V9_ROOT = ("/Users/hoangminhlong/my-quantitative/.worktrees/"
           "forex-free-v9/integration")            # READ-ONLY inheritance
VINTAGED_DIR = os.path.join(
    V9_ROOT, "data_raw/forex_free_v9_cpi")
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

CADS_ROOT = pa.DEFAULT_CADS_STORE_ROOT
SCRATCH = "/tmp/forex_ng1_d2_scratch"

OUT_NOVELTY = os.path.join(
    WORKTREE, "research/control/forex_ng1_run/d2/"
              "d2_novelty_panel_ng1.json")
OUT_FEAS = os.path.join(
    WORKTREE, "research/control/forex_ng1_run/d2/d2_feasibility_ng1.json")
OUT_FEAS_SUMMARY = os.path.join(
    WORKTREE, "research/control/forex_ng1_run/d1/feasibility/"
              "feasibility_summary.json")

CODE_FILES = [
    "research/assets/forex_ng1/d2/__init__.py",
    "research/assets/forex_ng1/d2/series.py",
    "research/assets/forex_ng1/d2/events.py",
    "research/assets/forex_ng1/d2/books.py",
    "research/assets/forex_ng1/d2/rho.py",
    "research/control/forex_ng1_run/d2/d2_run.py",
]

NOVELTY_BAR = 0.20
IDENTIFIABILITY_KILL = 0.98
RECENT_24M = "2023-05-01..2025-04-30"

#: The D1 frozen representation identities (P-12 measurement contracts);
#: read from the committed proposals, never re-typed here.
PROPOSAL_DIR = os.path.join(
    WORKTREE, "research/control/forex_ng1_run/d1/proposals")
PROPOSAL_FILES = {
    "FXNG1-A4-P1": "proposal_A4_P1.json",
    "FXNG1-A4-P2": "proposal_A4_P2.json",
    "FXNG1-A5-P1": "proposal_A5_P1.json",
    "FXNG1-A5-P2": "proposal_A5_P2.json",
}


def load_proposal_identities() -> dict:
    out = {}
    for pid, fname in PROPOSAL_FILES.items():
        path = os.path.join(PROPOSAL_DIR, fname)
        with open(path, "rb") as fh:
            prop = json.load(fh)
        out[pid] = {
            "hypothesis_id": prop["hypothesis_id"],
            "representation_id":
                prop["representation_identity"]["representation_id"],
            "identity_fields": prop["representation_identity"][
                "identity_fields"],
            "proposal_sha256": sha256_file(path),
        }
    return out

# A9-F referenced (NOT measured) proxy ladder, V2/V8 precedent:
COST_BPS_PER_SIDE = 1.5
COST_TIER = 2.0

A4_RECENT_FLOOR = 8           # decisions (eligible pair-decisions, Q-6)
A5P1_RECENT_FLOOR = 12        # events
A5P2_RECENT_FLOOR = 24        # pair-decisions

DECLARED = {
    "FXNG1-A4-P1": {"events_in_window": 302,
                    "pair_decisions_eligible": 557},
    "FXNG1-A4-P2": {"events_in_window": 302,
                    "pair_decisions_eligible": 557},
    "FXNG1-A5-P1": {"events_total": 50, "events_in_window": 49,
                    "recent_24m_events": 21, "coopen_events_total": 104,
                    "v7recap_events_total": 202},
    "FXNG1-A5-P2": {"pair_decisions_total": 89,
                    "pair_decisions_in_window": 86,
                    "recent_24m_pair_decisions": 33,
                    "v7recap_pair_decisions_total": 390},
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


# --------------------------------------------------------------------------- #
# 1. pinned inputs
# --------------------------------------------------------------------------- #

def load_pinned_inputs() -> dict:
    prov: dict = {"census": {}, "grid": {}, "spot": {}, "vintaged": {},
                  "committed_evidence": {}}

    census = E.load_census(CENSUS_PATH)
    prov["census"] = {
        "path": CENSUS_PATH, "sha256": E.CENSUS_SHA256_PIN,
        "total_instants": census["total_instants"],
        "first_release_counts_by_economy":
            census["first_release_counts_by_economy"],
    }

    grid_census_sha = sha256_file(GRID_CENSUS_PATH)
    if grid_census_sha != GRID_CENSUS_SHA_PIN:
        raise SystemExit(f"grid census sha drift: {grid_census_sha}")
    grid_census = json.load(open(GRID_CENSUS_PATH, encoding="utf-8"))
    prov["grid"]["census_sha256"] = grid_census_sha
    prov["grid"]["census_grid_days"] = grid_census["common_grid"][
        "grid_days"]

    manifest = load_pin_manifest(SPOT_MANIFEST_PATH)
    first_entry = next(iter(manifest["files"].values()))
    spot_data_dir = os.path.dirname(first_entry["copy_path_absolute"])
    if not os.path.isdir(spot_data_dir):
        spot_data_dir = os.path.join(
            WORKTREE, "data_raw/forex_ng1_spot")   # local fallback
    serieses = resolve_all_pairs(SPOT_MANIFEST_PATH, spot_data_dir)
    grid = common_weekday_grid(serieses, S0_WINDOW_START, S0_WINDOW_END)
    if len(grid) != grid_census["common_grid"]["grid_days"]:
        raise SystemExit(
            f"grid recompute mismatch: {len(grid)} != "
            f"{grid_census['common_grid']['grid_days']}")
    prov["spot"] = {
        "manifest_path": SPOT_MANIFEST_PATH,
        "data_dir": spot_data_dir,
        "resolved_sha256": {p: s.sha256 for p, s in serieses.items()},
        "bars": {p: s.bars for p, s in serieses.items()},
        "verify_on_read": "PASS (SpotIntegrityError would have raised)",
    }

    # vintaged legs: S2 manifest via CADS (GRANTED gate), staging bytes
    # verified against the manifest pins (p0 pattern)
    registry = pa.load_registry()
    ga4 = pa.ga4_granted()
    s2_manifest = pa.consume_s2_manifest(CADS_ROOT, registry, ga4)
    local_paths = {
        rec["file"]: os.path.join(VINTAGED_DIR, name)
        for name, rec in s2_manifest["series"].items()
        if rec["file"].startswith("fred_vintaged/")
        for name in [rec["file"]]
    }
    us_entry = pa.consume_via_plane(
        registry, CADS_ROOT, "S3:forex-announcement-ledger",
        "US/fred_cpiaucsl_rt.json", SCRATCH, ga4)
    local_paths[s2_manifest["series"]["CPIAUCSL"]["file"]] = \
        us_entry.scratch_path
    verify = pa.verify_s2_files(s2_manifest, local_paths)
    failed = [k for k, v in verify.items() if not v["match"]]
    if failed:
        raise SystemExit(f"vintaged leg sha mismatch: {failed}")
    prov["vintaged"] = {
        "s2_manifest_address": pa.S2_PINNED_ADDRESS,
        "staging_root": VINTAGED_DIR,
        "verify": {k: {"file": v["file"], "pinned_sha256":
                       v["pinned_sha256"], "match": v["match"]}
                   for k, v in verify.items()},
        "us_leg": {"via": "consume_via_plane",
                   "resolved_address": us_entry.resolved_address,
                   "query_verdict": us_entry.query_verdict},
        "dgs10_status": "NOT_PINNED_THIS_CYCLE: the S2 manifest at the "
                        "pinned CADS address carries only the 5 CPI "
                        "legs; no DGS10/T10YIE/T5YIE vintaged bytes "
                        "are in this cycle's frozen consumption set, "
                        "so the exact-spec CTL-DGS10LEVEL arm is "
                        "NOT_RUN (fail-closed); the committed "
                        "FXFV8-A5-P1-control-dgs10 schedule (DGS10 "
                        "level z252, V8 measured) carries the "
                        "DGS10-level veto shape instead.",
    }

    series_by_eco: dict[str, VintagedSeries] = {}
    for eco, series_id in ECONOMY_SERIES.items():
        rel = s2_manifest["series"][series_id]["file"]
        path = (us_entry.scratch_path if rel.startswith("US/")
                else os.path.join(VINTAGED_DIR, rel))
        payload = json.load(open(path, "rb"))
        observations = (payload["observations"]
                        if isinstance(payload, dict) else payload)
        rows = parse_realtime_observations(observations)
        series_by_eco[eco] = VintagedSeries(series_id=series_id, rows=rows)
    prov["vintaged"]["spacing"] = {
        eco: vs.spacing for eco, vs in series_by_eco.items()}

    v8_books, v8_prov = B.load_committed_cells(V8_EVIDENCE_PATH)
    v7a_books, v7a_prov = B.load_committed_cells(V7_ANCESTORS_PATH)
    v7p_books, v7p_prov = B.load_committed_cells(V7_PROPOSALS_PATH)
    prov["committed_evidence"] = {
        "v8_proposals": v8_prov, "v7_ancestors": v7a_prov,
        "v7_proposals_rerun": v7p_prov,
    }

    return {"census": census, "grid": grid, "serieses": serieses,
            "series_by_eco": series_by_eco, "provenance": prov,
            "committed": {"v8": v8_books, "v7a": v7a_books,
                          "v7p": v7p_books}}


# --------------------------------------------------------------------------- #
# 2. books
# --------------------------------------------------------------------------- #

def build_all_books(env: dict) -> dict:
    grid = env["grid"]
    grid_index = {d: i for i, d in enumerate(grid)}
    grid_iso = [d.isoformat() for d in grid]
    census = env["census"]
    events = E.first_release_events(census)
    state = E.order_state(events)
    series_by_eco = env["series_by_eco"]
    closes = {p: s.closes for p, s in env["serieses"].items()}

    a4p1 = B.build_a4_book("FXNG1-A4-P1-ANCHOR", "s1_seasonal_naive",
                           0.10, events, series_by_eco, grid, grid_index,
                           S0_WINDOW_END)
    a4p2 = B.build_a4_book("FXNG1-A4-P2-ANCHOR", "s2_trailing_yoy",
                           0.15, events, series_by_eco, grid, grid_index,
                           S0_WINDOW_END)
    a4p1_sham = B.build_sham7d_book(a4p1, grid, grid_index, S0_WINDOW_END)
    a4p2_sham = B.build_sham7d_book(a4p2, grid, grid_index, S0_WINDOW_END)

    a5p1 = B.build_a5p1_book("FXNG1-A5-P1-ANCHOR", "anchor", state,
                             series_by_eco, grid, grid_index, S0_WINDOW_END)
    a5p1_coopen = B.build_a5p1_book("FXNG1-A5-P1-NEIGH-COOPEN", "coopen",
                                    state, series_by_eco, grid, grid_index,
                                    S0_WINDOW_END)
    a5p1_recap = B.build_a5p1_book("FXNG1-A5-P1-CTL-V7RECAP", "v7recap",
                                   state, series_by_eco, grid, grid_index,
                                   S0_WINDOW_END)
    a5p2 = B.build_a5p2_book("FXNG1-A5-P2-ANCHOR", "anchor", state,
                             series_by_eco, grid, grid_index, S0_WINDOW_END)
    a5p2_recap = B.build_a5p2_book("FXNG1-A5-P2-CTL-V7RECAP", "v7recap",
                                   state, series_by_eco, grid, grid_index,
                                   S0_WINDOW_END)

    generic = B.build_generic_shapes(closes, grid, grid_index)
    v7_spill = B.build_v7_spillover_shadows(events, series_by_eco, grid,
                                            grid_index, S0_WINDOW_END)
    v7_lead = B.build_v7_leadlag_shadows(closes, grid, grid_index)

    anchors = {"FXNG1-A4-P1": a4p1, "FXNG1-A4-P2": a4p2,
               "FXNG1-A5-P1": a5p1, "FXNG1-A5-P2": a5p2}
    own_shadows = {"FXNG1-A4-P1": a4p1_sham, "FXNG1-A4-P2": a4p2_sham}
    ident_controls = {
        "FXNG1-A5-P1": {"CTL-V7RECAP": a5p1_recap,
                        "NEIGH-COOPEN": a5p1_coopen},
        "FXNG1-A5-P2": {"CTL-V7RECAP": a5p2_recap},
    }
    return {"anchors": anchors, "own_shadows": own_shadows,
            "ident_controls": ident_controls, "generic": generic,
            "v7_rebuilds": {**v7_spill, **v7_lead}, "state": state,
            "grid_iso": grid_iso, "a5p1_coopen": a5p1_coopen}


# --------------------------------------------------------------------------- #
# 3. novelty panel
# --------------------------------------------------------------------------- #

def novelty_panel(env: dict, built: dict) -> dict:
    anchors = built["anchors"]
    grid_iso = built["grid_iso"]
    committed = env["committed"]

    v8_names = ["FXFV8-A5-P1-anchor", "FXFV8-A5-P1-neighbour-z504",
                "FXFV8-A5-P1-control-dgs10",
                "FXFV8-A4-P2-neighbour-sham7d", "FXFV8-A4-P2-anchor",
                "FXFV8-A4-P2-control-dgs10", "FXFV8-A4-P1-anchor",
                "FXFV8-A4-P1-control-dgs10"]
    panel: dict[str, dict] = {}
    for n in v8_names:
        if n in committed["v8"]:
            panel[n] = committed["v8"][n]
    panel["V4_commodity_bloc_exposure"] = committed["v7a"][
        "V4_commodity_bloc_exposure"]
    panel["FXFV7-A4-P1_anchor_k4_committed"] = committed["v7p"][
        "FXFV7-A4-P1_anchor_k4"]
    panel["FXFV7-A6-P2_anchor_q80_committed"] = committed["v7p"][
        "FXFV7-A6-P2_anchor_q80"]
    panel.update(built["v7_rebuilds"])
    panel.update(built["generic"])

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
                                    else round(NOVELTY_BAR - r, 4))
        results[pid] = {
            "anchor_active_cells": anchor["meta"]["active_cells"],
            "pooled": pooled,
            "margins_to_bar": margins,
            "per_veto": comparisons,
        }
    return {"bar": NOVELTY_BAR,
            "panel_names": sorted(panel),
            "results": results,
            "method": {
                "representation": "signed exposure cells date|pair on "
                                  "the frozen daily 16:00-NY common "
                                  "grid (1842 days); exposure cells "
                                  "i..i+H-1; netting sign-of-sum",
                "variants": ["cellwise_signed_full_grid",
                             "cellwise_union_active",
                             "netsigned_union_dates_shared_pairs"],
                "rho": "Spearman, average-tie ranks, |rho| pooled max "
                       "over panel x variants; global sign flips of a "
                       "shape leave |rho| unchanged",
                "shared_pairs": list(B.FUNDED_PAIRS),
            }}


# --------------------------------------------------------------------------- #
# 4. feasibility (Q-6 + totals + A9-F) and identifiability
# --------------------------------------------------------------------------- #

def a9f_ceiling(book: dict, years: float) -> dict:
    m = book["meta"]
    fired = m.get("pair_decisions_fired", 0)
    fills = 2 * fired
    per_side = COST_BPS_PER_SIDE * COST_TIER
    return {
        "ladder": "REFERENCED proxy 1.5 bps/side, stress tier 2.0 "
                  "(V2/V8 precedent; Q-8 measured constants "
                  "NOT_YET_MEASURED by the P1 kernel lane -> the "
                  "proposal-law cost verdict stays NOT_RUN)",
        "fired_positions": fired,
        "total_fills": fills,
        "cost_bps_per_side_referenced": per_side,
        "cost_bps_round_trip_per_position": 2 * per_side,
        "total_cost_ceiling_bps_per_unit_notional": fills * per_side,
        "fired_positions_per_year": (round(fired / years, 3)
                                     if years else None),
        "holds_grid_days": m.get("hold_grid_days"),
    }


def feasibility(env: dict, built: dict, novelty: dict) -> dict:
    anchors = built["anchors"]
    grid_iso = built["grid_iso"]
    s0_years = (S0_WINDOW_END - S0_WINDOW_START).days / 365.25

    checks = {}
    for pid, book in anchors.items():
        m = book["meta"]
        row = {"recent_window": RECENT_24M,
               "recent_basis": "entry grid day within 2023-05-01.."
                               "2025-04-30 (the D1 disclosed basis)",
               "recent_eligible_decisions": None,
               "floor": None, "floor_pass": None}
        if pid.startswith("FXNG1-A4"):
            row["recent_eligible_decisions"] = m[
                "recent_pair_decisions_eligible"]
            row["recent_events"] = m["recent_events"]
            row["recent_fired_decisions"] = m[
                "recent_pair_decisions_fired"]
            row["floor"] = A4_RECENT_FLOOR
        elif pid == "FXNG1-A5-P1":
            row["recent_eligible_decisions"] = m["recent_events"]
            row["recent_fired_decisions"] = m[
                "recent_pair_decisions_fired"]
            row["floor"] = A5P1_RECENT_FLOOR
        else:
            row["recent_eligible_decisions"] = m[
                "recent_pair_decisions_eligible"]
            row["recent_fired_decisions"] = m[
                "recent_pair_decisions_fired"]
            row["floor"] = A5P2_RECENT_FLOOR
        row["floor_pass"] = (row["recent_eligible_decisions"]
                             >= row["floor"])
        checks[pid] = row

    declared_checks = {}
    for pid, book in anchors.items():
        m = book["meta"]
        dec = DECLARED[pid]
        got = {}
        if pid.startswith("FXNG1-A4"):
            got = {"events_in_window": m["events_in_window"],
                   "pair_decisions_eligible":
                       m["pair_decisions_eligible"]}
        elif pid == "FXNG1-A5-P1":
            got = {"events_total": m["events_total"],
                   "events_in_window": m["events_in_window"],
                   "recent_24m_events": m["recent_events"],
                   "coopen_events_total":
                       built["a5p1_coopen"]["meta"]["events_total"],
                   "v7recap_events_total":
                       built["ident_controls"][pid]["CTL-V7RECAP"][
                           "meta"]["events_total"]}
        else:
            got = {"pair_decisions_total": m["pair_decisions_total"],
                   "pair_decisions_in_window":
                       m["pair_decisions_eligible"],
                   "recent_24m_pair_decisions":
                       m["recent_pair_decisions_eligible"],
                   "v7recap_pair_decisions_total":
                       built["ident_controls"][pid]["CTL-V7RECAP"][
                           "meta"]["pair_decisions_total"]}
        declared_checks[pid] = {
            "declared": dec, "measured": got,
            "match": {k: (dec.get(k) == got.get(k)) for k in dec},
            "delta_measured_minus_declared": {
                k: (None if dec.get(k) is None or got.get(k) is None
                    else got.get(k) - dec.get(k)) for k in dec},
            "note": "A5 recent-window deltas vs the D1 disclosure come "
                    "from the D1 approximate weekday grid vs this "
                    "lane's exact 1842-day common grid (boundary-month "
                    "shifts only); all structural counts (months, "
                    "events, totals) re-measure exactly",
        }

    ident = identifiability(env, built)

    verdicts = {}
    for pid in anchors:
        reasons = []
        nov = novelty["results"][pid]["pooled"]["max_pooled_abs_rho"]
        if nov is None:
            verdicts[pid] = "INELIGIBLE_FAIL_CLOSED(novelty_unmeasurable)"
            continue
        if nov > NOVELTY_BAR:
            reasons.append(
                f"ANCESTRY_VETO rho={round(nov, 4)} margin="
                f"{round(NOVELTY_BAR - nov, 4)} worst="
                f"{novelty['results'][pid]['pooled']['worst']}")
        if not checks[pid]["floor_pass"]:
            reasons.append(
                f"Q6_FLOOR_FAIL {checks[pid]['recent_eligible_decisions']}"
                f" < {checks[pid]['floor']}")
        kill = ident["results"].get(pid, {}).get(
            "v7_ancestry_control_recreates_anchor")
        if kill:
            reasons.append(
                "V7_ANCESTRY_CONTROL_RECREATES_ANCHOR rho="
                f"{ident['results'][pid]['control_vs_anchor_max_abs_rho']}"
                " >= 0.98 (kill pre-score)")
        if reasons:
            verdicts[pid] = "VETO(" + "; ".join(reasons) + ")"
        else:
            verdicts[pid] = "ELIGIBLE"
    return {
        "schema": "forex_ng1_run/d2_feasibility@1",
        "q6_recent_window": checks,
        "totals_vs_declared": declared_checks,
        "a9f_cost_ceiling_referenced": {
            pid: a9f_ceiling(book, s0_years)
            for pid, book in anchors.items()},
        "identifiability": ident,
        "verdicts": verdicts,
    }


def identifiability(env: dict, built: dict) -> dict:
    grid_iso = built["grid_iso"]
    out = {"kill_bar": IDENTIFIABILITY_KILL, "results": {}}
    for pid, controls in built["ident_controls"].items():
        anchor = built["anchors"][pid]
        entry: dict = {"controls": {}}
        worst_name, worst = None, None
        for cname, cbook in controls.items():
            cmp = R.compare_schedules(anchor["cells"], cbook["cells"],
                                      grid_iso, list(B.FUNDED_PAIRS))
            entry["controls"][cname] = cmp
            r = cmp.get("max_abs_rho")
            if r is not None and (worst is None or r > worst):
                worst_name, worst = cname, r
        entry["control_vs_anchor_max_abs_rho"] = worst
        entry["worst_control"] = worst_name
        entry["v7_ancestry_control_recreates_anchor"] = bool(
            worst_name == "CTL-V7RECAP" and worst is not None
            and worst >= IDENTIFIABILITY_KILL)
        if worst_name == "CTL-V7RECAP" and worst is not None:
            entry["q11_null_validity"] = (
                "control null INVALID for order-state inference at "
                f"rho={round(worst, 4)}: the no-order form reproduces "
                "the anchor schedule, so a scored null on the anchor "
                "could not be attributed to the order filter"
                if worst >= IDENTIFIABILITY_KILL else
                f"control null valid at rho={round(worst, 4)} < "
                f"{IDENTIFIABILITY_KILL}: anchor and no-order form are "
                "schedule-separable")
        out["results"][pid] = entry

    # A4: nominal-control separability + own sham7d placebo rho
    committed_dgs10 = [
        ("FXFV8-A5-P1-control-dgs10", env["committed"]["v8"][
            "FXFV8-A5-P1-control-dgs10"]),
        ("FXFV8-A4-P1-control-dgs10", env["committed"]["v8"][
            "FXFV8-A4-P1-control-dgs10"]),
        ("FXFV8-A4-P2-control-dgs10", env["committed"]["v8"][
            "FXFV8-A4-P2-control-dgs10"]),
    ]
    for pid in ("FXNG1-A4-P1", "FXNG1-A4-P2"):
        anchor = built["anchors"][pid]
        entry: dict = {"nominal_separability": {}, "sham7d_placebo": {}}
        worst = None
        for name, book in committed_dgs10:
            cmp = R.compare_schedules(anchor["cells"], book["cells"],
                                      grid_iso, list(B.FUNDED_PAIRS))
            entry["nominal_separability"][name] = cmp
            r = cmp.get("max_abs_rho")
            if r is not None and (worst is None or r > worst):
                worst = r
        entry["nominal_separability_max_abs_rho"] = worst
        entry["nominal_separability_note"] = (
            "measured against the committed V8 DGS10-level exposure "
            "shapes (DGS10 level z252, 21bd state machine); the "
            "exact-spec CTL-DGS10LEVEL arm (trailing 252-grid-day "
            "median on the book's own event days) is NOT_RUN: no "
            "DGS10 vintaged bytes in this cycle's frozen set "
            "(fail-closed, dependency disclosed)")
        sham = built["own_shadows"][pid]
        cmp = R.compare_schedules(anchor["cells"], sham["cells"],
                                  grid_iso, list(B.FUNDED_PAIRS))
        entry["sham7d_placebo"] = cmp
        out["results"][pid] = entry
    return out


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #

def main() -> int:
    started = utcnow_iso()
    env = load_pinned_inputs()
    built = build_all_books(env)

    novelty = {
        "schema": "forex_ng1_run/d2_novelty_panel@1",
        "cycle_id": "FOREX-NG1",
        "task_id": "forex-ng1-d2-measurement",
        "measured_utc": started,
        "no_expectancy_law": "NO expectancy/PnL/PF computed in this "
                             "lane; rho is measured between signal "
                             "schedules only",
        "proposal_representation_identities": load_proposal_identities(),
        "order_state_counts": built["state"]["counts"],
        "representation_identity": {
            "grid": "daily 16:00 America/New_York common weekday grid, "
                    "1842 days 2018-04-04..2025-04-30 (spot grid census "
                    f"sha256 {GRID_CENSUS_SHA_PIN})",
            "cells": "signed exposure date|pair, entry i..i+H-1, "
                     "netting sign-of-sum",
            "quarterly_lag_law": "AUSCPIALLQINMEI/NZLCPIALLQINMEI: "
                                 "I(m-1)->previous observation (m-3 "
                                 "calendar months), I(m-12)->m-12 "
                                 "calendar months, I(m-13)->m-15 "
                                 "calendar months (observation-step "
                                 "lags preserving the seasonal-ratio "
                                 "structure; disclosed measurement "
                                 "identity)",
            "entry_clock": "D(e) = first common-grid day strictly after "
                           "the proposal's evidenced availability bound "
                           "(A(e) = EOD(operative date); A5 adds the "
                           "month-order closure bounds)",
        },
        "provenance": env["provenance"],
    }
    panel = novelty_panel(env, built)
    novelty.update(panel)

    feas = feasibility(env, built, panel)
    feas["measured_utc"] = started
    feas["cycle_id"] = "FOREX-NG1"
    feas["task_id"] = "forex-ng1-d2-measurement"
    feas["order_state_counts"] = built["state"]["counts"]

    summary = {
        "schema": "forex_ng1_run/d1_feasibility_summary@1",
        "cycle_id": "FOREX-NG1",
        "task_id": "forex-ng1-d2-measurement",
        "measured_utc": started,
        "source": "research/control/forex_ng1_run/d2/"
                  "d2_feasibility_ng1.json + d2_novelty_panel_ng1.json",
        "recent_window": RECENT_24M,
        "floors": {"FXNG1-A4-P1": A4_RECENT_FLOOR,
                   "FXNG1-A4-P2": A4_RECENT_FLOOR,
                   "FXNG1-A5-P1": A5P1_RECENT_FLOOR,
                   "FXNG1-A5-P2": A5P2_RECENT_FLOOR},
        "proposals": {},
    }
    for pid in built["anchors"]:
        q = feas["q6_recent_window"][pid]
        d = feas["totals_vs_declared"][pid]
        nov = panel["results"][pid]["pooled"]
        ident_ctl = feas["identifiability"]["results"].get(pid, {})
        summary["proposals"][pid] = {
            "recent_eligible_decisions": q["recent_eligible_decisions"],
            "floor": q["floor"], "floor_pass": q["floor_pass"],
            "declared_match_all": all(d["match"].values()),
            "novelty_max_pooled_abs_rho": nov["max_pooled_abs_rho"],
            "novelty_worst": nov["worst"],
            "novelty_pass": (nov["max_pooled_abs_rho"] is not None
                             and nov["max_pooled_abs_rho"]
                             <= NOVELTY_BAR),
            "identifiability_control_vs_anchor":
                ident_ctl.get("control_vs_anchor_max_abs_rho"),
            "a9f_cost_ceiling_bps_total":
                feas["a9f_cost_ceiling_referenced"][pid][
                    "total_cost_ceiling_bps_per_unit_notional"],
            "verdict": feas["verdicts"][pid],
        }

    code_shas = {rel: sha256_file(os.path.join(WORKTREE, rel))
                 for rel in CODE_FILES}
    novelty["code_sha256"] = code_shas
    feas["code_sha256"] = code_shas
    summary["code_sha256"] = code_shas

    p1 = write_json(OUT_NOVELTY, novelty)
    p2 = write_json(OUT_FEAS, feas)
    p3 = write_json(OUT_FEAS_SUMMARY, summary)
    print("novelty   ->", OUT_NOVELTY, p1[:16])
    print("feas     ->", OUT_FEAS, p2[:16])
    print("summary  ->", OUT_FEAS_SUMMARY, p3[:16])
    for pid, verdict in feas["verdicts"].items():
        nov = panel["results"][pid]["pooled"]
        print(f"{pid}: {verdict}  (novelty max|rho|="
              f"{nov['max_pooled_abs_rho']} worst={nov['worst']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
