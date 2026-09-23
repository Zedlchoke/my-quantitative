"""STOCKS-AMIHUD-V1 engine — frozen family_contract execution.

Implementation decisions pinned in impl_contract.json BEFORE any PnL:
  fold force-flat exit at the fold's LAST SESSION CLOSE; adjusted-open
  fills (raw open x adj factor); per-fold AUM_ref dollar base + compounded
  equity curve for MDD/return%; death exits and fold exits pay their fill
  cost like any other fill.
Guard classes iii/iv FAIL LOUD via FailLoud.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

from .panel import NameSeries, sessions_from_spy

IMPL_DIR = Path(__file__).resolve().parents[1]

GRID_START = "2019-01-02"
GRID_STEP = 21
WARMUP = 252
PRICE_FLOOR = 1.00
DV_FLOOR = 2_000_000.0
DV_WINDOW = 60
DV_MIN_PRESENT = 30
AUM_REF = 1_000_000.0
CAP_FRAC = 0.15
BANDS = [(50_000_000.0, 10.0), (10_000_000.0, 15.0), (2_000_000.0, 25.0)]  # (ge, bps)
STRESS_MULT = 2.0
FOLDS = {"F1_2019": ("2019-01-01", "2019-12-31"),
         "F2_2020": ("2020-01-01", "2020-12-31"),
         "F3_2021_22": ("2021-01-01", "2022-12-31")}
ANNUAL_MARKS = {"2021": "2021-12-31"}


class FailLoud(SystemExit):
    """Guard classes iii/iv — zero/negative count or statistical denominator."""


def band_bps(dvmed60: float) -> float:
    for floor, bps in BANDS:
        if dvmed60 >= floor:
            return bps
    return 25.0  # unreachable for eligible names; fails closed economically


@dataclass
class Guards:
    adj_excluded: int = 0
    dv_excluded: int = 0
    formation_skip_ret: int = 0
    formation_skip_dv: int = 0
    names_skipped_no_bar_at_t: int = 0
    names_skipped_no_t1: int = 0
    unbookable_dates: int = 0
    death_exits: int = 0
    fold_exits: int = 0
    rebalance_exits: int = 0
    entries: int = 0

    def as_dict(self) -> dict:
        return dict(self.__dict__)


@dataclass
class Hold:
    code: str
    entry_date: str
    entry_px: float          # adjusted basis
    weight: float
    notional: float
    entry_cost: float


def eligible_at(ns: NameSeries, t_i: int, t1_i: int, dvmed: float | None,
                sessions: list[str]) -> bool:
    # dynamic warmup: 253rd served session at the earliest
    if t_i < WARMUP:
        return False
    if not ns.adj_ok[t_i]:
        return False
    if ns.adj[t_i] < PRICE_FLOOR:
        return False
    if dvmed is None or dvmed < DV_FLOOR:
        return False
    if t1_i is None:
        return False
    return True


def dvmed60(ns: NameSeries, t_i: int) -> float | None:
    lo = max(0, t_i - DV_WINDOW + 1)
    vals = [ns.dv[i] for i in range(lo, t_i + 1) if ns.dv[i] > 0.0]
    if len(vals) < DV_MIN_PRESENT:
        return None
    vals.sort()
    n = len(vals)
    return vals[n // 2] if n % 2 == 1 else 0.5 * (vals[n // 2 - 1] + vals[n // 2])


def illiq(ns: NameSeries, t_i: int, D: int, guards: Guards) -> float | None:
    """Mean of |r_d| / DV_d over the D most recent served sessions < t."""
    lo = max(0, t_i - D, 1)  # need a previous bar for r
    terms: list[float] = []
    for i in range(lo, t_i):
        if not (ns.adj_ok[i] and ns.adj_ok[i - 1]):
            guards.formation_skip_ret += 1
            continue
        denom = ns.adj[i - 1]
        if not (denom > 0.0 and math.isfinite(denom)):   # class i
            guards.formation_skip_ret += 1
            continue
        r = ns.adj[i] / denom - 1.0
        if ns.dv[i] <= 0.0:                              # class ii
            guards.formation_skip_dv += 1
            continue
        terms.append(abs(r) / ns.dv[i])
    if len(terms) < max(D // 2, 1):
        return None          # formation quorum (pinned: family_contract v2)
    return sum(terms) / len(terms)


def past_ret5(ns: NameSeries, t_i: int, guards: Guards) -> float | None:
    lo = max(0, t_i - 5, 1)
    if lo == t_i:
        return None
    if not (ns.adj_ok[t_i - 1] and ns.adj_ok[lo - 1]):
        guards.formation_skip_ret += 1
        return None
    denom = ns.adj[lo - 1]
    if not (denom > 0.0 and math.isfinite(denom)):       # class i
        guards.formation_skip_ret += 1
        return None
    return ns.adj[t_i - 1] / denom - 1.0


def build_grid(sessions: list[str]) -> list[str]:
    idx = next((i for i, s in enumerate(sessions) if s >= GRID_START), None)
    if idx is None:
        raise FailLoud("no sessions at/after grid start")
    return sessions[idx::GRID_STEP]


def rank_book(scores: dict[str, float]) -> list[str]:
    """Top rank-count quintile; ties by ticker lexicographic."""
    n_elig = len(scores)
    if n_elig == 0:
        return []
    n_book = min(-(-n_elig // 5), n_elig)  # ceil(0.2*n) — class iii denominator-free
    order = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    return [c for c, _ in order[:n_book]]


def weights_for(book: list[str], dvmeds: dict[str, float]) -> dict[str, float]:
    n = len(book)
    if n <= 0:
        raise FailLoud("weights_for on empty book")      # class iii fail loud
    w: dict[str, float] = {}
    for c in book:
        cap = CAP_FRAC * dvmeds[c] / AUM_REF
        w[c] = min(1.0 / n, cap)
    return w
