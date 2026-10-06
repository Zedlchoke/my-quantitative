"""6E deep-research v2 shared library — lane DEEP-6E, task FUTURES-DEEPRESEARCH-V2-20261003.

Loads the Databento av1trim 6E ohlcv-1m panel (2020-01-01..2026-09-30,
three eras: AV1B backfill2 2020-2022, AV1R backfill 2022-2026-01, AV1T
original 2026), GLBX statistics (settlement/cleared volume/OI, 2023-10+),
definitions (2023-10+), CFTC legacy CoT EURO FX (as-published 2006+), FOMC
statements (archived HTML), and the ECB GC decision-date set (see
load_ecb_gc for evidence classes).

6E specifics vs the equity-index lanes:
  * FX: serial (non-HMUZ) contracts are listed and print bars but are dead
    books; the liquid vehicle is the front QUARTERLY (HMUZ). The registry
    parses ALL outright symbols and tags serial vs quarterly.
  * One-digit-year symbols are unambiguous in 2020..2029 (digit d -> 2020+d).
  * Expiry (last trade) = 2nd exchange business day before the 3rd Wednesday
    of the delivery month, holiday-shifted (MLK / Presidents' Day) — v1
    verified 20/20; re-validated here against each contract's last session.
  * Price fixed point 1e-9; minTick 5e-05 = $6.25/contract tick value.
  * Session 17:00 CT -> 16:00 CT (23h), maintenance break 16:00-17:00 CT.

Laws honored:
  * No PnL evaluation, no signal selection; descriptive only.
  * No vendor-stitched continuous series: held-contract series are built here
    from per-contract bars with explicit, declared, PIT-legal selection rules.
  * Session/segment logic is DST-correct (America/Chicago + Europe/London
    via zoneinfo); US/EU DST-mismatch weeks flagged.
  * Every threshold used inside analyses is strict-past/rolling.
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
CACHE = os.path.join(HERE, "6E_cache")

CHI = "America/Chicago"
LON = "Europe/London"
PX_SCALE = 1e9
TICK = 5e-05          # USD per EUR; $6.25 per contract
TICK_USD = 6.25

MONTH_CODE = {"F": 1, "G": 2, "H": 3, "J": 4, "K": 5, "M": 6,
              "N": 7, "Q": 8, "U": 9, "V": 10, "X": 11, "Z": 12}
CODE_MONTH = {v: k for k, v in MONTH_CODE.items()}
QUARTERLY = {"H", "M", "U", "Z"}
OUTRIGHT_RE = re.compile(r"^6E([FGHJKMNQUVXZ])(\d)$")

# Files (era -> path list). Order matters only for provenance tagging.
ERA_FILES = {
    "B2_2020_2022": [
        f"{DATA_ROOT}/parquet/AV1B-O1M-6E-BACKFILL2/AV1B-O1M-6E-BACKFILL2__2020-01-01_2022-01-01.parquet"],
    "R_2022_2026": [
        f"{DATA_ROOT}/parquet/AV1R-O1M-6E-BACKFILL/AV1R-O1M-6E-BACKFILL__2022-01-01_2024-01-01.parquet",
        f"{DATA_ROOT}/parquet/AV1R-O1M-6E-BACKFILL/AV1R-O1M-6E-BACKFILL__2024-01-01_2026-01-01.parquet"],
    "T_2026": [
        f"{DATA_ROOT}/parquet/AV1T-O1M-6E/AV1T-O1M-6E__2026-01-01_2026-07-01.parquet",
        f"{DATA_ROOT}/parquet/AV1T-O1M-6E/AV1T-O1M-6E__2026-07-01_2026-10-01.parquet"],
}

# Session segments in exchange-local (CT) clock. Trade date D runs 17:00 CT
# on D-1 through 16:00 CT on D (60-min break 16:00-17:00).
# Segment labels are disjoint over minute_of_day of the bar's own CT day.
SEGMENTS = [
    ("evening_open", 17 * 60, 19 * 60),        # D-1 17:00-19:00 post-settlement
    ("asia_evening", 19 * 60, 24 * 60),        # D-1 19:00-24:00 (Tokyo AM)
    ("asia_morning", 0 * 60, 2 * 60),          # D 00:00-02:00 (Tokyo PM)
    ("london_morning", 2 * 60, 5 * 60),        # D 02:00-05:00 CT (London AM, DST-dependent)
    ("london_midday", 5 * 60, 6 * 60 + 30),    # D 05:00-06:30 CT
    ("ecb_usdata_window", 6 * 60 + 30, 8 * 60),  # ECB ~06:45/07:15, US data 07:30 CT
    ("pre_rth", 8 * 60, 8 * 60 + 30),          # D 08:00-08:30 CT
    ("rth_first_hour", 8 * 60 + 30, 9 * 60 + 30),  # 09:30-10:30 ET
    ("us_morning_late", 9 * 60 + 30, 12 * 60),
    ("us_midday", 12 * 60, 12 * 60 + 45),
    ("fomc_window", 12 * 60 + 45, 14 * 60),    # 13:00 CT = 14:00 ET statements
    ("afternoon_close", 14 * 60, 16 * 60),     # 15:00-16:00 ET close ext
]
RTH_MIN = 7 * 60 + 30        # 08:30-16:00 CT IB-liquid-hours equivalent minutes
SESSION_TRADABLE_MIN = 23 * 60 - 60  # 17:00->16:00 minus 60m break


def load_outright_1m() -> pd.DataFrame:
    """Full 6E outright ohlcv-1m panel (all months incl. serials), cached.

    Applies the OUTRIGHT_RE filter (drops calendar-spread instruments like
    '6EG0-6EF0' and cross-symbol strays '6JZ7'/'SIJ5' — counted separately in
    the QA ledger) and keeps era provenance per row.
    """
    cache = os.path.join(CACHE, "6e_outright_1m.parquet")
    if os.path.exists(cache):
        return pd.read_parquet(cache)
    frames, provenance = [], {}
    for era, files in ERA_FILES.items():
        for f in files:
            d = pd.read_parquet(f)
            d["era"] = era
            frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    df["dt"] = pd.to_datetime(df["ts_event"], unit="ns", utc=True)
    df = df[df["raw_symbol"].astype(str).str.match(OUTRIGHT_RE)].copy()
    df = df.sort_values(["dt", "raw_symbol"]).reset_index(drop=True)
    for c in ("open", "high", "low", "close"):
        df[c + "_px"] = df[c] / PX_SCALE
    os.makedirs(CACHE, exist_ok=True)
    df.to_parquet(cache, index=False)
    return df


def load_all_symbol_census() -> dict:
    """Row counts by symbol class per era (QA ledger input)."""
    out = {}
    for era, files in ERA_FILES.items():
        tot = ou = sp = 0
        stray = {}
        for f in files:
            d = pd.read_parquet(f, columns=["raw_symbol"])
            syms = d["raw_symbol"].astype(str)
            tot += len(d)
            ou += int(syms.str.match(OUTRIGHT_RE).sum())
            dash = syms.str.contains("-")
            sp += int(dash.sum())
            other = syms[~dash & ~syms.str.match(OUTRIGHT_RE)]
            for s, n in other.value_counts().items():
                stray[s] = stray.get(s, 0) + int(n)
        out[era] = {"rows_total": tot, "rows_outright": ou,
                    "rows_calendar_spread_instr": sp, "stray_rows": stray}
    return out


# ----------------------------------------------------------------------------
# Expiry calendar: last trade = 2nd exchange business day before the 3rd
# Wednesday of the delivery month; exchange holidays MLK (3rd Mon Jan) and
# Washington's Birthday (3rd Mon Feb) shift it (v1: 20/20). Returns the
# last-trade DATE.
# ----------------------------------------------------------------------------

def third_weekday(year: int, month: int, weekday: int) -> dt.date:
    d = dt.date(year, month, 1)
    offset = (weekday - d.weekday()) % 7
    return d + dt.timedelta(days=offset + 14)


def mlk(year: int) -> dt.date:
    return third_weekday(year, 1, 0)   # Monday


def presidents(year: int) -> dt.date:
    return third_weekday(year, 2, 0)   # Monday


def columbus_day(year: int) -> dt.date:
    return nth_weekday(year, 10, 0, 2)  # 2nd Monday Oct


def nth_weekday(year: int, month: int, weekday: int, n: int) -> dt.date:
    d = dt.date(year, month, 1)
    offset = (weekday - d.weekday()) % 7
    return d + dt.timedelta(days=offset + 7 * (n - 1))


def good_friday(year: int) -> dt.date:
    # Western Easter (Anonymous Gregorian algorithm), minus 2 days.
    a = year % 19
    b, c = year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return dt.date(year, month, day) - dt.timedelta(days=2)


def exchange_holidays(year: int) -> set:
    """Holidays that can shift the IMM 2-business-day window for 6E
    delivery months (measured: MLK/Presidents via v1; Juneteenth via 6EM3
    2023-06-19; Columbus Day via 6EV4/6EV5 Oct serials; Good Friday and
    Veterans Day included defensively for Apr/Nov serial windows)."""
    h = {mlk(year), presidents(year), columbus_day(year),
         good_friday(year), dt.date(year, 11, 11)}
    if year >= 2022:
        h.add(dt.date(year, 6, 19))
    # observed-shift for fixed-date holidays falling on weekends
    out = set()
    for d in h:
        if d.weekday() == 5:
            out.add(d - dt.timedelta(days=1))
        elif d.weekday() == 6:
            out.add(d + dt.timedelta(days=1))
        else:
            out.add(d)
    return out


def last_trade_date(year: int, month: int) -> dt.date:
    tw = third_weekday(year, month, 2)  # Wednesday
    hol = exchange_holidays(year)
    d, stepped = tw, 0
    while stepped < 2:
        d -= dt.timedelta(days=1)
        if d.weekday() < 5 and d not in hol:
            stepped += 1
    return d


def symbol_year(digit: int) -> int:
    """2020-01-01..2026 window: digit d maps uniquely to 2020+d (0..8)."""
    return 2020 + digit


def build_contract_registry(df: pd.DataFrame) -> pd.DataFrame:
    """One row per outright contract. Expiry handling:
    expiry_rule = IMM 2-business-day rule incl. holiday shifts (MLK,
      Presidents, Juneteenth, Columbus Day, Good Friday, Veterans Day);
    expiry_obs = last session with bars (OBSERVED);
    expiry = expiry_obs when the contract has already expired by the data
      end (authoritative: actual last-trade session), else expiry_rule
      (future contracts, rule-only).
    """
    data_end = pd.Timestamp(df["session_date"].max())
    rows = []
    for sym, g in df.groupby("raw_symbol"):
        m = OUTRIGHT_RE.match(sym)
        code, digit = m.group(1), int(m.group(2))
        year = symbol_year(digit)
        month = MONTH_CODE[code]
        exp_rule = last_trade_date(year, month)
        last_sess = max(g["session_date"])
        expired = pd.Timestamp(last_sess) <= data_end and \
            pd.Timestamp(exp_rule) <= data_end
        exp_eff = last_sess if expired else exp_rule.isoformat()
        rows.append({
            "symbol": sym, "month": month, "year": year,
            "delivery": f"{year}-{month:02d}",
            "quarterly": code in QUARTERLY,
            "expiry_rule": exp_rule.isoformat(),
            "expiry_obs": str(last_sess),
            "expired": bool(expired),
            "expiry": str(exp_eff),
            "first_bar": g["dt"].min(), "last_bar": g["dt"].max(),
            "n_bars": len(g),
            "n_sessions": g["session_date"].nunique(),
            "instrument_ids": sorted(g["instrument_id"].unique().tolist()),
        })
    reg = pd.DataFrame(rows).sort_values(["delivery", "symbol"]).reset_index(drop=True)
    reg["contract"] = reg["symbol"] + "_" + reg["year"].astype(str)
    return reg


def annotate_panel(df: pd.DataFrame) -> pd.DataFrame:
    """Add CT-local time, session date, minute-of-day, segments, London-local
    morning flag, DST-mismatch flag."""
    local = df["dt"].dt.tz_convert(CHI)
    hhmm = local.dt.hour * 60 + local.dt.minute
    # trade date: CT wall-clock times >= 17:00 belong to the NEXT calendar
    # session. Wall-clock (naive) arithmetic — absolute timedelta addition
    # lands wrong on DST-transition evenings (normalize() keeps the
    # pre-transition offset).
    wall = local.dt.tz_localize(None).dt.normalize()
    df["session_date"] = (wall + pd.to_timedelta(
        (hhmm >= 17 * 60).astype(int), unit="D")).dt.date
    df["minute_of_day"] = hhmm
    df["in_break"] = (hhmm >= 16 * 60) & (hhmm < 17 * 60)
    dow = local.dt.dayofweek
    df["weekend_anomaly"] = ((dow == 4) & (hhmm >= 17 * 60)) | (dow == 5)
    seg = pd.Series("break", index=df.index, dtype="object")
    for name, a, b in SEGMENTS:
        seg[(hhmm >= a) & (hhmm < b)] = name
    df["segment"] = seg
    df["in_rth_liquid"] = (hhmm >= 8 * 60 + 30) & (hhmm < 16 * 60)  # IB-liquid equivalent
    # London-local morning (fully DST-correct): Europe/London 08:00-12:00
    lon = df["dt"].dt.tz_convert(LON)
    lon_hm = lon.dt.hour * 60 + lon.dt.minute
    df["in_london_morning_local"] = (lon_hm >= 8 * 60) & (lon_hm < 12 * 60)
    # US/EU DST-mismatch flag: Chicago-London offset differs from the usual
    # 6 hours (i.e., exactly one of the two zones is inside its DST season)
    chi_off = local.dt.strftime("%z").str.slice(0, 3).astype(int)
    lon_off = lon.dt.strftime("%z").str.slice(0, 3).astype(int)
    df["dst_mismatch"] = (chi_off - lon_off) != -6
    return df


# ----------------------------------------------------------------------------
# PIT held-contract selection rules (no vendor stitching, ever)
# ----------------------------------------------------------------------------

def front_by_calendar(sess: pd.DataFrame, reg: pd.DataFrame) -> pd.DataFrame:
    """v1 declared rule: hold front HMUZ until the last session BEFORE day 1
    of its delivery month; roll target = next HMUZ (quarterly-only variant)."""
    q = reg[reg["quarterly"]].sort_values("expiry")
    lut = q.set_index("contract")["expiry"].to_dict()
    contracts = list(q["contract"])
    held_rows = []
    for i, c in enumerate(contracts[:-1]):
        exp = pd.Timestamp(lut[c])
        nxt_exp = pd.Timestamp(lut[contracts[i + 1]])
        g = sess[(sess["contract"] == c) &
                 (pd.to_datetime(sess["session_date"]) < exp.replace(day=1))]
        if i > 0:
            prev_exp = pd.Timestamp(lut[contracts[i - 1]])
            g = g[pd.to_datetime(g["session_date"]) >= prev_exp.replace(day=1)]
        if len(g):
            held_rows.append(g[["session_date"]].assign(held=c))
    held = pd.concat(held_rows).sort_values("session_date")
    held = held.groupby("session_date")["held"].last().reset_index()
    return held


def front_by_expiry_week(sess: pd.DataFrame, reg: pd.DataFrame,
                         t_minus: int = 2) -> pd.DataFrame:
    """Expiry-week rule: roll at the close of the session t_minus sessions
    before the old contract's last-trade date (matches measured migration)."""
    q = reg[reg["quarterly"]].sort_values("expiry")
    lut = q.set_index("contract")["expiry"].to_dict()
    contracts = list(q["contract"])
    sdates = pd.to_datetime(sess["session_date"])
    all_dates = pd.DatetimeIndex(sorted(sess["session_date"].unique()))
    date_idx = {d.date(): i for i, d in enumerate(all_dates)}
    held_rows = []
    for i, c in enumerate(contracts[:-1]):
        exp = pd.Timestamp(lut[c]).date()
        if exp not in date_idx:
            j = None
            for k, d in enumerate(all_dates):
                if d.date() < exp:
                    j = k
                else:
                    break
            if j is None:
                continue
            roll_date = all_dates[max(0, j - (t_minus - 1))]
        else:
            roll_date = all_dates[max(0, date_idx[exp] - (t_minus - 1))]
        m_c = (sess["contract"] == c) & (sdates <= roll_date)
        if i > 0:
            prev_exp = pd.Timestamp(lut[contracts[i - 1]]).replace(day=1)
            m_c &= (sdates >= prev_exp)
        g = sess[m_c]
        if len(g):
            held_rows.append(g[["session_date"]].assign(held=c))
    held = pd.concat(held_rows).sort_values("session_date")
    held = held.groupby("session_date")["held"].last().reset_index()
    return held


def front_by_volume_crossover(sess: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    """PIT volume-triggered rule (quarterly only): hold c until next HMUZ n
    has trailing-k-session total volume > c's; decided at close of t using
    data through t; new contract held from t+1."""
    q = sess[sess["contract"].str.match(r"^6E[HMUZ]\d_20\d\d$")].copy()
    wide = q.pivot_table(index="session_date", columns="contract",
                         values="volume", aggfunc="sum").sort_index()
    roll = wide.rolling(k, min_periods=1).mean()
    state, held = None, []
    contracts = [c for c in wide.columns]
    order = sorted(contracts, key=lambda c: c.split("_")[1] + c[2])
    pos = {c: i for i, c in enumerate(order)}
    for d in wide.index:
        row = roll.loc[d].dropna()
        row = row[row > 0]
        if state is None:
            state = row.idxmax()
        else:
            nxt = next_quarterly(state)
            if nxt in row.index:
                cur_v = row.get(state, np.nan)
                if pd.isna(cur_v) or row[nxt] > cur_v:
                    state = nxt
        held.append(state)
    return pd.DataFrame({"session_date": wide.index, "held": held})


def next_quarterly(contract: str) -> str:
    sym, yr = contract.split("_")
    m = MONTH_CODE[sym[2]]
    y = int(yr)
    nxt_m, nxt_y = (m + 3, y) if m < 12 else (3, y + 1)
    return f"6E{CODE_MONTH[nxt_m]}{nxt_y % 10}_{nxt_y}"


# ----------------------------------------------------------------------------
# Non-price loaders
# ----------------------------------------------------------------------------

def load_cot_6e() -> pd.DataFrame:
    """CFTC legacy futures-only CoT for EURO FX (as-published, no revisions).
    observation_period = Tuesday as-of; released_at = Friday 15:30 ET.
    Market mapping verified: series COT_LEGACY_6E == 'EURO FX - CHICAGO
    MERCANTILE EXCHANGE' (nonprice_acquisition mapping)."""
    df = pd.read_parquet(f"{NONPRICE}/normalized/cftc_legacy_tidy.parquet")
    e = df[df["series_id"] == "COT_LEGACY_6E"].copy()
    e["obs_date"] = pd.to_datetime(e["observation_period"])
    e["net_noncomm"] = e["noncomm_long"] - e["noncomm_short"]
    e["net_comm"] = e["comm_long"] - e["comm_short"]
    e["net_all"] = (e["noncomm_long"] + e["comm_long"]
                    - e["noncomm_short"] - e["comm_short"])
    return e.sort_values("obs_date").reset_index(drop=True)


def load_fomc() -> pd.DataFrame:
    """FOMC statement events from archived federalreserve.gov HTML.
    release_time_et only where the statement itself carries
    'For release at H:MM a.m./p.m. E[SD]T' (primary-source proof)."""
    files = sorted(glob.glob(f"{NONPRICE}/fed/statements/monetary*.html"))
    rows = []
    for f in files:
        base = os.path.basename(f)
        m = re.fullmatch(r"monetary(\d{8})a\.html", base)
        if not m:
            continue
        d = pd.Timestamp(m.group(1))
        txt = open(f, encoding="utf-8", errors="replace").read()
        mt = re.search(
            r"For release at\s*(\d{1,2}):(\d{2})\s*([ap])\.m\.\s*(E[SD]T)", txt)
        time_et = None
        if mt:
            hh = int(mt.group(1)) % 12
            if mt.group(3) == "p":
                hh += 12
            time_et = dt.time(hh, int(mt.group(2)))
        rows.append({"date": d, "time_et": time_et, "statement_file": base})
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


ECB_GC = {
    # ECB Governing Council monetary-policy decision dates (press-release day,
    # decision 14:15 CET, press conference 14:45 CET — FACT, ECB pages fetched
    # 2026-10-02). Assembly method + direct verification disclosed in the
    # dossier: ECB archive is JS-rendered; 'verified' dates were machine-
    # checked by fetching the ECB press-release URL (HTTP 200 + date +
    # 'Monetary policy decisions' title).
    "2020": {"2020-01-23": 0, "2020-03-12": 1, "2020-03-18": 1, "2020-04-30": 1,
             "2020-06-04": 1, "2020-07-16": 1, "2020-09-10": 1, "2020-10-29": 1,
             "2020-12-10": 1},
    "2021": {"2021-01-21": 0, "2021-03-11": 0, "2021-04-22": 0, "2021-06-10": 0,
             "2021-07-22": 0, "2021-09-09": 0, "2021-10-28": 0, "2021-12-16": 0},
    "2022": {"2022-02-03": 1, "2022-03-10": 0, "2022-04-14": 0, "2022-06-09": 0,
             "2022-07-21": 1, "2022-09-08": 0, "2022-10-27": 0, "2022-12-15": 0},
    "2023": {"2023-02-02": 1, "2023-03-16": 1, "2023-05-04": 0, "2023-06-15": 0,
             "2023-07-27": 0, "2023-09-14": 0, "2023-10-26": 0, "2023-12-14": 0},
    "2024": {"2024-01-25": 0, "2024-03-07": 1, "2024-04-11": 0, "2024-06-06": 0,
             "2024-07-18": 0, "2024-09-12": 0, "2024-10-17": 1, "2024-12-12": 0},
    "2025": {"2025-01-30": 0, "2025-03-06": 0, "2025-04-17": 0, "2025-06-05": 0,
             "2025-07-24": 0, "2025-09-11": 0, "2025-10-30": 0, "2025-12-18": 0},
    "2026": {"2026-02-05": 0, "2026-03-19": 0, "2026-04-30": 0, "2026-06-11": 0,
             "2026-07-23": 0, "2026-09-10": 0},
}
ECB_VERIFIED = {"2020-03-12", "2020-06-04", "2020-09-10", "2020-12-10",
                "2022-02-03", "2022-07-21", "2023-02-02", "2023-03-16",
                "2024-03-07", "2024-10-17"}


def load_ecb_gc() -> pd.DataFrame:
    rows = []
    for yr, meetings in ECB_GC.items():
        for d, hikeday in meetings.items():
            rows.append({"date": pd.Timestamp(d),
                         "verified_direct": d in ECB_VERIFIED})
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


def load_statistics_6e() -> pd.DataFrame:
    """GLBX statistics for 6E outrights (2023-10+): stat_type 3 settlement,
    6 cleared volume, 9 open interest. OI publication lag: next morning
    (adapter README; disclosed wherever OI is used)."""
    files = sorted(glob.glob(
        f"{DATA_ROOT}/parquet/AV1T-statistics-ALL10/*.parquet"))
    dfs = []
    for f in files:
        d = pd.read_parquet(f)
        d = d[d["raw_symbol"].astype(str).str.match(OUTRIGHT_RE)]
        dfs.append(d)
    df = pd.concat(dfs, ignore_index=True)
    df["dt"] = pd.to_datetime(df["ts_event"], unit="ns", utc=True)
    df["ref_date"] = pd.to_datetime(df["ts_ref"], unit="ns", utc=True).dt.date
    return df


def load_estr() -> pd.DataFrame:
    """ECB €STR daily (latest_official_ecb_sdw vintage — NOT point-in-time;
    caveat disclosed; €STR itself is essentially unrevised)."""
    df = pd.read_parquet(f"{NONPRICE}/normalized/ecb_tidy.parquet")
    e = df[df["series_id"] == "ECB_ESTR"].copy()
    e["date"] = pd.to_datetime(e["observation_period"])
    return e.sort_values("date")[["date", "value"]].reset_index(drop=True)


def load_sofr() -> pd.DataFrame:
    """FRED SOFR daily, LATEST vintage CSV on disk (vintage caveat: not
    point-in-time; SOFR revisions are negligible per NY Fed methodology —
    flagged, not asserted)."""
    p = f"{NONPRICE}/fred_alfred/latest/SOFR_latest.csv"
    df = pd.read_csv(p)
    df["date"] = pd.to_datetime(df["observation_date"])
    return df.sort_values("date")[["date", "SOFR"]].reset_index(drop=True)


def load_mro_changes() -> pd.DataFrame:
    """ECB MRO fixed-rate change dates (ECB SDW FM series, on disk)."""
    p = f"{NONPRICE}/ecb/key_ecb_interest_rates_mro.csv"
    df = pd.read_csv(p)
    df["date"] = pd.to_datetime(df["TIME_PERIOD"])
    return df.sort_values("date")[["date", "OBS_VALUE"]].reset_index(drop=True)


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
    print("library module — run 6E_build_cache.py first, then 6E_a*.py")
