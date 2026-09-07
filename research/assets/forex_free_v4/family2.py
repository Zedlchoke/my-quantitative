"""FOREX-FREE-V4 family2: FXFV4-A6-P2 -- policy-change underreaction drift
with hike/cut asymmetry: an evidenced-availability event study on the daily
16:00-NY decision clock.

Binding spec: research/proposals/forex_free_v4/d1-a6-proposals/
PROPOSAL_FXFV4-A6-P2.json (SELECTED family2, cycle FOREX-FREE-V4), as
qualified by the BINDING implementation directives in
research/control/forex_free_v4_run/selection_freeze.json
(implementation_directives_from_audits) and the A9-F feasibility findings
(research/audits/forex_free_v4/a9_f_feasibility_v4.json, FXFV4-A6-P2).

This module mirrors the inherited V3 family-module discovery pattern
(research/assets/forex_free_v3/exec_driver.py: ``family_id=module.path``;
the module exposes the frozen family API contract)::

    run_arm(arm, data_paths, macro_reader=None, freeze_token=None)
        -> {"decisions": [...], "financing_events": [...], "meta": {...}}

No V3 frozen file is modified.  Booking goes through the inherited P1
accounting kernel (research.assets.forex_free_v3.accounting, imported
READ-ONLY); cell records mirror the V3 scored-runner record structure and
add the frozen margin-to-fail fields per Stage-A gate.

Arms (three frozen scored arms per the spec, plus the packet's benchmark
  treatment):
  "anchor"                  the frozen mechanism law: availability-gated
                            RATE_CHANGE events of the DEDUPED v2 ledger,
                            frozen area->pair direction map, H = 10 NY-days
                            for every event, next-session fills, force-flat
                            folds, dual book.
  "neighbour"               byte-identical to the anchor EXCEPT the holding
                            law: H_hike = 10 NY-days, H_cut = 3 NY-days
                            (hike/cut classified by the row's delta sign).
  "causal_negative_control" (driver shorthand "control"): byte-identical to
                            the anchor except each area's events drive a
                            DIFFERENT area's pair under the packet's FROZEN
                            sham derangement mapping (arms.control.
                            sham_derangement_frozen.mapping, implemented
                            verbatim; see SHAM_AREA).
  "benchmark_treatment"     the frozen incremental benchmark
                            (bench_schedule_id ``FXFV4-A6-P2-bench``): the
                            anchor law with every event's availability
                            instant shifted +180 calendar days LATER (a
                            round constant fixed ex ante; never tuned).
                            Never a scored cell of its own.

Frozen law (packet mechanism / pit_observable / entry_rules / exit_rules,
implemented here verbatim):

* Events are the RATE_CHANGE rows of the DEDUPED v2 announcement ledger
  (last-row-wins by (area, effective_date) over the raw 220-row file; the
  61 dropped rows are AVAILABILITY_UNEVIDENCED -> EVIDENCED upgrades) with
  delta = new_value - old_value != 0.
* Eligibility (A1 adjudication A-2, BINDING:
  research/control/forex_free_v4_run/a1_ambiguity_adjudication.json): the
  eligibility instant is the ledger row's PRECOMPUTED
  ``first_readable_decision_utc`` field (first 16:00-NY decision at/after
  max(operative availability, effective) -- the frozen program PIT
  invariant: a decision never reads a row whose effective_time_utc > T).
  Decision instant T = the first completed daily 16:00 America/New_York
  flat bar whose completion instant satisfies T >=
  first_readable_decision_utc (bar stamps 20:00Z EDT / 21:00Z EST via
  zoneinfo, DST-aware).  A row with a null ``first_readable_decision_utc``
  fails closed (MISSING_AVAILABLE_TIME_EVIDENCE) and is never read.  The
  deterministic tie-break still uses the row's operative availability
  instant (``announcement.operative_available_time_utc``), falling back to
  the eligibility instant when absent.  Financing vintages keep BOTH gates
  (availability AND effectiveness) exactly as before.  Events whose first
  decision instant falls before the frozen cutoff 2020-02-11 (snapshot
  start + one session + lag) are NO_EVAL fail-closed, never backfilled.
* Direction: for A != US, P(A) is the unique authorized pair containing A
  as the non-USD leg; side = +1 (long base) if delta > 0 and A is the
  pair's BASE currency, -1 if delta > 0 and A is the QUOTE currency,
  flipped for delta < 0.  For A = US the event drives ALL 7 pairs with the
  long-USD map on a hike: EUR/USD -1, GBP/USD -1, AUD/USD -1, NZD/USD -1,
  USD/JPY +1, USD/CHF +1, USD/CAD +1 (flipped on a cut).
* Entry at the OPEN of the next session's 16:00-NY bar strictly after T
  (one-event lag); the decision->fill gap must stay within the frozen
  4-day next-session constraint, else the signal fails closed to NO_TRADE.
  A missing next-session bar voids the signal.  Never same-bar fills,
  never fill-forward.
* Hold: anchor exactly 10 completed NY-days for every event (exit at the
  open of the 10th existing 16:00-NY bar after the entry bar); neighbour
  10 for hikes / 3 for cuts.  No targets, no stops, no refresh while the
  pair holds a position (ignored events are NO_TRADE, never deferred).
  Deterministic tie-break: events mapping to the same pair at the same
  decision instant resolve to the earlier availability instant.
* Missing exit bar (scheduled exit beyond the snapshot): earliest-
  scheduled exit at the latest existing 16:00-NY bar before the scheduled
  instant, never fill-forward; no earlier bar => the trade is voided.
* Force-flat: an open position exits at the OPEN of the last decision
  day's 16:00-NY bar before an internal fold boundary (2022-05-01,
  2024-07-01); an entry whose fill would land on that bar is suppressed.
  No position crosses a fold boundary.
* Governor: max 1 position per pair, max 1 entry per pair per NY-day
  (structural: one decision instant per pair per NY-day).
* Financing (frozen formula, verbatim): financing_adjusted_pnl =
  price_only_pnl + sign * notional_usd * (r_base - r_quote) *
  holding_days/365, accrued per calendar day at the day-start as-of
  policy-rate differential from the evidenced vintages (rows eligible only
  when available_time_utc <= the accrual instant; never eligible on their
  own effective date).  The vintages are reconstructed from the SAME
  deduped ledger (piecewise-constant policy-rate steps: BASELINE_LEVEL
  values plus every RATE_CHANGE step), so availability and effectiveness
  gating are the pinned v4 evidenced-vintages semantics exactly as the
  ledger carries them.  Adopted values are percent-per-annum; converted
  to annualized decimals (/100) exactly once at the family boundary.
  DISCLOSED APPROXIMATION: policy rates are unsecured official rates, NOT
  swap/OIS-implied rollover (HISTORICAL_ROLLOVER_FINANCING
  UNAVAILABLE_FAIL_CLOSED).

Determinism: same inputs -> byte-identical output (sorted iteration only,
no wall clock, no runtime randomness).  Fail-closed everywhere: missing
bars/ledger fields are recorded skips or BLOCKED_DATA, never fabricated,
never fill-forwarded.  Price input: the authorized H1 research snapshot
(``data_paths["h1_dir"]``), the ONLY price source.  No PnL is computed on
real data anywhere in this lane; :func:`schedule_counts` exposes
schedule-only counting for feasibility replays.
"""
from __future__ import annotations

import bisect
import glob
import json
import math
import os
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

# Inherited P1 accounting kernel (READ-ONLY reuse; never modified) and the
# frozen V3 decision-stream validator helpers (READ-ONLY reuse).
from research.assets.forex_free_v3 import accounting
from research.assets.forex_free_v3 import scored_runner as _kernel

__all__ = [
    "PROPOSAL_ID",
    "PAIR_UNIVERSE",
    "PAIR_AREAS",
    "AREA_ORDER",
    "AREA_OWN_PAIR",
    "US_HIKE_SIDE",
    "SHAM_AREA",
    "ANCHOR_HOLD_NY_DAYS",
    "NEIGHBOUR_CUT_HOLD_NY_DAYS",
    "BENCHMARK_LAG_DAYS",
    "BENCH_ARM",
    "NOTIONAL_USD",
    "FINANCING_FORMULA_ID",
    "DataBlocked",
    "run_arm",
    "schedule_counts",
    "load_ledger_rows",
    "dedupe_ledger_rows",
    "extract_events",
    "mapped_directions",
    "hold_ny_days",
    "fold_of",
    "assemble_cell_record",
    "margin_to_fail",
    "stage_a_gates",
    "family_control_gate",
]

PROPOSAL_ID = "FXFV4-A6-P2"

NY_TZ = ZoneInfo("America/New_York")
UTC = timezone.utc

PAIR_UNIVERSE = ("EUR/USD", "GBP/USD", "AUD/USD", "NZD/USD",
                 "USD/JPY", "USD/CHF", "USD/CAD")
# (base_area, quote_area) of each authorized pair (inherited V3 convention).
PAIR_AREAS = {
    "EUR/USD": ("EMU", "US"),
    "GBP/USD": ("GB", "US"),
    "AUD/USD": ("AU", "US"),
    "NZD/USD": ("NZ", "US"),
    "USD/JPY": ("US", "JP"),
    "USD/CHF": ("US", "CH"),
    "USD/CAD": ("US", "CA"),
}
# The 8 BIS WS_CBPOL areas backing the 7 pairs, in the packet's frozen
# control-derangement order (arms.control.sham_derangement_frozen.area_order).
AREA_ORDER = ("US", "EMU", "GB", "JP", "CH", "CA", "AU", "NZ")
# Non-US area -> its unique authorized pair (the packet's frozen map:
# EMU->EUR/USD, GB->GBP/USD, AU->AUD/USD, NZ->NZD/USD, JP->USD/JPY,
# CH->USD/CHF, CA->USD/CAD).
AREA_OWN_PAIR = {"EMU": "EUR/USD", "GB": "GBP/USD", "AU": "AUD/USD",
                 "NZ": "NZD/USD", "JP": "USD/JPY", "CH": "USD/CHF",
                 "CA": "USD/CAD"}
# Long-USD map on a US HIKE (packet mechanism, frozen verbatim); a cut
# flips every sign.
US_HIKE_SIDE = {"EUR/USD": -1, "GBP/USD": -1, "AUD/USD": -1, "NZD/USD": -1,
                "USD/JPY": 1, "USD/CHF": 1, "USD/CAD": 1}
# Control sham derangement, implemented as the packet's EXACT mapping table
# (arms.control.sham_derangement_frozen.mapping, verbatim):
#   US drives USD/CHF, EMU drives USD/CAD, GB drives AUD/USD,
#   JP drives NZD/USD, CH drives all 7 (long-USD map), CA drives EUR/USD,
#   AU drives GBP/USD, NZ drives USD/JPY.
# RECORDED DISCREPANCY (research/assets/forex_free_v4/AMBIGUITIES.md): the
# packet's rule sentence "sham(X) = area_order[(index(X)+3) mod 8]" yields
# US->JP, inconsistent with its own mapping table (US->CH, i.e. a +4
# rotation).  The mapping table governs here (it is the exact frozen
# mapping the lane directive cites, and the A9-F control_runnability note
# uses it: "US 22x7 -> USD/CHF only; CH 11 -> all 7").
SHAM_AREA = {"US": "CH", "EMU": "CA", "GB": "AU", "JP": "NZ",
             "CH": "US", "CA": "EMU", "AU": "GB", "NZ": "JP"}

# Frozen single-value constants (proposal single_frozen_parameter_set; the
# packet declares no_parameter_grid: exactly one value per constant).
ANCHOR_HOLD_NY_DAYS = 10
NEIGHBOUR_CUT_HOLD_NY_DAYS = 3
BENCHMARK_LAG_DAYS = 180  # +180 calendar days, frozen ex ante, never tuned
BENCH_ARM = "benchmark_treatment"
NOTIONAL_USD = 10000
NO_EVAL_CUTOFF_UTC = datetime(2020, 2, 11, 0, 0, 0, tzinfo=UTC)
MAX_FILL_LAG_DAYS = 4  # frozen next-session validator allowance

# Fold grid: the frozen kernel grid (scored_runner FOLD_BOUNDARIES of the
# inherited runner; binding directive "fold grid is the frozen kernel grid").
FOLD_BOUNDARIES = ("2020-03-01T00:00:00+00:00", "2022-05-01T00:00:00+00:00",
                   "2024-07-01T00:00:00+00:00", "2026-09-02T23:59:59+00:00")
INTERNAL_BOUNDARIES = (FOLD_BOUNDARIES[1], FOLD_BOUNDARIES[2])
PURGE_DAYS = 14

# Frozen Stage-A gate constants (inherited V3 frozen set, quoted verbatim
# from the kernel the packet inherits; margin-to-fail machinery is frozen
# at implementation per the binding directive).
MIN_EXPECTANCY = 0.0
MIN_PF = 1.10
MIN_POSITIVE_FOLDS = 2          # of 3 populated
MIN_FOLD_PF = 0.80
FOLD_POPULATED_MIN_TRADES = 30
MDD_CEILING_USD = 2500.0
MAX_POS_FOLD_SHARE = 0.50
MAX_PAIR_POS_SHARE = 0.40
STRESS_TIERS = (1.5, 2.0)
STRESS_MIN_PF = 1.00
DROPOUT_SCENARIOS = 8
DROPOUT_MIN_SURVIVAL = 6
USD_CORR_CEILING = 0.30
USD_DIAG_MIN_DAYS = 60
MIN_DECISIONS_PER_ARM = 40
CONTROL_REJECT_PF = 1.10        # preregistered control non-reproduction rule
BASE_TIER = 1.0

FINANCING_FORMULA_ID = "V4_FROZEN_POLICY_EVENT_DRIFT"
FINANCING_FORMULA_VERBATIM = (
    "financing_adjusted_pnl = price_only_pnl + sign * notional_usd * "
    "(r_base - r_quote) * holding_days/365, accrued per calendar day at the "
    "day-start as-of policy-rate differential from the evidenced vintages "
    "(rows eligible only when available_time_utc <= the accrual instant; "
    "never eligible on their own effective date)")
FINANCING_APPROXIMATION = (
    "policy rates are unsecured official rates, NOT swap/OIS-implied "
    "rollover; disclosed ex ante (HISTORICAL_ROLLOVER_FINANCING "
    "UNAVAILABLE_FAIL_CLOSED)")
# Adopted BIS WS_CBPOL values are percent-per-annum; converted to
# annualized decimals exactly once at the family financing boundary.
PERCENT_PER_ANNUM_TO_DECIMAL = 100.0

_ARM_IDS = {
    "anchor": "anchor",
    "neighbour": "neighbour",
    "control": "causal_negative_control",
    "causal_negative_control": "causal_negative_control",
    "benchmark_treatment": "bench",
}
_ARM_SHORT = {"anchor": "AN", "neighbour": "NE",
              "causal_negative_control": "CT", "bench": "BN"}
_META_ARM = {"anchor": "anchor", "neighbour": "neigh",
             "causal_negative_control": "ctrl", "bench": "bench"}

BLOCKED_DATA = "BLOCKED_DATA"


class DataBlocked(RuntimeError):
    """A required input is missing/malformed; the run fails closed."""

    reason = BLOCKED_DATA

    def __init__(self, detail: str) -> None:
        super().__init__(f"{BLOCKED_DATA}: {detail}")
        self.detail = detail


# ------------------------------------------------------------------ #
# deduped v2 announcement ledger (availability evidence)              #
# ------------------------------------------------------------------ #
def _parse_utc(raw, what: str) -> datetime:
    """Parse a UTC ISO stamp ('...Z' or explicit offset); fail closed."""
    if raw is None:
        raise DataBlocked(f"{what} is missing (fail closed)")
    try:
        t = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError as exc:
        raise DataBlocked(f"{what} is not an ISO-8601 instant: {raw!r}") from exc
    if t.tzinfo is None:
        raise DataBlocked(f"{what} is timezone-naive: {raw!r}")
    return t.astimezone(UTC)


def load_ledger_rows(path: str) -> list:
    """Read the pinned v2 announcement ledger jsonl; fail closed on
    malformed lines.  Returns the raw rows IN FILE ORDER (dedupe is
    last-row-wins over this order)."""
    if not isinstance(path, str) or not path or not os.path.exists(path):
        raise DataBlocked(f"announcement ledger not found: {path!r}")
    rows = []
    with open(path, "r", encoding="utf-8") as handle:
        for n, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except ValueError as exc:
                raise DataBlocked(f"ledger line {n} is not valid JSON: {exc}") from exc
            if not isinstance(row, dict) or "area" not in row \
                    or "row_type" not in row:
                raise DataBlocked(f"ledger line {n} is not a ledger row")
            rows.append(row)
    if not rows:
        raise DataBlocked("announcement ledger holds no rows")
    return rows


def dedupe_ledger_rows(rows: list) -> list:
    """Canonical dedupe: (area, effective_date) LAST-ROW-WINS over the raw
    file, preserving first-sighting order of the surviving keys (the
    binding directive: 151 unique events from the 220-row file; the 61
    dropped duplicates are UNEVIDENCED->EVIDENCED upgrades)."""
    dedup: dict = {}
    order: list = []
    for row in rows:
        key = (row.get("area"), row.get("effective_date"))
        if key not in dedup:
            order.append(key)
        dedup[key] = row
    return [dedup[k] for k in order]


def extract_events(deduped: list):
    """RATE_CHANGE rows with delta != 0 from the DEDUPED ledger.

    Returns (events, unavailable) where each event is a dict with
    ``area / effective_date / effective_dt / eligible_dt / available_dt /
    delta / value``.  Per the BINDING A1 adjudication A-2 the eligibility
    instant ``eligible_dt`` is the row's PRECOMPUTED
    ``first_readable_decision_utc`` field; a row with that field null
    fails closed (MISSING_AVAILABLE_TIME_EVIDENCE) and is NEVER read
    (never scheduled).  ``available_dt`` carries the row's operative
    availability stamp exactly as the ledger carries it (used only for
    the deterministic tie-break; ``None`` falls back to the eligibility
    instant).  Events are sorted by (eligible_dt, tie instant, area) for
    determinism.  Malformed RATE_CHANGE rows (unparsable stamps,
    non-numeric values) raise ``DataBlocked``.  BASELINE_LEVEL rows are
    returned separately as the vintage floor.
    """
    events, unavailable, baselines = [], [], []
    zero_delta = 0
    for row in deduped:
        row_type = row.get("row_type")
        area = row.get("area")
        if area not in AREA_ORDER:
            raise DataBlocked(f"ledger row carries unknown area {area!r}")
        ann = row.get("announcement") or {}
        if row_type == "BASELINE_LEVEL":
            value = row.get("new_value")
            if isinstance(value, bool) or not isinstance(value, (int, float)) \
                    or not math.isfinite(float(value)):
                raise DataBlocked(f"{area}: BASELINE_LEVEL value is not numeric")
            available = _parse_utc(ann.get("operative_available_time_utc"),
                                   f"{area} baseline operative_available_time_utc")
            baselines.append({"area": area, "value": float(value),
                              "available_dt": available})
            continue
        if row_type != "RATE_CHANGE":
            raise DataBlocked(f"ledger row_type {row_type!r} is not a ledger row type")
        old, new = row.get("old_value"), row.get("new_value")
        for name, v in (("old_value", old), ("new_value", new)):
            if isinstance(v, bool) or not isinstance(v, (int, float)) \
                    or not math.isfinite(float(v)):
                raise DataBlocked(f"{area} {row.get('effective_date')}: {name} is not numeric")
        delta = float(new) - float(old)
        if delta == 0:
            zero_delta += 1  # not an event by definition (none in the pinned ledger)
            continue
        # A1 adjudication A-2: eligibility = the PRECOMPUTED
        # first_readable_decision_utc; fail closed when null.
        raw_fr = row.get("first_readable_decision_utc")
        if raw_fr is None:
            unavailable.append({"area": area,
                                "effective_date": row.get("effective_date"),
                                "reason": "MISSING_AVAILABLE_TIME_EVIDENCE"})
            continue
        raw_avail = ann.get("operative_available_time_utc")
        events.append({
            "area": area,
            "effective_date": row.get("effective_date"),
            "effective_dt": _parse_utc(row.get("effective_time_utc"),
                                       f"{area} {row.get('effective_date')} effective_time_utc"),
            "eligible_dt": _parse_utc(raw_fr,
                                      f"{area} {row.get('effective_date')} first_readable_decision_utc"),
            "available_dt": (_parse_utc(raw_avail,
                                        f"{area} {row.get('effective_date')} operative_available_time_utc")
                             if raw_avail is not None else None),
            "delta": delta,
            "value": float(new),
        })
    events.sort(key=lambda e: (e["eligible_dt"], e["available_dt"] or e["eligible_dt"],
                               e["area"]))
    return {"events": events, "unavailable": unavailable,
            "baselines": baselines, "zero_delta_rows": zero_delta}


class LedgerVintageReader:
    """As-of policy-rate reader over the DEDUPED ledger (the pinned v4
    evidenced-vintages semantics: policy rates are piecewise constant; the
    deduped ledger carries every establishing step's value, effective
    instant and operative availability exactly as pinned).

    ``policy_rate(area, t)`` returns the percent-per-annum level of the row
    with the LATEST effective instant subject to BOTH frozen gates
    (available_time_utc <= t AND effective_time_utc <= t -- a rate is never
    read before it is in force, and never before its availability stamp);
    rows without an effective instant (the BASELINE_LEVEL floor) are
    eligible from their availability alone.  ``None`` = NO_EVAL (fail
    closed, never interpolated or fill-forwarded).
    """

    def __init__(self, deduped_rows: list) -> None:
        by_area: dict = defaultdict(list)
        for row in deduped_rows:
            area = row.get("area")
            ann = row.get("announcement") or {}
            raw_avail = ann.get("operative_available_time_utc")
            if raw_avail is None:
                continue  # never a readable vintage (fail-closed row)
            available = _parse_utc(raw_avail, f"{area} vintage availability")
            raw_eff = row.get("effective_time_utc")
            effective = (_parse_utc(raw_eff, f"{area} vintage effective_time_utc")
                         if raw_eff is not None else None)
            value = row.get("new_value")
            if isinstance(value, bool) or not isinstance(value, (int, float)) \
                    or not math.isfinite(float(value)):
                raise DataBlocked(f"{area}: vintage value is not numeric")
            by_area[area].append((effective, available, float(value)))
        self._series = {}
        for area, rows in by_area.items():
            rows.sort(key=lambda r: (r[0] or datetime(1, 1, 1, tzinfo=UTC), r[1]))
            self._series[area] = rows

    def policy_rate(self, area: str, t: datetime) -> float | None:
        rows = self._series.get(area)
        if not rows:
            return None
        best = None
        for effective, available, value in rows:  # ascending effective order
            if available > t:
                continue
            if effective is not None and effective > t:
                continue
            best = value  # latest eligible effective instant wins
        return best

    def differential(self, base_area: str, quote_area: str, t: datetime) -> float | None:
        base = self.policy_rate(base_area, t)
        if base is None:
            return None
        quote = self.policy_rate(quote_area, t)
        if quote is None:
            return None
        return base - quote


# ------------------------------------------------------------------ #
# price snapshot loading (authorized H1 research series ONLY)         #
# ------------------------------------------------------------------ #
def _parse_stamp(raw) -> datetime:
    try:
        return datetime.strptime(raw, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
    except (TypeError, ValueError) as exc:
        raise DataBlocked(f"unparsable H1 bar stamp {raw!r}") from exc


def load_h1_bars(h1_dir: str, pair: str) -> dict:
    """Load one pair's completed H1 bars from the authorized snapshot
    (inherited V3 loader semantics, mirrored verbatim): provider no-data
    windows are empty; malformed files, conflicting duplicate stamps and
    non-positive prices fail closed."""
    sym = pair.replace("/", "")
    paths = sorted(glob.glob(os.path.join(h1_dir, f"{sym}_1h_*.json")))
    if not paths:
        raise DataBlocked(f"no H1 snapshot files for {pair} under {h1_dir}")
    bars: dict = {}
    for path in paths:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, ValueError) as exc:
            raise DataBlocked(f"unreadable H1 snapshot file {path}: {exc}") from exc
        if isinstance(payload, dict) and payload.get("status") == "error":
            continue  # provider no-data window (recorded evidence, no bars)
        rows = payload.get("values") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            raise DataBlocked(f"H1 snapshot file {path} carries no values list")
        for row in rows:
            if not isinstance(row, dict):
                raise DataBlocked(f"H1 snapshot file {path} has a malformed row")
            try:
                stamp = _parse_stamp(row["datetime"])
                ohlc = (float(row["open"]), float(row["high"]),
                        float(row["low"]), float(row["close"]))
            except (KeyError, TypeError, ValueError) as exc:
                raise DataBlocked(
                    f"H1 snapshot file {path} row is not a parseable bar: {exc}") from exc
            if any(not math.isfinite(v) or v <= 0 for v in ohlc):
                raise DataBlocked(f"H1 snapshot file {path} has a non-positive/non-finite bar")
            if stamp in bars and bars[stamp] != ohlc:
                raise DataBlocked(f"conflicting duplicate H1 bar at {stamp.isoformat()}")
            bars[stamp] = ohlc
    if not bars:
        raise DataBlocked(f"H1 snapshot for {pair} holds no bars")
    return bars


# ------------------------------------------------------------------ #
# NY-day calendar: decision stamps and existing-bar helpers            #
# ------------------------------------------------------------------ #
def ny_decision_stamp(ny_day: date) -> datetime:
    """UTC instant of the 16:00 America/New_York bar of an NY calendar day
    (20:00Z EDT / 21:00Z EST via zoneinfo -- DST-aware, never fixed
    offsets)."""
    return datetime(ny_day.year, ny_day.month, ny_day.day, 16, 0, tzinfo=NY_TZ).astimezone(UTC)


def existing_decision_bars(bars: dict) -> list:
    """Sorted Mon-Fri 16:00-NY stamps that EXIST in the snapshot (a
    decision instant is a completed daily flat bar, so the bar must be
    present; holiday gaps simply do not enumerate)."""
    out = []
    for stamp in bars:
        local = stamp.astimezone(NY_TZ)
        if local.hour == 16 and local.minute == 0 and local.weekday() < 5:
            out.append(stamp)
    out.sort()
    return out


def first_bar_at_or_after(existing: list, t: datetime):
    """Index of the first EXISTING decision bar with stamp >= t, or None."""
    i = bisect.bisect_left(existing, t)
    return i if i < len(existing) else None


def _force_flat_indices(existing: list) -> set:
    """Indices of the last decision bar BEFORE each internal fold boundary
    (the bar whose OPEN is the boundary force-flat exit bar).  A boundary
    beyond the snapshot's last bar is not a boundary this book can ever
    interact with (data end closes every position first), so it produces
    no force-flat bar."""
    out = set()
    for boundary in INTERNAL_BOUNDARIES:
        b = datetime.fromisoformat(boundary)
        if not any(s >= b for s in existing):
            continue  # boundary outside the snapshot: no force-flat bar
        candidates = [i for i, s in enumerate(existing) if s < b]
        if candidates:
            out.add(max(candidates))
    return out


def _iso(t: datetime) -> str:
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00")


# ------------------------------------------------------------------ #
# frozen direction map and holding law                                #
# ------------------------------------------------------------------ #
def mapped_directions(event: dict, arm_id: str) -> dict:
    """{pair: side (+1 long base / -1 short base)} for one event under the
    arm's frozen mapping.  Anchor/neighbour/benchmark: the area's OWN pair
    (US events drive all 7 via the long-USD map).  Control: the packet's
    frozen sham derangement table, with the event's delta re-expressed per
    the SHAM area's base/quote role (sham == US => the long-USD map)."""
    area, delta = event["area"], event["delta"]
    if arm_id == "causal_negative_control":
        sham = SHAM_AREA[area]
    else:
        sham = area
    if sham == "US":
        base_side = 1 if delta > 0 else -1
        return {pair: base_side * s for pair, s in US_HIKE_SIDE.items()}
    pair = AREA_OWN_PAIR[sham]
    base_area, _quote = PAIR_AREAS[pair]
    if delta > 0:
        side = 1 if sham == base_area else -1
    else:
        side = -1 if sham == base_area else 1
    return {pair: side}


def hold_ny_days(event: dict, arm_id: str) -> int:
    """Frozen holding law: 10 NY-days everywhere except the neighbour's
    cuts (delta < 0), which hold 3."""
    if arm_id == "neighbour" and event["delta"] < 0:
        return NEIGHBOUR_CUT_HOLD_NY_DAYS
    return ANCHOR_HOLD_NY_DAYS


# ------------------------------------------------------------------ #
# per-pair schedule walk                                              #
# ------------------------------------------------------------------ #
def _schedule_pair(pair, existing, bars, candidates, arm_id, counts, skipped):
    """Walk one pair's existing decision bars through the frozen holding
    law.  ``candidates`` are pre-resolved event decisions for THIS pair
    ({decision_idx, ...}) sorted by (decision_ts, availability).  Returns
    the raw round trips (entry/exit indices; prices attached later)."""
    ff = _force_flat_indices(existing)
    by_idx = defaultdict(list)
    for c in candidates:
        by_idx[c["decision_idx"]].append(c)
    trips: list = []
    pos: dict | None = None
    for i, ts in enumerate(existing):
        # 1) exit: scheduled, boundary force-flat, or earliest-scheduled
        #    (data-end) exit all land on pos["exit_idx"].
        if pos is not None and i == pos["exit_idx"]:
            trips.append(dict(pos, exit_idx=i))
            pos = None
        # 2) event decisions at this bar (tie-break: earlier availability
        #    first -- candidates are pre-sorted).
        for c in by_idx.get(i, ()):
            if pos is not None:
                counts["no_refresh_ignored"] += 1  # NO_TRADE, never deferred
                continue
            if i + 1 >= len(existing):
                counts["missing_next_fill_bar"] += 1
                skipped.append({"pair": pair, "area": c["area"],
                                "effective_date": c["effective_date"],
                                "decision_ts": _iso(ts),
                                "reason": "MISSING_NEXT_FILL_BAR"})
                continue
            j = i + 1
            if existing[j] - ts > timedelta(days=MAX_FILL_LAG_DAYS):
                counts["fill_lag_exceeds_4_days"] += 1  # fail-closed NO_TRADE
                skipped.append({"pair": pair, "area": c["area"],
                                "effective_date": c["effective_date"],
                                "decision_ts": _iso(ts),
                                "fill_ts": _iso(existing[j]),
                                "reason": "FILL_LAG_EXCEEDS_4_DAYS"})
                continue
            if j in ff:
                counts["fold_boundary_no_entry"] += 1
                skipped.append({"pair": pair, "area": c["area"],
                                "effective_date": c["effective_date"],
                                "decision_ts": _iso(ts),
                                "reason": "FOLD_BOUNDARY_NO_ENTRY"})
                continue
            hold = hold_ny_days(c, arm_id)
            scheduled = j + hold
            # force-flat interception: the first boundary force-flat bar
            # after entry, when at/before the scheduled exit, closes the
            # position there (no position crosses a fold boundary).
            nxt_ff = min((f for f in ff if f > j), default=None)
            if nxt_ff is not None and nxt_ff <= scheduled:
                exit_idx, force_flat = nxt_ff, True
            elif scheduled < len(existing):
                exit_idx, force_flat = scheduled, False
            else:
                # Missing exit bar / beyond snapshot: earliest-scheduled
                # exit at the latest existing bar before the scheduled
                # instant; never fill-forward.  No such bar => void.
                if len(existing) - 1 <= j:
                    counts["end_of_data_no_exit"] += 1
                    skipped.append({"pair": pair, "area": c["area"],
                                    "effective_date": c["effective_date"],
                                    "decision_ts": _iso(ts),
                                    "reason": "END_OF_DATA_NO_EXIT"})
                    continue
                exit_idx, force_flat = len(existing) - 1, False
                counts["earliest_scheduled_exit_data_end"] += 1
            pos = {"decision_idx": i, "entry_idx": j, "exit_idx": exit_idx,
                   "side": c["side"], "force_flat": force_flat,
                   "area": c["area"], "effective_date": c["effective_date"],
                   "tie_dt": c["tie_dt"]}
    # pos can never survive the walk: every exit_idx is an existing index.
    if pos is not None:  # pragma: no cover - structural invariant
        raise DataBlocked(f"{pair}: position unresolved at end of walk")
    return trips


def _decisions_of(pair, existing, bars, trips, short):
    """Decision payloads (runner contract) from raw trips; fills at the
    OPEN of the entry/exit bars; deterministic ids."""
    tag = pair.replace("/", "")
    out = []
    for tr in trips:
        di, ei, xi = tr["decision_idx"], tr["entry_idx"], tr["exit_idx"]
        out.append({
            "decision_id": f"{PROPOSAL_ID}-{short}-{tag}-{tr['area']}-"
                           f"{tr['effective_date']}-{_iso(existing[di])}",
            "pair": pair,
            "side": tr["side"],
            "decision_ts": _iso(existing[di]),
            "notional_usd": NOTIONAL_USD,
            "entry_bar_ts": _iso(existing[ei]),
            "entry_price": bars[existing[ei]][0],
            "exit_bar_ts": _iso(existing[xi]),
            "exit_price": bars[existing[xi]][0],
            "force_flat": tr["force_flat"],
        })
    return out


def _financing_adjustment(reader: LedgerVintageReader, pair, trip) -> float:
    """sign * notional * sum(day-start as-of differentials)/365 over the
    calendar days [entry fill date, exit fill date).  Each accrual instant
    is the UTC day-start of the calendar day; eligibility requires
    available_time_utc <= instant AND effective_time_utc <= instant (never
    eligible on the effective date alone); a missing read fails closed."""
    base_area, quote_area = PAIR_AREAS[pair]
    day = trip["entry_dt"].astimezone(UTC).date()
    last = trip["exit_dt"].astimezone(UTC).date()
    diffs = []
    while day < last:
        t = datetime(day.year, day.month, day.day, tzinfo=UTC)
        diff = reader.differential(base_area, quote_area, t)
        if diff is None:
            raise DataBlocked(
                f"{pair}: no eligible policy-rate vintage for accrual at {_iso(t)}")
        diffs.append(diff / PERCENT_PER_ANNUM_TO_DECIMAL)
        day += timedelta(days=1)
    return trip["side"] * NOTIONAL_USD * math.fsum(diffs) / 365.0


# ------------------------------------------------------------------ #
# family API entry point                                               #
# ------------------------------------------------------------------ #
def run_arm(arm: str, data_paths: dict, macro_reader=None, freeze_token=None):
    """Frozen family API (see module docstring).  ``macro_reader`` and
    ``freeze_token`` are accepted per the runner contract and intentionally
    unused: macro reads go through the deduped pinned ledger (the pinned v4
    evidenced-vintages semantics); the runner owns scored/dry-run
    semantics."""
    arm_id = _ARM_IDS.get(arm)
    if arm_id is None:
        raise ValueError("family2 arm must be one of 'anchor'/'neighbour'/"
                         "'control'/'causal_negative_control'/"
                         f"'benchmark_treatment', got {arm!r}")
    if not isinstance(data_paths, dict):
        raise DataBlocked("data_paths must be a mapping")
    if not isinstance(data_paths.get("h1_dir"), str):
        raise DataBlocked("data_paths is missing the 'h1_dir' H1 snapshot directory")
    rows = load_ledger_rows(data_paths["announcement_ledger"])
    deduped = dedupe_ledger_rows(rows)
    extracted = extract_events(deduped)
    events = extracted["events"]
    unavailable = extracted["unavailable"]
    reader = LedgerVintageReader(deduped)

    use_bench_lag = arm_id == "bench"
    short = _ARM_SHORT[arm_id]
    decisions: list = []
    financing_events: list = []
    skipped: list = []
    schedule_totals: dict = {}
    counts_total: dict = {}
    no_eval_total = {"no_eval_before_cutoff": 0, "no_decision_bar_available": 0}

    for pair in PAIR_UNIVERSE:
        bars = load_h1_bars(data_paths["h1_dir"], pair)
        existing = existing_decision_bars(bars)
        counts = {"candidates": 0, "no_refresh_ignored": 0,
                  "missing_next_fill_bar": 0, "fill_lag_exceeds_4_days": 0,
                  "fold_boundary_no_entry": 0, "end_of_data_no_exit": 0,
                  "earliest_scheduled_exit_data_end": 0}
        candidates = []
        for ev in events:
            for c_pair, side in mapped_directions(ev, arm_id).items():
                if c_pair != pair:
                    continue
                counts["candidates"] += 1
                # A1 adjudication A-2: the schedule anchor is the row's
                # PRECOMPUTED first_readable_decision_utc.
                eligible = ev["eligible_dt"]
                if use_bench_lag:
                    eligible = eligible + timedelta(days=BENCHMARK_LAG_DAYS)
                idx = first_bar_at_or_after(existing, eligible)
                if idx is None:
                    no_eval_total["no_decision_bar_available"] += 1
                    skipped.append({"pair": pair, "area": ev["area"],
                                    "effective_date": ev["effective_date"],
                                    "reason": "NO_DECISION_BAR_AVAILABLE"})
                    continue
                decision_ts = existing[idx]
                if decision_ts < NO_EVAL_CUTOFF_UTC:
                    no_eval_total["no_eval_before_cutoff"] += 1  # NO_EVAL, never backfilled
                    continue
                candidates.append({"decision_idx": idx, "side": side,
                                   "area": ev["area"],
                                   "effective_date": ev["effective_date"],
                                   "eligible_dt": eligible,
                                   "tie_dt": ev["available_dt"] or eligible,
                                   "delta": ev["delta"]})
        # Deterministic order: decision instant, then earlier operative
        # availability (fallback: the eligibility instant), then effective
        # date, then area (full tie-break chain).
        candidates.sort(key=lambda c: (c["decision_idx"], c["tie_dt"],
                                       _eff_key(c), c["area"]))
        trips = _schedule_pair(pair, existing, bars, candidates, arm_id,
                               counts, skipped)
        pair_decisions = _decisions_of(pair, existing, bars, trips, short)
        for tr, dec in zip(trips, pair_decisions):
            tr = dict(tr,
                      entry_dt=existing[tr["entry_idx"]],
                      exit_dt=existing[tr["exit_idx"]])
            adjustment = _financing_adjustment(reader, pair, tr)
            financing_events.append({"decision_id": dec["decision_id"],
                                     "financing_adjustment_usd": adjustment,
                                     "formula": FINANCING_FORMULA_ID})
        decisions.extend(pair_decisions)
        schedule_totals[pair] = dict(counts, round_trips=len(pair_decisions),
                                    decision_bars=len(existing))
        counts_total[pair] = counts

    meta = {
        "decision_clock": "daily",
        "proposal_id": PROPOSAL_ID,
        "alpha_definition": "per_trade_expectancy_difference_v1",
        "pair_universe": list(PAIR_UNIVERSE),
        "arm_id": f"{PROPOSAL_ID}-{_META_ARM[arm_id]}",
        "decision_bar_convention": "completed H1 bar whose America/New_York wall "
                                   "time is 16:00, Mon-Fri only (20:00Z EDT / "
                                   "21:00Z EST via zoneinfo); fill at the OPEN of "
                                   "the next existing 16:00-NY bar (one-event lag); "
                                   "decision->fill gap fail-closed NO_TRADE beyond "
                                   "the frozen 4-day next-session constraint",
        "events": {
            "basis": "RATE_CHANGE rows of the DEDUPED v2 announcement ledger "
                     "(last-row-wins by (area, effective_date)), delta != 0",
            "deduped_rate_change_rows": sum(1 for r in deduped
                                            if r.get("row_type") == "RATE_CHANGE"),
            "raw_rows": len(rows),
            "events_used": len(events),
            "zero_delta_rows": extracted["zero_delta_rows"],
            "unavailable_never_read": unavailable,
            "n_unavailable_never_read": len(unavailable),
        },
        "eligibility": {
            "eligibility_field": "row.first_readable_decision_utc (the "
                                 "ledger's PRECOMPUTED first 16:00-NY "
                                 "decision at/after max(operative "
                                 "availability, effective) -- the frozen "
                                 "program PIT invariant: a decision never "
                                 "reads a row whose effective_time_utc > T)",
            "adjudication": "A1 adjudication A-2 applied (research/control/"
                            "forex_free_v4_run/a1_ambiguity_adjudication."
                            "json): eligibility = first_readable_decision_"
                            "utc; availability-only eligibility rejected",
            "rule": "T = first completed 16:00-NY bar with completion >= "
                    "first_readable_decision_utc; fail-closed "
                    "MISSING_AVAILABLE_TIME_EVIDENCE when the field is null; "
                    "tie-break on the operative availability instant "
                    "(fallback: the eligibility instant)",
            "no_eval_cutoff_utc": _iso(NO_EVAL_CUTOFF_UTC),
            "no_eval_before_cutoff": no_eval_total["no_eval_before_cutoff"],
            "no_decision_bar_available": no_eval_total["no_decision_bar_available"],
        },
        "direction_map": {
            "non_us": "area's own pair; +1 long base if delta>0 and the area is "
                      "the pair's base, -1 if the quote; flipped for delta<0",
            "us_drives_all_7_long_usd_on_hike": {p: s for p, s in US_HIKE_SIDE.items()},
            "area_own_pair": dict(AREA_OWN_PAIR),
        },
        "holding": {
            "anchor_ny_days": ANCHOR_HOLD_NY_DAYS,
            "neighbour_hike_ny_days": ANCHOR_HOLD_NY_DAYS,
            "neighbour_cut_ny_days": NEIGHBOUR_CUT_HOLD_NY_DAYS,
            "exit_rule": "open of the H-th existing 16:00-NY bar after the "
                         "entry bar; missing/beyond-data exit => earliest-"
                         "scheduled exit, never fill-forward",
        },
        "governor": {"max_positions_per_pair": 1,
                     "max_entries_per_pair_per_ny_day": 1,
                     "no_refresh_ignored": sum(c["no_refresh_ignored"]
                                               for c in counts_total.values()),
                     "tie_break": "same decision instant => earlier availability "
                                  "wins; later events ignored"},
        "financing": {
            "formula": FINANCING_FORMULA_VERBATIM,
            "formula_id": FINANCING_FORMULA_ID,
            "vintages": "reconstructed from the SAME deduped ledger "
                        "(BASELINE_LEVEL floor + every RATE_CHANGE step; "
                        "piecewise-constant policy rates), read as-of with "
                        "availability AND effectiveness gating at each "
                        "UTC day-start accrual instant",
            "units": "percent-per-annum converted to annualized decimals (/100) "
                     "exactly once at the family financing boundary",
            "disclosed_approximation": FINANCING_APPROXIMATION,
        },
        "skipped_decisions": skipped,
        "skipped_counts": _sorted_counts(skipped),
        "schedule_totals": schedule_totals,
    }
    if arm_id == "causal_negative_control":
        meta["sham_derangement"] = {
            "mapping": {a: SHAM_AREA[a] for a in AREA_ORDER},
            "area_order": list(AREA_ORDER),
            "source": "packet arms.control.sham_derangement_frozen.mapping "
                      "(implemented verbatim; see AMBIGUITIES.md for the "
                      "+3-rule vs mapping-table discrepancy record)",
            "disclosed_leakage": "sham mappings share USD legs and rate cycles "
                                 "cluster globally; the control destroys the "
                                 "area-specific surprise link only",
            "preregistered_non_reproduction_rule": "control reproduces (family "
                "fails its control gate) iff control financing-adjusted "
                "expectancy > 0 AND control pf >= 1.10, OR control expectancy "
                ">= 0.5 x anchor expectancy",
        }
    if arm_id == "bench":
        meta["benchmark_treatment"] = {
            "lag_days": BENCHMARK_LAG_DAYS,
            "definition": "the anchor law with every event's availability "
                          "instant shifted +180 calendar days LATER (frozen ex "
                          "ante, never tuned): fresh policy information removed, "
                          "schedule shape / clock / holding / fills / costs "
                          "unchanged",
            "bench_schedule_id": f"{PROPOSAL_ID}-bench",
        }
    return {"decisions": decisions, "financing_events": financing_events,
            "meta": meta}


def _eff_key(c):
    return c["effective_date"] or ""


def _sorted_counts(skipped: list) -> dict:
    out: dict = {}
    for item in skipped:
        out[item["reason"]] = out.get(item["reason"], 0) + 1
    return dict(sorted(out.items()))


# ------------------------------------------------------------------ #
# schedule-only replay (counts, no PnL, no prices beyond presence)     #
# ------------------------------------------------------------------ #
def schedule_counts(data_paths: dict) -> dict:
    """Schedule-only feasibility counts from the deduped ledger + the H1
    snapshot's bar-presence calendar ONLY.  Never computes PnL."""
    if not isinstance(data_paths, dict):
        raise DataBlocked("data_paths must be a mapping")
    if not isinstance(data_paths.get("h1_dir"), str):
        raise DataBlocked("data_paths is missing the 'h1_dir' H1 snapshot directory")
    rows = load_ledger_rows(data_paths["announcement_ledger"])
    deduped = dedupe_ledger_rows(rows)
    extracted = extract_events(deduped)
    events = extracted["events"]
    per_arm = {}
    for arm in ("anchor", "neighbour", "control"):
        arm_id = _ARM_IDS[arm]
        total = 0
        per_pair = {}
        for pair in PAIR_UNIVERSE:
            bars = load_h1_bars(data_paths["h1_dir"], pair)
            existing = existing_decision_bars(bars)
            n = 0
            for ev in events:
                if pair not in mapped_directions(ev, arm_id):
                    continue
                idx = first_bar_at_or_after(existing, ev["eligible_dt"])
                if idx is not None and existing[idx] >= NO_EVAL_CUTOFF_UTC:
                    n += 1
            per_pair[pair] = n
            total += n
        per_arm[arm] = {"total": total, "per_pair": per_pair}
    return {"proposal_id": PROPOSAL_ID, "events_used": len(events),
            "unavailable_never_read": len(extracted["unavailable"]),
            "per_arm_decision_counts": per_arm, "no_pnl": True}


# ------------------------------------------------------------------ #
# cell-record assembly (mirrors the inherited runner record structure) #
# plus the frozen margin-to-fail fields per Stage-A gate                #
# ------------------------------------------------------------------ #
def fold_of(entry_ts_iso):
    """Fold index by ENTRY instant (kernel semantics, mirrored): None if
    purged (within PURGE_DAYS after a fold start) or before the first
    boundary (warmup region)."""
    return _kernel.fold_of(entry_ts_iso)


def _exit_in_preboundary_purge(exit_ts_iso: str) -> bool:
    """True when the EXIT instant falls in the 14-calendar-day window
    BEFORE an internal fold boundary (the packet's purge-either-side rule;
    the after-entry side is the kernel fold_of purge)."""
    t = datetime.fromisoformat(str(exit_ts_iso))
    for boundary in INTERNAL_BOUNDARIES:
        b = datetime.fromisoformat(boundary)
        if b - timedelta(days=PURGE_DAYS) <= t < b:
            return True
    return False


def build_trade_specs(decisions: list) -> list:
    """Kernel TradeSpecs from decision payloads (runner _spec_of mirror)."""
    return [accounting.TradeSpec(
        trade_id=d["decision_id"], pair=d["pair"],
        side="LONG" if d["side"] > 0 else "SHORT",
        notional_usd=float(d["notional_usd"]),
        entry_price=float(d["entry_price"]),
        exit_price=float(d["exit_price"]),
        entry_ts_utc=d["entry_bar_ts"], exit_ts_utc=d["exit_bar_ts"])
        for d in decisions]


def stress_book(specs: list, scored_ids: set, fill_delay_events=None) -> dict:
    """F1-FIXED stress booking through the inherited kernel: the SAME
    trades re-booked at every tier of {1.0, 1.5, 2.0} with the tier
    multiplier reaching the BOOKED net PnL (gross tier-invariant; rows
    pairwise distinct certified inside the kernel).  ``fill_delay_events``
    is carried UNBLENDED."""
    result = accounting.book_stress(specs, fill_delay_events=fill_delay_events)
    out = {}
    for tier, r in sorted(result.items()):
        rows = [net for tid, net in r.booked_rows if tid in scored_ids]
        m = dict(accounting.book_metrics(rows))
        m["cost_component_delta_vs_base_usd"] = r.cost_component_delta_vs_base_usd
        m["stress_rows_distinct_certified"] = True
        out[f"tier{tier}"] = m
    return out


def assemble_cell_record(decisions, financing_events, *, arm,
                         family_id=PROPOSAL_ID, price_dir=None,
                         benchmark_expectancy=None):
    """Run one arm's decision stream through the inherited kernel pipeline
    and return the cell record mirroring the runner's record structure,
    plus ``margin_to_fail``: the frozen distance-to-threshold of EVERY
    Stage-A gate (binding directive: margin-to-fail reporting machinery
    frozen at implementation).  No dry-run sanitization here: the runner
    owns scored/dry-run semantics."""
    arm_id = _ARM_IDS.get(arm)
    if arm_id is None:
        raise ValueError(f"unknown arm {arm!r}")
    checked, adjustments, formula = _kernel.validate_decisions(
        decisions, financing_events)
    kept, dropped = _kernel.apply_session_gate(checked)
    specs = build_trade_specs(kept)
    dual = accounting.book_dual(specs, cost_tier=BASE_TIER,
                                financing_adjustment_usd=dict(adjustments))
    booked = []
    for d, col in zip(kept, dual):
        t2 = dict(d)
        t2["_gross_move_pnl"] = round(col.gross_price_pnl_usd, 10)
        t2["_price_only"] = round(col.price_only_pnl_usd, 10)
        t2["_financing"] = round(col.financing_adjustment_usd, 10)
        t2["_pnl"] = round(col.financing_adjusted_pnl_usd, 10)
        booked.append(t2)
    for t in booked:
        t["_fold"] = fold_of(t["entry_bar_ts"])
    exit_purged = [t for t in booked
                   if t["_fold"] is not None
                   and _exit_in_preboundary_purge(t["exit_bar_ts"])]
    scored = [t for t in booked
              if t["_fold"] is not None
              and not _exit_in_preboundary_purge(t["exit_bar_ts"])]
    pnls_fin = [t["_pnl"] for t in scored]
    pnls_price = [t["_price_only"] for t in scored]
    folds = _kernel.fold_metrics([dict(t, _pnl=p) for t, p in zip(scored, pnls_fin)])
    conc = _kernel.concentration([dict(t, _pnl=p) for t, p in zip(scored, pnls_fin)])
    mdd = _kernel.mdd_of([p for _, p in sorted(zip(scored, pnls_fin),
                                               key=lambda sp: sp[0]["exit_bar_ts"])])
    scenarios = _kernel.dropout_scenarios(scored, pnls_fin, folds)
    usd_index = usd_source = None
    if price_dir:
        usd_index, usd_source, _n = _kernel.usd_index_from_data_paths(
            {"h1_dir": price_dir})
    usd = _kernel.usd_drift_corr(
        [dict(t, _pnl=p) for t, p in zip(scored, pnls_fin)], usd_index or {})
    stress = stress_book(specs, {t["decision_id"] for t in scored}) if scored else {}
    base = accounting.book_metrics(pnls_fin)
    price_book = accounting.book_metrics(pnls_price)
    alpha = None
    if benchmark_expectancy is not None and base["trades"]:
        alpha = round(base["expectancy"] - float(benchmark_expectancy), 10)
    mtf = margin_to_fail(base=base, price_only=price_book, folds=folds, mdd=mdd,
                         fold_share=_kernel.fold_positive_share(folds),
                         conc=conc, scenarios=scenarios, usd=usd, alpha=alpha,
                         n_decisions=len(checked))
    cell_id = f"{family_id}:{arm}:tier1.0"
    extra = {
        "cell_id": cell_id, "family_id": family_id, "arm": arm,
        "proposal_id": PROPOSAL_ID,
        "decision_clock": "daily",
        "financing_formula": formula,
        "n_decisions": len(checked),
        "n_trades_kept": len(kept),
        "weekend_gate_dropped": len(dropped),
        "purged_trades": sum(1 for t in booked if t["_fold"] is None),
        "purge_excluded_exit_side": len(exit_purged),
        "folds_declared": list(FOLD_BOUNDARIES), "purge_days": PURGE_DAYS,
        "base": base,                             # financing-adjusted book
        "base_price_only": price_book,
        "folds": folds, "mdd_usd": mdd,
        "fold_positive_share": _kernel.fold_positive_share(folds),
        "pair_concentration": conc,
        "dropout_scenarios": scenarios,
        "break_even_cost_bps": accounting.break_even_bps(
            [t["_gross_move_pnl"] for t in scored]) if scored else None,
        "usd_drift_diag": usd, "usd_index_source": usd_source,
        "stress": stress,
        "delay_stress": {"carried_unblended": True, "n_delayed_trades": 0},
        "incremental_alpha": alpha,
        "incremental_alpha_definition": "per_trade_expectancy_difference_v1",
        "benchmark_expectancy": benchmark_expectancy,
        "margin_to_fail": mtf,
    }
    return accounting.build_scored_record(
        dual, record_id=cell_id, cost_tier=BASE_TIER, extra=extra)


def margin_to_fail(*, base, price_only, folds, mdd, fold_share, conc,
                   scenarios, usd, alpha, n_decisions) -> dict:
    """Frozen margin-to-fail fields per Stage-A gate (binding directive):
    the distance from each frozen threshold, recorded at implementation
    before any scored run.  ``None`` margins are gates that cannot evaluate
    on the record (e.g. no trades / diagnostic unevaluable)."""
    pop = [f for f in folds if f["populated"]]
    pos_pop = [f for f in pop if f["expectancy"] > 0]
    max_pair = max(conc.values()) if conc else None
    surv = sum(1 for s in scenarios if s["survived"]) if scenarios else 0
    corr = usd.get("corr") if isinstance(usd, dict) else None
    pf = base.get("pf")
    return {
        "gate_expectancy_gt_0": {
            "threshold": MIN_EXPECTANCY, "value": base.get("expectancy"),
            "margin": None if not base.get("trades")
            else round(base["expectancy"] - MIN_EXPECTANCY, 10)},
        "gate_pf_ge_1_10": {
            "threshold": MIN_PF, "value": pf,
            "margin": None if pf is None else round(pf - MIN_PF, 10)},
        "gate_price_only_expectancy_no_inversion": {
            "threshold": 0.0, "value": price_only.get("expectancy"),
            "margin": None if not price_only.get("trades")
            else round(price_only["expectancy"], 10)},
        "gate_positive_populated_folds_ge_2_of_3": {
            "threshold": MIN_POSITIVE_FOLDS, "populated_folds": len(pop),
            "value": len(pos_pop), "margin": len(pos_pop) - MIN_POSITIVE_FOLDS},
        "gate_fold_positive_share_le_0_50": {
            "threshold": MAX_POS_FOLD_SHARE, "value": fold_share,
            "margin": round(MAX_POS_FOLD_SHARE - fold_share, 10)},
        "gate_mdd_le_2500_usd": {
            "threshold": MDD_CEILING_USD, "value": mdd,
            "margin": round(MDD_CEILING_USD - mdd, 10)},
        "gate_pair_concentration_le_0_40": {
            "threshold": MAX_PAIR_POS_SHARE, "value": max_pair,
            "margin": None if max_pair is None
            else round(MAX_PAIR_POS_SHARE - max_pair, 10)},
        "gate_usd_drift_abs_corr_le_0_30": {
            "threshold": USD_CORR_CEILING, "value": corr,
            "evaluated": bool(usd.get("evaluated")) if isinstance(usd, dict) else False,
            "margin": None if (corr is None or not usd.get("evaluated"))
            else round(USD_CORR_CEILING - abs(corr), 10)},
        "gate_dropout_survival_ge_6_of_8": {
            "threshold": DROPOUT_MIN_SURVIVAL, "of": DROPOUT_SCENARIOS,
            "value": surv, "margin": surv - DROPOUT_MIN_SURVIVAL},
        "gate_incremental_alpha_gt_0": {
            "threshold": 0.0, "value": alpha,
            "margin": None if alpha is None else round(alpha, 10)},
        "gate_decisions_ge_40": {
            "threshold": MIN_DECISIONS_PER_ARM, "value": n_decisions,
            "margin": n_decisions - MIN_DECISIONS_PER_ARM},
    }


def stage_a_gates(record):
    """Frozen Stage-A gate set over this module's cell records (the
    inherited frozen kernel gate set, reused READ-ONLY so the thresholds
    and semantics can never drift from the runner)."""
    return _kernel.stage_a_gates(record)


def family_control_gate(anchor_record, control_record):
    """The packet's PREREGISTERED control non-reproduction rule (arms.
    control.preregistered_non_reproduction_rule, verbatim): the control
    REPRODUCES -- and the family fails its control gate regardless of the
    anchor's sign -- iff control financing-adjusted expectancy > 0 AND
    control PF >= 1.10, OR control expectancy >= 0.5 x anchor expectancy.
    Positive raw control PnL never overrides a firing control."""
    a = anchor_record["base"]["expectancy"]
    c = control_record["base"]["expectancy"]
    c_pf = control_record["base"].get("pf")
    clause_a = c > 0 and (c_pf is not None and c_pf >= CONTROL_REJECT_PF)
    clause_b = a is not None and c >= 0.5 * a
    return {"control_reproduces": bool(clause_a or clause_b),
            "clause_a_expectancy_and_pf": bool(clause_a),
            "clause_b_half_anchor_expectancy": bool(clause_b),
            "control_expectancy": c, "anchor_expectancy": a,
            "rule": "expectancy > 0 AND pf >= 1.10, OR expectancy >= "
                    "0.5 x anchor expectancy"}
