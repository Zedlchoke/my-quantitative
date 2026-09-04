"""The frozen OITD hysteresis tercile book (V13 I lane, A13-V13-A8-OITD).

Implements the book construction of ``research/proposals/v13/a8/OITD.md``
section 5 verbatim, as a PURE function of the PIT score map and the
previous retained book -- no data access, no clock, no PnL:

1. rank the eligible symbols by the arm's signal: ASCENDING for the
   unwind-duration arms (anchor / neighbour: long lowest-D tercile, short
   highest-D tercile) and DESCENDING for the causal control (long
   highest-turnover tercile, short lowest-turnover tercile); exact ties
   break by lexicographically smallest symbol id;
2. with ``n`` eligible names the tercile sizes are ``n // 3`` each: the
   ``n // 3`` best ranks are the long-ENTRY zone, the ``n // 3`` worst
   ranks the short-ENTRY zone, and the middle ranks are the BUFFER;
3. hysteresis: a flat symbol enters its zone's side; a held side exits
   ONLY when its rank crosses beyond the buffer into the opposite entry
   zone (a held long flips short; a held short flips long).  A long that
   drifts into the buffer stays long; a short in the buffer stays short;
4. equal weight per side ``min(leg_gross / n_side, cap)``; a side with
   fewer than 2 members leaves its budget in cash (no renormalisation of
   the other side);
5. FAIL-CLOSED membership guard: if either side has fewer than
   ``min_side_members`` (4) members at a stamp, that stamp's rebalance is
   SKIPPED and the previous book is carried (``carried_forward=True``) --
   no position-zeroing inference.  A held symbol that lost eligibility
   likewise skips the stamp (the previous book is held verbatim).  When
   there is no previous book to hold (flat start) the stamp fails closed
   with :class:`EligibilityShortfall`: a stamp without a well-formed book
   has NO book;
6. ``|w| <= cap`` and gross ``<= 2 * leg_gross <= 1.0`` hold BY
   CONSTRUCTION and are asserted after construction.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Optional

from research.adapter_v10.protocol import (
    AdapterError,
    ContractViolation,
    WEIGHT_TOL,
)

SCHEMA_VERSION = "v13i.oitd.book.v1"

WEIGHT_TOL_ = float(WEIGHT_TOL)

#: Reason codes for carried (skipped) rebalances.
REASON_HELD_INELIGIBLE = "HELD_SYMBOL_INELIGIBLE_BOOK_CARRIED"
REASON_SIDE_TOO_THIN = "SIDE_MEMBERSHIP_BELOW_MIN_BOOK_CARRIED"
REASON_OK = "OK"


class EligibilityShortfall(AdapterError):
    """A stamp has no well-formed book -- fail closed, never inferred."""


def build_hysteresis_book(
    scores: Mapping[str, Any],
    *,
    prev_book: Optional[Mapping[str, float]] = None,
    sort_ascending: bool,
    leg_gross: float,
    cap_max: float,
    min_side_members: int,
    min_eligible: int,
) -> dict[str, Any]:
    """The deterministic hysteresis tercile book for one decision stamp.

    ``scores`` maps PIT-eligible-candidate symbols to their signal value
    (already direction-normalised by the caller only in the sense of
    ``sort_ascending``; this module never inspects the signal's meaning).
    ``prev_book`` is the previous retained decision's target weights
    (``None``/empty = flat start).  Non-finite score entries are
    INELIGIBLE and recorded -- never guessed.
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
    held_prev = {sym for sym, w in prev_weights.items() if abs(w) > WEIGHT_TOL_}

    # fail-closed rule 5a: a held symbol without a computable score skips
    # the stamp (the previous book is held; no position-zeroing inference).
    missing_held = sorted(held_prev - set(cleaned))
    if missing_held:
        if not held_prev:
            raise ContractViolation("unreachable: missing_held with empty book")
        if len(prev_weights) == 0:
            raise EligibilityShortfall("no previous book to carry")
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
            f"only {len(eligible)} eligible names at this stamp; the "
            f"hysteresis book requires >= {int(min_eligible)} (fail-closed)"
        )

    n = len(eligible)
    sign = 1.0 if sort_ascending else -1.0
    ordered = sorted((sign * cleaned[sym], sym) for sym in eligible)
    ranks = {sym: idx + 1 for idx, (_key, sym) in enumerate(ordered)}
    n_lo = n // 3
    n_hi = n // 3

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
    for sym in eligible:
        z = zone(ranks[sym])
        if sym in prev_side["long"]:
            # exit (flip) only when the rank crosses beyond the buffer into
            # the opposite entry zone; buffer drift keeps the held side.
            if z == "SHORT_ENTER":
                shorts.add(sym)
            else:
                longs.add(sym)
        elif sym in prev_side["short"]:
            if z == "LONG_ENTER":
                longs.add(sym)
            else:
                shorts.add(sym)
        else:
            if z == "LONG_ENTER":
                longs.add(sym)
            elif z == "SHORT_ENTER":
                shorts.add(sym)

    # fail-closed rule 5b: a side below the membership floor skips the stamp.
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
    # rule 4: side budget in cash when a side has < 2 members (guard; the
    # membership floor above keeps this unreachable in the frozen family).
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
    held = {sym: w for sym, w in weights.items() if abs(w) > WEIGHT_TOL_}
    if not held:
        raise EligibilityShortfall("empty book after construction (fail-closed)")

    availability_ratio = len(cleaned) / float(max(n, 1))
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
        "gross": gross,
        "max_abs_weight": max_abs,
        "signal_availability_ratio": availability_ratio,
        "ineligible": dict(sorted(ineligible.items())),
        "tercile_sizes": {"long_entry": n_lo, "buffer": n - n_lo - n_hi, "short_entry": n_hi},
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

    Drop-one design (OITD.json item8): at every decision stamp drop the
    HELD symbol with maximum |weight|.  ``None`` when nothing is held.
    """
    held = [
        (abs(float(w)), str(sym))
        for sym, w in weights.items()
        if abs(float(w)) > WEIGHT_TOL_
    ]
    if not held:
        return None
    top = max(magnitude for magnitude, _sym in held)
    # deterministic tie-break: max |w|, then lexicographically SMALLEST name
    candidates = sorted(sym for magnitude, sym in held if magnitude == top)
    return candidates[0]


def drop_one_book(
    weights: Mapping[str, float],
) -> dict[str, Any]:
    """Drop the held max-|weight| symbol; remaining weights UNCHANGED.

    No post-score renormalisation (OITD.json item8, verbatim).  A
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
        if str(sym) != target and abs(float(w)) > WEIGHT_TOL_
    }
    return {
        "dropped_symbol": target,
        "dropped_weight": float(weights[target]),
        "weights": [[sym, remaining[sym]] for sym in sorted(remaining)],
        "n_held_after": len(remaining),
    }


__all__ = [
    "EligibilityShortfall",
    "REASON_HELD_INELIGIBLE",
    "REASON_OK",
    "REASON_SIDE_TOO_THIN",
    "SCHEMA_VERSION",
    "build_hysteresis_book",
    "drop_one_book",
    "held_max_abs_weight_symbol",
]
