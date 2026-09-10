"""Legacy hourly decision schedule projection — timestamps/ids/constants (A6).

Freeze authority: research/control/market_data_plane_v2_run/architecture_freeze_v2.json
(p3_wave_sha 09a223f6ce166e219beb67b25b8151361979ca21), frozen interface
``project_decision_schedule(result, context) -> list[dict]``:
"schedule-only decision rows with one-bar (or declared) availability lag; NO
PnL, NO signals beyond schedule, NO selection" and the forex
``legacy_parity_target``: "legacy hourly decision schedule parity on an
authorized S0 subset (SYNTHETIC ONLY in V2)".

Row semantics:

* exactly ONE decision row per completed bar;
* exactly ONE completed-bar availability lag: ``decision_time_utc_ns ==
  available_time_utc_ns == close_time_utc_ns +
  context.publication_lag_ns`` (the frozen provider publication-lag
  constant; default lag 0 == close_time);
* date-only next-day-exclusive availability bounds (the Data Fusion PIT
  rule for macro rows) are NOT applicable here — bars are timestamped and
  every row carries exact UTC nanosecond timestamps;
* rows carry TIMESTAMPS, IDS and CONSTANTS ONLY.  A denylist guard
  (``PNL_DENYLIST_PATTERN``) fails closed if any row key ever matches the
  PnL/returns/metrics family — the schedule can never grow a PnL column by
  accident.

stdlib + sibling modules only; never mutates its inputs.
"""

from __future__ import annotations

import re

from market_data_plane import bars as _bars

from .adapter import AdapterResult
from .context import AdapterContext

__all__ = [
    "SCHEDULE_ROW_KIND",
    "SCHEDULE_ROW_FIELDS",
    "PNL_DENYLIST_PATTERN",
    "project_decision_schedule",
]

#: Constant row kind (an id, not a computation).
SCHEDULE_ROW_KIND = "FOREX_HOURLY_DECISION_ROW"

#: Exact row field list — timestamps, ids and constants ONLY (order frozen).
SCHEDULE_ROW_FIELDS: tuple[str, ...] = (
    "row_kind",
    "instrument_id",
    "venue",
    "interval_ns",
    "bar_id",
    "bar_open_time_utc_ns",
    "bar_close_time_utc_ns",
    "available_time_utc_ns",
    "decision_time_utc_ns",
    "publication_lag_ns",
    "normalizer_version",
)

#: PnL-family denylist: NO schedule row key may match (fail-closed guard).
PNL_DENYLIST_PATTERN = re.compile(
    r"pnl|profit|return|sharpe|drawdown|cost|fee", re.IGNORECASE)


def _assert_no_pnl_keys(row: dict) -> None:
    leaked = [key for key in row if PNL_DENYLIST_PATTERN.search(str(key))]
    if leaked:
        raise AssertionError(
            f"decision schedule leak guard: forbidden key(s) {leaked}; "
            f"schedule rows carry timestamps/ids/constants only "
            f"(NO PnL/returns/metrics)")


def project_decision_schedule(result: AdapterResult,
                              context: AdapterContext) -> list[dict]:
    """One schedule row per completed bar; exactly one availability lag.

    Fail closed on a non-:class:`AdapterResult` first argument.  Rows are
    plain dicts with the exact :data:`SCHEDULE_ROW_FIELDS` key set, ordered
    like the bars (strictly increasing bar open times, enforced upstream by
    the stream normalizer).
    """
    if not isinstance(result, AdapterResult):
        raise _bars.BarError(
            "MALFORMED_SHAPE",
            f"project_decision_schedule expects an AdapterResult, "
            f"got {type(result).__name__}")

    rows: list[dict] = []
    for bar in result.bars:
        row = {
            "row_kind": SCHEDULE_ROW_KIND,
            "instrument_id": bar["instrument_id"],
            "venue": bar["venue"],
            "interval_ns": bar["interval_ns"],
            "bar_id": bar["bar_id"],
            "bar_open_time_utc_ns": bar["open_time_utc_ns"],
            "bar_close_time_utc_ns": bar["close_time_utc_ns"],
            "available_time_utc_ns": bar["available_time_utc_ns"],
            "decision_time_utc_ns": bar["available_time_utc_ns"],
            "publication_lag_ns": context.publication_lag_ns,
            "normalizer_version": context.normalizer_version,
        }
        if tuple(row) != SCHEDULE_ROW_FIELDS:
            raise AssertionError("internal error: schedule row field drift")
        _assert_no_pnl_keys(row)
        rows.append(row)
    return rows
