"""Attribution reconciliation for the V3 canonical factory (A2, deliverable 5).

Frozen contract: on synthetic fixtures the attribution identity
``fsum(symbol_contribution) - total_cost = total_pnl`` closes within the
frozen tolerance 1e-12 (measured residuals are ~1e-16 — the identity is exact
up to float rounding because equity evolves as E_d = E_{d-1} + E_{d-1}*p_d,
so E_T - E_0 = sum(E_{d-1} * p_d) = sum(contributions) exactly, minus costs).

The identity must hold for A4-style books, A5-style books with an explicit
CASH leg, and every stress variant — a residual above tolerance means the
accounting is broken (e.g. the V2 sidecar's CASH-in-turnover or double-add
cost accumulator), never a strategy property.
"""
import math

import pytest

from research.assets.stocks.factory import (
    ATTRIBUTION_TOLERANCE,
    AttributionBreakError,
    assert_reconciles,
    value_book,
)

from tests.stocks_free_v3.test_factory_valuation import (
    DIST, DIST_AAA, RAW_A4, RAW_A5, S4, S5, _entries_a4, _entries_a5,
)


def _variants():
    """(label, value_book kwargs) over both book styles."""
    cases = []
    for label, entries, raw, sessions in (
        ("a4", _entries_a4(), RAW_A4, S4),
        ("a5", _entries_a5(), RAW_A5, S5),
    ):
        for kwargs in ({}, {"adverse_bps": 25.0}, {"extra_delay_sessions": 1},
                       {"excluded_symbol": "BBB" if label == "a4" else "CCC"}):
            cases.append((f"{label}-{sorted(kwargs.items())}", entries, raw,
                          sessions, kwargs))
    return cases


@pytest.mark.parametrize("label,entries,raw,sessions,kwargs", _variants())
def test_attribution_reconciles_within_frozen_tolerance(label, entries, raw, sessions, kwargs):
    res = value_book(entries, raw, DIST, {}, sessions, cost_bps=100.0, **kwargs)
    assert abs(res.attribution_residual) <= ATTRIBUTION_TOLERANCE
    # measured precision: the identity is exact up to float noise
    assert abs(res.attribution_residual) < 1e-14
    assert_reconciles(res)  # identity + cost-charged-once, fail closed


def test_attribution_reconciles_with_distributions_and_no_periods():
    # distributions shift contribution into the ex-date leg
    res = value_book(_entries_a4(), RAW_A4, DIST_AAA, {}, S4, cost_bps=100.0)
    assert abs(res.attribution_residual) <= ATTRIBUTION_TOLERANCE
    assert_reconciles(res)
    # a book that never trades and never holds: zero everything, still closes
    empty = value_book([], RAW_A4, DIST, {}, S4, cost_bps=100.0)
    assert empty.total_pnl == 0.0 and empty.total_cost == 0.0
    assert empty.symbol_contribution == {}
    assert abs(empty.attribution_residual) <= ATTRIBUTION_TOLERANCE


def test_cash_leg_never_receives_contribution():
    res = value_book(_entries_a5(), RAW_A5, DIST, {}, S5, cost_bps=50.0)
    assert "CASH" not in res.symbol_contribution
    # realized contributions land on the ETF legs that earned them
    assert abs(res.symbol_contribution["CCC"] - (-0.0697550)) < 1e-9
    assert abs(res.symbol_contribution["DDD"] - 0.02302961325) < 1e-9
    contrib_sum = math.fsum(res.symbol_contribution.values())
    assert abs(contrib_sum - res.total_cost - res.total_pnl) <= ATTRIBUTION_TOLERANCE


def test_broken_attribution_residual_is_detected():
    res = value_book(_entries_a4(), RAW_A4, DIST, {}, S4, cost_bps=100.0)
    res.attribution_residual = 1e-6  # e.g. a CASH-in-turnover sidecar artifact
    with pytest.raises(AttributionBreakError, match="residual"):
        assert_reconciles(res)


def test_attribution_matches_hand_values_both_styles():
    a4 = value_book(_entries_a4(), RAW_A4, DIST, {}, S4, cost_bps=100.0)
    assert abs(a4.symbol_contribution["AAA"] - 0.05964) < 1e-12
    assert abs(a4.symbol_contribution["BBB"] - 0.0209042176) < 1e-12
    a5 = value_book(_entries_a5(), RAW_A5, DIST, {}, S5, cost_bps=50.0)
    assert abs(a5.symbol_contribution["CCC"] - (-0.0697550)) < 1e-12
    assert abs(a5.symbol_contribution["DDD"] - 0.02302961325) < 1e-12
