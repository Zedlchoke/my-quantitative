"""Frozen-parameter transfer test across an altcoin cohort.

This is intentionally not an optimizer.  It asks whether the already selected ETH
directional-MR rules transfer to other symbols without changing any parameters.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd


FROZEN_ETH_DIRECTIONAL_PARAMS = {
    "atr_stop_multiple": 1.5,
    "take_profit_multiple": 2.0,
    "vhf_max": 0.25,
    "adx_max": 20.0,
    "volume_max_ratio": 1.8,
    "htf_trend_filter": True,
    "htf_ema_period": 200,
    "htf_minutes": 60,
    "wyckoff_gate": True,
    "wyckoff_directional_bias": True,
}


def assert_frozen(settings) -> None:
    actual = asdict(settings.mean_reversion)
    drift = {
        key: {"expected": expected, "actual": actual.get(key)}
        for key, expected in FROZEN_ETH_DIRECTIONAL_PARAMS.items()
        if actual.get(key) != expected
    }
    if drift:
        raise ValueError(f"Transfer config changed frozen ETH parameters: {drift}")


def _common_range(catalog, settings) -> tuple[pd.Timestamp, pd.Timestamp]:
    starts: list[pd.Timestamp] = []
    ends: list[pd.Timestamp] = []
    for symbol in settings.market.symbols:
        bars = catalog.bars(settings.market.bar_type(symbol))
        if not bars:
            raise ValueError(f"No catalog bars for {symbol}")
        starts.append(pd.Timestamp(min(bar.ts_event for bar in bars), unit="ns", tz="UTC"))
        ends.append(pd.Timestamp(max(bar.ts_event for bar in bars), unit="ns", tz="UTC"))
    return max(starts), min(ends)


def _windows(start: pd.Timestamp, end: pd.Timestamp, folds: int) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    if folds < 1 or end <= start:
        raise ValueError("Invalid transfer-test interval/folds")
    edges = pd.date_range(start=start, end=end, periods=folds + 1)
    return [(edges[i], edges[i + 1]) for i in range(folds)]


def validate_transfer(config_path: str, *, folds: int, output: str) -> dict:
    from backtest.engine import run_backtest_for_symbol
    from config.settings import load_research_config
    from data.catalog import Catalog
    from research.breakout_wf import _metrics_in_window

    settings = load_research_config(config_path)
    if settings.strategy_type != "mean_reversion":
        raise ValueError("Transfer validator requires strategy_type=mean_reversion")
    assert_frozen(settings)
    catalog = Catalog(settings.data.catalog_path)
    start, end = _common_range(catalog, settings)
    windows = _windows(start, end, folds)
    cells: list[dict] = []

    for symbol in settings.market.symbols:
        instrument = catalog.instrument(settings.market.instrument_id(symbol))
        all_bars = catalog.bars(settings.market.bar_type(symbol))
        for index, (window_start, window_end) in enumerate(windows):
            warmup_start = window_start - pd.Timedelta(days=settings.mean_reversion.history_days)
            bars = [bar for bar in all_bars if warmup_start.value <= bar.ts_event <= window_end.value]
            run = run_backtest_for_symbol(
                settings.market,
                settings.risk,
                settings.strategy,
                settings.backtest,
                catalog,
                symbol=symbol,
                strategy_type=settings.strategy_type,
                mean_reversion=settings.mean_reversion,
                regime_switch=settings.regime_switch,
                breakout=settings.breakout,
                instrument=instrument,
                bars=bars,
                log_level="ERROR",
            )
            try:
                pnl, exp, pf, wr, trades = _metrics_in_window(
                    run.engine,
                    window_start.isoformat(),
                    window_end.isoformat(),
                )
            finally:
                run.engine.dispose()
            cells.append(
                {
                    "symbol": symbol,
                    "fold": index,
                    "start": window_start.isoformat(),
                    "end": window_end.isoformat(),
                    "pnl": pnl,
                    "expectancy": exp,
                    "profit_factor": pf,
                    "win_rate": wr,
                    "trades": trades,
                    "sharpe": None,
                    "max_drawdown": None,
                },
            )

    frame = pd.DataFrame(cells)
    symbols: list[dict] = []
    for symbol, group in frame.groupby("symbol"):
        trades = int(group["trades"].sum())
        weights = group["trades"].clip(lower=1)
        positive = int((group["expectancy"] > 0).sum())
        symbols.append(
            {
                "symbol": symbol,
                "trades": trades,
                "positive_folds": f"{positive}/{folds}",
                "expectancy": float((group["expectancy"] * weights).sum() / weights.sum()),
                "profit_factor": float((group["profit_factor"] * weights).sum() / weights.sum()),
                "pnl": float(group["pnl"].sum()),
                "passes_screen": positive / folds >= 2 / 3 and trades >= 20,
            },
        )

    summary = {
        "config": config_path,
        "frozen_params": FROZEN_ETH_DIRECTIONAL_PARAMS,
        "folds": folds,
        "common_start": start.isoformat(),
        "common_end": end.isoformat(),
        "symbols": symbols,
        "cells": cells,
        "note": "Screening only; final decision requires shared-capital portfolio backtest.",
    }
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
        handle.write("\n")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Frozen ETH-rule transfer test")
    parser.add_argument("--config", default="config/research_altcoin_transfer.yaml")
    parser.add_argument("--folds", type=int, default=6)
    parser.add_argument("--output", default="results/altcoin_transfer/transfer_wf.json")
    args = parser.parse_args()
    summary = validate_transfer(args.config, folds=args.folds, output=args.output)
    for row in summary["symbols"]:
        status = "PASS" if row["passes_screen"] else "FAIL"
        print(
            f"{row['symbol']}: {status} folds={row['positive_folds']} "
            f"exp={row['expectancy']:.4f} PF={row['profit_factor']:.2f} trades={row['trades']}",
        )
    print(f"Saved: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
