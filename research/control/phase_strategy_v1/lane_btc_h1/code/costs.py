"""Cost model arithmetic for BTC_H1 (plan sec 9 + dispatch).

BTC USDT-M perp: taker fee 5 bps/side, slippage 1 bps/side => 6 bps/side,
12 bps round trip. Funding 1.377e-5 per 8h, SIGNED by position (a long pays
positive funding; a short receives it). Tier multipliers 1.0/1.5/2.0 apply to
the FULL cost stack (fees + slippage + funding).

This module is pure arithmetic on NOTIONAL FRACTIONS. It never sees real
history and cannot produce strategy PnL: callers pass signed position
durations and prices for unit fixtures only.
"""
from __future__ import annotations

from dataclasses import dataclass

FEE_TAKER_BPS_PER_SIDE = 5.0
SLIPPAGE_BPS_PER_SIDE = 1.0
BPS_PER_SIDE = FEE_TAKER_BPS_PER_SIDE + SLIPPAGE_BPS_PER_SIDE  # 6.0
ROUND_TRIP_BPS = 2.0 * BPS_PER_SIDE  # 12.0
FUNDING_PER_8H = 1.377e-5  # fraction of notional, signed by position
FUNDING_TIMESTAMPS_HOURS = (0, 8, 16)  # UTC hours at which funding accrues

TIERS = (1.0, 1.5, 2.0)


@dataclass(frozen=True)
class Fill:
    """One execution. price in quote units; direction +1 long entry /
    -1 short entry (exit is the opposite side)."""
    price: float
    direction: int  # +1 opens long, -1 opens short
    timestamp_hours: float  # fractional hours since epoch (UTC)


def round_trip_cost_fraction(tier: float = 1.0) -> float:
    """Fee+slippage cost of one open+close as a fraction of notional."""
    return tier * ROUND_TRIP_BPS / 1e4


def funding_between(entry_fill: Fill, exit_fill: Fill, tier: float = 1.0) -> float:
    """Signed funding fraction accrued strictly inside (entry, exit] at the
    frozen funding timestamps. Positive value = cost to a long."""
    if entry_fill.direction not in (1, -1):
        raise ValueError("direction must be +1/-1")
    t0, t1 = entry_fill.timestamp_hours, exit_fill.timestamp_hours
    if t1 <= t0:
        return 0.0
    n_accruals = 0
    # count funding timestamps in (t0, t1]
    day = 24.0
    first_day = int(t0 // day)
    last_day = int(t1 // day)
    for d in range(first_day, last_day + 1):
        for hh in FUNDING_TIMESTAMPS_HOURS:
            t = d * day + hh
            if t0 < t <= t1:
                n_accruals += 1
    return entry_fill.direction * tier * FUNDING_PER_8H * n_accruals


def position_cost_fraction(entry_fill: Fill, exit_fill: Fill,
                           tier: float = 1.0) -> dict:
    """Full cost stack for one position as fractions of notional.
    fee+slip is sign-independent; funding is signed (positive = cost to long,
    negative = rebate to long / cost to short)."""
    fees = round_trip_cost_fraction(tier)
    fund = funding_between(entry_fill, exit_fill, tier)
    return {
        "tier": tier,
        "fees_slippage_fraction": fees,
        "fees_slippage_bps": fees * 1e4,
        "funding_fraction_signed": fund,
        "funding_bps_signed": fund * 1e4,
        "total_cost_bps_signed": (fees + fund) * 1e4,
    }
