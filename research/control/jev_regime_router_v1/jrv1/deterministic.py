"""Arm D — deterministic trend x vol regime classifier.

Per regime_strategy_mapping_freeze (ancestry regime.py semantics):
- dir = +1 if EMA12 > EMA48 and close > EMA48; -1 if EMA12 < EMA48 and
  close < EMA48; else 0 (regime-clock bars).
- ADX14 >= 22 (ancestry midpoint of adx_max 20 / breakout adx_min 25):
  dir +1 => UPTREND, dir -1 => DOWNTREND.
- Else range labeling by trailing-168-bar return r168 = close/close_{t-168}
  - 1 (simple): r168 < -10% => ACCUMULATION, r168 > +10% => DISTRIBUTION,
  else TRANSITION_UNKNOWN.
Output feeds the SAME persistence layer as Jev (one law, two classifiers):
each raw label is emitted as an eligible top1 (confidence 1.0, margin 1.0).
"""

from __future__ import annotations

import numpy as np

from . import indicators as ind
from .data import Bars
from .persistence import UNKNOWN, run_persistence

ADX_THRESHOLD = 22.0
RANGE_RETURN_WINDOW = 168
RANGE_RETURN_THRESHOLD = 0.10


def raw_deterministic_labels(regime_bars: Bars) -> list[dict]:
    """Per-bar raw label stream (eligible dicts) for the persistence layer."""
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
    """Persisted regime labels per regime bar for arm D."""
    raw = raw_deterministic_labels(regime_bars)
    return [p.persisted for p in run_persistence(raw, params)]
