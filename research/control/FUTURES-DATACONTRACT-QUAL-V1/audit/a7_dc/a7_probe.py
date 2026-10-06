"""A7-DC independent recompute probes (fresh-context auditor).

Reruns, from raw bytes, a subset of DC-VERIFY checks + NQ-2020 remeasure claims.
Read-only on all data roots and on FUTURES-DEEPRESEARCH-V2-20261003 artifacts.
Writes nothing outside audit/a7_dc/.
"""
import glob
import hashlib
import json
import os

import numpy as np
import pandas as pd

NP = "/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms/normalized"
VEND = "/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet"
OUT = {}

# ---------------------------------------------------------------- R1 path law
print("=== R1: PATH LAW ===")
paths = {
    "/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim": None,
    "/Users/hoangminhlong/.my-quantitative-data/futures-databento-av1trim": None,
    "/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms": None,
    "/Users/hoangminhlong/.my-quantitative-data/futures-10syms-v1/raw": None,
}
for p in paths:
    paths[p] = "EXISTS" if os.path.exists(p) else "MISSING"
    print(f"  {p}: {paths[p]}")
n_pq = len(glob.glob("/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet/*/*.parquet"))
print(f"  parquet files under physical root: {n_pq}")
OUT["R1_path_law"] = dict(paths, parquet_count=n_pq)

# ------------------------------------------------- R2 MOF tidy + CFTC sha256
print("\n=== R2: MOF tidy + CFTC fixed-tidy sha256 (raw bytes) ===")
mof = pd.read_parquet(f"{NP}/mof_intervention_tidy.parquet")
row = mof[mof.observation_period.astype(str).str.startswith("2022-10-24")]
bak = pd.read_parquet(f"{NP}/mof_intervention_tidy.parquet.bak_81rows_20261003")
c = f"{NP}/cftc_legacy_tidy.parquet"
sha = hashlib.sha256(open(c, "rb").read()).hexdigest()
cbak = f"{NP}/cftc_legacy_tidy.parquet.bak_prefix_mixed_20261003"
shabak = hashlib.sha256(open(cbak, "rb").read()).hexdigest()
crows = pd.read_parquet(c, columns=["series_id"]).shape[0]
cbakrows = pd.read_parquet(cbak, columns=["series_id"]).shape[0]
print(f"  MOF rows={len(mof)} range={mof.observation_period.min()}..{mof.observation_period.max()}")
print(f"  2022-10-24 row: value_yen_100m={row.value_yen_100m.iloc[0]} direction={row.direction.iloc[0]}")
print(f"  bak rows={len(bak)}")
print(f"  cftc sha256={sha}")
print(f"  cftc rows={crows}  bak rows={cbakrows} bak sha[:16]={shabak[:16]}")
OUT["R2_mof_cftc"] = {
    "mof_rows": int(len(mof)),
    "mof_range": [str(mof.observation_period.min()), str(mof.observation_period.max())],
    "mof_2022_10_24": {"value_yen_100m": float(row.value_yen_100m.iloc[0]),
                       "direction": str(row.direction.iloc[0])},
    "mof_bak_rows": int(len(bak)),
    "cftc_sha256": sha,
    "cftc_sha_prefix_match_f7a2719e745c2f6f": sha.startswith("f7a2719e745c2f6f"),
    "cftc_rows": int(crows),
    "cftc_bak_rows": int(cbakrows),
    "cftc_bak_sha16": shabak[:16],
}

# ------------------------------------------------- R5 NQ March-2020 recompute
print("\n=== R5: NQ 2020-03 session closes / returns recomputed from raw vendor bytes ===")
f = f"{VEND}/AV1R-O1M-NQ-DELTA/AV1R-O1M-NQ-DELTA__2018-06-01_2020-06-01.parquet"
cols = ["instrument_id", "ts_event", "raw_symbol", "close", "volume"]
df = pd.read_parquet(f, columns=cols)
df = df[df.ts_event >= int(pd.Timestamp("2020-02-28", tz="UTC").value)]  # ns epoch
df["dt"] = pd.to_datetime(df["ts_event"], unit="ns", utc=True)
loc = df["dt"].dt.tz_convert("America/Chicago")
hhmm = loc.dt.hour * 60 + loc.dt.minute
sess = loc.dt.normalize().dt.tz_localize(None)
df["session_date"] = (sess + pd.to_timedelta((loc.dt.hour >= 17).astype(int), unit="D")).dt.date
df = df[(hhmm < 16 * 60) | (hhmm >= 17 * 60)]  # drop 16:00-17:00 break bucket

g = df.groupby(["raw_symbol", "session_date"]).agg(
    close=("close", "last"), volume=("volume", "sum")).reset_index()
nqh = g[g.raw_symbol == "NQH0"].set_index("session_date")
alias = df[df.instrument_id == 16908]
ga = alias.groupby("session_date").agg(close=("close", "last"), volume=("volume", "sum"))

mar = pd.date_range("2020-03-09", "2020-03-24").date
rows = []
for d in mar:
    r = {"session": str(d)}
    if d in nqh.index:
        r["NQH0_close"] = round(float(nqh.loc[d, "close"]) / 1e9, 2)
        r["NQH0_vol"] = int(nqh.loc[d, "volume"])
    if d in ga.index:
        r["NQM0_id16908_close"] = round(float(ga.loc[d, "close"]) / 1e9, 2)
        r["NQM0_id16908_vol"] = int(ga.loc[d, "volume"])
    rows.append(r)
tbl = pd.DataFrame(rows)
print(tbl.to_string(index=False))

# OLD-view NQH0 daily log rets
old = (nqh.close / 1e9).astype(float).sort_index()
oldr = (np.log(old).diff() * 100).round(4)
print("\n  OLD-view NQH0 daily log rets (%):")
show = [pd.Timestamp(x).date() for x in
        ["2020-03-10", "2020-03-11", "2020-03-12", "2020-03-13", "2020-03-16",
         "2020-03-17", "2020-03-18", "2020-03-19", "2020-03-20"]]
print(oldr.loc[show].to_string())

# NEW-view: held NQM0(id16908) at 03-19/03-20 per the remeasure held map
newser = old.copy()
for d in ["2020-03-19", "2020-03-20"]:
    td = pd.Timestamp(d).date()
    newser.loc[td] = float(ga.loc[td, "close"]) / 1e9
newr = (np.log(newser).diff() * 100).round(4)
print("\n  NEW-view rets at the roll: 03-19 = %.4f%%, 03-20 = %.4f%%" % (
    newr.loc[pd.Timestamp("2020-03-19").date()], newr.loc[pd.Timestamp("2020-03-20").date()]))
print("  (remeasure JSON claims ret_0319_new=-1.0350, ret_0320_new=-3.7509)")

# k=5 trail5 means at close of 03-18 vs 03-19 (which close fired the switch?)
for end in ["2020-03-18", "2020-03-19"]:
    e = pd.Timestamp(end).date()
    w = pd.date_range(pd.Timestamp(end) - pd.Timedelta(days=14), end).date
    av = ga.loc[[x for x in w if x in ga.index], "volume"]
    hv = nqh.loc[[x for x in w if x in nqh.index], "volume"].tail(5)
    av5 = av.tail(5)
    print(f"  trail5 ending {end}: NQM0(16908) mean={av5.mean():,.0f} (n={len(av5)}) | "
          f"NQH0 mean={hv.mean():,.0f} (n={len(hv)})")

OUT["R5_nq_march2020"] = {
    "per_session": rows,
    "old_view_rets_pct": {str(k): float(v) for k, v in oldr.loc[show].items()},
    "new_view_ret_0319": float(newr.loc[pd.Timestamp("2020-03-19").date()]),
    "new_view_ret_0320": float(newr.loc[pd.Timestamp("2020-03-20").date()]),
}

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "a7_probe_r1_r2_r5.json"), "w") as fh:
    json.dump(OUT, fh, indent=1, default=str)
print("\nwrote a7_probe_r1_r2_r5.json")
