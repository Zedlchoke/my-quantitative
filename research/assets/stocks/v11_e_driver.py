"""V11 Phase E driver for the single selected family SFV11-A5-H1.

Modes
-----
--dry-run (the ONLY mode callable today): unscored wiring proof.  Emits a
SANITIZED ledger (research/control/stocks_free_v11_run/
execution_ledger_dryrun.json) with scored=false, real_pnl=false,
published=false, the three-arm structure records (population, fills,
turnover) and the binding NON-VACUITY gates (>= 30 scored decisions
overall, >= 5 per fold, >= 1 non-CASH leg per decision - zero decisions or
empty books = DRY_RUN_FAIL).  The dry-run ledger is byte-deterministic: it
carries NO wall-clock field, so same inputs -> byte-identical artifacts.

Scored mode (INERT until Q/E): refuses BEFORE ANY WORK unless BOTH keys
are present (two-key design; P-8: early or standing phrases never
authorize):
  1. the exact owner GO phrase "GO STOCKS V11 SCORED EXECUTION" as argv, AND
  2. environment flag V11_LAUNCH_AUTHORIZED=1 (set by the owner at Q/E
     time - this implementation lane never sets it).

    python -m research.assets.stocks.v11_e_driver --dry-run
    python -m research.assets.stocks.v11_e_driver 'GO STOCKS V11 SCORED EXECUTION'  # + env key

The scored path runs the 3 frozen arms (base + stress rerun at 2x band
cost = 20/30/50 bps per side, applied to booked PnL), the anchor
drop-one-symbol rerun, the drop-one-process-leg rerun (depth>=3-only
exposure), the frozen Stage-A gate table with margin-to-fail per gate
(LESSONS P-2) plus the packet gates (neighbour same-sign support; control
non-reproduction at |c_alpha| >= 0.5|a_alpha| same sign =
FALSIFIED_BY_CONTROL), and writes the ledger with
kernel_band_cost_v9.driver_ledger_counters ONLY (F-A7T-1: driver-emitted
counters; publish-time ledger edits are forbidden; publication
bookkeeping lives in a separate append-only record).

EODHD key handling: environment-only; every error string passes through
redact(); no key material can enter any artifact (assert_no_secrets).
No raw staging byte is read from this repo: data roots come from
v11_family_runner (V11_V9_ROOT / V11_V10_ROOT / V11_CONTROL_DIR knobs).
"""

import hashlib
import json
import os
import re
import subprocess
import sys

from research.assets.stocks import kernel_band_cost_v9 as kernel
from research.assets.stocks import v11_family_runner as r
from research.assets.stocks.v9_e_driver import (
    SECTORS,
    assert_no_secrets,
    evaluate,
    gate,
    load_bench,
    redact,
    sector_basket_from,
    sha256_file,
    sha256_json,
    window_return,
)
from research.assets.stocks.v9_family_runner import (
    FOLDS,
    fold_sessions,
    load_prices,
    load_universe,
)

LEDGER = os.path.join(r.RUN_DIR, "execution_ledger.json")
VERDICTS = os.path.join(r.RUN_DIR, "family_verdicts.json")
LEDGER_DRYRUN = os.path.join(r.RUN_DIR, "execution_ledger_dryrun.json")

# cohort pin (proposals/a5_process_H1.json universe.bookable_pool, verbatim)
COHORT_SHA_EXPECTED = ("6a95401ff84bff2144ac3c0b9426a6fa86daf3dde8d478195"
                       "666249e3fa2aa62")

# frozen Stage-A gate table (proposals/a5_process_H1.json
# stage_a_gates_applied_with_no_relaxation + frozen_thresholds; the v9
# evaluate() defaults coincide except the ETF rows, pinned here at 0.50)
FROZEN_GATES = {
    "position_pf_ge": 1.10,
    "min_populated_fold_pf_ge": 0.8,
    "folds_positive_ge": 2,
    "max_fold_mdd_le": 0.15,
    "fold_positive_share_le": 0.5,
    "etf_positive_share_le": 0.50,      # frozen_thresholds.etf_share_gate
    "risk_matched_excess_positive_folds_ge": 2,
    "control_alpha_abs_ratio_lt": 0.5,  # frozen_thresholds.control_alpha_ratio_kill
}
ETF_SHARE_PACKET = 0.50  # falsifiable_prediction (e): ETF positive share <= 0.50

NV_MIN_SCORED_OVERALL = 30       # turnover_and_sample_floor: >= 30 overall
NV_MIN_SCORED_PER_FOLD = 5       # >= 5 per fold
NV_MIN_LEGS_PER_DECISION = 1     # >= 1 non-CASH leg per decision


def redact_v11(text):
    return redact(text)


def sha256_big(path):
    """Chunked sha256 of a large staged file (never read whole)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_key(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            found = _find_key(v, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for v in obj:
            found = _find_key(v, key)
            if found is not None:
                return found
    return None


# ------------------------------------------------------------- layers

def build_layers(verify_pins=True, revision_path=None, timing_path=None,
                 cohort_path=None, scan_path=None, manifest_path=None,
                 expected_join=None):
    """Load the staged world for both modes: cohort universe + sectors, the
    revision/timing layers (full-census load), the depth join with the
    row-count reconciliation (production default: the P0 census
    1,667,422; overridden ONLY by synthetic fixtures), and the sha pins
    (fail-closed on any mismatch).  verify_pins=False is for synthetic
    fixtures ONLY - shas are then supplied by the caller of run_arm."""
    cohort_path = cohort_path or r.COHORT_PATH
    scan_path = scan_path or r.INTEGRITY_SCAN_PATH
    manifest_path = manifest_path or r.PRICE_MANIFEST_PATH
    revision_path = revision_path or r.REVISION_PATH
    timing_path = timing_path or r.TIMING_PATH
    universe = load_universe(cohort_path, scan_path)
    sectors = r.load_sectors(cohort_path)
    rev_rows, rev_counts = r.load_revision_layer(revision_path)
    depth_map, tim_counts = r.load_timing_depth(timing_path)
    stacks, join = r.build_stacks(
        rev_rows, depth_map,
        expected_join=(r.CENSUS_REVISION_GROUPS if expected_join is None
                       else expected_join))
    stacks_d3 = stacks  # same stacks; the d3 prefix arrays ride along
    if verify_pins:
        rev_sha = sha256_big(revision_path)
        tim_sha = sha256_big(timing_path)
        if rev_sha != r.REVISION_SHA_EXPECTED:
            raise SystemExit(
                f"REVISION layer sha mismatch: measured {rev_sha} != pinned "
                f"{r.REVISION_SHA_EXPECTED} - fail closed")
        if tim_sha != r.TIMING_SHA_EXPECTED:
            raise SystemExit(
                f"TIMING layer sha mismatch: measured {tim_sha} != pinned "
                f"{r.TIMING_SHA_EXPECTED} - fail closed")
        cohort_sha = sha256_file(cohort_path)
        if cohort_sha != COHORT_SHA_EXPECTED:
            raise SystemExit(
                f"cohort sha mismatch: measured {cohort_sha} != pinned "
                f"{COHORT_SHA_EXPECTED} - fail closed")
    else:
        rev_sha = tim_sha = cohort_sha = ""
    return {
        "universe": universe, "sectors": sectors, "stacks": stacks,
        "stacks_d3": stacks_d3, "counts": {
            "revision_rows_read": rev_counts["rows_read"],
            "revision_rows_kept": rev_counts["rows_kept"],
            "timing_rows_read": tim_counts["rows_read"],
            "timing_rows_kept_depth_ge2": tim_counts["rows_kept"],
            "joined_group_rows": join["joined_rows"],
        },
        "revision_sha": rev_sha, "timing_sha": tim_sha,
        "cohort_sha": cohort_sha,
        "price_manifest_sha": sha256_json(manifest_path),
    }


# ------------------------------------------------------------- dry run

def _nv_gate_rows(scored_records):
    """The three binding non-vacuity gate rows for one arm's decision
    records (margin-to-fail per gate, LESSONS P-2)."""
    per_fold = {}
    for x in scored_records:
        per_fold[x["fold"]] = per_fold.get(x["fold"], 0) + 1
    min_fold_n = min(per_fold_n for per_fold_n in per_fold.values()) \
        if per_fold else 0
    min_legs = min((x["legs"] for x in scored_records), default=0)
    return [
        gate("nv_scored_decisions_overall_ge",
             len(scored_records) >= NV_MIN_SCORED_OVERALL,
             len(scored_records), NV_MIN_SCORED_OVERALL, "ge"),
        gate("nv_scored_decisions_per_fold_ge",
             min_fold_n >= NV_MIN_SCORED_PER_FOLD, min_fold_n,
             NV_MIN_SCORED_PER_FOLD, "ge"),
        gate("nv_noncash_legs_per_decision_ge",
             min_legs >= NV_MIN_LEGS_PER_DECISION, min_legs,
             NV_MIN_LEGS_PER_DECISION, "ge"),
    ]


def build_dry_run_ledger(code_freeze_sha, go_phrase_observed=None,
                         layers=None, prices=None, folds=None):
    """Unscored wiring proof over the EXACT three frozen arms.  Returns
    (ledger_dict, ok: bool).  Deterministic: no wall-clock anywhere; same
    inputs -> byte-equal ledger."""
    if layers is None:
        layers = build_layers()
    if prices is None:
        prices = load_prices()
    if folds is None:
        folds = fold_sessions(prices, FOLDS)
    cells = []
    for arm_id in r.ARM_IDS:
        rec = r.run_arm(
            arm_id, layers["stacks"], prices, folds, dry_run=True,
            universe=layers["universe"], sectors=layers["sectors"],
            price_manifest_sha=layers["price_manifest_sha"],
            revision_sha=layers["revision_sha"],
            timing_sha=layers["timing_sha"],
            cohort_sha=layers["cohort_sha"],
            code_freeze_sha=code_freeze_sha)
        scored_records = [x for x in rec["schedule"]
                          if x.get("event") is None and not x["warmup"]]
        cells.append({
            "cell_id": f"{arm_id}-DRYRUN",
            "arm_id": arm_id,
            "family_id": rec["family_id"],
            "scored": False,
            "real_pnl": False,
            "published": False,
            "decisions_total": rec["decisions_total"],
            "scored_decisions_total": rec["scored_decisions_total"],
            "void_entry_orders": rec["void_entry_orders"],
            "terminations": rec["terminations"],
            "non_vacuity_gates": _nv_gate_rows(scored_records),
            "record": rec,
        })
    # binding non-vacuity gates: worst case ACROSS the three arms (each arm
    # must independently satisfy the frozen sample floors)
    agg = []
    for gi, gname in enumerate(("nv_scored_decisions_overall_ge",
                                "nv_scored_decisions_per_fold_ge",
                                "nv_noncash_legs_per_decision_ge")):
        rows = [c["non_vacuity_gates"][gi] for c in cells]
        worst = min(rows, key=lambda g: (g["observed"]
                                         if isinstance(g["observed"], (int, float))
                                         else 0))
        ok = all(g["verdict"] == "PASS" for g in rows)
        agg.append({
            "gate": gname, "verdict": "PASS" if ok else "FAIL",
            "observed": worst["observed"], "threshold": worst["threshold"],
            "margin_to_fail": worst["margin_to_fail"],
        })
    # pairwise-distinct record IDs across ALL cells (binding)
    ids = [srec["record_id"] for c in cells for srec in c["record"]["schedule"]]
    ids_distinct = len(set(ids)) == len(ids)
    if not ids_distinct:
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        raise ValueError(f"record IDs not pairwise distinct: {dupes[:5]}")
    counters = kernel.driver_ledger_counters(
        observed_delta=len(cells), published_delta=0)
    ledger = {
        "schema": "stocks_free_v11_run/execution_ledger_dryrun@1",
        "hypothesis_id": r.HYPOTHESIS_ID,
        "mode": "dry_run",
        "scored": False,
        "real_pnl": False,
        "published": False,
        "producer_role": "A8 (implementation lane dry-run wiring proof; "
                         "outcome-blind, no PnL computed)",
        "code_freeze_sha": code_freeze_sha,
        "revision_sha256": layers["revision_sha"],
        "timing_sha256": layers["timing_sha"],
        "cohort_sha256": layers["cohort_sha"],
        "price_manifest_sha256": layers["price_manifest_sha"],
        "layer_counts": layers["counts"],
        "go_phrase_observed": go_phrase_observed,
        "launch_flag_observed": bool(os.environ.get(r.LAUNCH_ENV)),
        "cells": cells,
        "non_vacuity_gates": agg,
        "record_ids_pairwise_distinct": ids_distinct,
        "counters": counters,
    }
    assert_no_secrets(ledger)
    ok = all(g["verdict"] == "PASS" for g in agg)
    return ledger, ok


# ------------------------------------------------------------- scored

def drop_one_fold_expectancy(decision_pnl, folds_order):
    """drop-one-fold: min over folds of EXPECTANCY with that fold removed
    (mean over the remaining scored decisions); survival = min > 0."""
    vals = []
    for drop in folds_order:
        rest = [x["pnl"] for x in decision_pnl if x["fold"] != drop]
        if not rest:
            return False, None
        vals.append(sum(rest) / len(rest))
    return (min(vals) > 0), [round(v, 10) for v in vals]


def run_scored(phrase, code_freeze_sha, layers=None, prices=None, folds=None,
               bench=None):
    """The scored pipeline.  CALLERS MUST HAVE PASSED the two-key check
    (run_arm re-checks per cell; this function refuses again up front so
    the driver itself stays inert without both keys)."""
    if not r.scored_authorized(phrase):
        raise SystemExit(
            "SCORED EXECUTION REFUSED: exact owner GO phrase and "
            f"{r.LAUNCH_ENV}=1 are both required (two-key)")
    if layers is None:
        layers = build_layers()
    if prices is None:
        prices = load_prices()
    if folds is None:
        folds = fold_sessions(prices, FOLDS)
    if bench is None:
        bench = load_bench()
    sector_basket = sector_basket_from(bench)
    folds_order = [f["fold_id"] for f in folds]
    common = dict(universe=layers["universe"], sectors=layers["sectors"],
                  price_manifest_sha=layers["price_manifest_sha"],
                  revision_sha=layers["revision_sha"],
                  timing_sha=layers["timing_sha"],
                  cohort_sha=layers["cohort_sha"],
                  code_freeze_sha=code_freeze_sha)
    arms = {}
    cells = []
    for arm_id in r.ARM_IDS:
        base = r.run_arm(arm_id, layers["stacks"], prices, folds,
                         dry_run=False, owner_go=phrase, **common)
        stress = r.run_arm(arm_id, layers["stacks"], prices, folds,
                           dry_run=False, owner_go=phrase, stress=True,
                           **common)
        arms[arm_id] = {"base": base, "stress": stress}
        for tier, rec in (("base", base), ("stress", stress)):
            cells.append({
                "cell_id": f"{arm_id}-{tier.upper()}",
                "arm_id": arm_id, "cost_tier": tier,
                "arm_config_digest": rec["arm_config_digest"],
                "data_snapshot_digest": rec["data_snapshot_digest"],
                "scored_decisions": rec["scored_decisions_total"],
                "void_entry_orders": rec["void_entry_orders"],
                "terminations": rec["terminations"],
            })
    a_id, n_id, c_id = r.ARM_IDS
    anchor_eval = evaluate(arms[a_id]["base"], bench["SPY"], sector_basket,
                           folds_order, gates=dict(FROZEN_GATES),
                           conc={"etf_positive_share_le": ETF_SHARE_PACKET,
                                 "fold_positive_share_le":
                                     FROZEN_GATES["fold_positive_share_le"]})
    neighbour_eval = evaluate(arms[n_id]["base"], bench["SPY"],
                              sector_basket, folds_order,
                              gates=dict(FROZEN_GATES),
                              conc={"etf_positive_share_le": ETF_SHARE_PACKET,
                                    "fold_positive_share_le":
                                        FROZEN_GATES["fold_positive_share_le"]})
    control_eval = evaluate(arms[c_id]["base"], bench["SPY"],
                            sector_basket, folds_order,
                            gates=dict(FROZEN_GATES),
                            conc={"etf_positive_share_le": ETF_SHARE_PACKET,
                                  "fold_positive_share_le":
                                      FROZEN_GATES["fold_positive_share_le"]},
                            control_alpha=anchor_eval["alpha"])
    # anchor preregistered rerun 1: drop the max-contribution symbol
    top_name = arms[a_id]["base"]["metrics"]["top_name_contribution"][0]
    stacks_drop = {k: v for k, v in layers["stacks"].items() if k != top_name}
    drop_sym = r.run_arm(a_id, stacks_drop, prices, folds, dry_run=False,
                         owner_go=phrase, **common)
    cells.append({
        "cell_id": f"{a_id}-DROPONE-SYMBOL", "arm_id": a_id,
        "cost_tier": "base", "rerun": "drop_one_symbol", "excluded": top_name,
    })
    # anchor preregistered rerun 2: process-leg depth >= 3 only
    drop_d3 = r.run_arm(a_id, layers["stacks_d3"], prices, folds,
                        dry_run=False, owner_go=phrase,
                        kind_override="late_share_depth3", **common)
    cells.append({
        "cell_id": f"{a_id}-DROPONE-PROCESS-LEG", "arm_id": a_id,
        "cost_tier": "base", "rerun": "drop_one_process_leg_depth_ge3",
    })
    observed_delta = len(cells)
    a_exp = anchor_eval["expectancy"]
    a_alpha = anchor_eval["alpha"]
    n_exp = neighbour_eval["expectancy"]
    c_exp = control_eval["expectancy"]
    c_alpha = control_eval["alpha"]
    # gates outside the per-arm table (frozen falsifiable_prediction + drops)
    drop_sym_exp = drop_sym["metrics"]["expectancy"]
    d3_exp = drop_d3["metrics"]["expectancy"]
    l1o_ok, l1o_vals = drop_one_fold_expectancy(
        arms[a_id]["base"]["metrics"]["decision_pnl"], folds_order)
    neighbour_support = (n_exp is not None and a_exp is not None
                         and (n_exp > 0) == (a_exp > 0))
    # falsification rule on SPY-excess ALPHA (frozen (g): same-sign
    # reproduction at >= 0.5x kills the family)
    control_reproduces = (c_alpha is not None and a_alpha not in (None, 0)
                          and (c_alpha > 0) == (a_alpha > 0)
                          and abs(c_alpha) >= 0.5 * abs(a_alpha))
    drop_sym_ok = drop_sym_exp is not None and drop_sym_exp > 0
    drop_d3_ok = (d3_exp is not None and a_exp is not None
                  and (d3_exp > 0) == (a_exp > 0) and d3_exp > 0)
    anchor_gates_pass = all(g["verdict"] == "PASS"
                            for g in anchor_eval["gates"])
    extra_gates = [
        gate("drop_one_symbol_survival", bool(drop_sym_ok),
             {"drop_symbol_expectancy":
                 round(drop_sym_exp, 10) if drop_sym_exp is not None else None,
              "excluded": top_name},
             "after-drop expectancy>0", "custom"),
        gate("drop_one_fold_survival", bool(l1o_ok),
             {"leave_one_fold_out_expectancy": l1o_vals},
             "min fold-removed expectancy>0", "custom"),
        gate("drop_one_process_leg_survival", bool(drop_d3_ok),
             {"depth3_expectancy":
                 round(d3_exp, 10) if d3_exp is not None else None,
              "anchor_expectancy":
                 round(a_exp, 10) if a_exp is not None else None},
             "sign preservation and expectancy>0", "custom"),
        gate("neighbor_mechanism_support", bool(neighbour_support),
             {"neighbour_expectancy":
                 round(n_exp, 10) if n_exp is not None else None,
              "anchor_expectancy":
                 round(a_exp, 10) if a_exp is not None else None},
             "same sign", "custom"),
    ]
    if control_reproduces:
        verdict = "FALSIFIED_BY_CONTROL"
    elif anchor_gates_pass and drop_sym_ok and l1o_ok and drop_d3_ok \
            and neighbour_support:
        verdict = "STAGE_A_SURVIVOR_CANDIDATE"
    else:
        verdict = "REJECT"
    verdicts = {
        r.HYPOTHESIS_ID: {
            "anchor": {"arm_id": a_id, **anchor_eval,
                       "gates_all_pass": anchor_gates_pass},
            "neighbour": {"arm_id": n_id, "expectancy": n_exp,
                          "pf": neighbour_eval["pf"],
                          "alpha": neighbour_eval["alpha"],
                          "support": neighbour_support},
            "control": {"arm_id": c_id, "expectancy": c_exp,
                        "alpha": c_alpha,
                        "reproduces_anchor": control_reproduces,
                        "gates": control_eval["gates"]},
            "packet_gates": extra_gates,
            "stress_note": ("stress rerun (2x band cost) reported "
                            "alongside base in the ledger cells; the frozen "
                            "gate list carries no stress-survival row"),
            "family_verdict": verdict,
        }
    }
    ledger = {
        "schema": "stocks_free_v11_run/execution_ledger@1",
        "hypothesis_id": r.HYPOTHESIS_ID,
        "mode": "scored",
        "owner_go": phrase,
        "launch_authorized_env": True,
        "code_freeze_sha": code_freeze_sha,
        "revision_sha256": layers["revision_sha"],
        "timing_sha256": layers["timing_sha"],
        "cohort_sha256": layers["cohort_sha"],
        "price_manifest_sha256": layers["price_manifest_sha"],
        "cells": cells,
        "counters": kernel.driver_ledger_counters(
            observed_delta=observed_delta, published_delta=0),
    }
    assert_no_secrets(ledger)
    assert_no_secrets(verdicts)
    return ledger, verdicts


# ---------------------------------------------------------------- main

def _git_head():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    except Exception as e:  # noqa: BLE001 - redacted, never retried blind
        raise SystemExit(redact(f"cannot resolve code freeze sha: {e}"))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    dry = "--dry-run" in argv
    positional = [a for a in argv if a != "--dry-run"]
    phrase = positional[0] if positional else None
    if dry:
        head = _git_head()
        try:
            ledger, ok = build_dry_run_ledger(
                head, go_phrase_observed=phrase)
        except Exception as e:  # noqa: BLE001 - redacted before display
            raise SystemExit(redact(f"dry-run failed: {e}"))
        os.makedirs(os.path.dirname(LEDGER_DRYRUN), exist_ok=True)
        with open(LEDGER_DRYRUN, "w") as f:
            json.dump(ledger, f, indent=1, sort_keys=True)
        print(json.dumps({
            "mode": "dry_run",
            "cells": [c["cell_id"] for c in ledger["cells"]],
            "non_vacuity_gates": [
                {"gate": g["gate"], "verdict": g["verdict"],
                 "observed": g["observed"], "margin_to_fail": g["margin_to_fail"]}
                for g in ledger["non_vacuity_gates"]],
            "counters": ledger["counters"],
            "ok": ok,
        }, indent=1))
        if not ok:
            raise SystemExit(
                "DRY_RUN_FAIL: non-vacuity gate failed (zero decisions or "
                "empty books) - BLOCKED_DATA is a sanctioned close; never "
                "re-matched, never re-tuned")
        return 0
    # scored: two-key, fail closed, BEFORE ANY WORK (no repo probe, no load)
    if not r.scored_authorized(phrase):
        raise SystemExit(
            "REFUSED: scored execution needs the exact owner GO phrase "
            f"as argv AND {r.LAUNCH_ENV}=1 in the environment (two-key; "
            "P-8: early or standing phrases never authorize)")
    head = _git_head()
    try:
        ledger, verdicts = run_scored(phrase, head)
    except Exception as e:  # noqa: BLE001 - redacted before display
        raise SystemExit(redact(f"scored run failed: {e}"))
    with open(LEDGER, "w") as f:
        json.dump(ledger, f, indent=1, sort_keys=True)
    with open(VERDICTS, "w") as f:
        json.dump(verdicts, f, indent=1, sort_keys=True)
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
