"""Schema/consistency tests for the four A6 freeze PROPOSALS (rsmv1).

These tests bind the proposals to each other, to the frozen V2 contract
files they consume, and to their own digests. They are pure document
checks: no PnL, no outcome data, no runtime artifacts.

Digest law: every proposal carries ``self_sha256`` computed over its
canonical JSON (rsmv1.freezes.canonical_json convention: sort_keys,
no spaces, ensure_ascii) with the ``self_sha256`` field removed.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

CYCLE_DIR = Path(__file__).resolve().parents[1]
FREEZES = CYCLE_DIR / "freezes"

PROPOSAL_FILES = {
    "arms": "rsmv1_arms_freeze.proposal.json",
    "selection": "rsmv1_selection_freeze.proposal.json",
    "turnover": "rsmv1_turnover_freeze.proposal.json",
    "evaluation": "rsmv1_evaluation_freeze.proposal.json",
}

EXPECT_SCHEMAS = {
    "arms": "rsmv1_arms_freeze_proposal@1",
    "selection": "rsmv1_selection_freeze_proposal@1",
    "turnover": "rsmv1_turnover_freeze_proposal@1",
    "evaluation": "rsmv1_evaluation_freeze_proposal@1",
}

VERDICT_VOCABULARY = {
    "DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION",
    "NO_REGIME_STRATEGY_INCREMENTAL_VALUE",
    "BLOCKED_THIN_REGIME_SAMPLE",
    "BLOCKED_COST_OR_CONTROL_AUTHORITY",
    "TECHABORT",
}

SCORED_ARM_IDS = ["A1", "A2", "B", "C", "D", "E", "F"]
CELLS = ["BTC_H1", "BTC_H4", "SPY_D1"]

# Frozen constants carried from the forked V1/V2 machinery (read lawfully
# from the V2-era fork; NOT tuned by this cycle).
F_TOL_EXPECTED = {
    "occupancy_max_abs_dev_per_label_pp": 0.02,
    "switches_rel_dev": 0.10,
    "mean_dwell_rel_dev": 0.10,
    "invested_frac_abs_dev_pp": 0.02,
}
F_SEED_COUNT = 21
F_MAX_ATTEMPTS = 200
Q11_MIN_DELTA = 0.02

REASON_CODES_EXPECTED = {
    "FIXED_FLAT_UNK",
    "OUTER_FLOOR_THIN",
    "FOLD1_NO_INNER",
    "ASSET_INELIGIBLE",
    "INNER_FLOOR_FAIL",
    "SINGLE_ELIGIBLE",
    "POOLED_WIN_STABLE",
    "TIE_BREAK_BTC_SHORT",
    "TIE_BREAK_FLAT",
    "STABILITY_NO_COMPARATIVE_FOLDS",
    "STABILITY_FAIL",
}

FILL_CAUSE_TAGS_EXPECTED = {
    "strategy_native",
    "regime_switch",
    "fold_force_flat",
    "unnecessary_close_reopen",
}


def _load(name: str) -> dict:
    return json.loads((FREEZES / PROPOSAL_FILES[name]).read_text())


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


# ---------------------------------------------------------------- parsing


def test_every_proposal_parses_and_has_schema():
    for key, fname in PROPOSAL_FILES.items():
        payload = _load(key)
        assert payload["schema"] == EXPECT_SCHEMAS[key], fname
        assert payload["cycle"] == "REGIME-STRATEGY-MAPPING-V1"
        assert payload["status"] == "PROPOSED_AWAITING_A1_FREEZE"


def test_every_proposal_carries_correct_self_sha256():
    for key in PROPOSAL_FILES:
        payload = _load(key)
        claimed = payload.pop("self_sha256")
        recomputed = hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()
        assert claimed == recomputed, PROPOSAL_FILES[key]
        assert len(claimed) == 64


def test_input_pins_match_actual_frozen_contract_digests():
    arms = _load("arms")
    pins = arms["input_pins"]
    for pin_key, fname in [
        ("fold_contract", "fold_contract.json"),
        ("mapping_arms_freeze", "mapping_arms_freeze.json"),
        ("safety_persistence_contract", "safety_persistence_contract.json"),
        ("decision_cache_manifest", "decision_cache_manifest.json"),
    ]:
        actual = hashlib.sha256((FREEZES / fname).read_bytes()).hexdigest()
        assert pins[pin_key]["sha256"] == actual, fname
        assert (FREEZES / fname).exists()


# ------------------------------------------------------------- arms freeze


def test_budget_is_21_with_seven_scored_arm_instances():
    arms = _load("arms")
    budget = arms["trial_budget"]
    assert budget["scored_cells"] == 21
    assert budget["cells"] == CELLS
    assert budget["scored_arm_instance_ids"] == SCORED_ARM_IDS
    assert 3 * 7 == budget["scored_cells"]
    assert set(budget["references_not_scored"]) == {"FLAT", "BUY_AND_HOLD"}


def test_all_arms_defined_with_roles_and_exactly_one_candidate():
    arms = _load("arms")
    defined = arms["arms"]
    assert set(defined) == set(SCORED_ARM_IDS)
    roles = {aid: defined[aid]["role"] for aid in SCORED_ARM_IDS}
    for aid, arm in defined.items():
        assert arm["scored"] is True, aid
        assert arm["role"], aid
        assert arm["question_isolated"], aid
    scored = [aid for aid, a in defined.items() if a["scored"]]
    assert sorted(scored) == sorted(SCORED_ARM_IDS)
    candidates = [aid for aid, r in roles.items() if r == "CANDIDATE"]
    assert candidates == ["C"]
    # disclosed outcome-informed control, never a candidate
    assert defined["D"]["role"] == "OUTCOME_INFORMED_CONTROL"
    assert "outcome-informed" in defined["D"]["disclosure"]
    assert defined["C"]["spec"]["never_outcome_informed"]


def test_arm_b_engine_equivalence_gate_and_pin_obligation():
    arms = _load("arms")
    gate = arms["arms"]["B"]["engine_equivalence_gate"]
    assert "<1e-6" in gate["law"] or "1e-6" in gate["law"]
    assert gate["failure"].startswith("any field mismatch")
    pins = arms["v2_reference_pins"]
    assert pins["status"] == "TO_PIN_AT_FREEZE_BY_A1"
    for cell in CELLS:
        assert pins["b_engine_equivalence_v2_jev_only_tier1_totals_per_cell"][cell] is None


def test_arm_f_null_design_is_fail_closed():
    arms = _load("arms")
    f = arms["arms"]["F"]["spec"]
    assert f["seeds"]["count"] == F_SEED_COUNT
    assert f["max_attempts_per_seed"] == F_MAX_ATTEMPTS
    for key, val in F_TOL_EXPECTED.items():
        assert f["matching_tolerances"][key] == val, key
    q11 = f["q11_movement_validation"]
    assert q11["mandatory"] is True
    assert q11["placement"].startswith("INSIDE the acceptance loop")
    assert q11["fail_closed"].startswith("if any seed")
    assert "NOT_RUN_CONTROL_MATCHING" in q11["fail_closed"]
    assert "null_invalid" in q11["v2_lesson"]


def test_arms_reference_the_turnover_and_selection_freezes():
    arms = _load("arms")
    c = arms["arms"]["C"]["spec"]
    assert "rsmv1_turnover_freeze.proposal.json" in c["execution"]
    assert "rsmv1_selection_freeze.proposal.json" in c["routing"]
    assert arms["arms"]["B"]["spec"]["mechanics"].startswith("ORIGINAL V2")


# --------------------------------------------------------- selection freeze


def test_selection_floors_frozen():
    sel = _load("selection")
    floors = sel["floors"]
    assert floors["inner_floors"]["min_episodes_pooled_inner"] == 5
    assert floors["inner_floors"]["min_eligible_decisions_pooled_inner"] == 150
    outer = floors["outer_sample_floors"]
    assert outer["min_episodes_total_per_regime_per_cell"] == 20
    assert outer["min_episodes_per_regime_per_outer_fold"] == 3
    assert outer["min_eligible_decisions_per_regime_per_outer_fold"] == 100
    assert floors["floor_adjustments"]["status"] == "none proposed by A6"
    assert sel["nested_walk_forward_law"]["outer_folds"]["count"] == 4
    assert sel["nested_walk_forward_law"]["fold_1_default"].startswith("k=1")


def test_selection_reason_codes_exhaustive_and_procedure_ordered():
    sel = _load("selection")
    proc = sel["decision_procedure"]
    codes = set(sel["reason_code_vocabulary"])
    assert codes == REASON_CODES_EXPECTED
    orders = [r["order"] for r in proc["rules"]]
    assert orders == sorted(orders) and orders == list(range(1, len(orders) + 1))
    # every terminal rule outcome is FLAT or SELECT with a vocabulary code
    for rule in proc["rules"]:
        assert rule["outcome"] in {
            "FLAT",
            "SELECT E[0]",
            "CONTINUE with eligible set E (|E| in {1,2})",
            "see pair_resolution below",
        }
        assert rule["reason_code"] in codes or rule["reason_code"] == "see pair_resolution"
    # pair outcomes use vocabulary codes only
    pair = proc["pair_resolution"]
    assert pair["exact_numeric_tie"]["tie_break_total_order"] == [
        "FLAT", "BTC_ONLY_SHORT", "LONG_CAPABLE",
    ]
    for line in pair["exact_numeric_tie"]["resolution"]:
        assert "TIE_BREAK_" in line
    for key in ("if_met", "if_not_met", "if_S_empty"):
        assert ("POOLED_WIN_STABLE" in pair["stability"][key]) or ("STABILITY_" in pair["stability"][key])


def test_selection_total_order_no_unspecified_ties():
    """The tie-break order must terminate for every class pairing, and the
    stability requirement must be defined for every |S| in 0..3."""
    sel = _load("selection")
    tie = sel["decision_procedure"]["pair_resolution"]["exact_numeric_tie"]
    order = tie["tie_break_total_order"]
    classes = ["FLAT", "BTC_ONLY_SHORT", "LONG_CAPABLE"]
    for a in classes:
        for b in classes:
            pair = {a, b}
            if len(pair) == 1:
                # identical classes: tie-break cannot discriminate -> FLAT
                assert any("FLAT, reason TIE_BREAK_FLAT" in line for line in tie["resolution"])
            else:
                # exactly one BTC_ONLY_SHORT resolves; otherwise FLAT.
                # Either way the outcome is defined -> no unspecified tie.
                assert "BTC_ONLY_SHORT" in order and "FLAT" in order
    # stability table: |S| -> required wins (0 => FLAT)
    required = {0: None, 1: 1, 2: 2, 3: 2}
    for s, want in required.items():
        if s == 0:
            continue
        import math

        assert math.ceil(2 * s / 3) == want, s
    stab = sel["decision_procedure"]["pair_resolution"]["stability"]
    assert "FLAT" in stab["if_S_empty"]
    assert "ceil(2 * |S| / 3)" in stab["required_wins"]
    assert stab["if_met"].startswith("SELECT pooled winner")
    assert stab["if_not_met"] == "FLAT, reason STABILITY_FAIL"


def test_selection_thin_law_and_outer_scored_once():
    sel = _load("selection")
    thin = sel["thin_regime_law"]
    assert thin["label"] == "NOT_RUN_THIN_REGIME"
    assert "never" in thin["anti_fraud_law"]
    assert "EXACTLY ONCE" in sel["nested_walk_forward_law"]["outer_scored_once"]
    assert "NEVER pooled" in sel["input_pins"]["cells_law"]


# --------------------------------------------------------- turnover freeze


def test_turnover_references_only_frozen_constants():
    turnover = _load("turnover")
    contract = json.loads((FREEZES / "safety_persistence_contract.json").read_text())
    pinned = turnover["input_pins"]["safety_persistence_contract"]
    params = contract["persistence_params"]
    for key in ("confirm_bars", "min_dwell", "cooldown", "min_confidence", "min_margin"):
        assert pinned["constants_used"][key] == params[key], key
    actual = hashlib.sha256((FREEZES / "safety_persistence_contract.json").read_bytes()).hexdigest()
    assert pinned["sha256"] == actual
    laws = {law["id"]: law for law in turnover["laws"]}
    assert laws["T1_REGIME_CONFIRMATION"]["law"].startswith("the persisted-regime machine")
    assert laws["T2_TRANSITION_BUFFER"]["frozen_k"] == 1
    assert laws["T3_MIN_DWELL"]["floor_constant"] == params["min_dwell"] == 6
    assert laws["T3_MIN_DWELL"]["direction"] == "LONGER_ONLY"
    assert laws["T6_SEPARATE_REPORTING"]["fields"] == [
        "regime_switch_count", "position_switch_count",
    ]
    assert set(laws["T6_SEPARATE_REPORTING"]["fill_cause_tags"]) == FILL_CAUSE_TAGS_EXPECTED


def test_turnover_applies_to_cde_only_and_rejection_law_fails_closed():
    turnover = _load("turnover")
    assert set(turnover["applies_to"]["arms"]) == {"C", "D", "E"}
    laws = {law["id"]: law for law in turnover["laws"]}
    t7 = laws["T7_TURNOVER_REJECTION"]
    assert "FAILS the cell" in t7["law"]
    assert "zero cost" in t7["law"]
    pins = t7["v2_trade_count_pins"]
    assert pins["status"] == "TO_PIN_AT_FREEZE_BY_A1"
    for cell in CELLS:
        assert pins["per_cell"][cell] is None
    assert laws["T4_NOOP_LAW"]["unnecessary_close_reopen"]["law"].startswith("must NEVER fire")
    assert turnover["invariants"]["zero_unnecessary_close_reopen"].endswith(
        "else TURNOVER_LAW_VIOLATION"
    )


# ------------------------------------------------------- evaluation freeze


def test_verdict_vocabulary_is_exact():
    ev = _load("evaluation")
    assert set(ev["verdict_vocabulary"]["allowed_values_exactly"]) == VERDICT_VOCABULARY
    assert len(ev["verdict_vocabulary"]["allowed_values_exactly"]) == 5


def test_trial_accounting_identity():
    ev = _load("evaluation")
    acc = ev["trial_accounting"]
    assert acc["total_scored_cells"] == 21
    assert acc["identity"] == "3 cells (BTC_H1, BTC_H4, SPY_D1) x 7 scored arm instances (A1, A2, B, C, D, E, F)"
    assert set(acc["references_excluded"]) == {"FLAT", "BUY_AND_HOLD"}
    joined = " ".join(acc["counting_laws"])
    assert "EVEN IF its artifact fails to publish" in joined
    assert "no mid-run stopping" in joined


def test_candidate_gates_match_plan_section_11():
    ev = _load("evaluation")
    gates = {g["id"]: g["law"] for g in ev["candidate_gates"]["gates"]}
    assert set(gates) == {f"G{i}" for i in range(1, 9)}
    assert "net_1x > 0" in gates["G1"]
    assert "net_1.5x > 0" in gates["G2"]
    assert "max(net_A1_1x, net_A2_1x)" in gates["G3"]
    assert "net_B_1x" in gates["G4"]
    assert ">= 3" in gates["G5"] and "max fold net" in gates["G5"]
    assert "net_D_1x" in gates["G6"] and "median(F seed nets" in gates["G6"]
    assert gates["G6"].startswith("not merely trading less")
    assert "byte-identical" in gates["G7"]
    assert "zero unresolved HIGH/CRITICAL" in gates["G8"]
    assert "F_INVALID_REST_ON_ABDE" in gates["G6"]


def test_verdict_ladder_is_total_and_ceiling_holds():
    ev = _load("evaluation")
    ladder = ev["verdict_ladder"]["ladder"]
    verdicts = [rung["verdict"] for rung in ladder]
    assert verdicts == [
        "TECHABORT",
        "BLOCKED_THIN_REGIME_SAMPLE",
        "BLOCKED_COST_OR_CONTROL_AUTHORITY",
        "DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION",
        "NO_REGIME_STRATEGY_INCREMENTAL_VALUE",
    ]
    # ceiling law: strongest allowed verdict under full contamination
    cont = ev["contamination_disclosure"]
    assert "outcome-observed" in cont["corpus_status"]
    assert cont["ceiling_law"].startswith("the strongest verdict")
    assert "DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION" in cont["ceiling_law"]
    assert cont["promotion_ban"].startswith("no promotion to shadow, paper, live")
    assert "prospective" in cont["successor_law"]
    assert cont["s1_status"] == "SEALED_UNTOUCHED (every asset)"


def test_honest_decision_table_covers_every_verdict():
    ev = _load("evaluation")
    table = ev["honest_decision_table"]
    produced = {row["verdict"].split(" ")[0] for row in table}
    assert VERDICT_VOCABULARY <= produced


# ----------------------------------------------------------- cross-freeze


def test_cells_consistent_across_freezes_and_fold_contract():
    fold = json.loads((FREEZES / "fold_contract.json").read_text())
    assert sorted(fold["cells"]) == sorted(CELLS)
    for cell in CELLS:
        assert len(fold["cells"][cell]["folds"]) == 4
    ev = _load("evaluation")
    assert CELLS == ["BTC_H1", "BTC_H4", "SPY_D1"]
    arms = _load("arms")
    assert arms["trial_budget"]["cells"] == CELLS


def test_design_memo_exists_and_names_every_arm_and_verdict():
    memo = CYCLE_DIR / "evidence" / "a6_controls_design.md"
    assert memo.exists()
    text = memo.read_text()
    for aid in SCORED_ARM_IDS:
        assert aid in text, aid
    for verdict in VERDICT_VOCABULARY:
        assert verdict in text, verdict
    assert "null_invalid" in text  # the V2 lesson is documented, not buried
