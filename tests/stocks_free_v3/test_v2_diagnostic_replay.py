"""V2 diagnostic replay: the old double-count pattern is detected (A2, del. 9).

Recomputes the V2 A5-style attribution on the synthetic A5-style hand fixture
(explicit CASH inside targets) under (i) the canonical path and (ii) a
faithful replica of the STOCKS-FREE-V2 staged-runner sidecar defect pattern
documented in research/audits/stocks_free_v2/z9_a7_terminal/AUDIT_REPORT.md:

  defect (a)  the turnover union ``set(targets) | set(weights) - {"CASH"}``
              binds as ``set(targets) | (set(weights) - {"CASH"})`` because
              ``-`` precedes ``|`` -- the explicit CASH leg inside A5 targets
              is therefore COUNTED as a tradable leg;
  defect (b)  ``total_cost += cost`` executed twice -- equity is deducted
              once but the accumulator doubles.

This is a DIAGNOSTIC REPLAY ONLY: it runs on a synthetic fixture, entirely in
memory; it rewrites no V2 scored artifact, creates no V2 trial, touches no
ledger, and the replica never enters research/assets/stocks/factory.py.

Hand computation of the replica on the A5 fixture (cost 50 bps; canonical
values in test_factory_valuation.py):
  e1: buggy turnover |0.7-0| + |0.3-1.0| = 1.4 (CASH counted!),
      cost 1.0*1.4*0.005 = 0.007 -- exactly 2x the canonical 0.0035,
      equity 0.993, accumulator 0.014 (added twice)
  e2: CCC -10% x w0.7: contribution 0.993*0.7*(-0.10) = -0.0695100,
      equity 0.993*0.93 = 0.9234900
  e3: buggy turnover |0-0.7| + |0.5-0| + |0.5-0.3| = 1.4 (CASH 0.3->0.5
      counted!), cost 0.9234900*1.4*0.005 = 0.006464430,
      equity 0.917025570, accumulator 0.014 + 2*0.006464430 = 0.026928860
  e4: contribution DDD 0.917025570*0.5*0.05 = 0.022925639250,
      equity 0.939951209250, buggy pnl -0.060048790750
  replica crosscheck residual = (-0.046584360750) - 0.026928860
                                - (-0.060048790750) = -0.013464430
  (exactly deducted 0.013464430 - accumulated 0.026928860: the double-add is
  isolated by the identity) -> |residual| = 0.013464430 >> 1e-12:
  OLD PATTERN DETECTED, while the canonical residual on the same data is
  ~1e-16 (<= frozen 1e-12).
"""
import math

import pytest

from research.assets.stocks.factory import (
    ATTRIBUTION_TOLERANCE,
    AttributionBreakError,
    ValuationResult,
    assert_reconciles,
    value_book,
)

from tests.stocks_free_v3.test_factory_valuation import (
    DIST, RAW_A5, S5, _entries_a5,
)

COST_BPS = 50.0


def _v2_sidecar_replica(entries, raw_close, sessions, cost_bps):
    """DIAGNOSTIC replica of the V2 sidecar defect pattern -- never for scoring.

    Encodes exactly the two documented defects on top of otherwise identical
    day-return/fill mechanics: the CASH leg of A5-style targets survives the
    turnover union (precedence bug, defect a) and the cost accumulator is
    incremented twice per fill (defect b).  Weights are initialized like the
    harness ({CASH: 1.0}) and rebuilt with the explicit CASH leg.  Returns
    ``(contribution, total_cost, fill_turnovers, deducted_costs, equity)``.
    """
    fill_map = {e["fill_date"]: e for e in entries}
    weights: dict = {"CASH": 1.0}
    equity = 1.0
    contribution: dict = {}
    total_cost = 0.0
    fill_turnovers, deducted = [], []
    first = True
    for d in sessions:
        if not first:
            port = 0.0
            for s, w in weights.items():
                if s == "CASH" or not w or d not in raw_close.get(s, {}):
                    continue
                prev = max(x for x in raw_close[s] if x < d)
                r = raw_close[s][d] / raw_close[s][prev] - 1.0
                port += w * r
                contribution[s] = contribution.get(s, 0.0) + equity * w * r
            equity *= (1.0 + port)
        else:
            first = False
        if d in fill_map:
            targets_all = dict(fill_map[d]["targets"])          # CASH included
            # defect (a): precedence bug, CASH leg inside targets survives
            legs = set(targets_all) | set(weights) - {"CASH"}
            turnover = sum(abs(targets_all.get(s, 0.0) - weights.get(s, 0.0))
                           for s in legs)
            cost = equity * turnover * cost_bps / 10_000.0
            equity -= cost                                      # deducted once
            total_cost += cost
            total_cost += cost                                  # defect (b)
            fill_turnovers.append(turnover)
            deducted.append(cost)
            etf = {s: w for s, w in targets_all.items() if s != "CASH"}
            weights = dict(targets_all, CASH=1.0 - sum(etf.values()))
    return contribution, total_cost, fill_turnovers, deducted, equity


def test_canonical_reconciliation_on_the_replay_fixture():
    res = value_book(_entries_a5(), RAW_A5, DIST, {}, S5, cost_bps=COST_BPS)
    assert abs(res.attribution_residual) <= ATTRIBUTION_TOLERANCE
    assert abs(res.attribution_residual) < 1e-14
    assert_reconciles(res)
    assert abs(res.total_pnl - (-0.05578585675)) < 1e-9


def test_defect_a_cash_leg_turnover_inflation_detected():
    res = value_book(_entries_a5(), RAW_A5, DIST, {}, S5, cost_bps=COST_BPS)
    _, _, fill_turnovers, deducted, _ = _v2_sidecar_replica(
        _entries_a5(), RAW_A5, S5, COST_BPS)
    # canonical: ETF legs only (0.7 + 1.2 = 1.9); replica: CASH legs counted
    canonical_turnover = sum(t for _, t, _ in res.fill_costs)
    assert abs(canonical_turnover - 1.9) < 1e-12
    assert abs(sum(fill_turnovers) - 2.8) < 1e-12
    # first fill exactly doubles ("roughly doubling per-fill cost", audit (a))
    assert abs(fill_turnovers[0] / res.fill_costs[0][1] - 2.0) < 1e-12
    # ...and the inflated cost was actually deducted from equity
    assert abs(sum(deducted) - 0.013464430) < 1e-9
    assert sum(deducted) - res.total_cost > 3e-3        # 0.013464 vs 0.009060


def test_defect_b_double_add_detected_by_the_identity():
    contrib, total_cost, _, deducted, equity = _v2_sidecar_replica(
        _entries_a5(), RAW_A5, S5, COST_BPS)
    pnl = equity - 1.0
    assert abs(pnl - (-0.060048790750)) < 1e-9
    residual = math.fsum(contrib.values()) - total_cost - pnl
    # the residual isolates the double-add EXACTLY: deducted - accumulated
    assert abs(residual - (-0.013464430)) < 1e-9
    assert abs(residual) > ATTRIBUTION_TOLERANCE        # DETECTED (>> 1e-12)
    # the frozen gate refuses such a result
    broken = ValuationResult(
        equity_curve={}, period_pnls=[], total_pnl=pnl, expectancy=0.0,
        profit_factor=None, max_drawdown=0.0, total_cost=total_cost,
        fill_costs=[("synthetic", 1.4, c) for c in deducted],
        symbol_contribution=dict(contrib),
        attribution_residual=residual)
    with pytest.raises(AttributionBreakError, match="double-add"):
        assert_reconciles(broken)


def test_repair_changes_the_measured_result():
    """Old numbers were corrupted: corrected pnl/cost differ from the replica."""
    res = value_book(_entries_a5(), RAW_A5, DIST, {}, S5, cost_bps=COST_BPS)
    _, total_cost, _, _, equity = _v2_sidecar_replica(
        _entries_a5(), RAW_A5, S5, COST_BPS)
    replica_pnl = equity - 1.0
    assert res.total_pnl - replica_pnl > 3e-3
    assert abs(res.total_cost - total_cost) > 1e-2      # 0.009060 vs 0.026929
    assert abs(res.attribution_residual) <= ATTRIBUTION_TOLERANCE
