"""Frozen feature/schedule computation for V11-SEED-LOTTERY-MAX-SKEW.

Everything in this module is a pure, deterministic function of the injected
completed-bar inputs.  The frozen contract
(``research/control/v11_run/selection_freeze_specs/V11-SEED-LOTTERY-MAX-SKEW.json``)
pins:

* window ``2025-08-22T00:00:00Z .. 2026-08-21T00:00:00Z``;
* decisions Mondays 00:00:00Z, features from COMPLETED 15m bars only;
* one declared execution lag: the fill event is the covering bar
  (``derived_open <= D < close``) exactly like the repo fill clock
  ``next_allowed_event_after_signal_bar_close``;
* daily UTC aggregation of 15m closes; BTC-residualised dailies via a 90d
  rolling daily beta vs BTCUSDT (the benchmark-excluded context leg);
* anchor ``LOT-RESMAX-7D-W``: 7d max daily residual return, low-minus-high
  residual-MAX quintile book;
* neighbour ``LOT-RESSKEW-30D-W``: 30d rolling skew of residual dailies,
  low-minus-high residual-skew quintile book;
* control ``LOT-RESMAX-7D-W-INV``: sign-inverted anchor book;
* 3 chronological folds F0/F1/F2 pinned by the freeze date ranges with
  force-flat at fold boundaries (no holding may cross a fold);
* BTC beta-neutral book construction from the frozen 90d daily beta;
* A7-N reversal-exposure diagnostic (per-stamp cross-sectional Spearman rho
  of the arm feature vs the 7d reversal proxy) -- DIAGNOSTIC ONLY, never a
  signal input.

No randomness, no wall-clock reads, no parameter beyond the frozen spec.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, Optional, Sequence

DAY_NS = 86_400_000_000_000
BAR_NS = 900_000_000_000

#: Frozen feature windows (spec: formation_days 7 / 30; beta 90d rolling).
BETA_WINDOW_DAYS = 90
MAX_WINDOW_DAYS = 7
SKEW_WINDOW_DAYS = 30
#: Reversal-exposure diagnostic window (A7-N OBJ: REV7 margin -0.4642).
REV_WINDOW_DAYS = 7
#: PIT listing/history filter: consecutive complete daily returns required
#: before a stamp (90 beta + 30 formation windows, uniform across arms).
HISTORY_DAYS_REQUIRED = BETA_WINDOW_DAYS + SKEW_WINDOW_DAYS
#: Active-trading filter: a completed bar within the trailing 48h.
ACTIVE_BAR_MAX_AGE_NS = 48 * 3600 * 1_000_000_000
#: PIT dollar-volume filter window (A1/A9-F prewindow convention).
DV_WINDOW_DAYS = 28
#: A complete UTC day aggregates exactly 96 fifteen-minute bars.
BARS_PER_DAY = 96
#: Quintile book: quintile count.
QUINTILES = 5
#: Minimum eligible names so each quintile leg holds >= 2 names and every
#: single-symbol weight stays <= the 0.30 adapter weight cap.
MIN_ELIGIBLE = 2 * QUINTILES
#: Adapter weight cap (protocol.DEFAULT_WEIGHT_CAP_MAX).
WEIGHT_CAP = 0.30
GROSS_TARGET = 1.0

#: Frozen feature kind per arm (anchor = residual MAX, neighbour = residual
#: skew; the causal control reuses the anchor feature with a flipped book).
FEATURE_KIND_RESMAX = "resmax"
FEATURE_KIND_RESSKEW = "resskew"

WINDOW_START_ISO = "2025-08-22T00:00:00Z"
WINDOW_END_ISO = "2026-08-21T00:00:00Z"

#: Frozen fold date ranges (spec `common.folds`), half-open except the last.
FOLD_RANGES: tuple[tuple[str, str, str], ...] = (
    ("F0", "2025-08-22", "2025-12-21"),
    ("F1", "2025-12-22", "2026-04-21"),
    ("F2", "2026-04-22", "2026-08-21"),
)

STATUS_OK = "OK"
STATUS_SKIP_NO_SELECTION = "SKIP_NO_SELECTION"
REASON_FOLD_BOUNDARY_FORCE_FLAT = "fold_boundary_force_flat"
REASON_BELOW_MIN_ELIGIBLE = "below_min_eligible_names"
REASON_WEIGHT_CAP = "weight_cap_breach_fail_closed"


class SpecViolation(ValueError):
    """A frozen-spec input condition failed (fail closed, never guessed)."""


# --------------------------------------------------------------------------- #
# Calendar helpers
# --------------------------------------------------------------------------- #
def _utc_midnight(day: str) -> int:
    """UTC midnight epoch ns of an ISO date ``YYYY-MM-DD`` (deterministic)."""
    import datetime as _dt

    date = _dt.date(int(day[0:4]), int(day[5:7]), int(day[8:10]))
    return int(
        _dt.datetime(date.year, date.month, date.day, tzinfo=_dt.timezone.utc).timestamp()
    ) * 1_000_000_000


def day_index(ns: int) -> int:
    """UTC day index (floor) of an epoch-ns stamp."""
    return int(ns) // DAY_NS


def mondays_in_window(start_ns: int, end_ns: int) -> tuple[int, ...]:
    """Mondays 00:00:00Z with ``start_ns < m <= end_ns`` (decision clock)."""
    import datetime as _dt

    first = ((start_ns // DAY_NS) + 1) * DAY_NS
    out = []
    cursor = first
    while cursor <= end_ns:
        weekday = _dt.datetime.fromtimestamp(
            cursor / 1e9, tz=_dt.timezone.utc
        ).weekday()
        if weekday == 0:  # Monday
            out.append(int(cursor))
        cursor += DAY_NS
    return tuple(out)


def build_schedule_instants(
    *, window_start_iso: str = WINDOW_START_ISO, window_end_iso: str = WINDOW_END_ISO
) -> tuple[int, ...]:
    """Frozen schedule: Monday decisions + terminal force-flat at window end.

    The final instant is the window-end boundary where every holding is
    force-flattened (adapter terminal edge, never an open decision).
    """
    start_ns = _utc_midnight(window_start_iso[:10])
    end_ns = _utc_midnight(window_end_iso[:10])
    decisions = [m for m in mondays_in_window(start_ns, end_ns) if m < end_ns]
    if len(decisions) < 2:
        raise SpecViolation("frozen window must contain at least two Monday stamps")
    return tuple(decisions) + (end_ns,)


def fold_of_instant(instant_ns: int) -> str:
    """Fold label of a schedule instant under the frozen date ranges."""
    for label, start, end in FOLD_RANGES:
        if _utc_midnight(start) <= instant_ns <= _utc_midnight(end):
            return label
    raise SpecViolation(f"instant {instant_ns} outside every frozen fold range")


def fold_force_flat_instants(instants: Sequence[int]) -> frozenset[int]:
    """Open instants at which a fold boundary forces the book flat, plus the
    terminal force-flat edge.

    The LAST open (non-terminal) instant of every fold carries an empty book
    so no holding can cross a fold boundary (freeze fold_policy); the final
    schedule instant is the terminal force-flat boundary itself.
    """
    open_instants = [int(v) for v in instants[:-1]]
    by_fold: dict[str, list[int]] = {}
    for instant in open_instants:
        by_fold.setdefault(fold_of_instant(instant), []).append(instant)
    boundary = frozenset(members[-1] for members in by_fold.values() if members)
    return boundary | {int(instants[-1])}


# --------------------------------------------------------------------------- #
# Injected daily inputs (immutable view over completed bars only)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class DailyFrame:
    """Complete-day UTC aggregates of one symbol's completed 15m bars.

    ``closes[d]`` is the LAST 15m close of UTC day ``d``; a day is present
    only when exactly ``BARS_PER_DAY`` bars completed that day (no forward
    fill, no partial-day substitutes).  ``dollar_volume[d]`` is that day's
    completed quote-volume sum.
    """

    closes: Mapping[int, float]
    dollar_volume: Mapping[int, float]

    def close(self, day: int) -> Optional[float]:
        return self.closes.get(int(day))

    def daily_return(self, day: int) -> Optional[float]:
        """Return of day ``day`` vs ``day-1`` (both days must be complete)."""
        previous = self.closes.get(int(day) - 1)
        current = self.closes.get(int(day))
        if previous is None or current is None or previous <= 0.0:
            return None
        return current / previous - 1.0


def aggregate_daily(bars: Sequence[Mapping[str, float]]) -> DailyFrame:
    """Aggregate completed 15m bars into a :class:`DailyFrame`.

    ``bars`` elements carry ``ts_event_ns`` (CLOSE stamp) and ``close`` /
    ``quote_volume``.  A day enters the frame only with exactly 96 completed
    bars; anything else is unavailable for that day (fail closed).
    """
    per_day: dict[int, list[float]] = {}
    per_day_qv: dict[int, float] = {}
    for bar in bars:
        day = day_index(int(bar["ts_event_ns"]))
        per_day.setdefault(day, []).append(float(bar["close"]))
        per_day_qv[day] = per_day_qv.get(day, 0.0) + float(bar["quote_volume"])
    closes: dict[int, float] = {}
    dollar_volume: dict[int, float] = {}
    for day, values in per_day.items():
        if len(values) != BARS_PER_DAY:
            continue
        closes[day] = values[-1]  # bars injected in ascending close order
        dollar_volume[day] = per_day_qv[day]
    return DailyFrame(closes=closes, dollar_volume=dollar_volume)


# --------------------------------------------------------------------------- #
# Frozen statistics (closed-form, deterministic)
# --------------------------------------------------------------------------- #
def rolling_beta(
    symbol_returns: Sequence[float], market_returns: Sequence[float]
) -> Optional[float]:
    """OLS beta of the symbol's dailies on BTC's dailies over one window."""
    n = len(symbol_returns)
    if n != BETA_WINDOW_DAYS or len(market_returns) != BETA_WINDOW_DAYS:
        return None
    mean_s = math.fsum(symbol_returns) / n
    mean_m = math.fsum(market_returns) / n
    cov = math.fsum(
        (s - mean_s) * (m - mean_m)
        for s, m in zip(symbol_returns, market_returns)
    )
    var = math.fsum((m - mean_m) ** 2 for m in market_returns)
    if var <= 0.0:
        return None
    return cov / var


def sample_skew(values: Sequence[float]) -> Optional[float]:
    """Moment-coefficient skewness g1 = m3 / m2**1.5 over the window."""
    n = len(values)
    if n != SKEW_WINDOW_DAYS:
        return None
    mean = math.fsum(values) / n
    m2 = math.fsum((v - mean) ** 2 for v in values) / n
    m3 = math.fsum((v - mean) ** 3 for v in values) / n
    if m2 <= 0.0:
        return None
    return m3 / (m2 ** 1.5)


def spearman_rho(xs: Sequence[float], ys: Sequence[float]) -> float:
    """Cross-sectional Spearman rank correlation (average ranks for ties)."""
    n = len(xs)
    if n != len(ys) or n < 2:
        raise SpecViolation("spearman_rho needs equal-length sequences of length >= 2")

    def _ranks(values: Sequence[float]) -> list[float]:
        order = sorted(range(n), key=lambda i: (values[i], i))
        ranks = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and values[order[j + 1]] == values[order[i]]:
                j += 1
            average = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                ranks[order[k]] = average
            i = j + 1
        return ranks

    rx, ry = _ranks(xs), _ranks(ys)
    mean_x = math.fsum(rx) / n
    mean_y = math.fsum(ry) / n
    cov = math.fsum((a - mean_x) * (b - mean_y) for a, b in zip(rx, ry))
    var_x = math.fsum((a - mean_x) ** 2 for a in rx)
    var_y = math.fsum((b - mean_y) ** 2 for b in ry)
    if var_x <= 0.0 or var_y <= 0.0:
        return 0.0
    return cov / math.sqrt(var_x * var_y)


# --------------------------------------------------------------------------- #
# Feature engine (one shared immutable state per plugin)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ArmSpec:
    """Frozen per-arm declaration (mirrors the selection-freeze spec)."""

    arm_id: str
    role: str
    formation_days: int
    inverted: bool


@dataclass(frozen=True)
class StampFeatures:
    """Feature vector + diagnostics for one decision stamp."""

    instant_ns: int
    features: Mapping[str, float]
    betas: Mapping[str, float]
    eligible: tuple[str, ...]
    reversal_rho: Optional[float]


class FeatureEngine:
    """Immutable PIT feature engine over injected completed-bar aggregates.

    The engine and BTC benchmark frame are injected at construction; every
    quantity at a stamp ``D`` is a function of observations with stamps
    ``<= D`` only (returns need strictly COMPLETED days before ``D``).
    """

    def __init__(
        self,
        *,
        daily_by_symbol: Mapping[str, DailyFrame],
        benchmark_symbol: str,
        formation_days_by_arm: Mapping[str, int],
        feature_kind_by_arm: Mapping[str, str],
    ) -> None:
        if benchmark_symbol not in daily_by_symbol:
            raise SpecViolation("benchmark BTC daily frame missing")
        self._daily = dict(daily_by_symbol)
        self._benchmark = str(benchmark_symbol)
        self._formation = {
            str(k): int(v) for k, v in formation_days_by_arm.items()
        }
        self._feature_kind = {
            str(k): str(v) for k, v in feature_kind_by_arm.items()
        }
        unknown = sorted(set(self._formation) ^ set(self._feature_kind))
        if unknown:
            raise SpecViolation(f"arm feature-kind mapping incomplete: {unknown}")
        for arm, kind in self._feature_kind.items():
            if kind not in (FEATURE_KIND_RESMAX, FEATURE_KIND_RESSKEW):
                raise SpecViolation(f"unknown frozen feature kind {kind!r} for {arm!r}")

    # -- PIT return access ------------------------------------------------ #
    def _returns_to(
        self, symbol: str, last_day: int, count: int
    ) -> Optional[list[tuple[int, float]]]:
        """Consecutive daily returns ``(day, r)`` with ``day <= last_day``.

        Returns ``None`` when any of the ``count`` days ending ``last_day``
        is unavailable (incomplete day / missing close) -- never skips a gap.
        """
        frame = self._daily.get(symbol)
        if frame is None:
            return None
        out = []
        for day in range(int(last_day) - count + 1, int(last_day) + 1):
            value = frame.daily_return(day)
            if value is None or not math.isfinite(value):
                return None
            out.append((day, value))
        return out

    def _beta_at(self, symbol: str, last_day: int) -> Optional[float]:
        """90d rolling beta on returns ending ``last_day`` (frozen window)."""
        pairs = self._returns_to(symbol, last_day, BETA_WINDOW_DAYS)
        market = self._returns_to(self._benchmark, last_day, BETA_WINDOW_DAYS)
        if pairs is None or market is None:
            return None
        return rolling_beta([r for _, r in pairs], [r for _, r in market])

    def _residual(self, symbol: str, day: int, beta: float) -> Optional[float]:
        """One BTC-residualised daily return ``r_i - beta * r_btc``."""
        frame = self._daily.get(symbol)
        market = self._daily.get(self._benchmark)
        if frame is None or market is None:
            return None
        r_i = frame.daily_return(day)
        r_m = market.daily_return(day)
        if r_i is None or r_m is None:
            return None
        return r_i - beta * r_m

    def _arm_feature(
        self, symbol: str, arm: str, last_day: int
    ) -> Optional[float]:
        formation = self._formation[arm]
        kind = self._feature_kind[arm]
        if kind == FEATURE_KIND_RESMAX:
            # anchor: residuals over the trailing `formation` days, each with
            # its own rolling 90d beta; feature = max daily residual.
            values = []
            for day in range(last_day - formation + 1, last_day + 1):
                beta = self._beta_at(symbol, day - 1)
                if beta is None:
                    return None
                eps = self._residual(symbol, day, beta)
                if eps is None:
                    return None
                values.append(eps)
            return max(values)
        if kind == FEATURE_KIND_RESSKEW:
            # neighbour: 30d rolling skew of residual dailies.
            values = []
            for day in range(last_day - formation + 1, last_day + 1):
                beta = self._beta_at(symbol, day - 1)
                if beta is None:
                    return None
                eps = self._residual(symbol, day, beta)
                if eps is None:
                    return None
                values.append(eps)
            return sample_skew(values)
        raise SpecViolation(f"unknown frozen feature kind for arm {arm!r}")

    def _eligible_universe(
        self, instant_ns: int, *, symbols: Sequence[str], last_completed_bar: Mapping[str, int]
    ) -> tuple[list[str], dict[str, float]]:
        """PIT eligibility in frozen order: listing/history, active, DV.

        The freeze pins "PIT eligibility by listing + DV filter".  DV filter:
        strictly POSITIVE trailing-28d completed dollar volume (a liquidity
        sanity floor, PIT-computed; the repo's median-of-cohort proxy would
        hard-cap the tradeable set below the quintile breadth the frozen
        book needs).  Fail closed on any incomplete DV day.
        """
        day = day_index(instant_ns) - 1  # last COMPLETE day before the stamp
        history_ok: list[str] = []
        for symbol in symbols:
            frame = self._daily.get(symbol)
            if frame is None:
                continue
            # (a) listing + warmup: HISTORY_DAYS_REQUIRED consecutive daily
            #     returns ending yesterday (covers beta + formation windows).
            if self._returns_to(symbol, day, HISTORY_DAYS_REQUIRED) is None:
                continue
            # (b) BTC warmup identical (market side must also be complete).
            if self._returns_to(self._benchmark, day, BETA_WINDOW_DAYS) is None:
                continue
            # (c) actively trading: a completed bar within the trailing 48h.
            last_bar = last_completed_bar.get(symbol)
            if last_bar is None or int(instant_ns) - int(last_bar) > ACTIVE_BAR_MAX_AGE_NS:
                continue
            history_ok.append(symbol)
        # (d) DV filter: positive completed 28d dollar volume, PIT.
        eligible: list[str] = []
        for symbol in history_ok:
            frame = self._daily[symbol]
            values = [
                frame.dollar_volume.get(d)
                for d in range(day - DV_WINDOW_DAYS + 1, day + 1)
            ]
            if any(v is None for v in values):
                continue
            if math.fsum(float(v) for v in values) > 0.0:  # type: ignore[arg-type]
                eligible.append(symbol)
        return sorted(eligible), {}

    # -- public per-stamp computation ------------------------------------- #
    def features_at(
        self,
        *,
        instant_ns: int,
        arm: str,
        symbols: Sequence[str],
        last_completed_bar: Mapping[str, int],
    ) -> StampFeatures:
        """Features/betas/eligibility/reversal-rho for one stamp (PIT)."""
        if arm not in self._formation:
            raise SpecViolation(f"unknown arm {arm!r}")
        eligible, _dv = self._eligible_universe(
            int(instant_ns), symbols=symbols, last_completed_bar=last_completed_bar
        )
        day = day_index(int(instant_ns)) - 1
        features: dict[str, float] = {}
        betas: dict[str, float] = {}
        for symbol in eligible:
            beta = self._beta_at(symbol, day)
            if beta is None:
                continue
            value = self._arm_feature(symbol, arm, day)
            if value is None or not math.isfinite(value):
                continue
            betas[symbol] = beta
            features[symbol] = value
        ordered = sorted(features)
        rho = self._reversal_rho(ordered, features, day)
        return StampFeatures(
            instant_ns=int(instant_ns),
            features={s: features[s] for s in ordered},
            betas={s: betas[s] for s in ordered},
            eligible=tuple(ordered),
            reversal_rho=rho,
        )

    def _reversal_rho(
        self, symbols: Sequence[str], features: Mapping[str, float], last_day: int
    ) -> Optional[float]:
        """A7-N diagnostic: Spearman rho of feature vs 7d reversal proxy.

        Reversal proxy = NEGATIVE trailing-7d summed residual return
        (A7-N evidence convention).  DIAGNOSTIC ONLY: nothing downstream may
        feed this into the book.
        """
        proxy: dict[str, float] = {}
        for symbol in symbols:
            values = []
            for day in range(last_day - REV_WINDOW_DAYS + 1, last_day + 1):
                beta = self._beta_at(symbol, day - 1)
                if beta is None:
                    break
                eps = self._residual(symbol, day, beta)
                if eps is None:
                    break
                values.append(eps)
            if len(values) != REV_WINDOW_DAYS:
                continue
            proxy[symbol] = -math.fsum(values)
        if len(proxy) != len(symbols) or len(proxy) < 2:
            return None
        return spearman_rho([features[s] for s in symbols], [proxy[s] for s in symbols])


def quintile_buckets(n: int) -> tuple[int, ...]:
    """Rank-boundary offsets of the five quintile buckets for ``n`` names.

    Boundaries ``round(i*n/5)`` (i = 0..5): with ``n >= MIN_ELIGIBLE`` the
    low and high buckets each hold >= 2 names, so equal-weight legs stay
    inside the adapter weight cap; middle buckets may differ by one name.
    """
    return tuple(round(i * n / QUINTILES) for i in range(QUINTILES + 1))


# --------------------------------------------------------------------------- #
# Frozen quintile book with BTC beta-neutral leg gross split
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class BookDecision:
    """Deterministic target-book decision for one stamp."""

    status: str
    weights: tuple[tuple[str, float], ...]
    carried_forward: bool
    reason_code: Optional[str]
    diagnostics: Mapping[str, object]


def build_quintile_book(
    *,
    stamp: StampFeatures,
    arm_spec: ArmSpec,
    benchmark_beta_mean: float,
) -> BookDecision:
    """Low-minus-high residual-feature quintile book, BTC beta-neutral.

    * long the LOW-quintile, short the HIGH-quintile (frozen sign;
      ``inverted`` flips it for the causal negative control);
    * leg gross split ``L = b_short/(b_long+b_short)``, ``S = 1 - L`` from the
      frozen 90d betas so the book's weighted BTC beta is ~0 (beta hedge);
      degenerate beta sums fall back to the dollar-neutral 50/50 split with a
      diagnostic flag;
    * fail closed to SKIP when the adapter weight cap cannot be respected.
    """
    eligible = stamp.eligible
    if len(eligible) < MIN_ELIGIBLE:
        return BookDecision(
            status=STATUS_SKIP_NO_SELECTION,
            weights=(),
            carried_forward=True,
            reason_code=REASON_BELOW_MIN_ELIGIBLE,
            diagnostics={"eligible": len(eligible)},
        )
    boundaries = quintile_buckets(len(eligible))
    ranked = sorted(eligible, key=lambda s: (stamp.features[s], s))
    low = tuple(ranked[boundaries[0]:boundaries[1]])
    high = tuple(ranked[boundaries[-2]:boundaries[-1]])
    if arm_spec.inverted:
        longs, shorts = high, low
    else:
        longs, shorts = low, high
    beta_long = math.fsum(stamp.betas[s] for s in longs) / len(longs)
    beta_short = math.fsum(stamp.betas[s] for s in shorts) / len(shorts)
    total = beta_long + beta_short
    diagnostics: dict[str, object] = {
        "quintile_size_low": len(low),
        "quintile_size_high": len(high),
        "eligible": len(eligible),
        "bucket_boundaries": list(boundaries),
        "beta_long_leg_mean": round(beta_long, 12),
        "beta_short_leg_mean": round(beta_short, 12),
        "benchmark_beta_mean": round(benchmark_beta_mean, 12),
        "reversal_rho_diagnostic": stamp.reversal_rho,
        "diagnostic_only_note": "reversal rho is never a signal input",
    }
    if total <= 0.0 or not math.isfinite(total):
        leg_gross_long = 0.5
        diagnostics["beta_split"] = "degenerate_dollar_neutral_fallback"
    else:
        leg_gross_long = beta_short / total
        diagnostics["beta_split"] = "btc_beta_neutral"
    weights: list[tuple[str, float]] = []
    for symbol in longs:
        weights.append((symbol, round(leg_gross_long / len(longs), 12)))
    leg_gross_short = GROSS_TARGET - leg_gross_long
    for symbol in shorts:
        weights.append((symbol, -round(leg_gross_short / len(shorts), 12)))
    gross = math.fsum(abs(w) for _, w in weights)
    if any(abs(w) > WEIGHT_CAP + 1e-9 for _, w in weights) or abs(gross - GROSS_TARGET) > 1e-6:
        return BookDecision(
            status=STATUS_SKIP_NO_SELECTION,
            weights=(),
            carried_forward=True,
            reason_code=REASON_WEIGHT_CAP,
            diagnostics=diagnostics,
        )
    return BookDecision(
        status=STATUS_OK,
        weights=tuple(sorted(weights)),
        carried_forward=False,
        reason_code=None,
        diagnostics=diagnostics,
    )


__all__ = [
    "ACTIVE_BAR_MAX_AGE_NS",
    "ArmSpec",
    "BARS_PER_DAY",
    "BAR_NS",
    "BETA_WINDOW_DAYS",
    "BookDecision",
    "DAY_NS",
    "DV_WINDOW_DAYS",
    "DailyFrame",
    "FeatureEngine",
    "FOLD_RANGES",
    "FEATURE_KIND_RESMAX",
    "FEATURE_KIND_RESSKEW",
    "GROSS_TARGET",
    "HISTORY_DAYS_REQUIRED",
    "MAX_WINDOW_DAYS",
    "MIN_ELIGIBLE",
    "QUINTILES",
    "REASON_BELOW_MIN_ELIGIBLE",
    "REASON_FOLD_BOUNDARY_FORCE_FLAT",
    "REASON_WEIGHT_CAP",
    "REV_WINDOW_DAYS",
    "SKEW_WINDOW_DAYS",
    "STATUS_OK",
    "STATUS_SKIP_NO_SELECTION",
    "SpecViolation",
    "StampFeatures",
    "WEIGHT_CAP",
    "WINDOW_END_ISO",
    "WINDOW_START_ISO",
    "aggregate_daily",
    "build_quintile_book",
    "build_schedule_instants",
    "day_index",
    "fold_force_flat_instants",
    "fold_of_instant",
    "mondays_in_window",
    "quintile_buckets",
    "rolling_beta",
    "sample_skew",
    "spearman_rho",
]
