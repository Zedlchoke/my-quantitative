"""Matrix <-> registry reconciliation finalizer (Sprint V3, PLAN section 11).

``finalize_matrix`` recomputes ALL counts from the FILESYSTEM and the FINAL
on-disk index -- never from a runner's in-memory loop counters.  This fixes
the Sprint V2 defect where ``report.json`` was overwritten by the last batch
and aggregates silently drifted from the real artifact tree.

Schema version 2 (PLAN section 8-D2) field meanings:

* declared_cells            report.json declaration (runner's plan size)
* indexed_cells             entries present in the FINAL index.json
* actual_cell_files         cell JSON artifacts actually on disk
* completed / pipeline_error / data_incomplete   per index statuses,
  cross-checked against each artifact's own ``cell_result.status``
* registry_entries_for_matrix   append-only registry lines with this matrix_id
* registry_cell_identity_entries  subset whose ``kind`` claims a cell result
  identity (CELL_RESULT / DIAGNOSTIC_RECALC); these must be UNIQUE per
  experiment_id -- two rows for one identity are real duplication (FAIL),
  while verification kinds (INDEPENDENT_RERUN_VERIFY, MATRIX_FINALIZE,
  ARTIFACT_INTEGRITY_VERIFY) are separate records counted apart
* registry_verification_entries   remaining verification-kind rows
* stage_a_artifact_dirs     distinct launch-manifest dirs whose matrix_id
  matches: union of the resolved stage_a root scan AND every indexed cell's
  own declared/derived experiment dir, so DIAGNOSTIC_RECALC matrices whose
  artifacts live under a diagnostic output root are measured at their real
  location instead of the legacy default root
* stage_a_dirs_expected     indexed cells that reference an experiment dir

Identity/integrity validation added in v2 (each FAIL-level):

* one intended experiment identity per index cell (duplicate ids FAIL);
* artifact document experiment_id must equal its index entry's;
* referenced experiment dirs exist and contain a matching launch manifest;
* stage_a_dirs<referenced_exp_dirs stays a mismatch (never harmless).

Schema version 3 (PLAN section 6.4 item 8 / finding N12; owner A5) makes the
finalizer FAIL-CLOSED -- each condition below appends a FAIL-level mismatch
entry instead of being merely reported:

* ``registry_append_only_violation`` when registry_append_only_verified is
  False (an out-of-band rewrite of the registry poisons every count);
* ``stale_stage_a_root`` when report.json declares a stage_a_root that still
  exists but no longer matches this matrix's identity (it holds launch
  manifests for OTHER matrix ids while this matrix's real artifact dirs live
  elsewhere) -- e.g. a diagnostic matrix declaring the scored root;
* ``missing_required_artifacts:<cell>`` when an indexed experiment dir
  carries runner data artifacts but is missing required settlement/accounting
  or gate/metric files (the N06 defect class). A directory holding ONLY its
  launch manifest is treated as a bare stub and is not required to carry the
  full artifact set;
* ``transition_counts_disagree_with_index`` when the report's declared
  experiment list/count blocks disagree with the FINAL index.

The report is derived from the final on-disk index only.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from research.protocol.registry import load_all

# v3 (PLAN section 6.4 item 8 / N12): fail-closed reconciliation. Bumped
# from v2; see module docstring for the new FAIL-level conditions.
RECONCILIATION_SCHEMA_VERSION = 3

#: Registry kinds that claim a CELL result identity (uniqueness-enforced).
#: Verification/finalize kinds may legitimately reference the same matrix
#: multiple times and are never treated as cell duplication.
CELL_IDENTITY_KINDS = frozenset(("CELL_RESULT", "DIAGNOSTIC_RECALC"))

#: v3 (N12): artifact files every REAL runner experiment directory must
#: contain. The check applies only once a directory carries any data
#: artifact beyond its launch manifest (a bare manifest-only stub is not a
#: finalized experiment output); after that, the FULL set is required so a
#: partial settlement/accounting writer (finding N06) can never reconcile.
REQUIRED_EXPERIMENT_ARTIFACT_FILES: tuple[str, ...] = (
    "canonical_metrics.json",
    "gate_result.json",
    "scorecard.json",
    "signal_ranks.jsonl",
    "orders.jsonl",
    "positions.jsonl",
    "portfolio_ledger.jsonl",
    "funding_cashflows.jsonl",
    "terminal_positions.jsonl",
    "exposure_control.jsonl",
    "accounting_reconciliation.json",
    "commission_slippage.json",
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _manifest_matrix_id(manifest_path: Path) -> str | None:
    """matrix_id inside a launch manifest, or None when unreadable."""
    try:
        import yaml

        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    except Exception:  # noqa: BLE001 - unreadable manifest counts as mismatch evidence below
        return None
    value = data.get("matrix_id")
    return str(value) if value is not None else None


def finalize_matrix(
    matrix_dir: str | Path,
    registry_path: str | Path | None = None,
    *,
    stage_a_root: str | Path | None = None,
) -> dict:
    """Recompute every count for ``matrix_dir``; write reconciliation.json.

    Returns the reconciliation payload.  ``all_counts_match`` is True only
    when completed == declared == indexed == actual files, every indexed cell
    holds ONE experiment identity with consistent artifact references, and no
    artifact is inconsistent with its index entry.
    """
    matrix_path = Path(matrix_dir)
    index_path = matrix_path / "index.json"
    report_path = matrix_path / "report.json"

    # FINAL index on disk -- never a runner's last-batch counters.
    report = _load_json(report_path) if report_path.is_file() else {}
    index = _load_json(index_path) if index_path.is_file() else {"cells": {}}
    cells: dict = index.get("cells") or {}
    matrix_ids = {
        str(report.get("matrix_id") or matrix_path.name),
        matrix_path.name,
    }

    # --- filesystem truth --------------------------------------------------- #
    cells_dir = matrix_path / "cells"
    cell_files = sorted(cells_dir.glob("*.json")) if cells_dir.is_dir() else []

    status_from_index: dict[str, int] = {}
    artifact_status_mismatches: list[str] = []
    missing_artifacts: list[str] = []
    fail_mismatches: list[str] = []
    seen_experiment_ids: dict[str, str] = {}
    exp_refs: dict[str, Path] = {}
    checked_artifact_sets: set[Path] = set()
    dir_style_artifacts = 0

    for key, entry in cells.items():
        status = entry.get("status")
        status_from_index[status] = status_from_index.get(status, 0) + 1

        experiment_id = entry.get("experiment_id")
        if experiment_id:
            if experiment_id in seen_experiment_ids:
                fail_mismatches.append(
                    f"duplicate_experiment_identity:{experiment_id}:"
                    f"{seen_experiment_ids[experiment_id]}+{key}"
                )
            else:
                seen_experiment_ids[experiment_id] = key

        artifact = entry.get("artifact_path")
        artifact_path = Path(artifact) if artifact else None
        if artifact_path is None or not (
            artifact_path.is_file() or artifact_path.is_dir()
        ):
            missing_artifacts.append(key)
        elif artifact_path.is_file():
            try:
                document = _load_json(artifact_path)
            except json.JSONDecodeError:
                artifact_status_mismatches.append(f"{key}:unreadable")
                document = None
            if document is not None:
                doc_status = (document.get("cell_result") or {}).get("status")
                if doc_status is not None and doc_status != status:
                    artifact_status_mismatches.append(f"{key}:{doc_status}!={status}")
                doc_experiment_id = (document.get("cell_result") or {}).get(
                    "experiment_id"
                ) or (document.get("provenance") or {}).get("experiment_id")
                if (
                    experiment_id
                    and doc_experiment_id
                    and str(doc_experiment_id) != str(experiment_id)
                ):
                    fail_mismatches.append(
                        f"artifact_identity_mismatch:{key}:"
                        f"{doc_experiment_id}!={experiment_id}"
                    )
        else:
            dir_style_artifacts += 1

        # Referenced experiment dir: explicit declaration wins; otherwise a
        # directory-style artifact path IS the exp dir (DIAGNOSTIC_RECALC
        # matrices keep launch manifests inside the diagnostic output root).
        declared_dir = entry.get("stage_a_dir")
        candidate = Path(declared_dir) if declared_dir else (
            artifact_path if artifact_path is not None and artifact_path.is_dir() else None
        )
        if candidate is None:
            continue
        exp_refs[key] = candidate
        manifest = candidate / "launch_manifest.yaml"
        if not manifest.is_file():
            fail_mismatches.append(f"stage_a_dir_invalid:{key}:missing_launch_manifest")
        elif _manifest_matrix_id(manifest) not in matrix_ids:
            fail_mismatches.append(f"stage_a_dir_invalid:{key}:matrix_id_mismatch")

        # v3 (N12): a directory carrying ANY data artifact beyond its launch
        # manifest claims to be a finalized experiment output and must hold
        # the COMPLETE artifact set -- a partial settlement/accounting writer
        # (finding N06 class) can never reconcile. Bare manifest-only stubs
        # are exempt (they make no data claims).
        if candidate.is_dir() and candidate not in checked_artifact_sets:
            checked_artifact_sets.add(candidate)
            has_data_artifacts = any(
                child.name != "launch_manifest.yaml"
                for child in candidate.iterdir()
                if child.is_file()
            )
            if has_data_artifacts:
                # Identity-aware required set (still fail-closed): a dir that
                # carries the V6P portfolio markers declares the FULL portfolio
                # artifact contract, so a partial writer (N06 class) can never
                # reconcile. Legacy v3-style provenance dirs make no portfolio
                # claims; their integrity is attested by the launch-manifest
                # trio checks above.
                if ((candidate / "canonical_metrics.json").is_file()
                        or (candidate / "gate_result.json").is_file()):
                    missing_required = [
                        name for name in REQUIRED_EXPERIMENT_ARTIFACT_FILES
                        if not (candidate / name).is_file()
                    ]
                else:
                    missing_required = []
                if missing_required:
                    fail_mismatches.append(
                        f"missing_required_artifacts:{key}:{sorted(missing_required)}"
                    )

    registry_entries = load_all(registry_path)
    registry_rows = [
        row for row in registry_entries if row.get("matrix_id") in matrix_ids
    ]
    identity_rows = [
        row for row in registry_rows if row.get("kind") in CELL_IDENTITY_KINDS
    ]
    verification_rows = [
        row for row in registry_rows if row.get("kind") not in CELL_IDENTITY_KINDS
    ]
    duplicate_ids = sorted(
        experiment_id
        for experiment_id, count in Counter(
            str(row.get("experiment_id")) for row in identity_rows
        ).items()
        if count > 1
    )
    for experiment_id in duplicate_ids:
        fail_mismatches.append(f"registry_duplicate_identity:{experiment_id}")

    stage_root = Path(
        stage_a_root
        or report.get("stage_a_root")
        or (
            matrix_path.parents[1] / "stage_a_v3"
            if (matrix_path.parents[1] / "stage_a_v3").is_dir()
            else "results/stage_a_v3"
        )
    )
    stage_dirs: set[Path] = set()
    if stage_root.is_dir():
        for exp_dir in stage_root.iterdir():
            manifest = exp_dir / "launch_manifest.yaml"
            if manifest.is_file() and _manifest_matrix_id(manifest) in matrix_ids:
                stage_dirs.add(exp_dir.resolve())
    for key, candidate in exp_refs.items():
        manifest = candidate / "launch_manifest.yaml"
        if manifest.is_file() and _manifest_matrix_id(manifest) in matrix_ids:
            stage_dirs.add(candidate.resolve())

    completed = status_from_index.get("COMPLETED", 0)
    pipeline_error = status_from_index.get("PIPELINE_ERROR", 0)
    data_incomplete = status_from_index.get("DATA_INCOMPLETE", 0)

    # v3 (N12) stale-root detection: report.json declares stage_a_root that
    # still EXISTS but no longer matches this matrix's identity -- every
    # launch manifest under it belongs to OTHER matrix ids while this
    # matrix's real artifact dirs were found elsewhere. Classic case: a
    # diagnostic matrix still declaring ``results/portfolio_v4``.
    declared_root_raw = report.get("stage_a_root")
    if declared_root_raw and exp_refs:
        declared_root = Path(str(declared_root_raw))
        if declared_root.is_dir():
            declared_matches_any_matrix_manifest = any(
                (exp_dir / "launch_manifest.yaml").is_file()
                and _manifest_matrix_id(exp_dir / "launch_manifest.yaml") in matrix_ids
                for exp_dir in declared_root.iterdir()
            )
            declared_holds_this_matrix = any(
                d.is_relative_to(declared_root.resolve())
                for d in stage_dirs
            )
            if not declared_matches_any_matrix_manifest and not declared_holds_this_matrix:
                fail_mismatches.append(f"stale_stage_a_root:{declared_root}")

    # v3 (N12): transition/audit count blocks must agree with the FINAL index.
    report_experiments = report.get("experiments")
    if isinstance(report_experiments, list) and report_experiments:
        if set(map(str, report_experiments)) != set(cells):
            fail_mismatches.append(
                "transition_counts_disagree_with_index:"
                f"report_experiments({len(report_experiments)})!=indexed_cells({len(cells)})"
            )

    declared_cells = int(report.get("declared_cells") or 0)
    counts = {
        "declared_cells": declared_cells,
        "indexed_cells": len(cells),
        "actual_cell_files": len(cell_files),
        "completed": completed,
        "pipeline_error": pipeline_error,
        "data_incomplete": data_incomplete,
        "registry_entries_for_matrix": len(registry_rows),
        "registry_cell_identity_entries": len(identity_rows),
        "registry_verification_entries": len(verification_rows),
        "stage_a_artifact_dirs": len(stage_dirs),
        "stage_a_dirs_expected": len(exp_refs),
    }

    mismatches: list[str] = []
    if declared_cells and len(cells) != declared_cells:
        mismatches.append(
            f"indexed_cells({len(cells)})!=declared_cells({declared_cells})"
        )
    file_style_cells = len(cells) - dir_style_artifacts
    if len(cell_files) != file_style_cells:
        mismatches.append(
            f"actual_cell_files({len(cell_files)})!=indexed_cells({file_style_cells})"
        )
    if missing_artifacts:
        fail_mismatches.append(f"missing_artifacts:{sorted(missing_artifacts)}")

    # v3 (N12): append-only verification is FAIL-level. A registry whose
    # appended_at ordering breaks has been rewritten out-of-band; every
    # count derived from it is untrustworthy, so the finalizer fails closed.
    append_only_verified = _verify_registry_append_only(registry_path)
    if not append_only_verified:
        fail_mismatches.append("registry_append_only_violation")

    mismatches.extend(fail_mismatches)
    if artifact_status_mismatches:
        mismatches.append(f"artifact_status_mismatch:{sorted(artifact_status_mismatches)}")
    if completed + pipeline_error + data_incomplete != len(cells):
        mismatches.append("status_counts_do_not_sum_to_indexed_cells")
    if declared_cells and exp_refs and len(stage_dirs) < len(exp_refs):
        mismatches.append(
            f"stage_a_artifact_dirs({len(stage_dirs)})<indexed_cells({len(cells)})"
        )

    verdict = "FAIL" if fail_mismatches else "PARTIAL"
    if not mismatches:
        verdict = "COMPLETE" if (declared_cells and completed == declared_cells) else "PARTIAL"

    payload = {
        "schema_version": RECONCILIATION_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "matrix_dir": str(matrix_path),
        "matrix_id": report.get("matrix_id") or matrix_path.name,
        "counts": counts,
        "mismatches": sorted(mismatches),
        "final_verdict": verdict,
        "registry_append_only_verified": append_only_verified,
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
