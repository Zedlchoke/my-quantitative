"""A7-DEEP-6J audit recompute, stages E-H: term structure / CIP / OI-lead /
events (MOF, BoJ) / CoT / MOF raw-CSV reconstruction. READ-ONLY on data."""
from __future__ import annotations

import csv
import glob
import json
import os
import re

import numpy as np
import pandas as pd

DATA_ROOT = "/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim"
NONPRICE = "/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms"
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "a7_cache")
OUTRIGHT_RE = re.compile(r"^6J[FGHJKMNQUVXZ]\d$")
MONTH_CODE = {"F": 1, "G": 2, "H": 3, "J": 4, "K": 5, "M": 6,
              "N": 7, "Q": 8, "U": 9, "V": 10, "X": 11, "Z": 12}
MOF_OPS = ["2022-09-22", "2022-10-21", "2022-10-24", "2024-04-29", "2024-05-01",
           "2024-07-11", "2024-07-12", "2026-04-30", "2026-05-04", "2026-05-06"]


def main():
    res = {}
    sess = pd.read_parquet(os.path.join(CACHE, "sessions.parquet"))
    held = pd.read_parquet(os.path.join(CACHE, "held_daily_coded.parquet"))
    reg = pd.read_json(glob.glob(os.path.join(
        "/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep/"
        "research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/6J_cache/"
        "contract_registry.json"))[0])
    # use own registry for expiries
    exp = {}
    for _, r in reg.iterrows():
        exp[r["contract"]] = pd.Timestamp(r["expiry"])

    # ---------- E: term structure ----------
    q = sess[sess["contract"].str.match(r"^6J[HMUZ]\d_\d{4}$")].copy()
    q["d"] = pd.to_datetime(q["session_date"])
    q["exp"] = q["contract"].map(exp)
    tot = sess.copy()
    tot["year"] = pd.to_datetime(tot["session_date"]).dt.year
    tot["is_q"] = tot["contract"].str.match(r"^6J[HMUZ]\d_\d{4}$")
    res["E_serial_share_pct_by_year"] = {
        str(y): float(100 * g.loc[~g["is_q"], "volume"].sum() / g["volume"].sum())
        for y, g in tot.groupby("year")}

    closes = q.pivot_table(index="d", columns="contract", values="close")
    bars = q.pivot_table(index="d", columns="contract", values="n_bars")
    vols = q.pivot_table(index="d", columns="contract", values="volume")
    qcons = sorted(closes.columns, key=lambda c: exp[c])
    pairs = []
    for a, b in zip(qcons[:-1], qcons[1:]):
        m = (closes[a].notna() & closes[b].notna()
             & bars[a].fillna(0).ge(30) & bars[b].fillna(0).ge(30))
        if m.sum() < 50:
            continue
        sp = (closes.loc[m, a] - closes.loc[m, b]) / 5e-7
        pairs.append({"near": a, "far": b, "n": int(m.sum()),
                      "pct_near_below_far": float(100 * (sp < 0).mean()),
                      "median_ticks": float(sp.median())})
    res["E_pairs"] = pairs
    res["E_pair_summary"] = {
        "n_pairs": len(pairs),
        "n_at_100pct": sum(p["pct_near_below_far"] == 100 for p in pairs),
        "median_of_medians_ticks": float(np.median([p["median_ticks"] for p in pairs])),
        "n_range": [min(p["n"] for p in pairs), max(p["n"] for p in pairs)],
        "median_ticks_range": [min(p["median_ticks"] for p in pairs),
                               max(p["median_ticks"] for p in pairs)]}

    held = held.sort_values("session_date").reset_index(drop=True)
    held["d"] = pd.to_datetime(held["session_date"])
    sw = held[held["contract"] != held["contract"].shift()].iloc[1:]
    rolls = []
    for i, row in sw.iterrows():
        new, old = row["contract"], held.loc[i - 1, "contract"]
        rdate = row["d"]
        both = closes[old].notna() & closes[new].notna()
        ti = both.index[both.values]
        ti = ti[ti <= rdate]
        t_last = ti.max() if len(ti) else None
        if t_last is not None:
            gap_ticks = (closes.loc[t_last, new] - closes.loc[t_last, old]) / 5e-7
            gap_pct = closes.loc[t_last, new] / closes.loc[t_last, old] - 1
        else:
            gap_ticks = gap_pct = np.nan
        dte = (exp[new] - exp[old]).days
        # raw volume crossover (per lane logic: within +-16d window)
        win = pd.date_range(rdate - pd.Timedelta(days=16), rdate + pd.Timedelta(days=16))
        vo = vols.loc[vols.index.isin(win), old]
        vn = vols.loc[vols.index.isin(win), new]
        bd = pd.DataFrame({"o": vo, "n": vn}).dropna()
        bd = bd[(bd["o"] > 0) | (bd["n"] > 0)]
        cross = bd.index[bd["n"] > bd["o"]]
        fx = cross.min() if len(cross) else None
        rolls.append({"switch": str(rdate.date()), "old": old, "new": new,
                      "gap_measured": str(t_last.date()) if t_last is not None else None,
                      "gap_ticks": float(gap_ticks),
                      "gap_pct": float(gap_pct),
                      "gap_ann_pct": float(100 * gap_pct * 365.0 / dte),
                      "vol_cross": str(fx.date()) if fx is not None else None,
                      "vol_cross_days_before_old_expiry": (
                          int((exp[old] - fx).days) if fx is not None else None),
                      "switch_days_before_old_expiry": int((exp[old] - rdate).days)})
    res["E_rolls"] = rolls
    gaps = [r["gap_ticks"] for r in rolls]
    res["E_roll_summary"] = {
        "n": len(rolls), "n_measured": len([g for g in gaps if np.isfinite(g)]),
        "positive": int(sum(g > 0 for g in gaps)),
        "negative": int(sum(g <= 0 for g in gaps)),
        "negatives": [(r["switch"], r["gap_ticks"]) for r in rolls if r["gap_ticks"] <= 0],
        "median_ticks": float(np.median(gaps)),
        "median_gap_pct": float(np.median([r["gap_pct"] for r in rolls])),
        "gap_ann_pct_by_year": {}}
    gy = {}
    for r in rolls:
        gy.setdefault(r["switch"][:4], []).append(r["gap_ann_pct"])
    res["E_roll_summary"]["gap_ann_pct_by_year"] = {
        y: {"median": float(np.median(v)),
            "min": float(min(v)), "max": float(max(v)), "n": len(v)}
        for y, v in sorted(gy.items())}
    res["E_vol_cross_days_before_expiry"] = sorted(
        [r["vol_cross_days_before_old_expiry"] for r in rolls
         if r["vol_cross_days_before_old_expiry"] is not None])

    # CIP
    tb = pd.read_parquet(f"{NONPRICE}/normalized/fred_latest_tidy.parquet")
    tb = tb[tb["series_id"] == "FRED_DTB3"].copy()
    tb["obs"] = pd.to_datetime(tb["observation_period"])
    tbm = tb.groupby(tb["obs"].dt.to_period("M"))["value"].mean()
    rows = []
    for r in rolls:
        m = pd.Period(r["switch"][:7], freq="M")
        if m in tbm.index:
            rows.append({"switch": r["switch"], "usd3m": float(tbm[m]),
                         "implied_jpy": float(tbm[m] - r["gap_ann_pct"])})
    by = {}
    for x in rows:
        by.setdefault(x["switch"][:4], []).append(x["implied_jpy"])
    res["E_cip"] = {"n": len(rows),
                    "implied_jpy_median_by_year": {
                        y: float(np.median(v)) for y, v in sorted(by.items())}}

    # OI migration + lead of OI cross over raw volume cross
    stats_files = sorted(glob.glob(f"{DATA_ROOT}/parquet/AV1T-statistics-ALL10/*.parquet"))
    oi = None
    for f in stats_files:
        d = pd.read_parquet(f)
        d = d[(d["stat_type"] == 9) & d["raw_symbol"].str.fullmatch(OUTRIGHT_RE)]
        oi = d if oi is None else pd.concat([oi, d])
    oi["d"] = pd.to_datetime(pd.to_datetime(oi["ts_ref"], unit="ns", utc=True).dt.date)
    piv = oi.pivot_table(index="d", columns="raw_symbol", values="quantity")
    leads = []
    for r in rolls:
        rd = pd.Timestamp(r["switch"])
        if rd < pd.Timestamp("2023-10-01"):
            continue
        olds, news = r["old"].split("_")[0], r["new"].split("_")[0]
        if olds not in piv.columns or news not in piv.columns:
            continue
        win = pd.date_range(rd - pd.Timedelta(days=20), rd + pd.Timedelta(days=20))
        sub = piv.loc[piv.index.isin(win), [olds, news]].dropna()
        if len(sub) < 5:
            continue
        oc = sub.index[sub[news] > sub[olds]]
        foci = oc.min() if len(oc) else None
        vc = pd.Timestamp(r["vol_cross"]) if r["vol_cross"] else None
        leads.append({
            "switch": r["switch"], "oi_cross": str(foci.date()) if foci is not None else None,
            "vol_cross": r["vol_cross"],
            "oi_lead_days_vs_vol_cross": (int((vc - foci).days)
                                          if (foci is not None and vc is not None) else None),
            "oi_cross_days_before_switch": (int((rd - foci).days)
                                            if foci is not None else None)})
    res["E_oi_leads"] = leads
    ld = [x["oi_lead_days_vs_vol_cross"] for x in leads
          if x["oi_lead_days_vs_vol_cross"] is not None]
    res["E_oi_lead_summary"] = {
        "n": len(ld), "min": min(ld), "max": max(ld),
        "n_in_3_7": sum(3 <= x <= 7 for x in ld),
        "values": sorted(ld)}

    # Sep-2026 exemplar
    z = vols["6JZ6_2026"].loc["2026-08-25":"2026-09-20"]
    u = vols["6JU6_2026"].loc["2026-08-25":"2026-09-20"]
    share = (z / (u + z) * 100).round(1)
    res["E_sep2026"] = {str(k.date()): float(v) for k, v in share.dropna().items()}
    u_last = sess[(sess["contract"] == "6JU6_2026")].sort_values("session_date").tail(2)
    res["E_sep2026_u6_final"] = [
        {"date": str(r["session_date"]), "bars": int(r["n_bars"]),
         "volume": int(r["volume"])} for _, r in u_last.iterrows()]

    # ---------- F: events (MOF op days, BoJ MPM) ----------
    m = held.copy()
    m["log_close"] = np.log(m["close"].astype(float))
    m["ret_within"] = m["log_close"] - m.groupby("contract")["log_close"].shift(1)
    m["vol_med21"] = m["volume"].shift(1).rolling(21, min_periods=10).median()
    m = m.reset_index(drop=True)
    tr_pct = []
    for i in range(len(m)):
        if i > 20:
            tr_pct.append(float((m["high"].iloc[max(0, i - 126):i] - m["low"].iloc[max(0, i - 126):i]).max()
                                and ((m["high"].iloc[max(0, i - 126):i] - m["low"].iloc[max(0, i - 126):i])
                                     < (m["high"].iloc[i] - m["low"].iloc[i])).mean()))
        else:
            tr_pct.append(np.nan)
    # simpler true range via prev close (session has prev_close? recompute)
    m["prev_close"] = m.groupby("contract")["close"].shift(1)
    tr = pd.concat([(m["high"] - m["prev_close"]).clip(lower=0),
                    (m["prev_close"] - m["low"]).clip(lower=0),
                    m["high"] - m["low"]], axis=1).max(axis=1)
    m["tr"] = tr
    m["tr_pct126"] = [float((m["tr"].iloc[max(0, i - 126):i] < m["tr"].iloc[i]).mean())
                      if i > 20 else np.nan for i in range(len(m))]

    mof = pd.read_parquet(f"{NONPRICE}/normalized/mof_intervention_tidy.parquet")
    mof["op_date"] = pd.to_datetime(mof["observation_period"])
    ops = mof[(mof["op_date"] >= "2020-01-01") & (mof["direction"] == "JPY_buying")]
    res["F_mof_parquet_ops"] = [
        {"date": str(r["op_date"].date()), "yen_bn": float(r["value_yen_100m"]) / 10.0}
        for _, r in ops.iterrows()]
    res["F_mof_parquet_meta"] = {
        "n_total": int(len(mof)), "span": f"{mof['op_date'].min().date()}..{mof['op_date'].max().date()}",
        "n_jpy_buying": int((mof["direction"] == "JPY_buying").sum())}

    # per-op anatomy incl the hidden 2022-10-24 and pending 07-30
    ann = pd.read_parquet(os.path.join(CACHE, "annotated.parquet"))
    hmap = dict(zip(pd.read_parquet(os.path.join(CACHE, "held_daily_coded.parquet"))["session_date"],
                    pd.read_parquet(os.path.join(CACHE, "held_daily_coded.parquet"))["contract"]))
    ah = ann[ann["session_date"].map(hmap).notna()]
    ah = ah[ah["contract"] == ah["session_date"].map(hmap)]
    ah = ah.copy()
    ah["range_px"] = (ah["high"].astype(float) - ah["low"].astype(float)) * 1e-9
    op_rows = []
    for ds in MOF_OPS + ["2026-07-30"]:
        row = m[m["session_date"].astype(str) == ds]
        if not len(row):
            op_rows.append({"date": ds, "note": "no held session"})
            continue
        r = row.iloc[0]
        bar = ah[ah["session_date"].astype(str) == ds]
        b1 = bar.nlargest(1, "volume").iloc[0]
        cts = {tz: f"{b1['minute_' + tz] // 60:02d}:{b1['minute_' + tz] % 60:02d}"
               for tz in ("tokyo", "london", "ny")}
        op_rows.append({
            "date": ds, "ret_pct": float(100 * r["ret_within"]) if pd.notna(r["ret_within"]) else None,
            "vol_x21": float(r["volume"] / r["vol_med21"]) if pd.notna(r["vol_med21"]) else None,
            "tr_pct126": float(r["tr_pct126"]),
            "session_vol": int(r["volume"]),
            "burst1_utc": str(b1["dt"]), "burst1_vol": int(b1["volume"]),
            "burst1_local": cts})
    res["F_op_anatomy"] = op_rows
    res["F_max_vol_session"] = {
        "date": str(m.loc[m["volume"].idxmax(), "session_date"]),
        "volume": int(m["volume"].max())}

    # BoJ MPM days
    boj = pd.read_parquet(f"{NONPRICE}/normalized/boj_fomc_statement_inventory.parquet")
    res["F_boj_inventory_cols"] = boj.columns.tolist()[:8]
    # statements archive
    dec = {}
    for f in sorted(glob.glob(f"{NONPRICE}/boj/statements/*/k*a.*")):
        b = os.path.basename(f)
        mm = re.fullmatch(r"k(\d{2})(\d{2})(\d{2})a\.(?:html|pdf|htm)", b)
        if mm:
            dec[f"20{mm.group(1)}-{mm.group(2)}-{mm.group(3)}"] = b
    mpm_dates = sorted(d for d in dec
                       if "2020-01-01" <= d <= "2026-09-30")
    mm_rows = []
    for ds in mpm_dates:
        row = m[m["session_date"].astype(str) == ds]
        if not len(row):
            continue
        r = row.iloc[0]
        mm_rows.append({"date": ds,
                        "abs_ret": float(abs(100 * r["ret_within"])) if pd.notna(r["ret_within"]) else None,
                        "vol_x": float(r["volume"] / r["vol_med21"]) if pd.notna(r["vol_med21"]) else None})
    mdf = pd.DataFrame(mm_rows).dropna()
    res["F_boj_mpm"] = {
        "n_decisions_2020_2026": len(mpm_dates), "n_measured": int(len(mdf)),
        "median_abs_ret_pct": float(mdf["abs_ret"].median()),
        "alldays_median_abs_ret_pct": float(100 * m["ret_within"].abs().median()),
        "median_vol_x": float(mdf["vol_x"].median())}
    # 2026-09-18 volume check
    sep26 = m[m["session_date"].astype(str).str.startswith("2026-09")].sort_values("session_date")
    res["F_sep2026_top_vol_days"] = [
        {"date": str(r["session_date"]), "volume": int(r["volume"])}
        for _, r in sep26.nlargest(3, "volume").iterrows()]

    # ---------- G: CoT ----------
    cot = pd.read_parquet(f"{NONPRICE}/normalized/cftc_legacy_tidy.parquet")
    j = cot[cot["series_id"] == "COT_LEGACY_6J"].copy()
    j["obs_date"] = pd.to_datetime(j["observation_period"])
    j["net"] = j["noncomm_long"] - j["noncomm_short"]
    j = j.sort_values("obs_date").reset_index(drop=True)
    res["G_cot"] = {
        "n_weeks": int(len(j)),
        "span": f"{j['obs_date'].min().date()}..{j['obs_date'].max().date()}",
        "net_min": int(j["net"].min()),
        "net_min_date": str(j.loc[j["net"].idxmin(), "obs_date"].date()),
        "net_max": int(j["net"].max()),
        "net_max_date": str(j.loc[j["net"].idxmax(), "obs_date"].date()),
        "min_2024": int(j[j["obs_date"].dt.year == 2024]["net"].min()),
        "min_2024_date": str(j.loc[j[(j["obs_date"].dt.year == 2024)]["net"].idxmin(), "obs_date"].date()),
        "rank_of_-163412": int((j["net"] < -163412).sum() + 1),
        "net_2026_07_28": int(j[j["obs_date"] == "2026-07-28"]["net"].iloc[0]),
        "swing_2024min_to_2025max": int(j["net"].max() - j[j["obs_date"].dt.year == 2024]["net"].min()),
        "oi_median_2020": float(j[j["obs_date"].dt.year == 2020]["open_interest_all"].median()),
        "oi_median_2026": float(j[j["obs_date"].dt.year == 2026]["open_interest_all"].median()),
        "prev_record_before_2024": {
            "net_min_pre2024": int(j[j["obs_date"] < "2024-01-01"]["net"].min()),
            "date": str(j.loc[j[j["obs_date"] < "2024-01-01"]["net"].idxmin(), "obs_date"].date())}}
    # z at 2026-07-28 (trailing 150wk strict past)
    mu = j["net"].rolling(150, min_periods=100).mean().shift(1)
    sd = j["net"].rolling(150, min_periods=100).std().shift(1)
    z = (j["net"] - mu) / sd
    res["G_cot"]["z_2026_07_28"] = float(z[j["obs_date"] == "2026-07-28"].iloc[0])

    # ---------- H: MOF raw CSV reconstruction ----------
    rows = []
    with open(f"{NONPRICE}/mof/foreign_exchange_intervention_operations.csv",
              encoding="shift-jis", errors="replace") as f:
        for row in csv.reader(f):
            rows.append(row)
    daily, cur_y, cur_m = [], None, None
    for r in rows:
        if len(r) < 9 or "期計" in r[0]:
            # aggregate row: may still carry nothing daily
            if len(r) > 3 and re.fullmatch(r"\d{4}", r[3].strip()):
                cur_y, cur_m = int(r[3]), None
            continue
        val = r[6].replace(",", "").strip()
        if not val or not r[8].strip():
            continue
        if re.fullmatch(r"\d{4}", r[3].strip()):
            cur_y = int(r[3])
        MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug",
               "Sep", "Oct", "Nov", "Dec"]
        if r[4].strip()[:3] in MON:
            cur_m = MON.index(r[4].strip()[:3]) + 1
        day_s = re.sub(r"\D", "", r[5])
        if not day_s or cur_y is None or cur_m is None:
            continue
        day = int(day_s)
        daily.append({"y": cur_y, "m": cur_m, "d": day,
                      "yen_100m": float(val),
                      "dir": "buy" if "bought" in r[8] else "sell"})
    dd = pd.DataFrame(daily)
    dd["date"] = pd.to_datetime(dict(year=dd["y"], month=dd["m"], day=dd["d"]), errors="coerce")
    res["H_csv_daily_rows"] = int(len(dd))
    res["H_csv_span"] = f"{dd['date'].min().date()}..{dd['date'].max().date()}"
    res["H_csv_n_buying"] = int((dd["dir"] == "buy").sum())
    # rows in CSV but not in parquet
    parq = set(mof["op_date"].dt.date)
    miss = dd[~dd["date"].dt.date.isin(parq)]
    res["H_in_csv_not_in_parquet"] = [
        {"date": str(r["date"].date()), "yen_bn": r["yen_100m"] / 10, "dir": r["dir"]}
        for _, r in miss.iterrows()]
    # rows in parquet not in CSV
    csv_dates = set(dd["date"].dt.date)
    extra = mof[~mof["op_date"].dt.date.isin(csv_dates)]
    res["H_in_parquet_not_in_csv"] = [str(x.date()) for x in extra["op_date"]]
    res["H_q4_2022_check"] = {
        "oct21_plus_oct24": 56202 + 7296,
        "quarterly_total_row": 63499}

    with open(os.path.join(HERE, "a7_events_results.json"), "w") as fh:
        json.dump(res, fh, indent=1, default=str)
    print("EVENTS COMPLETE")


if __name__ == "__main__":
    main()
