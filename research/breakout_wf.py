"""Walk-forward evaluation for breakout markup-only strategy (fixed params).

No grid search — validates whether the hand-crafted breakout leg has any
repeatable edge before considering live integration.

Warmup: each fold loads ``history_days`` of bars *before* the OOS window so
Wyckoff daily classification and Donchian/ADX indicators are ready. Metrics
count only positions **closed** inside the OOS window.

Usage
-----
    python -m research.breakout_wf --folds 3
    python -m research.breakout_wf --folds 3 --output results/optimize/breakout_wf3.json
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
from research.optimize import _windows


def _bars_with_warmup(
    bars: list,
    w_start: str,
    w_end: str,
    warmup_days: int,
) -> list:
    warm_ns = (pd.Timestamp(w_start) - pd.Timedelta(days=warmup_days)).value
    end_ns = pd.Timestamp(w_end).value
    return [bar for bar in bars if warm_ns <= bar.ts_event <= end_ns]


def _parse_pnl(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).split()[0])
    except ValueError:
        return None


def _metrics_in_window(engine, w_start: str, w_end: str) -> tuple[float, float, float, float, int]:
    """Return (total_pnl, expectancy, profit_factor, win_rate, trades) for OOS window."""
    df = engine.trader.generate_positions_report()
    start = pd.Timestamp(w_start)
    end = pd.Timestamp(w_end)
    if start.tzinfo is None:
        start = start.tz_localize("UTC")
    if end.tzinfo is None:
        end = end.tz_localize("UTC")

    pnls: list[float] = []
    for _, row in df.iterrows():
        ts_closed = row.get("ts_closed")
        if ts_closed is None:
            continue
        closed = pd.Timestamp(ts_closed)
        if closed.tzinfo is None:
            closed = closed.tz_localize("UTC")
        if not (start <= closed <= end):
            continue
        pnl = _parse_pnl(row.get("realized_pnl"))
        if pnl is not None:
            pnls.append(pnl)

    trades = len(pnls)
    if trades == 0:
        return 0.0, float("nan"), float("nan"), float("nan"), 0

    total = sum(pnls)
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    gross_win = sum(wins)
    gross_loss = abs(sum(losses))
    pf = gross_win / gross_loss if gross_loss > 0 else float("inf")
    return total, total / trades, pf, len(wins) / trades, trades


def run_walkforward(
    config_path: str,
    symbol: str,
    folds: int,
    min_trades: int,
) -> dict:
    settings = load_research_config(config_path)
    catalog = Catalog(settings.data.catalog_path)
    start, end = _data_range(catalog, symbol, settings.market)
    windows = _windows(start, end, folds)
    instrument = catalog.instrument(settings.market.instrument_id(symbol))
    all_bars = catalog.bars(settings.market.bar_type(symbol))
    warmup_days = settings.breakout.history_days

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
            breakout=settings.breakout,
            mean_reversion=None,
            regime_switch=None,
            trader_id="BKWF",
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
                "warmup_days": warmup_days,
                "bars": len(bars),
                "trades": trades,
                "pnl": round(pnl, 4),
                "expectancy": round(exp, 4) if trades else None,
                "profit_factor": round(pf, 4) if trades else None,
                "win_rate": round(wr, 4) if trades else None,
                "enough_trades": trades >= min_trades,
                "positive": trades > 0 and exp > 0,
            },
        )

    n_pos = sum(1 for f in fold_results if f["positive"])
    n_enough = sum(1 for f in fold_results if f["enough_trades"])
    total_trades = sum(f["trades"] for f in fold_results)
    total_pnl = sum(f["pnl"] for f in fold_results)
    traded = [f for f in fold_results if f["trades"] > 0]
    avg_exp = (
        sum(f["expectancy"] * f["trades"] for f in traded) / total_trades
        if total_trades > 0
        else float("nan")
    )

    summary = {
        "symbol": symbol,
        "strategy": "breakout_markup_only",
        "fold_count": folds,
        "min_trades": min_trades,
        "positive_folds": f"{n_pos}/{folds}",
        "folds_with_enough_trades": f"{n_enough}/{folds}",
        "total_trades": total_trades,
        "total_pnl": round(total_pnl, 4),
        "weighted_avg_expectancy": round(avg_exp, 4) if total_trades else None,
        "meets_acceptance": n_pos >= max(2, (folds * 2) // 3) and total_trades > 0 and avg_exp > 0,
        "fold_details": fold_results,
        "params": dataclasses.asdict(settings.breakout),
    }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Breakout walk-forward (fixed params)")
    parser.add_argument("--config", default="config/research_breakout_eth.yaml")
    parser.add_argument("--symbol", default="ETHUSDT")
    parser.add_argument("--folds", type=int, default=3)
    parser.add_argument("--min-trades", type=int, default=5)
    parser.add_argument("--output", default="results/optimize/breakout_wf3.json")
    args = parser.parse_args()

    summary = run_walkforward(args.config, args.symbol, args.folds, args.min_trades)

    print(f"Breakout WF | {summary['symbol']} | {summary['fold_count']} folds | FIXED params")
    print("=" * 72)
    for f in summary["fold_details"]:
        exp_s = f"{f['expectancy']:+.3f}" if f["expectancy"] is not None else "n/a"
        pf_s = f"{f['profit_factor']:.2f}" if f["profit_factor"] is not None else "n/a"
        flag = "+" if f["positive"] else "-"
        print(
            f"  F{f['window']} {flag} | {str(f['start'])[:10]} -> {str(f['end'])[:10]} | "
            f"trades={f['trades']:3d} exp={exp_s} PF={pf_s} PnL={f['pnl']:+.2f}",
        )
    print("-" * 72)
    avg_s = (
        f"{summary['weighted_avg_expectancy']:+.3f}"
        if summary["weighted_avg_expectancy"] is not None
        else "n/a"
    )
    print(
        f"  Total: trades={summary['total_trades']} PnL={summary['total_pnl']:+.2f} "
        f"avg_exp={avg_s} | positive_folds={summary['positive_folds']}",
    )
    status = "PASS" if summary["meets_acceptance"] else "FAIL"
    print(f"  Acceptance ({status}): need >=2/3 folds positive + avg exp > 0")

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nSaved: {out}")
    return 0 if summary["meets_acceptance"] else 1


if __name__ == "__main__":
    sys.exit(main())
