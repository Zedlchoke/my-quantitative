"""Dev-phase exploratory campaign runner (leak-guarded).

Physically loads ONLY bars with ts < HOLDOUT_START (2023-07-01 UTC): the
sealed holdout cannot be touched by this script. Emits one JSONL record per
trial (identity + per-cost-tier + per-fold metrics + gates) and a full
distribution summary. No candidate selection happens here beyond the frozen
rule; freezing writes candidates_frozen.json in a separate step.
"""
import datetime as dt
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

ROOT = HERE.parent
BARS = ROOT / "data_local" / "derived" / "bars15.parquet"
MANIFEST = ROOT / "data_local" / "duka" / "m1_manifest.json"
OUT = ROOT / "outcomes"
FREEZE = json.loads((ROOT / "selection_freeze.json").read_text())

HOLDOUT_START = pd.Timestamp("2023-07-01", tz="UTC")
KS = [1.0, 1.5, 2.0]


def head_sha():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(HERE), text=True
        ).strip()
    except Exception:
        return "UNMEASURED"


def fold_of(ts):
    d = str(pd.Timestamp(ts, unit="s", tz="UTC").date())
    if d <= "2022-06-30":
        return "F1" if d >= "2022-01-01" else "WARMUP"
    if d <= "2022-12-31":
        return "F2"
    if d <= "2023-06-30":
        return "F3"
    return "POST_DEV"


def main():
    df = pd.read_parquet(BARS)
    leak = int((df["ts"] >= HOLDOUT_START).sum())
    if leak:
        raise SystemExit(f"FAIL_CLOSED: {leak} holdout bars present in dev runner")
    plane = E.Plane(df)
    man_sha = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    code_sha = head_sha()
    OUT.mkdir(exist_ok=True)
    recs = []
    for fid, spec in E.FAMILIES.items():
        for ci, cfg in enumerate(spec["configs"]):
            arm = f"{fid}-C{ci + 1}"
            digest = E.config_digest(fid, cfg)
            target = spec["fn"](plane, cfg)
            rec = {
                "cycle_id": "EURUSD-OPEN-SEARCH-V1",
                "trial_id": f"{arm}",
                "family_id": fid,
                "arm_id": arm,
                "config": cfg,
                "config_digest": digest,
                "data_manifest_sha256": man_sha,
                "code_freeze_sha": code_sha,
                "d2": "OWNER_WAIVED_EXPLORATORY",
                "tiers": {},
                "folds": {},
            }
            for k in KS:
                trades, equity = E.run_strategy(plane, target, k)
                fold_metrics = {}
                for f in ("F1", "F2", "F3"):
                    idx = np.array([fold_of(t) == f for t in [tr["exit_ts"] for tr in trades]])
                    sub = [tr for tr, ok in zip(trades, idx) if ok]
                    fold_metrics[f] = E.metrics(sub, np.zeros(len(sub)))
                m_all = E.metrics(trades, equity)
                rec["tiers"][str(k)] = m_all
                if k == 1.0:
                    rec["folds"] = fold_metrics
                if k == 1.0:
                    rec["turnover_trades"] = m_all["trades"]
                    rec["hold_bars_median"] = (
                        float(np.median([tr["hold_bars"] for tr in trades])) if trades else 0
                    )
            g = rec["tiers"]
            gates = {
                "G1": g["1.0"]["net_pips"] > 0,
                "G2": (g["1.0"]["pf"] or 0) >= 1.10,
                "G3": sum(1 for f in rec["folds"].values() if f["net_pips"] > 0) >= 2,
                "G4": g["1.5"]["net_pips"] > 0,
                "G5": g["1.0"]["trades"] >= 30,
            }
            rec["gates"] = gates
            rec["eligible"] = all(gates.values())
            recs.append(rec)
            print(
                f"{arm:12s} net@1.0={g['1.0']['net_pips']:9.1f} net@1.5={g['1.5']['net_pips']:9.1f} "
                f"pf={str(g['1.0']['pf']):7s} trades={g['1.0']['trades']:5d} eligible={rec['eligible']}",
                flush=True,
            )
    with open(OUT / "campaign_dev.jsonl", "w") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")

    nets = [r["tiers"]["1.0"]["net_pips"] for r in recs]
    nets15 = [r["tiers"]["1.5"]["net_pips"] for r in recs]
    summary = {
        "schema": "eosv1.campaign_dev@1",
        "measured_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "code_freeze_sha": code_sha,
        "data_manifest_sha256": man_sha,
        "trials": len(recs),
        "budget_cap": FREEZE["budget_cap"],
        "positive_after_cost_k1": sum(1 for x in nets if x > 0),
        "negative_after_cost_k1": sum(1 for x in nets if x <= 0),
        "positive_at_stress_k15": sum(1 for x in nets15 if x > 0),
        "eligible": sum(1 for r in recs if r["eligible"]),
        "net_k1_pips": {"min": min(nets), "median": float(np.median(nets)), "max": max(nets)},
        "net_k15_pips": {"min": min(nets15), "median": float(np.median(nets15)), "max": max(nets15)},
        "total_trades_k1": sum(r["tiers"]["1.0"]["trades"] for r in recs),
        "per_family_best": {
            fid: max(
                (r for r in recs if r["family_id"] == fid),
                key=lambda r: r["tiers"]["1.5"]["net_pips"],
            )["arm_id"]
            for fid in E.FAMILIES
        },
    }
    (OUT / "dev_distribution.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
