"""A7-TERMINAL item 4: independent LOT recompute from exec-tree artifacts.

Recomputes portfolio/fold/stress metrics from the POSITIONS lists with my own
arithmetic (no reuse of producer evaluator code), then compares against
research/control/v11_run/family_verdict_lot.json gate outcomes.
"""
from __future__ import annotations

import json
from pathlib import Path

EXEC = Path(r"C:\Users\ROYAL\my-quantitative\.worktrees\v11\exec-v11-1\results\v11_phase_e\LOT")
CTRL = Path(r"C:\Users\ROYAL\my-quantitative\.worktrees\v11\a7-terminal\research\control\v11_run")

ARMS = {
    "anchor": "LOT-RESMAX-7D-W",
    "neighbour": "LOT-RESSKEW-30D-W",
    "control": "LOT-RESMAX-7D-W-INV",
}
CELLS = ["baseline", "fee_slippage_x1_5", "plus_2_ticks", "plus_1_event_delay", "drop_one_symbol"]


def load_artifact(arm: str, cell: str) -> dict:
    p = EXEC / arm / "matrix" / cell / "results" / "artifact.json"
    return json.loads(p.read_text(encoding="utf-8"))


def my_metrics(art: dict) -> dict:
    """Recompute everything from positions + daily_returns with own arithmetic."""
    pos = art["positions"]
    net = [p["net_pnl_per_unit"] for p in pos]
    n = len(pos)
    net_sum = sum(net)
    gross_pos = sum(x for x in net if x > 0)
    gross_neg = sum(x for x in net if x < 0)
    pf = (gross_pos / -gross_neg) if gross_neg < 0 else None
    # per-position identity check: net == price + funding - cost
    ident_bad = sum(
        1 for p in pos
        if abs((p["price_pnl_per_unit"] + p["funding_cashflow_per_unit"]
                - p["cost_allocated_per_unit"]) - p["net_pnl_per_unit"]) > 1e-9
    )
    # weight * price-return identity
    wret_bad = 0
    for p in pos:
        ret = (p["exit_price"] - p["entry_price"]) / p["entry_price"]
        if abs(p["signed_weight"] * ret - p["price_pnl_per_unit"]) > 1e-9:
            wret_bad += 1
    dr = art["daily_returns"]
    n_days = len(dr)
    day_net = [d["net_return_per_unit"] for d in dr]
    hit = (sum(1 for x in day_net if x > 0) / n_days) if n_days else None
    exp_day = net_sum / n_days if n_days else None
    # MDD on cumulative daily net (absolute return units)
    cum = peak = mdd = 0.0
    for x in day_net:
        cum += x
        peak = max(peak, cum)
        mdd = max(mdd, peak - cum)
    # folds from positions
    folds = {}
    for p in pos:
        f = folds.setdefault(p["fold_label"], {"net": 0.0, "npos": 0, "ppos": 0.0, "pneg": 0.0})
        f["net"] += p["net_pnl_per_unit"]
        f["npos"] += 1
        if p["net_pnl_per_unit"] > 0:
            f["ppos"] += p["net_pnl_per_unit"]
        elif p["net_pnl_per_unit"] < 0:
            f["pneg"] += p["net_pnl_per_unit"]
    fold_rows = {}
    for k, f in sorted(folds.items()):
        fold_rows[k] = {
            "net": f["net"],
            "n_positions": f["npos"],
            "pf": (f["ppos"] / -f["pneg"]) if f["pneg"] < 0 else None,
            "positive": f["net"] > 0,
        }
    # symbol contribution
    syms = {}
    for p in pos:
        syms[p["symbol"]] = syms.get(p["symbol"], 0.0) + p["net_pnl_per_unit"]
    total_abs = sum(abs(v) for v in syms.values())
    worst = max(syms.items(), key=lambda kv: abs(kv[1])) if syms else ("", 0.0)
    return {
        "n_positions": n,
        "net_return_sum": net_sum,
        "price_pnl_sum": sum(p["price_pnl_per_unit"] for p in pos),
        "cost_charged_sum": sum(p["cost_allocated_per_unit"] for p in pos),
        "funding_sum": sum(p["funding_cashflow_per_unit"] for p in pos),
        "position_pf": pf,
        "expectancy_per_day": exp_day,
        "n_days_with_records": n_days,
        "daily_hit_rate": hit,
        "max_drawdown": mdd,
        "position_identity_violations": ident_bad,
        "weight_return_violations": wret_bad,
        "daily_returns_sum": sum(day_net),
        "folds": fold_rows,
        "n_folds_positive": sum(1 for f in fold_rows.values() if f["positive"]),
        "folds_pf_below_080": sorted(k for k, f in fold_rows.items()
                                     if f["pf"] is not None and f["pf"] < 0.80),
        "max_symbol_abs_share": (abs(worst[1]) / total_abs) if total_abs else None,
        "worst_symbol": worst[0],
    }


def close(a, b, tol=5e-10):
    return abs(a - b) < tol


def main() -> None:
    out = {"schema": "a7_terminal_item4_lot_recompute_v1", "arms": {}}
    for role, arm in ARMS.items():
        base = my_metrics(load_artifact(arm, "baseline"))
        cells_out = {}
        for cell in CELLS:
            m = my_metrics(load_artifact(arm, cell))
            cells_out[cell] = {
                "net_return_sum": m["net_return_sum"],
                "position_pf": m["position_pf"],
                "n_positions": m["n_positions"],
                "max_drawdown": m["max_drawdown"],
                "identity_violations": m["position_identity_violations"],
                "weight_return_violations": m["weight_return_violations"],
            }
        out["arms"][role] = {"arm": arm, "baseline": base, "cells": cells_out}

    verdict = json.loads((CTRL / "family_verdict_lot.json").read_text(encoding="utf-8"))
    ma = out["arms"]["anchor"]["baseline"]
    claim = {
        "net_return_sum": verdict["anchor_metrics"]["net_return_sum"],
        "position_pf": verdict["anchor_metrics"]["position_pf"],
        "expectancy_per_day": verdict["anchor_metrics"]["expectancy_per_day"],
        "max_drawdown": verdict["anchor_metrics"]["max_drawdown"],
        "n_positions": verdict["anchor_metrics"]["n_positions"],
        "cost_charged_sum": verdict["anchor_metrics"]["cost_charged_sum"],
        "funding_sum": verdict["anchor_metrics"]["funding_sum"],
        "price_pnl_sum": verdict["anchor_metrics"]["price_pnl_sum"],
        "daily_hit_rate": verdict["anchor_metrics"]["daily_hit_rate"],
        "n_days_with_records": verdict["anchor_metrics"]["n_days_with_records"],
    }
    out["anchor_vs_claim"] = {
        k: {"mine": ma[k], "claimed": v,
            "match": close(ma[k], v) if isinstance(v, float) else ma[k] == v}
        for k, v in claim.items()
    }
    out["fold_check_vs_claim"] = {
        "folds_pf_below_080": {"mine": ma["folds_pf_below_080"], "claimed": ["F0", "F2"]},
        "n_folds_positive": {"mine": ma["n_folds_positive"], "claimed": 1},
    }
    out["anchor_stress_and_drop_cells_mine"] = {
        c: {"net": out["arms"]["anchor"]["cells"][c]["net_return_sum"],
            "pf": out["arms"]["anchor"]["cells"][c]["position_pf"]}
        for c in CELLS if c != "baseline"
    }
    out["control_net"] = {"mine": out["arms"]["control"]["baseline"]["net_return_sum"],
                          "claimed": verdict["control_metrics"]["net_return_sum"]}
    out["neighbour_net"] = {"mine": out["arms"]["neighbour"]["baseline"]["net_return_sum"],
                            "claimed": verdict["neighbour_metrics"]["net_return_sum"]}
    out["control_pf_mine"] = out["arms"]["control"]["baseline"]["position_pf"]
    out["neighbour_pf_mine"] = out["arms"]["neighbour"]["baseline"]["position_pf"]

    # my own gate re-evaluation
    g = {}
    g["after_cost_expectancy_gt_0"] = ma["expectancy_per_day"] > 0
    g["pf_ge_1_10"] = (ma["position_pf"] or 0) >= 1.10
    g["two_of_three_folds_positive"] = ma["n_folds_positive"] >= 2
    g["no_populated_fold_pf_below_0_80"] = len(ma["folds_pf_below_080"]) == 0
    pos_folds = [f["net"] for f in ma["folds"].values() if f["positive"]]
    g["no_positive_fold_gt_50pct_of_positive_pnl"] = (
        (max(pos_folds) / sum(pos_folds)) <= 0.5 if pos_folds else True)
    g["mdd_le_10pct"] = ma["max_drawdown"] <= 0.10
    g["symbol_contribution_le_40pct"] = ma["max_symbol_abs_share"] <= 0.40
    g["stressed_pnl_gt_0_and_pf_ge_1"] = all(
        out["arms"]["anchor"]["cells"][c]["net_return_sum"] > 0
        and (out["arms"]["anchor"]["cells"][c]["position_pf"] or 0) >= 1.0
        for c in ["fee_slippage_x1_5", "plus_2_ticks", "plus_1_event_delay"])
    g["neighbour_supports_anchor_samesign_expectancy"] = (
        (out["arms"]["neighbour"]["baseline"]["net_return_sum"] < 0)
        == (ma["net_return_sum"] < 0))
    g["causal_control_informative"] = (
        out["arms"]["control"]["baseline"]["net_return_sum"] * ma["net_return_sum"] < 0
    )
    out["my_gate_outcomes"] = g
    out["my_failed_gates"] = sorted(k for k, v in g.items() if not v)
    out["verdict_claimed"] = verdict["verdict"]
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
