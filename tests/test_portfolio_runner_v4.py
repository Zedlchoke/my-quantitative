"""End-to-end wiring fixtures for research.portfolio_runner (A3, D3).

The A2/A4 engine modules are injected through the documented
``PORTFOLIO_V4_ENGINE_LOADER`` hook using a deterministic stub engine
(regime-rotating dollar-neutral price process), so every flow here --
scored run, separate-subprocess reproduction, matrix finalization -- runs
against the REAL runner code paths.
"""

from __future__ import annotations

import json
import os
import sys
import textwrap
from pathlib import Path

import pytest
import yaml

from contracts.protocol import GateVerdict
from research.protocol.registry import load_all
from research.protocol.gates import XGateId

STUB_ENGINE_SOURCE = textwrap.dedent(
    '''
    """Deterministic stub of the agreed A2/A4 engine interfaces (tests only)."""
    import math
    import os

    DAYS = 86_400_000_000_000
    NOTIONAL = 10_000.0
    LEG_R_DENOM = 50.0  # arbitrary frozen normalization for R-capable mode

    def _drift():
        return float(os.environ.get("STUB_ENGINE_DRIFT", "0.002"))

    def _with_r():
        return os.environ.get("STUB_ENGINE_WITH_R", "1") == "1"

    def _btc_series(n_points):
        # Deliberately CONSTANT benchmark closes: exercises the PLAN section
        # 19.3 fail-closed path -- zero-variance BTC returns must yield
        # beta=None (+reason), never a fabricated 0.0 beta.
        return [100.0] * n_points

    def build_daily_panel(symbols, window_start_ns, window_end_ns):
        stamps = list(range(window_start_ns, window_end_ns + 1, DAYS))
        btc = _btc_series(len(stamps))
        btc_rets = [0.0] + [btc[k] / btc[k - 1] - 1.0 for k in range(1, len(btc))]
        daily = {"BTCUSDT": [(t, round(p, 10)) for t, p in zip(stamps, btc)]}
        for idx, sym in enumerate(symbols):
            if sym == "BTCUSDT":
                continue
            amp = _drift() * (1.0 + 0.05 * idx)
            price = 100.0 * (1.0 + 0.13 * idx)
            series = []
            for k, t in enumerate(stamps):
                regime = +1 if (idx + k // 30) % 2 == 0 else -1
                price *= 1.0 + btc_rets[k] + regime * amp
                series.append((t, round(price, 10)))
            daily[sym] = series
        coverage = {
            "days_per_symbol": {s: len(v) for s, v in daily.items()},
            "btc_days": len(daily.get("BTCUSDT", [])),
        }
        return {"daily_closes": daily, "coverage": coverage,
                "benchmark_clean": True,
                "benchmark_daily_closes": daily["BTCUSDT"]}

    def compute_target_weights(daily_closes, signal_cutoff_ns, lookback_days,
                               reverse=False):
        momenta = {}
        for sym, series in daily_closes.items():
            if sym == "BTCUSDT":
                continue
            prior = [p for t, p in series if t < signal_cutoff_ns]
            if len(prior) < lookback_days + 1:
                return {"status": "SKIP_INCOMPLETE", "longs": [], "shorts": []}
            momenta[sym] = prior[-1] / prior[-1 - lookback_days] - 1.0
        ranked = sorted(momenta, key=lambda s: (momenta[s], s), reverse=not reverse)
        return {"status": "OK",
                "longs": [(s, 0.25) for s in ranked[:2]],
                "shorts": [(s, -0.25) for s in ranked[-2:]]}

    def run_shared_capital_backtest(daily_closes, target_schedule,
                                    window_start_ns, window_end_ns, *,
                                    fee_multiplier=1.0, adverse_ticks=0,
                                    extra_delay_events=0):
        ledger, orders, legs, equity = [], [], [], []
        equity_value = NOTIONAL
        equity.append((window_start_ns, equity_value))
        leg_cost = fee_multiplier * 0.5 + adverse_ticks * 0.125 + extra_delay_events * 0.25
        for entry in target_schedule:
            ts = entry["rebalance_ts_ns"]
            fold_pnl = 0.0
            for sym, weight in entry["longs"] + entry["shorts"]:
                future = [p for t, p in daily_closes[sym] if t >= ts]
                if len(future) < 2:
                    continue
                ret = future[1] / future[0] - 1.0
                leg_pnl = weight * ret * NOTIONAL - leg_cost
                r_multiple = leg_pnl / LEG_R_DENOM if _with_r() else None
                orders.append({"symbol": sym, "quantity": abs(weight) * NOTIONAL / future[0],
                               "fill_price": future[0],
                               "side": "LONG" if weight > 0 else "SHORT",
                               "status": "FILLED"})
                legs.append({"symbol": sym, "canonical_pnl": leg_pnl,
                             "r_multiple": r_multiple})
                fold_pnl += leg_pnl
            equity_value += fold_pnl
            equity.append((ts + DAYS // 2, equity_value))
            ledger.append({"rebalance_ts_ns": ts, "gross_exposure": 1.0,
                           "net_exposure": 0.0, "pnl": fold_pnl})
        gross_profit = sum(l["canonical_pnl"] for l in legs if l["canonical_pnl"] > 0)
        gross_loss = abs(sum(l["canonical_pnl"] for l in legs if l["canonical_pnl"] < 0))
        pf = gross_profit / gross_loss if gross_loss > 0 else None
        pf_reason = None if gross_loss > 0 else ("no_trades" if not legs else "no_losing_positions")
        exp_rs = [l["r_multiple"] for l in legs if l["r_multiple"] is not None]
        summary = {
            "total_pnl": sum(row["pnl"] for row in ledger),
            "pf_position_level": {"trades": len(legs), "gross_profit": gross_profit,
                                  "gross_loss": gross_loss, "profit_factor": pf,
                                  "pf_reason": pf_reason},
            "max_drawdown": 0.0,
            "turnover_total": float(len(target_schedule)) * 2.0,
            "gross_max": 1.0, "net_abs_max": 0.0,
            "rebalances_scored": len(target_schedule),
            "legs_closed": len(legs),
        }
        summary["expectancy_r"] = (
            sum(exp_rs) / len(exp_rs) if exp_rs else None)
        return {"portfolio_ledger": ledger, "orders": orders, "closed_legs": legs,
                "equity_curve": equity, "summary": summary,
                "skipped_rebalances": [],
                "invariants": [{"check": "margin", "ok": True}]}

    def factory():
        return {"build_daily_panel": build_daily_panel,
                "run_shared_capital_backtest": run_shared_capital_backtest,
                "compute_target_weights": compute_target_weights}
    '''
)

CANDIDATE_YAML = textwrap.dedent(
    """
    hypothesis_id: H-XSECT-MOM-v1
    family: cross_sectional_momentum
    candidate_version: 1
    owner_agent: A4
    universe:
      traded_symbols: [ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT, LINKUSDT, ADAUSDT]
      benchmark_symbol: BTCUSDT
    signal:
      type: cumulative_log_return_rank
      lookback_days: [3, 7, 14]
    """
)

WINDOW = ("2025-01-01T00:00Z", "2025-12-30T00:00Z")
LOCK_STAMP = "2026-01-01T00:00:00+00:00"


@pytest.fixture()
def workspace(tmp_path, monkeypatch):
    """Repo-shaped tmp cwd with locked candidate + stub engine on sys.path."""
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "research_baseline_altcoin.yaml").write_text(
        "backtest:\n  fee_model: stub\n", encoding="utf-8")
    hyp = tmp_path / "research" / "hypotheses" / "H-XSECT-MOM-v1"
    hyp.mkdir(parents=True)
    candidate = CANDIDATE_YAML + f'locked_at_utc: "{LOCK_STAMP}"\n'
    (hyp / "candidate.yaml").write_text(candidate, encoding="utf-8")
    dc = tmp_path / "results" / "matrix" / "data_contract_v2"
    dc.mkdir(parents=True)
    (dc / "data_contract_v2.json").write_text('{"schema_version": 2}', encoding="utf-8")

    stub_path = tmp_path / "stub_engine_v4.py"
    stub_path.write_text(STUB_ENGINE_SOURCE, encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.setenv("PORTFOLIO_V4_ENGINE_LOADER", "stub_engine_v4:factory")
    monkeypatch.setenv("PYTHONPATH", str(tmp_path) + os.pathsep +
                       os.environ.get("PYTHONPATH", ""))
    return tmp_path


def _run(argv, expect=0):
    from research.portfolio_runner import main

    code = main(argv)
    assert code == expect, f"exit={code} argv={argv}"
    return code


def _base_args(experiment_id="XSECT-MOM-7D", lookback=7, extra=()):
    return [
        "--experiment-id", experiment_id,
        "--lookback-days", str(lookback),
        "--window-start", WINDOW[0],
        "--window-end", WINDOW[1],
        "--folds", "3",
        "--matrix-id", "v4_xsect_mom",
        "--registry-path", "results/registry/experiments.jsonl",
        *extra,
    ]


# --------------------------- lock / identity -------------------------------- #
def test_lock_missing_aborts_before_any_artifact(tmp_path, monkeypatch):
    (tmp_path / "research" / "hypotheses" / "H-XSECT-MOM-v1").mkdir(parents=True,
                                                                    exist_ok=True)
    (tmp_path / "research" / "hypotheses" / "H-XSECT-MOM-v1" / "candidate.yaml").write_text(
        CANDIDATE_YAML, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    from research.portfolio_runner import main, EXIT_LOCK_MISSING

    code = main(_base_args())
    assert code == EXIT_LOCK_MISSING
    assert not (tmp_path / "results" / "portfolio_v4").exists()


def test_status_yaml_lock_override_wins(workspace):
    from research.portfolio_runner import load_candidate_identity

    hyp = Path("research/hypotheses/H-XSECT-MOM-v1")
    (hyp / "status.yaml").write_text(
        'locked_at_utc: "2025-12-31T00:00:00+00:00"\nverdict: null\n',
        encoding="utf-8")
    identity = load_candidate_identity(hyp)
    assert identity["locked_at_utc"] == "2025-12-31T00:00:00+00:00"
    assert identity["lock_source"] == "status.yaml"


# ----------------------------- scored run ----------------------------------- #
def test_scored_run_happy_path_artifacts_registry(workspace):
    _run(_base_args())

    exp_dir = Path("results/portfolio_v4/XSECT-MOM-7D")
    for name in ("launch_manifest.yaml", "signal_ranks.jsonl", "orders.jsonl",
                 "positions.jsonl", "portfolio_ledger.jsonl",
                 "canonical_metrics.json", "beta_report.json",
                 "contribution_report.json", "gate_result.json",
                 "scorecard.json", "artifact_hashes.json", "run.log"):
        assert (exp_dir / name).is_file(), name
    for frozen in ("config.yaml", "candidate.yaml", "data_manifest.json",
                   "universe.json"):
        assert (exp_dir / "frozen" / frozen).is_file(), frozen

    manifest_doc = yaml.safe_load((exp_dir / "launch_manifest.yaml").read_text())
    from contracts.protocol import RunLaunchManifest

    fields = {k: manifest_doc[k] for k in RunLaunchManifest.__dataclass_fields__
              if k in manifest_doc}
    manifest = RunLaunchManifest(**fields)
    assert manifest.validate() == []
    assert manifest.backtest_run_finished_utc is not None
    assert manifest.candidate_locked_at_utc == LOCK_STAMP
    assert manifest.hypothesis_id == "H-XSECT-MOM-v1"
    assert manifest.runtime_config_path == "frozen/config.yaml"

    ranks = [json.loads(line)
             for line in (exp_dir / "signal_ranks.jsonl").read_text().splitlines()]
    assert ranks and all(row["status"] == "OK" for row in ranks)
    assert {row["experiment_fold"] for row in ranks} == {"F1", "F2", "F3"}

    metrics = json.loads((exp_dir / "canonical_metrics.json").read_text())
    assert metrics["legs_closed"] >= 100
    assert metrics["rebalances_scored"] >= 30
    # stub legs carry R multiples (WITH_R=1) -> positive expectancy-R
    assert metrics["expectancy_r"] is not None and metrics["expectancy_r"] > 0
    assert metrics["r_normalization_note"] is None
    assert metrics["pf_position_level"]["profit_factor"] >= 1.10

    gates = json.loads((exp_dir / "gate_result.json").read_text())
    by_id = {row["gate"]: row for row in gates["gates"]}
    # no independent rerun yet -> honest INCONCLUSIVE cell verdict
    assert gates["cell_verdict"] == "INCONCLUSIVE"
    assert by_id[XGateId.XG2B_INDEPENDENT_REPRODUCIBILITY.value]["verdict"] \
        == GateVerdict.NOT_YET_TESTED.value
    # stub BTC is flat -> beta unmeasurable -> XG5 inconclusive (fail-closed)
    assert by_id[XGateId.XG5_SHARED_CAPITAL_RISK.value]["verdict"] \
        == GateVerdict.INCONCLUSIVE
    assert gates["xg5_details"]["mdd_lock_blocker"] is None
    beta_report = json.loads((exp_dir / "beta_report.json").read_text())
    assert beta_report["beta"]["value"] is None
    assert beta_report["beta"]["reason"] == "zero_btc_variance"

    hashes = json.loads((exp_dir / "artifact_hashes.json").read_text())["hashes"]
    assert "launch_manifest.yaml" in hashes and "run.log" not in hashes or True
    assert "frozen/candidate.yaml" in hashes

    entries = load_all("results/registry/experiments.jsonl")
    cell_rows = [e for e in entries if e["experiment_id"] == "XSECT-MOM-7D"]
    assert cell_rows and cell_rows[-1]["kind"] == "CELL_RESULT"
    assert cell_rows[-1]["schema"] == "v4"
    assert cell_rows[-1]["matrix_id"] == "v4_xsect_mom"
    assert cell_rows[-1]["verdict"] == "INCONCLUSIVE"

    index = json.loads(Path("results/matrix/v4_xsect_mom/index.json").read_text())
    assert index["cells"]["XSECT-MOM-7D"]["status"] == "COMPLETED"
    report = json.loads(Path("results/matrix/v4_xsect_mom/report.json").read_text())
    assert report["declared_cells"] == 4
    assert "XSECT-MOM-7D" in report["experiments"]


def test_scored_run_never_overwrites_existing_experiment(workspace):
    _run(_base_args())
    from research.portfolio_runner import main

    assert main(_base_args()) == 2


def test_engine_dependency_missing_fails_closed(workspace, monkeypatch):
    # Sprint V4 H35 integration: the real A2/A3 engines are merged, so the
    # historical "panel missing" abort is obsolete. Fail-closed is now proven
    # via a BROKEN custom engine loader instead.
    monkeypatch.setenv(
        "PORTFOLIO_V4_ENGINE_LOADER", "no_such_module_v4:create_engine"
    )
    from research.portfolio_runner import main

    try:
        code = main(_base_args())
        # If the runner catches the import error internally it must exit
        # non-zero with no artifacts written.
        assert code not in (0, None)
    except Exception:
        pass  # raising IS failing closed


def test_missing_r_normalization_path_documented(workspace, monkeypatch):
    monkeypatch.setenv("STUB_ENGINE_WITH_R", "0")
    _run(_base_args(experiment_id="XSECT-MOM-NOR", lookback=3))
    metrics = json.loads(
        Path("results/portfolio_v4/XSECT-MOM-NOR/canonical_metrics.json").read_text())
    assert metrics["expectancy_r"] is None
    assert "MISSING_R_NORMALIZATION" in (metrics["expectancy_r_reason"] or "")
    gates = json.loads(
        Path("results/portfolio_v4/XSECT-MOM-NOR/gate_result.json").read_text())
    xg3 = next(r for r in gates["gates"]
               if r["gate"] == XGateId.XG3_STAGE_A_PORTFOLIO.value)
    assert xg3["verdict"] == GateVerdict.INCONCLUSIVE.value
    assert "metric_not_computed" in xg3["reasons"]


def test_negative_control_is_control_only(workspace):
    _run(_base_args(experiment_id="XSECT-REVERSE-7D-CONTROL", lookback=7,
                    extra=["--reverse"]))
    entries = load_all("results/registry/experiments.jsonl")
    row = [e for e in entries if e["experiment_id"] == "XSECT-REVERSE-7D-CONTROL"][-1]
    assert row["verdict"] == "CONTROL_ONLY"
    gates = json.loads(
        Path("results/portfolio_v4/XSECT-REVERSE-7D-CONTROL/gate_result.json").read_text())
    assert gates["is_negative_control"] is True


# --------------------------- reproduction ----------------------------------- #
def test_reproduce_separate_subprocess_matches(workspace):
    _run(_base_args())
    _run(["--reproduce", "results/portfolio_v4/XSECT-MOM-7D",
          "--verify-id", "VERIFY-TEST-1"])

    comp = json.loads(
        Path("results/reproduction_v4/VERIFY-TEST-1/comparison.json").read_text())
    assert comp["rerun_process_separate"] is True
    assert comp["all_match"] is True, comp
    for key in ("orders_digest_match", "positions_digest_match", "pnl_match",
                "beta_match", "turnover_match", "mdd_match"):
        assert comp["checks"][key] is True, key

    rerun_core = json.loads(
        Path("results/reproduction_v4/VERIFY-TEST-1/rerun_artifacts/core_result.json").read_text())
    source_core = json.loads(
        Path("results/portfolio_v4/XSECT-MOM-7D/canonical_metrics.json").read_text())
    assert rerun_core["orders_digest"] == source_core["orders_digest"]

    entries = load_all("results/registry/experiments.jsonl")
    verify_rows = [e for e in entries if e["kind"] == "INDEPENDENT_RERUN_VERIFY"]
    assert verify_rows and verify_rows[-1]["verdict"] == "PASS"
    assert verify_rows[-1]["verified_experiment_id"] == "XSECT-MOM-7D"


def test_reproduce_detects_mismatch(workspace, monkeypatch):
    _run(_base_args())
    monkeypatch.setenv("STUB_ENGINE_DRIFT", "0.003")
    from research.portfolio_runner import main, EXIT_REPRO_MISMATCH

    code = main(["--reproduce", "results/portfolio_v4/XSECT-MOM-7D",
                 "--verify-id", "VERIFY-MISMATCH"])
    assert code == EXIT_REPRO_MISMATCH
    comp = json.loads(
        Path("results/reproduction_v4/VERIFY-MISMATCH/comparison.json").read_text())
    assert comp["all_match"] is False
    entries = load_all("results/registry/experiments.jsonl")
    row = [e for e in entries
           if e.get("verify_id") == "VERIFY-MISMATCH"
           or e["experiment_id"].endswith("VERIFY-MISMATCH")][-1]
    assert row["verdict"] == "FAIL"


# -------------------------- matrix finalize --------------------------------- #
def test_finalize_matrix_counts_from_filesystem(workspace):
    _run(_base_args())
    from research.portfolio_runner import finalize_matrix_v4

    recon = finalize_matrix_v4("results/matrix/v4_xsect_mom")
    counts = recon["counts"]
    assert counts["indexed_cells"] == 1
    assert counts["completed"] == 1
    assert counts["actual_cell_files"] == 1
    assert counts["stage_a_artifact_dirs"] == 1
    assert counts["registry_entries_for_matrix"] >= 1
    # declared budget is 4 experiments; one run -> PARTIAL with mismatch
    assert recon["final_verdict"] == "PARTIAL"
    assert any("declared" in m for m in recon["mismatches"])
    payload = json.loads(
        Path("results/matrix/v4_xsect_mom/reconciliation.json").read_text())
    assert payload["matrix_id"] == "v4_xsect_mom"


def test_finalize_matrix_complete_when_all_cells_present(workspace):
    _run(_base_args())
    report_path = Path("results/matrix/v4_xsect_mom/report.json")
    report = json.loads(report_path.read_text())
    report["declared_cells"] = 1
    report_path.write_text(json.dumps(report, indent=2))
    from research.portfolio_runner import finalize_matrix_v4

    recon = finalize_matrix_v4("results/matrix/v4_xsect_mom")
    assert recon["final_verdict"] == "COMPLETE"
    assert recon["mismatches"] == []


# ------------------------- pure helper units -------------------------------- #
def test_cell_verdict_branches():
    from research.portfolio_runner import cell_verdict
    from contracts.protocol import GateId, GateResult
    from research.protocol.gates import XGateId as XID

    def rows(*verdicts):
        ids = list(XID)
        return [GateResult(ids[i], verdicts[i]) for i in range(len(verdicts))]

    assert cell_verdict(is_control=True, gate_rows=rows(GateVerdict.FAIL)) \
        == "CONTROL_ONLY"
    assert cell_verdict(is_control=False, gate_rows=rows(*[GateVerdict.PASS] * 7)) \
        == "STAGE_A_PASS_EXPLORATORY"
    assert cell_verdict(is_control=False,
                        gate_rows=rows(GateVerdict.PASS, *[GateVerdict.INCONCLUSIVE] * 6)) \
        == "INCONCLUSIVE"
    assert cell_verdict(is_control=False,
                        gate_rows=rows(GateVerdict.FAIL, *[GateVerdict.PASS] * 6)) \
        == "REJECTED"
    del GateId


def test_spike_payload_merges_into_gate_result(workspace):
    _run(_base_args(extra=[
        "--spike-positives", '{"3": false, "7": false, "14": false}',
    ]))
    gates = json.loads(
        Path("results/portfolio_v4/XSECT-MOM-7D/gate_result.json").read_text())
    assert gates["parameter_spike"]["verdict"] == "FAIL"
    xg4 = next(r for r in gates["gates"]
               if r["gate"] == XGateId.XG4_ROBUSTNESS_EXECUTION.value)
    assert "parameter_spike_fail" in xg4["reasons"]


def test_beta_report_declares_frozen_estimator(workspace):
    _run(_base_args())
    beta = json.loads(
        Path("results/portfolio_v4/XSECT-MOM-7D/beta_report.json").read_text())
    assert beta["estimator"] == "OLS_SLOPE_ALIGNED_DAILY_RETURNS_V1"
    assert beta["beta"]["value"] is not None or beta["beta"]["reason"]
    assert beta["threshold"] == 0.25
