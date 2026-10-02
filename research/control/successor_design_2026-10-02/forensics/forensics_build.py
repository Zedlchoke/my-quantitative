#!/usr/bin/env python3
"""forensics_build.py — TRADE-FORENSICS lane, successor_design_2026-10-02.

Deterministic, read-only over committed PC12A Stage-C artifacts; writes ONLY
into this forensics/ directory. ANALYSIS ONLY: journal-row counting and
arithmetic. NO engine run, NO PnL replay (no excursion reconstruction), NO
sealed/S1 bytes, NO network.

Inputs (read-only):
  research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/diagnostics/stagec/
      ARMS/{POLICY,B1_ALWAYS_ON}/{journal.jsonl,metrics.json}
  research/control/successor_design_2026-10-02/analysis/census.json

Outputs (this dir):
  guard_spend_band_histogram.json   (Deliverable B.1 machine evidence)
  session_dst_alignment.json        (Deliverable B.2 machine evidence)
  verification_checks.json          (reconciliation arithmetic, both briefs)
  trade_inventory.json              (Deliverable A.1 machine consolidation)

Docket-carried constants (W/L/B round-trip counts, breakeven c, session
bucket PnL) are embedded here ONLY as citation anchors labeled
"CITED_FROM_DOCKET" after sample verification in verification_checks.json;
they are NOT recomputed (that would require excursion reconstruction =
PnL replay, banned for this lane).

Usage:  .venv/bin/python research/control/successor_design_2026-10-02/forensics/forensics_build.py
"""
from __future__ import annotations

import calendar
import collections
import json
import math
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]  # .../my-quantitative
ARMS = REPO / "research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/diagnostics/stagec/ARMS"
CENSUS = REPO / "research/control/successor_design_2026-10-02/analysis/census.json"
OUT = Path(__file__).resolve().parent

ARM_NAMES = {"POLICY": "POLICY", "B1_ALWAYS_ON": "B1"}
DIR_OF = {"POLICY": "POLICY", "B1": "B1_ALWAYS_ON"}  # short name -> arm dir

# ---------------------------------------------------------------- citations
DOCKET_CITATIONS = {
    "USDJPY": "terminal_review_2026-10-01/symbol_docket/USDJPY_DOCKET.md",
    "EURUSD_GBPUSD": "terminal_review_2026-10-01/symbol_docket/EURGBP_DOCKET.md",
}
CITED_ROUNDT_TRIPS = {  # [M: prior dockets, carried forward; not recomputed]
    "USDJPY": {
        "POLICY": {"n": 393, "W": 157, "L": 224, "B": 12,
                   "docket_excursion_sum_net": 602943.11,
                   "docket_excursion_sum_net_defect": ("docket A section 0 sums swap with the WRONG SIGN "
                       "(fills + swap). True journal net = fills - swap = engine fold records "
                       "= 600,082.92 exactly; the docket's '2,860.19 residual / fold-edge mark "
                       "convention' equals exactly 2x swap. Measured this lane."),
                   "true_journal_net_engine_exact": 600082.92,
                   "friction": 128073.06, "force_flats": 4, "c_breakeven": 239.54},
        "B1": {"n": 310, "W": 135, "L": 163, "B": 12,
               "docket_excursion_sum_net": 689713.59,
               "docket_excursion_sum_net_defect": ("same swap-sign defect: true net = fills - swap "
                   "= 687,284.31 exactly; docket gap 2,429.28 = 2x swap"),
               "true_journal_net_engine_exact": 687284.31,
               "friction": 106651.05, "force_flats": 5, "c_breakeven": 239.54},
        "pooled_per_fold_WLB": {"0": [42, 56, 6], "1": [38, 46, 2], "2": [33, 48, 1],
                                "3": [37, 51, 3], "4": [24, 33, 4], "5": [42, 57, 0],
                                "6": [37, 58, 3], "7": [39, 38, 5]},
    },
    "EURUSD": {
        "POLICY": {"n": 182, "W": 92, "L": 85, "B": 5, "net_usd": 2315.2, "c_breakeven": 3.35,
                   "per_fold_net_usd": [999, 1216, 110, 96, 301, -346, -134, 74]},
        "B1": {"n": 250, "W": 121, "L": 119, "B": 10, "net_usd": 600.1, "c_breakeven": 3.37,
               "per_fold_net_usd": [999, 1402, -431, 85, -67, 186, -1696, 123]},
    },
    "GBPUSD": {
        "POLICY": {"n": 273, "W": 125, "L": 136, "B": 12, "net_usd": 942.4, "c_breakeven": 2.12,
                   "per_fold_net_usd": [166, 176, 196, -48, 143, -249, 343, 216]},
        "B1": {"n": 284, "W": 128, "L": 138, "B": 18, "net_usd": 718.7, "c_breakeven": 2.12,
               "per_fold_net_usd": [166, 176, 196, -48, 143, -351, 199, 238]},
    },
}
GUARD_DEFER_RE = re.compile(
    r"L6 cost guard: trailing 28d spend ([0-9.]+) >= cap ([0-9.]+)")


# ---------------------------------------------------------------- helpers
def iter_journal(arm: str):
    with open(ARMS / arm / "journal.jsonl") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def last_sunday(year: int, month: int):
    last_day = calendar.monthrange(year, month)[1]
    d = datetime(year, month, last_day, tzinfo=timezone.utc)
    return d - timedelta(days=(d.weekday() - 6) % 7)


def is_bst(dt_utc: datetime) -> bool:
    """BST (Europe/London DST): last Sunday of March 01:00 UTC -> last Sunday
    of October 01:00 UTC. All buckets analyzed sit at hours >= 12 UTC, i.e.
    after the 01:00 UTC transition instant, so date-level classification is
    exact for every row counted here."""
    start = last_sunday(dt_utc.year, 3)
    end = last_sunday(dt_utc.year, 10)
    return start <= dt_utc < end


def quantiles(sorted_vals, q):
    if not sorted_vals:
        return None
    idx = (len(sorted_vals) - 1) * q
    lo, hi = math.floor(idx), math.ceil(idx)
    if lo == hi:
        return sorted_vals[int(idx)]
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (idx - lo)


def r2(x):
    return None if x is None else round(x, 2)


# ---------------------------------------------------------------- main scan
def scan_arms():
    """One pass per arm; collect everything the evidence files need."""
    data = {}
    for arm_dir, arm in ARM_NAMES.items():
        rows = {"DECISION": 0, "NET_ORDER": 0, "SWAP": 0, "BLOCK": 0,
                "DEFER": 0, "NETTED_TO_ZERO": 0}
        per_leg = collections.defaultdict(lambda: collections.Counter())
        defers = []            # dict per DEFER row
        sym_cash = collections.defaultdict(float)   # NET_ORDER cash sums
        sym_swap = collections.defaultdict(float)   # SWAP sums (signed)
        sym_comm_cross = collections.defaultdict(float)
        cross_identity_ok = True                    # spread_once+slip==cross_cost
        jpy_ny_long = collections.Counter()          # (YYYY-MM, hour) -> n
        jpy_ny_long_dst = collections.Counter()      # (dst, hour) -> n
        eur_hours = collections.Counter()            # (YYYY-MM, hour) -> n
        eur_hours_dst = collections.Counter()
        eur_hours_dir = collections.Counter()        # (dst, hour, vote) -> n
        n_cross_checked = 0
        for r in iter_journal(arm_dir):
            kind = r.get("row_kind")
            if kind not in rows:
                continue
            rows[kind] += 1
            leg = r.get("leg_id")
            sym = r.get("symbol")
            if kind == "DECISION":
                if leg:
                    per_leg[leg]["decisions"] += 1
                    if r.get("direction_vote"):
                        per_leg[leg]["decisions_nonzero_vote"] += 1
                ts = r.get("ts_decision_utc")
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                hour = dt.hour
                vote = r.get("direction_vote") or 0
                if sym == "USDJPY" and vote == 1 and 16 <= hour < 21:
                    jpy_ny_long[(f"{dt.year}-{dt.month:02d}", hour)] += 1
                    jpy_ny_long_dst[("BST" if is_bst(dt) else "GMT", hour)] += 1
                if sym == "EURUSD" and hour in (12, 16) and vote != 0:
                    eur_hours[(f"{dt.year}-{dt.month:02d}", hour)] += 1
                    phase = "BST" if is_bst(dt) else "GMT"
                    eur_hours_dst[(phase, hour)] += 1
                    eur_hours_dir[(phase, hour, vote)] += 1
            elif kind == "NET_ORDER":
                per_leg_none = per_leg["null"]
                per_leg_none["fills"] += 1
                sym_cash[sym] += r.get("cash_delta_usd") or 0.0
                sym_comm_cross[sym] += (r.get("commission_usd") or 0.0) + \
                                       (r.get("cross_cost_usd") or 0.0)
                n_cross_checked += 1
                if abs((r.get("spread_once_usd") or 0) +
                       (r.get("slip_beyond_halfspread_usd") or 0) -
                       (r.get("cross_cost_usd") or 0)) > 1e-6:
                    cross_identity_ok = False
            elif kind == "SWAP":
                sym_swap[sym] += r.get("swap_usd") or 0.0
            elif kind == "BLOCK":
                per_leg[leg]["blocked"] += 1
                if (r.get("eligibility_rule_id") or "").startswith("E"):
                    per_leg[leg]["block_E1"] += 1
            elif kind == "NETTED_TO_ZERO":
                per_leg[leg]["netted_zero"] += 1
            elif kind == "DEFER":
                per_leg[leg]["deferred"] += 1
                g = r.get("guard") or {}
                m = GUARD_DEFER_RE.match(r.get("blocked_reason_detail") or "")
                defers.append({
                    "seq": r["seq"],
                    "ts_decision_utc": r.get("ts_decision_utc"),
                    "fold_id": r.get("fold_id"),
                    "leg_id": leg,
                    "symbol": sym,
                    "direction_vote": r.get("direction_vote"),
                    "spend_str": float(m.group(1)) if m else None,
                    "cap_str": float(m.group(2)) if m else None,
                    "spend_struct": g.get("trailing_spend_usd"),
                    "cap_struct": g.get("cap_usd"),
                    "window_days": g.get("window_days"),
                })
        data[arm] = {
            "row_counts": rows,
            "per_leg": {k: dict(v) for k, v in sorted(per_leg.items())},
            "defers": defers,
            "sym_cash": dict(sym_cash),
            "sym_swap": dict(sym_swap),
            "sym_comm_cross": dict(sym_comm_cross),
            "cross_identity_ok": cross_identity_ok,
            "n_cross_checked": n_cross_checked,
            "jpy_ny_long_month_hour": {f"{k[0]}|{k[1]}": v
                                       for k, v in sorted(jpy_ny_long.items())},
            "jpy_ny_long_dst_hour": {f"{k[0]}|{k[1]}": v
                                     for k, v in sorted(jpy_ny_long_dst.items())},
            "eur_hours_month_hour": {f"{k[0]}|{k[1]}": v
                                     for k, v in sorted(eur_hours.items())},
            "eur_hours_dst_hour": {f"{k[0]}|{k[1]}": v
                                   for k, v in sorted(eur_hours_dst.items())},
            "eur_hours_dst_hour_vote": {f"{k[0]}|{k[1]}|{k[2]}": v
                                        for k, v in sorted(eur_hours_dir.items())},
        }
    return data


# ------------------------------------------------- B.1 guard spend-band
def guard_analysis(data):
    out = {"purpose": ("J3 grid-node feasibility counts: for node m (cap x m), "
                       "a DEFER row with spend X >= m*cap would still defer "
                       "(TRUE defer under m); X < m*cap would be ADMITTED. "
                       "Counts of DECISION rows under a counterfactual "
                       "threshold ONLY - NOT marginal PnL. Admitted-set PnL "
                       "is measurable only by full-path replay (never by "
                       "arithmetic on these journals)."),
           "caveat_endogeneity": ("Under a counterfactual cap the trailing "
                                  "28d spend path itself evolves differently "
                                  "(admitted fills add spend, and subsequent "
                                  "netting changes later decisions); the "
                                  "static counts below are an upper-bound-"
                                  "style ordering tool, not a simulation."),
           "citations": {"cap_2836.97": "USDJPY_DOCKET.md H1; HYPOTHESIS_REGISTER A-H1/SU-RS-J3"},
           "arms": {}}
    for arm in ("POLICY", "B1"):
        defers = data[arm]["defers"]
        n = len(defers)
        caps = sorted({d["cap_struct"] for d in defers})
        string_parse_ok = all(d["spend_str"] is not None for d in defers)
        string_vs_struct_ok = all(
            abs(d["spend_str"] - round(d["spend_struct"], 4)) < 5e-5 and
            abs(d["cap_str"] - d["cap_struct"]) < 5e-5 for d in defers)
        ratios = sorted(d["spend_struct"] / d["cap_struct"] for d in defers)
        dist = {
            "n": n,
            "mean": r2(sum(ratios) / n),
            "min": r2(ratios[0]),
            "q25": r2(quantiles(ratios, 0.25)),
            "median": r2(quantiles(ratios, 0.50)),
            "q75": r2(quantiles(ratios, 0.75)),
            "q90": r2(quantiles(ratios, 0.90)),
            "q95": r2(quantiles(ratios, 0.95)),
            "max": r2(ratios[-1]),
            "share_ge_1p1": r2(sum(1 for r in ratios if r >= 1.1) / n),
            "share_ge_1p2": r2(sum(1 for r in ratios if r >= 1.2) / n),
            "share_ge_1p5": r2(sum(1 for r in ratios if r >= 1.5) / n),
            "share_ge_2p0": r2(sum(1 for r in ratios if r >= 2.0) / n),
        }
        nodes = {}
        for m in (1.5, 2.0, math.inf):
            label = "inf" if math.isinf(m) else str(m)
            per_fold = collections.OrderedDict()
            for f in range(8):
                rows_f = [d for d in defers if d["fold_id"] == f]
                true_d = sum(1 for d in rows_f if d["spend_struct"] >= m * d["cap_struct"])
                per_fold[str(f)] = {"true_defer": true_d,
                                    "admitted": len(rows_f) - true_d,
                                    "total": len(rows_f)}
            tot_true = sum(v["true_defer"] for v in per_fold.values())
            nodes[label] = {
                "threshold_rule": "defer iff trailing_spend >= "
                                  + ("INF (guard never fires)" if math.isinf(m)
                                     else f"{label} x cap"),
                "pooled": {"true_defer": tot_true, "admitted": n - tot_true,
                           "total": n},
                "per_fold": per_fold,
                "folds_with_admitted_ge_3": sum(1 for v in per_fold.values()
                                                 if v["admitted"] >= 3),
                "folds_with_admitted_lt_3": sum(1 for v in per_fold.values()
                                                 if 0 < v["admitted"] < 3),
                "note": ("m=inf: every observed defer is admitted (guard off); "
                         "matches the register's 'inf node VAL pooled ~248' "
                         "scale only in kind - see brief for the feasibility "
                         "reading against floors >=20/window, >=3/fold"
                         if math.isinf(m) else
                         "counts under static counterfactual threshold; "
                         "spend-path endogeneity caveat applies"),
                "key_finding": ("observed defer ratios never reach 1.5 "
                                "(max 1.20 POLICY / 1.41 B1): on the fired-"
                                "defer corpus the m=1.5, m=2.0 and m=inf "
                                "nodes are IDENTICAL in static count (all "
                                "admitted)"),
            }
        out["arms"][arm] = {
            "n_defer_rows": n,
            "cap_values_observed": caps,
            "cap_constant_2836.97": caps == [2836.97],
            "string_parse_ok_all_rows": string_parse_ok,
            "string_vs_struct_guard_field_agree": string_vs_struct_ok,
            "window_days_observed": sorted({d["window_days"] for d in defers}),
            "ratio_r_distribution": dist,
            "node_counts": nodes,
            "defer_rows_by_direction_vote": {
                str(v): n for v, n in sorted(collections.Counter(
                    d["direction_vote"] for d in defers).items())},
            "defer_rows_by_leg": dict(collections.Counter(d["leg_id"] for d in defers)),
            "defer_rows_by_fold": dict(sorted(collections.Counter(
                d["fold_id"] for d in defers).items())),
        }
    return out


# ------------------------------------------------- B.2 session / DST
def session_dst(data):
    def month_table(counter):
        months = sorted({k.split("|")[0] for k in counter})
        hours = sorted({int(k.split("|")[1]) for k in counter})
        return {
            "hours": hours,
            "months": {m: {str(h): counter.get(f"{m}|{h}", 0) for h in hours}
                       for m in months},
            "month_totals": {m: sum(counter.get(f"{m}|{h}", 0) for h in hours)
                             for m in months},
            "hour_totals": {str(h): sum(counter.get(f"{m}|{h}", 0)
                                        for m in months) for h in hours},
            "grand_total": sum(counter.values()),
        }

    def dst_table(counter):
        phases = ["GMT", "BST"]
        hours = sorted({int(k.split("|")[1]) for k in counter})
        tbl = {p: {str(h): counter.get(f"{p}|{h}", 0) for h in hours} for p in phases}
        gmt = sum(tbl["GMT"].values())
        bst = sum(tbl["BST"].values())
        return {"by_phase_hour": tbl,
                "phase_totals": {"GMT_winter": gmt, "BST_summer": bst,
                                 "grand_total": gmt + bst},
                "BST_share": r2(bst / (bst + gmt)) if (bst + gmt) else None}

    out = {
        "purpose": ("Descriptive DST-phase composition of the two negative "
                    "admission buckets named by the prior dockets. COUNTS of "
                    "DECISION rows only - no PnL is computed here; PnL by "
                    "DST phase is NOT_RUN under this lane (needs excursion "
                    "reconstruction = PnL replay)."),
        "dst_rule": ("Europe/London: BST from last Sunday of March 01:00 UTC "
                     "to last Sunday of October 01:00 UTC; date-level "
                     "classification exact for hours >= 12 UTC."),
        "london_close_overlay": {
            "GMT_winter": "London 16:00 close = 15:00 UTC; NY (EST=UTC-5) local for UTC hours 16-20 = 11:00-16:00; hour offset from London close = utc_hour - 15",
            "BST_summer": "London 16:00 close = 14:00 UTC; NY (EDT=UTC-4) local for UTC hours 16-20 = 12:00-17:00; hour offset from London close = utc_hour - 14",
            "reading": ("The fixed UTC bucket [16,21) starts 1h after London "
                        "close in winter but 2h after in summer and spans a "
                        "different NY-local window (11-16 vs 12-17): any "
                        "succession rule keyed to this bucket must be "
                        "declared in UTC-with-DST-phase or local-clock "
                        "terms, not bare UTC."),
        },
        "buckets": {},
    }
    for arm in ("POLICY", "B1"):
        d = data[arm]
        out["buckets"][arm] = {
            "USDJPY_NY_long_vote1_hour_16_20": {
                "definition": "DECISION rows, symbol USDJPY, direction_vote=+1, UTC hour in [16,21)",
                "month_x_hour": month_table(d["jpy_ny_long_month_hour"]),
                "dst_phase": dst_table(d["jpy_ny_long_dst_hour"]),
            },
            "EURUSD_hours_12_16_nonzero_vote": {
                "definition": "DECISION rows, symbol EURUSD, UTC hour in {12,16}, direction_vote != 0",
                "month_x_hour": month_table(d["eur_hours_month_hour"]),
                "dst_phase": dst_table(d["eur_hours_dst_hour"]),
                "dst_phase_by_vote": {k: v for k, v in
                                      sorted(d["eur_hours_dst_hour_vote"].items())},
            },
        }
    # corpus view: B1 decision stream is the superset (POLICY subset, census)
    out["corpus_note"] = ("B1_ALWAYS_ON's DECISION stream is the corpus "
                          "superset (3,467 points; POLICY 3,124 subset - "
                          "census.json decision_dedup). Use B1 for "
                          "market-structure composition; POLICY for the "
                          "scored policy's own bucket.")
    return out


# ------------------------------------------------- verification checks
def verification(data, census):
    checks = []
    ok = True

    def add(name, status, detail):
        nonlocal ok
        if status in ("MISMATCH", "FAIL"):
            ok = False
        checks.append({"check": name, "status": status, "detail": detail})

    # 1. row census vs census.json
    for arm, ckey in (("POLICY", "POLICY"), ("B1", "B1_ALWAYS_ON")):
        ref = census["arms"][ckey]["row_counts"]
        got = {k: v for k, v in data[arm]["row_counts"].items() if v}
        add(f"row_census[{arm}] vs census.json",
            "PASS" if got == ref else "MISMATCH", {"recount": got, "census": ref})

    # 2. per-leg blocked/deferred/netted vs census.json per_leg_inventory
    for arm, ckey in (("POLICY", "POLICY"), ("B1", "B1_ALWAYS_ON")):
        ref = census["per_leg_inventory"][ckey]
        mine = data[arm]["per_leg"]
        diffs = {}
        for leg, refc in ref.items():
            if leg == "null":
                continue
            gotc = {k: mine.get(leg, {}).get(k, 0)
                    for k in ("decisions", "decisions_nonzero_vote",
                              "blocked", "block_E1", "deferred", "netted_zero")
                    if refc.get(k)}
            if gotc != {k: v for k, v in refc.items() if k in gotc}:
                diffs[leg] = {"recount": gotc, "census": refc}
        add(f"per_leg_inventory[{arm}] vs census.json",
            "PASS" if not diffs else "MISMATCH", diffs or "all legs agree")

    # 3. guard cap constancy + string/struct agreement (both arms)
    for arm in ("POLICY", "B1"):
        dd = data[arm]["defers"]
        caps = {d["cap_struct"] for d in dd}
        agree = all(abs(d["spend_str"] - round(d["spend_struct"], 4)) < 5e-5
                    and d["cap_str"] == d["cap_struct"] for d in dd)
        add(f"guard_cap_constancy[{arm}]",
            "PASS" if caps == {2836.97} else "MISMATCH",
            {"caps": sorted(caps), "n": len(dd),
             "string_vs_struct_agree": agree,
             "cited_cap": 2836.97})

    # 4. fill cost identity: spread_once + slip == cross_cost on every fill
    for arm in ("POLICY", "B1"):
        add(f"fill_cost_identity[{arm}] (spread_once+slip==cross_cost)",
            "PASS" if data[arm]["cross_identity_ok"] else "FAIL",
            {"rows_checked": data[arm]["n_cross_checked"]})

    # 5. journal symbol net identity: fills - swap (swap_usd positive = cost
    #    outflow; all SWAP rows positive in both arms) vs engine fold sums.
    #    DEFECT CHECK: docket A section 0 states excursion sum_net = fills +
    #    swap (602,943.11) and explains the 2,860.19 gap to engine fold
    #    records as 'fold-edge mark convention'; measured here, the gap is
    #    exactly 2x swap in both arms and fills - swap reconciles to the
    #    engine to the cent on every cell.
    for arm in ("POLICY", "B1"):
        metrics = json.load(open(ARMS / DIR_OF[arm] / "metrics.json"))
        for sym in ("USDJPY", "EURUSD", "GBPUSD"):
            cash = data[arm]["sym_cash"][sym]
            swap = data[arm]["sym_swap"][sym]
            jrn = cash - swap
            rec = metrics["per_symbol_fold_records"][sym]
            eng = sum(v["cash_end"] - v["cash_start"] for v in rec.values())
            add(f"journal_net_identity[{arm},{sym}]: fills-swap == engine_fold_sum",
                "PASS" if abs(jrn - eng) <= 0.01 else "MISMATCH",
                {"fills": r2(cash), "swap": r2(swap), "fills_minus_swap": r2(jrn),
                 "engine_fold_sum": r2(eng), "delta": r2(jrn - eng),
                 "note": "identity convention per GATING_VS_SIZING fold cash law"})
    for arm, cited_sum in (("POLICY", 602943.11), ("B1", 689713.59)):
        swap = data[arm]["sym_swap"]["USDJPY"]
        cash = data[arm]["sym_cash"]["USDJPY"]
        true_net = cash - swap
        add(f"DOCKET_A_DEFECT[{arm},USDJPY] excursion sum_net swap sign",
            "DEFECT_QUANTIFIED",
            {"docket_excursion_sum_net": cited_sum,
             "true_journal_net_fills_minus_swap": r2(true_net),
             "gap": r2(cited_sum - true_net),
             "two_x_swap": r2(2 * swap),
             "gap_equals_two_x_swap": abs((cited_sum - true_net) - 2 * swap) < 0.02,
             "docket_explanation_of_gap": ("'2,860.19 (0.48%) - fold-edge mark "
                                           "convention in the rollup' (docket A sec 0)"),
             "measured_explanation": ("swap added with wrong sign in the docket's "
                                      "excursion net convention; with the correct "
                                      "sign the reconciliation to engine fold "
                                      "records is exact ($0.000)"),
             "impact": ("every ABSOLUTE USDJPY sum_net printed in docket A "
                        "(per-arm sums, pooled W/L/B outcome sums, and any "
                        "derived means) is overstated by exactly 1x swap "
                        "(+1,430.10 POLICY / +1,214.64 B1, 0.2-0.5%); W/L/B "
                        "classification (c=239.54 friction median) and all "
                        "relative POLICY-vs-B1 statements are unaffected; the "
                        "successor packet elsewhere (dossiers/complementarity/"
                        "census) quotes the correct engine numbers "
                        "600,082.92/687,284.31")})

    # 5b. EUR/GBP docket-cited nets vs journal identity (docket B subtracts
    #     swap correctly: net = gross - costs - swap)
    for arm, sym, cited in (("POLICY", "EURUSD", 2315.2), ("B1", "EURUSD", 600.1),
                            ("POLICY", "GBPUSD", 942.4), ("B1", "GBPUSD", 718.7)):
        jrn = data[arm]["sym_cash"][sym] - data[arm]["sym_swap"][sym]
        add(f"docket_B_cited_net[{arm},{sym}] vs journal fills-swap",
            "PASS" if abs(jrn - cited) <= 1.0 else "MISMATCH",
            {"journal": r2(jrn), "docket_cited": cited,
             "delta": r2(jrn - cited),
             "note": "docket B convention subtracts swap; consistent"})

    # 7. USDJPY friction vs metrics cost bill (docket claims EXACT)
    for arm_dir, arm in ARM_NAMES.items():
        metrics = json.load(open(ARMS / arm_dir / "metrics.json"))
        cb = metrics["per_symbol"]["USDJPY"]["cost_bill_totals_usd"]
        bill = (cb["commission"] + cb["slip"] + cb["spread_once"] + cb["swap"])
        jour = data[arm]["sym_comm_cross"]["USDJPY"] + \
            abs(data[arm]["sym_swap"]["USDJPY"])
        add(f"usdjpy_friction[{arm}] vs metrics cost_bill",
            "PASS" if abs(bill - jour) <= 0.02 else "MISMATCH",
            {"cost_bill_sum": r2(bill), "journal_comm_cross_plus_abs_swap": r2(jour),
             "delta": r2(bill - jour),
             "docket_cited_friction":
                 128073.06 if arm == "POLICY" else 106651.05})

    # 8. docket-cited EUR/GBP per-fold nets vs engine fold records (<= $1)
    docket_folds = {
        ("POLICY", "EURUSD"): [999, 1216, 110, 96, 301, -346, -134, 74],
        ("B1", "EURUSD"): [999, 1402, -431, 85, -67, 186, -1696, 123],
        ("POLICY", "GBPUSD"): [166, 176, 196, -48, 143, -249, 343, 216],
        ("B1", "GBPUSD"): [166, 176, 196, -48, 143, -351, 199, 238],
    }
    for (arm, sym), cited in docket_folds.items():
        metrics = json.load(open(ARMS / DIR_OF[arm] / "metrics.json"))
        rec = metrics["per_symbol_fold_records"][sym]
        worst = 0.0
        per_fold = {}
        for f in range(8):
            eng = rec[str(f)]["cash_end"] - rec[str(f)]["cash_start"]
            d = eng - cited[f]
            per_fold[str(f)] = {"engine": r2(eng), "docket": cited[f],
                                "delta": r2(d)}
            worst = max(worst, abs(d))
        add(f"docket_perfold_nets[{arm},{sym}] vs engine (claim <= $1)",
            "PASS" if worst <= 1.5 else "MISMATCH",
            {"worst_abs_delta": r2(worst), "per_fold": per_fold,
             "caveat": ("docket prints integer-rounded per-fold nets, so a "
                        "true <= $1.0 reconstruction delta can appear as up "
                        "to $1.5 against the engine; worst observed 1.11 "
                        "(B1 EURUSD f2) is within that printing tolerance - "
                        "the docket's <= $1 claim is neither falsified nor "
                        "exactly verifiable from printed integers")})

    # 9. USDJPY pooled per-fold W/L/B internal sums vs arm totals (docket A)
    pooled = CITED_ROUNDT_TRIPS["USDJPY"]["pooled_per_fold_WLB"]
    W = sum(v[0] for v in pooled.values())
    L = sum(v[1] for v in pooled.values())
    B = sum(v[2] for v in pooled.values())
    P, Bb = CITED_ROUNDT_TRIPS["USDJPY"]["POLICY"], CITED_ROUNDT_TRIPS["USDJPY"]["B1"]
    add("docket_usdjpy_pooled_WLB internal consistency (393+310=703; W/L/B arms sum)",
        "PASS" if (W, L, B) == (P["W"] + Bb["W"], P["L"] + Bb["L"],
                                P["B"] + Bb["B"]) and W + L + B == 703
        else "MISMATCH",
        {"pooled_WLB": [W, L, B],
         "arms_sum": [P["W"] + Bb["W"], P["L"] + Bb["L"], P["B"] + Bb["B"]]})

    # 10. EUR/GBP W/L/B internal consistency
    for sym in ("EURUSD", "GBPUSD"):
        P = CITED_ROUNDT_TRIPS[sym]["POLICY"]
        Bb = CITED_ROUNDT_TRIPS[sym]["B1"]
        add(f"docket_{sym}_WLB sums vs n",
            "PASS" if P["W"] + P["L"] + P["B"] == P["n"] and
            Bb["W"] + Bb["L"] + Bb["B"] == Bb["n"] else "MISMATCH",
            {"POLICY": [P["W"], P["L"], P["B"], P["n"]],
             "B1": [Bb["W"], Bb["L"], Bb["B"], Bb["n"]]})

    return {"all_pass": ok,
            "defects_found": [c for c in checks if c["status"] == "DEFECT_QUANTIFIED"],
            "checks": checks}


# ------------------------------------------------- A.1 inventory
def inventory(data, census):
    inv = {
        "provenance": {
            "round_trips_WLB": "CITED_FROM_DOCKET (not recomputed; sample-verified in verification_checks.json)",
            "blocked_deferred_netted": "[M] recount from journals (this script), cross-checked vs analysis/census.json per_leg_inventory",
            "cost_labels": {
                "bands": "DECLARED bands, PROVISIONAL_PENDING_COST_AUTHORITY (FILL_ACCOUNTING_SPEC section 3)",
                "measured_cells": "C1 general 0.5/0.9 pips p50/p90; C2 Mon-Thu (21:00,22:00] roll 2.1/7.4 (n=64,892); C2 Fri 0.8/1.8; C3 Sunday reopen 11.0/22.0 [M: DATA_AUDIT D]",
                "par_convention": "USDJPY cash_delta_usd carried at par from JPY notional (no /rate); SWAP rows rate-converted; absolute USD magnitudes scale ~1/USDJPY-rate under explicit conversion (docket A units caveat)",
                "slip_commission": "Slip U3 0.2 pip non-event / 1.0 event; commission U2 0.35 bps/side; swap U4/U5 1 pip/night, Wed x3 (DECLARED)",
            },
        },
        "citations": DOCKET_CITATIONS,
        "per_symbol": {},
    }
    cited = CITED_ROUNDT_TRIPS
    legs_by_symbol = {"USDJPY": ["USDJPY-S002", "USDJPY-S003", "USDJPY-S014",
                                 "USDJPY-S023", "USDJPY-S026",
                                 "VC2-LVNFAIL-USDJPY"],
                      "EURUSD": ["EURUSD-S009", "EURUSD-S013", "EURUSD-S046",
                                 "VC2-LVNFAIL-EURUSD"],
                      "GBPUSD": ["GBPUSD-S002", "GBPUSD-S017"]}
    for sym in ("USDJPY", "EURUSD", "GBPUSD"):
        inv["per_symbol"][sym] = {
            "round_trips": {
                "POLICY": cited[sym]["POLICY"],
                "B1": cited[sym]["B1"],
                **({"pooled_per_fold_WLB": cited[sym]["pooled_per_fold_WLB"]}
                   if sym == "USDJPY" else {}),
            },
            "blocked_deferred_netted_by_leg": {
                arm: {leg: data[arm]["per_leg"].get(leg, {})
                      for leg in legs_by_symbol[sym]}
                for arm in ("POLICY", "B1")
            },
        }
    inv["supermajority_block_metrics_only"] = {
        "note": ("no journal rows in either arm; per-leg counts from metrics "
                 "fills_by_outcome (census section 3.2): S026 706, S014 186, "
                 "S002(JPY) 55, S003 20, VC2-JPY 22; portfolio POLICY 659 vs "
                 "B1 1,021"),
        "pnl_attribution": "NOT_RUN (closest proxy pathdown_policy_sizing_netting -31,686 [derived])",
    }
    return inv


def main():
    data = scan_arms()
    census = json.load(open(CENSUS))

    guard = guard_analysis(data)
    with open(OUT / "guard_spend_band_histogram.json", "w") as fh:
        json.dump(guard, fh, indent=1, sort_keys=True)

    sess = session_dst(data)
    with open(OUT / "session_dst_alignment.json", "w") as fh:
        json.dump(sess, fh, indent=1, sort_keys=True)

    ver = verification(data, census)
    with open(OUT / "verification_checks.json", "w") as fh:
        json.dump(ver, fh, indent=1, sort_keys=True)

    inv = inventory(data, census)
    with open(OUT / "trade_inventory.json", "w") as fh:
        json.dump(inv, fh, indent=1, sort_keys=True)

    # console summary
    print("== verification:", "ALL PASS" if ver["all_pass"] else "SEE CHECKS")
    for c in ver["checks"]:
        if c["status"] != "PASS":
            print("  !!", c["check"], c["status"])
    for arm in ("POLICY", "B1"):
        g = guard["arms"][arm]
        r = g["ratio_r_distribution"]
        print(f"== guard[{arm}] n={r['n']} cap_const={g['cap_constant_2836.97']} "
              f"r: med={r['median']} q25={r['q25']} q75={r['q75']} "
              f"q90={r['q90']} q95={r['q95']} max={r['max']} "
              f"share>=1.5={r['share_ge_1p5']} share>=2.0={r['share_ge_2p0']}")
        for m in ("1.5", "2.0", "inf"):
            p = g["node_counts"][m]["pooled"]
            f3 = g["node_counts"][m]["folds_with_admitted_ge_3"]
            print(f"   node m={m}: true_defer={p['true_defer']} "
                  f"admitted={p['admitted']} folds(admitted>=3)={f3}")
    for arm in ("POLICY", "B1"):
        b = sess["buckets"][arm]
        j = b["USDJPY_NY_long_vote1_hour_16_20"]["dst_phase"]["phase_totals"]
        e = b["EURUSD_hours_12_16_nonzero_vote"]["dst_phase"]["phase_totals"]
        print(f"== session[{arm}] JPY-NY-long: GMT={j['GMT_winter']} "
              f"BST={j['BST_summer']} BST_share={b['USDJPY_NY_long_vote1_hour_16_20']['dst_phase']['BST_share']}"
              f" | EUR h12/16: GMT={e['GMT_winter']} BST={e['BST_summer']} "
              f"BST_share={b['EURUSD_hours_12_16_nonzero_vote']['dst_phase']['BST_share']}")
    print("written:", sorted(p.name for p in OUT.glob("*.json")))


if __name__ == "__main__":
    main()
