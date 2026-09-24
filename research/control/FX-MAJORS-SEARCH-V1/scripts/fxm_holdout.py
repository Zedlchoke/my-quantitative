"""FX-MAJORS-SEARCH-V1 holdout check: ONE look per pair (leak-guarded)."""
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import engine as E
import fx_lib as fx
from fxm_campaign import FAMILY, KS, HOLDOUT_START, load_h1_plane, slice_plane

ROOT = HERE.parent
OUT = ROOT / "outcomes"


def main():
    cand = json.loads((OUT / "candidates_frozen_fx.json").read_text())
    results = {"schema": "fxm.holdout_check@1", "run_count": 1, "pairs": {}}
    logp = OUT / "holdout_run_count_fx.json"
    if logp.exists():
        results["run_count"] = json.loads(logp.read_text()).get("run_count", 0) + 1
    for pair in cand["pairs"]:
        pip = fx.PAIRS[pair]["pip"]
        plane = load_h1_plane(pair)
        hold = slice_plane(plane, plane.ts >= int(HOLDOUT_START.timestamp()))
        if (hold.ts < int(HOLDOUT_START.timestamp())).any() or len(hold.ts) < 1000:
            raise SystemExit(f"FAIL_CLOSED: {pair} holdout plane invalid")
        out = {"holdout_bars": int(len(hold.ts)), "candidates": [], "baselines": {}}

        def run_one(target):
            o = {}
            for k in KS:
                trades, equity = E.run_strategy(hold, target, k, pip=pip)
                o[str(k)] = E.metrics(trades, equity)
            return o

        for c in cand["pairs"][pair]:
            spec = FAMILY[c["family_id"]]
            cfg = spec["configs"][c["config_index"]]
            out["candidates"].append({"arm_id": c["arm_id"], "config": cfg,
                                       "config_digest": E.config_digest(c["family_id"], cfg),
                                       "tiers": run_one(spec["fn"](hold, cfg, pip))})
        n = len(hold.ts)
        rng = np.random.default_rng(20260923 + hash(pair) % 1000)
        out["baselines"]["LONG_ALWAYS"] = run_one(np.ones(n, dtype=np.int8))
        out["baselines"]["SHORT_ALWAYS"] = run_one(-np.ones(n, dtype=np.int8))
        out["baselines"]["CASH"] = {"net_pips": 0.0, "trades": 0}
        out["baselines"]["RANDOM_MATCHED"] = run_one(rng.integers(-1, 2, size=n).astype(np.int8))
        results["pairs"][pair] = out

    results["measured_utc"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    results["note"] = ("program-S0 evidence; SUCCESS = net>0 @1.0 AND @1.5 per pair; "
                        "one look, failure final, no rescue")
    (OUT / "holdout_check_fx.json").write_text(json.dumps(results, indent=1))
    logp.write_text(json.dumps({"run_count": results["run_count"]}))
    for pair, out in results["pairs"].items():
        for c in out["candidates"]:
            print(pair, c["arm_id"], json.dumps(c["tiers"]))
        print(pair, "baselines:", json.dumps(out["baselines"], indent=1)[:500])


if __name__ == "__main__":
    main()
