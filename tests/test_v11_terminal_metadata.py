"""V11 terminal metadata reconciliation regression tests.

PLAN_crypto.md §5 R1: these tests pin the V11 terminal truth across state,
heartbeat, terminal report, family verdicts, reproduction reports and A7
audits. They fail on stale in-progress fields, wrong counters, S1-open claims
or a reversed performed/not-performed schema. Scientific artifacts must stay
byte-identical to the hashes frozen in v11r_reconciliation_intake.json.
"""

import hashlib
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTROL = REPO_ROOT / "research" / "control" / "v11_run"
AUDITS = REPO_ROOT / "research" / "audits" / "v11p" / "a7_terminal"

V11_TERMINAL_REMOTE_SHA = "df18f53dba30291065f9be157cae04bdcf15bf50"
AUDITED_SCIENCE_SHA = "85c14a77719beec5d16789c7dabdf02300173ce3"

IMMUTABLE_SCIENCE_HASHES = {
    "family_verdict_lot.json": "306852fdc3899a2a7021c8195320631326a23a97790cea91abbec3ae3987aa82",
    "family_verdict_illiq.json": "7bd459f1d9796645250fc312af7b603c9330631037a678b481e6415db2a8213b",
    "family_blocked_oilev.json": "c11bdacfd8354dae1d934c9c291e2cd5769eb0ae40c3caa34bab0ac8da244e4e",
    "reproduction_report_lot.json": "db35b325c0842f66432c6ca7c47261b208826e6074336ae2b477c3179afe8bc0",
    "reproduction_report_illiq.json": "328e671e9ec2fe6725e5c3ce0dc5519fa375000ccd0a66a186429ad90be2954a",
}


def _load(path: Path):
    return json.loads(path.read_text())


@pytest.fixture(scope="module")
def state():
    return _load(CONTROL / "state.json")


@pytest.fixture(scope="module")
def heartbeat():
    return _load(CONTROL / "heartbeat.json")


@pytest.fixture(scope="module")
def terminal():
    return _load(CONTROL / "terminal_report_v11.json")


@pytest.fixture(scope="module")
def intake():
    return _load(CONTROL / "v11r_reconciliation_intake.json")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --------------------------------------------------------------------------
# scientific immutability
# --------------------------------------------------------------------------


@pytest.mark.parametrize("fname", sorted(IMMUTABLE_SCIENCE_HASHES))
def test_scientific_artifacts_byte_identical(fname):
    path = CONTROL / fname
    assert path.exists(), f"immutable V11 artifact missing: {fname}"
    assert _sha256(path) == IMMUTABLE_SCIENCE_HASHES[fname], (
        f"{fname} changed during metadata reconciliation — scientific bytes "
        "are append-only evidence and must never be rewritten"
    )


def test_intake_pins_the_same_immutable_hashes(intake):
    pinned = intake["immutable_scientific_artifact_hashes_sha256"]
    for fname, digest in IMMUTABLE_SCIENCE_HASHES.items():
        key = f"research/control/v11_run/{fname}"
        assert pinned[key] == digest


# --------------------------------------------------------------------------
# terminal phase / verdict agreement
# --------------------------------------------------------------------------


def test_state_carries_terminal_phase_and_verdict(state):
    assert state["phase"] == "V11_TERMINAL_COMPLETE"
    assert state["verdict"] == "V11_TERMINAL_COMPLETE"
    assert "IN_PROGRESS" not in state["verdict"]
    assert state["sprint_verdict"].startswith("V11_REJECT_ALL")
    assert state["terminal_utc"] == "2026-09-03T09:08:04Z"


def test_state_reasons_are_terminal_not_p0_narrative(state):
    raw_reasons = json.dumps(state["verdict_reasons"])
    stale_fragments = [
        "A7-N novelty audit NOT completed",
        "D3 selection freeze NOT reached",
        "budget 0/12",
        "zero scored cells",
    ]
    for fragment in stale_fragments:
        assert fragment not in raw_reasons, (
            f"stale P0-era claim survived reconciliation: {fragment!r}"
        )
    joined = " ".join(state["verdict_reasons"])
    for required in [
        "V11_REJECT_ALL",
        "ALL_MATCH 33/33",
        "APPROVED, 0 FAIL",
        "125 published / 128 observed",
    ]:
        assert required in joined


def test_state_next_action_is_not_obsolete(state):
    nxt = state["next_thread_entry"]
    assert "dispatch A7-N" not in nxt
    assert "execute OI staging" not in nxt
    assert "then D3" not in nxt


# --------------------------------------------------------------------------
# heartbeat agreement
# --------------------------------------------------------------------------


def test_heartbeat_has_no_live_computation_claim(heartbeat):
    illiq = heartbeat["family_status"]["ILLIQ"]
    assert "computing" not in illiq.lower()
    assert "V11_FAMILY_REJECT" in illiq
    assert heartbeat["family_status"]["LOT"].startswith("3/3")


def test_heartbeat_has_no_archive_wait_claim(heartbeat):
    awaiting = heartbeat["awaiting"].lower()
    assert "absent from every mounted filesystem" not in awaiting
    assert "place the archive" not in awaiting
    assert awaiting.startswith("none")


def test_heartbeat_remote_tip_matches_pushed_terminal_sha(heartbeat):
    tip = heartbeat["remote_tip_orca_v11_integration"]
    assert tip == V11_TERMINAL_REMOTE_SHA
    strong_head = heartbeat["strong_host_status"]["head"]
    assert not strong_head.split(" ")[0] == tip or "superseded" in strong_head
    assert "==" not in strong_head or "superseded" in strong_head


def test_heartbeat_clock_is_superseded_not_counting_down(heartbeat):
    assert heartbeat["minutes_remaining"] is None
    assert heartbeat["clock_status"].startswith("SUPERSEDED")


def test_heartbeat_preserves_terminal_counters_and_seal(heartbeat):
    assert heartbeat["owned_workers"] == 0
    assert heartbeat["budget"].startswith("6/9")
    assert heartbeat["logical_totals"]["published"] == 125
    assert heartbeat["logical_totals"]["observed"] == 128
    assert heartbeat["sprint_verdict"] == "V11_REJECT_ALL"
    assert heartbeat["reproduction"].startswith("ALL_MATCH 33/33")
    assert heartbeat["families"]["LOT"].startswith("V11_FAMILY_REJECT")
    assert heartbeat["families"]["ILLIQ"].startswith("V11_FAMILY_REJECT")
    assert "BLOCKED_PRE_SCORE" in heartbeat["families"]["OILEV"]


# --------------------------------------------------------------------------
# terminal report agreement
# --------------------------------------------------------------------------


def test_terminal_report_distinguishes_science_metadata_remote_shas(terminal):
    heads = terminal["heads"]
    assert heads["audited_science_sha"] == AUDITED_SCIENCE_SHA
    assert heads["terminal_metadata_and_pushed_remote_sha"] == V11_TERMINAL_REMOTE_SHA
    assert (
        heads["audited_science_sha"] != heads["terminal_metadata_and_pushed_remote_sha"]
    )
    assert "integration_head" not in heads, (
        "conflated local-head field must not return; science vs metadata vs "
        "remote SHAs stay distinct"
    )


def test_terminal_report_marks_push_complete(terminal):
    pushed = terminal["boundaries"]["pushed"]
    assert pushed.startswith("COMPLETE")
    assert V11_TERMINAL_REMOTE_SHA in pushed
    assert not pushed.startswith("PENDING")


def test_terminal_report_next_action_not_obsolete(terminal):
    nxt = terminal["next_safe_action"]
    assert "push orca/v11-integration to origin (owner-authorized)" not in nxt


def test_terminal_report_boundaries_hold(terminal):
    b = terminal["boundaries"]
    assert b["s1_touched"] is False
    assert b["paper_testnet_live"] is False
    assert b["orders_placed"] is False
    assert b["main_merged"] is False
    assert b["history_rewritten"] is False
    assert b["worktrees_deleted"] is False


def test_terminal_report_workers_zero(terminal):
    assert terminal["workers"]["owned"] == 0


# --------------------------------------------------------------------------
# counters / budget / denominators agreement
# --------------------------------------------------------------------------


def test_denominators_agree_across_surfaces(state, heartbeat, terminal):
    logical_published = 125
    logical_observed = 128
    assert heartbeat["logical_totals"]["published"] == logical_published
    assert heartbeat["logical_totals"]["observed"] == logical_observed
    assert terminal["denominators"]["logical_published_total"] == logical_published
    assert terminal["denominators"]["logical_observed_total"] == logical_observed
    # heartbeat top-level counters are the P0-intake historical baselines
    assert (
        heartbeat["published_denominator"]
        == terminal["denominators"]["historical_published"]
        == 119
    )
    assert (
        heartbeat["observed_denominator"]
        == terminal["denominators"]["historical_observed"]
        == 120
    )


def test_budget_agrees_at_six_of_nine(state, heartbeat, terminal):
    assert terminal["budget"]["eligible_cells"] == 9
    assert terminal["budget"]["published_cells"] == 6
    assert terminal["budget"]["computed_eligible_cells"] == 6
    assert terminal["budget"]["def_slots_unused"] == 3
    assert terminal["budget"]["oilev_slots_blocked_pre_score"] == 3
    assert terminal["budget"]["disclosed_defective_computations"] == 2
    assert heartbeat["budget"].startswith("6/9")
    assert state["budget_final"]["computed_published"] == 6
    assert state["budget_final"]["eligible"] == 9


# --------------------------------------------------------------------------
# family verdicts and reproduction schema agreement
# --------------------------------------------------------------------------


def test_terminal_family_verdicts_match_family_artifacts(terminal):
    lot = _load(CONTROL / "family_verdict_lot.json")
    illiq = _load(CONTROL / "family_verdict_illiq.json")
    oilev = _load(CONTROL / "family_blocked_oilev.json")
    assert terminal["families"]["V11-SEED-LOTTERY-MAX-SKEW"]["verdict"] == lot["verdict"]
    assert terminal["families"]["A8-V11-ILLIQ-AMIHUD"]["verdict"] == illiq["verdict"]
    assert (
        terminal["families"]["A8-V11-OILEVER-DELEV"]["verdict"] == oilev["verdict"]
    )
    assert lot["verdict"] == "V11_FAMILY_REJECT"
    assert illiq["verdict"] == "V11_FAMILY_REJECT"
    assert oilev["verdict"].startswith("V11_FAMILY_BLOCKED_PRE_SCORE")


def test_family_anchor_metrics_match_terminal_report(terminal):
    lot = _load(CONTROL / "family_verdict_lot.json")["anchor_metrics"]
    illiq = _load(CONTROL / "family_verdict_illiq.json")["anchor_metrics"]
    lot_t = terminal["families"]["V11-SEED-LOTTERY-MAX-SKEW"]["anchor"]
    illiq_t = terminal["families"]["A8-V11-ILLIQ-AMIHUD"]["anchor"]
    for key in ("net_return_sum", "position_pf", "max_drawdown", "n_positions"):
        assert lot[key] == lot_t[key]
        assert illiq[key] == illiq_t[key]


def test_reproduction_performed_only_where_scored_cells_exist():
    """Performed/not-performed schema: families with scored cells have
    reproduction reports; the blocked family must never claim a performed
    reproduction."""
    lot = _load(CONTROL / "reproduction_report_lot.json")
    illiq = _load(CONTROL / "reproduction_report_illiq.json")
    assert not (CONTROL / "reproduction_report_oilev.json").exists()
    for report, cell_count in ((lot, 5), (illiq, 6)):
        assert report["schema"] == "v11_reproduction_report_v1"
        assert len(report["arms"]) == 3
        for arm in report["arms"]:
            assert arm["all_match"] is True
            assert len(arm["cells"]) == cell_count
            for cell in arm["cells"].values():
                assert cell["result_sha256_exec"] == cell["result_sha256_repro"]
                assert cell["norm_equal"] is True


def test_reproduction_totals_match_terminal_claim(terminal):
    lot = _load(CONTROL / "reproduction_report_lot.json")
    illiq = _load(CONTROL / "reproduction_report_illiq.json")
    total = sum(len(a["cells"]) for a in lot["arms"]) + sum(
        len(a["cells"]) for a in illiq["arms"]
    )
    assert total == 33
    assert terminal["reproduction"]["cells"] == total
    assert terminal["reproduction"]["status"] == "ALL_MATCH"


# --------------------------------------------------------------------------
# A7 audit agreement
# --------------------------------------------------------------------------


def test_a7_terminal_audits_approve_the_sprint_verdict(terminal):
    wave1 = _load(AUDITS / "a7_terminal_wave1.json")
    wave2 = _load(AUDITS / "a7_terminal_wave2.json")
    assert wave1["overall"] == "ALL_10_ITEMS_VERIFIED_0_FAIL"
    assert wave2["final_terminal_audit_verdict"] == "APPROVED"
    assert wave2["confirmed_sprint_verdict"] == terminal["sprint_verdict"]
    assert terminal["a7_terminal_audit"]["final_verdict"] == "APPROVED (0 FAIL)"
    assert terminal["a7_terminal_audit"]["wave1"].startswith("10/10 PASS")
    assert terminal["a7_terminal_audit"]["wave2"].startswith("APPROVED, 0 FAIL")


# --------------------------------------------------------------------------
# S1 / deployment seal
# --------------------------------------------------------------------------


def test_no_surface_claims_s1_or_deployment_activity(state, heartbeat, terminal):
    assert terminal["boundaries"]["s1_touched"] is False
    assert terminal["boundaries"]["paper_testnet_live"] is False
    assert terminal["boundaries"]["orders_placed"] is False
    for blob in (json.dumps(state), json.dumps(heartbeat)):
        assert "S1_OPEN" not in blob
        assert "s1_touched\": true" not in blob
        assert "enable_trading\": true" not in blob


# --------------------------------------------------------------------------
# append-only event log
# --------------------------------------------------------------------------


def test_event_log_is_append_only_and_carries_reconciliation_event():
    lines = (CONTROL / "event_log.jsonl").read_text().splitlines()
    rows = [json.loads(line) for line in lines if line.strip()]
    events = [row["event"] for row in rows]
    assert "V11_TERMINAL_REJECT_ALL_PUSH_AUTHORIZED" in events, (
        "pre-reconciliation terminal event row disappeared — event log is append-only"
    )
    assert events[-1] == "V11R_METADATA_RECONCILIATION_APPLIED"
    assert len(rows) >= 36


# --------------------------------------------------------------------------
# reconciliation provenance
# --------------------------------------------------------------------------


def test_reconciled_files_carry_provenance(state, heartbeat, terminal):
    for artifact in (state, heartbeat, terminal):
        assert artifact.get("reconciled_utc") == "2026-09-03T11:10:00Z"
        assert "PLAN_crypto" in artifact.get("reconciliation_note", "")
