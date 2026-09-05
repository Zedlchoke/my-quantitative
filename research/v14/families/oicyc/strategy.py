"""Frozen strategy primitives for the A14-V14-A8-OICYC family (V14 I lane).

This module implements the FROZEN contract of the V14 selection freeze
(``research/control/v14_run/selection_freeze_v14.json``, family
``A14-V14-A8-OICYC``) + the mechanism definition
``research/proposals/v14/a8/OICYC.md`` verbatim -- no tuning, no grids, no
parameter changes.  It is a pure, data-injected library: every observable
(daily staged OI rows, completed 15m bars, funding settlements, tick sizes)
is supplied by the caller, so the same primitives run on synthetic fixtures
and on the read-only workspace snapshot.  Nothing here reads the catalog,
computes a scored outcome, or persists anything.

Frozen arms (exactly three, proposal section 6 -- the selection freeze's
"OICYC anchor" shorthand is the proposal's ``CYC-28D`` arm id):

* anchor   ``CYC-28D``     -- ``CYC_s(T)`` = OLS slope of the symbol's daily
  log OI change on the contemporaneous LEAVE-ONE-OUT aggregate of the other
  18 tradeable symbols' daily log OI changes, over the 28 most recent paired
  daily changes whose end-row stamps are <= T (a 29-row window); long the
  lowest-CYC tercile, short the highest-CYC tercile;
* neighbour ``CYC-14D``    -- identical construction over the 14 most recent
  paired daily changes (a 15-row window);
* causal negative control ``CTL-OISHARE`` -- rank (descending presentation)
  on ``SH_s(T)`` = mean over the 28 most recent daily rows <= T of the
  symbol's OWN SHARE of the staged-universe aggregate OI; long the
  lowest-share tercile, short the highest-share tercile.  The control
  contains NO differencing, NO regression and NO OI-flow direction: it
  retains the mechanical dominance exposure and deletes every co-movement
  estimate.  It is never promotable; if it passes Stage-A while the anchor
  passes, the family is FALSIFIED (proposal section 6, preregistered).

SIGNAL (PIT, frozen p_freeze_v14 authority -- a decision at T reads only
records whose availability stamp is <= T; for staged OI the availability
stamp IS the row's own ``create_time``, read PER ROW and never assumed to be
23:55Z -- A9F-OBS-7 documents 48-59 of 417 days per symbol landing earlier):

* ``dlog_s(d) = ln(OI_s(d) / OI_s(d-1))`` over consecutive daily rows,
  stamped at the END row, defined iff both rows are present, positive and
  finite.  For every day in a window ALL 19 tradeable symbols must have
  rows (the aggregate needs a complete cross-section); any missing row
  fails the window CLOSED (symbol INELIGIBLE at that stamp, no back-fill,
  no partial aggregate).  Consecutive-ness is by day-row index, never by
  calendar-day arithmetic (stamps are read per row).
* ``M(d)`` = mean over the other 18 tradeable symbols' ``dlog_j(d)``
  (LEAVE-ONE-OUT: the regressand never appears in the regressor).
* ``CYC_s(T)`` = ``Cov(dlog_s, M) / Var(M)`` over the window (ddof=1),
  defined iff ``Var(M) > 0``.
* ``SH_s(T)`` = mean own share of the aggregate OI level over the 28 most
  recent daily rows <= T (complete cross-section per row; positive finite
  levels).

BOOK (hysteresis, proposal section 5, implemented as frozen): rank eligible
symbols by the arm signal (ascending on the value for all three arms, so
the LONG side is always the low-value tercile -- for the control that is
exactly the proposal's "long lowest-share tercile"; the frozen "rank
DESCENDING on SH_s" presentation is carried in the payload diagnostics as
``ranks_desc`` with rank 1 = highest share).  With ``n`` eligible names the
terciles are ``n // 3`` each: lowest tercile = long-ENTRY zone, highest
tercile = short-ENTRY zone, middle = BUFFER; the median rank is
``(n + 1) // 2``.  A flat symbol enters its entry zone's side.  A HELD side
EXITS ONLY WHEN THE RANK CROSSES BEYOND THE MEDIAN (a held long whose rank
rises above the median flips short; a held short whose rank falls below the
median flips long; a long at or below the median and a short at or above it
are held -- including through the buffer).  Exit = flip to the opposite
side, mirroring the frozen V13 hysteresis-family convention with the exit
band pinned at the median (the proposal's own, tighter-than-V13 band).
Equal weight per side ``min(0.5 / n_side, 0.30)``; a side with < 2 members
leaves its budget in cash (no renormalisation); gross <= 1.0 and
``|w| <= 0.30`` at every stamp BY CONSTRUCTION.  Side membership < 4 at a
stamp -> that stamp's rebalance is SKIPPED and the previous book is held
(fail-closed, no position-zeroing inference); a held symbol that lost
eligibility likewise skips the stamp; a flat start without a well-formed
book raises :class:`EligibilityShortfall` (a stamp without a well-formed
book has NO book).

UNIVERSE / CLOCK / FOLDS (proposal section 5):

* universe: the 19 tradeable symbols = frozen ``REQUIRED_SYMBOLS`` of
  ``research/v12/data_contract.py`` MINUS ``BTCUSDT``; BTCUSDT is the
  context benchmark ONLY (never ranked, never held, never inside the
  aggregate);
* window: blind-S0 screen window 2025-08-22..2026-08-21; OI warmup pool at
  the first stamp = 55 daily rows (2025-07-01..2025-08-21 pre-screen plus
  2025-08-22..24) = 54 daily changes -- anchor needs 29 rows, neighbour 15,
  control 28 rows; asserted fail-closed;
* decision clock: DISCRETIONARY decisions weekly Monday 00:00:00Z (first
  2025-08-25, last 2026-08-17; 52 scheduled) -- the DAILY conditioning is
  refreshed from the daily OI path at every stamp, which is where the daily
  cadence is load-bearing; the weekly clock satisfies the frozen
  <= 60 discretionary decisions/365d feasibility floor
  (``research/v11/cost_feasibility.py``).  Fold-terminal force-flat actions
  are counted and reported separately from discretionary decisions;
* folds: chronological F0/F1/F2 on the pinned calendar with the frozen
  1-day purge realised as a CALENDAR ZONE ``[end - 1d, end)`` (the measured
  V13 convention: exactly one stamp, 2026-04-20, falls inside F1's purge
  zone, leaving 51 effective Mondays at 17/17/17 -- the same counts the
  V14 D2 feasibility audit measured for this family);
* execution lag (ONE, declared): orders release at ``T + 15m``; the fill
  reference is the OPEN price of the FIRST completed 15m bar whose
  slot-open instant is >= the release instant (the 00:15Z slot for a Monday
  00:00:00Z decision).  Stress "+1 event delay" shifts the fill to the next
  15m bar's open.  The fill's readability horizon is its slot-open instant.

CONFIRMATORY STATUS (plan Section 1.1, proposal sections 2/12): this family
is preregistered CONFIRMATORY (shadow-region entry: the sign region was
observed in the V12 ``OILEV-V2-28D-FLOW-W-INV`` control arm, +0.758 raw).
Every payload carries the status so the driver records it in the verdict
and in the observed/published denominator accounting; every Stage-A gate
applies unrelaxed; positive raw PnL never overrides failed incremental
context or a firing control.

No module here computes a scored PnL.
"""

from __future__ import annotations

import math
from typing import Any, Iterable, Mapping, Optional, Sequence

from research.adapter_v10.protocol import (
    AdapterError,
    ContractViolation,
    StrategyIdentity,
)
from research.contract_v10 import (
    ADVERSE_TICKS_SLIPPAGE_FLOOR_V10,
    FILL_CLOCK_V10,
    TAKER_FEE_FLOOR_BPS_V10,
)
from research.v11.families.oilever_delev.strategy import (
    BAR_INTERVAL_NS,
    DAY_NS,
    FOLD_WINDOWS,
    HOUR_NS,
    iso_utc,
    parse_iso_utc,
    weekly_mondays,
)
from research.v11.publication_identity import arm_config_digest

# --------------------------------------------------------------------------- #
# Frozen identity (fields pinned by the V14 selection freeze / OICYC.md)
# --------------------------------------------------------------------------- #
FAMILY_ID = "A14-V14-A8-OICYC"
STRATEGY_ID = "hyp_a14_v14_a8_oicyc"
#: Long/short cross-sectional book; BTCUSDT is benchmark-excluded (context
#: only) and the BTC-beta context is a Stage-A scoring concern, never a leg.
DIRECTION = "long_short"
BENCHMARK_SYMBOL = "BTCUSDT"
MATRIX_COHORT_HINT = "v14"

WINDOW_START_ISO = "2025-08-22T00:00:00Z"
WINDOW_END_ISO = "2026-08-21T00:00:00Z"

FUNDING_SIGN_CONVENTION = "LONG_PAYS_POSITIVE_RATE"

ANCHOR_ARM = "CYC-28D"
NEIGHBOUR_ARM = "CYC-14D"
CONTROL_ARM = "CTL-OISHARE"

#: Arm id -> frozen role (selection_freeze_v14.json ``arms`` semantics).
ARM_ROLES: dict[str, str] = {
    ANCHOR_ARM: "anchor",
    NEIGHBOUR_ARM: "neighbour",
    CONTROL_ARM: "causal_negative_control",
}
ARM_IDS: tuple[str, ...] = tuple(sorted(ARM_ROLES))

#: Digest-bearing ``arm_config_id`` per arm.
ARM_CONFIG_IDS: dict[str, str] = {
    ANCHOR_ARM: "28D",
    NEIGHBOUR_ARM: "14D",
    CONTROL_ARM: "OISHARE",
}

#: Preregistered CONFIRMATORY status (plan Section 1.1; proposal sections
#: 2/12).  Carried by every payload, the plugin metadata surface and the
#: gate runner so the driver records it in the verdict and denominator.
CONFIRMATORY = "CONFIRMATORY"
SECTION_1_1_DISCLOSURE = (
    "shadow-region entry per PLAN_crypto_v14.md Section 1.1: the sign region "
    "was observed in the V12 OILEV-V2-28D-FLOW-W-INV causal control arm "
    "(+0.758 raw vs anchor -0.821); preregistered CONFIRMATORY status is "
    "recorded in the verdict record and in the observed/published "
    "denominator accounting; own falsification control CTL-OISHARE; "
    "|rho| <= 0.20 vs the OILEV-V2 anchor AND its inverted control "
    "(A7-N measured 0.0112, PASS); no gate relaxation"
)

#: Frozen per-arm signal spec: ``(signal_kind, window_rows, long_low_value)``.
#:   * ``cycle_slope``  -- CYC_s = OLS slope of dlog_s on the leave-one-out
#:     aggregate over ``window_rows`` daily rows (``window_rows - 1``
#:     changes); long = LOW slope;
#:   * ``own_share``    -- SH_s = mean own share of the aggregate OI level
#:     over ``window_rows`` daily rows; long = LOW share (the frozen
#:     "descending" rank presentation is diagnostics-only, see module
#:     docstring).
_ARM_SIGNAL: dict[str, tuple[str, int]] = {
    ANCHOR_ARM: ("cycle_slope", 29),
    NEIGHBOUR_ARM: ("cycle_slope", 15),
    CONTROL_ARM: ("own_share", 28),
}

#: Frozen schedule / folds strings (pinned V12 fold calendar).
DECISION_CLOCK = (
    "discretionary decisions weekly Monday 00:00:00Z (52 scheduled, 51 "
    "effective after the 1-day calendar-zone purge); DAILY conditioning "
    "refreshed from the daily staged-OI path with availability = the row's "
    "own create_time (read per row, never assumed); ONE declared execution "
    "lag (slot-open fill at T+15m)"
)
FOLDS_CONTRACT = (
    "chronological 3-fold force-flat per the pinned V12 fold calendar "
    "(F0 2025-08-22..2025-12-21, F1 2025-12-22..2026-04-21, "
    "F2 2026-04-22..2026-08-21) with the frozen 1-day purge as a CALENDAR "
    "ZONE [end - 1d, end) -- the measured V13 convention, exactly one stamp "
    "(2026-04-20) purged, 51 effective Mondays at 17/17/17; per-family cell "
    "matrices derived from the family's own folds contract (L-V11-1)"
)
PURGE_DAYS = 1
MIN_FOLDS = 3

#: Declared cost floors (contract_v10, inherited unchanged; identical to
#: every scored crypto family since V10 -- never loosened).
TAKER_FEE_FLOOR_BPS = float(TAKER_FEE_FLOOR_BPS_V10)
ADVERSE_TICK_SLIP_FLOOR = int(ADVERSE_TICKS_SLIPPAGE_FLOOR_V10)
FILL_CLOCK = FILL_CLOCK_V10

#: Pinned book constants (OICYC.md section 5, verbatim numbers).
LEG_GROSS = 0.5
CAP_MAX = 0.30
MIN_SIDE_MEMBERS = 4
#: Structural tercile floor: both sides need >= 4 of n//3 members.
MIN_ELIGIBLE = 12
#: The tradeable cohort size the frozen aggregate is built from.
TRADEABLE_UNIVERSE_SIZE = 19

#: Pinned signal constants (OICYC.md sections 4/6, verbatim numbers).
WINDOW_ROWS_ANCHOR = 29          # 28 paired daily changes
WINDOW_ROWS_NEIGHBOUR = 15       # 14 paired daily changes
WINDOW_ROWS_CONTROL = 28         # 28 daily rows for the mean own share
WARMUP_ROWS_FIRST_STAMP = 55     # daily rows available at 2025-08-25T00:00Z
FIRST_STAMP_ISO = "2025-08-25T00:00:00Z"

#: The ONE declared execution lag: orders release T + 15 minutes and fill at
#: the slot-open of the first 15m bar at/after release (00:15Z for a Monday
#: 00:00:00Z decision).  Stress "+1 event delay" shifts to the NEXT slot.
ORDER_RELEASE_LAG_NS = 900_000_000_000  # 15 minutes == one 15m slot

STATUS_OK = "OK"

#: Preregistered causal-control falsification rule (OICYC.md section 6,
#: verbatim decision table; encoded for the gate runner).
CONTROL_GATE_PASS = "CONTROL_GATE_PASS"
CONTROL_GATE_FALSIFIED = "FAMILY_FALSIFIED_CONTROL_REPRODUCES_ANCHOR"


# --------------------------------------------------------------------------- #
# Availability gate (the pinned fill/decision readability convention)
# --------------------------------------------------------------------------- #
class LookaheadViolation(ContractViolation):
    """An input with availability stamp > the readable horizon was consumed."""


def assert_inputs_available(
    availability_stamps: Iterable[int],
    *,
    as_of_ns: int,
    context: str,
) -> None:
    """Fail closed if any consumed input is available after ``as_of_ns``.

    THE pinned convention (p_freeze_v14 PIT authority; OICYC.md section 4):
    a decision at T reads only records with availability <= T, and a fill at
    slot-open F reads only records with availability <= F (a record stamped
    00:30Z is NOT readable by the 00:15Z fill -- e.g. the covering bar's own
    close).  Availability for these native observables is the record's own
    stamp (bar close boundary / staged-OI ``create_time`` / funding
    settlement stamp); retrieval time never substitutes (crypto_compat
    semantics).
    """
    horizon = int(as_of_ns)
    for raw in availability_stamps:
        stamp = int(raw)
        if stamp > horizon:
            raise LookaheadViolation(
                f"{context}: consumed input available at {iso_utc(stamp)} > "
                f"readable horizon {iso_utc(horizon)} (fail-closed)"
            )


# --------------------------------------------------------------------------- #
# PIT feature primitives (fail-closed; availability stamp == record stamp)
# --------------------------------------------------------------------------- #
def _finite_positive(value: float) -> bool:
    v = float(value)
    return v > 0.0 and v == v and v not in (float("inf"), float("-inf"))


def readable_rows(
    series: Sequence[tuple[int, float]], stamp_ns: int
) -> list[tuple[int, float]]:
    """The staged-OI rows whose OWN stamps are <= the decision stamp.

    Availability = the row's own ``create_time`` (the day's LAST 5-minute
    metrics snapshot; typically 23:55:00Z, occasionally earlier on partial
    days -- stamps are read per row, never assumed).  Series must be
    strictly increasing; duplicates raise.
    """
    stamp = int(stamp_ns)
    out: list[tuple[int, float]] = []
    last: Optional[int] = None
    for ts, value in series:
        t = int(ts)
        if last is not None and t <= last:
            raise ContractViolation(
                f"staged OI series must be strictly increasing at {iso_utc(t)}"
            )
        last = t
        if t > stamp:
            break  # availability-ordered; later rows are unreadable at T
        out.append((t, float(value)))
    return out


def warmup_rows_at(series: Sequence[tuple[int, float]], stamp_ns: int) -> int:
    """Count of staged daily OI rows readable at ``stamp_ns``."""
    return len(readable_rows(series, int(stamp_ns)))


def assert_first_stamp_warmup(
    oi_by_symbol: Mapping[str, Sequence[tuple[int, float]]],
    *,
    universe: Sequence[str],
    first_stamp_ns: int | None = None,
) -> dict[str, int]:
    """Fail closed unless the frozen 55-row warmup pool exists at stamp 1.

    OICYC.md section 4: the pre-screen OI warmup pool is 2025-07-01..
    2025-08-21 (52 daily rows) plus 2025-08-22..24, i.e. 55 daily rows
    available at the first decision stamp 2025-08-25T00:00Z; the anchor
    needs 29 rows, the neighbour 15 and the control 28 -- all fit with
    margin.  A shorter pool is a data insufficiency (fail closed, never
    back-filled).
    """
    stamp = int(first_stamp_ns) if first_stamp_ns is not None else parse_iso_utc(FIRST_STAMP_ISO)
    counts: dict[str, int] = {}
    for sym in sorted(str(s) for s in universe):
        series = oi_by_symbol.get(str(sym)) or ()
        count = warmup_rows_at(series, stamp)
        if count < WARMUP_ROWS_FIRST_STAMP:
            raise ContractViolation(
                f"{sym}: only {count} daily OI rows available at the frozen "
                f"first stamp {iso_utc(stamp)}; the frozen warmup pool "
                f"requires >= {WARMUP_ROWS_FIRST_STAMP} (fail-closed)"
            )
        counts[str(sym)] = count
    return counts


def day_index(ts_ns: int) -> int:
    """The UTC day bucket of a row stamp (the staged daily metrics day)."""
    return int(ts_ns) // DAY_NS


def daily_log_changes(
    series: Sequence[tuple[int, float]], stamp_ns: int
) -> dict[int, Optional[float]]:
    """Consecutive daily log changes with END-row stamp <= the decision stamp.

    Maps ``end_row_DAY_INDEX -> dlog`` (or ``None`` for a BROKEN pair: a
    missing/non-positive/non-finite level).  Rows are aligned by their UTC
    DAY bucket -- each symbol carries EXACTLY ONE row per day (the day's
    LAST 5-minute metrics snapshot; the staging manifest pins 417/417 day
    rows with zero gaps/duplicates and a duplicate day row refuses) -- and
    consecutive-ness is by DAY-ROW INDEX, never by calendar arithmetic and
    never by exact-stamp equality (A9F-OBS-7: the day's last snapshot can
    land before 23:55Z; stamps are read per row, never assumed).  Only
    rows whose own stamps are <= T are read (availability per row).
    """
    rows = readable_rows(series, int(stamp_ns))
    by_day: dict[int, tuple[int, float]] = {}
    for ts, value in rows:
        d = day_index(ts)
        if d in by_day:
            raise ContractViolation(
                f"staged OI series carries two rows for UTC day index {d} "
                "(manifest pins one row per day); refusing"
            )
        by_day[d] = (int(ts), float(value))
    days = sorted(by_day)
    out: dict[int, Optional[float]] = {}
    for d0, d1 in zip(days, days[1:]):
        v0 = by_day[d0][1]
        v1 = by_day[d1][1]
        if _finite_positive(v0) and _finite_positive(v1):
            dlog = math.log(v1 / v0)
            out[int(d1)] = dlog if math.isfinite(dlog) else None
        else:
            out[int(d1)] = None
    return out


def _variance_mean(values: Sequence[float]) -> tuple[float, float]:
    """Sample variance (ddof=1) and mean of a non-empty finite sequence."""
    n = len(values)
    if n < 2:
        return float("nan"), float("nan")
    mean = math.fsum(values) / float(n)
    var = math.fsum((v - mean) ** 2 for v in values) / float(n - 1)
    return var, mean


def cycle_slope(
    series_by_symbol: Mapping[str, Sequence[tuple[int, float]]],
    symbol: str,
    stamp_ns: int,
    *,
    universe: Sequence[str],
    window_rows: int,
    changes_by_symbol: Optional[Mapping[str, Mapping[int, Optional[float]]]] = None,
) -> Optional[float]:
    """``CYC_s(T)``: OLS slope of own daily log OI change on the
    leave-one-out aggregate over the most recent ``window_rows - 1`` paired
    daily changes whose end-row stamps are <= T.

    The aggregate ``M(d)`` is the mean over the OTHER declared-universe
    symbols' changes (LEAVE-ONE-OUT -- the regressand never appears in the
    regressor).  COMPLETE CROSS-SECTION: every day in the window must carry
    a finite change for EVERY declared symbol; any broken day fails the
    window CLOSED (symbol INELIGIBLE, no back-fill, no partial aggregate).
    Defined iff ``Var(M) > 0``; consumed row stamps are gated
    (``assert_inputs_available``) against the decision stamp.  A caller
    scoring the whole cross-section at one stamp may pass
    ``changes_by_symbol`` (precomputed :func:`daily_log_changes` maps) to
    parse each series once -- purely an efficiency path, byte-identical.
    """
    sym = str(symbol)
    rows_needed = int(window_rows)
    if rows_needed < 3:
        raise ContractViolation(
            "window_rows must be >= 3 (a defined ddof=1 slope needs >= 2 "
            "paired changes)"
        )
    stamp = int(stamp_ns)
    universe_symbols = sorted(str(s) for s in universe)
    if sym not in universe_symbols:
        raise ContractViolation(f"symbol {sym} is not in the declared universe")
    if changes_by_symbol is None:
        changes = {
            s: daily_log_changes(series_by_symbol.get(s) or (), stamp)
            for s in universe_symbols
        }
    else:
        changes = {
            s: dict(changes_by_symbol.get(s) or {}) for s in universe_symbols
        }
    # PRESENCE intersection (the D2 panel convention): a day enters the
    # candidate set iff EVERY declared symbol has a paired daily change
    # ending there; a BROKEN value (non-positive/non-finite level) stays
    # present and fails the window CLOSED below -- it never silently
    # shrinks the window.
    common: list[int] = sorted(
        set.intersection(*[set(changes[s]) for s in universe_symbols])
    )
    need = rows_needed - 1
    if len(common) < need:
        return None  # INELIGIBLE: incomplete window (fail-closed)
    days = common[-need:]
    consumed: list[int] = list(days)
    assert_inputs_available(consumed, as_of_ns=stamp, context="cycle_slope")
    own: list[float] = []
    agg: list[float] = []
    others = [s for s in universe_symbols if s != sym]
    if not others:
        return None
    for d in days:
        own_v = changes[sym][d]
        vals = [changes[j][d] for j in others]
        if own_v is None or any(v is None for v in vals):
            return None  # broken day inside the window: fail CLOSED
        own.append(float(own_v))
        agg.append(math.fsum(vals) / float(len(vals)))
    var_m, _mean_m = _variance_mean(agg)
    if not math.isfinite(var_m) or var_m <= 0.0:
        return None
    var_own, mean_own = _variance_mean(own)
    if not math.isfinite(var_own):
        return None
    mean_agg = math.fsum(agg) / float(len(agg))
    cov = math.fsum(
        (o - mean_own) * (m - mean_agg) for o, m in zip(own, agg)
    ) / float(len(own) - 1)
    slope = cov / var_m
    return slope if math.isfinite(slope) else None


def own_share_mean(
    series_by_symbol: Mapping[str, Sequence[tuple[int, float]]],
    symbol: str,
    stamp_ns: int,
    *,
    universe: Sequence[str],
    window_rows: int,
    readable_by_symbol: Optional[Mapping[str, Sequence[tuple[int, float]]]] = None,
) -> Optional[float]:
    """``SH_s(T)``: mean OWN SHARE of the staged-universe aggregate OI level
    over the ``window_rows`` most recent daily rows <= T.

    COMPLETE CROSS-SECTION per row: every declared symbol must carry a
    readable positive finite row at EXACTLY each consumed row stamp (the
    denominator is the sum over the 19 tradeable symbols); any missing row
    fails CLOSED.  The control quantity contains NO differencing, NO
    regression and NO OI-flow direction -- an OI-LEVEL share only.  A
    caller scoring the whole cross-section at one stamp may pass
    ``readable_by_symbol`` (precomputed :func:`readable_rows` lists) to
    parse each series once -- purely an efficiency path, byte-identical.
    """
    sym = str(symbol)
    rows_needed = int(window_rows)
    if rows_needed < 1:
        raise ContractViolation("window_rows must be >= 1")
    stamp = int(stamp_ns)
    universe_symbols = sorted(str(s) for s in universe)
    if sym not in universe_symbols:
        raise ContractViolation(f"symbol {sym} is not in the declared universe")
    if readable_by_symbol is None:
        readable_by_symbol = {
            s: readable_rows(series_by_symbol.get(s) or (), stamp)
            for s in universe_symbols
        }
    # align by UTC day bucket (ONE row per symbol per day, manifest-pinned;
    # the day's last snapshot may land before 23:55Z -- A9F-OBS-7) and take
    # the last `rows_needed` COMMON day-rows, availability-stamped per row
    by_day: dict[str, dict[int, tuple[int, float]]] = {}
    for s in universe_symbols:
        day_map: dict[int, tuple[int, float]] = {}
        for ts, value in (readable_by_symbol.get(s) or ()):
            d = day_index(int(ts))
            if d in day_map:
                raise ContractViolation(
                    f"staged OI series for {s} carries two rows for UTC day "
                    f"index {d}; refusing"
                )
            day_map[d] = (int(ts), float(value))
        by_day[s] = day_map
    common_days = sorted(set.intersection(*[set(m) for m in by_day.values()]))
    if len(common_days) < rows_needed:
        return None
    window_days = common_days[-rows_needed:]
    assert_inputs_available(
        [by_day[s][d][0] for d in window_days for s in universe_symbols],
        as_of_ns=stamp,
        context="own_share_mean",
    )
    total = 0.0
    for d in window_days:
        cross_total = 0.0
        own_value: Optional[float] = None
        for s in universe_symbols:
            ts, level = by_day[s][d]
            if not _finite_positive(level):
                return None  # broken level inside the window: fail closed
            cross_total += level
            if s == sym:
                own_value = level
        if own_value is None or cross_total <= 0.0:
            return None
        total += own_value / cross_total
    share = total / float(rows_needed)
    return share if math.isfinite(share) else None


def arm_signal_spec(arm_id: str) -> tuple[str, int]:
    """``(signal_kind, window_rows)`` of one frozen arm."""
    arm_id = str(arm_id)
    if arm_id not in _ARM_SIGNAL:
        raise ContractViolation(f"unknown arm_id {arm_id!r}; expected {ARM_IDS}")
    return _ARM_SIGNAL[arm_id]


def is_control_arm(arm_id: str) -> bool:
    return str(arm_id) == CONTROL_ARM


def signal_scores_at(
    arm_id: str,
    *,
    oi_by_symbol: Mapping[str, Sequence[tuple[int, float]]],
    stamp_ns: int,
    universe: Sequence[str],
) -> dict[str, float]:
    """PIT signal scores of one arm at one decision stamp.

    Anchor / neighbour: the leave-one-out cycle slope (window 29 / 15 rows).
    Control: the mean own share of the aggregate OI level (28 rows).  A
    symbol whose window fails closed is simply INELIGIBLE at the stamp
    (never guessed).  The anchor/neighbour REFUSE to run without the OI
    bundle; the control REQUIRES it (shares are OI levels).  BTCUSDT can
    never enter the tradeable universe.
    """
    arm_id = str(arm_id)
    kind, window_rows = arm_signal_spec(arm_id)
    if not oi_by_symbol:
        raise ContractViolation(
            f"{arm_id} requires the staged-OI bundle (the family signal is "
            "built from the daily OI path)"
        )
    universe_symbols = sorted(str(s) for s in universe)
    if BENCHMARK_SYMBOL in universe_symbols:
        raise ContractViolation(
            "the pinned benchmark leg can never enter the tradeable universe"
        )
    missing = [s for s in universe_symbols if not (oi_by_symbol.get(s) or ())]
    if missing:
        raise ContractViolation(
            f"declared universe symbols without staged OI rows: {sorted(missing)}"
        )
    stamp = int(stamp_ns)
    scores: dict[str, float] = {}
    # parse each series ONCE per stamp and share the precomputed maps
    # across the cross-section (pure efficiency; byte-identical scores)
    if kind == "cycle_slope":
        precomputed = {
            s: daily_log_changes(oi_by_symbol.get(s) or (), stamp)
            for s in universe_symbols
        }
        for sym in universe_symbols:
            value = cycle_slope(
                oi_by_symbol,
                sym,
                stamp,
                universe=universe_symbols,
                window_rows=int(window_rows),
                changes_by_symbol=precomputed,
            )
            if value is not None and math.isfinite(value):
                scores[sym] = float(value)
    else:
        precomputed = {
            s: readable_rows(oi_by_symbol.get(s) or (), stamp)
            for s in universe_symbols
        }
        for sym in universe_symbols:
            value = own_share_mean(
                oi_by_symbol,
                sym,
                stamp,
                universe=universe_symbols,
                window_rows=int(window_rows),
                readable_by_symbol=precomputed,
            )
            if value is not None and math.isfinite(value):
                scores[sym] = float(value)
    return scores


# --------------------------------------------------------------------------- #
# The frozen hysteresis book (median-exit; OICYC.md section 5 verbatim)
# --------------------------------------------------------------------------- #
SCHEMA_VERSION = "v14i.oicyc.book.v1"

#: Reason codes for carried (skipped) rebalances.
REASON_HELD_INELIGIBLE = "HELD_SYMBOL_INELIGIBLE_BOOK_CARRIED"
REASON_SIDE_TOO_THIN = "SIDE_MEMBERSHIP_BELOW_MIN_BOOK_CARRIED"
REASON_OK = "OK"


class EligibilityShortfall(AdapterError):
    """A stamp has no well-formed book -- fail closed, never inferred."""


def median_rank(n: int) -> int:
    """The median rank of an ``n``-name cross-section (1-based ranks)."""
    if n < 1:
        raise ContractViolation("n must be >= 1")
    return (int(n) + 1) // 2


def build_hysteresis_book(
    scores: Mapping[str, Any],
    *,
    prev_book: Optional[Mapping[str, float]] = None,
    sort_ascending: bool = True,
    leg_gross: float = LEG_GROSS,
    cap_max: float = CAP_MAX,
    min_side_members: int = MIN_SIDE_MEMBERS,
    min_eligible: int = MIN_ELIGIBLE,
) -> dict[str, Any]:
    """The deterministic median-exit hysteresis tercile book for one stamp.

    ``scores`` maps PIT-eligible candidate symbols to their signal value;
    ranks are ascending on ``sort_ascending``-oriented values with exact
    ties broken by lexicographically smallest symbol id (the LONG side is
    the low-value tercile when ``sort_ascending`` is True -- all three
    frozen arms run ascending-on-value so "long lowest CYC / lowest share"
    is structural).  Hysteresis: a flat symbol enters its entry zone's
    side; a HELD side exits ONLY when its rank crosses beyond the median
    (long -> rank > median flips short; short -> rank < median flips
    long); a long at/below the median and a short at/above it are held,
    including through the buffer.  Equal weight per side
    ``min(leg_gross / n_side, cap_max)``; a side with < 2 members leaves
    its budget in cash; a side with < ``min_side_members`` members (or any
    held symbol that lost eligibility) SKIPS the stamp and carries the
    previous book (fail-closed).  ``|w| <= cap`` and
    gross <= 2 * leg_gross <= 1.0 hold BY CONSTRUCTION and are asserted.
    """
    cap = float(cap_max)
    if cap <= 0.0:
        raise ContractViolation("cap_max must be positive")
    if not math.isfinite(float(leg_gross)) or float(leg_gross) <= 0.0:
        raise ContractViolation("leg_gross must be finite positive")
    if int(min_side_members) < 2:
        raise ContractViolation("min_side_members must be >= 2")

    cleaned: dict[str, float] = {}
    ineligible: dict[str, str] = {}
    for raw_sym, raw_value in dict(scores).items():
        sym = str(raw_sym)
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            ineligible[sym] = "NON_NUMERIC_SCORE"
            continue
        if not math.isfinite(value):
            ineligible[sym] = "NON_FINITE_SCORE"
            continue
        cleaned[sym] = value

    prev_weights: dict[str, float] = {}
    for sym, weight in dict(prev_book or {}).items():
        w = float(weight)
        if not math.isfinite(w):
            raise ContractViolation(f"previous book weight for {sym} is non-finite")
        prev_weights[str(sym)] = w
    held_prev = {sym for sym, w in prev_weights.items() if abs(w) > 1e-9}

    # fail-closed: a held symbol without a computable score skips the stamp
    # (the previous book is held; no position-zeroing inference).
    missing_held = sorted(held_prev - set(cleaned))
    if missing_held:
        return _carry_book(
            prev_weights,
            reason=REASON_HELD_INELIGIBLE,
            detail={"missing_held": missing_held},
            n_eligible=len(cleaned),
            cap=cap,
            ineligible=ineligible,
        )

    eligible = sorted(cleaned)
    if len(eligible) < int(min_eligible):
        raise EligibilityShortfall(
            f"only {len(eligible)} eligible names at this stamp; the frozen "
            f"complete-cross-section book requires >= {int(min_eligible)} "
            "(fail-closed)"
        )

    n = len(eligible)
    sign = 1.0 if sort_ascending else -1.0
    ordered = sorted((sign * cleaned[sym], sym) for sym in eligible)
    ranks = {sym: idx + 1 for idx, (_key, sym) in enumerate(ordered)}
    #: descending PRESENTATION (rank 1 = highest value) for the frozen
    #: "rank DESCENDING on SH_s" control language; AVERAGE ranks for ties
    #: (the repo-wide Spearman convention).  Diagnostics only.
    values = [cleaned[sym] for sym in eligible]
    ranks_desc: dict[str, float] = {}
    for sym in eligible:
        v = cleaned[sym]
        strictly_above = sum(1 for u in values if u > v)
        tied = sum(1 for u in values if u == v)
        ranks_desc[sym] = 1.0 + strictly_above + (tied - 1) / 2.0
    n_lo = n // 3
    n_hi = n // 3
    med = median_rank(n)

    def zone(rank: int) -> str:
        if rank <= n_lo:
            return "LONG_ENTER"
        if rank > n - n_hi:
            return "SHORT_ENTER"
        return "BUFFER"

    prev_side = {
        "long": {s for s in held_prev if prev_weights[s] > 0.0},
        "short": {s for s in held_prev if prev_weights[s] < 0.0},
    }
    longs: set[str] = set()
    shorts: set[str] = set()
    flips: dict[str, str] = {}
    for sym in eligible:
        r = ranks[sym]
        z = zone(r)
        if sym in prev_side["long"]:
            # EXIT only when the rank crosses beyond the median: exit = flip.
            if r > med:
                shorts.add(sym)
                flips[sym] = "long_flipped_short_at_median"
            else:
                longs.add(sym)
        elif sym in prev_side["short"]:
            if r < med:
                longs.add(sym)
                flips[sym] = "short_flipped_long_at_median"
            else:
                shorts.add(sym)
        else:
            if z == "LONG_ENTER":
                longs.add(sym)
            elif z == "SHORT_ENTER":
                shorts.add(sym)

    # fail-closed: a side below the membership floor skips the stamp.
    if len(longs) < int(min_side_members) or len(shorts) < int(min_side_members):
        if not prev_weights:
            raise EligibilityShortfall(
                f"first decision stamp has a side below the membership floor "
                f"({len(longs)}L/{len(shorts)}S < {int(min_side_members)}); "
                "no previous book to hold (fail-closed)"
            )
        return _carry_book(
            prev_weights,
            reason=REASON_SIDE_TOO_THIN,
            detail={
                "n_longs_would_be": len(longs),
                "n_shorts_would_be": len(shorts),
                "min_side_members": int(min_side_members),
            },
            n_eligible=n,
            cap=cap,
            ineligible=ineligible,
        )

    n_long, n_short = len(longs), len(shorts)
    # a side with < 2 members leaves its budget in cash (guard; the
    # membership floor keeps this unreachable in the frozen family).
    w_long = 0.0 if n_long < 2 else min(float(leg_gross) / n_long, cap)
    w_short = 0.0 if n_short < 2 else min(float(leg_gross) / n_short, cap)
    weights: dict[str, float] = {}
    for sym in longs:
        weights[sym] = w_long
    for sym in shorts:
        weights[sym] = -w_short
    gross = math.fsum(abs(w) for w in weights.values())
    max_abs = max((abs(w) for w in weights.values()), default=0.0)
    if max_abs > cap + 1e-12:
        raise ContractViolation(f"cap breached by construction: {max_abs}")
    if gross > 2.0 * float(leg_gross) + 1e-9:
        raise ContractViolation(f"gross breached by construction: {gross}")
    held = {sym: w for sym, w in weights.items() if abs(w) > 1e-9}
    if not held:
        raise EligibilityShortfall("empty book after construction (fail-closed)")

    return {
        "schema": SCHEMA_VERSION,
        "weights": [[sym, weights[sym]] for sym in sorted(weights)],
        "longs": [[sym, weights[sym]] for sym in sorted(longs)],
        "shorts": [[sym, weights[sym]] for sym in sorted(shorts)],
        "carried_forward": False,
        "reason_code": REASON_OK,
        "n_eligible": n,
        "n_longs": n_long,
        "n_shorts": n_short,
        "ranks": [[sym, ranks[sym]] for sym in sorted(ranks)],
        "ranks_desc": [[sym, ranks_desc[sym]] for sym in sorted(ranks_desc)],        "median_rank": int(med),
        "flips": dict(sorted(flips.items())),
        "gross": gross,
        "max_abs_weight": max_abs,
        "signal_availability_ratio": len(cleaned) / float(max(n, 1)),
        "ineligible": dict(sorted(ineligible.items())),
        "tercile_sizes": {
            "long_entry": n_lo,
            "buffer": n - n_lo - n_hi,
            "short_entry": n_hi,
        },
    }


def _carry_book(
    prev_weights: Mapping[str, float],
    *,
    reason: str,
    detail: dict[str, Any],
    n_eligible: int,
    cap: float,
    ineligible: Mapping[str, str],
) -> dict[str, Any]:
    """Hold the previous book verbatim (fail-closed rebalance skip)."""
    weights = {str(sym): float(w) for sym, w in prev_weights.items()}
    longs = [[sym, w] for sym, w in sorted(weights.items()) if w > 0.0]
    shorts = [[sym, w] for sym, w in sorted(weights.items()) if w < 0.0]
    gross = math.fsum(abs(w) for w in weights.values())
    max_abs = max((abs(w) for w in weights.values()), default=0.0)
    if max_abs > cap + 1e-12:
        raise ContractViolation("carried book breaches the frozen cap")
    return {
        "schema": SCHEMA_VERSION,
        "weights": [[sym, weights[sym]] for sym in sorted(weights)],
        "longs": longs,
        "shorts": shorts,
        "carried_forward": True,
        "reason_code": reason,
        "detail": dict(detail),
        "n_eligible": int(n_eligible),
        "n_longs": len(longs),
        "n_shorts": len(shorts),
        "ranks": [],
        "ranks_desc": [],
        "median_rank": None,
        "flips": {},
        "gross": gross,
        "max_abs_weight": max_abs,
        "signal_availability_ratio": 1.0,
        "ineligible": dict(sorted(ineligible.items())),
        "tercile_sizes": {},
    }


def held_max_abs_weight_symbol(
    weights: Mapping[str, float],
) -> Optional[str]:
    """The HELD symbol with maximum |weight|; ties break ascending name.

    Drop-one design (OICYC.md section 8): at every decision stamp drop the
    HELD symbol with maximum |weight|.  ``None`` when nothing is held.
    """
    held = [
        (abs(float(w)), str(sym))
        for sym, w in weights.items()
        if abs(float(w)) > 1e-9
    ]
    if not held:
        return None
    top = max(magnitude for magnitude, _sym in held)
    candidates = sorted(sym for magnitude, sym in held if magnitude == top)
    return candidates[0]


def drop_one_book(
    weights: Mapping[str, float],
) -> dict[str, Any]:
    """Drop the held max-|weight| symbol; remaining weights UNCHANGED.

    No post-score renormalisation (OICYC.md section 8, verbatim).  A
    zero-position book refuses (fail closed).
    """
    target = held_max_abs_weight_symbol(weights)
    if target is None:
        raise EligibilityShortfall(
            "drop-one refused: no held position (zero-position book)"
        )
    remaining = {
        str(sym): float(w)
        for sym, w in weights.items()
        if str(sym) != target and abs(float(w)) > 1e-9
    }
    return {
        "dropped_symbol": target,
        "dropped_weight": float(weights[target]),
        "weights": [[sym, remaining[sym]] for sym in sorted(remaining)],
        "n_held_after": len(remaining),
    }


# --------------------------------------------------------------------------- #
# Per-stamp target payload (chained by the plugin; pure here)
# --------------------------------------------------------------------------- #
def compute_targets_at(
    arm_id: str,
    *,
    oi_by_symbol: Mapping[str, Sequence[tuple[int, float]]],
    stamp_ns: int,
    universe: Sequence[str],
    prev_book: Optional[Mapping[str, float]] = None,
    gross: float = LEG_GROSS * 2.0,
) -> dict[str, Any]:
    """Frozen target book of one arm at one decision stamp.

    Ranks the eligible universe by the PIT signal and delegates to
    :func:`build_hysteresis_book` with the previous retained book (``None``
    = flat start).  Fail-closed on insufficient breadth
    (:class:`EligibilityShortfall`) and on any availability violation.
    No PnL is computed.  The payload carries the preregistered
    CONFIRMATORY status (plan Section 1.1) so the driver records it in the
    verdict and denominator.
    """
    arm_id = str(arm_id)
    kind, window_rows = arm_signal_spec(arm_id)
    stamp = int(stamp_ns)
    universe_symbols = sorted(str(s) for s in universe)
    scores = signal_scores_at(
        arm_id,
        oi_by_symbol=oi_by_symbol,
        stamp_ns=stamp,
        universe=universe_symbols,
    )
    book = build_hysteresis_book(
        scores,
        prev_book=prev_book,
        sort_ascending=True,
        leg_gross=LEG_GROSS,
        cap_max=CAP_MAX,
        min_side_members=MIN_SIDE_MEMBERS,
        min_eligible=max(MIN_ELIGIBLE, len(universe_symbols)),
    )
    honest_availability = len(scores) / float(max(len(universe_symbols), 1))
    weights = {str(sym): float(w) for sym, w in book["weights"]}
    ordered_weights = {sym: weights[sym] for sym in sorted(weights)}
    payload = {
        "schema": "v14i.oicyc.targets.v1",
        "family_id": FAMILY_ID,
        "arm_id": arm_id,
        "status": STATUS_OK,
        "weights": [[sym, ordered_weights[sym]] for sym in sorted(ordered_weights)],
        "longs": [[sym, round(float(w), 12)] for sym, w in book["longs"]],
        "shorts": [[sym, round(float(w), 12)] for sym, w in book["shorts"]],
        "carried_forward": bool(book["carried_forward"]),
        "reason_code": book["reason_code"],
        "decision_ns": stamp,
        "confirmatory": {
            "status": CONFIRMATORY,
            "authority": "PLAN_crypto_v14.md Section 1.1; OICYC.md sections 2/12",
            "disclosure": SECTION_1_1_DISCLOSURE,
        },
        "diagnostics": {
            "stamp_ns": stamp,
            "stamp_iso": iso_utc(stamp),
            "n_eligible": int(book["n_eligible"]),
            "n_longs": int(book["n_longs"]),
            "n_shorts": int(book["n_shorts"]),
            "signal_kind": kind,
            "window_rows": int(window_rows),
            "window_changes": int(window_rows - 1) if kind == "cycle_slope" else None,
            "sort": (
                "ascending on signal value (long = lowest CYC tercile)"
                if kind == "cycle_slope"
                else "ascending on SH value (long = lowest share); "
                "descending rank presentation in ranks_desc"
            ),
            "ranks": [[sym, int(r)] for sym, r in book["ranks"]],
            "ranks_desc": [[sym, int(r)] for sym, r in book.get("ranks_desc", [])],
            "median_rank": book.get("median_rank"),
            "flips": dict(book.get("flips", {})),
            "gross_after_weights": round(float(book["gross"]), 12),
            "max_abs_weight": round(float(book["max_abs_weight"]), 12),
            "signal_availability_ratio": round(float(honest_availability), 12),
        },
    }
    return payload


# --------------------------------------------------------------------------- #
# Execution: the pinned next-allowed-fill convention
# --------------------------------------------------------------------------- #
def snap_close_to_boundary(ts: int) -> int:
    """Forward-snap a raw bar-close stamp to the 15m boundary it terminates.

    Binance kline closes sit ~1ms (here ~999_936ns) before the nominal
    boundary; the snapped boundary is the PIT slot identity.  Identical
    pinned rule to the frozen V12/V13 audit loaders (frozen code is reused,
    never modified).
    """
    remainder = int(ts) % BAR_INTERVAL_NS
    forward = (BAR_INTERVAL_NS - remainder) % BAR_INTERVAL_NS
    if forward < BAR_INTERVAL_NS // 2:
        return int(ts) + forward
    return int(ts)


def next_allowed_fill(
    bars: Sequence[Any],
    symbol: str,
    *,
    decision_ns: int,
    event_delay_events: int = 0,
) -> Optional[Any]:
    """The ONE declared execution lag, pinned (OICYC.md section 5).

    Orders release at ``decision + 15m``; the fill reference is the OPEN
    price of the FIRST completed 15m bar whose slot-open instant is >= the
    release instant (for a Monday 00:00:00Z decision: the 00:15Z slot).
    Stress ``+1 event delay`` shifts to the NEXT slot's open (strictly
    later completed bars).  Missing slots -> NO event (never a shifted
    substitute).  Only the chosen bar's OPEN is consumed: it is observable
    AT the slot-open instant, while the bar's close stamp (slot-open + 15m)
    is NOT readable by this fill -- the availability horizon of the fill is
    its slot-open instant.
    """
    from research.v11.families.oilever_delev.strategy import FillEvent

    delay = int(event_delay_events)
    if delay < 0:
        raise ContractViolation("event_delay_events must be >= 0")
    decision = int(decision_ns)
    release = decision + ORDER_RELEASE_LAG_NS
    if decision % DAY_NS != 0:
        raise ContractViolation(
            f"decision stamp {iso_utc(decision)} is not a midnight UTC grid instant"
        )
    decorated = sorted(
        ((snap_close_to_boundary(int(b.ts_event_ns)), b) for b in bars),
        key=lambda pair: pair[0],
    )
    seen: set[int] = set()
    candidates: list[tuple[int, Any]] = []
    for boundary, bar in decorated:
        slot_open = boundary - BAR_INTERVAL_NS
        if slot_open in seen:
            raise ContractViolation(
                f"duplicate 15m slot {iso_utc(slot_open)} for {symbol}"
            )
        seen.add(slot_open)
        if slot_open >= release:
            candidates.append((slot_open, bar))
    if not candidates:
        return None
    index = min(delay, len(candidates) - 1)
    slot_open, chosen = candidates[index]
    fill = FillEvent(
        symbol=str(symbol),
        decision_ns=decision,
        fill_open_ns=int(slot_open),
        fill_bar_close_ns=int(chosen.ts_event_ns),
        event_offset=int(index),
        price=float(chosen.open),
    )
    if fill.fill_open_ns < release:
        raise ContractViolation("next-allowed-fill violated: slot-open < release")
    assert_inputs_available(
        (decision,),
        as_of_ns=fill.fill_open_ns,
        context="next_allowed_fill.decision_payload",
    )
    return fill


# --------------------------------------------------------------------------- #
# Schedule / folds (frozen clocks; the V11 pinned-window helpers are reused)
# --------------------------------------------------------------------------- #
def stamp_calendar() -> tuple[int, ...]:
    """Weekly Monday 00:00:00Z decision stamps over the frozen window."""
    return weekly_mondays(
        window_start_iso=WINDOW_START_ISO, window_end_iso=WINDOW_END_ISO
    )


def _fold_bounds_ns() -> list[tuple[int, str, int, int]]:
    """``[(index, label, start_ns, end_ns)]`` of the pinned fold calendar."""
    out: list[tuple[int, str, int, int]] = []
    for index, (label, start_iso, end_iso) in enumerate(FOLD_WINDOWS):
        start = parse_iso_utc(f"{start_iso}T00:00:00Z")
        end = parse_iso_utc(f"{end_iso}T00:00:00Z")
        if end <= start:
            raise ContractViolation(f"fold {label} has a non-positive window")
        out.append((index, label, start, end))
    return out


def fold_assignments(
    instants: Sequence[int],
) -> list[tuple[int, str, list[int], list[int]]]:
    """Assign decision stamps to the PINNED F0/F1/F2 calendar windows.

    A fold covers ``[start 00:00Z, end 00:00Z)``; the frozen 1-day purge
    zone is ``[end - PURGE_DAYS days, end)`` -- the MEASURED V13 convention
    (exactly one stamp, 2026-04-20, falls inside F1's zone, leaving 51
    effective Mondays at 17/17/17; the same counts the V14 D2 feasibility
    audit measured for this family).  Returns ``(index, label, effective_
    members, purged_members)``; purged stamps are force-flat gap stamps
    (no decision, no book opened there).
    """
    purge_ns = int(PURGE_DAYS) * DAY_NS
    members: dict[int, list[int]] = {}
    purged: dict[int, list[int]] = {}
    bounds = _fold_bounds_ns()
    for instant in sorted(int(v) for v in instants):
        for index, label, start, end in bounds:
            if start <= instant < end:
                if instant >= end - purge_ns:
                    purged.setdefault(index, []).append(instant)
                else:
                    members.setdefault(index, []).append(instant)
                break
        else:
            raise ContractViolation(
                f"decision stamp {iso_utc(instant)} outside every pinned fold"
            )
    out: list[tuple[int, str, list[int], list[int]]] = []
    for index, label, _start, _end in bounds:
        if not members.get(index):
            raise ContractViolation(f"pinned fold {label} received no decision stamps")
        out.append((index, label, list(members[index]), list(purged.get(index, []))))
    return out


def effective_schedule(
    instants: Sequence[int],
) -> tuple[list[int], dict[str, list[int]]]:
    """The effective (purged) decision schedule: ``(effective, purged_by_fold)``."""
    effective: list[int] = []
    purged_by_fold: dict[str, list[int]] = {}
    for _index, label, members, purged in fold_assignments(instants):
        effective.extend(members)
        if purged:
            purged_by_fold[label] = list(purged)
    return effective, purged_by_fold


def fold_end_ns(stamp_ns: int) -> int:
    """The force-flat boundary of the fold containing ``stamp_ns``."""
    stamp = int(stamp_ns)
    for _index, _label, start, end in _fold_bounds_ns():
        if start <= stamp < end:
            return int(end)
    raise ContractViolation(f"stamp {iso_utc(stamp)} outside every pinned fold")


def fold_end_instants() -> list[int]:
    """The three fold-boundary instants (force-flat points, frozen windows)."""
    return [
        int(parse_iso_utc(f"{end}T00:00:00Z"))
        for _label, _start, end in FOLD_WINDOWS
    ]


def window_start_ns() -> int:
    return parse_iso_utc(WINDOW_START_ISO)


def window_end_ns() -> int:
    return parse_iso_utc(WINDOW_END_ISO)


# --------------------------------------------------------------------------- #
# Preregistered causal-control rule (OICYC.md section 6 decision table)
# --------------------------------------------------------------------------- #
def evaluate_control_gate(*, anchor_passes: bool, control_passes: bool) -> dict[str, Any]:
    """The preregistered control rule (OICYC.md section 6) as a decision table.

    IF the anchor ``CYC-28D`` passes {after-cost expectancy > 0, position
    PF >= 1.10, >= 2/3 folds positive} THEN ``CTL-OISHARE`` must fail at
    least one of those three gates.  If the control ALSO passes all three,
    the edge is an OI-dominance/size effect, the co-movement information is
    redundant, and ``A14-V14-A8-OICYC`` is FALSIFIED as a
    cycle-participation mechanism.  The control is NEVER promotable
    regardless of its own result.
    """
    anchor = bool(anchor_passes)
    control = bool(control_passes)
    if anchor and control:
        verdict = CONTROL_GATE_FALSIFIED
    else:
        verdict = CONTROL_GATE_PASS
    return {
        "rule": (
            "IF anchor CYC-28D passes {expectancy>0, PF>=1.10, >=2/3 folds "
            "positive} THEN CTL-OISHARE must fail at least one; both passing "
            "falsifies the family (edge is an OI-dominance/size artifact)"
        ),
        "anchor_passes": anchor,
        "control_passes": control,
        "control_never_promotable": True,
        "verdict": verdict,
    }


# --------------------------------------------------------------------------- #
# Frozen identity accessors (digest payloads live in frozen_identity.py)
# --------------------------------------------------------------------------- #
def frozen_identity(arm_id: str) -> StrategyIdentity:
    """The frozen V14 identity of one arm (digest equality is test-pinned)."""
    from research.v14.families.oicyc.frozen_identity import frozen_identity as _impl

    return _impl(arm_id)


def frozen_arm_digest_report() -> dict[str, dict[str, Any]]:
    """Recomputed vs recorded ``arm_config_digest`` per arm (honest report)."""
    from research.v14.families.oicyc.frozen_identity import (
        OICYC_ARM_CONFIG_DIGESTS,
    )

    report: dict[str, dict[str, Any]] = {}
    for arm_id in ARM_IDS:
        identity = frozen_identity(arm_id)
        computed = arm_config_digest(identity, arm_id=arm_id)
        recorded = OICYC_ARM_CONFIG_DIGESTS[arm_id]
        report[arm_id] = {
            "computed_from_identity": computed,
            "recorded_in_freeze": recorded,
            "match": bool(computed == recorded),
        }
    return report


__all__ = [
    "ADVERSE_TICK_SLIP_FLOOR",
    "ANCHOR_ARM",
    "ARM_CONFIG_IDS",
    "ARM_IDS",
    "ARM_ROLES",
    "BAR_INTERVAL_NS",
    "BENCHMARK_SYMBOL",
    "CAP_MAX",
    "CONFIRMATORY",
    "CONTROL_ARM",
    "CONTROL_GATE_FALSIFIED",
    "CONTROL_GATE_PASS",
    "DAY_NS",
    "DECISION_CLOCK",
    "DIRECTION",
    "FAMILY_ID",
    "FILL_CLOCK",
    "FIRST_STAMP_ISO",
    "FOLD_WINDOWS",
    "FOLDS_CONTRACT",
    "LEG_GROSS",
    "MATRIX_COHORT_HINT",
    "MIN_ELIGIBLE",
    "MIN_FOLDS",
    "MIN_SIDE_MEMBERS",
    "NEIGHBOUR_ARM",
    "ORDER_RELEASE_LAG_NS",
    "PURGE_DAYS",
    "REASON_HELD_INELIGIBLE",
    "REASON_OK",
    "REASON_SIDE_TOO_THIN",
    "SECTION_1_1_DISCLOSURE",
    "STATUS_OK",
    "STRATEGY_ID",
    "TAKER_FEE_FLOOR_BPS",
    "TRADEABLE_UNIVERSE_SIZE",
    "WARMUP_ROWS_FIRST_STAMP",
    "WINDOW_END_ISO",
    "WINDOW_ROWS_ANCHOR",
    "WINDOW_ROWS_CONTROL",
    "WINDOW_ROWS_NEIGHBOUR",
    "WINDOW_START_ISO",
    "EligibilityShortfall",
    "LookaheadViolation",
    "SCHEMA_VERSION",
    "arm_signal_spec",
    "assert_first_stamp_warmup",
    "assert_inputs_available",
    "build_hysteresis_book",
    "compute_targets_at",
    "daily_log_changes",
    "day_index",
    "drop_one_book",
    "evaluate_control_gate",
    "cycle_slope",
    "effective_schedule",
    "fold_assignments",
    "fold_end_instants",
    "fold_end_ns",
    "frozen_arm_digest_report",
    "frozen_identity",
    "held_max_abs_weight_symbol",
    "iso_utc",
    "median_rank",
    "next_allowed_fill",
    "own_share_mean",
    "parse_iso_utc",
    "readable_rows",
    "signal_scores_at",
    "snap_close_to_boundary",
    "stamp_calendar",
    "warmup_rows_at",
    "window_end_ns",
    "window_start_ns",
]
