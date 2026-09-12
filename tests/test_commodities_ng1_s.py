"""COMMODITIES-NG1 S selection-freeze tests (task
commodities-ng1-s-selection-freeze).

Laws under test
---------------
1. Schema and completeness: the freeze carries the SIX mandatory sections
   (selected family + vetoes / arm plan / R1-R6 stage-A rules / cost
   contract binding / ranking basis / I-phase control battery binding);
   selection is NON-EMPTY with exactly ONE eligible family
   (COMMNG1-A4-P2) and three documented vetoes.
2. Verdict consistency: every verdict, pooled |rho|, margin and driving
   shadow recorded in the freeze equals the COMMITTED D2 panel on disk
   (re-read live); A4-P2 is the only ELIGIBLE proposal; the three vetoes
   are each driven by their own price-only re-clock.
3. Arm plan: single family, 3 of 6 budget cells booked and 3 unbooked
   (never padded); arms pairwise distinct by arm_config_digest with the
   digest RECOMPUTED from the recorded arm_config; every parameter value
   is either the D2 frozen neutral default or a member of the convention
   set committed in the D2 panel's frozen_parameter_rationales (parsed
   live); tau and h_max fixed across arms; symmetric tails.
4. R1-R6 stage-A rule order frozen (adapted faithfully from the FOREX-NG1
   freeze precedent at git d0992d17...), survivor clause present, S1
   sealed; folds span the measured counted window of the P2 gate.
5. Cost contract binding: frozen P1 contract sha, tier 2.0 PRIMARY,
   once-per-fill charge law, Q-16 drag carried, the 9 transaction-only
   legs STAY EXCLUDED, bookable set identical to the D1 declaration,
   cost ceilings equal to the D1-cited documentation values.
6. Ranking basis P-15 (preregistered evidence strength only) and the
   binding I-phase battery (mandatory price-only shadow + release-clock
   shadow + shifted-release placebo + the D1 falsification rule; k=4
   frozen; Q-11 invalid-null minimum >= the P2 frozen floor).
7. Citation re-verification: EVERY path+sha256 citation anywhere in the
   freeze is re-hashed from disk (worktree-relative or root-checkout
   read-only); the git-sourced precedent blob is re-hashed via
   ``git show <commit>:<path>``.
8. Negative scan (P-15/no-outcome law): NO outcome numbers anywhere in
   the freeze - recursive banned-key scan plus a numeric-leaf whitelist
   (every numeric leaf must sit under a pre-approved key and the
   whitelist itself contains no outcome vocabulary).  The scanner is
   tested against violating fixtures.

No returns are computed anywhere; the freeze is structure + citations +
preregistered rules only.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

WORKTREE = Path(__file__).resolve().parents[1]
ROOT_CHECKOUT = Path("/Users/hoangminhlong/my-quantitative")

RUN_DIR = WORKTREE / "research" / "control" / "commodities_ng1_run"
FREEZE_PATH = RUN_DIR / "s" / "selection_freeze.json"
PANEL_PATH = RUN_DIR / "d2" / "d2_novelty_panel.json"
P2_PATH = RUN_DIR / "p2_gate.json"
D1_PROPOSALS = {
    pid: RUN_DIR / "d1" / "proposals" / f"{pid}.json"
    for pid in ("COMMNG1-A4-P1", "COMMNG1-A4-P2",
                "COMMNG1-A5-P1", "COMMNG1-A5-P2")
}

SELECTED_ID = "COMMNG1-A4-P2"
VETOED_IDS = ("COMMNG1-A4-P1", "COMMNG1-A5-P1", "COMMNG1-A5-P2")
ALL_IDS = (SELECTED_ID,) + VETOED_IDS
MANDATORY_SECTIONS = (
    "section1_selected_family_and_vetoes",
    "section2_arm_plan",
    "section3_stage_a_rules_r1_r6",
    "section4_cost_contract_binding",
    "section5_ranking_basis",
    "section6_i_phase_control_battery_binding",
)

BANNED_KEY_TOKENS = (
    "pnl", "profit_factor", "sharpe", "drawdown", "win_rate", "hit_rate",
    "expectancy", "total_return", "net_return", "realized_return",
    "payoff", "scored",
)
# Every numeric leaf of the freeze must sit under one of these keys.
# The set contains NO outcome vocabulary (asserted below).
ALLOWED_NUMERIC_KEYS = frozenset({
    # D2 selection evidence (decision-state correlations, not outcomes)
    "pooled_abs_rho",
    "margin_to_ceiling",
    "novelty_ceiling_abs_rho",
    # per-shadow pooled |rho| leaves are keyed by shadow name
    "momentum_63s",
    "generic_dow_tue",
    "v16_close_displace_fade",
    "price_only_shadow",
    # trial accounting
    "trial_budget_cells",
    "booked_cells",
    "unbooked_cells",
    # feasibility (no-PnL counts/floors)
    "bookable_pair_count",
    "per_arm_min_eligible_instants_per_pair",
    "per_arm_min_eligible_instants_pooled",
    # frozen rule parameters (D2 committed defaults / convention values)
    "percentile_window_weeks_w",
    "tail_q_lo",
    "tail_q_hi",
    "trigger_tau_geometry",
    "carry_bound_weeks_h_max",
    "stale_releases_k",
    # cost constants (frozen P1 contract facts; documentation only)
    "primary_tier",
    "tier_ladder",
    "worst_case_round_trip_ceiling_bps",
})


# ----------------------------------------------------------------------- #
# fixtures / helpers
# ----------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def freeze():
    assert FREEZE_PATH.exists(), f"missing freeze artifact {FREEZE_PATH}"
    return json.loads(FREEZE_PATH.read_text())


@pytest.fixture(scope="module")
def panel():
    return json.loads(PANEL_PATH.read_text())


@pytest.fixture(scope="module")
def p2():
    return json.loads(P2_PATH.read_text())


@pytest.fixture(scope="module")
def d1_selected():
    return json.loads(D1_PROPOSALS[SELECTED_ID].read_text())


def canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def arm_digest(arm_config) -> str:
    return hashlib.sha256(canon(arm_config)).hexdigest()


def iter_named_keys(obj, prefix=""):
    """Yield every key path (dotted) in the structure."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else k
            yield path, k, v
            yield from iter_named_keys(v, path)
    elif isinstance(obj, list):
        for v in obj:
            yield from iter_named_keys(v, prefix)


def numeric_leaves(obj, named_key=None):
    """Yield (nearest_named_dict_key, value) for every int/float leaf.

    List indices are transparent: a number inside a list is attributed to
    the nearest dict key ABOVE the list.
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from numeric_leaves(v, k)
    elif isinstance(obj, list):
        for v in obj:
            yield from numeric_leaves(v, named_key)
    elif isinstance(obj, bool):
        return
    elif isinstance(obj, (int, float)):
        yield named_key, obj


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_git_blob(root: Path, commit: str, relpath: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), "show", f"{commit}:{relpath}"],
        check=True, capture_output=True).stdout
    return hashlib.sha256(out).hexdigest()


def all_citations(freeze):
    """Every dict anywhere in the freeze carrying both 'path' and
    'sha256' (a citation) - returned as (location, entry) pairs."""
    found = []

    def walk(obj, path=""):
        if isinstance(obj, dict):
            if isinstance(obj.get("path"), str) and \
                    isinstance(obj.get("sha256"), str):
                found.append((path, obj))
            for k, v in obj.items():
                walk(v, f"{path}.{k}" if path else k)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, f"{path}[{i}]")
    walk(freeze)
    return found


# ----------------------------------------------------------------------- #
# scanner self-tests (the negative scanner itself must be trustworthy)
# ----------------------------------------------------------------------- #

def banned_key_paths(obj):
    hits = []
    for path, key, _ in iter_named_keys(obj):
        low = key.lower()
        for token in BANNED_KEY_TOKENS:
            if token in low:
                hits.append((path, token))
    return hits


def non_whitelisted_numeric_keys(obj):
    bad = []
    for key, _value in numeric_leaves(obj):
        if key not in ALLOWED_NUMERIC_KEYS:
            bad.append(key)
    return bad


def test_scanner_flags_outcome_fixtures():
    assert banned_key_paths({"pnl": 1.0}) != []
    assert banned_key_paths({"nested": {"profit_factor": 1.2}}) != []
    assert banned_key_paths({"expectancy_after_cost": 0.001}) != []
    assert banned_key_paths({"a": [{"win_rate": 0.5}]}) != []
    assert non_whitelisted_numeric_keys({"pnl": 0.25}) == ["pnl"]
    assert non_whitelisted_numeric_keys({"sharpe": 1.1}) == ["sharpe"]
    assert non_whitelisted_numeric_keys(
        {"x": {"drawdown": -0.1}}) == ["drawdown"]


def test_scanner_allows_clean_fixtures():
    assert banned_key_paths({"pooled_abs_rho": 0.1, "booked_cells": 3}) == []
    assert non_whitelisted_numeric_keys(
        {"pooled_abs_rho": 0.1, "tier_ladder": [2.0, 1.0],
         "b": {"tail_q_lo": 0.1}}) == []


def test_whitelist_contains_no_outcome_vocabulary():
    for key in ALLOWED_NUMERIC_KEYS:
        low = key.lower()
        for token in BANNED_KEY_TOKENS:
            assert token not in low, (key, token)


# ----------------------------------------------------------------------- #
# 1. schema + completeness
# ----------------------------------------------------------------------- #

def test_schema_and_header(freeze):
    assert freeze["schema"] == "commodities_ng1_run/s_selection_freeze@1"
    assert freeze["cycle_id"] == "COMMODITIES-NG1"
    assert freeze["task_id"] == "commodities-ng1-s-selection-freeze"
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$",
                    freeze["frozen_at_utc"])
    assert freeze["s1"] == "SEALED_UNTOUCHED"
    assert freeze["outcome_knowledge_declaration"]["status"] == \
        "OUTCOME_BLIND_AT_FREEZE"
    assert "never tuned" in freeze["outcome_knowledge_declaration"]["law"]
    assert "no rescue" in freeze["outcome_knowledge_declaration"]["no_rescue"]


def test_six_mandatory_sections_present(freeze):
    assert freeze["mandatory_sections_index"] == list(MANDATORY_SECTIONS)
    for section in MANDATORY_SECTIONS:
        assert section in freeze, section


def test_selection_non_empty_single_family(freeze):
    s1 = freeze["section1_selected_family_and_vetoes"]
    assert s1["selection_non_empty"] is True
    assert s1["selected_family"]["proposal_id"] == SELECTED_ID
    assert s1["selected_family"]["d2_verdict"] == "ELIGIBLE"
    assert len(s1["vetoes"]) == 3
    assert {v["proposal_id"] for v in s1["vetoes"]} == set(VETOED_IDS)
    ids = ([s1["selected_family"]["proposal_id"]]
           + [v["proposal_id"] for v in s1["vetoes"]])
    assert sorted(ids) == sorted(ALL_IDS)


def test_freeze_base_sha_matches_dispatch(freeze):
    assert freeze["base_sha"] == \
        "c40d6f1313ad9cfea7dbcf376ffe2b46d15bb5a8"
    assert freeze["branch"] == "orca/commodities-ng1-integration"


# ----------------------------------------------------------------------- #
# 2. verdict consistency vs the committed D2 panel (re-read live)
# ----------------------------------------------------------------------- #

def test_selected_row_matches_d2_panel(freeze, panel):
    sel = freeze["section1_selected_family_and_vetoes"]["selected_family"]
    p = panel["proposals"][SELECTED_ID]
    assert p["verdict"] == "ELIGIBLE"
    assert sel["d2_verdict"] == p["verdict"]
    assert sel["pooled_abs_rho"] == p["proposal_pooled_abs_rho"]
    assert sel["margin_to_ceiling"] == p["margin_to_ceiling"]
    assert sel["driving_shadow"] == p["driving_shadow"]
    assert sel["novelty_ceiling_abs_rho"] == \
        panel["ceiling"]["abs_rho_ceiling"] == 0.2
    # the driving shadow is the argmax of the per-shadow pooled |rho|
    per_shadow = {sh: abs(sv["pearson_pooled"])
                  for sh, sv in p["shadows"].items()}
    for sh, val in sel["per_shadow_pooled_abs_rho"].items():
        assert val == per_shadow[sh], sh
    assert max(per_shadow, key=per_shadow.get) == sel["driving_shadow"]


def test_veto_rows_match_d2_panel(freeze, panel):
    for veto in freeze["section1_selected_family_and_vetoes"]["vetoes"]:
        p = panel["proposals"][veto["proposal_id"]]
        assert p["verdict"] == "VETO"
        assert veto["verdict"] == "VETO"
        assert veto["pooled_abs_rho"] == p["proposal_pooled_abs_rho"]
        assert veto["margin_to_ceiling"] == p["margin_to_ceiling"]
        assert veto["driving_shadow"] == p["driving_shadow"]
        # every veto this cycle is driven by the price-only re-clock
        assert veto["driving_shadow"] == "price_only_shadow"
        assert len(veto["reason"]) > 80


def test_a4p2_is_the_only_eligible_and_margin_positive(panel):
    verdicts = {pid: p["verdict"]
                for pid, p in panel["proposals"].items()}
    assert verdicts == {
        "COMMNG1-A4-P1": "VETO",
        "COMMNG1-A4-P2": "ELIGIBLE",
        "COMMNG1-A5-P1": "VETO",
        "COMMNG1-A5-P2": "VETO",
    }
    p = panel["proposals"][SELECTED_ID]
    assert p["margin_to_ceiling"] > 0.0
    assert p["proposal_pooled_abs_rho"] <= 0.2
    assert all(len(p["shadows"][sh]) > 0 for sh in p["shadows"])
    # no UNMEASURABLE shadow anywhere => no VETO_PENDING applies
    for pid, prop in panel["proposals"].items():
        assert prop["unmeasurable_shadows"] == [], pid


# ----------------------------------------------------------------------- #
# 3. arm plan
# ----------------------------------------------------------------------- #

def test_budget_accounting_never_padded(freeze):
    s2 = freeze["section2_arm_plan"]
    ta = freeze["trial_accounting"]
    assert s2["trial_budget_cells"] == ta["trial_budget_cells"] == 6
    assert s2["booked_cells"] == ta["booked_cells"] == 3
    assert s2["unbooked_cells"] == ta["unbooked_cells"] == 3
    assert s2["booked_cells"] + s2["unbooked_cells"] == 6
    assert "never padded" in s2["unbooked_policy"].lower()
    assert "never padded" in ta["unbooked_policy"].lower()
    assert s2["single_family"] == SELECTED_ID
    assert len(s2["arms"]) == 3
    assert all(a["selection_status"] == "BOOKED" for a in s2["arms"])
    assert ta["booked_arm_ids"] == [a["arm_id"] for a in s2["arms"]]


def test_arms_pairwise_distinct_digests_recomputed(freeze):
    arms = freeze["section2_arm_plan"]["arms"]
    digests = [a["arm_config_digest"] for a in arms]
    assert len(set(digests)) == len(digests) == 3
    for arm in arms:
        assert arm["family"] == SELECTED_ID
        assert arm["arm_config_digest"] == arm_digest(arm["arm_config"])
        assert len(arm["a_priori_rationale"]) > 80


def test_roles_one_anchor_two_neighbours(freeze):
    roles = [a["role"] for a in freeze["section2_arm_plan"]["arms"]]
    assert sorted(roles) == ["ANCHOR", "NEIGHBOUR", "NEIGHBOUR"]


def _convention_set(rationale: str) -> set:
    m = re.search(r"\{([^}]*)\}", rationale)
    assert m, rationale
    return {float(x) for x in m.group(1).split(",")}


def test_arm_parameters_from_d2_committed_envelope(freeze, panel):
    """Every parameter value must be the D2 neutral default or a member
    of the convention set committed in the D2 rationale text - proven
    against the LIVE panel, not hard-coded sets alone."""
    s2 = freeze["section2_arm_plan"]
    fp = panel["frozen_parameters"]
    rat = panel["frozen_parameter_rationales"]
    windows = _convention_set(rat["percentile_window_weeks"])
    tails = _convention_set(rat["tail_cut"])
    assert windows == {52.0, 104.0, 156.0}
    assert tails == {0.05, 0.10, 0.20}
    neutral = {
        "percentile_window_weeks_w": float(fp["percentile_window_weeks"]),
        "tail_q_lo": float(fp["tail_cut"]),
        "tail_q_hi": round(1.0 - float(fp["tail_cut"]), 10),
        "trigger_tau_geometry": float(fp["trigger_tau_geometry"]),
        "carry_bound_weeks_h_max": float(fp["carry_bound_weeks_a4p2"]),
    }
    seen_param_sets = []
    for arm in s2["arms"]:
        params = arm["arm_config"]["parameters"]
        seen_param_sets.append(json.dumps(params, sort_keys=True))
        # window: a committed convention value
        assert float(params["percentile_window_weeks_w"]) in windows
        # tail: a committed convention value, symmetric, both halves held
        assert float(params["tail_q_lo"]) in tails
        assert float(params["tail_q_hi"]) == \
            round(1.0 - float(params["tail_q_lo"]), 10)
        # single-declared-convention parameters fixed at the neutral value
        assert float(params["trigger_tau_geometry"]) == \
            neutral["trigger_tau_geometry"]
        assert float(params["carry_bound_weeks_h_max"]) == \
            neutral["carry_bound_weeks_h_max"]
    # the ANCHOR carries exactly the neutral defaults
    anchor = next(a for a in s2["arms"] if a["role"] == "ANCHOR")
    assert {k: float(v) for k, v in
            anchor["arm_config"]["parameters"].items()} == neutral
    # the neighbours differ from the anchor on exactly ONE pre-declared
    # AXIS each (the tail axis couples q_lo/q_hi and moves symmetrically)
    AXIS_FIELDS = {
        "window": ("percentile_window_weeks_w",),
        "tail": ("tail_q_lo", "tail_q_hi"),
        "trigger": ("trigger_tau_geometry",),
        "carry_bound": ("carry_bound_weeks_h_max",),
    }

    def differing_axes(params_a, params_b):
        return {name for name, fields in AXIS_FIELDS.items()
                if any(float(params_a[f]) != float(params_b[f])
                       for f in fields)}
    anchor_sig = json.dumps(anchor["arm_config"]["parameters"],
                            sort_keys=True)
    neighbour_axes = []
    for arm in s2["arms"]:
        if arm["role"] == "NEIGHBOUR":
            sig = json.dumps(arm["arm_config"]["parameters"], sort_keys=True)
            axes = differing_axes(anchor["arm_config"]["parameters"],
                                  arm["arm_config"]["parameters"])
            assert len(axes) == 1, (arm["arm_id"], axes)
            if axes == {"tail"}:
                p = arm["arm_config"]["parameters"]
                assert float(p["tail_q_hi"]) == \
                    round(1.0 - float(p["tail_q_lo"]), 10)
            assert sig != anchor_sig
            neighbour_axes.append(axes.pop())
    # the two neighbours move DIFFERENT axes (genuinely distinct variants)
    assert sorted(neighbour_axes) == ["tail", "window"]
    # and the three parameter sets are pairwise distinct
    assert len(set(seen_param_sets)) == 3


def test_execution_and_cost_constants_identical_across_arms(freeze):
    arms = freeze["section2_arm_plan"]["arms"]
    ex0 = arms[0]["arm_config"]["execution"]
    co0 = arms[0]["arm_config"]["cost_treatment"]
    for arm in arms[1:]:
        assert arm["arm_config"]["execution"] == ex0
        assert arm["arm_config"]["cost_treatment"] == co0
    assert co0["primary_tier"] == 2.0
    assert "ONCE per fill" in co0["charge_law"]
    assert "Q-16" in co0["q16_drag"]


# ----------------------------------------------------------------------- #
# 4. R1-R6 stage-A law
# ----------------------------------------------------------------------- #

def test_stage_a_rule_order_frozen(freeze):
    rules = freeze["section3_stage_a_rules_r1_r6"]["stage_a_rule_order_frozen"]
    assert len(rules) == 7
    prefixes = ("R1 EXPECTANCY", "R2 CONTROL_KILL", "R3 FOLDS", "R4 PF",
                "R5 STRESS", "R6 NON_CONCENTRATION", "survivor :=")
    for rule, prefix in zip(rules, prefixes):
        assert rule.startswith(prefix), (rule, prefix)
    assert "tier 2.0 PRIMARY" in rules[0]
    assert "0.5x" in rules[1] and "falsification rule" in rules[1]
    assert ">= 2/3" in rules[2]
    assert "1.10" in rules[3]
    assert "stress tier 2.0" in rules[4]
    assert "50%" in rules[5]
    assert "PROVISIONAL_STAGE_A_SURVIVOR" in rules[6]
    assert "S1 stays SEALED" in rules[6]
    assert "no rescue" in rules[6]


def test_stage_a_law_sources_cited(freeze):
    s3 = freeze["section3_stage_a_rules_r1_r6"]
    srcs = s3["law_sources"]
    roles = [s.get("role", "") for s in srcs]
    assert any("PLAN_crypto_ng1.md" in s["path"] for s in srcs)
    assert any("section 7" in r for r in roles)
    forex = [s for s in srcs if "forex_ng1_run/selection_freeze.json"
             in s["path"]]
    assert len(forex) == 1
    assert forex[0]["git_commit"] == \
        "d0992d17df8e2dfde57c9a0806a5798f14021a4f"
    assert "PRECEDENT" in forex[0]["role"]
    assert "adapted faithfully" in s3["adaptation_note"]


def test_forex_precedent_blob_hash_via_git(freeze):
    srcs = freeze["section3_stage_a_rules_r1_r6"]["law_sources"]
    forex = next(s for s in srcs if s.get("git_source"))
    assert sha256_git_blob(ROOT_CHECKOUT, forex["git_commit"],
                           forex["path"]) == forex["sha256"]


def test_folds_span_measured_counted_window(freeze, p2):
    s3 = freeze["section3_stage_a_rules_r1_r6"]
    folds = s3["folds_frozen"]
    assert len(folds) == 3
    firsts, lasts = set(), set()
    for pair in p2["per_pair_census"].values():
        fe = pair["floor_evaluation"]
        firsts.add(fe["counted_first_release"])
        lasts.add(fe["counted_last_release"])
    assert len(firsts) == 1 and len(lasts) == 1
    assert folds[0]["release_date_start"] == firsts.pop()
    assert folds[-1]["release_date_end"] == lasts.pop()
    # contiguous, strictly ordered, all within the counted window
    assert folds[0]["release_date_end"] < folds[1]["release_date_start"]
    assert folds[1]["release_date_end"] < folds[2]["release_date_start"]
    assert all(f["release_date_start"] >= folds[0]["release_date_start"]
               for f in folds)
    assert "never re-cut after outcomes" in \
        folds[0]["boundary_law"]


# ----------------------------------------------------------------------- #
# 5. cost contract binding
# ----------------------------------------------------------------------- #

def test_cost_contract_sha_and_tiers(freeze):
    s4 = freeze["section4_cost_contract_binding"]
    contract_path = WORKTREE / s4["cost_contract"]["path"]
    assert sha256_path(contract_path) == s4["cost_contract"]["sha256"]
    contract = json.loads(contract_path.read_text())
    assert s4["primary_tier"] == contract["primary_tier"] == 2.0
    assert s4["tier_ladder"] == contract["tier_ladder"] == [1.0, 1.5, 2.0]
    assert "ONCE per fill" in s4["charge_law"]
    assert "Q-16" in json.dumps(s4["q16_drag_binding"])
    # tracking proxy: measured where available AND fail-closed otherwise
    q16 = s4["q16_drag_binding"]
    assert "MEASURED_SAME_UNDERLYING_PAIRS" in \
        q16["tracking_proxy_where_available"]
    assert "NOT_MEASURED_NO_SAME_UNDERLYING_PAIR" in \
        q16["tracking_proxy_fail_closed"]


def test_transaction_only_legs_stay_excluded(freeze, p2, d1_selected):
    s4 = freeze["section4_cost_contract_binding"]
    s2 = freeze["section2_arm_plan"]
    p2_legs = p2["items"]["item3_cost_ceilings"][
        "values"]["expense_not_measured_legs_fail_closed"]
    d1_decl = d1_selected["feasibility_citation"][
        "d1_bookable_set_declaration"]
    excluded = s4["excluded_transaction_only_legs"]
    assert excluded["legs"] == p2_legs == [
        "BAR", "CPER", "PALL", "PPLT", "SGOL", "SIVR", "UNG", "USL", "USO"]
    assert len(excluded["legs"]) == 9
    assert excluded["excluded_pairs"] == d1_decl["excluded_pairs"]
    assert excluded["bookable_pairs"] == d1_decl["bookable_pairs"]
    # the SAME exclusion binds inside every arm config
    for arm in freeze["section2_arm_plan"]["arms"]:
        cfg = arm["arm_config"]
        assert cfg["excluded_transaction_only_legs"] == p2_legs
        assert cfg["bookable_pairs"] == d1_decl["bookable_pairs"]
    assert s2["bookable_set"]["pairs"] == d1_decl["bookable_pairs"]
    assert s2["bookable_set"]["bookable_pair_count"] == \
        d1_decl["bookable_pair_count"] == 11


def test_cost_ceilings_equal_d1_cited_values(freeze, d1_selected):
    s4 = freeze["section4_cost_contract_binding"]
    d1_ceilings = {e["leg"]: e["worst_case_round_trip_ceiling_bps"]
                   for e in d1_selected["feasibility_citation"]
                   ["cost_ceilings_cited"]["per_leg_worst_case_round_trip_ceiling_bps"]}
    freeze_ceilings = {e["leg"]: e["worst_case_round_trip_ceiling_bps"]
                       for e in s4["cost_ceilings_documentation_only"]
                       ["per_leg_worst_case_round_trip_ceiling_bps"]}
    assert freeze_ceilings == d1_ceilings
    assert "no PnL" in s4["cost_ceilings_documentation_only"]["convention"]


# ----------------------------------------------------------------------- #
# 6. ranking basis + I-phase battery binding
# ----------------------------------------------------------------------- #

def test_ranking_basis_p15_only(freeze):
    s5 = freeze["section5_ranking_basis"]
    text = json.dumps(s5)
    assert "P-15" in text
    assert "preregistered" in text.lower() or "PREREGISTERED" in text
    assert "ever selects" in text
    assert "kill" in text.lower()
    assert s5["selection_non_empty"] is True
    assert "DEGENERATE" in text  # single eligible family => degenerate rank
    assert "COMMODITIES_NG1_REJECT_ALL" in text


def test_battery_mandatory_killers_bound(freeze, d1_selected):
    s6 = freeze["section6_i_phase_control_battery_binding"]
    mandatory = {c["role"]: c for c in s6["mandatory_controls"]}
    assert set(mandatory) == {"PRICE_ONLY_SHADOW", "RELEASE_CLOCK_SHADOW",
                              "SHIFTED_RELEASE_PLACEBO"}
    for role, control in mandatory.items():
        assert control["kill_semantics"].startswith("DESIGNATED KILLER"), role
    # price-only shadow carries NO CoT input
    assert "NO CoT input" in mandatory["PRICE_ONLY_SHADOW"]["spec"]
    # placebo k frozen at the D1-declared minimum (>= 4)
    k = mandatory["SHIFTED_RELEASE_PLACEBO"]["stale_releases_k"]
    assert k == 4 and k >= 4
    assert ">= 4 releases" in mandatory["SHIFTED_RELEASE_PLACEBO"]["spec"]


def test_falsification_rule_bound_to_d1(freeze, d1_selected):
    s6 = freeze["section6_i_phase_control_battery_binding"]
    d1_rule = d1_selected["falsification_rule"]
    bound = s6["falsification_rule_binding"]
    assert bound["killer_controls"] == d1_rule["killer_controls"] == [
        "PRICE_ONLY_SHADOW", "RELEASE_CLOCK_SHADOW",
        "SHIFTED_RELEASE_PLACEBO"]
    # the statement is the D1 statement with only the phase token advanced
    assert bound["statement"] == d1_rule["statement"].replace(
        "at D2/I", "at I")
    assert bound["declared_at"].startswith("D1")
    assert "never moved after any scored number" in bound["declared_at"]


def test_diagnostic_controls_and_q11_law(freeze, p2):
    s6 = freeze["section6_i_phase_control_battery_binding"]
    diag = {c["role"]: c for c in s6["diagnostic_controls"]}
    assert set(diag) == {"DELAY_PAIR", "CLAIRVOYANT"}
    assert "does not kill alone" in diag["DELAY_PAIR"]["kill_semantics"]
    assert "NEVER selectable" in diag["CLAIRVOYANT"]["kill_semantics"]
    assert "Q-11" in s6["q11_invalid_null_law"]
    assert "NOT_RUN" in s6["q11_invalid_null_law"]
    # the frozen per-arm minimum imports the P2 frozen floor exactly
    s2 = freeze["section2_arm_plan"]
    floor = p2["frozen_floors"]["instants"]["floor"]
    assert s2["per_arm_min_eligible_instants_per_pair"] == floor == 300
    assert s2["per_arm_min_eligible_instants_pooled"] == floor * 11


def test_battery_binding_law(freeze):
    s6 = freeze["section6_i_phase_control_battery_binding"]
    assert s6["binding"].startswith("the I phase MUST implement and run")
    assert "fails the I gate" in s6["binding"]


# ----------------------------------------------------------------------- #
# 7. citation re-verification (every cited sha256 vs disk / git)
# ----------------------------------------------------------------------- #

def test_all_citations_verify_against_disk_or_git(freeze):
    citations = all_citations(freeze)
    # the freeze must actually carry citations (not vacuously pass)
    assert len(citations) >= 20
    for location, entry in citations:
        sha = entry["sha256"]
        assert re.fullmatch(r"[0-9a-f]{64}", sha), location
        if entry.get("git_source"):
            got = sha256_git_blob(ROOT_CHECKOUT, entry["git_commit"],
                                  entry["path"])
        elif entry.get("root_checkout"):
            path = Path(entry["path"])
            assert path.is_absolute(), location
            assert path.exists(), location
            got = sha256_path(path)
        else:
            path = WORKTREE / entry["path"]
            assert path.exists(), location
            got = sha256_path(path)
        assert got == sha, location


def test_core_citations_present(freeze):
    s1 = freeze["section1_selected_family_and_vetoes"]
    cites = s1["citations"]
    assert cites["d1_proposal_COMMNG1-A4-P2"]["sha256"] == \
        "f7fac936b29439680a981b4a8bc99f0c2070fac7108ec157e7e7c846eb1b18b9"
    assert cites["d2_novelty_panel"]["sha256"] == \
        "991905eb886af91607a6a7f80f632c788c73aa6fb006c045c83088f5cc8e9969"
    for pid in ALL_IDS:
        assert f"d1_proposal_{pid}" in cites, pid
    for required in ("d2_feasibility_renote", "p2_gate", "p1_cost_contract",
                     "p0_market_pairs", "plan_commodities_ng1",
                     "plan_crypto_ng1", "plan_forex_ng1"):
        assert required in cites, required


def test_selected_d2_panel_records_the_freeze_proposal_hash(panel, freeze):
    """The D2 panel's own input pins must agree with the freeze's citation
    of the selected proposal (no drift between lanes)."""
    cite = (freeze["section1_selected_family_and_vetoes"]
            ["citations"]["d1_proposal_COMMNG1-A4-P2"]["sha256"])
    assert panel["inputs"]["proposal_sha256"][SELECTED_ID] == cite


def test_feasibility_identity_with_p2_census(freeze, p2):
    s1 = freeze["section1_selected_family_and_vetoes"]["selected_family"]
    # the freeze quotes one pooled coverage value: verify it against the
    # per-pair census (all 20 pairs identical)
    coverages = {pair["floor_evaluation"]["release_to_session_coverage"]
                 for pair in p2["per_pair_census"].values()}
    grid = {pair["floor_evaluation"]["grid_eligible_instants"]
            for pair in p2["per_pair_census"].values()}
    assert coverages == {0.997512}
    assert grid == {401}
    assert "401" in s1["feasibility"]
    assert "0.997512" in s1["feasibility"]


# ----------------------------------------------------------------------- #
# 8. negative scan: NO outcome numbers anywhere in the freeze
# ----------------------------------------------------------------------- #

def test_no_banned_outcome_keys(freeze):
    hits = banned_key_paths(freeze)
    assert hits == [], hits


def test_every_numeric_leaf_whitelisted(freeze):
    bad = non_whitelisted_numeric_keys(freeze)
    assert bad == [], bad


def test_no_outcome_key_shapes_in_raw_text(freeze):
    raw = FREEZE_PATH.read_text()
    pattern = (r'"[^"]*(?:pnl|profit_factor|sharpe|drawdown|win_rate|'
               r'hit_rate|expectancy|total_return|net_return|payoff)'
               r'[^"]*"\s*:')
    assert re.search(pattern, raw, re.IGNORECASE) is None


def test_no_floats_beyond_documented_precision(freeze):
    """The D2 evidence numbers are recorded at the panel's own precision;
    the freeze must not introduce long computed-decimal numbers (the
    shape of measured outcomes) anywhere.  The ONLY over-precision
    literals permitted are frozen P1 cost-contract constants (e.g. the
    tracking-proxy divergences), verified by membership against the
    cited contract file itself."""
    raw = FREEZE_PATH.read_text()
    contract_raw = (WORKTREE / freeze["section4_cost_contract_binding"]
                    ["cost_contract"]["path"]).read_text()
    contract_numbers = set(re.findall(r"-?\d+\.\d+", contract_raw))
    for match in re.finditer(r"(?<![\w.])-?\d+\.\d{13,}", raw):
        literal = match.group(0)
        assert literal in contract_numbers, \
            f"over-precision numeric literal not a contract constant: " \
            f"{literal}"


def test_rho_family_numbers_confined_to_selection_evidence(freeze):
    """Every numeric leaf carrying a |rho|-family value must live in the
    D2-selection-evidence fields of section 1 - nowhere else."""
    s1 = freeze["section1_selected_family_and_vetoes"]
    allowed_substrings = ("per_shadow_pooled_abs_rho", "pooled_abs_rho",
                          "margin_to_ceiling", "novelty_ceiling_abs_rho")

    def walk(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                child = f"{path}.{k}" if path else k
                if k in ("pooled_abs_rho", "margin_to_ceiling",
                         "novelty_ceiling_abs_rho",
                         "per_shadow_pooled_abs_rho") or \
                        k in ("momentum_63s", "generic_dow_tue",
                              "v16_close_displace_fade",
                              "price_only_shadow"):
                    # numeric leaves under these keys must be inside s1
                    for _key, _val in numeric_leaves(v):
                        assert child.startswith(
                            "section1_selected_family_and_vetoes"), child
                walk(v, child)
        elif isinstance(obj, list):
            for v in obj:
                walk(v, path)
    walk(freeze)
    # and section 1 must actually hold the selected family's evidence
    assert s1["selected_family"]["pooled_abs_rho"] == 0.109559271631
