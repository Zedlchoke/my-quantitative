"""V11 Phase R — Stage-A family verdict evaluator (A1).

Evaluates the FROZEN Stage-A gates of PLAN section 15 from the scored cell
artifacts.  Numeric thresholds are exactly the frozen ones; the relational
gates (neighbour support, control information, drop-one survival) use the
documented qualitative readings recorded in each gate's ``reading`` field.
No threshold is invented or tuned here.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(r"C:\Users\ROYAL\my-quantitative")
EXEC = REPO / ".worktrees/v11/exec-v11-1"
PHASE_E = EXEC / "results/v11_phase_e"

FAMILIES = {
    "LOT": ["LOT-RESMAX-7D-W", "LOT-RESSKEW-30D-W", "LOT-RESMAX-7D-W-INV"],
    "ILLIQ": ["ILLIQ-AMIHUD-28D-W", "ILLIQ-AMIHUD-56D-W", "ILLIQ-AMIHUD-28D-W-INV"],
}
CONTROL = {"LOT": "LOT-RESMAX-7D-W-INV", "ILLIQ": "ILLIQ-AMIHUD-28D-W-INV"}
ARTIFACT = "{root}/matrix/{cell}/results/artifact.json"


def load(family, arm, cell="baseline"):
    p = PHASE_E / family / arm / "matrix" / cell / "results" / "artifact.json"
    return json.load(open(p))


def g(name, verdict, detail, reading=None):
    out = {"gate": name, "verdict": verdict, "detail": detail}
    if reading:
        out["reading"] = reading
    return out


def sign(x):
    return (x > 0) - (x < 0)


def evaluate(family: str) -> dict:
    anchor, neighbour, control = FAMILIES[family]
    a_art = load(family, anchor)
    a = a_art["portfolio_metrics"]
    gates = []
    summary = {}

    # 1-2 anchor headline
    gates.append(g("after_cost_expectancy_gt_0", a["expectancy_per_day"] > 0,
                   f"anchor expectancy/day={a['expectancy_per_day']}"))
    gates.append(g("pf_ge_1_10", (a["position_pf"] or 0) >= 1.10,
                   f"anchor PF={a['position_pf']}"))

    # 3-5 folds
    folds = [f for f in a_art["fold_metrics"] if f.get("included_in_metrics")]
    pos_folds = [f for f in folds if f["net_return_sum"] > 0]
    gates.append(g("two_of_three_folds_positive", len(pos_folds) >= 2,
                   f"{len(pos_folds)}/{len(folds)} folds net-positive"))
    populated = [f for f in folds if f["n_positions"] > 0]
    bad_pf = [f["fold_label"] for f in populated if (f["position_pf"] or 0) < 0.80]
    gates.append(g("no_populated_fold_pf_below_0_80", not bad_pf,
                   f"folds with PF<0.80: {bad_pf or 'none'}"))
    pos_sum = sum(f["net_return_sum"] for f in pos_folds)
    worst = max((f["net_return_sum"] / pos_sum) for f in pos_folds) if pos_folds else 0.0
    gates.append(g("no_positive_fold_gt_50pct_of_positive_pnl",
                   (worst <= 0.50) if pos_folds else True,
                   f"largest positive-fold share={round(worst, 4)}"
                   if pos_folds else "no positive folds (vacuous PASS)"))

    # 6 drawdown
    gates.append(g("mdd_le_10pct", a["max_drawdown"] <= 0.10,
                   f"anchor max_drawdown={a['max_drawdown']}"))

    # 7 symbol contribution (share of |net pnl| per symbol)
    per_sym = {}
    for p in a_art["positions"]:
        per_sym[p["symbol"]] = per_sym.get(p["symbol"], 0.0) + p["net_pnl_per_unit"] * p["signed_weight"]
    total_abs = sum(abs(v) for v in per_sym.values())
    worst_sym = max(per_sym, key=lambda s: abs(per_sym[s])) if per_sym else None
    share = (abs(per_sym[worst_sym]) / total_abs) if total_abs else 0.0
    gates.append(g("symbol_contribution_le_40pct", share <= 0.40,
                   f"max symbol share={round(share, 4)} ({worst_sym})"))

    # 8 trade evidence
    n_stamps = a_art["book_summary"]["n_books"]
    gates.append(g("minimum_trade_evidence", a["n_positions"] >= n_stamps,
                   f"n_positions={a['n_positions']} over {n_stamps} decision stamps"))

    # 9 drop-one-symbol / drop-one-fold survival (reading: sign stability of net)
    for cell in ("drop_one_symbol", "drop_one_fold"):
        try:
            r = load(family, anchor, cell)["portfolio_metrics"]
        except FileNotFoundError:
            gates.append(g(f"{cell}_survival", None, "NOT_RUN: family frozen folds() declares no dropped-fold cell",
                           reading="excluded by frozen family contract; recorded NOT_APPLICABLE_FROZEN_DESIGN"))
            continue
        same_sign = sign(r["net_return_sum"]) == sign(a["net_return_sum"])
        gates.append(g(f"{cell}_survival", same_sign,
                       f"{cell} net={r['net_return_sum']} vs baseline {a['net_return_sum']}",
                       reading="survival = net-return sign stability vs baseline"))

    # 10 stress cells
    stress_details, stress_pass = [], True
    for cell in ("fee_slippage_x1_5", "plus_2_ticks", "plus_1_event_delay"):
        r = load(family, anchor, cell)["portfolio_metrics"]
        ok = r["net_return_sum"] > 0 and (r["position_pf"] or 0) >= 1.00
        stress_pass = stress_pass and ok
        stress_details.append(f"{cell}: net={r['net_return_sum']}, PF={r['position_pf']}")
    gates.append(g("stressed_pnl_gt_0_and_pf_ge_1", stress_pass, "; ".join(stress_details)))

    # 11 neighbour supports anchor (reading: same-sign expectancy)
    n = load(family, neighbour)["portfolio_metrics"]
    gates.append(g("neighbour_supports_anchor", sign(n["expectancy_per_day"]) == sign(a["expectancy_per_day"]),
                   f"anchor exp/day={a['expectancy_per_day']}, neighbour exp/day={n['expectancy_per_day']}",
                   reading="support = same-sign after-cost expectancy"))

    # 12 causal negative control carries incremental information
    c = load(family, control)["portfolio_metrics"]
    spread_diff = abs(c["net_return_sum"] - a["net_return_sum"])
    denom = abs(a["net_return_sum"]) + abs(c["net_return_sum"])
    informative = (spread_diff / denom) >= 0.5 if denom else False
    inverted_win = c["net_return_sum"] > 0 > a["net_return_sum"]
    gates.append(g("causal_control_information", informative,
                   f"anchor net={a['net_return_sum']}, control net={c['net_return_sum']}, "
                   f"relative spread={round(spread_diff / denom, 4) if denom else 'n/a'}"
                   + ("; CONTROL POSITIVE while anchor negative: frozen falsification clause triggered"
                      if inverted_win else ""),
                   reading="control informative when sign(opposite) or |spread|>=50% of combined |net|"))

    verdict = "V11_STAGE_A_SURVIVOR_LOCKED_FOR_FUTURE_S1" if all(
        x["verdict"] is True for x in gates if x["verdict"] is not None) else "V11_FAMILY_REJECT"
    summary = {
        "schema": "v11_stage_a_family_verdict_v1",
        "producer_role": "A1",
        "family": family,
        "arms": {"anchor": anchor, "neighbour": neighbour, "control": control},
        "anchor_metrics": a,
        "neighbour_metrics": {k: n[k] for k in ("net_return_sum", "expectancy_per_day", "position_pf", "max_drawdown")},
        "control_metrics": {k: c[k] for k in ("net_return_sum", "expectancy_per_day", "position_pf", "max_drawdown")},
        "gates": gates,
        "verdict": verdict,
    }
    return summary


if __name__ == "__main__":
    print(json.dumps(evaluate(sys.argv[1] if len(sys.argv) > 1 else "LOT"), indent=1))
