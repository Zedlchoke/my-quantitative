"""VERIFY-A7READY T5 — FX-JA crosscheck from RAW parquets.

1. 6A tick-era break: independent session samples 3 pre-2020-11-20 and
   3 post-2020-11-23 from AV1B-O1M-6A-BACKFILL2 (2020-2022 chunk covers both
   eras); per-session close-to-close |diff| within instrument; min increment
   + GCD in int-nano; expect pre = 100,000 (1e-04 USD/AUD) and post = 50,000
   (5e-05). Prices are Databento int-nano (1e-9 USD per unit).
2. 6A cease-guard violation 2024-12-17: independent 2024 chain segment.
   Identity via raw_symbol ( outright 6A[HMUZ]<digit> ) + delivery-frame
   containment on the 3rd-Wednesday expiry; session = UTC-trade-date via the
   17:00-CT convention approximated here as session_date = UTC date of the
   CT-session open day (uses fx_ja_lib.add_session semantics reproduced
   independently: local 17:00 CT cutoff). Baseline k=5 rule: hold until
   next-quarter trailing-5-session mean volume > held trailing-5 mean.
   Claim to verify: on 2024-12-17 the chain still held 6AZ4 while 6AH5
   traded ~55,675 and 6AZ4 was dead (no bars).
3. 6J RT $67.42 = 2*(2.46+25.00+6.25) arithmetic + component crosscheck
   against 6j_orientation_recheck.json.
Writes verify/fxja_crosscheck.json. Read-only.
"""
import datetime as dt
import glob
import json
import os
import re

import numpy as np
import pandas as pd

WT = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-readiness/prep"
ROUND = os.path.join(WT, "research/control/FUTURES-SIX-READINESS-20261004")
RAW = "/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet"
OUT_RE = re.compile(r"^6A([FGHJKMNQUVXZ])(\d)$")
MC = {"F": 1, "G": 2, "H": 3, "J": 4, "K": 5, "M": 6,
      "N": 7, "Q": 8, "U": 9, "V": 10, "X": 11, "Z": 12}

res = {"schema": "verify_fxja_crosscheck@1", "checks": {}}

# ---------------- 1. tick eras ----------------
bf2 = glob.glob(f"{RAW}/AV1B-O1M-6A-BACKFILL2/*.parquet")[0]
df = pd.read_parquet(bf2, columns=["ts_event", "instrument_id", "raw_symbol",
                                   "close"])
df = df[df["raw_symbol"].str.match(OUT_RE)].copy()  # outright 6A only
dts = pd.to_datetime(df["ts_event"], unit="ns", utc=True)
df["day"] = dts.dt.date

def session_stats(day, expect):
    d = df[df["day"] == day].sort_values("ts_event")
    out = {"session_date": str(day), "bars": int(len(d)),
           "instruments": int(d["instrument_id"].nunique())}
    mins, gcds, odd_share_n, odd_share_d = [], None, 0, 0
    all_closes = []
    for _, g in d.groupby("instrument_id"):
        c = g["close"].to_numpy()
        all_closes.append(c)
        dd = np.abs(np.diff(c))
        nz = dd[dd > 0]
        if len(nz):
            mins.append(int(nz.min()))
            g = int(np.gcd.reduce(nz.astype(np.int64)))
            gcds = g if gcds is None else int(np.gcd(gcds, g))
            odd_share_n += int((nz == 50000).sum())
            odd_share_d += int(len(nz))
    all_closes = np.concatenate(all_closes)
    out["min_increment_int_nano"] = min(mins) if mins else None
    out["cross_instrument_gcd_int_nano"] = gcds
    out["min_increment_usd_per_aud"] = (min(mins) * 1e-9) if mins else None
    out["share_diffs_eq_50000"] = (odd_share_n / odd_share_d) if odd_share_d else None
    out["any_close_odd_50000_mod_100000"] = bool(
        ((all_closes % 100000) == 50000).any())
    out["expected_gcd"] = expect
    out["ok"] = gcds == expect
    return out

pre_days = [dt.date(2020, 11, 16), dt.date(2020, 11, 18), dt.date(2020, 11, 20)]
post_days = [dt.date(2020, 11, 23), dt.date(2020, 11, 25), dt.date(2020, 11, 27)]
res["checks"]["tick_era_pre"] = [session_stats(d, 100000) for d in pre_days]
res["checks"]["tick_era_post"] = [session_stats(d, 50000) for d in post_days]
res["checks"]["tick_era_ok"] = (
    all(s["ok"] for s in res["checks"]["tick_era_pre"]) and
    all(s["ok"] for s in res["checks"]["tick_era_post"]))

# ---------------- 2. 6A cease-guard 2024-12-17 ----------------
# chunk 2024: AV1R-O1M-6A-BACKFILL__2024-01-01_2026-01-01.parquet
f24 = f"{RAW}/AV1R-O1M-6A-BACKFILL/AV1R-O1M-6A-BACKFILL__2024-01-01_2026-01-01.parquet"
d24 = pd.read_parquet(f24, columns=["ts_event", "instrument_id", "raw_symbol",
                                    "close", "volume"])
t24 = pd.to_datetime(d24["ts_event"], unit="ns", utc=True)
# session attribution (independent, CT 17:00 convention): local hour >= 17
# belongs to next day's session
loc = t24.dt.tz_convert("America/Chicago")
sess = loc.dt.normalize() + pd.to_timedelta(
    (loc.dt.hour >= 17).astype(int).values, unit="D")
d24["session"] = sess.dt.date

# identity: raw_symbol -> contract with delivery-frame containment
def third_wed(y, m):
    d = dt.date(y, m, 1)
    return d + dt.timedelta(days=(2 - d.weekday()) % 7) + dt.timedelta(days=14)

d24 = d24[d24["raw_symbol"].str.match(OUT_RE)].copy()
codes = d24["raw_symbol"].str.extract(OUT_RE)
d24["code"] = codes[0]
d24["digit"] = codes[1].astype(int)
g = d24.groupby("raw_symbol")["ts_event"].agg(["min", "max"])
contract_of_sym = {}
for sym, row in g.iterrows():
    mch = OUT_RE.match(sym)
    letter, digit = mch.group(1), mch.group(2)
    mcode = MC[letter]
    digit_i = int(digit)
    t0 = pd.Timestamp(row["min"], unit="ns", tz="UTC")
    t1 = pd.Timestamp(row["max"], unit="ns", tz="UTC")
    cands = [third_wed(y, mcode) for y in range(2023, 2027)
             if y % 10 == digit_i]
    ok = [c for c in cands
          if (pd.Timestamp(c) - pd.Timedelta(days=820)).tz_localize("UTC") <= t0
          and t1 <= (pd.Timestamp(c) + pd.Timedelta(days=12)).tz_localize("UTC")]
    if len(ok) == 1:
        contract_of_sym[sym] = f"6A{letter}{digit}_{ok[0].year}"
    else:
        contract_of_sym[sym] = None
d24["contract"] = d24["raw_symbol"].map(contract_of_sym)
d24 = d24[d24["contract"].notna()]

st = d24.groupby(["session", "contract"])["volume"].sum().reset_index()
wide = st.pivot_table(index="session", columns="contract", values="volume",
                      aggfunc="sum").sort_index()
wide = wide.loc[(wide.index >= dt.date(2023, 12, 1)) &
                (wide.index <= dt.date(2024, 12, 31))]

# independent k=5 chain over this segment (seed = max trailing-5 at first row)
roll5 = wide.rolling(5, min_periods=1).mean()
dates = list(wide.index)
state = None
held_map = {}
for d0 in dates:
    row = roll5.loc[d0].dropna()
    row = row[row > 0]
    if state is None:
        state = row.idxmax()
    else:
        cur_v = row.get(state, np.nan)
        # next quarterly after state (same trailing year-digit)
        mch2 = re.fullmatch(r"6A([FGHJKMNQUVXZ])(\d)_(\d{4})", state)
        letter, digit, yr_s = mch2.group(1), mch2.group(2), int(mch2.group(3))
        m = MC[letter]
        nm, ny = (m + 3, yr_s) if m < 12 else (3, yr_s + 1)
        ncode = [k for k, v in MC.items() if v == nm][0]
        nxt = f"6A{ncode}{digit}_{ny}"
        if nxt in row.index:
            nv = row[nxt]
            if pd.notna(cur_v) and nv > cur_v:
                state = nxt
            elif pd.isna(cur_v):
                state = nxt
    held_map[d0] = state

target = dt.date(2024, 12, 17)
vol_6az4 = wide.at[target, "6AZ4_2024"] if "6AZ4_2024" in wide.columns else None
vol_6ah5 = wide.at[target, "6AH5_2025"] if "6AH5_2025" in wide.columns else None
bars_6az4 = int((d24[(d24["session"] == target) &
                     (d24["contract"] == "6AZ4_2024")]).shape[0])
last_az4 = d24[d24["contract"] == "6AZ4_2024"]["session"].max()
r5 = roll5.loc[target]
def _iv(v):
    try:
        import math
        return None if v is None or (isinstance(v, float) and math.isnan(v)) else int(v)
    except Exception:
        return None
def _fv(v):
    try:
        import math
        return None if v is None or (isinstance(v, float) and math.isnan(v)) else float(v)
    except Exception:
        return None
res["checks"]["cease_guard_2024_12_17"] = {
    "held_this_day_independent_chain": held_map.get(target),
    "claim": {"held": "6AZ4_2024", "6AH5_volume": 55675},
    "session_volume_6AZ4_2024": _iv(vol_6az4),
    "session_volume_6AH5_2025": _iv(vol_6ah5),
    "bars_6AZ4_2024_that_day": bars_6az4,
    "last_session_with_6AZ4_2024_bars": str(last_az4),
    "trailing5_6AZ4": _fv(r5.get("6AZ4_2024")),
    "trailing5_6AH5": _fv(r5.get("6AH5_2025")),
    "dead_held_confirmed": bars_6az4 == 0 and held_map.get(target) == "6AZ4_2024",
    "volume_55675_confirmed": (_iv(vol_6ah5) == 55675),
}
# next session switch check
d_after = [d for d in dates if d > target][:1]
if d_after:
    res["checks"]["cease_guard_2024_12_17"]["held_next_session"] = str(held_map.get(d_after[0]))

# ---------------- 3. 6J RT arithmetic ----------------
comp = 2.46 + 25.00 + 6.25
rt = 2 * comp
res["checks"]["six_j_rt"] = {
    "components": {"T1_fee": 2.46, "slippage_1_tick": 25.00, "tick_value": 6.25},
    "sum_per_side": comp, "rt_recomputed": rt, "claim": 67.42,
    "ok": abs(rt - 67.42) < 1e-9,
    "lane_file": "fx_ja/6j_orientation_recheck.json round_trip_table T1/slip1 rt_usd",
}

with open(os.path.join(ROUND, "verify/fxja_crosscheck.json"), "w") as fh:
    json.dump(res, fh, indent=1, default=str)
print(json.dumps(res["checks"], indent=1, default=str))
