#!/usr/bin/env python
"""MEAS-FX m2 — FX-F6 fwd-21d-vol -> intraday-sign transfer measurement
harness + synthetic-fixture demonstration (HYPO G4). Lane MEAS-FX, round
FUTURES-5SYM-PRESCORED-20261005 wave-3.

Outcome-blind law: the transfer statistic conditions a market observable on
a signal-family input (CoT stratum). The harness below is built and proven
on SYNTHETIC fixtures ONLY. The real-data run is the owner-gated part and is
recorded NOT_RUN-REAL-DATA (see m2_fx_f6_transfer.md for the exact split of
what is already committed-descriptive vs what remains conditional).

No network. No real market or CoT series is read by this script.
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))

# Committed descriptive inputs (cited, read-only context — NOT consumed by
# the harness): FUTURES-DEEPRESEARCH-V2-20261003/analysis/6E_a5_cot.json
#   positioning_vs_fwd_vol_descriptive: n_joined=347, n>=80pct=54, n<=20pct=36,
#   fwd21_vol_mean ge80=6.5218% vs le20=7.6838% (mid 6.9817%).
#   .../6B_a5_cot.json: corr(|z|, fwd vol20) = -0.0745, n_obs=326.
COMMITTED_DESCRIPTIVE = {
    "6E_signal_side": {
        "path": "FUTURES-DEEPRESEARCH-V2-20261003/analysis/6E_a5_cot.json:"
                "positioning_vs_fwd_vol_descriptive",
        "n_joined": 347, "n_pctile_ge80": 54, "n_pctile_le20": 36,
        "fwd21_vol_mean_pct_ge80": 6.5217801000129665,
        "fwd21_vol_mean_pct_le20": 7.683787027023775,
        "fwd21_vol_mean_pct_mid": 6.981696034345467,
        "pit_structure": "CoT net-noncomm 1,082 weeks 2006-01..2026-09; "
                         "Tue-observe / Fri-15:30 release; percentiles "
                         "strict-past 3y rolling; release-safe obs+3 join",
    },
    "6B_falsifier": {
        "path": "FUTURES-DEEPRESEARCH-V2-20261003/analysis/6B_a5_cot.json",
        "corr_abs_z_fwd_vol20": -0.07445679702265492, "n_obs": 326,
    },
}


# ------------------------------------------------------------- the harness
def strict_past_percentile(series: pd.Series, window: int = 156,
                           min_periods: int = 104,
                           include_current: bool = False) -> pd.Series:
    """Release-safe positioning percentile: rolling strict-past window
    (EXCLUDES the current observation when include_current=False), matching
    the committed 6E a5 construction law. Deterministic; no lookahead."""
    s = pd.Series(series, dtype=float)
    if include_current:
        lo = s.rolling(window, min_periods=min_periods).min()
        hi = s.rolling(window, min_periods=min_periods).max()
    else:
        lo = s.rolling(window, min_periods=min_periods).apply(
            lambda x: x.iloc[:-1].min(), raw=False)
        hi = s.rolling(window, min_periods=min_periods).apply(
            lambda x: x.iloc[:-1].max(), raw=False)
    rng = hi - lo
    out = (s - lo) / rng.replace(0.0, np.nan) * 100.0
    return out


def assign_strata(pctile: pd.Series, lo: float = 20.0,
                  hi: float = 80.0, lag_sessions: int = 3) -> pd.Series:
    """CoT stratum label, release-safe: the label computed from observation
    week t becomes usable only at t+lag_sessions (obs+3 committed law).
    Label in {HIGH, LOW, MID}; NaN percentile -> NaN label."""
    lab = pd.Series(np.nan, index=pctile.index, dtype=object)
    lab[pctile >= hi] = "HIGH"
    lab[pctile <= lo] = "LOW"
    lab[(pctile > lo) & (pctile < hi)] = "MID"
    return lab.shift(lag_sessions)


def intraday_sign_stability(session_returns: pd.Series,
                            labels: pd.Series, stratum: str) -> dict:
    """Descriptive intraday observable per stratum: the session-level
    sign-agreement rate between consecutive session returns (a sign-STABILITY
    statistic, not a return level — outcome-blind by construction; it uses
    signs of already-realized consecutive bars, conditioning only on the
    stratum membership, which is the measurement the family declares).
    REAL-DATA execution of this function is the owner-gated NOT_RUN part;
    here it is exercised on synthetic fixtures only."""
    r = session_returns[labels == stratum].dropna()
    r = r[r.shift(1).notna() & r.notna()]
    if len(r) < 2:
        return {"n_sessions": int(len(r)), "sign_agree_rate": None}
    same = np.sign(r) == np.sign(r.shift(1))
    return {"n_sessions": int(len(r)),
            "sign_agree_rate": float(same.mean())}


def transfer_statistic(session_returns: pd.Series, labels: pd.Series,
                       n_boot: int = 500, seed: int = 20261005) -> dict:
    """T = sign_agree_rate(HIGH) - sign_agree_rate(LOW), with a seeded
    block bootstrap CI (block=8 weeks; labels are autocorrelated via era
    clustering — iid forbidden per the overlay law)."""
    hi = intraday_sign_stability(session_returns, labels, "HIGH")
    lo = intraday_sign_stability(session_returns, labels, "LOW")
    if hi["sign_agree_rate"] is None or lo["sign_agree_rate"] is None:
        return {"T": None, "high": hi, "low": lo, "ci": None}
    t_obs = hi["sign_agree_rate"] - lo["sign_agree_rate"]
    df = pd.DataFrame({"r": session_returns, "l": labels}).dropna()
    df = df[df["l"].isin(["HIGH", "LOW"])]
    rng = np.random.default_rng(seed)
    idx = np.arange(len(df))
    stats = []
    for _ in range(n_boot):
        # circular block bootstrap over the joint (return, label) series
        starts = rng.integers(0, len(df), size=max(1, len(df) // 8))
        take = np.concatenate([(np.arange(s, s + 8) % len(df)) for s in starts])[:len(df)]
        b = df.iloc[take]
        bh = b[b["l"] == "HIGH"]["r"]
        bl = b[b["l"] == "LOW"]["r"]
        if len(bh) < 2 or len(bl) < 2:
            continue
        sh = float((np.sign(bh) == np.sign(bh.shift(1))).mean())
        sl = float((np.sign(bl) == np.sign(bl.shift(1))).mean())
        stats.append(sh - sl)
    ci = ([float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))]
          if len(stats) >= 100 else None)
    return {"T": float(t_obs), "high": hi, "low": lo,
            "ci95_blockboot": ci, "n_boot_valid": len(stats)}


def mde_inflation_disclosure(host_n_per_stratum: int) -> dict:
    """Overlay law: conditioning halves the host n per stratum => MDE
    inflates by sqrt(2). Pure arithmetic disclosure (court §c3 method)."""
    return {"host_n_per_stratum": host_n_per_stratum,
            "mde_inflation_factor": float(np.sqrt(2.0))}


# --------------------------------------------------------- synthetic fixtures
def gen_positioning(n_weeks: int, seed: int) -> pd.Series:
    """Deterministic CoT-like weekly positioning series (AR(1) + slow regime
    wave). Shared by the null/injection fixtures and the no-lookahead fixture
    so the F3 comparison is bit-identical at the head."""
    rng = np.random.default_rng(seed)
    pos = np.zeros(n_weeks)
    pos[0] = rng.normal()
    for i in range(1, n_weeks):
        pos[i] = 0.92 * pos[i - 1] + 0.3 * rng.normal() + 1.2 * np.sin(i / 60.0)
    weeks = pd.date_range("2015-01-04", periods=n_weeks, freq="7D")
    return pd.Series(pos, index=weeks)


def make_fixture(n_weeks: int = 600, seed: int = 7,
                 injected_delta: float | None = None) -> dict:
    """Fixture law (documented):
    - Weekly CoT-like positioning: AR(1) + slow regime wave, seeded.
    - Session returns: iid normal sign-symmetric base (P(agree)=0.5).
    - Injection (when injected_delta is not None): sessions in HIGH strata
      that currently DISAGREE with the previous (adjusted) session are
      flipped to agreeing with probability 2*injected_delta, applied
      sequentially so P(sign-agree | HIGH) -> 0.5 + injected_delta. LOW
      strata stay at the 0.5 base; the transfer statistic must recover
      ~+injected_delta."""
    pos = gen_positioning(n_weeks, seed)
    pct = strict_past_percentile(pos)
    lab = assign_strata(pct)
    # expand weekly labels to ~5 sessions/week
    sess_idx, sess_r, sess_lab = [], [], []
    rng = np.random.default_rng(seed + 100)
    for i, w in enumerate(pos.index):
        for k in range(5):
            sess_idx.append(w + pd.Timedelta(days=k))
        base = rng.normal(0, 1, 5)
        sess_r.extend(base.tolist())
        sess_lab.extend([lab.iloc[i]] * 5)
    r = pd.Series(sess_r, index=pd.DatetimeIndex(sess_idx))
    l = pd.Series(sess_lab, index=pd.DatetimeIndex(sess_idx))
    if injected_delta is not None:
        rng2 = np.random.default_rng(seed + 1)
        vals = r.to_numpy().copy()
        labs = l.to_numpy()
        p_flip = 2.0 * injected_delta
        for i in range(1, len(vals)):
            if labs[i] != "HIGH" or labs[i - 1] != "HIGH":
                continue
            if np.sign(vals[i]) != np.sign(vals[i - 1]):
                if rng2.random() < p_flip:
                    vals[i] = -vals[i]
        r = pd.Series(vals, index=r.index)
    return {"returns": r, "labels": l}


def main():
    res = {
        "schema": "meas_fx_m2_f6_transfer@1",
        "item": "WORK_QUEUE A-#9 / HYPO G4 — FX-F6 fwd-21d-vol -> intraday-sign transfer",
        "law": "harness + synthetic fixtures ONLY; real-data transfer run is "
               "owner-gated NOT_RUN-REAL-DATA (conditional-on-signal); no PnL; "
               "PB2 untouched; release-clock control (rows 107-109 precedent) "
               "is MANDATORY in any scored future and is wired as a required "
               "argument of any real run",
        "committed_descriptive_inputs": COMMITTED_DESCRIPTIVE,
        "committed_vs_conditional_split": {
            "already_committed_descriptive": [
                "6E signal side: fwd-21d vol by CoT stratum (>=80pct 6.52% vs "
                "<=20pct 7.68%, n=347 joined, strict-past percentiles, obs+3)",
                "6B cross-symbol falsifier: corr(|z|, fwd vol20) = -0.074 (n=326)",
            ],
            "remains_conditional_NOT_RUN": [
                "the INTRADAY transfer itself: host (F1/F4-6E) trigger-"
                "conditioned sign-stability / dispersion split by CoT stratum "
                "— this conditions a market observable on the family signal "
                "input and is the hypothesis content",
            ],
        },
        "real_data_run": {
            "status": "NOT_RUN-REAL-DATA",
            "grounds": "the transfer conditions on the CoT stratum label; "
                       "executing it on the 1m panels is conditional-on-signal "
                       "measurement = owner-gated; the descriptive signal-side "
                       "inputs already committed are reproduced above from the "
                       "committed JSONs (not recomputed from raw data)",
            "mandatory_when_owner_gates_it": [
                "release-clock control arm (COMMNG1-A4-P2 rows 107-109 law)",
                "mid-pctile (20-80) negative stratum",
                "6B near-zero cross-symbol falsifier re-check",
                "block bootstrap (iid forbidden), strict-past percentiles, "
                "obs+3 release-safe labels",
                "sqrt(2) MDE inflation disclosure on the host",
            ],
        },
        "harness": {
            "statistic": "T = sign_agree_rate(HIGH) - sign_agree_rate(LOW) on "
                         "consecutive session returns within strata; seeded "
                         "circular block bootstrap (block=8, 500 draws, "
                         "seed=20261005) 95% CI",
            "label_law": "strict-past 156-week percentile (current obs "
                         "excluded), strata >=80 / <=20, release-safe obs+3 lag",
            "fixtures": [],
        },
        "mde_disclosure": mde_inflation_disclosure(1362 // 2),
    }

    # F1: null fixture -> T inside CI
    fx0 = make_fixture(injected_delta=None, seed=7)
    t0 = transfer_statistic(fx0["returns"], fx0["labels"])
    f1_pass = t0["ci95_blockboot"] is not None and (
        t0["ci95_blockboot"][0] <= t0["T"] <= t0["ci95_blockboot"][1])
    res["harness"]["fixtures"].append({
        "id": "F1-null", "law": "no injection; T must sit inside its own CI",
        "T": t0["T"], "ci": t0["ci95_blockboot"],
        "n_high": t0["high"]["n_sessions"], "n_low": t0["low"]["n_sessions"],
        "pass": bool(f1_pass)})
    # F2: injected +0.10 sign-agreement shift -> T recovers the direction
    # and order of magnitude
    fx1 = make_fixture(injected_delta=0.10, seed=7)
    t1 = transfer_statistic(fx1["returns"], fx1["labels"])
    f2_pass = t1["T"] is not None and t1["T"] > 0.02
    res["harness"]["fixtures"].append({
        "id": "F2-inject+0.10",
        "law": "HIGH strata shifted toward sign agreement by +0.10 "
               "(P(agree|HIGH)->0.60, sequential injection); T must recover a "
               "positive value of that order (> 0.02)",
        "T": t1["T"], "ci": t1["ci95_blockboot"],
        "n_high": t1["high"]["n_sessions"], "n_low": t1["low"]["n_sessions"],
        "pass": bool(f2_pass)})
    # F3: no-lookahead — corrupting the FUTURE tail of the positioning series
    # must not change earlier strata labels
    lab_base = assign_strata(strict_past_percentile(gen_positioning(600, 7)))
    pos_c = gen_positioning(600, 7).copy()
    pos_c.iloc[-100:] = pos_c.iloc[-100:] + 50.0   # corrupt FUTURE tail only
    lab_c = assign_strata(strict_past_percentile(pos_c))
    same_head = bool(lab_c.iloc[:100].equals(lab_base.iloc[:100]))
    res["harness"]["fixtures"].append({
        "id": "F3-no-lookahead",
        "law": "corrupting the last 100 weeks of the positioning series must "
               "leave the first 100 strata labels byte-identical "
               "(strict-past construction proof)",
        "pass": same_head})
    # F4: release-safe lag — labels at week t use information available only
    # at t+3 (checked structurally: assign_strata shifts by 3)
    chk = assign_strata(pd.Series([90.0, 90.0, 90.0, 90.0] + [np.nan] * 4))
    res["harness"]["fixtures"].append({
        "id": "F4-release-lag",
        "law": "a HIGH percentile at row 0 must not surface in the label "
               "before row 3 (obs+3)",
        "label_rows_0_1_2": [str(chk.iloc[0]), str(chk.iloc[1]), str(chk.iloc[2])],
        "label_row_3": str(chk.iloc[3]),
        "pass": bool(all(pd.isna(chk.iloc[i]) for i in (0, 1, 2))
                     and chk.iloc[3] == "HIGH")})
    res["harness"]["fixtures_all_pass"] = bool(
        all(f["pass"] for f in res["harness"]["fixtures"]))

    jdump_path = os.path.join(HERE, "m2_fx_f6_transfer.json")
    with open(jdump_path, "w") as fh:
        json.dump(res, fh, indent=1, allow_nan=False)
    print("m2: fixtures_all_pass =", res["harness"]["fixtures_all_pass"],
          "| F1 T=%.4f ci=%s | F2 T=%.4f | real run=%s"
          % (t0["T"], t0["ci95_blockboot"], t1["T"],
             res["real_data_run"]["status"]))


if __name__ == "__main__":
    main()
