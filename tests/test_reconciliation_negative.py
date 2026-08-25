"""Negative fixtures for PLAN section 8-D2/D3 (owner A5).

D2: matrix reconciliation must validate declared==indexed==completed cells,
one experiment identity per cell, referenced experiment dirs, required
artifacts, registry uniqueness under the declared identity rule, and derive
everything from the FINAL index -- with diagnostic roots measured at their
real location (never marked harmless).

D3: every scored integrity gate must FAIL when its underlying evidence is
tampered with, and verdicts must stay distinct (PASS / FAIL / INCONCLUSIVE /
NOT_YET_TESTED) instead of collapsing to constant True.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

import research.protocol.registry as registry_mod
from contracts.protocol import (
    ArtifactIntegrityResult,
    GateVerdict,
    IndependentReproductionResult,
)
from research.protocol.gates import evaluate_xg1_measured
from research.protocol.reconciliation import finalize_matrix
from research.protocol.registry import append
from research.reconciliation import finalize_directory_hashes, verify_experiment_dir


@pytest.fixture()
def registry_env(tmp_path, monkeypatch):
    reg_path = tmp_path / "reg.jsonl"
    monkeypatch.setattr(registry_mod, "DEFAULT_REGISTRY_PATH", reg_path)
    monkeypatch.setattr(registry_mod, "DEFAULT_REGISTRY_DIR", tmp_path)
    return reg_path


def _append_rows(registry_env, rows):
    for i, row in enumerate(rows):
        append({**row, "appended_at": f"2026-08-24T00:{i // 60:02d}:{i % 60:02d}+00:00"},
               path=registry_env)


def _build_diagnostic_style_matrix(
    tmp_path: Path,
    name: str,
    *,
    cells: int = 4,
    declared: int | None = None,
    wrong_stage_a_root: bool = True,
) -> Path:
    """Replica of the measured v4_recalc_diagnostic_v5 layout: directory-style
    cell artifacts under a diagnostic output root, launch manifests inside."""
    matrix_dir = tmp_path / name
    matrix_dir.mkdir(parents=True)
    diag_root = tmp_path / f"{name}_diag_root"
    index_cells: dict[str, dict] = {}
    for i in range(cells):
        exp_id = f"XSECT-{i}-DIAG"
        exp_dir = diag_root / exp_id
        exp_dir.mkdir(parents=True)
        (exp_dir / "launch_manifest.yaml").write_text(
            yaml.safe_dump({"matrix_id": name, "experiment_id": exp_id}),
            encoding="utf-8",
        )
        index_cells[exp_id] = {
            "artifact_path": str(exp_dir),
            "status": "COMPLETED",
            "verdict": "REJECTED",
        }
    (matrix_dir / "index.json").write_text(
        json.dumps({"cells": index_cells, "matrix_id": name, "schema_version": 4}),
        encoding="utf-8",
    )
    report_doc = {"matrix_id": name, "declared_cells": declared if declared is not None else cells}
    if wrong_stage_a_root:
        report_doc["stage_a_root"] = str(tmp_path / "empty_default_root")
    (matrix_dir / "report.json").write_text(json.dumps(report_doc), encoding="utf-8")
    return matrix_dir


# --------------------------- D2 contract ------------------------------------- #

def test_diagnostic_matrix_with_wrong_declared_root_reconciles(tmp_path, registry_env):
    matrix_dir = _build_diagnostic_style_matrix(tmp_path, "v4_recalc_diagnostic_v5")
    _append_rows(
        registry_env,
        [
            {"experiment_id": f"XSECT-{i}-DIAG", "verdict": "REJECTED",
             "kind": "DIAGNOSTIC_RECALC", "schema": "v5",
             "source_trial_experiment_id": f"T{i}", "matrix_id": "v4_recalc_diagnostic_v5"}
            for i in range(4)
        ]
        + [
            {"experiment_id": f"RERUN-{i}", "verdict": "PASS",
             "kind": "INDEPENDENT_RERUN_VERIFY", "schema": "v5",
             "matrix_id": "v4_recalc_diagnostic_v5",
             "verified_experiment_id": f"XSECT-{i}-DIAG",
             "verification_type": "POSITIONS_DIGEST_PNL"}
            for i in range(4)
        ],
    )
    payload = finalize_matrix(matrix_dir, registry_env)
    counts = payload["counts"]
    # V6P N12 (A5): fail-closed reconciliation bumped the schema v2 -> v3.
    assert payload["schema_version"] == 3
    assert counts["declared_cells"] == counts["indexed_cells"] == counts["completed"] == 4
    assert counts["stage_a_dirs_expected"] == 4
    assert counts["stage_a_artifact_dirs"] == 4  # found at the REAL diagnostic root
    assert counts["registry_entries_for_matrix"] == 8
    assert counts["registry_cell_identity_entries"] == 4
    assert counts["registry_verification_entries"] == 4
    assert not any("stage_a" in m for m in payload["mismatches"])
    assert payload["final_verdict"] == "COMPLETE"


def test_missing_referenced_stage_a_dir_fails_closed(tmp_path, registry_env):
    matrix_dir = _build_diagnostic_style_matrix(tmp_path, "m_ghost_dir")
    index = json.loads((matrix_dir / "index.json").read_text())
    first_key = next(iter(index["cells"]))
    index["cells"][first_key]["stage_a_dir"] = str(tmp_path / "deleted_exp_dir")
    (matrix_dir / "index.json").write_text(json.dumps(index), encoding="utf-8")
    payload = finalize_matrix(matrix_dir, registry_env)
    assert payload["final_verdict"] == "FAIL"
    assert any(
        m.startswith("stage_a_dir_invalid:") and m.endswith(":missing_launch_manifest")
        for m in payload["mismatches"]
    )


def test_exp_dir_without_launch_manifest_fails_closed(tmp_path, registry_env):
    matrix_dir = _build_diagnostic_style_matrix(tmp_path, "m_no_manifest")
    index = json.loads((matrix_dir / "index.json").read_text())
    Path(index["cells"][next(iter(index["cells"]))]["artifact_path"]).joinpath(
        "launch_manifest.yaml"
    ).unlink()
    payload = finalize_matrix(matrix_dir, registry_env)
    assert payload["final_verdict"] == "FAIL"
    assert any(
        m.startswith("stage_a_dir_invalid:") and m.endswith(":missing_launch_manifest")
        for m in payload["mismatches"]
    )


def test_duplicate_index_experiment_identity_fails_closed(tmp_path, registry_env):
    matrix_dir = _build_diagnostic_style_matrix(tmp_path, "m_dup_exp", cells=2)
    index = json.loads((matrix_dir / "index.json").read_text())
    keys = list(index["cells"])
    index["cells"][keys[1]]["experiment_id"] = index["cells"][keys[0]][
        "experiment_id"
    ] = keys[0]
    (matrix_dir / "index.json").write_text(json.dumps(index), encoding="utf-8")
    payload = finalize_matrix(matrix_dir, registry_env)
    assert payload["final_verdict"] == "FAIL"
    assert any(m.startswith("duplicate_experiment_identity:") for m in payload["mismatches"])


def test_artifact_document_identity_mismatch_fails_closed(tmp_path, registry_env):
    matrix_dir = tmp_path / "m_ident"
    cells_dir = matrix_dir / "cells"
    cells_dir.mkdir(parents=True)
    artifact = cells_dir / "ema_atr__SOLUSDT__base.json"
    artifact.write_text(
        json.dumps({
            "identity": {"strategy_type": "ema_atr", "symbol": "SOLUSDT"},
            "cell_result": {"status": "COMPLETED", "experiment_id": "EXP-OTHER"},
        }),
        encoding="utf-8",
    )
    (matrix_dir / "index.json").write_text(json.dumps({"cells": {
        "ema_atr__SOLUSDT__base": {
            "artifact_path": str(artifact),
            "status": "COMPLETED",
            "experiment_id": "EXP-1",
        },
    }}), encoding="utf-8")
    (matrix_dir / "report.json").write_text(
        json.dumps({"matrix_id": "m_ident", "declared_cells": 1}), encoding="utf-8"
    )
    payload = finalize_matrix(matrix_dir, registry_env)
    assert payload["final_verdict"] == "FAIL"
    assert any(m.startswith("artifact_identity_mismatch:") for m in payload["mismatches"])


def test_registry_duplicate_cell_identity_fails_closed(tmp_path, registry_env):
    matrix_dir = _build_diagnostic_style_matrix(tmp_path, "m_regdup", cells=1)
    _append_rows(
        registry_env,
        [
            {"experiment_id": "XSECT-0-DIAG", "verdict": "REJECTED",
             "kind": "CELL_RESULT", "schema": "v3", "matrix_id": "m_regdup"},
            {"experiment_id": "XSECT-0-DIAG", "verdict": "REJECTED",
             "kind": "DIAGNOSTIC_RECALC", "schema": "v5",
             "source_trial_experiment_id": "T0", "matrix_id": "m_regdup"},
        ],
    )
    payload = finalize_matrix(matrix_dir, registry_env)
    assert payload["counts"]["registry_cell_identity_entries"] == 2
    assert payload["final_verdict"] == "FAIL"
    assert any(m.startswith("registry_duplicate_identity:XSECT-0-DIAG") for m in payload["mismatches"])


def test_verification_kind_repeats_are_not_cell_duplication(tmp_path, registry_env):
    matrix_dir = _build_diagnostic_style_matrix(tmp_path, "m_verify_ok", cells=1)
    _append_rows(
        registry_env,
        [
            {"experiment_id": f"RERUN-{i}", "verdict": "PASS",
             "kind": "INDEPENDENT_RERUN_VERIFY", "schema": "v5",
             "matrix_id": "m_verify_ok", "verified_experiment_id": "XSECT-0-DIAG",
             "verification_type": "POSITIONS_DIGEST_PNL"}
            for i in range(3)
        ],
    )
    payload = finalize_matrix(matrix_dir, registry_env)
    assert not any(m.startswith("registry_duplicate_identity") for m in payload["mismatches"])
    assert payload["counts"]["registry_verification_entries"] == 3


def test_counts_derived_from_final_index_not_stale_report(tmp_path, registry_env):
    matrix_dir = _build_diagnostic_style_matrix(
        tmp_path, "m_stale", cells=1, declared=7
    )
    payload = finalize_matrix(matrix_dir, registry_env)
    assert payload["counts"]["indexed_cells"] == 1
    assert payload["counts"]["completed"] == 1
    assert payload["counts"]["declared_cells"] == 7
    assert any(
        m.startswith("indexed_cells(1)!=declared_cells(7)") for m in payload["mismatches"]
    )
    assert payload["final_verdict"] == "PARTIAL"


# --------------------------- D3 negative fixtures ---------------------------- #

LEDGER_ROWS = [
    {"canonical_pnl": 10.0},
    {"canonical_pnl": -2.0},
]


def _build_finalized_exp_dir(tmp_path: Path, name: str = "EXP-XG2A") -> Path:
    exp_dir = tmp_path / name
    exp_dir.mkdir()
    (exp_dir / "cell.json").write_text(json.dumps({"experiment_id": name}), encoding="utf-8")
    (exp_dir / "positions.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in LEDGER_ROWS), encoding="utf-8"
    )
    (exp_dir / "funding_cashflows.jsonl").write_text(
        json.dumps({"funding_net": -0.5}) + "\n", encoding="utf-8"
    )
    (exp_dir / "costs.jsonl").write_text(
        json.dumps({"commission": 0.3, "modeled_slippage": 0.1}) + "\n", encoding="utf-8"
    )
    (exp_dir / "accounting_reconciliation.json").write_text(json.dumps({
        "positions_total_pnl": 8.0,
        "funding_total": -0.5,
        "commission_total": 0.3,
        "slippage_total": 0.1,
    }), encoding="utf-8")
    (exp_dir / "canonical_metrics.json").write_text(json.dumps({
        "net_canonical_pnl": 8.0, "trades": 2, "position_pf": 5.0,
    }), encoding="utf-8")
    (exp_dir / "gate_result.json").write_text(json.dumps({"rows": []}), encoding="utf-8")
    (exp_dir / "scorecard.json").write_text(json.dumps({"total": None}), encoding="utf-8")
    (exp_dir / "run.log").write_text("run complete\n", encoding="utf-8")
    finalize_directory_hashes(exp_dir)
    return exp_dir


def test_tampered_hashed_artifact_fails_xg2a(tmp_path):
    exp_dir = _build_finalized_exp_dir(tmp_path)
    target = exp_dir / "positions.jsonl"
    original = target.read_bytes()
    target.write_bytes(original.replace(b"10.0", b"11.0"))
    result = verify_experiment_dir(exp_dir, phase="final")
    assert result.verdict() is GateVerdict.FAIL
    assert result.hashes_match is False
    assert "artifact_hash_mismatch:positions.jsonl" in result.reasons


def test_post_hash_append_fails_freshness_measurement(tmp_path):
    exp_dir = _build_finalized_exp_dir(tmp_path)
    with (exp_dir / "run.log").open("a", encoding="utf-8") as handle:
        handle.write("smuggled post-hash line\n")
    result = verify_experiment_dir(exp_dir, phase="final")
    assert result.verdict() is GateVerdict.FAIL
    assert "artifact_hashes_stale:run.log" in result.reasons


def test_corrupted_ledger_digest_fails_accounting_only(tmp_path):
    exp_dir = _build_finalized_exp_dir(tmp_path)
    # Corrupt the position PnL digest source, then RE-hash: only the ledger
    # reconciliation may fail, proving it is measured from real rows.
    target = exp_dir / "positions.jsonl"
    target.write_text(
        "".join(json.dumps(r) + "\n" for r in [{"canonical_pnl": 99.0}, LEDGER_ROWS[1]]),
        encoding="utf-8",
    )
    finalize_directory_hashes(exp_dir)
    result = verify_experiment_dir(exp_dir, phase="final")
    assert result.hashes_match is True
    assert result.positions_reconcile is False
    assert "accounting_reconcile_fail:positions_total_pnl" in result.reasons
    assert result.verdict() is GateVerdict.FAIL


def test_unlisted_file_escapes_hash_manifest(tmp_path):
    exp_dir = _build_finalized_exp_dir(tmp_path)
    (exp_dir / "smuggled.json").write_text("{}", encoding="utf-8")
    result = verify_experiment_dir(exp_dir, phase="final")
    assert result.verdict() is GateVerdict.FAIL
    assert "unlisted_artifact_file:smuggled.json" in result.reasons


def test_measured_integrity_fields_stay_distinct_not_collapsed_true(tmp_path):
    exp_dir = _build_finalized_exp_dir(tmp_path)
    # Tamper a non-ledger artifact post-hash: schema stays valid, hashes and
    # freshness break, ledgers still reconcile -- each field stays honest.
    (exp_dir / "canonical_metrics.json").write_text(json.dumps({
        "net_canonical_pnl": 8.0, "trades": 3, "position_pf": 5.0,
    }), encoding="utf-8")
    result = verify_experiment_dir(exp_dir, phase="final")
    assert result.schema_valid is True
    assert result.hashes_match is False
    assert result.positions_reconcile is True
    assert result.report_index_reconcile is False
    assert "artifact_hash_mismatch:canonical_metrics.json" in result.reasons
    assert result.verdict() is GateVerdict.FAIL


CLEAN_XG1_ROWS = [
    {"signal_ts": 1000, "fill_ts": 2000},
    {"signal_ts": 1500, "fill_ts": 2500},
]
CLEAN_TRANSFORM_REGISTRY = {"learned_scale": {"status": "fitted", "fit_on": "train"}}
CLEAN_WARMUP = {"warmup_start": "2026-01-01", "scored_start": "2026-02-01",
                "scored_end": "2026-03-01"}


def test_xg1_measured_pass_fail_and_missing_verdicts_distinct():
    clean = evaluate_xg1_measured(
        CLEAN_XG1_ROWS,
        transform_registry=CLEAN_TRANSFORM_REGISTRY,
        warmup_boundaries=CLEAN_WARMUP,
    )
    assert clean.verdict is GateVerdict.PASS

    tampered = [dict(CLEAN_XG1_ROWS[0]), {**CLEAN_XG1_ROWS[1], "fill_ts": 1000}]
    violated = evaluate_xg1_measured(
        tampered,
        transform_registry=CLEAN_TRANSFORM_REGISTRY,
        warmup_boundaries=CLEAN_WARMUP,
    )
    assert violated.verdict is GateVerdict.FAIL

    missing = evaluate_xg1_measured(None)
    empty = evaluate_xg1_measured([])
    assert missing.verdict is GateVerdict.INCONCLUSIVE
    assert "evidence_missing" in missing.reasons
    assert empty.verdict is GateVerdict.INCONCLUSIVE

    assert len({clean.verdict, violated.verdict, missing.verdict}) == 3


def test_xg2b_reproduction_verdicts_stay_distinct():
    not_tested = IndependentReproductionResult(
        performed=False, rerun_process_separate=False,
        parameters_match=None, positions_digest_match=None,
        trade_count_match=None, canonical_pnl_match=None,
    )
    assert not_tested.verdict() is GateVerdict.NOT_YET_TESTED

    def _repro(**overrides):
        base = dict(
            performed=True, rerun_process_separate=True,
            parameters_match=True, positions_digest_match=True,
            trade_count_match=True, canonical_pnl_match=True,
        )
        return IndependentReproductionResult(**{**base, **overrides})

    assert _repro().verdict() is GateVerdict.PASS
    assert _repro(canonical_pnl_match=False).verdict() is GateVerdict.FAIL
    assert _repro(parameters_match=None).verdict() is GateVerdict.INCONCLUSIVE


def test_owned_gate_paths_contain_no_prebuilt_true_integrity():
    pattern = re.compile(
        r"(schema_valid|hashes_match|positions_reconcile|report_index_reconcile)"
        r"\s*=\s*True\b"
    )
    for source in (
        Path("research/reconciliation.py"),
        Path("research/protocol/reconciliation.py"),
    ):
        assert not pattern.search(source.read_text(encoding="utf-8")), source


def test_synthetic_all_true_integrity_is_detectably_different_from_measured(tmp_path):
    exp_dir = _build_finalized_exp_dir(tmp_path)
    (exp_dir / "costs.jsonl").write_text(
        json.dumps({"commission": 9.9, "modeled_slippage": 0.1}) + "\n", encoding="utf-8"
    )
    measured = verify_experiment_dir(exp_dir, phase="final")
    synthetic = ArtifactIntegrityResult(
        schema_valid=True, hashes_match=True,
        positions_reconcile=True, report_index_reconcile=True,
    )
    assert synthetic.verdict() is GateVerdict.PASS
    assert measured.positions_reconcile is False
    assert "accounting_reconcile_fail:commission_total" in measured.reasons
    assert measured.verdict() is GateVerdict.FAIL
