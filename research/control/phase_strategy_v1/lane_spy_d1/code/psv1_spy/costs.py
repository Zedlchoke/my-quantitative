"""Cost arithmetic units (SPY tier stack). COSTS ONLY — no returns.

Frozen SPY cost law (plan section 6 / dispatch):
  - 10 bps per fill, 20 bps per round trip at tier 1.0x;
  - tier multiplier applies to the FULL stack (per-fill and round-trip).
Tiers are frozen: 1.0x / 1.5x / 2.0x.
"""

from typing import Dict

PER_FILL_BPS = 10.0
ROUND_TRIP_BPS = 20.0
TIERS = (1.0, 1.5, 2.0)


def fill_cost_bps(n_fills: int, tier: float) -> float:
    if tier not in TIERS:
        raise ValueError(f"tier must be one of {TIERS}, got {tier}")
    return round(n_fills * PER_FILL_BPS * tier, 6)


def round_trip_cost_bps(n_round_trips: int, tier: float) -> float:
    if tier not in TIERS:
        raise ValueError(f"tier must be one of {TIERS}, got {tier}")
    return round(n_round_trips * ROUND_TRIP_BPS * tier, 6)


def tier_table(n_fills: int, n_round_trips: int) -> Dict[str, Dict[str, float]]:
    """Two equivalent views of the SAME cost money: n_fills x per-fill and
    n_round_trips x round-trip (2 fills = 1 round trip = 20 bps at 1.0x).
    No summation: the two views are not additive."""
    return {
        f"tier_{tier}x": {
            "fills_view_bps": fill_cost_bps(n_fills, tier),
            "round_trips_view_bps": round_trip_cost_bps(n_round_trips, tier),
            "equivalence_note": "2 fills = 1 round trip; both views price the same money and are never summed",
        }
        for tier in TIERS
    }
