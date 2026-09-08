"""SD5 — execution-cost models and fail-closed fill decisions (owner: A5).

Every expected number is HAND-COMPUTED and written literally with the
arithmetic in comments.  Halt / closed session / missing quote / missing
ADV / participation cap all produce NO fill (fail closed); the cost model
is immutable with a canonical cost_model_id digest.  No repository writes.
"""

from __future__ import annotations

import dataclasses

import pytest

from research.assets.common.execution_cost import CostModelId, ExecutionCostEstimate
from research.assets.stocks.accounting import (
    FLOAT_IDENTITY_TOLERANCE_USD,
    IdentityLedger,
    OrderRejection,
)
from research.assets.stocks.execution import (
    CommissionSchedule,
    EquityExecutionModel,
    ExecutionDecision,
    ImpactModel,
    NoQuoteSourceError,
    SpreadPolicy,
    deferred_entry_timestamp,
    next_executable_event_index,
)

T0 = "2026-03-02T14:30:00+00:00"
T1 = "2026-03-02T14:31:00+00:00"

# Shared model: per-share 0.005 with 1.00 order minimum; quotes required
# (no proxy); no impact; no slippage.
BASE_MODEL = EquityExecutionModel(
    cost_model_id="US_EQUITY_TAKER_TEST_V1",
    commission=CommissionSchedule(per_share=0.005, min_per_order=1.00),
    spread=SpreadPolicy(proxy_spread_bps=None),
    impact=ImpactModel(coefficient=0.0, max_participation=0.01),
    slippage_bps=0.0,
    currency="USD",
)


def _attempt(model, **overrides):
    kwargs = dict(
        symbol="AAPL", side="BUY", quantity=100, reference_price=50.00,
        timestamp_utc=T0, session_open=True, halted=False,
        bid=49.99, ask=50.01,
    )
    kwargs.update(overrides)
    return model.attempt_fill(**kwargs)


# --- commission schedule golden ------------------------------------------------- #
def test_commission_schedule_golden():
    schedule = CommissionSchedule(per_share=0.005, min_per_order=1.00)
    # 100 shares: 100*0.005 = 0.50 -> below the 1.00 minimum -> 1.00
    assert schedule.commission(100) == pytest.approx(1.00, abs=1e-12)
    # 300 shares: 300*0.005 = 1.50 -> above the minimum -> 1.50
    assert schedule.commission(300) == pytest.approx(1.50, abs=1e-12)
    # 1000 shares: 1000*0.005 = 5.00
    assert schedule.commission(1000) == pytest.approx(5.00, abs=1e-12)
    with pytest.raises(ValueError):
        schedule.commission(0)


# --- spread from quotes vs explicit conservative proxy --------------------------- #
def test_buy_fills_at_ask_and_pays_half_spread():
    decision = _attempt(BASE_MODEL, side="BUY")
    assert decision.status == "FILLED"
    # BUY fills at the ask 50.01 ; half-spread = (50.01 - 49.99)/2 = 0.01
    assert decision.fill.price == pytest.approx(50.01, abs=1e-12)
    assert decision.fill.cost.spread == pytest.approx(100 * 0.01, abs=1e-9)  # = 1.00
    assert decision.fill.cost.commission == pytest.approx(1.00, abs=1e-12)
    assert decision.fill.cost.slippage == 0.0
    assert decision.fill.cost.market_impact == 0.0
    assert decision.estimate.total() == pytest.approx(2.00, abs=1e-9)


def test_sell_fills_at_bid():
    decision = _attempt(BASE_MODEL, side="SELL")
    assert decision.fill.price == pytest.approx(49.99, abs=1e-12)
    assert decision.fill.cost.spread == pytest.approx(1.00, abs=1e-9)


def test_proxy_spread_when_quotes_are_absent():
    proxy_model = EquityExecutionModel(
        cost_model_id="US_EQUITY_TAKER_PROXY_V1",
        commission=CommissionSchedule(per_share=0.0, min_per_order=0.0),
        spread=SpreadPolicy(proxy_spread_bps=20.0),  # 20 bps FULL spread
        impact=ImpactModel(coefficient=0.0, max_participation=0.01),
        slippage_bps=0.0,
        currency="USD",
    )
    # mid = 50.00 ; half = 50 * 20 / 2 / 10000 = 0.05
    buy = _attempt(proxy_model, side="BUY", bid=None, ask=None)
    assert buy.fill.price == pytest.approx(50.05, abs=1e-12)   # mid + half
    assert buy.fill.cost.spread == pytest.approx(100 * 0.05, abs=1e-9)  # = 5.00
    sell = _attempt(proxy_model, side="SELL", bid=None, ask=None, timestamp_utc=T1)
    assert sell.fill.price == pytest.approx(49.95, abs=1e-12)  # mid - half
    # No quotes and no proxy -> fail closed:
    bare = EquityExecutionModel(
        cost_model_id="US_EQUITY_BARE_V1",
        commission=CommissionSchedule(per_share=0.0, min_per_order=0.0),
        spread=SpreadPolicy(proxy_spread_bps=None),
        impact=ImpactModel(coefficient=0.0, max_participation=0.01),
        slippage_bps=0.0,
        currency="USD",
    )
    with pytest.raises(NoQuoteSourceError):
        bare.spread.resolve(reference_price=50.00)
    missing = _attempt(bare, bid=None, ask=None)
    assert missing.status == "NO_FILL" and missing.reason == "MISSING_QUOTE"


def test_quotes_win_over_proxy_no_blending():
    proxy_model = EquityExecutionModel(
        cost_model_id="US_EQUITY_TAKER_PROXY_V1",
        commission=CommissionSchedule(per_share=0.0, min_per_order=0.0),
        spread=SpreadPolicy(proxy_spread_bps=100.0),  # deliberately wide proxy
        impact=ImpactModel(coefficient=0.0, max_participation=0.01),
        slippage_bps=0.0,
        currency="USD",
    )
    # Quotes exist -> they win; the 100 bps proxy stays inert (BUY @ ask 50.01).
    decision = _attempt(proxy_model, side="BUY")
    assert decision.fill.price == pytest.approx(50.01, abs=1e-12)


def test_crossed_quotes_are_a_data_error():
    with pytest.raises(ValueError, match="crossed quotes"):
        SpreadPolicy(proxy_spread_bps=None).resolve(
            reference_price=50.00, bid=50.10, ask=49.90
        )


# --- slippage --------------------------------------------------------------------- #
def test_slippage_golden():
    slip_model = EquityExecutionModel(
        cost_model_id="US_EQUITY_TAKER_SLIP_V1",
        commission=CommissionSchedule(per_share=0.0, min_per_order=0.0),
        spread=SpreadPolicy(proxy_spread_bps=None),
        impact=ImpactModel(coefficient=0.0, max_participation=0.01),
        slippage_bps=5.0,
        currency="USD",
    )
    decision = _attempt(slip_model, side="BUY", reference_price=10.00, bid=9.99, ask=10.01)
    # BUY fills at 10.01 ; slippage = 100 * 10.01 * 5 / 10000 = 0.5005
    assert decision.fill.price == pytest.approx(10.01, abs=1e-12)
    assert decision.fill.cost.slippage == pytest.approx(0.5005, abs=1e-12)


# --- participation/ADV impact and the order-size cap ------------------------------- #
def test_impact_square_root_golden():
    impact = ImpactModel(coefficient=0.5, max_participation=0.001)
    # participation = 100 / 1_000_000 = 0.0001 ; sqrt = 0.01
    # impact = 0.5 * 100.00 * 100 * 0.01 = 50.00
    assert impact.impact(price=100.00, quantity=100, adv=1_000_000) == pytest.approx(50.00, abs=1e-9)


def test_impact_flows_into_fill_and_estimate():
    impact_model = EquityExecutionModel(
        cost_model_id="US_EQUITY_TAKER_IMPACT_V1",
        commission=CommissionSchedule(per_share=0.0, min_per_order=0.0),
        spread=SpreadPolicy(proxy_spread_bps=None),
        impact=ImpactModel(coefficient=0.5, max_participation=0.001),
        slippage_bps=0.0,
        currency="USD",
    )
    decision = _attempt(
        impact_model, side="BUY", reference_price=100.00, bid=99.99, ask=100.01,
        adv=1_000_000,
    )
    assert decision.status == "FILLED"
    # fill at ask 100.01 ; impact = 0.5 * 100.01 * 100 * sqrt(100/1e6) = 50.005
    assert decision.fill.cost.market_impact == pytest.approx(50.005, abs=1e-9)
    # total = spread 1.00 (100 * 0.01 half-spread) + impact 50.005 = 51.005
    assert decision.estimate.total() == pytest.approx(51.005, abs=1e-9)


def test_participation_cap_produces_no_fill():
    impact_model = EquityExecutionModel(
        cost_model_id="US_EQUITY_TAKER_IMPACT_V1",
        commission=CommissionSchedule(per_share=0.0, min_per_order=0.0),
        spread=SpreadPolicy(proxy_spread_bps=None),
        impact=ImpactModel(coefficient=0.5, max_participation=0.0002),
        slippage_bps=0.0,
        currency="USD",
    )
    # participation = 300 / 1_000_000 = 0.0003 > cap 0.0002 -> NO FILL
    decision = _attempt(
        impact_model, quantity=300, reference_price=100.00,
        bid=99.99, ask=100.01, adv=1_000_000,
    )
    assert decision.status == "NO_FILL"
    assert decision.reason == "PARTICIPATION_CAP"
    assert decision.fill is None and decision.estimate is None
    assert decision.rejection_cost == 0.0


def test_impact_without_adv_fails_closed():
    impact_model = EquityExecutionModel(
        cost_model_id="US_EQUITY_TAKER_IMPACT_V1",
        commission=CommissionSchedule(per_share=0.0, min_per_order=0.0),
        spread=SpreadPolicy(proxy_spread_bps=None),
        impact=ImpactModel(coefficient=0.5, max_participation=0.01),
        slippage_bps=0.0,
        currency="USD",
    )
    decision = _attempt(impact_model, adv=None)
    assert decision.status == "NO_FILL" and decision.reason == "MISSING_ADV"
    # Through the estimate() interface: quotes present, ADV absent -> fail closed.
    with pytest.raises(Exception, match="adv"):
        impact_model.estimate(
            symbol="AAPL", side="BUY", quantity=100, price=50.0,
            context={"bid": 49.99, "ask": 50.01},
        )


# --- fail-closed sessions: halt / closed / missing quote produce NO fill ---------- #
@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"halted": True}, "HALTED"),
        ({"session_open": False}, "SESSION_CLOSED"),
        ({"bid": None, "ask": None}, "MISSING_QUOTE"),
        ({"bid": 49.99, "ask": None}, "MISSING_QUOTE"),
    ],
)
def test_no_fill_on_halt_closed_session_or_missing_quote(overrides, reason):
    decision = _attempt(BASE_MODEL, **overrides)
    assert decision.status == "NO_FILL"
    assert decision.reason == reason
    assert decision.fill is None
    assert decision.estimate is None
    assert decision.rejection_cost == 0.0


def test_no_fill_decision_booking_leaves_ledger_unchanged():
    ledger = IdentityLedger(starting_equity=10_000.00)
    decision = _attempt(BASE_MODEL, halted=True)
    assert decision.status == "NO_FILL"
    # A halted-session order produces NO fill and costs nothing:
    ledger.record_rejection(
        OrderRejection(
            symbol=decision.symbol, side=decision.side, quantity=decision.quantity,
            reason=decision.reason, timestamp_utc=decision.timestamp_utc,
            cost=decision.rejection_cost,
        )
    )
    assert ledger.fills == ()
    assert ledger.cash == 10_000.0
    terms = ledger.identity_terms()
    assert terms.ending_equity - terms.starting_equity == 0.0
    terms.assert_closes(FLOAT_IDENTITY_TOLERANCE_USD)


def test_filled_decision_books_into_ledger_and_closes():
    ledger = IdentityLedger(starting_equity=10_000.00)
    buy = _attempt(BASE_MODEL, side="BUY")
    ledger.apply_fill(buy.fill)
    # cash = 10000 - 100*50.01 - (1.00 commission + 1.00 spread) = 4997.00
    assert ledger.cash == pytest.approx(4997.00, abs=1e-6)
    sell = _attempt(BASE_MODEL, side="SELL", bid=50.99, ask=51.01, timestamp_utc=T1)
    ledger.apply_fill(sell.fill)
    # realized = (50.99 - 50.01) * 100 = 98.00 ; delta = 94.00 = 98 - 2 - 2
    terms = ledger.identity_terms()
    assert terms.realized_price_pnl == pytest.approx(98.00, abs=1e-9)
    assert terms.ending_equity - terms.starting_equity == pytest.approx(94.00, abs=1e-6)
    terms.assert_closes(FLOAT_IDENTITY_TOLERANCE_USD)


# --- the common estimate() interface ---------------------------------------------- #
def test_estimate_matches_attempt_fill_components():
    estimate = BASE_MODEL.estimate(
        symbol="AAPL", side="BUY", quantity=100, price=50.01,
        context={"bid": 49.99, "ask": 50.01},
    )
    assert isinstance(estimate, ExecutionCostEstimate)
    decision = _attempt(BASE_MODEL, side="BUY")
    assert estimate.commission == decision.estimate.commission
    assert estimate.spread_cost == decision.estimate.spread_cost
    assert estimate.total() == decision.estimate.total()
    assert estimate.canonical_json() == decision.estimate.canonical_json()


def test_cost_model_id_and_digest_are_immutable_and_sensitive():
    assert BASE_MODEL.model_id == CostModelId("US_EQUITY_TAKER_TEST_V1")
    twin = EquityExecutionModel(
        cost_model_id="US_EQUITY_TAKER_TEST_V1",
        commission=CommissionSchedule(per_share=0.005, min_per_order=1.00),
        spread=SpreadPolicy(proxy_spread_bps=None),
        impact=ImpactModel(coefficient=0.0, max_participation=0.01),
        slippage_bps=0.0,
        currency="USD",
    )
    changed = EquityExecutionModel(
        cost_model_id="US_EQUITY_TAKER_TEST_V1",
        commission=CommissionSchedule(per_share=0.006, min_per_order=1.00),  # one param differs
        spread=SpreadPolicy(proxy_spread_bps=None),
        impact=ImpactModel(coefficient=0.0, max_participation=0.01),
        slippage_bps=0.0,
        currency="USD",
    )
    assert BASE_MODEL.digest == twin.digest
    assert BASE_MODEL.digest != changed.digest
    assert len(BASE_MODEL.digest) == 64
    with pytest.raises(dataclasses.FrozenInstanceError):
        BASE_MODEL.slippage_bps = 1.0  # type: ignore[misc]


# --- one-event entry delay ----------------------------------------------------------- #
def test_one_event_entry_delay_never_fills_on_the_signal_event():
    flags = [True, False, False, True]
    # Signal on event 0 (executable): the entry may NOT be event 0 -> next is 3.
    assert next_executable_event_index(0, flags) == 3
    assert next_executable_event_index(1, flags) == 3
    assert next_executable_event_index(2, flags) == 3
    # Signal on the last event: no later executable event -> the entry never happens.
    assert next_executable_event_index(3, flags) is None
    assert next_executable_event_index(0, [False, False]) is None


def test_deferred_entry_timestamp_helper():
    stamps = ["2026-03-02T14:30:00+00:00", "2026-03-02T14:31:00+00:00",
              "2026-03-02T14:32:00+00:00", "2026-03-02T14:33:00+00:00"]
    flags = [True, False, False, True]
    assert deferred_entry_timestamp(stamps, flags, 0) == stamps[3]
    # Signal on the last event of a stream: the entry never executes.
    assert deferred_entry_timestamp(stamps, flags, 3) is None
    assert deferred_entry_timestamp(["s0", "s1"], [True, False], 0) is None
    with pytest.raises(ValueError):
        deferred_entry_timestamp(stamps, [True], 0)  # length mismatch fails closed


def test_decision_validation_is_fail_closed():
    with pytest.raises(ValueError, match="REQUIRES a non-empty reason"):
        ExecutionDecision(
            status="NO_FILL", reason=None, detail=None, symbol="AAPL", side="BUY",
            quantity=100, timestamp_utc=T0, fill=None, estimate=None, rejection_cost=0.0,
        )
    with pytest.raises(ValueError, match="must not carry a fill"):
        ExecutionDecision(
            status="NO_FILL", reason="HALTED", detail="x", symbol="AAPL", side="BUY",
            quantity=100, timestamp_utc=T0,
            fill=_attempt(BASE_MODEL).fill, estimate=None, rejection_cost=0.0,
        )
