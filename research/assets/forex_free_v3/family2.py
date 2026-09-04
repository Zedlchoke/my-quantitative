"""FOREX-FREE-V3 family2: FXFV3-A6-P1 -- realized-volatility regime-gated
policy-rate-differential carry at the daily 16:00-New-York decision clock.

Binding spec: research/proposals/forex_free_v3/a6_lane/proposal_1.{json,md}
(SELECTED family2, cycle FOREX-FREE-V3).  This module implements the frozen
family API contract documented in
research/assets/forex_free_v3/scored_runner.py (module docstring)::

    run_arm(arm, data_paths, macro_reader, freeze_token=None)
        -> {"decisions": [...], "financing_events": [...], "meta": {...}}

Arms (exactly three, per the spec):
  "anchor"                  LOW-vol state holds the as-of policy-rate
                            differential direction (+1 long base / -1 short
                            base); HIGH unwinds to flat; a direction flip
                            reverses at the same fill.
  "neighbour"               byte-identical to the anchor except the state
                            input is the close-to-close daily log-return
                            sample std (same LOW-tail presumption, different
                            estimator; same 20-day blocks / 10 baseline
                            blocks / 220-NY-day warmup).
  "causal_negative_control" (driver shorthand "control"): byte-identical to
                            the anchor except direction is read from a SHAM
                            leg-pair under the FROZEN derangement (base and
                            quote legs each rotated +2 positions along the
                            frozen pair order).  Deterministic by
                            construction: the rotation is a fixed constant,
                            never runtime randomness.

Frozen law (proposal pit_observables / arms, implemented here verbatim):

* Decision instant T = the completed daily 16:00 America/New_York flat H1
  bar of a Mon-Fri NY day (bar stamps 20:00Z in EDT / 21:00Z in EST via
  zoneinfo, never fixed offsets).  One decision per pair per NY trading day.
* rr_d = (sum of H1 true ranges of all bars in NY-day d's window) / (close
  of d's 16:00-NY bar), where d's window is the completed bars strictly
  after the previous enumerated NY weekday's 16:00-NY decision bar through
  d's own decision bar.  TR_t = max(high-low, |high-close_{t-1}|,
  |low-close_{t-1}|) on consecutive completed H1 bars; the first window bar
  chains off the previous decision bar's close.  All of d's window bars must
  exist, consecutive at hourly steps except the single structural weekend
  close (Fri->Mon), else the day is invalid (fail-closed).
* vol_state: S_T = mean of rr over the 20 most recent COMPLETED (valid)
  NY-days ending at d; B_T = median of the 10 prior non-overlapping 20-day
  block means (median of 10 = mean of the two middle order statistics);
  LOW iff S_T < B_T strictly (S_T == B_T => HIGH, no position).  Requires
  220 completed valid NY-days, else NO_EVAL.  The neighbour replaces rr with
  the sample std (ddof=1) of the 19 daily close-to-close log returns inside
  each 20-day window (identical warmup and blocks).
* direction_i(T) = sign(asof_diff_i(T)) read EXCLUSIVELY through the
  availability-gated ``macro_reader`` (available_time_utc <= T enforced by
  the reader; never bypassed, never backfilled).  Missing leg or exact zero
  => NO_EVAL for that pair-day.
* Entry/exit fills at the OPEN of the next EXISTING 16:00-NY bar after the
  decision (one-event lag; a missing next bar skips the action fail-closed
  and records a skipped decision).  No same-bar fills.
* Fold boundaries (2022-05-01, 2024-07-01 UTC, the runner's internal
  boundaries) force flat: an open position exits at the OPEN of the last
  decision day's 16:00-NY bar before the boundary (force_flat=true); an
  entry whose fill would land on that bar is suppressed.  No position
  crosses a fold boundary.
* Financing (frozen formula, baseline_invariants.json v3_financing_formula):
  financing_adjusted_pnl = price_only_pnl + sign * notional_usd *
  (r_base - r_quote) * holding_days/365, accrued per calendar day at the
  day-start as-of differential (weekend days carry the most recent prior
  weekday decision instant).  Adopted vintages carry percent-per-annum
  values; the differential is converted to annualized decimals (/100)
  exactly once at the family financing boundary.  DISCLOSED APPROXIMATION:
  policy rates are unsecured official rates, NOT swap/OIS-implied rollover
  (HISTORICAL_ROLLOVER_FINANCING UNAVAILABLE_FAIL_CLOSED).

Determinism: same inputs -> byte-identical output (sorted iteration only,
no wall clock, no runtime randomness; canonical JSON of the payload is
stable).  Fail-closed everywhere: missing bars/vintages/warmup are NO_EVAL
or BLOCKED_DATA, never fabricated, never fill-forwarded.

Price input: the authorized H1 research snapshot only (TwelveData-derived
JSON files ``{SYMBOL}_1h_*.json`` under ``data_paths["h1_dir"]``).  D1
series, bid/ask and rollover data are never read.  Schedule-only counting
(:func:`schedule_counts`) exposes decision counts WITHOUT any PnL and
without macro data for feasibility replays.
"""
from __future__ import annotations

import bisect
import glob
import json
import math
import os
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

__all__ = [
    "PROPOSAL_ID",
    "PAIR_UNIVERSE",
    "PAIR_ORDER",
    "PAIR_AREAS",
    "SHAM_LEGS",
    "FINANCING_FORMULA_ID",
    "DataBlocked",
    "run_arm",
    "schedule_counts",
    "ny_day_validity",
    "state_is_low",
    "derangement_sham_legs",
]

PROPOSAL_ID = "FXFV3-A6-P1"

NY_TZ = ZoneInfo("America/New_York")
UTC = timezone.utc

PAIR_UNIVERSE = ("EUR/USD", "GBP/USD", "AUD/USD", "NZD/USD",
                 "USD/JPY", "USD/CHF", "USD/CAD")
PAIR_ORDER = PAIR_UNIVERSE  # frozen derangement order (spec arms.control)
# Area mapping for the 8 currency areas backing the 7 pairs (BIS WS_CBPOL).
PAIR_AREAS = {
    "EUR/USD": ("EMU", "US"),
    "GBP/USD": ("GB", "US"),
    "AUD/USD": ("AU", "US"),
    "NZD/USD": ("NZ", "US"),
    "USD/JPY": ("US", "JP"),
    "USD/CHF": ("US", "CH"),
    "USD/CAD": ("US", "CA"),
}
DERANGEMENT_ROTATION = 2  # frozen: sham legs = pair_order[(i+2) mod 7]

# Frozen family constants (proposal single_frozen_parameter_set).
STATE_BLOCK_NY_DAYS = 20
BASELINE_BLOCKS = 10
WARMUP_VALID_NY_DAYS = STATE_BLOCK_NY_DAYS * (BASELINE_BLOCKS + 1)  # 220

NOTIONAL_USD = 10000
FINANCING_FORMULA_ID = "V3_FROZEN_POLICY_RATE_CARRY"
FINANCING_FORMULA_VERBATIM = (
    "financing_adjusted_pnl = price_only_pnl + sign * notional_usd * "
    "(r_base - r_quote) * holding_days/365, accrued per calendar day at the "
    "day-start as-of differential; sign=+1 for long base/short quote, "
    "-1 for short base/long quote")
FINANCING_APPROXIMATION = (
    "policy rates are unsecured official rates, NOT swap/OIS-implied "
    "rollover; disclosed ex ante (HISTORICAL_ROLLOVER_FINANCING "
    "UNAVAILABLE_FAIL_CLOSED)")

# Internal fold boundaries (runner FOLD_BOUNDARIES[1:3]; baseline_invariants
# folds[1:3]).  Positions never cross these instants.
INTERNAL_BOUNDARIES = (datetime(2022, 5, 1, tzinfo=UTC),
                       datetime(2024, 7, 1, tzinfo=UTC))

_ARM_IDS = {
    "anchor": "anchor",
    "neighbour": "neighbour",
    "control": "causal_negative_control",
    "causal_negative_control": "causal_negative_control",
}
_ARM_SHORT = {"anchor": "AN", "neighbour": "NE",
              "causal_negative_control": "CT"}


BLOCKED_DATA = "BLOCKED_DATA"


class DataBlocked(RuntimeError):
    """A required price-snapshot input is missing/malformed; fail closed."""

    reason = BLOCKED_DATA

    def __init__(self, detail: str) -> None:
        super().__init__(f"{BLOCKED_DATA}: {detail}")
        self.detail = detail


# ------------------------------------------------------------------ #
# frozen derangement (deterministic; no runtime randomness anywhere)  #
# ------------------------------------------------------------------ #
def derangement_sham_legs(pair: str) -> tuple[str, str]:
    """SHAM leg-pair for ``pair``: base and quote legs each rotated +2
    positions along the frozen pair order (spec arms.control
    sham_derangement_frozen).  Pure function of the frozen constant; the
    recorded 'seed' IS this fixed rotation.  Identity-free by construction
    (asserted)."""
    if pair not in PAIR_ORDER:
        raise DataBlocked(f"pair {pair!r} outside the frozen 7-pair universe")
    i = PAIR_ORDER.index(pair)
    j = (i + DERANGEMENT_ROTATION) % len(PAIR_ORDER)
    sham = PAIR_AREAS[PAIR_ORDER[j]]
    if sham == PAIR_AREAS[pair]:
        raise DataBlocked(  # pragma: no cover - frozen constant is a derangement
            "sham derangement maps a pair to itself; refusing")
    return sham


SHAM_LEGS = {p: derangement_sham_legs(p) for p in PAIR_ORDER}


# ------------------------------------------------------------------ #
# price snapshot loading (authorized H1 research series ONLY)         #
# ------------------------------------------------------------------ #
def _parse_stamp(raw: str) -> datetime:
    try:
        return datetime.strptime(raw, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
    except (TypeError, ValueError) as exc:
        raise DataBlocked(f"unparsable H1 bar stamp {raw!r}") from exc


def load_h1_bars(h1_dir: str, pair: str) -> dict[datetime, tuple]:
    """Load one pair's completed H1 bars from the authorized snapshot.

    Returns {utc stamp: (open, high, low, close)}.  Provider no-data
    responses (TwelveData error payloads) are empty windows, not errors;
    malformed files, conflicting duplicate stamps and non-positive prices
    fail closed.  File order is sorted for determinism."""
    sym = pair.replace("/", "")
    paths = sorted(glob.glob(os.path.join(h1_dir, f"{sym}_1h_*.json")))
    if not paths:
        raise DataBlocked(f"no H1 snapshot files for {pair} under {h1_dir}")
    bars: dict[datetime, tuple] = {}
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
# NY-day calendar: decision stamps, day validity, rr series            #
# ------------------------------------------------------------------ #
def ny_decision_stamp(ny_day: date) -> datetime:
    """UTC instant of the 16:00 America/New_York bar of NY calendar day."""
    return datetime(ny_day.year, ny_day.month, ny_day.day, 16, 0, tzinfo=NY_TZ).astimezone(UTC)


def enumerate_decision_days(bars: dict[datetime, tuple]) -> list[datetime]:
    """All Mon-Fri 16:00-NY decision stamps inside the bar range.

    This reproduces the A9-F measured enumeration exactly (weekday bars
    whose America/New_York wall time is 16:00); provider weekend-stamped
    bars are outside the session week and never enumerated."""
    if not bars:
        return []
    lo, hi = min(bars), max(bars)
    day = lo.astimezone(NY_TZ).date() - timedelta(days=1)
    end = hi.astimezone(NY_TZ).date() + timedelta(days=1)
    out = []
    while day <= end:
        if day.weekday() < 5:
            t = ny_decision_stamp(day)
            if lo <= t <= hi:
                out.append(t)
        day += timedelta(days=1)
    return out


def window_stamps(sorted_stamps: list, bars: dict[datetime, tuple],
                  prev_stamp: datetime, stamp: datetime) -> list:
    """Weekday-UTC stamps of the completed bars in (prev_stamp, stamp].

    Provider Sat/Sun-UTC-stamped artifacts are excluded (outside the
    session week); Monday-early-UTC stamps (Sunday evening NY) are kept --
    they are the week's first bars."""
    lo = bisect.bisect_right(sorted_stamps, prev_stamp)
    hi = bisect.bisect_right(sorted_stamps, stamp)
    return [s for s in sorted_stamps[lo:hi] if s.weekday() < 5]


def ny_day_validity(sorted_stamps: list, bars: dict[datetime, tuple],
                    prev_stamp: datetime, stamp: datetime) -> tuple[bool, str]:
    """Fail-closed NY-day validity for the window (prev_stamp, stamp].

    Valid iff: the previous decision bar exists (TR chain anchor), the
    window's weekday bars run consecutive at hourly steps from the window
    head to ``stamp`` -- with the single structural weekend close (a
    Fri->Mon gap, allowed at the head when prev is a Friday) as the ONLY
    permitted jump.  Returns (valid, reason)."""
    if stamp not in bars:
        return False, "MISSING_DECISION_BAR"
    if prev_stamp not in bars:
        return False, "MISSING_PREV_DECISION_BAR"
    present = window_stamps(sorted_stamps, bars, prev_stamp, stamp)
    if not present:
        return False, "EMPTY_WINDOW"
    head_ok = (present[0] == prev_stamp + timedelta(hours=1)) or \
              (prev_stamp.weekday() == 4 and present[0].weekday() == 0)
    if not head_ok:
        return False, "WINDOW_HEAD_HOLE"
    if present[-1] != stamp:
        return False, "WINDOW_TAIL_HOLE"
    jumps = 0
    for a, b in zip(present, present[1:]):
        if b - a != timedelta(hours=1):
            jumps += 1
            if jumps > 1 or not (a.weekday() == 4 and b.weekday() == 0):
                return False, "WINDOW_INTERNAL_GAP"
    return True, "OK"


def true_range(ohlc: tuple, prev_close: float) -> float:
    high, low = ohlc[1], ohlc[2]
    return max(high - low, abs(high - prev_close), abs(low - prev_close))


def rr_of_day(sorted_stamps: list, bars: dict[datetime, tuple],
              prev_stamp: datetime, stamp: datetime) -> float:
    """rr_d = sum of window true ranges / close of the decision bar.

    Callers must ensure :func:`ny_day_validity` passed for this window."""
    prev_close = bars[prev_stamp][3]
    acc = []
    for s in window_stamps(sorted_stamps, bars, prev_stamp, stamp):
        acc.append(true_range(bars[s], prev_close))
        prev_close = bars[s][3]
    return math.fsum(acc) / bars[stamp][3]


def _median10(values: list) -> float:
    """Median of the 10 block statistics: mean of the two middle order
    statistics (frozen convention for an even count)."""
    if len(values) != BASELINE_BLOCKS:
        raise ValueError("median10 requires exactly 10 block values")
    s = sorted(values)
    return (s[4] + s[5]) / 2.0


def _sample_std(values: list) -> float:
    """Sample std, ddof=1 (frozen neighbour estimator)."""
    n = len(values)
    if n < 2:
        raise ValueError("sample std requires >= 2 values")
    mean = math.fsum(values) / n
    return math.sqrt(math.fsum((v - mean) ** 2 for v in values) / (n - 1))


def state_is_low(block_values: list, prior_blocks: list, *, estimator: str) -> bool:
    """Frozen median split: LOW iff S_T < B_T strictly (S == B => HIGH).

    ``estimator`` is "mean" (anchor: block values are rr means) or "std"
    (neighbour: S_T is the current-window std; prior_blocks are block stds).
    ``block_values`` is the current 20-day window statistic sequence;
    ``prior_blocks`` the 10 prior block statistics."""
    if estimator == "mean":
        s_t = math.fsum(block_values) / len(block_values)
        b_t = _median10(prior_blocks)
    elif estimator == "std":
        s_t = _sample_std(block_values)
        b_t = _median10(prior_blocks)
    else:
        raise ValueError(f"unknown estimator {estimator!r}")
    return s_t < b_t


class PairSeries:
    """Per-pair derived calendar/state inputs (price history ONLY).

    Build once per pair per run; every field is deterministic from the H1
    snapshot.  ``valid`` flags fail-closed NY-day validity; ``rr`` holds the
    anchor state input; ``closes`` the 16:00-NY closes for the neighbour.
    ``valid_idx`` lists indices of valid days in order (the state walk)."""

    def __init__(self, pair: str, bars: dict[datetime, tuple]) -> None:
        self.pair = pair
        self.bars = bars
        self.stamps = enumerate_decision_days(bars)
        self._stamps_sorted = sorted(bars)
        self.has_bar = [s in bars for s in self.stamps]
        self.valid = [False] * len(self.stamps)
        self.rr: list = [None] * len(self.stamps)
        self.closes: list = [None] * len(self.stamps)
        for i, s in enumerate(self.stamps):
            if s in bars:
                self.closes[i] = bars[s][3]
        for i in range(1, len(self.stamps)):
            ok, _ = ny_day_validity(self._stamps_sorted, bars,
                                    self.stamps[i - 1], self.stamps[i])
            if ok:
                self.valid[i] = True
                self.rr[i] = rr_of_day(self._stamps_sorted, bars,
                                       self.stamps[i - 1], self.stamps[i])
        self.valid_idx = [i for i, v in enumerate(self.valid) if v]
        self._valid_pos = {i: k for k, i in enumerate(self.valid_idx)}

    def window_bars(self, prev_stamp: datetime, stamp: datetime) -> list:
        return window_stamps(self._stamps_sorted, self.bars, prev_stamp, stamp)

    def next_bar_index(self, i: int) -> int | None:
        """Index of the next enumerated day AFTER i whose decision bar
        exists (the one-event-lag fill bar), or None."""
        for j in range(i + 1, len(self.stamps)):
            if self.has_bar[j]:
                return j
        return None

    def vol_state(self, i: int, estimator: str) -> bool | None:
        """LOW/HIGH state at valid day i; None = NO_EVAL (short warmup).

        Requires i itself valid and 220 completed valid NY-days ending at
        i.  Reads price history only (rr series / closes), never prices
        after i and never macro data."""
        if not self.valid[i]:
            return None
        k = self._valid_pos[i]
        if k + 1 < WARMUP_VALID_NY_DAYS:
            return None
        cur = self.valid_idx[k - STATE_BLOCK_NY_DAYS + 1: k + 1]
        if estimator == "mean":
            block = [self.rr[j] for j in cur]
            prior = []
            for b in range(1, BASELINE_BLOCKS + 1):
                blk = self.valid_idx[
                    k - STATE_BLOCK_NY_DAYS * b - STATE_BLOCK_NY_DAYS + 1:
                    k - STATE_BLOCK_NY_DAYS * b + 1]
                prior.append(math.fsum(self.rr[j] for j in blk) / len(blk))
            return math.fsum(block) / len(block) < _median10(prior)
        if estimator == "std":
            closes = [self.closes[j] for j in cur]
            rets = [math.log(closes[m + 1] / closes[m]) for m in range(len(closes) - 1)]
            prior = []
            for b in range(1, BASELINE_BLOCKS + 1):
                blk = self.valid_idx[
                    k - STATE_BLOCK_NY_DAYS * b - STATE_BLOCK_NY_DAYS + 1:
                    k - STATE_BLOCK_NY_DAYS * b + 1]
                cs = [self.closes[j] for j in blk]
                prior.append(_sample_std(
                    [math.log(cs[m + 1] / cs[m]) for m in range(len(cs) - 1)]))
            return _sample_std(rets) < _median10(prior)
        raise ValueError(f"unknown estimator {estimator!r}")

    def state_evaluable(self, i: int) -> bool:
        """True when day i is valid with the full 220-valid-day warmup."""
        return bool(self.valid[i]) and \
            self._valid_pos.get(i, -1) + 1 >= WARMUP_VALID_NY_DAYS


# ------------------------------------------------------------------ #
# force-flat bookkeeping (internal fold boundaries)                    #
# ------------------------------------------------------------------ #
def _force_flat_day_indices(stamps: list) -> set[int]:
    """Indices of the last decision day BEFORE each internal boundary (the
    bar whose OPEN is the boundary force-flat exit bar)."""
    out = set()
    for boundary in INTERNAL_BOUNDARIES:
        candidates = [i for i, s in enumerate(stamps) if s < boundary]
        if candidates:
            out.add(max(candidates))
    return out


# ------------------------------------------------------------------ #
# schedule machine (shared by run_arm and schedule_counts)             #
# ------------------------------------------------------------------ #
def _iso(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%S+00:00")


# Adopted BIS WS_CBPOL / ECB SDMX EXR vintages carry percent-per-annum
# values (unit "percent_per_annum"); the frozen financing formula requires
# annualized DECIMALS, so the family converts at its boundary exactly once.
PERCENT_PER_ANNUM_TO_DECIMAL = 100.0


def _sign_or_none(diff):
    if diff is None:
        return None
    if diff > 0:
        return 1
    if diff < 0:
        return -1
    return None  # exact zero => no direction, pair-day NO_EVAL


def _schedule_pair(series: PairSeries, arm: str, direction_of):
    """Walk one pair's decision days through the frozen holding law.

    ``direction_of(day_index)`` -> +1/-1/None.  Returns
    (round_trips, skipped, counts) where round_trips are raw decision
    payloads (financing not yet attached), skipped is the fail-closed
    skipped-decision list, counts the schedule bookkeeping."""
    stamps = series.stamps
    ff_days = _force_flat_day_indices(stamps)
    estimator = "std" if arm == "neighbour" else "mean"
    trips: list = []
    skipped: list = []
    pos = None  # {"decision_i","side","fill_i"}
    counts = {"decision_days_evaluated": 0, "state_no_eval": 0,
              "direction_no_eval": 0, "missing_next_fill_bar": 0,
              "fold_boundary_no_entry": 0, "end_of_data_no_exit": 0}
    for i, ts in enumerate(stamps):
        if not series.has_bar[i]:
            continue
        nb = series.next_bar_index(i)
        # 1) force-flat: an open position exits at THIS bar's open.
        if i in ff_days and pos is not None:
            trips.append({"decision_i": pos["decision_i"], "entry_i": pos["fill_i"],
                          "exit_i": i, "side": pos["side"], "force_flat": True})
            pos = None
        # 2) decision read at this bar (day must be valid + warm + eligible).
        if not series.state_evaluable(i):
            if series.valid[i] and nb is not None:
                counts["state_no_eval"] += 1
            continue
        counts["decision_days_evaluated"] += 1
        direction = direction_of(i)
        low = series.vol_state(i, estimator)
        if direction is None:
            counts["direction_no_eval"] += 1
        if nb is None:
            # No next 16:00-NY bar exists: every fill fails closed.  An open
            # position is unresolvable and is recorded once after the walk.
            if pos is None and low is True and direction is not None:
                counts["missing_next_fill_bar"] += 1
                skipped.append({"pair": series.pair, "decision_ts": _iso(ts),
                                "reason": "MISSING_NEXT_FILL_BAR"})
            continue
        # 3) holding law.
        if pos is not None:
            if low is False:  # HIGH unwinds
                trips.append({"decision_i": pos["decision_i"], "entry_i": pos["fill_i"],
                              "exit_i": nb, "side": pos["side"], "force_flat": False})
                pos = None
            elif direction is not None and direction != pos["side"]:
                # direction flip reverses at the same fill
                trips.append({"decision_i": pos["decision_i"], "entry_i": pos["fill_i"],
                              "exit_i": nb, "side": pos["side"], "force_flat": False})
                pos = {"decision_i": i, "side": direction, "fill_i": nb}
            # LOW with same direction (or unreadable direction) => hold
        if pos is None and low is True and direction is not None:
            if nb in ff_days:
                counts["fold_boundary_no_entry"] += 1
                skipped.append({"pair": series.pair, "decision_ts": _iso(ts),
                                "reason": "FOLD_BOUNDARY_NO_ENTRY"})
            else:
                pos = {"decision_i": i, "side": direction, "fill_i": nb}
        # flat + HIGH / flat + NO_EVAL => no action (absence, never side 0)
    if pos is not None:
        counts["end_of_data_no_exit"] += 1
        skipped.append({"pair": series.pair,
                        "decision_ts": _iso(stamps[pos["decision_i"]]),
                        "reason": "END_OF_DATA_NO_EXIT"})
    return trips, skipped, counts


def _decisions_of(series: PairSeries, trips: list, arm: str) -> list:
    stamp = series.stamps
    out = []
    short = _ARM_SHORT[_ARM_IDS[arm]]
    for tr in trips:
        di, ei, xi = tr["decision_i"], tr["entry_i"], tr["exit_i"]
        out.append({
            "decision_id": f"{PROPOSAL_ID}-{short}-{series.pair.replace('/', '')}-{_iso(stamp[di])}",
            "pair": series.pair,
            "side": tr["side"],
            "decision_ts": _iso(stamp[di]),
            "notional_usd": NOTIONAL_USD,
            "entry_bar_ts": _iso(stamp[ei]),
            "entry_price": series.bars[stamp[ei]][0],
            "exit_bar_ts": _iso(stamp[xi]),
            "exit_price": series.bars[stamp[xi]][0],
            "force_flat": tr["force_flat"],
        })
    return out


def _financing_adjustment(macro_reader, series: PairSeries, trip: dict) -> float:
    """sign * notional * sum(day-start as-of differentials)/365 over the
    calendar days [entry fill date, exit fill date).  Weekend days carry
    the most recent prior weekday decision instant.  Availability gating is
    enforced by the reader at each (past) instant; a missing read fails
    closed (never fabricated, never interpolated)."""
    stamps = series.stamps
    entry_ts = stamps[trip["entry_i"]]
    exit_ts = stamps[trip["exit_i"]]
    base_area, quote_area = PAIR_AREAS[series.pair]
    day = entry_ts.astimezone(NY_TZ).date()
    last = exit_ts.astimezone(NY_TZ).date()
    diffs = []
    while day < last:
        if day.weekday() < 5:
            t = ny_decision_stamp(day)
        else:
            prior = [s for s in stamps if s.astimezone(NY_TZ).date() < day]
            if not prior:
                raise DataBlocked(f"no prior decision instant for weekend accrual {day}")
            t = prior[-1]
        diff = macro_reader.differential(base_area, quote_area, t)
        if diff is None:
            raise DataBlocked(
                f"missing eligible policy-rate vintage for accrual at {_iso(t)}")
        diffs.append(diff / PERCENT_PER_ANNUM_TO_DECIMAL)
        day += timedelta(days=1)
    return trip["side"] * NOTIONAL_USD * math.fsum(diffs) / 365.0


# ------------------------------------------------------------------ #
# family API entry point                                               #
# ------------------------------------------------------------------ #
def run_arm(arm: str, data_paths: dict, macro_reader, freeze_token=None):
    """Frozen family API (see module docstring).  ``freeze_token`` is
    accepted per the runner contract and intentionally unused here: the
    runner owns scored/dry-run semantics; the family branches on nothing."""
    arm_id = _ARM_IDS.get(arm)
    if arm_id is None:
        raise ValueError(f"family2 arm must be one of "
                         f"'anchor'/'neighbour'/'control'/'causal_negative_control', "
                         f"got {arm!r}")
    if not isinstance(data_paths, dict) or not isinstance(data_paths.get("h1_dir"), str):
        raise DataBlocked("data_paths is missing the 'h1_dir' H1 snapshot directory")
    if macro_reader is None:
        raise DataBlocked("run_arm requires an availability-gated macro_reader")

    use_sham = arm_id == "causal_negative_control"
    decisions: list = []
    financing_events: list = []
    skipped: list = []
    schedule_totals = {}
    for pair in PAIR_UNIVERSE:
        bars = load_h1_bars(data_paths["h1_dir"], pair)
        series = PairSeries(pair, bars)

        if use_sham:
            base_area, quote_area = SHAM_LEGS[pair]
        else:
            base_area, quote_area = PAIR_AREAS[pair]

        def direction_of(i, _s=series, _b=base_area, _q=quote_area):
            return _sign_or_none(macro_reader.differential(_b, _q, _s.stamps[i]))

        trips, pair_skipped, counts = _schedule_pair(series, arm_id, direction_of)
        skipped.extend(pair_skipped)
        pair_decisions = _decisions_of(series, trips, arm_id)
        for trip, dec in zip(trips, pair_decisions):
            adjustment = _financing_adjustment(macro_reader, series, trip)
            financing_events.append({"decision_id": dec["decision_id"],
                                     "financing_adjustment_usd": adjustment,
                                     "formula": FINANCING_FORMULA_ID})
        decisions.extend(pair_decisions)
        schedule_totals[pair] = {
            "decision_bars": sum(series.has_bar),
            "valid_ny_days": sum(series.valid),
            "invalid_ny_days": len(series.stamps) - sum(series.valid),
            "decision_days_evaluated": counts["decision_days_evaluated"],
            "state_no_eval": counts["state_no_eval"],
            "direction_no_eval": counts["direction_no_eval"],
            "missing_next_fill_bar": counts["missing_next_fill_bar"],
            "fold_boundary_no_entry": counts["fold_boundary_no_entry"],
            "end_of_data_no_exit": counts["end_of_data_no_exit"],
            "round_trips": len(pair_decisions),
        }

    meta = {
        "decision_clock": "daily",
        "proposal_id": PROPOSAL_ID,
        "pair_universe": list(PAIR_UNIVERSE),
        "arm_id": f"{PROPOSAL_ID}-"
                  + {"anchor": "anchor", "neighbour": "neigh",
                     "causal_negative_control": "ctrl"}[arm_id],
        "decision_bar_convention": "completed H1 bar whose America/New_York wall "
                                   "time is 16:00, Mon-Fri only (20:00Z EDT / "
                                   "21:00Z EST via zoneinfo); fill at the OPEN of "
                                   "the next existing 16:00-NY bar (one-event lag)",
        "vol_regime_window": {
            "state_block_ny_days": STATE_BLOCK_NY_DAYS,
            "baseline_blocks": BASELINE_BLOCKS,
            "warmup_completed_valid_ny_days": WARMUP_VALID_NY_DAYS,
            "anchor_measure": "S_T = mean(rr over the last 20 completed valid "
                              "NY-days); B_T = median of the 10 prior "
                              "non-overlapping 20-day block means; LOW iff "
                              "S_T < B_T strictly (S_T == B_T => HIGH)",
            "neighbour_measure": "S_T = sample std (ddof=1) of the 19 daily "
                                 "close-to-close log returns within the last 20 "
                                 "completed valid NY-days; B_T = median of the 10 "
                                 "prior block stds; LOW iff S_T < B_T strictly",
            "rr": "sum of H1 true ranges of all bars in the NY-day window "
                  "(previous 16:00-NY decision bar, day's 16:00-NY decision "
                  "bar] divided by the day's 16:00-NY close; window bars must "
                  "be consecutive hourly except the single Fri->Mon weekend "
                  "close, else the day is invalid (fail-closed)",
            "source": "price history ONLY (authorized H1 snapshot); never macro",
        },
        "sham_derangement": {
            "rule": "sham_base_i = base[(i+2) mod 7], sham_quote_i = "
                    "quote[(i+2) mod 7] along the frozen pair order",
            "seed": f"FROZEN rotate+{DERANGEMENT_ROTATION} (deterministic; "
                    "no runtime randomness)",
            "mapping": {p: list(SHAM_LEGS[p]) for p in PAIR_UNIVERSE},
        },
        "financing": {
            "formula": FINANCING_FORMULA_VERBATIM,
            "formula_id": FINANCING_FORMULA_ID,
            "units": "adopted vintages are percent-per-annum; the "
                     "differential is converted to annualized decimals "
                     "(/100) exactly once at the family financing boundary; "
                     "the direction sign is unit-invariant",
            "accrual": "per calendar day at the day-start as-of differential "
                       "(weekend days carry the most recent prior weekday "
                       "decision instant; reads availability-gated via the "
                       "macro reader at past instants only)",
            "disclosed_approximation": FINANCING_APPROXIMATION,
        },
        "macro_source": "adopted BIS WS_CBPOL policy-rate vintages read "
                        "exclusively through the availability-gated "
                        "PolicyRateReader (ECB SDMX EXR declared fallback); "
                        "available_time_utc <= decision T enforced by the "
                        "reader, never bypassed",
        "skipped_decisions": skipped,
        "skipped_counts": _sorted_counts(skipped),
        "schedule_totals": schedule_totals,
        "usd_index_daily_returns": None,
        "usd_index_note": "deferred to scoring integration: the frozen D1 "
                          "equal-weight USD-index daily-return formula is "
                          "supplying-side metadata; the runner owns the "
                          "correlation statistic and its frozen gate",
    }
    return {"decisions": decisions, "financing_events": financing_events,
            "meta": meta}


def _sorted_counts(skipped: list) -> dict:
    out: dict = {}
    for item in skipped:
        out[item["reason"]] = out.get(item["reason"], 0) + 1
    return dict(sorted(out.items()))


# ------------------------------------------------------------------ #
# schedule-only replay (counts, no PnL, no macro needed)               #
# ------------------------------------------------------------------ #
def schedule_counts(data_paths: dict) -> dict:
    """Schedule-only feasibility counts from the price snapshot ONLY.

    Never computes PnL and never reads macro data.  Per pair and per arm it
    counts the pair-days whose frozen schedule completes a state evaluation
    (valid day, 220-valid-day warmup met, next fill bar exists) -- the
    per-arm decision counts of the proposal's minimum_decisions contract.
    The three arms share the state-evaluability calendar, so the counts
    coincide by construction; the vol STATE differs per arm (anchor/control
    range-based, neighbour close-to-close) and is NOT evaluated here."""
    if not isinstance(data_paths, dict) or not isinstance(data_paths.get("h1_dir"), str):
        raise DataBlocked("data_paths is missing the 'h1_dir' H1 snapshot directory")
    pairs = {}
    totals = {a: 0 for a in ("anchor", "neighbour", "causal_negative_control")}
    total_bars = total_valid = 0
    for pair in PAIR_UNIVERSE:
        bars = load_h1_bars(data_paths["h1_dir"], pair)
        series = PairSeries(pair, bars)
        eligible = 0
        first_220 = None
        first_decision = None
        for k, i in enumerate(series.valid_idx):
            if k + 1 == WARMUP_VALID_NY_DAYS:
                first_220 = _iso(series.stamps[i])
            if k + 1 >= WARMUP_VALID_NY_DAYS and series.next_bar_index(i) is not None:
                eligible += 1
                if first_decision is None:
                    first_decision = _iso(series.stamps[i])
        bar_count = sum(series.has_bar)
        # A9-F bar-counting basis: the (n+1)-th weekday decision bar.
        bar_activation = _iso(series.stamps[WARMUP_VALID_NY_DAYS]) \
            if len(series.stamps) > WARMUP_VALID_NY_DAYS else None
        pairs[pair] = {
            "decision_bars_present": bar_count,
            "valid_ny_days": sum(series.valid),
            "invalid_ny_days": len(series.stamps) - sum(series.valid),
            "first_day_with_220_valid_history": first_220,
            "first_schedule_decision": first_decision,
            "bar_counting_activation_221st_bar": bar_activation,
            "schedule_decision_days": eligible,
        }
        for a in totals:
            totals[a] += eligible
        total_bars += bar_count
        total_valid += sum(series.valid)
    return {
        "pairs": pairs,
        "per_arm_decision_counts": totals,
        "totals": {"decision_bars_present": total_bars,
                   "valid_ny_days": total_valid},
        "no_pnl": True,
        "no_macro_read": True,
    }
