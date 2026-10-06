"""NQ deep-research v2 shared library — lane DEEP-NQ, task FUTURES-DEEPRESEARCH-V2-20261003.

V3 LANE COPY (NQ-ALIAS-REPAIR, FUTURES-SIX-READINESS-20261004): faithful copy
of the baseline NQ_deep_lib.py at d7fc6231 with exactly three additions and
ONE path change — nothing else touched:
  1. CACHE -> this lane's cache_v3/ (baseline NQ_cache stays untouched).
  2. ERRATUM-F1 VIEW RULE loader load_outright_1m_v3(): relabel
     instrument_id==16908 & dt<2020-06-01 from 'NQU8-NQM9' to 'NQM0' BEFORE
     the dash-excluding filter; all other dash rows (true calendar spreads)
     stay excluded. Adjudication A_ALIAS_NOT_ABSENCE
     (FUTURES-DEEPRESEARCH-V2-20261003/analysis/integration/nq2020_hole_probe.json),
     independently re-derived in this lane's alias_lineage.json.
  3. front_by_volume_crossover_cg(): k=5 crossover with an EXPLICIT cease
     guard (hard switch when the held contract has no bars today / is past
     its bars-present cessation), replacing the implicit weak k-window guard.
     Cessation is DERIVED as the last session with any bars for the contract
     in the v3 session table (declared; not exchange metadata).
Sessionization, contract registry, cluster resolution and the plain k=5 rule
are UNCHANGED baseline logic.

Loads the Databento av1trim NQ ohlcv-1m outright panel (2010-06-06..2026-09-30),
the GLBX statistics (settlement/cleared volume/OI, 2023-10+), definitions
(2023-10+), CFTC legacy CoT (as-published), and FOMC statement dates+times.

Laws honored:
  * No PnL evaluation, no signal selection; descriptive only.
  * No vendor-stitched continuous series: held-contract series are built here
    from per-contract bars with explicit, declared, PIT-legal selection rules.
  * Session/segment logic is DST-correct (America/Chicago via zoneinfo).
  * Every threshold used inside analyses is strict-past/rolling (enforced by
    callers, helpers here take only trailing windows).
"""
from __future__ import annotations

import datetime as dt
import glob
import json
import os
import re

import numpy as np
import pandas as pd

DATA_ROOT = os.path.expanduser(
    "/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim")
NONPRICE = os.path.expanduser(
    "/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms")
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache_v3")

# ERRATUM F1 view-rule cutover: id-16908 bars strictly before this UTC instant
# carried the dash alias; from it onward the vendor symbolized 'NQM0' directly.
ALIAS_CUTOVER = pd.Timestamp("2020-06-01", tz="UTC")

CHI = "America/Chicago"
NS = 1_000_000_000

MONTH_CODE = {"H": 3, "M": 6, "U": 9, "Z": 12}
CODE_MONTH = {3: "H", 6: "M", 9: "U", 12: "Z"}

# Session segments in exchange-local (CT) clock. Trade date D runs from the
# 17:00 CT open on D-1 through the close on D. ERA-A (2010-06..2015-09-18,
# measured): close 16:15 CT, maintenance break 16:15-17:00. ERA-B (from
# 2015-09-21, measured): close 16:00 CT, break 16:00-17:00. RTH core
# (cash-synchronous) = 08:30-15:00 CT in both eras; the post-cash extension
# 15:00-16:00 exists in both; ERA-A adds a 16:00-16:15 tail.
SESSION_SWITCH_DATE = pd.Timestamp("2015-09-21")  # first 16:00-close session (measured)
SEGMENTS = [
    ("ovn_evening", 17 * 60, 24 * 60),      # D-1 17:00-24:00
    ("ovn_overnight", 0 * 60, 7 * 60),      # D 00:00-07:00
    ("ovn_preopen", 7 * 60, 8 * 60 + 30),   # D 07:00-08:30
    ("rth_open30", 8 * 60 + 30, 9 * 60),    # 08:30-09:00
    ("rth_morning", 9 * 60, 11 * 60 + 30),  # 09:00-11:30
    ("rth_lunch", 11 * 60 + 30, 13 * 60 + 30),
    ("rth_afternoon", 13 * 60 + 30, 15 * 60),
    ("rth_cashclose_ext", 15 * 60, 16 * 60),  # 15:00-16:00 (both eras)
    ("close_tail_1615", 16 * 60, 16 * 60 + 15),  # ERA-A only
]
RTH_MIN = 6 * 60 + 30       # 08:30-15:00 cash-synchronous core = 390 minutes
SESSION_FULL_MIN_A = 23 * 60 + 15 - 60 + 15  # ERA-A tradable minutes (open 17:00 -> close 16:15 next day, minus 45m break): 1380
SESSION_FULL_MIN_B = 23 * 60 - 60            # ERA-B: 1320


def session_close_minute(session_date) -> int:
    """Minute-of-day of the session close on the trade date (measured eras)."""
    d = pd.Timestamp(session_date)
    return (16 * 60 + 15) if d < SESSION_SWITCH_DATE else 16 * 60


def load_outright_1m() -> pd.DataFrame:
    """Full NQ outright ohlcv-1m panel (cached parquet under NQ_cache/)."""
    cache = os.path.join(CACHE, "nq_outright_1m.parquet")
    if os.path.exists(cache):
        return pd.read_parquet(cache)
    files = sorted(glob.glob(
        f"{DATA_ROOT}/parquet/AV1R-O1M-NQ-DELTA/*.parquet")) + sorted(glob.glob(
        f"{DATA_ROOT}/parquet/AV1T-O1M-NQ/*.parquet"))
    dfs = []
    for f in files:
        d = pd.read_parquet(f)
        dfs.append(d[~d["raw_symbol"].str.contains("-")])
    df = pd.concat(dfs, ignore_index=True).sort_values("ts_event").reset_index(drop=True)
    df["dt"] = pd.to_datetime(df["ts_event"], unit="ns", utc=True)
    os.makedirs(CACHE, exist_ok=True)
    df.to_parquet(cache, index=False)
    return df


def load_outright_1m_v3() -> tuple[pd.DataFrame, dict]:
    """ERRATUM-F1 view-rule panel: identical to load_outright_1m() except the
    alias relabel (instrument_id==16908 & dt<ALIAS_CUTOVER -> 'NQM0') is
    applied BEFORE the dash-excluding filter. Returns (panel, relabel_stats).
    All other dash rows (true calendar spreads) stay excluded, as baseline."""
    files = sorted(glob.glob(
        f"{DATA_ROOT}/parquet/AV1R-O1M-NQ-DELTA/*.parquet")) + sorted(glob.glob(
        f"{DATA_ROOT}/parquet/AV1T-O1M-NQ/*.parquet"))
    dfs = []
    stats = {"files": 0, "rows_read": 0, "relabelled_rows": 0,
             "relabelled_volume": 0, "dash_rows_dropped_after_relabel": 0}
    for f in files:
        d = pd.read_parquet(f)
        stats["files"] += 1
        stats["rows_read"] += int(len(d))
        dtu = pd.to_datetime(d["ts_event"], unit="ns", utc=True)
        m = ((d["instrument_id"] == 16908) & (dtu < ALIAS_CUTOVER))
        stats["relabelled_rows"] += int(m.sum())
        stats["relabelled_volume"] += int(d.loc[m, "volume"].sum())
        d.loc[m, "raw_symbol"] = "NQM0"
        keep = ~d["raw_symbol"].str.contains("-", regex=False)
        stats["dash_rows_dropped_after_relabel"] += int((~keep).sum())
        d = d[keep]
        d["dt"] = dtu[keep]
        dfs.append(d)
    df = pd.concat(dfs, ignore_index=True).sort_values("ts_event").reset_index(drop=True)
    # dt column already aligned per-file; rebuilt identically to baseline:
    df["dt"] = pd.to_datetime(df["ts_event"], unit="ns", utc=True)
    return df, stats


def load_annotated_1m() -> pd.DataFrame:
    """Annotated 1m panel (contract keys, session dates, segments)."""
    cache = os.path.join(CACHE, "nq_annotated_1m.parquet")
    if os.path.exists(cache):
        return pd.read_parquet(cache)
    raise RuntimeError("run NQ_build_cache.py first")


# ----------------------------------------------------------------------------
# Contract registry: raw_symbol (one-digit-year CME convention, epoch-ambiguous)
# -> calendar identity. A symbol like NQZ0 appears twice in 2010-2026 (Dec 2010
# and Dec 2020); we split a symbol's bars into contiguous time clusters and pick
# the expiry year y in {2010..2027}, y % 10 == digit, whose delivery 3rd Friday
# contains the cluster inside [expiry-27 months, expiry+10 days].
# ----------------------------------------------------------------------------

def third_friday(year: int, month: int) -> dt.date:
    d = dt.date(year, month, 1)
    # first Friday
    offset = (4 - d.weekday()) % 7  # Friday == 4
    first_fri = d + dt.timedelta(days=offset)
    return first_fri + dt.timedelta(days=14)


def build_contract_registry(df: pd.DataFrame) -> pd.DataFrame:
    """One row per (symbol cluster) contract: symbol, expiry, first/last bar."""
    g = df.groupby("raw_symbol", sort=False)
    rows = []
    for sym, idx in g.groups.items():
        m = re.fullmatch(r"NQ([HMUZ])(\d)", sym)
        if m is None:
            raise ValueError(f"unexpected outright symbol {sym}")
        code, digit = m.group(1), int(m.group(2))
        sub = df.loc[idx]
        # contiguous clusters: gap > 45 days starts a new cluster
        ts = sub["dt"].sort_values().reset_index(drop=True)
        breaks = ts.diff() > pd.Timedelta(days=45)
        cluster_id = breaks.cumsum()
        sub = sub.assign(_cluster=cluster_id.values)
        for cid, grp in sub.groupby("_cluster"):
            t0, t1 = grp["dt"].min(), grp["dt"].max()
            cands = [third_friday(y, MONTH_CODE[code])
                     for y in range(2010, 2028) if y % 10 == digit]
            ok = [c for c in cands
                  if (pd.Timestamp(c) - pd.Timedelta(days=820)).tz_localize("UTC") <= t0
                  and t1 <= (pd.Timestamp(c) + pd.Timedelta(days=12)).tz_localize("UTC")]
            if len(ok) != 1:
                # tiny clusters matching no candidate window are vendor strays
                # (e.g. single deferred-quarter prints on an ambiguous symbol):
                # excluded from analysis, recorded for the QA ledger.
                if len(grp) < 50:
                    rows.append({
                        "symbol": sym, "cluster": int(cid), "expiry": None,
                        "expiry_ts": pd.NaT, "month": MONTH_CODE[code],
                        "year": None, "first_bar": t0, "last_bar": t1,
                        "n_bars": len(grp), "instrument_ids": sorted(
                            grp["instrument_id"].unique().tolist()),
                        "stray": True,
                    })
                    continue
                raise ValueError(
                    f"{sym} cluster {cid} span {t0}..{t1} (n={len(grp)}) "
                    f"-> candidates {ok}")
            rows.append({
                "symbol": sym, "cluster": int(cid),
                "expiry": ok[0].isoformat(),
                "expiry_ts": pd.Timestamp(ok[0], tz="UTC"),
                "month": MONTH_CODE[code], "year": ok[0].year,
                "first_bar": t0, "last_bar": t1, "n_bars": len(grp),
                "instrument_ids": sorted(grp["instrument_id"].unique().tolist()),
                "stray": False,
            })
    reg = pd.DataFrame(rows).sort_values("expiry", na_position="last").reset_index(drop=True)
    # quarterly contract key like NQZ0_2020 for uniqueness; strays keyed uniquely
    def _key(r):
        if bool(r.get("stray", False)):
            return f"STRAY_{r['symbol']}_{r['cluster']}"
        return f"{r['symbol']}_{int(r['year'])}"
    reg["contract"] = reg.apply(_key, axis=1)
    return reg


def annotate_panel(df: pd.DataFrame, reg: pd.DataFrame) -> pd.DataFrame:
    """Add dt-local, session date, minute-of-day, segment labels, contract key."""
    local = df["dt"].dt.tz_convert(CHI)
    hhmm = local.dt.hour * 60 + local.dt.minute
    # trade date: local times >= 17:00 belong to the NEXT calendar session
    # (wall-clock day arithmetic: on the 25h fall-back day, absolute 24h
    # addition would land 23:00 the SAME day — DST-corrected via Day offset)
    sess_date = local.dt.normalize()
    roll = local.dt.hour >= 17
    # v3 dtype fix (behavior-identical): the baseline's offset-map addition
    # crashes on the current pandas (.dt on object result). MEASURED baseline
    # behavior (baseline nq_sessions cache) is an ABSOLUTE 24h shift of the
    # tz-aware normalized midnight: on fall-back DST Sundays, post-17:00
    # Globex-open bars land 23:00 the SAME wall day and therefore keep the
    # SUNDAY session_date (the lib comment claims DST-corrected Day
    # semantics; the cache proves absolute semantics — 35 (contract,session)
    # fall-back rows). Reproduced exactly here; disclosed in the lane report.
    sdate = (sess_date + pd.to_timedelta(roll.astype(int).values, unit="D")
             ).dt.tz_localize(None)
    close_min = np.where(sdate < SESSION_SWITCH_DATE, 16 * 60 + 15, 16 * 60)
    # maintenance break: [close, 17:00) per era
    df["in_break"] = (hhmm >= close_min) & (hhmm < 17 * 60)
    # bars past the era's close but before 17:00 in the WRONG era are anomalies
    dow = local.dt.dayofweek
    df["weekend_anomaly"] = ((dow == 4) & (hhmm >= 17 * 60)) | (dow == 5)
    df["session_date"] = sdate.dt.date
    df["minute_of_day"] = hhmm
    seg = pd.Series("break", index=df.index, dtype="object")
    for name, a, b in SEGMENTS:
        seg[(hhmm >= a) & (hhmm < b)] = name
    # era-B bars inside the 16:00-16:15 tail are break anomalies (segment stays
    # 'break' only if in_break; the tail segment is era-A). Assign tail only
    # for era-A sessions:
    tail_ok = sdate < SESSION_SWITCH_DATE
    seg[(hhmm >= 16 * 60) & (hhmm < 16 * 60 + 15) & tail_ok] = "close_tail_1615"
    df["segment"] = seg
    df["in_rth"] = (hhmm >= 8 * 60 + 30) & (hhmm < 15 * 60)  # cash-synchronous core
    df["in_rth_ext"] = (hhmm >= 8 * 60 + 30) & (hhmm < close_min)
    # map (symbol, cluster) -> contract key
    regmap = reg[["symbol", "cluster", "contract", "expiry"]].copy()
    df = df.sort_values(["raw_symbol", "dt"]).reset_index(drop=True)
    brk = df.groupby("raw_symbol")["dt"].diff() > pd.Timedelta(days=45)
    df["_cluster"] = brk.groupby(df["raw_symbol"]).cumsum().fillna(0).astype(int)
    key = df["raw_symbol"] + "|" + df["_cluster"].astype(str)
    regkey = regmap["symbol"] + "|" + regmap["cluster"].astype(str)
    lut = pd.Series(regmap["contract"].values, index=regkey.values)
    df["contract"] = key.map(lut)
    exp_lut = pd.Series(regmap["expiry"].values, index=regkey.values)
    df["expiry"] = key.map(exp_lut)
    if df["contract"].isna().any():
        raise ValueError("unmapped contract rows")
    return df


def session_table(df: pd.DataFrame) -> pd.DataFrame:
    """Deprecated vectorized-unfriendly helper — see NQ_build_cache.py."""
    raise NotImplementedError("use NQ_build_cache.py vectorized path")


# ----------------------------------------------------------------------------
# PIT held-contract selection rules (no vendor stitching, ever)
# ----------------------------------------------------------------------------

_QKEY = __import__("re").compile(r"^NQ[HMUZ]\d_\d{4}$")


def _real_contracts(sess: pd.DataFrame) -> pd.DataFrame:
    """Drop stray/unresolved contract keys (STRAY_*) from a session table."""
    return sess[sess["contract"].str.match(_QKEY)].copy()


def front_by_volume_crossover(sess: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    """PIT volume-triggered rule: hold contract c until contract n (next
    quarterly) has trailing-k-session volume > c's trailing-k-session volume,
    computed strictly from data up to and including session t (decision at
    close of t; new contract held from t+1). The held contract is the
    highest-volume contract among listed with volume continuity.
    Returns session-level frame with held contract per session_date."""
    sess = _real_contracts(sess)
    wide = sess.pivot_table(index="session_date", columns="contract",
                            values="volume", aggfunc="sum").sort_index()
    # trailing k-day mean per contract (strictly past + current day close)
    roll = wide.rolling(k, min_periods=1).mean()
    held = []
    prev = None
    dates = wide.index
    # iterate in time order; decision uses only info up to current date
    state = None
    held_contracts = []
    for d in dates:
        row = roll.loc[d]
        row = row.dropna()
        row = row[row > 0]
        if state is None:
            # start with max trailing-volume contract
            state = row.idxmax()
        else:
            # candidate switch: only to the NEXT quarterly after current
            nxt = next_quarter(state)
            if nxt in row.index:
                cur_v = row.get(state, np.nan)
                nxt_v = row[nxt]
                if pd.notna(cur_v) and nxt_v > cur_v:
                    state = nxt
                elif pd.isna(cur_v):
                    state = nxt
        held_contracts.append(state)
    out = pd.DataFrame({"session_date": dates, "held": held_contracts})
    return out


def next_quarter(contract: str) -> str:
    sym, yr = contract.split("_")
    m = MONTH_CODE[sym[2]]
    y = int(yr)
    nxt_m, nxt_y = (m + 3, y) if m < 12 else (3, y + 1)
    return f"NQ{CODE_MONTH[nxt_m]}{nxt_y % 10}_{nxt_y}"


def cessation_by_bars(sess: pd.DataFrame) -> dict:
    """DERIVED cessation per contract: the last session_date with ANY session
    row (bars present) for that contract, from the v3 session table.
    DECLARED DERIVATION — not exchange metadata; cross-checked by the caller
    against contract_registry last_bar. Diagnostic-only (non-PIT when applied
    inside a chain rule; disclosed wherever used)."""
    sess = _real_contracts(sess)
    return sess.groupby("contract")["session_date"].max().to_dict()


def front_by_volume_crossover_cg(sess: pd.DataFrame, k: int = 5,
                                 cessation: dict | None = None
                                 ) -> pd.DataFrame:
    """k=5 volume-crossover with an EXPLICIT cease guard (v3 variant).

    Identical to front_by_volume_crossover except: at each session close t,
    if the currently held contract shows NO bars today (absent from the
    session table) or t is at/past its derived bars-present cessation, the
    rule switches IMMEDIATELY to the next quarterly (first candidate with
    data today, else first candidate with any data), regardless of trailing
    volume. The baseline's implicit guard waited for a FULL k-window of
    absence (NQ_deep_lib.py:266-267); the 6J dossier law (6J_DEEP_v2.md
    section 8 ERRATUM M-5) proved that failure mode real on 6J 2022-09-20.
    cessation: contract -> last bars-present session_date (derived; see
    cessation_by_bars). Non-PIT lookback when applied in-sample — diagnostic
    variant only, disclosed as such."""
    sess = _real_contracts(sess)
    wide = sess.pivot_table(index="session_date", columns="contract",
                            values="volume", aggfunc="sum").sort_index()
    if cessation is None:
        cessation = cessation_by_bars(sess)
    roll = wide.rolling(k, min_periods=1).mean()
    dates = wide.index
    state = None
    held_contracts = []
    guards_fired = 0
    for d in dates:
        row = roll.loc[d]
        row = row.dropna()
        row = row[row > 0]
        if state is None:
            state = row.idxmax()
        else:
            cur_v = row.get(state, np.nan)
            ces = cessation.get(state)
            dead = pd.isna(cur_v) or (ces is not None
                                      and pd.Timestamp(d) > pd.Timestamp(ces))
            if dead:
                guards_fired += 1
                cand = state
                for _ in range(4):          # walk forward at most 4 quarters
                    cand = next_quarter(cand)
                    if cand in wide.columns and pd.notna(
                            wide.at[d, cand]) and wide.at[d, cand] > 0:
                        break
                else:                        # no live candidate today:
                    cand = next_quarter(state)  # fall back to next quarterly
                state = cand
            else:
                nxt = next_quarter(state)
                if nxt in row.index:
                    nxt_v = row[nxt]
                    if pd.notna(cur_v) and nxt_v > cur_v:
                        state = nxt
                    elif pd.isna(cur_v):
                        state = nxt
        held_contracts.append(state)
    out = pd.DataFrame({"session_date": dates, "held": held_contracts})
    out.attrs["guards_fired"] = guards_fired
    return out


def front_by_calendar(sess: pd.DataFrame, reg: pd.DataFrame) -> pd.DataFrame:
    """v1 declared rule: hold until the last session BEFORE day 1 of the held
    contract's delivery month; roll at that close (PIT-legal)."""
    sess = _real_contracts(sess)
    lut = reg.set_index("contract")["expiry"].to_dict()
    by_c = {}
    for c, g in sess.groupby("contract"):
        g = g.sort_values("session_date")
        by_c[c] = g
    # ordered contracts by expiry
    contracts = sorted(by_c.keys(), key=lambda c: lut[c])
    out = []
    for i, c in enumerate(contracts[:-1]):
        exp = pd.Timestamp(lut[c])
        # sessions strictly before delivery month start, and after previous
        # contract's delivery month start - 1 (i.e., this contract's hold window)
        g = by_c[c]
        win = g[pd.to_datetime(g["session_date"]) <
                exp.replace(day=1)]
        if i > 0:
            prev_exp = pd.Timestamp(lut[contracts[i - 1]])
            win = win[pd.to_datetime(win["session_date"]) >= prev_exp.replace(day=1)]
        if len(win):
            out.append(win[["session_date", "contract"]].
                       rename(columns={"contract": "held"}))
    held = pd.concat(out).sort_values("session_date")
    held = held.groupby("session_date")["held"].last().reset_index()
    return held


# ----------------------------------------------------------------------------
# Non-price loaders
# ----------------------------------------------------------------------------

def load_cot_nq() -> pd.DataFrame:
    """CFTC legacy futures-only CoT for NQ (as-published, no revisions).
    observation_period = Tuesday as-of; released_at = Friday 15:30 ET.

    [ERRATUM F2 note, 2026-10-03, lane DOSSIER-ERRATA-V2] On the FIXED tidy
    (INTEGRATION-FIX-V2) this returns ONLY the canonical E-mini NASDAQ-100
    line (1,082 rows, 2006-2026). The historical 'three mixed market lines
    on duplicate dates' state described in the A5 docstring pre-dates the
    2026-10-03 exact-name fix and is historical record only. The NASDAQ-100
    Consolidated line analyzed by NQ_a5_cot.py now lives under its own id —
    use load_cot_nq_consolidated()."""
    df = pd.read_parquet(f"{NONPRICE}/normalized/cftc_legacy_tidy.parquet")
    nq = df[df["series_id"] == "COT_LEGACY_NQ"].copy()
    nq["obs_date"] = pd.to_datetime(nq["observation_period"])
    nq["net_noncomm"] = nq["noncomm_long"] - nq["noncomm_short"]
    nq["net_comm"] = nq["comm_long"] - nq["comm_short"]
    nq = nq.sort_values("obs_date")
    return nq


def load_cot_nq_all_lines() -> pd.DataFrame:
    """All NQ-family CoT series on the fixed tidy: canonical COT_LEGACY_NQ
    (E-mini line) + every COT_LEGACY_NQ__ALT__* sibling (Consolidated /
    Micro E-mini / Nasdaq-100 stock-index lines). ERRATUM F2 helper — lets
    callers pin an exact series_id instead of filtering market_name
    strings."""
    df = pd.read_parquet(f"{NONPRICE}/normalized/cftc_legacy_tidy.parquet")
    nq = df[df["series_id"].str.startswith("COT_LEGACY_NQ")].copy()
    nq["obs_date"] = pd.to_datetime(nq["observation_period"])
    nq["net_noncomm"] = nq["noncomm_long"] - nq["noncomm_short"]
    nq["net_comm"] = nq["comm_long"] - nq["comm_short"]
    nq = nq.sort_values("obs_date")
    return nq


def load_cot_nq_consolidated() -> pd.DataFrame:
    """The NASDAQ-100 Consolidated line (the series NQ_a5_cot.py analyzes),
    pinned by exact fixed-tidy series id with an empty-guard (ERRATUM F2:
    the old market_name prefix filter selects 0 rows on the fixed tidy —
    silent-empty re-run hazard). Expected 850 rows 2010-06-15..2026-09-22
    (A7-NQ r5)."""
    alt = ("COT_LEGACY_NQ__ALT__NASDAQ_100_CONSOLIDATED_"
           "CHICAGO_MERCANTILE_EXCHANGE")
    df = pd.read_parquet(f"{NONPRICE}/normalized/cftc_legacy_tidy.parquet")
    cons = df[df["series_id"] == alt].copy()
    if cons.empty:
        raise SystemExit(
            f"ERRATUM F2 guard: series {alt!r} not found in the tidy — "
            "refusing to return an empty frame (silent-empty hazard).")
    cons["obs_date"] = pd.to_datetime(cons["observation_period"])
    cons["net_noncomm"] = cons["noncomm_long"] - cons["noncomm_short"]
    cons["net_comm"] = cons["comm_long"] - cons["comm_short"]
    return cons.sort_values("obs_date").reset_index(drop=True)


def load_fomc() -> pd.DataFrame:
    """FOMC statement events from the archived federalreserve.gov HTML.
    release_time_et is only set where the statement itself carries
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
        rows.append({"date": d, "time_et": time_et,
                     "statement_file": base})
    fomc = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    return fomc


def load_statistics_nq() -> pd.DataFrame:
    """GLBX statistics for NQ outrights (2023-10+): stat_type 3 settlement,
    6 cleared volume, 9 open interest."""
    files = sorted(glob.glob(
        f"{DATA_ROOT}/parquet/AV1T-statistics-ALL10/*.parquet"))
    dfs = []
    for f in files:
        d = pd.read_parquet(f)
        d = d[d["raw_symbol"].str.startswith("NQ")
              & ~d["raw_symbol"].str.contains("-")]
        dfs.append(d)
    df = pd.concat(dfs, ignore_index=True)
    df["dt"] = pd.to_datetime(df["ts_event"], unit="ns", utc=True)
    df["ref_date"] = pd.to_datetime(df["ts_ref"], unit="ns", utc=True).dt.date
    return df


def load_definitions_nq() -> pd.DataFrame:
    files = sorted(glob.glob(
        f"{DATA_ROOT}/parquet/AV1T-definition-ALL10/*.parquet"))
    dfs = []
    for f in files:
        d = pd.read_parquet(f)
        d = d[d["raw_symbol"].str.fullmatch(r"NQ[HMUZ]\d")]
        dfs.append(d)
    df = pd.concat(dfs, ignore_index=True)
    df["dt"] = pd.to_datetime(df["ts_event"], unit="ns", utc=True)
    return df


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
    print("library module — run the NQ_a*.py scripts")
