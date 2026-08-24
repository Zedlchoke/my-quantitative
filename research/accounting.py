"""Canonical accounting primitives for Sprint V5 (owner A2, PLAN §31.2).

This module is the single source of truth for leg-level PnL field semantics
and for the fold/experiment accounting identity required by Sprint V5:

1. Canonical field unification (finding F01): every leg row emitted by the
   shared-capital engine carries exactly ONE PnL key, ``canonical_pnl``
   (= realized PnL after commissions + slippage + allocated funding).
   Legacy artifacts/rows that only carry ``realized_pnl`` must go through
   :func:`map_to_canonical`, an EXPLICIT adapter that raises
   :class:`AccountingFieldError` when neither field is present. It never
   silently defaults to 0.

2. Terminal policy (finding F04): the locked policy constant
   ``FORCE_LIQUIDATE_AT_LAST_OBSERVABLE_BAR`` mirrors
   ``research.portfolio_engine.TERMINAL_POLICY``. Open legs are force-closed
   at each fold window's last observable 15m close and join the closed-leg
   population, so PF / contribution / PnL share ONE population.

3. Accounting identity: :func:`build_accounting_reconciliation` encodes::

       ending_equity - starting_equity
       = closed_price_pnl
         + terminal_pnl
         + funding_cashflows
         - commissions
         - slippage
         - rejection_costs

   evaluated per fold AND for the whole experiment at tolerance
   ``1e-9`` scaled by the equity magnitudes involved.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

TERMINAL_POLICY = "FORCE_LIQUIDATE_AT_LAST_OBSERVABLE_BAR"

IDENTITY_FORMULA = (
    "ending_equity - starting_equity == closed_price_pnl + terminal_pnl "
    "+ funding_cashflows - commissions - slippage - rejection_costs"
)

IDENTITY_TOL_SCALE = 1e-9


class AccountingFieldError(ValueError):
    """Raised when a PnL row carries neither canonical_pnl nor realized_pnl."""


def map_to_canonical(row: Mapping[str, Any]) -> float:
    """Explicit legacy->canonical PnL adapter (F01).

    Preference order: ``canonical_pnl`` then ``realized_pnl``. Missing or
    null values in BOTH fields raise :class:`AccountingFieldError`; this
    adapter never silently defaults to 0.
    """
    if not isinstance(row, Mapping):
        raise AccountingFieldError(
            f"map_to_canonical expects a mapping row, got {type(row).__name__}"
        )
    canonical = row.get("canonical_pnl")
    if canonical is not None:
        return float(canonical)
    legacy = row.get("realized_pnl")
    if legacy is not None:
        return float(legacy)
    raise AccountingFieldError(
        "row has neither 'canonical_pnl' nor 'realized_pnl'; refusing to "
        f"default to 0 (keys={sorted(row)})"
    )


def identity_tolerance(starting_equity: float, ending_equity: float) -> float:
    """Scaled tolerance: 1e-9 relative to the equity scale, floored at 1e-9."""
    return IDENTITY_TOL_SCALE * max(1.0, abs(float(starting_equity)),
                                    abs(float(ending_equity)))


def build_accounting_reconciliation(
    *,
    starting_equity: float,
    ending_equity: float,
    closed_price_pnl: float,
    terminal_pnl: float,
    funding_cashflows: float,
    commissions: float,
    slippage: float,
    rejection_costs: float,
    scope: str = "experiment",
    fold_id: int | str | None = None,
    terminal_policy: str = TERMINAL_POLICY,
    capital_reset_injection: float = 0.0,
) -> dict:
    """Evaluate the V5 accounting identity for one scope.

    Returns a JSON-safe dict; ``identity_ok`` is True iff the residual
    ``(ending - starting) - rhs`` is within the scaled tolerance.

    ``capital_reset_injection`` is reserved for the LEGACY ``reset_folds``
    diagnostic mode of the portfolio engine: a fold-start 100k restart is an
    explicit capital injection that the identity must account for
    (``rhs += injection``). Continuous-capital runs always pass 0.0; any
    non-zero value is reported verbatim for audit.
    """
    start_e = float(starting_equity)
    end_e = float(ending_equity)
    closed = float(closed_price_pnl)
    terminal = float(terminal_pnl)
    funding = float(funding_cashflows)
    comm = float(commissions)
    slip = float(slippage)
    rej = float(rejection_costs)
    inject = float(capital_reset_injection)

    equity_delta = end_e - start_e
    rhs = closed + terminal + funding - comm - slip - rej + inject
    residual = equity_delta - rhs
    tol = identity_tolerance(start_e, end_e)
    return {
        "identity_formula": IDENTITY_FORMULA,
        "terminal_policy": terminal_policy,
        "scope": scope,
        "fold_id": fold_id,
        "starting_equity": start_e,
        "ending_equity": end_e,
        "equity_delta": equity_delta,
        "closed_price_pnl": closed,
        "terminal_pnl": terminal,
        "funding_cashflows": funding,
        "commissions": comm,
        "slippage": slip,
        "rejection_costs": rejection_costs,
        "capital_reset_injection": inject,
        "rhs_total": rhs,
        "residual": residual,
        "tolerance": tol,
        "identity_ok": bool(abs(residual) <= tol),
        "identity_note": (
            "rhs includes capital_reset_injection "
            "(legacy reset_folds diagnostic mode)"
            if inject
            else ""
        ),
    }


def build_commission_slippage(
    orders: Sequence[Mapping[str, Any]],
) -> dict:
    """Summarise commissions/slippage over executed orders + rejected rows.

    Returns ``{"total_commission", "total_slippage", "rejected_orders"}``
    where ``rejected_orders`` lists every order row carrying a
    ``rejected_reason`` (V5 requires these persisted, not dropped).
    """
    executed = [o for o in orders if o.get("rejected_reason") is None]
    rejected = [dict(o) for o in orders if o.get("rejected_reason") is not None]
    return {
        "total_commission": sum(float(o.get("fee") or 0.0) for o in executed),
        "total_slippage": sum(
            float(o.get("slippage_cost") or 0.0) for o in executed
        ),
        "rejected_orders": rejected,
    }
