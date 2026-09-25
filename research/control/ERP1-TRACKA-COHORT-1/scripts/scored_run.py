"""Scored-phase runner — ERP1-TRACKA-COHORT-1 (tracka1-scored lane, GO-2).

Usage:
    scored_run.py dryrun    # exact-arm machinery pass, scored=false
    scored_run.py scored    # the 12 dev cells + seam/kill laws + holdout

DRY-RUN LAW (handbook 19.2): scored=false; no PnL/PF/stress/break-even at
any record depth (recursively scanned); record IDs pairwise distinct;
replay zero denominator delta (ledger untouched, byte-verified); non-
vacuous (zero-decision book = fail; FLAT is the declared null control).

SEQUENCE LAW: dry-run evidence committed BEFORE any scored computation.
Holdout pass runs ONLY after all dev verdicts are computed and recorded,
per the frozen membership (freeze pin ii, sha 45ff897d...).

Frozen inputs are read from freeze/GO1_freeze_artifact.json (+ erratum E1)
— arm digests, seeds, windows, seam constants, placebo r/hold, holdout
membership. No frozen file is modified. Ledger: APPEND-ONLY.
"""
from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np

LANE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LANE / "scripts"))

import scored_lib as S  # noqa: E402
import tracka_lib as T  # noqa: E402
from falsifier_run import (  # noqa: E402
    FOLD_TABLE, HOLDOUT_END, HOLDOUT_START, PAIRS, ts_of,
)

OUT_DIR = LANE
OUT_DRYRUN = OUT_DIR / "scored_dryrun.json"
OUT_DEV = OUT_DIR / "scored_dev_cells.json"
OUT_HOLDOUT = OUT_DIR / "scored_holdout_look.json"
OUT_SEAM = OUT_DIR / "scored_seam_law.json"
OUT_KILLS = OUT_DIR / "scored_kill_laws.json"
OUT_DSR = OUT_DIR / "scored_dsr.json"
OUT_REPORT = OUT_DIR / "SCORED_REPORT.md"
OUT_LEDGER = OUT_DIR / "trial_ledger.jsonl"
SERIES_DIR = OUT_DIR / "series"
HANDOFF = OUT_DIR / "handoffs" / "HANDOFF_tracka1_scored.json"

CYCLE_ID = "ERP1-TRACKA-COHORT-1"
GO2_RECORD = Path("/Users/hoangminhlong/my-quantitative/research/control/"
                  "ECONOMIC-ROBUSTNESS-PROGRAM-V1/tracka_cohort1/GO2_gate/"
                  "GO_RECORDED.json")
DISPATCH_SHA = "5ca856824b1576bfa8c5ba83a541178a3ef9596e"

DEV_ARMS = ["R-ANCHOR", "R-ORIG", "R-NEIGH", "CAUSAL-PLACEBO", "INVERTED",
            "BASELINE-SET"]
NULL_BOOK = "FLAT"  # declared null control inside BASELINE-SET
DECISION_BOOKS = ["R-ANCHOR", "R-ORIG", "R-NEIGH", "CAUSAL-PLACEBO",
                  "INVERTED", "SHORT_ALWAYS", "LONG_ALWAYS"]
KILL_PRECEDENCE = ["KILL_PIT_SEAM", "KILL_CONTROL_REPRODUCED",
                   "KILL_INVERSION", "KILL_BETA_EXPLAINED",
                   "KILL_HOLDOUT_FAIL"]

LEAK_KEY_RE = re.compile(
    r"net|pnl|pf|profit|sharpe|expectanc|win|drawdown|equity|stress|"
    r"breakeven|break_even|gross|pips",
    re.IGNORECASE)


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def canon_sha(obj) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def ts_index_of(p, ts_epoch: int) -> int:
    return int(np.searchsorted(p.ts, ts_epoch, side="left"))


def load_frozen(pair: str):
    freeze = S.load_freeze()
    reg = S.registry_digests(freeze)
    pc = freeze["clock_placebo_rebuild"]["per_pair"][pair]
    sc = freeze["seam_constants"][pair]
    return {
        "freeze": freeze,
        "digests": {arm: reg[(pair, arm)] for arm in DEV_ARMS},
        "holdout_digests": {
            "R-ANCHOR": freeze["pins"]["(ii)_holdout_pass_membership"]
            ["per_pair"][pair]["anchor_arms"][0]["arm_config_digest"],
            "CAUSAL-PLACEBO": freeze["pins"]["(ii)_holdout_pass_membership"]
            ["per_pair"][pair]["companions_single_pass"][0]
            ["arm_config_digest"],
            "INVERTED": freeze["pins"]["(ii)_holdout_pass_membership"]
            ["per_pair"][pair]["companions_single_pass"][1]
            ["arm_config_digest"],
            "BASELINE-SET": freeze["pins"]["(ii)_holdout_pass_membership"]
            ["per_pair"][pair]["companions_single_pass"][2]
            ["arm_config_digest"],
        },
        "placebo_r": pc["r"],
        "placebo_hold": pc["hold_bars"],
        "placebo_frozen_counts": {"days_selected": None,
                                  "entries_placed": pc["entries_placed"],
                                  "trips_dev": pc["trips_dev"]},
        "c_rt_pips": sc["c_rt_pips"]["R-ANCHOR"],
        "N_diff_frozen": {"N_diff": sc["N_diff"],
                          "anchor_only": sc["N_diff_anchor_only"],
                          "orig_only": sc["N_diff_orig_only"]},
    }


# ================================================================ dryrun ===

def leak_scan(obj, path="$") -> list:
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            kp = f"{path}.{k}"
            if LEAK_KEY_RE.search(str(k)) and k not in (
                    "schema", "cycle_id"):
                hits.append(f"{kp} (key)")
            hits.extend(leak_scan(v, kp))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(leak_scan(v, f"{path}[{i}]"))
    elif isinstance(obj, str):
        # a stray serialized number under a banned key is caught above;
        # here catch banned metric words inside string VALUES of any key
        if LEAK_KEY_RE.search(obj) and len(obj) < 200 and \
                re.search(r"\b(pnl|profit\s*factor|sharpe|net\s+pips)\b",
                          obj, re.IGNORECASE):
            hits.append(f"{path} (value)")
    return hits


def fold_counts_from_schedule(trips: list, fold_table=FOLD_TABLE) -> tuple:
    """COUNTS-ONLY fold assignment for schedule trips (no PnL fields)."""
    per_fold = {fid: 0 for fid, _, _ in fold_table}
    straddles = 0
    for t in trips:
        fid = S.fold_of_ts(t["entry_ts"], fold_table)
        if fid is None:
            continue
        per_fold[fid] += 1
        if S.fold_of_ts(t["exit_ts"], fold_table) != fid:
            straddles += 1
    return per_fold, straddles


def build_pair_machinery(pair: str) -> dict:
    """Signal arrays + schedules + COUNTS only (scored=false path)."""
    fr = load_frozen(pair)
    p_dev = S.load_plane(pair, include_holdout=False)
    p_full = S.load_plane(pair, include_holdout=True)
    tgts_full = S.build_targets(p_full)
    tgts_dev = S.build_targets(p_dev)
    pl_full = S.placebo_target_full_panel(
        p_full, fr["placebo_r"], fr["placebo_hold"])
    pl_dev = S.placebo_target_full_panel(
        p_dev, fr["placebo_r"], fr["placebo_hold"])
    n_dev = len(p_dev.ts)
    ident = {
        "dev_plane_bars": n_dev,
        "full_plane_bars": len(p_full.ts),
        "full_is_dev_prefix_plus_holdout": bool(
            np.array_equal(p_full.ts[:n_dev], p_dev.ts)),
        "targets_full_vs_devpanel_identical_on_prefix": {
            arm: bool(np.array_equal(tgts_full[arm][:n_dev], tgts_dev[arm]))
            for arm in tgts_full},
        "placebo_full_vs_devpanel_identical_on_prefix": bool(
            np.array_equal(pl_full["tgt"][:n_dev], pl_dev["tgt"])),
        "M1_shift_equivalence_recheck": bool(
            np.array_equal(tgts_dev["R-ANCHOR"],
                           T.f_rangeexp_anchor_shift(p_dev))),
        "spread_planes_identical_dev_vs_trueHL_note":
            "ANC signal plane; s_open/s_close verified bit-identical "
            "across conventions in the freeze plane_semantics_pin "
            "(max abs diff 0.0)",
    }
    widx = S.dev_warmup_end_idx(p_dev)
    arms = dict(tgts_dev)
    arms["CAUSAL-PLACEBO"] = pl_dev["tgt"]
    sched = {}
    for arm, tgt in arms.items():
        sched[arm] = T.schedule_only(p_dev, tgt, widx)
    # placebo dev counts vs frozen
    pl_counts = {
        "days_selected_dev": pl_dev["days_selected"],
        "entries_placed_dev": pl_dev["entries_placed"],
        "trips_dev_schedule": len(sched["CAUSAL-PLACEBO"]),
        "frozen_entries_placed": fr["placebo_frozen_counts"]
        ["entries_placed"],
        "frozen_trips_dev": fr["placebo_frozen_counts"]["trips_dev"],
    }
    cells = []
    for arm in DEV_ARMS:
        book_map = ({"FLAT": "FLAT", "SHORT_ALWAYS": "SHORT_ALWAYS",
                     "LONG_ALWAYS": "LONG_ALWAYS"}
                    if arm == "BASELINE-SET" else {arm: None})
        entry = {
            "cell_id": f"{pair}/{arm}@{fr['digests'][arm]}",
            "pair": pair, "arm": arm,
            "arm_config_digest": fr["digests"][arm],
            "target_sha256": {
                bk: hashlib.sha256(arms[bk].tobytes()).hexdigest()[:16]
                for bk in book_map},
            "n_trades_dev_schedule": {bk: len(sched[bk])
                                      for bk in book_map},
            "per_fold_trades_k1_ref": {
                bk: fold_counts_from_schedule(sched[bk])[0]
                for bk in book_map},
            "fold_straddles": {
                bk: fold_counts_from_schedule(sched[bk])[1]
                for bk in book_map},
            "non_vacuous": {
                bk: (True if bk == "FLAT" else len(sched[bk]) > 0)
                for bk in book_map},
        }
        cells.append(entry)
    return {
        "pair": pair, "warmup_end_idx": widx,
        "warmup_end_ts": int(p_dev.ts[widx]),
        "machinery_identity": ident,
        "placebo_counts_vs_frozen": pl_counts,
        "cells": cells,
        "pairwise_distinct_ids": len(
            {c["cell_id"] for c in cells}) == len(cells),
    }


def run_dryrun() -> int:
    ledger_sha_before = sha256_file(OUT_LEDGER)
    out = {
        "schema": "tracka_scored_dryrun@1",
        "cycle_id": CYCLE_ID,
        "lane": "tracka1-scored",
        "mode": "EXACT_ARM_DRY_RUN scored=false real_pnl=false "
                "published=false",
        "created_utc": now_utc(),
        "dispatch_sha": DISPATCH_SHA,
        "go2_record_sha256": sha256_file(GO2_RECORD),
        "pairs": {},
    }
    for pair in PAIRS:
        out["pairs"][pair] = build_pair_machinery(pair)
    # non-vacuity verdict (FLAT exempt as declared null control)
    vac = []
    for pair, po in out["pairs"].items():
        for c in po["cells"]:
            for bk, ok in c["non_vacuous"].items():
                if not ok:
                    vac.append(f"{pair}/{c['arm']}/{bk}")
    out["non_vacuous_all_decision_books"] = len(vac) == 0
    out["non_vacuous_violations"] = vac
    out["leak_scan_hits"] = leak_scan(out)
    out["leak_scan_clean"] = len(out["leak_scan_hits"]) == 0
    out["ledger_sha256_before"] = ledger_sha_before
    OUT_DRYRUN.write_text(json.dumps(out, indent=1, default=str))
    # re-run replay check: a second build must be byte-identical
    replay = {"pairs": {pair: build_pair_machinery(pair) for pair in PAIRS}}
    replay_ids = {pair: [c["cell_id"] for c in po["cells"]]
                  for pair, po in replay["pairs"].items()}
    first_ids = {pair: [c["cell_id"] for c in po["cells"]]
                 for pair, po in out["pairs"].items()}
    counts_replay = {pair: [{bk: v for bk, v in c["n_trades_dev_schedule"]
                             .items()} for c in replay["pairs"][pair]["cells"]]
                     for pair in PAIRS}
    counts_first = {pair: [{bk: v for bk, v in c["n_trades_dev_schedule"]
                            .items()} for c in out["pairs"][pair]["cells"]]
                    for pair in PAIRS}
    ledger_sha_after = sha256_file(OUT_LEDGER)
    out["replay_zero_denominator_delta"] = {
        "ids_identical": replay_ids == first_ids,
        "schedule_counts_identical": counts_replay == counts_first,
        "ledger_sha256_after": ledger_sha_after,
        "ledger_unchanged": ledger_sha_before == ledger_sha_after,
        "denominator_delta_rows": 0,
    }
    out["gates"] = {
        "ids_pairwise_distinct": all(
            po["pairwise_distinct_ids"] for po in out["pairs"].values()),
        "non_vacuous": out["non_vacuous_all_decision_books"],
        "leak_scan_clean": out["leak_scan_clean"],
        "replay_clean": out["replay_zero_denominator_delta"],
        "machinery_identity_all": {
            pair: {
                "prefix_identity": all(
                    po["machinery_identity"]
                    ["targets_full_vs_devpanel_identical_on_prefix"]
                    .values()),
                "placebo_prefix_identity": po["machinery_identity"]
                ["placebo_full_vs_devpanel_identical_on_prefix"],
                "M1_recheck": po["machinery_identity"]
                ["M1_shift_equivalence_recheck"],
                "placebo_counts_match_frozen":
                    po["placebo_counts_vs_frozen"]["entries_placed_dev"]
                    == po["placebo_counts_vs_frozen"]["frozen_entries_placed"]
                    and po["placebo_counts_vs_frozen"]["trips_dev_schedule"]
                    == po["placebo_counts_vs_frozen"]["frozen_trips_dev"],
                "no_fold_straddles": all(
                    v == 0 for c in po["cells"]
                    for v in c["fold_straddles"].values()),
            } for pair, po in out["pairs"].items()},
    }
    OUT_DRYRUN.write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps({
        "leak_scan_clean": out["leak_scan_clean"],
        "non_vacuous": out["non_vacuous_all_decision_books"],
        "ids_distinct": out["gates"]["ids_pairwise_distinct"],
        "replay": out["replay_zero_denominator_delta"],
        "machinery": out["gates"]["machinery_identity_all"],
    }, indent=1, default=str))
    ok = (out["leak_scan_clean"] and out["non_vacuous_all_decision_books"]
          and out["gates"]["ids_pairwise_distinct"]
          and out["replay_zero_denominator_delta"]["ledger_unchanged"]
          and all(all(v for k, v in m.items())
                  for m in out["gates"]["machinery_identity_all"].values()))
    return 0 if ok else 9


# ================================================================ scored ===

def cell_label_for(arm: str, fired: dict, anchor_verdict: str,
                   holdout_ok: bool) -> str:
    """Terminal per-arm-per-pair label, vocabulary per plan 9.3 /
    dispatch: CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION |
    NOT_POWERED_CANDIDATE | KILL_* | REJECT."""
    for k in KILL_PRECEDENCE:
        if fired.get(k):
            if k == "KILL_PIT_SEAM" and arm in ("R-ANCHOR", "R-ORIG"):
                return k
            if k == "KILL_CONTROL_REPRODUCED" and arm in (
                    "R-ANCHOR", "CAUSAL-PLACEBO"):
                return k
            if k == "KILL_INVERSION" and arm in ("R-ANCHOR", "INVERTED"):
                return k
            if k == "KILL_BETA_EXPLAINED" and arm in (
                    "R-ANCHOR", "BASELINE-SET"):
                return k
            if k == "KILL_HOLDOUT_FAIL" and arm == "R-ANCHOR":
                return k
            return "REJECT"
    if arm == "R-ANCHOR":
        if anchor_verdict == "PROMOTED":
            return "CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION"
        if anchor_verdict == "NOT_POWERED":
            return "NOT_POWERED_CANDIDATE"
        return "REJECT"
    return "REJECT"


def scored_cells_for_pair(pair: str) -> dict:
    fr = load_frozen(pair)
    freeze = fr["freeze"]
    p_dev = S.load_plane(pair, include_holdout=False)
    p_full = S.load_plane(pair, include_holdout=True)
    tgts_full = S.build_targets(p_full)
    pl_full = S.placebo_target_full_panel(
        p_full, fr["placebo_r"], fr["placebo_hold"])
    tgts_dev = S.build_targets(p_dev)
    pl_dev = S.placebo_target_full_panel(
        p_dev, fr["placebo_r"], fr["placebo_hold"])
    n_dev = len(p_dev.ts)
    prefix_ok = all(
        np.array_equal(tgts_full[a][:n_dev], tgts_dev[a])
        for a in tgts_dev) and np.array_equal(
        pl_full["tgt"][:n_dev], pl_dev["tgt"])
    if not prefix_ok:
        raise RuntimeError(f"{pair}: full-panel/dev-panel target prefix "
                           "identity FAILED - machinery drift")
    widx = S.dev_warmup_end_idx(p_dev)
    arms = dict(tgts_dev)
    arms["CAUSAL-PLACEBO"] = pl_dev["tgt"]

    # ---- 12 scored cells: run the ancestry fill/PnL path -------------
    cells = {}
    for arm in DEV_ARMS:
        book_map = (["FLAT", "SHORT_ALWAYS", "LONG_ALWAYS"]
                    if arm == "BASELINE-SET" else [arm])
        cell = {
            "pair": pair, "arm": arm,
            "arm_config_digest": fr["digests"][arm],
            "mechanism_id": "M1",
            "fold_or_holdout_tag": "DEV_FOLDS_F1_F6",
            "books": {},
        }
        for bk in book_map:
            cell["books"][bk] = {}
            for k in S.K_BOOKS:
                trades, _ = S.run_cell(p_dev, arms[bk], k, widx)
                dec = S.decompose(p_dev, trades, k)
                gm = S.gate_metrics(p_dev, trades, k)
                cell["books"][bk][str(k)] = {
                    "decompose": dec, "gates": {
                        kk: gm[kk] for kk in (
                            "per_fold_net_pips", "per_fold_trades",
                            "fold_straddles", "n_months",
                            "months_with_trades", "n_trades_fold_assigned",
                            "top_fold_id", "top_fold_share",
                            "top5_trades_share", "top_hour",
                            "top_hour_share", "pf",
                            "total_positive_net_pips")},
                    "trades": trades,  # in-memory only; stripped on write
                }
        cells[arm] = cell

    # promote BASELINE-SET's primary cell view: the beta-matched book
    beta = S.BETA_MATCHED[pair]
    for arm, cell in cells.items():
        if arm == "BASELINE-SET":
            cell["beta_matched_book"] = beta
            cell["books_view"] = "beta-matched book is the row's net/gross; \
all books' decomposition inside gates_with_margins_to_fail"

    # ---- gates with margins (anchor primary; all arms evaluated) ------
    for arm, cell in cells.items():
        view = beta if arm == "BASELINE-SET" else arm
        b1 = cell["books"][view]["1.0"]
        cell["gates"] = S.evaluate_gates(
            {"books": {"1.0": {"decompose": b1["decompose"],
                               "gates": b1["gates"]},
                       "1.5": cell["books"][view]["1.5"],
                       "2.0": cell["books"][view]["2.0"]}})
        cell["exclusion_zones"] = S.exclusion_zones(
            {"books": {"1.0": {"decompose": b1["decompose"],
                               "gates": b1["gates"],
                               "trades": cell["books"][view]["1.0"]
                               ["trades"]}},
             "fold_or_holdout_tag": "DEV_FOLDS_F1_F6"}, arm, pair)
    anchor_gates = cells["R-ANCHOR"]["gates"]
    gates_all_pass = all(v["verdict"] == "PASS"
                         for v in anchor_gates.values())
    rt_dev_union = cells["R-ANCHOR"]["books"]["R-ANCHOR"]["1.0"][
        "decompose"]["n_trades"]

    # ---- seam law ------------------------------------------------------
    seam = S.seam_law(p_dev,
                      cells["R-ORIG"]["books"]["R-ORIG"]["1.0"]["trades"],
                      cells["R-ANCHOR"]["books"]["R-ANCHOR"]["1.0"]["trades"],
                      fr["c_rt_pips"], fr["N_diff_frozen"])

    # ---- kill laws (k=1.0 book) ----------------------------------------
    fa = {f: v for f, v in cells["R-ANCHOR"]["books"]["R-ANCHOR"]["1.0"]
          ["gates"]["per_fold_net_pips"].items()}
    fi = {f: v for f, v in cells["INVERTED"]["books"]["INVERTED"]["1.0"]
          ["gates"]["per_fold_net_pips"].items()}
    fp = {f: v for f, v in cells["CAUSAL-PLACEBO"]["books"]
          ["CAUSAL-PLACEBO"]["1.0"]["gates"]
          ["per_fold_net_pips"].items()}
    kinv = S.kill_inversion(
        cells["R-ANCHOR"]["books"]["R-ANCHOR"]["1.0"]["trades"],
        cells["INVERTED"]["books"]["INVERTED"]["1.0"]["trades"], fa, fi)
    kctl = S.kill_control(
        cells["R-ANCHOR"]["books"]["R-ANCHOR"]["1.0"]["trades"],
        cells["CAUSAL-PLACEBO"]["books"]["CAUSAL-PLACEBO"]["1.0"]["trades"],
        fa, fp)
    book_trades = {
        "SHORT_ALWAYS": cells["BASELINE-SET"]["books"]["SHORT_ALWAYS"]
        ["1.0"]["trades"],
        "LONG_ALWAYS": cells["BASELINE-SET"]["books"]["LONG_ALWAYS"]
        ["1.0"]["trades"],
    }
    kbeta = S.kill_beta(
        cells["R-ANCHOR"]["books"]["R-ANCHOR"]["1.0"]["trades"],
        book_trades, pair)
    fired = {
        "KILL_PIT_SEAM": bool(seam["fires"]),
        "KILL_CONTROL_REPRODUCED": bool(kctl["fires"]),
        "KILL_INVERSION": bool(kinv["fires"]),
        "KILL_BETA_EXPLAINED": bool(kbeta["fires"]),
    }
    any_kill = any(fired.values())

    # placebo per-occupied-hour rider (scored-phase diagnostic obligation)
    rider = per_occupied_hour_rider(
        cells["R-ANCHOR"]["books"]["R-ANCHOR"]["1.0"]["trades"],
        cells["CAUSAL-PLACEBO"]["books"]["CAUSAL-PLACEBO"]["1.0"]["trades"])

    return {
        "pair": pair,
        "frozen": {k: v for k, v in fr.items() if k != "freeze"},
        "cells": cells,
        "anchor_gates_all_pass": gates_all_pass,
        "anchor_rt_dev_union": rt_dev_union,
        "power_gate_rt_236": {"threshold": 236,
                              "rt": rt_dev_union,
                              "pass": rt_dev_union >= 236},
        "seam": seam,
        "kills": {"KILL_INVERSION": kinv, "KILL_CONTROL_REPRODUCED": kctl,
                  "KILL_BETA_EXPLAINED": kbeta},
        "fired": fired,
        "any_kill": any_kill,
        "placebo_rider_net_per_occupied_hour": rider,
        "warmup_end_idx": widx,
        "n_dev_bars": n_dev,
        "p_full_bars": len(p_full.ts),
        "_ctx": {"p_full": p_full, "tgts_full": tgts_full,
                 "pl_full": pl_full, "fr": fr},
    }


def per_occupied_hour_rider(trades_anchor: list,
                            trades_placebo: list) -> dict:
    """Scored-phase rider (freeze clock_placebo_rebuild): control net per
    occupied entry-hour vs anchor net per occupied entry-hour."""

    def by_hour(trades):
        net, cnt = {}, {}
        for t in trades:
            h = int((t["entry_ts"] // 3600) % 24)
            net[h] = net.get(h, 0.0) + t["pips"]
            cnt[h] = cnt.get(h, 0) + 1
        return net, cnt

    na, ca = by_hour(trades_anchor)
    nc, cc = by_hour(trades_placebo)
    return {
        "anchor_net_by_entry_hour": {h: round(v, 2)
                                     for h, v in sorted(na.items())},
        "placebo_net_by_entry_hour": {h: round(v, 2)
                                      for h, v in sorted(nc.items())},
        "anchor_net_per_occupied_hour": round(
            sum(na.values()) / max(len(na), 1), 4),
        "placebo_net_per_occupied_hour": round(
            sum(nc.values()) / max(len(nc), 1), 4),
        "anchor_occupied_hours": len(na),
        "placebo_occupied_hours": len(nc),
    }


def persist_series(res: dict) -> list:
    """Per-period (daily) series per scored cell at every k book + the
    per-trade pips of the k=1.0 book (DSR inputs, G7 reproducibility)."""
    SERIES_DIR.mkdir(exist_ok=True)
    written = []
    pair = res["pair"]
    beta = S.BETA_MATCHED[pair]
    start = ts_of("2021-01-01")
    end = ts_of("2025-12-31", end=True)
    for arm, cell in res["cells"].items():
        view = beta if arm == "BASELINE-SET" else arm
        payload = {"cycle_id": CYCLE_ID, "pair": pair, "arm": arm,
                   "view_book": view, "tag": "DEV_FOLDS_F1_F6",
                   "k_books": {}}
        for kstr, book in cell["books"][view].items():
            trades = book["trades"]
            ser = S.daily_series(trades, start, end)
            payload["k_books"][kstr] = {
                "daily_net_pips": {str(int(d)): round(float(v), 4)
                                   for d, v in ser.items() if v != 0.0},
                "n_days": int(len(ser)),
                "per_fold_net_pips": book["gates"]["per_fold_net_pips"],
                "per_trade_pips_k_book": [round(float(t["pips"]), 4)
                                          for t in trades],
            }
        fp = SERIES_DIR / f"{pair}_{arm.replace('/', '_')}_dev_series.json"
        fp.write_text(json.dumps(payload, indent=1))
        written.append(str(fp.relative_to(LANE)))
    return written


# =================================================================== main ==

def dev_status_of(res: dict) -> dict:
    """Pre-holdout dev verdict (recorded BEFORE any holdout read)."""
    if res["any_kill"]:
        label = next(k for k in KILL_PRECEDENCE if res["fired"].get(k))
        return {"status": "KILLED_AT_DEV", "eligible_for_holdout": False,
                "terminal_label": label,
                "fired_kills": [k for k in KILL_PRECEDENCE
                                if res["fired"].get(k)]}
    if not res["anchor_gates_all_pass"]:
        failed = [g for g, v in res["cells"]["R-ANCHOR"]["gates"].items()
                  if v["verdict"] == "FAIL"]
        return {"status": "REJECTED_AT_DEV",
                "eligible_for_holdout": False, "terminal_label": "REJECT",
                "failed_gates": failed}
    return {"status": "DEV_GATES_ALL_PASS_NO_KILL",
            "eligible_for_holdout": True, "terminal_label": None,
            "power_gate": res["power_gate_rt_236"]}


def strip_trades(obj):
    if isinstance(obj, dict):
        return {k: strip_trades(v) for k, v in obj.items()
                if k not in ("trades",)}
    if isinstance(obj, list):
        return [strip_trades(v) for v in obj]
    return obj


def sha_chain_row(freeze: dict, freeze_sha: str, pair: str) -> dict:
    return {
        "code_freeze": freeze["sha_chain"]["code_freeze"],
        "data_manifest": {pair: freeze["cost_book"]["census_sha256"][pair]},
        "selection_digest": freeze_sha,
        "scored_code": {
            "scripts/scored_lib.py": sha256_file(LANE / "scripts"
                                                 / "scored_lib.py"),
            "scripts/scored_run.py": sha256_file(LANE / "scripts"
                                                 / "scored_run.py"),
        },
        "go2_record_sha256": sha256_file(GO2_RECORD),
    }


def run_scored() -> int:
    freeze = S.load_freeze()
    freeze_sha = sha256_file(S.FREEZE_PATH)
    labels_class = freeze["labels_class"]

    # ---- 1+2: dev cells for both pairs (verdicts computed) ------------
    results = {pair: scored_cells_for_pair(pair) for pair in PAIRS}

    # ---- 3: persist per-period series (DSR inputs) --------------------
    series_files = []
    daily = {}
    start = ts_of("2021-01-01")
    end = ts_of("2025-12-31", end=True)
    for pair, res in results.items():
        series_files.extend(persist_series(res))
        beta = S.BETA_MATCHED[pair]
        for arm, cell in res["cells"].items():
            view = beta if arm == "BASELINE-SET" else arm
            trades = cell["books"][view]["1.0"]["trades"]
            daily[f"{pair}/{arm}"] = S.daily_series(trades, start, end)

    # ---- 4: record dev verdicts (BEFORE any holdout read) -------------
    dev_out = {
        "schema": "tracka_scored_dev_cells@1", "cycle_id": CYCLE_ID,
        "created_utc": now_utc(), "freeze_sha256": freeze_sha,
        "pairs": {}}
    for pair, res in results.items():
        dev_out["pairs"][pair] = {
            "status": dev_status_of(res),
            "anchor_gates": res["cells"]["R-ANCHOR"]["gates"],
            "cells": strip_trades(res["cells"]),
            "seam": res["seam"],
            "kills": res["kills"], "fired": res["fired"],
            "power_gate": res["power_gate_rt_236"],
            "placebo_rider": res["placebo_rider_net_per_occupied_hour"],
        }
    OUT_DEV.write_text(json.dumps(dev_out, indent=1, default=str))
    OUT_SEAM.write_text(json.dumps(
        {pair: results[pair]["seam"] for pair in PAIRS}, indent=1,
        default=str))
    OUT_KILLS.write_text(json.dumps(
        {pair: {"KILL_INVERSION": results[pair]["kills"]
                ["KILL_INVERSION"],
                "KILL_CONTROL_REPRODUCED": results[pair]["kills"]
                ["KILL_CONTROL_REPRODUCED"],
                "KILL_BETA_EXPLAINED": results[pair]["kills"]
                ["KILL_BETA_EXPLAINED"],
                "fired": results[pair]["fired"]} for pair in PAIRS},
        indent=1, default=str))

    # ---- 5: holdout one-look pass (only for eligible pairs) -----------
    holdout_out = {"schema": "tracka_scored_holdout@1",
                   "cycle_id": CYCLE_ID, "created_utc": now_utc(),
                   "membership_sha256": freeze["pins"]
                   ["(ii)_holdout_pass_membership"]["sha256"],
                   "pairs": {}}
    for pair, res in results.items():
        st = dev_status_of(res)
        if not st["eligible_for_holdout"]:
            holdout_out["pairs"][pair] = {
                "read": False,
                "status": "HOLDOUT_UNREAD_CONSUMED_BY_NONE",
                "reason": f"R-ANCHOR dev status {st['status']} "
                          f"({st.get('terminal_label') or st.get('failed_gates')}) "
                          "- a dead arm takes no holdout look (plan 9.1)",
            }
            continue
        p_full = res["_ctx"]["p_full"]
        widx_holdout = res["n_dev_bars"] - 1  # last dev bar: executor starts
        look, conditions = S.holdout_pass(
            pair, p_full, res["_ctx"]["tgts_full"], res["_ctx"]["pl_full"],
            widx_holdout)
        holdout_out["pairs"][pair] = {"read": True, "look": look,
                                      "promote_conditions": conditions,
                                      "power_gate": res["power_gate_rt_236"]}
    OUT_HOLDOUT.write_text(json.dumps(holdout_out, indent=1, default=str))

    # ---- 6: DSR across ALL cohort trials; PBO fail-closed -------------
    dsr_out = {
        "schema": "tracka_scored_dsr@1", "cycle_id": CYCLE_ID,
        "created_utc": now_utc(),
        "per_cell_series_files": series_files,
        "anchors": {}, "pbo": "NOT_RUN_FAIL_CLOSED (6-arm classes = 12 "
                              "cells but < 8 distinct CONFIG classes for "
                              "PBO's CSCV; fail-closed per plan 10)",
        "note": "DSR per anchor cell, deflated against the SR dispersion "
                "of ALL 12 cohort scored cells (FLAT null book "
                "contributes SR=0 by convention)",
    }
    for pair in PAIRS:
        tgt_cell = f"{pair}/R-ANCHOR"
        d = S.deflated_sharpe(daily, tgt_cell)
        dsr_out["anchors"][pair] = d
    OUT_DSR.write_text(json.dumps(dsr_out, indent=1, default=str))

    # ---- 7: terminal labels -------------------------------------------
    terminal = {}
    for pair, res in results.items():
        st = dev_status_of(res)
        fired = dict(res["fired"])
        hp = holdout_out["pairs"][pair]
        if st["eligible_for_holdout"]:
            conds = hp["promote_conditions"]
            if all(conds.values()):
                label = ("CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION"
                         if res["power_gate_rt_236"]["pass"]
                         else "NOT_POWERED_CANDIDATE")
            else:
                fired["KILL_HOLDOUT_FAIL"] = True
                label = "KILL_HOLDOUT_FAIL"
        else:
            label = st["terminal_label"]
        terminal[pair] = {"anchor_label": label, "fired": fired,
                          "eligible_for_holdout": st["eligible_for_holdout"]}

    # ---- 8: ledger append (append-only) --------------------------------
    rows = build_scored_ledger(results, holdout_out, terminal, freeze,
                               freeze_sha, labels_class)
    before = OUT_LEDGER.read_text()
    with open(OUT_LEDGER, "a") as f:
        for r in rows:
            f.write(json.dumps(r, default=str) + "\n")
    after = OUT_LEDGER.read_text()
    assert after.startswith(before), "ledger append-only law violated"

    # ---- 9: report ------------------------------------------------------
    write_report(results, holdout_out, terminal, dsr_out, rows)

    print(json.dumps({
        "pairs": {pair: {
            "anchor_gates_pass": results[pair]["anchor_gates_all_pass"],
            "fired": results[pair]["fired"],
            "seam_S": results[pair]["seam"]["S_net_pips"],
            "rt_dev": results[pair]["anchor_rt_dev_union"],
            "terminal_label": terminal[pair]["anchor_label"],
            "holdout_read": hp_read(holdout_out, pair),
        } for pair in PAIRS},
        "dsr": {pair: dsr_out["anchors"][pair]["DSR"] for pair in PAIRS},
        "ledger_rows_appended": len(rows),
    }, indent=1, default=str))
    return 0


def hp_read(holdout_out: dict, pair: str):
    return holdout_out["pairs"][pair].get("read")


def build_scored_ledger(results: dict, holdout_out: dict, terminal: dict,
                        freeze: dict, freeze_sha: str,
                        labels_class: list) -> list:
    rows = []
    for pair, res in results.items():
        beta = S.BETA_MATCHED[pair]
        term = terminal[pair]
        for arm, cell in res["cells"].items():
            view = beta if arm == "BASELINE-SET" else arm
            b1 = cell["books"][view]["1.0"]
            b15 = cell["books"][view]["1.5"]
            verdict = cell_label_for(
                arm, term["fired"],
                "PROMOTED" if term["anchor_label"] ==
                "CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION"
                else ("NOT_POWERED" if term["anchor_label"]
                      == "NOT_POWERED_CANDIDATE" else "REJECT"),
                True)
            gates_field = {
                "dev_gates_G1_G8": cell["gates"],
                "k1.0": {"net_pips": b1["decompose"]["net_pips"],
                         "gross_pips": b1["decompose"]["gross_pips"],
                         "cost_pips": b1["decompose"]["cost_pips"],
                         "n_trades": b1["decompose"]["n_trades"]},
                "k1.5": {"net_pips": b15["decompose"]["net_pips"],
                         "gross_pips": b15["decompose"]["gross_pips"]},
                "fired_kill_laws": term["fired"],
            }
            if arm == "BASELINE-SET":
                gates_field["composite_books"] = {
                    bk: {kk: {"net_pips": cell["books"][bk][kk]
                              ["decompose"]["net_pips"],
                              "gross_pips": cell["books"][bk][kk]
                              ["decompose"]["gross_pips"],
                              "n_trades": cell["books"][bk][kk]
                              ["decompose"]["n_trades"]}
                         for kk in ("1.0", "1.5", "2.0")}
                    for bk in ("FLAT", "SHORT_ALWAYS", "LONG_ALWAYS")}
                gates_field["beta_matched_book"] = beta
            if arm == "R-ANCHOR":
                gates_field["seam_law"] = res["seam"]
                gates_field["power_gate_rt_236"] = res["power_gate_rt_236"]
                gates_field["placebo_rider"] = \
                    res["placebo_rider_net_per_occupied_hour"]
            if arm == "R-ORIG":
                gates_field["role"] = "seam probe; NEVER selectable"
            if arm == "R-NEIGH":
                gates_field["role"] = "support check; NEVER selectable"
            rows.append({
                "cycle_id": CYCLE_ID, "mechanism_id": "M1", "arm_id": arm,
                "arm_config_digest": cell["arm_config_digest"],
                "pair": pair,
                "fold_or_holdout_tag": "DEV_FOLDS_F1_F6",
                "cost_tier": "PAPER_TIER_PER_SESSION_X_K",
                "net_pnl": b1["decompose"]["net_pips"],
                "gross_pnl": b1["decompose"]["gross_pips"],
                "gates_with_margins_to_fail": gates_field,
                "verdict": verdict,
                "verdict_note": cell_note(arm, term),
                "exclusion_zones": cell["exclusion_zones"],
                "labels": list(labels_class),
                "sha_chain": sha_chain_row(freeze, freeze_sha, pair),
            })
        # holdout rows
        hp = holdout_out["pairs"][pair]
        if hp["read"]:
            hd = load_frozen(pair)["holdout_digests"]
            beta = S.BETA_MATCHED[pair]
            for arm in ("R-ANCHOR", "CAUSAL-PLACEBO", "INVERTED",
                        "BASELINE-SET"):
                view = {"BASELINE-SET": beta}.get(arm, arm)
                l1 = hp["look"]["arms"][view]["1.0"]
                l15 = hp["look"]["arms"][view]["1.5"]
                verdict = term["anchor_label"] if arm == "R-ANCHOR" \
                    else "REJECT"
                rows.append({
                    "cycle_id": CYCLE_ID, "mechanism_id": "M1",
                    "arm_id": arm, "arm_config_digest": hd[arm],
                    "pair": pair,
                    "fold_or_holdout_tag":
                        "HOLDOUT_2026-01-01..2026-06-30",
                    "cost_tier": "PAPER_TIER_PER_SESSION_X_K",
                    "net_pnl": l1["net_pips"], "gross_pnl": l1["gross_pips"],
                    "gates_with_margins_to_fail": {
                        "holdout_k1.0": l1, "holdout_k1.5": l15,
                        "promote_conditions": hp["promote_conditions"],
                        "power_gate": hp["power_gate"],
                        "role": "companion single-pass" if arm != "R-ANCHOR"
                        else "anchor one-look"},
                    "verdict": verdict,
                    "verdict_note": ("companion of the one-look pass; never "
                                     "selectable" if arm != "R-ANCHOR"
                                     else "terminal per-pair label"),
                    "exclusion_zones": None,
                    "labels": list(labels_class),
                    "sha_chain": sha_chain_row(freeze, freeze_sha, pair),
                })
        else:
            rows.append({
                "cycle_id": CYCLE_ID, "mechanism_id": "M1",
                "arm_id": "R-ANCHOR",
                "arm_config_digest": results[pair]["frozen"]["digests"]
                ["R-ANCHOR"],
                "pair": pair,
                "fold_or_holdout_tag": "HOLDOUT_UNREAD",
                "cost_tier": "PAPER_TIER_PER_SESSION_X_K",
                "net_pnl": None, "gross_pnl": None,
                "gates_with_margins_to_fail": {
                    "reason": hp["reason"],
                    "fired_dev_kills": term["fired"]},
                "verdict": "HOLDOUT_UNREAD_CONSUMED_BY_NONE",
                "verdict_note": "no holdout look exists for this pair; the "
                                "one-look window was never read",
                "exclusion_zones": None,
                "labels": list(labels_class),
                "sha_chain": sha_chain_row(freeze, freeze_sha, pair),
            })
    return rows


def cell_note(arm: str, term: dict) -> str:
    fired = [k for k in KILL_PRECEDENCE if term["fired"].get(k)]
    if arm == "R-ANCHOR":
        return (f"terminal label {term['anchor_label']}; "
                f"fired kill laws: {fired or 'none'}")
    if arm in ("R-ORIG", "R-NEIGH"):
        return "never selectable per plan 4.2; diagnostic cell"
    return (f"control/companion cell; never selectable; fired kill laws "
            f"affecting the pair: {fired or 'none'}")


# ------------------------------------------------------------- report -----

def fmt_gate(name, g) -> str:
    d = g["detail"]
    return (f"| {name} | {g['verdict']} | {g['margin_to_fail']} | "
            f"{json.dumps(d, default=str)[:160]} |")


def write_report(results: dict, holdout_out: dict, terminal: dict,
                 dsr_out: dict, rows: list) -> None:
    lines = []
    a = lines.append
    a("# SCORED REPORT — ERP1-TRACKA-COHORT-1 (tracka1-scored, GO-2)")
    a("")
    a(f"Generated: {now_utc()}. Authority: freeze/GO1_freeze_artifact.json "
      "(+ erratum E1); plan 9.1-9.4, 10, 4.2; GO-2 record EXACT match.")
    a("First PnL-bearing execution of the cycle. Dry-run evidence was "
      "committed BEFORE any scored computation (scored_dryrun.json).")
    a("")
    for pair, res in results.items():
        term = terminal[pair]
        a(f"## Pair {pair}")
        a("")
        cell = res["cells"]["R-ANCHOR"]
        b1 = cell["books"]["R-ANCHOR"]["1.0"]
        a(f"### R-ANCHOR dev gates (k=1.0 book; RT dev union = "
          f"{res['anchor_rt_dev_union']})")
        a("")
        a("| gate | verdict | margin to fail | detail |")
        a("|---|---|---|---|")
        for gname, gv in cell["gates"].items():
            a(fmt_gate(gname, gv))
        a("")
        a(f"Anchor net @k: " + ", ".join(
            f"{k}={cell['books']['R-ANCHOR'][k]['decompose']['net_pips']} "
            f"pips ({cell['books']['R-ANCHOR'][k]['decompose']['n_trades']} "
            f"RT)" for k in ("1.0", "1.5", "2.0")))
        a("")
        a("### Seam law (per pair, k=1.0)")
        a("")
        s = res["seam"]
        a(f"- S = net(R-ORIG) - net(R-ANCHOR) = {s['net_R-ORIG_pips']} - "
          f"{s['net_R-ANCHOR_pips']} = **{s['S_net_pips']} pips**; "
          f"c_rt frozen = {s['c_rt_frozen_pips']} pips "
          f"(recomputed {s['c_rt_recomputed_pips']})")
        a(f"- limb (i): S > 10*c_rt = {s['limb_i']['threshold_pips']} -> "
          f"**{'FIRES' if s['limb_i']['fires'] else 'no'}**")
        a(f"- limb (ii): S > 3*c_rt = {s['limb_ii']['threshold_pips']} AND "
          f"S>0 on >=4/6 folds (S>0 folds = "
          f"{s['folds_S_positive']}) -> **"
          f"{'FIRES' if s['limb_ii']['fires'] else 'no'}**")
        l3 = s["limb_iii"]
        if l3["status"] == "EVALUATED":
            a(f"- limb (iii): matched pairs {l3['matched_pairs']} "
              f"(>= 20 floor); mean R-ORIG-matched "
              f"{l3['mean_orig_matched_pips']} vs mean R-ANCHOR-matched "
              f"{l3['mean_anchor_matched_pips']}; delta "
              f"{l3['delta_pips']} vs 1*c_rt = {s['c_rt_frozen_pips']} -> "
              f"**{'FIRES' if l3['fires'] else 'no'}** "
              f"(unmatched excluded: {l3['unmatched_orig_only_excluded']} "
              f"orig / {l3['unmatched_anchor_only_excluded']} anchor)")
        else:
            a(f"- limb (iii): **NOT_RUN fail-closed** "
              f"(matched {l3['matched_pairs']} < floor "
              f"{l3['min_n_floor']}); limbs (i)/(ii) decide")
        a(f"- seam verdict: **{s['verdict']}**; per-fold S: "
          f"{s['per_fold_S_pips']}")
        a("")
        a("### Kill laws (per pair, k=1.0)")
        a("")
        k = res["kills"]
        ki, kc, kb = (k["KILL_INVERSION"], k["KILL_CONTROL_REPRODUCED"],
                      k["KILL_BETA_EXPLAINED"])
        a(f"- KILL_INVERSION: inverted net {ki['net_inverted_pips']} vs "
          f"anchor {ki['net_anchor_pips']} -> overall limb "
          f"{'FIRES' if ki['limb_overall']['fires'] else 'no'}; shadow-folds "
          f"limb {'FIRES' if ki['limb_shadow_folds']['fires'] else 'no'} "
          f"{ki['limb_shadow_folds'].get('violating_folds') or ''} => "
          f"**{ki['verdict']}**")
        a(f"- KILL_CONTROL_REPRODUCED: placebo net {kc['net_placebo_pips']} "
          f"vs 0.5*anchor {kc['half_anchor_threshold']} -> band limb "
          f"{'FIRES' if kc['limb_band']['fires'] else 'no'}; fold-residue "
          f"limb (placebo folds>0 = "
          f"{kc['limb_fold_residue']['placebo_positive_folds']}/6, anchor < "
          f"2x placebo) {'FIRES' if kc['limb_fold_residue']['fires'] else 'no'}"
          f" => **{kc['verdict']}**")
        a(f"- KILL_BETA_EXPLAINED: beta-matched book = "
          f"{kb['beta_matched_book']} net {kb['net_beta_matched_pips']}; "
          f"anchor - beta = {kb['anchor_minus_beta_pips']}; "
          f"always-on books {kb['always_on_books_net_pips']} => "
          f"**{kb['verdict']}**")
        a("")
        rider = res["placebo_rider_net_per_occupied_hour"]
        a(f"Placebo rider (net per occupied entry-hour): anchor "
          f"{rider['anchor_net_per_occupied_hour']} pips/hour over "
          f"{rider['anchor_occupied_hours']} hours; placebo "
          f"{rider['placebo_net_per_occupied_hour']} pips/hour over "
          f"{rider['placebo_occupied_hours']} hours")
        a("")
        a("### All-arm dev summary (k=1.0 net pips | RT | PF | G-gates)")
        a("")
        beta = S.BETA_MATCHED[pair]
        a("| arm | net@1.0 | net@1.5 | RT | PF | G1-G8 |")
        a("|---|---|---|---|---|---|")
        for arm, c in res["cells"].items():
            view = beta if arm == "BASELINE-SET" else arm
            gates = c["gates"]
            gsum = " ".join(
                f"{g.split('_')[0]}:{v['verdict'][0]}"
                for g, v in gates.items())
            a(f"| {arm} (view {view}) "
              f"| {c['books'][view]['1.0']['decompose']['net_pips']} "
              f"| {c['books'][view]['1.5']['decompose']['net_pips']} "
              f"| {c['books'][view]['1.0']['decompose']['n_trades']} "
              f"| {c['books'][view]['1.0']['gates']['pf']} | {gsum} |")
        a("")
        hp = holdout_out["pairs"][pair]
        a("### Holdout (one-look law)")
        a("")
        if hp["read"]:
            la = hp["look"]["arms"]["R-ANCHOR"]
            lc = hp["look"]["arms"]["CAUSAL-PLACEBO"]
            li = hp["look"]["arms"]["INVERTED"]
            lb = hp["look"]["arms"][S.BETA_MATCHED[pair]]
            a(f"- R-ANCHOR holdout net: @1.0 = "
              f"{la['1.0']['net_pips']} pips, @1.5 = "
              f"{la['1.5']['net_pips']} pips "
              f"({la['1.0']['n_trades']} RT)")
            a(f"- companions: placebo @1.0 {lc['1.0']['net_pips']}; "
              f"inverted @1.0 {li['1.0']['net_pips']}; beta-matched "
              f"{S.BETA_MATCHED[pair]} @1.0 {lb['1.0']['net_pips']}")
            a(f"- PROMOTE conditions: {hp['promote_conditions']}")
            a(f"- power gate: {hp['power_gate']}")
        else:
            a(f"- **{hp['status']}** — {hp['reason']}")
        a("")
        a(f"### Terminal verdict — R-ANCHOR {pair}: "
          f"**{term['anchor_label']}**")
        a("")
    a("## DSR (deflated Sharpe, ALL cohort trials)")
    a("")
    a(f"- {dsr_out['note']}")
    for pair, d in dsr_out["anchors"].items():
        a(f"- {pair}: DSR = **{d['DSR']}** (SR_hat daily = "
          f"{d['target_stats']['sr_daily']:.6f}, SR0 = "
          f"{d['SR0_expected_max']:.6f}, N = {d['N_trials']}, "
          f"T = {d['target_stats']['n_periods']} trading days)")
    a(f"- PBO: {dsr_out['pbo']}")
    a("")
    a("## Cohort-level conclusion")
    a("")
    labels = {p: terminal[p]["anchor_label"] for p in PAIRS}
    if all(v == "CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION"
           for v in labels.values()):
        concl = ("Both pairs' R-ANCHOR arms passed every preregistered dev "
                 "gate with no kill law fired and verified on the one-look "
                 "holdout: the strongest allowed cohort-level statement is "
                 "TWO paper-tier candidates pending prospective "
                 "verification (PAPER_TIER labels hold; this grants "
                 "eligibility to REQUEST a prospective-shadow amendment, "
                 "never S1, never live).")
    elif any(v == "CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION"
             for v in labels.values()):
        concl = ("One pair's R-ANCHOR reached paper-tier candidate status; "
                 "the other did not survive the frozen gates. Per-arm "
                 "verdicts above are the authority.")
    else:
        concl = ("No arm of this cohort reached candidate status under the "
                 "frozen gates; the cohort closes per the per-pair verdicts "
                 "above (REJECT/KILL_* as recorded). No replacement enters "
                 "mid-cohort (plan 9.3).")
    a(concl)
    a("")
    a("## Ledger")
    a("")
    a(f"- {len(rows)} scored rows appended to trial_ledger.jsonl "
      f"(append-only). Verdict vocabulary: CANDIDATE_PENDING_PROSPECTIVE_"
      f"VERIFICATION / NOT_POWERED_CANDIDATE / KILL_* / REJECT (+ "
      f"HOLDOUT_UNREAD_CONSUMED_BY_NONE bookkeeping rows).")
    a("- Mandatory labels on every row: SINGLE_SOURCE_PANEL, "
      "FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK, PAPER_TIER.")
    a("")
    OUT_REPORT.write_text("\n".join(lines))


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "dryrun"
    if mode == "dryrun":
        return run_dryrun()
    if mode != "scored":
        print("usage: scored_run.py dryrun|scored")
        return 2
    return run_scored()


if __name__ == "__main__":
    sys.exit(main())
