"""PSV1 lane_btc_h4 — ancestry self-check (plan §7).

Computes signal-series rho (correlation of information content, pre-PnL,
V2 D2 convention) between each proposal's position series and the
price-reconstructible BTC dead shadows from plan §7.2. Shadows requiring
data outside this cell (OI, DVOL, pairs) are recorded NOT_MEASURED_WITH_REASON.
Bar: |rho| <= 0.20 (config.RHO_BAR).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config


def _z(s: pd.Series, win: int) -> pd.Series:
    m = s.rolling(win).mean()
    sd = s.rolling(win).std()
    return (s - m) / sd.replace(0.0, np.nan)


def shadow_series(close: pd.Series, quote_volume: pd.Series) -> dict[str, pd.Series]:
    """Dead-shadow signal series on the H4 clock (information content, not returns).

    Reconstructible from this cell's own price/volume data only.
    """
    ret1 = close.pct_change()
    w = config.SHADOW_WINDOWS

    disp = w["close_displace_fade"]["disp"]
    zw = w["close_displace_fade"]["z"]
    displacement = close / close.shift(disp) - 1.0
    close_displace_fade = -_z(displacement, zw)

    rev24_leg = -(close / close.shift(w["rev24_leg"]["disp"]) - 1.0)

    signed = np.sign(ret1.fillna(0.0))
    win = w["run_imbalance"]["win"]
    run_imbalance = signed.rolling(win).sum() / win

    illiq = ret1.abs() / quote_volume.replace(0.0, np.nan)
    amihud_illiq = _z(illiq, w["amihud_illiq"]["win"])

    return {
        "close_displace_fade": close_displace_fade,
        "rev24_leg": rev24_leg,
        "run_imbalance": run_imbalance,
        "amihud_illiq": amihud_illiq,
    }


def daily_sample(series: pd.Series, bucket_ms: pd.Series) -> pd.Series:
    """Last H4 bucket of each UTC day (hour-20 bucket) sampled signal series."""
    df = pd.DataFrame({"v": series.to_numpy(), "ms": bucket_ms.to_numpy()})
    day = (df["ms"] // 86_400_000).astype("int64")
    idx = df.groupby(day).tail(1).index
    out = df.loc[idx, "v"]
    out.index = df.loc[idx, "ms"].to_numpy()
    return out.sort_index()


def rho_vs_shadows(position_daily: pd.Series, shadows_h4: dict[str, pd.Series],
                   bucket_ms: pd.Series) -> dict:
    """Pearson rho of daily-sampled information series; V2 D2 convention."""
    results: dict[str, dict] = {}
    for name, sh in shadows_h4.items():
        sh_daily = daily_sample(sh, bucket_ms)
        joined = pd.concat([position_daily.rename("cand"), sh_daily.rename("shadow")],
                           axis=1, join="inner").dropna()
        if len(joined) < 100:
            results[name] = {"rho": None, "n": int(len(joined)),
                             "verdict": "NOT_MEASURED_INSUFFICIENT_OVERLAP"}
            continue
        r = float(joined["cand"].corr(joined["shadow"]))
        results[name] = {
            "rho": r, "n": int(len(joined)),
            "abs_rho": abs(r),
            "bar": config.RHO_BAR,
            "verdict": "WITHIN_BAR" if abs(r) <= config.RHO_BAR else "EXCEEDS_BAR_DISCLOSED",
        }
    for name, reason in config.SHADOW_NOT_MEASURED.items():
        results[name] = {"rho": "NOT_MEASURED_WITH_REASON", "reason": reason}
    return results
