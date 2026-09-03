"""Frozen feature signals for the A5-SFV2-TREND-DEFENSIVE family (schedule-only).

Implements the preregistered feature definitions of
``research/proposals/stocks_free_v2/a5_arm1_tsm12_ivol.json``,
``a5_arm2_sma200_weekly.json`` and ``a5_arm3_tsm12_inverted_control.json``
exactly.  All functions are PURE: every series is INJECTED (issuer-reconstructed
total-return chains per amended FD2: raw closes x issuer-confirmed split factors
+ official SSGA/SPDR distribution records).  No data IO, no network, no keys,
and no returns/PnL/PF of any strategy is ever computed here (schedule-only lane).

Frozen feature semantics (spec quotes; nothing below is tuned):

* Arm 1/3 signal (``TIME_SERIES_MOMENTUM_SIGN_12M``):
  ``m_i(t) = TR_i(t) / TR_i(t-252) - 1`` on completed TR-chain sessions through
  decision date t; ELIGIBLE iff ``m > 0`` (anchor) / ``m < 0`` (inverted
  control); ``m == 0`` exactly -> INELIGIBLE (declared tie-break).
* Arm 2 signal (``PRICE_VS_SMA200_TREND_FILTER``):
  ``sma_i(t) = mean of TR_i over the last 200 completed TR-chain sessions
  inclusive of t``; ELIGIBLE iff ``TR_i(t) > sma_i(t)``; tie -> INELIGIBLE.
* Volatility estimator (all arms, ``REALIZED_VOL_SIMPLE_RETURN_STD``):
  ``sigma_i(t) = std(ddof=1)`` of the last 63 completed daily simple TR returns,
  annualized by ``sqrt(252)``; ``sigma_arena(t) = sqrt(mean over ELIGIBLE i of
  sigma_i(t)^2)`` — deterministic variance average, no covariance estimation
  (declared a priori simplification); empty eligible set -> ``sigma_arena = 0``.
"""

from __future__ import annotations

import math
from typing import Mapping, Sequence

# Frozen estimator constants (spec-defined; identical across all three arms).
TSMOM_LOOKBACK_SESSIONS = 252
SMA_WINDOW_SESSIONS = 200
VOL_WINDOW_SESSIONS = 63
VOL_DDOF = 1
ANNUALIZATION_SESSIONS = 252.0

DateLike = object  # datetime.date (kept annotation-free for flat importlib loading)


def _tr_at(tr_by_date: Mapping[DateLike, float], session: DateLike, symbol: str) -> float:
    value = tr_by_date.get(session)
    if value is None:
        raise KeyError(
            f"missing TR point for {symbol} on {session!r} "
            "(cohort census guarantees full coverage; fail closed)"
        )
    return float(value)


def _sessions_through(sessions: Sequence[DateLike], decision_date: DateLike) -> list:
    """Completed sessions with data available at a decision (no lookahead)."""
    return [s for s in sessions if s <= decision_date]


def feature_requirement_sessions(gate: str, lookback_sessions: int) -> int:
    """Completed TR sessions every cohort member needs before a decision at t.

    TSMOM needs ``TR_i(t - lookback)`` to exist, i.e. lookback + 1 points
    through t inclusive (the frozen ramp text says ">= 252 completed TR
    sessions"; the frozen formula ``m_i(t) = TR_i(t)/TR_i(t-252) - 1`` is the
    binding authority and strictly requires the t-252 endpoint, so 253 is the
    minimal faithful reading).  The SMA filter averages the last ``window``
    sessions inclusive of t, so exactly ``window`` points suffice.
    """
    if gate == "TSMOM_SIGN":
        return lookback_sessions + 1
    if gate == "SMA_ABOVE":
        return lookback_sessions
    raise ValueError(f"unknown gate kind {gate!r}")


def completed_session_count(
    tr_by_date: Mapping[DateLike, float],
    sessions: Sequence[DateLike],
    decision_date: DateLike,
) -> int:
    """Number of completed TR sessions for one symbol through ``decision_date``."""
    return sum(1 for s in _sessions_through(sessions, decision_date) if s in tr_by_date)


def tsmom_momentum(
    tr_by_date: Mapping[DateLike, float],
    sessions: Sequence[DateLike],
    symbol: str,
    decision_date: DateLike,
    lookback_sessions: int = TSMOM_LOOKBACK_SESSIONS,
) -> float:
    """``m = TR(t) / TR(t - lookback) - 1`` on completed sessions (no lookahead)."""
    completed = _sessions_through(sessions, decision_date)
    if len(completed) < lookback_sessions + 1:
        raise ValueError(
            f"{symbol}: TSMOM needs {lookback_sessions + 1} completed sessions "
            f"through {decision_date!r}, found {len(completed)}"
        )
    tr_now = _tr_at(tr_by_date, completed[-1], symbol)
    tr_past = _tr_at(tr_by_date, completed[-1 - lookback_sessions], symbol)
    return tr_now / tr_past - 1.0


def tsmom_eligible(
    tr_by_date: Mapping[DateLike, float],
    sessions: Sequence[DateLike],
    symbol: str,
    decision_date: DateLike,
    lookback_sessions: int = TSMOM_LOOKBACK_SESSIONS,
    inverted_sign: bool = False,
) -> bool:
    """Frozen sign gate: eligible iff ``m > 0`` (anchor) or ``m < 0`` (control).

    ``m == 0`` exactly -> INELIGIBLE under both signs (declared tie-break,
    measure-zero on real data).
    """
    momentum = tsmom_momentum(tr_by_date, sessions, symbol, decision_date, lookback_sessions)
    return momentum < 0.0 if inverted_sign else momentum > 0.0


def sma_value(
    tr_by_date: Mapping[DateLike, float],
    sessions: Sequence[DateLike],
    symbol: str,
    decision_date: DateLike,
    window_sessions: int = SMA_WINDOW_SESSIONS,
) -> float:
    """Mean TR over the last ``window`` completed sessions inclusive of t."""
    completed = _sessions_through(sessions, decision_date)
    if len(completed) < window_sessions:
        raise ValueError(
            f"{symbol}: SMA needs {window_sessions} completed sessions "
            f"through {decision_date!r}, found {len(completed)}"
        )
    window = completed[-window_sessions:]
    return sum(_tr_at(tr_by_date, s, symbol) for s in window) / float(window_sessions)


def sma_eligible(
    tr_by_date: Mapping[DateLike, float],
    sessions: Sequence[DateLike],
    symbol: str,
    decision_date: DateLike,
    window_sessions: int = SMA_WINDOW_SESSIONS,
) -> bool:
    """Frozen price-vs-SMA gate: eligible iff ``TR(t) > sma(t)``; tie -> INELIGIBLE."""
    tr_now = _tr_at(tr_by_date, _sessions_through(sessions, decision_date)[-1], symbol)
    return tr_now > sma_value(tr_by_date, sessions, symbol, decision_date, window_sessions)


def realized_vol_annualized(
    tr_values_in_order: Sequence[float],
    window_sessions: int = VOL_WINDOW_SESSIONS,
    ddof: int = VOL_DDOF,
    annualization_sessions: float = ANNUALIZATION_SESSIONS,
) -> float:
    """Annualized realized vol: ``std(ddof)`` of the last ``window`` simple returns * sqrt(252).

    ``tr_values_in_order`` are the completed TR-chain points through the
    decision date in session order; the estimator consumes the last
    ``window + 1`` points (``window`` daily simple returns).  Callers guarantee
    the ramp has already secured enough history (63 returns need 64 points,
    which is below every arm's feature requirement).
    """
    if len(tr_values_in_order) < window_sessions + 1:
        raise ValueError(
            f"realized vol needs {window_sessions + 1} completed TR points, "
            f"found {len(tr_values_in_order)}"
        )
    tail = [float(v) for v in tr_values_in_order[-(window_sessions + 1):]]
    returns = [tail[i] / tail[i - 1] - 1.0 for i in range(1, len(tail))]
    mean = sum(returns) / float(len(returns))
    squared = sum((r - mean) ** 2 for r in returns)
    variance = squared / float(len(returns) - ddof)
    return math.sqrt(variance) * math.sqrt(annualization_sessions)


def realized_vol_for_symbol(
    tr_by_date: Mapping[DateLike, float],
    sessions: Sequence[DateLike],
    symbol: str,
    decision_date: DateLike,
    window_sessions: int = VOL_WINDOW_SESSIONS,
) -> float:
    """Per-ETF realized vol on TR returns through ``decision_date`` (no lookahead)."""
    completed = _sessions_through(sessions, decision_date)
    values = [_tr_at(tr_by_date, s, symbol) for s in completed]
    return realized_vol_annualized(values, window_sessions=window_sessions)


def arena_volatility(symbol_sigmas: Mapping[str, float]) -> float:
    """``sigma_arena = sqrt(mean over ELIGIBLE i of sigma_i^2)``; empty -> 0.0.

    Deterministic equal-weight variance average over the eligible set only —
    no covariance estimation (declared simplification).  The empty-set case
    returns 0.0, which the defensive mapping reads as ``g = 1.0`` (declared
    deterministic tie-break); an empty eligible set is 100% cash regardless.
    """
    if not symbol_sigmas:
        return 0.0
    mean_variance = sum(float(s) ** 2 for s in symbol_sigmas.values()) / float(len(symbol_sigmas))
    return math.sqrt(mean_variance)
