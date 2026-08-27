"""G3 FAIL-FIRST adapter acceptance suite -- BG-1..BG-6, G15, F2/G-H06, G17.

STATUS AT COMMIT TIME (sprint V10P-R, lane ``v10p-g3-qa``, bootstrap
``5bb1a90551c8f7823773af713316a45e0ca070cd``)
-------------------------------------------------------------
``research/adapter_v10`` DOES NOT EXIST YET.  Importing it raises ImportError,
therefore **this module fails at pytest collection**: that RED state is the
intended, scientific status of an acceptance suite that gates an interface
before it is implemented.  Recorded in
``research/audits/v10/g3_adapter_acceptance.json`` as
``clearly_expected_initial_state = "RED"``.

Rules honoured by this file
---------------------------
* NO skipif/skip/importorskip markers -- a missing adapter is a RED collection
  error, never a silent skip.
* Assertions are NOT relaxed: they are the acceptance bar G1/G2 must meet.
  Only the single frozen import block below may be touched at integration time
  (and only to align it with the implemented surface, which must itself match
  the frozen contract documented there -- any mismatch is a finding, not a
  test change).
* These tests are independent of G1/G2: they import ONLY ``research.adapter_v10``
  plus frozen repo constants (``research.hyp_a8_m01``, ``research.contract_v10``,
  ``research.cache_v10``, ``research.resource_governor_v10``).  No G1/G2 module
  is imported by name.

FROZEN ADAPTER INTERFACE ASSUMED BY THIS SUITE (A1 must adjudicate)
-------------------------------------------------------------------
Package ``research/adapter_v10`` exporting, at minimum::

    ADAPTER_INTERFACE_VERSION: str            # non-empty
    GenericRunnerV10                          # BG-1/BG-2/BG-4/BG-6 driver class
        def __init__(self, *, strategy: Any, config: Mapping[str, Any])
        strategy must expose, through the plugin protocol (NO family ids):
            strategy_id, config, schedule_provider
        methods:
            compute_fold_metrics(unit_gross_returns_by_fold) -> Mapping
            convert_target_book(decision_ns, target_book, prior_weights,
                                events, tick_sizes=None, stress=None) -> Mapping
            schedule(scenario) -> Mapping           # M01-shaped rows
            finalise_schedule_payload(schedule) -> Mapping
            stress_variants(cohort, fold_labels) -> list[Mapping]
            finalize_stress(results_by_variant_id, required_ids) -> Mapping
            publish_trial(entry, ledger_path) -> Mapping
    checked_funding_accrual(holdings, settlements) -> Mapping        # BG-3/G15
    cache_decision(payload_or_path) -> Mapping                       # F2/G-H06
    resource_cap_report(payload_or_path) -> Mapping                  # G17
    validate_resource_cap_report(payload) -> Mapping                 # G17

Returned mappings carry the exact keys asserted below (asserted with ``==`` on
required subsets, never by loosening).
"""

from __future__ import annotations

import json
import math
from decimal import Decimal
from typing import Any, Dict, List, Mapping, Sequence

import pytest

from research.adapter_v10 import (          # FAIL-FIRST: module does not exist yet
    ADAPTER_INTERFACE_VERSION,
    GenericRunnerV10,
    cache_decision,
    checked_funding_accrual,
    resource_cap_report,
    validate_resource_cap_report,
)
from research.cache_v10 import SharedCacheMergeGate
from research.contract_v10 import STRESS_MATRIX_V10
from research.global_ledger import verify_append_only
from research.hyp_a8_m01 import (
    ADVERSE_TICK_SLIP_FLOOR,
    CAP,
    DAY_NS,
    FORCE_FLAT_REASON,
    FORCE_FLAT_STATUS,
    GROSS_TARGET,
    HoldingSpan,
    M01Bar,
    StressParams,
    TAKER_FEE_FLOOR_BPS,
    apply_stress_filter,
    parse_iso_utc_ns,
    payload_sha256,
    resolve_fill_event,
    traded_notional,
)
from research.pit_hooks_v10 import InfoPoint
from research.resource_governor_v10 import MIN_RESERVED_RAM_GB

#: H08 cross-reference for the audit artifact (which cases each test gates).
H08_TEST_REF: Dict[str, str] = {
    "BG1": "test_bg1_fold_metrics_hand_computed_per_fold",
    "BG2": "test_bg2_target_book_fill_payload_exact_keys_and_values",
    "BG4": "test_bg4_stress_variant_matrix_must_be_complete",
    "BG5": "test_bg5_flat_hard_benchmark_zero_series_exact",
    "BG6": "test_bg6_ledger_idempotency_duplicate_publish_rejected",
    "G15": "test_g15_checked_accrual_hand_computed_long_short_mixed",
    "F2": "test_f2_cache_decision_enabled_only_with_complete_proof_pair",
    "G17": "test_g17_final_cap_is_min_owner_ceiling_measured_safe_cap",
}


def _runner() -> GenericRunnerV10:
    """A minimal deterministic dummy strategy plugin (family-neutral)."""
    strategy = _DummyStrategy()
    return GenericRunnerV10(strategy=strategy, config=_DUMMY_CONFIG)


class _DummyStrategy:
    """Smallest possible plugin proving the adapter is generic (no M01 ids)."""

    strategy_id = "DUMMY_V10_G3"

    def __init__(self) -> None:
        self.config = dict(_DUMMY_CONFIG)
        self.schedule_provider = "injected_fixture_rows"


_DUMMY_CONFIG: Dict[str, Any] = {
    "cohort": ["AAAUSDT", "BBBUSDT"],
    "window_start_iso": "2025-09-01T00:00:00Z",
    "window_end_iso": "2025-09-03T00:00:00Z",
    "cap": CAP,
    "gross": GROSS_TARGET,
    "taker_fee_bps": TAKER_FEE_FLOOR_BPS,
    "adverse_tick_slip": ADVERSE_TICK_SLIP_FLOOR,
}


# ========================================================================= #
# BG-1  schedule -> fold-level expectancy / PF / MDD (hand-computed values)
# ========================================================================= #
FOLD_RETURNS: Dict[str, List[float]] = {
    "F1": [0.01, 0.02, -0.01],
    "F2": [-0.02, 0.04],
}


def _independent_oracle(returns: Sequence[float]) -> Dict[str, float]:
    wins = math.fsum(r for r in returns if r > 0.0)
    losses = math.fsum(r for r in returns if r <= 0.0)
    equity, peak, mdd = 1.0, 1.0, 0.0
    for r in returns:
        equity *= 1.0 + float(r)
        peak = max(peak, equity)
        mdd = max(mdd, 1.0 - equity / peak)
    return {
        "expectancy": math.fsum(returns) / len(returns),
        "profit_factor": math.inf if losses == 0.0 else wins / abs(losses),
        "max_drawdown": mdd,
    }


def test_bg1_fold_metrics_hand_computed_per_fold():
    """BG-1: two synthetic folds must produce EXACTLY these hand values."""
    runner = _runner()
    metrics = runner.compute_fold_metrics(dict(FOLD_RETURNS))

    raw_folds = metrics["folds"]
    if isinstance(raw_folds, Mapping):
        entries = [dict(value, fold_id=key) for key, value in raw_folds.items()]
    else:
        entries = list(raw_folds)
    assert [entry["fold_id"] for entry in entries] == ["F1", "F2"], (
        "fold identity and chronological order must be preserved"
    )

    folds = {entry["fold_id"]: entry for entry in entries}

    f1 = folds["F1"]
    assert f1["expectancy"] == pytest.approx(
        float(Decimal("0.02") / Decimal(3)), rel=1e-12
    )
    assert f1["profit_factor"] == pytest.approx(3.0, rel=1e-12)
    assert f1["max_drawdown"] == pytest.approx(0.01, rel=1e-6)
    assert f1["n_days"] == 3

    f2 = folds["F2"]
    assert f2["expectancy"] == pytest.approx(0.01, rel=1e-12)
    assert f2["profit_factor"] == pytest.approx(2.0, rel=1e-12)
    assert f2["max_drawdown"] == pytest.approx(0.02, rel=1e-6)
    assert f2["n_days"] == 2

    # Pooled aggregate over both folds, independent of the adapter's internals.
    pooled = _independent_oracle(FOLD_RETURNS["F1"] + FOLD_RETURNS["F2"])
    aggregate = metrics["aggregate"]
    assert aggregate["expectancy"] == pytest.approx(pooled["expectancy"], rel=1e-12)
    assert aggregate["profit_factor"] == pytest.approx(
        float(Decimal("0.07") / Decimal("0.03")), rel=1e-12
    )
    assert aggregate["max_drawdown"] == pytest.approx(pooled["max_drawdown"], rel=1e-9)


def test_bg1_fold_metrics_are_deterministic_payload_hashes():
    """Same input twice => identical payload hash (deterministic artifacts)."""
    runner = _runner()
    first = runner.compute_fold_metrics(dict(FOLD_RETURNS))
    second = runner.compute_fold_metrics(dict(FOLD_RETURNS))
    assert payload_sha256(first) == payload_sha256(second)


# ========================================================================= #
# BG-2  target book -> fill / scoring payload, force-flat terminal row
# ========================================================================= #
_PRICES = {"AAAUSDT": 100.0, "BBBUSDT": 200.0}
_TICKS = {"AAAUSDT": 0.01, "BBBUSDT": 0.01}
_T0 = parse_iso_utc_ns("2025-09-02T00:00:00Z")
_T_END = _T0 + DAY_NS


def _events_for(symbols: Sequence[str], decision_ns: int) -> Dict[str, Any]:
    events: Dict[str, Any] = {}
    for symbol in symbols:
        bars = _dummy_bars(symbol, decision_ns)
        events[symbol] = resolve_fill_event(bars, symbol, decision_ns=decision_ns)
    return events


def _dummy_bars(symbol: str, decision_ns: int):
    """One completed 15m bar COVERING the decision instant (fill at D's open)."""
    price = _PRICES[symbol]
    return [
        M01Bar(
            # close stamp sits a shave inside the grid: bar_open <= D < close
            ts_event_ns=decision_ns + 900_000_000_000 - 100_000,
            ts_init_ns=decision_ns + 900_000_000_000 - 100_000,
            open=price,
            high=price * 1.01,
            low=price * 0.99,
            close=price * 1.001,
            volume=1_000.0,
            quote_volume=1_000.0 * price,
            count=11,
            taker_buy_quote_volume=0.55 * 1_000.0 * price,
        )
    ]


def test_bg2_target_book_fill_payload_exact_keys_and_values():
    """BG-2: fill payload must expose exact keys and hand-computed values."""
    runner = _runner()
    target_book = {"AAAUSDT": 0.30, "BBBUSDT": -0.30}
    prior: Dict[str, float] = {}

    payload = runner.convert_target_book(
        _T0, target_book, prior, _events_for(target_book, _T0), tick_sizes=_TICKS
    )

    required_keys = {
        "decision_ns",
        "fills",
        "turnover_one_side",
        "cost_per_unit_gross",
        "is_force_flat_boundary",
    }
    assert required_keys <= set(payload), f"missing payload keys: {required_keys - set(payload)}"
    assert payload["decision_ns"] == _T0
    assert payload["is_force_flat_boundary"] is False

    fills = {entry["symbol"]: entry for entry in payload["fills"]}
    assert set(fills) == set(target_book)
    for symbol, weight in target_book.items():
        entry = fills[symbol]
        assert entry["target_weight"] == pytest.approx(weight, abs=1e-12)
        assert entry["prior_weight"] == 0.0
        assert entry["status"] == "FILLED_NEXT_EVENT"
        assert entry["applied"] is True
        assert entry["event_offset"] == 0
        assert entry["price"] == pytest.approx(_PRICES[symbol], rel=1e-12)
        assert entry["signed_weight_change"] == pytest.approx(weight, abs=1e-12)
        assert {"fill_open_ns", "fill_bar_close_ns"} <= set(entry)
        assert entry["fill_open_ns"] <= _T0 < entry["fill_bar_close_ns"]

    assert payload["turnover_one_side"] == pytest.approx(
        traded_notional(prior, target_book), rel=1e-12
    )
    # Hand-computed baseline cost: 0.30*(5bps+1tick) + 0.30*(5bps+0.5tick) = 3.45e-4
    assert payload["cost_per_unit_gross"] == pytest.approx(
        float(Decimal("0.000345")), rel=1e-12
    )

    # Stress plumbing is a pure parameter change, never a code change.
    stressed = runner.convert_target_book(
        _T0, target_book, prior, _events_for(target_book, _T0),
        tick_sizes=_TICKS, stress=StressParams(fee_multiplier=1.5),
    )
    assert stressed["cost_per_unit_gross"] == pytest.approx(
        float(Decimal("0.000495")), rel=1e-12
    )


def test_bg2_force_flat_boundary_is_mandatory_and_terminal_row_is_flat():
    """BG-2: at the final scored boundary the book MUST be flattened."""
    runner = _runner()
    prior_book = {"AAAUSDT": 0.30, "BBBUSDT": -0.30}

    payload = runner.convert_target_book(
        _T_END,
        {"AAAUSDT": 0.30, "BBBUSDT": -0.30},          # targets are IRRELEVANT here
        prior_book,
        _events_for(prior_book, _T_END),
        tick_sizes=_TICKS,
        force_flat_boundary_ns=_T_END,
    )

    assert payload["is_force_flat_boundary"] is True
    assert payload["force_flat_reason"] == FORCE_FLAT_REASON
    assert all(
        float(entry["target_weight"]) == 0.0 for entry in payload["fills"]
    ), "the terminal row must flatten every leg"
    closed_gross = sum(abs(float(entry["prior_weight"])) for entry in payload["fills"])
    assert closed_gross == pytest.approx(0.60, rel=1e-12), (
        "the boundary closes the whole prior book"
    )

    # And at schedule level: the LAST row carries the frozen reason, empty book.
    injected_opening_row = {
        "action": "OPEN_REBALANCE",
        "decision_ns": _T0,
        "status": "OK",
        "weights": [["AAAUSDT", 0.30], ["BBBUSDT", -0.30]],
        "fills": [
            {"symbol": "AAAUSDT", "applied": True, "fill_open_ns": _T0,
             "fill_bar_close_ns": _T0 + DAY_NS, "price": 100.0,
             "target_weight": 0.30, "prior_weight": 0.0},
            {"symbol": "BBBUSDT", "applied": True, "fill_open_ns": _T0,
             "fill_bar_close_ns": _T0 + DAY_NS, "price": 200.0,
             "target_weight": -0.30, "prior_weight": 0.0},
        ],
    }
    schedule = runner.schedule(
        {"rows": [injected_opening_row], "final_boundary_ns": _T_END}
    )
    rows = schedule["rows"]
    assert rows[-1]["action"] == FORCE_FLAT_STATUS
    assert rows[-1]["reason_code"] == FORCE_FLAT_REASON
    assert rows[-1]["weights"] == []
    assert sum(abs(w) for _, w in rows[-1]["weights"]) == 0.0

    finalised = runner.finalise_schedule_payload(schedule)
    assert payload_sha256(schedule) == payload_sha256(
        runner.finalise_schedule_payload(schedule)
    ), "deterministic artifacts: identical schedule => identical payload hash"


# ========================================================================= #
# BG-4  full preregistered stress matrix
# ========================================================================= #
def test_bg4_stress_variant_matrix_must_be_complete():
    """BG-4: baseline + all five preregistered cells, expanded per member."""
    runner = _runner()
    cohort = sorted(_DUMMY_CONFIG["cohort"])
    fold_labels = ["F1", "F2", "F3"]

    variants = runner.stress_variants(cohort, fold_labels)
    assert isinstance(variants, list) and variants, "a variant plan is required"

    def _family(entry: Mapping[str, Any]) -> str:
        value = entry.get("family", entry.get("id"))
        token = str(value)
        return token.split(":")[0]

    def _qualifier(entry: Mapping[str, Any]) -> str:
        value = entry.get("id", "")
        return str(value).split(":", 1)[1] if ":" in str(value) else ""

    families: Dict[str, List[Mapping[str, Any]]] = {}
    for entry in variants:
        assert "stress" in entry, (
            f"planned variant {entry.get('id', entry)!r} must carry its stress object"
        )
        families.setdefault(_family(entry), []).append(entry)

    # Exactly the preregistered surface: baseline + the frozen five cells.
    allowed_families = {"baseline", *STRESS_MATRIX_V10}
    assert set(families) == allowed_families, (
        f"stress surface drifted: {sorted(set(families) ^ allowed_families)}"
    )
    assert len(families["baseline"]) == 1
    assert len(families["fee_slippage_x1_5"]) == 1
    assert len(families["plus_2_ticks"]) == 1
    assert len(families["plus_1_event_delay"]) == 1

    # drop_one_symbol: ONE cell per cohort symbol, and the stress object really
    # removes exactly that symbol through the frozen primitive.
    symbol_cells = families["drop_one_symbol"]
    assert sorted(_qualifier(entry) for entry in symbol_cells) == cohort
    for entry in symbol_cells:
        dropped = _qualifier(entry)
        stress = _stress_of(entry)
        assert list(stress["drop_symbols"]) == [dropped]
        assert apply_stress_filter(cohort, StressParams(drop_symbols=(dropped,))) == [
            symbol for symbol in cohort if symbol != dropped
        ]

    # drop_one_fold: ONE cell per fold, and the fold index is really dropped.
    fold_cells = families["drop_one_fold"]
    assert sorted(_qualifier(entry) for entry in fold_cells) == fold_labels
    for entry in fold_cells:
        stress = _stress_of(entry)
        assert stress["dropped_fold_index"] == fold_labels.index(_qualifier(entry))

    # Parameter values are the frozen floors/offsets, never looser.
    assert _stress_of(families["fee_slippage_x1_5"][0])["fee_multiplier"] == pytest.approx(1.5)
    assert _stress_of(families["plus_2_ticks"][0])["tick_slip_ticks"] == \
        ADVERSE_TICK_SLIP_FLOOR + 2
    assert _stress_of(families["plus_1_event_delay"][0])["event_delay_events"] == 1
    baseline_stress = _stress_of(families["baseline"][0])
    assert baseline_stress["fee_multiplier"] == pytest.approx(1.0)
    assert baseline_stress["tick_slip_ticks"] == ADVERSE_TICK_SLIP_FLOOR
    assert baseline_stress["event_delay_events"] == 0


def _stress_of(entry: Mapping[str, Any]) -> Mapping[str, Any]:
    """Read the effective stress parameters off a planned variant entry."""
    stress = entry["stress"]
    if hasattr(stress, "fee_multiplier"):
        return {
            "fee_multiplier": float(stress.fee_multiplier),
            "tick_slip_ticks": int(stress.tick_slip_ticks),
            "event_delay_events": int(stress.event_delay_events),
            "drop_symbols": list(stress.drop_symbols),
            "dropped_fold_index": stress.dropped_fold_index,
        }
    return {
        "fee_multiplier": float(stress["fee_multiplier"]),
        "tick_slip_ticks": int(stress["tick_slip_ticks"]),
        "event_delay_events": int(stress["event_delay_events"]),
        "drop_symbols": list(stress.get("drop_symbols", ())),
        "dropped_fold_index": stress.get("dropped_fold_index"),
    }


def test_bg4_finalization_refuses_any_missing_variant():
    """Refuse-finalize-if-any-required-variant-missing (mirror of H08-18)."""
    runner = _runner()
    cohort = sorted(_DUMMY_CONFIG["cohort"])
    fold_labels = ["F1", "F2", "F3"]
    required = [str(entry.get("id", entry)) for entry in
                runner.stress_variants(cohort, fold_labels)]

    complete = {vid: {"schema_version": "orca.adapter.v10.result.v1",
                      "variant_id": vid,
                      "schedule_sha256": "0" * 64,
                      "metrics": {}} for vid in required}
    assert runner.finalize_stress(complete, required)["finalized"] is True

    victim = required[-1]
    incomplete = {k: v for k, v in complete.items() if k != victim}
    with pytest.raises(Exception) as excinfo:
        runner.finalize_stress(incomplete, required)
    assert victim in str(excinfo.value), "the missing variant must be named"

    # No undeclared cell may be smuggled into the matrix.
    extra = dict(complete)
    extra["invented_day_mean_cell"] = dict(complete[required[0]],
                                           variant_id="invented_day_mean_cell")
    with pytest.raises(Exception):
        runner.finalize_stress(extra, required)


# ========================================================================= #
# BG-5  flat hard benchmark + context-only BTC-neutral / buy-and-hold
# ========================================================================= #
def test_bg5_flat_hard_benchmark_zero_series_exact():
    """BG-5: the hard gate is an all-zero series of the RIGHT length."""
    runner = _runner()
    n_days = 7
    flat = runner.flat_hard_benchmark(n_days=n_days)

    assert len(flat["daily_unit_gross_return"]) == n_days
    assert list(flat["daily_unit_gross_return"]) == [0.0] * n_days
    assert flat["total_return"] == 0.0
    assert flat["expectancy"] == 0.0
    assert flat["profit_factor_is_undefined"] is True, "PF of 0/0 is flagged, not faked"
    assert flat["benchmark"] == "flat_hard"
    assert flat["role"] == "hard_gate"


def test_bg5_btc_neutral_context_matches_gross_one_exposure_identity():
    """BG-5: neutral_ret[i] = pnl[i]/gross[i] - btc[i]*net[i]/gross[i]."""
    runner = _runner()
    pnl = [100.0, -50.0, 200.0, -100.0]
    gross = [200.0] * 4
    net = [0.0, 0.0, 200.0, 200.0]
    btc = [0.01, -0.02, 0.01, -0.02]

    context = runner.context_benchmark(
        kind="btc_beta_neutral", daily_pnl=pnl, daily_gross_exposure=gross,
        daily_net_exposure=net, benchmark_daily_return=btc,
    )
    neutral = list(context["daily_unit_gross_return"])
    assert neutral[0] == pytest.approx(0.5, abs=1e-15)
    assert neutral[1] == pytest.approx(-0.25, abs=1e-15)
    assert neutral[2] == pytest.approx(0.99, rel=1e-12)
    assert neutral[3] == pytest.approx(-0.48, rel=1e-12)

    # Gross-exposure accounting consistency, exact to 1e-12:
    lhs = sum(n * g for n, g in zip(neutral, gross))
    rhs = sum(pnl) - sum(b * w for b, w in zip(btc, net))
    assert lhs == pytest.approx(rhs, rel=1e-12)

    # Context benchmarks are context-only by contract: never scored, never gates.
    assert context["role"] == "context_only"
    buy_hold = runner.context_benchmark(
        kind="buy_and_hold", daily_pnl=pnl, daily_gross_exposure=gross,
        daily_net_exposure=net, benchmark_daily_return=btc,
    )
    assert list(buy_hold["daily_unit_gross_return"]) == pytest.approx(btc)


# ========================================================================= #
# BG-6  publish scored cell exactly once / denominator integrity
# ========================================================================= #
def test_bg6_ledger_idempotency_duplicate_publish_rejected(tmp_path):
    """BG-6: one trial identity contributes ONE row, ever."""
    runner = _runner()
    ledger_path = tmp_path / "ledger.jsonl"
    entry = {
        "experiment_id": "v10p_dummy_cell",
        "verdict": "PASS",
        "matrix_id": "v10p-dummy",
        "kind": "CELL_RESULT",
        "schema": "orca.v10.cell.v1",
        "score_sha256": "b" * 64,
    }

    first = runner.publish_trial(entry, ledger_path=ledger_path)
    assert first["published"] is True

    with pytest.raises(Exception) as excinfo:                # duplicate publish
        runner.publish_trial(dict(entry), ledger_path=ledger_path)
    assert "duplicate" in str(excinfo.value).lower()

    assert verify_append_only(ledger_path) is True
    denominator = runner.denominator(ledger_path=ledger_path)
    assert denominator == 1, "a rerun may never double-count the denominator"

    # Re-running the same publish path changes nothing at all.
    with pytest.raises(Exception):
        runner.publish_trial(dict(entry), ledger_path=ledger_path)
    assert runner.denominator(ledger_path=ledger_path) == 1


def test_bg6_publish_after_prescore_failure_is_forbidden(tmp_path):
    """BG-6: no publish on a failed/absent score, and never a partial row."""
    runner = _runner()
    ledger_path = tmp_path / "ledger.jsonl"

    with pytest.raises(Exception):
        runner.publish_trial(
            {"experiment_id": "v10p_failed_cell", "verdict": "PARTIAL_PRE_SCORE"},
            ledger_path=ledger_path,
        )
    assert not ledger_path.exists() or verify_append_only(ledger_path) is True


# ========================================================================= #
# G15  independent numeric funding reconciliation
# ========================================================================= #
_G15_T0 = parse_iso_utc_ns("2026-01-01T00:00:00Z")
_HOUR_NS = 3600 * 1_000_000_000


def _settlement(hour: int, rate: str) -> InfoPoint:
    return InfoPoint(_G15_T0 + hour * _HOUR_NS, float(Decimal(rate)))


def test_g15_checked_accrual_hand_computed_long_short_mixed():
    """G15: long pays positive rate, short receives it, mixed cadences."""
    holdings = [
        HoldingSpan("ETHUSDT", 0.50, _G15_T0, _G15_T0 + 24 * _HOUR_NS),   # long
        HoldingSpan("SOLUSDT", -0.25, _G15_T0, _G15_T0 + 24 * _HOUR_NS),  # short
        HoldingSpan("XRPUSDT", 0.10, _G15_T0 + 24 * _HOUR_NS,
                    _G15_T0 + 48 * _HOUR_NS),                            # later day
    ]
    settlements = (
        [_settlement(h, "0.0001") for h in (8, 16)]                 # ETH 8h cadence
        + [_settlement(h, "0.00002") for h in range(1, 25)          # SOL 1h cadence
           if h not in (8, 16)]
        + [_settlement(30, "0.002"), _settlement(48, "0.0005")]     # XRP day 2
    )

    report = checked_funding_accrual(holdings, settlements)

    by_symbol: Dict[str, List[Mapping[str, Any]]] = {}
    for flow in report["cashflows"]:
        by_symbol.setdefault(str(flow["symbol"]), []).append(flow)

    eth_total = math.fsum(float(f["cashflow_per_unit_capital"]) for f in by_symbol["ETHUSDT"])
    sol_total = math.fsum(float(f["cashflow_per_unit_capital"]) for f in by_symbol["SOLUSDT"])
    xrp_total = math.fsum(float(f["cashflow_per_unit_capital"]) for f in by_symbol["XRPUSDT"])

    # ETH long 0.50 pays: 2 x (0.50 * 0.0001) = -0.0001 per unit capital.
    assert eth_total == pytest.approx(-0.0001, rel=1e-9)
    # SOL short -0.25 receives: 22 x (0.25 * 0.00002) = +0.00011.
    assert sol_total == pytest.approx(0.00011, rel=1e-9)
    # XRP long 0.10 pays: 0.10*0.002 + 0.10*0.0005 = -0.00025.
    assert xrp_total == pytest.approx(-0.00025, rel=1e-9)
    assert report["coverage"]["is_complete"] is True
    assert report["sign_convention"] == "LONG_PAYS_POSITIVE_RATE"


def test_g15_checked_accrual_marks_unavailable_span_fail_closed():
    """G15/H08-13: a held span with no settlement must be MARKED, not 0."""
    holdings = [HoldingSpan("SOLUSDT", -0.20, _G15_T0, _G15_T0 + 24 * _HOUR_NS)]
    settlements = [_settlement(48, "0.0003")]          # published after the span

    report = checked_funding_accrual(holdings, settlements, coverage_required=True)
    assert report["coverage"]["is_complete"] is False
    assert [entry["symbol"] for entry in report["coverage"]["unavailable_spans"]] == \
        ["SOLUSDT"]
    assert report["status"] == "UNAVAILABLE_FAIL_CLOSED"
    assert report["cashflows"] == [], "uncovered accrual must never be silently zeroed"


def test_g15_no_accrual_outside_the_holding_span_or_before_publish():
    """G15: (start, end] exclusivity; nothing before the settlement publish."""
    holdings = [HoldingSpan("XRPUSDT", 0.10, _G15_T0 + 24 * _HOUR_NS,
                            _G15_T0 + 48 * _HOUR_NS)]
    settlements = [
        _settlement(0, "0.001"),       # before the span opens
        _settlement(24, "0.002"),      # == span START: excluded
        _settlement(30, "0.002"),      # inside: accrues -0.0002
        _settlement(48, "0.0005"),     # == span END: accrues -0.00005
        _settlement(60, "0.004"),      # after close: excluded
    ]
    report = checked_funding_accrual(holdings, settlements)
    flows = report["cashflows"]
    observed = [(int(f["settle_ts_ns"]), float(f["cashflow_per_unit_capital"]))
                for f in flows]
    assert len(observed) == 2
    assert observed[0][0] == _G15_T0 + 30 * _HOUR_NS
    assert observed[0][1] == pytest.approx(-0.0002, rel=1e-12)
    assert observed[1][0] == _G15_T0 + 48 * _HOUR_NS
    assert observed[1][1] == pytest.approx(-0.00005, rel=1e-12)
    assert all(
        int(f["settle_ts_ns"]) > holdings[0].start_ns
        and int(f["settle_ts_ns"]) <= holdings[0].end_ns
        for f in flows
    )


# ========================================================================= #
# F2 / G-H06  cache decision gating
# ========================================================================= #
def _complete_cache_proof_payload() -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "artifact": "cache_decision_v10",
        "raw_reads_pair": {"cached": 2, "uncached": 18},
        "preregistered_budget_max_raw_reads": SharedCacheMergeGate.MAX_RAW_READS_FULL_STRESS,
        "parity_proof": True,
        "repro_all_match": True,
        "wall_time_cached_s": 1.0,
        "wall_time_uncached_s": 10.0,
    }


def test_f2_cache_decision_enabled_only_with_complete_proof_pair():
    """F2: enable=true ONLY with raw_reads_pair(cached<=uncached) + budget field."""
    decision = cache_decision(_complete_cache_proof_payload())
    assert decision["enabled"] is True
    assert decision["raw_reads_pair"]["cached"] <= decision["raw_reads_pair"]["uncached"]
    assert decision["preregistered_budget_max_raw_reads"] > 0

    # cached reads ABOVE uncached reads is not a cache win => must stay disabled.
    worse = _complete_cache_proof_payload()
    worse["raw_reads_pair"] = {"cached": 20, "uncached": 18}
    assert cache_decision(worse)["enabled"] is False

    # Missing preregistered budget field => disabled, never assumed.
    no_budget = _complete_cache_proof_payload()
    del no_budget["preregistered_budget_max_raw_reads"]
    assert cache_decision(no_budget)["enabled"] is False

    # Missing raw-read pair entirely => disabled.
    no_pair = _complete_cache_proof_payload()
    del no_pair["raw_reads_pair"]
    assert cache_decision(no_pair)["enabled"] is False

    # The real gate still refuses over-budget reads (module-level cross-check).
    over = SharedCacheMergeGate().evaluate(
        parity_proof=True, repro_all_match=True, raw_reads=18,
        wall_time_cached_s=1.0, wall_time_uncached_s=10.0, strict=True,
    )
    assert over["adopted"] is False


def test_f2_cache_absent_means_operate_disabled_by_default(monkeypatch):
    """F2: no decision artifact => cache OFF.  No env flag may silently turn it on."""
    monkeypatch.delenv("V10_CACHE_ENABLED", raising=False)
    monkeypatch.delenv("ORCA_V10_CACHE_ENABLED", raising=False)

    for absent in (None, {}, "", "/nonexistent/cache_decision_v10.json"):
        decision = cache_decision(absent)
        assert decision["enabled"] is False
        assert decision["mode"] in ("DISABLED_DECISION_ABSENT", "DISABLED")
        assert decision["reasons"], "the refusal must state its reason"

    # Even a truthy env override cannot enable the cache without a decision.
    monkeypatch.setenv("V10_CACHE_ENABLED", "1")
    assert cache_decision(None)["enabled"] is False


# ========================================================================= #
# G17  one authoritative resource cap
# ========================================================================= #
def _valid_cap_payload(owner_ceiling: int, measured_safe_cap: int) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "artifact": "resource_cap_report_v10",
        "owner_ceiling": owner_ceiling,
        "measured_safe_cap": measured_safe_cap,
        "measured_peak_worker_ram_gb": 1.0,
        "available_ram_gb": 8.0,
        "reserved_ram_gb": MIN_RESERVED_RAM_GB,
        "final_cap": min(owner_ceiling, measured_safe_cap),
    }


def test_g17_final_cap_is_min_owner_ceiling_measured_safe_cap():
    """G17: exactly one final_cap, computed as min(owner_ceiling, measured_safe)."""
    payload = _valid_cap_payload(owner_ceiling=1, measured_safe_cap=3)
    report = resource_cap_report(payload)
    assert report["final_cap"] == 1
    assert isinstance(report["final_cap"], int)
    validation = validate_resource_cap_report(payload)
    assert validation["is_valid"] is True

    # measured_safe_cap below the ceiling pulls the cap down.
    tight = _valid_cap_payload(owner_ceiling=4, measured_safe_cap=2)
    assert resource_cap_report(tight)["final_cap"] == 2


def test_g17_cap_report_red_when_final_exceeds_measured_safe_cap():
    """G17: artifact claiming final > measured_safe_cap must be REJECTED."""
    inflated = _valid_cap_payload(owner_ceiling=1, measured_safe_cap=0)
    inflated["final_cap"] = 1                     # formula cap is 0 => contradiction
    validation = validate_resource_cap_report(inflated)
    assert validation["is_valid"] is False
    assert any("measured_safe_cap" in reason for reason in validation["reasons"])

    with pytest.raises(Exception):
        resource_cap_report(inflated)

    # cap == 0 means NO local scored launch; it can never be overridden to 1.
    zero = _valid_cap_payload(owner_ceiling=1, measured_safe_cap=0)
    assert resource_cap_report(zero)["final_cap"] == 0


def test_g17_cap_report_rejects_missing_or_duplicate_inputs():
    """G17: both inputs present, exactly one final_cap, integer typed."""
    missing = _valid_cap_payload(1, 2)
    del missing["measured_safe_cap"]
    assert validate_resource_cap_report(missing)["is_valid"] is False

    duplicated = _valid_cap_payload(1, 2)
    duplicated["final_cap"] = [1, 1]              # two final_cap values => ambiguous
    assert validate_resource_cap_report(duplicated)["is_valid"] is False

    float_cap = _valid_cap_payload(1, 2)
    float_cap["final_cap"] = 1.0                  # cap must be an int, not a float
    assert validate_resource_cap_report(float_cap)["is_valid"] is False

    assert validate_resource_cap_report({})["is_valid"] is False


def test_adapter_interface_version_is_declared():
    """The adapter must declare its interface version (contract freezing)."""
    assert isinstance(ADAPTER_INTERFACE_VERSION, str) and ADAPTER_INTERFACE_VERSION
    assert STRESS_MATRIX_V10 == (
        "fee_slippage_x1_5",
        "plus_2_ticks",
        "plus_1_event_delay",
        "drop_one_symbol",
        "drop_one_fold",
    )
