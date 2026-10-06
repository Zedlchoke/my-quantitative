"""NQ-ALIAS-REPAIR Task 2 — v3 rebuild of the full-era NQ chain with the
ERRATUM-F1 alias view rule. Adapted from the baseline NQ_build_cache.py
(FUTURES-DEEPRESEARCH-V2-20261003) — copy-and-modify; the baseline caches are
never written.

Stages (run one per process to keep each command short):
  panel    load raw (13 files, chunk-per-file) + relabel view + drop remaining
           dash rows -> cache_v3/nq_outright_1m_v3.parquet
  annotate contract registry + annotation + session table (baseline logic,
           unchanged) -> nq_annotated_1m_v3.parquet, contract_registry_v3.json,
           nq_sessions_v3.parquet
  held     held chains: plain k=5 (baseline rule, unchanged) + k=5 EXPLICIT
           cease-guard variant; held daily right-merge
           -> held_volume_k5_v3.parquet, held_volume_k5_cg_v3.parquet,
              nq_held_daily_v3.parquet
  all      panel -> annotate -> held

NO PnL, NO strategy metrics; coverage/volume/roll descriptive only.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nq_deep_lib_v3 as L  # noqa: E402

CACHE = L.CACHE
STATS = os.path.join(CACHE, "rebuild_stats.json")


def stage_panel() -> None:
    os.makedirs(CACHE, exist_ok=True)
    print("loading raw with ERRATUM-F1 view rule ...", flush=True)
    df, stats = L.load_outright_1m_v3()
    print(f"rows={len(df):,} span {df['dt'].min()} .. {df['dt'].max()}")
    print("relabel stats:", stats)
    df.to_parquet(os.path.join(CACHE, "nq_outright_1m_v3.parquet"), index=False)
    import json
    prev = {}
    if os.path.exists(STATS):
        prev = json.load(open(STATS))
    prev["panel"] = stats
    prev["panel"]["rows_out"] = int(len(df))
    prev["panel"]["ts_min_utc"] = str(df["dt"].min())
    prev["panel"]["ts_max_utc"] = str(df["dt"].max())
    with open(STATS, "w") as fh:
        json.dump(prev, fh, indent=1)
    print("panel stage complete")


def stage_annotate() -> None:
    df = pd.read_parquet(os.path.join(CACHE, "nq_outright_1m_v3.parquet"))
    print(f"panel rows={len(df):,}")
    print("building contract registry ...", flush=True)
    reg = L.build_contract_registry(df)
    print(f"contracts={len(reg)}")
    multi = reg.groupby("contract").size()
    if (multi > 1).any():
        print("contract keys spanning multiple clusters (expected for NQM0_2020):")
        print(multi[multi > 1].to_string())
    print("annotating panel ...", flush=True)
    df = L.annotate_panel(df, reg)
    n_break = int(df["in_break"].sum())
    n_wknd = int(df["weekend_anomaly"].sum())
    print(f"break bars={n_break} weekend-anomaly bars={n_wknd}")
    df.to_parquet(os.path.join(CACHE, "nq_annotated_1m_v3.parquet"), index=False)

    print("session table (vectorized, baseline logic) ...", flush=True)
    df = df[~df["in_break"]].copy()
    df = df.sort_values(["contract", "dt"]).reset_index(drop=True)
    g = df.groupby(["contract", "session_date"], sort=True)
    sess = g.agg(
        open=("open", "first"), high=("high", "max"), low=("low", "min"),
        close=("close", "last"), volume=("volume", "sum"), n_bars=("dt", "size"),
        first_min=("minute_of_day", "first"), last_min=("minute_of_day", "last"),
    ).reset_index()
    rth = df[df["in_rth"]]
    rg = rth.groupby(["contract", "session_date"], sort=True)
    rth_agg = rg.agg(
        rth_volume=("volume", "sum"), rth_bars=("dt", "size"),
        rth_first_min=("minute_of_day", "first"),
        rth_last_min=("minute_of_day", "last")).reset_index()
    sess = sess.merge(rth_agg, on=["contract", "session_date"], how="left")
    rthx = df[df["in_rth_ext"]]
    xg = rthx.groupby(["contract", "session_date"], sort=True)
    xagg = xg.agg(rthx_volume=("volume", "sum"),
                  rthx_bars=("dt", "size")).reset_index()
    sess = sess.merge(xagg, on=["contract", "session_date"], how="left")
    segv = df.groupby(["contract", "session_date", "segment"], sort=True)[
        "volume"].sum().unstack(fill_value=0)
    segr = df.groupby(["contract", "session_date", "segment"], sort=True).agg(
        hi=("high", "max"), lo=("low", "min"))
    segr_range = (segr["hi"] - segr["lo"]).unstack()
    mi = pd.MultiIndex.from_frame(sess[["contract", "session_date"]])
    segv = segv.reindex(mi, fill_value=0)
    segr_range = segr_range.reindex(mi)
    for name, _a, _b in L.SEGMENTS:
        sess[f"vol_{name}"] = segv[name].values if name in segv.columns else 0
        if name in segr_range.columns:
            sess[f"rng_{name}"] = segr_range[name].values
        else:
            sess[f"rng_{name}"] = np.nan
    sess = sess.sort_values(["contract", "session_date"]).reset_index(drop=True)
    sess["prev_close"] = sess.groupby("contract")["close"].shift(1)
    tr_hi = (sess["high"] - sess["prev_close"]).clip(lower=0)
    tr_lo = (sess["prev_close"] - sess["low"]).clip(lower=0)
    sess["true_range"] = pd.concat(
        [tr_hi, tr_lo, sess["high"] - sess["low"]], axis=1).max(axis=1)
    sess["rth_coverage"] = sess["rth_bars"].fillna(0) / L.RTH_MIN
    sess.to_parquet(os.path.join(CACHE, "nq_sessions_v3.parquet"), index=False)
    print(f"session rows={len(sess):,} contracts={sess['contract'].nunique()}")

    reg_out = reg.copy()
    reg_out["first_bar"] = reg_out["first_bar"].astype(str)
    reg_out["last_bar"] = reg_out["last_bar"].astype(str)
    reg_out["expiry_ts"] = reg_out["expiry_ts"].astype(str)
    reg_out.to_json(os.path.join(CACHE, "contract_registry_v3.json"),
                    orient="records", indent=1)
    import json
    prev = {}
    if os.path.exists(STATS):
        prev = json.load(open(STATS))
    prev["annotate"] = {
        "contracts": int(len(reg)),
        "session_rows": int(len(sess)),
        "session_contracts": int(sess["contract"].nunique()),
        "break_bars": n_break, "weekend_anomaly_bars": n_wknd,
        "multi_cluster_contracts": {str(k): int(v) for k, v in
                                    multi[multi > 1].items()},
    }
    with open(STATS, "w") as fh:
        json.dump(prev, fh, indent=1)
    print("annotate stage complete")


def stage_held() -> None:
    import json
    sess = pd.read_parquet(os.path.join(CACHE, "nq_sessions_v3.parquet"))
    held = L.front_by_volume_crossover(sess, k=5)
    held.to_parquet(os.path.join(CACHE, "held_volume_k5_v3.parquet"), index=False)
    n_rolls = int((held["held"] != held["held"].shift()).sum() - 1)
    ces = L.cessation_by_bars(sess)
    held_cg = L.front_by_volume_crossover_cg(sess, k=5, cessation=ces)
    held_cg.attrs  # noqa: B018  (guards_fired read below via attrs)
    guards = held_cg.attrs.get("guards_fired")
    held_cg = pd.DataFrame(held_cg)
    held_cg.to_parquet(os.path.join(CACHE, "held_volume_k5_cg_v3.parquet"),
                       index=False)
    print(f"plain k=5: sessions={len(held):,} rolls={n_rolls}")
    print(f"cg    k=5: sessions={len(held_cg):,} "
          f"rolls={int((held_cg['held'] != held_cg['held'].shift()).sum() - 1)} "
          f"cease_guards_fired={guards}")

    # held daily (right merge — sessions without held-contract bars keep NaN,
    # baseline held_daily() construction from NQ_a1_regimes.py)
    m = sess.merge(held.rename(columns={"held": "contract"}),
                   on=["session_date", "contract"], how="right")
    m = m.sort_values("session_date").reset_index(drop=True)
    m["d"] = pd.to_datetime(m["session_date"])
    m["log_close"] = np.log(m["close"].astype(float))
    m["ret"] = m["log_close"].diff()
    m["cov"] = m["rth_coverage"].clip(0, 1).fillna(0.0)
    m["depleted"] = (m["cov"] < 0.25) | m["close"].isna()
    keep = ["d", "session_date", "contract", "open", "high", "low", "close",
            "volume", "n_bars", "rth_coverage", "prev_close", "true_range",
            "log_close", "ret", "cov", "depleted"]
    m[keep].to_parquet(os.path.join(CACHE, "nq_held_daily_v3.parquet"),
                       index=False)
    print(f"held daily rows={len(m):,} "
          f"nan_close={int(m['close'].isna().sum())} "
          f"depleted={int(m['depleted'].sum())}")

    prev = {}
    if os.path.exists(STATS):
        prev = json.load(open(STATS))
    prev["held"] = {
        "plain_k5_rolls": n_rolls,
        "plain_k5_sessions": int(len(held)),
        "cg_k5_rolls": int((held_cg["held"] != held_cg["held"].shift()).sum() - 1),
        "cg_guards_fired": int(guards) if guards is not None else None,
        "held_daily_rows": int(len(m)),
        "held_daily_nan_close": int(m["close"].isna().sum()),
    }
    with open(STATS, "w") as fh:
        json.dump(prev, fh, indent=1)
    print("held stage complete")


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "all"
    if stage in ("panel", "all"):
        stage_panel()
    if stage in ("annotate", "all"):
        stage_annotate()
    if stage in ("held", "all"):
        stage_held()
