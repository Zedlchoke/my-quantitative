"""DIAG scoring driver — one pass, both pairs, as specified. No tuning.

OWNER instruction 2026-09-26 (diag lane): score the current shadow
strategy law ("daemon law") on EURUSD and GBPUSD, 5 books per pair,
k in {1.0, 1.5, 2.0}, full diagnostic panel 2021-01-01..2026-06-30,
folds F1..F6, 2026H1 labeled CONSUMED_SURFACE_DESCRIPTIVE, R-DAEMON
G1-G8 arithmetic (informative), mode-flip statistics, beta check.

Outputs (diag namespace only):
  diag/diag_daemon_results.json   full machine-readable results
  diag/diag_ledger.jsonl          one row per arm x pair
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

DIAG = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DIAG / "scripts"))
sys.path.insert(0, str(DIAG.parent / "scripts"))

import diag_lib as G  # noqa: E402

OUT_RESULTS = DIAG / "diag_daemon_results.json"
OUT_LEDGER = DIAG / "diag_ledger.jsonl"

OWNER_INSTRUCTION_NOTE = (
    "OWNER instruction 2026-09-26 (verbatim intent): score the CURRENT "
    "shadow strategy law ('daemon law') on EURUSD and GBPUSD as a "
    "DIAGNOSTIC exercise on OUTCOME-EXPOSED surfaces. Positive results "
    "CANNOT count as candidate evidence (umbrella 5.8/6 ancestry law; "
    "cohort plan 3); if R-DAEMON is materially positive at k=1.0 with "
    "PF>>1 and beats beta, the reading is 'warrants a properly frozen "
    "new identity + forward shadow test', NOT 'edge proven'; if weak or "
    "negative, consistent with the seam attribution, closes the "
    "question. No parameter tuned, no variant tried, no rescue: one "
    "pass, both pairs, as specified.")


def main() -> int:
    results = {
        "schema": "diag_daemon_results@1",
        "cycle_id": "ERP1-TRACKA-COHORT-1",
        "lane": "tracka1-diag-daemon",
        "verdict_class": "DIAGNOSTIC_OUTCOME_EXPOSED (never promotable "
                         "evidence, regardless of result)",
        "owner_instruction": OWNER_INSTRUCTION_NOTE,
        "windows": {
            "panel": [G.PANEL_START, G.PANEL_END],
            "folds": [list(f) for f in G.FOLD_TABLE],
            "w2026H1": [G.W26_START, G.W26_END],
            "w2026H1_label": "CONSUMED_SURFACE_DESCRIPTIVE",
        },
        "plane": "ANCESTRY convention H1 signal plane (close-column high) "
                 "per the cohort plane pin; port true-H/L plane = cost "
                 "plane; spreads bit-identical (census gate)",
        "pinned_choices": {
            "warmup_end_idx": 0,
            "note": "no warmup parameter introduced; every arm identical; "
                    "the law's own history machinery governs when modes "
                    "exist",
            "g_gate_panel": "full diagnostic panel (informative); fold "
                            "assignment + concentration shares cover "
                            "F1..F6 (2021-2025)",
        },
        "arms": ["R-DAEMON", "R-ORIG", "R-ANCHOR", "SHORT_ALWAYS",
                 "LONG_ALWAYS"],
        "cost_books": "k in {1.0, 1.5, 2.0} x the fill bar's own measured "
                      "spread, through the committed engine (opposite-"
                      "quote fills; no fills on/after the 19:00 bar; "
                      "force-flat at the day-close bar close, 20:00 UTC; "
                      "weekend flat)",
        "sha_chain": G.sha_chain(),
        "pairs": {},
    }

    ledger = []
    for pair in G.PAIRS:
        p = G.load_plane(pair)
        tgts, first_mode, changes = G.build_targets(p)
        pair_res = {
            "plane_bars": int(len(p.ts)),
            "traded_days": int(len(p.traded_days())),
            "first_ts": str(p.ts[0]), "last_ts": str(p.ts[-1]),
            "arms": {}, "daemon": {},
        }
        books = {}
        for arm, tgt in tgts.items():
            arm_books = G.run_arm(p, tgt)
            books[arm] = arm_books
            pair_res["arms"][arm] = arm_books
        pair_res["daemon"]["mode_flip_stats"] = G.daemon_mode_stats(
            p, first_mode, changes)
        pair_res["daemon"]["bar_disagreement"] = G.daemon_bar_disagreement(
            p, tgts)
        pair_res["daemon"]["g_gates_informative"] = G.g_gates_informative(
            books["R-DAEMON"])
        pair_res["daemon"]["beta_check"] = G.beta_check(books, pair)
        results["pairs"][pair] = pair_res

        # ---------------- ledger: one row per arm x pair ---------------
        for arm in tgts:
            b1 = books[arm]["1.0"]
            row = {
                "cycle_id": "ERP1-TRACKA-COHORT-1",
                "lane": "tracka1-diag-daemon",
                "mechanism_id": "DIAG",
                "arm_id": arm,
                "arm_config_digest": None,
                "pair": pair,
                "fold_or_holdout_tag": "DIAG_FULL_PANEL_2021_01_2026_06",
                "cost_tier": "PAPER_TIER_PER_SESSION_X_K",
                "net_pnl": {"1.0": b1["decompose"]["net_pips"],
                            "1.5": books[arm]["1.5"]["decompose"]["net_pips"],
                            "2.0": books[arm]["2.0"]["decompose"]["net_pips"]},
                "gross_pnl": {"1.0": b1["decompose"]["gross_pips"]},
                "n_trades": {"1.0": b1["decompose"]["n_trades"]},
                "pf": {k: books[arm][k]["gate_metrics"]["pf"]
                       for k in ("1.0", "1.5", "2.0")},
                "per_fold_net_pips_k1.0": b1["gate_metrics"]["per_fold_net_pips"],
                "w2026H1": b1["w2026H1"],
                "gates_with_margins_to_fail": (
                    pair_res["daemon"]["g_gates_informative"]
                    if arm == "R-DAEMON" else {}),
                "verdict": "DIAGNOSTIC_DESCRIPTIVE",
                "exclusion_zones": None,
                "labels": G.LABELS,
                "falsifier_id": "DIAG-DAEMON" if arm == "R-DAEMON"
                                else "DIAG-REFERENCE",
                "sha_chain": {"results_schema": results["schema"]},
                "selectable": arm in ("R-ANCHOR",) or False,
                "note": (
                    "R-ORIG is the byte-faithful leaky ancestor law "
                    "(placement reference, never selectable); R-DAEMON "
                    "is the M-3 emulation of the running shadow law; "
                    "SHORT/LONG_ALWAYS are the baseline books. "
                    "DIAGNOSTIC_OUTCOME_EXPOSED: no promotion semantics."
                    if arm != "R-DAEMON" else
                    "object of the owner's question; 2026H1 window is "
                    "CONSUMED_SURFACE_DESCRIPTIVE"),
            }
            ledger.append(row)

    OUT_RESULTS.write_text(json.dumps(results, indent=1, default=str))
    with open(OUT_LEDGER, "w") as f:
        for r in ledger:
            f.write(json.dumps(r, default=str) + "\n")

    # ---------------- console summary ----------------
    print(json.dumps({
        "pairs": {
            pair: {
                arm: {
                    "net@1.0": results["pairs"][pair]["arms"][arm]["1.0"]["decompose"]["net_pips"],
                    "pf@1.0": results["pairs"][pair]["arms"][arm]["gate_metrics"]["pf"] if False else results["pairs"][pair]["arms"][arm]["1.0"]["gate_metrics"]["pf"],
                    "rt@1.0": results["pairs"][pair]["arms"][arm]["1.0"]["decompose"]["n_trades"],
                    "net@1.5": results["pairs"][pair]["arms"][arm]["1.5"]["decompose"]["net_pips"],
                    "net@2.0": results["pairs"][pair]["arms"][arm]["2.0"]["decompose"]["net_pips"],
                } for arm in results["pairs"][pair]["arms"]},
            "mode_flips": results["pairs"][pair]["daemon"]["mode_flip_stats"]["n_days_mode_changed_midday"],
            "beta_check": results["pairs"][pair]["daemon"]["beta_check"],
        }
        for pair in G.PAIRS
    }, indent=1, default=str))
    print(f"\nresults -> {OUT_RESULTS}\nledger  -> {OUT_LEDGER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
