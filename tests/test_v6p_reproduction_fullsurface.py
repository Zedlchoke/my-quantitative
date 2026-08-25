"""V6P A5 fixtures: full-surface reproduction + reconciliation fail-closed.

PLAN section 6.4 items 8-10 under test (owner A5):

* N11 -- ``run_reproduce`` compares the FULL scored surface: signals, orders,
  positions, ledger, funding cashflows, terminal positions, exposure
  control, accounting reconciliation, commission/slippage, canonical metrics
  (incl. fold returns / MDD), stress report, gate verdict maps, scorecard
  totals and the final artifact-hash manifest. ``all_match`` is true only if
  EVERY component matches; comparison.json lists per-component booleans.
  A single byte flip in any copied artifact (e.g. funding_cashflows) must
  break its component AND all_match.
* N12 -- finalize_matrix is FAIL-CLOSED (schema v3): append-only violation,
  stale declared stage_a_root, required artifacts missing from an indexed
  experiment dir, and transition counts disagreeing with the index each
  produce a FAIL-level mismatch entry.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

import research.protocol.registry as registry_mod
from contracts.protocol import GateVerdict
from research.portfolio_runner import EXIT_REPRO_MISMATCH, main
from research.protocol.reconciliation import (
    REQUIRED_EXPERIMENT_ARTIFACT_FILES,
    RECONCILIATION_SCHEMA_VERSION,
    finalize_matrix,
)
from research.protocol.registry import append
from research.reconciliation import finalize_directory_hashes, verify_experiment_dir

WINDOW_START = "2026-01-01T00:00Z"
WINDOW_END = "2026-01-04T00:00Z"
LOCK_STAMP = "2026-01-05T00:00:00+00:00"

CANDIDATE_YAML = (
    "hypothesis_id: H-XSECT-MOM-v1\n"
    "family: cross_sectional_momentum\n"
    "candidate_version: 1\n"
    "owner_agent: A4\n"
    "universe:\n"
    "  traded_symbols: [SYMAUSDT, SYMBUSDT]\n"
    "  benchmark_symbol: BTCUSDT\n"
    "signal:\n"
    "  type: cumulative_log_return_rank\n"
    "  lookback_days: [3]\n"
)

FULL_SURFACE_CHECKS = (
    "signals_match",
    "orders_match",
    "positions_match",
    "ledger_match",
    "funding_cashflows_match",
    "terminal_positions_match",
    "exposure_control_match",
    "accounting_reconciliation_match",
    "commission_slippage_match",
    "stress_report_match",
    "canonical_metrics_match",
    "fold_returns_match",
    "gate_result_verdicts_match",
    "scorecard_totals_match",
    "artifact_hashes_match",
    # legacy numeric components retained for continuity:
    "orders_digest_match", "positions_digest_match", "pnl_match",
    "beta_match", "turnover_match", "mdd_match",
)


def _ns(iso_text: str) -> int:
    text = iso_text.replace("Z", "+00:00")
    return int(datetime.fromisoformat(text).astimezone(timezone.utc)
               .timestamp() * 1_000_000_000)


def _spec(workspace, name="panel"):
    days = ["2026-01-01", "2026-01-02", "2026-01-03"]
    bars = []
    for day_iso in days:
        for hhmm in ("00:15", "00:30", "08:00"):  # 08:00 hosts the funding stamp
            ts = f"{day_iso}T{hhmm}:00Z"
            for sym, close in (("SYMAUSDT", 100.0), ("SYMBUSDT", 100.0),
                               ("BTCUSDT", 100.0)):
                bars.append({"symbol": sym, "ts": ts, "open": close,
                             "high": close, "low": close, "close": close,
                             "volume": 1.0})
    spec = {
        "traded_symbols": ["SYMAUSDT", "SYMBUSDT"],
        "benchmark_symbol": "BTCUSDT",
        "initial_capital": 100000.0,
        "fee_taker": 0.0005,
        "slippage_ticks": 1,
        "tick_size": {"*": 0.01},
        "step_size": {"*": 0.001},
        "min_notional": 5.0,
        "bars": bars,
        "funding": [
            {"symbol": "SYMAUSDT",
             "funding_time_ms": _ns("2026-01-02T08:00:00Z") // 1_000_000,
             "fundingRate": "0.0001"},
            {"symbol": "SYMBUSDT",
             "funding_time_ms": _ns("2026-01-02T08:00:00Z") // 1_000_000,
             "fundingRate": "0.0003"},
        ],
        "targets": {
            "longs": [["SYMAUSDT", 0.25]],
            "shorts": [["SYMBUSDT", -0.25]],
        },
    }
    path = workspace / f"{name}.json"
    path.write_text(json.dumps(spec), encoding="utf-8")
    return path


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


def _scored(workspace, experiment_id="V6P-A5-FULLSURF") -> Path:
    code = main([
        "--experiment-id", experiment_id,
        "--lookback-days", "3",
        "--window-start", WINDOW_START,
        "--window-end", WINDOW_END,
        "--folds", "3",
        "--matrix-id", "v6p_a5_repro",
        "--registry-path", "results/registry/experiments.jsonl",
        "--synthetic-panel", str(_spec(workspace)),
    ])
    assert code == 0
    return Path("results/portfolio_v4") / experiment_id


# --------------------------- N11 full surface -------------------------------- #
def test_full_surface_reproduction_matches_component_by_component(workspace):
    source = _scored(workspace)
    code = main([
        "--reproduce", str(source),
        "--verify-id", "VERIFY-FULL-1",
        "--registry-path", "results/registry/experiments.jsonl",
    ])
    assert code == 0
    comp = json.loads(Path(
        "results/reproduction_v4/VERIFY-FULL-1/comparison.json").read_text())
    assert comp["comparison_surface"] == "full_v6p_n11"
    assert comp["rerun_process_separate"] is True
    for key in FULL_SURFACE_CHECKS:
        assert comp["checks"][key] is True, key
    assert comp["all_match"] is True
    # Per-component listing carries digests for every copied artifact.
    for component in ("signals", "orders", "positions", "ledger",
                      "funding_cashflows", "terminal_positions",
                      "exposure_control", "accounting_reconciliation",
                      "commission_slippage", "stress_report",
                      "canonical_metrics"):
        detail = comp["components"][component]
        assert detail["match"] is True, component
        assert detail["source_sha256"] == detail["rerun_sha256"]


def test_byte_flip_in_funding_copy_breaks_component_and_all_match(workspace):
    source = _scored(workspace)
    target = source / "funding_cashflows.jsonl"
    original = target.read_bytes()
    target.write_bytes(original.replace(b'"rate": 0.0001', b'"rate": 0.9'))
    assert target.read_bytes() != original

    code = main([
        "--reproduce", str(source),
        "--verify-id", "VERIFY-BYTEFLIP",
        "--registry-path", "results/registry/experiments.jsonl",
    ])
    assert code == EXIT_REPRO_MISMATCH
    comp = json.loads(Path(
        "results/reproduction_v4/VERIFY-BYTEFLIP/comparison.json").read_text())
    assert comp["checks"]["funding_cashflows_match"] is False
    assert comp["components"]["funding_cashflows"]["reason"] == \
        "digest_mismatch"
    # The tampered source also fails external-reader hash verification.
    assert comp["checks"]["artifact_hashes_match"] is False
    assert comp["all_match"] is False


def test_missing_source_surface_fails_closed(workspace):
    source = _scored(workspace, "V6P-A5-NOSTRESSFILE")
    (source / "stress_report.json").unlink()
    code = main([
        "--reproduce", str(source),
        "--verify-id", "VERIFY-MISSING-SURFACE",
        "--registry-path", "results/registry/experiments.jsonl",
    ])
    assert code == EXIT_REPRO_MISMATCH
    comp = json.loads(Path(
        "results/reproduction_v4/VERIFY-MISSING-SURFACE/comparison.json"
    ).read_text())
    assert comp["checks"]["stress_report_match"] is False
    assert comp["components"]["stress_report"]["reason"] == \
        "missing_source_artifact"
    assert comp["all_match"] is False


# ------------------ N12 reconciliation fail-closed (schema v3) --------------- #
@pytest.fixture()
def registry_env(tmp_path, monkeypatch):
    reg_path = tmp_path / "reg.jsonl"
    monkeypatch.setattr(registry_mod, "DEFAULT_REGISTRY_PATH", reg_path)
    monkeypatch.setattr(registry_mod, "DEFAULT_REGISTRY_DIR", tmp_path)
    return reg_path


def _full_exp_dir(root: Path, matrix_id: str, exp_id: str) -> Path:
    """A REAL-looking finalized experiment dir (complete artifact set)."""
    exp_dir = root / exp_id
    exp_dir.mkdir(parents=True)
    (exp_dir / "launch_manifest.yaml").write_text(yaml.safe_dump({
        "matrix_id": matrix_id, "experiment_id": exp_id}), encoding="utf-8")
    for name in REQUIRED_EXPERIMENT_ARTIFACT_FILES:
        if name.endswith(".jsonl"):
            (exp_dir / name).write_text('{"row": 1}\n', encoding="utf-8")
        else:
            (exp_dir / name).write_text(json.dumps({"ok": True}),
                                        encoding="utf-8")
    return exp_dir


def _matrix(tmp_path: Path, name: str, *, stage_a_root=None,
            experiments=None) -> tuple[Path, Path]:
    root = tmp_path / f"{name}_root"
    exp_dir = _full_exp_dir(root, name, f"{name}-EXP-1")
    matrix_dir = tmp_path / name
    matrix_dir.mkdir()
    (matrix_dir / "index.json").write_text(json.dumps({"cells": {
        f"{name}-EXP-1": {
            "artifact_path": str(exp_dir),
            "stage_a_dir": str(exp_dir),
            "status": "COMPLETED",
            "verdict": "REJECTED",
            "experiment_id": f"{name}-EXP-1",
        },
    }, "matrix_id": name, "schema_version": 4}), encoding="utf-8")
    report_doc = {"matrix_id": name, "declared_cells": 1}
    if stage_a_root is not None:
        report_doc["stage_a_root"] = str(stage_a_root)
    if experiments is not None:
        report_doc["experiments"] = experiments
    (matrix_dir / "report.json").write_text(json.dumps(report_doc),
                                            encoding="utf-8")
    return matrix_dir, exp_dir


def test_schema_bumped_to_v3_and_clean_matrix_completes(tmp_path, registry_env):
    matrix_dir, _ = _matrix(tmp_path, "m_v3_clean",
                            experiments=["m_v3_clean-EXP-1"])
    payload = finalize_matrix(matrix_dir, registry_env)
    assert RECONCILIATION_SCHEMA_VERSION == 3  # v2 -> v3 bump (N12)
    assert payload["schema_version"] == 3
    assert payload["final_verdict"] == "COMPLETE"
    assert payload["registry_append_only_verified"] is True


def test_append_only_violation_fails_finalization(tmp_path, registry_env):
    matrix_dir, _ = _matrix(tmp_path, "m_append_only",
                            experiments=["m_append_only-EXP-1"])
    append({"experiment_id": "LATER", "verdict": "PASS",
            "appended_at": "2026-08-24T02:00:00+00:00"}, path=registry_env)
    append({"experiment_id": "EARLIER", "verdict": "PASS",
            "appended_at": "2026-08-24T01:00:00+00:00"}, path=registry_env)
    payload = finalize_matrix(matrix_dir, registry_env)
    assert payload["registry_append_only_verified"] is False
    assert "registry_append_only_violation" in payload["mismatches"]
    assert payload["final_verdict"] == "FAIL"


def test_stale_declared_stage_a_root_fails(tmp_path, registry_env):
    # The declared root EXISTS but holds only OTHER matrices' experiments --
    # classic N12 case of a diagnostic matrix still declaring the scored root.
    stale_root = tmp_path / "stale_root"
    foreign = _full_exp_dir(stale_root, "some_other_matrix", "FOREIGN-EXP")
    matrix_dir, _ = _matrix(tmp_path, "m_stale_root", stage_a_root=stale_root)
    payload = finalize_matrix(matrix_dir, registry_env)
    assert any(m.startswith("stale_stage_a_root:") for m in payload["mismatches"])
    assert payload["final_verdict"] == "FAIL"


def test_missing_required_artifact_in_indexed_dir_fails(tmp_path, registry_env):
    matrix_dir, exp_dir = _matrix(tmp_path, "m_missing_art")
    (exp_dir / "funding_cashflows.jsonl").unlink()  # N06 defect class
    payload = finalize_matrix(matrix_dir, registry_env)
    assert any(m.startswith("missing_required_artifacts:")
               and "funding_cashflows.jsonl" in m
               for m in payload["mismatches"])
    assert payload["final_verdict"] == "FAIL"


def test_transition_counts_disagreeing_with_index_fail(tmp_path, registry_env):
    matrix_dir, _ = _matrix(tmp_path, "m_transition",
                            experiments=["SOME_OTHER_ID"])
    payload = finalize_matrix(matrix_dir, registry_env)
    assert any(m.startswith("transition_counts_disagree_with_index:")
               for m in payload["mismatches"])
    assert payload["final_verdict"] == "FAIL"


def test_manifest_only_stub_dirs_are_exempt_from_artifact_set(
        tmp_path, registry_env):
    # Diagnostic placeholder dirs holding ONLY a launch manifest make no
    # data claims; v3 must NOT demand the full artifact set from them.
    matrix_dir = tmp_path / "m_stub_ok"
    matrix_dir.mkdir()
    exp_dir = tmp_path / "m_stub_ok_root" / "STUB-EXP"
    exp_dir.mkdir(parents=True)
    (exp_dir / "launch_manifest.yaml").write_text(
        yaml.safe_dump({"matrix_id": "m_stub_ok",
                        "experiment_id": "STUB-EXP"}), encoding="utf-8")
    (matrix_dir / "index.json").write_text(json.dumps({"cells": {
        "STUB-EXP": {"artifact_path": str(exp_dir),
                     "stage_a_dir": str(exp_dir),
                     "status": "COMPLETED", "verdict": "REJECTED",
                     "experiment_id": "STUB-EXP"}},
        "matrix_id": "m_stub_ok", "schema_version": 4}), encoding="utf-8")
    (matrix_dir / "report.json").write_text(json.dumps({
        "matrix_id": "m_stub_ok", "declared_cells": 1}), encoding="utf-8")
    payload = finalize_matrix(matrix_dir, registry_env)
    assert not any(m.startswith("missing_required_artifacts:")
                   for m in payload["mismatches"])
    assert payload["final_verdict"] == "COMPLETE"


# --------------------- XG2a tampered-hash negative --------------------------- #
def test_tampered_hash_breaks_xg2a_external_reader_verification(tmp_path):
    exp_dir = tmp_path / "EXP-TAMPER"
    exp_dir.mkdir()
    (exp_dir / "cell.json").write_text(json.dumps({"experiment_id": "X"}),
                                       encoding="utf-8")
    (exp_dir / "positions.jsonl").write_text(
        json.dumps({"canonical_pnl": 10.0}) + "\n", encoding="utf-8")
    (exp_dir / "funding_cashflows.jsonl").write_text(
        json.dumps({"funding_net": -0.5}) + "\n", encoding="utf-8")
    (exp_dir / "costs.jsonl").write_text(
        json.dumps({"commission": 0.3, "modeled_slippage": 0.1}) + "\n",
        encoding="utf-8")
    (exp_dir / "accounting_reconciliation.json").write_text(json.dumps({
        "positions_total_pnl": 10.0, "funding_total": -0.5,
        "commission_total": 0.3, "slippage_total": 0.1}), encoding="utf-8")
    finalize_directory_hashes(exp_dir)

    clean = verify_experiment_dir(exp_dir, phase="inputs")
    assert clean.hashes_match is True

    # Byte-flip AFTER finalization must be detected.
    (exp_dir / "funding_cashflows.jsonl").write_text(
        json.dumps({"funding_net": +0.5}) + "\n", encoding="utf-8")
    tampered = verify_experiment_dir(exp_dir, phase="inputs")
    assert tampered.verdict() is GateVerdict.FAIL
    assert tampered.hashes_match is False
    assert "artifact_hash_mismatch:funding_cashflows.jsonl" in tampered.reasons
