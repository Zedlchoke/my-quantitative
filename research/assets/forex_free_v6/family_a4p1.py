#!/usr/bin/env python
"""FOREX-FREE-V6 family FXFV6-A4-P1: own-economy CPI reaction-direction drift
(I1 implementation lane, cycle FOREX-FREE-V6).

Implements the SELECTED family EXACTLY as frozen by

  * research/control/forex_free_v6_run/d1/a4_postrelease/proposal_P1.json
    (sha256 329607fda5859fd92c7ce45093c40b99859afc5011d9f76bdd6844953cc5e856),
  * research/control/forex_free_v6_run/selection_freeze.json
    (arms anchor / neighbour / control with 6 frozen arm_config_digests),
  * research/control/forex_free_v6_run/p3_conditioning_clocks_v6.json
    (the ONLY conditioning authority: 246 evidenced CPI clocks, GB 88 /
    CA 105 / AU 23 / NZ 30 in-S0; CA rows carry the v3 TRUE-UTC pins and
    ``available_for_daily_decision_date``).

MECHANISM (frozen law, transcribed from the proposal): on each published
conditioning clock for a pair's own economy, read the market's INITIAL
reaction direction on the pair's DAILY 16:00-NY decision-close series and
hold in that direction:

    D0     = the first CONDITIONABLE decision date of the clock
             (GB/AU DAY precision: the published decision_date, conditionable
             at that date's 16:00-NY decision by the published convention;
             NZ INSTANT: decision_date, gated by the expressed stamp
             preceding that decision instant; CA INSTANT: decision_date when
             available_time_utc precedes the decision instant, otherwise --
             exactly the 3 published boundary_shift rows -- ONLY the
             published next-weekday available_for_daily_decision_date);
    D_prev = immediately preceding weekday decision date;
    R      = ln(close(D0) / close(D_prev));
    side   = sign(R)              (R == 0 exactly -> event skipped, counted);
    entry fill  = close(D1), D1 = next weekday after D0 (FX 24/5 weekday
             convention, no holiday refinement) -- NEVER a same-bar fill;
    exit fill   = close(D1 + k decision sessions) (anchor k=5, neighbour
             k=10); the time exit is issued at the immediately preceding
             decision instant (D1+k-1) so the exit fill is also never
             same-bar.

BINDING FREEZE CONSTRAINT: DAILY closes ONLY (the staged 1day snapshots);
any intraday dependency makes the cell INFEASIBLE (selection_freeze.json
risk_disclosures).  The 4h snapshots are never read by this module.

No print VALUES and no consensus estimates are used or assumed: the
direction signal is the pair's own measured price reaction.

ARMS (selection_freeze.json):

  anchor    every published clock, k=5;
  neighbour identical except k=10 (single differing design axis);
  control   MANDATORY sham calendar: every clock's CONDITIONABLE date
            shifted +7 calendar days (CA boundary rows shift from their
            published available_for_daily_decision_date); the sham's
            D_prev is the previous weekday of the shifted date; same price
            series, same fills, same evidenced semantics, same fold
            contract.  A shifted date coinciding with a real published
            clock is mechanically reported and does NOT alter the sham.

FAIL-CLOSED DISCIPLINE:

  * decisions only where the clocks file evidences availability (P-1): a
    clock NOT published in the clocks file is never conditionable; AU
    documented gaps simply produce no clocks (no inferred availability);
  * a clock whose published stamp contradicts the conditionability
    semantics at implementation time is skipped and counted
    (unavailable_fail_closed), never remapped by inference;
  * every missing decision-series close (D_prev, D0, D1, exit) skips the
    event fail-closed and is counted -- never fill-forwarded;
  * warmup: 5 decision closes of the pair's decision series must exist
    ending at close(D_prev); otherwise warmup_skipped;
  * overlap policy: max ONE open position per pair; a new event on a pair
    with an open position is skipped and counted collision_skipped (no
    stacking, no early exit, no re-entry).  The governor is applied on the
    resolved schedule BEFORE the reaction is evaluated (a collision-skipped
    event never reaches the signal), so the schedule is identical across
    arms up to the frozen single design axis;
  * S0: clock decision_dates must lie inside the clocks authority's own
    S0 window (2018-04-04..2025-07-24, enforced by the loader).  A sham
    SHIFTED date is not a published clock date and carries no S0 cap; its
    trades still fail closed at staged-data end;
  * reconciliation: trades + skips must equal the published per-economy
    clock counts (GB 88 / CA 105 / AU 23 / NZ 30, total 246) or the run
    is BLOCKED;
  * every emitted decision carries the resolved clock tuple (economy,
    decision_date, conditionable_date, available_time_utc, archive_sha256)
    resolvable to a row of the clocks file; the CA boundary remap count is
    reported (frozen sanity gate: exactly 3 published boundary rows).

Fold contract (frozen in the proposal): F1 2018-04-04..2020-12-31,
F2 2021-01-01..2023-03-31, F3 2023-04-01..2025-07-24; trades assigned by
event decision_date D0.  Trades whose hold [entry fill, exit fill] crosses
an internal fold boundary are flagged span_boundary_purged (purged from
drop-one computations; purge window 16 calendar days covers the max 11-session
hold); they are never truncated (the k-session hold IS the mechanism).

Costs, financing and books are driver-owned (exec_driver_v6.py); this
module is decision machinery only and computes no PnL.
"""
from __future__ import annotations

import json
import math
import os
from collections import OrderedDict
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

__all__ = [
    "run_arm", "load_clocks", "load_daily_closes", "DataBlocked",
    "reaction_direction", "resolve_schedule", "ny_decision_stamp",
    "ARM_IDS", "ECONOMY_PAIR", "FOLD_CONTRACT", "INTERNAL_FOLD_STARTS",
]

UTC = timezone.utc
NY_TZ = ZoneInfo("America/New_York")

CYCLE_ID = "FOREX-FREE-V6"
PROPOSAL_ID = "FXFV6-A4-P1"
FAMILY_ID = "FXFV6-A4-P1"

ARM_IDS = {
    "anchor": "anchor_reaction_drift_k5",
    "neighbour": "neighbour_reaction_drift_k10",
    "control": "control_sham_calendar_plus7_k5",
}
K_HOLD = {"anchor": 5, "neighbour": 10, "control": 5}
SHAM_SHIFT_CALENDAR_DAYS = 7

# frozen clocks -> pair map (proposal universe; the four FUNDED economies)
ECONOMY_PAIR = OrderedDict(
    (("GB", "GBPUSD"), ("CA", "USDCAD"), ("AU", "AUDUSD"), ("NZ", "NZDUSD"))
)
PAIR_AREAS = {  # financing attribution (driver bookkeeping input)
    "GBPUSD": ("GB", "US"),
    "USDCAD": ("US", "CA"),
    "AUDUSD": ("AU", "US"),
    "NZDUSD": ("NZ", "US"),
}
ECONOMY_ORDER = ("GB", "CA", "AU", "NZ")

EXPECTED_CLOCK_COUNTS = {"GB": 88, "CA": 105, "AU": 23, "NZ": 30}
TOTAL_CLOCKS_PUBLISHED = 246
WARMUP_DECISION_CLOSES = 5          # closes ending at close(D_prev)
NOTIONAL_USD = 10000.0
PURGE_DAYS = 16                     # covers the max 11-session hold
S0_START = "2018-04-04"
S0_END = "2025-07-24"

FOLD_CONTRACT = (
    {"id": "F1", "start": "2018-04-04", "end": "2020-12-31"},
    {"id": "F2", "start": "2021-01-01", "end": "2023-03-31"},
    {"id": "F3", "start": "2023-04-01", "end": "2025-07-24"},
)
INTERNAL_FOLD_STARTS = ("2021-01-01", "2023-04-01")

DECISION_CLOCK = "daily 16:00 America/New_York (DST-correct via zoneinfo)"
ALPHA_DEFINITION = "per_trade_expectancy_difference_v1"
FINANCING_FORMULA_ID = "fx5_day_start_asof_policy_rate_diff_v5ledger_v1"

REASON_UNAVAILABLE = "unavailable_fail_closed"
REASON_WARMUP = "warmup_skipped"
REASON_ZERO = "zero_signal_skipped"
REASON_COLLISION = "collision_skipped"
REASON_MISSING_PREV = "missing_close_d_prev"
REASON_MISSING_D0 = "missing_close_d0"
REASON_MISSING_FILL = "missing_close_d1"
REASON_MISSING_EXIT = "missing_close_exit"
REASON_END_OF_DATA = "end_of_data_no_exit"

ALL_SKIPPED_REASONS = (
    REASON_UNAVAILABLE, REASON_WARMUP, REASON_ZERO, REASON_COLLISION,
    REASON_MISSING_PREV, REASON_MISSING_D0, REASON_MISSING_FILL,
    REASON_MISSING_EXIT, REASON_END_OF_DATA,
)


class DataBlocked(RuntimeError):
    """A required evidenced input is missing/malformed; fail closed."""

    reason = "BLOCKED_DATA"

    def __init__(self, detail: str) -> None:
        super().__init__(f"BLOCKED_DATA: {detail}")
        self.detail = detail


# ------------------------------------------------------------------ #
# conditioning clocks (the ONLY conditioning authority)               #
# ------------------------------------------------------------------ #
def _parse_utc(raw, what: str) -> datetime:
    if not isinstance(raw, str) or not raw:
        raise DataBlocked(f"{what}: missing UTC instant")
    try:
        t = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DataBlocked(f"{what}: unparsable UTC instant {raw!r}") from exc
    if t.tzinfo is None:
        raise DataBlocked(f"{what}: timezone-naive instant {raw!r}")
    return t.astimezone(UTC)


def _iso(t: datetime) -> str:
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def ny_decision_stamp(day: date) -> datetime:
    """UTC instant of the 16:00 America/New_York decision of ``day``
    (20:00Z EDT / 21:00Z EST via zoneinfo -- DST-aware, never fixed)."""
    return datetime(day.year, day.month, day.day, 16, 0, tzinfo=NY_TZ).astimezone(UTC)


def load_clocks(path) -> list:
    """Load + verify the p3 conditioning clocks (fail closed).

    Every row must carry decision_date, available_time_utc, precision,
    reference_period and a 64-hex archive_sha256; the economy must be one
    of the four funded economies; the decision_date must lie inside the
    authority's own S0 window; (economy, decision_date) unique; per-economy
    and total counts must equal BOTH the file header and the frozen
    published counts (GB 88 / CA 105 / AU 23 / NZ 30 = 246)."""
    if not isinstance(path, str) or not os.path.exists(path):
        raise DataBlocked(f"conditioning clocks file not found: {path!r}")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, ValueError) as exc:
        raise DataBlocked(f"unreadable conditioning clocks file {path}: {exc}")
    clocks_raw = payload.get("clocks") if isinstance(payload, dict) else None
    if not isinstance(clocks_raw, list) or not clocks_raw:
        raise DataBlocked("conditioning clocks file carries no clocks list")
    header = payload.get("per_economy_in_S0")
    if not isinstance(header, dict):
        raise DataBlocked("clocks file carries no per_economy_in_S0 header")
    s0 = payload.get("S0_window")
    if not isinstance(s0, dict) or "start" not in s0 or "end" not in s0:
        raise DataBlocked("clocks file carries no S0_window")

    clocks = []
    seen = set()
    counts = {e: 0 for e in ECONOMY_ORDER}
    for i, row in enumerate(clocks_raw):
        if not isinstance(row, dict):
            raise DataBlocked(f"clock row {i}: not a mapping")
        economy = row.get("economy")
        if economy not in ECONOMY_PAIR:
            raise DataBlocked(f"clock row {i}: economy {economy!r} is not a "
                              "funded economy of this family")
        decision_date = row.get("decision_date")
        try:
            dd = date.fromisoformat(str(decision_date))
        except (TypeError, ValueError) as exc:
            raise DataBlocked(f"clock row {i}: unparsable decision_date "
                              f"{decision_date!r}") from exc
        if not (date.fromisoformat(str(s0["start"])) <= dd
                <= date.fromisoformat(str(s0["end"]))):
            raise DataBlocked(f"clock row {i}: decision_date {decision_date} "
                              "outside the authority's own S0 window")
        available = _parse_utc(row.get("available_time_utc"),
                               f"clock row {i} ({economy} {decision_date})")
        precision = row.get("precision")
        if not isinstance(precision, str) or not precision:
            raise DataBlocked(f"clock row {i}: missing precision")
        reference = row.get("reference_period")
        if not isinstance(reference, str) or not reference:
            raise DataBlocked(f"clock row {i}: missing reference_period")
        sha = row.get("archive_sha256")
        if (not isinstance(sha, str) or len(sha) != 64
                or any(ch not in "0123456789abcdef" for ch in sha.lower())):
            raise DataBlocked(f"clock row {i}: archive_sha256 missing or not "
                              f"64-hex: {sha!r}")
        key = (economy, str(decision_date))
        if key in seen:
            raise DataBlocked(f"clock row {i}: duplicate (economy, "
                              f"decision_date) {key}")
        seen.add(key)
        counts[economy] += 1
        clocks.append({
            "economy": economy,
            "decision_date": str(decision_date),
            "available": available,
            "precision": precision,
            "reference_period": reference,
            "archive_sha256": sha,
            "available_for_daily_decision_date":
                row.get("available_for_daily_decision_date"),
        })
    for economy in ECONOMY_ORDER:
        if counts[economy] != header.get(economy) \
                or counts[economy] != EXPECTED_CLOCK_COUNTS[economy]:
            raise DataBlocked(
                f"clock count mismatch for {economy}: file has "
                f"{counts[economy]}, header {header.get(economy)!r}, frozen "
                f"authority {EXPECTED_CLOCK_COUNTS[economy]}")
    if len(clocks) != TOTAL_CLOCKS_PUBLISHED:
        raise DataBlocked(f"total clock count mismatch: {len(clocks)} != "
                          f"{TOTAL_CLOCKS_PUBLISHED}")
    clocks.sort(key=lambda c: (c["available"], c["economy"],
                               c["decision_date"]))
    return clocks


# ------------------------------------------------------------------ #
# staged DAILY decision series (1day snapshots ONLY; the freeze       #
# forbids any intraday dependency)                                    #
# ------------------------------------------------------------------ #
def load_daily_closes(price_dir: str, pair: str) -> dict:
    """One pair's weekday decision-close series {date: close} from the
    staged 1day snapshot (``{PAIR}_1day_*.json``; daily bar stamped with
    its decision date).  Weekend stamps are not decision days (published
    FX 24/5 weekday convention) and are excluded.  Malformed files,
    conflicting duplicate dates and non-positive/non-finite closes fail
    closed.  The 4h snapshots are never read."""
    sym = pair.replace("/", "")
    paths = sorted(p for p in os.listdir(price_dir)
                   if p.startswith(f"{sym}_1day_") and p.endswith(".json")) \
        if os.path.isdir(price_dir) else []
    if not paths:
        raise DataBlocked(f"no 1day staged snapshot for {pair} under {price_dir}")
    rows = {}
    for name in paths:
        full = os.path.join(price_dir, name)
        try:
            with open(full, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, ValueError) as exc:
            raise DataBlocked(f"unreadable 1day snapshot {full}: {exc}")
        if isinstance(payload, dict) and payload.get("status") == "error":
            continue  # provider no-data window (evidence of a gap, no bars)
        values = payload.get("values") if isinstance(payload, dict) else None
        if not isinstance(values, list):
            raise DataBlocked(f"1day snapshot {full} carries no values list")
        for row in values:
            if not isinstance(row, dict):
                raise DataBlocked(f"1day snapshot {full} malformed row")
            try:
                day = date.fromisoformat(str(row["datetime"]))
                close = float(row["close"])
            except (KeyError, TypeError, ValueError) as exc:
                raise DataBlocked(f"1day snapshot {full}: unparseable bar "
                                  f"({exc})")
            if day.weekday() >= 5:
                continue  # weekend stamp: not a weekday decision close
            if not (math.isfinite(close) and close > 0):
                raise DataBlocked(f"1day snapshot {full}: non-positive close "
                                  f"at {day.isoformat()}")
            if day in rows and rows[day] != close:
                raise DataBlocked(f"conflicting duplicate daily close at "
                                  f"{day.isoformat()} in {full}")
            rows[day] = close
    if not rows:
        raise DataBlocked(f"1day snapshot for {pair} holds no weekday closes")
    return rows


# ------------------------------------------------------------------ #
# the frozen reaction law                                             #
# ------------------------------------------------------------------ #
def reaction_direction(close_d0: float, close_prev: float) -> float:
    """R = ln(close(D0)/close(D_prev)) to float precision."""
    return math.log(close_d0 / close_prev)


def direction_of(r: float) -> int:
    """side = sign(R); an EXACT zero is NO_TRADE (fail-closed)."""
    if r > 0.0:
        return 1
    if r < 0.0:
        return -1
    return 0


def next_weekday(day: date) -> date:
    """Next weekday (FX 24/5 convention; no holiday refinement -- the
    published next_trading_day_rule)."""
    day = day + timedelta(days=1)
    while day.weekday() >= 5:
        day += timedelta(days=1)
    return day


def prev_weekday(day: date) -> date:
    day = day - timedelta(days=1)
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return day


def conditionable_date(clock: dict):
    """(conditionable decision date, is_ca_boundary_remap) under the frozen
    availability semantics, or (None, False) when the published stamp
    contradicts them (skip fail-closed).

      GB/AU (DAY precision, 23:59:59Z end-of-day bound): the decision_date,
        conditionable at that date's 16:00-NY decision by construction;
      NZ (INSTANT, conservative flat +12:00 LATER bound): decision_date,
        gated on the expressed stamp preceding that decision instant;
      CA (INSTANT): decision_date when available_time_utc precedes the
        decision instant; otherwise ONLY the published
        available_for_daily_decision_date (exactly the 3 published
        boundary_shift rows); a post-decision-instant CA stamp with no
        later afdd contradicts the semantics -> fail closed.
    """
    economy = clock["economy"]
    dd = date.fromisoformat(clock["decision_date"])
    precision = clock["precision"]
    if economy in ("GB", "AU"):
        if not precision.startswith("DAY"):
            return None, False  # contradicts the published DAY convention
        return dd, False
    inst = clock["available"]
    decision_inst = ny_decision_stamp(dd)
    if economy == "NZ":
        if inst > decision_inst:
            return None, False
        return dd, False
    # CA: INSTANT with the P0b v3 TRUE-UTC pins
    if inst <= decision_inst:
        return dd, False
    afdd = clock.get("available_for_daily_decision_date")
    if not isinstance(afdd, str):
        return None, False
    afdd_day = date.fromisoformat(afdd)
    if afdd_day <= dd:
        return None, False  # boundary stamp that does not move forward:
                            # contradicts the published boundary semantics
    return afdd_day, True


def fold_of_date(day: date):
    """Fold id by frozen contract, or None before F1 (warmup region)."""
    for f in FOLD_CONTRACT:
        if date.fromisoformat(f["start"]) <= day <= date.fromisoformat(f["end"]):
            return f["id"]
    return None


def spans_internal_boundary(entry_day: date, exit_day: date) -> bool:
    """True when the hold [entry fill, exit fill] crosses an internal fold
    boundary (the drop-one purge rule; PURGE_DAYS=16 covers the max
    11-session hold)."""
    for b in INTERNAL_FOLD_STARTS:
        bd = date.fromisoformat(b)
        if entry_day < bd <= exit_day:
            return True
    return False


# ------------------------------------------------------------------ #
# schedule resolution (per clock, fail-closed voids)                  #
# ------------------------------------------------------------------ #
def resolve_schedule(cond_day: date, k: int, series: dict, series_days: list):
    """(reason, leg) for one conditionable date over the pair's weekday
    decision series.

    leg = {d0, d_prev, d1, exit_day, entry_price, exit_price} with
    D_prev the immediately preceding weekday, D1 the next weekday and the
    exit the k-th decision session after D1.  Any missing close voids the
    event (never fill-forwarded); the exit decision is issued at
    D1+k-1 so the exit fill is never same-bar.
    """
    d_prev = prev_weekday(cond_day)
    if d_prev not in series:
        return REASON_MISSING_PREV, None
    # warmup: WARMUP_DECISION_CLOSES closes ENDING at close(D_prev)
    prior = [d for d in series_days if d < d_prev]
    if len(prior) < WARMUP_DECISION_CLOSES - 1:
        return REASON_WARMUP, None
    if cond_day not in series:
        return REASON_MISSING_D0, None
    d1 = next_weekday(cond_day)
    if d1 not in series:
        return REASON_MISSING_FILL, None
    i1 = series_days.index(d1)
    iexit = i1 + k
    if iexit >= len(series_days):
        return REASON_END_OF_DATA, None
    exit_day = series_days[iexit]
    return None, {
        "d0": cond_day, "d_prev": d_prev, "d1": d1, "exit_day": exit_day,
        "entry_price": series[d1], "exit_price": series[exit_day],
        "exit_decision_day": series_days[iexit - 1],
    }


# ------------------------------------------------------------------ #
# family API entry point                                              #
# ------------------------------------------------------------------ #
def run_arm(arm: str, data_paths: dict):
    """Frozen family API (V6 driver runner contract).

    Returns {"decisions": [...], "meta": {...}}.  No PnL is computed here.

    Decisions are emitted AFTER the per-pair collision governor walk (the
    schedule is arm-invariant up to the frozen single design axis) and the
    reaction evaluation (R == 0 exactly -> skipped, counted).
    """
    arm_id = ARM_IDS.get(arm)
    if arm_id is None:
        raise ValueError(f"arm must be one of {sorted(ARM_IDS)}, got {arm!r}")
    if not isinstance(data_paths, dict):
        raise DataBlocked("data_paths must be a mapping")
    for key in ("price_1day_dir", "conditioning_clocks"):
        if not isinstance(data_paths.get(key), str):
            raise DataBlocked(f"data_paths is missing the {key!r} path")

    clocks = load_clocks(data_paths["conditioning_clocks"])
    clocks_by_economy = {e: [c for c in clocks if c["economy"] == e]
                         for e in ECONOMY_ORDER}
    k = K_HOLD[arm]
    shift = (timedelta(days=SHAM_SHIFT_CALENDAR_DAYS) if arm == "control"
             else timedelta(days=0))

    skipped = {reason: 0 for reason in ALL_SKIPPED_REASONS}
    per_economy = {}
    schedule = []      # resolved legs (pre-governor), with clock tuples
    boundary_schedule = 0
    boundary_events = 0

    for economy in ECONOMY_ORDER:
        pair = ECONOMY_PAIR[economy]
        series = load_daily_closes(data_paths["price_1day_dir"], pair)
        series_days = sorted(series)
        counts = {reason: 0 for reason in ALL_SKIPPED_REASONS}
        counts["published_clocks"] = len(clocks_by_economy[economy])
        resolved = []
        for clock in clocks_by_economy[economy]:
            cond, is_remap = conditionable_date(clock)
            if cond is None:
                counts[REASON_UNAVAILABLE] += 1
                skipped[REASON_UNAVAILABLE] += 1
                continue
            if is_remap:
                counts["ca_boundary_remap_events"] = \
                    counts.get("ca_boundary_remap_events", 0) + 1
                boundary_events += 1
            target = cond + shift  # control: the shifted CONDITIONABLE date
            reason, leg = resolve_schedule(target, k, series, series_days)
            if reason is not None:
                counts[reason] += 1
                skipped[reason] += 1
                continue
            leg = dict(leg)
            leg["economy"] = economy
            leg["pair"] = pair
            leg["clock"] = clock
            # the date the arm conditions on (the +7d shifted date for the
            # sham control) plus the published unshifted value
            leg["conditionable_date"] = target
            leg["published_conditionable_date"] = cond
            leg["is_ca_boundary_remap"] = bool(is_remap)
            leg["sham_shifted"] = arm == "control"
            resolved.append(leg)
            if is_remap:
                counts["ca_boundary_remap_in_schedule"] = \
                    counts.get("ca_boundary_remap_in_schedule", 0) + 1
                boundary_schedule += 1        # collision governor: max one open position per pair, chronological
        # by the event's D0 decision instant (an event on a pair with an
        # open position is skipped and counted; no stacking, no re-entry)
        resolved.sort(key=lambda l: (l["d0"], l["clock"]["decision_date"]))
        open_exit = None
        for leg in resolved:
            if open_exit is not None and leg["d0"] < open_exit:
                counts[REASON_COLLISION] += 1
                skipped[REASON_COLLISION] += 1
                continue
            close_d0 = series[leg["d0"]]
            close_prev = series[leg["d_prev"]]
            r = reaction_direction(close_d0, close_prev)
            side = direction_of(r)
            if side == 0:
                counts[REASON_ZERO] += 1
                skipped[REASON_ZERO] += 1
                continue
            leg["r"] = r
            leg["abs_r"] = abs(r)
            leg["side"] = side
            open_exit = leg["exit_day"]
            schedule.append(leg)
        counts["trades"] = sum(1 for l in schedule if l["economy"] == economy)
        counts["ca_boundary_remap_qualified"] = sum(
            1 for l in schedule
            if l["economy"] == economy and l["is_ca_boundary_remap"])
        # frozen reconciliation: trades + skips == published clocks
        n_skips = sum(v for kk, v in counts.items()
                      if kk in ALL_SKIPPED_REASONS)
        if counts["trades"] + n_skips != counts["published_clocks"]:
            raise DataBlocked(
                f"{economy}: schedule does not reconcile: trades "
                f"{counts['trades']} + skips {n_skips} != published clocks "
                f"{counts['published_clocks']}")
        per_economy[economy] = counts

    decisions = []
    for leg in schedule:
        d0 = leg["d0"]
        entry_day, exit_day = leg["d1"], leg["exit_day"]
        decisions.append({
            "decision_id": (
                f"{PROPOSAL_ID}-{arm}-{leg['pair']}-"
                f"{leg['clock']['decision_date']}-{d0.isoformat()}"),
            "pair": leg["pair"],
            "side": leg["side"],
            "decision_ts": _iso(ny_decision_stamp(d0)),
            "notional_usd": NOTIONAL_USD,
            "entry_ts": _iso(ny_decision_stamp(entry_day)),
            "entry_price": leg["entry_price"],
            "exit_ts": _iso(ny_decision_stamp(exit_day)),
            "exit_price": leg["exit_price"],
            "exit_decision_ts": _iso(ny_decision_stamp(leg["exit_decision_day"])),
            "r_value": leg["r"],
            "abs_r_diag": leg["abs_r"],
            "force_flat": False,   # time exit; never truncated in this family
            "span_boundary_purged": spans_internal_boundary(entry_day, exit_day),
            "fold": fold_of_date(d0),
            "economy": leg["economy"],
            "clock_decision_date": leg["clock"]["decision_date"],
            "conditionable_date": leg["conditionable_date"].isoformat(),
            "published_conditionable_date":
                leg["published_conditionable_date"].isoformat(),
            "available_time_utc": _iso(leg["clock"]["available"]),
            "archive_sha256": leg["clock"]["archive_sha256"],
            "ca_boundary_remap": leg["is_ca_boundary_remap"],
            "sham_shifted": leg["sham_shifted"],
            "k_hold": k,
        })

    total_trades = len(decisions)
    total_skips = sum(skipped.values())
    if total_trades + total_skips != TOTAL_CLOCKS_PUBLISHED:
        raise DataBlocked(
            f"arm {arm}: pooled schedule does not reconcile: trades "
            f"{total_trades} + skips {total_skips} != "
            f"{TOTAL_CLOCKS_PUBLISHED} published clocks")
    # frozen sanity gate CA_BOUNDARY_COUNT: exactly the 3 published CA
    # boundary_shift rows may use next-weekday conditionability (the remap
    # rule fires exactly 3 times -- over/under-firing is an implementation
    # BUG -> BLOCKED, never silently absorbed).  Whether a remapped event
    # then survives the fail-closed skips is reported, never forced.
    if boundary_events != 3:
        raise DataBlocked(
            f"arm {arm}: CA_BOUNDARY_COUNT violated: next-weekday "
            f"conditionability fired {boundary_events} times, frozen "
            "authority says exactly 3")

    meta = {
        "proposal_id": PROPOSAL_ID,
        "family_id": FAMILY_ID,
        "cycle_id": CYCLE_ID,
        "arm": arm,
        "arm_id": arm_id,
        "decision_clock": DECISION_CLOCK,
        "alpha_definition": ALPHA_DEFINITION,
        "financing_formula_id": FINANCING_FORMULA_ID,
        "granularity": "daily closes ONLY (1day snapshots; freeze binding "
                       "constraint: any intraday dependency is forbidden)",
        "frozen_constants": {
            "k_hold": k,
            "sham_shift_calendar_days": (SHAM_SHIFT_CALENDAR_DAYS
                                         if arm == "control" else 0),
            "warmup_decision_closes": WARMUP_DECISION_CLOSES,
            "notional_usd_unit": NOTIONAL_USD,
            "clocks_pair_map": dict(ECONOMY_PAIR),
            "purge_days": PURGE_DAYS,
            "s0_window": {"start": S0_START, "end": S0_END},
        },
        "fold_contract": [dict(f) for f in FOLD_CONTRACT],
        "economy_clock_counts": {e: len(clocks_by_economy[e])
                                 for e in ECONOMY_ORDER},
        "per_economy_schedule": per_economy,
        "skipped_counts": {k_: v for k_, v in sorted(skipped.items())},
        "ca_boundary_remap_published": 3,
        "ca_boundary_remap_events": boundary_events,
        "ca_boundary_remap_in_schedule": boundary_schedule,
        "ca_boundary_remap_qualified": sum(
            1 for d in decisions if d["ca_boundary_remap"]),
        "n_decisions": total_trades,
    }
    return {"decisions": decisions, "meta": meta}
