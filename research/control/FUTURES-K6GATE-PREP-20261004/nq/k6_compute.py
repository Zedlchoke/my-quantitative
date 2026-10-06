"""Lane NQ-K6 compute — FUTURES-K6GATE-PREP-20261004.

Pre-registered 0-cost anatomy gates + descriptive rebuilds on cache_v3.
Recipes mirrored verbatim from committed generators
(FUTURES-DEEPRESEARCH-V2-20261003/analysis/NQ_a1_regimes.py,
NQ_a2_sessions.py, NQ_a4_events.py). DESCRIPTIVE ONLY — no PnL, no
conditional-on-signal statistic, no parameter selection.
"""
from __future__ import annotations
import glob, json, os, re, sys
import numpy as np
import pandas as pd

WT = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-k6gate/prep"
OUT = f"{WT}/research/control/FUTURES-K6GATE-PREP-20261004/nq"
CACHE = f"{WT}/research/control/FUTURES-SIX-READINESS-20261004/nq/cache_v3"
NONPRICE = os.path.expanduser(
    "/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms")
CHI = "America/Chicago"
SESSION_SWITCH_DATE = pd.Timestamp("2015-09-21")

def jdump(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, sort_keys=False, default=str)
    print("wrote", path, flush=True)

def era_close_min(d):
    return 16 * 60 + 15 if pd.Timestamp(d) < SESSION_SWITCH_DATE else 16 * 60

# ---------------------------------------------------------------- calendars
def load_fomc():
    files = sorted(glob.glob(f"{NONPRICE}/fed/statements/monetary*.html"))
    rows = []
    for f in files:
        m = re.fullmatch(r"monetary(\d{8})a\.html", os.path.basename(f))
        if not m:
            continue
        d = pd.Timestamp(m.group(1))
        txt = open(f, encoding="utf-8", errors="replace").read()
        mt = re.search(r"For release at\s*(\d{1,2}):(\d{2})\s*([ap])\.m\.\s*(E[SD]T)", txt)
        t = None
        if mt:
            hh = int(mt.group(1)) % 12 + (12 if mt.group(3) == "p" else 0)
            t = f"{hh:02d}:{mt.group(2)}:00"
        rows.append({"date": d, "time_et": t, "statement_file": os.path.basename(f)})
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)

def load_bls():
    p = f"{WT}/research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/events_bbo_coverage/bls_dates.json"
    b = json.load(open(p))
    out = {}
    for series in ("CPI", "EMPSIT"):
        ds = []
        for y, yb in b["series"][series]["years"].items():
            ds += list(yb["dates"])
        out[series] = sorted(set(ds))
    return out, b

def load_expiries():
    p = f"{WT}/research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/cme_cal/nq_es/nq_cal_coverage.json"
    d = json.load(open(p))
    ds = []
    for y, yb in d["expirations"]["per_year"].items():
        for q in ("mar", "jun", "sep", "dec"):
            ds.append(yb[q])
    return sorted(set(ds)), d

# ---------------------------------------------------------------- small data
print("loading sessions/held ...", flush=True)
sess = pd.read_parquet(f"{CACHE}/nq_sessions_v3.parquet")
held = pd.read_parquet(f"{CACHE}/held_volume_k5_v3.parquet")
hs = sess.merge(held.rename(columns={"held": "contract"}),
                on=["session_date", "contract"], how="inner")
hs["d"] = pd.to_datetime(hs["session_date"])
hs["clean"] = hs["rth_coverage"].fillna(0) >= 0.6
fomc = load_fomc()
bls, blsdoc = load_bls()
exp_dates, caldoc = load_expiries()
fomc_dates = set(fomc["date"].dt.normalize())
print(f"held sessions {len(hs)}, fomc {len(fomc)}, cpi {len(bls['CPI'])}, "
      f"empsit {len(bls['EMPSIT'])}, expiries {len(exp_dates)}", flush=True)

# ---------------------------------------------------------------- big panel
print("loading annotated 1m (single shot) ...", flush=True)
cols = ["contract", "session_date", "minute_of_day", "close", "high", "low",
        "volume", "dt", "in_rth"]
df = pd.read_parquet(f"{CACHE}/nq_annotated_1m_v3.parquet", columns=cols)
df["d"] = pd.to_datetime(df["session_date"])
df = df.sort_values(["contract", "dt"]).reset_index(drop=True)
lc = np.log(df["close"].astype(float))
df["r1"] = lc.groupby(df["contract"]).diff()
df.loc[df["contract"].ne(df["contract"].shift()), "r1"] = np.nan
df["vol"] = df["volume"].astype(np.int64)
print(f"panel rows {len(df)}", flush=True)

dfh = df.merge(held.rename(columns={"held": "contract"}),
               on=["contract", "session_date"], how="inner")
print(f"held-contract bars {len(dfh)}", flush=True)

# ================================================================= M1 — FOMC
print("M1 ...", flush=True)
REL = 13 * 60
WINDOWS = [("m120_60", -120, -60), ("m60_0", -60, 0), ("h0_30", 0, 30),
           ("h30_60", 30, 60), ("h60_120", 60, 120), ("h120_180", 120, 180)]
# fixed minute windows -> precompute per held session sums
hs_idx = hs.set_index("d")
pool_ok = hs[(hs["rth_coverage"].fillna(0) >= 0.6)]
ev2 = fomc[fomc["time_et"].astype(str) == "14:00:00"].copy()
win_rows = []
for _, ev in ev2.iterrows():
    day = ev["date"].normalize()
    if day not in hs_idx.index:
        continue
    row = hs_idx.loc[day]
    if pd.isna(row["rth_coverage"]) or row["rth_coverage"] < 0.6:
        continue
    lo, hi = day - pd.Timedelta(days=21), day + pd.Timedelta(days=21)
    pool_dates = hs[(hs["d"] >= lo) & (hs["d"] <= hi)
                    & (hs["d"].dt.dayofweek == day.dayofweek)
                    & (~hs["d"].isin(fomc_dates))
                    & (hs["rth_coverage"].fillna(0) >= 0.6)]["d"]
    pb = dfh[dfh["d"].isin(pool_dates)]
    b = dfh[dfh["d"] == day]
    if not len(b):
        continue
    rec = {"date": str(day.date())}
    for name, a, bb in WINDOWS:
        m0, m1 = REL + a, REL + bb
        eb = b[(b["minute_of_day"] >= m0) & (b["minute_of_day"] < m1)]
        cb = pb[(pb["minute_of_day"] >= m0) & (pb["minute_of_day"] < m1)]
        ev_vol = float(eb["vol"].sum())
        ev_absr = float(eb["r1"].abs().mean()) if len(eb) > 1 else np.nan
        cv = float(cb.groupby("d")["vol"].sum().median())
        ca = float(cb.assign(ar1=cb["r1"].abs()).groupby("d")["ar1"].mean().median())
        rec[f"vol_ratio_{name}"] = ev_vol / cv if cv else np.nan
        rec[f"absr_ratio_{name}"] = ev_absr / ca if ca and not np.isnan(ev_absr) else np.nan
        ev_rng = float(eb["high"].max() - eb["low"].min()) if len(eb) else np.nan
        cr = float(cb.groupby("d").apply(
            lambda g_: g_["high"].max() - g_["low"].min(), include_groups=False).median())
        rec[f"rng_ratio_{name}"] = ev_rng / cr if cr and not np.isnan(ev_rng) else np.nan
    # release minute
    em = b[b["minute_of_day"] == REL]
    cm = pb[pb["minute_of_day"] == REL]
    if len(em) and len(cm):
        rec["release_minute_vol_ratio"] = float(em["vol"].iloc[0] / cm["vol"].median())
    win_rows.append(rec)
wd = pd.DataFrame(win_rows)
m1 = {"schema": "nq_k6_m1_fomc_anatomy_v3@1",
      "n_events_qualifying": int(len(wd)),
      "n_2pm_events_total": int(len(ev2)),
      "windows": {}}
for name, _a, _b in WINDOWS:
    m1["windows"][name] = {
        "vol_ratio_median": float(wd[f"vol_ratio_{name}"].median()),
        "absr_ratio_median": float(wd[f"absr_ratio_{name}"].median()),
        "rng_ratio_median": float(wd[f"rng_ratio_{name}"].median())}
m1["windows"]["release_minute"] = {
    "vol_ratio_median": float(wd["release_minute_vol_ratio"].median())}
wd["year"] = pd.to_datetime(wd["date"]).dt.year
era_hour = {}
for name, a, b in [("2016_2019", 2016, 2019), ("2020_2022", 2020, 2022),
                   ("2023_2026", 2023, 2026)]:
    w = wd[(wd["year"] >= a) & (wd["year"] <= b)]
    if len(w):
        era_hour[name] = {
            "n": int(len(w)),
            "h0_30_vol_ratio": float(w["vol_ratio_h0_30"].median()),
            "h0_30_absr_ratio": float(w["absr_ratio_h0_30"].median()),
            "m60_0_vol_ratio": float(w["vol_ratio_m60_0"].median()),
            "h120_180_vol_ratio": float(w["vol_ratio_h120_180"].median())}
m1["era_table"] = era_hour
jdump(m1, f"{OUT}/m1_fomc_anatomy_v3.json")

# ================================================================= M5 — 07:30
print("M5 ...", flush=True)
release_dates = sorted(set(bls["CPI"]) | set(bls["EMPSIT"]))
canceled_2025 = ["2025-11-13", "2025-11-07"]  # vintage-law canceled-but-expected
M = {"450": 7 * 60 + 30, "445": 7 * 60 + 25, "449": 7 * 60 + 29, "451": 7 * 60 + 31}
m5 = {"schema": "nq_k6_m5_0730_era_v3@1",
      "anchor_note": "07:30 CT = 08:30 ET release slot (family anchor; "
                     "dispatch wording '07:30 ET' read as the family anchor)",
      "cells": {}}
eras_m5 = [("2010-16", "2010-06-07", "2016-09-30"),
           ("2017-20", "2017-01-01", "2020-02-21"),
           ("2023-26", "2023-01-01", "2026-10-01")]
for name, a, b in eras_m5:
    w = dfh[(dfh["d"] >= a) & (dfh["d"] <= b)]  # exact mirror of a2 minute_profiles
    tot = float(w["vol"].sum())
    cell = {"class_calfree_mirror": {"era_total_vol": tot}}
    for k, m in M.items():
        mw = w[w["minute_of_day"] == m]
        cell["class_calfree_mirror"][f"share_{k}"] = float(mw["vol"].sum() / tot)
        cell["class_calfree_mirror"][f"absret_{k}_bp"] = float(mw["r1"].abs().mean() * 1e4)
    cell["class_calfree_mirror"]["spike_ratio_0730_vs_0725"] = (
        cell["class_calfree_mirror"]["share_450"] / cell["class_calfree_mirror"]["share_445"])
    # coverage>=0.6 variant (as predeclared)
    w6 = w[w["d"].isin(hs[hs["clean"]]["d"])]
    tot6 = float(w6["vol"].sum())
    cv = {"era_total_vol": tot6}
    for k, m in M.items():
        mw = w6[w6["minute_of_day"] == m]
        cv[f"share_{k}"] = float(mw["vol"].sum() / tot6)
        cv[f"absret_{k}_bp"] = float(mw["r1"].abs().mean() * 1e4)
    cv["spike_ratio_0730_vs_0725"] = cv["share_450"] / cv["share_445"]
    cell["class_calfree_cov06"] = cv
    # release-day vs same-weekday controls
    rel_days = [pd.Timestamp(x) for x in release_dates
                if a <= x <= b]
    rel_cancel = [pd.Timestamp(x) for x in canceled_2025 if a <= x <= b]
    rel_all = rel_days + rel_cancel
    ctrl = hs[(hs["d"] >= a) & (hs["d"] <= b) & hs["clean"]
              & (hs["d"].dt.dayofweek.isin([0, 1, 2, 3, 4]))
              & (~hs["d"].isin([pd.Timestamp(x) for x in release_dates]))
              & (~hs["d"].isin([pd.Timestamp(x) for x in canceled_2025]))]
    rrow = {"n_release_days_in_era": len(rel_all),
            "n_release_with_held_session": 0, "n_controls": int(len(ctrl))}
    if rel_all:
        bw = dfh[dfh["d"].isin(rel_all) & dfh["d"].isin(hs[hs["clean"]]["d"])]
        sess_vol = bw.groupby("d")["vol"].sum()
        v450 = bw[bw["minute_of_day"] == 450].groupby("d")["vol"].sum()
        a450 = bw[bw["minute_of_day"] == 450].groupby("d")["r1"].apply(
            lambda s: float(np.nanmean(np.abs(s))) if len(s) else np.nan)
        share_rel = (v450 / sess_vol).dropna()
        # controls per-session minute-450 share
        bwc = dfh[dfh["d"].isin(ctrl["d"])]
        sess_volc = bwc.groupby("d")["vol"].sum()
        v450c = bwc[bwc["minute_of_day"] == 450].groupby("d")["vol"].sum()
        a450c = bwc[bwc["minute_of_day"] == 450].groupby("d")["r1"].apply(
            lambda s: float(np.nanmean(np.abs(s))) if len(s) else np.nan)
        share_ctrl = (v450c / sess_volc).dropna()
        rrow["n_release_with_held_session"] = int(len(share_rel))
        rrow["share_0730_release_median"] = float(share_rel.median()) if len(share_rel) else None
        rrow["share_0730_control_median"] = float(share_ctrl.median()) if len(share_ctrl) else None
        rrow["ratio_release_vs_control"] = (
            float(share_rel.median() / share_ctrl.median())
            if len(share_rel) and len(share_ctrl) and share_ctrl.median() else None)
        rrow["absret_0730_release_bp"] = float(a450.mean() * 1e4) if len(a450) else None
        rrow["absret_0730_control_bp"] = float(a450c.mean() * 1e4) if len(a450c) else None
    cell["class_release_vs_control"] = rrow
    m5["cells"][name] = cell
jdump(m5, f"{OUT}/m5_0730_era_v3.json")

# ================================================================= M2 — F5-K6
print("M2 ...", flush=True)
DFH_BY_D = {k: g for k, g in dfh.groupby("d", sort=True)}
tri = [("2010-16", "2010-06-07", "2016-12-31"),
       ("2017-21", "2017-01-01", "2021-12-31"),
       ("2022-26", "2022-01-01", "2026-10-01")]
exp_ts = [pd.Timestamp(x) for x in exp_dates]
bls_all = set(pd.Timestamp(x) for x in release_dates)
m2 = {"schema": "nq_k6_m2_expwitch_anatomy_v3@1", "tri_eras": {},
      "integrity": {}}
for name, a, b in tri:
    fridays = hs[(hs["d"] >= a) & (hs["d"] <= b) & (hs["d"].dt.dayofweek == 4)]
    w_set = set(d for d in fridays["d"] if any(d == e for e in exp_ts))
    o_set = set(fridays["d"]) - w_set - fomc_dates - bls_all
    res = {}
    for cls, dset in (("W", w_set), ("O", o_set)):
        g = hs[hs["d"].isin(dset)]
        gc = g[g["clean"]]
        gb = dfh[dfh["d"].isin(dset)]
        # close window per session
        cms = {r.d: (era_close_min(r.d) if r.last_min >= era_close_min(r.d) - 45
                     else int(r.last_min)) for r in g.itertuples()}
        cw_vol, cw_absr, fs_absr = [], [], []
        for d in sorted(dset):
            bb = DFH_BY_D.get(d)
            if bb is None or not len(bb):
                continue
            cm = cms.get(d)
            if cm is None:
                continue
            cwb = bb[(bb["minute_of_day"] > cm - 60) & (bb["minute_of_day"] <= cm)]
            sv = float(bb["vol"].sum())
            if sv and len(cwb):
                cw_vol.append(float(cwb["vol"].sum() / sv))
                cw_absr.append(float(cwb["r1"].abs().mean() * 1e4))
            fs_absr.append(float(bb["r1"].abs().mean() * 1e4))
        res[cls] = {
            "n_sessions_held": int(len(g)), "n_sessions_clean": int(len(gc)),
            "vol_median": float(gc["volume"].median()) if len(gc) else None,
            "vol_p25": float(gc["volume"].quantile(.25)) if len(gc) else None,
            "vol_p75": float(gc["volume"].quantile(.75)) if len(gc) else None,
            "rth_bars_median": float(gc["rth_bars"].median()) if len(gc) else None,
            "rth_bars_p10": float(gc["rth_bars"].quantile(.1)) if len(gc) else None,
            "n_bars_median": float(g["n_bars"].median()) if len(g) else None,
            "absret_full_median_bp": float(np.median(fs_absr)) if fs_absr else None,
            "closewin_volshare_median": float(np.median(cw_vol)) if cw_vol else None,
            "closewin_absret_median_bp": float(np.median(cw_absr)) if cw_absr else None}
    if res["O"]["vol_median"]:
        res["ratio_W_vs_O"] = {
            "vol_median": res["W"]["vol_median"] / res["O"]["vol_median"],
            "absret_full": (res["W"]["absret_full_median_bp"] /
                            res["O"]["absret_full_median_bp"])
            if res["O"]["absret_full_median_bp"] else None,
            "closewin_volshare": (res["W"]["closewin_volshare_median"] /
                                  res["O"]["closewin_volshare_median"])
            if res["O"]["closewin_volshare_median"] else None,
            "closewin_absret": (res["W"]["closewin_absret_median_bp"] /
                                res["O"]["closewin_absret_median_bp"])
            if res["O"]["closewin_absret_median_bp"] else None}
    m2["tri_eras"][name] = res

# integrity (ii): expiry-Friday phantom gaps + switch-day descriptive
gap_fails, gap_rows = [], []
for d in sorted(w_set_all := set(hs[hs["d"].isin(exp_ts)]["d"])):
    g = hs[hs["d"] == d]
    for r in g.itertuples():
        cm = era_close_min(r.d) if r.last_min >= era_close_min(r.d) - 45 else int(r.last_min)
        bb0 = DFH_BY_D.get(r.d)
        if bb0 is None:
            continue
        bb = bb0["minute_of_day"]
        present = sorted(set(int(x) for x in bb if 510 <= x <= cm))
        if not present:
            continue
        expected = cm - 510 + 1
        maxgap, run = 0, present[0] - 510
        prev = present[0]
        for x in present[1:]:
            run = x - prev - 1
            maxgap = max(maxgap, run)
            prev = x
        maxgap = max(maxgap, cm - prev)
        ok = (maxgap <= 5) and (len(present) >= 0.8 * expected)
        gap_rows.append({"date": str(r.d.date()), "contract": r.contract,
                         "max_gap_min": int(maxgap),
                         "present": len(present), "expected": expected,
                         "pass": bool(ok)})
        if not ok:
            gap_fails.append(gap_rows[-1])
m2["integrity"] = {
    "n_expiry_friday_held_sessions": len(gap_rows),
    "n_fail_phantom_gap": len(gap_fails),
    "fails": gap_fails[:20]}
jdump(m2, f"{OUT}/m2_expwitch_anatomy_v3.json")

# switch-day descriptive needs held daily series — built in M4 block below;
# append after M4 computes it.

# ================================================================= M3 — dispersion
print("M3 ...", flush=True)
gb = dfh.groupby("d", sort=True)
rows = []
for d, g in gb:
    full = g["r1"].abs() * 1e4
    rth = g[g["in_rth"] == True]["r1"].abs() * 1e4  # noqa: E712
    r5 = (g[g["in_rth"] == True]  # noqa: E712
          .assign(bk=(g[g["in_rth"] == True]["minute_of_day"] // 5))
          .groupby("bk")["close"].last())
    r5ret = np.log(r5.astype(float)).diff().dropna()
    rows.append({
        "d": str(d.date()),
        "n_bars": int(len(g)),
        "n_bars_rth": int((g["in_rth"] == True).sum()),  # noqa: E712
        "absret_mean_bp": float(full.mean()) if len(full) else None,
        "absret_median_bp": float(full.median()) if len(full) else None,
        "absret_sd_bp": float(full.std()) if len(full) > 1 else None,
        "rth_absret_median_bp": float(rth.median()) if len(rth) else None,
        "rth_5min_sd_bp": float(r5ret.std() * np.sqrt(78) * 1e4) if len(r5ret) > 2 else None})
sdisp = pd.DataFrame(rows)
sdisp_meta = {"schema": "nq_session_dispersion_v3@1",
              "n_sessions": int(len(sdisp)),
              "first": sdisp["d"].iloc[0], "last": sdisp["d"].iloc[-1],
              "per_year": {}, "full_era": {}, "hole_window_2020_03_05": {}}
meas = ["absret_mean_bp", "absret_median_bp", "absret_sd_bp",
        "rth_absret_median_bp", "rth_5min_sd_bp"]
yy = pd.to_datetime(sdisp["d"]).dt.year
for y, g in sdisp.groupby(yy):
    sdisp_meta["per_year"][str(int(y))] = {
        "n_sessions": int(len(g)),
        **{m: {"median": float(g[m].median()),
               "p25": float(g[m].quantile(.25)),
               "p75": float(g[m].quantile(.75))} for m in meas}}
sdisp_meta["full_era"] = {
    "n_sessions": int(len(sdisp)),
    **{m: {"median": float(sdisp[m].median()),
           "p25": float(sdisp[m].quantile(.25)),
           "p75": float(sdisp[m].quantile(.75))} for m in meas}}
hole = sdisp[(sdisp["d"] >= "2020-03-23") & (sdisp["d"] <= "2020-05-29")]
sdisp_meta["hole_window_2020_03_05"] = {
    "window": "2020-03-23..2020-05-29 (the pre-v3 vendor hole)",
    "n_sessions": int(len(hole)),
    **{m: ({"median": float(hole[m].median()),
            "p25": float(hole[m].quantile(.25)),
            "p75": float(hole[m].quantile(.75))} if len(hole) else None)
       for m in meas}}
jdump(sdisp_meta, f"{OUT}/session_dispersion_v3.json")
sdisp.to_parquet(f"{OUT}/session_dispersion_v3_per_session.parquet", index=False)

# ================================================================= M4 — a1/a2
print("M4 ...", flush=True)
d = hs.sort_values("session_date").reset_index(drop=True)
d["log_close"] = np.log(d["close"].astype(float))
d["ret"] = d["log_close"].diff()
d["cov"] = d["rth_coverage"].clip(0, 1).fillna(0.0)
d["depleted"] = (d["cov"] < 0.25) | d["close"].isna()

a1 = {"schema": "nq_f3_rebuild_a1a2_v3@1", "note":
      "full-era rebuild of NQ_a1_regimes@1/NQ_a2_sessions@1 recipes on "
      "cache_v3 (alias-recovered chain); descriptive aggregation only — "
      "no RR signal, no PnL", "a1": {}, "a2": {}}
r = d["ret"].dropna()
a1["a1"]["panel"] = {
    "n_sessions": int(len(d)), "first": str(d["d"].iloc[0].date()),
    "last": str(d["d"].iloc[-1].date()),
    "roll_rule": "PIT volume-crossover k=5, decide t-1, hold from t",
    "n_rolls": int((held["held"] != held["held"].shift()).sum() - 1),
    "depleted_sessions": int(d["depleted"].sum())}
ann = 252.0
volz = {}
for w in (5, 10, 20, 60, 120, 252):
    volz[f"rvol_{w}d"] = d["ret"].rolling(w, min_periods=max(2, int(w * .75))).std() * np.sqrt(ann)
vdf = pd.DataFrame(volz)
vol_summary = {}
for c in vdf:
    s = vdf[c].dropna()
    vol_summary[c] = {"min": float(s.min()), "p5": float(s.quantile(.05)),
                      "p25": float(s.quantile(.25)), "median": float(s.median()),
                      "p75": float(s.quantile(.75)), "p95": float(s.quantile(.95)),
                      "max": float(s.max()),
                      "argmin_date": str(d["d"][s.idxmin()].date()),
                      "argmax_date": str(d["d"][s.idxmax()].date()),
                      "last": float(s.iloc[-1])}
a1["a1"]["realized_vol_summary"] = vol_summary
rv20 = vdf["rvol_20d"]
a1["a1"]["vol_clustering"] = {
    "acf1_abs_ret_252d_median": float(
        d["ret"].abs().rolling(252).apply(
            lambda x: np.corrcoef(x[:-1], x[1:])[0, 1], raw=True).dropna().median()),
    "vol20_of_vol20": float(rv20.diff().abs().rolling(252).median().dropna().median())}

def variance_ratio(ret, q):
    var1 = ret.rolling(252, min_periods=189).var()
    varq = ret.rolling(q, min_periods=q).sum().rolling(252, min_periods=189).var()
    return varq / (q * var1)

vrdf = pd.DataFrame({f"vr_{q}": variance_ratio(d["ret"], q) for q in (5, 20, 60)})
acf_rolling = d["ret"].rolling(252).apply(
    lambda x: np.corrcoef(x[:-1], x[1:])[0, 1], raw=True).dropna()
a1["a1"]["trend_persistence"] = {
    "acf1_ret_full": float(r.autocorr(1)),
    "acf1_ret_rolling252_median": float(acf_rolling.median()),
    "acf1_ret_rolling252_p10_p90": [float(x) for x in acf_rolling.quantile([.1, .9])],
    "variance_ratios_full": {k: float(v.dropna().iloc[-252:].mean())
                             for k, v in vrdf.items()},
    "variance_ratio_20_median": float(vrdf["vr_20"].dropna().median()),
    "variance_ratio_20_p10_p90": [float(x) for x in vrdf["vr_20"].dropna().quantile([.1, .9])]}

d["cum"] = d["log_close"] - d["log_close"].iloc[0]
d["peak"] = d["cum"].cummax()
d["dd"] = d["cum"] - d["peak"]

def drawdown_episodes(dd, min_depth=0.10):
    eps, in_dd, start, trough = [], False, None, None
    for i, (dt_, v) in enumerate(dd.items()):
        if not in_dd and v < -min_depth:
            in_dd, start, trough = True, i, i
        elif in_dd:
            if v < dd.iloc[trough]:
                trough = i
            if v >= -1e-9:
                eps.append((start, trough, i)); in_dd = False
    if in_dd:
        eps.append((start, trough, None))
    return eps

ep_list = []
for s, t, e in drawdown_episodes(d["dd"], 0.10):
    ep_list.append({"start": str(d["d"].iloc[s].date()),
                    "trough": str(d["d"].iloc[t].date()),
                    "end": (str(d["d"].iloc[e].date()) if e is not None else "unrecovered"),
                    "depth_pct": float(-100 * d["dd"].iloc[t]),
                    "peak_to_trough_sessions": int(t - s),
                    "recovery_sessions": (int(e - t) if e is not None else None),
                    "trough_is_depleted_window": bool(d["depleted"].iloc[t])})
ep_list.sort(key=lambda x: -x["depth_pct"])
a1["a1"]["drawdowns_ge10pct"] = ep_list

d["year"] = d["d"].dt.year
yearly = []
for y, g in d.groupby("year"):
    rr = g["ret"].dropna()
    cum = g.set_index("d")["cum"]
    dd_y = cum - cum.cummax()
    yearly.append({"year": int(y), "n_sessions": int(len(g)),
                   "ret_pct": float(100 * g["ret"].sum()),
                   "vol_ann_pct": float(100 * rr.std() * np.sqrt(252)) if len(rr) > 2 else None,
                   "skew": float(rr.skew()) if len(rr) > 10 else None,
                   "ex_kurt": float(rr.kurt()) if len(rr) > 10 else None,
                   "up_days_pct": float(100 * (rr > 0).mean()),
                   "worst_day_pct": float(100 * rr.min()),
                   "best_day_pct": float(100 * rr.max()),
                   "max_dd_pct": float(-100 * dd_y.min()) if len(dd_y) else None,
                   "avg_daily_vol_contracts": float(g["volume"].mean()),
                   "median_true_range_pts": float(g["true_range"].median()),
                   "depleted_sessions": int(g["depleted"].sum()),
                   "med_rvol20": float((g["ret"].rolling(20, min_periods=15).std()
                                        * np.sqrt(252)).median())})
a1["a1"]["yearly"] = yearly

rv60 = vdf["rvol_60d"]
lab_vol = []
win = 756
for i in range(len(rv60)):
    lo = max(0, i - win)
    seg = rv60.iloc[lo:i + 1].dropna()
    if len(seg) < 300:
        lab_vol.append(None)
    else:
        hist = seg.iloc[:-1]
        q1, q2 = hist.quantile(1 / 3), hist.quantile(2 / 3)
        lab_vol.append(1 if seg.iloc[-1] <= q1 else (2 if seg.iloc[-1] <= q2 else 3))
d["regime_vol"] = lab_vol
counts = pd.Series([x for x in lab_vol if x is not None]).value_counts()
a1["a1"]["regime_vol_tercile_counts"] = {str(k): int(v) for k, v in counts.items()}
ct = pd.crosstab(d["year"], pd.Series(lab_vol, name="rv"))
a1["a1"]["regime_vol_by_year"] = {
    str(int(y)): {str(int(k)): int(v) for k, v in row.items() if pd.notna(k)}
    for y, row in ct.iterrows()}
mu = d["ret"].rolling(120, min_periods=90).mean()
se = d["ret"].rolling(120, min_periods=90).std() / np.sqrt(120)
tstat = (mu / se).where(se > 0)
d["regime_trend"] = np.where(tstat > 1, "trend_up",
                     np.where(tstat < -1, "trend_down", "range"))
tr_counts = d["regime_trend"][d["ret"].notna()].value_counts()
a1["a1"]["regime_trend_counts"] = {k: int(v) for k, v in tr_counts.items()}
ct2 = pd.crosstab(d["year"], d["regime_trend"])
a1["a1"]["regime_trend_by_year"] = {
    str(int(y)): {k: int(v) for k, v in row.items() if pd.notna(k)}
    for y, row in ct2.iterrows()}
d["hi_vol"] = pd.Series(lab_vol, index=d.index) == 3
a1["a1"]["share_high_vol_by_year"] = {
    str(int(y)): float(g["hi_vol"].mean()) for y, g in d.groupby("year")}
full20 = vdf["rvol_20d"].dropna()
v1w = d["d"] >= pd.Timestamp("2025-05-30")
v1_rvol = vdf["rvol_20d"][v1w].dropna()
prior = d["d"] < pd.Timestamp("2025-01-01")
prior_rvol = vdf["rvol_20d"][prior].dropna()
a1["a1"]["v1_window_context"] = {
    "v1_window": "2025-05-30..2026-10-01 (true-front, v1 dossier W2)",
    "rvol20_median_v1window_pct": float(100 * v1_rvol.median()),
    "rvol20_median_2010_2024_pct": float(100 * prior_rvol.median()),
    "rvol20_percentile_of_v1window_median_within_2010_2024":
        float((prior_rvol < v1_rvol.median()).mean()),
    "rvol20_p10_p90_2010_2024_pct": [float(100 * prior_rvol.quantile(.1)),
                                     float(100 * prior_rvol.quantile(.9))],
    "v1_rvol20_range_pct": [float(100 * v1_rvol.min()), float(100 * v1_rvol.max())],
    "v1_window_max_dd_pct": float(-100 * d[d.index.isin(v1w[v1w].index)]["dd"].min())}

# calendar-rule sensitivity from cache_v3 registry
try:
    reg = pd.DataFrame(json.load(open(f"{CACHE}/contract_registry_v3.json")))
    sess_real = sess[sess["contract"].isin(set(reg["contract"]))]
    lut = reg.set_index("contract")["expiry"].to_dict()
    by_c = {c: g.sort_values("session_date") for c, g in sess_real.groupby("contract")}
    contracts = sorted(by_c.keys(), key=lambda c: lut[c])
    outs = []
    for i, c in enumerate(contracts[:-1]):
        exp = pd.Timestamp(lut[c])
        g = by_c[c]
        winm = g[pd.to_datetime(g["session_date"]) < exp.replace(day=1)]
        if i > 0:
            prev_exp = pd.Timestamp(lut[contracts[i - 1]])
            winm = winm[pd.to_datetime(winm["session_date"]) >= prev_exp.replace(day=1)]
        if len(winm):
            outs.append(winm[["session_date", "contract"]].rename(columns={"contract": "held"}))
    held_cal = pd.concat(outs).sort_values("session_date")
    held_cal = held_cal.groupby("session_date")["held"].last().reset_index()
    dc = hs.merge(held_cal, on=["session_date", "contract"], how="right")
    dc = dc.sort_values("session_date").reset_index(drop=True)
    dc["log_close"] = np.log(dc["close"].astype(float))
    rc = dc["log_close"].diff().dropna()
    a1["a1"]["calendar_rule_sensitivity"] = {
        "vol_ann_pct": float(100 * rc.std() * np.sqrt(252)),
        "n_sessions": int(len(dc)),
        "note": "v1 rule rebuilt from contract_registry_v3; thin first ~2 weeks of each quarter"}
except Exception as e:  # noqa: BLE001
    a1["a1"]["calendar_rule_sensitivity"] = {"NOT_RUN": True, "reason": repr(e)[:300]}

# ---- switch-day NEW-4-class descriptive (M2 ii b), from held chain
sw_idx = held[held["held"] != held["held"].shift()].index.tolist()[1:]
dsw = d.copy()
dsw["is_switch"] = dsw.index.isin(sw_idx)
gap_abs = dsw["ret"].abs()
m2sw = {
    "switch": {"n": int(dsw["is_switch"].sum()),
               "median_abs_gap_bp": float(gap_abs[dsw["is_switch"]].median() * 1e4),
               "p90_abs_gap_bp": float(gap_abs[dsw["is_switch"]].quantile(.9) * 1e4)},
    "non_switch": {"n": int((~dsw["is_switch"] & gap_abs.notna()).sum()),
                   "median_abs_gap_bp": float(gap_abs[~dsw["is_switch"]].median() * 1e4),
                   "p90_abs_gap_bp": float(gap_abs[~dsw["is_switch"]].quantile(.9) * 1e4)}}
m2sw["ratio_median_switch_vs_non"] = (m2sw["switch"]["median_abs_gap_bp"]
                                      / m2sw["non_switch"]["median_abs_gap_bp"])
m2sw["flag_gt_2x"] = bool(m2sw["ratio_median_switch_vs_non"] > 2.0)
with open(f"{OUT}/m2_expwitch_anatomy_v3.json") as f:
    m2j = json.load(f)
m2j["integrity"]["switch_day_descriptive_NEW4_class"] = m2sw
jdump(m2j, f"{OUT}/m2_expwitch_anatomy_v3.json")

# ---- a2 on v3
ERAS = [("2010-06_2012-12", "2010-06-07", "2012-12-31"),
        ("2013-01_2016-09", "2013-01-01", "2016-09-30"),
        ("2017-01_2020-02", "2017-01-01", "2020-02-21"),
        ("2020-03_2020-05", "2020-03-01", "2020-05-31"),
        ("2020-06_2022-12", "2020-06-01", "2022-12-30"),
        ("2023-01_2026-09", "2023-01-01", "2026-10-01")]
SEG_LIST = ["ovn_evening", "ovn_overnight", "ovn_preopen", "rth_open30",
            "rth_morning", "rth_lunch", "rth_afternoon", "rth_cashclose_ext",
            "vol_close_tail_1615"]
SEG_LIST = [s.replace("vol_", "") for s in SEG_LIST]
OVN = ["ovn_evening", "ovn_overnight", "ovn_preopen"]
a2 = {}
a2["held_sessions"] = int(len(hs))
a2["clean_sessions"] = int(hs["clean"].sum())
a2["excluded_low_coverage"] = int((~hs["clean"]).sum())
a2["note_exclusions"] = ("v3 rebuild: hole-era sessions (2020-03..05) now real; "
                         "low-coverage exclusions remain at coverage < 0.6")
era_out = {}
for name, a, b in ERAS:
    w = hs[(hs["d"] >= a) & (hs["d"] <= b) & hs["clean"]]
    if not len(w):
        continue
    segs = {}
    tot = sum(w[f"vol_{s}"] for s in SEG_LIST)
    for s in SEG_LIST:
        share = w[f"vol_{s}"] / tot
        segs[s] = {"vol_share_mean": float(share.mean()),
                   "vol_share_median": float(share.median()),
                   "rng_median_pts": float(w[f"rng_{s}"].median() / 1e9)}
    era_out[name] = {"n_sessions": int(len(w)), "segments": segs,
                     "ovn_share_mean": float(sum(segs[s]["vol_share_mean"] for s in OVN)),
                     "rth_core_share_mean": float(sum(segs[s]["vol_share_mean"]
                                                      for s in ["rth_open30", "rth_morning",
                                                                "rth_lunch", "rth_afternoon"])),
                     "open30_plus_morning90": float(segs["rth_open30"]["vol_share_mean"]
                                                    + segs["rth_morning"]["vol_share_mean"]),
                     "avg_session_volume": float(w["volume"].mean())}
a2["era_segments"] = era_out
ys = []
for y, g in hs[hs["clean"]].groupby(hs["d"].dt.year):
    tot = sum(g[f"vol_{s}"] for s in SEG_LIST)
    ovn = sum(g[f"vol_{s}"] for s in OVN)
    ys.append({"year": int(y), "ovn_share": float((ovn / tot).mean()),
               "open30_share": float((g["vol_rth_open30"] / tot).mean()),
               "avg_vol": float(g["volume"].mean())})
a2["yearly_overnight_share"] = ys
prof = {}
for name, a, b in ERAS:
    w = dfh[(dfh["d"] >= a) & (dfh["d"] <= b)]
    if not len(w):
        continue
    sv = w.groupby("minute_of_day")["vol"].sum()
    sv = sv / sv.sum()
    sr = w.groupby("minute_of_day")["r1"].mean()
    prof[name] = {"vol_share_by_minute": {int(k): float(v) for k, v in sv.items()},
                  "absret_by_minute": {int(k): float(v) for k, v in sr.items()}}
a2["minute_profiles"] = prof
hours = [(8*60+30, 9*60), (9*60, 10*60), (10*60, 11*60), (11*60, 12*60),
         (12*60, 13*60), (13*60, 14*60), (14*60, 15*60), (15*60, 16*60)]
u = {}
for name, a, b in ERAS:
    w = dfh[(dfh["d"] >= a) & (dfh["d"] <= b)]
    if not len(w):
        continue
    row = {}
    for h0, h1 in hours:
        mm = w[(w["minute_of_day"] >= h0) & (w["minute_of_day"] < h1)]
        row[f"{h0//60:02d}{h0%60:02d}-{h1//60:02d}{h1%60:02d}"] = {
            "vol_share": float(mm["vol"].sum() / w["vol"].sum()),
            "absret_mean": float(mm["r1"].mean())}
    u[name] = row
a2["rth_hourly"] = u
hs["close_min"] = hs["d"].map(era_close_min)
shorts = hs[(hs["rth_coverage"].fillna(0) > 0.3)
            & (hs["last_min"] < hs["close_min"] - 45)].copy()
fri_era = ((shorts["d"].dt.dayofweek == 4) & (shorts["d"] < "2012-12-01")
           & (shorts["last_min"] < 930))
a2["friday_early_close_eraA"] = {
    "n_sessions": int(fri_era.sum()),
    "window": "2010-06-07..2012-11 era-A Friday 15:15 CT (measured per-session)",
    "close_minute_ct": "15:15 CT", "mon_thu_close_ct": "16:15 CT in the same era"}
shorts2 = shorts[~fri_era]
sv_norm = []
for r_ in shorts2.itertuples():
    yr = r_.d.year
    peers = hs[hs["clean"] & (hs["d"].dt.year == yr)
               & (hs["last_min"] >= hs["close_min"] - 45)]
    if len(peers):
        sv_norm.append(float(r_.volume / peers["volume"].median()))
a2["holiday_short_sessions"] = {
    "n": int(len(shorts2)),
    "method": "last trade minute >=45min before the era's close, coverage otherwise clean",
    "dates": [{"date": str(r_.session_date), "last_min": int(r_.last_min),
               "close_min": int(r_.close_min)} for r_ in shorts2.itertuples()],
    "volume_vs_year_median": {"median": float(np.median(sv_norm)) if sv_norm else None,
                              "n": len(sv_norm)}}
a1["a2"] = a2
jdump(a1, f"{OUT}/nq_f3_rebuild_a1a2.json")

# consistency cross-check vs readiness lane's held_daily_v3
try:
    hdv3 = pd.read_parquet(f"{CACHE}/nq_held_daily_v3.parquet")
    merged = d[["d", "ret"]].merge(hdv3[["d", "ret"]], on="d", suffixes=("_rebuild", "_readiness"))
    both = merged.dropna()
    maxdiff = float((both["ret_rebuild"] - both["ret_readiness"]).abs().max())
    a1["crosscheck_held_daily_v3"] = {
        "n_compared": int(len(both)),
        "max_abs_ret_diff": maxdiff,
        "n_ret_rebuild_nonnan": int(d["ret"].notna().sum()),
        "n_ret_readiness_nonnan": int(hdv3["ret"].notna().sum())}
    jdump(a1, f"{OUT}/nq_f3_rebuild_a1a2.json")
except Exception as e:  # noqa: BLE001
    a1["crosscheck_held_daily_v3"] = {"NOT_RUN": True, "reason": repr(e)[:200]}
    jdump(a1, f"{OUT}/nq_f3_rebuild_a1a2.json")

print("ALL MISSIONS DONE", flush=True)
