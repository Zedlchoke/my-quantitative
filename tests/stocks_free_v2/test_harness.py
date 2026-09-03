"""Hand-computed goldens for the STOCKS-FREE-V2 shared harness (A1, Z6).

Valuation contract (documented in harness.py): rebalance AT the fill close
(fill day earns no same-day return on new weights); day returns use the
weights set at the previous close; turnover counts ETF-leg changes only;
cost = equity x ETF-turnover x bps / 1e4 deducted at the fill.

Fixture A (two fills): sessions s1..s5; AAA raw 100,110,110,--,--; BBB raw
50,50,50,52,52. Book: FILL s1 {AAA:1.0}; FILL s3 {BBB:1.0}; FORCE_FLAT s5.
Hand computation (cost 100 bps):
  s1 fill: turnover 1.0, cost 0.01, equity 0.99
  s2: x1.10 -> 1.089            (AAA +10%)
  s3: x1.00 -> 1.089 (AAA flat); fill BBB: ETF turnover |1-0|+|0-... = 1.0
      + AAA close 1.0 -> total 2.0? No: weights at s2 close are {AAA:1.0},
      targets {BBB:1.0} => ETF turnover = 2.0, cost 0.02 -> equity 1.089*0.98
      = 1.06722 ; period1 pnl = 1.06722-0.99 = 0.07722
  s4: BBB 52/50-1 = +4% -> 1.06722*1.04 = 1.1099088
  s5: BBB flat -> 1.1099088; FORCE_FLAT: turnover 1.0, cost 0.01099088 ->
      equity 1.09891792 ; period2 pnl = 1.1099088-1.06722 = 0.0426888
  total_pnl = 0.09891792 ; expectancy = 0.04945896 ; PF None (no losses)
  MDD: peak 1.1099088 (s4/s5 curve), trough 0.99 -> (1.1099088-0.99)/1.1099088
"""
from research.stocks_free_v2.harness import (
    TrialLedger, canonical_json, reconstruct_tr, s1_denied, value_book,
)

S = ["2020-01-06", "2020-01-07", "2020-01-08", "2020-01-09", "2020-01-10"]

RAW = {
    "AAA": {"2020-01-06": 100.0, "2020-01-07": 110.0, "2020-01-08": 110.0},
    "BBB": {"2020-01-06": 50.0, "2020-01-07": 50.0, "2020-01-08": 50.0,
            "2020-01-09": 52.0, "2020-01-10": 52.0},
}
DIST = {}


def _entries():
    return [
        {"entry_type": "FILL", "fill_date": S[0], "targets": {"AAA": 1.0},
         "cash_weight": 0.0, "turnover_one_way": 1.0},
        {"entry_type": "FILL", "fill_date": S[2], "targets": {"BBB": 1.0},
         "cash_weight": 0.0, "turnover_one_way": 2.0},
        {"entry_type": "FORCE_FLAT", "fill_date": S[4], "targets": {},
         "cash_weight": 1.0, "turnover_one_way": 1.0},
    ]


def test_golden_valuation_two_fills():
    res = value_book(_entries(), RAW, DIST, {}, S, cost_bps=100.0)
    # period PnL convention: net of the cost charged at the period's START
    # (the rebalance into the book); the terminal flat cost appears only in
    # total/curve.
    assert abs(res.period_pnls[0][1] - 0.099) < 1e-9
    assert abs(res.period_pnls[1][1] - 0.0426888) < 1e-9
    assert abs(res.total_pnl - 0.09880971) < 1e-8
    assert abs(res.expectancy - 0.0472296) < 1e-8
    assert abs(res.total_cost - 0.042879088) < 1e-8
    assert res.profit_factor is None  # no losing periods -> PF undefined
    # MDD: peak 1.089 (s2) -> trough 1.06722 (s3, post-cost) = 2%
    assert abs(res.max_drawdown - (1.089 - 1.06722) / 1.089) < 1e-12
    assert abs(res.equity_curve[S[0]] - 0.99) < 1e-12   # cost visible in curve
    assert abs(res.equity_curve[S[3]] - 1.1099088) < 1e-9


def test_stress_cost_reduces_pnl():
    base = value_book(_entries(), RAW, DIST, {}, S, cost_bps=100.0)
    stressed = value_book(_entries(), RAW, DIST, {}, S, cost_bps=200.0)
    assert stressed.total_pnl < base.total_pnl
    # base costs: 1.0 turn @s1 = 0.01; 2.0 turns @s3 = 0.02178; 1.0 @s5 = 0.0111
    assert abs(base.total_cost - 0.042879088) < 1e-8


def test_adverse_bps_reduces_pnl():
    base = value_book(_entries(), RAW, DIST, {}, S, cost_bps=100.0)
    adverse = value_book(_entries(), RAW, DIST, {}, S, cost_bps=100.0, adverse_bps=50.0)
    assert adverse.total_pnl < base.total_pnl


def test_extra_delay_shifts_fill():
    base = value_book(_entries(), RAW, DIST, {}, S, cost_bps=100.0)
    delayed = value_book(_entries(), RAW, DIST, {}, S, cost_bps=100.0,
                         extra_delay_sessions=1)
    assert delayed.total_pnl != base.total_pnl


def test_drop_one_symbol_goes_to_cash_cost_free():
    res = value_book(_entries(), RAW, DIST, {}, S, cost_bps=100.0,
                     excluded_symbol="AAA")
    # s1 fill holds nothing (all cash, zero ETF turnover, zero cost);
    # s3 fills BBB exactly as before (turnover 1.0, cost at equity 1.0).
    assert res.period_pnls[0][1] == 0.0
    assert abs(res.period_pnls[1][1] - 0.0396) < 1e-9
    assert abs(res.total_pnl - 0.019304) < 1e-8


def test_reconstruct_tr_with_distribution_and_split():
    raw = {"2020-01-06": 100.0, "2020-01-07": 50.0}   # 2:1 split on 01-07
    tr = reconstruct_tr(raw, {"2020-01-07": 0.0}, {"2020-01-07": 2.0})
    assert abs(tr["2020-01-07"] - 1.0) < 1e-12        # split is TR-neutral
    raw2 = {"2020-01-06": 100.0, "2020-01-07": 99.0}  # -1% price, $1/share dist
    tr2 = reconstruct_tr(raw2, {"2020-01-07": 1.0}, {})
    assert abs(tr2["2020-01-07"] - 1.0) < 1e-12       # dist exactly offsets


def test_s1_denial():
    assert s1_denied("data/book_S1_2025-08-15.json", "2025-08-01", "2026-07-31")
    assert s1_denied("data/s1/partition.json", "2025-08-01", "2026-07-31")
    assert s1_denied("data/S1_snapshot.bin", "2025-08-01", "2026-07-31")
    assert s1_denied("data/2025-12-05_close.json", "2025-08-01", "2026-07-31")
    assert not s1_denied("data/s0/2025-07-31.json", "2025-08-01", "2026-07-31")
    assert not s1_denied("data/s0/2018-04-04.json", "2025-08-01", "2026-07-31")


def test_ledger_counters_and_replay():
    ledger = TrialLedger()
    key = "ARM_X::digest"
    ledger.compute_recorded(key)
    ledger.compute_recorded(key + "::other")
    assert ledger.observed == 2
    art = {"anything": "finite"}
    assert ledger.publish(key, art) is True          # first publication
    assert ledger.publish(key, art) is False         # idempotent replay
    assert ledger.observed == 2                      # replay: zero delta
    assert len(ledger.published_keys) == 1


def test_canonical_json_deterministic():
    a = canonical_json({"b": 1, "a": [2, 3]})
    b = canonical_json({"a": [2, 3], "b": 1})
    assert a == b and a == '{"a":[2,3],"b":1}'
