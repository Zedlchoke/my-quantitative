"""RATES-NG1 I-phase dry-run plumbing self-check + i-gate assembly.

Cycle RATES-NG1, task rates-ng1-i-implementation.

``dry_run_plumbing`` runs the FULL I-phase machinery end-to-end on the
SYNTHETIC fixtures (fixtures.py) and emits STRUCTURAL COUNTS ONLY:
decision counts, state-defined vs UNDEFINED counts, round trips, exit
reasons, kernel row counts, dual-book equality flags, battery
alignment counts and the rules scaffold.  NO PnL, NO after-cost edge,
NO outcome number of any kind -- the emission is leak-scanned
(rules.scan_emission_for_outcome_tokens) and the scan result is part of
the payload.

``build_i_gate_payload`` assembles the measured structural sections of
research/control/rates_ng1_run/i/i_gate.json (per-work-item PASS/FAIL
with measured structural values only).
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any

from research.assets.rates_ng1.runners import fixtures as fx
from research.assets.rates_ng1.runners.battery import (
    KILLER_ROLES,
    align_defined_pairs,
    placebo_state,
)
from research.assets.rates_ng1.runners.runner import (
    FAMILY_ID,
    LEG_PAIR,
    TENOR_BRACKET_MAPPING,
    assemble_cell_configs,
    clock_only_state,
    curve_coordinates,
    level_control_state,
    run_arm,
)
from research.assets.rates_ng1.runners.rules import (
    FROZEN_RULE_ORDER,
    fold_bounds,
    pbo_record,
    scan_emission_for_outcome_tokens,
)

SCHEMA = "rates_ng1_run/i_dry_run_plumbing@1"
GATE_SCHEMA = "rates_ng1_run/i_gate@1"

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
FREEZE_PATH = os.path.join(
    REPO_ROOT, "research", "control", "rates_ng1_run", "s",
    "selection_freeze.json")
CENSUS_PATH = os.path.join(
    REPO_ROOT, "research", "control", "rates_ng1_run",
    "p2_grid_census.json")
COST_CONTRACT_PATH = os.path.join(
    REPO_ROOT, "research", "control", "rates_ng1_run",
    "p1_cost_contract.json")

#: The packet's exact test command (recorded verbatim in the gate).
TEST_COMMAND = ("cd /Users/hoangminhlong/my-quantitative/"
                ".worktrees/rates-ng1/integration && "
                "/Users/hoangminhlong/my-quantitative/.venv/bin/python "
                "-m pytest tests/test_rates_ng1_i.py -q")

ANCHOR_ARM_ID = "RATESNG1-A5-P1-ARM-NEUTRAL"


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_freeze() -> dict:
    with open(FREEZE_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def census_structural() -> dict:
    """MEASURED structural facts of the committed P2 grid census:
    file sha256 + list lengths ONLY (bookable instants, grid sessions).
    No series content is read past the lengths; no outcome is computed
    (I-phase structural-plumbing law)."""
    with open(CENSUS_PATH, "r", encoding="utf-8") as fh:
        census = json.load(fh)
    c = census["census"]
    return {
        "p2_grid_census_sha256": _sha256_file(CENSUS_PATH),
        "bookable_instants_len": len(c["bookable_instants"]),
        "grid_dates_len": len(c["grid_dates"]),
    }


def dry_run_plumbing() -> dict:
    """Full plumbing self-check on SYNTHETIC data; structural counts
    only, no PnL, no outcome numbers."""
    freeze = load_freeze()
    cells = assemble_cell_configs(freeze)
    bundle = fx.synthetic_state_inputs()
    instants = bundle["instants"]

    arms: dict[str, Any] = {}
    anchor_states: list = []
    digests: set[str] = set()
    for cell in cells:
        res = run_arm(
            arm_id=cell["arm_id"],
            arm_role=cell["role"],
            config=cell["config"],
            instants=instants,
            curve_by_date=bundle["curve_by_date"],
            leg_closes_by_date=bundle["leg_closes"],
            tiers_bps=bundle["tiers_bps"],
            er_daily=bundle["er_daily"],
        )
        digests.add(res["arm_config_digest"])
        meta = dict(res["meta"])
        books_struct = res["books_structural"]
        meta["ledgers"] = books_struct
        meta["cost_events_total"] = sum(v["cost_events"]
                                        for v in books_struct.values())
        meta["fills_total"] = sum(v["fills"] for v in books_struct.values())
        meta["all_ledgers_dual_book_equality_ok"] = all(
            v["dual_book_equality_ok"] for v in books_struct.values())
        arms[cell["arm_id"]] = meta
        if cell["arm_id"] == ANCHOR_ARM_ID:
            anchor_states = res["state_series"]

    # Battery control states on the SAME synthetic grid (structural
    # alignment counts only -- no edges, no outcomes).
    level_state = level_control_state(_level_series(bundle, instants))
    clock_state = clock_only_state(instants)
    placebo = placebo_state(anchor_states)
    controls = {
        "LEVEL_VS_SHAPE_DECOMPOSITION_CONTROL":
            _align_counts(anchor_states, level_state),
        "CLOCK_ONLY_SHADOW": _align_counts(anchor_states, clock_state),
        "PLACEBO": _align_counts(anchor_states, placebo),
    }
    battery = {
        "anchor_arm": ANCHOR_ARM_ID,
        "killer_roles": list(KILLER_ROLES),
        "k_misalign_sessions": 5,
        "q11_alignment_counts_synthetic": controls,
        "kill_semantics": "strictly greater after-cost per-decision "
                          "edge; comparator unit-tested on synthetic "
                          "edge fixtures (tests/test_rates_ng1_i.py)",
    }

    payload = {
        "schema": SCHEMA,
        "task_id": "rates-ng1-i-implementation",
        "cycle_id": "RATES-NG1",
        "mode": "DRY_RUN_PLUMBING_SYNTHETIC",
        "synthetic": True,
        "real_substrate": False,
        "scored": False,
        "outcome_computation": "refused in I: structural counts only, "
                               "no after-cost series is computed",
        "synthetic_grid": {
            "n_sessions": len(bundle["grid"]),
            "warmup": 8,
            "n_instants": len(instants),
        },
        "freeze_citation": {
            "path": "research/control/rates_ng1_run/s/"
                    "selection_freeze.json",
            "sha256": _sha256_file(FREEZE_PATH),
        },
        "family_id": FAMILY_ID,
        "leg_pair": dict(LEG_PAIR),
        "tenor_bracket_mapping": dict(TENOR_BRACKET_MAPPING),
        "cells": [{"cell_id": c["cell_id"], "arm_id": c["arm_id"],
                   "role": c["role"],
                   "arm_config_digest": c["arm_config_digest"]}
                  for c in cells],
        "arms": arms,
        "battery": battery,
        "rules_scaffold": {
            "frozen_rule_order": list(FROZEN_RULE_ORDER),
            "fold_windows": [list(w) for w in fold_bounds()],
            "pbo": pbo_record(len(cells)),
        },
        "identity": {
            "cell_count": len(cells),
            "arm_config_digests_pairwise_distinct": len(digests) == len(
                cells),
        },
    }
    payload["leak_scan"] = scan_emission_for_outcome_tokens(payload)
    return payload


def _level_series(bundle: dict, instants: list[dict]) -> list:
    return curve_coordinates(bundle["curve_by_date"], instants)["level"]


def _align_counts(a: list, b: list) -> dict:
    al = align_defined_pairs(a, b)
    return {k: al[k] for k in ("n_instants", "n_pairs_used",
                               "dropped_undefined_side_a",
                               "dropped_undefined_side_b")}


def build_i_gate_payload(base_sha: str,
                         tests_row: dict | None = None) -> dict:
    """Assemble the i_gate.json payload: per-work-item PASS/FAIL with
    MEASURED STRUCTURAL VALUES ONLY (digests, counts, cited frozen
    constants).  ``tests_row`` is supplied by the lane after the packet
    test command has been executed."""
    dry = dry_run_plumbing()
    if not dry["leak_scan"]["clean"]:
        raise RuntimeError(
            f"emission leak scan failed: {dry['leak_scan']['leaks']}")
    arms = dry["arms"]
    cells = dry["cells"]
    _census_struct = census_structural()
    freeze = load_freeze()

    gate = {
        "schema": GATE_SCHEMA,
        "cycle_id": "RATES-NG1",
        "task_id": "rates-ng1-i-implementation",
        "base_sha": base_sha,
        "branch": "orca/rates-ng1-integration",
        "worktree": "/Users/hoangminhlong/my-quantitative/"
                    ".worktrees/rates-ng1/integration",
        "scope_law": "I phase: unit tests + dry-run plumbing on "
                     "SYNTHETIC fixtures only; NO scored execution on "
                     "real data; NO outcome numbers on real data; "
                     "real-substrate access limited to structural "
                     "plumbing (digests, series lengths, config "
                     "assembly); S1 SEALED_UNTOUCHED",
        "items": {},
        "structural_values": {},
    }

    # -- work item 1: family runner -----------------------------------
    gate["items"]["1_family_runner"] = {
        "verdict": "PASS" if (
            len(cells) == 3
            and dry["identity"]["arm_config_digests_pairwise_distinct"]
            and all(arms[a]["decision_ids_pairwise_distinct"] for a in arms)
            and all(arms[a]["all_ledgers_dual_book_equality_ok"]
                    for a in arms)) else "FAIL",
        "measured": {
            "cells_assembled": len(cells),
            "arm_config_digests": {c["arm_id"]: c["arm_config_digest"]
                                   for c in cells},
            "digests_pairwise_distinct":
                dry["identity"]["arm_config_digests_pairwise_distinct"],
            "gate_variants": ["both_above_plus1_both_below_minus1_"
                              "else_zero",
                              "both_above_upper_q_plus1_both_below_"
                              "lower_q_minus1_else_zero",
                              "either_above_plus1_either_below_"
                              "minus1_else_zero"],
            "leg_pair": dry["leg_pair"],
            "tenor_bracket_mapping": dry["tenor_bracket_mapping"],
            "kernel_booking": "P1 DualBookLedger verbatim; spread cost "
                              "once per fill on BOTH legs; ACT/365F "
                              "drag per leg per round trip; SHORT legs "
                              "mirror-booked with disclosed runner "
                              "sign",
        },
    }

    # -- work item 2: control battery ----------------------------------
    bat = dry["battery"]["q11_alignment_counts_synthetic"]
    gate["items"]["2_control_battery"] = {
        "verdict": "PASS" if (sorted(bat) == sorted(KILLER_ROLES)
                              and dry["battery"]["k_misalign_sessions"]
                              == 5) else "FAIL",
        "measured": {
            "roles": sorted(KILLER_ROLES),
            "declared_executioner": "LEVEL_VS_SHAPE_DECOMPOSITION_CONTROL",
            "k_misalign_sessions": dry["battery"]["k_misalign_sessions"],
            "q11_alignment_counts_synthetic": bat,
            "kill_semantics": dry["battery"]["kill_semantics"],
        },
    }

    # -- work item 3: R1-R6 scaffolding + PBO law ----------------------
    gate["items"]["3_rules_r1_r6_pbo"] = {
        "verdict": "PASS" if (
            dry["rules_scaffold"]["pbo"]["status"]
            == "NOT_RUN_FAIL_CLOSED_CELLS_LT_8") else "FAIL",
        "measured": {
            "fold_windows": dry["rules_scaffold"]["fold_windows"],
            "frozen_bounds": {"r1_expectancy_gt": 0.0,
                              "r3_min_positive_folds": 2,
                              "r4_pf_min": 1.10,
                              "r6_max_single_instant_gross_share": 0.5},
            "pbo": dry["rules_scaffold"]["pbo"],
        },
    }

    # -- work item 4: tests --------------------------------------------
    row = tests_row or {"command": TEST_COMMAND, "exit_code": None,
                        "verdict": "NOT_RUN"}
    gate["items"]["4_tests"] = dict(row)

    # -- negative scan ---------------------------------------------------
    gate["negative_scan"] = {
        "emission_leak_scan_clean": dry["leak_scan"]["clean"],
        "patterns": dry["leak_scan"]["patterns"],
        "outcome_numbers_on_real_substrate": "NONE_COMPUTED_IN_I",
        "synthetic_only_declaration": dry["outcome_computation"],
    }

    gate["structural_values"] = {
        "dry_run_synthetic_grid": dry["synthetic_grid"],
        "arms_structural_counts": {
            a: {k: arms[a][k] for k in
                ("decisions_total", "states_defined", "states_undefined",
                 "state_events_nonzero", "round_trips", "folds_decisions",
                 "exit_reasons", "fold_force_flat_same_day",
                 "fills_total", "cost_events_total")}
            for a in sorted(arms)},
        "committed_artifact_pins": {
            "selection_freeze_sha256":
                dry["freeze_citation"]["sha256"],
            "p1_cost_contract_sha256": _sha256_file(COST_CONTRACT_PATH),
            "p2_grid_census_measured": _census_struct,
            "grid_counts_vs_freeze_cited": {
                "freeze_cited_bookable_instants":
                    freeze.get("section_1_selected_family", {})
                    .get("feasibility_evidence", {})
                    .get("bookable_instants"),
                "freeze_cited_grid_sessions":
                    freeze.get("section_1_selected_family", {})
                    .get("feasibility_evidence", {})
                    .get("grid_sessions"),
                "bookable_instants_match": _census_struct[
                    "bookable_instants_len"] == (
                    freeze.get("section_1_selected_family", {})
                    .get("feasibility_evidence", {})
                    .get("bookable_instants")),
                "grid_sessions_match": _census_struct[
                    "grid_dates_len"] == (
                    freeze.get("section_1_selected_family", {})
                    .get("feasibility_evidence", {})
                    .get("grid_sessions")),
            },
        },
        "s1": "SEALED_UNTOUCHED",
    }
    return gate
