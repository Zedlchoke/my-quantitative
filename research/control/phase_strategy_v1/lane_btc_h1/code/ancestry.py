"""Ancestry self-check (plan sec 7): signal-series rho vs named dead shadows.

Rho = Pearson correlation of information content (V2 D2 convention), computed
pre-PnL from SIGNAL series (positions/desired books and shadow signals), never
from returns. Only shadows reconstructible from THIS cell's own price/volume
data are measured; the rest get rho NOT_MEASURED_WITH_REASON plus a
mechanism-class distance argument.

Reading of the bar (recorded explicitly because the plan text is ambiguous):
plan sec13 E3 lists eligibility as `rho vs applicable dead shadows <= 0.20`;
we therefore apply |rho| <= 0.20 => DISTINCT mechanism (eligible) and
|rho| > 0.20 => SAME mechanism (self-veto). The ambiguity is disclosed to A1,
who adjudicates ancestry at integration.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

RHO_BAR = 0.20


def rev24_reversal_shadow(close: np.ndarray, horizon: int = 24) -> np.ndarray:
    """Named shadow: `rev24-style short-horizon reversal per-leg`.
    Reconstruction from the name: fade the 24h (24-bar) return.
    signal = -sign(close_t - close_{t-horizon})."""
    d = np.zeros_like(close)
    d[horizon:] = close[horizon:] - close[:-horizon]
    return -np.sign(d)


def close_displace_fade_shadow(close: np.ndarray, window: int = 24) -> np.ndarray:
    """Named shadow: `close-displace-fade`.
    Reconstruction: fade the displacement of close from its short mean.
    signal = -sign(close_t - SMA24(close)_t)."""
    sma = pd.Series(close).rolling(window).mean().to_numpy()
    return -np.sign(close - sma)


def run_imbalance_shadow(close: np.ndarray, window: int = 24) -> np.ndarray:
    """Named shadow: `run_imbalance`.

    A7-H1 REMEDIATION (2026-09-23): this shadow IS reconstructible from
    closes alone. Construction is the frozen shadow_series formula:
    sign of the 1-bar close return, rolled mean over `window` bars
    (sign(ret1).rolling(win).sum()/win). Window win=24 follows this lane's
    frozen convention for the other shadows (rev24 horizon, close-displace
    window, amihud rolling window are all 24 hourly bars). Estimator is the
    same signal-series Pearson on the common finite grid as every other
    measurement here (information content of signals, NOT returns).
    """
    ret1 = np.diff(close, prepend=np.nan)
    sgn = np.sign(ret1)
    return pd.Series(sgn).rolling(window).sum().to_numpy() / window


def amihud_illiquidity_shadow(close: np.ndarray, quote_volume: np.ndarray,
                              window: int = 24) -> np.ndarray:
    """Named shadow: `amihud-illiquidity proxy`.
    Reconstruction: rolling mean of |r_t| / quote_volume_t, standardized."""
    r = np.zeros_like(close)
    r[1:] = close[1:] / close[:-1] - 1.0
    illiq = np.abs(r) / np.maximum(quote_volume, 1e-12)
    roll = pd.Series(illiq).rolling(window).mean().to_numpy()
    mu = np.nanmean(roll)
    sd = np.nanstd(roll)
    return (roll - mu) / (sd if sd > 0 else 1.0)


def signal_rho(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson correlation on the common finite grid."""
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 3:
        return float("nan")
    x, y = a[m], b[m]
    if np.std(x) == 0 or np.std(y) == 0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def measure(close: np.ndarray, quote_volume: np.ndarray,
            candidate_signals: dict[str, np.ndarray]) -> dict:
    shadows = {
        "rev24_reversal": rev24_reversal_shadow(close),
        "close_displace_fade": close_displace_fade_shadow(close),
        "run_imbalance": run_imbalance_shadow(close),
    }
    amihud = amihud_illiquidity_shadow(close, quote_volume)
    out: dict = {
        "rho_bar": RHO_BAR,
        "per_candidate": {},
        "remediation": {
            "id": "A7-H1",
            "date": "2026-09-23",
            "note": "run_imbalance was previously recorded NOT_MEASURED "
                    "('not reconstructible from 1h OHLCV'); A7 found it "
                    "reconstructible from closes alone. Reconstructed with "
                    "the frozen shadow_series construction "
                    "sign(ret1).rolling(24).sum()/24 (window 24 = this "
                    "lane's convention for all other shadows), measured on "
                    "the identical full-grid signal series and estimator "
                    "(Pearson information-content correlation) as the "
                    "original <=0.082 measurements. OI-level/OI-share, "
                    "generic DVOL and pair-spread shadows remain "
                    "NOT_MEASURED_WITH_REASON (observables absent from the "
                    "cell contract).",
        },
    }
    not_measured = {
        "oi_level_oi_share_stoch": "requires open-interest data absent from "
                                   "the kline manifest; not reconstructible "
                                   "(mechanism class: positioning leverage; "
                                   "candidates carry no positioning input)",
        "generic_dvol_shock": "requires the DVOL index; not reconstructible "
                              "from OHLCV (mechanism class: implied-vol "
                              "shock conditioning; candidates have no "
                              "options-vol input)",
        "pair_spread_trend_composites": "requires a second asset; single-asset "
                                        "cell cannot express a pair spread "
                                        "(mechanism class: cross-instrument "
                                        "relative value)",
    }
    for name, sig in candidate_signals.items():
        rec: dict = {}
        for sname, sh in shadows.items():
            r = signal_rho(sig, sh)
            rec[sname] = {
                "rho": r,
                "measured": True,
                "distinct_within_bar": bool(abs(r) <= RHO_BAR),
            }
        rec["amihud_illiquidity_proxy"] = {
            "rho": signal_rho(sig, amihud),
            "measured": True,
            "distinct_within_bar": bool(abs(signal_rho(sig, amihud)) <= RHO_BAR),
        }
        rec["not_measured"] = not_measured
        rec["self_veto"] = any(
            not rec[k]["distinct_within_bar"]
            for k in ("rev24_reversal", "close_displace_fade",
                      "amihud_illiquidity_proxy", "run_imbalance")
        )
        out["per_candidate"][name] = rec
    return out
