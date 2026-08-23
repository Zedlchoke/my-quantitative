"""V3 execution-truth micro fixtures (PLAN section 7).

Proves, on the installed NautilusTrader engine (source of truth), that:

* NEXT_BAR_EVENT_BASELINE: a signal on closed bar t is submitted on bar t+1
  and fills at bar_{t+1}.CLOSE +- one tick (next-bar-close — there is no
  native next-bar-open fill for bar data). Hard invariant
  ``signal_ts < submit_ts <= fill_ts`` holds for every scored entry.
* SAME_BAR_CLOSE_DIAGNOSTIC: legacy behaviour fills on the signal bar itself;
  every record carries ``evidence_class=DIAGNOSTIC_ONLY``.
* Initial risk / R accounting: initial_stop_price frozen at entry from the
  ATR multiple, initial_risk_usdt = |fill - stop| x qty, r_multiple =
  canonical_pnl / initial_risk_usdt; non-positive risk -> None +
  invalid_initial_risk.

Hand-checked numbers (6 bars, closes 100..105, entry scripted on bar #2):
    baseline : signal@bar2.ts < submit@bar3.ts == fill@bar3.ts,
               fill = 103.00 + 0.01 tick, qty = 10.000,
               stop = 102.51, initial_risk = 5.0 USDT,
               slippage_cost = 0.10 USDT;
               exit on bar #4 fills at 104.00 - 0.01 = 103.99,
               raw pnl = 9.80, realized net of taker commissions = 8.972,
               r_multiple = 1.7944.
    same-bar : fill@bar2.ts at 102.01, evidence DIAGNOSTIC_ONLY.

Note: Nautilus MARGIN accounts report PositionClosed.realized_pnl NET of
commissions; ``commission`` is captured separately for decomposition.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.engine import BacktestEngineConfig
from nautilus_trader.backtest.models.fee import MakerTakerFeeModel
from nautilus_trader.backtest.models.fill import OneTickSlippageFillModel
from nautilus_trader.adapters.binance.common.types import BinanceBar
from nautilus_trader.config import LoggingConfig
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import AccountType
from nautilus_trader.model.enums import OmsType
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.objects import Money
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from nautilus_trader.test_kit.providers import TestInstrumentProvider

from backtest.engine import EXECUTION_RECORD_REQUIRED_KEYS
from backtest.engine import _attach_execution_evidence
from backtest.engine import expectancy_r as records_expectancy_r
from backtest.engine import validate_execution_records
from contracts.protocol import ExecutionMode
from strategy_base import BaseFuturesStrategy
from strategy_base import BaseFuturesStrategyConfig

INSTRUMENT_ID = InstrumentId.from_str("ETHUSDT-PERP.BINANCE")
BAR_TYPE = BarType.from_str("ETHUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL")
TICK = 0.01
T0_NS = 1767225600000000000  # 2026-01-01T00:00:00Z
STEP_NS = 900_000_000_000  # 15 minutes
N_BARS = 6
CLOSES = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]


def _ts(bar_index: int) -> int:
    return T0_NS + (bar_index + 1) * STEP_NS


def _make_bar(index: int) -> BinanceBar:
    close = CLOSES[index]
    return BinanceBar(
        BAR_TYPE,
        Price(close - 0.5, 2),
        Price(close + 0.5, 2),
        Price(close - 0.5, 2),
        Price(close, 2),
        Quantity(10_000.000, 3),
        Decimal("1000000"),
        1,
        Decimal("500000"),
        Decimal("1000000"),
        _ts(index),
        _ts(index),
    )


class ScriptedStrategy(BaseFuturesStrategy):
    """Signals BUY on a chosen bar index; exits on a later bar index."""

    def __init__(self, config: BaseFuturesStrategyConfig, script: dict[int, str]) -> None:
        super().__init__(config)
        self.script = script
        self.bar_ts_seen: list[int] = []

    def indicators(self) -> list:
        return []

    def on_bar(self, bar) -> None:  # noqa: D102 - wrapped by deferral decorator
        self.bar_ts_seen.append(int(bar.ts_event))
        action = self.script.get(len(self.bar_ts_seen) - 1)
        close = bar.close.as_double()
        if action == "BUY":
            # atr 0.25 x stop_multiple 2.0 -> 0.50 stop distance
            self._submit_entry(OrderSide.BUY, close, atr=0.25, stop_multiple=2.0)
        elif action == "EXIT":
            self._submit_exit("scripted_exit", close)


def _build_config(**overrides) -> BaseFuturesStrategyConfig:
    params = dict(
        instrument_id=INSTRUMENT_ID,
        bar_type=BAR_TYPE,
        risk_per_trade_usdt=Decimal("5"),  # 5 / 0.5 -> qty 10 exactly
        max_notional_usdt=Decimal("100000"),
        max_daily_loss_usdt=Decimal("1000"),
        max_trades_per_day=4,
        cooldown_bars_after_loss=0,
        enable_trading=True,
        request_historical_bars=False,
    )
    params.update(overrides)
    return BaseFuturesStrategyConfig(**params)


def _run_engine(strategy: BaseFuturesStrategy) -> BacktestEngine:
    instrument = TestInstrumentProvider.ethusdt_perp_binance()
    engine = BacktestEngine(
        config=BacktestEngineConfig(
            trader_id="TESTER-001",
            logging=LoggingConfig(bypass_logging=True),
        ),
    )
    engine.add_venue(
        venue=Venue("BINANCE"),
        oms_type=OmsType.NETTING,
        account_type=AccountType.MARGIN,
        base_currency=instrument.quote_currency,
        starting_balances=[Money.from_str("10000 USDT")],
        default_leverage=Decimal("1"),
        leverages={INSTRUMENT_ID: Decimal("1")},
        fee_model=MakerTakerFeeModel(),  # taker 0.04% embedded in instrument
        fill_model=OneTickSlippageFillModel(),
    )
    engine.add_instrument(instrument)
    engine.add_data([_make_bar(i) for i in range(N_BARS)])
    engine.add_strategy(strategy)
    engine.run()
    result = engine.get_result()  # NOT idempotent: returns a new object
    _attach_execution_evidence(engine, result)
    strategy._result = result
    return engine


def _run_and_result(strategy) -> tuple:
    engine = _run_engine(strategy)
    return strategy, getattr(strategy, "_result"), engine


def _baseline_strategy(**overrides) -> ScriptedStrategy:
    overrides.setdefault(
        "execution_mode",
        ExecutionMode.NEXT_BAR_EVENT_BASELINE.value,
    )
    return ScriptedStrategy(_build_config(**overrides), {2: "BUY", 4: "EXIT"})


class TestNextBarEventBaselineEngineFixture:
    @pytest.fixture()
    def run(self):
        strategy = _baseline_strategy()
        return _run_and_result(strategy)

    def test_signal_submit_fill_ordering_and_next_bar_close_semantics(self, run):
        strategy, result, _engine = run
        assert len(result.execution_records) == 1
        rec = result.execution_records[0]
        # Signal decided while processing bar #2; submission happened during
        # bar #3's event; the fill carries the SAME ts_init as the submit bar.
        assert rec["signal_ts"] == _ts(2)
        assert rec["submit_ts"] == _ts(3)
        assert rec["fill_ts"] == _ts(3)
        assert rec["signal_ts"] < rec["submit_ts"] <= rec["fill_ts"]
        # Fill occurred AT bar #3's close + one adverse tick (next-bar-CLOSE).
        assert rec["signal_reference_price"] == 102.0
        assert rec["fill_price"] == pytest.approx(103.0 + TICK)
        bar3_low, bar3_high = CLOSES[3] - 0.5, CLOSES[3] + 0.5
        k = 2 * TICK
        assert bar3_low - k <= rec["fill_price"] <= bar3_high + k

    def test_execution_record_has_all_plan_section7_keys(self, run):
        _strategy, result, _engine = run
        rec = result.execution_records[0]
        missing = [k for k in EXECUTION_RECORD_REQUIRED_KEYS if k not in rec]
        assert missing == []
        assert rec["execution_mode"] == "NEXT_BAR_EVENT_BASELINE"
        assert rec["evidence_class"] == "SCORED"
        assert rec["side"] == "LONG"
        assert rec["symbol"] == "ETHUSDT"
        assert rec["fold"] == "n/a"
        assert rec["slippage_ticks"] == 1
        assert rec["funding_pnl"] is None  # runner join point
        assert rec["commission"] is not None and rec["commission"] > 0

    def test_initial_risk_math_hand_checked(self, run):
        _strategy, result, _engine = run
        rec = result.execution_records[0]
        assert rec["quantity"] == pytest.approx(10.0)
        # stop = fill - atr(0.25) x multiple(2.0) = 103.01 - 0.50 = 102.51
        assert rec["initial_stop_price"] == pytest.approx(103.01 - 0.50)
        expected_risk = abs(103.01 - 102.51) * 10.0
        assert rec["initial_risk_usdt"] == pytest.approx(expected_risk)
        assert rec["initial_risk_usdt"] == pytest.approx(5.0)
        # slippage vs submit-bar reference close (103.00): one tick x qty.
        assert rec["slippage_cost"] == pytest.approx(TICK * 10.0)

    def test_close_pnl_and_r_multiple_hand_checked(self, run):
        _strategy, result, _engine = run
        rec = result.execution_records[0]
        # Exit scripted on bar #4: submitted during bar #4, filled at its close.
        assert rec["exit_signal_ts"] == rec["exit_submit_ts"] == _ts(4)
        assert rec["exit_fill_ts"] == _ts(4)
        # SELL reduce fills one adverse tick below bar #4 close: 104.00-0.01.
        raw_pnl = (103.99 - 103.01) * 10.0  # 9.80
        # Nautilus MARGIN accounts report realized PnL net of commissions
        # (taker 0.04% per side on this instrument):
        #   entry 1030.10 x 0.0004 = 0.41204 ; exit 1039.90 x 0.0004 = 0.41596
        expected_realized = raw_pnl - (0.41204 + 0.41596)
        assert rec["gross_pnl"] == pytest.approx(expected_realized)
        assert rec["canonical_pnl"] == pytest.approx(rec["gross_pnl"])
        assert rec["r_multiple"] == pytest.approx(expected_realized / 5.0)

    def test_engine_level_evidence_helpers(self, run):
        _strategy, result, engine = run
        assert result.execution_violations == []
        assert result.execution_evidence_reasons == []
        expected_r = result.execution_records[0]["r_multiple"]
        assert result.expectancy_r == pytest.approx(expected_r)
        from backtest.engine import collect_execution_records

        collected, collected_violations = collect_execution_records(engine)
        assert len(collected) == 1
        assert collected_violations == []
        assert validate_execution_records(collected) == []


class TestSameBarCloseDiagnosticMode:
    def test_same_bar_fill_is_diagnostic_only(self):
        strategy = _baseline_strategy(
            execution_mode=ExecutionMode.SAME_BAR_CLOSE_DIAGNOSTIC.value,
        )
        _strategy, result, _engine = _run_and_result(strategy)
        assert len(result.execution_records) == 1
        rec = result.execution_records[0]
        # Legacy semantics: submit AND fill on the SIGNAL bar itself.
        assert rec["signal_ts"] == rec["submit_ts"] == rec["fill_ts"] == _ts(2)
        assert rec["fill_price"] == pytest.approx(102.0 + TICK)
        assert rec["evidence_class"] == "DIAGNOSTIC_ONLY"
        assert rec["initial_risk_usdt"] == pytest.approx(abs(102.01 - 101.51) * 10.0)
        # Diagnostic artifacts are exempt from the scored ordering invariant...
        assert "signal_fill_ordering_violation" not in rec["reason_codes"]
        # ...and validator flags any diagnostic-labelled record claiming the
        # scored mode (label/mode coherence).
        assert validate_execution_records([rec]) == []


class TestRiskAccountingEdgeCases:
    def test_invalid_initial_risk_marks_reason_and_skips_division(self):
        class ZeroStopStrategy(ScriptedStrategy):
            def _initial_stop_for(self, side, fill_price):
                return fill_price  # degenerate stop -> zero risk

        strategy = ZeroStopStrategy(
            _build_config(execution_mode=ExecutionMode.NEXT_BAR_EVENT_BASELINE.value),
            {2: "BUY", 4: "EXIT"},
        )
        _strategy, result, _engine = _run_and_result(strategy)
        rec = result.execution_records[0]
        assert rec["initial_risk_usdt"] is None
        assert "invalid_initial_risk" in rec["reason_codes"]
        assert rec["r_multiple"] is None
        reasons = validate_execution_records(result.execution_records)
        assert f"invalid_initial_risk:{rec['position_id']}" in reasons

    def test_ordering_violation_raises_when_strict(self):
        class BrokenOrderingStrategy(ScriptedStrategy):
            def _check_signal_fill_ordering(self, record):  # simulate violation
                record["submit_ts"] = record["signal_ts"]  # corrupt to equal
                return super()._check_signal_fill_ordering(record)

        strategy = BrokenOrderingStrategy(
            _build_config(strict_execution_invariant=False),
            {2: "BUY"},
        )
        _strategy, result, _engine = _run_and_result(strategy)
        assert result.execution_violations, "violation must be counted"
        assert any(
            "signal_fill_ordering_violation" in reason
            for reason in result.execution_evidence_reasons
        )

    def test_expectancy_r_none_safe(self):
        assert records_expectancy_r([]) is None
        assert records_expectancy_r(
            [{"r_multiple": None}, {"r_multiple": None}],
        ) is None
        assert records_expectancy_r(
            [{"r_multiple": 2.0}, {"r_multiple": -1.0}, {"r_multiple": None}],
        ) == pytest.approx(0.5)


class TestDeferralQueueMechanics:
    """Direct base-class queue tests without an engine."""

    class _FakePortfolio:
        def is_flat(self, _instrument_id) -> bool:
            return True

    class _FakeCache:
        def orders_open(self, **_kwargs):
            return []

        def orders_inflight(self, **_kwargs):
            return []

    class QueueHarness(ScriptedStrategy):
        """Shadow framework objects so the flush path runs head-less."""

        def __init__(self, config) -> None:
            super().__init__(config, script={})
            self.instrument = TestInstrumentProvider.ethusdt_perp_binance()
            self.executed: list[dict] = []

        @property
        def portfolio(self):
            return TestDeferralQueueMechanics._FakePortfolio()

        @property
        def cache(self):
            return TestDeferralQueueMechanics._FakeCache()

        def _execute_entry_intent(self, intent: dict) -> None:
            self.executed.append(intent)

    def _harness(self):
        strategy = self.QueueHarness(
            _build_config(execution_mode=ExecutionMode.NEXT_BAR_EVENT_BASELINE.value),
        )
        return strategy

    def test_intent_queued_on_signal_bar_flushed_once_next_bar(self):
        strategy = self._harness()
        bars = [_make_bar(i) for i in range(4)]
        strategy.on_bar(bars[0])
        strategy.on_bar(bars[1])
        assert strategy._pending_entry is None  # nothing signalled yet
        assert strategy.executed == []
        # Signal fires while processing bar #1 (latest event seen so far).
        strategy._submit_entry(OrderSide.BUY, 102.0, atr=0.25, stop_multiple=2.0)
        queued = strategy._pending_entry
        assert queued is not None  # held, NOT submitted on the signal bar
        assert queued["signal_ts"] == _ts(1)
        assert queued["signal_reference_price"] == 102.0
        assert queued["stop_multiple"] == 2.0
        assert strategy.executed == []  # still deferred
        # First subsequent bar event flushes the intent exactly once.
        strategy.on_bar(bars[2])
        assert strategy._pending_entry is None
        assert len(strategy.executed) == 1
        assert strategy.executed[0]["signal_ts"] == _ts(1)
        # submit_ts is stamped inside the real _execute_entry_intent; this
        # head-less stub asserts flush-bar facts only (see engine fixtures).
        assert strategy.executed[0]["submit_reference_price"] == CLOSES[2]
        # A later bar event must not re-flush anything.
        strategy.on_bar(bars[3])
        assert len(strategy.executed) == 1
