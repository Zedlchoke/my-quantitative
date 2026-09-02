"""G1 adapter tests: SYNTHETIC data only, nothing scored (sprint V10P-R).

Coverage required by the lane brief:

* BG1 -- deterministic fold membership + stable output hashes (two builds);
* BG2 -- target book -> portfolio/fill/scoring payload conversion: signs,
  magnitudes and the 0.30 cap (breach refused, boundary accepted);
* BG4 -- the six named stress cells (baseline + the frozen five), one
  artifact per cell, unique result/shard/log roots;
* BG5 -- flat hard benchmark exactly zero plus context-only buy-and-hold and
  benchmark-excluded neutral outputs;
* BG6 -- exactly-once publication: first publish succeeds, a second publish
  with the same key is refused, a failed pre-score publishes nothing and the
  scored denominator never moves on a rerun;
* reuse -- the dummy strategy and the M01 thin plugin run the SAME
  parameterized adapter suite (plus exact-value dummy assertions and
  interface-contract assertions for the M01 plugin on tiny synthetic frames).

No catalog parquet is read, no scored window is touched, and no real PnL/PF of
M01 is inspected anywhere below.
"""

from __future__ import annotations

import json
import math
import tempfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from research.adapter_v10.benchmarks import (
    build_benchmark_block,
    flat_benchmark,
)
from research.adapter_v10.converters import (
    build_portfolio_payload,
    fill_payload_row,
    normalise_target_book,
    summarise_books,
)
from research.adapter_v10.dummy_strategy import DummyDeterministicStrategy
from research.adapter_v10.hashes import payload_sha256
from research.adapter_v10.m01_plugin import M01Plugin
from research.adapter_v10.metrics import (
    PF_NO_POSITIONS_NOTE,
    aggregate_portfolio,
    daily_expectancy,
    max_drawdown,
    position_profit_factor,
)
from research.adapter_v10.protocol import (
    DEFAULT_WEIGHT_CAP_MAX,
    AdapterError,
    ContractViolation,
    DataUnavailable,
    FillRecord,
    FillStatusVocabulary,
    FoldSpec,
    ImmutableSchedule,
    PositionSpan,
    SettlementPoint,
    StrategyIdentity,
    StressSpec,
)
from research.adapter_v10.publish import (
    PUBLISHED_CELL_KIND,
    evaluate_pre_score_gate,
    publish_trial,
    trial_denominator,
    trial_key,
)
from research.adapter_v10.runner import run_full_stress_matrix, run_strategy
from research.adapter_v10.stress import (
    BASELINE_NAME,
    STRESS_SURFACE_VARIANTS,
    assert_unique_roots,
    build_stress_spec,
    stress_matrix_cells,
)
from research.contract_v10 import STRESS_MATRIX_V10
from research.global_ledger import digest, snapshot
from research.pit_hooks_v10 import DataIntegrityError
import research.hyp_a8_m01 as m01_module
from research.hyp_a8_m01 import M01Bar

DAY_NS = 86_400_000_000_000
STEP_NS = 15 * 60 * 1_000_000_000
CLOSE_SHAVE_NS = 100_000


def utc_ns(*args: int) -> int:
    stamp = datetime(*args, tzinfo=timezone.utc)
    return int(stamp.timestamp()) * 1_000_000_000


JAN = lambda d, h=0: utc_ns(2025, 1, d, h)  # noqa: E731

DUMMY_INSTANTS = [JAN(2), JAN(3), JAN(4), JAN(5), JAN(6), JAN(7)]
DUMMY_SYMBOLS = tuple(f"SYM{i:02d}" for i in range(10))
#: distinct drifts so price moves do NOT cancel across a dollar-neutral book
DUMMY_DRIFTS = {sym: 0.001 * ((index % 5) - 2) for index, sym in enumerate(DUMMY_SYMBOLS)}
DUMMY_RATES = (0.0, 0.0001, -0.0002, 0.00005)


def make_dummy(**overrides) -> DummyDeterministicStrategy:
    kwargs = dict(
        symbols=DUMMY_SYMBOLS,
        instants_ns=DUMMY_INSTANTS,
        n_select=4,
        daily_drift_by_symbol=DUMMY_DRIFTS,
        settle_rate_by_day_index=DUMMY_RATES,
        excluded_benchmark_symbol="BENCH00",
        window_start_iso="2025-01-01T00:00:00Z",
        window_end_iso="2025-01-08T00:00:00Z",
        fold_count=2,
        purge_days=1,
    )
    kwargs.update(overrides)
    return DummyDeterministicStrategy(**kwargs)


# --------------------------------------------------------------------------- #
# M01 synthetic bar fixture (96 completed 15m bars per UTC day)
# --------------------------------------------------------------------------- #
M01_BASE_NS = utc_ns(2025, 9, 1)
M01_WINDOW_START = "2025-09-01T00:00:00Z"
M01_WINDOW_END = "2025-09-10T00:00:00Z"
M01_SYMBOLS = tuple(f"SYM{i}USDT" for i in range(10))
M01_CONTEXT_ONLY = ("BTCUSDT",)


def m01_day_bars(day_start_ns: int, *, flow_f: float, open_px: float) -> list[M01Bar]:
    bars: list[M01Bar] = []
    price = open_px
    for index in range(96):
        nxt = price * 1.0001
        ts_event = day_start_ns + (index + 1) * STEP_NS - CLOSE_SHAVE_NS
        qty = 1_000.0 / 96
        bars.append(
            M01Bar(
                ts_event_ns=ts_event,
                ts_init_ns=ts_event,
                open=price,
                high=max(price, nxt) * 1.001,
                low=min(price, nxt) * 0.999,
                close=nxt,
                volume=qty,
                quote_volume=qty * price,
                count=10 + index % 3,
                taker_buy_quote_volume=flow_f * qty * price,
            )
        )
        price = nxt
    return bars


def make_m01_bars(days: int = 10) -> dict[str, tuple[M01Bar, ...]]:
    bars: dict[str, tuple[M01Bar, ...]] = {}
    symbols = [*M01_SYMBOLS, *M01_CONTEXT_ONLY]
    for index, symbol in enumerate(symbols):
        sequence: list[M01Bar] = []
        for day in range(days):
            flow = 0.5 + 0.02 * ((index + day) % 5)
            price = 100.0 + 5.0 * index
            sequence.extend(
                m01_day_bars(M01_BASE_NS + day * DAY_NS, flow_f=flow, open_px=price)
            )
        bars[symbol] = tuple(sequence)
    return bars


def make_m01_plugin(**overrides) -> M01Plugin:
    bars = overrides.pop("bars_by_symbol", None) or make_m01_bars()
    kwargs = dict(
        bars_by_symbol=bars,
        window_start_iso=M01_WINDOW_START,
        window_end_iso=M01_WINDOW_END,
        tick_sizes={sym: 0.01 for sym in bars},
        context_only_symbols=M01_CONTEXT_ONLY,
        settle_points_by_symbol={
            sym: [
                SettlementPoint(
                    publish_ts_ns=M01_BASE_NS + day * DAY_NS + 8 * 3600 * 1_000_000_000,
                    value=0.0001 * ((day % 3) - 1),
                )
                for day in range(1, 10)
            ]
            for sym in bars
        },
    )
    kwargs.update(overrides)
    return M01Plugin(**kwargs)


STRATEGIES = {
    "dummy": make_dummy,
    "m01_plugin": make_m01_plugin,
}


# --------------------------------------------------------------------------- #
# BG1 -- deterministic folds + hash stability
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("factory", STRATEGIES.values(), ids=list(STRATEGIES))
def test_bg1_fold_membership_and_hash_stable_across_builds(factory, tmp_path):
    first = run_strategy(factory(), out_dir=tmp_path / "run1", write_artifact_file=True)
    second = run_strategy(factory(), out_dir=tmp_path / "run2", write_artifact_file=True)

    assert first["hashes"]["result_sha256"] == second["hashes"]["result_sha256"]
    assert first["fold_membership"] == second["fold_membership"]
    assert first["fold_attribution"] == second["fold_attribution"]

    # folds are chronological, non-overlapping and cover the schedule together
    instants = list(first["schedule"]["first_decision_ns"] and _instants_from(first))
    seen: list[int] = []
    for fold in sorted(first["folds"], key=lambda f: f["index"]):
        members = fold["instants"]
        assert members == sorted(members)
        assert not set(members) & set(seen)
        seen.extend(members)
    assert set(seen) <= set(instants)
    # every instant is attributed exactly once
    attributed = [i for members in first["fold_attribution"].values() for i in members]
    assert sorted(attributed) == sorted(instants)

    # artifacts on disk are identical bytes for both independent builds
    artifact_a = (tmp_path / "run1" / "results" / "artifact.json").read_text()
    artifact_b = (tmp_path / "run2" / "results" / "artifact.json").read_text()
    assert artifact_a == artifact_b


def _instants_from(result) -> list[int]:
    lo, hi = result["schedule"]["first_decision_ns"], result["schedule"]["last_decision_ns"]
    n = result["schedule"]["n_instants"]
    if n == 1:
        return [lo]
    step = (hi - lo) // (n - 1)
    schedule = [lo + index * step for index in range(n)]
    assert len(schedule) == n
    return schedule


def test_bg1_fold_metrics_are_after_cost_and_funding():
    rows = [
        (0.0, 0.0, 0.0005),   # establishment cost only
        (0.001, 0.0002, 0.0),  # price + funding
        (-0.002, -0.0001, 0.0),
    ]
    nets = [p + f - c for p, f, c in rows]
    assert max_drawdown(nets) == pytest.approx(0.0021, abs=1e-12)
    assert daily_expectancy(nets) == pytest.approx(sum(nets) / 3, abs=1e-15)
    pf, reason = position_profit_factor([0.5, -0.25, 0.25, 0.0])
    assert reason == ""
    assert pf == pytest.approx(0.75 / 0.25, abs=1e-12)
    pf_none, note = position_profit_factor([0.5, 0.5])
    assert pf_none is None and note == "no_losing_positions"
    pf_empty, note_empty = position_profit_factor([])
    assert pf_empty is None and note_empty == PF_NO_POSITIONS_NOTE
    portfolio = aggregate_portfolio(daily_rows=[], positions=[])
    assert portfolio["n_days_with_records"] == 0
    assert portfolio["position_pf"] is None


# --------------------------------------------------------------------------- #
# BG2 -- target book conversion
# --------------------------------------------------------------------------- #
def test_bg2_conversion_signs_magnitudes_and_cap():
    book = normalise_target_book(
        {"weights": [["AAA", 0.3], ["BBB", -0.2], ["CCC", 0.1]]}, decision_ns=11
    )
    assert [sym for sym, _ in book.longs] == ["AAA", "CCC"]
    assert [sym for sym, _ in book.shorts] == ["BBB"]
    assert book.diagnostics["gross_realised"] == pytest.approx(0.6, abs=1e-12)
    assert book.diagnostics["max_abs_weight"] == pytest.approx(0.3, abs=1e-12)
    assert book.diagnostics["cap_max"] == pytest.approx(DEFAULT_WEIGHT_CAP_MAX, abs=1e-12)

    mapping_form = normalise_target_book({"AAA": 0.05, "BBB": -0.05}, decision_ns=12)
    assert mapping_form.as_mapping() == {"AAA": 0.05, "BBB": -0.05}

    with pytest.raises(ContractViolation) as breach:
        normalise_target_book({"AAA": 0.31}, decision_ns=13)
    assert "cap breach" in str(breach.value)

    exact_cap = normalise_target_book({"AAA": DEFAULT_WEIGHT_CAP_MAX}, decision_ns=14)
    assert exact_cap.longs == (("AAA", 0.3),)

    with pytest.raises(ContractViolation):
        normalise_target_book([["AAA", 0.1], ["AAA", 0.2]], decision_ns=15)
    with pytest.raises(ContractViolation):
        normalise_target_book({"AAA": float("nan")}, decision_ns=16)


def test_bg2_fill_and_portfolio_payload_round_trip():
    fills = (
        FillRecord(
            symbol="AAA",
            decision_ns=21,
            status=FillStatusVocabulary.APPLIED,
            applied=True,
            price=100.0,
            fill_open_ns=21 + 900_000_000_000,
            fill_bar_close_ns=21 + 2 * 900_000_000_000,
            event_offset=0,
        ),
        FillRecord(symbol="ZZZ", decision_ns=21),
    )
    row = fill_payload_row(
        decision_ns=21,
        action="OPEN_REBALANCE",
        book=None,
        fills=fills,
        prior_weights={"AAA": 0.1, "ZZZ": -0.1},
        new_weights={"AAA": 0.3, "ZZZ": 0.0},
        cost_charged=0.002,
        carry_forward=False,
    )
    assert row["turnover_one_side"] == pytest.approx(0.3, abs=1e-12)
    assert row["longs"] == [["AAA", 0.3]]
    assert row["shorts"] == []
    assert row["fills"][0]["signed_weight_change"] == pytest.approx(0.2, abs=1e-12)
    assert row["fills"][1]["signed_weight_change"] == pytest.approx(0.1, abs=1e-12)
    assert row["fills"][1]["applied"] is False

    payload = build_portfolio_payload([row], stress=StressSpec(name=BASELINE_NAME))
    assert payload["n_boundaries"] == 1
    assert payload["summary"]["total_turnover_one_side"] == pytest.approx(0.3, abs=1e-12)
    assert payload["summary"]["total_cost_charged"] == pytest.approx(0.002, abs=1e-12)
    assert payload["summary"]["force_flat_present"] is False
    assert summarise_books([]) == {"n_books": 0}


def test_bg2_adapter_rejects_over_cap_book_from_strategy():
    strategy = make_dummy()
    original = strategy.targets_at

    def over_cap(instant_ns, *, universe, stress):
        book = original(instant_ns, universe=universe, stress=stress)
        weights = [[sym, weight] for sym, weight in book["weights"]]
        weights[0] = [weights[0][0], 0.31]
        return {**book, "weights": weights}

    strategy.targets_at = over_cap  # type: ignore[method-assign]
    with pytest.raises(AdapterError):
        run_strategy(strategy, write_artifact_file=False)


# --------------------------------------------------------------------------- #
# BG4 -- stress matrix
# --------------------------------------------------------------------------- #
def test_bg4_stress_matrix_cells_and_unique_roots():
    baseline = StressSpec(name=BASELINE_NAME, tick_slip_ticks=1)
    cells = stress_matrix_cells(
        strategy_baseline=baseline, droppable_symbols=("AAA", "BBB")
    )
    assert [cell.name for cell in cells] == [BASELINE_NAME, *STRESS_MATRIX_V10]
    assert len(cells) == 6
    assert assert_unique_roots(cells) == {
        "unique_result_roots": 6,
        "unique_shard_roots": 6,
        "unique_log_roots": 6,
        "n_cells": 6,
    }
    by_name = {cell.name: cell for cell in cells}
    assert by_name["fee_slippage_x1_5"].spec.fee_multiplier == pytest.approx(1.5, abs=1e-12)
    assert by_name["plus_2_ticks"].spec.tick_slip_ticks == 3
    assert by_name["plus_1_event_delay"].spec.event_delay_events == 1
    assert by_name["drop_one_symbol"].spec.drop_symbols == ("AAA",)
    assert by_name["drop_one_fold"].spec.dropped_fold_index == 0
    assert by_name[BASELINE_NAME].spec.is_baseline

    with pytest.raises(ContractViolation):
        build_stress_spec("not_a_cell", strategy_baseline=baseline, droppable_symbols=("AAA",))
    with pytest.raises(ContractViolation):
        build_stress_spec(
            "drop_one_symbol", strategy_baseline=baseline, droppable_symbols=()
        )


@pytest.mark.parametrize("factory", STRATEGIES.values(), ids=list(STRATEGIES))
def test_bg4_full_matrix_runs_all_six_cells_with_own_artifacts(factory, tmp_path):
    matrix = run_full_stress_matrix(factory(), out_root=tmp_path / "matrix")
    assert matrix["matrix_cells"] == [BASELINE_NAME, *STRESS_MATRIX_V10]
    assert matrix["uniqueness"]["n_cells"] == 6
    roots = [run["artifact_paths"]["result_root"] for run in matrix["runs"].values()]
    shards = [run["artifact_paths"]["shard_root"] for run in matrix["runs"].values()]
    logs = [run["artifact_paths"]["log_root"] for run in matrix["runs"].values()]
    artifacts = [run["artifact_paths"]["artifact_path"] for run in matrix["runs"].values()]
    assert len(set(roots)) == len(set(shards)) == len(set(logs)) == len(set(artifacts)) == 6
    for name, run in matrix["runs"].items():
        path = Path(run["artifact_paths"]["artifact_path"])
        assert path.is_file(), name
        payload = json.loads(path.read_text())
        assert payload["stress"]["name"] == name
        assert payload["hashes"]["result_sha256"] == run["hashes"]["result_sha256"]
    # the whole matrix digest is stable across an independent rebuild
    rebuilt = run_full_stress_matrix(factory(), out_root=tmp_path / "matrix2")
    assert rebuilt["matrix_digest"] == matrix["matrix_digest"]
    # drop_one_fold really drops a fold from the scored table
    dropped = matrix["runs"]["drop_one_fold"]
    assert sum(1 for fold in dropped["folds"] if fold["dropped"]) == 1
    assert all(fold["included_in_metrics"] for fold in dropped["fold_metrics"])


# --------------------------------------------------------------------------- #
# BG5 -- flat hard benchmark + context outputs
# --------------------------------------------------------------------------- #
def test_bg5_flat_benchmark_is_exactly_zero_and_context_only():
    instants = [JAN(2), JAN(3), JAN(4)]
    flat = flat_benchmark(instants=instants)
    assert flat["cumulative_return"] == 0.0
    assert flat["max_drawdown"] == 0.0
    assert flat["enters_denominator"] is False
    assert flat["role"] == "hard_gate"
    assert all(value == 0.0 for value in flat["net_return_per_unit"])
    with pytest.raises(AdapterError):
        flat_benchmark(instants=[JAN(2)])


@pytest.mark.parametrize("factory", STRATEGIES.values(), ids=list(STRATEGIES))
def test_bg5_context_outputs_excluded_leg_never_tradeable(factory):
    result = run_strategy(factory(), write_artifact_file=False)
    benchmarks = result["benchmarks"]
    excluded = set(result["benchmark_symbols_excluded"])
    if excluded:
        # an excluded leg never becomes a tradeable universe member
        assert not excluded & set(result["universe"])
        # and it is absent from the neutral context book
        assert not excluded & set(benchmarks["excluded_neutral"]["weights"])
        assert benchmarks["excluded_neutral"]["role"] == "context_only"
    assert benchmarks["flat_hard"]["cumulative_return"] == 0.0
    assert benchmarks["buy_and_hold"]["enters_denominator"] is False
    assert benchmarks["excluded_neutral"]["enters_denominator"] is False
    assert result["scored"] is False

    # context outputs respond to marks (rising marks -> positive hold return)
    def rising(syms, ts):
        day = (ts - JAN(2)) // DAY_NS
        return {
            sym: 100.0 + 10.0 * index + 5.0 * day for index, sym in enumerate(syms)
        }

    block = build_benchmark_block(
        identity=_identity_from(result),
        context_symbols=["AAA", "BBB"],
        instants=[JAN(2), JAN(3)],
        marks_at=rising,
    )
    assert block["buy_and_hold"]["cumulative_gross_return"] > 0.0
    assert block["excluded_neutral"]["cumulative_gross_return"] > 0.0


def _identity_from(result) -> StrategyIdentity:
    payload = result["identity"]
    return StrategyIdentity(
        strategy_id=payload["strategy_id"],
        family_id=payload["family_id"],
        arm_config_id=payload["arm_config_id"],
        direction=payload["direction"],
        window_start_iso=payload["window_start_iso"],
        window_end_iso=payload["window_end_iso"],
        benchmark_symbols_excluded=tuple(payload["benchmark_symbols_excluded"]),
        funding_sign_convention=payload["funding_sign_convention"],
        config=payload["config"],
    )


# --------------------------------------------------------------------------- #
# BG6 -- exactly-once publication
# --------------------------------------------------------------------------- #
SCORED_METRICS = {
    "score_valid": True,
    "net_return_sum": 0.0123,
    "expectancy_per_day": 0.0004,
    "max_drawdown": 0.0031,
}


def _publish_kwargs(tmp_path, ledger_name="ledger.jsonl", matrix_id="v8x_dummy_cell"):
    strategy = make_dummy()
    return dict(
        identity=strategy.identity(),
        stress_signature=StressSpec(name=BASELINE_NAME).signature(),
        scored_metrics=dict(SCORED_METRICS),
        payload_digests={"result_sha256": "a" * 64},
        experiment_digest="b" * 64,
        matrix_id=matrix_id,
        ledger_path=str(tmp_path / ledger_name),
    )


def test_bg6_publish_once_then_idempotent_then_denominator_stable(tmp_path):
    kwargs = _publish_kwargs(tmp_path)
    before = trial_denominator(kwargs["ledger_path"])

    first = publish_trial(**kwargs)
    assert first["published"] is True
    assert first["stage"] == "PUBLISHED"
    assert first["denominator_delta"] == 1
    assert trial_denominator(kwargs["ledger_path"]) == before + 1

    # the same key again: refused, nothing appended, denominator unchanged
    second = publish_trial(**kwargs)
    assert second["published"] is False
    assert second["stage"] == "IDEMPOTENT_REPLAY_SKIPPED"
    assert second["existing_experiment_id"] == first["experiment_id"]
    assert trial_denominator(kwargs["ledger_path"]) == before + 1

    state = snapshot(kwargs["ledger_path"])
    assert state["count"] == before + 1
    assert digest(state) == digest(snapshot(kwargs["ledger_path"])["rows"])
    row = state["rows"][-1]
    assert row["kind"] == PUBLISHED_CELL_KIND
    assert row["trial_key_sha256"] == trial_key(_payload_for(kwargs))
    assert row["experiment_id"] == f"{kwargs['matrix_id']}-{row['trial_key_sha256'][:16]}"


def _payload_for(kwargs) -> dict:
    from research.adapter_v10.publish import canonical_scored_payload

    return canonical_scored_payload(
        identity=kwargs["identity"], stress_signature=kwargs["stress_signature"]
    )


def test_bg6_prescore_failure_blocks_every_publish(tmp_path):
    kwargs = _publish_kwargs(tmp_path, ledger_name="blocked.jsonl")
    blocked_metrics = {**SCORED_METRICS, "score_valid": False}
    result = publish_trial(**{**kwargs, "scored_metrics": blocked_metrics})
    assert result["published"] is False
    assert result["stage"] == "PRE_SCORE_GATE_BLOCKED"
    assert result["pre_score_passed"] is False
    assert result["pre_score_reasons"] == ["pre_score_flag_false"]
    assert not (tmp_path / "blocked.jsonl").exists()
    assert trial_denominator(kwargs["ledger_path"]) == 0

    missing = {k: v for k, v in SCORED_METRICS.items() if k != "expectancy_per_day"}
    gate_ok, reasons = evaluate_pre_score_gate(missing)
    assert gate_ok is False
    assert "pre_score_field_absent:expectancy_per_day" in reasons
    ok, empty = evaluate_pre_score_gate(SCORED_METRICS)
    assert ok is True and empty == []


def test_bg6_rerun_never_double_counts_the_denominator(tmp_path):
    kwargs = _publish_kwargs(tmp_path, ledger_name="rerun.jsonl")
    publish_trial(**kwargs)
    denominator_after_first = trial_denominator(kwargs["ledger_path"])
    for _ in range(3):
        replay = publish_trial(**kwargs)
        assert replay["published"] is False
    assert trial_denominator(kwargs["ledger_path"]) == denominator_after_first

    # a different stress cell is a different key -> a new denominator entry
    other = publish_trial(
        **{
            **kwargs,
            "stress_signature": StressSpec(name="plus_2_ticks", tick_slip_ticks=3).signature(),
        }
    )
    assert other["published"] is True
    assert trial_denominator(kwargs["ledger_path"]) == denominator_after_first + 1


def test_bg6_refuses_to_append_to_a_violated_ledger(tmp_path):
    kwargs = _publish_kwargs(tmp_path, ledger_name="violated.jsonl")
    path = tmp_path / "violated.jsonl"
    path.write_text(
        json.dumps({"experiment_id": "x", "verdict": "y", "appended_at": "2025-01-01T00:00:00Z"})
        + "\n"
        + json.dumps({"experiment_id": "y", "verdict": "z", "appended_at": "2024-01-01T00:00:00Z"})
        + "\n",
        encoding="utf-8",
    )
    result = publish_trial(**kwargs)
    assert result["published"] is False
    assert result["stage"] == "LEDGER_APPEND_REFUSED"
    assert trial_denominator(kwargs["ledger_path"]) == 0


# --------------------------------------------------------------------------- #
# Reuse proof -- dummy end-to-end with exact values
# --------------------------------------------------------------------------- #
def test_dummy_end_to_end_exact_values(tmp_path):
    strategy = make_dummy()
    result = run_strategy(strategy, out_dir=tmp_path / "dummy")
    stress = result["stress"]
    assert stress["name"] == BASELINE_NAME
    assert stress["tick_slip_ticks"] == 1 and stress["fee_multiplier"] == 1.0

    universe = list(strategy.tradeable_universe())
    # book at instant 0: rotation starts at index 0 -> first 4 sorted symbols
    first_book = result["books"][0]
    chosen = universe[:4]
    assert [sym for sym, _ in first_book["weights"]] == sorted(chosen)
    assert first_book["longs"] == [
        [sorted(chosen)[0], 0.25],
        [sorted(chosen)[1], 0.25],
    ]
    assert first_book["shorts"] == [
        [sorted(chosen)[2], -0.25],
        [sorted(chosen)[3], -0.25],
    ]
    # rotation: instant 1 starts at universe[1]
    second_book = result["books"][1]
    assert [sym for sym, _ in second_book["weights"]] == sorted(universe[1:5])

    # fills land exactly one synthetic bar after the decision instant
    fill = result["portfolio_payload"]["rows"][0]["fills"][0]
    assert fill["status"] == FillStatusVocabulary.APPLIED
    assert fill["fill_open_ns"] == DUMMY_INSTANTS[0] + 900_000_000_000
    assert fill["price"] == strategy.mark_price(fill["symbol"], DUMMY_INSTANTS[0] + 900_000_000_000)

    # force-flat closes the book at the final instant
    assert result["portfolio_payload"]["summary"]["force_flat_present"] is True
    assert result["portfolio_payload"]["rows"][-1]["weights"] == {}
    assert result["portfolio_payload"]["rows"][-1]["action"] == "FORCE_FLAT"

    # schedule + folds: 6 instants, 2 folds, one purge gap, one force-flat edge
    assert result["schedule"]["n_instants"] == 6
    assert result["purge_gap_instants"] == [DUMMY_INSTANTS[2], DUMMY_INSTANTS[5]]
    assert [f["label"] for f in result["folds"]] == ["F1", "F2"]

    # entry cost of the first book: per-leg |dw| * (5bp fee + 1 tick of slippage)
    # at the deterministic fill price of each leg, one side of 1.0 traded
    entry_book = dict(first_book["weights"])
    expected_first_cost = round(
        math.fsum(
            abs(weight)
            * (5e-4 + 1 * 0.01 / strategy.mark_price(sym, DUMMY_INSTANTS[0] + 900_000_000_000))
            for sym, weight in entry_book.items()
        ),
        12,
    )
    assert result["daily_returns"][0]["cost_charged_per_unit"] == pytest.approx(
        expected_first_cost, abs=1e-12
    )
    # every boundary after the first carries no entry cost unless the book changed
    assert result["daily_returns"][1]["cost_charged_per_unit"] > 0.0

    # funding accrues on held legs: long pays a positive rate (negative cashflow)
    held = [p for p in result["positions"] if p["funding_cashflow_per_unit"] != 0.0]
    assert held, "expected at least one funding accrual"
    for position in held:
        expected = -position["signed_weight"] * _rate_for(position["entry_ns"])
        assert position["funding_cashflow_per_unit"] == pytest.approx(expected, abs=1e-12)

    assert result["portfolio_metrics"]["n_positions"] == len(result["positions"])
    assert result["fold_metrics"][0]["n_days_with_records"] == 3
    assert result["hashes"]["portfolio_payload_sha256"] == payload_sha256(
        result["portfolio_payload"]
    )
    assert Path(result["artifacts"]["artifact"]).is_file()


def _rate_for(entry_ns: int) -> float:
    index = (entry_ns - DUMMY_INSTANTS[0]) // DAY_NS
    return DUMMY_RATES[int(index) % len(DUMMY_RATES)]


def test_dummy_rejects_random_or_misconfigured_inputs():
    with pytest.raises(AdapterError):
        make_dummy(instants_ns=[JAN(2), JAN(2), JAN(3)])
    with pytest.raises(AdapterError):
        make_dummy(symbols=("A", "A", "B"))
    with pytest.raises(AdapterError):
        make_dummy(n_select=99)
    schedule = make_dummy().schedule()
    assert isinstance(schedule, ImmutableSchedule)
    with pytest.raises(AdapterError):
        ImmutableSchedule(instants=(1, 1, 2), source="dup")


# --------------------------------------------------------------------------- #
# Reuse proof -- same suite for both plugins
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("factory", STRATEGIES.values(), ids=list(STRATEGIES))
def test_common_adapter_invariants_for_every_strategy(factory, tmp_path):
    strategy = factory()
    result = run_strategy(strategy, write_artifact_file=False)
    identity = strategy.identity()

    assert result["producer_role"] == "G1"
    assert result["scored"] is False
    assert result["identity"]["family_id"] == identity.family_id
    assert result["universe"] == sorted(strategy.tradeable_universe())
    assert result["schedule"]["n_instants"] == len(strategy.schedule().instants)
    # every applied fill bar CLOSES strictly after its decision instant
    for row in result["portfolio_payload"]["rows"]:
        for fill in row["fills"]:
            if fill["applied"]:
                assert fill["fill_bar_close_ns"] > fill["decision_ns"]
                assert fill["fill_open_ns"] >= fill["decision_ns"] - 900_000_000_000
                assert fill["price"] > 0.0
    # the final boundary is always the force-flat edge with an empty book
    assert result["portfolio_payload"]["rows"][-1]["action"] == "FORCE_FLAT"
    assert result["portfolio_payload"]["rows"][-1]["weights"] == {}
    # books respect the cap and stay unit-gross when not carried
    for book in result["books"]:
        assert book["diagnostics"]["max_abs_weight"] <= DEFAULT_WEIGHT_CAP_MAX + 1e-9
        if not book["carried_forward"]:
            assert book["diagnostics"]["gross_realised"] == pytest.approx(
                strategy.identity().config.get("gross", 1.0), abs=1e-9
            )
    # realized ledger reconciles with the fold table
    total_positions = sum(fold["n_positions"] for fold in result["fold_metrics"])
    assert total_positions == len(result["positions"])
    assert result["portfolio_metrics"]["net_return_sum"] == pytest.approx(
        sum(row["net_return_per_unit"] for row in result["daily_returns"]), abs=1e-12
    )


# --------------------------------------------------------------------------- #
# M01 plugin interface contracts (synthetic frames only)
# --------------------------------------------------------------------------- #
def test_m01_plugin_interface_contracts_on_synthetic_frames():
    bars = make_m01_bars(days=3)
    plugin = make_m01_plugin(bars_by_symbol=bars)
    stress = plugin.baseline_stress()

    identity = plugin.identity()
    assert identity.benchmark_symbols_excluded == M01_CONTEXT_ONLY
    assert identity.funding_sign_convention == "LONG_PAYS_POSITIVE_RATE"
    assert list(plugin.tradeable_universe()) == sorted(M01_SYMBOLS)
    assert list(plugin.benchmark_context_symbols()) == sorted(
        [*M01_SYMBOLS, *M01_CONTEXT_ONLY]
    )

    # schedule provider: immutable, exactly the UTC midnights of the window
    schedule = plugin.schedule()
    expected_days = [
        M01_BASE_NS + day * DAY_NS for day in range(1, 10)
    ]
    assert list(schedule.instants) == expected_days
    assert schedule.sha256 == plugin.schedule().sha256
    with pytest.raises(AttributeError):  # frozen dataclass -> immutable schedule
        schedule.instants = ()

    # targets: M01 books come back through the generic normaliser unchanged
    universe = plugin.universe(stress)
    raw = plugin.targets_at(schedule.instants[0], universe=universe, stress=stress)
    assert raw["status"] == "OK"
    assert raw["n_eligible"] >= 8
    weights = {sym: weight for sym, weight in raw["weights"]}
    assert max(abs(w) for w in weights.values()) <= 0.30 + 1e-12
    assert math.isclose(sum(abs(w) for w in weights.values()), 1.0, abs_tol=1e-9)

    # fills: strict-later event clock at the bar covering the boundary
    fills = plugin.fills_at(
        schedule.instants[0], symbols=universe[:3], stress=stress
    )
    assert all(fill.applied for fill in fills)
    assert all(fill.event_offset == 0 for fill in fills)
    for fill in fills:
        covering = [
            bar
            for bar in plugin._bars[fill.symbol]
            if bar.ts_event_ns - STEP_NS <= fill.decision_ns < bar.ts_event_ns
        ]
        assert covering and covering[0].open == fill.price

    delayed = plugin.fills_at(
        schedule.instants[0],
        symbols=universe[:3],
        stress=StressSpec(name="plus_1_event_delay", event_delay_events=1),
    )
    assert all(fill.event_offset == 1 for fill in delayed)

    # costs delegate to the frozen primitive: identical arithmetic
    prices = {sym: 100.0 for sym in universe[:2]}
    cost = plugin.rebalance_cost_between(
        {}, {universe[0]: 0.5, universe[1]: -0.5}, prices=prices, stress=stress
    )
    expected = 1.0 * (5.0 * 1e-4 + 1 * 0.01 / 100.0)
    assert cost == pytest.approx(expected, abs=1e-12)
    fee_cell = build_stress_spec(
        "fee_slippage_x1_5", strategy_baseline=stress, droppable_symbols=universe
    )
    stressed = plugin.rebalance_cost_between(
        {},
        {universe[0]: 0.5, universe[1]: -0.5},
        prices=prices,
        stress=fee_cell,
    )
    assert stressed == pytest.approx(1.0 * (7.5e-4 + 1 * 0.01 / 100.0), abs=1e-12)
    # a stress spec built without the strategy floor carries no tick slippage
    bare = plugin.rebalance_cost_between(
        {},
        {universe[0]: 0.5, universe[1]: -0.5},
        prices=prices,
        stress=StressSpec(name="fee_slippage_x1_5", fee_multiplier=1.5),
    )
    assert bare == pytest.approx(1.0 * 7.5e-4, abs=1e-12)

    # funding: long pays positive rate over the exact held span
    spans = [
        PositionSpan(symbol=universe[0], signed_weight=0.25, start_ns=expected_days[0], end_ns=expected_days[1]),
    ]
    flows = plugin.funding_cashflows_for_spans(spans)
    assert flows, "expected accrual inside the held span"
    for flow in flows:
        assert flow["sign_convention"] == "LONG_PAYS_POSITIVE_RATE"
        assert flow["cashflow_per_unit_capital"] == pytest.approx(
            -0.25 * flow["rate"], abs=1e-15
        )
        assert expected_days[0] < flow["publish_ts_ns"] <= expected_days[1]

    # drop-one-symbol stress filters the cohort and fails closed on junk
    assert list(plugin.universe(
        StressSpec(name="drop_one_symbol", drop_symbols=(M01_SYMBOLS[0],))
    )) == sorted(M01_SYMBOLS[1:])
    with pytest.raises(AdapterError):
        plugin.universe(StressSpec(name="drop_one_symbol", drop_symbols=("NOPE",)))

    # folds come from the frozen primitive with purge >= holding horizon
    folds = plugin.folds(stress=stress, instants=list(schedule.instants))
    assert [fold.label for fold in folds] == ["F1", "F2", "F3"]
    assert all(fold.purge_days == 1 for fold in folds)
    dropped = plugin.folds(
        stress=StressSpec(name="drop_one_fold", dropped_fold_index=0),
        instants=list(schedule.instants),
    )
    assert [fold.dropped for fold in dropped] == [True, False, False]

    # marks resolve through the covering bar and return None when absent
    marks = plugin.marks_at([universe[0]], expected_days[0])
    assert marks[universe[0]] == plugin._covering_bar(universe[0], expected_days[0]).open
    inside_second_bar = expected_days[0] + STEP_NS + 1
    assert (
        plugin.marks_at([universe[0]], inside_second_bar)[universe[0]]
        == plugin._covering_bar(universe[0], inside_second_bar).open
    )
    assert plugin.marks_at([universe[0]], expected_days[0] + 40 * DAY_NS) == {
        universe[0]: None
    }


def test_m01_plugin_benchmark_exclusion_is_enforced():
    plugin = make_m01_plugin()
    result = run_strategy(plugin, write_artifact_file=False)
    assert result["benchmark_symbols_excluded"] == ["BTCUSDT"]
    assert "BTCUSDT" not in result["universe"]
    assert result["identity"]["family_id"] == plugin.identity().family_id
    with pytest.raises(AdapterError):
        # a benchmark leg can never be a tradeable member
        run_strategy(make_m01_plugin(context_only_symbols=()), write_artifact_file=False)


# --------------------------------------------------------------------------- #
# Genericity guard
# --------------------------------------------------------------------------- #
GENERIC_MODULES = [
    "research/adapter_v10/__init__.py",
    "research/adapter_v10/base.py",
    "research/adapter_v10/benchmarks.py",
    "research/adapter_v10/converters.py",
    "research/adapter_v10/hashes.py",
    "research/adapter_v10/metrics.py",
    "research/adapter_v10/publish.py",
    "research/adapter_v10/runner.py",
    "research/adapter_v10/stress.py",
    "research/adapter_v10/protocol.py",
]


def test_generic_paths_free_of_family_tokens():
    banned = ("M01", "A8", "BTCUSDT", "a8_panel_family", "trial_v10")
    for relative in GENERIC_MODULES:
        text = Path(relative).read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{relative} hard-codes {token!r}"
        assert "hyp_a8_m01" not in text, f"{relative} imports a family module"


# --------------------------------------------------------------------------- #
# Fail-closed paths (missing marks, duplicated/out-of-span settlements)
# --------------------------------------------------------------------------- #
def test_missing_valuation_marks_fail_closed():
    strategy = make_dummy()
    strategy.marks_at = lambda syms, ts: {sym: None for sym in syms}  # type: ignore[method-assign]
    with pytest.raises(DataUnavailable):
        run_strategy(strategy, write_artifact_file=False)


def test_settlements_fail_closed_or_silent_outside_held_spans():
    plugin = make_m01_plugin()
    edge = utc_ns(2025, 9, 1)
    duplicated = tuple(
        SettlementPoint(publish_ts_ns=edge + 8 * 3600 * 1_000_000_000, value=0.0001)
        for _ in range(2)
    )
    plugin._settlements = {sym: duplicated for sym in plugin._bars}
    # the shared PIT hook refuses duplicate settlement stamps (fail closed)
    with pytest.raises((AdapterError, DataIntegrityError)):
        run_strategy(plugin, write_artifact_file=False)

    far_past = make_m01_plugin()
    far_past._settlements = {
        sym: (SettlementPoint(publish_ts_ns=edge - 10 * DAY_NS, value=0.5),)
        for sym in far_past._bars
    }
    result = run_strategy(far_past, write_artifact_file=False)
    assert math.fsum(p["funding_cashflow_per_unit"] for p in result["positions"]) == 0.0


# --------------------------------------------------------------------------- #
# Frozen QA-contract facade (A1 interface reconciliation, commit 2)
# --------------------------------------------------------------------------- #
from research.adapter_v10 import (  # noqa: E402
    ADAPTER_INTERFACE_VERSION,
    GenericRunnerV10,
    cache_decision,
    checked_funding_accrual,
    resource_cap_report,
    validate_resource_cap_report,
)
from research.hyp_a8_m01 import (  # noqa: E402
    ADVERSE_TICK_SLIP_FLOOR,
    FORCE_FLAT_REASON as M01_FORCE_FLAT_REASON,
    FORCE_FLAT_STATUS as M01_FORCE_FLAT_STATUS,
    HoldingSpan,
    StressParams,
)
from research.pit_hooks_v10 import InfoPoint  # noqa: E402
from research.cache_v10 import SharedCacheMergeGate  # noqa: E402


class _FacadeDummyStrategy:
    """Smallest generic plugin for the facade (strategy_id/config/schedule_provider)."""

    strategy_id = "DUMMY_FACADE_V10"

    def __init__(self) -> None:
        self.config = dict(FACADE_CONFIG)
        self.schedule_provider = "injected_fixture_rows"


FACADE_CONFIG: dict = {
    "cohort": ["AAAUSDT", "BBBUSDT"],
    "window_start_iso": "2025-09-01T00:00:00Z",
    "window_end_iso": "2025-09-03T00:00:00Z",
    "cap": 0.30,
    "gross": 1.0,
    "taker_fee_bps": 5.0,
    "adverse_tick_slip": 1,
}


def _facade_runner() -> GenericRunnerV10:
    return GenericRunnerV10(strategy=_FacadeDummyStrategy(), config=FACADE_CONFIG)


FACADE_FOLD_RETURNS = {"F1": [0.01, 0.02, -0.01], "F2": [-0.02, 0.04]}


def _facade_oracle(returns):
    wins = math.fsum(r for r in returns if r > 0.0)
    losses = math.fsum(r for r in returns if r <= 0.0)
    equity, peak, mdd = 1.0, 1.0, 0.0
    for value in returns:
        equity *= 1.0 + float(value)
        peak = max(peak, equity)
        mdd = max(mdd, 1.0 - equity / peak)
    return {
        "expectancy": math.fsum(returns) / len(returns),
        "profit_factor": wins / abs(losses),
        "max_drawdown": mdd,
    }


def test_facade_fold_metrics_match_hand_computed_values_and_pool():
    metrics = _facade_runner().compute_fold_metrics(dict(FACADE_FOLD_RETURNS))
    entries = {entry["fold_id"]: entry for entry in metrics["folds"]}
    assert [entry["fold_id"] for entry in metrics["folds"]] == ["F1", "F2"]

    assert entries["F1"]["n_days"] == 3
    assert entries["F1"]["expectancy"] == pytest.approx(
        float(Decimal("0.02") / Decimal(3)), rel=1e-12
    )
    assert entries["F1"]["profit_factor"] == pytest.approx(3.0, rel=1e-12)
    assert entries["F1"]["max_drawdown"] == pytest.approx(0.01, rel=1e-6)

    assert entries["F2"]["n_days"] == 2
    assert entries["F2"]["expectancy"] == pytest.approx(0.01, rel=1e-12)
    assert entries["F2"]["profit_factor"] == pytest.approx(2.0, rel=1e-12)
    assert entries["F2"]["max_drawdown"] == pytest.approx(0.02, rel=1e-6)

    pooled = _facade_oracle(FACADE_FOLD_RETURNS["F1"] + FACADE_FOLD_RETURNS["F2"])
    aggregate = metrics["aggregate"]
    assert aggregate["expectancy"] == pytest.approx(pooled["expectancy"], rel=1e-12)
    assert aggregate["profit_factor"] == pytest.approx(
        float(Decimal("0.07") / Decimal("0.03")), rel=1e-12
    )
    assert aggregate["max_drawdown"] == pytest.approx(pooled["max_drawdown"], rel=1e-9)

    twice = _facade_runner().compute_fold_metrics(dict(FACADE_FOLD_RETURNS))
    assert payload_sha256(metrics) == payload_sha256(twice)

    # a fold with no losing day is flagged undefined, never faked as a number
    undefined = _facade_runner().compute_fold_metrics({"F1": [0.01, 0.02]})
    assert undefined["folds"][0]["profit_factor"] is None
    assert undefined["folds"][0]["profit_factor_is_undefined"] is True
    with pytest.raises(AdapterError):
        _facade_runner().compute_fold_metrics({})
    with pytest.raises(AdapterError):
        GenericRunnerV10(strategy=object(), config=FACADE_CONFIG)


def test_facade_convert_target_book_exact_cost_and_vocabulary():
    runner = _facade_runner()
    prices = {"AAAUSDT": 100.0, "BBBUSDT": 200.0}
    ticks = {"AAAUSDT": 0.01, "BBBUSDT": 0.01}
    t0 = utc_ns(2025, 9, 2)
    events = {
        symbol: m01_module.resolve_fill_event(
            _facade_bars(symbol, t0), symbol, decision_ns=t0
        )
        for symbol in prices
    }

    payload = runner.convert_target_book(
        t0, {"AAAUSDT": 0.30, "BBBUSDT": -0.30}, {}, events, tick_sizes=ticks
    )
    assert {"decision_ns", "fills", "turnover_one_side", "cost_per_unit_gross",
            "is_force_flat_boundary"} <= set(payload)
    assert payload["decision_ns"] == t0
    assert payload["is_force_flat_boundary"] is False
    fills = {entry["symbol"]: entry for entry in payload["fills"]}
    assert set(fills) == set(prices)
    for symbol, weight in {"AAAUSDT": 0.30, "BBBUSDT": -0.30}.items():
        entry = fills[symbol]
        assert entry["status"] == "FILLED_NEXT_EVENT"
        assert entry["applied"] is True
        assert entry["event_offset"] == 0
        assert entry["target_weight"] == pytest.approx(weight, abs=1e-12)
        assert entry["prior_weight"] == 0.0
        assert entry["signed_weight_change"] == pytest.approx(weight, abs=1e-12)
        assert entry["price"] == pytest.approx(prices[symbol], rel=1e-12)
        assert entry["fill_open_ns"] <= t0 < entry["fill_bar_close_ns"]
    assert payload["turnover_one_side"] == pytest.approx(0.60, abs=1e-12)
    assert payload["cost_per_unit_gross"] == pytest.approx(
        float(Decimal("0.000345")), rel=1e-12
    )
    stressed = runner.convert_target_book(
        t0,
        {"AAAUSDT": 0.30, "BBBUSDT": -0.30},
        {},
        events,
        tick_sizes=ticks,
        stress=StressParams(fee_multiplier=1.5),
    )
    assert stressed["cost_per_unit_gross"] == pytest.approx(
        float(Decimal("0.000495")), rel=1e-12
    )
    # the stress signature is also readable as a plain mapping
    as_mapping = runner.convert_target_book(
        t0,
        {"AAAUSDT": 0.30, "BBBUSDT": -0.30},
        {},
        events,
        tick_sizes=ticks,
        stress={"fee_multiplier": 1.5, "tick_slip_ticks": 1},
    )
    assert as_mapping["cost_per_unit_gross"] == pytest.approx(
        float(Decimal("0.000495")), rel=1e-12
    )
    # a leg that cannot fill is never silently scored
    with pytest.raises(AdapterError):
        runner.convert_target_book(t0, {"AAAUSDT": 0.30}, {}, {}, tick_sizes=ticks)


def _facade_bars(symbol: str, decision_ns: int):
    price = {"AAAUSDT": 100.0, "BBBUSDT": 200.0}[symbol]
    return [
        M01Bar(
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


def test_facade_force_flat_and_schedule_terminal_row():
    runner = _facade_runner()
    prices = {"AAAUSDT": 100.0, "BBBUSDT": 200.0}
    ticks = {"AAAUSDT": 0.01, "BBBUSDT": 0.01}
    t0 = utc_ns(2025, 9, 2)
    t_end = t0 + DAY_NS
    events = {
        symbol: m01_module.resolve_fill_event(
            _facade_bars(symbol, t_end), symbol, decision_ns=t_end
        )
        for symbol in prices
    }
    payload = runner.convert_target_book(
        t_end,
        {"AAAUSDT": 0.30, "BBBUSDT": -0.30},
        {"AAAUSDT": 0.30, "BBBUSDT": -0.30},
        events,
        tick_sizes=ticks,
        force_flat_boundary_ns=t_end,
    )
    assert payload["is_force_flat_boundary"] is True
    assert payload["force_flat_reason"] == "force_flat_final_scored_window_boundary"
    assert all(float(entry["target_weight"]) == 0.0 for entry in payload["fills"])
    assert sum(abs(float(entry["prior_weight"])) for entry in payload["fills"]) == pytest.approx(0.60, abs=1e-12)

    opening_row = {
        "action": "OPEN_REBALANCE",
        "decision_ns": t0,
        "status": "OK",
        "weights": [["AAAUSDT", 0.30], ["BBBUSDT", -0.30]],
        "fills": [
            {"symbol": "AAAUSDT", "applied": True, "fill_open_ns": t0,
             "fill_bar_close_ns": t0 + DAY_NS, "price": 100.0,
             "target_weight": 0.30, "prior_weight": 0.0},
        ],
    }
    schedule = runner.schedule({"rows": [opening_row], "final_boundary_ns": t_end})
    rows = schedule["rows"]
    assert rows[-1]["action"] == M01_FORCE_FLAT_STATUS
    assert rows[-1]["reason_code"] == M01_FORCE_FLAT_REASON
    assert rows[-1]["weights"] == []
    assert sum(abs(weight) for _, weight in rows[-1]["weights"]) == 0.0
    finalised = runner.finalise_schedule_payload(schedule)
    assert payload_sha256(schedule) == payload_sha256(finalised)
    json.dumps(finalised)  # artifact payload is JSON-safe without any key added
    assert set(finalised) == set(schedule)
    # the mirrored terminal vocabulary never drifts from the frozen module
    assert M01_FORCE_FLAT_STATUS == "FORCE_FLAT"
    assert M01_FORCE_FLAT_REASON == "force_flat_final_scored_window_boundary"


def test_facade_stress_variants_and_finalize():
    runner = _facade_runner()
    cohort = sorted(FACADE_CONFIG["cohort"])
    fold_labels = ["F1", "F2", "F3"]
    variants = runner.stress_variants(cohort, fold_labels)

    def family(entry):
        return str(entry.get("family", entry.get("id"))).split(":")[0]

    def qualifier(entry):
        return str(entry.get("id", "")).split(":", 1)[1] if ":" in str(entry.get("id", "")) else ""

    grouped: dict = {}
    for entry in variants:
        assert "stress" in entry
        grouped.setdefault(family(entry), []).append(entry)
    assert set(grouped) == {"baseline", *STRESS_SURFACE_VARIANTS}
    assert len(grouped["baseline"]) == 1
    assert len(grouped["fee_slippage_x1_5"]) == 1
    assert len(grouped["plus_2_ticks"]) == 1
    assert len(grouped["plus_1_event_delay"]) == 1
    assert sorted(qualifier(entry) for entry in grouped["drop_one_symbol"]) == cohort
    for entry in grouped["drop_one_symbol"]:
        assert list(entry["stress"]["drop_symbols"]) == [qualifier(entry)]
    assert sorted(qualifier(entry) for entry in grouped["drop_one_fold"]) == fold_labels
    for entry in grouped["drop_one_fold"]:
        assert entry["stress"]["dropped_fold_index"] == fold_labels.index(qualifier(entry))

    def params(stress):
        return {
            "fee_multiplier": float(stress["fee_multiplier"]),
            "tick_slip_ticks": int(stress["tick_slip_ticks"]),
            "event_delay_events": int(stress["event_delay_events"]),
        }

    assert params(grouped["fee_slippage_x1_5"][0]["stress"])["fee_multiplier"] == pytest.approx(1.5)
    assert params(grouped["plus_2_ticks"][0]["stress"])["tick_slip_ticks"] == ADVERSE_TICK_SLIP_FLOOR + 2
    assert params(grouped["plus_1_event_delay"][0]["stress"])["event_delay_events"] == 1
    baseline = grouped["baseline"][0]["stress"]
    assert baseline["fee_multiplier"] == pytest.approx(1.0)
    assert baseline["tick_slip_ticks"] == ADVERSE_TICK_SLIP_FLOOR
    assert baseline["event_delay_events"] == 0

    required = [entry["id"] for entry in variants]
    complete = {
        vid: {"schema_version": "orca.adapter.v10.result.v1", "variant_id": vid,
              "schedule_sha256": "0" * 64, "metrics": {}}
        for vid in required
    }
    assert runner.finalize_stress(complete, required) == {
        "finalized": True,
        "n_variants": len(required),
        "variant_ids": required,
        "payload_sha256": runner.finalize_stress(complete, required)["payload_sha256"],
    }
    victim = required[-1]
    with pytest.raises(AdapterError) as missing:
        runner.finalize_stress({k: v for k, v in complete.items() if k != victim}, required)
    assert victim in str(missing.value)
    extra = dict(complete)
    extra["invented_cell"] = dict(complete[required[0]], variant_id="invented_cell")
    with pytest.raises(AdapterError):
        runner.finalize_stress(extra, required)


def test_facade_flat_and_context_benchmarks():
    runner = _facade_runner()
    flat = runner.flat_hard_benchmark(n_days=7)
    assert list(flat["daily_unit_gross_return"]) == [0.0] * 7
    assert flat["total_return"] == 0.0
    assert flat["expectancy"] == 0.0
    assert flat["profit_factor_is_undefined"] is True
    assert flat["benchmark"] == "flat_hard"
    assert flat["role"] == "hard_gate"
    with pytest.raises(AdapterError):
        runner.flat_hard_benchmark(n_days=0)

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
    assert sum(n * g for n, g in zip(neutral, gross)) == pytest.approx(
        sum(pnl) - sum(b * w for b, w in zip(btc, net)), rel=1e-12
    )
    assert context["role"] == "context_only"
    hold = runner.context_benchmark(
        kind="buy_and_hold", daily_pnl=pnl, daily_gross_exposure=gross,
        daily_net_exposure=net, benchmark_daily_return=btc,
    )
    assert list(hold["daily_unit_gross_return"]) == pytest.approx(btc)
    assert hold["role"] == "context_only"
    with pytest.raises(AdapterError):
        runner.context_benchmark(
            kind="unknown", daily_pnl=pnl, daily_gross_exposure=gross,
            daily_net_exposure=net, benchmark_daily_return=btc,
        )
    with pytest.raises(AdapterError):
        runner.context_benchmark(
            kind="btc_beta_neutral", daily_pnl=pnl, daily_gross_exposure=gross[:-1],
            daily_net_exposure=net, benchmark_daily_return=btc,
        )


def test_facade_publish_denominator_and_prescore_refusal(tmp_path):
    runner = _facade_runner()
    ledger = tmp_path / "facade_ledger.jsonl"
    entry = {
        "experiment_id": "v10p_dummy_cell",
        "verdict": "PASS",
        "matrix_id": "v10p-dummy",
        "kind": "CELL_RESULT",
        "schema": "orca.v10.cell.v1",
        "score_sha256": "b" * 64,
    }
    first = runner.publish_trial(entry, ledger_path=ledger)
    assert first["published"] is True
    with pytest.raises(AdapterError) as duplicate:
        runner.publish_trial(dict(entry), ledger_path=ledger)
    assert "duplicate" in str(duplicate.value).lower()
    from research.global_ledger import verify_append_only

    assert verify_append_only(ledger) is True
    assert runner.denominator(ledger_path=ledger) == 1
    with pytest.raises(AdapterError):
        runner.publish_trial(dict(entry), ledger_path=ledger)
    assert runner.denominator(ledger_path=ledger) == 1

    with pytest.raises(AdapterError):
        runner.publish_trial(
            {"experiment_id": "v10p_failed_cell", "verdict": "PARTIAL_PRE_SCORE"},
            ledger_path=ledger,
        )
    assert not ledger.exists() or verify_append_only(ledger) is True
    assert runner.denominator(ledger_path=ledger) == 1
    with pytest.raises(AdapterError):
        runner.publish_trial({"experiment_id": "x", "verdict": "PASS"}, ledger_path=ledger)


def test_facade_checked_funding_accrual_hand_computed(tmp_path=None):
    t0 = utc_ns(2026, 1, 1)
    hour = 3600 * 1_000_000_000

    def settle(hour_index: int, rate: str) -> InfoPoint:
        return InfoPoint(t0 + hour_index * hour, float(Decimal(rate)))

    holdings = [
        HoldingSpan("ETHUSDT", 0.50, t0, t0 + 24 * hour),
        HoldingSpan("SOLUSDT", -0.25, t0, t0 + 24 * hour),
        HoldingSpan("XRPUSDT", 0.10, t0 + 24 * hour, t0 + 48 * hour),
    ]
    per_symbol = {
        "ETHUSDT": [settle(h, "0.0001") for h in (8, 16)],
        "SOLUSDT": [settle(h, "0.00002") for h in range(1, 25) if h not in (8, 16)],
        "XRPUSDT": [settle(30, "0.002"), settle(48, "0.0005")],
    }
    report = checked_funding_accrual(holdings, per_symbol)
    assert report["coverage"]["series_mode"] == "per_symbol"
    by_symbol: dict = {}
    for flow in report["cashflows"]:
        by_symbol.setdefault(flow["symbol"], []).append(flow)
    eth = math.fsum(f["cashflow_per_unit_capital"] for f in by_symbol["ETHUSDT"])
    sol = math.fsum(f["cashflow_per_unit_capital"] for f in by_symbol["SOLUSDT"])
    xrp = math.fsum(f["cashflow_per_unit_capital"] for f in by_symbol["XRPUSDT"])
    assert eth == pytest.approx(-0.0001, rel=1e-9)
    assert sol == pytest.approx(0.00011, rel=1e-9)
    assert xrp == pytest.approx(-0.00025, rel=1e-9)
    assert report["coverage"]["is_complete"] is True
    assert report["sign_convention"] == "LONG_PAYS_POSITIVE_RATE"
    assert report["status"] == "OK"

    # points that carry their own symbol are attributed to that instrument only
    labelled_points = [
        {"symbol": sym, "publish_ts_ns": int(point.publish_ts_ns), "value": float(point.value)}
        for sym, series in per_symbol.items()
        for point in series
    ]
    labelled_report = checked_funding_accrual(holdings, labelled_points)
    assert labelled_report["coverage"]["series_mode"] == "per_symbol"
    assert math.fsum(f["cashflow_per_unit_capital"] for f in labelled_report["cashflows"]
                     if f["symbol"] == "ETHUSDT") == pytest.approx(-0.0001, rel=1e-9)
    assert math.fsum(f["cashflow_per_unit_capital"] for f in labelled_report["cashflows"]
                     if f["symbol"] == "SOLUSDT") == pytest.approx(0.00011, rel=1e-9)

    # an UNLABELLED flat series is SHARED by every held leg (never invented):
    # each instrument accrues on every instant it is held across.
    flat_series = [point for series in per_symbol.values() for point in series]
    shared = checked_funding_accrual(holdings, flat_series)
    assert shared["coverage"]["series_mode"] == "shared_flat_series"
    eth_shared = math.fsum(f["cashflow_per_unit_capital"] for f in shared["cashflows"]
                           if f["symbol"] == "ETHUSDT")
    sol_shared = math.fsum(f["cashflow_per_unit_capital"] for f in shared["cashflows"]
                           if f["symbol"] == "SOLUSDT")
    assert eth_shared == pytest.approx(-0.5 * (2 * 0.0001 + 22 * 0.00002), rel=1e-9)
    assert sol_shared == pytest.approx(0.25 * (2 * 0.0001 + 22 * 0.00002), rel=1e-9)

    uncovered = checked_funding_accrual(
        [HoldingSpan("SOLUSDT", -0.20, t0, t0 + 24 * hour)],
        [settle(48, "0.0003")],
        coverage_required=True,
    )
    assert uncovered["coverage"]["is_complete"] is False
    assert [entry["symbol"] for entry in uncovered["coverage"]["unavailable_spans"]] == ["SOLUSDT"]
    assert uncovered["status"] == "UNAVAILABLE_FAIL_CLOSED"
    assert uncovered["cashflows"] == []

    edges = checked_funding_accrual(
        [HoldingSpan("XRPUSDT", 0.10, t0 + 24 * hour, t0 + 48 * hour)],
        [
            settle(0, "0.001"),
            settle(24, "0.002"),
            settle(30, "0.002"),
            settle(48, "0.0005"),
            settle(60, "0.004"),
        ],
    )
    observed = [(int(f["settle_ts_ns"]), float(f["cashflow_per_unit_capital"]))
                for f in edges["cashflows"]]
    assert len(observed) == 2
    assert observed[0][0] == t0 + 30 * hour
    assert observed[0][1] == pytest.approx(-0.0002, rel=1e-12)
    assert observed[1][0] == t0 + 48 * hour
    assert observed[1][1] == pytest.approx(-0.00005, rel=1e-12)
    assert all(
        holdings_edge.start_ns < int(f["settle_ts_ns"]) <= holdings_edge.end_ns
        for f in edges["cashflows"]
        for holdings_edge in [HoldingSpan("XRPUSDT", 0.10, t0 + 24 * hour, t0 + 48 * hour)]
    )


def test_facade_cache_decision_gate():
    complete = {
        "schema_version": 1,
        "artifact": "cache_decision_v10",
        "raw_reads_pair": {"cached": 2, "uncached": 18},
        "preregistered_budget_max_raw_reads": SharedCacheMergeGate.MAX_RAW_READS_FULL_STRESS,
        "parity_proof": True,
        "repro_all_match": True,
        "wall_time_cached_s": 1.0,
        "wall_time_uncached_s": 10.0,
    }
    decision = cache_decision(complete)
    assert decision["enabled"] is True
    assert decision["raw_reads_pair"]["cached"] <= decision["raw_reads_pair"]["uncached"]
    assert decision["preregistered_budget_max_raw_reads"] > 0

    worse = dict(complete, raw_reads_pair={"cached": 20, "uncached": 18})
    assert cache_decision(worse)["enabled"] is False
    no_budget = dict(complete)
    del no_budget["preregistered_budget_max_raw_reads"]
    assert cache_decision(no_budget)["enabled"] is False
    no_pair = dict(complete)
    del no_pair["raw_reads_pair"]
    assert cache_decision(no_pair)["enabled"] is False
    for absent in (None, {}, "", "/nonexistent/cache_decision_v10.json"):
        decision = cache_decision(absent)
        assert decision["enabled"] is False
        assert decision["mode"] in ("DISABLED_DECISION_ABSENT", "DISABLED")
        assert decision["reasons"]
    # a written decision file is honoured through the same entry point
    payload_path = Path(tempfile.mkdtemp()) / "cache_decision_v10.json"
    payload_path.write_text(json.dumps(complete), encoding="utf-8")
    assert cache_decision(str(payload_path))["enabled"] is True


def test_facade_resource_cap_report_and_validator():
    def cap_payload(owner: int, measured: int) -> dict:
        return {
            "schema_version": 1,
            "artifact": "resource_cap_report_v10",
            "owner_ceiling": owner,
            "measured_safe_cap": measured,
            "measured_peak_worker_ram_gb": 1.0,
            "available_ram_gb": 8.0,
            "reserved_ram_gb": 2.0,
            "final_cap": min(owner, measured),
        }

    report = resource_cap_report(cap_payload(1, 3))
    assert report["final_cap"] == 1
    assert isinstance(report["final_cap"], int)
    assert validate_resource_cap_report(cap_payload(1, 3))["is_valid"] is True
    assert resource_cap_report(cap_payload(4, 2))["final_cap"] == 2
    zero = resource_cap_report(cap_payload(1, 0))
    assert zero["final_cap"] == 0
    assert zero["scored_launch_allowed"] is False

    inflated = cap_payload(1, 0)
    inflated["final_cap"] = 1
    validation = validate_resource_cap_report(inflated)
    assert validation["is_valid"] is False
    assert any("measured_safe_cap" in reason for reason in validation["reasons"])
    with pytest.raises(AdapterError):
        resource_cap_report(inflated)

    missing = cap_payload(1, 2)
    del missing["measured_safe_cap"]
    assert validate_resource_cap_report(missing)["is_valid"] is False
    duplicated = cap_payload(1, 2)
    duplicated["final_cap"] = [1, 1]
    assert validate_resource_cap_report(duplicated)["is_valid"] is False
    float_cap = cap_payload(1, 2)
    float_cap["final_cap"] = 1.0
    assert validate_resource_cap_report(float_cap)["is_valid"] is False
    assert validate_resource_cap_report({})["is_valid"] is False
    with pytest.raises(AdapterError):
        resource_cap_report(None)
    with pytest.raises(AdapterError):
        resource_cap_report("/nonexistent/resource_cap_report_v10.json")


def test_facade_interface_version_declared_and_mirrored_vocabulary():
    assert isinstance(ADAPTER_INTERFACE_VERSION, str) and ADAPTER_INTERFACE_VERSION
    assert ADAPTER_INTERFACE_VERSION == "v10.adapter.interface.v1"
    assert STRESS_SURFACE_VARIANTS == (
        "fee_slippage_x1_5",
        "plus_2_ticks",
        "plus_1_event_delay",
        "drop_one_symbol",
        "drop_one_fold",
    )
