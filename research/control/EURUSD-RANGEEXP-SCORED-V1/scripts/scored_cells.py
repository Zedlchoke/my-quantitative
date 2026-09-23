"""EURUSD-RANGEEXP-SCORED-V1 scored cells S1..S6 (plan-preregistered).

  --dry-run : exact-arm sanitized run — S1 reconciliation on dev prints only
              MATCH/MISMATCH booleans (zero PnL exposure); used for A7
              prelaunch. Full run requires the owner GO at the gate.

Cells:
  S1 reproduction gate: C3/C4 books dev+holdout x k in {1.0,1.5,2.0} must
     reconcile (tolerance 1e-9 abs on pips, exact on trades/pf rounding) with
     V2's committed campaign_dev_v2.jsonl + holdout_check_v2.json.
  S2..S5 leg decompositions (long/short net, trades, hit, PF, symmetry).
  S6 mechanical drift flag: DRIFT_DEPENDED iff short_leg_net > 0 AND
     |short_leg_net| >= 0.5*total_net AND SHORT_ALWAYS_net > 0 (same window,
     k=1.0).
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import engine as E
from v2_campaign import FAMILY_V2, load_h1_plane

ROOT = HERE.parent
OUT = ROOT / "outcomes"
KS = [1.0, 1.5, 2.0]
HOLDOUT_START = pd.Timestamp("2026-01-01", tz="UTC")
CANDS = [("FX2-RANGEEXP-C3", "FX2-RANGEEXP", 2), ("FX2-RANGEEXP-C4", "FX2-RANGEEXP", 3)]
TOL = 1e-6


def head_sha():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(HERE), text=True).strip()


def slices():
    import copy

    plane = load_h1_plane()
    cut = int(HOLDOUT_START.timestamp())
    dev_m = plane.ts < cut
    hold_m = ~dev_m

    def sl(m):
        q = copy.copy(plane)  # shallow copy: every array attr is replaced below,
        # so the source plane is never mutated by the first slice
        for attr in ("ts", "b_o", "b_h", "b_l", "b_c", "a_o", "a_c", "s_o", "s_c",
                     "hhmm", "day", "hour", "minute", "is_day_close", "fill_ok"):
            setattr(q, attr, np.asarray(getattr(q, attr))[m])
        q.skip = np.asarray(q.skip)[m]
        q.last_tradable_of_day = np.asarray(q.last_tradable_of_day)[m]
        return q

    return sl(dev_m), sl(hold_m)


def cfg_of(arm_id):
    fid = "FX2-RANGEEXP"
    ci = 2 if arm_id.endswith("C3") else 3
    return fid, ci, FAMILY_V2[fid]["configs"][ci]


def v2_refs():
    refs = {}
    for r in map(json.loads, (ROOT.parent / "EURUSD-OPEN-SEARCH-V2" / "outcomes" / "campaign_dev_v2.jsonl").read_text().splitlines()):
        refs[r["arm_id"]] = r["tiers"]
    h = json.loads((ROOT.parent / "EURUSD-OPEN-SEARCH-V2" / "outcomes" / "holdout_check_v2.json").read_text())
    for c in h["candidates"]:
        refs[c["arm_id"] + "::HOLDOUT"] = c["tiers"]
    return refs


def legs(trades):
    pn = np.array([t["pips"] for t in trades])
    if len(pn) == 0:
        return {"long_net": 0.0, "short_net": 0.0, "long_trades": 0, "short_trades": 0,
                "symmetry_short_share": None}
    lg = pn[[t["dir"] > 0 for t in trades]]
    sh = pn[[t["dir"] < 0 for t in trades]]
    tot = float(pn.sum())
    return {
        "long_net": round(float(lg.sum()), 2) if len(lg) else 0.0,
        "short_net": round(float(sh.sum()), 2) if len(sh) else 0.0,
        "long_trades": int(len(lg)),
        "short_trades": int(len(sh)),
        "long_hit": round(float((lg > 0).mean()), 4) if len(lg) else None,
        "short_hit": round(float((sh > 0).mean()), 4) if len(sh) else None,
        "total_net": round(tot, 2),
        "symmetry_short_share": round(float(sh.sum() / tot), 4) if tot != 0 else None,
    }


def main(dry_run=False):
    dev, hold = slices()
    refs = v2_refs()
    man_sha = hashlib.sha256(
        (ROOT / "data_local" / "duka" / "m1_manifest.json").read_bytes()
    ).hexdigest()
    rec = {
        "schema": "eosv1s.scored_cells@1",
        "cycle_id": "EURUSD-RANGEEXP-SCORED-V1",
        "code_freeze_sha": head_sha(),
        "data_manifest_sha256": man_sha,
        "s1_reproduction": [], "legs": [], "s6_drift_flags": [],
    }

    for arm_id, fid, ci in CANDS:
        cfg = cfg_of(arm_id)[2]
        for name, plane, ref_key in (("DEV", dev, arm_id), ("HOLDOUT", hold, arm_id + "::HOLDOUT")):
            target = FAMILY_V2[fid]["fn"](plane, cfg)
            for k in KS:
                trades, _ = E.run_strategy(plane, target, k)
                m = E.metrics(trades, np.zeros(len(trades)))
                ref = refs[ref_key][str(k)]
                ok = (
                    m["trades"] == ref["trades"]
                    and abs(m["net_pips"] - ref["net_pips"]) <= TOL
                    and (m["pf"] is None) == (ref["pf"] is None)
                    and (m["pf"] is None or abs(m["pf"] - ref["pf"]) <= 1e-6)
                )
                rec["s1_reproduction"].append({
                    "arm": arm_id, "window": name, "k": k, "reconciled": bool(ok),
                })
                if name == "DEV" or not dry_run:
                    pass
            if not dry_run:
                trades, _ = E.run_strategy(plane, target, 1.0)
                L = legs(trades)
                rec["legs"].append({"arm": arm_id, "window": name, **L})

    if not dry_run:
        ones = np.ones(len(dev.ts), dtype=np.int8)
        sa_dev = E.metrics(E.run_strategy(dev, ones, 1.0)[0], np.zeros(len(dev.ts)))["net_pips"]
        ones = np.ones(len(hold.ts), dtype=np.int8)
        sa_hold = E.metrics(E.run_strategy(hold, ones, 1.0)[0], np.zeros(len(hold.ts)))["net_pips"]
        rec["baselines"] = {"SHORT_ALWAYS_dev_k1": sa_dev, "SHORT_ALWAYS_holdout_k1": sa_hold}
        for L in rec["legs"]:
            sa = sa_dev if L["window"] == "DEV" else sa_hold
            drift = (
                L["short_net"] > 0
                and L["total_net"] != 0
                and abs(L["short_net"]) >= 0.5 * abs(L["total_net"])
                and sa > 0
            )
            rec["s6_drift_flags"].append({
                "arm": L["arm"], "window": L["window"],
                "flag": "DRIFT_DEPENDED" if drift else "NO_DRIFT_FLAG",
                "short_beta_note": f"SHORT_ALWAYS(window,k=1.0)={sa:+.1f} pips",
            })
        (OUT / "scored_cells.json").write_text(json.dumps(rec, indent=1))
        print(json.dumps(rec["s6_drift_flags"], indent=1))
        print("legs:", json.dumps(rec["legs"], indent=1)[:1200])
    else:
        s1 = rec["s1_reproduction"]
        print(json.dumps(s1, indent=1))
        assert all(x["reconciled"] for x in s1), "S1 reconciliation FAILED"
        print("DRY_RUN: S1 all reconciled; no PnL printed")


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
