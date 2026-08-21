"""Out-of-sample validation for a fixed parameter set.

Walk-forward folds use all catalog data during optimization. This script holds
out the most recent *N* days and backtests the frozen params on that window only
(NOTES.md §7 criterion 4 — manual OOS check before demo/live).

Usage
-----
    python -m research.oos_validate --config config/research_mean_reversion_eth.yaml
    python -m research.oos_validate --config config/research_mean_reversion_eth.yaml --holdout-days 90
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

import pandas as pd

from backtest.engine import run_backtest_for_symbol
from config.settings import load_research_config
from data.catalog import Catalog
from research.optimize import _data_range
from research.optimize import _extract_metrics

MIN_OOS_TRADES = 10
MIN_OOS_PROFIT_FACTOR = 1.0
MIN_OOS_EXPECTANCY = 0.0


def _holdout_window(
    catalog_end: pd.Timestamp,
    holdout_days: int,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    start = catalog_end - pd.Timedelta(days=holdout_days)
    return start, catalog_end


def validate_oos(
    config_path: str,
    *,
    holdout_days: int = 60,
    min_trades: int = MIN_OOS_TRADES,
    min_pf: float = MIN_OOS_PROFIT_FACTOR,
    min_exp: float = MIN_OOS_EXPECTANCY,
    output: str | None = None,
) -> dict:
    settings = load_research_config(config_path)
    catalog = Catalog(settings.data.catalog_path)
    symbol = settings.market.symbols[0]

    _, catalog_end = _data_range(catalog, symbol, settings.market)
    oos_start, oos_end = _holdout_window(catalog_end, holdout_days)

    bt = dataclasses.replace(
        settings.backtest,
        start=oos_start.isoformat(),
        end=oos_end.isoformat(),
    )

    run = run_backtest_for_symbol(
        settings.market,
        settings.risk,
        settings.strategy,
        bt,
        catalog,
        symbol=symbol,
        strategy_type=settings.strategy_type,
        mean_reversion=settings.mean_reversion,
        regime_switch=settings.regime_switch,
        trader_id="OOS",
        log_level="OFF",
    )
    try:
        pnl, exp, pf, win_rate, trades, sharpe, dd = _extract_metrics(
            run.result,
            settings.market.base_currency,
        )
    finally:
        run.engine.dispose()

    passes = trades >= min_trades and pf >= min_pf and exp > min_exp
    summary = {
        "symbol": symbol,
        "strategy_type": settings.strategy_type,
        "holdout_days": holdout_days,
        "window_start": oos_start.isoformat(),
        "window_end": oos_end.isoformat(),
        "trades": trades,
        "expectancy": round(exp, 4),
        "profit_factor": round(pf, 4),
        "win_rate": round(win_rate, 4),
        "pnl": round(pnl, 4),
        "sharpe": round(sharpe, 4),
        "max_drawdown": round(dd, 4),
        "passes_oos": passes,
        "thresholds": {
            "min_trades": min_trades,
            "min_profit_factor": min_pf,
            "min_expectancy": min_exp,
        },
    }

    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="OOS validation on hold-out window")
    parser.add_argument("--config", default="config/research_mean_reversion_eth.yaml")
    parser.add_argument("--holdout-days", type=int, default=60)
    parser.add_argument("--min-trades", type=int, default=MIN_OOS_TRADES)
    parser.add_argument("--min-pf", type=float, default=MIN_OOS_PROFIT_FACTOR)
    parser.add_argument("--output", default=None, help="Optional JSON output path")
    args = parser.parse_args()

    summary = validate_oos(
        args.config,
        holdout_days=args.holdout_days,
        min_trades=args.min_trades,
        min_pf=args.min_pf,
        output=args.output,
    )

    status = "PASS" if summary["passes_oos"] else "FAIL"
    print(f"OOS validation [{status}] — {summary['symbol']}")
    print(f"  Window : {summary['window_start'][:10]} -> {summary['window_end'][:10]} "
          f"({summary['holdout_days']}d hold-out)")
    print(f"  Trades : {summary['trades']} (min {summary['thresholds']['min_trades']})")
    print(f"  Exp    : {summary['expectancy']:+.4f} (need > {summary['thresholds']['min_expectancy']})")
    print(f"  PF     : {summary['profit_factor']:.4f} (min {summary['thresholds']['min_profit_factor']})")
    print(f"  PnL    : {summary['pnl']:+.2f} USDT")
    print(f"  Win%   : {summary['win_rate']:.1%}")

    if not summary["passes_oos"]:
        print("\nNot ready for demo trading — review params or extend signal-only period.")
        return 1
    print("\nOOS check passed. Proceed: signal-only live -> then enable_trading on Testnet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
