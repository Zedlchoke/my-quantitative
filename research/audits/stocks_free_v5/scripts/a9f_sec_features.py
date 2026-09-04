"""A9-F PIT feature build-through + control identifiability (NO PnL computed).

One streaming pass over the frozen SEC store (fields of the six proposals),
canonical bridge panels at every declared decision slot, coverage vs declared
floors, anchor-vs-control rank divergence vs declared kill thresholds, and
measured membership churn for turnover arithmetic.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import date

import numpy as np

from a9f_lib import (
    FIELDS_NEEDED, FOLDS, SECTORS, S0_START,
    aggregate_sector_asof, build_panel, fold_sessions, global_clock, iter_sec_records,
    load_close, load_panel_sectors, load_spy_calendar, pre_s0_fractions,
    quarterly_clock, rank_dict, session_at, side_overlap_fraction, spearman,
    store_sha256, to_normalized, top_bottom_book, basket_changes, hysteresis_book,
)

OUT = {}

TICK_FIELDS_Q = {}  # filled in main


def observations(panel, session):
    return panel.get(session, {})


def cov(obs):
    return round(obs.coverage, 4) if obs is not None else None


def eff(obs):
    return str(obs.effective_date) if obs is not None else None


def val(obs):
    return obs.value if obs is not None else None


def main():
    print("hashing store...", flush=True)
    sha = store_sha256()
    OUT["store_sha256_measured"] = sha
    OUT["store_sha256_declared"] = "f53eb3712bc9d686ec8a91b3715beaf73be1e5243a89af1816bd62eea51df955"
    OUT["store_sha_match"] = sha == OUT["store_sha256_declared"]
    print("store sha match:", OUT["store_sha_match"], flush=True)

    print("streaming SEC store (one pass, wanted fields)...", flush=True)
    n_total = 0
    n_kept = 0
    kept = {f: [] for f in FIELDS_NEEDED}
    for obj in iter_sec_records(FIELDS_NEEDED):
        n_total += 1
        try:
            kept[obj["field"]].append(to_normalized(obj))
            n_kept += 1
        except Exception as e:  # malformed row: count and continue (audit note)
            continue
    OUT["sec_store"] = {
        "records_fields_of_interest": {f: len(v) for f, v in kept.items()},
        "records_scanned": n_total,
    }
    print("kept:", {f: len(v) for f, v in kept.items()}, flush=True)

    filer_sectors = load_panel_sectors()
    OUT["panel_filers_mapped"] = len(filer_sectors)

    # census verification: pre-S0 availability fractions
    OUT["pre_s0_fractions_recomputed"] = {
        f: {s: round(x, 3) for s, x in v.items()} for f, v in pre_s0_fractions(kept, filer_sectors).items()
    }

    cal = load_spy_calendar()
    s0 = [d for d in cal if S0_START <= d <= date(2025, 7, 31)]
    folds = fold_sessions(s0)
    qticks = quarterly_clock(folds, 63, 567)          # a4/a5 arms: 10 ticks x 3 folds
    qtick_list = sorted(t for v in qticks.values() for t in v)
    seeds = set(folds[f][0] for f in folds)
    g42 = global_clock(s0, 42)                         # a6 arms: 44 slots

    # ETF leg-eligibility helper
    hist_dates = {s: sorted(load_close(s)) for s in SECTORS}

    def eligible_by_history(sym, t, need):
        dts = hist_dates[sym]
        return sum(1 for x in dts if x <= t) >= need

    def leg_elig(t, need):
        return {s for s in SECTORS if eligible_by_history(s, t, need)}

    # ------------------------------------------------------------ panels ----
    print("building quarterly panels...", flush=True)
    ref252 = {t: session_at(cal, t, 252) for t in qtick_list}

    # a4_h1: Assets gap 400 at ticks and t-252 refs
    assets400_t = build_panel(kept, filer_sectors, qtick_list, "us-gaap:Assets", 400)
    ref_sessions = sorted(set(ref252.values()))
    assets400_ref = build_panel(kept, filer_sectors, ref_sessions, "us-gaap:Assets", 400)
    # a4_h2: cash gap 400 + assets gap 400 at ticks (assets reused)
    cash400 = build_panel(kept, filer_sectors, qtick_list,
                          "us-gaap:CashAndCashEquivalentsAtCarryingValue", 400)
    curr400 = build_panel(kept, filer_sectors, qtick_list, "us-gaap:AssetsCurrent", 400)
    # a5_h1: float gap 550 + LSE gap 550
    float550 = build_panel(kept, filer_sectors, qtick_list, "dei:EntityPublicFloat", 550)
    lse550 = build_panel(kept, filer_sectors, qtick_list,
                         "us-gaap:LiabilitiesAndStockholdersEquity", 550)
    # a6_h1: AssetsCurrent gap 200 + Assets gap 200 on the 42-grid
    curr200 = build_panel(kept, filer_sectors, g42, "us-gaap:AssetsCurrent", 200)
    assets200 = build_panel(kept, filer_sectors, g42, "us-gaap:Assets", 200)
    print("panels done", flush=True)

    FLOOR = 0.60

    # ---------------------------------------------------------- a4_h1 -------
    a4h1 = {"declared_gates": {
        "census_floor": 0.80, "coverage_floor_both_endpoints": 0.60,
        "endpoint_effective_date_coherence_days": 100, "leg_history_sessions": 63,
        "kill": "mean |rho| <= 0.40 AND max |rho| <= 0.60; CAN-FIRE: control dispersion > 0 at every tick AND >= 5 control-book membership changes; >= 9 eligible at every tick"}}
    per_tick = []
    anchor_ranks, control_ranks = {}, {}
    for fid in qticks:
        for t in qticks[fid]:
            r = ref252[t]
            elig, why = {}, {}
            legs = leg_elig(t, 63)
            for s in SECTORS:
                ot, orf = observations(assets400_t, t).get(s), observations(assets400_ref, r).get(s)
                if ot is None or orf is None:
                    why[s] = "missing_panel"
                    continue
                if ot.coverage < FLOOR or orf.coverage < FLOOR:
                    why[s] = f"coverage {cov(ot)}/{cov(orf)}"
                    continue
                gapdays = abs((ot.effective_date - orf.effective_date).days)
                if gapdays > 100:
                    why[s] = f"coherence {gapdays}d"
                    continue
                if s not in legs:
                    why[s] = "leg_history<63"
                    continue
                g = math.log(ot.value / orf.value)
                elig[s] = {"g": g, "lnM": math.log(ot.value),
                           "cov_t": cov(ot), "cov_ref": cov(orf),
                           "eff_t": eff(ot), "eff_ref": eff(orf), "coh_days": gapdays}
            keys = sorted(elig)
            a4h1.setdefault("min_elig", 99)
            a4h1["min_elig"] = min(a4h1["min_elig"], len(keys))
            gv = {s: elig[s]["g"] for s in keys}
            lv = {s: elig[s]["lnM"] for s in keys}
            anchor_ranks[t] = rank_dict(gv, reverse=True)
            control_ranks[t] = rank_dict(lv, reverse=True)
            rho = spearman(list(gv.values()), list(lv.values())) if len(keys) >= 3 else float("nan")
            per_tick.append({
                "tick": str(t), "fold": fid, "ref": str(r), "n_eligible": len(keys),
                "excluded": why, "rho_anchor_vs_control": round(rho, 4),
                "control_dispersion": round(float(np.std(list(lv.values()))), 6) if keys else 0.0,
            })
    a4h1["per_tick"] = per_tick
    rhos = [x["rho_anchor_vs_control"] for x in per_tick]
    a4h1["rho_mean_abs"] = round(float(np.nanmean(np.abs(rhos))), 4)
    a4h1["rho_max_abs"] = round(float(np.nanmax(np.abs(rhos))), 4)
    a4h1["gate_mean_le_0.40"] = a4h1["rho_mean_abs"] <= 0.40
    a4h1["gate_max_le_0.60"] = a4h1["rho_max_abs"] <= 0.60
    a4h1["gate_elig_ge_9_all_ticks"] = a4h1["min_elig"] >= 9
    ctrl_books = hysteresis_book(control_ranks, seeds)
    ch = basket_changes(ctrl_books)
    a4h1["control_book_membership_changes_total"] = int(sum(c["legs_changed"] for c in ch))
    a4h1["control_dispersion_positive_all_ticks"] = all(x["control_dispersion"] > 0 for x in per_tick)
    a4h1["gate_can_fire"] = (a4h1["control_dispersion_positive_all_ticks"]
                             and a4h1["control_book_membership_changes_total"] >= 5)
    a4h1["identifiable"] = (a4h1["gate_mean_le_0.40"] and a4h1["gate_max_le_0.60"]
                            and a4h1["gate_elig_ge_9_all_ticks"] and a4h1["gate_can_fire"])
    # anchor book churn for turnover arithmetic
    anchor_books = hysteresis_book(anchor_ranks, seeds)
    anch_ch = basket_changes(anchor_books)
    a4h1["anchor_membership_changes_total"] = int(sum(c["legs_changed"] for c in anch_ch))
    a4h1["anchor_legs_changed_per_transition"] = [c["legs_changed"] for c in anch_ch]
    OUT["a4_h1"] = a4h1
    print("a4_h1: mean|rho|", a4h1["rho_mean_abs"], "max", a4h1["rho_max_abs"],
          "min_elig", a4h1["min_elig"], "identifiable", a4h1["identifiable"], flush=True)

    # ---------------------------------------------------------- a4_h2 -------
    a4h2 = {"declared_gates": {
        "census_floor_both_fields": 0.80, "census_excluded": ["XLF"],
        "coverage_floor_both_fields": 0.60, "effective_date_coherence_days": 100,
        "leg_history_sessions": 63,
        "kill": "mean |rho| <= 0.40 AND max |rho| <= 0.60; CAN-FIRE; >= 9 eligible anchor/control every tick, >= 8 neighbour"}}
    per_tick = []
    anchor_ranks2, control_ranks2 = {}, {}
    for fid in qticks:
        for t in qticks[fid]:
            elig, why = {}, {}
            legs = leg_elig(t, 63)
            for s in SECTORS:
                oc = observations(cash400, t).get(s)
                oa = observations(assets400_t, t).get(s)
                if s == "XLF":
                    why[s] = "census cash 0.70 < 0.80 (ex ante)"
                    continue
                if oc is None or oa is None:
                    why[s] = "missing_panel"
                    continue
                if oc.coverage < FLOOR or oa.coverage < FLOOR:
                    why[s] = f"coverage cash {cov(oc)}/assets {cov(oa)}"
                    continue
                gapdays = abs((oc.effective_date - oa.effective_date).days)
                if gapdays > 100:
                    why[s] = f"coherence {gapdays}d"
                    continue
                if s not in legs:
                    why[s] = "leg_history<63"
                    continue
                elig[s] = {"ci": oc.value / oa.value, "ln_cash": math.log(oc.value),
                           "cov_cash": cov(oc), "cov_assets": cov(oa),
                           "eff_cash": eff(oc), "eff_assets": eff(oa), "coh_days": gapdays}
            keys = sorted(elig)
            a4h2["min_elig"] = min(a4h2.get("min_elig", 99), len(keys))
            civ = {s: elig[s]["ci"] for s in keys}
            lv = {s: elig[s]["ln_cash"] for s in keys}
            anchor_ranks2[t] = rank_dict(civ, reverse=True)
            control_ranks2[t] = rank_dict(lv, reverse=True)
            rho = spearman(list(civ.values()), list(lv.values())) if len(keys) >= 3 else float("nan")
            per_tick.append({
                "tick": str(t), "fold": fid, "n_eligible": len(keys), "excluded": why,
                "rho_anchor_vs_control": round(rho, 4),
                "control_dispersion": round(float(np.std(list(lv.values()))), 6) if keys else 0.0,
            })
    a4h2["per_tick"] = per_tick
    rhos = [x["rho_anchor_vs_control"] for x in per_tick]
    a4h2["rho_mean_abs"] = round(float(np.nanmean(np.abs(rhos))), 4)
    a4h2["rho_max_abs"] = round(float(np.nanmax(np.abs(rhos))), 4)
    a4h2["gate_mean_le_0.40"] = a4h2["rho_mean_abs"] <= 0.40
    a4h2["gate_max_le_0.60"] = a4h2["rho_max_abs"] <= 0.60
    a4h2["gate_elig_ge_9_all_ticks"] = a4h2["min_elig"] >= 9
    ctrl_books2 = hysteresis_book(control_ranks2, seeds)
    ch2 = basket_changes(ctrl_books2)
    a4h2["control_book_membership_changes_total"] = int(sum(c["legs_changed"] for c in ch2))
    a4h2["control_dispersion_positive_all_ticks"] = all(x["control_dispersion"] > 0 for x in per_tick)
    a4h2["gate_can_fire"] = (a4h2["control_dispersion_positive_all_ticks"]
                             and a4h2["control_book_membership_changes_total"] >= 5)
    # neighbour rank-set floor: 9 census sectors passing cash+current, >= 8 at every tick
    neigh9 = ["XLB", "XLC", "XLE", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"]
    neigh_min = 99
    for fid in qticks:
        for t in qticks[fid]:
            legs = leg_elig(t, 63)
            n = sum(1 for s in neigh9 if s in legs)
            neigh_min = min(neigh_min, n)
    a4h2["neighbour_min_eligible"] = neigh_min
    a4h2["gate_neighbour_ge_8"] = neigh_min >= 8
    a4h2["identifiable"] = (a4h2["gate_mean_le_0.40"] and a4h2["gate_max_le_0.60"]
                            and a4h2["gate_elig_ge_9_all_ticks"] and a4h2["gate_can_fire"]
                            and a4h2["gate_neighbour_ge_8"])
    anchor_books2 = hysteresis_book(anchor_ranks2, seeds)
    anch_ch2 = basket_changes(anchor_books2)
    a4h2["anchor_membership_changes_total"] = int(sum(c["legs_changed"] for c in anch_ch2))
    a4h2["anchor_legs_changed_per_transition"] = [c["legs_changed"] for c in anch_ch2]
    OUT["a4_h2"] = a4h2
    print("a4_h2: mean|rho|", a4h2["rho_mean_abs"], "max", a4h2["rho_max_abs"],
          "min_elig", a4h2["min_elig"], "neigh_min", neigh_min,
          "identifiable", a4h2["identifiable"], flush=True)

    # ---------------------------------------------------------- a5_h1 -------
    a5h1 = {"declared_gates": {
        "census_floor_both_fields": 0.80, "coverage_floor": 0.60,
        "leg_history_sessions": 21,
        "kill": "Spearman(anchor, control) <= 0.90 at decision slots AND >= 25% of slots differ in >= 1 long/short membership leg"}}
    per_tick = []
    anchor_ranks3, control_ranks3 = {}, {}
    for fid in qticks:
        for t in qticks[fid]:
            elig, why = {}, {}
            legs = leg_elig(t, 21)
            for s in SECTORS:
                ofl = observations(float550, t).get(s)
                ol = observations(lse550, t).get(s)
                if ofl is None or ol is None:
                    why[s] = "missing_panel"
                    continue
                if ofl.coverage < FLOOR or ol.coverage < FLOOR:
                    why[s] = f"coverage float {cov(ofl)}/lse {cov(ol)}"
                    continue
                if s not in legs:
                    why[s] = "leg_history<21"
                    continue
                elig[s] = {"R": ofl.value / ol.value, "float_level": ofl.value,
                           "cov_float": cov(ofl), "cov_lse": cov(ol)}
            keys = sorted(elig)
            a5h1["min_elig"] = min(a5h1.get("min_elig", 99), len(keys))
            rv = {s: elig[s]["R"] for s in keys}
            fv = {s: elig[s]["float_level"] for s in keys}
            anchor_ranks3[t] = rank_dict(rv, reverse=False)
            control_ranks3[t] = rank_dict(fv, reverse=False)
            rho = spearman(list(rv.values()), list(fv.values())) if len(keys) >= 3 else float("nan")
            per_tick.append({
                "tick": str(t), "fold": fid, "n_eligible": len(keys), "excluded": why,
                "rho_anchor_vs_control": round(rho, 4),
            })
    a5h1["per_tick"] = per_tick
    rhos = [x["rho_anchor_vs_control"] for x in per_tick]
    a5h1["rho_mean_abs"] = round(float(np.nanmean(np.abs(rhos))), 4)
    a5h1["rho_max_abs"] = round(float(np.nanmax(np.abs(rhos))), 4)
    a5h1["gate_rho_le_0.90"] = a5h1["rho_max_abs"] <= 0.90
    # membership divergence on fresh 3v3 books (a5 has no hysteresis)
    ab = top_bottom_book(anchor_ranks3)
    cb = top_bottom_book(control_ranks3)
    ticks = sorted(anchor_ranks3)
    diverging = sum(1 for t in ticks if ab[t]["long"] != cb[t]["long"] or ab[t]["short"] != cb[t]["short"])
    a5h1["slots_with_membership_divergence"] = diverging
    a5h1["slots_total"] = len(ticks)
    a5h1["divergence_fraction"] = round(diverging / len(ticks), 4)
    a5h1["gate_divergence_ge_25pct"] = a5h1["divergence_fraction"] >= 0.25
    a5h1["identifiable"] = a5h1["gate_rho_le_0.90"] and a5h1["gate_divergence_ge_25pct"]
    anch_ch3 = basket_changes(ab)
    a5h1["anchor_legs_changed_per_transition"] = [c["legs_changed"] for c in anch_ch3]
    a5h1["anchor_membership_changes_total"] = int(sum(c["legs_changed"] for c in anch_ch3))
    OUT["a5_h1"] = a5h1
    print("a5_h1: mean|rho|", a5h1["rho_mean_abs"], "max", a5h1["rho_max_abs"],
          "divergence", a5h1["divergence_fraction"], "identifiable", a5h1["identifiable"], flush=True)

    # ---------------------------------------------------------- a6_h1 -------
    a6h1 = {"declared_gates": {
        "census_9_sectors": ["XLB", "XLC", "XLE", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"],
        "coverage_floor_per_leg": 0.40, "leg_history_sessions": 252,
        "skip_rule_lt_6_eligible": True,
        "kill": "mean |rho| >= 0.60 across decision sessions OR >= 2 of 3 legs share the same side in >= 70% of sessions"}}
    per_tick = []
    anchor_ranks4, control_ranks4 = {}, {}
    for t in g42:
        elig, why = {}, {}
        legs = leg_elig(t, 252)
        census9 = set(a6h1["declared_gates"]["census_9_sectors"])
        for s in SECTORS:
            if s not in census9:
                why[s] = "census AssetsCurrent not fundable (ex ante)"
                continue
            oc = observations(curr200, t).get(s)
            oa = observations(assets200, t).get(s)
            if oc is None or oa is None:
                why[s] = "missing_panel"
                continue
            if oc.coverage < 0.40 or oa.coverage < 0.40:
                why[s] = f"coverage curr {cov(oc)}/assets {cov(oa)}"
                continue
            if s not in legs:
                why[s] = "leg_history<252"
                continue
            elig[s] = {"wcint": oc.value / oa.value, "assets_level": oa.value,
                       "cov_curr": cov(oc), "cov_assets": cov(oa)}
        keys = sorted(elig)
        a6h1["min_elig"] = min(a6h1.get("min_elig", 99), len(keys))
        wv = {s: elig[s]["wcint"] for s in keys}
        av = {s: elig[s]["assets_level"] for s in keys}
        anchor_ranks4[t] = rank_dict(wv, reverse=False)
        control_ranks4[t] = rank_dict(av, reverse=False)
        rho = spearman(list(wv.values()), list(av.values())) if len(keys) >= 3 else float("nan")
        per_tick.append({
            "tick": str(t), "n_eligible": len(keys), "excluded": why,
            "rho_anchor_vs_control": round(rho, 4),
        })
    a6h1["per_tick"] = per_tick
    rhos = [x["rho_anchor_vs_control"] for x in per_tick]
    a6h1["rho_mean_abs"] = round(float(np.nanmean(np.abs(rhos))), 4)
    a6h1["rho_max_abs"] = round(float(np.nanmax(np.abs(rhos))), 4)
    a6h1["gate_mean_abs_below_0.60"] = a6h1["rho_mean_abs"] < 0.60
    ab4 = top_bottom_book(anchor_ranks4)
    cb4 = top_bottom_book(control_ranks4)
    a6h1["long_overlap_ge2_fraction"] = round(side_overlap_fraction(ab4, cb4, "long", 2), 4)
    a6h1["short_overlap_ge2_fraction"] = round(side_overlap_fraction(ab4, cb4, "short", 2), 4)
    a6h1["gate_no_70pct_2of3_side_sharing"] = (a6h1["long_overlap_ge2_fraction"] < 0.70
                                               and a6h1["short_overlap_ge2_fraction"] < 0.70)
    a6h1["gate_skip_never_triggered"] = a6h1["min_elig"] >= 6
    a6h1["identifiable"] = (a6h1["gate_mean_abs_below_0.60"]
                            and a6h1["gate_no_70pct_2of3_side_sharing"])
    anch_ch4 = basket_changes(ab4)
    a6h1["anchor_legs_changed_per_transition"] = [c["legs_changed"] for c in anch_ch4]
    a6h1["anchor_membership_changes_total"] = int(sum(c["legs_changed"] for c in anch_ch4))
    OUT["a6_h1"] = a6h1
    print("a6_h1: mean|rho|", a6h1["rho_mean_abs"], "max", a6h1["rho_max_abs"],
          "overlap L/S", a6h1["long_overlap_ge2_fraction"], a6h1["short_overlap_ge2_fraction"],
          "min_elig", a6h1["min_elig"], "identifiable", a6h1["identifiable"], flush=True)

    json.dump(OUT, open("sec_features_out.json", "w"), indent=1, default=str)
    print("wrote sec_features_out.json", flush=True)


if __name__ == "__main__":
    main()
