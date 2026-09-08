"""F6 family-1 implementation: FROZEN proposal FXFV1-A3-P1 (FOREX-FREE-V1).

London-Open Session Continuation: 3-bar post-open momentum, flattened
strictly before the NY rollover.

AUTHORITATIVE SPEC: research/proposals/forex_free_v1/a3_lane/proposal_1.json
(frozen in F5 via research/control/forex_free_v1_run/selection_freeze.json,
before any outcome was observed).  This module implements that spec exactly:
no redesign, no tuning, and no scoring of returns on real data.  Label:
RESEARCH_CANDIDATE_NOT_LIVE_READY.

Frozen contracts implemented here (fail closed, always):

* ``load_bars`` validates normalized H1 OHLC bars in UTC; malformed rows,
  missing fields, non-finite / non-positive / internally inconsistent
  prices, non-hour-aligned stamps and duplicate timestamps are rejected;
* the signal uses COMPLETED bars only: a bar timestamped T (bar open) is
  completed at T + 1h.  Session anchors are frozen wall times in named
  IANA zones via :mod:`zoneinfo` (never fixed offsets, never derived from
  data): London open L = 08:00 Europe/London (anchor + causal control),
  New York open N = 08:00 America/New_York (neighbour).  Session
  membership of every signal bar is asserted in the session's own zone so
  BST/GMT and EST/EDT are always DST-correct;
* momentum m = c3/c0 - 1 with c0 = close of the last completed bar with
  end <= session open (the bar [open-1h, open)) and c3 = close of the 3rd
  session bar (bar [open+2h, open+3h)); the signal is public at open+3h
  and the signal bar is complete before any entry.  Positions:
  anchor and neighbour take sign(m); the causal control takes -sign(m)
  (anti-momentum, identical timing); m == 0 -> no trade;
* entry fills at the CLOSE of the NEXT completed H1 bar after the signal
  bar (bar [open+3h, open+4h), fill instant open+4h), conservative
  close-to-close; the worst cost cell (x2.0) shifts the entry fill one
  additional completed bar later (t+2 close instead of t+1 close); the
  flatten rule is never delayed;
* flatten at the close of the last completed H1 bar whose end is
  STRICTLY BEFORE the same weekday's 17:00 America/New_York rollover.
  Hourly bars end on whole hours, so the flatten bar uniformly ends at
  16:00 New York wall clock (bar end 20:00Z in EDT weeks, 21:00Z in EST
  weeks); that exact bar is REQUIRED -- if it is absent the pair-day is
  NO_TRADE (fail closed), never substituted with an earlier bar;
* missing required bars (c0, c3, entry fill bar, flatten bar) make the
  pair-day NO_TRADE with an explicit reason; no interpolation, no
  carry-over of signals; one position per pair per day; no re-entry;
* costs are a frozen PROXY declared a priori: 1.5 bps per side x
  {1.0, 1.5, 2.0} applied to every fill (entry and exit), so the base
  round trip is 3.0 bps; no bid/ask series is used or assumed;
* ``run_arm`` is schedule-only feasibility: decisions / fills /
  cashflows / costs / turnover / decisions-per-year and a canonical JSON
  of the whole run.  No return series is scored and nothing in this
  module authorizes scoring;
* every position is flattened before the rollover instant of its own
  trade day: no overnight, no financing, no weekend exposure (the Friday
  flatten coincides with the frozen Friday 16:00 America/New_York week
  close).

All instants are computed in America/New_York + Europe/London named zones
with an explicit fold policy (fold=0) and a round-trip check that fails
closed on nonexistent or ambiguous local wall times.  Whole-hour
bar-boundary alignment of session and rollover instants is asserted.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence
from zoneinfo import ZoneInfo

__all__ = [
    "FAMILY_ID",
    "LABEL",
    "ARM_IDS",
    "COST_TIERS",
    "BASE_BPS_PER_SIDE",
    "MOMENTUM_BARS",
    "Family1Error",
    "SignalUnavailable",
    "Bar",
    "load_bars",
    "signal",
    "arm_day_plan",
    "build_schedule",
    "run_arm",
    "arm_identity",
    "frozen_arm_configs",
    "compute_metrics",
    "publish",
    "canonical_json",
    "sha256_hex",
]

FAMILY_ID = "FXFV1-A3-P1"
LABEL = "RESEARCH_CANDIDATE_NOT_LIVE_READY"

UTC = timezone.utc
LONDON_ZONE = "Europe/London"
NEW_YORK_ZONE = "America/New_York"
_LONDON = ZoneInfo(LONDON_ZONE)
_NEW_YORK = ZoneInfo(NEW_YORK_ZONE)

# Frozen session clocks (proposal_1.json "dst_session_clock_spec").
SESSION_OPEN_WALL_HOUR = 8  # 08:00 London (anchor/control) and 08:00 New York (neighbour)
ROLLOVER_WALL_HOUR = 17  # 17:00 America/New_York daily rollover
MOMENTUM_BARS = 3  # the only momentum window; no grid permitted
BASE_BPS_PER_SIDE = 1.5  # frozen proxy spread cost, per fill side
COST_TIERS = (1.0, 1.5, 2.0)  # frozen cost-stress multipliers (S1, S2, S3)
WORST_TIER = 2.0  # S3: additionally one-event entry delay
ONE_HOUR = timedelta(hours=1)
YEAR_SECONDS = 365.25 * 86400.0

ARM_IDS = ("anchor", "neighbour", "control")

NO_TRADE_MISSING_BAR = "MISSING_BAR"
NO_TRADE_ZERO_MOMENTUM = "ZERO_MOMENTUM"

RUN_SCHEMA = "forex_free_v1_family1_run_v1"
LEDGER_SCHEMA = "forex_free_v1_family1_temp_ledger_v1"
ARM_IDENTITY_SCHEMA = "forex_free_v1_family1_arm_identity_v1"

_EXTRA_DELAY_ALLOWED = (0, 1)  # 0 = S1/S2, 1 = the frozen S3 one-event delay


class Family1Error(ValueError):
    """Any fail-closed violation of the frozen FXFV1-A3-P1 contracts."""


class SignalUnavailable(Family1Error):
    """A required bar for a pair-day is absent: the day must be NO_TRADE."""


# --------------------------------------------------------------------------- #
# Bars
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Bar:
    """One completed-when-over H1 bar; ``ts`` is the bar OPEN (aware UTC)."""

    ts: datetime
    open: float
    high: float
    low: float
    close: float

    @property
    def end(self) -> datetime:
        """The instant at which this bar is COMPLETED (open + 1h)."""
        return self.ts + ONE_HOUR


def parse_utc_timestamp(value: Any, field: str) -> datetime:
    """Parse an instant that must be an aware UTC whole-hour timestamp."""
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        text = value.strip()
        if text.endswith(("Z", "z")):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError as exc:
            raise Family1Error(f"{field}: malformed timestamp {value!r}: {exc}") from exc
    else:
        raise Family1Error(f"{field}: timestamp must be an ISO-8601 UTC string or datetime, got {type(value).__name__}")
    if dt.tzinfo is None:
        raise Family1Error(f"{field}: timestamp {value!r} is naive; UTC-aware required (fail closed)")
    dt = dt.astimezone(UTC)
    if dt.utcoffset() != timedelta(0):
        raise Family1Error(f"{field}: timestamp {value!r} is not UTC (fail closed)")
    return dt


def _validate_price(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise Family1Error(f"{field}: price must be a real number, got {type(value).__name__}")
    price = float(value)
    if not math.isfinite(price):
        raise Family1Error(f"{field}: price must be finite, got {price!r}")
    if price <= 0.0:
        raise Family1Error(f"{field}: price must be positive, got {price!r}")
    return price


def load_bars(rows: Sequence[Mapping[str, Any]]) -> tuple[Bar, ...]:
    """Validate normalized H1 OHLC bars and return them sorted by open time.

    Each row: {"timestamp": UTC instant string, "open"/"high"/"low"/"close":
    positive finite floats}.  Fails closed on malformed or missing fields,
    non-finite or inconsistent prices, non-hour-aligned stamps, and
    duplicate timestamps.  Gaps (weekends, holidays) are NOT errors here;
    they surface later as fail-closed NO_TRADE pair-days.
    """
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        raise Family1Error("bars: rows must be a sequence of row mappings")
    if len(rows) == 0:
        raise Family1Error("bars: at least one bar row is required (fail closed on empty input)")
    bars: list[Bar] = []
    seen: set[datetime] = set()
    for i, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise Family1Error(f"bars[{i}]: row must be a mapping, got {type(row).__name__}")
        missing = [key for key in ("timestamp", "open", "high", "low", "close") if key not in row]
        if missing:
            raise Family1Error(f"bars[{i}]: missing required field(s) {missing}")
        ts = parse_utc_timestamp(row["timestamp"], f"bars[{i}].timestamp")
        if ts.minute != 0 or ts.second != 0 or ts.microsecond != 0:
            raise Family1Error(f"bars[{i}]: timestamp {ts.isoformat()} is not an H1 bar boundary (whole hour required)")
        if ts in seen:
            raise Family1Error(f"bars[{i}]: duplicate bar timestamp {ts.isoformat()} (fail closed)")
        seen.add(ts)
        o = _validate_price(row["open"], f"bars[{i}].open")
        h = _validate_price(row["high"], f"bars[{i}].high")
        lo = _validate_price(row["low"], f"bars[{i}].low")
        c = _validate_price(row["close"], f"bars[{i}].close")
        if h < max(o, c) or lo > min(o, c) or h < lo:
            raise Family1Error(
                f"bars[{i}]: inconsistent OHLC at {ts.isoformat()} "
                f"(open={o}, high={h}, low={lo}, close={c})"
            )
        bars.append(Bar(ts=ts, open=o, high=h, low=lo, close=c))
    bars.sort(key=lambda b: b.ts)
    return tuple(bars)


def _bar_index(bars: Sequence[Bar]) -> dict[datetime, Bar]:
    """Index bars by open timestamp; fail closed if unsorted or duplicated."""
    index: dict[datetime, Bar] = {}
    previous: datetime | None = None
    for bar in bars:
        if not isinstance(bar, Bar):
            raise Family1Error(f"bars: expected Bar records, got {type(bar).__name__}")
        if previous is not None and bar.ts <= previous:
            raise Family1Error(f"bars: timestamps not strictly increasing at {bar.ts.isoformat()}")
        index[bar.ts] = bar
        previous = bar.ts
    return index


def _require_bar(index: dict[datetime, Bar], start: datetime, role: str) -> Bar:
    bar = index.get(start)
    if bar is None:
        raise SignalUnavailable(f"{NO_TRADE_MISSING_BAR}: required {role} bar starting {start.isoformat()} absent")
    return bar


# --------------------------------------------------------------------------- #
# Frozen session clocks (named zones only; fold policy explicit)
# --------------------------------------------------------------------------- #


def _resolve_wall_instant(day: date, hour: int, minute: int, zone: ZoneInfo, zone_name: str, purpose: str) -> datetime:
    """Resolve a naive local wall time to an aware UTC instant, fail closed.

    Nonexistent wall times (DST spring-forward gap) are rejected by
    round-trip check; ambiguous wall times (fall-back) resolve by the
    explicit fold=0 (earlier instant) policy.  The resulting UTC instant
    must land on an H1 bar boundary (whole hour) -- for whole-hour wall
    times this asserts that the zone's UTC offset is a whole number of
    hours (true for Europe/London and America/New_York; violated zones
    fail closed per the frozen spec).
    """
    wall = datetime(day.year, day.month, day.day, hour, minute, tzinfo=zone, fold=0)
    instant = wall.astimezone(UTC)
    back = instant.astimezone(zone)
    if (back.year, back.month, back.day, back.hour, back.minute) != (day.year, day.month, day.day, hour, minute):
        raise Family1Error(
            f"{purpose}: local wall time {hour:02d}:{minute:02d} on {day.isoformat()} "
            f"does not exist or is ambiguous in {zone_name} (fold policy fold=0; fail closed)"
        )
    if instant.minute != 0 or instant.second != 0 or instant.microsecond != 0:
        raise Family1Error(
            f"{purpose}: {hour:02d}:{minute:02d} {zone_name} on {day.isoformat()} "
            f"maps to non-bar-boundary UTC instant {instant.isoformat()} (whole-hour alignment asserted)"
        )
    return instant


def _rollover_instant(trade_day: date) -> datetime:
    """R = 17:00 America/New_York on the trade day (22:00Z EST, 21:00Z EDT)."""
    return _resolve_wall_instant(trade_day, ROLLOVER_WALL_HOUR, 0, _NEW_YORK, NEW_YORK_ZONE, "NY rollover")


def _session_open_instant(trade_day: date, zone: ZoneInfo, zone_name: str) -> datetime:
    """L or N = 08:00 in the arm's session zone on the trade day."""
    return _resolve_wall_instant(trade_day, SESSION_OPEN_WALL_HOUR, 0, zone, zone_name, "session open")


def _assert_session_membership(bar_start: datetime, trade_day: date, zone: ZoneInfo, zone_name: str, offset_bars: int) -> None:
    """Assert a signal-window bar really sits at the expected in-session wall time."""
    wall = bar_start.astimezone(zone)
    expected_hour = SESSION_OPEN_WALL_HOUR + offset_bars
    if wall.date() != trade_day or wall.hour != expected_hour or wall.minute != 0:
        raise Family1Error(
            f"session membership violated: bar starting {bar_start.isoformat()} is not at "
            f"{expected_hour:02d}:00 {zone_name} on {trade_day.isoformat()} (DST-correct membership asserted)"
        )


# --------------------------------------------------------------------------- #
# Frozen arm definitions
# --------------------------------------------------------------------------- #


def frozen_arm_configs() -> dict[str, dict[str, Any]]:
    """The three frozen arm configurations, exactly as declared in the spec.

    anchor   : London-open 3-bar continuation (position = sign(m)).
    neighbour: New York-open analogue, identical construction (position = sign(m)),
               the theoretically weaker same-signed variant.
    control  : sign-flipped anchor (anti-momentum, position = -sign(m)),
               identical signal timing, fills, flatten rule and costs.
    """
    common = {
        "session_open_wall_hour": SESSION_OPEN_WALL_HOUR,
        "momentum_bars": MOMENTUM_BARS,
        "rollover_zone": NEW_YORK_ZONE,
        "rollover_wall_hour": ROLLOVER_WALL_HOUR,
        "execution": "next_completed_bar_close",
        "flatten": "last_completed_bar_end_strictly_before_rollover",
        "base_cost_bps_per_side": BASE_BPS_PER_SIDE,
    }
    return {
        "anchor": {**common, "session_zone": LONDON_ZONE, "position_sign": 1},
        "neighbour": {**common, "session_zone": NEW_YORK_ZONE, "position_sign": 1},
        "control": {**common, "session_zone": LONDON_ZONE, "position_sign": -1},
    }


def _arm_settings(arm_id: Any) -> tuple[str, ZoneInfo, int]:
    if not isinstance(arm_id, str) or arm_id not in ARM_IDS:
        raise Family1Error(f"arm_id must be one of {ARM_IDS}, got {arm_id!r}")
    config = frozen_arm_configs()[arm_id]
    zone_name = config["session_zone"]
    return zone_name, ZoneInfo(zone_name), config["position_sign"]


# --------------------------------------------------------------------------- #
# Canonical JSON / digests
# --------------------------------------------------------------------------- #


def _canonical(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise Family1Error(f"canonical JSON: non-finite float {value!r} is not allowed")
        return round(value, 12)
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    raise Family1Error(f"canonical JSON: unsupported type {type(value).__name__} (fail closed)")


def canonical_json(value: Any) -> str:
    """Deterministic canonical JSON: sorted keys, tight separators, quantized floats."""
    return json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def arm_identity(arm_id: Any, config: Mapping[str, Any]) -> str:
    """Canonical sha256 identity of an arm under its frozen configuration.

    The anchor, the NY-open neighbour and the sign-flipped causal control
    MUST produce three distinct digests (different session zone and/or
    position sign); the digest is stable across calls (pure function of
    the canonical payload).
    """
    if not isinstance(arm_id, str) or arm_id not in ARM_IDS:
        raise Family1Error(f"arm_id must be one of {ARM_IDS}, got {arm_id!r}")
    if not isinstance(config, Mapping):
        raise Family1Error(f"config must be a mapping, got {type(config).__name__}")
    payload = {
        "schema": ARM_IDENTITY_SCHEMA,
        "family_id": FAMILY_ID,
        "label": LABEL,
        "arm_id": arm_id,
        "config": config,
    }
    return sha256_hex(canonical_json(payload))


# --------------------------------------------------------------------------- #
# Signal (completed bars only; public at session_open + 3h)
# --------------------------------------------------------------------------- #


def _coerce_day(value: Any, field: str) -> date:
    if isinstance(value, datetime):
        return value.astimezone(UTC).date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise Family1Error(f"{field}: malformed date {value!r}: {exc}") from exc
    raise Family1Error(f"{field}: date must be YYYY-MM-DD, got {type(value).__name__}")


def _signal_position(bars: Sequence[Bar], arm_id: str, trade_day: date) -> dict[str, Any]:
    """Compute the frozen 3-bar session momentum position for one pair-day.

    Raises SignalUnavailable when a required signal bar is absent (the
    caller must turn that into a counted NO_TRADE pair-day).
    """
    zone_name, zone, position_sign = _arm_settings(arm_id)
    if trade_day.weekday() >= 5:
        raise Family1Error(
            f"{arm_id}: {trade_day.isoformat()} is a weekend; the frozen week contains no "
            "session signal on Sat/Sun (Sunday 21:00 New York open maps to Monday's FX day)"
        )
    index = _bar_index(bars)
    open_instant = _session_open_instant(trade_day, zone, zone_name)

    # c0: close of the last completed bar with end <= session open
    # (whole-hour grid => the bar starting one hour before the open).
    c0_bar = _require_bar(index, open_instant - ONE_HOUR, f"{arm_id} c0 (pre-open)")
    c0_end_wall = c0_bar.end.astimezone(zone)
    if c0_end_wall.date() != trade_day or c0_end_wall.hour != SESSION_OPEN_WALL_HOUR:
        raise Family1Error(f"{arm_id}: c0 bar does not complete at the {zone_name} session open (fail closed)")

    # c1..c3: the first three session bars; c3 = close of bar [open+2h, open+3h).
    session_bars = []
    for offset in range(MOMENTUM_BARS):
        start = open_instant + offset * ONE_HOUR
        _assert_session_membership(start, trade_day, zone, zone_name, offset)
        session_bars.append(_require_bar(index, start, f"{arm_id} session bar {offset + 1}"))
    c3_bar = session_bars[-1]
    signal_ts = c3_bar.end  # public instant: session open + 3h, signal bar complete

    momentum = c3_bar.close / c0_bar.close - 1.0
    if not math.isfinite(momentum):
        raise Family1Error(f"{arm_id}: non-finite momentum on {trade_day.isoformat()} (fail closed)")
    raw_sign = 1 if momentum > 0.0 else (-1 if momentum < 0.0 else 0)
    return {
        "arm_id": arm_id,
        "trade_day": trade_day,
        "session_zone": zone_name,
        "session_open_utc": open_instant,
        "c0": c0_bar.close,
        "c3": c3_bar.close,
        "momentum": momentum,
        "raw_sign": raw_sign,
        "position_sign": position_sign,
        "position": raw_sign * position_sign,
        "signal_ts": signal_ts,
    }


def signal(bars: Sequence[Bar], arm_config: Mapping[str, Any]) -> int:
    """Frozen signal: +1 / -1 / 0 for one pair-day under one frozen arm.

    ``arm_config`` requires {"arm_id": anchor|neighbour|control,
    "signal_date": "YYYY-MM-DD"}.  The signal uses completed bars only and
    is fully public at session_open + 3h; the signal bar completes before
    any entry.  Raises SignalUnavailable when a required bar is missing
    (callers must convert that to a fail-closed NO_TRADE pair-day) and
    Family1Error on weekend dates or invalid configuration.
    """
    if not isinstance(arm_config, Mapping):
        raise Family1Error(f"arm_config must be a mapping, got {type(arm_config).__name__}")
    for key in ("arm_id", "signal_date"):
        if key not in arm_config:
            raise Family1Error(f"arm_config: missing required key {key!r}")
    arm_id = arm_config["arm_id"]
    trade_day = _coerce_day(arm_config["signal_date"], "arm_config.signal_date")
    return _signal_position(bars, arm_id, trade_day)["position"]


# --------------------------------------------------------------------------- #
# Schedule: next-allowed-bar entry, flatten strictly before the rollover
# --------------------------------------------------------------------------- #


def build_schedule(bars: Sequence[Bar], signal_ts: Any, *, extra_delay_events: int = 0) -> dict[str, Any]:
    """Entry/flatten schedule for one signal.

    ``signal_ts`` is the instant the signal became public (= close of the
    signal bar).  Entry = the NEXT allowed bar (the bar STARTING at
    signal_ts, i.e. never the signal bar itself), filled at that bar's
    close; ``extra_delay_events`` (0 or 1, the frozen S3 one-event delay)
    shifts the entry fill one additional completed bar later.  Flatten =
    the last completed H1 bar whose end is STRICTLY BEFORE the same
    trade day's 17:00 America/New_York rollover -- on the whole-hour grid
    that is exactly the bar ending 16:00 New York wall clock (20:00Z in
    EDT weeks, 21:00Z in EST weeks); that bar is required and is never
    substituted.  No position may span the rollover (no overnight).

    Raises SignalUnavailable if the signal, entry or flatten bar is
    absent, and Family1Error on any schedule invariant violation.
    """
    if extra_delay_events not in _EXTRA_DELAY_ALLOWED:
        raise Family1Error(f"extra_delay_events must be 0 or 1 (frozen), got {extra_delay_events!r}")
    signal_instant = parse_utc_timestamp(signal_ts, "signal_ts")
    if signal_instant.minute != 0 or signal_instant.second != 0 or signal_instant.microsecond != 0:
        raise Family1Error(f"signal_ts {signal_instant.isoformat()} is not an H1 bar boundary")

    index = _bar_index(bars)
    signal_bar = _require_bar(index, signal_instant - ONE_HOUR, "signal (3rd session) bar")
    if signal_bar.end != signal_instant:  # structural: end == ts + 1h
        raise Family1Error("signal bar end does not equal signal_ts (fail closed)")

    trade_day = signal_instant.astimezone(_NEW_YORK).date()
    rollover = _rollover_instant(trade_day)
    flatten_end = rollover - ONE_HOUR  # the bar ending exactly one hour before R
    flatten_start = flatten_end - ONE_HOUR

    entry_start = signal_instant + extra_delay_events * ONE_HOUR
    entry_bar = _require_bar(index, entry_start, "entry fill bar")
    entry_fill_instant = entry_bar.end

    flatten_bar = _require_bar(index, flatten_start, "flatten bar")
    if flatten_bar.end != flatten_end:
        raise Family1Error("flatten bar end invariant violated (fail closed)")

    if not signal_instant < entry_fill_instant:
        raise Family1Error("entry fill is not strictly after the signal instant (fail closed)")
    if not entry_fill_instant < flatten_end:
        raise Family1Error("entry fill is not strictly before the flatten bar end (fail closed)")
    if not flatten_end < rollover:
        raise Family1Error("flatten is not strictly before the rollover instant (fail closed)")
    entry_day = entry_fill_instant.astimezone(_NEW_YORK).date()
    flatten_day = flatten_end.astimezone(_NEW_YORK).date()
    if entry_day != trade_day or flatten_day != trade_day:
        raise Family1Error("entry/flatten do not sit on the signal's own New York trade day (overnight exposure forbidden)")

    return {
        "trade_day": trade_day,
        "rollover_utc": rollover,
        "signal_bar_start": signal_bar.ts,
        "signal_ts": signal_instant,
        "entry_bar_start": entry_bar.ts,
        "entry_fill_instant": entry_fill_instant,
        "entry_price": entry_bar.close,
        "flatten_bar_start": flatten_bar.ts,
        "flatten_end_utc": flatten_end,
        "flatten_price": flatten_bar.close,
        "extra_delay_events": extra_delay_events,
    }


def arm_day_plan(bars: Sequence[Bar], arm_id: str, trade_day: Any, *, extra_delay_events: int = 0) -> dict[str, Any]:
    """Full frozen plan for one pair-day under one arm: signal + schedule.

    Raises SignalUnavailable when any required bar is absent (the run
    layer records the pair-day as NO_TRADE / MISSING_BAR, fail closed).
    """
    day = _coerce_day(trade_day, "trade_day")
    position_part = _signal_position(bars, arm_id, day)
    schedule = build_schedule(bars, position_part["signal_ts"], extra_delay_events=extra_delay_events)
    return {**position_part, "schedule": schedule}


# --------------------------------------------------------------------------- #
# run_arm: schedule-only feasibility over the whole bar span
# --------------------------------------------------------------------------- #


def run_arm(bars: Sequence[Bar], arm_id: str, cost_tier: float, pair: str | None = None) -> dict[str, Any]:
    """Run one frozen arm over one cost-stress cell across the bar span.

    cost_tier in {1.0, 1.5, 2.0}: cost = 1.5 bps/side x tier on EVERY
    fill; tier 2.0 (S3) additionally applies the frozen one-event entry
    delay (fill at bar t+2 close instead of t+1; flatten unchanged).

    Returns decisions, fills, cashflows, costs_bps, turnover,
    decisions_per_year (schedule-only feasibility -- no return series is
    scored here) and the canonical JSON + sha256 of the whole run.
    Weekday pair-days with missing required bars are recorded as
    NO_TRADE / MISSING_BAR and counted (fail closed, no interpolation).
    """
    zone_name, _, _ = _arm_settings(arm_id)  # validates arm_id
    if isinstance(cost_tier, bool) or not isinstance(cost_tier, (int, float)) or float(cost_tier) not in COST_TIERS:
        raise Family1Error(f"cost_tier must be one of {COST_TIERS}, got {cost_tier!r}")
    tier = float(cost_tier)
    bps_per_side = BASE_BPS_PER_SIDE * tier  # 1.5 / 2.25 / 3.0 bps exactly
    round_trip_bps = 2.0 * bps_per_side
    extra_delay = 1 if tier == WORST_TIER else 0

    ordered = tuple(bars)
    _bar_index(ordered)  # fail closed up front on unsorted/duplicated bar input
    first_day = ordered[0].ts.date()
    last_day = ordered[-1].ts.date()

    decisions: list[dict[str, Any]] = []
    fills: list[dict[str, Any]] = []
    cashflows: list[dict[str, Any]] = []
    no_trade_by_reason: dict[str, int] = {}
    trade_days = 0

    day = first_day
    while day <= last_day:
        if day.weekday() < 5:  # Mon..Fri only: no London/NY session signal on weekends
            date_iso = day.isoformat()
            try:
                plan = arm_day_plan(ordered, arm_id, day, extra_delay_events=extra_delay)
            except SignalUnavailable as exc:
                no_trade_by_reason[NO_TRADE_MISSING_BAR] = no_trade_by_reason.get(NO_TRADE_MISSING_BAR, 0) + 1
                decisions.append(
                    {
                        "date": date_iso,
                        "arm_id": arm_id,
                        "decision": "NO_TRADE",
                        "position": 0,
                        "reason": NO_TRADE_MISSING_BAR,
                        "detail": str(exc),
                    }
                )
                day += timedelta(days=1)
                continue

            position = plan["position"]
            schedule = plan["schedule"]
            if position == 0:
                no_trade_by_reason[NO_TRADE_ZERO_MOMENTUM] = no_trade_by_reason.get(NO_TRADE_ZERO_MOMENTUM, 0) + 1
                decisions.append(
                    {
                        "date": date_iso,
                        "arm_id": arm_id,
                        "decision": "NO_TRADE",
                        "position": 0,
                        "reason": NO_TRADE_ZERO_MOMENTUM,
                        "momentum": plan["momentum"],
                        "signal_ts": schedule["signal_ts"],
                    }
                )
                day += timedelta(days=1)
                continue

            trade_days += 1
            trade_id = f"{arm_id}|{pair if pair else '-'}|{date_iso}"
            entry_side = "BUY" if position > 0 else "SELL"
            exit_side = "SELL" if position > 0 else "BUY"
            entry_price = schedule["entry_price"]
            flatten_price = schedule["flatten_price"]
            decisions.append(
                {
                    "date": date_iso,
                    "arm_id": arm_id,
                    "decision": "ENTER",
                    "position": position,
                    "reason": None,
                    "signal_ts": schedule["signal_ts"],
                    "entry_fill_instant": schedule["entry_fill_instant"],
                    "flatten_end_utc": schedule["flatten_end_utc"],
                }
            )
            fills.append(
                {
                    "trade_id": trade_id,
                    "role": "ENTRY",
                    "instant": schedule["entry_fill_instant"],
                    "price": entry_price,
                    "side": entry_side,
                    "cost_bps": bps_per_side,
                }
            )
            fills.append(
                {
                    "trade_id": trade_id,
                    "role": "FLATTEN",
                    "instant": schedule["flatten_end_utc"],
                    "price": flatten_price,
                    "side": exit_side,
                    "cost_bps": bps_per_side,
                }
            )
            gross = position * (flatten_price / entry_price - 1.0)
            cost_frac = round_trip_bps / 10_000.0
            net = gross - cost_frac
            if not (math.isfinite(gross) and math.isfinite(net)):
                raise Family1Error(f"non-finite cashflow on {date_iso} (fail closed)")
            cashflows.append(
                {
                    "trade_id": trade_id,
                    "position": position,
                    "entry_instant": schedule["entry_fill_instant"],
                    "exit_instant": schedule["flatten_end_utc"],
                    "gross_return_frac": gross,
                    "cost_frac": cost_frac,
                    "net_return_frac": net,
                }
            )
        day += timedelta(days=1)

    span_seconds = (ordered[-1].end - ordered[0].ts).total_seconds()
    years = span_seconds / YEAR_SECONDS if span_seconds > 0 else 0.0
    trades_per_year = (trade_days / years) if years > 0 else 0.0
    fill_count = 2 * trade_days
    total_bps = trade_days * round_trip_bps
    result: dict[str, Any] = {
        "schema": RUN_SCHEMA,
        "family_id": FAMILY_ID,
        "label": LABEL,
        "arm_id": arm_id,
        "pair": pair,
        "cost_tier": tier,
        "extra_delay_events": extra_delay,
        "bps_per_side": bps_per_side,
        "session_zone": zone_name,
        "schedule_only": True,  # feasibility arithmetic only; no return series scored
        "scoring_authorized": False,
        "bar_span": {"first_bar_start": ordered[0].ts, "last_bar_end": ordered[-1].end},
        "decisions": decisions,
        "fills": fills,
        "cashflows": cashflows,
        "costs_bps": {
            "per_side_bps": bps_per_side,
            "round_trip_bps": round_trip_bps,
            "total_bps": total_bps,
            "fills": fill_count,
        },
        "turnover": {
            "fills": fill_count,
            "units": 2 * trade_days,  # one entry + one flatten, one unit each
            "units_per_year": (2 * trade_days / years) if years > 0 else 0.0,
        },
        "decisions_per_year": trades_per_year,
        "feasibility": {
            "years": years,
            "trade_days": trade_days,
            "no_trade_days": sum(no_trade_by_reason.values()),
            "no_trade_by_reason": no_trade_by_reason,
            "cost_drag_bps_per_year": trades_per_year * round_trip_bps,
        },
    }
    run_json = canonical_json(result)
    result["canonical_json"] = run_json
    result["run_digest"] = sha256_hex(run_json)
    return result


# --------------------------------------------------------------------------- #
# Metrics placeholder and temporary-ledger publication
# --------------------------------------------------------------------------- #


def compute_metrics(book: Any) -> dict[str, Any]:
    """Finite placeholder metrics for dry runs (NO scored performance claim).

    ``book`` is a sequence of cashflow mappings (each with a finite
    "net_return_frac") or plain finite floats.  win_rate is placeholder
    arithmetic on synthetic books only; nothing here authorizes scoring.
    """
    if isinstance(book, (str, bytes)) or not isinstance(book, Sequence):
        raise Family1Error("book must be a sequence of cashflow records or floats")
    returns: list[float] = []
    for i, record in enumerate(book):
        value = record.get("net_return_frac") if isinstance(record, Mapping) else record
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise Family1Error(f"book[{i}]: net return must be a real number, got {type(value).__name__}")
        value = float(value)
        if not math.isfinite(value):
            raise Family1Error(f"book[{i}]: net return must be finite, got {value!r}")
        returns.append(value)
    n = len(returns)
    wins = sum(1 for r in returns if r > 0.0)
    return {
        "schema": "forex_free_v1_family1_metrics_v1",
        "family_id": FAMILY_ID,
        "placeholder": True,
        "n_trades": n,
        "win_rate": (wins / n) if n > 0 else 0.0,
        "mean_net_return_frac": (sum(returns) / n) if n > 0 else 0.0,
    }


def publish(ledger_path: Any, run_digest: Any, *, family_id: str = FAMILY_ID) -> dict[str, Any]:
    """Append-only temporary-ledger publication; idempotent on the digest.

    The ledger is a JSONL scratch file (temporary, RESEARCH_CANDIDATE).
    If ``run_digest`` is already present, replaying is a strict NO-OP:
    the file is not touched and nothing is appended.  Malformed existing
    rows fail closed.  No wall-clock timestamps are recorded, so the
    ledger content is a pure function of the set of published digests.
    """
    if not isinstance(run_digest, str):
        raise Family1Error(f"run_digest must be a hex string, got {type(run_digest).__name__}")
    digest = run_digest.strip().lower()
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise Family1Error(f"run_digest must be a 64-char sha256 hex digest, got {run_digest!r}")
    path = Path(ledger_path)

    existing_rows = 0
    seen: set[str] = set()
    if path.exists():
        text = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                raise Family1Error(f"ledger {path}: malformed blank row at line {line_no} (fail closed)")
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise Family1Error(f"ledger {path}: malformed JSON at line {line_no}: {exc}") from exc
            if not isinstance(row, Mapping) or not isinstance(row.get("run_digest"), str):
                raise Family1Error(f"ledger {path}: row at line {line_no} lacks a run_digest (fail closed)")
            seen.add(row["run_digest"].lower())
            existing_rows += 1

    if digest in seen:
        return {"status": "NOOP", "path": str(path), "total_rows": existing_rows, "appended": False}

    row_json = json.dumps(
        _canonical({"schema": LEDGER_SCHEMA, "family_id": family_id, "temporary": True, "run_digest": digest}),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(row_json + "\n")
    return {"status": "APPENDED", "path": str(path), "total_rows": existing_rows + 1, "appended": True}
