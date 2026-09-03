"""Frozen strategy primitives for the A8-V11-OILEVER-DELEV family (lane I-3).

This module implements the FROZEN contract pinned by
``research/control/v11_run/selection_freeze_specs/A8-V11-OILEVER-DELEV.json``
(bootstrap ``01139a8``) verbatim -- no tuning, no grids, no parameter
changes.  It is a pure, data-injected library: every observable (completed
15m bars, OI snapshot series, funding settlements, tick sizes) is supplied by
the caller, so the same primitives run on synthetic fixtures and on the
staged read-only snapshot.  Nothing here reads the catalog, computes a scored
outcome, or persists anything.

Frozen contract (spec file, verbatim):

* anchor ``OILEV-FLOW-28D-W`` -- 28d log OI-growth from the daily-last OI
  snapshot, THEN residualised cross-sectionally per stamp against the
  trailing-28d return (per-stamp cross-sectional OLS of OI-growth on
  trailing return with intercept; residual = traded signal); long
  deleveraged / short crowded quintiles, beta-neutral;
* neighbour ``OILEV-STOCK-56D-W`` -- 56d OI level percentile of the symbol's
  own history, same residualisation, book "low minus high";
* control ``OILEV-FLOW-28D-W-INV`` -- the anchor feature/book sign-inverted
  (causal negative control).

PIT rule (frozen, from the A9-F2 re-audit): the OI value used at a Monday
00:00:00Z decision stamp is the last COMPLETED 5m row strictly BEFORE the
stamp; staleness must be <= 48h or the stamp is UNAVAILABLE for that symbol
(fail closed).  Features are completed-bar only; the trailing-28d return uses
the last completed 15m bar strictly before the stamp and the last completed
bar strictly before ``stamp - 28d``.  Execution fills at the open of the 15m
bar covering the decision instant (the first allowed execution event after
availability -- the frozen "one declared execution lag").

The BTC beta hedge is a CONTEXT semantic (identity direction
``long_short_beta_neutral`` + the frozen 90d daily-beta context benchmark);
BTCUSDT is benchmark-excluded and can never appear as a position.  The
cross-sectional residualisation above removes the linear momentum component
of the raw feature, which is the frozen load-bearing orthogonalisation
mandated by the A1 rho addendum (pooled rho(OI-growth, MOM28) = 0.5651 FAIL).
"""

from __future__ import annotations

import bisect
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping, Optional, Sequence

from research.adapter_v10.protocol import (
    ContractViolation,
    StrategyIdentity,
)
from research.contract_v10 import (
    ADVERSE_TICKS_SLIPPAGE_FLOOR_V10,
    FILL_CLOCK_V10,
    TAKER_FEE_FLOOR_BPS_V10,
)

# --------------------------------------------------------------------------- #
# Frozen identity (reproduces the selection_freeze.json digests EXACTLY)
# --------------------------------------------------------------------------- #
FAMILY_ID = "A8-V11-OILEVER-DELEV"
STRATEGY_ID = "A8-V11-OILEVER-DELEV.v1"
DIRECTION = "long_short_beta_neutral"
BENCHMARK_SYMBOL = "BTCUSDT"

WINDOW_START_ISO = "2025-08-22T00:00:00Z"
WINDOW_END_ISO = "2026-08-21T00:00:00Z"

#: Arm id -> frozen role (``arm_config_id``).
ARM_ROLES: dict[str, str] = {
    "OILEV-FLOW-28D-W": "anchor",
    "OILEV-STOCK-56D-W": "neighbour",
    "OILEV-FLOW-28D-W-INV": "causal_negative_control",
}
ARM_IDS: tuple[str, ...] = tuple(sorted(ARM_ROLES))
ANCHOR_ARM = "OILEV-FLOW-28D-W"
NEIGHBOUR_ARM = "OILEV-STOCK-56D-W"
CONTROL_ARM = "OILEV-FLOW-28D-W-INV"

#: Frozen spec strings (``selection_freeze_specs`` common block, verbatim).
DECISION_CLOCK = (
    "Mondays 00:00:00Z; features from completed 15m bars + last COMPLETED OI "
    "5m row strictly before stamp; one declared execution lag after availability"
)
COSTS = (
    "generic adapter fees/slippage; native funding while held; "
    "stress = fee x1.5, +2 ticks, +1 event delay"
)

#: Frozen per-arm feature/book strings (spec ``arms`` entries, verbatim).
FEATURE_FLOW = (
    "28d log OI-growth from daily-last OI snapshot, residualised "
    "cross-sectionally per stamp vs trailing-28d return (frozen orthogonalisation)"
)
FEATURE_STOCK = "56d OI level percentile of own history, same residualisation"
BOOK_ANCHOR = "long deleveraged / short crowded quintiles, beta-neutral"
BOOK_NEIGHBOUR = "low minus high"
BOOK_CONTROL = "sign-inverted"
FALSIFICATION_CONTROL = "positive after-cost spread destroys mechanism"

FORMATION_DAYS_ANCHOR = 28
FORMATION_DAYS_NEIGHBOUR = 56
HOLDING_DAYS = 7

#: Frozen config payload per arm (whole frozen feature/book/clock/costs/
#: falsification; window stamps are cell fields and stay out of the digest).
_FROZEN_CONFIGS: dict[str, dict] = {
    ANCHOR_ARM: {
        "feature": FEATURE_FLOW,
        "book": BOOK_ANCHOR,
        "formation_days": FORMATION_DAYS_ANCHOR,
        "holding_days": HOLDING_DAYS,
        "decision_clock": DECISION_CLOCK,
        "costs": COSTS,
        "falsification": "",
    },
    NEIGHBOUR_ARM: {
        "feature": FEATURE_STOCK,
        "book": BOOK_NEIGHBOUR,
        "formation_days": FORMATION_DAYS_NEIGHBOUR,
        "holding_days": HOLDING_DAYS,
        "decision_clock": DECISION_CLOCK,
        "costs": COSTS,
        "falsification": "",
    },
    CONTROL_ARM: {
        "feature": FEATURE_FLOW,
        "book": BOOK_CONTROL,
        "formation_days": FORMATION_DAYS_ANCHOR,
        "holding_days": HOLDING_DAYS,
        "decision_clock": DECISION_CLOCK,
        "costs": COSTS,
        "falsification": FALSIFICATION_CONTROL,
    },
}


def frozen_arm_config(arm_id: str) -> dict:
    """The exact frozen ``config`` payload of one arm (digest-reproducing)."""
    arm_id = str(arm_id)
    if arm_id not in _FROZEN_CONFIGS:
        raise ContractViolation(f"unknown arm_id {arm_id!r}; expected {ARM_IDS}")
    return dict(_FROZEN_CONFIGS[arm_id])


def frozen_identity(arm_id: str) -> StrategyIdentity:
    """The frozen V11 identity of one arm (digest equality is test-pinned)."""
    return StrategyIdentity(
        strategy_id=STRATEGY_ID,
        family_id=FAMILY_ID,
        arm_config_id=ARM_ROLES[str(arm_id)],
        direction=DIRECTION,
        window_start_iso=WINDOW_START_ISO,
        window_end_iso=WINDOW_END_ISO,
        benchmark_symbols_excluded=(BENCHMARK_SYMBOL,),
        arm_id=str(arm_id),
        config=frozen_arm_config(arm_id),
    )


# --------------------------------------------------------------------------- #
# Frozen numeric contract
# --------------------------------------------------------------------------- #
DAY_NS = 86_400_000_000_000
HOUR_NS = 3_600_000_000_000
BAR_INTERVAL_NS = 900_000_000_000  # 15m completed bars

QUINTILES = 5
GROSS_TARGET = 1.0
CAP_MAX = 0.30
OI_MAX_STALENESS_HOURS = 48
RETURN_WINDOW_DAYS = 28
STOCK_WINDOW_DAYS = 56
LISTING_HISTORY_DAYS = 60
ACTIVITY_MAX_HOURS = 48
DV_WINDOW_DAYS = 28
BETA_WINDOW_DAYS = 90

#: Declared cost floors (contract_v10; equal to the staged snapshot values
#: used by the A9-F2 feasibility audit).
TAKER_FEE_FLOOR_BPS = float(TAKER_FEE_FLOOR_BPS_V10)
ADVERSE_TICK_SLIP_FLOOR = int(ADVERSE_TICKS_SLIPPAGE_FLOOR_V10)

FILL_CLOCK = FILL_CLOCK_V10

#: Pinned folds (spec ``common.folds``; force-flat at fold boundaries is
#: realised by the adapter's purge/carry accounting at fold edges).
FOLD_WINDOWS: tuple[tuple[str, str, str], ...] = (
    ("F0", "2025-08-22", "2025-12-21"),
    ("F1", "2025-12-22", "2026-04-21"),
    ("F2", "2026-04-22", "2026-08-21"),
)
PURGE_DAYS = 1
MIN_FOLDS = 3

STATUS_OK = "OK"
STATUS_SKIP = "SKIP_NO_SELECTION"

_BOOK_FEATURES: dict[str, str] = {
    ANCHOR_ARM: "flow",
    NEIGHBOUR_ARM: "stock",
    CONTROL_ARM: "flow",
}
_BOOK_INVERTED: dict[str, bool] = {
    ANCHOR_ARM: False,
    NEIGHBOUR_ARM: False,
    CONTROL_ARM: True,
}


# --------------------------------------------------------------------------- #
# Injected observables
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class Bar:
    """One COMPLETED 15m bar; ``ts_event_ns`` is its exchange CLOSE stamp."""

    ts_event_ns: int
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    quote_volume: float = 0.0

    def __post_init__(self) -> None:
        if int(self.ts_event_ns) <= 0:
            raise ContractViolation("bar ts_event_ns must be positive")
        for name in ("open", "high", "low", "close"):
            value = float(getattr(self, name))
            if not math.isfinite(value) or value <= 0.0:
                raise ContractViolation(f"bar {name} must be finite positive")


def bar_open_ns(bar: Bar) -> int:
    """Derived OPEN stamp of a close-stamped bar (repo PIT convention)."""
    return int(bar.ts_event_ns) - BAR_INTERVAL_NS


def parse_iso_utc(text: str) -> int:
    """``YYYY-MM-DDTHH:MM:SSZ`` -> UTC epoch ns (fail closed otherwise)."""
    raw = str(text).strip()
    if not raw.endswith("Z"):
        raise ContractViolation(f"window stamp must end with Z: {text!r}")
    moment = datetime.fromisoformat(raw[:-1]).replace(tzinfo=timezone.utc)
    return int(moment.timestamp()) * 1_000_000_000


def iso_utc(ns: int) -> str:
    return (
        datetime.fromtimestamp(int(ns) / 1e9, tz=timezone.utc)
        .strftime("%Y-%m-%dT%H:%M:%SZ")
    )


# --------------------------------------------------------------------------- #
# PIT lookups (fail closed)
# --------------------------------------------------------------------------- #
def oi_anchor_before(
    series: Sequence[tuple[int, float]],
    stamp_ns: int,
    *,
    max_staleness_ns: int = OI_MAX_STALENESS_HOURS * HOUR_NS,
) -> Optional[float]:
    """Last COMPLETED OI row STRICTLY BEFORE ``stamp_ns`` (frozen PIT rule).

    A row at or after the stamp is never used; the row must be no staler than
    the frozen 48h gate and carry a positive value, otherwise the anchor is
    UNAVAILABLE (``None`` -- the stamp fails closed for that symbol).
    """
    stamp = int(stamp_ns)
    if not series:
        return None
    times = [int(t) for t, _ in series]
    idx = bisect.bisect_left(times, stamp) - 1  # strictly-before lookup
    if idx < 0:
        return None
    ts, value = series[idx]
    if stamp - int(ts) > max_staleness_ns:
        return None  # stale: UNAVAILABLE, fail closed
    value = float(value)
    if not math.isfinite(value) or value <= 0.0:
        return None
    return value


def last_bar_strictly_before(bars: Sequence[Bar], stamp_ns: int) -> Optional[Bar]:
    """Last completed bar with ``ts_event < stamp`` (completed-bar features)."""
    stamp = int(stamp_ns)
    times = [int(b.ts_event_ns) for b in bars]
    idx = bisect.bisect_left(times, stamp) - 1
    if idx < 0:
        return None
    return bars[idx]


def trailing_return(
    bars: Sequence[Bar], stamp_ns: int, *, window_days: int = RETURN_WINDOW_DAYS
) -> Optional[float]:
    """Trailing ``window_days`` return from completed bars strictly before stamps."""
    now = last_bar_strictly_before(bars, int(stamp_ns))
    past = last_bar_strictly_before(bars, int(stamp_ns) - int(window_days) * DAY_NS)
    if now is None or past is None:
        return None
    if past.close <= 0.0:
        return None
    value = float(now.close) / float(past.close) - 1.0
    return value if math.isfinite(value) else None


def oi_flow_growth(
    series: Sequence[tuple[int, float]],
    stamp_ns: int,
    *,
    formation_days: int = FORMATION_DAYS_ANCHOR,
    max_staleness_ns: int = OI_MAX_STALENESS_HOURS * HOUR_NS,
) -> Optional[float]:
    """28d log OI-growth; both anchors strictly-before, fresh and positive."""
    now = oi_anchor_before(series, int(stamp_ns), max_staleness_ns=max_staleness_ns)
    past = oi_anchor_before(
        series,
        int(stamp_ns) - int(formation_days) * DAY_NS,
        max_staleness_ns=max_staleness_ns,
    )
    if now is None or past is None or past <= 0.0:
        return None
    value = math.log(float(now) / float(past))
    return value if math.isfinite(value) else None


def oi_stock_percentile(
    series: Sequence[tuple[int, float]],
    stamp_ns: int,
    *,
    window_days: int = STOCK_WINDOW_DAYS,
    max_staleness_ns: int = OI_MAX_STALENESS_HOURS * HOUR_NS,
) -> Optional[float]:
    """Percentile of the current OI level within its own trailing history."""
    now = oi_anchor_before(series, int(stamp_ns), max_staleness_ns=max_staleness_ns)
    if now is None:
        return None
    lo = int(stamp_ns) - int(window_days) * DAY_NS
    window = [float(v) for t, v in series if lo <= int(t) < int(stamp_ns)]
    if len(window) < 2:
        return None  # fail closed: no percentile without history
    rank = sum(1 for v in window if v <= now)
    return rank / len(window)


def daily_dollar_volume_median(
    bars: Sequence[Bar], stamp_ns: int, *, window_days: int = DV_WINDOW_DAYS
) -> Optional[float]:
    """Median daily quote-volume over ``(stamp - window, stamp]`` (PIT)."""
    lo = int(stamp_ns) - int(window_days) * DAY_NS
    per_day: dict[int, float] = {}
    for bar in bars:
        ts = int(bar.ts_event_ns)
        if lo < ts <= int(stamp_ns):
            day = (ts // DAY_NS) * DAY_NS
            per_day[day] = per_day.get(day, 0.0) + float(bar.quote_volume)
    if not per_day:
        return None
    values = sorted(per_day.values())
    mid = len(values) // 2
    if len(values) % 2:
        return values[mid]
    return 0.5 * (values[mid - 1] + values[mid])


def eligible_symbols_at(
    bars_by_symbol: Mapping[str, Sequence[Bar]],
    stamp_ns: int,
    *,
    universe: Sequence[str],
    listing_history_days: int = LISTING_HISTORY_DAYS,
    activity_max_hours: int = ACTIVITY_MAX_HOURS,
) -> tuple[list[str], dict[str, dict]]:
    """PIT eligibility by listing + activity + DV filter (frozen universe rule).

    Identical rule to the A9-F2 feasibility audit: listed with at least
    ``listing_history_days`` of history, active (a completed bar within
    ``activity_max_hours`` before the stamp), and 28d daily dollar-volume
    median STRICTLY ABOVE the cross-sectional median of the active set.
    """
    stamp = int(stamp_ns)
    candidates: list[str] = []
    medians: dict[str, float] = {}
    detail: dict[str, dict] = {}
    for sym in sorted(set(universe)):
        bars = bars_by_symbol.get(str(sym)) or ()
        if not bars:
            continue
        first_ts = int(bars[0].ts_event_ns)
        times = [int(b.ts_event_ns) for b in bars]
        idx = bisect.bisect_left(times, stamp) - 1
        if idx < 0:
            continue
        if first_ts > stamp - int(listing_history_days) * DAY_NS:
            detail[str(sym)] = {"eligible": False, "reason": "listing_history"}
            continue
        if stamp - times[idx] > int(activity_max_hours) * HOUR_NS:
            detail[str(sym)] = {"eligible": False, "reason": "inactive"}
            continue
        med = daily_dollar_volume_median(bars, stamp)
        if med is None:
            detail[str(sym)] = {"eligible": False, "reason": "no_dv_window"}
            continue
        candidates.append(str(sym))
        medians[str(sym)] = med
    if len(medians) < 2:
        detail.update({sym: {"eligible": False, "reason": "no_cross_section"} for sym in medians})
        return [], detail
    ordered = sorted(medians.values())
    mid = len(ordered) // 2
    xsec = ordered[mid] if len(ordered) % 2 else 0.5 * (ordered[mid - 1] + ordered[mid])
    eligible = sorted(sym for sym, med in medians.items() if med > xsec)
    for sym in medians:
        detail[sym] = {"eligible": sym in eligible, "dv_median": medians[sym]}
    return eligible, detail


# --------------------------------------------------------------------------- #
# Frozen cross-sectional momentum-orthogonalisation
# --------------------------------------------------------------------------- #
def residualise_against_return(
    values: Mapping[str, float],
    returns: Mapping[str, float],
) -> Optional[tuple[dict[str, float], dict[str, float]]]:
    """Per-stamp cross-sectional OLS (constant + slope) of values on returns.

    The residual IS the traded signal (frozen orthogonalisation).  Fail closed
    (``None``) with fewer than 3 names or a degenerate return cross-section.
    Returns ``(residuals, diagnostics)`` with the OLS intercept/slope/R^2.
    """
    names = sorted(set(values) & set(returns))
    if len(names) < 3:
        return None
    xs = [float(returns[s]) for s in names]
    ys = [float(values[s]) for s in names]
    n = float(len(names))
    mean_x = math.fsum(xs) / n
    mean_y = math.fsum(ys) / n
    sxx = math.fsum((x - mean_x) ** 2 for x in xs)
    sxy = math.fsum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    if not math.isfinite(sxx) or sxx <= 0.0:
        return None  # degenerate return cross-section: refuse, never guess
    slope = sxy / sxx
    intercept = mean_y - slope * mean_x
    if not (math.isfinite(slope) and math.isfinite(intercept)):
        return None
    residuals: dict[str, float] = {}
    ss_res = 0.0
    ss_tot = 0.0
    for s, x, y in zip(names, xs, ys):
        resid = y - (intercept + slope * x)
        if not math.isfinite(resid):
            return None
        residuals[s] = resid
        ss_res += resid * resid
        ss_tot += (y - mean_y) ** 2
    r2 = 0.0 if ss_tot <= 0.0 else max(0.0, 1.0 - ss_res / ss_tot)
    diagnostics = {
        "n": int(len(names)),
        "ols_intercept": intercept,
        "ols_slope": slope,
        "cross_sectional_r2": r2,
    }
    return residuals, diagnostics


def pearson_rho(xs: Sequence[float], ys: Sequence[float]) -> float:
    """Pearson cross-sectional correlation (orthogonality diagnostic)."""
    if len(xs) != len(ys) or len(xs) < 2:
        raise ContractViolation("pearson_rho needs equal-length series >= 2")
    n = float(len(xs))
    mx = math.fsum(xs) / n
    my = math.fsum(ys) / n
    sxy = math.fsum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = math.fsum((x - mx) ** 2 for x in xs)
    syy = math.fsum((y - my) ** 2 for y in ys)
    if sxx <= 0.0 or syy <= 0.0:
        return 0.0
    return sxy / math.sqrt(sxx * syy)


def _rank(values: Sequence[float]) -> list[float]:
    """Average ranks (ties share the mean rank) for Spearman rho."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman_rho(xs: Sequence[float], ys: Sequence[float]) -> float:
    """Spearman rank correlation (frozen diagnostic for the rho gate)."""
    return pearson_rho(_rank(list(xs)), _rank(list(ys)))


# --------------------------------------------------------------------------- #
# Quintile book (frozen geometry)
# --------------------------------------------------------------------------- #
def quintile_bucket(ranks: int, rank: int, *, quintiles: int = QUINTILES) -> int:
    """Deterministic quintile bucket of one 0-based rank in ``[0, n)``."""
    return (rank * quintiles) // ranks


def quintile_book(
    residuals: Mapping[str, float],
    *,
    invert: bool = False,
    gross: float = GROSS_TARGET,
) -> dict[str, object]:
    """Long lowest / short highest residual quintile, equal weight, dollar-neutral.

    ``invert=True`` flips the book sign end-to-end (the frozen causal negative
    control).  Requires at least one name in each traded extreme bucket.
    """
    sign = -1.0 if invert else 1.0
    ordered = sorted((sign * float(v), sym) for sym, v in residuals.items())
    n = len(ordered)
    long_side = []
    short_side = []
    for rank, (_key, sym) in enumerate(ordered):
        bucket = quintile_bucket(n, rank)
        if bucket == 0:
            long_side.append(sym)
        elif bucket == QUINTILES - 1:
            short_side.append(sym)
    if not long_side or not short_side:
        raise ContractViolation("quintile book needs both extreme buckets non-empty")
    long_weight = (gross / 2.0) / len(long_side)
    short_weight = (gross / 2.0) / len(short_side)
    weights: dict[str, float] = {}
    for sym in long_side:
        weights[sym] = weights.get(sym, 0.0) + long_weight
    for sym in short_side:
        weights[sym] = weights.get(sym, 0.0) - short_weight
    return {
        "weights": {sym: round(w, 12) for sym, w in sorted(weights.items())},
        "longs": sorted(long_side),
        "shorts": sorted(short_side),
    }


# --------------------------------------------------------------------------- #
# Per-stamp targets (all three arms)
# --------------------------------------------------------------------------- #
def compute_targets_at(
    arm_id: str,
    *,
    bars_by_symbol: Mapping[str, Sequence[Bar]],
    oi_by_symbol: Mapping[str, Sequence[tuple[int, float]]],
    stamp_ns: int,
    universe: Sequence[str],
    gross: float = GROSS_TARGET,
) -> dict[str, object]:
    """Frozen target book of one arm at one Monday 00:00:00Z stamp.

    Fail-closed at every step: a symbol with an unavailable/stale OI anchor,
    an incomplete trailing return, or a degenerate cross-section is simply not
    part of the signal; fewer than 5 complete names (quintile feasibility) or
    a degenerate OLS refuses the stamp (``SKIP_NO_SELECTION``, never a guess).
    """
    arm_id = str(arm_id)
    if arm_id not in ARM_ROLES:
        raise ContractViolation(f"unknown arm_id {arm_id!r}")
    stamp = int(stamp_ns)
    eligible, eligibility_detail = eligible_symbols_at(bars_by_symbol, stamp, universe=universe)
    result: dict[str, object] = {
        "schema": "v11i.oilever_delev.targets.v1",
        "family_id": FAMILY_ID,
        "arm_id": arm_id,
        "status": STATUS_SKIP,
        "weights": [],
        "longs": [],
        "shorts": [],
        "carried_forward": True,
        "diagnostics": {
            "stamp_ns": stamp,
            "stamp_iso": iso_utc(stamp),
            "n_eligible_dv": len(eligible),
            "reason_code": None,
        },
    }
    if len(eligible) < 2:
        result["diagnostics"] = {
            **result["diagnostics"],  # type: ignore[dict-item]
            "reason_code": "no_dv_eligible_cross_section",
        }
        return result

    feature_kind = _BOOK_FEATURES[arm_id]
    values: dict[str, float] = {}
    returns: dict[str, float] = {}
    for sym in eligible:
        bars = bars_by_symbol.get(sym) or ()
        series = oi_by_symbol.get(sym) or ()
        if feature_kind == "flow":
            value = oi_flow_growth(series, stamp)
        else:
            value = oi_stock_percentile(series, stamp)
        ret = trailing_return(bars, stamp)
        if value is None or ret is None:
            continue
        values[sym] = value
        returns[sym] = ret
    n_complete = len(values)
    diagnostics = {
        **result["diagnostics"],  # type: ignore[dict-item]
        "n_complete": n_complete,
        "feature_kind": feature_kind,
    }
    if n_complete < QUINTILES:
        result["diagnostics"] = {
            **diagnostics,  # type: ignore[dict-item]
            "reason_code": f"complete_{n_complete}_lt_quintiles_{QUINTILES}",
        }
        return result

    residualised = residualise_against_return(values, returns)
    if residualised is None:
        result["diagnostics"] = {
            **diagnostics,  # type: ignore[dict-item]
            "reason_code": "degenerate_orthogonalisation",
        }
        return result
    residuals, ols = residualised
    book = quintile_book(residuals, invert=_BOOK_INVERTED[arm_id], gross=gross)
    weights: dict[str, float] = book["weights"]  # type: ignore[assignment]
    result.update(
        status=STATUS_OK,
        weights=[[sym, weight] for sym, weight in sorted(weights.items())],
        longs=[[sym, round(weights[sym], 12)] for sym in book["longs"]],  # type: ignore[index]
        shorts=[[sym, round(weights[sym], 12)] for sym in book["shorts"]],  # type: ignore[index]
        carried_forward=False,
    )
    result["diagnostics"] = {
        **diagnostics,  # type: ignore[dict-item]
        "ols_intercept": round(float(ols["ols_intercept"]), 12),
        "ols_slope": round(float(ols["ols_slope"]), 12),
        "cross_sectional_r2": round(float(ols["cross_sectional_r2"]), 12),
        "long_bucket": list(book["longs"]),  # type: ignore[index]
        "short_bucket": list(book["shorts"]),  # type: ignore[index]
        "residual_rho_vs_trailing_return": round(
            pearson_rho(
                [residuals[s] for s in sorted(residuals)],
                [returns[s] for s in sorted(residuals)],
            ),
            12,
        ),
        "reason_code": None,
    }
    return result


# --------------------------------------------------------------------------- #
# Schedule / folds / fills (frozen clocks)
# --------------------------------------------------------------------------- #
def weekly_mondays(
    *,
    window_start_iso: str = WINDOW_START_ISO,
    window_end_iso: str = WINDOW_END_ISO,
) -> tuple[int, ...]:
    """Monday 00:00:00Z decision instants inside the frozen window."""
    start_ns = parse_iso_utc(window_start_iso)
    end_ns = parse_iso_utc(window_end_iso)
    first_day = ((start_ns // DAY_NS) + 1) * DAY_NS  # strictly after the start edge
    mondays = [
        day
        for day in range(first_day, end_ns + 1, DAY_NS)
        if datetime.fromtimestamp(day / 1e9, tz=timezone.utc).weekday() == 0
    ]
    if len(mondays) < 2:
        raise ContractViolation("frozen window must contain at least two Mondays")
    return tuple(mondays)


def fold_assignments(
    instants: Sequence[int],
) -> list[tuple[int, str, list[int]]]:
    """Assign decision stamps to the PINNED F0/F1/F2 calendar windows."""
    members: dict[str, list[int]] = {label: [] for label, _s, _e in FOLD_WINDOWS}
    for instant in sorted(int(v) for v in instants):
        date = datetime.fromtimestamp(instant / 1e9, tz=timezone.utc).date().isoformat()
        for index, (label, start, end) in enumerate(FOLD_WINDOWS):
            if start <= date <= end:
                members[label].append(instant)
                break
        else:
            raise ContractViolation(f"decision stamp {iso_utc(instant)} outside every pinned fold")
    out: list[tuple[int, str, list[int]]] = []
    for index, (label, _start, _end) in enumerate(FOLD_WINDOWS):
        if not members[label]:
            raise ContractViolation(f"pinned fold {label} received no decision stamps")
        out.append((index, label, list(members[label])))
    return out


def purge_fold_members(
    assignments: Sequence[tuple[int, str, list[int]]],
    *,
    purge_days: int = PURGE_DAYS,
) -> list[tuple[int, str, list[int], list[int]]]:
    """Strip the trailing ``purge_days`` instants of each fold (purge gaps).

    Returns ``(index, label, declared_members, purge_gap_instants)``; a book
    opened inside a fold therefore always realises inside that fold -- the
    frozen force-flat-at-fold-boundary policy under the adapter's accounting.
    """
    out: list[tuple[int, str, list[int], list[int]]] = []
    for index, label, members in assignments:
        if len(members) <= purge_days:
            raise ContractViolation(f"fold {label} cannot absorb purge {purge_days}")
        out.append((index, label, list(members[:-purge_days]), list(members[-purge_days:])))
    return out


@dataclass(frozen=True, slots=True)
class FillEvent:
    """The synchronous fill event for one symbol at one decision instant."""

    symbol: str
    decision_ns: int
    fill_open_ns: int
    fill_bar_close_ns: int
    event_offset: int
    price: float


def resolve_fill_event(
    bars: Sequence[Bar],
    symbol: str,
    *,
    decision_ns: int,
    event_delay_events: int = 0,
) -> Optional[FillEvent]:
    """Fill at the open of the bar covering the decision; walk event delays.

    Identical strict-later clock to the repo's panel fill resolver: the frozen
    "one declared execution lag" is the first allowed execution event after
    availability (real close stamps sit a shave before the nominal grid line,
    so the covering bar is identified by interval containment
    ``open <= D < close``).  Missing opening slot -> NO event (never a shifted
    substitute).
    """
    delay = int(event_delay_events)
    if delay < 0:
        raise ContractViolation("event_delay_events must be >= 0")
    decision = int(decision_ns)
    ordered = sorted(bars, key=lambda b: int(b.ts_event_ns))
    start_idx: Optional[int] = None
    for idx, bar in enumerate(ordered):
        if bar_open_ns(bar) <= decision < int(bar.ts_event_ns):
            start_idx = idx
            break
    if start_idx is None or start_idx + delay >= len(ordered):
        return None
    chosen = ordered[start_idx + delay]
    return FillEvent(
        symbol=str(symbol),
        decision_ns=decision,
        fill_open_ns=bar_open_ns(chosen),
        fill_bar_close_ns=int(chosen.ts_event_ns),
        event_offset=delay,
        price=float(chosen.open),
    )


def covering_bar(bars: Sequence[Bar], instant_ns: int) -> Optional[Bar]:
    """Bar with ``open <= instant < close`` (valuation marks fallback)."""
    instant = int(instant_ns)
    for bar in bars:
        if bar_open_ns(bar) <= instant < int(bar.ts_event_ns):
            return bar
    return None


# --------------------------------------------------------------------------- #
# Context-only BTC beta hedge (frozen 90d daily beta; never a position)
# --------------------------------------------------------------------------- #
def daily_closes(bars: Sequence[Bar], stamp_ns: int, *, window_days: int) -> dict[int, float]:
    """Last completed close per UTC day inside ``(stamp - window, stamp]``."""
    lo = int(stamp_ns) - int(window_days) * DAY_NS
    out: dict[int, float] = {}
    for bar in bars:
        ts = int(bar.ts_event_ns)
        if lo < ts <= int(stamp_ns):
            day = (ts // DAY_NS) * DAY_NS
            out[day] = float(bar.close)
    return out


def beta_hedge_ratio(
    bars: Sequence[Bar],
    benchmark_bars: Sequence[Bar],
    stamp_ns: int,
    *,
    window_days: int = BETA_WINDOW_DAYS,
) -> Optional[float]:
    """OLS beta of the symbol's daily returns vs BTC over the trailing window.

    Context-only (alpha-context hedge ratio; BTCUSDT is benchmark-excluded
    and never enters the tradeable book).
    """
    own = daily_closes(bars, stamp_ns, window_days=window_days)
    bench = daily_closes(benchmark_bars, stamp_ns, window_days=window_days)
    common = sorted(set(own) & set(bench))
    if len(common) < 3:
        return None
    xr = [bench[d] / bench[common[i - 1]] - 1.0 for i, d in enumerate(common) if i > 0]
    yr = [own[d] / own[common[i - 1]] - 1.0 for i, d in enumerate(common) if i > 0]
    n = float(len(xr))
    mx = math.fsum(xr) / n
    my = math.fsum(yr) / n
    sxx = math.fsum((x - mx) ** 2 for x in xr)
    if sxx <= 0.0:
        return None
    beta = math.fsum((x - mx) * (y - my) for x, y in zip(xr, yr)) / sxx
    return beta if math.isfinite(beta) else None


__all__ = [
    "ADVERSE_TICK_SLIP_FLOOR",
    "ANCHOR_ARM",
    "ARM_IDS",
    "ARM_ROLES",
    "Bar",
    "BENCHMARK_SYMBOL",
    "BAR_INTERVAL_NS",
    "BETA_WINDOW_DAYS",
    "CAP_MAX",
    "CONTROL_ARM",
    "COSTS",
    "DIRECTION",
    "DECISION_CLOCK",
    "DAY_NS",
    "DV_WINDOW_DAYS",
    "FALSIFICATION_CONTROL",
    "FAMILY_ID",
    "FILL_CLOCK",
    "FOLD_WINDOWS",
    "FORMATION_DAYS_ANCHOR",
    "FORMATION_DAYS_NEIGHBOUR",
    "FEATURE_FLOW",
    "FEATURE_STOCK",
    "FillEvent",
    "GROSS_TARGET",
    "HOLDING_DAYS",
    "HOUR_NS",
    "LISTING_HISTORY_DAYS",
    "MIN_FOLDS",
    "NEIGHBOUR_ARM",
    "OI_MAX_STALENESS_HOURS",
    "PURGE_DAYS",
    "QUINTILES",
    "RETURN_WINDOW_DAYS",
    "STATUS_OK",
    "STATUS_SKIP",
    "STRATEGY_ID",
    "STOCK_WINDOW_DAYS",
    "TAKER_FEE_FLOOR_BPS",
    "ACTIVITY_MAX_HOURS",
    "BOOK_ANCHOR",
    "BOOK_CONTROL",
    "BOOK_NEIGHBOUR",
    "Bar",
    "WINDOW_END_ISO",
    "WINDOW_START_ISO",
    "bar_open_ns",
    "beta_hedge_ratio",
    "compute_targets_at",
    "covering_bar",
    "daily_dollar_volume_median",
    "eligible_symbols_at",
    "frozen_arm_config",
    "frozen_identity",
    "iso_utc",
    "last_bar_strictly_before",
    "oi_anchor_before",
    "oi_flow_growth",
    "oi_stock_percentile",
    "parse_iso_utc",
    "pearson_rho",
    "purge_fold_members",
    "quintile_book",
    "quintile_bucket",
    "resolve_fill_event",
    "residualise_against_return",
    "spearman_rho",
    "trailing_return",
    "weekly_mondays",
]
