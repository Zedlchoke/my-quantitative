"""ATTRIBUTION lane driver — ERP1-TRACKA-COHORT-1 / failres-attrib (Phase A).

One pass, frozen laws only, no tuning, no variants. DIAGNOSTIC on
OUTCOME-EXPOSED surfaces (never promotable evidence).

Sequence:
  1. heavy-lock inspect (must be FREE_PROVEN, else NOT_RUN_RESOURCE_CONFLICT)
  2. rebuild the diag 5 books on both pairs (byte-copied ANC planes,
     committed engine/laws, warmup_end_idx=0) at k=1.0 and k=0.0
     (+ R-DAEMON k=1.5/2.0 for the k-decay table)
  3. RECONCILIATION GUARD: per-fold/total nets vs DIAG_DAEMON_REPORT
     §3.1/§3.2 (tolerance 0.05 pips). Any disagreement -> write BLOCKED
     report, write nothing else, exit 1.
  4. emit trade tables / aggregates / daily join tables / provenance.

Outputs (failres namespace only, this worktree):
  failres_attrib_trades_{EURUSD,GBPUSD}.json
  failres_attrib_agg_{EURUSD,GBPUSD}.json
  failres_daily_{EURUSD,GBPUSD}.json
  failres_attrib_PROVENANCE.json
"""
from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

import failres_attrib_lib as L

OUT = L.FAILRES
ROOT_REPO = Path("/Users/hoangminhlong/my-quantitative")
# parents: [research/control, research, <worktree root: failres-attrib>]
WORKTREE = L.COHORT.parents[2]
assert (WORKTREE / ".git").exists(), f"not a worktree root: {WORKTREE}"
assert WORKTREE.name == "failres-attrib", f"unexpected worktree: {WORKTREE}"
RESEARCHCTL = ROOT_REPO / "research" / "researchctl.py"
VENV_PY = ROOT_REPO / ".venv" / "bin" / "python"

# ------------------------- reconciliation targets (DIAG_DAEMON_REPORT) -------
EURUSD_RDAEMON_FOLDS = {"F1": -188.8, "F2": -884.4, "F3": 1049.8,
                        "F4": 348.3, "F5": -191.5, "F6": 257.0}
EURUSD_TOTALS_K1 = {"R-DAEMON": (812.2, 1062), "R-ORIG": (7322.7, None),
                    "R-ANCHOR": (1052.7, None), "SHORT_ALWAYS": (704.6, None),
                    "LONG_ALWAYS": (-1665.5, None)}
GBPUSD_RDAEMON_TOTAL = -1708.9
GBPUSD_RDAEMON_F3 = -1272.7
TOL = 0.05
EXPECTED_EURUSD_H1_SHA = ("2e175b06209dfc6f942a4e614ee0c574d86be3d8077c9835"
                          "102b8ad7612e4f9d")


def lock_inspect() -> dict:
    r = subprocess.run(
        [str(VENV_PY), str(RESEARCHCTL), "locks", "inspect"],
        capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def git(*args) -> str:
    return subprocess.run(["git", "-C", str(WORKTREE), *args],
                          capture_output=True, text=True, check=True).stdout.strip()


def check_recon(pair: str, recon: dict) -> list:
    """Returns a list of mismatch strings (empty == PASS)."""
    bad = []
    arms = recon["arms"]
    if pair == "EURUSD":
        for f, v in EURUSD_RDAEMON_FOLDS.items():
            got = arms["R-DAEMON"]["per_fold_net"][f]
            if abs(got - v) > TOL:
                bad.append(f"EURUSD R-DAEMON {f}: got {got}, diag {v}")
        for arm, (net, rt) in EURUSD_TOTALS_K1.items():
            got = arms[arm]["net_full_panel"]
            if abs(got - net) > TOL:
                bad.append(f"EURUSD {arm} total: got {got}, diag {net}")
            if rt is not None and arms[arm]["rt_full_panel"] != rt:
                bad.append(f"EURUSD {arm} RT: got "
                           f"{arms[arm]['rt_full_panel']}, diag {rt}")
    else:
        got = arms["R-DAEMON"]["net_full_panel"]
        if abs(got - GBPUSD_RDAEMON_TOTAL) > TOL:
            bad.append(f"GBPUSD R-DAEMON total: got {got}, diag "
                       f"{GBPUSD_RDAEMON_TOTAL}")
        got3 = arms["R-DAEMON"]["per_fold_net"]["F3"]
        if abs(got3 - GBPUSD_RDAEMON_F3) > TOL:
            bad.append(f"GBPUSD R-DAEMON F3: got {got3}, diag "
                       f"{GBPUSD_RDAEMON_F3}")
    return bad


def main() -> int:
    t0 = dt.datetime.now(dt.timezone.utc)
    lock_before = lock_inspect()
    if lock_before.get("verdict") != "FREE_PROVEN":
        print(json.dumps({"status": "NOT_RUN_RESOURCE_CONFLICT",
                          "lock": lock_before}))
        return 2

    results = {}
    for pair in L.PAIRS:
        p = L.load_plane(pair)
        trades_by_book, (first_mode, changes, bar_label), checks = \
            L.build_books(p)
        recon = L.recon_block(pair, trades_by_book, checks)
        bad = check_recon(pair, recon)
        if bad:
            blocked = {
                "status": "BLOCKED_RECONCILIATION_MISMATCH",
                "pair": pair,
                "mismatches": bad,
                "recon": recon,
                "note": "Reconciliation guard tripped (>0.05 pips vs "
                        "DIAG_DAEMON_REPORT §3.1/§3.2). Per dispatch: commit "
                        "nothing, write the BLOCKED report, stop.",
                "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
            }
            (OUT / "ATTRIB_failres_BLOCKED.json").write_text(
                json.dumps(blocked, indent=1, default=str) + "\n")
            print(json.dumps({"status": "BLOCKED", "pair": pair,
                              "mismatches": bad}, indent=1))
            return 1
        ctx = L.day_context(p, bar_label, first_mode, changes)
        exposure = L.signed_exposure_by_day(p, _daemon_tgt(p))
        rows = L.trade_table(p, pair, trades_by_book, bar_label, ctx)
        daemon_rows = [r for r in rows if r["book"] == "R-DAEMON"]
        agg = L.aggregate_pair(pair, p, trades_by_book, daemon_rows, rows,
                               ctx, recon)
        daily = L.daily_join_table(pair, trades_by_book, ctx, exposure)
        if pair == "EURUSD":
            agg["f2_deep_dive"] = L.f2_deep_dive(trades_by_book, rows, ctx)
        results[pair] = {"rows": rows, "agg": agg, "daily": daily}
        print(f"[{pair}] recon PASS; trades={len(rows)} "
              f"(daemon={len(daemon_rows)}); days={len(daily['rows'])}")

    lock_after = lock_inspect()

    for pair in L.PAIRS:
        r = results[pair]
        L.write_json(OUT / f"failres_attrib_trades_{pair}.json", {
            "schema": "failres_attrib_trades@1", "pair": pair,
            "labels": L.LABELS,
            "note": "k=1.0 books, committed engine law; gross = SAME book "
                    "at k=0.0 (zero-cost fills); cost = net(k1) - net(k0) "
                    "per trade (cost decomposition, NOT a variant); "
                    "mode_at_entry = instrumented daemon mode at the "
                    "entry's signal bar (labeled_daemon asserted identical "
                    "to the authoritative walk); exit_type: FORCE_FLAT "
                    "(day-close bar) > REVERSAL (next trade enters at this "
                    "exit ts) > TARGET_EXIT; R-ORIG rows carry "
                    "R-ORIG-SEMANTICS (leaky law, placement reference).",
            "n_rows": len(r["rows"]), "rows": r["rows"]})
        L.write_json(OUT / f"failres_attrib_agg_{pair}.json", r["agg"])
        L.write_json(OUT / f"failres_daily_{pair}.json", r["daily"])

    parquets = {f.name: L.sha256_file(f)
                for f in sorted(L.DERIVED.glob("*.parquet"))}
    cohort_scripts = L.COHORT / "scripts"
    diag_scripts = L.COHORT / "diag" / "scripts"
    code_sha = {
        "scripts/engine.py": L.sha256_file(cohort_scripts / "engine.py"),
        "scripts/tracka_lib.py": L.sha256_file(cohort_scripts / "tracka_lib.py"),
        "scripts/scored_lib.py": L.sha256_file(cohort_scripts / "scored_lib.py"),
        "scripts/falsifier_run.py": L.sha256_file(cohort_scripts / "falsifier_run.py"),
        "diag/scripts/diag_lib.py": L.sha256_file(diag_scripts / "diag_lib.py"),
        "diag/scripts/pair_config_diag.py":
            L.sha256_file(diag_scripts / "pair_config_diag.py"),
        "failres/scripts/failres_attrib_lib.py":
            L.sha256_file(Path(__file__).parent / "failres_attrib_lib.py"),
        "failres/scripts/failres_attrib_run.py": L.sha256_file(Path(__file__)),
    }
    t1 = dt.datetime.now(dt.timezone.utc)
    prov = {
        "schema": "failres_attrib_provenance@1",
        "cycle_id": "ERP1-TRACKA-COHORT-1",
        "lane": "failres-attrib",
        "labels": L.LABELS,
        "verdict_class": "DIAGNOSTIC_OUTCOME_EXPOSED (never promotable "
                         "evidence, regardless of result)",
        "base_sha": "05168bfebc0dc53f8cc2e6b2a7f0cb79bc80b0a9",
        "dispatch_sha": "05168bfebc0dc53f8cc2e6b2a7f0cb79bc80b0a9",
        "worktree": str(WORKTREE),
        "branch": "orca/erp1-ta1-failres-attrib",
        "head_at_write": git("rev-parse", "HEAD"),
        "python": sys.version.split()[0],
        "run_started_utc": t0.isoformat(),
        "run_finished_utc": t1.isoformat(),
        "fold_table_used": [list(f) for f in L.FOLD_TABLE],
        "fold_authority": "scripts/falsifier_run.py FOLD_TABLE (imported, "
                          "never redefined)",
        "panel_window": [L.PANEL_START, L.PANEL_END],
        "plane_loader": "diag_lib.load_plane convention; bars1h_ANC_{pair}"
                        ".parquet from failres/data_local/derived (byte "
                        "copies of the diag lane's derived dir); ts <= "
                        "2026-06-30T23:59:59Z; SignalPlane pip_mult=1/pip",
        "parquet_sha256": parquets,
        "expected_EURUSD_H1_sha256": EXPECTED_EURUSD_H1_SHA,
        "eurusd_h1_sha_match":
            parquets.get("bars1h_ANC_EURUSD.parquet") == EXPECTED_EURUSD_H1_SHA,
        "code_sha256": code_sha,
        "lock_verdict_before_compute": {
            "verdict": lock_before["verdict"],
            "reason": lock_before.get("reason"),
            "flock_state": lock_before.get("evidence", {}).get("flock_state"),
        },
        "lock_verdict_after_compute": {
            "verdict": lock_after["verdict"],
            "reason": lock_after.get("reason"),
            "flock_state": lock_after.get("evidence", {}).get("flock_state"),
        },
        "reconciliation": {pair: {
            "status": "PASS",
            "targets": "DIAG_DAEMON_REPORT §3.1/§3.2",
            "tolerance_pips": TOL,
            "reproduced": results[pair]["agg"]["reconciliation"],
        } for pair in L.PAIRS},
        "pinned_choices": {
            "warmup_end_idx": 0,
            "k_books": "k=1.0 primary; k=0.0 SAME-book cost decomposition; "
                       "k=1.5/2.0 only for the R-DAEMON k-decay table",
            "tercile_cuts": "computed on the FULL panel, applied per fold "
                            "(descriptive, one pass)",
        },
        "known_limitations": [
            "FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK: fill quality is not "
            "measurable on M1 bid/ask bars — paper-tier costs only",
            "SINGLE_SOURCE_PANEL: one M1 corpus per pair (Dukascopy census)",
            "DIAGNOSTIC_OUTCOME_EXPOSED: folds are the family's dev "
            "surfaces; nothing here is promotable evidence",
            "correlation with any per-fold/per-hour/per-mode factor is NOT "
            "causation; no event data was used or overlaid in this lane",
            "mode_at_entry uses an instrumented (asserted-identical) copy "
            "of the daemon walk for bar-level labels",
        ],
    }
    L.write_json(OUT / "failres_attrib_PROVENANCE.json", prov)

    # console summary for the report
    for pair in L.PAIRS:
        agg = results[pair]["agg"]
        print(f"\n===== {pair} recon =====")
        for arm, a in agg["reconciliation"]["arms"].items():
            print(f"  {arm:13s} total {a['net_full_panel']:>9.1f} "
                  f"rt {a['rt_full_panel']:>5d} folds "
                  f"{[a['per_fold_net'][f] for f in L.FOLD_IDS]}")
    print("\nprovenance -> failres_attrib_PROVENANCE.json")
    return 0


def _daemon_tgt(p):
    tgt, _, _ = __import__("tracka_lib").f_rangeexp_daemon(p)
    return tgt


if __name__ == "__main__":
    sys.exit(main())
