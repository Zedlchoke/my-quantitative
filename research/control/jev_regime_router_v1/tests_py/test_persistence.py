"""Persistence state machine: hand-computed transition table (golden)."""

from __future__ import annotations

import pytest

from jrv1.persistence import (
    UNKNOWN,
    PersistedBar,
    PersistenceState,
    raw_from_response,
    run_persistence,
    step,
)

P = {"min_confidence": 0.5, "min_margin": 0.2, "confirm_bars": 2, "min_dwell": 6, "cooldown": 3}
U = "UPTREND"
D = "DOWNTREND"


def E(label):
    return {"label": label, "eligible": True}


def X():
    return {"label": UNKNOWN, "eligible": False}  # error / ineligible candidate


def feed(stream):
    return run_persistence(stream, P)


def test_initial_state_unknown():
    out = feed([])
    assert out == []


def test_unknown_candidate_bars_accrue_dwell_and_never_switch():
    out = feed([X()] * 20)
    assert all(p.persisted == UNKNOWN for p in out)
    assert out[-1].bars_in_current == 20


def test_first_switch_needs_confirm_and_dwell():
    stream = [X()] * 6 + [E(U), E(U)]
    out = feed(stream)
    # bars 0-5: dwell 1..6; bar6: streak 1 (dwell 6 but confirm 1<2); bar7: streak 2 -> SWITCH
    assert [p.persisted for p in out[:7]] == [UNKNOWN] * 7
    assert out[6].persisted == UNKNOWN
    assert out[7].persisted == U
    assert out[7].switched is True
    assert out[7].bars_in_current == 0


def test_confirm_without_dwell_no_switch():
    stream = [E(U), E(U)] + [X()] * 10
    out = feed(stream)
    # bar1: streak 2 but dwell=1 < 6 -> no switch; state stays UNKNOWN forever here
    assert out[1].persisted == UNKNOWN
    assert all(p.persisted == UNKNOWN for p in out)


def test_streak_reset_on_interruption():
    stream = [X()] * 6 + [E(U), X(), E(U)]
    out = feed(stream)
    # bar6 streak1; bar7 UNKNOWN resets streak; bar8 streak1 -> no switch
    assert out[8].persisted == UNKNOWN
    assert out[8].bars_in_current == 9


def test_flap_after_initial_dwell_switches_alternately():
    stream = [E(U), E(U), E(D), E(D)] * 5
    out = feed(stream)
    # hand table: dwell accrues in UNKNOWN (bars 0..6 -> 7); bar7 D confirms
    # with dwell 7 >= 6 -> switch; U cooled at 8,9 (cooldown 3 from bar7);
    # U re-confirms at bars 16,17 with dwell 9 -> switch at 17
    assert out[7].persisted == D and out[7].switched
    assert out[8].persisted == D and out[8].raw_label == U  # cooled: no switch
    assert out[9].persisted == D
    assert out[12].persisted == D and out[13].persisted == D  # dwell still short
    assert out[16].persisted == D
    assert out[17].persisted == U and out[17].switched
    assert out[18].persisted == U


def test_cooldown_bars_failed_candidates():
    stream = [X()] * 6 + [E(U), E(U)] + [E(D)] * 5
    out = feed(stream)
    # switch to U at bar7; DOWN set to expire at bar 7+3=10 -> barred 8,9,10
    # (raw label stays DOWNTREND but candidacy is refused by cooldown)
    assert out[7].switched
    assert out[8].persisted == U and out[8].raw_label == D
    assert out[9].persisted == U and out[9].raw_label == D
    assert out[10].persisted == U and out[10].raw_label == D
    assert out[10].eligible is True  # eligible raw, but cooled -> no candidacy
    # bar11: cooldown expired -> DOWN streak 1 (needs confirm 2, no switch yet)
    assert out[11].raw_label == D and out[11].eligible is True
    assert out[11].persisted == U


def test_switch_back_after_dwell_and_confirm():
    stream = [X()] * 6 + [E(U)] * 10 + [E(D)] * 3
    out = feed(stream)
    assert out[7].persisted == U
    # U bars 8..15 accrue dwell; D eligible again at bar16 (cooldown from bar7
    # expired), streak at 16,17 -> switch to D at bar17
    assert out[15].persisted == U
    assert out[16].persisted == U and out[16].raw_label == D
    assert out[17].persisted == D
    assert out[17].switched is True
    assert out[18].persisted == D and not out[18].switched


def test_raw_equal_current_accrues_dwell_and_resets_streak():
    stream = [X()] * 6 + [E(U)] * 4
    out = feed(stream)
    assert out[7].persisted == U
    assert out[8].raw_label == U
    assert out[8].bars_in_current == 1
    assert out[9].bars_in_current == 2


def test_error_stream_never_switches():
    out = feed([X()] * 50)
    assert all(p.persisted == UNKNOWN for p in out)


def test_raw_from_response_eligibility():
    probs = {"ACCUMULATION": 0.1, "UPTREND": 0.55, "DISTRIBUTION": 0.05, "DOWNTREND": 0.05, "TRANSITION_UNKNOWN": 0.25}
    resp = {"status": "OK", "regime": U, "probabilities": probs, "confidence": 0.6}
    raw, eligible = raw_from_response(resp, P)
    assert raw == U and eligible is True
    # confidence below floor -> ineligible
    resp2 = dict(resp, confidence=0.4)
    raw2, eligible2 = raw_from_response(resp2, P)
    assert (raw2, eligible2) == (UNKNOWN, False)
    # margin below floor -> ineligible
    probs3 = dict(probs, UPTREND=0.45, TRANSITION_UNKNOWN=0.35)
    resp3 = {"status": "OK", "regime": U, "probabilities": probs3, "confidence": 0.6}
    assert raw_from_response(resp3, P)[1] is False
    # error statuses -> ineligible
    for st in ("TIMEOUT", "PROVIDER_ERROR", "SCHEMA_ERROR"):
        assert raw_from_response({"status": st}, P) == (UNKNOWN, False)
    assert raw_from_response(None, P) == (UNKNOWN, False)


def test_unknown_regime_label_cannot_be_candidate():
    resp = {"status": "OK", "regime": UNKNOWN,
            "probabilities": {"ACCUMULATION": 0.05, "UPTREND": 0.05, "DISTRIBUTION": 0.05,
                              "DOWNTREND": 0.05, "TRANSITION_UNKNOWN": 0.80},
            "confidence": 0.9}
    raw, eligible = raw_from_response(resp, P)
    assert (raw, eligible) == (UNKNOWN, False)
