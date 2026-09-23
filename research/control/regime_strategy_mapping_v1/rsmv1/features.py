"""Causal regime-clock features f01..f16 + NAMED SEMANTIC STATE (V2 core).

Laws implemented here (golden-tested):
- feature MATH is identical to V1 f01..f16 (same formulas, same windows,
  same fail-closed conventions) — carried over verbatim.
- warmup = 192 regime bars of the cell (H4 cell: 192 H4 bars); states are
  only built for t >= warmup.
- strictly trailing windows; no centered windows; no whole-sample statistics;
  rv_pctile ranks against its own trailing 168 PAST values (exclusive).
- clv_24 fail-closed: zero-range bars dropped from the mean; all 24
  zero-range -> NaN -> state LOCAL_INVALID, never sent.
- SEMANTIC STATE (never an anonymous vector): every raw numeric keeps its
  name; every semantic bin is computed from the frozen thresholds in
  freezes/semantic_state_contract.json (bins frozen from domain-standard
  conventions + synthetic fixtures BEFORE any historical call, never from
  PnL). prior_structure / prior_direction derive from the persisted
  effective regime (see the freeze maps).
- Bin boundary convention: left-closed half-open intervals [t_i, t_{i+1});
  a value exactly on a threshold belongs to the HIGHER label. Uniform across
  all bins.
- state_id = sha256('JRV2' || asset || data_sha || bar_ts)[:16] — NEW salt
  family, provably disjoint from V1 (isolation tests).
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

# Named raw numerics that travel IN the semantic state (freeze contract).
# short/medium/long_return are the raw r4/r24/r72.
NUMERIC_FIELDS = {
    "short_return": "r4",
    "medium_return": "r24",
    "long_return": "r72",
    "ema_slope_fast": "ema_slope_fast",
    "ema_slope_slow": "ema_slope_slow",
    "dist_ema": "dist_ema",
    "adx14": "adx14",
    "atr_pct": "atr_pct",
    "rv_pctile": "rv_pctile",
    "dd_168": "dd_168",
    "dist_low": "dist_low",
    "range_pos": "range_pos",
    "vol_z": "vol_z",
    "clv_24": "clv_24",
}

# Frozen bins (semantic_state_contract.json): bin name -> (field, thresholds, labels).
BINS = {
    "fast_trend": ("ema_slope_fast", (-0.002, -0.0003, 0.0003, 0.002),
                   ("strong_down", "weak_down", "flat", "weak_up", "strong_up")),
    "slow_trend": ("ema_slope_slow", (-0.0015, -0.0002, 0.0002, 0.0015),
                   ("strong_down", "weak_down", "flat", "weak_up", "strong_up")),
    "trend_strength": ("adx14", (20.0, 30.0), ("low", "medium", "high")),
    "volatility_regime": ("rv_pctile", (0.25, 0.75, 0.90),
                          ("low", "normal", "high", "extreme")),
    "drawdown_state": ("dd_168", (-0.20, -0.05), ("deep", "mild", "near_high")),
    "range_location": ("range_pos", (-0.30, 0.30), ("near_low", "middle", "near_high")),
    "close_location": ("clv_24", (0.40, 0.60), ("weak", "neutral", "strong")),
    "volume_state": ("vol_z", (-1.0, 1.0), ("low", "normal", "high")),
    "dist_to_ema": ("dist_ema", (-1.5, -0.25, 0.25, 1.5),
                    ("extended_below", "below", "at", "above", "extended_above")),
}

# prior maps (semantic_state_contract.json, verbatim)
PRIOR_STRUCTURE_MAP = {
    "UPTREND": "TREND_UP",
    "DOWNTREND": "TREND_DOWN",
    "ACCUMULATION": "RANGE",
    "DISTRIBUTION": "RANGE",
    "TRANSITION_UNKNOWN": "RANGE",
    None: "none",
}
PRIOR_DIRECTION_MAP = {
    "UPTREND": "UP",
    "DOWNTREND": "DOWN",
    "ACCUMULATION": "DOWN",
    "DISTRIBUTION": "UP",
    "TRANSITION_UNKNOWN": "NEUTRAL",
    None: "none",
}


def log_returns(close: np.ndarray) -> np.ndarray:
    out = np.zeros(len(close), dtype=np.float64)
    out[1:] = np.log(close[1:] / close[:-1])
    return out


def binize(value: float, thresholds, labels) -> str:
    """Left-closed half-open binning: [t_{i-1}, t_i) -> labels[i]."""
    for t, lab in zip(thresholds, labels):
        if value < t:
            return lab
    return labels[-1]


def compute_bins(numerics: dict) -> dict:
    """Recompute every bin from named raw numerics (used by features and by
    the canary perturbation generator)."""
    out = {}
    for bin_name, (field, thresholds, labels) in BINS.items():
        v = numerics.get(field)
        if v is None or v != v:
            continue  # bin uncomputed when its raw source is absent
        out[bin_name] = binize(float(v), thresholds, labels)
    return out


class RegimeFeatures:
    """Precomputed causal feature arrays over regime bars (V1 math verbatim)."""

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

    def numerics_at(self, t: int) -> dict | None:
        """Named raw numerics at bar t, or None if any is non-finite."""
        vec = self.vector_at(t)
        if vec is None:
            return None
        by_name = dict(zip(FEATURE_ORDER, vec))
        return {name: by_name[src] for name, src in NUMERIC_FIELDS.items()}


def _roll_ret(close: np.ndarray, k: int) -> np.ndarray:
    out = np.full(len(close), np.nan)
    out[k:] = np.log(close[k:] / close[:-k])
    return out


def _slope(e: np.ndarray, k: int) -> np.ndarray:
    out = np.full(len(e), np.nan)
    out[k:] = (e[k:] / e[:-k] - 1.0) / k
    return out


def semantic_state(
    asset: str,
    fz: Freezes,
    regime_bars: Bars,
    t: int,
    feats: RegimeFeatures,
    prior_regime: str | None,
) -> dict | None:
    """Build the NAMED SEMANTIC STATE at regime bar t (None if LOCAL_INVALID).

    payload = {
      bins:            {9 named semantic bins from frozen thresholds},
      numerics:        {14 named raw numerics},
      prior_structure: TREND_UP|TREND_DOWN|RANGE|none   (persisted map),
      prior_direction: UP|DOWN|NEUTRAL|none             (persisted map),
    }
    Causality: trailing-only windows; prior = persisted regime in force at
    t-1 (the caller passes it). No symbol, no dates, no price levels.
    """
    numerics = feats.numerics_at(t)
    if numerics is None:
        return None
    return {
        "bins": compute_bins(numerics),
        "numerics": {k: float(v) for k, v in numerics.items()},
        "prior_structure": PRIOR_STRUCTURE_MAP.get(prior_regime, "none"),
        "prior_direction": PRIOR_DIRECTION_MAP.get(prior_regime, "none"),
    }


def state_payload(st: dict) -> dict:
    """The anonymized state object sent across the boundary (nothing else)."""
    return {
        "bins": dict(st["bins"]),
        "numerics": {k: float(v) for k, v in st["numerics"].items()},
        "prior_structure": st["prior_structure"],
        "prior_direction": st["prior_direction"],
    }


def normalize_semantic_state(raw: dict) -> dict:
    """Normalize a state into the nested payload form.

    Accepts either the nested form {bins, numerics, prior_structure,
    prior_direction} or the FLAT freeze-fixture form (bin names and numeric
    names mixed at the top level with the prior keys).
    """
    if "bins" in raw or "numerics" in raw:
        return {
            "bins": dict(raw.get("bins", {})),
            "numerics": {k: float(v) for k, v in raw.get("numerics", {}).items()},
            "prior_structure": raw.get("prior_structure", "none"),
            "prior_direction": raw.get("prior_direction", "none"),
        }
    bins = {k: raw[k] for k in BINS if k in raw}
    numerics = {k: float(raw[k]) for k in NUMERIC_FIELDS if k in raw}
    return {
        "bins": bins,
        "numerics": numerics,
        "prior_structure": raw.get("prior_structure", "none"),
        "prior_direction": raw.get("prior_direction", "none"),
    }
