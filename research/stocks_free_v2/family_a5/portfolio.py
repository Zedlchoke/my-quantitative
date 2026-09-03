"""Frozen defensive allocation mapping for the A5-SFV2-TREND-DEFENSIVE family.

Implements ``DETERMINISTIC_VOL_TARGET_TO_CASH`` exactly as preregistered in
``a5_arm1_tsm12_ivol.json`` (and, identically, in the arm-2 and arm-3 specs):

* ``g(t) = min(1.0, 0.10 / sigma_arena(t))`` when ``sigma_arena(t) > 0``;
  ``g(t) = 1.0`` if ``sigma_arena(t) <= 0`` (declared deterministic tie-break).
* ``w_i(t) = min(0.35, 1/|E|)`` for eligible i, ``E`` = eligible set at t;
  ``w = 0`` for ineligible i.
* final ETF weight ``= g(t) * w_i(t)``; ``CASH = 1 - g(t) * sum_i w_i(t)`` —
  the uncapped residual goes to CASH, NEVER redistributed to other ETFs.
* Edge cases (spec-declared): empty eligible set -> book = 100% cash;
  eligible set of size 1 or 2 -> the 35% cap binds and the residual is cash.
* Invariants (always enforced structurally): long-only, gross <= 1.0,
  single-ETF weight <= 0.35, no shorting, no leverage, cash explicit.

Pure arithmetic on injected inputs only; schedule-only lane — no returns, PnL,
PF or any scored metric is computed anywhere in this package.
"""

from __future__ import annotations

from typing import Iterable

CASH_SYMBOL = "CASH"

TARGET_VOL_ANNUAL = 0.10
PER_ETF_CAP = 0.35

# Float-dust tolerance for the <= 1.0 gross bookkeeping (e.g. 3 x (1/3) sums).
_GROSS_TOLERANCE = 1e-12


def gross_scalar(arena_sigma: float, target_vol_annual: float = TARGET_VOL_ANNUAL) -> float:
    """``g(t) = min(1.0, target / sigma_arena)``; ``g = 1.0`` if ``sigma_arena <= 0``."""
    if arena_sigma <= 0.0:
        return 1.0
    return min(1.0, float(target_vol_annual) / float(arena_sigma))


def base_equal_weights(eligible_symbols: Iterable[str], per_etf_cap: float = PER_ETF_CAP) -> dict:
    """``w_i = min(0.35, 1/|E|)`` — the cap binds only for ``|E| <= 2``.

    For ``|E| >= 3`` the cap is slack (``1/|E| <= 1/3 < 0.35``) and the base
    book is fully invested (sum = 1.0 up to float dust).  For ``|E| = 1..2``
    the residual is cash, never redistributed (spec-declared).
    """
    symbols = list(eligible_symbols)
    if not symbols:
        return {}
    return {s: min(float(per_etf_cap), 1.0 / len(symbols)) for s in symbols}


def defensive_target_weights(
    eligible_symbols: Iterable[str],
    arena_sigma: float,
    target_vol_annual: float = TARGET_VOL_ANNUAL,
    per_etf_cap: float = PER_ETF_CAP,
) -> dict:
    """Full target book (ETF weights + explicit CASH weight) for one decision.

    Returns ``{symbol: weight, ..., "CASH": cash_weight}``.  Deterministic in
    the injected eligible set and arena vol; no scored quantity is produced.
    """
    symbols = sorted(set(eligible_symbols))
    if not symbols:
        return {CASH_SYMBOL: 1.0}
    scalar = gross_scalar(arena_sigma, target_vol_annual)
    weights = {s: scalar * w for s, w in base_equal_weights(symbols, per_etf_cap).items()}
    gross = sum(weights.values())
    cash = 1.0 - gross
    if cash < 0.0 and cash > -_GROSS_TOLERANCE:
        cash = 0.0  # float dust only; gross stays <= 1.0 structurally
    weights[CASH_SYMBOL] = cash
    return weights


def book_gross(weights: dict) -> float:
    """Sum of ETF weights (CASH excluded) — gross exposure of a target book."""
    return sum(w for s, w in weights.items() if s != CASH_SYMBOL)


def two_way_turnover(previous_weights: dict, next_weights: dict) -> float:
    """Two-way turnover between consecutive target books: ``sum_i |w_i' - w_i|``.

    ETF names only; CASH absorbs the balance and is excluded to avoid
    double counting (each ETF delta is mirrored one-for-one by cash).
    A force-flat liquidation from a fully invested book therefore measures
    exactly the book's gross.
    """
    names = set(previous_weights) | set(next_weights)
    names.discard(CASH_SYMBOL)
    return sum(abs(float(next_weights.get(s, 0.0)) - float(previous_weights.get(s, 0.0))) for s in names)
