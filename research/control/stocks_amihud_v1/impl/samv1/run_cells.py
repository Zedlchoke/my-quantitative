"""STOCKS-AMIHUD-V1 cell runner CLI.

  --mode dry-run : sanitized exact-arm dry-run (NO outcome at any depth;
                   records carry schedules/guards only; leak-scan enforced)
  --mode scored  : full outcomes (ONLY after owner GO at the cycle gate)

Exactly three cells: SAMV1-ANCHOR-ILLIQ21 / SAMV1-NEIGH-ILLIQ63 /
SAMV1-C-REVERSAL5. Refuses: a fourth cell, any S1-flavored input, unknown
mode. Deterministic: sorted iteration everywhere; no RNG in cells (RNG
only in the benchmark twin, seeded).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

IMPL = Path(__file__).resolve().parents[1]
HERE = IMPL.parent
sys.path.insert(0, str(IMPL))

from samv1 import engine as E  # noqa: E402
from samv1.panel import load_panel, sessions_from_spy  # noqa: E402
from samv1.portfolio import simulate, assert_no_outcome_fields  # noqa: E402

CELLS = [
    ("SAMV1-ANCHOR-ILLIQ21", "illiq21"),
    ("SAMV1-NEIGH-ILLIQ63", "illiq63"),
    ("SAMV1-C-REVERSAL5", "reversal5"),
]


def load_universe_codes() -> list[str]:
    uni = json.loads((HERE / "p0" / "universe_frozen.json").read_text())
    return sorted(uni["codes"].keys())


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
    print(f"panel: {len(panel)} names, {len(sessions)} sessions, "
          f"load_guards={guard_load}", flush=True)

    records = []
    for cell_id, axis in CELLS:
        sim = simulate(panel, sessions, axis, scored=(args.mode == "scored"))
        rec = {
            "cell_id": cell_id,
            "cycle_id": "STOCKS-AMIHUD-V1",
            "arm_id": cell_id,
            "axis": axis,
            "mode": args.mode,
            "n_holds": len(sim["holds"]),
            "n_entries": sim["guards"].entries,
            "per_date": [
                {"date": d["date"], "fold": d["fold"], "n_elig": d["n_elig"],
                 "n_book": d["n_book"], "bookable": d["bookable"]}
                for d in sim["per_date"]],
            "guards": sim["guards"].as_dict(),
            "load_guards": guard_load,
        }
        if args.mode == "scored":
            from samv1 import evaluate as EV
            folds = {}
            for f in E.FOLDS:
                folds[f] = EV.fold_summary(sim["holds"], f)
                folds[f + "_stress2"] = EV.fold_summary(sim["holds"], f,
                                                        E.STRESS_MULT)
            curve = EV.equity_curve(sim["holds"], sessions)
            rec["folds"] = folds
            rec["mdd_pct"] = EV.max_drawdown(curve)
            rec["concentration"] = EV.concentration(sim["holds"])
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
