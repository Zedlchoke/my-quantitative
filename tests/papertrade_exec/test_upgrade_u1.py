"""PAPERDESK UPGRADE V2 — U1 battery: FEE-ONCE locks (owner work package
2026-10-21).

Finding (research/control/PAPERDESK-FIXALL-NCAA-V1/FEE_ONCE_FINDING.md):
the PM taker fee 0.05·p·(1−p) is deducted EXACTLY ONCE in BOTH lanes —
  * standard: walk_ask bakes it into spend -> vwap -> odds = 1/vwap
    (pm_moneyline.py:240-247, execute.py:1533/1562);
  * WSL: pinned walk -> fee_total, fee_law_d_eff = shares/(spend+fee)
    (wsl_lane.py:362-373, R5-2).
The flat COST_FRICTION 0.02 is a frozen friction BUFFER subtracted once at
the EV gate in BOTH lanes (pinned risk.py:22-24/:133) — not a second fee,
never in settlement. These tests LOCK that behavior with hand-computed
numbers (pure functions; walk_ask network mocked; no ledger, no pins).
"""
from __future__ import annotations

import io
import json
import sys
import urllib.request
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from research.papertrade_exec import decision_pipeline as DP      # noqa: E402
from research.papertrade_exec import laws                          # noqa: E402
from research.papertrade_exec import pm_moneyline as PML           # noqa: E402
from research.papertrade_exec import wsl_lane                      # noqa: E402


# ------------------------------------------------- T-U1-A: standard walk ----

def test_u1_a_standard_walk_bakes_fee_once_into_vwap(tmp_path, monkeypatch):
    """One-level book at ask 0.50, stake 500c. HAND MATH:
    fee/share = 0.05·0.50·0.50 = 0.0125; cost/share = 0.50 + 0.0125 = 0.5125;
    500c = $5 -> 5 shares; spend = 5·0.5125 = 2.5625 ($256c, fee 6.25c);
    vwap = 2.5625/5 = 0.5125 (FEE-INCLUSIVE); the stored odds law
    (execute.py:1533 odds = round(1/vwap, 6)) = 1/0.5125 = 1.95122 — the
    fee enters ONCE, in the denominator. Raw 1/0.50 = 2.0 would be the
    no-fee counterfactual (2.44% richer) — locked against."""
    book = {"asks": [{"price": "0.50", "size": "500"}]}

    class _Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(PML.urllib.request, "urlopen",
                        lambda req, timeout=30: _Resp(json.dumps(book)
                                                      .encode()))
    walk = PML.walk_ask("tok", stake_cents=500, data_root=tmp_path)
    assert walk["filled_shares"] == 5.0
    assert walk["fee_cents"] == 6                      # 6.25c -> 6c display
    assert walk["vwap_ask"] == pytest.approx(0.5125)   # cost+fee per share
    odds_stored = round(1.0 / walk["vwap_ask"], 6)     # execute.py:1533 law
    assert odds_stored == 1.95122
    # fee-once FORMULA lock: odds == 1/(a + 0.05·a·(1−a)); once — not twice
    a = 0.50
    assert odds_stored == round(1.0 / (a + laws.PM_TAKER_FEE_RATE * a *
                                       (1 - a)), 6)
    assert odds_stored != round(1.0 / (a + 2 * laws.PM_TAKER_FEE_RATE * a *
                                       (1 - a)), 6)  # double-fee refuted
    assert odds_stored != 2.0                          # no-fee refuted


# ------------------------------------------- T-U1-B: standard gate EV math ---

def test_u1_b_standard_gate_ev_fee_once_flat_buffer_once():
    """Gate math via decision_pipeline.check_deterministic_gates (the pure
    standard-lane evaluator). HAND MATH with the stored odds 1.95122
    (fee once, from T-U1-A):
      EV = p·d − 1 − FLAT_FEE_PRE_CUTOVER(0.02)
      p=0.55: 0.55·1.95122 = 1.073171; 1.073171 − 1.02 = +0.053171 >= 0.05
              -> G_EV PASSES (marginal but lawful bet);
      p=0.52: 0.52·1.95122 = 1.0146344; 1.0146344 − 1.02 = −0.0053656
              -> NO_EDGE (G_EV fails).
    The flat buffer is applied ONCE: p·d − 1 − 0.04 would be −0.006829 and
    must NOT be the gate's EV (a double-counted buffer is refuted)."""
    p = {"HOME": 0.55}
    odds = {"HOME": 1.95122}
    base = dict(stake_cents=500, equity_cents=100000,
                open_exposure_cents=0, open_cap_cents=50000,
                drawdown_frac=0.0, drawdown_paused=False,
                snapshot_before_anchor=True, anchor_passed=False,
                quote_present=True, depth_walked=True, fees_once=True)
    ok, gates, ev = DP.check_deterministic_gates(
        p=p, odds=odds, chosen_leg="HOME", **base)
    assert ev == pytest.approx(0.053171, abs=1e-9)
    assert ev == pytest.approx(0.55 * 1.95122 - 1.0 -
                               laws.FLAT_FEE_PRE_CUTOVER, abs=1e-12)
    g_ev = next(g for g in gates if g["gate"] == "G_EV")
    assert g_ev["pass"] is True
    assert ok is True
    # buffer ONCE: 0.04 total friction is NOT what the gate computes
    assert ev != pytest.approx(0.55 * 1.95122 - 1.04, abs=1e-6)
    # sub-threshold: the fee-inclusive odds + buffer kill the weak edge
    ok2, gates2, ev2 = DP.check_deterministic_gates(
        p={"HOME": 0.52}, odds=odds, chosen_leg="HOME", **base)
    assert ev2 == pytest.approx(-0.0053656, abs=1e-9)
    assert next(g for g in gates2 if g["gate"] == "G_EV")["pass"] is False
    assert ok2 is False
    # the walk's fee-once guarantee is a gate INPUT: fees_once=False blocks
    ok3, gates3, _ = DP.check_deterministic_gates(
        p=p, odds=odds, chosen_leg="HOME", **{**base, "fees_once": False})
    assert ok3 is False
    assert next(g for g in gates3 if g["gate"] == "G_FEES")["pass"] is False


# --------------------------------------------------- T-U1-C: WSL fee law ----

def test_u1_c_wsl_fee_law_d_eff_once_and_settle_exact():
    """WSL lane via wsl_lane.fee_law_d_eff (pure). HAND MATH: single level
    ask 0.40, 10 shares taken: fee/share = 0.05·0.40·0.60 = 0.012, fee_total
    = 0.12; spend (cost only) = 10·0.40 = 4.00; outlay = 4.00 + 0.12 = 4.12
    (= the walked stake 412c, walk_budget_for_stake law B + F(B) = stake).
      d_eff = shares/outlay = 10/4.12 = 2.427184466…
      fee ONCE in the denominator: shares/spend = 2.5 is the NO-fee
      counterfactual and must NOT be d_eff.
      Pinned settle (risk.py:276) at stake 412c:
        pnl_win = round(412·(d_eff−1)) = round(412·5.88/4.12) = 588c
      equals the true net win shares·$1 − outlay = 10.00 − 4.12 = 5.88 $
      = 588c EXACTLY — the payout carries NO second fee."""
    walk = {"spend_usdc": 4.00, "fee_total_usdc": 0.12,
            "filled_shares": 10.0}
    assert walk["fee_total_usdc"] == pytest.approx(
        laws.PM_TAKER_FEE_RATE * 0.40 * (1 - 0.40) * 10.0)
    d_eff = wsl_lane.fee_law_d_eff(walk)
    assert d_eff == pytest.approx(10.0 / 4.12)
    assert d_eff == pytest.approx(2.427184466, abs=1e-8)
    assert d_eff != pytest.approx(10.0 / 4.00)          # fee-missing refuted
    assert d_eff != pytest.approx(10.0 / (4.00 + 0.24))  # fee-twice refuted
    # the pinned settle law applied to this walk is the true net win
    stake_cents = 412                                    # = 100·outlay
    pnl = int(round(stake_cents * (d_eff - 1.0)))        # risk.py:276 shape
    assert pnl == 588
    assert pnl == pytest.approx(100 * (10.0 - 4.12))     # shares − outlay
