"""QuestionIO: producer digest, forced-choice validation, usage law, store."""

from __future__ import annotations

import hashlib
import json

import pytest

from jrv2 import QUESTION_IO_SCHEMA
from jrv2.features import normalize_semantic_state
from jrv2.mock_adapter import MOCK_MODEL, mock_decide
from jrv2.questionio import (
    DecisionStore,
    build_request_line,
    compute_input_digest,
    validate_response_line,
)


def _state():
    return normalize_semantic_state(
        {
            "fast_trend": "weak_up", "slow_trend": "flat", "trend_strength": "medium",
            "volatility_regime": "normal", "drawdown_state": "mild", "range_location": "middle",
            "close_location": "neutral", "volume_state": "normal", "dist_to_ema": "at",
            "short_return": 0.002, "medium_return": 0.011, "long_return": 0.28,
            "ema_slope_fast": 0.0009, "ema_slope_slow": 0.0004, "dist_ema": 1.2,
            "adx14": 34, "atr_pct": 0.008, "rv_pctile": 0.62, "dd_168": -0.03,
            "dist_low": 0.3, "range_pos": 0.42, "vol_z": 0.35, "clv_24": 0.62,
            "prior_structure": "TREND_UP", "prior_direction": "UP",
        }
    )


def test_producer_digest_is_deterministic_and_matches_golden_shape():
    st = _state()
    d1 = compute_input_digest(st, MOCK_MODEL)
    d2 = compute_input_digest(st, MOCK_MODEL)
    assert d1 == d2 and len(d1) == 64
    # different model -> different digest
    assert compute_input_digest(st, "other") != d1


def test_request_line_carries_producer_digest():
    st = _state()
    line = build_request_line("0123456789abcdef", st, MOCK_MODEL)
    assert line["schema"] == QUESTION_IO_SCHEMA
    assert line["input_digest"] == compute_input_digest(line["state"], MOCK_MODEL)
    assert set(line["state"].keys()) == {"bins", "numerics", "prior_structure", "prior_direction"}


def _ok_response(sid="0123456789abcdef", state=None, model=MOCK_MODEL, **overrides):
    st = state if state is not None else _state()
    line = build_request_line(sid, st, model)
    resp = mock_decide(sid, st, model)
    for k, v in overrides.items():
        if v is ...:
            resp.pop(k, None)
        else:
            resp[k] = v
    return line, resp


def test_ok_response_validates_clean():
    line, resp = _ok_response()
    normalized, violation = validate_response_line(resp, line["state_id"], line["input_digest"], None)
    assert violation is None
    assert normalized["status"] == "OK"
    assert set(normalized["answers"].keys()) == {"structure", "direction", "phase"}
    assert normalized["usage"]["input_tokens"] >= 0


def test_schema_field_law():
    line, resp = _ok_response()
    resp["schema"] = "jrv1_decision_io@1"  # V1 namespace must not validate
    normalized, violation = validate_response_line(resp, line["state_id"], line["input_digest"])
    assert violation == "schema_field"
    assert normalized["status"] == "SCHEMA_ERROR"


def test_digest_echo_law():
    line, resp = _ok_response()
    resp["input_digest"] = "0" * 64  # tampered echo
    normalized, violation = validate_response_line(resp, line["state_id"], line["input_digest"])
    assert violation == "input_digest_mismatch"
    assert normalized["status"] == "SCHEMA_ERROR"


def test_model_pin_mismatch_is_schema_error():
    line, resp = _ok_response()
    resp["model"] = "jev-someone-else"
    normalized, violation = validate_response_line(resp, line["state_id"], line["input_digest"], MOCK_MODEL)
    assert violation == "model_pin_mismatch"


def test_fifth_phase_label_is_schema_error():
    line, resp = _ok_response()
    resp["answers"]["phase"]["choice"] = "TRANSITION_UNKNOWN"
    normalized, violation = validate_response_line(resp, line["state_id"], line["input_digest"])
    assert violation == "phase_choice_not_in_schema"
    assert normalized["status"] == "SCHEMA_ERROR"
    # UNKNOWN-equivalent too
    resp2 = _ok_response()[1]
    resp2["answers"]["phase"]["choice"] = "UNKNOWN"
    _, v2 = validate_response_line(resp2, line["state_id"], line["input_digest"])
    assert v2 == "phase_choice_not_in_schema"
    # free text
    resp3 = _ok_response()[1]
    resp3["answers"]["phase"]["choice"] = "kinda trending"
    _, v3 = validate_response_line(resp3, line["state_id"], line["input_digest"])
    assert v3 == "phase_choice_not_in_schema"


def test_missing_answers_or_question_is_schema_error():
    line, resp = _ok_response()
    resp["answers"] = {"structure": resp["answers"]["structure"], "direction": resp["answers"]["direction"]}
    _, v = validate_response_line(resp, line["state_id"], line["input_digest"])
    assert v == "answers_question_set_mismatch"
    line2, resp2 = _ok_response()
    del resp2["answers"]["phase"]
    _, v2 = validate_response_line(resp2, line2["state_id"], line2["input_digest"])
    assert v2 == "answers_question_set_mismatch"  # question set no longer exact


def test_probability_laws_per_question():
    line, resp = _ok_response()
    resp["answers"]["phase"]["probabilities"]["UPTREND"] = 0.4  # sum 0.8
    _, v = validate_response_line(resp, line["state_id"], line["input_digest"])
    assert v == "phase_probability_sum"
    line2, resp2 = _ok_response()
    resp2["answers"]["structure"]["probabilities"]["MYSTERY"] = 0.5  # option set violation
    del resp2["answers"]["structure"]["probabilities"]["RANGE"]
    _, v2 = validate_response_line(resp2, line2["state_id"], line2["input_digest"])
    assert v2 == "structure_probabilities_option_set_mismatch"


def test_usage_persisted_per_response_law():
    line, resp = _ok_response()
    del resp["usage"]
    _, v = validate_response_line(resp, line["state_id"], line["input_digest"])
    assert v == "missing_usage"
    line2, resp2 = _ok_response()
    resp2["usage"] = {"input_tokens": 1}  # missing output
    _, v2 = validate_response_line(resp2, line2["state_id"], line2["input_digest"])
    assert v2 == "missing_usage"
    # non-OK statuses do not require usage
    line3, resp3 = _ok_response()
    resp3["status"] = "TIMEOUT"
    resp3.pop("usage", None)
    norm, v3 = validate_response_line(resp3, line3["state_id"], line3["input_digest"])
    assert v3 is None and norm["status"] == "TIMEOUT"


def test_error_statuses_are_not_violations():
    for status in ("TIMEOUT", "PROVIDER_ERROR", "SCHEMA_ERROR", "LOCAL_INVALID"):
        line, resp = _ok_response(status=status)
        resp.pop("answers", None)
        normalized, violation = validate_response_line(resp, line["state_id"], line["input_digest"])
        assert violation is None
        assert normalized["status"] == status


def test_store_append_only_and_incidents(tmp_path):
    p = tmp_path / "decisions.jsonl"
    st = _state()
    sid = "aaaaaaaaaaaaaaaa"
    line = build_request_line(sid, st, MOCK_MODEL)
    resp = mock_decide(sid, st, MOCK_MODEL)
    store = DecisionStore()
    store.append(p, resp)
    with pytest.raises(ValueError, match="cache immutability"):
        store.append(p, resp)
    # divergent duplicate flagged on reload
    other = dict(resp)
    other["latency_ms"] = 99.0
    with open(p, "ab") as f:
        f.write((json.dumps(other, sort_keys=True) + "\n").encode())
    store2 = DecisionStore.load(p)
    assert len(store2.by_state_id) == 1
    assert any(i["type"] == "duplicate_request" and i["identical"] is False for i in store2.incidents)
    # corrupt line incident
    with open(p, "ab") as f:
        f.write(b"{not json}\n")
    store3 = DecisionStore.load(p)
    assert any(i["type"] == "corrupt_line" for i in store3.incidents)


def test_golden_digest_vectors_pinned():
    """Cross-language authority: the same literals pinned in
    adapter/test/digest_golden.test.ts (Python producer side)."""
    from jrv2.freezes import canonical_json

    MODEL = "mock-pin-2"
    vecs = [
        (
            {"bins": {"fast_trend": "weak_up"}, "numerics": {"short_return": 1e-05, "adx14": 34.0},
             "prior_structure": "RANGE", "prior_direction": "NEUTRAL"},
            '{"bins":{"fast_trend":"weak_up"},"numerics":{"adx14":34.0,"short_return":1e-05},'
            '"prior_direction":"NEUTRAL","prior_structure":"RANGE"}',
            "d74b136f63824fefafe67ad5e6ddc543a63e8ca99ea828b42fd9c656ad61c3c4",
        ),
        (
            {"bins": {"fast_trend": "flat"}, "numerics": {"short_return": 0.01, "long_return": 1.234e-07},
             "prior_structure": "TREND_UP", "prior_direction": "UP"},
            '{"bins":{"fast_trend":"flat"},"numerics":{"long_return":1.234e-07,"short_return":0.01},'
            '"prior_direction":"UP","prior_structure":"TREND_UP"}',
            "29722fb83f019362082763f9a0691db703bdbbc41aea6310fb1a5a34b278c366",
        ),
    ]
    for state, canonical, digest in vecs:
        assert canonical_json(state) == canonical
        assert compute_input_digest(state, MODEL) == digest
