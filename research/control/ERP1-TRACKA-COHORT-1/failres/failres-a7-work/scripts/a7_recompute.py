"""A7 L2 — independent book recomputation with A7's OWN executor.

The fill law is reimplemented here directly from the committed engine
DOCSTRING semantics (engine.py is NOT imported, not called):
  - signal = target array on the CLOSED bar t; fill at bar t+1 open;
  - marketable fills at the OPPOSITE quote, k x that bar's own spread:
      open long  buy  at b_o + k*s_o      open short sell at a_o - k*s_o
      close long sell at a_o - k*s_o      close short buy  at b_o + k*s_o
    day-close force-flat closes use the CLOSE spread s_c likewise;
  - no fills on/after the day-close bar (H1 law: fill_ok = tradable &
    hour <= 18; day-close = last tradable bar, hour 19);
  - force-flat at the day-close bar's close; flat over gaps/weekends by
    construction (day-close every traded day).
Per-trade pips rounded to 2 dp exactly as the engine records them.

Signal laws are the FROZEN OBJECTS UNDER AUDIT and are imported from
tracka_lib (allowed by dispatch); SHORT/LONG_ALWAYS session targets and
all fills/aggregation/fold-assignment/exit-type logic are A7's own.

Planes: EURUSD = A7's own rebuilt parquet (L1); GBPUSD = the audited
byte copy (L1 rebuild was EURUSD-only per dispatch; disclosed).
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

A7_WORK = Path(__file__).resolve().parent.parent
COHORT = A7_WORK.parent
REBUILD_EURUSD = A7_WORK / "derived" / "bars1h_ANC_EURUSD_A7.parquet"
AUDITED_GBPUSD = ("/Users/hoangminhlong/my-quantitative/.worktrees/"
                  "erp1-tracka-cohort-1/failres-attrib/research/control/"
                  "ERP1-TRACKA-COHORT-1/failres/data_local/derived/"
                  "bars1h_ANC_GBPUSD.parquet")
FAILRES = COHORT / "failres"
RESULTS = A7_WORK / "layer_results"
PANEL_END = "2026-06-30"

sys.path.insert(0, str(COHORT / "scripts"))
sys.path.insert(0, str(COHORT / "diag" / "scripts"))
import tracka_lib as T  # noqa: E402
from falsifier_run import FOLD_TABLE  # noqa: E402

FOLD_IDS = [f for f, _, _ in FOLD_TABLE]
SEC_DAY = 86400

# C5 targets — DIAG_DAEMON_REPORT §3.1/§3.2 as claimed in the audited
# ATTRIB_failres_REPORT §0 (independent targets, not the lane's JSONs)
C5_EURUSD_RDAEMON_FOLDS = {"F1": -188.8, "F2": -884.4, "F3": 1049.8,
                           "F4": 348.3, "F5": -191.5, "F6": 257.0}
C5_EURUSD_TOTALS = {"R-DAEMON": 812.2, "R-ORIG": 7322.7, "R-ANCHOR": 1052.7,
                    "SHORT_ALWAYS": 704.6, "LONG_ALWAYS": -1665.5}
C5_EURUSD_RDAEMON_RT = 1062
C5_GBPUSD_RDAEMON_TOTAL = -1708.9
C5_GBPUSD_RDAEMON_F3 = -1272.7


def ts_of(day_str: str, end: bool = False) -> int:
    t = dt.datetime.fromisoformat(day_str).replace(tzinfo=dt.timezone.utc)
    if end:
        t = t + dt.timedelta(days=1) - dt.timedelta(seconds=1)
    return int(t.timestamp())


FOLD_WIN = {f: (ts_of(s), ts_of(e, end=True)) for f, s, e in FOLD_TABLE}


def load_plane_eurusd() -> T.SignalPlane:
    df = pd.read_parquet(REBUILD_EURUSD)
    if np.issubdtype(df["ts"].dtype, np.integer):
        df["ts"] = pd.to_datetime(df["ts"], unit="s", utc=True)
    df = df[df["ts"] <= pd.Timestamp(f"{PANEL_END}T23:59:59Z")]
    return T.SignalPlane(df, pip_mult=1e4)


def load_plane_gbpusd() -> T.SignalPlane:
    df = pd.read_parquet(AUDITED_GBPUSD)
    df = df[df["ts"] <= pd.Timestamp(f"{PANEL_END}T23:59:59Z")]
    return T.SignalPlane(df, pip_mult=1e4)


# ------------------------------------------------- A7's own executor -------

def a7_run(p, tgt, k: float):
    """Independent fill-law executor (see module docstring). Returns the
    round-trip list: entry_ts, exit_ts, dir, pips (2dp), hold_bars."""
    n = len(p.ts)
    pos = 0
    entry_i = -1
    entry_px = 0.0
    trades = []

    def close_trade(i, exit_px):
        nonlocal pos
        pnl = (exit_px - entry_px) * pos * p.pip_mult
        trades.append({"entry_ts": int(p.ts[entry_i]),
                       "exit_ts": int(p.ts[i]), "dir": int(pos),
                       "pips": round(float(pnl), 2),
                       "hold_bars": int(i - entry_i)})
        pos = 0

    for i in range(n):
        if p.is_day_close[i]:
            if pos != 0:
                px = (p.a_c[i] - k * p.s_c[i]) if pos > 0 \
                    else (p.b_c[i] + k * p.s_c[i])
                close_trade(i, px)
            continue
        want = int(tgt[i - 1]) if i > 0 else 0
        if not p.fill_ok[i]:
            want = 0
        if want != pos:
            if pos != 0:
                px = (p.a_o[i] - k * p.s_o[i]) if pos > 0 \
                    else (p.b_o[i] + k * p.s_o[i])
                close_trade(i, px)
            if want != 0:
                pos = want
                entry_i = i
                entry_px = (p.b_o[i] + k * p.s_o[i]) if want > 0 \
                    else (p.a_o[i] - k * p.s_o[i])
    if pos != 0:
        raise SystemExit("FAIL: open position past final day-close")
    return trades


def a7_exit_types(p, trades) -> list:
    out = []
    for j, t in enumerate(trades):
        xb = int(np.searchsorted(p.ts, t["exit_ts"]))
        if p.is_day_close[xb]:
            out.append("FORCE_FLAT")
        elif j + 1 < len(trades) and trades[j + 1]["entry_ts"] == t["exit_ts"]:
            out.append("REVERSAL")
        else:
            out.append("TARGET_EXIT")
    return out


def a7_daily_series(trades, lo: int, hi: int) -> np.ndarray:
    per_day = {}
    for t in trades:
        d = t["entry_ts"] // SEC_DAY
        per_day[d] = per_day.get(d, 0.0) + t["pips"]
    days = np.arange(lo // SEC_DAY, hi // SEC_DAY + 1)
    return np.array([per_day.get(int(d), 0.0) for d in days], dtype=float)


def pearson(x, y) -> float:
    xm, ym = x - x.mean(), y - y.mean()
    den = float(np.sqrt((xm * xm).sum() * (ym * ym).sum()))
    return float((xm * ym).sum() / den) if den > 0 else 0.0


def fold_nets(trades) -> dict:
    per = {f: 0.0 for f in FOLD_IDS}
    rt = {f: 0 for f in FOLD_IDS}
    tot = 0.0
    n = 0
    for t in trades:
        v = float(t["pips"])
        tot += v
        n += 1
        for f, (lo, hi) in FOLD_WIN.items():
            if lo <= t["entry_ts"] <= hi:
                per[f] += v
                rt[f] += 1
                break
    return {"total": round(tot, 2), "rt": n,
            "per_fold": {f: round(v, 2) for f, v in per.items()},
            "per_fold_rt": rt}


# ----------------------------------------------------------------- main ----

def close_enough(mine, claim, tol=0.05) -> dict:
    return {"claim": claim, "a7": mine, "delta": round(mine - claim, 6),
            "pass": bool(abs(mine - claim) <= tol)}


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = {"schema": "a7_l2_recompute@1",
           "labels": ["A7_INDEPENDENT_REPRODUCTION",
                      "FAILURE_ROOT_CAUSE_RESEARCH",
                      "DIAGNOSTIC_OUTCOME_EXPOSED"],
           "executor": "a7 own fill-law executor (engine.py not imported)",
           "planes": {"EURUSD": "A7 rebuilt (L1)", "GBPUSD": "audited copy"},
           "checks": []}

    for pair in ("EURUSD", "GBPUSD"):
        p = load_plane_eurusd() if pair == "EURUSD" else load_plane_gbpusd()
        sess = ((~p.skip) & (p.hour >= 7) & (p.hour <= 18)).astype(np.int8)
        tgt_d, first_mode, changes = T.f_rangeexp_daemon(p)
        tgts = {"R-DAEMON": tgt_d,
                "R-ORIG": T.f_rangeexp_orig(p),
                "R-ANCHOR": T.f_rangeexp_anchor_shift(p),
                "SHORT_ALWAYS": (-sess).astype(np.int8),
                "LONG_ALWAYS": sess.astype(np.int8)}
        books = {}
        for arm, tgt in tgts.items():
            t1 = a7_run(p, tgt, 1.0)
            t0 = a7_run(p, tgt, 0.0)
            if len(t1) != len(t0) or any(
                    (a["entry_ts"], a["exit_ts"], a["dir"]) !=
                    (b["entry_ts"], b["exit_ts"], b["dir"])
                    for a, b in zip(t1, t0)):
                raise SystemExit(f"FAIL {arm}: k0/k1 schedules differ")
            books[arm] = t1
        d = f"_{pair}" if False else ""
        res_pair = {"pair": pair}

        # ---- (a) C5: fold nets + totals --------------------------------
        if pair == "EURUSD":
            fn = fold_nets(books["R-DAEMON"])
            for f, v in C5_EURUSD_RDAEMON_FOLDS.items():
                res_pair[f"C5_RDAEMON_{f}"] = close_enough(
                    fn["per_fold"][f], v)
                res_pair[f"C5_RDAEMON_{f}_rt"] = {
                    "claim": None, "a7": fn["per_fold_rt"][f]}
            for arm, v in C5_EURUSD_TOTALS.items():
                fna = fold_nets(books[arm])
                res_pair[f"C5_total_{arm}"] = close_enough(fna["total"], v)
            res_pair["C5_RDAEMON_RT"] = {
                "claim": C5_EURUSD_RDAEMON_RT, "a7": fn["rt"],
                "pass": fn["rt"] == C5_EURUSD_RDAEMON_RT}
        else:
            fn = fold_nets(books["R-DAEMON"])
            res_pair["C5_GBPUSD_total"] = close_enough(
                fn["total"], C5_GBPUSD_RDAEMON_TOTAL)
            res_pair["C5_GBPUSD_F3"] = close_enough(
                fn["per_fold"]["F3"], C5_GBPUSD_RDAEMON_F3)

        # ---- (b) C1: exit-type split (R-DAEMON, k=1.0) -----------------
        xt = a7_exit_types(p, books["R-DAEMON"])
        rd = books["R-DAEMON"]

        def xt_pool(fold, kind):
            sel = [(t, x) for t, x in zip(rd, xt)
                   if x == kind and FOLD_WIN[fold][0] <= t["entry_ts"]
                   <= FOLD_WIN[fold][1]]
            return {"rt": len(sel),
                    "net": round(sum(t["pips"] for t, _ in sel), 2)}

        rev_total = sum(1 for x in xt if x == "REVERSAL")
        res_pair["C1_REVERSAL_count_full"] = {
            "claim": 0, "a7": rev_total, "pass": rev_total == 0}
        f2s, f2e = FOLD_WIN["F2"]
        # REPORT §2 per-pair F2 FF/TE claims
        ff_f2_claim, ff_f2_rt_claim = ((-2116.5, 128) if pair == "EURUSD"
                                       else (-1489.9, 131))
        te_f2_claim, te_f2_rt_claim = ((1232.1, 38) if pair == "EURUSD"
                                       else (1601.1, 41))
        sel_ff = [t for t, x in zip(rd, xt) if x == "FORCE_FLAT"
                  and f2s <= t["entry_ts"] <= f2e]
        sel_te = [t for t, x in zip(rd, xt) if x == "TARGET_EXIT"
                  and f2s <= t["entry_ts"] <= f2e]
        res_pair["C1_FF_F2"] = close_enough(
            round(sum(t["pips"] for t in sel_ff), 2), ff_f2_claim)
        res_pair["C1_FF_F2_rt"] = {"claim": ff_f2_rt_claim, "a7": len(sel_ff),
                                   "pass": len(sel_ff) == ff_f2_rt_claim}
        res_pair["C1_TE_F2"] = close_enough(
            round(sum(t["pips"] for t in sel_te), 2), te_f2_claim)
        res_pair["C1_TE_F2_rt"] = {"claim": te_f2_rt_claim, "a7": len(sel_te),
                                   "pass": len(sel_te) == te_f2_rt_claim}
        # REPORT §2 full-panel FF/TE claims (both pairs)
        ff_full_claim, ff_full_rt_claim = ((-5466.2, 839) if pair == "EURUSD"
                                           else (-9429.7, 842))
        te_full_claim, te_full_rt_claim = ((6278.4, 223) if pair == "EURUSD"
                                           else (7720.8, 224))
        sel_ff = [t for t, x in zip(rd, xt) if x == "FORCE_FLAT"]
        sel_te = [t for t, x in zip(rd, xt) if x == "TARGET_EXIT"]
        res_pair["C1_FF_full"] = close_enough(
            round(sum(t["pips"] for t in sel_ff), 2), ff_full_claim)
        res_pair["C1_FF_full_rt"] = {"claim": ff_full_rt_claim,
                                     "a7": len(sel_ff),
                                     "pass": len(sel_ff) == ff_full_rt_claim}
        res_pair["C1_TE_full"] = close_enough(
            round(sum(t["pips"] for t in sel_te), 2), te_full_claim)
        res_pair["C1_TE_full_rt"] = {"claim": te_full_rt_claim,
                                     "a7": len(sel_te),
                                     "pass": len(sel_te) == te_full_rt_claim}
        # sign checks + REPORT §2 per-fold table, every pair-fold
        table_claims = {
            "EURUSD": {"F1": (-909.6, 121, 720.8, 43),
                       "F2": (-2116.5, 128, 1232.1, 38),
                       "F3": (-608.5, 120, 1658.3, 44),
                       "F4": (-668.7, 129, 1017.0, 37),
                       "F5": (-854.9, 135, 663.4, 24),
                       "F6": (-460.3, 133, 717.3, 24)},
            "GBPUSD": {"F1": (-1205.7, 121, 1084.2, 35),
                       "F2": (-1489.9, 131, 1601.1, 41),
                       "F3": (-2463.2, 134, 1190.5, 26),
                       "F4": (-643.8, 119, 1433.6, 40),
                       "F5": (-1464.2, 129, 1057.1, 36),
                       "F6": (-1664.1, 131, 935.3, 30)},
        }
        signs = {}
        for f in FOLD_IDS:
            ff, te = xt_pool(f, "FORCE_FLAT"), xt_pool(f, "TARGET_EXIT")
            cl = table_claims[pair][f]
            signs[f] = {"FF_net": ff["net"], "FF_rt": ff["rt"],
                        "TE_net": te["net"], "TE_rt": te["rt"],
                        "ff_negative": ff["net"] < 0 if ff["rt"] else None,
                        "te_positive": te["net"] > 0 if te["rt"] else None,
                        "table_match": bool(
                            ff["net"] == cl[0] and ff["rt"] == cl[1]
                            and te["net"] == cl[2] and te["rt"] == cl[3])}
        res_pair["C1_per_fold"] = signs
        res_pair["C1_FF_negative_all_folds"] = {
            "claim": "all 6 folds", "a7": all(v["ff_negative"]
                                              for v in signs.values()),
            "pass": all(v["ff_negative"] for v in signs.values())}
        res_pair["C1_TE_positive_all_folds"] = {
            "claim": "all 6 folds", "a7": all(v["te_positive"]
                                              for v in signs.values()),
            "pass": all(v["te_positive"] for v in signs.values())}

        if pair == "EURUSD":
            # ---- (c) C2: F2 gross/cost + direction ---------------------
            t0 = a7_run(p, tgt_d, 0.0)
            gross = {t["entry_ts"]: t["pips"] for t in t0}
            f2 = [t for t in rd if f2s <= t["entry_ts"] <= f2e]
            net_f2 = round(sum(t["pips"] for t in f2), 2)
            # k-decay supplement (REPORT §3): A7 executor at k=1.5/2.0
            kd_15 = round(sum(t["pips"] for t in a7_run(p, tgt_d, 1.5)
                              if f2s <= t["entry_ts"] <= f2e), 2)
            kd_20 = round(sum(t["pips"] for t in a7_run(p, tgt_d, 2.0)
                              if f2s <= t["entry_ts"] <= f2e), 2)
            res_pair["C_kdecay_F2_A7"] = {
                "claim": {"1.0": -884.4, "1.5": -942.1, "2.0": -999.7},
                "a7": {"1.0": net_f2, "1.5": kd_15, "2.0": kd_20},
                "pass": bool(abs(kd_15 - (-942.1)) <= 0.0501
                             and abs(kd_20 - (-999.7)) <= 0.05)}
            gross_f2 = round(sum(gross[t["entry_ts"]] for t in f2), 2)
            cost_f2 = round(net_f2 - gross_f2, 2)
            res_pair["C2_F2_net"] = close_enough(net_f2, -884.4)
            res_pair["C2_F2_gross"] = close_enough(gross_f2, -769.1)
            res_pair["C2_F2_cost"] = close_enough(cost_f2, -115.3)
            lng = [t for t in f2 if t["dir"] > 0]
            sht = [t for t in f2 if t["dir"] < 0]
            res_pair["C2_F2_long"] = close_enough(
                round(sum(t["pips"] for t in lng), 2), -696.0)
            res_pair["C2_F2_long_rt"] = {"claim": 95, "a7": len(lng),
                                         "pass": len(lng) == 95}
            res_pair["C2_F2_short"] = close_enough(
                round(sum(t["pips"] for t in sht), 2), -188.4)
            res_pair["C2_F2_short_rt"] = {"claim": 71, "a7": len(sht),
                                          "pass": len(sht) == 71}

            # ---- (d) C3: flip-day pools (F2) ---------------------------
            flips, nonflips = [], []
            for t in f2:
                day = t["entry_ts"] // SEC_DAY
                (flips if changes.get(day, 0) > 0 else nonflips).append(t)
            fl_net = round(sum(t["pips"] for t in flips), 2)
            nf_net = round(sum(t["pips"] for t in nonflips), 2)
            res_pair["C3_flip_net"] = close_enough(fl_net, -1455.5)
            res_pair["C3_flip_rt"] = {"claim": 102, "a7": len(flips),
                                      "pass": len(flips) == 102}
            res_pair["C3_flip_mean"] = {
                "claim": -14.27,
                "a7": round(fl_net / len(flips), 4) if flips else None,
                "pass": bool(abs(fl_net / len(flips) - (-14.27)) <= 0.005)
                if flips else False}
            res_pair["C3_nonflip_net"] = close_enough(nf_net, 571.1)
            res_pair["C3_nonflip_rt"] = {"claim": 64, "a7": len(nonflips),
                                         "pass": len(nonflips) == 64}
            res_pair["C3_nonflip_mean"] = {
                "claim": 8.92,
                "a7": round(nf_net / len(nonflips), 4) if nonflips else None,
                "pass": bool(abs(nf_net / len(nonflips) - 8.92) <= 0.005)
                if nonflips else False}

            # ---- (e) C4: beta pull (F2) --------------------------------
            lo, hi = FOLD_WIN["F2"]
            x = a7_daily_series(books["R-DAEMON"], lo, hi)
            ys = a7_daily_series(books["SHORT_ALWAYS"], lo, hi)
            rho = pearson(x, ys)
            res_pair["C4_rho_daily_daemon_vs_short_F2"] = {
                "claim": -0.189, "a7": round(rho, 6),
                "pass": bool(abs(rho - (-0.189)) <= 1e-6 + 5e-4)}
            res_pair["C4_daemon_minus_short_F2"] = close_enough(
                round(float(x.sum() - ys.sum()), 2), -1723.2)

        out["checks"].append(res_pair)
        print(f"[{pair}] computed: "
              + json.dumps({k: v for k, v in res_pair.items()
                            if k.startswith("C5_")
                            and isinstance(v, dict) and "a7" in v},
                           default=str)[:400])

    n_bad = sum(1 for rp in out["checks"] for k, v in rp.items()
                if isinstance(v, dict) and v.get("pass") is False)
    out["failed_checks"] = n_bad
    out["verdict"] = "ALL_MATCH" if n_bad == 0 else "DIFFS"
    (RESULTS / "a7_l2_recompute.json").write_text(
        json.dumps(out, indent=1, default=str) + "\n")
    print(json.dumps({"failed_checks": n_bad, "verdict": out["verdict"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
