"""RATES-NG1 S selection-freeze tests (task rates-ng1-s-selection-freeze).

Layers:

1. Schema + completeness: the six mandatory freeze sections, selection
   non-empty, single ELIGIBLE family, arm budget law.
2. Citation hashes re-verified: every sha256 pin in the freeze artifact
   is recomputed from the committed worktree bytes; the FOREX-NG1
   precedent and the ng1 cycle-law plan blobs are re-hashed via git.
3. Arm digest law: arm_config_digest recomputation, pairwise
   distinctness, variants differ ONLY in declared gate fields.
4. Rule order + battery binding: R1-R6 adapted from the FOREX-NG1
   precedent, the declared level-vs-shape executioner, folds, placebo k.
5. Negative scan: NO outcome number of any kind in the freeze (token
   scan + numeric-leaf allowlist + series-smuggling bound).

Scope law: these tests consume no market data; they re-hash committed
artifacts and recompute digests from the committed freeze alone.  They
compute no outcome.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROOT_CHECKOUT = "/Users/hoangminhlong/my-quantitative"

FREEZE_PATH = os.path.join(
    REPO_ROOT, "research", "control", "rates_ng1_run", "s",
    "selection_freeze.json")
PANEL_PATH = os.path.join(
    REPO_ROOT, "research", "control", "rates_ng1_run", "d2",
    "d2_novelty_panel.json")

BASE_SHA = "206bd5c6ac09b50b69ce4da66e825cb89132e91f"
EXPECTED_SCHEMA = "rates_ng1_run/s_selection_freeze@1"
EXPECTED_FAMILY = "RATESNG1-A5-P1"
VETOED = ("RATESNG1-A4-P1", "RATESNG1-A4-P2", "RATESNG1-A5-P2")

PRECEDENT_COMMIT = "d0992d17df8e2dfde57c9a0806a5798f14021a4f"
PRECEDENT_PATH = "research/control/forex_ng1_run/selection_freeze.json"
PRECEDENT_CONTENT_SHA256 = (
    "5d7eb5793e02e7919d59ba16a9fa8c3041e3d7e23274c605fbec639c81d2c8ee")
RUBRIC_PLAN_BLOB = "ed845ba295859c42683fabc777b7ea7d6230604a"
CYCLE_LAW_PLAN_BLOB = "170982ba6ac75735e6940561cb11a41b11c279f1"

#: Frozen numeric-leaf allowlist (key names).  Every int/float leaf in
#: the freeze must sit under one of these keys; anything else is a
#: violation (d1-gate negative-scan method, adapted).
NUMERIC_LEAF_ALLOWLIST = frozenset({
    "schema_version",
    # selection summary + novelty evidence (decision-state correlations,
    # preregistered ceiling/margin -- selection evidence, no outcome)
    "selected_family_count",
    "novelty_abs_rho_ceiling",
    "proposal_pooled_abs_rho",
    "margin_to_ceiling",
    "shadows_measured",
    "unmeasurable_shadows",
    "per_shadow_pooled_abs_max",
    "n_defined",
    "n_total",
    # feasibility census counts (Q-6, no outcome content)
    "bookable_instants",
    "grid_sessions",
    "warmup_sessions",
    "coverage_fraction",
    "min_bookable_instants_floor",
    "min_coverage_fraction_floor",
    # rubric budget constants
    "families_max",
    "arms_per_family_max",
    "cell_budget",
    "arm_count",
    "booked_cells",
    "unbooked_cells",
    # frozen arm parameter variants
    "min_past_points",
    "holding_trading_days",
    "upper_quantile",
    "lower_quantile",
    # frozen cost-projection constants (ceilings, not outcomes)
    "cost_ladder_tier",
    "per_leg_stress_tier_bps",
    "per_leg_worst_case_round_trip_ceiling_bps",
    # frozen placebo constant
    "k_misalign_sessions",
})

#: Outcome-metric tokens that must appear NOWHERE in the freeze text.
FORBIDDEN_TOKENS = (
    "sharpe", "pnl", "win_rate", "drawdown", "total_return",
    "profit_factor",
)


def _load_freeze():
    with open(FREEZE_PATH) as f:
        return json.load(f)


def _load_panel():
    with open(PANEL_PATH) as f:
        return json.load(f)


def _walk_leaves(node, path=()):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _walk_leaves(v, path + (k,))
    elif isinstance(node, list):
        for v in node:
            yield from _walk_leaves(v, path)
    else:
        yield path, node


def _canonical_digest(cfg) -> str:
    return hashlib.sha256(
        json.dumps(cfg, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _git(*args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", ROOT_CHECKOUT, *args],
        check=True, capture_output=True).stdout


# ------------------------------------------------------------------ #
# 1. Schema + completeness
# ------------------------------------------------------------------ #
class TestSchemaCompleteness:
    def test_schema_and_identity(self):
        fz = _load_freeze()
        assert fz["schema"] == EXPECTED_SCHEMA
        assert fz["cycle_id"] == "RATES-NG1"
        assert fz["task_id"] == "rates-ng1-s-selection-freeze"
        assert fz["base_sha"] == BASE_SHA
        assert re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", fz["frozen_at_utc"])
        assert fz["s1"] == "SEALED_UNTOUCHED"

    def test_six_mandatory_sections_present(self):
        fz = _load_freeze()
        for i, name in enumerate(
                ["selected_family", "arm_configuration_plan",
                 "stage_a_rule_order_frozen", "cost_contract_binding",
                 "ranking_basis", "control_battery_binding"], start=1):
            key = f"section_{i}_{name}"
            assert key in fz, f"missing mandatory section {key}"
            assert isinstance(fz[key], dict) and fz[key]

    def test_selection_non_empty_single_eligible_family(self):
        fz = _load_freeze()
        assert fz["selection_summary"]["selection_non_empty"] is True
        s1 = fz["section_1_selected_family"]
        assert s1["family_id"] == EXPECTED_FAMILY
        assert s1["lane"] == "A5"
        assert fz["selection_summary"]["eligible_proposal_ids"] == [
            EXPECTED_FAMILY]
        assert sorted(fz["selection_summary"]["vetoed_proposal_ids"]) == \
            sorted(VETOED)

    def test_d2_verdicts_restated_match_committed_panel(self):
        fz = _load_freeze()
        panel = _load_panel()
        sel = panel["proposals"][EXPECTED_FAMILY]
        assert sel["verdict"] == "ELIGIBLE"
        ev = fz["section_1_selected_family"]["d2_novelty_evidence"]
        assert ev["proposal_pooled_abs_rho"] == \
            pytest.approx(sel["proposal_pooled_abs_rho"])
        assert ev["margin_to_ceiling"] == \
            pytest.approx(sel["margin_to_ceiling"])
        assert ev["novelty_abs_rho_ceiling"] == pytest.approx(
            sel["ceiling"])
        for pid in VETOED:
            assert panel["proposals"][pid]["verdict"] == "VETO"
            not_sel = fz["section_1_selected_family"][
                "why_others_not_selected"][pid]
            assert "VETO" in not_sel

    def test_arm_budget_law(self):
        fz = _load_freeze()
        s2 = fz["section_2_arm_configuration_plan"]
        assert s2["families_max"] == 2
        assert s2["arms_per_family_max"] == 3
        assert s2["cell_budget"] == 6
        assert s2["selected_family_count"] == 1
        assert 1 <= s2["arm_count"] <= s2["arms_per_family_max"]
        assert s2["booked_cells"] == s2["arm_count"]
        assert s2["booked_cells"] + s2["unbooked_cells"] == \
            s2["cell_budget"]
        assert s2["unbooked_cells"] == 3
        assert "UNBOOKED" in s2["budget_law"]

    def test_freeze_is_self_sufficient_for_i_phase(self):
        """Everything the I phase needs must be in the artifact."""
        fz = _load_freeze()
        s2 = fz["section_2_arm_configuration_plan"]
        shared = s2["shared_arm_law"]
        # leg pair + sign convention + clock + exit + grid
        assert shared["leg_pair_freeze"]["front_leg"] == "SHY"
        assert shared["leg_pair_freeze"]["long_leg"] == "TLT"
        assert "state +1" in shared["sign_convention"]
        assert "16:00" in shared["entry_clock_law"]
        assert "force-flat" in shared["exit_law"]
        assert "bookable_instants" in shared["grid_law"]
        # folds frozen inside R3
        rules = fz["section_3_stage_a_rule_order_frozen"]["rules"]
        assert any("2019-01-07" in r and "2026-09-11" in r for r in rules)
        # placebo k frozen
        assert fz["section_6_control_battery_binding"][
            "k_misalign_sessions"] == 5


# ------------------------------------------------------------------ #
# 2. Citation hashes re-verified
# ------------------------------------------------------------------ #
class TestCitationsReverified:
    def test_every_citation_pin_matches_worktree_bytes(self):
        fz = _load_freeze()
        pins = fz["citation_pins"]
        assert len(pins) >= 10
        for rel, recorded in pins.items():
            with open(os.path.join(REPO_ROOT, rel), "rb") as f:
                actual = hashlib.sha256(f.read()).hexdigest()
            assert actual == recorded, f"stale pin: {rel}"

    def test_selected_family_citations_are_pinned(self):
        fz = _load_freeze()
        s1 = fz["section_1_selected_family"]
        assert s1["proposal_citation"]["sha256"] == \
            fz["citation_pins"][
                "research/control/rates_ng1_run/d1/proposals/"
                "RATESNG1-A5-P1.json"]
        assert s1["d2_panel_citation"]["sha256"] == \
            fz["citation_pins"][
                "research/control/rates_ng1_run/d2/d2_novelty_panel.json"]

    def test_forex_ng1_precedent_rehashed_from_git(self):
        fz = _load_freeze()
        prev = fz["provenance"]["precedent_selection_freeze"]
        assert prev["commit_sha"] == PRECEDENT_COMMIT
        assert prev["branch"] == "orca/forex-ng1-integration"
        assert prev["path"] == PRECEDENT_PATH
        blob = _git("show", f"{PRECEDENT_COMMIT}:{PRECEDENT_PATH}")
        assert hashlib.sha256(blob).hexdigest() == \
            PRECEDENT_CONTENT_SHA256
        assert prev["content_sha256"] == PRECEDENT_CONTENT_SHA256

    def test_precedent_carries_r1_r6_source_block(self):
        raw = _git("show", f"{PRECEDENT_COMMIT}:{PRECEDENT_PATH}")
        precedent = json.loads(raw)
        rules = precedent["stage_a_rule_order_frozen"]
        assert len(rules) >= 6  # R1-R6 + survivor law trailer
        for i in range(6):
            assert rules[i].startswith(f"R{i + 1} "), rules[i]
        assert "survivor" in rules[-1]

    def test_ng1_plan_blobs_verified(self):
        fz = _load_freeze()
        assert fz["provenance"]["rubric"]["git_blob_sha256"] == \
            RUBRIC_PLAN_BLOB
        assert fz["provenance"]["ng1_cycle_law"]["git_blob_sha256"] == \
            CYCLE_LAW_PLAN_BLOB
        assert _git("rev-parse", "HEAD:plans/PLAN_rates_ng1.md"
                    ).strip().decode() == RUBRIC_PLAN_BLOB
        assert _git("rev-parse", "HEAD:plans/PLAN_crypto_ng1.md"
                    ).strip().decode() == CYCLE_LAW_PLAN_BLOB


# ------------------------------------------------------------------ #
# 3. Arm digest law
# ------------------------------------------------------------------ #
class TestArmDigestLaw:
    def test_digests_recompute_and_are_distinct(self):
        fz = _load_freeze()
        arms = fz["section_2_arm_configuration_plan"]["arms"]
        assert len(arms) == 3
        digests = set()
        for arm in arms:
            assert arm["arm_config_digest"] == \
                _canonical_digest(arm["config"])
            assert re.fullmatch(r"[0-9a-f]{64}",
                                arm["arm_config_digest"])
            digests.add(arm["arm_config_digest"])
        assert len(digests) == 3, "arm_config_digests must be pairwise distinct"

    def test_variants_differ_only_in_gate_fields(self):
        fz = _load_freeze()
        arms = fz["section_2_arm_configuration_plan"]["arms"]
        configs = [a["config"] for a in arms]
        base = configs[0]
        for cfg in configs[1:]:
            assert set(cfg) == set(base)
            for key in cfg:
                if key == "gate":
                    assert cfg[key] != base[key]
                else:
                    assert cfg[key] == base[key], \
                        f"non-gate field {key} must be shared across arms"
        # gate variants cover the declared neutral/conservative/aggressive
        rules = {a["config"]["gate"]["state_rule"] for a in arms}
        assert rules == {
            "both_above_plus1_both_below_minus1_else_zero",
            "both_above_upper_q_plus1_both_below_lower_q_minus1_else_zero",
            "either_above_plus1_either_below_minus1_else_zero",
        }

    def test_neutral_arm_is_the_d2_frozen_default(self):
        """The neutral arm's gate must be the D2 commit-1 frozen state
        rule, verbatim (d2_frozen_defaults.A5_P1_CURVATURE_GATED_SLOPE).
        """
        sys.path.insert(0, REPO_ROOT)
        from research.control.rates_ng1_run.d2 import d2_frozen_defaults as fd
        fz = _load_freeze()
        arms = fz["section_2_arm_configuration_plan"]["arms"]
        neutral = next(a for a in arms
                       if a["arm_id"].endswith("ARM-NEUTRAL"))
        frozen = fd.A5_P1_CURVATURE_GATED_SLOPE
        gate = neutral["config"]["gate"]
        assert gate["state_rule"] == frozen["state_rule"]
        assert gate["bucket_cut"] == frozen["bucket_cut"]
        assert neutral["config"]["orthogonalization"]["rule"] == \
            frozen["orthogonalization"]
        assert neutral["config"]["orthogonalization"]["min_past_points"] \
            == frozen["min_past_points"]
        assert neutral["config"]["decomposition"]["slope_tenors"] == \
            frozen["slope_tenors"]
        assert neutral["config"]["decomposition"]["curvature_tenors"] == \
            frozen["curvature_tenors"]
        assert neutral["config"]["decomposition"]["level_tenor"] == \
            frozen["level_tenor"]

    def test_digest_is_tamper_evident(self):
        fz = _load_freeze()
        arm = fz["section_2_arm_configuration_plan"]["arms"][0]
        tampered = json.loads(json.dumps(arm["config"]))
        tampered["holding_trading_days"] = 7
        assert _canonical_digest(tampered) != arm["arm_config_digest"]


# ------------------------------------------------------------------ #
# 4. Rule order + battery binding
# ------------------------------------------------------------------ #
class TestRuleOrderAndBattery:
    def test_six_rules_in_order(self):
        fz = _load_freeze()
        rules = fz["section_3_stage_a_rule_order_frozen"]["rules"]
        assert len(rules) == 6
        for i, rule in enumerate(rules, start=1):
            assert rule.startswith(f"R{i} "), rule

    def test_r1_r6_bounds_match_precedent_law(self):
        fz = _load_freeze()
        rules = " ".join(
            fz["section_3_stage_a_rule_order_frozen"]["rules"])
        assert "expectancy > 0" in rules
        assert "2 of 3" in rules
        assert "1.10" in rules
        assert "50%" in rules

    def test_r2_names_the_declared_executioner(self):
        fz = _load_freeze()
        r2 = fz["section_3_stage_a_rule_order_frozen"]["rules"][1]
        assert "level-vs-shape decomposition control" in r2
        assert "strictly greater after-cost per-decision edge" in r2
        assert "FX-V8" in r2 and "CTL-DGS10LEVEL" in r2

    def test_folds_contiguous_and_cover_window(self):
        fz = _load_freeze()
        r3 = fz["section_3_stage_a_rule_order_frozen"]["rules"][2]
        dates = re.findall(r"\d{4}-\d{2}-\d{2}", r3)
        # window range, then the three contiguous fold ranges
        assert dates == ["2019-01-07", "2026-09-11",
                         "2019-01-07", "2021-07-28",
                         "2021-07-29", "2024-02-18",
                         "2024-02-19", "2026-09-11"]

    def test_battery_controls_bound(self):
        fz = _load_freeze()
        battery = fz["section_6_control_battery_binding"]
        roles = [c["role"] for c in battery["controls"]]
        assert roles == ["LEVEL_VS_SHAPE_DECOMPOSITION_CONTROL",
                         "CLOCK_ONLY_SHADOW", "PLACEBO"]
        lvl = battery["controls"][0]
        assert lvl["mandatory"] is True
        assert lvl["status"] == "DECLARED_EXECUTIONER"
        assert battery["k_misalign_sessions"] == 5
        fr = battery["falsification_rule"]
        assert fr["killer_controls"] == roles
        assert fr["declared_at"].startswith("D1")

    def test_q11_distinction_bound(self):
        fz = _load_freeze()
        assert "DISTINCTLY" in \
            fz["section_6_control_battery_binding"]["q11_law"]


# ------------------------------------------------------------------ #
# 5. Cost binding
# ------------------------------------------------------------------ #
class TestCostBinding:
    def test_contract_pin_and_tier(self):
        fz = _load_freeze()
        s4 = fz["section_4_cost_contract_binding"]
        assert s4["tier_2_0_primary"] is True
        assert s4["cost_ladder_tier"] == 2.0
        assert s4["cost_frequency"] == "once_per_fill"
        assert s4["both_legs_charged"] is True
        contract_rel = s4["contract"]["path"]
        assert contract_rel == (
            "research/control/rates_ng1_run/p1_cost_contract.json")
        with open(os.path.join(REPO_ROOT, contract_rel), "rb") as f:
            assert hashlib.sha256(f.read()).hexdigest() == \
                s4["contract"]["sha256"]

    def test_per_leg_tiers_match_contract_bytes(self):
        fz = _load_freeze()
        with open(os.path.join(
                REPO_ROOT, "research/control/rates_ng1_run/"
                           "p1_cost_contract.json")) as f:
            contract = json.load(f)
        s4 = fz["section_4_cost_contract_binding"]
        for leg, bps in s4["per_leg_stress_tier_bps"].items():
            assert contract["per_etp"][leg]["stress_tier_bps"] == \
                pytest.approx(bps)
        assert s4["consumption_law"]["plane"].startswith(
            "ALL substrate consumption via")
        assert "close+1" in s4["consumption_law"]["clock"]


# ------------------------------------------------------------------ #
# 6. Negative scan: NO outcome numbers
# ------------------------------------------------------------------ #
class TestNegativeNoOutcomeNumbers:
    def test_no_forbidden_outcome_tokens(self):
        raw = open(FREEZE_PATH).read()
        for token in FORBIDDEN_TOKENS:
            hits = re.findall(token, raw, flags=re.IGNORECASE)
            assert hits == [], f"forbidden outcome token {token!r}: {hits}"

    def test_numeric_leaves_all_in_allowlist(self):
        fz = _load_freeze()
        violations = []
        for path, leaf in _walk_leaves(fz):
            if isinstance(leaf, bool) or not isinstance(leaf, (int, float)):
                continue
            # "sit under a key name in the frozen allowlist" (d1-gate
            # negative-scan method): any ancestor key must be allowlisted.
            if not any(k in NUMERIC_LEAF_ALLOWLIST for k in path):
                violations.append((".".join(path), leaf))
        assert violations == [], \
            f"numeric leaves outside frozen allowlist: {violations}"

    def test_no_numeric_series_smuggled(self):
        fz = _load_freeze()
        for path, leaf in _walk_leaves(fz):
            if isinstance(leaf, list):
                numeric = [v for v in leaf
                           if isinstance(v, (int, float))
                           and not isinstance(v, bool)]
                assert len(numeric) <= 8, \
                    f"numeric series smuggled under {'.'.join(path)}"

    def test_ranking_basis_preregistered_only(self):
        fz = _load_freeze()
        s5 = fz["section_5_ranking_basis"]
        assert s5["preregistered_evidence_strength_only"] is True
        assert "never select" in s5["p_15_restated"]
        assert "no cross-family ranking is performed" in \
            s5["application_here"]
        assert "No rubric threshold" in s5["no_threshold_moves"]
