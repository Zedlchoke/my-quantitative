#!/usr/bin/env python
"""FOREX-FREE-V2 family2 module: FXFV2-A4-P2 "London-AM range break confirmed
by retest-hold" (A9 implementation lane).

FROZEN SPEC (immutable, zero invention)
---------------------------------------
* ``research/proposals/forex_free_v2/a4_lane/proposal_2.json``
  sha256 93e940a9da932719dfe97ff76977abfc82c7b4ea663bc70c62d90a54fd4f56cd
  (verified at implementation; recorded in
  ``research/control/forex_free_v2_run/lane_report_family2.json``).
* selection contract: ``research/control/forex_free_v2_run/selection_freeze.json``
  family2 entry (family2 = FXFV2-A4-P2, arms anchor/neighbour/control).
* frequency/cost: ``research/control/forex_free_v2_run/frequency_contract.json``.

MODULE API (the central scored runner calls exactly this)
---------------------------------------------------------
``FAMILY_ID = "family2"``; ``PROPOSAL_ID = "FXFV2-A4-P2"``;
``ARMS = ("anchor", "neighbour", "control")``;
``compute_arm_schedule(arm, canonical_rows_by_pair, cost_tier=1.0, data=None)``
returning ``{"family_id","proposal_id","arm","cost_tier","trades","decisions",
"no_trade_days","schedule_digest","warmup_first_evaluable_date", ...}``.  NO PnL
fields exist anywhere in the schedule: the runner books every trade through the
accounting kernel (:mod:`research.assets.forex_free_v2.accounting`), which is
the single PnL/cost authority.  ``trade_id = f"{FAMILY_ID}|{arm}|{pair}|{entry_ts}"``.

STATE MACHINE (per pair, per Europe/London-local date D; every window is
half-open on the H1 bar-open London wall time; all wall<->UTC mappings go
through zoneinfo named-zone conversion, never fixed offsets)
----------------------------------------------------------------
1. London-AM range: the 4 bars with London-local open wall time in
   ``[08:00,12:00)`` (opens 08:00/09:00/10:00/11:00).  ``L_H = max(high)``,
   ``L_L = min(low)``.  ALL 4 bars are required; any missing bar invalidates
   the day -> ``MISSING_RANGE_BAR`` no-trade, fail-closed, never fill-forward.
2. Initial break: first completed bar with London-local open in
   ``[12:00,17:00)`` (opens 12:00..16:00) with ``high > L_H`` (side UP,
   ``L_B = L_H``) or ``low < L_L`` (side DOWN, ``L_B = L_L``).  Both sides in
   one bar -> side = ``sign(close - (L_H+L_L)/2)``; exact tie -> day ends
   ``TIE_NO_TRADE`` (counted as a decision for all arms).  The break bar's far
   extreme ``E_B`` = its high (UP) / low (DOWN).  No break in the window ->
   ``NO_BREAK`` (not a decision).
3. Resolution scan: bars with London-local open in ``[break+1h, 19:00)``
   (the proposal's ``[12:00,19:00)`` resolution window, strictly after the
   break bar -- a "subsequent" retest per the mechanism):
   * anchor retest-hold: UP ``low(b) <= L_B and close(b) > L_B``; DOWN mirror
     (``high(b) >= L_B and close(b) < L_B``).  First such bar = anchor DECISION
     bar.
   * neighbour retest-hold: identical law against ``E_B`` instead of ``L_B``.
   * void (failed retest): UP ``close(b) < L_H``; DOWN ``close(b) > L_L``,
     counted only BEFORE any anchor retest-hold (the proposal's "before any
     retest-hold" qualifier; the anchor's L_B retest is the law the void is
     defined against).  First such bar = control DECISION bar and voids the
     day for anchor and neighbour.
   The three events are mutually exclusive on any single bar (UP: retest needs
   ``close > L_H`` / ``close > E_B > L_H``, void needs ``close < L_H``).  Each
   arm locks at its first event; a void ends the whole day (anchor and
   neighbour dead, control decided); an anchor retest leaves the neighbour
   scan running (the neighbour may fire later on a different bar) but blocks
   any later void.  No event by window end -> ``NO_RESOLUTION`` (decision, no
   trade, all arms).  If the anchor retest fired first, the control's day
   resolves ``RETEST_HOLD_FIRST`` (decision, no trade).
4. Entry: OPEN of the next allowed H1 bar after the decision bar completes --
   the bar stamped exactly ``decision_bar_open + 1h`` (tier 2.0: ``+2h`` --
   every fill delayed one additional event).  The entry bar must EXIST at that
   exact instant (missing -> ``MISSING_ENTRY_BAR``, decision without trade,
   never fill-forward); its London-local open wall time must be ``< 20:00``
   (else ``ENTRY_DEADLINE``); tier 2.0 additionally requires the entry instant
   to precede the forced-flat instant (else ``TIER2_ENTRY_AFTER_FLAT``).
   ``decision_ts`` on the trade is the decision bar's CLOSE instant
   (``open + 1h``) -- the PIT moment the decision becomes known; ``entry_ts``
   is the entry bar-open stamp.
5. Exit, earlier of:
   * (a) invalidation: first completed bar AT or AFTER the entry bar whose
     close satisfies the law -- anchor/neighbour: long ``close < L_H`` /
     short ``close > L_L`` (back inside the pre-break range); control: beyond
     the OPPOSITE range extreme (long ``close < L_L`` / short ``close > L_H``).
     Exit at ``invalidating_bar_open + 1h`` (tier 2.0 ``+2h``).  If that exit
     bar does not exist -> trade dropped ``MISSING_EXIT_BAR`` (fail-closed;
     the only exit fallback the spec allows is the forced-flat one).
   * (b) forced flat: the bar stamped 16:00 America/New_York on the entry UTC
     day, exit at its OPEN (``data_authority.last_flat_bar_index``).  If that
     bar is absent, exit at the OPEN of the latest existing bar strictly
     between the entry instant and the flat instant, recorded as an early
     forced flat (proposal ``forced_flat`` fallback: "the immediately
     preceding existing H1 bar"); if no such bar exists the trade cannot be
     exited -> dropped ``MISSING_FLAT_BAR`` (NO_TRADE, fail-closed).
   Exit-instant tie (invalidation exit instant == flat instant) resolves to
   ``invalidation`` (deterministic tie-break; identical fill either way).

GOVERNOR (first-class; deterministic and PIT-safe; skip, never queue)
---------------------------------------------------------------------
* <= 1 entry / pair / UTC day: structural (one state machine per pair per
  London-local date, and every entry instant of this schedule lies on the same
  UTC date as its London-local date), plus an explicit defensive check.
* <= 3 round trips / pair / week, week = ``[Monday 00:00Z, next Monday
  00:00Z)`` per the proposal's frozen ``utc_week_definition``.  (The dispatch
  note phrased the week as "Sun 21:00 NY based"; every tradable instant of
  this schedule lies between London 12:00 and New York 16:00 on a weekday, so
  the two definitions partition the tradable instants identically -- recorded
  as a resolved ambiguity for A7 review.)  Exceeding either cap drops the
  signal (``WEEKLY_CAP``); a trade dropped by a cap consumes no budget (it
  never becomes a round trip).

COST / TIER
-----------
``cost_tier`` must be one of accounting.COST_TIERS (1.0/1.5/2.0).  Tiers
stress the per-side cost only; tier 2.0 additionally delays every fill by one
event (recomputing the schedule) as specified.  The module computes NO money
amounts; ``accounting.bps_cost`` remains the only cost authority.

WARMUP
------
``warmup_bars = 48`` (frozen): the first 48 H1 bars of each pair establish bar
continuity only; the first evaluable London-local date is the London-local
date of bar 48.  Earlier days are not evaluated (not decisions, not no-trade
days); ``warmup_first_evaluable_date`` reports the boundary.

PIT / determinism
-----------------
Every decision uses only bars completed at or before the decision bar's close
(one-event lag to entry); exits legitimately read post-entry bars but the
DECISION/ENTRY schedule never does (proven by the mutation evidence test).
Pair schedules are independent (drop-one-pair invariance holds by construction
and is tested).  ``schedule_digest`` = sha256 over the canonical JSON bytes
(``accounting.canonical_json_bytes``) of the fixed record
``{"arm","cost_tier","decisions","family_id","no_trade_days","proposal_id",
"trades"}`` with trades sorted by ``(pair, entry_ts)`` -- deterministic across
runs.

Publication gate
----------------
This module publishes nothing on its own.  ``authorized_publication`` is the
frozen gate any caller must pass to publish a family record: without the owner
authorization token every publication is refused; with ``scored=False`` a real
publication is refused (only a dummy dry-run that writes zero bytes is
allowed, per run_contract ``scoring_discipline``); a real publication requires
the authorization token AND ``scored=True`` and then goes through the
once-only ``accounting.AtomicJsonlPublisher``.

No network, no new data authority, no raw-data commit: rows come from the
caller (or, for the schedule-only audit, from
``research.assets.forex_free_v1.td_loader.load_pair_h1`` over the READ-ONLY
V1 snapshot root).  Real-data use is COUNTS-ONLY: no PnL is computed, printed
or returned anywhere in this module.
"""
from __future__ import annotations

import bisect
import datetime as _dt
import os
from zoneinfo import ZoneInfo

from research.assets.forex.sessions import local_wall_to_utc
from research.assets.forex_free_v2 import accounting as ACC
from research.assets.forex_free_v2 import data_authority as DA

__all__ = [
    "FAMILY_ID",
    "PROPOSAL_ID",
    "PROPOSAL_SHA256",
    "ARMS",
    "PAIR_UNIVERSE",
    "WARMUP_BARS",
    "AUTHORIZATION_TOKEN",
    "PublicationRefused",
    "Family2Error",
    "compute_arm_schedule",
    "authorized_publication",
    "week_monday_utc",
]

# --- frozen identity ------------------------------------------------------------- #
FAMILY_ID = "family2"
PROPOSAL_ID = "FXFV2-A4-P2"
PROPOSAL_SHA256 = "93e940a9da932719dfe97ff76977abfc82c7b4ea663bc70c62d90a54fd4f56cd"
ARMS = ("anchor", "neighbour", "control")
PAIR_UNIVERSE = ["EUR/USD", "GBP/USD", "AUD/USD", "NZD/USD", "USD/JPY", "USD/CHF", "USD/CAD"]

# --- frozen constants (proposal_2.json, verbatim) --------------------------------- #
LONDON_ZONE = "Europe/London"
NEW_YORK_ZONE = "America/New_York"
_LONDON = ZoneInfo(LONDON_ZONE)

WARMUP_BARS = 48                       # clocks.warmup_bars
_RANGE_HOURS = (8, 9, 10, 11)          # london_am_range_D: [08:00,12:00) bar opens
_TRIGGER_HOURS = (12, 13, 14, 15, 16)  # initial_break: [12:00,17:00) bar opens
_RESOLUTION_LAST_OPEN_HOUR = 18        # resolution window [12:00,19:00) bar opens
_ENTRY_DEADLINE_HOUR = 20              # entry bar-open < 20:00 Europe/London
_FLAT_NY_HOUR = 16                     # forced flat 16:00 America/New_York bar open
MAX_ENTRIES_PER_PAIR_PER_UTC_DAY = 1   # trade_budget_governor
MAX_RT_PER_PAIR_PER_WEEK = 3           # trade_budget_governor
NOTIONAL_USD = float(ACC.FROZEN_NOTIONAL_USD_UNIT)  # 10000.0, frozen design unit

_HOUR = _dt.timedelta(hours=1)
_UTC = _dt.timezone.utc

# Owner authorization token (run_contract hard_stop wording); publication gate only.
AUTHORIZATION_TOKEN = "GO FOREX V2 SCORED EXECUTION"


class Family2Error(ValueError):
    """A family2 input or state rule was violated (fail-closed)."""


class PublicationRefused(PermissionError):
    """A publication attempt failed the frozen authorization gate."""


# --- small helpers ------------------------------------------------------------------ #
def _fmt(moment: _dt.datetime) -> str:
    """Canonical UTC stamp string used in trades, ids and digests."""
    return moment.astimezone(_UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _wall_open_utc(day: _dt.date, hour: int) -> _dt.datetime:
    """Exact UTC instant of an H1 bar-open at ``hour:00`` London wall on ``day``.

    Named-zone conversion via zoneinfo (never a fixed offset).  The hours this
    schedule uses (08:00..20:00 London on weekdays) never fall inside a DST
    transition gap/fold, so the mapping is unambiguous year-round.
    """
    return local_wall_to_utc(LONDON_ZONE, _dt.datetime.combine(day, _dt.time(hour, 0)))


def _london_open(moment_utc: _dt.datetime) -> _dt.datetime:
    """London-local wall open of a bar stamped ``moment_utc`` (bar-open UTC)."""
    return moment_utc.astimezone(_UTC).astimezone(_LONDON)


def week_monday_utc(moment_utc: _dt.datetime) -> _dt.date:
    """Monday (UTC date) of the frozen week ``[Mon 00:00Z, next Mon 00:00Z)``."""
    day = moment_utc.astimezone(_UTC).date()
    return day - _dt.timedelta(days=day.weekday())


def _validate_rows(pair: str, rows) -> list[dict]:
    """Validate one pair's canonical rows: ascending, unique, well-formed.

    Stamps are bar-open UTC instants (frozen provider semantics, enforced by
    ``data_authority.parse_stamp``).  Duplicates or disorder fail closed --
    this module never silently reorders or dedupes a scored input.
    """
    if not isinstance(rows, (list, tuple)) or not rows:
        raise Family2Error(f"{pair}: rows must be a non-empty sequence")
    out = []
    prev = None
    for i, raw in enumerate(rows):
        if not isinstance(raw, dict):
            raise Family2Error(f"{pair}: rows[{i}] must be a bar dict")
        stamp = DA.parse_stamp(raw["datetime"], f"{pair}.rows[{i}].datetime")
        if prev is not None:
            if stamp == prev:
                raise Family2Error(f"{pair}: duplicate bar stamp {_fmt(stamp)}")
            if stamp < prev:
                raise Family2Error(f"{pair}: bars not ascending at {_fmt(stamp)}")
        prev = stamp
        try:
            o, h, l, c = (float(raw["open"]), float(raw["high"]),
                          float(raw["low"]), float(raw["close"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise Family2Error(f"{pair}: rows[{i}] malformed OHLC: {exc}") from exc
        out.append({"ts": stamp, "open": o, "high": h, "low": l, "close": c})
    return out


def _resolve_tier(cost_tier) -> float:
    if isinstance(cost_tier, bool) or not isinstance(cost_tier, (int, float)):
        raise Family2Error(f"cost_tier must be a number, got {cost_tier!r}")
    tier = float(cost_tier)
    if tier not in ACC.COST_TIERS:
        raise Family2Error(f"cost_tier must be one of {ACC.COST_TIERS}, got {cost_tier!r}")
    return tier


# --- shared per-day state machine ----------------------------------------------------- #
def _day_events(by_stamp: dict, day: _dt.date) -> dict:
    """Shared (arm-agnostic) day state machine: range, break, resolution events.

    ``by_stamp`` maps bar-open UTC instant -> validated bar dict.  Returned
    dict keys: ``L_H``/``L_L`` (London-AM extremes), ``no_break`` (bool),
    ``tie`` (bool), ``side`` (+1/-1/0), ``L_B`` (broken extreme), ``E_B``
    (break bar's far extreme), ``decision bars`` as ``anchor_retest_idx`` /
    ``neigh_retest_idx`` / ``void_idx`` (bar-open instants; ``void_idx`` only
    before any anchor retest-hold, per the frozen void_state law).
    """
    range_bars = []
    for hour in _RANGE_HOURS:
        bar = by_stamp.get(_wall_open_utc(day, hour))
        if bar is None:
            return {"range_missing": True}  # missing London-AM bar invalidates the day
        range_bars.append(bar)
    l_h = max(b["high"] for b in range_bars)
    l_l = min(b["low"] for b in range_bars)
    midpoint = (l_h + l_l) / 2.0

    events = {
        "range_missing": False, "L_H": l_h, "L_L": l_l, "midpoint": midpoint,
        "no_break": True, "tie": False, "side": 0, "L_B": None, "E_B": None,
        "break_ts": None,
        "anchor_retest_ts": None, "neigh_retest_ts": None, "void_ts": None,
    }

    # --- initial break: [12:00,17:00) London bar opens -------------------------- #
    break_hour = None
    for hour in _TRIGGER_HOURS:
        bar = by_stamp.get(_wall_open_utc(day, hour))
        if bar is None:
            continue
        up, down = bar["high"] > l_h, bar["low"] < l_l
        if not up and not down:
            continue
        events.update(no_break=False, break_ts=bar["ts"])
        break_hour = hour
        if up and down:
            # both sides in one bar: side = sign(close - midpoint); tie => no trade
            side = (bar["close"] > midpoint) - (bar["close"] < midpoint)
            events["tie"] = side == 0
            events["side"] = side
            events["L_B"] = l_h if side > 0 else (l_l if side < 0 else None)
            events["E_B"] = bar["high"] if side > 0 else (bar["low"] if side < 0 else None)
        else:
            events["side"] = 1 if up else -1
            events["L_B"] = l_h if up else l_l
            events["E_B"] = bar["high"] if up else bar["low"]
        break
    if events["no_break"] or events["tie"]:
        return events  # exact tie: day over for every arm (caller records it)

    # --- resolution scan: [break+1h, 19:00) London bar opens -------------------- #
    # void counts only BEFORE any anchor retest-hold; a void ends the day; an
    # anchor retest lets the neighbour scan continue (and blocks later voids).
    anchor_fired = False
    up = events["side"] > 0
    for hour in range(break_hour + 1, _RESOLUTION_LAST_OPEN_HOUR + 1):
        bar = by_stamp.get(_wall_open_utc(day, hour))
        if bar is None:
            continue
        if not anchor_fired and events["anchor_retest_ts"] is None:
            retest = (bar["low"] <= events["L_B"] and bar["close"] > events["L_B"]) if up \
                else (bar["high"] >= events["L_B"] and bar["close"] < events["L_B"])
            if retest:
                events["anchor_retest_ts"] = bar["ts"]
                anchor_fired = True
        if events["neigh_retest_ts"] is None:
            retest = (bar["low"] <= events["E_B"] and bar["close"] > events["E_B"]) if up \
                else (bar["high"] >= events["E_B"] and bar["close"] < events["E_B"])
            if retest:
                events["neigh_retest_ts"] = bar["ts"]
        if not anchor_fired and events["void_ts"] is None:
            voided = bar["close"] < l_h if up else bar["close"] > l_l
            if voided:
                events["void_ts"] = bar["ts"]
                break  # void: day over for anchor and neighbour; control decided
    return events


# --- per-pair, per-arm schedule -------------------------------------------------------- #
def _pair_arm_schedule(arm: str, pair: str, rows, tier: float) -> dict:
    bars = _validate_rows(pair, rows)
    empty = {"trades": [], "decisions": 0, "no_trade_days": {},
             "first_evaluable": None, "early_forced_flats": 0}
    if len(bars) <= WARMUP_BARS:
        return empty
    by_stamp = {b["ts"]: b for b in bars}
    stamps = [b["ts"] for b in bars]  # ascending (validated)

    # evaluable days: London-local dates present in the series, warmup-gated
    days = sorted({_london_open(b["ts"]).date() for b in bars[WARMUP_BARS:]})
    first_evaluable = days[0] if days else None

    trades: list[dict] = []
    reasons: dict[str, int] = {}
    decisions = 0
    early_forced_flats = 0
    entry_utc_days_used: set[_dt.date] = set()  # daily governor (defensive)
    week_rt_counts: dict[_dt.date, int] = {}    # weekly governor (frozen UTC week)
    delay = _HOUR * (2 if tier == 2.0 else 1)   # tier 2.0: every fill +1 event

    def no_trade(reason: str, *, decision: bool) -> None:
        nonlocal decisions
        reasons[reason] = reasons.get(reason, 0) + 1
        if decision:
            decisions += 1

    for day in days:
        ev = _day_events(by_stamp, day)
        if ev["range_missing"]:
            no_trade("MISSING_RANGE_BAR", decision=False)  # fail-closed day
            continue
        if ev["no_break"]:
            no_trade("NO_BREAK", decision=False)
            continue
        if ev["tie"]:
            no_trade("TIE_NO_TRADE", decision=True)
            continue

        # --- per-arm decision bar ------------------------------------------------ #
        if arm == "anchor":
            decision_ts_instant = ev["anchor_retest_ts"]
            unresolved = "VOID" if ev["void_ts"] is not None else "NO_RESOLUTION"
        elif arm == "neighbour":
            decision_ts_instant = ev["neigh_retest_ts"]
            unresolved = "VOID" if ev["void_ts"] is not None else "NO_RESOLUTION"
        elif arm == "control":
            decision_ts_instant = ev["void_ts"]
            unresolved = ("RETEST_HOLD_FIRST"
                          if ev["anchor_retest_ts"] is not None else "NO_RESOLUTION")
        else:
            raise Family2Error(f"unknown arm {arm!r} (must be one of {ARMS})")
        if decision_ts_instant is None:
            no_trade(unresolved, decision=True)
            continue
        decisions += 1  # the arm's state machine reached its resolution
        side = ev["side"]
        l_h, l_l = ev["L_H"], ev["L_L"]

        # --- entry: exact instant decision_open + 1 event (tier 2.0: +2) ---------- #
        entry_instant = decision_ts_instant + delay
        entry_bar = by_stamp.get(entry_instant)
        if entry_bar is None:
            no_trade("MISSING_ENTRY_BAR", decision=False)  # fail-closed, no fill-forward
            continue
        if _london_open(entry_instant).hour >= _ENTRY_DEADLINE_HOUR:
            no_trade("ENTRY_DEADLINE", decision=False)
            continue
        entry_date = entry_instant.astimezone(_UTC).date()

        # --- forced-flat target: 16:00 New York bar open on the entry UTC day ----- #
        flat_instant = DA.flat_bar_instant_utc(entry_date, NEW_YORK_ZONE)
        early_flat = False
        flat_bar = by_stamp.get(flat_instant)
        if flat_bar is None:
            # proposal forced_flat fallback: exit at the OPEN of the immediately
            # preceding EXISTING H1 bar; none resolvable => NO_TRADE fail-closed
            lo = bisect.bisect_right(stamps, entry_instant)
            hi = bisect.bisect_left(stamps, flat_instant)
            if hi <= lo:
                no_trade("MISSING_FLAT_BAR", decision=False)
                continue
            flat_bar = bars[hi - 1]
            early_flat = True
        flat_instant, flat_open = flat_bar["ts"], flat_bar["open"]

        if tier == 2.0 and entry_instant >= flat_instant:
            no_trade("TIER2_ENTRY_AFTER_FLAT", decision=False)
            continue

        # --- governor (deterministic, PIT-safe; skip, never queue) ----------------- #
        if entry_date in entry_utc_days_used:
            no_trade("DAILY_CAP", decision=False)
            continue
        week = week_monday_utc(entry_instant)
        if week_rt_counts.get(week, 0) >= MAX_RT_PER_PAIR_PER_WEEK:
            no_trade("WEEKLY_CAP", decision=False)
            continue

        # --- invalidation scan (first completed bar AT or AFTER the entry bar) ----- #
        if arm == "control":
            inv_hit = (lambda b: b["close"] < l_l) if side > 0 else (lambda b: b["close"] > l_h)
        else:
            inv_hit = (lambda b: b["close"] < l_h) if side > 0 else (lambda b: b["close"] > l_l)

        inv_ts = None
        start = bisect.bisect_left(stamps, entry_instant)
        for bar in bars[start:]:
            if bar["ts"] > flat_instant:
                break  # scan only up to the forced-flat bar (inclusive)
            if inv_hit(bar):
                inv_ts = bar["ts"]
                break

        if inv_ts is not None:
            exit_instant = inv_ts + delay
            exit_bar = by_stamp.get(exit_instant)
            if exit_bar is None:
                no_trade("MISSING_EXIT_BAR", decision=False)  # fail-closed: no fill-forward
                continue
            if exit_instant > flat_instant:
                exit_instant, exit_price, exit_reason = flat_instant, flat_open, "forced_flat"
            else:
                exit_price, exit_reason = exit_bar["open"], "invalidation"
        else:
            exit_instant, exit_price, exit_reason = flat_instant, flat_open, "forced_flat"
        if early_flat:
            early_forced_flats += 1

        # --- schedule entry (NO PnL fields: the runner books via the kernel) ------- #
        entry_ts = _fmt(entry_instant)
        trades.append({
            "trade_id": f"{FAMILY_ID}|{arm}|{pair}|{entry_ts}",
            "pair": pair,
            "side": side,
            "notional_usd": NOTIONAL_USD,
            "entry_price": entry_bar["open"],
            "entry_ts": entry_ts,
            "decision_ts": _fmt(decision_ts_instant + _HOUR),
            "exit_price": exit_price,
            "exit_ts": _fmt(exit_instant),
            "exit_reason": exit_reason,
        })
        entry_utc_days_used.add(entry_date)
        week_rt_counts[week] = week_rt_counts.get(week, 0) + 1

    trades.sort(key=lambda t: (t["pair"], t["entry_ts"]))
    return {"trades": trades, "decisions": decisions, "no_trade_days": reasons,
            "first_evaluable": first_evaluable, "early_forced_flats": early_forced_flats}


# --- module API ------------------------------------------------------------------------- #
def compute_arm_schedule(arm, canonical_rows_by_pair, cost_tier=1.0, data=None) -> dict:
    """Frozen module API: the scored runner's single entry point.

    ``arm`` in ``("anchor","neighbour","control")``; ``canonical_rows_by_pair``
    maps pair -> list of canonical H1 bar dicts (``td_loader.load_pair_h1``
    schema: ``datetime/open/high/low/close``, bar-open UTC stamps).  When it is
    ``None``, ``data`` must carry ``{"rows_by_pair": ...}`` or
    ``{"data_root": <root>}`` (the latter loads all 7 universe pairs via
    ``td_loader`` for the schedule-only audit; COUNTS ONLY, never PnL).
    ``cost_tier`` in accounting.COST_TIERS stresses cost; tier 2.0 also delays
    every fill one event (schedule recomputed).

    Returns ``{"family_id","proposal_id","arm","cost_tier","trades",
    "decisions","no_trade_days","schedule_digest","warmup_first_evaluable_date",
    "early_forced_flat_count","pairs"}``.  Trades carry exactly
    ``trade_id/pair/side/notional_usd/entry_price/entry_ts/decision_ts/
    exit_price/exit_ts/exit_reason`` and NO PnL fields.
    """
    if arm not in ARMS:
        raise Family2Error(f"arm must be one of {ARMS}, got {arm!r}")
    tier = _resolve_tier(cost_tier)

    if canonical_rows_by_pair is None:
        data = data or {}
        if isinstance(data, dict) and "rows_by_pair" in data:
            canonical_rows_by_pair = data["rows_by_pair"]
        elif isinstance(data, dict) and "data_root" in data:
            from research.assets.forex_free_v1 import td_loader
            canonical_rows_by_pair = {
                pair: td_loader.load_pair_h1(pair, data["data_root"])[0]
                for pair in PAIR_UNIVERSE
            }
        else:
            raise Family2Error("canonical_rows_by_pair is None and data carries "
                               "neither 'rows_by_pair' nor 'data_root'")
    if not isinstance(canonical_rows_by_pair, dict) or not canonical_rows_by_pair:
        raise Family2Error("canonical_rows_by_pair must be a non-empty dict of pair -> rows")

    merged_trades: list[dict] = []
    decisions = 0
    reasons: dict[str, int] = {}
    first_evaluables: list[_dt.date] = []
    early_flats = 0
    for pair in sorted(canonical_rows_by_pair):
        res = _pair_arm_schedule(arm, pair, canonical_rows_by_pair[pair], tier)
        merged_trades.extend(res["trades"])
        decisions += res["decisions"]
        for reason, count in res["no_trade_days"].items():
            reasons[reason] = reasons.get(reason, 0) + count
        if res["first_evaluable"] is not None:
            first_evaluables.append(res["first_evaluable"])
        early_flats += res["early_forced_flats"]
    merged_trades.sort(key=lambda t: (t["pair"], t["entry_ts"]))

    record = {
        "family_id": FAMILY_ID,
        "proposal_id": PROPOSAL_ID,
        "arm": arm,
        "cost_tier": tier,
        "decisions": decisions,
        "no_trade_days": dict(sorted(reasons.items())),
        "trades": merged_trades,
    }
    return {
        **record,
        "schedule_digest": ACC.sha256_hex(ACC.canonical_json_bytes(record)),
        "warmup_first_evaluable_date": (min(first_evaluables).isoformat()
                                        if first_evaluables else None),
        "early_forced_flat_count": early_flats,
        "pairs": sorted(canonical_rows_by_pair),
    }


# --- publication gate --------------------------------------------------------------------- #
def authorized_publication(record, ledger_path, *, authorization=None, scored=False,
                           real_pnl=False) -> dict:
    """Frozen publication gate for family2 records.  Publishes nothing itself
    unless every gate opens; returns a structured verdict.

    * ``authorization`` must equal ``AUTHORIZATION_TOKEN`` -- anything else
      raises :class:`PublicationRefused` (``NO_AUTHORIZATION``) and no byte is
      written.
    * ``scored=False``: a REAL publication is refused
      (``SCORED_FALSE_REFUSE_REAL_PUBLISH``); only a dummy dry-run
      (``real_pnl=False``, per run_contract ``dummy_dry_run_allowed_only_with``)
      is allowed and it writes ZERO bytes (returns the plan only).
    * ``scored=True`` + authorized: a real publication goes through the
      once-only :class:`accounting.AtomicJsonlPublisher`.
    """
    if authorization != AUTHORIZATION_TOKEN:
        raise PublicationRefused(
            "NO_AUTHORIZATION: family2 refuses to publish without the owner "
            "authorization token (A1 hard stop before the first scored cell)")
    if real_pnl and not scored:
        raise PublicationRefused(
            "SCORED_FALSE_REFUSE_REAL_PUBLISH: scored=False refuses a real "
            "publication; only a dummy dry-run (scored=False, real_pnl=False, "
            "zero bytes written) is allowed")
    if not real_pnl:
        return {"mode": "dummy_dry_run", "wrote_bytes": 0,
                "ledger_path": os.fspath(ledger_path), "published_now": 0}
    publisher = ACC.AtomicJsonlPublisher(ledger_path)
    observed_delta, published_now = publisher.publish_once(record)
    return {"mode": "real_publication",
            "ledger_path": os.fspath(ledger_path),
            "observed_delta": observed_delta, "published_now": published_now}
