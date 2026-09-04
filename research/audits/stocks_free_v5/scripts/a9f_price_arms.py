"""A9-F coverage tables + price-only arm identifiability + turnover arithmetic.

Part 2 of the audit. Rebuilds panels from a persisted cache if present.
NO strategy PnL is computed anywhere: only PIT feature/rank arithmetic,
portfolio weight schedules (deterministic book construction) and closed-form
arithmetic. Book daily-return series are NOT computed.
"""

from __future__ import annotations

import json
import math
from datetime import date

import numpy as np

from a9f_lib import (
    SECTORS, S0_START,
    basket_changes, build_panel, fold_sessions, global_clock, iter_sec_records,
    load_close, load_panel_sectors, load_spy_calendar, quarterly_clock, rank_dict,
    session_at, side_overlap_fraction, spearman, store_sha256, to_normalized,
    top_bottom_book,
)

CACHE = "panels_cache.json"


def panel_key(field, gap):
    return f"{field}|gap{gap}"


def build_all_panels(kept, filer_sectors, cal):
    folds = fold_sessions([d for d in cal if S0_START <= d <= date(2025, 7, 31)])
    qticks = sorted(t for v in quarterly_clock(folds, 63, 567).values() for t in v)
    g42 = global_clock([d for d in cal if S0_START <= d <= date(2025, 7, 31)], 42)
    ref252 = sorted({session_at(cal, t, 252) for t in qticks})

    specs = [
        ("us-gaap:Assets", 400, qticks),
        ("us-gaap:Assets", 400, ref252),
        ("us-gaap:CashAndCashEquivalentsAtCarryingValue", 400, qticks),
        ("us-gaap:AssetsCurrent", 400, qticks),
        ("dei:EntityPublicFloat", 550, qticks),
        ("us-gaap:LiabilitiesAndStockholdersEquity", 550, qticks),
        ("us-gaap:AssetsCurrent", 200, g42),
        ("us-gaap:Assets", 200, g42),
    ]
    cache = {}
    for field, gap, sessions in specs:
        key = panel_key(field, gap)
        cache.setdefault(key, {})
        panel = build_panel(kept, filer_sectors, sessions, field, gap)
        for s in sorted(panel):
            obs = panel[s][s] if False else None
        for session in sessions:
            obs_map = panel.get(session, {})
            cache[key][str(session)] = {
                sec: {
                    "coverage": round(obs_map[sec].coverage, 4),
                    "eff": str(obs_map[sec].effective_date),
                    "value": obs_map[sec].value,
                    "n_incl": obs_map[sec].filers_included,
                    "n_map": obs_map[sec].filers_mapped,
                }
                for sec in obs_map
            }
        print("panel built:", key, len(sessions), "sessions", flush=True)
    json.dump(cache, open(CACHE, "w"))
    return cache


def load_or_build(kept, filer_sectors, cal):
    import os
    if os.path.exists(CACHE):
        return json.load(open(CACHE))
    return build_all_panels(kept, filer_sectors, cal)


# ---------------------------------------------------------------- helpers ----

def daily_returns(sym):
    px = load_close(sym, "_all_p1")
    dts = sorted(px)
    out = {}
    for a, b in zip(dts, dts[1:]):
        out[b] = px[b] / px[a] - 1.0
    return out, px


def windowed_vol_sq(ret: dict, cal: list, t: date, n: int):
    """mean of r(u)^2 over the n sessions ending at t (population, no demeaning)."""
    idx = cal.index(t)
    if idx < n:
        return None
    vals = []
    for k in range(idx - n + 1, idx + 1):
        r = ret.get(cal[k])
        if r is None:
            return None
        vals.append(r)
    return float(np.mean(np.square(vals)))


def main():
    cal = load_spy_calendar()
    s0 = [d for d in cal if S0_START <= d <= date(2025, 7, 31)]
    folds = fold_sessions(s0)
    qticks = quarterly_clock(folds, 63, 567)
    qtick_list = sorted(t for v in qticks.values() for t in v)
    seeds = {folds[f][0] for f in folds}
    g42 = global_clock(s0, 42)

    out = {}

    # ------------------------------------------------- panels (cache) -------
    import os
    if not os.path.exists(CACHE):
        print("streaming SEC store...", flush=True)
        kept = {f: [] for f in (
            "us-gaap:Assets", "us-gaap:AssetsCurrent",
            "us-gaap:CashAndCashEquivalentsAtCarryingValue",
            "dei:EntityPublicFloat", "us-gaap:LiabilitiesAndStockholdersEquity")}
        for obj in iter_sec_records(set(kept)):
            try:
                kept[obj["field"]].append(to_normalized(obj))
            except Exception:
                pass
        build_all_panels(kept, load_panel_sectors(), cal)
    cache = json.load(open(CACHE))
    out["panels_cached_keys"] = list(cache.keys())

    ASSETS = "us-gaap:Assets"
    CASH = "us-gaap:CashAndCashEquivalentsAtCarryingValue"
    CURR = "us-gaap:AssetsCurrent"
    FLOAT = "dei:EntityPublicFloat"
    LSE = "us-gaap:LiabilitiesAndStockholdersEquity"

    def P(field, gap, session):
        return cache[panel_key(field, gap)].get(str(session), {})

    # ------------------------------------- coverage tables (per proposal) ---
    def coverage_table(name, field_gap_pairs, sessions, floor, per_leg=True):
        """Per-sector per-slot coverage vs the declared floor."""
        table = {}
        below = {s: 0 for s in SECTORS}
        mins = {s: 1.0 for s in SECTORS}
        for t in sessions:
            row = {}
            for s in SECTORS:
                covs = []
                for field, gap in field_gap_pairs:
                    o = P(field, gap, t).get(s)
                    covs.append(o["coverage"] if o else 0.0)
                c = min(covs) if per_leg else float(np.mean(covs))
                row[s] = [round(x, 4) for x in covs]
                if c < floor:
                    below[s] += 1
                    mins[s] = min(mins[s], c)
            table[str(t)] = row
        return {
            "field_gap_pairs": [list(x) for x in field_gap_pairs],
            "declared_floor": floor,
            "n_slots": len(sessions),
            "per_slot_per_sector": table,
            "per_sector_slots_below_floor": below,
            "per_sector_min_coverage": {s: round(v, 4) for s, v in mins.items()},
        }

    # a4_h1: assets gap 400, floor 0.60 at t AND ref -> report t-side plus ref-side
    ref252 = {t: session_at(cal, t, 252) for t in qtick_list}
    ref_sessions = sorted(set(ref252.values()))
    out["cov_a4h1_tick"] = coverage_table("a4h1", [(ASSETS, 400)], qtick_list, 0.60)
    out["cov_a4h1_ref252"] = coverage_table("a4h1ref", [(ASSETS, 400)], ref_sessions, 0.60)
    out["cov_a4h2"] = coverage_table("a4h2", [(CASH, 400), (ASSETS, 400)], qtick_list, 0.60)
    out["cov_a5h1"] = coverage_table("a5h1", [(FLOAT, 550), (LSE, 550)], qtick_list, 0.60)
    out["cov_a6h1"] = coverage_table("a6h1", [(CURR, 200), (ASSETS, 200)], g42, 0.40)
    print("coverage tables done", flush=True)

    # newest-vintage cohort-size mechanism stat (assets gap 400 at 30 ticks)
    incl_all, mapv = [], None
    for t in qtick_list:
        for s, o in P(ASSETS, 400, t).items():
            incl_all.append(o["n_incl"])
            mapv = o["n_map"]
    out["single_vintage_cohort_stats_assets400"] = {
        "n_sector_ticks": len(incl_all),
        "median_filers_in_newest_vintage": int(np.median(incl_all)),
        "max": int(np.max(incl_all)),
        "panel_per_sector_typical": mapv,
        "fraction_sector_ticks_below_60pct": round(float(np.mean(
            [1 if i / (mapv or 1) < 0.60 else 0 for i in incl_all])), 4),
    }

    # ------------------------------------------------------- price arms -----
    rets, closes_all, closes_none = {}, {}, {}
    for s in ["SPY"] + list(SECTORS):
        rets[s], closes_all[s] = daily_returns(s)
        pxn = load_close(s, "_none_p1")
        closes_none[s] = pxn
    spy_ret = rets["SPY"]

    def hist_count(sym, t):
        return sum(1 for d in closes_all[sym] if d <= t)

    # ---- a5_h2 ----
    a5h2 = {"declared_gates": {
        "kill": "Spearman(anchor ranks, stale t-63 ranks) <= 0.90 at decision slots AND >= 25% of slots with >= 1 differing long/short membership leg",
        "overlay": "c_t = min(1, 0.10/sigma_book_ann(t)), sigma_book_ann = sqrt(252*mean(r_book^2, t-62..t)), banded DOWN to 0.10, recomputed only at slots"}}
    per_tick = []
    fresh_ranks, stale_ranks = {}, {}
    for fid in qticks:
        for t in qticks[fid]:
            sig = {}
            for s in SECTORS:
                if hist_count(s, t) < 63:
                    continue
                v = windowed_vol_sq(rets[s], cal, t, 63)
                if v is None:
                    continue
                sig[s] = math.sqrt(v)
            t_ref = cal[cal.index(t) - 63]
            sig_stale = {}
            for s in SECTORS:
                if hist_count(s, t_ref) < 63:
                    continue
                v = windowed_vol_sq(rets[s], cal, t_ref, 63)
                if v is None:
                    continue
                sig_stale[s] = math.sqrt(v)
            fresh_ranks[t] = rank_dict(sig, reverse=False)
            stale_ranks[t] = rank_dict(sig_stale, reverse=False)
            common = sorted(set(sig) & set(sig_stale))
            rho = spearman([sig[s] for s in common], [sig_stale[s] for s in common]) if len(common) >= 3 else float("nan")
            per_tick.append({"tick": str(t), "fold": fid, "n_elig_fresh": len(sig),
                             "n_stale": len(sig_stale), "n_common": len(common),
                             "rho_fresh_vs_stale": round(rho, 4)})
    a5h2["per_tick"] = per_tick
    rhos = [x["rho_fresh_vs_stale"] for x in per_tick]
    a5h2["rho_mean_abs"] = round(float(np.nanmean(np.abs(rhos))), 4)
    a5h2["rho_max_abs"] = round(float(np.nanmax(np.abs(rhos))), 4)
    ab5 = top_bottom_book(fresh_ranks)
    cb5 = top_bottom_book(stale_ranks)
    ticks5 = sorted(fresh_ranks)
    div = sum(1 for t in ticks5 if ab5[t]["long"] != cb5[t]["long"] or ab5[t]["short"] != cb5[t]["short"])
    a5h2["slots_with_membership_divergence"] = div
    a5h2["slots_total"] = len(ticks5)
    a5h2["divergence_fraction"] = round(div / len(ticks5), 4)
    a5h2["gate_rho_le_0.90_max"] = a5h2["rho_max_abs"] <= 0.90
    a5h2["gate_divergence_ge_25pct"] = a5h2["divergence_fraction"] >= 0.25
    a5h2["identifiable_strict_max_reading"] = a5h2["gate_rho_le_0.90_max"] and a5h2["gate_divergence_ge_25pct"]
    ch5 = basket_changes(ab5)
    a5h2["anchor_legs_changed_per_transition"] = [c["legs_changed"] for c in ch5]
    a5h2["anchor_membership_changes_total"] = int(sum(c["legs_changed"] for c in ch5))
    # measured sigma scale at first/last tick (feature arithmetic, not PnL)
    t0 = ticks5[0]
    a5h2["sigma63_scale_sample_first_tick"] = {s: round(math.sqrt(windowed_vol_sq(rets[s], cal, t0, 63)) * math.sqrt(252), 4)
                                               for s in SECTORS if s in fresh_ranks[t0]}
    out["a5_h2"] = a5h2
    print("a5_h2: mean|rho|", a5h2["rho_mean_abs"], "max", a5h2["rho_max_abs"],
          "div", a5h2["divergence_fraction"], flush=True)

    # ---- a6_h2 ----
    a6h2 = {"declared_gates": {
        "kill": "mean |rho| >= 0.60 across sessions OR >= 2 of 3 legs share the same side in >= 70% of sessions",
        "eligibility": ">= 252 sessions history AND >= 5 defined pairs (63-return Pearson)"}}
    per_tick = []
    anchor_ranks6, control_ranks6 = {}, {}
    for t in g42:
        elig = [s for s in SECTORS if hist_count(s, t) >= 252]
        # 63 returns ending at t
        def win(sym):
            idx = cal.index(t)
            vals = []
            for k in range(idx - 63 + 1, idx + 1):
                r = rets[sym].get(cal[k])
                if r is None:
                    return None
                vals.append(r)
            return vals
        wins = {s: win(s) for s in elig}
        corr = {}
        for i in elig:
            for j in elig:
                if i >= j:
                    continue
                vi, vj = wins[i], wins[j]
                if vi is None or vj is None:
                    continue
                si2, sj2 = float(np.var(vi)), float(np.var(vj))
                if si2 < 1e-12 or sj2 < 1e-12:
                    continue
                c = float(np.corrcoef(vi, vj)[0, 1])
                corr[(i, j)] = c
        coup = {}
        for i in elig:
            cs = [c for (a, b), c in corr.items() if i in (a, b)]
            if len(cs) >= 5:
                coup[i] = float(np.mean(cs))
        price = {s: closes_none[s][t] for s in elig if t in closes_none[s]}
        anchor_ranks6[t] = rank_dict(coup, reverse=False)
        control_ranks6[t] = rank_dict(price, reverse=False)
        common = sorted(set(coup) & set(price))
        rho = spearman([coup[s] for s in common], [price[s] for s in common]) if len(common) >= 3 else float("nan")
        per_tick.append({"tick": str(t), "n_eligible": len(elig), "n_defined_pairs_sectors": len(coup),
                         "rho_anchor_vs_nomprice": round(rho, 4)})
    a6h2["per_tick"] = per_tick
    rhos = [x["rho_anchor_vs_nomprice"] for x in per_tick]
    a6h2["rho_mean_abs"] = round(float(np.nanmean(np.abs(rhos))), 4)
    a6h2["rho_max_abs"] = round(float(np.nanmax(np.abs(rhos))), 4)
    a6h2["gate_mean_abs_below_0.60"] = a6h2["rho_mean_abs"] < 0.60
    ab6 = top_bottom_book(anchor_ranks6)
    cb6 = top_bottom_book(control_ranks6)
    a6h2["long_overlap_ge2_fraction"] = round(side_overlap_fraction(ab6, cb6, "long", 2), 4)
    a6h2["short_overlap_ge2_fraction"] = round(side_overlap_fraction(ab6, cb6, "short", 2), 4)
    a6h2["gate_no_70pct_2of3_side_sharing"] = (a6h2["long_overlap_ge2_fraction"] < 0.70
                                               and a6h2["short_overlap_ge2_fraction"] < 0.70)
    a6h2["min_eligible"] = min(x["n_eligible"] for x in per_tick)
    a6h2["gate_skip_never_triggered"] = a6h2["min_eligible"] >= 6
    a6h2["identifiable"] = a6h2["gate_mean_abs_below_0.60"] and a6h2["gate_no_70pct_2of3_side_sharing"]
    ch6 = basket_changes(ab6)
    a6h2["anchor_legs_changed_per_transition"] = [c["legs_changed"] for c in ch6]
    a6h2["anchor_membership_changes_total"] = int(sum(c["legs_changed"] for c in ch6))
    out["a6_h2"] = a6h2
    print("a6_h2: mean|rho|", a6h2["rho_mean_abs"], "max", a6h2["rho_max_abs"],
          "overlap L/S", a6h2["long_overlap_ge2_fraction"], a6h2["short_overlap_ge2_fraction"], flush=True)

    # ------------------------------------- turnover arithmetic (estimates) --
    def year_fraction(d0, d1):
        return (d1 - d0).days / 365.25

    def churn_turnover(book, legs_changed, per_leg_w, ticks_per_year, boundary_gross):
        legs = np.array(legs_changed, dtype=float)
        mean_changed = float(legs.mean()) if len(legs) else 0.0
        worst = float(legs.max()) if len(legs) else 0.0
        # exits+entries per transition = 2*legs_changed when basket sizes constant
        two_way_per_tick_mid = mean_changed * per_leg_w
        two_way_per_tick_max = worst * per_leg_w
        return {
            "legs_changed_mean_per_transition": round(mean_changed, 3),
            "legs_changed_max_per_transition": int(worst),
            "two_way_per_rebalance_mid": round(two_way_per_tick_mid, 4),
            "two_way_per_rebalance_max": round(two_way_per_tick_max, 4),
            "rebalance_component_mid_per_year": round(two_way_per_tick_mid * ticks_per_year, 3),
            "rebalance_component_max_per_year": round(two_way_per_tick_max * ticks_per_year, 3),
            "boundary_build_flat_component_per_year_upper": round(boundary_gross / 7.24, 3),
        }

    s0_years = year_fraction(date(2018, 4, 4), date(2025, 7, 31))
    ticks_per_year_q = 30 / s0_years
    ticks_per_year_42 = 44 / s0_years
    out["turnover_clock"] = {
        "s0_years": round(s0_years, 3),
        "quarterly_ticks_per_year": round(ticks_per_year_q, 3),
        "grid42_ticks_per_year": round(ticks_per_year_42, 3),
    }
    # per_leg_w: two-way |dw| of one replaced leg pair = 2*(1/6) if counting
    # exit+entry; legs_changed counts legs replaced on both sides already, so
    # each replaced leg contributes 2*(1/6) total (exit + entry).
    pw = 2 * (1.0 / 6.0)
    out["turnover_a5h2"] = churn_turnover(ab5, a5h2["anchor_legs_changed_per_transition"],
                                          pw, ticks_per_year_q, 1.0)
    out["turnover_a6h2"] = churn_turnover(ab6, a6h2["anchor_legs_changed_per_transition"],
                                          pw, ticks_per_year_42, 1.0)
    # overlay component for a5_h2: each 0.10 band step changes six legs of base
    # gross 1.0 -> two-way |dc|*1.0; declared expected |dc| 0.2-0.4 per decision.
    out["turnover_a5h2_overlay_component"] = {
        "note": "band step of 0.10 => 0.10 two-way per slot; declared |dc| 0.2-0.4",
        "declared_mid_per_year": round(0.3 * ticks_per_year_q, 3),
        "declared_max_per_year": round(0.4 * ticks_per_year_q, 3),
    }
    # a6 hedge leg: measured beta drift would need the arm's own weight history;
    # bounded by the truncation |dw_hedge| <= 0.25 per rebalance.
    out["turnover_a6_hedge_bound_per_year"] = round(0.25 * ticks_per_year_42, 3)

    # design-level worst cases (labeled upper bounds)
    out["turnover_design_upper_bounds"] = {
        "quarterly_3v3_full_reconstitution_per_year": round(2.0 * ticks_per_year_q + 1.0 / s0_years * 4, 2),
        "grid42_3v3_full_reconstitution_per_year": round(2.0 * ticks_per_year_42 + 1.0 / s0_years * 4, 2),
        "ceiling": 6.0,
    }

    json.dump(out, open("price_arms_out.json", "w"), indent=1, default=str)
    print("wrote price_arms_out.json", flush=True)


if __name__ == "__main__":
    main()
