#!/usr/bin/env python
"""Remediation run 2 (RSMV1-INC-1): recompute ONLY arms C/C_RELAXED/F/
F_RELAXED after the direction-dispatch bug fix; preserve run-1 artifacts.

Law (CLAUDE.md §24 bug-after-scoring): run-1 outcomes are NOT deleted and
NOT edited — C*/F* run-1 files move to runtime/scored_run1_invalid/ with
byte preservation; the observed denominator keeps counting them
(classified INVALID_DIRECTION_DISPATCH_BUG); run 2 is a NEW identity
(remediation of INC-1) adding 12 scored cells. Arms A1/A2/B/D/E are
unchanged by the fix (V2-name dispatch identical; engine equivalence
re-verified MATCH immediately before this run).

GO-gated: refuses without the same token as cmd_scored.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

CYCLE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CYCLE_DIR))

GO_PHRASE = "GO REGIME STRATEGY MAPPING V1 DISCOVERY BACKTEST"
TOKEN = CYCLE_DIR / "SCORED_GO.json"
RUN1_INVALID = CYCLE_DIR / "runtime" / "scored_run1_invalid"

CF_ARMS = ["C_REGIME_SPECIALIST_ROUTER", "C_RELAXED_REGIME_SPECIALIST_ROUTER"]


def main() -> int:
    if not TOKEN.exists() or hashlib.sha256(TOKEN.read_bytes()).hexdigest() != \
            hashlib.sha256(GO_PHRASE.encode()).hexdigest():
        print("REFUSED_BACKTEST_QUARANTINE (remediation run 2)")
        return 20

    from rsmv1.scored import (
        RELAXED_OUTER_FLOORS, CellCtx, V2_JEV_TRADE_PINS, _persist,
        _run_engine, arm_c, arm_d, arm_e, arm_f, ControlMatchFailure,
    )
    from rsmv1.strategies import FLAT

    out_root = CYCLE_DIR / "runtime" / "scored"

    # 1) preserve run-1 C*/F*/D/E artifacts byte-exact (C*/F* invalid per
    #    INC-1; D/E superseded: run-1 used the pre-INC-1b fixed-point
    #    routing; the final report must use ONE routing law)
    RUN1_INVALID.mkdir(parents=True, exist_ok=True)
    for cell in ("BTC_H1", "BTC_H4", "SPY_D1"):
        src = out_root / cell
        dst = RUN1_INVALID / cell
        dst.mkdir(parents=True, exist_ok=True)
        for arm in CF_ARMS + ["F_EPISODE_SHUFFLED_MATCHED",
                              "F_RELAXED_EPISODE_SHUFFLED_MATCHED",
                              "D_SPARSE_JEV_RISK_OFF_VETO",
                              "E_DETERMINISTIC_PLUS_JEV_VETO"]:
            if not (src / arm).exists():
                continue
            t1 = src / arm / "tier_1.json"
            is_run1 = True
            if t1.exists():
                try:
                    if json.loads(t1.read_text()).get(
                            "extra", {}).get("run_identity"):
                        is_run1 = False
                except Exception:
                    pass
            if is_run1:
                shutil.move(str(src / arm), str(dst / arm))
            else:
                # earlier remediation output (deterministic rewrite coming)
                shutil.rmtree(src / arm)
    shutil.copy(out_root / "scored_summary.json",
                RUN1_INVALID / "scored_summary_run1.json")

    summary: dict = {
        "schema": "rsmv1_scored_remediation_run2@1",
        "cycle": "REGIME-STRATEGY-MAPPING-V1",
        "remediation_of": "RSMV1-INC-1 direction-dispatch bug (see "
                          "incidents/incident_run1.json)",
        "started_at_utc": datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"),
        "cells": {},
        "trial_accounting": {
            "run1_observed": 27,
            "run1_valid": 15,
            "run1_invalid_c_f": 12,
            "run2_observed_cf": 0,
            "total_observed_all_runs": 27,
        },
    }
    observed2 = 0
    for cell in ("BTC_H1", "BTC_H4", "SPY_D1"):
        ctx = CellCtx(cell)
        cell_blk: dict = {"arms": {}}

        res_c, sel_audit, route_report, mapping = arm_c(ctx, 1.0)
        turnover = {
            "v2_jev_only_trade_pin": V2_JEV_TRADE_PINS[cell],
            "arm_c_trades": res_c.totals["trades"],
            "verdict": "PASS"
            if res_c.totals["trades"] < V2_JEV_TRADE_PINS[cell] else "FAIL",
        }
        cr_tiers = {1.0: res_c}
        for tier in (1.5, 2.0):
            r, _, _, _ = arm_c(ctx, tier)
            cr_tiers[tier] = r
        for tier, res in sorted(cr_tiers.items()):
            _persist(out_root, cell, "C_REGIME_SPECIALIST_ROUTER", tier, res,
                     {"selection_audit": sel_audit,
                      "routing_report": route_report,
                      "turnover_rejection_law": turnover,
                      "run_identity": "run2-remediation-INC-1"})
            cell_blk["arms"].setdefault(
                "C_REGIME_SPECIALIST_ROUTER", {})[
                {1.0: "tier_1", 1.5: "tier_1p5", 2.0: "tier_2"}[tier]] = {
                "net": res.totals["net_pnl"],
                "trades": res.totals["trades"],
                "fold_nets": list(res.fold_net_pnl)}

        res_cr, sel_audit_r, route_report_r, mapping_r = arm_c(
            ctx, 1.0, outer_floors=RELAXED_OUTER_FLOORS)
        cr2 = {1.0: res_cr}
        for tier in (1.5, 2.0):
            r, _, _, _ = arm_c(ctx, tier, outer_floors=RELAXED_OUTER_FLOORS)
            cr2[tier] = r
        for tier, res in sorted(cr2.items()):
            _persist(out_root, cell, "C_RELAXED_REGIME_SPECIALIST_ROUTER",
                     tier, res,
                     {"selection_audit": sel_audit_r,
                      "routing_report": route_report_r,
                      "outer_floors": RELAXED_OUTER_FLOORS,
                      "sensitivity_note": "owner-instructed relaxed-floor "
                                          "variant; NOT the primary candidate",
                      "run_identity": "run2-remediation-INC-1"})
            cell_blk["arms"].setdefault(
                "C_RELAXED_REGIME_SPECIALIST_ROUTER", {})[
                {1.0: "tier_1", 1.5: "tier_1p5", 2.0: "tier_2"}[tier]] = {
                "net": res.totals["net_pnl"],
                "trades": res.totals["trades"],
                "fold_nets": list(res.fold_net_pnl)}

        # D/E recomputed under the FINAL (deferral) mechanism so the whole
        # report uses one routing law (run-1 D/E superseded; A1/A2/B never
        # touch route_arm and remain run-1 valid, byte-verified by repro).
        for arm_name, fn in (
                ("D_SPARSE_JEV_RISK_OFF_VETO", lambda t: arm_d(ctx, t)),
                ("E_DETERMINISTIC_PLUS_JEV_VETO", lambda t: arm_e(ctx, t))):
            res0, rep0 = fn(1.0)
            de_tiers = {1.0: res0}
            for tier in (1.5, 2.0):
                r, _ = fn(tier)
                de_tiers[tier] = r
            for tier, res in sorted(de_tiers.items()):
                _persist(out_root, cell, arm_name, tier, res,
                         {"routing_report": rep0,
                          "run_identity": "run2-remediation-INC-1b-deferral"})
                cell_blk["arms"].setdefault(arm_name, {})[
                    {1.0: "tier_1", 1.5: "tier_1p5", 2.0: "tier_2"}[tier]] = {
                    "net": res.totals["net_pnl"],
                    "trades": res.totals["trades"],
                    "fold_nets": list(res.fold_net_pnl)}
            observed2 += 1

        for arm_name, mapping_for_f in (
                ("F_EPISODE_SHUFFLED_MATCHED", mapping),
                ("F_RELAXED_EPISODE_SHUFFLED_MATCHED", mapping_r)):
            try:
                f_blk = arm_f(ctx, mapping_for_f, 1.0)
                _persist(out_root, cell, arm_name, 1.0,
                         _run_engine(ctx, [FLAT] * ctx.n, ctx.a4_specs, 1.0),
                         {"f_control": f_blk,
                          "run_identity": "run2-remediation-INC-1"})
                cell_blk["arms"][arm_name] = {
                    "median_net_pnl": f_blk["median_net_pnl"],
                    "seeds": len(f_blk["seeds"]),
                    "null_invalid_flag": f_blk["null_invalid_flag"]}
            except ControlMatchFailure as exc:
                cell_blk["arms"][arm_name] = {
                    "status": "NOT_RUN_CONTROL_MATCHING", "detail": exc.payload}
            observed2 += 1
        observed2 += 2
        summary["cells"][cell] = cell_blk
        summary["trial_accounting"]["run2_observed_cf"] = observed2
        summary["trial_accounting"]["total_observed_all_runs"] = 27 + observed2

    summary["finished_at_utc"] = datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    (out_root / "scored_summary_run2_cf.json").write_text(
        json.dumps(summary, indent=1, sort_keys=True, default=str) + "\n")
    print("remediation run2 complete: cf cells", observed2,
          "| total observed all runs", 27 + observed2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
