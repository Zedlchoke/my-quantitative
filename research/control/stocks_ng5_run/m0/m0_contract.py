"""M0 structural-novelty contract machinery (STOCKS-NG5 / FOREX-NG6 shared law).

Owner-mandated methodology gate (plans/PLAN_stocks_ng5.md §3, PLAN_forex_ng6.md §3).
Implements the six comparison families (seven named metrics), the frozen
family-verdict rule, same-instant clustering, control classification and the
G8/G9 freeze/refuse semantics.  Pure numpy; deterministic.

Law encoded here:
- structural novelty is measured in SIGNAL SPACE ONLY: no future returns,
  PnL, payoff correlation or any outcome enters the verdict (G3/G4);
- a sign-inverted form is the SAME mechanism with the direction flipped
  (G2) and can only ever be an arm/control, never a new family;
- the pooled ancestry bar is the program bar 0.20 and is immovable (G9);
- thresholds live in a frozen, hashed contract that measurement refuses
  to run against when the hash does not match (G8).
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np

PROGRAM_RHO_BAR = 0.20  # G9: immovable program bar (NG1-NG3 vetoes stand)
SIGN_NEG_BAR = -0.80  # below this weight-Pearson with low sign agreement
SIGN_AGREEMENT_BAR = 0.10  # ... the form is a sign inversion
AGGREGATION = "max_abs_correlation"

SAME_FAMILY = "SAME_FAMILY"
SAME_MECHANISM_DIFFERENT_DIRECTION = "SAME_MECHANISM_DIFFERENT_DIRECTION"
DIFFERENT_FAMILY = "DIFFERENT_FAMILY"


# ---------------------------------------------------------------- metrics

def _pearson(x: np.ndarray, y: np.ndarray) -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.size < 2:
        return 0.0
    xs = x - x.mean()
    ys = y - y.mean()
    denom = math.sqrt(float(xs @ xs) * float(ys @ ys))
    if denom == 0.0:
        return 0.0
    return float((xs @ ys) / denom)


def _rank(x: np.ndarray) -> np.ndarray:
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(x.size, dtype=float)
    ranks[order] = np.arange(1, x.size + 1, dtype=float)
    return ranks


def _spearman(x: np.ndarray, y: np.ndarray) -> float:
    return _pearson(_rank(np.asarray(x, dtype=float)), _rank(np.asarray(y, dtype=float)))


def _sign_agreement(a: np.ndarray, b: np.ndarray) -> float:
    a = np.sign(np.asarray(a, dtype=float))
    b = np.sign(np.asarray(b, dtype=float))
    mask = (a != 0) & (b != 0)
    if not mask.any():
        return 1.0  # nothing active on either side: trivially "agreeing"
    return float((a[mask] == b[mask]).mean())


def _active_jaccard(a: np.ndarray, b: np.ndarray) -> float:
    a_on = np.asarray(a, dtype=float) != 0
    b_on = np.asarray(b, dtype=float) != 0
    union = int((a_on | b_on).sum())
    if union == 0:
        return 1.0
    return float((a_on & b_on).sum() / union)


def _decision(a: np.ndarray) -> np.ndarray:
    """Decision class of a book: long / flat / short."""
    return np.sign(np.asarray(a, dtype=float))


def _decision_overlap(a: np.ndarray, b: np.ndarray) -> float:
    da, db = _decision(a), _decision(b)
    return float((da == db).mean())


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    denom = math.sqrt(float(a @ a) * float(b @ b))
    if denom == 0.0:
        return 0.0
    return float((a @ b) / denom)


def primary_comparisons(
    weights_a: np.ndarray,
    weights_b: np.ndarray,
    signals_a: np.ndarray,
    signals_b: np.ndarray,
) -> dict:
    """The six comparison families / seven named metrics (G5).

    Signal-space only.  There is deliberately NO returns argument: feeding
    outcomes into novelty measurement is the G4 violation class.
    """
    w_a = np.asarray(weights_a, dtype=float)
    w_b = np.asarray(weights_b, dtype=float)
    s_a = np.asarray(signals_a, dtype=float)
    s_b = np.asarray(signals_b, dtype=float)
    for v in (w_a, w_b, s_a, s_b):
        if not (v.size == w_a.size == w_b.size == s_a.size == s_b.size):
            raise ValueError("aligned decision-grid vectors required")
    return {
        "target_weight_pearson": _pearson(w_a, w_b),
        "target_weight_spearman": _spearman(w_a, w_b),
        "signal_rank_correlation": _spearman(s_a, s_b),
        "sign_agreement": _sign_agreement(s_a, s_b),
        "active_set_jaccard": _active_jaccard(w_a, w_b),
        "decision_overlap": _decision_overlap(w_a, w_b),
        "exposure_cosine": _cosine(w_a, w_b),
    }


def pooled_abs_correlation(metrics: dict) -> float:
    return max(
        abs(metrics["target_weight_pearson"]),
        abs(metrics["target_weight_spearman"]),
        abs(metrics["signal_rank_correlation"]),
    )


# ---------------------------------------------------------------- verdict

def family_verdict(metrics: dict, contract: dict) -> str:
    """Frozen verdict rule; the contract hash must already be verified (G8).

    Inversion is adjudicated BEFORE the pooled-rho family merge: an exact
    or near-exact sign inversion has maximal |rho| BY CONSTRUCTION, so
    checking the family bar first would misclassify every inverted form
    as a new family — the G2 violation class.
    """
    assert contract["aggregation"] == AGGREGATION
    if (
        metrics["target_weight_pearson"] <= contract["sign_neg_bar"]
        and metrics["sign_agreement"] <= contract["sign_agreement_bar"]
    ):
        return SAME_MECHANISM_DIFFERENT_DIRECTION
    rho = pooled_abs_correlation(metrics)
    if rho > contract["rho_bar"]:
        return SAME_FAMILY
    return DIFFERENT_FAMILY


# ------------------------------------------------- G6 same-instant clustering

def effective_observation_count(keys) -> int:
    """Samples sharing a decision date / release instant are ONE observation."""
    return len({k for k in keys})


# ------------------------------------------------------- G7 control classes

CONTROL_CLASSES = {
    "price_only_payoff": "E_FALSIFICATION",
    "momentum_shadow": "E_FALSIFICATION",
    "clock_only_book": "E_FALSIFICATION",
    "sign_inverted": "ARM_CONTROL",
    "delayed_state": "NULL_CONTROL",
    "shuffled_calendar": "NULL_CONTROL",
}


def control_classification(control_kind: str) -> str:
    return CONTROL_CLASSES[control_kind]


# ------------------------------------------------------ G8/G9 freeze + load

CONTRACT_FIELDS = {
    "rho_bar": PROGRAM_RHO_BAR,
    "sign_neg_bar": SIGN_NEG_BAR,
    "sign_agreement_bar": SIGN_AGREEMENT_BAR,
    "aggregation": AGGREGATION,
}


def freeze_contract(path: str | Path) -> str:
    blob = json.dumps(CONTRACT_FIELDS, sort_keys=True, indent=1).encode()
    path = Path(path)
    path.write_bytes(blob)
    return hashlib.sha256(blob).hexdigest()


class ContractRefused(Exception):
    """G8 hash mismatch or G9 bar violation: measurement must fail closed."""


def load_contract(path: str | Path, expected_sha256: str) -> dict:
    blob = Path(path).read_bytes()
    if hashlib.sha256(blob).hexdigest() != expected_sha256:
        raise ContractRefused("G8: contract hash mismatch — measurement refuses")
    contract = json.loads(blob)
    if contract["rho_bar"] != PROGRAM_RHO_BAR:
        raise ContractRefused(
            "G9: program bar 0.20 is immovable; NG1-NG3 vetoes are not grounds "
            "to lower it (got %r)" % (contract["rho_bar"],)
        )
    if contract["aggregation"] != AGGREGATION:
        raise ContractRefused("G8: aggregation rule is frozen")
    return contract


def measure_with_contract(metrics: dict, path: str | Path, expected_sha256: str) -> str:
    return family_verdict(metrics, load_contract(path, expected_sha256))


# ------------------------------------------- G10 wrong-implementation probe

def wrong_verdict_signal_times_shared_return(
    signals_a: np.ndarray,
    signals_b: np.ndarray,
    shared_future_returns: np.ndarray,
) -> str:
    """Deliberately WRONG kernel (G10 sensitivity demo).

    Computes candidate PnLs as signal x shared future return and merges on
    payoff correlation — exactly the implementation class the golden suite
    must catch and reject.
    """
    pnl_a = np.asarray(signals_a, dtype=float) * np.asarray(shared_future_returns, dtype=float)
    pnl_b = np.asarray(signals_b, dtype=float) * np.asarray(shared_future_returns, dtype=float)
    if abs(_pearson(pnl_a, pnl_b)) > PROGRAM_RHO_BAR:
        return SAME_FAMILY
    return DIFFERENT_FAMILY
