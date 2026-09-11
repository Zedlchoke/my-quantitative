"""Dual-book accounting kernel for FOREX-NG1 (I-phase).

Frozen laws (selection freeze cost contract + V8 kernel inheritance):

- cost = notional x 1.5 bps/side x stress tier, charged exactly ONCE per
  FILL; a round trip is 2 fills (entry + exit) => 2 charges, never
  re-scaled after booking;
- ladder {1.0, 1.5, 2.0}, tier 2.0 PRIMARY;
- PnL identity (V2..V8 inherited USD-unit design):
  pnl_usd = direction x notional_usd x (exit_price / entry_price - 1);
- dual books: GROSS = price-only (no costs); NET(tier) = gross - 2 x
  per-fill cost at that tier.

SCORED GATING: ``compute_outcomes`` requires ``scored=True`` AND a
spot-channel authority status of AUTHORIZED, and this lane NEVER enables
it (the dry-run consumes decision records only).  The unit tests
exercise the kernel on synthetic /tmp fixtures, never on the pinned
series.
"""

from __future__ import annotations

import math

from research.assets.forex_ng1.run import config as C


class AccountingRefused(Exception):
    """Fail-closed accounting refusal (dry-run lanes never compute
    outcomes)."""


def bps_cost(notional_usd: float, tier: float) -> float:
    """Per-fill cost in USD: notional x 1.5 bps x tier (once per fill)."""
    if tier not in C.COST_TIER_LADDER:
        raise AccountingRefused(f"tier {tier!r} not in the frozen ladder")
    if notional_usd <= 0:
        raise AccountingRefused("notional must be positive")
    return notional_usd * (C.COST_BPS_PER_SIDE / 10000.0) * float(tier)


def round_trip_costs(notional_usd: float,
                     tiers: tuple = C.COST_TIER_LADDER) -> dict:
    """Once-per-fill cost blocks for one round trip (2 fills).  The
    per-fill charge is listed separately so 'once per fill' is an
    auditable property, not an assertion."""
    return {
        str(tier): {
            "fills": 2,
            "cost_per_fill_usd": bps_cost(notional_usd, tier),
            "cost_round_trip_usd": 2.0 * bps_cost(notional_usd, tier),
        }
        for tier in tiers}


def price_pnl_usd(direction: int, notional_usd: float, entry_price: float,
                  exit_price: float) -> float:
    """The frozen PnL identity (no costs)."""
    if entry_price <= 0 or exit_price <= 0:
        raise AccountingRefused("prices must be positive")
    return direction * notional_usd * (exit_price / entry_price - 1.0)


def compute_outcomes(decisions: list[dict], prices_by_pair: dict,
                     *, scored: bool = False,
                     spot_authority: str | None = None) -> dict:
    """Dual-book outcome computation.  REFUSED unless scored=True and the
    spot channel is AUTHORIZED (fail-closed; the I lane never calls this
    with scored=True -- the refusal below is the tested behavior)."""
    if not scored:
        raise AccountingRefused(
            "outcome computation refused: scored=False (dry-run lane; "
            "no PnL may be computed here)")
    if spot_authority != "AUTHORIZED":
        raise AccountingRefused(
            "outcome computation refused: spot channel authority "
            f"{spot_authority!r} != AUTHORIZED")
    gross, net = [], {str(t): [] for t in C.COST_TIER_LADDER}
    for rec in decisions:
        px = prices_by_pair[rec["pair"]]
        entry = px[rec["entry_grid_day"]]
        exit_ = px[rec["exit_grid_day"]]
        notional = rec["units"] * C.NOTIONAL_USD_UNIT
        g = price_pnl_usd(rec["direction"], notional, entry, exit_)
        gross.append(g)
        for tier in C.COST_TIER_LADDER:
            cost = 2.0 * bps_cost(notional, tier)
            net[str(tier)].append(g - cost)
    return {
        "trades": len(decisions),
        "gross": book_metrics(gross),
        "net": {t: book_metrics(v) for t, v in net.items()},
    }


def book_metrics(pnls: list[float]) -> dict:
    """Count/sum/expectancy metrics of one book (used by the scored lane;
    pure function, exercised on fixtures only in this lane)."""
    if not pnls:
        return {"trades": 0, "total": None, "expectancy": None}
    total = math.fsum(pnls)
    return {"trades": len(pnls), "total": total,
            "expectancy": total / len(pnls)}
