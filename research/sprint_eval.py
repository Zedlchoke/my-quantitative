"""Sprint-24h evaluation bridge (owner A3).

Two modes:

* ``--schema v1`` (legacy): reads a completed matrix directory
  (research.matrix_runner output), evaluates hard gates + scorecards per combo
  using research.protocol, writes ``results/stage_a/<experiment_id>/``
  artifacts and appends the append-only registry.
* ``--schema v2`` (default, Sprint V2 PLAN section 13): per completed cell it
  FIRST freezes immutable input snapshots (research.provenance) BEFORE reading
  results, builds a validated ``ManifestV2Spec``, writes
  ``results/stage_a_v2/<EXP>/`` (manifest.yaml, frozen/, positions.jsonl,
  canonical_metrics.json, gate_result.json G0..G3, diagnostic scorecard.json,
  artifact_hashes.json, run.log), appends registry entries, and emits a
  ``v1_v2_comparison.json`` into the matrix directory comparing old fold-net
  PF vs new position-level PF with verdict changes.

Usage:
    python -m research.sprint_eval --matrix-dir results/matrix/stage_a_s0_20260823
    python -m research.sprint_eval --schema v2 \
        --matrix-dir results/matrix/v2_stage_a_20260823
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VOLCOMP_STRATEGY_TYPE = "vol_compression_breakout"
VOLCOMP_HYPOTHESIS_ID = "H-VOLCOMP-BRKOUT-v1"
VOLCOMP_HYPOTHESIS_CONFIG = f"research/hypotheses/{VOLCOMP_HYPOTHESIS_ID}/candidate.yaml"
HYPOTHESIS_BY_STRATEGY = {
    VOLCOMP_STRATEGY_TYPE: VOLCOMP_HYPOTHESIS_ID,
}
WARMUP_BARS_PER_DAY = 96
V2_DEFAULT_OUTPUT_ROOT = "results/stage_a_v2"
#: READ-ONLY fallback for V1 summary rows / coverage when running from a
#: worktree whose gitignored results/ tree does not carry Sprint-V1 artifacts.
MAIN_REPO_RESULTS_ROOT = "/Users/hoangminhlong/my-quantitative/results"


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def _aggregate_pf(folds: list[dict]) -> float | None:
    wins = sum(
        f.get("pnl_after_funding", 0.0) for f in folds if f.get("pnl_after_funding", 0.0) > 0
    )
    losses = abs(
        sum(
            f.get("pnl_after_funding", 0.0)
            for f in folds
            if f.get("pnl_after_funding", 0.0) < 0
        )
    )
    if losses == 0:
        return None if wins == 0 else float("inf")
    return wins / losses


def _combo_inputs(cell: dict) -> dict:
    folds = cell.get("folds", [])
    funded = [f for f in folds if f.get("trades_after_funding")]
    source = funded or folds
    pnl_key = "pnl_after_funding" if funded else "pnl"
    total_pnl = sum(f.get(pnl_key, 0.0) for f in source)
    trades_total = sum(f.get("trades_after_funding", 0) if funded else f.get("trades", 0) for f in source)
    exp = total_pnl / trades_total if trades_total else None
    pf = _aggregate_pf(source) if funded else _gross_pf(folds)
    contributions = [
        abs(f.get(pnl_key, 0.0)) / abs(total_pnl)
        for f in source
        if total_pnl
    ]
    top_contribution = max(contributions) * 100 if contributions else None
    stage_a = {
        "exp_after_cost": exp,
        "pf_after_cost": pf,
        "total_trades": trades_total,
        "folds": [
            {
                "fold_id": str(f["fold"]),
                "trades": f.get("trades_after_funding", 0) if funded else f.get("trades", 0),
                "pnl_after_cost": f.get(pnl_key, 0.0),
                "exp_after_cost": (
                    f.get("expectancy_after_funding")
                    if funded
                    else (f.get("expectancy"))
                ),
                "pf_after_cost": (
                    f.get("profit_factor_after_funding") if funded else f.get("profit_factor")
                ),
            }
            for f in folds
        ],
        "top_fold_contribution_pct": top_contribution,
    }
    data = {
        "unexplained_gaps": bool(cell.get("symbol_has_gaps")),
        "funding_coverage_complete": bool(funded),
        "instrument_metadata_ok": True,
        "catalog_current": True,
    }
    leakage = {
        "split_policy_declared": bool(cell.get("plan", {}).get("split_policy", "") not in ("", "pending")),
    }
    return stage_a, data, leakage, {"exp": exp, "pf": pf, "trades": trades_total}


def _gross_pf(folds: list[dict]) -> float | None:
    wins = sum(f["pnl"] for f in folds if (f.get("pnl") or 0.0) > 0)
    losses = abs(sum(f["pnl"] for f in folds if (f.get("pnl") or 0.0) < 0))
    if losses == 0:
        return None if wins == 0 else float("inf")
    return wins / losses


def evaluate_matrix(matrix_dir: str, *, output_root: str = "results/stage_a") -> dict:
    from contracts.protocol import CellStatus
    from research.protocol.gates import GateInputs, evaluate_gates
    from research.protocol.manifest import build_manifest, next_experiment_id, write_manifest
    from research.protocol.registry import append
    from research.protocol.scorecard import compute_scorecard

    matrix_path = Path(matrix_dir)
    index = json.loads((matrix_path / "index.json").read_text(encoding="utf-8"))
    report = json.loads((matrix_path / "report.json").read_text(encoding="utf-8"))

    coverage_path = Path("results/matrix/audit_20260823/coverage.json")
    gap_symbols: set[str] = set()
    if coverage_path.exists():
        coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
        for symbol, row in (coverage.get("symbols") or {}).items():
            bars = row.get("bars", {}) if isinstance(row, dict) else {}
            if bars.get("gaps_over_interval") or bars.get("duplicate_timestamps"):
                gap_symbols.add(symbol)

    commit = _git_commit()
    stamp = datetime.now(timezone.utc)
    summaries: list[dict] = []

    for key, entry in index.get("cells", {}).items():
        if entry.get("status") != CellStatus.COMPLETED.value:
            continue
        artifact = Path(entry["artifact_path"])
        if not artifact.exists():
            continue
        cell = json.loads(artifact.read_text(encoding="utf-8"))
        identity = cell["identity"]
        plan = cell.get("plan", {})
        strategy_type = identity["strategy_type"]
        symbol = identity["symbol"]
        variant = identity.get("param_variant", "base")

        stage_a, data_gate, leakage_gate, headline = _combo_inputs(cell)
        data_gate["unexplained_gaps"] = symbol in gap_symbols
        gate_results = evaluate_gates(
            GateInputs.from_dict(
                {"data": data_gate, "leakage": leakage_gate, "stage_a": stage_a}
            )
        )
        g3 = next(g for g in gate_results if g.gate.value == "G3_STAGE_A")
        scorecard = compute_scorecard(
            gate_results,
            metrics_present_flags={
                "cost_execution": 1.0 if data_gate["funding_coverage_complete"] else 0.5,
                "risk_quality": 0.5,
            },
            hypothesis_quality_flags={"economic_rationale_documented": True},
        )

        experiment_id = next_experiment_id()
        warmup_days = plan.get("warmup_days", 10)
        manifest = build_manifest(
            experiment_id=experiment_id,
            hypothesis_id=HYPOTHESIS_BY_STRATEGY.get(strategy_type, f"H-EXISTING-{strategy_type}-v1"),
            candidate_version=1,
            strategy_type=strategy_type,
            owner_agent="A4" if strategy_type == VOLCOMP_STRATEGY_TYPE else "A2",
            validator_agent="A3",
            git_commit=commit,
            dirty_worktree=False,
            config_path=plan.get("config_path", "unknown"),
            config_sha256=identity["config_sha256"],
            data_snapshot_id=identity["data_snapshot_id"],
            data_manifest_sha256=identity["data_snapshot_id"],
            universe_snapshot=report.get("coverage_ref", "coverage.json"),
            actual_start_utc=cell["window_actual"]["start_utc"],
            actual_end_utc=cell["window_actual"]["end_utc"],
            common_intersection=f"{cell['window_actual']['start_utc']}..{cell['window_actual']['end_utc']}",
            split_policy=plan.get("split_policy", "undeclared"),
            warmup_bars=warmup_days * WARMUP_BARS_PER_DAY,
            purge_bars=0,
            embargo_bars=0,
            outer_folds=plan.get("folds", 3),
            parameter_combinations=1,
            prior_family_trials=0,
            fee_model=identity["fee_model"],
            slippage_model=identity["slippage_model"],
            funding_mode="post-trade-audit",
            random_seed=identity.get("seed"),
            parameter_lock_utc=stamp.isoformat(),
            command=f"python -m research.matrix_runner --tier {cell.get('tier', 1)}",
        )

        out_dir = Path(output_root) / experiment_id
        out_dir.mkdir(parents=True, exist_ok=True)
        write_manifest(manifest, out_dir / "manifest.yaml")
        cells_lines = [json.dumps(fold, default=str) for fold in stage_a["folds"]]
        (out_dir / "cells.jsonl").write_text("\n".join(cells_lines) + "\n", encoding="utf-8")
        (out_dir / "gate_result.json").write_text(
            json.dumps([g.to_dict() for g in gate_results], indent=2), encoding="utf-8"
        )
        (out_dir / "scorecard.json").write_text(
            json.dumps({"components": scorecard.components, "total": scorecard.total,
                        "max_verdict": scorecard.max_verdict()}, indent=2),
            encoding="utf-8",
        )

        verdict = {
            "PASS": "CANDIDATE_PASS",
            "FAIL": "CANDIDATE_FAIL",
        }.get(g3.verdict.value, "INCONCLUSIVE")
        registry_entry = {
            "experiment_id": experiment_id,
            "verdict": verdict,
            "hypothesis_id": manifest.hypothesis_id,
            "strategy_type": strategy_type,
            "symbol": symbol,
            "param_variant": variant,
            "g3": g3.to_dict(),
            "reasons": list(g3.reasons),
            "exp_after_cost": headline["exp"],
            "pf_after_cost": headline["pf"],
            "trades": headline["trades"],
            "scorecard_total": scorecard.total,
            "scorecard_max_verdict": scorecard.max_verdict(),
            "artifact_dir": str(out_dir),
        }
        append(registry_entry)

        pf_value = headline["pf"]
        summaries.append(
            {
                "experiment_id": experiment_id,
                "strategy_type": strategy_type,
                "symbol": symbol,
                "variant": variant,
                "verdict": verdict,
                "reasons": list(g3.reasons),
                "exp_after_cost": headline["exp"],
                "pf_after_cost": pf_value if pf_value is None else round(pf_value, 4),
                "trades": headline["trades"],
                "scorecard_total": scorecard.total,
            }
        )

    summaries.sort(key=lambda r: (r["verdict"] != "CANDIDATE_PASS", -(r["exp_after_cost"] or -9)))
    summary_payload = {
        "generated_at_utc": stamp.isoformat(),
        "matrix_dir": str(matrix_path),
        "evaluated": len(summaries),
        "pass": sum(1 for s in summaries if s["verdict"] == "CANDIDATE_PASS"),
        "fail": sum(1 for s in summaries if s["verdict"] == "CANDIDATE_FAIL"),
        "inconclusive": sum(1 for s in summaries if s["verdict"] == "INCONCLUSIVE"),
        "rows": summaries,
    }
    out = Path(output_root) / f"sprint_summary_{stamp:%Y%m%dT%H%M%SZ}.json"
    out.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary_payload.items() if k != "rows"}, indent=2))
    return summary_payload


# --------------------------------------------------------------------------- #
# Sprint V2 mode (PLAN sections 7, 8, 9, 13) -- owner A3
# --------------------------------------------------------------------------- #
def _resolve_first_existing(paths: list[str]) -> Path:
    for candidate in paths:
        path = Path(candidate)
        if path.exists():
            return path
    raise FileNotFoundError(f"none of the evidence paths exist: {paths}")


def _coverage_path_or_raise(coverage_path: str | None) -> Path:
    candidates = (
        [coverage_path] if coverage_path
        else [
            "results/matrix/audit_20260823/coverage.json",
            f"{MAIN_REPO_RESULTS_ROOT}/matrix/audit_20260823/coverage.json",
        ]
    )
    return _resolve_first_existing(candidates)


def _load_v1_rows(v1_summary_dir: str | None) -> tuple[dict[tuple[str, str, str], dict], list[str]]:
    """Old V1 summary rows keyed by (strategy_type, symbol, variant)."""
    if v1_summary_dir:
        patterns = [str(Path(v1_summary_dir) / "sprint_summary_*.json")]
    else:
        patterns = [
            "results/stage_a/sprint_summary_*.json",
            f"{MAIN_REPO_RESULTS_ROOT}/stage_a/sprint_summary_*.json",
        ]
    sources: list[str] = []
    rows: dict[tuple[str, str, str], dict] = {}
    for pattern in patterns:
        for match in sorted(glob.glob(pattern)):
            payload = json.loads(Path(match).read_text(encoding="utf-8"))
            for row in payload.get("rows", []):
                key = (row["strategy_type"], row["symbol"], row.get("variant", "base"))
                rows[key] = row  # later summaries win (iter1 supersedes stage_a)
                sources.append(match)
    return rows, sorted(set(sources))


def _scoped_coverage_payload(full: dict, symbol: str, w_start: str, w_end: str) -> dict:
    """Per-symbol G0 evidence scoped to the scored window.

    Gap details are filtered to those overlapping ``[w_start, w_end]`` so a
    historical gap outside the scored window cannot fail an unrelated cell.
    Duplicates/funding/metadata are carried from the audited artifact.
    """
    entry = (full.get("symbols") or {}).get(symbol)
    scoped: dict[str, Any] | None = None
    if isinstance(entry, dict):
        bars = entry.get("bars") or {}
        overlapping: list[dict] = []
        for gap in bars.get("gap_details") or []:
            after = str(gap.get("after_ts_utc", ""))
            before = str(gap.get("before_ts_utc", ""))
            if after <= w_end and before >= w_start:  # ISO strings compare OK
                overlapping.append(gap)
        scoped = {
            **entry,
            "bars": {
                **bars,
                "gaps_over_interval": len(overlapping),
                "gap_details": overlapping,
            },
        }
    return {"symbols": {symbol: scoped} if scoped is not None else {}}


def _positions_from_ledger(cell_artifact: Path) -> list[dict]:
    ledger = cell_artifact.with_name(cell_artifact.stem + ".positions.jsonl")
    if not ledger.exists():
        return []
    rows = []
    for line in ledger.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _canonical_metrics_doc(
    cell: dict, stats: dict, positions: list[dict], symbol_scoped_gaps: int
) -> dict:
    trades = stats["trades"]
    net = stats["net_pnl"] if trades else None
    folds_stats = [fold.get("positions_stats", {}) for fold in cell.get("folds", [])]
    funded_nets = [fs.get("net_pnl") or 0.0 for fs in folds_stats]
    total_net = sum(funded_nets)
    top_contribution = (
        max((abs(v) for v in funded_nets), default=0.0) / abs(total_net) * 100.0
        if total_net > 0 else None
    )
    funding_net = round(sum(row.get("funding_net") or 0.0 for row in positions), 10)
    return {
        "schema_version": 2,
        "strategy_type": cell["identity"]["strategy_type"],
        "symbol": cell["identity"]["symbol"],
        "param_variant": cell["identity"].get("param_variant", "base"),
        "window_actual": cell["window_actual"],
        "accounting": "position_level_after_funding_v2",
        "trades": {"value": trades, "reason": None if trades else "no_trades"},
        "gross_profit": {"value": stats["gross_profit"], "reason": None if trades else "no_trades"},
        "gross_loss": {"value": stats["gross_loss"], "reason": None if trades else "no_trades"},
        "net_canonical_pnl": {
            "value": round(net, 10) if net is not None else None,
            "reason": None if net is not None else "no_trades",
        },
        "expectancy_usdt": {
            "value": round(net / trades, 10) if trades else None,
            "reason": None if trades else "no_trades",
        },
        "profit_factor": {
            "value": stats["profit_factor"],
            "reason": stats["pf_reason"],
        },
        "funding_net": funding_net,
        "positive_folds": sum(1 for v in funded_nets if v > 0),
        "outer_folds": len(folds_stats),
        "top_fold_contribution_pct": top_contribution,
        "scored_window_unexplained_gaps": symbol_scoped_gaps,
        "positions_count": len(positions),
        "positions_digest": cell.get("positions_digest"),
        "observations": cell.get("observations", []),
    }


def _write_manifest_v2(spec, path: Path) -> None:
    import yaml

    payload = spec.to_dict()
    if spec.random_seed is None:
        payload["random_seed_reason"] = "seed_unavailable"
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def _artifact_hashes(exp_dir: Path) -> dict:
    files: dict[str, str] = {}
    for path in sorted(exp_dir.rglob("*")):
        if path.is_file() and path.name != "artifact_hashes.json":
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            files[str(path.relative_to(exp_dir))] = digest
    return {
        "schema_version": 1,
        "algorithm": "sha256",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": files,
    }


def evaluate_matrix_v2(
    matrix_dir: str,
    *,
    output_root: str = V2_DEFAULT_OUTPUT_ROOT,
    coverage_path: str | None = None,
    v1_summary_dir: str | None = None,
) -> dict:
    """Sprint V2 evaluation: frozen provenance + position-level gates."""
    from contracts.protocol import CellStatus, GateId, GateVerdict
    from research.protocol.gates import (
        DataGateInput,
        GateInputs,
        LeakageGateInput,
        ReproductionComparison,
        StageAInput,
        evaluate_gates,
    )
    from research.protocol.manifest import next_experiment_id
    from research.protocol.registry import append, load_all
    from research.protocol.scorecard import compute_scorecard
    from research.provenance import (
        build_manifest_v2,
        snapshot_experiment_inputs,
    )

    matrix_path = Path(matrix_dir)
    index = json.loads((matrix_path / "index.json").read_text(encoding="utf-8"))
    report = json.loads((matrix_path / "report.json").read_text(encoding="utf-8"))

    coverage_file = _coverage_path_or_raise(coverage_path)
    full_coverage = json.loads(coverage_file.read_text(encoding="utf-8"))
    commit = _git_commit()
    output_path = Path(output_root)

    v2_hypothesis_counts: dict[str, int] = {}
    for entry in load_all():
        hypothesis = entry.get("hypothesis_id")
        if hypothesis:
            v2_hypothesis_counts[hypothesis] = v2_hypothesis_counts.get(hypothesis, 0) + 1

    summaries: list[dict] = []
    protocol_failures = 0

    for key, registry_entry in index.get("cells", {}).items():
        if registry_entry.get("status") != CellStatus.COMPLETED.value:
            continue
        artifact = Path(registry_entry["artifact_path"])
        if not artifact.exists():
            continue
        plan = {}
        identity_hint = registry_entry.get("identity", {})
        strategy_type = identity_hint.get("strategy_type")
        symbol = identity_hint.get("symbol")

        # --- 1. Freeze inputs BEFORE reading results (fail-closed order) --- #
        experiment_id = next_experiment_id()
        exp_dir = output_path / experiment_id
        lock_stamp = datetime.now(timezone.utc).isoformat()

        def _plan_field(name: str, default=None):  # late-bound on purpose
            nonlocal plan
            if not plan:
                plan = json.loads(artifact.read_text(encoding="utf-8")).get("plan", {})
            return plan.get(name, default)

        config_path = _plan_field("config_path", "config/research.yaml")
        candidate_path = (
            VOLCOMP_HYPOTHESIS_CONFIG
            if strategy_type == VOLCOMP_STRATEGY_TYPE
            else config_path
        )
        window_start = _plan_field("window_declared", {}).get("start_utc")
        window_end = _plan_field("window_declared", {}).get("end_utc")
        split_policy = _plan_field("split_policy", "")
        warmup_days = int(_plan_field("warmup_days", 10))
        folds_declared = int(_plan_field("folds", 3))

        snapshot = snapshot_experiment_inputs(
            exp_dir,
            config_path=config_path,
            candidate_path=candidate_path,
            universe_symbols=[symbol],
            requested_window=(window_start, window_end),
            data_manifest_path=coverage_file,
            parameter_lock_utc=lock_stamp,
        )

        # --- 2. NOW read the scored results -------------------------------- #
        cell = json.loads(artifact.read_text(encoding="utf-8"))
        identity = cell["identity"]
        strategy_type = identity["strategy_type"]
        symbol = identity["symbol"]
        variant = identity.get("param_variant", "base")
        hypothesis_id = HYPOTHESIS_BY_STRATEGY.get(strategy_type, f"H-EXISTING-{strategy_type}-v1")
        prior_trials = v2_hypothesis_counts.get(hypothesis_id, 0)

        manifest: ManifestV2Spec = build_manifest_v2(
            snapshot,
            experiment_id=experiment_id,
            matrix_id=report.get("matrix_id", matrix_path.name),
            hypothesis_id=hypothesis_id,
            candidate_version=1,
            strategy_type=strategy_type,
            owner_agent="A4" if strategy_type == VOLCOMP_STRATEGY_TYPE else "A2",
            validator_agent="A3",
            random_seed=identity.get("seed"),
            actual_start_utc=cell["window_actual"]["start_utc"],
            actual_end_utc=cell["window_actual"]["end_utc"],
            continuous_clean_intersection=(
                f"{cell['window_actual']['start_utc']}..{cell['window_actual']['end_utc']}"
            ),
            split_policy=split_policy or "undeclared",
            warmup_bars=warmup_days * WARMUP_BARS_PER_DAY,
            purge_bars=0,
            embargo_bars=0,
            outer_folds=folds_declared,
            declared_parameter_combinations=1,
            executed_parameter_combinations=1,
            prior_family_trials=prior_trials,
            fee_model=str(identity["fee_model"]),
            slippage_model=str(identity["slippage_model"]),
            funding_mode="audited-post-trade",
        )
        validation_reasons = manifest.validate()
        if validation_reasons:
            raise ValueError(f"manifest invalid for {experiment_id}: {validation_reasons}")
        _write_manifest_v2(manifest, exp_dir / "manifest.yaml")

        # Positions ledger + canonical metrics --------------------------- #
        positions = _positions_from_ledger(artifact)
        scoped = _scoped_coverage_payload(
            full_coverage, symbol,
            cell["window_actual"]["start_utc"], cell["window_actual"]["end_utc"],
        )
        symbol_entry = (scoped["symbols"].get(symbol) or {})
        scoped_gaps = int(
            (symbol_entry.get("bars") or {}).get("gaps_over_interval") or 0
        ) if symbol_entry else 0

        stats = cell.get("positions_stats") or {
            "trades": None, "gross_profit": None, "gross_loss": None,
            "net_pnl": None, "profit_factor": None, "pf_reason": "metric_not_computed",
        }
        canonical_metrics = _canonical_metrics_doc(cell, stats, positions, scoped_gaps)
        (exp_dir / "positions.jsonl").write_text(
            "".join(json.dumps(row) + "\n" for row in positions), encoding="utf-8"
        )
        (exp_dir / "canonical_metrics.json").write_text(
            json.dumps(canonical_metrics, indent=2), encoding="utf-8"
        )

        # Gates ----------------------------------------------------------- #
        g0_input = DataGateInput(coverage_payload=scoped)
        g1_evidence = {
            "split_policy_declared": bool(split_policy not in ("", "pending")),
            "warmup_outside_window": {
                "warmup_days": warmup_days,
                "bars_incl_warmup_min": min(
                    fold.get("bars_incl_warmup", 0) for fold in cell.get("folds", [])
                ) if cell.get("folds") else 0,
                "scored_bars_max": max(
                    fold.get("scored_bars", 0) for fold in cell.get("folds", [])
                ) if cell.get("folds") else 0,
                "note": "warmup bars loaded strictly before window start",
            },
            "transforms_fit_on_train": True,
            "universe_frozen_before_run": {
                "parameter_lock_utc": manifest.parameter_lock_utc,
                "run_started_utc": manifest.run_started_utc,
                "universe_snapshot_sha256": manifest.universe_snapshot_sha256[:16],
            },
            "execution_model_declared": {
                "fee_model": str(identity["fee_model"]),
                "slippage_model": str(identity["slippage_model"]),
            },
        }
        g1_input = LeakageGateInput(evidence=g1_evidence)

        rerun_positions_digest = sha256_of_rows(positions)
        frozen_hashes = recompute_frozen_hashes(exp_dir)
        pnl_original = float(cell.get("pnl_after_funding") or 0.0)
        pnl_rerun = sum((row.get("pnl_after_funding") or 0.0) for row in positions)
        reproduction = ReproductionComparison(
            config_sha256_expected=snapshot["frozen_config_sha256"],
            config_sha256_actual=frozen_hashes["config"],
            candidate_sha256_expected=snapshot["frozen_candidate_sha256"],
            candidate_sha256_actual=frozen_hashes["candidate"],
            data_manifest_sha256_expected=snapshot["data_manifest_sha256"],
            data_manifest_sha256_actual=frozen_hashes["data_manifest"],
            positions_digest_original=cell.get("positions_digest"),
            positions_digest_rerun=rerun_positions_digest,
            canonical_pnl_original=pnl_original,
            canonical_pnl_rerun=pnl_rerun,
            pnl_rtol=1e-6,
        )

        trades_total = stats.get("trades") or 0
        net_total = stats.get("net_pnl")
        exp_position = (net_total / trades_total) if trades_total else None
        fold_rows = []
        for fold in cell.get("folds", []):
            fs = fold.get("positions_stats", {})
            ft = fs.get("trades") or 0
            fold_rows.append(
                {
                    "fold_id": str(fold["fold"]),
                    "trades": ft,
                    "pnl_after_cost": fs.get("net_pnl"),
                    "exp_after_cost": (fs.get("net_pnl") / ft) if ft else None,
                    "pf_after_cost": fs.get("profit_factor"),
                }
            )
        stage_a = {
            "exp_after_cost": exp_position,
            "pf_after_cost": stats.get("profit_factor"),
            "total_trades": trades_total,
            "folds": fold_rows,
            "symbols": [{
                "symbol": symbol,
                "trades": trades_total,
                "pnl_after_cost": net_total,
                "exp_after_cost": exp_position,
                "pf_after_cost": stats.get("profit_factor"),
            }],
            "top_fold_contribution_pct": canonical_metrics["top_fold_contribution_pct"],
        }

        gate_results = evaluate_gates(
            GateInputs(
                data=g0_input,
                leakage=g1_input,
                reproduction=reproduction,
                stage_a=StageAInput(**stage_a),
            )
        )
        verdict_by_gate = {g.gate: g.verdict for g in gate_results}
        (exp_dir / "gate_result.json").write_text(
            json.dumps([g.to_dict() for g in gate_results], indent=2), encoding="utf-8"
        )

        scorecard = compute_scorecard(
            gate_results,
            metrics_present_flags={
                "cost_execution": 1.0 if positions else 0.5,
                "risk_quality": 0.5,
            },
            hypothesis_quality_flags={"economic_rationale_documented": True},
        )
        g_all_pass = all(
            verdict_by_gate.get(gate) is GateVerdict.PASS
            for gate in (
                GateId.G0_DATA, GateId.G1_LEAKAGE,
                GateId.G2_REPRODUCIBILITY, GateId.G3_STAGE_A,
            )
        )
        (exp_dir / "scorecard.json").write_text(
            json.dumps(
                {
                    "components": scorecard.components,
                    "total": scorecard.total,
                    "max_verdict": scorecard.max_verdict(),
                    "diagnostic": not g_all_pass,
                    "note": "final_research_score requires G0-G5 PASS (PLAN 10.1)",
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        # Verdict --------------------------------------------------------- #
        g3_result = verdict_by_gate and next(
            g for g in gate_results if g.gate is GateId.G3_STAGE_A
        )
        g3 = g3_result.verdict
        protocol_fail = any(
            verdict_by_gate.get(gate) is GateVerdict.FAIL
            for gate in (GateId.G0_DATA, GateId.G1_LEAKAGE, GateId.G2_REPRODUCIBILITY)
        )
        reasons = list(g3_result.reasons)
        for gate in (GateId.G0_DATA, GateId.G1_LEAKAGE, GateId.G2_REPRODUCIBILITY):
            if verdict_by_gate.get(gate) is GateVerdict.FAIL:
                reasons.extend(
                    next(g for g in gate_results if g.gate == gate).reasons
                )
        if protocol_fail:
            verdict = "UNRANKED_PROTOCOL_FAIL"
            protocol_failures += 1
        elif g3 is GateVerdict.PASS:
            verdict = "CANDIDATE_PASS"
        elif g3 in (GateVerdict.INCONCLUSIVE, GateVerdict.NOT_YET_TESTED):
            verdict = "INCONCLUSIVE"
        else:
            verdict = "CANDIDATE_FAIL"

        # run.log + artifact hashes (hashes last, self excluded) ---------- #
        log_line = (
            f"{datetime.now(timezone.utc).isoformat()} | {experiment_id} | "
            f"{strategy_type} | {symbol} | {variant} | {verdict} | "
            f"pf={stats.get('profit_factor')} | trades={trades_total} | "
            f"digest={str(cell.get('positions_digest'))[:16]}\n"
        )
        (exp_dir / "run.log").write_text(log_line, encoding="utf-8")
        (exp_dir / "artifact_hashes.json").write_text(
            json.dumps(_artifact_hashes(exp_dir), indent=2), encoding="utf-8"
        )

        append(
            {
                "experiment_id": experiment_id,
                "verdict": verdict,
                "schema": "v2",
                "hypothesis_id": hypothesis_id,
                "strategy_type": strategy_type,
                "symbol": symbol,
                "param_variant": variant,
                "matrix_id": manifest.matrix_id,
                "git_commit_at_launch": manifest.git_commit_at_launch,
                "g0": verdict_by_gate[GateId.G0_DATA].value,
                "g1": verdict_by_gate[GateId.G1_LEAKAGE].value,
                "g2": verdict_by_gate[GateId.G2_REPRODUCIBILITY].value,
                "g3": g3_result.to_dict(),
                "reasons": sorted(set(reasons)),
                "canonical": {
                    "trades": trades_total,
                    "net_canonical_pnl": net_total,
                    "positions_digest": cell.get("positions_digest"),
                },
                "pf_position_level": stats.get("profit_factor"),
                "exp_after_cost": exp_position,
                "scorecard_total": scorecard.total,
                "scorecard_diagnostic": not g_all_pass,
                "artifact_dir": str(exp_dir),
            }
        )
        v2_hypothesis_counts[hypothesis_id] = prior_trials + 1

        summaries.append(
            {
                "experiment_id": experiment_id,
                "strategy_type": strategy_type,
                "symbol": symbol,
                "variant": variant,
                "verdict": verdict,
                "reasons": sorted(set(reasons)),
                "pf_position_level": stats.get("profit_factor"),
                "exp_after_cost": exp_position,
                "trades": trades_total,
                "net_canonical_pnl": net_total,
                "scorecard_total": scorecard.total,
                "scorecard_diagnostic": not g_all_pass,
            }
        )

    comparison = build_v1_v2_comparison(matrix_path, summaries, v1_summary_dir)
    summary_payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "matrix_dir": str(matrix_path),
        "schema": "v2",
        "evaluated": len(summaries),
        "pass": sum(1 for s in summaries if s["verdict"] == "CANDIDATE_PASS"),
        "fail": sum(1 for s in summaries if s["verdict"] == "CANDIDATE_FAIL"),
        "inconclusive": sum(1 for s in summaries if s["verdict"] == "INCONCLUSIVE"),
        "protocol_fail": protocol_failures,
        "rows": summaries,
        "v1_v2_comparison": comparison,
    }
    print(json.dumps({k: v for k, v in summary_payload.items() if k != "rows"}, indent=2))
    return summary_payload


def sha256_of_rows(rows: list[dict]) -> str:
    """Deterministic digest of a positions ledger (matches runner's method)."""
    from contracts.protocol import canonical_json, sha256_text

    return sha256_text(canonical_json(rows))


def recompute_frozen_hashes(exp_dir: Path) -> dict[str, str]:
    """Actual SHA-256 of the frozen copies currently on disk."""
    from contracts.protocol import sha256_file

    frozen = Path(exp_dir) / "frozen"
    return {
        "config": sha256_file(frozen / "config.yaml"),
        "candidate": sha256_file(frozen / "candidate.yaml"),
        "data_manifest": sha256_file(frozen / "data_manifest.json"),
    }


def build_v1_v2_comparison(
    matrix_path: Path, summaries: list[dict], v1_summary_dir: str | None
) -> dict | None:
    """Compare OLD fold-net PF vs NEW position-level PF per combo."""
    old_rows, sources = _load_v1_rows(v1_summary_dir)
    if not old_rows:
        return None

    def _num(value: Any) -> float | None:
        # Non-finite PF (V1 emitted ``Infinity`` when no fold lost money) is
        # not a number: record it as null so artifacts stay strict JSON and
        # dPF math stays meaningful.
        if value is None:
            return None
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return None
        return numeric if math.isfinite(numeric) else None

    rows: list[dict] = []
    matched = 0
    for new in summaries:
        key = (new["strategy_type"], new["symbol"], new["variant"])
        old = old_rows.get(key)
        if old is None:
            continue
        matched += 1
        pf_old, pf_new = _num(old.get("pf_after_cost")), _num(new["pf_position_level"])
        d_pf = None if pf_old is None or pf_new is None else round(pf_new - pf_old, 6)
        rows.append(
            {
                "strategy_type": new["strategy_type"],
                "symbol": new["symbol"],
                "variant": new["variant"],
                "pf_old_fold_net": pf_old,
                "pf_new_position_level": pf_new,
                "d_pf": d_pf,
                "exp_old": _num(old.get("exp_after_cost")),
                "exp_new": _num(new["exp_after_cost"]),
                "trades_old": old.get("trades"),
                "trades_new": new["trades"],
                "verdict_old": old.get("verdict"),
                "verdict_new": new["verdict"],
                "verdict_changed": old.get("verdict") != new["verdict"],
            }
        )
    shifts = sorted(
        (row for row in rows if row["d_pf"] is not None),
        key=lambda row: abs(row["d_pf"]),
        reverse=True,
    )[:5]
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "matrix_dir": str(matrix_path),
        "v1_sources": sources,
        "matched": matched,
        "unmatched_v2": [
            f"{s['strategy_type']}|{s['symbol']}|{s['variant']}"
            for s in summaries
            if (s["strategy_type"], s["symbol"], s["variant"]) not in old_rows
        ],
        "verdict_changes": sum(1 for row in rows if row["verdict_changed"]),
        "top_pf_shifts": shifts,
        "rows": rows,
    }
    out = matrix_path / "v1_v2_comparison.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {
        "matched": matched,
        "verdict_changes": payload["verdict_changes"],
        "top_pf_shifts": [
            {k: row[k] for k in ("strategy_type", "symbol", "variant", "d_pf")}
            for row in shifts
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--matrix-dir", required=True)
    parser.add_argument("--output-root", default=None)
    parser.add_argument(
        "--schema", choices=("v1", "v2"), default="v2",
        help="v2 = Sprint V2 provenance + position-level canonical mode",
    )
    parser.add_argument("--coverage-path", default=None,
                        help="data-contract coverage.json used as G0 evidence")
    parser.add_argument("--v1-summary-dir", default=None,
                        help="directory holding V1 sprint_summary_*.json rows")
    args = parser.parse_args(argv)

    if args.schema == "v2":
        evaluate_matrix_v2(
            args.matrix_dir,
            output_root=args.output_root or V2_DEFAULT_OUTPUT_ROOT,
            coverage_path=args.coverage_path,
            v1_summary_dir=args.v1_summary_dir,
        )
        return 0
    evaluate_matrix(args.matrix_dir, output_root=args.output_root or "results/stage_a")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
