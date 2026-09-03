"""Hand-computed goldens for the V3 canonical measurement factory (A2).

Canonical contract (research/assets/stocks/factory.py): rebalance AT the fill
close (fill day earns no same-day return on new weights); day returns use the
weights set at the previous close; turnover counts ETF-leg changes ONLY —
an explicit "CASH" leg inside targets is never a tradable leg; cost =
equity x ETF-turnover x bps / 1e4, deducted from equity at the fill and
accumulated into total_cost EXACTLY ONCE.

Fixture A4-A (A4-style book: no explicit CASH in targets, separate
cash_weight). Sessions s1..s5; AAA raw 100,110,110,110,110; BBB raw
50,50,50,52,52. Book: FILL s1 {AAA:0.6} cash 0.4; FILL s3 {AAA:0.3,BBB:0.5}
cash 0.2; FORCE_FLAT s5. Hand computation (cost 100 bps):
  s1 fill: turnover |0.6-0| = 0.6, cost 1.0*0.6*0.01 = 0.006, equity 0.994
  s2: AAA +10% x w0.6 -> equity 0.994*1.06 = 1.05364
  s3: AAA flat -> 1.05364; period1 = 1.05364-0.994 = 0.05964; fill:
      turnover |0.3-0.6|+|0.5-0| = 0.8, cost 1.05364*0.8*0.01 = 0.00842912,
      equity 1.04521088, total_cost 0.01442912
  s4: BBB +4% x w0.5 -> +2% -> equity 1.04521088*1.02 = 1.0661150976
  s5: flat -> 1.0661150976; period2 = 1.0661150976-1.04521088 = 0.0209042176;
      FORCE_FLAT: turnover 0.8, cost 0.0085289207808,
      equity 1.0575861768192, total_cost 0.0229580407808
  total_pnl 0.0575861768192; final flush adds period3 = (s5, 0.0);
  expectancy = (0.05964 + 0.0209042176 + 0.0)/3 = 0.026848072533333335;
  PF None (no losing periods)
  MDD: both cost dips are exactly 0.8% of the pre-cost peak (cost/peak =
  0.008 by construction) -> max_drawdown 0.008
  attribution: AAA 0.994*0.6*0.10 = 0.05964; BBB 1.04521088*0.5*0.04 =
  0.0209042176; 0.0805442176 - 0.0229580407808 = 0.0575861768192 (exact)

Fixture A5-A (A5-style book: explicit "CASH" inside targets, matching
cash_weight). Sessions e1..e4; CCC raw 100,90,90,90 (-10% at e2, then flat);
DDD raw 200,200,200,210 (+5% at e4). Book: FILL e1 {CCC:0.7, CASH:0.3};
FILL e3 {DDD:0.5, CASH:0.5}. Hand computation (cost 50 bps):
  e1 fill: ETF turnover |0.7-0| = 0.7 (CASH 1.0->0.3 NOT counted),
      cost 1.0*0.7*0.005 = 0.0035, equity 0.9965, total_cost 0.0035
  e2: CCC -10% x w0.7 -> -7% -> equity 0.9965*0.93 = 0.9267450
  e3: CCC flat -> 0.9267450; period1 = 0.9267450 - 0.9965 = -0.0697550;
      fill: ETF turnover |0-0.7|+|0.5-0| = 1.2 (the CASH leg 0.3->0.5 adds
      NOTHING — the audit defect (a) repair),
      cost 0.9267450*1.2*0.005 = 0.005560470, equity 0.921184530,
      total_cost 0.009060470
  e4: DDD +5% x w0.5 -> +2.5% -> equity 0.921184530*1.025 = 0.94421414325;
      final flush: period2 = 0.02302961325
  total_pnl -0.05578585675; total_cost 0.009060470;
  expectancy = (-0.0697550 + 0.02302961325)/2 = -0.023362693375;
  PF = 0.02302961325/0.0697550; MDD = (0.9965-0.921184530)/0.9965
  attribution: CCC 0.9965*0.7*(-0.10) = -0.0697550; DDD 0.921184530*0.5*0.05
      = 0.02302961325; -0.04672538675 - 0.009060470 = -0.05578585675 (exact)
"""
import pytest

from research.assets.stocks.factory import (
    ATTRIBUTION_TOLERANCE,
    AttributionBreakError,
    assert_reconciles,
    etf_leg_turnover,
    normalize_entry_targets,
    value_book,
)
from research.stocks_free_v2.harness import value_book as harness_value_book

S4 = ["2020-01-06", "2020-01-07", "2020-01-08", "2020-01-09", "2020-01-10"]
RAW_A4 = {
    "AAA": {"2020-01-06": 100.0, "2020-01-07": 110.0, "2020-01-08": 110.0,
            "2020-01-09": 110.0, "2020-01-10": 110.0},
    "BBB": {"2020-01-06": 50.0, "2020-01-07": 50.0, "2020-01-08": 50.0,
            "2020-01-09": 52.0, "2020-01-10": 52.0},
}
DIST = {}
DIST_AAA = {"AAA": {"2020-01-07": 0.5}}  # $0.50/share on 01-07

S5 = ["2020-02-03", "2020-02-04", "2020-02-05", "2020-02-06"]
RAW_A5 = {
    "CCC": {"2020-02-03": 100.0, "2020-02-04": 90.0,
            "2020-02-05": 90.0, "2020-02-06": 90.0},
    "DDD": {"2020-02-03": 200.0, "2020-02-04": 200.0,
            "2020-02-05": 200.0, "2020-02-06": 210.0},
}


def _entries_a4():
    return [
        {"entry_type": "FILL", "fill_date": S4[0], "targets": {"AAA": 0.6},
         "cash_weight": 0.4},
        {"entry_type": "FILL", "fill_date": S4[2], "targets": {"AAA": 0.3, "BBB": 0.5},
         "cash_weight": 0.2},
        {"entry_type": "FORCE_FLAT", "fill_date": S4[4], "targets": {}},
    ]


def _entries_a5():
    return [
        {"entry_type": "FILL", "fill_date": S5[0], "targets": {"CCC": 0.7, "CASH": 0.3},
         "cash_weight": 0.3},
        {"entry_type": "FILL", "fill_date": S5[2], "targets": {"DDD": 0.5, "CASH": 0.5},
         "cash_weight": 0.5},
    ]


# --------------------------------------------------------------------------- #
# canonical turnover: CASH is never a tradable leg
# --------------------------------------------------------------------------- #
def test_etf_leg_turnover_excludes_cash_everywhere():
    # ETF legs only: |0-0.7| + |0.5-0| = 1.2; CASH 0.3->0.5 contributes 0.
    assert etf_leg_turnover({"CCC": 0.7, "CASH": 0.3}, {"DDD": 0.5, "CASH": 0.5}) == 1.2
    # From all-cash into a book with explicit CASH: only the ETF leg counts.
    assert etf_leg_turnover({"CASH": 1.0}, {"CCC": 0.7, "CASH": 0.3}) == 0.7
    # Full ETF-to-ETF switch: 2.0 regardless of where CASH sits.
    assert etf_leg_turnover({"AAA": 1.0}, {"BBB": 1.0}) == 2.0
    assert etf_leg_turnover({}, {"CASH": 1.0}) == 0.0


def test_normalize_entry_targets_styles_and_failures():
    # A4-style: targets untouched, cash from cash_weight.
    assert normalize_entry_targets(_entries_a4()[0]) == ({"AAA": 0.6}, 0.4)
    # A5-style: explicit CASH leg stripped, cash honored from the leg.
    assert normalize_entry_targets(_entries_a5()[0]) == ({"CCC": 0.7}, 0.3)
    # Explicit CASH with NO cash_weight key: the leg is honored, not zeroed.
    assert normalize_entry_targets(
        {"entry_type": "FILL", "fill_date": "x", "targets": {"CCC": 0.7, "CASH": 0.3}},
    ) == ({"CCC": 0.7}, 0.3)
    # FORCE_FLAT: empty targets, cash 1.0.
    assert normalize_entry_targets(_entries_a4()[2]) == ({}, 1.0)
    # Fail-closed: explicit CASH disagreeing with cash_weight is an error.
    with pytest.raises(ValueError, match="disagrees"):
        normalize_entry_targets({"entry_type": "FILL", "fill_date": "x",
                                 "targets": {"CCC": 0.7, "CASH": 0.3},
                                 "cash_weight": 0.4})


# --------------------------------------------------------------------------- #
# hand-computed golden: A4-style book
# --------------------------------------------------------------------------- #
def test_golden_a4_style_book():
    res = value_book(_entries_a4(), RAW_A4, DIST, {}, S4, cost_bps=100.0)
    assert len(res.period_pnls) == 3                     # incl. final (s5, 0.0)
    assert abs(res.period_pnls[0][1] - 0.05964) < 1e-9
    assert abs(res.period_pnls[1][1] - 0.0209042176) < 1e-9
    assert res.period_pnls[2] == (S4[4], 0.0)
    assert abs(res.total_pnl - 0.0575861768192) < 1e-9
    assert abs(res.expectancy - 0.026848072533333335) < 1e-12
    assert abs(res.total_cost - 0.0229580407808) < 1e-9
    assert res.profit_factor is None                      # no losing periods
    assert abs(res.max_drawdown - 0.008) < 1e-12
    assert abs(res.equity_curve[S4[0]] - 0.994) < 1e-12   # fill-1 cost visible
    assert abs(res.equity_curve[S4[3]] - 1.0661150976) < 1e-9
    assert abs(res.equity_curve[S4[4]] - 1.0575861768192) < 1e-9
    # per-fill records: (date, etf turnover, cost), CASH never in turnover
    assert res.fill_costs[0] == (S4[0], 0.6, 0.006)
    assert abs(res.fill_costs[1][1] - 0.8) < 1e-12
    assert abs(res.fill_costs[1][2] - 0.00842912) < 1e-12
    assert abs(res.fill_costs[2][2] - 0.0085289207808) < 1e-12
    assert len(res.fill_costs) == 3


def test_golden_a5_style_book_explicit_cash_leg():
    res = value_book(_entries_a5(), RAW_A5, DIST, {}, S5, cost_bps=50.0)
    assert len(res.period_pnls) == 2
    assert abs(res.period_pnls[0][1] - (-0.0697550)) < 1e-9
    assert abs(res.period_pnls[1][1] - 0.02302961325) < 1e-9
    assert abs(res.total_pnl - (-0.05578585675)) < 1e-9
    assert abs(res.total_cost - 0.009060470) < 1e-9
    assert abs(res.expectancy - (-0.023362693375)) < 1e-9
    assert abs(res.profit_factor - 0.02302961325 / 0.0697550) < 1e-9
    assert abs(res.max_drawdown - (0.9965 - 0.921184530) / 0.9965) < 1e-9
    # The A5 cash-leg change 0.3 -> 0.5 must NOT appear in any fill turnover.
    assert res.fill_costs[0] == (S5[0], 0.7, 0.0035)
    assert abs(res.fill_costs[1][1] - 1.2) < 1e-12
    assert abs(res.fill_costs[1][2] - 0.005560470) < 1e-9
    assert len(res.fill_costs) == 2


def test_books_with_and_without_explicit_cash_valued_identically():
    """A4-style and A5-style spellings of the SAME book are identical.

    {CCC:0.7} + cash_weight 0.3  ==  {CCC:0.7, CASH:0.3} + cash_weight 0.3.
    """
    a4_style = value_book(
        [{"entry_type": "FILL", "fill_date": S5[0], "targets": {"CCC": 0.7},
          "cash_weight": 0.3}],
        RAW_A5, DIST, {}, S5, cost_bps=50.0)
    a5_style = value_book([_entries_a5()[0]], RAW_A5, DIST, {}, S5, cost_bps=50.0)
    assert a4_style.total_pnl == a5_style.total_pnl
    assert a4_style.total_cost == a5_style.total_cost
    assert a4_style.equity_curve == a5_style.equity_curve
    assert a4_style.fill_costs == a5_style.fill_costs


# --------------------------------------------------------------------------- #
# cost charged exactly once (regression: must fail on the double-add pattern)
# --------------------------------------------------------------------------- #
def test_cost_accumulator_equals_fsum_of_per_fill_costs():
    for res in (value_book(_entries_a4(), RAW_A4, DIST, {}, S4, cost_bps=100.0),
                value_book(_entries_a5(), RAW_A5, DIST, {}, S5, cost_bps=50.0)):
        # Exact once-only accumulation, pinned via assert_reconciles and here
        # via a direct identity: doubling the accumulator MUST be detected.
        assert_reconciles(res)
        cost_sum = sum(c for _, _, c in res.fill_costs)
        assert abs(res.total_cost - cost_sum) <= 1e-12 * max(1.0, abs(cost_sum))


def test_reconcile_fails_on_reintroduced_double_add_pattern():
    res = value_book(_entries_a5(), RAW_A5, DIST, {}, S5, cost_bps=50.0)
    broken = res
    broken.total_cost = 2.0 * res.total_cost        # the V2 sidecar defect (b)
    with pytest.raises(AttributionBreakError, match="double-add"):
        assert_reconciles(broken)


def test_equity_deduction_and_accumulator_agree():
    """Equity is deducted exactly the accumulated cost: curve[0] pinpoints it."""
    res = value_book(_entries_a5(), RAW_A5, DIST, {}, S5, cost_bps=50.0)
    first_fill = res.fill_costs[0]
    assert abs((1.0 - res.equity_curve[S5[0]]) - first_fill[2]) < 1e-15
    # terminal equity reconciles: 1 + contributions - costs = equity_final
    identity = 1.0 + sum(res.symbol_contribution.values()) - res.total_cost
    assert abs(identity - (1.0 + res.total_pnl)) <= ATTRIBUTION_TOLERANCE


# --------------------------------------------------------------------------- #
# equivalence with the V2 canonical harness (bit-identical on valid inputs)
# --------------------------------------------------------------------------- #
def test_equivalence_with_harness_a4_style():
    mine = value_book(_entries_a4(), RAW_A4, DIST, {}, S4, cost_bps=100.0)
    theirs = harness_value_book(_entries_a4(), RAW_A4, DIST, {}, S4, cost_bps=100.0)
    assert mine.equity_curve == theirs.equity_curve
    assert mine.period_pnls == theirs.period_pnls
    assert mine.total_pnl == theirs.total_pnl
    assert mine.total_cost == theirs.total_cost
    assert mine.expectancy == theirs.expectancy
    assert mine.profit_factor == theirs.profit_factor
    assert mine.max_drawdown == theirs.max_drawdown


def test_equivalence_with_harness_a5_style_explicit_cash():
    mine = value_book(_entries_a5(), RAW_A5, DIST, {}, S5, cost_bps=50.0)
    theirs = harness_value_book(_entries_a5(), RAW_A5, DIST, {}, S5, cost_bps=50.0)
    assert mine.equity_curve == theirs.equity_curve
    assert mine.period_pnls == theirs.period_pnls
    assert mine.total_pnl == theirs.total_pnl
    assert mine.total_cost == theirs.total_cost          # CASH stripped, charged once
    assert mine.max_drawdown == theirs.max_drawdown


def test_equivalence_with_harness_variants():
    for kwargs in ({"adverse_bps": 25.0},
                   {"extra_delay_sessions": 1},
                   {"excluded_symbol": "AAA"},
                   {"adverse_bps": 10.0, "extra_delay_sessions": 2}):
        mine = value_book(_entries_a4(), RAW_A4, DIST, {}, S4, cost_bps=100.0, **kwargs)
        theirs = harness_value_book(_entries_a4(), RAW_A4, DIST, {}, S4,
                                    cost_bps=100.0, **kwargs)
        assert mine.equity_curve == theirs.equity_curve, kwargs
        assert mine.total_pnl == theirs.total_pnl, kwargs
        assert mine.total_cost == theirs.total_cost, kwargs


def test_equivalence_with_harness_distributions():
    mine = value_book(_entries_a4(), RAW_A4, DIST_AAA, {}, S4, cost_bps=100.0)
    theirs = harness_value_book(_entries_a4(), RAW_A4, DIST_AAA, {}, S4, cost_bps=100.0)
    assert mine.equity_curve == theirs.equity_curve
    assert mine.total_pnl == theirs.total_pnl
    assert mine.total_cost == theirs.total_cost
