"""STOCKS-SEARCH-V1 P0 library (plans/PLAN_stocks_search_v1.md §4 F1–F9, §3b, §5).

P0 is source engineering + census ONLY: this module computes COUNTS of state
firings per frozen configuration per fold.  It contains NO candidate return,
PnL, PF, Sharpe, drawdown, survivor or S1 evidence path anywhere — the only
array mathematics is on states (booleans), dollar-volume medians and vol
estimators, never on forward returns.

D2 IS SKIPPED THIS CYCLE by owner amendment §3b: no R0/ancestry rho
machinery exists in this module (NOT_RUN, never an inferred PASS).

Frozen conventions (declared ex ante, never tuned):
- P-12 representation: the EODHD adjusted (total-return) series is THE
  single representation.  Per-session factor f_t = adjusted_close_t /
  close_t reconstructs adjusted open/high/low; all states and any later
  returns live on the SAME adjusted series.
- Warmup law (NG6 A4 re-inherited): 252 served sessions; the first
  eligible decision of ANY configuration is no earlier than the 253rd
  served session of its name (0-based index >= 252).  Where a
  construction needs a longer history the construction need wins; the
  extra warmup attrition is censused (F4).
- Zero-range law (§5): a bar with high == low makes RANGE (EVENT-UNWIND
  component 3) and CLV undefined — the state is NOT FIRED on that bar
  (fail-closed, never imputed); degenerate bars are counted.
- Bookability floors (F4, applied as declared at fired decisions):
  adjusted close >= $1.00 AND trailing 60-session median dollar volume
  >= $2M (dvol = adj_close * volume).
- ADV bands (F6): trailing 252-session median dvol at the fired decision
  >= 50M -> A, >= 10M -> B, >= 2M -> C, below -> SUBFLOOR; non-finite
  median -> UNRESOLVED and fails closed (never a silent default band).
  Schedule BAND_BPS = {A:10, B:15, C:25} bps/fill; STRESS TIER 2.0
  PRIMARY; worst-case ceiling 25 bps x 2 fills x 2.0 = 100 bps round
  trip.  No cost is COMPUTED at P0 beyond band assignment.
- Clock (F5): ONE frozen daily decision clock — decision at t close,
  fills at t+1 open and t+1+H open; bar-readable close+1 availability
  (V7 law).  Sessions are ISO dates (timezone-naive); the exchange
  calendar is America/New_York; DST shifts never duplicate or drop a
  session date (fixture-tested).
- Fold freeze (F8): three chronological folds frozen BEFORE any
  per-config census.  Window 2015-01-02..2026-09-16 (NG6-re-inherited,
  deterministic, outcome-blind); boundaries = exact calendar thirds of
  the window computed on dates, INDEPENDENT of any event or price data.
  F1 = [start, B1], F2 = (B1, B2], F3 = (B2, end].  Regime law: the
  window contains the 2020-03 deleveraging (F2 region); 2008Q4–2009
  predates the window so the never-share rule is moot (NG6 regime_law).
- Population floor (F8): >= 30 bookable fired decisions per fold,
  evaluated and REPORTED per configuration-fold; a violation is a
  fail-closed kill record, never a silent drop.
- H (hold) affects only the execution legs (clock), not the firing
  state; fired counts are identical across H within a state.  The H
  variants remain distinct configurations per the frozen §5 grid.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import date, timedelta

import numpy as np

# ------------------------------------------------------------- frozen laws

CYCLE_ID = "STOCKS-SEARCH-V1"
TASK_ID = "ssearch-p0"
PLAN = "plans/PLAN_stocks_search_v1.md"

WINDOW_START = "2015-01-02"     # first XNYS regular session of 2015
WINDOW_END = "2026-09-16"       # last completed session before the P0 date
WARMUP_SESSIONS = 252           # first eligible decision = 253rd served session
DVOL_WINDOW = 60
DVOL_MULT = 1.5
RANGE_MIN = 0.5
FLOOR_PRICE = 1.00
FLOOR_DVOL = 2_000_000.0
FOLD_EVENT_FLOOR = 30           # Q-6 recent-window floor, fail-closed
BANDS_DEF = {"A": 50e6, "B": 10e6, "C": 2e6}
BAND_BPS = {"A": 10, "B": 15, "C": 25}
STRESS_TIER = 2.0
WORST_CASE_BPS_ROUNDTRIP = BAND_BPS["C"] * 2 * STRESS_TIER  # 100
BAND_KEYS = ("A", "B", "C", "SUBFLOOR", "UNRESOLVED")
GRID_CAP = 120
PERCENTILE_METHOD = "linear"    # pinned interpolation method (§5)
CLV_WINDOW = 20

FAMILIES = (
    "EVENT-UNWIND", "GAP", "52W-HIGH", "CLV-RANGE", "DVOL-SHOCK", "VOL-REGIME",
)
FAMILY_COUNTS = {
    "EVENT-UNWIND": 9,   # K {21,63,252} x H {5,10,20}
    "GAP": 12,           # pctl {25,50,75} x dir {fade,confirm} x H {1,5}
    "52W-HIGH": 6,       # band {2,5,10}% x H {5,20}
    "CLV-RANGE": 4,      # k {5,10} x H {5,10}
    "DVOL-SHOCK": 8,     # ratio {1.5,3.0} x dir {fade,confirm} x H {1,5}
    "VOL-REGIME": 8,     # L {21,63} x dir {low,high} x H {5,20}
}

FOLD_FLOOR_PASS_BASIS = "bookable_fired"   # NG6 Q-6 precedent


# --------------------------------------------------------- config enumeration

def enumerate_configs() -> list[dict]:
    """The 47 frozen §5 configurations (P0 census target list).

    config ID = SSS-<FAMILY>-<PARAMKEY>, stable, lexicographic.
    warmup_need = 0-based first eligible decision index for the
    construction (>= WARMUP_SESSIONS by the warmup law).
    """
    configs: list[dict] = []
    # family 1: EVENT-UNWIND — K x H (all four components ANDed)
    for K in (21, 63, 252):
        for H in (5, 10, 20):
            configs.append({
                "config_id": f"SSS-EVENT-UNWIND-K{K}-H{H}",
                "family": "EVENT-UNWIND",
                "params": {"K": K, "H": H},
                "warmup_need": max(WARMUP_SESSIONS, K),
                "state": ("BREAK adj_low_t < min(adj_low_{t-K..t-1}) AND "
                          "RECLAIM adj_close_t > that prior low AND "
                          "RANGE (close-low)/(high-low) >= 0.5 (zero-range "
                          "law: high==low NOT FIRED) AND PARTICIPATION "
                          "dvol_t >= 1.5x trailing 60-session median dvol"),
            })
    # family 2: GAP — threshold percentile x direction x H
    for p in (25, 50, 75):
        for d in ("fade", "confirm"):
            for H in (1, 5):
                configs.append({
                    "config_id": f"SSS-GAP-P{p}-{d.upper()}-H{H}",
                    "family": "GAP",
                    "params": {"pctl": p, "direction": d, "H": H},
                    "warmup_need": WARMUP_SESSIONS,
                    "state": (f"gap_t = open_t/close_{{t-1}} - 1 on the "
                              f"adjusted series; threshold = {p}th percentile "
                              f"(linear) of the trailing 252-session gap "
                              f"history ending at and including t; "
                              f"fade FIRED iff gap_t <= threshold; confirm "
                              f"FIRED iff gap_t >= threshold (long-only)"),
                })
    # family 3: 52W-HIGH — band x H
    for band in (2, 5, 10):
        for H in (5, 20):
            configs.append({
                "config_id": f"SSS-52W-HIGH-B{band}-H{H}",
                "family": "52W-HIGH",
                "params": {"band_pct": band, "H": H},
                "warmup_need": WARMUP_SESSIONS,
                "state": ("high_t = rolling 252-session max of adjusted "
                          "close ending at and including t; proximity_t = "
                          "(high_t - close_t)/high_t; FIRED iff proximity_t "
                          "<= band/100 (long inside the band, flat outside; "
                          "sign frozen from construction)"),
            })
    # family 4: CLV-RANGE — k x H
    for k in (5, 10):
        for H in (5, 10):
            configs.append({
                "config_id": f"SSS-CLV-RANGE-K{k}-H{H}",
                "family": "CLV-RANGE",
                "params": {"k": k, "H": H},
                "warmup_need": max(WARMUP_SESSIONS, CLV_WINDOW - 1 + k),
                "state": ("CLV_t = ((C-L)-(H-C))/(H-L); zero-range law: "
                          "high==low bar undefined and NOT FIRED; P_t = sum "
                          "of CLV over the trailing 20 completed bars "
                          "(undefined if ANY bar in the window is "
                          "degenerate — fail-closed); slope = P_t - "
                          "P_{t-k}; FIRED iff slope > 0 (strict; long "
                          "accumulation, sign frozen from construction)"),
            })
    # family 5: DVOL-SHOCK — ratio x direction x H
    for ratio in ("1.5x", "3.0x"):
        r = float(ratio.rstrip("x"))
        for d in ("fade", "confirm"):
            for H in (1, 5):
                configs.append({
                    "config_id": f"SSS-DVOL-SHOCK-R{ratio}-{d.upper()}-H{H}",
                    "family": "DVOL-SHOCK",
                    "params": {"ratio": r, "direction": d, "H": H},
                    "warmup_need": WARMUP_SESSIONS,
                    "state": (f"ratio_t = dvol_t / median(dvol over trailing "
                              f"60 sessions ending at t-1); ret_t = "
                              f"close_t/close_{{t-1}} - 1 on the adjusted "
                              f"series; shock present iff ratio_t >= {r}; "
                              f"confirm FIRED iff shock AND ret_t > 0; fade "
                              f"FIRED iff shock AND ret_t < 0 (ret_t == 0 "
                              f"NOT FIRED, fail-closed neutral)"),
                })
    # family 6: VOL-REGIME — L x direction x H
    for L in (21, 63):
        for d in ("low", "high"):
            for H in (5, 20):
                configs.append({
                    "config_id": f"SSS-VOL-REGIME-L{L}-{d.upper()}-H{H}",
                    "family": "VOL-REGIME",
                    "params": {"L": L, "direction": d, "H": H},
                    "warmup_need": max(WARMUP_SESSIONS, WARMUP_SESSIONS - 1 + L),
                    "state": (f"sigma_j = close-to-close log-return std "
                              f"(ddof=1) over the trailing {L} returns ending "
                              f"at and including j; boundaries = 1/3 and 2/3 "
                              f"quantiles (linear) of sigma over the trailing "
                              f"252-session window ending at and including t, "
                              f"refreshed daily, same-bar assignment — NEVER "
                              f"full-sample; long-LOW FIRED iff sigma_t <= "
                              f"q1; long-HIGH FIRED iff sigma_t >= q2 "
                              f"(middle tercile flat)"),
                })
    configs.sort(key=lambda c: c["config_id"])
    return configs


def assert_grid_law(configs: list[dict] | None = None) -> dict:
    """§5 grid-cap law: 47 configurations, <= 120, per-family counts."""
    configs = enumerate_configs() if configs is None else configs
    ids = [c["config_id"] for c in configs]
    counts: dict[str, int] = {}
    for c in configs:
        counts[c["family"]] = counts.get(c["family"], 0) + 1
    assert len(ids) == len(set(ids)), "config IDs not unique"
    assert ids == sorted(ids), "config IDs not lexicographic"
    assert len(configs) <= GRID_CAP, "grid cap violated"
    assert counts == FAMILY_COUNTS, f"family counts {counts} != frozen {FAMILY_COUNTS}"
    assert all(c["config_id"].startswith("SSS-") for c in configs)
    return {"n_configs": len(configs), "family_counts": counts, "cap": GRID_CAP}


# ------------------------------------------------------------------ states

def _dvol(adj_close: np.ndarray, volume: np.ndarray) -> np.ndarray:
    return adj_close * volume


def _rolling_median(a: np.ndarray, window: int) -> np.ndarray:
    """out[i] = median(a[i-window:i]) (window sessions ENDING at i-1);
    out[i] = NaN when i < window.

    r2: batched over a sliding view — np.median(axis=1) applies the identical
    per-row algorithm, bit-equal to the r1 per-i loop (equivalence-gated)."""
    out = np.full(a.shape, np.nan)
    if a.shape[0] >= window:
        from numpy.lib.stride_tricks import sliding_window_view
        sw = sliding_window_view(a, window)          # sw[m] = a[m:m+window]
        out[window - 1:] = np.median(sw, axis=1)     # out[i-1] = median(a[i-window:i])
    return out


def _rolling_max(a: np.ndarray, window: int) -> np.ndarray:
    """out[i] = max(a[i-window+1:i+1]) (window sessions ending at AND
    including i); out[i] = NaN when i < window-1."""
    out = np.full(a.shape, np.nan)
    if a.shape[0] >= window:
        from numpy.lib.stride_tricks import sliding_window_view
        sw = sliding_window_view(a, window)
        out[window - 1:] = sw.max(axis=1)
    return out


def census_event_unwind(adj_open, adj_high, adj_low, adj_close, volume,
                        K: int, first_i: int | None = None,
                        med60: np.ndarray | None = None):
    """Fired iff BREAK AND RECLAIM AND RANGE AND PARTICIPATION (§5 family 1).

    Zero-range law: high==low -> RANGE undefined -> NOT FIRED (counted).
    Warmup: first eligible decision index >= max(WARMUP_SESSIONS, K).
    """
    first_i = max(WARMUP_SESSIONS, K) if first_i is None else first_i
    n = adj_close.shape[0]
    fired = np.zeros(n, dtype=bool)
    drops = {"warmup": 0, "break": 0, "break_no_reclaim": 0, "range_undefined": 0,
             "range": 0, "dvol": 0, "floor_price": 0, "floor_dvol": 0}
    if n <= first_i:
        drops["warmup"] = n
        return fired, np.zeros(n, dtype=bool), drops
    dvol = _dvol(adj_close, volume)
    if med60 is None:
        med60 = _rolling_median(dvol, DVOL_WINDOW)
    degenerate = adj_high <= adj_low
    for i in range(first_i, n):
        if i < K:
            drops["warmup"] += 1        # construction window out of range
            continue
        prior_lo = float(np.min(adj_low[i - K:i]))
        if not (adj_low[i] < prior_lo):
            drops["break"] += 1
            continue
        if not (adj_close[i] > prior_lo):
            drops["break_no_reclaim"] += 1
            continue
        if degenerate[i]:
            drops["range_undefined"] += 1   # zero-range law: never imputed
            continue
        range_frac = (float(adj_close[i]) - float(adj_low[i])) / (
            float(adj_high[i]) - float(adj_low[i]))
        if range_frac < RANGE_MIN:
            drops["range"] += 1
            continue
        m = med60[i]
        if not np.isfinite(m) or m <= 0 or dvol[i] < DVOL_MULT * m:
            drops["dvol"] += 1
            continue
        fired[i] = True
        if adj_close[i] < FLOOR_PRICE:
            drops["floor_price"] += 1
        if m < FLOOR_DVOL:
            drops["floor_dvol"] += 1
    return fired, _bookable(fired, adj_close, volume, med60), drops


def census_gap(adj_open, adj_close, volume, pctl: int, direction: str,
               first_i: int | None = None,
               med60: np.ndarray | None = None):
    """Fired iff gap_t on the chosen side of its trailing-252 percentile.

    gap_t = adj_open_t/adj_close_{t-1} - 1; history = the trailing 252
    gaps ending at and including t; percentile linear (pinned).
    fade FIRED iff gap_t <= P_pctl; confirm FIRED iff gap_t >= P_pctl.
    """
    first_i = WARMUP_SESSIONS if first_i is None else first_i
    n = adj_close.shape[0]
    fired = np.zeros(n, dtype=bool)
    drops = {"warmup": 0, "history_undefined": 0, "no_side": 0}
    if n <= first_i:
        drops["warmup"] = n
        return fired, np.zeros(n, dtype=bool), drops
    with np.errstate(divide="ignore", invalid="ignore"):
        gaps = np.full(n, np.nan)
        gaps[1:] = adj_open[1:] / adj_close[:-1] - 1.0
    for i in range(first_i, n):
        if i < 251:
            drops["history_undefined"] += 1   # 252-gap history out of range
            continue
        hist = gaps[i - 251:i + 1]
        if not np.all(np.isfinite(hist)):
            drops["history_undefined"] += 1
            continue
        thr = float(np.percentile(hist, pctl, method=PERCENTILE_METHOD))
        g = float(gaps[i])
        if direction == "fade":
            hit = g <= thr
        elif direction == "confirm":
            hit = g >= thr
        else:
            raise ValueError(f"unknown GAP direction {direction}")
        if hit:
            fired[i] = True
        else:
            drops["no_side"] += 1
    return fired, _bookable(fired, adj_close, volume, med60), drops


def census_52w_high(adj_close, volume, band_pct: int,
                    first_i: int | None = None,
                    med60: np.ndarray | None = None):
    """Fired iff proximity to the rolling 252-session adjusted-close high
    (ending at and including t) is <= band_pct/100."""
    first_i = WARMUP_SESSIONS if first_i is None else first_i
    n = adj_close.shape[0]
    fired = np.zeros(n, dtype=bool)
    drops = {"warmup": 0, "history_undefined": 0, "outside_band": 0}
    if n <= first_i:
        drops["warmup"] = n
        return fired, np.zeros(n, dtype=bool), drops
    high = _rolling_max(adj_close, 252)
    for i in range(first_i, n):
        hi = float(high[i])
        if not np.isfinite(hi):
            drops["history_undefined"] += 1
            continue
        if not hi > 0.0:
            # r2 fix (real-data defect, disclosed): zero-priced OTC shells
            # carry a 252-session high of exactly 0.0 — proximity is
            # UNDEFINED there; the state NEVER fires and the bar is
            # censused (same fail-closed family as the zero-range law).
            # r1 crashed with ZeroDivisionError on this input.
            drops["history_undefined"] += 1
            continue
        prox = (hi - float(adj_close[i])) / hi
        if prox <= band_pct / 100.0:
            fired[i] = True
        else:
            drops["outside_band"] += 1
    return fired, _bookable(fired, adj_close, volume, med60), drops


def census_clv_range(adj_high, adj_low, adj_close, volume, k: int,
                     first_i: int | None = None,
                     med60: np.ndarray | None = None):
    """P_t = sum of CLV over the trailing 20 completed bars; slope = P_t -
    P_{t-k}; FIRED iff slope > 0 (strict).  Zero-range law: a high==low bar
    makes CLV undefined -> P undefined on any window containing it -> NOT
    FIRED (fail-closed, never imputed); degenerate bars counted."""
    first_i = max(WARMUP_SESSIONS, CLV_WINDOW - 1 + k) if first_i is None else first_i
    n = adj_close.shape[0]
    fired = np.zeros(n, dtype=bool)
    drops = {"warmup": 0, "range_undefined": 0, "slope_nonpos": 0}
    if n <= first_i:
        drops["warmup"] = n
        return fired, np.zeros(n, dtype=bool), drops
    span = adj_high - adj_low
    degenerate = span <= 0
    clv = np.full(n, np.nan)
    ok = ~degenerate
    clv[ok] = ((adj_close[ok] - adj_low[ok]) - (adj_high[ok] - adj_close[ok])) / span[ok]
    need = CLV_WINDOW + k          # bars t-(CLV_WINDOW-1)-k .. t
    for i in range(first_i, n):
        if i - need + 1 < 0:
            drops["range_undefined"] += 1   # window out of range
            continue
        win = clv[i - need + 1:i + 1]
        if not np.all(np.isfinite(win)):
            drops["range_undefined"] += 1   # includes zero-range bars in-window
            continue
        p_t = float(win[-CLV_WINDOW:].sum())
        p_prev = float(win[:CLV_WINDOW].sum())
        if p_t - p_prev > 0:
            fired[i] = True
        else:
            drops["slope_nonpos"] += 1
    return fired, _bookable(fired, adj_close, volume, med60), drops


def census_dvol_shock(adj_close, volume, ratio: float, direction: str,
                      first_i: int | None = None,
                      med60: np.ndarray | None = None):
    """Shock iff dvol_t >= ratio * median(dvol over trailing 60 sessions
    ending at t-1).  confirm FIRED iff shock AND ret_t > 0; fade FIRED iff
    shock AND ret_t < 0; ret_t == 0 NOT FIRED (fail-closed neutral)."""
    first_i = WARMUP_SESSIONS if first_i is None else first_i
    n = adj_close.shape[0]
    fired = np.zeros(n, dtype=bool)
    drops = {"warmup": 0, "no_shock": 0, "neutral_ret": 0}
    if n <= first_i:
        drops["warmup"] = n
        return fired, np.zeros(n, dtype=bool), drops
    dvol = _dvol(adj_close, volume)
    if med60 is None:
        med60 = _rolling_median(dvol, DVOL_WINDOW)
    with np.errstate(divide="ignore", invalid="ignore"):
        ret = np.full(n, np.nan)
        ret[1:] = adj_close[1:] / adj_close[:-1] - 1.0
    for i in range(first_i, n):
        m = med60[i]
        if not np.isfinite(m) or m <= 0 or dvol[i] < ratio * m:
            drops["no_shock"] += 1
            continue
        r = float(ret[i])
        if r > 0 and direction == "confirm":
            fired[i] = True
        elif r < 0 and direction == "fade":
            fired[i] = True
        else:
            drops["neutral_ret"] += 1
    return fired, _bookable(fired, adj_close, volume, med60), drops


def census_vol_regime(adj_close, volume, L: int, direction: str,
                      first_i: int | None = None,
                      med60: np.ndarray | None = None):
    """sigma_j = std(ddof=1) of close-to-close log returns over the
    trailing L returns ending at and including j; boundaries = 1/3, 2/3
    quantiles (linear) of sigma over the trailing 252-session window
    ending at and including t, same-bar assignment, NEVER full-sample.
    long-LOW FIRED iff sigma_t <= q1; long-HIGH FIRED iff sigma_t >= q2."""
    need = WARMUP_SESSIONS - 1 + L
    first_i = need if first_i is None else first_i
    n = adj_close.shape[0]
    fired = np.zeros(n, dtype=bool)
    drops = {"warmup": 0, "history_undefined": 0, "middle_tercile": 0}
    if n <= first_i:
        drops["warmup"] = n
        return fired, np.zeros(n, dtype=bool), drops
    with np.errstate(divide="ignore", invalid="ignore"):
        lr = np.full(n, np.nan)
        lr[1:] = np.log(adj_close[1:] / adj_close[:-1])
    # sigma_j over the L returns at sessions j-L+1..j
    rets = lr[1:]  # rets[j-1] = log return at session j
    sigma = np.full(n, np.nan)
    for j in range(L, n):
        w = rets[j - L:j]
        if np.all(np.isfinite(w)) and w.shape[0] == L:
            sigma[j] = float(np.std(w, ddof=1))
    for i in range(first_i, n):
        if i < 251:
            drops["history_undefined"] += 1   # 252-sigma history out of range
            continue
        hist = sigma[i - 251:i + 1]
        if not np.all(np.isfinite(hist)):
            drops["history_undefined"] += 1
            continue
        q1, q2 = np.percentile(hist, [100.0 / 3.0, 200.0 / 3.0],
                               method=PERCENTILE_METHOD)
        s = float(sigma[i])
        if direction == "low":
            if s <= q1:
                fired[i] = True
            else:
                drops["middle_tercile"] += 1
        elif direction == "high":
            if s >= q2:
                fired[i] = True
            else:
                drops["middle_tercile"] += 1
        else:
            raise ValueError(f"unknown VOL-REGIME direction {direction}")
    return fired, _bookable(fired, adj_close, volume, med60), drops


# ----------------------------------------------------- r2 fast kernels ----
# Batched re-expressions of the r1 census kernels with IDENTICAL semantics
# (same drop-bucket priority, same thresholds, same nan/fail-closed laws).
# Every full-census run must first pass equivalence_gate(): old vs new must
# agree EXACTLY (fired mask, bookable mask, drop counts) on a deterministic
# sample of real cached names, else the run TECHABORTs (fail-closed).

def census_event_unwind_fast(adj_open, adj_high, adj_low, adj_close, volume,
                             K: int, first_i: int | None = None,
                             med60: np.ndarray | None = None):
    """Vectorized census_event_unwind (identical semantics)."""
    from numpy.lib.stride_tricks import sliding_window_view
    first_i = max(WARMUP_SESSIONS, K) if first_i is None else first_i
    n = adj_close.shape[0]
    fired = np.zeros(n, dtype=bool)
    drops = {"warmup": 0, "break": 0, "break_no_reclaim": 0, "range_undefined": 0,
             "range": 0, "dvol": 0, "floor_price": 0, "floor_dvol": 0}
    if n <= first_i:
        drops["warmup"] = n
        return fired, np.zeros(n, dtype=bool), drops
    dvol = _dvol(adj_close, volume)
    if med60 is None:
        med60 = _rolling_median(dvol, DVOL_WINDOW)
    prior_lo = np.full(n, np.nan)
    if n > K:
        sw = sliding_window_view(adj_low, K)          # sw[m] = adj_low[m:m+K]
        prior_lo[K:] = sw.min(axis=1)[:n - K]         # prior_lo[i] = min(low[i-K:i])
    e = slice(first_i, n)
    lo_e, pr_e = adj_low[e], prior_lo[e]
    cl_e, hi_e = adj_close[e], adj_high[e]
    dv_e, m_e = dvol[e], med60[e]
    deg_e = hi_e <= lo_e
    span_e = hi_e - lo_e
    with np.errstate(divide="ignore", invalid="ignore"):
        frac_e = np.where(span_e > 0, (cl_e - lo_e) / span_e, np.nan)
    c_break = lo_e < pr_e
    c_reclaim = c_break & (cl_e > pr_e)
    c_range = c_reclaim & ~deg_e & (frac_e >= RANGE_MIN)
    with np.errstate(invalid="ignore"):
        dv_ok = np.isfinite(m_e) & (m_e > 0) & (dv_e >= DVOL_MULT * m_e)
    c_fire = c_range & dv_ok
    fired_idx = first_i + np.nonzero(c_fire)[0]
    fired[fired_idx] = True
    with np.errstate(invalid="ignore"):
        drops["break"] = int((~c_break).sum())
        drops["break_no_reclaim"] = int((c_break & ~c_reclaim).sum())
        drops["range_undefined"] = int((c_reclaim & deg_e).sum())
        drops["range"] = int((c_reclaim & ~deg_e & (frac_e < RANGE_MIN)).sum())
        drops["dvol"] = int((c_range & ~dv_ok).sum())
        drops["floor_price"] = int((c_fire & (cl_e < FLOOR_PRICE)).sum())
        drops["floor_dvol"] = int((c_fire & (m_e < FLOOR_DVOL)).sum())
    return fired, _bookable(fired, adj_close, volume, med60), drops


def census_gap_fast(adj_open, adj_close, volume, pctl: int, direction: str,
                    first_i: int | None = None,
                    med60: np.ndarray | None = None):
    """Vectorized census_gap (identical semantics; percentile batched over a
    sliding view — nan-containing windows yield nan thresholds exactly like
    the r1 all-finite check)."""
    from numpy.lib.stride_tricks import sliding_window_view
    first_i = WARMUP_SESSIONS if first_i is None else first_i
    n = adj_close.shape[0]
    fired = np.zeros(n, dtype=bool)
    drops = {"warmup": 0, "history_undefined": 0, "no_side": 0}
    if n <= first_i:
        drops["warmup"] = n
        return fired, np.zeros(n, dtype=bool), drops
    with np.errstate(divide="ignore", invalid="ignore"):
        gaps = np.full(n, np.nan)
        gaps[1:] = adj_open[1:] / adj_close[:-1] - 1.0
    sw = sliding_window_view(gaps, 252)               # sw[m] = gaps[m:m+252]
    with np.errstate(invalid="ignore"):
        thr_all = np.percentile(sw, pctl, axis=1, method=PERCENTILE_METHOD)
    e = slice(first_i, n)                             # i >= first_i >= 252
    thr_e = thr_all[e.start - 251:]
    fin_e = np.isfinite(thr_e)
    g_e = gaps[e]
    if direction == "fade":
        hit = fin_e & (g_e <= thr_e)
    elif direction == "confirm":
        hit = fin_e & (g_e >= thr_e)
    else:
        raise ValueError(f"unknown GAP direction {direction}")
    fired[first_i + np.nonzero(hit)[0]] = True
    drops["history_undefined"] = int((~fin_e).sum())
    drops["no_side"] = int((fin_e & ~hit).sum())
    return fired, _bookable(fired, adj_close, volume, med60), drops


def census_dvol_shock_fast(adj_close, volume, ratio: float, direction: str,
                           first_i: int | None = None,
                           med60: np.ndarray | None = None):
    """Vectorized census_dvol_shock (identical semantics)."""
    first_i = WARMUP_SESSIONS if first_i is None else first_i
    n = adj_close.shape[0]
    fired = np.zeros(n, dtype=bool)
    drops = {"warmup": 0, "no_shock": 0, "neutral_ret": 0}
    if n <= first_i:
        drops["warmup"] = n
        return fired, np.zeros(n, dtype=bool), drops
    dvol = _dvol(adj_close, volume)
    if med60 is None:
        med60 = _rolling_median(dvol, DVOL_WINDOW)
    with np.errstate(divide="ignore", invalid="ignore"):
        ret = np.full(n, np.nan)
        ret[1:] = adj_close[1:] / adj_close[:-1] - 1.0
    e = slice(first_i, n)
    m_e, dv_e, r_e = med60[e], dvol[e], ret[e]
    with np.errstate(invalid="ignore"):
        shock = np.isfinite(m_e) & (m_e > 0) & (dv_e >= ratio * m_e)
        if direction == "confirm":
            hit = shock & (r_e > 0)
        elif direction == "fade":
            hit = shock & (r_e < 0)
        else:
            raise ValueError(f"unknown DVOL-SHOCK direction {direction}")
    fired[first_i + np.nonzero(hit)[0]] = True
    drops["no_shock"] = int((~shock).sum())
    drops["neutral_ret"] = int((shock & ~hit).sum())
    return fired, _bookable(fired, adj_close, volume, med60), drops


def census_vol_regime_fast(adj_close, volume, L: int, direction: str,
                           first_i: int | None = None,
                           med60: np.ndarray | None = None):
    """Vectorized census_vol_regime (identical semantics: causal sigma over
    the trailing L returns, tercile boundaries over the trailing 252 sigma
    window, same-bar assignment, nan windows fail closed)."""
    from numpy.lib.stride_tricks import sliding_window_view
    need = WARMUP_SESSIONS - 1 + L
    first_i = need if first_i is None else first_i
    n = adj_close.shape[0]
    fired = np.zeros(n, dtype=bool)
    drops = {"warmup": 0, "history_undefined": 0, "middle_tercile": 0}
    if n <= first_i:
        drops["warmup"] = n
        return fired, np.zeros(n, dtype=bool), drops
    with np.errstate(divide="ignore", invalid="ignore"):
        lr = np.full(n, np.nan)
        lr[1:] = np.log(adj_close[1:] / adj_close[:-1])
    rets = lr[1:]                                     # rets[m] = return at session m+1
    sigma = np.full(n, np.nan)
    if n > L:
        sw = sliding_window_view(rets, L)             # sw[m] = rets[m:m+L] -> session j=m+L
        with np.errstate(invalid="ignore"):
            sigma[L:] = np.std(sw, axis=1, ddof=1)    # nan window -> nan (fail-closed)
    sw2 = sliding_window_view(sigma, 252)             # sw2[m] = sigma[m:m+252] -> session i=m+251
    with np.errstate(invalid="ignore"):
        q = np.percentile(sw2, [100.0 / 3.0, 200.0 / 3.0], axis=1,
                          method=PERCENTILE_METHOD)   # (2, n-251)
    e = slice(first_i, n)                             # i >= 251+L > 251
    m0 = e.start - 251
    q1_e, q2_e, s_e = q[0, m0:], q[1, m0:], sigma[e]
    fin_e = np.isfinite(q1_e) & np.isfinite(q2_e)
    with np.errstate(invalid="ignore"):
        if direction == "low":
            hit = fin_e & (s_e <= q1_e)
        elif direction == "high":
            hit = fin_e & (s_e >= q2_e)
        else:
            raise ValueError(f"unknown VOL-REGIME direction {direction}")
    fired[first_i + np.nonzero(hit)[0]] = True
    drops["history_undefined"] = int((~fin_e).sum())
    drops["middle_tercile"] = int((fin_e & ~hit).sum())
    return fired, _bookable(fired, adj_close, volume, med60), drops


def run_config_census_r1(config: dict, adj_open, adj_high, adj_low, adj_close,
                         volume, first_i: int | None = None):
    """Dispatch to the r1 (reference) kernels — equivalence-gate baseline."""
    fam, p = config["family"], config["params"]
    if fam == "EVENT-UNWIND":
        return census_event_unwind(adj_open, adj_high, adj_low, adj_close,
                                   volume, p["K"], first_i)
    if fam == "GAP":
        return census_gap(adj_open, adj_close, volume, p["pctl"],
                          p["direction"], first_i)
    if fam == "52W-HIGH":
        return census_52w_high(adj_close, volume, p["band_pct"], first_i)
    if fam == "CLV-RANGE":
        return census_clv_range(adj_high, adj_low, adj_close, volume,
                                p["k"], first_i)
    if fam == "DVOL-SHOCK":
        return census_dvol_shock(adj_close, volume, p["ratio"],
                                 p["direction"], first_i)
    if fam == "VOL-REGIME":
        return census_vol_regime(adj_close, volume, p["L"], p["direction"],
                                 first_i)
    raise ValueError(f"unknown family {fam}")


def run_config_census(config: dict, adj_open, adj_high, adj_low, adj_close,
                      volume, first_i: int | None = None,
                      med60: np.ndarray | None = None):
    """Dispatch ONE frozen configuration's census on ONE name (pure).

    Returns (fired_mask, bookable_mask, drops).  r2: dispatches to the
    batched kernels (bit-equivalent to the r1 reference kernels, enforced
    by the runner's equivalence gate on real data); the per-name med60
    series is shared across configurations."""
    fam, p = config["family"], config["params"]
    if fam == "EVENT-UNWIND":
        return census_event_unwind_fast(adj_open, adj_high, adj_low, adj_close,
                                        volume, p["K"], first_i, med60)
    if fam == "GAP":
        return census_gap_fast(adj_open, adj_close, volume, p["pctl"],
                               p["direction"], first_i, med60)
    if fam == "52W-HIGH":
        return census_52w_high(adj_close, volume, p["band_pct"], first_i,
                               med60)
    if fam == "CLV-RANGE":
        return census_clv_range(adj_high, adj_low, adj_close, volume,
                                p["k"], first_i, med60)
    if fam == "DVOL-SHOCK":
        return census_dvol_shock_fast(adj_close, volume, p["ratio"],
                                      p["direction"], first_i, med60)
    if fam == "VOL-REGIME":
        return census_vol_regime_fast(adj_close, volume, p["L"], p["direction"],
                                      first_i, med60)
    raise ValueError(f"unknown family {fam}")


# ------------------------------------------------------ floors, bands, clock

def _bookable(fired: np.ndarray, adj_close: np.ndarray, volume: np.ndarray,
              med60: np.ndarray | None = None) -> np.ndarray:
    """F4 bookability floors applied AT FIRED DECISIONS only:
    adj_close >= $1.00 AND trailing 60-session median dvol >= $2M
    (dvol = adj_close * volume).  A non-finite median fails the floor."""
    out = np.zeros(fired.shape, dtype=bool)
    idx = np.nonzero(fired)[0]
    if idx.size == 0:
        return out
    if med60 is None:
        med60 = _rolling_median(_dvol(adj_close, volume), DVOL_WINDOW)
    m = med60[idx]
    ok_price = adj_close[idx] >= FLOOR_PRICE
    ok_dvol = np.isfinite(m) & (m >= FLOOR_DVOL)
    out[idx] = ok_price & ok_dvol
    return out


def resolve_band(median_dvol_252) -> str:
    """F6 ADV band, fail-closed: non-finite median -> UNRESOLVED (raise)."""
    if median_dvol_252 is None or not np.isfinite(median_dvol_252):
        raise ValueError("band UNRESOLVED: median_dvol_252 missing/non-finite "
                         "(fail-closed)")
    if median_dvol_252 >= BANDS_DEF["A"]:
        return "A"
    if median_dvol_252 >= BANDS_DEF["B"]:
        return "B"
    if median_dvol_252 >= BANDS_DEF["C"]:
        return "C"
    return "SUBFLOOR"


def clock_legs(t: int, H: int) -> tuple[int, int, int]:
    """F5 frozen clock: decision at t close, entry t+1 open, exit t+1+H open."""
    if H <= 0:
        raise ValueError("H must be positive")
    return t, t + 1, t + 1 + H


# ------------------------------------------------------------------- folds

def fold_boundaries(start: str = WINDOW_START, end: str = WINDOW_END) -> list[str]:
    """Calendar thirds of [start, end] on DATES — independent of any event
    or price data, so the freeze needs no source access."""
    d0, d1 = date.fromisoformat(start), date.fromisoformat(end)
    total = (d1 - d0).days
    if total <= 0:
        raise ValueError("empty window")
    b1 = d0 + timedelta(days=total // 3)
    b2 = d0 + timedelta(days=(2 * total) // 3)
    return [b1.isoformat(), b2.isoformat()]


def fold_freeze_artifact() -> dict:
    b1, b2 = fold_boundaries()
    return {
        "schema": "stocks_search_v1_fold_freeze@1",
        "cycle_id": CYCLE_ID,
        "gate": "F8 (plans/PLAN_stocks_search_v1.md §4)",
        "window": [WINDOW_START, WINDOW_END],
        "rule": ("three chronological folds; boundaries = exact calendar "
                 "thirds of the window computed on DATES, independent of "
                 "event/price data; F1 = [start, B1], F2 = (B1, B2], "
                 "F3 = (B2, end]; decision assigned by decision DATE"),
        "boundaries": {"B1": b1, "B2": b2},
        "folds": [
            {"id": "F1", "start": WINDOW_START, "end": b1},
            {"id": "F2", "start": b1, "end": b2, "half_open": "(B1, B2]"},
            {"id": "F3", "start": b2, "end": WINDOW_END, "half_open": "(B2, end]"},
        ],
        "regime_law": ("window 2015+: the 2020-03 deleveraging sits in F2, "
                       "the 2022 bear in F3; 2008Q4–2009 predates the window "
                       "so the never-share rule (2008Q4–2009 and 2020-03 "
                       "never in one fold) is moot"),
        "q6_floor": {"floor": FOLD_EVENT_FLOOR, "basis": FOLD_FLOOR_PASS_BASIS,
                     "law": "fail-closed kill recorded, never silently dropped",
                     "measured": False,
                     "note": ("counts materialize at census time; the freeze "
                              "(window, rule, boundaries) is source-"
                              "independent and frozen BEFORE any census")},
        "frozen_at_utc": None,   # filled by the writer
        "lineage": "NG6 fold convention re-inherited (calendar thirds, window 2015+)",
    }


def assign_fold(iso_date: str, b1: str, b2: str) -> str:
    """F1 = [start, B1], F2 = (B1, B2], F3 = (B2, end]."""
    d = date.fromisoformat(iso_date)
    if d <= date.fromisoformat(b1):
        return "F1"
    if d <= date.fromisoformat(b2):
        return "F2"
    return "F3"


def never_share_law_ok(b1: str, b2: str, window_start: str, window_end: str,
                       regime_a: str = "2008-12-01", regime_b: str = "2020-03-15") -> bool:
    """F8 law: 2008Q4–2009 and 2020-03 never share a fold — true iff the
    regimes land in different folds OR at least one predates the window."""
    fa = fb = None
    if date.fromisoformat(window_start) <= date.fromisoformat(regime_a) <= date.fromisoformat(window_end):
        fa = assign_fold(regime_a, b1, b2)
    if date.fromisoformat(window_start) <= date.fromisoformat(regime_b) <= date.fromisoformat(window_end):
        fb = assign_fold(regime_b, b1, b2)
    return fa is None or fb is None or fa != fb


# ------------------------------------------------------------- gate logic

KEY_ENV_VAR = "EODHD_API_KEY"


def key_status(env: dict | None = None) -> dict:
    """Env-var presence probe.  NEVER returns or logs the key material."""
    env = os.environ if env is None else env
    present = KEY_ENV_VAR in env and len(str(env[KEY_ENV_VAR]).strip()) > 0
    return {"env_var": KEY_ENV_VAR, "present": present,
            "law": "key from environment variable ONLY; never echoed, never "
                   "written to any artifact"}


def three_layer_gate(reachable: dict, permitted: bool, served: dict) -> dict:
    """P-25 three-layer gate: reachable AND permitted AND served — all
    three layers must PASS or the gate FAILS (fail-closed)."""
    ok_reachable = bool(reachable) and all(
        r.get("status") == 200 for r in reachable.values())
    ok_served = bool(served) and all(
        s.get("status") == 200 and s.get("has_adjusted_close")
        and s.get("has_volume") for s in served.values())
    layers = {"reachable": ok_reachable, "permitted": bool(permitted),
              "served": ok_served}
    return {"layers": layers, "pass": all(layers.values())}


def verdict_row(verdict: str, law: str, detail: dict) -> dict:
    return {"verdict": verdict, "law": law, "detail": detail}


def assemble_gate(gates: dict, d2_status: str = "SKIPPED_BY_OWNER_AMENDMENT_3B",
                  r0_status: str = "NOT_RUN") -> dict:
    """Assemble the p0_gate.json body.  Overall verdict, fail-closed:
    F1 FAIL -> BLOCKED_SOURCE_OR_SCHEMA; any FAIL -> FAIL_FAIL_CLOSED;
    all PASS -> PASS; otherwise NOT_RUN_FAIL_CLOSED."""
    if gates["F1"]["verdict"] == "FAIL":
        overall = "BLOCKED_SOURCE_OR_SCHEMA"
    elif any(g["verdict"] == "FAIL" for g in gates.values()):
        overall = "FAIL_FAIL_CLOSED"
    elif all(g["verdict"] == "PASS" for g in gates.values()):
        overall = "PASS"
    else:
        overall = "NOT_RUN_FAIL_CLOSED"
    return {
        "schema": "stocks_search_v1_p0_gate@1",
        "cycle_id": CYCLE_ID,
        "task_id": TASK_ID,
        "plan": PLAN,
        "scope": ("P0 = source engineering + census ONLY; no candidate PnL, "
                  "PF, Sharpe, drawdown, survivors or S1 evidence computed "
                  "anywhere in this run"),
        "d2_status": d2_status,
        "r0_status": r0_status,
        "amendment_3b": ("D2 skipped by owner amendment §3b (2026-09-17 #2); "
                         "the per-config fired census is measured at P0 as a "
                         "pure data census (fired counts only)"),
        "relaxation_disclosure": ("accepted under owner-relaxed acceptance "
                                  "battery (R0 0.30 / DSR alpha 0.10 at N = "
                                  "grid) | PBO NOT_RUN fail-closed (<=3 cells, "
                                  "d0992d17 class) | R0 NOT_RUN (D2 skipped by "
                                  "owner amendment §3b)"),
        "gates": gates,
        "overall_verdict": overall,
        "outcome": ("STOCKS_SEARCH_V1_BLOCKED_SOURCE_OR_SCHEMA"
                    if overall == "BLOCKED_SOURCE_OR_SCHEMA" else None),
        "no_pnl_computed": True,
    }


def blocked_gates(reason: str, evidence: dict) -> dict:
    """The fail-closed F1-failure gate set: F1 FAIL; F2–F8 NOT_RUN blocked
    by F1; F9 NOT_RUN (partial artifacts committed, digests pinned)."""
    gates = {
        "F1": verdict_row(
            "FAIL",
            "P-25 three-layer gate FIRST, before any bulk retrieval; key "
            "from EODHD_API_KEY env var ONLY",
            {"reason": reason, "evidence": evidence}),
    }
    for gid, law in (
        ("F2", "canaries at window start/middle/recent end; double-pull "
               "byte-identity; raw sha256 pinned; never-existed ticker 404"),
        ("F3", "adjusted (total-return) series is THE single representation"),
        ("F4", "death-inclusive cohort census; served-session census; "
               "bookability floors; warmup 252 served sessions"),
        ("F5", "ONE frozen daily decision clock; bar-readable close+1; "
               "timezone/DST fixtures"),
        ("F6", "band schedule A:10/B:15/C:25 bps on ADV {50M,10M,2M}; "
               "band-C fraction ON the fired population"),
        ("F7", "SPY adjusted series acquired + pinned"),
        ("F8", "folds frozen BEFORE census; per-config per-fold fired census "
               "over all 47 §5 configurations; floor >= 30 bookable fired "
               "decisions/fold fail-closed"),
    ):
        detail = {"blocked_by": "F1", "fail_closed": True}
        if gid == "F5":
            detail["committed_contract"] = "clock_contract.json (frozen, no network needed)"
            detail["dst_fixtures"] = ("tests/test_stocks_search_v1_p0.py runs "
                                      "without network; a green run verifies "
                                      "the clock/DST fixture layer only — the "
                                      "served-session data plane stays NOT_RUN")
        gates[gid] = verdict_row("NOT_RUN", law, detail)
    gates["F9"] = verdict_row(
        "NOT_RUN",
        "census code, raw-request manifest, digest manifest, calendar/clock "
        "contract, cost bands, folds AND the frozen search-space manifest "
        "committed; detached rerun reproduces",
        {"blocked_by": "F1",
         "committed_partial": True,
         "note": ("census code + fold/cost/clock/config freezes committed "
                  "with sha256 digests; raw-request and digest manifests "
                  "materialize only on a keyed run; detached rerun NOT "
                  "demonstrated")})
    return gates


# ------------------------------------------------------------------ digests

def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(path) -> str:
    return sha_bytes(open(path, "rb").read())


def redact(s: str) -> str:
    """Best-effort token scrub for any string that might embed a URL."""
    return re.sub(r"(api_token|token)=[^&\\s'\\\"]+", r"\1=REDACTED", s)


def write_json(path, obj) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(obj, indent=1, sort_keys=True) + "\n"
    path.write_text(data)
    return sha_bytes(data.encode())
