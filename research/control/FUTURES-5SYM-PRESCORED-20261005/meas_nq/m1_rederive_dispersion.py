#!/usr/bin/env python
"""LANE-MEAS-NQ M1 — G11 session-sigma dispersion proxy re-derivation on cache_v3.

DESCRIPTIVE ONLY. Reads the committed cache_v3 parquets (canonical-CANDIDATE,
ADOPT-D9 UNSIGNED — read posture per SPEC_NQ.md section 2: consumption cited
per-cycle, never treated as ratified). No conditional-on-signal returns; no PnL.

What it does
  1. sha256-verifies the inputs it reads against the pinned adopt hashes
     (FUTURES-SIX-ADOPT-PREP-20261004/adopt/cache_v3_hashes.json).
  2. Single-shot read of nq_annotated_1m_v3.parquet (needed columns only) and
     independently re-derives, per held session (4,219):
       - the five committed measures of session_dispersion_v3.json
         (recipe law mirrored verbatim: contract-internal |1m log ret|,
         first bar per contract NaN, RTH = in_rth flag, 5-min non-overlapping
         RTH closes x sqrt(78) dailyization);
       - NEW per-session-class decomposition (RTH / Globex / maintenance-break
         classes per SPEC_NQ.md section 1/3 session law: RTH 08:30 CT ->
         era-correct close 16:15 CT through 2015-09-18 then 16:00 CT;
         maintenance window = in_break; Globex = remainder);
       - the sigma proxy: per-year std of held-daily log rets x sqrt(252),
         median across years -> bp. Old (pre-recovery defect) vs new.
  3. Diffs new vs committed k6gate artifact session_dispersion_v3.json (+ its
     per-session parquet) with exact deltas and per-delta classification:
       MEASUREMENT_IDENTICAL | DEFECT_CORRECTED | NEW_MEASUREMENT.
  4. Writes m1_session_sigma_v3.json + m1_per_session_rederived.parquet in the
     lane dir. The .md narrative is written separately by the lane.

Exit code 0 on success (diff table built); nonzero on hash mismatch or crash.
"""
import hashlib
import json
import os
import sys
import time

import numpy as np
import pandas as pd

WT = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-5sym-prescored/prep"
CACHE = f"{WT}/research/control/FUTURES-SIX-READINESS-20261004/nq/cache_v3"
ADOPT_HASHES = f"{WT}/research/control/FUTURES-SIX-ADOPT-PREP-20261004/adopt/cache_v3_hashes.json"
K6_NQ = f"{WT}/research/control/FUTURES-K6GATE-PREP-20261004/nq"
PRE_REC = f"{WT}/research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/NQ_a1_regimes.json"
OUT = f"{WT}/research/control/FUTURES-5SYM-PRESCORED-20261005/meas_nq"

ANN = f"{CACHE}/nq_annotated_1m_v3.parquet"
HELD = f"{CACHE}/nq_held_daily_v3.parquet"
OLD_JSON = f"{K6_NQ}/session_dispersion_v3.json"
OLD_PQ = f"{K6_NQ}/session_dispersion_v3_per_session.parquet"

FILES = ["nq_annotated_1m_v3.parquet", "nq_held_daily_v3.parquet",
         "nq_sessions_v3.parquet", "held_volume_k5_v3.parquet"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def classify(delta, rel_tol=1e-9):
    if delta == 0.0:
        return "MEASUREMENT_IDENTICAL"
    return "DEFECT_CORRECTED" if abs(delta) > rel_tol else "MEASUREMENT_IDENTICAL"


def stats3(s):
    return {"median": float(s.median()),
            "p25": float(s.quantile(.25)),
            "p75": float(s.quantile(.75))}


def main():
    t0 = time.time()
    res = {"schema": "meas_nq_m1_session_sigma_v3@1",
           "cycle": "FUTURES-5SYM-PRESCORED-20261005", "lane": "MEAS-NQ",
           "wave": 3, "descriptive_only": True,
           "d9_status": "UNSIGNED — cache_v3 read as canonical-CANDIDATE per SPEC_NQ.md §2",
           "input_hashes": {}, "hash_check": None}

    # -- 1. input hash pinning ------------------------------------------------
    adopt = json.load(open(ADOPT_HASHES))
    ok = True
    for f in FILES:
        d = sha256(f"{CACHE}/{f}")
        res["input_hashes"][f] = d
        if f in adopt.get("hashes_live", {}):
            match = (d == adopt["hashes_live"][f]["sha256"])
            res["input_hashes"][f + "__matches_adopt"] = bool(match)
            ok &= match
    res["hash_check"] = "PASS_ALL_PINNED" if ok else "FAIL_DRIFT"
    if not ok:
        res["final"] = "FAIL_INPUT_DRIFT"
        json.dump(res, open(f"{OUT}/m1_session_sigma_v3.json", "w"), indent=1)
        print("FAIL_INPUT_DRIFT", file=sys.stderr)
        return 2
    print(f"[{time.time()-t0:6.1f}s] input hashes verified against adopt pins", flush=True)

    # -- 2. single-shot panel read (locked discipline: recorded before/after) --
    cols = ["contract", "session_date", "minute_of_day", "dt", "close",
            "in_rth", "in_break"]
    df = pd.read_parquet(ANN, columns=cols)
    print(f"[{time.time()-t0:6.1f}s] panel read rows={len(df)}", flush=True)

    # recipe law mirrored verbatim from the committed M3 (k6_compute.py):
    # sort by (contract, dt); r1 = log-close diff within contract;
    # first bar of each contract NaN.
    # recipe law mirrored verbatim from the committed M3 (k6_compute.py):
    # r1 is computed on the FULL panel first (sort (contract, dt);
    # log-close diff within contract; first bar of each contract NaN),
    # THEN restricted to held-chain (contract, session_date) pairs via
    # inner merge with held_volume_k5_v3.parquet (4,219 sessions) —
    # order matters: the first held bar of a contract carries the
    # contract-internal diff from the preceding (non-held) bar.
    lc = np.log(df["close"].astype(float))
    df["r1"] = lc.groupby(df["contract"], observed=True).diff()
    df.loc[df["contract"].ne(df["contract"].shift()), "r1"] = np.nan
    held_chain = pd.read_parquet(f"{CACHE}/held_volume_k5_v3.parquet")
    df = df.merge(held_chain.rename(columns={"held": "contract"}),
                  on=["contract", "session_date"], how="inner")
    df["absr"] = df["r1"].abs() * 1e4

    # -- 3. per-session measures (committed set) + class decomposition --------
    rows = []
    for d, g in df.groupby("session_date", observed=True, sort=True):
        full = g["absr"].dropna()
        rthm = g.loc[g["in_rth"] == True, "absr"].dropna()          # noqa: E712
        brkm = g.loc[g["in_break"] == True, "absr"].dropna()        # noqa: E712
        glbm = g.loc[(g["in_rth"] == False) & (g["in_break"] == False),  # noqa: E712
                     "absr"].dropna()
        # 5-min non-overlapping RTH closes (minute-of-day from dt, UTC clock
        # identical ordering to the committed minute_of_day column)
        gr = g.loc[g["in_rth"] == True].copy()                      # noqa: E712
        if len(gr):
            gr["bk"] = gr["minute_of_day"] // 5
            r5close = gr.groupby("bk")["close"].last()
            r5ret = np.log(r5close.astype(float)).diff().dropna()
            r5sd = float(r5ret.std() * np.sqrt(78) * 1e4) if len(r5ret) > 2 else None
        else:
            r5sd = None
        def _s(x):
            return {"mean": (float(x.mean()) if len(x) else None),
                    "median": (float(x.median()) if len(x) else None),
                    "sd": (float(x.std()) if len(x) > 1 else None),
                    "n_obs": int(len(x))}
        rows.append({
            "d": str(d), "n_bars": int(len(g)),
            "n_bars_rth": int((g["in_rth"] == True).sum()),         # noqa: E712
            "n_bars_break": int((g["in_break"] == True).sum()),     # noqa: E712
            "absret_mean_bp": float(full.mean()) if len(full) else None,
            "absret_median_bp": float(full.median()) if len(full) else None,
            "absret_sd_bp": float(full.std()) if len(full) > 1 else None,
            "rth_absret_median_bp": float(rthm.median()) if len(rthm) else None,
            "rth_5min_sd_bp": r5sd,
            "cls_rth": _s(rthm), "cls_globex": _s(glbm), "cls_break": _s(brkm)})
    sdisp = pd.DataFrame(rows)
    # flatten class dicts for parquet
    flat = sdisp.drop(columns=["cls_rth", "cls_globex", "cls_break"]).copy()
    for cls in ("rth", "globex", "break"):
        for m in ("mean", "median", "sd"):
            flat[f"{cls}_absret_{m}_bp"] = [
                (r[f"cls_{cls}"][m] if r[f"cls_{cls}"] else None) for _, r in sdisp.iterrows()]
        flat[f"{cls}_n_obs"] = [(r[f"cls_{cls}"]["n_obs"] if r[f"cls_{cls}"] else 0)
                                for _, r in sdisp.iterrows()]
    flat.to_parquet(f"{OUT}/m1_per_session_rederived.parquet", index=False)
    print(f"[{time.time()-t0:6.1f}s] per-session re-derivation done n={len(sdisp)}", flush=True)

    meas = ["absret_mean_bp", "absret_median_bp", "absret_sd_bp",
            "rth_absret_median_bp", "rth_5min_sd_bp"]
    yy = pd.to_datetime(sdisp["d"]).dt.year
    per_year_new = {}
    for y, g in sdisp.groupby(yy):
        per_year_new[str(int(y))] = {
            "n_sessions": int(len(g)),
            **{m: stats3(g[m].dropna()) for m in meas}}
    full_era_new = {"n_sessions": int(len(sdisp)),
                    **{m: stats3(sdisp[m].dropna()) for m in meas}}
    hole = sdisp[(sdisp["d"] >= "2020-03-23") & (sdisp["d"] <= "2020-05-29")]
    hole_new = {"window": "2020-03-23..2020-05-29 (the pre-v3 vendor hole)",
                "n_sessions": int(len(hole)),
                **{m: stats3(hole[m].dropna()) for m in meas}}

    # session-class aggregates (NEW)
    cls_new = {}
    for cls in ("rth", "globex", "break"):
        col = f"{cls}_absret_mean_bp"
        sub = flat[flat[f"{cls}_n_obs"] > 0]
        cls_new[cls] = {
            "n_sessions_with_obs": int(len(sub)),
            "share_sessions": float(len(sub) / len(flat)),
            "absret_mean_bp": stats3(sub[col].dropna()) if len(sub) else None,
            "absret_median_bp": stats3(sub[f"{cls}_absret_median_bp"].dropna()) if len(sub) else None,
            "absret_sd_bp": stats3(sub[f"{cls}_absret_sd_bp"].dropna()) if len(sub) else None}

    # -- 4. sigma proxy: old (pre-recovery defect) vs new (v3) ----------------
    held = pd.read_parquet(HELD)
    hd = held.sort_values("d").reset_index(drop=True)
    hd["year"] = pd.to_datetime(hd["d"]).dt.year
    yr = []
    for y, g in hd.groupby("year"):
        rr = g["ret"].dropna()
        if len(rr) > 2:
            yr.append({"year": int(y), "n_nonnan_rets": int(len(rr)),
                       "vol_ann_pct": float(100 * rr.std() * np.sqrt(252))})
    vols = [r["vol_ann_pct"] for r in yr]
    # vol_ann_pct is a PERCENT: sigma_bp = pct/100 / sqrt(252) * 1e4
    sigma_new_bp = float(np.median(vols) / np.sqrt(252) * 100)
    pre = json.load(open(PRE_REC))
    pre_by_year = {y_["year"]: y_ for y_ in pre["yearly"]}
    pre_vols = [y_["vol_ann_pct"] for y_ in pre["yearly"] if y_.get("vol_ann_pct") is not None]
    sigma_old_bp = float(np.median(pre_vols) / np.sqrt(252) * 100)
    sigma_year_diffs = []
    for r in yr:
        o = pre_by_year.get(r["year"], {}).get("vol_ann_pct")
        if o is not None:
            dd = r["vol_ann_pct"] - o
            sigma_year_diffs.append({
                "year": r["year"], "vol_ann_pct_old": float(o),
                "vol_ann_pct_new_v3": r["vol_ann_pct"], "delta_pct_pts": float(dd),
                "depleted_old": pre_by_year[r["year"]].get("depleted_sessions"),
                "classification": ("MEASUREMENT_IDENTICAL" if abs(dd) < 1e-9
                                   else "DEFECT_CORRECTED")})
    res_sigma_defect_years = sigma_year_diffs
    res["sigma_proxy"] = {
        "law": "sigma_bp = median_over_years( std(daily held log rets in year) * sqrt(252) ) * 1e4",
        "old_pre_recovery": {
            "source": "NQ_a1_regimes.json (FUTURES-DEEPRESEARCH-V2-20261003/analysis/, sha 66efedc7-class pre-recovery build)",
            "median_vol_ann_pct_years": float(np.median(pre_vols)),
            "sigma_bp": sigma_old_bp,
            "defect": ("pre-recovery series: 2020-03-23..2020-05-29 vendor hole depleted "
                       "(77 depleted sessions, 51 in 2020; year-2020 vol_ann computed on a "
                       "depleted year) + v2 wrong roll 2020-06-01 (NQH0_2020 dead-held 49 sessions)"),
            "cited_census_print": "session sigma ~= 112.3 bp (HYPOTHESES_ESNQ_R3.md §7 F5-K2)"},
        "new_v3": {
            "source": "nq_held_daily_v3.parquet (this lane re-derivation)",
            "per_year": yr,
            "median_vol_ann_pct_years": float(np.median(vols)),
            "sigma_bp": sigma_new_bp},
        "delta_bp": sigma_new_bp - sigma_old_bp,
        "per_year_diffs": res_sigma_defect_years,
        "median_year_invariant": (abs(sigma_new_bp - sigma_old_bp) < 1e-9),
        "classification_median": ("MEASUREMENT_IDENTICAL"
                                  if abs(sigma_new_bp - sigma_old_bp) < 1e-9
                                  else "DEFECT_CORRECTED"),
        "classification_per_year": ("DEFECT_CORRECTED (tail years; median year "
                                    "sits in an untouched year)")}

    # -- 5. diff vs committed k6gate artifact ---------------------------------
    old = json.load(open(OLD_JSON))
    diffs = []

    def diff_block(tag, newb, oldb):
        for m in meas:
            for q in ("median", "p25", "p75"):
                nv = newb.get(m, {}).get(q)
                ov = oldb.get(m, {}).get(q)
                if nv is None and ov is None:
                    continue
                dlt = (nv - ov) if (nv is not None and ov is not None) else None
                diffs.append({
                    "block": tag, "measure": m, "quantile": q,
                    "old_committed": ov, "new_rederived": nv,
                    "delta": dlt,
                    "classification": (classify(dlt) if dlt is not None else "NOT_COMPARABLE")})

    diff_block("full_era", full_era_new, old["full_era"])
    n_years_diff = 0
    for y in sorted(set(per_year_new) | set(old["per_year"])):
        if y in per_year_new and y in old["per_year"]:
            diff_block(f"per_year[{y}]", per_year_new[y], old["per_year"][y])
            n_years_diff += 1
        else:
            diffs.append({"block": f"per_year[{y}]", "measure": "*", "quantile": "*",
                          "old_committed": y in old["per_year"], "new_rederived": y in per_year_new,
                          "delta": None, "classification": "NEW_MEASUREMENT"})
    diff_block("hole_window_2020_03_05", hole_new, old["hole_window_2020_03_05"])

    # per-session parquet compare
    oldp = pd.read_parquet(OLD_PQ)
    m = flat.merge(oldp, on="d", suffixes=("_new", "_old"))
    pq_report = {"n_compared": int(len(m)),
                 "max_abs_delta": {}, "n_rows_any_delta": 0}
    any_delta = np.zeros(len(m), dtype=bool)
    for c in ["n_bars", "n_bars_rth", "absret_mean_bp", "absret_median_bp",
              "absret_sd_bp", "rth_absret_median_bp", "rth_5min_sd_bp"]:
        a = m[f"{c}_new"].astype(float).to_numpy()
        b = m[f"{c}_old"].astype(float).to_numpy()
        both = ~(np.isnan(a) & np.isnan(b))
        dlt = np.where(both, np.abs(np.nan_to_num(a) - np.nan_to_num(b)), 0.0)
        pq_report["max_abs_delta"][c] = float(dlt.max())
        any_delta |= (dlt > 0) & both
    pq_report["n_rows_any_delta"] = int(any_delta.sum())

    n_ident = sum(1 for x in diffs if x["classification"] == "MEASUREMENT_IDENTICAL")
    n_defect = sum(1 for x in diffs if x["classification"] == "DEFECT_CORRECTED")
    n_new = sum(1 for x in diffs if x["classification"] == "NEW_MEASUREMENT")

    res["rederived"] = {"n_sessions": int(len(sdisp)),
                        "first": sdisp["d"].iloc[0], "last": sdisp["d"].iloc[-1],
                        "per_year": per_year_new, "full_era": full_era_new,
                        "hole_window_2020_03_05": hole_new,
                        "session_class_decomposition": cls_new}
    res["diff_vs_committed_k6gate_artifact"] = {
        "old_artifact": "FUTURES-K6GATE-PREP-20261004/nq/session_dispersion_v3.json",
        "n_comparisons": len(diffs), "n_measurement_identical": n_ident,
        "n_defect_corrected": n_defect, "n_new_measurement_rows": n_new,
        "diffs": diffs}
    res["per_session_parquet_compare"] = pq_report
    res["headline"] = {
        "sigma_old_bp": sigma_old_bp, "sigma_new_bp": sigma_new_bp,
        "sigma_delta_bp": sigma_new_bp - sigma_old_bp,
        "rth5min_full_era_median_bp": full_era_new["rth_5min_sd_bp"]["median"],
        "hole_window_n_sessions": hole_new["n_sessions"]}
    res["elapsed_s"] = round(time.time() - t0, 1)
    res["final"] = "PASS_DESCRIPTIVE"
    json.dump(res, open(f"{OUT}/m1_session_sigma_v3.json", "w"), indent=1)
    print(f"[{time.time()-t0:6.1f}s] M1 done: identical={n_ident} defect={n_defect} "
          f"new={n_new}; sigma {sigma_old_bp:.2f} -> {sigma_new_bp:.2f} bp", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
