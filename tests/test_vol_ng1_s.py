"""VOL-NG1 S selection-freeze tests (task vol-ng1-s-selection-freeze).

Schema/completeness checks on the six mandatory sections, citation-hash
re-verification against disk, frozen-arm law checks (anchors == the D2
frozen neutral defaults; variants on declared axes only; pairwise-distinct
digests), R1-R6 rule-set provenance and fold law, cost-contract binding,
C8 verbatim equality, and the negative scan (NO outcome numbers anywhere
in the freeze -- numeric leaves restricted to a preregistration
whitelist; no outcome-worded keys at all).

No network, no scoring, no PnL/outcome numbers anywhere (Q-6).
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.control.vol_ng1_run.d2 import d2_novelty as dn  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
WT = REPO_ROOT
P = REPO_ROOT / "research/control/vol_ng1_run"
FREEZE_PATH = P / "s/selection_freeze.json"
PANEL_PATH = P / "d2/d2_novelty_panel.json"
P2G_PATH = P / "p2_gate.json"
CC_PATH = P / "p1_cost_contract.json"
P1G_PATH = P / "p1_gate.json"
P0G_PATH = P / "p0_gate.json"
D1G_PATH = P / "d1/d1_gate.json"
A4_PATH = P / "d1/proposals/VOLNG1-A4-P2.json"
A5_PATH = P / "d1/proposals/VOLNG1-A5-P2.json"
CA_PATH = REPO_ROOT / "research/assets/vol_ng1/corp_actions.py"
PA_PATH = REPO_ROOT / "research/assets/vol_ng1/plane_adapter.py"

FOREX_FREEZE_COMMIT = "d0992d17df8e2dfde57c9a0806a5798f14021a4f"
FOREX_FREEZE_PATH = ("research/control/forex_ng1_run/"
                     "selection_freeze.json")

EXPECTED_A4_SHA = "4ee9a299fed526226cc76c211acd23565fda3522149b7b357907cdb5ebb409d1"
EXPECTED_A5_SHA = "b1a0a1e2ebf6e705c1788639731d6e880958fd945c319bcc55a3d4d2ef8924b4"

#: numeric-leaf whitelist: the ONLY keys allowed to carry numbers in the
#: freeze (preregistered structural facts, frozen parameters, margins,
#: counts and the tier ladder).  Anything else numeric is an outcome
#: number by construction and fails the negative scan.
ALLOWED_NUMERIC_KEYS = {
    # frozen arm parameters (declared axes only)
    "d_threshold", "latch_m_sessions", "asym_threshold", "latch_sessions",
    "standardization_min_history", "proxy_lookback_sessions",
    # D2 novelty evidence (decision-state correlation margins, not outcomes)
    "pooled_abs_max", "margin_to_gate", "novelty_margin",
    # rubric budget / arm bookkeeping
    "arms_per_family_max", "cells_total_max", "trial_budget", "arm_count",
    "rank", "budget_cell", "primary_tier", "tier_ladder",
    # frozen battery constants
    "calendar_shift_k_sessions", "placebo_seed",
    # committed P2/P0 structural census facts (feasibility citations)
    "grid_sessions_total", "warmup_carveout_sessions", "bookable_instants",
    "coverage_primary", "coverage_primary_denominator",
    "measured_bookable_instants", "frozen_floor_min_bookable_instants",
    "measured_bookable_computable_instants",
    "frozen_floor_min_bookable_computable_instants",
    "frozen_floor_min_coverage",
}

#: any key worded as a scored outcome is banned outright (regardless of
#: value type) -- rule text lives in string VALUES, never in keys
OUTCOME_KEY_RE = re.compile(
    r"(pnl|expectancy|profit[_ ]?factor|sharpe|sortino|drawdown|"
    r"win[_ ]?rate|hit[_ ]?rate|cagr|calmar|return)", re.IGNORECASE)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_digest(cfg: dict) -> str:
    return hashlib.sha256(json.dumps(
        cfg, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True).encode("utf-8")).hexdigest()


@pytest.fixture(scope="module")
def freeze() -> dict:
    assert FREEZE_PATH.exists(), "selection_freeze.json missing"
    return json.loads(FREEZE_PATH.read_text())


@pytest.fixture(scope="module")
def panel() -> dict:
    return json.loads(PANEL_PATH.read_text())


# ------------------------------------------------------------------ schema
def test_schema_and_six_mandatory_sections(freeze):
    assert freeze["schema"] == "vol_ng1_selection_freeze@1"
    assert freeze["cycle_id"] == "VOL-NG1"
    assert freeze["task_id"] == "vol-ng1-s-selection-freeze"
    assert freeze["base_sha_verified"] == freeze["git_head_at_freeze"]
    assert freeze["base_sha_verified"] == (
        "646ad433eeeb0f2f20ef5937c5cec1267717d245")
    for section in freeze["mandatory_sections"]:
        assert section in freeze, f"missing mandatory section {section}"
        assert freeze[section], f"empty mandatory section {section}"
    assert freeze["mandatory_sections"] == [
        "selected_families", "arm_configuration_plan", "rule_set_r1_r6",
        "cost_contract_binding", "ranking_basis", "i_phase_control_battery"]
    assert freeze["s1_status"] == "SEALED_UNTOUCHED"
    blind = freeze["blindness_declaration"]
    assert blind["no_scored_number_exists"] is True
    assert blind["no_scored_outcome_quantity_anywhere"] is True


# ------------------------------------------------------- section 1: families
def test_selected_families_exactly_the_d2_eligible_pair(freeze, panel):
    sel = freeze["selected_families"]
    fams = {f["family_key"] for f in sel["families"]}
    assert fams == set(panel["summary"]["eligible"])
    assert len(sel["families"]) == 2
    for fam in sel["families"]:
        prow = next(p for p in panel["proposals"]
                    if p["proposal_id"] == fam["family_key"])
        assert prow["verdict"] == "ELIGIBLE"
        assert fam["d2_panel"]["verdict"] == "ELIGIBLE"
        assert fam["d2_panel"]["pooled_abs_max"] == pytest.approx(
            prow["pooled_abs_max"], abs=1e-9)
        assert fam["d2_panel"]["margin_to_gate"] == pytest.approx(
            prow["margin_to_gate"], abs=1e-9)
        assert fam["d2_panel"]["sha256"] == _sha256(PANEL_PATH)


def test_not_selected_families_match_panel_vetoes(freeze, panel):
    ns = {n["family_key"]: n for n in
          freeze["selected_families"]["not_selected_families"]}
    assert set(ns) == set(panel["summary"]["veto"])
    for key, row in ns.items():
        prow = next(p for p in panel["proposals"]
                    if p["proposal_id"] == key)
        assert prow["verdict"] == "VETO"
        assert row["pooled_abs_max"] == pytest.approx(
            prow["pooled_abs_max"], abs=1e-9)
        assert row["pooled_abs_max"] > 0.2
        assert "never argued away" in row["reason"]


def test_citation_hashes_reverified_against_disk(freeze):
    cit = freeze["cost_and_gate_citations"]
    assert cit["p0_gate_json_sha256"] == _sha256(P0G_PATH)
    assert cit["p1_gate_json_sha256"] == _sha256(P1G_PATH)
    assert cit["p1_cost_contract_json_sha256"] == _sha256(CC_PATH)
    assert cit["p2_gate_json_sha256"] == _sha256(P2G_PATH)
    assert cit["d1_gate_json_sha256"] == _sha256(D1G_PATH)
    assert cit["d2_novelty_panel_json_sha256"] == _sha256(PANEL_PATH)
    # code-artifact digests live in their binding sections
    bind = freeze["cost_contract_binding"]
    assert bind["corp_actions_py_sha256"] == _sha256(CA_PATH)
    assert bind["gate_citations"]["corp_actions_py_sha256"] == _sha256(CA_PATH)
    assert bind["gate_citations"]["plane_adapter_py_sha256"] == _sha256(PA_PATH)
    scl = freeze["representation_freeze"]["series_consumption_law"]
    assert scl["corp_actions_py_sha256"] == _sha256(CA_PATH)
    assert scl["plane_adapter_py_sha256"] == _sha256(PA_PATH)


def test_proposal_sha256_citations_match_disk_and_d1_gate(freeze):
    d1g = json.loads(D1G_PATH.read_text())
    gate_shas = {p["proposal_id"]: p["sha256"] for p in d1g["proposals"]}
    for fam in freeze["selected_families"]["families"]:
        disk = _sha256(REPO_ROOT / fam["proposal_path"])
        assert fam["proposal_sha256"] == disk
        assert gate_shas[fam["family_key"]] == disk
    assert gate_shas["VOLNG1-A4-P2"] == EXPECTED_A4_SHA
    assert gate_shas["VOLNG1-A5-P2"] == EXPECTED_A5_SHA


def test_c8_limitation_carried_verbatim(freeze):
    fam = next(f for f in freeze["selected_families"]["families"]
               if f["family_key"] == "VOLNG1-A5-P2")
    p2g = json.loads(P2G_PATH.read_text())
    committed = p2g["sections"]["a5_risk_premium"]["structural_limitation"]
    proposal = json.loads(A5_PATH.read_text())
    verbatim = fam["structural_limitation_p2_gate_c8_verbatim"]
    assert verbatim == committed
    assert verbatim == proposal["structural_limitation_p2_gate_c8_verbatim"]
    assert "implied-vs-implied-complex proxy" in verbatim
    assert "never the classic implied-vs-spot-realized" in verbatim


# ------------------------------------------------- section 2: arm plan
def test_arm_budget_law(freeze):
    plan = freeze["arm_configuration_plan"]
    assert plan["arms_per_family_max"] == 3
    assert plan["cells_total_max"] == 6
    assert plan["trial_budget"] == 6
    assert plan["arm_count"] == len(plan["arms"]) == 6
    per_family: dict[str, int] = {}
    for arm in plan["arms"]:
        per_family[arm["family_key"]] = (
            per_family.get(arm["family_key"], 0) + 1)
    assert per_family == {"VOLNG1-A4-P2": 3, "VOLNG1-A5-P2": 3}
    cells = sorted(a["budget_cell"] for a in plan["arms"])
    assert cells == [1, 2, 3, 4, 5, 6]


def test_arm_config_digests_pairwise_distinct_and_self_consistent(freeze):
    plan = freeze["arm_configuration_plan"]
    digests = [a["arm_config_digest"] for a in plan["arms"]]
    assert len(digests) == len(set(digests)), "arm_config_digest collision"
    for arm in plan["arms"]:
        assert arm["arm_config_digest"] == _canonical_digest(arm["config"])
        assert re.fullmatch(r"[0-9a-f]{64}", arm["arm_config_digest"])


def test_anchor_arms_are_the_d2_frozen_neutral_defaults(freeze):
    plan = freeze["arm_configuration_plan"]
    a4a = next(a for a in plan["arms"]
               if a["arm_id"] == "VOLNG1-A4-P2-ANCHOR")["config"]
    assert a4a["d_threshold"] == dn.FROZEN_DEFAULTS["a4p2_d_threshold"]
    assert a4a["latch_m_sessions"] == dn.FROZEN_DEFAULTS[
        "a4p2_latch_m_sessions"]
    assert a4a["regime_action_map"] == dn.FROZEN_DEFAULTS[
        "a4p2_regime_action_map"]
    assert a4a["slope_functional_form"] == dn.FROZEN_DEFAULTS[
        "slope_functional_form"]
    assert a4a["second_difference_form"] == dn.FROZEN_DEFAULTS[
        "second_difference_form"]
    a5a = next(a for a in plan["arms"]
               if a["arm_id"] == "VOLNG1-A5-P2-ANCHOR")["config"]
    assert a5a["asym_threshold"] == dn.FROZEN_DEFAULTS["a5p2_asym_threshold"]
    assert a5a["latch_sessions"] == dn.FROZEN_DEFAULTS["a5p2_latch_sessions"]
    assert a5a["state_action_map"] == dn.FROZEN_DEFAULTS[
        "a5p2_state_action_map"]
    assert a5a["mid_reference_leg"] == dn.FROZEN_DEFAULTS[
        "a5p2_mid_reference_leg"]
    assert a5a["standardization_min_history"] == dn.FROZEN_DEFAULTS[
        "standardization_min_history"]
    assert a5a["proxy_leg_short_bucket"] == "VXX"


def test_variants_differ_from_anchor_on_declared_axes_only(freeze):
    plan = freeze["arm_configuration_plan"]
    arms = {a["arm_id"]: a["config"] for a in plan["arms"]}
    a4_anchor = arms["VOLNG1-A4-P2-ANCHOR"]
    for vid in ("VOLNG1-A4-P2-NEIGH-PERSIST", "VOLNG1-A4-P2-NEIGH-FAST"):
        diff = {k for k in a4_anchor
                if a4_anchor[k] != arms[vid][k]}
        assert diff == {"latch_m_sessions"}, (vid, diff)
    m_by_arm = {vid: arms[vid]["latch_m_sessions"]
                for vid in ("VOLNG1-A4-P2-NEIGH-PERSIST",
                            "VOLNG1-A4-P2-ANCHOR",
                            "VOLNG1-A4-P2-NEIGH-FAST")}
    assert m_by_arm == {"VOLNG1-A4-P2-NEIGH-PERSIST": 4,
                        "VOLNG1-A4-P2-ANCHOR": 3,
                        "VOLNG1-A4-P2-NEIGH-FAST": 2}
    a5_anchor = arms["VOLNG1-A5-P2-ANCHOR"]
    for vid in ("VOLNG1-A5-P2-NEIGH-STRICT", "VOLNG1-A5-P2-NEIGH-FAST"):
        diff = {k for k in a5_anchor if a5_anchor[k] != arms[vid][k]}
        assert diff == {"asym_threshold", "latch_sessions"}, (vid, diff)
    strict = arms["VOLNG1-A5-P2-NEIGH-STRICT"]
    fast = arms["VOLNG1-A5-P2-NEIGH-FAST"]
    assert (strict["asym_threshold"], strict["latch_sessions"]) == (0.75, 3)
    assert (fast["asym_threshold"], fast["latch_sessions"]) == (0.25, 1)


def test_arm_role_symmetry_and_rationale_documented(freeze):
    plan = freeze["arm_configuration_plan"]
    roles: dict[str, list[str]] = {}
    for arm in plan["arms"]:
        roles.setdefault(arm["family_key"], []).append(arm["role"])
        assert arm["variant_rationale"].strip()
        assert "not tuned" in arm["variant_rationale"]
    for fam, rs in roles.items():
        assert sorted(rs) == ["ANCHOR", "NEIGHBOUR_AGGRESSIVE",
                              "NEIGHBOUR_CONSERVATIVE"], (fam, rs)
    assert "WITHOUT outcome knowledge" in plan["parameter_freeze_rationale"]
    assert "economic_magnitude_honesty" in plan["parameter_freeze_rationale"]


def test_arm_leg_subsets_within_frozen_consumption_set(freeze):
    cc = json.loads(CC_PATH.read_text())
    short_legs = {k for k, v in cc["legs"].items() if v["bucket"] == "SHORT"}
    mid_legs = {k for k, v in cc["legs"].items() if v["bucket"] == "MID"}
    assert short_legs == {"VXX", "UVXY", "SVXY", "VIXY"}
    assert mid_legs == {"VIXM", "VXZ"}
    plan = freeze["arm_configuration_plan"]
    for arm in plan["arms"]:
        cfg = arm["config"]
        assert set(cfg["leg_subset"]) <= short_legs | mid_legs
        if arm["family_key"] == "VOLNG1-A5-P2":
            assert set(cfg["bucket_map"]["front"]) == short_legs
            assert set(cfg["bucket_map"]["mid"]) == mid_legs


# ------------------------------------------------- section 3: R1-R6 rules
def test_rule_set_r1_r6_complete_and_ordered(freeze):
    rules = freeze["rule_set_r1_r6"]["rule_order"]
    assert len(rules) == 6
    for i, expected in enumerate(["R1", "R2", "R3", "R4", "R5", "R6"], 1):
        assert rules[i - 1].startswith(expected)
    rs = freeze["rule_set_r1_r6"]
    assert "PROVISIONAL_STAGE_A_SURVIVOR" in rs["survivor_law"]
    assert "NOT_RUN" in rs["fail_closed_law"]
    assert "never an inferred PASS" in rs["fail_closed_law"]
    # adapted thresholds inherited verbatim from the precedent
    r4 = next(r for r in rules if r.startswith("R4"))
    assert "1.10" in r4
    r2 = next(r for r in rules if r.startswith("R2"))
    assert "0.5x" in r2
    r6 = next(r for r in rules if r.startswith("R6"))
    assert "50%" in r6


def test_rule_set_provenance_cites_forex_precedent_and_cycle_law(freeze):
    prov = freeze["rule_set_r1_r6"]["provenance"]
    forex = [p for p in prov
             if p.get("commit_sha") == FOREX_FREEZE_COMMIT]
    assert forex, "FOREX-NG1 freeze commit not cited"
    assert any(p["path"] == FOREX_FREEZE_PATH for p in forex)
    assert any("PLAN_crypto_ng1.md" in p.get("path", "") for p in prov)
    assert any("PLAN_vol_ng1.md" in p.get("path", "") for p in prov)


def test_frozen_folds_contiguous_inside_bookable_window(freeze):
    rs = freeze["rule_set_r1_r6"]
    folds = rs["frozen_folds"]
    assert [f["fold"] for f in folds] == ["F1", "F2", "F3"]
    grid = freeze["representation_freeze"]["common_grid"]
    first, last = grid["first_bookable_instant"], grid["last_bookable_instant"]
    assert folds[0]["window"][0] == first
    assert folds[-1]["window"][1] == last
    for a, b in zip(folds, folds[1:]):
        assert a["window"][1] < b["window"][0], "folds overlap or non-monotone"


def test_family_falsification_rules_bound_to_rule_sites(freeze):
    rs = freeze["rule_set_r1_r6"]
    binds = {b["family_key"]: b for b in rs["family_falsification_binding"]}
    assert set(binds) == {"VOLNG1-A4-P2", "VOLNG1-A5-P2"}
    assert binds["VOLNG1-A4-P2"]["rule_source"].startswith(
        "VOLNG1-A4-P2.json falsification_rule")
    assert binds["VOLNG1-A5-P2"]["rule_source"].startswith(
        "VOLNG1-A5-P2.json falsification_rule")
    assert "VOL_NG1_REJECT_ALL" in binds["VOLNG1-A4-P2"]["binding"]
    assert "VOL_NG1_REJECT_ALL" in binds["VOLNG1-A5-P2"]["binding"]
    # binding sites are declared in the section-6 battery law
    sites = {r["family_key"]: r["binding_site"] for r in
             freeze["i_phase_control_battery"]["family_falsification_rules"]}
    assert sites == {"VOLNG1-A4-P2": "R1/R5", "VOLNG1-A5-P2": "R2"}


# --------------------------------------------- section 4: cost binding
def test_cost_contract_binding(freeze):
    bind = freeze["cost_contract_binding"]
    cc = json.loads(CC_PATH.read_text())
    assert bind["cost_contract_json_sha256"] == _sha256(CC_PATH)
    assert bind["tier_ladder"] == cc["tier_ladder"] == [1.0, 1.5, 2.0]
    assert bind["primary_tier"] == cc["primary_tier"] == 2.0
    assert bind["q16_path_ladder_carried"] is True
    assert bind["q16_law_verbatim"] == cc["q16_law"]
    assert bind["q8_law_verbatim"] == cc["q8_law"]
    assert bind["cost_once_per_fill_law_verbatim"] == cc["execution_note"]
    assert "once per fill" in bind["cost_once_per_fill_law_verbatim"]


def test_execution_layer_is_the_p1_event_adjusted_layer(freeze):
    bind = freeze["cost_contract_binding"]
    assert bind["corp_actions_py_sha256"] == _sha256(CA_PATH)
    assert "corp_actions.py" in bind["execution_layer_law"]
    assert "MANDATORY" in bind["execution_layer_law"]
    assert "never raw" in bind["execution_layer_law"]


def test_per_leg_path_formulas_match_cost_contract(freeze):
    bind = freeze["cost_contract_binding"]
    cc = json.loads(CC_PATH.read_text())
    formulas = {leg: v["path_cost"]["formula"]
                for leg, v in cc["legs"].items()}
    short_f = bind["per_leg_path_law"][
        "SHORT_bucket_legs_VXX_UVXY_SVXY_VIXY"]["path_formula"]
    mid_f = bind["per_leg_path_law"]["MID_bucket_legs_VIXM_VXZ"][
        "path_formula"]
    for leg in ("VXX", "UVXY", "SVXY", "VIXY"):
        assert formulas[leg] == short_f
    for leg in ("VIXM", "VXZ"):
        assert formulas[leg] == mid_f


# ---------------------------------------------- section 5: ranking basis
def test_ranking_by_preregistered_evidence_strength_only(freeze, panel):
    rb = freeze["ranking_basis"]
    assert rb["no_outcome_input_declaration"] is True
    assert "P-15" in rb["law"]
    assert rb["p15_law_restatement"] == ("smoke numbers kill + disclose, "
                                         "never select (P-15)")
    ranked = rb["ranked_evidence"]
    assert [e["rank"] for e in ranked] == [1, 2]
    assert [e["family_key"] for e in ranked] == [
        "VOLNG1-A5-P2", "VOLNG1-A4-P2"]
    prow = {p["proposal_id"]: p for p in panel["proposals"]}
    for e in ranked:
        assert e["novelty_margin"] == pytest.approx(
            prow[e["family_key"]]["margin_to_gate"], abs=1e-9)
        assert e["pooled_abs_max"] == pytest.approx(
            prow[e["family_key"]]["pooled_abs_max"], abs=1e-9)


# ------------------------------------------- section 6: control battery
def test_battery_binding_per_runner(freeze):
    bat = freeze["i_phase_control_battery"]
    mandated = {"index_only_shadow", "cost_path_control",
                "calendar_clock_shadow", "placebo",
                "invalid_null_distinction"}
    controls = bat["controls"]
    for name in mandated:
        assert controls[name]["mandatory"] is True, name
    runners = bat["runner_map"]
    assert {r["arm_id"] for r in runners} == {
        a["arm_id"] for a in freeze["arm_configuration_plan"]["arms"]}
    for r in runners:
        assert set(r["battery_binding"]) == mandated | {
            "family_falsification_rule"}
    # frozen battery constants (symbolic at D1, frozen HERE at S)
    assert controls["calendar_clock_shadow"]["calendar_shift_k_sessions"] == 5
    assert controls["placebo"]["placebo_seed"] == 20260912
    assert "matched marginals" in controls["placebo"]["spec"]
    assert "VETOES, not suggestions" in bat["battery_law"]
    assert "NOT_RUN" in bat["battery_law"]


def test_battery_index_only_shadows_match_d1_specs(freeze):
    bat = freeze["i_phase_control_battery"]
    ios = bat["controls"]["index_only_shadow"]
    a4p = json.loads(A4_PATH.read_text())["control_battery_spec"][
        "index_only_shadow"]
    a5p = json.loads(A5_PATH.read_text())["control_battery_spec"][
        "index_only_shadow"]
    assert "no ETP price anywhere in the state" in ios["a4_p2_spec"]
    assert "no ETP price anywhere" in ios["a5_p2_spec"]
    assert ios["a4_p2_spec"] != a4p["spec"]  # adapted, not copied bytes
    assert "index" in ios["a4_p2_spec"] and "index" in ios["a5_p2_spec"]


def test_battery_cites_family_falsification_rules_by_sha(freeze):
    bat = freeze["i_phase_control_battery"]
    frules = {r["family_key"]: r
              for r in bat["family_falsification_rules"]}
    assert frules["VOLNG1-A4-P2"]["binding_site"] == "R1/R5"
    assert frules["VOLNG1-A5-P2"]["binding_site"] == "R2"
    assert frules["VOLNG1-A4-P2"]["rule_citation"].endswith(EXPECTED_A4_SHA)
    assert frules["VOLNG1-A5-P2"]["rule_citation"].endswith(EXPECTED_A5_SHA)
    # rule citations resolve to the committed proposal bytes
    assert EXPECTED_A4_SHA == _sha256(A4_PATH)
    assert EXPECTED_A5_SHA == _sha256(A5_PATH)


# ------------------------------------------------ negative scan (Q-6/P-15)
def _walk_keys(node, out):
    if isinstance(node, dict):
        for k, v in node.items():
            out.append(k)
            _walk_keys(v, out)
    elif isinstance(node, list):
        for el in node:
            _walk_keys(el, out)


#: dict-valued containers whose INNER numeric leaves are the frozen,
#: declared state-code semantics of the rule forms (the D2 committed
#: action maps); their contents are parameters, not outcomes
ACTION_MAP_CONTAINER_KEYS = {
    "regime_action_map", "state_action_map", "action_pole_encoding",
    "bucket_action_map",
}


def _walk_numeric_leaves(node, key=None, out=None, container_ok=False):
    if out is None:
        out = []
    if isinstance(node, dict):
        inner_ok = container_ok or key in ACTION_MAP_CONTAINER_KEYS
        for k, v in node.items():
            _walk_numeric_leaves(v, k, out, inner_ok)
    elif isinstance(node, list):
        for el in node:
            _walk_numeric_leaves(el, key, out, container_ok)
    elif isinstance(node, bool):
        pass
    elif isinstance(node, (int, float)):
        if not container_ok:
            out.append((key, node))
    return out


def test_negative_scan_no_outcome_worded_keys(freeze):
    keys: list[str] = []
    _walk_keys(freeze, keys)
    hits = [k for k in keys if OUTCOME_KEY_RE.search(k)]
    assert not hits, f"outcome-worded keys in freeze: {hits}"


def test_negative_scan_numeric_leaves_whitelisted_only(freeze):
    nums = _walk_numeric_leaves(freeze)
    bad = [(k, v) for k, v in nums
           if k is None or k not in ALLOWED_NUMERIC_KEYS]
    assert not bad, f"non-whitelisted numeric leaves (outcome risk): {bad}"


def test_negative_scan_no_scored_artifact_references(freeze):
    raw = FREEZE_PATH.read_text()
    for token in ("PROVISIONAL_STAGE_A_SURVIVOR_LOCKED",
                  "scored=True", "compute_outcomes"):
        assert token not in raw, token
    # the survivor word may appear only inside the frozen RULE law text
    assert "PROVISIONAL_STAGE_A_SURVIVOR" in raw  # survivor_law definition


def test_embedded_test_command_matches_packet(freeze):
    assert freeze["test_command"] == (
        "cd " + str(REPO_ROOT) + " && "
        "/Users/hoangminhlong/my-quantitative/.venv/bin/python "
        "-m pytest tests/test_vol_ng1_s.py -q")
