#!/usr/bin/env python
"""A7-DEEP-ES audit R1: INDEPENDENT recompute of roll/term-structure headline
numbers straight from the vendor parquet (no ES_cache, no lane code reuse).

Checks (dossier sec 0.1/0.3/0.4, sec 4):
  - 66 completed rolls; volume crossover 3-5 sessions before expiry, median 5
  - T5 calendar rule deviation 0..-2 sessions, never >3 (v1-H1 condition)
  - DECL thin window median 9, range 6-11 (65 rolls)
  - OI crossover leads volume by exactly 1 calendar day (12 rolls, >=500k floor)
  - calendar spread at crossover by year + 61/66 sign match vs (DFF - 1.8pp)
  - 2026-09 roll spread +67.75 pts (v1 cross-validation)
  - FLOOR SENSITIVITY: crossover without the >=100k new-volume floor; OI
    crossover without the >=500k floor (stray-print divergence quantified)

READ-ONLY except this audit dir. Run:
  /Users/hoangminhlong/my-quantitative/.venv/bin/python a7_r1_roll.py
"""
import glob
import json
import os
import re

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
VEND = "/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet"
NS = 1_000_000_000.0
PAT = re.compile(r"^ES[HMUZ][0-9]$")
MCODE = {"H": 3, "M": 6, "U": 9, "Z": 12}

# ------------------------------------------------------------------ pass 1
chunks = sorted(glob.glob(f"{VEND}/AV1R-O1M-ES-DELTA/*.parquet")) + \
         sorted(glob.glob(f"{VEND}/AV1T-O1M-ES/*.parquet"))
print("vendor chunks:", len(chunks))
rows = []
n_raw = 0
for fp in chunks:
    d = pd.read_parquet(fp, columns=["instrument_id", "raw_symbol", "ts_event",
                                     "open", "close", "volume"])
    n_raw += len(d)
    d = d[d["raw_symbol"].str.match(PAT)]
    rows.append(d)
m = pd.concat(rows, ignore_index=True)
del rows
print("vendor rows total:", n_raw, "| ES quarterly outright rows:", len(m))
# dedupe check (chunks butt at boundaries)
dups = m.duplicated(subset=["instrument_id", "ts_event"]).sum()
print("duplicate (instrument, ts_event) rows:", dups)

chi = pd.DatetimeIndex(pd.to_datetime(m["ts_event"].to_numpy(), utc=True)) \
        .tz_convert("America/Chicago")
m["hhmm"] = chi.hour * 100 + chi.minute
m["sess"] = chi + pd.to_timedelta((chi.hour >= 17).astype("int32"), unit="D")
m["sess"] = pd.DatetimeIndex(m["sess"]).normalize().tz_localize(None)
# session-minute key: 17:00 open = 0 ... next-day 16:59 = 1379 (session spans
# midnight relative to calendar clock, so hhmm alone is NOT the session order)
m["mkey"] = np.where(chi.hour >= 17, (chi.hour - 17) * 60 + chi.minute,
                     (chi.hour + 7) * 60 + chi.minute)
m = m.drop(columns=["ts_event"])

# per (instrument, sess): volume + marks
m = m.sort_values(["instrument_id", "sess", "mkey"], kind="stable")
g = m.groupby(["instrument_id", "sess"], sort=True)
cd = g.agg(vol_total=("volume", "sum"),
           sess_close=("close", "last"),
           first_bar=("hhmm", "first")).reset_index()
cd["sess_close"] = cd["sess_close"] / NS
print("contract-days:", len(cd))

# rth marks per (instrument, sess): first open >= 0830 <1600; last close >=0830 <1600
rth = m[(m["hhmm"] >= 830) & (m["hhmm"] < 1600)]
gm = rth.groupby(["instrument_id", "sess"], sort=True).agg(
    rth_open=("open", "first"), rth_close16=("close", "last")).reset_index()
gm["rth_open"] = gm["rth_open"] / NS
gm["rth_close16"] = gm["rth_close16"] / NS
cd = cd.merge(gm, on=["instrument_id", "sess"], how="left")

# ---------------------------------------------------------------- deliveries
sym = m.groupby("instrument_id")["raw_symbol"].first()
last_sess = cd.groupby("instrument_id")["sess"].max()
first_sess = cd.groupby("instrument_id")["sess"].min()
data_end = cd["sess"].max()
deliveries = []
for iid in cd["instrument_id"].unique():
    s = sym[iid]
    mo = MCODE[s[2]]
    ls = last_sess[iid]
    # expired quarterly: last session month == delivery month (expiry = 3rd
    # Friday of delivery month). still-listed: delivery is the next occurrence
    # of month `mo` strictly after the last observed session's month.
    yy = ls.year + (1 if mo < ls.month else 0)
    deliveries.append({"instrument_id": iid, "symbol": s,
                       "delivery": f"{yy:04d}-{mo:02d}",
                       "first": first_sess[iid], "last": ls})
D = pd.DataFrame(deliveries).sort_values("delivery").reset_index(drop=True)
print("contracts:", len(D), D["delivery"].iloc[0], "->", D["delivery"].iloc[-1])
print(D.head(3).to_string(), "\n", D.tail(6).to_string())

# naive 3rd Friday + holiday-adjusted expiry model (Juneteenth June shift)
def nth_friday(y, mo, n=3):
    d = pd.Timestamp(year=y, month=mo, day=1)
    first_fri = d + pd.Timedelta(days=(4 - d.dayofweek) % 7)
    return first_fri + pd.Timedelta(weeks=n - 1)

def expiry_model(y, mo):
    """3rd Friday; if that day is a market holiday, move back one business
    day. The only mid-month Friday holiday that can hit an ES quarterly 3rd
    Friday in-window is Juneteenth (June; market-closed 2022+; Sat->observed
    Fri). 2021: Juneteenth signed Jun-17, markets OPEN Jun-18 (ESM1 expired
    Fri 2021-06-18 normally)."""
    d = nth_friday(y, mo)
    if mo == 6 and y >= 2022:
        jj = pd.Timestamp(year=y, month=6, day=19)
        # federal observance: Sat -> preceding Fri; Sun -> following Mon
        obs = jj if jj.dayofweek < 5 else (
            jj - pd.Timedelta(days=1) if jj.dayofweek == 5
            else jj + pd.Timedelta(days=1))
        if d == obs:
            d = d - pd.Timedelta(days=1)
            while d.dayofweek == 6:
                d = d - pd.Timedelta(days=1)
    return d

D["naive_3f"] = [nth_friday(int(dd[:4]), int(dd[5:7])) for dd in D["delivery"]]
D["model_exp"] = [expiry_model(int(dd[:4]), int(dd[5:7])) for dd in D["delivery"]]
D["last_vol_sess"] = D["last"]

# expired in-window = delivery month 2026-09 or earlier (stray 2027 tails that
# stopped printing early are NOT expired; they are excluded print-tails)
expired = D[D["delivery"] <= "2026-09"].copy()
match_naive = (expired["last"].dt.normalize() == expired["naive_3f"]).sum()
match_model = (expired["last"].dt.normalize() == expired["model_exp"]).sum()
print(f"expired contracts: {len(expired)} | last==naive3F: {match_naive} | "
      f"last==holiday-model: {match_model}")
mism = expired[expired["last"].dt.normalize() != expired["naive_3f"]]
print("naive mismatches:\n", mism[["symbol", "delivery", "last", "naive_3f"]].to_string())

# definitions check (2023-10+) for ESM7 2027-06-17 claim
defs = []
for fp in sorted(glob.glob(f"{VEND}/AV1T-definition-ALL10/*.parquet")):
    dd = pd.read_parquet(fp)
    if "raw_symbol" in dd.columns:
        defs.append(dd)
DE = pd.concat(defs, ignore_index=True)
es_def = DE[(DE.get("raw_symbol", pd.Series(dtype=str)).str.match(PAT) if "raw_symbol" in DE else False)]
cols = [c for c in ("instrument_id", "raw_symbol", "expiration", "expiration_date",
                    "close_time", "ts_event") if c in es_def.columns]
es_def = es_def[cols].drop_duplicates(subset=["instrument_id"])
es_def.to_json(os.path.join(HERE, "r1_es_definitions.json"), orient="records",
               date_format="iso", indent=1)
esm7 = es_def[es_def["raw_symbol"] == "ESM7"].copy()
if len(esm7) and "expiration" in esm7:
    esm7["expiration_dt"] = pd.to_datetime(
        esm7["expiration"].astype("int64"), unit="ns", utc=True)
print("ESM7 definition rows:\n", esm7.to_string())

# ------------------------------------------------------------------- chains
piv = cd.pivot_table(index="sess", columns="instrument_id", values="vol_total")
piv.index = pd.DatetimeIndex(piv.index)
sess_ix = list(piv.index)
spos = {s.date(): i for i, s in enumerate(sess_ix)}

maxday = cd.groupby("instrument_id")["vol_total"].max()
real = D[D["instrument_id"].isin(maxday[maxday >= 100_000].index)]
real = real.sort_values("delivery").reset_index(drop=True)
dl = list(real["delivery"])
iid_of = dict(zip(real["delivery"], real["instrument_id"]))
last_of = dict(zip(real["delivery"], pd.to_datetime(real["last"])))
print("real liquid deliveries:", len(dl))

# expiry session per delivery: observed last-trade (expired) else definitions
def_exp = {}
sym2del = dict(zip(real["symbol"], real["delivery"]))
for _, r in es_def.iterrows():
    d = sym2del.get(r["raw_symbol"])
    if d is None:
        continue
    v = r.get("expiration")
    if v is None:
        continue
    try:
        ts = pd.to_datetime(int(v), unit="ns", utc=True).tz_convert("America/Chicago")
        def_exp[d] = ts.date().isoformat()
    except (ValueError, TypeError):
        def_exp[d] = str(v)[:10]
expiry_of = {}
for d in dl:
    if last_of[d] < data_end - pd.Timedelta(days=5):
        expiry_of[d] = last_of[d]
    elif d in def_exp:
        expiry_of[d] = pd.Timestamp(def_exp[d])
    else:
        expiry_of[d] = last_of[d]

def build_vol_chain():
    cur = dl[0]
    out = []
    for i, s in enumerate(sess_ix):
        if i > 0:
            cands = [d for d in dl if d >= cur][:2]
            pv = piv.loc[sess_ix[i - 1]]
            vols = {d: pv.get(iid_of[d], np.nan) for d in cands}
            vols = {k: v for k, v in vols.items() if pd.notna(v)}
            if vols:
                best = max(vols, key=lambda d: (vols[d], -dl.index(d)))
                if best != cur and dl.index(best) > dl.index(cur):
                    cur = best
        out.append(cur)
    return pd.Series(out, index=piv.index)

vol_chain = build_vol_chain()
n_sw_vol = int((vol_chain != vol_chain.shift()).sum() - 1)
print("VOL chain switches:", n_sw_vol)

# ---------------------------------------------------------------- roll table
def roll_table(floor_val):
    """floor_val: minimum new-contract session volume to count as crossover
    (0 = no floor). Stray deferred prints are 1-400 lots; true fronts trade
    0.5-2.6M."""
    out = []
    for k in range(len(dl) - 1):
        d0, d1 = dl[k], dl[k + 1]
        i0, i1 = iid_of[d0], iid_of[d1]
        sub = piv[[i0, i1]].dropna()
        if len(sub) == 0:
            continue
        if sub[i1].max() < 100_000:
            continue
        cross = None
        for s in sub.index:
            if sub.at[s, i1] > sub.at[s, i0] and sub.at[s, i1] >= floor_val:
                cross = s
                break
        if cross is None:
            continue
        ci = sub.index.get_loc(cross)
        expd = expiry_of[d0]
        p_exp = spos.get(pd.Timestamp(expd).date(), None)
        p_cross = spos[cross.date()]
        # spread on prior session (both books' closes)
        prev = sub.index[ci - 1] if ci > 0 else None
        spread = None
        old_lvl = None
        if prev is not None:
            try:
                oc = cd[(cd["instrument_id"] == i0) & (cd["sess"] == prev)]["sess_close"].iloc[-1]
                nc = cd[(cd["instrument_id"] == i1) & (cd["sess"] == prev)]["sess_close"].iloc[-1]
                spread = float(nc - oc)
                old_lvl = float(oc)
            except IndexError:
                pass
        # DECL switch: last session strictly before day-1 of delivery month
        y, mo = int(d0[:4]), int(d0[5:7])
        first_day = pd.Timestamp(year=y, month=mo, day=1)
        prior = [s for s in sess_ix if s < first_day]
        dsw = prior[-1] if prior else None
        thin = spos[cross.date()] - spos[dsw.date()] if dsw else None
        t5s = p_exp - 5
        out.append({
            "old": d0, "new": d1, "year": int(d0[:4]),
            "expiry": str(pd.Timestamp(expd).date()),
            "crossover": str(cross.date()),
            "sess_before_expiry": p_exp - p_cross if p_exp is not None else None,
            "t5_minus_cross": t5s - p_cross if p_exp is not None else None,
            "spread_pts": spread,
            "old_level": old_lvl,
            "decl_thin": thin,
            "new_vol_at_cross": float(sub.at[cross, i1]),
            "old_vol_at_cross": float(sub.at[cross, i0]),
        })
    return pd.DataFrame(out)

R_floored = roll_table(100_000)
R_nofloor = roll_table(0)
R_floor10k = roll_table(10_000)
R_floor50k = roll_table(50_000)

def quick(R):
    return {"n": int(len(R)),
            "median": float(R["sess_before_expiry"].median()),
            "min": int(R["sess_before_expiry"].min()),
            "max": int(R["sess_before_expiry"].max())}
print("\nFLOOR SENSITIVITY (crossover sessions before expiry):")
print("  no floor   :", quick(R_nofloor))
print("  >=10k floor:", quick(R_floor10k))
print("  >=50k floor:", quick(R_floor50k))
print("  >=100k     :", quick(R_floored))

# DFF
fr = pd.read_parquet(os.path.expanduser(
    "~/.my-quantitative-data/futures-nonprice-10syms/normalized/fred_latest_tidy.parquet"))
dff = fr[fr["series_id"] == "FRED_DFF"].copy()
dff["date"] = pd.to_datetime(dff["observation_period"])
dff = dff.set_index("date")["value"].astype(float)

def summarize(R, tag):
    R = R.copy()
    R["dff"] = [float(dff.asof(pd.Timestamp(c))) for c in R["crossover"]]
    R["ann_pct"] = R["spread_pts"] / R["old_level"] * 100 * 4
    R["sign_match"] = [np.sign(s) == np.sign(v - 1.8)
                       for s, v in zip(R["spread_pts"], R["dff"])]
    by_year = R.groupby("year").agg(
        n=("old", "size"), med_pts=("spread_pts", "median"),
        med_ann=("ann_pct", "median"), dff_med=("dff", "median"),
        n_pos=("spread_pts", lambda s: int((s > 0).sum()))).reset_index()
    out = {
        "tag": tag,
        "n_rolls": int(len(R)),
        "sess_before_expiry": {
            "min": int(R["sess_before_expiry"].min()),
            "median": float(R["sess_before_expiry"].median()),
            "max": int(R["sess_before_expiry"].max()),
            "mean": float(R["sess_before_expiry"].mean())},
        "t5_minus_cross": {
            "min": int(R["t5_minus_cross"].min()), "max": int(R["t5_minus_cross"].max()),
            "n_abs_gt3": int((R["t5_minus_cross"].abs() > 3).sum())},
        "decl_thin": {
            "n": int(R["decl_thin"].notna().sum()),
            "median": float(R["decl_thin"].median()),
            "min": int(R["decl_thin"].min()), "max": int(R["decl_thin"].max())},
        "sign_match_dff": {
            "n": int(len(R)), "n_match": int(R["sign_match"].sum()),
            "mismatch_years": sorted(R.loc[~R["sign_match"], "year"].tolist())},
        "n_spread_pos": int((R["spread_pts"] > 0).sum()),
        "n_spread_neg": int((R["spread_pts"] < 0).sum()),
        "by_year": by_year.to_dict(orient="records"),
        "roll_2026_09": R[R["old"] == "2026-09"][
            ["old", "crossover", "sess_before_expiry", "spread_pts", "ann_pct",
             "new_vol_at_cross", "old_vol_at_cross"]].to_dict(orient="records"),
    }
    return out, R

sum_floored, Rf = summarize(R_floored, "floored(>=100k)")
sum_nofloor, Rn = summarize(R_nofloor, "NO_FLOOR")

# floor divergence detail
div = []
for _, r in Rn.iterrows():
    rf = Rf[Rf["old"] == r["old"]]
    if len(rf) and rf["crossover"].iloc[0] != r["crossover"]:
        div.append({"old": r["old"], "nofloor_crossover": r["crossover"],
                    "nofloor_sess_before_expiry": int(r["sess_before_expiry"]),
                    "nofloor_new_vol": r["new_vol_at_cross"],
                    "floored_crossover": rf["crossover"].iloc[0],
                    "floored_sess_before_expiry": int(rf["sess_before_expiry"].iloc[0]),
                    "floored_new_vol": float(rf["new_vol_at_cross"].iloc[0])})
print("\nfloor-divergent rolls:", len(div))
for d in div:
    print(" ", d)

# ---------------------------------------------------------------- OI crossovers
sts = []
for fp in sorted(glob.glob(f"{VEND}/AV1T-statistics-ALL10/*.parquet")):
    st = pd.read_parquet(fp)
    sts.append(st)
ST = pd.concat(sts, ignore_index=True)
print("statistics stat_types:", sorted(ST["stat_type"].unique().tolist()))
oi_rows = ST[(ST["raw_symbol"].str.match(PAT)) & (ST["stat_type"] == 9)].copy()
print("ES stat_type=9 rows:", len(oi_rows))
oi_rows = oi_rows.sort_values("ts_event").drop_duplicates(
    subset=["raw_symbol", "ts_ref"], keep="last")
oi_rows["ref"] = pd.to_datetime(oi_rows["ts_ref"].astype("int64"), unit="ns").dt.normalize()
oi_rows["delivery"] = oi_rows["raw_symbol"].map(sym2del)
oiq_full = oi_rows.dropna(subset=["delivery"]).pivot_table(
    index="ref", columns="delivery", values="quantity", aggfunc="last")
oiq_full = oiq_full[oiq_full.index >= pd.Timestamp("2023-09-28")]
print("OI pivot:", oiq_full.shape, oiq_full.index.min(), "->", oiq_full.index.max())

def oi_crossovers(floor):
    out = []
    for k in range(len(dl) - 1):
        d0, d1 = dl[k], dl[k + 1]
        if d0 < "2023-10" or d0 not in oiq_full.columns or d1 not in oiq_full.columns:
            continue
        o0, o1 = oiq_full[d0].dropna(), oiq_full[d1].dropna()
        common = o0.index.intersection(o1.index)
        for s in common:
            if o1[s] > o0[s] and (o1[s] >= 500_000 or floor == 0):
                rf = Rf[Rf["old"] == d0]
                out.append({
                    "old": d0,
                    "oi_crossover": str(pd.Timestamp(s).date()),
                    "vol_crossover": rf["crossover"].iloc[0] if len(rf) else None,
                    "oi_new_val": float(o1[s]),
                    "cal_days_oi_minus_vol": (pd.Timestamp(s).normalize() -
                                              pd.Timestamp(rf["crossover"].iloc[0])).days
                    if len(rf) else None})
                break
    return out

oi_floored = oi_crossovers(1)
oi_nofloor = oi_crossovers(0)
print("\nOI crossovers floored:", len(oi_floored),
      "| lead-by-1-day:", sum(1 for x in oi_floored if x["cal_days_oi_minus_vol"] == -1))
print("OI crossovers NO floor:", len(oi_nofloor))
for x in oi_nofloor:
    if not any(y["old"] == x["old"] and y["oi_crossover"] == x["oi_crossover"] for y in oi_floored):
        print("  no-floor-only crossover:", x)

result = {
    "recompute": "independent from vendor parquet (audit lane A7-DEEP-ES)",
    "vendor_rows": n_raw,
    "es_quarterly_rows": int(len(m)),
    "duplicate_instrument_ts_rows": int(dups),
    "n_contracts": int(len(D)),
    "expired_contracts": int(len(expired)),
    "last_eq_naive3F": int(match_naive),
    "last_eq_holiday_model": int(match_model),
    "naive_mismatches": mism[["symbol", "delivery"]].assign(
        last=mism["last"].astype(str), naive3F=mism["naive_3f"].astype(str)
    ).to_dict(orient="records"),
    "esm7_definition": esm7.to_dict(orient="records"),
    "floor_sensitivity": {
        "nofloor": quick(R_nofloor), "floor_10k": quick(R_floor10k),
        "floor_50k": quick(R_floor50k), "floor_100k": quick(R_floored)},
    "floored": sum_floored,
    "nofloor": sum_nofloor,
    "floor_divergent_rolls": div,
    "oi_floored": oi_floored,
    "oi_nofloor": oi_nofloor,
    "rolls_floored_detail": Rf.drop(columns=["sign_match"]).to_dict(orient="records"),
}
with open(os.path.join(HERE, "r1_roll.json"), "w") as f:
    json.dump(result, f, indent=1, default=str)
print("\nWROTE r1_roll.json")
