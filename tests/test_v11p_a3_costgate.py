"""V11 lane A3 tests -- schedule-only cost feasibility gate.

Small synthetic schedules prove each metric, each frozen floor boundary
(one pass case and one fail case per floor), missing-input fail-closed
behaviour, and that the gate never emits a scored outcome field.
"""

from __future__ import annotations

import dataclasses
import json
import math

import pytest

from research.adapter_v10.base import GenericStrategyBase
from research.adapter_v10.protocol import (
    ContractViolation,
    CostModel,
    SettlementPoint,
    StressSpec,
)
from research.v11.cost_feasibility import (
    DAY_NS,
    FLOOR_TABLE,
    KIND_DISCRETIONARY,
    KIND_FORCED_FLAT,
    SCHEMA_VERSION,
    CostFeasibilityReport,
    ScheduleArtifacts,
    ScheduleDecision,
    SignalAvailability,
    STRESS_EXTRA_TICKS,
    STRESS_FEE_MULTIPLIER,
    _GateCostAdapter,
    evaluate_schedule_cost_feasibility,
)

DAY = DAY_NS
PRICE = 100.0
TICK_SIZE = 0.01
SETTLE_OFFSET = int(0.75 * DAY)  # stamps sit at (d - 0.25) days


# --------------------------------------------------------------------------- #
# Synthetic schedule builders
# --------------------------------------------------------------------------- #
def ns_day(d: float) -> int:
    return int(round(d * DAY))


def book(day: float, weights: dict[str, float], kind: str = KIND_DISCRETIONARY) -> ScheduleDecision:
    return ScheduleDecision(instant_ns=ns_day(day), kind=kind, weights=dict(weights))


def cost_model(fee_bps: float = 5.0, tick_floor: int = 1, symbols=()) -> CostModel:
    return CostModel(
        taker_fee_bps=fee_bps,
        adverse_tick_slip_floor=tick_floor,
        default_tick_sizes={sym: TICK_SIZE for sym in symbols},
    )


def settlements_for(symbol: str, days: range) -> tuple[SettlementPoint, ...]:
    return tuple(
        SettlementPoint(publish_ts_ns=ns_day(d) + SETTLE_OFFSET - DAY, value=0.0001)
        for d in days
    )


def flat_prices(instant_ns: int, symbols) -> dict[str, float]:
    return {sym: PRICE for sym in symbols}


def build(
    instant_days: list[float],
    decisions: list[ScheduleDecision],
    *,
    fee_bps: float = 5.0,
    tick_floor: int = 1,
    symbols: tuple[str, ...] = ("SYM_A", "SYM_B", "SYM_C", "SYM_D", "SYM_E"),
    price_symbols=None,
    settle_days: range = range(1, 400),
    settle_symbols=None,
    availability: str = "all",
) -> ScheduleArtifacts:
    cost = cost_model(fee_bps, tick_floor, symbols)
    fills = {
        d.instant_ns: flat_prices(d.instant_ns, price_symbols or symbols) for d in decisions
    }
    settle_syms = list(settle_symbols) if settle_symbols is not None else list(symbols)
    settl = {sym: settlements_for(sym, settle_days) for sym in settle_syms}
    if availability == "all":
        avail = {
            d.instant_ns: SignalAvailability(instant_ns=d.instant_ns, available=True)
            for d in decisions
        }
    elif availability == "none-supplied":
        avail = None
    else:  # explicit mapping expected
        avail = availability
    return ScheduleArtifacts(
        instants_ns=tuple(ns_day(d) for d in instant_days),
        decisions={d.instant_ns: d for d in decisions},
        fill_prices=fills,
        settlements=settl,
        cost_model=cost,
        signal_availability=avail,
    )


def five_equal_book(day: float, kind: str = KIND_DISCRETIONARY) -> ScheduleDecision:
    return book(day, {f"SYM_{c}": 0.2 for c in "ABCDE"}, kind=kind)


def floor_row(report, floor_id: str) -> dict:
    return next(row for row in report.payload["floors"] if row["floor_id"] == floor_id)


def metric(report, key: str) -> dict:
    return report.payload["metrics"][key]


# --------------------------------------------------------------------------- #
# Canonical full-PASS schedule (also the reuse + determinism fixture)
# --------------------------------------------------------------------------- #
def pass_schedule() -> ScheduleArtifacts:
    """53 weekly instants over 364 days; terminal force-flat at the end."""
    days = [float(7 * i) for i in range(53)]
    decisions = [five_equal_book(d) for d in days[:-1]]
    decisions.append(book(days[-1], {}, kind=KIND_FORCED_FLAT))
    return build(days, decisions)


def test_canonical_pass_schedule_passes_every_floor():
    report = evaluate_schedule_cost_feasibility(pass_schedule())
    assert report.verdict == "PASS"
    assert all(row["status"] == "PASS" for row in report.payload["floors"])
    assert report.payload["unavailable_metrics"] == []
    # window / decisions
    assert metric(report, "window_days")["value"] == 364.0
    assert metric(report, "discretionary_decision_count")["value"] == 52
    assert metric(report, "forced_flat_decision_count")["value"] == 1
    assert metric(report, "decisions_per_365d")["value"] == round(52 * 365 / 364, 9)


def test_payload_is_json_safe_and_schema_stamped():
    report = evaluate_schedule_cost_feasibility(pass_schedule())
    assert report.payload["schema_version"] == SCHEMA_VERSION
    json.dumps(report.payload)  # must not raise


def test_gate_is_deterministic():
    first = evaluate_schedule_cost_feasibility(pass_schedule())
    second = evaluate_schedule_cost_feasibility(pass_schedule())
    assert first.verdict == second.verdict
    assert first.payload == second.payload


# --------------------------------------------------------------------------- #
# Metric proofs
# --------------------------------------------------------------------------- #
def test_one_way_turnover_from_target_deltas_exact():
    decisions = [
        book(0, {"A": 0.5}),
        book(10, {"A": 0.2, "B": 0.3}),
        book(20, {}, kind=KIND_FORCED_FLAT),
    ]
    artifacts = build([0.0, 10.0, 20.0], decisions, symbols=("A", "B"))
    report = evaluate_schedule_cost_feasibility(artifacts)
    assert metric(report, "one_way_turnover_discretionary")["value"] == 1.1
    assert metric(report, "one_way_turnover_forced_flat")["value"] == 0.5
    assert metric(report, "one_way_turnover_total")["value"] == 1.6
    shares = metric(report, "per_symbol_turnover_share")["value"]
    assert shares["A"] == 0.625
    assert shares["B"] == 0.375
    assert metric(report, "max_symbol_turnover_share_symbol")["value"] == "A"


def test_holding_duration_median_and_max():
    days = [0.0, 2.0, 4.0, 6.0, 8.0, 10.0]
    decisions = [
        book(0, {"A": 0.4, "B": 0.3}),
        book(2, {"A": 0.4, "B": 0.3, "C": 0.3}),
        book(4, {"A": 0.4, "C": 0.3}),
        book(6, {"A": 0.4, "C": 0.3}),
        book(8, {"A": 0.4}),
        book(10, {}, kind=KIND_FORCED_FLAT),
    ]
    artifacts = build(days, decisions, symbols=("A", "B", "C"))
    report = evaluate_schedule_cost_feasibility(artifacts)
    # spans: A (0,10]=10d, B (0,4]=4d, C (2,8]=6d
    assert metric(report, "completed_holding_span_count")["value"] == 3
    assert metric(report, "censored_open_span_count")["value"] == 0
    assert metric(report, "median_intended_holding_days")["value"] == 6.0
    assert metric(report, "max_intended_holding_days")["value"] == 10.0


def test_censored_open_spans_are_excluded_not_inferred():
    days = [0.0, 10.0]
    decisions = [book(0, {"A": 1.0}), book(10, {"A": 1.0})]
    artifacts = build(days, decisions, symbols=("A",))
    report = evaluate_schedule_cost_feasibility(artifacts)
    assert metric(report, "censored_open_span_count")["value"] == 1
    assert metric(report, "median_intended_holding_days")["status"] == "UNAVAILABLE"


def test_funding_event_count_while_held():
    days = [0.0, 4.0, 6.0, 10.0]
    decisions = [
        book(0, {"A": 0.5}),
        book(4, {"A": 0.5, "B": 0.5}),
        book(6, {"A": 0.5}),
        book(10, {}, kind=KIND_FORCED_FLAT),
    ]
    artifacts = build(days, decisions, symbols=("A", "B"), settle_days=range(1, 11))
    report = evaluate_schedule_cost_feasibility(artifacts)
    # A held (0,10]: stamps at 0.75d..9.75d -> 10 events; B held (4,6]: 4.75d, 5.75d -> 2
    assert metric(report, "funding_events_while_held_total")["value"] == 12
    assert metric(report, "funding_events_per_365d")["value"] == round(12 * 365 / 10, 9)


def test_funding_events_use_only_held_symbols_cadence():
    """Symbols flat for the whole window contribute zero funding events."""
    days = [0.0, 10.0]
    decisions = [book(0, {"A": 0.5}), book(10, {}, kind=KIND_FORCED_FLAT)]
    artifacts = build(days, decisions, symbols=("A", "B"), settle_days=range(1, 11))
    report = evaluate_schedule_cost_feasibility(artifacts)
    # A span (0,10] -> 10 events; B never held -> 0
    assert metric(report, "funding_events_while_held_total")["value"] == 10


def test_signal_availability_and_missingness_reported():
    days = [float(d) for d in range(10)]
    decisions = [book(d, {"A": 1.0}) for d in days]
    avail = {
        ns_day(d): SignalAvailability(
            instant_ns=ns_day(d),
            available=d not in (3, 7),
            missing_symbols=() if d not in (3, 7) else ("SIG_X",),
        )
        for d in days
    }
    artifacts = build(days, decisions, symbols=("A",), availability=avail)
    report = evaluate_schedule_cost_feasibility(artifacts)
    assert metric(report, "signal_availability_fraction")["value"] == 0.8
    assert metric(report, "signal_missing_instant_count")["value"] == 2
    assert metric(report, "signal_missing_instants")["value"] == [ns_day(3), ns_day(7)]


def test_cost_math_is_reused_from_the_adapter_not_reforked():
    artifacts = pass_schedule()
    report = evaluate_schedule_cost_feasibility(artifacts)
    adapter = _GateCostAdapter(artifacts.cost_model, artifacts.settlements)
    baseline = StressSpec(name="baseline", tick_slip_ticks=1)
    stressed = StressSpec(
        name="stress", fee_multiplier=STRESS_FEE_MULTIPLIER, tick_slip_ticks=1 + STRESS_EXTRA_TICKS
    )
    prev: dict[str, float] = {}
    expected_base: list[float] = []
    expected_stressed: list[float] = []
    for instant in artifacts.instants_ns:
        new_book = dict(artifacts.decisions[instant].weights)
        prices = dict(artifacts.fill_prices[instant])
        expected_base.append(
            GenericStrategyBase.rebalance_cost_between(
                adapter, prev, new_book, prices=prices, stress=baseline
            )
        )
        expected_stressed.append(
            GenericStrategyBase.rebalance_cost_between(
                adapter, prev, new_book, prices=prices, stress=stressed
            )
        )
        prev = new_book
    assert (
        metric(report, "annualised_base_cost_drag_frac_of_gross_total_cost")["value"]
        == round(math.fsum(expected_base), 9)
    )
    assert (
        metric(report, "annualised_stressed_cost_drag_frac_of_gross_total_cost")["value"]
        == round(math.fsum(expected_stressed), 9)
    )
    assert metric(report, "annualised_stressed_cost_drag_frac_of_gross")["value"] > metric(
        report, "annualised_base_cost_drag_frac_of_gross"
    )["value"]


# --------------------------------------------------------------------------- #
# Frozen floor 1: <= 60 discretionary decisions per 365 days
# --------------------------------------------------------------------------- #
def evenly_spread_books(n_instants: int) -> tuple[list[float], list[ScheduleDecision]]:
    last = 365.0
    days = [round(i * last / (n_instants - 1), 9) for i in range(n_instants)]
    decisions = [five_equal_book(d) for d in days[:-1]]
    decisions.append(book(days[-1], {}, kind=KIND_FORCED_FLAT))
    return days, decisions


def test_floor_decisions_boundary_60_per_365d_passes():
    days, decisions = evenly_spread_books(61)  # 60 discretionary over exactly 365d
    report = evaluate_schedule_cost_feasibility(build(days, decisions))
    row = floor_row(report, "max_discretionary_decisions_per_365d")
    assert row["observed"] == 60.0
    assert row["status"] == "PASS"
    assert report.verdict == "PASS"


def test_floor_decisions_61_per_365d_fails():
    days, decisions = evenly_spread_books(62)  # 61 discretionary over exactly 365d
    report = evaluate_schedule_cost_feasibility(build(days, decisions))
    row = floor_row(report, "max_discretionary_decisions_per_365d")
    assert row["observed"] == 61.0
    assert row["status"] == "FAIL"
    assert report.verdict == "FAIL"
    # every other floor still passes in this isolated case
    others = [r for r in report.payload["floors"] if r["floor_id"] != "max_discretionary_decisions_per_365d"]
    assert all(r["status"] == "PASS" for r in others)


def test_forced_flat_actions_stay_out_of_the_discretionary_count():
    report = evaluate_schedule_cost_feasibility(pass_schedule())
    assert metric(report, "forced_flat_decision_count")["value"] == 1
    assert metric(report, "discretionary_decision_count")["value"] == 52
    # per-365d normalisation uses ONLY discretionary decisions
    assert metric(report, "decisions_per_365d")["value"] == round(52 * 365 / 364, 9)


# --------------------------------------------------------------------------- #
# Frozen floor 2: median intended holding >= 3 calendar days
# --------------------------------------------------------------------------- #
def holding_schedule(exit_day: float) -> ScheduleArtifacts:
    days = [0.0, exit_day, exit_day + 2.0, 365.0]
    first = {f"SYM_{c}": 0.2 for c in "ABCDE"}
    second = {f"SYM_{c}": 0.2 for c in "FGHIJ"}
    decisions = [
        book(0.0, first),
        book(exit_day, second),
        book(exit_day + 2.0, second),
        book(365.0, second),
    ]
    symbols = tuple(sorted(set(first) | set(second)))
    return build(days, decisions, symbols=symbols)


def test_floor_median_holding_boundary_3_days_passes():
    report = evaluate_schedule_cost_feasibility(holding_schedule(3.0))
    row = floor_row(report, "min_median_intended_holding_days")
    assert row["observed"] == 3.0
    assert row["status"] == "PASS"


def test_floor_median_holding_below_3_days_fails():
    report = evaluate_schedule_cost_feasibility(holding_schedule(2.0))
    row = floor_row(report, "min_median_intended_holding_days")
    assert row["observed"] == 2.0
    assert row["status"] == "FAIL"
    assert report.verdict == "FAIL"
    others = [r for r in report.payload["floors"] if r["floor_id"] != "min_median_intended_holding_days"]
    assert all(r["status"] == "PASS" for r in others)


# --------------------------------------------------------------------------- #
# Frozen floors 3+4: annualised base drag <= 8%, stressed drag <= 12%
# --------------------------------------------------------------------------- #
def swap_schedule(n_instants: int) -> ScheduleArtifacts:
    """Alternate a 10-symbol full book with a flat discretionary book.

    Every transition then trades exactly 1.0 one-way (entry or exit), the
    average gross capital is 0.5 (last instant flat keeps the parity even),
    and with a 10 bps fee floor the base drag lands on exact calibration
    points: n=40 -> 0.08 (boundary PASS), n=42 -> 0.084 (FAIL),
    stressed (x1.5 fee + 2 ticks) n=40 -> 0.136 (FAIL), n=20 -> 0.068 (PASS).
    """
    full_book = {f"A{i}": 0.1 for i in range(10)}
    days = [round(i * 365.0 / (n_instants - 1), 9) for i in range(n_instants)]
    decisions = [
        book(d, full_book if i % 2 == 0 else {}) for i, d in enumerate(days)
    ]
    symbols = tuple(sorted(full_book))
    return build(
        days,
        decisions,
        fee_bps=10.0,
        tick_floor=0,
        symbols=symbols,
    )


def test_floor_base_drag_boundary_exactly_8pct_passes():
    report = evaluate_schedule_cost_feasibility(swap_schedule(40))
    base = floor_row(report, "max_base_cost_drag_frac_of_gross")
    assert base["observed"] == 0.08  # 40 x 1.0 x 0.001 / 0.5 gross
    assert base["status"] == "PASS"


def test_floor_base_drag_above_8pct_fails():
    report = evaluate_schedule_cost_feasibility(swap_schedule(42))
    base = floor_row(report, "max_base_cost_drag_frac_of_gross")
    assert base["observed"] == round(42 * 0.001 / 0.5, 9)  # 0.084 > 0.08
    assert base["status"] == "FAIL"
    assert report.verdict == "FAIL"


def test_floor_stressed_drag_above_12pct_fails_while_base_passes():
    report = evaluate_schedule_cost_feasibility(swap_schedule(40))
    stressed = floor_row(report, "max_stressed_cost_drag_frac_of_gross")
    assert stressed["observed"] == round(40 * 0.0017 / 0.5, 9)  # 0.136 > 0.12
    assert stressed["status"] == "FAIL"
    assert floor_row(report, "max_base_cost_drag_frac_of_gross")["status"] == "PASS"


def test_floor_stressed_drag_within_12pct_passes():
    report = evaluate_schedule_cost_feasibility(swap_schedule(20))
    stressed = floor_row(report, "max_stressed_cost_drag_frac_of_gross")
    assert stressed["observed"] == round(20 * 0.0017 / 0.5, 9)  # 0.068 <= 0.12
    assert stressed["status"] == "PASS"
    assert report.verdict == "PASS"


# --------------------------------------------------------------------------- #
# Frozen floor 5: no symbol > 25% of total turnover
# --------------------------------------------------------------------------- #
def test_floor_turnover_share_boundary_exactly_25pct_passes():
    days = [float(7 * i) for i in range(53)]
    decisions = [book(d, {f"SYM_{c}": 0.25 for c in "ABCD"}) for d in days[:-1]]
    decisions.append(book(days[-1], {}, kind=KIND_FORCED_FLAT))
    report = evaluate_schedule_cost_feasibility(
        build(days, decisions, symbols=("SYM_A", "SYM_B", "SYM_C", "SYM_D"))
    )
    row = floor_row(report, "max_symbol_turnover_share")
    assert row["observed"] == 0.25
    assert row["status"] == "PASS"


def test_floor_turnover_share_above_25pct_fails_in_isolation():
    days = [float(7 * i) for i in range(53)]
    decisions = []
    for i, d in enumerate(days[:-1]):
        weights = {f"SYM_{c}": 0.125 for c in "ABCD"}
        weights["X"] = 0.5 if i % 2 == 0 else 0.0
        decisions.append(book(d, weights))
    decisions.append(book(days[-1], {}, kind=KIND_FORCED_FLAT))
    symbols = ("SYM_A", "SYM_B", "SYM_C", "SYM_D", "X")
    report = evaluate_schedule_cost_feasibility(build(days, decisions, symbols=symbols))
    row = floor_row(report, "max_symbol_turnover_share")
    assert row["status"] == "FAIL"
    assert row["observed"] > 0.25
    others = [r for r in report.payload["floors"] if r["floor_id"] != "max_symbol_turnover_share"]
    assert all(r["status"] == "PASS" for r in others)
    assert report.verdict == "FAIL"


# --------------------------------------------------------------------------- #
# Fail-closed behaviour
# --------------------------------------------------------------------------- #
def test_missing_fill_price_fails_closed_to_unavailable():
    artifacts = pass_schedule()
    first_instant = artifacts.instants_ns[0]
    broken_fills = {
        k: ({sym: p for sym, p in v.items() if sym != "SYM_A"} if k == first_instant else v)
        for k, v in artifacts.fill_prices.items()
    }
    broken = ScheduleArtifacts(
        instants_ns=artifacts.instants_ns,
        decisions=artifacts.decisions,
        fill_prices=broken_fills,
        settlements=artifacts.settlements,
        cost_model=artifacts.cost_model,
        signal_availability=artifacts.signal_availability,
    )
    report = evaluate_schedule_cost_feasibility(broken)
    assert report.verdict == "UNAVAILABLE_FAIL_CLOSED"
    assert metric(report, "annualised_base_cost_drag_frac_of_gross")["status"] == "UNAVAILABLE"
    assert metric(report, "annualised_stressed_cost_drag_frac_of_gross")["status"] == "UNAVAILABLE"
    drag_rows = [
        r
        for r in report.payload["floors"]
        if "cost_drag" in r["floor_id"]
    ]
    assert all(r["status"] == "UNAVAILABLE" for r in drag_rows)


def test_missing_settlement_cadence_fails_closed():
    artifacts = pass_schedule()
    partial = {
        sym: pts for sym, pts in artifacts.settlements.items() if sym != "SYM_E"
    }
    broken = ScheduleArtifacts(
        instants_ns=artifacts.instants_ns,
        decisions=artifacts.decisions,
        fill_prices=artifacts.fill_prices,
        settlements=partial,
        cost_model=artifacts.cost_model,
        signal_availability=artifacts.signal_availability,
    )
    report = evaluate_schedule_cost_feasibility(broken)
    assert report.verdict == "UNAVAILABLE_FAIL_CLOSED"
    funding = metric(report, "funding_events_while_held_total")
    assert funding["status"] == "UNAVAILABLE"
    assert "SYM_E" in funding["reason"]


def test_missing_signal_availability_fails_closed():
    artifacts = pass_schedule()
    broken = ScheduleArtifacts(
        instants_ns=artifacts.instants_ns,
        decisions=artifacts.decisions,
        fill_prices=artifacts.fill_prices,
        settlements=artifacts.settlements,
        cost_model=artifacts.cost_model,
        signal_availability=None,
    )
    report = evaluate_schedule_cost_feasibility(broken)
    assert report.verdict == "UNAVAILABLE_FAIL_CLOSED"
    assert metric(report, "signal_availability_fraction")["status"] == "UNAVAILABLE"
    assert metric(report, "signal_missing_instant_count")["status"] == "UNAVAILABLE"
    # the missing-input metrics are named on the report and no verdict is PASS
    assert "signal_availability_fraction" in report.payload["unavailable_metrics"]
    assert report.verdict != "PASS"


def test_partial_signal_availability_coverage_fails_closed():
    artifacts = pass_schedule()
    avail = dict(artifacts.signal_availability)
    avail.pop(artifacts.instants_ns[-1])
    broken = ScheduleArtifacts(
        instants_ns=artifacts.instants_ns,
        decisions=artifacts.decisions,
        fill_prices=artifacts.fill_prices,
        settlements=artifacts.settlements,
        cost_model=artifacts.cost_model,
        signal_availability=avail,
    )
    report = evaluate_schedule_cost_feasibility(broken)
    assert report.verdict == "UNAVAILABLE_FAIL_CLOSED"
    assert metric(report, "signal_availability_fraction")["status"] == "UNAVAILABLE"


def test_missing_decision_book_is_structural_contract_violation():
    artifacts = pass_schedule()
    with pytest.raises(ContractViolation):
        ScheduleArtifacts(
            instants_ns=artifacts.instants_ns,
            decisions={
                k: v for k, v in artifacts.decisions.items() if k != artifacts.instants_ns[0]
            },
            fill_prices=artifacts.fill_prices,
            settlements=artifacts.settlements,
            cost_model=artifacts.cost_model,
            signal_availability=artifacts.signal_availability,
        )


def test_unknown_decision_kind_is_rejected():
    with pytest.raises(ContractViolation):
        ScheduleDecision(instant_ns=ns_day(0), kind="SOMETHING_ELSE", weights={})


# --------------------------------------------------------------------------- #
# Outcome blindness: the gate never emits a return/PnL field
# --------------------------------------------------------------------------- #
FORBIDDEN_KEY_TOKENS = (
    "return",
    "pnl",
    "profit",
    "sharpe",
    "drawdown",
    "equity",
    "cum",
    "wealth",
)


def _walk_keys(node) -> set[str]:
    keys: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            keys.add(str(key).lower())
            keys |= _walk_keys(value)
    elif isinstance(node, (list, tuple)):
        for item in node:
            keys |= _walk_keys(item)
    return keys


def test_no_report_key_contains_a_scored_outcome_token():
    scenarios = [
        pass_schedule(),
        swap_schedule(40),
        holding_schedule(2.0),
    ]
    artifacts = pass_schedule()
    scenarios.append(
        ScheduleArtifacts(
            instants_ns=artifacts.instants_ns,
            decisions=artifacts.decisions,
            fill_prices=artifacts.fill_prices,
            settlements=artifacts.settlements,
            cost_model=artifacts.cost_model,
            signal_availability=None,
        )
    )
    for artifacts in scenarios:
        payload = evaluate_schedule_cost_feasibility(artifacts).payload
        keys = _walk_keys(payload)
        for key in keys:
            for token in FORBIDDEN_KEY_TOKENS:
                assert token not in key, f"forbidden outcome token {token!r} in key {key!r}"


def test_report_dataclass_fields_are_outcome_blind():
    field_names = [f.name.lower() for f in dataclasses.fields(CostFeasibilityReport)]
    for name in field_names:
        for token in FORBIDDEN_KEY_TOKENS:
            assert token not in name


def test_public_module_surface_is_outcome_blind():
    import research.v11.cost_feasibility as module

    public = [name for name in dir(module) if not name.startswith("_")]
    for name in public:
        for token in ("pnl", "profit", "sharpe", "drawdown"):
            assert token not in name.lower()


def test_attestation_asserts_no_scored_series_emitted():
    report = evaluate_schedule_cost_feasibility(pass_schedule())
    attestation = report.payload["outcome_blind_attestation"]
    assert attestation["schedule_artifacts_only"] is True
    assert attestation["scored_outcome_series_emitted"] is False


def test_frozen_floor_table_matches_plan_values():
    thresholds = {row["floor_id"]: row["frozen_threshold"] for row in FLOOR_TABLE}
    assert thresholds == {
        "max_discretionary_decisions_per_365d": 60.0,
        "min_median_intended_holding_days": 3.0,
        "max_base_cost_drag_frac_of_gross": 0.08,
        "max_stressed_cost_drag_frac_of_gross": 0.12,
        "max_symbol_turnover_share": 0.25,
    }
