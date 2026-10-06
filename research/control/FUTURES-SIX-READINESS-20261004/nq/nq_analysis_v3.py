"""NQ-ALIAS-REPAIR Tasks 3+4+5 — before/after 2020 re-measure, full-chain
cease-guard audit, phantom-drift re-measure on the v3 rebuild.

Evidence sources:
  BEFORE (read-only): FUTURES-DEEPRESEARCH-V2-20261003/analysis/NQ_cache/
  AFTER:  this lane's cache_v3/ (built by nq_rebuild_v3.py)

Laws: descriptive coverage/volume/roll-gap/close-level aggregates ONLY — no
PnL, no returns beyond session close levels, no strategy metrics. Roll-gap
and embed figures are HAZARD metrics of NOT adjusting the chain (phantom
drift), labeled as such.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nq_deep_lib_v3 as L  # noqa: E402

BASE = ("/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-readiness"
        "/prep/research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/NQ_cache")
V3 = L.CACHE
W1 = ("2018-08-15", "2020-06-30")   # alias listing window + post-cutover
W2 = ("2020-01-01", "2020-12-31")   # calendar 2020


def jdump(obj, path):
    with open(path, "w") as fh:
        json.dump(L._san(obj), fh, indent=1, allow_nan=False)


def roll_events(held: pd.DataFrame, exp: dict) -> pd.DataFrame:
    h = held.sort_values("session_date").reset_index(drop=True)
    h["prev"] = h["held"].shift()
    r = h[h["held"].ne(h["prev"]) & h["prev"].notna()].copy()
    r["days_to_expiry"] = [
        (pd.Timestamp(exp[o]) - pd.Timestamp(d)).days if o in exp else None
        for o, d in zip(r["prev"], r["session_date"])]
    return r[["session_date", "prev", "held", "days_to_expiry"]].rename(
        columns={"prev": "old", "held": "new"})


def a3_spread_stats(sess_real: pd.DataFrame, rolls: pd.DataFrame) -> pd.DataFrame:
    """Mirror NQ_a3_term.py exactly: roll-day gap + trailing-window median."""
    closes = sess_real.pivot_table(index="session_date", columns="contract",
                                   values="close")
    vols = sess_real.pivot_table(index="session_date", columns="contract",
                                 values="volume")
    rows = []
    for r in rolls.itertuples():
        old, new, dstr = r.old, r.new, r.session_date
        if old not in closes.columns or new not in closes.columns:
            rows.append({"roll_session": dstr, "old": old, "new": new,
                         "days_to_expiry": r.days_to_expiry,
                         "spread_pts_roll_day": None,
                         "spread_pts_median10": None,
                         "old_volume_roll_day": None,
                         "new_volume_roll_day": None})
            continue
        di = closes.index.get_loc(dstr)
        window = closes.index[max(0, di - 12):di + 1]
        sp = ((closes.loc[window, new] - closes.loc[window, old]) / 1e9).dropna()
        ov = vols.loc[dstr, old] if old in vols.columns else np.nan
        nv = vols.loc[dstr, new] if new in vols.columns else np.nan
        rows.append({
            "roll_session": dstr, "old": old, "new": new,
            "days_to_expiry": r.days_to_expiry,
            "spread_pts_roll_day": float(sp.iloc[-1]) if len(sp) else None,
            "spread_pts_median10": (float(sp.iloc[:-1].median())
                                    if len(sp) > 2 else None),
            "old_volume_roll_day": (float(ov)
                                    if pd.notna(ov) and ov else None),
            "new_volume_roll_day": (float(nv) if pd.notna(nv) else None),
        })
    return pd.DataFrame(rows)


def panel_window_stats(path: str, a: str, b: str) -> dict:
    import pyarrow.parquet as pq
    t = pq.read_table(path, columns=["ts_event", "volume"])
    ts = pd.Series(pd.to_datetime(t["ts_event"], unit="ns", utc=True))
    m = ((ts >= pd.Timestamp(a, tz="UTC")) &
         (ts <= pd.Timestamp(b, tz="UTC") + pd.Timedelta(days=1))).to_numpy()
    vol = t["volume"].to_numpy()[m]
    return {"bars": int(m.sum()), "volume": int(vol.sum())}


def hold_segments(held: pd.DataFrame, sess_real: pd.DataFrame) -> pd.DataFrame:
    """Per hold segment: bars-present cessation and dead-held sessions."""
    ces = sess_real.groupby("contract")["session_date"].max()
    h = held.sort_values("session_date").reset_index(drop=True)
    h["seg"] = h["held"].ne(h["held"].shift()).cumsum()
    out = []
    for (seg), g in h.groupby("seg"):
        c = g["held"].iloc[0]
        first, last = g["session_date"].iloc[0], g["session_date"].iloc[-1]
        ces_d = ces.get(c)
        dead = int((g["session_date"] > ces_d).sum()) if ces_d is not None \
            else int(len(g))
        last_day_bars = bool(ces_d is not None and last <= ces_d)
        out.append({
            "contract": c, "first_held": str(first), "last_held": str(last),
            "n_sessions": int(len(g)),
            "cessation_bars_present_last_session":
                str(ces_d) if ces_d is not None else None,
            "last_held_day_has_bars": last_day_bars,
            "dead_held_sessions": dead,
            "violation": (not last_day_bars) or dead > 0,
        })
    return pd.DataFrame(out)


def main() -> None:
    # ---------------- load BEFORE (read-only) and AFTER ----------------
    sess_b = pd.read_parquet(os.path.join(BASE, "nq_sessions.parquet"))
    held_b = pd.read_parquet(os.path.join(BASE, "held_volume_k5.parquet"))
    hd_b = pd.read_parquet(os.path.join(BASE, "nq_held_daily.parquet"))
    reg_b = pd.read_json(os.path.join(BASE, "contract_registry.json"))
    sess_v = pd.read_parquet(os.path.join(V3, "nq_sessions_v3.parquet"))
    held_v = pd.read_parquet(os.path.join(V3, "held_volume_k5_v3.parquet"))
    held_cg = pd.read_parquet(os.path.join(V3, "held_volume_k5_cg_v3.parquet"))
    hd_v = pd.read_parquet(os.path.join(V3, "nq_held_daily_v3.parquet"))
    reg_v = pd.read_json(os.path.join(V3, "contract_registry_v3.json"))
    # normalize object-dtype session dates to datetime64 for comparisons
    for f in (sess_b, sess_v, held_b, held_v, held_cg):
        f["session_date"] = pd.to_datetime(f["session_date"])
    exp_b = reg_b.set_index("contract")["expiry"].dropna().to_dict()
    exp_v = reg_v.set_index("contract")["expiry"].dropna().to_dict()
    sess_b_real = L._real_contracts(sess_b)
    sess_v_real = L._real_contracts(sess_v)

    res3 = {"schema": "nq_before_after_2020@1",
            "lane": "NQ-ALIAS-REPAIR",
            "windows": {"alias_window_plus_cutover": list(W1),
                        "calendar_2020": list(W2)}}

    # ---- bars / volume recovered (panels, both windows) ----
    for wname, (a, b) in (("W1_alias_window", W1), ("W2_calendar_2020", W2)):
        pb = panel_window_stats(os.path.join(BASE, "nq_outright_1m.parquet"), a, b)
        pv = panel_window_stats(os.path.join(V3, "nq_outright_1m_v3.parquet"), a, b)
        res3[f"panel_{wname}"] = {
            "before_bars": pb["bars"], "after_bars": pv["bars"],
            "bars_recovered": pv["bars"] - pb["bars"],
            "before_volume": pb["volume"], "after_volume": pv["volume"],
            "volume_recovered": pv["volume"] - pb["volume"]}

    # ---- held-chain session counts: NaN vs real closes ----
    def chain_stats(hd: pd.DataFrame, a: str, b: str) -> dict:
        m = ((hd["d"] >= a) & (hd["d"] <= b))
        w = hd[m]
        return {"held_sessions": int(len(w)),
                "real_close_sessions": int(w["close"].notna().sum()),
                "nan_close_sessions": int(w["close"].isna().sum()),
                "depleted_sessions": int(w["depleted"].sum()) if "depleted" in w else None}
    for wname, (a, b) in (("W1_alias_window", W1), ("W2_calendar_2020", W2)):
        res3[f"held_chain_{wname}"] = {
            "before": chain_stats(hd_b, a, b), "after": chain_stats(hd_v, a, b)}

    # ---- held contract sequence through the window ----
    def seq(held: pd.DataFrame, a: str, b: str) -> list:
        h = held[(held["session_date"] >= pd.Timestamp(a)) &
                 (held["session_date"] <= pd.Timestamp(b))]
        h = h.sort_values("session_date")
        seg = h[h["held"].ne(h["held"].shift())]
        return [{"from": str(r.session_date), "held": r.held}
                for r in seg.itertuples()]
    res3["held_sequence_2019_06_2020_06_30"] = {
        "before": seq(held_b, "2019-06-01", "2020-06-30"),
        "after": seq(held_v, "2019-06-01", "2020-06-30")}

    # ---- rolls: totals + window reconciliation ----
    rb = roll_events(held_b, exp_b)
    rv = roll_events(held_v, exp_v)
    rcg = roll_events(held_cg, exp_v)
    res3["total_chain_rolls"] = {"baseline_k5": int(len(rb)),
                                 "v3_k5": int(len(rv)),
                                 "v3_k5_cease_guard": int(len(rcg))}
    wa, wb = "2018-08-01", "2020-06-30"
    rbw = rb[(rb["session_date"] >= wa) & (rb["session_date"] <= wb)]
    rvw = rv[(rv["session_date"] >= wa) & (rv["session_date"] <= wb)]
    rcgw = rcg[(rcg["session_date"] >= wa) & (rcg["session_date"] <= wb)]
    res3["rolls_in_window"] = {
        "window": [wa, wb],
        "before_k5": rbw.to_dict("records"),
        "after_k5": rvw.to_dict("records"),
        "after_k5_cease_guard": rcgw.to_dict("records")}
    # roll-by-roll reconciliation over the FULL chain
    mb = rb.merge(rv, on=["old", "new"], how="outer",
                  suffixes=("_before", "_after"))
    res3["roll_by_roll_reconciliation"] = {
        "matched_pairs": int(mb.dropna(subset=["session_date_before",
                                               "session_date_after"]).shape[0]),
        "date_changed": mb[mb["session_date_before"].fillna("?") !=
                           mb["session_date_after"].fillna("?")][
            ["old", "new", "session_date_before", "session_date_after",
             "days_to_expiry_before", "days_to_expiry_after"]].to_dict("records")}
    # dte>45 quarantine check on v3
    dte = rv["days_to_expiry"].dropna().astype(int)
    inband = dte[(dte >= 0) & (dte <= 45)]
    res3["dte_quarantine_check_v3"] = {
        "n_rolls": int(len(rv)), "n_with_expiry": int(len(dte)),
        "n_in_0_45_band": int(len(inband)),
        "out_of_band": rv[(rv["days_to_expiry"].isna()) |
                          (rv["days_to_expiry"] < 0) |
                          (rv["days_to_expiry"] > 45)][
            ["session_date", "old", "new", "days_to_expiry"]].to_dict("records"),
        "baseline_note": "baseline a3 excluded rolls with dte>45 as 2020 "
                         "hole artifacts (62 of 66 in band); after the fix "
                         "the quarantine is " + ("NOT needed" if len(inband) == len(dte) else "STILL needed")}

    # ---- 2020 unadjusted-embed (hazard metric of NOT adjusting) ----
    spb = a3_spread_stats(sess_b_real, rb)
    spv = a3_spread_stats(sess_v_real, rv)
    for tag, sp in (("before", spb), ("after", spv)):
        ok = sp.dropna(subset=["spread_pts_roll_day"])
        ok = ok[ok["old_volume_roll_day"].fillna(0) > 0]
        ok = ok.assign(year=pd.to_datetime(ok["roll_session"]).dt.year)
        embed = ok.groupby("year")["spread_pts_roll_day"].sum()
        res3[f"unadjusted_embed_pts_per_year_{tag}"] = {
            str(int(k)): float(v) for k, v in embed.items()}
        if tag == "after":
            ok.to_parquet(os.path.join(V3, "v3_rolls_spread_stats.parquet"),
                          index=False)

    jdump(res3, os.path.join(HERE, "before_after_2020.json"))
    print("task3 wrote before_after_2020.json")

    # ================= Task 4: cease-guard audit =================
    audit = {"schema": "nq_cease_guard_audit@1", "lane": "NQ-ALIAS-REPAIR",
             "law_cross_reference": {
                 "source": "6J_DEEP_v2.md section 8 ERRATUM M-5 "
                           "(FUTURES-DEEPRESEARCH-V2-20261003/dossiers_v2/)",
                 "proven_failure": "6J 2022-09-20: plain k-window rule held "
                                   "ceased U2 while Z2 traded 125,303 lots; "
                                   "baseline weak guard NQ_deep_lib.py:266-267 "
                                   "switches only after the ceased contract is "
                                   "absent a FULL k-window"},
             "cessation_derivation": "DECLARED DERIVATION: cessation(contract) "
                                     "= last session_date with any session row "
                                     "(bars present) for that contract in the "
                                     "respective rebuild's session table — NOT "
                                     "exchange metadata; cross-checked against "
                                     "registry last_bar below",
             "violation_definition": "a hold segment VIOLATES if its last held "
                                     "session has no bars for the held "
                                     "contract (last_held_day_has_bars=False) "
                                     "or any held session is past the held "
                                     "contract's bars-present cessation "
                                     "(dead_held_sessions>0) — the 6J "
                                     "held-a-dead-contract failure mode"}
    seg_v = hold_segments(held_v, sess_v_real)
    seg_cg = hold_segments(held_cg, sess_v_real)
    seg_b = hold_segments(held_b, sess_b_real)
    audit["v3_plain_k5"] = {
        "n_segments": int(len(seg_v)),
        "n_violations": int(seg_v["violation"].sum()),
        "violations": seg_v[seg_v["violation"]].to_dict("records")}
    audit["v3_k5_cease_guard"] = {
        "n_segments": int(len(seg_cg)),
        "n_violations": int(seg_cg["violation"].sum()),
        "violations": seg_cg[seg_cg["violation"]].to_dict("records")}
    audit["baseline_before_k5"] = {
        "n_segments": int(len(seg_b)),
        "n_violations": int(seg_b["violation"].sum()),
        "violations": seg_b[seg_b["violation"]].to_dict("records"),
        "note": "BEFORE chain: 1 expected violation — NQH0_2020 held through "
                "the alias hole (2020-03-23..2020-05-29) after its 03-20 "
                "expiry; dead-handoff roll fired 2020-06-01 (dte -73)"}
    # cessation vs registry last_bar cross-check (v3) — same session-date
    # derivation as the lib: CT normalize, then +1 day when hour >= 17
    lb = reg_v.dropna(subset=["last_bar"]).copy()
    loc = pd.to_datetime(lb["last_bar"], utc=True).dt.tz_convert(L.CHI)
    lb["last_session"] = (loc.dt.normalize() + pd.to_timedelta(
        (loc.dt.hour >= 17).astype(int), unit="D")).dt.tz_localize(None)
    lbd = lb.groupby("contract")["last_session"].max().dt.date.astype(str).to_dict()
    mism = []
    for c, ces in sess_v_real.groupby("contract")["session_date"].max().items():
        if c in lbd and str(ces.date()) != lbd[c]:
            mism.append({"contract": c, "cessation": str(ces.date()),
                         "registry_last_bar_session": lbd[c]})
    audit["cessation_vs_registry_last_bar_mismatches"] = mism
    seg_v.to_parquet(os.path.join(V3, "v3_hold_segments_k5.parquet"), index=False)
    jdump(audit, os.path.join(HERE, "cease_guard_audit.json"))
    print(f"task4: v3 k5 violations={int(seg_v['violation'].sum())} "
          f"cg violations={int(seg_cg['violation'].sum())} "
          f"baseline violations={int(seg_b['violation'].sum())}")

    # ================= Task 5: phantom drift v3 =================
    ok = pd.read_parquet(os.path.join(V3, "v3_rolls_spread_stats.parquet"))
    pd5 = {"schema": "nq_phantom_drift_v3@1", "lane": "NQ-ALIAS-REPAIR",
           "label": "HAZARD METRICS OF NOT ADJUSTING THE CHAIN — phantom "
                    "drift; not tradable statistics",
           "method": "NQ_a3_term.py methodology mirrored: ok = rolls with "
                     "spread data and old_volume_roll_day>0; corr over "
                     "(spread_pts_roll_day, spread_pts_median10)"}
    base_corr = 0.9990802440849986
    corr = float(ok["spread_pts_roll_day"].corr(ok["spread_pts_median10"]))
    pd5["v3"] = {"n_rolls_with_spread": int(len(ok)),
                 "corr_rollgap_vs_spreadmed10": corr,
                 "baseline_corr": base_corr,
                 "corr_delta_vs_baseline": corr - base_corr,
                 "gap_pts_median": float(ok["spread_pts_roll_day"].median()),
                 "gap_pts_p10": float(ok["spread_pts_roll_day"].quantile(.1)),
                 "gap_pts_p90": float(ok["spread_pts_roll_day"].quantile(.9))}
    embed_v = res3["unadjusted_embed_pts_per_year_after"]
    embed_b = res3["unadjusted_embed_pts_per_year_before"]
    pd5["embed_pts_per_year_v3"] = embed_v
    pd5["embed_pts_per_year_baseline"] = embed_b
    pd5["embed_2020"] = {"baseline_with_holes": embed_b.get("2020"),
                         "v3_recovered": embed_v.get("2020")}
    jdump(pd5, os.path.join(HERE, "phantom_drift_v3.json"))
    print(f"task5: corr v3={corr:.5f} baseline={base_corr:.5f}; "
          f"embed2020 baseline={embed_b.get('2020')} v3={embed_v.get('2020')}")


if __name__ == "__main__":
    main()
