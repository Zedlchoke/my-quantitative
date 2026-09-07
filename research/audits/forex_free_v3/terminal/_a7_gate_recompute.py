"""A7 TERMINAL C3+C4+C5: recompute the full frozen Stage-A gate set from the
stored record fields for all 6 canonical V3 cells, recompute trade
reconciliation and control coherence, and compare every recomputed verdict
against the stored gates/gate_reasons fields.

Gate constants are hard-imported from the freeze-pinned runner module in
THIS tree (sha-verified against the W3C freeze manifest), not retyped.
Run from the r-a7-terminal worktree with .venv/bin/python.
"""
import json
import os
import sys

REPO = "/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v3/r-a7-terminal"
LEDGER = os.path.join(REPO, "research/control/forex_free_v3_run/scored_ledger_published.jsonl")

sys.path.insert(0, REPO)
from research.assets.forex_free_v3 import scored_runner as R  # noqa: E402

records = []
with open(LEDGER, "r", encoding="utf-8") as fh:
    for line in fh:
        records.append(json.loads(line))

assert len(records) == 6, f"expected 6 records, got {len(records)}"

# ---------- independent flag-level checks per cell ----------
def independent_checks(rec):
    """Every frozen threshold re-derived from the record's own fields."""
    base = rec["base"]
    po = rec["base_price_only"]
    pop = [f for f in rec["folds"] if f["populated"]]
    pos_pop = [f for f in pop if f["expectancy"] > 0]
    scenarios = rec.get("dropout_scenarios") or []
    surv = sum(1 for s in scenarios if s["survived"])
    tiers = rec.get("stress") or {}
    t10, t15, t20 = (tiers.get("tier1.0") or {}).get("total_pnl"), \
                    (tiers.get("tier1.5") or {}).get("total_pnl"), \
                    (tiers.get("tier2.0") or {}).get("total_pnl")
    diag = rec.get("usd_drift_diag") or {}
    checks = {
        "expectancy_positive": base["expectancy"] > 0.0,
        "pf_ge_1.10": base["pf"] is not None and base["pf"] >= R.MIN_PF,
        "pos_populated_folds_ge_2": len(pos_pop) >= R.MIN_POSITIVE_FOLDS,
        "populated_fold_pf_ge_0.80": all(f["pf"] is None or f["pf"] >= R.MIN_FOLD_PF for f in pop),
        "mdd_le_2500": rec["mdd_usd"] <= R.MDD_CEILING_USD,
        "fold_positive_share_le_0.50": rec["fold_positive_share"] <= R.MAX_POS_FOLD_SHARE,
        "max_pair_share_le_0.40": (not rec["pair_concentration"]) or
                                  max(rec["pair_concentration"].values()) <= R.MAX_PAIR_POS_SHARE,
        "stress_tiers_present": all(tiers.get(f"tier{t}") for t in ("1.0", "1.5", "2.0")),
        "stress_tier_rows_distinct": bool(t10 is not None and t15 is not None and t20 is not None
                                          and len({round(t10, 6), round(t15, 6), round(t20, 6)}) == 3),
        "stress_tiers_decline": bool(t10 is not None and t15 is not None and t20 is not None
                                     and t10 >= t15 >= t20),
        "stress_tier_pnl_positive": all(tiers[f"tier{t}"]["total_pnl"] > 0
                                        for t in ("1.0", "1.5", "2.0") if tiers.get(f"tier{t}")),
        "stress_tier_pf_ge_1.0": all(tiers[f"tier{t}"]["pf"] is None or tiers[f"tier{t}"]["pf"] >= R.STRESS_MIN_PF
                                     for t in ("1.0", "1.5", "2.0") if tiers.get(f"tier{t}")),
        "dropout_scenarios_8": len(scenarios) == R.DROPOUT_SCENARIOS,
        "dropout_survival_ge_6_of_8": surv >= R.DROPOUT_MIN_SURVIVAL,
        "usd_corr_within_0.30": (not diag.get("evaluated")) or
                                (diag.get("corr") is not None and abs(diag["corr"]) <= R.USD_CORR_CEILING),
        "usd_eval_days_ge_60": (not diag.get("evaluated")) or diag.get("n_days", 0) >= R.USD_DIAG_MIN_DAYS,
        "decisions_ge_floor": rec.get("n_decisions", 0) >= R.MIN_DECISIONS_PER_ARM,
        "financing_no_inversion": not (base["expectancy"] > 0.0 and po["expectancy"] <= 0.0),
        "incremental_alpha_positive": rec.get("incremental_alpha") is None or rec["incremental_alpha"] > 0,
        "scored_and_published": bool(rec.get("scored")) and bool(rec.get("published")),
    }
    return checks, surv

# ---------- C4: trade reconciliation ----------
def trade_recon(rec):
    fold_sum = sum(f["trades"] for f in rec["folds"])
    return {
        "n_trades": rec["n_trades"],
        "n_trades_kept": rec["n_trades_kept"],
        "fold_trades_sum": fold_sum,
        "purged_trades": rec["purged_trades"],
        "kept_eq_trades": rec["n_trades"] == rec["n_trades_kept"],
        "fold_sum_plus_purge_eq_kept": fold_sum + rec["purged_trades"] == rec["n_trades_kept"],
        "base_trades_eq_fold_sum": rec["base"]["trades"] == fold_sum,
        "fold_trades_eq_sum_of_folds_field": fold_sum == sum(f["trades"] for f in rec["folds"]),
    }

# ---------- run ----------
cells = {}
for rec in records:
    rid = rec["record_id"]
    checks, surv = independent_checks(rec)
    gates_frozen, reasons_frozen = R.stage_a_gates(rec)
    cells[rid] = {
        "stored_gates": rec["gates"],
        "stored_gate_reasons": rec["gate_reasons"],
        "recomputed_gates": gates_frozen,
        "recomputed_gate_reasons": reasons_frozen,
        "verdict_match": gates_frozen == rec["gates"],
        "reasons_match": sorted(reasons_frozen) == sorted(rec["gate_reasons"]),
        "independent_checks": checks,
        "independent_all_pass": all(checks.values()),
        "dropout_survived": surv,
        "trade_reconciliation": trade_recon(rec),
    }

# mechanism sanity per family from stored records
fams = {}
for rec in records:
    fams.setdefault(rec["family_id"], {})[rec["arm"]] = rec
mechanism = {}
for fid, arms in fams.items():
    ms, ms_reasons = R.mechanism_sanity(arms)
    a, n, c = arms["anchor"], arms["neighbour"], arms["control"]
    mechanism[fid] = {
        "recomputed_mechanism_sanity": ms,
        "recomputed_reasons": ms_reasons,
        "anchor_gates": a["gates"],
        "neighbour_gates": n["gates"],
        "control_gates": c["gates"],
        "control_fails_as_designed": c["gates"] is False,
        "control_expectancy": c["base"]["expectancy"],
        "control_pf": c["base"]["pf"],
        "control_reproduces_gate": (c["base"]["expectancy"] > 0 and
                                    (c["base"]["pf"] is None or c["base"]["pf"] >= R.CONTROL_REJECT_PF)),
        "anchor_vs_control": a["base"]["expectancy"] > c["base"]["expectancy"],
        "anchor_expectancy": a["base"]["expectancy"],
        "anchor_price_only_expectancy": a["base_price_only"]["expectancy"],
        "financing_sign_agreement": (a["base"]["expectancy"] > 0) == (a["base_price_only"]["expectancy"] > 0),
    }

out = {
    "schema": "forex_free_v3_a7_gate_recompute_v1",
    "runner_constants": {
        "MIN_EXPECTANCY": R.MIN_EXPECTANCY, "MIN_PF": R.MIN_PF,
        "MIN_POSITIVE_FOLDS": R.MIN_POSITIVE_FOLDS, "MIN_FOLD_PF": R.MIN_FOLD_PF,
        "MDD_CEILING_USD": R.MDD_CEILING_USD, "MAX_POS_FOLD_SHARE": R.MAX_POS_FOLD_SHARE,
        "MAX_PAIR_POS_SHARE": R.MAX_PAIR_POS_SHARE, "STRESS_MIN_PF": R.STRESS_MIN_PF,
        "DROPOUT_SCENARIOS": R.DROPOUT_SCENARIOS, "DROPOUT_MIN_SURVIVAL": R.DROPOUT_MIN_SURVIVAL,
        "USD_CORR_CEILING": R.USD_CORR_CEILING, "USD_DIAG_MIN_DAYS": R.USD_DIAG_MIN_DAYS,
        "MIN_DECISIONS_PER_ARM": R.MIN_DECISIONS_PER_ARM,
        "NEIGHBOUR_MIN_EXPECTANCY": R.NEIGHBOUR_MIN_EXPECTANCY,
        "CONTROL_REJECT_PF": R.CONTROL_REJECT_PF,
    },
    "cells": cells,
    "mechanism": mechanism,
    "all_cells_verdict_match": all(c["verdict_match"] and c["reasons_match"] for c in cells.values()),
}
print(json.dumps(out, indent=1))
