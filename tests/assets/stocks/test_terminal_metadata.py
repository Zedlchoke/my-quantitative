"""Terminal-metadata and data-authority packet contracts (reconciliation).

Locks the 2026-09-02 terminal reconciliation:

- ``terminal_report.json`` must express forbidden actions explicitly and can
  never again carry the reversed-meaning ``forbidden_actions_performed`` key;
- ``state.json`` must never again point at S2 as "next";
- the six agreement surfaces (state, heartbeat, terminal_report, selection
  freeze, event log, wayfinder MAP) must state the same terminal facts;
- the data-authority packet stays provider-neutral and fail-closed.

A1 owns this file; A7 verifies independently.
"""
import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
CTRL = REPO / "research/control/stocks_run"
DA = CTRL / "data_authority"
MAP = REPO / "research/wayfinder/MAP.md"

VERDICT = "STOCKS_BLOCKED_DATA_AUTHORITY"
FAMILIES = {"EQ_S2_A3_F1_PIT_RECON_FLOW", "A5-S2-F1-LENDING-CONSTRAINT-PREMIUM"}
FORBIDDEN_SET = {
    "push", "merge to main", "deletion/reset of others' history",
    "S1 access", "paid data", "credentials", "paper/live orders",
}


def _load(path):
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def state():
    return _load(CTRL / "state.json")


@pytest.fixture(scope="module")
def heartbeat():
    return _load(CTRL / "heartbeat.json")


@pytest.fixture(scope="module")
def terminal():
    return _load(CTRL / "terminal_report.json")


@pytest.fixture(scope="module")
def freeze():
    return _load(CTRL / "selection_freeze.json")


@pytest.fixture(scope="module")
def packet():
    return _load(DA / "requirements.json")


@pytest.fixture(scope="module")
def template():
    return _load(DA / "provider_evaluation_template.json")


@pytest.fixture(scope="module")
def map_text():
    return re.sub(r"\s+", " ", MAP.read_text())


# --------------------------------------------------------------------------
# 1. forbidden actions cannot reverse meaning again
# --------------------------------------------------------------------------

def test_reversed_meaning_key_is_gone(terminal):
    assert "forbidden_actions_performed" not in terminal


def test_forbidden_actions_explicit_and_one_sided(terminal):
    fa = terminal["forbidden_actions"]
    assert fa["performed"] == []
    assert FORBIDDEN_SET <= set(fa["not_performed"])


# --------------------------------------------------------------------------
# 2. state.next cannot point at a completed wave again
# --------------------------------------------------------------------------

def test_no_stale_next_key(state):
    assert "next" not in state


def test_next_authorized_sequence_orders_data_authority_before_s4_s5_s6(state):
    seq = [step.lower() for step in state["next_authorized_sequence"]]
    joined = " ".join(seq)
    assert "data authority" in joined
    idx = {k: next(i for i, s in enumerate(seq) if k in s)
           for k in ("1.", "2.", "3.", "4.")}
    assert idx["1."] < idx["2."] < idx["3."] < idx["4."]
    assert any("s4" in s for s in seq)
    assert any("s5" in s for s in seq)
    assert any("s6" in s for s in seq)


def test_sequence_does_not_describe_s2_as_future_work(state):
    blob = json.dumps(state["next_authorized_sequence"]).lower()
    assert "s2" not in blob


# --------------------------------------------------------------------------
# 3. six-surface terminal agreement
# --------------------------------------------------------------------------

def test_phase_terminal_at_s3(state, heartbeat, terminal, freeze):
    assert state["phase"] == "TERMINAL"
    assert state["wave"] == "S3"
    assert heartbeat["phase"] == "TERMINAL_AT_S3"
    assert terminal["terminal_phase"] == "TERMINAL_AT_S3"
    assert freeze["sprint_phase"] == "TERMINAL_AT_S3"


def test_verdict_identical_everywhere(state, heartbeat, terminal, freeze, map_text):
    for source in (state["verdict"], heartbeat["verdict"],
                   terminal["sprint_verdict"], freeze["sprint_verdict"]):
        assert source == VERDICT
    assert VERDICT in map_text


def test_exactly_two_selected_families_agree(state, terminal, freeze):
    assert {f["family_id"] for f in freeze["selected_families"]} == FAMILIES
    assert set(state["selection"]["families"]) == FAMILIES
    assert set(terminal["completed"]["S3"]["selected"]) == FAMILIES


def test_scored_cells_zero_everywhere(state, terminal, freeze):
    assert state["counters"]["budget_used"] == 0
    assert terminal["scored_cells_computed"] == 0
    assert freeze["budget"]["computed"] == 0


def test_denominators_zero_zero_everywhere(state, terminal, map_text):
    assert state["counters"]["published"] == 0
    assert state["counters"]["observed"] == 0
    assert terminal["counters"]["published_denominator"] == 0
    assert terminal["counters"]["observed_denominator"] == 0
    assert "counters 0/0" in map_text


def test_budget_zero_of_six_everywhere(state, terminal, freeze, map_text):
    assert state["counters"]["budget_planned"] == 6
    assert freeze["budget"]["planned_cells"] == 6
    assert terminal["counters"]["budget"] == "0/6"
    assert "0/6" in map_text


def test_s1_sealed_everywhere(terminal, freeze, map_text):
    assert terminal["s1_sealed"] is True
    assert freeze["s1_sealed"] is True
    assert "S1: sealed and untouched" in map_text


def test_workers_zero_everywhere(heartbeat, terminal, map_text):
    assert heartbeat["active_light_agents"] == 0
    assert heartbeat["heavy_workers"] == 0
    assert terminal["workers"]["owned_heavy_workers"] == 0
    assert terminal["workers"]["owned_pids_alive"] == 0
    assert "Owned workers: 0" in map_text


def test_next_action_is_data_authority_everywhere(state, terminal, map_text):
    assert "data authority" in state["next_safe_action"].lower()
    assert "data authority" in terminal["next_safe_action"].lower()
    assert "PIT data authority" in map_text


def test_event_log_append_only_has_reconciliation_row():
    rows = [json.loads(line)
            for line in (CTRL / "event_log.jsonl").read_text().splitlines() if line]
    events = [r["event"] for r in rows]
    assert events.count("TERMINAL_METADATA_RECONCILIATION") == 1
    # terminal verdict row still present from the original closeout
    assert "SPRINT_TERMINAL" in events


# --------------------------------------------------------------------------
# 4. data-authority packet stays provider-neutral and fail-closed
# --------------------------------------------------------------------------

REQUIRED_META_FIELDS = {
    "id", "area", "required_or_optional", "consuming_family_or_component",
    "pit_clock", "minimum_coverage", "rejection_condition",
    "evidence_needed_for_PASS", "synthetic_fixture_exists", "status",
}


def test_packet_has_all_requirement_areas(packet):
    ids = [r["id"] for r in packet["requirements"]]
    assert len(ids) == 19
    assert len(set(ids)) == 19
    assert ids[:3] == ["R01", "R02", "R03"]
    assert ids[-1] == "R19"


def test_every_requirement_record_complete_and_fail_closed(packet):
    for rec in packet["requirements"]:
        assert REQUIRED_META_FIELDS <= set(rec), rec["id"]
        assert rec["required_or_optional"] == "required"
        assert rec["status"] == "UNAVAILABLE_FAIL_CLOSED", rec["id"]
        assert rec["evidence_needed_for_PASS"]


def test_packet_names_both_frozen_families(packet):
    blob = json.dumps(packet["consumers"])
    assert "EQ_S2_A3_F1_PIT_RECON_FLOW" in blob
    assert "A5-S2-F1-LENDING-CONSTRAINT-PREMIUM" in blob


def test_packet_rules_forbid_purchase_and_inference(packet):
    blob = " ".join(packet["rules"]).lower()
    assert "no purchase" in blob
    assert "unavailable_fail_closed" in blob


def test_evaluation_template_unfilled_and_not_run(template):
    assert template["provider_identity"]["provider_name"] is None
    evals = template["per_requirement_evaluation"]
    assert len(evals) == 19
    assert all(e["verdict"] == "NOT_RUN" for e in evals.values())
    assert template["summary"]["data_authority_verdict"] == "UNAVAILABLE_FAIL_CLOSED"
    assert template["summary"]["not_run_count"] == 19


@pytest.mark.parametrize("name", [
    "requirements.json", "requirements.md",
    "provider_evaluation_template.json", "ingestion_acceptance_checklist.md",
])
def test_packet_artifacts_exist(name):
    p = DA / name
    assert p.is_file() and p.stat().st_size > 500, name
