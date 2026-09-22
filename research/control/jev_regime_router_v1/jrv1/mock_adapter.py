"""DETERMINISTIC mock classifier for SMOKE-namespace pipeline tests.

Never used for scoring. Mirrors the jrv1_decision_io@1 response schema and is
rule-based so the frozen synthetic canaries pass (FIX1->UPTREND, FIX2->
DOWNTREND, FIX3->ACCUMULATION, FIX4->DISTRIBUTION, FIX5->TRANSITION_UNKNOWN;
FIX6 is LOCAL_INVALID upstream and is never sent here).

Probability jitter is derived from a sha256 of the canonical feature vector
(deterministic per state, no global RNG state). The mock model name is
clearly namespaced so no artifact can be mistaken for a live response.
"""

from __future__ import annotations

import hashlib

from . import DECISION_IO_SCHEMA
from .decisions import compute_input_digest

MOCK_MODEL = "mock-deterministic-v1"
MOCK_NAMESPACE = "MOCK_SMOKE"

_UNKNOWN = "TRANSITION_UNKNOWN"


def mock_rule(vector: list[float]) -> str:
    """Rule mapping clear synthetic structure to the frozen expected labels."""
    (
        r1,
        r4,
        r12,
        r24,
        r72,
        slope_fast,
        slope_slow,
        dist_ema,
        adx,
        atr_pct,
        rv_pctile,
        dd168,
        dist_low,
        range_pos,
        vol_z,
        clv,
    ) = vector
    if adx >= 22.0 and r72 > 0.15 and slope_slow > 0:
        return "UPTREND"
    if adx >= 22.0 and r72 < -0.15 and slope_slow < 0:
        return "DOWNTREND"
    if adx < 22.0 and r72 < -0.10:
        return "ACCUMULATION"
    if adx < 22.0 and r72 > 0.10:
        return "DISTRIBUTION"
    return _UNKNOWN


def _jitter(vector: list[float]) -> tuple[int, int, int]:
    h = hashlib.sha256(
        ",".join(repr(float(v)) for v in vector).encode("utf-8")
    ).digest()
    return h[0], h[1], h[2]


def mock_decide(state_id: str, payload: dict, requested_model: str = MOCK_MODEL) -> dict:
    """Deterministic mock response line (schema-identical to the real one)."""
    vector = payload["feature_vector"]
    digest = compute_input_digest(payload, requested_model)
    rule = mock_rule(vector)
    probs = {lab: 0.0 for lab in (
        "ACCUMULATION",
        "UPTREND",
        "DISTRIBUTION",
        "DOWNTREND",
        _UNKNOWN,
    )}
    if rule == _UNKNOWN:
        # deliberately ineligible top1 (confidence below the persistence floor)
        probs[_UNKNOWN] = 0.60
        for lab in probs:
            if lab != _UNKNOWN:
                probs[lab] = 0.10
        confidence = 0.40
    else:
        j0, j1, j2 = _jitter(vector)
        top1 = 0.55 + (j0 % 50) / 1000.0  # 0.550..0.599
        top2 = top1 - 0.30                # margin exactly 0.30 >= 0.20
        rest = round(1.0 - top1 - top2, 12)
        probs[rule] = top1
        probs[_UNKNOWN] = top2
        others = [lab for lab in probs if lab not in (rule, _UNKNOWN)]
        w = [1 + (j1 % 5), 1 + (j2 % 5), 1 + ((j1 + j2) % 5)]
        sw = sum(w)
        acc = 0.0
        for k, lab in enumerate(others):
            share = rest * w[k] / sw
            probs[lab] = share
            acc += share
        probs[others[-1]] += rest - acc  # exact sum-to-one correction
        confidence = top1
    return {
        "schema": DECISION_IO_SCHEMA,
        "state_id": state_id,
        "status": "OK",
        "regime": rule,
        "probabilities": probs,
        "confidence": confidence,
        "model": MOCK_MODEL,
        "request_id": hashlib.sha256((state_id + digest).encode()).hexdigest()[:12],
        "input_digest": digest,
        "latency_ms": 1.0,
        "error_class": None,
        "namespace": MOCK_NAMESPACE,
    }


class MockProvider:
    """Provider interface for sequential_timeline (SMOKE namespace only)."""

    def __init__(self, requested_model: str = MOCK_MODEL) -> None:
        self.requested_model = requested_model

    def __call__(self, state_id: str, payload: dict) -> dict:
        return mock_decide(state_id, payload, self.requested_model)
