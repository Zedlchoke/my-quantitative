"""Drop-one-ETF selection: deterministic, held-only, contribution-ranked (A2).

Frozen definition (PLAN_stocks.md section 9 A2, deliverable 7): the drop-one
diagnostic excludes a HELD ETF with the largest realized absolute-weight
contribution (|symbol_contribution| from the canonical attribution), ties
broken lexicographically by symbol.  Dropping a non-held symbol, CASH, or a
zero-contribution ETF is REJECTED (fail closed).

Hand fixture: weights {AAA:0.5, BBB:0.3, CCC:0.0, CASH:0.2}, contributions
{AAA:0.02, BBB:-0.05}: CCC is not held (zero weight), CASH never selectable;
|BBB| 0.05 > |AAA| 0.02 -> BBB selected despite its negative sign.
Tie: {AAA:+0.05, BBB:-0.05} -> lexicographic AAA.
All-zero contributions -> rejected.  On the A4-style hand book the realized
contributions AAA 0.05964 / BBB 0.0209042176 select AAA.
"""
import pytest

from research.assets.stocks.factory import (
    assert_drop_one_allowed,
    select_drop_one_symbol,
    value_book,
)

from tests.stocks_free_v3.test_factory_valuation import (
    DIST, RAW_A4, S4, _entries_a4,
)


def test_selects_largest_absolute_contribution_among_held():
    weights = {"AAA": 0.5, "BBB": 0.3, "CCC": 0.0, "CASH": 0.2}
    contribution = {"AAA": 0.02, "BBB": -0.05}
    assert select_drop_one_symbol(contribution, weights) == "BBB"


def test_tie_breaks_lexicographically():
    weights = {"AAA": 0.5, "BBB": 0.3, "CASH": 0.2}
    assert select_drop_one_symbol({"AAA": 0.05, "BBB": -0.05}, weights) == "AAA"
    assert select_drop_one_symbol({"AAA": -0.05, "BBB": 0.05}, weights) == "AAA"


def test_selection_from_realized_attribution_of_hand_book():
    res = value_book(_entries_a4(), RAW_A4, DIST, {}, S4, cost_bps=100.0)
    weights = {"AAA": 0.3, "BBB": 0.5, "CASH": 0.2}
    assert select_drop_one_symbol(res.symbol_contribution, weights) == "AAA"


def test_rejects_non_held_cash_and_zero_contribution():
    weights = {"AAA": 0.5, "BBB": 0.3, "CCC": 0.0, "CASH": 0.2}
    contribution = {"AAA": 0.02, "BBB": -0.05}
    with pytest.raises(ValueError, match="not held"):
        assert_drop_one_allowed("CCC", contribution, weights)
    with pytest.raises(ValueError, match="not held"):
        assert_drop_one_allowed("ZZZ", contribution, weights)
    with pytest.raises(ValueError, match="CASH"):
        assert_drop_one_allowed("CASH", contribution, weights)
    with pytest.raises(ValueError, match="zero realized contribution"):
        assert_drop_one_allowed("BBB", {"AAA": 0.02}, weights)
    # nothing held at all
    with pytest.raises(ValueError, match="holds no ETF"):
        select_drop_one_symbol(contribution, {"CASH": 1.0})
    # largest realized contribution among held is exactly zero
    with pytest.raises(ValueError, match="zero realized contribution"):
        select_drop_one_symbol({"AAA": 0.0, "BBB": 0.0}, {"AAA": 0.5, "BBB": 0.5})


def test_zero_weight_symbols_never_win_selection():
    weights = {"AAA": 0.0, "BBB": 0.4}
    contribution = {"AAA": 9.9, "BBB": 0.01}  # AAA huge but NOT held
    assert select_drop_one_symbol(contribution, weights) == "BBB"
