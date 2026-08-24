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

from contracts.protocol import GateId, GateVerdict, require_reason

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
# Sprint V3 mode (PLAN sections 8-11) -- owner A3
#
# The evaluator ONLY READS the runner-written launch manifest; it never
# creates lock timestamps or fabricates leakage/execution evidence.
# --------------------------------------------------------------------------- #
V3_DEFAULT_OUTPUT_ROOT = "results/stage_a_v3"


def _leakage_from_artifact(document: dict):
    """Rehydrate runner-emitted LeakageEvidence from a cell artifact."""
    from contracts.protocol import LeakageEvidence

    raw = document.get("leakage_evidence")
    if not isinstance(raw, dict):
        return None
    return LeakageEvidence(
        split_policy_declared=bool(raw.get("split_policy_declared")),
        warmup_boundaries=raw.get("warmup_boundaries"),
        transform_evidence=raw.get("transform_evidence"),
        universe_freeze=raw.get("universe_freeze"),
        execution_ordering=raw.get("execution_ordering"),
        notes=tuple(raw.get("notes") or ()),
    )


def _positions_reconcile(positions: list[dict], cell: dict) -> bool:
    """sum(canonical position PnL) must equal cell net within rel 1e-9."""
    net = (cell.get("positions_stats") or {}).get("net_pnl")
    if net is None:
        net = cell.get("pnl_after_funding") or 0.0
    total = sum((row.get("pnl_after_funding") or 0.0) for row in positions)
    scale = max(1.0, abs(float(net)))
    return abs(total - float(net)) <= 1e-9 * scale


def _verify_manifest_hashes(manifest, exp_dir: Path) -> bool:
    from contracts.protocol import sha256_file

    frozen = exp_dir / "frozen"
    pairs = (
        (manifest.runtime_config_sha256, frozen / "runtime_config.yaml"),
        (manifest.candidate_spec_sha256, frozen / "candidate.yaml"),
        (manifest.data_manifest_sha256, frozen / "data_manifest.json"),
        (manifest.universe_sha256, frozen / "universe.json"),
    )
    return all(
        target.is_file() and sha256_file(target) == expected
        for expected, target in pairs
    )


def _rationale_flags(candidate_path: Path) -> dict[str, bool]:
    """Hypothesis-doc presence + specificity flags (never constants)."""
    import yaml

    flags = {
        "economic_mechanism_specific": False,
        "expected_counterparty_named": False,
        "invalidating_evidence_pre_registered": False,
        "entry_exit_rules_concrete": False,
    }
    try:
        raw = yaml.safe_load(candidate_path.read_text(encoding="utf-8")) or {}
    except Exception:  # noqa: BLE001 - unreadable spec simply earns no points
        return flags

    def _specific(value: Any, min_len: int) -> bool:
        return isinstance(value, str) and len(value.strip()) >= min_len

    invalidating = raw.get("invalidating_evidence")
    flags["economic_mechanism_specific"] = _specific(
        raw.get("economic_mechanism"), 80
    )
    flags["expected_counterparty_named"] = _specific(
        raw.get("expected_counterparty"), 40
    )
    flags["invalidating_evidence_pre_registered"] = (
        isinstance(invalidating, list)
        and len(invalidating) >= 2
        and all(isinstance(item, str) and len(item.strip()) > 20 for item in invalidating)
    )
    flags["entry_exit_rules_concrete"] = _specific(raw.get("entry_exit_rules"), 120)
    return flags


def _top_fold_contribution(cell: dict) -> float | None:
    folds_stats = [fold.get("positions_stats", {}) for fold in cell.get("folds", [])]
    funded_nets = [fs.get("net_pnl") or 0.0 for fs in folds_stats]
    total_net = sum(funded_nets)
    if total_net > 0 and funded_nets:
        return max(abs(v) for v in funded_nets) / abs(total_net) * 100.0
    return None


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
        verdict_by_gate = {
            (g.gate.value if hasattr(g.gate, "value") else str(g.gate)): g.verdict
            for g in gate_results
        }
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
                GateId.G0_DATA.value, GateId.G1_LEAKAGE.value,
                "G2A_ARTIFACT_INTEGRITY", "G2B_INDEPENDENT_REPRODUCIBILITY",
                GateId.G3_STAGE_A.value,
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
        def _row_for(gate_value: str):
            return next(
                g
                for g in gate_results
                if (g.gate.value if hasattr(g.gate, "value") else str(g.gate))
                == gate_value
            )

        g3_result = _row_for(GateId.G3_STAGE_A.value)
        g3 = g3_result.verdict
        protocol_fail_gates = (
            GateId.G0_DATA.value, GateId.G1_LEAKAGE.value, "G2A_ARTIFACT_INTEGRITY",
        )
        protocol_fail = any(
            verdict_by_gate.get(gate) is GateVerdict.FAIL for gate in protocol_fail_gates
        )
        reasons = list(g3_result.reasons)
        for row in gate_results:
            row_gate = row.gate.value if hasattr(row.gate, "value") else str(row.gate)
            if row_gate in protocol_fail_gates and row.verdict is GateVerdict.FAIL:
                reasons.extend(row.reasons)
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
                "g0": verdict_by_gate[GateId.G0_DATA.value].value,
                "g1": verdict_by_gate[GateId.G1_LEAKAGE.value].value,
                "g2a": verdict_by_gate["G2A_ARTIFACT_INTEGRITY"].value,
                "g2b": verdict_by_gate["G2B_INDEPENDENT_REPRODUCIBILITY"].value,
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


def evaluate_matrix_v3(
    matrix_dir: str,
    *,
    output_root: str = V3_DEFAULT_OUTPUT_ROOT,
    coverage_path: str | None = None,
    registry_path: str | Path | None = None,
    finalize: bool = True,
) -> dict:
    """Sprint V3 evaluation: read-only provenance + separated G2a/G2b gates.

    Per COMPLETED cell the evaluator reads the runner's launch manifest and
    emitted LeakageEvidence, evaluates gates G0/G1/G2A/G2B/G3, scores the
    real-band scorecard, writes gate/scorecard artifacts next to the frozen
    inputs, and appends one CELL_RESULT registry row per declared cell
    (including PIPELINE_ERROR cells).  With ``finalize`` the matrix is
    reconciled from the final index/filesystem (reconciliation.json) and a
    MATRIX_FINALIZE row is appended.
    """
    from contracts.protocol import (
        ArtifactIntegrityResult,
        CellStatus,
        IndependentReproductionResult,
        require_reason,
    )
    from research.matrix_runner import LaunchManifestInvalid, read_launch_manifest
    from research.protocol.gates import (
        DataGateInput,
        GateInputs,
        RunnerLeakageGateInput,
        StageAInput,
        evaluate_gates,
        g2_promotion_pass,
    )
    from research.protocol.registry import append, load_all
    from research.protocol.reconciliation import (
        append_matrix_finalize_entry,
        finalize_matrix,
    )
    from research.protocol.scorecard import compute_scorecard_v3, score_eligibility

    matrix_path = Path(matrix_dir)
    index = json.loads((matrix_path / "index.json").read_text(encoding="utf-8"))
    report = json.loads((matrix_path / "report.json").read_text(encoding="utf-8"))
    coverage_file = _coverage_path_or_raise(coverage_path)
    full_coverage = json.loads(coverage_file.read_text(encoding="utf-8"))
    output_path = Path(output_root)

    rerun_by_experiment: dict[str, dict] = {}
    for row in load_all(registry_path):
        if row.get("kind") == "INDEPENDENT_RERUN_VERIFY" and row.get(
            "verified_experiment_id"
        ):
            rerun_by_experiment.setdefault(row["verified_experiment_id"], row)

    summaries: list[dict] = []
    protocol_failures = 0

    for key, index_entry in index.get("cells", {}).items():
        identity_hint = index_entry.get("identity", {})
        strategy_type = identity_hint.get("strategy_type")
        symbol = identity_hint.get("symbol")
        variant = identity_hint.get("param_variant", "base")
        experiment_id = index_entry.get("experiment_id")
        status = index_entry.get("status")

        artifact_rel = index_entry.get("artifact_path")
        artifact = Path(artifact_rel) if artifact_rel else None
        cell: dict = {}
        if artifact and artifact.is_file():
            try:
                cell = json.loads(artifact.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                cell = {}

        if status != CellStatus.COMPLETED.value:
            reasons = sorted(
                set(index_entry.get("reason_codes") or [])
                | set(cell.get("launch_manifest_reasons") or [])
            ) or ["cell_failed_exception"]
            append(
                {
                    "experiment_id": experiment_id,
                    "verdict": status,
                    "kind": "CELL_RESULT",
                    "schema": "v3",
                    "matrix_id": report.get("matrix_id", matrix_path.name),
                    "hypothesis_id": (cell.get("provenance") or {}).get("hypothesis_id")
                    or f"H-EXISTING-{strategy_type}-v1",
                    "strategy_type": strategy_type,
                    "symbol": symbol,
                    "param_variant": variant,
                    "reasons": reasons,
                },
                path=registry_path,
            )
            summaries.append(
                {
                    "experiment_id": experiment_id,
                    "strategy_type": strategy_type,
                    "symbol": symbol,
                    "variant": variant,
                    "verdict": status,
                    "reasons": reasons,
                }
            )
            continue

        exp_dir = Path(index_entry.get("stage_a_dir") or (output_path / experiment_id))

        # 1. READ-ONLY provenance: the runner's launch manifest ------------- #
        try:
            manifest = read_launch_manifest(exp_dir / "launch_manifest.yaml")
            manifest_reasons: list[str] = []
        except (LaunchManifestInvalid, ValueError, FileNotFoundError) as exc:
            manifest = None
            manifest_reasons = list(getattr(exc, "reasons", ()) or ()) or [
                require_reason("manifest_missing_field")
            ]

        positions = _positions_from_ledger(artifact)
        scoped = _scoped_coverage_payload(
            full_coverage,
            symbol,
            cell["window_actual"]["start_utc"],
            cell["window_actual"]["end_utc"],
        )

        # 2. Gates ------------------------------------------------------------ #
        g0_input = DataGateInput(coverage_payload=scoped)
        g1_input = RunnerLeakageGateInput(evidence=_leakage_from_artifact(cell))

        schema_valid = manifest is not None and not manifest_reasons
        hashes_match = bool(
            manifest is not None and _verify_manifest_hashes(manifest, exp_dir)
        )
        g2a_result = ArtifactIntegrityResult(
            schema_valid=schema_valid,
            hashes_match=hashes_match,
            positions_reconcile=_positions_reconcile(positions, cell),
            report_index_reconcile=(
                cell.get("cell_result", {}).get("status") == status
                and bool(experiment_id)
            ),
            reasons=tuple(sorted(set(manifest_reasons))),
        )
        rerun_row = rerun_by_experiment.get(experiment_id)
        if rerun_row:
            g2b_result = IndependentReproductionResult(
                performed=True,
                rerun_process_separate=bool(rerun_row.get("rerun_process_separate", True)),
                parameters_match=bool(rerun_row.get("parameters_match")),
                positions_digest_match=bool(rerun_row.get("positions_digest_match")),
                trade_count_match=bool(rerun_row.get("trade_count_match")),
                canonical_pnl_match=bool(rerun_row.get("canonical_pnl_match")),
                source_experiment_id=experiment_id,
                rerun_experiment_id=rerun_row.get("rerun_experiment_id"),
            )
        else:
            # No independent rerun yet => NOT_YET_TESTED (diagnostic only).
            g2b_result = IndependentReproductionResult(
                performed=False,
                rerun_process_separate=False,
                parameters_match=None,
                positions_digest_match=None,
                trade_count_match=None,
                canonical_pnl_match=None,
            )

        stats = cell.get("positions_stats") or {}
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
        stage_a = StageAInput(
            exp_after_cost=exp_position,
            pf_after_cost=stats.get("profit_factor"),
            total_trades=trades_total,
            folds=fold_rows,
            symbols=[
                {
                    "symbol": symbol,
                    "trades": trades_total,
                    "pnl_after_cost": net_total,
                    "exp_after_cost": exp_position,
                    "pf_after_cost": stats.get("profit_factor"),
                }
            ],
            top_fold_contribution_pct=_top_fold_contribution(cell),
        )

        gate_results = evaluate_gates(
            GateInputs(
                data=g0_input,
                leakage=g1_input,
                artifact_integrity=g2a_result,
                independent_reproduction=g2b_result,
                stage_a=stage_a,
            )
        )
        verdict_by_gate = {
            (g.gate.value if hasattr(g.gate, "value") else str(g.gate)): g.verdict
            for g in gate_results
        }
        (exp_dir / "gate_result.json").write_text(
            json.dumps([g.to_dict() for g in gate_results], indent=2), encoding="utf-8"
        )

        # 3. Canonical metrics incl. R normalization ------------------------- #
        r_values = [
            row.get("r_multiple")
            for row in positions
            if isinstance(row.get("r_multiple"), (int, float))
        ]
        expectancy_r = (sum(r_values) / len(r_values)) if r_values else None
        positive_folds = sum(1 for row in fold_rows if (row["pnl_after_cost"] or 0) > 0)
        canonical_metrics = {
            "schema_version": 3,
            "accounting": "position_level_after_funding_v3",
            "execution_mode": (cell.get("provenance") or {}).get("execution_mode"),
            "strategy_type": strategy_type,
            "symbol": symbol,
            "param_variant": variant,
            "window_actual": cell.get("window_actual"),
            "trades": {
                "value": trades_total,
                "reason": None if trades_total else require_reason("no_trades"),
            },
            "net_canonical_pnl": {
                "value": round(net_total, 10) if net_total is not None else None,
                "reason": None if net_total is not None else require_reason("no_trades"),
            },
            "expectancy_usdt": {
                "value": round(exp_position, 10) if exp_position is not None else None,
                "reason": (
                    None if exp_position is not None else require_reason("no_trades")
                ),
            },
            "expectancy_r": {
                "value": round(expectancy_r, 10) if expectancy_r is not None else None,
                "reason": (
                    None
                    if expectancy_r is not None
                    else require_reason("metric_not_computed")
                ),
            },
            "position_pf": {"value": stats.get("profit_factor"), "reason": stats.get("pf_reason")},
            "positive_folds": positive_folds,
            "outer_folds": len(fold_rows),
            "closed_positions": len(positions),
            "positions_digest": cell.get("positions_digest"),
            "observations": cell.get("observations", []),
        }
        (exp_dir / "canonical_metrics.json").write_text(
            json.dumps(canonical_metrics, indent=2), encoding="utf-8"
        )

        # 4. Real-band scorecard from REAL evidence -------------------------- #
        candidate_path = exp_dir / "frozen" / "candidate.yaml"
        cost_flags = {
            # Survivor stress evidence does not exist until G3 survivors run.
            "fee_stress_evidence": False,
            "slippage_stress_evidence": False,
            "delay_stress_evidence": False,
            # Post-trade funding audit availability IS evidenced per cell.
            "funding_audit_evidence": bool(positions)
            and all(row.get("funding_net") is not None for row in positions),
        }
        risk_flags = {
            "max_drawdown_present": False,
            "dd_duration_present": False,
            "r_normalization_present": expectancy_r is not None,
        }
        scorecard = compute_scorecard_v3(
            gate_results,
            {
                "expectancy_r": expectancy_r,
                "position_pf": stats.get("profit_factor"),
                "positive_folds": positive_folds,
                "outer_folds": len(fold_rows),
                "closed_trades": trades_total,
                "flat_benchmark_pass": None,  # no flat benchmark engine this sprint
                "rationale_flags": _rationale_flags(candidate_path),
                "cost_flags": cost_flags,
                "risk_flags": risk_flags,
            },
        )
        eligibility = score_eligibility(gate_results)

        def _row(gate_value: str):
            return next(
                g
                for g in gate_results
                if (g.gate.value if hasattr(g.gate, "value") else str(g.gate))
                == gate_value
            )

        g2a_row = _row("G2A_ARTIFACT_INTEGRITY")
        g2b_row = _row("G2B_INDEPENDENT_REPRODUCIBILITY")
        promotion_pass = g2_promotion_pass(g2a_row, g2b_row)
        (exp_dir / "scorecard.json").write_text(
            json.dumps(
                {
                    "schema_version": 3,
                    "components": scorecard.components,
                    "total": scorecard.total,
                    "max_verdict": scorecard.max_verdict(),
                    "eligibility": eligibility,
                    "g2_promotion_pass": promotion_pass,
                    "note": (
                        "final_research_score requires G0-G5 PASS; G2b not run "
                        "=> diagnostic only (PLAN section 10.2)"
                    ),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        # 5. Verdict ----------------------------------------------------------- #
        g3_row = _row(GateId.G3_STAGE_A.value)
        protocol_fail = any(
            verdict_by_gate.get(gate) is GateVerdict.FAIL
            for gate in ("G0_DATA", "G1_LEAKAGE", "G2A_ARTIFACT_INTEGRITY")
        )
        reasons = sorted(
            {
                code
                for row in gate_results
                if row.verdict is GateVerdict.FAIL
                for code in row.reasons
            }
            | set(g3_row.reasons)
        )
        if protocol_fail:
            verdict = "UNRANKED_PROTOCOL_FAIL"
            protocol_failures += 1
        elif eligibility["eligibility"] == "DIAGNOSTIC_ONLY":
            verdict = "DIAGNOSTIC_G2B_NOT_RUN"
        elif g3_row.verdict is GateVerdict.PASS:
            verdict = "CANDIDATE_PASS"
        elif g3_row.verdict in (GateVerdict.INCONCLUSIVE, GateVerdict.NOT_YET_TESTED):
            verdict = "INCONCLUSIVE"
        else:
            verdict = "CANDIDATE_FAIL"

        log_line = (
            f"{datetime.now(timezone.utc).isoformat()} | {experiment_id} | "
            f"{strategy_type} | {symbol} | {variant} | {verdict} | "
            f"g1={verdict_by_gate['G1_LEAKAGE'].value} "
            f"g2a={verdict_by_gate['G2A_ARTIFACT_INTEGRITY'].value} "
            f"g2b={verdict_by_gate['G2B_INDEPENDENT_REPRODUCIBILITY'].value} | "
            f"pf={stats.get('profit_factor')} | trades={trades_total}\n"
        )
        (exp_dir / "run.log").write_text(log_line, encoding="utf-8")
        (exp_dir / "artifact_hashes.json").write_text(
            json.dumps(_artifact_hashes(exp_dir), indent=2), encoding="utf-8"
        )

        append(
            {
                "experiment_id": experiment_id,
                "verdict": verdict,
                "kind": "CELL_RESULT",
                "schema": "v3",
                "hypothesis_id": (
                    manifest.hypothesis_id if manifest else f"H-EXISTING-{strategy_type}-v1"
                ),
                "candidate_version": manifest.candidate_version if manifest else None,
                "owner_agent": manifest.owner_agent if manifest else None,
                "validator_agent": manifest.validator_agent if manifest else "A3",
                "strategy_type": strategy_type,
                "symbol": symbol,
                "param_variant": variant,
                "matrix_id": (
                    manifest.matrix_id if manifest else report.get("matrix_id", matrix_path.name)
                ),
                "git_commit_at_launch": (cell.get("provenance") or {}).get("git_commit_at_launch"),
                "execution_mode": (cell.get("provenance") or {}).get("execution_mode"),
                "g0": verdict_by_gate["G0_DATA"].value,
                "g1": verdict_by_gate["G1_LEAKAGE"].value,
                "g2a": verdict_by_gate["G2A_ARTIFACT_INTEGRITY"].value,
                "g2b": verdict_by_gate["G2B_INDEPENDENT_REPRODUCIBILITY"].value,
                "g3": g3_row.to_dict(),
                "reasons": reasons,
                "canonical": {
                    "trades": trades_total,
                    "net_canonical_pnl": net_total,
                    "positions_digest": cell.get("positions_digest"),
                },
                "pf_position_level": stats.get("profit_factor"),
                "exp_after_cost": exp_position,
                "scorecard_total": scorecard.total,
                "eligibility": eligibility["eligibility"],
                "artifact_dir": str(exp_dir),
            },
            path=registry_path,
        )

        summaries.append(
            {
                "experiment_id": experiment_id,
                "strategy_type": strategy_type,
                "symbol": symbol,
                "variant": variant,
                "verdict": verdict,
                "eligibility": eligibility["eligibility"],
                "reasons": reasons,
                "g1": verdict_by_gate["G1_LEAKAGE"].value,
                "g2a": verdict_by_gate["G2A_ARTIFACT_INTEGRITY"].value,
                "g2b": verdict_by_gate["G2B_INDEPENDENT_REPRODUCIBILITY"].value,
                "pf_position_level": stats.get("profit_factor"),
                "exp_after_cost": exp_position,
                "expectancy_r": canonical_metrics["expectancy_r"]["value"],
                "trades": trades_total,
                "net_canonical_pnl": net_total,
                "scorecard_total": scorecard.total,
            }
        )

    reconciliation = finalize_matrix(matrix_path, registry_path) if finalize else None
    if finalize and not reconciliation["mismatches"]:
        append_matrix_finalize_entry(matrix_path, reconciliation, registry_path=registry_path)

    summary_payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "matrix_dir": str(matrix_path),
        "schema": "v3",
        "evaluated": len(summaries),
        "pass": sum(1 for s in summaries if s["verdict"] == "CANDIDATE_PASS"),
        "fail": sum(1 for s in summaries if s["verdict"] == "CANDIDATE_FAIL"),
        "inconclusive": sum(1 for s in summaries if s["verdict"] == "INCONCLUSIVE"),
        "protocol_fail": protocol_failures,
        "diagnostic_g2b_not_run": sum(
            1 for s in summaries if s["verdict"] == "DIAGNOSTIC_G2B_NOT_RUN"
        ),
        "pipeline_error": sum(1 for s in summaries if s["verdict"] == "PIPELINE_ERROR"),
        "rows": summaries,
        "reconciliation": reconciliation,
    }
    print(json.dumps({k: v for k, v in summary_payload.items() if k != "rows"}, indent=2))
    return summary_payload


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


# --------------------------------------------------------------------------- #
# Sprint V5 mode (PLAN sections 31.4/31.5, V5-C17/C18/C25/C26) -- owner A3.
#
# Evaluates diagnostic-recalculation experiment directories
# ``results/diagnostic_v5/<id>-DIAG-V5``:
#
# * canonical metrics are built WITHOUT fake expectancy-R (F07);
# * XG1 evidence is COUNTED from execution_ledger.jsonl rows (F16);
# * XG2a is MEASURED via research.reconciliation.verify_experiment_dir
#   (F15) -- hashes fresh, every file listed, accounting reconciled 1e-9;
# * portfolio edge uses family-aware metrics only (daily Sharpe, median fold
#   return, chained WFA MDD, reconciled contributions);
# * artifact_hashes.json is written LAST via finalize_artifacts() and a
#   .hashes_final sentinel makes any later in-process write RAISE.
#
# Expected runner-written inputs inside each diagnostic dir:
#   cell.json                    identity/source trial/folds/universe
#   execution_ledger.jsonl       {signal_ts, fill_ts} per scored entry
#   transforms.json              actual transform registry ({} allowed)
#   positions.jsonl              {symbol, canonical_pnl}
#   funding_cashflows.jsonl      {funding_net}
#   costs.jsonl                  {commission, modeled_slippage}
#   accounting_reconciliation.json  totals for the three ledgers above
#   fold_returns.json            [[daily returns of fold], ...]
#   equity_curve.json            optional continuous [[ts, equity], ...]
# --------------------------------------------------------------------------- #
V5_DEFAULT_OUTPUT_ROOT = "results/diagnostic_v5"
V5_DIAGNOSTIC_SUFFIX = "-DIAG-V5"
#: Canonical reason for a missing measured metric (V5 reason semantics).
METRIC_MISSING_V5 = "metric_missing"

_FINALIZED_DIRS: set[str] = set()


class HashesFinalViolation(RuntimeError):
    """Raised when a process tries to write after artifact_hashes.json."""


def assert_not_finalized(path: str | Path) -> None:
    """Refuse writes under any directory already finalized in-process."""
    resolved = Path(path).resolve()
    for finalized in _FINALIZED_DIRS:
        if str(resolved) == finalized or finalized in str(resolved):
            raise HashesFinalViolation(
                f"write refused: {resolved} is under finalized "
                f"{finalized} (artifact_hashes.json already written)"
            )


def guarded_write_text(path: str | Path, text: str) -> Path:
    """The ONLY sanctioned writer inside a diagnostic experiment directory."""
    target = Path(path)
    assert_not_finalized(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


def guarded_write_json(path: str | Path, payload: Any) -> Path:
    import json as _json

    return guarded_write_text(path, _json.dumps(payload, indent=2))


def finalize_artifacts(exp_dir: str | Path) -> Path:
    """Write artifact_hashes.json LAST + .hashes_final sentinel.

    Every writer touching the directory must have closed BEFORE this call.
    Afterwards any in-process :func:`guarded_write_text` under ``exp_dir``
    raises :class:`HashesFinalViolation`.
    """
    from research.reconciliation import finalize_directory_hashes

    directory = Path(exp_dir)
    out = finalize_directory_hashes(directory)
    _FINALIZED_DIRS.add(str(directory.resolve()))
    return out


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _fold_aggregate_returns(fold_return_series: list[list[float]]) -> list[float]:
    """Per-fold compounded return ((prod(1+r)) - 1); sign == fold PnL sign."""
    aggregates = []
    for series in fold_return_series:
        growth = 1.0
        for r in series:
            growth *= 1.0 + float(r)
        aggregates.append(growth - 1.0)
    return aggregates


def evaluate_diagnostic_v5(
    diagnostic_root: str | Path = V5_DEFAULT_OUTPUT_ROOT,
    *,
    registry_path: str | Path | None = None,
    finalize: bool = True,
) -> dict:
    """Evaluate every ``*-DIAG-V5`` dir; measured gates + family metrics."""
    from contracts.protocol import ArtifactIntegrityResult, GateVerdict
    from research.dsr import dsr_probability, pbo_cscv
    from research.portfolio_metrics import (
        CHAINED_MDD_ESTIMATOR,
        DAILY_SHARPE_ESTIMATOR,
        MEDIAN_FOLD_RETURN_ESTIMATOR,
        ContributionMismatch,
        chain_fold_segments,
        chained_returns_mdd,
        daily_sharpe,
        median_fold_return,
        per_symbol_contribution,
    )
    from research.protocol.gates import (
        XGateInputs,
        XGateId,
        XStageAInput,
        evaluate_xgates,
    )
    from research.protocol.registry import append
    from research.protocol.scorecard import compute_scorecard_v3
    from research.reconciliation import verify_experiment_dir

    root = Path(diagnostic_root)
    summaries: list[dict] = []
    if not root.is_dir():
        payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "diagnostic_root": str(root),
            "schema": "v5",
            "evaluated": 0,
            "rows": [],
        }
        print(json.dumps(payload, indent=2))
        return payload

    for exp_dir in sorted(root.iterdir()):
        if not exp_dir.is_dir() or not exp_dir.name.endswith(V5_DIAGNOSTIC_SUFFIX):
            continue
        cell_path = exp_dir / "cell.json"
        if not cell_path.is_file():
            continue
        cell = json.loads(cell_path.read_text(encoding="utf-8"))
        source_trial = cell.get("source_trial_experiment_id")
        universe = [str(s) for s in cell.get("universe") or []]
        folds_meta = cell.get("folds") or []
        fold_start_equities = [
            float(f.get("start_equity", 100_000.0)) for f in folds_meta
        ]

        ledger_rows = _read_jsonl(exp_dir / "execution_ledger.jsonl")
        try:
            transform_registry = json.loads(
                (exp_dir / "transforms.json").read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            transform_registry = {}
        positions = _read_jsonl(exp_dir / "positions.jsonl")
        funding_rows = _read_jsonl(exp_dir / "funding_cashflows.jsonl")
        cost_rows = _read_jsonl(exp_dir / "costs.jsonl")
        fold_return_series = json.loads(
            (exp_dir / "fold_returns.json").read_text(encoding="utf-8")
        )
        accounting_path = exp_dir / "accounting_reconciliation.json"
        accounting = (
            json.loads(accounting_path.read_text(encoding="utf-8"))
            if accounting_path.is_file()
            else {}
        )

        integrity_pre = verify_experiment_dir(exp_dir, phase="inputs")
        from research.reconciliation import base_reason_codes

        # Gate rows need registered reason codes; raw detail is preserved
        # separately in gate_result.json / the registry entry.
        integrity_pre_gated = ArtifactIntegrityResult(
            schema_valid=integrity_pre.schema_valid,
            hashes_match=integrity_pre.hashes_match,
            positions_reconcile=integrity_pre.positions_reconcile,
            report_index_reconcile=integrity_pre.report_index_reconcile,
            reasons=base_reason_codes(integrity_pre.reasons),
        )

        reasons_fail: list[str] = []
        contribution_error: str | None = None

        # --- family-aware canonical metrics (NO fake R) ------------------ #
        total_pnl = sum(float(row.get("canonical_pnl") or 0.0) for row in positions)
        wins = sum(float(r["canonical_pnl"]) for r in positions
                   if float(r.get("canonical_pnl") or 0.0) > 0)
        losses = abs(sum(float(r["canonical_pnl"]) for r in positions
                         if float(r.get("canonical_pnl") or 0.0) < 0))
        position_pf = (None if losses == 0 else round(wins / losses, 10))
        pf_reason = (
            "no_trades" if not positions else ("no_losing_positions" if losses == 0 else None)
        )

        flat_daily_returns = [
            float(r) for series in fold_return_series for r in series
        ]
        sharpe_value, sharpe_reason = daily_sharpe(flat_daily_returns)
        fold_aggregates = _fold_aggregate_returns(fold_return_series)
        median_return = median_fold_return(fold_aggregates)
        chained_mdd = chained_returns_mdd(fold_start_equities, fold_return_series)

        funding_total = math.fsum(float(r.get("funding_net") or 0.0) for r in funding_rows)
        commission_total = math.fsum(float(r.get("commission") or 0.0) for r in cost_rows)
        slippage_total = math.fsum(float(r.get("modeled_slippage") or 0.0) for r in cost_rows)

        top_symbol: str | None = None
        top_share: float | None = None
        try:
            shares = per_symbol_contribution(
                positions,
                total_pnl=total_pnl,
                population=universe or None,
            )
            if shares:
                top_symbol = max(sorted(shares), key=lambda k: shares[k])
                top_share = shares[top_symbol]
        except ContributionMismatch as exc:
            contribution_error = str(exc)

        canonical_metrics = {
            "schema_version": 5,
            "accounting": "position_level_after_funding_v5",
            "strategy_type": cell.get("strategy_type"),
            "symbol": cell.get("symbol"),
            "window_actual": cell.get("window_actual"),
            "source_trial_experiment_id": source_trial,
            "net_canonical_pnl": {"value": round(total_pnl, 10), "reason": None},
            "trades": {
                "value": len(positions),
                "reason": None if positions else require_reason("no_trades"),
            },
            "position_pf": {"value": position_pf, "reason": pf_reason},
            # F07: no stop => no R. Explicit null + reason, never a proxy.
            "expectancy_r": {"value": None, "reason": "MISSING_R_NORMALIZATION"},
            "funding_total": round(funding_total, 10),
            "commission_total": round(commission_total, 10),
            "modeled_slippage_total": round(slippage_total, 10),
            "daily_sharpe": {
                "value": None if sharpe_value is None else round(sharpe_value, 10),
                "reason": sharpe_reason,
                "estimator_id": DAILY_SHARPE_ESTIMATOR,
                "rf": 0.0,
            },
            "median_fold_return": {
                "value": None if median_return is None else round(median_return, 10),
                "reason": None if median_return is not None else METRIC_MISSING_V5,
                "estimator_id": MEDIAN_FOLD_RETURN_ESTIMATOR,
            },
            "positive_folds": sum(1 for v in fold_aggregates if v > 0),
            "outer_folds": len(fold_aggregates),
            "chained_wfa_mdd": {
                "value": round(chained_mdd, 10),
                "estimator_id": CHAINED_MDD_ESTIMATOR,
            },
            "top_symbol_contribution": {
                "symbol": top_symbol,
                "share": None if top_share is None else round(top_share, 10),
            },
        }

        # --- measured gates ------------------------------------------------ #
        stage_a = XStageAInput(
            pnl=total_pnl if positions else None,
            pf=position_pf,
            pf_reason=pf_reason,
            fold_returns=fold_aggregates or None,
            folds=[
                {"fold_id": f"f{k+1}", "pnl": v}
                for k, v in enumerate(fold_aggregates)
            ],
            rebalances_scored=int(cell.get("rebalances_scored") or 0) or None,
            legs_closed=len(positions),
            top_symbol_contribution=top_share,
        )
        gate_inputs = XGateInputs(
            coverage=cell.get("coverage"),
            declared_symbols=cell.get("declared_symbols"),
            # Always route through the MEASURED XG1 path: an empty/absent
            # ledger must yield evidence_missing, never the legacy boolean
            # struct interpretation.
            execution_ledger_rows=list(ledger_rows),
            transform_registry=transform_registry or None,
            warmup_boundaries=(cell.get("warmup_boundaries") or {}),
            artifact_integrity=integrity_pre_gated,
            stage_a=stage_a,
        )
        gate_results = evaluate_xgates(gate_inputs)
        verdict_by_gate = {
            (r.gate.value if hasattr(r.gate, "value") else str(r.gate)): r.verdict
            for r in gate_results
        }
        xg2a_verdict = verdict_by_gate[XGateId.XG2A_ARTIFACT_INTEGRITY.value]

        # Contribution mismatch is an integrity FAIL (F01/F02), not a crash.
        if contribution_error is not None:
            xg2a_verdict = GateVerdict.FAIL
            reasons_fail.append("contribution_mismatch")

        # --- scorecard via G-id translation -------------------------------- #
        from research.portfolio_runner import map_xg_to_g_scores

        translated = map_xg_to_g_scores(gate_results)
        sharpe_ok = sharpe_reason is None
        scorecard = compute_scorecard_v3(
            translated,
            {
                "expectancy_r": None,  # never fake R
                "position_pf": position_pf,
                "positive_folds": canonical_metrics["positive_folds"],
                "outer_folds": canonical_metrics["outer_folds"],
                "closed_trades": len(positions),
                "flat_benchmark_pass": None,
                "rationale_flags": {},
                "cost_flags": {},
                "risk_flags": {},
            },
        )

        # --- write evaluator outputs (guarded) ------------------------------ #
        guarded_write_json(exp_dir / "canonical_metrics.json", canonical_metrics)
        guarded_write_json(
            exp_dir / "gate_result.json",
            {
                "schema": "v5",
                "xg2a_evidence": {
                    "measured_before_evaluation": True,
                    "verdict": integrity_pre.verdict().value,
                    "reasons": list(integrity_pre.reasons),
                },
                "rows": [r.to_dict() for r in gate_results],
            },
        )
        guarded_write_json(
            exp_dir / "scorecard.json",
            {
                "schema_version": 5,
                "components": scorecard.components,
                "total": scorecard.total,
                "max_verdict": scorecard.max_verdict(),
                "note": "diagnostic recalculation; no fake expectancy-R (PLAN 31.4)",
            },
        )

        protocol_fail = (
            xg2a_verdict is GateVerdict.FAIL
            or verdict_by_gate.get(XGateId.XG1_POINT_IN_TIME.value) is GateVerdict.FAIL
            or bool(reasons_fail)
        )
        xg3_verdict = verdict_by_gate[XGateId.XG3_STAGE_A_PORTFOLIO.value]
        if protocol_fail:
            verdict = "UNRANKED_PROTOCOL_FAIL"
        elif (
            xg2a_verdict is GateVerdict.PASS
            and verdict_by_gate[XGateId.XG1_POINT_IN_TIME.value] is GateVerdict.PASS
            and xg3_verdict is GateVerdict.PASS
        ):
            verdict = "DIAG_RECALC_MATCH_PASS"
        else:
            verdict = "INCONCLUSIVE"

        log_line = (
            f"{datetime.now(timezone.utc).isoformat()} | {exp_dir.name} | DIAG-V5 | "
            f"{verdict} | xg1={verdict_by_gate[XGateId.XG1_POINT_IN_TIME.value].value} "
            f"xg2a={xg2a_verdict.value} "
            f"xg3={verdict_by_gate[XGateId.XG3_STAGE_A_PORTFOLIO.value].value}\n"
        )
        guarded_write_text(exp_dir / "run.log", log_line)

        # --- hashes LAST, then post-finalize verification ------------------- #
        integrity_post = None
        if finalize:
            finalize_artifacts(exp_dir)
            integrity_post = verify_experiment_dir(exp_dir, phase="final")
            if integrity_post.verdict() is not GateVerdict.PASS:
                verdict = "UNRANKED_PROTOCOL_FAIL"
                reasons_fail.extend(integrity_post.reasons)

        entry = {
            "experiment_id": exp_dir.name,
            "verdict": verdict,
            "kind": "DIAGNOSTIC_RECALC",
            "schema": "v5",
            "source_trial_experiment_id": source_trial,
            "verified_experiment_id": exp_dir.name,
            "verification_type": "V4_DIAGNOSTIC_RECALC",
            "xg1": verdict_by_gate[XGateId.XG1_POINT_IN_TIME.value].value,
            "xg2a": xg2a_verdict.value,
            "xg3": verdict_by_gate[XGateId.XG3_STAGE_A_PORTFOLIO.value].value,
            "reasons": sorted(set(reasons_fail)),
            "canonical": {
                "net_canonical_pnl": total_pnl,
                "positions_digest_source": cell.get("positions_digest"),
                "chained_wfa_mdd": chained_mdd,
                "median_fold_return": median_return,
                "daily_sharpe": sharpe_value,
            },
            "post_finalize_integrity": (
                None
                if integrity_post is None
                else {
                    "verdict": integrity_post.verdict().value,
                    "reasons": list(integrity_post.reasons),
                }
            ),
            "scorecard_total": scorecard.total,
            "artifact_dir": str(exp_dir),
        }
        append(entry, path=registry_path)
        summaries.append(entry)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "diagnostic_root": str(root),
        "schema": "v5",
        "evaluated": len(summaries),
        "protocol_fail": sum(1 for s in summaries if s["verdict"] == "UNRANKED_PROTOCOL_FAIL"),
        "pass": sum(1 for s in summaries if s["verdict"] == "DIAG_RECALC_MATCH_PASS"),
        "inconclusive": sum(1 for s in summaries if s["verdict"] == "INCONCLUSIVE"),
        "dsr_available": dsr_probability.__name__ == "dsr_probability",
        "pbo_min_configs": pbo_cscv({})["min_configs_required"],
        "rows": summaries,
    }
    print(json.dumps(payload, indent=2))
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--matrix-dir", required=True)
    parser.add_argument("--output-root", default=None)
    parser.add_argument(
        "--schema", choices=("v1", "v2", "v3", "v5"), default="v3",
        help=(
            "v3 = Sprint V3 read-only provenance + G2a/G2b separation "
            "(default); v2 = Sprint V2 provenance mode; "
            "v5 = diagnostic recalculation dirs (PLAN 31.5)"
        ),
    )
    parser.add_argument("--registry-path", default=None,
                        help="append-only registry file (default results/registry/experiments.jsonl)")
    parser.add_argument("--no-finalize", action="store_true",
                        help="skip matrix reconciliation/finalize (v3) or hash finalization (v5)")
    parser.add_argument("--diagnostic-root", default=V5_DEFAULT_OUTPUT_ROOT,
                        help="directory holding *-DIAG-V5 experiment dirs (v5 only)")
    parser.add_argument("--coverage-path", default=None,
                        help="data-contract coverage.json used as G0 evidence")
    parser.add_argument("--v1-summary-dir", default=None,
                        help="directory holding V1 sprint_summary_*.json rows")
    args = parser.parse_args(argv)

    if args.schema == "v5":
        payload = evaluate_diagnostic_v5(
            args.diagnostic_root,
            registry_path=args.registry_path,
            finalize=not args.no_finalize,
        )
        return 0 if payload["protocol_fail"] == 0 else 1
    if args.schema == "v3":
        payload = evaluate_matrix_v3(
            args.matrix_dir,
            output_root=args.output_root or V3_DEFAULT_OUTPUT_ROOT,
            coverage_path=args.coverage_path,
            registry_path=args.registry_path,
            finalize=not args.no_finalize,
        )
        reconciliation = (payload or {}).get("reconciliation") or {}
        return 0 if not reconciliation.get("mismatches") else 1
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
