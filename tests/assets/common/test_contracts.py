"""Asset-neutral contract, instrument, cost and carry interface tests.

Covers PLAN_stocks.md section 6 deliverables:
- explicit asset_class/venue/calendar_id/cost_model_id, no defaults anywhere;
- position-PnL PF strictly separate from return-series PF;
- double canonical serialization determinism;
- immutable CostModelId and neutral CashflowLine result type.
"""

from __future__ import annotations

import hashlib

import pytest

from research.assets.common.carrying_cost import (
    CASHFLOW_KINDS,
    CarryingCostModel,
    CashflowLine,
    CryptoFundingCarry,
    EquityBorrowDividendCarry,
    FxRolloverCarry,
)
from research.assets.common.contracts import (
    AssetExperimentContract,
    MetricReading,
    ScoredResultContract,
    canonical_json,
)
from research.assets.common.execution_cost import (
    CostModelId,
    ExecutionCostEstimate,
    ExecutionCostModel,
)
from research.assets.common.instrument import InstrumentSpec

D1 = hashlib.sha256(b"universe").hexdigest()
D2 = hashlib.sha256(b"arm-config").hexdigest()
D3 = hashlib.sha256(b"provider-schema").hexdigest()


def _contract_kwargs(**overrides):
    kwargs = {
        "experiment_id": "EXP-20260902-0001",
        "asset_class": "US_CASH_EQUITY",
        "venue": "XNYS",
        "calendar_id": "XNYS_SESSIONS_V1",
        "cost_model_id": "EQUITY_TAKER_V1",
        "universe_digest": D1,
        "family_id": "FAM_VOL",
        "arm_id": "ARM_A",
        "arm_config_digest": D2,
    }
    kwargs.update(overrides)
    return kwargs


def _instrument_kwargs(**overrides):
    kwargs = {
        "symbol": "AAPL",
        "venue": "XNYS",
        "asset_class": "US_CASH_EQUITY",
        "tick_size": 0.01,
        "lot_size": 1.0,
        "calendar_id": "XNYS_SESSIONS_V1",
        "cost_model_id": "EQUITY_TAKER_V1",
        "quote_currency": "USD",
    }
    kwargs.update(overrides)
    return kwargs


# --- required identity fields: no defaults ---------------------------------- #
@pytest.mark.parametrize(
    "missing",
    ["asset_class", "venue", "calendar_id", "cost_model_id", "universe_digest", "family_id"],
)
def test_contract_identity_fields_are_required(missing):
    kwargs = _contract_kwargs()
    del kwargs[missing]
    with pytest.raises(TypeError):
        AssetExperimentContract(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize("field", ["asset_class", "venue", "calendar_id", "cost_model_id"])
def test_contract_rejects_empty_identity_values(field):
    with pytest.raises(ValueError):
        AssetExperimentContract(**_contract_kwargs(**{field: ""}))


def test_contract_rejects_non_hex_or_bad_asset_class():
    with pytest.raises(ValueError, match="asset_class"):
        AssetExperimentContract(**_contract_kwargs(asset_class="crypto perp"))
    with pytest.raises(ValueError, match="universe_digest"):
        AssetExperimentContract(**_contract_kwargs(universe_digest="deadbeef"))


def test_contract_calendar_is_referenced_by_id_never_defaulted():
    # A contract cannot be built without naming a calendar; there is no
    # fallback constant anywhere in the contracts module.
    import research.assets.common.contracts as contracts_module

    defaultish = [
        name
        for name in dir(contracts_module)
        if name.upper().startswith(("DEFAULT", "DEFAULT_CALENDAR", "DEFAULT_ASSET"))
    ]
    assert defaultish == []
    contract = AssetExperimentContract(**_contract_kwargs())
    assert contract.calendar_id == "XNYS_SESSIONS_V1"


# --- profit factor separation ------------------------------------------------ #
def test_profit_factors_are_two_distinct_fields():
    contract = AssetExperimentContract(
        **_contract_kwargs(
            position_pnl_profit_factor=MetricReading.known(1.3),
            return_series_profit_factor=MetricReading.known(1.1),
        )
    )
    payload = contract.canonical_payload()
    assert payload["position_pnl_profit_factor"] == {"value": 1.3, "reason": None}
    assert payload["return_series_profit_factor"] == {"value": 1.1, "reason": None}
    assert "profit_factor" not in contract.__dataclass_fields__
    assert not hasattr(contract, "profit_factor")


def test_scored_result_profit_factors_are_keyword_only_and_separate():
    pos_pf = MetricReading.known(1.25)
    series_pf = MetricReading.missing("metric_not_computed")
    scored = ScoredResultContract(
        experiment_id="EXP-20260902-0001",
        asset_class="US_CASH_EQUITY",
        position_pnl_profit_factor=pos_pf,
        return_series_profit_factor=series_pf,
    )
    payload = scored.canonical_payload()
    # Distinct serialized keys, never one shared 'profit_factor' value.
    assert set(payload) >= {"position_pnl_profit_factor", "return_series_profit_factor"}
    assert payload["position_pnl_profit_factor"]["value"] == 1.25
    assert payload["return_series_profit_factor"]["reason"] == "metric_not_computed"
    # Positional swap is structurally impossible (kw_only fields).
    with pytest.raises(TypeError):
        ScoredResultContract(  # type: ignore[misc]
            "EXP-20260902-0001", "US_CASH_EQUITY", pos_pf, series_pf
        )


def test_metric_reading_requires_reason_for_missing_value():
    with pytest.raises(ValueError, match="reason"):
        MetricReading(value=None, reason=None)
    with pytest.raises(ValueError, match="reason"):
        MetricReading(value=None, reason="  ")
    with pytest.raises(ValueError, match="reason"):
        MetricReading(value=1.0, reason="oops")
    assert MetricReading.missing("metric_not_computed").reason == "metric_not_computed"


# --- canonical serialization determinism ------------------------------------- #
def test_double_serialization_determinism_contract():
    contract = AssetExperimentContract(**_contract_kwargs())
    first = contract.canonical_json()
    second = canonical_json(contract.canonical_payload())
    third = canonical_json(contract.canonical_payload())
    assert first == second == third


def test_double_serialization_determinism_instrument_and_scored():
    instrument = InstrumentSpec(**_instrument_kwargs())
    scored = ScoredResultContract(
        experiment_id="EXP-20260902-0001",
        asset_class="US_CASH_EQUITY",
        position_pnl_profit_factor=MetricReading.known(1.2),
        return_series_profit_factor=MetricReading.missing("metric_not_computed"),
    )
    for obj in (instrument, scored):
        once = obj.canonical_json()
        twice = canonical_json(obj.canonical_payload())
        thrice = canonical_json(obj.canonical_payload())
        assert once == twice == thrice


# --- instrument metadata ------------------------------------------------------ #
def test_instrument_validation_positive_tick_lot_and_tokens():
    spec = InstrumentSpec(**_instrument_kwargs())
    assert spec.canonical_payload()["symbol"] == "AAPL"
    with pytest.raises(ValueError, match="tick_size"):
        InstrumentSpec(**_instrument_kwargs(tick_size=0.0))
    with pytest.raises(ValueError, match="lot_size"):
        InstrumentSpec(**_instrument_kwargs(lot_size=-1.0))
    with pytest.raises(ValueError, match="calendar_id"):
        InstrumentSpec(**_instrument_kwargs(calendar_id=""))


def test_instrument_requires_calendar_and_cost_model():
    kwargs = _instrument_kwargs()
    del kwargs["calendar_id"]
    del kwargs["cost_model_id"]
    with pytest.raises(TypeError):
        InstrumentSpec(**kwargs)  # type: ignore[arg-type]


# --- cost model identity + execution cost interface --------------------------- #
def test_cost_model_id_is_immutable_and_hashable():
    model_id = CostModelId("EQUITY_TAKER_V1")
    assert str(model_id) == "EQUITY_TAKER_V1"
    assert model_id == CostModelId("EQUITY_TAKER_V1")
    assert hash(model_id) == hash(CostModelId("EQUITY_TAKER_V1"))
    with pytest.raises(AttributeError):
        model_id.value = "OTHER"  # type: ignore[misc]
    with pytest.raises(ValueError):
        CostModelId("")
    with pytest.raises(ValueError):
        CostModelId("bad model id")


def _estimate(**overrides):
    kwargs = {
        "symbol": "AAPL",
        "side": "BUY",
        "quantity": 100.0,
        "price": 189.25,
        "commission": 1.0,
        "spread_cost": 0.5,
        "slippage_cost": 0.25,
        "impact_cost": 0.125,
        "currency": "USD",
        "cost_model_id": "EQUITY_TAKER_V1",
    }
    kwargs.update(overrides)
    return ExecutionCostEstimate(**kwargs)


def test_execution_cost_estimate_totals_and_validates():
    estimate = _estimate()
    assert estimate.total() == pytest.approx(1.875)
    with pytest.raises(ValueError, match="commission"):
        _estimate(commission=-0.1)
    with pytest.raises(ValueError, match="side"):
        _estimate(side="LONG")
    rebuilt = ExecutionCostEstimate(**estimate.canonical_payload())
    assert rebuilt == estimate


def test_execution_cost_model_is_abstract_with_id_interface():
    with pytest.raises(TypeError):
        ExecutionCostModel()  # type: ignore[abstract]
    assert "model_id" in ExecutionCostModel.__abstractmethods__
    assert "estimate" in ExecutionCostModel.__abstractmethods__


class _StubCostModel(ExecutionCostModel):
    @property
    def model_id(self) -> CostModelId:
        return CostModelId("STUB_V1")

    def estimate(self, *, symbol, side, quantity, price, context=None):
        return _estimate(symbol=symbol, side=side, quantity=quantity, price=price)


def test_stub_cost_model_satisfies_interface():
    model = _StubCostModel()
    assert model.model_id == CostModelId("STUB_V1")
    estimate = model.estimate(symbol="AAPL", side="BUY", quantity=10.0, price=5.0)
    assert estimate.cost_model_id == "EQUITY_TAKER_V1"


# --- carrying cost interface + CashflowLine ----------------------------------- #
def _cashflow(**overrides):
    kwargs = {
        "timestamp_utc": "2026-09-01T00:00:00+00:00",
        "amount": -1.25,
        "currency": "USDT",
        "kind": "FUNDING",
        "instrument_symbol": "BTCUSDT-PERP",
    }
    kwargs.update(overrides)
    return CashflowLine(**kwargs)


def test_cashflow_line_signed_amounts_and_kinds():
    paid = _cashflow()
    received = _cashflow(amount=2.5)
    assert paid.is_paid and not received.is_paid
    assert sorted(CASHFLOW_KINDS) == ["BORROW", "DIVIDEND", "FUNDING", "ROLLOVER"]
    with pytest.raises(ValueError, match="kind"):
        _cashflow(kind="MYSTERY")
    with pytest.raises(ValueError, match="timestamp_utc"):
        _cashflow(timestamp_utc="not-a-timestamp")
    with pytest.raises(ValueError, match="timestamp_utc"):
        _cashflow(timestamp_utc="2026-09-01T00:00:00")  # naive
    with pytest.raises(ValueError, match="finite"):
        _cashflow(amount=float("inf"))
    rebuilt = CashflowLine(**paid.canonical_payload())
    assert rebuilt == paid


def test_carry_models_are_abstract_per_asset_class():
    for cls in (
        CarryingCostModel,
        CryptoFundingCarry,
        EquityBorrowDividendCarry,
        FxRolloverCarry,
    ):
        with pytest.raises(TypeError):
            cls()  # type: ignore[abstract]
    assert "cashflows" in CarryingCostModel.__abstractmethods__
