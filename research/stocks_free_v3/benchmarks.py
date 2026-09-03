"""Frozen V3 benchmark semantics: four deterministic series builders.

Owner: lane A3, STOCKS-FREE-V3 P1 (PLAN_stocks.md section 9 A3, deliverable
4: "Freeze benchmark semantics before proposals").  These are DETERMINISTIC
BENCHMARK SERIES BUILDERS with hand-computed golden tests on synthetic
inputs — NOT scored strategy runs, and never executed on real S1 data.

The four frozen constructions
-----------------------------
1. ``FLAT_HARD`` — 0.0 return every session; level 1.0.  The hard floor any
   arm must beat.
2. ``SPY_TOTAL_RETURN`` — issuer total return of SPY: split-adjusted raw
   close chained with issuer distributions,
   ``r(d) = (sadj(d) + dist(d)) / sadj(prev(d)) - 1`` where ``sadj`` is the
   raw close multiplied by the cumulative split factor over all effective
   dates ON OR BEFORE ``d`` (factor semantics: a 2:1 split has ``factor =
   2.0``; the first post-split close is doubled so the series is continuous
   through the split and a split without a distribution yields a 0.0
   return).  This is the V2 issuer-TR reconstruction semantics (FD2
   amended).
3. ``EQUAL_WEIGHT_SECTOR_TOTAL_RETURN`` — equal weight across the ten sector
   ETFs (the cohort minus SPY), rebalanced daily:
   ``r_ew(d) = mean_i r_i(d)``.  Members missing a return on any session
   fail closed.
4. ``RISK_MATCHED_SPY_CONTEXT`` — SPY total return scaled EX ANTE by an
   arm's frozen gross/vol rule: the scaling applied on session ``d`` is a
   function ONLY of SPY TR returns realized strictly before ``d`` (inside
   the benchmark window), never of ``d`` itself or later — so the benchmark
   cannot look ahead.  ``s(d) = clip(target_daily_vol / realized_vol,
   min_gross, max_gross)`` with ``realized_vol`` the population standard
   deviation (ddof=0, frozen) of the last ``lookback_sessions`` available
   returns; fewer available returns than the lookback scales by
   ``min_gross`` (frozen conservative default); zero realized vol scales by
   ``max_gross``.

Every builder returns a :class:`BenchmarkSeries` carrying a
``definition_digest`` (sha256 over the canonical rule payload) and a
``series_digest`` (sha256 over the canonical dates/returns/levels payload),
so a V3 trial identity can pin the exact benchmark bytes.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Mapping, Sequence

from research.assets.common.contracts import canonical_json, require_finite_float, require_token
from research.stocks_free_v3.authority import BENCHMARK_SYMBOL

BENCHMARK_FLAT_HARD = "FLAT_HARD"
BENCHMARK_SPY_TOTAL_RETURN = "SPY_TOTAL_RETURN"
BENCHMARK_EW_SECTOR_TOTAL_RETURN = "EQUAL_WEIGHT_SECTOR_TOTAL_RETURN"
BENCHMARK_RISK_MATCHED_SPY = "RISK_MATCHED_SPY_CONTEXT"

BENCHMARK_SCHEMA = "stocks_free_v3/benchmark@1"


class BenchmarkError(ValueError):
    """Raised when a benchmark cannot be built from the declared inputs."""


@dataclass(frozen=True)
class VolScalingRule:
    """An arm's frozen ex-ante gross/vol scaling rule.

    ``realized_vol`` is the population standard deviation (ddof=0, frozen
    here and not configurable) of the last ``lookback_sessions`` realized
    SPY TR returns strictly before the decision session.  ``scaling =
    clip(target_daily_vol / realized_vol, min_gross, max_gross)``; a
    zero realized vol scales by ``max_gross``; fewer realized returns than
    the lookback scales by ``min_gross`` (the only implemented
    insufficient-history policy, frozen conservative).
    """

    lookback_sessions: int
    target_daily_vol: float
    min_gross: float
    max_gross: float
    insufficient_history: str = "MIN_GROSS"

    def __post_init__(self) -> None:
        if (
            isinstance(self.lookback_sessions, bool)
            or not isinstance(self.lookback_sessions, int)
            or self.lookback_sessions < 1
        ):
            raise ValueError("lookback_sessions must be a positive int")
        require_finite_float(self.target_daily_vol, "target_daily_vol", positive=True)
        require_finite_float(self.min_gross, "min_gross")
        require_finite_float(self.max_gross, "max_gross")
        if self.min_gross < 0.0:
            raise ValueError("min_gross must be >= 0")
        if self.max_gross < self.min_gross:
            raise ValueError("max_gross must be >= min_gross")
        if self.insufficient_history != "MIN_GROSS":
            raise ValueError(
                "insufficient_history must be MIN_GROSS (frozen conservative default)"
            )

    @property
    def kind(self) -> str:
        return "EX_ANTE_GROSS_VOL_CLIP_DD0"

    def to_payload(self) -> dict:
        return {
            "kind": self.kind,
            "lookback_sessions": self.lookback_sessions,
            "target_daily_vol": self.target_daily_vol,
            "min_gross": self.min_gross,
            "max_gross": self.max_gross,
            "insufficient_history": self.insufficient_history,
        }

    @property
    def digest(self) -> str:
        return hashlib.sha256(canonical_json(self.to_payload()).encode("utf-8")).hexdigest()

    def scale(self, realized_returns: Sequence[float]) -> float:
        """Ex-ante scaling from returns realized STRICTLY BEFORE the decision."""
        history = list(realized_returns)[-self.lookback_sessions :]
        if len(history) < self.lookback_sessions:
            return self.min_gross
        mean = sum(history) / len(history)
        variance = sum((r - mean) ** 2 for r in history) / len(history)  # ddof=0
        vol = math.sqrt(variance)
        if vol == 0.0:
            return self.max_gross
        raw = self.target_daily_vol / vol
        return min(max(raw, self.min_gross), self.max_gross)


#: V3 baseline rule frozen at P1: 63-session lookback, 1% daily target vol,
#: gross clipped to [0.0, 2.0].
DEFAULT_VOL_SCALING_RULE = VolScalingRule(
    lookback_sessions=63,
    target_daily_vol=0.01,
    min_gross=0.0,
    max_gross=2.0,
)


# --- price transformation ------------------------------------------------------- #


def split_adjusted_closes(
    raw_close: Mapping[str, float],
    split_factors: Mapping[str, float],
) -> dict[str, float]:
    """Raw closes multiplied by the cumulative split factor over effective
    dates on or before each observation (factor semantics: a 2:1 split has
    ``factor = 2.0``, the first post-split close is doubled, and the series
    is continuous through the split).  Same convention as the V2 issuer-TR
    reconstruction: a 100 -> 50 raw close across a 2:1 split with no
    distribution reconstructs a 0.0 return.
    """
    effective = sorted(
        (eff, require_finite_float(f, f"split factor {eff}", positive=True))
        for eff, f in split_factors.items()
    )
    out: dict[str, float] = {}
    for d in sorted(raw_close):
        cumulative = 1.0
        for eff, factor in effective:
            if d >= eff:
                cumulative *= factor
        sadj = float(raw_close[d]) * cumulative
        require_finite_float(sadj, f"sadj {d}", positive=True)
        out[d] = sadj
    return out


def issuer_total_return_daily(
    raw_close: Mapping[str, float],
    distributions: Mapping[str, float],
    split_factors: Mapping[str, float],
) -> tuple[list[str], list[float]]:
    """Issuer TR daily returns over consecutive observations of one symbol.

    ``r(d) = (sadj(d) + dist(d)) / sadj(prev(d)) - 1`` with ``dist(d)`` the
    per-share cash distribution with ex-date ``d`` (0.0 when none).  Returns
    (ascending dates, returns), one return per observation after the first.
    """
    sadj = split_adjusted_closes(raw_close, split_factors)
    dates = sorted(sadj)
    if len(dates) < 2:
        raise BenchmarkError("issuer TR needs at least two observations")
    out_dates: list[str] = []
    out_returns: list[float] = []
    for previous, current in zip(dates, dates[1:]):
        dist = float(distributions.get(current, 0.0))
        require_finite_float(dist, f"distribution {current}")
        if dist < 0.0:
            raise BenchmarkError(f"negative distribution on {current}")
        r = (sadj[current] + dist) / sadj[previous] - 1.0
        require_finite_float(r, f"TR return {current}")
        out_dates.append(current)
        out_returns.append(r)
    return out_dates, out_returns


# --- benchmark series ------------------------------------------------------------ #


@dataclass(frozen=True)
class BenchmarkSeries:
    """One deterministic benchmark series over a declared session window."""

    benchmark_id: str
    kind: str
    window_start: str
    window_end: str
    dates: tuple[str, ...]
    returns: tuple[float | None, ...]
    levels: tuple[float, ...]
    definition_digest: str
    rule: VolScalingRule | None = None
    scalings: tuple[float | None, ...] = ()

    def __post_init__(self) -> None:
        require_token(self.benchmark_id, "benchmark_id")
        if not (len(self.dates) == len(self.returns) == len(self.levels)):
            raise BenchmarkError("dates/returns/levels length mismatch")
        if not self.dates:
            raise BenchmarkError("empty benchmark series")
        if list(self.dates) != sorted(self.dates):
            raise BenchmarkError("benchmark dates must ascend")
        if self.levels[0] != 1.0:
            raise BenchmarkError("benchmark level must normalize to 1.0 at window start")
        if self.returns[0] is not None:
            raise BenchmarkError("the first session of a window carries no return")
        if self.scalings and len(self.scalings) != len(self.dates):
            raise BenchmarkError("scalings length mismatch")
        expected = 1.0
        for i, r in enumerate(self.returns):
            if i == 0:
                continue
            if r is None:
                raise BenchmarkError(f"missing return at {self.dates[i]}")
            expected *= 1.0 + r
            if not math.isclose(expected, self.levels[i], rel_tol=1e-12, abs_tol=1e-15):
                raise BenchmarkError(
                    f"level chain broken at {self.dates[i]}: {self.levels[i]} vs {expected}"
                )

    @property
    def total_return(self) -> float:
        return self.levels[-1] - 1.0

    def series_digest(self) -> str:
        payload = {
            "schema": BENCHMARK_SCHEMA,
            "benchmark_id": self.benchmark_id,
            "kind": self.kind,
            "window": [self.window_start, self.window_end],
            "dates": list(self.dates),
            "returns": list(self.returns),
            "levels": list(self.levels),
        }
        return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _window_sessions(
    sessions: Sequence[str], window_start: str, window_end: str
) -> list[str]:
    if window_end < window_start:
        raise BenchmarkError("window end precedes window start")
    in_window = [d for d in sessions if window_start <= d <= window_end]
    if not in_window:
        raise BenchmarkError("no declared sessions inside the window")
    if in_window[0] != window_start or in_window[-1] != window_end:
        raise BenchmarkError(
            "window bounds must themselves be declared sessions "
            f"({window_start}..{window_end} vs {in_window[0]}..{in_window[-1]})"
        )
    return in_window


def _definition_digest(
    benchmark_id: str,
    kind: str,
    window_start: str,
    window_end: str,
    *,
    rule: VolScalingRule | None = None,
    members: Sequence[str] = (),
) -> str:
    payload = {
        "schema": BENCHMARK_SCHEMA,
        "benchmark_id": benchmark_id,
        "kind": kind,
        "window": [window_start, window_end],
        "members": list(members),
        "rule": rule.to_payload() if rule is not None else None,
    }
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _member_tr_returns(
    symbol: str,
    raw_close: Mapping[str, float],
    distributions: Mapping[str, float],
    split_factors: Mapping[str, float],
    window_sessions: Sequence[str],
) -> dict[str, float]:
    """Issuer TR returns of one member keyed by session (second onward).

    Fails closed unless every session after the first has an issuer-TR
    return computed against the IMMEDIATELY preceding declared session.
    """
    dates, returns = issuer_total_return_daily(raw_close, distributions, split_factors)
    by_date = dict(zip(dates, returns))
    out: dict[str, float] = {}
    for previous, current in zip(window_sessions, window_sessions[1:]):
        if current not in by_date:
            raise BenchmarkError(
                f"{symbol}: no issuer-TR return on session {current} "
                "(missing observation or broken session adjacency)"
            )
        if previous not in raw_close:
            raise BenchmarkError(
                f"{symbol}: session {current} lacks a preceding observation "
                f"({previous}); the TR return would span a gap"
            )
        out[current] = by_date[current]
    return out


def build_flat_benchmark(
    sessions: Sequence[str],
    window_start: str,
    window_end: str,
) -> BenchmarkSeries:
    """Benchmark 1: the flat hard benchmark — 0.0 return, level 1.0."""
    in_window = _window_sessions(sessions, window_start, window_end)
    definition = _definition_digest(BENCHMARK_FLAT_HARD, "FLAT", window_start, window_end)
    return BenchmarkSeries(
        benchmark_id=BENCHMARK_FLAT_HARD,
        kind="FLAT",
        window_start=window_start,
        window_end=window_end,
        dates=tuple(in_window),
        returns=tuple([None] + [0.0] * (len(in_window) - 1)),
        levels=tuple([1.0] * len(in_window)),
        definition_digest=definition,
    )


def build_spy_total_return(
    raw_close: Mapping[str, float],
    distributions: Mapping[str, float],
    split_factors: Mapping[str, float],
    sessions: Sequence[str],
    window_start: str,
    window_end: str,
    *,
    benchmark_id: str = BENCHMARK_SPY_TOTAL_RETURN,
) -> BenchmarkSeries:
    """Benchmark 2: SPY issuer total return over the window."""
    in_window = _window_sessions(sessions, window_start, window_end)
    tr = _member_tr_returns(
        BENCHMARK_SYMBOL, raw_close, distributions, split_factors, in_window
    )
    returns: list[float | None] = [None]
    levels: list[float] = [1.0]
    for d in in_window[1:]:
        r = tr[d]
        returns.append(r)
        levels.append(levels[-1] * (1.0 + r))
    definition = _definition_digest(benchmark_id, "SPY_TR", window_start, window_end)
    return BenchmarkSeries(
        benchmark_id=benchmark_id,
        kind="SPY_TR",
        window_start=window_start,
        window_end=window_end,
        dates=tuple(in_window),
        returns=tuple(returns),
        levels=tuple(levels),
        definition_digest=definition,
    )


def build_equal_weight_sector_total_return(
    raw_closes: Mapping[str, Mapping[str, float]],
    distributions: Mapping[str, Mapping[str, float]],
    split_factors: Mapping[str, Mapping[str, float]],
    sector_symbols: Sequence[str],
    sessions: Sequence[str],
    window_start: str,
    window_end: str,
    *,
    benchmark_id: str = BENCHMARK_EW_SECTOR_TOTAL_RETURN,
) -> BenchmarkSeries:
    """Benchmark 3: equal weight (daily rebalanced) across the sector ETFs.

    The V3-frozen membership is the cohort minus SPY (ten sector ETFs,
    :data:`research.stocks_free_v3.authority.SECTOR_SYMBOLS`); a synthetic
    membership is only for golden tests.
    """
    symbols = sorted(set(sector_symbols))
    if not symbols:
        raise BenchmarkError("equal-weight benchmark needs at least one member")
    in_window = _window_sessions(sessions, window_start, window_end)
    member_returns = {
        s: _member_tr_returns(
            s,
            raw_closes[s],
            distributions.get(s, {}),
            split_factors.get(s, {}),
            in_window,
        )
        for s in symbols
    }
    weight = 1.0 / len(symbols)
    returns: list[float | None] = [None]
    levels: list[float] = [1.0]
    for d in in_window[1:]:
        r_ew = weight * sum(member_returns[s][d] for s in symbols)
        require_finite_float(r_ew, f"EW return {d}")
        returns.append(r_ew)
        levels.append(levels[-1] * (1.0 + r_ew))
    definition = _definition_digest(
        benchmark_id, "EW_SECTOR_TR", window_start, window_end, members=symbols
    )
    return BenchmarkSeries(
        benchmark_id=benchmark_id,
        kind="EW_SECTOR_TR",
        window_start=window_start,
        window_end=window_end,
        dates=tuple(in_window),
        returns=tuple(returns),
        levels=tuple(levels),
        definition_digest=definition,
    )


def build_risk_matched_spy(
    raw_close: Mapping[str, float],
    distributions: Mapping[str, float],
    split_factors: Mapping[str, float],
    sessions: Sequence[str],
    window_start: str,
    window_end: str,
    rule: VolScalingRule,
    *,
    benchmark_id: str = BENCHMARK_RISK_MATCHED_SPY,
) -> BenchmarkSeries:
    """Benchmark 4: SPY TR scaled EX ANTE by the arm's frozen gross/vol rule.

    The scaling on session ``d`` uses only realized SPY TR returns STRICTLY
    BEFORE ``d`` (inside this benchmark window).  Perturbing a session's own
    return changes the scaled series at that session ONLY through the
    unscaled SPY return, never through the scaling — the ex-ante property the
    golden tests assert.
    """
    if not isinstance(rule, VolScalingRule):
        raise BenchmarkError("risk-matched benchmark requires a frozen VolScalingRule")
    in_window = _window_sessions(sessions, window_start, window_end)
    tr = _member_tr_returns(
        BENCHMARK_SYMBOL, raw_close, distributions, split_factors, in_window
    )
    returns: list[float | None] = [None]
    levels: list[float] = [1.0]
    scalings: list[float | None] = [None]
    realized: list[float] = []
    for d in in_window[1:]:
        scale = rule.scale(realized)
        realized.append(tr[d])
        returns.append(scale * tr[d])
        levels.append(levels[-1] * (1.0 + returns[-1]))
        scalings.append(scale)
    definition = _definition_digest(
        benchmark_id, "RISK_MATCHED_SPY", window_start, window_end, rule=rule
    )
    return BenchmarkSeries(
        benchmark_id=benchmark_id,
        kind="RISK_MATCHED_SPY",
        window_start=window_start,
        window_end=window_end,
        dates=tuple(in_window),
        returns=tuple(returns),
        levels=tuple(levels),
        definition_digest=definition,
        rule=rule,
        scalings=tuple(scalings),
    )


__all__ = [
    "BENCHMARK_EW_SECTOR_TOTAL_RETURN",
    "BENCHMARK_FLAT_HARD",
    "BENCHMARK_RISK_MATCHED_SPY",
    "BENCHMARK_SCHEMA",
    "BENCHMARK_SPY_TOTAL_RETURN",
    "BenchmarkError",
    "BenchmarkSeries",
    "DEFAULT_VOL_SCALING_RULE",
    "VolScalingRule",
    "build_equal_weight_sector_total_return",
    "build_flat_benchmark",
    "build_risk_matched_spy",
    "build_spy_total_return",
    "issuer_total_return_daily",
    "split_adjusted_closes",
]
