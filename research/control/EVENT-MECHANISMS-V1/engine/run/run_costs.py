"""E7 — frozen cost constants + per-event cost bands + ceiling grid TEMPLATE."""
from __future__ import annotations

import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from emv1 import config as C
from emv1 import costs


def read_records(path):
    return [json.loads(l) for l in open(path) if l.strip()]


def main() -> None:
    ev = {
        "frozen_contract": {
            "source_path": "research/control/stocks_amihud_retest_v1/d1/cost_contract.json",
            "source_branch": "orca/stocks-amihud-retest-v1-integration",
            "blob_sha256": C.COST_CONTRACT_SHA256,
            "frozen_utc": "2026-09-23T06:40:00Z",
            "band_schedule_bps_per_fill": {"A": 10, "B": 15, "C": 25},
            "band_thresholds_dvmed60_usd": {"A_ge": 50_000_000, "B_ge": 10_000_000, "C_ge": 2_000_000},
            "dv_floor_usd": C.DV_FLOOR,
            "dv_window_sessions": C.DV_WINDOW,
            "dv_min_present": C.DV_MIN_PRESENT,
            "participation_cap_fraction": C.CAP_FRAC,
            "cost_debit_law": "cost exactly once per fill; entry and exit are separate fills",
            "stress": "x2.0 PRIMARY; ceiling_bps_round_trip 100 = 25 bps x 2 fills x 2.0",
            "q2_conditional_law": {
                "source_path": "research/wayfinder/LESSONS.md (Q-2)",
                "source_branch": "orca/stocks-amihud-retest-v1-integration",
                "constants": "at the open, per-minute movement ran 3.33x midday and the measured spread 3.35x midday",
                "application": "entries fill at session opens -> entry side priced at the EXPENSIVE open band (3.35x); exit at close ~ midday basis (1.0x)",
            },
            "band_c_13_8_percent": {
                "value": 0.138,
                "meaning": "band-C fraction of the STOCKS-NG6 fired population (NOT majority)",
                "source": "plans/CYCLE_REGISTRY.json STOCKS-NG6 terminal phase entry; research/wayfinder/HYPOTHESIS_LEDGER.md STOCKS-NG6 row",
                "engine_cross_check": "impl/samv1r/engine.py BANDS/DV_FLOOR/CAP_FRAC/STRESS_MULT verbatim",
            },
        },
    }
    all_recs = read_records(os.path.join(C.EVIDENCE_DIR, "a1_decisions.jsonl")) + \
               read_records(os.path.join(C.EVIDENCE_DIR, "a2_decisions.jsonl"))
    # per-event round-trip cost band at x1.0/1.5/2.0 (prices+bands only, R2-6)
    arms = sorted(set(r["arm_id"] for r in all_recs))
    per_arm = {a: [r for r in all_recs if r["arm_id"] == a] for a in arms}
    pops = {a: len(v) for a, v in per_arm.items()}
    class_counts = {a: dict(Counter(r["dv_band_class"] for r in v)) for a, v in per_arm.items()}
    ev["arm_band_class_counts"] = class_counts
    ev["per_event_round_trip_bps"] = {
        a: {
            "x1.0": round(costs.per_event_round_trip_bps(v[0], 1.0), 2) if v else None,
            "distribution_note": "bands vary per event by DVmed60 class; entry=base*3.35, exit=base*1.0",
            "class_table_bps": {c: round((bps * C.OPEN_BAND_MULT + bps * C.MIDDAY_BAND_MULT), 2)
                                 for c, bps in (("A", 10.0), ("B", 15.0), ("C", 25.0))},
        } for a, v in per_arm.items()
    }
    ev["ceiling_grid_template"] = costs.ceiling_grid(pops, class_counts)
    # median band per arm (feasibility descriptor, not a return)
    import numpy as np
    ev["arm_dvmed60_median"] = {
        a: (float(np.median([r["dvmed60_decision"] for r in v])) if v else None)
        for a, v in per_arm.items()
    }
    out = os.path.join(C.EVIDENCE_DIR, "cost_evidence.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(ev, open(out, "w"), indent=1, sort_keys=True)
    print("band class counts per arm:", json.dumps(class_counts, indent=1))
    print("grid rows:", len(ev["ceiling_grid_template"]), "->", out)


if __name__ == "__main__":
    main()
