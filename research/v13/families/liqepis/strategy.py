"""Frozen strategy primitives for the A13-V13-A5-LIQEPIS family (V13 I lane).

This module implements the FROZEN contract pinned by
``research/control/v13_run/selection_freeze_v13.json`` +
``research/proposals/v13/a5/LIQEPIS.{md,json}`` (selection-freeze SHA
``834f71d``) verbatim -- no tuning, no grids, no parameter changes.  It is a
pure, data-injected library: every observable (completed 15m fusion bars,
funding settlements, tick sizes) is supplied by the caller as
:class:`FusionBarSeries` / settlement mappings, so the same primitives run
on synthetic fixtures and on the read-only workspace snapshot.  Nothing
here reads the catalog, computes a scored outcome, or persists anything.

SIGNAL (bars-only, fusion availability semantics): at a decision instant
``T`` (Monday 00:00:00Z, on the 15m grid) a symbol's episodicity is the
normalized Herfindahl of dollar-volume shares over the trailing
``FORMATION_BARS_ANCHOR`` (2688 = 28d) / ``FORMATION_BARS_NEIGHBOUR``
(5376 = 56d) completed 15m slots whose close boundaries lie in
``(T - N*15m, T]``::

    q_b = close_b x volume_b ;  Q = sum_b q_b ;  H = (sum_b q_b^2) / Q^2
    (uniform baseline 1/2688)

A decision at T never reads a row whose availability stamp is > T
(``research/data_fusion/crypto_compat.py`` semantics: a completed bar is
available at its close boundary).  EVERY slot of the formation window must
carry exactly one present-and-available row; one missing/unavailable slot
REFUSES the symbol at that stamp (fail-closed, no back-fill) -- gaps can
never masquerade as thinness.

BOOK: long the ``LEGS_PER_SIDE`` (6) lowest-H names, short the 6 highest-H
names, equal weight ``1/12`` per held symbol, gross 1.0, middle tercile
flat; exact score ties break by symbol id ascending (declared a priori);
``max |weight| = 1/12 <= 0.30`` by construction and asserted.  Fewer than
``MIN_ELIGIBLE`` (13 = 6 + 6 + a non-empty middle tercile) eligible names
raises :class:`EligibilityShortfall` (fail closed).  The benchmark leg
(BTCUSDT) is benchmark-only and can never enter the book.

ARMS: anchor ``LIQEPIS-28D`` (2688 bars), neighbour ``LIQEPIS-56D``
(5376 bars, same mechanism/book), causal negative control
``LIQEPIS-SIGN-INV`` (identical 28d construction and book with the sign
inverted end-to-end; its falsification rule is encoded in
:mod:`research.v13.families.liqepis.gate_runner`).

SCHEDULE / FOLDS: weekly Monday 00:00:00Z stamps over the frozen window
2025-08-22T00:00:00Z..2026-08-21T00:00:00Z (52 stamps; first 2025-08-25).
Chronological F0/F1/F2 with the 1-day purge realised as a calendar zone
(the last day before each fold's end boundary): exactly one stamp
(2026-04-20) is purged, leaving 51 effective Mondays at 17/17/17 per fold
(measured A9-F convention; selection_freeze_v13 correction note).  Holding
spans are force-flat-clamped at their fold's end boundary.

EXECUTION (ONE declared lag): fills at the close of the first completed
15m bar STRICTLY after ``T`` (Monday 00:15:00Z close); the +1-delay stress
walks to the next completed bar (Monday 00:30:00Z close).  A genuinely
missing slot advances to the next completed bar (a real execution event --
never a shifted substitute); a fill bar whose availability exceeds its own
close refuses (you cannot transact on a row you cannot yet read).

DROP-ONE (wording pinned exactly -- A9-F spec-gap closure): see
:data:`DROP_ONE_PIN`.

No PnL, no returns, no scored metric is computed anywhere in this module.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Sequence

import numpy as np

from research.adapter_v10.protocol import (
    ContractViolation,
    DEFAULT_WEIGHT_CAP_MAX,
    WEIGHT_TOL,
)
from research.adapter_v10.stress import HELD_WEIGHT_TOL
from research.v11.publication_identity import arm_config_digest  # noqa: F401  (re-exported identity plumbing)
from research.v11.families.oilever_delev.strategy import (
    iso_utc,
    parse_iso_utc,
    weekly_mondays,
)

# --------------------------------------------------------------------------- #
# Frozen constants (selection_freeze_v13.json + LIQEPIS proposal, verbatim)
# --------------------------------------------------------------------------- #
FAMILY_ID = "A13-V13-A5-LIQEPIS"
STRATEGY_ID = "hyp_a13_v13_liqepis"
#: dollar-neutral 6v6 tercile book; BTC beta is a CONTEXT adjustment at the
#: gate only and never alters leg weights (proposal item 07).
DIRECTION = "long_short_dollar_neutral"
BENCHMARK_SYMBOL = "BTCUSDT"
MATRIX_COHORT_HINT = "v13"

WINDOW_START_ISO = "2025-08-22T00:00:00Z"
WINDOW_END_ISO = "2026-08-21T00:00:00Z"

FUNDING_SIGN_CONVENTION = "LONG_PAYS_POSITIVE_RATE"

ANCHOR_ARM = "LIQEPIS-28D"
NEIGHBOUR_ARM = "LIQEPIS-56D"
CONTROL_ARM = "LIQEPIS-SIGN-INV"
ARM_ROLES: dict[str, str] = {
    ANCHOR_ARM: "anchor",
    NEIGHBOUR_ARM: "neighbour",
    CONTROL_ARM: "causal_negative_control",
}
ARM_IDS: tuple[str, ...] = tuple(sorted(ARM_ROLES))
ANCHOR_ARM_CONFIG_ID = "28D-HHI"
NEIGHBOUR_ARM_CONFIG_ID = "56D-HHI"
CONTROL_ARM_CONFIG_ID = "28D-HHI-INVERTED"
ARM_CONFIG_IDS: dict[str, str] = {
    ANCHOR_ARM: ANCHOR_ARM_CONFIG_ID,
    NEIGHBOUR_ARM: NEIGHBOUR_ARM_CONFIG_ID,
    CONTROL_ARM: CONTROL_ARM_CONFIG_ID,
}

DAY_NS = 86_400_000_000_000
BAR_INTERVAL_NS = 900_000_000_000  # 15m completed bars
FORMATION_BARS_ANCHOR = 2688  # 28d x 96 slots/day
FORMATION_BARS_NEIGHBOUR = 5376  # 56d x 96
FORMATION_DAYS_ANCHOR = 28
FORMATION_DAYS_NEIGHBOUR = 56
HOLDING_DAYS = 7
LEGS_PER_SIDE = 6
#: 6 + 6 held names plus at least one middle-tercile name; below this the
#: tercile construction has no middle bucket and the stamp fails closed.
MIN_ELIGIBLE = 2 * LEGS_PER_SIDE + 1
GROSS_TARGET = 1.0
CAP_MAX = float(DEFAULT_WEIGHT_CAP_MAX)
#: Designed per-name weight: gross/2 split evenly inside each 6-name leg.
PER_NAME_WEIGHT = (GROSS_TARGET / 2.0) / float(LEGS_PER_SIDE)
DROP_ONE_LEG_NAMES = LEGS_PER_SIDE - 1
DROP_ONE_PER_NAME_WEIGHT = (GROSS_TARGET / 2.0) / float(DROP_ONE_LEG_NAMES)

#: Frozen per-arm ``(formation_bars, invert)`` mapping.
ARM_SPECS: dict[str, tuple[int, bool]] = {
    ANCHOR_ARM: (FORMATION_BARS_ANCHOR, False),
    NEIGHBOUR_ARM: (FORMATION_BARS_NEIGHBOUR, False),
    CONTROL_ARM: (FORMATION_BARS_ANCHOR, True),
}

#: Frozen schedule / folds strings (proposal item 05 / A9-F measurement).
DECISION_CLOCK = (
    "weekly, every Monday 00:00:00Z; 52 scheduled Mondays in the blind-S0 "
    "window, 51 effective after the 1-day purge (2026-04-20 in the F1 purge "
    "zone); one declared execution lag"
)
FILL_RULE = (
    "fills at the close of the first completed 15m bar strictly after the "
    "decision stamp (Monday 00:15:00Z close); stress +1 event delay fills "
    "at the Monday 00:30:00Z close"
)
FOLDS_CONTRACT = (
    "chronological F0/F1/F2 force-flat per the frozen V12 fold calendar "
    "(F0 2025-08-22..2025-12-21, F1 2025-12-22..2026-04-21, "
    "F2 2026-04-22..2026-08-21) with the 1-day purge as a calendar zone "
    "(the last day before each fold end boundary); measured A9-F outcome: "
    "51 effective Mondays at 17/17/17 per fold (L-V11-1 per-family fold "
    "contract)"
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

#: The first decision stamp of the frozen window (2025-08-25 is a Monday);
#: the first-stamp warmup must be satisfiable from PRE-WINDOW bars.
FIRST_STAMP_ISO = "2025-08-25T00:00:00Z"

#: The single stamp measured inside the F1 1-day purge zone (A9-F;
#: selection_freeze_v13 records the corrected 51-effective-Monday floor).
F1_PURGED_STAMP_ISO = "2026-04-20T00:00:00Z"

STATUS_OK = "OK"

#: Signal identity string (digest payload / diagnostics).
SIGNAL_NAME = "hhi_15m_dollar_volume_shares"

#: The exact evaluation order of the frozen Herfindahl (deterministic):
#: ``H = (sum q_b^2) / (sum q_b)^2`` with float64 vectorized sums.
H_EVALUATION = "H = (sum_b q_b**2) / (sum_b q_b)**2 ; q_b = close x volume"

#: Refusal reason codes (fail-closed; never guessed around).
REASON_MISSING_OR_NON_FINITE_SLOT = "MISSING_OR_NON_FINITE_SLOT"
REASON_UNAVAILABLE_ROW = "UNAVAILABLE_ROW"
REASON_DEGENERATE_ZERO_Q = "DEGENERATE_ZERO_Q"
REASON_INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"


class EligibilityShortfall(ContractViolation):
    """A stamp has fewer than ``MIN_ELIGIBLE`` eligible names -- no book."""


# --------------------------------------------------------------------------- #
# Drop-one wording pin (A9-F a5 requirement: pin the tie-break and the
# renormalization wording EXACTLY; recorded spec gap closed here).
# --------------------------------------------------------------------------- #
DROP_ONE_PIN = (
    "drop-one identifies the EARLIEST fold-stamp carrying the largest held "
    "|weight| across the whole arm schedule (chronological tie-break across "
    "stamps), then drops the single HELD symbol attaining that maximum at "
    "that stamp among held positions only (|w| > 1e-9; exact |weight| ties "
    "break by lexicographically smallest symbol id ascending; an unheld "
    "symbol can never be selected). Renormalization (A9-F spec-gap closure, "
    "pinned exactly): the eleven surviving held names KEEP their sides and "
    "are renormalized WITHIN each side at constant per-side gross 0.5 -- the "
    "dropped side renormalizes its 5 survivors to 1/10 each (the frozen "
    "'renormalize to 5 symbols per side at 1/10' realized on the affected "
    "side, because dropping exactly one symbol from the 6v6 book leaves 11 "
    "names and the frozen 'drop the single symbol' requirement forbids a "
    "second drop) while the untouched side keeps its 6 names at 1/12 each; "
    "gross 1.0 and dollar neutrality are preserved, the middle tercile stays "
    "flat and the benchmark is never held."
)


# --------------------------------------------------------------------------- #
# Fusion bars (availability-carrying completed 15m bars)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class FusionBarSeries:
    """Boundary-indexed completed 15m bars with fusion availability stamps.

    ``close`` / ``volume`` are float64 arrays over the 15m slot grid
    ``origin_ns + k * BAR_INTERVAL_NS``; a slot with NO row carries NaN in
    both arrays (a gap -- never back-filled).  ``available_ns`` carries each
    row's fusion availability stamp (honest bars: exactly their close
    boundary); a late/corrected row may carry a later stamp, in which case
    decisions at or before that stamp refuse the row (fail closed).
    """

    origin_ns: int
    close: np.ndarray
    volume: np.ndarray
    available_ns: np.ndarray
    _q_cache: np.ndarray = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        n = self.close.shape[0]
        if not (self.volume.shape[0] == self.available_ns.shape[0] == n):
            raise ContractViolation("fusion arrays must share one length")
        if int(self.origin_ns) % BAR_INTERVAL_NS != 0:
            raise ContractViolation("series origin must sit on the 15m grid")
        if int(self.origin_ns) < 0 or n == 0:
            raise ContractViolation("series origin must be positive and non-empty")

    @property
    def end_ns(self) -> int:
        """Exclusive end of the covered grid (one past the last boundary)."""
        return int(self.origin_ns) + self.close.shape[0] * BAR_INTERVAL_NS

    @property
    def q(self) -> np.ndarray:
        """``q_b = close x volume`` per slot (NaN where either is missing)."""
        return self._q_cache

    def slot_index(self, boundary_ns: int) -> int:
        """Grid index of one 15m boundary (refuses off-grid stamps)."""
        offset = int(boundary_ns) - int(self.origin_ns)
        if offset < 0 or offset % BAR_INTERVAL_NS != 0:
            raise ContractViolation(
                f"boundary {boundary_ns} is not on this series' 15m grid"
            )
        return offset // BAR_INTERVAL_NS


def series_from_rows(
    rows: Sequence[tuple[int, int, float, float]],
) -> FusionBarSeries:
    """Build one :class:`FusionBarSeries` from ``(boundary_ns, available_ns,
    close, volume)`` rows.

    Fail-closed: duplicate boundaries, off-grid boundaries, availability
    earlier than the bar's own close (a bar cannot be readable before it
    closed) and non-finite prices are refused; missing slots stay NaN.
    """
    if not rows:
        raise ContractViolation("series_from_rows needs at least one row")
    boundaries = [int(r[0]) for r in rows]
    for b in boundaries:
        if b <= 0 or b % BAR_INTERVAL_NS != 0:
            raise ContractViolation(f"bar boundary off the 15m grid: {b}")
    origin = min(boundaries)
    last = max(boundaries)
    n = (last - origin) // BAR_INTERVAL_NS + 1
    close = np.full(n, np.nan, dtype=np.float64)
    volume = np.full(n, np.nan, dtype=np.float64)
    available = (origin + np.arange(n, dtype=np.int64) * BAR_INTERVAL_NS)
    seen: set[int] = set()
    for boundary, avail, c, v in rows:
        idx = (int(boundary) - origin) // BAR_INTERVAL_NS
        if int(boundary) in seen:
            raise ContractViolation(f"duplicate bar boundary {boundary}")
        seen.add(int(boundary))
        close_v = float(c)
        vol_v = float(v)
        if not math.isfinite(close_v) or close_v <= 0.0:
            raise ContractViolation(f"non-positive close at boundary {boundary}")
        if not math.isfinite(vol_v) or vol_v < 0.0:
            raise ContractViolation(f"non-finite/negative volume at boundary {boundary}")
        if int(avail) < int(boundary):
            raise ContractViolation(
                f"availability {avail} precedes the bar's own close {boundary}"
            )
        close[idx] = close_v
        volume[idx] = vol_v
        available[idx] = int(avail)
    q = close * volume
    return FusionBarSeries(
        origin_ns=int(origin),
        close=close,
        volume=volume,
        available_ns=available,
        _q_cache=q,
    )


# --------------------------------------------------------------------------- #
# The frozen episodicity signal (HHI of 15m dollar-volume shares)
# --------------------------------------------------------------------------- #
def episodicity_at(
    series: FusionBarSeries,
    stamp_ns: int,
    *,
    formation_bars: int,
) -> tuple[Optional[float], Optional[str]]:
    """``(H, None)`` when computable, else ``(None, refusal_reason)``.

    The formation window at ``stamp_ns`` is the trailing ``formation_bars``
    completed slots with close boundaries in ``(T - N*15m, T]``.  Fail-closed
    refusal reasons: :data:`REASON_INSUFFICIENT_HISTORY`,
    :data:`REASON_MISSING_OR_NON_FINITE_SLOT` (every slot must be present),
    :data:`REASON_UNAVAILABLE_ROW` (a row available after T is unreadable at
    T), :data:`REASON_DEGENERATE_ZERO_Q`.
    """
    stamp = int(stamp_ns)
    if stamp % BAR_INTERVAL_NS != 0:
        raise ContractViolation("decision stamps must sit on the 15m grid")
    n = int(formation_bars)
    if n <= 1:
        raise ContractViolation("formation_bars must exceed 1")
    last_idx = stamp - int(series.origin_ns)
    if last_idx < 0 or last_idx % BAR_INTERVAL_NS != 0:
        return None, REASON_INSUFFICIENT_HISTORY
    last_slot = last_idx // BAR_INTERVAL_NS
    if last_slot >= series.close.shape[0] or last_slot + 1 < n:
        return None, REASON_INSUFFICIENT_HISTORY
    lo = last_slot + 1 - n
    q = series.q[lo : last_slot + 1]
    assert q.shape[0] == n, "formation window slice must be exactly n slots"
    if not bool(np.isfinite(q).all()):
        return None, REASON_MISSING_OR_NON_FINITE_SLOT
    avail = series.available_ns[lo : last_slot + 1]
    if bool((avail > stamp).any()):
        return None, REASON_UNAVAILABLE_ROW
    total_q = float(q.sum())
    if not math.isfinite(total_q) or total_q <= 0.0:
        return None, REASON_DEGENERATE_ZERO_Q
    value = float(np.dot(q, q)) / (total_q * total_q)
    if not math.isfinite(value) or value <= 0.0:
        return None, REASON_DEGENERATE_ZERO_Q
    return value, None


def arm_spec(arm_id: str) -> tuple[int, bool]:
    """``(formation_bars, invert)`` of one frozen arm."""
    arm_id = str(arm_id)
    if arm_id not in ARM_SPECS:
        raise ContractViolation(f"unknown arm_id {arm_id!r}; expected {ARM_IDS}")
    return ARM_SPECS[arm_id]


def signal_scores_at(
    arm_id: str,
    *,
    bars_by_symbol: Mapping[str, FusionBarSeries],
    stamp_ns: int,
    universe: Sequence[str],
) -> dict[str, float]:
    """PIT episodicity scores of one arm at one Monday 00:00:00Z stamp.

    A symbol whose formation window refuses (missing slot, unavailable row,
    degenerate window) is simply INELIGIBLE at the stamp (fail closed, never
    guessed).  The pinned benchmark leg is refused outright.
    """
    formation_bars, _invert = arm_spec(arm_id)
    if BENCHMARK_SYMBOL in {str(s) for s in universe}:
        raise ContractViolation(
            "the pinned benchmark leg can never enter the tradeable universe"
        )
    scores: dict[str, float] = {}
    for sym in sorted({str(s) for s in universe}):
        series = bars_by_symbol.get(sym)
        if series is None:
            continue
        value, _reason = episodicity_at(
            series, int(stamp_ns), formation_bars=formation_bars
        )
        if value is None:
            continue  # INELIGIBLE at this stamp (fail closed)
        scores[sym] = value
    return scores


# --------------------------------------------------------------------------- #
# Per-stamp target book (frozen 6v6 tercile geometry)
# --------------------------------------------------------------------------- #
def build_liqepis_book(
    scores: Mapping[str, Any],
    *,
    invert: bool = False,
    legs_per_side: int = LEGS_PER_SIDE,
    min_eligible: int = MIN_ELIGIBLE,
    gross: float = GROSS_TARGET,
    cap_max: float = CAP_MAX,
) -> dict[str, Any]:
    """The deterministic LIQEPIS tercile book for one decision stamp.

    ``scores`` maps PIT-eligible symbols to their episodicity ``H`` (higher =
    burstier).  Long the ``legs_per_side`` LOWEST scores (smooth turnover),
    short the ``legs_per_side`` HIGHEST (bursty), equal weight
    ``(gross/2)/legs_per_side`` per held symbol, middle tercile flat; exact
    score ties break by lexicographically smallest symbol id (declared a
    priori).  ``invert=True`` flips the whole book end-to-end (the causal
    negative control arm).  Below ``min_eligible`` raises
    :class:`EligibilityShortfall`.  The cap holds by construction and is
    asserted, not assumed.  No PnL.
    """
    cap = float(cap_max)
    if cap <= 0.0:
        raise ContractViolation("cap_max must be positive")
    if int(legs_per_side) < 1:
        raise ContractViolation("legs_per_side must be >= 1")
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
    if len(eligible) < int(min_eligible):
        raise EligibilityShortfall(
            f"only {len(eligible)} eligible names at this stamp; the LIQEPIS "
            f"tercile book requires >= {int(min_eligible)} (fail-closed)"
        )

    sign = -1.0 if invert else 1.0
    ordered = sorted((sign * cleaned[sym], sym) for sym in eligible)
    k = int(legs_per_side)
    longs = [sym for _value, sym in ordered[:k]]
    shorts = [sym for _value, sym in ordered[len(ordered) - k :]]
    overlap = sorted(set(longs) & set(shorts))
    if overlap:
        raise ContractViolation(f"long/short legs overlap: {overlap}")

    per_name = (float(gross) / 2.0) / float(k)
    weights: dict[str, float] = {sym: per_name for sym in longs}
    for sym in shorts:
        weights[sym] = weights.get(sym, 0.0) - per_name

    max_abs = max(abs(w) for w in weights.values())
    if max_abs > cap:
        raise ContractViolation(
            f"LIQEPIS book violates the frozen cap by construction: "
            f"max|w|={max_abs} > {cap} (the frozen 1/{2 * k} weight must never "
            "require scaling)"
        )
    rounded = {sym: round(w, 12) for sym, w in sorted(weights.items())}
    post_max = max(abs(w) for w in rounded.values())
    assert post_max <= cap + WEIGHT_TOL, (
        f"cap must hold by construction: max|w|={post_max} > {cap}"
    )
    return {
        "schema": "v13i.liqepis.book.v1",
        "status": STATUS_OK,
        "weights": [[sym, rounded[sym]] for sym in sorted(rounded)],
        "longs": sorted(longs),
        "shorts": sorted(shorts),
        "middle": [sym for sym in eligible if sym not in set(longs) | set(shorts)],
        "n_eligible": len(eligible),
        "n_longs": len(longs),
        "n_shorts": len(shorts),
        "per_name_weight_before_scale": round(per_name, 12),
        "scale_applied": 1.0,
        "max_abs_weight": round(post_max, 12),
        "cap_max": cap,
        "gross_after_scale": round(math.fsum(abs(w) for w in rounded.values()), 12),
        "diagnostics": {
            "ineligible_scores": ineligible,
            "ranking_rule": (
                f"long = {k} lowest episodicity H (smooth turnover), short = {k} "
                "highest H (bursty); exact score ties broken by lexicographically "
                "smallest symbol id ascending; middle tercile flat"
            ),
            "invert": bool(invert),
            "signal": SIGNAL_NAME,
        },
    }


def compute_targets_at(
    arm_id: str,
    *,
    bars_by_symbol: Mapping[str, FusionBarSeries],
    stamp_ns: int,
    universe: Sequence[str],
    gross: float = GROSS_TARGET,
) -> dict[str, Any]:
    """Frozen target book of one arm at one Monday 00:00:00Z stamp.

    Ranks the eligible universe by the frozen episodicity signal and
    delegates to :func:`build_liqepis_book`.  Fewer than ``MIN_ELIGIBLE``
    eligible names raises :class:`EligibilityShortfall` (fail closed).
    Schedule-only: no PnL is computed.
    """
    formation_bars, invert = arm_spec(arm_id)
    stamp = int(stamp_ns)
    scores: dict[str, float] = {}
    refused: dict[str, str] = {}
    for sym in sorted({str(s) for s in universe}):
        if sym == BENCHMARK_SYMBOL:
            raise ContractViolation(
                "the pinned benchmark leg can never enter the tradeable universe"
            )
        series = bars_by_symbol.get(sym)
        if series is None:
            refused[sym] = "NO_BARS_INJECTED"
            continue
        value, reason = episodicity_at(series, stamp, formation_bars=formation_bars)
        if value is None:
            refused[sym] = str(reason)
            continue
        scores[sym] = value
    book = build_liqepis_book(scores, invert=invert, gross=float(gross))
    final_weights = {str(sym): float(w) for sym, w in book["weights"]}
    weights = {sym: final_weights[sym] for sym in sorted(final_weights)}
    formation_days = (
        FORMATION_DAYS_ANCHOR
        if formation_bars == FORMATION_BARS_ANCHOR
        else FORMATION_DAYS_NEIGHBOUR
    )
    return {
        "schema": "v13i.liqepis.targets.v1",
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
            "n_longs": int(book["n_longs"]),
            "n_shorts": int(book["n_shorts"]),
            "n_refused": len(refused),
            "refused": {sym: str(reason) for sym, reason in sorted(refused.items())},
            "signal": SIGNAL_NAME,
            "signal_evaluation": H_EVALUATION,
            "formation_bars": int(formation_bars),
            "formation_days": int(formation_days),
            "invert": bool(invert),
            "max_abs_weight": book["max_abs_weight"],
            "gross_after_scale": book["gross_after_scale"],
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
    ``[end - PURGE_DAYS days, end)``.  Returns ``(index, label, effective_
    members, purged_members)`` with the purged stamps listed per fold
    (force-flat gap stamps: no decision, no book, flat positions).
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
    series: FusionBarSeries,
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
    you cannot transact on a row you cannot yet read.
    """
    delay = int(event_delay_events)
    if delay < 0:
        raise ContractViolation("event_delay_events must be >= 0")
    decision = int(decision_ns)
    if decision % BAR_INTERVAL_NS != 0:
        raise ContractViolation("decision stamps must sit on the 15m grid")
    start = series.slot_index(decision) + 1  # first boundary strictly after T
    if start >= series.close.shape[0]:
        return None
    completed = np.nonzero(np.isfinite(series.close[start:]))[0]
    if completed.shape[0] == 0 or delay >= int(completed.shape[0]):
        return None
    idx = start + int(completed[delay])
    boundary = int(series.origin_ns) + idx * BAR_INTERVAL_NS
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
def select_drop_one_symbol_at(weights: Mapping[str, float]) -> str:
    """The HELD max-|weight| symbol at one stamp (ties -> smallest symbol id).

    Held means ``|w| > HELD_WEIGHT_TOL``; an unheld symbol can never be
    selected; a book with no held symbol fails closed.
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
    largest = max(held.values())
    tied = sorted(sym for sym, value in held.items() if value == largest)
    return tied[0]


def schedule_drop_one(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Pin-exact schedule-level drop-one selection (see :data:`DROP_ONE_PIN`).

    Scans the arm's effective target records chronologically; the selected
    stamp is the EARLIEST stamp attaining the largest held |weight| across
    the whole schedule, and the dropped symbol is the held max-|weight|
    symbol at that stamp (ties -> lexicographically smallest symbol id).
    """
    best: Optional[tuple[float, int, str]] = None
    for record in records:
        stamp = int(record.get("decision_ns", record.get("stamp_ns", 0)))
        weights, _err = _weights_mapping(record)
        if not weights:
            continue
        held = {
            sym: abs(w) for sym, w in weights.items() if abs(w) > HELD_WEIGHT_TOL
        }
        if not held:
            continue
        largest = max(held.values())
        symbol = sorted(s for s, v in held.items() if v == largest)[0]
        key = (-largest, stamp, symbol)
        if best is None or key < best:  # largest |w|, then EARLIEST stamp, then symbol
            best = (-largest, stamp, symbol)
    if best is None:
        raise ContractViolation(
            "schedule_drop_one found no held position in the whole schedule"
        )
    neg_weight, stamp, symbol = best
    return {
        "stamp_ns": stamp,
        "symbol": symbol,
        "held_abs_weight": round(-neg_weight, 12),
        "proven_held": True,
        "pin": DROP_ONE_PIN,
    }


def build_drop_one_book(
    weights: Mapping[str, float],
    *,
    dropped_symbol: str,
) -> dict[str, Any]:
    """Renormalize one 6v6 book after dropping one held symbol (per the pin).

    The eleven survivors keep their sides; each side is renormalized WITHIN
    itself at constant per-side gross 0.5 (dropped side: 5 names at 1/10;
    untouched side: 6 names at 1/12), preserving gross 1.0 and dollar
    neutrality; middle tercile flat; the dropped symbol must be HELD at this
    stamp (fail closed otherwise).  See :data:`DROP_ONE_PIN`.
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
    if sorted((n_longs, n_shorts)) != sorted(
        (DROP_ONE_LEG_NAMES, DROP_ONE_LEG_NAMES + 1)
    ):
        raise ContractViolation(
            "drop-one renormalization expects one 5-name side and one "
            f"6-name side; got {n_longs}L/{n_shorts}S"
        )
    half_gross = float(GROSS_TARGET) / 2.0
    renormalized = {}
    for sym, w in sorted(survivors.items()):
        per_name = half_gross / float(n_longs if w > 0.0 else n_shorts)
        renormalized[sym] = round(per_name if w > 0.0 else -per_name, 12)
    return {
        "schema": "v13i.liqepis.drop_one_book.v1",
        "dropped_symbol": dropped,
        "dropped_side": "long" if weights_map[dropped] > 0.0 else "short",
        "weights": [[sym, renormalized[sym]] for sym in sorted(renormalized)],
        "longs": sorted(s for s, w in renormalized.items() if w > 0.0),
        "shorts": sorted(s for s, w in renormalized.items() if w < 0.0),
        "per_name_weight_dropped_side": round(
            half_gross / float(min(n_longs, n_shorts)), 12
        ),
        "per_name_weight_untouched_side": round(
            half_gross / float(max(n_longs, n_shorts)), 12
        ),
        "gross": round(
            math.fsum(abs(w) for w in renormalized.values()), 12
        ),
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
def _weights_mapping(record: Any) -> tuple[dict[str, float], Optional[str]]:
    """``[[sym, w], ...]`` / ``{sym: w}`` -> mapping (mirrors V12 feasibility)."""
    body = record.get("weights") if isinstance(record, Mapping) else record
    if isinstance(body, Mapping):
        out: dict[str, float] = {}
        for sym, weight in body.items():
            out[str(sym)] = float(weight)
        return out, None
    if isinstance(body, Sequence) and not isinstance(body, (str, bytes)):
        out = {}
        for entry in body:
            out[str(entry[0])] = float(entry[1])
        return out, None
    return {}, "BAD_BOOK_SHAPE"


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
    "BAR_INTERVAL_NS",
    "BENCHMARK_SYMBOL",
    "CAP_MAX",
    "CloseFillEvent",
    "CONTROL_ARM",
    "CONTROL_ARM_CONFIG_ID",
    "DAY_NS",
    "DECISION_CLOCK",
    "DIRECTION",
    "DROP_ONE_LEG_NAMES",
    "DROP_ONE_PER_NAME_WEIGHT",
    "DROP_ONE_PIN",
    "EligibilityShortfall",
    "F1_PURGED_STAMP_ISO",
    "FAMILY_ID",
    "FIRST_STAMP_ISO",
    "FOLD_WINDOWS",
    "FOLDS_CONTRACT",
    "FILL_RULE",
    "FORMATION_BARS_ANCHOR",
    "FORMATION_BARS_NEIGHBOUR",
    "FORMATION_DAYS_ANCHOR",
    "FORMATION_DAYS_NEIGHBOUR",
    "FusionBarSeries",
    "GROSS_TARGET",
    "H_EVALUATION",
    "HOLDING_DAYS",
    "LEGS_PER_SIDE",
    "MATRIX_COHORT_HINT",
    "MIN_ELIGIBLE",
    "MIN_FOLDS",
    "NEIGHBOUR_ARM",
    "NEIGHBOUR_ARM_CONFIG_ID",
    "PER_NAME_WEIGHT",
    "PURGE_DAYS",
    "REASON_DEGENERATE_ZERO_Q",
    "REASON_INSUFFICIENT_HISTORY",
    "REASON_MISSING_OR_NON_FINITE_SLOT",
    "REASON_UNAVAILABLE_ROW",
    "SIGNAL_NAME",
    "STATUS_OK",
    "STRATEGY_ID",
    "WINDOW_END_ISO",
    "WINDOW_START_ISO",
    "build_drop_one_book",
    "build_liqepis_book",
    "cash_reconciliation",
    "compute_targets_at",
    "effective_schedule",
    "episodicity_at",
    "fold_assignments",
    "fold_end_ns",
    "force_flat_span_end",
    "iso_utc",
    "next_allowed_close_fill",
    "parse_iso_utc",
    "schedule_drop_one",
    "select_drop_one_symbol_at",
    "series_from_rows",
    "signal_scores_at",
    "stamp_calendar",
    "window_end_ns",
    "window_start_ns",
]
