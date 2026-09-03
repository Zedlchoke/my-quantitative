"""PIT feature computation for SFV3-A5-IDIO-SHOCK-REVERSAL (frozen spec).

Signal, exactly as frozen (selection_freeze.json families[0] ``signal`` and
proposal section 4 "Formation (exact, frozen constants)"):

* ``r_i,s``  — issuer-TR daily return of ETF i (SPY included as the market
  factor) built by ``research.stocks_free_v3.benchmarks.issuer_total_return_daily``
  upstream; this module consumes the returns, it never re-derives them;
* ``beta_i(t)`` — OLS slope of ``r_i`` on ``r_SPY`` over the trailing 60
  completed sessions ``[t-59 .. t]``, inclusive of ``t``;
* ``epsilon_i,s(t) = r_i,s - beta_i(t) * r_SPY,s`` for ``s`` in that window;
* ``sigma_i(t)`` — population standard deviation (ddof=0) of the residuals;
* ``z_i(t) = epsilon_i,t(t) / sigma_i(t)`` — today's residual scaled by the
  window's residual sigma.

Determinism: every reduction is a fixed-order plain-Python ``math.fsum`` over
explicitly ordered sequences, so identical inputs produce bit-identical
features on every run and via every code path (direct per-session recompute
vs. regenerated from a cached :class:`FeatureFrame` — equality is pinned by
test).

Completed-session PIT only: ``z`` at session ``t`` uses nothing after ``t``.
A session with fewer than ``lookback_sessions`` available returns carries no
feature.  A degenerate window (zero SPY variance, so the OLS slope is
undefined) fails closed.  A zero sigma cannot produce a defined ``z`` (the
frozen quantity ``residual / sigma`` is undefined there); such sessions carry
``z = None`` and are therefore never eligible to trigger — the conservative
reading of the freeze, applied identically to all three arms.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, Sequence

#: Frozen formation constants (selection_freeze.json families[0]).
BETA_LOOKBACK_SESSIONS = 60
RESIDUAL_DDOF = 0

#: A6/TOM keeps SPY as benchmark only; the trigger universe is the 10 sectors.
FEATURE_SCHEMA = "stocks_free_v3/family_idio_shock/features@1"


class FeatureError(ValueError):
    """Raised when a frozen feature cannot be formed (fail closed)."""


@dataclass(frozen=True)
class FeatureFrame:
    """Per-session idio-shock features for the 10 sector ETFs.

    ``z[sessions[k]][symbol]`` is the frozen ``z_i(t)`` (``None`` where
    undefined — warmup sessions and zero-sigma sessions).  ``beta`` and
    ``sigma`` carry the same keying where defined.  Sessions before the first
    fully-populated 60-session window are absent from the mappings.
    """

    sessions: tuple[str, ...]
    symbols: tuple[str, ...]
    beta: Mapping[str, Mapping[str, float]]
    sigma: Mapping[str, Mapping[str, float]]
    z: Mapping[str, Mapping[str, float | None]]

    @property
    def feature_sessions(self) -> tuple[str, ...]:
        """Sessions carrying a (possibly None) z observation."""
        return tuple(self.z.keys())

    def triggered(self, session: str, symbol: str, threshold: float) -> bool:
        """True exactly when a defined z breaches the signed threshold."""
        value = self.z[session].get(symbol)
        return value is not None and value <= threshold


def ols_slope(xs: Sequence[float], ys: Sequence[float]) -> float:
    """OLS slope of ``ys`` on ``xs`` (population moments, fixed order).

    ``sum((x-mx)(y-my)) / sum((x-mx)^2)`` with means as exact ``fsum/n``.
    Zero x-variance raises :class:`FeatureError` (the slope is undefined).
    """
    n = len(xs)
    if n != len(ys) or n == 0:
        raise FeatureError(f"ols_slope length mismatch: {n} vs {len(ys)}")
    mx = math.fsum(xs) / n
    my = math.fsum(ys) / n
    sxy = math.fsum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = math.fsum((x - mx) ** 2 for x in xs)
    if sxx == 0.0:
        raise FeatureError("ols_slope undefined: zero x-variance in the window")
    return sxy / sxx


def population_std(values: Sequence[float]) -> float:
    """Population (ddof=0) standard deviation, fixed-order fsum."""
    n = len(values)
    if n == 0:
        raise FeatureError("population_std of an empty sequence")
    mean = math.fsum(values) / n
    variance = math.fsum((v - mean) ** 2 for v in values) / n
    return math.sqrt(variance)


def compute_features(
    sessions: Sequence[str],
    returns: Mapping[str, Mapping[str, float]],
    sector_symbols: Sequence[str],
    benchmark_symbol: str,
    *,
    lookback_sessions: int = BETA_LOOKBACK_SESSIONS,
) -> FeatureFrame:
    """Compute the frozen z features for every eligible completed session.

    ``returns`` maps each symbol to ``{session: issuer-TR return}``; the
    first session of the calendar naturally carries no return (issuer TR
    starts at the second observation).  A window missing ANY of the
    ``lookback_sessions`` returns for the sector symbol or the benchmark
    symbol yields no feature for that session (warmup, fail-closed to
    absence — never a partial-window estimate).  A sector symbol missing a
    return inside an otherwise-complete window is a data break
    (:class:`FeatureError`).
    """
    sessions = list(sessions)
    if len(sessions) < lookback_sessions:
        return FeatureFrame(
            sessions=tuple(sessions),
            symbols=tuple(sector_symbols),
            beta={}, sigma={}, z={},
        )
    symbols = tuple(sorted(set(sector_symbols)))
    if benchmark_symbol in symbols:
        raise FeatureError("the benchmark symbol must not be in the trigger universe")
    beta_out: dict[str, dict[str, float]] = {}
    sigma_out: dict[str, dict[str, float]] = {}
    z_out: dict[str, dict[str, float | None]] = {}
    spy = returns.get(benchmark_symbol)
    if spy is None:
        raise FeatureError(f"no returns supplied for the benchmark {benchmark_symbol!r}")
    for end in range(lookback_sessions - 1, len(sessions)):
        window = sessions[end - lookback_sessions + 1 : end + 1]
        if any(s not in spy for s in window):
            continue  # benchmark warmup: no feature anywhere this session
        xs = [spy[s] for s in window]
        beta_row: dict[str, float] = {}
        sigma_row: dict[str, float] = {}
        z_row: dict[str, float | None] = {}
        for symbol in symbols:
            series = returns.get(symbol)
            if series is None:
                raise FeatureError(f"no returns supplied for sector {symbol!r}")
            missing = [s for s in window if s not in series]
            if missing:
                raise FeatureError(
                    f"{symbol}: missing issuer-TR return(s) in the window ending "
                    f"{sessions[end]} (first {missing[0]}); the cohort must be complete"
                )
            ys = [series[s] for s in window]
            beta = ols_slope(xs, ys)
            residuals = [y - beta * x for x, y in zip(xs, ys)]
            sigma = population_std(residuals)
            beta_row[symbol] = beta
            sigma_row[symbol] = sigma
            # z is the frozen quantity residual_t / sigma_t; it is undefined
            # (and never triggering) where sigma == 0.
            z_row[symbol] = (
                residuals[-1] / sigma if sigma != 0.0 else None
            )
        session = sessions[end]
        beta_out[session] = beta_row
        sigma_out[session] = sigma_row
        z_out[session] = z_row
    return FeatureFrame(
        sessions=tuple(sessions),
        symbols=symbols,
        beta=beta_out,
        sigma=sigma_out,
        z=z_out,
    )


__all__ = [
    "BETA_LOOKBACK_SESSIONS",
    "FEATURE_SCHEMA",
    "RESIDUAL_DDOF",
    "FeatureError",
    "FeatureFrame",
    "compute_features",
    "ols_slope",
    "population_std",
]
