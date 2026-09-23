"""Phase-rule golden tests (plan §14): named outputs, UNKNOWN conditions,
causality/no-lookahead mutation, warmup exclusion. All fixtures synthetic."""

import numpy as np
import pandas as pd
import pytest

from research.control.phase_strategy_v1.lane_btc_h4.pipeline import config
from research.control.phase_strategy_v1.lane_btc_h4.pipeline.phase_rule import (
    UNKNOWN, FROZEN, classify, notch_variants, label_agreement)

UNK = UNKNOWN


def _lin_up(n=300):
    return pd.Series(np.arange(n, dtype="float64") * 0.5 + 100.0)


def _lin_down(n=300):
    return pd.Series(1000.0 - np.arange(n, dtype="float64") * 0.5)


def test_golden_uptrend_named_output():
    labels = classify(_lin_up())
    assert labels.iloc[FROZEN.warmup + 1] == "UPTREND"
    post = labels.iloc[FROZEN.warmup:]
    assert (post == "UPTREND").mean() > 0.95


def test_golden_downtrend_named_output():
    labels = classify(_lin_down())
    assert labels.iloc[FROZEN.warmup + 1] == "DOWNTREND"
    post = labels.iloc[FROZEN.warmup:]
    assert (post == "DOWNTREND").mean() > 0.9


def _v_pump_recover(n=400):
    """Pump -> dump -> recovery: the right side of the V recovers above the
    120-bars-ago value (sma turns up) while the dump top is still inside the
    sma window (price still below the mean) -> ACCUMULATION quadrant.
    Dump onset (price above the falling mean) -> DISTRIBUTION quadrant."""
    p = np.empty(n)
    p[:60] = 100.0
    p[60:100] = 100.0 + np.arange(40) * 2.0        # pump 100 -> 180
    p[100:130] = 180.0 - np.arange(30) * 2.33      # dump 180 -> ~110
    p[130:] = 110.0 + np.arange(n - 130) * 0.4     # recovery
    return pd.Series(p)


def test_golden_accumulation_and_distribution_quadrants():
    labs = classify(_v_pump_recover())
    counts = labs.value_counts().to_dict()
    assert counts.get("ACCUMULATION", 0) >= 10
    assert counts.get("DISTRIBUTION", 0) >= 10
    assert counts.get("UPTREND", 0) >= 100


def test_unknown_on_flat_series():
    labels = classify(pd.Series(np.full(400, 100.0)))
    assert (labels == UNK).all()


def test_warmup_exclusion():
    labels = classify(_lin_up())
    assert (labels.iloc[: FROZEN.warmup] == UNK).all(), "no label before warmup bars"
    assert labels.iloc[FROZEN.warmup - 1] == UNK
    assert FROZEN.warmup == config.N_SMA + config.M_SLOPE + config.CONFIRM


def test_no_lookahead_future_mutation_invariant():
    close = _lin_up(400)
    base = classify(close)
    mutated = close.copy()
    mutated.iloc[200:] = 1e9  # drastic future perturbation
    after = classify(mutated)
    assert (base.iloc[:200].to_numpy() == after.iloc[:200].to_numpy()).all()


def test_confirmation_flicker_stays_unknown():
    # a single-bar quadrant flip inside a trend must not produce a label
    close = _lin_up(400).copy()
    labels_base = classify(close)
    # base series is UPTREND throughout post-warmup; inject a 2-bar flat patch:
    # even if raw state flips for <=2 bars, U4 keeps labels at those bars UNKNOWN
    patched = close.copy()
    patched.iloc[300:302] = close.iloc[299]
    labels = classify(patched)
    assert labels.iloc[300] == UNK or labels_base.iloc[300] == labels.iloc[300]
    assert (labels.iloc[: FROZEN.warmup] == UNK).all()


def test_exactly_five_outputs():
    labels = classify(_v_pump_recover())
    assert set(labels.unique()) <= set(config.PHASES)


def test_sensitivity_notch_ladder_shape_and_agreement():
    close = _lin_up(400)
    base = classify(close)
    variants = notch_variants()
    assert len(variants) == 15  # 5 params x 3 ladder values (base incl. -> identity rows)
    for key, params in variants.items():
        agree = label_agreement(base, classify(close, params))
        assert 0.0 <= agree <= 1.0
    # identical params reproduce exactly (determinism)
    assert label_agreement(base, classify(close, FROZEN)) == 1.0
