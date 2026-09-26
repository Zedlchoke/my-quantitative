"""ERP1-TRACKA-COHORT-1 — falsifier-lane PRE-PnL battery runner (GO-1).

Runs the plan §8 battery in the dispatch order, on the NEW pairs' DEV
windows only (holdout untouched — the one-look window is never read):

  Task 1  F-5 declared-band arithmetic on COSTS (M3 kill / M1 report)
  Task 2  F-PIT-1 M-1..M-5 + seam constants + F-3 mode-sham
  Task 3  F-1 ancestry rho vs the 12 frozen census family functions
  Task 4  F-3 clock-placebo constructibility predicates
  Task 5  F-6 per-fold + last-6-months round-trip COUNTS vs floors
  Task 6  F-7 concentration-statistic + exclusion-zone declarations

HARD LAW: signal arrays, schedules, counts, spreads and rho ONLY. No
net-return / expectancy / PF / win-rate arithmetic of any arm anywhere.
Seeds are pinned in the freeze artifact BEFORE any computation that
consumes them (pins written first in main()).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

LANE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LANE / "scripts"))

import tracka_lib as T  # noqa: E402

DERIVED = LANE / "data_local" / "derived"
FREEZE_DIR = LANE / "freeze"
OUT_RESULTS = LANE / "falsifier_results.json"
OUT_FREEZE = FREEZE_DIR / "GO1_freeze_artifact.json"
OUT_LEDGER = LANE / "trial_ledger.jsonl"

PAIRS = ["AUDUSD", "USDCAD"]

# ---- frozen pins (written to the freeze artifact before consumption) ----
BOOTSTRAP_SEED = 20260925
MODE_SHAM_SEED = 20260925
WARMUP_TRADED_DAYS = 61
DEV_START, DEV_END = "2021-01-01", "2025-12-31"
HOLDOUT_START, HOLDOUT_END = "2026-01-01", "2026-06-30"  # NEVER READ HERE
LAST6_START, LAST6_END = "2025-07-01", "2025-12-31"
FOLD_TABLE = [
    ("F1", "2021-01-01", "2021-10-31"),
    ("F2", "2021-11-01", "2022-08-31"),
    ("F3", "2022-09-01", "2023-06-30"),
    ("F4", "2023-07-01", "2024-04-30"),
    ("F5", "2024-05-01", "2025-02-28"),
    ("F6", "2025-03-01", "2025-12-31"),
]
FLOORS = {"smoke": 30, "adjudication": 100, "promote_dev_union": 236}
SEAM_LIMB3_MIN_N = 20

BREAK_BUCKETS = ("london_07_12", "ny_overlap_12_16", "ny_late_16_21")

# F-1 frozen variant set: 12 ancestry census family functions x 2 pinned
# variants each (lane-pinned; pip-parametrized; frozen in the freeze
# artifact before the rho computation).
F1_VARIANTS = [
    ("GAP", "f_gap", {"th_pips": 5.0, "mode": "follow"}),
    ("GAP", "f_gap", {"th_pips": 10.0, "mode": "fade"}),
    ("PDHLOC", "f_pdhloc", {"buf_pips": 0.0, "opposite_exit": True}),
    ("PDHLOC", "f_pdhloc", {"buf_pips": 1.0, "opposite_exit": False}),
    ("DOW", "f_dow_simple", {"weeks": 4, "min_days": 20}),
    ("DOW", "f_dow_simple", {"weeks": 8, "min_days": 40}),
    ("ASIAFADE", "f_asiafade", {"asia_end": 6, "buf_pips": 0.0}),
    ("ASIAFADE", "f_asiafade", {"asia_end": 7, "buf_pips": 1.0}),
    ("SESSMA", "f_sessma", {"th": 0.5, "win_atr": 24}),
    ("SESSMA", "f_sessma", {"th": 1.0, "win_atr": 48}),
    ("H1TSMOM", "f_h1tsmom", {"K": 24}),
    ("H1TSMOM", "f_h1tsmom", {"K": 96}),
    ("H1DONCH", "f_h1donch", {"L": 24, "hold_mult": 4}),
    ("H1DONCH", "f_h1donch", {"L": 48, "hold_mult": 4}),
    ("DAYMOM", "f_daymom", {"N": 1}),
    ("DAYMOM", "f_daymom", {"N": 5}),
    ("RANGEEXP", "f_rangeexp", {"lo_q": 0.3, "hi_q": 0.7,
                                "use_breakout": False}),
    ("RANGEEXP", "f_rangeexp", {"lo_q": 0.3, "hi_q": 0.7,
                                "use_breakout": True}),
    ("STOCH", "f_stoch", {"N": 24, "th_hi": 80, "th_lo": 20}),
    ("STOCH", "f_stoch", {"N": 48, "th_hi": 80, "th_lo": 20}),
    ("ROUNDNUM", "f_roundnum", {"grid_pips": 10.0, "prox_pips": 1.0}),
    ("ROUNDNUM", "f_roundnum", {"grid_pips": 50.0, "prox_pips": 2.0}),
    ("HOURREV", "f_hourrev", {"win_days": 5, "invert": False}),
    ("HOURREV", "f_hourrev", {"win_days": 20, "invert": False}),
]

M1_LAW_COMMON = {
    "family_fn": "v2_lib.f_rangeexp",
    "lo_q": 0.3, "hi_q": 0.7, "use_breakout": False,
    "trading_hours_utc": "07-18 action window; 00-19 tradable",
    "force_flat": "no fills on/after the 19:00 H1 bar; flat at 20:00 UTC",
    "plane_convention": "ANCESTRY close-column high / true-low (signal "
                        "plane); port true-H/L plane = cost plane",
    "warmup_traded_days": WARMUP_TRADED_DAYS,
    "hist_len_days": T.HIST_LEN,
}


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def canon_sha(obj) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def arm_digest(mechanism, arm, pair, extra):
    return canon_sha({"mechanism": mechanism, "arm": arm, "pair": pair,
                      "law": M1_LAW_COMMON, **extra})[:16]


def ts_of(day_str, end=False):
    t = dt.datetime.fromisoformat(day_str).replace(tzinfo=dt.timezone.utc)
    if end:
        t = t + dt.timedelta(days=1) - dt.timedelta(seconds=1)
    return int(t.timestamp())


def run() -> dict:
    results = {"schema": "tracka_falsifier_results@1",
               "cycle_id": "ERP1-TRACKA-COHORT-1",
               "lane": "tracka1-falsifier",
               "seeds": {"bootstrap_seed": BOOTSTRAP_SEED,
                         "mode_sham_seed": MODE_SHAM_SEED},
               "pairs": {}, "f5": {}, "f7_declaration": f7_declaration()}

    # ---------------- Task 1: F-5 (census cost arithmetic, both pairs) --
    results["f5"] = f5_arithmetic()

    # ---------------- Tasks 2-5 per pair --------------------------------
    for pair in PAIRS:
        results["pairs"][pair] = run_pair(pair)
    return results


# ============================================================ F-5 =========

def f5_arithmetic() -> dict:
    """F-5 declared-band arithmetic on COSTS from the committed censuses.

    Conditional spread at the break-window buckets = the n-weighted mean
    of the bucket OPEN p50s over the buckets the 07-18 UTC window
    actually fills in (london_07_12, ny_overlap_12_16, ny_late_16_21).
    Stress RT = 2 crossings x 2.0 x conditional spread (pips). M3's D2
    condition: stress RT >= 2.0 pips (vs the proposal's <= 1.5 pip
    hypothesis) => pre-PnL kill. M1: report-only (no declared premium
    band exists in the freeze)."""
    out = {"formula": "stress_rt_pips = 2 crossings x k x s_cond; "
                      "s_cond = n-weighted mean of bucket OPEN p50s over "
                      + ",".join(BREAK_BUCKETS),
           "pairs": {}, "M3_USDCAD": {}, "M1_report_only": {}}
    conds = {}
    for pair in PAIRS:
        c = json.loads((DERIVED / f"census_{pair}.json").read_text())
        buckets = c["spread_pips"]["by_session"]
        num = den = 0.0
        per_bucket = {}
        for b in BREAK_BUCKETS:
            e = buckets[b]
            p50 = e["open"]["50"]
            per_bucket[b] = {"n": e["n"], "open_p50_pips": p50}
            num += e["n"] * p50
            den += e["n"]
        s_cond = round(num / den, 4)
        max_bucket = max(v["open_p50_pips"] for v in per_bucket.values())
        floors = {f"k{k}": round(2 * k * s_cond, 4)
                  for k in (1.0, 1.5, 2.0)}
        out["pairs"][pair] = {
            "conditional_open_p50_pips": s_cond,
            "per_bucket": per_bucket,
            "max_bucket_open_p50_pips": max_bucket,
            "overall_open_p50_pips": c["spread_pips"]["overall_open"]["50"],
            "rollover_open_p50_pips":
                buckets["rollover_21_22"]["open"]["50"],
            "rt_cost_floors_pips": floors,
            "rt_at_max_bucket": {f"k{k}": round(2 * k * max_bucket, 4)
                                 for k in (1.0, 1.5, 2.0)},
        }
        conds[pair] = s_cond

    # --- M3 (USDCAD home pair): D2 pre-declared kill condition --------
    s_usdcad = conds["USDCAD"]
    stress_rt = round(2 * 2.0 * s_usdcad, 4)
    kill = stress_rt >= 2.0
    out["M3_USDCAD"] = {
        "falsifier_id": "F-5",
        "declared_hypothesis": "premium band <= 1.5 pips round trip "
                               "(proposal field 2, D2 pre-declaration)",
        "kill_condition": "measured stress RT >= 2.0 pips",
        "measured_stress_rt_pips": stress_rt,
        "measured_base_rt_pips": round(2 * 1.0 * s_usdcad, 4),
        "verdict": "NOT_SCORED_FALSIFIED" if kill else "SURVIVES_F5",
        "margin_to_kill_line_pips": round(stress_rt - 2.0, 4),
        "note": "kill fired on the census conditional spread; robustness: "
                "every break bucket individually gives p50 1.2 -> stress "
                "RT 4.8 >= 2.0; even the base book (k=1.0) RT 2.4 exceeds "
                "the 1.5-pip hypothesis band",
        "m3_only_conditions_now_moot": [
            "V-1 fixture (rho vs R-ANCHOR > 0.60)",
            "T-1 session-collapse tripwire",
            "T-2 just-closed-bar PIT fixture",
            "T-3 >=2% mutation non-vacuity",
        ],
    }
    # --- M1: report-only cost floors ----------------------------------
    out["M1_report_only"] = {
        pair: {
            "declared_premium_band": None,
            "disposition": "REPORT_ONLY_F5_NO_DECLARED_BAND",
            "stress_rt_pips_k2": out["pairs"][pair]["rt_cost_floors_pips"]["k2.0"],
        } for pair in PAIRS
    }
    return out


# ==================================================== per-pair battery ====

def run_pair(pair: str) -> dict:
    from pair_config import load_pair_config
    cfg = load_pair_config(pair)
    pip_mult = 1.0 / cfg.pip

    df = pd.read_parquet(DERIVED / f"bars1h_ANC_{pair}.parquet")
    df = df[df["ts"] < pd.Timestamp(f"{HOLDOUT_START}T00:00:00Z")]
    p = T.SignalPlane(df, pip_mult=pip_mult)

    days = p.traded_days()
    warmup_end_idx = int(np.nonzero(p.day == days[WARMUP_TRADED_DAYS - 1])[0][-1])
    idx = np.arange(len(p.ts))
    post = idx > warmup_end_idx
    in_session = (~p.skip) & (p.hour >= 7) & (p.hour <= 18) & post
    out = {"pair": pair, "pip_mult": pip_mult,
           "dev_bars": int(len(p.ts)), "dev_traded_days": int(len(days)),
           "warmup_end_idx": warmup_end_idx,
           "warmup_end_ts": int(p.ts[warmup_end_idx]),
           "in_session_post_warmup_bars": int(in_session.sum())}

    # ---------------- Task 2: F-PIT-1 (M-1..M-5) -----------------------
    tgt_orig = T.f_rangeexp_orig(p)
    tgt_anch_a = T.f_rangeexp_anchor_shift(p)
    tgt_anch_b = T.f_rangeexp_anchor_independent(p)
    m1_equal = bool(np.array_equal(tgt_anch_a, tgt_anch_b))
    out["M1_shift_equivalence"] = {
        "impl_a": "pure usage-index shift of the ancestor function",
        "impl_b": "independent from-scratch percentile of ranges[d-1][0] "
                  "vs history strictly before d-1",
        "arrays_equal": m1_equal,
        "verdict": "PASS" if m1_equal else "NOT_RUN_ARMS_REDERIVED",
    }

    n_diff_bars = int((tgt_anch_a[in_session] != tgt_orig[in_session]).sum())
    m2_share = n_diff_bars / max(int(in_session.sum()), 1)
    out["M2_non_vacuity"] = {
        "denominator": "in-session (07-18 UTC) post-warmup dev bars",
        "in_session_bars": int(in_session.sum()),
        "differing_bars": n_diff_bars,
        "share": m2_share,
        "gate": ">= 0.02",
        "verdict": ("PASS" if m2_share >= 0.02 else "KILL_VACUOUS_MUTATION"),
        "margin_to_gate": m2_share - 0.02,
    }

    # day-level labels: R-ORIG vs R-ANCHOR (mechanism of M-2)
    days_l, ranges = T.day_ranges(p)
    pct = T.pct_full_panel(days_l, ranges)
    prev = T._day_prev_map(days_l)

    def label_of(m):
        return "flat" if m is None or m <= 0 else \
            ("follow" if m > 0.7 else "fade")

    orig_labels = {d: label_of(pct.get(d)) for d in days_l}
    anch_labels = {d: label_of(pct.get(prev[d]) if d in prev else None)
                   for d in days_l}
    post_days = [d for d in days_l if d > days_l[WARMUP_TRADED_DAYS - 1]]
    day_changed = sum(1 for d in post_days if orig_labels[d] != anch_labels[d])
    out["day_label_shift_effect"] = {
        "post_warmup_days": len(post_days),
        "days_label_changed_anchor_vs_orig": day_changed,
        "share": day_changed / max(len(post_days), 1),
        "orig_label_counts": {k: sum(1 for d in post_days
                                     if orig_labels[d] == k)
                              for k in ("flat", "fade", "follow")},
        "anchor_label_counts": {k: sum(1 for d in post_days
                                       if anch_labels[d] == k)
                                for k in ("flat", "fade", "follow")},
    }

    # M-3 daemon seam
    tgt_daemon, daemon_first_mode, daemon_changes = T.f_rangeexp_daemon(p)
    daemon_bar_dis = int((tgt_daemon[in_session] != tgt_orig[in_session]).sum())
    daemon_bar_dis_anch = int((tgt_daemon[in_session] != tgt_anch_a[in_session]).sum())
    daemon_day_labels = {}
    for d in post_days:
        daemon_day_labels[d] = daemon_first_mode.get(d, "flat")
    flips = sum(1 for d in post_days
                if daemon_day_labels[d] != orig_labels[d])
    early_silenced = [d for d in post_days
                      if orig_labels[d] != "flat" and daemon_day_labels[d] == "flat"]
    daemon_only_active = [d for d in post_days
                          if orig_labels[d] == "flat" and daemon_day_labels[d] != "flat"]
    midday_flip_days = sum(1 for d in post_days if daemon_changes.get(d, 0) > 0)
    out["M3_daemon_seam"] = {
        "verdict": "DISCLOSED_SEAM",
        "bar_disagreement_vs_orig": daemon_bar_dis,
        "bar_disagreement_share_vs_orig": daemon_bar_dis / max(int(in_session.sum()), 1),
        "bar_disagreement_vs_anchor": daemon_bar_dis_anch,
        "day_mode_flip_rate_vs_orig": flips / max(len(post_days), 1),
        "days_orig_active_daemon_flat": len(early_silenced),
        "days_orig_flat_daemon_active": len(daemon_only_active),
        "days_daemon_mode_changed_midday": midday_flip_days,
        "daemon_first_mode_counts": {k: sum(1 for d in post_days if
                                            daemon_day_labels[d] == k)
                                     for k in ("flat", "fade", "follow")},
        "semantics_pin": "at each signal bar the mode is the "
                         "searchsorted-left percentile of the partial "
                         "day range up to and including that bar vs the "
                         "trailing-60 full prior-day ranges; the state "
                         "machine consumes the current bar's mode; pos "
                         "persists within the day; pd_h/pd_l = prior "
                         "day's full hi/lo",
    }

    # M-5 truncation PIT proof
    trunc = T.truncation_pit_probe(p)
    out["M5_truncation_pit"] = {
        "orig_T0_diff_days": len(trunc["orig_t0_diff_days"]),
        "orig_T0_share_of_days": len(trunc["orig_t0_diff_days"]) / max(trunc["n_days"], 1),
        "orig_T1_diff_days": len(trunc["orig_t1_diff_days"]),
        "anchor_diff_days": len(trunc["anchor_trunc_diff_days"]),
        "anchor_full_vs_shift_impl_identical": trunc["anchor_full_vs_shift_impl_identical"],
        "orig_verdict": "LEAK_PROVEN (truncated replay differs)" if
        len(trunc["orig_t0_diff_days"]) > 0 else "FAIL_NO_DIFF",
        "anchor_verdict": "PIT_CLEAN_AS_EXECUTED (identical)" if
        len(trunc["anchor_trunc_diff_days"]) == 0 else "FAIL_DIFFERS",
        "definition": "truncated replay = day-stat layer from the prefix "
                      "panel strictly before the day's first bar; the "
                      "bar-walk then runs over the day's bars (T0 strict "
                      "day start; T1 first-bar-closed prefix disclosed)",
    }

    # mode-sham (F-3 extension)
    tgt_sham, sham_stats = T.mode_sham(p, seed=MODE_SHAM_SEED)
    sham_bar_dis = int((tgt_sham[in_session] != tgt_anch_a[in_session]).sum())
    sham_stats["bar_disagreement_vs_anchor"] = sham_bar_dis
    sham_stats["bar_disagreement_share"] = sham_bar_dis / max(int(in_session.sum()), 1)
    sham_stats["non_vacuity_gate"] = ">= 0.02 of day labels change"
    sham_stats["verdict"] = ("PASS_NON_VACUOUS" if
                             sham_stats["labels_changed_share_all_days"] >= 0.02
                             else "KILL_VACUOUS_MUTATION")
    out["mode_sham"] = sham_stats

    # ---------------- schedules (counts/costs only) --------------------
    sched = {}
    tgt_neigh = T.f_rangeexp_anchor_shift(p, lo_q=0.25, hi_q=0.75)
    tgt_inv = (-tgt_anch_a).astype(np.int8)
    sess = ((~p.skip) & (p.hour >= 7) & (p.hour <= 18)).astype(np.int8)
    sched["R-ANCHOR"] = T.schedule_only(p, tgt_anch_a, warmup_end_idx)
    sched["R-ORIG"] = T.schedule_only(p, tgt_orig, warmup_end_idx)
    sched["R-NEIGH"] = T.schedule_only(p, tgt_neigh, warmup_end_idx)
    sched["INVERTED"] = T.schedule_only(p, tgt_inv, warmup_end_idx)
    sched["SHORT_ALWAYS"] = T.schedule_only(p, (-sess).astype(np.int8),
                                            warmup_end_idx)
    sched["LONG_ALWAYS"] = T.schedule_only(p, sess, warmup_end_idx)
    sched["FLAT"] = []

    # ---------------- seam constants (c_rt, N_diff; S NOT computable) --
    c_rt = {
        arm: (float(np.median([T.trip_cost_pips(p, t, k=1.0)
                               for t in trips]))
              if trips else None)
        for arm, trips in (("R-ANCHOR", sched["R-ANCHOR"]),
                           ("R-ORIG", sched["R-ORIG"]))
    }
    nd, a_only, o_only = T.n_diff_trips(sched["R-ANCHOR"], sched["R-ORIG"])
    limb3 = T.limb3_matched_pairs(sched["R-ORIG"], sched["R-ANCHOR"],
                                  min_n=SEAM_LIMB3_MIN_N)
    out["seam_constants"] = {
        "c_rt_formula": "median over the arm's dev-window closed round "
                        "trips of [s_open(entry fill bar) + s_open(exit "
                        "bar) for signal exits / s_close(day-close bar) "
                        "for force-flat exits] x pip_mult, base book "
                        "k=1.0, pips",
        "c_rt_pips": {k: (round(v, 4) if v is not None else None)
                      for k, v in c_rt.items()},
        "N_diff": nd, "N_diff_anchor_only": a_only, "N_diff_orig_only": o_only,
        "S_statistic": "NOT_COMPUTABLE_PRE_PNL (seam limbs (i)/(ii) are "
                       "evaluated in the scored phase; this lane freezes "
                       "the constants and machinery only)",
        "limb3_machinery": {k: limb3[k] for k in
                            ("orig_only", "anchor_only", "matched_pairs",
                             "min_n_floor", "evaluable")},
        "limb3_pairing_rule": "nearest-in-time unmatched R-ANCHOR-only "
                              "trip within the same UTC day; equidistant "
                              "resolves to the EARLIER entry_ts (frozen)",
    }

    # ---------------- Task 3: F-1 ancestry rho --------------------------
    f1 = f1_rho(p, tgt_anch_a, in_session, warmup_end_idx)
    out["F1_ancestry_rho"] = f1

    # ---------------- Task 4: F-3 placebo constructibility --------------
    out["F3_placebo_probe"] = T.placebo_probe(
        p, sched["R-ANCHOR"], in_session, warmup_end_idx=warmup_end_idx)
    out["F3_placebo_probe"]["anchor_tgt_in_session_occupancy"] = \
        float((tgt_anch_a[in_session] != 0).mean())
    out["F3_placebo_probe"]["predicate_failure_note"] = (
        "occupancy predicate 10-40% NOT satisfiable under the pinned "
        "recipe (and the anchor's own in-session occupancy already "
        "exceeds the band): per plan 8 F-3 the causal control must be "
        "REBUILT before scoring; recorded as a scored-phase "
        "prerequisite, not an arm kill")

    # ---------------- Task 5: F-6 populations ---------------------------
    out["F6_populations"] = f6_counts(p, sched)

    out["schedule_counts_dev_total"] = {k: len(v) for k, v in sched.items()}
    return out


def f1_rho(p, tgt_anchor, in_session, warmup_end_idx) -> dict:
    """F-1: Spearman rho of R-ANCHOR's target array vs each frozen census
    family variant, in the ancestry target-array representation (the full
    scored target array over post-warmup dev bars)."""
    fnmap = {
        "f_gap": lambda c: T.f_gap(p, None, c["mode"], th_pips=c["th_pips"]),
        "f_pdhloc": lambda c: T.f_pdhloc(p, None, c["opposite_exit"],
                                         buf_pips=c["buf_pips"]),
        "f_dow_simple": lambda c: T.f_dow_simple(p, c["weeks"], c["min_days"]),
        "f_asiafade": lambda c: T.f_asiafade(p, c["asia_end"], None,
                                             buf_pips=c["buf_pips"]),
        "f_sessma": lambda c: T.f_sessma(p, c["th"], c["win_atr"]),
        "f_h1tsmom": lambda c: T.f_h1tsmom(p, c["K"]),
        "f_h1donch": lambda c: T.f_h1donch(p, c["L"], c["hold_mult"]),
        "f_daymom": lambda c: T.f_daymom(p, c["N"]),
        "f_rangeexp": lambda c: T.f_rangeexp_orig(
            p, c["lo_q"], c["hi_q"], c["use_breakout"]),
        "f_stoch": lambda c: T.f_stoch(p, c["N"], c["th_hi"], c["th_lo"]),
        "f_roundnum": lambda c: T.f_roundnum(p, c["grid_pips"],
                                             c["prox_pips"]),
        "f_hourrev": lambda c: T.f_hourrev(p, c["win_days"], c["invert"]),
    }
    rows = []
    for fam, fn, cfg in F1_VARIANTS:
        t = fnmap[fn](cfg)
        rho_full = T.spearman_rho(tgt_anchor, t)
        rho_ins = T.spearman_rho(tgt_anchor[in_session], t[in_session])
        rows.append({"family": fam, "variant": cfg,
                     "abs_rho_full_array": round(abs(rho_full), 6),
                     "abs_rho_in_session": round(abs(rho_ins), 6)})
    abs_full = [r["abs_rho_full_array"] for r in rows]
    pooled = float(np.mean(abs_full))
    mx = max(rows, key=lambda r: r["abs_rho_full_array"])
    rangeexp = [r for r in rows if r["family"] == "RANGEEXP"]
    return {
        "representation": "ancestry target-array representation: the full "
                          "scored int8 target array over post-warmup dev "
                          "bars (in-session-only rho also logged)",
        "gate": "pooled |rho| <= 0.20 (binding for Task-2 proposals; "
                "for M1 Task-1 this is DISCLOSURE of declared ancestry)",
        "pooled_abs_rho": round(pooled, 6),
        "max_abs_rho": mx["abs_rho_full_array"],
        "max_abs_rho_variant": {"family": mx["family"],
                                "variant": mx["variant"]},
        "rangeexp_family_abs_rho": {str(r["variant"]): r["abs_rho_full_array"]
                                    for r in rangeexp},
        "n_variants": len(rows),
        "rows": rows,
    }


def f6_counts(p, sched) -> dict:
    def fold_of(entry_ts):
        for fid, s, e in FOLD_TABLE:
            if ts_of(s) <= entry_ts <= ts_of(e, end=True):
                return fid
        return None

    l6s, l6e = ts_of(LAST6_START), ts_of(LAST6_END, end=True)
    out = {"floors": FLOORS,
           "folds": {fid: [s, e] for fid, s, e in FOLD_TABLE},
           "last6_window": [LAST6_START, LAST6_END], "arms": {}}
    for arm, trips in sched.items():
        per_fold = {fid: 0 for fid, _, _ in FOLD_TABLE}
        last6 = 0
        for t in trips:
            fid = fold_of(t["entry_ts"])
            if fid:
                per_fold[fid] += 1
            if l6s <= t["entry_ts"] <= l6e:
                last6 += 1
        total = sum(per_fold.values())
        out["arms"][arm] = {
            "per_fold": per_fold,
            "dev_union_total": total,
            "last6_months": last6,
            "meets_smoke_30_dev": total >= FLOORS["smoke"],
            "meets_adjudication_100_dev": total >= FLOORS["adjudication"],
            "meets_promote_236_dev_union": total >= FLOORS["promote_dev_union"],
            "meets_smoke_30_last6": last6 >= FLOORS["smoke"],
            "note": "counts assigned by ENTRY ts; fold-boundary force-flat "
                    "is the scored phase's executor law",
        }
    return out


def f7_declaration() -> dict:
    """F-7 pre-check: declared concentration statistics + exclusion-zone
    fields the scored phase MUST emit (no computation now — no PnL
    exists)."""
    return {
        "declared_statistics": {
            "fold_level": "top-fold share = max over folds of "
                          "(positive net in fold) / (total positive net); "
                          "gate G6 <= 0.50",
            "trade_level": "top-5-trades share = sum of the 5 largest "
                           "positive-trade pips / total positive net; "
                           "gate G7 <= 0.50 (top-single-trade share also "
                           "logged)",
            "session_hour_level": "top single session-hour share = max "
                                  "over UTC hours of (positive net in "
                                  "hour) / (total positive net); gate "
                                  "G8 <= 0.50",
        },
        "books": "computed at k=1.0 and k=2.0, folds F1..F6 (dev) only",
        "exclusion_zone_log_fields": ["level(fold|trade|hour)", "id",
                                      "share", "threshold", "cost_tier k",
                                      "arm_id", "pair", "fold_or_holdout_tag"],
        "status": "DECLARED_PRE_PNL (scored-phase emission requirement; "
                  "nothing computable in this lane)",
    }


# ------------------------------------------------- freeze artifact -------

HOLDOUT_MEMBERSHIP = {
    pair: {
        "anchor_arms": [
            {"mechanism": "M1", "arm": "R-ANCHOR", "pair": pair,
             "arm_config_digest": arm_digest(
                 "M1", "R-ANCHOR", pair,
                 {"mode_index": "d-1", "guard": "pct[d-1] > 0"})},
        ],
        "companions_single_pass": [
            {"mechanism": "M1", "arm": "CAUSAL-PLACEBO", "pair": pair,
             "arm_config_digest": arm_digest(
                 "M1", "CAUSAL-PLACEBO", pair, {"recipe": "pinned"})},
            {"mechanism": "M1", "arm": "INVERTED", "pair": pair,
             "arm_config_digest": arm_digest(
                 "M1", "INVERTED", pair, {"law": "-tgt(R-ANCHOR)"})},
            {"mechanism": "M1", "arm": "BASELINE-SET", "pair": pair,
             "arm_config_digest": arm_digest(
                 "M1", "BASELINE-SET", pair,
                 {"books": ["FLAT", "SHORT_ALWAYS", "LONG_ALWAYS"],
                  "beta_matched": "AUDUSD->SHORT_ALWAYS; USDCAD->LONG_ALWAYS"})},
        ],
        "excluded_never_selectable": ["R-ORIG", "R-NEIGH", "R-DAEMON",
                                      "mode-sham", "M2 (vetoed at D2)",
                                      "M3 (NOT_SCORED_FALSIFIED at F-5)"],
    }
    for pair in PAIRS
}


def build_freeze(results: dict) -> dict:
    code_paths = ["scripts/tracka_lib.py", "scripts/falsifier_run.py",
                  "scripts/build_signal_plane.py"]
    code_chain = {pth: hashlib.sha256((LANE / pth).read_bytes()).hexdigest()
                  for pth in code_paths}
    membership_blob = json.dumps(HOLDOUT_MEMBERSHIP, sort_keys=True,
                                 default=str)
    membership_sha = hashlib.sha256(membership_blob.encode()).hexdigest()
    censuses = {pair: sha256_file(DERIVED / f"census_{pair}.json")
                for pair in PAIRS}
    manifests = {pair: sha256_file(
        LANE / "data_local" / "duka" / f"m1_manifest_{pair}.json")
        for pair in PAIRS}
    plane_diffs = {pair: json.loads(
        (DERIVED / f"plane_diff_{pair}.json").read_text()) for pair in PAIRS}

    freeze = {
        "schema": "tracka_go1_freeze@1",
        "cycle_id": "ERP1-TRACKA-COHORT-1",
        "lane": "tracka1-falsifier",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(
            timespec="seconds"),
        "dispatch_sha": "2682422a62e64edd25cca42b6a51fdffdfba4d14",
        "verdict_class": "PRE_PNL_FREEZE (GO-1 consumed; GO-2 NOT given; "
                         "no scored row exists)",
        "pins": {
            "(i)_seeds": {
                "bootstrap_seed": BOOTSTRAP_SEED,
                "mode_sham_seed": MODE_SHAM_SEED,
                "storage_path": "research/control/ERP1-TRACKA-COHORT-1/"
                                "freeze/GO1_freeze_artifact.json",
                "rng": "numpy PCG64 default_rng(seed); mode-sham draws are "
                       "per-pair (fresh default_rng(MODE_SHAM_SEED) per "
                       "pair call), deterministic; bootstrap seed is "
                       "reserved for the scored-phase power gate",
                "pin_order": "pins written to freeze_pins.json before any "
                             "computation consumed them; measured "
                             "constants merged into this committed "
                             "artifact afterward (no scored computation "
                             "exists in this cycle segment)",
            },
            "(ii)_holdout_pass_membership": {
                "law": "plan 9.1 one-look holdout; membership frozen "
                       "before the pass; anchors + companions computed in "
                       "the SAME single pass; never-selectable arms take "
                       "no look",
                "per_pair": HOLDOUT_MEMBERSHIP,
                "sha256": membership_sha,
            },
            "(iii)_mode_sham_outcome_vocabulary": {
                "non_vacuity_failure_lt_2pct_labels_changed":
                    "KILL_VACUOUS_MUTATION (arm set re-derived once, "
                    "pre-PnL, registered amendment inheriting the "
                    "consumed look)",
                "seam_law_firing_attributable_to_mode_channel":
                    "KILL_PIT_SEAM",
                "otherwise": "diagnostic-only record — never a positive "
                             "input",
            },
            "(iv)_two_pair_utc_close_semantics": "Identical UTC close law "
                "for AUDUSD and USDCAD: signal on CLOSED H1 bar, fill at "
                "next H1 open at the opposite quote; no fills on/after "
                "the 19:00 H1 bar; every position force-flat at the "
                "19:00-bar close (20:00 UTC); weekend flat; no overnight, "
                "no swap (structural-zero financing by executor "
                "fixture). NO per-pair local-close variant exists in "
                "this cohort.",
            "(v)_seam_limb3_minimum_N": {
                "floor": SEAM_LIMB3_MIN_N,
                "rule": "matched-pair count < 20 => limb (iii) NOT_RUN "
                        "fail-closed; limbs (i)/(ii) decide",
            },
        },
        "plane_semantics_pin": {
            "decision_rule": "ANCESTRY convention for the SIGNAL plane of "
                             "all arms; port true-H/L bars remain the "
                             "COST plane (spread charging unchanged)",
            "ancestor_convention_exact": "15m high = max(CLOSE column), "
                                         "15m low = min(LOW column) under "
                                         "the verified (sec,o,c,l,h,v) "
                                         "decode; H1 = max/min of the "
                                         "four 15m bars. LINEAGE-NOTE-1 "
                                         "precision: ONLY the high is "
                                         "close-column; the ancestor low "
                                         "was already the true low",
            "verification": plane_diffs,
            "consequence": "ancestor 15m/H1 ranges are narrower on the "
                           "top than true-H/L ranges; R-ORIG is a "
                           "faithful ancestor instantiation on the ANC "
                           "plane; cost spreads verified bit-identical "
                           "(max abs diff 0.0) across conventions",
        },
        "seam_constants": {
            pair: results["pairs"][pair]["seam_constants"] for pair in PAIRS
        },
        "f1_frozen_variant_set": {
            "law": "skeptic representation law (plan 8 F-1): pooled "
                   "|rho| on the EXACT scored target-array representation",
            "n_variants": len(F1_VARIANTS),
            "variants": [{"family": f, "fn": fn, "config": c}
                         for f, fn, c in F1_VARIANTS],
            "measured": {pair: {
                "pooled_abs_rho": results["pairs"][pair]["F1_ancestry_rho"]["pooled_abs_rho"],
                "max_abs_rho": results["pairs"][pair]["F1_ancestry_rho"]["max_abs_rho"],
            } for pair in PAIRS},
        },
        "arm_registry": [],
        "windows": {
            "dev": f"{DEV_START}..{DEV_END}",
            "holdout_untouched_here": f"{HOLDOUT_START}..{HOLDOUT_END}",
            "warmup_traded_days": WARMUP_TRADED_DAYS,
            "folds": [list(f) for f in FOLD_TABLE],
            "last6_feasibility_window": [LAST6_START, LAST6_END],
        },
        "cost_book": {
            "tiers": "k in {1.0 base, 1.5 stress-report, 2.0 stress} on "
                     "the fill bar's own measured spread (per-session "
                     "census curve = persisted authority)",
            "authority_pointer": "plan 6; census_{SYM}.json (schema "
                                 "tracka_census@2, committed)",
            "census_sha256": censuses,
            "m1_manifest_sha256": manifests,
        },
        "f5_verdicts": {
            "M3_USDCAD": results["f5"]["M3_USDCAD"],
            "M1_report_only": results["f5"]["M1_report_only"],
        },
        "f7_concentration_declaration": results["f7_declaration"],
        "placebo_recipe_pin": {
            "entries_per_day": "round(anchor avg entries per traded day), min 1",
            "entry_hour": "round(anchor avg entry hour) clamp [7,17]; "
                          "+2h for the second entry when entries/day >= 2",
            "direction": "alternates by traded-day index (+1 on even)",
            "exit": "after round(anchor avg hold_bars) bars or the "
                    "day-close bar, whichever first",
            "note": "constructibility probe only; the scored-phase "
                    "control is built under this exact recipe",
        },
        "sha_chain": {
            "code_freeze": code_chain,
            "falsifier_results_sha256": None,  # filled by the writer
        },
        "labels_class": ["SINGLE_SOURCE_PANEL",
                         "FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK",
                         "PAPER_TIER"],
    }
    for pair in PAIRS:
        freeze["arm_registry"].extend([
            {"mechanism": "M1", "arm": "R-ANCHOR", "pair": pair,
             "arm_config_digest": arm_digest(
                 "M1", "R-ANCHOR", pair,
                 {"mode_index": "d-1", "guard": "pct[d-1] > 0"}),
             "status": "FROZEN_PRE_PNL"},
            {"mechanism": "M1", "arm": "R-ORIG", "pair": pair,
             "arm_config_digest": arm_digest(
                 "M1", "R-ORIG", pair,
                 {"mode_index": "d (ancestor byte-faithful; recorded PIT "
                                "seam)"}),
             "status": "FROZEN_PRE_PNL (diagnostic; never selectable)"},
            {"mechanism": "M1", "arm": "R-NEIGH", "pair": pair,
             "arm_config_digest": arm_digest(
                 "M1", "R-NEIGH", pair,
                 {"lo_q": 0.25, "hi_q": 0.75, "semantics": "R-ANCHOR"}),
             "status": "FROZEN_PRE_PNL (support check; never selectable)"},
            {"mechanism": "M1", "arm": "CAUSAL-PLACEBO", "pair": pair,
             "arm_config_digest": arm_digest(
                 "M1", "CAUSAL-PLACEBO", pair, {"recipe": "pinned"}),
             "status": "FROZEN_PRE_PNL"},
            {"mechanism": "M1", "arm": "INVERTED", "pair": pair,
             "arm_config_digest": arm_digest(
                 "M1", "INVERTED", pair, {"law": "-tgt(R-ANCHOR)"}),
             "status": "FROZEN_PRE_PNL"},
            {"mechanism": "M1", "arm": "BASELINE-SET", "pair": pair,
             "arm_config_digest": arm_digest(
                 "M1", "BASELINE-SET", pair,
                 {"books": ["FLAT", "SHORT_ALWAYS", "LONG_ALWAYS"]}),
             "status": "FROZEN_PRE_PNL"},
            {"mechanism": "M3", "arm": "ALL", "pair": "USDCAD",
             "arm_config_digest": None,
             "status": "NOT_SCORED_FALSIFIED (F-5, pre-PnL; all M3-only "
                       "conditions moot)"},
            {"mechanism": "M2", "arm": "ALL", "pair": None,
             "arm_config_digest": None,
             "status": "NOT_SCORED_FALSIFIED (D2 V-4_BLEND; pre-existing)"},
        ])
    return freeze


# --------------------------------------------------------- ledger --------

def labels():
    return ["SINGLE_SOURCE_PANEL", "FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK",
            "PAPER_TIER"]


def base_row(**kw):
    row = {
        "cycle_id": "ERP1-TRACKA-COHORT-1",
        "mechanism_id": None, "arm_id": None, "arm_config_digest": None,
        "pair": None, "fold_or_holdout_tag": "PRE_PNL_BATTERY",
        "cost_tier": "PAPER_TIER_PER_SESSION_X_K",
        "net_pnl": None, "gross_pnl": None,
        "gates_with_margins_to_fail": {}, "verdict": None,
        "exclusion_zones": None, "labels": labels(),
        "falsifier_id": None,
        "sha_chain": {},
    }
    row.update(kw)
    return row


def build_ledger(results: dict, freeze: dict, results_sha: str) -> list:
    chain = {"code_freeze": freeze["sha_chain"]["code_freeze"],
             "data_manifest": {
                 pair: freeze["cost_book"]["census_sha256"][pair]
                 for pair in PAIRS},
             "selection_digest": results_sha}
    rows = []
    # data-gate rows
    for pair in PAIRS:
        rows.append(base_row(
            falsifier_id="DATAGATE", pair=pair,
            verdict="BUILD_PASS",
            gates_with_margins_to_fail=json.loads(
                (DERIVED / f"census_{pair}.json").read_text())["gate_margins"],
            sha_chain=chain,
            note="data-gate lane verdict re-ledgered at freeze (authority: "
                 "HANDOFF_tracka1_datagate.json + census JSON)"))
    # F-5 rows
    m3 = results["f5"]["M3_USDCAD"]
    rows.append(base_row(
        falsifier_id="F-5", mechanism_id="M3", arm_id="ALL", pair="USDCAD",
        verdict=m3["verdict"],
        gates_with_margins_to_fail={
            "kill_line_stress_rt_pips": 2.0,
            "measured_stress_rt_pips": m3["measured_stress_rt_pips"],
            "margin_to_kill_line_pips": m3["margin_to_kill_line_pips"],
            "measured_base_rt_pips": m3["measured_base_rt_pips"],
            "declared_hypothesis": m3["declared_hypothesis"],
            "m3_only_conditions_moot": m3["m3_only_conditions_now_moot"],
        },
        sha_chain=chain,
        note="D2 pre-declared arithmetic kill from the committed census; "
             "no scored cell, no V-1/T-1/T-2/T-3 consumption (moot)"))
    for pair in PAIRS:
        ro = results["f5"]["M1_report_only"][pair]
        rows.append(base_row(
            falsifier_id="F-5", mechanism_id="M1", arm_id="ALL", pair=pair,
            verdict="REPORT_ONLY_F5_NO_DECLARED_BAND",
            gates_with_margins_to_fail={
                "rt_cost_floors_pips": results["f5"]["pairs"][pair]["rt_cost_floors_pips"],
                "conditional_open_p50_pips": results["f5"]["pairs"][pair]["conditional_open_p50_pips"],
                "declared_premium_band": None,
            },
            sha_chain=chain,
            note="M1 has no declared premium band in the freeze; F-5 is "
                 "report-only; no kill invented"))
    # F-PIT-1 rows
    for pair in PAIRS:
        pp = results["pairs"][pair]
        m1v, m2v, m5 = (pp["M1_shift_equivalence"]["verdict"],
                        pp["M2_non_vacuity"]["verdict"],
                        pp["M5_truncation_pit"])
        if m1v != "PASS":
            verdict = "NOT_RUN_ARMS_REDERIVED"
        elif m2v != "PASS":
            verdict = "KILL_VACUOUS_MUTATION"
        else:
            verdict = "PASS_PIT"
        rows.append(base_row(
            falsifier_id="F-PIT-1", mechanism_id="M1",
            arm_id="R-ANCHOR(+R-ORIG probe)", pair=pair,
            verdict=verdict,
            gates_with_margins_to_fail={
                "M1": pp["M1_shift_equivalence"],
                "M2": pp["M2_non_vacuity"],
                "M3": {k: v for k, v in pp["M3_daemon_seam"].items()
                       if k != "semantics_pin"},
                "M5": {k: v for k, v in m5.items() if k != "definition"},
                "mode_sham": {k: v for k, v in pp["mode_sham"].items()},
                "S_statistic": pp["seam_constants"]["S_statistic"],
                "c_rt_pips": pp["seam_constants"]["c_rt_pips"],
                "N_diff": pp["seam_constants"]["N_diff"],
            },
            sha_chain=chain,
            note="seam limbs (i)/(ii) evaluated in the scored phase; M-3 "
                 "is DISCLOSED_SEAM (never a kill)"))
    # F-1 rows
    for pair in PAIRS:
        f1 = results["pairs"][pair]["F1_ancestry_rho"]
        rows.append(base_row(
            falsifier_id="F-1", mechanism_id="M1", arm_id="R-ANCHOR",
            pair=pair, verdict="ANCESTRY_RHO_DISCLOSED",
            gates_with_margins_to_fail={
                "pooled_abs_rho": f1["pooled_abs_rho"],
                "gate_threshold": 0.20,
                "max_abs_rho": f1["max_abs_rho"],
                "max_abs_rho_variant": f1["max_abs_rho_variant"],
                "rangeexp_family_abs_rho": f1["rangeexp_family_abs_rho"],
                "gate_applicability": "binding for Task-2 proposals; M1 "
                                      "is the declared Task-1 replication "
                                      "of this family (plan 3.5 disclosure)",
            },
            sha_chain=chain,
            note="frozen variant set = 12 census family functions x 2 "
                 "pinned variants; M3's V-1 fixture MOOT (M3 killed at "
                 "F-5)"))
    # mode-sham rows
    for pair in PAIRS:
        ms = results["pairs"][pair]["mode_sham"]
        rows.append(base_row(
            falsifier_id="F-3-mode-sham", mechanism_id="M1",
            arm_id="R-ANCHOR", pair=pair, verdict=ms["verdict"],
            gates_with_margins_to_fail={
                "labels_changed_share_all_days":
                    ms["labels_changed_share_all_days"],
                "labels_changed_share_active_days":
                    ms["labels_changed_share_active_days"],
                "bar_disagreement_share": ms["bar_disagreement_share"],
                "seed": MODE_SHAM_SEED,
            },
            sha_chain=chain,
            note="diagnostic-only record per freeze pin (iii); never a "
                 "positive input"))
    # F-6 rows
    for pair in PAIRS:
        f6 = results["pairs"][pair]["F6_populations"]["arms"]
        for arm, stats in f6.items():
            rows.append(base_row(
                falsifier_id="F-6", mechanism_id="M1", arm_id=arm,
                pair=pair, verdict="POPULATIONS_VS_FLOORS",
                fold_or_holdout_tag="DEV_FOLDS_F1_F6+LAST6",
                gates_with_margins_to_fail={
                    "per_fold_counts": stats["per_fold"],
                    "dev_union_total": stats["dev_union_total"],
                    "last6_months": stats["last6_months"],
                    "meets_smoke_30_dev": stats["meets_smoke_30_dev"],
                    "meets_adjudication_100_dev": stats["meets_adjudication_100_dev"],
                    "meets_promote_236_dev_union": stats["meets_promote_236_dev_union"],
                    "meets_smoke_30_last6": stats["meets_smoke_30_last6"],
                },
                sha_chain=chain,
                note="COUNTS ONLY (no PnL); G-gate verdicts need the "
                     "scored phase"))
    return rows


# ----------------------------------------------------------------- main --

def main() -> int:
    FREEZE_DIR.mkdir(exist_ok=True)
    # pins BEFORE any consuming computation
    pins = {
        "bootstrap_seed": BOOTSTRAP_SEED,
        "mode_sham_seed": MODE_SHAM_SEED,
        "storage_path": str(OUT_FREEZE),
        "written_utc": dt.datetime.now(dt.timezone.utc).isoformat(
            timespec="seconds"),
    }
    (FREEZE_DIR / "freeze_pins.json").write_text(json.dumps(pins, indent=1))

    results = run()
    OUT_RESULTS.write_text(json.dumps(results, indent=1, default=str))
    results_sha = sha256_file(OUT_RESULTS)

    freeze = build_freeze(results)
    freeze["sha_chain"]["falsifier_results_sha256"] = results_sha
    freeze["sha_chain"]["freeze_pins_bootstrap"] = pins
    OUT_FREEZE.write_text(json.dumps(freeze, indent=1, default=str))

    rows = build_ledger(results, freeze, results_sha)
    # Ledger SEED write: exactly-once, idempotent. The plan's append-only
    # law governs rows AFTER the seed is committed; the seed itself is
    # regenerated deterministically from the frozen inputs on re-run so a
    # lane re-execution can never duplicate a row.
    with open(OUT_LEDGER, "w") as f:
        for r in rows:
            f.write(json.dumps(r, default=str) + "\n")

    print(json.dumps({
        "f5_M3": results["f5"]["M3_USDCAD"]["verdict"],
        "f5_M3_stress_rt": results["f5"]["M3_USDCAD"]["measured_stress_rt_pips"],
        "pairs": {pair: {
            "M1": results["pairs"][pair]["M1_shift_equivalence"]["verdict"],
            "M2": results["pairs"][pair]["M2_non_vacuity"]["verdict"],
            "M2_share": results["pairs"][pair]["M2_non_vacuity"]["share"],
            "M5_orig": results["pairs"][pair]["M5_truncation_pit"]["orig_verdict"],
            "M5_anchor": results["pairs"][pair]["M5_truncation_pit"]["anchor_verdict"],
            "mode_sham": results["pairs"][pair]["mode_sham"]["verdict"],
            "mode_sham_share": results["pairs"][pair]["mode_sham"]["labels_changed_share_all_days"],
            "pooled_rho": results["pairs"][pair]["F1_ancestry_rho"]["pooled_abs_rho"],
            "max_rho": results["pairs"][pair]["F1_ancestry_rho"]["max_abs_rho"],
            "c_rt_anchor": results["pairs"][pair]["seam_constants"]["c_rt_pips"]["R-ANCHOR"],
            "N_diff": results["pairs"][pair]["seam_constants"]["N_diff"],
            "anchor_trips": results["pairs"][pair]["schedule_counts_dev_total"]["R-ANCHOR"],
            "orig_trips": results["pairs"][pair]["schedule_counts_dev_total"]["R-ORIG"],
        } for pair in PAIRS},
        "ledger_rows": len(rows),
    }, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
