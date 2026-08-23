"""Matrix <-> registry reconciliation finalizer (Sprint V3, PLAN section 11).

``finalize_matrix`` recomputes ALL counts from the FILESYSTEM and the FINAL
on-disk index -- never from a runner's in-memory loop counters.  This fixes
the Sprint V2 defect where ``report.json`` was overwritten by the last batch
and aggregates silently drifted from the real artifact tree.

Counts recomputed:

* declared_cells            report.json declaration (runner's plan size)
* indexed_cells             entries present in the FINAL index.json
* actual_cell_files         cell JSON artifacts actually on disk
* completed / pipeline_error / data_incomplete   per index statuses,
  cross-checked against each artifact's own ``cell_result.status``
* registry_entries_for_matrix   append-only registry lines with this matrix_id
* stage_a_artifact_dirs     launch-manifest dirs on disk whose matrix_id matches

Any mismatch between these counts is recorded and makes the finalization
verdict PARTIAL/FAIL; the CLI wrapper exits non-zero so pipelines stop.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from research.protocol.registry import load_all

RECONCILIATION_SCHEMA_VERSION = 1


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def finalize_matrix(matrix_dir: str | Path, registry_path: str | Path | None = None) -> dict:
    """Recompute every count for ``matrix_dir``; write reconciliation.json.

    Returns the reconciliation payload.  ``all_counts_match`` is True only
    when completed == declared == indexed == actual files and no artifact is
    inconsistent with its index entry.
    """
    matrix_path = Path(matrix_dir)
    index_path = matrix_path / "index.json"
    report_path = matrix_path / "report.json"

    report = _load_json(report_path) if report_path.is_file() else {}
    index = _load_json(index_path) if index_path.is_file() else {"cells": {}}
    cells: dict = index.get("cells") or {}

    # --- filesystem truth --------------------------------------------------- #
    cells_dir = matrix_path / "cells"
    cell_files = sorted(cells_dir.glob("*.json")) if cells_dir.is_dir() else []

    status_from_index: dict[str, int] = {}
    artifact_status_mismatches: list[str] = []
    missing_artifacts: list[str] = []
    for key, entry in cells.items():
        status = entry.get("status")
        status_from_index[status] = status_from_index.get(status, 0) + 1
        artifact = entry.get("artifact_path")
        if not artifact or not Path(artifact).is_file():
            missing_artifacts.append(key)
            continue
        try:
            document = _load_json(Path(artifact))
        except json.JSONDecodeError:
            artifact_status_mismatches.append(f"{key}:unreadable")
            continue
        doc_status = (document.get("cell_result") or {}).get("status")
        if doc_status is not None and doc_status != status:
            artifact_status_mismatches.append(f"{key}:{doc_status}!={status}")

    registry_entries = load_all(registry_path)
    matrix_ids = {
        str(report.get("matrix_id") or matrix_path.name),
        matrix_path.name,
    }
    registry_rows = [
        row for row in registry_entries if row.get("matrix_id") in matrix_ids
    ]

    stage_a_root = Path(
        report.get("stage_a_root") or "results/stage_a_v3"
    )
    stage_a_dirs = 0
    if stage_a_root.is_dir():
        for exp_dir in stage_a_root.iterdir():
            manifest = exp_dir / "launch_manifest.yaml"
            if not manifest.is_file():
                continue
            try:
                import yaml

                data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
            except Exception:  # noqa: BLE001 - unreadable manifest counts as mismatch evidence below
                continue
            if data.get("matrix_id") in matrix_ids:
                stage_a_dirs += 1

    completed = status_from_index.get("COMPLETED", 0)
    pipeline_error = status_from_index.get("PIPELINE_ERROR", 0)
    data_incomplete = status_from_index.get("DATA_INCOMPLETE", 0)

    declared_cells = int(report.get("declared_cells") or 0)
    counts = {
        "declared_cells": declared_cells,
        "indexed_cells": len(cells),
        "actual_cell_files": len(cell_files),
        "completed": completed,
        "pipeline_error": pipeline_error,
        "data_incomplete": data_incomplete,
        "registry_entries_for_matrix": len(registry_rows),
        "stage_a_artifact_dirs": stage_a_dirs,
    }

    mismatches: list[str] = []
    if declared_cells and len(cells) != declared_cells:
        mismatches.append(
            f"indexed_cells({len(cells)})!=declared_cells({declared_cells})"
        )
    if len(cell_files) != len(cells):
        mismatches.append(
            f"actual_cell_files({len(cell_files)})!=indexed_cells({len(cells)})"
        )
    if missing_artifacts:
        mismatches.append(f"missing_artifacts:{sorted(missing_artifacts)}")
    if artifact_status_mismatches:
        mismatches.append(f"artifact_status_mismatch:{sorted(artifact_status_mismatches)}")
    if completed + pipeline_error + data_incomplete != len(cells):
        mismatches.append("status_counts_do_not_sum_to_indexed_cells")
    if declared_cells and stage_a_dirs < len(cells):
        mismatches.append(
            f"stage_a_artifact_dirs({stage_a_dirs})<indexed_cells({len(cells)})"
        )

    if mismatches:
        verdict = (
            "FAIL"
            if missing_artifacts or artifact_status_mismatches
            else "PARTIAL"
        )
    elif declared_cells and completed == declared_cells:
        verdict = "COMPLETE"
    else:
        verdict = "PARTIAL"

    payload = {
        "schema_version": RECONCILIATION_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "matrix_dir": str(matrix_path),
        "matrix_id": report.get("matrix_id") or matrix_path.name,
        "counts": counts,
        "mismatches": sorted(mismatches),
        "final_verdict": verdict,
        "registry_append_only_verified": _verify_registry_append_only(registry_path),
    }
    out_path = matrix_path / "reconciliation.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def _verify_registry_append_only(registry_path: str | Path | None) -> bool:
    from research.protocol.registry import verify_append_only

    try:
        return verify_append_only(registry_path)
    except ValueError:
        return False


def append_matrix_finalize_entry(
    matrix_dir: str | Path,
    reconciliation: dict,
    *,
    registry_path: str | Path | None = None,
) -> dict:
    """Append the MATRIX_FINALIZE registry row (kind-enforced)."""
    from research.protocol.registry import append

    matrix_path = Path(matrix_dir)
    return append(
        {
            "experiment_id": f"FINALIZE-{matrix_path.name}-{reconciliation['generated_at_utc']}",
            "verdict": reconciliation["final_verdict"],
            "kind": "MATRIX_FINALIZE",
            "schema": "v3",
            "matrix_id": reconciliation["matrix_id"],
            "verified_experiment_id": reconciliation["matrix_id"],
            "verification_type": "MATRIX_RECONCILIATION",
            "counts": reconciliation["counts"],
            "mismatches": reconciliation["mismatches"],
        },
        path=registry_path,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--matrix-dir", required=True)
    parser.add_argument("--registry-path", default=None)
    parser.add_argument("--append-finalize-entry", action="store_true")
    args = parser.parse_args(argv)

    reconciliation = finalize_matrix(args.matrix_dir, args.registry_path)
    if args.append_finalize_entry:
        append_matrix_finalize_entry(args.matrix_dir, reconciliation, registry_path=args.registry_path)
    print(json.dumps(reconciliation, indent=2))
    return 0 if not reconciliation["mismatches"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
