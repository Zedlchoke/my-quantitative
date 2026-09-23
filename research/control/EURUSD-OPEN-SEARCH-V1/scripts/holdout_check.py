"""P3 candidate check: ONE holdout pass + baselines (leak-guarded).

Inputs : outcomes/candidates_frozen.json  (written by the freeze step only)
         data_local/derived/bars15.parquet
Loads ONLY bars with ts >= HOLDOUT_START (2023-07-01) — the holdout plane.
Runs each frozen candidate's family/config ONCE at k=1.0/1.5/2.0 plus the
frozen baselines, writes outcomes/holdout_check.json, and exits. Re-running
against a failed holdout with changed parameters is FORBIDDEN by plan §5;
this script records run_count to make tampering visible.
"""
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import engine as E

ROOT = HERE.parent
BARS = ROOT / "data_local" / "derived" / "bars15.parquet"
OUT = ROOT / "outcomes"
FREEZE = json.loads((ROOT / "selection_freeze.json").read_text())

HOLDOUT_START = pd.Timestamp("2023-07-01", tz="UTC")
KS = [1.0, 1.5, 2.0]
RUN_LOG = OUT / "holdout_run_count.json"


def main():
    cand = json.loads((OUT / "candidates_frozen.json").read_text())
    df = pd.read_parquet(BARS)
    hold = df[df["ts"] >= HOLDOUT_START].reset_index(drop=True)
    if len(hold) < 50_000:
        raise SystemExit("FAIL_CLOSED: holdout plane unexpectedly small")
    plane = E.Plane(hold)
    results = {"schema": "eosv1.holdout_check@1", "run_count": 1, "candidates": [],
                "baselines": {}}
    if RUN_LOG.exists():
        prev = json.loads(RUN_LOG.read_text())
        results["run_count"] = prev.get("run_count", 0) + 1
        if prev.get("holdout_bars") != len(hold):
            results["tamper_warning"] = "holdout bar count changed since previous run"

    def run_one(name, target):
        out = {}
        for k in KS:
            trades, equity = E.run_strategy(plane, target, k)
            out[str(k)] = E.metrics(trades, equity)
        return out

    for c in cand["candidates"]:
        spec = E.FAMILIES[c["family_id"]]
        cfg = spec["configs"][c["config_index"]]
        target = spec["fn"](plane, cfg)
        results["candidates"].append({
            "arm_id": c["arm_id"], "family_id": c["family_id"],
            "config_index": c["config_index"], "config": cfg,
            "config_digest": E.config_digest(c["family_id"], cfg),
            "tiers": run_one(c["arm_id"], target),
        })

    ones = np.ones(len(plane.ts), dtype=np.int8)
    results["baselines"]["LONG_ALWAYS"] = run_one("LONG_ALWAYS", ones)
    results["baselines"]["SHORT_ALWAYS"] = run_one("SHORT_ALWAYS", -ones)
    results["baselines"]["CASH"] = {"net_pips": 0.0, "trades": 0}
    rng = np.random.default_rng(20260923)
    rnd = rng.integers(-1, 2, size=len(plane.ts)).astype(np.int8)
    results["baselines"]["RANDOM_MATCHED(seed=20260923)"] = run_one("RANDOM", rnd)

    results["holdout_bars"] = int(len(hold))
    results["measured_utc"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    results["note"] = ("program-S0 evidence only; never S1, never a real-money "
                       "claim (plan §5); a failed holdout is final for this campaign")
    (OUT / "holdout_check.json").write_text(json.dumps(results, indent=1))
    RUN_LOG.write_text(json.dumps({"run_count": results["run_count"],
                                   "holdout_bars": len(hold)}))
    print(json.dumps(results["candidates"], indent=1)[:1500])
    print("baselines:", json.dumps(results["baselines"], indent=1)[:800])


if __name__ == "__main__":
    main()
