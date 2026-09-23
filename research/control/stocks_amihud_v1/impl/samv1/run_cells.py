"""STOCKS-AMIHUD-V1 cell runner CLI.

  --mode dry-run : sanitized exact-arm dry-run (NO outcome at any depth;
                   records carry schedules/guards only; leak-scan enforced)
  --mode scored  : full outcomes + benchmarks + evaluation contract
                   (ONLY after owner GO at the cycle gate)

Exactly three cells: SAMV1-ANCHOR-ILLIQ21 / SAMV1-NEIGH-ILLIQ63 /
SAMV1-C-REVERSAL5. Refuses: a fourth cell, any S1-flavored input, unknown
mode. Deterministic: sorted iteration everywhere; RNG only in the seeded
benchmark twin. Trial identity fields on every record (A7 prelaunch M-1).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

IMPL = Path(__file__).resolve().parents[1]
HERE = IMPL.parent
sys.path.insert(0, str(IMPL))

from samv1 import engine as E                                   # noqa: E402
from samv1.panel import load_panel, sessions_from_spy           # noqa: E402
from samv1.portfolio import simulate, assert_no_outcome_fields  # noqa: E402

CELLS = [
    ("SAMV1-ANCHOR-ILLIQ21", "illiq21"),
    ("SAMV1-NEIGH-ILLIQ63", "illiq63"),
    ("SAMV1-C-REVERSAL5", "reversal5"),
]


def load_universe_codes() -> list[str]:
    uni = json.loads((HERE / "p0" / "universe_frozen.json").read_text())
    return sorted(uni["codes"].keys())


def identity_digests() -> dict:
    fam = (HERE / "d1" / "family_contract.json").read_bytes()
    cost = (HERE / "d1" / "cost_contract.json").read_bytes()
    implc = (IMPL / "impl_contract.json").read_bytes()
    dvh = hashlib.sha256(fam + cost + implc).hexdigest()
    snap = hashlib.sha256(
        (HERE / "p0" / "crawl_manifest_v2.jsonl").read_bytes()
        + (HERE / "p0" / "universe_frozen.json").read_bytes()).hexdigest()
    import subprocess
    head = subprocess.run(
        ["git", "-C", str(HERE.parents[1]), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True).stdout.strip()
    return {"cycle_id": "STOCKS-AMIHUD-V1",
            "family_id": "SAMV1-AMIHUD-LONG-ILLIQ",
            "arm_config_digest": dvh,
            "data_snapshot_digest": snap,
            "code_freeze_sha": head,
            "cost_tier": "BAND_BPS{10,15,25}@ADV{50M,10M,2M}+stress2.0",
            "fold_contract": "F1=CY2019|F2=CY2020|F3=CY2021-22"}


def main() -> int:
    for a in sys.argv[1:]:
        low = a.lower()
        if "--s1" in low or "/s1/" in low or "s1:" in low:
            print("REFUSED: S1-flavored input", file=sys.stderr)
            return 9
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["dry-run", "scored"])
    args = ap.parse_args()

    t0 = time.time()
    codes = load_universe_codes() + ["SPY", "AAPL", "TSLA"]
    panel, guard_load = load_panel(codes)
    sessions = sessions_from_spy()
    spy = panel["SPY"]
    print(f"panel: {len(panel)} names, {len(sessions)} sessions, "
          f"load_guards={guard_load}", flush=True)

    records = []
    anchor_per_date = None
    anchor_holds = None
    for cell_id, axis in CELLS:
        sim = simulate(panel, sessions, axis, scored=(args.mode == "scored"))
        rec = {
            "cell_id": cell_id,
            **identity_digests(),
            "axis": axis,
            "mode": args.mode,
            "n_holds": len(sim["holds"]),
            "n_entries": sim["guards"].entries,
            "per_date": [
                {"date": d["date"], "fold": d["fold"], "n_elig": d["n_elig"],
                 "n_book": d["n_book"], "bookable": d["bookable"],
                 "book_codes": d.get("book_codes", [])}
                for d in sim["per_date"]],
            "guards": sim["guards"].as_dict(),
            "load_guards": guard_load,
        }
        if axis == "illiq21":
            anchor_per_date = sim["per_date"]
            anchor_holds = sim["holds"]
        if args.mode == "scored":
            from samv1 import evaluate as EV
            from samv1 import benchmarks as BM
            rows = EV.hold_rows(sim["holds"])
            rec["hold_rows_count"] = len(rows)
            rec["folds"] = {f: EV.fold_summary(rows, f) for f in E.FOLDS}
            rec["folds_stress2"] = {}
            for f in E.FOLDS:
                base = rec["folds"][f]
                rec["folds_stress2"][f] = {
                    "fold": f, "n_holds": base["n_holds"],
                    "gross_pnl": base["gross_pnl"],
                    "costs": base["costs"] * E.STRESS_MULT,
                    "net_pnl": base["gross_pnl"] - base["costs"] * E.STRESS_MULT}
            rec["annual_split_net"] = EV.annual_split(rows)
            curve = EV.equity_curve(sim["holds"])
            rec["mdd_pct"] = EV.max_drawdown(curve)
            rec["concentration"] = EV.concentration(rows)
            rec["drop_one"] = EV.drop_one(rows)
            te = EV.turnover_exposure(sim["per_date"], sim["holds"])
            rec["exposure"] = te
            rec["beta_vs_spy"] = EV.beta_from_panel(sim["holds"], panel, spy)
            # benchmarks (evaluation context)
            spyb = BM.spy_twin(spy, sessions, scored=True)
            spy_rows = EV.hold_rows(spyb["holds"])
            rec["spy_benchmark_folds"] = {
                h.fold: {"entry": h.entry_fill_date, "exit": h.exit.fill_date,
                         "gross_pnl": h.notional * (h.exit.fill_px / h.entry_px - 1.0),
                         "costs": h.entry_cost + (h.exit_cost or 0.0)}
                for h in spyb["holds"] if h.exit is not None}
            rec["spy_excess_folds"] = EV.spy_excess_folds(
                [{ "fold": f, "net_pnl": rec["folds"][f]["net_pnl"]} for f in E.FOLDS],
                spyb["holds"], te["mean_invested_weight"])
            mb = BM.matched_book(anchor_per_date, panel, sessions, scored=True)
            mb_rows = EV.hold_rows(mb["holds"])
            rec["matched_book_folds"] = {
                f: (EV.fold_summary(mb_rows, f)
                    if any(r["fold"] == f for r in mb_rows) else None)
                for f in E.FOLDS} if mb_rows else {}
            rt = BM.random_timing_twins(spy, sessions)
            rt_nets = []
            for cal in rt:
                rr = EV.hold_rows(cal["holds"])
                if rr:
                    rt_nets.append(sum(r["net_pnl"] for r in rr))
            rec["random_timing_twin_n"] = len(rt_nets)
            if rt_nets:
                rt_nets.sort()
                rec["random_timing_twin_net_pnl_median"] = rt_nets[len(rt_nets)//2]
                rec["random_timing_twin_net_pnl_min"] = rt_nets[0]
                rec["random_timing_twin_net_pnl_max"] = rt_nets[-1]
            rec["hold_rows"] = rows  # full attribution rows (scored only)
        records.append(rec)

    ids = [r["cell_id"] for r in records]
    if len(ids) != 3 or len(set(ids)) != 3:
        print("FAIL: exact-3-cells/distinct-IDs violated", file=sys.stderr)
        return 8
    if args.mode == "dry-run":
        try:
            for r in records:
                assert_no_outcome_fields(r, r["cell_id"])
        except E.FailLoud as ex:
            print(f"FAIL: {ex}", file=sys.stderr)
            return 7
        vacuous = [r["cell_id"] for r in records if r["n_entries"] == 0]
        if vacuous:
            print(f"FAIL: vacuous cells {vacuous}", file=sys.stderr)
            return 6
        out = HERE / "z_dryrun" / "z_dryrun_records.json"
        out.parent.mkdir(exist_ok=True)
        out.write_text(json.dumps({"schema": "z_dryrun/stocks_amihud_v1@1",
                                   "mode": "dry-run",
                                   "records": records,
                                   "elapsed_s": round(time.time() - t0, 1)},
                                  indent=1))
        print(f"dry-run OK -> {out} ({time.time()-t0:.0f}s)", flush=True)
        return 0

    out = HERE / "scored" / "scored_records.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"schema": "scored/stocks_amihud_v1@1",
                               "mode": "scored", "records": records},
                              indent=1))
    print(f"scored OK -> {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
