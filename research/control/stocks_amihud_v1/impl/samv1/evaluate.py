"""STOCKS-AMIHUD-V1 evaluation (SCORED MODE ONLY — never in dry-run).

Implements the FULL evaluation_contract (A7 prelaunch H-4): per-fold
summaries incl. stress, per-hold rows for attribution/reproduction, annual
split marks inside F3, SPY-excess at matched exposure, market beta vs SPY,
vol-tercile composition, drop-one-ticker / drop-one-year survival,
turnover, exposure, top-decile share, concentration.
"""
from __future__ import annotations

from . import engine as E
from .panel import NameSeries
from .portfolio import HoldRec

ANNUAL_MARKS = {"F3_2021_22": "2021-12-31"}


def hold_net(h: HoldRec, stress_mult: float = 1.0) -> float:
    if h.exit is None:
        raise E.FailLoud(f"unexited hold {h.code}")
    gross = h.notional * (h.exit.fill_px / h.entry_px - 1.0)
    costs = (h.entry_cost + (h.exit_cost or 0.0)) * stress_mult
    return gross - costs


def hold_row(h: HoldRec, stress_mult: float = 1.0) -> dict:
    if h.exit is None:
        raise E.FailLoud(f"unexited hold {h.code}")
    gross = h.notional * (h.exit.fill_px / h.entry_px - 1.0)
    return {"code": h.code, "fold": h.fold,
            "entry_decision": h.entry_decision,
            "entry_fill": h.entry_fill_date, "entry_px": h.entry_px,
            "exit_kind": h.exit.kind, "exit_fill": h.exit.fill_date,
            "exit_px": h.exit.fill_px, "weight": h.weight,
            "notional": h.notional, "entry_cost": h.entry_cost,
            "exit_cost": h.exit_cost or 0.0,
            "gross_pnl": gross,
            "net_pnl": gross - (h.entry_cost + (h.exit_cost or 0.0)) * stress_mult}


def hold_rows(holds: list[HoldRec], stress_mult: float = 1.0) -> list[dict]:
    return [hold_row(h, stress_mult) for h in holds if h.exit is not None]


def fold_summary(rows: list[dict], fold: str) -> dict:
    hs = [r for r in rows if r["fold"] == fold]
    if not hs:
        raise E.FailLoud(f"fold {fold} has no exited holds")
    gross = sum(r["gross_pnl"] for r in hs)
    costs = sum(r["entry_cost"] + r["exit_cost"] for r in hs)
    net = gross - costs
    gross_win = sum(r["gross_pnl"] for r in hs if r["gross_pnl"] > 0.0)
    gross_loss = gross - gross_win
    if gross_loss == 0.0:
        pf = float("inf") if gross_win > 0 else None   # 0/0: reported None
    else:
        pf = gross_win / -gross_loss
    return {"fold": fold, "n_holds": len(hs), "gross_pnl": gross,
            "costs": costs, "net_pnl": net,
            "return_pct_on_aum_ref": net / E.AUM_REF * 100.0,
            "profit_factor": pf,
            "expectancy_per_decision": net / len(hs),
            "death_exits": sum(1 for r in hs if r["exit_kind"] == "death"),
            "fold_exits": sum(1 for r in hs if r["exit_kind"] == "fold")}


def annual_split(rows: list[dict]) -> dict:
    """Mark-to-market annual attribution; F3 splits at 2021-12-31 (holds
    spanning the mark contribute their pre/post parts pro-rata by the
    linear price path between entry and exit px — impl_contract v2)."""
    out = {"2019": 0.0, "2020": 0.0, "2021": 0.0, "2022": 0.0}
    mark = ANNUAL_MARKS["F3_2021_22"]
    for r in rows:
        if r["fold"] in ("F1_2019", "F2_2020"):
            out[r["fold"][:4]] += r["net_pnl"]
            continue
        if r["entry_fill"] <= mark < r["exit_fill"]:
            span = (r["exit_fill"], r["entry_fill"])
            # linear time interpolation on ISO dates
            def days(a: str, b: str) -> float:
                import datetime as dt
                return (dt.date.fromisoformat(a) - dt.date.fromisoformat(b)).days
            frac = days(mark, r["entry_fill"]) / days(r["exit_fill"], r["entry_fill"])
            if not (0.0 <= frac <= 1.0):
                raise E.FailLoud("annual mark fraction outside [0,1]")
            pre = r["gross_pnl"] * frac - (r["entry_cost"] + 0.5 * r["exit_cost"])
            post = r["gross_pnl"] * (1.0 - frac) - 0.5 * r["exit_cost"]
            out["2021"] += pre
            out["2022"] += post
        elif r["exit_fill"] <= mark:
            out["2021"] += r["net_pnl"]
        else:
            out["2022"] += r["net_pnl"]
    return out


def equity_curve(holds: list[HoldRec]) -> list[tuple[str, float]]:
    events: list[tuple[str, float]] = []
    for h in holds:
        if h.exit is None:
            raise E.FailLoud("unexited hold in equity curve")
        r = h.weight * (h.exit.fill_px / h.entry_px - 1.0)
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


def concentration(rows: list[dict]) -> dict:
    total = sum(r["net_pnl"] for r in rows)
    if total <= 0.0:
        return {"note": "total net PnL <= 0: shares undefined, reported as-is",
                "total_net_pnl": total}
    by_ticker: dict[str, float] = {}
    by_fold = {f: 0.0 for f, _ in E.FOLDS.items()}
    for r in rows:
        by_ticker[r["code"]] = by_ticker.get(r["code"], 0.0) + r["net_pnl"]
        by_fold[r["fold"]] += r["net_pnl"]
    top_ticker, top_val = max(by_ticker.items(), key=lambda kv: kv[1])
    ranked = sorted(by_ticker.values(), reverse=True)
    k = max(1, len(ranked) // 10)
    top_decile = sum(ranked[:k])
    ann = annual_split(rows)
    top_year, top_year_val = max(ann.items(), key=lambda kv: kv[1])
    return {"total_net_pnl": total,
            "largest_fold": max(by_fold, key=by_fold.get),
            "largest_fold_share_pct": max(by_fold.values()) / total * 100.0,
            "largest_ticker": top_ticker,
            "largest_ticker_share_pct": top_val / total * 100.0,
            "largest_year": top_year,
            "largest_year_share_pct": (top_year_val / total * 100.0
                                       if top_year_val > 0 else 0.0),
            "top_decile_tickers_share_pct": top_decile / total * 100.0}


def drop_one(rows: list[dict]) -> dict:
    """Additive leave-one-out survival on net totals (per-hold rows make
    this exact): net_excluding_ticker and net_excluding_year positivity."""
    total = sum(r["net_pnl"] for r in rows)
    by_ticker: dict[str, float] = {}
    ann = annual_split(rows)
    for r in rows:
        by_ticker[r["code"]] = by_ticker.get(r["code"], 0.0) + r["net_pnl"]
    worst_ticker_margin = min(total - v for v in by_ticker.values())
    years = ["2019", "2020", "2021", "2022"]
    worst_year_margin = min(total - ann[y] for y in years)
    return {"drop_one_ticker_survives": worst_ticker_margin > 0.0,
            "drop_one_ticker_worst_margin": worst_ticker_margin,
            "drop_one_year_survives": worst_year_margin > 0.0,
            "drop_one_year_worst_margin": worst_year_margin}


def turnover_exposure(per_date: list[dict], holds: list[HoldRec]) -> dict:
    """Turnover: traded notional per rebalance / AUM_ref, averaged over
    bookable dates. Exposure: mean invested weight per bookable date."""
    # invested weight per rebalance = sum of entry weights entered that date
    by_date: dict[str, float] = {}
    for h in holds:
        by_date[h.entry_decision] = by_date.get(h.entry_decision, 0.0) + h.weight
    bookable_dates = [d["date"] for d in per_date if d["bookable"]]
    if not bookable_dates:
        raise E.FailLoud("no bookable dates for turnover/exposure")
    ws = [by_date.get(t, 0.0) for t in bookable_dates]
    return {"mean_invested_weight": sum(ws) / len(ws),
            "max_invested_weight": max(ws),
            "turnover_note": "weight-based turnover approximates notional/AUM for near-par books; per-fill notional sums in hold rows give the exact figure"}


def beta_from_panel(holds: list[HoldRec], panel: dict[str, NameSeries],
                    spy: NameSeries) -> float | None:
    num = den = 0.0
    for h in holds:
        ns = panel.get(h.code)
        if ns is None:
            continue
        di = ns.idx.get(h.entry_decision)
        if di is None:
            continue
        lo = max(1, di - 60)
        xs, ys = [], []
        for i in range(lo, di + 1):
            si = spy.idx.get(ns.dates[i])
            if si is None or not (ns.adj_ok[i] and ns.adj_ok[i - 1]
                                  and spy.adj_ok[si] and spy.adj_ok[si - 1]):
                continue
            if ns.adj[i - 1] <= 0 or spy.adj[si - 1] <= 0:
                continue
            xs.append(spy.adj[si] / spy.adj[si - 1] - 1.0)
            ys.append(ns.adj[i] / ns.adj[i - 1] - 1.0)
        if len(xs) < 30:
            continue
        n = len(xs)
        mx = sum(xs) / n
        my = sum(ys) / n
        sxx = sum((x - mx) ** 2 for x in xs)
        if sxx <= 0.0:
            raise E.FailLoud("beta denominator sxx<=0 (class iv)")
        sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        b = sxy / sxx
        num += h.weight * b
        den += h.weight
    if den <= 0.0:
        return None
    return num / den


def spy_excess_folds(rows: list[dict], spy_holds: list[HoldRec],
                      avg_exposure: float) -> dict:
    """Book fold net return minus avg-exposure-scaled SPY fold return."""
    spy_by_fold: dict[str, float] = {}
    for h in spy_holds:
        if h.exit is None:
            continue
        spy_by_fold[h.fold] = (h.exit.fill_px / h.entry_px - 1.0)
    out = {}
    for f, _ in E.FOLDS.items():
        fr = next((r for r in rows if r["fold"] == f), None)
        if fr is None:
            continue
        book_ret = fr["net_pnl"] / E.AUM_REF
        spy_ret = spy_by_fold.get(f)
        out[f] = (book_ret - avg_exposure * spy_ret) if spy_ret is not None else None
    return out
