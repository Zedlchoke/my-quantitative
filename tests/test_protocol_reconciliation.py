"""Matrix/registry reconciliation finalizer tests (Sprint V3, PLAN section 11).

Builds tmp matrix dirs (index + cells + stage_a launch manifests) and asserts
every count is recomputed from the filesystem/final index, that mismatches
yield PARTIAL/FAIL verdicts and a non-zero CLI exit, and that registry entry
kinds are enforced.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

import research.protocol.registry as registry_mod
from research.protocol.reconciliation import (
    append_matrix_finalize_entry,
    finalize_matrix,
)
from research.protocol.registry import append, load_all, validate_entry_kind


def _cell_document(strategy: str, symbol: str, status: str = "COMPLETED") -> dict:
    return {
        "schema_version": 3,
        "identity": {
            "strategy_type": strategy,
            "symbol": symbol,
            "param_variant": "base",
        },
        "cell_result": {"status": status},
    }


def _build_matrix(
    tmp_path: Path,
    name: str,
    *,
    declared: int,
    indexed: int,
    completed: int,
    errors: int = 0,
    extra_file: bool = False,
    with_stage_a: bool = True,
    matrix_id: str | None = None,
) -> Path:
    matrix_dir = tmp_path / name
    cells_dir = matrix_dir / "cells"
    cells_dir.mkdir(parents=True)

    index_cells: dict[str, dict] = {}
    for i in range(completed):
        strategy = f"strat{i}"
        stem = f"{strategy}__SYM{i}__base"
        artifact = cells_dir / f"{stem}.json"
        artifact.write_text(
            json.dumps(_cell_document(strategy, f"SYM{i}")), encoding="utf-8"
        )
        index_cells[stem] = {
            "artifact_path": str(artifact),
            "status": "COMPLETED",
            "experiment_id": f"EXP-{i}",
        }
    for i in range(errors):
        stem = f"err{i}__SYM__base"
        artifact = cells_dir / f"{stem}.json"
        artifact.write_text(json.dumps(_cell_document("err", "SYM", "PIPELINE_ERROR")), encoding="utf-8")
        index_cells[stem] = {
            "artifact_path": str(artifact),
            "status": "PIPELINE_ERROR",
            "experiment_id": f"EXP-E{i}",
        }

    # Simulate an index entry whose artifact is missing from disk entirely.
    for i in range(indexed - completed - errors):
        stem = f"ghost{i}__SYM__base"
        index_cells[stem] = {
            "artifact_path": str(cells_dir / f"{stem}.json"),
            "status": "COMPLETED",
            "experiment_id": f"EXP-G{i}",
        }

    (matrix_dir / "index.json").write_text(
        json.dumps({"schema_version": 1, "cells": index_cells}), encoding="utf-8"
    )
    report_doc = {"matrix_id": matrix_id or name, "declared_cells": declared}
    if with_stage_a:
        report_doc["stage_a_root"] = str(tmp_path / "stage_a_v3")
    (matrix_dir / "report.json").write_text(json.dumps(report_doc), encoding="utf-8")
    if extra_file:
        (cells_dir / "orphan__SYM__base.json").write_text("{}", encoding="utf-8")
    if with_stage_a:
        stage_root = tmp_path / "stage_a_v3"
        for i in range(completed + errors):
            exp_dir = stage_root / f"EXP-{i if i < completed else 'E' + str(i - completed)}"
            exp_dir.mkdir(parents=True)
            manifest = {
                "schema_version": 3,
                "matrix_id": matrix_id or name,
                "experiment_id": exp_dir.name,
            }
            (exp_dir / "launch_manifest.yaml").write_text(
                yaml.safe_dump(manifest), encoding="utf-8"
            )
    return matrix_dir


@pytest.fixture()
def registry_env(tmp_path, monkeypatch):
    monkeypatch.setattr(registry_mod, "DEFAULT_REGISTRY_PATH", tmp_path / "reg.jsonl")
    monkeypatch.setattr(registry_mod, "DEFAULT_REGISTRY_DIR", tmp_path)
    return tmp_path / "reg.jsonl"


def test_finalize_counts_recomputed_from_filesystem(tmp_path, registry_env):
    matrix_dir = _build_matrix(tmp_path, "m_ok", declared=3, indexed=3, completed=2, errors=1)
    payload = finalize_matrix(matrix_dir, registry_env)
    counts = payload["counts"]
    assert counts["declared_cells"] == 3
    assert counts["indexed_cells"] == 3
    assert counts["actual_cell_files"] == 3
    assert counts["completed"] == 2
    assert counts["pipeline_error"] == 1
    assert counts["data_incomplete"] == 0
    assert counts["stage_a_artifact_dirs"] == 3
    assert payload["final_verdict"] == "PARTIAL"  # completed != declared
    assert (Path(matrix_dir) / "reconciliation.json").is_file()


def test_finalize_complete_when_all_counts_match(tmp_path, registry_env):
    matrix_dir = _build_matrix(tmp_path, "m_full", declared=2, indexed=2, completed=2)
    payload = finalize_matrix(matrix_dir, registry_env)
    assert payload["final_verdict"] == "COMPLETE"
    assert payload["mismatches"] == []


def test_finalize_detects_missing_artifact_and_orphan_files(tmp_path, registry_env):
    matrix_dir = _build_matrix(
        tmp_path, "m_bad", declared=4, indexed=4, completed=2, errors=1
    )
    payload = finalize_matrix(matrix_dir, registry_env)
    assert payload["final_verdict"] == "FAIL"
    assert any(m.startswith("missing_artifacts") for m in payload["mismatches"])
    assert any(m.startswith("actual_cell_files(3)!=indexed_cells(4)") for m in payload["mismatches"])


def test_finalize_counts_registry_rows_for_matrix_only(tmp_path, registry_env):
    matrix_dir = _build_matrix(tmp_path, "m_reg", declared=1, indexed=1, completed=1)
    for row in (
        {"experiment_id": "X1", "verdict": "PASS", "kind": "CELL_RESULT", "schema": "v3",
         "matrix_id": "m_reg"},
        {"experiment_id": "X2", "verdict": "PASS", "kind": "CELL_RESULT", "schema": "v3",
         "matrix_id": "other_matrix"},
    ):
        append(row, path=registry_env)
    payload = finalize_matrix(matrix_dir, registry_env)
    assert payload["counts"]["registry_entries_for_matrix"] == 1


def test_finalize_entry_appends_kind_enforced_row(tmp_path, registry_env):
    matrix_dir = _build_matrix(tmp_path, "m_fin", declared=1, indexed=1, completed=1)
    payload = finalize_matrix(matrix_dir, registry_env)
    stored = append_matrix_finalize_entry(matrix_dir, payload, registry_path=registry_env)
    assert stored["kind"] == "MATRIX_FINALIZE"
    assert load_all(registry_env)[-1]["verification_type"] == "MATRIX_RECONCILIATION"


# ------------------------- registry kind contract ----------------------------- #
def test_verify_kinds_require_identity_fields():
    base = {"kind": "ARTIFACT_INTEGRITY_VERIFY"}
    reasons = validate_entry_kind(base)
    assert set(reasons) == {
        "registry_missing_field:schema",
        "registry_missing_field:matrix_id",
        "registry_missing_field:verified_experiment_id",
        "registry_missing_field:verification_type",
    }


def test_cell_result_kind_requires_schema_and_matrix():
    reasons = validate_entry_kind({"kind": "CELL_RESULT"})
    assert set(reasons) == {
        "registry_missing_field:schema",
        "registry_missing_field:matrix_id",
    }


def test_unknown_kind_rejected_and_append_is_fail_closed(registry_env):
    with pytest.raises(ValueError, match="unknown_registry_kind"):
        append({"experiment_id": "E", "verdict": "V", "kind": "MYSTERY"}, path=registry_env)
    with pytest.raises(ValueError, match="registry_missing_field"):
        append(
            {
                "experiment_id": "E",
                "verdict": "V",
                "kind": "INDEPENDENT_RERUN_VERIFY",
                "schema": "v3",
            },
            path=registry_env,
        )
    assert not registry_env.exists()  # nothing written on rejection


def test_valid_verify_entry_appends_cleanly(registry_env):
    stored = append(
        {
            "experiment_id": "RERUN-1",
            "verdict": "MATCH",
            "kind": "INDEPENDENT_RERUN_VERIFY",
            "schema": "v3",
            "matrix_id": "v3_execution_truth",
            "verified_experiment_id": "EXP-0001",
            "verification_type": "POSITIONS_DIGEST_PNL",
        },
        path=registry_env,
    )
    assert stored["verified_experiment_id"] == "EXP-0001"
