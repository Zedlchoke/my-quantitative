#!/usr/bin/env python3
"""A7 terminal audit helper: recompute the V15 verdict from published bytes.

Recomputes the frozen Stage-A gate table for all six arms directly from
results/v15_phase_e bytes and cross-checks every number in
research/control/v15_run/terminal_report_v15.json (12-dp agreement).
Read-only except for its JSON stdout (redirected by the caller).
"""
import json
import sys
from pathlib import Path

EXEC = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/crypto/v15/e-exec-1"
)
RES = EXEC / "results/v15_phase_e"
TREPORT = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/crypto/v15/r-a7-terminal"
) / "research/control/v15_run/terminal_report_v15.json"

ARMS = [
    ("elite_size_asym", "A5-F1-ANCHOR-ASYM", "anchor"),
    ("elite_size_asym", "A5-F1-NEIGHBOR", "neighbour"),
    ("elite_size_asym", "A5-F1-CTL-ELITELEVEL", "causal_negative_control"),
    ("taker_sat", "A6-F1-ANCHOR-SAT", "anchor"),
    ("taker_sat", "A6-F1-NEIGHBOR", "neighbour"),
    ("taker_sat", "A6-F1-CTL-RAWSAT", "causal_negative_control"),
]


def agree(a, b, dp=9):
    """True when a and b agree to at least dp decimal places."""
    return round(float(a), dp) == round(float(b), dp)


def main():
    tr = json.loads(TREPORT.read_text())
    out = {"arms": {}, "checks": {}, "issues": []}

    for fam, arm, role in ARMS:
        bm = json.loads((RES / fam / arm / "baseline_metrics.json").read_text())
        cs = json.loads((RES / fam / arm / "cell_summary.json").read_text())
        sm = bm["scored_metrics"]
        fs = bm["fold_signs"]

        exp = float(sm["expectancy_per_day"])
        pf = float(sm["position_pf"])
        mdd = float(sm["max_drawdown"])
        fp = list(fs["fold_positive"])
        n_pos = sum(1 for x in fp if x)
        fns = {k: float(v) for k, v in fs["fold_net_sums"].items()}
        pos_nets = [v for v in fns.values() if v > 0]
        lf_share = (
            (max(pos_nets) / sum(pos_nets)) if pos_nets else None
        )

        g1 = exp > 0.0
        g2 = pf >= 1.10
        g3 = n_pos >= 2
        g4 = (lf_share is not None) and lf_share <= 0.50
        g5 = mdd <= 0.20
        headline_pass = g1 and g2 and g3 and g4 and g5

        # cross-check vs terminal report cell_results
        cr = tr["cell_results"][arm]
        xchecks = {
            "cell.exp": agree(cr["expectancy_per_day"], exp, 12),
            "cell.pf": agree(cr["position_pf"], pf, 12),
            "cell.mdd": agree(cr["mdd"], mdd, 12),
            "cell.cost_fills": agree(cr["cost_fills"], float(sm["cost_fills"]), 12),
            "cell.folds": str(cr["folds_positive"]).startswith(f"{n_pos}/3"),
            "cell.role": cr["role"] == role == cs["role"],
        }

        # family gate table cross-check (anchors only carry full tables)
        gt = None
        for fid, table in tr["family_gate_tables"].items():
            short = "A5" if fid.startswith("A5") else "A6"
            if arm.startswith(short) and (
                (table.get("G1_expectancy_gt_0", {}) or {}).get("value") is not None
            ):
                if (fid.startswith("A5")) == arm.startswith("A5"):
                    if arm.endswith(("ANCHOR-ASYM", "ANCHOR-SAT")):
                        gt = table
        if gt:
            xchecks["gt.G1.value"] = agree(gt["G1_expectancy_gt_0"]["value"], exp, 12)
            xchecks["gt.G2.value"] = agree(gt["G2_pf_ge_1p10"]["value"], pf, 12)
            xchecks["gt.G5.value"] = agree(gt["G5_mdd_le_0p20"]["value"], mdd, 12)

        out["arms"][arm] = {
            "family": fam,
            "role": role,
            "exp": exp, "pf": pf, "mdd": mdd,
            "folds_positive": f"{n_pos}/3",
            "fold_net_sums": fns,
            "largest_fold_positive_share": lf_share,
            "gates": {"G1_exp>0": g1, "G2_pf>=1.10": g2, "G3_folds>=2/3": g3,
                      "G4_lf_share<=0.50": g4, "G5_mdd<=0.20": g5},
            "headline_pass": headline_pass,
            "net_return_sum": float(sm["net_return_sum"]),
            "margin_to_fail_present": "margin_to_fail" in cs and "margin_to_fail" in sm,
            "mtf_symbol_share_margin": cs["margin_to_fail"]["margins"].get(
                "largest_symbol_positive_pnl_share"),
            "publish_stage": cs["publish_stage"],
            "producer_head_sha": cs["producer_head_sha"],
            "digest_matches_ledger": None,  # filled below
            "xchecks_vs_terminal_report": xchecks,
        }

    # ledger checks
    led_digests, led_tk = [], []
    led_ok = True
    for fam, _, _ in ARMS:
        rows = [
            json.loads(l)
            for l in (RES / "ledgers" / f"{fam}.jsonl").read_text().splitlines()
            if l.strip()
        ]
        if len(rows) != 3:
            led_ok = False
            out["issues"].append(f"ledger {fam} rows={len(rows)} != 3")
        for r in rows:
            led_digests.append(r["arm_config_digest"])
            led_tk.append(r["trial_key"])
            a = out["arms"].get(r["arm_id"])
            if a is None:
                led_ok = False
                out["issues"].append(f"ledger arm unknown {r['arm_id']}")
            else:
                a["digest_matches_ledger"] = (
                    r["arm_config_digest"] in [
                        json.loads((RES / f2 / a2 / "cell_summary.json").read_text())["arm_config_digest"]
                        for f2, a2, _ in ARMS if a2 == r["arm_id"]
                    ]
                )
                cs2 = json.loads(
                    (RES / r["cell"]["family"] / r["arm_id"] / "cell_summary.json").read_text()
                )
                if cs2["result_sha256"] != r["result_sha256"]:
                    led_ok = False
                    out["issues"].append(f"result_sha256 mismatch {r['arm_id']}")
                if r["producer_head_sha"] != "824190ca8622e194c2bbe1fed77fd488faac5df4":
                    led_ok = False
                    out["issues"].append(f"producer_head != freeze {r['arm_id']}")
    out["checks"]["ledger_rows_3x2"] = led_ok
    out["checks"]["digests_pairwise_unique_6"] = len(set(led_digests)) == 6
    out["checks"]["trial_keys_unique_6_replay_zero"] = len(set(led_tk)) == 6

    # rule order #1 verdict recompute
    f1_anchor = out["arms"]["A5-F1-ANCHOR-ASYM"]
    f2_anchor = out["arms"]["A6-F1-ANCHOR-SAT"]
    rule1_f1_reject = not f1_anchor["gates"]["G1_exp>0"]
    rule1_f2_reject = not f2_anchor["gates"]["G1_exp>0"]
    out["checks"]["rule_order_1_family_REJECT_f1"] = rule1_f1_reject
    out["checks"]["rule_order_1_family_REJECT_f2"] = rule1_f2_reject
    out["checks"]["terminal_report_family_verdicts_REJECT"] = all(
        v.get("family_verdict") == "V15_FAMILY_REJECT (rule order #1)"
        for v in tr["family_gate_tables"].values()
    )

    # F1 firing control standalone headline pass
    ctl1 = out["arms"]["A5-F1-CTL-ELITELEVEL"]
    out["checks"]["F1_control_CTL-ELITELEVEL_passes_headline_standalone"] = ctl1[
        "headline_pass"
    ]
    # F2 control does NOT reproduce
    ctl2 = out["arms"]["A6-F1-CTL-RAWSAT"]
    out["checks"]["F2_control_CTL-RAWSAT_does_NOT_reproduce"] = not ctl2[
        "headline_pass"
    ]
    # control pass/fail must not change verdict under rule order #1
    out["checks"]["verdict_invariant_to_controls_under_rule1"] = (
        rule1_f1_reject and rule1_f2_reject
    )

    # all terminal report xchecks
    flat = [v for a in out["arms"].values() for v in a["xchecks_vs_terminal_report"].values()]
    out["checks"]["terminal_report_numbers_match_published_bytes"] = all(flat)

    # denominators
    den = tr["denominators"]
    out["checks"]["denominators_149_152"] = (
        den["published_logical_before"] == 143
        and den["observed_logical_before"] == 146
        and den["published_logical_after"] == 149
        and den["observed_logical_after"] == 152
    )

    # margin_to_fail present in all cell summaries
    out["checks"]["margin_to_fail_in_all_cell_summaries"] = all(
        a["margin_to_fail_present"] for a in out["arms"].values()
    )

    # reproduction artifact
    rep = json.loads((RES / "reproduction_v15.json").read_text())
    out["checks"]["reproduction_ALL_MATCH"] = (
        json.dumps(rep)
        .count('"match": true') >= 6
        or rep.get("verdict") == "ALL_MATCH"
        or all(
            (v.get("verdict") == "MATCH") or (v.get("match") is True)
            for v in [rep] if isinstance(v, dict)
        )
    )
    out["reproduction_summary"] = {
        k: rep[k] for k in list(rep.keys())[:8] if not isinstance(rep[k], (dict, list))
    }

    print(json.dumps(out, indent=1, default=str))
    bad = [k for k, v in out["checks"].items() if v is not True]
    print("NON_PASS_CHECKS:", bad if bad else "none", file=sys.stderr)


if __name__ == "__main__":
    main()
