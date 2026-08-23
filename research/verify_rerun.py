"""Sprint-24h independent verification (G2) for matrix-produced experiments (A1).

Re-executes the exact CellPlan recorded for an experiment and compares the
fresh artifact against the original: trades count, net PnL after funding
(relative tol 1e-6) and a deterministic digest of the fold rows.

Usage:
    python -m research.verify_rerun --experiment-id EXP-20260823-0049 \
        --matrix-dir results/matrix/stage_a_s0_20260823
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from contracts.protocol import (
    GateId,
    GateResult,
    GateVerdict,
    canonical_json,
    sha256_text,
)


def _find_cell_artifact(matrix_dir: Path, strategy_type: str, symbol: str, variant: str) -> Path | None:
    index = json.loads((matrix_dir / "index.json").read_text(encoding="utf-8"))
    for entry in index.get("cells", {}).values():
        ident = entry.get("identity", {})
        if (
            ident.get("strategy_type") == strategy_type
            and ident.get("symbol") == symbol
            and ident.get("param_variant", "base") == variant
            and entry.get("status") == "COMPLETED"
        ):
            path = Path(entry["artifact_path"])
            if path.exists():
                return path
    return None


def verify_rerun(matrix_dir: str, strategy_type: str, symbol: str, variant: str = "base",
                 *, folds: int = 3) -> tuple[GateResult, dict]:
    from research.matrix_runner import execute_cell, make_plan

    matrix_path = Path(matrix_dir)
    original_path = _find_cell_artifact(matrix_path, strategy_type, symbol, variant)
    if original_path is None:
        return (
            GateResult(GateId.G2_REPRODUCIBILITY, GateVerdict.NOT_YET_TESTED,
                       ("metric_not_computed",)),
            {},
        )
    original = json.loads(original_path.read_text(encoding="utf-8"))
    plan_doc = original["plan"]
    window_start = pd.Timestamp(plan_doc["window_declared"]["start_utc"])
    window_end = pd.Timestamp(plan_doc["window_declared"]["end_utc"])

    plan = make_plan(
        strategy_type,
        symbol,
        tier=plan_doc.get("tier", 1),
        folds=plan_doc.get("folds", folds),
        window_start=window_start,
        window_end=window_end,
        catalog_path=plan_doc.get("catalog_path", "./catalog_live_crypto"),
        funding_path=plan_doc.get("funding_path", "funding_data/scan_2026"),
        param_variant=variant,
    )

    hash_ok = plan.config_sha256 == original["identity"]["config_sha256"]
    fresh = execute_cell(plan)

    trades_match = int(fresh["total_trades"]) == int(original["total_trades"])
    orig_pnl = float(original.get("pnl_after_funding") or 0.0)
    fresh_pnl = float(fresh.get("pnl_after_funding") or 0.0)
    denom = max(1.0, abs(orig_pnl))
    pnl_match = abs(fresh_pnl - orig_pnl) / denom <= 1e-6

    def _digest(doc: dict) -> str:
        payload = [
            {k: f.get(k) for k in ("fold", "trades", "trades_after_funding", "pnl", "pnl_after_funding")}
            for f in doc["folds"]
        ]
        return sha256_text(canonical_json(payload))

    digest_match = _digest(fresh) == _digest(original)

    reasons: list[str] = []
    if not hash_ok:
        reasons.append("hash_mismatch")
    if not trades_match:
        reasons.append("rerun_positions_mismatch")
    if not pnl_match:
        reasons.append("rerun_pnl_mismatch")
    if not digest_match:
        reasons.append("rerun_positions_mismatch")

    verdict = GateVerdict.PASS if not reasons else GateVerdict.FAIL
    details = {
        "strategy_type": strategy_type,
        "symbol": symbol,
        "param_variant": variant,
        "config_hash_match": hash_ok,
        "trades_original": int(original["total_trades"]),
        "trades_rerun": int(fresh["total_trades"]),
        "pnl_after_funding_original": orig_pnl,
        "pnl_after_funding_rerun": fresh_pnl,
        "fold_digest_match": digest_match,
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    return GateResult(GateId.G2_REPRODUCIBILITY, verdict, tuple(reasons)), details


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--matrix-dir", required=True)
    parser.add_argument("--strategy-type", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--variant", default="base")
    args = parser.parse_args(argv)

    result, details = verify_rerun(args.matrix_dir, args.strategy_type, args.symbol, args.variant)
    print(json.dumps({"g2": result.to_dict(), **details}, indent=2))

    from research.protocol.registry import append

    append(
        {
            "experiment_id": f"VERIFY-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}",
            "verdict": f"G2_{result.verdict.value}",
            "verified_experiment": {
                "strategy_type": args.strategy_type,
                "symbol": args.symbol,
                "param_variant": args.variant,
                "matrix_dir": args.matrix_dir,
            },
            "reasons": list(result.reasons),
            **details,
        }
    )
    return 0 if result.verdict == GateVerdict.PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
