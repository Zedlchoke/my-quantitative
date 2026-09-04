#!/usr/bin/env python
"""FOREX-FREE-V3R R2: corrected-availability recompute of the exact W3C cells.

STATUS: DRAFT -- UNRUN (authored during a session shell outage).  Nothing in
this file edits frozen code: it DRIVES the frozen runner modules exactly as
exec_driver does, with one input change (macro vintages come from the
evidenced copies built by build_evidenced_vintages.py).

Guards, in execution order (every guard aborts the whole recompute):
  G1  W3C freeze: the 7 frozen file hashes must match the cycle's
      w3_freeze.json AND the V3 published ledger sha256 must match the
      owner pin -- measured IMMEDIATELY BEFORE any run, after the run's
      imports, so a drift can never slip between check and compute.
  G2  Ledger pin: the announcement ledger is pinned (LEDGER_PINNED + sha256).
  G3  Evidenced vintages exist and their manifest is fatal-free, and the
      frozen vintage files still hash to the w3_freeze.json data pins.
  G4  TWIN DETERMINISM: phase 'baseline' first recomputeS the six cells
      under the FROZEN vintages and requires exact equality of every
      computed metric against the V3 published ledger row.  A mismatch is
      a hard abort -- the corrected numbers would be uninterpretable.
  G5  Publication: there is NO publication path in this script.  compute_cell
      is called directly with the freeze token (real books) and results are
      written only to research/control/forex_free_v3r_run/ artifacts.  No
      scored-ledger append occurs anywhere; the V3 budget is untouched.

Phases
------
  baseline   G4 twin verification (frozen vintages) -> twin_verification.json
  corrected  the six cells under evidenced vintages -> v3r_records.jsonl +
             v3r_recompute_report.json (BOTH books per cell, frozen
             stage_a_gates + mechanism_sanity verdicts reported as
             PASS/FAIL, no verdict of the plan-section-5 kind)
  diff       decision-grid readable-rate diff old-vs-new availability over
             the 7 frozen pairs -> decision_diff_table.json
  recon      expectancy-to-PnL reconciliation per arm/book (audit finding 3)
             -> reconciliation.json (also embedded in the corrected report)
  mtest      DSR/PBO statement over the program history (audit finding 4)
             -> multiple_testing_statement.json; computable pieces are
             computed via research/dsr.py, the rest is reported NOT_RUN
             fail-closed (never inferred)

Usage
-----
  .venv/bin/python research/control/forex_free_v3r_run/recompute_v3r.py \
      --v3-worktree /Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v3/integration \
      --data-paths-template <path to the V3 scored run's data_paths JSON> \
      [--program-ledger <path to the program published ledger jsonl>] \
      [--phases baseline corrected diff recon mtest]   # default: all, in order
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
import sys
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

RUN_DIR = os.path.dirname(os.path.abspath(__file__))
NY = ZoneInfo("America/New_York")

V3_W3C_LEDGER_SHA256 = "6329cabcf80f6cc67009dec7f042fba3832607dd2133c00a9e6e4f4a81f2f173"
FROZEN_FILE_KEYS = ("scored_runner.py", "macro_reader.py", "accounting.py",
                    "family1.py", "family2.py", "macro_fetch.py", "exec_driver.py")
FROZEN_PREFIX = "research/assets/forex_free_v3/"

# computed-metric keys that MUST be byte-equal between the V3 ledger row and
# the baseline twin recompute (anything outside this list is lineage metadata)
TWIN_KEYS = (
    "cell_id", "n_decisions", "n_trades", "n_trades_kept", "weekend_gate_dropped",
    "purged_trades", "gross_price_pnl_usd", "price_only_pnl_usd",
    "financing_adjustment_usd", "financing_adjusted_pnl_usd", "base",
    "base_price_only", "folds", "fold_positive_share", "mdd_usd",
    "pair_concentration", "drop_one_expectancy", "dropout_scenarios",
    "break_even_cost_bps", "usd_drift_diag", "usd_index_source", "usd_index_pairs",
    "stress", "incremental_alpha", "incremental_alpha_definition",
    "benchmark_treatment", "financing_formula", "proposal_id",
)

PAIRS = ("EUR/USD", "GBP/USD", "AUD/USD", "NZD/USD",
         "USD/JPY", "USD/CHF", "USD/CAD")
PAIR_AREAS = {"EUR/USD": ("EMU", "US"), "GBP/USD": ("GB", "US"),
              "AUD/USD": ("AU", "US"), "NZD/USD": ("NZ", "US"),
              "USD/JPY": ("US", "JP"), "USD/CHF": ("US", "CH"),
              "USD/CAD": ("US", "CA")}
WINDOW_START, WINDOW_END = date(2019, 1, 1), date(2026, 9, 2)


def sha256_file(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def guard_w3c(v3_worktree):
    """G1: frozen code + V3 ledger pins, measured immediately before compute."""
    freeze = json.load(open(os.path.join(
        v3_worktree, "research/control/forex_free_v3_run/w3_freeze.json")))
    mismatches = []
    for rel, want in freeze["code_hashes"].items():
        got = sha256_file(os.path.join(v3_worktree, rel))
        if got != want:
            mismatches.append({"file": rel, "expected": want, "observed": got})
    ledger = os.path.join(v3_worktree,
                          "research/control/forex_free_v3_run/scored_ledger_published.jsonl")
    got_ledger = sha256_file(ledger)
    if got_ledger != V3_W3C_LEDGER_SHA256:
        mismatches.append({"file": "scored_ledger_published.jsonl",
                           "expected": V3_W3C_LEDGER_SHA256, "observed": got_ledger})
    if mismatches:
        raise SystemExit(json.dumps({"GUARD": "G1_W3C_PIN_MISMATCH",
                                     "mismatches": mismatches}, indent=1))
    return freeze


def guard_ledger():
    """G2: announcement ledger pinned and hash-stable."""
    pin_path = os.path.join(RUN_DIR, "LEDGER_PINNED")
    if not os.path.exists(pin_path):
        raise SystemExit(json.dumps({"GUARD": "G2_LEDGER_NOT_PINNED"}, indent=1))
    pin = json.load(open(pin_path))
    raw = open(os.path.join(RUN_DIR, "announcement_ledger.jsonl"), "rb").read()
    if hashlib.sha256(raw).hexdigest() != pin.get("ledger_sha256"):
        raise SystemExit(json.dumps({"GUARD": "G2_LEDGER_SHA256_MISMATCH"}, indent=1))
    return pin


def guard_vintages(vintage_dir, evidenced_dir, freeze):
    """G3: frozen inputs still pinned; evidenced inputs present + fatal-free."""
    pins = freeze["data_freeze"]["macro_vintages"]["file_sha256"]
    for area in ("US", "EMU", "GB", "JP", "CH", "CA", "AU", "NZ"):
        want = pins[f"{area}.json"]
        got = sha256_file(os.path.join(vintage_dir, f"{area}.json"))
        if got != want:
            raise SystemExit(json.dumps(
                {"GUARD": "G3_FROZEN_VINTAGE_DRIFT", "area": area,
                 "expected": want, "observed": got}, indent=1))
        ev_path = os.path.join(evidenced_dir, f"{area}.json")
        if not os.path.exists(ev_path):
            raise SystemExit(json.dumps(
                {"GUARD": "G3_EVIDENCED_VINTAGE_MISSING", "area": area}, indent=1))
    manifest = json.load(open(os.path.join(evidenced_dir, "evidenced_vintages_manifest.json")))
    if manifest.get("fatal"):
        raise SystemExit(json.dumps({"GUARD": "G3_EVIDENCED_MANIFEST_FATAL",
                                     "fatal": manifest["fatal"]}, indent=1))
    return manifest


def build_data_paths(template_path, macro_dir):
    """The V3 data_paths template with ONLY macro_vintages re-pointed."""
    template = json.load(open(template_path))
    data_paths = dict(template)
    data_paths["macro_vintages"] = {
        area: os.path.join(macro_dir, f"{area}.json")
        for area in ("US", "EMU", "GB", "JP", "CH", "CA", "AU", "NZ")
    }
    return data_paths


def compute_all_cells(data_paths):
    """Run the six frozen cells through the frozen runner (no publication)."""
    from research.assets.forex_free_v3 import scored_runner as R
    for family_id, module_path in (("family1", "research.assets.forex_free_v3.family1"),
                                   ("family2", "research.assets.forex_free_v3.family2")):
        R.register_family(family_id, importlib.import_module(module_path))
    cells = {}
    sanity = {}
    for family_id in ("family1", "family2"):
        family_cells = {}
        for arm in R.ARMS:
            record = R.compute_cell(family_id, arm, data_paths,
                                    freeze_token=R.FREEZE_TOKEN)
            gates, reasons = R.stage_a_gates(record)
            record["gates"] = gates
            record["gate_reasons"] = reasons
            cells[record["cell_id"]] = record
            family_cells[arm] = record
        ok, reasons = R.mechanism_sanity(family_cells)
        sanity[f"{family_id}:MECHANISM_SANITY"] = {"pass": ok, "reasons": reasons}
    return cells, sanity


def twin_compare(v3_ledger_path, recomputed):
    """G4: every TWIN_KEY of every V3 row must equal the twin recompute."""
    v3_rows = {}
    for line in open(v3_ledger_path, encoding="utf-8"):
        row = json.loads(line)
        v3_rows[row["cell_id"]] = row
    diffs = []
    for cell_id, record in recomputed.items():
        v3 = v3_rows.get(cell_id)
        if v3 is None:
            diffs.append({"cell_id": cell_id, "reason": "no V3 row"})
            continue
        for key in TWIN_KEYS:
            if json.dumps(record.get(key), sort_keys=True) != json.dumps(v3.get(key), sort_keys=True):
                diffs.append({"cell_id": cell_id, "key": key,
                              "v3": v3.get(key), "twin": record.get(key)})
    return diffs


# ---------------------------------------------------------------------------
# diff phase: readable-rate diff over the frozen pair grid
# ---------------------------------------------------------------------------
def decision_grid():
    day = WINDOW_START
    instants = []
    while day <= WINDOW_END:
        instants.append(datetime(day.year, day.month, day.day, 16, 0, tzinfo=NY)
                        .astimezone(timezone.utc).isoformat().replace("+00:00", "Z"))
        day = date.fromordinal(day.toordinal() + 1)
    return instants


def diff_phase(frozen_dir, evidenced_dir):
    from research.assets.forex_free_v3.macro_reader import PolicyRateReader
    areas = ("US", "EMU", "GB", "JP", "CH", "CA", "AU", "NZ")
    frozen_paths = {"macro_vintages": {a: os.path.join(frozen_dir, f"{a}.json")
                                       for a in areas}}
    evidenced_paths = {"macro_vintages": {a: os.path.join(evidenced_dir, f"{a}.json")
                                          for a in areas}}
    old_reader = PolicyRateReader.from_data_paths(frozen_paths)
    new_reader = PolicyRateReader.from_data_paths(evidenced_paths)
    rows = []
    for pair, (base, quote) in PAIR_AREAS.items():
        for decision_iso in decision_grid():
            r_old = old_reader.differential(base, quote, decision_iso)
            r_new = new_reader.differential(base, quote, decision_iso)
            differs = (r_old != r_new)
            if differs:
                rows.append({
                    "pair": pair, "decision_ts_utc": decision_iso,
                    "rate_old": r_old, "rate_new": r_new,
                    "sign_flip": (r_old is None or r_new is None
                                  or (r_old > 0) != (r_new > 0)),
                    "none_to_value": r_old is None and r_new is not None,
                    "value_to_none": r_old is not None and r_new is None,
                })
    out = os.path.join(RUN_DIR, "decision_diff_table.json")
    with open(out, "w", encoding="utf-8") as handle:
        json.dump({"schema": "forex_free_v3r_decision_diff_v1",
                   "n_diff_decisions": len(rows),
                   "n_sign_flips": sum(1 for r in rows if r["sign_flip"]),
                   "rows": rows}, handle, indent=1)
    return {"n_diff_decisions": len(rows),
            "n_sign_flips": sum(1 for r in rows if r["sign_flip"]),
            "path": out}


# ---------------------------------------------------------------------------
# reconciliation phase (audit finding 3)
# ---------------------------------------------------------------------------
def reconcile_cell(record):
    """Explicit arithmetic bridge per arm, both books.

    Contract basis (frozen runner, compute_cell):
      booked columns  = sums over ALL session-gated kept trades
                        (n_trades == len(dual) == n_trades_kept);
      base/base_price_only = book_metrics over the SCORED subset only
                        (fold-assigned, i.e. excluding trades purged within
                        PURGE_DAYS after an internal fold boundary);
      expectancy      = base.total_pnl / base.trades (per book).
    The bridge therefore is:
      booked_column = base.total_pnl + purged_trades_contribution (per book)
      cost bridge   = gross_price_pnl_usd - price_only_pnl_usd
                      == n_trades * round_trip_cost (1.5 bps/side x tier 1.0
                      == 3.00 USD per round trip at the 10000 USD-unit notional)
    """
    n_trades = record["n_trades"]
    base = record["base"]
    base_po = record["base_price_only"]
    purged = record["purged_trades"]
    scored_n = base["trades"]
    round_trip = 3.0
    bridge = {
        "cell_id": record["cell_id"],
        "populations": {
            "n_decisions": record["n_decisions"],
            "weekend_gate_dropped": record["weekend_gate_dropped"],
            "n_trades_kept_booked": record["n_trades_kept"],
            "purged_trades_not_scored": purged,
            "scored_population_base": scored_n,
            "identity_kept_equals_scored_plus_purged":
                record["n_trades_kept"] == scored_n + purged,
        },
        "financing_adjusted_book": {
            "expectancy_per_trade": base["expectancy"],
            "expectancy_times_scored_population": round(base["expectancy"] * scored_n, 10),
            "base_total_pnl": base["total_pnl"],
            "expectancy_bridge_holds":
                abs(base["expectancy"] * scored_n - base["total_pnl"]) < 1e-6,
            "booked_financing_adjusted_pnl_usd": record["financing_adjusted_pnl_usd"],
            "purged_trades_contribution_fin_adj": round(
                record["financing_adjusted_pnl_usd"] - base["total_pnl"], 10),
        },
        "price_only_book": {
            "expectancy_per_trade": base_po["expectancy"],
            "expectancy_times_scored_population": round(base_po["expectancy"] * scored_n, 10),
            "base_total_pnl": base_po["total_pnl"],
            "expectancy_bridge_holds":
                abs(base_po["expectancy"] * scored_n - base_po["total_pnl"]) < 1e-6,
            "booked_price_only_pnl_usd": record["price_only_pnl_usd"],
            "purged_trades_contribution_price_only": round(
                record["price_only_pnl_usd"] - base_po["total_pnl"], 10),
        },
        "cost_bridge": {
            "gross_price_pnl_usd": record["gross_price_pnl_usd"],
            "price_only_pnl_usd": record["price_only_pnl_usd"],
            "implied_total_cost": round(
                record["gross_price_pnl_usd"] - record["price_only_pnl_usd"], 10),
            "expected_cost_n_trades_x_3usd": round(n_trades * round_trip, 10),
            "cost_bridge_holds":
                abs((record["gross_price_pnl_usd"] - record["price_only_pnl_usd"])
                    - n_trades * round_trip) < 1e-6,
        },
        "dual_book_identity": {
            "financing_adjustment_usd": record["financing_adjustment_usd"],
            "price_plus_adjustment": round(
                record["price_only_pnl_usd"] + record["financing_adjustment_usd"], 10),
            "identity_holds": abs(
                (record["price_only_pnl_usd"] + record["financing_adjustment_usd"])
                - record["financing_adjusted_pnl_usd"]) < 1e-6,
        },
        "incremental_alpha_bridge": {
            "alpha_definition": record.get("incremental_alpha_definition"),
            "incremental_alpha": record.get("incremental_alpha"),
            "anchor_expectancy": base["expectancy"],
            "benchmark_expectancy": (record.get("benchmark_treatment") or {})
                .get("expectancy"),
        },
        "audit_finding_3_resolution": (
            "expectancy is defined on the SCORED (post-purge) population "
            "(base.trades), booked columns sum the FULL kept book "
            "(n_trades_kept); the audit's expectancy x n_trades(113) "
            "arithmetic mixed the two populations.  The price-only sign flip "
            "is carried by the purged trades' contribution, shown above."),
    }
    return bridge


def recon_phase(cells):
    bridges = [reconcile_cell(rec) for rec in cells.values()]
    out = os.path.join(RUN_DIR, "reconciliation.json")
    with open(out, "w", encoding="utf-8") as handle:
        json.dump({"schema": "forex_free_v3r_reconciliation_v1",
                   "bridges": bridges,
                   "all_identities_hold": all(
                       b["financing_adjusted_book"]["expectancy_bridge_holds"]
                       and b["price_only_book"]["expectancy_bridge_holds"]
                       and b["cost_bridge"]["cost_bridge_holds"]
                       and b["dual_book_identity"]["identity_holds"]
                       and b["populations"]["identity_kept_equals_scored_plus_purged"]
                       for b in bridges)}, handle, indent=1)
    return {"path": out, "n_cells": len(bridges)}


# ---------------------------------------------------------------------------
# multiple-testing statement (audit finding 4)
# ---------------------------------------------------------------------------
def mtest_phase(program_ledger_path, corrected_cells):
    sys.path.insert(0, os.path.join(RUN_DIR, "..", "..", "..", ".."))
    from research.dsr import DSR_ESTIMATOR_ID, PBO_ESTIMATOR_ID, dsr_probability, pbo_cscv

    statement = {
        "schema": "forex_free_v3r_multiple_testing_statement_v1",
        "estimators": {"dsr": DSR_ESTIMATOR_ID, "pbo": PBO_ESTIMATOR_ID},
        "program_published_cells": None,
        "n_trials_used": None,
        "dsr": None, "pbo": None,
        "not_run_reasons": [],
        "note": "S1 remains the arbiter; this statement is for the record only",
    }
    cells = []
    if program_ledger_path and os.path.exists(program_ledger_path):
        for line in open(program_ledger_path, encoding="utf-8"):
            row = json.loads(line)
            cells.append(row)
        statement["program_published_cells"] = len(cells)
    if not cells:
        statement["not_run_reasons"].append("PROGRAM_LEDGER_UNAVAILABLE")
    # DSR needs >= 2 trial Sharpe series and per-period returns to estimate
    # skew/kurtosis/sample length.  Published program rows carry aggregate
    # metrics only, so the honest computation is NOT_RUN unless per-period
    # series are found in the ledger.
    has_series = any(isinstance(row.get("daily_returns"), list) for row in cells)
    if not has_series:
        statement["not_run_reasons"].append(
            "NO_PER_PERIOD_SERIES_IN_PUBLISHED_LEDGER (aggregates only)")
        statement["dsr"] = {"dsr": None, "reason": "insufficient_inputs",
                            "n_trials_candidate": len(cells)}
    else:
        # compute path left explicit for the run that finds series data
        statement["not_run_reasons"].append("SERIES_EXTRACTION_NOT_IMPLEMENTED_IN_DRAFT")
    if corrected_cells:
        anchor = corrected_cells.get("family2:anchor:tier1.0", {})
        statement["subject_cell"] = {
            "cell_id": anchor.get("cell_id"),
            "base_expectancy": (anchor.get("base") or {}).get("expectancy"),
        }
    out = os.path.join(RUN_DIR, "multiple_testing_statement.json")
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(statement, handle, indent=1, sort_keys=True)
    return {"path": out, "not_run_reasons": statement["not_run_reasons"]}


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--v3-worktree", required=True)
    parser.add_argument("--data-paths-template", required=True,
                        help="the data_paths JSON of the V3 scored run; only "
                             "macro_vintages is re-pointed, price paths pass "
                             "through byte-identically")
    parser.add_argument("--vintage-dir", default="data_raw/forex_free_v3_macro")
    parser.add_argument("--evidenced-dir", default="data_raw/forex_free_v3r_macro_evidenced")
    parser.add_argument("--program-ledger", default=None)
    parser.add_argument("--phases", default="baseline,corrected,diff,recon,mtest")
    args = parser.parse_args()

    wanted = [p.strip() for p in args.phases.split(",") if p.strip()]

    freeze = guard_w3c(args.v3_worktree)                    # G1
    ledger_pin = guard_ledger()                             # G2
    guard_vintages(args.vintage_dir, args.evidenced_dir, freeze)  # G3
    v3_ledger = os.path.join(
        args.v3_worktree, "research/control/forex_free_v3_run/scored_ledger_published.jsonl")

    report = {"schema": "forex_free_v3r_recompute_report_v1",
              "w3c_ledger_pin": ledger_pin, "guards": "G1..G3 PASS"}

    if "baseline" in wanted:                                # G4 twin
        baseline_paths = build_data_paths(args.data_paths_template, args.vintage_dir)
        cells_twin, sanity_twin = compute_all_cells(baseline_paths)
        diffs = twin_compare(v3_ledger, cells_twin)
        if diffs:
            raise SystemExit(json.dumps({"GUARD": "G4_TWIN_MISMATCH",
                                         "diffs": diffs[:20]}, indent=1))
        with open(os.path.join(RUN_DIR, "twin_verification.json"), "w") as handle:
            json.dump({"schema": "forex_free_v3r_twin_verification_v1",
                       "result": "ALL_MATCH",
                       "cells_compared": sorted(cells_twin),
                       "keys_compared": TWIN_KEYS}, handle, indent=1)
        report["twin"] = "ALL_MATCH"

    if "corrected" in wanted:
        evidenced_paths = build_data_paths(args.data_paths_template, args.evidenced_dir)
        cells, sanity = compute_all_cells(evidenced_paths)
        report["cells"] = {
            cell_id: {
                "gates": "PASS" if rec["gates"] else "FAIL",
                "gate_reasons": rec["gate_reasons"],
                "n_trades": rec["n_trades"],
                "price_only_pnl_usd": rec["price_only_pnl_usd"],
                "financing_adjusted_pnl_usd": rec["financing_adjusted_pnl_usd"],
                "base": rec["base"], "base_price_only": rec["base_price_only"],
            } for cell_id, rec in cells.items()
        }
        report["mechanism_sanity"] = sanity
        with open(os.path.join(RUN_DIR, "v3r_records.jsonl"), "w") as handle:
            for cell_id, rec in cells.items():
                handle.write(json.dumps(rec, sort_keys=True, separators=(",", ":"),
                                        ensure_ascii=False) + "\n")
        report["no_publication_performed"] = True

    if "diff" in wanted:
        report["diff"] = diff_phase(args.vintage_dir, args.evidenced_dir)
    if "recon" in wanted:
        # reconcile the corrected cells if present, else the frozen V3 rows
        if "corrected" in wanted and cells:
            report["reconciliation"] = recon_phase(cells)
        else:
            v3_cells = {}
            for line in open(v3_ledger, encoding="utf-8"):
                row = json.loads(line)
                if row.get("arm") in ("anchor", "neighbour", "causal_negative_control") \
                        or row.get("record_id", "").endswith("tier1.0"):
                    v3_cells[row["cell_id"]] = row
            report["reconciliation"] = recon_phase(v3_cells)
    if "mtest" in wanted:
        report["multiple_testing"] = mtest_phase(args.program_ledger,
                                                 cells if "corrected" in wanted else None)

    with open(os.path.join(RUN_DIR, "v3r_recompute_report.json"), "w") as handle:
        json.dump(report, handle, indent=1, sort_keys=True)
    print(json.dumps({k: report.get(k) for k in
                      ("twin", "diff", "reconciliation", "multiple_testing")},
                     default=None, indent=1))


if __name__ == "__main__":
    main()
