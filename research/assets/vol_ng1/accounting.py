"""VOL-NG1 P1 dual-book accounting kernel (inherited shape).

Inheritance provenance (plan section 5: "inherited dual-book
accounting kernel with compatibility tests"):

- ``research.assets.forex_ng1.run.accounting`` (ng1 P1 kernel shape,
  FOREX-NG1 I-phase commit family): dual books GROSS = price-only and
  NET(tier) = gross minus costs; ladder {1.0, 1.5, 2.0} with tier 2.0
  PRIMARY; the cost is charged exactly ONCE per FILL and never
  re-scaled after booking; a round trip is 2 fills => 2 charges;
  ``compute_outcomes`` is fail-closed REFUSED unless scored=True AND
  the market channel authority is AUTHORIZED (P1 never scores).
- ``research.accounting`` (the SHARED module at repo root): imported,
  not forked -- the kernel's books are reconciled through
  ``shared.build_accounting_reconciliation`` and any legacy row goes
  through ``shared.map_to_canonical`` (never a silent 0).

VOL-NG1 deltas vs the forex shape: the per-fill cost is the leg's
MEASURED stress half-spread (Q-8, from the tier-2.0 cost contract)
scaled by the tier -- not a flat bps constant; expense drag and the
Q-16 roll/decay path component are carried as explicitly recorded
per-day mechanism lines, never folded silently into fills.

Degenerate compatibility case (hand-computed, tested):
notional 10_000; entry 40, exit 44, long; stress spread 2.0% =>
gross PnL 1_000.00; half-spread 1.0% => 100.00 per fill at tier 1.0;
NET(1.0) = 1_000 - 200 = 800; NET(1.5) = 1_000 - 300 = 700;
NET(2.0) = 1_000 - 400 = 600; dual-book ledger equality: each book's
equity delta equals its own booked flow total and each book satisfies
the shared-module identity.

No proposals, no signals, no scoring, no outcome numbers anywhere:
``compute_outcomes`` REFUSES in this lane (tested).
"""

from __future__ import annotations

import sys

REPO_ROOT = None


def _repo_root() -> str:
    global REPO_ROOT
    if REPO_ROOT is None:
        import os
        REPO_ROOT = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    return REPO_ROOT


if _repo_root() not in sys.path:
    sys.path.insert(0, _repo_root())

from research import accounting as shared            # noqa: E402

SCHEMA = "vol_ng1/accounting@1"

#: Inherited tier ladder (FOREX-NG1 kernel shape): tier 2.0 PRIMARY.
COST_TIER_LADDER = (1.0, 1.5, 2.0)
PRIMARY_TIER = 2.0

#: Fills per round trip (kernel convention: entry + exit).
FILLS_PER_ROUND_TRIP = 2


class AccountingRefused(Exception):
    """Fail-closed accounting refusal."""


def require_tier(tier: float) -> float:
    if tier not in COST_TIER_LADDER:
        raise AccountingRefused(
            f"tier {tier!r} not in the frozen ladder "
            f"{COST_TIER_LADDER}")
    return float(tier)


def stress_half_spread_frac(stress_spread_frac: float) -> float:
    """Half of the leg's measured stress effective spread: the
    per-fill execution friction in fractional notional (a round trip
    crosses the full spread)."""
    s = float(stress_spread_frac)
    if s <= 0:
        raise AccountingRefused("stress spread must be positive")
    if s > 1.0:
        raise AccountingRefused(
            f"stress spread {s!r} > 100%: implausible, refusing")
    return s / 2.0


def per_fill_cost_usd(notional_usd: float, stress_spread_frac: float,
                      tier: float) -> float:
    """Once-per-fill execution cost: notional x measured half-spread
    x tier.  Charged at every fill; never re-scaled after booking."""
    require_tier(tier)
    if notional_usd <= 0:
        raise AccountingRefused("notional must be positive")
    return notional_usd * stress_half_spread_frac(stress_spread_frac) \
        * float(tier)


def price_pnl_usd(direction: int, notional_usd: float, entry_price: float,
                  exit_price: float) -> float:
    """The frozen price PnL identity (no costs; inherited)."""
    if direction not in (-1, 1):
        raise AccountingRefused(
            f"direction {direction!r} must be -1 or +1")
    if entry_price <= 0 or exit_price <= 0:
        raise AccountingRefused("prices must be positive")
    return float(direction) * float(notional_usd) \
        * (float(exit_price) / float(entry_price) - 1.0)


def book_round_trip(*, direction: int, notional_usd: float,
                    entry_price: float, exit_price: float,
                    stress_spread_frac: float,
                    tiers: tuple = COST_TIER_LADDER) -> dict:
    """One round trip across both books: GROSS price PnL plus the
    exactly-once-per-fill charges per tier."""
    gross = price_pnl_usd(direction, notional_usd, entry_price,
                          exit_price)
    fills = {
        str(t): {
            "fills": FILLS_PER_ROUND_TRIP,
            "cost_per_fill_usd": per_fill_cost_usd(
                notional_usd, stress_spread_frac, t),
        }
        for t in tiers
    }
    net = {
        t: gross - b["cost_per_fill_usd"] * b["fills"]
        for t, b in fills.items()
    }
    return {
        "gross_pnl_usd": gross,
        "fills": fills,
        "net_pnl_usd_by_tier": net,
        "notional_usd": float(notional_usd),
        "stress_spread_frac": float(stress_spread_frac),
    }


def dual_book_ledger(round_trips: list[dict],
                     starting_equity: float) -> dict:
    """Walk the GROSS and NET(tier) books over booked round trips and
    reconcile EVERY book through the SHARED module identity::

        ending - starting == closed_price_pnl - slippage

    (commissions/funding/rejections are structurally 0 here; the
    measured execution spread is booked in the slippage field --
    explicit, not folded).  Dual-book equality: each book's equity
    delta equals its own flow total, and NET(tier) deltas equal the
    gross delta minus that tier's cost total.
    """
    start = float(starting_equity)
    if round_trips == []:
        raise AccountingRefused("degenerate ledger: no round trips")
    gross_flows = [rt["gross_pnl_usd"] for rt in round_trips]
    books = {
        "GROSS": {
            "flows": gross_flows,
            "commissions": 0.0,
            "slippage": 0.0,
        },
    }
    tiers = [t for t in COST_TIER_LADDER]
    for t in tiers:
        cost_total = sum(
            rt["fills"][str(t)]["cost_per_fill_usd"]
            * rt["fills"][str(t)]["fills"] for rt in round_trips)
        books[f"NET_{t}"] = {
            "flows": [g - rt["fills"][str(t)]["cost_per_fill_usd"]
                      * rt["fills"][str(t)]["fills"]
                      for g, rt in zip(gross_flows, round_trips)],
            "commissions": 0.0,
            "slippage": cost_total,
        }
    rows = {}
    gross_total = sum(gross_flows)
    for name, b in books.items():
        flow_total = sum(b["flows"])
        ending = start + flow_total
        rec = shared.build_accounting_reconciliation(
            starting_equity=start,
            ending_equity=ending,
            # the identity's price term is the GROSS book: costs are
            # carried by the slippage field, so for NET(tier) books
            #   ending - starting == gross_total - cost_total(tier)
            closed_price_pnl=gross_total,
            terminal_pnl=0.0,
            funding_cashflows=0.0,
            commissions=b["commissions"],
            slippage=b["slippage"],
            rejection_costs=0.0,
            scope="p1_kernel_compat",
        )
        rows[name] = {
            "starting_equity": start,
            "ending_equity": ending,
            "equity_delta": flow_total,
            "gross_total": gross_total,
            "flow_total": flow_total,
            "cost_total": b["slippage"],
            "shared_identity": rec,
            "identity_ok": rec["identity_ok"],
        }
    # dual-book equality laws (fail-closed)
    gross_delta = rows["GROSS"]["equity_delta"]
    for t in tiers:
        name = f"NET_{t}"
        expected = gross_delta - rows[name]["cost_total"]
        if abs(rows[name]["equity_delta"] - expected) > 1e-9:
            raise AccountingRefused(
                f"dual-book inequality at {name}: "
                f"{rows[name]['equity_delta']} != {expected}")
    return {
        "schema": SCHEMA,
        "starting_equity": start,
        "books": rows,
        "gross_book": "GROSS",
        "primary_book": "NET_2.0",
        "dual_book_equality_ok": all(r["identity_ok"]
                                     for r in rows.values()),
    }


def compute_outcomes(round_trips: list[dict], *, scored: bool = False,
                     market_authority: str | None = None) -> dict:
    """Scored outcome computation: REFUSED unless scored=True AND the
    market-channel authority is exactly AUTHORIZED.  The P1 lane
    NEVER calls this with scored=True -- the tested behavior is the
    refusal itself."""
    if not scored:
        raise AccountingRefused(
            "outcome computation refused: scored=False (P1 kernel "
            "lane; no outcomes may be computed here)")
    if market_authority != "AUTHORIZED":
        raise AccountingRefused(
            "outcome computation refused: market channel authority "
            f"{market_authority!r} != AUTHORIZED")
    raise AccountingRefused(
        "scored path not implemented in the P1 kernel lane "
        "(fail-closed: nothing past this point)")


def canonical_flow(row: dict) -> float:
    """Legacy row adapter: explicit, never a silent 0 (shared F01)."""
    return shared.map_to_canonical(row)
