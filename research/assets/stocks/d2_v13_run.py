"""STOCKS-FREE-V13 D2 execution runner (THIN - the machine does the math).

Runs the SIX registered proposal anchors (registered into
machine.PROPOSAL_EXPOSURE_BUILDERS by importing
research.assets.stocks.d2_v13_proposal_handlers - import side-effect) plus
their declared CONTROL exposures through the D2 machine's novelty_block
(pooled midrank Spearman vs all FIFTEEN veto entries, bar |rho| <= 0.20,
fail-closed on nulls) and identifiability_anchor_vs_control (pooled +
per-date anchor-vs-control rho with each proposal's declared gates and the
universally binding self-subsumption kill at |rho| > 0.98), and emits

    research/control/stocks_free_v13_run/audits/d2_v13_novelty_feasibility.json

with per-proposal veto_rho / margins / identifiability / feasibility blocks.

MACHINERY:
  - acquires the MACHINE-WIDE heavy lock via governance.heavy_lock.acquire
    (cycle STOCKS-FREE-V13, role D2_MEASURE); LockBusy -> exit code 3
    NOT_RUN_RESOURCE_CONFLICT, single attempt, no spin;
  - determinism x2: the WHOLE measurement runs twice; the two result
    payloads are byte-compared (and sha256-recorded); a mismatch is a
    FAILED reproduction;
  - release records FINISHED, or FAILED with the stderr tail (V16 lesson).

DISCIPLINE: feature/rank arithmetic only - zero PnL, zero returns, zero
selection, zero scoring. Proposal kills (BLOCKED_*) are recorded verdicts,
not runner failures; the runner fails only on machinery errors.

Usage (from the worktree ROOT):
  /Users/hoangminhlong/my-quantitative/.venv/bin/python -m research.assets.stocks.d2_v13_run <built_at_utc>

Exit codes: 0 written; 1 failed (FAILED release); 2 blocked (input pins /
context load refused); 3 NOT_RUN_RESOURCE_CONFLICT (lock busy); 4
CONTROL_STATE_DRIFT; 64 usage.
"""

from __future__ import annotations

import hashlib
import json
import sys
import traceback

from research.assets.stocks import d2_v13_novelty_measure as machine
from research.assets.stocks import d2_v13_proposal_handlers as handlers
from research.governance import heavy_lock

CYCLE = "STOCKS-FREE-V13"
ROLE = "D2_MEASURE"
AUDIT_PATH = machine.V13_OUT / "d2_v13_novelty_feasibility.json"

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_BLOCKED = 2
EXIT_LOCK_BUSY = 3
EXIT_DRIFT = 4
EXIT_USAGE = 64

# Declared feasibility floors measurable at D2 (counts only - no PnL).
# Binding adjudication stays with P2/scoring per each proposal's text; D2
# reports the measured population fail-closed.
FOLD_POPULATED_PERIODS_FLOOR = 5          # A5 C8 / A6 overall floors
A6_COHORT_SCOREABLE_FLOOR = 30            # A6 per scored date
A6_LEG_FLOOR = 5                          # A6 per leg per scored date


def to_machine_keys(exposure):
    """{(cik, iso_date_str): float} -> {(cik, datetime.date): float} (the
    machine's veto builders take date objects)."""
    return {(e, machine.dd(t)): v for (e, t), v in exposure.items()}


def feasibility_block(C, anchor, pid):
    """Measured, non-scoring feasibility facts on the defined exposure
    population: pairs/entities/dates, per-fold population, and (where the
    proposal declares them) the floor comparisons."""
    dates = sorted({t for _e, t in anchor})
    per_fold = {}
    for t in dates:
        fold = machine.fold_of(C, t)
        fid = fold["fold_id"] if fold else "UNFOLDED"
        rec = per_fold.setdefault(fid, {"defined_pairs": 0, "defined_dates": 0,
                                        "dates": []})
        rec["defined_pairs"] += sum(1 for (e, tt) in anchor if tt == t)
        rec["defined_dates"] += 1
        rec["dates"].append(t.isoformat())
    for fid in per_fold:
        per_fold[fid]["populated_dates"] = per_fold[fid]["defined_dates"]
    block = {
        "anchor_pairs_defined": len(anchor),
        "anchor_entities_defined": len({e for e, _t in anchor}),
        "anchor_dates_defined": len(dates),
        "per_fold": {fid: {"defined_pairs": rec["defined_pairs"],
                           "defined_dates": rec["defined_dates"]}
                     for fid, rec in sorted(per_fold.items())},
    }
    if pid in ("SFV13-A5-P1", "SFV13-A5-P2", "SFV13-A6-P1", "SFV13-A5-P2",
               "SFV13-A6-P2"):
        block["declared_fold_populated_periods_floor"] = \
            FOLD_POPULATED_PERIODS_FLOOR
        block["fold_populated_periods_pass"] = bool(
            per_fold and all(rec["defined_dates"] >= FOLD_POPULATED_PERIODS_FLOOR
                             for rec in per_fold.values()))
    if pid in ("SFV13-A6-P1", "SFV13-A6-P2"):
        per_date_counts = {}
        leg_counts = {}
        for t in dates:
            vals = [v for (_e, tt), v in anchor.items() if tt == t]
            per_date_counts[t.isoformat()] = len(vals)
            leg_counts[t.isoformat()] = {
                "long_states": sum(1 for v in vals if v > 0),
                "short_states": sum(1 for v in vals if v < 0)}
        block["declared_cohort_scoreable_floor_per_date"] = \
            A6_COHORT_SCOREABLE_FLOOR
        block["declared_leg_floor_per_leg_per_date"] = A6_LEG_FLOOR
        block["min_pairs_per_scored_date"] = min(per_date_counts.values())
        block["dates_meeting_cohort_scoreable_floor"] = sum(
            1 for n in per_date_counts.values()
            if n >= A6_COHORT_SCOREABLE_FLOOR)
        block["per_date_pairs"] = per_date_counts
        block["per_date_leg_states"] = leg_counts
        block["floors_note"] = ("measured at D2, informational; the declared "
                                "kill points for these floors are P2 "
                                "coverage-first and the scored-book floors, "
                                "not the D2 novelty measurement")
    if pid == "SFV13-A4-P2":
        f1 = per_fold.get("S0_FOLD_1", {})
        block["fold1_opportunistic_seeding_note"] = (
            "declared fold-1 thinning risk (24-month identity-history "
            "seeding); measured fold-1 defined pairs: "
            f"{f1.get('defined_pairs', 0)}")
    if pid in ("SFV13-A4-P1", "SFV13-A4-P2"):
        block["fold_population_note"] = (
            "no per-fold decision-period floor declared at D2 for this "
            "proposal (its per-fold funding floor is the P2 coverage-first "
            "kill)")
    return block


def measure_once(C):
    """One full measurement pass. Returns (payload_str, results_dict).
    Deterministic: sorted iteration only; every builder is a pure function
    of the context's cached staged bytes."""
    results = {}
    for pid in sorted(machine.PROPOSAL_EXPOSURE_BUILDERS):
        entry = {"proposal_id": pid}
        anchor_raw = machine.PROPOSAL_EXPOSURE_BUILDERS[pid](C)
        if not isinstance(anchor_raw, dict) or not anchor_raw:
            entry["verdict"] = "BLOCKED_EXPOSURE_UNDEFINED"
            entry["anchor_pairs"] = 0
            results[pid] = entry
            continue
        anchor = to_machine_keys(anchor_raw)
        nov = machine.novelty_block(C, anchor)
        entry["anchor_pairs"] = len(anchor)
        entry["anchor_entities"] = len({e for e, _t in anchor})
        entry["anchor_dates"] = len({t for _e, t in anchor})
        entry["novelty"] = nov
        entry["verdict_novelty"] = ("ELIGIBLE" if nov["novelty_pass_le_020"]
                                    else "BLOCKED_NOVELTY")
        idents = {}
        for cn in sorted(handlers.PROPOSAL_CONTROL_BUILDERS.get(pid, {})):
            spec = handlers.PROPOSAL_CONTROL_BUILDERS[pid][cn]
            ctrl_raw = spec["builder"](C)
            if not isinstance(ctrl_raw, dict) or not ctrl_raw:
                idents[cn] = {"verdict": "BLOCKED_CONTROL_DESIGN_FAILURE",
                              "control_pairs": 0}
                continue
            ctrl = to_machine_keys(ctrl_raw)
            gate = (spec["ctrl_gate"] if spec["ctrl_gate"] is not None
                    else machine.SELF_SUBSUMPTION_RHO)
            idt = machine.identifiability_anchor_vs_control(
                C, anchor, ctrl, gate,
                per_date_gate=spec.get("per_date_gate"),
                date_pass_share=spec.get("date_pass_share"))
            idt["declared_ctrl_gate"] = spec["ctrl_gate"]
            idt["applied_pooled_gate"] = gate
            idt["gate_basis"] = spec["gate_basis"]
            idt["control_pairs_defined"] = len(ctrl)
            idt["control_entities"] = len({e for e, _t in ctrl})
            idents[cn] = idt
        entry["identifiability"] = idents
        entry["feasibility"] = feasibility_block(C, anchor, pid)
        results[pid] = entry
    payload = json.dumps({"results": results}, indent=1, sort_keys=True)
    return payload, results


def harvest_diagnostics(C):
    """Cumulative handler diag counters (cumulative across both determinism
    passes - counter semantics, not per-pass)."""
    cache = getattr(C, "_d2p_cache", {})
    return {k: v for k, v in sorted(cache.items()) if k.startswith("diag:")}


def run(built_at_utc):
    print("[d2-run] acquiring machine-wide heavy lock...", flush=True)
    try:
        handle = heavy_lock.acquire(
            cycle_id=CYCLE, role=ROLE, worktree=str(machine.REPO_ROOT),
            command=[sys.executable, __file__, built_at_utc],
            expected_artifacts=[str(AUDIT_PATH)])
    except heavy_lock.LockBusyError as exc:
        sys.stderr.write(f"NOT_RUN_RESOURCE_CONFLICT: {exc}\n")
        return EXIT_LOCK_BUSY
    except heavy_lock.HeavyLockError as exc:
        sys.stderr.write(f"CONTROL_STATE_DRIFT: {exc}\n")
        return EXIT_DRIFT

    try:
        C, rc = machine.load_context()
        if rc != 0:
            handle.release(status="FAILED",
                           note="input pins / context load refused "
                                "(fail-closed; see stderr)")
            return EXIT_BLOCKED
        machine._bench_series(C)

        payload1, results = measure_once(C)
        payload2, _results2 = measure_once(C)
        identical = payload1 == payload2
        determinism = {
            "passes": 2,
            "byte_identical": identical,
            "sha256_pass_1": hashlib.sha256(payload1.encode()).hexdigest(),
            "sha256_pass_2": hashlib.sha256(payload2.encode()).hexdigest(),
            "scope": "whole measurement (all six anchors + all controls + "
                     "novelty + identifiability + feasibility), recomputed "
                     "from the context's staged bytes",
        }
        if not identical:
            sys.stderr.write("REPRODUCTION FAILURE: determinism x2 payloads "
                             "differ - audit NOT written\n")
            handle.release(status="FAILED",
                           note="determinism x2 byte-compare FAILED")
            return EXIT_FAILED

        audit = {
            "schema": "stocks_free_v13_run/d2_proposal_feasibility@1",
            "built_at_utc": built_at_utc,
            "cycle": machine.CYCLE,
            "base_sha": machine.BASE_SHA,
            "worktree": str(machine.REPO_ROOT),
            "producer_role": "D2 execution runner over the six registered "
                             "proposal handlers + declared control handlers "
                             "(machine-wide heavy lock held, role "
                             "D2_MEASURE)",
            "discipline": "feature/rank arithmetic only; zero PnL, zero "
                          "returns, zero selection, zero scoring; a killed "
                          "proposal is a successful preregistered outcome",
            "input_integrity": {
                "pin_verdicts": C.pin_verdicts,
                "rev_dir_encoding_check": C.dir_check,
                "priced_counts": C.priced_counts,
                "folds": C.folds,
            },
            "veto_set": {"count": len(machine.VETO_NAMES),
                         "names": machine.VETO_NAMES},
            "novelty_bar": machine.NOVELTY_BAR,
            "self_subsumption_rho": machine.SELF_SUBSUMPTION_RHO,
            "registered_proposal_builders":
                sorted(machine.PROPOSAL_EXPOSURE_BUILDERS),
            "registered_control_builders": {
                pid: sorted(handlers.PROPOSAL_CONTROL_BUILDERS.get(pid, {}))
                for pid in sorted(machine.PROPOSAL_EXPOSURE_BUILDERS)},
            "results": results,
            "handler_diag_counters": harvest_diagnostics(C),
            "determinism": determinism,
            "verdict_rule": (
                "novelty: BLOCKED_NOVELTY if pooled |rho| > 0.20 vs ANY of "
                "the FIFTEEN veto entries (fail-closed on unmeasured "
                "vetoes); identifiability: measured per control with the "
                "proposal's declared pooled/per-date gates where declared "
                "(A4 sham: 0.30 / 0.30 @ >= 90% of dates), else only the "
                "universally declared self-subsumption bound 0.98 (pooled "
                "rho >= 0.98 kills PRE-SCORE); the operative control kill "
                "for controls without a declared rho gate remains the "
                "book-level same-sign >= 0.5x expectancy rule evaluated at "
                "scoring; selection and scoring remain A7+ decisions"),
            "no_pnl_no_outcomes": True,
        }
        payload = json.dumps(audit, indent=1, sort_keys=True)
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(AUDIT_PATH, "w") as fh:
            fh.write(payload)
        print(f"[d2-run] wrote {AUDIT_PATH} ({len(payload)} bytes)",
              flush=True)
        handle.release(status="FINISHED",
                       note=f"d2 novelty+feasibility written: {AUDIT_PATH} "
                            f"({len(payload)} bytes); determinism x2 "
                            f"byte_identical={identical}")
        return EXIT_OK
    except Exception:
        err = traceback.format_exc()
        sys.stderr.write(err)
        try:
            handle.release(status="FAILED",
                           note="stderr tail: " +
                                err.strip().splitlines()[-1][:300])
        except Exception:
            pass
        return EXIT_FAILED


def main(argv):
    if len(argv) < 2:
        sys.stderr.write(
            "usage: d2_v13_run.py <built_at_utc>\n"
            "(registers the six proposal handlers via import, runs the full "
            "measurement twice under the machine-wide heavy lock, "
            "byte-compares, writes the audit)\n")
        return EXIT_USAGE
    return run(argv[1])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
