"""COMMODITIES-NG1 P1 dual-book accounting kernel (inherited, not forked).

Root kernel: ``research/accounting.py`` -- the shared dual-book
accounting module (canonical PnL field semantics, terminal policy,
fold/experiment accounting identity) -- is IMPORTED here and every
ledger this kernel emits is reconciled through
``build_accounting_reconciliation`` from that module.  Nothing from the
root module is re-implemented locally.

Laws wired for the commodities cycle (plan section 5, Q-8, Q-16):

- cost is charged exactly ONCE per FILL; a round trip is 2 fills
  (entry + exit) => exactly 2 transaction charges, never re-scaled
  after booking;
- stress tier ladder ``{1.0, 1.5, 2.0}``, tier ``2.0`` PRIMARY (Q-8:
  the transaction component is the Corwin-Schultz p90 half-spread
  measured from RAW EOD highs/lows; the tier scales ONLY this
  transaction component);
- instrument drag (expense-ratio daily accrual + measured
  same-underlying tracking-divergence proxy where pairs exist, Q-16)
  is a DAILY ACCRUAL on the NET books and is tier-independent: it is
  a fact of holding the instrument, not a stress parameter;
- dual books: ``GROSS`` = price-only PnL; ``NET(tier)`` = gross minus
  transaction costs (once per fill, tier-scaled) minus drag accruals
  (tier-independent);
- PnL identity (USD-unit design inherited through the forex-ng1 P1
  kernel shape): ``direction x notional x (exit/entry - 1)``;
- terminal policy: open legs are force-closed at the last observable
  mark under the root module's ``TERMINAL_POLICY`` so gross, net and
  reconciliation share ONE population.

This module computes NO market outcome: it is exercised on synthetic
fixtures in the P1 tests and, later phases, on decision records under
the cycle's own scored-execution gate.
"""

from __future__ import annotations

import math

# Root dual-book kernel module: imported, NEVER forked (packet law).
from research.accounting import (  # noqa: F401  (re-exported identity)
    TERMINAL_POLICY,
    AccountingFieldError,
    build_accounting_reconciliation,
    identity_tolerance,
    map_to_canonical,
)

SCHEMA = "commodities_ng1/kernel@1"

#: Stress tier ladder (plan section 5); tier 2.0 PRIMARY.
COST_TIER_LADDER = (1.0, 1.5, 2.0)
PRIMARY_TIER = 2.0

#: Dual-book identities.
BOOKS = ("GROSS", "NET")

#: Instrument drag accruals are tier-independent (instrument fee fact,
#: Q-16) -- recorded as an explicit kernel constant so the property is
#: an auditable decision, not an accident.
DRAG_IS_TIER_INDEPENDENT = True

#: Calendar convention for daily accruals (consistent with the cycle's
#: annualization convention elsewhere; 365.25-day Julian year).
DAYS_PER_YEAR = 365.25


class KernelRefused(Exception):
    """Fail-closed kernel refusal (malformed trade, unknown tier,
    negative cost constant, missing fill)."""


def fill_transaction_cost(notional_usd: float, half_spread_frac: float,
                          tier: float) -> float:
    """Transaction cost of ONE fill: notional x half-spread x tier.

    ``half_spread_frac`` is the per-fill effective half-spread as a
    fraction of price (half of the Corwin-Schultz full spread).  A
    round trip pays the FULL spread across exactly 2 fills.  Charged
    once per fill, never re-scaled after booking.
    """
    if tier not in COST_TIER_LADDER:
        raise KernelRefused(
            f"tier {tier!r} not in the frozen ladder {COST_TIER_LADDER}")
    if not math.isfinite(float(notional_usd)):
        raise KernelRefused("notional must be finite")
    if notional_usd <= 0:
        raise KernelRefused("notional must be positive")
    if half_spread_frac is None or half_spread_frac < 0:
        raise KernelRefused(
            f"half-spread {half_spread_frac!r} invalid "
            "(measured constant required; None is a fail-closed refusal)")
    return float(notional_usd) * float(half_spread_frac) * float(tier)


def drag_accrual(notional_usd: float, annual_drag_rate: float | None,
                 days_held: int) -> float:
    """Instrument drag accrual over a holding period (Q-16).

    ``annual_drag_rate`` is the annualized drag fraction (expense-ratio
    daily drag + measured same-underlying tracking-divergence proxy
    where pairs exist).  ``None`` (no pair / no measured fee fact) is a
    caller-disclosed limitation: the accrual contributes 0.0 and the
    caller must carry the disclosure in the cost contract -- the kernel
    never invents a rate.
    """
    if notional_usd <= 0:
        raise KernelRefused("notional must be positive")
    if int(days_held) < 0:
        raise KernelRefused("days_held must be non-negative")
    if annual_drag_rate is None:
        return 0.0
    rate = float(annual_drag_rate)
    if rate < 0 or rate > 1.0:
        raise KernelRefused(
            f"annual drag rate {rate!r} outside [0, 1]: not a valid "
            "measured/declared instrument drag")
    return (float(notional_usd) * rate * int(days_held)) / DAYS_PER_YEAR


def price_pnl(direction: int, notional_usd: float, entry_price: float,
              exit_price: float) -> float:
    """Frozen PnL identity (no costs)."""
    if direction not in (1, -1):
        raise KernelRefused(f"direction {direction!r} must be +1/-1")
    if entry_price <= 0 or exit_price <= 0:
        raise KernelRefused("prices must be positive")
    return direction * float(notional_usd) * (
        float(exit_price) / float(entry_price) - 1.0)


def trade_costs(trade: dict, cost_constants: dict,
                tiers: tuple = COST_TIER_LADDER) -> dict:
    """Cost events of ONE trade at every tier.

    The trade carries exactly one row per FILL in ``fills``; each fill
    is charged once (the trade record is the audit trail that the
    once-per-fill law holds).  Drag accrues over ``days_held`` and is
    identical across tiers (tier-independent instrument fact).
    """
    notional = float(trade["notional_usd"])
    half = cost_constants.get("half_spread_frac")
    days = int(trade["days_held"])
    n_fills = len(trade.get("fills", ()))
    if n_fills < 1:
        raise KernelRefused(
            f"trade {trade.get('trade_id')!r}: no fill events; refusing "
            "to book a trade without its fills")
    transaction = {
        str(t): fill_transaction_cost(notional, half, t) * n_fills
        for t in tiers
    }
    expense = drag_accrual(notional, cost_constants.get("expense_annual"),
                           days)
    tracking = drag_accrual(
        notional, cost_constants.get("tracking_divergence_annual"), days)
    drag_total = expense + tracking
    return {
        "fills": n_fills,
        "transaction_by_tier": transaction,
        "drag_expense": expense,
        "drag_tracking": tracking,
        "drag_total": drag_total,
        "days_held": days,
    }


def dual_book_ledger(trades: list[dict], costs_by_leg: dict,
                     tiers: tuple = COST_TIER_LADDER) -> dict:
    """Dual-book ledger over a trade population.

    ``trades`` rows: {trade_id, leg, direction, notional_usd,
    entry_price, exit_price, days_held, fills: [..], closed: bool}.
    Open trades are force-closed at their exit mark (which must be the
    last observable bar's price) under the root ``TERMINAL_POLICY``.

    ``costs_by_leg[leg]``: {half_spread_frac, expense_annual,
    tracking_divergence_annual} -- the measured constants from the
    committed cost contract (``half_spread_frac`` is REQUIRED; a leg
    without a measured spread constant refuses to book, fail-closed).

    Reconciliation runs through the ROOT module's
    ``build_accounting_reconciliation``: cost buckets are commissions
    (transaction, once per fill) and slippage (instrument drag
    accrual); funding and rejection costs are 0 by construction here.
    """
    gross_rows, closed_gross, terminal_gross = [], [], []
    comm_by_tier = {str(t): [] for t in tiers}
    slip_by_tier = {str(t): [] for t in tiers}
    net_by_tier = {str(t): [] for t in tiers}
    canonical_rows = []
    for trade in trades:
        leg = trade["leg"]
        consts = costs_by_leg.get(leg)
        if consts is None or consts.get("half_spread_frac") is None:
            raise KernelRefused(
                f"leg {leg!r}: no measured half-spread constant in the "
                "cost contract; booking refused (fail-closed)")
        costs = trade_costs(trade, consts, tiers)
        g = price_pnl(int(trade["direction"]),
                      float(trade["notional_usd"]),
                      float(trade["entry_price"]),
                      float(trade["exit_price"]))
        gross_rows.append(g)
        (closed_gross if trade.get("closed", True) else terminal_gross
         ).append(g)
        for t in tiers:
            transaction = costs["transaction_by_tier"][str(t)]
            net = g - transaction - costs["drag_total"]
            comm_by_tier[str(t)].append(transaction)
            slip_by_tier[str(t)].append(costs["drag_total"])
            net_by_tier[str(t)].append(net)
            if t == PRIMARY_TIER:
                canonical_rows.append({
                    "trade_id": trade.get("trade_id"),
                    "leg": leg,
                    "gross_pnl_usd": g,
                    "canonical_pnl": net,
                })
    return {
        "schema": SCHEMA,
        "terminal_policy": TERMINAL_POLICY,
        "primary_tier": PRIMARY_TIER,
        "trades": len(trades),
        "fills": sum(len(t.get("fills", ())) for t in trades),
        "gross": book_metrics(gross_rows),
        "gross_closed_total": math.fsum(closed_gross),
        "gross_terminal_total": math.fsum(terminal_gross),
        "net": {str(t): book_metrics(net_by_tier[str(t)]) for t in tiers},
        "costs": {
            str(t): {
                "commissions_total": math.fsum(comm_by_tier[str(t)]),
                "slippage_total": math.fsum(slip_by_tier[str(t)]),
            }
            for t in tiers
        },
        "canonical_rows": canonical_rows,
    }


def reconcile_ledger(ledger: dict, tier: float = PRIMARY_TIER) -> dict:
    """Reconcile one ledger through the ROOT kernel's identity.

    Identity (root module): ending - starting == closed_price_pnl +
    terminal_pnl + funding - commissions - slippage - rejection.
    Dual-book equality holds iff ``identity_ok`` AND the net total
    equals gross minus the tier's cost buckets exactly.
    """
    if tier not in COST_TIER_LADDER:
        raise KernelRefused(f"tier {tier!r} not in the frozen ladder")
    costs = ledger["costs"][str(tier)]
    recon = build_accounting_reconciliation(
        starting_equity=0.0,
        ending_equity=ledger["net"][str(tier)]["total"],
        closed_price_pnl=ledger["gross_closed_total"],
        terminal_pnl=ledger["gross_terminal_total"],
        funding_cashflows=0.0,
        commissions=costs["commissions_total"],
        slippage=costs["slippage_total"],
        rejection_costs=0.0,
        scope="commodities_ng1_dual_book_ledger",
        terminal_policy=ledger["terminal_policy"],
    )
    dual_book_equality = (
        abs(ledger["net"][str(tier)]["total"]
            - (ledger["gross"]["total"]
               - costs["commissions_total"]
               - costs["slippage_total"]))
        <= identity_tolerance(0.0, ledger["net"][str(tier)]["total"]))
    return {
        "schema": SCHEMA,
        "via_root_module": "research.accounting."
                           "build_accounting_reconciliation",
        "tier": tier,
        "reconciliation": recon,
        "identity_ok": bool(recon["identity_ok"] and dual_book_equality),
        "dual_book_equality": bool(dual_book_equality),
    }


def book_metrics(pnls: list[float]) -> dict:
    """Count/total of one book (pure function; expectancy is a scored
    quantity and is NOT computed here -- no outcomes in P1)."""
    if not pnls:
        return {"trades": 0, "total": None}
    return {"trades": len(pnls), "total": math.fsum(pnls)}
