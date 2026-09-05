"""Compare EMA-ATR long-only vs mean-reversion by Wyckoff phase (markup focus).

Descriptive study — same fixed Wyckoff labels, no parameter optimization.
Attributes closed trades to phase at entry on full 2-year ETH backtest.

Usage
-----
    python -m research.wyckoff_markup_compare
"""

from __future__ import annotations

import argparse
import dataclasses
import sys

import pandas as pd
from nautilus_trader.adapters.binance.common.types import BinanceBar

from backtest.engine import run_backtest_for_symbol
from config.settings import load_research_config
from data.catalog import Catalog
from regime_wyckoff import WyckoffPhase
from research.optimize import _data_range
from research.optimize import _extract_metrics
from research.wyckoff_analysis import _bars_to_daily_df
from research.wyckoff_analysis import label_daily_phases


def _phase_at_timestamp(labeled: pd.DataFrame, ts: pd.Timestamp) -> str:
    day = ts.normalize()
    if day in labeled.index:
        val = labeled.loc[day, "phase"]
        if isinstance(val, pd.Series):
            val = val.iloc[-1]
        return val if val else WyckoffPhase.TRANSITION.value
    prior = labeled.index[labeled.index <= day]
    if len(prior) == 0:
        return WyckoffPhase.TRANSITION.value
    val = labeled.loc[prior[-1], "phase"]
    if isinstance(val, pd.Series):
        val = val.iloc[-1]
    return val if val else WyckoffPhase.TRANSITION.value


def _parse_pnl(value) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).split()[0])
    except ValueError:
        return None


def _run_and_attribute(
    *,
    settings,
    catalog: Catalog,
    symbol: str,
    strategy_type: str,
    mean_reversion,
    labeled: pd.DataFrame,
) -> tuple[dict, dict]:
    run = run_backtest_for_symbol(
        settings.market,
        settings.risk,
        settings.strategy,
        settings.backtest,
        catalog,
        symbol=symbol,
        strategy_type=strategy_type,
        mean_reversion=mean_reversion,
        regime_switch=settings.regime_switch,
        trader_id="CMP",
        log_level="OFF",
    )
    try:
        pnl, exp, pf, wr, trades, _, _ = _extract_metrics(
            run.result,
            settings.market.base_currency,
        )
        overall = {
            "trades": trades,
            "pnl": pnl,
            "expectancy": exp,
            "profit_factor": pf,
            "win_rate": wr,
        }
        by_phase: dict[str, list[float]] = {p.value: [] for p in WyckoffPhase}
        positions_df = run.engine.trader.generate_positions_report()
        for _, row in positions_df.iterrows():
            ts_opened = row.get("ts_opened")
            pnl_val = _parse_pnl(row.get("realized_pnl"))
            if ts_opened is None or pnl_val is None:
                continue
            opened = pd.Timestamp(ts_opened)
            if opened.tzinfo is None:
                opened = opened.tz_localize("UTC")
            phase = _phase_at_timestamp(labeled, opened)
            by_phase.setdefault(phase, []).append(pnl_val)
        return overall, by_phase
    finally:
        run.engine.dispose()


def _phase_stats(pnls: list[float]) -> dict:
    if not pnls:
        return {"trades": 0, "pnl": 0.0, "expectancy": 0.0, "win_rate": 0.0}
    wins = sum(1 for p in pnls if p > 0)
    return {
        "trades": len(pnls),
        "pnl": sum(pnls),
        "expectancy": sum(pnls) / len(pnls),
        "win_rate": wins / len(pnls),
    }


def _print_row(name: str, stats: dict) -> None:
    print(
        f"  {name:16s} trades={stats['trades']:3d} "
        f"PnL={stats['pnl']:+8.2f} exp={stats['expectancy']:+.3f} "
        f"WR={stats['win_rate']:.0%}",
    )


def compare(config_mr: str, config_ema: str, symbol: str) -> None:
    mr_settings = load_research_config(config_mr)
    ema_settings = load_research_config(config_ema)
    catalog = Catalog(mr_settings.data.catalog_path)
    start, end = _data_range(catalog, symbol, mr_settings.market)
    bars = catalog.bars(mr_settings.market.bar_type(symbol))
    daily = _bars_to_daily_df(bars)
    labeled = label_daily_phases(daily)

    ema_risk = dataclasses.replace(
        mr_settings.risk,
        allow_short=False,
        atr_stop_multiple=ema_settings.risk.atr_stop_multiple,
    )
    ema_strategy = ema_settings.strategy

    print(f"Wyckoff strategy compare | {symbol} | {start.date()} → {end.date()}")
    print("EMA = long-only (allow_short=false) | MR = validated ETH MR config")
    print("=" * 72)

    mr_overall, mr_by_phase = _run_and_attribute(
        settings=mr_settings,
        catalog=catalog,
        symbol=symbol,
        strategy_type="mean_reversion",
        mean_reversion=mr_settings.mean_reversion,
        labeled=labeled,
    )
    ema_overall, ema_by_phase = _run_and_attribute(
        settings=dataclasses.replace(
            mr_settings,
            strategy=ema_strategy,
            strategy_type="ema_atr",
            risk=ema_risk,
        ),
        catalog=catalog,
        symbol=symbol,
        strategy_type="ema_atr",
        mean_reversion=None,
        labeled=labeled,
    )

    print("\nFull sample (2 years):")
    _print_row("MR", mr_overall)
    _print_row("EMA long-only", ema_overall)

    focus_phases = [
        WyckoffPhase.MARKUP,
        WyckoffPhase.MARKDOWN,
        WyckoffPhase.TRANSITION,
        WyckoffPhase.ACCUMULATION,
    ]
    print("\nBy Wyckoff phase at entry (descriptive):")
    print(f"  {'Phase':16s} {'MR':^32s} {'EMA long':^32s}")
    for phase in focus_phases:
        mr_s = _phase_stats(mr_by_phase.get(phase.value, []))
        ema_s = _phase_stats(ema_by_phase.get(phase.value, []))
        print(f"\n  {phase.value}:")
        _print_row("MR", mr_s)
        _print_row("EMA long-only", ema_s)
        if mr_s["trades"] and ema_s["trades"]:
            delta = ema_s["pnl"] - mr_s["pnl"]
            print(f"  {'':16s} EMA vs MR PnL delta: {delta:+.2f} USDT")

    markup_mr = _phase_stats(mr_by_phase.get(WyckoffPhase.MARKUP.value, []))
    markup_ema = _phase_stats(ema_by_phase.get(WyckoffPhase.MARKUP.value, []))
    print("\n" + "=" * 72)
    print("MARKUP conclusion (fixed rules, not optimized):")
    if markup_ema["trades"] == 0:
        print("  EMA long: no trades opened during markup days.")
    elif markup_ema["pnl"] > markup_mr["pnl"]:
        print(
            f"  EMA long beats MR on markup entries "
            f"({markup_ema['pnl']:+.2f} vs {markup_mr['pnl']:+.2f} USDT, "
            f"n={markup_ema['trades']} vs {markup_mr['trades']}).",
        )
        print("  → Wyckoff policy: use EMA long in markup, MR elsewhere.")
    else:
        print(
            f"  MR still >= EMA on markup ({markup_mr['pnl']:+.2f} vs "
            f"{markup_ema['pnl']:+.2f}), but sample n={markup_mr['trades']}/{markup_ema['trades']}.",
        )
        print("  → Need more markup days / paper test before switching leg.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare EMA vs MR by Wyckoff phase")
    parser.add_argument("--config-mr", default="config/research_mean_reversion_eth.yaml")
    parser.add_argument("--config-ema", default="config/research.yaml")
    parser.add_argument("--symbol", default="ETHUSDT")
    args = parser.parse_args()
    compare(args.config_mr, args.config_ema, args.symbol)
    return 0


if __name__ == "__main__":
    sys.exit(main())
