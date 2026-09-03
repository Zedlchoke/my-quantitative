"""A7-TERMINAL wave 2: independent ILLIQ Stage-A gate recompute.

Own arithmetic over exec-tree artifact positions/daily ledgers (producer
evaluator not imported).  Verifies family_verdict_illiq.json gate-by-gate,
in particular the positive-fold concentration share claimed 0.7055.
"""
from __future__ import annotations

import json
from pathlib import Path

EXEC = Path(r"C:\Users\ROYAL\my-quantitative\.worktrees\v11\exec-v11-1\results\v11_phase_e\ILLIQ")
CTRL = Path(r"C:\Users\ROYAL\my-quantitative\.worktrees\v11\a7-terminal\research\control\v11_run")

ARMS = {
    "anchor": "ILLIQ-AMIHUD-28D-W",
    "neighbour": "ILLIQ-AMIHUD-56D-W",
    "control": "ILLIQ-AMIHUD-28D-W-INV",
}
CELLS = ["baseline", "fee_slippage_x1_5", "plus_2_ticks", "plus_1_event_delay",
         "drop_one_symbol", "drop_one_fold"]


def load(arm, cell):
    return json.loads((EXEC / arm / "matrix" / cell / "results" / "artifact.json")
                      .read_text(encoding="utf-8"))


def metrics(art):
    pos = art["positions"]
    net = [p["net_pnl_per_unit"] for p in pos]
    net_sum = sum(net)
    gp = sum(x for x in net if x > 0)
    gn = sum(x for x in net if x < 0)
    dr = art["daily_returns"]
    day = [d["net_return_per_unit"] for d in dr]
    cum = peak = mdd = 0.0
    for x in day:
        cum += x
        peak = max(peak, cum)
        mdd = max(mdd, peak - cum)
    folds = {}
    for p in pos:
        f = folds.setdefault(p["fold_label"], {"net": 0.0, "npos": 0, "ppos": 0.0, "pneg": 0.0})
        f["net"] += p["net_pnl_per_unit"]
        f["npos"] += 1
        if p["net_pnl_per_unit"] > 0:
            f["ppos"] += p["net_pnl_per_unit"]
        elif p["net_pnl_per_unit"] < 0:
            f["pneg"] += p["net_pnl_per_unit"]
    fold_rows = {k: {"net": f["net"], "n_positions": f["npos"],
                     "pf": (f["ppos"] / -f["pneg"]) if f["pneg"] < 0 else None,
                     "positive": f["net"] > 0}
                 for k, f in sorted(folds.items())}
    per_sym = {}
    for p in pos:
        per_sym[p["symbol"]] = per_sym.get(p["symbol"], 0.0) + p["net_pnl_per_unit"] * p["signed_weight"]
    tot = sum(abs(v) for v in per_sym.values())
    worst = max(per_sym.items(), key=lambda kv: abs(kv[1])) if per_sym else ("", 0.0)
    return {
        "n_positions": len(pos),
        "net_return_sum_positions": net_sum,
        "net_return_sum_daily": sum(day),
        "cost_charged_sum_daily": sum(d["cost_charged_per_unit"] for d in dr),
        "price_pnl_sum": sum(p["price_pnl_per_unit"] for p in pos),
        "funding_sum_positions": sum(p["funding_cashflow_per_unit"] for p in pos),
        "position_pf": (gp / -gn) if gn < 0 else None,
        "expectancy_per_day": net_sum / len(dr) if dr else None,
        "n_days_with_records": len(dr),
        "daily_hit_rate": (sum(1 for x in day if x > 0) / len(day)) if day else None,
        "max_drawdown": mdd,
        "folds": fold_rows,
        "n_folds_positive": sum(1 for f in fold_rows.values() if f["positive"]),
        "folds_pf_below_080": sorted(k for k, f in fold_rows.items()
                                     if f["pf"] is not None and f["pf"] < 0.80),
        "pos_fold_share": {
            k: (f["net"] / sum(x["net"] for x in fold_rows.values() if x["positive"]))
            for k, f in fold_rows.items() if f["positive"]
        } if any(f["positive"] for f in fold_rows.values()) else {},
        "max_symbol_abs_share": (abs(worst[1]) / tot) if tot else None,
        "worst_symbol": worst[0],
        "identity_violations": sum(
            1 for p in pos
            if abs((p["price_pnl_per_unit"] + p["funding_cashflow_per_unit"]
                    - p["cost_allocated_per_unit"]) - p["net_pnl_per_unit"]) > 1e-9),
    }


def main():
    out = {"schema": "a7_terminal_wave2_illiq_recompute_v1"}
    arms = {}
    for role, arm in ARMS.items():
        base = metrics(load(arm, "baseline"))
        cells = {}
        for c in CELLS:
            m = metrics(load(arm, c))
            cells[c] = {"net_daily": m["net_return_sum_daily"], "pf": m["position_pf"],
                        "n_positions": m["n_positions"]}
        arms[role] = {"arm": arm, "baseline": base, "cells": cells}
    out["arms"] = arms
    a = arms["anchor"]["baseline"]

    # claimed values (family_verdict_illiq.json, evidence copy from integration 85c14a7)
    verdict = json.loads((Path(__file__).resolve().parents[1] / "evidence"
                          / "family_verdict_illiq_at85c14a7.json").read_text(encoding="utf-8"))
    cl = {
        "net_return_sum_daily": 0.581969254868,
        "position_pf": 1.35484101084,
        "expectancy_per_day": 0.01119171644,
        "max_drawdown": 0.091821657373,
        "n_positions": 336,
        "n_days_with_records": 52,
        "cost_charged_sum_daily": 0.011107886509,
        "price_pnl_sum": 0.482850008651,
        "funding_sum_positions": 0.110227132726,
        "daily_hit_rate": 0.461538461538,
    }
    out["anchor_vs_claim"] = {
        k: {"mine": a[k], "claimed": v,
            "match": abs(a[k] - v) < 5e-9 if isinstance(v, float) else a[k] == v}
        for k, v in cl.items()
    }
    # concentration: largest positive-fold share of positive PnL
    pos_folds = {k: f["net"] for k, f in a["folds"].items() if f["positive"]}
    tot_pos = sum(pos_folds.values())
    largest_share = max(pos_folds.values()) / tot_pos if tot_pos else None
    out["my_positive_fold_concentration"] = {
        "positive_folds": pos_folds,
        "largest_share": largest_share,
        "claimed": 0.7055,
        "match_4dp": abs(round(largest_share, 4) - 0.7055) < 5e-5,
        "exceeds_050": largest_share > 0.50,
        "fold_fold_shares": a["pos_fold_share"],
    }
    out["my_symbol_share"] = {"share": a["max_symbol_abs_share"], "symbol": a["worst_symbol"],
                              "claimed": 0.2981}
    # gate re-evaluation
    nb = arms["neighbour"]["baseline"]
    cb = arms["control"]["baseline"]
    stress_ok = all(
        arms["anchor"]["cells"][c]["net_daily"] > 0
        and (arms["anchor"]["cells"][c]["pf"] or 0) >= 1.0
        for c in ["fee_slippage_x1_5", "plus_2_ticks", "plus_1_event_delay"])
    g = {
        "after_cost_expectancy_gt_0": a["expectancy_per_day"] > 0,
        "pf_ge_1_10": (a["position_pf"] or 0) >= 1.10,
        "two_of_three_folds_positive": a["n_folds_positive"] >= 2,
        "no_populated_fold_pf_below_0_80": len(a["folds_pf_below_080"]) == 0,
        "no_positive_fold_gt_50pct_of_positive_pnl": largest_share <= 0.50,
        "mdd_le_10pct": a["max_drawdown"] <= 0.10,
        "symbol_contribution_le_40pct": a["max_symbol_abs_share"] <= 0.40,
        "minimum_trade_evidence": a["n_positions"] >= 100,
        "drop_one_symbol_survival": (arms["anchor"]["cells"]["drop_one_symbol"]["net_daily"] < 0)
                                    == (a["net_return_sum_daily"] < 0),
        "drop_one_fold_survival": (arms["anchor"]["cells"]["drop_one_fold"]["net_daily"] < 0)
                                  == (a["net_return_sum_daily"] < 0),
        "stressed_pnl_gt_0_and_pf_ge_1": stress_ok,
        "neighbour_supports_anchor_samesign": (nb["net_return_sum_daily"] < 0)
                                              == (a["net_return_sum_daily"] < 0),
        "causal_control_informative": cb["net_return_sum_daily"] * a["net_return_sum_daily"] < 0,
    }
    out["my_gate_outcomes"] = g
    out["my_failed_gates"] = sorted(k for k, v in g.items() if not v)
    out["producer_failed_gates"] = sorted(
        gt["gate"] for gt in verdict["gates"] if gt["verdict"] is False)
    out["gate_sets_equal"] = set(out["my_failed_gates"]) == set(out["producer_failed_gates"])
    out["verdict_claimed"] = verdict["verdict"]
    out["control_net_mine"] = cb["net_return_sum_daily"]
    out["neighbour_net_mine"] = nb["net_return_sum_daily"]
    out["drop_one_symbol_cell_note"] = {
        "baseline_n_positions": a["n_positions"],
        "drop_one_symbol_n_positions": arms["anchor"]["cells"]["drop_one_symbol"]["n_positions"],
        "identical_net_to_baseline": abs(arms["anchor"]["cells"]["drop_one_symbol"]["net_daily"]
                                         - a["net_return_sum_daily"]) < 1e-9,
    }
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
