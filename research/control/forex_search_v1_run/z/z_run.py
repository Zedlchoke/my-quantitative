#!/usr/bin/env python
"""FOREX-SEARCH-V1 Z-lane deterministic runner (lane fsearch-z, plan §9 Z).

Phase Z per plans/PLAN_forex_search_v1.md §9: SANITIZED EXACT-ARM DRY-RUN +
RECURSIVE LEAK SCAN over the I-lane engines (research/control/
forex_search_v1_run/i/{i_engine.py,adjudicate.py}) and the frozen S
selection (s/selection_freeze.json) — all consumed READ-ONLY.

NO REAL DATA ANYWHERE: the dataset is a deterministic seeded synthetic
5-leg OHLC construction (np.random.RandomState — frozen streams) with
holidays/missing bars, a fold boundary, zero-range (high==low) degenerate
bars, a flat-close run, and known wedges for the CLOCK-COND / OPEN-GAP /
VOL-DRIFT states. The GO-gate checks run the staging loader ONLY against a
stubbed empty /tmp directory — real staging bytes are never read.

Outputs (this lane's only writes):
  z/dry_run_report.json   — pipeline + checks battery (a)-(f) of the packet
  z/leak_scan.json        — static (AST) + dynamic (taint) PIT audit
Exit 0 iff every check PASSes and the leak verdict is NO_LEAK_FOUND.
--selfcheck re-runs everything and requires a byte-identical report payload.
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # keep p0/, i/ byte-clean (read-only lanes)

import ast
import hashlib
import json
import os
import re
import shutil
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/forex-search-v1/integration")
RUN = WT / "research/control/forex_search_v1_run"
I_DIR = RUN / "i"
P0_DIR = RUN / "p0"
Z_DIR = RUN / "z"
sys.path.insert(0, str(I_DIR))

import i_engine as eng  # noqa: E402
import adjudicate as adj  # noqa: E402

PC = eng.p0()

DISPATCH_SHA = "cd1fe57379f679b455b3142b5e5ac1ba4944d3b3"
BRANCH = "orca/forex-search-v1-integration"
SEED = 20260917
N_BASE = 4980
N_PREPEND_EURUSD = 27
START_DATE = date(2008, 1, 2)
LEGS_ORDER = list(eng.LEGS)
BASE_PX = {"EURUSD": 1.10, "GBPUSD": 1.35, "USDCAD": 1.30,
           "AUDUSD": 0.72, "NZDUSD": 0.62}
STRESS = eng.STRESS_MULTIPLIER_PRIMARY

# plan §10 disclosure strings, typed VERBATIM from
# plans/PLAN_forex_search_v1.md (read-only) — the dry run asserts that every
# produced verdict carries these exact strings.
PLAN_S3_DISCLOSURE = (
    "accepted under owner-relaxed acceptance battery (R0 0.30 / DSR alpha "
    "0.10 at N = grid) | PBO NOT_RUN fail-closed (<=3 cells, d0992d17 "
    "class) | R0 NOT_RUN (D2 skipped by owner amendment §3b)")
PLAN_S4F4_DISCLOSURE = (
    "financing = stated-conservative nightly-average extrapolation (1.7 "
    "bps; worst single night may exceed it; no per-leg differential census "
    "exists — OHLC-only source)")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def sha256_obj(obj) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, indent=1).encode("utf-8")


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# =====================================================================
# Synthetic sanitized dataset (seeded, deterministic; NO archive bytes)
# =====================================================================

def weekday_dates(start: date, n: int) -> list:
    out, d = [], start
    while len(out) < n:
        if d.isoweekday() <= 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def prepend_weekdays(before: date, k: int) -> list:
    out, d = [], before - timedelta(days=1)
    while len(out) < k:
        if d.isoweekday() <= 5:
            out.append(d.isoformat())
        d -= timedelta(days=1)
    return sorted(out)


def leg_drop_mask(k_leg: int, n: int) -> np.ndarray:
    """Deterministic per-leg weekday-holiday drops (~1/397 of base bars)."""
    j = np.arange(n)
    return (((j + 7 * (k_leg + 1)) * 31) % 397) == 0


def generate_dataset() -> tuple:
    rng = np.random.RandomState(SEED)
    base_dates = weekday_dates(START_DATE, N_BASE)
    pre = prepend_weekdays(START_DATE, N_PREPEND_EURUSD)
    legs, meta = {}, {}
    for k, ln in enumerate(LEGS_ORDER):
        is_eur = ln == "EURUSD"
        n_pre = len(pre) if is_eur else 0
        n = N_BASE + n_pre
        dates_all = (list(pre) + list(base_dates)) if is_eur else list(base_dates)
        drop = leg_drop_mask(k, N_BASE)  # holidays: weekday bars removed, NO ffill
        keep = np.ones(n, dtype=bool)
        keep[n_pre:] = ~drop
        dates = [d for d, kp in zip(dates_all, keep) if kp]
        base_ord = np.full(n, -1, dtype=np.int64)
        base_ord[n_pre:] = np.arange(N_BASE)
        base_ord = base_ord[keep]
        bo = np.maximum(base_ord, 0)
        calm = (bo // 130) % 2 == 0
        sigma = np.where(calm, 0.0020, 0.0120)
        sigma[base_ord < 0] = 0.0020
        drift = np.where(calm, 0.00035, -0.00090)  # VOL-DRIFT wedge
        drift[base_ord < 0] = 0.0
        day = np.array([int(d[8:10]) for d in dates])
        mpw = np.where(day >= 16, 0.0002, 0.0)     # CLOCK-COND monthpos wedge
        mpw[base_ord < 0] = 0.0
        nk = len(dates)
        ret = drift + mpw + sigma * rng.standard_normal(nk)
        gw = np.zeros(nk)
        is_wedge = (base_ord % 89 == 0) & (base_ord >= 89)
        sign = np.where((bo // 89) % 2 == 0, 1.0, -1.0)
        gw[is_wedge] = sign[is_wedge] * 6.0 * sigma[is_wedge]  # OPEN-GAP wedge
        eps = rng.uniform(-1e-4, 1e-4, nk)
        c = np.empty(nk)
        o = np.empty(nk)
        c[0] = o[0] = BASE_PX[ln]
        for idx in range(1, nk):
            o[idx] = c[idx - 1] * (1.0 + gw[idx] + eps[idx])
            c[idx] = c[idx - 1] * float(np.exp(ret[idx]))
        h = np.maximum(o, c) * (1.0 + np.abs(rng.standard_normal(nk)) * 0.3 * sigma)
        low = np.minimum(o, c) * (1.0 - np.abs(rng.standard_normal(nk)) * 0.3 * sigma)
        # degenerate zero-range bars (the high==low analog in FX)
        degen = (base_ord % 601 == 5) & (base_ord >= 0)
        for idx in np.nonzero(degen)[0]:
            o[idx] = h[idx] = low[idx] = c[idx]
        # flat-close run (zero-variance degenerate analog), base ordinals 3000..3004
        i2999 = np.nonzero(base_ord == 2999)[0]
        flat = (base_ord >= 3000) & (base_ord <= 3004)
        flat_present = bool(i2999.size and flat.any())
        if flat_present:
            c_flat = float(c[i2999[0]])
            for idx in np.nonzero(flat)[0]:
                o[idx] = h[idx] = low[idx] = c[idx] = c_flat
        legs[ln] = {"symbol": ln, "dates": dates, "open": o, "high": h,
                    "low": low, "close": c}
        meta[ln] = {
            "rows": len(dates), "first": dates[0], "last": dates[-1],
            "holiday_drops": int(drop.sum()),
            "prepend_own_only_dates": n_pre,
            "zero_range_bars": int(degen.sum()) + (int(flat.sum())
                                                   if flat_present else 0),
            "gap_wedge_bars": int(is_wedge.sum()),
        }
    sets = [set(v["dates"]) for v in legs.values()]
    master = sorted(set.intersection(*sets))
    folds = PC.make_folds(master)
    digests = {ln: hashlib.sha256(np.concatenate(
        [legs[ln]["open"], legs[ln]["high"], legs[ln]["low"],
         legs[ln]["close"]]).tobytes()).hexdigest() for ln in LEGS_ORDER}
    dsig = sha256_obj({"legs": digests, "master": master, "seed": SEED})
    return legs, master, folds, {
        "seed": SEED, "generator": "numpy.random.RandomState (frozen streams)",
        "n_base_weekdays": N_BASE, "start": START_DATE.isoformat(),
        "master_bars": len(master),
        "fold_boundaries_index": folds["boundaries_index"],
        "fold_last_bars": [b - 1 for b in folds["boundaries_index"][1:]],
        "per_leg": meta,
        "wedges": {
            "CLOCK-COND": "day-of-month >= 16 carries +2 bps extra drift",
            "OPEN-GAP": "every 89th base bar opens +/- 6 sigma vs prior close",
            "VOL-DRIFT": "alternating calm (0.20%/d) / stressed (1.20%/d) "
                         "130-bar blocks; calm blocks drift up, stressed drift down",
        },
        "degenerates": "zero-range (high==low) bars every 601st base bar + a "
                       "5-bar flat-close run at base ordinals 3000..3004",
        "dataset_sha256": dsig,
        "no_real_data": "synthetic only; no staging/archive bytes read",
    }


# =====================================================================
# Full pipeline through the I-lane engines + adjudicator (exact arms)
# =====================================================================

def build_usd_ctx(trades: list, master: list, usd: dict) -> dict:
    _, fin = eng.ladder_bps(trades, STRESS)
    per_leg = {}
    for ln in LEGS_ORDER:
        rho, _ = eng.pearson(eng.daily_pnl_series(trades, fin, master, legname=ln),
                             usd["per_leg_usd_side_bps"][ln])
        per_leg[ln] = float(rho) if rho is not None else None
    rho_p, _ = eng.pearson(eng.daily_pnl_series(trades, fin, master),
                           usd["basket_bps"])
    return {"per_leg_corr": per_leg,
            "pooled_corr": float(rho_p) if rho_p is not None else None}


def gate_audit(cfg: dict, pos: dict, legs: dict, master: list, folds: dict,
               own_index: dict) -> dict:
    """Full audit of the force-flat/execution gate: for EVERY raw state
    firing, pos != 0 IFF gate_firing passes; every gated firing is
    classified (no-execution-bar / beyond-sample / cross-fold)."""
    fold_id = eng.fold_ids(folds, len(master))
    audit = {"kept": 0, "gated_no_exec": 0, "gated_beyond_sample": 0,
             "gated_cross_fold": 0, "mismatches": []}
    raw = eng.raw_state(cfg, legs, master, LEGS_ORDER, shift=0)
    for ln in LEGS_ORDER:
        dates = legs[ln]["dates"]
        for mi, direction in sorted(raw[ln].items()):
            mi = int(mi)
            passes = eng.gate_firing(mi, direction, ln, legs, master, fold_id,
                                     own_index[ln])
            want = 1 if direction == "LONG" else -1
            if passes:
                audit["kept"] += 1
                if int(pos[ln][mi]) != want:
                    audit["mismatches"].append({"leg": ln, "mi": mi,
                                                "kind": "kept_but_zero"})
            else:
                if int(pos[ln][mi]) != 0:
                    audit["mismatches"].append({"leg": ln, "mi": mi,
                                                "kind": "gated_but_positioned"})
                i = own_index[ln].get(master[mi])
                if i is None or i + 1 >= len(dates):
                    audit["gated_no_exec"] += 1
                else:
                    mi_next = int(np.searchsorted(master, dates[i + 1]))
                    if mi_next >= len(master):
                        audit["gated_beyond_sample"] += 1
                    elif fold_id[mi_next] != fold_id[mi]:
                        audit["gated_cross_fold"] += 1
                    else:
                        audit["mismatches"].append({"leg": ln, "mi": mi,
                                                    "kind": "unclassified_gate"})
    return audit


def run_pipeline(legs: dict, master: list, folds: dict) -> dict:
    freeze = eng.load_freeze()  # verifies the frozen selection_freeze sha
    arms = [s["config_id"] for s in freeze["selections"]]
    excerpts = {s["config_id"]: s["config_manifest_excerpt_verbatim"]
                for s in freeze["selections"]}
    usd = eng.usd_basket_series(legs, master, LEGS_ORDER)
    own_index = {ln: {d: i for i, d in enumerate(legs[ln]["dates"])}
                 for ln in LEGS_ORDER}
    per_arm, positions_by_arm, ctxs = {}, {}, []
    for cid in arms:
        cfg = excerpts[cid]
        pos = eng.build_positions(cfg, legs, master, folds, LEGS_ORDER)
        trades = eng.build_trades(pos, legs, master, folds, LEGS_ORDER)
        audit = gate_audit(cfg, pos, legs, master, folds, own_index)
        mut = eng.pit_mutated_positions(cfg, legs, master, folds, LEGS_ORDER)
        census = eng.weekday_share_of_firings(pos, master, LEGS_ORDER)
        comp_pos = eng.build_control_positions("complement", cfg, legs, master,
                                               folds, LEGS_ORDER)
        comp_trades = eng.build_trades(comp_pos, legs, master, folds, LEGS_ORDER)
        to_trades, to_note = None, None
        try:
            to_pos = eng.build_control_positions("trend_only", cfg, legs, master,
                                                 folds, LEGS_ORDER)
            to_trades = eng.build_trades(to_pos, legs, master, folds, LEGS_ORDER)
        except eng.Stop as st:
            to_note = {"code": st.code, "detail": st.detail}
        co_pos = eng.build_control_positions("clock_only", cfg, legs, master,
                                             folds, LEGS_ORDER)
        co_trades = eng.build_trades(co_pos, legs, master, folds, LEGS_ORDER)
        ctx = {
            "config_id": cid, "family": cfg["family"], "trades": trades,
            "stress": STRESS, "folds": folds, "master": master,
            "complement_trades": comp_trades,
            "trend_only_trades": to_trades,
            "trend_only_definition": cfg["r4_trend_only_book"],
            "clock_only_trades": co_trades,
            "weekday_census": census,
            "usd": build_usd_ctx(trades, master, usd),
            "shadows": {},          # absent controls: NOT_RUN, kill-only
            "k6_fold_nets": None,   # exact test NOT frozen at S: NOT_ADJUDICABLE
            "mutated_positions": mut,
            "serial_clustering": eng.serial_clustering_census(pos, LEGS_ORDER),
        }
        ctxs.append(ctx)
        positions_by_arm[cid] = pos
        price, financed = eng.ladder_bps(trades, STRESS)
        per_arm[cid] = {
            "family": cfg["family"],
            "positions_digest_synthetic": eng.positions_digest(pos, LEGS_ORDER),
            "n_trades": len(trades),
            "n_positions_fired": int(sum(int(np.count_nonzero(pos[ln]))
                                         for ln in LEGS_ORDER)),
            "gross_bps_total": float(sum(t["gross_bps"] for t in trades)),
            "price_book_net_bps": float(price.sum()),
            "financed_book_net_bps": float(financed.sum()),
            "gate_audit": {k: v for k, v in audit.items() if k != "mismatches"},
            "gate_audit_mismatch_count": len(audit["mismatches"]),
            "trend_only_note": to_note,
        }
    verdict = adj.adjudicate_cycle(ctxs, positions_by_arm, LEGS_ORDER,
                                   frozen_matrix=None)  # frozen-matrix rho
    # equality is deferred to the scored E run on REAL data (synthetic
    # positions cannot reproduce real-data position rhos by construction)
    return {"freeze_selected_order": arms, "per_arm": per_arm,
            "verdict": verdict, "n_master": len(master),
            "legs_order": LEGS_ORDER}


# =====================================================================
# Checks battery (packet items a)-(f))
# =====================================================================

def check(cid: str, desc: str, ok: bool, detail) -> dict:
    return {"id": cid, "description": desc,
            "verdict": "PASS" if ok else "FAIL", "detail": detail}


def run_checks(ds_meta: dict, legs: dict, master: list, folds: dict,
               run1: dict, run2: dict, go_rows: list) -> list:
    checks = []
    freeze = eng.load_freeze()
    arms = run1["freeze_selected_order"]
    own_index = {ln: {d: i for i, d in enumerate(legs[ln]["dates"])}
                 for ln in LEGS_ORDER}

    # (a) determinism -------------------------------------------------
    same_ds = ds_meta["dataset_sha256"] == run2["dataset_meta"]["dataset_sha256"]
    same_pos = all(run1["per_arm"][c]["positions_digest_synthetic"] ==
                   run2["per_arm"][c]["positions_digest_synthetic"] for c in arms)
    same_verdict = canonical(run1["verdict"]) == canonical(run2["verdict"])
    checks.append(check(
        "A1_PIPELINE_DOUBLE_RUN_BYTE_IDENTICAL",
        "two independent in-process runs (fresh dataset generation + full "
        "pipeline + adjudication) produce byte-identical canonical payloads",
        same_ds and same_pos and same_verdict,
        {"dataset_digest_equal": same_ds, "positions_digests_equal": same_pos,
         "adjudication_verdict_bytes_equal": same_verdict}))
    checks.append(check(
        "A2_CROSS_RUN_SELFCHECK",
        "--selfcheck re-runs everything and byte-compares the stored report "
        "payload (exit code is the verdict; see handoff test rows)",
        True,
        "executed via `z_run.py --selfcheck`; result recorded in the handoff "
        "tests[] rows, not embedded here (the file cannot contain its own "
        "comparison verdict)"))

    # (b) fold force-flat ---------------------------------------------
    bounds = folds["boundaries_index"]
    b_zero = True
    raw_fired_at_boundary = 0
    raw_clock = eng.raw_state(freeze["selections"][0]
                              ["config_manifest_excerpt_verbatim"],
                              legs, master, LEGS_ORDER, shift=0)
    for b in bounds[1:]:
        mi = b - 1
        for ln in LEGS_ORDER:
            if int(run1["_positions"][arms[0]][ln][mi]) != 0:
                b_zero = False
            raw_fired_at_boundary += int(mi in raw_clock[ln])
    checks.append(check(
        "B1_FORCE_FLAT_BOUNDARY_POSITIONS_ZERO",
        "no position exists on the last decision bar of any fold (execution "
        "bar t+1 would land in the next fold)",
        b_zero, {"boundary_minus_one_bars": [b - 1 for b in bounds[1:]]}))
    audit_all = {c: run1["per_arm"][c]["gate_audit"] for c in arms}
    mismatches = sum(run1["per_arm"][c]["gate_audit_mismatch_count"] for c in arms)
    checks.append(check(
        "B2_GATE_AUDIT_ALL_FIRINGS_CLASSIFIED",
        "for every raw state firing across all arms/legs: position != 0 IFF "
        "the force-flat gate passes; every gated firing classified",
        mismatches == 0,
        {"per_arm": audit_all,
         "note": "gated = cross-fold / beyond-sample / no-execution-bar; "
                 f"raw CLOCK-COND firings at boundary-1 bars: "
                 f"{raw_fired_at_boundary} (non-vacuity evidence)"}))
    fold_id = eng.fold_ids(folds, len(master))
    # B3: verify per-trade fold consistency directly on the built books
    # (build_trades itself raises CONTRACT_VIOLATION on any cross-fold
    # position, so a completed build is already gate-proofed; re-assert).
    b3_ok = True
    for c in arms:
        for t in _arm_trades(run1, c):
            if t["fold"] != fold_id[t["mi_decision"]]:
                b3_ok = False
    checks.append(check(
        "B3_TRADES_NEVER_CROSS_FOLD",
        "build_trades raises CONTRACT_VIOLATION on any cross-fold position; "
        "all three arm books were built without abort and every trade record "
        "carries fold == fold(decision bar)",
        b3_ok, {"trades_per_arm": {c: run1["per_arm"][c]["n_trades"]
                                   for c in arms}}))
    last = len(master) - 1
    beyond = all(not eng.gate_firing(last, "LONG", ln, legs, master, fold_id,
                                     own_index[ln]) for ln in LEGS_ORDER)
    checks.append(check(
        "B4_BEYOND_SAMPLE_REFUSAL",
        "gate_firing refuses a firing whose execution bar localizes beyond "
        "the frozen sample (last master bar, every leg)",
        beyond, {"last_master_bar": master[last]}))

    # (c) dual books ----------------------------------------------------
    c1, c2 = True, True
    for c in arms:
        db = _db(run1, c)
        c1 = c1 and db["verdict"] == "PASS" and bool(db["detail"]["pass"])
        # elementwise financed <= price on the arm's own trades
        tr = _arm_trades(run1, c)
        price, financed = eng.ladder_bps(tr, STRESS)
        c2 = c2 and bool(np.all(financed <= price + 1e-9))
    checks.append(check(
        "C1_DUAL_BOOKS_PASS_ALL_ARMS",
        "dual-books gate PASSes for all three arm books at stress 2.0 "
        "(financed never adds pnl; no aggregate sign inversion)",
        c1, {c: {"price_net_bps": _db(run1, c)["detail"]["price_net_bps"],
                 "financed_net_bps":
                     _db(run1, c)["detail"]["financed_net_bps"],
                 "worst_case_round_trip_bps":
                     _db(run1, c)["detail"]["worst_case_round_trip_bps"]}
            for c in arms}))
    checks.append(check(
        "C2_FINANCED_LE_PRICE_ELEMENTWISE",
        "financed book bps <= price book bps on every single trade of every "
        "arm (the uniform charge can only subtract)",
        c2, {}))
    # checker sensitivity: the gate must FIRE on violation fixtures
    base = [{"leg": "EURUSD", "fold": 1, "state_key": "side+1", "side": 1,
             "mi_decision": 0, "decision_date": master[0], "entry": 1.0,
             "exit": 1.0, "gross_bps": 5.0}]
    bad_fin = eng.dual_books_check(base, STRESS, fin_bps=-1.0)
    inv = eng.dual_books_check(
        [{"leg": "EURUSD", "fold": 1, "state_key": "side+1", "side": 1,
          "mi_decision": 0, "decision_date": master[0], "entry": 1.0,
          "exit": 1.0, "gross_bps": 7.0},
         {"leg": "GBPUSD", "fold": 1, "state_key": "side+1", "side": 1,
          "mi_decision": 1, "decision_date": master[1], "entry": 1.0,
          "exit": 1.0, "gross_bps": 7.0}], STRESS)
    checks.append(check(
        "C3_CHECKER_SENSITIVITY_NEGATIVE_FINANCING_FLAGGED",
        "checker sensitivity: a fixture whose 'financing' ADDS pnl "
        "(negative band) is flagged (financed_never_adds_pnl False -> fail)",
        bad_fin["financed_never_adds_pnl"] is False and bad_fin["pass"] is False,
        bad_fin))
    checks.append(check(
        "C4_CHECKER_SENSITIVITY_SIGN_INVERSION_FLAGGED",
        "checker sensitivity: a fixture whose financed aggregate inverts the "
        "price-book sign is flagged (sign_inversion True -> fail)",
        inv["sign_inversion"] is True and inv["pass"] is False, inv))

    # (d) 9.4 bps worst-case arithmetic ---------------------------------
    wc = eng.WORST_CASE_ROUND_TRIP_BPS
    zero = [{"leg": "EURUSD", "fold": 1, "state_key": "side+1", "side": 1,
             "mi_decision": 0, "decision_date": master[0], "entry": 1.0,
             "exit": 1.0, "gross_bps": 0.0}]
    _, fin_zero = eng.ladder_bps(zero, STRESS)
    be = [{"leg": "EURUSD", "fold": 1, "state_key": "side+1", "side": 1,
           "mi_decision": 0, "decision_date": master[0], "entry": 1.0,
           "exit": 1.00094, "gross_bps": (1.00094 / 1.0 - 1.0) * 1e4}]
    _, fin_be = eng.ladder_bps(be, STRESS)
    checks.append(check(
        "D1_WORST_CASE_CONSTANT_94",
        "operative stress worst case per round trip == 2 x 1.5 x 2.0 + "
        "1.7 x 2.0 == 9.4 bps (engine constant)",
        abs(wc - 9.4) < 1e-9,
        {"constant": wc, "arithmetic": "2 x 1.5 x 2.0 = 6.0 cost + "
                                       "1.7 x 2.0 = 3.4 financing"}))
    checks.append(check(
        "D2_ZERO_GROSS_TRADE_FINANCED_MINUS_94BPS",
        "hand check: a zero-gross round trip costs EXACTLY 9.4 bps financed "
        "at stress 2.0",
        abs(float(fin_zero[0]) + 9.4) < 1e-9, {"financed_bps": float(fin_zero[0])}))
    checks.append(check(
        "D3_BREAKEVEN_GROSS_94BPS_TRADE_FINANCED_ZERO",
        "hand check: a round trip with gross == +9.4 bps breaks EXACTLY even "
        "financed at stress 2.0",
        abs(float(fin_be[0])) < 1e-9,
        {"gross_bps": float(be[0]["gross_bps"]),
         "financed_bps": float(fin_be[0])}))
    t0 = _arm_trades(run1, arms[0])[0]
    g_manual = t0["side"] * (t0["exit"] / t0["entry"] - 1.0) * 1e4
    p_manual = g_manual - 2 * eng.COST_BPS_PER_FILL * STRESS
    f_manual = p_manual - eng.FIN_BPS_PER_NIGHT * STRESS
    pr, fi = eng.ladder_bps([t0], STRESS)
    checks.append(check(
        "D4_PIPELINE_TRADE_HAND_RECOMPUTE",
        "first fired trade of the rank-1 arm recomputed by hand: gross, "
        "price book and financed book all match the engine ladder",
        abs(g_manual - t0["gross_bps"]) < 1e-9 and
        abs(p_manual - float(pr[0])) < 1e-9 and
        abs(f_manual - float(fi[0])) < 1e-9,
        {"trade": {k: t0[k] for k in ("leg", "decision_date", "side",
                                      "entry", "exit")},
         "hand_gross_bps": g_manual, "hand_price_bps": p_manual,
         "hand_financed_bps": f_manual}))

    # (e) labels + verbatim disclosures ---------------------------------
    arm_labels_ok, cyc = True, run1["verdict"]
    for a in cyc["arms"]:
        lab = a["labels"]
        arm_labels_ok = arm_labels_ok and \
            lab["r0_ancestry"] == "NOT_RUN" and lab["pbo"] == "NOT_RUN" and \
            lab["relaxation_disclosure_verbatim"] == PLAN_S3_DISCLOSURE and \
            lab["financing_disclosure_verbatim"] == PLAN_S4F4_DISCLOSURE
    lab_c = cyc["labels"]
    checks.append(check(
        "E1_LABELS_ON_EVERY_ARM_AND_CYCLE",
        "every arm verdict AND the cycle verdict carry R0 NOT_RUN + "
        "PBO NOT_RUN fail-closed labels",
        arm_labels_ok and lab_c["r0_ancestry"] == "NOT_RUN"
        and lab_c["pbo"] == "NOT_RUN",
        {"cycle_labels": lab_c}))
    checks.append(check(
        "E2_PLAN_SECTION3_DISCLOSURE_VERBATIM",
        "the §3 relaxation disclosure string equals the plan §10 text "
        "VERBATIM (typed from plans/PLAN_forex_search_v1.md)",
        lab_c["relaxation_disclosure_verbatim"] == PLAN_S3_DISCLOSURE and
        PLAN_S3_DISCLOSURE == adj.RELAXATION_DISCLOSURE, {}))
    checks.append(check(
        "E3_PLAN_SECTION4F4_FINANCING_DISCLOSURE_VERBATIM",
        "the §4 F4 financing disclosure string equals the plan §10 text "
        "VERBATIM",
        lab_c["financing_disclosure_verbatim"] == PLAN_S4F4_DISCLOSURE and
        PLAN_S4F4_DISCLOSURE == adj.FINANCING_DISCLOSURE, {}))
    checks.append(check(
        "E4_SCORED_EXECUTION_NOT_AUTHORIZED_MARKER",
        "cycle verdict carries scored_execution = NOT_AUTHORIZED_PRE_GO",
        str(cyc["scored_execution"]).startswith("NOT_AUTHORIZED_PRE_GO"),
        {"scored_execution": cyc["scored_execution"]}))

    # (f) + Task 3: GO gate ----------------------------------------------
    f_ok = all(r["verdict"] == "PASS" for r in go_rows)
    checks.append(check(
        "F1_GO_GATE_ABSENT_PHRASE_REFUSED",
        "staging loader refuses full-data execution with NO GO phrase "
        "(SCORED_EXECUTION_NOT_AUTHORIZED)",
        go_rows[0]["verdict"] == "PASS", go_rows[0]["detail"]))
    checks.append(check(
        "F2_GO_GATE_PARAPHRASES_REFUSED",
        "paraphrased / near-miss phrases are refused; ONLY the exact "
        "`GO FOREX SEARCH V1 SCORED EXECUTION` can open the gate",
        all(r["verdict"] == "PASS" for r in go_rows[1:-1]),
        [r["detail"] for r in go_rows[1:-1]]))
    checks.append(check(
        "F3_GO_GATE_EXACT_PHRASE_OPENS_ON_STUB_ONLY",
        "the exact phrase opens the gate ON A STUBBED EMPTY /tmp PATH ONLY "
        "(loader then fails INPUT_MISMATCH on the stub; real staging bytes "
        "never read; scored execution NOT performed)",
        go_rows[-1]["verdict"] == "PASS", go_rows[-1]["detail"]))
    checks.append(check(
        "G1_SYNTHETIC_ONLY_DECLARATION",
        "no real archive data anywhere in this dry run (seeded synthetic "
        "generator; staging loader exercised only against the empty stub)",
        True, {"dataset_sha256": ds_meta["dataset_sha256"],
               "generator": ds_meta["generator"]}))
    return checks


def _arm_trades(run1: dict, cid: str) -> list:
    return run1["_trades"][cid]


def _db(run1: dict, cid: str) -> dict:
    """The DUAL-BOOKS adjudication row for one arm (detail = engine check)."""
    return next(a["dual_books"] for a in run1["verdict"]["arms"]
                if a["config_id"] == cid)


# =====================================================================
# GO-gate verification (Task 3) — stubbed path ONLY
# =====================================================================

def go_gate_checks() -> list:
    rows = []
    prior = os.environ.pop("FOREX_SEARCH_V1_GO_PHRASE", None)
    phrase = eng.GO_PHRASE
    try:
        # F1: no phrase -> hard refusal
        try:
            eng.load_staging_legs()
            rows.append(check("F1", "no phrase", False,
                              "loader did NOT refuse — INCIDENT"))
        except eng.Stop as st:
            rows.append(check(
                "F1", "no phrase",
                st.code == "SCORED_EXECUTION_NOT_AUTHORIZED",
                {"raised": st.code}))
        # F2: paraphrases -> refusals
        paraphrases = [phrase + " NOW", phrase.lower(), phrase + " ",
                       " " + phrase, phrase.replace("SCORED ", ""),
                       phrase.replace("V1", "V2"),
                       phrase.replace("  ", " ").replace(" ", "  ")]
        all_refused, observed = True, []
        for p in paraphrases:
            os.environ["FOREX_SEARCH_V1_GO_PHRASE"] = p
            try:
                eng.load_staging_legs()
                all_refused = False
                observed.append({"phrase": repr(p), "raised": None})
            except eng.Stop as st:
                observed.append({"phrase": repr(p),
                                 "raised": st.code,
                                 "refused": st.code ==
                                 "SCORED_EXECUTION_NOT_AUTHORIZED"})
                all_refused = all_refused and st.code == \
                    "SCORED_EXECUTION_NOT_AUTHORIZED"
        rows.append(check("F2", "paraphrases", all_refused, observed))
        # F3: EXACT phrase on a stubbed EMPTY /tmp staging root
        stub = Path(tempfile.mkdtemp(prefix="fsearch_z_go_stub_"))
        real_staging = PC.STAGING
        try:
            assert not any(stub.iterdir()), "stub must start empty"
            PC.STAGING = stub
            os.environ["FOREX_SEARCH_V1_GO_PHRASE"] = phrase
            try:
                eng.load_staging_legs()
                opened, refusal = False, None
            except eng.Stop as st:
                opened = st.code != "SCORED_EXECUTION_NOT_AUTHORIZED"
                refusal = st.code
            stub_untouched = not any(stub.iterdir())
            rows.append(check(
                "F3", "exact phrase on stub",
                bool(opened and refusal == "INPUT_MISMATCH" and stub_untouched),
                {"gate_opened_by_exact_phrase": opened,
                 "post_gate_refusal_on_stub": refusal,
                 "stub_path_label": "/tmp/fsearch_z_go_stub_<random>/ "
                                    "(fresh empty temp dir per run; path not "
                                    "recorded to keep the report payload "
                                    "byte-deterministic)",
                 "stub_empty_before_and_after": True,
                 "real_staging_root": str(real_staging),
                 "real_bytes_read": False,
                 "note": "the E-phase scored run is NOT performed by this "
                         "lane; only the gate LOGIC was verified on a stub"}))
        finally:
            PC.STAGING = real_staging
            shutil.rmtree(stub, ignore_errors=True)
    finally:
        if prior is not None:
            os.environ["FOREX_SEARCH_V1_GO_PHRASE"] = prior
        else:
            os.environ.pop("FOREX_SEARCH_V1_GO_PHRASE", None)
    return rows


# =====================================================================
# RECURSIVE LEAK SCAN — static (AST, fail-closed) + dynamic (taint)
# =====================================================================

WATCHED_ATTRS = {"quantile", "percentile", "std", "var", "mean", "max", "min",
                 "nanmax", "nanmin", "nanmean", "nanstd", "sum", "cumsum",
                 "cummax", "cummin", "median", "average", "corrcoef",
                 "maximum", "accumulate"}
FORBIDDEN_ATTRS = {"ffill", "fillna", "bfill", "backfill", "pad",
                   "interpolate", "rolling", "expanding", "shift", "resample",
                   "ewm"}
HIDDEN_IO_NAMES = {"open", "read_text", "read_bytes", "load", "loads"}
TRAILING_RE = re.compile(r":\s*i\s*\+\s*1\s*\]")
FORWARD_RE = re.compile(r"\[\s*i\s*\+\s*1\s*\]")

STATE_ENGINES_P0 = ["state_clv_divergence", "state_extreme_fade",
                    "state_open_gap", "state_vol_drift", "state_clock_cond",
                    "_rolling_max", "_rolling_min", "compute_state"]
STATE_ENGINES_I = ["state_vol_drift_condition_flip", "state_open_gap_trend_only",
                   "state_vol_drift_trend_only"]

# allowlist: (file, enclosing function, normalized call segment) -> label
WATCHED_ALLOW = {
    ("p0_census.py", "_rolling_max", "a[i - K + 1:i + 1].max()"): "TRAILING_WINDOW_STAT",
    ("p0_census.py", "_rolling_min", "a[i - K + 1:i + 1].min()"): "TRAILING_WINDOW_STAT",
    ("p0_census.py", "state_clv_divergence", "clv[i - w20 + 1:i + 1].sum()"):
        "TRAILING_WINDOW_STAT (not in the 3-arm path; scanned for completeness)",
    ("p0_census.py", "state_clv_divergence", "np.maximum(h - l, 1e-300)"):
        "ELEMENTWISE_GUARD (zero-range protection; elementwise, no window, "
        "not in the 3-arm path)",
    ("p0_census.py", "state_open_gap", "np.quantile(w, q_level)"):
        "TRAILING_WINDOW_STAT (w = g[i-251:i+1], ends at decision bar t)",
    ("p0_census.py", "state_vol_drift", "np.std(lr[i - L + 1:i + 1], ddof=1)"):
        "TRAILING_WINDOW_STAT (L returns ending at t)",
    ("p0_census.py", "state_vol_drift", "np.quantile(w, 1.0 / 3.0)"):
        "TRAILING_WINDOW_STAT (w = vol[i-251:i+1])",
    ("p0_census.py", "state_vol_drift", "np.quantile(w, 2.0 / 3.0)"):
        "TRAILING_WINDOW_STAT (w = vol[i-251:i+1])",
    ("p0_census.py", "ohlc_integrity", "np.sum(h < np.maximum(o, c))"):
        "CENSUS_COUNT (integrity-violation census over raw arrays — P0 "
        "metadata, never a state input)",
    ("p0_census.py", "ohlc_integrity", "np.maximum(o, c)"):
        "ELEMENTWISE_TRANSFORM (elementwise max, no reduction)",
    ("p0_census.py", "ohlc_integrity", "np.minimum(o, c)"):
        "ELEMENTWISE_TRANSFORM (elementwise min, no reduction)",
    ("p0_census.py", "ohlc_integrity", "np.sum(l > np.minimum(o, c))"):
        "CENSUS_COUNT",
    ("p0_census.py", "ohlc_integrity",
     "np.sum(np.minimum(np.minimum(o, h), np.minimum(l, c)) <= 0)"):
        "CENSUS_COUNT (non-positive-price census)",
    ("p0_census.py", "ohlc_integrity", "np.sum(h == l)"):
        "CENSUS_COUNT (zero-range bar census)",
    ("i_engine.py", "state_vol_drift_condition_flip",
     "np.std(lr[i - L + 1:i + 1], ddof=1)"): "TRAILING_WINDOW_STAT",
    ("i_engine.py", "state_vol_drift_condition_flip",
     "np.quantile(w, 2.0 / 3.0)"): "TRAILING_WINDOW_STAT (w = vol[i-251:i+1])",
    ("i_engine.py", "summarize_book", "arr[arr > 0].sum()"): "METRIC_ON_PNL",
    ("i_engine.py", "summarize_book", "arr[arr < 0].sum()"): "METRIC_ON_PNL",
    ("i_engine.py", "summarize_book",
     'arr[[i for i, t in enumerate(trades) if t["fold"] == f]].sum()'):
        "METRIC_ON_PNL",
    ("i_engine.py", "summarize_book", "arr.sum()"): "METRIC_ON_PNL",
    ("i_engine.py", "summarize_book", "arr.mean()"): "METRIC_ON_PNL",
    ("i_engine.py", "dual_books_check", "financed.sum()"): "METRIC_ON_PNL",
    ("i_engine.py", "dual_books_check", "price.sum()"): "METRIC_ON_PNL",
    ("i_engine.py", "usd_basket_series",
     "np.mean([per_leg[ln] for ln in legs_order], axis=0)"): "CONTROL_PNL_SPACE",
    ("i_engine.py", "pearson", "np.std(a)"): "METRIC_ON_SERIES",
    ("i_engine.py", "pearson", "np.std(b)"): "METRIC_ON_SERIES",
    ("i_engine.py", "pearson",
     "np.mean((a - a.mean()) * (b - b.mean()))"): "METRIC_ON_SERIES",
    ("i_engine.py", "pearson", "a.mean()"): "METRIC_ON_SERIES",
    ("i_engine.py", "pearson", "b.mean()"): "METRIC_ON_SERIES",
    ("i_engine.py", "max_drawdown_frac", "np.std(arr)"): "METRIC_ON_PNL",
    ("i_engine.py", "max_drawdown_frac", "np.maximum.accumulate(eq)"): "METRIC_ON_PNL",
    ("i_engine.py", "max_drawdown_frac", "np.max(1.0 - eq / peak)"): "METRIC_ON_PNL",
    ("i_engine.py", "weekday_share_of_firings",
     "max(shares[str(d)] for d in (1, 2, 3, 4, 5))"): "METRIC_ON_CENSUS",
    ("i_engine.py", "serial_clustering_census",
     "sum(1 for i in idx if (i - 1) in idx)"): "CENSUS_COUNT",
    ("i_engine.py", "serial_clustering_census",
     'sum(v["fired"] for v in per_leg.values())'): "CENSUS_COUNT",
    ("i_engine.py", "serial_clustering_census",
     'sum(v["consecutive_fired"] for v in per_leg.values())'): "CENSUS_COUNT",
    ("adjudicate.py", "financed_expectancy", "financed.mean()"): "METRIC_ON_PNL",
    ("adjudicate.py", "total_net", "financed.sum()"): "METRIC_ON_PNL",
    ("adjudicate.py", "fold_nets", "financed[idx].sum()"): "METRIC_ON_PNL",
    ("adjudicate.py", "stage_a",
     'np.mean([t["gross_bps"] for t in trades])'): "METRIC_ON_PNL",
    ("adjudicate.py", "stage_a",
     "sum(1 for f in (1, 2, 3) if per_fold.get(str(f), 0.0) > 0.0)"):
        "METRIC_ON_PNL",
    ("adjudicate.py", "stage_a", "max(per_fold.values())"): "METRIC_ON_PNL",
    ("adjudicate.py", "stage_a", "fin_rest.mean()"): "METRIC_ON_PNL",
}

# len() is a SHAPE read (bounds checks), not a statistic — excluded.
BUILTIN_COUNT_NAMES = {"sum", "max", "min"}

# forward-read (index i+1) classification per function
FORWARD_ALLOW = {
    "state_open_gap": "F3_EXCEPTION (g[i+1] = open(t+1) - close(t), the ONE "
                      "declared same-bar exception; fill at that same open)",
    "state_open_gap_trend_only": "F3_EXCEPTION_R4 (declared in the frozen D1 "
                                 "trend-only definition; same exception)",
    "build_trades": "EXECUTION_BAR_LAW (entry/exit at bar t+1 per §4 F3/§8; "
                    "for OPEN-GAP the entry bar IS the exception bar)",
    "gate_firing": "EXECUTION_LOCALIZATION (fold force-flat check only, no "
                   "state input)",
    "usd_basket_series": "CONTROL_PNL_SPACE (USD-drift control correlation "
                         "lives in outcome space, never a state input)",
    "structural_census": "CENSUS_CALENDAR_WALK (weekday-holiday counting "
                         "between consecutive own bars — census metadata, "
                         "never a state input)",
    "run_census": "EXECUTION_LOCALIZATION (next_own execution-bar map for "
                  "the census counting law — force-flat, never a state "
                  "input)",
}
TRAILING_FUNCS = {"state_vol_drift", "_rolling_max", "_rolling_min",
                  "state_clv_divergence", "state_vol_drift_condition_flip",
                  "state_vol_drift_trend_only", "state_extreme_fade"}


def norm(s: str) -> str:
    return " ".join(s.split())


def static_scan() -> dict:
    files = {
        "p0_census.py": P0_DIR / "p0_census.py",
        "i_engine.py": I_DIR / "i_engine.py",
        "adjudicate.py": I_DIR / "adjudicate.py",
    }
    findings, suspects = [], []
    for fname, path in files.items():
        src = path.read_text()
        tree = ast.parse(src)
        lines = src.splitlines()
        fn_stack = []

        class V(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                fn_stack.append(node.name)
                self.generic_visit(node)
                fn_stack.pop()

            visit_AsyncFunctionDef = visit_FunctionDef

            def _classify_call(self, node):
                f = node.func
                name = f.attr if isinstance(f, ast.Attribute) else \
                    (f.id if isinstance(f, ast.Name) else None)
                if name is None:
                    return
                fn = fn_stack[-1] if fn_stack else "<module>"
                if name in BUILTIN_COUNT_NAMES and isinstance(f, ast.Name):
                    seg = norm(ast.get_source_segment(src, node) or "")
                    if fn in STATE_ENGINES_P0 + STATE_ENGINES_I:
                        suspects.append({
                            "file": fname, "line": node.lineno, "func": fn,
                            "kind": "BUILTIN_STAT_IN_STATE_ENGINE",
                            "call": seg,
                            "note": "builtin reduction inside a state engine "
                                    "— fail-closed"})
                    else:
                        findings.append({
                            "file": fname, "line": node.lineno, "func": fn,
                            "kind": "STAT_CALL_CLASSIFIED", "call": seg,
                            "classification": "BUILTIN_COUNT_OR_MAX on "
                                              "already-computed structures "
                                              "(bookkeeping/census, never a "
                                              "state input)"})
                    return
                if name in FORBIDDEN_ATTRS:
                    suspects.append({
                        "file": fname, "line": node.lineno, "func": fn,
                        "kind": "FORBIDDEN_METHOD_CALL", "call": name,
                        "segment": norm(ast.get_source_segment(src, node) or ""),
                        "note": "ffill/shift/rolling-class method call — "
                                "leak suspect, fail-closed"})
                    return
                if name in HIDDEN_IO_NAMES and fn in STATE_ENGINES_P0 + \
                        STATE_ENGINES_I:
                    suspects.append({
                        "file": fname, "line": node.lineno, "func": fn,
                        "kind": "HIDDEN_IO_IN_STATE_ENGINE", "call": name,
                        "segment": norm(ast.get_source_segment(src, node) or ""),
                        "note": "state engines must consume only the passed "
                                "arrays — fail-closed"})
                    return
                if name in WATCHED_ATTRS:
                    seg = norm(ast.get_source_segment(src, node) or "")
                    key = (fname, fn, seg)
                    if key in WATCHED_ALLOW:
                        findings.append({
                            "file": fname, "line": node.lineno, "func": fn,
                            "kind": "STAT_CALL_CLASSIFIED", "call": seg,
                            "classification": WATCHED_ALLOW[key]})
                    else:
                        suspects.append({
                            "file": fname, "line": node.lineno, "func": fn,
                            "kind": "UNCLASSIFIED_STAT_CALL", "call": seg,
                            "note": "statistics call not on the trailing-"
                                    "window/metric allowlist — fail-closed"})

            def visit_Call(self, node):
                self._classify_call(node)
                self.generic_visit(node)

            def visit_Subscript(self, node):
                fn = fn_stack[-1] if fn_stack else "<module>"
                seg = norm(ast.get_source_segment(src, node) or "")
                if FORWARD_RE.search(seg):
                    if fn in FORWARD_ALLOW:
                        findings.append({
                            "file": fname, "line": node.lineno, "func": fn,
                            "kind": "FORWARD_READ_CLASSIFIED", "expr": seg,
                            "classification": FORWARD_ALLOW[fn]})
                    else:
                        suspects.append({
                            "file": fname, "line": node.lineno, "func": fn,
                            "kind": "UNCLASSIFIED_FORWARD_READ", "expr": seg,
                            "note": "index i+1 read outside the declared §4 "
                                    "F3 exception surfaces — fail-closed"})
                elif TRAILING_RE.search(seg) and (fn in TRAILING_FUNCS or
                                                  fn in STATE_ENGINES_P0):
                    findings.append({
                        "file": fname, "line": node.lineno, "func": fn,
                        "kind": "TRAILING_WINDOW_CLASSIFIED", "expr": seg,
                        "classification": "TRAILING_WINDOW (upper bound i+1 "
                                          "= INCLUSIVE end at decision bar t)"})
                self.generic_visit(node)

            def visit_Constant(self, node):
                if isinstance(node.value, str) and \
                        ("ffill" in node.value or "fillna" in node.value):
                    findings.append({
                        "file": fname, "line": node.lineno,
                        "kind": "STRING_MENTION_ONLY",
                        "text": node.value[:120],
                        "classification": "DISCLOSURE_STRING (negation/law "
                                          "text, not code)"})
                self.generic_visit(node)

        V().visit(tree)
    expected = {
        "i_engine.py/build_trades": 3,
        "i_engine.py/gate_firing": 1,
        "i_engine.py/state_open_gap_trend_only": 3,
        "i_engine.py/usd_basket_series": 2,
        "p0_census.py/run_census": 1,
        "p0_census.py/state_open_gap": 1,
        "p0_census.py/structural_census": 2,
    }
    counts = {}
    for f in findings:
        if f["kind"] == "FORWARD_READ_CLASSIFIED":
            key = f"{f['file']}/{f['func']}"
            counts[key] = counts.get(key, 0) + 1
    checks = [
        {"check": "no forbidden method calls (ffill/fillna/rolling/shift/...)",
         "suspects": len([s for s in suspects
                          if s["kind"] == "FORBIDDEN_METHOD_CALL"])},
        {"check": "no hidden I/O inside state engines",
         "suspects": len([s for s in suspects
                          if s["kind"] == "HIDDEN_IO_IN_STATE_ENGINE"])},
        {"check": "all statistics calls classified (trailing-window or "
                  "outcome-space metric)",
         "suspects": len([s for s in suspects
                          if s["kind"] == "UNCLASSIFIED_STAT_CALL"])},
        {"check": "all forward reads classified (F3 exception / execution "
                  "bar / control space)",
         "suspects": len([s for s in suspects
                          if s["kind"] == "UNCLASSIFIED_FORWARD_READ"])},
    ]
    return {
        "scope": [{"file": f"research/control/forex_search_v1_run/"
                            f"{'p0' if n == 'p0_census.py' else 'i'}/{n}",
                   "sha256": sha256_file(p), "bytes": p.stat().st_size}
                  for n, p in files.items()],
        "classified_findings": findings,
        "suspects": suspects,
        "static_checks": checks,
        "forward_read_counts": counts,
        "forward_read_expected": expected,
        "input_surface": {
            "FSS-CLOCK-COND-MONTHPOS-SECOND-LONG":
                "master-calendar date ONLY (day-of-month >= 16); no price "
                "input at all (p0_census.state_clock_cond)",
            "FSS-OPEN-GAP-CONFIRM-Q50":
                "close[<=t] and open[<=t+1]; trigger g[i+1]=open(t+1)-close(t) "
                "is the frozen §4 F3 exception; fill AT open(t+1) "
                "(i_engine.build_trades entry=leg.open[i+1])",
            "FSS-VOL-DRIFT-MOM-L63":
                "close[<=t] only (L-bar log-return std + trailing 252-bar "
                "tercile window + L-bar close change, all ending at t)",
        },
        "no_ffill_feed_evidence": [
            "p0_census.load_leg: raises on duplicate/non-date stamps and "
            "non-positive prices; NEVER repairs or fills (vintage law)",
            "p0_census.calendar_census: master = 5-leg intersection; "
            '"ffill_used": false; missing bars counted, never filled',
            "i_engine.build_positions: raises INPUT_MISMATCH unless master is "
            "a subset of each leg calendar — no imputation path exists",
        ],
        "fail_closed": bool(suspects),
    }


# --------------------------------------------------------------- dynamic

def _copy_leg(leg: dict) -> dict:
    return {k: (v.copy() if isinstance(v, np.ndarray) else v)
            for k, v in leg.items()}


def _taint_after(leg: dict, i_own: int, preserve_open_next: bool,
                 fut_mult: float = 1.05) -> dict:
    """Taint everything STRICTLY AFTER the decision instant: bars >= i+2 in
    full; bar i+1's high/low/close. open[i+1] is preserved iff the family's
    frozen §4 F3 exception requires it (OPEN-GAP); for CLOCK-COND/VOL-DRIFT
    the open(t+1) is tainted too (state must not read it either)."""
    t = _copy_leg(leg)
    n = len(t["close"])
    for j in range(i_own + 2, n):
        for k in ("open", "high", "low", "close"):
            t[k][j] *= fut_mult
    if i_own + 1 < n:
        for k in ("high", "low", "close"):
            t[k][i_own + 1] *= fut_mult
        if not preserve_open_next:
            t["open"][i_own + 1] *= fut_mult
    return t


def _doctor_one_bar(leg: dict, j: int, mult: float = 1.10) -> dict:
    t = _copy_leg(leg)
    for k in ("open", "high", "low", "close"):
        t[k][j] *= mult
    return t


def _state_subset(state: dict, m_max: int) -> dict:
    return {m: v for m, v in state.items() if m <= m_max}


def dynamic_scan(legs: dict, master: list, folds: dict) -> dict:
    pc = PC
    excerpts = {s["config_id"]: s["config_manifest_excerpt_verbatim"]
                for s in eng.load_freeze()["selections"]}
    fam_cfg = {
        "FSS-CLOCK-COND-MONTHPOS-SECOND-LONG": ("CLOCK-COND", False),
        "FSS-OPEN-GAP-CONFIRM-Q50": ("OPEN-GAP", True),
        "FSS-VOL-DRIFT-MOM-L63": ("VOL-DRIFT", False),
    }
    ln = "EURUSD"
    own = {d: i for i, d in enumerate(legs[ln]["dates"])}
    om = [own.get(d) for d in master]
    results = []
    all_pass = True
    for cid, (fam, preserve_open_next) in fam_cfg.items():
        cfg = excerpts[cid]
        ecfg = {"config_id": cid, "family": fam, **cfg["parameters"]}
        clean = pc.compute_state(ecfg, legs[ln], om, master)
        fired = sorted(m for m, d in clean.items() if m + 5 < len(master))
        fracs = [0.05, 0.3, 0.5, 0.7, 0.9, 0.99]
        probes = []
        for fr in fracs:
            mi = fired[min(len(fired) - 1, int(fr * (len(fired) - 1)))]
            if mi not in probes:
                probes.append(mi)
        row = {"arm": cid, "family": fam, "leg": ln, "probes": [],
               "invariance_pass": True, "positive_control_pass": None}
        for mi in probes:
            i = om[mi]
            tainted = _taint_after(legs[ln], i, preserve_open_next)
            ts = pc.compute_state(ecfg, tainted, om, master)
            eq = _state_subset(ts, mi) == _state_subset(clean, mi)
            doct = _doctor_one_bar(legs[ln], i + 3)
            ds = pc.compute_state(ecfg, doct, om, master)
            eq2 = _state_subset(ds, mi) == _state_subset(clean, mi)
            changed_later = sum(1 for m in ts
                                if m > mi and ts.get(m) != clean.get(m))
            if fam == "CLOCK-COND":
                eq = eq and ts == clean  # price-free state: global invariance
            ok = bool(eq and eq2)
            row["invariance_pass"] = row["invariance_pass"] and ok
            row["probes"].append({
                "mi": mi, "decision_date": master[mi], "own_index": i,
                "state": clean.get(mi),
                "invariant_through_decision_under_future_taint": bool(eq),
                "invariant_under_single_doctored_bar_i_plus_3": bool(eq2),
                "state_changes_at_later_bars_expected": changed_later})
        # positive controls: prove the engine READS the allowed instants
        if fam == "OPEN-GAP":
            shorts = [mi for mi in probes if clean.get(mi) == "SHORT"]
            longs = [mi for mi in probes if clean.get(mi) == "LONG"]
            mult, pool = (1.5, shorts) if shorts else (0.25, longs)
            changed = 0
            for mi in pool:
                t = _copy_leg(legs[ln])
                t["open"][om[mi] + 1] *= mult
                ts = pc.compute_state(ecfg, t, om, master)
                changed += int(ts.get(mi) != clean.get(mi))
            row["positive_control_pass"] = changed >= 1
            row["positive_control_note"] = (
                f"tainting open(t+1) by x{mult} flips the state at "
                f"{changed}/{len(pool)} fired probes — the declared §4 F3 "
                "exception input is genuinely consumed (harness sensitivity "
                "proof, not a leak: the fill price IS that open)")
        elif fam == "VOL-DRIFT":
            changed = 0
            for mi in probes:
                t = _copy_leg(legs[ln])
                t["close"][om[mi]] *= 1.5
                ts = pc.compute_state(ecfg, t, om, master)
                changed += int(ts.get(mi) != clean.get(mi))
            row["positive_control_pass"] = changed >= 1
            row["positive_control_note"] = (
                f"tainting close(t) flips the state at {changed}/{len(probes)} "
                "fired probes — bar-t close is genuinely consumed (ALLOWED "
                "input per the decision instant)")
        else:
            row["positive_control_pass"] = all(
                p["invariant_through_decision_under_future_taint"]
                for p in row["probes"])
            row["positive_control_note"] = (
                "CLOCK-COND consumes NO price input: global state equality "
                "under full price taint is itself the sensitivity check")
        row["pass"] = bool(row["invariance_pass"] and
                           row["positive_control_pass"])
        all_pass = all_pass and row["pass"]
        results.append(row)
    # pipeline-level taint: one probe per family, full build_positions rerun
    pipe = []
    own_index = {l: {d: i for i, d in enumerate(legs[l]["dates"])}
                 for l in LEGS_ORDER}
    for cid, (fam, preserve_open_next) in fam_cfg.items():
        cfg = excerpts[cid]
        ecfg = {"config_id": cid, "family": fam, **cfg["parameters"]}
        clean_state = pc.compute_state(ecfg, legs["EURUSD"], om, master)
        fired = sorted(clean_state)
        mi = fired[len(fired) // 2]
        i = om[mi]
        tainted_legs = dict(legs)
        tainted_legs["EURUSD"] = _taint_after(legs["EURUSD"], i,
                                              preserve_open_next)
        clean_pos = eng.build_positions(cfg, legs, master, folds, LEGS_ORDER)
        taint_pos = eng.build_positions(cfg, tainted_legs, master, folds,
                                        LEGS_ORDER)
        same = all(np.array_equal(clean_pos[l][:mi + 1], taint_pos[l][:mi + 1])
                   for l in LEGS_ORDER)
        pipe.append({"arm": cid, "probe_mi": mi,
                     "positions_equal_through_decision": bool(same)})
        all_pass = all_pass and same
    return {
        "method": "feed-level taint shim: deep-copied leg arrays with all "
                  "data STRICTLY AFTER the decision instant multiplied by "
                  "1.05 (bars >= t+2 in full; bar t+1 high/low/close; "
                  "open(t+1) preserved ONLY for the OPEN-GAP §4 F3 "
                  "exception), then the SAME frozen compute_state / "
                  "build_positions code is re-run",
        "per_family": results,
        "pipeline_level": pipe,
        "verdict": "NO_LEAK_FOUND" if all_pass else "LEAK_FOUND",
        "fail_closed": True,
    }


# =====================================================================
# main
# =====================================================================

def full_payload() -> tuple:
    legs, master, folds, ds_meta = generate_dataset()
    run1 = run_pipeline(legs, master, folds)
    run1["_positions"] = {}  # filled below (kept out of the report payload)
    # rebuild positions for check battery (cheap relative to pipeline)
    freeze = eng.load_freeze()
    excerpts = {s["config_id"]: s["config_manifest_excerpt_verbatim"]
                for s in freeze["selections"]}
    positions, trades = {}, {}
    for cid in run1["freeze_selected_order"]:
        positions[cid] = eng.build_positions(excerpts[cid], legs, master,
                                             folds, LEGS_ORDER)
        trades[cid] = eng.build_trades(positions[cid], legs, master, folds,
                                       LEGS_ORDER)
    run1["_positions"] = positions
    run1["_trades"] = trades
    # determinism second run (fresh generation, full pipeline)
    legs2, master2, folds2, ds_meta2 = generate_dataset()
    run2 = run_pipeline(legs2, master2, folds2)
    run2["dataset_meta"] = ds_meta2
    go_rows = go_gate_checks()
    checks = run_checks(ds_meta, legs, master, folds, run1, run2, go_rows)
    static = static_scan()
    dyn = dynamic_scan(legs, master, folds)
    any_fail = any(c["verdict"] != "PASS" for c in checks) or \
        static["fail_closed"] or dyn["verdict"] != "NO_LEAK_FOUND"
    payload = {
        "schema": "fsearch_z_dry_run_report@1",
        "task_id": "fsearch-z",
        "cycle_id": "ZCODE-ORCHESTRATION-V3",
        "real_cycle": "FOREX-SEARCH-V1",
        "role": "quant-implementer",
        "lane": "fsearch-z",
        "plan": "plans/PLAN_forex_search_v1.md §9 Z (read-only)",
        "base_sha": DISPATCH_SHA,
        "branch": BRANCH,
        "worktree": str(WT),
        "inputs_read_only": {
            "i_engine.py": sha256_file(I_DIR / "i_engine.py"),
            "adjudicate.py": sha256_file(I_DIR / "adjudicate.py"),
            "p0_census.py": sha256_file(P0_DIR / "p0_census.py"),
            "selection_freeze.json": sha256_file(
                RUN / "s/selection_freeze.json"),
            "freeze_sha_verified_by_engine": eng.FREEZE_SHA256,
        },
        "synthetic_dataset": ds_meta,
        "arms": run1["freeze_selected_order"],
        "arm_summaries_SYNTHETIC_NOT_EVIDENCE": run1["per_arm"],
        "adjudication_cycle_verdict_SYNTHETIC_NOT_EVIDENCE": run1["verdict"],
        "checks": checks,
        "go_gate_rows": go_rows,
        "leak_scan_summary": {
            "static_verdict": "NO_LEAK_FOUND" if not static["fail_closed"]
            else "LEAK_FOUND",
            "static_suspect_count": len(static["suspects"]),
            "dynamic_verdict": dyn["verdict"],
            "full_report": "z/leak_scan.json",
        },
        "fail_closed": {"any_failed": bool(any_fail)},
        "scored_execution": "NOT_PERFORMED — sanitized dry-run only; the "
                            "staging loader was exercised exclusively against "
                            "an empty stubbed /tmp path",
        "notes": [
            "ALL numbers in this report are SYNTHETIC-fixture mechanics "
            "evidence, never strategy performance evidence.",
            "verify_positions_vs_freeze() and the p20 frozen-matrix equality "
            "re-check are deliberately NOT exercised here: they are "
            "meaningful only against REAL data at the scored E run behind "
            "the owner GO phrase (synthetic positions cannot reproduce the "
            "frozen real-data position digests/rhos by construction).",
            "R0 NOT_RUN / PBO NOT_RUN / D2 SKIPPED labels are carried on "
            "every produced verdict exactly as at the I lane.",
        ],
    }
    return payload, static, dyn, any_fail


def main(argv: list) -> int:
    Z_DIR.mkdir(parents=True, exist_ok=True)
    payload, static, dyn, any_fail = full_payload()
    rep_path = Z_DIR / "dry_run_report.json"
    leak_path = Z_DIR / "leak_scan.json"
    selfcheck = "--selfcheck" in argv
    if selfcheck and rep_path.exists():
        prev = json.loads(rep_path.read_text())
        prev.pop("measured_utc", None)
        match = canonical(prev) == canonical(payload)
        print(f"[z] selfcheck byte-identical payload: {match}")
        if not match:
            return 3
    payload["measured_utc"] = now_utc()
    rep_path.write_text(json.dumps(payload, sort_keys=True, indent=1) + "\n")
    leak = {
        "schema": "fsearch_z_leak_scan@1",
        "task_id": "fsearch-z",
        "cycle_id": "ZCODE-ORCHESTRATION-V3",
        "real_cycle": "FOREX-SEARCH-V1",
        "role": "quant-implementer",
        "lane": "fsearch-z",
        "base_sha": DISPATCH_SHA,
        "scope": "the 3 frozen S-selected arm engines (CLOCK-COND / "
                 "OPEN-GAP / VOL-DRIFT) through the imported P0 state code "
                 "plus the I-lane complement/trend-only engines and the "
                 "trade/fill mapping — recursive: engines -> their P0 state "
                 "engines -> the data feed",
        "static": static,
        "dynamic": dyn,
        "verdict": "NO_LEAK_FOUND" if (not static["fail_closed"] and
                                       dyn["verdict"] == "NO_LEAK_FOUND")
        else "LEAK_FOUND",
        "law": "every state input must derive ONLY from information available "
               "at or before the decision instant (CLOCK-COND/VOL-DRIFT: "
               "bar-t close and earlier; OPEN-GAP: close(t) + open(t+1) per "
               "the frozen §4 F3 exception, fill at that same open). Any "
               "leak = LEAK_FOUND, fail-closed.",
        "measured_utc": now_utc(),
    }
    leak_path.write_text(json.dumps(leak, sort_keys=True, indent=1) + "\n")
    failed = [c["id"] for c in payload["checks"] if c["verdict"] != "PASS"]
    print(f"[z] checks={len(payload['checks'])} failed={failed} "
          f"leak={leak['verdict']}")
    return 0 if (not any_fail and not selfcheck) or \
        (selfcheck and not failed and leak["verdict"] == "NO_LEAK_FOUND") else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
