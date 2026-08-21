"""Compare MR baseline vs Wyckoff directional bias (3-fold walk-forward).

Baseline: ``config/research_mean_reversion_eth.yaml`` (gate only).
Directional: ``config/research_mean_reversion_eth_directional.yaml`` (+ phase side bias).

Usage
-----
    python -m research.mr_directional_wf --folds 3
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
from research.breakout_wf import _bars_with_warmup
from research.breakout_wf import _metrics_in_window
from research.optimize import _data_range
from research.optimize import _windows


def _run_variant(
    config_path: str,
    symbol: str,
    windows: list[tuple[str, str]],
    warmup_days: int,
) -> dict:
    settings = load_research_config(config_path)
    catalog = Catalog(settings.data.catalog_path)
    instrument = catalog.instrument(settings.market.instrument_id(symbol))
    all_bars = catalog.bars(settings.market.bar_type(symbol))

    fold_results: list[dict] = []
    for w_idx, (w_start, w_end) in enumerate(windows):
        bars = _bars_with_warmup(all_bars, w_start, w_end, warmup_days)
        bt = dataclasses.replace(settings.backtest, start=None, end=None)
        run = run_backtest_for_symbol(
            settings.market,
            settings.risk,
            settings.strategy,
            bt,
            catalog,
            symbol=symbol,
            strategy_type=settings.strategy_type,
            mean_reversion=settings.mean_reversion,
            regime_switch=None,
            breakout=None,
            trader_id="MRDIR",
            log_level="OFF",
            instrument=instrument,
            bars=bars,
        )
        try:
            pnl, exp, pf, wr, trades = _metrics_in_window(run.engine, w_start, w_end)
        finally:
            run.engine.dispose()

        fold_results.append(
            {
                "window": w_idx,
                "start": w_start,
                "end": w_end,
                "trades": trades,
                "pnl": round(pnl, 4),
                "expectancy": round(exp, 4) if trades else None,
                "profit_factor": round(pf, 4) if trades else None,
                "positive": trades > 0 and exp > 0,
            },
        )

    n_pos = sum(1 for f in fold_results if f["positive"])
    folds = len(fold_results)
    total_trades = sum(f["trades"] for f in fold_results)
    total_pnl = sum(f["pnl"] for f in fold_results)
    traded = [f for f in fold_results if f["trades"] > 0]
    avg_exp = (
        sum(f["expectancy"] * f["trades"] for f in traded) / total_trades
        if total_trades > 0
        else None
    )
    return {
        "config": config_path,
        "directional_bias": settings.mean_reversion.wyckoff_directional_bias,
        "positive_folds": f"{n_pos}/{folds}",
        "total_trades": total_trades,
        "total_pnl": round(total_pnl, 4),
        "weighted_avg_expectancy": round(avg_exp, 4) if avg_exp is not None else None,
        "meets_acceptance": n_pos >= max(2, (folds * 2) // 3) and total_trades > 0 and (avg_exp or 0) > 0,
        "folds": fold_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="MR baseline vs Wyckoff directional WF")
    parser.add_argument("--baseline", default="config/research_mean_reversion_eth.yaml")
    parser.add_argument(
        "--directional",
        default="config/research_mean_reversion_eth_directional.yaml",
    )
    parser.add_argument("--symbol", default="ETHUSDT")
    parser.add_argument("--folds", type=int, default=3)
    parser.add_argument("--output", default="results/optimize/mr_directional_wf3.json")
    args = parser.parse_args()

    settings = load_research_config(args.directional)
    catalog = Catalog(settings.data.catalog_path)
    start, end = _data_range(catalog, args.symbol, settings.market)
    windows = _windows(start, end, args.folds)
    warmup = settings.mean_reversion.history_days

    baseline = _run_variant(args.baseline, args.symbol, windows, warmup)
    directional = _run_variant(args.directional, args.symbol, windows, warmup)

    print(f"MR Wyckoff directional WF | {args.symbol} | {args.folds} folds")
    print("=" * 72)
    for label, result in ("BASELINE (gate only)", baseline), ("DIRECTIONAL (+ phase bias)", directional):
        print(f"\n{label}: {result['config']}")
        for f in result["folds"]:
            exp_s = f"{f['expectancy']:+.3f}" if f["expectancy"] is not None else "n/a"
            flag = "+" if f["positive"] else "-"
            print(
                f"  F{f['window']} {flag} | {str(f['start'])[:10]} -> {str(f['end'])[:10]} | "
                f"trades={f['trades']:3d} exp={exp_s} PnL={f['pnl']:+.2f}",
            )
        avg_s = (
            f"{result['weighted_avg_expectancy']:+.3f}"
            if result["weighted_avg_expectancy"] is not None
            else "n/a"
        )
        status = "PASS" if result["meets_acceptance"] else "FAIL"
        print(
            f"  Total: trades={result['total_trades']} PnL={result['total_pnl']:+.2f} "
            f"avg_exp={avg_s} | {status}",
        )

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps({"baseline": baseline, "directional": directional}, indent=2),
        encoding="utf-8",
    )
    print(f"\nSaved: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
