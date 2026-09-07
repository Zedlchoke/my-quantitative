"""Frozen cross-sectional tercile/quintile book for A5-V15-F1.

Verbatim from proposal_P1 ``entry_exit_rules`` (nothing tuned):

* entry: on decision date D, rank the eligible symbols by the arm signal
  ascending; LONG side = bottom 7 (elite size leans most SHORT), SHORT side
  = top 7 (elite size leans most LONG -- fade the size-heavy side), middle
  flat.  The causal control runs the IDENTICAL side construction on its own
  signal (long bottom tercile / short top tercile).
* weights: per-name signed weight = ``side_gross / n_side`` with
  ``side_gross = 0.5`` per populated side (0.5/7 ~= 0.0714 for the
  7/6/7 anchor/control; 0.10 for the neighbour's frozen 5/10/5), under the
  0.30 per-symbol signed cap; gross <= 1.0 enforced by construction.
* shrunken cross-sections (amendment_1 refusals shrink the eligible set):
  side counts scale proportionally -- ``n_side = max(1, round(n *
  side_fraction))`` with the frozen fractions 1/3 (anchor/control: 20 -> 7,
  the frozen 7/6/7) and 1/4 (neighbour: 20 -> 5, the frozen 5/10/5), so the
  full-universe books match the frozen counts exactly;
* refusal-while-held dates (A1-ordered PRE-SCORE gross-cap remediation):
  the carried refused weights keep their budget and the fresh book
  renormalizes into the RESIDUAL budget ``GROSS_MAX - sum|carried|``
  (:func:`renormalize_into_residual`), so gross <= 1.0 at every transition.
* ties break by symbol id ascending (deterministic).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping, Tuple

from research.v15.families.elite_size_asym.frozen_identity import (
    ANCHOR_SIDE_FRACTION,
    GROSS_MAX,
    NEIGHBOR_SIDE_FRACTION,
    SIDE_GROSS,
    WEIGHT_CAP_SIGNED,
)


class BookViolation(RuntimeError):
    """A constructed book violates a frozen weight/gross invariant."""


def side_count(n_eligible: int, side_fraction: float) -> int:
    """Frozen proportional side count (7 on 20 at 1/3; 5 on 20 at 1/4)."""
    if n_eligible < 2:
        return 0
    return max(1, int(round(n_eligible * side_fraction)))


def per_name_weight(n_side: int) -> float:
    """``min(side_gross / n_side, cap)`` -- 0.5/7 on the 7/6/7 book."""
    if n_side <= 0:
        return 0.0
    return min(SIDE_GROSS / n_side, WEIGHT_CAP_SIGNED)


@dataclass(frozen=True)
class BookSpec:
    """Frozen per-arm book shape (see arms.py for the arm bindings)."""

    side_fraction: float


ANCHOR_BOOK = BookSpec(side_fraction=ANCHOR_SIDE_FRACTION)
NEIGHBOR_BOOK = BookSpec(side_fraction=NEIGHBOR_SIDE_FRACTION)


def build_book(
    *,
    signals: Mapping[str, float],
    book_spec: BookSpec,
) -> Dict[str, float]:
    """Target signed weights from the eligible cross-section's signals.

    Long the lowest-signal ``n_side`` names, short the highest-signal
    ``n_side`` names, middle flat (deterministic tie-break: symbol id
    ascending).  Raises :class:`BookViolation` on any cap/gross breach
    (fail closed).
    """
    eligible = sorted((str(sym) for sym in signals), key=lambda s: s)
    if len(eligible) < 2:
        return {}
    ordered = sorted(eligible, key=lambda sym: (float(signals[sym]), sym))
    n = len(ordered)
    n_side = side_count(n, book_spec.side_fraction)
    if n_side == 0 or 2 * n_side > n:
        return {}
    weight = per_name_weight(n_side)
    book: Dict[str, float] = {}
    for sym in ordered[:n_side]:
        book[sym] = weight
    for sym in ordered[n - n_side :]:
        book[sym] = -weight
    gross = sum(abs(w) for w in book.values())
    if gross > GROSS_MAX + 1e-12:
        raise BookViolation(f"gross {gross!r} exceeds {GROSS_MAX}")
    if any(abs(w) > WEIGHT_CAP_SIGNED + 1e-12 for w in book.values()):
        raise BookViolation(
            f"per-symbol signed weight exceeds {WEIGHT_CAP_SIGNED}: {book}"
        )
    return {sym: float(w) for sym, w in sorted(book.items())}


def book_gross(book: Mapping[str, float]) -> float:
    return float(sum(abs(w) for w in book.values()))


def side_symbols(book: Mapping[str, float]) -> Tuple[list, list]:
    """(long_symbols, short_symbols) of a book, each sorted."""
    longs = sorted(s for s, w in book.items() if w > 0.0)
    shorts = sorted(s for s, w in book.items() if w < 0.0)
    return longs, shorts


_GROSS_TOL = 1e-12


def renormalize_into_residual(
    desired: Mapping[str, float],
    carried_refused: Mapping[str, float],
    *,
    gross_max: float = GROSS_MAX,
) -> Tuple[Dict[str, float], Dict[str, float]]:
    """Residual-budget renormalization for refusal-while-held dates.

    A1-ordered PRE-SCORE remediation (binding adjudication, cycle
    CRYPTO-V15): when a held symbol's decision is hole-refused, its weight
    is carried unchanged (its decision never becomes a fill) while the
    fresh book renormalizes into the RESIDUAL budget
    ``gross_max - sum(|carried refused weights|)`` -- the fresh side budgets
    scale proportionally to the residual (the frozen 0.30 signed cap still
    binds each name; a downward scale can only shrink weights), and gross
    stays <= gross_max at the transition.

    Returns ``(merged_desired, event)`` where ``merged_desired`` carries the
    (possibly scaled) fresh book PLUS the carried refused weights (their
    budget is reserved; their decision never becomes a fill) and ``event``
    carries the hand-auditable renormalization evidence.  When the fresh
    book already fits the residual it is returned unchanged (no scale-up,
    so the signed cap can never be re-introduced).  When the residual is
    <= 0 the fresh side is forced flat and the event records it
    (unreachable under the frozen 0.30 cap with the folded universes, kept
    as a fail-closed branch).  The refused legs themselves always merge
    back unchanged -- dropping them would turn their carry into a
    threshold-triggered exit fill, exactly the double-charge the
    remediation forbids.
    """
    carried_gross = sum(abs(float(w)) for w in carried_refused.values())
    fresh_gross = sum(abs(float(w)) for w in desired.values())
    residual = gross_max - carried_gross
    carried = {sym: float(w) for sym, w in carried_refused.items()}
    event = {
        "carried_gross": carried_gross,
        "fresh_gross_before": fresh_gross,
        "residual": residual,
        "scale": 1.0,
        "forced_fresh_flat": False,
    }
    if not desired:
        return carried, event
    if residual <= _GROSS_TOL:
        return carried, {**event, "forced_fresh_flat": True}
    if fresh_gross > residual + _GROSS_TOL:
        scale = residual / fresh_gross
        scaled = {sym: float(w) * scale for sym, w in desired.items()}
        return {**scaled, **carried}, {**event, "scale": scale}
    return {**desired, **carried}, event


__all__ = [
    "ANCHOR_BOOK",
    "BookSpec",
    "BookViolation",
    "NEIGHBOR_BOOK",
    "book_gross",
    "build_book",
    "per_name_weight",
    "renormalize_into_residual",
    "side_count",
    "side_symbols",
]
