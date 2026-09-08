"""V10 Q-phase exact-arm sanitized dry-run driver (A1).

Runs all six frozen arms in dry-run mode (outcome-blind), enforces binding
non-vacuity gates, the recursive leak scan, byte-identical determinism and
the zero-denominator-delta rule, and writes
research/control/stocks_free_v10_run/q_dryrun_evidence_v10.json.

NO PnL, NO returns, NO metrics may appear in any record or this file.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

from research.assets.stocks import v10_family_runner as vfr
from research.assets.stocks.v9_family_runner import (
    FOLDS,
    fold_sessions,
    load_prices,
    load_universe,
)

CONTROL = Path(__file__).resolve().parents[2] / "control/stocks_free_v10_run"
EVIDENCE = CONTROL / "q_dryrun_evidence_v10.json"
LEAK_KEYS = {"pnl", "return", "returns", "alpha", "sharpe", "pf",
             "expectancy", "profit", "sum_pnl", "metrics", "mdd"}
SAMPLING_FLOOR = 0.25          # populated_frac floor (V9 convention)
MIN_SCORED_DECISIONS = 30
MIN_PER_FOLD = 5


def walk_leak(node, path="root", findings=None):
    findings = [] if findings is None else findings
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(k, str) and k.lower() in LEAK_KEYS:
                findings.append(f"{path}.{k}")
            walk_leak(v, f"{path}.{k}", findings)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk_leak(v, f"{path}[{i}]", findings)
    return findings


def arm_folds(prices, universe):
    uni_prices = {k: v for k, v in prices.items() if k in universe}
    return fold_sessions(uni_prices if len(uni_prices) >= 10 else prices)


def main() -> int:
    t0 = time.time()
    print("[q] loading layers/prices/universe...", flush=True)
    timing = vfr.load_timing_layer()
    revision = vfr.load_revision_layer()
    prices = load_prices()
    universe = load_universe()
    cohort = json.load(open(
        Path(vfr.__file__).resolve().parents[2] / "control/stocks_free_v9_run/cohort_v9.json"))
    sectors = {m["cik"]: m.get("sector", "")
               for cls in ("ALIVE_EVIDENCED", "DEAD_EVIDENCED")
               for m in cohort["members"][cls]}
    folds = arm_folds(prices, universe)
    print(f"[q] entities={len(universe)} fold_sessions="
          f"{[len(f['sessions']) for f in folds]}", flush=True)

    layer_digest = hashlib.sha256(
        (vfr.TIMING_PATH.name + vfr.REVISION_PATH.name).encode()).hexdigest()
    price_manifest = CONTROL.parent / "stocks_free_v9_run/p0d_v9_price_manifest.json"
    price_manifest_sha = hashlib.sha256(price_manifest.read_bytes()).hexdigest()

    arms = {}
    all_pass = True
    for arm_id in vfr.ARM_SPECS:
        runs = []
        for rep in (1, 2):
            rec = vfr.run_arm(
                arm_id, timing, revision, prices, folds, dry_run=True,
                universe=universe, sectors=sectors,
                price_manifest_sha=price_manifest_sha,
                layer_digest=layer_digest, code_freeze_sha="Q_DRY_RUN")
            runs.append(json.dumps(rec, sort_keys=True))
        byte_identical = runs[0] == runs[1]
        rec = json.loads(runs[0])
        leaks = walk_leak(rec)
        # non-vacuity on the scored (non-warmup) decision records
        decisions = [x for x in rec["schedule"] if x.get("event") is None]
        scored = [x for x in decisions if not x["warmup"]]
        per_fold = {}
        for f in FOLDS:
            per_fold[f["fold_id"]] = sum(
                1 for x in scored if x["fold"] == f["fold_id"] and x["legs"] > 0)
        frac_ok = sum(1 for x in scored if x["populated_frac"] >= SAMPLING_FLOOR)
        checks = {
            "byte_identical_x2": byte_identical,
            "leak_scan_findings": leaks,
            "scored_decisions_ge_30": len(scored) >= MIN_SCORED_DECISIONS,
            "per_fold_scored_legs_ge_5": all(v >= MIN_PER_FOLD for v in per_fold.values()),
            "any_noncash_leg_every_scored_decision": all(x["legs"] > 0 for x in scored),
            "populated_frac_floor_90pct": (
                frac_ok >= 0.9 * len(scored) if scored else False),
        }
        passed = (byte_identical and not leaks
                  and checks["scored_decisions_ge_30"]
                  and checks["per_fold_scored_legs_ge_5"]
                  and checks["any_noncash_leg_every_scored_decision"]
                  and checks["populated_frac_floor_90pct"])
        all_pass = all_pass and passed
        arms[arm_id] = {
            "nonvacuity": {
                "scored_decisions": len(scored),
                "per_fold_scored_legs": per_fold,
                "populated_frac_ge_floor": frac_ok,
                "scored_total": checks["scored_decisions_ge_30"],
                "folds_total": checks["per_fold_scored_legs_ge_5"],
                "legs_total": checks["any_noncash_leg_every_scored_decision"],
                "floor_total": checks["populated_frac_floor_90pct"],
            },
            "byte_identical_x2": byte_identical,
            "leak_scan_findings": leaks,
            "void_entry_orders": rec["void_entry_orders"],
            "terminations": rec["terminations"],
            "verdict": "PASS" if passed else "FAIL",
        }
        print(f"[q] {arm_id}: {arms[arm_id]['verdict']} "
              f"scored={len(scored)} per_fold={per_fold}", flush=True)

    evidence = {
        "schema": "stocks_free_v10_run/q_dryrun_evidence@1",
        "built_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "producer_role": "A1 (PLAN_stocks_v10 sec3 Q exact-arm sanitized dry-run)",
        "discipline": "scored=false everywhere; no PnL/returns/metrics in any record; byte-identical x2 per arm; zero denominator delta (no publication record written by the dry-run)",
        "sampling_floor": SAMPLING_FLOOR,
        "min_scored_decisions": MIN_SCORED_DECISIONS,
        "min_per_fold": MIN_PER_FOLD,
        "arms": arms,
        "verdict": "DRY_RUN_PASS_NONVACUOUS" if all_pass else "DRY_RUN_FAIL",
        "runtime_seconds": round(time.time() - t0, 1),
    }
    EVIDENCE.write_text(json.dumps(evidence, indent=1) + "\n")
    print(f"[q] verdict={evidence['verdict']} written {EVIDENCE}", flush=True)
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
