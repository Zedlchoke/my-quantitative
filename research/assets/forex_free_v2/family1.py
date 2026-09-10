"""FOREX-FREE-V2 family1 module (F2-I, A9 role): frozen proposal FXFV2-A4-P1
"Tokyo-range compression -> London-morning expansion", implemented verbatim
from research/proposals/forex_free_v2/a4_lane/proposal_1.json
(sha256 e9878d43609213e74ac7bcc7b75dfeb2c464c05733ec675c030e091d414aaf0d,
verified at implementation; selection contract: family1 entry of
research/control/forex_free_v2_run/selection_freeze.json).

Schedule-only module: this file produces TRADE SCHEDULES (entry/exit events,
counts, reasons, a deterministic digest).  It contains NO PnL fields anywhere
-- the central scored runner books the emitted trades through the frozen
accounting kernel (research/assets/forex_free_v2/accounting.py).  The only
cost knowledge here is the frozen tier semantic: cost_tier 2.0 delays every
fill by one additional H1 event (proposal ``cost.tier_2_rule``).

Frozen design constants (proposal ``arms.*.single_frozen_parameter_set`` --
exactly one value per constant, no grids)::

    tokyo_session_wall        09:00-18:00 Asia/Tokyo  (= [00:00,09:00) UTC, no DST)
    london_morning_window     08:00-12:00 Europe/London wall time of the bar OPEN
    trailing_median_sessions  20 (within the trailing 30 calendar days)
    compression_ratio         0.75 (anchor and control state)
    neighbour state           tokyo_range_D < 5th-smallest of the same 20 ranges
    control trigger           Tokyo range midpoint M (placebo level)
    forced_flat               16:00 America/New_York bar open on the entry UTC day
    governor                  <= 1 entry/pair/UTC-day (structural),
                              <= 3 round trips/pair/UTC-week (dropped, not deferred)

Fail-closed laws (proposal ``missing_bar_rule``, ``pit_timing``): any bar
required by the state, decision, entry or exit evaluation that is missing
means NO_TRADE (or the earliest-available scheduled exit for forced-flat
only), never a silent fill-forward, never an entry without a flat exit
available that day.  Wall-clock mappings go through zoneinfo named zones
(``state_provenance``) -- never fixed UTC offsets.

Reused frozen authorities (no duplication): td_loader bar schema,
data_authority.parse_stamp / last_flat_bar_index / flat_bar_instant_utc,
accounting.canonical_json_bytes / sha256_hex / COST_TIERS.
"""
from __future__ import annotations

import bisect
import datetime as _dt
import statistics
from collections import Counter
from typing import Any, Mapping, Sequence

from research.assets.forex.sessions import local_wall_to_utc
from research.assets.forex_free_v2.accounting import (
    COST_TIERS,
    canonical_json_bytes,
    sha256_hex,
)
from research.assets.forex_free_v2.data_authority import (
    flat_bar_instant_utc,
    parse_stamp,
)

__all__ = [
    "FAMILY_ID",
    "PROPOSAL_ID",
    "ARMS",
    "TOKYO_ZONE",
    "LONDON_ZONE",
    "NEW_YORK_ZONE",
    "TOKYO_SESSION_BARS",
    "LONDON_MORNING_BARS",
    "TRAILING_SESSIONS",
    "TRAILING_WINDOW_DAYS",
    "COMPRESSION_RATIO",
    "NEIGHBOUR_ORDER_STATISTIC",
    "NOTIONAL_USD",
    "MAX_ENTRIES_PER_PAIR_PER_UTC_DAY",
    "MAX_ROUND_TRIPS_PER_PAIR_PER_UTC_WEEK",
    "EXIT_REASONS",
    "NO_TRADE_REASONS",
    "PublicationNotAuthorized",
    "publish_schedule_once",
    "tokyo_session_slots",
    "london_morning_slots",
    "tokyo_sessions",
    "trailing_ranges",
    "state_from_sessions",
    "state_features",
    "compute_arm_schedule",
    "arm_decision_days",
]

# --- frozen identity ------------------------------------------------------------ #
FAMILY_ID = "family1"
PROPOSAL_ID = "FXFV2-A4-P1"
ARMS = ("anchor", "neighbour", "control")

TOKYO_ZONE = "Asia/Tokyo"
LONDON_ZONE = "Europe/London"
NEW_YORK_ZONE = "America/New_York"

# --- frozen constants (proposal single_frozen_parameter_set) --------------------- #
TOKYO_SESSION_BARS = 9        # 09:00..17:00 Asia/Tokyo bar-open wall hours
LONDON_MORNING_BARS = 4       # 08:00..11:00 Europe/London bar-open wall hours
TRAILING_SESSIONS = 20        # most recent valid sessions in the window
TRAILING_WINDOW_DAYS = 30     # calendar days; window = [D-30, D)
COMPRESSION_RATIO = 0.75      # anchor/control state: range < 0.75 * median20
NEIGHBOUR_ORDER_STATISTIC = 5  # 5th-smallest of the trailing 20 ranges
NOTIONAL_USD = 10000          # frozen USD-unit notional (booking is the runner's job)

MAX_ENTRIES_PER_PAIR_PER_UTC_DAY = 1
MAX_ROUND_TRIPS_PER_PAIR_PER_UTC_WEEK = 3

EXIT_REASONS = ("invalidation", "forced_flat")

# Terminal per-pair-day reasons; every scanned pair-day lands in exactly one
# bucket, so sum(no_trade_days.values()) + len(trades of the pair) equals the
# number of UTC dates present in the pair's rows.  The first four are
# "state not evaluated / no trigger evaluation" days; from ``no_break_in_window``
# on the day completed a first-break trigger evaluation and counts as a DECISION
# (proposal ``minimum_decisions``: go or no-go; void entries count too).
NO_TRADE_REASONS = (
    "tokyo_session_incomplete",
    "trailing_state_unavailable",
    "not_in_compression_state",
    "london_window_incomplete",
    "no_break_in_window",
    "governor_week_cap",
    "entry_bar_missing",
    "flat_exit_unavailable",
    "entry_not_before_forced_flat",
)

_HOUR = _dt.timedelta(hours=1)
_UTC = _dt.timezone.utc


def _iso(moment: _dt.datetime) -> str:
    return moment.astimezone(_UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- publication guard (schedule publication, never real PnL) -------------------- #
class PublicationNotAuthorized(RuntimeError):
    """A schedule publication was attempted without frozen authorization."""


def publish_schedule_once(
    schedule: Mapping[str, Any],
    ledger_path: str,
    authorization_path: str,
    score_authorized: bool = False,
    dry_run: bool = False,
) -> dict:
    """Publish a schedule summary once-only, gated by an authorization file.

    Dummy dry-run support: no real PnL ever flows through here (the schedule
    carries no PnL fields by construction).  Fail-closed semantics:

    * ``authorization_path`` missing / unparsable / not ``score_authorized:
      true`` => :class:`PublicationNotAuthorized` raised (always).
    * ``score_authorized=False`` (the dummy flag): publish is REFUSED.  With
      ``dry_run=True`` the refusal is reported as a status dict and nothing
      is written; with ``dry_run=False`` it raises.
    * Fully authorized: the canonical schedule digest line is appended via
      the frozen :class:`~research.assets.forex_free_v2.accounting.
      AtomicJsonlPublisher` (once-only per digest).
    """
    import json
    import os

    from research.assets.forex_free_v2.accounting import AtomicJsonlPublisher

    try:
        with open(authorization_path, "r", encoding="utf-8") as handle:
            auth = json.load(handle)
    except (OSError, ValueError) as exc:
        raise PublicationNotAuthorized(
            f"PUBLICATION_REFUSED: authorization file {authorization_path!r} "
            f"missing or unparsable ({exc}); no schedule may be published"
        ) from exc
    if auth.get("score_authorized") is not True:
        raise PublicationNotAuthorized(
            f"PUBLICATION_REFUSED: {authorization_path!r} does not authorize "
            "scoring (score_authorized is not true)"
        )
    summary = {
        "family_id": schedule.get("family_id"),
        "proposal_id": schedule.get("proposal_id"),
        "arm": schedule.get("arm"),
        "cost_tier": schedule.get("cost_tier"),
        "schedule_digest": schedule.get("schedule_digest"),
    }
    if not score_authorized:
        status = {
            "status": "REFUSED_SCORE_NOT_AUTHORIZED",
            "written": False,
            "dry_run": bool(dry_run),
            "summary": summary,
        }
        if dry_run:
            return status
        raise PublicationNotAuthorized(
            "PUBLICATION_REFUSED: score-authorized flag is false; "
            "dummy dry-run only (pass dry_run=True for a no-write refusal report)"
        )
    publisher = AtomicJsonlPublisher(ledger_path)
    observed_delta, published_now = publisher.publish_once(summary)
    return {
        "status": "PUBLISHED",
        "written": bool(published_now),
        "dry_run": False,
        "observed_delta": observed_delta,
        "published_now": published_now,
        "summary": summary,
    }


# --- clock mapping (named zones via zoneinfo, never fixed offsets) ---------------- #
def tokyo_session_slots(day: _dt.date) -> list[_dt.datetime]:
    """UTC bar-open instants of the Tokyo session of Tokyo-local ``day``.

    The session is 09:00-18:00 Asia/Tokyo wall (sessions.py TOKYO_SESSION
    convention) mapped through zoneinfo; because Japan has no DST this equals
    [00:00, 09:00) UTC of the same UTC date.  The mapping itself is a
    named-zone conversion, per the proposal ``state_provenance``.
    """
    return [
        local_wall_to_utc(TOKYO_ZONE, _dt.datetime.combine(day, _dt.time(h, 0)))
        for h in range(9, 18)
    ]


def london_morning_slots(day: _dt.date) -> list[_dt.datetime]:
    """UTC bar-open instants of the London morning window of London-local ``day``.

    Window [08:00, 12:00) Europe/London wall time of the bar OPEN
    (4 hourly slots); BST/GMT handled by zoneinfo named-zone conversion.
    """
    return [
        local_wall_to_utc(LONDON_ZONE, _dt.datetime.combine(day, _dt.time(h, 0)))
        for h in range(8, 12)
    ]


# --- state features (hand-verifiable goldens live on these) ------------------------ #
def tokyo_sessions(rows: Sequence[Mapping[str, Any]]) -> dict[_dt.date, dict[str, Any]]:
    """Tokyo sessions of ``rows`` (td_loader schema) that are VALID.

    A session of Tokyo-local civil date D is valid only if all 9 H1 bars
    exist (fail-closed otherwise: the day's state is NOT evaluated).  For
    each valid session: ``range = max(high) - min(low)`` over the 9 bars,
    ``t_high``, ``t_low`` and ``mid = (t_high + t_low) / 2``.
    """
    index = _stamp_index(rows)
    sessions: dict[_dt.date, dict[str, Any]] = {}
    for day in sorted({stamp.date() for stamp in index}):
        slots = tokyo_session_slots(day)
        if any(slot not in index for slot in slots):
            continue
        bars = [rows[index[slot]] for slot in slots]
        highs = [float(bar["high"]) for bar in bars]
        lows = [float(bar["low"]) for bar in bars]
        t_high = max(highs)
        t_low = min(lows)
        sessions[day] = {
            "range": t_high - t_low,
            "t_high": t_high,
            "t_low": t_low,
            "mid": (t_high + t_low) / 2.0,
        }
    return sessions


def trailing_ranges(
    sessions: Mapping[_dt.date, Mapping[str, Any]],
    day: _dt.date,
) -> list[float] | None:
    """Ranges of the 20 most recent VALID sessions strictly before ``day``,
    all within the trailing 30 calendar days (window [day-30, day)).

    Fewer than 20 such sessions => state NOT evaluated (``None``, fail-closed).
    """
    window_start = day - _dt.timedelta(days=TRAILING_WINDOW_DAYS)
    prior = sorted(d for d in sessions if window_start <= d < day)
    if len(prior) < TRAILING_SESSIONS:
        return None
    return [sessions[d]["range"] for d in prior[-TRAILING_SESSIONS:]]


def state_from_sessions(
    sessions: Mapping[_dt.date, Mapping[str, Any]],
    day: _dt.date,
    arm: str,
    sorted_days: Sequence[_dt.date] | None = None,
) -> dict[str, Any] | None:
    """State features of ``day`` from precomputed valid sessions; ``None`` if
    the state is not evaluated (Tokyo session incomplete or the trailing
    20-session window is unavailable -- both fail closed).

    ``compressed``: anchor/control ``range_D < 0.75 * median20``;
    neighbour ``range_D < Q20`` (5th-smallest of the same 20 ranges,
    no interpolation).  The control arm holds the anchor's compression state
    and swaps only the trigger/invalidation level to the midpoint M.

    ``sorted_days`` may carry the precomputed ascending session dates (an
    internal optimization for full-history runs; results are identical).
    """
    if arm not in ARMS:
        raise ValueError(f"arm must be one of {ARMS}, got {arm!r}")
    if day not in sessions:
        return None
    if sorted_days is None:
        ranges = trailing_ranges(sessions, day)
        if ranges is None:
            return None
    else:
        window_start = day - _dt.timedelta(days=TRAILING_WINDOW_DAYS)
        lo = bisect.bisect_left(sorted_days, window_start)
        hi = bisect.bisect_left(sorted_days, day)
        prior = list(sorted_days[lo:hi])
        if len(prior) < TRAILING_SESSIONS:
            return None
        ranges = [sessions[d]["range"] for d in prior[-TRAILING_SESSIONS:]]
    session = sessions[day]
    median20 = statistics.median(ranges)
    q20 = sorted(ranges)[NEIGHBOUR_ORDER_STATISTIC - 1]
    compressed_anchor = session["range"] < COMPRESSION_RATIO * median20
    compressed = compressed_anchor if arm != "neighbour" else (session["range"] < q20)
    return {
        "day": day,
        "tokyo_range": session["range"],
        "t_high": session["t_high"],
        "t_low": session["t_low"],
        "mid": session["mid"],
        "median20": median20,
        "q20": q20,
        "trailing_ranges": list(ranges),
        "compressed_anchor": compressed_anchor,
        "compressed": compressed,
    }


def state_features(
    rows: Sequence[Mapping[str, Any]],
    day: _dt.date,
    arm: str,
) -> dict[str, Any] | None:
    """Convenience wrapper: :func:`state_from_sessions` over
    :func:`tokyo_sessions` of ``rows`` (single-day golden checks)."""
    return state_from_sessions(tokyo_sessions(rows), day, arm)


# --- internals ---------------------------------------------------------------------- #
def _stamp_index(rows: Sequence[Mapping[str, Any]]) -> dict[_dt.datetime, int]:
    """Stamp -> row index; fail closed on duplicates or non-ascending order."""
    index: dict[_dt.datetime, int] = {}
    previous: _dt.datetime | None = None
    for i, row in enumerate(rows):
        stamp = parse_stamp(row["datetime"], f"rows[{i}].datetime")
        if stamp in index:
            raise ValueError(f"duplicate bar stamp {_iso(stamp)}; td_loader output must be unique")
        if previous is not None and stamp < previous:
            raise ValueError(f"non-ascending bar stamps at index {i}; td_loader output must be sorted")
        index[stamp] = i
        previous = stamp
    return index


def _validate_cost_tier(cost_tier: Any) -> float:
    if isinstance(cost_tier, bool) or not isinstance(cost_tier, (int, float)):
        raise ValueError(f"cost_tier must be a number, got {cost_tier!r}")
    tier = float(cost_tier)
    if tier not in COST_TIERS:
        raise ValueError(f"cost_tier must be one of {COST_TIERS}, got {cost_tier!r}")
    return tier


def _break_direction(
    high: float,
    low: float,
    close: float,
    t_high: float,
    t_low: float,
    mid: float,
    arm: str,
) -> int | None:
    """``+1`` / ``-1`` when the bar's break_test fires; ``None`` when it does
    not; ``0`` for an exact tie (both breaches, close exactly at M => no
    trade from this bar, later bars may still fire).  The both-breaches tie
    break uses sign(close - M) in every arm (proposal ``break_test``); the
    control arm swaps the trigger levels to M."""
    if arm == "control":
        up, down = high > mid, low < mid
    else:
        up, down = high > t_high, low < t_low
    if up and down:
        if close > mid:
            return 1
        if close < mid:
            return -1
        return 0
    if up:
        return 1
    if down:
        return -1
    return None


def _invalidated(close: float, direction: int, t_high: float, t_low: float,
                 mid: float, arm: str) -> bool:
    """Completed-bar invalidation: long close back inside the range below the
    trigger level (T_H; control M); short close back above (T_L; control M)."""
    level = mid if arm == "control" else (t_high if direction == 1 else t_low)
    return close < level if direction == 1 else close > level


def _week_key(day: _dt.date) -> _dt.date:
    """Frozen UTC week key: [Monday 00:00Z, next Monday 00:00Z)."""
    return day - _dt.timedelta(days=day.weekday())


# --- the frozen schedule ------------------------------------------------------------ #
def _run_arm(
    arm: str,
    canonical_rows_by_pair: Mapping[str, Sequence[Mapping[str, Any]]],
    tier: float,
) -> tuple[list[dict[str, Any]], int, dict[str, int], str | None,
           dict[str, list[str]]]:
    """Single internal pass shared by :func:`compute_arm_schedule` and
    :func:`arm_decision_days`.  Pairs are processed independently (no
    cross-pair state anywhere), in sorted-pair order, over UTC dates
    ascending.  Returns ``(trades, decisions, no_trade_counts,
    first_evaluable_iso, decision_days_by_pair)``."""
    fill_delay = 1 if tier == 2.0 else 0  # only tier 2.0 delays fills

    trades: list[dict[str, Any]] = []
    decisions = 0
    no_trade = Counter({reason: 0 for reason in NO_TRADE_REASONS})
    first_evaluable: _dt.date | None = None
    decision_days_by_pair: dict[str, list[str]] = {}

    for pair in sorted(canonical_rows_by_pair):
        rows = list(canonical_rows_by_pair[pair])
        if not rows:
            decision_days_by_pair[pair] = []
            continue
        index = _stamp_index(rows)
        stamps = sorted(index)
        sessions = tokyo_sessions(rows)
        session_days = sorted(sessions)
        week_round_trips: dict[_dt.date, int] = {}
        pair_decision_days: list[str] = []

        for day in sorted({stamp.date() for stamp in stamps}):
            features = state_from_sessions(sessions, day, arm, sorted_days=session_days)
            if features is None:
                # Which fail-closed gate: today's Tokyo session or the trailing state?
                slots = tokyo_session_slots(day)
                complete = all(slot in index for slot in slots)
                no_trade["tokyo_session_incomplete" if not complete
                         else "trailing_state_unavailable"] += 1
                continue
            if not features["compressed"]:
                no_trade["not_in_compression_state"] += 1
                continue

            slots = london_morning_slots(day)
            if any(slot not in index for slot in slots):
                no_trade["london_window_incomplete"] += 1
                continue

            t_high, t_low, mid = features["t_high"], features["t_low"], features["mid"]
            decision_slot: _dt.datetime | None = None
            direction = 0
            for slot in slots:
                bar = rows[index[slot]]
                fired = _break_direction(float(bar["high"]), float(bar["low"]),
                                         float(bar["close"]), t_high, t_low, mid, arm)
                if fired is None:
                    continue
                if fired == 0:  # exact tie => no trade from this bar
                    continue
                decision_slot, direction = slot, fired
                break

            if decision_slot is None:
                # no-go: the day's first-break trigger evaluation completed
                decisions += 1
                pair_decision_days.append(day.isoformat())
                first_evaluable = (day if first_evaluable is None
                                   else min(first_evaluable, day))
                no_trade["no_break_in_window"] += 1
                continue
            # go: the trigger evaluation completed with a qualifying break
            decisions += 1
            pair_decision_days.append(day.isoformat())
            first_evaluable = (day if first_evaluable is None
                               else min(first_evaluable, day))

            # Governor: <= 1 entry/pair/UTC-day is structural (only the day's
            # first qualifying break reaches this point); <= 3 round trips per
            # UTC week drops the signal deterministically (not deferred).
            week = _week_key(day)
            if week_round_trips.get(week, 0) >= MAX_ROUND_TRIPS_PER_PAIR_PER_UTC_WEEK:
                no_trade["governor_week_cap"] += 1
                continue

            # Entry: OPEN of the next allowed H1 bar after the decision bar,
            # delayed by one extra event at tier 2.0.  Missing => void, NO_TRADE.
            entry_slot = decision_slot + _HOUR * (1 + fill_delay)
            if entry_slot not in index:
                no_trade["entry_bar_missing"] += 1
                continue
            entry_i = index[entry_slot]

            # Forced flat: the 16:00 New York bar open on the entry UTC day
            # (20:00Z EDT / 21:00Z EST).  If that bar is absent, the frozen
            # fallback exits at the open of the immediately preceding existing
            # H1 bar of the same day (early forced flat); if no such bar exists
            # after the entry, no flat exit is available => NO_TRADE (an entry
            # is never made without a flat exit available that day).
            flat_instant = flat_bar_instant_utc(day)
            if flat_instant in index:
                forced_i = index[flat_instant]
                forced_slot = flat_instant
            else:
                earlier = [s for s in stamps
                           if s.date() == day and s < flat_instant and s > entry_slot]
                if not earlier:
                    no_trade["flat_exit_unavailable"] += 1
                    continue
                forced_slot = max(earlier)
                forced_i = index[forced_slot]
            if entry_slot >= forced_slot:
                # (reachable only with contrived clocks) cannot enter before the flat
                no_trade["entry_not_before_forced_flat"] += 1
                continue

            # Invalidation scan over completed bars at-or-after the entry bar,
            # strictly before the forced-flat bar (the flat bar's open closes
            # the position before its own close exists).  Exit fills one event
            # after the triggering bar (+ one extra at tier 2.0), bounded by
            # the forced-flat instant; a delayed fill beyond the flat rule
            # degrades to the forced-flat exit; a missing fill slot skips to a
            # later trigger (the guaranteed forced-flat exit always remains).
            exit_slot: _dt.datetime | None = None
            exit_reason = "forced_flat"
            for i in range(entry_i, forced_i):
                bar = rows[i]
                if not _invalidated(float(bar["close"]), direction, t_high, t_low,
                                    mid, arm):
                    continue
                fill_slot = parse_stamp(bar["datetime"]) + _HOUR * (1 + fill_delay)
                if fill_slot in index and fill_slot <= forced_slot:
                    exit_slot = fill_slot
                    exit_reason = "invalidation"
                    break
                if fill_slot in index:
                    # delayed fill would land after the flat rule: bounded
                    exit_slot = forced_slot
                    exit_reason = "forced_flat"
                    break
                # fill slot missing: this invalidation cannot fill; the scan
                # continues (the forced-flat exit is still guaranteed).
            if exit_slot is None:
                exit_slot = forced_slot

            exit_i = index[exit_slot]
            entry_ts = _iso(entry_slot)
            trades.append({
                "trade_id": f"{FAMILY_ID}|{arm}|{pair}|{entry_ts}",
                "pair": pair,
                "side": direction,
                "notional_usd": NOTIONAL_USD,
                "entry_price": float(rows[entry_i]["open"]),
                "entry_ts": entry_ts,
                "decision_ts": _iso(decision_slot),
                "exit_price": float(rows[exit_i]["open"]),
                "exit_ts": _iso(exit_slot),
                "exit_reason": exit_reason,
            })
            week_round_trips[week] = week_round_trips.get(week, 0) + 1
        decision_days_by_pair[pair] = pair_decision_days

    return trades, decisions, dict(no_trade), (
        first_evaluable.isoformat() if first_evaluable else None), decision_days_by_pair


def compute_arm_schedule(
    arm: str,
    canonical_rows_by_pair: Mapping[str, Sequence[Mapping[str, Any]]],
    cost_tier: float = 1.0,
    data: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute the frozen FXFV2-A4-P1 schedule of ``arm`` over the pairs.

    Pairs are processed independently (no cross-pair state anywhere), in
    sorted-pair order, over UTC dates ascending.  Returns a schedule dict
    with trades (NO PnL fields -- the runner books them through the
    accounting kernel), the decision count, terminal no-trade reason counts,
    the first evaluable date, and ``schedule_digest`` =
    sha256(canonical_json_bytes(payload)).

    Tier semantics (proposal ``cost.tier_2_rule``): ``cost_tier=2.0`` delays
    each fill (entry and exit) by one additional H1 event, recomputing the
    schedule; a delayed entry that cannot happen before the forced-flat rule
    voids the trade (NO_TRADE), a delayed exit is still bounded by the
    forced-flat instant.
    """
    if arm not in ARMS:
        raise ValueError(f"arm must be one of {ARMS}, got {arm!r}")
    tier = _validate_cost_tier(cost_tier)
    if data is not None and not isinstance(data, Mapping):
        raise ValueError("data must be a mapping when provided (reserved; unused)")
    trades, decisions, no_trade, first_evaluable, _ = _run_arm(arm, canonical_rows_by_pair, tier)
    payload = {
        "family_id": FAMILY_ID,
        "proposal_id": PROPOSAL_ID,
        "arm": arm,
        "cost_tier": tier,
        "trades": trades,
        "decisions": decisions,
        "no_trade_days": dict(sorted(no_trade.items())),
        "warmup_first_evaluable_date": first_evaluable,
    }
    return {**payload, "schedule_digest": sha256_hex(canonical_json_bytes(payload))}


def arm_decision_days(
    arm: str,
    canonical_rows_by_pair: Mapping[str, Sequence[Mapping[str, Any]]],
    cost_tier: float = 1.0,
    data: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Per-pair UTC decision days of ``arm`` (audit companion; same frozen
    code path as :func:`compute_arm_schedule`).

    A decision day is a state-valid compressed UTC day on which the arm's
    first-break trigger evaluation completed (go or no-go; void entries
    included) -- the proposal ``minimum_decisions`` unit.  Returns
    ``{"arm", "cost_tier", "decisions_by_pair": {pair: [ISO dates...]}}
    `` in ascending order.  ``sum(len(v))`` equals the ``decisions`` count of
    the schedule for the same inputs (asserted by the evidence tests).
    """
    if arm not in ARMS:
        raise ValueError(f"arm must be one of {ARMS}, got {arm!r}")
    tier = _validate_cost_tier(cost_tier)
    if data is not None and not isinstance(data, Mapping):
        raise ValueError("data must be a mapping when provided (reserved; unused)")
    _, decisions, _, _, by_pair = _run_arm(arm, canonical_rows_by_pair, tier)
    return {
        "arm": arm,
        "cost_tier": tier,
        "decisions": decisions,
        "decisions_by_pair": dict(sorted(by_pair.items())),
    }
