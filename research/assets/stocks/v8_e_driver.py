"""V8 Phase E scored-execution driver (PLAN_stocks_v7.md section 11 semantics,
inherited by PLAN_stocks_v8.md section 4).

Refuses to run unless invoked with the EXACT owner GO phrase:
    python -m research.assets.stocks.v8_e_driver 'GO STOCKS V8 SCORED EXECUTION'

Runs the six frozen cells serially (2 families x anchor/neighbour/control)
plus the preregistered reruns (stress x2 band cost; anchor drop-one-symbol;
F1 drop-INVENTORY-leg; F2 drop-one-sector), evaluates the FROZEN Stage-A
gate contract from p3_invariants_freeze.json (carried V4/V5 payload) with
margin-to-fail per gate (LESSONS P-2), and writes:

  research/control/stocks_free_v8_run/execution_ledger.json
  research/control/stocks_free_v8_run/family_verdicts.json
"""

import copy
import hashlib
import json
import os
import subprocess
import sys
import time

from research.assets.stocks import v8_family_runner as r

BENCH_DIR = f"{r.ROOT}/.staging_prices_v8/benchmarks"
LEDGER = "research/control/stocks_free_v8_run/execution_ledger.json"
VERDICTS = "research/control/stocks_free_v8_run/family_verdicts.json"
GATES = json.load(open("research/control/stocks_free_v8_run/p3_invariants_freeze.json"))["carried_payload"]["stage_a_gates_carried_forward"]
CONC = json.load(open("research/control/stocks_free_v8_run/p3_invariants_freeze.json"))["carried_payload"]["concentration_and_robustness"]
SECTORS = ["XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY"]
F1_FIELDS = ["us-gaap:AccountsReceivableNetCurrent", "us-gaap:InventoryNet",
             "us-gaap:AccountsPayableCurrent", "us-gaap:Assets",
             "us-gaap:AllowanceForDoubtfulAccountsReceivableCurrent"]
F2_FIELDS = ["us-gaap:AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment",
             "us-gaap:PropertyPlantAndEquipmentGross", "us-gaap:UnrecognizedTaxBenefits",
             "us-gaap:Goodwill", "us-gaap:Assets"]


def load_bench():
    out = {}
    for t in ["SPY"] + SECTORS:
        bars = json.load(open(f"{BENCH_DIR}/{t}.json"))
        pos = {b["date"]: i for i, b in enumerate(bars)}
        out[t] = {"adj": [float(b["adjusted_close"]) for b in bars], "pos": pos}
    return out


def window_return(bench, d0, d1):
    i0, i1 = bench["pos"].get(d0), bench["pos"].get(d1)
    if i0 is None or i1 is None or i1 <= i0:
        return None
    return bench["adj"][i1] / bench["adj"][i0] - 1.0


def gate(name, ok, observed, threshold, direction):
    return {"gate": name, "verdict": "PASS" if ok else "FAIL",
            "observed": observed, "threshold": threshold,
            "margin_to_fail": (round(observed - threshold, 6) if direction == "gt"
                               else round(threshold - observed, 6))}


def evaluate(decision_pnl, folds_order, spy, sector_basket, control_alpha=None):
    """Frozen Stage-A gate table for one arm record."""
    n = len(decision_pnl)
    e = sum(x["pnl"] for x in decision_pnl)
    wins = sum(x["pnl"] for x in decision_pnl if x["pnl"] > 0)
    losses = -sum(x["pnl"] for x in decision_pnl if x["pnl"] < 0)
    pf = wins / losses if losses > 0 else None
    per_fold = {f: [x["pnl"] for x in decision_pnl if x["fold"] == f] for f in folds_order}
    fold_pos = sum(1 for f in folds_order if per_fold[f] and sum(per_fold[f]) > 0)
    fold_pf = {}
    mdds = {}
    for f in folds_order:
        xs = per_fold[f]
        w = sum(x for x in xs if x > 0)
        l = -sum(x for x in xs if x < 0)
        fold_pf[f] = w / l if l > 0 else None
        cum = peak = m = 0.0
        for x in xs:
            cum += x
            peak = max(peak, cum)
            m = max(m, peak - cum)
        mdds[f] = m
    # risk-matched SPY context (gross = 1.0) per decision
    alphas = []
    for x in decision_pnl:
        spy_r = window_return(spy, x["fill_d"], x["end_d"])
        if spy_r is not None:
            alphas.append(x["pnl"] - spy_r)
    alpha = sum(alphas) / len(alphas) if alphas else None
    alpha_folds = []
    for f in folds_order:
        fa = [x["pnl"] - window_return(spy, x["fill_d"], x["end_d"])
              for x in decision_pnl if x["fold"] == f
              if window_return(spy, x["fill_d"], x["end_d"]) is not None]
        alpha_folds.append(sum(fa))
    # sector-factor co-movement share among positive decisions
    pos_dec = [x for x in decision_pnl if x["pnl"] > 0]
    etf_pos = 0
    for x in pos_dec:
        sec_r = window_return(sector_basket, x["fill_d"], x["end_d"])
        if sec_r is not None and sec_r > 0:
            etf_pos += 1
    etf_share = etf_pos / len(pos_dec) if pos_dec else 0.0
    pos_share_fold = max(
        (sum(x for x in per_fold[f] if x > 0) for f in folds_order), default=0.0)
    pos_share = pos_share_fold / wins if wins > 0 else 0.0
    g = [
        gate("expectancy_gt", e > 0, round(e, 8), 0.0, "gt"),
        gate("position_pf_ge", pf is not None and pf >= GATES["position_pf_ge"],
             round(pf, 4) if pf else pf, GATES["position_pf_ge"], "ge"),
        gate("folds_positive_ge", fold_pos >= GATES["folds_positive_ge"], fold_pos,
             GATES["folds_positive_ge"], "ge"),
        gate("min_populated_fold_pf_ge",
             all(v is not None and v >= GATES["min_populated_fold_pf_ge"]
                 for v in fold_pf.values() if v is not None) and any(v is not None for v in fold_pf.values()),
             {k: (round(v, 3) if v else v) for k, v in fold_pf.items()},
             GATES["min_populated_fold_pf_ge"], "ge"),
        gate("max_fold_mdd_le", max(mdds.values()) <= GATES["max_fold_mdd_le"],
             round(max(mdds.values()), 4), GATES["max_fold_mdd_le"], "le"),
        gate("fold_positive_share_le", pos_share <= CONC["fold_positive_share_le"],
             round(pos_share, 4), CONC["fold_positive_share_le"], "le"),
        gate("etf_positive_share_le", etf_share <= CONC["etf_positive_share_le"],
             round(etf_share, 4), CONC["etf_positive_share_le"], "le"),
        gate("risk_matched_excess_positive_folds_ge",
             sum(1 for a in alpha_folds if a > 0) >= GATES["risk_matched_excess_positive_folds_ge"],
             sum(1 for a in alpha_folds if a > 0),
             GATES["risk_matched_excess_positive_folds_ge"], "ge"),
        gate("anchor_overall_alpha_gt", alpha is not None and alpha > 0,
             round(alpha, 8) if alpha is not None else None, 0.0, "gt"),
    ]
    if control_alpha is not None:
        ratio = abs(control_alpha) / abs(alpha) if alpha else None
        g.append(gate("control_alpha_abs_ratio_lt",
                      ratio is not None and ratio < GATES["control_alpha_abs_ratio_lt"],
                      round(ratio, 4) if ratio is not None else None,
                      GATES["control_alpha_abs_ratio_lt"], "lt"))
    return {"gates": g, "expectancy": e, "pf": pf, "alpha": alpha,
            "fold_positive": fold_pos, "per_fold_pnl": {f: round(sum(v), 8) for f, v in per_fold.items()},
            "mdd": {k: round(v, 6) for k, v in mdds.items()},
            "n_decisions": n}


def decision_series(rec, prices, folds):
    """Attach fill/end sessions to the scored decision pnl list."""
    out = []
    # global union calendar for fill/end sessions
    all_days = sorted({d for p in prices.values() for d in p["date"]})
    dpos = {d: i for i, d in enumerate(all_days)}
    for x in rec["metrics"]["decision_pnl"]:
        g = dpos[x["d"]]
        fill_d = all_days[g + 1]
        # next scored decision date in the same fold sequence
        out.append({"d": x["d"], "fold": x["fold"], "pnl": x["pnl"],
                    "fill_d": fill_d, "end_d": None})
    for i, x in enumerate(out):
        nxt = next((y for y in out[i + 1:] if y["fold"] == x["fold"]), None)
        x["end_d"] = nxt["fill_d"] if nxt else None
    # fold-end decisions: end at last session of their fold
    fold_last = {f["fold_id"]: f["sessions"][-1] for f in folds}
    for x in out:
        if x["end_d"] is None:
            x["end_d"] = fold_last[x["fold"]]
    return out


def main():
    if len(sys.argv) < 2 or sys.argv[1] != r.GO_PHRASE:
        raise SystemExit("REFUSED: exact owner GO phrase required as argv[1]")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    started = time.time()
    prices = r.load_prices()
    folds = r.fold_sessions(prices)
    folds_order = [f["fold_id"] for f in folds]
    bench = load_bench()
    sector_basket = {"adj": None, "pos": None}  # equal-weight basket below
    # equal-weight sector basket adj path built from mean of adjusted closes
    import statistics as st
    series = {}
    for t in SECTORS:
        for d, i in bench[t]["pos"].items():
            series.setdefault(d, []).append(bench[t]["adj"][i])
    sdays = sorted(series)
    sector_basket = {"pos": {d: i for i, d in enumerate(sdays)},
                     "adj": [st.mean(series[d]) for d in sdays]}

    panel_sha = hashlib.sha256(open(r.PANEL, "rb").read()).hexdigest()
    man = json.load(open("research/control/stocks_free_v8_run/p0a_eodhd_price_manifest.json"))
    man_sha = hashlib.sha256(json.dumps(man, sort_keys=True).encode()).hexdigest()

    panels = {"SFV8-F1": r.load_panel(F1_FIELDS), "SFV8-F2": r.load_panel(F2_FIELDS)}
    cells = []
    verdicts = {}
    for fam, arm_ids in (("SFV8-F1", ["SFV8-F1-ANCHOR", "SFV8-F1-NEIGHBOUR", "SFV8-F1-CONTROL"]),
                         ("SFV8-F2", ["SFV8-F2-ANCHOR", "SFV8-F2-NEIGHBOUR", "SFV8-F2-CONTROL"])):
        panel = panels[fam]
        recs = {}
        recs = {}
        for arm_id in arm_ids:
            t0 = time.time()
            base = r.run_arm(arm_id, panel, prices, folds, dry_run=False,
                             owner_go=sys.argv[1], price_manifest_sha=man_sha,
                             panel_sha=panel_sha, code_freeze_sha=head)
            stress = r.run_arm(arm_id, panel, prices, folds, dry_run=False,
                               owner_go=sys.argv[1], price_manifest_sha=man_sha,
                               panel_sha=panel_sha, code_freeze_sha=head, stress=True)
            recs[arm_id] = {"base": base, "stress": stress}
            cells.append({
                "cell_id": f"{arm_id}-BASE", "family_id": base["family_id"],
                "arm_id": arm_id, "cost_tier": "base",
                "arm_config_digest": base["arm_config_digest"],
                "data_snapshot_digest": base["data_snapshot_digest"],
                "code_freeze_sha": head, "runtime_s": round(time.time() - t0, 1),
                "scored_decisions": base["scored_decisions_total"],
                "expectancy": base["metrics"]["expectancy"],
                "sum_pnl": base["metrics"]["sum_pnl"], "pf": base["metrics"]["pf"],
                "folds": base["metrics"]["folds"],
                "stress_sum_pnl": stress["metrics"]["sum_pnl"],
                "stress_pf": stress["metrics"]["pf"],
                "missing_price_legs": base["missing_price_legs"],
            })
        # anchor reruns (preregistered)
        a_id = f"{fam}-ANCHOR"
        base = recs[a_id]["base"]
        top_name = base["metrics"]["top_name_contribution"][0]
        t0 = time.time()
        panel_drop = {k: v for k, v in panel.items() if k != top_name}
        d1 = r.run_arm(a_id, panel_drop, prices, folds, dry_run=False,
                       owner_go=sys.argv[1], price_manifest_sha=man_sha,
                       panel_sha=panel_sha, code_freeze_sha=head)
        reruns = [{"rerun": "drop_one_symbol", "excluded": top_name,
                   "expectancy": d1["metrics"]["expectancy"],
                   "runtime_s": round(time.time() - t0, 1)}]
        if fam == "SFV8-F1":
            t0 = time.time()
            spec = copy.deepcopy(r.ARM_SPECS[a_id])
            spec["drop_leg_index"] = 1  # drop InventoryNet leg (a4_h1 drop-one-signal-leg)
            r.ARM_SPECS[a_id + "-NOINV"] = spec
            d2 = r.run_arm(a_id + "-NOINV", panel, prices, folds, dry_run=False,
                           owner_go=sys.argv[1], price_manifest_sha=man_sha,
                           panel_sha=panel_sha, code_freeze_sha=head)
            reruns.append({"rerun": "drop_signal_leg_inventorynet",
                           "expectancy": d2["metrics"]["expectancy"],
                           "runtime_s": round(time.time() - t0, 1)})
        else:
            t0 = time.time()
            sec_contrib = {}
            for e, v in panel.items():
                sec_contrib.setdefault(v["sector"], 0.0)
            # largest sector by name count as the drop-one-sector candidate
            from collections import Counter
            biggest = Counter(v["sector"] for v in panel.values()).most_common(1)[0][0]
            panel_ds = {k: v for k, v in panel.items() if v["sector"] != biggest}
            d3 = r.run_arm(a_id, panel_ds, prices, folds, dry_run=False,
                           owner_go=sys.argv[1], price_manifest_sha=man_sha,
                           panel_sha=panel_sha, code_freeze_sha=head)
            reruns.append({"rerun": "drop_one_sector", "excluded_sector": biggest,
                           "expectancy": d3["metrics"]["expectancy"],
                           "runtime_s": round(time.time() - t0, 1)})
        recs[a_id]["reruns"] = reruns

        # ---- evaluation (per family; INC-5 fix: recs is family-scoped) ----
        series_by_arm = {}
        for arm_id in arm_ids:
            recs[arm_id]["series"] = decision_series(recs[arm_id]["base"], prices, folds)
            series_by_arm[arm_id] = recs[arm_id]["series"]
        a, nb, c = arm_ids
        anchor_eval = evaluate(series_by_arm[a], folds_order, bench["SPY"], sector_basket)
        # control ratio
        c_eval = evaluate(series_by_arm[c], folds_order, bench["SPY"], sector_basket,
                          control_alpha=anchor_eval["alpha"])
        n_eval = evaluate(series_by_arm[nb], folds_order, bench["SPY"], sector_basket)
        anchor_gates_pass = all(g["verdict"] == "PASS" for g in anchor_eval["gates"])
        stress = recs[a]["stress"]["metrics"]
        stress_ok = stress["sum_pnl"] > 0
        drop = recs[a].get("reruns", [])
        drop_ok = all(x["expectancy"] > 0 for x in drop) if drop else None
        neighbour_support = (n_eval["expectancy"] is not None and anchor_eval["expectancy"] is not None
                             and (n_eval["expectancy"] > 0) == (anchor_eval["expectancy"] > 0))
        control_reproduces = (c_eval["expectancy"] is not None and anchor_eval["expectancy"] is not None
                              and (c_eval["expectancy"] > 0) == (anchor_eval["expectancy"] > 0)
                              and abs(c_eval["expectancy"]) >= 0.5 * abs(anchor_eval["expectancy"]))
        verdicts[fam] = {
            "anchor": {"arm_id": a, **anchor_eval, "gates_all_pass": anchor_gates_pass,
                       "stress_sum_pnl": round(stress["sum_pnl"], 8), "stress_positive": stress_ok,
                       "reruns": recs[a].get("reruns", []), "reruns_survive": drop_ok},
            "neighbour": {"arm_id": nb, "expectancy": n_eval["expectancy"],
                          "pf": n_eval["pf"], "support": neighbour_support},
            "control": {"arm_id": c, "expectancy": c_eval["expectancy"],
                        "reproduces_anchor": control_reproduces,
                        **{"gates": c_eval["gates"]}},
            "family_verdict": None,
        }
        if anchor_gates_pass and stress_ok and drop_ok and neighbour_support and not control_reproduces:
            verdicts[fam]["family_verdict"] = "STAGE_A_SURVIVOR_CANDIDATE"
        elif control_reproduces:
            verdicts[fam]["family_verdict"] = "FALSIFIED_BY_CONTROL"
        else:
            verdicts[fam]["family_verdict"] = "REJECT"

    ledger = {
        "schema": "stocks_free_v8_run/execution_ledger@1",
        "measured_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "producer_role": "A1 (Phase E scored execution, owner GO accepted post-prelaunch)",
        "owner_go": "GO STOCKS V8 SCORED EXECUTION",
        "code_freeze_sha": head,
        "runner_semantics_freeze": "8c6c4c0 (post-authorization changes strictly additive: decision_pnl reporting array + drop_leg_index rerun hook; ARM_SPECS digests unchanged)",
        "panel_sha256": panel_sha, "price_manifest_sha256": man_sha,
        "cells": cells,
        "observed_delta": 6, "published_delta": 0,
        "runtime_total_s": round(time.time() - started, 1),
    }
    json.dump(ledger, open(LEDGER, "w"), indent=1)
    json.dump(verdicts, open(VERDICTS, "w"), indent=1)
    print(json.dumps({f: {"verdict": v["family_verdict"],
                          "anchor_expectancy": v["anchor"]["expectancy"],
                          "anchor_pf": v["anchor"]["pf"],
                          "anchor_alpha": v["anchor"]["alpha"],
                          "gates_all_pass": v["anchor"]["gates_all_pass"],
                          "stress_positive": v["anchor"]["stress_positive"],
                          "reruns_survive": v["anchor"]["reruns_survive"],
                          "neighbour_support": v["neighbour"]["support"],
                          "control_reproduces": v["control"]["reproduces_anchor"]}
                     for f, v in verdicts.items()}, indent=1))


if __name__ == "__main__":
    main()
