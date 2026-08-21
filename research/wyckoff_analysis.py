"""Wyckoff phase analysis for ETH — descriptive, fixed-threshold regime study.

Labels each day with accumulation / markup / distribution / markdown using
``regime_wyckoff`` (thresholds NOT tuned on ETH). Reports:

- Time in each phase per calendar year (stability check)
- ETH buy-and-hold return per phase
- Mean-reversion backtest PnL attributed to phase at **entry** (descriptive only)
- Year-split validation: same rules on 2024–2025 vs 2025–2026

Usage
-----
    python -m research.wyckoff_analysis
    python -m research.wyckoff_analysis --symbol ETHUSDT
"""

from __future__ import annotations

import argparse
import dataclasses
import sys
from collections import Counter

import pandas as pd
from nautilus_trader.adapters.binance.common.types import BinanceBar

from backtest.engine import run_backtest_for_symbol
from config.settings import load_research_config
from data.catalog import Catalog
from regime_wyckoff import DEFAULT_POLICIES
from regime_wyckoff import WyckoffConfig
from regime_wyckoff import WyckoffPhase
from regime_wyckoff import classify_wyckoff_row
from research.optimize import _data_range
from research.optimize import _extract_metrics


def _bars_to_daily_df(bars: list[BinanceBar]) -> pd.DataFrame:
    rows = [
        {
            "ts": pd.Timestamp(b.ts_event, tz="UTC"),
            "open": b.open.as_double(),
            "high": b.high.as_double(),
            "low": b.low.as_double(),
            "close": b.close.as_double(),
            "volume": b.volume.as_double(),
        }
        for b in bars
    ]
    intraday = pd.DataFrame(rows).set_index("ts").sort_index()
    daily = intraday.resample("1D").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"},
    ).dropna()
    return daily


def _wilder_adx(daily: pd.DataFrame, period: int = 14) -> pd.Series:
    high = daily["high"].astype(float)
    low = daily["low"].astype(float)
    close = daily["close"].astype(float)
    up = high.diff()
    down = -low.diff()
    plus_dm = up.where((up > down) & (up > 0), 0.0)
    minus_dm = down.where((down > up) & (down > 0), 0.0)
    tr = pd.concat(
        [high - low, (high - close.shift()).abs(), (low - close.shift()).abs()],
        axis=1,
    ).max(axis=1)
    atr = tr.ewm(alpha=1 / period, adjust=False).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1 / period, adjust=False).mean() / atr.replace(0, pd.NA)
    minus_di = 100 * minus_dm.ewm(alpha=1 / period, adjust=False).mean() / atr.replace(0, pd.NA)
    denom = plus_di + minus_di
    dx = (100 * (plus_di - minus_di).abs() / denom).where(denom > 0)
    return dx.astype(float).ewm(alpha=1 / period, adjust=False).mean()


def label_daily_phases(daily: pd.DataFrame, cfg: WyckoffConfig | None = None) -> pd.DataFrame:
    """Return daily DataFrame with phase labels and features."""
    c = cfg or WyckoffConfig()
    out = daily.copy()
    out["ema_fast"] = out["close"].ewm(span=c.ema_fast, adjust=False).mean()
    out["ema_slow"] = out["close"].ewm(span=c.ema_slow, adjust=False).mean()
    out["return_pct"] = out["close"].pct_change(c.return_lookback_days) * 100
    roll_low = out["low"].rolling(c.range_lookback_days).min()
    roll_high = out["high"].rolling(c.range_lookback_days).max()
    span = (roll_high - roll_low).replace(0, pd.NA)
    out["range_position"] = (out["close"] - roll_low) / span
    out["adx"] = _wilder_adx(out, c.adx_period)
    out["daily_return_pct"] = out["close"].pct_change() * 100

    phases: list[str | None] = []
    for _, row in out.iterrows():
        if pd.isna(row["return_pct"]) or pd.isna(row["range_position"]) or pd.isna(row["adx"]):
            phases.append(None)
            continue
        phase = classify_wyckoff_row(
            close=float(row["close"]),
            ema_fast=float(row["ema_fast"]),
            ema_slow=float(row["ema_slow"]),
            return_pct=float(row["return_pct"]),
            range_position=float(row["range_position"]),
            adx=float(row["adx"]),
            cfg=c,
        )
        phases.append(phase.value)
    out["phase"] = phases
    return out


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


def _summarize_phases(labeled: pd.DataFrame, title: str) -> None:
    valid = labeled.dropna(subset=["phase"])
    if valid.empty:
        print(f"{title}: no labeled days")
        return

    print(f"\n{'=' * 72}")
    print(title)
    print(f"Days labeled: {len(valid)} | {valid.index.min().date()} → {valid.index.max().date()}")

    counts = Counter(valid["phase"])
    total = len(valid)
    print("\nTime in phase:")
    for phase in WyckoffPhase:
        n = counts.get(phase.value, 0)
        print(f"  {phase.value:14s} {n:4d} days ({100 * n / total:5.1f}%)")

    print("\nETH daily return by phase (descriptive):")
    for phase in WyckoffPhase:
        sub = valid[valid["phase"] == phase.value]
        if sub.empty:
            continue
        print(
            f"  {phase.value:14s} avg daily ret={sub['daily_return_pct'].mean():+.3f}% "
            f"| vol={sub['daily_return_pct'].std():.2f}% | n={len(sub)}",
        )

    print("\nPolicy (hand-crafted, not optimized):")
    for phase in WyckoffPhase:
        p = DEFAULT_POLICIES[phase]
        print(f"  {phase.value:14s} → {p.strategy} @ {p.risk_pct}% | {p.notes}")


def _year_split_report(labeled: pd.DataFrame) -> None:
    valid = labeled.dropna(subset=["phase"]).copy()
    valid["year"] = valid.index.year
    print(f"\n{'=' * 72}")
    print("Year-split stability (same fixed rules each year — overfit check)")
    for year, group in valid.groupby("year"):
        counts = Counter(group["phase"])
        total = len(group)
        parts = ", ".join(
            f"{ph.value}={100 * counts.get(ph.value, 0) / total:.0f}%"
            for ph in WyckoffPhase
        )
        print(f"  {year}: {total} days | {parts}")


def _mr_by_phase(config_path: str, labeled: pd.DataFrame, symbol: str) -> None:
    """Attribute full-period MR backtest trades to Wyckoff phase at entry."""
    settings = load_research_config(config_path)
    catalog = Catalog(settings.data.catalog_path)
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
        trader_id="WYCKOFF",
        log_level="OFF",
    )
    try:
        engine = run.engine
        positions_df = engine.trader.generate_positions_report()
        phase_pnls: dict[str, list[float]] = {p.value: [] for p in WyckoffPhase}

        for _, row in positions_df.iterrows():
            ts_opened = row.get("ts_opened")
            pnl_raw = row.get("realized_pnl")
            if ts_opened is None or pnl_raw is None:
                continue
            opened = pd.Timestamp(ts_opened)
            if opened.tzinfo is None:
                opened = opened.tz_localize("UTC")
            phase = _phase_at_timestamp(labeled, opened)
            pnl_str = str(pnl_raw).split()[0]
            try:
                pnl = float(pnl_str)
            except ValueError:
                continue
            phase_pnls.setdefault(phase, []).append(pnl)

        print(f"\n{'=' * 72}")
        print("Mean-reversion PnL by Wyckoff phase at entry (descriptive, not optimized)")
        print(f"Total closed positions: {sum(len(v) for v in phase_pnls.values())}")
        for phase in WyckoffPhase:
            pnls = phase_pnls.get(phase.value, [])
            if not pnls:
                print(f"  {phase.value:14s} no trades")
                continue
            wins = sum(1 for p in pnls if p > 0)
            print(
                f"  {phase.value:14s} n={len(pnls):3d} "
                f"total={sum(pnls):+.2f} exp={sum(pnls)/len(pnls):+.3f} "
                f"win={100*wins/len(pnls):.0f}%",
            )

        pnl, exp, pf, _, trades, _, _ = _extract_metrics(run.result, settings.market.base_currency)
        print(f"\n  Full backtest: trades={trades} exp={exp:+.3f} PF={pf:.2f} PnL={pnl:+.2f}")
    finally:
        run.engine.dispose()


def _transition_matrix(labeled: pd.DataFrame) -> None:
    valid = labeled.dropna(subset=["phase"]).copy()
    valid["prev_phase"] = valid["phase"].shift(1)
    pairs = valid.dropna(subset=["prev_phase"])
    print(f"\n{'=' * 72}")
    print("Phase transition counts (daily, descriptive)")
    pivot = pd.crosstab(pairs["prev_phase"], pairs["phase"], normalize="index") * 100
    print(pivot.round(0).astype(int).to_string())


def analyze(config_path: str, symbol: str) -> None:
    settings = load_research_config(config_path)
    catalog = Catalog(settings.data.catalog_path)
    start, end = _data_range(catalog, symbol, settings.market)
    bars = catalog.bars(settings.market.bar_type(symbol))
    daily = _bars_to_daily_df(bars)
    labeled = label_daily_phases(daily)

    print(f"Wyckoff analysis | {symbol} | {start.date()} → {end.date()}")
    print("Thresholds: FIXED (WyckoffConfig defaults — not tuned on ETH)")

    _summarize_phases(labeled, "Full sample")
    _year_split_report(labeled)
    _transition_matrix(labeled)
    _mr_by_phase(config_path, labeled, symbol)


def main() -> int:
    parser = argparse.ArgumentParser(description="Wyckoff phase analysis")
    parser.add_argument("--config", default="config/research_mean_reversion_eth.yaml")
    parser.add_argument("--symbol", default="ETHUSDT")
    args = parser.parse_args()
    analyze(args.config, args.symbol)
    return 0


if __name__ == "__main__":
    sys.exit(main())
