"""STOCKS-AMIHUD-V1 evaluation (SCORED MODE ONLY — never in dry-run).

Computes per-fold and aggregate outcomes per evaluation_contract.json:
per-fold $ PnL at AUM_ref base; compounded equity curve for return%/MDD;
annual split marks inside F3 (2021-12-31 close, mark-only); concentration;
SPY-excess; stress tier 2.0; drop-one-ticker / drop-one-year.
"""
from __future__ import annotations

from . import engine as E
from .portfolio import HoldRec


def hold_net(h: HoldRec, stress_mult: float = 1.0) -> float:
    if h.exit is None:
        raise E.FailLoud(f"unexited hold {h.code}")
    gross = h.notional * (h.exit.fill_px / h.entry_px - 1.0)
    # entry_cost/exit_cost are stored at base band; stress multiplies the
    # sum symmetrically (tier 2.0 = all bands x2.0; base = x1.0)
    costs = (h.entry_cost + (h.exit_cost or 0.0)) * stress_mult
    return gross - costs


def fold_summary(holds: list[HoldRec], fold: str,
                 stress_mult: float = 1.0) -> dict:
    hs = [h for h in holds if h.fold == fold and h.exit is not None]
    if not hs:
        raise E.FailLoud(f"fold {fold} has no exited holds")  # class iii
    gross = sum(h.notional * (h.exit.fill_px / h.entry_px - 1.0) for h in hs)
    costs = sum((h.entry_cost + (h.exit_cost or 0.0)) * stress_mult for h in hs)
    net = gross - costs
    wins = [h for h in hs
            if h.notional * (h.exit.fill_px / h.entry_px - 1.0) > 0.0]
    gross_win = sum(h.notional * (h.exit.fill_px / h.entry_px - 1.0) for h in wins)
    gross_loss = gross - gross_win  # <= 0
    return {
        "fold": fold, "n_holds": len(hs),
        "gross_pnl": gross, "costs": costs, "net_pnl": net,
        "return_pct_on_aum_ref": net / E.AUM_REF * 100.0,
        "profit_factor": (gross_win / -gross_loss) if gross_loss < 0 else
                         (float("inf") if gross_win > 0 else E.FailLoud("PF undefined 0/0")),
        "expectancy_per_decision": net / len(hs),
        "n_entries": len(hs),
        "death_exits": sum(1 for h in hs if h.exit.kind == "death"),
        "fold_exits": sum(1 for h in hs if h.exit.kind == "fold"),
    }


def equity_curve(holds: list[HoldRec], sessions: list[str]) -> list[tuple[str, float]]:
    """Compounded curve at fill dates (fold returns compound across folds)."""
    events: list[tuple[str, float]] = []
    for h in holds:
        if h.exit is None:
            raise E.FailLoud("unexited hold in equity curve")
        r = h.weight * (h.exit.fill_px / h.entry_px - 1.0)
        events.append((h.entry_fill_date, -0.0))
        events.append((h.exit.fill_date, r))
    events.sort(key=lambda x: x[0])
    eq, out = 1.0, []
    for d, r in events:
        eq *= (1.0 + r)
        out.append((d, eq))
    return out


def max_drawdown(curve: list[tuple[str, float]]) -> float:
    peak, mdd = 1.0, 0.0
    for _, v in curve:
        peak = max(peak, v)
        mdd = max(mdd, (peak - v) / peak)
    return mdd * 100.0


def concentration(holds: list[HoldRec]) -> dict:
    hs = [h for h in holds if h.exit is not None]
    net = {h.code: 0.0 for h in hs}
    folds = {f: 0.0 for f, _ in E.FOLDS.items()}
    total = 0.0
    for h in hs:
        g = hold_net(h)
        net[h.code] += g
        folds[h.fold] += g
        total += g
    def share(x: float) -> float:
        if total > 0:
            return x / total
        return E.FailLoud("concentration share with non-positive total")
    top_ticker = max(net.items(), key=lambda kv: kv[1]) if net else ("", 0.0)
    sorted_folds = sorted(folds.items(), key=lambda kv: -kv[1])
    return {
        "largest_fold": sorted_folds[0][0],
        "largest_fold_share_pct": share(sorted_folds[0][1]) * 100.0,
        "largest_ticker": top_ticker[0],
        "largest_ticker_share_pct": share(top_ticker[1]) * 100.0,
        "top_decile_tickers_share_pct": None,  # filled by caller if total>0
    }
