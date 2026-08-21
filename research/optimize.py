"""Parameter grid-search optimizer.

Searches a parameter grid for a strategy across every traded symbol and (optionally)
multiple time windows, and ranks combinations by **expectancy** and **profit
factor** — not by win rate — with a minimum-trade filter to reject noise.

Walk-forward ranking also includes Sharpe, max drawdown, and the NOTES.md §7
acceptance flags. Cell results are cached as JSONL so a run can be resumed.

Usage
-----
    python -m research.optimize --config config/research_mean_reversion.yaml --grid quick
    python -m research.optimize --config config/research.yaml --grid quick --folds 3
    python -m research.optimize --config config/research_mean_reversion.yaml --grid quick --folds 3
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from backtest.engine import run_backtest_for_symbol
from config.settings import load_research_config
from data.catalog import Catalog
from research.acceptance import evaluate_combo_cells
from research.acceptance import valid_ema_combo

# Grid specs: param names map onto the strategy / risk dataclasses.
_MEAN_REVERSION_GRIDS = {
    "quick": {
        "atr_stop_multiple": [1.5, 2.0],
        "take_profit_multiple": [2.0, 2.5],
        "vhf_max": [0.25, 0.35],
        "adx_max": [20.0, 25.0],
        "volume_max_ratio": [1.3, 1.8],
    },
    "full": {
        "atr_stop_multiple": [1.5, 2.0, 2.5],
        "take_profit_multiple": [1.5, 2.0, 2.5],
        "vhf_max": [0.25, 0.35, 0.45],
        "adx_max": [20.0, 25.0, 30.0],
        "volume_max_ratio": [1.3, 1.8],
        "rsi_oversold": [5.0, 10.0],
    },
}

_REGIME_SWITCH_GRIDS = {
    "quick": {
        "trend_stop_multiple": [1.5, 2.0, 3.0],
        "mean_reversion_stop_multiple": [1.5, 2.0],
        "take_profit_multiple": [2.0, 2.5],
        "vhf_max": [0.25, 0.35],
        "adx_max": [20.0, 25.0],
    },
    "full": {
        "trend_stop_multiple": [1.5, 2.0, 3.0],
        "mean_reversion_stop_multiple": [1.5, 2.0],
        "take_profit_multiple": [2.0, 2.5],
        "vhf_max": [0.25, 0.35],
        "adx_max": [20.0, 25.0, 30.0],
        "volume_max_ratio": [1.3, 1.8],
    },
}

_EMA_ATR_GRIDS = {
    "quick": {
        "atr_stop_multiple": [1.5, 2.0, 3.0],
        "fast_ema_period": [10, 20],
        "slow_ema_period": [40, 50],
    },
    "full": {
        "atr_stop_multiple": [1.5, 2.0, 3.0],
        "fast_ema_period": [10, 20, 30],
        "slow_ema_period": [40, 50, 60],
        "trend_ema_period": [150, 200],
    },
}

GRIDS = {
    "mean_reversion": _MEAN_REVERSION_GRIDS,
    "regime_switch": _REGIME_SWITCH_GRIDS,
    "ema_atr": _EMA_ATR_GRIDS,
}

_STRATEGY_PARAM_KEYS = {
    "fast_ema_period",
    "slow_ema_period",
    "trend_ema_period",
    "atr_period",
    "history_days",
}
_RISK_PARAM_KEYS = {"atr_stop_multiple"}


@dataclass
class Cell:
    """One (combo, symbol, window) evaluation result."""

    params: dict
    symbol: str
    window: int
    pnl: float
    expectancy: float
    profit_factor: float
    win_rate: float
    trades: int
    sharpe: float = 0.0
    max_drawdown: float = 0.0


def _grid_values(grid: dict[str, list]) -> list[dict]:
    """Cartesian product of a param grid into a list of dicts."""
    combos: list[dict] = [{}]
    for key, values in grid.items():
        new_combos: list[dict] = []
        for combo in combos:
            for value in values:
                new_combos.append({**combo, key: value})
        combos = new_combos
    return combos


def _metric_by_name(mapping: dict, *names: str, contains: str | None = None) -> float:
    for name in names:
        if name in mapping and mapping[name] is not None:
            try:
                return float(mapping[name])
            except (TypeError, ValueError):
                continue
    if contains:
        needle = contains.lower()
        for key, value in mapping.items():
            if needle in str(key).lower() and value is not None:
                try:
                    return float(value)
                except (TypeError, ValueError):
                    continue
    return 0.0


def _extract_metrics(result, base_currency: str) -> tuple[float, float, float, float, int, float, float]:
    pnl_stats = result.stats_pnls.get(base_currency, {})
    pnl = float(pnl_stats.get("PnL (total)", 0.0) or 0.0)
    expectancy = float(pnl_stats.get("Expectancy", 0.0) or 0.0)
    win_rate = float(pnl_stats.get("Win Rate", 0.0) or 0.0)
    returns = result.stats_returns or {}
    profit_factor = _metric_by_name(returns, "Profit Factor")
    sharpe = _metric_by_name(returns, "Sharpe Ratio (252 days)", contains="sharpe")
    drawdown = _metric_by_name(returns, "Max Drawdown", "Max (Drawdown)", contains="drawdown")
    trades = int(result.total_positions or 0)
    return pnl, expectancy, profit_factor, win_rate, trades, sharpe, drawdown


def _split_ema_params(params: dict) -> tuple[dict, dict]:
    strategy_params = {k: v for k, v in params.items() if k in _STRATEGY_PARAM_KEYS}
    risk_params = {k: v for k, v in params.items() if k in _RISK_PARAM_KEYS}
    return strategy_params, risk_params


def _bars_for_window(
    bars: list,
    w_start: str | None,
    w_end: str | None,
) -> list:
    """Return only bars inside a walk-forward window (major speedup vs full catalog)."""
    if w_start is None or w_end is None:
        return bars
    start_ns = pd.Timestamp(w_start).value
    end_ns = pd.Timestamp(w_end).value
    return [bar for bar in bars if start_ns <= bar.ts_event <= end_ns]


def _preload_symbol_cache(
    catalog: Catalog,
    market,
    symbol: str,
    windows: list[tuple[str | None, str | None]],
) -> tuple:
    instrument_id = market.instrument_id(symbol)
    bar_type = market.bar_type(symbol)
    instrument = catalog.instrument(instrument_id)
    bars = catalog.bars(bar_type)
    window_bars = {
        w_idx: _bars_for_window(bars, w_start, w_end)
        for w_idx, (w_start, w_end) in enumerate(windows)
    }
    return instrument, window_bars


def _windows(start: pd.Timestamp, end: pd.Timestamp, folds: int) -> list[tuple[str | None, str | None]]:
    if folds <= 1:
        return [(None, None)]
    total = end - start
    step = total / folds
    windows = []
    for i in range(folds):
        w_start = start + step * i
        w_end = start + step * (i + 1)
        windows.append((w_start.isoformat(), w_end.isoformat()))
    return windows


def _data_range(catalog: Catalog, symbol: str, market) -> tuple[pd.Timestamp, pd.Timestamp]:
    from nautilus_trader.adapters.binance.common.types import BinanceBar

    bar_type = market.bar_type(symbol)
    first = catalog.raw.query_first_timestamp(BinanceBar, str(bar_type))
    last = catalog.raw.query_last_timestamp(BinanceBar, str(bar_type))
    return first, last


def _combo_key(params: dict) -> tuple:
    return tuple(sorted(params.items()))


def _cell_id(params: dict, symbol: str, window: int) -> str:
    return json.dumps({"params": params, "symbol": symbol, "window": int(window)}, sort_keys=True)


def _load_cached_cells(output_dir: Path) -> list[dict]:
    cells: list[dict] = []
    for path in sorted(output_dir.glob("cells*.jsonl")):
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                cells.append(json.loads(line))
    return cells


def _run_cells(
    config_path: str,
    strategy_type: str,
    combos: list[dict],
    symbols: tuple[str, ...],
    windows: list[tuple[str | None, str | None]],
    base_currency: str,
    cache_path: str,
    done_ids: list[str],
) -> list[dict]:
    """Run all backtests for one process (reuses per-symbol bars)."""
    settings = load_research_config(config_path)
    catalog = Catalog(settings.data.catalog_path)
    skip = set(done_ids)

    cache: dict[str, tuple] = {}
    for symbol in symbols:
        cache[symbol] = _preload_symbol_cache(catalog, settings.market, symbol, windows)

    out: list[dict] = []
    pending_writes = 0
    with open(cache_path, "a", encoding="utf-8") as cache_file:
        for params in combos:
            mean_rev = settings.mean_reversion
            regime_sw = settings.regime_switch
            strategy = settings.strategy
            risk = settings.risk
            if strategy_type == "mean_reversion":
                mean_rev = dataclasses.replace(settings.mean_reversion, **params)
            elif strategy_type == "regime_switch":
                regime_sw = dataclasses.replace(settings.regime_switch, **params)
            elif strategy_type == "ema_atr":
                strategy_params, risk_params = _split_ema_params(params)
                if strategy_params:
                    strategy = dataclasses.replace(settings.strategy, **strategy_params)
                if risk_params:
                    risk = dataclasses.replace(settings.risk, **risk_params)
            else:
                raise ValueError(f"grid not supported for {strategy_type}")

            for symbol in symbols:
                instrument, window_bars = cache[symbol]
                for w_idx, (w_start, w_end) in enumerate(windows):
                    key = _cell_id(params, symbol, w_idx)
                    if key in skip:
                        continue
                    # Bars are pre-sliced per window; no need to filter again in the engine.
                    bt = dataclasses.replace(settings.backtest, start=None, end=None)
                    run = run_backtest_for_symbol(
                        settings.market,
                        risk,
                        strategy,
                        bt,
                        catalog,
                        symbol=symbol,
                        strategy_type=strategy_type,
                        mean_reversion=mean_rev,
                        regime_switch=regime_sw,
                        trader_id="OPT",
                        log_level="OFF",
                        instrument=instrument,
                        bars=window_bars[w_idx],
                    )
                    pnl, exp, pf, wr, trades, sharpe, dd = _extract_metrics(
                        run.result,
                        base_currency,
                    )
                    run.engine.dispose()
                    row = {
                        "params": params,
                        "symbol": symbol,
                        "window": w_idx,
                        "pnl": pnl,
                        "expectancy": exp,
                        "profit_factor": pf,
                        "win_rate": wr,
                        "trades": trades,
                        "sharpe": sharpe,
                        "max_drawdown": dd,
                    }
                    cache_file.write(json.dumps(row, default=str) + "\n")
                    pending_writes += 1
                    if pending_writes >= 20:
                        cache_file.flush()
                        pending_writes = 0
                    out.append(row)
        if pending_writes:
            cache_file.flush()
    return out


def _rank_cells(cells: list[Cell], min_trades: int) -> pd.DataFrame:
    df = pd.DataFrame([dataclasses.asdict(c) for c in cells])
    if df.empty:
        return df
    grouped = df.groupby(df["params"].apply(lambda p: tuple(sorted(p.items()))))

    rows = []
    for key, group in grouped:
        total_trades = int(group["trades"].sum())
        weights = group["trades"].clip(lower=1)
        mean_exp = float((group["expectancy"] * weights).sum() / weights.sum())
        mean_pf = float((group["profit_factor"] * weights).sum() / weights.sum())
        mean_wr = float((group["win_rate"] * weights).sum() / weights.sum())
        mean_sharpe = float((group["sharpe"] * weights).sum() / weights.sum())
        # Most severe drawdown (nautilus typically reports a negative number).
        worst_dd = float(group["max_drawdown"].min())
        total_pnl = float(group["pnl"].sum())
        pos_cells = int((group["expectancy"] > 0).sum())
        n_cells = len(group)
        accepted = evaluate_combo_cells(group)
        row = dict(key)
        row.update(
            {
                "total_trades": total_trades,
                "expectancy": mean_exp,
                "profit_factor": mean_pf,
                "win_rate": mean_wr,
                "sharpe": mean_sharpe,
                "max_drawdown": worst_dd,
                "total_pnl": total_pnl,
                "positive_cells": f"{pos_cells}/{n_cells}",
                "positive_folds": accepted.positive_folds,
                "all_symbols_positive": accepted.all_symbols_positive,
                "pf_majority": accepted.pf_majority,
                "meets_acceptance": accepted.meets_acceptance,
            },
        )
        rows.append(row)

    result = pd.DataFrame(rows)
    result = result.sort_values("expectancy", ascending=False).reset_index(drop=True)
    result["enough_trades"] = result["total_trades"] >= min_trades
    return result


def optimize(
    config_path: str,
    grid: str,
    *,
    folds: int = 1,
    min_trades: int = 20,
    top: int = 15,
    output_dir: str = "./results/optimize",
    workers: int | None = None,
    resume: bool = True,
) -> pd.DataFrame:
    """Run the grid search and return a ranked DataFrame (also saved to disk)."""
    settings = load_research_config(config_path)
    strategy_type = settings.strategy_type
    grid_specs = GRIDS.get(strategy_type)
    if grid_specs is None:
        raise ValueError(f"grid search not implemented for {strategy_type}")
    if grid not in grid_specs:
        raise ValueError(f"unknown grid {grid!r}; expected {sorted(grid_specs)}")

    catalog = Catalog(settings.data.catalog_path)
    combos = [c for c in _grid_values(grid_specs[grid]) if valid_ema_combo(c)]
    base_currency = settings.market.base_currency

    first_sym = settings.market.symbols[0]
    start, end = _data_range(catalog, first_sym, settings.market)
    windows = _windows(start, end, folds)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    cached = _load_cached_cells(out) if resume else []
    done_lookup = {
        _cell_id(row["params"], row["symbol"], int(row["window"])) for row in cached
    }
    expected_cells = len(settings.market.symbols) * len(windows)
    remaining = [
        combo
        for combo in combos
        if sum(
            1
            for symbol in settings.market.symbols
            for w_idx in range(len(windows))
            if _cell_id(combo, symbol, w_idx) in done_lookup
        )
        < expected_cells
    ]

    total_backtests = len(combos) * expected_cells
    print(
        f"Optimizing {strategy_type} [{grid}]: {len(combos)} combos x "
        f"{len(settings.market.symbols)} symbols x {len(windows)} windows = "
        f"{total_backtests} backtests "
        f"({len(cached)} cached, {len(remaining)} combos remaining)",
    )

    n_workers = workers or os.cpu_count() or 1
    n_workers = max(1, min(n_workers, max(len(remaining), 1)))
    chunks = [remaining[i::n_workers] for i in range(n_workers)]
    chunks = [c for c in chunks if c]
    print(f"Running with {max(len(chunks), 1)} worker processes")

    t0 = time.time()
    new_cells: list[dict] = []
    if remaining:
        done_ids = list(done_lookup)
        if len(chunks) == 1:
            new_cells = _run_cells(
                config_path,
                strategy_type,
                chunks[0],
                settings.market.symbols,
                windows,
                base_currency,
                str(out / "cells_w0.jsonl"),
                done_ids,
            )
        else:
            with ProcessPoolExecutor(max_workers=len(chunks)) as pool:
                futures = [
                    pool.submit(
                        _run_cells,
                        config_path,
                        strategy_type,
                        chunk,
                        settings.market.symbols,
                        windows,
                        base_currency,
                        str(out / f"cells_w{i}.jsonl"),
                        done_ids,
                    )
                    for i, chunk in enumerate(chunks)
                ]
                for fut in futures:
                    new_cells.extend(fut.result())

    elapsed = time.time() - t0
    ran = len(new_cells)
    rate = (ran / elapsed) if elapsed > 0 and ran else 0.0
    print(f"New backtests done in {elapsed:.0f}s ({rate:.1f} backtests/s)")

    all_rows = cached + new_cells
    cells = [Cell(**{k: v for k, v in row.items() if k in Cell.__dataclass_fields__}) for row in all_rows]
    result = _rank_cells(cells, min_trades)

    result.to_csv(out / "ranking.csv", index=False)
    with (out / "ranking.json").open("w", encoding="utf-8") as handle:
        json.dump(result.to_dict(orient="records"), handle, indent=2, default=str)

    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Grid-search strategy parameters")
    parser.add_argument("--config", default="config/research_mean_reversion.yaml")
    parser.add_argument("--grid", default="quick", choices=["quick", "full"])
    parser.add_argument("--folds", type=int, default=1, help="walk-forward windows (1 = whole period)")
    parser.add_argument("--min-trades", type=int, default=20)
    parser.add_argument("--top", type=int, default=15)
    parser.add_argument("--output-dir", default="./results/optimize")
    parser.add_argument("--workers", type=int, default=None, help="parallel worker processes")
    parser.add_argument("--no-resume", action="store_true", help="ignore cached cells and rerun")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = optimize(
        args.config,
        args.grid,
        folds=args.folds,
        min_trades=args.min_trades,
        top=args.top,
        output_dir=args.output_dir,
        workers=args.workers,
        resume=not args.no_resume,
    )

    if result.empty:
        print("No optimizer cells produced. Download catalog data first.")
        return 1

    print("\n===== RANKING (by expectancy) =====")
    hide = {"total_pnl", "win_rate"}
    cols = [c for c in result.columns if c not in hide]
    filtered = result[(result["total_trades"] >= args.min_trades)]
    if filtered.empty:
        print(f"(no combo reached min_trades={args.min_trades}; showing unfiltered)")
        filtered = result
    print(filtered[cols].head(args.top).to_string(index=False))

    accepted = result[result["meets_acceptance"] & (result["total_trades"] >= args.min_trades)]
    if accepted.empty:
        print(
            "\nNo combo meets NOTES.md acceptance "
            "(>=2/3 positive folds, all symbols positive, PF>1.1 on a majority of cells). "
            "Keep current defaults; do not promote.",
        )
    else:
        print(
            f"\n{len(accepted)} combo(s) meet acceptance — still do a true OOS window "
            "before changing research.yaml / live.yaml defaults.",
        )
        print(accepted[cols].head(args.top).to_string(index=False))

    print(
        f"\nSaved to {args.output_dir}/ranking.csv + ranking.json "
        f"(min_trades={args.min_trades}; cache=cells*.jsonl)",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
