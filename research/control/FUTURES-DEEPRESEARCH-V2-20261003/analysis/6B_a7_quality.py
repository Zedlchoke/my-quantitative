"""6B v2 a7 — data-quality ledger per era: FX-BACKFILL2 2020-22 vs AV1R
2022-2026.04 vs AV1T 2026.04-10; butt joints, OHLC sanity, DST days,
session completeness, stray inventory. Emits 6B_a7_quality.json."""
from __future__ import annotations

import glob
import importlib.util
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "six_b_deep_lib", os.path.join(HERE, "6B_deep_lib.py"))
lib = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lib)

OUT = {"eras": {}, "global": {}}

# raw re-read per era (all symbols incl. spreads for the ledger)
eras = [
    ("backfill_2020_2022", "AV1B-O1M-6B-BACKFILL2"),
    ("main_2022_2026_04", "AV1R-O1M-6B-BACKFILL"),
    ("recent_2026_04_10", "AV1T-O1M-6B"),
]
frames = {}
for name, pat in eras:
    files = sorted(glob.glob(f"{lib.DATA_ROOT}/parquet/{pat}/*.parquet"))
    d = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    d["dt"] = pd.to_datetime(d["ts_event"], unit="ns", utc=True)
    frames[name] = d
    spread = d[d["raw_symbol"].str.contains("-")]
    outr = d[~d["raw_symbol"].str.contains("-")]
    q = outr[outr["raw_symbol"].str.fullmatch(r"6B[HMUZ]\d")]
    bad_ohlc = int(((outr["high"] < outr["low"]) | (outr["high"] < outr["open"])
                    | (outr["high"] < outr["close"]) | (outr["low"] > outr["open"])
                    | (outr["low"] > outr["close"])).sum())
    OUT["eras"][name] = {
        "files": [os.path.basename(f) for f in files],
        "rows_total": int(len(d)),
        "rows_spread_instruments": int(len(spread)),
        "rows_outright": int(len(outr)),
        "rows_quarterly_outright": int(len(q)),
        "volume_spread_instruments": int(spread["volume"].sum()),
        "volume_outright": int(outr["volume"].sum()),
        "zero_volume_bars_outright": int((outr["volume"] == 0).sum()),
        "ohlc_violations": bad_ohlc,
        "negative_price_bars_outright": int((outr["close"] <= 0).sum()),
        "duplicate_key_rows": int(d.duplicated(
            subset=["instrument_id", "ts_event"]).sum()),
        "span": [str(d["dt"].min()), str(d["dt"].max())],
    }

# ---- butt joints: overlap/continuity ------------------------------------------
joints = {}
for a, b, jdate in [("backfill_2020_2022", "main_2022_2026_04", "2022-01-01"),
                    ("main_2022_2022", "recent_2026_04_10", "2026-04-01")]:
    pass
for a, b, jdate in [("backfill_2020_2022", "main_2022_2026_04", "2022-01-01"),
                    ("main_2022_2026_04", "recent_2026_04_10", "2026-04-01")]:
    jt = pd.Timestamp(jdate, tz="UTC")
    da, db = frames[a], frames[b]
    win_a = da[(da["dt"] >= jt - pd.Timedelta(days=3))
               & (da["dt"] < jt + pd.Timedelta(days=3))]
    win_b = db[(db["dt"] >= jt - pd.Timedelta(days=3))
               & (db["dt"] < jt + pd.Timedelta(days=3))]
    key_a = set(zip(win_a["instrument_id"], win_a["ts_event"]))
    key_b = set(zip(win_b["instrument_id"], win_b["ts_event"]))
    # price continuity on the front quarterly around the joint
    front_sym = {"2022-01-01": "6BH2", "2026-04-01": "6BM6"}[jdate]
    fa = da[(da["raw_symbol"] == front_sym) & (da["dt"] < jt)]
    fb = db[(db["raw_symbol"] == front_sym) & (db["dt"] >= jt)]
    gap_pct = None
    if len(fa) and len(fb):
        gap_pct = float((fb["open"].iloc[0] - fa["close"].iloc[-1])
                        / fa["close"].iloc[-1] * 100)
    joints[jdate] = {
        "rows_within_3d": {"left": int(len(win_a)), "right": int(len(win_b))},
        "exact_duplicate_keys_across_joint": len(key_a & key_b),
        f"front_{front_sym}_close_to_open_gap_pct_across_joint": gap_pct,
    }
OUT["butt_joints"] = joints

# ---- session completeness vs weekdays -----------------------------------------
sess = pd.read_parquet(os.path.join(lib.CACHE, "6b_sessions.parquet"))
held = pd.read_parquet(os.path.join(lib.CACHE, "held_calendar.parquet"))
m = sess.merge(held, on="session_date")
m = m[m["contract"] == m["held"]]
m["d"] = pd.to_datetime(m["session_date"])
m = m.sort_values("d")
m["era"] = np.where(m["d"] < "2022-01-01", "backfill_2020_2022",
                    np.where(m["d"] < "2026-04-01", "main_2022_2026_04",
                             "recent_2026_04_10"))
for era, g in m.groupby("era"):
    weekdays = pd.date_range(g["d"].min(), g["d"].max(), freq="B")
    actual = set(g["d"])
    missing = [str(x.date()) for x in weekdays if x not in actual]
    OUT["eras"][era]["sessions_held_chain"] = int(g["d"].nunique())
    OUT["eras"][era]["weekdays_expected"] = int(len(weekdays))
    OUT["eras"][era]["missing_weekday_sessions_sample"] = missing[:12]
    OUT["eras"][era]["n_missing_weekdays"] = len(missing)
    OUT["eras"][era]["median_bars_per_session"] = float(g["n_bars"].median())
    OUT["eras"][era]["sessions_below_600_bars"] = int((g["n_bars"] < 600).sum())

# ---- DST transition sessions ---------------------------------------------------
for day in ["2021-03-14", "2021-11-07", "2022-03-13", "2022-11-06",
            "2023-03-12", "2023-11-05", "2024-03-10", "2024-11-03",
            "2025-03-09", "2025-11-02"]:
    # session date = transition Sunday's Monday (session opens Sun 17:00 CT)
    sd = (pd.Timestamp(day) + pd.Timedelta(days=1)).date()
    row = m[m["d"] == pd.Timestamp(sd)]
    if len(row):
        OUT.setdefault("dst_transition_sessions", {})[str(sd)] = {
            "bars": int(row["n_bars"].iloc[0]),
            "note": "US DST switch inside session (23h/25h CT day)",
        }

# ---- stray inventory summary ----------------------------------------------------
reg = lib.build_contract_registry(
    pd.read_parquet(os.path.join(lib.CACHE, "6b_outright_1m.parquet")))
s = reg[reg["stray"]]
OUT["global"]["stray_clusters"] = {
    "n": int(len(s)), "bars": int(s["n_bars"].sum()), "volume": int(s["volume"].sum()),
    "by_reason": {k: int(v) for k, v in s.groupby("stray_reason").size().items()},
    "detail": [
        {"symbol": r["symbol"], "reason": r["stray_reason"],
         "n_bars": int(r["n_bars"]), "volume": int(r["volume"]),
         "first": str(r["first_bar"]), "last": str(r["last_bar"])}
        for _, r in s.iterrows() if r["stray_reason"] != "serial_or_foreign_symbol"],
}
OUT["global"]["serial_contracts_excluded_by_design"] = {
    "n_clusters": int((s["stray_reason"] == "serial_or_foreign_symbol").sum()),
    "bars": int(s.loc[s["stray_reason"] == "serial_or_foreign_symbol", "n_bars"].sum()),
    "volume": int(s.loc[s["stray_reason"] == "serial_or_foreign_symbol", "volume"].sum()),
    "share_of_outright_volume_pct": float(
        s.loc[s["stray_reason"] == "serial_or_foreign_symbol", "volume"].sum()
        / pd.read_parquet(os.path.join(lib.CACHE, "6b_outright_1m.parquet"),
                          columns=["volume"])["volume"].sum() * 100),
}
# min tick from definitions (primary-source adjudication of v1 conflict)
defs = lib.load_definitions_6b()
OUT["global"]["min_price_increment_definitions"] = {
    "raw_fixed9": sorted(defs["min_price_increment"].unique().tolist()),
    "usd": sorted((defs["min_price_increment"].unique() / 1e9).tolist()),
    "n_instruments": int(len(defs)),
}
# weekend anomaly bars
df_ann = pd.read_parquet(os.path.join(lib.CACHE, "6b_annotated_1m.parquet"))
OUT["global"]["weekend_anomaly_bars"] = int(df_ann["weekend_anomaly"].sum())
OUT["global"]["bars_in_maintenance_break"] = int(df_ann["in_break"].sum())

lib.jdump(OUT, os.path.join(HERE, "6B_a7_quality.json"))
print("a7 done.")
for k, v in OUT["eras"].items():
    print(k, {kk: v[kk] for kk in ("rows_outright", "ohlc_violations",
                                   "duplicate_key_rows", "n_missing_weekdays",
                                   "median_bars_per_session")})
print("joints:", {k: {kk: vv for kk, vv in v.items() if "gap" in kk or "duplicate" in kk}
                  for k, v in OUT["butt_joints"].items()})
