"""STOCKS-NG6 D2 ancestry battery (plans/PLAN_stocks_ng6.md §6/§7, non-scored).

Measures STRUCTURAL NOVELTY ONLY: pooled |rho| (Pearson AND Spearman) of the
frozen R0 shadow inventory (research/control/stocks_ng6_run/d2/
shadow_inventory.json, G8 commit-first 833641ed, sha b1e3c6d8…) against the
anchor and neighbour BOOK STATES (event indicator with H=10 holding
footprint, per the d1_freeze constructions).

NO PnL, NO expectancy, NO Sharpe/drawdown, NO forward return of any book is
computed anywhere in this run — every shadow feature is a TRAILING state at
session t close (outcome-blind; R1+ adjudicates returns later, never here).

Fail-closed laws enforced here:
- G8: inventory sha256 mismatch -> REFUSE before loading any market data;
- input authority: P0 verdict sha-pins (retrieval manifest + events census)
  must verify, and the recomputed census must reproduce the P0 census
  (symbol, date, bookable) set exactly;
- NG5 staging files must re-hash to NG5's committed F9 pins;
- DGS10-level shadow: UNMEASURABLE (no rates series constructible from the
  price cache) — recorded, never skipped silently;
- 0.20 bar immovable (G9); every control null reported (population +
  lag-1 autocorrelation) before it may ever kill (Q-11); unpopulated or
  degenerate nulls are NOT_ADJUDICABLE, never silent.

The machine-wide heavy lock (research.governance.heavy_lock) is held for the
whole computation; busy => NOT_RUN_RESOURCE_CONFLICT verdict, never a spin.
"""

from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-ng6/integration")
HERE = WT / "research/control/stocks_ng6_run/d2"
P0 = WT / "research/control/stocks_ng6_run/p0"
CACHE = WT / "data_raw/stocks_ng6_eod"
INV = HERE / "shadow_inventory.json"
OUT = HERE / "d2_verdict.json"

INV_SHA256 = "b1e3c6d881d5b41d6d9fdfce76ba03f2ee4d3bee6346779adda44bc781571eb4"
EVENTS_CENSUS_SHA256 = "cc194c14b0901e5ef98de0751e2e437ccdf996c787814975049f92465f177642"
RETRIEVAL_MANIFEST_SHA256 = "1137b32b6e8355b37d5c81df8ddbca7d027f496dde6b84bd4cc110b076e71211"

# frozen ex-ante constants (inventory + plan §6; never tuned post hoc)
RV_WINDOWS = (20, 60)          # A4 axis 2: both windows declared
REVERSAL_REBALANCE = 5         # C-REVERSAL-PLAIN clock (plan §6)
RANDOM_TIMING_EVERY = 63       # C-RANDOM-TIMING clock twin (plan §6)
HOLD = 10                      # H=10 holding footprint (d1_freeze)
DVOL_WINDOW = 60
DVOL_MULT = 1.5
FLOOR_PRICE = 1.00
FLOOR_DVOL = 2_000_000.0
BETA_WINDOW = 63
BETA_MIN_PRESENT = 40
BAR = 0.20                     # R0 bar, immovable (G9)
SELF_SUB_BAR = 0.98            # P-20 books-distinct
DIVIDEND_DOMINATED_FRACTION = 0.80  # declared ex ante in the inventory entry

NG5_STAGING = Path("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-ng5/"
                   "integration/research/control/stocks_ng5_run/p0/staging")
NG5_PINS = {  # committed F9 block of NG5's P0 verdict (prior-cycle evidence)
    "QQEW": "28119258e76c051725dde42b0fa120ca7d9b04201193638b0fab2ab174a8be9a",
    "QQQ": "ff204ad3cc55e7e6aaf72ac70001ad2eb925bbcff8923c2d8fd82b4c6cafa0ea",
    "RSP": "c27a1c2f91745562a52a6de2563b7f34894d858da7344f2efc891122628d2742",
    "SPY": "7a66f450046f22ac9d79035aaf8ac1fb2b9260e3b6da8564329c47b1ae7b35f7",
}
NG5_L = 13
NG5_ZWIN = 104

RATES_PROXIES = ("TLT", "IEF", "SHY", "IEI", "TLH", "BND", "AGG", "GOVT", "UST", "DGS10")

SHADOW_KEYS = ("mom63", "mom121_pre", "rev5", "rev21", "dd252", "dvolshock",
               "rv20", "rv60", "svshare", "beta63", "deathprox",
               "book_anchor", "book_neigh", "book_rawanchor", "evmask", "gpos")

_last_hb = {"t": 0.0}


class InventoryMismatch(RuntimeError):
    """G8: the frozen inventory does not hash to the committed value."""


class InputAuthorityError(RuntimeError):
    """P0 sha-pins or census reproduction failed (fail-closed)."""


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def log(m):
    print(f"[d2] {m}", flush=True)


def load_inventory() -> dict:
    raw = INV.read_bytes()
    got = sha(raw)
    if got != INV_SHA256:
        raise InventoryMismatch(
            f"shadow_inventory.json sha256 {got} != committed {INV_SHA256} (G8 refuse)")
    return json.loads(raw)


# ---------------------------------------------------------------- statistics

def pearson(x: np.ndarray, y: np.ndarray):
    m = np.isfinite(x) & np.isfinite(y)
    xs = x[m].astype(np.float64)
    ys = y[m].astype(np.float64)
    n = int(xs.size)
    if n < 3:
        return None, n
    xc = xs - xs.mean()
    yc = ys - ys.mean()
    den = float(np.sqrt((xc * xc).sum() * (yc * yc).sum()))
    if den == 0.0:
        return None, n
    return float((xc * yc).sum() / den), n


def rankdata_avg(a: np.ndarray) -> np.ndarray:
    """Average ranks (1-based), ties averaged (scipy rankdata 'average' form)."""
    a = np.asarray(a, dtype=np.float64)
    n = a.size
    sorter = np.argsort(a, kind="mergesort")
    inv = np.empty(n, dtype=np.intp)
    inv[sorter] = np.arange(n)
    sa = a[sorter]
    obs = np.r_[True, sa[1:] != sa[:-1]]
    dense = np.cumsum(obs)[inv]
    starts = np.nonzero(obs)[0]                      # 0-based group starts
    ends = np.append(starts[1:], n)                  # 0-based group ends (exclusive)
    avg = (starts + ends + 1) / 2.0                  # average 1-based rank per group
    return avg[dense - 1]


def spearman(x: np.ndarray, y: np.ndarray):
    m = np.isfinite(x) & np.isfinite(y)
    if int(m.sum()) < 3:
        return None, int(m.sum())
    return pearson(rankdata_avg(x[m]), rankdata_avg(y[m]))


def rho_record(x: np.ndarray, y: np.ndarray) -> dict:
    p, n1 = pearson(x, y)
    s, _ = spearman(x, y)
    rec = {"n": n1,
           "pearson": None if p is None else round(p, 6),
           "spearman": None if s is None else round(s, 6)}
    vals = [abs(v) for v in (p, s) if v is not None]
    rec["abs_max"] = max(vals) if vals else None
    rec["margin_to_020"] = (None if rec["abs_max"] is None
                            else round(BAR - rec["abs_max"], 6))
    return rec


def weekday0(iso: np.ndarray) -> np.ndarray:
    """Monday=0 convention (epoch 1970-01-01 was a Thursday: +3 offset)."""
    d = np.array(iso, dtype="datetime64[D]").astype(int)
    return ((d + 3) % 7).astype(int)


# ---------------------------------------------------------------- inputs

def verify_input_authority() -> dict:
    checks = {}
    rm = sha((P0 / "retrieval_manifest.json").read_bytes())
    checks["retrieval_manifest_sha256_match"] = rm == RETRIEVAL_MANIFEST_SHA256
    ec_bytes = gzip.decompress((P0 / "events_census.json.gz").read_bytes())
    checks["events_census_sha256_match"] = sha(ec_bytes) == EVENTS_CENSUS_SHA256
    if not (checks["retrieval_manifest_sha256_match"] and checks["events_census_sha256_match"]):
        raise InputAuthorityError(f"P0 sha-pin mismatch: {checks}")
    expected = {(r["symbol"], r["date"], bool(r["bookable"])) for r in json.loads(ec_bytes)}
    syms = sorted(p.name[:-8] for p in CACHE.glob("*.json.gz"))
    checks["p0_verdict"] = json.loads((P0 / "p0_verdict.json").read_text())["verdict"]
    checks["cache_symbols"] = len(syms)
    checks["rates_proxy_symbols_in_cache"] = [s for s in RATES_PROXIES if s in syms]
    checks["expected_census_rows"] = len(expected)
    return {"checks": checks, "expected_census": expected, "symbols": syms}


def load_grid_and_folds() -> dict:
    f = json.loads((P0 / "folds.json").read_text())
    spy_rows = json.loads(gzip.decompress((CACHE / "SPY.json.gz").read_bytes()))
    dates = sorted({r["date"] for r in spy_rows})
    lo, hi = f["window"]
    grid = [d for d in dates if lo <= d <= hi]
    fold_of = {}
    for fd in f["folds"]:
        for d in grid:
            if fd["start"] <= d <= fd["end"]:
                fold_of[d] = fd["id"]
    if len(fold_of) != len(grid):
        raise InputAuthorityError("folds.json does not tile the frozen grid")
    gidx = {d: i for i, d in enumerate(grid)}
    by_date = {r["date"]: r for r in spy_rows}
    spy_close = np.array([by_date[d]["adjusted_close"] for d in grid], dtype=float)
    spy_ret = np.full(len(grid), np.nan)
    spy_ret[1:] = spy_close[1:] / spy_close[:-1] - 1.0
    months = np.array(grid, dtype="datetime64[M]")
    return {"grid": grid, "gidx": gidx, "fold_of": fold_of, "spy_ret": spy_ret,
            "month_start": np.r_[True, months[1:] != months[:-1]],
            "month_end": np.r_[months[:-1] != months[1:], True],
            "folds_doc": f}


def verify_ng5_pins() -> dict:
    out = {}
    for k, want in NG5_PINS.items():
        got = sha((NG5_STAGING / f"{k}_full.json").read_bytes())
        out[k] = {"match": got == want}
        if got != want:
            raise InputAuthorityError(f"NG5 staging {k} sha mismatch: {got} != {want}")
    return out


def ng5_weekly_leg_state(grid: list[str]) -> tuple[np.ndarray, dict]:
    """NG5 ANCHOR-TREND-L13 weekly leg (1=QQQ, 0=SPY) on the frozen grid.

    Exact NG5 D1-freeze formulas: weekly state s_t = 0.5*(ln(QQEW/QQQ) +
    ln(RSP/SPY)) at the LAST session of each ISO week over the four-leg
    common session set (a week missing any leg = SKIPPED decision, prior leg
    held); m_t = s_t - s_{t-13}; z_t = m_t / stdev(trailing 104 weekly m,
    ddof=1); z_t >= 0 -> hold QQQ else SPY; undefined z carries the prior
    leg (initial leg SPY, declared).  A week's hold covers grid sessions in
    (D_k, D_{k+1}].
    """
    closes: dict[str, dict[str, float]] = {}
    for k in NG5_PINS:
        rows = json.loads((NG5_STAGING / f"{k}_full.json").read_text())
        closes[k] = {r["date"]: float(r["adjusted_close"]) for r in rows}
    common = sorted(set(closes["QQQ"]) & set(closes["SPY"])
                    & set(closes["QQEW"]) & set(closes["RSP"]))
    week_of: dict[str, str] = {}  # iso-week Thursday -> last common session
    for d in common:
        wd = int((np.datetime64(d, "D").astype(int) + 3) % 7)          # 0=Mon
        thu = str(np.datetime64(d, "D") + np.int64(3 - wd))
        prev = week_of.get(thu)
        if prev is None or d > prev:
            week_of[thu] = d
    wk = sorted(week_of.values())
    s = np.array([0.5 * (np.log(closes["QQEW"][d] / closes["QQQ"][d])
                         + np.log(closes["RSP"][d] / closes["SPY"][d])) for d in wk])
    leg_week: dict[str, int] = {}
    prior = 0  # initial leg SPY (declared)
    for j, d in enumerate(wk):
        if j >= NG5_L + NG5_ZWIN - 1:
            lo = j - (NG5_ZWIN - 1)
            hist = s[lo:j + 1] - s[lo - NG5_L: j + 1 - NG5_L]
            m = float(s[j] - s[j - NG5_L])
            sd = float(np.std(hist, ddof=1))
            if np.isfinite(m) and np.isfinite(sd) and sd > 0:
                prior = 1 if (m / sd) >= 0 else 0
        leg_week[d] = prior
    dec = sorted(leg_week)
    leg_arr = np.full(len(grid), np.nan)
    pos = 0
    for k in range(len(dec) - 1):
        d0, d1 = dec[k], dec[k + 1]
        while pos < len(grid) and grid[pos] <= d0:
            pos += 1
        while pos < len(grid) and grid[pos] <= d1:
            leg_arr[pos] = leg_week[d0]
            pos += 1
    while pos < len(grid):  # after the last decision: prior leg carried (declared)
        leg_arr[pos] = leg_week[dec[-1]]
        pos += 1
    meta = {"weeks": len(wk), "decisions": len(dec),
            "first_decision": dec[0] if dec else None,
            "grid_share_qqq_leg": (round(float(np.nanmean(leg_arr)), 4)
                                   if np.isfinite(leg_arr).any() else None)}
    return leg_arr, meta


# ---------------------------------------------------------------- per-name math

def load_symbol(sym: str):
    rows = json.loads(gzip.decompress((CACHE / f"{sym}.json.gz").read_bytes()))
    seen: set[str] = set()
    rows2 = []
    for r in rows:
        if r["date"] in seen:
            continue
        seen.add(r["date"])
        rows2.append(r)
    rows2.sort(key=lambda r: r["date"])
    dates = [r["date"] for r in rows2]
    o = np.array([r["open"] for r in rows2], dtype=float)
    h = np.array([r["high"] for r in rows2], dtype=float)
    l = np.array([r["low"] for r in rows2], dtype=float)
    c = np.array([r["close"] for r in rows2], dtype=float)
    ac = np.array([r["adjusted_close"] for r in rows2], dtype=float)
    v = np.array([r["volume"] for r in rows2], dtype=float)
    fac = np.divide(ac, c, out=np.ones_like(ac), where=c != 0)
    return dates, o, h, l, c, ac, v, fac


def ret_series(ac: np.ndarray) -> np.ndarray:
    r = np.full(len(ac), np.nan)
    if len(ac) > 1:
        with np.errstate(divide="ignore", invalid="ignore"):
            r[1:] = ac[1:] / ac[:-1] - 1.0
    return r


def shift_ret(ac: np.ndarray, k: int) -> np.ndarray:
    """adj_close_t / adj_close_{t-(k-1)} - 1 (k served sessions inclusive)."""
    n = len(ac)
    out = np.full(n, np.nan)
    if n >= k:
        with np.errstate(divide="ignore", invalid="ignore"):
            out[k - 1:] = ac[k - 1:] / ac[:n - k + 1] - 1.0
    return out


def rolling_std_finite(r: np.ndarray, w: int) -> np.ndarray:
    """Sample stdev (ddof=1) of the trailing w returns; requires all w finite."""
    n = len(r)
    out = np.full(n, np.nan)
    if n < w:
        return out
    fin = np.isfinite(r).astype(float)
    x = np.where(np.isfinite(r), r, 0.0)
    c1 = np.cumsum(np.r_[0.0, x])
    c2 = np.cumsum(np.r_[0.0, x * x])
    cf = np.cumsum(np.r_[0.0, fin])
    s1 = c1[w:] - c1[:-w]
    s2 = c2[w:] - c2[:-w]
    sf = cf[w:] - cf[:-w]
    var = np.maximum(s2 - s1 * s1 / w, 0.0) / (w - 1)
    vals = np.sqrt(var)
    vals[sf != w] = np.nan
    out[w - 1:] = vals
    return out


def rolling_max_incl(x: np.ndarray, w: int) -> np.ndarray:
    """Trailing w-session max INCLUDING the current session."""
    n = len(x)
    out = np.full(n, np.nan)
    for i in range(w - 1, n):
        out[i] = x[i - w + 1:i + 1].max()
    return out


def rolling_median_prev(x: np.ndarray, w: int) -> np.ndarray:
    """Median of the w sessions BEFORE i (excludes i)."""
    n = len(x)
    out = np.full(n, np.nan)
    for i in range(w, n):
        out[i] = np.median(x[i - w:i])
    return out


def beta63_on_grid(gpos: np.ndarray, r: np.ndarray, spy_ret: np.ndarray,
                   n_grid: int) -> np.ndarray:
    """Rolling BETA_WINDOW-grid-session OLS beta of served returns on SPY."""
    out = np.full(n_grid, np.nan)
    if len(gpos) == 0:
        return out
    g0, g1 = int(gpos[0]), int(gpos[-1])
    L = g1 - g0 + 1
    fin = np.isfinite(r)
    present = np.zeros(L)
    present[gpos[fin] - g0] = 1.0
    x_raw = spy_ret[g0:g1 + 1]
    xfin = np.isfinite(x_raw)
    present = present * xfin.astype(float)
    x0 = np.where(xfin, x_raw, 0.0) * present
    yfull = np.zeros(L)
    yfull[gpos[fin] - g0] = r[fin]
    y0 = yfull * present

    def roll(cs: np.ndarray) -> np.ndarray:
        c = np.cumsum(np.r_[np.zeros(BETA_WINDOW), cs])
        return c[BETA_WINDOW:] - c[:-BETA_WINDOW]

    cn, cx, cy = roll(present), roll(x0), roll(y0)
    cxx, cyy, cxy = roll(x0 * x0), roll(y0 * y0), roll(x0 * y0)
    k = BETA_WINDOW - 1
    n = cn[k:]
    den = n * cxx[k:] - cx[k:] ** 2
    num = n * cxy[k:] - cx[k:] * cy[k:]
    beta = np.divide(num, den, out=np.full(len(n), np.nan), where=den > 0)
    beta = np.where(n >= BETA_MIN_PRESENT, beta, np.nan)
    out[g0 + np.arange(k, L)] = beta
    return out


class Flats:
    def __init__(self):
        self.d: dict[str, list] = {k: [] for k in SHADOW_KEYS}

    def add(self, key: str, arr: np.ndarray):
        self.d[key].append(np.asarray(arr, dtype=np.float64))

    def cat(self, key: str) -> np.ndarray:
        parts = self.d[key]
        return np.concatenate(parts) if parts else np.array([])


# ---------------------------------------------------------------- assembly helpers

def per_session_threshold(values: np.ndarray, gpos: np.ndarray, n_grid: int,
                          kind: str) -> np.ndarray:
    """Per-grid-session statistic over the cross-section of finite values."""
    thr = np.full(n_grid, np.nan)
    order = np.argsort(gpos, kind="stable")
    v = values[order]
    g = gpos[order]
    uniq, starts = np.unique(g, return_index=True)
    ends = np.r_[starts[1:], len(g)]
    for u, a, b in zip(uniq, starts, ends):
        seg = v[a:b]
        seg = seg[np.isfinite(seg)]
        if seg.size >= 3:
            if kind == "tercile_top":
                thr[u] = np.quantile(seg, 2.0 / 3.0)
            elif kind == "z":
                mu, sd = seg.mean(), seg.std(ddof=0)
                if sd > 0:
                    thr[u] = mu  # z computed as (value - thr) / scale below
    if kind == "z":
        # second pass for scale
        scale = np.full(n_grid, np.nan)
        for u, a, b in zip(uniq, starts, ends):
            seg = v[a:b]
            seg = seg[np.isfinite(seg)]
            if seg.size >= 3 and seg.std(ddof=0) > 0:
                scale[u] = seg.std(ddof=0)
        return np.vstack([thr, scale])
    return thr


def lag1_autocorr(b: np.ndarray):
    return pearson(b[:-1], b[1:])


# ---------------------------------------------------------------- main run

def _run(hb, inv: dict) -> dict:
    t0 = time.time()
    auth = verify_input_authority()
    expected_census = auth["expected_census"]
    log(f"input authority OK: {auth['checks']['cache_symbols']} cache symbols, "
        f"{auth['checks']['expected_census_rows']} census rows, "
        f"P0 {auth['checks']['p0_verdict']}")

    env = load_grid_and_folds()
    grid, gidx, fold_of = env["grid"], env["gidx"], env["fold_of"]
    n_grid = len(grid)
    fold_grid = [fold_of[d] for d in grid]
    log(f"grid {n_grid} sessions {grid[0]}..{grid[-1]}")

    ng5_pincheck = verify_ng5_pins()
    ng5_leg, ng5_meta = ng5_weekly_leg_state(grid)
    log(f"NG5 leg state: {ng5_meta}")

    spec = importlib.util.spec_from_file_location("sng6_p0_census_run", P0 / "p0_census_run.py")
    p0mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(p0mod)
    compute_events = p0mod.compute_events

    flats = Flats()
    census_seen: set = set()
    event_dates_bookable: list[str] = []
    raw_event_keys: set = set()
    event_ledger: list = []   # (chunk, i, footprint_j_list) for BOOKABLE anchor events
    sym_state: list = []      # per-chunk (gpos int64, floor_ok bool, date_fold list)
    cb_floors = np.zeros(n_grid)
    dvol_only_held = np.zeros(n_grid)
    range_only_held = np.zeros(n_grid)
    randtiming_held = np.zeros(n_grid)
    rebal_records: list = []
    episodes = {"dvol_only": 0, "range_only": 0, "randtiming": 0}
    summary = {"names": 0, "rows": 0, "anchor_footprint_sessions": 0,
               "neighbour_events": 0, "neighbour_dropped_no_session": 0,
               "raw_bookable_events": 0}

    members = json.loads((P0 / "cohort" / "cohort_members.json").read_text())
    death_dates = {m["ticker"]: m["death_date"] for m in members if m.get("death_date")}

    def beat(phase):
        if time.time() - _last_hb["t"] >= 45:
            _last_hb["t"] = time.time()
            hb.heartbeat(extra={"phase": phase, "names_done": summary["names"]})

    for sym in sorted(auth["symbols"]):
        path = CACHE / f"{sym}.json.gz"
        if not path.exists():
            continue
        dates, o, h, l, c, ac, v, fac = load_symbol(sym)
        n = len(dates)
        ao, ah, al = o * fac, h * fac, l * fac
        chunk = summary["names"]
        summary["names"] += 1
        summary["rows"] += n

        events, _ = compute_events(dates, ao, ah, al, ac, v)      # frozen P0 census
        raw_events, _ = compute_events(dates, o, h, l, c, v)      # dividend check only
        for e in raw_events:
            if e["bookable"]:
                raw_event_keys.add((sym, e["date"]))
        summary["raw_bookable_events"] += sum(1 for e in raw_events if e["bookable"])
        for e in events:
            census_seen.add((sym, e["date"], bool(e["bookable"])))
            if e["bookable"]:
                event_dates_bookable.append(e["date"])
                if e["date"] not in gidx:
                    summary["bookable_events_off_decision_grid"] = \
                        summary.get("bookable_events_off_decision_grid", 0) + 1

        # the pooled measurement grid is the FROZEN SPY-served decision grid;
        # a name's off-grid served sessions (weekend/holiday bars, censused at
        # P0) carry state computation but produce no (name, session) row
        on_grid = np.array([d in gidx for d in dates], dtype=bool)
        gpos_full = np.full(n, -1, dtype=np.int64)
        og = np.nonzero(on_grid)[0]
        gpos_full[og] = [gidx[dates[j]] for j in og]
        gpos = gpos_full[og]
        date_fold = [fold_of.get(d) for d in dates]

        def fp_on_grid(start: int, end: int, efold) -> list[int]:
            """Held served indices inside the entry fold AND on the grid."""
            return [j for j in range(max(0, start), min(end + 1, n))
                    if on_grid[j] and date_fold[j] == efold]

        if n == 0 or len(og) == 0:
            for k in SHADOW_KEYS:
                flats.add(k, np.array([]))
            sym_state.append((np.array([], dtype=np.int64), np.zeros(0, dtype=bool), []))
            beat("per_symbol_pass")
            continue

        dvol = ac * v
        r = ret_series(ac)

        # ---- shadows (trailing, served-session basis; rows on the grid only)
        flats.add("mom63", shift_ret(ac, 63)[on_grid])
        flats.add("mom121_pre", (shift_ret(ac, 252) - shift_ret(ac, 21))[on_grid])
        flats.add("rev5", shift_ret(ac, 5)[on_grid])
        flats.add("rev21", shift_ret(ac, 21)[on_grid])
        dd = 1.0 - ac / rolling_max_incl(ac, 252) if n >= 252 else np.full(n, np.nan)
        flats.add("dd252", dd[on_grid])
        med60 = rolling_median_prev(dvol, DVOL_WINDOW)
        with np.errstate(divide="ignore", invalid="ignore"):
            dshock = np.where(med60 > 0, dvol / med60, np.nan)
        flats.add("dvolshock", dshock[on_grid])
        flats.add("rv20", rolling_std_finite(r, 20)[on_grid])
        flats.add("rv60", rolling_std_finite(r, 60)[on_grid])
        down = np.where(np.isfinite(r), np.minimum(r, 0.0) ** 2, 0.0)
        tot = np.where(np.isfinite(r), r ** 2, 0.0)
        cnt = np.where(np.isfinite(r), 1.0, 0.0)
        sv = np.full(n, np.nan)
        if n >= 60:
            w = 60
            cd = np.cumsum(np.r_[0.0, down])
            ct = np.cumsum(np.r_[0.0, tot])
            cc = np.cumsum(np.r_[0.0, cnt])
            sd_ = cd[w:] - cd[:-w]
            st_ = ct[w:] - ct[:-w]
            sc_ = cc[w:] - cc[:-w]
            with np.errstate(divide="ignore", invalid="ignore"):
                vals = np.where((st_ > 0) & (sc_ >= w), sd_ / st_, np.nan)
            sv[w - 1:] = vals
        flats.add("svshare", sv[on_grid])
        b63 = beta63_on_grid(gpos, r[og], env["spy_ret"], n_grid)
        flats.add("beta63", b63[gpos])

        dprox = np.zeros(n)
        dth = death_dates.get(sym)
        if dth is not None:
            elig = [j for j, d in enumerate(dates) if d <= dth]
            if elig:
                dprox[max(0, elig[-1] - 10):elig[-1] + 1] = 1.0
        flats.add("deathprox", dprox[on_grid])

        # ---- book states + event windows + neighbour confirmation
        anchor_book = np.zeros(n)
        evmask = np.zeros(n)
        neigh_book = np.zeros(n)
        for e in events:
            if not e["bookable"]:
                continue
            i = e["i"]
            evmask[i:min(i + HOLD + 1, n)] = 1.0
            efold = date_fold[i + 1] if i + 1 <= n - 1 else None
            js_on = fp_on_grid(i + 1, i + HOLD, efold)
            li = int(np.searchsorted(og, i)) if on_grid[i] else -1
            ljs = np.searchsorted(og, np.array(js_on, dtype=np.int64)) if js_on else []
            event_ledger.append((chunk, li, ljs))
            if i + 1 <= n - 1:
                anchor_book[fp_on_grid(i + 1, i + HOLD, efold)] = 1.0
                if ac[i + 1] > e["prior_low"]:
                    if i + 2 <= n - 1:
                        neigh_book[fp_on_grid(i + 2, i + 1 + HOLD,
                                              date_fold[i + 2])] = 1.0
                        summary["neighbour_events"] += 1
                    else:
                        summary["neighbour_dropped_no_session"] += 1
        summary["anchor_footprint_sessions"] += int((anchor_book > 0).sum())
        flats.add("book_anchor", anchor_book[on_grid])
        flats.add("book_neigh", neigh_book[on_grid])
        flats.add("evmask", evmask[on_grid])
        flats.add("gpos", gpos)

        raw_book = np.zeros(n)
        for e in raw_events:
            if e["bookable"] and e["i"] + 1 <= n - 1:
                raw_book[fp_on_grid(e["i"] + 1, e["i"] + HOLD,
                                    date_fold[e["i"] + 1])] = 1.0
        flats.add("book_rawanchor", raw_book[on_grid])

        # ---- controls accumulation (Q-11; nulls only, never PnL)
        floor_ok = (ac >= FLOOR_PRICE) & (med60 >= FLOOR_DVOL)
        dvol_ok = np.zeros(n, dtype=bool)
        pos_ok = np.nonzero(med60 > 0)[0]
        if len(pos_ok):
            dvol_ok[pos_ok] = dvol[pos_ok] / med60[pos_ok] >= DVOL_MULT
        for i in np.nonzero(dvol_ok & floor_ok)[0]:
            if i + 1 <= n - 1:
                js = fp_on_grid(i + 1, i + HOLD, date_fold[i + 1])
                if js:
                    np.add.at(dvol_only_held, gpos_full[js], 1.0)
                    episodes["dvol_only"] += 1
        hl_ok = ah > al
        with np.errstate(divide="ignore", invalid="ignore"):
            range_frac = np.where(hl_ok, (ac - al) / (ah - al), np.nan)
        rng_ok = (range_frac >= 0.5) & dvol_ok & floor_ok
        for i in np.nonzero(rng_ok)[0]:
            if i + 1 <= n - 1:
                js = fp_on_grid(i + 1, i + HOLD, date_fold[i + 1])
                if js:
                    np.add.at(range_only_held, gpos_full[js], 1.0)
                    episodes["range_only"] += 1
        np.add.at(cb_floors, gpos_full[floor_ok & on_grid], 1.0)
        for j in np.nonzero(floor_ok & on_grid)[0]:
            if gpos_full[j] % RANDOM_TIMING_EVERY == 0 and j + 1 <= n - 1:
                js = fp_on_grid(j + 1, j + HOLD, date_fold[j + 1])
                if js:
                    np.add.at(randtiming_held, gpos_full[js], 1.0)
                    episodes["randtiming"] += 1
        ret5 = shift_ret(ac, 5)
        for j in np.nonzero(floor_ok & on_grid & np.isfinite(ret5))[0]:
            if gpos_full[j] % REVERSAL_REBALANCE == 0:
                rebal_records.append((int(gpos_full[j]), float(ret5[j])))
        sym_state.append((gpos, floor_ok[on_grid],
                          [date_fold[j] for j in og]))
        beat("per_symbol_pass")

    # ---------------- census reproduction (fail-closed)
    census_reproduced = census_seen == expected_census
    if not census_reproduced:
        miss = len(expected_census - census_seen)
        extra = len(census_seen - expected_census)
        raise InputAuthorityError(
            f"recomputed census != P0 census (missing={miss}, extra={extra})")

    log("per-symbol pass complete; assembling pooled arrays")
    hb.heartbeat(extra={"phase": "assemble"})
    F = {k: flats.cat(k) for k in SHADOW_KEYS}
    gpos_flat = F["gpos"].astype(np.int64)
    n_flat = len(gpos_flat)
    offsets = np.cumsum(np.r_[0, [len(a) for a in flats.d["gpos"]]])

    # ---- cross-sectional transforms
    mu_sc = per_session_threshold(F["mom121_pre"], gpos_flat, n_grid, "z")
    thr = mu_sc[0][gpos_flat]
    scl = mu_sc[1][gpos_flat]
    with np.errstate(invalid="ignore"):
        mom121 = np.where(np.isfinite(thr) & np.isfinite(scl),
                          (F["mom121_pre"] - thr) / scl, np.nan)

    rv_terc_thr = {w: per_session_threshold(F[f"rv{w}"], gpos_flat, n_grid,
                                            "tercile_top") for w in RV_WINDOWS}
    voltercile = {w: np.where(np.isfinite(F[f"rv{w}"]) & np.isfinite(rv_terc_thr[w][gpos_flat]),
                              (F[f"rv{w}"] >= rv_terc_thr[w][gpos_flat]).astype(float), np.nan)
                  for w in RV_WINDOWS}

    # ---- grid-level shadows broadcast to (name, session)
    if event_dates_bookable:
        dow_hist = np.bincount(weekday0(np.array(event_dates_bookable)), minlength=5).astype(float)
    else:
        dow_hist = np.zeros(5)
    dow_share = dow_hist / max(1.0, dow_hist.sum())
    dow_state_grid = dow_share[weekday0(np.array(grid))]
    month_start_grid = env["month_start"].astype(float)
    month_end_grid = env["month_end"].astype(float)
    dow_flat = dow_state_grid[gpos_flat]
    mstart_flat = month_start_grid[gpos_flat]
    mend_flat = month_end_grid[gpos_flat]
    ng5_flat = ng5_leg[gpos_flat]

    # ---- vol-restricted event footprints (deferred tercile lookups)
    volrestricted = {w: np.zeros(n_flat) for w in RV_WINDOWS}
    vr_events = {w: 0 for w in RV_WINDOWS}
    for chunk, li, ljs in event_ledger:
        if li < 0 or len(ljs) == 0:
            continue
        base = offsets[chunk]
        fi = base + li
        g_i = int(gpos_flat[fi])
        for w in RV_WINDOWS:
            thr_i = rv_terc_thr[w][g_i]
            v_i = F[f"rv{w}"][fi]
            if np.isfinite(thr_i) and np.isfinite(v_i) and v_i >= thr_i:
                volrestricted[w][base + np.asarray(ljs, dtype=np.int64)] = 1.0
                vr_events[w] += 1

    # ---- C-CAL-HIST: start = every observed bookable anchor event date;
    #      hold EVERY name bookable at that session for H=10 (A4 BC-4a)
    cal_starts = {gidx[d] for d in event_dates_bookable if d in gidx}
    calhist_held = np.zeros(n_grid)
    calhist_episodes = 0
    for (gpos_s, floor_ok, date_fold) in sym_state:
        ns = len(gpos_s)
        for j in np.nonzero(floor_ok)[0]:
            if int(gpos_s[j]) in cal_starts and j + 1 <= ns - 1:
                efold = date_fold[j + 1]
                js = [k for k in range(j + 1, min(j + 1 + HOLD, ns)) if date_fold[k] == efold]
                np.add.at(calhist_held, gpos_s[js], 1.0)
                calhist_episodes += 1

    # ---- C-REVERSAL-PLAIN: every-5th-session rebalance, bottom-5 by 5s return
    reversal_held = np.zeros(n_grid)
    rebal = {}
    for g, v in rebal_records:
        rebal.setdefault(g, []).append(v)
    reversal_rebalances = 0
    for g, vals in rebal.items():
        take = np.sort(np.array(vals))[:5]
        entry = g + 1
        if entry >= n_grid:
            continue
        efold = fold_grid[entry]
        for t in range(entry, min(entry + REVERSAL_REBALANCE, n_grid)):
            if fold_grid[t] == efold:
                reversal_held[t] += len(take)
        reversal_rebalances += 1

    # ---------------- rho battery
    targets = {"anchor": F["book_anchor"], "neighbour": F["book_neigh"]}
    cond = F["evmask"] > 0.5
    battery: dict = {}

    def measure(name: str, series: np.ndarray):
        recs = {}
        for tgt, book in targets.items():
            recs[tgt] = {"cohort_wide": rho_record(series, book)}
            if cond.any():
                recs[tgt]["event_conditional"] = rho_record(series[cond], book[cond])
        battery[name] = recs

    measure("momentum_63s_generic", F["mom63"])
    measure("momentum_12_1_xsec", mom121)
    measure("reversal_5d", F["rev5"])
    measure("reversal_21d", F["rev21"])
    measure("drawdown_depth_252", F["dd252"])
    measure("dvol_shock", F["dvolshock"])
    measure("realized_vol_level_20d", F["rv20"])
    measure("realized_vol_level_60d", F["rv60"])
    for w in RV_WINDOWS:
        measure(f"vol_tercile_top_book_{w}d", voltercile[w])
        measure(f"vol_restricted_event_{w}d", volrestricted[w])
    measure("semivariance_share_60d", F["svshare"])
    measure("rolling_beta_63d", F["beta63"])
    measure("death_proximity_10s", F["deathprox"])
    measure("calendar_dow_state", dow_flat)
    measure("calendar_monthstart_state", mstart_flat)
    measure("calendar_monthend_state", mend_flat)
    measure("ng5_relative_breadth_rotation_state", ng5_flat)

    # ---------------- neighbour self-subsumption (P-20)
    self_sub = rho_record(F["book_neigh"], F["book_anchor"])
    self_sub["form"] = "cohort_wide pooled book-vs-book (P-20)"

    # ---------------- control nulls (Q-11: population + lag-1 autocorrelation)
    def null_report(name, held, ep):
        p, n = lag1_autocorr(held)
        sd = float(held.std(ddof=0))
        valid = ep > 0 and sd > 0 and p is not None
        return {"population_book_episodes": int(ep),
                "held_name_sessions": int(held.sum()),
                "held_count_series_mean": round(float(held.mean()), 4),
                "held_count_series_sd": round(sd, 4),
                "lag1_autocorrelation": None if p is None else round(p, 6),
                "autocorr_pairs": n,
                "disposition": ("VALID_NULL_IDENTIFIED" if valid else "NOT_ADJUDICABLE"),
                "not_adjudicable_reason": (None if valid else
                                           "unpopulated or degenerate (zero-variance) null")}

    control_nulls = {
        "C-REVERSAL-PLAIN": null_report("C-REVERSAL-PLAIN", reversal_held,
                                        5 * reversal_rebalances),
        "C-RANGE-ONLY": null_report("C-RANGE-ONLY", range_only_held, episodes["range_only"]),
        "C-DVOL-ONLY": null_report("C-DVOL-ONLY", dvol_only_held, episodes["dvol_only"]),
        "C-RANDOM-TIMING": null_report("C-RANDOM-TIMING", randtiming_held,
                                       episodes["randtiming"]),
        "C-CAL-HIST": null_report("C-CAL-HIST", calhist_held, calhist_episodes),
    }
    control_null_rules = ("Q-11 C-NULL-VALIDITY: population + lag-1 autocorrelation of "
                          "every null, reported BEFORE any control may kill; book-state "
                          "nulls only (no PnL exists at D2). Deterministic rules: "
                          "C-REVERSAL-PLAIN = every-5th-grid-session bottom-5 by trailing "
                          "5-session adjusted return (bookable cohort), 5-session holds; "
                          "C-RANGE-ONLY = range>=0.5 + participation + floors, NO level "
                          "event, H=10; C-DVOL-ONLY = participation + floors only, H=10; "
                          "C-RANDOM-TIMING = every-63rd-grid-session, all bookable names, "
                          "H=10; C-CAL-HIST = start on EVERY observed bookable event "
                          "decision date, all bookable names, H=10 (reproduces the "
                          "event-date histogram exactly). All footprints force-flat at "
                          "the entry session's fold boundary and at name death.")

    # ---------------- dividend-decomposition non-scored check
    adj_keys = {(s, d) for (s, d, b) in census_seen if b}
    inter = adj_keys & raw_event_keys
    ov_adj = len(inter) / max(1, len(adj_keys))
    ov_raw = len(inter) / max(1, len(raw_event_keys))
    div_rho = rho_record(F["book_rawanchor"], F["book_anchor"])
    distribution_dominated = min(ov_adj, ov_raw) < DIVIDEND_DOMINATED_FRACTION
    dividend_check = {
        "adjusted_basis_bookable_events": len(adj_keys),
        "raw_basis_bookable_events": len(raw_event_keys),
        "overlap_events": len(inter),
        "overlap_fraction_of_adjusted": round(ov_adj, 6),
        "overlap_fraction_of_raw": round(ov_raw, 6),
        "book_state_rho_adjusted_vs_raw": div_rho,
        "declared_threshold": DIVIDEND_DOMINATED_FRACTION,
        "distribution_dominated_flag": ("DISTRIBUTION_DOMINATED_FAIL_CLOSED"
                                        if distribution_dominated
                                        else "NOT_DISTRIBUTION_DOMINATED"),
        "scored_slot": "none (non-scored diagnostic; no 0.20 bar)",
    }

    # ---------------- verdict
    def records_for(target):
        out = []
        for name, per in battery.items():
            for form, rec in per[target].items():
                out.append((name, form, rec))
        return out

    anchor_hits = [(n2, f2, r2) for n2, f2, r2 in records_for("anchor")
                   if r2["abs_max"] is not None and r2["abs_max"] > BAR]
    neigh_hits = [(n2, f2, r2) for n2, f2, r2 in records_for("neighbour")
                  if r2["abs_max"] is not None and r2["abs_max"] > BAR]
    self_subsumed = self_sub["abs_max"] is not None and self_sub["abs_max"] > SELF_SUB_BAR

    anchor_r0 = "R0_VETO" if anchor_hits else "PASS"
    neigh_r0 = "R0_VETO" if neigh_hits else "PASS"
    neigh_disp = ("SELF_SUBSUMED" if self_subsumed
                  else ("R0_VETO" if neigh_hits else "DISTINCT_BOOK"))
    if anchor_r0 == "R0_VETO":
        overall = "D2_R0_VETO"
        selection = "EMPTY -> the cycle's close path (plan §7)"
        next_action = "Lead: D2-veto close path"
    else:
        overall = "D2_PASS"
        survivors = "anchor only" if neigh_disp in ("SELF_SUBSUMED", "R0_VETO") \
            else "anchor + neighbour"
        selection = (f"selection may proceed at S with: {survivors}"
                     if neigh_disp != "SELF_SUBSUMED" else
                     "neighbour SELF-SUBSUMED -> family continues anchor-only; "
                     "selection may proceed at S with: anchor only")
        next_action = "Lead: selection freeze (S)" + (
            " (anchor only; neighbour self-subsumed)" if self_subsumed else "")

    not_adjudicable = [
        {"item": "dgs10_level_state", "reason": "UNMEASURABLE fail-closed: no rates series "
         "constructible from the P0 price/volume cache (rates-proxy scan: "
         f"{auth['checks']['rates_proxy_symbols_in_cache']}); this cycle's P0 staged no "
         "exogenous rates authority. Recorded, never skipped silently."},
    ] + [{"item": f"control_null:{k}", "reason": v["not_adjudicable_reason"]}
         for k, v in control_nulls.items() if v["disposition"] == "NOT_ADJUDICABLE"]

    incidents = []
    if distribution_dominated:
        incidents.append("dividend-decomposition: DISTRIBUTION_DOMINATED_FAIL_CLOSED "
                         "(non-scored representation-contamination flag; adjusted-basis "
                         "event identity is distribution-dominated per the declared 0.80 "
                         "overlap criterion)")
    if self_subsumed:
        incidents.append("neighbour SELF-SUBSUMED (P-20): pooled |rho| vs anchor book state "
                         f"> {SELF_SUB_BAR}; family continues anchor-only per d1_freeze")

    verdict = {
        "schema": "stocks_ng6_d2_verdict@1",
        "cycle_id": "STOCKS-NG6",
        "role": "A8-D2 measurement lane (non-scored ancestry battery)",
        "plan": "plans/PLAN_stocks_ng6.md §6/§7",
        "measured_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": round(time.time() - t0, 1),
        "no_pnl_computed": True,
        "no_anchor_return_computed": True,
        "inventory": {
            "path": "research/control/stocks_ng6_run/d2/shadow_inventory.json",
            "sha256": INV_SHA256,
            "hash_verified_before_any_rho": True,
            "committed_at": "833641ed (G8 commit-first)",
        },
        "input_authority": {
            "cache": "data_raw/stocks_ng6_eod/",
            "cache_symbols": auth["checks"]["cache_symbols"],
            "rows_scanned": summary["rows"],
            "retrieval_manifest_sha256_match": auth["checks"]["retrieval_manifest_sha256_match"],
            "events_census_sha256_match": auth["checks"]["events_census_sha256_match"],
            "census_reproduction_exact": census_reproduced,
            "p0_verdict": auth["checks"]["p0_verdict"],
        },
        "grid": {"sessions": n_grid, "window": [grid[0], grid[-1]],
                 "folds": {fd["id"]: [fd["start"], fd["end"]] for fd in env["folds_doc"]["folds"]}},
        "books": {
            "anchor_events_bookable": len(adj_keys),
            "anchor_book_state_sessions": int(F["book_anchor"].sum()),
            "neighbour_events": summary["neighbour_events"],
            "neighbour_book_state_sessions": int(F["book_neigh"].sum()),
            "neighbour_dropped_no_confirm_or_exit_session":
                summary["neighbour_dropped_no_session"],
            "bookable_events_off_decision_grid":
                summary.get("bookable_events_off_decision_grid", 0),
            "grid_note": "pooled rows exist only on frozen SPY-served decision-grid "
                         "sessions; a name's off-grid served bars (weekend/holiday "
                         "rows, censused at P0) carry served-sequence state "
                         "computation but produce no (name, session) row",
            "raw_basis_bookable_events": len(raw_event_keys),
        },
        "bar": {"R0_abs_rho": BAR, "immovable": True, "law": "G9 no-threshold-rescue"},
        "rho_battery": battery,
        "battery_reading_law": "every measured record is veto-eligible (cohort-wide AND "
                               "event-conditional) — the fail-closed direction; the "
                               "BINDING applicable forms per the frozen inventory are "
                               "the event-conditional ones for reversal/dd/dvol-shock/"
                               "vol entries",
        "neighbour_self_subsumption": self_sub,
        "control_nulls_Q11": control_nulls,
        "control_null_deterministic_rules": control_null_rules,
        "dividend_decomposition_check": dividend_check,
        "ng5_shadow_data": {"pins_verified": ng5_pincheck, "construction_meta": ng5_meta},
        "not_adjudicable": not_adjudicable,
        "incidents": incidents,
        "verdict_per_arm": {
            "SNG6-A2-P1-ANCHOR-TRAP-RECLAIM": anchor_r0,
            "SNG6-A2-P1-NEIGH-CONFIRM-2S": neigh_disp,
            "anchor_veto_firing_records": [
                {"shadow": n2, "form": f2, **r2} for n2, f2, r2 in anchor_hits],
            "neighbour_veto_firing_records": [
                {"shadow": n2, "form": f2, **r2} for n2, f2, r2 in neigh_hits],
        },
        "verdict": overall,
        "selection": selection,
        "recommended_next_action": next_action,
    }
    OUT.write_text(json.dumps(verdict, indent=1, sort_keys=True) + "\n")
    log(f"VERDICT {overall}; anchor {anchor_r0}, neighbour {neigh_disp}, "
        f"self_sub |rho|max={self_sub['abs_max']}")
    return verdict


def main() -> int:
    HERE.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(WT))
    from research.governance import heavy_lock
    from research.governance.heavy_lock import LockBusyError

    # G8: verify the inventory hash BEFORE taking the heavy lock (refuse fast)
    try:
        inv = load_inventory()
    except InventoryMismatch as exc:
        OUT.write_text(json.dumps({
            "schema": "stocks_ng6_d2_verdict@1", "cycle_id": "STOCKS-NG6",
            "verdict": "D2_REFUSED_INVENTORY_HASH_MISMATCH", "blocker": str(exc),
            "measured_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "no_pnl_computed": True}, indent=1, sort_keys=True) + "\n")
        log(f"REFUSED: {exc}")
        return 1

    lock_cmd = [sys.executable, str(Path(__file__).resolve())]
    try:
        with heavy_lock.acquire(
            cycle_id="STOCKS-NG6",
            role="D2_ANCESTRY_HEAVY",
            worktree=str(WT),
            command=lock_cmd,
            expected_artifacts=[str(OUT)],
        ) as hb:
            try:
                _run(hb, inv)
                return 0
            except (InputAuthorityError, MemoryError, OSError, ValueError) as exc:
                err = f"{type(exc).__name__}: {exc}"[:600]
                log(f"TECHABORT: {err}")
                OUT.write_text(json.dumps({
                    "schema": "stocks_ng6_d2_verdict@1", "cycle_id": "STOCKS-NG6",
                    "verdict": "D2_TECHABORT", "blocker": err,
                    "inventory_sha256": INV_SHA256,
                    "measured_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "no_pnl_computed": True}, indent=1, sort_keys=True) + "\n")
                hb.heartbeat(extra={"status": "techabort", "blocker": err})
                return 1
    except LockBusyError as exc:
        OUT.write_text(json.dumps({
            "schema": "stocks_ng6_d2_verdict@1", "cycle_id": "STOCKS-NG6",
            "verdict": "NOT_RUN_RESOURCE_CONFLICT",
            "blocker": f"machine-wide heavy lock held: {exc}"[:600],
            "measured_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "no_pnl_computed": True}, indent=1, sort_keys=True) + "\n")
        log(f"NOT_RUN_RESOURCE_CONFLICT: {exc}")
        return 1
    except Exception as exc:  # noqa: BLE001 - honest blocker verdict, lock released cleanly
        import traceback
        traceback.print_exc()
        err = f"{type(exc).__name__}: {exc}"[:600]
        log(f"TECHABORT: {err}")
        OUT.write_text(json.dumps({
            "schema": "stocks_ng6_d2_verdict@1", "cycle_id": "STOCKS-NG6",
            "verdict": "D2_TECHABORT", "blocker": err,
            "inventory_sha256": INV_SHA256,
            "measured_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "no_pnl_computed": True}, indent=1, sort_keys=True) + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
