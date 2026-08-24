"""Hand-fixture tests for the shared-capital portfolio engine (Sprint V4, A2).

Synthetic 3-symbol (plus benchmark) 15m worlds with hand-computed order math.
Bar-stamp convention mirrors real catalog data: the bar covering slot k of a
day closes at stamp ``midnight + k*900e9 - 1`` ns. The daily-close bar is the
23:45-slot bar (last bar at/before each midnight); the first bar of a day
(slot 1, stamp ``C + 900e9 - 1``) is the execution event for cutoff ``C``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from research.portfolio_engine import run_shared_capital_backtest
from research.xsect_rank import compute_target_weights

DAY_NS = 86_400_000_000_000
BAR_NS = 900_000_000_000
T0 = 1_755_475_200_000_000_000  # 2025-08-18T00:00:00Z (UTC midnight)

SYMS = ["ETHUSDT", "SOLUSDT", "XRPUSDT"]
EXT_SYMS = ["AAAUSDT", "BBBUSDT"]

TEN_SYMS = [f"S{i}USDT" for i in range(10)]
ALL_SYMS = SYMS + EXT_SYMS + ["BTCUSDT"] + TEN_SYMS

ENGINE_KW = dict(
    tick_size={s: 0.01 for s in ALL_SYMS},
    step_size={s: 0.001 for s in ALL_SYMS},
    min_notional=10.0,
    fee_taker=0.0005,
    slippage_ticks=1,
)


def zero_sum_wf(longs, shorts, weight=0.2):
    """Deterministic OK-result weight_fn: legs scaled to sum to exactly zero."""
    ws = weight * len(longs) / len(shorts) if shorts else 0.0
    return lambda C: {
        "status": "OK", "signal_cutoff_ns": C, "scores": {},
        "longs": [[s, weight] for s in longs],
        "shorts": [[s, -ws] for s in shorts],
    }


def stamp(day: int, slot: int) -> int:
    """Close stamp of the bar covering slot `slot` of day `day`."""
    return T0 + day * DAY_NS + slot * BAR_NS - 1


def build_world(closes: dict[str, dict[tuple[int, int], float]]):
    bars = {
        sym: [
            (stamp(d, s), px, px, px, px, 10.0)
            for (d, s), px in sorted(events.items())
        ]
        for sym, events in closes.items()
    }
    daily: dict[str, list[tuple[int, float]]] = {}
    for sym, events in closes.items():
        pts = [
            (stamp(d, 95), px)
            for (d, s), px in sorted(events.items())
            if s == 95 and stamp(d, 95) <= _max_boundary(events)
        ]
        daily[sym] = pts
    return bars, daily


def _max_boundary(events: dict[tuple[int, int], float]) -> int:
    return max(stamp(d, s) for d, s in events)


def rank_wf(daily, *, lookback=1, long_count=1, short_count=1, weight=0.25,
            min_eligible=3):
    return lambda C: compute_target_weights(
        daily, C, lookback_days=lookback, long_count=long_count,
        short_count=short_count, weight=weight, min_eligible=min_eligible,
    )


def write_funding_bundle(root: Path, symbol: str, rows: list[tuple[int, str]],
                         start_ms=0, end_ms=4_000_000_000_000) -> None:
    d = root / symbol
    d.mkdir(parents=True, exist_ok=True)
    payload = {
        "requested_start_ms": start_ms,
        "requested_end_ms": end_ms,
        "rows": [{"fundingTime": ms, "fundingRate": rate} for ms, rate in rows],
    }
    (d / "funding.json").write_text(json.dumps(payload))


def base_world_extra_day() -> tuple[dict, dict]:
    """World where C2 opens ETH-long/SOL-short, C3 flips both."""
    closes = {
        "ETHUSDT": {
            (0, 95): 100.0, (1, 95): 110.0, (2, 1): 100.50,
            (2, 95): 80.0, (3, 1): 81.0,
        },
        "SOLUSDT": {
            (0, 95): 100.0, (1, 95): 90.0, (2, 1): 99.50,
            (2, 95): 130.0, (3, 1): 129.0,
        },
        "XRPUSDT": {
            (0, 95): 100.0, (1, 95): 100.0, (2, 1): 100.0,
            (2, 95): 100.0, (3, 1): 100.0,
        },
    }
    return build_world(closes)


# --------------------------------------------------------------------------- #
# Order math: fees + slippage exact decimals
# --------------------------------------------------------------------------- #
def test_order_math_fees_and_slippage_exact():
    bars, daily = base_world_extra_day()
    res = run_shared_capital_backtest(
        bars, daily, rank_wf(daily), initial_capital=100_000.0, **ENGINE_KW
    )

    # C2 executes at bar (2,1): long ETH (top score ln(110/100)), short SOL.
    qty_eth = 248.756  # floor(0.25*100000/100.50, step 0.001)
    qty_sol = 251.256  # floor(0.25*100000/99.50, step 0.001)
    o_eth, o_sol = res.orders[0], res.orders[1]
    assert (o_eth["symbol"], o_eth["side"], o_eth["kind"]) == ("ETHUSDT", "BUY", "open")
    assert o_eth["qty"] == pytest.approx(qty_eth, abs=1e-12)
    assert o_eth["ref_price"] == pytest.approx(100.50)
    assert o_eth["fill_price"] == pytest.approx(100.51)  # +1 tick adverse
    assert o_eth["slippage_cost"] == pytest.approx(qty_eth * 0.01, abs=1e-12)
    assert o_eth["fee"] == pytest.approx(qty_eth * 100.51 * 0.0005, abs=1e-9)
    assert o_eth["rejected_reason"] is None

    assert (o_sol["symbol"], o_sol["side"], o_sol["kind"]) == ("SOLUSDT", "SELL", "open")
    assert o_sol["qty"] == pytest.approx(qty_sol, abs=1e-12)
    assert o_sol["fill_price"] == pytest.approx(99.49)  # -1 tick adverse
    assert o_sol["fee"] == pytest.approx(qty_sol * 99.49 * 0.0005, abs=1e-9)
    assert o_sol["slippage_cost"] == pytest.approx(qty_sol * 0.01, abs=1e-12)

    fee_eth = qty_eth * 100.51 * 0.0005
    fee_sol = qty_sol * 99.49 * 0.0005
    cash_expected = (
        100_000.0
        - qty_eth * 100.51 - fee_eth
        + qty_sol * 99.49 - fee_sol
    )
    c2_ledger = next(r for r in res.portfolio_ledger if r["ts"] == stamp(2, 1))
    assert c2_ledger["cash"] == pytest.approx(cash_expected, abs=1e-6)
    assert c2_ledger["positions"]["ETHUSDT"] == pytest.approx(qty_eth, abs=1e-9)
    assert c2_ledger["positions"]["SOLUSDT"] == pytest.approx(-qty_sol, abs=1e-9)
    assert "XRPUSDT" not in c2_ledger["positions"]
    executed_all = [o for o in res.orders if o["rejected_reason"] is None]
    assert res.summary["turnover_total_notional"] == pytest.approx(
        sum(o["qty"] * o["ref_price"] for o in executed_all), rel=1e-9
    )
    assert res.summary["turnover_total_notional"] >= (
        sum(o["qty"] * o["ref_price"] for o in executed_all if o["ts"] == stamp(2, 1))
    )
    assert res.skipped_rebalances, "C0/C1 must be skipped (insufficient history)"
    assert res.summary["rebalances_scored"] == 2  # C2 open + C3 flip


# --------------------------------------------------------------------------- #
# Reductions execute before increases
# --------------------------------------------------------------------------- #
def test_reductions_execute_before_increases():
    bars, daily = base_world_extra_day()
    res = run_shared_capital_backtest(
        bars, daily, rank_wf(daily), initial_capital=100_000.0, **ENGINE_KW
    )
    flip_orders = [o for o in res.orders if o["ts"] == stamp(3, 1)]
    kinds = [o["kind"] for o in flip_orders]
    assert kinds[0] == "reduce_to_zero" and kinds[1] == "reduce_to_zero"
    assert set(kinds[2:]) == {"flip_open"}
    red_idx = [i for i, k in enumerate(kinds) if k == "reduce_to_zero"]
    inc_idx = [i for i, k in enumerate(kinds) if k != "reduce_to_zero"]
    assert max(red_idx) < min(inc_idx)
    # flips execute (no margin rejections) — reductions freed cash first
    assert all(o["rejected_reason"] is None for o in flip_orders)


def test_margin_precheck_credits_reductions_before_buy_outlay():
    """White-box: the whole-rebalance pre-check must credit reduction proceeds
    BEFORE comparing against buy outlays (reduction-first accounting).

    Book: long 20 ETH (@100), short 5 SOL (@100); cash 200;
    equity = 200 + 2000 - 500 = 1700. Zero-sum rotation targets:
    ETH de-risks to +0.01 (releases ~1890), AAA opens +0.20 (buy outlay
    ~340 > cash 200), SOL stays -0.25 (delta 0). Without crediting the
    ETH reduction the AAA buy would be margin-rejected.
    """
    from research.portfolio_engine import _execute_rebalance_core

    syms = ("ETHUSDT", "SOLUSDT", "AAAUSDT")
    state = {
        "cash": 200.0,
        "equity": 200.0 + 20 * 100.0 - 5 * 100.0,
        "pos": {"ETHUSDT": 20.0, "SOLUSDT": -5.0, "AAAUSDT": 0.0},
        "avg_entry": {"ETHUSDT": 100.0, "SOLUSDT": 100.0, "AAAUSDT": 0.0},
        "leg_cost": {"ETHUSDT": 0.0, "SOLUSDT": 0.0, "AAAUSDT": 0.0},
    }
    params = dict(
        tick_size={s: 0.01 for s in syms},
        step_size={s: 0.001 for s in syms},
        min_notional=10.0, fee_taker=0.0005, slippage_ticks=1,
    )
    orders, closed_legs, checks = [], [], []
    breached = _execute_rebalance_core(
        cutoff=123, ts=456, fold_id=0,
        targets={"ETHUSDT": 0.01, "SOLUSDT": -0.21, "AAAUSDT": 0.20},
        refs={s: 100.0 for s in syms},
        state=state, params=params,
        orders=orders, closed_legs=closed_legs, invariant_checks=checks,
    )
    kinds = [(o["symbol"], o["kind"], o["rejected_reason"]) for o in orders]
    eth_red = next(o for o in orders if o["symbol"] == "ETHUSDT")
    aaa_open = next(o for o in orders if o["symbol"] == "AAAUSDT")
    assert eth_red["kind"] == "partial_reduce" and eth_red["side"] == "SELL"
    assert eth_red["fill_price"] is not None
    assert aaa_open["kind"] == "open" and aaa_open["fill_price"] is not None
    assert not [o for o in orders if o["rejected_reason"] == "margin_breach"], kinds
    assert orders.index(eth_red) < orders.index(aaa_open)
    assert breached is False
    assert checks[-1]["margin_ok"] is True


# --------------------------------------------------------------------------- #
# Skip semantics
# --------------------------------------------------------------------------- #
def test_skip_keeps_positions_and_records_reason():
    # XRP's daily series has a GAP (no day-2 close, resumes day 3):
    # rank sees non-consecutive daily points at C4 -> whole-cross-section SKIP.
    closes = {
        "ETHUSDT": {(0, 95): 100.0, (1, 95): 110.0, (2, 1): 100.50,
                    (2, 95): 112.0, (3, 95): 111.0, (4, 1): 111.5},
        "SOLUSDT": {(0, 95): 100.0, (1, 95): 90.0, (2, 1): 99.50,
                    (2, 95): 89.0, (3, 95): 90.0, (4, 1): 90.5},
        "XRPUSDT": {(0, 95): 100.0, (1, 95): 100.0, (2, 1): 100.0,
                    (3, 95): 100.0, (4, 1): 100.0},
    }
    bars, daily = build_world(closes)
    res = run_shared_capital_backtest(
        bars, daily, rank_wf(daily), initial_capital=100_000.0, **ENGINE_KW
    )
    target_skip = [
        r for r in res.skipped_rebalances if r["signal_ts"] == T0 + 4 * DAY_NS
    ]
    assert target_skip, "C4 must be skipped (XRP daily gap)"
    assert target_skip[0]["reason_code"] == "incomplete_cross_section_skip"
    assert target_skip[0]["execution_bar_ts"] == stamp(4, 1)
    before = next(r for r in res.portfolio_ledger if r["ts"] == stamp(3, 95))
    after = res.portfolio_ledger[-1]
    assert after["positions"].keys() == before["positions"].keys()
    for s, q in before["positions"].items():
        assert after["positions"][s] == pytest.approx(q, abs=1e-9), "skip keeps positions"
    assert not [o for o in res.orders if o["ts"] == stamp(4, 1)]


# --------------------------------------------------------------------------- #
# Funding
# --------------------------------------------------------------------------- #
def test_funding_applied_once_per_settlement_to_held_side_only(tmp_path: Path):
    closes = {
        "ETHUSDT": {(0, 95): 100.0, (1, 95): 110.0, (2, 1): 100.50},
        "SOLUSDT": {(0, 95): 100.0, (1, 95): 90.0, (2, 1): 99.50},
        "XRPUSDT": {(0, 95): 100.0, (1, 95): 100.0, (2, 1): 100.0},
    }
    # settlement-crossing bars at 08:15 and 16:15 of day 2
    closes["ETHUSDT"][(2, 33)] = 101.0
    closes["ETHUSDT"][(2, 65)] = 102.0
    closes["SOLUSDT"][(2, 33)] = 98.5
    closes["SOLUSDT"][(2, 65)] = 98.0
    closes["XRPUSDT"][(2, 33)] = 100.0
    closes["XRPUSDT"][(2, 65)] = 100.0
    bars, daily = build_world(closes)

    s1_ms = (T0 + 2 * DAY_NS + 8 * 3_600 * 1_000_000_000) // 1_000_000
    s2_ms = (T0 + 2 * DAY_NS + 16 * 3_600 * 1_000_000_000) // 1_000_000
    write_funding_bundle(tmp_path, "ETHUSDT", [(s1_ms, "0.0001"), (s2_ms, "0.0002")])
    write_funding_bundle(tmp_path, "SOLUSDT", [(s1_ms, "-0.0001"), (s2_ms, "0.0003")])

    res = run_shared_capital_backtest(
        bars, daily, rank_wf(daily), initial_capital=100_000.0,
        funding_bundles_dir=str(tmp_path), **{
            k: v for k, v in ENGINE_KW.items()
        },
    )
    fr = res.funding_cashflows
    assert len(fr) == 4, "two settlements x two held legs, applied exactly once"
    keys = [(r["symbol"], r["ts"]) for r in fr]
    assert len(set(keys)) == len(keys), "no duplicate application"

    qty_eth = 248.756
    qty_sol = 251.256
    eth_rows = {r["ts"]: r for r in fr if r["symbol"] == "ETHUSDT"}
    sol_rows = {r["ts"]: r for r in fr if r["symbol"] == "SOLUSDT"}
    s1_ns = s1_ms * 1_000_000
    s2_ns = s2_ms * 1_000_000
    # long pays positive rate on signed mark notional
    assert eth_rows[s1_ns]["cashflow"] == pytest.approx(-0.0001 * qty_eth * 101.0)
    assert eth_rows[s2_ns]["cashflow"] == pytest.approx(-0.0002 * qty_eth * 102.0)
    # short with negative rate pays too: -(-0.0001)*(-notional) < 0
    assert sol_rows[s1_ns]["cashflow"] == pytest.approx(-0.0001 * qty_sol * 98.5)
    # short receives positive-rate settlement: +0.0003 * notional
    assert sol_rows[s2_ns]["cashflow"] == pytest.approx(0.0003 * qty_sol * 98.0)
    # XRP flat: never funded
    assert all(r["symbol"] != "XRPUSDT" for r in fr)
    # cash hit immediately
    total_cf = sum(r["cashflow"] for r in fr)
    assert res.meta["funding_total"] == pytest.approx(total_cf, abs=1e-12)


def test_missing_funding_row_for_held_leg_fails_closed(tmp_path: Path):
    closes = {
        "ETHUSDT": {(0, 95): 100.0, (1, 95): 110.0, (2, 1): 100.50, (2, 33): 101.0},
        "SOLUSDT": {(0, 95): 100.0, (1, 95): 90.0, (2, 1): 99.50, (2, 33): 98.5},
        "XRPUSDT": {(0, 95): 100.0, (1, 95): 100.0, (2, 1): 100.0, (2, 33): 100.0},
    }
    bars, daily = build_world(closes)
    s1_ms = (T0 + 2 * DAY_NS + 8 * 3_600 * 1_000_000_000) // 1_000_000
    write_funding_bundle(tmp_path, "ETHUSDT", [(s1_ms + 28_800_000, "0.0001")])
    write_funding_bundle(tmp_path, "SOLUSDT", [(s1_ms, "-0.0001")])
    with pytest.raises(ValueError, match="missing funding settlement"):
        run_shared_capital_backtest(
            bars, daily, rank_wf(daily), initial_capital=100_000.0,
            funding_bundles_dir=str(tmp_path),
            tick_size=ENGINE_KW["tick_size"], step_size=ENGINE_KW["step_size"],
            min_notional=10.0,
        )


# --------------------------------------------------------------------------- #
# Flip: closed leg + reverse opening
# --------------------------------------------------------------------------- #
def test_flip_closes_leg_and_opens_reverse():
    bars, daily = base_world_extra_day()
    res = run_shared_capital_backtest(
        bars, daily, rank_wf(daily), initial_capital=100_000.0, **ENGINE_KW
    )
    sides = {(leg["symbol"], leg["side"]) for leg in res.closed_legs}
    assert ("ETHUSDT", "LONG") in sides and ("SOLUSDT", "SHORT") in sides
    eth_leg = next(l for l in res.closed_legs if l["symbol"] == "ETHUSDT")
    qty_eth = 248.756
    assert eth_leg["qty"] == pytest.approx(qty_eth, abs=1e-9)
    assert eth_leg["entry_price"] == pytest.approx(100.50)
    assert eth_leg["exit_price"] == pytest.approx(81.0)
    entry_cost = qty_eth * 100.51 * 0.0005 + qty_eth * 0.01
    gross = qty_eth * (81.0 - 100.50)
    assert eth_leg["gross_pnl"] == pytest.approx(gross, abs=1e-6)
    assert eth_leg["realized_pnl"] == pytest.approx(gross - entry_cost, abs=1e-6)

    sol_leg = next(l for l in res.closed_legs if l["symbol"] == "SOLUSDT")
    qty_sol = 251.256
    assert sol_leg["side"] == "SHORT"
    entry_cost_sol = qty_sol * 99.49 * 0.0005 + qty_sol * 0.01
    gross_sol = qty_sol * (99.50 - 129.0)
    assert sol_leg["realized_pnl"] == pytest.approx(gross_sol - entry_cost_sol, abs=1e-6)

    # reverse legs opened at the flip event
    last = res.portfolio_ledger[-1]
    assert last["positions"]["ETHUSDT"] < 0, "ETH flipped short"
    assert last["positions"]["SOLUSDT"] > 0, "SOL flipped long"
    flip_eth = [o for o in res.orders
                if o["ts"] == stamp(3, 1) and o["symbol"] == "ETHUSDT"]
    assert [o["kind"] for o in flip_eth] == ["reduce_to_zero", "flip_open"]
    assert flip_eth[0]["side"] == "SELL" and flip_eth[1]["side"] == "SELL"
    assert res.summary["legs_closed"] == 2


# --------------------------------------------------------------------------- #
# Invariant guards
# --------------------------------------------------------------------------- #
def test_weight_cap_breach_guard_raises():
    bars, daily = base_world_extra_day()

    def rogue_wf(C):
        return {
            "status": "OK", "signal_cutoff_ns": C, "scores": {},
            "longs": [["ETHUSDT", 0.5]], "shorts": [["SOLUSDT", -0.5]],
        }

    with pytest.raises(ValueError, match="invariant breach"):
        run_shared_capital_backtest(
            bars, daily, rogue_wf, initial_capital=100_000.0, **ENGINE_KW
        )


def test_nonzero_sum_targets_guard_raises():
    bars, daily = base_world_extra_day()

    def rogue_wf(C):
        return {
            "status": "OK", "signal_cutoff_ns": C, "scores": {},
            "longs": [["ETHUSDT", 0.25]], "shorts": [],
        }

    with pytest.raises(ValueError, match="invariant breach"):
        run_shared_capital_backtest(
            bars, daily, rogue_wf, initial_capital=100_000.0, **ENGINE_KW
        )


def test_cash_identity_holds_at_every_step():
    bars, daily = base_world_extra_day()
    res = run_shared_capital_backtest(
        bars, daily, rank_wf(daily), initial_capital=100_000.0, **ENGINE_KW
    )
    assert res.portfolio_ledger
    for row in res.portfolio_ledger:
        rhs = row["cash"] + sum(
            row["positions"][s] * px for s, px in row["marks"].items()
        )
        assert row["equity"] == pytest.approx(rhs, abs=1e-6)
        assert row["cash_identity_ok"] is True
    assert all(r["all_pass"] for r in res.invariant_checks)


# --------------------------------------------------------------------------- #
# Margin rejection and fold abort
# --------------------------------------------------------------------------- #
def ten_sym_world():
    closes = {}
    for sym in TEN_SYMS:
        closes[sym] = {(0, 95): 100.0, (1, 95): 100.0, (2, 1): 100.0}
    return build_world(closes)


LONGS5 = TEN_SYMS[:5]
SHORTS5 = TEN_SYMS[5:]


def _core_state(cash=1000.0, pos=None, equity=None):
    return {
        "cash": cash,
        "equity": equity if equity is not None else cash,
        "pos": pos or {"ETHUSDT": 0.0, "SOLUSDT": 0.0},
        "avg_entry": {"ETHUSDT": 0.0, "SOLUSDT": 0.0},
        "leg_cost": {"ETHUSDT": 0.0, "SOLUSDT": 0.0},
    }


def _core_params(**over):
    p = dict(
        tick_size={s: 0.01 for s in ("ETHUSDT", "SOLUSDT")},
        step_size={s: 0.001 for s in ("ETHUSDT", "SOLUSDT")},
        min_notional=10.0,
        fee_taker=0.0005,
        slippage_ticks=1,
    )
    p.update(over)
    return p


def test_margin_breach_rejects_increases_but_executes_reductions():
    """White-box: buy outlays above post-reduction free cash are rejected."""
    from research.portfolio_engine import _execute_rebalance_core

    # Stress state (post funding-drain): free cash 100 but equity-sized
    # targets demand ~2000.25 of buy outlay -> every increase is rejected
    # with margin_breach while any reductions would still execute.
    state = _core_state(cash=100.0)
    state["equity"] = 8000.0
    orders, closed_legs, checks = [], [], []
    breached = _execute_rebalance_core(
        cutoff=123, ts=456, fold_id=0,
        targets={"ETHUSDT": 0.25, "SOLUSDT": -0.25},
        refs={"ETHUSDT": 100.0, "SOLUSDT": 100.0},
        state=state, params=_core_params(),
        orders=orders, closed_legs=closed_legs, invariant_checks=checks,
    )
    rejected = [o for o in orders if o["rejected_reason"] == "margin_breach"]
    assert {o["symbol"] for o in rejected} == {"ETHUSDT", "SOLUSDT"}
    assert len(rejected) == 2
    assert all(o["fill_price"] is None for o in rejected)
    assert all(o["notional"] > state["cash"] for o in rejected)
    # nothing executed: flat book stays flat, cash untouched
    assert state["pos"] == {"ETHUSDT": 0.0, "SOLUSDT": 0.0}
    assert state["cash"] == pytest.approx(100.0)
    assert breached is False and checks[-1]["margin_ok"] is True


def test_negative_margin_reports_breach_flag_for_fold_abort():
    """White-box: already-negative cash emits a failing invariant row and the
    breach flag the driver uses to abort the fold (positions untouched)."""
    from research.portfolio_engine import _execute_rebalance_core

    state = _core_state(cash=-5.0)  # drained by prior funding/losses
    orders, closed_legs, checks = [], [], []
    breached = _execute_rebalance_core(
        cutoff=123, ts=456, fold_id=0,
        targets={"ETHUSDT": 0.25, "SOLUSDT": -0.25},
        refs={"ETHUSDT": 100.0, "SOLUSDT": 100.0},
        state=state, params=_core_params(slippage_ticks=0),
        orders=orders, closed_legs=closed_legs, invariant_checks=checks,
    )
    assert breached is True
    row = checks[-1]
    assert row["margin_ok"] is False and row["all_pass"] is False
    assert row["cash_identity_ok"] is True
    # nothing executable without free cash: flat book -> no fills at all
    assert not [o for o in orders if o["rejected_reason"] is None]


def test_driver_aborts_fold_on_margin_breach_and_resumes_next_fold(tmp_path: Path):
    """End-to-end: funding stress drains cash below zero while the book stays
    FROZEN (skipped rebalances); the next executed rebalance records
    margin_breach, aborts its fold, suppresses further cutoffs inside it,
    keeps positions frozen, and each later fold is re-checked fail-closed."""
    closes = {
        "ETHUSDT": {(0, 95): 100.0, (1, 95): 110.0, (2, 1): 100.50},
        "SOLUSDT": {(0, 95): 100.0, (1, 95): 90.0, (2, 1): 99.50},
        "XRPUSDT": {(0, 95): 100.0, (1, 95): 100.0, (2, 1): 100.0},
    }
    for sym, px_e, px_s in (("ETHUSDT", 101.0, 98.5), ("SOLUSDT", 98.5, 98.0)):
        pass
    # settlement-crossing marks for days 2..5 (8h / 16h slots) plus exec bars
    extra = {
        "ETHUSDT": {(2, 33): 101.0, (2, 65): 102.0, (3, 1): 103.0,
                    (3, 33): 103.5, (3, 65): 104.0, (4, 1): 104.5, (5, 1): 105.0},
        "SOLUSDT": {(2, 33): 98.5, (2, 65): 98.0, (3, 1): 97.5,
                    (3, 33): 97.0, (3, 65): 96.5, (4, 1): 96.0, (5, 1): 95.5},
        "XRPUSDT": {(2, 33): 100.0, (2, 65): 100.0, (3, 1): 100.0,
                    (3, 33): 100.0, (3, 65): 100.0, (4, 1): 100.0, (5, 1): 100.0},
    }
    for sym, ev in extra.items():
        closes[sym].update(ev)
    bars, daily = build_world(closes)

    def settle_ms(day, hour):
        return (T0 + day * DAY_NS + hour * 3_600 * 1_000_000_000) // 1_000_000

    hours = (0, 8, 16)
    write_funding_bundle(tmp_path, "ETHUSDT",
                         [(settle_ms(d, h), "0.5") for d in (1, 2, 3, 4) for h in hours])
    write_funding_bundle(tmp_path, "SOLUSDT",
                         [(settle_ms(d, h), "-0.5") for d in (1, 2, 3, 4) for h in hours])

    c2, c3, c4, c5 = (T0 + k * DAY_NS for k in (2, 3, 4, 5))

    def stress_wf(C):
        if C < c2:
            return {"status": "SKIP_INCOMPLETE", "reason_code": "incomplete_cross_section_skip",
                    "signal_cutoff_ns": C, "scores": {}, "longs": [], "shorts": []}
        if C == c2:
            return {"status": "OK", "signal_cutoff_ns": C, "scores": {},
                    "longs": [["ETHUSDT", 0.25]], "shorts": [["SOLUSDT", -0.25]]}
        if C in (c3,):  # book frozen while funding drains the account
            return {"status": "SKIP_INCOMPLETE", "reason_code": "incomplete_cross_section_skip",
                    "signal_cutoff_ns": C, "scores": {}, "longs": [], "shorts": []}
        return {"status": "OK", "signal_cutoff_ns": C, "scores": {},
                "longs": [["ETHUSDT", 0.01]], "shorts": [["SOLUSDT", -0.01]]}

    # fold 0 ends after the C4 execution bar so the breach belongs to fold 0
    folds = [(T0, T0 + 4 * DAY_NS + BAR_NS - 1),
             (T0 + 4 * DAY_NS + BAR_NS, T0 + 30 * DAY_NS)]
    res = run_shared_capital_backtest(
        bars, daily, stress_wf, initial_capital=10_000.0, folds=folds,
        funding_bundles_dir=str(tmp_path),
        tick_size={s: 0.01 for s in SYMS}, step_size={s: 0.001 for s in SYMS},
        min_notional=10.0, fee_taker=0.0005, slippage_ticks=0,
    )
    bad_rows = [r for r in res.invariant_checks if not r["margin_ok"]]
    assert bad_rows, "margin breach must be recorded at C4"
    assert bad_rows[0]["signal_ts"] == c4
    assert bad_rows[0]["all_pass"] is False
    # fold 0 breached at C4; fold 1's first attempt is re-checked and breaches
    # again while cash is still negative (fail-closed, never force-trades)
    assert res.meta["aborted_folds"] == [0, 1]
    # every cutoff from C1 onward evaluated exactly once (the grid starts at
    # the first bar event): c1/c3 skipped, c2 opened, c4 breached (fold 0),
    # c5 re-checked and breached again (fold 1)
    assert res.meta["weight_fn_calls"] == 5
    assert bad_rows[-1]["signal_ts"] == c5
    # held legs persist through the aborted region (never force-liquidated)
    assert any(r["positions"] for r in res.portfolio_ledger)


# --------------------------------------------------------------------------- #
# Precision / min-notional
# --------------------------------------------------------------------------- #
def test_sub_min_notional_orders_rejected_with_precision_reason():
    bars, daily = base_world_extra_day()

    def tiny_wf(C):
        return {
            "status": "OK", "signal_cutoff_ns": C, "scores": {},
            "longs": [["ETHUSDT", 0.0025]], "shorts": [["SOLUSDT", -0.0025]],
        }

    res = run_shared_capital_backtest(
        bars, daily, tiny_wf, initial_capital=100_000.0,
        tick_size=ENGINE_KW["tick_size"], step_size=ENGINE_KW["step_size"],
        min_notional=1000.0, fee_taker=0.0005, slippage_ticks=1,
    )
    rejected = [
        o for o in res.orders if o["rejected_reason"] == "weight_precision_reject"
    ]
    c2_rejected = [o for o in rejected if o["ts"] == stamp(2, 1)]
    assert len(c2_rejected) == 2
    assert all(o["fill_price"] is None for o in rejected)
    assert all(o["notional"] < 1000.0 for o in rejected)
    assert res.portfolio_ledger[-1]["positions"] == {}


# --------------------------------------------------------------------------- #
# Benchmark exclusion + summary sanity
# --------------------------------------------------------------------------- #
def test_btc_benchmark_never_traded():
    closes = {
        "BTCUSDT": {(0, 95): 50000.0, (1, 95): 60000.0, (2, 1): 60000.0},
        "ETHUSDT": {(0, 95): 100.0, (1, 95): 110.0, (2, 1): 100.50},
        "SOLUSDT": {(0, 95): 100.0, (1, 95): 90.0, (2, 1): 99.50},
        "XRPUSDT": {(0, 95): 100.0, (1, 95): 100.0, (2, 1): 100.0},
    }
    bars, daily = build_world(closes)
    res = run_shared_capital_backtest(
        bars, daily, rank_wf(daily), initial_capital=100_000.0, **ENGINE_KW
    )
    assert all(o["symbol"] != "BTCUSDT" for o in res.orders)
    assert "BTCUSDT" not in res.portfolio_ledger[-1]["positions"]


def test_summary_metrics_consistent():
    bars, daily = base_world_extra_day()
    res = run_shared_capital_backtest(
        bars, daily, rank_wf(daily), initial_capital=100_000.0, **ENGINE_KW
    )
    s = res.summary
    assert set(s) == {
        "total_pnl", "trades", "gross_profit", "gross_loss", "profit_factor",
        "pf_reason", "max_drawdown_frac", "max_dd_duration_days",
        "turnover_total_notional", "gross_exposure_max", "net_abs_max",
        "rebalances_scored", "legs_closed",
    }
    assert s["trades"] == len(res.closed_legs) == s["legs_closed"]
    gp = sum(l["realized_pnl"] for l in res.closed_legs if l["realized_pnl"] > 0)
    gl = abs(sum(l["realized_pnl"] for l in res.closed_legs if l["realized_pnl"] < 0))
    assert s["gross_profit"] == pytest.approx(gp, abs=1e-6)
    assert s["gross_loss"] == pytest.approx(gl, abs=1e-6)
    assert s["profit_factor"] == pytest.approx(gp / gl, rel=1e-9)
    assert s["total_pnl"] == pytest.approx(res.equity_curve[-1][1] - 100_000.0, abs=1e-9)
    # target-side caps hold on every rebalance (mark drift between rebalances
    # may exceed them, which is why the caps are enforced on targets)
    assert all(r["gross_within_cap"] for r in res.invariant_checks)
    assert s["gross_exposure_max"] == pytest.approx(
        max(r["gross_exposure"] for r in res.portfolio_ledger), abs=1e-12
    )
    assert s["net_abs_max"] == pytest.approx(
        max(abs(r["net_exposure"]) for r in res.portfolio_ledger), abs=1e-12
    )
    executed = [o for o in res.orders if o["rejected_reason"] is None]
    assert s["turnover_total_notional"] == pytest.approx(
        sum(o["qty"] * o["ref_price"] for o in executed), abs=1e-6
    )


# --------------------------------------------------------------------------- #
# Determinism
# --------------------------------------------------------------------------- #
def test_two_runs_produce_identical_canonical_json():
    bars, daily = base_world_extra_day()
    kw = dict(ENGINE_KW)
    r1 = run_shared_capital_backtest(bars, daily, rank_wf(daily),
                                     initial_capital=100_000.0, **kw)
    r2 = run_shared_capital_backtest(bars, daily, rank_wf(daily),
                                     initial_capital=100_000.0, **kw)
    d1 = hashlib.sha256(r1.canonical_json().encode()).hexdigest()
    d2 = hashlib.sha256(r2.canonical_json().encode()).hexdigest()
    assert d1 == d2
    # and the payload is canonical JSON (sorted keys, compact separators)
    assert r1.canonical_json() == json.dumps(
        json.loads(r1.canonical_json()), sort_keys=True, separators=(",", ":")
    )
