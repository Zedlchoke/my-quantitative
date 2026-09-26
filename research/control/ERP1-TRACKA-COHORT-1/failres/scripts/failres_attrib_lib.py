"""ATTRIBUTION lane library — ERP1-TRACKA-COHORT-1 / failres-attrib (Phase A).

FAILURE_ROOT_CAUSE_RESEARCH · DIAGNOSTIC_OUTCOME_EXPOSED ·
SINGLE_SOURCE_PANEL · FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK · PAPER_TIER.

Owner instruction (2026-09-26, verbatim intent): explain why the EURUSD
R-DAEMON shadow law is losing in F1/F2/F5, especially F2 2021-11..2022-08.
Phase A = attribution DECOMPOSITION, facts only, no winner-picking, no
strategy proposal, no tuning (one pass, frozen laws only). NOTHING here is
promotable evidence regardless of result; correlation != causation; no
event overlay happens in this lane.

Machinery reused UNMODIFIED from the committed cycle + diag lane:
  engine.run_strategy        fill/cost law (signal on closed bar -> next H1
                             open at the opposite quote; cost = fill bar's
                             own spread x k; no fills on/after 19:00;
                             force-flat at the day-close 20:00 UTC)
  tracka_lib.f_rangeexp_*    the three laws (R-DAEMON / R-ORIG / R-ANCHOR)
  falsifier_run.FOLD_TABLE   the ONLY fold authority (imported, never
                             redefined)
  diag_lib conventions       plane loading, 5-book set, warmup_end_idx=0

Cost decomposition is NOT a variant: the SAME book is re-run at k=0.0
(zero-cost fills; the engine state machine is price-independent, so the
trade schedule is identical) and per-trade cost := net(k=1.0) - net(k=0.0).

The R-DAEMON walk is additionally instrumented with a per-bar mode-label
array (labeled_daemon below: verbatim copy of tracka_lib.f_rangeexp_daemon
plus label recording); the run asserts the instrumented target and the
first-mode/change dicts are IDENTICAL to the authoritative machinery, so
the labels cannot diverge from the scored law.

R-ORIG numbers carry provenance R-ORIG-SEMANTICS (leaky law, placement
reference only; citation law of INCIDENT_RANGEFADE_PIT_SEAM_2026-09-25).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

COHORT = Path(__file__).resolve().parent.parent.parent   # .../ERP1-TRACKA-COHORT-1
FAILRES = COHORT / "failres"
DERIVED = FAILRES / "data_local" / "derived"
for _p in (str(COHORT / "scripts"), str(COHORT / "diag" / "scripts"),
           str(FAILRES / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import engine as E  # noqa: E402
import tracka_lib as T  # noqa: E402
import scored_lib as S  # noqa: E402
from falsifier_run import FOLD_TABLE, ts_of  # noqa: E402
from pair_config_diag import load_pair_config  # noqa: E402

SEC_DAY = T.SEC_DAY
PAIRS = ("EURUSD", "GBPUSD")
PANEL_END = "2026-06-30"
PANEL_START = "2021-01-01"
BOOKS = ("R-DAEMON", "R-ORIG", "R-ANCHOR", "SHORT_ALWAYS", "LONG_ALWAYS")
LABELS = ["FAILURE_ROOT_CAUSE_RESEARCH", "DIAGNOSTIC_OUTCOME_EXPOSED",
          "SINGLE_SOURCE_PANEL", "FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK",
          "PAPER_TIER"]
HOUR_BUCKETS = (("asia_00_06", 0, 6), ("london_07_12", 7, 12),
                ("ny_13_18", 13, 18))
MODES = ("flat", "fade", "follow")
BAR_LABEL = {0: "flat", 1: "fade", 2: "follow"}
FOLD_IDS = [f for f, _, _ in FOLD_TABLE]


def sha256_file(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def iso(ts_epoch: int) -> str:
    return dt.datetime.fromtimestamp(int(ts_epoch), tz=dt.timezone.utc) \
        .strftime("%Y-%m-%dT%H:%M:%SZ")


def date_of(day_epoch: int) -> str:
    return dt.datetime.fromtimestamp(int(day_epoch) * SEC_DAY,
                                     tz=dt.timezone.utc).strftime("%Y-%m-%d")


# ------------------------------------------------------------- plane/loader --

def load_plane(pair: str) -> T.SignalPlane:
    """diag_lib.load_plane convention, pointed at the failres byte-copy
    dir (sha256-pinned in failres_attrib_PROVENANCE.json)."""
    cfg = load_pair_config(pair)
    df = pd.read_parquet(DERIVED / f"bars1h_ANC_{pair}.parquet")
    df = df[df["ts"] <= pd.Timestamp(f"{PANEL_END}T23:59:59Z")]
    return T.SignalPlane(df, pip_mult=1.0 / cfg.pip)


def labeled_daemon(p: T.SignalPlane, lo_q=0.3, hi_q=0.7,
                   use_breakout=False, hist_len=T.HIST_LEN):
    """VERBATIM copy of tracka_lib.f_rangeexp_daemon (frozen law) plus a
    per-bar mode-label code array (0 flat / 1 fade / 2 follow) recorded on
    the same control-flow paths. The run script asserts array/dict equality
    against the authoritative T.f_rangeexp_daemon output."""
    days, ranges = T.day_ranges(p)
    prev = T._day_prev_map(days)
    hist_full = []
    hist_before = {}
    for d in days:
        hist_before[d] = sorted(hist_full[-hist_len:])
        if d in ranges:
            hist_full.append(ranges[d][0])
    run_hi = run_lo = None
    cur_day = -1
    pos = 0
    tgt = np.zeros(len(p.ts), dtype=np.int8)
    bar_label = np.zeros(len(p.ts), dtype=np.int8)
    day_first_mode = {}
    day_mode_changes = {}
    last_label = {}
    seen_in_session = set()
    for i in range(len(p.ts)):
        if p.skip[i]:
            continue
        d = p.day[i]
        if d != cur_day:
            cur_day, pos = d, 0
            run_hi, run_lo = -np.inf, np.inf
        run_hi = max(run_hi, p.b_h[i])
        run_lo = min(run_lo, p.b_l[i])
        hb = hist_before.get(d)
        mode = None
        if hb:
            mode = float(np.searchsorted(hb, run_hi - run_lo) / len(hb))
        pd_h = ranges[d][1] if d in ranges else None
        pd_l = ranges[d][2] if d in ranges else None
        if p.hour[i] < 7 or p.hour[i] > 18:
            tgt[i] = 0
            bar_label[i] = 0
            continue
        if d not in seen_in_session:
            seen_in_session.add(d)
            day_first_mode[d] = ("flat" if mode is None or mode <= 0
                                 else ("follow" if mode > hi_q else "fade"))
            last_label[d] = day_first_mode[d]
        if mode is None or mode <= 0 or pd_h is None:
            tgt[i] = 0
            bar_label[i] = 0
            continue
        label = "follow" if mode > hi_q else "fade"
        if last_label.get(d) != label:
            day_mode_changes[d] = day_mode_changes.get(d, 0) + 1
            last_label[d] = label
        expand = (mode > hi_q) if not use_breakout else (mode < lo_q)
        bar_label[i] = 2 if expand else 1
        if expand:
            if pos == 0:
                if p.b_c[i] > pd_h:
                    pos = 1
                elif p.b_c[i] < pd_l:
                    pos = -1
        else:
            mid = (pd_h + pd_l) / 2
            if pos == 0:
                if p.b_c[i] > pd_h:
                    pos = -1
                elif p.b_c[i] < pd_l:
                    pos = 1
            else:
                if abs(p.b_c[i] - mid) < (pd_h - pd_l) / 4:
                    pos = 0
        tgt[i] = pos
    return tgt, day_first_mode, day_mode_changes, bar_label


# ------------------------------------------------------------ day context ----

def day_context(p: T.SignalPlane, bar_label: np.ndarray,
                daemon_first_mode: dict, daemon_changes: dict) -> dict:
    """PIT day-level table keyed by day-epoch: ex_ante_vol_pct (= pct[d-1],
    the R-ANCHOR mode input — fully known at day start), day spread p50
    (open spread, tradable bars), daemon first mode / change counts, fold."""
    days, ranges = T.day_ranges(p)
    pct = T.pct_full_panel(days, ranges)
    prev = T._day_prev_map(days)
    spread_pips = p.s_o * p.pip_mult
    ins = (~p.skip) & (p.hour >= 7) & (p.hour <= 18)
    bars_by_day = {}
    for i in np.nonzero(~p.skip)[0]:
        bars_by_day.setdefault(int(p.day[i]), []).append(int(i))
    ctx = {}
    for d in days:
        di = bars_by_day.get(int(d), [])
        dp = prev.get(d)
        ex_ante = pct.get(dp) if dp is not None else None
        sp = spread_pips[di]
        ins_i = [i for i in di if ins[i]]
        ctx[int(d)] = {
            "date": date_of(d),
            "fold": S.fold_of_ts(int(d) * SEC_DAY),
            "ex_ante_vol_pct": None if ex_ante is None
            else round(float(ex_ante), 6),
            "day_spread_p50_pips": round(float(np.median(sp)), 4),
            "daemon_first_mode": daemon_first_mode.get(int(d), "flat"),
            "n_mode_changes": int(daemon_changes.get(int(d), 0)),
        }
    return ctx


def signed_exposure_by_day(p: T.SignalPlane, tgt: np.ndarray) -> dict:
    """Mean of the daemon target over each day's in-session bars
    (fraction long minus fraction short)."""
    ins = (~p.skip) & (p.hour >= 7) & (p.hour <= 18)
    vals = tgt[ins].astype(float)
    days = p.day[ins]
    out = {}
    for d in np.unique(days):
        m = days == d
        out[int(d)] = round(float(vals[m].mean()), 6)
    return out


def fold_in_session_exposure(p: T.SignalPlane, tgt: np.ndarray) -> dict:
    """B.8(i): mean signed daemon target over in-session bars per fold."""
    ins = (~p.skip) & (p.hour >= 7) & (p.hour <= 18)
    out = {}
    for f, s, e in FOLD_TABLE:
        m = ins & (p.ts >= ts_of(s)) & (p.ts <= ts_of(e, end=True))
        out[f] = round(float(tgt[m].astype(float).mean()), 6) if m.any() \
            else 0.0
    return out


# ------------------------------------------------------------------ books ----

def build_books(p: T.SignalPlane):
    """Run the 5 diagnostic books through the committed engine: k=1.0 and
    k=0.0 for every arm (cost decomposition), plus R-DAEMON at k=1.5/2.0
    (k-decay). Asserts the labeled daemon == authoritative daemon and that
    the k=0/k=1 schedules are identical (price-independent state machine)."""
    sess = ((~p.skip) & (p.hour >= 7) & (p.hour <= 18)).astype(np.int8)
    tgt_auth, first_mode, changes = T.f_rangeexp_daemon(p)
    tgt_lab, first_mode_lab, changes_lab, bar_label = labeled_daemon(p)
    checks = {
        "labeled_daemon_tgt_identical": bool(np.array_equal(tgt_auth,
                                                            tgt_lab)),
        "labeled_daemon_first_mode_identical": first_mode == first_mode_lab,
        "labeled_daemon_changes_identical": changes == changes_lab,
    }
    if not all(checks.values()):
        raise SystemExit(f"FAIL_CLOSED labeled daemon diverged: {checks}")
    tgts = {
        "R-DAEMON": tgt_auth,
        "R-ORIG": T.f_rangeexp_orig(p),
        "R-ANCHOR": T.f_rangeexp_anchor_shift(p),
        "SHORT_ALWAYS": (-sess).astype(np.int8),
        "LONG_ALWAYS": sess,
    }
    trades_by_book = {}
    for arm, tgt in tgts.items():
        t1, _ = E.run_strategy(p, tgt, 1.0, warmup_end_idx=0)
        t0, _ = E.run_strategy(p, tgt, 0.0, warmup_end_idx=0)
        if len(t1) != len(t0):
            raise SystemExit(f"FAIL_CLOSED {arm}: schedule differs across k")
        for a, b in zip(t1, t0):
            if (a["entry_ts"], a["exit_ts"], a["dir"]) != \
                    (b["entry_ts"], b["exit_ts"], b["dir"]):
                raise SystemExit(f"FAIL_CLOSED {arm}: schedule differs across k")
        trades_by_book[arm] = {"1.0": t1, "0.0": t0}
        if arm == "R-DAEMON":
            for k in (1.5, 2.0):
                tk, _ = E.run_strategy(p, tgt, k, warmup_end_idx=0)
                trades_by_book[arm][str(k)] = tk
    return trades_by_book, (first_mode, changes, bar_label), checks


def exit_types(p: T.SignalPlane, trades: list) -> list:
    """FORCE_FLAT if the exit bar is the day-close bar; else REVERSAL if the
    next trade enters at this trade's exit ts (same bar open, opposite dir
    by engine construction); else TARGET_EXIT."""
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


def trade_table(p: T.SignalPlane, pair: str, trades_by_book: dict,
                bar_label: np.ndarray, ctx: dict) -> list:
    """Per round-trip records (k=1.0) for R-DAEMON / R-ORIG / R-ANCHOR.
    gross = net at k=0.0 (zero-cost fills); cost = net(k1) - net(k0).
    mode_at_entry = instrumented daemon mode label at the entry's SIGNAL
    bar (entry bar index - 1)."""
    rows = []
    for arm in ("R-DAEMON", "R-ORIG", "R-ANCHOR"):
        t1 = trades_by_book[arm]["1.0"]
        t0 = trades_by_book[arm]["0.0"]
        xt = exit_types(p, t1)
        for j, (a, b) in enumerate(zip(t1, t0)):
            net = float(a["pips"])
            gross = float(b["pips"])
            e_day = int(a["entry_ts"] // SEC_DAY)
            c = ctx[e_day]
            eb = int(np.searchsorted(p.ts, a["entry_ts"]))
            xb = int(np.searchsorted(p.ts, a["exit_ts"]))
            rows.append({
                "book": arm,
                "pair": pair,
                "entry_ts": int(a["entry_ts"]),
                "entry_ts_utc": iso(a["entry_ts"]),
                "exit_ts": int(a["exit_ts"]),
                "exit_ts_utc": iso(a["exit_ts"]),
                "dir": int(a["dir"]),
                "fold": c["fold"],
                "day": c["date"],
                "net_pips": round(net, 2),
                "gross_pips": round(gross, 2),
                "cost_pips": round(net - gross, 2),
                "entry_hour_utc": int(p.hour[eb]),
                "exit_hour_utc": int(p.hour[xb]),
                "hold_bars": int(a["hold_bars"]),
                "exit_type": xt[j],
                "day_first_mode": c["daemon_first_mode"],
                "mode_at_entry": BAR_LABEL[int(bar_label[eb - 1])]
                if eb > 0 else "flat",
                "n_mode_changes_that_day": c["n_mode_changes"],
                "ex_ante_vol_pct": c["ex_ante_vol_pct"],
                "entry_bar_spread_pips":
                    round(float(p.s_o[eb] * p.pip_mult), 4),
                "exit_bar_spread_pips": round(float(
                    (p.s_c[xb] if p.is_day_close[xb] else p.s_o[xb])
                    * p.pip_mult), 4),
                "labels": LABELS + (["R-ORIG-SEMANTICS"]
                                    if arm == "R-ORIG" else []),
            })
    rows.sort(key=lambda r: (r["entry_ts"], r["book"]))
    return rows


# ------------------------------------------------------------- aggregation ---

def _bucket(rows) -> dict:
    n = len(rows)
    net = round(sum(r["net_pips"] for r in rows), 2)
    gross = round(sum(r["gross_pips"] for r in rows), 2)
    cost = round(sum(r["cost_pips"] for r in rows), 2)
    return {"rt": n, "net_pips": net, "gross_pips": gross, "cost_pips": cost,
            "mean_trade_pips": round(net / n, 4) if n else None}


def _group(rows, keyfn, order) -> dict:
    g = {}
    for r in rows:
        g.setdefault(keyfn(r), []).append(r)
    return {k: _bucket(g.get(k, [])) for k in order}


def daily_nets_by_book(trades_by_book: dict) -> dict:
    """net pips per entry-day per book (k=1.0)."""
    out = {}
    for arm in BOOKS:
        dn = {}
        for t in trades_by_book[arm]["1.0"]:
            d = int(t["entry_ts"] // SEC_DAY)
            dn[d] = dn.get(d, 0.0) + float(t["pips"])
        out[arm] = dn
    return out


def recon_block(pair: str, trades_by_book: dict, checks: dict) -> dict:
    """Reconciliation surface: full-panel net/RT + per-fold nets by ENTRY ts
    (folds = imported FOLD_TABLE) for all 5 books at k=1.0."""
    arms = {}
    for arm in BOOKS:
        per = {f: 0.0 for f in FOLD_IDS}
        rt = {f: 0 for f in FOLD_IDS}
        tot = 0.0
        n = 0
        for t in trades_by_book[arm]["1.0"]:
            v = float(t["pips"])
            tot += v
            n += 1
            fid = S.fold_of_ts(t["entry_ts"])
            if fid:
                per[fid] += v
                rt[fid] += 1
        arms[arm] = {"net_full_panel": round(tot, 2), "rt_full_panel": n,
                     "per_fold_net": {f: round(v, 2) for f, v in per.items()},
                     "per_fold_rt": rt}
    return {"labels": LABELS, "tolerance_pips": 0.05,
            "target_source": "DIAG_DAEMON_REPORT.md §3.1/§3.2 "
                             "(diag branch 4aae6226; byte-copied planes; "
                             "same committed engine/law imports)",
            "instrument_checks": checks,
            "arms": arms}


def aggregate_pair(pair: str, p: T.SignalPlane, trades_by_book: dict,
                   daemon_rows: list, all_rows: list, ctx: dict,
                   recon: dict) -> dict:
    """Phase-A per-fold aggregates (B.1-B.10). R-DAEMON decomposed fully;
    R-ORIG/R-ANCHOR get direction splits; SHORT/LONG enter the beta block."""
    folds = FOLD_IDS
    daemon_fold = {f: [r for r in daemon_rows if r["fold"] == f]
                   for f in folds}
    orig_rows = [r for r in all_rows if r["book"] == "R-ORIG"]
    anchor_rows = [r for r in all_rows if r["book"] == "R-ANCHOR"]
    dnets = daily_nets_by_book(trades_by_book)

    # ---- full-panel tercile cuts (descriptive, ONE pass, applied per fold)
    ex_vals = np.array([r["ex_ante_vol_pct"] for r in daemon_rows
                        if r["ex_ante_vol_pct"] is not None], dtype=float)
    ex_cuts = [round(float(x), 6) for x in
               np.percentile(ex_vals, [100 / 3, 200 / 3])]
    sp_vals = np.array([r["entry_bar_spread_pips"] for r in daemon_rows],
                       dtype=float)
    sp_cuts = [round(float(x), 6) for x in
               np.percentile(sp_vals, [100 / 3, 200 / 3])]

    def tercile_of(v, cuts):
        if v is None:
            return "na"
        return "t1_low" if v <= cuts[0] else ("t2_mid" if v <= cuts[1]
                                              else "t3_high")

    # day sets
    flat_days = {d for d, c in ctx.items() if c["daemon_first_mode"] == "flat"}
    active_days = set(ctx) - flat_days
    flip_days = {d for d, c in ctx.items() if c["n_mode_changes"] > 0}
    exp_fold = fold_in_session_exposure(
        p, _daemon_target_for_exposure(p, trades_by_book))
    fold_window = {f: (ts_of(s), ts_of(e, end=True))
                   for f, s, e in FOLD_TABLE}

    per_fold = {}
    for f in folds:
        lo, hi = fold_window[f]
        drows = daemon_fold[f]
        orows = [r for r in orig_rows if r["fold"] == f]
        arows = [r for r in anchor_rows if r["fold"] == f]
        days_in_fold = [d for d, c in ctx.items() if c["fold"] == f]

        by_dir = {}
        for nm, rows in (("R-DAEMON", drows), ("R-ORIG", orows),
                         ("R-ANCHOR", arows)):
            by_dir[nm] = {
                "long": _bucket([r for r in rows if r["dir"] > 0]),
                "short": _bucket([r for r in rows if r["dir"] < 0]),
            }

        by_mode_entry = _group(drows, lambda r: r["mode_at_entry"], MODES)

        dfm_days = {m: [d for d in days_in_fold
                        if ctx[d]["daemon_first_mode"] == m] for m in MODES}
        by_day_first_mode = {
            "_days_in_fold": {m: len(dfm_days[m]) for m in MODES},
            "_days_zero_daemon_trades": {
                m: sum(1 for d in dfm_days[m] if d not in dnets["R-DAEMON"])
                for m in MODES},
            **{m: _bucket([r for r in drows if r["day_first_mode"] == m])
               for m in MODES},
        }

        by_hour = {nm: _bucket([r for r in drows
                                if lo2 <= r["entry_hour_utc"] <= hi2])
                   for nm, lo2, hi2 in HOUR_BUCKETS}

        by_exante = {lab: _bucket([r for r in drows if
                                   tercile_of(r["ex_ante_vol_pct"],
                                              ex_cuts) == lab])
                     for lab in ("t1_low", "t2_mid", "t3_high", "na")}
        by_spread = {lab: _bucket([r for r in drows if
                                   tercile_of(r["entry_bar_spread_pips"],
                                              sp_cuts) == lab])
                     for lab in ("t1_low", "t2_mid", "t3_high")}
        by_exit = _group(drows, lambda r: r["exit_type"],
                         ("FORCE_FLAT", "REVERSAL", "TARGET_EXIT"))

        flip_d = [d for d in days_in_fold if d in flip_days]
        nonflip_d = [d for d in days_in_fold if d not in flip_days]
        by_flip = {
            "flip_days": {**_bucket([r for r in drows
                                     if r["n_mode_changes_that_day"] > 0]),
                          "n_days": len(flip_d)},
            "non_flip_days": {**_bucket([r for r in drows
                                         if r["n_mode_changes_that_day"] == 0]),
                              "n_days": len(nonflip_d)},
        }

        s_d = S.daily_series(trades_by_book["R-DAEMON"]["1.0"], lo, hi)
        s_s = S.daily_series(trades_by_book["SHORT_ALWAYS"]["1.0"], lo, hi)
        s_l = S.daily_series(trades_by_book["LONG_ALWAYS"]["1.0"], lo, hi)
        x, ys, yl = (s_d.to_numpy(float), s_s.to_numpy(float),
                     s_l.to_numpy(float))
        slope_s, rho_s = _ols_rho(x, ys)
        slope_l, rho_l = _ols_rho(x, yl)
        beta = {
            "avg_signed_in_session_exposure": exp_fold[f],
            "ols_slope_daemon_daily_vs_short_daily": round(slope_s, 6),
            "pearson_rho_daemon_daily_vs_short_daily": round(rho_s, 6),
            "ols_slope_daemon_daily_vs_long_daily": round(slope_l, 6),
            "pearson_rho_daemon_daily_vs_long_daily": round(rho_l, 6),
            "daemon_net_minus_short_net": round(float(x.sum() - ys.sum()), 2),
            "daemon_net_minus_long_net": round(float(x.sum() - yl.sum()), 2),
        }

        sil = [d for d in days_in_fold if d in flat_days]
        act = [d for d in days_in_fold if d in active_days]
        orig_rt_sil = sum(1 for t in trades_by_book["R-ORIG"]["1.0"]
                          if lo <= t["entry_ts"] <= hi
                          and int(t["entry_ts"] // SEC_DAY) in set(sil))
        orig_rt_act = sum(1 for t in trades_by_book["R-ORIG"]["1.0"]
                          if lo <= t["entry_ts"] <= hi
                          and int(t["entry_ts"] // SEC_DAY) in set(act))
        silenced = {
            "n_days_first_mode_flat": len(sil),
            "n_days_daemon_first_mode_active": len(act),
            "R-ORIG-SEMANTICS_net_on_silenced_days": round(
                sum(dnets["R-ORIG"].get(d, 0.0) for d in sil), 2),
            "R-ORIG-SEMANTICS_rt_on_silenced_days": orig_rt_sil,
            "R-ORIG-SEMANTICS_net_on_daemon_active_days": round(
                sum(dnets["R-ORIG"].get(d, 0.0) for d in act), 2),
            "R-ORIG-SEMANTICS_rt_on_daemon_active_days": orig_rt_act,
            "R-DAEMON_net_on_silenced_days": round(
                sum(dnets["R-DAEMON"].get(d, 0.0) for d in sil), 2),
        }

        per_fold[f] = {
            "by_direction": by_dir,
            "by_mode_at_entry_R-DAEMON": by_mode_entry,
            "by_day_first_mode_R-DAEMON": by_day_first_mode,
            "by_entry_hour_bucket_R-DAEMON": by_hour,
            "by_ex_ante_tercile_R-DAEMON": by_exante,
            "by_entry_spread_tercile_R-DAEMON": by_spread,
            "by_exit_type_R-DAEMON": by_exit,
            "mode_flip_R-DAEMON": by_flip,
            "beta_pull": beta,
            "early_silenced": silenced,
        }

    return {
        "schema": "failres_attrib_agg@1",
        "pair": pair,
        "labels": LABELS,
        "provenance_note": (
            "DIAGNOSTIC_OUTCOME_EXPOSED decomposition of the diag lane's "
            "5 books; cost decomposition = SAME book re-run at k=0.0 (not a "
            "variant); R-ORIG rows carry R-ORIG-SEMANTICS (leaky law, "
            "placement reference only); folds = falsifier FOLD_TABLE "
            "(imported); tercile cuts computed on the FULL panel, applied "
            "per fold (descriptive, one pass); no tuning, no variants."),
        "reconciliation": recon,
        "k_decay_R-DAEMON": {
            f: {k: round(float(sum(t["pips"] for t in
                                   trades_by_book["R-DAEMON"][k]
                                   if lo <= t["entry_ts"] <= hi)), 2)
                for k in ("1.0", "1.5", "2.0")}
            for f, (lo, hi) in fold_window.items()},
        "tercile_cuts_full_panel": {"ex_ante_vol_pct": ex_cuts,
                                    "entry_bar_spread_pips": sp_cuts},
        "per_fold": per_fold,
    }


def _daemon_target_for_exposure(p: T.SignalPlane, trades_by_book: dict):
    """Rebuild the daemon target for the exposure statistic from the SAME
    walk (cheap: rerun authoritative function)."""
    tgt, _, _ = T.f_rangeexp_daemon(p)
    return tgt


def _ols_rho(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    xm, ym = x - x.mean(), y - y.mean()
    denom = float((xm * xm).sum())
    slope = float((xm * ym).sum() / denom) if denom > 0 else 0.0
    sx = float(np.sqrt((xm * xm).sum()))
    sy = float(np.sqrt((ym * ym).sum()))
    rho = float((xm * ym).sum() / (sx * sy)) if sx > 0 and sy > 0 else 0.0
    return slope, rho


def daily_join_table(pair: str, trades_by_book: dict, ctx: dict,
                     exposure_by_day: dict) -> dict:
    """D: per traded day join surface for the (separate) events lane."""
    days = sorted(ctx)
    dnets = daily_nets_by_book(trades_by_book)
    key = {"R-DAEMON": "net_daemon", "R-ORIG": "net_orig",
           "R-ANCHOR": "net_anchor", "SHORT_ALWAYS": "net_short",
           "LONG_ALWAYS": "net_long"}
    rows = []
    for d in days:
        c = ctx[d]
        row = {"date": c["date"], "fold": c["fold"]}
        for arm, k in key.items():
            row[k] = round(dnets[arm].get(d, 0.0), 2)
        row.update({
            "daemon_signed_in_session_exposure":
                exposure_by_day.get(d, 0.0),
            "day_first_mode": c["daemon_first_mode"],
            "n_mode_changes": c["n_mode_changes"],
            "ex_ante_vol_pct": c["ex_ante_vol_pct"],
            "day_spread_p50_pips": c["day_spread_p50_pips"],
        })
        rows.append(row)
    return {"schema": "failres_daily@1", "pair": pair, "labels": LABELS,
            "note": "per traded day; nets k=1.0 keyed by entry day "
                    "(force-flat law: exit same day); R-ORIG column carries "
                    "R-ORIG-SEMANTICS; the events overlay is ANOTHER lane's "
                    "job — none performed here",
            "rows": rows}


def f2_deep_dive(trades_by_book: dict, all_rows: list, ctx: dict) -> dict:
    """C: EURUSD F2 (2021-11..2022-08) deep dive."""
    f2s, f2e = ts_of("2021-11-01"), ts_of("2022-08-31", end=True)
    months = ["2021-11", "2021-12", "2022-01", "2022-02", "2022-03",
              "2022-04", "2022-05", "2022-06", "2022-07", "2022-08"]
    monthly = {m: {arm: {"net_pips": 0.0, "rt": 0} for arm in BOOKS}
               for m in months}
    for arm in BOOKS:
        for t in trades_by_book[arm]["1.0"]:
            if not (f2s <= t["entry_ts"] <= f2e):
                continue
            m = dt.datetime.fromtimestamp(int(t["entry_ts"]),
                                          tz=dt.timezone.utc)\
                .strftime("%Y-%m")
            monthly[m][arm]["net_pips"] = round(
                monthly[m][arm]["net_pips"] + float(t["pips"]), 2)
            monthly[m][arm]["rt"] += 1

    date_to_day = {c["date"]: d for d, c in ctx.items()}
    drows = [r for r in all_rows if r["book"] == "R-DAEMON"
             and f2s <= r["entry_ts"] <= f2e]
    by_day = {}
    for r in drows:
        by_day.setdefault(r["day"], []).append(r)
    day_nets = {d: sum(r["net_pips"] for r in rs) for d, rs in by_day.items()}
    worst = sorted(day_nets, key=lambda d: day_nets[d])[:15]
    orig_day = {}
    for r in all_rows:
        if r["book"] == "R-ORIG":
            orig_day[r["day"]] = orig_day.get(r["day"], 0.0) + r["net_pips"]
    worst_detail = []
    for d in worst:
        rs = by_day[d]
        c = ctx[date_to_day[d]]
        hours = {}
        for r in rs:
            hours[str(r["entry_hour_utc"])] = \
                hours.get(str(r["entry_hour_utc"]), 0) + 1
        worst_detail.append({
            "date": d,
            "daemon_net_pips": round(day_nets[d], 2),
            "n_trades": len(rs),
            "long_net_pips": round(sum(r["net_pips"] for r in rs
                                       if r["dir"] > 0), 2),
            "short_net_pips": round(sum(r["net_pips"] for r in rs
                                        if r["dir"] < 0), 2),
            "n_long": sum(1 for r in rs if r["dir"] > 0),
            "n_short": sum(1 for r in rs if r["dir"] < 0),
            "n_mode_changes": c["n_mode_changes"],
            "day_first_mode": c["daemon_first_mode"],
            "ex_ante_vol_pct": c["ex_ante_vol_pct"],
            "entry_hours_histogram": dict(sorted(hours.items(),
                                                 key=lambda kv: int(kv[0]))),
            "R-ORIG-SEMANTICS_net_same_day": round(orig_day.get(d, 0.0), 2),
        })

    def cum_by_dir(rows):
        rows = sorted(rows, key=lambda r: r["entry_ts"])
        cl = cs = 0.0
        arr = []
        for r in rows:
            if r["dir"] > 0:
                cl += r["net_pips"]
            else:
                cs += r["net_pips"]
            arr.append({"entry_ts_utc": r["entry_ts_utc"],
                        "cum_long_net": round(cl, 2),
                        "cum_short_net": round(cs, 2)})
        return {"final_cum_long_net": round(cl, 2),
                "final_cum_short_net": round(cs, 2),
                "path": arr}

    daemon_f2_days = set(by_day)
    orig_f2 = [r for r in all_rows if r["book"] == "R-ORIG"
               and f2s <= r["entry_ts"] <= f2e]
    orig_restricted = [r for r in orig_f2 if r["day"] in daemon_f2_days]
    return {
        "window": ["2021-11-01", "2022-08-31"],
        "labels": LABELS + ["R-ORIG-SEMANTICS"],
        "monthly_nets_all_books": monthly,
        "worst_15_daemon_days": worst_detail,
        "cum_long_vs_short_R-DAEMON_F2": cum_by_dir(drows),
        "cum_long_vs_short_R-ORIG_on_daemon_F2_trading_days":
            {"R-ORIG-SEMANTICS": True, **cum_by_dir(orig_restricted)},
        "R-ORIG-SEMANTICS_F2_totals": {
            "net_all_f2_days": round(sum(r["net_pips"] for r in orig_f2), 2),
            "net_on_daemon_f2_trading_days": round(
                sum(r["net_pips"] for r in orig_restricted), 2),
        },
    }


def write_json(path: Path, obj):
    path.write_text(json.dumps(obj, indent=1, default=str) + "\n")
