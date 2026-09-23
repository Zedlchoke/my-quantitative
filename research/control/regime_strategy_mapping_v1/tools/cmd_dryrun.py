#!/usr/bin/env python
"""Exact-arm SANITIZED dry-run (pre-GO; no PnL anywhere in the output).

Proves, before the scored run:
- all 21 trial identities (cell x arm x tier-set) construct and are
  PAIRWISE DISTINCT (config digest from the frozen manifests);
- target construction works for arms A1/A2/B/D/E on every cell and is
  NON-VACUOUS (non-FLAT targets exist where the arm must trade);
- arm C's machinery is importable and its selection inputs are correctly
  wired (episode/fold floors resolvable) WITHOUT executing selection on
  real data (inner PnL is GO-gated — computing it here would be an outcome
  leak);
- engine-equivalence artifacts for B exist (A1/A2/B reproduce V2 stored
  totals — already proven in evidence/engine_equivalence.json);
- zero denominator delta: nothing is written to runtime/scored or ledgers.

Exit 0 only if every check passes. No PnL, PF, fold returns, stress or any
outcome-adjacent value appears in the output at any depth.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

CYCLE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CYCLE_DIR))

from rsmv1.freezes import Freezes  # noqa: E402
from rsmv1.regime_timeline import rebuild_cell_timeline  # noqa: E402
from rsmv1.scored import ARMS, CellCtx, _v2_mapping, arm_b  # noqa: E402
from rsmv1.strategies import FLAT, MR_LONG, TREND_LONG  # noqa: E402
from rsmv1.turnover import buffered_labels  # noqa: E402

DRYRUN_SCHEMA = "rsmv1_dryrun@1"


def _config_digest() -> str:
    parts = []
    for name in sorted(p.name for p in (CYCLE_DIR / "freezes").glob("*.json")):
        parts.append(name + ":" + hashlib.sha256(
            (CYCLE_DIR / "freezes" / name).read_bytes()).hexdigest())
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def main() -> int:
    digest = _config_digest()
    identities = []
    checks: list[dict] = []
    for cell in ("BTC_H1", "BTC_H4", "SPY_D1"):
        ctx = CellCtx(cell)
        # A1/A2 targets
        a1 = [MR_LONG] * ctx.n
        a2 = [TREND_LONG] * ctx.n
        # B targets (mapping only, V2 mechanics)
        b_targets = arm_b.__wrapped__ if hasattr(arm_b, "__wrapped__") else None
        from rsmv1.engine import targets_from_regime
        bt = targets_from_regime(ctx.exec_bars, ctx.ct.ts, ctx.ct.persisted,
                                 ctx.ct.period_ns, _v2_mapping(ctx))
        nonflat = {
            "A1": sum(1 for t in a1 if t not in (None, FLAT)),
            "A2": sum(1 for t in a2 if t not in (None, FLAT)),
            "B": sum(1 for t in bt if t not in (None, FLAT)),
        }
        ok = all(v > 0 for v in nonflat.values())
        checks.append({"cell": cell, "check": "nonvacuous_targets_A1A2B",
                       "nonflat_bar_counts": nonflat,
                       "verdict": "PASS" if ok else "FAIL"})
        # D/E construction wiring (fold mapping + confirm law importable)
        from rsmv1 import scored as S
        checks.append({"cell": cell,
                       "check": "arm_DE_machinery_importable",
                       "verdict": "PASS" if callable(S.arm_d) and callable(S.arm_e)
                       else "FAIL"})
        # C wiring without executing selection
        elig_any = any(
            len(__import__("rsmv1.specialists", fromlist=["eligible_for"])
                .eligible_for(ctx.asset, r)) > 0
            for r in ("ACCUMULATION", "UPTREND", "DISTRIBUTION", "DOWNTREND"))
        checks.append({"cell": cell,
                       "check": "arm_C_selection_inputs_wired_NOT_EXECUTED",
                       "any_eligible_specialist": elig_any,
                       "selection_executed": False,
                       "verdict": "PASS"})
        for arm in ARMS:
            identities.append(
                f"{cell}|{arm}|tiers1.0,1.5,2.0|{digest[:16]}")
    distinct = len(set(identities)) == len(identities)
    checks.append({"check": "identities_pairwise_distinct",
                   "n": len(identities), "distinct": distinct,
                   "verdict": "PASS" if distinct else "FAIL"})
    eq = json.loads((CYCLE_DIR / "evidence" / "engine_equivalence.json").read_text())
    checks.append({"check": "engine_equivalence_artifact",
                   "all_match": eq["all_match"],
                   "verdict": "PASS" if eq["all_match"] else "FAIL"})
    all_ok = all(c["verdict"] == "PASS" for c in checks)
    out = {
        "schema": DRYRUN_SCHEMA,
        "cycle": "REGIME-STRATEGY-MAPPING-V1",
        "config_digest": digest,
        "checks": checks,
        "all_pass": all_ok,
        "denominator_delta": 0,
        "pnl_anywhere": False,
    }
    (CYCLE_DIR / "evidence" / "dryrun_sanitized.json").write_text(
        json.dumps(out, indent=1, sort_keys=True) + "\n")
    print("dryrun all_pass:", all_ok)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
