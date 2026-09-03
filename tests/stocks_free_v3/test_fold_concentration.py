"""Fold concentration: ONE per-arm definition (A2, deliverable 6).

Frozen definition (PLAN_stocks.md section 9 A2): per-arm positive fold
contribution divided by that SAME arm's total positive fold contribution.
No family pool, no neighbour substitution, no mixed gross/net denominator.

Hand fixture: arm folds [0.3, -0.1, 0.5] -> positive total 0.8,
shares [0.375, 0.0, 0.625], max_share 0.625 (the -0.1 fold contributes 0 to
numerator and denominator). Equal folds [0.2, 0.2, 0.2] -> shares [1/3]*3.
No positive fold at all [-0.1, 0.0, -0.3] -> positive_total 0.0, all shares
0.0: no gains exist, so no fold concentrates gains.
"""
import math

import pytest

from research.assets.stocks.factory import (
    fold_concentration,
    per_arm_fold_concentration,
)


def test_hand_computed_shares():
    fc = fold_concentration([0.3, -0.1, 0.5], arm_id="ARM_X")
    assert fc.arm_id == "ARM_X"
    assert fc.positive_total == 0.8
    for got, want in zip(fc.shares, (0.375, 0.0, 0.625)):
        assert abs(got - want) < 1e-15
    assert abs(fc.max_share - 0.625) < 1e-15


def test_equal_folds_split_evenly():
    fc = fold_concentration([0.2, 0.2, 0.2])
    for s in fc.shares:
        assert abs(s - 1.0 / 3.0) < 1e-15
    assert abs(fc.max_share - 1.0 / 3.0) < 1e-15


def test_no_positive_fold_reports_zero_concentration():
    fc = fold_concentration([-0.1, 0.0, -0.3])
    assert fc.positive_total == 0.0
    assert fc.shares == (0.0, 0.0, 0.0)
    assert fc.max_share == 0.0


def test_two_folds_from_synthetic_valuation():
    # period PnLs of the A5-style hand fixture: [-0.0697550, 0.02302961325]
    fc = fold_concentration([-0.0697550, 0.02302961325])
    assert fc.shares[0] == 0.0
    assert abs(fc.shares[1] - 1.0) < 1e-15
    assert fc.max_share == 1.0


def test_per_arm_denominators_are_independent():
    arms = {"ARM_A": [0.3, -0.1, 0.5], "ARM_B": [0.2, 0.2, 0.2]}
    per_arm = per_arm_fold_concentration(arms)
    assert abs(per_arm["ARM_A"].max_share - 0.625) < 1e-15
    assert abs(per_arm["ARM_B"].max_share - 1.0 / 3.0) < 1e-15
    # removing or adding OTHER arms never changes an arm's result
    assert per_arm_fold_concentration({"ARM_A": arms["ARM_A"]})["ARM_A"] == per_arm["ARM_A"]
    wider = dict(arms)
    wider["ARM_C"] = [10.0, -10.0, 10.0]
    assert per_arm_fold_concentration(wider)["ARM_A"] == per_arm["ARM_A"]
    # a family-pooled denominator would give ARM_A share 0.3/(0.3+0.5+0.6) --
    # explicitly NOT what this definition produces
    assert abs(per_arm["ARM_A"].shares[0] - 0.3 / 1.4) > 1e-3


def test_empty_input_rejected():
    with pytest.raises(ValueError, match="non-empty"):
        fold_concentration([])
    with pytest.raises(ValueError, match="non-empty"):
        fold_concentration("not-a-sequence")
    assert per_arm_fold_concentration({}) == {}
