"""PSV1 lane_btc_h4 — deterministic causal phase rule (plan §5; frozen in config).

Decision at H4 close; first executable fill at the NEXT H4 open (>=1 bar lag
is a property of the strategy layer; the rule itself only ever reads bars
with close time <= decision time).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import config

UNKNOWN = "TRANSITION_UNKNOWN"


@dataclass(frozen=True)
class PhaseParams:
    n_sma: int = config.N_SMA
    m_slope: int = config.M_SLOPE
    deadband_slope: float = config.DEADBAND_SLOPE
    deadband_side: float = config.DEADBAND_SIDE
    confirm: int = config.CONFIRM

    @property
    def warmup(self) -> int:
        return self.n_sma + self.m_slope + self.confirm


FROZEN = PhaseParams()


def classify(close: pd.Series, p: PhaseParams = FROZEN) -> pd.Series:
    """Causal per-bar phase labels on the H4 close series (indexed 0..T-1).

    No look-ahead: sma/slope/side at t use closes <= t; the confirmation
    window uses raw states at t-confirm+1..t. Future perturbations cannot
    change past labels (tested in tests_py).
    """
    close_arr = close.to_numpy(dtype="float64")
    n = len(close_arr)
    sma = pd.Series(close_arr).rolling(p.n_sma).mean().to_numpy()
    sma_lag = np.full(n, np.nan)
    idx = np.arange(p.n_sma + p.m_slope - 1, n)
    sma_lag[idx] = sma[idx - p.m_slope]

    with np.errstate(invalid="ignore", divide="ignore"):
        slope = sma / sma_lag - 1.0
        side = close_arr / sma - 1.0

    raw = np.full(n, UNKNOWN, dtype=object)
    for t in range(n):
        if t < p.warmup - 1:
            continue  # U1 warmup
        if not np.isfinite(sma[t]) or not np.isfinite(sma_lag[t]):
            continue
        if abs(slope[t]) < p.deadband_slope:
            continue  # U2
        if abs(side[t]) < p.deadband_side:
            continue  # U3
        if slope[t] > 0 and side[t] < 0:
            raw[t] = "ACCUMULATION"
        elif slope[t] > 0 and side[t] >= 0:
            raw[t] = "UPTREND"
        elif slope[t] < 0 and side[t] > 0:
            raw[t] = "DISTRIBUTION"
        else:
            raw[t] = "DOWNTREND"

    # U4 confirmation: raw state must repeat CONFIRM consecutive bars.
    labels = np.full(n, UNKNOWN, dtype=object)
    c = p.confirm
    for t in range(c - 1, n):
        s = raw[t]
        if s != UNKNOWN and all(raw[t - k] == s for k in range(1, c)):
            labels[t] = s
    return pd.Series(labels, index=close.index, name="phase")


def notch_variants() -> dict[str, PhaseParams]:
    """+-1 notch variants for the label-agreement sensitivity table."""
    out: dict[str, PhaseParams] = {}
    ladder = config.NOTCH_LADDER
    for name, values in ladder.items():
        for v in values:
            key = f"{name}={v}"
            out[key] = PhaseParams(
                n_sma=v if name == "N_SMA" else config.N_SMA,
                m_slope=v if name == "M_SLOPE" else config.M_SLOPE,
                deadband_slope=v if name == "DEADBAND_SLOPE" else config.DEADBAND_SLOPE,
                deadband_side=v if name == "DEADBAND_SIDE" else config.DEADBAND_SIDE,
                confirm=v if name == "CONFIRM" else config.CONFIRM,
            )
    return out


def label_agreement(a: pd.Series, b: pd.Series) -> float:
    """Share of positions with identical labels (sensitivity table metric)."""
    if len(a) != len(b):
        raise ValueError("length mismatch")
    return float((a.to_numpy() == b.to_numpy()).mean())
