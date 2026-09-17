#!/usr/bin/env python
"""CRYPTO-NG4 D2 measurement lane (plan plans/PLAN_crypto_ng4.md sections 6/7).

Role: A8-D2, lane d2-battery, cycle CRYPTO-NG4. HEAVY: runs under the
machine-wide heavy lock (research.governance.heavy_lock). Held =>
NOT_RUN_RESOURCE_CONFLICT, clean stop.

What this lane measures: STRUCTURAL NOVELTY ONLY.
  - HISTORICAL ancestry battery: pooled AND per-pair |rho| (Pearson AND
    Spearman) of the frozen BETDIS anchor/neighbour book-STATE series vs
    every shadow in the committed shadow_inventory.json (plan section 6
    A4 BINDING set + the re-pinned X1 inventory; census predicate
    ^(CRYPTO|CNG|SCNG)). Bar 0.20 immovable (R0); P-2 margins recorded.
  - Fold population census per arm per the FROZEN UTC folds: any fold
    with < 4 decisions kills that arm pre-score (NG3-A5 class).
  - VENUE controls (prospective, per pair): recorded
    NOT_RUN_COVERAGE_INSUFFICIENT fail-closed while the frozen
    60-consecutive-UTC-day floor is unmet. No PASS may exist on any
    scored pair today.

What this lane NEVER does: compute or report anchor PnL/expectancy/PF/
Sharpe/drawdown; read PROSPECTIVE-SHADOW-V1 bytes; touch the running
collectors; move any threshold.

Representation (P-12 / d1_freeze): the pair residual/z BOOK STATE on the
frozen S4 H1 panels. Anchor state series in {-1,0,+1}: z-band entry at
bar t close (|z_AB(t)| >= 2.5 anchor / >= 2.0 neighbour), entry at bar
t+1, exit at H = 24 bars or the first bar close where |z_AB| crosses 0,
whichever first; every full holding window inside a single frozen fold.
Every shadow is rendered SAME-BET over the anchor's own active bars.

Run:
  .venv/bin/python research/control/crypto_ng4_run/d2/d2_run.py

Refuses to run when research/control/crypto_ng4_run/d2/shadow_inventory.json
does not hash to SHADOW_INVENTORY_SHA256 (commit-first discipline).
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

_WORKTREE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_WORKTREE))

from research.governance.heavy_lock import (  # noqa: E402
    HeavyLockError,
    LockBusyError,
    acquire,
)

CTRL = _WORKTREE / "research" / "control" / "crypto_ng4_run"
D2_DIR = CTRL / "d2"
P0_DIR = CTRL / "p0"

INVENTORY_PATH = D2_DIR / "shadow_inventory.json"
# Committed-first shadow inventory (sha256 of the exact committed bytes).
SHADOW_INVENTORY_SHA256 = "b291d66c55a9527b442363006faa5ff94bc456a4ee540644ab34e6b7727d52a6"
VERDICT_PATH = D2_DIR / "d2_verdict.json"
MANIFEST_PATH = D2_DIR / "d2_manifest.json"

P0_MANIFEST_PATH = P0_DIR / "p0_manifest.json"
SOL_CONSTANTS_PATH = P0_DIR / "sol_rv24_constants.json"
COLLECTOR_START_MANIFEST = CTRL / "collectors" / "start_manifest.json"

PANEL_PINS = {
    "BTCUSDT": "111c1a2d6d62e26c1874bb428c10216e4926ae37ab0102ca098849ca25f5e7b1",
    "ETHUSDT": "ebd487a69404a1104d9123584c93af044a2796c338185d8466599b9f34bb440b",
    "SOLUSDT": "c4ca0b6eb719122054abec2a03fcac20d3f7794c5bf6d3c546ee6db1cb6e2107",
}
OI_PIN = "f26a61e45a0f79322140c66a1a8862b6d933e0a831d7559af459ef638fbefbd3"
STORE_ROOT = Path("/Users/hoangminhlong/my-quantitative/.runtime/v3_cads_store")

PAIRS = [("BTCUSDT", "ETHUSDT"), ("BTCUSDT", "SOLUSDT"), ("ETHUSDT", "SOLUSDT")]
PAIR_NAMES = [f"{a}-{b}" for a, b in PAIRS]
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

N_BARS = 8760
FIRST_HOUR = datetime(2025, 8, 22, 0, tzinfo=timezone.utc)
H1 = timedelta(hours=1)
BETA_WINDOW = 720          # 30 panel days, frozen (d1_freeze / A2 dossier)
Z_BAND_ANCHOR = 2.5        # d1_freeze arm CNG4-A2-P1-BETDIS-ANCHOR
Z_BAND_NEIGH = 2.0         # d1_freeze arm CNG4-A2-P1-NEIGH-Z2FREQ
HORIZON = 24               # H = 24 bars exit
FIRST_DECIDABLE_BAR = 61 * 24   # day index 61 = 2025-10-22 (d1_freeze / A2 dossier)
STALE_SHIFT = 720          # STALE-BETA: beta and z windows shifted +30 panel days
FOLDS = {
    "FOLD-1": ("2025-10-22T00:00Z", "2026-01-05T23:00Z"),
    "FOLD-2": ("2026-01-06T00:00Z", "2026-03-22T23:00Z"),
    "FOLD-3": ("2026-03-23T00:00Z", "2026-06-06T23:00Z"),
    "FOLD-4": ("2026-06-07T00:00Z", "2026-08-21T23:00Z"),
}
RV24_THRESHOLDS = {  # frozen; BTC/ETH plan section 7, SOL pinned at P0
    "BTCUSDT": {"LOW": 0.0171, "MID": 0.0299, "HIGH": 0.0542},
    "ETHUSDT": {"LOW": 0.0331, "MID": 0.0571, "HIGH": 0.1042},
    "SOLUSDT": {"LOW": 0.02878350677250594, "MID": 0.04103275430315502,
                "HIGH": 0.05800430184441088},
}
RHO_BAR = 0.20             # immovable (R0 / P-2)
MIN_PAIRS = 8              # P-12 (NG3 d2 method inherited)
NEIGH_SUBSUMPTION_BAR = 0.98   # P-20
FOLD_POP_FLOOR = 4         # NG3-A5 precedent
VENUE_FLOOR_DAYS = 60      # frozen collection contract
SHAM_SEED = 20260916       # deterministic, declared in the shadow inventory
SHAM_SHIFT = 24            # +/-24 H1 bars = +/-24h

PANEL_WINDOW_START_MS = int(FIRST_HOUR.timestamp() * 1000)
OI_EPOCH_MS = int(datetime(2025, 4, 25, 0, tzinfo=timezone.utc).timestamp() * 1000)
OI_SNAPSHOT_MS = 4 * 3_600_000


# --------------------------------------------------------------------------- #
# rho machinery (NG3 d2 method inherited verbatim; importable, network-free)
# --------------------------------------------------------------------------- #

def pearson(x, y) -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.size < 2 or x.std() == 0 or y.std() == 0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def _avg_ranks(v) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    order = np.argsort(v, kind="mergesort")
    ranks = np.empty(v.size, dtype=float)
    sv = v[order]
    i = 0
    while i < sv.size:
        j = i
        while j + 1 < sv.size and sv[j + 1] == sv[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return ranks


def spearman(x, y) -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.size < 2 or np.all(x == x[0]) or np.all(y == y[0]):
        return float("nan")
    return pearson(_avg_ranks(x), _avg_ranks(y))


def rho_row(x, y, bar: float = RHO_BAR, min_pairs: int = MIN_PAIRS) -> dict:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    n = int(x.size)
    if n < min_pairs:
        return {"n_pairs": n, "pearson": None, "spearman": None,
                "max_abs_rho": None, "margin_to_bar": None,
                "status": "UNMEASURED_LOW_N"}
    if x.std() == 0 or y.std() == 0:
        return {"n_pairs": n, "pearson": None, "spearman": None,
                "max_abs_rho": None, "margin_to_bar": None,
                "status": "UNMEASURED_ZERO_VARIANCE"}
    p, s = pearson(x, y), spearman(x, y)
    m = max(abs(p), abs(s))
    return {"n_pairs": n, "pearson": round(p, 6), "spearman": round(s, 6),
            "max_abs_rho": round(m, 6), "margin_to_bar": round(bar - m, 6),
            "status": "VETO" if m > bar else "MEASURED"}


# --------------------------------------------------------------------------- #
# frozen panel load (verified byte paths from P0)
# --------------------------------------------------------------------------- #

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_cads_object(address: str) -> Path:
    path = STORE_ROOT / "objects" / address[:2] / address
    if not path.is_file():
        raise FileNotFoundError(f"CADS object absent: {address}")
    if sha256_file(path) != address:
        raise ValueError(f"CADS integrity failure on {address}")
    return path


def load_panel(symbol: str) -> dict:
    import csv

    path = resolve_cads_object(PANEL_PINS[symbol])
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if len(rows) != N_BARS:
        raise ValueError(f"{symbol}: expected {N_BARS} rows, found {len(rows)}")
    f = lambda col: np.array([float(r[col]) for r in rows])
    return {
        "last": f("last_price"), "first": f("first_price"),
        "quote": f("quote_total"), "buy_qty": f("buy_qty"),
        "sell_qty": f("sell_qty"), "buy_count": f("buy_count"),
        "n_trades": f("n_trades"), "entry_gap": f("entry_gap_s"),
        "max_run_buy": f("max_run_buy"), "max_run_sell": f("max_run_sell"),
        "max_trade_quote": f("max_trade_quote"),
        "hours": np.array([int(r["hour_utc"][11:13]) for r in rows]),
        "days": np.array([int(datetime.strptime(r["day_utc"], "%Y-%m-%d")
                              .replace(tzinfo=timezone.utc).timestamp() // 86400)
                          for r in rows]),
    }


def bar_ts(bar_idx: int) -> datetime:
    return FIRST_HOUR + bar_idx * H1


def fold_of_bar(bar_idx: int) -> str | None:
    fmt = bar_ts(bar_idx).strftime("%Y-%m-%dT%H:%MZ")
    for name, (a, b) in FOLDS.items():
        if a <= fmt <= b:
            return name
    return None


def fold_bar_ranges() -> dict:
    out = {}
    for name, (a, b) in FOLDS.items():
        sa = datetime.strptime(a, "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)
        sb = datetime.strptime(b, "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)
        out[name] = (int((sa - FIRST_HOUR).total_seconds() // 3600),
                     int((sb - FIRST_HOUR).total_seconds() // 3600))
    return out


# --------------------------------------------------------------------------- #
# rolling primitives (all PIT: windows end at t-1 unless stated)
# --------------------------------------------------------------------------- #

def rolling_ols_slope(x: np.ndarray, y: np.ndarray, w: int, shift: int = 0) -> np.ndarray:
    """beta_end[t] = OLS slope of y on x over bars [t-w+1-shift, t-shift].

    PIT: beta_end[t] uses bars <= t only. NaN until the window fills or
    the regressor is degenerate.
    """
    T = x.size
    ok = np.isfinite(x) & np.isfinite(y)
    xc, yc = np.where(ok, x, 0.0), np.where(ok, y, 0.0)
    swx = np.concatenate(([0.0], np.cumsum(xc)))
    swy = np.concatenate(([0.0], np.cumsum(yc)))
    swxy = np.concatenate(([0.0], np.cumsum(xc * yc)))
    swxx = np.concatenate(([0.0], np.cumsum(xc * xc)))
    nv = np.concatenate(([0], np.cumsum(ok.astype(np.int64))))
    beta = np.full(T, np.nan)
    hi = np.arange(w - 1 + shift, T - shift)
    end = hi - shift                    # window END bar (as-of bar: hi)
    lo = end - w + 1                    # window START bar
    # sw[k] = sum of x[0..k-1]  =>  window [lo..end] sums are sw[end+1]-sw[lo]
    sx = swx[end + 1] - swx[lo]
    sy = swy[end + 1] - swy[lo]
    sxy = swxy[end + 1] - swxy[lo]
    sxx = swxx[end + 1] - swxx[lo]
    denom = w * sxx - sx * sx
    with np.errstate(divide="ignore", invalid="ignore"):
        b = (w * sxy - sx * sy) / denom
    full = (nv[end + 1] - nv[lo]) == w
    beta[hi] = np.where(full & (denom > 0), b, np.nan)
    return beta


def rolling_median_lag(arr: np.ndarray, w: int) -> np.ndarray:
    """out[t] = median(arr[t-w..t-1]) (lags >= 1 bar, PIT)."""
    out = np.full(arr.size, np.nan)
    if arr.size <= w:
        return out
    win = np.lib.stride_tricks.sliding_window_view(arr[:arr.size - 1], w)
    out[w:] = np.median(win, axis=1)
    return out


def rolling_ratio_level(arr: np.ndarray, w: int) -> np.ndarray:
    """arr[t] / median(arr[t-w..t-1]); lags >= 1 bar (PIT)."""
    med = rolling_median_lag(arr, w)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = arr / med
    out[~np.isfinite(med)] = np.nan
    return out


def trailing_sum(ret: np.ndarray, w: int) -> np.ndarray:
    """out[t] = sum of ret[t-w+1..t] (includes bar t's return, known at close)."""
    r = np.nan_to_num(ret, nan=0.0)
    c = np.concatenate(([0.0], np.cumsum(r)))
    out = np.full(ret.size, np.nan)
    idx = np.arange(w, ret.size)
    out[idx] = c[idx + 1] - c[idx + 1 - w]
    return out


def log_returns(last: np.ndarray) -> np.ndarray:
    r = np.log(last[1:] / last[:-1])
    return np.concatenate(([np.nan], r))


def rolling_corr(a: np.ndarray, b: np.ndarray, w: int, lag: int = 0,
                 end_shift: int = 1) -> np.ndarray:
    """Rolling Pearson corr over the w bars ending at u-end_shift.

    Pair orientation (lead-lag): lag > 0 pairs (a[s], b[s-lag]) — a leads
    b; lag < 0 pairs (a[s+lag], b[s]) — b leads a. With end_shift=1 every
    value consumed is <= the evaluation bar's prior close (PIT).
    """
    T = a.size
    out = np.full(T, np.nan)
    if lag > 0:
        bb = np.full(T, np.nan)
        bb[lag:] = b[:T - lag]
        aa = a
    elif lag < 0:
        aa = np.full(T, np.nan)
        aa[:T + lag] = a[-lag:]
        bb = b
    else:
        aa, bb = a, b
    valid = np.isfinite(aa) & np.isfinite(bb)
    af = np.where(valid, aa, 0.0)
    bf = np.where(valid, bb, 0.0)
    c1 = np.concatenate(([0.0], np.cumsum(af)))
    c2 = np.concatenate(([0.0], np.cumsum(bf)))
    c3 = np.concatenate(([0.0], np.cumsum(af * bf)))
    c4 = np.concatenate(([0.0], np.cumsum(af * af)))
    c5 = np.concatenate(([0.0], np.cumsum(bf * bf)))
    nv = np.concatenate(([0], np.cumsum(valid.astype(np.int64))))
    for u in range(w + end_shift - 1, T):
        lo, hi = u - end_shift - w + 1, u - end_shift + 1
        n = nv[hi] - nv[lo]
        if n < max(8, w // 2):
            continue
        sx = c1[hi] - c1[lo]
        sy = c2[hi] - c2[lo]
        sxy = c3[hi] - c3[lo]
        sxx = c4[hi] - c4[lo]
        syy = c5[hi] - c5[lo]
        den = np.sqrt(max(n * sxx - sx * sx, 0.0) * max(n * syy - sy * sy, 0.0))
        if den > 0:
            out[u] = (n * sxy - sx * sy) / den
    return out


def rv24_series(last: np.ndarray) -> np.ndarray:
    """rv24(t) = sqrt(sum of trailing 24 squared H1 log returns)."""
    r2 = np.nan_to_num(log_returns(last), nan=0.0) ** 2
    c = np.concatenate(([0.0], np.cumsum(r2)))
    out = np.full(last.size, np.nan)
    idx = np.arange(24, last.size)
    out[idx] = np.sqrt(c[idx + 1] - c[idx + 1 - 24])
    return out


# --------------------------------------------------------------------------- #
# BETDIS book construction (d1_freeze construction verbatim)
# --------------------------------------------------------------------------- #

def build_pair_state(panel_a: dict, panel_b: dict, band: float,
                     stale_shift: int = 0) -> dict:
    """BETDIS book-state series for one pair at one z-band.

    beta_AB(t-1): rolling OLS slope of r_legA on r_legB over the trailing
    BETA_WINDOW bars ending at t-1 (PIT-strict); e_AB(t) = r_legA(t) -
    beta_AB(t-1)*r_legB(t); z_AB(t) = e_AB(t) / (rolling BETA_WINDOW-bar
    MAD-to-sigma of e_AB ending at t-1). Entry at bar t close when
    |z_AB(t)| >= band and no open position; entry bar t+1; exit at H bars
    or the first bar close where sign(z)*z_AB crosses 0, whichever first;
    an entry is taken only if the full H-bar window fits inside one
    frozen fold (force-flat fold discipline).
    stale_shift > 0 moves the beta AND z windows back by that many bars
    (STALE-BETA causal control).
    """
    T = panel_a["last"].size
    ra, rb = log_returns(panel_a["last"]), log_returns(panel_b["last"])
    beta_end = rolling_ols_slope(rb, ra, BETA_WINDOW, shift=stale_shift)
    e = np.full(T, np.nan)
    u = np.arange(1, T)
    src = beta_end[u - 1]
    ok = np.isfinite(src) & np.isfinite(ra[u]) & np.isfinite(rb[u])
    e[u[ok]] = ra[u[ok]] - src[ok] * rb[u[ok]]
    sigma_end = rolling_mad_sigma(np.nan_to_num(e, nan=0.0), BETA_WINDOW, e)
    z = np.full(T, np.nan)
    t = np.arange(1, T)
    sv = sigma_end[t - 1] > 0
    with np.errstate(divide="ignore", invalid="ignore"):
        zval = e[t] / sigma_end[t - 1]
    z[t[sv & np.isfinite(zval)]] = zval[sv & np.isfinite(zval)]

    ranges = fold_bar_ranges()
    fold_starts = sorted((a, name) for name, (a, _b) in ranges.items())
    fold_ends = {name: b for name, (_a, b) in ranges.items()}
    state = np.zeros(T, dtype=float)
    decisions = []
    i = FIRST_DECIDABLE_BAR
    while i < T:
        if not np.isfinite(z[i]) or abs(z[i]) < band:
            i += 1
            continue
        j = i + 1
        fname = fold_of_bar(j)
        if fname is None or j + HORIZON - 1 > fold_ends[fname]:
            later = [a for a, nm in fold_starts if a > i]
            if not later:
                break
            i = later[0]
            continue
        sign = 1.0 if z[i] > 0 else -1.0
        end_needed = j + HORIZON - 1
        exit_bar = end_needed
        for uu in range(j, end_needed + 1):
            if np.isfinite(z[uu]) and sign * z[uu] <= 0:
                exit_bar = uu
                break
        state[j:exit_bar + 1] = sign
        decisions.append({
            "decision_bar": int(i), "entry_bar": int(j), "exit_bar": int(exit_bar),
            "sign": sign, "fold": fname, "z_entry": float(z[i]),
        })
        i = exit_bar + 1
    return {"z": z, "state": state, "decisions": decisions, "e": e}


def rolling_mad_sigma(e_filled: np.ndarray, w: int, e_defined: np.ndarray) -> np.ndarray:
    """sigma_end[s] = 1.4826 * MAD(e[s-w+1..s]) about the window median;
    valid only when all w residual values in the window are defined."""
    T = e_filled.size
    sigma = np.full(T, np.nan)
    if T < w:
        return sigma
    win = np.lib.stride_tricks.sliding_window_view(e_filled, w)
    med = np.median(win, axis=1)
    mad = np.median(np.abs(win - med[:, None]), axis=1)
    sigma[w - 1:] = 1.4826 * mad
    csum = np.concatenate(([0], np.cumsum(np.isfinite(e_defined).astype(np.int64))))
    s = np.arange(w - 1, T)
    bad = (csum[s + 1] - csum[s + 1 - w]) != w
    sigma[s[bad]] = np.nan
    return sigma


# --------------------------------------------------------------------------- #
# daily aggregates + NG1 shapes (pinned definitions, panel-native)
# --------------------------------------------------------------------------- #

def day_bounds(days: np.ndarray):
    bounds = np.searchsorted(days, np.unique(days))
    return np.unique(days), np.append(bounds, days.size)


def daily_series(p: dict) -> dict:
    """Per-UTC-date aggregates from one panel."""
    d = p["days"]
    uu, bounds = day_bounds(d)
    csum = lambda col: np.concatenate(([0.0], np.cumsum(p[col])))
    n_tr, bq, sq = csum("n_trades"), csum("buy_qty"), csum("sell_qty")
    bc, qt, qty = csum("buy_count"), csum("quote"), csum("buy_qty") + csum("sell_qty")
    out = {"day": [int(x) for x in uu], "n_trades": [], "quote": [],
           "buy_qty": [], "sell_qty": [], "buy_count": [], "qty": [],
           "close": [], "max_run_buy": [], "max_run_sell": [],
           "max_trade_quote": [], "ret": [], "vwap": [], "avg_ticket": []}
    prev_close = None
    tickets = []
    for k in range(uu.size):
        lo, hi = bounds[k], bounds[k + 1]
        n = n_tr[hi] - n_tr[lo]
        q = qt[hi] - qt[lo]
        vol = qty[hi] - qty[lo]
        close = p["last"][hi - 1]
        ret = np.log(close / prev_close) if prev_close else np.nan
        vwap = q / vol if vol > 0 else np.nan
        ticket = q / n if n > 0 else np.nan
        for name, v in (("n_trades", n), ("quote", q), ("buy_qty", bq[hi] - bq[lo]),
                        ("sell_qty", sq[hi] - sq[lo]), ("buy_count", bc[hi] - bc[lo]),
                        ("qty", vol), ("close", close),
                        ("max_run_buy", p["max_run_buy"][lo:hi].max()),
                        ("max_run_sell", p["max_run_sell"][lo:hi].max()),
                        ("max_trade_quote", p["max_trade_quote"][lo:hi].sum()),
                        ("ret", ret), ("vwap", vwap), ("avg_ticket", ticket)):
            out[name].append(float(v) if np.isfinite(v) else np.nan)
        tickets.append(ticket)
        prev_close = close
    return out


def daily_to_grid(days: np.ndarray, day_list, values) -> np.ndarray:
    m = dict(zip(day_list, values))
    return np.array([m.get(int(x), np.nan) for x in days], dtype=float)


def lagged_daily_median(day_list, values, w: int):
    """median of the prior w dates (lags >= 1 date, PIT)."""
    out = [np.nan] * len(values)
    for k in range(w, len(values)):
        win = [v for v in values[k - w:k] if np.isfinite(v)]
        if win:
            out[k] = float(np.median(win))
    return out


def leg_shapes(sym: str, p: dict) -> dict:
    """Per-leg shadow series (engine key suffix .[sym] added by caller)."""
    d = p["days"]
    ds = daily_series(p)
    grid = lambda name: daily_to_grid(d, ds["day"], ds[name])
    shapes = {}
    # NG1 generic + v16/v17 per-symbol shapes (definitions pinned verbatim)
    med21 = lagged_daily_median(ds["day"], ds["quote"], 21)
    shapes["generic_dvol_shock"] = grid("quote") / daily_to_grid(d, ds["day"], med21)
    shapes["generic_dvol_level_log"] = daily_to_grid(
        d, ds["day"], [np.log(v) if np.isfinite(v) and v > 0 else np.nan
                       for v in ds["quote"]])
    shapes["generic_tsmom28"] = tsmom28_grid(p, ds)
    shapes["cng4_rv24_stress_leg"] = rv24_state_grid(p, "stress")
    shapes["cng4_rv24_label_ordinal_leg"] = rv24_state_grid(p, "ordinal")
    shapes["cng4_rev24_leg"] = -trailing_sum(log_returns(p["last"]), 24)
    shapes["cng4_mom168_leg"] = trailing_sum(log_returns(p["last"]), 168)
    shapes["cng4_x3_tape_proxy_leg"] = np.sign(log_returns(p["last"])) * rolling_ratio_level(
        p["quote"], 1440)
    shapes["cng4_taker_imbalance_leg"] = (p["buy_qty"] - p["sell_qty"]) / (
        p["buy_qty"] + p["sell_qty"])
    shapes["cng4_fill_clock_cluster_leg"] = rolling_ratio_level(p["n_trades"], 720)
    shapes["v17proxy_run_imb"] = daily_to_grid(
        d, ds["day"], [(b - s) / (b + s) if (b + s) > 0 else np.nan
                       for b, s in zip(ds["buy_qty"], ds["sell_qty"])])
    shapes["v17proxy_taker_sat"] = daily_to_grid(
        d, ds["day"], [bc / n if n > 0 else np.nan
                       for bc, n in zip(ds["buy_count"], ds["n_trades"])])
    shapes["v17proxy_ret"] = grid("ret")
    med60_ticket = lagged_daily_median(ds["day"], ds["avg_ticket"], 60)
    shapes["v17proxy_avg_ticket_ratio"] = daily_to_grid(
        d, ds["day"], [t / m if np.isfinite(t) and np.isfinite(m) and m > 0 else np.nan
                       for t, m in zip(ds["avg_ticket"], med60_ticket)])
    shapes["v17proxy_amihud"] = daily_to_grid(
        d, ds["day"], [abs(r) / q * 1e9 if np.isfinite(r) and q and q > 0 else np.nan
                       for r, q in zip(ds["ret"], ds["quote"])])
    shapes["v17proxy_elite"] = grid("max_trade_quote")
    shapes["v16_close_displace_fade"] = daily_to_grid(
        d, ds["day"], [(c - v) / v if np.isfinite(v) and v > 0 else np.nan
                       for c, v in zip(ds["close"], ds["vwap"])])
    shapes["v16_runpersist"] = daily_to_grid(
        d, ds["day"], [(mb - ms) / (mb + ms) if (mb + ms) > 0 else np.nan
                       for mb, ms in zip(ds["max_run_buy"], ds["max_run_sell"])])
    shapes["v17_silres_event"] = silres_event(p)
    return shapes


def tsmom28_grid(p: dict, ds: dict) -> np.ndarray:
    closes = np.array(ds["close"], dtype=float)
    vals = [np.nan] * closes.size
    for k in range(28, closes.size):
        if np.isfinite(closes[k]) and np.isfinite(closes[k - 28]) and closes[k - 28] > 0:
            vals[k] = float(np.log(closes[k] / closes[k - 28]))
    return daily_to_grid(p["days"], ds["day"], vals)


def rv24_state_grid(p: dict, kind: str) -> np.ndarray:
    thr = RV24_THRESHOLDS[p.get("_sym", "BTCUSDT")]
    rv = rv24_series(p["last"])
    if kind == "stress":
        return np.where(np.isfinite(rv), (rv > thr["HIGH"]).astype(float), np.nan)
    return _ordinal(rv, thr)


def _ordinal(rv: np.ndarray, thr: dict) -> np.ndarray:
    out = np.full(rv.size, np.nan)
    out[np.isfinite(rv) & (rv <= thr["LOW"])] = 0.0
    out[np.isfinite(rv) & (rv > thr["LOW"]) & (rv <= thr["MID"])] = 1.0
    out[np.isfinite(rv) & (rv > thr["MID"]) & (rv <= thr["HIGH"])] = 2.0
    out[np.isfinite(rv) & (rv > thr["HIGH"])] = 3.0
    return out


def silres_event(p: dict) -> np.ndarray:
    """dir(b) * 1[entry_gap_s >= Q90(prev 720 bars) and n_trades >= 1.5*median(prev 720)].

    Declared reading: dir(b) = sign(last_price - first_price) of the bar."""
    T = p["last"].size
    w = 720
    gap_q = np.full(T, np.inf)
    tr_m = np.full(T, np.inf)
    for arr, out, fn in ((p["entry_gap"], gap_q, "q"), (p["n_trades"], tr_m, "m")):
        win = np.lib.stride_tricks.sliding_window_view(arr[:T - 1], w)
        vals = np.quantile(win, 0.90, axis=1) if fn == "q" else np.median(win, axis=1)
        out[w:] = vals
    dirn = np.sign(p["last"] - p["first"])
    hit = ((p["entry_gap"] >= gap_q) & (p["n_trades"] >= 1.5 * tr_m)).astype(float)
    return dirn * hit


# --------------------------------------------------------------------------- #
# market-state + OI + funding shapes
# --------------------------------------------------------------------------- #

def session_share_by_day(p: dict, h_lo: int, h_hi: int) -> tuple[list, list]:
    d = p["days"]
    sel = (p["hours"] >= h_lo) & (p["hours"] <= h_hi)
    tot = np.concatenate(([0.0], np.cumsum(p["n_trades"])))
    usv = np.concatenate(([0.0], np.cumsum(np.where(sel, p["n_trades"], 0.0))))
    uu, bounds = day_bounds(d)
    days, shares = [], []
    for k in range(uu.size):
        lo, hi = bounds[k], bounds[k + 1]
        tt = tot[hi] - tot[lo]
        days.append(int(uu[k]))
        shares.append((usv[hi] - usv[lo]) / tt if tt > 0 else np.nan)
    return days, shares


def attn_phase_grid(panels: dict) -> np.ndarray:
    """SOL US-session (14..21 UTC) trade-count share minus majors' share, day t-1."""
    shares = {sym: session_share_by_day(p, 14, 21) for sym, p in panels.items()}
    sol = dict(zip(*shares["SOLUSDT"]))
    btc = dict(zip(*shares["BTCUSDT"]))
    eth = dict(zip(*shares["ETHUSDT"]))
    d = panels["BTCUSDT"]["days"]
    out = np.full(d.size, np.nan)
    for t in range(d.size):
        prev = int(d[t]) - 1
        s, m1, m2 = sol.get(prev, np.nan), btc.get(prev, np.nan), eth.get(prev, np.nan)
        if np.isfinite(s) and np.isfinite(m1) and np.isfinite(m2):
            out[t] = s - 0.5 * (m1 + m2)
    return out


def ticket_breadth_grid(panels: dict) -> np.ndarray:
    """SOL avg-ticket/med60 ratio divided by majors' same ratio, day t-1."""
    d = panels["BTCUSDT"]["days"]
    ratios = {}
    for sym in SYMBOLS:
        ds = daily_series(panels[sym])
        med60 = lagged_daily_median(ds["day"], ds["avg_ticket"], 60)
        ratios[sym] = {day: (t / m if np.isfinite(t) and np.isfinite(m) and m > 0 else np.nan)
                       for day, t, m in zip(ds["day"], ds["avg_ticket"], med60)}
    out = np.full(d.size, np.nan)
    for t in range(d.size):
        prev = int(d[t]) - 1
        s = ratios["SOLUSDT"].get(prev, np.nan)
        m1 = ratios["BTCUSDT"].get(prev, np.nan)
        m2 = ratios["ETHUSDT"].get(prev, np.nan)
        if np.isfinite(s) and np.isfinite(m1) and np.isfinite(m2) and (m1 + m2) > 0:
            out[t] = s / (0.5 * (m1 + m2))
    return out


def oi_level_grid(oi_series: np.ndarray) -> np.ndarray:
    """OI level of the H4 snapshot containing the bar close."""
    out = np.full(N_BARS, np.nan)
    close_ms = PANEL_WINDOW_START_MS + (np.arange(N_BARS) + 1) * 3_600_000
    k = (close_ms - OI_EPOCH_MS) // OI_SNAPSHOT_MS
    ok = (k >= 0) & (k < oi_series.size)
    out[ok] = oi_series[k[ok]]
    return out


def oi_cascade_grid(panels: dict, oi_by_sym: dict) -> np.ndarray:
    """+1 for 24h following an H4 close whose 24h OI change <= P10 of the past
    720 H4 closes AND 24h panel return < 0 (mean across the 3 legs), else 0."""
    series = oi_by_sym["BTCUSDT"]
    n_snap = series.size
    chg = np.full(n_snap, np.nan)
    chg[6:] = series[6:] - series[:-6]
    p10 = np.full(n_snap, np.nan)
    for k in range(720, n_snap):
        win = chg[k - 720:k]
        fin = win[np.isfinite(win)]
        if fin.size:
            p10[k] = np.quantile(fin, 0.10)
    rets = {sym: log_returns(p["last"]) for sym, p in panels.items()}
    out = np.zeros(N_BARS)
    for k in range(720, n_snap):
        if not (np.isfinite(chg[k]) and np.isfinite(p10[k]) and chg[k] <= p10[k]):
            continue
        snap_ms = OI_EPOCH_MS + k * OI_SNAPSHOT_MS
        t0 = int((snap_ms - PANEL_WINDOW_START_MS) // 3_600_000) - 1
        if t0 < 24 or t0 + 24 > N_BARS:
            continue
        mean_r24 = np.mean([np.nansum(rets[sym][t0 - 23:t0 + 1]) / 24.0
                            for sym in SYMBOLS])
        if mean_r24 < 0:
            out[t0 + 1:t0 + 25] = 1.0
    return out


def funding_level_series(funding_rows: list) -> np.ndarray | None:
    """v17_fundjump_funding_level: rate of the last settlement with
    fundingTime <= bar close. Rows exist only inside the P0 sample window;
    bars outside => NaN (never imputed)."""
    if not funding_rows:
        return None
    times = np.array([int(r["fundingTime"]) for r in funding_rows])
    rates = np.array([float(r["fundingRate"]) for r in funding_rows])
    order = np.argsort(times)
    times, rates = times[order], rates[order]
    out = np.full(N_BARS, np.nan)
    close_ms = PANEL_WINDOW_START_MS + (np.arange(N_BARS) + 1) * 3_600_000
    k = np.searchsorted(times, close_ms, side="right") - 1
    ok = k >= 0
    out[ok] = rates[k[ok]]
    return out


# --------------------------------------------------------------------------- #
# shadow assembly
# --------------------------------------------------------------------------- #

def calendar_shapes(panels: dict) -> dict:
    hours = panels["BTCUSDT"]["hours"]
    weekday = (panels["BTCUSDT"]["days"] + 3) % 7  # epoch day -> Mon=0
    wkndliq = np.where((weekday >= 5) | ((weekday == 4) & (hours >= 22)), -1.0, 0.0)
    out = {
        "v17_wkndliq_flag": wkndliq,
        "generic_weekend_flag": (weekday >= 5).astype(float),
        "cng4_wkndliq_flag": wkndliq,
        "cng4_weekend_flag": (weekday >= 5).astype(float),
    }
    for k in range(7):
        out[f"generic_dow_{k}"] = (weekday == k).astype(float)
    out["generic_session_us"] = ((hours >= 13) & (hours <= 21)).astype(float)
    out["generic_session_eu"] = ((hours >= 7) & (hours <= 15)).astype(float)
    out["generic_session_asia"] = ((hours >= 0) & (hours <= 7)).astype(float)
    return out


def build_shadows(panels: dict, oi: dict, funding_levels: dict) -> tuple[dict, dict]:
    """Returns (shadows, key_to_inventory).

    shadows: engine key -> {pair_name: np.ndarray(T,)}. Per-leg shapes bind
    only on pairs containing the leg; engine keys carry a "[LEG]" suffix and
    key_to_inventory maps each engine key back to its shadow_inventory.json
    entry name (coverage is asserted against the inventory at run time).
    """
    S = {}
    key_to_inv = {}

    def add(inventory_name: str, series_by_sym: dict):
        for sym, series in series_by_sym.items():
            key = f"{inventory_name}[{sym}]"
            S[key] = {}
            for a, b in PAIRS:
                if sym in (a, b):
                    S[key][f"{a}-{b}"] = series
            key_to_inv[key] = inventory_name

    for sym in SYMBOLS:
        p = dict(panels[sym])
        p["_sym"] = sym
        shapes = leg_shapes(sym, p)
        for inv_name, series in shapes.items():
            add(inv_name, {sym: series})

    cal = calendar_shapes(panels)
    for inv_name, series in cal.items():
        key = inv_name
        S[key] = {f"{a}-{b}": series for a, b in PAIRS}
        key_to_inv[key] = inv_name

    oi_by_sym = {sym: np.asarray(oi[sym], dtype=float) for sym in SYMBOLS}
    for pair_grid, inv_name in ((oi_level_grid(oi_by_sym["BTCUSDT"]), "v17_oi_level"),
                                (oi_cascade_grid(panels, oi_by_sym), "v17_oicascade_event"),
                                (attn_phase_grid(panels), "v17_attn_phase"),
                                (ticket_breadth_grid(panels), "v17_ticket_breadth")):
        S[inv_name] = {f"{a}-{b}": pair_grid for a, b in PAIRS}
        key_to_inv[inv_name] = inv_name

    for sym in SYMBOLS:
        if funding_levels.get(sym) is not None:
            add("v17_fundjump_funding_level", {sym: funding_levels[sym]})

    # pair-level shapes
    for a, b in PAIRS:
        name = f"{a}-{b}"
        ra, rb = log_returns(panels[a]["last"]), log_returns(panels[b]["last"])
        for k in (24, 72):
            S.setdefault(f"cng4_corr_decay_{k}", {})[name] = rolling_corr(ra, rb, k)
            key_to_inv.setdefault(f"cng4_corr_decay_{k}", f"cng4_corr_decay_{k}")
        for k, lag in (("m2", -2), ("m1", -1), ("p1", 1), ("p2", 2)):
            S.setdefault(f"cng4_lead_lag_{k}", {})[name] = rolling_corr(
                ra, rb, 72, lag=lag)
            key_to_inv.setdefault(f"cng4_lead_lag_{k}", f"cng4_lead_lag_{k}")
        spread = panels[a]["last"] / panels[b]["last"]
        lret = np.log(spread[1:] / spread[:-1])
        lret = np.concatenate(([np.nan], lret))
        trend = np.sign(trailing_sum(lret, 48))
        S.setdefault("cng4_pair_spread_trend_lag1", {})[name] = trend
        key_to_inv.setdefault("cng4_pair_spread_trend_lag1",
                              "cng4_pair_spread_trend_lag1")
    return S, key_to_inv


def pair_residual_shock(books: dict) -> dict:
    """cng4_dvol_shock_pair_residual = |e_AB(t)| / median(|e_AB(u)|, u in
    [t-504, t-1]) per pair (504 = 21 days x 24 H1 bars; lags >= 1 bar)."""
    out = {}
    for pname, book in books.items():
        e = book["e"]
        med = rolling_median_lag(np.abs(np.nan_to_num(e, nan=0.0)), 504)
        with np.errstate(divide="ignore", invalid="ignore"):
            v = np.abs(e) / med
        v[~np.isfinite(med)] = np.nan
        out[pname] = v
    return out


def sham_book(anchor_books: dict) -> dict:
    """Randomized-event-time sham: anchor windows translated by a seeded
    +/-24-bar offset; one-position book semantics; windows crossing the
    panel edge or a fold boundary are dropped (drop counted)."""
    rng = np.random.default_rng(SHAM_SEED)
    state, meta = {}, {}
    for pname, book in anchor_books.items():
        st = np.zeros(N_BARS)
        kept, dropped, last_exit = 0, 0, -1
        for dec in book["decisions"]:
            delta = int(rng.choice([-SHAM_SHIFT, SHAM_SHIFT]))
            j, x = dec["entry_bar"] + delta, dec["exit_bar"] + delta
            if (j < 1 or x >= N_BARS or fold_of_bar(j) != dec["fold"]
                    or fold_of_bar(x) != dec["fold"] or j <= last_exit):
                dropped += 1
                continue
            st[j:x + 1] = dec["sign"]
            last_exit = x
            kept += 1
        state[pname] = st
        meta[pname] = {"kept": kept, "dropped": dropped}
    return {"state_by_pair": state, "meta": meta}


# --------------------------------------------------------------------------- #
# fold population census (pure; NG3-A5 class kill rule)
# --------------------------------------------------------------------------- #

def pair_fold_report(decisions: list) -> dict:
    """Decision counts per frozen fold for one pair-book + the kill rule:
    any fold with < FOLD_POP_FLOOR decisions kills the arm pre-score."""
    counts = {f: 0 for f in FOLDS}
    wknd = {f: 0 for f in FOLDS}
    wkday = {f: 0 for f in FOLDS}
    for dec in decisions:
        counts[dec["fold"]] += 1
        if bar_ts(dec["entry_bar"]).weekday() >= 5:
            wknd[dec["fold"]] += 1
        else:
            wkday[dec["fold"]] += 1
    under = sorted(f for f, c in counts.items() if c < FOLD_POP_FLOOR)
    return {
        "decisions_per_fold": counts,
        "weekend_entry_decisions_per_fold": wknd,
        "weekday_entry_decisions_per_fold": wkday,
        "total_decisions": sum(counts.values()),
        "folds_below_floor": under,
        "pre_score_dead": bool(under),
    }


# --------------------------------------------------------------------------- #
# venue controls (fail-closed)
# --------------------------------------------------------------------------- #

def venue_status() -> dict:
    started = None
    if COLLECTOR_START_MANIFEST.is_file():
        mf = json.loads(COLLECTOR_START_MANIFEST.read_text())
        starts = [v.get("started_process_utc") for v in mf.get("venues", {}).values()
                  if v.get("started_process_utc")]
        started = min(starts) if starts else mf.get("started_manifest_utc")
    coverage_days = 0.0  # no complete UTC day of collection has elapsed
    per_pair = {}
    for pname in PAIR_NAMES:
        per_pair[pname] = {
            "controls": ["venue_divergence", "basis", "spread_proxy",
                         "liquidation_volatility", "weekend_liquidity",
                         "funding_state"],
            "status": "NOT_RUN_COVERAGE_INSUFFICIENT",
            "fail_closed": True,
        }
    return {
        "schema": "crypto_ng4_run/d2/venue_status@1",
        "collectors_first_process_utc": started,
        "complete_coverage_utc_days": coverage_days,
        "frozen_floor_consecutive_utc_days": VENUE_FLOOR_DAYS,
        "floor_met": coverage_days >= VENUE_FLOOR_DAYS,
        "per_pair": per_pair,
        "rule": ("prospective floor unmet => every venue control on every scored "
                 "pair is NOT_RUN_COVERAGE_INSUFFICIENT fail-closed; no PASS may "
                 "exist on any scored pair today"),
    }


# --------------------------------------------------------------------------- #
# measurement core (pure; importable by tests without the heavy lock)
# --------------------------------------------------------------------------- #

def measure_core(panels: dict, oi: dict, funding_levels: dict,
                 inventory: dict) -> dict:
    books = {}
    for a, b in PAIRS:
        pname = f"{a}-{b}"
        books[pname] = {
            "anchor": build_pair_state(panels[a], panels[b], Z_BAND_ANCHOR),
            "neighbour": build_pair_state(panels[a], panels[b], Z_BAND_NEIGH),
            "stale": build_pair_state(panels[a], panels[b], Z_BAND_ANCHOR,
                                      stale_shift=STALE_SHIFT),
        }

    shadows, key_to_inv = build_shadows(panels, oi, funding_levels)
    shadows["cng4_dvol_shock_pair_residual"] = pair_residual_shock(
        {p: b["anchor"] for p, b in books.items()})
    key_to_inv["cng4_dvol_shock_pair_residual"] = "cng4_dvol_shock_pair_residual"

    # inventory coverage: every mandatory inventory shape name must be carried
    inv_names = set()
    for group in inventory.get("groups", []):
        for e in group.get("shapes", []):
            inv_names.add(e["name"])
    carried = set(key_to_inv.values())
    missing = sorted(inv_names - carried - {"cng4_sham_randomized_event_time",
                                            "cng4_stale_beta_control",
                                            "cng4_neighbour_z2_freq"})
    sham = sham_book({p: b["anchor"] for p, b in books.items()})

    tables = {}
    for arm in ("anchor", "neighbour", "stale"):
        table = {}
        for key in sorted(shadows):
            per_pair_rows, xs, ys = {}, [], []
            for pname in PAIR_NAMES:
                if pname not in shadows[key]:
                    continue
                mask = books[pname][arm]["state"] != 0
                x = books[pname][arm]["state"][mask]
                y = np.asarray(shadows[key][pname], dtype=float)[mask]
                row = rho_row(x, y)
                per_pair_rows[pname] = row
                if row["status"] in ("MEASURED", "VETO"):
                    xs.append(x)
                    ys.append(y)
            pooled = (rho_row(np.concatenate(xs), np.concatenate(ys))
                      if xs else {"n_pairs": 0, "pearson": None, "spearman": None,
                                  "max_abs_rho": None, "margin_to_bar": None,
                                  "status": "UNMEASURED_NO_SUPPORT"})
            table[key] = {"inventory_name": key_to_inv[key],
                          "pooled": pooled, "per_pair": per_pair_rows}
        tables[arm] = table

    # SHAM rendered same-bet over the anchor's active bars
    xs, ys = [], []
    sham_rows = {}
    for pname in books:
        mask = books[pname]["anchor"]["state"] != 0
        x = books[pname]["anchor"]["state"][mask]
        y = sham["state_by_pair"][pname][mask]
        sham_rows[pname] = rho_row(x, y)
        xs.append(x)
        ys.append(y)
    sham_table = {"pooled": rho_row(np.concatenate(xs), np.concatenate(ys)),
                  "per_pair": sham_rows, "windows": sham["meta"]}

    # neighbour-vs-anchor self-subsumption (P-20), pooled state-series rho
    xs = [books[p]["anchor"]["state"] for p in books]
    ys = [books[p]["neighbour"]["state"] for p in books]
    subsumption = rho_row(np.concatenate(xs), np.concatenate(ys),
                          bar=NEIGH_SUBSUMPTION_BAR)

    # fold population census
    fold_pops = {}
    for arm in ("anchor", "neighbour", "stale"):
        fold_pops[arm] = {pname: pair_fold_report(books[pname][arm]["decisions"])
                          for pname in books}

    def table_vetoes(table):
        out = []
        for key, rows in table.items():
            if rows["pooled"]["status"] == "VETO":
                out.append({"shadow": key, "inventory_name": rows["inventory_name"],
                            "scope": "pooled",
                            "max_abs_rho": rows["pooled"]["max_abs_rho"],
                            "margin_to_bar": rows["pooled"]["margin_to_bar"]})
            for pname, row in rows["per_pair"].items():
                if row.get("status") == "VETO":
                    out.append({"shadow": key, "inventory_name": rows["inventory_name"],
                                "scope": pname, "max_abs_rho": row["max_abs_rho"],
                                "margin_to_bar": row["margin_to_bar"]})
        return out

    anchor_vetoes = table_vetoes(tables["anchor"])
    unmeasured = []
    for key, rows in tables["anchor"].items():
        if str(rows["pooled"]["status"]).startswith("UNMEASURED"):
            unmeasured.append({"shadow": key, "scope": "pooled",
                               "status": rows["pooled"]["status"]})
        for pname, row in rows["per_pair"].items():
            if str(row.get("status", "")).startswith("UNMEASURED"):
                unmeasured.append({"shadow": key, "scope": pname,
                                   "status": row["status"]})

    anchor_pop_dead = any(v["pre_score_dead"] for v in fold_pops["anchor"].values())
    neigh_pop_dead = any(v["pre_score_dead"] for v in fold_pops["neighbour"].values())
    neigh_subsumption_dead = bool(
        subsumption.get("max_abs_rho") is not None
        and subsumption["max_abs_rho"] > NEIGH_SUBSUMPTION_BAR)

    if anchor_vetoes:
        cycle_state, verdict = "ANCESTRY_VETO_CLOSE", "ANCESTRY_VETO"
    else:
        cycle_state = "WAITING_PROSPECTIVE_COVERAGE"
        verdict = "WAITING_PROSPECTIVE_COVERAGE"

    return {
        "schema": "crypto_ng4_run/d2/verdict@1",
        "cycle_id": "CRYPTO-NG4",
        "lane": "d2-battery",
        "role": "A8-D2",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "worktree": str(_WORKTREE),
        "branch": "orca/crypto-ng4-integration",
        "base_head": "950f3bfdc9a5b45993d09107b99c744d2c6ac726",
        "pnl_ban": ("no anchor returns, PnL, expectancy, PF, Sharpe or drawdown "
                    "computed or reported anywhere; only book-STATE series rho, "
                    "fold populations, and venue coverage status"),
        "inventory": {
            "path": str(INVENTORY_PATH),
            "sha256": SHADOW_INVENTORY_SHA256,
            "verified": True,
            "census_predicate": "^(CRYPTO|CNG|SCNG)",
            "shapes_carried": len(key_to_inv),
            "shapes_missing": missing,
        },
        "method": {
            "rho_bar": RHO_BAR,
            "min_pairs": MIN_PAIRS,
            "fold_population_floor": FOLD_POP_FLOOR,
            "neighbour_subsumption_bar_P20": NEIGH_SUBSUMPTION_BAR,
            "representation": ("P-12 / d1_freeze: anchor book-STATE series {-1,0,+1} "
                               "on the frozen S4 H1 panels; shadows rendered same-bet "
                               "over the anchor's active bars; pooled symbol-major "
                               "chronological; Pearson + Spearman"),
            "shadow_implementation_notes": [
                "per-leg engine keys carry a [LEG] suffix; inventory_name maps back to shadow_inventory.json",
                "daily shapes: per-UTC-date panel aggregates applied to every H1 bar of the date",
                "v17_silres_event dir(b) = sign(last_price - first_price) of the bar (declared reading)",
                "v17_oi_level / v17_oicascade_event: pinned CADS OI H4 series anchored 2025-04-25T00Z, snapshot = floor((bar_close - epoch)/4h)",
                "v17_fundjump_funding_level: P0 funding-sample window only; bars outside UNMEASURED (never imputed); SOL excluded per family spec",
                "rolling windows end at t-1 (PIT, lags >= 1 bar) wherever the formula requires; rv24/rev24/mom168/tsmom28 include bar t's own return per their pinned definitions",
                "SHAM seed 20260916, +/-24-bar shift, one-position book semantics, drops counted",
            ],
        },
        "books": {
            pname: {arm: {"n_decisions": len(b["decisions"]),
                          "first_decision_bar": (b["decisions"][0]["decision_bar"]
                                                 if b["decisions"] else None),
                          "active_bars": int((b["state"] != 0).sum())}
                    for arm, b in arms.items()}
            for pname, arms in books.items()},
        "rho_tables": {
            "CNG4-A2-P1-BETDIS-ANCHOR": tables["anchor"],
            "CNG4-A2-P1-NEIGH-Z2FREQ": tables["neighbour"],
            "STALE-BETA-control": tables["stale"],
        },
        "sham_table": sham_table,
        "neighbour_self_subsumption_P20": subsumption,
        "r0_ancestry_vetoes_fired": anchor_vetoes,
        "unmeasured_rows_anchor": unmeasured,
        "fold_populations": fold_pops,
        "fold_population_rule": (
            f"any fold < {FOLD_POP_FLOOR} decisions kills the arm pre-score "
            "(NG3-A5 class)"),
        "arm_pre_score_status": {
            "CNG4-A2-P1-BETDIS-ANCHOR":
                "PRE_SCORE_DEAD" if anchor_pop_dead else "POPULATED",
            "CNG4-A2-P1-NEIGH-Z2FREQ": (
                "PRE_SCORE_DEAD" if neigh_pop_dead else
                "SUBSUMPTION_DEAD" if neigh_subsumption_dead else "POPULATED"),
        },
        "venue_controls": venue_status(),
        "cycle_state": cycle_state,
        "verdict": verdict,
        "verdict_note": (
            ("R0 ancestry veto fired: " + "; ".join(
                f"{v['shadow']}@{v['scope']}={v['max_abs_rho']}"
                for v in anchor_vetoes)
             + " -> ancestry-veto close path (plan §6 R0)."
             if anchor_vetoes else
             "Historical ancestry battery survived the immovable 0.20 bar; venue "
             "controls are NOT_RUN_COVERAGE_INSUFFICIENT (collectors live "
             "2026-09-16T22:29Z, frozen floor 60 consecutive UTC days) -> the "
             "cycle parks at WAITING_PROSPECTIVE_COVERAGE. Never PASS, never "
             "scored.")),
    }


# --------------------------------------------------------------------------- #
# entrypoint (heavy lock + commit-first hash gate)
# --------------------------------------------------------------------------- #

def run_main() -> int:
    if not INVENTORY_PATH.is_file():
        print("REFUSED: shadow_inventory.json absent", file=sys.stderr)
        return 2
    actual = sha256_file(INVENTORY_PATH)
    if actual != SHADOW_INVENTORY_SHA256:
        print(f"REFUSED: shadow_inventory.json hash mismatch: {actual} != "
              f"pinned {SHADOW_INVENTORY_SHA256}", file=sys.stderr)
        return 2

    try:
        handle = acquire(
            cycle_id="CRYPTO-NG4",
            role="D2_ANCESTRY_HEAVY",
            worktree=str(_WORKTREE),
            command=[sys.executable, str(Path(__file__).resolve())],
            expected_artifacts=[str(VERDICT_PATH), str(MANIFEST_PATH)],
        )
    except LockBusyError as exc:
        print(f"NOT_RUN_RESOURCE_CONFLICT: {exc}", file=sys.stderr)
        return 3
    except HeavyLockError as exc:
        print(f"NOT_RUN_CONTROL_STATE_DRIFT: {exc}", file=sys.stderr)
        return 4

    try:
        p0m = json.loads(P0_MANIFEST_PATH.read_text())
        if p0m.get("f3_census", {}).get("n_pairs") != 3:
            raise ValueError("P0 manifest census is not 3 pairs")
        sol_c = json.loads(SOL_CONSTANTS_PATH.read_text())
        if abs(sol_c["thresholds"]["HIGH"] - RV24_THRESHOLDS["SOLUSDT"]["HIGH"]) > 1e-15:
            raise ValueError("SOL RV24 constants drift vs the P0 pin")

        panels = {sym: load_panel(sym) for sym in SYMBOLS}
        oi = json.loads(resolve_cads_object(OI_PIN).read_text())
        funding_levels = {}
        for sym in SYMBOLS:
            fpath = P0_DIR / "funding" / f"{sym}_funding_sample.json"
            funding_levels[sym] = (funding_level_series(json.loads(fpath.read_text()))
                                   if fpath.is_file() else None)
        inventory = json.loads(INVENTORY_PATH.read_text())
        result = measure_core(panels, oi, funding_levels, inventory)
    except Exception as exc:
        handle.release(status="FAILED", note=f"{type(exc).__name__}: {exc}")
        raise

    handle.release(status="FINISHED")
    D2_DIR.mkdir(parents=True, exist_ok=True)
    VERDICT_PATH.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n",
                            encoding="utf-8")
    print("cycle_state:", result["cycle_state"])
    print("verdict:", result["verdict"])
    print("r0 vetoes:", len(result["r0_ancestry_vetoes_fired"]))
    return 0


if __name__ == "__main__":
    sys.exit(run_main())
