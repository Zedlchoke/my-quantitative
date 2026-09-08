#!/usr/bin/env python
"""FOREX-FREE-V3 execution driver: runs the six frozen cells SERIALLY per
family (anchor -> neighbour -> causal control) from one code tree.

Modes:
  dummy  - full pipeline with scored=false, real_pnl=false: decision events
           and mechanics on the supplied data paths, book columns are 0.0
           placeholders, publication refused; writes a dry-run report only.
           Reveals no outcome.
  scored - real PnL; REFUSES to start unless --authorization carries the
           frozen freeze token (FOREX_FREE_V3_W3).  The owner must
           explicitly authorize scored execution before this mode is ever
           invoked.

Families are supplied as repeatable --family family_id=module.path options;
each module implements the runner family API contract (see the
research.assets.forex_free_v3.scored_runner module docstring).  Any arm
exceeding the frozen per-arm wall clock is a fail-closed TECHABORT: the run
stops, nothing further is booked or published, and the report records the
abort (PLAN_forex_v3.md section 11).

Usage:
  .venv/bin/python -m research.assets.forex_free_v3.exec_driver \
      --mode dummy --data-paths <paths.json> --family family1=fam_pkg.fam_mod \
      --report <out.json> [--ledger <path> --authorization <path>
      --freeze-token FOREX_FREE_V3_W3 --timeout-minutes 60]
"""
import argparse
import importlib
import json
import time

from research.assets.forex_free_v3 import scored_runner as R


def _load_families(specs):
    for spec in specs:
        if "=" not in spec:
            raise SystemExit(f"--family expects family_id=module.path, got {spec!r}")
        family_id, module_path = spec.split("=", 1)
        R.register_family(family_id, importlib.import_module(module_path))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("dummy", "scored"), required=True)
    ap.add_argument("--data-paths", required=True,
                    help="JSON file holding the data_paths dict passed to families")
    ap.add_argument("--family", action="append", required=True,
                    help="family_id=module.path (repeatable)")
    ap.add_argument("--report", required=True)
    ap.add_argument("--ledger", default=None)
    ap.add_argument("--authorization", default=None)
    ap.add_argument("--freeze-token", default=R.FREEZE_TOKEN)
    ap.add_argument("--timeout-minutes", type=float, default=None)
    args = ap.parse_args()

    if args.mode == "scored":
        if not (args.ledger and args.authorization and args.freeze_token):
            raise SystemExit("scored mode requires --ledger, --authorization, --freeze-token")

    _load_families(args.family)
    with open(args.data_paths, "r", encoding="utf-8") as handle:
        data_paths = json.load(handle)
    freeze_token = R.FREEZE_TOKEN if args.mode == "scored" else None

    t0 = time.time()
    cells = []
    techaborted = False
    for family_id in R.FAMILIES:
        family_cells = {}
        for arm in R.ARMS:
            try:
                rec = R.compute_cell(family_id, arm, data_paths,
                                     freeze_token=freeze_token,
                                     timeout_minutes=args.timeout_minutes)
            except R.TechAbort as exc:
                cells.append({"cell_id": f"{family_id}:{arm}:TECHABORT",
                              "gates_pass": False, "gate_reasons": ["TECHABORT_TIMEOUT"],
                              "detail": str(exc), "dry_run": args.mode == "dummy"})
                techaborted = True
                break
            gates, reasons = R.stage_a_gates(rec)
            family_cells[arm] = rec
            published_now = 0
            if args.mode == "scored":
                rec["observed_delta"], published_now = R.publish_cell(
                    args.ledger, rec, args.authorization, args.freeze_token)
                rec["published"] = published_now == 1
            rec["gate_evaluated"] = True
            cells.append({"cell_id": rec["cell_id"], "gates_pass": gates,
                          "gate_reasons": reasons, "published_now": published_now,
                          "dry_run": rec["dry_run"]})
        if techaborted:
            break
        if len(family_cells) == len(R.ARMS):
            sanity, sanity_reasons = R.mechanism_sanity(family_cells)
            cells.append({"cell_id": f"{family_id}:MECHANISM_SANITY",
                          "gates_pass": sanity, "gate_reasons": sanity_reasons,
                          "dry_run": args.mode == "dummy"})

    report = {
        "schema": "forex_free_v3_exec_report_v1",
        "mode": args.mode,
        "scored": args.mode == "scored",
        "real_pnl": args.mode == "scored",
        "techaborted": techaborted,
        "cells": cells,
        "elapsed_s": round(time.time() - t0, 1),
        "note": ("DUMMY DRY-RUN: scored=false, real_pnl=false, publication "
                 "refused; book values are placeholders and carry no outcome "
                 "information." if args.mode == "dummy" else
                 "SCORED EXECUTION (owner-authorized)"),
    }
    if techaborted:
        report["note"] += " FAIL-CLOSED TECHABORT: run stopped before further booking."
    with open(args.report, "w") as f:
        json.dump(report, f, indent=1)
    print(json.dumps({"mode": args.mode, "cells": len(cells),
                      "techaborted": techaborted, "report": args.report}))
    if techaborted:
        raise SystemExit(3)


if __name__ == "__main__":
    main()
