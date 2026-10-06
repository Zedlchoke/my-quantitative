#!/usr/bin/env python
"""ES deep-research v2 — contract-daily panel, PIT chains, roll/term structure
(lane DEEP-ES, task FUTURES-DEEPRESEARCH-V2-20261003).

DESCRIPTIVE ONLY. Builds:
  ES_cache/es_contract_daily.parquet  per contract x session_date aggregates
  ES_cache/es_chain_daily.parquet     continuous chains (see rules) + marks
  ES_roll_termstructure.json          roll table + gap/migration descriptives

Chain rules (all PIT-legal, thresholds strict-past):
  VOL  : hold contract with max PRIOR-session total volume among the two
         nearest quarterlies (lag-1 volume crossover; ties -> nearer expiry)
  T5   : calendar roll at close 5 trading sessions before the delivery-month
         expiry session (expiry session = observed last-trade session when the
         contract expired in-window, else definitions expiry)
  DECL : v1 data-lane declared rule - last session before day-1 of the
         delivery month
  OI   : same as VOL but using prior published open interest (statistics
         stat_type=9, ts_ref = positions date; usable 2023-10+ only)

Back-adjustment: multiplicative (ratio) factors at switch sessions; unadjusted
levels also kept. Daily marks from the 1m panel: session close = last 1m close
at/ before 16:00 Chicago; RTH open = first bar open >= 08:30; RTH close = last
bar close < 15:00 ("NY cash close") and < 16:00 ("RTH close"); overnight close
= last bar close < 08:30; session open = first bar of the 17:00-> session.

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python ES_chains.py
"""
import json
import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "ES_cache")
NS = 1_000_000_000.0

# ------------------------------------------------------------ load 1m panel
m = pd.read_parquet(os.path.join(CACHE, "es_1m_outright.parquet"))
meta = json.load(open(os.path.join(CACHE, "es_contracts.json")))
contracts = {c["instrument_id"]: c for c in meta["contracts"]}
m["delivery"] = m["instrument_id"].map(lambda i: contracts[i]["delivery"])
m["delivery_ord"] = pd.PeriodIndex(m["delivery"], freq="Q").astype("int64")
chi = pd.DatetimeIndex(pd.to_datetime(m["ts_event"], unit="ns", utc=True)) \
    .tz_convert("America/Chicago")
m["chi"] = chi
m["sess"] = chi + pd.to_timedelta((chi.hour >= 17).astype("int64"), unit="D")
m["sess"] = pd.DatetimeIndex(m["sess"]).normalize().tz_localize(None)
m["hhmm"] = chi.hour * 100 + chi.minute
m["minute_of_sess"] = np.where(
    chi.hour >= 17, (chi.hour - 17) * 60 + chi.minute,
    (chi.hour + 7) * 60 + chi.minute)   # 17:00 = 0 .. next 16:59 = 1379
SEG = np.where(m["hhmm"] >= 1700, "ON", np.where(m["hhmm"] >= 1600, "BRK",
        np.where(m["hhmm"] >= 830, "RTH", "ON")))

# session close proxy = minute 1379 (=15:59->16:00 bar); allow 1375..1379
# use closes of last bars: for marks we take per (contract,sess) aggregates.
for col in ("open", "high", "low", "close"):
    m[col] = m[col] / NS

m["seg"] = SEG
m.to_parquet(os.path.join(CACHE, "es_1m_seg.parquet"), index=False)
print("1m rows:", len(m))

# ------------------------------------------------- contract x day aggregates
g = m.groupby(["instrument_id", "sess", "seg"], sort=True)
agg = g.agg(vol=("volume", "sum"), n_bars=("volume", "size"),
            hi=("high", "max"), lo=("low", "min")).reset_index()
cd = agg.pivot_table(index=["instrument_id", "sess"], columns="seg",
                     values=["vol", "n_bars", "hi", "lo"]).reset_index()
cd.columns = [f"{a}_{b}".strip("_") for a, b in cd.columns]
cd = cd.rename(columns={"vol_ON": "vol_on", "vol_RTH": "vol_rth",
                        "vol_BRK": "vol_brk",
                        "n_bars_ON": "nb_on", "n_bars_RTH": "nb_rth",
                        "n_bars_BRK": "nb_brk",
                        "hi_ON": "hi_on", "lo_ON": "lo_on",
                        "hi_RTH": "hi_rth", "lo_RTH": "lo_rth"})
cd["vol_total"] = cd[["vol_on", "vol_rth", "vol_brk"]].sum(axis=1, min_count=1)

# session marks per contract-day (from raw bars, exact)
marks = m.groupby(["instrument_id", "sess"]).apply(
    lambda x: pd.Series({
        "sess_open": x["open"].iloc[0],
        "sess_close": x["close"].iloc[-1],
        "rth_open": x.loc[x["seg"] == "RTH", "open"].iloc[0]
            if (x["seg"] == "RTH").any() else np.nan,
        "rth_close16": x.loc[(x["seg"] == "RTH"), "close"].iloc[-1]
            if (x["seg"] == "RTH").any() else np.nan,
        "cash_close15": x.loc[(x["seg"] == "RTH") & (x["hhmm"] < 1500),
                              "close"].iloc[-1]
            if ((x["seg"] == "RTH") & (x["hhmm"] < 1500)).any() else np.nan,
        "on_close": x.loc[x["seg"] == "ON", "close"].iloc[-1]
            if (x["seg"] == "ON").any() else np.nan,
        "hh_lo": x["low"].min(), "hh_hi": x["high"].max(),
    }), include_groups=False).reset_index()
cd = cd.merge(marks, on=["instrument_id", "sess"])
cd["symbol"] = cd["instrument_id"].map(lambda i: contracts[i]["symbol"])
cd["delivery"] = cd["instrument_id"].map(lambda i: contracts[i]["delivery"])
cd.to_parquet(os.path.join(CACHE, "es_contract_daily.parquet"), index=False)
print("contract-days:", len(cd))

# ---------------------------------------------------------- session calendar
# a session exists if ANY contract traded; union across contracts
all_sess = sorted(cd["sess"].unique())
sess_ix = pd.DatetimeIndex(all_sess)
print("sessions:", len(all_sess), all_sess[0].date(), "->", all_sess[-1].date())

# expiry session per delivery: observed last-trade session for contracts that
# expired inside the window; vendor definitions expiry for still-listed.
expiry_of = {}
for c in meta["contracts"]:
    if c.get("definition_expiration") and c.get("still_listed"):
        expiry_of[c["delivery"]] = c["definition_expiration"][:10]
    elif c.get("last_volume_session"):
        expiry_of[c["delivery"]] = c["last_volume_session"]
    elif c.get("definition_expiration"):
        expiry_of[c["delivery"]] = c["definition_expiration"][:10]

# REAL liquid quarterlies only: a contract counts for chains/rolls if it ever
# traded >=100k contracts in a single session (true fronts do; the 2027
# deferred tails with 1-2 stray prints never do).
maxday = cd.groupby("delivery")["vol_total"].max()
real = sorted([d for d, v in maxday.items() if v >= 100_000])
print("real liquid deliveries:", len(real), real[0], "->", real[-1])
deliveries = real

# trading-day index for calendar rules
tdf = pd.DataFrame({"sess": sess_ix})
tdf["i"] = np.arange(len(tdf))
sess_pos = dict(zip(tdf["sess"], tdf["i"]))

def sessions_before(datestr, n):
    """the n-th trading session strictly before `datestr`'s session."""
    d = pd.Timestamp(datestr)
    pos = sess_pos.get(d)
    if pos is None:
        pos = tdf["i"][tdf["sess"] < d].iloc[-1]
    return tdf["sess"].iloc[pos - n].date().isoformat() if pos - n >= 0 else None

# ------------------------------------------------------------ chain rules
piv = cd.pivot_table(index="sess", columns="delivery", values="vol_total")
piv.index = pd.DatetimeIndex(piv.index)

def initial_front(rule, s0):
    """Front contract at the first session under each rule."""
    if rule == "DECL":
        for d in deliveries:
            y, mo = int(d[:4]), int(d[5:7])
            first_next = pd.Timestamp(year=y, month=mo, day=1)
            prior = tdf[tdf["sess"] < first_next]
            sw = prior["sess"].iloc[-1] if len(prior) else None
            if sw is not None and sw >= s0:
                return d
        return deliveries[-1]
    return deliveries[0]

def build_chain(rule):
    """returns DataFrame(sess, front_delivery) using strict-past info only."""
    rows = []
    cur = None
    dl = deliveries
    for s in piv.index:
        if cur is None:
            cur = initial_front(rule, s)
            rows.append((s, cur))
            continue
        if rule == "VOL":
            cands = [d for d in dl if d >= cur][:2]
            prev = piv.index[piv.index < s]
            if len(prev) and len(cands) == 2:
                pv = piv.loc[prev[-1]]
                vols = {d: pv.get(d, np.nan) for d in cands}
                vols = {d: v for d, v in vols.items() if not pd.isna(v)}
                if vols:
                    best = max(vols, key=lambda d: (vols[d], -dl.index(d)))
                    if best != cur and dl.index(best) > dl.index(cur):
                        cur = best
        elif rule == "T5":
            sw = sessions_before(expiry_of[cur], 5)
            if (sw is None and cur != dl[-1]) or (sw and s >= pd.Timestamp(sw)):
                nxt = dl[dl.index(cur) + 1] if dl.index(cur) + 1 < len(dl) else cur
                cur = nxt
        elif rule == "DECL":
            y, mo = int(cur[:4]), int(cur[5:7])
            first_next = pd.Timestamp(year=y, month=mo, day=1)
            prior = tdf[tdf["sess"] < first_next]
            sw = prior["sess"].iloc[-1] if len(prior) else None
            if sw is not None and s >= sw and dl.index(cur) + 1 < len(dl):
                cur = dl[dl.index(cur) + 1]
        rows.append((s, cur))
    return pd.DataFrame(rows, columns=["sess", "front"]).set_index("sess")

chains = {r: build_chain(r) for r in ("VOL", "T5", "DECL")}
for r, ch in chains.items():
    print(r, "switches:", (ch["front"] != ch["front"].shift()).sum() - 1)

# OI chain 2023-10+ (statistics): prior published OI per delivery
oi = pd.read_parquet(os.path.join(CACHE, "es_statistics_daily.parquet"))
oi["ref_date"] = pd.to_datetime(oi["ref_date"])
oiq = oi[oi["open_interest"].notna()].pivot_table(
    index="ref_date", columns="symbol", values="open_interest")
# symbol -> delivery
s2d = {c["symbol"]: c["delivery"] for c in meta["contracts"]
       if c["delivery"] >= "2023-10"}
oiq = oiq.rename(columns=s2d)
oiq = oiq.groupby(axis=1, level=0).max() if oiq.columns.duplicated().any() else oiq

def build_oi_chain():
    rows = []
    cur = None
    dl_oi = sorted([d for d in deliveries if d >= "2023-12"])
    for s in piv.index:
        if s < pd.Timestamp("2023-10-15"):
            continue
        if cur is None:
            cur = dl_oi[0]
        else:
            prev = oiq.index[oiq.index < s]
            if len(prev):
                po = oiq.loc[prev[-1]]
                cands = [d for d in dl_oi if d >= cur][:2]
                vals = {d: po.get(d, np.nan) for d in cands}
                vals = {d: v for d, v in vals.items() if not pd.isna(v)}
                if vals:
                    best = max(vals, key=lambda d: (vals[d], -dl_oi.index(d)))
                    if best != cur and dl_oi.index(best) > dl_oi.index(cur):
                        cur = best
        rows.append((s, cur))
    return pd.DataFrame(rows, columns=["sess", "front"]).set_index("sess")

oi_chain = build_oi_chain()
print("OI switches:", (oi_chain["front"] != oi_chain["front"].shift()).sum() - 1)

# ------------------------------------------------------- chain daily marks
cdi = cd.set_index(["sess", "delivery"])

def chain_marks(ch):
    out = []
    for s, d in ch["front"].items():
        try:
            r = cdi.loc[(s, d)]
        except KeyError:
            continue
        out.append({"sess": s, "front": d,
                    "symbol": r["symbol"],
                    "close": r["sess_close"], "open": r["sess_open"],
                    "rth_open": r["rth_open"], "rth_close16": r["rth_close16"],
                    "cash_close15": r["cash_close15"], "on_close": r["on_close"],
                    "hi": r["hh_hi"], "lo": r["hh_lo"],
                    "vol_total": r["vol_total"], "vol_rth": r["vol_rth"],
                    "vol_on": r["vol_on"]})
    df = pd.DataFrame(out).set_index("sess")
    # ratio back-adjustment on session close across switch sessions
    df["switch"] = df["front"] != df["front"].shift()
    adj = 1.0
    adjf = []
    prev_close = None
    for i, (s, r) in enumerate(df.iterrows()):
        if i > 0 and r["switch"]:
            old_close = prev_close            # close of previous front
            new_prev = df["close"].iloc[i - 1]  # same: prev session front close
            # ratio factor uses prev session's two closes? we need the NEW
            # contract's close on the SAME prev session:
            try:
                new_on_prev = cdi.loc[(df.index[i - 1], r["front"])]["sess_close"]
            except KeyError:
                new_on_prev = np.nan
            if pd.notna(old_close) and pd.notna(new_on_prev) and new_on_prev != 0:
                adj *= float(old_close) / float(new_on_prev)
        adjf.append(adj)
        prev_close = r["close"]
    df["ratio_factor"] = adjf
    df["close_adj"] = df["close"] * df["ratio_factor"]
    return df

cm = {r: chain_marks(ch) for r, ch in chains.items()}
cm["OI"] = chain_marks(oi_chain)
for r, df in cm.items():
    df.to_parquet(os.path.join(CACHE, f"es_chain_{r}.parquet"))
    print(r, "chain rows:", len(df))

# ------------------------------------------------------------- roll table
roll_rows = []
volch = cm["VOL"]
for k in range(len(deliveries) - 1):
    d0, d1 = deliveries[k], deliveries[k + 1]
    sub = cd[cd["delivery"] == d1].set_index("sess")
    sub0 = cd[cd["delivery"] == d0].set_index("sess")
    both = sub.index.intersection(sub0.index)
    if len(both) == 0:
        continue
    vv = pd.DataFrame({"old": sub0.loc[both, "vol_total"],
                       "new": sub.loc[both, "vol_total"]}).dropna()
    if vv["new"].max() < 100_000:      # not a real roll (deferred tail)
        continue
    cross = None
    for s in vv.index:
        w = vv.loc[s]
        # require front-scale volume on the NEW contract: deferred stray
        # prints (1-10 lots) must not count as a liquidity crossover
        if w["new"] > w["old"] and w["new"] >= 100_000:
            cross = s
            break
    last8 = vv.tail(8)
    exp_s = pd.Timestamp(expiry_of[d0])
    gap_close = gap_rth = None
    if cross is not None:
        ci = vv.index.get_loc(cross)
        if ci > 0:
            prev_s = vv.index[ci - 1]
            try:
                old_c = sub0.loc[prev_s, "sess_close"]
                new_c = sub.loc[prev_s, "sess_close"]
                old_r = sub0.loc[prev_s, "rth_close16"]
                new_r = sub.loc[prev_s, "rth_close16"]
                gap_close = float(new_c - old_c)
                gap_rth = float(new_r - old_r) if pd.notna(old_r) and pd.notna(new_r) else None
            except KeyError:
                pass
    # OI crossover (statistics era only); require front-scale OI on the new
    # contract (>=500k) - deferred stray OI prints (2-5k lots, calendar-spread
    # artifacts) must not count
    oi_cross = None
    if d0 >= "2023-10":
        try:
            o0 = oiq[d0].dropna()
            o1 = oiq[d1].dropna()
            common = o0.index.intersection(o1.index)
            for s in common:
                if o1[s] > o0[s] and o1[s] >= 500_000:
                    oi_cross = s.date().isoformat()
                    break
        except KeyError:
            pass
    sw_mask = (volch["front"] == d1) & (volch["front"].shift() == d0)
    sw_sess = volch.index[sw_mask]
    # unadjusted switch jump on the VOL chain (old close last held vs new
    # close first held) - what an unadjusted continuous series would embed
    jump = None
    if len(sw_sess):
        i0 = volch.index.get_loc(sw_sess[0])
        prev_close_old = volch["close"].iloc[i0 - 1]
        jump = float(volch["close"].iloc[i0] - prev_close_old)
    roll_rows.append({
        "old": d0, "new": d1,
        "expiry_session": expiry_of[d0],
        "volume_crossover_session": cross.date().isoformat() if cross is not None else None,
        "calendar_days_before_expiry": int((exp_s - cross).days) if cross is not None else None,
        "oi_crossover_session": oi_cross,
        "vol_chain_switch_session": sw_sess[0].date().isoformat() if len(sw_sess) else None,
        "calendar_spread_at_crossover": gap_close,
        "calendar_spread_at_crossover_rthclose": gap_rth,
        "unadjusted_switch_jump": jump,
        "old_vol_on_crossover": int(vv.loc[cross, "old"]) if cross is not None else None,
        "new_vol_on_crossover": int(vv.loc[cross, "new"]) if cross is not None else None,
        "new_share_last8_mean": float((last8["new"] / (last8["new"] + last8["old"])).mean()) if len(last8) else None,
    })
roll = pd.DataFrame(roll_rows)
roll.to_json(os.path.join(CACHE, "es_roll_table.json"), orient="records",
             date_format="iso", indent=1)
print("roll rows:", len(roll))
print(roll.head(3).to_string())
print(roll.tail(3).to_string())
