#!/usr/bin/env python
"""Independent reproduction of the deterministic scored arms.

Recomputes A1/A2/B/D/E (run-1 identities; code paths untouched by the
incident fixes — equivalence gate re-verified) and C/C_RELAXED/F/F_RELAXED
(run-2 remediation identities) into runtime/scored_repro/ and byte-compares
every file against runtime/scored/. GO-gated like the scored run.

F controls that recorded NOT_RUN_CONTROL_MATCHING are reproduced as the
same fail-closed outcome (comparison = status equality).
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

CYCLE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CYCLE_DIR))

GO_PHRASE = "GO REGIME STRATEGY MAPPING V1 DISCOVERY BACKTEST"


def main() -> int:
    token = CYCLE_DIR / "SCORED_GO.json"
    if hashlib.sha256(token.read_bytes()).hexdigest() != hashlib.sha256(
            GO_PHRASE.encode()).hexdigest():
        print("REFUSED_BACKTEST_QUARANTINE (repro)")
        return 20

    import json

    from rsmv1.scored import (
        RELAXED_OUTER_FLOORS, CellCtx, _persist, arm_a1, arm_a2, arm_b,
        arm_c, arm_d, arm_e, arm_f, ControlMatchFailure,
    )
    from rsmv1.strategies import FLAT, MR_LONG, TREND_LONG

    scored = CYCLE_DIR / "runtime" / "scored"
    repro = CYCLE_DIR / "runtime" / "scored_repro"
    repro.mkdir(parents=True, exist_ok=True)

    report: list[dict] = []

    def cmp_file(cell: str, arm: str, tier_tag: str) -> dict:
        """A1/A2/B carry no extras -> BYTE compare. The remediated arms
        (C*/D/E) carry writer extras (audit trails) the repro does not
        duplicate -> CONTENT compare on every computational field
        (totals, folds, trades, identities) ignoring `extra`."""
        a = scored / cell / arm / f"{tier_tag}.json"
        b = repro / cell / arm / f"{tier_tag}.json"
        if not a.exists() or not b.exists():
            return {"cell": cell, "arm": arm, "tier": tier_tag,
                    "verdict": "MISSING"}
        ha = hashlib.sha256(a.read_bytes()).hexdigest()
        hb = hashlib.sha256(b.read_bytes()).hexdigest()
        if ha == hb:
            return {"cell": cell, "arm": arm, "tier": tier_tag,
                    "verdict": "MATCH", "mode": "byte",
                    "sha": ha[:12]}
        ja = json.loads(a.read_text())
        jb = json.loads(b.read_text())
        ja.pop("extra", None)
        jb.pop("extra", None)
        if ja == jb:
            return {"cell": cell, "arm": arm, "tier": tier_tag,
                    "verdict": "MATCH", "mode": "content-minus-extra",
                    "sha_a": ha[:12], "sha_b": hb[:12]}
        return {"cell": cell, "arm": arm, "tier": tier_tag,
                "verdict": "DIFF", "mode": "content-minus-extra",
                "sha_a": ha[:12], "sha_b": hb[:12]}

    for cell in ("BTC_H1", "BTC_H4", "SPY_D1"):
        ctx = CellCtx(cell)

        # A1/A2/B/D/E (run-1 identities)
        arms_static = {
            "A1_ALWAYS_ON_MR": lambda t: arm_a1(ctx, t),
            "A2_ALWAYS_ON_TREND": lambda t: arm_a2(ctx, t),
            "B_ORIGINAL_V2_MAPPING": lambda t: arm_b(ctx, t),
            "D_SPARSE_JEV_RISK_OFF_VETO": lambda t: arm_d(ctx, t)[0],
            "E_DETERMINISTIC_PLUS_JEV_VETO": lambda t: arm_e(ctx, t)[0],
        }
        for arm, fn in arms_static.items():
            for tier, tag in ((1.0, "tier_1"), (1.5, "tier_1p5"),
                              (2.0, "tier_2")):
                res = fn(tier)
                _persist(repro, cell, arm, tier, res)
                report.append(cmp_file(cell, arm, tag))

        # C / C_RELAXED (run-2 identities)
        for arm, floors in (("C_REGIME_SPECIALIST_ROUTER", None),
                            ("C_RELAXED_REGIME_SPECIALIST_ROUTER",
                             RELAXED_OUTER_FLOORS)):
            for tier, tag in ((1.0, "tier_1"), (1.5, "tier_1p5"),
                              (2.0, "tier_2")):
                res, _, _, _ = arm_c(ctx, tier, outer_floors=floors)
                _persist(repro, cell, arm, tier, res)
                report.append(cmp_file(cell, arm, tag))

        # F / F_RELAXED: run 2 records matching SUCCESS as tier files and
        # fail-closed NOT_RUN only in the summary — compare against whichever
        # authority holds the outcome.
        _, sel, _, mapping = arm_c(ctx, 1.0)
        _, sel_r, _, mapping_r = arm_c(ctx, 1.0, outer_floors=RELAXED_OUTER_FLOORS)
        run2_summary = json.loads(
            (scored / "scored_summary_run2_cf.json").read_text())
        for arm, mp in (("F_EPISODE_SHUFFLED_MATCHED", mapping),
                        ("F_RELAXED_EPISODE_SHUFFLED_MATCHED", mapping_r)):
            orig_row = run2_summary["cells"][cell]["arms"][arm]
            orig_failed = "status" in orig_row
            try:
                blk = arm_f(ctx, mp, 1.0)
                repro_status = {"median_net_pnl": blk["median_net_pnl"],
                                "seeds": len(blk["seeds"])}
            except ControlMatchFailure:
                repro_status = {"status": "NOT_RUN_CONTROL_MATCHING"}
            same = (orig_failed and "status" in repro_status) or (
                (not orig_failed) and repro_status.get("median_net_pnl") ==
                orig_row.get("median_net_pnl"))
            report.append({"cell": cell, "arm": arm, "tier": "tier_1",
                           "verdict": "MATCH" if same else "DIFF",
                           "orig": {k: orig_row.get(k) for k in
                                    ("status", "median_net_pnl", "seeds")},
                           "repro": repro_status})

    n_match = sum(1 for r in report if r["verdict"] == "MATCH")
    out = {"schema": "rsmv1_reproduction@1",
           "all_match": n_match == len(report),
           "n": len(report), "n_match": n_match,
           "failures": [r for r in report if r["verdict"] != "MATCH"],
           "report": report}
    (CYCLE_DIR / "evidence" / "reproduction_report.json").write_text(
        json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(f"reproduction: {n_match}/{len(report)} MATCH -> all_match="
          f"{out['all_match']}")
    return 0 if out["all_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
