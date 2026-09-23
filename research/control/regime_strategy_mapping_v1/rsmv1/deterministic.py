"""Deterministic trend x vol regime classifier — V1 arm-D law UNCHANGED.

Per mapping_arms_freeze (identical to the V1 frozen classifier):
- dir = +1 if EMA12 > EMA48 and close > EMA48; -1 if EMA12 < EMA48 and
  close < EMA48; else 0 (regime-clock bars).
- ADX14 >= 22: dir +1 => UPTREND, dir -1 => DOWNTREND.
- Else range labeling by trailing-168-bar return r168 = close/close_{t-168}
  - 1 (simple): r168 < -10% => ACCUMULATION, r168 > +10% => DISTRIBUTION,
  else no eligible proposal.
Output feeds the SAME persistence layer as Jev (one law, two classifiers):
each eligible label is emitted as a proposal (confidence 1.0, margin 1.0
semantics — persistence eligibility only).
"""

from __future__ import annotations

import numpy as np

from . import indicators as ind
from .data import Bars
from .safety import UNKNOWN, run_persistence

ADX_THRESHOLD = 22.0
RANGE_RETURN_WINDOW = 168
RANGE_RETURN_THRESHOLD = 0.10


def raw_deterministic_labels(regime_bars: Bars) -> list[dict]:
    """Per-bar raw proposal stream (eligible dicts) for the persistence layer."""
    close = regime_bars.close
    ema12 = ind.ema(close, 12)
    ema48 = ind.ema(close, 48)
    adx14 = ind.adx(regime_bars.high, regime_bars.low, close, 14)
    T = len(close)
    out = []
    for t in range(T):
        lab = UNKNOWN
        eligible = False
        if t >= RANGE_RETURN_WINDOW and np.isfinite(adx14[t]):
            c = float(close[t])
            if ema12[t] > ema48[t] and c > ema48[t]:
                d = 1
            elif ema12[t] < ema48[t] and c < ema48[t]:
                d = -1
            else:
                d = 0
            if d != 0 and adx14[t] >= ADX_THRESHOLD:
                lab = "UPTREND" if d > 0 else "DOWNTREND"
                eligible = True
            else:
                r168 = c / float(close[t - RANGE_RETURN_WINDOW]) - 1.0
                if r168 < -RANGE_RETURN_THRESHOLD:
                    lab = "ACCUMULATION"
                    eligible = True
                elif r168 > RANGE_RETURN_THRESHOLD:
                    lab = "DISTRIBUTION"
                    eligible = True
        out.append({"label": lab, "eligible": eligible})
    return out


def deterministic_persisted(regime_bars: Bars, params: dict) -> list[str]:
    """Persisted proposal labels per regime bar (the deterministic router path)."""
    raw = raw_deterministic_labels(regime_bars)
    return [p.persisted for p in run_persistence(raw, params)]
