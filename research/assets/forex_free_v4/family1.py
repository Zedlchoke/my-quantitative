"""FOREX-FREE-V4 family1: FXFV4-A6-P1 commodity-bloc risk-off event basket.

Mechanical implementation of the SELECTED, FROZEN packet
``research/proposals/forex_free_v4/d1-a6-proposals/PROPOSAL_FXFV4-A6-P1.json``
(sha256 e827c904...) against the inherited V3 family API contract (module
docstring of :mod:`research.assets.forex_free_v3.scored_runner`)::

    run_arm(arm, data_paths, macro_reader, freeze_token=None)
        -> {"decisions": [...], "financing_events": [...], "meta": {...}}

The mechanism (packet `mechanism`, transcribed as frozen law):

* DECISION CLOCK -- one decision per NY trading day at the completion instant
  of the daily 16:00 America/New_York flat bar (DST-aware named zone via
  zoneinfo: 20:00Z stamps in EDT weeks, 21:00Z in EST weeks; never fixed
  offsets).  ``decision_ts`` carries the 16:00-NY bar instant of the decision
  day -- the packet's "bar stamps 20:00Z in EDT weeks / 21:00Z in EST weeks"
  and the frozen runner validator (_is_ny_1600) both require the 16:00-NY
  wall-time stamp; the trigger inputs are the completed closes observable at
  that bar's completion, strictly before the next-session fill instant.
* TRIGGER -- S_t = signed mean of the daily log returns of the 16:00-NY
  completed closes: +r(AUD/USD,t), +r(NZD/USD,t), -r(USD/CAD,t) (frozen sign
  convention; the negated USD/CAD return expresses CAD strength in the same
  direction as AUD/NZD strength).  z_t = (S_t - mean(S over the 60 most
  recent completed NY-days strictly before t)) / std(same 60 days); a
  risk-off event fires on day t iff z_t <= -1.0 (<= semantics frozen; the
  standardization window NEVER includes day t itself).
* BASKET -- on an event, at the OPEN of the next session's 16:00-NY bar, if
  that leg is flat: SHORT AUD/USD, SHORT NZD/USD, LONG USD/CAD, SHORT
  USD/JPY, SHORT USD/CHF (frozen 5-leg map).  Exactly 5 completed NY-days
  hold; exit at the open of the 16:00-NY bar after the 5th completed NY-day
  (exit bar = the 5th existing daily bar after the entry bar in the leg's
  own 16:00-NY bar sequence).  No targets, no stops, no signal refresh while
  a leg is open; the governor (max 1 position per pair, max 1 entry per pair
  per NY-day) turns blocked events into NO_TRADE, never deferrals.
* FILL CONVENTION -- next-session fill: the first existing 16:00-NY bar of
  the leg strictly after the decision instant (at least one full session;
  at most 4 calendar days over holiday weekends -- a larger gap fails closed
  to NO_TRADE, the frozen ONE_EVENT_LAG discipline; never same-bar fills,
  never fill-forward).
* FORCE-FLAT -- on every frozen fold boundary (2022-05-01, 2024-07-01 and
  the span end 2026-09-02) any open leg exits at the OPEN of the last
  existing 16:00-NY bar before the boundary (force_flat=true); an entry
  whose fill would land exactly on that flatten bar is suppressed
  (NO_TRADE); entries filling after the boundary are allowed and scored in
  the next fold by the runner's fold_of semantics.  No position ever crosses
  a boundary.
* VALIDITY (fail-closed) -- a NY-day is valid for a pair iff that day's
  completed 16:00-NY bar exists AND the pair's H1 bars of that NY-day are
  gap-free (consecutive 1-hour steps; holes, holidays and early closes
  invalidate the day).  Decision days and the 60-day standardization window
  run over days valid for ALL trigger pairs of the arm; daily returns are
  log closes over consecutive valid days.  Missing data NEVER backfills.

Arms (frozen, one parameter set each, no grids):

* ``anchor``   -- exactly the frozen law above (mean bloc estimator).
* ``neighbour`` -- one presumption away: MEDIAN of the same three signed
  returns replaces the MEAN; byte-identical otherwise.
* ``control`` (``causal_negative_control``) -- the sham majors bloc:
  z^sham_t standardizes mean(+r(EUR/USD,t), +r(GBP/USD,t)) over its own
  trailing 60 valid NY-days; event iff z^sham_t <= -1.0; the basket, clocks,
  holding law, governor and costs are byte-identical to the anchor.  Its
  preregistered non-reproduction rule is applied at scoring
  (runner mechanism_sanity / packet control gate), not here.
* ``benchmark_treatment`` -- the packet's incremental_test benchmark
  (arm_id FXFV4-A6-P1-bench): the anchor law with the trigger read STALE --
  the event flag of decision day t is the z evaluated on NY-day t-10 (10
  valid NY-days, strictly exceeding the 5-day drift window); identical legs,
  clocks, holding, fills, costs.  Booked by the runner inside the scored
  anchor cell for the per-trade expectancy-difference incremental alpha
  (meta.alpha_definition = "per_trade_expectancy_difference_v1", the packet's
  frozen gate); never a scored cell of its own.

Policy rates enter ONLY through the injected ``macro_reader`` for the
financing accrual (accounting, not signal -- the packet's lane_diversity_note);
the SIGNAL is price-only on the authorized H1 snapshot.

data_paths (opaque to the runner; consumed here):
    ``price_h1_dir``   directory of the canonical TwelveData H1 window files
                       (td_loader schema; error-status no-coverage windows
                       skipped; overlaps deduped; OHLC-inconsistent bars
                       quarantined with the inherited 0.1 percent ceiling).
    ``macro_vintages`` area -> vintage JSON path (used only when
                       ``macro_reader`` is None, exactly as V3 family1).

Determinism: same inputs -> byte-identical output; no wall-clock reads; float
arithmetic in fixed order.  ``freeze_token`` is accepted and ignored.

NO scored PnL is computed here: this module produces schedules and carries
financing events; booking, gating and publication belong to the runner.  The
margin-to-fail reporting fields required by the V4 selection freeze are
attached runner-side via :func:`margin_to_fail` (see
FAMILY1_IMPLEMENTATION_NOTES.md).
"""
from __future__ import annotations

import bisect
import json
import math
import os
import statistics
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

__all__ = [
    "PROPOSAL_ID", "PAIRS", "TRIGGER_PAIRS", "TRIGGER_SIGNS", "SHAM_TRIGGER_PAIRS",
    "SHAM_TRIGGER_SIGNS", "RESPONSE_LEGS", "STANDARDIZATION_WINDOW_NY_DAYS",
    "EVENT_THRESHOLD", "HOLDING_NY_DAYS", "BENCHMARK_STALENESS_NY_DAYS",
    "NOTIONAL_USD", "MAX_FILL_LAG_DAYS", "FOLD_BOUNDARIES", "FORCE_FLAT_BOUNDARIES",
    "Z_STD_DDOF", "ARM_IDS", "BENCHMARK_ARM", "ALPHA_DEFINITION",
    "run_arm", "load_pair_h1_bars", "daily_decision_bars", "ny_day_valid_map",
    "valid_daily_bars", "trigger_day_series", "bloc_signed_returns", "z_standardize",
    "event_flags_from_z", "benchmark_event_flags", "schedule_legs",
    "financing_adjustment_usd", "margin_to_fail", "drop_one_leg_schedule",
]

PROPOSAL_ID = "FXFV4-A6-P1"

# Frozen 7-pair authorized universe (packet universe.authorized_universe).
PAIRS = ("EUR/USD", "GBP/USD", "AUD/USD", "NZD/USD",
         "USD/JPY", "USD/CHF", "USD/CAD")

# Anchor/neighbour trigger bloc: the documented commodity-currency trio with
# the frozen sign convention (+AUD/USD, +NZD/USD, -USD/CAD).
TRIGGER_PAIRS = ("AUD/USD", "NZD/USD", "USD/CAD")
TRIGGER_SIGNS = {"AUD/USD": 1.0, "NZD/USD": 1.0, "USD/CAD": -1.0}
# Control sham bloc (fixed, derangement-free; packet arms.control).
SHAM_TRIGGER_PAIRS = ("EUR/USD", "GBP/USD")
SHAM_TRIGGER_SIGNS = {"EUR/USD": 1.0, "GBP/USD": 1.0}
# Frozen 5-leg basket and directions (side: +1 LONG base, -1 SHORT base).
RESPONSE_LEGS = (("AUD/USD", -1), ("NZD/USD", -1), ("USD/CAD", +1),
                 ("USD/JPY", -1), ("USD/CHF", -1))

STANDARDIZATION_WINDOW_NY_DAYS = 60   # trailing valid NY-days strictly before t
EVENT_THRESHOLD = -1.0                # event iff z <= -1.0 (<= frozen)
HOLDING_NY_DAYS = 5                   # exactly 5 completed NY-days per leg
BENCHMARK_STALENESS_NY_DAYS = 10      # benchmark trigger read on NY-day t-10
NOTIONAL_USD = 10000                  # frozen USD-unit design
MAX_FILL_LAG_DAYS = 4                 # mirror of the runner one-event-lag allowance
# Sample standard deviation (ddof=1, statistics.stdev) for the z denominator;
# see AMBIGUITIES.md (population-vs-sample std is not stated in the packet;
# the choice is this single frozen constant, recorded for A1).
Z_STD_DDOF = 1

# Frozen kernel fold grid (selection_freeze implementation directive; V3
# scored_runner.FOLD_BOUNDARIES verbatim).  Boundaries that force flat: both
# internal boundaries plus the span end (no position crosses a boundary or
# survives past the last bar).
FOLD_BOUNDARIES = ("2020-03-01T00:00:00+00:00", "2022-05-01T00:00:00+00:00",
                   "2024-07-01T00:00:00+00:00", "2026-09-02T23:59:59+00:00")
FORCE_FLAT_BOUNDARIES = FOLD_BOUNDARIES[1:]

ARMS = ("anchor", "neighbour", "causal_negative_control")
BENCHMARK_ARM = "benchmark_treatment"   # runner-required, never a scored cell
ARM_ALIASES = {"control": "causal_negative_control"}
ARM_IDS = {
    "anchor": "FXFV4-A6-P1-anchor",
    "neighbour": "FXFV4-A6-P1-neigh",
    "causal_negative_control": "FXFV4-A6-P1-ctrl",
    "benchmark_treatment": "FXFV4-A6-P1-bench",   # packet incremental_test
}
# Packet incremental_test.gate: anchor financing-adjusted expectancy minus
# benchmark financing-adjusted expectancy (the V3 runner's frozen definition).
ALPHA_DEFINITION = "per_trade_expectancy_difference_v1"

FINANCING_FORMULA = "FXFV4_FROZEN_POLICY_RATE_CARRY_ACCRUAL"
FINANCING_ROUND_DP = 10                 # single defined rounding point
FINANCING_DISCLOSURE = (
    "policy rates are unsecured official rates, NOT swap/OIS-implied or "
    "broker rollover financing; per-calendar-day accrual at the day-start "
    "as-of differential from the evidenced BIS WS_CBPOL vintages (rows "
    "eligible only when available_time_utc <= the accrual instant; never on "
    "their own effective date)")
QUARANTINE_CEILING = 0.001              # td_loader-inherited OHLC-artifact ceiling

# Frozen market convention: pair -> (base rate area, quote rate area)
# (inherited unchanged from the V3 kernel).
PAIR_AREAS = {
    "EUR/USD": ("EMU", "US"),
    "GBP/USD": ("GB", "US"),
    "AUD/USD": ("AU", "US"),
    "NZD/USD": ("NZ", "US"),
    "USD/JPY": ("US", "JP"),
    "USD/CHF": ("US", "CH"),
    "USD/CAD": ("US", "CA"),
}

_NY = ZoneInfo("America/New_York")
_UTC = timezone.utc

RESPONSE_LEGS_LEGSET = tuple(l for l, _s in RESPONSE_LEGS)


# --------------------------------------------------------------------------
# price loading (td_loader schema; mirrored verbatim from V3 family1)
# --------------------------------------------------------------------------
def _parse_bar_ts(raw):
    """Snapshot bar stamps are UTC wall time; accept the canonical
    'YYYY-MM-DD HH:MM:SS' form and ISO-T fallback; fail closed otherwise."""
    if not isinstance(raw, str):
        raise ValueError(f"malformed bar timestamp: {raw!r}")
    text = raw.strip()
    try:
        t = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        t = datetime.fromisoformat(text)  # ISO-T fallback
    if t.tzinfo is not None:
        return t.astimezone(_UTC)
    return t.replace(tzinfo=_UTC)


def load_pair_h1_bars(pair: str, price_h1_dir: str) -> list:
    """Ascending, unique, validated H1 bars for one pair from the canonical
    window files (``<TAG>_1h_*_a.json``) under ``price_h1_dir``.

    Error-status provider windows (no coverage) are skipped; overlapping
    windows dedupe on the bar stamp; OHLC-inconsistent provider artifacts are
    quarantined (excluded, counted) with the inherited 0.1 percent fail-closed
    ceiling; malformed rows raise (BLOCKED_DATA; never fabricated).  Each bar
    is ``(open_utc, open, high, low, close)``.
    """
    tag = pair.replace("/", "")
    if not os.path.isdir(price_h1_dir):
        raise RuntimeError(
            f"BLOCKED_DATA: no price H1 directory for {pair}: {price_h1_dir!r}")
    names = sorted(f for f in os.listdir(price_h1_dir)
                   if f.startswith(f"{tag}_1h_") and f.endswith("_a.json")
                   and "TRUNCATED" not in f)
    if not names:
        raise RuntimeError(
            f"BLOCKED_DATA: no canonical H1 window files for {pair} under {price_h1_dir!r}")
    rows: list = []
    seen: set = set()
    quarantined = 0
    considered = 0
    for name in names:
        with open(os.path.join(price_h1_dir, name), "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, dict) and payload.get("status") == "error":
            continue  # provider no-coverage window (recorded upstream in the probe)
        values = payload.get("values") if isinstance(payload, dict) else None
        if not isinstance(values, list):
            raise RuntimeError(f"BLOCKED_DATA: malformed H1 window {name!r}")
        for row in values:
            try:
                ts = _parse_bar_ts(row["datetime"])
                bar = (ts, float(row["open"]), float(row["high"]),
                       float(row["low"]), float(row["close"]))
            except (KeyError, TypeError, ValueError) as exc:
                raise RuntimeError(f"BLOCKED_DATA: malformed bar in {name!r}: {exc}") from exc
            if ts in seen:
                continue  # boundary overlap between adjacent windows
            considered += 1
            o, h, lo, c = bar[1], bar[2], bar[3], bar[4]
            if not (h >= lo and h >= o and h >= c and lo <= o and lo <= c
                    and o > 0 and c > 0):
                quarantined += 1
                continue
            seen.add(ts)
            rows.append(bar)
    if considered and quarantined / considered > QUARANTINE_CEILING:
        raise RuntimeError(
            f"BLOCKED_DATA: quarantine ceiling exceeded for {pair}: "
            f"{quarantined}/{considered}")
    rows.sort(key=lambda b: b[0])
    return rows


# --------------------------------------------------------------------------
# daily decision bars and NY-day validity (16:00 New York, named zone)
# --------------------------------------------------------------------------
def daily_decision_bars(h1_bars: list) -> list:
    """The 16:00 America/New_York weekday H1 bars (the daily flat bar whose
    completion instant is the decision clock).  Returns ``(open_utc, open_px,
    close_px)`` ascending; DST-aware via the named zone (20:00Z EDT weeks,
    21:00Z EST weeks)."""
    out = []
    for ts, o, _h, _lo, c in h1_bars:
        ny = ts.astimezone(_NY)
        if ny.hour == 16 and ny.minute == 0 and ny.weekday() < 5:
            out.append((ts, o, c))
    return out


def ny_day_valid_map(h1_bars: list) -> dict:
    """``{ny_date: bool}`` NY-day validity for one pair (fail-closed).

    A NY-day is valid iff (a) the day's completed 16:00 America/New_York bar
    exists and (b) the pair's H1 bars of that NY-day are gap-free (sorted
    bar instants step exactly one hour -- no interior holes; a missing chunk,
    a full holiday or an early close invalidates the day).  The packet's
    "all of that day's completed H1 bars exist" is implemented hole-free and
    provider-grid-free: see AMBIGUITIES.md (A6P1 ambiguity on the per-day
    bar-count convention)."""
    by_day: dict = {}
    have_close: set = set()
    for ts, _o, _h, _lo, _c in h1_bars:
        ny = ts.astimezone(_NY)
        d = ny.date()
        by_day.setdefault(d, []).append(ts)
        if ny.hour == 16 and ny.minute == 0:
            have_close.add(d)
    out = {}
    for d, stamps in by_day.items():
        stamps = sorted(stamps)
        gap_free = all((b - a) == timedelta(hours=1) for a, b in zip(stamps, stamps[1:]))
        out[d] = bool(gap_free and d in have_close)
    return out


def valid_daily_bars(h1_bars: list) -> list:
    """The 16:00-NY weekday bars of VALID NY-days only:
    ``(open_utc, open_px, close_px)`` ascending (fail-closed trigger history;
    invalid days contribute nothing, never backfilled)."""
    valid = ny_day_valid_map(h1_bars)
    out = []
    for ts, o, _h, _lo, c in h1_bars:
        ny = ts.astimezone(_NY)
        if ny.hour == 16 and ny.minute == 0 and ny.weekday() < 5 \
                and valid.get(ny.date(), False):
            out.append((ts, o, c))
    return out


# --------------------------------------------------------------------------
# trigger series (pure; exposed for hand-computed goldens)
# --------------------------------------------------------------------------
def _valid_day_grid(valid_daily_by_pair: dict, pairs) -> list:
    """Ascending common valid-day grid ``[(ts, {pair: (ts, open, close)})]``
    over the days valid for ALL ``pairs`` (intersection by the day's 16:00-NY
    instant)."""
    sets = []
    for p in pairs:
        m = {}
        for ts, o, c in valid_daily_by_pair[p]:
            m[ts] = (ts, o, c)
        sets.append(m)
    common = set(sets[0])
    for m in sets[1:]:
        common &= set(m)
    out = []
    for ts in sorted(common):
        out.append((ts, {p: sets[i][ts] for i, p in enumerate(pairs)}))
    return out


def bloc_signed_returns(day_bars: dict, prev_day_bars: dict, pairs, signs) -> dict:
    """Signed daily log returns of the 16:00-NY completed closes over one
    valid-day step: ``sign * ln(close_t / close_{t-1})`` per pair (frozen
    sign convention; pure, hand-golden surface)."""
    out = {}
    for p in pairs:
        c_t = day_bars[p][2]
        c_prev = prev_day_bars[p][2]
        if not (c_t > 0 and c_prev > 0):
            raise RuntimeError(f"BLOCKED_DATA: non-positive close for {p}")
        out[p] = signs[p] * math.log(c_t / c_prev)
    return out


def trigger_day_series(daily_by_pair: dict, pairs, signs, estimator: str):
    """Per valid decision day, the bloc strength S and its inputs.

    Returns a list of dicts ``{"ts", "k", "r", "s"}`` in ascending day order,
    where ``k`` is the valid-day index, ``r`` the signed per-pair log returns
    over the previous valid day (day k-1) and ``s`` the bloc strength
    (``estimator`` "mean" or "median" of the signed returns).  Day 0 carries
    no return (``s`` is None).  ``estimator`` anything else fails closed.
    """
    if estimator not in ("mean", "median"):
        raise ValueError(f"unknown bloc estimator {estimator!r}")
    grid = _valid_day_grid(daily_by_pair, pairs)
    out = []
    for k, (ts, bars) in enumerate(grid):
        if k == 0:
            out.append({"ts": ts, "k": k, "r": None, "s": None})
            continue
        r = bloc_signed_returns(bars, grid[k - 1][1], pairs, signs)
        values = [r[p] for p in pairs]
        s = math.fsum(values) / len(values) if estimator == "mean" \
            else statistics.median(values)
        out.append({"ts": ts, "k": k, "r": r, "s": s})
    return out


def z_standardize(s_series: list, window: int = STANDARDIZATION_WINDOW_NY_DAYS,
                  ddof: int = Z_STD_DDOF):
    """Frozen z-score: ``z_k = (S_k - mean(S[k-window:k])) / std(S[k-window:k])``
    over the ``window`` most recent values STRICTLY BEFORE k (the decision day
    never enters its own window).  Returns a list aligned with ``s_series``
    (None where the window is incomplete or the window std is 0 -- fail-closed
    NO_EVAL, never a fabricated z)."""
    out = [None] * len(s_series)
    if ddof != 1:
        raise ValueError("frozen z denominator is the sample std (ddof=1)")
    for k in range(len(s_series)):
        if k < window:
            continue
        win = [s_series[i] for i in range(k - window, k)]
        if any(v is None for v in win):
            continue
        sd = statistics.stdev(win)
        if not (sd > 0):
            continue
        out[k] = (s_series[k] - math.fsum(win) / window) / sd
    return out


def event_flags_from_z(z_series: list, threshold: float = EVENT_THRESHOLD) -> list:
    """Event iff z <= threshold (<= semantics frozen); None (NO_EVAL) never
    fires."""
    return [z is not None and z <= threshold for z in z_series]


def benchmark_event_flags(z_series: list,
                          staleness: int = BENCHMARK_STALENESS_NY_DAYS,
                          threshold: float = EVENT_THRESHOLD) -> list:
    """Benchmark (stale-trigger) event flags: day k fires iff the trigger
    evaluated on valid-day k-staleness fired (S read on NY-day t-10; the
    staleness strictly exceeds the 5-day drift window)."""
    out = [False] * len(z_series)
    for k in range(len(z_series)):
        j = k - staleness
        out[k] = bool(j >= 0 and z_series[j] is not None and z_series[j] <= threshold)
    return out


# --------------------------------------------------------------------------
# schedule (governor + fail-closed fills + fold force-flat)
# --------------------------------------------------------------------------
def _iso(t: datetime) -> str:
    return t.astimezone(_UTC).isoformat()


def force_flat_indices(daily: list) -> set:
    """Per leg: indices of the last existing 16:00-NY bar before each frozen
    force-flat boundary (internal fold boundaries + span end).  A grid that
    ends before a boundary still force-flats at its last bar (the boundary's
    last-preceding bar): no position survives past the final bar."""
    idx: set = set()
    for boundary in FORCE_FLAT_BOUNDARIES:
        b = datetime.fromisoformat(boundary)
        before = [i for i, bar in enumerate(daily) if bar[0] < b]
        if before:
            idx.add(before[-1])
    return idx


def _resolve_exit(bars, entry_idx, ff_indices):
    """Exit for an entry at ``entry_idx``: the 5th existing daily bar after
    the entry bar (exactly 5 completed NY-days), force-clamped to the last
    pre-boundary bar when the scheduled exit would cross a frozen fold
    boundary, or to the final bar at data end.  exit index > entry index
    always (an entry filling exactly on a flatten bar is suppressed before
    this is reached)."""
    sched = entry_idx + HOLDING_NY_DAYS
    later_ff = sorted(f for f in ff_indices if f > entry_idx)
    if later_ff and later_ff[0] <= sched:
        return later_ff[0], True
    if sched >= len(bars):
        return len(bars) - 1, True  # data end: last existing bar
    return sched, False


def schedule_legs(arm_id: str, decision_instants: list, legs_daily: dict,
                  notional_usd: int = NOTIONAL_USD) -> dict:
    """Frozen basket state machine for one arm over one decision-day set.

    ``decision_instants``  ascending UTC instants of the arm's event days
                           (one decision per NY-day; the day's 16:00-NY
                           instant).
    ``legs_daily``         {leg: [(ts, open, close)] ascending} the legs'
                           EXISTING 16:00-NY bars (fills need bar existence,
                           not trigger-day validity).

    Governor: max 1 position per leg; a leg is flat at decision instant T iff
    no open position satisfies entry_bar_ts <= T < exit_bar_ts (a position
    exiting exactly at T is closed at the decision completion -- flat).
    Blocked / unfillable events are NO_TRADE records, never deferred, never
    fill-forwarded.  Exits resolve at entry time (boundary / data-end clamp).
    """
    ff_by_leg = {leg: force_flat_indices(bars) for leg, bars in legs_daily.items()}
    decisions: list = []
    skipped: list = []
    counters = {"n_decision_instants": len(decision_instants),
                "n_leg_events_considered": 0, "n_leg_blocked_open": 0,
                "n_entries": 0, "n_skipped_entry_fills": 0,
                "n_entries_suppressed_by_boundary": 0,
                "n_force_flats": 0, "n_round_trips": 0}
    open_pos = {}  # leg -> {"entry_idx", "entry_ts", "exit_ts", ...}

    for ts in decision_instants:
        ts_dt = ts if isinstance(ts, datetime) else datetime.fromisoformat(str(ts))
        for leg, side in RESPONSE_LEGS:
            if leg not in legs_daily:
                continue  # drop-one scenario: the leg is excluded entirely
            counters["n_leg_events_considered"] += 1
            bars = legs_daily[leg]
            ts_list = [b[0] for b in bars]
            pos = open_pos.get(leg)
            if pos is not None:
                if pos["exit_ts"] <= ts_dt:
                    open_pos.pop(leg, None)  # closed at/before this decision
                else:
                    counters["n_leg_blocked_open"] += 1
                    continue  # already in a position: event ignored (no refresh)
            j = bisect.bisect_right(ts_list, ts_dt)
            if j >= len(bars):
                skipped.append({"decision_ts": _iso(ts_dt), "pair": leg,
                                "reason": "NO_NEXT_BAR_FOR_ENTRY_FILL"})
                counters["n_skipped_entry_fills"] += 1
                continue
            fill_ts = bars[j][0]
            if fill_ts - ts_dt > timedelta(days=MAX_FILL_LAG_DAYS):
                skipped.append({"decision_ts": _iso(ts_dt), "pair": leg,
                                "reason": "ENTRY_FILL_LAG_EXCEEDS_FROZEN_ALLOWANCE"})
                counters["n_skipped_entry_fills"] += 1
                continue
            if j in ff_by_leg[leg]:
                # the fill would land exactly on the fold flatten bar (a
                # zero-length forced round trip): NO_TRADE, never deferred
                skipped.append({"decision_ts": _iso(ts_dt), "pair": leg,
                                "reason": "ENTRY_FILLS_AT_FOLD_FLATTEN_BAR"})
                counters["n_entries_suppressed_by_boundary"] += 1
                continue
            exit_idx, force_flat = _resolve_exit(bars, j, ff_by_leg[leg])
            open_pos[leg] = {"side": side, "decision_ts": ts_dt,
                             "entry_idx": j, "entry_ts": fill_ts,
                             "exit_idx": exit_idx, "exit_ts": bars[exit_idx][0],
                             "force_flat": force_flat}
            counters["n_entries"] += 1

    for leg, side in RESPONSE_LEGS:
        if leg not in legs_daily:
            continue  # drop-one scenario: the leg is excluded entirely
        pos = open_pos.pop(leg, None)
        if pos is None:
            continue
        bars = legs_daily[leg]
        did = f"{arm_id}|{leg}|{_iso(pos['decision_ts'])}"
        decisions.append({
            "decision_id": did,
            "pair": leg,
            "decision_ts": _iso(pos["decision_ts"]),
            "side": int(side),
            "notional_usd": int(notional_usd),
            "entry_bar_ts": _iso(bars[pos["entry_idx"]][0]),
            "entry_price": bars[pos["entry_idx"]][1],
            "exit_bar_ts": _iso(bars[pos["exit_idx"]][0]),
            "exit_price": bars[pos["exit_idx"]][1],
            "force_flat": bool(pos["force_flat"]),
        })
        counters["n_force_flats"] += int(pos["force_flat"])
        counters["n_round_trips"] += 1
    decisions.sort(key=lambda d: (d["decision_ts"], d["pair"]))
    return {"decisions": decisions, "skipped_entries": skipped,
            "counters": counters}


# --------------------------------------------------------------------------
# financing events (frozen formula, carried never computed by the runner)
# --------------------------------------------------------------------------
def financing_adjustment_usd(pair: str, decision: dict, reader) -> float:
    """``sign * notional * sum_of_daily(d) / 365`` accrued per calendar day
    at that day's 00:00Z as-of differential over the held calendar days
    (inherited V3 kernel convention, verbatim)."""
    base_area, quote_area = PAIR_AREAS[pair]
    entry = datetime.fromisoformat(decision["entry_bar_ts"])
    exit_ = datetime.fromisoformat(decision["exit_bar_ts"])
    day = entry.astimezone(_UTC).replace(hour=0, minute=0, second=0,
                                         microsecond=0) + timedelta(days=1)
    day_ds: list = []
    while day <= exit_:
        d = reader.differential(base_area, quote_area, day)
        if d is None:
            raise RuntimeError(
                "BLOCKED_DATA: financing day-start differential not evaluable for "
                f"{pair} at {day.isoformat()}; fail closed (never backfilled)")
        day_ds.append(d / 100.0)  # percent-per-annum vintages -> decimals
        day += timedelta(days=1)
    sign = 1.0 if decision["side"] > 0 else -1.0
    value = sign * float(decision["notional_usd"]) * math.fsum(day_ds) / 365.0
    return round(value, FINANCING_ROUND_DP)


# --------------------------------------------------------------------------
# the frozen arm wiring
# --------------------------------------------------------------------------
_ARM_TRIGGER = {
    "anchor": (TRIGGER_PAIRS, TRIGGER_SIGNS, "mean"),
    "neighbour": (TRIGGER_PAIRS, TRIGGER_SIGNS, "median"),
    "causal_negative_control": (SHAM_TRIGGER_PAIRS, SHAM_TRIGGER_SIGNS, "mean"),
    "benchmark_treatment": (TRIGGER_PAIRS, TRIGGER_SIGNS, "mean"),
}


def _run_spec(trigger_pairs, trigger_signs, estimator, stale_trigger_days: int,
              legs, price_dir, reader, arm_id: str, leg_universe=None) -> dict:
    """One arm schedule from frozen constants (pure orchestration; shared by
    run_arm and the drop-one leg-drop scenarios)."""
    trigger_daily = {p: valid_daily_bars(load_pair_h1_bars(p, price_dir))
                     for p in trigger_pairs}
    series = trigger_day_series(trigger_daily, trigger_pairs, trigger_signs,
                                estimator)
    s_series = [day["s"] for day in series]
    z_series = z_standardize(s_series)
    if stale_trigger_days:
        flags = benchmark_event_flags(z_series, staleness=stale_trigger_days)
    else:
        flags = event_flags_from_z(z_series)
    decision_instants = [day["ts"] for day, f in zip(series, flags) if f]
    legs_daily = {leg: daily_decision_bars(load_pair_h1_bars(leg, price_dir))
                  for leg in (leg_universe or legs)}
    sched = schedule_legs(arm_id, decision_instants, legs_daily)
    n_no_eval = sum(1 for z in z_series if z is None)
    counters = sched["counters"]
    counters["n_trigger_valid_days"] = len(series)
    counters["n_trigger_return_days"] = sum(1 for d in series if d["s"] is not None)
    counters["n_trigger_evaluable_days"] = sum(1 for z in z_series if z is not None)
    counters["n_event_days"] = len(decision_instants)
    counters["n_no_eval_days"] = n_no_eval
    return {"decisions": sched["decisions"], "skipped_entries": sched["skipped_entries"],
            "counters": counters}


def run_arm(arm: str, data_paths: dict, macro_reader, freeze_token=None) -> dict:
    """Runner contract entry point (see module docstring).  ``arm`` is one of
    ``anchor`` / ``neighbour`` / ``causal_negative_control`` (shorthand
    ``control`` accepted) or the runner-required ``benchmark_treatment``.
    ``freeze_token`` is accepted and ignored (dummy-vs-scored is a
    runner-side distinction)."""
    arm = ARM_ALIASES.get(arm, arm)
    if arm not in ARM_IDS:
        raise ValueError(f"unknown arm {arm!r}; expected one of {sorted(ARM_IDS)}")
    price_dir = (data_paths or {}).get("price_h1_dir")
    if not price_dir:
        raise RuntimeError("BLOCKED_DATA: data_paths is missing 'price_h1_dir'")
    if macro_reader is None:
        from research.assets.forex_free_v3.macro_reader import from_data_paths
        macro_reader = from_data_paths(data_paths)

    trigger_pairs, trigger_signs, estimator = _ARM_TRIGGER[arm]
    stale = BENCHMARK_STALENESS_NY_DAYS if arm == BENCHMARK_ARM else 0
    legs = [leg for leg, _side in RESPONSE_LEGS]
    spec = _run_spec(trigger_pairs, trigger_signs, estimator, stale, legs,
                     price_dir, macro_reader, ARM_IDS[arm])

    all_decisions: list = []
    financing_events: list = []
    for decision in spec["decisions"]:
        adjustment = financing_adjustment_usd(decision["pair"], decision,
                                              macro_reader)
        all_decisions.append(decision)
        financing_events.append({
            "decision_id": decision["decision_id"],
            "financing_adjustment_usd": adjustment,
            "formula": FINANCING_FORMULA,
        })
    all_decisions.sort(key=lambda d: (d["decision_ts"], d["pair"]))
    index = {d["decision_id"]: i for i, d in enumerate(all_decisions)}
    financing_events.sort(key=lambda ev: index[ev["decision_id"]])

    meta = {
        "decision_clock": "daily",
        "proposal_id": PROPOSAL_ID,
        "family_id": "family1",
        "arm": arm,
        "arm_id": ARM_IDS[arm],
        "pair_universe": list(PAIRS),
        "trigger_pairs": list(trigger_pairs),
        "trigger_sign_convention": [f"{'+' if trigger_signs[p] > 0 else '-'}{p}"
                                    for p in trigger_pairs],
        "bloc_estimator": estimator,
        "response_legs": [f"{'LONG' if s > 0 else 'SHORT'} {p}"
                          for p, s in RESPONSE_LEGS],
        "standardization_window_ny_days": STANDARDIZATION_WINDOW_NY_DAYS,
        "event_threshold": EVENT_THRESHOLD,
        "holding_ny_days": HOLDING_NY_DAYS,
        "benchmark_staleness_ny_days": stale,
        "warmup_daily_bars": STANDARDIZATION_WINDOW_NY_DAYS + 1,
        "alpha_definition": ALPHA_DEFINITION,
        "notional_usd_unit": NOTIONAL_USD,
        "financing_formula": FINANCING_FORMULA,
        "financing_disclosure": FINANCING_DISCLOSURE,
        "macro_access_note": (
            "policy rates read ONLY via macro_reader for the financing accrual "
            "(availability-gated; the SIGNAL is price-only; lane diversity: no "
            "policy input anywhere in trigger or direction)"),
        "z_std_ddof": Z_STD_DDOF,
        "fill_delay_events": {},  # frozen one-session delay stress: separate
        # component carried UNBLENDED through the kernel's metadata channel
        # (book_stress fill_delay_events); no cost blending by construction.
        "fold_boundaries": list(FOLD_BOUNDARIES),
        "force_flat_boundaries": list(FORCE_FLAT_BOUNDARIES),
        "schedule": {"total": spec["counters"]},
        "skipped_entries": spec["skipped_entries"],
    }
    if arm == BENCHMARK_ARM:
        meta["benchmark_treatment_note"] = (
            "the packet's incremental_test benchmark: the anchor law with the "
            "trigger read STALE on NY-day t-10 (10 valid NY-days, strictly "
            "beyond the 5-day drift window); identical legs, clocks, holding, "
            "fills, costs.  Booked by the runner inside the scored anchor "
            "cell for the per-trade expectancy-difference incremental alpha.")
    return {"decisions": all_decisions, "financing_events": financing_events,
            "meta": meta}


# --------------------------------------------------------------------------
# drop-one leg-drop scenarios (packet drop_one_design; schedule level)
# --------------------------------------------------------------------------
def drop_one_leg_schedule(leg: str, data_paths: dict, macro_reader,
                          freeze_token=None) -> dict:
    """The anchor law recomputed with exactly one basket leg excluded.

    Dropping a TRIGGER leg (AUD/USD, NZD/USD, USD/CAD) also removes it from
    S_t (the bloc renormalizes to the remaining trigger pairs with the frozen
    signs); dropping a RESPONSE leg (USD/JPY, USD/CHF) removes it from the
    basket only.  Everything else byte-identical to the anchor.  The 5
    leg-drops plus the inherited drop-one-BEST-fold scenario form the
    packet's 6-scenario suite (see FAMILY1_IMPLEMENTATION_NOTES.md for the
    harness mapping; non-vacuity asserted at implementation as a test)."""
    if leg not in RESPONSE_LEGS_LEGSET:
        raise ValueError(f"unknown leg {leg!r}")
    pairs = tuple(p for p in TRIGGER_PAIRS if p != leg)
    signs = {p: TRIGGER_SIGNS[p] for p in pairs}
    legs = tuple(l for l, _s in RESPONSE_LEGS if l != leg)
    price_dir = (data_paths or {}).get("price_h1_dir")
    if not price_dir:
        raise RuntimeError("BLOCKED_DATA: data_paths is missing 'price_h1_dir'")
    return _run_spec(pairs, signs, "mean", 0, legs, price_dir, macro_reader,
                     f"{ARM_IDS['anchor']}|drop:{leg}")


# --------------------------------------------------------------------------
# margin-to-fail reporting (V4 selection freeze implementation directive:
# every scored cell records distance-to-threshold for every Stage-A gate)
# --------------------------------------------------------------------------
MIN_EXPECTANCY = 0.0
MIN_PF = 1.10
MIN_POSITIVE_FOLDS = 2
MIN_FOLD_PF = 0.80
FOLD_POPULATED_MIN_TRADES = 30
MDD_CEILING_USD = 2500.0
MAX_POS_FOLD_SHARE = 0.50
MAX_PAIR_POS_SHARE = 0.40
DROPOUT_SCENARIOS = 8
DROPOUT_MIN_SURVIVAL = 6
USD_CORR_CEILING = 0.30
STRESS_MIN_PF = 1.00
MIN_DECISIONS_PER_ARM = 40


def margin_to_fail(record: dict) -> dict:
    """Per-gate distance-to-threshold fields for one runner cell record
    (V3 ``compute_cell`` record shape).

    Sign convention, frozen: every margin is the distance from the observed
    value to its gate threshold measured into the PASSING side -- positive
    means passing, zero means at-threshold (passing for >=-gates, failing for
    strict >-gates exactly as the frozen ``stage_a_gates`` evaluates them),
    negative means failing.  ``None`` = not evaluable on this record (the
    corresponding gate cannot fire, e.g. an unevaluated diagnostic).
    """
    base = record.get("base") or {}
    price = record.get("base_price_only") or base
    folds = record.get("folds") or []
    populated = [f for f in folds if f.get("populated")]
    scenarios = record.get("dropout_scenarios") or []
    surv = sum(1 for s in scenarios if s.get("survived"))
    diag = record.get("usd_drift_diag") or {}
    conc = record.get("pair_concentration") or {}
    stress = record.get("stress") or {}

    exp = base.get("expectancy")
    pf = base.get("pf")
    alpha = record.get("incremental_alpha")
    pos_pop = [f for f in populated if f.get("expectancy", 0) > 0]
    pop_pfs = [f["pf"] for f in populated if f.get("pf") is not None]
    share = record.get("fold_positive_share")
    mdd = record.get("mdd_usd")
    usd_corr = diag.get("corr") if diag.get("evaluated") else None

    def _tier_margins(tier):
        m = stress.get(f"tier{tier}")
        if not m:
            return None, None
        pf_m = None if m.get("pf") is None else round(m["pf"] - STRESS_MIN_PF, 10)
        return pf_m, m.get("total_pnl")

    t15_pf, t15_total = _tier_margins(1.5)
    t20_pf, t20_total = _tier_margins(2.0)
    return {
        # the eight margins required by the lane directive
        "margin_expectancy_vs_0": None if exp is None else round(exp - MIN_EXPECTANCY, 10),
        "margin_pf_vs_1_10": None if pf is None else round(pf - MIN_PF, 10),
        "margin_fold_positive_share_vs_50pct": None if share is None else round(MAX_POS_FOLD_SHARE - share, 10),
        "margin_mdd_vs_ceiling_usd": None if mdd is None else round(MDD_CEILING_USD - mdd, 10),
        "margin_usd_drift_vs_0_30": None if usd_corr is None else round(USD_CORR_CEILING - abs(usd_corr), 10),
        "margin_concentration_vs_40pct": (None if not conc else
                                          round(MAX_PAIR_POS_SHARE - max(conc.values()), 10)),
        "margin_dropout_vs_6_of_8": surv - DROPOUT_MIN_SURVIVAL,
        "margin_incremental_alpha_vs_0": None if alpha is None else round(alpha, 10),
        # the remaining frozen Stage-A gates (selection freeze: every gate)
        "margin_price_only_sign": (None if price.get("expectancy") is None
                                   else round(price["expectancy"], 10)),
        "margin_decision_floor_vs_40": record.get("n_decisions", 0) - MIN_DECISIONS_PER_ARM,
        "margin_populated_folds_positive_vs_2": len(pos_pop) - MIN_POSITIVE_FOLDS,
        "margin_fold_pf_vs_0_80": (None if not pop_pfs else
                                   round(min(pop_pfs) - MIN_FOLD_PF, 10)),
        "margin_stress_tier_1_5_pf_vs_1_00": t15_pf,
        "margin_stress_tier_1_5_total_sign": t15_total,
        "margin_stress_tier_2_0_pf_vs_1_00": t20_pf,
        "margin_stress_tier_2_0_total_sign": t20_total,
        # population context (diagnostic; floor breach => INDETERMINATE)
        "fold_populated_counts": [f.get("trades", 0) for f in folds],
        "fold_populated_min_trades": FOLD_POPULATED_MIN_TRADES,
        "dropout_scenarios_total": DROPOUT_SCENARIOS,
    }
