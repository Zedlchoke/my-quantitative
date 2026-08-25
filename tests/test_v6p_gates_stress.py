"""V6P A5 negative/golden fixtures: measured XG1 + unconditional stresses.

PLAN section 6.4 repairs under test (owner A5):

* N07 -- the scored path supplies REAL execution-ledger rows assembled from
  ``execution['orders']`` + rank stamps into ``evaluate_xg1_measured``;
  hand-built booleans are gone from the scored path (legacy struct only
  survives flagged ``not_scored_usable``). Counters required for PASS:
  ``missing_ts_count == 0`` AND zero ``fill_ts <= signal_ts`` violations;
  missing inputs are INCONCLUSIVE, never PASS.
* N09 -- benchmark incompleteness emits ``benchmark_coverage_incomplete``;
  ``funding_coverage_insufficient`` is reserved for measured settlement
  shortfalls of TRADED symbols.
* N10 -- fee x1.5 / adverse-two-ticks / extra-one-event-delay /
  drop-one-symbol (every symbol) / drop-one-fold execute UNCONDITIONALLY
  (even when the base edge FAILs or on reverse controls), each measured
  with the family-aware metric set -- never expectancy_r. A negative base
  edge stays REJECTED: stress evidence is diagnostic-only.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from contracts.protocol import GateVerdict
from research.protocol.gates import (
    XGateId,
    count_execution_evidence,
    evaluate_xg1_measured,
    evaluate_xgates,
)
from research.protocol.gates import DataGateInput, GateInputs, evaluate_gates
import research.portfolio_runner as pr

WINDOW_START = "2026-01-01T00:00Z"
WINDOW_END = "2026-01-04T00:00Z"
LOCK_STAMP = "2026-01-05T00:00:00+00:00"

CANDIDATE_YAML = (
    "hypothesis_id: H-XSECT-MOM-v1\n"
    "family: cross_sectional_momentum\n"
    "candidate_version: 1\n"
    "owner_agent: A4\n"
    "universe:\n"
    "  traded_symbols: [SYMAUSDT, SYMBUSDT, SYMCUSDT, SYMDUSDT]\n"
    "  benchmark_symbol: BTCUSDT\n"
    "signal:\n"
    "  type: cumulative_log_return_rank\n"
    "  lookback_days: [3]\n"
)


def _ns(iso_text: str) -> int:
    text = iso_text.replace("Z", "+00:00")
    dt = datetime.fromisoformat(text).astimezone(timezone.utc)
    return int(dt.timestamp() * 1_000_000_000)


def _bars(day_isos, closes_by_symbol):
    # No bar ever sits exactly on a midnight cutoff stamp, so every fill
    # lands strictly AFTER its signal (measured XG1 can legitimately PASS).
    rows = []
    for day_iso in day_isos:
        for hhmm in ("00:15", "00:30"):
            ts = f"{day_iso}T{hhmm}:00Z"
            for sym, close in closes_by_symbol.items():
                rows.append({
                    "symbol": sym, "ts": ts,
                    "open": close, "high": close,
                    "low": close, "close": close, "volume": 1.0,
                })
    return rows


TRADED = ["SYMAUSDT", "SYMBUSDT", "SYMCUSDT", "SYMDUSDT"]


def _spec() -> dict:
    days = ["2026-01-01", "2026-01-02", "2026-01-03"]
    return {
        "traded_symbols": TRADED,
        "benchmark_symbol": "BTCUSDT",
        "initial_capital": 100000.0,
        "fee_taker": 0.0005,
        "slippage_ticks": 1,
        "tick_size": {"*": 0.01},
        "step_size": {"*": 0.001},
        "min_notional": 5.0,
        # Flat prices: equity moves ONLY through costs/funding -> the base
        # edge is NEGATIVE, which is exactly the N10 unconditional-stress
        # scenario (stresses must still execute; verdict stays REJECTED).
        # Two longs vs two shorts keeps the book dollar-neutral after ANY
        # single-symbol drop (drop-one must execute, not invariant-breach).
        "bars": _bars(days, {
            "SYMAUSDT": 100.0, "SYMBUSDT": 100.0, "SYMCUSDT": 100.0,
            "SYMDUSDT": 100.0, "BTCUSDT": 100.0,
        }),
        "funding": [
            {"symbol": "SYMAUSDT",
             "funding_time_ms": _ns("2026-01-02T08:00:00Z") // 1_000_000,
             "fundingRate": "0.0001"},
            {"symbol": "SYMBUSDT",
             "funding_time_ms": _ns("2026-01-02T08:00:00Z") // 1_000_000,
             "fundingRate": "0.0003"},
        ],
        "targets": {
            "longs": [["SYMAUSDT", 0.25], ["SYMBUSDT", 0.25]],
            "shorts": [["SYMCUSDT", -0.25], ["SYMDUSDT", -0.25]],
        },
    }


@pytest.fixture()
def workspace(tmp_path, monkeypatch):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "research_baseline_altcoin.yaml").write_text(
        "backtest:\n  fee_model: stub\n", encoding="utf-8")
    hyp = tmp_path / "research" / "hypotheses" / "H-XSECT-MOM-v1"
    hyp.mkdir(parents=True)
    (hyp / "candidate.yaml").write_text(
        CANDIDATE_YAML + f'locked_at_utc: "{LOCK_STAMP}"\n', encoding="utf-8")
    dc = tmp_path / "results" / "matrix" / "data_contract_v2"
    dc.mkdir(parents=True)
    (dc / "data_contract_v2.json").write_text('{"schema_version": 2}',
                                              encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _run_scored(workspace, experiment_id="V6P-A5-MEASURED") -> Path:
    spec_path = workspace / f"{experiment_id}-panel.json"
    spec_path.write_text(json.dumps(_spec()), encoding="utf-8")
    from research.portfolio_runner import main

    code = main([
        "--experiment-id", experiment_id,
        "--lookback-days", "3",
        "--window-start", WINDOW_START,
        "--window-end", WINDOW_END,
        "--folds", "3",
        "--matrix-id", "v6p_a5_gates",
        "--registry-path", "results/registry/experiments.jsonl",
        "--synthetic-panel", str(spec_path),
    ])
    assert code == 0
    return Path("results/portfolio_v4") / experiment_id


# ----------------------------- N09 reason split ------------------------------ #
def _xg0_coverage(btc_clean=True, btc_days=10):
    return {
        "required_days": 10,
        "traded_symbols": {
            "ETHUSDT": {"days_present": 10},
            "SOLUSDT": {"days_present": 10},
        },
        "benchmark": {
            "symbol": "BTCUSDT", "days_present": btc_days, "clean": btc_clean,
        },
    }


def test_benchmark_incompleteness_gets_its_own_reason_code():
    row = evaluate_xgates({"coverage": _xg0_coverage(btc_clean=False)})[0]
    assert row.gate == XGateId.XG0_DATA_UNIVERSE
    assert row.verdict is GateVerdict.FAIL
    assert "benchmark_coverage_incomplete" in row.reasons
    assert "funding_coverage_insufficient" not in row.reasons


def test_traded_symbol_funding_shortfall_keeps_funding_reason():
    # Measured settlement shortfall of a TRADED symbol (G0 coverage payload)
    # is the ONLY thing allowed to emit funding_coverage_insufficient.
    payload = {
        "symbols": {
            "ETHUSDT": {
                "bars": {"duplicate_timestamps": 0, "gaps_over_interval": 0},
                "instrument_metadata_present": True,
                "funding": {"bundle_present": False,
                            "covers_declared_window": True},
            },
        },
    }
    result = evaluate_gates(GateInputs(data=DataGateInput(
        coverage_payload=payload)))[0]
    assert result.verdict is GateVerdict.FAIL
    assert "funding_coverage_insufficient" in result.reasons


# ----------------------------- N07 measured XG1 ------------------------------ #
def _fake_execution(signal_stamps, orders):
    return {
        "signal_ranks": [
            {"signal_cutoff_ns": ts} for ts in signal_stamps
        ],
        "orders": orders,
    }


def test_assemble_xg1_rows_are_measured_from_orders_and_rank_stamps():
    s1, s2 = _ns("2026-01-02T00:00:00Z"), _ns("2026-01-03T00:00:00Z")
    execution = _fake_execution(
        [s1, s2],
        [
            {"symbol": "SYMAUSDT", "kind": "open", "ts": s1 + 900_000_000_000},
            {"symbol": "SYMBUSDT", "kind": "terminal_liquidate",
             "ts": s2 + 1800_000_000_000},
        ],
    )
    rows = pr.assemble_xg1_measured_rows(execution)
    assert [r["signal_ts"] for r in rows] == [s1, s2]
    assert all(r["fill_ts"] > r["signal_ts"] for r in rows)

    counters = count_execution_evidence(rows).to_dict()
    assert counters["missing_ts"] == 0
    assert counters["violations"] == 0
    result = evaluate_xg1_measured(
        rows, transform_registry={}, warmup_boundaries={
            "warmup_start": "w", "scored_start": "s", "scored_end": "e"})
    assert result.verdict is GateVerdict.PASS


def test_measured_xg1_fails_on_fill_not_after_signal():
    s1 = _ns("2026-01-02T00:00:00Z")
    rows = pr.assemble_xg1_measured_rows(_fake_execution(
        [s1], [{"symbol": "A", "kind": "open", "ts": s1}]))  # same-stamp fill
    counters = count_execution_evidence(rows).to_dict()
    assert counters["violations"] == 1 and counters["missing_ts"] == 0
    result = evaluate_xg1_measured(
        rows, transform_registry={}, warmup_boundaries={
            "warmup_start": "w", "scored_start": "s", "scored_end": "e"})
    assert result.verdict is GateVerdict.FAIL
    assert "signal_fill_ordering_violation" in result.reasons


def test_missing_timestamps_never_pass():
    s1 = _ns("2026-01-02T00:00:00Z")
    rows = pr.assemble_xg1_measured_rows(_fake_execution(
        [s1], [{"symbol": "A", "kind": "open"}]))  # no ts at all
    counters = count_execution_evidence(rows).to_dict()
    assert counters["missing_ts"] == 1
    result = evaluate_xg1_measured(
        rows, transform_registry={}, warmup_boundaries={
            "warmup_start": "w", "scored_start": "s", "scored_end": "e"})
    assert result.verdict is GateVerdict.INCONCLUSIVE
    assert "g1_evidence_missing" in result.reasons
    # Absent ledger entirely => evidence_missing, never PASS.
    empty = evaluate_xg1_measured(None)
    assert empty.verdict is GateVerdict.INCONCLUSIVE
    assert "evidence_missing" in empty.reasons


def test_scored_gate_inputs_carry_rows_not_booleans(workspace):
    exp_dir = _run_scored(workspace)
    execution = {
        "metrics": json.loads(
            (exp_dir / "canonical_metrics.json").read_text(encoding="utf-8")),
    }
    # Rebuild the runner-side assembly exactly as the scored path does.
    ranks = [json.loads(line) for line in
             (exp_dir / "signal_ranks.jsonl").read_text().splitlines()]
    orders = [json.loads(line) for line in
              (exp_dir / "orders.jsonl").read_text().splitlines()]
    rows = pr.assemble_xg1_measured_rows({
        "signal_ranks": ranks, "orders": orders})
    assert rows and all(r["signal_ts"] is not None for r in rows)

    gate_doc = json.loads(
        (exp_dir / "gate_result.json").read_text(encoding="utf-8"))
    by_id = {row["gate"]: row for row in gate_doc["gates"]}
    xg1 = by_id[XGateId.XG1_POINT_IN_TIME.value]
    assert xg1["verdict"] == GateVerdict.PASS.value
    counters = gate_doc["xg1_measured_counters"]
    assert counters["missing_ts"] == 0
    assert counters["violations"] == 0
    assert counters["entries"] == len(orders) > 0


def _shell_metrics() -> dict:
    return {
        "total_pnl": 1.0, "fold_pnls": {}, "fold_returns": {},
        "fold_exp_rs": {}, "pf_position_level": {"profit_factor": 1.5,
                                                 "pf_reason": None},
        "expectancy_r": None, "gross_max": 0.5, "net_abs_max": 0.0,
        "max_abs_target_weight": 0.25, "margin_breach_rows": 0,
        "top_symbol_share": 0.1, "beta": None, "max_drawdown_fraction": 0.01,
        "rebalances_scored": 30, "legs_closed": 100, "top_fold_share": 0.2,
    }


def test_legacy_boolean_struct_only_as_not_scored_usable():
    execution = _fake_execution([123], [{"symbol": "A", "ts": 456}])
    inputs = pr.build_gate_inputs(
        {**execution, "metrics": _shell_metrics()},
        declared_symbols=["A"], required_days=1,
        warmup_boundaries={"warmup_start": "w", "scored_start": "s",
                           "scored_end": "e"},
    )
    assert "pit_evidence" not in inputs  # deleted from the scored path
    assert inputs["execution_ledger_rows"]

    compat = pr.build_gate_inputs(
        {**execution, "metrics": _shell_metrics()},
        declared_symbols=["A"], required_days=1,
        warmup_boundaries={"warmup_start": "w", "scored_start": "s",
                           "scored_end": "e"},
        legacy_boolean_compat=True,
    )
    assert compat["pit_evidence"]["not_scored_usable"] is True


# -------------------- N10 unconditional family-aware stresses ---------------- #
def test_stresses_execute_and_report_despite_negative_base_edge(workspace):
    exp_dir = _run_scored(workspace)
    gate_doc = json.loads(
        (exp_dir / "gate_result.json").read_text(encoding="utf-8"))
    by_id = {row["gate"]: row for row in gate_doc["gates"]}
    base_xg3 = by_id[XGateId.XG3_STAGE_A_PORTFOLIO.value]
    assert base_xg3["verdict"] == GateVerdict.FAIL.value  # costs-only panel
    assert gate_doc["cell_verdict"] == "REJECTED"  # stress cannot rescue

    report = json.loads(
        (exp_dir / "stress_report.json").read_text(encoding="utf-8"))
    assert report["executed_unconditionally"] is True
    assert report["base_edge_verdict"] == GateVerdict.FAIL.value
    assert set(report["metric_set"]) == {
        "canonical_pnl", "profit_factor", "funding_pnl", "fold_returns",
        "mdd_continuous", "max_gross_exposure"}

    baseline = report["baseline"]
    assert baseline["canonical_pnl"] < 0
    for key in pr.STRESS_METRIC_KEYS:
        assert key in baseline, key

    variants = report["variants"]
    expected_families = (
        "fee_x1_5", "adverse_two_ticks", "extra_one_event_delay",
        *(f"drop_one_symbol:{sym}" for sym in TRADED),
        "drop_one_fold:F1", "drop_one_fold:F2", "drop_one_fold:F3",
    )
    for name in expected_families:
        assert name in variants, name
    for name, entry in variants.items():
        assert entry.get("executed") is True, name
        for key in pr.STRESS_METRIC_KEYS:
            assert key in entry, (name, key)

    # Cost stresses really bite: stricter costs => strictly worse PnL.
    assert variants["fee_x1_5"]["canonical_pnl"] < baseline["canonical_pnl"]
    assert (variants["adverse_two_ticks"]["canonical_pnl"]
            < baseline["canonical_pnl"])
    # Drop-one-fold arithmetic reconciles against the removed fold.
    folds_block = json.loads(
        (exp_dir / "contribution_report.json").read_text(encoding="utf-8")
    )["fold_pnls"]
    for fid, fold_pnl in folds_block.items():
        dropped = variants[f"drop_one_fold:{fid}"]
        assert dropped["removed_fold_canonical_pnl"] == pytest.approx(fold_pnl)
        assert dropped["canonical_pnl"] == pytest.approx(
            baseline["canonical_pnl"] - fold_pnl, rel=1e-9, abs=1e-9)

    flags = pr.derive_dropone_clean_flags(report)
    # Symmetric cost-only fixture: no drop flips the base sign, so both
    # diagnostics are honestly CLEAN (True). Sign-flip semantics under an
    # asymmetric population are covered by
    # test_dropone_flag_semantics_absence_vs_flip below.
    assert flags["dropone_symbol_clean"] is True
    assert flags["dropone_fold_clean"] is True


def test_dropone_flag_semantics_absence_vs_flip():
    base = {"canonical_pnl": -100.0}
    # No drop_one_symbol variants at all => None (never tested), not True.
    assert pr.derive_dropone_clean_flags({
        "baseline": base, "variants": {}})["dropone_symbol_clean"] is None
    # Executed variant flipping the sign => not clean.
    flipped = pr.derive_dropone_clean_flags({
        "baseline": base,
        "variants": {"drop_one_symbol:A": {"canonical_pnl": 50.0}}})
    assert flipped["dropone_symbol_clean"] is False
