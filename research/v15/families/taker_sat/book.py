"""Frozen book + schedule machinery for TAKER-SAT.

BOOK (``proposal_P1.json`` ``entry_exit_rules``, verbatim):

* on each 5-day decision date D at 00:00 UTC, rank the available symbols by
  the arm feature S descending; ties broken by symbol name ascending
  (deterministic);
* SHORT the top 5 (extreme buy-side aggression saturation), LONG the bottom
  5 (extreme sell-side aggression saturation);
* signed weight +0.10 per long name, -0.10 per short name; gross = 1.0;
  per-symbol signed weight 0.10 <= cap 0.30 (asserted by construction);
* hold until the next decision date; exit fills at that date's 00:00 UTC
  open;
* if fewer than 10 symbols have complete window data on D, compute ranks on
  the available names; if fewer than 10 are available, stay flat for that
  cycle (preregistered, deterministic);
* force-flat on the last day of each fold and through the 1-day purge.

SCHEDULE: decisions every 5 calendar days from each fold start inside the
fold's effective span ``[start, end - purge)``; each fold's purge-zone first
day 00:00 UTC is a FORCE-FLAT instant.  With ``n >= 10`` available names
both sides always have exactly 5 members, so the book is well-formed by
construction; the cost model charges only weight-DELTA transitions (a
carried book charges exactly 0.0 -- cost once per fill).
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Optional, Sequence

from research.adapter_v10.protocol import ContractViolation
from research.v15.families.taker_sat.frozen_identity import (
    CAP_MAX,
    FOLDS,
    GROSS_MAX,
    MIN_AVAILABLE,
    N_SIDE,
    PURGE_DAYS,
    REBALANCE_DAYS,
    WEIGHT_PER_NAME,
)

DAY_NS = 86_400_000_000_000

SCHEMA_VERSION = "v15i.taker_sat.book.v1"

REASON_OK = "OK"
REASON_INSUFFICIENT_AVAILABLE = "INSUFFICIENT_AVAILABLE_NAMES"


# --------------------------------------------------------------------------- #
# Schedule (frozen folds; the 5-day per-fold grid + force-flat instants)
# --------------------------------------------------------------------------- #
def fold_bounds(folds: Sequence[tuple[str, str, str]] = FOLDS):
    """``[(index, label, start_ns, end_ns)]``; end is EXCLUSIVE."""
    from research.v11.families.oilever_delev.strategy import parse_iso_utc

    out: list[tuple[int, str, int, int]] = []
    for index, (label, start_date, end_exclusive_date) in enumerate(folds):
        start = parse_iso_utc(f"{start_date}T00:00:00Z")
        end = parse_iso_utc(f"{end_exclusive_date}T00:00:00Z")
        if end <= start:
            raise ContractViolation(f"fold {label} has a non-positive window")
        out.append((index, str(label), start, end))
    for (i0, l0, _s0, e0), (i1, l1, s1, _e1) in zip(out, out[1:]):
        if s1 < e0:
            raise ContractViolation(f"fold {l1} overlaps fold {l0}")
    return out


def fold_decision_dates(
    start_ns: int, end_ns: int, *, rebalance_days: int = REBALANCE_DAYS,
    purge_days: int = PURGE_DAYS,
) -> list[int]:
    """Decision stamps ``start + 5k days`` inside ``[start, end - purge)``.

    The 1-day purge zone ``[end - purge, end)`` carries no decision and is
    force-flat; a decision date would never be scheduled there.
    """
    purge_ns = int(purge_days) * DAY_NS
    step = int(rebalance_days) * DAY_NS
    if step <= 0 or purge_ns <= 0:
        raise ContractViolation("rebalance_days and purge_days must be positive")
    purge_start = end_ns - purge_ns
    dates: list[int] = []
    instant = start_ns
    while instant < purge_start:
        dates.append(instant)
        instant += step
    if not dates:
        raise ContractViolation("a fold produced no decision dates (fail-closed)")
    return dates


def schedule(folds: Sequence[tuple[str, str, str]] = FOLDS) -> list[dict[str, Any]]:
    """The chronological boundary schedule of the frozen clock.

    Each entry: ``{"instant_ns", "kind" ("decision" | "force_flat"),
    "fold_index", "fold_label"}``.  Force-flat instants sit at the purge
    zone's first day 00:00 UTC (the fold's last covered date) -- flat through
    the purge and into the next fold's first decision.
    """
    boundaries: list[dict[str, Any]] = []
    for index, label, start, end in fold_bounds(folds):
        purge_ns = int(PURGE_DAYS) * DAY_NS
        for instant in fold_decision_dates(start, end):
            boundaries.append(
                {
                    "instant_ns": int(instant),
                    "kind": "decision",
                    "fold_index": index,
                    "fold_label": str(label),
                }
            )
        boundaries.append(
            {
                "instant_ns": int(end - purge_ns),
                "kind": "force_flat",
                "fold_index": index,
                "fold_label": str(label),
            }
        )
    boundaries.sort(key=lambda b: b["instant_ns"])
    stamps = [b["instant_ns"] for b in boundaries]
    if len(set(stamps)) != len(stamps):
        raise ContractViolation("schedule produced a duplicate instant")
    for fold_index in sorted({b["fold_index"] for b in boundaries}):
        members = [b for b in boundaries if b["fold_index"] == fold_index]
        if not any(b["kind"] == "decision" for b in members):
            raise ContractViolation(f"fold index {fold_index} has no decisions")
    return boundaries


def fold_of_instant(instant_ns: int, folds: Sequence[tuple[str, str, str]] = FOLDS) -> str:
    """The fold label whose ``[start, end)`` covers the instant (realized rows
    at a fold's force-flat edge trail that fold -- the V14 attribution rule)."""
    stamp = int(instant_ns)
    for _index, label, start, end in fold_bounds(folds):
        if start <= stamp < end:
            return str(label)
    raise ContractViolation(f"instant {instant_ns} outside every declared fold")


# --------------------------------------------------------------------------- #
# The frozen 5-vs-5 extreme-fade book
# --------------------------------------------------------------------------- #
def build_book(scores: Mapping[str, float]) -> dict[str, Any]:
    """The deterministic cross-sectional extreme-fade book for one decision.

    ``scores`` maps AVAILABLE symbols (complete window data, decision not
    refused) to their finite feature value.  Ranks are DESCENDING on the
    value with exact ties broken by symbol name ascending: the top
    ``N_SIDE`` names are SHORT, the bottom ``N_SIDE`` names are LONG, the
    middle is unheld.  Fewer than ``MIN_AVAILABLE`` available names stays
    flat for the cycle (preregistered).  ``|w| = 0.10 <= cap 0.30`` and
    ``gross = 1.0 <= 1.0`` hold BY CONSTRUCTION and are asserted.
    """
    cleaned: dict[str, float] = {}
    for raw_sym, raw_value in dict(scores).items():
        sym = str(raw_sym)
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(value):
            cleaned[sym] = value
    available = sorted(cleaned)
    if len(available) < int(MIN_AVAILABLE):
        return {
            "schema": SCHEMA_VERSION,
            "weights": {},
            "longs": [],
            "shorts": [],
            "carried_forward": False,
            "reason_code": REASON_INSUFFICIENT_AVAILABLE,
            "n_available": len(available),
            "ranks": [],
            "gross": 0.0,
            "max_abs_weight": 0.0,
        }
    # descending on value, ties by symbol name ascending (deterministic).
    ordered = sorted(available, key=lambda sym: (-cleaned[sym], sym))
    shorts = ordered[: int(N_SIDE)]
    longs = ordered[len(ordered) - int(N_SIDE):]
    if set(shorts) & set(longs):
        raise ContractViolation(
            "long and short sides overlap (needs >= 2 * N_SIDE available)"
        )
    weights: dict[str, float] = {}
    for sym in longs:
        weights[sym] = float(WEIGHT_PER_NAME)
    for sym in shorts:
        weights[sym] = -float(WEIGHT_PER_NAME)
    gross = math.fsum(abs(w) for w in weights.values())
    max_abs = max(abs(w) for w in weights.values())
    if max_abs > float(CAP_MAX) + 1e-12:
        raise ContractViolation(f"cap breached by construction: {max_abs}")
    if gross > float(GROSS_MAX) + 1e-9:
        raise ContractViolation(f"gross breached by construction: {gross}")
    ranks = {sym: idx + 1 for idx, sym in enumerate(ordered)}
    return {
        "schema": SCHEMA_VERSION,
        "weights": dict(sorted(weights.items())),
        "longs": [[sym, weights[sym]] for sym in sorted(longs)],
        "shorts": [[sym, weights[sym]] for sym in sorted(shorts)],
        "carried_forward": False,
        "reason_code": REASON_OK,
        "n_available": len(available),
        "ranks": [[sym, ranks[sym]] for sym in sorted(ranks)],
        "gross": gross,
        "max_abs_weight": max_abs,
    }


# --------------------------------------------------------------------------- #
# Cost model (exactly once per fill; weight-delta transitions only)
# --------------------------------------------------------------------------- #
def transition_cost(
    old_weights: Mapping[str, float],
    new_weights: Mapping[str, float],
    *,
    prices: Mapping[str, float],
    tick_sizes: Mapping[str, float],
    taker_fee_bps: float,
    slip_ticks: int,
) -> float:
    """``Sigma_symbols |dw| * (fee_bps*1e-4*mult + slip_ticks*tick/price)``.

    The frozen V10 cost arithmetic (fee + adverse-tick slippage per unit
    notional), charged EXACTLY ONCE per fill: a carried book has identical
    prior/target weights, sums zero deltas and charges exactly 0.0.  The
    caller supplies the tier multipliers (base: 1.0 / 1 tick; stress:
    x1.5 / 3 ticks).
    """
    total = 0.0
    symbols = sorted(set(dict(old_weights)) | set(dict(new_weights)))
    for sym in symbols:
        old_w = float(dict(old_weights).get(sym, 0.0))
        new_w = float(dict(new_weights).get(sym, 0.0))
        delta = abs(new_w - old_w)
        if delta <= 1e-15:
            continue
        price = float(prices[sym])
        tick = float(tick_sizes[sym])
        if not (math.isfinite(price) and price > 0.0):
            raise ContractViolation(f"{sym}: non-positive fill price {price!r}")
        if not (math.isfinite(tick) and tick > 0.0):
            raise ContractViolation(f"{sym}: non-positive tick size {tick!r}")
        rate = float(taker_fee_bps) * 1e-4 + int(slip_ticks) * tick / price
        total += delta * rate
    return total


def weights_equal(
    a: Mapping[str, float], b: Mapping[str, float], tol: float = 1e-12
) -> bool:
    """True iff both books carry identical symbols with identical weights."""
    keys = set(dict(a)) | set(dict(b))
    for key in keys:
        if abs(float(dict(a).get(key, 0.0)) - float(dict(b).get(key, 0.0))) > tol:
            return False
    return True


__all__ = [
    "DAY_NS",
    "REASON_INSUFFICIENT_AVAILABLE",
    "REASON_OK",
    "SCHEMA_VERSION",
    "build_book",
    "fold_bounds",
    "fold_decision_dates",
    "fold_of_instant",
    "schedule",
    "transition_cost",
    "weights_equal",
]
