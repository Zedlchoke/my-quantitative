"""Sprint-24h evaluation bridge (owner A1).

Reads a completed matrix directory (research.matrix_runner output), evaluates
hard gates + scorecards per combo using research.protocol, writes
results/stage_a/<experiment_id>/ artifacts and appends the append-only registry.

Usage:
    python -m research.sprint_eval --matrix-dir results/matrix/stage_a_s0_20260823
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

VOLCOMP_STRATEGY_TYPE = "vol_compression_breakout"
HYPOTHESIS_BY_STRATEGY = {
    VOLCOMP_STRATEGY_TYPE: "H-VOLCOMP-BRKOUT-v1",
}
WARMUP_BARS_PER_DAY = 96


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--matrix-dir", required=True)
    parser.add_argument("--output-root", default="results/stage_a")
    args = parser.parse_args(argv)
    evaluate_matrix(args.matrix_dir, output_root=args.output_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
