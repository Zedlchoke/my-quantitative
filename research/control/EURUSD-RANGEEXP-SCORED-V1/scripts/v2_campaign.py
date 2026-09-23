"""V2 dev campaign (leak-guarded) + family/config registry.

FROZEN registry: FAMILY_V2 below is emitted into selection_freeze_v2.json and
committed BEFORE any outcome is computed. Gates G1-G5 per plan §4 (G2 PF>=1.20).
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
import v2_lib as V

ROOT = HERE.parent
BARS15 = ROOT / "data_local" / "derived" / "bars15.parquet"
MANIFEST = ROOT / "data_local" / "duka" / "m1_manifest.json"
OUT = ROOT / "outcomes"
FREEZE = ROOT / "selection_freeze_v2.json"

HOLDOUT_START = pd.Timestamp("2026-01-01", tz="UTC")
KS = [1.0, 1.5, 2.0]

FAMILY_V2 = {
    "FX2-GAP": {
        "fn": lambda p, c: V.f_gap(p, c["th"], c["mode"]),
        "configs": [
            {"th": 10, "mode": "follow"}, {"th": 20, "mode": "follow"},
            {"th": 10, "mode": "fade"}, {"th": 20, "mode": "fade"},
        ],
    },
    "FX2-PDHLOC": {
        "fn": lambda p, c: V.f_pdhloc(p, c["buf"], c["opposite_exit"]),
        "configs": [
            {"buf": 0.0, "opposite_exit": True}, {"buf": 0.0002, "opposite_exit": True},
            {"buf": 0.0, "opposite_exit": False}, {"buf": 0.0002, "opposite_exit": False},
        ],
    },
    "FX2-DOW": {
        "fn": lambda p, c: V.f_dow_simple(p, c["weeks"], c["min_past"]),
        "configs": [
            {"weeks": 4, "min_past": 8}, {"weeks": 8, "min_past": 8},
            {"weeks": 4, "min_past": 16}, {"weeks": 8, "min_past": 16},
        ],
    },
    "FX2-ASIAFADE": {
        "fn": lambda p, c: V.f_asiafade(p, c["asia_end"], c["buf"]),
        "configs": [
            {"asia_end": 6, "buf": 0.0}, {"asia_end": 7, "buf": 0.0},
            {"asia_end": 6, "buf": 0.0001}, {"asia_end": 7, "buf": 0.0001},
        ],
    },
    "FX2-SESSMA": {
        "fn": lambda p, c: V.f_sessma(p, c["th"], c["atr_n"]),
        "configs": [
            {"th": 1.0, "atr_n": 96}, {"th": 1.5, "atr_n": 96},
            {"th": 1.0, "atr_n": 192}, {"th": 1.5, "atr_n": 192},
        ],
    },
    "FX2-H1TSMOM": {
        "fn": lambda p, c: V.f_h1tsmom(p, c["K"]),
        "configs": [{"K": 24}, {"K": 48}, {"K": 96}, {"K": 168}],
    },
    "FX2-H1DONCH": {
        "fn": lambda p, c: V.f_h1donch(p, c["L"], c["hold_mult"]),
        "configs": [
            {"L": 24, "hold_mult": 4}, {"L": 48, "hold_mult": 4},
            {"L": 96, "hold_mult": 3}, {"L": 168, "hold_mult": 3},
        ],
    },
    "FX2-DAYMOM": {
        "fn": lambda p, c: V.f_daymom(p, c["N"]),
        "configs": [{"N": 2}, {"N": 3}, {"N": 5}, {"N": 10}],
    },
    "FX2-RANGEEXP": {
        "fn": lambda p, c: V.f_rangeexp(p, c["lo_q"], c["hi_q"], c["use_breakout"]),
        "configs": [
            {"lo_q": 0.3, "hi_q": 0.7, "use_breakout": True},
            {"lo_q": 0.25, "hi_q": 0.75, "use_breakout": True},
            {"lo_q": 0.3, "hi_q": 0.7, "use_breakout": False},
            {"lo_q": 0.25, "hi_q": 0.75, "use_breakout": False},
        ],
    },
    "FX2-STOCH": {
        "fn": lambda p, c: V.f_stoch(p, c["N"], c["th_hi"], c["th_lo"]),
        "configs": [
            {"N": 24, "th_hi": 80, "th_lo": 20}, {"N": 24, "th_hi": 85, "th_lo": 15},
            {"N": 48, "th_hi": 80, "th_lo": 20}, {"N": 48, "th_hi": 85, "th_lo": 15},
        ],
    },
    "FX2-ROUNDNUM": {
        "fn": lambda p, c: V.f_roundnum(p, c["grid"], c["prox"]),
        "configs": [
            {"grid": 0.0025, "prox": 0.0003}, {"grid": 0.0050, "prox": 0.0003},
            {"grid": 0.0025, "prox": 0.0005}, {"grid": 0.0050, "prox": 0.0005},
        ],
    },
    "FX2-HOURREV": {
        "fn": lambda p, c: V.f_hourrev(p, c["win_days"], c["invert"]),
        "configs": [
            {"win_days": 40, "invert": True}, {"win_days": 80, "invert": True},
            {"win_days": 120, "invert": True}, {"win_days": 40, "invert": False},
        ],
    },
}


def load_h1_plane():
    """H1 plane over the FULL window (runner slices before outcomes)."""
    h1 = pd.read_parquet(ROOT / "data_local" / "derived" / "bars1h.parquet")
    h1 = h1.reset_index().rename(columns={"ts": "ts"})
    return V.H1Plane(h1)


def fold_of(ts_epoch):
    d = str(dt.datetime.utcfromtimestamp(int(ts_epoch)).date())
    for fid, (a, b) in {
        "F1": ("2022-07-01", "2022-12-31"),
        "F2": ("2023-01-01", "2023-06-30"),
        "F3": ("2023-07-01", "2023-12-31"),
        "F4": ("2024-01-01", "2024-06-30"),
        "F5": ("2024-07-01", "2024-12-31"),
        "F6": ("2025-01-01", "2025-06-30"),
    }.items():
        if a <= d <= b:
            return fid
    return "WARMUP" if d < "2022-07-01" else "POST_DEV"


def emit_freeze():
    fam = {}
    for fid, spec in FAMILY_V2.items():
        fam[fid] = {
            "configs": spec["configs"],
            "config_digests": [E.config_digest(fid, c) for c in spec["configs"]],
        }
    freeze = {
        "schema": "eosv2.selection_freeze@1",
        "cycle_id": "EURUSD-OPEN-SEARCH-V2",
        "frozen_before_any_outcome": True,
        "engine_semantics": "v1 engine (scripts/engine.py sha cc868402e63d unchanged)",
        "engine_sha256": hashlib.sha256(
            (HERE / "engine.py").read_bytes()
        ).hexdigest(),
        "windows": {
            "dev": "2021-01-01..2025-12-31 (V1 holdout demoted to dev; disclosed)",
            "holdout_SEALED": "2026-01-01..2026-06-30 (never touched by any search)",
        },
        "folds": {
            "F1": "2022-07..2022-12", "F2": "2023-01..2023-06",
            "F3": "2023-07..2023-12", "F4": "2024-01..2024-06",
            "F5": "2024-07..2024-12", "F6": "2025-01..2025-06",
        },
        "cost_tiers": {"primary_k": 1.0, "stress_k": 1.5, "reported_k": 2.0},
        "gates": {
            "G1": "net_pips > 0 @k=1.0",
            "G2": "PF >= 1.20 @k=1.0 (raised from V1's 1.10 per observed OOS decay)",
            "G3": ">= 4/6 folds net>0",
            "G4": "net_pips > 0 @k=1.5",
            "G5": "trades >= 30",
        },
        "selection_rule": "eligible = all gates; rank net@1.5; freeze <=2",
        "holdout_SUCCESS_preregistered": "net>0 @1.0 AND net>0 @1.5; ONE look; failure final",
        "families": fam,
        "trial_count": sum(len(v["configs"]) for v in fam.values()),
        "budget_cap": 96,
        "ancestry_disclosure": {
            "FX2-H1TSMOM": "horizon change of V1 FXOS-03 (15m->H1 + skip-mask)",
            "FX2-H1DONCH": "horizon change of V1 FXOS-02",
            "FX2-HOURREV-C4": "non-inverted control = V1 FXOS-24 form at H1",
            "all_others": "new mechanisms (plan §5)",
        },
        "leak_guards": [
            "dev runner loads only bars ts < 2026-01-01",
            "holdout runner loads only bars ts >= 2026-01-01; run_count logged",
        ],
    }
    FREEZE.write_text(json.dumps(freeze, indent=1))
    return freeze


def main():
    if not FREEZE.exists():
        raise SystemExit("FAIL_CLOSED: selection_freeze_v2.json missing — commit the freeze first")
    freeze = json.loads(FREEZE.read_text())
    plane_full = load_h1_plane()
    dev_mask = plane_full.ts < int(HOLDOUT_START.timestamp())
    dev = plane_full
    # physically drop holdout bars from the arrays
    for attr in ("ts", "b_o", "b_h", "b_l", "b_c", "a_o", "a_c", "s_o", "s_c",
                 "hhmm", "day", "hour", "minute", "is_day_close", "fill_ok"):
        arr = getattr(dev, attr)
        setattr(dev, attr, arr[dev_mask])
    dev.skip = dev.skip[dev_mask]
    dev.last_tradable_of_day = dev.last_tradable_of_day[dev_mask]
    if (dev.ts >= int(HOLDOUT_START.timestamp())).any():
        raise SystemExit("FAIL_CLOSED: holdout bars present in dev runner")

    man_sha = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    code_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(HERE), text=True).strip()
    OUT.mkdir(exist_ok=True)
    recs = []
    for fid, spec in FAMILY_V2.items():
        for ci, cfg in enumerate(spec["configs"]):
            arm = f"{fid}-C{ci + 1}"
            target = spec["fn"](dev, cfg)
            rec = {
                "cycle_id": "EURUSD-OPEN-SEARCH-V2", "trial_id": arm,
                "family_id": fid, "arm_id": arm, "config": cfg,
                "config_digest": E.config_digest(fid, cfg),
                "data_manifest_sha256": man_sha, "code_freeze_sha": code_sha,
                "d2": "OWNER_WAIVED_EXPLORATORY", "tiers": {}, "folds": {},
            }
            for k in KS:
                trades, equity = E.run_strategy(dev, target, k)
                rec["tiers"][str(k)] = E.metrics(trades, equity)
                if k == 1.0:
                    rec["turnover_trades"] = len(trades)
                    fm = {}
                    for f in ("F1", "F2", "F3", "F4", "F5", "F6"):
                        sub = [t for t in trades if fold_of(t["exit_ts"]) == f]
                        fm[f] = E.metrics(sub, np.zeros(len(sub)))
                    rec["folds"] = fm
            g1 = rec["tiers"]["1.0"]; g15 = rec["tiers"]["1.5"]
            gates = {
                "G1": g1["net_pips"] > 0,
                "G2": (g1["pf"] or 0) >= 1.20,
                "G3": sum(1 for f in rec["folds"].values() if f["net_pips"] > 0) >= 4,
                "G4": g15["net_pips"] > 0,
                "G5": g1["trades"] >= 30,
            }
            rec["gates"] = gates
            rec["eligible"] = all(gates.values())
            recs.append(rec)
            print(f"{arm:16s} net@1.0={g1['net_pips']:9.1f} net@1.5={g15['net_pips']:9.1f} "
                  f"pf={str(g1['pf']):7s} tr={g1['trades']:5d} elig={rec['eligible']}", flush=True)
    with open(OUT / "campaign_dev_v2.jsonl", "w") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")
    nets = [r["tiers"]["1.0"]["net_pips"] for r in recs]
    nets15 = [r["tiers"]["1.5"]["net_pips"] for r in recs]
    summary = {
        "schema": "eosv2.campaign_dev@1",
        "measured_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "code_freeze_sha": code_sha, "data_manifest_sha256": man_sha,
        "trials": len(recs), "budget_cap": freeze["budget_cap"],
        "positive_after_cost_k1": sum(1 for x in nets if x > 0),
        "positive_at_stress_k15": sum(1 for x in nets15 if x > 0),
        "eligible": sum(1 for r in recs if r["eligible"]),
        "net_k1_pips": {"min": min(nets), "median": float(np.median(nets)), "max": max(nets)},
        "net_k15_pips": {"min": min(nets15), "median": float(np.median(nets15)), "max": max(nets15)},
        "total_trades_k1": sum(r["tiers"]["1.0"]["trades"] for r in recs),
    }
    (OUT / "dev_distribution_v2.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
