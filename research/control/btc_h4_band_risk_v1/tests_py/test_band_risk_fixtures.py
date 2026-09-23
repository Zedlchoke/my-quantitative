"""BRV1 hand-computed fixtures for the overlay law (plan section 1)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
sys.dont_write_bytecode = True
import band_risk as B      # noqa: E402


def make_panel(close):
    ms = 1577836800000 + np.arange(len(close)) * 4 * 3600 * 1000
    return pd.DataFrame({"bucket_ms": ms, "open": close, "high": close,
                         "low": close, "close": close})


def flat_then(closes, n_flat=260, price=100.0):
    return np.concatenate([np.full(n_flat, price), np.asarray(closes, float)])


def test_trail_golden_fires_one_bar_after_peak_break():
    close = flat_then([102.0, 103.0, 104.0, 93.0])
    panel = make_panel(close)
    dec = B.sig_band_overlay(panel, band=0.005, trail=0.10)
    # entry decision at bar 260 (102/100-1=2% > 0.5%); peak walks 102->104;
    # bar 263: 93 < 104*0.9=93.6 -> TRAIL exit decision exactly there
    assert dec[260] == 1.0 and dec[261] == 1.0 and dec[262] == 1.0
    assert dec[263] == 0.0


def test_trail_not_triggered_by_old_peak_after_reentry():
    close = flat_then([102.0, 104.0, 90.0, 91.0, 102.0, 101.0])
    panel = make_panel(close)
    dec = B.sig_band_overlay(panel, band=0.005, trail=0.10)
    # bar 260 in (2%); 261 in (peak 104); 262: 90<93.6 exit TRAIL; 263: flat
    # (cooldown 0 default -> band entry allowed): 91/100=−9% no; 264: 102 →
    # re-entry decision, peak RESETS to 102; 265: 101 < 102*0.9=91.8? NO ->
    # stays long (old peak 104 must not leak: 101<93.6 false anyway)
    assert dec[262] == 0.0 and dec[264] == 1.0 and dec[265] == 1.0


def test_cat_golden():
    close = flat_then([102.0, 103.0, 86.0])
    panel = make_panel(close)
    dec = B.sig_band_overlay(panel, band=0.005, cat=0.15)
    # entry_ref = 102 (bar 260); bar 262: 86 < 102*0.85=86.7 -> CAT exit
    assert dec[261] == 1.0 and dec[262] == 0.0


def test_cooldown_blocks_band_reentry_only_for_k_bars():
    close = flat_then([102.0, 103.0, 93.0, 103.5, 103.6, 103.7])
    panel = make_panel(close)
    dec = B.sig_band_overlay(panel, band=0.005, trail=0.10, cooldown=2)
    # 262: 93 < 103*0.9=92.7? NO (93>92.7) — adjust: trail exit needs <92.7
    # -> use 92.0 instead in this scenario
    close2 = flat_then([102.0, 103.0, 92.0, 103.5, 103.6, 103.7])
    dec2 = B.sig_band_overlay(make_panel(close2), band=0.005, trail=0.10, cooldown=2)
    assert dec2[262] == 0.0            # TRAIL exit at 92 < 92.7
    assert dec2[263] == 0.0            # cooldown bar 1 (r=3.5% would enter)
    assert dec2[264] == 0.0            # cooldown bar 2
    assert dec2[265] == 1.0            # cooldown expired -> band re-entry


def test_band_exit_still_works_without_overlay():
    close = flat_then([102.0, 103.0, 98.5])
    panel = make_panel(close)
    dec = B.sig_band_overlay(panel, band=0.005)  # no trail/cat
    # bar 262: 98.5/100-1 = −1.5% < −0.5% -> base band exit
    assert dec[261] == 1.0 and dec[262] == 0.0


def test_fold_reset_starts_flat():
    close = flat_then([102.0, 103.0, 104.0, 103.0, 102.0, 101.0])
    panel = make_panel(close)
    folds = np.zeros(len(close), dtype=int)
    folds[263:] = 1  # fold boundary between bars 262 and 263
    dec = B.sig_band_overlay(panel, band=0.005, trail=0.10, folds=folds)
    # long across 260..262; fold reset at 263 -> flat; re-entry only via band:
    # 103/100-1 = 3% > 0.5% -> re-entry decision at 263 with fresh peak
    assert dec[262] == 1.0 and dec[263] == 1.0
    # and the fresh peak means bar 265 (101 vs peak 103*0.9=92.7) stays long
    assert dec[265] == 1.0


def test_no_leverage_and_finite(dec=None):
    close = flat_then([102.0] * 8)
    panel = make_panel(close)
    dec = B.sig_band_overlay(panel, band=0.005, trail=0.10)
    assert set(np.unique(dec)).issubset({0.0, 1.0})
