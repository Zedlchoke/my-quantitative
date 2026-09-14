"""Event id determinism, atomic append, idempotency, crash detection (G5)."""

import json
import os

import pytest

from research.shadow_v1 import events, ledger
from research.shadow_v1.events import (
    build_data_blocked_event,
    compute_event_id,
    validate_event_record,
)

FAM = "ILLIQ-AMIHUD-28D-W"
ARM = "ILLIQ-AMIHUD-28D-W"
TS = "2026-01-05T00:00:00Z"


def _sample_record(family_id=FAM, ts=TS):
    rec = build_data_blocked_event(
        family_id=family_id,
        arm_id=ARM,
        scheduled_decision_utc=ts,
        observed_at_utc=ts,
        feature_cutoff_utc=ts,
        code_freeze_sha="deadbeef",
        config_digest="cafe",
        cost_regime_digest="ab524d0ef974ef3ee23236ec89ba1df50ba52c37d5de973429349291aef44d65",
        blocked_reason="late bars",
    )
    validate_event_record(rec)
    return rec


def test_event_id_deterministic_and_format():
    a = compute_event_id(FAM, ARM, TS)
    b = compute_event_id(FAM, ARM, TS)
    assert a == b
    assert len(a) == 32
    assert a == a.lower()
    int(a, 16)  # lowercase hex
    import hashlib

    expected = hashlib.sha256(
        f"PROSPECTIVE-SHADOW-V1|{FAM}|{ARM}|{TS}".encode()
    ).hexdigest()[:32]
    assert a == expected


def test_event_id_changes_with_inputs():
    base = compute_event_id(FAM, ARM, TS)
    assert compute_event_id("XSECT-FUND-CARRY-7D", ARM, TS) != base
    assert compute_event_id(FAM, ARM, "2026-01-12T00:00:00Z") != base
    assert compute_event_id(FAM, "other-arm", TS) != base


def test_append_and_read_back(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    rec = _sample_record()
    assert ledger.append_event(path, rec) == "appended"
    raw = open(path, "rb").read()
    assert raw.endswith(b"\n")
    assert json.loads(raw.decode())["event_id"] == rec["event_id"]
    got = ledger.scan_events(path)
    assert len(got) == 1 and got[0]["event_id"] == rec["event_id"]
    import hashlib

    assert ledger.ledger_digest(path) == hashlib.sha256(raw).hexdigest()


def test_duplicate_append_skipped_idempotently(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    rec = _sample_record()
    assert ledger.append_event(path, rec) == "appended"
    size_before = os.path.getsize(path)
    digest_before = ledger.ledger_digest(path)
    assert ledger.append_event(path, dict(rec)) == "skipped_existing"
    assert os.path.getsize(path) == size_before
    assert ledger.ledger_digest(path) == digest_before
    assert len(ledger.scan_events(path)) == 1


def test_restart_rerun_byte_identical_zero_duplicates(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    batch = [
        _sample_record(ts="2026-01-05T00:00:00Z"),
        _sample_record(ts="2026-01-12T00:00:00Z"),
        _sample_record(ts="2026-01-19T00:00:00Z"),
    ]
    for rec in batch:
        assert ledger.append_event(path, rec) == "appended"
    digest = ledger.ledger_digest(path)
    size = os.path.getsize(path)
    # simulated second worker run over the same window
    for rec in batch:
        assert ledger.append_event(path, dict(rec)) == "skipped_existing"
    assert ledger.ledger_digest(path) == digest
    assert os.path.getsize(path) == size
    ids = ledger.event_ids(path)
    assert len(ids) == 3
    assert len(ledger.scan_events(path)) == 3


def test_crash_partial_line_detected_and_never_truncated(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    rec = _sample_record()
    ledger.append_event(path, rec)
    good_bytes = open(path, "rb").read()
    # simulate a crash mid-append: a torn trailing line without newline
    with open(path, "ab") as fh:
        fh.write(b'{"event_id": "torn", "partial": tru')
    with pytest.raises(ledger.LedgerCorruptError):
        ledger.scan_events(path)
    with pytest.raises(ledger.LedgerCorruptError):
        ledger.event_ids(path)
    # refusal must not modify bytes
    assert open(path, "rb").read() == good_bytes + b'{"event_id": "torn", "partial": tru'
    # and appends are refused too (scan precedes any dedupe read)
    with pytest.raises(ledger.LedgerCorruptError):
        ledger.append_event(path, _sample_record(ts="2026-01-26T00:00:00Z"))


def test_garbled_json_line_detected(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    with open(path, "wb") as fh:
        fh.write(b'{"event_id": "ok"}\n')
        fh.write(b"not json at all\n")
    with pytest.raises(ledger.LedgerCorruptError):
        ledger.scan_events(path)


def test_append_requires_event_id(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    with pytest.raises(ledger.LedgerError):
        ledger.append_event(path, {"no": "id"})


def test_event_contract_rejects_unknown_or_missing_fields():
    rec = _sample_record()
    bad_missing = {k: v for k, v in rec.items() if k != "equity"}
    with pytest.raises(events.EventContractError):
        validate_event_record(bad_missing)
    bad_extra = dict(rec)
    bad_extra["extra_field"] = 1
    with pytest.raises(events.EventContractError):
        validate_event_record(bad_extra)
    bad_id = dict(rec)
    bad_id["event_id"] = "0" * 32
    with pytest.raises(events.EventContractError):
        validate_event_record(bad_id)
    bad_action = dict(rec)
    bad_action["no_order_proof"] = {"emitted_action_types": ["PLACE_ORDER"]}
    with pytest.raises(events.EventContractError):
        validate_event_record(bad_action)
