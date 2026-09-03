"""FXFV1-A3-P2 -- Late-NY fade of the volatility-standardized intraday extension.

FROZEN family-2 implementation for cycle FOREX-FREE-V1 (F6, family 2).

AUTHORITATIVE SPEC (implemented exactly, no redesign, no tuning):
    research/proposals/forex_free_v1/a3_lane/proposal_2.json
Selection: research/control/forex_free_v1_run/selection_freeze.json
    (family "FXFV1-A3-P2", arms: anchor / Tokyo-open neighbour /
    sign-flipped continuation causal control; 3 frozen cost cells).

Mechanism (frozen): measure the same-day move from the NY-open reference
after exactly four completed NY-session H1 bars; when that move is large
relative to the pair's trailing 20-trading-day daily volatility
(|z| = |r / sigma20| >= 1.0, gate exactly 1.0), take the OPPOSITE side
(fade of -sign(r)) for the late-NY window and flatten strictly before the
17:00 America/New_York rollover.  Arms:

* ``anchor``    -- NY 08:00 America/New_York anchor, fade (-sign(r)).
* ``neighbour`` -- Tokyo 09:00 Asia/Tokyo anchor, identical construction,
                   same gate, same NY-rollover sigma series and NY flatten.
* ``control``   -- sign-flipped anchor (continuation): buy the standardized
                   extension instead of fading it (causal control).

Frozen constants (from the spec, never re-tuned):
    gate |z| >= 1.0; signal window exactly 4 session bars; sigma lookback
    exactly 20 prior FX trading days (sample stdev, n-1, of rollover-to-
    rollover daily log closes, PRIOR days only -- PIT); costs 1.5 bps/side
    x tier {1.0, 1.5, 2.0}; tier 2.0 adds exactly one entry-delay event.

Execution (frozen, conservative close-to-close): signal computed on
completed bar t only (bar timestamp = OPEN; bar completes at open+1h);
earliest entry fill = close of bar t+1 (the 5th session bar; 13:00 New York
wall clock for the anchor); S3 tier fills at bar t+2 close; exit = close of
the last completed H1 bar with end STRICTLY BEFORE the applicable 17:00
America/New_York rollover (uniformly the bar ending 16:00 New York wall
clock, EST end 21:00Z / EDT end 20:00Z); no position spans a rollover or
the weekend; one position per pair per day.

Calendar: all instants from named IANA zones via ``zoneinfo`` (DST-correct);
NY open 08:00 America/New_York and Tokyo open 09:00 Asia/Tokyo are asserted
whole-hour bar-boundary aligned (fail-closed); nonexistent wall times fail
closed; ambiguous wall times resolved by explicit fold=0 (earliest) policy;
FX week window: open Sunday 21:00 America/New_York, close Friday 16:00
America/New_York (identical to research/assets/forex/sessions.py
DEFAULT_FX_WEEK_CONVENTION); Sunday open maps to Monday's FX trading day;
out-of-week bars are excluded by calendar rule only.

PURITY: pure Python stdlib only, deterministic, no network, no random, no
clock reads.  This module NEVER scores real data; ``compute_metrics`` emits
dummy finite feasibility metrics only.

Label: RESEARCH_CANDIDATE_NOT_LIVE_READY.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import date, datetime, time as dtime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

__all__ = [
    "FAMILY_ID",
    "PROPOSAL_ID",
    "LABEL",
    "GATE_Z",
    "SESSION_WINDOW_BARS",
    "SIGMA_LOOKBACK_DAYS",
    "BPS_PER_SIDE_BASE",
    "COST_TIERS",
    "ARM_IDS",
    "FailClosed",
    "BarSeries",
    "load_bars",
    "signal",
    "build_schedule",
    "run_arm",
    "arm_identity",
    "compute_metrics",
    "publish",
    "canonical_json",
    "run_digest",
]

# --------------------------------------------------------------------------
# Frozen constants (proposal_2.json; must not be modified)
# --------------------------------------------------------------------------

FAMILY_ID = "FXFV1-A3-P2"
PROPOSAL_ID = "FXFV1-A3-P2"
CYCLE_ID = "FOREX-FREE-V1"
LABEL = "RESEARCH_CANDIDATE_NOT_LIVE_READY"

GATE_Z = 1.0                     # frozen gate, exactly 1.0
SESSION_WINDOW_BARS = 4          # exactly 4 session bars (p0 -> p4)
SIGMA_LOOKBACK_DAYS = 20         # exactly 20 prior trading days
BPS_PER_SIDE_BASE = 1.5          # 1.5 bps per side, applied to every fill
COST_TIERS = (1.0, 1.5, 2.0)     # frozen cost stress multipliers
DELAY_EVENTS_BY_TIER = {1.0: 0, 1.5: 0, 2.0: 1}

ARM_IDS = ("anchor", "neighbour", "control")
ARM_REGISTRY = {
    # direction_multiplier: +1 -> take fade position -sign(r) (anchor,
    # neighbour); -1 -> sign-flipped continuation control (+sign(r)).
    "anchor": {
        "anchor_zone": "America/New_York",
        "anchor_hour": 8,
        "direction_multiplier": 1,
    },
    "neighbour": {
        "anchor_zone": "Asia/Tokyo",
        "anchor_hour": 9,
        "direction_multiplier": 1,
    },
    "control": {
        "anchor_zone": "America/New_York",
        "anchor_hour": 8,
        "direction_multiplier": -1,
    },
}

UTC = timezone.utc
NY_TZ = ZoneInfo("America/New_York")
TOKYO_TZ = ZoneInfo("Asia/Tokyo")
HOUR = timedelta(hours=1)


class FailClosed(Exception):
    """Raised on any malformed input, missing bar, or invariant violation.

    The family is fail-closed by design: every abnormal case becomes an
    explicit error (load/validation) or a counted NO_TRADE decision.
    """


# --------------------------------------------------------------------------
# Canonical JSON / digests
# --------------------------------------------------------------------------


def canonical_json(obj) -> str:
    """Deterministic canonical JSON: sorted keys, tight separators, ASCII."""
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    )


def run_digest(payload) -> str:
    """Canonical sha256 hex digest of a JSON-serializable payload."""
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _iso(dt: datetime) -> str:
    """Canonical UTC ISO stamp, e.g. '2020-02-26T18:00:00Z'."""
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------
# Zone helpers (named zones only; no fixed UTC offsets anywhere)
# --------------------------------------------------------------------------


def _zone_instant_utc(day: date, hour: int, tz: ZoneInfo) -> datetime:
    """UTC instant of ``hour:00`` local wall time on ``day`` in named ``tz``.

    Fail-closed on nonexistent wall times (DST spring-forward); ambiguous
    wall times are resolved by the frozen fold=0 (earliest) policy.  Asserts
    whole-hour bar-boundary alignment of the resulting UTC instant.
    """
    naive = datetime(day.year, day.month, day.day, hour)
    aware = naive.replace(tzinfo=tz, fold=0)
    utc = aware.astimezone(UTC)
    if utc.astimezone(tz).replace(tzinfo=None) != naive:
        raise FailClosed(
            f"nonexistent wall time {naive} in {tz} (fail-closed)"
        )
    # Ambiguity policy (frozen): fold=0, i.e. the earliest instant.  The
    # session hours used here (08/09/12/13/16/17 local) never land in the
    # 01:00-02:00 local transition window, but the policy is explicit.
    if aware.utcoffset() != aware.replace(fold=1).utcoffset():
        pass  # ambiguous wall time -> fold=0 chosen above, by policy
    if not (utc.minute == 0 and utc.second == 0 and utc.microsecond == 0):
        raise FailClosed(
            f"anchor instant {_iso(utc)} is not whole-hour aligned (fail-closed)"
        )
    return utc


def _rollover_utc(day: date) -> datetime:
    """17:00 America/New_York rollover instant on NY calendar ``day``."""
    return _zone_instant_utc(day, 17, NY_TZ)


def _prev_weekday(day: date) -> date:
    step = 3 if day.weekday() == 0 else (2 if day.weekday() == 6 else 1)
    return day - timedelta(days=step)


def _next_weekday(day: date) -> date:
    step = 3 if day.weekday() == 4 else (2 if day.weekday() == 5 else 1)
    return day + timedelta(days=step)


def _rollover_after(instant: datetime) -> datetime:
    """First 17:00 America/New_York rollover strictly after ``instant``.

    Uniform flatten clock for both arms: for the NY anchor this is the same
    weekday's rollover (entry 13:00/14:00 NY < 17:00 NY); for the Tokyo
    neighbour it is the rollover that closes the NY trading day containing
    the position (e.g. Tokyo Friday 14:00 fill -> Friday 16:00 NY week
    close), preserving the no-overnight / no-weekend invariants.
    """
    day = instant.astimezone(NY_TZ).date()
    for _ in range(10):
        roll = _rollover_utc(day)
        if roll > instant and day.weekday() <= 4:
            return roll
        day = _next_weekday(day)
    raise FailClosed("no applicable NY rollover found (fail-closed)")


def _in_fx_week(dt_utc: datetime) -> bool:
    """Frozen week window: Sun 21:00 America/New_York .. Fri 16:00 inclusive.

    Identical convention to research/assets/forex/sessions.py
    DEFAULT_FX_WEEK_CONVENTION.  A bar belongs to the week when its OPEN
    instant is inside the window (the Friday 16:00-close bar opens 15:00).
    """
    ny = dt_utc.astimezone(NY_TZ)
    wd = ny.weekday()
    if wd == 5:                      # Saturday
        return False
    if wd == 6:                      # Sunday: open 21:00
        return ny.time() >= dtime(21, 0)
    if wd == 4:                      # Friday: closed from 16:00
        return ny.time() < dtime(16, 0)
    return True


# --------------------------------------------------------------------------
# Bar loading / validation (fail-closed)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Bar:
    open_dt: datetime   # aware UTC, bar OPEN time (H1 bar completes +1h)
    open: float
    high: float
    low: float
    close: float

    @property
    def end_dt(self) -> datetime:
        return self.open_dt + HOUR


class BarSeries:
    """Immutable, validated, time-sorted H1 bar series (one pair)."""

    def __init__(self, bars: list[Bar]):
        self.bars: list[Bar] = bars
        self._by_open: dict[datetime, int] = {}
        self._by_end: dict[datetime, int] = {}
        for i, b in enumerate(bars):
            self._by_open[b.open_dt] = i
            self._by_end[b.end_dt] = i

    def __len__(self) -> int:
        return len(self.bars)

    def index_of_open(self, open_dt: datetime):
        return self._by_open.get(open_dt)

    def index_of_end(self, end_dt: datetime):
        return self._by_end.get(end_dt)

    def close_at_open(self, open_dt: datetime):
        i = self._by_open.get(open_dt)
        return None if i is None else self.bars[i].close

    def close_at_end(self, end_dt: datetime):
        i = self._by_end.get(end_dt)
        return None if i is None else self.bars[i].close

    @property
    def first_open(self) -> datetime:
        return self.bars[0].open_dt

    @property
    def last_end(self) -> datetime:
        return self.bars[-1].end_dt


def _parse_utc(ts) -> datetime:
    if not isinstance(ts, str):
        raise FailClosed(f"timestamp not a string: {ts!r}")
    s = ts.strip()
    try:
        dt = datetime.fromisoformat(s[:-1] + "+00:00" if s.endswith(("Z", "z")) else s)
    except ValueError as exc:
        raise FailClosed(f"malformed timestamp {ts!r}: {exc}") from exc
    if dt.tzinfo is None:
        raise FailClosed(f"naive (tz-less) timestamp {ts!r} (fail-closed)")
    if dt.utcoffset() != timedelta(0):
        raise FailClosed(f"non-UTC timestamp {ts!r} (fail-closed)")
    return dt.astimezone(UTC)


def _as_finite_float(value, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FailClosed(f"field {field} not a number: {value!r}")
    v = float(value)
    if not math.isfinite(v):
        raise FailClosed(f"field {field} not finite: {value!r}")
    return v


def load_bars(rows) -> BarSeries:
    """Validate normalized H1 bars and return an immutable BarSeries.

    Each row: ``{"datetime": <UTC ISO string, bar OPEN time>, "open": float,
    "high": float, "low": float, "close": float}``.  Fail-closed on:
    missing fields, malformed / naive / non-UTC / off-the-hour timestamps,
    non-numeric or non-finite prices, OHLC inconsistencies, duplicate
    timestamps, and empty input.  Output is sorted by open time.
    """
    if isinstance(rows, BarSeries):
        return rows
    if not isinstance(rows, (list, tuple)):
        raise FailClosed("bars payload must be a list of row dicts")
    if len(rows) == 0:
        raise FailClosed("empty bar series (fail-closed)")

    bars: list[Bar] = []
    seen: set[datetime] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise FailClosed(f"bar row not a dict: {row!r}")
        for key in ("datetime", "open", "high", "low", "close"):
            if key not in row:
                raise FailClosed(f"bar row missing field {key!r}: {row!r}")
        open_dt = _parse_utc(row["datetime"])
        if not (open_dt.minute == 0 and open_dt.second == 0
                and open_dt.microsecond == 0):
            raise FailClosed(
                f"bar timestamp {row['datetime']!r} off the H1 hour grid"
            )
        if open_dt in seen:
            raise FailClosed(f"duplicate bar timestamp {row['datetime']!r}")
        seen.add(open_dt)
        o = _as_finite_float(row["open"], "open")
        h = _as_finite_float(row["high"], "high")
        l = _as_finite_float(row["low"], "low")
        c = _as_finite_float(row["close"], "close")
        if h < l or h < o or h < c or l > o or l > c:
            raise FailClosed(f"OHLC inconsistency at {row['datetime']!r}")
        bars.append(Bar(open_dt, o, h, l, c))

    bars.sort(key=lambda b: b.open_dt)
    return BarSeries(bars)


# --------------------------------------------------------------------------
# Arm configuration (frozen; conflicting config fails closed)
# --------------------------------------------------------------------------

_CONFIG_KEYS = (
    "arm_id",
    "anchor_zone",
    "anchor_hour",
    "direction_multiplier",
    "gate_z",
    "session_window_bars",
    "sigma_lookback_days",
    "cost_basis_bps_per_side",
)


@dataclass(frozen=True)
class ArmSpec:
    arm_id: str
    tz: ZoneInfo
    tz_name: str
    anchor_hour: int
    direction_multiplier: int   # +1 fade (anchor/neighbour), -1 control


def _resolve_arm(arm_id, config=None) -> ArmSpec:
    if not isinstance(arm_id, str) or arm_id not in ARM_IDS:
        raise FailClosed(f"unknown arm_id {arm_id!r}; expected one of {ARM_IDS}")
    base = dict(ARM_REGISTRY[arm_id])
    if config is not None:
        if not isinstance(config, dict):
            raise FailClosed("arm config must be a dict")
        for key, value in config.items():
            if key == "arm_id":
                if value != arm_id:
                    raise FailClosed("arm_id mismatch in config")
                continue
            if key not in _CONFIG_KEYS:
                raise FailClosed(f"unknown config key {key!r} (fail-closed)")
            frozen = {
                "anchor_zone": base["anchor_zone"],
                "anchor_hour": base["anchor_hour"],
                "direction_multiplier": base["direction_multiplier"],
                "gate_z": GATE_Z,
                "session_window_bars": SESSION_WINDOW_BARS,
                "sigma_lookback_days": SIGMA_LOOKBACK_DAYS,
                "cost_basis_bps_per_side": BPS_PER_SIDE_BASE,
            }[key]
            if value != frozen:
                raise FailClosed(
                    f"config {key}={value!r} conflicts with frozen value "
                    f"{frozen!r} (no re-tuning permitted)"
                )
    tz = NY_TZ if base["anchor_zone"] == "America/New_York" else TOKYO_TZ
    return ArmSpec(
        arm_id=arm_id,
        tz=tz,
        tz_name=base["anchor_zone"],
        anchor_hour=int(base["anchor_hour"]),
        direction_multiplier=int(base["direction_multiplier"]),
    )


def _resolve_tier(cost_tier) -> float:
    try:
        v = float(cost_tier)
    except (TypeError, ValueError) as exc:
        raise FailClosed(f"bad cost tier {cost_tier!r}") from exc
    for t in COST_TIERS:
        if v == t:
            return t
    raise FailClosed(
        f"cost tier {cost_tier!r} outside frozen cells {COST_TIERS} (fail-closed)"
    )


def arm_identity(arm_id, config=None) -> str:
    """Canonical sha256 of the frozen arm identity.

    Binds arm_id, the frozen mechanism constants, execution/cost basis and
    label into one digest.  The three arms produce three distinct digests;
    repeated generation is bit-stable.
    """
    spec = _resolve_arm(arm_id, config)
    payload = {
        "family_id": FAMILY_ID,
        "proposal_id": PROPOSAL_ID,
        "cycle_id": CYCLE_ID,
        "arm_id": spec.arm_id,
        "anchor_zone": spec.tz_name,
        "anchor_hour_local": spec.anchor_hour,
        "direction_multiplier": spec.direction_multiplier,
        "gate_z": GATE_Z,
        "session_window_bars": SESSION_WINDOW_BARS,
        "sigma_lookback_days": SIGMA_LOOKBACK_DAYS,
        "sigma_basis": "rollover_to_rollover_daily_log_returns_prior_days_only",
        "execution": "next_allowed_bar_close_to_close",
        "flatten": "last_completed_h1_bar_end_strictly_before_1700_america_new_york",
        "week_window": "sunday_2100_to_friday_1600_america_new_york",
        "cost_basis_bps_per_side": BPS_PER_SIDE_BASE,
        "cost_tiers": list(COST_TIERS),
        "delay_events_by_tier": {str(k): v for k, v in DELAY_EVENTS_BY_TIER.items()},
        "label": LABEL,
    }
    return run_digest(payload)


# --------------------------------------------------------------------------
# Signal (frozen mechanism)
# --------------------------------------------------------------------------


def _sample_stdev(values: list[float]) -> float:
    n = len(values)
    if n < 2:
        raise FailClosed("sample stdev needs >= 2 observations")
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / (n - 1)
    return math.sqrt(var)


def _sigma20_closes(series: BarSeries, sig_ny_date: date):
    """Trailing 21 rollover-to-rollover daily closes STRICTLY BEFORE the
    signal's NY trading date (PIT: prior days only, no same-day leakage).

    Returns (closes_ascending, reason_or_None).
    """
    data_start_ny_date = series.first_open.astimezone(NY_TZ).date()
    days = []
    d = sig_ny_date
    for _ in range(SIGMA_LOOKBACK_DAYS + 1):
        d = _prev_weekday(d)
        days.append(d)
    days.reverse()  # ascending: 21 NY weekdays strictly before sig_ny_date
    closes = []
    for day in days:
        if day < data_start_ny_date:
            return [], "WARMUP"
        end = _rollover_utc(day) - HOUR   # bar ending 16:00 NY (EST/EDT exact)
        c = series.close_at_end(end)
        if c is None:
            return [], "MISSING_BAR"
        closes.append(c)
    return closes, None


def _signal_for_day(series: BarSeries, spec: ArmSpec, day: date) -> dict:
    """Frozen per-day signal evaluation for one arm (see module docstring)."""
    anchor_open = _zone_instant_utc(day, spec.anchor_hour, spec.tz)
    p0_open = anchor_open - HOUR

    def _close_at(dt_open: datetime):
        i = series.index_of_open(dt_open)
        if i is None or not _in_fx_week(series.bars[i].open_dt):
            return None
        return series.bars[i].close

    p0 = _close_at(p0_open)
    if p0 is None:
        return {"direction": 0, "reason": "MISSING_BAR", "signal_ts": None,
                "r": None, "sigma": None, "z": None, "p0_close": None,
                "p4_close": None}
    session_closes = []
    for k in range(SESSION_WINDOW_BARS):
        c = _close_at(anchor_open + k * HOUR)
        if c is None:
            return {"direction": 0, "reason": "MISSING_BAR", "signal_ts": None,
                    "r": None, "sigma": None, "z": None, "p0_close": None,
                    "p4_close": None}
        session_closes.append(c)
    p4 = session_closes[-1]
    signal_ts = anchor_open + SESSION_WINDOW_BARS * HOUR  # bar t completed

    closes, reason = _sigma20_closes(
        series, signal_ts.astimezone(NY_TZ).date()
    )
    if reason is not None:
        return {"direction": 0, "reason": reason, "signal_ts": _iso(signal_ts),
                "r": None, "sigma": None, "z": None, "p0_close": p0,
                "p4_close": p4}
    returns = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]
    sigma = _sample_stdev(returns)
    if not math.isfinite(sigma) or sigma <= 0.0:
        return {"direction": 0, "reason": "DEGENERATE_SIGMA",
                "signal_ts": _iso(signal_ts), "r": None, "sigma": sigma,
                "z": None, "p0_close": p0, "p4_close": p4}

    r = p4 / p0 - 1.0
    z = r / sigma
    direction = 0
    if r != 0.0 and abs(z) >= GATE_Z:
        fade = -1 if r > 0 else 1          # fade of -sign(r)
        direction = fade * spec.direction_multiplier
    return {
        "direction": direction,
        "reason": "TRIGGERED" if direction != 0 else "GATE_NOT_MET",
        "signal_ts": _iso(signal_ts),
        "r": r, "sigma": sigma, "z": z,
        "p0_close": p0, "p4_close": p4,
    }


def _latest_evaluable_day(series: BarSeries, spec: ArmSpec):
    """Most recent local weekday whose p0..p4 bars are all present."""
    last_local = series.last_end.astimezone(spec.tz).date()
    first_local = series.first_open.astimezone(spec.tz).date()
    d = last_local
    while d >= first_local:
        if d.weekday() <= 4:
            anchor_open = _zone_instant_utc(d, spec.anchor_hour, spec.tz)
            need = [anchor_open - HOUR] + [
                anchor_open + k * HOUR for k in range(SESSION_WINDOW_BARS)
            ]
            if all(series.index_of_open(t) is not None for t in need):
                return d
        d = d - timedelta(days=1)
    return None


def signal(bars, arm_config, day=None) -> int:
    """Frozen signal: +1 / -1 / 0 for one arm.

    ``bars``: validated rows or BarSeries for ONE pair.
    ``arm_config``: dict, must carry ``arm_id`` in
        {"anchor", "neighbour", "control"}; any frozen-constant keys present
        are validated against the frozen values (conflicts fail closed).
    ``day``: optional local anchor date; default = most recent evaluable day.

    Anchor: fade -sign(r) of the 4-bar NY-session extension when
    |z| = |r/sigma20| >= 1.0; neighbour: identical at the Tokyo open;
    control: sign-flipped (continuation).  0 means no trade (gate not met,
    warm-up, or missing bars -- see ``signal_detail`` for the reason).
    """
    direction, _reason, _info = signal_detail(bars, arm_config, day)
    return direction


def signal_detail(bars, arm_config, day=None):
    """Like ``signal`` but returns (direction, reason, info) with the full
    per-day evaluation record (r, sigma, z, signal_ts)."""
    if not isinstance(arm_config, dict) or "arm_id" not in arm_config:
        raise FailClosed("arm_config must be a dict containing 'arm_id'")
    spec = _resolve_arm(arm_config["arm_id"], arm_config)
    series = load_bars(bars)
    if day is None:
        day = _latest_evaluable_day(series, spec)
        if day is None:
            return 0, "MISSING_BAR", {"signal_ts": None}
    info = _signal_for_day(series, spec, day)
    return info["direction"], info["reason"], info


# --------------------------------------------------------------------------
# Schedule (entry / flatten, DST-exact, fail-closed)
# --------------------------------------------------------------------------


def build_schedule(series, signal_ts, delay_events=0) -> dict:
    """Frozen entry/flatten schedule for one signal event.

    ``signal_ts``  : completion instant (END) of the signal bar; the signal
                     bar must already be completed before any entry.
    ``delay_events``: 0 (S1/S2) or 1 (S3 one-event entry delay).

    Entry  = the NEXT allowed bar after the signal bar, i.e. the H1 bar
             opening at signal_ts + delay_events*1h (missing -> NO_TRADE);
             fill at that bar's CLOSE (conservative close-to-close).
    Exit   = the last completed H1 bar whose end is STRICTLY BEFORE the
             applicable 17:00 America/New_York rollover (uniformly the bar
             ending 16:00 New York wall clock: 21:00Z in EST, 20:00Z in
             EDT); missing -> NO_TRADE.  Feasibility invariants
             (entry fill < flatten end < rollover, exit after entry) are
             asserted fail-closed.
    """
    series = load_bars(series)
    if delay_events not in (0, 1):
        raise FailClosed("delay_events must be 0 or 1")
    signal_dt = _parse_utc(signal_ts if isinstance(signal_ts, str) else _iso(signal_ts))
    t_idx = series.index_of_end(signal_dt)
    if t_idx is None:
        return {"feasible": False, "reason": "MISSING_BAR",
                "detail": "signal bar"}
    entry_open = signal_dt + delay_events * HOUR
    entry_idx = series.index_of_open(entry_open)
    if entry_idx is None or not _in_fx_week(entry_open):
        return {"feasible": False, "reason": "MISSING_BAR",
                "detail": "entry bar"}
    if entry_idx <= t_idx:
        return {"feasible": False, "reason": "SCHEDULE_INFEASIBLE",
                "detail": "entry not after signal bar"}
    entry_bar = series.bars[entry_idx]
    entry_fill = entry_bar.end_dt
    entry_px = entry_bar.close
    rollover = _rollover_after(entry_fill)
    exit_end = rollover - HOUR
    exit_idx = series.index_of_end(exit_end)
    if exit_idx is None or not _in_fx_week(series.bars[exit_idx].open_dt):
        return {"feasible": False, "reason": "MISSING_BAR",
                "detail": "flatten bar"}
    if not (entry_fill < exit_end < rollover):
        return {"feasible": False, "reason": "SCHEDULE_INFEASIBLE",
                "detail": "flatten window violated"}
    if exit_idx <= entry_idx:
        return {"feasible": False, "reason": "SCHEDULE_INFEASIBLE",
                "detail": "exit not after entry"}
    exit_bar = series.bars[exit_idx]
    return {
        "feasible": True,
        "reason": "OK",
        "signal_bar_idx": t_idx,
        "entry_open_ts": _iso(entry_bar.open_dt),
        "entry_fill_ts": _iso(entry_fill),
        "entry_px": entry_px,
        "exit_ts": _iso(exit_bar.end_dt),
        "exit_px": exit_bar.close,
        "rollover_ts": _iso(rollover),
        "delay_events": delay_events,
    }


# --------------------------------------------------------------------------
# Arm runner (decisions / fills / cashflows / costs / feasibility)
# --------------------------------------------------------------------------


def run_arm(bars, arm_id, cost_tier, pair=None) -> dict:
    """Run one frozen arm over one pair's bars at one frozen cost cell.

    Returns decisions (every evaluated pair-day, incl. counted NO_TRADE
    reasons), fills (next-allowed-bar close fills), cashflows (gross /
    cost / net per trade, synthetic-data plumbing only), costs_bps,
    turnover, decisions_per_year and the canonical JSON (+sha256) of the
    whole report.  Deterministic; identical inputs reproduce the identical
    canonical JSON byte-for-byte.
    """
    spec = _resolve_arm(arm_id)
    tier = _resolve_tier(cost_tier)
    delay = DELAY_EVENTS_BY_TIER[tier]
    series = load_bars(bars)

    in_week = [b for b in series.bars if _in_fx_week(b.open_dt)]
    if not in_week:
        raise FailClosed("no in-week bars (fail-closed)")
    first_day = in_week[0].open_dt.astimezone(spec.tz).date()
    last_day = in_week[-1].open_dt.astimezone(spec.tz).date()

    decisions, fills, cashflows = [], [], []
    day = first_day
    while day <= last_day:
        if day.weekday() <= 4:
            info = _signal_for_day(series, spec, day)
            direction = info["direction"]
            decision = {
                "arm_id": spec.arm_id,
                "pair": pair,
                "day": day.isoformat(),
                "signal_ts": info["signal_ts"],
                "r": info["r"],
                "sigma": info["sigma"],
                "z": info["z"],
                "direction": direction,
                "reason": info["reason"],
            }
            if direction == 0:
                decisions.append(decision)
            else:
                sched = build_schedule(series, info["signal_ts"], delay)
                if not sched["feasible"]:
                    decision = dict(decision, direction=0,
                                    reason=sched["reason"],
                                    schedule_detail=sched.get("detail"))
                    decisions.append(decision)
                else:
                    if spec.tz is NY_TZ and sched["rollover_ts"][:10] != day.isoformat():
                        raise FailClosed(
                            "anchor arm rollover left the signal day (fail-closed)"
                        )
                    decision["reason"] = "TRIGGERED"
                    decisions.append(decision)
                    gross = direction * (sched["exit_px"] / sched["entry_px"] - 1.0)
                    rt_bps = 2.0 * BPS_PER_SIDE_BASE * tier
                    cost_ret = rt_bps / 1e4
                    net = gross - cost_ret
                    fills.append({
                        "arm_id": spec.arm_id,
                        "pair": pair,
                        "day": day.isoformat(),
                        "direction": direction,
                        "entry_open_ts": sched["entry_open_ts"],
                        "entry_fill_ts": sched["entry_fill_ts"],
                        "entry_px": sched["entry_px"],
                        "exit_ts": sched["exit_ts"],
                        "exit_px": sched["exit_px"],
                        "rollover_ts": sched["rollover_ts"],
                        "delay_events": delay,
                        "round_trip_bps": rt_bps,
                    })
                    cashflows.append({
                        "arm_id": spec.arm_id,
                        "pair": pair,
                        "day": day.isoformat(),
                        "gross_ret": gross,
                        "cost_ret": cost_ret,
                        "net_ret": net,
                    })
        day = day + timedelta(days=1)

    n_trades = len(fills)
    n_decisions = len(decisions)
    per_side_bps = BPS_PER_SIDE_BASE * tier
    rt_bps = 2.0 * per_side_bps
    total_paid_bps = rt_bps * n_trades
    turnover = 2.0 * n_trades  # notional units: entry + exit per trade
    # decision-day span in the arm's local calendar (every decision has a
    # day, including missing-bar NO_TRADE days, so the pace is total)
    years = ((last_day - first_day).days / 365.25) if n_decisions > 1 else 0.0
    decisions_per_year = (
        float(n_decisions) / years if years > 0 else float(n_decisions)
    )

    core = {
        "family_id": FAMILY_ID,
        "proposal_id": PROPOSAL_ID,
        "label": LABEL,
        "arm_id": spec.arm_id,
        "arm_digest": arm_identity(arm_id),
        "cost_tier": tier,
        "pair": pair,
        "n_decisions": n_decisions,
        "n_trades": n_trades,
        "decisions": decisions,
        "fills": fills,
        "cashflows": cashflows,
        "costs_bps": {
            "per_side_bps": per_side_bps,
            "round_trip_bps": rt_bps,
            "total_paid_bps": total_paid_bps,
        },
        "turnover": turnover,
        "decisions_per_year": decisions_per_year,
        "scope": "SCHEDULE_ONLY_DRYRUN_NO_SCORING",
    }
    cj = canonical_json(core)
    return dict(core, canonical_json=cj, sha256=run_digest(core))


# --------------------------------------------------------------------------
# Dummy finite metrics (dry runs only -- no scored PnL)
# --------------------------------------------------------------------------


def compute_metrics(book) -> dict:
    """Dummy finite feasibility metrics for dry runs.

    ``book`` is a run_arm report or a list of reports.  Counts and cost
    arithmetic only; means are plumbing over synthetic dry-run cashflows
    and carry no scored meaning.  Every value is finite by construction.
    """
    reports = [book] if isinstance(book, dict) and "decisions" in book else list(book)
    n_dec = 0
    n_tr = 0
    turnover = 0.0
    cost_bps = 0.0
    dpy_max = 0.0
    gross_vals = []
    net_vals = []
    for rep in reports:
        n_dec += int(rep["n_decisions"])
        n_tr += int(rep["n_trades"])
        turnover += float(rep["turnover"])
        cost_bps += float(rep["costs_bps"]["total_paid_bps"])
        dpy_max = max(dpy_max, float(rep["decisions_per_year"]))
        gross_vals.extend(cf["gross_ret"] for cf in rep["cashflows"])
        net_vals.extend(cf["net_ret"] for cf in rep["cashflows"])

    def _mean(vals):
        return sum(vals) / len(vals) if vals else 0.0

    metrics = {
        "n_decisions": float(n_dec),
        "n_trades": float(n_tr),
        "decisions_per_year_arm_max": dpy_max,
        "turnover": turnover,
        "total_cost_bps": cost_bps,
        "mean_gross_ret": _mean(gross_vals),
        "mean_net_ret": _mean(net_vals),
    }
    metrics["all_finite"] = all(
        math.isfinite(v) for v in metrics.values() if isinstance(v, float)
    )
    metrics.update({
        "scored": False,
        "status": "DRY_RUN_FEASIBILITY_ONLY",
        "label": LABEL,
    })
    return metrics


# --------------------------------------------------------------------------
# Append-only temporary ledger (dry runs); identical-digest replay = no-op
# --------------------------------------------------------------------------

LEDGER_SCHEMA = "forex_free_v1_family2_dryrun_ledger_v1"


def publish(ledger_path, run_digest_value, rows=()) -> dict:
    """Append a dry-run payload to a temporary append-only JSONL ledger.

    Behaviour: if the ledger already contains a run header with the SAME
    run_digest, this is a replay and a strict NO-OP (zero rows added).
    Otherwise a run header line followed by the row lines is appended.
    Malformed existing lines fail closed (append-only integrity).
    """
    path = Path(ledger_path)
    header = {
        "record": "run_header",
        "schema": LEDGER_SCHEMA,
        "family_id": FAMILY_ID,
        "proposal_id": PROPOSAL_ID,
        "label": LABEL,
        "run_digest": run_digest_value,
        "rows": len(tuple(rows)),
    }
    if path.exists():
        with path.open("r", encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise FailClosed(
                        f"corrupt ledger line {lineno} (fail-closed): {exc}"
                    ) from exc
                if (obj.get("record") == "run_header"
                        and obj.get("run_digest") == run_digest_value):
                    return {
                        "status": "REPLAY_NOOP",
                        "rows_added": 0,
                        "run_digest": run_digest_value,
                    }
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(canonical_json(header) + "\n")
        for row in rows:
            payload = dict(row)
            payload["record"] = "row"
            payload["run_digest"] = run_digest_value
            fh.write(canonical_json(payload) + "\n")
    return {
        "status": "APPENDED",
        "rows_added": 1 + len(tuple(rows)),
        "run_digest": run_digest_value,
    }
