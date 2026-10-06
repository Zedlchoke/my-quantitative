"""6J deep-research v2 shared library — lane DEEP-6J, task FUTURES-DEEPRESEARCH-V2-20261003.

Loads the Databento av1trim 6J ohlcv-1m outright panel (2020-01-01..2026-09-30,
four chained windows: AV1B BACKFILL2 2020-22, AV1R BACKFILL 2022-26, AV1T 2026),
the GLBX statistics (settlement/cleared volume/OI, 2023-10+ only), definitions
(2023-10+ only), CFTC legacy CoT as-published (2006-01..2026-09), MOF daily FX
intervention history (81 ops 1991-04..2026-05, publish lag ~1 month), BoJ MPM
decision index (2010-2026), and FRED rate series (latest + year-end vintages).

Laws honored:
  * No PnL evaluation, no signal selection; descriptive anatomy only.
  * No vendor-stitched continuous series: held-contract series are built here
    from per-contract bars with explicit, declared, PIT-legal selection rules.
  * Session/segment logic is DST-correct per center clock (Asia/Tokyo,
    Europe/London, America/New_York, America/Chicago via zoneinfo) — Tokyo has
    no DST; US/UK windows float vs UTC and vs each other.
  * Every threshold used inside analyses is strict-past/rolling.
  * Quote orientation: 6J = USD per JPY (price UP = yen appreciation); a long
    6J is long JPY / short USD. Never read 6J as USDJPY.
"""
from __future__ import annotations

import datetime as dt
import glob
import json
import os
import re

import numpy as np
import pandas as pd

DATA_ROOT = "/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim"
NONPRICE = "/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms"
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "6J_cache")

CHI = "America/Chicago"
TOK = "Asia/Tokyo"        # no DST
LON = "Europe/London"     # DST, differs from US by ~2wk
NY = "America/New_York"   # DST, = CT + 1h always (both shift together)
NS = 1_000_000_000
PX_SCALE = 1e-9           # Databento GLBX 6J prices are int nanos (5e-7 tick = 500)
TICK = 500                # int-nano units per 6J tick (5e-7 USD per JPY)

MONTH_CODE = {"F": 1, "G": 2, "H": 3, "J": 4, "K": 5, "M": 6,
              "N": 7, "Q": 8, "U": 9, "V": 10, "X": 11, "Z": 12}
CODE_MONTH = {v: k for k, v in MONTH_CODE.items()}
QUARTERS = "HMUZ"

# Exchange session (Globex, FX futures): open 17:00 CT D-1, close 16:00 CT D,
# continuous 23h (NO intraday maintenance break for CME FX — MEASURED on this
# panel: median held-contract session has 1357 of 1380 possible 1m bars; the
# 16:00-17:00 CT halt contains exactly 1 stray bar in 2.84M). Trade date = CT
# date of the close. Held throughout 2020-2026 (no era switch, unlike NQ/ES).
OPEN_MIN = 17 * 60        # CT minute-of-day of session open (prior calendar day)
CLOSE_MIN = 16 * 60       # CT minute-of-day of session close (trade date)
SESSION_FULL_MIN = 23 * 60  # 1380 tradable minutes (17:00 D-1 -> 16:00 D)

# Disjoint exchange-clock partition (CT wall clock, trade-date frame: the
# session runs 17:00 D-1 -> 16:00 D; minute_of_day>=17 belongs to NEXT session).
# These CT buckets are DST-stable in CT terms; their UTC equivalents shift 1h.
CT_BUCKETS = [
    ("asia_early_17_21", 17 * 60, 21 * 60),   # 17:00-21:00 CT: Sydney/Tokyo pre-open
    ("tokyo_day_21_02", 21 * 60, 26 * 60),    # 21:00-02:00 CT (= Tokyo 09:00-15:00 JST when CDT; 10:00-16:00 JST when CST)
    ("asia_late_02_07", 26 * 60, 31 * 60),    # 02:00-07:00 CT: Tokyo close/evening
    ("london_am_02_05", 2 * 60, 5 * 60),      # London 08:00-11:00 local approx (see center windows for exact)
    ("ny_am_07_10", 7 * 60, 10 * 60),
    ("ny_lunch_10_12", 10 * 60, 12 * 60),
    ("ny_pm_12_15", 12 * 60, 15 * 60),
    ("close_15_16", 15 * 60, 16 * 60),
    ("break_16_17", 16 * 60, 17 * 60),
]
# NOTE: the CT_BUCKETS partition maps minute_of_day with session-open rollover:
# minutes 17:00-24:00 of D-1 + 00:00-16:00 of D form the trade-date session.

# Center-local named windows (DST-correct via tz_convert; overlap disclosed).
CENTER_WINDOWS = {
    "tokyo_am":     (TOK, 9 * 60, 11 * 60 + 30),
    "tokyo_lunch":  (TOK, 11 * 60 + 30, 12 * 60 + 30),
    "tokyo_pm":     (TOK, 12 * 60 + 30, 15 * 60),
    "tokyo_fix":    (TOK, 15 * 60, 15 * 60 + 45),   # 15:00-15:45 JST incl OSE close
    "london_am":    (LON, 8 * 60, 12 * 60),
    "london_pm":    (LON, 12 * 60, 16 * 60 + 30),   # incl 16:00 London/WMR fix
    "ny_am":        (NY, 8 * 60 + 20, 12 * 60),     # CME FX pit legacy open 08:20 ET
    "ny_pm":        (NY, 12 * 60, 16 * 60),
    "ny_post":      (NY, 16 * 60, 17 * 60),         # 16:00-17:00 ET tail (=15:00-16:00 CT)
}

FILES_OHLCV = (
    sorted(glob.glob(f"{DATA_ROOT}/parquet/AV1B-O1M-6J-BACKFILL2/*.parquet"))
    + sorted(glob.glob(f"{DATA_ROOT}/parquet/AV1R-O1M-6J-BACKFILL/*.parquet"))
    + sorted(glob.glob(f"{DATA_ROOT}/parquet/AV1T-O1M-6J/*.parquet"))
)

_OUTRIGHT_RE = re.compile(r"^6J([FGHJKMNQUVXZ])(\d)$")


def third_wednesday(year: int, month: int) -> dt.date:
    """CME FX futures delivery: third Wednesday of the contract month
    (last trading ceases 09:16 CT two business days prior — FACT-secondary,
    v1 dossier S1 lastTradeTime; used here for contract identity only)."""
    d = dt.date(year, month, 1)
    offset = (2 - d.weekday()) % 7  # Wednesday == 2
    first_wed = d + dt.timedelta(days=offset)
    return first_wed + dt.timedelta(days=14)


def load_outright_1m() -> pd.DataFrame:
    """Full 6J outright ohlcv-1m panel (cached parquet under 6J_cache/).
    Filters: raw_symbol must match ^6J[month][digit]$ (drops calendar-spread
    legs like '6JH1-6JZ0' and the one stray non-6J symbol in BACKFILL2)."""
    cache = os.path.join(CACHE, "6j_outright_1m.parquet")
    if os.path.exists(cache):
        return pd.read_parquet(cache)
    dfs = []
    for f in FILES_OHLCV:
        d = pd.read_parquet(f)
        keep = d["raw_symbol"].str.fullmatch(_OUTRIGHT_RE)
        bad = d.loc[~keep, "raw_symbol"].unique().tolist()
        assert all(("-" in str(s)) or not str(s).startswith("6J") for s in bad), bad
        dfs.append(d[keep])
    df = pd.concat(dfs, ignore_index=True).sort_values("ts_event").reset_index(drop=True)
    df["dt"] = pd.to_datetime(df["ts_event"], unit="ns", utc=True)
    os.makedirs(CACHE, exist_ok=True)
    df.to_parquet(cache, index=False)
    return df


def build_contract_registry(df: pd.DataFrame) -> pd.DataFrame:
    """One row per (symbol cluster) contract. One-digit-year CME symbols are
    decade-ambiguous (6JH0 = Mar 2010 or Mar 2020): split a symbol's bars into
    contiguous clusters (>60d gap) and pick the expiry year y in 2010..2028,
    y % 10 == digit, whose 3rd-Wednesday delivery puts the cluster inside
    [expiry - 27 months, expiry + 10 days]. Stray micro-clusters (<50 bars)
    matching nothing are recorded, excluded from analysis."""
    rows = []
    for sym, idx in df.groupby("raw_symbol", sort=False).groups.items():
        m = _OUTRIGHT_RE.fullmatch(sym)
        code, digit = m.group(1), int(m.group(2))
        sub = df.loc[idx]
        ts = sub["dt"].sort_values().reset_index(drop=True)
        breaks = ts.diff() > pd.Timedelta(days=60)
        sub = sub.assign(_cluster=breaks.cumsum().values)
        for cid, grp in sub.groupby("_cluster"):
            t0, t1 = grp["dt"].min(), grp["dt"].max()
            cands = [third_wednesday(y, MONTH_CODE[code])
                     for y in range(2010, 2029) if y % 10 == digit]
            ok = [c for c in cands
                  if (pd.Timestamp(c) - pd.Timedelta(days=820)).tz_localize("UTC") <= t0
                  and t1 <= (pd.Timestamp(c) + pd.Timedelta(days=10)).tz_localize("UTC")]
            if len(ok) != 1:
                if len(grp) < 50:
                    rows.append({"symbol": sym, "cluster": int(cid), "expiry": None,
                                 "month": MONTH_CODE[code], "year": None,
                                 "first_bar": t0, "last_bar": t1, "n_bars": len(grp),
                                 "instrument_ids": sorted(grp["instrument_id"].unique().tolist()),
                                 "stray": True})
                    continue
                raise ValueError(f"{sym} cluster {cid} span {t0}..{t1} "
                                 f"(n={len(grp)}) -> candidates {ok}")
            rows.append({"symbol": sym, "cluster": int(cid),
                         "expiry": ok[0].isoformat(), "month": MONTH_CODE[code],
                         "year": ok[0].year, "first_bar": t0, "last_bar": t1,
                         "n_bars": len(grp),
                         "instrument_ids": sorted(grp["instrument_id"].unique().tolist()),
                         "stray": False})
    reg = pd.DataFrame(rows).sort_values("expiry", na_position="last").reset_index(drop=True)

    def _key(r):
        if bool(r.get("stray", False)):
            return f"STRAY_{r['symbol']}_{r['cluster']}"
        return f"{r['symbol']}_{int(r['year'])}"
    reg["contract"] = reg.apply(_key, axis=1)
    return reg


def annotate_panel(df: pd.DataFrame, reg: pd.DataFrame) -> pd.DataFrame:
    """Add dt-local CT + center clocks, session_date, minute-of-day, contract key."""
    local = df["dt"].dt.tz_convert(CHI)
    hhmm = local.dt.hour * 60 + local.dt.minute
    # trade date in CT wall-clock terms: naive normalize + integer day add is
    # DST-proof (absolute-24h adds on tz-aware stamps shift an hour on the
    # 25h/23h transition days; naive midnight + 1 day is always next midnight)
    naive = local.dt.tz_localize(None)
    roll = naive.dt.hour >= 17
    sdate = naive.dt.normalize() + pd.to_timedelta(roll.astype("int64"), unit="D")
    df["session_date"] = sdate.dt.date
    df["minute_ct"] = hhmm                      # CT wall clock of the bar
    df["in_break"] = (hhmm >= CLOSE_MIN) & (hhmm < OPEN_MIN)
    dow = local.dt.dayofweek
    df["weekend_anomaly"] = ((dow == 4) & (hhmm >= OPEN_MIN)) | (dow == 5)
    # session-minute index: minutes since session open (DST-length-aware)
    # for bars on D-1 evening (>=17:00), offset = hhmm-1020; else hhmm+420
    sm = np.where(hhmm >= OPEN_MIN, hhmm - OPEN_MIN, hhmm + (24 * 60 - OPEN_MIN))
    df["session_min"] = sm
    # center clocks (vectorized via tz_convert once each)
    for name, tz in (("tokyo", TOK), ("london", LON), ("ny", NY)):
        c = df["dt"].dt.tz_convert(tz)
        df[f"minute_{name}"] = c.dt.hour * 60 + c.dt.minute
        # trade-date frame for the center: Tokyo day starts 00:00 JST of the
        # calendar Tokyo date containing the CT session close. For labeling we
        # only need minute-of-day, windows are local-day windows; bars in the
        # Tokyo-morning (US evening) belong to Tokyo's NEXT calendar day —
        # handled in window assignment by center-local hour only.
    # map (symbol, cluster) -> contract key
    regmap = reg[["symbol", "cluster", "contract", "expiry"]].copy()
    df = df.sort_values(["raw_symbol", "dt"]).reset_index(drop=True)
    brk = df.groupby("raw_symbol")["dt"].diff() > pd.Timedelta(days=60)
    df["_cluster"] = brk.groupby(df["raw_symbol"]).cumsum().fillna(0).astype(int)
    key = df["raw_symbol"] + "|" + df["_cluster"].astype(str)
    regkey = regmap["symbol"] + "|" + regmap["cluster"].astype(str)
    lut = pd.Series(regmap["contract"].values, index=regkey.values)
    df["contract"] = key.map(lut)
    df["expiry"] = key.map(pd.Series(regmap["expiry"].values, index=regkey.values))
    if df["contract"].isna().any():
        raise ValueError("unmapped contract rows")
    return df


def assign_center_windows(df: pd.DataFrame) -> pd.DataFrame:
    """Boolean column per CENTER_WINDOW (overlap by design, descriptive slices)."""
    for name, (tz, a, b) in CENTER_WINDOWS.items():
        col = f"minute_{ {'Asia/Tokyo': 'tokyo', 'Europe/London': 'london', 'America/New_York': 'ny'}[tz] }"
        df[f"w_{name}"] = (df[col] >= a) & (df[col] < b)
    return df


def assign_ct_buckets(df: pd.DataFrame) -> pd.DataFrame:
    """Disjoint partition of the session into CT-clock buckets (trade-date frame:
    session minute 0..1319 -> bucket by CT wall minute with 17:00-24:00 of D-1)."""
    seg = pd.Series("outside", index=df.index, dtype="object")
    for name, a, b in CT_BUCKETS[:-1]:  # break handled separately
        lo, hi = a, min(b, 24 * 60)
        seg[(df["minute_ct"] >= lo) & (df["minute_ct"] < hi)] = name
        if b > 24 * 60:  # wraps past midnight into next CT day
            seg[(df["minute_ct"] >= 0) & (df["minute_ct"] < b - 24 * 60)] = name
    seg[df["in_break"]] = "break_16_17"
    df["ct_bucket"] = seg
    return df


# ----------------------------------------------------------------------------
# PIT held-contract selection rules (no vendor stitching, ever)
# ----------------------------------------------------------------------------

_QKEY = re.compile(r"^6J[HMUZ]\d_\d{4}$")


def _real_contracts(sess: pd.DataFrame) -> pd.DataFrame:
    return sess[sess["contract"].str.match(_QKEY)].copy()


def next_quarter(contract: str) -> str:
    sym, yr = contract.split("_")
    m = MONTH_CODE[sym[2]]
    y = int(yr)
    nxt_m, nxt_y = (m + 3, y) if m < 12 else (3, y + 1)
    return f"6J{CODE_MONTH[nxt_m]}{nxt_y % 10}_{nxt_y}"


def front_by_volume_crossover(sess: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    """PIT volume-triggered rule over the HMUZ chain only: hold c until the
    next quarterly n has trailing-k-session volume > c's; decided with data
    through session t close, new contract held from t+1. (Serials excluded —
    v1 measured them dead: <=0.3% of volume.)"""
    sess = _real_contracts(sess)
    wide = sess.pivot_table(index="session_date", columns="contract",
                            values="volume", aggfunc="sum").sort_index()
    roll = wide.rolling(k, min_periods=1).mean()
    state = None
    held_contracts = []
    for d in roll.index:
        row = roll.loc[d].dropna()
        row = row[row > 0]
        if state is None:
            state = row.idxmax()
        else:
            nxt = next_quarter(state)
            if nxt in row.index:
                cur_v = row.get(state, np.nan)
                if pd.isna(cur_v) or row[nxt] > cur_v:
                    state = nxt
        held_contracts.append(state)
    return pd.DataFrame({"session_date": roll.index, "held": held_contracts})


def front_by_calendar_quarterly(sess: pd.DataFrame, reg: pd.DataFrame) -> pd.DataFrame:
    """v1-consistent executable rule: hold nearest HMUZ quarterly until the last
    session before its delivery month, then roll to the next quarterly."""
    sess = _real_contracts(sess)
    lut = reg.set_index("contract")["expiry"].to_dict()
    by_c = {c: g.sort_values("session_date") for c, g in sess.groupby("contract")}
    contracts = sorted(by_c.keys(), key=lambda c: lut[c])
    out = []
    for i, c in enumerate(contracts[:-1]):
        exp = pd.Timestamp(lut[c])
        g = by_c[c]
        win = g[pd.to_datetime(g["session_date"]) < exp.replace(day=1)]
        if i > 0:
            prev_exp = pd.Timestamp(lut[contracts[i - 1]])
            win = win[pd.to_datetime(win["session_date"]) >= prev_exp.replace(day=1)]
        if len(win):
            out.append(win[["session_date", "contract"]].rename(columns={"contract": "held"}))
    held = pd.concat(out).sort_values("session_date")
    return held.groupby("session_date")["held"].last().reset_index()


# ----------------------------------------------------------------------------
# Non-price loaders (all read-only, primary-source archives under NONPRICE/)
# ----------------------------------------------------------------------------

def load_mof_intervention() -> pd.DataFrame:
    """MOF daily FX intervention ops, 1991-04..2026-05 (81 ops; official
    history published with ~1-month lag — NOT same-day PIT). Units: 100m JPY."""
    df = pd.read_parquet(f"{NONPRICE}/normalized/mof_intervention_tidy.parquet")
    df["op_date"] = pd.to_datetime(df["observation_period"])
    return df.sort_values("op_date").reset_index(drop=True)


def load_boj_mpm() -> pd.DataFrame:
    """BoJ MPM decision events (day-2 statement dates), UNION of two primary
    archives fetched by the nonprice lane:
      * statements/{year}/k%y%m%da.* — decision statement files (complete
        2010-2026; only 'a' docs = the decision statement itself);
      * mpmdeci/mpr_YYYY_index.html — titles incl 'Change in the Guideline' /
        'Changes in the Monetary Policy Framework' regime-change detection
        (index snapshots cover 2018..2026-01 only; archive-only dates carry
        title=None, is_regime_change=None = title-unverified)."""
    dec = {}
    for f in sorted(glob.glob(f"{NONPRICE}/boj/statements/*/k*a.*")):
        b = os.path.basename(f)
        m = re.fullmatch(r"k(\d{2})(\d{2})(\d{2})a\.(?:html|pdf|htm)", b)
        if m:
            d = dt.date(2000 + int(m.group(1)), int(m.group(2)), int(m.group(3)))
            dec[d] = {"date": d, "title": None, "is_regime_change": None,
                      "source": f"statements_archive:{b}"}
    for f in sorted(glob.glob(f"{NONPRICE}/boj/mpmdeci/mpr_*_index.html")):
        t = open(f, encoding="utf-8", errors="replace").read()
        links = re.findall(
            r'href="(/en/mopo/mpmdeci/state_\d{4}/k(\d{6})[a-z]\.(?:htm|pdf))"[^>]*>(.*?)</a>',
            t, re.S)
        for href, ymd, txt in links:
            txt = re.sub(r"<[^>]+>", "", txt).replace("&nbsp;", " ").strip()
            m = re.fullmatch(r"(\d{2})(\d{2})(\d{2})", ymd)
            d = dt.date(2000 + int(m.group(1)), int(m.group(2)), int(m.group(3)))
            regime = ("Change in the Guideline" in txt
                      or "Changes in the Monetary Policy Framework" in txt)
            if d in dec:
                dec[d]["title"] = txt
                dec[d]["is_regime_change"] = regime
                dec[d]["source"] += "+mpmdeci_index"
    df = pd.DataFrame(sorted(dec.values(), key=lambda r: r["date"]))
    return df.reset_index(drop=True)


def load_cot_6j() -> pd.DataFrame:
    """CFTC legacy futures-only CoT for JPY (as-published, not revised).
    observation_period = Tuesday as-of; released Friday 15:30 ET."""
    df = pd.read_parquet(f"{NONPRICE}/normalized/cftc_legacy_tidy.parquet")
    j = df[df["series_id"] == "COT_LEGACY_6J"].copy()
    j["obs_date"] = pd.to_datetime(j["observation_period"])
    j["net_noncomm"] = j["noncomm_long"] - j["noncomm_short"]
    j["net_comm"] = j["comm_long"] - j["comm_short"]
    return j.sort_values("obs_date").reset_index(drop=True)


def load_fred(series: str, vintage: str = "latest") -> pd.DataFrame:
    """FRED tidy series. vintage='latest' uses fred_latest_tidy (asof 2026-09-30
    snapshot); 'pit' uses fred_vintage_attempts_tidy (year-end snapshots only —
    NOT a dense PIT vintage source; caveat disclosed wherever used)."""
    fn = "fred_latest_tidy.parquet" if vintage == "latest" else "fred_vintage_attempts_tidy.parquet"
    df = pd.read_parquet(f"{NONPRICE}/normalized/{fn}")
    s = df[df["series_id"] == series].copy()
    if vintage != "latest":
        s = s[s["vintage_flag"] == f"pit_snapshot_asof_{vintage}"]
    s["obs"] = pd.to_datetime(s["observation_period"])
    return s.sort_values("obs").reset_index(drop=True)


def load_statistics_6j() -> pd.DataFrame:
    """GLBX statistics for 6J outrights, 2023-10+ ONLY: stat_type 3 settlement,
    6 cleared volume, 9 open interest (OI data ends 2026-09 or last chunk)."""
    files = sorted(glob.glob(f"{DATA_ROOT}/parquet/AV1T-statistics-ALL10/*.parquet"))
    dfs = []
    for f in files:
        d = pd.read_parquet(f)
        d = d[d["raw_symbol"].str.fullmatch(_OUTRIGHT_RE)]
        dfs.append(d)
    df = pd.concat(dfs, ignore_index=True)
    df["dt"] = pd.to_datetime(df["ts_event"], unit="ns", utc=True)
    df["ref_date"] = pd.to_datetime(df["ts_ref"], unit="ns", utc=True).dt.date
    return df


def load_definitions_6j() -> pd.DataFrame:
    files = sorted(glob.glob(f"{DATA_ROOT}/parquet/AV1T-definition-ALL10/*.parquet"))
    dfs = []
    for f in files:
        d = pd.read_parquet(f)
        d = d[d["raw_symbol"].str.fullmatch(_OUTRIGHT_RE)]
        dfs.append(d)
    df = pd.concat(dfs, ignore_index=True)
    df["dt"] = pd.to_datetime(df["ts_event"], unit="ns", utc=True)
    return df


# ----------------------------------------------------------------------------
# JSON helper
# ----------------------------------------------------------------------------

def _san(o):
    if isinstance(o, dict):
        return {str(k): _san(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_san(v) for v in o]
    if isinstance(o, (float, np.floating)):
        return float(o) if np.isfinite(o) else None
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (pd.Timestamp, dt.date, dt.datetime)):
        return str(o)
    if isinstance(o, np.ndarray):
        return _san(o.tolist())
    return o


def jdump(obj, path):
    with open(path, "w") as fh:
        json.dump(_san(obj), fh, indent=1, allow_nan=False)


if __name__ == "__main__":
    print("library module — run the 6J_a*.py scripts")
