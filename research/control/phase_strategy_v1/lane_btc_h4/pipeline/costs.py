"""PSV1 lane_btc_h4 — cost model arithmetic (frozen; unit fixtures in tests_py).

BTC costs: taker 5 bps/side + slippage 1 bps/side = 6 bps/side, 12 bps round
trip. Funding 1.377e-5 per 8h, signed by position (long pays positive).
Tier multipliers (1.0/1.5/2.0) apply to the FULL cost stack.

These are pure arithmetic helpers over SYNTHETIC inputs in tests; the
feasibility ceiling uses cadence counts only (no strategy returns anywhere).
"""

from __future__ import annotations

from . import config

BPS = 1e-4


def side_cost_fraction(tier: float = 1.0) -> float:
    """One fill's fee+slippage as a fraction of notional, tiered."""
    return config.COST_PER_SIDE_BPS * BPS * tier


def round_trip_cost_fraction(tier: float = 1.0) -> float:
    return config.COST_ROUND_TRIP_BPS * BPS * tier


def funding_cost_fraction(boundaries: int, position_sign: int, tier: float = 1.0) -> float:
    """Signed funding cost: positive = paid by the position.

    Long (+1) pays the positive frozen rate; short (-1) receives it.
    """
    return boundaries * config.FUNDING_PER_8H * position_sign * tier


def per_trade_cost_fraction(boundaries: int, position_sign: int, tier: float = 1.0,
                            include_funding: bool = True) -> float:
    """Round-trip fees+slippage plus signed funding, full stack, tiered.

    Cost convention: positive numbers are costs paid by the strategy.
    """
    c = round_trip_cost_fraction(tier)
    if include_funding:
        c += funding_cost_fraction(boundaries, position_sign, tier)
    return c


def ceiling_check(trades_per_fold: dict, median_hold_bars: int | None,
                  tier_survival: float = 1.5) -> dict:
    """Plan §11 arithmetic: cadence vs cost at 1.5x with the frozen plausible-edge bound.

    Uses hold length in H4 bars only to count 8h funding boundaries
    (bars_to_boundary_count: bar-level approximation used for the ceiling
    table; exact timestamp count lives in funding_boundary_count).
    """
    total_trades = int(sum(trades_per_fold.values()))
    n_folds = max(1, len(trades_per_fold))
    rt_15 = round_trip_cost_fraction(tier_survival)
    fund_per_day_15 = funding_cost_fraction(3, 1, tier_survival)  # 3 boundaries/day
    hold_days = (median_hold_bars * 4 / 24) if median_hold_bars else 0.0
    cost_at_15_bps = (rt_15 + fund_per_day_15 * hold_days) * 1e4
    struck = cost_at_15_bps > config.PLAUSIBLE_EDGE_BPS
    return {
        "law": "cadence x frozen cost stack vs PLAUSIBLE_EDGE_BPS bound; no strategy returns used",
        "plausible_edge_bps": config.PLAUSIBLE_EDGE_BPS,
        "round_trip_bps_at_1.0x": config.COST_ROUND_TRIP_BPS,
        "funding_per_day_bps_at_1.0x": funding_cost_fraction(3, 1, 1.0) * 1e4,
        "total_trades_all_folds": total_trades,
        "trades_per_fold": {str(k): v for k, v in trades_per_fold.items()},
        "median_hold_days": hold_days,
        "per_trade_cost_bps_at_1.5x": cost_at_15_bps,
        "verdict": "PASS_WITHIN_CEILING" if not struck else "STRUCK_BY_CEILING",
        "margin_note": ("candidate survives the ceiling if its frozen cadence keeps "
                        "1.5x per-trade cost below the preregistered plausible-edge bound; "
                        "actual edge is measured only post-GO in the scored run"),
    }
