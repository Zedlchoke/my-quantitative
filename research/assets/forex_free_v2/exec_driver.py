#!/usr/bin/env python
"""FOREX-FREE-V2 execution driver: runs the six frozen cells SERIALLY
(family1 anchor->neighbour->control, then family2) from one code tree.

Modes:
  dummy  - full pipeline with scored=false, real_pnl=false: schedules and
           mechanics on the real snapshot, placeholder pnl=0, publication
           refused; writes a dry-run report only. Reveals no outcome.
  scored - real PnL; REFUSES to start unless --authorization carries the
           frozen W2 SHA. The owner must explicitly authorize scored
           execution before this mode is ever invoked.

Usage:
  .venv/bin/python -m research.assets.forex_free_v2.exec_driver \
      --mode dummy --data-root <path> --report <out.json> \
      [--ledger <path> --authorization <path> --w2-sha <sha>]
"""
import argparse
import json
import time

from research.assets.forex_free_v2 import scored_runner as R

ARMS = ("anchor", "neighbour", "control")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("dummy", "scored"), required=True)
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--ledger", default=None)
    ap.add_argument("--authorization", default=None)
    ap.add_argument("--w2-sha", default=None)
    args = ap.parse_args()

    if args.mode == "scored":
        if not (args.ledger and args.authorization and args.w2_sha):
            raise SystemExit("scored mode requires --ledger, --authorization, --w2-sha")

    t0 = time.time()
    rows = R.load_rows(args.data_root)
    cells = []
    for family_id in ("family1", "family2"):
        family_cells = {}
        for arm in ARMS:
            rec = R.compute_cell(family_id, arm, rows, dry_run=(args.mode == "dummy"))
            gates, reasons = R.stage_a_gates(rec)
            family_cells[arm] = rec
            published_now = 0
            if args.mode == "scored":
                rec["observed_delta"], published_now = R.publish_cell(
                    args.ledger, rec, args.authorization, args.w2_sha)
                rec["published"] = published_now == 1
            rec["gate_evaluated"] = True
            cells.append({"cell_id": rec["cell_id"], "gates_pass": gates,
                          "gate_reasons": reasons, "published_now": published_now,
                          "dry_run": rec["dry_run"]})
        sanity, sanity_reasons = R.mechanism_sanity(family_cells)
        cells.append({"cell_id": f"{family_id}:MECHANISM_SANITY",
                      "gates_pass": sanity, "gate_reasons": sanity_reasons,
                      "dry_run": args.mode == "dummy"})

    report = {
        "schema": "forex_free_v2_exec_report_v1",
        "mode": args.mode,
        "scored": args.mode == "scored",
        "real_pnl": args.mode == "scored",
        "cells": cells,
        "elapsed_s": round(time.time() - t0, 1),
        "note": ("DUMMY DRY-RUN: scored=false, real_pnl=false, publication "
                 "refused; pnl values are placeholders and carry no outcome "
                 "information." if args.mode == "dummy" else
                 "SCORED EXECUTION (owner-authorized)"),
    }
    with open(args.report, "w") as f:
        json.dump(report, f, indent=1)
    print(json.dumps({"mode": args.mode, "cells": len(cells),
                      "report": args.report}))


if __name__ == "__main__":
    main()
