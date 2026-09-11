"""V3 authority registry tests (plan section 7A.2 + PA1 contract)."""

import pytest

from research.platform_v3.authority import (
    AuthorityError,
    AuthorityRegistry,
    IllegalTransition,
    NotInTargetSet,
)


def _grant_path(reg, series="S1:form4-xml-substrate", channel="edgar"):
    reg.register(series, source="sec-edgar", channel=channel)
    reg.transition(series, "INGESTED")
    reg.transition(series, "VERIFIED")
    reg.evidence(series,
                 pit_verdict="PASS_PIT_EVIDENCED",
                 license_status="AUTHORIZED",
                 entitlement_status="AUTHORIZED",
                 canary_probe={channel: "PASS"},
                 cads_pins=["a" * 64])


def test_full_grant_path(tmp_path):
    path = str(tmp_path / "authority.jsonl")
    reg = AuthorityRegistry(path)
    _grant_path(reg)
    assert reg.adjudicate("S1:form4-xml-substrate", granted_by="A1",
                          granted_at="2026-09-11T00:00:00Z") == "GRANTED"
    assert reg.verdict("S1:form4-xml-substrate") == "GRANTED"


def test_blocked_when_canary_missing(tmp_path):
    path = str(tmp_path / "authority.jsonl")
    reg = AuthorityRegistry(path)
    reg.register("S1:form4-stream", source="sec-edgar", channel="edgar")
    reg.transition("S1:form4-stream", "INGESTED")
    reg.transition("S1:form4-stream", "VERIFIED")
    reg.evidence("S1:form4-stream",
                 pit_verdict="PASS_PIT_EVIDENCED",
                 license_status="AUTHORIZED",
                 entitlement_status="AUTHORIZED",
                 canary_probe={},          # NO probe for the channel
                 cads_pins=["b" * 64])
    assert reg.adjudicate("S1:form4-stream", granted_by="A1",
                          granted_at="now").startswith("BLOCKED")
    assert reg.verdict("S1:form4-stream").startswith("BLOCKED")


def test_retrospective_only_is_blocked(tmp_path):
    path = str(tmp_path / "authority.jsonl")
    reg = AuthorityRegistry(path)
    reg.register("S2:fred-keyed-vintage-classes", source="fred",
                 channel="fred-api")
    reg.transition("S2:fred-keyed-vintage-classes", "INGESTED")
    reg.transition("S2:fred-keyed-vintage-classes", "VERIFIED")
    reg.evidence("S2:fred-keyed-vintage-classes",
                 pit_verdict="RETROSPECTIVE_ONLY",   # not PIT-evidenced
                 license_status="AUTHORIZED",
                 entitlement_status="AUTHORIZED",
                 canary_probe={"fred-api": "PASS"},
                 cads_pins=["c" * 64])
    assert reg.adjudicate("S2:fred-keyed-vintage-classes", granted_by="A1",
                          granted_at="now").startswith("BLOCKED")


def test_no_backward_transitions(tmp_path):
    reg = AuthorityRegistry(str(tmp_path / "a.jsonl"))
    reg.register("S4:binance-daily-h1-panels", source="binance-vision",
                 channel="binance-vision")
    reg.transition("S4:binance-daily-h1-panels", "INGESTED")
    with pytest.raises(IllegalTransition):
        reg.transition("S4:binance-daily-h1-panels", "REGISTERED")


def test_blocked_is_terminal(tmp_path):
    reg = AuthorityRegistry(str(tmp_path / "a.jsonl"))
    reg.register("S4:binance-open-interest", source="binance-vision",
                 channel="binance-vision")
    reg.transition("S4:binance-open-interest", "BLOCKED")
    with pytest.raises(IllegalTransition):
        reg.transition("S4:binance-open-interest", "VERIFIED")
    with pytest.raises(IllegalTransition):
        reg.transition("S4:binance-open-interest", "GRANTED")


def test_retry_is_new_attempt_record_not_rollback(tmp_path):
    path = str(tmp_path / "a.jsonl")
    reg = AuthorityRegistry(path)
    reg.register("S3:forex-print-calendars", source="official",
                 channel="bis")
    reg.transition("S3:forex-print-calendars", "INGESTED", attempt="t1")
    # t1 failed -> a NEW registration attempt is illegal (duplicate
    # REGISTER), and rollback to REGISTERED is illegal; the forward-only
    # machine forces either BLOCKED or continuation.
    with pytest.raises(IllegalTransition):
        reg.transition("S3:forex-print-calendars", "REGISTERED",
                       attempt="t2")


def test_out_of_target_set_defaults_blocked(tmp_path):
    reg = AuthorityRegistry(str(tmp_path / "a.jsonl"))
    with pytest.raises(NotInTargetSet):
        reg.register("X:unplanned-series", source="anywhere",
                     channel="some-channel")
    # and the default verdict for unknown series is BLOCKED_DATA
    assert reg.verdict("X:unplanned-series").startswith("BLOCKED_DATA")


def test_journal_replay_consistent(tmp_path):
    path = str(tmp_path / "a.jsonl")
    reg = AuthorityRegistry(path)
    _grant_path(reg)
    reg.adjudicate("S1:form4-xml-substrate", granted_by="A1",
                   granted_at="now")
    replayed = AuthorityRegistry(path)
    assert replayed.verdict("S1:form4-xml-substrate") == "GRANTED"


def test_unknown_journal_event_is_drift(tmp_path):
    path = str(tmp_path / "a.jsonl")
    reg = AuthorityRegistry(path)
    reg.register("S1:eodhd-corp-actions", source="eodhd", channel="eodhd")
    with open(path, "a") as fh:
        fh.write('{"event": "MAGIC", "series_id": "S1:eodhd-corp-actions"}\n')
    with pytest.raises(AuthorityError):
        AuthorityRegistry(path)


def test_duplicate_register_rejected(tmp_path):
    path = str(tmp_path / "a.jsonl")
    reg = AuthorityRegistry(path)
    reg.register("S1:form4-xml-substrate", source="s", channel="c")
    with open(path, "a") as fh:
        fh.write('{"event": "REGISTER", "series_id": '
                 '"S1:form4-xml-substrate", "source": "s", '
                 '"channel": "c"}\n')
    with pytest.raises(AuthorityError):
        AuthorityRegistry(path)
