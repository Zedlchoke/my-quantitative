#!/usr/bin/env python
"""FOREX-FREE-V5 family FXFV5-A6-P1: pre-release position-avoidance window
(I1 implementation lane, cycle FOREX-FREE-V5).

Implements the SELECTED family EXACTLY as frozen by

  * research/control/forex_free_v5_run/i1_inputs/PROPOSAL_FXFV5-A6-P1.json
    (materialized from git object c82403d8c6f39a9d31c276db4d8510b70313c6cd),
  * research/control/forex_free_v5_run/selection_freeze.json
    (``selected.arms``: anchor / neighbour (+7d sham-calendar) /
    causal control (stale-calendar proximity isolation)),
  * research/control/forex_free_v5_run/p3_conditioning_clocks_v5.json
    (the ONLY conditioning clocks: 246 evidenced CPI clocks, GB 88 /
    CA 105 / AU 23 / NZ 30 in-S0, each row carrying decision_date,
    available_time_utc, precision, reference_period, archive_sha256).

MECHANISM (frozen law, transcribed verbatim from the packet): for each
evidenced clock c = (economy E, available_time_utc a) mapped to the unique
authorized pair P(E) (GB->GBP/USD, CA->USD/CAD, AU->AUD/USD, NZ->NZD/USD):

    F = the last completed 16:00 America/New_York bar of P(E) strictly
        before a;
    D = the completed 16:00-NY bar of the previous valid session strictly
        before F (decision bar);
    X = the first completed 16:00-NY bar strictly after a.

At D compute x = the sum of the 10 most recent daily log returns of P(E)
over completed 16:00-NY closes strictly before D; direction = -sign(x)
(exact zero -> NO_TRADE, fail-closed).  If flat and the governor allows,
enter at the OPEN of F and exit at the OPEN of X -- the holding window
[F, X] spans the evidenced release instant a by construction (F < a < X),
holds no post-release session beyond X, and never reads the print's value.

ARMS (selection_freeze.json, the frozen selection record):

  anchor      the frozen law on the published clocks;
  neighbour   sham-calendar: the same law anchored to a+7 calendar days
              (same time-of-day); a sham anchor is VALID iff no evidenced
              clock of ANY of the 4 evidenced economies falls strictly
              inside the resulting sham holding window; invalid anchors
              are dropped fail-closed and counted (sham_dropped);
  control     stale-calendar proximity isolation: the same law anchored to
              each economy's PREVIOUS evidenced clock (c_prev) -- decision,
              fill and exit instants all derived from c_prev's window with
              directions computed at the c_prev-anchored decision bar;
              the first clock per economy has no predecessor and is
              skipped (counted);
  benchmark_treatment
              kernel-required aux arm (scored_runner.BENCHMARK_ARM: booked
              inside a scored anchor cell, never a scored cell); its frozen
              schedule IS the stale-calendar (c_prev) law -- the packet's
              FXFV5-A6-P1-bench schedule.  (The selection freeze reuses the
              c_prev law as the scored ``control``; the kernel additionally
              needs a BENCHMARK_ARM to compute the packet's incremental
              alpha = anchor expectancy - stale expectancy, so the two
              slots share the same frozen schedule.)

FAIL-CLOSED DISCIPLINE (all inherited):

  * AU documented gaps (and any other gap) produce NO decision, never an
    inferred one: clocks whose F or X does not exist inside the snapshot,
    whose warmup (11 completed valid NY-day closes strictly before the
    decision bar) is short, or whose window a fold force-flat truncation
    would void, are EXCLUDED and counted -- never fill-forwarded.
  * Decisions are strictly availability-lagged: the decision bar D is a
    completed bar strictly before F < a, so every feature closes before
    the decision instant and no feature anywhere reads data with
    available_time > its computation instant.  The print's VALUE is never
    read (clock rows carry timing evidence only).
  * S0 cap: entries with instant >= 2025-07-25T00:00:00Z are excluded and
    counted (s0_cap_excluded) per the clocks authority S0 window
    2018-04-04..2025-07-24.
  * Fill lag > the frozen 4-day next-session constraint -> NO_TRADE.
  * Governor: max 1 position per pair, max 1 entry per pair per NY-day;
    blocked signals are NO_TRADE, never deferred.
  * Fold force-flat: a window that would cross an internal kernel fold
    boundary exits at the last completed 16:00-NY bar before the boundary
    (force_flat=true, kernel-attributed); a trade spanning a boundary is
    refused (the kernel's FOLD_FORCE_FLAT_VIOLATION backstop never fires
    on a scheduled trade).  A truncation that would break F < a < exit is
    a voided clock, never a shortened-span trade.
  * Financing: dual-book formula frozen verbatim (packet
    dual_book_and_financing.financing_formula_frozen_verbatim) --
    sign * notional_usd * sum(day-start as-of policy-rate differentials)
    / 365 over the calendar days [entry fill date, exit fill date), rates
    from the pinned V5-extension announcement ledger
    (sha256 cf1f01a7ec2d3d7506892c045139910937147df49d3742cc4ec72b36d20fd902)
    with rows eligible only when available_time_utc <= the accrual instant
    AND effective_time_utc <= the accrual instant (a day-start accrual can
    therefore never read a row on the row's own effective date).  The
    ledger's RATE_CHANGE rows are NEVER a signal: accounting only.

No parameter grid: exactly one frozen value per constant per arm
(trailing 10-NY-day sum everywhere -- the packet's neighbour-horizon
variant was not in the selected arm set; +7-day sham shift; c_prev
staleness; fixed clocks->pair map).
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

from research.assets.forex_free_v3.scored_runner import (  # read-only kernel
    INTERNAL_BOUNDARIES,
    MAX_FILL_LAG_DAYS,
)

__all__ = ["run_arm", "load_clocks", "LedgerVintageReader", "DataBlocked",
           "trailing_return_sum", "direction_of", "resolve_window",
           "fold_exit_resolution"]

UTC = timezone.utc
NY_TZ = ZoneInfo("America/New_York")

CYCLE_ID = "FOREX-FREE-V5"
PROPOSAL_ID = "FXFV5-A6-P1"

# --- the three scored arms (selection_freeze.json selected.arms) ---------
ARM_IDS = {
    "anchor": "FXFV5-A6-P1-anchor",
    "neighbour": "FXFV5-A6-P1-neigh",     # sham-calendar (+7d), same law
    "control": "FXFV5-A6-P1-ctrl",        # stale-calendar (c_prev)
    # kernel-internal benchmark (never a scored cell): the packet's
    # incremental_test bench schedule -- the same frozen c_prev law.
    "benchmark_treatment": "FXFV5-A6-P1-bench",
}
_ARM_SHORT = {"anchor": "an", "neighbour": "nh", "control": "ct",
              "benchmark_treatment": "bt"}

# --- frozen clocks -> pair map (evidence-dictated, packet universe) ------
ECONOMY_PAIR = {"GB": "GBP/USD", "CA": "USD/CAD", "AU": "AUD/USD",
                "NZ": "NZD/USD"}
PAIR_AREAS = {"GBP/USD": ("GB", "US"), "USD/CAD": ("US", "CA"),
              "AUD/USD": ("AU", "US"), "NZD/USD": ("NZ", "US")}
ECONOMY_ORDER = ("GB", "CA", "AU", "NZ")

# --- frozen single values (no_parameter_grid) ----------------------------
TRAILING_RETURN_SUM_NY_DAYS = 10   # the anchor reversal law, ALL arms
SHAM_SHIFT_CALENDAR_DAYS = 7       # neighbour's only presumption swap
STALENESS_MODE = "c_prev"          # control / benchmark_treatment
WARMUP_NY_CLOSES = 11              # 10-day return sum needs 11 closes
NOTIONAL_USD = 10000.0
S0_CAP_ENTRY_UTC = "2025-07-25T00:00:00+00:00"   # S0 window ends 2025-07-24
EXPECTED_CLOCK_COUNTS = {"GB": 88, "CA": 105, "AU": 23, "NZ": 30}
TOTAL_CLOCKS_PUBLISHED = 246
PERCENT_PER_ANNUM_TO_DECIMAL = 100.0

FINANCING_FORMULA_ID = "fx5_day_start_asof_policy_rate_diff_v5ledger_v1"
FINANCING_FORMULA = (
    "financing_adjusted_pnl = price_only_pnl + sign * notional_usd * "
    "(r_base - r_quote) * holding_days/365, accrued per calendar day at "
    "the day-start as-of policy-rate differential from the evidenced "
    "policy-rate vintages of the pinned V5-extension announcement ledger "
    "(sha256 cf1f01a7ec2d3d7506892c045139910937147df49d3742cc4ec72b36d20fd902); "
    "rows eligible only when available_time_utc <= the accrual instant "
    "(and effective_time_utc <= the accrual instant -- never eligible on "
    "their own effective date); accounting only, never a signal")

ALPHA_DEFINITION = "per_trade_expectancy_difference_v1"

REASON_NO_DECISION_BAR = "no_decision_bar_available"
REASON_F_MISSING = "f_missing_void"
REASON_X_MISSING = "x_missing_void"
REASON_S0_CAP = "s0_cap_excluded"
REASON_WARMUP_VOID = "warmup_void"
REASON_ZERO_DIRECTION = "exact_zero_direction"
REASON_FILL_LAG = "fill_lag_exceeds_4_days"
REASON_FOLD_VOID = "fold_window_voided"
REASON_FOLD_NO_ENTRY = "fold_boundary_no_entry"
REASON_SHAM_DROPPED = "sham_dropped"
REASON_NO_PREDECESSOR = "stale_no_predecessor_skipped"
REASON_GOVERNOR_OPEN = "governor_position_open_no_refresh"
REASON_GOVERNOR_DAY = "governor_same_ny_day_entry"

ALL_SKIPPED_REASONS = (
    REASON_NO_DECISION_BAR, REASON_F_MISSING, REASON_X_MISSING,
    REASON_S0_CAP, REASON_WARMUP_VOID, REASON_ZERO_DIRECTION,
    REASON_FILL_LAG, REASON_FOLD_VOID, REASON_FOLD_NO_ENTRY,
    REASON_SHAM_DROPPED, REASON_NO_PREDECESSOR, REASON_GOVERNOR_OPEN,
    REASON_GOVERNOR_DAY,
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


def load_clocks(path) -> list:
    """Load + verify the p3 conditioning clocks (fail closed).

    Every row must carry decision_date, available_time_utc, precision,
    reference_period and a 64-hex archive_sha256; the economy must be one
    of the four evidenced economies; the decision_date must lie inside the
    authority's own S0 window; (economy, decision_date) must be unique;
    the per-economy and total counts must equal BOTH the file header and
    the frozen published counts (GB 88 / CA 105 / AU 23 / NZ 30 = 246).
    A missing file or ANY malformed row raises DataBlocked: documented
    gaps fail closed, never inferred."""
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
        raise DataBlocked("conditioning clocks file carries no "
                          "per_economy_in_S0 header")
    s0 = payload.get("S0_window")
    if not isinstance(s0, dict) or "start" not in s0 or "end" not in s0:
        raise DataBlocked("conditioning clocks file carries no S0_window")

    clocks = []
    seen = set()
    counts = defaultdict(int)
    for i, row in enumerate(clocks_raw):
        if not isinstance(row, dict):
            raise DataBlocked(f"clock row {i}: not a mapping")
        economy = row.get("economy")
        if economy not in ECONOMY_PAIR:
            raise DataBlocked(f"clock row {i}: economy {economy!r} is not an "
                              "evidenced economy of this family")
        decision_date = row.get("decision_date")
        if not isinstance(decision_date, str):
            raise DataBlocked(f"clock row {i}: missing decision_date")
        try:
            dd = date.fromisoformat(decision_date)
        except ValueError as exc:
            raise DataBlocked(f"clock row {i}: unparsable decision_date "
                              f"{decision_date!r}") from exc
        if not (date.fromisoformat(str(s0["start"])) <= dd
                <= date.fromisoformat(str(s0["end"]))):
            raise DataBlocked(f"clock row {i}: decision_date {decision_date} "
                              "outside the authority's own S0 window")
        available = _parse_utc(row.get("available_time_utc"),
                               f"clock row {i} ({economy} {decision_date}) "
                               "available_time_utc")
        precision = row.get("precision")
        if not isinstance(precision, str) or not precision:
            raise DataBlocked(f"clock row {i}: missing precision")
        reference = row.get("reference_period")
        if not isinstance(reference, str) or not reference:
            raise DataBlocked(f"clock row {i}: missing reference_period")
        sha = row.get("archive_sha256")
        if (not isinstance(sha, str) or len(sha) != 64
                or any(ch not in "0123456789abcdef" for ch in sha.lower())):
            raise DataBlocked(f"clock row {i}: archive_sha256 missing or "
                              f"not a 64-hex digest: {sha!r}")
        key = (economy, decision_date)
        if key in seen:
            raise DataBlocked(f"clock row {i}: duplicate (economy, "
                              f"decision_date) {key}")
        seen.add(key)
        counts[economy] += 1
        clocks.append({"economy": economy, "decision_date": decision_date,
                       "available": available, "precision": precision,
                       "reference_period": reference,
                       "archive_sha256": sha})

    for economy in ECONOMY_ORDER:
        expected_header = header.get(economy)
        expected_frozen = EXPECTED_CLOCK_COUNTS[economy]
        if counts[economy] != expected_header \
                or counts[economy] != expected_frozen:
            raise DataBlocked(
                f"clock count mismatch for {economy}: file has "
                f"{counts[economy]}, header says {expected_header!r}, frozen "
                f"authority says {expected_frozen}")
    if len(clocks) != TOTAL_CLOCKS_PUBLISHED:
        raise DataBlocked(
            f"total clock count mismatch: parsed {len(clocks)}, frozen "
            f"authority says {TOTAL_CLOCKS_PUBLISHED}")
    total_header = payload.get("total_clocks_published")
    if total_header is not None and total_header != len(clocks):
        raise DataBlocked(
            f"header total_clocks_published {total_header!r} != parsed "
            f"{len(clocks)}")
    clocks.sort(key=lambda c: (c["available"], c["economy"],
                               c["decision_date"]))
    return clocks


# ------------------------------------------------------------------ #
# financing vintage reader (pinned V5-extension ledger; accounting    #
# only -- the ledger's RATE_CHANGE rows are never a signal)           #
# ------------------------------------------------------------------ #
def load_ledger_rows(path) -> list:
    if not isinstance(path, str) or not os.path.exists(path):
        raise DataBlocked(f"announcement ledger not found: {path!r}")
    rows = []
    with open(path, "r", encoding="utf-8") as handle:
        for ln, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except ValueError as exc:
                raise DataBlocked(f"announcement ledger line {ln}: "
                                  f"unparsable JSON ({exc})")
    if not rows:
        raise DataBlocked("announcement ledger is empty")
    return rows


def dedupe_ledger_rows(rows) -> list:
    """Canonical dedupe: (area, effective_date) LAST-ROW-WINS over the raw
    file, preserving first-sighting order of the surviving keys (the
    inherited pinned-ledger semantics; effective_date may be None for
    baseline-style rows -- first-sighting order keeps the result
    deterministic)."""
    dedup = {}
    order = []
    for row in rows:
        key = (row.get("area"), row.get("effective_date"))
        if key not in dedup:
            order.append(key)
        dedup[key] = row
    return [dedup[k] for k in order]


class LedgerVintageReader:
    """As-of policy-rate reader over the DEDUPED pinned ledger (inherited
    evidenced-vintages semantics).  ``policy_rate(area, t)`` returns the
    percent-per-annum level of the row with the LATEST effective instant
    subject to BOTH frozen gates: available_time_utc <= t AND
    effective_time_utc <= t (a rate is never read before it is in force
    and never before its availability stamp -- a day-start accrual can
    never read a row on the row's own effective date).  ``None`` =
    NO_EVAL (fail closed, never interpolated or fill-forwarded)."""

    def __init__(self, deduped_rows: list) -> None:
        by_area = defaultdict(list)
        for row in deduped_rows:
            area = row.get("area")
            ann = row.get("announcement") or {}
            raw_avail = ann.get("operative_available_time_utc")
            if raw_avail is None:
                continue  # never a readable vintage (fail-closed row)
            available = _parse_utc(raw_avail, f"{area} vintage availability")
            raw_eff = row.get("effective_time_utc")
            effective = (_parse_utc(raw_eff, f"{area} effective_time_utc")
                         if raw_eff is not None else None)
            value = row.get("new_value")
            if isinstance(value, bool) or not isinstance(value, (int, float)) \
                    or not math.isfinite(float(value)):
                raise DataBlocked(f"{area}: vintage value is not numeric")
            by_area[area].append((effective, available, float(value)))
        self._series = {}
        for area, rows in by_area.items():
            rows.sort(key=lambda r: (r[0] or datetime(1, 1, 1, tzinfo=UTC),
                                     r[1]))
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

    def differential(self, base_area: str, quote_area: str,
                     t: datetime) -> float | None:
        base = self.policy_rate(base_area, t)
        if base is None:
            return None
        quote = self.policy_rate(quote_area, t)
        if quote is None:
            return None
        return base - quote


def financing_adjustment(reader: LedgerVintageReader, pair: str,
                         trip: dict) -> float:
    """Frozen dual-book financing (packet formula, verbatim semantics):
    sign * notional * sum(day-start as-of differentials)/365 over the
    calendar days [entry fill date, exit fill date).  A missing eligible
    read at any accrual instant fails closed."""
    base_area, quote_area = PAIR_AREAS[pair]
    day = trip["entry_dt"].astimezone(UTC).date()
    last = trip["exit_dt"].astimezone(UTC).date()
    diffs = []
    while day < last:
        t = datetime(day.year, day.month, day.day, tzinfo=UTC)
        diff = reader.differential(base_area, quote_area, t)
        if diff is None:
            raise DataBlocked(
                f"{pair}: no eligible policy-rate vintage for accrual at "
                f"{_iso(t)}")
        diffs.append(diff / PERCENT_PER_ANNUM_TO_DECIMAL)
        day += timedelta(days=1)
    return trip["side"] * NOTIONAL_USD * math.fsum(diffs) / 365.0


# ------------------------------------------------------------------ #
# price snapshot (authorized H1 research series ONLY; inherited       #
# loader semantics mirrored verbatim)                                 #
# ------------------------------------------------------------------ #
def _parse_stamp(raw) -> datetime:
    try:
        return datetime.strptime(raw, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
    except (TypeError, ValueError) as exc:
        raise DataBlocked(f"unparsable H1 bar stamp {raw!r}") from exc


def load_h1_bars(h1_dir: str, pair: str) -> dict:
    """One pair's completed H1 bars from the authorized snapshot: provider
    no-data windows are empty; malformed files, conflicting duplicate
    stamps and non-positive prices fail closed."""
    sym = pair.replace("/", "")
    paths = sorted(glob.glob(os.path.join(h1_dir, f"{sym}_1h_*.json")))
    if not paths:
        raise DataBlocked(f"no H1 snapshot files for {pair} under {h1_dir}")
    bars = {}
    for path in paths:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, ValueError) as exc:
            raise DataBlocked(f"unreadable H1 snapshot file {path}: {exc}")
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
                    f"H1 snapshot file {path} row is not a parseable bar: {exc}")
            if any(not math.isfinite(v) or v <= 0 for v in ohlc):
                raise DataBlocked(
                    f"H1 snapshot file {path} has a non-positive/non-finite bar")
            if stamp in bars and bars[stamp] != ohlc:
                raise DataBlocked(
                    f"conflicting duplicate H1 bar at {stamp.isoformat()}")
            bars[stamp] = ohlc
    if not bars:
        raise DataBlocked(f"H1 snapshot for {pair} holds no bars")
    return bars


# ------------------------------------------------------------------ #
# NY-day calendar (16:00 America/New_York; DST-aware via zoneinfo)    #
# ------------------------------------------------------------------ #
def ny_decision_stamp(ny_day: date) -> datetime:
    """UTC instant of the 16:00 America/New_York bar of an NY calendar day
    (20:00Z EDT / 21:00Z EST via zoneinfo -- DST-aware, never fixed
    offsets)."""
    return datetime(ny_day.year, ny_day.month, ny_day.day, 16, 0,
                    tzinfo=NY_TZ).astimezone(UTC)


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


def force_flat_indices(existing: list) -> set:
    """Indices of the last existing decision bar STRICTLY BEFORE each
    internal kernel fold boundary (the bar whose OPEN is the boundary
    force-flat exit bar).  A boundary beyond the snapshot's last bar
    produces no force-flat bar (data end closes every position first).
    Exposed for the fold geometry goldens; the schedule walk reads the
    fold geometry directly via :func:`fold_exit_resolution`."""
    out = set()
    for boundary in INTERNAL_BOUNDARIES:
        b = datetime.fromisoformat(boundary)
        if not any(s >= b for s in existing):
            continue
        candidates = [i for i, s in enumerate(existing) if s < b]
        if candidates:
            out.add(max(candidates))
    return out


# ------------------------------------------------------------------ #
# the frozen reversal law                                             #
# ------------------------------------------------------------------ #
def trailing_return_sum(closes) -> float:
    """x = sum of the 10 most recent daily log returns over the given
    completed 16:00-NY closes (all STRICTLY BEFORE the decision bar).
    ``closes`` must hold exactly n+1 = 11 closes (fail-closed warmup)."""
    closes = list(closes)
    n = TRAILING_RETURN_SUM_NY_DAYS
    if len(closes) != n + 1:
        raise DataBlocked(
            f"warmup violated: the trailing {n}-day return sum needs exactly "
            f"{n + 1} completed closes strictly before the decision bar, "
            f"got {len(closes)}")
    return math.fsum(math.log(closes[j] / closes[j - 1])
                     for j in range(1, len(closes)))


def direction_of(x: float) -> int:
    """direction = -sign(x); an EXACT zero is NO_TRADE (fail-closed)."""
    if x > 0.0:
        return -1
    if x < 0.0:
        return 1
    return 0


# ------------------------------------------------------------------ #
# window resolution (F / D / X around one availability instant)       #
# ------------------------------------------------------------------ #
def resolve_window(a: datetime, existing: list):
    """(reason, (d_idx, f_idx, x_idx)) for availability instant ``a`` over
    the pair's existing decision bars: F = last bar strictly before a,
    D = the bar one session before F, X = first bar strictly after a.
    Any missing leg -> (reason, None) -- a voided clock, never inferred.
    Mechanically enforces F < a < X."""
    f_idx = bisect.bisect_left(existing, a) - 1  # last stamp < a
    if f_idx < 0:
        return REASON_F_MISSING, None
    if f_idx == 0:
        return REASON_NO_DECISION_BAR, None
    x_idx = bisect.bisect_right(existing, a)    # first stamp > a
    if x_idx >= len(existing):
        return REASON_X_MISSING, None
    if not (existing[f_idx] < a < existing[x_idx]):  # pragma: no cover
        raise DataBlocked(  # mechanical invariant, unreachable by bisect
            f"window invariant violated: F={_iso(existing[f_idx])} "
            f"a={_iso(a)} X={_iso(existing[x_idx])}")
    return None, (f_idx - 1, f_idx, x_idx)


def warmup_closes(existing: list, bars: dict, d_idx: int):
    """The 11 completed closes strictly before the decision bar (the
    frozen warmup: the 10-day return sum needs 11 closes), or None (void
    -- never fill-forward)."""
    need = TRAILING_RETURN_SUM_NY_DAYS + 1
    if d_idx < need:
        return None
    return [bars[existing[j]][3] for j in range(d_idx - need, d_idx)]


def fold_exit_resolution(f_idx: int, x_idx: int, a: datetime,
                         existing: list):
    """Fold force-flat resolution for a raw window [F, X].  Returns
    (reason, exit_idx, force_flat): a window that would cross an internal
    kernel boundary exits at the last bar strictly before the boundary
    (force_flat=True -- the truncated exit is itself strictly before the
    boundary, so a scheduled trade can never span it and the kernel's
    FOLD_FORCE_FLAT_VIOLATION backstop can never fire); a truncation that
    would break F < a < exit VOIDS the clock (a shortened window must
    never be emitted -- the span property IS the mechanism)."""
    for boundary in INTERNAL_BOUNDARIES:
        b = datetime.fromisoformat(boundary)
        f_ts, x_ts = existing[f_idx], existing[x_idx]
        if not (f_ts < b <= x_ts):
            continue
        ff_idx = max(i for i, s in enumerate(existing) if s < b)
        if ff_idx <= f_idx:
            return REASON_FOLD_NO_ENTRY, None, False
        if existing[ff_idx] <= a:
            return REASON_FOLD_VOID, None, False
        return None, ff_idx, True
    return None, x_idx, False


# ------------------------------------------------------------------ #
# arm target schedules                                                #
# ------------------------------------------------------------------ #
def _all_clocks(clocks_by_economy: dict) -> list:
    out = []
    for economy in ECONOMY_ORDER:
        out.extend(clocks_by_economy.get(economy, []))
    return out


def arm_targets(arm: str, clocks_by_economy: dict, skipped: dict) -> list:
    """[(clock, availability_instant)] whose window the arm trades, in the
    arm's frozen schedule:
      anchor      every published clock at its evidenced instant;
      neighbour   every clock shifted +7 calendar days (same time-of-day);
      control /
      benchmark_treatment
                  each economy's clocks[1:] traded at the PREVIOUS clock's
                  evidenced instant (c_prev anchoring; the first clock per
                  economy has no predecessor and is skipped, counted)."""
    if arm == "anchor":
        return [(c, c["available"]) for c in _all_clocks(clocks_by_economy)]
    if arm == "neighbour":
        shift = timedelta(days=SHAM_SHIFT_CALENDAR_DAYS)
        return [(c, c["available"] + shift)
                for c in _all_clocks(clocks_by_economy)]
    if arm in ("control", "benchmark_treatment"):
        targets = []
        for economy in ECONOMY_ORDER:
            clocks = clocks_by_economy.get(economy, [])
            if clocks:
                skipped[REASON_NO_PREDECESSOR] = \
                    skipped.get(REASON_NO_PREDECESSOR, 0) + 1
            # every trade anchored to the SAME economy's PREVIOUS evidenced
            # clock: target clock c_i (i >= 1) trades c_{i-1}'s window --
            # decision, fill and exit instants all derived from c_prev's
            # window (the target carries c_prev's availability instant).
            for prev, c in zip(clocks, clocks[1:]):
                targets.append((c, prev["available"]))
        return targets
    raise ValueError(f"arm must be one of {sorted(ARM_IDS)}, got {arm!r}")


# ------------------------------------------------------------------ #
# family API entry point                                              #
# ------------------------------------------------------------------ #
def run_arm(arm: str, data_paths: dict, macro_reader=None, freeze_token=None):
    """Frozen family API (runner contract of the inherited V3 kernel).

    ``macro_reader`` and ``freeze_token`` are accepted per the contract and
    intentionally unused: the conditioning authority is
    data_paths['conditioning_clocks'] (p3_conditioning_clocks_v5.json) and
    the financing input is data_paths['announcement_ledger'] (the pinned
    V5-extension ledger), accounting only.

    Returns {"decisions": [...], "financing_events": [...], "meta": {...}}.
    """
    arm_id = ARM_IDS.get(arm)
    if arm_id is None:
        raise ValueError(f"arm must be one of {sorted(ARM_IDS)}, got {arm!r}")
    if not isinstance(data_paths, dict):
        raise DataBlocked("data_paths must be a mapping")
    for key in ("price_h1_dir", "conditioning_clocks", "announcement_ledger"):
        if not isinstance(data_paths.get(key), str):
            raise DataBlocked(f"data_paths is missing the {key!r} path")

    clocks = load_clocks(data_paths["conditioning_clocks"])
    clocks_by_economy = {e: [c for c in clocks if c["economy"] == e]
                         for e in ECONOMY_ORDER}
    all_instants = sorted(c["available"] for c in clocks)

    rows = load_ledger_rows(data_paths["announcement_ledger"])
    deduped = dedupe_ledger_rows(rows)
    reader = LedgerVintageReader(deduped)

    skipped = {reason: 0 for reason in ALL_SKIPPED_REASONS}
    targets = arm_targets(arm, clocks_by_economy, skipped)
    short = _ARM_SHORT[arm]
    s0_cap = datetime.fromisoformat(S0_CAP_ENTRY_UTC)

    decisions = []
    financing_events = []
    schedule_totals = {}

    for economy in ECONOMY_ORDER:
        pair = ECONOMY_PAIR[economy]
        bars = load_h1_bars(data_paths["price_h1_dir"], pair)
        existing = existing_decision_bars(bars)
        counts = {reason: 0 for reason in
                  ("candidates", "round_trips", "decision_bars",
                   "no_refresh_ignored", REASON_NO_DECISION_BAR,
                   REASON_F_MISSING, REASON_X_MISSING, REASON_S0_CAP,
                   REASON_WARMUP_VOID, REASON_ZERO_DIRECTION,
                   REASON_FILL_LAG, REASON_FOLD_VOID,
                   REASON_FOLD_NO_ENTRY, REASON_SHAM_DROPPED)}
        counts["decision_bars"] = len(existing)

        pair_targets = [t for t in targets if t[0]["economy"] == economy]
        pair_targets.sort(key=lambda t: (t[1], t[0]["available"],
                                         t[0]["decision_date"]))
        counts["candidates"] = len(pair_targets)

        n_round_trips = 0
        last_exit_ts = None       # the open position's scheduled exit
        last_entry_day = None     # governor: max 1 entry per pair per NY-day

        for clock, a in pair_targets:
            # 1) availability-lagged window resolution (fail-closed voids)
            reason, window = resolve_window(a, existing)
            if reason is not None:
                counts[reason] += 1
                skipped[reason] += 1
                continue
            d_idx, f_idx, x_idx = window

            # 2) family-side S0 cap (counted): the window must complete
            #    inside the clocks authority's S0 window -- a clock is
            #    excluded when its entry instant is at/after the cap or its
            #    exit bar (the first post-release session) would fall after
            #    the cap (2025-07-25T00:00:00Z)
            if existing[f_idx] >= s0_cap or existing[x_idx] > s0_cap:
                counts[REASON_S0_CAP] += 1
                skipped[REASON_S0_CAP] += 1
                continue

            # 3) warmup: 11 completed closes strictly before D (never
            #    inferred, never fill-forwarded)
            warm = warmup_closes(existing, bars, d_idx)
            if warm is None:
                counts[REASON_WARMUP_VOID] += 1
                skipped[REASON_WARMUP_VOID] += 1
                continue

            # 4) the frozen reversal law: direction = -sign(trailing sum);
            #    an EXACT zero is NO_TRADE (fail-closed)
            side = direction_of(trailing_return_sum(warm))
            if side == 0:
                counts[REASON_ZERO_DIRECTION] += 1
                skipped[REASON_ZERO_DIRECTION] += 1
                continue

            # 5) fold force-flat truncation (span-preserving) or void
            reason, exit_idx, force_flat = fold_exit_resolution(
                f_idx, x_idx, a, existing)
            if reason is not None:
                counts[reason] += 1
                skipped[reason] += 1
                continue

            # 6) neighbour (sham-calendar) validity: no evidenced clock of
            #    ANY evidenced economy strictly inside the sham window
            if arm == "neighbour":
                f_ts, x_ts = existing[f_idx], existing[exit_idx]
                if any(f_ts < inst < x_ts for inst in all_instants):
                    counts[REASON_SHAM_DROPPED] += 1
                    skipped[REASON_SHAM_DROPPED] += 1
                    continue

            # 7) one-event lag: F must be the next session after D, within
            #    the frozen 4-day next-session constraint (fail-closed)
            if existing[f_idx] - existing[d_idx] > timedelta(
                    days=MAX_FILL_LAG_DAYS):
                counts[REASON_FILL_LAG] += 1
                skipped[REASON_FILL_LAG] += 1
                continue

            # 8) governor (deterministic, PIT-safe): blocked -> NO_TRADE,
            #    never deferred
            entry_ts = existing[f_idx]
            if last_exit_ts is not None and entry_ts < last_exit_ts:
                counts["no_refresh_ignored"] += 1
                skipped[REASON_GOVERNOR_OPEN] += 1
                continue
            entry_day = entry_ts.astimezone(NY_TZ).date()
            if last_entry_day == entry_day:
                skipped[REASON_GOVERNOR_DAY] += 1
                continue

            # 9) schedule + emit the round trip (fills at the OPEN of the
            #    entry/exit bars; deterministic id)
            trip = {"d_idx": d_idx, "f_idx": f_idx, "exit_idx": exit_idx,
                    "side": side, "force_flat": force_flat,
                    "economy": economy,
                    "decision_date": clock["decision_date"]}
            dec = _decision_of(pair, existing, bars, trip, short)
            trip_full = dict(trip,
                             entry_dt=existing[f_idx],
                             exit_dt=existing[exit_idx])
            adjustment = financing_adjustment(reader, pair, trip_full)
            financing_events.append({
                "decision_id": dec["decision_id"],
                "financing_adjustment_usd": adjustment,
                "formula": FINANCING_FORMULA_ID,
            })
            decisions.append(dec)
            n_round_trips += 1
            last_exit_ts = existing[exit_idx]
            last_entry_day = entry_day

        counts["round_trips"] = n_round_trips
        schedule_totals[pair] = counts

    meta = {
        "decision_clock": "daily",
        "proposal_id": PROPOSAL_ID,
        "family_id": PROPOSAL_ID,
        "cycle_id": CYCLE_ID,
        "alpha_definition": ALPHA_DEFINITION,
        "arm_id": arm_id,
        "warmup_daily_bars": WARMUP_NY_CLOSES,
        "fill_delay_events": {},
        "financing_formula": FINANCING_FORMULA,
        "clock_counters": {
            "published_clocks": len(clocks),
            "arm_candidates": len(targets),
            "skipped_no_predecessor": skipped[REASON_NO_PREDECESSOR],
            "sham_dropped": skipped[REASON_SHAM_DROPPED],
            "s0_cap_excluded": skipped[REASON_S0_CAP],
            "warmup_void": skipped[REASON_WARMUP_VOID],
            "exact_zero_direction": skipped[REASON_ZERO_DIRECTION],
            "fold_window_voided": skipped[REASON_FOLD_VOID],
            "fold_boundary_no_entry": skipped[REASON_FOLD_NO_ENTRY],
            "missing_decision_bar": skipped[REASON_NO_DECISION_BAR],
            "missing_f": skipped[REASON_F_MISSING],
            "missing_x": skipped[REASON_X_MISSING],
            "fill_lag_refused": skipped[REASON_FILL_LAG],
            "governor_blocked_open": skipped[REASON_GOVERNOR_OPEN],
            "governor_blocked_same_day": skipped[REASON_GOVERNOR_DAY],
        },
        "economy_clock_counts": {
            e: len(clocks_by_economy.get(e, [])) for e in ECONOMY_ORDER},
        "skipped_counts": {k: v for k, v in sorted(skipped.items())},
        "schedule_totals": schedule_totals,
        "frozen_constants": {
            "trailing_return_sum_ny_days": TRAILING_RETURN_SUM_NY_DAYS,
            "sham_shift_calendar_days": SHAM_SHIFT_CALENDAR_DAYS,
            "staleness_mode": (STALENESS_MODE if arm in
                               ("control", "benchmark_treatment") else None),
            "s0_cap_entry_utc": S0_CAP_ENTRY_UTC,
            "notional_usd_unit": NOTIONAL_USD,
            "clocks_pair_map": dict(ECONOMY_PAIR),
        },
    }
    return {"decisions": decisions, "financing_events": financing_events,
            "meta": meta}


def _decision_of(pair, existing, bars, tr, short):
    """Decision payload (runner contract): fills at the OPEN of the entry/
    exit bars; deterministic ids embedding arm, economy, clock date and
    decision-bar instant."""
    d_idx, f_idx, x_idx = tr["d_idx"], tr["f_idx"], tr["exit_idx"]
    tag = pair.replace("/", "")
    return {
        "decision_id": f"{PROPOSAL_ID}-{short}-{tag}-{tr['economy']}-"
                       f"{tr['decision_date']}-{_iso(existing[d_idx])}",
        "pair": pair,
        "side": tr["side"],
        "decision_ts": _iso(existing[d_idx]),
        "notional_usd": NOTIONAL_USD,
        "entry_bar_ts": _iso(existing[f_idx]),
        "entry_price": bars[existing[f_idx]][0],
        "exit_bar_ts": _iso(existing[x_idx]),
        "exit_price": bars[existing[x_idx]][0],
        "force_flat": tr["force_flat"],
    }
