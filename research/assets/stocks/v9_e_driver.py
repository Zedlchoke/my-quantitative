"""V9 Phase E driver for the single selected family SFV9-A4-H2.

Modes
-----
--dry-run (the ONLY mode callable today): unscored wiring proof.  Emits a
sanitized ledger with scored=false, real_pnl=false, published=false, the
arm structure records (population, fills, turnover), the preregistered
SAMPLING FLOOR gate (median populated fraction >= 0.25 per decision,
else BLOCKED_DATA - sanctioned close, never re-matched or re-tuned) and
binding non-vacuity gates; pairwise-distinct record IDs are enforced.
The dry-run ledger is byte-deterministic: it carries NO wall-clock field.

Scored mode (INERT until Q/E): refuses unless BOTH keys are present
(two-key design; P-8: early or standing phrases never authorize):
  1. the exact owner GO phrase "GO STOCKS V9 SCORED EXECUTION" as argv, AND
  2. environment flag V9_LAUNCH_AUTHORIZED=1 set by A1 at Q/E time.

    python -m research.assets.stocks.v9_e_driver --dry-run
    python -m research.assets.stocks.v9_e_driver 'GO STOCKS V9 SCORED EXECUTION'   # + env key

The scored path runs the 3 frozen arms (base + stress rerun at 2x band
cost = 20/30/50 bps per side), the anchor drop-one-symbol rerun, evaluates
the inherited Stage-A gate table with margin-to-fail per gate (LESSONS
P-2) plus the packet gates (neighbour mechanism support, control
non-reproduction at |c| >= 0.5|a| = FALSIFIED_BY_CONTROL), and writes the
ledger with kernel_band_cost_v9.driver_ledger_counters ONLY (F-A7T-1:
driver-emitted counters; publish-time ledger edits are forbidden;
publication bookkeeping lives in append_publication_record).

EODHD key handling: environment-only; every error string passes through
redact(); no key material can enter any artifact (assert_no_secrets).
No raw staging byte is read from this repo: data roots come from
V9_REPO_ROOT (see v9_family_runner).
"""

import hashlib
import json
import os
import re
import statistics
import subprocess
import sys

from research.assets.stocks import kernel_band_cost_v9 as kernel
from research.assets.stocks import v9_family_runner as r

LEDGER = os.path.join(r.CONTROL_DIR, "execution_ledger.json")
VERDICTS = os.path.join(r.CONTROL_DIR, "family_verdicts.json")
LEDGER_DRYRUN = os.path.join(r.CONTROL_DIR, "execution_ledger_dryrun.json")
P3 = os.path.join(r.CONTROL_DIR, "p3_invariants_freeze.json")

SECTORS = ["XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY"]
NV_MIN_SCORED_OVERALL = 30       # p3 accounting: min scored decisions overall
NV_MIN_SCORED_PER_FOLD = 5       # p3 accounting: min scored decisions per fold
NV_MIN_LEGS_PER_DECISION = 1     # p3 accounting: min non-CASH legs per decision
ETF_SHARE_PACKET = 0.50          # packet gates_ex_ante "etf_share_le" row;
# the p3-frozen etf_positive_share_le = 0.35 also binds (tighter) - both reported

_REDACT = re.compile(r"api_token=[^&\s\"]+|EODHD_API_KEY=[^\s&\"]+")


def redact(text):
    """Redact key material from any error string (boundary: keys are
    environment-only and redacted from every error string and artifact)."""
    return _REDACT.sub("REDACTED", str(text))


def assert_no_secrets(obj):
    """Hard stop if key material leaked into an artifact."""
    blob = json.dumps(obj, default=str)
    if "EODHD_API_KEY" in blob or re.search(r"api_token=[^&\s\"]+", blob):
        raise RuntimeError(redact("secret material detected in artifact"))


def _find_key(obj, key):
    """Depth-first lookup for a freeze key (the P3 file nests carried
    payloads, so explicit paths are fragile)."""
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


def load_freezes(p3_path=P3):
    with open(p3_path) as f:
        p3 = json.load(f)
    gates = _find_key(p3, "stage_a_gates_carried_forward") or {}
    conc = _find_key(p3, "concentration_and_robustness") or {}
    return gates, conc


def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def sha256_json(path):
    with open(path, "rb") as f:
        return hashlib.sha256(json.dumps(json.load(f), sort_keys=True).encode()).hexdigest()


def gate(name, ok, observed, threshold, direction):
    """Inherited gate row with margin-to-fail (LESSONS P-2)."""
    num = isinstance(observed, (int, float)) and not isinstance(observed, bool)
    if num:
        margin = (round(observed - threshold, 6) if direction in ("gt", "ge")
                  else round(threshold - observed, 6))
    else:
        margin = None
    return {"gate": name, "verdict": "PASS" if ok else "FAIL",
            "observed": observed, "threshold": threshold,
            "margin_to_fail": margin}


def load_bench(bench_dir=None):
    """SPY + the 11 SPDR sector ETF total-return paths, from the SAME env
    data root as the panel/prices (tests point this at a tiny synthetic
    benchmark fixture)."""
    root = bench_dir or r.BENCH
    out = {}
    for t in ["SPY"] + SECTORS:
        with open(os.path.join(root, f"{t}.json")) as f:
            bars = json.load(f)
        out[t] = {"adj": [float(b["adjusted_close"]) for b in bars],
                  "pos": {b["date"]: i for i, b in enumerate(bars)}}
    return out


def window_return(bench, d0, d1):
    i0, i1 = bench["pos"].get(d0), bench["pos"].get(d1)
    if i0 is None or i1 is None or i1 <= i0:
        return None
    return bench["adj"][i1] / bench["adj"][i0] - 1.0


def sector_basket_from(bench):
    """Equal-weight sector basket adjusted path (mean of adjusted closes)."""
    series = {}
    for t in SECTORS:
        for d, i in bench[t]["pos"].items():
            series.setdefault(d, []).append(bench[t]["adj"][i])
    sdays = sorted(series)
    return {"pos": {d: i for i, d in enumerate(sdays)},
            "adj": [sum(series[d]) / len(series[d]) for d in sdays]}


def evaluate(rec, spy, sector_basket, folds_order, control_alpha=None,
             gates=None, conc=None):
    """Inherited Stage-A gate table for one scored arm record, with the
    packet additions (etf packet row); margin-to-fail per gate."""
    gates = gates or {}
    conc = conc or {}
    xs = rec["metrics"]["decision_pnl"]
    n = len(xs)
    e = sum(x["pnl"] for x in xs)
    wins = sum(x["pnl"] for x in xs if x["pnl"] > 0)
    losses = -sum(x["pnl"] for x in xs if x["pnl"] < 0)
    pf = wins / losses if losses > 0 else None
    per_fold = {f: [x["pnl"] for x in xs if x["fold"] == f] for f in folds_order}
    fold_pos = sum(1 for f in folds_order if per_fold[f] and sum(per_fold[f]) > 0)
    fold_pf, mdds = {}, {}
    for f in folds_order:
        fxs = per_fold[f]
        w = sum(x for x in fxs if x > 0)
        l = -sum(x for x in fxs if x < 0)
        fold_pf[f] = w / l if l > 0 else None
        cum = peak = m = 0.0
        for x in fxs:
            cum += x
            peak = max(peak, cum)
            m = max(m, peak - cum)
        mdds[f] = m
    alphas = []
    for x in xs:
        spy_r = window_return(spy, x["fill_d"], x["end_d"])
        if spy_r is not None:
            alphas.append(x["pnl"] - spy_r)
    alpha = sum(alphas) / len(alphas) if alphas else None
    alpha_folds = []
    for f in folds_order:
        fa = [x["pnl"] - wr for x in xs if x["fold"] == f
              for wr in [window_return(spy, x["fill_d"], x["end_d"])]
              if wr is not None]
        alpha_folds.append(sum(fa))
    pos_dec = [x for x in xs if x["pnl"] > 0]
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
        gate("position_pf_ge", pf is not None and pf >= gates.get("position_pf_ge", 1.1),
             round(pf, 4) if pf is not None else pf, gates.get("position_pf_ge", 1.1), "ge"),
        gate("folds_positive_ge",
             fold_pos >= gates.get("folds_positive_ge", 2), fold_pos,
             gates.get("folds_positive_ge", 2), "ge"),
        gate("min_populated_fold_pf_ge",
             any(v is not None for v in fold_pf.values())
             and all(v is None or v >= gates.get("min_populated_fold_pf_ge", 0.8)
                     for v in fold_pf.values()),
             {k: (round(v, 3) if v is not None else v) for k, v in fold_pf.items()},
             gates.get("min_populated_fold_pf_ge", 0.8), "ge"),
        gate("max_fold_mdd_le", max(mdds.values()) <= gates.get("max_fold_mdd_le", 0.15),
             round(max(mdds.values()), 4), gates.get("max_fold_mdd_le", 0.15), "le"),
        gate("fold_positive_share_le",
             pos_share <= conc.get("fold_positive_share_le", 0.5),
             round(pos_share, 4), conc.get("fold_positive_share_le", 0.5), "le"),
        gate("etf_positive_share_le",
             etf_share <= conc.get("etf_positive_share_le", 0.35),
             round(etf_share, 4), conc.get("etf_positive_share_le", 0.35), "le"),
        gate("etf_share_le_packet", etf_share <= ETF_SHARE_PACKET,
             round(etf_share, 4), ETF_SHARE_PACKET, "le"),
        gate("risk_matched_excess_positive_folds_ge",
             sum(1 for a in alpha_folds if a > 0)
             >= gates.get("risk_matched_excess_positive_folds_ge", 2),
             sum(1 for a in alpha_folds if a > 0),
             gates.get("risk_matched_excess_positive_folds_ge", 2), "ge"),
        gate("anchor_overall_alpha_gt", alpha is not None and alpha > 0,
             round(alpha, 8) if alpha is not None else None, 0.0, "gt"),
    ]
    if control_alpha is not None:
        ratio = abs(control_alpha) / abs(alpha) if alpha else None
        g.append(gate("control_alpha_abs_ratio_lt",
                      ratio is not None
                      and ratio < gates.get("control_alpha_abs_ratio_lt", 0.5),
                      round(ratio, 4) if ratio is not None else None,
                      gates.get("control_alpha_abs_ratio_lt", 0.5), "lt"))
    return {"gates": g, "expectancy": e, "pf": pf, "alpha": alpha,
            "fold_positive": fold_pos, "n_decisions": n,
            "per_fold_pnl": {f: round(sum(v), 8) for f, v in per_fold.items()},
            "mdd": {k: round(v, 6) for k, v in mdds.items()},
            "etf_share": round(etf_share, 4)}


def drop_one_fold_ok(decision_pnl, folds_order):
    """p3 drop_one_fold: min over folds of expectancy with that fold removed;
    survival = min > 0."""
    vals = []
    for drop in folds_order:
        rest = [x["pnl"] for x in decision_pnl if x["fold"] != drop]
        if not rest:
            return False, None
        vals.append(sum(rest))
    return (min(vals) > 0), [round(v, 8) for v in vals]


# ------------------------------------------------------------- dry run

def build_dry_run_ledger(code_freeze_sha, go_phrase_observed=None,
                         universe=None, panel=None, prices=None, folds=None,
                         panel_sha="", price_manifest_sha=""):
    """Unscored wiring proof.  Returns (ledger_dict, ok: bool).  Deterministic:
    no wall-clock anywhere; same inputs -> byte-equal ledger."""
    if universe is None:
        universe = r.load_universe()
    if panel is None:
        panel, counts = r.load_panel({r.RE_FIELD, r.CASH_FIELD, r.ASSETS_FIELD})
    else:
        counts = {"rows_read": -1, "rows_kept": -1}
    if prices is None:
        prices = r.load_prices()
    if folds is None:
        folds = r.fold_sessions(prices)
    if not panel_sha:
        panel_sha = sha256_file(r.PANEL)
    if not price_manifest_sha:
        price_manifest_sha = sha256_json(r.PRICE_MANIFEST_PATH)
    cells = []
    for arm_id in r.ARM_IDS:
        rec = r.run_arm(arm_id, panel, prices, folds, dry_run=True,
                        universe=universe, price_manifest_sha=price_manifest_sha,
                        panel_sha=panel_sha, code_freeze_sha=code_freeze_sha)
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
            "record": rec,
        })
    # sampling floor gate: anchor, non-warmup decisions (fiscal-matched
    # deltas are the lossy construction - the gate lives on the anchor)
    anchor = cells[0]["record"]["schedule"]
    fracs = [x["populated_frac"] for x in anchor
             if x.get("event") is None and not x["warmup"]]
    median_frac = statistics.median(fracs) if fracs else 0.0
    sampling = {
        "gate": "sampling_floor",
        "threshold": r.SAMPLING_FLOOR,
        "median_populated_frac": round(median_frac, 6),
        "decisions_measured": len(fracs),
        "verdict": "PASS" if median_frac >= r.SAMPLING_FLOOR else "BLOCKED_DATA",
    }
    # binding non-vacuity gates (anchor)
    scored = [x for x in anchor if x.get("event") is None and not x["warmup"]]
    per_fold_n = {}
    for x in scored:
        per_fold_n[x["fold"]] = per_fold_n.get(x["fold"], 0) + 1
    min_fold_n = min(per_fold_n.values()) if per_fold_n else 0
    min_legs = min((x["legs"] for x in scored), default=0)
    nv = [
        gate("nv_scored_decisions_overall_ge",
             len(scored) >= NV_MIN_SCORED_OVERALL, len(scored),
             NV_MIN_SCORED_OVERALL, "ge"),
        gate("nv_scored_decisions_per_fold_ge",
             min_fold_n >= NV_MIN_SCORED_PER_FOLD, min_fold_n,
             NV_MIN_SCORED_PER_FOLD, "ge"),
        gate("nv_noncash_legs_per_decision_ge",
             min_legs >= NV_MIN_LEGS_PER_DECISION, min_legs,
             NV_MIN_LEGS_PER_DECISION, "ge"),
    ]
    # pairwise-distinct record IDs across ALL cells (binding)
    ids = [srec["record_id"] for c in cells for srec in c["record"]["schedule"]]
    ids_distinct = len(set(ids)) == len(ids)
    if not ids_distinct:
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        raise ValueError(f"record IDs not pairwise distinct: {dupes[:5]}")
    counters = kernel.driver_ledger_counters(
        observed_delta=len(cells), published_delta=0)
    ledger = {
        "schema": "stocks_free_v9_run/execution_ledger_dryrun@1",
        "hypothesis_id": "SFV9-A4-H2",
        "mode": "dry_run",
        "scored": False,
        "real_pnl": False,
        "published": False,
        "producer_role": "A8 (implementation lane dry-run wiring proof; "
                         "outcome-blind, no PnL computed)",
        "code_freeze_sha": code_freeze_sha,
        "panel_sha256": panel_sha,
        "price_manifest_sha256": price_manifest_sha,
        "panel_rows_read": counts["rows_read"],
        "panel_rows_kept_usd": counts["rows_kept"],
        "go_phrase_observed": go_phrase_observed,
        "launch_flag_observed": bool(os.environ.get(r.LAUNCH_ENV)),
        "cells": cells,
        "sampling_floor_gate": sampling,
        "non_vacuity_gates": nv,
        "record_ids_pairwise_distinct": ids_distinct,
        "counters": counters,
    }
    assert_no_secrets(ledger)
    ok = (sampling["verdict"] == "PASS"
          and all(g["verdict"] == "PASS" for g in nv))
    return ledger, ok


# ------------------------------------------------------------- scored

def run_scored(phrase, code_freeze_sha, gates=None, conc=None,
               universe=None, panel=None, prices=None, folds=None,
               bench=None, panel_sha="", price_manifest_sha=""):
    """The scored pipeline.  CALLERS MUST HAVE PASSED the two-key check
    (run_arm re-checks per cell; this function refuses again up front so
    the driver itself stays inert without both keys)."""
    if not r.scored_authorized(phrase):
        raise SystemExit(
            "SCORED EXECUTION REFUSED: exact owner GO phrase and "
            f"{r.LAUNCH_ENV}=1 are both required (two-key)")
    gates = gates if gates is not None else load_freezes()[0]
    conc = conc if conc is not None else load_freezes()[1]
    if universe is None:
        universe = r.load_universe()
    if panel is None:
        panel, _ = r.load_panel({r.RE_FIELD, r.CASH_FIELD, r.ASSETS_FIELD})
    if prices is None:
        prices = r.load_prices()
    if folds is None:
        folds = r.fold_sessions(prices)
    if bench is None:
        bench = load_bench()
    if not panel_sha:
        panel_sha = sha256_file(r.PANEL)
    if not price_manifest_sha:
        price_manifest_sha = sha256_json(r.PRICE_MANIFEST_PATH)
    sector_basket = sector_basket_from(bench)
    folds_order = [f["fold_id"] for f in folds]
    arms = {}
    cells = []
    for arm_id in r.ARM_IDS:
        base = r.run_arm(arm_id, panel, prices, folds, dry_run=False,
                         owner_go=phrase, universe=universe,
                         price_manifest_sha=price_manifest_sha,
                         panel_sha=panel_sha, code_freeze_sha=code_freeze_sha)
        stress = r.run_arm(arm_id, panel, prices, folds, dry_run=False,
                           owner_go=phrase, universe=universe, stress=True,
                           price_manifest_sha=price_manifest_sha,
                           panel_sha=panel_sha, code_freeze_sha=code_freeze_sha)
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
                           folds_order, gates=gates, conc=conc)
    neighbour_eval = evaluate(arms[n_id]["base"], bench["SPY"], sector_basket,
                              folds_order, gates=gates, conc=conc)
    control_eval = evaluate(arms[c_id]["base"], bench["SPY"], sector_basket,
                            folds_order, gates=gates, conc=conc,
                            control_alpha=anchor_eval["alpha"])
    # anchor preregistered rerun: drop the max-contribution symbol
    top_name = arms[a_id]["base"]["metrics"]["top_name_contribution"][0]
    panel_drop = {k: v for k, v in panel.items() if k != top_name}
    drop = r.run_arm(a_id, panel_drop, prices, folds, dry_run=False,
                     owner_go=phrase, universe=universe,
                     price_manifest_sha=price_manifest_sha,
                     panel_sha=panel_sha, code_freeze_sha=code_freeze_sha)
    cells.append({
        "cell_id": f"{a_id}-DROPONE", "arm_id": a_id, "cost_tier": "base",
        "rerun": "drop_one_symbol", "excluded": top_name,
    })
    observed_delta = len(cells)
    # gates outside the per-arm table
    stress_m = arms[a_id]["stress"]["metrics"]
    stress_pf = stress_m["pf"]
    stress_ok = stress_m["sum_pnl"] > 0 and (stress_pf is None or stress_pf >= 1.0)
    drop_exp = drop["metrics"]["expectancy"]
    l1o_ok, l1o_vals = drop_one_fold_ok(
        arms[a_id]["base"]["metrics"]["decision_pnl"], folds_order)
    drop_ok = (drop_exp is not None and drop_exp > 0 and l1o_ok)
    a_exp, n_exp, c_exp = (anchor_eval["expectancy"],
                           neighbour_eval["expectancy"],
                           control_eval["expectancy"])
    neighbour_support = (n_exp is not None and a_exp is not None
                         and (n_exp > 0) == (a_exp > 0))
    control_reproduces = (c_exp is not None and a_exp is not None
                          and (c_exp > 0) == (a_exp > 0)
                          and abs(c_exp) >= 0.5 * abs(a_exp))
    anchor_gates_pass = all(g["verdict"] == "PASS" for g in anchor_eval["gates"])
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
    if anchor_gates_pass and stress_ok and drop_ok and neighbour_support \
            and not control_reproduces:
        verdict = "STAGE_A_SURVIVOR_CANDIDATE"
    elif control_reproduces:
        verdict = "FALSIFIED_BY_CONTROL"
    else:
        verdict = "REJECT"
    verdicts = {
        "SFV9-A4-H2": {
            "anchor": {"arm_id": a_id, **anchor_eval,
                       "gates_all_pass": anchor_gates_pass},
            "neighbour": {"arm_id": n_id, "expectancy": n_exp,
                          "pf": neighbour_eval["pf"],
                          "support": neighbour_support},
            "control": {"arm_id": c_id, "expectancy": c_exp,
                        "reproduces_anchor": control_reproduces,
                        "gates": control_eval["gates"]},
            "packet_gates": extra_gates,
            "sampling_floor_gate_note": "evaluated at dry-run "
                                        "(execution_ledger_dryrun.json)",
            "family_verdict": verdict,
        }
    }
    ledger = {
        "schema": "stocks_free_v9_run/execution_ledger@1",
        "hypothesis_id": "SFV9-A4-H2",
        "mode": "scored",
        "owner_go": phrase,
        "launch_authorized_env": True,
        "code_freeze_sha": code_freeze_sha,
        "panel_sha256": panel_sha,
        "price_manifest_sha256": price_manifest_sha,
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
    head = _git_head()
    if dry:
        try:
            ledger, ok = build_dry_run_ledger(
                head, go_phrase_observed=phrase)
        except Exception as e:  # noqa: BLE001 - redacted before display
            raise SystemExit(redact(f"dry-run failed: {e}"))
        with open(LEDGER_DRYRUN, "w") as f:
            json.dump(ledger, f, indent=1, sort_keys=True)
        print(json.dumps({
            "mode": "dry_run",
            "cells": [c["cell_id"] for c in ledger["cells"]],
            "sampling_floor_gate": ledger["sampling_floor_gate"],
            "non_vacuity_gates": [
                {"gate": g["gate"], "verdict": g["verdict"]}
                for g in ledger["non_vacuity_gates"]],
            "counters": ledger["counters"],
            "ok": ok,
        }, indent=1))
        if not ok:
            raise SystemExit(
                "DRY RUN BLOCKED: sampling floor or non-vacuity gate failed "
                "(BLOCKED_DATA is a sanctioned close; never re-matched, "
                "never re-tuned)")
        return 0
    # scored: two-key, fail closed, BEFORE any work
    if not r.scored_authorized(phrase):
        raise SystemExit(
            "REFUSED: scored execution needs the exact owner GO phrase "
            f"as argv AND {r.LAUNCH_ENV}=1 in the environment (two-key; "
            "P-8: early or standing phrases never authorize)")
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
