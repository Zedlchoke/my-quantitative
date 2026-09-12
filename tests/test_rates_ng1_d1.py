"""RATES-NG1 D1 tests (dispatch: rates-ng1-d1-proposals).

Outcome-blind PROPOSAL validation for the D1 phase.  The four
proposal files are MECHANISM DECLARATIONS authored before anyone
measures anything; these tests assert that the frozen template
fields are complete, that the blindness negative scan holds (no
outcome metric vocabulary, no numeric leaf outside the frozen
structural allowlist), that the lane control batteries have their
mandatory roles, and that every sha256 pin inside a proposal
matches a re-hash of the named committed artifact.

Hand-built synthetic fixtures cover the validator itself (valid
minimal proposal; one violation per frozen-field class; battery
role gaps; token and numeric-leaf scan catches; pin mismatch).
No network access; no outcome statistic is computed anywhere in
this file or in the artifacts it checks.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import os

import pytest

WORKTREE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
D1_MODULE_PATH = os.path.join(
    WORKTREE, "research", "control", "rates_ng1_run", "d1",
    "d1_validate.py")
PROPOSALS_DIR = os.path.join(
    WORKTREE, "research", "control", "rates_ng1_run", "d1", "proposals")
GATE_PATH = os.path.join(
    WORKTREE, "research", "control", "rates_ng1_run", "d1", "d1_gate.json")

_SPEC = importlib.util.spec_from_file_location("d1_validate", D1_MODULE_PATH)
dv = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(dv)


# --------------------------------------------------------------------- #
# helpers                                                                #
# --------------------------------------------------------------------- #

def _load_committed(pid: str) -> dict:
    with open(os.path.join(PROPOSALS_DIR, f"{pid}.json"),
              encoding="utf-8") as fh:
        return json.load(fh)


def _committed_raw(pid: str) -> str:
    with open(os.path.join(PROPOSALS_DIR, f"{pid}.json"),
              encoding="utf-8") as fh:
        return fh.read()


def _minimal_valid_proposal() -> dict:
    return {
        "schema": dv.SCHEMA_PROPOSAL,
        "cycle_id": dv.CYCLE_ID,
        "task_id": dv.TASK_ID,
        "proposal_id": "RATESNG1-A4-PX",
        "lane": "A4",
        "title": "synthetic fixture proposal",
        "base_sha": dv.BASE_SHA,
        "blindness_declaration": {"status": "OUTCOME_BLIND", "law": "x"},
        "mechanism": {
            "narrative": "synthetic forced-participant story",
            "forced_participant": {"who": "synthetic"},
            "information_source": "calendar only",
            "state_definition_symbolic": "symbolic",
        },
        "decision_rule_family": "event-window position with "
                                "state-conditioned direction",
        "representation_identity": {
            "grid": {"bookable_count": 1918},
            "series": {"rows": [{"leg": "TLT", "rows": 6071}]},
            "event_mapping": {"law": "PIT later-bound"},
            "decision_instant_law": {"law": "V7 close+1"},
        },
        "ancestry_risk_statement": {"named_kill_candidates": []},
        "control_battery_spec": {"arms": [
            {"role": "ANCHOR", "spec": "s"},
            {"role": "DELAY_PAIR", "spec": "s"},
            {"role": "CLAIRVOYANT", "spec": "s"},
            {"role": "CLOCK_ONLY_SHADOW", "spec": "s"},
            {"role": "SHIFTED_CALENDAR_PLACEBO", "spec": "s"},
        ]},
        "feasibility_citation": {
            "floors": {"min_bookable_instants": 1500,
                       "min_grid_eligible_events": 150},
        },
        "falsification_rule": {"statement": "kill if a killer out-earns"},
    }


# --------------------------------------------------------------------- #
# 1. synthetic fixtures: completeness                                    #
# --------------------------------------------------------------------- #

def test_synthetic_minimal_valid_proposal_passes():
    res = dv.validate_proposal_obj(_minimal_valid_proposal())
    assert res["completeness_violations"] == []
    assert res["battery_violations"] == []
    assert res["numeric_leaf_violations"] == []


@pytest.mark.parametrize("key", dv.REQUIRED_KEYS)
def test_synthetic_missing_required_field_is_caught(key):
    obj = _minimal_valid_proposal()
    del obj[key]
    res = dv.validate_proposal_obj(obj)
    assert f"MISSING_FIELD:{key}" in res["completeness_violations"]


@pytest.mark.parametrize("key", dv.REQUIRED_KEYS)
def test_synthetic_empty_required_field_is_caught(key):
    obj = _minimal_valid_proposal()
    obj[key] = {} if isinstance(obj[key], dict) else ""
    res = dv.validate_proposal_obj(obj)
    assert f"EMPTY_FIELD:{key}" in res["completeness_violations"]


def test_synthetic_bad_schema_and_base_sha_are_caught():
    obj = _minimal_valid_proposal()
    obj["schema"] = "rates_ng1_run/d1_proposal@0"
    obj["base_sha"] = "0" * 64
    res = dv.validate_proposal_obj(obj)
    assert any(v.startswith("BAD_SCHEMA")
               for v in res["completeness_violations"])
    assert any(v.startswith("BAD_BASE_SHA")
               for v in res["completeness_violations"])


def test_synthetic_non_blind_declaration_is_caught():
    obj = _minimal_valid_proposal()
    obj["blindness_declaration"] = {"status": "SOMETHING_ELSE"}
    res = dv.validate_proposal_obj(obj)
    assert "BAD_BLINDNESS_DECLARATION" in res["completeness_violations"]


# --------------------------------------------------------------------- #
# 2. synthetic fixtures: blindness negative scan                         #
# --------------------------------------------------------------------- #

@pytest.mark.parametrize("token", [
    "the expectancy of the arm",
    "the arm PnL",
    "sharpe ratio of the anchor",
    "hit_rate of the state",
    "win rate of the placebo",
    "the strategy CAGR",
    "max drawdown",
    "profit factor",
    "the arm returns",          # bare return/returns
    "total_return of the cell",
    "mean return per trade",
    "average_return per decision",
    "the alpha earned",
])
def test_synthetic_forbidden_tokens_are_caught(token):
    assert dv.forbidden_token_scan(token) != []


def test_synthetic_clean_prose_has_no_token_hits():
    text = ("KILL if the placebo earns a strictly greater after-cost "
            "per-decision edge than the anchor on the identical grid.")
    assert dv.forbidden_token_scan(text) == []


def test_synthetic_non_allowlisted_numeric_leaf_is_caught():
    obj = _minimal_valid_proposal()
    obj["mechanism"]["sneaky_outcome_metric"] = 1.23
    res = dv.validate_proposal_obj(obj)
    assert any(v["key"] == "sneaky_outcome_metric"
               for v in res["numeric_leaf_violations"])


def test_synthetic_ticker_keyed_numeric_leaf_is_caught():
    obj = _minimal_valid_proposal()
    obj["representation_identity"]["series"]["by_leg"] = {"TLT": 6071}
    res = dv.validate_proposal_obj(obj)
    assert any(v["key"] == "TLT"
               for v in res["numeric_leaf_violations"])


def test_synthetic_allowlisted_numeric_leaves_pass():
    obj = _minimal_valid_proposal()
    obj["feasibility_citation"]["cost_ceilings_cited"] = {
        "per_leg": [{"leg": "SHY",
                     "stress_tier_bps": 5.979816345415081,
                     "worst_case_round_trip_ceiling_bps": 12.247303923706875}]
    }
    res = dv.validate_proposal_obj(obj)
    assert res["numeric_leaf_violations"] == []


def test_synthetic_bool_values_are_not_numeric_violations():
    obj = _minimal_valid_proposal()
    obj["representation_identity"]["grid"]["bookable"] = True
    res = dv.validate_proposal_obj(obj)
    assert res["numeric_leaf_violations"] == []


# --------------------------------------------------------------------- #
# 3. synthetic fixtures: battery composition                             #
# --------------------------------------------------------------------- #

def test_synthetic_a4_missing_killer_role_is_caught():
    obj = _minimal_valid_proposal()
    obj["control_battery_spec"]["arms"] = [
        a for a in obj["control_battery_spec"]["arms"]
        if a["role"] != "SHIFTED_CALENDAR_PLACEBO"]
    res = dv.validate_proposal_obj(obj)
    assert "MISSING_ARM_ROLE:SHIFTED_CALENDAR_PLACEBO" \
        in res["battery_violations"]


def test_synthetic_a5_requires_level_vs_shape_control():
    obj = _minimal_valid_proposal()
    obj["lane"] = "A5"
    obj["control_battery_spec"]["arms"] = [
        {"role": "ANCHOR", "spec": "s"},
        {"role": "CLOCK_ONLY_SHADOW", "spec": "s"},
        {"role": "PLACEBO", "spec": "s"},
    ]
    res = dv.validate_proposal_obj(obj)
    assert "MISSING_ARM_ROLE:LEVEL_VS_SHAPE_DECOMPOSITION_CONTROL" \
        in res["battery_violations"]


def test_synthetic_unknown_lane_is_caught():
    obj = _minimal_valid_proposal()
    obj["lane"] = "A9"
    res = dv.validate_proposal_obj(obj)
    assert any(v.startswith("BAD_LANE") for v in res["battery_violations"])


# --------------------------------------------------------------------- #
# 4. synthetic fixtures: pin verification                                #
# --------------------------------------------------------------------- #

def test_synthetic_pin_mismatch_is_caught(tmp_path):
    bad = tmp_path / "decoy.txt"
    bad.write_text("not the pinned bytes", encoding="utf-8")
    obj = _minimal_valid_proposal()
    obj["feasibility_citation"]["floor_artifacts"] = [{
        "path": "decoy.txt",
        "sha256": "0" * 64,
    }]
    res = dv.pin_violations(obj, worktree=str(tmp_path))
    assert res == [{"path": "decoy.txt", "error": "SHA_MISMATCH"}]


def test_synthetic_pin_missing_file_is_caught(tmp_path):
    obj = _minimal_valid_proposal()
    obj["feasibility_citation"]["floor_artifacts"] = [{
        "path": "no_such_file.txt",
        "sha256": "0" * 64,
    }]
    res = dv.pin_violations(obj, worktree=str(tmp_path))
    assert res == [{"path": "no_such_file.txt", "error": "MISSING_FILE"}]


# --------------------------------------------------------------------- #
# 5. committed proposals: identity, completeness, blindness              #
# --------------------------------------------------------------------- #

def test_committed_proposal_ids_and_files_exist():
    for pid in dv.PROPOSAL_IDS:
        assert os.path.isfile(os.path.join(PROPOSALS_DIR, f"{pid}.json"))


@pytest.mark.parametrize("pid", dv.PROPOSAL_IDS)
def test_committed_proposal_full_validation(pid):
    obj = _load_committed(pid)
    assert obj["proposal_id"] == pid
    res = dv.validate_proposal_obj(obj)
    assert res["completeness_violations"] == []
    assert res["battery_violations"] == []
    assert res["numeric_leaf_violations"] == []
    assert res["pin_violations"] == []
    assert dv.forbidden_token_scan(_committed_raw(pid)) == []


@pytest.mark.parametrize("pid", dv.PROPOSAL_IDS)
def test_committed_proposal_lane_identity(pid):
    obj = _load_committed(pid)
    want_lane = "A4" if pid.startswith("RATESNG1-A4") else "A5"
    assert obj["lane"] == want_lane
    assert obj["schema"] == dv.SCHEMA_PROPOSAL
    assert obj["cycle_id"] == dv.CYCLE_ID
    assert obj["base_sha"] == dv.BASE_SHA
    assert obj["blindness_declaration"]["status"] == "OUTCOME_BLIND"


@pytest.mark.parametrize("pid", dv.PROPOSAL_IDS)
def test_committed_proposal_battery_roles_complete(pid):
    obj = _load_committed(pid)
    roles = {a["role"] for a in obj["control_battery_spec"]["arms"]}
    assert dv.BATTERY_ROLE_REQUIREMENTS[obj["lane"]] <= roles
    assert "ANCHOR" in roles


@pytest.mark.parametrize("pid", dv.PROPOSAL_IDS)
def test_committed_proposal_representation_identity_laws(pid):
    obj = _load_committed(pid)
    rep = obj["representation_identity"]
    grid_blob = json.dumps(rep["grid"])
    series_blob = json.dumps(rep["series"])
    assert "16:00" in grid_blob and "1918" in grid_blob
    assert "P2 common grid" in grid_blob
    # curve + ETP legs both named, consumed via the plane
    assert "consume_via_plane" in series_blob
    assert "TLT" in series_blob and "SHY" in series_blob
    assert "IEF" in series_blob and "IEI" in series_blob
    # decision instant law = V7 close+1, no same-day reads
    dil = json.dumps(rep["decision_instant_law"])
    assert "V7 close+1" in dil and "no same-day reads" in dil


@pytest.mark.parametrize("pid", dv.PROPOSAL_IDS)
def test_committed_proposal_ancestry_names_all_shadows(pid):
    obj = _load_committed(pid)
    blob = json.dumps(obj["ancestry_risk_statement"])
    for shadow in ("DGS10-level", "#14", "#15",
                   "reaction-direction", "momentum_63s", "generic_dow_tue"):
        assert shadow in blob, f"{pid}: ancestry missing {shadow}"


def test_committed_a4_event_mapping_pit_later_bound():
    for pid in ("RATESNG1-A4-P1", "RATESNG1-A4-P2"):
        obj = _load_committed(pid)
        ev = obj["representation_identity"]["event_mapping"]
        blob = json.dumps(ev)
        assert "PIT later-bound" in blob
        assert "REFUSED" in blob          # same-day close refused
        assert "STRICTLY AFTER" in blob   # first later grid session
        assert ev["event_count"] == 3555
        assert ev["sha256"] == (
            "71411ace6061848f988f63d790c20352835a53f62fc688159b54748c35d7b48b")


def test_committed_a5_mandatory_level_vs_shape_control():
    for pid in ("RATESNG1-A5-P1", "RATESNG1-A5-P2"):
        obj = _load_committed(pid)
        arms = obj["control_battery_spec"]["arms"]
        lvl = [a for a in arms
               if a["role"] == "LEVEL_VS_SHAPE_DECOMPOSITION_CONTROL"]
        assert len(lvl) == 1
        assert "MANDATORY" in lvl[0]["name"]
        assert "orthogonal" in json.dumps(obj["control_battery_spec"]).lower()
        # falsification rule names the level-control kill
        assert "LEVEL_VS_SHAPE_DECOMPOSITION_CONTROL" \
            in obj["falsification_rule"]["killer_controls"]


def test_committed_proposal_falsification_rules_are_concrete():
    for pid in dv.PROPOSAL_IDS:
        fr = _load_committed(pid)["falsification_rule"]
        blob = json.dumps(fr)
        assert "KILL if" in fr["statement"]
        assert fr["declared_at"].startswith("D1")
        assert fr["measurable_at"] in ("D2/I", "D2")
        assert fr["killer_controls"]


def test_committed_proposal_feasibility_pins_match_p2_gate_numbers():
    gate = json.load(open(os.path.join(
        WORKTREE, "research", "control", "rates_ng1_run", "p2_gate.json"),
        encoding="utf-8"))
    ceilings = gate["cost_ceilings"]["per_leg"]
    for pid in dv.PROPOSAL_IDS:
        cc = _load_committed(pid)["feasibility_citation"][
            "cost_ceilings_cited"]
        for row in cc["per_leg_worst_case_round_trip_ceiling_bps"]:
            want = ceilings[row["leg"]]["worst_case_round_trip_ceiling_bps"]
            assert row["worst_case_round_trip_ceiling_bps"] == want


def test_committed_proposals_carry_pins_that_verify_on_disk():
    total_pins = 0
    for pid in dv.PROPOSAL_IDS:
        obj = _load_committed(pid)
        assert dv.pin_violations(obj) == []
        n_pins = _count_pins(obj)
        # A4 pins include grid + eligibility + cost contract + gate +
        # P0 censuses; A5 pins include grid + curve + ETP + contract.
        if pid.startswith("RATESNG1-A4"):
            assert n_pins >= 6
        else:
            assert n_pins >= 5
        total_pins += n_pins
    assert total_pins >= 22


def _count_pins(obj) -> int:
    n = 0
    if isinstance(obj, dict):
        if "path" in obj and "sha256" in obj:
            n += 1
        for v in obj.values():
            n += _count_pins(v)
    elif isinstance(obj, list):
        for v in obj:
            n += _count_pins(v)
    return n


# --------------------------------------------------------------------- #
# 6. committed d1_gate.json                                              #
# --------------------------------------------------------------------- #

def test_gate_schema_pin_and_verdicts():
    with open(GATE_PATH, encoding="utf-8") as fh:
        gate = json.load(fh)
    assert gate["schema"] == dv.SCHEMA_GATE
    assert gate["schema_version"] == dv.GATE_SCHEMA_VERSION
    assert gate["cycle_id"] == dv.CYCLE_ID
    assert gate["base_sha"] == dv.BASE_SHA
    assert gate["verdict"] == "PASS"
    assert [f["proposal_id"] for f in gate["proposal_files"]] \
        == dv.PROPOSAL_IDS
    for f in gate["proposal_files"]:
        assert f["verdict"] == "PASS"
        assert f["completeness_verdict"] == "PASS"
        assert f["battery_verdict"] == "PASS"
        assert f["missing_fields"] == []
        assert f["forbidden_token_hits"] == []
        assert f["numeric_leaf_violations"] == []
        assert f["pin_violations"] == []


def test_gate_negative_scan_is_clean():
    with open(GATE_PATH, encoding="utf-8") as fh:
        gate = json.load(fh)
    scan = gate["blindness_negative_scan"]
    assert scan["verdict"] == "PASS"
    assert scan["proposals_scanned"] == 4
    assert scan["forbidden_token_hits"] == 0
    assert scan["numeric_leaf_violations"] == 0
    assert scan["files_with_outcome_numbers"] == 0


def test_gate_matches_live_rederivation_from_committed_files():
    with open(GATE_PATH, encoding="utf-8") as fh:
        committed = json.load(fh)
    live = dv.build_gate(authored_utc=committed["authored_utc"])
    assert live == committed


def test_gate_file_pins_match_proposal_files_on_disk():
    with open(GATE_PATH, encoding="utf-8") as fh:
        gate = json.load(fh)
    for f in gate["proposal_files"]:
        p = os.path.join(WORKTREE, f["path"])
        assert os.path.isfile(p)
        with open(p, "rb") as fh:
            import hashlib
            assert hashlib.sha256(fh.read()).hexdigest() == f["sha256"]
