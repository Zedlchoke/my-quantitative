"""DETERMINISTIC mock classifier for MOCK-namespace pipeline tests.

Never used for scoring. Produces jrv2_question_io@1 response lines with
THREE typed answer blocks (structure/direction/phase — the phase choice is
ALWAYS one of the 4 schema phases; the mock can never abstain either).
Rule-based on the named semantic bins so the frozen synthetic canaries pass:
C1->UPTREND, C2->DOWNTREND, C3->ACCUMULATION, C4->DISTRIBUTION via consistent
answers; C5/C6/C7 produce answers that are schema-valid but hierarchically
contradictory (code-owned UNKNOWN via the safety layer); C8 is
LOCAL_INVALID upstream and never sent.

Probability jitter derives from a sha256 of the input digest (deterministic
per state, no global RNG). Mock model names are clearly namespaced so no
artifact can be mistaken for a live response.
"""

from __future__ import annotations

import hashlib

from . import QUESTION_IO_SCHEMA, PHASES, STRUCTURES, DIRECTIONS
from .questionio import compute_input_digest

MOCK_MODEL = "mock-deterministic-v2"
MOCK_NAMESPACE = "MOCK"
REPLAY_MOCK_MODEL = "mock-pin-2"


def mock_answers(bins: dict, prior_direction: str, prior_structure: str) -> dict:
    """Deterministic (structure, direction, phase) answers from the bins.

    Plausible-label heuristic aligned with the canary fixtures:
    - fast & slow agree up + strength medium/high -> TREND/UP/UPTREND
    - fast & slow agree down + strength medium/high -> TREND/DOWN/DOWNTREND
    - fast flat -> RANGE/NEUTRAL + phase by prior (DOWN->ACCUMULATION,
      UP->DISTRIBUTION, NEUTRAL/none->UPTREND = contradiction -> code UNKNOWN)
    - anything else (mixed/disagreeing) -> TREND/NEUTRAL (contradiction)
    """
    fast = bins.get("fast_trend", "flat")
    slow = bins.get("slow_trend", "flat")
    strength = bins.get("trend_strength", "low")
    fast_up = fast in ("weak_up", "strong_up")
    fast_dn = fast in ("weak_down", "strong_down")
    slow_up = slow in ("weak_up", "strong_up")
    slow_dn = slow in ("weak_down", "strong_down")
    pd = prior_direction if prior_direction in ("UP", "DOWN", "NEUTRAL") else "NEUTRAL"

    if fast_up and slow_up:
        return {"structure": "TREND", "direction": "UP", "phase": "UPTREND"}
    if fast_dn and slow_dn:
        return {"structure": "TREND", "direction": "DOWN", "phase": "DOWNTREND"}
    if fast == "flat" and not fast_up and not fast_dn:
        if pd == "DOWN":
            return {"structure": "RANGE", "direction": "NEUTRAL", "phase": "ACCUMULATION"}
        if pd == "UP":
            return {"structure": "RANGE", "direction": "NEUTRAL", "phase": "DISTRIBUTION"}
        # contradiction: RANGE + NEUTRAL + prior NEUTRAL
        return {"structure": "RANGE", "direction": "NEUTRAL", "phase": "UPTREND"}
    if fast_up and strength in ("high", "medium") and not slow_dn:
        return {"structure": "TREND", "direction": "UP", "phase": "UPTREND"}
    if fast_dn and strength in ("high", "medium") and not slow_up:
        return {"structure": "TREND", "direction": "DOWN", "phase": "DOWNTREND"}
    # mixed evidence -> schema-valid contradiction (TREND + NEUTRAL)
    return {"structure": "TREND", "direction": "NEUTRAL", "phase": "UPTREND"}


def _answer_block(top: str, options, h: bytes) -> dict:
    """Integer-cents probability block over `options`, sum EXACTLY 1.00.

    top = 55..82 cents; the remainder splits deterministically across the
    non-top options (each >= 1 cent; phase margin >= 0.40 by construction).
    """
    rest = [o for o in options if o != top]
    top_cents = 55 + (h[0] % 28)  # 55..82
    rem = 100 - top_cents
    n_rest = len(rest)
    base = rem // n_rest
    extra = rem - base * n_rest
    probs = {top: top_cents / 100}
    for i, opt in enumerate(rest):
        c = base + (1 if i < extra else 0)
        probs[opt] = c / 100
    return {
        "choice": top,
        "probabilities": probs,
        "confidence": top_cents / 100,
    }


def mock_decide(state_id: str, state: dict, requested_model: str = MOCK_MODEL) -> dict:
    """Deterministic mock response line (schema-identical to the real one)."""
    from .features import normalize_semantic_state

    st = normalize_semantic_state(state)
    digest = compute_input_digest(st, requested_model)
    ans = mock_answers(st["bins"], st["prior_direction"], st["prior_structure"])
    h = hashlib.sha256(f"{digest}|mock-v2".encode("utf-8")).digest()
    return {
        "schema": QUESTION_IO_SCHEMA,
        "state_id": state_id,
        "status": "OK",
        "answers": {
            "structure": _answer_block(ans["structure"], STRUCTURES, h[0:32]),
            "direction": _answer_block(ans["direction"], DIRECTIONS, h[1:33]),
            "phase": _answer_block(ans["phase"], PHASES, h[2:34]),
        },
        "model": requested_model,
        "request_id": "mock-" + hashlib.sha256((state_id + digest).encode()).hexdigest()[:12],
        "input_digest": digest,
        "prior_direction": st["prior_direction"],
        "latency_ms": 1.0,
        "usage": {"input_tokens": 40 + (h[3] % 20), "output_tokens": 8 + (h[4] % 8)},
        "error_class": None,
        "mock": True,
        "namespace": MOCK_NAMESPACE,
    }


class MockProvider:
    """Provider interface for sequential_timeline (MOCK namespace only)."""

    def __init__(self, requested_model: str = MOCK_MODEL) -> None:
        self.requested_model = requested_model

    def __call__(self, state_id: str, state: dict) -> dict:
        return mock_decide(state_id, state, self.requested_model)
