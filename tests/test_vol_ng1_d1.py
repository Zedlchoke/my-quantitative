"""VOL-NG1 D1 tests (task vol-ng1-d1-proposals).

Outcome-blind proposal artifact checks, per the dispatch packet:

1. Committed-artifact integrity: the sha256 digests cited inside every
   proposal (p0/p1/p2 gates, cost contract, corp_actions.py,
   plane_adapter.py, plane-consumed series digests) are recomputed from
   the files at HEAD and refused on any drift;
2. Frozen template fields on all four proposals (proposal_id/lane/title,
   mechanism with FORCED and LATE participant, decision_rule_family with
   symbolic parameters, representation_identity (P-12) with V7 close+1
   and plane+event-adjusted series law, ancestry_risk_statement naming
   every kill-candidate shadow, control_battery_spec with the MANDATORY
   index-only shadow + cost-path control plus calendar-clock shadow and
   placebo, feasibility_citation to the P2 floors, falsification_rule
   with one concrete kill);
3. A5 law: BOTH A5 proposals carry the implied-complex realized-vol
   structural limitation VERBATIM (exact string equality against
   p2_gate.json) and the A4 proposals do NOT claim it;
4. Negative scan (blindness law): no outcome-ish key anywhere, every
   numeric leaf confined to the citation blocks AND present verbatim as
   a number inside the committed P0/P1/P2 artifacts, no long numeric
   arrays;
5. Synthetic fixtures: the same validator accepts a minimal valid
   synthetic proposal and REFUSES corrupted variants (missing mandatory
   control, outcome key, non-committed number, numeric leaf outside the
   citation blocks, wrong A5 limitation string);
6. d1_gate.json: schema, four COMPLETE verdicts, clean negative scan,
   proposal digests equal the files on disk.

No network, no measurement, no signal arithmetic: the tests inspect
artifact STRUCTURE only.  Every number asserted here is either a
committed structural fact re-read from a gate file or a count of
violations (expected 0).
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

REPO_ROOT = Path(__file__).resolve().parents[1]
D1_DIR = REPO_ROOT / "research/control/vol_ng1_run/d1"
PROPOSALS_DIR = D1_DIR / "proposals"
GATE_PATH = D1_DIR / "d1_gate.json"
P0_GATE_PATH = REPO_ROOT / "research/control/vol_ng1_run/p0_gate.json"
P1_GATE_PATH = REPO_ROOT / "research/control/vol_ng1_run/p1_gate.json"
CONTRACT_PATH = REPO_ROOT / "research/control/vol_ng1_run/p1_cost_contract.json"
P2_GATE_PATH = REPO_ROOT / "research/control/vol_ng1_run/p2_gate.json"
CORP_ACTIONS_PATH = REPO_ROOT / "research/assets/vol_ng1/corp_actions.py"
PLANE_ADAPTER_PATH = REPO_ROOT / "research/assets/vol_ng1/plane_adapter.py"

EXPECTED_IDS = [
    "VOLNG1-A4-P1",
    "VOLNG1-A4-P2",
    "VOLNG1-A5-P1",
    "VOLNG1-A5-P2",
]
EXPECTED_LANES = {
    "VOLNG1-A4-P1": "A4_term_structure_slope",
    "VOLNG1-A4-P2": "A4_term_structure_slope",
    "VOLNG1-A5-P1": "A5_risk_premium_state",
    "VOLNG1-A5-P2": "A5_risk_premium_state",
}
TEMPLATE_FIELDS = [
    "schema",
    "cycle_id",
    "proposal_id",
    "lane",
    "title",
    "blindness_declaration",
    "mechanism",
    "decision_rule_family",
    "representation_identity",
    "ancestry_risk_statement",
    "control_battery_spec",
    "feasibility_citation",
    "falsification_rule",
    "committed_citations",
]
KILL_SHADOWS = [
    "v16_close_displace_fade",
    "v17_oi_level",
    "dvol_shock",
    "momentum_63s",
    "generic_dow_tue",
]
#: Root blocks under which numeric leaves are ALLOWED (structural-fact
#: citation blocks only).
NUMERIC_BLOCK_ROOTS = {
    "representation_identity",
    "feasibility_citation",
    "committed_citations",
}
#: Outcome pattern for KEY NAMES (values are covered by the numeric-leaf
#: law; narrative strings never carry keys).
FORBIDDEN_KEY_RE = re.compile(
    r"(expectanc|pnl|sharpe|sortino|calmar|hit_rate|win_rate|drawdown|"
    r"profit|cumulative_return|returns|outcome_number)",
    re.IGNORECASE,
)
MAX_NUMERIC_ARRAY_LEN = 8


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _collect_numbers(doc) -> set:
    """Every int/float leaf (bools excluded) anywhere in a document."""
    out: set = set()
    if isinstance(doc, bool):
        return out
    if isinstance(doc, (int, float)):
        out.add(doc)
    elif isinstance(doc, dict):
        for v in doc.values():
            out |= _collect_numbers(v)
    elif isinstance(doc, list):
        for v in doc:
            out |= _collect_numbers(v)
    return out


def _walk(doc, path: str = ""):
    """Yield (path, key, value) for every leaf/container key."""
    if isinstance(doc, dict):
        for k, v in doc.items():
            yield f"{path}.{k}" if path else k, k, v
            yield from _walk(v, f"{path}.{k}" if path else k)
    elif isinstance(doc, list):
        for i, v in enumerate(doc):
            yield from _walk(v, f"{path}[{i}]")


def committed_numbers() -> set:
    """Numbers legally citable: any number inside the committed
    P0/P1/P2 artifacts (gates + frozen cost contract)."""
    out: set = set()
    for p in (P0_GATE_PATH, P1_GATE_PATH, CONTRACT_PATH, P2_GATE_PATH):
        out |= _collect_numbers(_load(p))
    return out


def validate_proposal(prop: dict, committed: set, p2: dict) -> None:
    """Fail-closed validator: template completeness + blindness law.

    Raises ValueError with every violation found (never silently
    truncates to the first).
    """
    errors: list[str] = []

    # -- template completeness -------------------------------------
    for field in TEMPLATE_FIELDS:
        if field not in prop:
            errors.append(f"missing template field: {field}")
    if errors:
        raise ValueError("; ".join(errors))

    if prop["schema"] != "vol_ng1_run/d1_proposal@1":
        errors.append("schema must be vol_ng1_run/d1_proposal@1")
    if prop["cycle_id"] != "VOL-NG1":
        errors.append("cycle_id must be VOL-NG1")

    # mechanism must name the forced and late participant explicitly
    mech = prop["mechanism"]
    for key in ("narrative", "forced_participant", "late_participant",
                "claim_declared_blind", "economic_magnitude_honesty"):
        if key not in mech or not isinstance(mech[key], str) or not mech[key]:
            errors.append(f"mechanism.{key} missing/empty")

    # decision rule family: parameters stay symbolic until D2/S
    drf = prop["decision_rule_family"]
    for key in ("family_id", "state_definition_symbolic",
                "action_map_symbolic", "parameters", "parameter_law"):
        if key not in drf:
            errors.append(f"decision_rule_family.{key} missing")
    if "symbolic" not in drf.get("parameter_law", "").lower():
        errors.append("decision_rule_family.parameter_law must declare "
                      "parameters symbolic until D2/S")
    if not all(isinstance(p, str) for p in drf.get("parameters", [])):
        errors.append("decision_rule_family.parameters must be symbolic "
                      "strings (no numeric thresholds at D1)")

    # ancestry: every kill-candidate shadow named
    anc = prop["ancestry_risk_statement"]
    shadows = anc.get("kill_candidate_shadows", [])
    for s in KILL_SHADOWS:
        if s not in shadows:
            errors.append(f"ancestry_risk_statement missing shadow {s}")
    if "d2_test_of_claim" not in anc:
        errors.append("ancestry_risk_statement.d2_test_of_claim missing")

    # control battery: both mandatory controls + calendar + placebo
    battery = prop["control_battery_spec"]
    for ctrl in ("index_only_shadow", "cost_path_control",
                 "calendar_clock_shadow", "placebo"):
        if ctrl not in battery:
            errors.append(f"control_battery_spec.{ctrl} missing")
    if not battery.get("index_only_shadow", {}).get("mandatory", False):
        errors.append("index_only_shadow must be MANDATORY")
    if not battery.get("cost_path_control", {}).get("mandatory", False):
        errors.append("cost_path_control must be MANDATORY")
    if "q-16" not in battery.get("cost_path_control", {}).get(
            "spec", "").lower():
        errors.append("cost_path_control must carry the Q-16 path "
                      "component explicitly")

    # feasibility citation must cite the p2 gate by sha256
    feas = prop["feasibility_citation"]
    if "p2_gate_json_sha256" not in feas:
        errors.append("feasibility_citation must cite p2_gate sha256")

    # falsification rule: one preregistered concrete kill
    fr = prop["falsification_rule"].get("rule", "")
    if "KILL" not in fr:
        errors.append("falsification_rule must contain a concrete KILL "
                      "condition")

    # A5 law: verbatim limitation, exact equality; A4 must NOT claim it
    limitation = p2["sections"]["a5_risk_premium"]["structural_limitation"]
    if prop["lane"] == "A5_risk_premium_state":
        got = prop.get("structural_limitation_p2_gate_c8_verbatim")
        if got != limitation:
            errors.append("A5 structural limitation must be carried "
                          "VERBATIM from p2_gate.json (exact equality)")
    else:
        if "structural_limitation_p2_gate_c8_verbatim" in prop:
            errors.append("A4 proposal must not claim the A5 structural "
                          "limitation")

    # -- blindness law: negative scan ------------------------------
    for path, key, _value in _walk(prop):
        if isinstance(key, str) and FORBIDDEN_KEY_RE.search(key):
            errors.append(f"forbidden outcome-ish key: {path}")

    for path, key, value in _walk(prop):
        root = path.split(".", 1)[0].split("[", 1)[0]
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            if root not in NUMERIC_BLOCK_ROOTS:
                errors.append(
                    f"numeric leaf outside citation blocks: {path}={value!r}")
            elif value not in committed:
                errors.append(
                    f"non-committed numeric leaf: {path}={value!r}")
        if isinstance(value, list):
            nums = [v for v in value
                    if isinstance(v, (int, float))
                    and not isinstance(v, bool)]
            if len(nums) > MAX_NUMERIC_ARRAY_LEN:
                errors.append(f"numeric array too long: {path}")

    if errors:
        raise ValueError("; ".join(errors))


@pytest.fixture(scope="module")
def p2_gate() -> dict:
    return _load(P2_GATE_PATH)


@pytest.fixture(scope="module")
def committed() -> set:
    return committed_numbers()


@pytest.fixture(scope="module")
def proposals() -> dict:
    out = {}
    for pid in EXPECTED_IDS:
        path = PROPOSALS_DIR / f"{pid}.json"
        assert path.exists(), f"missing proposal: {path}"
        out[pid] = _load(path)
    return out


# ---------------------------------------------------------------------
# 1. committed-artifact integrity (digest drift refused)
# ---------------------------------------------------------------------

def test_artifact_digests_cited_match_files_at_head(proposals):
    for pid, prop in proposals.items():
        cited = prop["committed_citations"]
        pairs = {
            "p0_gate_json_sha256": P0_GATE_PATH,
            "p1_gate_json_sha256": P1_GATE_PATH,
            "p1_cost_contract_json_sha256": CONTRACT_PATH,
            "p2_gate_json_sha256": P2_GATE_PATH,
            "corp_actions_py_sha256": CORP_ACTIONS_PATH,
            "plane_adapter_py_sha256": PLANE_ADAPTER_PATH,
        }
        for field, path in pairs.items():
            assert cited[field] == _sha256(path), (
                f"{pid}: digest drift on {field}")


def test_series_digests_equal_plane_consumed_constants(proposals, p2_gate):
    consumed = p2_gate["consumed_via_plane"]
    for pid, prop in proposals.items():
        digests = prop["committed_citations"]["series_digests_consumed_via_plane"]
        assert set(digests) == set(consumed["etp_digests"]) | set(
            consumed["index_digests"]), f"{pid}: series digest set drift"
        for series, digest in digests.items():
            pool = {**consumed["etp_digests"], **consumed["index_digests"]}
            assert digest == pool[series], (
                f"{pid}: series {series} digest != plane-consumed constant")


def test_feasibility_numbers_equal_p2_gate_values(proposals, p2_gate):
    a4 = p2_gate["sections"]["a4_term_structure_slope"]
    a5 = p2_gate["sections"]["a5_risk_premium"]
    ceilings = {leg: spec["round_trip_cost_ceiling_bps"]
                for leg, spec in
                p2_gate["sections"]["cost_ceilings"]["legs"].items()}
    for pid, prop in proposals.items():
        feas = prop["feasibility_citation"]
        assert feas["p2_gate_json_sha256"] == _sha256(P2_GATE_PATH)
        assert feas["worst_case_round_trip_cost_ceiling_bps_by_leg"] == \
            ceilings, f"{pid}: ceiling values must equal the P2 gate"
        if prop["lane"] == "A4_term_structure_slope":
            assert feas["lane_verdict"] == "PASS"
            assert feas["measured_bookable_instants"] == \
                a4["bookable_instants"]
            assert feas["frozen_floor_min_bookable_instants"] == \
                a4["frozen_floors"]["min_bookable_instants"]
            assert feas["measured_coverage_primary"] == \
                a4["coverage_primary"]
            assert feas["frozen_floor_min_coverage"] == \
                a4["frozen_floors"]["min_coverage"]
        else:
            assert feas["lane_verdict"] == "FEASIBLE"
            assert feas["measured_bookable_computable_instants"] == \
                a5["bookable_instants_state_computable"]
            assert feas["frozen_floor_min_bookable_computable_instants"] == \
                a5["frozen_floor"]["min_bookable_computable_instants"]


def test_representation_grid_numbers_equal_p2_gate(proposals, p2_gate):
    a4 = p2_gate["sections"]["a4_term_structure_slope"]
    evl = p2_gate["sections"]["event_adjusted_layer"]
    for pid, prop in proposals.items():
        grid = prop["representation_identity"]["common_grid"]
        assert grid["grid_sessions_total"] == a4["grid_sessions_total"]
        assert grid["warmup_carveout_sessions"] == \
            a4["warmup_carveout_sessions"]
        assert grid["first_bookable_instant"] == a4["first_bookable_instant"]
        assert grid["last_bookable_instant"] == a4["last_bookable_instant"]
        assert grid["v7_tail_refused_sessions"] == \
            a4["v7_tail_refused_sessions"]
        assert grid["bookable_instants"] == a4["bookable_instants"]
        assert grid["coverage_primary"] == a4["coverage_primary"]
        assert grid["coverage_primary_denominator"] == \
            a4["coverage_primary_denominator"]
        series_law = prop["representation_identity"]["series_law"]
        assert "never raw" in series_law["etp_legs"]
        assert "corp_actions.event_adjusted_closes" in series_law["etp_legs"]
        # residual number cited in the event-layer narrative equals the gate
        assert str(evl["max_abs_mechanical_residual"]) in \
            series_law["event_layer_citation"]


# ---------------------------------------------------------------------
# 2. frozen template fields on all four proposals
# ---------------------------------------------------------------------

def test_all_four_proposals_present_and_complete(proposals, committed,
                                                 p2_gate):
    assert set(proposals) == set(EXPECTED_IDS)
    for pid, prop in proposals.items():
        validate_proposal(prop, committed, p2_gate)


def test_ids_and_lanes_match_plan(proposals):
    for pid, prop in proposals.items():
        assert prop["proposal_id"] == pid
        assert prop["lane"] == EXPECTED_LANES[pid]
    lanes = {p["lane"] for p in proposals.values()}
    assert lanes == {"A4_term_structure_slope", "A5_risk_premium_state"}
    for lane in lanes:
        assert sum(1 for p in proposals.values() if p["lane"] == lane) == 2


def test_mechanism_names_forced_and_late_participant(proposals):
    for pid, prop in proposals.items():
        mech = prop["mechanism"]
        assert "forced_participant" in mech and mech["forced_participant"]
        assert "late_participant" in mech and mech["late_participant"]


def test_decision_rule_parameters_symbolic_until_d2_s(proposals):
    for pid, prop in proposals.items():
        drf = prop["decision_rule_family"]
        assert "symbolic" in drf["parameter_law"].lower()
        assert "D2/S" in drf["parameter_law"] or "d2/s" in \
            drf["parameter_law"].lower()
        for p in drf["parameters"]:
            assert isinstance(p, str), f"{pid}: numeric threshold at D1"


def test_representation_identity_law_complete(proposals, p2_gate):
    clocks = _load(P1_GATE_PATH)["sections"]["clocks"]
    for pid, prop in proposals.items():
        ri = prop["representation_identity"]
        law = ri["decision_instant_law"]["law"]
        assert "V7" in law and "close+1" in law.replace(" ", "")
        assert "refused" in law
        assert "16:00 America/New_York" in \
            ri["decision_instant_law"]["clock"]
        assert clocks["dst_report"]["all_match"] is True
        pairs = clocks["close_plus_1_pairs"]
        assert all(p["verdict"] == "MEASURED" for p in pairs)
        assert ri["common_grid"]["v7_tail_refused_sessions"] == \
            ["2026-09-11"]


def test_control_battery_mandatory_controls_every_proposal(proposals):
    for pid, prop in proposals.items():
        battery = prop["control_battery_spec"]
        idx = battery["index_only_shadow"]
        assert idx["mandatory"] is True
        assert "ALONE" in idx["spec"].upper()
        cost = battery["cost_path_control"]
        assert cost["mandatory"] is True
        assert "ladder" in cost["spec"].lower()
        assert "q-16" in cost["spec"].lower()
        assert "calendar_clock_shadow" in battery
        assert "placebo" in battery
        assert "invalid_null_distinction" in battery


def test_ancestry_shadows_all_named_with_differentiation(proposals):
    for pid, prop in proposals.items():
        anc = prop["ancestry_risk_statement"]
        for shadow in KILL_SHADOWS:
            assert shadow in anc["kill_candidate_shadows"]
            reason = anc["why_information_differs"][shadow]
            assert isinstance(reason, str) and len(reason) > 40
        assert "D2" in anc["d2_test_of_claim"]


def test_falsification_rule_single_concrete_kill(proposals):
    for pid, prop in proposals.items():
        rule = prop["falsification_rule"]["rule"]
        assert "KILL" in rule
        assert len(rule) > 120


# ---------------------------------------------------------------------
# 3. A5 law: verbatim structural limitation
# ---------------------------------------------------------------------

def test_a5_limitation_verbatim_a4_does_not_claim(p2_gate):
    limitation = p2_gate["sections"]["a5_risk_premium"]["structural_limitation"]
    for pid in ("VOLNG1-A5-P1", "VOLNG1-A5-P2"):
        prop = _load(PROPOSALS_DIR / f"{pid}.json")
        assert prop["lane"] == "A5_risk_premium_state"
        assert prop["structural_limitation_p2_gate_c8_verbatim"] == \
            limitation, f"{pid}: limitation must be VERBATIM"
        assert prop["structural_limitation_consequence"]
    for pid in ("VOLNG1-A4-P1", "VOLNG1-A4-P2"):
        prop = _load(PROPOSALS_DIR / f"{pid}.json")
        assert "structural_limitation_p2_gate_c8_verbatim" not in prop


def test_a5_state_inputs_bound_to_p2_declaration(proposals, p2_gate):
    a5 = p2_gate["sections"]["a5_risk_premium"]
    for pid in ("VOLNG1-A5-P1", "VOLNG1-A5-P2"):
        state = proposals[pid]["representation_identity"]["state_input_law"]
        assert "event-adjusted vxx close" in \
            state["realized_side_short_bucket"].lower()
        assert "never raw" in state["realized_side_short_bucket"].lower()
        assert a5["implied_series"].startswith("S7:cboe-vol-index-histories")
        assert "GRANTED" in state["all_inputs_granted"]
        assert "computability census only" in state["computability"]
        # proxy lookback cited in words inside a string, number only in gates
        assert "twenty-one" in state["realized_side_short_bucket"]


# ---------------------------------------------------------------------
# 4. negative scan over the committed proposals
# ---------------------------------------------------------------------

def _scan(prop: dict, committed: set) -> list[str]:
    errors: list[str] = []
    for path, key, _value in _walk(prop):
        if isinstance(key, str) and FORBIDDEN_KEY_RE.search(key):
            errors.append(f"outcome-ish key: {path}")
    for path, _key, value in _walk(prop):
        root = path.split(".", 1)[0].split("[", 1)[0]
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            if root not in NUMERIC_BLOCK_ROOTS:
                errors.append(f"numeric outside blocks: {path}={value!r}")
            elif value not in committed:
                errors.append(f"non-committed number: {path}={value!r}")
        if isinstance(value, list):
            nums = [v for v in value if isinstance(v, (int, float))
                    and not isinstance(v, bool)]
            if len(nums) > MAX_NUMERIC_ARRAY_LEN:
                errors.append(f"numeric array too long: {path}")
    return errors


def test_negative_scan_no_outcome_numbers_in_any_proposal(proposals,
                                                          committed):
    violations = {}
    for pid, prop in proposals.items():
        found = _scan(prop, committed)
        if found:
            violations[pid] = found
    assert not violations, f"blindness-law violations: {violations}"


def test_negative_scan_is_not_vacuous():
    """The committed-fact membership law must actually bite: the gates
    must NOT contain arbitrary probe numbers, and the proposal set must
    contain at least one numeric leaf per allowed block."""
    committed = committed_numbers()
    for probe in (0.5, 1.234, 42, 999999, -0.25):
        assert probe not in committed
    for pid in EXPECTED_IDS:
        prop = _load(PROPOSALS_DIR / f"{pid}.json")
        for root in ("representation_identity", "feasibility_citation"):
            leaves = [
                v for path, _k, v in _walk(prop[root])
                if isinstance(v, (int, float)) and not isinstance(v, bool)
            ]
            assert leaves, f"{pid}: no numeric leaves under {root}"
        digests = [
            v for _p, _k, v in _walk(prop["committed_citations"])
            if isinstance(v, str) and re.fullmatch(r"[0-9a-f]{64}", v)
        ]
        assert digests, f"{pid}: no sha256 digests under committed_citations"


# ---------------------------------------------------------------------
# 5. synthetic fixtures: validator accepts valid, refuses corrupted
# ---------------------------------------------------------------------

def _minimal_proposal(p2_gate: dict) -> dict:
    limitation = p2_gate["sections"]["a5_risk_premium"]["structural_limitation"]
    return {
        "schema": "vol_ng1_run/d1_proposal@1",
        "cycle_id": "VOL-NG1",
        "proposal_id": "SYNTH-P1",
        "lane": "A5_risk_premium_state",
        "title": "synthetic fixture",
        "blindness_declaration": {"law": "outcome-blind", "no_measurement_performed": True},
        "mechanism": {
            "narrative": "n",
            "forced_participant": "f",
            "late_participant": "l",
            "claim_declared_blind": "c",
            "economic_magnitude_honesty": "e",
        },
        "decision_rule_family": {
            "family_id": "synth",
            "state_definition_symbolic": "s",
            "action_map_symbolic": "a",
            "parameters": ["theta"],
            "parameter_law": "ALL parameters symbolic until D2/S",
        },
        "representation_identity": {
            "common_grid": {"bookable_instants": 1914},
            "series_law": {
                "etp_legs": "consumed ONLY through "
                            "corp_actions.event_adjusted_closes -- never raw",
                "event_layer_citation": "residual 1.1121916654310837e-07",
            },
            "decision_instant_law": {
                "law": "V7 close+1; refused tail",
                "clock": "16:00 America/New_York",
            },
        },
        "ancestry_risk_statement": {
            "kill_candidate_shadows": list(KILL_SHADOWS),
            "why_information_differs": {s: "x" * 50 for s in KILL_SHADOWS},
            "d2_test_of_claim": "D2 pooled ancestry margin",
        },
        "control_battery_spec": {
            "index_only_shadow": {"mandatory": True,
                                  "spec": "index series ALONE"},
            "cost_path_control": {"mandatory": True,
                                  "spec": "survive the measured path-cost "
                                          "ladder with the Q-16 component"},
            "calendar_clock_shadow": {"spec": "s"},
            "placebo": {"spec": "s"},
            "invalid_null_distinction": "INVALID refused, never NULL",
        },
        "feasibility_citation": {
            "p2_gate_json_sha256": "0" * 64,
            "frozen_floor_min_coverage": 0.9,
        },
        "falsification_rule": {"rule": "KILL if after-cost expectancy <= 0 "
                                       "at primary tier on the P2 grid "
                                       "after the full ladder, period."},
        "committed_citations": {},
        "structural_limitation_p2_gate_c8_verbatim": limitation,
    }


def test_synthetic_valid_fixture_passes(p2_gate, committed):
    validate_proposal(_minimal_proposal(p2_gate), committed, p2_gate)


def test_synthetic_missing_mandatory_control_refused(p2_gate, committed):
    prop = _minimal_proposal(p2_gate)
    del prop["control_battery_spec"]["index_only_shadow"]
    with pytest.raises(ValueError, match="index_only_shadow"):
        validate_proposal(prop, committed, p2_gate)


def test_synthetic_outcome_key_refused(p2_gate, committed):
    prop = _minimal_proposal(p2_gate)
    prop["expectancy_by_state"] = "something"
    with pytest.raises(ValueError, match="outcome-ish key"):
        validate_proposal(prop, committed, p2_gate)


def test_synthetic_non_committed_number_refused(p2_gate, committed):
    prop = _minimal_proposal(p2_gate)
    prop["representation_identity"]["novel"] = 123.456
    with pytest.raises(ValueError, match="non-committed numeric leaf"):
        validate_proposal(prop, committed, p2_gate)


def test_synthetic_number_outside_citation_blocks_refused(p2_gate, committed):
    prop = _minimal_proposal(p2_gate)
    prop["mechanism"]["sneaky_number"] = 1914  # committed value, wrong place
    with pytest.raises(ValueError, match="outside citation blocks"):
        validate_proposal(prop, committed, p2_gate)


def test_synthetic_wrong_a5_limitation_refused(p2_gate, committed):
    prop = _minimal_proposal(p2_gate)
    prop["structural_limitation_p2_gate_c8_verbatim"] = \
        prop["structural_limitation_p2_gate_c8_verbatim"].replace(
            "implied-complex", "spot")
    with pytest.raises(ValueError, match="VERBATIM"):
        validate_proposal(prop, committed, p2_gate)


def test_synthetic_missing_forced_participant_refused(p2_gate, committed):
    prop = _minimal_proposal(p2_gate)
    del prop["mechanism"]["forced_participant"]
    with pytest.raises(ValueError, match="forced_participant"):
        validate_proposal(prop, committed, p2_gate)


# ---------------------------------------------------------------------
# 6. d1_gate.json consistency
# ---------------------------------------------------------------------

def test_d1_gate_schema_and_verdict():
    gate = _load(GATE_PATH)
    assert gate["schema"] == "vol_ng1_run/d1_gate@1"
    assert gate["cycle_id"] == "VOL-NG1"
    assert gate["task_id"] == "vol-ng1-d1-proposals"
    assert gate["verdict"] == "PASS"
    assert gate["tests"]["exit_code"] == 0
    assert gate["tests"]["verdict"] == "PASS"


def test_d1_gate_covers_all_four_proposals_with_digests():
    gate = _load(GATE_PATH)
    entries = {e["proposal_id"]: e for e in gate["proposals"]}
    assert set(entries) == set(EXPECTED_IDS)
    for pid, entry in entries.items():
        assert entry["verdict"] == "COMPLETE"
        assert all(v is True for k, v in entry["template_checks"].items()
                   if not k.startswith("a5_limitation"))
        a5_required = pid.startswith("VOLNG1-A5")
        assert entry["template_checks"]["a5_limitation_verbatim_required"] \
            is a5_required
        if a5_required:
            assert entry["template_checks"]["a5_limitation_verbatim_present"] \
                is True
        assert entry["sha256"] == _sha256(REPO_ROOT / entry["path"])


def test_d1_gate_negative_scan_clean_and_consistent(proposals, committed):
    gate = _load(GATE_PATH)
    scan = gate["negative_scan"]
    assert scan["verdict"] == "PASS"
    assert scan["outcome_keys_found"] == []
    assert scan["numeric_leaves_outside_committed_facts"] == []
    assert scan["long_numeric_arrays_found"] == []
    # gate's recorded scan law must match this file's independent scan
    for pid, prop in proposals.items():
        assert not _scan(prop, committed), f"{pid}: scan disagreement"
