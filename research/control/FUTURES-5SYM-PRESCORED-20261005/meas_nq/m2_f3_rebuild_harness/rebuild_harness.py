#!/usr/bin/env python
"""NQ-F3 full-era rebuild HARNESS (LANE-MEAS-NQ, wave 3) — code + synthetic checks.

THIS IS THE HARNESS, NOT THE REAL RUN. The real-data rebuild is gated:
the harness HARD-REFUSES real cache_v3 inputs while ADOPT-D9 is unsigned
(exit 20, REFUSAL artifact with FINAL status). ADOPT-D9 status as of this
lane: UNSIGNED (D8_D9_DECISION_SHEET.md, FUTURES-SIX-ADOPT-PREP-20261004)
=> cache_v3 is canonical-CANDIDATE and the F3 rebuild's real-data execution
is NOT_RUN. Only --synthetic executions run in this wave.

Pipeline (mirrors the committed k6gate method, nq_f3_rebuild_a1a2.json,
recipes from NQ_a1_regimes.py / NQ_a2_sessions.py):
  chain reconstruction inputs -> NaN-aware per-session ret series ->
  a1 aggregate tables (rvol_{5,10,20,60,120,252}d, vol clustering,
  trend persistence, drawdowns >=10%, yearly, vol-regime terciles) ->
  a2-style aggregate tables (held/clean/depleted counts, fold-sliced
  segments) -> roll set -> ret cross-check vs input column.

Laws applied:
  - Fold boundaries per SPEC_NQ.md section 6:
      F1 2010-06-06..2012-12-31, F2 2013-01-01..2017-12-31,
      F3 2018-01-01..2021-12-31, F4 2022-01-01..2026-09-30.
    Warmup = 252 held sessions excluded from SCORING at each fold head
    (descriptive slices here include all sessions; the warmup count is
    reported, never applied as a silent cut).
  - DST law: PRESERVED QUIRK — session_date labels are consumed exactly as
    carried by the input table (the cache's 35 Sunday-labeled rows flow
    through unchanged); the harness NEVER re-derives session boundaries.
  - NaN-aware chain law: rets never bridge a missing close (diff with NaN
    on either side => NaN); no synthetic jump is ever inserted.

Exit codes: 0 PASS | 2 input-drift | 10 selfcheck mismatch | 20
REFUSED_D9_UNSIGNED | 21 missing input | 30 usage.

Usage:
  python rebuild_harness.py --synthetic --outdir <dir>     # fixture run
  python rebuild_harness.py --selfcheck --outdir <dir>     # fixture + expected check
  python rebuild_harness.py --real --cache <cache_v3 dir>
        --d9-ratification <path to adopt/D9_RATIFICATION.json>
"""
import argparse
import hashlib
import json
import math
import os
import random
import sys
from datetime import date, timedelta

import numpy as np
import pandas as pd

SCHEMA = "nq_f3_rebuild_harness@1"
EXIT_OK, EXIT_DRIFT, EXIT_MISMATCH, EXIT_REFUSED, EXIT_MISSING, EXIT_USAGE = 0, 2, 10, 20, 21, 30

# SPEC_NQ.md section 6 fold law (panel coverage 2010-06-06..2026-09-30)
FOLDS = [("F1", "2010-06-06", "2012-12-31"),
         ("F2", "2013-01-01", "2017-12-31"),
         ("F3", "2018-01-01", "2021-12-31"),
         ("F4", "2022-01-01", "2026-09-30")]
WARMUP_SESSIONS = 252

# ADOPT-D9 gate: the ONLY lawful unlock is an owner-signed ratification
# artifact at exactly this schema, presented to --d9-ratification.
D9_RATIFICATION_SCHEMA = "d9_ratification@1"
D9_REQUIRED_DECISION = "ADOPT-D9-OptionA"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def jdump(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, sort_keys=True, default=str)


# --------------------------------------------------------------------------
# D9 gate
# --------------------------------------------------------------------------
def d9_gate(ratification_path):
    """Fail-closed: returns (ok, reason). Absent/ill-formed/mismatched => refuse."""
    if not ratification_path:
        return False, "no --d9-ratification supplied (ADOPT-D9 default = UNSIGNED)"
    if not os.path.exists(ratification_path):
        return False, f"ratification artifact not found: {ratification_path}"
    try:
        r = json.load(open(ratification_path))
    except Exception as e:  # noqa: BLE001
        return False, f"ratification artifact unparseable: {e}"
    if r.get("schema") != D9_RATIFICATION_SCHEMA:
        return False, f"ratification schema != {D9_RATIFICATION_SCHEMA}"
    if r.get("decision") != D9_REQUIRED_DECISION:
        return False, (f"ratification decision != {D9_REQUIRED_DECISION} "
                       f"(got {r.get('decision')!r})")
    if not r.get("signed_by") or not r.get("date"):
        return False, "ratification missing signed_by/date"
    return True, "ADOPT-D9-OptionA ratified artifact accepted"


# --------------------------------------------------------------------------
# Pipeline: NaN-aware chain -> ret series -> a1/a2 aggregates
# --------------------------------------------------------------------------
def build_ret_series(held_daily):
    """held_daily: DataFrame[d, close, rth_coverage, ...] sorted by d.
    Returns ret series (NaN-aware), cov, depleted mask."""
    d = held_daily.sort_values("d").reset_index(drop=True)
    d["log_close"] = np.log(d["close"].astype(float))  # NaN stays NaN
    d["ret"] = d["log_close"].diff()                   # NaN if either side NaN
    d["cov"] = d["rth_coverage"].clip(0, 1).fillna(0.0)
    d["depleted"] = (d["cov"] < 0.25) | d["close"].isna()
    return d


def variance_ratio(ret, q):
    var1 = ret.rolling(252, min_periods=189).var()
    varq = ret.rolling(q, min_periods=q).sum().rolling(252, min_periods=189).var()
    return varq / (q * var1)


def drawdown_episodes(dd, min_depth=0.10):
    eps, in_dd, start, trough = [], False, None, None
    for i, (dt_, v) in enumerate(dd.items()):
        if not in_dd and v < -min_depth:
            in_dd, start, trough = True, i, i
        elif in_dd:
            if v < dd.iloc[trough]:
                trough = i
            if v >= -1e-9:
                eps.append((start, trough, i))
                in_dd = False
    if in_dd:
        eps.append((start, trough, None))
    return eps


def run_pipeline(held_daily, rolls_table, inputs_manifest, note):
    """Full a1/a2 rebuild on a held-daily panel (real or synthetic)."""
    d = build_ret_series(held_daily)
    ann = 252.0
    volz = {f"rvol_{w}d": d["ret"].rolling(w, min_periods=max(2, int(w * .75))).std() * np.sqrt(ann)
            for w in (5, 10, 20, 60, 120, 252)}
    vdf = pd.DataFrame(volz)
    vol_summary = {}
    for c in vdf:
        s = vdf[c].dropna()
        if not len(s):
            vol_summary[c] = None
            continue
        vol_summary[c] = {"min": float(s.min()), "p5": float(s.quantile(.05)),
                          "p25": float(s.quantile(.25)), "median": float(s.median()),
                          "p75": float(s.quantile(.75)), "p95": float(s.quantile(.95)),
                          "max": float(s.max()),
                          "argmin_date": str(d["d"].iloc[s.idxmin()])[:10],
                          "argmax_date": str(d["d"].iloc[s.idxmax()])[:10],
                          "last": float(s.iloc[-1])}
    rv20 = vdf["rvol_20d"]
    rv60 = vdf["rvol_60d"]

    acf_abs = d["ret"].abs().rolling(252).apply(
        lambda x: np.corrcoef(x[:-1], x[1:])[0, 1], raw=True)
    acf_ret = d["ret"].rolling(252).apply(
        lambda x: np.corrcoef(x[:-1], x[1:])[0, 1], raw=True).dropna()
    vrdf = pd.DataFrame({f"vr_{q}": variance_ratio(d["ret"], q) for q in (5, 20, 60)})

    r = d["ret"].dropna()
    d["cum"] = d["log_close"] - d["log_close"].iloc[0]
    d["peak"] = d["cum"].cummax()
    d["dd"] = d["cum"] - d["peak"]
    ep_list = []
    for s_, t, e in drawdown_episodes(d["dd"], 0.10):
        ep_list.append({"start": str(d["d"].iloc[s_])[:10],
                        "trough": str(d["d"].iloc[t])[:10],
                        "end": (str(d["d"].iloc[e])[:10] if e is not None else "unrecovered"),
                        "depth_pct": float(-100 * d["dd"].iloc[t]),
                        "peak_to_trough_sessions": int(t - s_),
                        "recovery_sessions": (int(e - t) if e is not None else None),
                        "trough_is_depleted_window": bool(d["depleted"].iloc[t])})
    ep_list.sort(key=lambda x: -x["depth_pct"])

    d["year"] = pd.to_datetime(d["d"]).dt.year
    yearly = []
    for y, g in d.groupby("year"):
        rr = g["ret"].dropna()
        cum = g.set_index("d")["cum"]
        dd_y = cum - cum.cummax()
        yearly.append({"year": int(y), "n_sessions": int(len(g)),
                       "ret_pct": float(100 * g["ret"].sum()),
                       "vol_ann_pct": float(100 * rr.std() * np.sqrt(252)) if len(rr) > 2 else None,
                       "skew": float(rr.skew()) if len(rr) > 10 else None,
                       "ex_kurt": float(rr.kurt()) if len(rr) > 10 else None,
                       "up_days_pct": float(100 * (rr > 0).mean()),
                       "worst_day_pct": float(100 * rr.min()),
                       "best_day_pct": float(100 * rr.max()),
                       "max_dd_pct": float(-100 * dd_y.min()) if len(dd_y) else None,
                       "avg_daily_vol_contracts": float(g["volume"].mean()),
                       "median_true_range_pts": float(g["true_range"].median()),
                       "depleted_sessions": int(g["depleted"].sum()),
                       "med_rvol20": float((g["ret"].rolling(20, min_periods=15).std()
                                            * np.sqrt(252)).median())})

    # vol-regime terciles (756-day expanding history, min 300 obs)
    lab_vol, win = [], 756
    for i in range(len(rv60)):
        lo = max(0, i - win)
        seg = rv60.iloc[lo:i + 1].dropna()
        if len(seg) < 300:
            lab_vol.append(None)
        else:
            hist = seg.iloc[:-1]
            q1, q2 = hist.quantile(1 / 3), hist.quantile(2 / 3)
            lab_vol.append(1 if seg.iloc[-1] <= q1 else (2 if seg.iloc[-1] <= q2 else 3))
    d["regime_vol"] = lab_vol
    counts = pd.Series([x for x in lab_vol if x is not None]).value_counts()
    regime_counts = {str(int(k)): int(v) for k, v in counts.items()}

    # fold slices (SPEC_NQ section 6 fold law; descriptive, warmup reported not applied)
    fold_rows = []
    for name, lo, hi in FOLDS:
        m = (d["d"] >= lo) & (d["d"] <= hi)
        g = d[m]
        if not len(g):
            fold_rows.append({"fold": name, "window": f"{lo}..{hi}", "n_sessions": 0,
                              "warmup_sessions_excluded_from_scoring": WARMUP_SESSIONS,
                              "n_scoring_sessions_if_scored": 0})
            continue
        rr = g["ret"].dropna()
        fold_rows.append({
            "fold": name, "window": f"{lo}..{hi}", "n_sessions": int(len(g)),
            "n_nonnan_rets": int(len(rr)),
            "warmup_sessions_excluded_from_scoring": WARMUP_SESSIONS,
            "n_scoring_sessions_if_scored": max(0, int(len(g)) - WARMUP_SESSIONS),
            "vol_ann_pct": float(100 * rr.std() * np.sqrt(252)) if len(rr) > 2 else None,
            "ret_pct": float(100 * g["ret"].sum()),
            "rvol20_median_pct": float(vdf.loc[g.index, "rvol_20d"].median() * 100)
            if vdf.loc[g.index, "rvol_20d"].notna().any() else None,
            "depleted_sessions": int(g["depleted"].sum())})

    # roll set from the chain table (held contract changes)
    rt = rolls_table.sort_values("d").reset_index(drop=True)
    held_c = rt["held"].astype(str)
    switch = held_c.ne(held_c.shift())
    roll_dates = [str(x)[:10] for x in rt.loc[switch & (np.arange(len(rt)) > 0), "d"]]

    # cross-check: recomputed rets vs any provided ret column (never trusted)
    xchk = None
    if "ret" in held_daily.columns:
        provided = held_daily.sort_values("d")["ret"].astype(float).to_numpy()
        mine = d["ret"].to_numpy()
        both = ~(np.isnan(provided) & np.isnan(mine))
        diff = np.where(both, np.abs(np.nan_to_num(provided) - np.nan_to_num(mine)), 0.0)
        xchk = {"n_compared": int(both.sum()), "max_abs_ret_diff": float(diff.max()),
                "n_nan_recomputed": int(np.isnan(mine).sum()),
                "n_nan_provided": int(np.isnan(provided).sum())}

    clean = d[~d["depleted"] & (d["cov"] >= 0.6)]
    # DST preserved-quirk observable: rows whose session_date label differs from
    # the session index date are carried through UNCHANGED (never re-derived).
    if "session_date" in held_daily.columns:
        sd = held_daily.sort_values("d")["session_date"].astype(str).str.slice(0, 10)
        quirk = int((sd.to_numpy() != d["d"].astype(str).str.slice(0, 10).to_numpy()).sum())
    else:
        quirk = 0
    out = {
        "schema": SCHEMA, "note": note,
        "inputs_manifest": inputs_manifest,
        "laws": {"folds": FOLDS, "warmup_sessions": WARMUP_SESSIONS,
                 "dst_law": "PRESERVED_QUIRK (session labels consumed as carried; never re-derived)",
                 "chain_law": "NaN-aware: rets never bridge a missing close; no synthetic jump"},
        "panel": {"n_sessions": int(len(d)),
                  "first": str(d["d"].iloc[0])[:10], "last": str(d["d"].iloc[-1])[:10],
                  "n_rolls": len(roll_dates), "roll_dates": roll_dates,
                  "depleted_sessions": int(d["depleted"].sum()),
                  "clean_sessions_cov_ge_0.6": int(len(clean))},
        "a1": {"realized_vol_summary": vol_summary,
               "vol_clustering": {
                   "acf1_abs_ret_252d_median": float(acf_abs.dropna().median()),
                   "vol20_of_vol20": float(rv20.diff().abs().rolling(252).median().dropna().median())},
               "trend_persistence": {
                   "acf1_ret_full": float(r.autocorr(1)),
                   "acf1_ret_rolling252_median": float(acf_ret.median()),
                   "acf1_ret_rolling252_p10_p90": [float(x) for x in acf_ret.quantile([.1, .9])],
                   "variance_ratios_full": {k: float(v.dropna().iloc[-252:].mean())
                                            for k, v in vrdf.items()},
                   "variance_ratio_20_median": float(vrdf["vr_20"].dropna().median()),
                   "variance_ratio_20_p10_p90": [float(x) for x in vrdf["vr_20"].dropna().quantile([.1, .9])]},
               "drawdowns_ge10pct": ep_list,
               "yearly": yearly,
               "regime_vol_tercile_counts": regime_counts},
        "a2": {"held_sessions": int(len(d)),
               "clean_sessions": int(len(clean)),
               "excluded_low_coverage": int(len(d) - len(clean)),
               "fold_segments": fold_rows},
        "crosscheck_provided_ret": xchk,
        "quirk_labeled_sessions": quirk,
        "sunday_labeled_sessions": int(sum(
            1 for x in pd.to_datetime(d["d"]).dt.dayofweek if x == 6))}
    return out


# --------------------------------------------------------------------------
# Synthetic fixture generator (deterministic; law documented in fixture_law)
# --------------------------------------------------------------------------
N_SESSIONS = 1044          # 4 x 261 business-day blocks, 2017-01-02 .. 2020-12-31
START = date(2017, 1, 2)
ROLL_IDX = (300, 640, 900)          # held-contract switch session indices
HOLE_START, HOLE_LEN = 500, 10      # NaN-close hole (gap anomaly 1)
THIN_IDX = (760, 761)               # rth_coverage 0.10 depleted sessions (gap anomaly 2)
RAMP_START, RAMP_LEN, RAMP_RET = 620, 40, 0.02     # deterministic run-up: guarantees the pre-crash peak is the all-time high
CRASH_START, CRASH_LEN, CRASH_RET = 660, 30, -0.02   # known >=10% drawdown block
RECOVERY_START, RECOVERY_LEN, RECOVERY_RET = 690, 40, 0.015  # V-shape closes the episode
ERA_B_START = 700                   # era boundary (2 eras): vol x2 + volume x3 from here
BASE = 6000.0


def business_days(n):
    out, cur = [], START
    while len(out) < n:
        if cur.weekday() < 5:
            out.append(cur)
        cur += timedelta(days=1)
    return out


def gen_synthetic(outdir):
    """Deterministic synthetic held-daily + chain panels with known embedded
    rolls, hole, thin sessions, crash block, and 2 eras."""
    os.makedirs(outdir, exist_ok=True)
    rng = random.Random(20261005)
    days = business_days(N_SESSIONS)
    rows, close = [], BASE
    for i, day in enumerate(days):
        era_b = i >= ERA_B_START
        vol = 0.010 if era_b else 0.005
        if HOLE_START <= i < HOLE_START + HOLE_LEN:
            close_i, cov, vol_c = None, 0.0, 0
        else:
            if RAMP_START <= i < RAMP_START + RAMP_LEN:
                r = RAMP_RET
            elif CRASH_START <= i < CRASH_START + CRASH_LEN:
                r = CRASH_RET
            elif RECOVERY_START <= i < RECOVERY_START + RECOVERY_LEN:
                r = RECOVERY_RET
            else:
                u = rng.random()          # MT19937, fixed seed => deterministic
                r = vol * (2.0 * u - 1.0)
            close = close * (1.0 + r) if close is not None else BASE
            close_i = round(close, 2)
            cov = 0.10 if i in THIN_IDX else 0.95
            vol_c = int(300000 * (3.0 if era_b else 1.0) * (0.5 + rng.random()))
        contract = (f"NQFIX_A" if i < ROLL_IDX[0] else
                    f"NQFIX_B" if i < ROLL_IDX[1] else
                    f"NQFIX_C" if i < ROLL_IDX[2] else f"NQFIX_D")
        rows.append({"d": str(day), "session_date": str(day),
                     "contract": contract, "open": close_i, "high": close_i,
                     "low": close_i, "close": close_i, "volume": vol_c,
                     "n_bars": (0 if close_i is None else 390),
                     "rth_coverage": cov,
                     "prev_close": None, "true_range": float(vol_c) / 1e5,
                     "log_close": None, "ret": None, "cov": None, "depleted": None})
    df = pd.DataFrame(rows)
    # DST preserved-quirk row: relabel ONE session_date to its Sunday (label kept,
    # 'd' unchanged) — harness must carry the label through unchanged.
    quirk_i = ERA_B_START + 3
    qd = date.fromisoformat(df.loc[quirk_i, "d"])
    df.loc[quirk_i, "session_date"] = str(qd - timedelta(days=qd.weekday() + 1))
    # recompute the derived columns exactly as the readiness cache ships them
    lc = np.log(df["close"].astype(float))
    df["log_close"] = lc
    df["ret"] = lc.diff()
    df.loc[0, "ret"] = np.nan
    df["cov"] = df["rth_coverage"].clip(0, 1).fillna(0.0)
    df["depleted"] = (df["cov"] < 0.25) | df["close"].isna()
    chain = df[["d", "contract"]].rename(columns={"contract": "held"}).copy()
    df.to_parquet(os.path.join(outdir, "fixture_held_daily.parquet"), index=False)
    chain.to_parquet(os.path.join(outdir, "fixture_chain.parquet"), index=False)

    hole_dates = [str(days[i]) for i in range(HOLE_START, HOLE_START + HOLE_LEN)]
    ramp_dates = [str(days[i]) for i in range(RAMP_START, RAMP_START + RAMP_LEN)]
    crash_dates = [str(days[i]) for i in range(CRASH_START, CRASH_START + CRASH_LEN)]
    recovery_dates = [str(days[i]) for i in range(RECOVERY_START, RECOVERY_START + RECOVERY_LEN)]
    law = {
        "schema": "meas_nq_synthetic_fixture_law@1",
        "generator": "gen_synthetic in rebuild_harness.py; random.Random(20261005).random() only (MT19937, version-stable)",
        "n_sessions": N_SESSIONS, "start": str(START),
        "eras": [{"era": "A", "sessions": f"0..{ERA_B_START - 1}",
                  "vol_class": "daily vol 0.5%-class, volume 300k-class"},
                 {"era": "B", "sessions": f"{ERA_B_START}..{N_SESSIONS - 1}",
                  "vol_class": "daily vol 1.0%-class (x2), volume 900k-class (x3)"}],
        "embedded_rolls": {"indices": list(ROLL_IDX),
                           "dates": [str(days[i]) for i in ROLL_IDX],
                           "contracts": "NQFIX_A->B->C->D (3 switches)"},
        "gap_anomalies": [
            {"kind": "vendor-hole analog", "indices": f"{HOLE_START}..{HOLE_START + HOLE_LEN - 1}",
             "dates": hole_dates, "expected": "close NaN => rets NaN on hole and both boundaries (11 NaN rets + first-session NaN = 12); depleted +10"},
            {"kind": "low-coverage depleted", "indices": list(THIN_IDX),
             "dates": [str(days[i]) for i in THIN_IDX],
             "expected": "rth_coverage 0.10 < 0.25 => depleted, closes real"},
            {"kind": "known crash + recovery V (closed-form drawdown)",
             "ramp_indices": f"{RAMP_START}..{RAMP_START + RAMP_LEN - 1}",
             "ramp_dates": ramp_dates, "ramp_daily_ret": RAMP_RET,
             "ramp_law": "deterministic +2%/day run-up guarantees the pre-crash peak (session 659) is the all-time high — the crash episode is isolated from prior random-walk drift",
             "crash_indices": f"{CRASH_START}..{CRASH_START + CRASH_LEN - 1}",
             "crash_dates": crash_dates, "crash_daily_log_ret": CRASH_RET,
             "recovery_indices": f"{RECOVERY_START}..{RECOVERY_START + RECOVERY_LEN - 1}",
             "recovery_dates": recovery_dates, "recovery_daily_ret": RECOVERY_RET,
             "expected": ("exactly one >=10% drawdown episode with peak = crash_start-1 "
                          "(session 659), trough = crash_end (session 689), depth = "
                          "100*(1-(0.98)^30) ~ 45.45% on unrounded closes; the recovery "
                          "block (x1.015^40 ~ x1.814 vs x0.545) closes the episode, "
                          "leaving ~1.1% residual dd; later random-walk episodes, if any, "
                          "never reach the crash trough date")},
            {"kind": "DST preserved-quirk row", "index": ERA_B_START + 3,
             "expected": "session_date Sunday label carried through unchanged; 'd' unchanged"}],
        "fold_membership_note": "2017 sessions fall in F2; 2018-2020 in F3 (SPEC_NQ fold law)"}
    jdump(law, os.path.join(outdir, "fixture_law.json"))
    return outdir


# --------------------------------------------------------------------------
# Modes
# --------------------------------------------------------------------------
def write_manifest(paths):
    man = {"schema": "rebuild_input_manifest@1",
           "inputs": [{"path": p, "sha256": sha256(p),
                       "bytes": os.path.getsize(p)} for p in paths]}
    return man


def load_panel_from_manifest(manifest):
    """Re-read inputs; verify manifest hashes (input drift check)."""
    frames = []
    for item in manifest["inputs"]:
        p = item["path"]
        if not os.path.exists(p):
            raise FileNotFoundError(p)
        if sha256(p) != item["sha256"]:
            raise IOError(f"INPUT_DRIFT sha256 mismatch: {p}")
        frames.append(pd.read_parquet(p))
    held = next(f for f in frames if "rth_coverage" in f.columns)
    chain = next(f for f in frames if "held" in f.columns)
    return held, chain


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--selfcheck", action="store_true")
    ap.add_argument("--real", action="store_true")
    ap.add_argument("--cache", default=None,
                    help="real cache_v3 dir (only lawful after D9 ratification)")
    ap.add_argument("--d9-ratification", dest="d9_ratification", default=None)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--fixture-dir", default=None,
                    help="reuse an existing generated fixture (selfcheck)")
    args = ap.parse_args(argv)

    n_modes = sum(bool(x) for x in (args.synthetic, args.selfcheck, args.real))
    if n_modes != 1:
        print("exactly one of --synthetic/--selfcheck/--real required", file=sys.stderr)
        return EXIT_USAGE
    os.makedirs(args.outdir, exist_ok=True)

    # ---------------- REAL MODE: hard D9 gate ----------------
    if args.real:
        ok, reason = d9_gate(args.d9_ratification)
        if not ok:
            art = {
                "schema": "rebuild_execution_status@1",
                "mode": "real",
                "final": "REFUSED_D9_UNSIGNED",
                "refusal_code": "REFUSAL_D9_UNSIGNED",
                "reason": reason,
                "gate_law": ("rebuild_harness hard-refuses real cache_v3 inputs while "
                             "ADOPT-D9 is unsigned; cache_v3 stays canonical-CANDIDATE "
                             "(D8_D9_DECISION_SHEET.md, FUTURES-SIX-ADOPT-PREP-20261004); "
                             "unlock requires an owner-signed d9_ratification@1 artifact "
                             "with decision ADOPT-D9-OptionA presented via --d9-ratification"),
                "cache_arg": args.cache,
                "d9_ratification_arg": args.d9_ratification,
                "real_rebuild_executed": False,
                "real_rebuild_status": "NOT_RUN"}
            jdump(art, os.path.join(args.outdir, "REAL_RUN_REFUSED.json"))
            print(f"REFUSED_D9_UNSIGNED: {reason}", file=sys.stderr)
            return EXIT_REFUSED
        # (lawful path exists but is unreachable until the owner signs; the
        #  drift check + pipeline would then run — implemented for completeness)
        if not args.cache:
            print("--cache required in ratified real mode", file=sys.stderr)
            return EXIT_USAGE
        files = ["nq_held_daily_v3.parquet", "held_volume_k5_v3.parquet"]
        paths = [os.path.join(args.cache, f) for f in files]
        man = write_manifest(paths)
        try:
            held, chain = load_panel_from_manifest(man)
        except (FileNotFoundError, IOError) as e:
            print(f"INPUT_DRIFT/missing: {e}", file=sys.stderr)
            return EXIT_DRIFT
        out = run_pipeline(held, chain, man,
                           "REAL cache_v3 F3 rebuild (D9-ratified path) — descriptive")
        jdump(out, os.path.join(args.outdir, "f3_rebuild_real.json"))
        return EXIT_OK

    # ---------------- SYNTHETIC ----------------
    fdir = args.fixture_dir or os.path.join(args.outdir, "fixture")
    if not args.fixture_dir:
        gen_synthetic(fdir)
    man = write_manifest([os.path.join(fdir, "fixture_held_daily.parquet"),
                          os.path.join(fdir, "fixture_chain.parquet")])
    jdump(man, os.path.join(args.outdir, "input_manifest.json"))
    try:
        held, chain = load_panel_from_manifest(man)
    except (FileNotFoundError, IOError) as e:
        print(f"missing input: {e}", file=sys.stderr)
        return EXIT_MISSING
    out = run_pipeline(held, chain, man,
                       "SYNTHETIC fixture F3 rebuild (deterministic generator; "
                       "no real data touched) — descriptive")
    jdump(out, os.path.join(args.outdir, "f3_rebuild_synthetic.json"))
    if not args.selfcheck:
        print(f"synthetic rebuild written: {args.outdir}/f3_rebuild_synthetic.json")
        return EXIT_OK

    # ---------------- SELFCHECK: independent expected comparison ----------------
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, here)
    import expected_check  # noqa: E402  (independent implementation, pure python)
    expected = expected_check.compute_expected(fdir)
    cmpres = expected_check.compare(out, expected)
    cmpres["fixture_law"] = json.load(open(os.path.join(fdir, "fixture_law.json")))
    cmpres["final"] = "PASS_SYNTHETIC_SELFCHECK" if cmpres["all_match"] else "FAIL_SYNTHETIC_SELFCHECK"
    jdump(cmpres, os.path.join(args.outdir, "selfcheck_results.json"))
    if not cmpres["all_match"]:
        for m in cmpres["mismatches"]:
            print("MISMATCH:", m, file=sys.stderr)
        print(f"SELFCHECK FAILED: {args.outdir}/selfcheck_results.json", file=sys.stderr)
        return EXIT_MISMATCH
    print(f"SELFCHECK PASS: {len(cmpres['checks'])} checks, "
          f"{args.outdir}/selfcheck_results.json")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
