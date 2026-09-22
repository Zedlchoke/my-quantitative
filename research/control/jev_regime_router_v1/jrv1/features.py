"""Causal regime-clock features f01..f17 per feature_contract.json.

Laws implemented here (golden-tested):
- warmup = 192 regime bars; states are only built for t >= warmup.
- strictly trailing windows; no centered windows; no whole-sample statistics;
  rv_pctile ranks against its own trailing 168 PAST values (exclusive).
- f16 clv_24 is fail-closed: zero-range bars are dropped from the mean; if
  all 24 are zero-range the feature is NaN -> state LOCAL_INVALID, never sent.
- state payload = {feature_vector: [f01..f16], prior_regime: label|null};
  state_id = sha256(asset_salt||bar_close_ns)[:16]; carries no calendar.
"""

from __future__ import annotations

import numpy as np

from . import indicators as ind
from .data import Bars
from .freezes import Freezes

WARMUP_REGIME_BARS = 192
RV_WINDOW = 24
RANK_WINDOW = 168
DD_WINDOW = 168
RANGE_WINDOW = 24
VOLZ_WINDOW = 168
CLV_WINDOW = 24

FEATURE_ORDER = (
    "r1",
    "r4",
    "r12",
    "r24",
    "r72",
    "ema_slope_fast",
    "ema_slope_slow",
    "dist_ema",
    "adx14",
    "atr_pct",
    "rv_pctile",
    "dd_168",
    "dist_low",
    "range_pos",
    "vol_z",
    "clv_24",
)

LABELS = (
    "ACCUMULATION",
    "UPTREND",
    "DISTRIBUTION",
    "DOWNTREND",
    "TRANSITION_UNKNOWN",
)


def log_returns(close: np.ndarray) -> np.ndarray:
    out = np.zeros(len(close), dtype=np.float64)
    out[1:] = np.log(close[1:] / close[:-1])
    return out


class RegimeFeatures:
    """Precomputed causal feature arrays over regime bars."""

    def __init__(self, bars: Bars) -> None:
        close = bars.close
        high = bars.high
        low = bars.low
        vol = bars.volume
        T = len(close)
        self.T = T
        self.ts_close = bars.ts_close
        r = log_returns(close)
        ema12 = ind.ema(close, 12)
        ema48 = ind.ema(close, 48)
        ema50 = ind.ema(close, 50)
        atr14 = ind.atr(high, low, close, 14)
        adx14 = ind.adx(high, low, close, 14)

        rv24 = np.full(T, np.nan)
        for t in range(RV_WINDOW, T):
            rv24[t] = float(np.std(r[t - RV_WINDOW + 1 : t + 1]))

        rv_pctile = np.full(T, np.nan)
        for t in range(WARMUP_REGIME_BARS, T):
            past = rv24[t - RANK_WINDOW : t]
            cur = rv24[t]
            if np.isnan(cur) or np.isnan(past).any():
                continue
            rv_pctile[t] = float(np.count_nonzero(past < cur)) / float(RANK_WINDOW)

        dd168 = np.full(T, np.nan)
        dist_low = np.full(T, np.nan)
        with np.errstate(divide="ignore", invalid="ignore"):
            for t in range(DD_WINDOW - 1, T):
                w = close[t - DD_WINDOW + 1 : t + 1]
                dd168[t] = close[t] / float(np.max(w)) - 1.0
                dist_low[t] = close[t] / float(np.min(w)) - 1.0

        range_pos = np.full(T, np.nan)
        for t in range(RANGE_WINDOW - 1, T):
            w = close[t - RANGE_WINDOW + 1 : t + 1]
            mx = float(np.max(w))
            mn = float(np.min(w))
            range_pos[t] = 0.0 if mx == mn else (close[t] - mn) / (mx - mn) - 0.5

        vol_z = np.full(T, np.nan)
        for t in range(VOLZ_WINDOW - 1, T):
            w = vol[t - VOLZ_WINDOW + 1 : t + 1]
            m = float(np.mean(w))
            s = float(np.std(w))
            vol_z[t] = np.nan if m <= 0 else (vol[t] / m - 1.0) / (s / m)

        clv24 = np.full(T, np.nan)
        for t in range(CLV_WINDOW - 1, T):
            vals = []
            for i in range(t - CLV_WINDOW + 1, t + 1):
                rng = high[i] - low[i]
                if rng > 0:
                    vals.append((close[i] - low[i]) / rng)
            if vals:
                clv24[t] = float(np.mean(vals))
            # else: fail-closed NaN (all 24 zero-range)

        with np.errstate(divide="ignore", invalid="ignore"):
            self.arrays = {
                "r1": r,
                "r4": _roll_ret(close, 4),
                "r12": _roll_ret(close, 12),
                "r24": _roll_ret(close, 24),
                "r72": _roll_ret(close, 72),
                "ema_slope_fast": _slope(ema12, 12),
                "ema_slope_slow": _slope(ema48, 48),
                "dist_ema": np.where(atr14 > 0, (close / ema50 - 1.0) / (atr14 / close), np.nan),
                "adx14": adx14,
                "atr_pct": np.where(close > 0, atr14 / close, np.nan),
                "rv_pctile": rv_pctile,
                "dd_168": dd168,
                "dist_low": dist_low,
                "range_pos": range_pos,
                "vol_z": vol_z,
                "clv_24": clv24,
            }

    def vector_at(self, t: int) -> list[float] | None:
        """Feature vector f01..f16 at bar t, or None if any is non-finite."""
        if t < WARMUP_REGIME_BARS or t >= self.T:
            return None
        vec = []
        for name in FEATURE_ORDER:
            v = float(self.arrays[name][t])
            if not np.isfinite(v):
                return None
            vec.append(v)
        return vec


def _roll_ret(close: np.ndarray, k: int) -> np.ndarray:
    out = np.full(len(close), np.nan)
    out[k:] = np.log(close[k:] / close[:-k])
    return out


def _slope(e: np.ndarray, k: int) -> np.ndarray:
    out = np.full(len(e), np.nan)
    out[k:] = (e[k:] / e[:-k] - 1.0) / k
    return out


def build_states(
    asset: str,
    fz: Freezes,
    regime_bars: Bars,
    prior_labels: list[str | None] | None = None,
) -> list[dict]:
    """Build decision states for t >= warmup.

    prior_labels[t] = persisted regime label in force AT bar t (post-update
    output of the persistence layer); the payload for bar t carries the label
    in force at t-1 (all None/null before the first persisted state).
    Non-finite feature vectors produce a LOCAL_INVALID state that is never
    sent to any provider.
    """
    feats = RegimeFeatures(regime_bars)
    states = []
    for t in range(WARMUP_REGIME_BARS, feats.T):
        vec = feats.vector_at(t)
        prior = None
        if prior_labels is not None and t - 1 >= 0:
            prior = prior_labels[t - 1]
        st = {
            "state_id": fz.state_id(asset, int(regime_bars.ts_close[t])),
            "regime_bar_close_ns": int(regime_bars.ts_close[t]),
            "bar_index": int(t),
            "feature_vector": vec,
            "prior_regime": prior,
            "local_invalid": vec is None,
        }
        states.append(st)
    return states


def state_payload(st: dict) -> dict:
    """The anonymized state object sent across the boundary (nothing else)."""
    if st["local_invalid"]:
        raise ValueError("LOCAL_INVALID state must never be serialized for a provider")
    return {
        "feature_vector": [float(v) for v in st["feature_vector"]],
        "prior_regime": st["prior_regime"],
    }
