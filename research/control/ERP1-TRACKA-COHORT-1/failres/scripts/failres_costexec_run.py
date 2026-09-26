"""COST/EXECUTION lane run script — ERP1-TRACKA-COHORT-1 / failres-cost.

FAILURE_ROOT_CAUSE_RESEARCH · DIAGNOSTIC_OUTCOME_EXPOSED ·
SINGLE_SOURCE_PANEL · FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK · PAPER_TIER.

Phase A cost-side reading of the failres-attrib artifacts (committed at
base 3b1c29fa). AUDIT + DECOMPOSITION ONLY: no strategy proposal, no
parameter tuning, no shadow/journal/registry contact, one pass over
frozen inputs.

Wording law (program): taker fills PAY the spread (entry at the opposite
quote + per-bar spread x k). No "earning/capturing the spread", no
maker/queue claims, no "fill at mid"/"zero slippage". Honest cost
sentence: "taker at opposite quote + measured per-bar spread x k;
commission and slippage-beyond-spread DECLARED_UNMEASURED,
stress-covered".

What this script does
  T1  per-fold gross/cost/net table (R-DAEMON, both pairs, k=1.0 with
      k=1.5/2.0 decay restated), cost shares, losing-fold verdicts
      (COST_DOMINATED / GROSS_NEGATIVE / MIXED) with arithmetic.
  T2  spread-at-fill regime: entry-bar-spread distribution for trades
      actually taken, per fold and per entry-hour bucket, vs same-day
      spread p50 (daily table) and vs panel p50 (census).
  T3  independent sample verification: 50 R-DAEMON trades per pair
      (random.Random(20260926)) recomputed from the parquet + the
      committed engine charging law at k=1.0 and k=0.0;
      gross = k0 pnl, cost = k1 - k0; max abs deviation vs the
      attribution tables (tolerance 0.01 pips; beyond = FINDING).
  T4  F-5-style ceiling arithmetic from the committed census session
      spread curves: full RT cost at k=1.0 and x2.0 stress, break-hour
      conditional (never global p50), stated as the gross premium a
      candidate must declare per RT to be non-fragile.
  T5  exit-type x cost interaction: mean cost per RT, FORCE_FLAT vs
      TARGET_EXIT vs REVERSAL pools, per fold.
  T6  facts-only reading inputs: k=0 gross per fold (sign-flip test).

Outputs: failres_costexec_agg.json (+ printed summary used for the MD
report). Discrepancies vs the attribution lane are FINDINGS, never edits.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd

COHORT = Path(__file__).resolve().parent.parent.parent   # .../ERP1-TRACKA-COHORT-1
FAILRES = COHORT / "failres"
DERIVED = FAILRES / "data_local" / "derived"
DIAG_DERIVED = COHORT / "diag" / "data_local" / "derived"
for _p in (str(COHORT / "scripts"), str(COHORT / "diag" / "scripts"),
           str(FAILRES / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from falsifier_run import FOLD_TABLE  # noqa: E402  (ONLY fold authority)
from pair_config_diag import load_pair_config  # noqa: E402

PANEL_END = "2026-06-30"
PAIRS = ("EURUSD", "GBPUSD")
FOLD_IDS = [f for f, _, _ in FOLD_TABLE]
LOSING_FOLDS = {"EURUSD": ("F1", "F2", "F5"), "GBPUSD": ("F3", "F5", "F6")}
HOUR_BUCKETS = (("asia_00_06", 0, 6), ("london_07_12", 7, 12),
                ("ny_13_18", 13, 18))
# census break-hour buckets (committed census by_session_open keys)
BREAK_BUCKETS = ("rollover_21_22", "late_22_24", "friday_20_23_open",
                 "sunday_open_21_22")
SESSION_BUCKETS = ("asia_00_07", "london_07_12", "ny_overlap_12_16",
                   "ny_late_16_21")
LABELS = ["FAILURE_ROOT_CAUSE_RESEARCH", "DIAGNOSTIC_OUTCOME_EXPOSED",
          "SINGLE_SOURCE_PANEL", "FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK",
          "PAPER_TIER"]
SEED = 20260926
SAMPLE_N = 50
SAMPLE_TOL_PIPS = 0.01


def sha256_file(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def r2(x) -> float:
    return round(float(x), 2)


def r4(x) -> float:
    return round(float(x), 4)


def load_rows(pair: str) -> list:
    d = json.loads((FAILRES / f"failres_attrib_trades_{pair}.json").read_text())
    assert d["pair"] == pair and d["schema"] == "failres_attrib_trades@1"
    return d["rows"]


def load_daily_sp50(pair: str) -> dict:
    d = json.loads((FAILRES / f"failres_daily_{pair}.json").read_text())
    return {r["date"]: r["day_spread_p50_pips"] for r in d["rows"]}


def load_agg(pair: str) -> dict:
    return json.loads((FAILRES / f"failres_attrib_agg_{pair}.json").read_text())


# ------------------------------------------------------------------ T1 ----

def fold_tables(rows: list) -> dict:
    """Per-fold R-DAEMON gross/cost/net from the per-trade attribution
    rows (k=1.0 primary), cost shares, per-RT mean cost, k-decay restated
    from the agg."""
    out = {}
    for f in FOLD_IDS:
        fr = [r for r in rows if r["book"] == "R-DAEMON" and r["fold"] == f]
        net = sum(r["net_pips"] for r in fr)
        gross = sum(r["gross_pips"] for r in fr)
        cost = sum(r["cost_pips"] for r in fr)
        rec = {
            "rt": len(fr),
            "gross_pips": r2(gross),
            "cost_pips": r2(cost),
            "net_pips": r2(net),
            "mean_cost_per_rt_pips": r4(-cost / len(fr)) if fr else None,
            "identity_residual_pips": r2(net - (gross + cost)),
        }
        if net < 0:
            loss = -net
            share_cost = (-cost) / loss      # cost_pips <= 0
            share_gross = (-gross) / loss    # can be negative if gross > 0
            rec["loss_pips"] = r2(loss)
            rec["cost_share_of_loss"] = r4(share_cost)
            rec["gross_share_of_loss"] = r4(share_gross)
            rec["cost_over_abs_gross"] = (None if gross == 0
                                          else r4(-cost / abs(gross)))
            if share_cost > 0.5 >= share_gross:
                rec["verdict"] = "COST_DOMINATED"
            elif share_gross > 0.5 >= share_cost:
                rec["verdict"] = "GROSS_NEGATIVE"
            elif share_cost > 0.5 and share_gross > 0.5:
                rec["verdict"] = "MIXED"
            elif abs(share_cost - 0.5) < 1e-9:
                rec["verdict"] = "MIXED"
            else:
                # gross > 0 pushed negative purely by cost -> fully cost
                rec["verdict"] = "COST_DOMINATED"
        else:
            rec["loss_pips"] = None
            rec["verdict"] = None   # winning fold: no verdict requested
        out[f] = rec
    return out


# ------------------------------------------------------------------ T2 ----

def pctiles(vals) -> dict:
    if not len(vals):
        return {"n": 0}
    q = np.percentile(np.asarray(vals, dtype=float), [25, 50, 75, 99])
    return {"n": int(len(vals)), "p25": r4(q[0]), "p50": r4(q[1]),
            "p75": r4(q[2]), "p99": r4(q[3])}


def spread_regime(rows: list, daily_sp50: dict, panel_p50: float) -> dict:
    """Entry-bar spread distribution for R-DAEMON trades actually taken,
    per fold and per entry-hour bucket; ratio vs same-day spread p50."""
    dr = [r for r in rows if r["book"] == "R-DAEMON"]
    out = {"panel_p50_census_pips": panel_p50, "per_fold": {},
           "per_entry_hour_bucket": {}}
    for f in FOLD_IDS:
        fr = [r for r in dr if r["fold"] == f]
        sp = [r["entry_bar_spread_pips"] for r in fr]
        ratios = [r["entry_bar_spread_pips"] / daily_sp50[r["day"]]
                  for r in fr if r["day"] in daily_sp50
                  and daily_sp50[r["day"]] > 0]
        out["per_fold"][f] = {
            **pctiles(sp),
            "median_ratio_to_day_p50": r4(np.median(ratios)) if ratios else None,
            "share_filled_above_day_p50": r4(float(np.mean(
                [x > 1.0 for x in ratios]))) if ratios else None,
        }
    for nm, lo, hi in HOUR_BUCKETS:
        br = [r for r in dr if r["fold"] in FOLD_IDS
              and lo <= r["entry_hour_utc"] <= hi]
        sp = [r["entry_bar_spread_pips"] for r in br]
        ratios = [r["entry_bar_spread_pips"] / daily_sp50[r["day"]]
                  for r in br if r["day"] in daily_sp50
                  and daily_sp50[r["day"]] > 0]
        out["per_entry_hour_bucket"][nm] = {
            **pctiles(sp),
            "median_ratio_to_day_p50": r4(np.median(ratios)) if ratios else None,
        }
    # losing-fold vs winning-fold headline
    return out


# ------------------------------------------------------------------ T3 ----

def recompute_pair(pair: str, rows: list) -> dict:
    """Independent recompute of gross/cost for a seeded random sample of
    R-DAEMON trades, straight from the parquet + engine charging law.

    Plane semantics MUST match the committed machinery (tracka_lib.
    SignalPlane, which the attribution lane feeds to engine.run_strategy):
    s_open := a_o - b_o and s_close := a_c - b_c are RECOMPUTED from the
    quote columns (the parquet's own spread columns are NOT used by the
    plane); tradable bars are hour <= 19; the day-close bar is the LAST
    TRADABLE bar of the day (the 19:00 bar) and its CLOSE prices settle
    force-flat exits; all other exits settle at the exit bar's OPEN."""
    cfg = load_pair_config(pair)
    pip_mult = 1.0 / cfg.pip
    df = pd.read_parquet(DERIVED / f"bars1h_ANC_{pair}.parquet")
    df = df[df["ts"] <= pd.Timestamp(f"{PANEL_END}T23:59:59Z")]
    ts = (df["ts"].dt.tz_convert("UTC").dt.tz_localize(None)
          .to_numpy().astype("datetime64[s]").astype("int64"))
    b_o = df["b_o"].to_numpy(); a_o = df["a_o"].to_numpy()
    b_c = df["b_c"].to_numpy(); a_c = df["a_c"].to_numpy()
    s_o = a_o - b_o              # SignalPlane recomputes, never reads
    s_c = a_c - b_c              # the parquet spread columns
    hour = (ts // 3600 % 24).astype(np.int32)
    day = ts // 86400
    tradable = hour <= 19
    last_of_day = {}
    for i in range(len(ts)):
        if tradable[i]:
            last_of_day[day[i]] = i
    is_day_close = np.zeros(len(ts), dtype=bool)
    is_day_close[[last_of_day[d] for d in day if d in last_of_day]] = True

    daemon = sorted([r for r in rows if r["book"] == "R-DAEMON"],
                    key=lambda r: (r["entry_ts"], r["exit_ts"]))
    rng = random.Random(SEED)
    sample = rng.sample(daemon, SAMPLE_N)

    def pnl_at(k, r):
        eb = int(np.searchsorted(ts, r["entry_ts"]))
        xb = int(np.searchsorted(ts, r["exit_ts"]))
        assert ts[eb] == r["entry_ts"] and ts[xb] == r["exit_ts"], \
            f"schedule ts mismatch {pair} {r['entry_ts_utc']}"
        d = r["dir"]
        entry_px = (b_o[eb] + k * s_o[eb]) if d > 0 \
            else (a_o[eb] - k * s_o[eb])
        if is_day_close[xb]:   # FORCE_FLAT at the day-close bar CLOSE
            exit_px = (a_c[xb] - k * s_c[xb]) if d > 0 \
                else (b_c[xb] + k * s_c[xb])
        else:                  # reversal/target exit at the bar OPEN
            exit_px = (a_o[xb] - k * s_o[xb]) if d > 0 \
                else (b_o[xb] + k * s_o[xb])
        return (exit_px - entry_px) * d * pip_mult

    details = []
    max_dev = 0.0
    for r in sample:
        g = pnl_at(0.0, r)
        n1 = pnl_at(1.0, r)
        dev = max(abs(g - r["gross_pips"]), abs(n1 - r["net_pips"]),
                  abs((n1 - g) - r["cost_pips"]))
        max_dev = max(max_dev, float(dev))
        details.append({
            "entry_ts_utc": r["entry_ts_utc"], "exit_ts_utc": r["exit_ts_utc"],
            "dir": r["dir"], "fold": r["fold"], "exit_type": r["exit_type"],
            "attrib_gross": r["gross_pips"], "recomputed_gross": r2(g),
            "attrib_net": r["net_pips"], "recomputed_net": r2(n1),
            "attrib_cost": r["cost_pips"], "recomputed_cost": r2(n1 - g),
            "max_abs_dev_pips": float(dev),
        })
    return {
        "pair": pair, "seed": SEED, "n_sampled": len(sample),
        "tolerance_pips": SAMPLE_TOL_PIPS,
        "max_abs_dev_pips": float(max_dev),
        "verdict": "PASS" if max_dev <= SAMPLE_TOL_PIPS else "DEVIATION",
        "sampled_trades": details,
    }


# ------------------------------------------------------------------ T4 ----

def ceiling_arithmetic(pair: str) -> dict:
    """F-5-style ceiling: full RT cost at k=1.0 and x2.0 stress from the
    committed census session spread curves (conditional, never global
    p50). RT(bucket) = entry crossing + exit crossing, both filled at
    that bucket's conditional spread."""
    c = json.loads((DIAG_DERIVED / f"census_{pair}.json").read_text())
    bs = c["spread_pips"]["by_session_open"]
    out = {"pair": pair, "source": "census spread_pips.by_session_open",
           "buckets": {}}
    for b in SESSION_BUCKETS + BREAK_BUCKETS:
        p50 = bs[b]["50"]; p90 = bs[b]["90"]
        rt_k1 = 2 * p50
        rt_k2 = 2 * (2 * p50)
        out["buckets"][b] = {
            "crossing_p50_pips": p50, "crossing_p90_pips": p90,
            "rt_base_k1_pips": r2(rt_k1),
            "rt_stress_k2_pips": r2(rt_k2),
            "nonfragile_line_2x_stress_pips": r2(2 * rt_k2),
            "sentence": (
                f"a candidate must declare a gross premium per round trip "
                f"above {r2(rt_k1)} pips at base / {r2(2 * rt_k2)} pips at "
                f"x2.0 stress to be non-fragile if BOTH fills land in the "
                f"{b} book"),
        }
    # mixed case matching the cohort's actual law: session entry, force-flat
    # exit at the day-close bar (ny_late_16_21 book at the 19:00-bar close)
    sess = min(bs["london_07_12"]["50"], bs["ny_overlap_12_16"]["50"])
    mix_k1 = sess + bs["ny_late_16_21"]["50"]
    out["cohort_law_mixed_rt"] = {
        "definition": "entry crossing at best regular-session p50 "
                      "(london/ny-overlap) + exit crossing at the "
                      "day-close (ny_late_16_21) p50",
        "rt_base_k1_pips": r2(mix_k1),
        "rt_stress_k2_pips": r2(2 * mix_k1),
        "nonfragile_line_2x_stress_pips": r2(4 * mix_k1),
    }
    return out


# ------------------------------------------------------------------ T5 ----

def exit_type_cost(rows: list) -> dict:
    out = {}
    for f in FOLD_IDS:
        fr = [r for r in rows if r["book"] == "R-DAEMON" and r["fold"] == f]
        rec = {}
        for xt in ("FORCE_FLAT", "REVERSAL", "TARGET_EXIT"):
            xr = [r for r in fr if r["exit_type"] == xt]
            rec[xt] = {
                "rt": len(xr),
                "mean_cost_per_rt_pips":
                    r4(-sum(r["cost_pips"] for r in xr) / len(xr))
                    if xr else None,
                "cost_pips": r2(sum(r["cost_pips"] for r in xr)),
            }
        out[f] = rec
    return out


# ------------------------------------------------------------------ main --

def main() -> dict:
    result = {"schema": "failres_costexec_agg@1", "labels": LABELS,
              "seed": SEED, "pairs": {}}
    for pair in PAIRS:
        rows = load_rows(pair)
        agg = load_agg(pair)
        daily = load_daily_sp50(pair)
        census = json.loads(
            (DIAG_DERIVED / f"census_{pair}.json").read_text())
        panel_p50 = census["spread_pips"]["overall_open"]["50"]

        ft = fold_tables(rows)
        # k-decay restated from the attribution agg (B.10) — read, verified
        # by summation identity only.
        for f in FOLD_IDS:
            ft[f]["k_decay_from_attrib_agg"] = agg["k_decay_R-DAEMON"][f]
            # summation identity: per-fold net(k=1.0) from rows must equal
            # the agg's k_decay 1.0 entry within rounding
            assert abs(ft[f]["net_pips"]
                       - agg["k_decay_R-DAEMON"][f]["1.0"]) <= 0.05, \
                f"{pair} {f}: rows/agg k=1.0 mismatch"

        sr = spread_regime(rows, daily, panel_p50)
        sv = recompute_pair(pair, rows)
        ca = ceiling_arithmetic(pair)
        et = exit_type_cost(rows)

        dr = [r for r in rows if r["book"] == "R-DAEMON"
              and r["fold"] in FOLD_IDS]
        k0_by_fold = {f: ft[f]["gross_pips"] for f in FOLD_IDS}
        sign_flips = [f for f in FOLD_IDS
                      if ft[f]["net_pips"] < 0 and ft[f]["gross_pips"] > 0]

        result["pairs"][pair] = {
            "labels": LABELS,
            "rt_fold_rows": int(len(dr)),
            "panel_p50_entry_spread_census_pips": panel_p50,
            "T1_fold_table": ft,
            "T2_spread_regime": sr,
            "T3_sample_verification": sv,
            "T4_ceiling": ca,
            "T5_exit_type_cost": et,
            "T6_reading": {
                "k0_gross_by_fold_pips": k0_by_fold,
                "folds_negative_net_positive_gross_sign_flip": sign_flips,
                "note": "sign flip = fold whose net sign would flip at "
                        "zero cost (k=0 gross); facts only",
            },
        }

        # console summary for the report
        print(f"\n===== {pair} =====")
        for f in FOLD_IDS:
            t = ft[f]
            print(f"{f}: rt={t['rt']:4d} gross={t['gross_pips']:9.2f} "
                  f"cost={t['cost_pips']:8.2f} net={t['net_pips']:9.2f} "
                  f"mean_cost/RT={t['mean_cost_per_rt_pips']:.4f} "
                  f"verdict={t['verdict']}")
            if t["verdict"]:
                print(f"     arithmetic: net {t['net_pips']} = gross "
                      f"{t['gross_pips']} + cost {t['cost_pips']}; "
                      f"loss {-t['net_pips']:.2f} -> cost share "
                      f"{t['cost_share_of_loss']:.3f}, gross share "
                      f"{t['gross_share_of_loss']:.3f}")
        print(f"sample verification: {sv['verdict']} "
              f"max_abs_dev={sv['max_abs_dev_pips']:.6f} pips "
              f"(n={sv['n_sampled']}, tol={sv['tolerance_pips']})")
        print(f"T2 per_fold: " + json.dumps(sr["per_fold"]))
        print(f"T6 sign flips: {sign_flips}")

    out_path = FAILRES / "failres_costexec_agg.json"
    out_path.write_text(json.dumps(result, indent=1, default=str) + "\n")
    print(f"\nwrote {out_path}")
    return result


if __name__ == "__main__":
    main()
