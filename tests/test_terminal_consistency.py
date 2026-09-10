"""F3 terminal-consistency validator tests (MARKET-DATA-PLANE-V2 freeze F3).

The stale fixture below is SYNTHETIC: it is shape-copied from the real V1
run dir research/control/market_data_plane_v1_run/ as of the freeze
(state P8_A7_AUDIT_IN_FLIGHT with short head 35492e6, G11 IN FLIGHT /
G12 PENDING; heartbeat same phase and older than the terminal close;
worktree_manifest planned[] still listing the a8-nautilus / a7-audit lanes;
registry row head 6643359826f8ef25dea0c29b58994241d905a9ea with an empty
integration_worktree) but no test touches the real tree: every fixture is
built in-memory or in tmp_path (hermetic).

Frozen required behavior:
  - the stale fixture FAILS (non-empty findings) WITHOUT an addendum;
  - it PASSES ([]) ONLY when the addendum names EVERY stale field with its
    exact stale value and the derived corrected value;
  - historical bad bytes stay visible: the validator never mutates its
    inputs and never writes a file.
"""
from __future__ import annotations

import copy
import json
import sys
from collections import Counter
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

from governance import terminal_consistency as tc  # noqa: E402

# -------------------------------------------------------- frozen constants

REPORT_HEAD = "9662781dfcd066eb3ca3084752e33cb99f07aa4c"
BRANCH_TIP = "917b8749c6e61887d0e1046a3b99a1f1cf53dca6"
EARLY_REGISTRY_HEAD = "6643359826f8ef25dea0c29b58994241d905a9ea"
STALE_PHASE = "P8_A7_AUDIT_IN_FLIGHT"
TERMINAL_PHASE = "P9_TERMINAL"
RECORDED_UTC = "2026-09-09T13:37:43Z"
HEARTBEAT_UTC = "2026-09-09T13:14:37Z"
V1_WORKTREE = "/Users/hoangminhlong/my-quantitative/.worktrees/market-data-plane-v1/integration"

STALE_EVENT_LINES = [
    json.dumps({"utc": "2026-09-09T10:59:25Z", "event": "P0_BOOTSTRAP",
                "detail": "owner GO consumed at its gate; integration "
                          "worktree created from main f3903f8"}),
    json.dumps({"utc": "2026-09-09T13:14:37Z", "event": "P3_TO_P7_COMPLETE",
                "detail": "A8 picked; P5 battery PASS; A7 dispatched from "
                          "frozen 42981b1"}),
    json.dumps({"utc": RECORDED_UTC, "event": TERMINAL_PHASE,
                "detail": "verdict MARKET_DATA_PLANE_V1_BLOCKED_RESOURCE_"
                          "CONFLICT: all gates PASS except G9 full-suite "
                          "component"}),
]


# ----------------------------------------------------------------- fixtures

def _terminal_report():
    return {
        "schema": "mdp_terminal_report@1",
        "cycle": "MARKET-DATA-PLANE-V1",
        "verdict": "MARKET_DATA_PLANE_V1_BLOCKED_RESOURCE_CONFLICT",
        "recorded_utc": RECORDED_UTC,
        "head_integration": REPORT_HEAD,
        "gates": {
            "G0": "PASS",
            "G1": "PASS (M0)",
            "G2": "PASS (upstream_manifest.json)",
            "G3": "PASS (G3_data_fusion_fixes.json)",
            "G4": "PASS (227-test MDP suite)",
            "G5": "PASS (incl. detached-tree reproduction)",
            "G6": "PASS",
            "G7": "PASS (nautilus 1.230.0)",
            "G8": "PASS (secret/forbidden/execution scans)",
            "G8A": "PASS (dvc_poc_result.json)",
            "G8B": "PASS (mdp_ci + mdp_deep)",
            "G8C": "PANDERA_EVALUATED_NOT_ADOPTED (2/7 frozen criteria fail)",
            "G8D": "PASS",
            "G9": "PARTIAL: targeted+compat PASS; FULL SUITE "
                  "NOT_RUN_RESOURCE_CONFLICT",
            "G10": "PASS (baseline frozen: median 11573.1 eps)",
            "G11": "PASS (A7 verdict 0 HIGH/CRITICAL, pinned to 42981b1)",
            "G12": "PASS (no owned workers; all MDP worktrees clean)",
        },
    }


def _stale_state():
    return {
        "phase": STALE_PHASE,
        "updated_utc": HEARTBEAT_UTC,
        "head_integration": "35492e6",
        "open_gates": ["G0", "G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8",
                       "G8A", "G8B", "G8C", "G8D", "G9", "G10", "G11", "G12"],
        "lanes_running": ["A2", "A3", "A4"],
        "completed_gates": {
            "G0": "PASS (P0)",
            "G1": "PASS (M0)",
            "G2": "PASS (P1 pin)",
            "G3": "PASS (P4 fixes)",
            "G4": "PASS",
            "G5": "PASS (incl. detached-tree reproduction)",
            "G6": "PASS",
            "G7": "PASS (A8)",
            "G8": "PASS (scans)",
            "G8A": "PASS (DVC POC + DVC-LIMITATION-1)",
            "G8B": "PASS (mdp_ci+deep)",
            "G8C": "PANDERA_EVALUATED_NOT_ADOPTED",
            "G8D": "PASS",
            "G9": "PARTIAL — targeted/compat/compileall/diff-check PASS; "
                  "full suite NOT_RUN_RESOURCE_CONFLICT",
            "G10": "PASS (baseline frozen 11573.1 eps median)",
            "G11": "IN FLIGHT (A7)",
            "G12": "PENDING",
        },
    }


def _stale_heartbeat():
    return {"utc": HEARTBEAT_UTC, "phase": STALE_PHASE, "holder": "A1"}


def _stale_manifest():
    return {
        "root_head_at_creation": "f3903f8524c73f83d1884a5fcd0433e0a5a5c4fd",
        "worktrees": [
            {"path": ".worktrees/market-data-plane-v1/integration",
             "branch": "orca/market-data-plane-v1-integration",
             "base": "main@f3903f8", "owner": "A1"},
        ],
        "planned": [
            {"path": ".worktrees/market-data-plane-v1/a8-nautilus",
             "branch": "orca/market-data-plane-v1-a8-nautilus",
             "owner": "A8"},
            {"path": ".worktrees/market-data-plane-v1/a7-audit",
             "branch": "orca/market-data-plane-v1-a7-audit",
             "owner": "A7"},
        ],
        "updated_utc": "2026-09-09T11:18:45Z",
    }


def _stale_registry_row():
    return {
        "cycle_id": "MARKET-DATA-PLANE-V1",
        "lifecycle": "TERMINAL",
        "phase": "BLOCKED_RESOURCE_CONFLICT (resumable)",
        "integration_worktree": "",
        "branch": "orca/market-data-plane-v1-integration",
        "head": EARLY_REGISTRY_HEAD,
        "workers": 0,
        "go_phrase": "",
        "go_phrase_state": "DEAD (consumed or extinguished at its cycle's "
                           "close per P-8 / RULES §7)",
        "heartbeat_utc": "2026-09-09T11:36:23Z",
        "active_heavy": False,
    }


def _stale_bundle():
    return {
        "terminal_report": _terminal_report(),
        "state": _stale_state(),
        "heartbeat": _stale_heartbeat(),
        "worktree_manifest": _stale_manifest(),
        "registry_row": _stale_registry_row(),
        "branch_tip": BRANCH_TIP,
        "event_log_lines": list(STALE_EVENT_LINES),
    }


def _call(bundle, addendum=None):
    return tc.validate_terminal_consistency(
        bundle["terminal_report"], bundle["state"], bundle["heartbeat"],
        bundle["worktree_manifest"], bundle["registry_row"],
        bundle["branch_tip"], bundle["event_log_lines"], addendum)


def _full_addendum(bundle, expected_registry_head=BRANCH_TIP):
    report, state, hb, manifest = (bundle["terminal_report"],
                                   bundle["state"], bundle["heartbeat"],
                                   bundle["worktree_manifest"])
    return {
        "schema": "mdp_terminal_addendum@1",
        "cycle": report["cycle"],
        "supersedes_fields": [
            {"file": "state.json", "field": "phase",
             "stale_value": state["phase"],
             "corrected_value": TERMINAL_PHASE},
            {"file": "state.json", "field": "head_integration",
             "stale_value": state["head_integration"],
             "corrected_value": report["head_integration"]},
            {"file": "state.json", "field": "completed_gates.G11",
             "stale_value": state["completed_gates"]["G11"],
             "corrected_value": report["gates"]["G11"]},
            {"file": "state.json", "field": "completed_gates.G12",
             "stale_value": state["completed_gates"]["G12"],
             "corrected_value": report["gates"]["G12"]},
            {"file": "state.json", "field": "open_gates",
             "stale_value": state["open_gates"],
             "corrected_value": ["G8C", "G9"]},
            {"file": "heartbeat.json", "field": "phase",
             "stale_value": hb["phase"],
             "corrected_value": TERMINAL_PHASE},
            {"file": "heartbeat.json", "field": "utc",
             "stale_value": hb["utc"],
             "corrected_value": report["recorded_utc"]},
            {"file": "worktree_manifest.json", "field": "planned[0]",
             "stale_value": manifest["planned"][0], "corrected_value": None},
            {"file": "worktree_manifest.json", "field": "planned[1]",
             "stale_value": manifest["planned"][1], "corrected_value": None},
            {"file": "registry", "field": "head",
             "stale_value": EARLY_REGISTRY_HEAD,
             "corrected_value": expected_registry_head},
            {"file": "registry", "field": "integration_worktree",
             "stale_value": "", "corrected_value": V1_WORKTREE},
        ],
        "evidence": [
            "terminal_report.json verdict + gates (P9 close)",
            "git rev-parse orca/market-data-plane-v1-integration",
        ],
        "created_utc": "2026-09-10T03:00:00Z",
    }


def _consistent_bundle():
    b = _stale_bundle()
    report = b["terminal_report"]
    b["state"].update(phase=TERMINAL_PHASE,
                      head_integration=REPORT_HEAD,
                      open_gates=["G8C", "G9"])
    b["state"]["completed_gates"]["G11"] = report["gates"]["G11"]
    b["state"]["completed_gates"]["G12"] = report["gates"]["G12"]
    b["heartbeat"].update(phase=TERMINAL_PHASE, utc=RECORDED_UTC)
    b["worktree_manifest"]["planned"] = []
    b["registry_row"].update(head=BRANCH_TIP,
                             integration_worktree=V1_WORKTREE)
    return b


# ------------------------------------------------------------------- tests

def test_stale_fixture_fails_without_addendum():
    findings = _call(_stale_bundle())
    assert findings, "the frozen V1 stale fixture must FAIL without addendum"
    counts = Counter(f["kind"] for f in findings)
    assert counts == {
        "STATE_PHASE_STALE": 1,
        "STATE_HEAD_MISMATCH": 1,
        "GATE_STATE_CONTRADICTION": 2,   # G11 IN FLIGHT, G12 PENDING
        "OPEN_GATES_CONTRADICTION": 1,
        "HEARTBEAT_PHASE_STALE": 1,
        "HEARTBEAT_STALE": 1,
        "PLANNED_LANE_STALE": 2,         # a8-nautilus, a7-audit
        "REGISTRY_HEAD_STALE": 1,        # 6643359 vs branch tip
        "REGISTRY_WORKTREE_MISSING": 1,  # empty integration_worktree
    }
    details = "\n".join(f["detail"] for f in findings)
    for stale_marker in ("P8_A7_AUDIT_IN_FLIGHT", "'35492e6'",
                         "IN FLIGHT (A7)", "'PENDING'", "a8-nautilus",
                         "a7-audit", EARLY_REGISTRY_HEAD, "917b8749"):
        assert stale_marker in details, f"missing stale marker: {stale_marker}"


def test_finding_shape_is_exactly_kind_severity_detail():
    findings = _call(_stale_bundle())
    for f in findings:
        assert set(f) == {"kind", "severity", "detail"}
        assert f["severity"] in {"LOW", "MEDIUM", "HIGH"}
        assert f["detail"]
    by_kind = {f["kind"]: f for f in findings}
    assert by_kind["STATE_PHASE_STALE"]["severity"] == "HIGH"
    assert by_kind["REGISTRY_HEAD_STALE"]["severity"] == "HIGH"
    assert by_kind["PLANNED_LANE_STALE"]["severity"] == "MEDIUM"
    assert by_kind["HEARTBEAT_STALE"]["severity"] == "LOW"


def test_full_addendum_passes_empty():
    bundle = _stale_bundle()
    assert _call(bundle, _full_addendum(bundle)) == []


def test_partial_addendum_leaves_uncovered_findings():
    bundle = _stale_bundle()
    add = _full_addendum(bundle)
    # drop exactly the heartbeat-phase correction
    add["supersedes_fields"] = [
        e for e in add["supersedes_fields"]
        if not (e["file"] == "heartbeat.json" and e["field"] == "phase")]
    findings = _call(bundle, add)
    assert [f["kind"] for f in findings] == ["HEARTBEAT_PHASE_STALE"]


def test_wrong_corrected_value_is_not_covered():
    bundle = _stale_bundle()
    add = _full_addendum(bundle)
    for e in add["supersedes_fields"]:
        if e["file"] == "state.json" and e["field"] == "phase":
            e["corrected_value"] = "P10_DONE"  # not what the artifacts derive
    kinds = [f["kind"] for f in _call(bundle, add)]
    assert kinds.count("STATE_PHASE_STALE") == 1


def test_wrong_stale_value_is_not_covered():
    bundle = _stale_bundle()
    add = _full_addendum(bundle)
    for e in add["supersedes_fields"]:
        if e["field"] == "integration_worktree":
            e["stale_value"] = "/some/other/path"  # bytes say ""
    kinds = [f["kind"] for f in _call(bundle, add)]
    assert kinds.count("REGISTRY_WORKTREE_MISSING") == 1


def test_empty_string_correction_never_covers_worktree():
    bundle = _stale_bundle()
    add = _full_addendum(bundle)
    for e in add["supersedes_fields"]:
        if e["field"] == "integration_worktree":
            e["corrected_value"] = ""  # non-empty string required
    kinds = [f["kind"] for f in _call(bundle, add)]
    assert kinds.count("REGISTRY_WORKTREE_MISSING") == 1


@pytest.mark.parametrize("mutate", [
    {"schema": "mdp_terminal_addendum@0"},
    {"cycle": "FOREIGN-CYCLE"},
    {"created_utc": "not-a-timestamp"},
])
def test_invalid_addendum_is_rejected_and_coverages_dropped(mutate):
    bundle = _stale_bundle()
    add = _full_addendum(bundle)
    add.update(mutate)
    findings = _call(bundle, add)
    kinds = Counter(f["kind"] for f in findings)
    assert kinds["ADDENDUM_INVALID"] == 1
    # NO correction applied: every original stale finding stands
    for kind, n in Counter(f["kind"] for f in _call(bundle)).items():
        assert kinds[kind] == n, kind


def test_addendum_without_supersedes_fields_is_invalid():
    bundle = _stale_bundle()
    add = _full_addendum(bundle)
    add["supersedes_fields"] = []
    kinds = [f["kind"] for f in _call(bundle, add)]
    assert "ADDENDUM_INVALID" in kinds
    assert "STATE_PHASE_STALE" in kinds  # nothing was covered


def test_validator_never_mutates_inputs():
    bundle = _stale_bundle()
    before = copy.deepcopy(bundle)
    add = _full_addendum(bundle)
    add_before = copy.deepcopy(add)
    _call(bundle)
    _call(bundle, add)
    assert bundle == before, "historical bytes must stay untouched in memory"
    assert add == add_before


def test_consistent_terminal_fixture_passes_with_no_addendum():
    assert _call(_consistent_bundle()) == []


def test_registry_terminal_workers_and_go_death_enforced():
    b = _consistent_bundle()
    b["registry_row"]["workers"] = 1
    findings = _call(b)
    assert [f["kind"] for f in findings] == ["REGISTRY_TERMINAL_WORKERS"]

    b = _consistent_bundle()
    b["registry_row"]["go_phrase_state"] = "REGISTERED_NOT_CONSUMED"
    findings = _call(b)
    assert [f["kind"] for f in findings] == ["REGISTRY_GO_NOT_DEAD"]

    b = _consistent_bundle()
    b["registry_row"]["go_phrase_state"] = "DEAD (extinguished at close)"
    assert _call(b) == []  # any DEAD-prefixed dead state is consistent


def test_registry_lifecycle_must_be_terminal():
    b = _consistent_bundle()
    b["registry_row"]["lifecycle"] = "ACTIVE_LIGHT"
    findings = _call(b)
    assert [f["kind"] for f in findings] == ["REGISTRY_LIFECYCLE_STALE"]


def test_registry_head_checked_against_branch_tip_then_report_head():
    b = _consistent_bundle()
    b["registry_row"]["head"] = REPORT_HEAD  # tip unknown -> report head ok
    b["branch_tip"] = None
    assert _call(b) == []
    b["branch_tip"] = BRANCH_TIP
    findings = _call(b)
    assert [f["kind"] for f in findings] == ["REGISTRY_HEAD_STALE"]
    assert BRANCH_TIP in findings[0]["detail"]


def test_missing_registry_row_is_a_finding():
    b = _consistent_bundle()
    b["registry_row"] = None
    findings = _call(b)
    assert [f["kind"] for f in findings] == ["REGISTRY_ROW_MISSING"]


def test_event_log_malformed_lines_are_findings():
    b = _consistent_bundle()
    b["event_log_lines"] = list(STALE_EVENT_LINES) + ["{not json at all"]
    findings = _call(b)
    assert [f["kind"] for f in findings] == ["EVENT_LOG_MALFORMED"]

    b["event_log_lines"] = list(STALE_EVENT_LINES) + ["42"]  # JSON, not event
    findings = _call(b)
    assert [f["kind"] for f in findings] == ["EVENT_LOG_MALFORMED"]

    b["event_log_lines"] = list(STALE_EVENT_LINES) + ["", "  "]  # tolerated
    assert _call(b) == []


def test_terminal_phase_is_derived_from_the_event_log():
    b = _consistent_bundle()
    b["event_log_lines"] = [
        json.dumps({"utc": RECORDED_UTC, "event": "P9_CLOSE",
                    "detail": "synthetic alternate terminal event name"})]
    b["state"]["phase"] = "P9_CLOSE"
    b["heartbeat"]["phase"] = "P9_CLOSE"
    assert _call(b) == []  # expected phase derived from the log, not hardcoded


def test_heartbeat_staleness_needs_addendum_even_alone():
    b = _consistent_bundle()
    b["heartbeat"]["utc"] = HEARTBEAT_UTC  # older than the terminal close
    findings = _call(b)
    assert [f["kind"] for f in findings] == ["HEARTBEAT_STALE"]

    add = {"schema": "mdp_terminal_addendum@1", "cycle":
           b["terminal_report"]["cycle"],
           "supersedes_fields": [
               {"file": "heartbeat.json", "field": "utc",
                "stale_value": HEARTBEAT_UTC,
                "corrected_value": RECORDED_UTC}],
           "evidence": ["terminal_report recorded_utc"],
           "created_utc": "2026-09-10T03:00:00Z"}
    assert _call(b, add) == []


def test_invalid_terminal_report_blocks_dependent_checks():
    b = _consistent_bundle()
    b["terminal_report"] = {"schema": "mdp_terminal_report@1"}  # no verdict etc
    findings = _call(b)
    assert [f["kind"] for f in findings] == ["TERMINAL_REPORT_INVALID"]


# ------------------------------------------------------- check_v1_run_dir

def _write_run_dir(root: Path) -> Path:
    run_dir = root / "research" / "control" / "market_data_plane_v1_run"
    run_dir.mkdir(parents=True)
    b = _stale_bundle()
    (run_dir / "terminal_report.json").write_text(
        json.dumps(b["terminal_report"], indent=1))
    (run_dir / "state.json").write_text(json.dumps(b["state"], indent=1))
    (run_dir / "heartbeat.json").write_text(
        json.dumps(b["heartbeat"], indent=1))
    (run_dir / "worktree_manifest.json").write_text(
        json.dumps(b["worktree_manifest"], indent=1))
    (run_dir / "event_log.jsonl").write_text(
        "\n".join(b["event_log_lines"]) + "\n")
    (root / "plans").mkdir(exist_ok=True)
    (root / "plans" / "CYCLE_REGISTRY.json").write_text(json.dumps({
        "schema": "cycle_registry@1",
        "cycles": [b["registry_row"]],
    }))
    return run_dir


def test_check_v1_run_dir_fails_stale_then_passes_with_addendum(tmp_path):
    run_dir = _write_run_dir(tmp_path)
    tree_before = sorted(str(p) for p in run_dir.rglob("*"))

    findings = tc.check_v1_run_dir(run_dir)
    assert findings, "stale run dir must FAIL without addendum"
    counts = Counter(f["kind"] for f in findings)
    # no git repo in tmp -> branch tip unresolvable -> registry head is
    # expected to match the terminal report head instead
    assert "REGISTRY_HEAD_STALE" in counts
    assert "REGISTRY_WORKTREE_MISSING" in counts
    assert counts["PLANNED_LANE_STALE"] == 2

    bundle = _stale_bundle()
    add = _full_addendum(bundle, expected_registry_head=REPORT_HEAD)
    assert tc.check_v1_run_dir(run_dir, addendum=add) == []

    assert sorted(str(p) for p in run_dir.rglob("*")) == tree_before, \
        "check_v1_run_dir must never write (historical bytes stay visible)"


def test_check_v1_run_dir_missing_file_is_a_finding(tmp_path):
    run_dir = _write_run_dir(tmp_path)
    (run_dir / "worktree_manifest.json").unlink()
    kinds = [f["kind"] for f in tc.check_v1_run_dir(run_dir)]
    assert "RUN_FILE_MISSING" in kinds


def test_check_v1_run_dir_unreadable_json_is_a_finding(tmp_path):
    run_dir = _write_run_dir(tmp_path)
    (run_dir / "heartbeat.json").write_text("{oops")
    kinds = [f["kind"] for f in tc.check_v1_run_dir(run_dir)]
    assert "RUN_FILE_UNREADABLE" in kinds


def test_check_v1_run_dir_without_registry_row(tmp_path):
    run_dir = _write_run_dir(tmp_path)
    (tmp_path / "plans" / "CYCLE_REGISTRY.json").unlink()
    kinds = [f["kind"] for f in tc.check_v1_run_dir(run_dir)]
    assert "REGISTRY_ROW_MISSING" in kinds
