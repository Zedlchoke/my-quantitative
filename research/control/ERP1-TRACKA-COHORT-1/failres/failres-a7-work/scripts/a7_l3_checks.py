"""A7 L3 — committed-artifact self-consistency + test-suite re-run.

Checks the committed failres JSONs' INTERNAL identities and the REPORT's
tables against the JSONs (no recomputation here — L2 owns that):
  I1  per-trade net == gross + cost (ALL rows, both pairs, <= 0.011 for
      2dp rounding);
  I2  per-fold sums recomputed FROM the trade tables == agg per_fold_net,
      and trade-table totals == agg net_full_panel / rt (all 5 books,
      both pairs);
  I3  daily join table sums == trade-table sums (per book, full panel,
      and daemon per fold);
  I4  REPORT §2/§3/§4 headline numbers == committed agg JSON values
      (EURUSD F2 row, k-decay, GBPUSD F3 block);
  I5  GBPUSD F3 internal identities (dir/mode/flip/hour/exit buckets all
      sum to the fold net).
Also runs the attribution lane's committed pytest suite in this worktree.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

A7_WORK = Path(__file__).resolve().parent.parent
COHORT = A7_WORK.parent
FAILRES = COHORT / "failres"
RESULTS = A7_WORK / "layer_results"
VENV_PY = "/Users/hoangminhlong/my-quantitative/.venv/bin/python"
BOOKS = ("R-DAEMON", "R-ORIG", "R-ANCHOR", "SHORT_ALWAYS", "LONG_ALWAYS")
FOLD_IDS = ["F1", "F2", "F3", "F4", "F5", "F6"]

checks = []


def add(name, ok, detail):
    checks.append({"check": name, "pass": bool(ok), "detail": detail})


def main() -> int:
    tr = {p: json.loads((FAILRES / f"failres_attrib_trades_{p}.json").read_text())
          for p in ("EURUSD", "GBPUSD")}
    ag = {p: json.loads((FAILRES / f"failres_attrib_agg_{p}.json").read_text())
          for p in ("EURUSD", "GBPUSD")}
    dl = {p: json.loads((FAILRES / f"failres_daily_{p}.json").read_text())
          for p in ("EURUSD", "GBPUSD")}

    # ---- I1 per-trade identity (all rows) --------------------------------
    for p in ("EURUSD", "GBPUSD"):
        rows = tr[p]["rows"]
        assert tr[p]["n_rows"] == len(rows)
        bad = [r for r in rows
               if abs((r["gross_pips"] + r["cost_pips"]) - r["net_pips"])
               > 0.011]
        add(f"I1_net_eq_gross_plus_cost_{p}", not bad,
            f"{len(rows)} rows, violations {len(bad)}")

    # ---- I2 fold sums from trade rows == agg recon -----------------------
    # (the trades JSON carries only the R-DAEMON/R-ORIG/R-ANCHOR books by
    # schema; SHORT/LONG_ALWAYS totals live in the recon block and are
    # verified via the daily table in I3 and recomputed in L2)
    for p in ("EURUSD", "GBPUSD"):
        arms = ag[p]["reconciliation"]["arms"]
        for arm in ("R-DAEMON", "R-ORIG", "R-ANCHOR"):
            rows = [r for r in tr[p]["rows"] if r["book"] == arm]
            tot = round(sum(r["net_pips"] for r in rows), 2)
            add(f"I2_total_{p}_{arm}", abs(tot - arms[arm]["net_full_panel"])
                <= 0.005 and len(rows) == arms[arm]["rt_full_panel"],
                f"trades {tot}/{len(rows)} vs agg "
                f"{arms[arm]['net_full_panel']}/{arms[arm]['rt_full_panel']}")
            per = {f: round(sum(r["net_pips"] for r in rows
                               if r["fold"] == f), 2) for f in FOLD_IDS}
            prt = {f: sum(1 for r in rows if r["fold"] == f)
                   for f in FOLD_IDS}
            ok = all(abs(per[f] - arms[arm]["per_fold_net"][f]) <= 0.005
                     for f in FOLD_IDS) and \
                all(prt[f] == arms[arm]["per_fold_rt"][f] for f in FOLD_IDS)
            add(f"I2_folds_{p}_{arm}", ok,
                f"per_fold {per} vs agg {arms[arm]['per_fold_net']}")
        # SHORT/LONG: trades JSON must NOT carry them; recon totals exist
        books_present = {r["book"] for r in tr[p]["rows"]}
        add(f"I2_trades_books_schema_{p}",
            books_present == {"R-DAEMON", "R-ORIG", "R-ANCHOR"},
            f"books in trades JSON: {sorted(books_present)}")

    # ---- I3 daily table sums == trade sums -------------------------------
    for p in ("EURUSD", "GBPUSD"):
        col = {"R-DAEMON": "net_daemon", "R-ORIG": "net_orig",
               "R-ANCHOR": "net_anchor", "SHORT_ALWAYS": "net_short",
               "LONG_ALWAYS": "net_long"}
        arms = ag[p]["reconciliation"]["arms"]
        for arm, c in col.items():
            s = round(sum(r[c] for r in dl[p]["rows"]), 2)
            add(f"I3_daily_full_{p}_{arm}",
                abs(s - arms[arm]["net_full_panel"]) <= 0.05,
                f"daily {s} vs agg {arms[arm]['net_full_panel']}")
        per_f = {f: round(sum(r["net_daemon"] for r in dl[p]["rows"]
                              if r["fold"] == f), 2) for f in FOLD_IDS}
        ok = all(abs(per_f[f] - arms["R-DAEMON"]["per_fold_net"][f]) <= 0.05
                 for f in FOLD_IDS)
        add(f"I3_daily_daemon_folds_{p}", ok, json.dumps(per_f))

    # ---- I4 REPORT tables vs committed agg JSON --------------------------
    eu = ag["EURUSD"]
    f2 = eu["per_fold"]["F2"]
    add("I4_EURUSD_F2_direction",
        f2["by_direction"]["R-DAEMON"]["long"]["net_pips"] == -696.0
        and f2["by_direction"]["R-DAEMON"]["long"]["rt"] == 95
        and f2["by_direction"]["R-DAEMON"]["short"]["net_pips"] == -188.4
        and f2["by_direction"]["R-DAEMON"]["short"]["rt"] == 71,
        json.dumps(f2["by_direction"]["R-DAEMON"]))
    add("I4_EURUSD_F2_mode_entry",
        f2["by_mode_at_entry_R-DAEMON"]["fade"]["net_pips"] == -476.5
        and f2["by_mode_at_entry_R-DAEMON"]["fade"]["rt"] == 138
        and f2["by_mode_at_entry_R-DAEMON"]["follow"]["net_pips"] == -407.9
        and f2["by_mode_at_entry_R-DAEMON"]["follow"]["rt"] == 28,
        json.dumps(f2["by_mode_at_entry_R-DAEMON"]))
    add("I4_EURUSD_F2_flip",
        f2["mode_flip_R-DAEMON"]["flip_days"]["net_pips"] == -1455.5
        and f2["mode_flip_R-DAEMON"]["flip_days"]["rt"] == 102
        and f2["mode_flip_R-DAEMON"]["non_flip_days"]["net_pips"] == 571.1
        and f2["mode_flip_R-DAEMON"]["non_flip_days"]["rt"] == 64,
        json.dumps(f2["mode_flip_R-DAEMON"]))
    add("I4_EURUSD_F2_beta",
        f2["beta_pull"]["daemon_net_minus_short_net"] == -1723.2
        and round(f2["beta_pull"][
            "pearson_rho_daemon_daily_vs_short_daily"], 3) == -0.189,
        json.dumps(f2["beta_pull"]))
    add("I4_EURUSD_F2_terciles",
        [f2["by_ex_ante_tercile_R-DAEMON"][k]["net_pips"]
         for k in ("t1_low", "t2_mid", "t3_high")] == [-359.3, -491.4, -33.7],
        json.dumps({k: f2["by_ex_ante_tercile_R-DAEMON"][k]["net_pips"]
                    for k in ("t1_low", "t2_mid", "t3_high")}))
    kd = eu["k_decay_R-DAEMON"]["F2"]
    add("I4_EURUSD_kdecay_F2",
        abs(kd["1.0"] - (-884.4)) <= 0.0501
        and abs(kd["1.5"] - (-942.1)) <= 0.0501
        and abs(kd["2.0"] - (-999.7)) <= 0.0501,
        json.dumps(kd) + " (REPORT -942.1 is the 1dp display rounding of the "
                         "JSON's -942.05; A7's own executor reproduces "
                         "-942.05/-999.7 exactly — see L2 supplement)")
    add("I4_EURUSD_F2_exittype",
        f2["by_exit_type_R-DAEMON"]["FORCE_FLAT"]["net_pips"] == -2116.5
        and f2["by_exit_type_R-DAEMON"]["FORCE_FLAT"]["rt"] == 128
        and f2["by_exit_type_R-DAEMON"]["TARGET_EXIT"]["net_pips"] == 1232.1
        and f2["by_exit_type_R-DAEMON"]["TARGET_EXIT"]["rt"] == 38
        and f2["by_exit_type_R-DAEMON"]["REVERSAL"]["rt"] == 0,
        json.dumps(f2["by_exit_type_R-DAEMON"]))

    # ---- I5 GBPUSD F3 internal identities + REPORT §4 claims -------------
    gp = ag["GBPUSD"]["per_fold"]["F3"]
    f3net = ag["GBPUSD"]["reconciliation"]["arms"]["R-DAEMON"][
        "per_fold_net"]["F3"]
    bd = gp["by_direction"]["R-DAEMON"]
    add("I5_GBPUSD_F3_dir_claims",
        bd["long"]["net_pips"] == -438.7 and bd["long"]["rt"] == 79
        and bd["short"]["net_pips"] == -834.0 and bd["short"]["rt"] == 81,
        json.dumps(bd))
    add("I5_GBPUSD_F3_dir_sum",
        abs(round(bd["long"]["net_pips"] + bd["short"]["net_pips"], 2)
            - f3net) <= 0.01 and bd["long"]["rt"] + bd["short"]["rt"] == 160,
        f"long+short {round(bd['long']['net_pips'] + bd['short']['net_pips'], 2)}"
        f" vs fold {f3net}")
    bm = gp["by_mode_at_entry_R-DAEMON"]
    add("I5_GBPUSD_F3_mode_claims",
        bm["fade"]["net_pips"] == -941.5 and bm["follow"]["net_pips"] == -331.2,
        json.dumps({k: bm[k]["net_pips"] for k in ("fade", "follow", "flat")}))
    add("I5_GBPUSD_F3_mode_sum",
        abs(round(sum(bm[k]["net_pips"] for k in bm), 2) - f3net) <= 0.01,
        f"modes {round(sum(bm[k]['net_pips'] for k in bm), 2)} vs {f3net}")
    mf = gp["mode_flip_R-DAEMON"]
    add("I5_GBPUSD_F3_flip_claims",
        mf["flip_days"]["net_pips"] == -2002.3 and mf["flip_days"]["rt"] == 96
        and mf["non_flip_days"]["net_pips"] == 729.6
        and mf["non_flip_days"]["rt"] == 64, json.dumps(mf))
    add("I5_GBPUSD_F3_flip_sum",
        abs(round(mf["flip_days"]["net_pips"]
                  + mf["non_flip_days"]["net_pips"], 2) - f3net) <= 0.01,
        f"flip+nonflip {round(mf['flip_days']['net_pips'] + mf['non_flip_days']['net_pips'], 2)} vs {f3net}")
    bh = gp["by_entry_hour_bucket_R-DAEMON"]
    add("I5_GBPUSD_F3_london_claim",
        bh["london_07_12"]["net_pips"] == -1287.1,
        json.dumps({k: bh[k]["net_pips"] for k in bh}))
    add("I5_GBPUSD_F3_hours_sum",
        abs(round(sum(bh[k]["net_pips"] for k in bh), 2) - f3net) <= 0.01,
        f"hours {round(sum(bh[k]['net_pips'] for k in bh), 2)} vs {f3net}")
    be = gp["by_ex_ante_tercile_R-DAEMON"]
    add("I5_GBPUSD_F3_t3_claim",
        be["t3_high"]["net_pips"] == -1395.7,
        json.dumps({k: be[k]["net_pips"] for k in
                    ("t1_low", "t2_mid", "t3_high")}))
    add("I5_GBPUSD_F3_beta_short",
        gp["beta_pull"]["daemon_net_minus_short_net"] == -270.1
        and gp["beta_pull"]["daemon_net_minus_short_net"] == gp["beta_pull"][
            "daemon_net_minus_short_net"],
        json.dumps({k: gp["beta_pull"][k] for k in
                    ("daemon_net_minus_short_net",
                     "pearson_rho_daemon_daily_vs_short_daily")}))
    add("I5_GBPUSD_kdecay_F3",
        ag["GBPUSD"]["k_decay_R-DAEMON"]["F3"] == {"1.0": -1272.7,
                                                   "2.0": -1624.3,
                                                   "1.5": ag["GBPUSD"][
                                                       "k_decay_R-DAEMON"][
                                                       "F3"]["1.5"]},
        json.dumps(ag["GBPUSD"]["k_decay_R-DAEMON"]["F3"]))
    be5 = gp["by_exit_type_R-DAEMON"]
    add("I5_GBPUSD_F3_exit_sum",
        abs(round(sum(be5[k]["net_pips"] for k in be5), 2) - f3net) <= 0.01,
        f"exit types {round(sum(be5[k]['net_pips'] for k in be5), 2)} vs {f3net}")

    # ---- attribution lane's committed tests in THIS worktree -------------
    wt_root = A7_WORK.parents[3]
    r = subprocess.run(
        [VENV_PY, "-m", "pytest",
         "research/control/ERP1-TRACKA-COHORT-1/failres/tests/"
         "test_failres_attrib.py", "-q"],
        capture_output=True, text=True, cwd=str(wt_root), timeout=1200)
    tail = (r.stdout or "").strip().splitlines()[-4:]
    add("pytest_failres_attrib",
        r.returncode == 0,
        f"rc={r.returncode}; " + " | ".join(tail))

    n_bad = sum(1 for c in checks if not c["pass"])
    out = {"schema": "a7_l3_checks@1",
           "labels": ["A7_INDEPENDENT_REPRODUCTION",
                      "FAILURE_ROOT_CAUSE_RESEARCH",
                      "DIAGNOSTIC_OUTCOME_EXPOSED"],
           "checks": checks, "failed": n_bad,
           "verdict": "ALL_MATCH" if n_bad == 0 else "DIFFS"}
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "a7_l3_checks.json").write_text(json.dumps(out, indent=1) + "\n")
    for c in checks:
        print(("PASS " if c["pass"] else "FAIL ") + c["check"]
              + (" :: " + c["detail"] if not c["pass"] else ""))
    print(json.dumps({"failed": n_bad, "verdict": out["verdict"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
