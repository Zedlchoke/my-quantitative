"""Safety layer: code-owned UNKNOWN triggers + consistency matrix + persistence.

The 2x3x4x3 consistency matrix (structure x direction x phase x
prior_direction = 72 combinations) is verified against an INDEPENDENT
hand-computed expectation table built directly from the freeze's
consistency_law text — never by calling the implementation.
"""

from __future__ import annotations

import pytest

from jrv2.safety import (
    UNKNOWN,
    PersistedBar,
    PersistenceState,
    effective_from_response,
    evaluate_consistency,
    expected_phase,
    persisted_labels,
    run_persistence,
    step,
)

P = {"min_confidence": 0.5, "min_margin": 0.2, "confirm_bars": 2, "min_dwell": 6, "cooldown": 3}
U = "UPTREND"
D = "DOWNTREND"

STRUCTURES = ("TREND", "RANGE")
DIRECTIONS = ("UP", "DOWN", "NEUTRAL")
PHASES = ("ACCUMULATION", "UPTREND", "DISTRIBUTION", "DOWNTREND")
PRIORS = ("UP", "DOWN", "NEUTRAL")


def _independent_expected(structure, direction, phase, prior):
    """Independent re-derivation of the freeze consistency_law, verbatim
    from question_contract.json (test authority — NOT the implementation)."""
    rules = [
        ("TREND", "UP", "UPTREND", None),
        ("TREND", "DOWN", "DOWNTREND", None),
        ("RANGE", "NEUTRAL", "ACCUMULATION", "DOWN"),
        ("RANGE", "NEUTRAL", "DISTRIBUTION", "UP"),
    ]
    for s, d, ph, pd in rules:
        if s == structure and d == direction and ph == phase:
            if pd is None or pd == prior:
                return True
    return False


# ---------------------------------------------------------------------------
# full 2x3x4x3 matrix (72 combos)
# ---------------------------------------------------------------------------


def test_full_consistency_matrix_72_combos():
    n_ok = 0
    for s in STRUCTURES:
        for d in DIRECTIONS:
            for ph in PHASES:
                for pd in PRIORS:
                    ok, reason = evaluate_consistency(s, d, ph, pd)
                    want = _independent_expected(s, d, ph, pd)
                    assert ok == want, (s, d, ph, pd, reason, want)
                    if ok:
                        n_ok += 1
    # exactly 4 consistent rows: TREND+UP+UPTREND(*3 priors),
    # TREND+DOWN+DOWNTREND(*3), RANGE+NEUTRAL+ACC(prior DOWN),
    # RANGE+NEUTRAL+DIST(prior UP)
    assert n_ok == 3 + 3 + 1 + 1


def test_each_contradiction_pattern_fires_independently():
    # TREND + NEUTRAL
    assert not evaluate_consistency("TREND", "NEUTRAL", "UPTREND", "UP")[0]
    assert evaluate_consistency("TREND", "NEUTRAL", "UPTREND", "UP")[1] == "contradiction_structure_direction_prior"
    # RANGE + UP
    assert not evaluate_consistency("RANGE", "UP", "UPTREND", "UP")[0]
    # RANGE + DOWN
    assert not evaluate_consistency("RANGE", "DOWN", "DOWNTREND", "DOWN")[0]
    # RANGE + NEUTRAL + prior NEUTRAL
    assert not evaluate_consistency("RANGE", "NEUTRAL", "ACCUMULATION", "NEUTRAL")[0]
    # phase disagreeing with structure x direction
    assert not evaluate_consistency("TREND", "UP", "DOWNTREND", "UP")[0]
    assert evaluate_consistency("TREND", "UP", "DOWNTREND", "UP")[1] == "phase_disagrees_with_structure_direction"
    # phase ACCUMULATION with prior UP (RANGE+NEUTRAL+prior UP expects DISTRIBUTION)
    assert not evaluate_consistency("RANGE", "NEUTRAL", "ACCUMULATION", "UP")[0]
    # phase DISTRIBUTION with prior DOWN
    assert not evaluate_consistency("RANGE", "NEUTRAL", "DISTRIBUTION", "DOWN")[0]
    # out-of-schema inputs
    assert not evaluate_consistency("TRENDISH", "UP", "UPTREND", "UP")[0]
    assert not evaluate_consistency("TREND", "SIDEWAYS", "UPTREND", "UP")[0]
    assert not evaluate_consistency("TREND", "UP", "TRANSITION_UNKNOWN", "UP")[0]


def test_prior_none_treated_as_neutral():
    # 'none' prior + RANGE + NEUTRAL -> contradiction (conservative start)
    ok, _ = evaluate_consistency("RANGE", "NEUTRAL", "ACCUMULATION", "none")
    assert not ok


def _resp(phase="UPTREND", structure="TREND", direction="UP", prior="UP",
          conf=0.8, top=0.6, second=0.2, status="OK", usage=True, model=None):
    probs = {"ACCUMULATION": 0.05, "UPTREND": 0.05, "DISTRIBUTION": 0.05, "DOWNTREND": 0.05}
    probs[phase] = top
    rest = [p for p in probs if p != phase]
    probs[rest[0]] = second
    rem = 0.90 - top - second  # remaining mass on rest[1]; rest[2] keeps 0.05
    probs[rest[1]] = 0.05 + rem
    return {
        "status": status,
        "answers": {
            "structure": {"choice": structure, "probabilities": {"TREND": 0.7, "RANGE": 0.3}, "confidence": conf},
            "direction": {"choice": direction, "probabilities": {"UP": 0.7, "DOWN": 0.15, "NEUTRAL": 0.15}, "confidence": conf},
            "phase": {"choice": phase, "probabilities": probs, "confidence": conf},
        },
        "prior_direction": prior,
        "usage": {"input_tokens": 10, "output_tokens": 2} if usage else None,
        "model": model,
    }


def test_effective_ok_path():
    label, eligible, reason = effective_from_response(_resp(), P)
    assert (label, eligible, reason) == ("UPTREND", True, "ok")


def test_code_owned_unknown_low_confidence():
    label, eligible, reason = effective_from_response(_resp(conf=0.49), P)
    assert (label, eligible) == (UNKNOWN, False)
    assert reason == "low_confidence"
    # exactly at the threshold passes
    label2, eligible2, reason2 = effective_from_response(_resp(conf=0.50, top=0.60, second=0.30), P)
    assert eligible2 is True and reason2 == "ok"


def test_code_owned_unknown_low_margin():
    label, eligible, reason = effective_from_response(_resp(top=0.55, second=0.36), P)
    assert (label, eligible) == (UNKNOWN, False)
    assert reason == "low_margin"
    # exactly at the threshold passes (margin exactly 0.20)
    _, eligible2, reason2 = effective_from_response(_resp(top=0.55, second=0.35), P)
    assert eligible2 is True and reason2 == "ok"


def test_code_owned_unknown_each_contradiction_pattern():
    for kw in (
        {"structure": "RANGE"},                       # RANGE+UP contradiction
        {"direction": "NEUTRAL"},                     # TREND+NEUTRAL
        {"phase": "ACCUMULATION"},                    # phase mismatch + prior rule
        {"structure": "RANGE", "direction": "NEUTRAL", "phase": "ACCUMULATION", "prior": "NEUTRAL"},
        # RANGE+NEUTRAL+prior NEUTRAL -> contradiction
    ):
        resp = _resp(**kw)
        label, eligible, reason = effective_from_response(resp, P)
        assert (label, eligible) == (UNKNOWN, False), kw
        assert reason.startswith(("contradiction", "phase_")), kw


def test_code_owned_unknown_provider_and_schema_failures():
    for resp in (None, {"status": "TIMEOUT"}, {"status": "PROVIDER_ERROR"},
                 {"status": "SCHEMA_ERROR"}, {"status": "LOCAL_INVALID"}):
        label, eligible, reason = effective_from_response(resp, P)
        assert (label, eligible) == (UNKNOWN, False)
    # missing usage already coerced to SCHEMA_ERROR upstream; a non-OK status
    # with phase data still abstains
    label, _, _ = effective_from_response(_resp(status="TIMEOUT"), P)
    assert label == UNKNOWN


def test_effective_missing_phase_block():
    resp = {"status": "OK", "answers": {}, "usage": {"input_tokens": 1, "output_tokens": 1}}
    label, eligible, reason = effective_from_response(resp, P)
    assert (label, eligible) == (UNKNOWN, False)
    assert reason == "phase_not_in_schema"


# ---------------------------------------------------------------------------
# persistence machine (V1 golden table, carried over verbatim)
# ---------------------------------------------------------------------------


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
    assert out[1].persisted == UNKNOWN
    assert all(p.persisted == UNKNOWN for p in out)


def test_streak_reset_on_interruption():
    stream = [X()] * 6 + [E(U), X(), E(U)]
    out = feed(stream)
    assert out[8].persisted == UNKNOWN
    assert out[8].bars_in_current == 9


def test_flap_after_initial_dwell_switches_alternately():
    stream = [E(U), E(U), E(D), E(D)] * 5
    out = feed(stream)
    assert out[7].persisted == D and out[7].switched
    assert out[8].persisted == D and out[8].raw_label == U  # cooled: no switch
    assert out[9].persisted == D
    assert out[12].persisted == D and out[13].persisted == D
    assert out[16].persisted == D
    assert out[17].persisted == U and out[17].switched
    assert out[18].persisted == U


def test_cooldown_bars_failed_candidates():
    stream = [X()] * 6 + [E(U), E(U)] + [E(D)] * 5
    out = feed(stream)
    assert out[7].switched
    assert out[8].persisted == U and out[8].raw_label == D
    assert out[9].persisted == U and out[9].raw_label == D
    assert out[10].persisted == U and out[10].raw_label == D
    assert out[10].eligible is True  # eligible raw, but cooled -> no candidacy
    assert out[11].raw_label == D and out[11].eligible is True
    assert out[11].persisted == U


def test_switch_back_after_dwell_and_confirm():
    stream = [X()] * 6 + [E(U)] * 10 + [E(D)] * 3
    out = feed(stream)
    assert out[7].persisted == U
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


def test_persistence_over_effective_labels_from_responses():
    """The machine consumes EFFECTIVE labels: responses that fail the safety
    layer are UNKNOWN-candidates and never switch the persisted state."""
    stream = [None] * 6 + [_resp(), _resp(), _resp(conf=0.3)]
    out = run_persistence(stream, P)
    assert out[7].persisted == U and out[7].switched  # two eligible UPTREND
    assert out[8].raw_label == UNKNOWN  # low conf -> candidate
    assert out[8].persisted == U


def test_thresholds_never_lowered():
    """no_forced_trades_law: a low-confidence stream can never produce an
    eligible effective label, no matter how long it runs."""
    stream = [_resp(conf=0.10)] * 100
    out = run_persistence(stream, P)
    assert all(p.persisted == UNKNOWN for p in out)
