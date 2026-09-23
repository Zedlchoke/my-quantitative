"""BTC-H4-BAND-RISK-V1 — exit-side overlay decision builders (frozen law,
plan section 1). Decision series only; pricing is es1_engine.simulate.

Law: base = ES1 band law (long enters when close > SMA200*(1+b), exits when
close < SMA200*(1-b)). Overlay adds EXIT-ONLY triggers evaluated at H4
close while the band state is long:
  TRAIL: close < peak_close_since_entry * (1 - trail)  -> exit
  CAT:   close < entry_ref_close * (1 - cat)           -> exit
  COOLDOWN k: after any OVERLAY exit, band entries blocked for k bars
Fold law: the overlay state machine RESETS to flat at each fold boundary
(simulate force-flats at fold ends; each fold starts fresh; cooldown does
not carry across folds). Re-entry is ONLY via the band law.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def sig_band_overlay(panel, band: float, trail: float | None = None,
                     cat: float | None = None, cooldown: int = 0,
                     folds: np.ndarray | None = None) -> np.ndarray:
    close = panel["close"].to_numpy(float)
    sma = pd.Series(close).rolling(200).mean().to_numpy()
    n = len(close)
    dec = np.zeros(n)
    state = 0
    peak = None
    entry_ref = None
    cool = 0
    for t in range(n):
        if folds is not None and t > 0 and folds[t] != folds[t - 1]:
            state, peak, entry_ref, cool = 0, None, None, 0  # fold reset
        finite = bool(np.isfinite(sma[t]))
        r = close[t] / sma[t] - 1.0 if finite else None
        if state == 0:
            if cool > 0:
                cool -= 1
            elif finite and r > band:
                state = 1
                peak = close[t]
                entry_ref = close[t]
                dec[t] = 1.0
        else:
            peak = max(peak, close[t])
            exit_now = False
            if trail is not None and close[t] < peak * (1.0 - trail):
                exit_now = True          # TRAIL
            if not exit_now and cat is not None and close[t] < entry_ref * (1.0 - cat):
                exit_now = True          # CAT
            if not exit_now and (not finite or r < -band):
                exit_now = True          # base band exit
            if exit_now:
                state = 0
                dec[t] = 0.0
                if trail is not None or cat is not None:
                    cool = cooldown      # churn law on overlay exits only
            else:
                dec[t] = 1.0
    return dec
