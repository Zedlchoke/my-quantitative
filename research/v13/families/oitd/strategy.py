"""Frozen strategy primitives for the A13-V13-A8-OITD family (V13 I lane).

This module implements the FROZEN contract of the V13 selection freeze
(``research/control/v13_run/selection_freeze_v13.json``, family
``A13-V13-A8-OITD``) + the mechanism definition
``research/proposals/v13/a8/OITD.md`` / ``.json`` verbatim -- no tuning, no
grids, no parameter changes.  It is a pure, data-injected library: every
observable (per-UTC-day dollar turnover from completed 15m bars, daily OI
snapshots, mark-price snapshots, funding settlements, tick sizes) is
supplied by the caller, so the same primitives run on synthetic fixtures
and on the read-only workspace snapshot.  Nothing here reads the catalog,
computes a scored outcome, or persists anything.

Frozen arms (exactly three):

* anchor   ``OITD-28D``     -- ``D = OI7 x MK / TO(28d)``; long lowest-D
  tercile, short highest-D tercile (the mechanism as stated);
* neighbour ``OITD-56D``    -- identical construction with a 56d turnover
  denominator (same mechanism, different justified parameter);
* causal negative control ``CTL-FLOW-ONLY`` -- rank on 28d mean daily
  dollar turnover ALONE, DESCENDING (long highest-turnover tercile, short
  lowest-turnover tercile).  The OI numerator is DELETED: the control arm
  is constructed without OI or mark inputs and the signal layer REFUSES
  to run it with either injected (fail-closed proof of deletion).

SIGNAL (PIT, fusion availability semantics -- a decision at T reads only
records whose availability stamp is <= T; availability for these native
observables IS the record stamp: bar close boundary, OI snapshot stamp,
mark snapshot stamp; research/data_fusion/crypto_compat.py):

* ``OI7_s(T)``  = mean of the latest 7 daily OI records with stamp <= T,
  all within the trailing 10 days; fewer than 7 -> INELIGIBLE
  (fail-closed, no back-fill);
* ``MK_s(T)``   = latest mark record with stamp <= T within trailing 24h;
  else INELIGIBLE;
* ``TO_s(T,W)`` = mean daily dollar turnover over the ``W`` completed UTC
  day buckets ending immediately before T's own day bucket -- exactly the
  completed 15m bars whose close stamps fall in ``(T-W, T]``; EVERY day in
  the window must be present and fully covered (gaps are failures, never
  filled);
* ``D_s(T)``    = ``OI7_s(T) * MK_s(T) / TO_s(T, 28d)`` (anchor) or
  ``/ TO_s(T, 56d)`` (neighbour) -- days of average turnover needed to
  unwind the symbol's standing notional OI.

BOOK (hysteresis; research/v13/families/oitd/book.py): rank eligible
symbols; the lowest tercile is the long-entry zone, the highest tercile
the short-entry zone, the middle tercile the buffer.  A flat symbol
enters its zone's side; a held side exits ONLY when the rank crosses
beyond the buffer into the opposite entry zone (then it flips).  Equal
weight per side ``min(0.5 / n_side, 0.30)``; a side with < 2 members
leaves its budget in cash; a side with < 4 members (or any held symbol
that lost eligibility) skips the stamp's rebalance and holds the previous
book (fail-closed, no position-zeroing inference).  ``|w| <= 0.30`` and
gross <= 1.0 at every stamp BY CONSTRUCTION and asserted.

SCHEDULE / FILLS (the A9-F engine-convention pin, explicit and tested):

* decisions: weekly Monday 00:00:00Z over the frozen blind-S0 screen
  window (52 stamps; first 2025-08-25, last 2026-08-17);
* folds: chronological F0/F1/F2 on the pinned V12 fold calendar with the
  frozen 1-stamp purge; force-flat at fold boundaries (the purge strips
  each fold's trailing stamp so a book opened inside a fold realises
  inside that fold);
* execution lag (ONE, declared): orders release at ``T + 15m``; the fill
  reference is the OPEN price of the FIRST 15m bar whose slot-open
  instant is >= the release instant (for a Monday 00:00:00Z decision:
  the 00:15Z slot).  ``next_allowed_fill`` consumes ONLY that bar's
  open -- a quantity observable AT the slot-open instant -- and never
  the bar's close (stamped 15 minutes later, NOT readable by the fill).
  The fill-availability convention is explicit: every input consumed by
  a fill at slot-open ``F`` must carry an availability stamp <= ``F``;
  the gate :func:`assert_inputs_available` enforces it fail-closed and
  the mutation tests pin it.

Stress conventions inherited (L-V11-1): fee x1.5 / +2 adverse ticks /
+1 event delay on the family's own folds contract.  The frozen adapter
surface (GenericStrategyBase) supplies baseline cells, drop-one
filtering, fold assembly and the LONG_PAYS_POSITIVE_RATE funding accrual.

No module here computes a scored PnL.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional, Sequence

from research.adapter_v10.protocol import (
    ContractViolation,
    StrategyIdentity,
)
from research.contract_v10 import (
    ADVERSE_TICKS_SLIPPAGE_FLOOR_V10,
    FILL_CLOCK_V10,
    TAKER_FEE_FLOOR_BPS_V10,
)
from research.v11.families.oilever_delev.strategy import (
    DAY_NS,
    HOUR_NS,
    iso_utc,
    parse_iso_utc,
    weekly_mondays,
)
from research.v11.publication_identity import arm_config_digest

# --------------------------------------------------------------------------- #
# Frozen identity (fields pinned by the V13 selection freeze / OITD.json)
# --------------------------------------------------------------------------- #
FAMILY_ID = "A13-V13-A8-OITD"
STRATEGY_ID = "hyp_a13_v13_a8_oitd"
#: Long/short cross-sectional book; BTCUSDT is benchmark-excluded (context
#: only) and the BTC-beta context is a Stage-A scoring concern, never a leg.
DIRECTION = "long_short"
BENCHMARK_SYMBOL = "BTCUSDT"
MATRIX_COHORT_HINT = "v13"

WINDOW_START_ISO = "2025-08-22T00:00:00Z"
WINDOW_END_ISO = "2026-08-21T00:00:00Z"

FUNDING_SIGN_CONVENTION = "LONG_PAYS_POSITIVE_RATE"

ANCHOR_ARM = "OITD-28D"
NEIGHBOUR_ARM = "OITD-56D"
CONTROL_ARM = "CTL-FLOW-ONLY"

#: Arm id -> frozen role (selection_freeze_v13.json ``arms`` semantics).
ARM_ROLES: dict[str, str] = {
    ANCHOR_ARM: "anchor",
    NEIGHBOUR_ARM: "neighbour",
    CONTROL_ARM: "causal_negative_control",
}
ARM_IDS: tuple[str, ...] = tuple(sorted(ARM_ROLES))

#: Digest-bearing ``arm_config_id`` per arm.
ARM_CONFIG_IDS: dict[str, str] = {
    ANCHOR_ARM: "28D",
    NEIGHBOUR_ARM: "56D",
    CONTROL_ARM: "FLOW-ONLY",
}

#: The ``arm_config_digest`` values RECORDED for this implementation
#: (computed from :func:`frozen_identity` via
#: ``research.v11.publication_identity.arm_config_digest`` at freeze time
#: of this lane and pinned here; the digest equality is test-pinned so any
#: identity drift surfaces instead of passing silently).
FROZEN_ARM_CONFIG_DIGESTS: dict[str, str] = {
    ANCHOR_ARM: "9f121f3e1f425b1c17f8b2f8bba55cff7e4de0138e4c79f7896dea23c2a4640c",
    NEIGHBOUR_ARM: "620ef97b72ca305cfcab39b81219c251bb445e965ba706c6241c5b8dbbbda413",
    CONTROL_ARM: "e3b02064955acdf3c6c35e22a1355300a5e7655739b95929faa3a299ee7357b2",
}

#: Frozen per-arm signal spec: turnover window days, signal kind, and the
#: cross-sectional sort direction of the ranking key.
#:   * ``unwind_duration`` -- D = OI7 x MK / TO(W); ranked ASCENDING
#:     (long lowest-D tercile, short highest-D tercile);
#:   * ``turnover_only`` -- TO(W) alone; ranked DESCENDING (long
#:     highest-turnover tercile, short lowest-turnover tercile); the OI
#:     numerator is deleted (constant-across-symbols numerator removed).
_ARM_SIGNAL: dict[str, tuple[str, int, bool]] = {
    ANCHOR_ARM: ("unwind_duration", 28, True),
    NEIGHBOUR_ARM: ("unwind_duration", 56, True),
    CONTROL_ARM: ("turnover_only", 28, False),
}

#: Frozen config payloads per arm (digest inputs; canonicalised sorted).
_FROZEN_CONFIGS: dict[str, dict] = {
    ANCHOR_ARM: {
        "book": "oitd_hysteresis_tercile",
        "signal": "unwind_duration",
        "turnover_days": 28,
        "oi_stamps": 7,
        "oi_stamp_span_days": 10,
        "mark_max_age_hours": 24,
        "leg_gross": 0.5,
        "weight_cap_abs": 0.3,
        "min_side_members": 4,
        "decision_clock": "weekly Monday 00:00:00Z",
        "fill_convention": "slot_open_first_bar_at_or_after_T_plus_15m",
        "window": ["2025-08-22T00:00:00Z", "2026-08-21T00:00:00Z"],
    },
    NEIGHBOUR_ARM: {
        "book": "oitd_hysteresis_tercile",
        "signal": "unwind_duration",
        "turnover_days": 56,
        "oi_stamps": 7,
        "oi_stamp_span_days": 10,
        "mark_max_age_hours": 24,
        "leg_gross": 0.5,
        "weight_cap_abs": 0.3,
        "min_side_members": 4,
        "decision_clock": "weekly Monday 00:00:00Z",
        "fill_convention": "slot_open_first_bar_at_or_after_T_plus_15m",
        "window": ["2025-08-22T00:00:00Z", "2026-08-21T00:00:00Z"],
    },
    CONTROL_ARM: {
        "book": "oitd_hysteresis_tercile",
        "signal": "turnover_only",
        "turnover_days": 28,
        "oi_numerator": "deleted",
        "sort": "descending_turnover",
        "leg_gross": 0.5,
        "weight_cap_abs": 0.3,
        "min_side_members": 4,
        "decision_clock": "weekly Monday 00:00:00Z",
        "fill_convention": "slot_open_first_bar_at_or_after_T_plus_15m",
        "window": ["2025-08-22T00:00:00Z", "2026-08-21T00:00:00Z"],
    },
}

#: Frozen schedule / folds strings (pinned V12 fold calendar, byte-for-byte).
DECISION_CLOCK = (
    "weekly Monday 00:00:00Z; features from completed 15m bars (day buckets), "
    "daily OI snapshots and mark snapshots with availability stamp <= the "
    "decision stamp; ONE declared execution lag (slot-open fill at T+15m)"
)
FOLDS_CONTRACT = (
    "chronological 3-fold force-flat per the frozen V12 fold calendar "
    "(F0 2025-08-22..2025-12-21, F1 2025-12-22..2026-04-21, "
    "F2 2026-04-22..2026-08-21) with the frozen 1-stamp purge; per-family "
    "cell matrices derived from the family's frozen folds contract (L-V11-1)"
)
FOLD_WINDOWS: tuple[tuple[str, str, str], ...] = (
    ("F0", "2025-08-22", "2025-12-21"),
    ("F1", "2025-12-22", "2026-04-21"),
    ("F2", "2026-04-22", "2026-08-21"),
)
PURGE_DAYS = 1
MIN_FOLDS = 3

#: Declared cost floors (contract_v10, inherited unchanged; identical to
#: every scored crypto family since V10 -- never loosened).
TAKER_FEE_FLOOR_BPS = float(TAKER_FEE_FLOOR_BPS_V10)
ADVERSE_TICK_SLIP_FLOOR = int(ADVERSE_TICKS_SLIPPAGE_FLOOR_V10)
FILL_CLOCK = FILL_CLOCK_V10

#: Pinned book constants (OITD.json item5, verbatim numbers).
LEG_GROSS = 0.5
CAP_MAX = 0.30
MIN_SIDE_MEMBERS = 4
#: Both terciles need >= MIN_SIDE_MEMBERS members: n//3 >= 4 -> n >= 12.
MIN_ELIGIBLE = 12

#: Pinned signal constants (OITD.json item4, verbatim numbers).
OI_STAMPS_REQUIRED = 7
OI_STAMP_SPAN_DAYS = 10
MARK_MAX_AGE_HOURS = 24
TURNOVER_DAYS_ANCHOR = 28
TURNOVER_DAYS_NEIGHBOUR = 56

#: 15m bars per fully covered UTC day bucket.
BARS_PER_DAY = 96

#: The ONE declared execution lag: orders release T + 15 minutes and fill at
#: the slot-open of the first 15m bar at/after release (00:15Z for a Monday
#: 00:00:00Z decision).  Stress "+1 event delay" shifts to the NEXT slot.
ORDER_RELEASE_LAG_NS = 900_000_000_000  # 15 minutes == one 15m slot

BAR_INTERVAL_NS = 900_000_000_000

STATUS_OK = "OK"

#: Preregistered causal-control falsification rule (OITD.json item6,
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

    THE pinned convention (A9-F engine-convention caveat, selection freeze):
    a decision at T reads only records with availability <= T, and a fill at
    slot-open F reads only records with availability <= F (a record stamped
    00:30Z is NOT readable by the 00:15Z fill -- e.g. the covering bar's own
    close).  Availability for these native observables is the record's own
    stamp (bar close boundary / OI snapshot stamp / mark snapshot stamp);
    retrieval time never substitutes (crypto_compat semantics).
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
# Frozen identity accessors
# --------------------------------------------------------------------------- #
def frozen_arm_config(arm_id: str) -> dict:
    """The exact frozen ``config`` payload of one arm (digest input)."""
    arm_id = str(arm_id)
    if arm_id not in _FROZEN_CONFIGS:
        raise ContractViolation(f"unknown arm_id {arm_id!r}; expected {ARM_IDS}")
    return dict(_FROZEN_CONFIGS[arm_id])


def frozen_identity(arm_id: str) -> StrategyIdentity:
    """The frozen V13 identity of one arm (digest equality is test-pinned)."""
    arm_id = str(arm_id)
    if arm_id not in ARM_CONFIG_IDS:
        raise ContractViolation(f"unknown arm_id {arm_id!r}; expected {ARM_IDS}")
    return StrategyIdentity(
        strategy_id=STRATEGY_ID,
        family_id=FAMILY_ID,
        arm_config_id=ARM_CONFIG_IDS[arm_id],
        direction=DIRECTION,
        window_start_iso=WINDOW_START_ISO,
        window_end_iso=WINDOW_END_ISO,
        benchmark_symbols_excluded=(BENCHMARK_SYMBOL,),
        funding_sign_convention=FUNDING_SIGN_CONVENTION,
        matrix_cohort_hint=MATRIX_COHORT_HINT,
        arm_id=arm_id,
        config=frozen_arm_config(arm_id),
    )


def frozen_arm_digest_report() -> dict[str, dict[str, Any]]:
    """Recomputed vs recorded ``arm_config_digest`` per arm (honest report)."""
    report: dict[str, dict[str, Any]] = {}
    for arm_id in ARM_IDS:
        identity = frozen_identity(arm_id)
        computed = arm_config_digest(identity, arm_id=arm_id)
        recorded = FROZEN_ARM_CONFIG_DIGESTS[arm_id]
        report[arm_id] = {
            "computed_from_identity": computed,
            "recorded_in_freeze": recorded,
            "match": bool(computed == recorded),
        }
    return report


def arm_signal_spec(arm_id: str) -> tuple[str, int, bool]:
    """``(signal_kind, turnover_days, sort_ascending)`` of one frozen arm."""
    arm_id = str(arm_id)
    if arm_id not in _ARM_SIGNAL:
        raise ContractViolation(f"unknown arm_id {arm_id!r}; expected {ARM_IDS}")
    return _ARM_SIGNAL[arm_id]


def is_control_arm(arm_id: str) -> bool:
    return str(arm_id) == CONTROL_ARM


def evaluate_control_gate(*, anchor_passes: bool, control_passes: bool) -> dict[str, Any]:
    """The preregistered control rule (OITD.json item6) as a decision table.

    IF the anchor passes the three gates {after-cost expectancy > 0,
    position PF >= 1.10, >= 2/3 folds positive} THEN the control must fail
    at least one of them; if the control ALSO passes all three, the edge is
    a pure turnover-level (flow) effect, the OI stock is redundant, and the
    family is FALSIFIED as a distinct positioning-structure mechanism.
    """
    anchor = bool(anchor_passes)
    control = bool(control_passes)
    if anchor and control:
        verdict = CONTROL_GATE_FALSIFIED
    else:
        verdict = CONTROL_GATE_PASS
    return {
        "rule": (
            "IF anchor OITD-28D passes {expectancy>0, PF>=1.10, >=2/3 folds "
            "positive} THEN CTL-FLOW-ONLY must fail at least one; both "
            "passing falsifies the family (edge is pure turnover flow)"
        ),
        "anchor_passes": anchor,
        "control_passes": control,
        "verdict": verdict,
    }


# --------------------------------------------------------------------------- #
# PIT feature primitives (fail-closed; availability stamp == record stamp)
# --------------------------------------------------------------------------- #
def mean_daily_turnover(
    day_turnover: Mapping[int, float],
    stamp_ns: int,
    *,
    window_days: int,
) -> Optional[float]:
    """Mean daily dollar turnover over the ``window_days`` completed UTC day
    buckets ending immediately before the stamp's own day bucket.

    Keys of ``day_turnover`` are UTC DAY INDICES (``ns // DAY_NS``; the
    audit loader buckets each completed bar by the day containing its
    slot).  Exactly the completed 15m bars with close stamps in
    ``(T-W, T]``: T is a Monday 00:00:00Z decision stamp, so the window is
    the ``W`` full UTC trading days ``[T-W, T)`` whose 96th bar closes at
    (or within a hair of) the bucket boundary.  EVERY day must be present
    in ``day_turnover`` (incomplete days are omitted by the loader and
    simply missing here); a missing day is a GAP -- fail closed (``None``),
    never interpolated.  Non-positive or non-finite daily values also fail
    closed.
    """
    stamp = int(stamp_ns)
    days = int(window_days)
    if days <= 0:
        raise ContractViolation("window_days must be positive")
    stamp_day_index = stamp // DAY_NS
    values: list[float] = []
    for k in range(1, days + 1):
        day_index = stamp_day_index - k
        raw = day_turnover.get(int(day_index))
        if raw is None:
            return None  # gap: fail closed, never filled
        value = float(raw)
        if not (value > 0.0) or value != value or value in (float("inf"), float("-inf")):
            return None
        values.append(value)
    total = 0.0
    for value in values:
        total += value
    return total / float(days)


def oi7_mean(
    series: Sequence[tuple[int, float]],
    stamp_ns: int,
    *,
    n_stamps: int = OI_STAMPS_REQUIRED,
    span_days: int = OI_STAMP_SPAN_DAYS,
) -> Optional[float]:
    """Mean of the latest ``n_stamps`` daily OI records with stamp <= T.

    All stamps must lie within the trailing ``span_days``; fewer than
    ``n_stamps`` records in the span -> INELIGIBLE (``None``, fail-closed,
    no back-fill).  Values must be finite positive (OI is a level).
    """
    stamp = int(stamp_ns)
    span_ns = int(span_days) * DAY_NS
    window: list[tuple[int, float]] = []
    for ts, value in series:
        t = int(ts)
        if t > stamp:
            break  # series is availability-ordered; later rows are unreadable
        if t <= stamp - span_ns:
            continue
        v = float(value)
        if not (v > 0.0) or v != v or v in (float("inf"), float("-inf")):
            return None  # non-positive OI: fail closed
        window.append((t, v))
    if len(window) < int(n_stamps):
        return None
    latest = window[-int(n_stamps):]
    total = 0.0
    for _t, v in latest:
        total += v
    # every consumed record must be available by the stamp (explicit gate)
    assert_inputs_available(
        (t for t, _v in latest), as_of_ns=stamp, context="oi7_mean"
    )
    return total / float(len(latest))


def latest_mark(
    series: Sequence[tuple[int, float]],
    stamp_ns: int,
    *,
    max_age_ns: int = MARK_MAX_AGE_HOURS * HOUR_NS,
) -> Optional[float]:
    """Latest mark record with stamp <= T within the trailing max age."""
    stamp = int(stamp_ns)
    chosen: Optional[tuple[int, float]] = None
    for ts, value in series:
        t = int(ts)
        if t > stamp:
            break
        chosen = (t, float(value))
    if chosen is None:
        return None
    t, v = chosen
    if stamp - t > int(max_age_ns):
        return None
    if not (v > 0.0) or v != v or v in (float("inf"), float("-inf")):
        return None
    assert_inputs_available((t,), as_of_ns=stamp, context="latest_mark")
    return v


def signal_scores_at(
    arm_id: str,
    *,
    day_turnover_by_symbol: Mapping[str, Mapping[int, float]],
    stamp_ns: int,
    universe: Sequence[str],
    oi_by_symbol: Optional[Mapping[str, Sequence[tuple[int, float]]]] = None,
    mark_by_symbol: Optional[Mapping[str, Sequence[tuple[int, float]]]] = None,
) -> dict[str, float]:
    """PIT signal scores of one arm at one Monday 00:00:00Z stamp.

    Anchor / neighbour: ``D = OI7 x MK / TO(W)`` (higher = longer unwind
    duration).  Control: ``TO(28d)`` alone, and the control arm REFUSES OI
    or mark inputs outright (the numerator is deleted by construction --
    running it with either injected raises :class:`ContractViolation`).
    A symbol whose denominator, OI history or mark is unavailable is simply
    INELIGIBLE at the stamp (fail-closed, never guessed).
    """
    arm_id = str(arm_id)
    kind, window_days, _asc = arm_signal_spec(arm_id)
    if kind == "turnover_only":
        if oi_by_symbol or mark_by_symbol:
            raise ContractViolation(
                "CTL-FLOW-ONLY must run with the OI numerator deleted: "
                "oi_by_symbol/mark_by_symbol must be empty/None"
            )
    universe_symbols = sorted(str(s) for s in universe)
    if BENCHMARK_SYMBOL in universe_symbols:
        raise ContractViolation(
            "the pinned benchmark leg can never enter the tradeable universe"
        )
    stamp = int(stamp_ns)
    scores: dict[str, float] = {}
    for sym in universe_symbols:
        days = day_turnover_by_symbol.get(sym) or {}
        turnover = mean_daily_turnover(days, stamp, window_days=int(window_days))
        if turnover is None or turnover <= 0.0:
            continue  # INELIGIBLE (gap/non-positive denominator)
        if kind == "turnover_only":
            scores[sym] = float(turnover)
            continue
        oi_series = (oi_by_symbol or {}).get(sym) or ()
        mark_series = (mark_by_symbol or {}).get(sym) or ()
        oi7 = oi7_mean(oi_series, stamp)
        if oi7 is None:
            continue  # INELIGIBLE (insufficient OI history, fail-closed)
        mark = latest_mark(mark_series, stamp)
        if mark is None:
            continue  # INELIGIBLE (stale/absent mark)
        duration = oi7 * mark / turnover
        if not (duration > 0.0) or duration != duration:
            continue
        scores[sym] = float(duration)
    return scores


# --------------------------------------------------------------------------- #
# Per-stamp target book (delegates to the frozen hysteresis book builder)
# --------------------------------------------------------------------------- #
def compute_targets_at(
    arm_id: str,
    *,
    day_turnover_by_symbol: Mapping[str, Mapping[int, float]],
    stamp_ns: int,
    universe: Sequence[str],
    prev_book: Optional[Mapping[str, float]] = None,
    oi_by_symbol: Optional[Mapping[str, Sequence[tuple[int, float]]]] = None,
    mark_by_symbol: Optional[Mapping[str, Sequence[tuple[int, float]]]] = None,
    gross: float = LEG_GROSS * 2.0,
) -> dict[str, Any]:
    """Frozen target book of one arm at one Monday 00:00:00Z stamp.

    Ranks the eligible universe by the PIT signal and delegates to
    :func:`research.v13.families.oitd.book.build_hysteresis_book` with the
    previous retained book (``None`` = flat start).  Fail-closed on
    insufficient breadth (:class:`EligibilityShortfall`) and on any
    availability violation.  No PnL is computed.
    """
    from research.v13.families.oitd.book import build_hysteresis_book

    arm_id = str(arm_id)
    kind, window_days, sort_ascending = arm_signal_spec(arm_id)
    stamp = int(stamp_ns)
    scores = signal_scores_at(
        arm_id,
        day_turnover_by_symbol=day_turnover_by_symbol,
        stamp_ns=stamp,
        universe=universe,
        oi_by_symbol=oi_by_symbol,
        mark_by_symbol=mark_by_symbol,
    )
    book = build_hysteresis_book(
        scores,
        prev_book=prev_book,
        sort_ascending=bool(sort_ascending),
        leg_gross=LEG_GROSS,
        cap_max=CAP_MAX,
        min_side_members=MIN_SIDE_MEMBERS,
        min_eligible=MIN_ELIGIBLE,
    )
    # Honest per-symbol signal coverage at this stamp: computable scores
    # over the whole declared universe (the book builder cannot know the
    # universe, so the ratio it reports internally is book-local).
    honest_availability = len(scores) / float(max(len({str(s) for s in universe}), 1))
    weights = {str(sym): float(w) for sym, w in book["weights"]}
    ordered_weights = {sym: weights[sym] for sym in sorted(weights)}
    payload = {
        "schema": "v13i.oitd.targets.v1",
        "family_id": FAMILY_ID,
        "arm_id": arm_id,
        "status": STATUS_OK,
        "weights": [[sym, ordered_weights[sym]] for sym in sorted(ordered_weights)],
        "longs": [[sym, round(float(w), 12)] for sym, w in book["longs"]],
        "shorts": [[sym, round(float(w), 12)] for sym, w in book["shorts"]],
        "carried_forward": bool(book["carried_forward"]),
        "reason_code": book["reason_code"],
        "decision_ns": stamp,
        "diagnostics": {
            "stamp_ns": stamp,
            "stamp_iso": iso_utc(stamp),
            "n_eligible": int(book["n_eligible"]),
            "n_longs": int(book["n_longs"]),
            "n_shorts": int(book["n_shorts"]),
            "signal_kind": kind,
            "turnover_days": int(window_days),
            "sort_ascending": bool(sort_ascending),
            "ranks": [[sym, int(r)] for sym, r in book["ranks"]],
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
    pinned rule to the frozen V12 audit loader (equality test-pinned
    against it; frozen code is reused, never modified).
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
    """The ONE declared execution lag, pinned (A9-F engine convention).

    Orders release at ``decision + 15m``; the fill reference is the OPEN
    price of the FIRST completed 15m bar whose slot-open instant is >= the
    release instant (next-allowed-fill: for a Monday 00:00:00Z decision,
    the 00:15Z slot).  Stress ``+1 event delay`` shifts to the NEXT slot's
    open (strictly later completed bars).  Missing slots -> NO event
    (never a shifted substitute).  Only the chosen bar's OPEN is consumed:
    it is observable AT the slot-open instant, while the bar's close stamp
    (slot-open + 15m) is NOT readable by this fill -- the availability
    horizon of the fill is its slot-open instant.
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
    # slot-open stamps must be unique per symbol (one completed bar per slot)
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
    # THE invariant: the fill never happens before the release instant ...
    if fill.fill_open_ns < release:
        raise ContractViolation("next-allowed-fill violated: slot-open < release")
    # ... and the fill's readability horizon is its own slot-open instant
    # (the consumed input is the bar OPEN at that instant; the bar's close
    # stamp is strictly later and is never read by the fill).
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


def fold_assignments(instants: Sequence[int]) -> list[tuple[int, str, list[int]]]:
    """Assign decision stamps to the PINNED F0/F1/F2 calendar windows."""
    from research.v11.families.oilever_delev.strategy import fold_assignments as _assign

    return _assign(list(instants))


def purge_fold_members(
    assignments: Sequence[tuple[int, str, list[int]]],
    *,
    purge_days: int = PURGE_DAYS,
) -> list[tuple[int, str, list[int], list[int]]]:
    """Strip the trailing ``purge_days`` instants of each fold (purge gaps).

    A book opened inside a fold therefore always realises inside that fold
    (force-flat at fold boundaries under the adapter's accounting).
    """
    from research.v11.families.oilever_delev.strategy import (
        purge_fold_members as _purge,
    )

    return _purge(list(assignments), purge_days=int(purge_days))


def window_start_ns() -> int:
    return parse_iso_utc(WINDOW_START_ISO)


def window_end_ns() -> int:
    return parse_iso_utc(WINDOW_END_ISO)


__all__ = [
    "ADVERSE_TICK_SLIP_FLOOR",
    "ANCHOR_ARM",
    "ARM_CONFIG_IDS",
    "ARM_IDS",
    "ARM_ROLES",
    "BAR_INTERVAL_NS",
    "BARS_PER_DAY",
    "BENCHMARK_SYMBOL",
    "CAP_MAX",
    "CONTROL_ARM",
    "CONTROL_GATE_FALSIFIED",
    "CONTROL_GATE_PASS",
    "DECISION_CLOCK",
    "DIRECTION",
    "FAMILY_ID",
    "FILL_CLOCK",
    "FOLD_WINDOWS",
    "FOLDS_CONTRACT",
    "FROZEN_ARM_CONFIG_DIGESTS",
    "LEG_GROSS",
    "MARK_MAX_AGE_HOURS",
    "MATRIX_COHORT_HINT",
    "MIN_ELIGIBLE",
    "MIN_FOLDS",
    "MIN_SIDE_MEMBERS",
    "NEIGHBOUR_ARM",
    "OI_STAMPS_REQUIRED",
    "OI_STAMP_SPAN_DAYS",
    "ORDER_RELEASE_LAG_NS",
    "PURGE_DAYS",
    "STATUS_OK",
    "STRATEGY_ID",
    "TAKER_FEE_FLOOR_BPS",
    "TURNOVER_DAYS_ANCHOR",
    "TURNOVER_DAYS_NEIGHBOUR",
    "WINDOW_END_ISO",
    "WINDOW_START_ISO",
    "LookaheadViolation",
    "arm_signal_spec",
    "assert_inputs_available",
    "compute_targets_at",
    "evaluate_control_gate",
    "fold_assignments",
    "frozen_arm_config",
    "frozen_arm_digest_report",
    "frozen_identity",
    "iso_utc",
    "latest_mark",
    "mean_daily_turnover",
    "next_allowed_fill",
    "oi7_mean",
    "parse_iso_utc",
    "purge_fold_members",
    "signal_scores_at",
    "snap_close_to_boundary",
    "stamp_calendar",
    "window_end_ns",
    "window_start_ns",
]
