"""RATES-NG1 I-phase SYNTHETIC fixtures (shared by the unit tests and
the --dry-run-plumbing self-check).

SCOPE LAW: these fixtures are 100% synthetic.  No real substrate bytes,
no plane consumption and no market data of any kind enter the I-phase
tests or the dry-run plumbing self-check.  The only real objects used
are committed CODE (clock.ny_close_utc for DST-true timestamps on the
synthetic calendar) and frozen CONSTANTS (fold windows, holding, k,
notional) -- and the frozen rule machinery itself.

Determinism law: every series is a pure function of its seed/shape
constants (an explicit LCG, not a PRNG runtime), so the dry-run
structural counts are exactly reproducible.
"""

from __future__ import annotations

import datetime as dt
import math
from typing import Any

from research.assets.rates_ng1 import clock as ck
from research.assets.rates_ng1.runners.runner import (
    K_MISALIGN_SESSIONS,
    HOLDING_TRADING_DAYS,
    NOTIONAL_PER_LEG_USD,
)

SCHEMA = "rates_ng1/runners/fixtures@1"

#: Frozen tier-2.0 per-leg stress tiers (CS p90 bps), cited verbatim
#: from research/control/rates_ng1_run/p1_cost_contract.json (sha256
#: e7db0eef...; COST CEILING constants, not outcome measurements).
SYNTHETIC_TIERS_BPS = {
    "SHY": 5.979816345415081,
    "TLT": 49.17915491263504,
}

#: Official ER fee facts (0.15%/yr each) -> ACT/365F daily drag, cited
#: from the same frozen contract.
SYNTHETIC_ER_DAILY = {
    "SHY": 0.0015 / 365.0,
    "TLT": 0.0015 / 365.0,
}


class LCG:
    """Deterministic linear congruential generator (Numerical Recipes
    constants); a pure function of the seed."""

    def __init__(self, seed: int):
        self.state = seed & 0xFFFFFFFF

    def next_u01(self) -> float:
        self.state = (1103515245 * self.state + 12345) & 0x7FFFFFFF
        return self.state / 0x7FFFFFFF


def weekday_sessions(start_iso: str, n_sessions: int) -> list[str]:
    """``n_sessions`` consecutive Mon-Fri calendar sessions from
    ``start_iso`` (the fixture's own session calendar; deterministic)."""
    d = dt.date.fromisoformat(start_iso)
    out: list[str] = []
    while len(out) < n_sessions:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def synthetic_grid(n_sessions: int = 320,
                   start_iso: str = "2019-01-07",
                   warmup: int = 8) -> tuple[list[str], list[dict]]:
    """A synthetic bookable grid: weekday sessions; bookable instants
    after ``warmup`` sessions with a predecessor, each carrying the
    session_index, the V7 readable_bar_date (previous grid session) and
    the TRUE 16:00 NY close instant (P1 clock law, DST via zoneinfo --
    legitimately real code on a synthetic calendar)."""
    grid = weekday_sessions(start_iso, n_sessions)
    instants: list[dict] = []
    for t in range(max(1, warmup), n_sessions):
        instants.append({
            "session_index": t,
            "decision_session": grid[t],
            "decision_utc": ck.ny_close_utc(grid[t]).isoformat(),
            "readable_bar_date": grid[t - 1],
        })
    return grid, instants


def synthetic_curve(grid: list[str]) -> dict[str, dict[str, float]]:
    """Synthetic 2 Yr / 10 Yr / 30 Yr par-yield rows: smooth waves
    engineered so the level-orthogonalized shape coordinates cross
    their sample cuts and all three gate variants fire."""
    out: dict[str, dict[str, float]] = {}
    n = len(grid)
    for t, d in enumerate(grid):
        y10 = 2.50 + 0.80 * math.sin(2.0 * math.pi * t / 41.0)
        y2 = (y10 - 1.30
              - 0.55 * math.sin(2.0 * math.pi * t / 17.0 + 0.7))
        y30 = (y10 + 0.90
               + 0.60 * math.cos(2.0 * math.pi * t / 23.0 + 1.1))
        out[d] = {"2 Yr": round(y2, 6), "10 Yr": round(y10, 6),
                  "30 Yr": round(y30, 6)}
    assert len(out) == n
    return out


def synthetic_leg_closes(grid: list[str]) -> dict[str, dict[str, float]]:
    """Synthetic RAW closes for the two mapped legs (slow waves around
    realistic levels; strictly positive)."""
    shy: dict[str, float] = {}
    tlt: dict[str, float] = {}
    n = len(grid)
    for t, d in enumerate(grid):
        shy[d] = round(81.00 + 0.40 * math.sin(2.0 * math.pi * t / 29.0),
                       4)
        tlt[d] = round(99.00
                       + 2.50 * math.sin(2.0 * math.pi * t / 37.0 + 0.4),
                       4)
    assert len(shy) == n and len(tlt) == n
    return {"SHY": shy, "TLT": tlt}


def synthetic_state_inputs(n_sessions: int = 320,
                           start_iso: str = "2019-01-07",
                           warmup: int = 8,
                           ) -> dict[str, Any]:
    """One deterministic synthetic substrate bundle: grid, instants,
    curve rows, leg closes + the frozen cost constants cited."""
    grid, instants = synthetic_grid(n_sessions, start_iso, warmup)
    return {
        "schema": SCHEMA,
        "synthetic": True,
        "real_substrate": False,
        "grid": grid,
        "instants": instants,
        "curve_by_date": synthetic_curve(grid),
        "leg_closes": synthetic_leg_closes(grid),
        "tiers_bps": dict(SYNTHETIC_TIERS_BPS),
        "er_daily": dict(SYNTHETIC_ER_DAILY),
        "frozen_constants_cited": {
            "holding_trading_days": HOLDING_TRADING_DAYS,
            "k_misalign_sessions": K_MISALIGN_SESSIONS,
            "notional_per_leg_usd": NOTIONAL_PER_LEG_USD,
        },
    }
