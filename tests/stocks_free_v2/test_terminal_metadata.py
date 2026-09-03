"""V2R terminal-metadata regression tests (PLAN_stocks.md section 7 R1).

The STOCKS-FREE-V2 science is immutable; these tests pin the reconciled
metadata surfaces so a stale W1, a stale pending-audit suffix, a null
verdict, a phantom running cell, or an edited history file can never again
be shipped as the terminal state.
"""
import hashlib
import json
from pathlib import Path

RUN = Path("research/control/stocks_free_v2_run")
AUDITS = Path("research/audits/stocks_free_v2")

CANONICAL_W1 = "106378230abecbaefff4248eeb373794f1b73038"
STALE_W1 = "5046a87cea2e33be8c77ff35ed8302daeeff859c"
EFFECTIVE_VERDICT = "STOCKS_FREE_V1_REJECT_ALL"

# Byte-pins for preserved history (recorded in v2r_reconciliation_intake.json).
PRESERVED_SHA256 = {
    "terminal_report.json":
        "76bf2a66473472f40b6489d6d4fd848d3c1b15184123a7cc72408951d8d59ebe",
    "family_verdicts.json":
        "69325ae6640e4161b005204c8fb1399b1a598a81ddf766eb2710d77b68cf66bf",
    "family_verdicts_amendment.json":
        "c299bb47d8be0cea26b2f97f3f8e9f7c21e438418f2a49b3c1f14403ff83ee3f",
    "z9_reproduction.json":
        "adc195fd93361c94adb76f8499a8879a3770415d2e731ef51788dc0b39095206",
    "ledger.json":
        "83b9d3194474815b6931e7cf747a3051c5a287a539090d78c9208fa8be0a517d",
}
# The pre-reconciliation event log (15 rows); later rows may only be appended.
EVENT_LOG_PREFIX_SHA256 = (
    "f886d73151d1e195674bfa18edc4c30129efb86cfdeba69f19c062ecb7676b7b")


def _load(name):
    return json.loads((RUN / name).read_text())


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def test_state_carries_canonical_w1():
    state = _load("state.json")
    assert state["W1"] == CANONICAL_W1
    assert STALE_W1 not in state["W1"]
    supersession = state["W1_supersession"]
    assert supersession["from"] == STALE_W1
    assert CANONICAL_W1 in supersession["reason"]


def test_state_has_no_pending_reaudit_status():
    state = _load("state.json")
    fd2 = state["gates"]["FD2_RAW_ADJUSTED_CA_PASS"]
    assert "PENDING" not in fd2
    assert fd2 == "PASS_AMENDED_V2_SPLIT_FACTORS"
    assert "PASS_AMENDED_V2_SPLIT_FACTORS_A7_REAUDIT_PENDING" == (
        state["gate_supersessions"]["FD2_RAW_ADJUSTED_CA_PASS"]["from"])


def test_effective_verdict_is_unambiguous_everywhere():
    for name in ("state.json", "heartbeat.json",
                 "terminal_effective_verdict.json"):
        doc = _load(name)
        verdict = doc.get("verdict") or doc.get("effective_sprint_verdict")
        assert verdict == EFFECTIVE_VERDICT, name


def test_effective_verdict_artifact_pins_history():
    eff = _load("terminal_effective_verdict.json")
    chain = eff["authority_chain"]
    assert chain["original_terminal_report"]["historical_label"] == (
        "STOCKS_FREE_V1_INCOMPLETE_NOT_PROMOTABLE")
    assert chain["original_terminal_report"]["status"] == (
        "PRESERVED_AS_HISTORY")
    assert chain["family_verdicts_amendment"]["status"] == (
        "AUTHORITATIVE_AMENDMENT")
    assert eff["effective_family_verdicts"] == {
        "A4_XSEC_ETF_RELATIVE_MOMENTUM": "STOCKS_FREE_V1_FAMILY_REJECT",
        "A5-SFV2-TREND-DEFENSIVE": "STOCKS_FREE_V1_FAMILY_REJECT",
    }
    assert eff["canonical_w1"] == CANONICAL_W1
    assert eff["no_stage_a_survivors"] and eff["not_promotable"]


def test_heartbeat_has_no_null_verdict_and_no_running_cell():
    hb = _load("heartbeat.json")
    assert hb["verdict"] == EFFECTIVE_VERDICT
    assert hb["current_cell"] is None
    assert hb["current_cell_running"] is False
    assert hb["heavy_workers"] == 0
    assert hb["active_light_agents"] == 0
    assert hb["completed_cells"] == 6


def test_counters_remain_six_over_six():
    state = _load("state.json")
    assert state["counters"] == {
        "published": 6, "observed": 6, "budget_used": 6, "budget_planned": 6}
    term = _load("terminal_report.json")
    assert term["denominators"] == {"observed": 6, "published": 6}
    assert term["budget"]["computed"] == term["budget"]["published"] == 6


def test_s1_sealed_and_workers_zero():
    for name in ("state.json", "heartbeat.json",
                 "terminal_effective_verdict.json"):
        doc = _load(name)
        blob = json.dumps(doc)
        assert "SEALED" in blob, name
    eff = _load("terminal_effective_verdict.json")
    assert eff["workers"] == 0
    assert eff["s1"] == "SEALED_UNTOUCHED"


def test_history_files_are_byte_identical():
    for name, expected in PRESERVED_SHA256.items():
        assert _sha256(RUN / name) == expected, name


def test_event_log_is_append_only_with_reconciliation_row():
    lines = (RUN / "event_log.jsonl").read_text().splitlines(keepends=True)
    assert len(lines) >= 16
    prefix = "".join(lines[:15])
    assert hashlib.sha256(prefix.encode()).hexdigest() == (
        EVENT_LOG_PREFIX_SHA256)
    reconciliation = json.loads(lines[15])
    assert reconciliation["event"] == "V2R_METADATA_RECONCILIATION"
    assert reconciliation["detail"]["prior_rows_edited"] == 0


def test_z9_reproduction_all_match():
    z9 = _load("z9_reproduction.json")
    assert z9["all_match"] is True
    assert len(z9["cells"]) == 6
    assert all(c["match"] for c in z9["cells"].values())


def test_map_and_continue_agree():
    map_text = Path("research/wayfinder/MAP.md").read_text()
    assert EFFECTIVE_VERDICT in map_text
    assert CANONICAL_W1 in map_text
    cont = Path("CONTINUE.md").read_text()
    assert EFFECTIVE_VERDICT in cont
    assert CANONICAL_W1 in cont
    assert "SEALED_UNTOUCHED" in cont


def test_terminal_a7_audit_present():
    audit = AUDITS / "z9_a7_terminal" / "AUDIT_REPORT.md"
    text = audit.read_text()
    assert "STRONGEST_CLAIM_IS_REJECT_ALL" in text


def test_reconciliation_intake_records_intake_hashes():
    intake = _load("v2r_reconciliation_intake.json")
    assert intake["v2_terminal"]["head"] == (
        "efb89a6aa99e130440c00830903990878d607dcb")
    assert intake["v2_terminal"]["canonical_w1"] == CANONICAL_W1
    for name, expected in PRESERVED_SHA256.items():
        assert intake["preserved_bytes_sha256"][name] == expected
