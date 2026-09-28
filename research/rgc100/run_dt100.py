"""DT100 runner. Modes:
  dry     — decision counts, record IDs, distinctness, control parity. NO PnL.
  scored  — full stats + rows jsonl + report (only after owner GO at gate).

Usage: python run_dt100.py --mode dry [--families DT100-01-ORB,...] [--out DIR]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dt100 import config, signals
from dt100.arms import ARMS
from dt100.data import aggregate, load_binance_zipdir, load_fx_pair
from dt100.engine import clock_shadow, run_arm, stale_lag

_D: dict[str, object] = {}


def src(key: str):
    if key in _D:
        return _D[key]
    s = config.SRC
    if key == "btc1m":
        v = load_binance_zipdir(s["btc1m"])
    elif key == "sol1m":
        v = load_binance_zipdir(s["sol1m"])
    elif key == "eth1h":
        v = load_binance_zipdir(s["eth1h"])
    elif key == "sol1h":
        v = load_binance_zipdir(s["sol1h"])
    elif key == "btc1h":
        v = aggregate(load_binance_zipdir(s["btc1m"]), "1h")
    elif key in ("eur", "gbp", "jpy"):
        v = load_fx_pair(s[f"{key}_m1_bid"], s[f"{key}_m1_ask"], config.FX_SCALES[key])
    elif key.startswith("premium_"):
        v = load_binance_zipdir(s[key])
    elif key.startswith("spot_"):
        v = load_binance_zipdir(s[key])
    elif key == "quarterly_btc":
        from dt100.data import load_quarterly_continuous
        v = load_quarterly_continuous(s[key])
    elif key.startswith("funding_"):
        v = load_funding(s[key])
    else:
        raise KeyError(key)
    _D[key] = v
    return v


def load_funding(dirname: str) -> pd.DataFrame:
    files = sorted(Path(dirname).glob("*.zip"))
    frames = []
    for zp in files:
        with zipfile.ZipFile(zp) as z:
            with z.open(z.namelist()[0]) as fh:
                df = pd.read_csv(io.BytesIO(fh.read()), header=None,
                                 names=["calc_time", "interval", "rate"],
                                 low_memory=False)
        if len(df) and not str(df.iloc[0, 0]).isdigit():   # header row present
            with zipfile.ZipFile(zp) as z2:
                blob = z2.read(z2.namelist()[0])
            df = pd.read_csv(io.BytesIO(blob), header=0, low_memory=False)
            df = df.iloc[:, :3]
            df.columns = ["calc_time", "interval", "rate"]
        frames.append(df)
    out = pd.concat(frames, ignore_index=True).drop_duplicates("calc_time")
    out["ts"] = pd.to_datetime(pd.to_numeric(out["calc_time"]), unit="ms", utc=True)
    out["rate"] = pd.to_numeric(out["rate"])
    return out[["ts", "rate"]].sort_values("ts").reset_index(drop=True)


def fund_contra_pos(df_1m: pd.DataFrame, funding: pd.DataFrame, p: dict) -> pd.Series:
    z = (funding["rate"] - funding["rate"].rolling(p["zwin"], min_periods=30).mean()) \
        / funding["rate"].rolling(p["zwin"], min_periods=30).std()
    posf = pd.Series(0.0, index=funding.index)
    posf[z.shift(1) > p["band"]] = -1.0     # extreme positive funding -> short
    posf[z.shift(1) < -p["band"]] = 1.0
    # hold to next settlement: ffill within 8h, then map to the 1m grid
    held = posf.replace(0.0, np.nan).ffill(limit=1).fillna(0.0)
    mapped = pd.merge_asof(df_1m[["ts"]], pd.DataFrame({"ts": funding["ts"], "pos": held}),
                           on="ts", direction="forward")["pos"].fillna(0.0)
    return pd.Series(mapped.to_numpy(), index=df_1m.index)


def build_pos(arm: dict, df):
    kind, p = arm["kind"], arm["params"]
    extra = {k: arm[k] for k in ("lead", "other", "legs", "premium") if k in arm}
    if kind == "fund_contra":
        return fund_contra_pos(df, src("funding_btc"), p)
    if kind == "carry_pair":
        pairdf = signals.carry_pair(df, src(extra["other"]), p).dropna().reset_index(drop=True)
        pos = pd.Series(0.0, index=pairdf.index)
        pos[pairdf["pz"].shift(1) > p["band"]] = 1.0    # perp rich -> long spread
        pos[pairdf["pz"].shift(1) < -p["band"]] = -1.0
        out = pd.Series(0.0, index=pairdf.index)
        for i in np.flatnonzero(pos.to_numpy() != 0):
            out.iloc[i + 1:i + 1 + p["hold"]] = pos.iloc[i]
        synth = pd.DataFrame({"ts": pairdf["ts"], "o": pairdf["spread"].shift(1),
                              "h": pairdf["spread"], "l": pairdf["spread"],
                              "c": pairdf["spread"]}).dropna().reset_index(drop=True)
        return ("SYNTH", synth, out.iloc[1:].reset_index(drop=True))
    if kind == "basis_term":
        pairdf = signals.basis_term(df, src(extra["other"]), src(extra["premium"]), p)
        pairdf = pairdf.dropna().reset_index(drop=True)
        pos = pd.Series(0.0, index=pairdf.index)
        pos[pairdf["dz"].shift(1) > p["band"]] = -1.0   # term rich -> short spread
        pos[pairdf["dz"].shift(1) < -p["band"]] = 1.0
        out = pd.Series(0.0, index=pairdf.index)
        for i in np.flatnonzero(pos.to_numpy() != 0):
            out.iloc[i + 1:i + 1 + p["hold"]] = pos.iloc[i]
        # PnL marks on the TRADEABLE level spread (log quarterly - log perp),
        # never on the z-score; dz is only the trigger.
        synth = pd.DataFrame({"ts": pairdf["ts"], "o": pairdf["spread"].shift(1),
                              "h": pairdf["spread"], "l": pairdf["spread"],
                              "c": pairdf["spread"]}).dropna().reset_index(drop=True)
        return ("SYNTH", synth, out.iloc[1:].reset_index(drop=True))
    fn = getattr(signals, kind)
    if kind == "leadlag":
        ll = signals.leadlag(src(extra["lead"]), df, p)
        synth = ll[["ts", "o", "h", "l", "c"]]
        return ("SYNTH", synth, ll["pos"])
    if kind in ("pair_mr",):
        pairdf = signals.pair_mr(df, src(extra["other"]), p).dropna().reset_index(drop=True)
        z = pairdf["z"]
        pos = pd.Series(0.0, index=pairdf.index)
        pos[z.shift(1) > p["band"]] = -1.0
        pos[z.shift(1) < -p["band"]] = 1.0
        out = pd.Series(0.0, index=pairdf.index)
        for i in np.flatnonzero(pos.to_numpy() != 0):
            out.iloc[i + 1:i + 1 + p["hold"]] = pos.iloc[i]
        synth = pd.DataFrame({"ts": pairdf["ts"], "o": pairdf["spread"].shift(1),
                              "h": pairdf["spread"], "l": pairdf["spread"],
                              "c": pairdf["spread"]}).iloc[1:].reset_index(drop=True)
        return ("SYNTH", synth, out.iloc[1:].reset_index(drop=True))
    if kind == "corr_break":
        cb = signals.corr_break(df, src(extra["other"]), p)
        return ("SYNTH", cb[["ts", "o", "h", "l", "c"]], cb["pos"])
    return fn(df, p)


def digest_bytes(arr) -> str:
    return hashlib.sha256(np.ascontiguousarray(arr.astype(float)).tobytes()).hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["dry", "scored"], required=True)
    ap.add_argument("--families", default="")
    ap.add_argument("--out", default=None)
    ap.add_argument("--stress", type=float, default=1.0)
    ap.add_argument("--stress-all", action="store_true",
                    help="scored mode: run x1.0/x1.5/x2.0 in one data pass")
    args = ap.parse_args()
    want = set(filter(None, args.families.split(",")))
    out = Path(args.out or (Path(config.WT) / "research/control/DAYTRADER-100-V1"
                            / ("dry_run" if args.mode == "dry" else "scored")))
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for fam in ARMS:
        if want and fam["family"] not in want:
            continue
        for arm_name in ("anchor", "n1", "n2"):
            spec = fam[arm_name]
            rid = f"{fam['family']}::{arm_name}::{digest_bytes(np.frombuffer(json.dumps(spec['params'], sort_keys=True).encode(), dtype=np.uint8))}"
            try:
                df = src(spec["source"])
                built = build_pos(spec, df)
                if isinstance(built, tuple):
                    _, mark_df, pos = built
                else:
                    mark_df, pos = df, built
                folds = config.CRYPTO_FOLDS if fam["asset"] == "crypto" else config.FX_FOLDS
                warmup = config.CRYPTO_WARMUP[1] if fam["asset"] == "crypto" else config.FX_WARMUP[1]
                funding = None
                if fam["family"] in ("DT100-C1-FORECASTFUND", "DT100-35-FUNDCONTRA",
                                     "DT100-46-CARRY", "DT100-95-BASISTERM"):
                    funding = src("funding_btc")
                legs = spec.get("legs", 1)
                # dir=+1 on the synthetic spread = SHORT the perp leg for both
                # CARRY and BASISTERM -> funding is INCOME on that leg (A7 HIGH-1)
                fsign = -1.0 if fam["family"] in ("DT100-46-CARRY",
                                                  "DT100-95-BASISTERM") else 1.0
                run_kwargs = dict(folds=folds, asset=fam["asset"], symbol=fam["symbol"],
                                  warmup_end=warmup, funding=funding,
                                  cost_multiplier=float(legs), funding_sign=fsign,
                                  spread_marking=fam["family"] in (
                                      "DT100-46-CARRY", "DT100-75-PAIRMR",
                                      "DT100-79-ETHBTC", "DT100-95-BASISTERM"))
                if args.mode == "dry":
                    stats = run_arm(mark_df, pos, stress=args.stress, **run_kwargs)
                    per_fold_counts = {k: v.get("n", 0) for k, v in stats.get("per_fold", {}).items()}
                    cs = clock_shadow(pos, mark_df["ts"])
                    # parity invariant = FIRED-BAR count preserved (trade counts
                    # legitimately differ when permuted directions merge/split)
                    parity = int((cs != 0).sum()) == int((pos != 0).sum())
                    rows.append({
                        "record_id": rid, "family": fam["family"], "arm": arm_name,
                        "trades_total": stats.get("trades", 0),
                        "trades_per_fold": per_fold_counts,
                        "decision_digest": digest_bytes(pos.to_numpy()),
                        "fired_bars": int((pos != 0).sum()),
                        "clock_shadow_fired_bars": int((cs != 0).sum()),
                        "controls_parity": parity,
                        "non_vacuous": stats.get("trades", 0) >= 50,
                        "mode": "dry (NO PnL computed)",
                    })
                else:
                    for s in ([1.0, 1.5, 2.0] if args.stress_all else [args.stress]):
                        stats = run_arm(mark_df, pos, stress=s, **run_kwargs)
                        rows.append({"record_id": rid, "family": fam["family"],
                                     "arm": arm_name, "stress": s,
                                     "disclosure": config.DISCLOSURE, **stats})
            except FileNotFoundError as e:
                rows.append({"record_id": rid, "family": fam["family"], "arm": arm_name,
                             "verdict": "NOT_RUN_DATA_BLOCKED_UNDER_OWNER_ORDER",
                             "detail": str(e)[:160], "mode": args.mode})
            except Exception as e:  # noqa: BLE001 — loud TECHABORT row, never silent
                rows.append({"record_id": rid, "family": fam["family"], "arm": arm_name,
                             "verdict": "TECHABORT", "detail": f"{type(e).__name__}: {e}"[:200],
                             "mode": args.mode})
    ids = [r["record_id"] for r in rows]
    dup = len(ids) != len(set(ids))
    payload = {"rows": rows, "record_ids_distinct": not dup, "n_rows": len(rows)}
    dest = out / f"dt100_{args.mode}_stress{args.stress}.json"
    dest.write_text(json.dumps(payload, indent=1, default=str))
    print(json.dumps({"dest": str(dest), "n_rows": len(rows),
                      "record_ids_distinct": not dup,
                      "not_run_blocked": sum(1 for r in rows if "verdict" in r),
                      "non_vacuous_fail": sum(1 for r in rows if not r.get("non_vacuous", True)),
                      "parity_fail": sum(1 for r in rows if not r.get("controls_parity", True))}))


if __name__ == "__main__":
    main()
