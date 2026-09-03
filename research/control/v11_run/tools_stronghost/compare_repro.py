"""V11 Phase R — reproduction comparator (A1).

Compares exec-tree scored cell artifacts against repro-tree re-executions.
FROZEN NORMALISATION RULE (recorded before any reproduction run, per PLAN 15):
the only permitted byte difference is each tree's own absolute root path,
normalised by replacing the tree root string with the placeholder
``<TREE_ROOT>`` in every compared JSON payload (recursive, string values).
Everything else must match exactly (matrix digest, per-run hashes, canonical
artifact contents).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(r"C:\Users\ROYAL\my-quantitative")
EXEC = REPO / ".worktrees/v11/exec-v11-1"
REPRO = REPO / ".worktrees/v11/repro-v11-1"
PHASE = "results/v11_phase_e"


def norm(value, root: Path):
    if isinstance(value, str):
        return value.replace(str(root), "<TREE_ROOT>").replace(str(root).replace("\\", "/"), "<TREE_ROOT>")
    if isinstance(value, list):
        return [norm(v, root) for v in value]
    if isinstance(value, dict):
        return {k: norm(v, root) for k, v in value.items()}
    return value


def compare_arm(family: str, arm: str) -> dict:
    a_root = EXEC / PHASE / family / arm
    r_root = REPRO / PHASE / family / arm
    out = {"family": family, "arm": arm, "cells": {}, "matrix_digest": None}
    a_summary = json.load(open(a_root / "matrix_summary.json"))
    out["matrix_digest_exec"] = a_summary.get("matrix_digest")
    all_match = True
    for cell in a_summary["matrix_cells"]:
        a_art = json.load(open(a_root / "matrix" / cell / "results" / "artifact.json"))
        r_art = json.load(open(r_root / "matrix" / cell / "results" / "artifact.json"))
        a_hash = a_art["hashes"]["result_sha256"]
        r_hash = r_art["hashes"]["result_sha256"]
        norm_equal = norm(a_art, EXEC) == norm(r_art, REPRO)
        out["cells"][cell] = {"result_sha256_exec": a_hash, "result_sha256_repro": r_hash, "norm_equal": norm_equal}
        all_match = all_match and (a_hash == r_hash) and norm_equal
    out["all_match"] = all_match
    return out


if __name__ == "__main__":
    family = sys.argv[1]
    arms = sys.argv[2:]
    results = [compare_arm(family, arm) for arm in arms]
    print(json.dumps({"schema": "v11_reproduction_report_v1", "family": family,
                      "arms": results,
                      "verdict": "ALL_MATCH" if all(r["all_match"] for r in results) else "MISMATCH"}, indent=1))
