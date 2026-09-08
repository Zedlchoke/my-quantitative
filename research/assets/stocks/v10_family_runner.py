"""V10 family runner (A8): SFV10-A4-H1 and SFV10-A5-H1 exactly as frozen in
research/control/stocks_free_v10_run/selection_freeze.json.

Inherits the V9 simulation machinery unchanged (prices, bands via the L-I3
fail-closed kernel, fold sessions, 63+21k decision grid, sector tercile books
with one-decile hysteresis, next-session fills with fill-check, dead-name
exit at last close with the C-rate ceiling, fold force-flat) and swaps the
signal layer for the P0 timing/revision observables.

Signals (frozen specs):
  timing_*  : the filer-period group with the LARGEST first_avail strictly
              before the decision gate, age <= 800 days; ties on first_avail
              average their values (measured convention); exposure = -value
  rev_breadth: per-field max-eff groups with last_avail < gate and age <=
              800; |Q| >= 4 or unpopulated; share of rev_dir == dir_value
  severity  : median rev_mag over down-revised non-null groups in Q;
              empty -> 0.0 (the declared extreme-clean tie mass)

Two-key scored authorization: the exact owner GO phrase AND the V10 launch
environment flag.  dry_run=True keeps the record outcome-blind (no PnL, no
returns, no metrics anywhere).
"""

from __future__ import annotations

import hashlib
import json
import os
import statistics
import sys
from datetime import date
from pathlib import Path

from research.assets.stocks import kernel_band_cost_v9 as kernel
from research.assets.stocks.v9_family_runner import (
    FOLDS,
    GRID_START,
    GRID_STEP,
    CLOCK_DAYS,
    decision_grid,
    fold_sessions,
    load_prices,
    load_universe,
    pct_rank,
    target_book,
    weights_from_book,
)

WORKTREE = Path(__file__).resolve().parents[3]
TIMING_PATH = WORKTREE / ".staging_sec_v10/v10_timing_observables.jsonl"
REVISION_PATH = WORKTREE / ".staging_sec_v10/v10_revision_observables.jsonl"
RECORD_SCHEMA = "stocks_free_v10_run/arm_record@1"
GO_PHRASE = "GO STOCKS V10 SCORED EXECUTION"
LAUNCH_ENV = "STOCKS_V10_LAUNCH_AUTHORIZED"

ARM_SPECS = {
    "SFV10-A4-H1-ANCHOR": {"family": "SFV10-A4-H1", "kind": "timing", "value": "own_z", "direction": "high_long", "warmup_decisions": 0},
    "SFV10-A4-H1-NEIGHBOUR": {"family": "SFV10-A4-H1", "kind": "timing", "value": "cohort_z", "direction": "high_long", "warmup_decisions": 0},
    "SFV10-A4-H1-CONTROL": {"family": "SFV10-A4-H1", "kind": "timing", "value": "first_lag_days", "direction": "high_long", "warmup_decisions": 0},
    "SFV10-A5-H1-ANCHOR": {"family": "SFV10-A5-H1", "kind": "rev_breadth", "value": -1, "direction": "low_long", "warmup_decisions": 0},
    "SFV10-A5-H1-NEIGHBOUR": {"family": "SFV10-A5-H1", "kind": "severity", "value": None, "direction": "low_long", "warmup_decisions": 0},
    "SFV10-A5-H1-CONTROL": {"family": "SFV10-A5-H1", "kind": "rev_breadth", "value": 1, "direction": "low_long", "warmup_decisions": 0},
}

MIN_SECTOR_NAMES = 6
BREADTH_MIN_Q = 4


def scored_authorized(owner_go):
    return (owner_go == GO_PHRASE
            and os.environ.get(LAUNCH_ENV) == "1")


def load_timing_layer(path=None):
    out = {}
    with open(path or TIMING_PATH, buffering=1 << 20) as fh:
        for line in fh:
            r = json.loads(line)
            out.setdefault(r["e"], []).append(
                (r["first_avail"], r["eff"], r["own_z"], r["cohort_z"], r["first_lag_days"]))
    return out


def load_revision_layer(path=None):
    out = {}
    with open(path or REVISION_PATH, buffering=1 << 20) as fh:
        for line in fh:
            r = json.loads(line)
            out.setdefault(r["e"], []).append(r)
    return out


def _days_between(a_iso, b_iso):
    return (date.fromisoformat(a_iso) - date.fromisoformat(b_iso)).days


def sig_timing(rows, decision_date, value):
    """Largest-first_avail group before the gate, age <= 800; ties average;
    exposure = -value (early filers long)."""
    if not rows:
        return None
    best_av = None
    vals = []
    for av, eff, oz, cz, lag in rows:
        if av >= decision_date:
            continue
        if _days_between(decision_date, av) > CLOCK_DAYS:
            continue
        v = {"own_z": oz, "cohort_z": cz, "first_lag_days": lag}[value]
        if v is None:
            continue
        if best_av is None or av > best_av:
            best_av = av
            vals = [v]
        elif av == best_av:
            vals.append(v)
    if not vals:
        return None
    return -(sum(vals) / len(vals))


def _qualifying_q(rev_rows, decision_date):
    """Per-field max-eff groups, last_avail < gate, age <= 800."""
    best = {}
    for r in rev_rows:
        la = r["last_avail"]
        if la >= decision_date:
            continue
        if _days_between(decision_date, la) > CLOCK_DAYS:
            continue
        f = r["f"]
        if f not in best or r["eff"] > best[f]["eff"]:
            best[f] = r
    return list(best.values())


def sig_breadth(rev_rows, decision_date, dir_value):
    q = _qualifying_q(rev_rows, decision_date)
    if len(q) < BREADTH_MIN_Q:
        return None
    return sum(1 for r in q if r["rev_dir"] == dir_value) / len(q)


def sig_severity(rev_rows, decision_date):
    q = _qualifying_q(rev_rows, decision_date)
    if len(q) < BREADTH_MIN_Q:
        return None
    mags = [r["rev_mag"] for r in q if r["rev_dir"] == -1 and r["rev_mag"] is not None]
    if not mags:
        return 0.0
    return statistics.median(mags)


def signal_value(spec, timing_entity, revision_entity, decision_date):
    kind = spec["kind"]
    if kind == "timing":
        return sig_timing(timing_entity or [], decision_date, spec["value"])
    if kind == "rev_breadth":
        return sig_breadth(revision_entity or [], decision_date, spec["value"])
    if kind == "severity":
        return sig_severity(revision_entity or [], decision_date)
    raise ValueError(f"unknown V10 arm kind {kind}")


def run_arm(arm_id, timing_layer, revision_layer, prices, folds, dry_run,
            owner_go=None, universe=None, sectors=None, price_manifest_sha="",
            layer_digest="", code_freeze_sha="", stress=False):
    spec = ARM_SPECS[arm_id]
    if not dry_run and not scored_authorized(owner_go):
        raise SystemExit(
            "SCORED EXECUTION REFUSED: exact owner GO phrase and "
            f"{LAUNCH_ENV}=1 are both required (two-key)")
    sectors = sectors or {}
    cost_mult = 2.0 if stress else 1.0
    global_days = sorted({d for p in prices.values() for d in p["date"]})
    day_pos = {d: i for i, d in enumerate(global_days)}

    held = {}
    prev_exec = {}
    held_band = {}
    records = []
    fold_metrics = {}
    name_contrib = {}
    decision_pnls = []
    void_entry_orders = 0
    terminations = 0
    turnover_total = 0.0

    for fold in folds:
        sess = fold["sessions"]
        grid_dates, grid_idx = decision_grid(sess)
        fold_pnls = []
        last_bands = {}
        last_scored_entry = None
        for gi, d in enumerate(grid_dates):
            is_warmup = gi < spec["warmup_decisions"] and fold["fold_id"] == "S0_FOLD_1"
            if d not in day_pos:
                continue
            gi_global = day_pos[d]
            bands = {}
            elig = {}
            for e, p in prices.items():
                if universe is not None and e not in universe:
                    continue
                i = p["pos"].get(d)
                if i is None or i < 62:
                    continue
                adv = statistics.median(p["dvol"][i - 62: i + 1])
                b = kernel.band_of(adv)
                bands[e] = b
                held_band[e] = b
                if b != "UNTRADABLE" and p["raw"][i] >= 1.00:
                    elig[e] = i
            last_bands = bands
            raw_sig = {}
            for e in elig:
                sig = signal_value(spec, timing_layer.get(e), revision_layer.get(e), d)
                if sig is not None and sig == sig:
                    raw_sig[e] = sig
            populated_frac = (len(raw_sig) / len(elig)) if elig else 0.0
            ranks = pct_rank(raw_sig)
            ranks = {k: (sectors.get(k, ""), v) for k, v in ranks.items()}
            # sector tags come from the timing layer entity keys' cohort tag:
            # the runner receives sectors via the universe mapping below
            book, n_active = target_book(ranks, held, spec["direction"])
            w = weights_from_book(book, sectors)
            fill_d = global_days[gi_global + 1] if gi_global + 1 < len(global_days) else None
            if fill_d is None or fill_d > sess[-1]:
                records.append({
                    "record_id": f"{arm_id}|{fold['fold_id']}|SKIP|{d}",
                    "decision_date": d, "fill_date": fill_d,
                    "fold": fold["fold_id"], "event": "FILL_BEYOND_FOLD_END",
                    "eligible": len(elig), "populated": len(raw_sig),
                    "populated_frac": round(populated_frac, 6),
                    "active_sectors": n_active, "legs": 0,
                    "turnover": 0.0, "cost_bps_paid": 0.0, "warmup": is_warmup,
                })
                continue
            turnover = 0.0
            cost = 0.0
            exec_w = {}
            for n in sorted(set(w) | set(prev_exec)):
                tgt = w.get(n, 0.0)
                old = prev_exec.get(n, 0.0)
                if abs(tgt - old) <= 1e-12:
                    if tgt != 0.0:
                        exec_w[n] = tgt
                    continue
                p = prices.get(n)
                if p is None or p["pos"].get(fill_d) is None:
                    if old != 0.0:
                        raise RuntimeError(
                            f"exit order for {n!r} without a fill-session bar - "
                            "book-state invariant violated")
                    void_entry_orders += 1
                    continue
                dw = tgt - old
                turnover += abs(dw)
                if abs(tgt) < abs(old):
                    cost += kernel.exit_cost_bps(n, dw, bands, cost_mult)
                else:
                    cost += kernel.fill_cost_bps(n, dw, bands, cost_mult)
                if tgt != 0.0:
                    exec_w[n] = tgt
            if not exec_w:
                # every order voided by the fill-check (fill session has a
                # bar for almost no name — union-calendar holiday artifact):
                # the decision is UNFILLABLE, recorded as an event (never a
                # scored zero-leg decision); the previous book and executed
                # weights persist unchanged into the next decision.
                records.append({
                    "record_id": f"{arm_id}|{fold['fold_id']}|D|{d}",
                    "decision_date": d, "fill_date": fill_d,
                    "fold": fold["fold_id"],
                    "event": "DECISION_UNFILLABLE_VOID",
                    "eligible": len(elig), "populated": len(raw_sig),
                    "populated_frac": round(populated_frac, 6),
                    "active_sectors": n_active, "legs": 0,
                    "turnover": 0.0, "cost_bps_paid": 0.0,
                    "warmup": is_warmup, "voided_book_names": len(w),
                })
                continue
            turnover_total += turnover
            end_date = None
            nxt_gi = gi + 1
            if nxt_gi < len(grid_idx) and grid_dates[nxt_gi] in day_pos:
                ng = day_pos[grid_dates[nxt_gi]]
                if ng + 1 < len(global_days):
                    end_date = global_days[ng + 1]
            if end_date is None or end_date > sess[-1]:
                end_date = sess[-1]
            pnl = 0.0
            next_exec = {}
            for n in sorted(exec_w):
                wgt = exec_w[n]
                p = prices[n]
                fi = p["pos"][fill_d]
                ei = p["pos"].get(end_date)
                r_ret = None
                if ei is not None and ei > fi:
                    next_exec[n] = wgt
                    if not dry_run:
                        r_ret = p["adj"][ei] / p["adj"][fi] - 1.0
                else:
                    if not dry_run:
                        li = len(p["adj"]) - 1
                        r_ret = p["adj"][li] / p["adj"][fi] - 1.0
                    xcost = (abs(wgt)
                             * kernel.resolve_exit_band_bps(n, held_band)
                             * cost_mult / 10_000.0)
                    cost += xcost
                    turnover += abs(wgt)
                    turnover_total += abs(wgt)
                    terminations += 1
                if not dry_run:
                    pnl += wgt * r_ret
                    name_contrib[n] = name_contrib.get(n, 0.0) + wgt * r_ret
            pnl -= cost
            decision_pnls.append({
                "d": d, "fill_d": fill_d, "end_d": end_date,
                "fold": fold["fold_id"], "scored": not is_warmup,
            })
            if not dry_run and not is_warmup:
                fold_pnls.append(pnl)
                decision_pnls[-1]["pnl"] = pnl
                last_scored_entry = decision_pnls[-1]
            records.append({
                "record_id": f"{arm_id}|{fold['fold_id']}|D|{d}",
                "decision_date": d, "fill_date": fill_d,
                "fold": fold["fold_id"],
                "eligible": len(elig), "populated": len(raw_sig),
                "populated_frac": round(populated_frac, 6),
                "active_sectors": n_active, "legs": len(exec_w),
                "turnover": round(turnover, 6),
                "cost_bps_paid": round(cost * 1e4, 4),
                "warmup": is_warmup,
            })
            held = book
            prev_exec = next_exec
        if prev_exec:
            close_turnover = sum(abs(x) for x in prev_exec.values())
            close_cost = sum(
                abs(x) * kernel.resolve_exit_band_bps(n, last_bands) * cost_mult / 10_000.0
                for n, x in prev_exec.items())
            turnover_total += close_turnover
            if not dry_run and fold_pnls:
                fold_pnls[-1] -= close_cost
                if last_scored_entry is not None:
                    last_scored_entry["pnl"] = last_scored_entry["pnl"] - close_cost
            records.append({
                "record_id": f"{arm_id}|{fold['fold_id']}|FLAT|{sess[-1]}",
                "decision_date": sess[-1], "fill_date": sess[-1],
                "fold": fold["fold_id"],
                "eligible": 0, "populated": 0, "populated_frac": 0.0,
                "active_sectors": 0, "legs": 0,
                "turnover": round(close_turnover, 6),
                "cost_bps_paid": round(close_cost * 1e4, 4),
                "warmup": False, "event": "FOLD_FORCE_FLAT",
            })
            held = {}
            prev_exec = {}
            held_band = {}
        if not dry_run:
            e_sum = sum(fold_pnls)
            wins = sum(x for x in fold_pnls if x > 0)
            losses = -sum(x for x in fold_pnls if x < 0)
            cum, peak_fold, mdd = 0.0, 0.0, 0.0
            for x in fold_pnls:
                cum += x
                peak_fold = max(peak_fold, cum)
                mdd = max(mdd, peak_fold - cum)
            fold_metrics[fold["fold_id"]] = {
                "decisions": len(fold_pnls), "sum_pnl": round(e_sum, 8),
                "pf": round(wins / losses, 6) if losses > 0 else None,
                "mdd": round(mdd, 8),
            }
    decision_records = [x for x in records if x.get("event") is None]
    record = {
        "schema": RECORD_SCHEMA,
        "hypothesis_id": spec["family"],
        "arm_id": arm_id,
        "family_id": spec["family"],
        "arm_config_digest": hashlib.sha256(
            json.dumps(spec, sort_keys=True).encode()).hexdigest(),
        "data_snapshot_digest": hashlib.sha256(
            (layer_digest + price_manifest_sha).encode()).hexdigest(),
        "code_freeze_sha": code_freeze_sha,
        "dry_run": dry_run,
        "scored": not dry_run,
        "stress": stress,
        "direction": spec["direction"],
        "warmup_decisions": spec["warmup_decisions"],
        "decisions_total": len(decision_records),
        "scored_decisions_total": sum(
            1 for x in decision_records if not x["warmup"]),
        "void_entry_orders": void_entry_orders,
        "terminations": terminations,
        "turnover_two_way_total": round(turnover_total, 6),
        "fold_structure": [
            {k: (len(v) if k == "sessions" else v) for k, v in f.items()}
            for f in folds],
        "schedule": records,
    }
    if not dry_run:
        scored = [x for x in decision_pnls if x["scored"] and "pnl" in x]
        e_sum = sum(x["pnl"] for x in scored)
        wins = sum(x["pnl"] for x in scored if x["pnl"] > 0)
        losses = -sum(x["pnl"] for x in scored if x["pnl"] < 0)
        record["metrics"] = {
            "expectancy": round(e_sum / len(scored), 10) if scored else None,
            "sum_pnl": round(e_sum, 8),
            "pf": round(wins / losses, 6) if losses > 0 else None,
            "folds": fold_metrics,
            "top_name_contribution": (
                max(name_contrib.items(), key=lambda kv: kv[1])
                if name_contrib else None),
            "decision_pnl": [
                {"d": x["d"], "fill_d": x["fill_d"], "end_d": x["end_d"],
                 "fold": x["fold"], "pnl": round(x["pnl"], 10)}
                for x in scored],
        }
    return record
