"""Frozen strategy primitives for the A14-V14-A5-BASISLV-PREMFADE family.

This module implements the FROZEN contract pinned by
``research/control/v14_run/selection_freeze_v14.json`` +
``research/proposals/v14/a5/BASISLV-PREMFADE.md`` (selection-freeze SHA
``d16341f``) verbatim -- no tuning, no grids, no parameter changes.  It is a
pure, data-injected library: every observable (completed 15m basis-route
premium buckets, completed 15m execution bars, funding settlements, tick
sizes) is supplied by the caller, so the same primitives run on synthetic
fixtures and on the A9-F staged observables.  Nothing here reads the
catalog, computes a scored outcome, or persists anything.

SIGNAL (basis route ONLY, fusion availability semantics): at a decision
instant ``T`` (Monday 00:00:00Z, on the 15m grid) a symbol's premium level
is the mean of the per-bucket perp-vs-index premium over the trailing
``FORMATION_BUCKETS_ANCHOR`` (2688 = 28d) / ``FORMATION_BUCKETS_NEIGHBOUR``
(5376 = 56d) COMPLETED 15m buckets whose close boundaries lie in
``(T - N*15m, T]``::

    p_b = (futuresPrice_b - indexPrice_b) / indexPrice_b   (basis route)
    b_i(T) = mean of p_b over the N completed buckets

A decision at T never reads a row whose availability stamp is > T
(``research/data_fusion/crypto_compat.py`` semantics; the frozen lag
convention: a bucket covering ``[t_open, t_open+15m)`` is available at its
close ``t_close = t_open + 15m``; the last admissible bucket for a Monday
00:00Z stamp is ``[Sun 23:45, Mon 00:00)``; no partial bucket is ever
read).  EVERY slot of the formation window must exist and be available;
one missing/unavailable slot REFUSES the symbol at that stamp (fail-closed,
no back-fill, no synthesized tail -- L-V12-5).  The premium klines /
markPriceKlines / indexPriceKlines routes are DECLARED OUT OF SCOPE for the
signal (proposal section 10): the conditioning space is the basis route
alone, with the endpoint's own ``basisRate`` used only as a staging
identity cross-check (declared absolute tolerance, fail-closed).

BOOK: long the ``floor(n_eligible/3)`` LOWEST-premium names (the low /
discount tier), short the ``floor(n_eligible/3)`` HIGHEST-premium names
(the high / premium tier), equal weight ``1/(2*floor(n_eligible/3))`` per
held symbol, gross 1.0, middle tercile flat; ranks ascend by
``(b_i, symbol id)`` -- exact score ties break by symbol id ascending
(declared a priori).  Fewer than ``MIN_ELIGIBLE`` (12) eligible names
raises :class:`EligibilityShortfall` (the stamp refuses and the refusal is
counted; fail closed).  ``max |weight| = 1/(2*floor(12/3)) = 1/8 = 0.125
<= 0.30`` at every stamp by construction (L-V11-2 co-design satisfied) and
is asserted, never assumed.  BTCUSDT (bars) is benchmark/beta context only
and can never enter the book.

ARMS (exactly 3): anchor ``BASISLV-PREMFADE-28D`` (2688 buckets),
neighbour ``BASISLV-PREMFADE-56D`` (5376 buckets, same mechanism/book),
causal negative control ``BASISLV-PREMFADE-28D-INV`` (the EXACT
sign-inverted anchor book, weights element-wise negated; its preregistered
falsification rule lives in
:mod:`research.v14.families.basislv_premfade.gate_runner`).

SCHEDULE / FOLDS: weekly Monday 00:00:00Z stamps over the blind-S0 screen
window 2025-08-22T00:00:00Z..2026-08-21T00:00:00Z (52 stamps; first
2025-08-25).  Chronological F0/F1/F2 (F0 2025-08-22..2025-12-21,
F1 2025-12-22..2026-04-21, F2 2026-04-22..2026-08-21) with the 1-day purge
realised by the V12 frozen fold contract as the V11-lineage TRAILING
calendar zone (each fold's last day before its end boundary; the identical
``purge_fold_members`` convention measured at 51 effective Mondays,
17/17/17, by both the V13 implementation and the A9-F feasibility run;
A9F-OBS-4 recorded).  Exactly one stamp (2026-04-20, the F1-end purge
zone) is purged, leaving 51 effective Mondays.  Holding spans are
force-flat-clamped at their fold's end boundary; the F0 fold-terminal
effective stamp (2025-12-15) is answered with the FLAT book so no position
crosses a fold boundary (the frozen V13 fold-terminal precedent).

EXECUTION (ONE declared lag): fills at the close of the first completed
15m bar STRICTLY after ``T`` (Monday 00:15:00Z close); the +1-delay stress
walks to the next completed bar (Monday 00:30:00Z close).  A genuinely
missing slot advances to the next completed bar (a real execution event --
never a shifted substitute); a fill bar whose availability exceeds its own
close refuses (you cannot transact on a row you cannot yet read).

PRICE-ONLY FAILURE CLAUSE: the price-only vs total expectancy split is
NEVER computed here.  The scored layer (Phase E) computes it and passes it
to :mod:`research.v14.families.basislv_premfade.gate_runner`, which applies
the preregistered clause (price-only <= 0 while total is positive only via
native funding credits => carry-harvest artifact => family rejected) as a
gate input.

COSTS (L-V14-0 remediated kernel, binding): charged on FILLS ONLY --
exactly once per fill, never per holding-day, never per stamp on open
positions; real perp-metadata tick sizes (no uniform stubs); native funding
settlements on held legs exactly once per settlement; scored cells report
cost broken out by fills vs holding terms.

DROP-ONE (wording pinned exactly -- see :data:`DROP_ONE_PIN`).

No PnL, no returns, no scored metric is computed anywhere in this module.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Sequence

import numpy as np

from research.adapter_v10.protocol import (
    ContractViolation,
    DEFAULT_WEIGHT_CAP_MAX,
    WEIGHT_TOL,
)
from research.adapter_v10.stress import HELD_WEIGHT_TOL
from research.v11.families.oilever_delev.strategy import (
    iso_utc,
    parse_iso_utc,
    weekly_mondays,
)

# --------------------------------------------------------------------------- #
# Frozen constants (selection_freeze_v14.json + BASISLV-PREMFADE proposal)
# --------------------------------------------------------------------------- #
FAMILY_ID = "A14-V14-A5-BASISLV-PREMFADE"
STRATEGY_ID = "hyp_a14_v14_basislv_premfade"
#: dollar-neutral long/short tercile book; BTC beta is a CONTEXT adjustment
#: at the gate only and never alters leg weights (proposal section 7).
DIRECTION = "long_short_dollar_neutral"
BENCHMARK_SYMBOL = "BTCUSDT"
MATRIX_COHORT_HINT = "v14"

WINDOW_START_ISO = "2025-08-22T00:00:00Z"
WINDOW_END_ISO = "2026-08-21T00:00:00Z"

FUNDING_SIGN_CONVENTION = "LONG_PAYS_POSITIVE_RATE"

ANCHOR_ARM = "BASISLV-PREMFADE-28D"
NEIGHBOUR_ARM = "BASISLV-PREMFADE-56D"
CONTROL_ARM = "BASISLV-PREMFADE-28D-INV"
ARM_ROLES: dict[str, str] = {
    ANCHOR_ARM: "anchor",
    NEIGHBOUR_ARM: "neighbour",
    CONTROL_ARM: "causal_negative_control",
}
ARM_IDS: tuple[str, ...] = tuple(sorted(ARM_ROLES))
ANCHOR_ARM_CONFIG_ID = "28D-PREMIUM-LEVEL"
NEIGHBOUR_ARM_CONFIG_ID = "56D-PREMIUM-LEVEL"
CONTROL_ARM_CONFIG_ID = "28D-PREMIUM-LEVEL-INVERTED"
ARM_CONFIG_IDS: dict[str, str] = {
    ANCHOR_ARM: ANCHOR_ARM_CONFIG_ID,
    NEIGHBOUR_ARM: NEIGHBOUR_ARM_CONFIG_ID,
    CONTROL_ARM: CONTROL_ARM_CONFIG_ID,
}

DAY_NS = 86_400_000_000_000
BUCKET_NS = 900_000_000_000  # one 15m basis/bars bucket
FORMATION_BUCKETS_ANCHOR = 2688  # 28d x 96 completed buckets/day
FORMATION_BUCKETS_NEIGHBOUR = 5376  # 56d x 96
FORMATION_DAYS_ANCHOR = 28
FORMATION_DAYS_NEIGHBOUR = 56
HOLDING_DAYS = 7
GROSS_TARGET = 1.0
CAP_MAX = float(DEFAULT_WEIGHT_CAP_MAX)
#: Minimum eligible names for a stamp to trade (proposal section 5/8).
MIN_ELIGIBLE = 12
#: Side size ``k = floor(n_eligible / 3)``; at the 12-name floor k = 4 so
#: the designed weight 1/(2k) = 1/8 = 0.125 <= 0.30 at EVERY admissible stamp.
SIDE_DIVISOR = 3

#: Frozen per-arm ``(formation_buckets, invert)`` mapping.  The control arm
#: is the EXACT sign-inverted anchor book (weights element-wise negated).
ARM_SPECS: dict[str, tuple[int, bool]] = {
    ANCHOR_ARM: (FORMATION_BUCKETS_ANCHOR, False),
    NEIGHBOUR_ARM: (FORMATION_BUCKETS_NEIGHBOUR, False),
    CONTROL_ARM: (FORMATION_BUCKETS_ANCHOR, True),
}

#: Frozen schedule / folds strings (proposal section 5; A9-F measurement).
DECISION_CLOCK = (
    "weekly, every Monday 00:00:00Z; 52 scheduled Mondays in the blind-S0 "
    "screen window 2025-08-22..2026-08-21 (first 2025-08-25), 51 effective "
    "after the 1-day purge (2026-04-20 in the F1 trailing purge zone); one "
    "declared execution lag"
)
FILL_RULE = (
    "fills at the close of the first completed 15m bar strictly after the "
    "decision stamp (Monday 00:15:00Z close); stress +1 event delay fills "
    "at the Monday 00:30:00Z close"
)
FOLDS_CONTRACT = (
    "chronological F0/F1/F2 force-flat per the frozen V12 fold contract "
    "(F0 2025-08-22..2025-12-21, F1 2025-12-22..2026-04-21, "
    "F2 2026-04-22..2026-08-21) with the 1-day purge as the trailing "
    "calendar zone of each fold (V11-lineage purge_fold_members convention, "
    "the reading measured at 51 effective Mondays 17/17/17 by both the V13 "
    "implementation and A9-F; A9F-OBS-4 recorded); exactly one stamp "
    "(2026-04-20) is purged"
)
#: Pinned fold calendar windows: ``[start 00:00Z, end 00:00Z)`` per fold;
#: the purge zone of a fold is ``[end - PURGE_DAYS days, end)``.
FOLD_WINDOWS: tuple[tuple[str, str, str], ...] = (
    ("F0", "2025-08-22", "2025-12-21"),
    ("F1", "2025-12-22", "2026-04-21"),
    ("F2", "2026-04-22", "2026-08-21"),
)
PURGE_DAYS = 1
MIN_FOLDS = 3
MIN_DECISIONS_PER_FOLD = 15

#: The first decision stamp of the frozen window (2025-08-25 is a Monday);
#: the first-stamp warmup must be satisfiable from PRE-WINDOW data (the
#: neighbour needs basis buckets back to 2025-06-30, inside the authorized
#: window 2024-08-20..2026-08-21).
FIRST_STAMP_ISO = "2025-08-25T00:00:00Z"
FIRST_STAMP_WARMUP_FROM_ISO = "2025-06-30T00:00:00Z"

#: The single stamp measured inside the F1 trailing 1-day purge zone
#: (V11-lineage purge convention; A9-F measured 51 effective Mondays).
F1_PURGED_STAMP_ISO = "2026-04-20T00:00:00Z"

#: The F0 fold-terminal effective stamp: the next calendar stamp belongs to
#: F1, so the boundary action IS the flat transition (fold-terminal
#: force-flat; V13 frozen precedent -- no position crosses a fold boundary).
F0_FOLD_TERMINAL_STAMP_ISO = "2025-12-15T00:00:00Z"

STATUS_OK = "OK"

#: Signal identity strings (digest payload / diagnostics).
SIGNAL_NAME = "mean_15m_perp_index_premium_level"
SIGNAL_EVALUATION = (
    "b_i(T) = mean of p_b over the trailing N completed 15m buckets; "
    "p_b = (futuresPrice_b - indexPrice_b) / indexPrice_b (basis route)"
)
SIGNAL_ROUTE = (
    "/futures/data/basis contractType=PERPETUAL period=15m pair=<SYM>; "
    "fields futuresPrice/indexPrice (+ basis/basisRate identity cross-check)"
)
#: Frozen lag convention (proposal section 4, verbatim intent).
LAG_CONVENTION = (
    "a period bucket covering [t_open, t_open+15m) is available at its "
    "close t_close = t_open+15m (conservative bar-close availability class); "
    "a decision at T uses ONLY fully-closed prior buckets with t_close <= T; "
    "the last admissible bucket for a Monday 00:00Z stamp is "
    "[Sun 23:45, Mon 00:00); no partial bucket is ever read"
)
#: Staging identity check tolerance (ABSOLUTE band; A9F-OBS-3: an absolute
#: band is required -- a relative band flags near-zero-premium buckets
#: spuriously; 1e-4 because the endpoint's own basisRate is rounded to 4
#: decimal places, the same band A9-F measured across all 19 names).
BASIS_IDENTITY_TOL_ABS = 1e-4

#: Refusal reason codes (fail-closed; never guessed around).
REASON_MISSING_OR_NON_FINITE_SLOT = "MISSING_OR_NON_FINITE_SLOT"
REASON_UNAVAILABLE_ROW = "UNAVAILABLE_ROW"
REASON_INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"

#: The price-only failure clause is a GATE INPUT: the scored layer computes
#: the split, this lane only pins the rule text and carries the contract.
PRICE_ONLY_CLAUSE_TEXT = (
    "price-only expectancy <= 0 while total expectancy is positive only "
    "through native funding credits => the mechanism is a carry harvest, "
    "not a price-unwind mechanism; family REJECTED as declared ex ante "
    "(proposal sections 2(e)/9; V6 adjacency).  The price-only / total "
    "split is computed by the scored layer and applied by "
    "research.v14.families.basislv_premfade.gate_runner; it is never "
    "computed in this package."
)

#: Drop-one wording pinned exactly (proposal section 8, verbatim intent).
DROP_ONE_PIN = (
    "drop-one identifies the EARLIEST fold-stamp carrying the largest held "
    "|weight| across the whole arm schedule (chronological tie-break across "
    "stamps; under the equal-weight book all legs at one stamp tie, so the "
    "stamp-level choice is outcome-free); at that stamp it drops the single "
    "HELD leg with the LARGEST |b_i(T)| -- the most extreme premium "
    "expression, the strongest mechanism instantiation (exact |b_i| ties "
    "break by lexicographically smallest symbol id ascending; an unheld "
    "symbol can never be selected, non-vacuousness L-V11-7).  "
    "Renormalization (proposal section 8, literal text): the remaining "
    "2k-1 held legs KEEP their sides and are renormalized to gross 1.0 as "
    "equal legs at 1/(2k-1) each; the middle tercile stays flat and the "
    "benchmark is never held.  The family survives only if the anchor's "
    "fold-sign pattern and the control rule's outcome are unchanged."
)


class EligibilityShortfall(ContractViolation):
    """A stamp has fewer than ``MIN_ELIGIBLE`` eligible names -- no book."""


# --------------------------------------------------------------------------- #
# Availability-carrying completed 15m series (basis route / execution bars)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class BasisRouteSeries:
    """Boundary-indexed completed 15m basis-route premium series.

    Slots are indexed by their CLOSE boundary: slot ``k`` covers
    ``[origin_ns + (k-1)*BUCKET, origin_ns + k*BUCKET)`` and is available at
    its close boundary (the frozen bar-close availability class).  A slot
    with NO admissible row carries NaN in ``premium`` (a gap -- never
    back-filled).  ``available_ns`` carries each row's fusion availability
    stamp (honest route rows: exactly their close boundary); a late row may
    carry a later stamp, in which case decisions at or before that stamp
    refuse the row (fail closed).
    """

    origin_ns: int
    premium: np.ndarray
    available_ns: np.ndarray

    def __post_init__(self) -> None:
        n = self.premium.shape[0]
        if self.available_ns.shape[0] != n:
            raise ContractViolation("basis route arrays must share one length")
        if int(self.origin_ns) % BUCKET_NS != 0:
            raise ContractViolation("basis route origin must sit on the 15m grid")
        if int(self.origin_ns) <= 0 or n == 0:
            raise ContractViolation("basis route origin must be positive and non-empty")

    @property
    def end_ns(self) -> int:
        """Exclusive end of the covered grid (one past the last close)."""
        return int(self.origin_ns) + self.premium.shape[0] * BUCKET_NS

    def close_ns(self, index: int) -> int:
        """The close boundary of slot ``index``."""
        return int(self.origin_ns) + int(index) * BUCKET_NS

    def slot_index(self, boundary_ns: int) -> int:
        """Grid index of one 15m close boundary (refuses off-grid stamps)."""
        offset = int(boundary_ns) - int(self.origin_ns)
        if offset < 0 or offset % BUCKET_NS != 0:
            raise ContractViolation(
                f"boundary {boundary_ns} is not on this series' 15m grid"
            )
        return offset // BUCKET_NS


def basis_series_from_rows(
    rows: Sequence[tuple[int, int, float]],
) -> BasisRouteSeries:
    """Build one :class:`BasisRouteSeries` from ``(close_ns, available_ns,
    premium)`` rows.

    Fail-closed: duplicate or off-grid close boundaries, availability
    earlier than the bucket's own close (a bucket cannot be readable before
    it closed) and non-finite premiums are refused; missing slots stay NaN.
    """
    if not rows:
        raise ContractViolation("basis_series_from_rows needs at least one row")
    closes = [int(r[0]) for r in rows]
    for c in closes:
        if c <= 0 or c % BUCKET_NS != 0:
            raise ContractViolation(f"basis bucket close off the 15m grid: {c}")
    origin = min(closes)
    last = max(closes)
    n = (last - origin) // BUCKET_NS + 1
    premium = np.full(n, np.nan, dtype=np.float64)
    available = origin + np.arange(n, dtype=np.int64) * BUCKET_NS
    seen: set[int] = set()
    for close_ns, avail, p in rows:
        idx = (int(close_ns) - origin) // BUCKET_NS
        if int(close_ns) in seen:
            raise ContractViolation(f"duplicate basis bucket close {close_ns}")
        seen.add(int(close_ns))
        value = float(p)
        if not math.isfinite(value):
            raise ContractViolation(f"non-finite premium at close {close_ns}")
        if int(avail) < int(close_ns):
            raise ContractViolation(
                f"availability {avail} precedes the bucket's own close {close_ns}"
            )
        premium[idx] = value
        available[idx] = int(avail)
    return BasisRouteSeries(
        origin_ns=int(origin), premium=premium, available_ns=available
    )


@dataclass(frozen=True)
class BarSeries:
    """Boundary-indexed completed 15m execution bars (close prices only).

    Slot ``k`` covers ``[origin_ns + (k-1)*BUCKET, origin_ns + k*BUCKET)``;
    ``close[k]`` is the bar's close at the slot boundary.  A missing slot
    carries NaN.  ``available_ns`` is the fusion availability stamp (honest
    bars: exactly their close boundary).
    """

    origin_ns: int
    close: np.ndarray
    available_ns: np.ndarray

    def __post_init__(self) -> None:
        n = self.close.shape[0]
        if self.available_ns.shape[0] != n:
            raise ContractViolation("bar arrays must share one length")
        if int(self.origin_ns) % BUCKET_NS != 0:
            raise ContractViolation("bar origin must sit on the 15m grid")
        if int(self.origin_ns) <= 0 or n == 0:
            raise ContractViolation("bar origin must be positive and non-empty")

    @property
    def end_ns(self) -> int:
        return int(self.origin_ns) + self.close.shape[0] * BUCKET_NS

    def slot_index(self, boundary_ns: int) -> int:
        offset = int(boundary_ns) - int(self.origin_ns)
        if offset < 0 or offset % BUCKET_NS != 0:
            raise ContractViolation(
                f"boundary {boundary_ns} is not on this series' 15m grid"
            )
        return offset // BUCKET_NS


def bars_from_rows(rows: Sequence[tuple[int, int, float]]) -> BarSeries:
    """Build one :class:`BarSeries` from ``(close_ns, available_ns, close)`` rows."""
    if not rows:
        raise ContractViolation("bars_from_rows needs at least one row")
    closes = [int(r[0]) for r in rows]
    for c in closes:
        if c <= 0 or c % BUCKET_NS != 0:
            raise ContractViolation(f"bar close off the 15m grid: {c}")
    origin = min(closes)
    last = max(closes)
    n = (last - origin) // BUCKET_NS + 1
    close_arr = np.full(n, np.nan, dtype=np.float64)
    available = origin + np.arange(n, dtype=np.int64) * BUCKET_NS
    seen: set[int] = set()
    for close_ns, avail, px in rows:
        idx = (int(close_ns) - origin) // BUCKET_NS
        if int(close_ns) in seen:
            raise ContractViolation(f"duplicate bar close {close_ns}")
        seen.add(int(close_ns))
        price = float(px)
        if not math.isfinite(price) or price <= 0.0:
            raise ContractViolation(f"non-positive close at boundary {close_ns}")
        if int(avail) < int(close_ns):
            raise ContractViolation(
                f"availability {avail} precedes the bar's own close {close_ns}"
            )
        close_arr[idx] = price
        available[idx] = int(avail)
    return BarSeries(origin_ns=int(origin), close=close_arr, available_ns=available)


# --------------------------------------------------------------------------- #
# The frozen premium-level signal (basis route; fail closed)
# --------------------------------------------------------------------------- #
def premium_level_at(
    series: BasisRouteSeries,
    stamp_ns: int,
    *,
    formation_buckets: int,
) -> tuple[Optional[float], Optional[str]]:
    """``(b_i, None)`` when computable, else ``(None, refusal_reason)``.

    The formation window at ``stamp_ns`` is the trailing ``formation_buckets``
    completed slots with close boundaries in ``(T - N*15m, T]`` -- the last
    admissible bucket for a Monday 00:00Z stamp is ``[Sun 23:45, Mon 00:00)``.
    Fail-closed refusal reasons: :data:`REASON_INSUFFICIENT_HISTORY`,
    :data:`REASON_MISSING_OR_NON_FINITE_SLOT` (every slot must be present and
    finite), :data:`REASON_UNAVAILABLE_ROW` (a row available after T is
    unreadable at T -- a decision at T can never read ``available_time > T``).
    """
    stamp = int(stamp_ns)
    if stamp % BUCKET_NS != 0:
        raise ContractViolation("decision stamps must sit on the 15m grid")
    n = int(formation_buckets)
    if n <= 1:
        raise ContractViolation("formation_buckets must exceed 1")
    offset = stamp - int(series.origin_ns)
    if offset < 0 or offset % BUCKET_NS != 0:
        return None, REASON_INSUFFICIENT_HISTORY
    last_slot = offset // BUCKET_NS
    if last_slot >= series.premium.shape[0] or last_slot + 1 < n:
        return None, REASON_INSUFFICIENT_HISTORY
    lo = last_slot + 1 - n
    window = series.premium[lo : last_slot + 1]
    assert window.shape[0] == n, "formation window slice must be exactly n slots"
    if not bool(np.isfinite(window).all()):
        return None, REASON_MISSING_OR_NON_FINITE_SLOT
    avail = series.available_ns[lo : last_slot + 1]
    if bool((avail > stamp).any()):
        return None, REASON_UNAVAILABLE_ROW
    value = float(window.mean())
    if not math.isfinite(value):
        return None, REASON_MISSING_OR_NON_FINITE_SLOT
    return value, None


def arm_spec(arm_id: str) -> tuple[int, bool]:
    """``(formation_buckets, invert)`` of one frozen arm."""
    arm_id = str(arm_id)
    if arm_id not in ARM_SPECS:
        raise ContractViolation(f"unknown arm_id {arm_id!r}; expected {ARM_IDS}")
    return ARM_SPECS[arm_id]


def side_geometry(n_eligible: int) -> tuple[int, float]:
    """``(k, per_leg_weight)`` of the frozen book at ``n_eligible`` names.

    ``k = floor(n_eligible / 3)`` legs per side, equal weight
    ``gross / (2k)`` per leg; gross is exactly 1.0 and
    ``max |weight| = 1/(2k) <= 1/8 = 0.125 <= 0.30`` at every admissible
    stamp (the 12-name floor gives k = 4), asserted here by construction.
    """
    n = int(n_eligible)
    if n < MIN_ELIGIBLE:
        raise EligibilityShortfall(
            f"only {n} eligible names; the frozen book requires >= {MIN_ELIGIBLE}"
        )
    k = n // SIDE_DIVISOR
    if k < 1:
        raise EligibilityShortfall(f"n_eligible {n} yields an empty side (k=0)")
    per_leg = (GROSS_TARGET / 2.0) / float(k)
    if per_leg > CAP_MAX + WEIGHT_TOL:
        raise ContractViolation(
            f"designed per-leg weight {per_leg} exceeds the frozen cap {CAP_MAX}"
        )
    return k, per_leg


# --------------------------------------------------------------------------- #
# Per-stamp target book (frozen tercile geometry, varying side size)
# --------------------------------------------------------------------------- #
def build_premfade_book(
    scores: Mapping[str, Any],
    *,
    invert: bool = False,
    min_eligible: int = MIN_ELIGIBLE,
    gross: float = GROSS_TARGET,
    cap_max: float = CAP_MAX,
) -> dict[str, Any]:
    """The deterministic PREMFADE tercile book for one decision stamp.

    ``scores`` maps PIT-eligible symbols to their premium level ``b_i``
    (higher = richer premium / more crowded long).  Ranks ascend by
    ``(b_i, symbol id)``; long the ``k = floor(n/3)`` lowest (low/discount
    tier), short the ``k`` highest (high/premium tier), equal weight
    ``(gross/2)/k`` per held symbol, middle flat; exact score ties break by
    symbol id ascending (declared a priori -- mechanically, a tie straddling
    the short boundary sends the lexicographically larger symbol short and a
    tie at the long boundary keeps the lexicographically smaller symbol
    long).  ``invert=True`` returns the EXACT sign-inverted book (the causal
    negative control): the base book is built unchanged and every weight is
    element-wise negated, so ``weights_INV == -weights_BASE`` always.  Below
    ``min_eligible`` raises :class:`EligibilityShortfall`.  The cap holds by
    construction and is asserted.  No PnL.
    """
    cap = float(cap_max)
    if cap <= 0.0:
        raise ContractViolation("cap_max must be positive")
    if not math.isfinite(float(gross)) or float(gross) <= 0.0:
        raise ContractViolation("gross must be finite positive")

    cleaned: dict[str, float] = {}
    ineligible: dict[str, str] = {}
    for raw_sym, raw_value in dict(scores).items():
        sym = str(raw_sym)
        if sym == BENCHMARK_SYMBOL:
            raise ContractViolation(
                "the pinned benchmark leg can never enter the tradeable book"
            )
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            ineligible[sym] = "NON_NUMERIC_SCORE"
            continue
        if not math.isfinite(value):
            ineligible[sym] = "NON_FINITE_SCORE"
            continue
        cleaned[sym] = value

    eligible = sorted(cleaned)
    n = len(eligible)
    if n < int(min_eligible):
        raise EligibilityShortfall(
            f"only {n} eligible names at this stamp; the PREMFADE tercile "
            f"book requires >= {int(min_eligible)} (fail-closed)"
        )
    k, per_leg = side_geometry(n)
    if per_leg > cap + WEIGHT_TOL:
        raise ContractViolation(
            f"PREMFADE book violates the frozen cap by construction: "
            f"per-leg {per_leg} > {cap}"
        )

    ordered = sorted((cleaned[sym], sym) for sym in eligible)
    longs = [sym for _value, sym in ordered[:k]]
    shorts = [sym for _value, sym in ordered[n - k :]]
    overlap = sorted(set(longs) & set(shorts))
    if overlap:
        raise ContractViolation(f"long/short legs overlap: {overlap}")

    weights: dict[str, float] = {sym: per_leg for sym in longs}
    for sym in shorts:
        weights[sym] = weights.get(sym, 0.0) - per_leg
    if invert:
        weights = {sym: -w for sym, w in weights.items()}
        longs, shorts = list(shorts), list(longs)

    rounded = {sym: round(w, 12) for sym, w in sorted(weights.items())}
    max_abs = max(abs(w) for w in rounded.values())
    assert max_abs <= cap + WEIGHT_TOL, (
        f"cap must hold by construction: max|w|={max_abs} > {cap}"
    )
    gross_realised = math.fsum(abs(w) for w in rounded.values())
    assert abs(gross_realised - float(gross)) <= 1e-9, "gross must be exact"
    return {
        "schema": "v14i.basislv_premfade.book.v1",
        "status": STATUS_OK,
        "weights": [[sym, rounded[sym]] for sym in sorted(rounded)],
        "longs": sorted(longs),
        "shorts": sorted(shorts),
        "middle": [sym for sym in eligible if sym not in set(longs) | set(shorts)],
        "n_eligible": n,
        "side_size": int(k),
        "n_longs": len(longs),
        "n_shorts": len(shorts),
        "per_leg_weight": round(abs(per_leg if not invert else -per_leg), 12),
        "scale_applied": 1.0,
        "max_abs_weight": round(max_abs, 12),
        "cap_max": cap,
        "gross_after_scale": round(gross_realised, 12),
        "diagnostics": {
            "ineligible_scores": ineligible,
            "ranking_rule": (
                f"ranks ascend by (b_i, symbol id); long = {k} lowest premium "
                f"(low/discount tier), short = {k} highest premium (high/premium "
                "tier); exact score ties break by symbol id ascending; middle "
                "tercile flat"
            ),
            "invert": bool(invert),
            "signal": SIGNAL_NAME,
        },
    }


def signal_scores_at(
    arm_id: str,
    *,
    basis_by_symbol: Mapping[str, BasisRouteSeries],
    stamp_ns: int,
    universe: Sequence[str],
) -> tuple[dict[str, float], dict[str, str]]:
    """PIT premium levels of one arm at one Monday 00:00:00Z stamp.

    A symbol whose formation window refuses (missing slot, unavailable row,
    insufficient history) is INELIGIBLE at the stamp (fail closed, never
    guessed).  The pinned benchmark leg is refused outright.  Returns
    ``(scores, refused)``.
    """
    formation_buckets, _invert = arm_spec(arm_id)
    if BENCHMARK_SYMBOL in {str(s) for s in universe}:
        raise ContractViolation(
            "the pinned benchmark leg can never enter the tradeable universe"
        )
    scores: dict[str, float] = {}
    refused: dict[str, str] = {}
    for sym in sorted({str(s) for s in universe}):
        series = basis_by_symbol.get(sym)
        if series is None:
            refused[sym] = "NO_BASIS_SERIES_INJECTED"
            continue
        value, reason = premium_level_at(
            series, int(stamp_ns), formation_buckets=formation_buckets
        )
        if value is None:
            refused[sym] = str(reason)
            continue
        scores[sym] = value
    return scores, refused


def compute_targets_at(
    arm_id: str,
    *,
    basis_by_symbol: Mapping[str, BasisRouteSeries],
    stamp_ns: int,
    universe: Sequence[str],
    gross: float = GROSS_TARGET,
) -> dict[str, Any]:
    """Frozen target book of one arm at one Monday 00:00:00Z stamp.

    Ranks the eligible universe by the frozen premium-level signal and
    delegates to :func:`build_premfade_book`.  Fewer than ``MIN_ELIGIBLE``
    eligible names raises :class:`EligibilityShortfall` (the stamp refuses;
    fail closed).  Schedule-only: no PnL is computed.
    """
    formation_buckets, invert = arm_spec(arm_id)
    stamp = int(stamp_ns)
    scores, refused = signal_scores_at(
        arm_id,
        basis_by_symbol=basis_by_symbol,
        stamp_ns=stamp,
        universe=universe,
    )
    book = build_premfade_book(scores, invert=invert, gross=float(gross))
    final_weights = {str(sym): float(w) for sym, w in book["weights"]}
    weights = {sym: final_weights[sym] for sym in sorted(final_weights)}
    formation_days = (
        FORMATION_DAYS_ANCHOR
        if formation_buckets == FORMATION_BUCKETS_ANCHOR
        else FORMATION_DAYS_NEIGHBOUR
    )
    return {
        "schema": "v14i.basislv_premfade.targets.v1",
        "family_id": FAMILY_ID,
        "arm_id": str(arm_id),
        "status": STATUS_OK,
        "weights": [[sym, weights[sym]] for sym in sorted(weights)],
        "longs": [[sym, round(final_weights[sym], 12)] for sym in book["longs"]],
        "shorts": [[sym, round(final_weights[sym], 12)] for sym in book["shorts"]],
        "middle": list(book["middle"]),
        "carried_forward": False,
        "decision_ns": stamp,
        "diagnostics": {
            "stamp_ns": stamp,
            "stamp_iso": iso_utc(stamp),
            "n_eligible": int(book["n_eligible"]),
            "side_size": int(book["side_size"]),
            "n_longs": int(book["n_longs"]),
            "n_shorts": int(book["n_shorts"]),
            "per_leg_weight": book["per_leg_weight"],
            "n_refused": len(refused),
            "refused": {sym: str(reason) for sym, reason in sorted(refused.items())},
            "signal": SIGNAL_NAME,
            "signal_evaluation": SIGNAL_EVALUATION,
            "signal_route": SIGNAL_ROUTE,
            "lag_convention": LAG_CONVENTION,
            "formation_buckets": int(formation_buckets),
            "formation_days": int(formation_days),
            "invert": bool(invert),
            "max_abs_weight": book["max_abs_weight"],
            "gross_after_scale": book["gross_after_scale"],
            "price_only_split_note": PRICE_ONLY_CLAUSE_TEXT,
            "reason_code": None,
        },
    }


# --------------------------------------------------------------------------- #
# Schedule / folds / force-flat (frozen clocks)
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

    A fold covers ``[start 00:00Z, end 00:00Z)``; the 1-day purge zone is
    the TRAILING calendar zone ``[end - PURGE_DAYS days, end)`` (the frozen
    V11-lineage ``purge_fold_members`` convention -- the reading measured at
    51 effective Mondays 17/17/17 by the V13 implementation and A9-F;
    A9F-OBS-4 recorded).  Returns ``(index, label, effective_members,
    purged_members)`` with the purged stamps listed per fold (force-flat gap
    stamps: no decision, no book, flat positions).
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


def force_flat_span_end(start_ns: int, *, holding_days: int = HOLDING_DAYS) -> int:
    """Clamped holding-span end: ``min(T + holding_days, fold end)``.

    The explicit force-flat-at-fold-boundaries enforcement: a span opened
    inside a fold can never extend past that fold's end boundary.
    """
    intended = int(start_ns) + int(holding_days) * DAY_NS
    return min(intended, fold_end_ns(int(start_ns)))


# --------------------------------------------------------------------------- #
# Execution: next-allowed-fill (close of the first completed 15m bar
# strictly after the decision stamp)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class CloseFillEvent:
    """The close-fill event for one symbol at one decision instant."""

    symbol: str
    decision_ns: int
    fill_ns: int  # the fill bar's close boundary (the fill instant)
    price: float  # the fill bar's CLOSE
    event_offset: int  # 0 = the first allowed bar (00:15Z); stress = 1 (00:30Z)


def next_allowed_close_fill(
    series: BarSeries,
    symbol: str,
    *,
    decision_ns: int,
    event_delay_events: int = 0,
) -> Optional[CloseFillEvent]:
    """Fill at the close of the first completed 15m bar STRICTLY after ``T``.

    Only genuinely COMPLETED bars count: the first allowed event is the
    first bar with a finite close whose boundary is > T; a genuinely
    missing slot therefore advances to the next completed bar (a real
    execution event, never an invented substitute at the empty slot).
    ``event_delay_events`` walks strictly later completed bars (the frozen
    +1-delay stress fills at the Monday 00:30:00Z close when the 00:15Z bar
    completed).  No completed bar at all yields ``None`` (fail closed).  A
    fill bar whose availability exceeds its own close refuses (``None``):
    you cannot transact on a row you cannot yet read -- a decision at T can
    never read data available after T (crypto_compat pin style).
    """
    delay = int(event_delay_events)
    if delay < 0:
        raise ContractViolation("event_delay_events must be >= 0")
    decision = int(decision_ns)
    if decision % BUCKET_NS != 0:
        raise ContractViolation("decision stamps must sit on the 15m grid")
    start = series.slot_index(decision) + 1  # first boundary strictly after T
    if start >= series.close.shape[0]:
        return None
    completed = np.nonzero(np.isfinite(series.close[start:]))[0]
    if completed.shape[0] == 0 or delay >= int(completed.shape[0]):
        return None
    idx = start + int(completed[delay])
    boundary = int(series.origin_ns) + idx * BUCKET_NS
    close = float(series.close[idx])
    if not math.isfinite(close) or close <= 0.0:
        return None
    if int(series.available_ns[idx]) > boundary:
        return None  # the fill bar is not yet readable at its own close
    return CloseFillEvent(
        symbol=str(symbol),
        decision_ns=decision,
        fill_ns=boundary,
        price=close,
        event_offset=delay,
    )


# --------------------------------------------------------------------------- #
# Drop-one (pinned wording; see DROP_ONE_PIN)
# --------------------------------------------------------------------------- #
def select_drop_one_symbol_at(
    weights: Mapping[str, float],
    scores: Mapping[str, float],
) -> str:
    """The held max-|weight| leg with the largest |b_i| at one stamp.

    Held means ``|w| > HELD_WEIGHT_TOL``; an unheld symbol can never be
    selected.  Under the equal-weight book every held leg ties on |weight|,
    so the pre-declared outcome-free tie-break applies: drop the held leg
    with the LARGEST ``|b_i|`` (the most extreme premium expression);
    exact |b_i| ties break by lexicographically smallest symbol id.  A book
    with no held symbol, or a held symbol without a score, fails closed.
    """
    held = {
        str(sym): abs(float(w))
        for sym, w in dict(weights).items()
        if abs(float(w)) > HELD_WEIGHT_TOL
    }
    if not held:
        raise ContractViolation(
            "drop-one found no held symbol at this stamp; refusing to select "
            "an unheld symbol (non-vacuousness pin)"
        )
    ranked: list[tuple[float, str]] = []
    for sym in sorted(held):
        if sym not in {str(s) for s in dict(scores)}:
            raise ContractViolation(
                f"drop-one held symbol {sym!r} carries no premium score at "
                "this stamp (fail closed)"
            )
        value = abs(float(scores[sym]))
        if not math.isfinite(value):
            raise ContractViolation(f"non-finite premium score for {sym!r}")
        ranked.append((-value, sym))  # largest |b_i| first, then smallest id
    ranked.sort()
    return ranked[0][1]


def schedule_drop_one(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Pin-exact schedule-level drop-one selection (see :data:`DROP_ONE_PIN`).

    Scans the arm's effective target records chronologically; the selected
    stamp is the EARLIEST stamp attaining the largest held |weight| across
    the whole schedule.  Each record must carry a ``scores`` diagnostics
    mapping (symbol -> b_i) for the stamp-level tie-break.
    """
    best: Optional[tuple[float, int]] = None
    for record in records:
        stamp = int(record.get("decision_ns", record.get("stamp_ns", 0)))
        body = record.get("weights")
        weights: dict[str, float] = {}
        if isinstance(body, Mapping):
            weights = {str(s): float(w) for s, w in body.items()}
        elif isinstance(body, Sequence) and not isinstance(body, (str, bytes)):
            weights = {str(e[0]): float(e[1]) for e in body}
        held = {
            sym: abs(w) for sym, w in weights.items() if abs(w) > HELD_WEIGHT_TOL
        }
        if not held:
            continue
        largest = max(held.values())
        key = (-largest, stamp)
        if best is None or key < best:  # largest |w|, then EARLIEST stamp
            best = key
    if best is None:
        raise ContractViolation(
            "schedule_drop_one found no held position in the whole schedule"
        )
    neg_weight, stamp = best
    return {
        "stamp_ns": stamp,
        "held_abs_weight": round(-neg_weight, 12),
        "proven_held": True,
        "pin": DROP_ONE_PIN,
    }


def build_drop_one_book(
    weights: Mapping[str, float],
    *,
    dropped_symbol: str,
) -> dict[str, Any]:
    """Renormalize one book after dropping one held symbol (per the pin).

    The remaining ``2k-1`` held legs KEEP their sides and are renormalized
    to gross 1.0 as equal legs at ``1/(2k-1)`` each (proposal section 8,
    literal text); the middle tercile stays flat; the dropped symbol must
    be HELD at this stamp (fail closed otherwise).
    """
    dropped = str(dropped_symbol)
    weights_map = {str(sym): float(w) for sym, w in dict(weights).items()}
    if dropped not in weights_map:
        raise ContractViolation(
            f"drop-one target {dropped!r} is not held at this stamp "
            "(non-vacuousness pin)"
        )
    if abs(weights_map[dropped]) <= HELD_WEIGHT_TOL:
        raise ContractViolation(
            f"drop-one target {dropped!r} carries no held weight at this "
            "stamp (non-vacuousness pin)"
        )
    survivors = {
        sym: w for sym, w in weights_map.items()
        if sym != dropped and abs(w) > HELD_WEIGHT_TOL
    }
    n_longs = sum(1 for w in survivors.values() if w > 0.0)
    n_shorts = sum(1 for w in survivors.values() if w < 0.0)
    n_survivors = n_longs + n_shorts
    if n_longs < 1 or n_shorts < 1:
        raise ContractViolation(
            "drop-one renormalization must keep both sides populated; got "
            f"{n_longs}L/{n_shorts}S"
        )
    per_leg = round(GROSS_TARGET / float(n_survivors), 12)
    renormalized = {
        sym: (per_leg if w > 0.0 else -per_leg) for sym, w in sorted(survivors.items())
    }
    gross = math.fsum(abs(w) for w in renormalized.values())
    assert abs(gross - GROSS_TARGET) <= 1e-9, "drop-one gross must be 1.0"
    return {
        "schema": "v14i.basislv_premfade.drop_one_book.v1",
        "dropped_symbol": dropped,
        "dropped_side": "long" if weights_map[dropped] > 0.0 else "short",
        "weights": [[sym, renormalized[sym]] for sym in sorted(renormalized)],
        "longs": sorted(s for s, w in renormalized.items() if w > 0.0),
        "shorts": sorted(s for s, w in renormalized.items() if w < 0.0),
        "n_surviving_legs": int(n_survivors),
        "per_leg_weight": per_leg,
        "gross": round(gross, 12),
        "pin": DROP_ONE_PIN,
    }


# --------------------------------------------------------------------------- #
# Book/cash reconciliation (V12-inherited convention: cash is NOT a tradable
# symbol and never appears in weights or concentration/turnover)
# --------------------------------------------------------------------------- #
def cash_reconciliation(weights: Mapping[str, float]) -> dict[str, Any]:
    """The per-stamp capital identity of one book.

    With capital normalised to 1.0: ``net + cash_line == 1`` where
    ``net = sum(weights)`` and ``cash_line = 1 - net``.  Cash is never a
    position, and the pinned benchmark leg can never appear in the book.
    """
    items = {str(sym): float(w) for sym, w in dict(weights).items()}
    if BENCHMARK_SYMBOL in items:
        raise ContractViolation("the benchmark leg can never appear in a book")
    net = math.fsum(items.values())
    gross = math.fsum(abs(w) for w in items.values())
    cash_line = 1.0 - net
    return {
        "cash_is_tradable_symbol": False,
        "n_positions": sum(1 for w in items.values() if abs(w) > HELD_WEIGHT_TOL),
        "net_exposure": round(net, 12),
        "gross": round(gross, 12),
        "cash_line": round(cash_line, 12),
        "net_plus_cash_is_one": bool(abs(net + cash_line - 1.0) <= WEIGHT_TOL),
        "reconciles": bool(abs(net) <= WEIGHT_TOL and gross <= GROSS_TARGET + WEIGHT_TOL),
    }


# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #
def window_start_ns() -> int:
    return parse_iso_utc(WINDOW_START_ISO)


def window_end_ns() -> int:
    return parse_iso_utc(WINDOW_END_ISO)


__all__ = [
    "ANCHOR_ARM",
    "ANCHOR_ARM_CONFIG_ID",
    "ARM_CONFIG_IDS",
    "ARM_IDS",
    "ARM_ROLES",
    "ARM_SPECS",
    "BASIS_IDENTITY_TOL_ABS",
    "BarSeries",
    "BasisRouteSeries",
    "BUCKET_NS",
    "BENCHMARK_SYMBOL",
    "CAP_MAX",
    "CloseFillEvent",
    "CONTROL_ARM",
    "CONTROL_ARM_CONFIG_ID",
    "DAY_NS",
    "DECISION_CLOCK",
    "DIRECTION",
    "DROP_ONE_PIN",
    "EligibilityShortfall",
    "F0_FOLD_TERMINAL_STAMP_ISO",
    "F1_PURGED_STAMP_ISO",
    "FAMILY_ID",
    "FIRST_STAMP_ISO",
    "FIRST_STAMP_WARMUP_FROM_ISO",
    "FOLD_WINDOWS",
    "FOLDS_CONTRACT",
    "FILL_RULE",
    "FORMATION_BUCKETS_ANCHOR",
    "FORMATION_BUCKETS_NEIGHBOUR",
    "FORMATION_DAYS_ANCHOR",
    "FORMATION_DAYS_NEIGHBOUR",
    "GROSS_TARGET",
    "HOLDING_DAYS",
    "LAG_CONVENTION",
    "MATRIX_COHORT_HINT",
    "MIN_DECISIONS_PER_FOLD",
    "MIN_ELIGIBLE",
    "MIN_FOLDS",
    "NEIGHBOUR_ARM",
    "NEIGHBOUR_ARM_CONFIG_ID",
    "PRICE_ONLY_CLAUSE_TEXT",
    "PURGE_DAYS",
    "REASON_INSUFFICIENT_HISTORY",
    "REASON_MISSING_OR_NON_FINITE_SLOT",
    "REASON_UNAVAILABLE_ROW",
    "SIDE_DIVISOR",
    "SIGNAL_EVALUATION",
    "SIGNAL_NAME",
    "SIGNAL_ROUTE",
    "STATUS_OK",
    "STRATEGY_ID",
    "WINDOW_END_ISO",
    "WINDOW_START_ISO",
    "bars_from_rows",
    "basis_series_from_rows",
    "build_drop_one_book",
    "build_premfade_book",
    "cash_reconciliation",
    "compute_targets_at",
    "effective_schedule",
    "fold_assignments",
    "fold_end_ns",
    "force_flat_span_end",
    "iso_utc",
    "next_allowed_close_fill",
    "parse_iso_utc",
    "premium_level_at",
    "schedule_drop_one",
    "select_drop_one_symbol_at",
    "side_geometry",
    "signal_scores_at",
    "stamp_calendar",
    "window_end_ns",
    "window_start_ns",
]
