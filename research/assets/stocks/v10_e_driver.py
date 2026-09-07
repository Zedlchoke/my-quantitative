"""V10 E-phase scored driver (A1).

Two-key: refuses without the exact owner phrase (argv[1]) AND
STOCKS_V10_LAUNCH_AUTHORIZED=1.  Runs the six frozen arms (2 families x
anchor/neighbour/control) as base + stress rerun (2x band), plus a
drop-one-symbol rerun for each anchor, evaluates the inherited Stage-A gate
table with margin-to-fail (P-2), and writes:

  research/control/stocks_free_v10_run/execution_ledger.json   (driver ledger)
  research/control/stocks_free_v10_run/family_verdicts.json    (verdicts)
  research/control/stocks_free_v10_run/publication_record.json (append-only)

Counters (V9 convention): trials = 6 (the scored cells); stress and drop-one
reruns are not trials.  observed_delta = 14 (6 trials + 6 stress + 2 drop-one).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from research.assets.stocks import kernel_band_cost_v9 as kernel
from research.assets.stocks import v10_family_runner as r
from research.assets.stocks.v9_e_driver import (
    assert_no_secrets,
    drop_one_fold_ok,
    evaluate,
    load_bench,
    redact,
    sector_basket_from,
    sha256_file,
    sha256_json,
)

WORKTREE = Path(__file__).resolve().parents[3]
CONTROL = WORKTREE / "research/control/stocks_free_v10_run"
LEDGER = CONTROL / "execution_ledger.json"
VERDICTS = CONTROL / "family_verdicts.json"
PUBREC = CONTROL / "publication_record.json"
PRICE_MANIFEST = (WORKTREE / "research/control/stocks_free_v9_run/"
                  "p0d_v9_price_manifest.json")

ARM_GROUPS = {
    "SFV10-A4-H1": ["SFV10-A4-H1-ANCHOR", "SFV10-A4-H1-NEIGHBOUR", "SFV10-A4-H1-CONTROL"],
    "SFV10-A5-H1": ["SFV10-A5-H1-ANCHOR", "SFV10-A5-H1-NEIGHBOUR", "SFV10-A5-H1-CONTROL"],
}


def _git_head():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    except Exception as e:  # noqa: BLE001 - redacted, never retried blind
        raise SystemExit(redact(f"cannot resolve code freeze sha: {e}"))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    phrase = argv[0] if argv else None
    if not r.scored_authorized(phrase):
        raise SystemExit(
            "REFUSED: scored execution needs the exact owner GO phrase "
            f"as argv AND {r.LAUNCH_ENV}=1 in the environment (two-key; "
            "P-8: early or standing phrases never authorize)")
    head = _git_head()
    timing = r.load_timing_layer()
    revision = r.load_revision_layer()
    prices = r.load_prices()
    universe = r.load_universe()
    cohort = json.load(open(WORKTREE / "research/control/stocks_free_v9_run/cohort_v9.json"))
    sectors = {m["cik"]: m.get("sector", "")
               for cls in ("ALIVE_EVIDENCED", "DEAD_EVIDENCED")
               for m in cohort["members"][cls]}
    folds = r.fold_sessions(prices)
    bench = load_bench()
    sector_basket = sector_basket_from(bench)
    folds_order = [f["fold_id"] for f in folds]
    h = __import__("hashlib").sha256()
    for layer_path in (r.TIMING_PATH, r.REVISION_PATH):
        h.update(sha256_file(str(layer_path)).encode())
    layer_digest = h.hexdigest()
    price_manifest_sha = sha256_json(str(PRICE_MANIFEST))

    arms = {}
    cells = []
    for family, group in ARM_GROUPS.items():
        for arm_id in group:
            base = r.run_arm(arm_id, timing, revision, prices, folds,
                             dry_run=False, owner_go=phrase, universe=universe,
                             sectors=sectors, price_manifest_sha=price_manifest_sha,
                             layer_digest=layer_digest, code_freeze_sha=head)
            stress = r.run_arm(arm_id, timing, revision, prices, folds,
                               dry_run=False, owner_go=phrase, universe=universe,
                               sectors=sectors, stress=True,
                               price_manifest_sha=price_manifest_sha,
                               layer_digest=layer_digest, code_freeze_sha=head)
            arms[arm_id] = {"base": base, "stress": stress}
            for tier, rec in (("base", base), ("stress", stress)):
                cells.append({
                    "cell_id": f"{arm_id}-{tier.upper()}",
                    "arm_id": arm_id, "family_id": family,
                    "cost_tier": tier,
                    "arm_config_digest": rec["arm_config_digest"],
                    "data_snapshot_digest": rec["data_snapshot_digest"],
                    "scored_decisions": rec["scored_decisions_total"],
                    "void_entry_orders": rec["void_entry_orders"],
                    "terminations": rec["terminations"],
                })
        # drop-one-symbol rerun for the family anchor
        a_id = group[0]
        top_name = arms[a_id]["base"]["metrics"]["top_name_contribution"][0]
        timing_d = {k: v for k, v in timing.items() if k != top_name}
        revision_d = {k: v for k, v in revision.items() if k != top_name}
        drop = r.run_arm(a_id, timing_d, revision_d, prices, folds,
                         dry_run=False, owner_go=phrase, universe=universe,
                         sectors=sectors, price_manifest_sha=price_manifest_sha,
                         layer_digest=layer_digest, code_freeze_sha=head)
        cells.append({
            "cell_id": f"{a_id}-DROPONE", "arm_id": a_id, "family_id": family,
            "cost_tier": "base", "rerun": "drop_one_symbol",
            "excluded": top_name,
        })
        arms[a_id]["drop_one"] = drop

    observed_delta = len(cells)
    verdicts = {}
    all_gate_rows = []
    for family, group in ARM_GROUPS.items():
        a_id, n_id, c_id = group
        anchor_eval = evaluate(arms[a_id]["base"], bench["SPY"], sector_basket,
                               folds_order)
        neighbour_eval = evaluate(arms[n_id]["base"], bench["SPY"],
                                  sector_basket, folds_order)
        control_eval = evaluate(arms[c_id]["base"], bench["SPY"],
                                sector_basket, folds_order,
                                control_alpha=anchor_eval["alpha"])
        stress_m = arms[a_id]["stress"]["metrics"]
        stress_pf = stress_m["pf"]
        stress_ok = stress_m["sum_pnl"] > 0 and (stress_pf is None or stress_pf >= 1.0)
        drop_m = arms[a_id]["drop_one"]["metrics"]
        drop_exp = drop_m["expectancy"]
        l1o_ok, l1o_vals = drop_one_fold_ok(
            arms[a_id]["base"]["metrics"]["decision_pnl"], folds_order)
        drop_ok = drop_exp is not None and drop_exp > 0 and l1o_ok
        a_exp, n_exp, c_exp = (anchor_eval["expectancy"],
                               neighbour_eval["expectancy"],
                               control_eval["expectancy"])
        neighbour_support = (n_exp is not None and a_exp is not None
                             and (n_exp > 0) == (a_exp > 0))
        control_reproduces = (c_exp is not None and a_exp is not None
                              and (c_exp > 0) == (a_exp > 0)
                              and abs(c_exp) >= 0.5 * abs(a_exp))
        anchor_gates_pass = all(g["verdict"] == "PASS"
                                for g in anchor_eval["gates"])
        from research.assets.stocks.v9_e_driver import gate
        extra_gates = [
            gate("stress_positive", stress_ok,
                 {"sum_pnl": round(stress_m["sum_pnl"], 8), "pf": stress_pf},
                 "pnl>0 and pf>=1.0", "custom"),
            gate("drop_one_survival", bool(drop_ok),
                 {"drop_symbol_expectancy": round(drop_exp, 8) if drop_exp is not None else None,
                  "leave_one_fold_out_expectancy": l1o_vals},
                 "drop-symbol expectancy>0 and min leave-one-fold-out >0", "custom"),
            gate("neighbor_mechanism_support", bool(neighbour_support),
                 {"neighbour_expectancy": round(n_exp, 8) if n_exp is not None else None,
                  "anchor_expectancy": round(a_exp, 8) if a_exp is not None else None},
                 "same sign", "custom"),
        ]
        all_gate_rows.extend(anchor_eval["gates"] + extra_gates)
        if anchor_gates_pass and stress_ok and drop_ok and neighbour_support \
                and not control_reproduces:
            verdict = "STAGE_A_SURVIVOR_CANDIDATE"
        elif control_reproduces:
            verdict = "FALSIFIED_BY_CONTROL"
        else:
            verdict = "REJECT"
        verdicts[family] = {
            "anchor": {"arm_id": a_id, **anchor_eval,
                       "gates_all_pass": anchor_gates_pass},
            "neighbour": {"arm_id": n_id, "expectancy": n_exp,
                          "pf": neighbour_eval["pf"],
                          "support": neighbour_support},
            "control": {"arm_id": c_id, "expectancy": c_exp,
                        "reproduces_anchor": control_reproduces,
                        "gates": control_eval["gates"]},
            "packet_gates": extra_gates,
            "margin_to_fail_per_gate": {
                g["gate"]: g["margin"] for g in anchor_eval["gates"] + extra_gates
                if g.get("margin") is not None},
            "family_verdict": verdict,
        }

    ledger = {
        "schema": "stocks_free_v10_run/execution_ledger@1",
        "hypothesis_ids": list(ARM_GROUPS.keys()),
        "mode": "scored",
        "owner_go": phrase,
        "launch_authorized_env": True,
        "a7_prelaunch_verdict": "STOCKS_FREE_V10_S0_LAUNCH_AUTHORIZED",
        "code_freeze_sha": head,
        "price_manifest_sha256": price_manifest_sha,
        "observable_layer_digest": layer_digest,
        "cells": cells,
        "counters": kernel.driver_ledger_counters(
            observed_delta=observed_delta, published_delta=0),
    }
    assert_no_secrets(ledger)
    assert_no_secrets(verdicts)
    LEDGER.write_text(json.dumps(ledger, indent=1, sort_keys=True) + "\n")
    VERDICTS.write_text(json.dumps(verdicts, indent=1, sort_keys=True) + "\n")

    # publication: append-only bookkeeping, never edits the driver ledger
    prev = json.loads(PUBREC.read_text()) if PUBREC.exists() else None
    rec = kernel.append_publication_record(
        prev, cycle="STOCKS-FREE-V10", code_freeze_sha=head,
        published=[c["cell_id"] for c in cells
                   if c["cost_tier"] == "base" and "rerun" not in c],
        reruns=[c["cell_id"] for c in cells
                if c["cost_tier"] == "stress" or "rerun" in c],
        published_delta=6, rerun_delta=observed_delta - 6,
        note="reruns are not trials (V8 convention, adjudicated append-only)")
    PUBREC.write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n")

    published_ledger = json.loads(LEDGER.read_text())
    published_ledger["counters"] = kernel.driver_ledger_counters(
        observed_delta=observed_delta, published_delta=6)
    LEDGER.write_text(json.dumps(published_ledger, indent=1, sort_keys=True) + "\n")

    print(json.dumps({f: {"verdict": v["family_verdict"],
                          "anchor_expectancy": v["anchor"]["expectancy"],
                          "anchor_alpha": v["anchor"]["alpha"],
                          "gates_all_pass": v["anchor"]["gates_all_pass"],
                          "neighbour_support": v["neighbour"]["support"],
                          "control_reproduces": v["control"]["reproduces_anchor"]}
                     for f, v in verdicts.items()}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
