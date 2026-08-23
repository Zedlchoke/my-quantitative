"""Independent rerun harness (G2 reproducibility).

``reproduce_from_manifest`` reloads the experiment config, recomputes the
config SHA-256, re-runs a single-symbol/fold walk-forward cell via
``research.baseline_wf.run_walkforward`` and compares against the original
metrics recorded in the append-only registry:

* config hash equality                 -> else reason ``hash_mismatch``
* trades count equality                -> else ``rerun_positions_mismatch``
* net canonical PnL within relative tolerance 1e-6 -> else
  ``rerun_pnl_mismatch``
* deterministic summary digest equality -> else ``rerun_positions_mismatch``

The original entry must carry a ``canonical`` block::

    {"trades": int, "net_canonical_pnl": float,
     "positions_digest": <digest_from_wf_summary(original_summary)>}

Digest note: until per-fill digests are exposed by the runner, the digest is
the canonical JSON hash of the walk-forward ``cells`` table, which is stable
and deterministic for an identical rerun.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from contracts.protocol import (
    GateId,
    GateResult,
    GateVerdict,
    canonical_json,
    sha256_file,
    sha256_text,
)
from research.baseline_wf import run_walkforward as _run_walkforward
from research.protocol.manifest import ManifestSpec, read_manifest
from research.protocol.registry import DEFAULT_REGISTRY_PATH, load_all

REL_TOLERANCE = 1e-6


def digest_from_wf_summary(summary: dict) -> str:
    """Deterministic digest of a walk-forward summary's cells table."""
    payload = {
        "cells": summary.get("cells", []),
        "strategy_type": summary.get("strategy_type"),
        "symbols": summary.get("symbols"),
        "folds": summary.get("folds"),
    }
    return sha256_text(canonical_json(payload))


def summarize_wf_metrics(summary: dict) -> tuple[int, float]:
    """Return (trades, net pnl after funding) summed over walk-forward cells."""
    cells = summary.get("cells", [])
    trades = sum(int(cell.get("trades", 0) or 0) for cell in cells)
    pnl_values = [
        float(cell["pnl_after_funding"])
        if cell.get("pnl_after_funding") is not None
        else float(cell.get("pnl", 0.0) or 0.0)
        for cell in cells
    ]
    return trades, math.fsum(pnl_values)


def build_registry_entry(
    experiment_id: str,
    verdict: str,
    *,
    symbol: str,
    wf_summary: dict,
    extra: dict | None = None,
) -> dict:
    """Registry-ready entry with the ``canonical`` block filled from a run."""
    trades, pnl = summarize_wf_metrics(wf_summary)
    payload = {
        "experiment_id": experiment_id,
        "verdict": verdict,
        "symbol": symbol,
        "canonical": {
            "trades": trades,
            "net_canonical_pnl": pnl,
            "positions_digest": digest_from_wf_summary(wf_summary),
        },
    }
    if extra:
        payload.update(extra)
    return payload


def _within_relative_tolerance(actual: float, expected: float, tol: float) -> bool:
    scale = max(abs(expected), abs(actual), 1.0)
    return abs(actual - expected) <= tol * scale


def _find_registry_entry(experiment_id: str, registry_path: Path | None) -> dict | None:
    matches = [
        entry
        for entry in load_all(registry_path)
        if entry.get("experiment_id") == experiment_id
    ]
    return matches[-1] if matches else None


def reproduce_from_manifest(
    manifest_path: str | Path,
    workdir: str | Path = ".",
    *,
    registry_path: str | Path | None = None,
    runner=None,
) -> GateResult:
    """Re-run the experiment referenced by ``manifest_path`` and judge G2."""
    manifest: ManifestSpec = read_manifest(manifest_path)
    reasons: list[str] = []

    config_path = Path(manifest.config_path)
    if not config_path.exists() or sha256_file(config_path) != manifest.config_sha256:
        reasons.append("hash_mismatch")

    registry_file = Path(registry_path) if registry_path is not None else DEFAULT_REGISTRY_PATH
    entry = _find_registry_entry(manifest.experiment_id, registry_file)
    canonical = entry.get("canonical") if entry else None
    required_keys = {"trades", "net_canonical_pnl", "positions_digest"}
    if not isinstance(canonical, dict) or not required_keys.issubset(canonical):
        return GateResult(
            GateId.G2_REPRODUCIBILITY,
            GateVerdict.NOT_YET_TESTED,
            ("metric_not_computed",),
        )

    symbol = entry.get("symbol")
    if not symbol:
        token = str(manifest.common_intersection).replace(",", " ").split()
        symbol = token[0] if token else None
    if not symbol:
        return GateResult(
            GateId.G2_REPRODUCIBILITY,
            GateVerdict.NOT_YET_TESTED,
            ("metric_not_computed",),
        )

    workdir_path = Path(workdir)
    workdir_path.mkdir(parents=True, exist_ok=True)
    output_path = workdir_path / f"reproduce_{manifest.experiment_id}.json"

    run = runner or _run_walkforward
    summary = run(
        str(config_path),
        manifest.strategy_type,
        (str(symbol),),
        1,
        str(output_path),
    )
    if isinstance(summary, str):
        summary = json.loads(Path(summary).read_text(encoding="utf-8"))

    rerun_trades, rerun_pnl = summarize_wf_metrics(summary)
    rerun_digest = digest_from_wf_summary(summary)

    if int(canonical["trades"]) != rerun_trades:
        reasons.append("rerun_positions_mismatch")
    if not _within_relative_tolerance(
        rerun_pnl, float(canonical["net_canonical_pnl"]), REL_TOLERANCE
    ):
        reasons.append("rerun_pnl_mismatch")
    if str(canonical["positions_digest"]) != rerun_digest:
        reasons.append("rerun_positions_mismatch")

    if reasons:
        return GateResult(
            GateId.G2_REPRODUCIBILITY, GateVerdict.FAIL, tuple(dict.fromkeys(reasons))
        )
    return GateResult(GateId.G2_REPRODUCIBILITY, GateVerdict.PASS)
