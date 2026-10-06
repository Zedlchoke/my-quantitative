"""test_expwitch_stub — the EXPWITCH-NQ leg is DEAD-AT-GATE: any identity
request refuses with code EXPWITCH_DEAD_AT_GATE (SPEC_NQ.md s.8.1; RC-6.3;
P5-NQ5). No adapter, no fixtures, no IDs exist for this leg."""
from __future__ import annotations

import pytest

from expwitch_refusal import (EXPWITCH_DEAD_AT_GATE, ExpwitchDeadAtGate,
                              ExpwitchStub, request_expwitch,
                              request_expwitch_identity)


def test_any_identity_request_refuses():
    with pytest.raises(ExpwitchDeadAtGate) as ei:
        request_expwitch_identity(identity_id="FBNQ1-F5-CONT-UP-D0-S2")
    assert ei.value.code == EXPWITCH_DEAD_AT_GATE
    rec = ei.value.record()
    assert rec["code"] == EXPWITCH_DEAD_AT_GATE
    assert rec["leg"] == "EXPWITCH-NQ"
    assert "P5-NQ5" in rec["owner_slot"]
    assert any("35/66" in b for b in rec["basis"]), "F5-K6 part (ii) basis must be cited"


def test_request_with_any_and_no_args_refuses():
    with pytest.raises(ExpwitchDeadAtGate):
        request_expwitch_identity()
    with pytest.raises(ExpwitchDeadAtGate):
        request_expwitch_identity(foo="bar", identity_id="EXPWITCH-ANYTHING")


def test_non_raising_twin_returns_record():
    rec = request_expwitch(identity_id="FBNQ1-F5-REV-DN-D30-S2")
    assert rec["code"] == EXPWITCH_DEAD_AT_GATE
    assert rec["disposition"].startswith("DEAD-AT-GATE")
    assert "re-litigated" in rec["disposition"].lower()
    assert any("NQ-D" in o for o in rec["options_blocked"])


def test_stub_object_refuses_on_every_surface():
    stub = ExpwitchStub()
    for call in (lambda: stub.build_observables({}),
                 lambda: stub.signal("x"),
                 lambda: stub.order_intent("y"),
                 lambda: stub.apply_exclusions({})):
        with pytest.raises(ExpwitchDeadAtGate) as ei:
            call()
        assert ei.value.code == EXPWITCH_DEAD_AT_GATE
    assert stub.dead_at_gate is True
    assert stub.refusal_record()["code"] == EXPWITCH_DEAD_AT_GATE


def test_refusal_is_not_convertible_to_pass():
    """The refusal record must never carry a PASS-shaped verdict field."""
    rec = request_expwitch()
    assert "verdict" not in rec
    assert "pass" not in rec
    assert "note" in rec and "gate pass" in rec["note"]
