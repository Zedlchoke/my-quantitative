"""Analyze ETH market regime per walk-forward fold.

Compares fold windows where mean-reversion backtests were strongly positive vs
strongly negative (NOTES.md bước 2) to characterize VHF, ADX, trend drift,
range-filter pass rate, and higher-timeframe trend state.

Usage
-----
    python -m research.regime_analysis
    python -m research.regime_analysis --folds 6 --symbol ETHUSDT
    python -m research.regime_analysis --folds 6 --bad-folds 1,2 --good-folds 0,3,4,5
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass

import pandas as pd
from nautilus_trader.adapters.binance.common.types import BinanceBar
from nautilus_trader.indicators import VerticalHorizontalFilter

from config.settings import load_research_config
from data.catalog import Catalog
from regime import AverageDirectionalIndex
from regime import is_ranging
from research.optimize import _data_range
from research.optimize import _windows


@dataclass(frozen=True)
class FoldMetrics:
    fold: int
    start: str
    end: str
    bars: int
    return_pct: float
    abs_drift_pct: float
    max_drawdown_pct: float
    adx_mean: float
    adx_median: float
    adx_gt_20_pct: float
    adx_gt_25_pct: float
    vhf_mean: float
    vhf_gt_25_pct: float
    vhf_gt_35_pct: float
    range_filter_pct: float
    htf_ema200_slope_pct: float
    htf_trend: str
    autocorr_lag1: float


def _bars_to_df(bars: list[BinanceBar]) -> pd.DataFrame:
    rows = []
    for bar in bars:
        rows.append(
            {
                "ts": pd.Timestamp(bar.ts_event, tz="UTC"),
                "open": bar.open.as_double(),
                "high": bar.high.as_double(),
                "low": bar.low.as_double(),
                "close": bar.close.as_double(),
                "volume": bar.volume.as_double(),
            },
        )
    df = pd.DataFrame(rows).set_index("ts").sort_index()
    return df


def _compute_indicators(df: pd.DataFrame, vhf_period: int, adx_period: int) -> pd.DataFrame:
    out = df.copy()
    adx = AverageDirectionalIndex(adx_period)
    vhf = VerticalHorizontalFilter(vhf_period)
    adx_vals: list[float | None] = []
    vhf_vals: list[float | None] = []
    for _, row in out.iterrows():
        adx.update(row["high"], row["low"], row["close"])
        vhf.update_raw(row["close"])
        adx_vals.append(adx.value if adx.initialized else None)
        vhf_vals.append(vhf.value if vhf.initialized else None)
    out["adx"] = adx_vals
    out["vhf"] = vhf_vals
    return out


def _htf_trend_label(df: pd.DataFrame, ema_period: int = 200) -> tuple[str, float]:
    """Resample 15m → 1h, EMA trend slope over the fold (% change of EMA)."""
    hourly = df["close"].resample("1h").last().dropna()
    if len(hourly) < ema_period + 5:
        return "unknown", 0.0
    ema = hourly.ewm(span=ema_period, adjust=False).mean()
    slope = (ema.iloc[-1] - ema.iloc[max(0, len(ema) - ema_period // 4)]) / ema.iloc[0] * 100
    last_close = hourly.iloc[-1]
    last_ema = ema.iloc[-1]
    if last_close > last_ema * 1.02 and slope > 1.0:
        label = "uptrend"
    elif last_close < last_ema * 0.98 and slope < -1.0:
        label = "downtrend"
    elif abs(slope) < 0.5:
        label = "sideways"
    else:
        label = "mixed"
    return label, float(slope)


def _fold_metrics(
    fold: int,
    df: pd.DataFrame,
    *,
    vhf_max: float,
    adx_max: float,
    volume_max_ratio: float,
    volume_sma_period: int,
) -> FoldMetrics:
    w_start = df.index[0]
    w_end = df.index[-1]
    ret = (df["close"].iloc[-1] / df["close"].iloc[0] - 1) * 100
    abs_drift = abs(ret)
    roll_max = df["close"].cummax()
    dd = ((df["close"] - roll_max) / roll_max * 100).min()

    valid = df.dropna(subset=["adx", "vhf"])
    vol_sma = valid["volume"].rolling(volume_sma_period).mean()
    ranging = valid.apply(
        lambda r: is_ranging(
            vhf=r["vhf"],
            vhf_max=vhf_max,
            adx=r["adx"],
            adx_max=adx_max,
            volume=r["volume"],
            volume_sma=vol_sma.loc[r.name] if r.name in vol_sma.index else 0,
            volume_max_ratio=volume_max_ratio,
        )
        if pd.notna(vol_sma.loc[r.name])
        else False,
        axis=1,
    )
    rets = valid["close"].pct_change().dropna()
    autocorr = float(rets.autocorr(lag=1)) if len(rets) > 2 else 0.0
    htf_label, htf_slope = _htf_trend_label(valid)

    return FoldMetrics(
        fold=fold,
        start=str(w_start.date()),
        end=str(w_end.date()),
        bars=len(df),
        return_pct=round(ret, 2),
        abs_drift_pct=round(abs_drift, 2),
        max_drawdown_pct=round(float(dd), 2),
        adx_mean=round(float(valid["adx"].mean()), 1),
        adx_median=round(float(valid["adx"].median()), 1),
        adx_gt_20_pct=round(float((valid["adx"] > 20).mean() * 100), 1),
        adx_gt_25_pct=round(float((valid["adx"] > 25).mean() * 100), 1),
        vhf_mean=round(float(valid["vhf"].mean()), 3),
        vhf_gt_25_pct=round(float((valid["vhf"] > 0.25).mean() * 100), 1),
        vhf_gt_35_pct=round(float((valid["vhf"] > 0.35).mean() * 100), 1),
        range_filter_pct=round(float(ranging.mean() * 100), 1) if len(ranging) else 0.0,
        htf_ema200_slope_pct=round(htf_slope, 2),
        htf_trend=htf_label,
        autocorr_lag1=round(autocorr, 3),
    )


def _print_fold(m: FoldMetrics, label: str = "") -> None:
    tag = f" [{label}]" if label else ""
    print(
        f"F{m.fold}{tag} {m.start} → {m.end} | "
        f"ret={m.return_pct:+.1f}% dd={m.max_drawdown_pct:.1f}% | "
        f"HTF={m.htf_trend} (slope {m.htf_ema200_slope_pct:+.1f}%) | "
        f"ADX mean={m.adx_mean} >20={m.adx_gt_20_pct:.0f}% | "
        f"VHF mean={m.vhf_mean} >0.25={m.vhf_gt_25_pct:.0f}% | "
        f"range_ok={m.range_filter_pct:.0f}% | autocorr={m.autocorr_lag1:+.2f}",
    )


def analyze(
    config_path: str,
    symbol: str,
    folds: int,
    bad_folds: list[int],
    good_folds: list[int],
) -> list[FoldMetrics]:
    settings = load_research_config(config_path)
    catalog = Catalog(settings.data.catalog_path)
    start, end = _data_range(catalog, symbol, settings.market)
    windows = _windows(start, end, folds)

    bar_type = settings.market.bar_type(symbol)
    all_bars = catalog.bars(bar_type)
    df_all = _bars_to_df(all_bars)

    mr = settings.mean_reversion
    results: list[FoldMetrics] = []

    print(f"ETH regime analysis | {start.date()} → {end.date()} | {folds} folds | bars={len(df_all)}")
    print("=" * 100)

    for i, (w_start, w_end) in enumerate(windows):
        w_start_ts = pd.Timestamp(w_start)
        w_end_ts = pd.Timestamp(w_end)
        df = df_all.loc[w_start_ts:w_end_ts].copy()
        if len(df) < 100:
            continue
        df = _compute_indicators(df, mr.vhf_period, mr.adx_period)
        m = _fold_metrics(
            i,
            df,
            vhf_max=mr.vhf_max,
            adx_max=mr.adx_max,
            volume_max_ratio=mr.volume_max_ratio,
            volume_sma_period=mr.volume_sma_period,
        )
        label = ""
        if i in bad_folds:
            label = "BAD MR"
        elif i in good_folds:
            label = "GOOD MR"
        _print_fold(m, label)
        results.append(m)

    bad = [r for r in results if r.fold in bad_folds]
    good = [r for r in results if r.fold in good_folds]
    if bad and good:
        print("\n--- Aggregate: BAD vs GOOD folds ---")
        for name, group in [("BAD", bad), ("GOOD", good)]:
            print(
                f"{name} (n={len(group)}): "
                f"avg |ret|={sum(r.abs_drift_pct for r in group)/len(group):.1f}% | "
                f"HTF uptrend/downtrend/sideways="
                f"{sum(1 for r in group if r.htf_trend=='uptrend')}/"
                f"{sum(1 for r in group if r.htf_trend=='downtrend')}/"
                f"{sum(1 for r in group if r.htf_trend=='sideways')} | "
                f"ADX mean={sum(r.adx_mean for r in group)/len(group):.1f} | "
                f"range_ok={sum(r.range_filter_pct for r in group)/len(group):.0f}% | "
                f"autocorr={sum(r.autocorr_lag1 for r in group)/len(group):+.2f}",
            )

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="ETH fold regime analysis")
    parser.add_argument("--config", default="config/research_mean_reversion_eth.yaml")
    parser.add_argument("--symbol", default="ETHUSDT")
    parser.add_argument("--folds", type=int, default=6)
    parser.add_argument("--bad-folds", default="1,2", help="Fold indices with bad MR backtest")
    parser.add_argument("--good-folds", default="0,3,4,5", help="Fold indices with good MR backtest")
    args = parser.parse_args()
    bad = [int(x) for x in args.bad_folds.split(",") if x.strip().isdigit()]
    good = [int(x) for x in args.good_folds.split(",") if x.strip().isdigit()]
    analyze(args.config, args.symbol, args.folds, bad, good)
    return 0


if __name__ == "__main__":
    sys.exit(main())
