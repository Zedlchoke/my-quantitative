"""Frozen feature primitives + staged metrics loader for TAKER-SAT.

Implements ``proposal_P1.json`` ``features_and_lags`` EXACTLY (no tuning):

* ``five_minute_hygiene``   -- per 5-minute label, ``r_t`` is clipped to
  ``[0.2, 5.0]`` before log, then ``clip(ln r_t, -1.609, +1.609)``;
* ``daily_aggression_a_i_d`` -- mean over the 288 labels of metrics_date d
  of the clipped log ratio (equal-weighted across 5-minute windows; the
  known accepted limitation, identical in every arm);
* ``positioning_churn_o_i_W`` -- ``|ln(OIv_2355(d_last) / OIv_2355(d_first))|``
  where ``OIv_2355(x)`` is ``sum_open_interest_value`` at the 23:55 label of
  metrics_date x;
* ``anchor_feature_S_i_D``  -- ``S = A_bar / (O + 0.02)`` with ``A_bar`` the
  mean of ``a_i_d`` over W = metrics dates ``[D-12, D-3]`` (10 daily
  aggregates, all <= D-3) and O the churn across the same window endpoints;
* neighbour                 -- identical except W = ``[D-23, D-3]`` inclusive
  (21 daily aggregates; ADJUDICATED_BY_A1 pre-score: the explicit dated
  range binds over the draft prose count "20") with the churn endpoints
  moved to the same window;
* causal control CTL-RAWSAT -- the feature is raw ``A_bar_i`` with NO churn
  denominator (identical pipeline, window, ranking, weights, rules, costs).

LAG (``MEASURED_BOUND_LAG_3D``): the window of a decision at D ends at
``D - 3`` calendar days; nothing at or after ``D - 2`` is ever read.

HOLE RULE (p3_freeze_amendment_1): feature windows compute over available
staged rows only; a lookback window with MORE than 10% missing metrics-day
cells refuses the symbol's decision (integer test ``10 * missing > n``,
so exactly 10% still computes over the available days); churn endpoints
must themselves be present -- a missing endpoint refuses the decision
fail-closed, never synthesizes.

LOADER (frozen staging gate, fail closed): a (symbol, metrics_date) cell is
valid iff it carries exactly 288 rows, 288 unique ``create_time`` labels
forming the full 00:00..23:55 grid, sorted ascending by create_time, with
finite positive values in the two authorized fields
(``sum_taker_long_short_vol_ratio``, ``sum_open_interest_value``) and
``ts`` equal to the parsed ``create_time`` label (row identity normalized to
snapshot time).  Any violation REFUSES THE CELL (recorded defect; the cell
counts as missing for the hole rule) -- never a partial repair.  The four
global defect dates (2025-07-21, 2025-07-22, 2025-08-29, 2026-08-12) are
excluded before parsing.  A missing symbol file is a hard failure.

The taker ratio is a FLOW field (``[T, T+5min)`` at label T): the daily
aggregate consumes each label of its own metrics_date exactly once -- a
boundary stamp appears in exactly one 5-minute bucket of one day, never in
two aggregates.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Mapping, Optional

from research.adapter_v10.protocol import ContractViolation
from research.v15.families.taker_sat.frozen_identity import (
    CHURN_FLOOR_C,
    GLOBAL_DEFECT_DATES,
    LAG_DAYS,
    LOG_CLIP_ABS,
    RATIO_CLIP_HI,
    RATIO_CLIP_LO,
)

DAY_NS = 86_400_000_000_000
#: 288 five-minute labels per metrics day (00:00 .. 23:55).
LABELS_PER_DAY = 288

#: Reasons recorded in the refusal registry / defect census.
DEFECT_GRID_INCOMPLETE = "METRICS_GRID_INCOMPLETE"
DEFECT_DUPLICATE_LABEL = "METRICS_DUPLICATE_LABEL"
DEFECT_NOT_SORTED = "METRICS_NOT_SORTED"
DEFECT_BAD_VALUE = "METRICS_BAD_VALUE"
DEFECT_TS_LABEL_MISMATCH = "METRICS_TS_LABEL_MISMATCH"
MISSING_GLOBAL_DEFECT_DATE = "GLOBAL_DEFECT_DATE"
REFUSE_HOLE_FRACTION = "HOLE_FRACTION_EXCEEDED"
REFUSE_ENDPOINT_MISSING = "WINDOW_ENDPOINT_MISSING"
REFUSE_CHURN_UNDEFINED = "CHURN_UNDEFINED"
REFUSE_NON_FINITE = "NON_FINITE_FEATURE"


class StagedDataError(ContractViolation):
    """A staged input is structurally unusable -- fail closed, never guess."""


# --------------------------------------------------------------------------- #
# Pure feature math (golden-testable; no I/O)
# --------------------------------------------------------------------------- #
def clip_log_ratio(raw_ratio: float) -> float:
    """``clip(ln clip(r_t, 0.2, 5.0), -1.609, +1.609)`` (frozen hygiene)."""
    r = float(raw_ratio)
    if not math.isfinite(r) or r <= 0.0:
        raise ContractViolation(
            f"taker ratio must be finite positive before the hygiene clip, "
            f"got {r!r} (fail-closed)"
        )
    r = min(max(r, RATIO_CLIP_LO), RATIO_CLIP_HI)
    value = math.log(r)
    return min(max(value, -LOG_CLIP_ABS), LOG_CLIP_ABS)


def daily_aggression(label_ratios: Mapping[Any, float]) -> float:
    """``a_i_d``: mean of the clipped log ratio over ONE metrics_date's labels.

    ``label_ratios`` maps the 288 five-minute labels of a single metrics_date
    to the raw ``sum_taker_long_short_vol_ratio`` value.  Each label is the
    FLOW window ``[T, T+5min)``: it is consumed exactly once -- the map keys
    enforce bucket identity, so a boundary stamp can never enter two daily
    aggregates.  The full 288-label set is required (a refused cell never
    reaches this function).
    """
    if len(label_ratios) != LABELS_PER_DAY:
        raise ContractViolation(
            f"daily aggression requires exactly {LABELS_PER_DAY} labels, got "
            f"{len(label_ratios)} (refused cells never aggregate)"
        )
    seen: set[Any] = set()
    clipped: list[float] = []
    for label, raw in label_ratios.items():
        if label in seen:
            raise ContractViolation(
                f"duplicate 5-minute label {label!r} in one metrics_date "
                "(a stamp must appear in exactly one bucket)"
            )
        seen.add(label)
        clipped.append(clip_log_ratio(raw))
    return math.fsum(clipped) / float(LABELS_PER_DAY)


def positioning_churn(oi_first: float, oi_last: float) -> float:
    """``O = |ln(OIv_2355(d_last) / OIv_2355(d_first))|`` (frozen definition)."""
    a = float(oi_first)
    b = float(oi_last)
    if not (math.isfinite(a) and a > 0.0) or not (math.isfinite(b) and b > 0.0):
        raise ContractViolation(
            "positioning churn requires finite positive OI values at both "
            f"window endpoints (got {a!r}, {b!r}); the decision is refused, "
            "never synthesized"
        )
    return abs(math.log(b / a))


def saturation_score(a_bar: float, churn: float, c: float = CHURN_FLOOR_C) -> float:
    """``S = A_bar / (O + c)`` with the frozen regularization floor c = 0.02."""
    a = float(a_bar)
    o = float(churn)
    if not math.isfinite(a) or not math.isfinite(o) or o + float(c) <= 0.0:
        raise ContractViolation("saturation score inputs must be finite")
    return a / (o + float(c))


def window_dates(decision_date_ns: int, window_days: int) -> list[int]:
    """Metrics-day midnight stamps ``[D-3-(n-1) .. D-3]`` (chronological).

    The lag is structural: the LAST date of the window is ``D - LAG_DAYS``,
    so nothing at or after ``D - 2`` can ever enter a feature (a mutation of
    those rows cannot move any decision -- test-pinned).
    """
    n = int(window_days)
    if n < 2:
        raise ContractViolation("window_days must be >= 2")
    day = int(decision_date_ns) // DAY_NS
    last = day - int(LAG_DAYS)
    return [(last - n + 1 + k) * DAY_NS for k in range(n)]


def ns_to_date_str(ns: int) -> str:
    from research.v11.families.oilever_delev.strategy import iso_utc

    return iso_utc(int(ns))[:10]


def date_str_to_ns(date_str: str) -> int:
    from research.v11.families.oilever_delev.strategy import parse_iso_utc

    return parse_iso_utc(f"{str(date_str)}T00:00:00Z")


# --------------------------------------------------------------------------- #
# Per-arm feature evaluation over the loaded daily structures
# --------------------------------------------------------------------------- #
def evaluate_symbol_feature(
    *,
    window_days: int,
    with_churn: bool,
    daily_by_date: Mapping[int, Mapping[str, float]],
    decision_date_ns: int,
) -> tuple[Optional[float], Optional[str]]:
    """One symbol's arm feature at decision date D, or a refusal reason.

    Returns ``(score, None)`` when the symbol is AVAILABLE, or
    ``(None, reason)`` when its decision is REFUSED (hole fraction exceeded,
    churn endpoint missing/undefined, non-finite result).  Refused decisions
    never become fills and never synthesize data.  The control arm passes
    ``with_churn=False``: its feature consumes the daily aggression window
    only (no OI endpoint -- structurally independent of the anchor).
    """
    dates = window_dates(decision_date_ns, int(window_days))
    present: list[tuple[int, float]] = []
    missing = 0
    for day_ns in dates:
        day = daily_by_date.get(day_ns)
        if day is None or "a" not in day:
            missing += 1
            continue
        present.append((day_ns, float(day["a"])))
    # amendment-1 hole rule, integer-exact: MORE than 10% missing refuses
    # (missing/n > 1/10  <=>  10 * missing > n; exactly 10% still computes).
    if 10 * missing > len(dates):
        return None, REFUSE_HOLE_FRACTION
    if not present:
        return None, REFUSE_HOLE_FRACTION
    a_bar = math.fsum(a for _d, a in present) / float(len(present))
    if not math.isfinite(a_bar):
        return None, REFUSE_NON_FINITE
    if not with_churn:
        return a_bar, None
    first_ns, last_ns = dates[0], dates[-1]
    first = daily_by_date.get(first_ns)
    last = daily_by_date.get(last_ns)
    if first is None or "oi2355" not in first or last is None or "oi2355" not in last:
        return None, REFUSE_ENDPOINT_MISSING
    try:
        churn = positioning_churn(first["oi2355"], last["oi2355"])
    except ContractViolation:
        return None, REFUSE_CHURN_UNDEFINED
    score = saturation_score(a_bar, churn)
    if not math.isfinite(score):
        return None, REFUSE_NON_FINITE
    return score, None


# --------------------------------------------------------------------------- #
# Staged metrics loader (fail-closed per the frozen staging gate)
# --------------------------------------------------------------------------- #
_AUTHORIZED_FIELDS = (
    "sum_taker_long_short_vol_ratio",
    "sum_open_interest_value",
)


def _label_set() -> set[str]:
    labels: set[str] = set()
    for hour in range(24):
        for minute in (0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55):
            labels.add(f"{hour:02d}:{minute:02d}:00")
    return labels


_EXPECTED_LABELS = _label_set()


def load_metrics_daily(
    data_root,
    universe,
    *,
    global_defect_dates=frozenset(GLOBAL_DEFECT_DATES),
):
    """Load per-symbol daily aggregates from the staged metrics parquet root.

    Returns ``(daily, defects)`` where ``daily`` maps
    ``symbol -> {day_ns -> {"a": daily aggression, "oi2355": OI value at the
    23:55 label}}`` for every VALID metrics_date cell, and ``defects`` is the
    list of ``{"symbol", "date", "reason"}`` refusals (global defect dates +
    per-cell integrity violations).  Refused cells are MISSING data for the
    hole rule -- never repaired, never synthesized.  Missing symbol files
    raise :class:`StagedDataError`.
    """
    import pandas as pd

    daily: dict[str, dict[int, dict[str, float]]] = {}
    defects: list[dict[str, str]] = []
    for sym in sorted(str(s) for s in universe):
        path = Path(data_root) / "metrics" / f"{sym}.parquet"
        if not path.is_file():
            raise StagedDataError(f"{sym}: metrics parquet missing: {path}")
        frame = pd.read_parquet(path)
        for column in ("create_time", "ts", *_AUTHORIZED_FIELDS):
            if column not in frame.columns:
                raise StagedDataError(f"{sym}: metrics column missing: {column}")
        frame = frame.sort_values("create_time", kind="mergesort")
        stamps = pd.to_datetime(frame["create_time"], format="%Y-%m-%d %H:%M:%S")
        frame = frame.assign(_day=stamps.dt.strftime("%Y-%m-%d"), _time=stamps.dt.strftime("%H:%M:%S"))
        ts_series = pd.to_datetime(frame["ts"])
        if not bool((ts_series.values == stamps.values).all()):
            raise StagedDataError(
                f"{sym}: ts column disagrees with the create_time label "
                "(row identity must be normalized to snapshot time)"
            )
        by_day = dict(tuple(frame.groupby("_day", sort=True)))
        sym_daily: dict[int, dict[str, float]] = {}
        for date_str, day_frame in by_day.items():
            if date_str in global_defect_dates:
                defects.append(
                    {"symbol": sym, "date": date_str, "reason": MISSING_GLOBAL_DEFECT_DATE}
                )
                continue
            if len(day_frame) != LABELS_PER_DAY:
                defects.append(
                    {"symbol": sym, "date": date_str, "reason": DEFECT_GRID_INCOMPLETE}
                )
                continue
            times = list(day_frame["_time"])
            if len(set(times)) != LABELS_PER_DAY:
                defects.append(
                    {"symbol": sym, "date": date_str, "reason": DEFECT_DUPLICATE_LABEL}
                )
                continue
            if set(times) != _EXPECTED_LABELS:
                defects.append(
                    {"symbol": sym, "date": date_str, "reason": DEFECT_GRID_INCOMPLETE}
                )
                continue
            ratio = day_frame["sum_taker_long_short_vol_ratio"]
            oi = day_frame["sum_open_interest_value"]
            if bool(ratio.isna().any()) or bool(oi.isna().any()):
                defects.append(
                    {"symbol": sym, "date": date_str, "reason": DEFECT_BAD_VALUE}
                )
                continue
            r_vals = [float(v) for v in ratio]
            o_vals = [float(v) for v in oi]
            if any((not math.isfinite(v)) or v <= 0.0 for v in r_vals) or any(
                (not math.isfinite(v)) or v <= 0.0 for v in o_vals
            ):
                defects.append(
                    {"symbol": sym, "date": date_str, "reason": DEFECT_BAD_VALUE}
                )
                continue
            total = 0.0
            for v in r_vals:
                total += clip_log_ratio(v)
            oi2355 = o_vals[list(times).index("23:55:00")]
            sym_daily[date_str_to_ns(date_str)] = {
                "a": total / float(LABELS_PER_DAY),
                "oi2355": oi2355,
            }
        daily[sym] = sym_daily
    return daily, defects


def symbol_scores_at(
    *,
    arm_window_days: int,
    arm_with_churn: bool,
    daily: Mapping[str, Mapping[int, Mapping[str, float]]],
    universe,
    decision_date_ns: int,
    refusals=None,
) -> dict[str, float]:
    """Cross-sectional scores of ONE arm at decision date D (available only).

    A symbol whose feature refuses is simply absent (its refusal is recorded
    when a ``refusals`` registry is supplied); it is never guessed.
    """
    scores: dict[str, float] = {}
    for sym in sorted(str(s) for s in universe):
        score, reason = evaluate_symbol_feature(
            window_days=arm_window_days,
            with_churn=arm_with_churn,
            daily_by_date=daily.get(sym, {}),
            decision_date_ns=decision_date_ns,
        )
        if reason is None:
            scores[sym] = float(score)
        elif refusals is not None:
            refusals.record(
                ns_to_date_str(decision_date_ns), sym, reason,
                detail={"window_days": int(arm_window_days)},
            )
    return scores


__all__ = [
    "DAY_NS",
    "DEFECT_BAD_VALUE",
    "DEFECT_DUPLICATE_LABEL",
    "DEFECT_GRID_INCOMPLETE",
    "DEFECT_NOT_SORTED",
    "DEFECT_TS_LABEL_MISMATCH",
    "LABELS_PER_DAY",
    "MISSING_GLOBAL_DEFECT_DATE",
    "REFUSE_CHURN_UNDEFINED",
    "REFUSE_ENDPOINT_MISSING",
    "REFUSE_HOLE_FRACTION",
    "REFUSE_NON_FINITE",
    "StagedDataError",
    "clip_log_ratio",
    "daily_aggression",
    "date_str_to_ns",
    "evaluate_symbol_feature",
    "load_metrics_daily",
    "ns_to_date_str",
    "positioning_churn",
    "saturation_score",
    "symbol_scores_at",
    "window_dates",
]
