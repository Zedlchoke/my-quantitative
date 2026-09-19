#!/usr/bin/env python3
"""STOCKS-SEARCH-V1 Z-lane runner (plans/PLAN_stocks_search_v1.md §9 phase Z).

Sanitized EXACT-ARM dry-run + RECURSIVE LEAK SCAN on a deterministic
synthetic dataset.  Consumed READ-ONLY: i/i_engine.py + i/adjudicate.py
(committed at HEAD 5c701987, branch orca/stocks-search-v1-integration),
s/selection_freeze.json (sha256
2d56c0dbcd21117272ae0d618d697020271b088896255b4ecf132452524e3fac) and the
sha256-pinned P0 census kernels p0/p0_lib.py that the engines reuse for
the firing states.  Writes ONLY under z/ (+ its handoff copies).

Modes
-----
--selfcheck    full dry-run (TASK 1) + recursive leak scan (TASK 2);
               writes z/dry_run_report.json and z/leak_scan.json;
               exit 0 iff EVERY check PASSes and the leak scan is CLEAN
               (fail-closed: any single failure -> nonzero exit).
--emit-digest  build the dataset, run the full 3-cell pipeline, print one
               JSON line {"dataset_sha256": ..., "pipeline_sha256": ...};
               used for CROSS-PROCESS determinism under different
               PYTHONHASHSEED values.

Synthetic dataset (deterministic, closed-form; NO RNG):
  calendar           984 business days from 2015-01-05
  folds              b1 = calendar[327], b2 = calendar[655] (thirds)
  names              42 (SYN00..SYN41), staggered listings (offset
                     (7k mod 168)), volume classes A(80e6)/B(15e6)/C(3e6)
  delisted           SYN30..SYN35 die at calendar 500/570/640/710/780/850
                     (death session = last served session); SYN31/32 carry
                     engineered last-session wedges so the BC-7 kinds
                     death_zero_length / died_before_entry are GUARANTEED
  late listings      SYN40 (offset 780), SYN41 (offset 700) -> warmup
                     attrition (SYN40 never reaches 252 served sessions)
  zero-range bars    SYN10..SYN15 carry high==low bars every 97th served
                     session from served index 100 (law: never fired on,
                     never imputed)
  wedges             GAP: a +5% overnight gap wedge per name (served 500;
                     delisted 30/31/32 at death-2/death-1/death) ->
                     GAP-P25-CONFIRM fires deterministically at the wedge;
                     52W-HIGH: a 40-session sawtooth (1.00 <-> 0.85) keeps
                     proximity inside/outside the 10% band on known bars
                     (close == 1.00 -> prox 0 -> FIRES; troughs -> no fire);
                     VOL-REGIME: SYN20..SYN29 get a quiet zone (calendar
                     600..750, +/-1bp alternating returns) whose sigma
                     collapses below the trailing tercile -> long-LOW
                     fires through the zone.

Hand-checkable trade (check C5): SYN02 (volume class C -> med252 band C),
GAP wedge at CALENDAR index 500 (served index 486; start offset 14):
decision t, entry t+1 open = close_t*0.999, exit t+2 open =
sawtooth(487)*0.998; net = gross - 2*25*2.0/1e4 = gross - 0.0100 ->
the 100 bps worst-case round trip is the operative deduction, verified
to 1e-12 against closed-form constants (never read from the arrays).

NO real data is read anywhere; the GO-gated real-data loader is exercised
with STUB paths only (the real P0 cache path is never provided); no
scored execution exists in this lane and every report says so.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent            # .../stocks_search_v1_run/z
_RUN_DIR = _HERE.parent                           # stocks_search_v1_run
_REPO_ROOT = _RUN_DIR.parents[1].parent           # worktree root
_I_DIR = _RUN_DIR / "i"
for _p in (str(_REPO_ROOT), str(_I_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import i_engine as E            # noqa: E402  (read-only I-lane engines)
import adjudicate as A          # noqa: E402  (read-only I-lane harness)

# ------------------------------------------------------------- constants
CYCLE_ID = "ZCODE-ORCHESTRATION-V3"
REAL_CYCLE = "STOCKS-SEARCH-V1"
TASK_ID = "ssearch-z"
BASE_SHA = "5c701987f997e29d35c9096f59827243e52f6d91"
BRANCH = "orca/stocks-search-v1-integration"
FREEZE_SHA = "2d56c0dbcd21117272ae0d618d697020271b088896255b4ecf132452524e3fac"

N_CAL = 984
CAL_START = date(2015, 1, 5)
B1_IDX = 327
B2_IDX = 655
N_NAMES = 42
CLASS_VOL = {0: 80_000_000.0, 1: 15_000_000.0, 2: 3_000_000.0}
CLASS_BAND = {0: "A", 1: "B", 2: "C"}
DEATHS = {30: 500, 31: 570, 32: 640, 33: 710, 34: 780, 35: 850}
DEATH_WEDGES = {30: DEATHS[30] - 2, 31: DEATHS[31] - 1, 32: DEATHS[32]}
VOL_WEDGE_NAMES = frozenset(range(20, 30))
QUIET_CAL_RANGE = range(600, 750)
ZERO_RANGE_NAMES = frozenset(range(10, 16))
LATE_START = {40: 780, 41: 700}
GAP_WEDGE_SERVED = 500
TAINT_CAP = {"SSS-GAP-P25-CONFIRM-H1": 60,
             "SSS-52W-HIGH-B10-H20": 60,
             "SSS-VOL-REGIME-L21-LOW-H20": 40}
DOCTOR2_SYM, DOCTOR2_IDX = "SYN00", 450
DISCLOSURE_PLAN_VERBATIM = (
    "accepted under owner-relaxed acceptance battery (R0 0.30 / DSR alpha "
    "0.10 at N = grid) | PBO NOT_RUN fail-closed (<=3 cells, d0992d17 "
    "class) | R0 NOT_RUN (D2 skipped by owner amendment §3b)")

GO_ABSENT = ""
GO_PARAPHRASES = (
    "go stocks search v1 scored execution",                  # case
    "GO STOCKS SEARCH V1 SCORED EXECUTIO",                  # truncated
    "GO STOCKS SEARCH V1 EXECUTION",                        # dropped word
    "PLEASE GO STOCKS SEARCH V1 SCORED EXECUTION",          # prefixed
    "GO STOCKS SEARCH V1 SCORED EXECUTION NOW",             # suffixed
    "GO STOCKS SEARCH V1 SCORED EXECUTION ",                # trailing space
    "GO  STOCKS SEARCH V1 SCORED EXECUTION",                # double space
)


# ----------------------------------------------------------- dataset build

def gfac(j: int) -> float:
    """Deterministic overnight gap factor cycle for opens."""
    return (0.998, 1.000, 1.002, 0.999)[j % 4]


def sawtooth(j: int) -> float:
    """40-session price sawtooth 1.00 -> 0.85 -> 1.00 (52W-HIGH wedge)."""
    a = j % 40
    if a < 20:
        return 1.0 - 0.15 * (a / 19.0)
    return 0.85 + 0.15 * ((a - 20) / 19.0)


def build_calendar() -> list:
    days, d = [], CAL_START
    while len(days) < N_CAL:
        if d.weekday() < 5:
            days.append(d.isoformat())
        d += timedelta(days=1)
    return days


def build_name(k: int, calendar: list):
    """Deterministic synthetic name k (closed form; no RNG anywhere)."""
    sym = f"SYN{k:02d}"
    cs = LATE_START.get(k, (k * 7) % 168)
    ce = DEATHS.get(k, N_CAL - 1)
    served = list(range(cs, ce + 1))
    n = len(served)
    quiet = set(QUIET_CAL_RANGE) if k in VOL_WEDGE_NAMES else set()

    close = np.empty(n, dtype=float)
    for i in range(n):
        if served[i] in quiet and i > 0:
            step = 0.0001 * (1.0 if i % 2 == 0 else -1.0)
            close[i] = close[i - 1] * (1.0 + step)
        else:
            close[i] = sawtooth(i)

    wedge = None
    if k in DEATH_WEDGES:
        w = DEATH_WEDGES[k] - cs
        wedge = w if 1 <= w < n else None
    elif k not in LATE_START:
        w = GAP_WEDGE_SERVED - cs
        wedge = w if 1 <= w < n else None
    if wedge is not None:
        close[wedge] = close[wedge - 1] * 1.05

    op = np.empty(n, dtype=float)
    op[0] = close[0]
    for i in range(1, n):
        op[i] = close[i - 1] * gfac(i)
    if wedge is not None:
        op[wedge] = close[wedge - 1] * 1.05

    n_zero_range = 0
    if k in ZERO_RANGE_NAMES:
        for i in range(100, n):
            if (i - 43) % 97 == 0:
                op[i] = close[i]          # degenerate bar: high == low
                n_zero_range += 1

    hi = np.maximum(op, close) * 1.001
    lo = np.minimum(op, close) * 0.999
    if k in ZERO_RANGE_NAMES:
        for i in range(100, n):
            if (i - 43) % 97 == 0:
                hi[i] = close[i]
                lo[i] = close[i]

    vol = np.full(n, CLASS_VOL[k % 3], dtype=float)
    nm = E.NameData(sym, tuple(calendar[i] for i in served), op, hi, lo,
                    close, vol)
    meta = {"symbol": sym, "cal_start": cs, "cal_end": ce,
            "n_served": n, "delisted": k in DEATHS,
            "gap_wedge_served": wedge, "zero_range_bars": n_zero_range,
            "vol_class": CLASS_BAND[k % 3],
            "vol_regime_quiet_zone": k in VOL_WEDGE_NAMES}
    return nm, meta


def build_spy(calendar: list) -> E.NameData:
    n = len(calendar)
    close = np.empty(n, dtype=float)
    close[0] = 1.0
    for i in range(1, n):
        close[i] = close[i - 1] * 1.0002
    op = np.empty(n, dtype=float)
    op[0] = close[0]
    for i in range(1, n):
        op[i] = close[i - 1]
    hi = np.maximum(op, close) * 1.001
    lo = np.minimum(op, close) * 0.999
    return E.NameData("SPY", tuple(calendar), op, hi, lo, close,
                      np.full(n, 1e9, dtype=float))


def build_dataset():
    calendar = build_calendar()
    names, metas = {}, []
    for k in range(N_NAMES):
        nm, meta = build_name(k, calendar)
        names[nm.symbol] = nm
        metas.append(meta)
    spy = build_spy(calendar)
    b1, b2 = calendar[B1_IDX], calendar[B2_IDX]
    meta = {
        "seed_label": "closed-form-deterministic (no RNG; z_run.py v1)",
        "n_calendar_sessions": len(calendar),
        "calendar_start": calendar[0], "calendar_end": calendar[-1],
        "folds": {"b1": b1, "b2": b2,
                  "F1": [calendar[0], b1], "F2": [b1, b2],
                  "F3": [b2, calendar[-1]]},
        "n_names": len(names),
        "n_served_bars_total": sum(m["n_served"] for m in metas),
        "n_delisted": sum(1 for m in metas if m["delisted"]),
        "delisted_symbols": sorted(m["symbol"] for m in metas
                                   if m["delisted"]),
        "staggered_listing_offsets": sorted({m["cal_start"] for m in metas}),
        "late_listings": {"SYN40": LATE_START[40], "SYN41": LATE_START[41]},
        "zero_range_bars_total": sum(m["zero_range_bars"] for m in metas),
        "zero_range_symbols": sorted(m["symbol"] for m in metas
                                     if m["zero_range_bars"]),
        "gap_wedges": {m["symbol"]: m["gap_wedge_served"] for m in metas
                       if m["gap_wedge_served"] is not None},
        "vol_regime_quiet_zone_names": sorted(
            m["symbol"] for m in metas if m["vol_regime_quiet_zone"]),
        "volume_classes": CLASS_BAND,
        "spy": "deterministic 2bp/day drift, volume 1e9, full calendar",
    }
    return {"names": names, "spy": spy, "calendar": calendar,
            "b1": b1, "b2": b2, "meta": meta}


# --------------------------------------------------------------- pipeline

BOOK_KEYS = ("candidate", "c_complement", "r5_component", "c_delay_h",
             "c_random_timing", "c_cal_hist", "c_reversal_plain")


def run_pipeline(names, spy, calendar, b1, b2):
    """Full end-to-end: build_all_books + adjudicate for the 3 frozen cells."""
    reports, bundles, series = {}, {}, {}
    for cid in E.CELL_IDS:
        cell = E.CELL_BY_ID[cid]
        bundle = E.build_all_books(names, cell, calendar, b1, b2,
                                   stress=E.STRESS_TIER)
        reports[cid] = A.adjudicate_candidate(bundle, spy, calendar, b1, b2)
        bundles[cid] = bundle
        series[cid] = {k: bundle[k].series_sha256() for k in BOOK_KEYS}
    return reports, bundles, series


def canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def pipeline_digest(names, spy, calendar, b1, b2, meta):
    reports, bundles, series = run_pipeline(names, spy, calendar, b1, b2)
    payload = {"meta": meta, "reports": reports, "series": series}
    return sha256_text(canon(payload)), reports, bundles, series


# ----------------------------------------------------------------- checks

def check(cid, title, method, ok, evidence):
    if not isinstance(title, str):
        title = title[0]
    return {"id": cid, "title": title, "method": method,
            "result": "PASS" if ok else "FAIL", "evidence": evidence}


HAND_TRADE_SYM = "SYN02"          # volume class C -> band C -> 100 bps case
HAND_TRADE_START = (2 * 7) % 168  # 14
HAND_TRADE_T = GAP_WEDGE_SERVED - HAND_TRADE_START   # served index 486


def hand_expected_gap_trade():
    """Closed-form constants for the SYN02 GAP wedge trade (no array reads).

    SYN02 starts at calendar offset 14, so the wedge at CALENDAR 500 is at
    served index t = 486; dvol = close x 3e6 in [2.55e6, 3.15e6] -> med252
    band C (>= $2M, < $10M).  Constants:
    close[t-1] = sawtooth(485) = 1.0 - 0.15*(5/19)
    close[t]   = close[t-1] * 1.05   (wedge);  open[t] = close[t]
    open[t+1]  = close[t] * gfac(487) = close[t] * 0.999
    close[t+1] = sawtooth(487) = 1.0 - 0.15*(7/19)
    open[t+2]  = close[t+1] * gfac(488) = close[t+1] * 0.998
    gross = open[t+2]/open[t+1] - 1 ; band C ; net = gross - 0.0100
    (the 25bps x 2 fills x stress 2.0 WORST-CASE round trip)
    """
    c_prev = 1.0 - 0.15 * (5.0 / 19.0)
    c_t = c_prev * 1.05
    o_t1 = c_t * 0.999
    c_t1 = 1.0 - 0.15 * (7.0 / 19.0)
    o_t2 = c_t1 * 0.998
    gross = o_t2 / o_t1 - 1.0
    return {"symbol": HAND_TRADE_SYM, "wedge_calendar_index":
            GAP_WEDGE_SERVED, "decision_served": HAND_TRADE_T,
            "entry_served": HAND_TRADE_T + 1, "exit_served": HAND_TRADE_T + 2,
            "open_entry": o_t1, "open_exit": o_t2, "gross": gross,
            "band": "C", "cost_round_trip": 2 * 25 * 2.0 / 1e4,
            "net": gross - 2 * 25 * 2.0 / 1e4}


def find_leg(book, sym, decision_date):
    for lg in book.legs:
        if lg.symbol == sym and lg.decision_date == decision_date:
            return lg
    return None


def fold_end_index(nm, fends, fold):
    target = fends[fold]
    last = None
    for i, d in enumerate(nm.dates):
        if d <= target:
            last = i
        else:
            break
    return last


def global_leg_scan(bundles, names, calendar, b1, b2):
    """Structural scan of every leg in every book of every cell.

    Per-leg re-derivation: fold by DECISION date; entry index ==
    decision + 1 (+H for C-DELAY-H); exit index == entry + book H unless
    force-flat (exit = the name's last served session <= fold end, with
    the natural exit proven to cross); net == gross - 2*band*stress/1e4
    to 1e-12; band equals the name's engineered volume class.
    """
    L = E.load_p0_lib()
    cal = tuple(calendar)
    fends = E.fold_ends(cal, b1, b2)
    n_legs = n_ff = 0
    problems = []
    cost_max = 0.0
    band_mismatch = []
    for cid, bundle in bundles.items():
        for key in BOOK_KEYS:
            book = bundle[key]
            hk = int(book.H)
            entry_off = 1 + (hk if key == "c_delay_h" else 0)
            for lg in book.legs:
                n_legs += 1
                nm = names.get(lg.symbol)
                if nm is None:
                    problems.append([cid, key, lg.symbol, "not-in-cohort"])
                    continue
                di = E.nm_dates_index(nm, lg.decision_date)
                ei = E.nm_dates_index(nm, lg.entry_date)
                xi = E.nm_dates_index(nm, lg.exit_date)
                fold = L.assign_fold(lg.decision_date, b1, b2)
                if lg.fold != fold:
                    problems.append([cid, key, lg.symbol, "fold-mismatch"])
                if ei != di + entry_off:
                    problems.append([cid, key, lg.symbol, "entry-clock",
                                     di, ei])
                if lg.force_flat:
                    n_ff += 1
                    ff = fold_end_index(nm, fends, fold)
                    if xi != ff or di + entry_off + hk <= ff:
                        problems.append([cid, key, lg.symbol, "ff-anchor"])
                else:
                    if xi != di + entry_off + hk:
                        problems.append([cid, key, lg.symbol, "exit-clock",
                                         di, xi])
                    if lg.exit_date > fends[fold]:
                        problems.append([cid, key, lg.symbol, "past-fold-end"])
                expect_net = (lg.gross - 2.0 * (L.BAND_BPS[lg.band]
                                                * book.stress) / 1e4)
                if abs(lg.net - expect_net) > 1e-12:
                    problems.append([cid, key, lg.symbol, "net-formula"])
                cost_max = max(cost_max,
                               2.0 * L.BAND_BPS[lg.band] * book.stress / 1e4)
                if lg.symbol.startswith("SYN"):
                    want = CLASS_BAND[int(lg.symbol[3:]) % 3]
                    if lg.band != want:
                        band_mismatch.append([cid, key, lg.symbol, lg.band,
                                              want])
    return {"n_legs": n_legs, "n_force_flat": n_ff, "problems": problems,
            "max_round_trip_cost": cost_max, "band_mismatch": band_mismatch}


def run_all_checks(ds, reports, bundles, series, digest_inproc):
    """TASK 1 checks C0..C9.  Returns (checks, all_ok)."""
    names, spy, calendar, b1, b2 = (ds["names"], ds["spy"], ds["calendar"],
                                    ds["b1"], ds["b2"])
    cal = tuple(calendar)
    cal_index = {d: i for i, d in enumerate(cal)}
    fends = E.fold_ends(cal, b1, b2)
    checks = []
    ok_all = True

    # ---- C0 freeze verification (stop-condition guard)
    try:
        fv = E.verify_freeze()
        E.load_p0_lib()
        c0_ok = (fv["freeze_sha256"] == FREEZE_SHA
                 and fv["status"] == "SELECTION_FROZEN"
                 and fv["n_cells"] == 3)
        ev = {"freeze_sha256": fv["freeze_sha256"], "status": fv["status"],
              "n_cells": fv["n_cells"], "p0_lib_pinned_import": "OK"}
    except E.FrozenShaMismatch as exc:
        c0_ok, ev = False, {"FROZEN_SHA_MISMATCH": str(exc)}
    checks.append(check("C0", "Binding freeze verification",
                        "verify_freeze() + load_p0_lib() pin at import; "
                        "mismatch is the FROZEN_SHA_MISMATCH stop condition",
                        c0_ok, ev))
    ok_all &= c0_ok

    # ---- C1 in-process determinism (byte-identical rerun)
    digest2, reports2, _b2, series2 = pipeline_digest(
        names, spy, calendar, b1, b2, ds["meta"])
    c1_ok = digest2 == digest_inproc
    checks.append(check("C1", "In-process determinism (byte-identical rerun)",
                        "full pipeline run twice in one process; canonical "
                        "JSON sha256 over all 3 cell adjudication reports + "
                        "21 book series digests must be identical",
                        c1_ok, {"digest_run1": digest_inproc,
                                "digest_run2": digest2}))
    ok_all &= c1_ok

    # ---- C3 fold force-flat (engineered case + global structural scan)
    scan = global_leg_scan(bundles, names, calendar, b1, b2)
    nm0 = names["SYN00"]
    legs_ff, _c, _cnt = E.build_legs(nm0, [320], 20, cal_index, fends,
                                     E.STRESS_TIER)
    ff_leg = legs_ff[0] if legs_ff else None
    exp_gross_ff = None
    if ff_leg is not None:
        e_i = E.nm_dates_index(nm0, ff_leg.entry_date)
        x_i = E.nm_dates_index(nm0, ff_leg.exit_date)
        exp_gross_ff = (float(nm0.adj_open[x_i]) / float(nm0.adj_open[e_i])
                        - 1.0)
    book_leg_320 = find_leg(bundles["SSS-52W-HIGH-B10-H20"]["candidate"],
                            "SYN00", cal[320])
    c3_ok = (not scan["problems"] and ff_leg is not None
             and ff_leg.force_flat is True
             and ff_leg.exit_date == cal[B1_IDX]
             and abs(ff_leg.gross - exp_gross_ff) < 1e-12
             and scan["n_force_flat"] > 0
             and book_leg_320 is not None and book_leg_320.force_flat is True
             and book_leg_320.exit_date == cal[B1_IDX])
    # fold_not_opened exhibited: SYN00 decision AT b1 under 52W (H=20)
    legs_fno, _c2, cnt_fno = E.build_legs(nm0, [B1_IDX], 20, cal_index,
                                          fends, E.STRESS_TIER)
    c3_ok &= (len(legs_fno) == 0 and cnt_fno["fold_not_opened"] == 1)
    checks.append(check("C3", "Fold force-flat + fold boundary clock",
                        "every leg in every book re-derived structurally "
                        "(fold by decision date; entry = decision+offset; "
                        "force-flat exit = the name's last served session "
                        "<= fold end with the natural exit proven to cross; "
                        "natural exit otherwise); engineered SYN00 52W "
                        "decision at calendar[320] must force-flat at "
                        "calendar[327]=B1 (hand leg AND end-to-end book "
                        "leg); a decision AT B1 must be fold_not_opened",
                        c3_ok, {
                            "engineered_leg": {
                                "symbol": "SYN00", "decision": cal[320],
                                "exit": ff_leg.exit_date if ff_leg else None,
                                "force_flat": bool(ff_leg.force_flat)
                                if ff_leg else None,
                                "gross_matches_recompute":
                                    bool(ff_leg
                                         and abs(ff_leg.gross - exp_gross_ff)
                                         < 1e-12)},
                            "book_leg_same_exit_and_anchor":
                                bool(book_leg_320 is not None
                                     and book_leg_320.exit_date == cal[B1_IDX]
                                     and book_leg_320.force_flat is True),
                            "fold_not_opened_syn00_at_b1":
                                cnt_fno["fold_not_opened"],
                            "structural_scan": {
                                "legs_scanned": scan["n_legs"],
                                "force_flat_legs": scan["n_force_flat"],
                                "problems": scan["problems"][:20],
                                "n_problems": len(scan["problems"])}}))
    ok_all &= c3_ok

    # ---- C4 BC-7 death handling
    gap_b = bundles["SSS-GAP-P25-CONFIRM-H1"]["candidate"]
    w52_b = bundles["SSS-52W-HIGH-B10-H20"]["candidate"]
    vol_b = bundles["SSS-VOL-REGIME-L21-LOW-H20"]["candidate"]
    kinds_gap = sorted({lg.censored_kind for lg in gap_b.censored_legs
                        if lg.censored_kind})
    kinds_all = sorted({lg.censored_kind for b in (gap_b, w52_b, vol_b)
                        for lg in b.censored_legs if lg.censored_kind})
    # SYN30: wedge at calendar DEATHS[30]-2 -> natural exit AT the death
    # session (the death session serves the exit; NOT censored)
    syn30_start = (30 * 7) % 168
    legs30, cens30, _ = E.build_legs(names["SYN30"],
                                     [DEATHS[30] - 2 - syn30_start], 1,
                                     cal_index, fends, E.STRESS_TIER)
    death_serves = bool(legs30 and legs30[0].exit_date == cal[DEATHS[30]]
                        and not legs30[0].censored
                        and not cens30)
    # censored legs carry no net; expectancy excludes them
    censored_have_no_net = all(lg.net != lg.net
                               for b in (gap_b, w52_b, vol_b)
                               for lg in b.censored_legs)
    mean_ok = True
    for b in (gap_b, w52_b, vol_b):
        nets = [lg.net for lg in b.legs]
        if nets:
            mean_ok &= (float(np.mean(nets)) == b.expectancy)
    # death_open gross recompute on every death_open leg
    death_open_ok = True
    n_death_open = 0
    for b in (gap_b, w52_b, vol_b):
        for lg in b.censored_legs:
            if lg.censored_kind != "death_open":
                continue
            n_death_open += 1
            nm = names[lg.symbol]
            e_i = E.nm_dates_index(nm, lg.entry_date)
            x_i = E.nm_dates_index(nm, lg.exit_date)
            g = float(nm.adj_open[x_i]) / float(nm.adj_open[e_i]) - 1.0
            if abs(g - lg.gross) > 1e-12:
                death_open_ok = False
    inv_bound = all(
        reports[cid]["death_invariance"]["verdict_matches"] is not False
        for cid in E.CELL_IDS)
    # death_open split: engine-frozen BC-7 censors at the name's LAST
    # SERVED session - both true deaths (delisted names) and the dataset's
    # right-edge censoring exhibit the same machinery (the scored E run
    # has the identical window-edge semantics at the S0 end)
    death_open_split = {}
    for b, tag in ((gap_b, "GAP"), (w52_b, "52W"), (vol_b, "VOL")):
        split = {"at_window_edge": 0, "delisted_name": 0}
        for lg in b.censored_legs:
            if lg.censored_kind != "death_open":
                continue
            nmk = names[lg.symbol]
            key = ("at_window_edge"
                   if nmk.dates[-1] == calendar[-1] else "delisted_name")
            split[key] += 1
        death_open_split[tag] = split
    c4_ok = (set(kinds_all) >= {"death_zero_length", "died_before_entry"}
             and n_death_open > 0 and death_serves and censored_have_no_net
             and bool(mean_ok) and death_open_ok and inv_bound)
    checks.append(check("C4", "BC-7 death contract",
                        "engineered last-session wedges force "
                        "death_zero_length (SYN31) and died_before_entry "
                        "(SYN32); the delisted cohort yields death_open "
                        "legs in the H=20 arms; SYN30 demonstrates the "
                        "death session serving a natural exit; censored "
                        "legs carry no net and are excluded from the "
                        "expectancy numerator (verified by recompute); "
                        "death_open gross recomputed = "
                        "death-open/entry-open to 1e-12; adjudicate's "
                        "death-censoring invariance bound in all 3 reports; "
                        "the engine-frozen BC-7 horizon is the name's LAST "
                        "SERVED session, so the split also reports "
                        "window-edge censoring (identical semantics apply "
                        "at the S0 end in the scored E run)",
                        c4_ok, {
                            "censored_kinds_gap": kinds_gap,
                            "censored_kinds_all_arms": kinds_all,
                            "n_death_open": n_death_open,
                            "death_open_split_per_arm": death_open_split,
                            "death_open_gross_recompute_ok": death_open_ok,
                            "syn30_death_session_serves_natural_exit":
                                death_serves,
                            "censored_legs_net_is_nan": censored_have_no_net,
                            "expectancy_excludes_censored": bool(mean_ok),
                            "death_invariance_bound_in_reports": inv_bound}))
    ok_all &= c4_ok

    # ---- C5 cost bands + hand-checkable trade + 100 bps worst case
    exp = hand_expected_gap_trade()
    nmht = names[HAND_TRADE_SYM]
    legs500, _c5, _k5 = E.build_legs(nmht, [HAND_TRADE_T], 1, cal_index,
                                     fends, E.STRESS_TIER)
    lg500 = legs500[0] if legs500 else None
    trade_ok = bool(lg500 is not None
                    and lg500.decision_date == cal[GAP_WEDGE_SERVED]
                    and lg500.entry_date == cal[GAP_WEDGE_SERVED + 1]
                    and lg500.exit_date == cal[GAP_WEDGE_SERVED + 2]
                    and lg500.band == exp["band"]
                    and abs(lg500.gross - exp["gross"]) < 1e-12
                    and abs(lg500.net - exp["net"]) < 1e-12)
    in_book = find_leg(gap_b, HAND_TRADE_SYM, cal[GAP_WEDGE_SERVED])
    e2e_ok = bool(in_book is not None
                  and abs(in_book.net - exp["net"]) < 1e-12
                  and in_book.band == "C")
    bands_ok = (not scan["band_mismatch"]
                and scan["max_round_trip_cost"] <= 0.0100 + 1e-15)
    per_book_bands = {}
    for b, bb in (("GAP", gap_b), ("52W", w52_b), ("VOL", vol_b)):
        per_book_bands[b] = sorted({lg.band for lg in bb.legs})
    c5_ok = trade_ok and e2e_ok and bands_ok
    checks.append(check("C5", "Cost bands + 100 bps worst case (hand-checked)",
                        "hand-checkable trade derived from closed-form "
                        "constants (NEVER read from the arrays): SYN02 "
                        "(volume class C) GAP wedge decision calendar[500] "
                        "(served 486), entry 501 open, exit 502 open, band "
                        "C, net = gross - 0.0100 = the 25bps x 2 fills x "
                        "stress 2.0 WORST-CASE ceiling; the same leg must "
                        "appear in the end-to-end candidate book; every leg "
                        "in every book carries its engineered volume-class "
                        "band (A/B/C) and satisfies net = gross - "
                        "2*band*2.0/1e4 to 1e-12; observed round-trip cost "
                        "<= the 100 bps ceiling",
                        c5_ok, {
                            "expected_constants": exp,
                            "engineered_leg": {
                                "decision": cal[500], "entry": cal[501],
                                "exit": cal[502],
                                "band": lg500.band if lg500 else None,
                                "gross": lg500.gross if lg500 else None,
                                "net": lg500.net if lg500 else None,
                                "matches_hand_constants": trade_ok},
                            "end_to_end_book_leg_matches": e2e_ok,
                            "bands_per_book": per_book_bands,
                            "band_class_mismatches":
                                scan["band_mismatch"][:20],
                            "max_round_trip_cost_observed":
                                scan["max_round_trip_cost"],
                            "worst_case_ceiling_bps": 100}))
    ok_all &= c5_ok

    # ---- C6 verdict labels + disclosure verbatim
    labels_ok = True
    label_ev = {}
    for cid in E.CELL_IDS:
        r = reports[cid]
        okr = (r["r0_status"] == "R0_NOT_RUN"
               and r["r0_verbatim"] == E.R0_NOT_RUN_VERBATIM
               and r["r0_verbatim"] == "R0 NOT_RUN (D2 skipped by owner "
                                       "amendment §3b)"
               and r["pbo_status"] == "PBO_NOT_RUN"
               and r["pbo_verbatim"] == E.PBO_NOT_RUN_VERBATIM
               and r["pbo_verbatim"] == "PBO NOT_RUN fail-closed (<=3 "
                                        "cells, d0992d17 class)"
               and r["disclosure_section10"] ==
               E.DISCLOSURE_SECTION10_VERBATIM
               and r["disclosure_section10"] == DISCLOSURE_PLAN_VERBATIM
               and r["budget"]["used"] == 0 and r["budget"]["max"] == 3
               and r["dsr"]["gate"] == "E_SCORED_ONLY")
        labels_ok &= okr
        label_ev[cid] = {"synthetic_verdict": r["verdict"],
                         "r0_status": r["r0_status"],
                         "pbo_status": r["pbo_status"],
                         "budget_used": r["budget"]["used"],
                         "dsr_gate": r["dsr"]["gate"],
                         "labels_verbatim_ok": bool(okr)}
    checks.append(check("C6", "Verdict labels + §10 relaxation disclosure",
                        "every cell's adjudication report carries "
                        "R0_NOT_RUN + PBO_NOT_RUN + the §3/§10 relaxation "
                        "disclosure string VERBATIM (checked against both "
                        "the engine constants AND the plan §10 text), "
                        "budget 0/3 and the E-scored-only DSR gate",
                        labels_ok, label_ev))
    ok_all &= bool(labels_ok)

    # ---- C7 GO gate (stub paths only; the real cache is never provided)
    go_ev = {"refused": [], "exact_phrase_stub_path": None}
    go_ok = True
    manifest = str(_HERE / "stub_retrieval_manifest_DOES_NOT_EXIST.json")
    with tempfile.TemporaryDirectory() as td:
        stub_cache = str(Path(td) / "stub_cache_empty")
        for bad in (GO_ABSENT,) + GO_PARAPHRASES:
            try:
                A.load_real_data(bad, stub_cache, manifest)
                go_ev["refused"].append({"phrase": repr(bad),
                                         "refused": False})
                go_ok = False
            except A.GoGateRefused:
                go_ev["refused"].append({"phrase": repr(bad),
                                         "refused": True})
            except Exception as exc:                       # noqa: BLE001
                go_ev["refused"].append({"phrase": repr(bad),
                                         "refused": False,
                                         "wrong_error": type(exc).__name__})
                go_ok = False
        try:
            A.load_real_data(E.GO_PHRASE, stub_cache, manifest)
            go_ok = False
            go_ev["exact_phrase_stub_path"] = "UNEXPECTEDLY LOADED"
        except A.GoGateRefused:
            go_ok = False
            go_ev["exact_phrase_stub_path"] = (
                "GoGateRefused (WRONG: the exact phrase must pass the gate)")
        except FileNotFoundError as exc:
            go_ev["exact_phrase_stub_path"] = {
                "gate": "PASSED (exact phrase consumed)",
                "data_path": "FileNotFoundError on the STUB cache dir",
                "detail": str(exc)[:160]}
        except Exception as exc:                           # noqa: BLE001
            go_ok = False
            go_ev["exact_phrase_stub_path"] = {
                "unexpected": type(exc).__name__, "detail": str(exc)[:160]}
    c7_ok = (go_ok
             and all(r["refused"] for r in go_ev["refused"])
             and isinstance(go_ev["exact_phrase_stub_path"], dict)
             and go_ev["exact_phrase_stub_path"].get("gate")
             == "PASSED (exact phrase consumed)")
    checks.append(check("C7", "GO-gated real-data loader (stub paths only)",
                        "the absent phrase + 7 paraphrased/truncated/"
                        "padded variants must raise GoGateRefused (P-8: "
                        "early or paraphrased GO dies unconsumed); the "
                        "EXACT phrase passes the gate and then fails on a "
                        "STUB cache dir (FileNotFoundError) - the real P0 "
                        "cache path is never provided and no real data is "
                        "ever loaded in this lane",
                        c7_ok, go_ev))
    ok_all &= c7_ok

    # ---- C8 zero-range law
    L = E.load_p0_lib()
    n = 70
    o = np.full(n, 1.0)
    h = np.full(n, 1.02)
    lo = np.full(n, 0.98)
    c = np.full(n, 1.0)
    c[60:64] = 0.90
    h[60:64] = 0.92
    lo[60:64] = 0.90
    # candidate bar t=65: BREAK (0.80 < prior-3 low 0.90) + RECLAIM
    # (close 1.60 > 0.90) + range 0.9756 >= 0.5 + participation
    # (dvol 1.6e8 >= 1.5 x med60 ~1e8)
    c[65] = 1.60
    lo[65] = 0.80
    h_deg = h.copy()
    h_deg[65] = 1.60          # DEGENERATE twin: high == low == close
    lo_deg = lo.copy()
    lo_deg[65] = 1.60
    h_ctl = h.copy()
    h_ctl[65] = 1.62          # non-degenerate twin
    v = np.full(n, 1e8)
    fired_zr, _bk, drops_zr = L.census_event_unwind(o, h_deg, lo_deg, c, v,
                                                    3, first_i=10)
    fired_ctl, _bk2, drops_ctl = L.census_event_unwind(o, h_ctl, lo, c, v,
                                                       3, first_i=10)
    zr_count = ds["meta"]["zero_range_bars_total"]
    arms_clean = all(lg.gross == lg.gross
                     for cid in E.CELL_IDS
                     for lg in bundles[cid]["candidate"].legs)
    c8_ok = (not bool(fired_zr[65])) and bool(fired_ctl[65]) and zr_count > 0 \
        and arms_clean
    checks.append(check(
        "C8", "Zero-range law (high==low never fired, never imputed)",
        "p0 census kernel on a crafted mini-series: an otherwise-qualifying "
        "EVENT-UNWIND bar (break+reclaim+range+participation all true) made "
        "degenerate (high==low) is NOT fired and counted, while its "
        "non-degenerate twin FIRES (control proving the test can detect); "
        "the cohort carries zero-range bars and all 3 arms ran clean with "
        "them present",
        c8_ok, {"degenerate_bar_fired": bool(fired_zr[65]),
                "degenerate_counted_in_drops":
                    drops_zr.get("range_undefined", 0),
                "twin_bar_fired": bool(fired_ctl[65]),
                "zero_range_bars_in_cohort": zr_count,
                "arms_ran_clean": arms_clean}))
    ok_all &= c8_ok

    # ---- C9 wedge liveness + synthetic verdicts recorded
    vol_cell = E.CELL_BY_ID["SSS-VOL-REGIME-L21-LOW-H20"]
    zone_fired = zone_total = early_fired = early_total = 0
    for symk in sorted(ds["meta"]["vol_regime_quiet_zone_names"]):
        nmk = names[symk]
        f_mask, _bm = E.state_fired_mask(nmk, "VOL-REGIME",
                                         vol_cell["params"])
        lo_i = E.nm_dates_index(nmk, calendar[601])
        hi_i = E.nm_dates_index(nmk, calendar[729])
        e_i = E.nm_dates_index(nmk, calendar[660])
        if lo_i is None or hi_i is None or e_i is None:
            continue
        zone_fired += int(f_mask[lo_i:hi_i + 1].sum())
        zone_total += hi_i + 1 - lo_i
        early_fired += int(f_mask[lo_i:e_i + 1].sum())
        early_total += e_i + 1 - lo_i
    zone_share = zone_fired / zone_total if zone_total else 0.0
    early_share = early_fired / early_total if early_total else 0.0
    gap_mask_syn00 = E.state_fired_mask(
        nm0, "GAP",
        E.CELL_BY_ID["SSS-GAP-P25-CONFIRM-H1"]["params"])[0]
    gap_wedge_fired = bool(gap_mask_syn00[GAP_WEDGE_SERVED])
    w52_mask_syn00 = E.state_fired_mask(
        nm0, "52W-HIGH", E.CELL_BY_ID["SSS-52W-HIGH-B10-H20"]["params"])[0]
    peaks = [i for i in range(300, 700) if i % 40 == 0]
    w52_peak_share = sum(1 for i in peaks if w52_mask_syn00[i]) / len(peaks)
    c9_ok = (gap_wedge_fired and zone_share >= 0.30 and early_share >= 0.90
             and w52_peak_share >= 0.99
             and all(reports[cid]["primary"] is not None
                     for cid in E.CELL_IDS))
    checks.append(check(
        "C9", "Wedge liveness + full-pipeline verdicts (SYNTHETIC)",
        "the engineered wedges fire on cue: the GAP wedge bar fires "
        "CONFIRM; the VOL-REGIME quiet zone fires long-LOW (early zone "
        ">= 90%, whole zone >= 30%); every sawtooth peak fires 52W-HIGH "
        "(>= 99%); the full pipeline produced a verdict for all 3 cells "
        "(SYNTHETIC verdicts - NO scored meaning, explicitly not "
        "evidence of anything)",
        c9_ok, {
            "gap_wedge_bar_fired": gap_wedge_fired,
            "vol_quiet_zone_fired_share": round(zone_share, 4),
            "vol_quiet_zone_early_share": round(early_share, 4),
            "w52_sawtooth_peak_fired_share": round(w52_peak_share, 4),
            "synthetic_verdicts": {cid: reports[cid]["verdict"]
                                   for cid in E.CELL_IDS}}))
    ok_all &= c9_ok

    return checks, bool(ok_all)


# ------------------------------------------------------------- leak scan

def _line_of(path: Path, snippet: str):
    """1-based line number of the first occurrence of snippet (live)."""
    for i, line in enumerate(path.read_text().splitlines(), 1):
        if snippet in line:
            return i
    return None


def static_scan():
    """TASK 2 static half: forbidden-pattern greps + curated PIT evidence."""
    files = {
        "p0/p0_lib.py": _RUN_DIR / "p0" / "p0_lib.py",
        "i/i_engine.py": _I_DIR / "i_engine.py",
        "i/adjudicate.py": _I_DIR / "adjudicate.py",
    }
    forbidden = ["ffill", "bfill", "fillna", "interpolate(", "pandas",
                 ".shift(", "expanding(", "merge_asof", "reindex(",
                 "np.nanmax", "np.nanmin", "np.nansum",
                 "method='ffill'", "method='bfill'"]
    grep_hits = []
    for label, path in files.items():
        text = path.read_text().splitlines()
        for pat in forbidden:
            for i, line in enumerate(text, 1):
                if pat in line:
                    grep_hits.append({"file": label, "line": i,
                                      "pattern": pat,
                                      "snippet": line.strip()[:120]})
    watch = ["np.percentile", "np.median", "np.std", ".max(", ".min(",
             "sliding_window_view", "cumsum", "cummax"]
    watch_hits = []
    for label, path in files.items():
        text = path.read_text().splitlines()
        for pat in watch:
            for i, line in enumerate(text, 1):
                if pat in line:
                    watch_hits.append({"file": label, "line": i,
                                       "pattern": pat,
                                       "snippet": line.strip()[:120]})
    P0 = files["p0/p0_lib.py"]
    IE = files["i/i_engine.py"]
    AD = files["i/adjudicate.py"]
    curated_rows = [
        (P0, "_rolling_median", "p0/p0_lib.py",
         "trailing sliding window via sliding_window_view; out[i] covers "
         "[i-window+1, i] (ends AT i); NaN before the window exists; NO "
         "forward read.  NOTE: the module docstring says 'ending at i-1' - "
         "the DOCSTRING IS WRONG vs the code (the code is trailing-"
         "INCLUSIVE); both readings are backward-safe (PIT-clean).  "
         "Recorded as DOC_INCONSISTENCY, not a leak: the kernel (code) is "
         "the frozen authority shared byte-identically by the census and "
         "the engines, so arm identity is unaffected.",
         "OK_BACKWARD_WINDOW + DOC_INCONSISTENCY_BENIGN"),
        (P0, "_rolling_max", "p0/p0_lib.py",
         "sw.max(axis=1) over sliding_window_view: out[i] = "
         "max(a[i-251:i+1]) trailing-inclusive; drives the 52W-HIGH state "
         "high_t; NO forward read.",
         "OK_BACKWARD_WINDOW"),
        (P0, "gaps[i - 251:i + 1]", "p0/p0_lib.py",
         "GAP percentile history = trailing 252 gaps ENDING AT AND "
         "INCLUDING t; gap_t itself = open_t/close_{t-1}-1 (backward "
         "diff); the decision bar's own gap is included by construction "
         "(state at t reads info <= t only).",
         "OK_TRAILING_INCLUSIVE"),
        (P0, "sigma[i - 251:i + 1]", "p0/p0_lib.py",
         "VOL-REGIME tercile boundaries from the trailing 252-sigma window "
         "ending at and including t; sigma_j = std over the trailing L "
         "returns; NEVER full-sample (verified: no percentile call outside "
         "a trailing slice).",
         "OK_TRAILING_INCLUSIVE"),
        (P0, "np.min(adj_low[i - K:i])", "p0/p0_lib.py",
         "EVENT-UNWIND prior-K low EXCLUDES bar t per the §5 spec "
         "min(adj_low_{t-K..t-1}).",
         "OK_EXCLUDES_T"),
        (IE, "def med252_series", "i/i_engine.py",
         "band median dvol over the trailing 252 sessions ending at and "
         "including i; band assignment at decision t uses info <= t only.",
         "OK_TRAILING_INCLUSIVE"),
        (IE, "entry_i = t + entry_offset", "i/i_engine.py",
         "entry = t+1 open, exit = t+1+H open: fills strictly AFTER the "
         "decision instant; no same-bar fill anywhere (positive controls "
         "D3/D5 prove the t+1 open is genuinely read).",
         "OK_CLOCK_NO_SAME_BAR"),
        (IE, "for d in held:", "i/i_engine.py",
         "log slices open[d+1]/open[d] for d in [entry, exit): forward "
         "prices are consumed ONLY as the leg's own OUTCOME accounting "
         "inside its holding window - never into state formation.",
         "OK_OUTCOME_ONLY"),
        (IE, "while ff_exit + 1 < n and dates[ff_exit + 1] <= fends[fold]:",
         "i/i_engine.py",
         "force-flat anchor walks forward over SERVED-DATE comparisons "
         "against the ex-ante frozen fold calendar only - it never reads a "
         "price/volume of a future bar; fold ends are calendar thirds "
         "frozen before any measurement (p0_lib.fold_boundaries).",
         "OK_CALENDAR_ONLY"),
        (IE, "mutated[1:] = mut_state[:-1]", "i/i_engine.py",
         "C-PIT-MUTATION control shifts the state mask one session EARLIER "
         "(recompute at i-1) - a mutation control, not a state input.",
         "OK_CONTROL"),
        (AD, "def max_drawdown", "i/adjudicate.py",
         "cumsum over the REALIZED P-11 book series - an OUTCOME statistic "
         "for the MDD gate; the adjudication harness never feeds state "
         "formation.",
         "OK_OUTCOME_ONLY"),
        (AD, "def load_real_data", "i/adjudicate.py",
         "the real-data path: refuses without the EXACT GO phrase (P-8), "
         "then verifies freeze pins before any parse; not reachable from "
         "the dry-run path exercised here (stub paths only).",
         "OK_GO_GATED"),
    ]
    curated = []
    for path, snippet, label, analysis, verdict in curated_rows:
        curated.append({"file": label,
                        "line": _line_of(path, snippet),
                        "snippet": snippet[:100],
                        "analysis": analysis, "verdict": verdict})
    return {"method": "static audit of the imported P0 census kernels "
                      "(p0/p0_lib.py) + the arm engines (i/i_engine.py) + "
                      "the harness (i/adjudicate.py) at HEAD " + BASE_SHA,
            "forbidden_patterns": forbidden,
            "forbidden_hits": grep_hits,
            "window_stat_calls": watch_hits,
            "curated_evidence": curated,
            "n_forbidden_hits": len(grep_hits)}


def _doctor_from(nm: E.NameData, t: int, price_mult: float = 3.7,
                 vol_mult: float = 5.0) -> E.NameData:
    """TAINT: multiply every bar STRICTLY AFTER decision index t."""
    n = len(nm.dates)
    m = np.ones(n, dtype=bool)
    m[:t + 1] = False
    return E.NameData(
        nm.symbol, nm.dates,
        np.where(m, nm.adj_open * price_mult, nm.adj_open),
        np.where(m, nm.adj_high * price_mult, nm.adj_high),
        np.where(m, nm.adj_low * price_mult, nm.adj_low),
        np.where(m, nm.adj_close * price_mult, nm.adj_close),
        np.where(m, nm.volume * vol_mult, nm.volume))


def _doctor_one(nm: E.NameData, k: int, field: str, mult: float):
    arrs = {f: np.array(getattr(nm, f), dtype=float, copy=True)
            for f in ("adj_open", "adj_high", "adj_low", "adj_close",
                      "volume")}
    arrs[field][k] *= mult
    return E.NameData(nm.symbol, nm.dates, arrs["adj_open"],
                      arrs["adj_high"], arrs["adj_low"], arrs["adj_close"],
                      arrs["volume"])


def _doctor_one_bar(nm: E.NameData, k: int, price_mult: float = 3.0,
                    vol_mult: float = 5.0) -> E.NameData:
    """Doctor EXACTLY ONE bar (all price fields x price_mult, volume x
    vol_mult) - the single-bar end-to-end probe."""
    def d(a):
        out = np.array(a, dtype=float, copy=True)
        out[k] *= price_mult
        return out
    vol = np.array(nm.volume, dtype=float, copy=True)
    vol[k] *= vol_mult
    return E.NameData(nm.symbol, nm.dates, d(nm.adj_open), d(nm.adj_high),
                      d(nm.adj_low), d(nm.adj_close), vol)


def dynamic_leak_scan(names, spy, calendar, b1, b2, bundles):
    """TASK 2 dynamic half: taint / doctored-future / positive controls."""
    tests = []
    findings = []
    cal = tuple(calendar)
    fends = E.fold_ends(cal, b1, b2)
    cal_index = {d: i for i, d in enumerate(cal)}

    def record(tid, design, ok, evidence):
        tests.append({"id": tid, "design": design,
                      "result": "PASS" if ok else "FAIL",
                      "evidence": evidence})
        if not ok:
            findings.append({"test": tid, "severity": "LEAK",
                             "evidence": evidence})

    # ---- D1: taint everything AFTER each sampled decision instant
    L = E.load_p0_lib()
    for cid in E.CELL_IDS:
        cell = E.CELL_BY_ID[cid]
        masks = E.arm_decision_masks(names, cell)
        samples = []
        for sym in sorted(masks):
            nm = names[sym]
            by_fold = {}
            for t in masks[sym]:
                by_fold.setdefault(L.assign_fold(nm.dates[t], b1, b2),
                                   []).append(t)
            for f in sorted(by_fold):
                for t in by_fold[f][:2]:
                    samples.append((sym, t))
            if len(samples) >= TAINT_CAP[cid]:
                break
        samples = samples[:TAINT_CAP[cid]]
        n_ok = 0
        failures = []
        for sym, t in samples:
            nm = names[sym]
            f1, b1m = E.state_fired_mask(nm, cell["family"], cell["params"])
            dnm = _doctor_from(nm, t)
            f2, b2m = E.state_fired_mask(dnm, cell["family"], cell["params"])
            if f1[t] == f2[t] and b1m[t] == b2m[t]:
                n_ok += 1
            else:
                failures.append({"symbol": sym, "t": t, "date": nm.dates[t],
                                 "fired_baseline": bool(f1[t]),
                                 "fired_doctored": bool(f2[t])})
        record("D1:" + cid,
               "TAINT every bar strictly AFTER the decision instant "
               "(prices x3.7, volume x5.0) and re-run the EXACT frozen "
               "state kernel: fired[t] and bookable[t] must be invariant "
               "for every sampled (name, decision) across all folds",
               not failures,
               {"n_samples": len(samples), "n_invariant": n_ok,
                "failures": failures[:10]})

    # ---- D2: single doctored FUTURE bar, full end-to-end pipeline
    base_masks = {cid: E.arm_decision_masks(names, E.CELL_BY_ID[cid])
                  for cid in E.CELL_IDS}
    dnames = dict(names)
    dnames[DOCTOR2_SYM] = _doctor_one_bar(names[DOCTOR2_SYM], DOCTOR2_IDX,
                                          3.0, 5.0)
    _drep, dbund, _dser = run_pipeline(dnames, spy, calendar, b1, b2)
    cid52 = "SSS-52W-HIGH-B10-H20"
    cidgap = "SSS-GAP-P25-CONFIRM-H1"
    cidvol = "SSS-VOL-REGIME-L21-LOW-H20"
    nm0 = names[DOCTOR2_SYM]
    # (i) state invariance for decisions whose window ends before the bar
    inv_ok = True
    bad_state = []
    for cid in (cidgap, cid52, cidvol):
        cell = E.CELL_BY_ID[cid]
        f_base, b_base = E.state_fired_mask(nm0, cell["family"],
                                            cell["params"])
        f_doc, b_doc = E.state_fired_mask(dnames[DOCTOR2_SYM],
                                          cell["family"], cell["params"])
        for t in base_masks[cid][DOCTOR2_SYM]:
            if t <= DOCTOR2_IDX - 2 and (f_base[t] != f_doc[t]
                                         or b_base[t] != b_doc[t]):
                inv_ok = False
                bad_state.append({"cell": cid, "t": t})
    # (ii) band + entry invariance for t <= K-2
    band_ok = True
    entry_bad = []
    base_by_key = {(lg.symbol, lg.decision_date): lg
                   for lg in bundles[cid52]["candidate"].legs}
    doc_by_key = {(lg.symbol, lg.decision_date): lg
                  for lg in dbund[cid52]["candidate"].legs}
    for key, lg in base_by_key.items():
        if key[0] != DOCTOR2_SYM:
            continue
        di = E.nm_dates_index(nm0, key[1])
        if di is None or di > DOCTOR2_IDX - 2:
            continue
        dlg = doc_by_key.get(key)
        if dlg is None:
            band_ok = False
            entry_bad.append({"decision": key[1], "issue": "leg-missing"})
            continue
        if lg.band != dlg.band or lg.entry_date != dlg.entry_date:
            band_ok = False
            entry_bad.append({"decision": key[1]})
    # (iii) POSITIVE CONTROL: legs holding across K change gross; legs
    # entirely before K are unchanged
    changed = unchanged = 0
    pc_ok = True
    for key, lg in base_by_key.items():
        if key[0] != DOCTOR2_SYM:
            continue
        di = E.nm_dates_index(nm0, key[1])
        if di is None or di > DOCTOR2_IDX - 1:
            continue
        dlg = doc_by_key.get(key)
        if dlg is None:
            continue
        entry_i = di + 1
        xi = E.nm_dates_index(nm0, lg.exit_date)
        if entry_i <= DOCTOR2_IDX <= xi:
            if lg.gross != dlg.gross:
                changed += 1
        elif xi is not None and xi < DOCTOR2_IDX:
            if lg.gross == dlg.gross and lg.net == dlg.net:
                unchanged += 1
            else:
                pc_ok = False
    pc_ok &= changed >= 1
    # (iv) untouched names' arm masks identical (8 deterministic probes)
    other_ok = True
    probe = sorted(names)[::6]
    for sym in probe:
        if sym == DOCTOR2_SYM:
            continue
        for cid in E.CELL_IDS:
            if base_masks[cid][sym] != E.arm_decision_masks(
                    dnames, E.CELL_BY_ID[cid])[sym]:
                other_ok = False
    d2_ok = inv_ok and band_ok and pc_ok and other_ok
    record("D2:end-to-end-doctored-future-bar",
           f"doctor ONE future bar ({DOCTOR2_SYM} @ calendar index "
           f"{DOCTOR2_IDX}: all prices x3, volume x5) and re-run the FULL "
           "3-cell pipeline: (i) state of every decision whose window "
           "ends before the bar is invariant; (ii) band + entry invariant; "
           "(iii) POSITIVE CONTROL: legs whose entry/exit open IS the "
           "doctored bar change gross while legs entirely before it are "
           "unchanged (proves the bar is read exactly where the contract "
           "says it must be and nowhere else); (iv) untouched names' "
           "masks identical",
           d2_ok,
           {"doctored_bar": [DOCTOR2_SYM, DOCTOR2_IDX],
            "state_invariance_ok": inv_ok,
            "state_failures": bad_state[:10],
            "band_entry_invariance_ok": band_ok,
            "band_entry_failures": entry_bad[:10],
            "positive_control_legs_changed": changed,
            "positive_control_legs_before_bar_unchanged": unchanged,
            "other_names_masks_identical": other_ok,
            "probe_names": probe})

    # ---- D3: POSITIVE CONTROL - the entry genuinely reads the t+1 OPEN
    d3_ok = True
    d3_ev = []
    for cid, t0 in ((cidgap, GAP_WEDGE_SERVED), (cid52, 320)):
        cell = E.CELL_BY_ID[cid]
        H = int(cell["params"]["H"])
        nm = names[DOCTOR2_SYM]
        f1, _ = E.state_fired_mask(nm, cell["family"], cell["params"])
        dnm = _doctor_one(nm, t0 + 1, "adj_open", 3.0)
        f2, _b2m = E.state_fired_mask(dnm, cell["family"], cell["params"])
        med1 = E.med252_series(nm)
        med2 = E.med252_series(dnm)
        legs_a, _, _ = E.build_legs(nm, [t0], H, cal_index, fends,
                                    E.STRESS_TIER)
        legs_b, _, _ = E.build_legs(dnm, [t0], H, cal_index, fends,
                                    E.STRESS_TIER)
        gross_changed = bool(legs_a and legs_b
                             and legs_a[0].gross != legs_b[0].gross)
        state_same = bool(f1[t0] == f2[t0])
        band_same = bool(E.band_at(nm, t0, med1)
                         == E.band_at(dnm, t0, med2))
        okr = state_same and band_same and gross_changed
        d3_ok &= okr
        d3_ev.append({"cell": cid, "t0": t0,
                      "fired_invariant": state_same,
                      "band_invariant": band_same,
                      "gross_changed_by_entry_open_doctor": gross_changed})
    record("D3:positive-control-entry-open",
           "doctor ONLY open[t0+1] (x3.0): the STATE at t0 and the band at "
           "t0 must NOT move (their windows end at t0) while the leg gross "
           "MUST move - proves the engine genuinely fills at the t+1 open "
           "AND that the instrumentation detects state/price sensitivity",
           d3_ok, {"cases": d3_ev})

    # ---- D4: state window ends exactly at t
    d4_ok = True
    d4_ev = []
    nm = names[DOCTOR2_SYM]
    t0 = 320
    dnm = _doctor_one(nm, t0 + 1, "adj_close", 0.5)   # crash close[t0+1]
    for cid in E.CELL_IDS:
        cell = E.CELL_BY_ID[cid]
        f1, b1m = E.state_fired_mask(nm, cell["family"], cell["params"])
        f2, b2m = E.state_fired_mask(dnm, cell["family"], cell["params"])
        same_at_t0 = bool(f1[t0] == f2[t0] and b1m[t0] == b2m[t0])
        d4_ok &= same_at_t0
        d4_ev.append({"cell": cid, "fired_t0_invariant": same_at_t0,
                      "fired_t0": bool(f1[t0])})
    # 52W must flip OFF at t0+1 under the crash (proximity >> band)
    f52_1, _ = E.state_fired_mask(nm, "52W-HIGH", {"band_pct": 10})
    f52_2, _ = E.state_fired_mask(dnm, "52W-HIGH", {"band_pct": 10})
    flip52 = bool(f52_1[t0 + 1]) and not bool(f52_2[t0 + 1])
    d4_ok &= flip52
    # GAP at t0+1 must be UNCHANGED (correct semantics: gap_{t0+1} reads
    # open[t0+1] and close[t0]; close[t0+1] is NOT in its state window)
    fg1, _ = E.state_fired_mask(nm, "GAP",
                                {"pctl": 25, "direction": "confirm"})
    fg2, _ = E.state_fired_mask(dnm, "GAP",
                                {"pctl": 25, "direction": "confirm"})
    gap_same = bool(fg1[t0 + 1] == fg2[t0 + 1])
    d4_ok &= gap_same
    record("D4:state-window-ends-at-t",
           "doctor ONLY close[t0+1] (x0.5 crash): state at t0 invariant "
           "for ALL three families; 52W-HIGH flips OFF at t0+1 (positive "
           "control: the crashed bar legitimately enters ITS OWN window); "
           "GAP at t0+1 unchanged (its window genuinely never reads "
           "close[t0+1]) - pins the exact info boundary: state(s) reads "
           "info <= s, never beyond",
           d4_ok, {"t0": t0, "cases": d4_ev,
                   "w52_flip_off_at_t0_plus_1": flip52,
                   "gap_invariant_at_t0_plus_1": gap_same})

    # ---- D5: no same-bar fills anywhere (structural, all books)
    scan = global_leg_scan(bundles, names, calendar, b1, b2)
    d5_ok = not scan["problems"]
    record("D5:no-same-bar-fills",
           "structural scan of EVERY leg in EVERY book of EVERY cell: "
           "entry index == decision index + 1 (candidate and all controls) "
           "or +1+H (C-DELAY-H); exit index == entry + book H unless "
           "force-flat (then the fold anchor); net = gross - "
           "2*band*stress/1e4 to 1e-12",
           d5_ok, {"legs_scanned": scan["n_legs"],
                   "problems": scan["problems"][:10],
                   "n_problems": len(scan["problems"])})

    return tests, findings


def run_leak_scan(ds, bundles):
    static = static_scan()
    tests, findings = dynamic_leak_scan(
        ds["names"], ds["spy"], ds["calendar"], ds["b1"], ds["b2"], bundles)
    ok = (static["n_forbidden_hits"] == 0 and not findings
          and all(t["result"] == "PASS" for t in tests))
    return {
        "schema": "stocks_search_v1_leak_scan@1",
        "cycle_id": CYCLE_ID, "real_cycle_id": REAL_CYCLE,
        "task_id": TASK_ID, "base_sha": BASE_SHA, "branch": BRANCH,
        "scope": ("PIT audit of the 3 exact-arm engines: every state input "
                  "must derive ONLY from info available at or before the "
                  "decision instant (t close); fail-closed: any leak = "
                  "LEAK_FOUND"),
        "status": "CLEAN" if ok else "LEAK_FOUND",
        "fail_closed": ("any failed test, forbidden-pattern hit or engine-"
                        "reported leak sets status=LEAK_FOUND and the lane "
                        "exits nonzero - never an inferred CLEAN"),
        "static": static,
        "dynamic": tests,
        "findings": findings,
        "doc_notes": [
            {"kind": "DOC_INCONSISTENCY_BENIGN",
             "detail": ("p0_lib._rolling_median docstring says the window "
                        "ends at i-1; the CODE (and every caller) is "
                        "trailing-INCLUSIVE of i.  Both readings are "
                        "backward-safe (no forward information); the "
                        "kernel is the frozen authority shared by the "
                        "census and the engines, so arm identity is "
                        "unaffected.  Disclosed, not a leak.")},
            {"kind": "DESIGN_NOTE_DISCLOSED",
             "detail": ("The fold force-flat anchor walks served dates "
                        "against the ex-ante frozen fold calendar (dates "
                        "only, never future prices).  The fold freeze is "
                        "calendar-thirds computed before any measurement "
                        "(p0_lib.fold_boundaries), so this is not "
                        "lookahead.")},
        ],
        "conclusion": ("CLEAN - no lookahead, no ffill/imputation, no "
                       "full-sample statistic in state formation, no "
                       "same-bar fill, no target/return leakage into "
                       "state; the entry genuinely reads the t+1 open and "
                       "every state window ends at t (positive controls "
                       "prove the instrumentation is sensitive)" if ok
                       else "LEAK_FOUND - fail-closed"),
    }


# ------------------------------------------------------------------ main

def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, sort_keys=True) + "\n")
    return sha256_text(canon(obj))


def git(*args):
    return subprocess.run(
        ["git", "-C", str(_REPO_ROOT), *args], capture_output=True,
        text=True, check=True).stdout.strip()


def emit_digest():
    ds = build_dataset()
    d, _r, _b, _s = pipeline_digest(ds["names"], ds["spy"], ds["calendar"],
                                    ds["b1"], ds["b2"], ds["meta"])
    print(json.dumps({
        "dataset_sha256": sha256_text(canon(ds["meta"])),
        "pipeline_sha256": d}))
    return 0


def selfcheck():
    head = git("rev-parse", "HEAD")
    branch = git("branch", "--show-current")
    if head != BASE_SHA or branch != BRANCH:
        print(json.dumps({"STOP_CONDITION": "FROZEN_SHA_MISMATCH",
                          "head": head, "branch": branch}))
        return 2

    # lock posture: this lane runs NO heavy job and takes no heavy lock
    lock = subprocess.run(
        ["/Users/hoangminhlong/my-quantitative/.venv/bin/python",
         "/Users/hoangminhlong/my-quantitative/research/researchctl.py",
         "locks", "inspect"], capture_output=True, text=True)
    try:
        lock_state = json.loads(lock.stdout).get("verdict", "UNKNOWN")
    except Exception:                                       # noqa: BLE001
        lock_state = "UNPARSED"

    ds = build_dataset()
    digest, reports, bundles, series = pipeline_digest(
        ds["names"], ds["spy"], ds["calendar"], ds["b1"], ds["b2"],
        ds["meta"])

    # cross-process determinism (different PYTHONHASHSEED)
    sub_digests = []
    for seed in ("1", "random"):
        env = dict(os.environ)
        env["PYTHONHASHSEED"] = seed
        r = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--emit-digest"],
            capture_output=True, text=True, env=env, cwd=str(_REPO_ROOT))
        if r.returncode != 0:
            sub_digests.append({"seed": seed, "error": r.stderr[-400:]})
        else:
            sub_digests.append({"seed": seed,
                                **json.loads(
                                    r.stdout.strip().splitlines()[-1])})
    xok = (len(sub_digests) == 2
           and all("pipeline_sha256" in s for s in sub_digests)
           and sub_digests[0]["pipeline_sha256"]
           == sub_digests[1]["pipeline_sha256"] == digest)

    checks, t1_ok = run_all_checks(ds, reports, bundles, series, digest)
    checks.insert(2, check(
        "C2", "Cross-process determinism (PYTHONHASHSEED 1 vs random)",
        "the full pipeline re-run in two fresh subprocesses under "
        "different hash seeds must reproduce the in-process digest "
        "byte-identically", xok,
        {"in_process": digest, "subprocesses": sub_digests}))
    t1_ok = t1_ok and xok

    leak = run_leak_scan(ds, bundles)

    # battery: the I-lane suite (and P0, read-only import) must stay green
    pytest = subprocess.run(
        ["/Users/hoangminhlong/my-quantitative/.venv/bin/python", "-m",
         "pytest", "tests/test_stocks_search_v1_i.py", "-q"],
        capture_output=True, text=True, cwd=str(_REPO_ROOT))
    pytest_p0 = subprocess.run(
        ["/Users/hoangminhlong/my-quantitative/.venv/bin/python", "-m",
         "pytest", "tests/test_stocks_search_v1_p0.py", "-q"],
        capture_output=True, text=True, cwd=str(_REPO_ROOT))
    battery = [
        {"command": ".venv/bin/python -m pytest "
                    "tests/test_stocks_search_v1_i.py -q",
         "exit_code": pytest.returncode,
         "tail": (pytest.stdout or pytest.stderr).strip().splitlines()[-1:]},
        {"command": ".venv/bin/python -m pytest "
                    "tests/test_stocks_search_v1_p0.py -q",
         "exit_code": pytest_p0.returncode,
         "tail": (pytest_p0.stdout or pytest_p0.stderr)
         .strip().splitlines()[-1:]},
    ]

    all_ok = (t1_ok and leak["status"] == "CLEAN"
              and pytest.returncode == 0 and pytest_p0.returncode == 0)

    dry = {
        "schema": "stocks_search_v1_dry_run_report@1",
        "cycle_id": CYCLE_ID, "real_cycle_id": REAL_CYCLE,
        "task_id": TASK_ID,
        "phase": "Z (sanitized exact-arm dry-run + recursive leak scan)",
        "base_sha": BASE_SHA, "branch": BRANCH, "head_verified": head,
        "engines_consumed_read_only": {
            "i_engine": str(_I_DIR / "i_engine.py"),
            "adjudicate": str(_I_DIR / "adjudicate.py"),
            "selection_freeze_sha256": FREEZE_SHA,
            "p0_lib_pin": "verified inside load_p0_lib (freeze "
                          "data_manifests_sha256['p0_lib.py'])"},
        "sanitized": True,
        "scored": False,
        "scope_statement": ("SYNTHETIC data only; NO real archive was read "
                            "or executed; the GO-gated loader was exercised "
                            "with STUB paths only; all cell verdicts below "
                            "are synthetic-verdicts with NO scored meaning "
                            "and are not evidence of profitability"),
        "heavy_lock": {"taken": False,
                       "machine_state_at_run": lock_state,
                       "note": ("light sanitized job; the machine-wide "
                                "heavy lock is not required and was not "
                                "taken; shadow workers (15315/15316) "
                                "untouched")},
        "dataset": ds["meta"],
        "determinism": {
            "in_process_pipeline_sha256": digest,
            "note": "full evidence in checks C1/C2"},
        "checks": checks,
        "leak_scan_status": leak["status"],
        "battery": battery,
        "all_checks_pass": all_ok,
        "overall": "PASS" if all_ok else "FAIL",
    }
    d1 = write_json(_HERE / "dry_run_report.json", dry)
    d2 = write_json(_HERE / "leak_scan.json", leak)
    print(json.dumps({
        "overall": dry["overall"],
        "checks": {c["id"]: c["result"] for c in checks},
        "leak_scan": leak["status"],
        "battery": {b["command"]: b["exit_code"] for b in battery},
        "digest": digest,
        "reports": {"dry_run_report_sha256": d1, "leak_scan_sha256": d2}},
        indent=1))
    return 0 if all_ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selfcheck", action="store_true")
    ap.add_argument("--emit-digest", action="store_true")
    args = ap.parse_args()
    if args.emit_digest:
        return emit_digest()
    return selfcheck()


if __name__ == "__main__":
    sys.exit(main())
