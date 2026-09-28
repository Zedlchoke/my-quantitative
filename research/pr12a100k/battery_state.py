"""pr12a100k.battery_state — PRE-PnL state battery (Lane I1b,
PORTFOLIO-ROUTER-12ASSETS-100K-V1).

Runs the two frozen pre-PnL measurements on the state engine:

(a) STATE CENSUS on the 5-pair intersection calendar (286 decision Fridays
    2021-01-08..2026-06-26, COVERAGE_NOTE Mon-aligned weeks): per-state
    merged episodes, dwell, occupancy, transitions matrix, and the
    preregistered floors F1 (>=10 merged episodes total), F2 (>=2 raw
    episodes per 26-week test fold), F3 (>=26 state-true weeks per fold),
    each with margin-to-floor. Failures mark the state NOT_RUN_THIN
    (permanent FLAT rows downstream) without stopping the other states.
    The fold grid (26w test, expanding train, 1w embargo, 52w warmup) is
    SAVED to research/pr12a100k/fold_grid.json for the evaluation lane.

(b) REPRESENTATION-RHO BATTERY (P-29, bar |rho| <= 0.20 pooled) vs dead
    ancestor observable classes, plus the P-20 arm-distinctness PRE-metric.
    No PnL is computed anywhere.

Run (canonical command, from the cycle worktree integration/):
    /Users/hoangminhlong/my-quantitative/.venv/bin/python \
        research/pr12a100k/battery_state.py

Outputs:
    research/control/PORTFOLIO-ROUTER-12ASSETS-100K-V1/battery/
        STATE_BATTERY_REPORT.json
        STATE_BATTERY_REPORT.md
    research/pr12a100k/fold_grid.json

Determinism: every number is a pure function of the frozen raw files; the
report carries payload_sha256 over the provenance-free payload so a re-run
must reproduce it byte-for-byte (only the provenance block — command,
runtimes, timestamp — may vary between runs).
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))          # .../pr12a100k
PKG = HERE
if PKG not in sys.path:
    sys.path.insert(0, PKG)

import loaders          # noqa: E402
import state_engine as se  # noqa: E402

# PKG = <worktree>/integration/research/pr12a100k -> worktree root is two
# dirnames up (integration/), NOT three (that would escape the worktree).
WORKTREE = os.path.dirname(os.path.dirname(PKG))
CONTROL = os.path.join(
    WORKTREE, "research", "control", "PORTFOLIO-ROUTER-12ASSETS-100K-V1")
BATTERY_DIR = os.path.join(CONTROL, "battery")
FOLD_GRID_PATH = os.path.join(PKG, "fold_grid.json")
REPORT_JSON = os.path.join(BATTERY_DIR, "STATE_BATTERY_REPORT.json")
REPORT_MD = os.path.join(BATTERY_DIR, "STATE_BATTERY_REPORT.md")

# Intersection calendar (COVERAGE_NOTE: Mon-aligned weeks Mon 2021-01-04 ..
# Sun 2026-06-28 = 286 weeks; Friday decisions).
CAL_FIRST = "2021-01-08"
CAL_LAST = "2026-06-26"
CAL_N = 286

WARMUP_WEEKS = 52
TEST_WEEKS = 26
EMBARGO_WEEKS = 1

F1_FLOOR = 10   # merged episodes / state, total
F2_FLOOR = 2    # raw episodes / state / fold
F3_FLOOR = 26   # state-true weeks / state / fold
RHO_BAR = 0.20  # P-29

M1_SYMBOLS = ("EURUSD", "GBPUSD", "USDJPY")
H1_SYMBOLS = ("USDCAD", "AUDUSD")
ALL_SYMBOLS = M1_SYMBOLS + H1_SYMBOLS

RV_RETURNS = 30          # 30-trading-day realized vol
RV_MIN_HISTORY = 63      # below this the RV percentile is undefined
ATR_PERIOD = 14
ATR_PCT = 80.0           # expansion = ATR14 >= its trailing-252 p80
DD_ENTRY = -0.30         # PSV1 SPARSE_RISK_OFF constants
DD_EXIT = -0.10
DD_DWELL_BARS = 90


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------------------
# D1 panel construction (price tape, for the rho battery only)
# ---------------------------------------------------------------------------

def _d1_mid_from_m1(m1: pd.DataFrame) -> pd.DataFrame:
    """D1 mid OHLC from a tradable M1 frame (close-stamped, loaders
    convention). mid_h/mid_l from per-minute (bid_h+ask_h)/2, (bid_l+ask_l)/2.
    """
    df = pd.DataFrame({
        "mid_o": m1["mid_o"],
        "mid_h": (m1["bid_h"] + m1["ask_h"]) / 2.0,
        "mid_l": (m1["bid_l"] + m1["ask_l"]) / 2.0,
        "mid_c": m1["mid_c"],
    })
    out = df.resample("D", closed="right", label="right").agg(
        {"mid_o": "first", "mid_h": "max", "mid_l": "min", "mid_c": "last"}
    ).dropna(how="all")
    return out


def load_d1_panels() -> tuple[dict[str, pd.DataFrame], dict]:
    """D1 mid panels for the 5 FX symbols in the data plane."""
    panels: dict[str, pd.DataFrame] = {}
    prov: dict[str, dict] = {}
    years = range(2021, 2027)
    for sym in M1_SYMBOLS:
        chunks = []
        for y in years:
            end = f"{y}-12-31" if y < 2026 else "2026-06-30"
            m1, meta = loaders.load_fx_m1(
                sym, start=f"{y}-01-01", end=end, tradable_only=True)
            chunks.append(_d1_mid_from_m1(m1))
        d1 = pd.concat(chunks).sort_index()
        panels[sym] = d1
        prov[sym] = {"kind": "m1_bi5->D1", "bars": int(len(d1)),
                     "first": str(d1.index.min().date()),
                     "last": str(d1.index.max().date())}
    for sym in H1_SYMBOLS:
        h1, meta = loaders.load_fx_h1(sym)
        d1 = h1[["mid_c"]].resample("D", closed="right", label="right").agg(
            {"mid_c": "last"}).dropna()
        panels[sym] = d1
        prov[sym] = {"kind": "anc_h1->D1 (mid close only; no true H/L "
                              "in ANC panels — ATR not computed for these)",
                     "bars": int(len(d1)),
                     "first": str(d1.index.min().date()),
                     "last": str(d1.index.max().date())}
    return panels, prov


# ---------------------------------------------------------------------------
# Derived tape observables
# ---------------------------------------------------------------------------

def rv30_percentile_series(d1: pd.DataFrame) -> pd.Series:
    """30-trading-day realized-vol percentile (inclusive rank within the
    trailing 252 RV values; min history RV_MIN_HISTORY; else NaN)."""
    c = d1["mid_c"].to_numpy(dtype="float64")
    r = np.full(len(c), np.nan)
    r[1:] = np.log(c[1:] / c[:-1])
    rv = np.full(len(c), np.nan)
    for i in range(RV_RETURNS, len(c)):
        rv[i] = float(np.std(r[i - RV_RETURNS + 1:i + 1], ddof=1))
    out = np.full(len(c), np.nan)
    for i in range(len(c)):
        if not np.isfinite(rv[i]):
            continue
        lo = max(0, i - se.PERCENTILE_WINDOW + 1)
        w = rv[lo:i + 1]
        w = w[np.isfinite(w)]
        if len(w) >= RV_MIN_HISTORY:
            out[i] = 100.0 * float(np.count_nonzero(w <= rv[i])) / len(w)
    return pd.Series(out, index=d1.index, name="rv30_pct")


def atr14_expansion_series(d1: pd.DataFrame) -> pd.Series:
    """ATR14 expansion indicator: ATR14 >= its inclusive p80 within the
    trailing 252 ATR values (NaN until 14 bars + rank history)."""
    h = d1["mid_h"].to_numpy(dtype="float64")
    l = d1["mid_l"].to_numpy(dtype="float64")
    c = d1["mid_c"].to_numpy(dtype="float64")
    tr = np.full(len(c), np.nan)
    tr[1:] = np.maximum.reduce([
        h[1:] - l[1:], np.abs(h[1:] - c[:-1]), np.abs(l[1:] - c[:-1])])
    atr = np.full(len(c), np.nan)
    for i in range(ATR_PERIOD, len(c)):
        atr[i] = float(np.nanmean(tr[i - ATR_PERIOD + 1:i + 1]))
    out = np.full(len(c), np.nan)
    for i in range(len(c)):
        if not np.isfinite(atr[i]):
            continue
        lo = max(0, i - se.PERCENTILE_WINDOW + 1)
        w = atr[lo:i + 1]
        w = w[np.isfinite(w)]
        if len(w) >= RV_MIN_HISTORY:
            pct = 100.0 * float(np.count_nonzero(w <= atr[i])) / len(w)
            out[i] = 1.0 if pct >= ATR_PCT else 0.0
    return pd.Series(out, index=d1.index, name="atr_expansion")


def drawdown_hysteresis_labels(d1: pd.DataFrame) -> pd.Series:
    """PSV1 SPARSE_RISK_OFF-style 2-regime labels on D1 closes.

    RISK_OFF entered when drawdown-from-running-max <= −30% for 90
    consecutive bars; RISK_ON re-entered when drawdown >= −10% for 90
    consecutive bars. Starts RISK_ON. (Constants from the frozen
    BTC-H4-TWO-REGIME detector, MAP.md lines 296-299.)
    """
    c = d1["mid_c"].to_numpy(dtype="float64")
    runmax = np.maximum.accumulate(c)
    dd = c / runmax - 1.0
    label = np.zeros(len(c), dtype="int8")  # 0 = RISK_ON, 1 = RISK_OFF
    entry_run = 0
    exit_run = 0
    for i in range(1, len(c)):
        if label[i - 1] == 0:
            entry_run = entry_run + 1 if dd[i] <= DD_ENTRY else 0
            if entry_run >= DD_DWELL_BARS:
                label[i] = 1
                entry_run = 0
                exit_run = 0
            else:
                label[i] = 0
        else:
            exit_run = exit_run + 1 if dd[i] >= DD_EXIT else 0
            if exit_run >= DD_DWELL_BARS:
                label[i] = 0
                exit_run = 0
                entry_run = 0
            else:
                label[i] = 1
    return pd.Series(label, index=d1.index, name="risk_off")


def sample_at_fridays(series: pd.Series, friday_ts_utc: np.ndarray) -> np.ndarray:
    """Value of a D1-stamped series at the last completed D1 bar before
    each decision timestamp (no lookahead: D1 bars close at 00:00 UTC of
    the following calendar day, so the decision Friday sees Thursday's
    bar — the same T−1 discipline as the engine's V2)."""
    idx = pd.DatetimeIndex(series.index).as_unit("ns").asi8
    vals = series.to_numpy(dtype="float64")
    pos = idx.searchsorted(friday_ts_utc, side="right") - 1
    out = np.full(len(pos), np.nan)
    for k, p in enumerate(pos):
        if p >= 0:
            out[k] = vals[p]
    return out


def pearson(x: np.ndarray, y: np.ndarray) -> tuple[float | None, int, str]:
    """Pearson rho over jointly-finite pairs; degenerate-aware."""
    m = np.isfinite(x) & np.isfinite(y)
    n = int(m.sum())
    if n < 3:
        return None, n, "insufficient_overlap"
    xs, ys = x[m], y[m]
    if np.std(xs) == 0.0 or np.std(ys) == 0.0:
        return None, n, "degenerate_constant_series"
    rho = float(np.corrcoef(xs, ys)[0, 1])
    return rho, n, "ok"


# ---------------------------------------------------------------------------
# Census + fold grid
# ---------------------------------------------------------------------------

def build_fold_grid(fridays: list[pd.Timestamp]) -> list[dict]:
    """26w test folds, expanding train, 1w embargo, 52w warmup consumed."""
    folds = []
    t = WARMUP_WEEKS
    while t + TEST_WEEKS <= len(fridays):
        folds.append({
            "fold_id": len(folds) + 1,
            "train_start": fridays[0].date().isoformat(),
            "train_end": fridays[t - 1 - EMBARGO_WEEKS].date().isoformat(),
            "embargo_week": fridays[t - 1].date().isoformat(),
            "test_start": fridays[t].date().isoformat(),
            "test_end": fridays[t + TEST_WEEKS - 1].date().isoformat(),
            "train_weeks": t - EMBARGO_WEEKS,
            "test_weeks": TEST_WEEKS,
        })
        t += TEST_WEEKS
    return folds


def raw_runs(seq: list[str]) -> list[tuple[str, int, int]]:
    runs = []
    s = 0
    for i in range(1, len(seq) + 1):
        if i == len(seq) or seq[i] != seq[s]:
            runs.append((seq[s], s, i - 1))
            s = i
    return runs


def census(tl: pd.DataFrame, fridays: list[pd.Timestamp],
           folds: list[dict]) -> dict:
    eff = list(tl["effective_state"])
    cand = list(tl["state"])
    ep_ids = list(tl["episode_id"])
    n = len(eff)

    # merged episodes parsed from the engine's own episode_id chain
    merged: dict[str, dict] = {}
    for i, ep in enumerate(ep_ids):
        if ep is None:
            continue
        rec = merged.setdefault(ep, {"state": eff[i], "start": i, "end": i,
                                     "true_weeks": 0})
        rec["end"] = max(rec["end"], i)
        rec["true_weeks"] += 1
    runs = raw_runs(eff)

    # transitions matrix (full, incl. diagonal)
    tm = {a: {b: 0 for b in se.STATES} for a in se.STATES}
    for i in range(1, n):
        tm[eff[i - 1]][eff[i]] += 1

    states_report: dict[str, dict] = {}
    for st in se.STATES:
        eps = [r for r in merged.values() if r["state"] == st]
        spans = sorted(e["end"] - e["start"] + 1 for e in eps)
        occ = sum(1 for e in eff if e == st)
        cand_weeks = sum(1 for c in cand if c == st)
        f1 = len(eps)
        f1_margin = f1 - F1_FLOOR

        per_fold_f2: dict[int, int] = {}
        per_fold_f3: dict[int, int] = {}
        for fo in folds:
            ts0 = (pd.Timestamp(fo["test_start"]) - fridays[0]).days // 7
            ts1 = (pd.Timestamp(fo["test_end"]) - fridays[0]).days // 7
            per_fold_f2[fo["fold_id"]] = sum(
                1 for (_s, a, b) in runs
                if _s == st and a <= ts1 and b >= ts0)
            per_fold_f3[fo["fold_id"]] = sum(
                1 for i in range(ts0, ts1 + 1) if eff[i] == st)
        f2_min = min(per_fold_f2.values())
        f3_min = min(per_fold_f3.values())
        verdict = ("PASS_FLOORS" if (f1 >= F1_FLOOR and f2_min >= F2_FLOOR
                                     and f3_min >= F3_FLOOR)
                   else "NOT_RUN_THIN")
        states_report[st] = {
            "candidate_weeks": cand_weeks,
            "occupancy_weeks": occ,
            "n_raw_runs": sum(1 for s, _a, _b in runs if s == st),
            "n_merged_episodes": f1,
            "merged_dwell_span_weeks": {
                "mean": float(np.mean(spans)) if spans else None,
                "median": float(np.median(spans)) if spans else None,
                "min": int(spans[0]) if spans else None,
                "max": int(spans[-1]) if spans else None,
            },
            "floors": {
                "F1_merged_episodes_total": {
                    "value": f1, "floor": F1_FLOOR, "margin": f1_margin,
                    "pass": f1 >= F1_FLOOR},
                "F2_raw_episodes_per_fold": {
                    "min_over_folds": f2_min, "floor": F2_FLOOR,
                    "margin": f2_min - F2_FLOOR,
                    "pass": f2_min >= F2_FLOOR, "per_fold": per_fold_f2},
                "F3_state_true_weeks_per_fold": {
                    "min_over_folds": f3_min, "floor": F3_FLOOR,
                    "margin": f3_min - F3_FLOOR,
                    "pass": f3_min >= F3_FLOOR, "per_fold": per_fold_f3},
            },
            "verdict": verdict,
        }
    return {
        "n_fridays": n,
        "states": states_report,
        "transitions_matrix_effective": tm,
        "raw_runs": [{"state": s, "start": fridays[a].date().isoformat(),
                      "end": fridays[b].date().isoformat(),
                      "weeks": b - a + 1} for s, a, b in runs],
        "merged_episodes": sorted(
            [{"episode_id": ep, "state": r["state"],
              "start": fridays[r["start"]].date().isoformat(),
              "end": fridays[r["end"]].date().isoformat(),
              "span_weeks": r["end"] - r["start"] + 1,
              "state_true_weeks": r["true_weeks"]}
             for ep, r in merged.items()],
            key=lambda d: d["start"]),
    }


# ---------------------------------------------------------------------------
# Rho battery
# ---------------------------------------------------------------------------

def rho_battery(tl: pd.DataFrame, panels: dict[str, pd.DataFrame],
                prov: dict) -> dict:
    v2_pct = tl["v2_pct"].to_numpy(dtype="float64")
    v2_stress = (tl["v2_band"].to_numpy() == "STRESS").astype("float64")
    state_stress = (tl["state"].to_numpy() == "RISK_STRESS").astype("float64")
    v3_war = (tl["v3_band"].to_numpy() == "WAR").astype("float64")
    friday_utc = np.array(
        [se._to_utc_ns(pd.Timestamp(t)) for t in
         [se._decision_friday_ts(pd.Timestamp(d).date().isoformat())
          for d in tl["decision_ts"]]], dtype="int64")

    eurusd = panels["EURUSD"]
    rv_pct = sample_at_fridays(rv30_percentile_series(eurusd), friday_utc)
    rv_p80 = np.where(np.isfinite(rv_pct), (rv_pct >= 80.0).astype("float64"),
                      np.nan)
    atr_exp = sample_at_fridays(atr14_expansion_series(eurusd), friday_utc)

    rows: list[dict] = []

    def add(name, x, y, ancestor, note):
        rho, n, status = pearson(x, y)
        rows.append({
            "comparison": name, "dead_ancestor_class": ancestor,
            "pearson_rho": rho, "n_weeks": n, "status": status,
            "bar": RHO_BAR,
            "verdict": ("PASS" if status == "ok" and abs(rho) <= RHO_BAR
                        else ("FAIL_RHO_BAR" if status == "ok" else status)),
            "note": note,
        })

    # (i) EURUSD 30d RV percentile vs our V2 (continuous + indicator form)
    add("rho(v2_pct, eurusd_rv30_pct) [continuous]", v2_pct, rv_pct,
        "RGC-G2 / FXFV3-A6 vol-percentile observable class",
        "V2 = VIX 252d inclusive percentile; EURUSD RV30 percentile sampled "
        "at the same Fridays on last-completed D1 bar")
    add("rho(v2_STRESS, eurusd_rv_p80) [indicator]", v2_stress, rv_p80,
        "RGC-G2 / FXFV3-A6 vol-percentile observable class", "")
    # (ii) RISK_STRESS state binary vs RV-p80 indicator
    add("rho(state_RISK_STRESS, eurusd_rv_p80) [indicator]", state_stress,
        rv_p80, "FXFV3-A6 RV-gated conditioning class",
        "state = raw ladder output (pre-dwell)")
    # short-window disclosure for the RV side
    short_window = int(np.count_nonzero(
        np.isfinite(v2_pct) & ~np.isfinite(rv_pct)))

    # (iii) per-symbol PSV1-style drawdown-hysteresis labels vs our state
    dd_table = {}
    for sym in ALL_SYMBOLS:
        lab = sample_at_fridays(drawdown_hysteresis_labels(panels[sym]),
                                friday_utc)
        rho_state, n1, s1 = pearson(state_stress, lab)
        rho_v2, n2, s2 = pearson(v2_stress, lab)
        n_off = int(np.nansum(lab))
        dd_table[sym] = {
            "rho_state_RISK_STRESS_vs_riskoff": rho_state,
            "n_weeks": n1, "status": s1,
            "rho_v2_STRESS_vs_riskoff": rho_v2,
            "risk_off_weeks": n_off,
            "verdict": ("PASS" if s1 == "ok" and abs(rho_state) <= RHO_BAR
                        else ("FAIL_RHO_BAR" if s1 == "ok" else s1)),
        }
    # (iv) TIPS slope — no data, NOT_RUN disclosed
    tips_row = {
        "comparison": "rho(V1 or state, tips_slope_z252)",
        "dead_ancestor_class": "FXFV8-A5 inflation-compensation term slope",
        "pearson_rho": None, "n_weeks": 0, "status": "NOT_RUN",
        "bar": RHO_BAR, "verdict": "NOT_RUN",
        "note": "no TIPS series in the data plane (L1 scope); disclosed, "
                "not substituted (dispatch contract)",
    }

    # P-20 arm-distinctness PRE-metrics
    m_p20 = np.isfinite(v2_stress) & np.isfinite(atr_exp)
    distinct_v2_atr = float(np.mean(
        v2_stress[m_p20] != atr_exp[m_p20])) if m_p20.sum() else None

    return {
        "rows": rows + [tips_row],
        "drawdown_hysteresis_per_symbol": dd_table,
        "rv_side_disclosure": {
            "fridays_where_rv_undefined_short_history": short_window,
            "note": "EURUSD D1 panel starts 2021-01; the first ~11 months of "
                    "Fridays have <252 RV observations and use the available "
                    "window (>=63 obs) — disclosed, deterministic",
        },
        "p20_distinctness": {
            "frac_fridays_v2band_differs_from_atr_expansion": distinct_v2_atr,
            "n_weeks": int(m_p20.sum()),
            "note": "ATR14>=p80(trailing 252) expansion indicator on EURUSD "
                    "D1 (vol_expansion_onset sleeve class)",
            "v3_backwardation_proxy": {
                "status": "SKIPPED_CIRCULAR",
                "note": "the 20d-backwardation proxy named by the dispatch "
                        "IS the Brent−WTI spread itself (= V3's own input); "
                        "measuring V3_band against it is tautological "
                        "(P-20), so the row is skipped and documented, "
                        "per the dispatch instruction",
            },
        },
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def write_markdown(report: dict, path: str) -> None:
    p = report
    lines = []
    a = lines.append
    a("# STATE BATTERY REPORT — I1b (PORTFOLIO-ROUTER-12ASSETS-100K-V1)")
    a("")
    a("Pre-PnL state census + representation-rho battery. NO PnL computed.")
    a("Engine: `research/pr12a100k/state_engine.py`; battery: "
      "`research/pr12a100k/battery_state.py`.")
    a("")
    a("- Command: `{}`".format(p["provenance"]["command"]))
    a("- Total runtime: {:.1f}s; payload_sha256 `{}` (deterministic core; "
      "re-runs must reproduce it)".format(
          p["provenance"]["runtimes_s"]["total"], p["payload_sha256"]))
    a("- Calendar: {} .. {} ({} Fridays, 5-pair intersection, COVERAGE_NOTE)"
      .format(p["calendar"]["first_friday"], p["calendar"]["last_friday"],
              p["calendar"]["n_fridays"]))
    a("- Fold grid: {} folds -> `{}`".format(
        p["fold_grid"]["n_folds"], FOLD_GRID_PATH))
    a("")
    a("## (a) State census and floors")
    a("")
    a("| state | merged ep | raw runs | occupancy w | dwell mean/med w |"
      " F1 marg | F2 min (fold) marg | F3 min w marg | verdict |")
    a("|---|---|---|---|---|---|---|---|---|")
    for st in se.STATES:
        s = p["state_census"]["states"][st]
        f = s["floors"]
        d = s["merged_dwell_span_weeks"]
        a("| {} | {} | {} | {} | {}/{} | {} ({}) | {} ({}) | {} ({}) | {} |".format(
            st, s["n_merged_episodes"], s["n_raw_runs"], s["occupancy_weeks"],
            None if d["mean"] is None else round(d["mean"], 1),
            None if d["median"] is None else round(d["median"], 1),
            f["F1_merged_episodes_total"]["value"],
            f["F1_merged_episodes_total"]["margin"],
            f["F2_raw_episodes_per_fold"]["min_over_folds"],
            f["F2_raw_episodes_per_fold"]["margin"],
            f["F3_state_true_weeks_per_fold"]["min_over_folds"],
            f["F3_state_true_weeks_per_fold"]["margin"],
            s["verdict"]))
    a("")
    a("Floors: F1 >= {} merged episodes (total); F2 >= {} raw episodes per "
      "26-week fold; F3 >= {} state-true weeks per fold. Any failure => "
      "NOT_RUN_THIN (permanent FLAT rows downstream).".format(
          F1_FLOOR, F2_FLOOR, F3_FLOOR))
    a("")
    a("Transitions matrix (effective, rows=from): see JSON "
      "`state_census.transitions_matrix_effective`.")
    a("")
    a("## (b) Representation-rho battery (P-29 bar |rho| <= 0.20)")
    a("")
    a("| comparison | rho | n | verdict |")
    a("|---|---|---|---|")
    for r in p["rho_battery"]["rows"]:
        rho = r["pearson_rho"]
        a("| {} | {} | {} | {} |".format(
            r["comparison"],
            "n/a" if rho is None else round(rho, 4), r["n_weeks"],
            r["verdict"]))
    a("")
    a("Per-symbol PSV1-style drawdown-hysteresis (−30%/−10%, 90-bar dwell):")
    a("")
    a("| symbol | rho(state RISK_STRESS, RISK_OFF) | risk-off weeks | verdict |")
    a("|---|---|---|---|")
    for sym, d in p["rho_battery"]["drawdown_hysteresis_per_symbol"].items():
        r1 = d["rho_state_RISK_STRESS_vs_riskoff"]
        a("| {} | {} | {} | {} |".format(
            sym, "n/a" if r1 is None else round(r1, 4),
            d["risk_off_weeks"], d["verdict"]))
    a("")
    a("P-20 distinctness: fraction of Fridays where V2_band differs from "
      "the ATR14-expansion indicator = {} (n={}); V3 vs 20d-backwardation "
      "proxy SKIPPED_CIRCULAR (the proxy IS the Brent−WTI spread — "
      "documented, not measured).".format(
          None if p["rho_battery"]["p20_distinctness"]
          ["frac_fridays_v2band_differs_from_atr_expansion"] is None
          else round(p["rho_battery"]["p20_distinctness"]
                     ["frac_fridays_v2band_differs_from_atr_expansion"], 4),
          p["rho_battery"]["p20_distinctness"]["n_weeks"]))
    a("")
    a("## Interpretation notes / disclosures")
    a("")
    for note in p["notes_disclosures"]:
        a("- {}".format(note))
    a("")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def main() -> None:
    t_start = time.time()
    os.makedirs(BATTERY_DIR, exist_ok=True)

    # ---- panel + timeline (twice: determinism self-check) ----------------
    t0 = time.time()
    panel = se.build_macro_panel()
    t_panel = time.time() - t0
    fridays = list(pd.date_range(CAL_FIRST, CAL_LAST, freq="7D"))
    assert len(fridays) == CAL_N, f"calendar drift: {len(fridays)} Fridays"

    t0 = time.time()
    tl = se.state_timeline(panel, [f.date().isoformat() for f in fridays])
    tl2 = se.state_timeline(panel, [f.date().isoformat() for f in fridays])
    det_ok = tl.equals(tl2)
    tl_sha = _sha256_bytes(tl.to_csv(index=False).encode())
    t_tl = time.time() - t0

    # ---- fold grid --------------------------------------------------------
    folds = build_fold_grid(fridays)
    fold_doc = {
        "schema": "pr12a100k_fold_grid@1",
        "cycle": "PORTFOLIO-ROUTER-12ASSETS-100K-V1",
        "generated_by": "research/pr12a100k/battery_state.py (Lane I1b)",
        "basis": "5-pair intersection calendar, Mon-aligned weeks "
                 "2021-01-04..2026-06-28 (COVERAGE_NOTE); Friday decision "
                 "dates; ISO dates",
        "params": {"warmup_weeks": WARMUP_WEEKS, "test_weeks": TEST_WEEKS,
                   "embargo_weeks": EMBARGO_WEEKS, "n_fridays": len(fridays),
                   "first_friday": fridays[0].date().isoformat(),
                   "last_friday": fridays[-1].date().isoformat()},
        "n_folds": len(folds),
        "folds": folds,
    }
    with open(FOLD_GRID_PATH, "w", encoding="utf-8") as fh:
        json.dump(fold_doc, fh, indent=1, sort_keys=False)
        fh.write("\n")

    # ---- census ------------------------------------------------------------
    t0 = time.time()
    cen = census(tl, fridays, folds)
    t_census = time.time() - t0

    # ---- rho battery -------------------------------------------------------
    t0 = time.time()
    panels, d1prov = load_d1_panels()
    rho = rho_battery(tl, panels, d1prov)
    t_rho = time.time() - t0

    # ---- assemble report ----------------------------------------------------
    notes = [
        "V2 consumes THURSDAY's VIX close at a Friday decision (design "
        "draft §3.4 uniform T−1 buffer + PIT_DOSSIER G-PIT-V2 application "
        "sentence); the bare available_at formula (d 16:15 ET) would also "
        "admit the Friday close — interpretation documented in "
        "state_engine.py, conservative direction (costs staleness, never "
        "lookahead).",
        "Percentile convention: weak/inclusive rank over the trailing 252 "
        "usable observations INCLUDING the current one (documented in "
        "state_engine.py); a constant series ranks p100 — an intentional "
        "property, irrelevant on real data.",
        "Episode merge is an episode-accounting convention only: it assigns "
        "shared episode_ids to same-state runs separated by <4 weekly "
        "observations and never rewrites weekly effective_state values "
        "(fabricating state during intervening weeks would violate the "
        "fail-closed ABSTAIN law).",
        "ABSTAIN bypasses min-dwell (effective immediately): holding a "
        "prior tradeable state through a stale week would be carrying "
        "state forward — forbidden by the frozen contract.",
        "ages_days['v2'] is business days (Mon–Fri, holidays counted — "
        "conservative); v1/v3 are calendar days; each var is reported in "
        "the unit its own staleness law uses.",
        "D1 tape observables (RV/ATR/drawdown) are sampled at the last "
        "COMPLETED D1 bar before each Friday 17:00 ET decision (= "
        "Thursday's bar) — same T−1 discipline as the engine.",
        "USDCAD/AUDUSD D1 close comes from the sparse ANC H1 panels "
        "(tradable-filtered; bid_h/bid_l are ancestor-convention minute-"
        "close aggregates per COVERAGE_NOTE) — closes exact, H/L not used.",
        "XAUUSD/XAGUSD/BRENT/WTI/NATGAS tapes are not in this data plane "
        "(L1 scope): the drawdown-hysteresis battery covers the 5 FX "
        "symbols only, disclosed.",
        "Floors are the dispatch-frozen weekly adaptation of the PSV1 "
        "triplet; F3 >= 26 state-true weeks per 26-week fold requires "
        "full-fold occupancy — structurally brutal by design; margins are "
        "reported, never relaxed post-hoc.",
    ]
    payload = {
        "schema": "pr12a100k_state_battery@1",
        "cycle": "PORTFOLIO-ROUTER-12ASSETS-100K-V1",
        "lane": "I1b_state_engine",
        "engine": "research/pr12a100k/state_engine.py",
        "panel": {
            "sources": {k: {"path": v["path"], "sha256": v["sha256"],
                            "n_obs": v["n_obs"], "first": v["first_date"],
                            "last": v["last_date"]}
                        for k, v in panel.sources.items()},
            "epoch_first_computable_friday":
                panel.epoch_ts().isoformat() if panel.epoch_ts() else None,
        },
        "calendar": {"first_friday": fridays[0].date().isoformat(),
                     "last_friday": fridays[-1].date().isoformat(),
                     "n_fridays": len(fridays),
                     "basis": "5-pair intersection Mon-aligned weeks "
                              "(COVERAGE_NOTE data_manifest_fx)"},
        "state_census": cen,
        "fold_grid": {"n_folds": len(folds),
                      "params": fold_doc["params"],
                      "folds": folds,
                      "saved_to": FOLD_GRID_PATH},
        "rho_battery": rho,
        "d1_panels": d1prov,
        "determinism": {"timeline_double_run_identical": bool(det_ok),
                        "timeline_csv_sha256": tl_sha},
        "notes_disclosures": notes,
    }
    provenance = {
        "command": "{} {}".format(
            os.path.abspath(sys.executable),
            " ".join([os.path.abspath(__file__)] + sys.argv[1:])),
        "cwd": os.getcwd(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                          time.gmtime()),
        "runtimes_s": {"build_macro_panel": round(t_panel, 2),
                       "state_timeline_x2": round(t_tl, 2),
                       "census": round(t_census, 2),
                       "rho_battery_incl_d1_loads": round(t_rho, 2),
                       "total": None},
    }
    provenance["runtimes_s"]["total"] = round(time.time() - t_start, 2)
    payload_sha = _sha256_bytes(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())
    report = dict(payload)
    report["payload_sha256"] = payload_sha
    report["provenance"] = provenance

    with open(REPORT_JSON, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1, sort_keys=False)
        fh.write("\n")
    write_markdown(report, REPORT_MD)

    # console summary
    print("state battery done in {:.1f}s".format(provenance["runtimes_s"]["total"]))
    print("timeline deterministic:", det_ok, "sha256", tl_sha[:12])
    print("fold grid:", len(folds), "folds ->", FOLD_GRID_PATH)
    for st in se.STATES:
        s = cen["states"][st]
        print("  {:12s} eps={:3d} occ={:3d} verdict={}".format(
            st, s["n_merged_episodes"], s["occupancy_weeks"], s["verdict"]))
    print("payload_sha256", payload_sha)
    print("report:", REPORT_JSON)


if __name__ == "__main__":
    main()
