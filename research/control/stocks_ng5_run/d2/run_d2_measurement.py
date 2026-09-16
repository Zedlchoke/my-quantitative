"""STOCKS-NG5 D2 measurement (non-scored) — plans/PLAN_stocks_ng5.md §7.

Implements EXACTLY the frozen pre-rho formula pin
(d2_pre_rho_formula_pin.json, schema @2, self_hash 88851364..., PIN-R1
difference form for log-spreads).  Measures the frozen shadow inventory
v2 against the anchor on the frozen weekly grid.  NO candidate returns,
PnL, PF, Sharpe, drawdown or survivor anywhere in this run.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import sys
import time

import numpy as np
import pandas as pd

WT = pathlib.Path("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-ng5/integration")
CTL = WT / "research/control/stocks_ng5_run"
BAR = 0.20


def log(m):
    print(f"[d2] {m}", flush=True)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    t0 = time.time()
    M = load_module(CTL / "m0/m0_contract.py", "m0_contract")

    # verify the pin is the committed one (hash convention: self_hash key
    # PRESENT with an empty value, matching the writers)
    pin = json.loads((CTL / "d2/d2_pre_rho_formula_pin.json").read_text())
    copy = dict(pin)
    claimed = copy["self_hash"]
    copy["self_hash"] = ""
    blob = json.dumps(copy, indent=1, sort_keys=True).encode()
    assert hashlib.sha256(blob).hexdigest() == claimed, "PIN self_hash mismatch"
    assert pin["schema"] == "stocks_ng5_d2_pre_rho_formula_pin@2", "pin schema"
    log(f"pin verified: {pin['schema']} self_hash {claimed[:12]}")

    # ---- load staged daily series (sha-pinned at P0) ----
    daily = {}
    for sym in ("QQQ", "SPY", "QQEW", "RSP"):
        rows = json.loads((CTL / f"p0/staging/{sym}_full.json").read_text())
        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").set_index("date")
        daily[sym] = df
    qqq_logret = np.log(daily["QQQ"]["adjusted_close"]).diff()
    spy_logret = np.log(daily["SPY"]["adjusted_close"]).diff()

    # ---- weekly observations (pin grid) ----
    all_dates = sorted(set().union(*[set(daily[s].index) for s in daily]))
    s = pd.Series(1, index=pd.DatetimeIndex(all_dates))
    week_key = pd.Series(s.index.isocalendar()[["year", "week"]].apply(tuple, axis=1), index=s.index)
    obs_rows = []
    skipped_weeks = []
    for wk, grp in s.groupby(week_key):
        last_date = grp.index.max()
        vals = {}
        ok = True
        for sym in ("QQQ", "SPY", "QQEW", "RSP"):
            if last_date in daily[sym].index:
                vals[sym] = daily[sym].loc[last_date]
            else:
                ok = False
                break
        if ok:
            obs_rows.append({
                "date": last_date,
                "qqq": float(vals["QQQ"]["adjusted_close"]), "spy": float(vals["SPY"]["adjusted_close"]),
                "qqew": float(vals["QQEW"]["adjusted_close"]), "rsp": float(vals["RSP"]["adjusted_close"]),
                "qqq_p": float(vals["QQQ"]["close"]), "spy_p": float(vals["SPY"]["close"]),
                "qqew_p": float(vals["QQEW"]["close"]), "rsp_p": float(vals["RSP"]["close"]),
                "qqq_vol": float(vals["QQQ"]["volume"]),
            })
        else:
            skipped_weeks.append(str(last_date.date()))
    obs = pd.DataFrame(obs_rows).set_index("date").sort_index()
    obs = obs[obs.index >= pd.Timestamp("2006-04-28")]  # frozen grid start
    log(f"weekly observations: {len(obs)} (skipped weeks: {skipped_weeks})")

    # ---- daily features sampled to the observation dates (ffill) ----
    d = obs.index
    px = daily["QQQ"]["adjusted_close"]
    feat = {}
    feat["qqq_63d"] = px / px.shift(63) - 1
    feat["qqq_252d"] = px / px.shift(252) - 1
    feat["qqq_vol21"] = qqq_logret.rolling(21).std(ddof=0)
    feat["qqq_vol252"] = qqq_logret.rolling(252).std(ddof=0)
    dv = daily["QQQ"]["adjusted_close"] * daily["QQQ"]["volume"]
    feat["qqq_dv63"] = dv.rolling(63).median()
    cov63 = qqq_logret.rolling(63).cov(spy_logret)
    var63 = spy_logret.rolling(63).var(ddof=1)
    feat["qqq_beta63"] = cov63 / var63
    F = pd.DataFrame({k: v.reindex(d, method="ffill") for k, v in feat.items()})

    # ---- weekly series ----
    spread_adj = np.log(obs["qqew"] / obs["qqq"]) + np.log(obs["rsp"] / obs["spy"])
    spread_p = np.log(obs["qqew_p"] / obs["qqq_p"]) + np.log(obs["rsp_p"] / obs["spy_p"])
    dist_only = spread_adj - spread_p
    relmom = np.log(obs["qqq"] / obs["spy"])
    qqq_ret13w = obs["qqq"] / obs["qqq"].shift(13) - 1
    qqq_ret52w = obs["qqq"] / obs["qqq"].shift(52) - 1

    # macro AX2 as-of (+1 conservative day)
    def macro_weekly(series_id):
        rows = json.loads((CTL / f"p0/staging/FRED_{series_id}.json").read_text())["observations"]
        md = pd.to_datetime([r["date"] for r in rows])
        mv = pd.to_numeric([r["value"] for r in rows], errors="coerce")
        ms = pd.Series(mv, index=md).dropna()
        avail = ms.index + pd.Timedelta(days=1)
        return ms.reindex(avail).reindex(d, method="ffill")

    dgs10 = macro_weekly("DGS10")
    dfii10 = macro_weekly("DFII10")

    def z104(x: pd.Series) -> pd.Series:
        mu = x.rolling(104, min_periods=104).mean()
        sd = x.rolling(104, min_periods=104).std(ddof=0)
        return (x - mu) / sd

    # ---- anchor ----
    anchor_sig = z104(spread_adj - spread_adj.shift(13))
    anchor_w = np.sign(anchor_sig)

    # ---- shadows per pin ----
    sh = {}
    sh["SH-A1-RELMOM-13W"] = (z104(relmom - relmom.shift(13)), None)
    sh["SH-A1b-RELMOM-52W"] = (z104(relmom - relmom.shift(52)), None)
    sh["SH-A2-ABSMOM-63D"] = (z104(F["qqq_63d"]), None)
    sh["SH-A2b-ABSMOM-252D"] = (z104(F["qqq_252d"]), None)
    sh["SH-A3-VOLLEVEL-21S"] = (z104(F["qqq_vol21"]), None)
    sh["SH-A3b-VOLLEVEL-52W"] = (z104(F["qqq_vol252"]), None)
    sh["SH-A4-DOLLARVOL"] = (z104(F["qqq_dv63"]), None)
    dow = pd.Series(d.isocalendar()["day"].astype(float), index=d)
    sh["SH-A5-DOW"] = (dow, np.sign(dow - 3.0))  # pin: weights = sign(signal-3)
    parity = pd.Series(np.where(d.isocalendar()["week"] % 2 == 1, 1.0, -1.0), index=d)
    sh["SH-A5b-WEEKPARITY"] = (parity, parity.copy())

    def month_end_dist(t: pd.Timestamp) -> float:
        cur = t + pd.offsets.MonthEnd(0)
        prev = t - pd.offsets.MonthEnd(1)
        d_cur = (cur - t).days
        d_prev = (t - prev).days
        return float(d_cur if d_cur <= d_prev else -d_prev)

    month_end = pd.Series([month_end_dist(pd.Timestamp(t)) for t in d], index=d, dtype=float)
    sh["SH-A5c-MONTHEND"] = (month_end, np.sign(month_end))
    sh["SH-A6-QQQHEAT"] = (z104(qqq_ret13w), np.sign(qqq_ret13w))
    sh["SH-A7a-ROLLBETA-63S"] = (z104(F["qqq_beta63"]), None)
    sh["SH-A8a-DFII10-SHOCK-13W"] = (z104(dfii10 - dfii10.shift(13)), None)
    sh["SH-A8b-DGS10-LEVEL-13W"] = (z104(dgs10), None)
    sh["SH-A9-DIV-DECOMP"] = (  # two sub-shadows
        (z104(spread_p - spread_p.shift(13)), z104(dist_only - dist_only.shift(13))), None)
    sh["SH-A9b-TRENDDEF-GEOM"] = (z104(qqq_ret52w), np.sign(qqq_ret52w))

    valid_anchor = anchor_sig.dropna().index

    results = []
    veto = []
    for sid, (sig, w_override) in sh.items():
        subs = [(f"{sid}", sig, w_override)] if not isinstance(sig, tuple) else [
            (f"{sid}-PRICEONLY", sig[0], None), (f"{sid}-DISTONLY", sig[1], None)]
        for name, s_sig, w_override2 in subs:
            if sid == "SH-A10-MNQ-CAUSAL-TEMPLATE":
                continue
            valid = valid_anchor.intersection(s_sig.dropna().index)
            if len(valid) < 60:
                results.append({"shadow": name, "pooled_abs_rho": None, "verdict": "UNMEASURABLE_INSUFFICIENT_OVERLAP",
                                "overlap": int(len(valid))})
                veto.append(name)
                continue
            a_sig = anchor_sig.loc[valid]
            s2 = s_sig.loc[valid]
            w_a = anchor_w.loc[valid]
            w_s = np.sign(s2) if w_override2 is None else w_override2.loc[valid]
            m = M.primary_comparisons(np.asarray(w_a, float), np.asarray(w_s, float),
                                      np.asarray(a_sig, float), np.asarray(s2, float))
            pooled = M.pooled_abs_correlation(m)
            margin = BAR - pooled
            row = {"shadow": name, "overlap_obs": int(len(valid)), "pooled_abs_rho": round(pooled, 6),
                   "weight_pearson": round(m["target_weight_pearson"], 6),
                   "weight_spearman": round(m["target_weight_spearman"], 6),
                   "signal_rank_spearman": round(m["signal_rank_correlation"], 6),
                   "margin_to_bar": round(margin, 6),
                   "verdict": "CLEAN" if pooled <= BAR else "ANCESTRY_VETO"}
            results.append(row)
            if pooled > BAR:
                veto.append(name)
            log(f"{name}: pooled={pooled:.4f} margin={margin:+.4f} n={len(valid)} "
                f"{'VETO' if pooled > BAR else 'clean'}")

    # ---- feasibility (non-scored) ----
    folds = json.loads((CTL / "p0/fold_freeze.json").read_text())["folds"]
    decisions = anchor_sig.dropna().index
    fold_counts = {f["id"]: int(((decisions >= pd.Timestamp(f["start"])) & (decisions <= pd.Timestamp(f["end"]))).sum())
                   for f in folds}
    def turnover(sig, lag):
        w = np.sign(z104(spread_adj - spread_adj.shift(lag))).dropna()
        return float((w.values[1:] != w.values[:-1]).mean())
    turn = {"anchor_L13": turnover(None, 13), "arm_L4": turnover(None, 4), "arm_L52": turnover(None, 52)}
    ceiling = {"band_bps": 10, "fills_per_rotation": 2, "rotations_per_year": 52,
               "base_bps_per_year": 1040, "stress_tier": 2.0, "stress_bps_per_year": 2080,
               "law": "pre-registered plan F6; never re-derived (P-21/P-15)"}

    verdict = "D2_VETO_ALL" if veto else "D2_PASS"
    out = {
        "schema": "stocks_ng5_d2_measurement_verdict@1",
        "cycle_id": "STOCKS-NG5",
        "measured_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": round(time.time() - t0, 1),
        "pin": {"schema": pin["schema"], "self_hash": claimed},
        "m0_contract_sha256": hashlib.sha256((CTL / "m0/m0_contract.py").read_bytes()).hexdigest(),
        "grid": {"observations": int(len(obs)), "skipped_weeks": skipped_weeks,
                 "anchor_decisions": int(len(decisions)), "fold_decisions": fold_counts},
        "turnover_fraction": turn,
        "cost_ceiling": ceiling,
        "shadow_measurements": results,
        "vetoed_shadows": veto,
        "template_rule": "SH-A10-MNQ-CAUSAL-TEMPLATE: no index-level causal rescue; carried as binding rule",
        "no_returns_computed": True,
        "verdict": verdict,
        "law": "VETO => selection empty, no scored cell, cycle closes 0/3 (terminal path); PASS => S/I/Z/A7 prelaunch, stop before owner GO",
    }
    (CTL / "d2/d2_measurement_verdict.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    log(f"VERDICT: {verdict} (vetoed: {veto if veto else 'none'})")
    return 0 if veto == [] else 2  # exit 2 = veto (a valid research outcome)


if __name__ == "__main__":
    raise SystemExit(main())
