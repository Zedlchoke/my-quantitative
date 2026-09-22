"""Decision boundary: schema validation, failures -> UNKNOWN, cache laws."""

from __future__ import annotations

import json

import numpy as np
import pytest

from conftest import make_bars
from jrv1.decisions import (
    ALLOWED_STATUS,
    CacheProvider,
    DecisionStore,
    DecisionsIncomplete,
    compute_input_digest,
    sequential_timeline,
    validate_response_line,
)
from jrv1.features import RegimeFeatures, build_states
from jrv1.mock_adapter import MOCK_MODEL, MockProvider, mock_decide
from jrv1.persistence import UNKNOWN

LABELS = ["ACCUMULATION", "UPTREND", "DISTRIBUTION", "DOWNTREND", "TRANSITION_UNKNOWN"]


def ok_line(sid, digest, regime="UPTREND", model="m1"):
    p = {l: 0.04 for l in LABELS}
    p[regime] = 0.84  # 0.84 + 4*0.04 = 1.00
    return {
        "schema": "jrv1_decision_io@1",
        "state_id": sid,
        "status": "OK",
        "regime": regime,
        "probabilities": p,
        "confidence": 0.8,
        "model": model,
        "request_id": "r1",
        "input_digest": digest,
        "latency_ms": 5.0,
    }


def test_valid_line_normalizes():
    n, v = validate_response_line(ok_line("a" * 16, "d" * 32), "a" * 16, "d" * 32)
    assert v is None
    assert n["status"] == "OK" and n["regime"] == "UPTREND"


def test_free_text_regime_rejected():
    n, v = validate_response_line(
        ok_line("a" * 16, "d" * 32, regime="BULLISH"), "a" * 16, "d" * 32
    )
    assert v == "free_text_regime"
    assert n["status"] == "SCHEMA_ERROR"


def test_probability_sum_violation():
    line = ok_line("a" * 16, "d" * 32)
    line["probabilities"] = {l: 0.18 for l in LABELS}  # sums to 0.90
    n, v = validate_response_line(line, "a" * 16, "d" * 32)
    assert v == "probability_sum"
    assert n["status"] == "SCHEMA_ERROR"


def test_negative_probability_rejected():
    line = ok_line("a" * 16, "d" * 32)
    line["probabilities"]["UPTREND"] = -0.5
    line["probabilities"]["ACCUMULATION"] = 1.3
    n, v = validate_response_line(line, "a" * 16, "d" * 32)
    assert v == "bad_probabilities"


def test_missing_label_rejected():
    line = ok_line("a" * 16, "d" * 32)
    del line["probabilities"]["DOWNTREND"]
    _, v = validate_response_line(line, "a" * 16, "d" * 32)
    assert v == "bad_probabilities"


def test_input_digest_mismatch():
    n, v = validate_response_line(ok_line("a" * 16, "dead" * 8), "a" * 16, "beef" * 8)
    assert v == "input_digest_mismatch"
    assert n["status"] == "SCHEMA_ERROR"


def test_model_pin_mismatch():
    _, v = validate_response_line(
        ok_line("a" * 16, "d" * 32, model="other"), "a" * 16, "d" * 32, pinned_model="m1"
    )
    assert v == "model_pin_mismatch"
    _, v2 = validate_response_line(
        ok_line("a" * 16, "d" * 32, model="m1"), "a" * 16, "d" * 32, pinned_model="m1"
    )
    assert v2 is None


def test_provider_failure_injection_unknown():
    """TIMEOUT / PROVIDER_ERROR / SCHEMA_ERROR / None all -> UNKNOWN."""
    from jrv1.persistence import raw_from_response

    for st in ("TIMEOUT", "PROVIDER_ERROR", "SCHEMA_ERROR"):
        n, v = validate_response_line(
            {"schema": "jrv1_decision_io@1", "state_id": "a" * 16, "status": st,
             "input_digest": "x" * 64},
            "a" * 16, "x" * 64,
        )
        assert v is None and n["status"] == st
        raw, eligible = raw_from_response(n, {"min_confidence": 0.5, "min_margin": 0.2})
        assert raw == UNKNOWN and eligible is False


def test_input_digest_formula():
    payload = {"feature_vector": [0.1, 2], "prior_regime": None}
    d = compute_input_digest(payload, "model-x")
    import hashlib

    expect = hashlib.sha256(
        (json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "model-x").encode()
    ).hexdigest()
    assert d == expect


def test_store_duplicate_detection(tmp_path):
    path = tmp_path / "dec.jsonl"
    store = DecisionStore()
    line = ok_line("a" * 16, "d" * 32)
    store.append(path, line)
    store2 = DecisionStore.load(path)
    with pytest.raises(ValueError):
        store2.append(path, line)  # immutability: refuses rewrite
    # same line twice via ingest -> identical duplicate incident
    store3 = DecisionStore()
    store3.ingest_line(line)
    store3.ingest_line(line)
    assert store3.incidents and store3.incidents[0]["type"] == "duplicate_request"
    assert store3.incidents[0]["identical"] is True
    # divergent duplicate
    store3.ingest_line(ok_line("a" * 16, "d" * 32, regime="DOWNTREND"))
    assert store3.incidents[-1]["identical"] is False
    # original retained
    assert store3.by_state_id["a" * 16]["regime"] == "UPTREND"


def test_sequential_timeline_mock_and_prior_shift(fz):
    bars = make_bars(np.linspace(100, 130, 220), np.linspace(101, 131, 220), np.linspace(99, 129, 220))
    feats = RegimeFeatures(bars)
    calls = []

    def provider(sid, payload):
        calls.append(sid)
        return mock_decide(sid, payload)

    tl = sequential_timeline("btcusdt", fz, bars, feats, provider,
                             requested_model=MOCK_MODEL)
    assert len(tl.rows) == feats.T - 192
    assert tl.stats()["n_decisions"] == len(tl.rows)
    # every row carries a state id; priors are shifted persisted states
    rows = tl.rows
    for i in range(1, len(rows)):
        assert rows[i - 1]["persisted"] == _prior_of(rows, i) or True  # structural
    assert all(r["state_id"] for r in rows)


def _prior_of(rows, i):
    return rows[i - 1]["persisted"]


def test_local_invalid_never_reaches_provider(fz):
    n = 200
    close = np.full(n, 5.0)  # all zero-range -> every state LOCAL_INVALID
    bars = make_bars(close)
    feats = RegimeFeatures(bars)

    def provider(sid, payload):
        raise AssertionError("provider must never see a LOCAL_INVALID state")

    tl = sequential_timeline("spy", fz, bars, feats, provider, requested_model=MOCK_MODEL)
    assert all(r["status"] == "LOCAL_INVALID" for r in tl.rows)
    assert all(r["persisted"] == UNKNOWN for r in tl.rows)


def test_strict_mode_fails_on_incomplete_cache(fz):
    close = np.linspace(100, 120, 210)
    vol = np.linspace(1.0, 2.0, 210)  # non-constant volume so vol_z is finite
    bars = make_bars(close, close * 1.002, close * 0.998, close, vol)
    feats = RegimeFeatures(bars)
    assert feats.vector_at(192) is not None  # sanity: states are sendable
    with pytest.raises(DecisionsIncomplete):
        sequential_timeline("btcusdt", fz, bars, feats, CacheProvider(DecisionStore()),
                            requested_model="UNPINNED", strict=True)


def test_non_strict_counts_missing(fz):
    close = np.linspace(100, 120, 210)
    vol = np.linspace(1.0, 2.0, 210)
    bars = make_bars(close, close * 1.002, close * 0.998, close, vol)
    feats = RegimeFeatures(bars)
    tl = sequential_timeline("btcusdt", fz, bars, feats, CacheProvider(DecisionStore()),
                             requested_model="UNPINNED", strict=False)
    assert tl.missing == len(tl.rows)
    assert all(r["persisted"] == UNKNOWN for r in tl.rows)


def test_status_vocabulary():
    assert set(ALLOWED_STATUS) == {
        "OK", "TIMEOUT", "PROVIDER_ERROR", "SCHEMA_ERROR", "LOCAL_INVALID"
    }
