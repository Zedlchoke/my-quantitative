"""Walk-forward runner for the frozen independent baseline strategies.

The runner evaluates one strategy at a time, never tunes parameters, and reports
both realized-PnL metrics and post-trade funding-adjusted metrics when bundles are
available.  It is intentionally separate from the production backtest command so
that OOS windows cannot accidentally reuse a portfolio result.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
from pathlib import Path

import pandas as pd

from backtest.engine import run_backtest_for_symbol
from config.settings import load_research_config
from data.catalog import Catalog
from reports.funding import build_funding_audit
from research.breakout_wf import _metrics_in_window


BASELINE_TYPES = {"reclaim_mr", "trend_pullback", "markdown_breakdown"}


def _common_range(catalog: Catalog, settings, symbols: tuple[str, ...]) -> tuple[pd.Timestamp, pd.Timestamp]:
    starts: list[pd.Timestamp] = []
    ends: list[pd.Timestamp] = []
    for symbol in symbols:
        bars = catalog.bars(settings.market.bar_type(symbol))
        if not bars:
            raise ValueError(f"No catalog bars for {symbol}")
        starts.append(pd.Timestamp(min(bar.ts_event for bar in bars), unit="ns", tz="UTC"))
        ends.append(pd.Timestamp(max(bar.ts_event for bar in bars), unit="ns", tz="UTC"))
    return max(starts), min(ends)


def _windows(start: pd.Timestamp, end: pd.Timestamp, folds: int) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    if folds < 1 or end <= start:
        raise ValueError("Invalid interval/folds")
    edges = pd.date_range(start=start, end=end, periods=folds + 1)
    return [(edges[i], edges[i + 1]) for i in range(folds)]


def _settings_for_type(settings, strategy_type: str):
    if strategy_type not in BASELINE_TYPES:
        raise ValueError(f"strategy_type must be one of {sorted(BASELINE_TYPES)}")
    updated = dataclasses.replace(settings, strategy_type=strategy_type)
    updated.validate()
    return updated


def _strategy_kwargs(settings) -> dict[str, object]:
    return {
        "mean_reversion": settings.mean_reversion,
        "regime_switch": settings.regime_switch,
        "breakout": settings.breakout,
        "reclaim_mr": settings.reclaim_mr,
        "trend_pullback": settings.trend_pullback,
        "markdown_breakdown": settings.markdown_breakdown,
    }


def _funding_metrics(engine, funding_data_path: str | None, w_start: pd.Timestamp, w_end: pd.Timestamp) -> tuple[float, float, float, int]:
    if not funding_data_path:
        return 0.0, 0.0, 0.0, 0
    audit = build_funding_audit(engine.trader.generate_positions_report(), funding_data_path)
    adjusted = audit.adjusted_positions
    if adjusted.empty:
        return 0.0, 0.0, 0.0, 0
    pnls: list[float] = []
    funding_net = 0.0
    for _, row in adjusted.iterrows():
        closed = pd.Timestamp(row["ts_closed"])
        if closed.tzinfo is None:
            closed = closed.tz_localize("UTC")
        if w_start <= closed <= w_end:
            pnls.append(float(row["realized_pnl_after_funding"]))
            funding_net += float(row["funding_net"])
    if not pnls:
        return 0.0, 0.0, 0.0, 0
    wins = [pnl for pnl in pnls if pnl > 0]
    losses = [pnl for pnl in pnls if pnl <= 0]
    gross_loss = abs(sum(losses))
    pf = sum(wins) / gross_loss if gross_loss else float("inf")
    return sum(pnls), sum(pnls) / len(pnls), pf, len(pnls)


def _buy_hold_pnl(bars: list, w_start: pd.Timestamp, w_end: pd.Timestamp, notional: float) -> float:
    """Return a simple fixed-notional long benchmark for one OOS window."""
    window = [bar for bar in bars if w_start.value <= bar.ts_event <= w_end.value]
    if len(window) < 2:
        return 0.0
    start = window[0].close.as_double()
    end = window[-1].close.as_double()
    return notional * (end / start - 1.0) if start > 0 else 0.0


def run_walkforward(
    config_path: str,
    strategy_type: str,
    symbols: tuple[str, ...] | None,
    folds: int,
    output: str,
) -> dict[str, object]:
    settings = _settings_for_type(load_research_config(config_path), strategy_type)
    symbols = symbols or settings.market.symbols
    if not symbols:
        raise ValueError("At least one symbol is required")
    settings = dataclasses.replace(settings, market=dataclasses.replace(settings.market, symbols=symbols))
    catalog = Catalog(settings.data.catalog_path)
    start, end = _common_range(catalog, settings, symbols)
    windows = _windows(start, end, folds)
    baseline = getattr(settings, strategy_type)
    warmup_days = baseline.history_days
    cells: list[dict[str, object]] = []

    for symbol in symbols:
        instrument = catalog.instrument(settings.market.instrument_id(symbol))
        all_bars = catalog.bars(settings.market.bar_type(symbol))
        if instrument is None:
            raise ValueError(f"Instrument not found for {symbol}")
        for index, (w_start, w_end) in enumerate(windows):
            warmup_start = w_start - pd.Timedelta(days=warmup_days)
            bars = [bar for bar in all_bars if warmup_start.value <= bar.ts_event <= w_end.value]
            backtest = dataclasses.replace(settings.backtest, start=None, end=None)
            run = run_backtest_for_symbol(
                settings.market,
                settings.risk,
                settings.strategy,
                backtest,
                catalog,
                symbol=symbol,
                strategy_type=strategy_type,
                **_strategy_kwargs(settings),
                trader_id=f"BASELINE-{strategy_type}",
                log_level="OFF",
                instrument=instrument,
                bars=bars,
            )
            try:
                pnl, exp, pf, wr, trades = _metrics_in_window(
                    run.engine,
                    w_start.isoformat(),
                    w_end.isoformat(),
                )
                funding_pnl, funding_exp, funding_pf, funding_trades = _funding_metrics(
                    run.engine,
                    settings.report.funding_data_path,
                    w_start,
                    w_end,
                )
            finally:
                run.engine.dispose()
            buy_hold = _buy_hold_pnl(bars, w_start, w_end, float(settings.risk.max_notional))
            cells.append(
                {
                    "symbol": symbol,
                    "fold": index,
                    "start": w_start.isoformat(),
                    "end": w_end.isoformat(),
                    "bars": len(bars),
                    "trades": trades,
                    "pnl": round(pnl, 6),
                    "expectancy": round(exp, 6) if trades else None,
                    "profit_factor": round(pf, 6) if trades else None,
                    "win_rate": round(wr, 6) if trades else None,
                    "funding_trades": funding_trades,
                    "pnl_after_funding": round(funding_pnl, 6),
                    "buy_hold_pnl_at_max_notional": round(buy_hold, 6),
                    "flat_pnl": 0.0,
                    "expectancy_after_funding": round(funding_exp, 6) if funding_trades else None,
                    "profit_factor_after_funding": round(funding_pf, 6) if funding_trades else None,
                    "positive": trades > 0 and exp > 0,
                    "positive_after_funding": funding_trades > 0 and funding_exp > 0,
                },
            )

    frame = pd.DataFrame(cells)
    symbols_summary: list[dict[str, object]] = []
    for symbol, group in frame.groupby("symbol", sort=True):
        traded = group[group["trades"] > 0]
        after = group[group["funding_trades"] > 0]
        total_trades = int(group["trades"].sum())
        total_after = int(group["funding_trades"].sum())
        avg_exp = float((traded["expectancy"] * traded["trades"]).sum() / total_trades) if total_trades else 0.0
        avg_after = float((after["expectancy_after_funding"] * after["funding_trades"]).sum() / total_after) if total_after else avg_exp
        positive = int(group["positive"].sum())
        positive_after = int(group["positive_after_funding"].sum()) if total_after else positive
        symbols_summary.append(
            {
                "symbol": symbol,
                "trades": total_trades,
                "positive_folds": f"{positive}/{folds}",
                "positive_after_funding": f"{positive_after}/{folds}",
                "expectancy": round(avg_exp, 6),
                "expectancy_after_funding": round(avg_after, 6),
                "pnl": round(float(group["pnl"].sum()), 6),
                "pnl_after_funding": round(float(group["pnl_after_funding"].sum()), 6),
                "buy_hold_pnl_at_max_notional": round(float(group["buy_hold_pnl_at_max_notional"].sum()), 6),
                "passes_screen": positive_after / folds >= 2 / 3 and avg_after > 0 and total_after >= 20,
            },
        )

    summary = {
        "config": config_path,
        "strategy_type": strategy_type,
        "symbols": list(symbols),
        "folds": folds,
        "common_start": start.isoformat(),
        "common_end": end.isoformat(),
        "baseline_params": dataclasses.asdict(baseline),
        "symbol_summary": symbols_summary,
        "cells": cells,
        "note": "Research screening only; no parameter tuning or promotion.",
    }
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Frozen baseline strategy walk-forward")
    parser.add_argument("--config", default="config/research_baseline_eth.yaml")
    parser.add_argument("--strategy-type", choices=sorted(BASELINE_TYPES))
    parser.add_argument("--symbols", nargs="+")
    parser.add_argument("--folds", type=int, default=3)
    parser.add_argument("--output", default="results/baselines/wf.json")
    args = parser.parse_args()
    settings = load_research_config(args.config)
    strategy_type = args.strategy_type or settings.strategy_type
    result = run_walkforward(
        args.config,
        strategy_type,
        tuple(args.symbols) if args.symbols else None,
        args.folds,
        args.output,
    )
    for row in result["symbol_summary"]:
        status = "PASS" if row["passes_screen"] else "FAIL"
        print(
            f"{row['symbol']}: {status} | folds={row['positive_after_funding']} "
            f"exp={row['expectancy_after_funding']:+.4f} "
            f"PnL={row['pnl_after_funding']:+.2f} trades={row['trades']}",
        )
    print(f"Saved: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
