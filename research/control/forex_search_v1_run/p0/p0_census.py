"""FOREX-SEARCH-V1 P0 census engine (plans/PLAN_forex_search_v1.md §4 F1–F7).

P0 is source engineering and census ONLY: no candidate PnL/PF/Sharpe/
drawdown/survivors/S1 evidence anywhere in this module. The fired census
counts STATE FIRINGS per configuration per fold — counts only. D2 is
SKIPPED this cycle (owner amendment §3b): no R0/ancestry rho machinery
exists here and none may be added without a new owner instruction.

Determinism: census artifacts are pure functions of the pinned staging
bytes (sha256-pinned) — a detached rerun is byte-identical except fields
explicitly labelled measured_*.

Staging is read from the extracted P-13 single-vintage TD archives
(extraction digests pinned in manifest_pin.json). The raw archives live
OUTSIDE the repo (~/staging_backups/cleanup_2026-09-12/) and are never
copied into it.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/forex-search-v1/integration")
P0 = WT / "research/control/forex_search_v1_run/p0"
STAGING = Path("/tmp/fsearch_p0_staging")

ARCHIVE_ROOT = Path("/Users/hoangminhlong/staging_backups/cleanup_2026-09-12")

# Plan §4: per-pair archive digests (plan-frozen prefixes; full digests
# pinned here as measured at P0 and re-verified on every run).
PAIR_SOURCES = {
    "EURUSD": ("forex-ng4_ez_eurusd.tar.gz", "data_raw/forex_ng4_spot/EURUSD.json",
               "01cb862bf260682c995debaf9322d38c4803b265ad0a4bbb66aea78770c43c02"),
    "GBPUSD": ("forex-v9_cpi_spot.tar.gz", "data_raw/forex_free_v9_spot/GBPUSD.json",
               "e3e4c519f4c36b394ad08c1e52ed16ae087030372febfdb5558ebcdbee83e4a7"),
    "USDCAD": ("forex-v9_cpi_spot.tar.gz", "data_raw/forex_free_v9_spot/USDCAD.json",
               "4b988c4487b2ff0284ca0ecd04b6118c23516a89a147dd87cbab3b1bbf52ec2f"),
    "AUDUSD": ("forex-v9_cpi_spot.tar.gz", "data_raw/forex_free_v9_spot/AUDUSD.json",
               "097cfe59cd702c3dd2479f37abeae5fd751fdf53cbe305ffa0ea3820e17e5e17"),
    "NZDUSD": ("forex-v9_cpi_spot.tar.gz", "data_raw/forex_free_v9_spot/NZDUSD.json",
               "7dff32999bdb38c5d972bd1ed4ff93a8807057ffb7120621f83b146dc0b79d5b"),
}
LEGS = ["EURUSD", "GBPUSD", "USDCAD", "AUDUSD", "NZDUSD"]

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# §4 F4 constants (wired for later phases; NO cost computation at P0).
COST_BPS_PER_FILL = 1.5
FIN_BPS_PER_NIGHT = 1.7
STRESS_MULTIPLIER = 2.0

# §8 warmup (master-calendar 1-based first decision bar):
WARMUP_BARS = {"VOL-DRIFT": 252, "OPEN-GAP": 252,
               "CLV-DIVERGENCE": 60, "EXTREME-FADE": 60, "CLOCK-COND": 60}
CLV_SLOPE_WINDOW_IS_20 = 20  # 20-bar CLV pressure window (plan §5 family 1)
GAP_WINDOW = 252             # trailing signed-gap distribution (§5 family 3)
VOL_TERCILE_WINDOW = 252     # trailing tercile window (§5 family 4)
FIRED_RATE_FORM = (0.02, 0.10)
POOLED_FLOOR_PER_FOLD = 30
R5_MAX_WEEKDAY_SHARE_FLOOR = 0.35  # recorded only at P0; R5 evaluates later
R2_PER_STATE_FLOOR = 10            # recorded only at P0; R2 evaluates later


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sha256_obj(obj) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


# ---------------------------------------------------------------- staging

def load_leg(path: Path) -> dict:
    """Load one TD staging JSON into ascending-date arrays.

    Keeps the ORIGINAL strings (vendor bytes) for re-pull comparison and
    float arrays for integrity/census math. No ffill, no repair: any
    integrity violation raises (fail-closed).
    """
    raw = json.loads(path.read_text())
    values = raw["values"]
    dates, o, h, l, c = [], [], [], [], []
    os_, hs, ls, cs = [], [], [], []
    seen = set()
    for row in values:  # served newest-first; normalize to ascending below
        d = row["datetime"]
        if not DATE_RE.match(d):
            raise ValueError(f"non-date stamp {d!r} in {path.name}")
        if d in seen:
            raise ValueError(f"duplicate stamp {d!r} in {path.name}")
        seen.add(d)
        dates.append(d)
        os_.append(row["open"]); hs.append(row["high"])
        ls.append(row["low"]); cs.append(row["close"])
    order = sorted(range(len(dates)), key=lambda i: dates[i])
    dates = [dates[i] for i in order]
    os_ = [os_[i] for i in order]; hs = [hs[i] for i in order]
    ls = [ls[i] for i in order]; cs = [cs[i] for i in order]
    o = np.array([float(x) for x in os_])
    h = np.array([float(x) for x in hs])
    l = np.array([float(x) for x in ls])
    c = np.array([float(x) for x in cs])
    # Hard integrity failures abort (fail-closed). Vendor micro-rounding
    # inconsistencies (H < max(O,C) or L > min(O,C) by ~1 point) are CENSUS
    # items: counted and disclosed, never repaired, never ffilled.
    if np.any(o <= 0) or np.any(h <= 0) or np.any(l <= 0) or np.any(c <= 0):
        raise ValueError(f"non-positive price in {path.name}")
    return {"symbol": raw["meta"]["symbol"], "dates": dates,
            "open": o, "high": h, "low": l, "close": c,
            "open_s": os_, "high_s": hs, "low_s": ls, "close_s": cs,
            "source_archive": None, "source_member": None}


def structural_census(leg: dict) -> dict:
    """F1(ii) per-leg structural census. Violations are COUNTED, never
    repaired: the archive bytes stay exactly as served (vintage law).
    """
    integ = ohlc_integrity(leg)
    violation_rows = (integ["high_lt_max_open_close_rows"]
                      + integ["low_gt_min_open_close_rows"])
    dates = leg["dates"]
    from datetime import date, timedelta
    weekdays = {}
    for d in dates:
        y, m, dd = (int(x) for x in d.split("-"))
        wd = date(y, m, dd).isoweekday()
        weekdays[wd] = weekdays.get(wd, 0) + 1
    # strictly monotone stamps, one bar per date (load_leg already rejects dupes)
    mono = all(dates[i] < dates[i + 1] for i in range(len(dates) - 1))
    # intra-leg holiday census: missing WEEKDAY calendar dates between
    # consecutive own bars (weekend spans excluded). Never filled — counted.
    holidays = []
    ds = [date(*map(int, d.split("-"))) for d in dates]
    for i in range(len(ds) - 1):
        d1, d2 = ds[i], ds[i + 1]
        cur = d1 + timedelta(days=1)
        while cur < d2:
            if cur.isoweekday() <= 5:
                holidays.append(cur.isoformat())
            cur += timedelta(days=1)
    return {
        "intra_leg_weekday_holidays": holidays,
        "intra_leg_weekday_holiday_count": len(holidays),
        "ohlc_integrity": integ,
        "ohlc_violation_rows": violation_rows,
        "ohlc_violation_rate": round(violation_rows / max(len(dates), 1), 8),
        "rows": len(dates),
        "first": dates[0], "last": dates[-1],
        "strictly_monotone_dates": mono,
        "date_only_stamps": True,  # enforced by DATE_RE in load_leg
        "weekday_bar_counts": {str(k): v for k, v in sorted(weekdays.items())},
        "fields": ["close", "datetime", "high", "low", "open"],
        "volume_field_present": False,
    }


def ohlc_integrity(leg: dict) -> dict:
    o, h, l, c = leg["open"], leg["high"], leg["low"], leg["close"]
    return {
        "high_lt_max_open_close_rows": int(np.sum(h < np.maximum(o, c))),
        "low_gt_min_open_close_rows": int(np.sum(l > np.minimum(o, c))),
        "nonpositive_price_rows": int(np.sum(np.minimum(np.minimum(o, h),
                                                        np.minimum(l, c)) <= 0)),
        "zero_range_rows": int(np.sum(h == l)),
    }


# ------------------------------------------------------------- calendar F1(v)

def calendar_census(legs: dict) -> dict:
    sets = {k: set(v["dates"]) for k, v in legs.items()}
    union = set().union(*sets.values())
    inter = set.intersection(*sets.values())
    master = sorted(inter)
    per_leg = {}
    for k in LEGS:
        missing = sorted(union - sets[k])
        extra_own_only = sorted(sets[k] - inter)
        per_leg[k] = {
            "rows": len(sets[k]),
            "missing_vs_union": missing,
            "missing_vs_union_count": len(missing),
            "own_only_vs_master_count": len(extra_own_only),
            "own_only_vs_master_first_last": ([extra_own_only[0], extra_own_only[-1]]
                                              if extra_own_only else []),
        }
    from datetime import date
    wdc = {}
    for d in master:
        y, m, dd = (int(x) for x in d.split("-"))
        wd = date(y, m, dd).isoweekday()
        wdc[wd] = wdc.get(wd, 0) + 1
    return {
        "master_calendar": master,
        "master_len": len(master),
        "master_first": master[0], "master_last": master[-1],
        "master_weekday_counts": {str(k): v for k, v in sorted(wdc.items())},
        "weekend_dates_in_master": [d for d in master
                                    if date(*map(int, d.split("-"))).isoweekday() > 5],
        "per_leg": per_leg,
        "ffill_used": False,
    }


# ------------------------------------------------------------------ folds F5

def make_folds(master: list) -> dict:
    n = len(master)
    f1 = n // 3
    f2 = n // 3
    bounds = [0, f1, f1 + f2, n]
    return {
        "schema": "folds_freeze@1",
        "law": "three chronological folds of the intersecting 5-leg master "
               "calendar, contiguous thirds by bar count, frozen BEFORE any "
               "per-config census; warmup consumed inside fold 1 per §8; "
               "force-flat at fold boundary by construction (a firing counts "
               "only if the leg's own execution bar t+1 lies in the SAME fold "
               "as its decision bar t)",
        "fold_count": 3,
        "boundaries_index": bounds,
        "folds": [
            {"fold": 1, "first": master[bounds[0]], "last": master[bounds[1] - 1],
             "master_bars": bounds[1] - bounds[0]},
            {"fold": 2, "first": master[bounds[1]], "last": master[bounds[2] - 1],
             "master_bars": bounds[2] - bounds[1]},
            {"fold": 3, "first": master[bounds[2]], "last": master[bounds[3] - 1],
             "master_bars": bounds[3] - bounds[2]},
        ],
        "master_dates_sha256": sha256_obj(master),
        "measured_before_any_census": True,
    }


def fold_of(folds: dict, master_index: int) -> int:
    b = folds["boundaries_index"]
    for f in range(3):
        if b[f] <= master_index < b[f + 1]:
            return f + 1
    raise ValueError(master_index)


# ------------------------------------------------------------ configurations

def enumerate_configs() -> list:
    """The 33 plan-frozen configurations (§5). Config IDs stable,
    lexicographic. Signs/directions as pinned in the census manifest.
    """
    cfgs = []
    for K in (10, 20, 60):
        for k in (5, 10):
            cfgs.append({"config_id": f"FSS-CLV-DIVERGENCE-K{K}-S{k}",
                         "family": "CLV-DIVERGENCE", "K": K, "slope_k": k})
    for K in (10, 20, 60):
        cfgs.append({"config_id": f"FSS-EXTREME-FADE-K{K}",
                     "family": "EXTREME-FADE", "K": K})
    for mode in ("CONFIRM", "FADE"):
        for q in (25, 50, 75):
            cfgs.append({"config_id": f"FSS-OPEN-GAP-{mode}-Q{q}",
                         "family": "OPEN-GAP", "mode": mode, "pct": q})
    for mode in ("MOM", "REV"):
        for L in (21, 63):
            cfgs.append({"config_id": f"FSS-VOL-DRIFT-{mode}-L{L}",
                         "family": "VOL-DRIFT", "mode": mode, "L": L})
    for d in (1, 2, 3, 4, 5):
        for direction in ("LONG", "SHORT"):
            cfgs.append({"config_id": f"FSS-CLOCK-COND-DOW{d}-{direction}",
                         "family": "CLOCK-COND", "dow": d, "direction": direction})
    for half in ("FIRST", "SECOND"):
        for direction in ("LONG", "SHORT"):
            cfgs.append({"config_id": f"FSS-CLOCK-COND-MONTHPOS-{half}-{direction}",
                         "family": "CLOCK-COND", "monthpos": half,
                         "direction": direction})
    assert len(cfgs) == 33, len(cfgs)
    return sorted(cfgs, key=lambda c: c["config_id"])


# ------------------------------------------------------------- state engines
# All engines are per-leg, causal, complete-window fail-closed: a state that
# cannot be formed from COMPLETE windows is NOT FIRED. No expanding or
# partial windows anywhere. Each returns a dict {master_index: direction}.

def _rolling_max(a: np.ndarray, K: int) -> np.ndarray:
    out = np.full(len(a), np.nan)
    for i in range(K - 1, len(a)):
        out[i] = a[i - K + 1:i + 1].max()
    return out


def _rolling_min(a: np.ndarray, K: int) -> np.ndarray:
    out = np.full(len(a), np.nan)
    for i in range(K - 1, len(a)):
        out[i] = a[i - K + 1:i + 1].min()
    return out


def state_clv_divergence(leg: dict, own_of_master: list, K: int, k: int,
                         warmup_master: int) -> dict:
    """Fresh K-bar close extreme + divergent 20-bar CLV pressure slope.

    CLV[i] = ((C−L)−(H−C))/(H−L) (0 when H==L). pressure20[i] = sum CLV
    over the trailing 20 bars ending at i. slope s = pressure20[i] −
    pressure20[i−k] (complete windows only). Fires SHORT on a fresh K-bar
    close HIGH with s<0 (bearish divergence); LONG on a fresh K-bar close
    LOW with s>0 (bullish divergence).
    """
    o, h, l, c = leg["open"], leg["high"], leg["low"], leg["close"]
    n = len(c)
    rng = np.maximum(h - l, 1e-300)
    clv = np.where(h == l, 0.0, ((c - l) - (h - c)) / rng)
    pres = np.full(n, np.nan)
    w20 = CLV_SLOPE_WINDOW_IS_20
    for i in range(w20 - 1, n):
        pres[i] = clv[i - w20 + 1:i + 1].sum()
    kmax_hi = _rolling_max(c, K)
    kmax_lo = _rolling_min(c, K)
    out = {}
    for m, i in enumerate(own_of_master):
        if m < warmup_master:
            continue
        j = i - k  # earlier pressure anchor (complete 20-window required there)
        if i < CLV_SLOPE_WINDOW_IS_20 - 1 or j < CLV_SLOPE_WINDOW_IS_20 - 1:
            continue  # cannot form from complete windows -> not fired
        s = pres[i] - pres[j]
        fresh_hi = c[i] >= kmax_hi[i] if not np.isnan(kmax_hi[i]) else False
        fresh_lo = c[i] <= kmax_lo[i] if not np.isnan(kmax_lo[i]) else False
        if fresh_hi and s < 0:
            out[m] = "SHORT"
        elif fresh_lo and s > 0:
            out[m] = "LONG"
    return out


def state_extreme_fade(leg: dict, own_of_master: list, K: int,
                       warmup_master: int) -> dict:
    """Fresh K-bar close extreme faded: fresh K-bar close HIGH -> SHORT,
    fresh K-bar close LOW -> LONG (causal complement of CLV-DIVERGENCE).
    """
    c = leg["close"]
    kmax_hi = _rolling_max(c, K)
    kmax_lo = _rolling_min(c, K)
    out = {}
    for m, i in enumerate(own_of_master):
        if m < warmup_master:
            continue
        if np.isnan(kmax_hi[i]):
            continue
        if c[i] >= kmax_hi[i]:
            out[m] = "SHORT"
        elif c[i] <= kmax_lo[i]:
            out[m] = "LONG"
    return out


def state_open_gap(leg: dict, own_of_master: list, mode: str, pct: int,
                   warmup_master: int) -> dict:
    """OPEN-GAP (§4 F3 exception): state formed from close(t) and open(t+1),
    knowable exactly at bar t+1's open; forced fill AT that open(t+1) is the
    ONE declared same-bar exception. gap g[i] = open[i] − close[i−1] SIGNED;
    trigger level = SIGNED quantile q_p of the trailing 252-gap window
    ending at and including g[i] (never absolute-value). Threshold pin (P0
    census; D1 owns the freeze): the percentile ITSELF selects the side —
    p < 50 is a DOWN-tail level (fires when g[i+1] <= q_p), p > 50 is an
    UP-tail level (fires when g[i+1] >= q_p), p == 50 splits BOTH sides at
    the median (fires when g[i+1] crosses the median in either direction).
    FADE: up->SHORT / down->LONG. CONFIRM: up->LONG / down->SHORT. FADE and
    CONFIRM share firing EVENTS by construction (frozen direction differs
    only); counts are therefore equal within a threshold config — the
    census counts events, direction lives in the manifest.
    Fires only if the leg's own execution bar i+1 exists (fold check done by
    the caller).
    """
    o, c = leg["open"], leg["close"]
    n = len(c)
    g = np.full(n, np.nan)
    g[1:] = o[1:] - c[:-1]
    q_level = pct / 100.0
    out = {}
    for m, i in enumerate(own_of_master):
        if m < warmup_master:
            continue
        if i + 1 >= n:
            continue
        if i - GAP_WINDOW + 1 < 1 or np.isnan(g[i - GAP_WINDOW + 1:i + 1]).any():
            continue  # incomplete gap window -> not fired
        w = g[i - GAP_WINDOW + 1:i + 1]
        q = float(np.quantile(w, q_level))
        gp = g[i + 1]
        if pct < 50:
            fired, up = gp <= q, False
        elif pct > 50:
            fired, up = gp >= q, True
        else:
            if gp > q:
                fired, up = True, True
            elif gp < q:
                fired, up = True, False
            else:
                fired, up = False, False
        if not fired:
            continue
        if mode == "FADE":
            out[m] = "SHORT" if up else "LONG"
        else:
            out[m] = "LONG" if up else "SHORT"
    return out


def state_vol_drift(leg: dict, own_of_master: list, mode: str, L: int,
                    warmup_master: int) -> dict:
    """Realized-vol tercile-conditional 1-session momentum/reversal.

    vol[i] = sample std (ddof=1) of close-to-close log returns over the
    trailing L returns ending at i. Tercile boundaries = 1/3 and 2/3
    quantiles (linear interpolation) of the trailing 252-bar window of the
    SAME estimator ending at and including i — CAUSAL, never full-sample.
    Same-bar assignment. Regime pin (from mechanism, Q-12, not tuned):
    MOM configs condition on the LOW tercile (drift persists in calm
    regimes); REV configs on the HIGH tercile (overreaction corrects in
    stressed regimes). Complete-window law: boundaries need i >= L+251
    (own index), so first possible firing is later than the §8 warmup bar
    for L>1 — the fail-closed no-partial-window law, declared.
    """
    c = leg["close"]
    n = len(c)
    lr = np.full(n, np.nan)
    lr[1:] = np.log(c[1:] / c[:-1])
    vol = np.full(n, np.nan)
    for i in range(L, n):
        vol[i] = np.std(lr[i - L + 1:i + 1], ddof=1)
    out = {}
    for m, i in enumerate(own_of_master):
        if m < warmup_master:
            continue
        if i < L + VOL_TERCILE_WINDOW - 1 or np.isnan(vol[i - VOL_TERCILE_WINDOW + 1:i + 1]).any():
            continue  # incomplete estimator window -> not fired
        w = vol[i - VOL_TERCILE_WINDOW + 1:i + 1]
        b1 = float(np.quantile(w, 1.0 / 3.0))
        b2 = float(np.quantile(w, 2.0 / 3.0))
        v = vol[i]
        low, high = v <= b1, v >= b2
        if i - L < 0:
            continue
        r = c[i] - c[i - L]
        if mode == "MOM":
            if low and r > 0:
                out[m] = "LONG"
            elif low and r < 0:
                out[m] = "SHORT"
        else:
            if high and r > 0:
                out[m] = "SHORT"
            elif high and r < 0:
                out[m] = "LONG"
    return out


def state_clock_cond(leg: dict, master: list, dow: int | None = None,
                     monthpos: str | None = None, direction: str = "LONG",
                     warmup_master: int = 60) -> dict:
    """Day-of-week / month-position conditional state, fixed direction.

    DOW: ISO weekday of the decision date. MONTHPOS: first-half = day of
    month 1..15, second-half = 16..end (decision date's calendar day).
    """
    from datetime import date
    out = {}
    for m in range(warmup_master, len(master)):
        y, mo, d = (int(x) for x in master[m].split("-"))
        dt = date(y, mo, d)
        if dow is not None:
            hit = dt.isoweekday() == dow
        else:
            first_half = d <= 15
            hit = first_half if monthpos == "FIRST" else (not first_half)
        if hit:
            out[m] = direction
    return out


def compute_state(cfg: dict, leg: dict, own_of_master: list,
                  master: list) -> dict:
    w = WARMUP_BARS[cfg["family"]]
    fam = cfg["family"]
    if fam == "CLV-DIVERGENCE":
        return state_clv_divergence(leg, own_of_master, cfg["K"], cfg["slope_k"], w)
    if fam == "EXTREME-FADE":
        return state_extreme_fade(leg, own_of_master, cfg["K"], w)
    if fam == "OPEN-GAP":
        return state_open_gap(leg, own_of_master, cfg["mode"], cfg["pct"], w)
    if fam == "VOL-DRIFT":
        return state_vol_drift(leg, own_of_master, cfg["mode"], cfg["L"], w)
    if fam == "CLOCK-COND":
        return state_clock_cond(leg, master, cfg.get("dow"), cfg.get("monthpos"),
                                cfg.get("direction", "LONG"), w)
    raise ValueError(fam)


# ------------------------------------------------------------------ census

def run_census(legs: dict, cal: dict, folds: dict, configs: list) -> dict:
    master = cal["master_calendar"]
    own_index = {k: {d: i for i, d in enumerate(v["dates"])} for k, v in legs.items()}
    next_own = {k: {v["dates"][i]: v["dates"][i + 1] for i in range(len(v["dates"]) - 1)}
                for k, v in legs.items()}
    fold_id_of_master = [fold_of(folds, m) for m in range(len(master))]
    per_cfg = {}
    for cfg in configs:
        firings_by_fold = {1: 0, 2: 0, 3: 0}
        by_leg = {}
        dow_hist = {str(d): 0 for d in (1, 2, 3, 4, 5, 6, 7)}
        from datetime import date
        for legname in LEGS:
            leg = legs[legname]
            own_map = own_index[legname]
            own_of_master = [own_map[d] for d in master]
            state = compute_state(cfg, leg, own_of_master, master)
            cnt = 0
            for m, direction in sorted(state.items()):
                f = fold_id_of_master[m]
                d_t = master[m]
                nxt = next_own[legname].get(d_t)
                if nxt is None:
                    continue  # no execution bar -> force-flat, not fired
                mi_next = _master_index(master, nxt)
                if mi_next is None:
                    continue  # execution beyond frozen sample -> force-flat
                f_next = fold_of(folds, mi_next)
                if f_next != f:
                    continue  # force-flat at fold boundary (§8)
                firings_by_fold[f] += 1
                cnt += 1
                y, mo, dd = (int(x) for x in d_t.split("-"))
                dow_hist[str(date(y, mo, dd).isoweekday())] += 1
            by_leg[legname] = cnt
        total = sum(firings_by_fold.values())
        denom = {f: 5 * (folds["folds"][f - 1]["master_bars"]) for f in (1, 2, 3)}
        rates = {str(f): round(firings_by_fold[f] / denom[f], 6) for f in (1, 2, 3)}
        shares = {}
        tot_dow = sum(dow_hist.values())
        for d in (1, 2, 3, 4, 5, 6, 7):
            shares[str(d)] = round(dow_hist[str(d)] / tot_dow, 6) if tot_dow else 0.0
        max_share = max(shares[str(d)] for d in (1, 2, 3, 4, 5))
        per_cfg[cfg["config_id"]] = {
            "family": cfg["family"],
            "fired_by_fold": {str(f): firings_by_fold[f] for f in (1, 2, 3)},
            "fired_total": total,
            "fired_by_leg": by_leg,
            "decision_leg_days_by_fold": {str(f): denom[f] for f in (1, 2, 3)},
            "fired_rate_by_fold": rates,
            "rate_form_in_[0.02,0.10]_by_fold": {
                str(f): (FIRED_RATE_FORM[0] <= rates[str(f)] <= FIRED_RATE_FORM[1])
                for f in (1, 2, 3)},
            "pooled_floor_ge30_by_fold": {
                str(f): firings_by_fold[f] >= POOLED_FLOOR_PER_FOLD
                for f in (1, 2, 3)},
            "pooled_floor_fail_closed_kill_if_any_fold_below": any(
                firings_by_fold[f] < POOLED_FLOOR_PER_FOLD for f in (1, 2, 3)),
            "dow_share_of_firings": shares,
            "max_weekday_share": round(max_share, 6),
            "r5_weekday_share_floor_recorded_only": R5_MAX_WEEKDAY_SHARE_FLOOR,
            "r2_per_state_floor_recorded_only": R2_PER_STATE_FLOOR,
        }
    return {
        "schema": "fired_census@1",
        "law": "fired census = COUNTS of state firings per configuration only "
               "(§3b). No candidate returns, PnL, PF, Sharpe, drawdown, "
               "survivors or S1 evidence computed anywhere. A state that "
               "cannot form from COMPLETE windows does not fire (fail-closed). "
               "Firing attributed to the fold of decision bar t; counted only "
               "if the leg's own execution bar t+1 exists in the SAME fold "
               "(force-flat at fold boundary). OPEN-GAP uses its declared "
               "timing exception (§4 F3): state from close(t)/open(t+1), "
               "forced fill at open(t+1), still attributed to decision bar t. "
               "FADE and CONFIRM configurations share firing events by "
               "construction (their frozen directions differ only), so their "
               "counts are equal within a threshold config.",
        "config_count": len(configs),
        "clock_cond_count": sum(1 for c in configs if c["family"] == "CLOCK-COND"),
        "per_config": per_cfg,
        "form_note": "fired-rate form [0.02, 0.10] bars/leg/day (§4 F5); the "
                     "recent-window measured value replaces the form at P2; "
                     "membership reported here is the FORM evaluation only",
        "floor_note": "pooled >= 30 fired decisions/fold (§4 F5); configs "
                      "below the floor in any fold are fail-closed kills — "
                      "recorded, never silently dropped",
    }


def _master_index(master: list, d: str):
    """Fold-localization of a (possibly non-master) execution date.

    Mid-sample non-master dates (another leg's holiday) localize to the
    fold of the first master date >= d. A date BEYOND the frozen master
    sample returns None — the execution lies outside the frozen folds and
    the firing is not counted (force-flat fail-closed).
    """
    import bisect
    i = bisect.bisect_left(master, d)
    if i >= len(master):
        return None
    return i


# ------------------------------------------------------------------- main

def build_manifest_pin(tarball_digests: dict) -> dict:
    pin = {
        "schema": "p0_manifest_pin@1",
        "cycle": "FOREX-SEARCH-V1",
        "archive_root": str(ARCHIVE_ROOT),
        "archive_root_outside_repo": True,
        "tarball_sha256_vs_SHA256SUMS": tarball_digests,
        "pairs": {},
        "ng1_copies_byte_identical": True,
        "excluded": {"XAUUSD": "EXCLUDED per plan §4 (cost authority BLOCKED, "
                               "FOREX-NG6 P0-F4)"},
        "vintage_law": "single P-13 vintage; the archive is THE authority; "
                       "divergence at F1(iii) is disclosed, never merged",
    }
    for leg in LEGS:
        archive, member, expect = PAIR_SOURCES[leg]
        p = STAGING / member
        dig = sha256_file(p)
        legd = load_leg(p)
        pin["pairs"][leg] = {
            "archive": archive,
            "member": member,
            "sha256": dig,
            "matches_plan_frozen_digest": dig == expect,
            "rows": len(legd["dates"]),
            "first": legd["dates"][0],
            "last": legd["dates"][-1],
        }
    # ng1 byte-identity check
    ng1 = {"AUDUSD": "data_raw/forex_ng1_spot/AUDUSD.json",
           "GBPUSD": "data_raw/forex_ng1_spot/GBPUSD.json",
           "NZDUSD": "data_raw/forex_ng1_spot/NZDUSD.json",
           "USDCAD": "data_raw/forex_ng1_spot/USDCAD.json"}
    idents = {}
    for leg, member in ng1.items():
        idents[leg] = sha256_file(STAGING / member) == pin["pairs"][leg]["sha256"]
    pin["ng1_copy_identity"] = idents
    pin["ng1_copies_byte_identical"] = all(idents.values())
    return pin


def write_json(path: Path, obj) -> str:
    path.write_text(json.dumps(obj, indent=1, sort_keys=True) + "\n")
    return sha256_file(path)


def main() -> int:
    P0.mkdir(parents=True, exist_ok=True)
    digests = {}
    sums = ARCHIVE_ROOT / "SHA256SUMS.txt"
    expected = {}
    for line in sums.read_text().splitlines():
        if line.strip():
            d, name = line.split()
            expected[name] = d
    for name, d in sorted(expected.items()):
        f = ARCHIVE_ROOT / name
        ok = f.exists() and sha256_file(f) == d
        digests[name] = {"expected": d, "match": ok}
    if not all(v["match"] for v in digests.values()):
        print("[p0] FATAL: tarball digest mismatch", flush=True)
        return 2

    pin = build_manifest_pin(digests)
    if not all(v["matches_plan_frozen_digest"] for v in pin["pairs"].values()):
        print("[p0] FATAL: pair digest mismatch vs plan-frozen digests", flush=True)
        write_json(P0 / "manifest_pin.json", pin)
        return 2

    legs = {k: load_leg(STAGING / PAIR_SOURCES[k][1]) for k in LEGS}
    for k, v in legs.items():
        v["source_archive"] = PAIR_SOURCES[k][0]
        v["source_member"] = PAIR_SOURCES[k][1]

    struct = {k: structural_census(v) for k, v in legs.items()}
    stamp_convention = (
        "16:00-NY stamp convention (frozen): TD serves date-only stamps "
        "(YYYY-MM-DD, no intraday component), one bar per date, strictly "
        "monotone. The cycle's frozen decision clock (§4 F3) reads the bar "
        "dated D as the completed daily session whose decision close is "
        "16:00 America/New_York on date D; state forms on completed bar t; "
        "entry at bar t+1 open, exit at bar t+1 close. The 16:00-NY "
        "assignment is the cycle's clock law, not a vendor claim; the "
        "vendor stamp is a calendar date.")
    struct_out = {
        "schema": "structural_census@1",
        "stamp_convention": stamp_convention,
        "violation_law": "OHLC micro-rounding inconsistencies are COUNTED and "
                         "disclosed, never repaired or ffilled (vintage law: "
                         "the bytes stay exactly as served); non-positive "
                         "prices, duplicate or non-date stamps abort "
                         "fail-closed",
        "per_leg": struct,
    }
    write_json(P0 / "structural_census.json", struct_out)

    cal = calendar_census(legs)
    folds = make_folds(cal["master_calendar"])
    folds_sha = write_json(P0 / "folds_freeze.json", folds)  # frozen BEFORE census
    print(f"[p0] folds frozen sha={folds_sha[:16]} "
          f"master_bars={folds['boundaries_index'][-1]}", flush=True)

    configs = enumerate_configs()
    census = run_census(legs, cal, folds, configs)
    write_json(P0 / "fired_census.json", census)

    pin_sha = write_json(P0 / "manifest_pin.json", pin)
    cal_out = {k: v for k, v in cal.items() if k != "master_calendar"}
    cal_out["master_calendar_sha256"] = sha256_obj(cal["master_calendar"])
    cal_out["schema"] = "calendar_census@1"
    cal_out["law"] = "intersecting 5-leg calendar census (F1(v)): holidays and " \
                     "missing bars counted per leg vs the union; master = " \
                     "intersection; NO ffill anywhere — nothing is filled, " \
                     "forwarded or repaired"
    cal_sha = write_json(P0 / "calendar_census.json", cal_out)

    f4 = {
        "schema": "cost_financing_manifest@1",
        "constants": {
            "cost_bps_per_fill_floor": COST_BPS_PER_FILL,
            "financing_bps_per_night": FIN_BPS_PER_NIGHT,
            "stress_tier_multiplier_primary": STRESS_MULTIPLIER,
            "operative_stress_worst_bps_per_round_trip":
                2 * COST_BPS_PER_FILL * STRESS_MULTIPLIER
                + FIN_BPS_PER_NIGHT * STRESS_MULTIPLIER,
            "label": "STATED-CONSERVATIVE",
            "v6_razor_class_hurdle_bps_named": 3.0,
        },
        "financing_derivation_verbatim_from_plan_s4_F4": (
            "every trade holds exactly one session and is charged exactly one "
            "conservative worst-night band of 1.7 bps (derivation: NG7-A4's "
            "committed illustration \"~5.1 bps over 3 nights\" for NZD-USD; "
            "5.1/3 = 1.7 — caveats DISCLOSED: a 3-night cumulative average "
            "does NOT bound the single worst night, and NZD-USD-worst is "
            "generalized to all five legs without a per-leg differential "
            "census, none being derivable from OHLC-only TD; the D1 manifest "
            "prints source bytes, arithmetic and these caveats verbatim)"),
        "charged_uniformly": "charged uniformly across legs regardless of sign, "
                             "so no leg can benefit from an assumed favourable "
                             "differential",
        "dual_books_wiring": "dual-books gate runs with the financed book = "
                             "price book + this uniform charge; sign inversion "
                             "between them fails the arm, fail-closed (§6)",
        "p0_computation": "NONE — constants wired for later phases only; no "
                          "cost, return or PnL number is computed at P0",
    }
    write_json(P0 / "cost_financing_manifest.json", f4)

    f7 = {
        "schema": "control_source_authority@1",
        "classes": {
            "NY_Fed_rates_SOFR_EFFR_BGCR_TGCR_OBFR": "RETRIEVAL_TIME_ONLY",
            "OFR_series": "RETROSPECTIVE_ONLY",
        },
        "law": "NY Fed rates and OFR series are D2 funding/liquidity CONTROLS "
               "ONLY — never an FX signal (A3 identity ruling re-inherited); "
               "no forward-fill across holiday/release gaps; no "
               "retrieval-time-only evidence claims historical PIT; a control "
               "state not knowable at decision time is RETROSPECTIVE_ONLY and "
               "may KILL but may NEVER RESCUE (§6 scoping rule)",
        "p0_action": "pulled NOTHING at P0; classes recorded as constraints "
                     "for later phases",
    }
    write_json(P0 / "control_source_authority.json", f7)

    print(f"[p0] artifacts: pin={pin_sha[:16]} cal={cal_sha[:16]} "
          f"census configs={census['config_count']}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
