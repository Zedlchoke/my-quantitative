"""Portfolio construction and target books for frozen family A4 (Z5/A6).

SCHEDULE-ONLY.  Deterministic long-only target weights + explicit cash
residual; no returns, PnL, PF or any scored metric is ever computed here.

Frozen rules implemented (spec ``portfolio_construction``):

- ``"long-only selected ETFs + cash; gross exposure <= 1.0; no shorts, no
  leverage"``;
- anchor/control: ``"equal weight across the 3 selected ETFs (33.3333% each),
  residual 0% to cash"``;
- neighbour: ``"deterministic inverse-volatility: w_i proportional to
  1/sigma_i(t) over the 3 selected ETFs, per-ETF cap 35% (capped then
  renormalized to gross 1.0), residual to cash"``;
- ``"per-ETF weight cap 35% of gross for all arms"``;
- partial holdings: ``"if fewer than 3 ETFs are rankable at t (not expected
  in S0), hold the rankable ones at equal (or inverse-vol) weight and put
  the residual in cash"`` — interpreted deterministically as: the k
  rankable names receive the arm's weighting scheme normalized over the k
  names, scaled to gross k/top_n (equal slots of 1/top_n each), residual to
  cash.  For k = top_n this reduces exactly to the frozen full-book rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from .signals import (
    WEIGHT_EQUAL,
    WEIGHT_INVERSE_VOL,
    canonical_json,
)

# Weights/turnover are rounded ONLY for canonical serialization; all
# arithmetic is full precision.  The rounding is a deterministic pure
# function, so double-generation equality holds exactly.
SERIALIZATION_DP = 10

EPS = 1e-12


def _round(value: float) -> float:
    return round(value + 0.0, SERIALIZATION_DP)


def normalize_capped(
    raw: Mapping[str, float], cap: float, max_iterations: int = 64
) -> dict[str, float]:
    """Cap-and-renormalize raw positive weights to sum 1.0, cap enforced.

    Deterministic iterative redistribution: names above the cap are pinned
    at the cap, the remaining mass is redistributed proportionally to their
    raw weights among the uncapped names, repeated until the cap holds
    everywhere.  Fails closed instead of guessing on non-convergence.
    """
    if not raw:
        return {}
    symbols = sorted(raw)
    if any((not (raw[s] > 0.0)) for s in symbols):
        raise ValueError("raw weights must be strictly positive")
    total = sum(raw[s] for s in symbols)
    weights = {s: raw[s] / total for s in symbols}
    for _ in range(max_iterations):
        over = [s for s in symbols if weights[s] > cap + EPS]
        if not over:
            break
        fixed_mass = sum(cap for _ in over)
        free = [s for s in symbols if s not in set(over)]
        free_mass = 1.0 - fixed_mass
        if free:
            free_raw_total = sum(raw[s] for s in free)
            for s in over:
                weights[s] = cap
            for s in free:
                weights[s] = free_mass * raw[s] / free_raw_total
        else:
            # Every name is at/above the cap: pin all and stop (only
            # possible when len(symbols) * cap >= 1.0).
            for s in over:
                weights[s] = cap
            break
    else:
        raise ValueError("cap renormalization did not converge; fail closed")
    excess = sum(weights.values()) - 1.0
    if abs(excess) > 1e-9:
        raise ValueError("capped weights must sum to 1.0")
    return weights


def weight_book(
    selected: Sequence[str],
    config,  # ArmConfig (typed loosely to avoid a circular import)
    sigma_by_symbol: Mapping[str, float] | None = None,
) -> dict[str, float]:
    """Deterministic target ETF weights for one decision (gross <= 1).

    Equal weighting uses ``1/top_n`` slots; inverse-vol weights are
    proportional to ``1/sigma`` over the selected names, capped at the
    frozen per-ETF cap, then renormalized.  With k < top_n selected names
    the scheme is scaled to gross ``k / top_n`` and the residual goes to
    cash (spec partial-holdings rule).
    """
    if not selected:
        return {}
    k = len(selected)
    scale = k / config.top_n
    if config.weighting == WEIGHT_EQUAL:
        normalized = {s: 1.0 / k for s in selected}
    elif config.weighting == WEIGHT_INVERSE_VOL:
        if sigma_by_symbol is None:
            raise ValueError("inverse-vol weighting requires injected sigmas")
        raw = {}
        for s in selected:
            sigma = sigma_by_symbol.get(s)
            if sigma is None or not (sigma > 0.0):
                raise ValueError(f"inverse-vol weighting requires sigma > 0 for {s}")
            raw[s] = 1.0 / float(sigma)
        normalized = normalize_capped(raw, config.per_etf_cap)
    else:
        raise ValueError(f"unknown weighting {config.weighting!r}")
    weights = {s: scale * normalized[s] for s in sorted(selected)}
    cap = config.per_etf_cap
    for s, w in weights.items():
        if w < -EPS or w > cap + 1e-9:
            raise ValueError(f"weight {w} for {s} violates long-only/{cap} cap")
    if sum(weights.values()) > 1.0 + 1e-9:
        raise ValueError("gross exposure above 1.0; fail closed")
    return weights


def turnover_one_way(
    previous: Mapping[str, float], new: Mapping[str, float]
) -> float:
    """One-way turnover between two books: sum of |Δw| over ETF symbols.

    Convention (documented for the Z6 feasibility check against the frozen
    ``<= 6.0x gross one-way per year`` ceiling): a full 3-name rotation is
    2.0 (each of 3 exits + 3 entries at 1/3); changing one name is 2/3.
    Cash is excluded (it is the residual asset, zero yield per run
    contract).
    """
    symbols = set(previous) | set(new)
    return sum(abs(float(new.get(s, 0.0)) - float(previous.get(s, 0.0))) for s in symbols)


@dataclass(frozen=True)
class BookEntry:
    """One deterministic schedule event for one arm.

    ``decision_fill``: a decision taken at ``decision_date`` fills at
    ``fill_date`` (the immediately following regular session, one-event
    delay, raw executable prices).  ``force_flat``: the frozen force-flat
    event flattens the book at ``fill_date`` close.
    """

    entry_type: str                                   # decision_fill | force_flat
    fill_date: str                                    # ISO date of the fill/flat
    fold_id: str
    targets: dict[str, float]                         # ETF symbol -> weight
    cash_weight: float
    gross: float
    turnover_one_way: float
    decision_date: str | None = None                  # None for force_flat
    fill_ref_prices: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.entry_type not in ("decision_fill", "force_flat"):
            raise ValueError(f"unknown entry type {self.entry_type!r}")
        if self.entry_type == "decision_fill" and self.decision_date is None:
            raise ValueError("decision_fill entries carry a decision_date")
        gross = sum(self.targets.values())
        if abs(gross - self.gross) > 1e-9:
            raise ValueError("gross must equal the sum of target weights")
        if abs(self.cash_weight + self.gross - 1.0) > 1e-9:
            raise ValueError("cash weight must be the residual to 1.0")
        for w in self.targets.values():
            if w < 0.0:
                raise ValueError("long-only: negative target weight")

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "entry_type": self.entry_type,
            "decision_date": self.decision_date,
            "fill_date": self.fill_date,
            "fold_id": self.fold_id,
            "targets": {s: _round(w) for s, w in sorted(self.targets.items())},
            "cash_weight": _round(self.cash_weight),
            "gross": _round(self.gross),
            "turnover_one_way": _round(self.turnover_one_way),
            "fill_ref_prices": {
                s: _round(p) for s, p in sorted(self.fill_ref_prices.items())
            },
        }


@dataclass(frozen=True)
class TargetBookStream:
    """The deterministic target-book stream of one arm + schedule summary."""

    family_id: str
    arm_id: str
    arm_config_digest: str
    calendar_id: str
    entries: tuple[BookEntry, ...]
    summary: dict[str, object]

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "family_id": self.family_id,
            "arm_id": self.arm_id,
            "arm_config_digest": self.arm_config_digest,
            "calendar_id": self.calendar_id,
            "entries": [entry.to_canonical_dict() for entry in self.entries],
            "summary": self.summary,
        }

    def to_canonical_json(self) -> str:
        return canonical_json(self.to_canonical_dict())
