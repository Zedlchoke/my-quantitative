"""V2 P3 holdout check: ONE look, leak-guarded (loads only ts >= 2026-01-01)."""
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import engine as E
from v2_campaign import FAMILY_V2, KS, HOLDOUT_START, load_h1_plane

ROOT = HERE.parent
OUT = ROOT / "outcomes"
RUN_LOG = OUT / "holdout_run_count_v2.json"


def main():
    cand = json.loads((OUT / "candidates_frozen_v2.json").read_text())
    plane_full = load_h1_plane()
    mask = plane_full.ts >= int(HOLDOUT_START.timestamp())
    hold = plane_full
    for attr in ("ts", "b_o", "b_h", "b_l", "b_c", "a_o", "a_c", "s_o", "s_c",
                 "hhmm", "day", "hour", "minute", "is_day_close", "fill_ok"):
        setattr(hold, attr, getattr(hold, attr)[mask])
    hold.skip = hold.skip[mask]
    hold.last_tradable_of_day = hold.last_tradable_of_day[mask]
    if (hold.ts < int(HOLDOUT_START.timestamp())).any() or len(hold.ts) < 2000:
        raise SystemExit("FAIL_CLOSED: holdout plane invalid")

    results = {"schema": "eosv2.holdout_check@1", "run_count": 1,
               "holdout_bars": int(len(hold.ts)),
               "window": [str(pd.Timestamp(hold.ts.min(), unit="s", tz="UTC")),
                          str(pd.Timestamp(hold.ts.max(), unit="s", tz="UTC"))],
               "candidates": [], "baselines": {}}
    if RUN_LOG.exists():
        prev = json.loads(RUN_LOG.read_text())
        results["run_count"] = prev.get("run_count", 0) + 1
        if prev.get("holdout_bars") != len(hold.ts):
            results["tamper_warning"] = "holdout bar count changed"

    def run_one(target):
        out = {}
        for k in KS:
            trades, equity = E.run_strategy(hold, target, k)
            out[str(k)] = E.metrics(trades, equity)
        return out

    for c in cand["candidates"]:
        spec = FAMILY_V2[c["family_id"]]
        cfg = spec["configs"][c["config_index"]]
        results["candidates"].append({
            "arm_id": c["arm_id"], "family_id": c["family_id"],
            "config_index": c["config_index"], "config": cfg,
            "config_digest": E.config_digest(c["family_id"], cfg),
            "tiers": run_one(spec["fn"](hold, cfg)),
        })
    ones = np.ones(len(hold.ts), dtype=np.int8)
    results["baselines"]["LONG_ALWAYS"] = run_one(ones)
    results["baselines"]["SHORT_ALWAYS"] = run_one(-ones)
    results["baselines"]["CASH"] = {"net_pips": 0.0, "trades": 0}
    rng = np.random.default_rng(20260923)
    results["baselines"]["RANDOM_MATCHED(seed=20260923)"] = run_one(
        rng.integers(-1, 2, size=len(hold.ts)).astype(np.int8)
    )
    results["measured_utc"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    results["note"] = "program-S0 evidence only; failure is final, no rescue (plan §4)"
    (OUT / "holdout_check_v2.json").write_text(json.dumps(results, indent=1))
    RUN_LOG.write_text(json.dumps({"run_count": results["run_count"],
                                   "holdout_bars": int(len(hold.ts))}))
    for c in results["candidates"]:
        print(c["arm_id"], json.dumps(c["tiers"]))
    print("baselines:", json.dumps(results["baselines"], indent=1)[:600])


if __name__ == "__main__":
    main()
