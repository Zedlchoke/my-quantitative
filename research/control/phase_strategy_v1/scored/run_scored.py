"""PSV1 scored run orchestrator (post-GO; plan §15; evaluation_freeze).

Modes:
  dry    — sanitized exact-arm dry-run: activity counts only, non-vacuous
           + distinct-ID assertions; NO PnL is computed or emitted.
  scored — the one atomic scored run: full cost stack, tiers 1.0/1.5/2.0,
           gates G1-G7 (G8 repro / G9 A7 terminal are appended externally).

Usage: python run_scored.py --mode dry|scored --out <dir>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import accounting as acc  # noqa: E402
import books as bk  # noqa: E402
import cells  # noqa: E402

CODE_FREEZE_SHA = "8865e7d33e6e6e00d9b1dae7ce8b911e740139aa"
TIERS = [1.0, 1.5, 2.0]

L1_ARMS = [
    ("PSV1-BTC_H1-UPTREND-BREAKOUT_CONT", "UPTREND"),
    ("PSV1-BTC_H1-ACC-FLOOR_PROVISION", "ACCUMULATION"),
    ("PSV1-BTC_H1-DOWNTREND-BREAKDOWN_CONT", "DOWNTREND"),
]


def _sha_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build_cell_runs(cell: dict) -> dict:
    """arms: {arm_id: fills}; controls: {control_id: builder callable}."""
    out = {"arms": {}, "controls": {}, "baselines": {}}
    if cell["cell"] == "BTC_H1":
        for arm_id, _phase in L1_ARMS:
            ev, side = bk.l1_candidate_signals(cell, arm_id)
            out["arms"][arm_id] = {
                "fills": bk.l1_events_to_fills(ev, side),
                "entries": len(ev.entries), "exits": len(ev.exits),
                "exit_reasons": dict(ev.exit_reasons),
                "unnecessary_close_reopen": ev.unnecessary_close_reopen,
            }
        out["controls"] = {
            "CTL-SHUFFLED::PSV1-BTC_H1-UPTREND-BREAKOUT_CONT":
                ("l1_shuffled", "PSV1-BTC_H1-UPTREND-BREAKOUT_CONT"),
            "CTL-SHUFFLED::PSV1-BTC_H1-DOWNTREND-BREAKDOWN_CONT":
                ("l1_shuffled", "PSV1-BTC_H1-DOWNTREND-BREAKDOWN_CONT"),
            "CTL-CLOCKONLY::PSV1-BTC_H1-ACC-FLOOR_PROVISION":
                ("l1_clockonly", "PSV1-BTC_H1-ACC-FLOOR_PROVISION"),
        }
    elif cell["cell"] == "BTC_H4":
        book = bk.l2_run_book(cell)
        out["arms"]["PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION"] = {
            "fills": bk.l2_fills_from_book(book),
            "entries": book["n_entries"], "exits": book["n_exits"],
            "exit_reasons": dict(book["exit_reason_counts"]),
            "unnecessary_close_reopen": 0,
            "_book": book,
        }
        out["controls"] = {
            "CTL-BLOCKSHUFFLE::PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION":
                ("l2_blockshuffle", "PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION"),
        }
    else:
        out["arms"] = {}
        out["controls"] = {}
    out["baselines"] = {
        "BASELINE-CASH": [],
        "BASELINE-ALWAYS_ON_LONG": bk.baseline_always_on_long(cell),
        "BASELINE-ALWAYS_ON_TREND_LF": bk.baseline_always_on_trend_lf(cell),
        "BASELINE-SPARSE_RISK_OFF": bk.baseline_sparse_risk_off(cell, 0.30 if "BTC" in cell["cell"] else 0.20),
    }
    return out


def _funding_mask(cell):
    if cell["funding_rate"]:
        return acc.btc_8h_boundary_mask(cell["open_ms"])
    return None


def _acct(cell, fills, tier):
    return acc.run_accounting(
        cell["open"], cell["close"], fills, cell["fold_ids"],
        cell["bps"], tier=tier,
        funding_mask=_funding_mask(cell), funding_rate=cell["funding_rate"])


def run_dry(out_dir: Path) -> dict:
    report = {"mode": "dry", "code_freeze_sha": CODE_FREEZE_SHA, "cells": {}}
    ids = []
    for loader in (cells.load_btc_h1, cells.load_btc_h4, cells.load_spy):
        cell = loader()
        runs = build_cell_runs(cell)
        cell_rep = {}
        for arm_id, spec in runs["arms"].items():
            ids.append(arm_id)
            cell_rep[arm_id] = {
                "entries": spec["entries"], "exits": spec["exits"],
                "fills": len(spec["fills"]),
                "non_vacuous": spec["entries"] > 0,
            }
        for b_id, fills in runs["baselines"].items():
            ids.append(b_id + "::" + cell["cell"])
            if b_id == "BASELINE-CASH":
                act = 0
            else:
                act = len(fills)
            cell_rep[b_id] = {"fills": act,
                              "non_vacuous": act > 0 or b_id == "BASELINE-CASH"}
        report["cells"][cell["cell"]] = cell_rep
    assert len(ids) == len(set(ids)), "arm IDs not distinct"
    report["ids_distinct"] = True
    report["non_vacuous_all"] = all(
        v.get("non_vacuous", True) for c in report["cells"].values() for v in c.values())
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "dry_run_report.json").write_text(json.dumps(report, indent=1))
    return report


def l2_blockshuffle_control(cell: dict, tier: float):
    rng = np.random.default_rng(bk.CONTROL_SEED)
    labels = np.asarray(cell["labels"]).astype(str)
    cand_book = bk.l2_run_book(cell)
    cand_res = _acct(cell, bk.l2_fills_from_book(cand_book), tier)
    sh = labels.copy()
    block = 30
    for f in sorted(set(int(x) for x in cell["fold_ids"].tolist())):
        idx = np.where(cell["fold_ids"] == f)[0]
        up = (labels[idx] == "UPTREND").astype(int)
        pad = (-len(up)) % block
        upp = np.concatenate([up, np.zeros(pad, dtype=int)])
        blocks = upp.reshape(-1, block)
        perm = rng.permutation(blocks.shape[0])
        shuffled = blocks[perm].reshape(-1)[:len(up)].astype(bool)
        orig = labels[idx]
        new = np.where(shuffled, "UPTREND",
                       np.where(orig == "UPTREND", "TRANSITION_UNKNOWN", orig))
        sh[idx] = new
    book2 = bk.l2_run_book(cell, sh)
    res2 = _acct(cell, bk.l2_fills_from_book(book2), tier)
    valid = book2["n_entries"] >= 0.5 * cand_book["n_entries"]
    return {
        "candidate_net": cand_res["net"], "candidate_entries": cand_book["n_entries"],
        "control_net": res2["net"], "control_entries": book2["n_entries"],
        "movement_validation": "entries>=50% candidate",
        "valid": bool(valid), "kill": bool(valid and res2["net"] > cand_res["net"]),
    }


def run_scored(out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    tier_dir = out_dir / "tiers"
    tier_dir.mkdir(exist_ok=True)
    ledger = {
        "schema": "psv1_scored_ledger@1",
        "cycle_id": "PHASE-STRATEGY-V1",
        "code_freeze_sha": CODE_FREEZE_SHA,
        "go_phrase": "GO PHASE STRATEGY V1 SCORED EXECUTION",
        "data_authority": {
            "BTC_H1_manifest_sha256": _sha_file(cells.BASE / "lane_btc_h1" / "data" / "manifest.json"),
            "BTC_H4_manifest_sha256": _sha_file(cells.BASE / "lane_btc_h4" / "data" / "manifest.json"),
            "SPY_snapshot_sha256": cells.SNAPSHOT_SHA256,
        },
        "arms": {}, "baselines": {}, "controls": {}, "gates": {},
    }
    for loader in (cells.load_btc_h1, cells.load_btc_h4, cells.load_spy):
        cell = loader()
        cname = cell["cell"]
        runs = build_cell_runs(cell)
        fold_names = cell.get("fold_names") or {i: f"F{i+1}" for i in sorted(set(cell["fold_ids"].tolist()))}
        for arm_id, spec in runs["arms"].items():
            tier_res = {}
            for tier in TIERS:
                res = _acct(cell, spec["fills"], tier)
                res.pop("trade_records")
                tier_res[f"{tier}x"] = res
            ledger["arms"][f"{cname}::{arm_id}"] = {
                "phase": next((p for a, p in L1_ARMS if a == arm_id), "UPTREND" if "UPTREND" in arm_id else "?"),
                "entries": spec["entries"], "exits": spec["exits"],
                "exit_reasons": spec["exit_reasons"],
                "unnecessary_close_reopen": spec["unnecessary_close_reopen"],
                "tiers": tier_res,
            }
        for b_id, fills in runs["baselines"].items():
            tier_res = {}
            for tier in TIERS:
                res = _acct(cell, fills, tier)
                res.pop("trade_records")
                tier_res[f"{tier}x"] = res
            ledger["baselines"][f"{cname}::{b_id}"] = {"tiers": tier_res}
        for ctl_id, (kind, target) in runs["controls"].items():
            if kind == "l1_shuffled":
                rep = bk.l1_phase_shuffled_control(cell, target, 1.0, cell["bps"],
                                                   _funding_mask(cell), cell["funding_rate"])
            elif kind == "l1_clockonly":
                rep = bk.l1_clock_only_control(cell, 1.0, cell["bps"],
                                               _funding_mask(cell), cell["funding_rate"])
            else:
                rep = l2_blockshuffle_control(cell, 1.0)
            ledger["controls"][f"{cname}::{ctl_id}"] = rep
        # fold/era mapping for reporting
        ledger.setdefault("fold_map", {})[cname] = fold_names
    # ---- gates per candidate (base tier = 1.0x) ----
    for key, arm in ledger["arms"].items():
        cname, arm_id = key.split("::", 1)
        t1 = arm["tiers"]["1.0x"]
        t15 = arm["tiers"]["1.5x"]
        base_nets = {b.split("::", 1)[1]: v["tiers"]["1.0x"]["net"]
                     for b, v in ledger["baselines"].items() if b.startswith(cname + "::")}
        fold_nets = t1["per_fold_net"]
        pos_folds = {k: v for k, v in fold_nets.items() if v > 0}
        g4 = (sum(1 for v in fold_nets.values() if v > 0) >= 3
              or (sum(fold_nets.values()) - max(fold_nets.values())) > 0)
        gates = {
            "G1_net_gt0_1x": t1["net"] > 0,
            "G2_net_gt0_15x": t15["net"] > 0,
            "G3_beats_all_baselines_1x": all(t1["net"] > v for v in base_nets.values()),
            "G4_fold_robustness": bool(g4),
            "G5_concentration_le_050": (t1["fold_concentration"] is None
                                        or t1["fold_concentration"] <= 0.50),
        }
        ctl = ledger["controls"].get(f"{cname}::CTL-SHUFFLED::{arm_id}") \
            or ledger["controls"].get(f"{cname}::CTL-CLOCKONLY::{arm_id}") \
            or ledger["controls"].get(f"{cname}::CTL-BLOCKSHUFFLE::{arm_id}")
        if ctl is None:
            gates["G6_control"] = "NOT_RUN"
        elif "median_net" in ctl:
            if not ctl.get("valid_draws"):
                gates["G6_control"] = "INVALID_NULL_DISCLOSED (rests on G1-G5)"
            else:
                gates["G6_control"] = "KILLED" if ctl["median_net"] > t1["net"] else "PASS"
        elif "net" in ctl:
            gates["G6_control"] = "KILLED" if ctl["net"] > t1["net"] else "PASS"
        elif "kill" in ctl:
            gates["G6_control"] = "KILLED" if ctl["kill"] else "PASS"
        gates["G7_churn"] = (arm["unnecessary_close_reopen"] == 0)
        gates["G8_reproduction"] = "PENDING_TWIN"
        gates["G9_a7_terminal"] = "PENDING_A7"
        ledger["gates"][key] = gates
    passed = [k for k, g in ledger["gates"].items()
              if all(v in (True, "PASS", "INVALID_NULL_DISCLOSED (rests on G1-G5)",
                           "NOT_RUN") for kk, v in g.items()
                     if kk not in ("G8_reproduction", "G9_a7_terminal"))]
    ledger["candidates_passing_G1_G7"] = passed
    ledger["observed_scored_denominator"] = (
        len(ledger["arms"]) * len(TIERS) + len(ledger["baselines"]) * len(TIERS)
        + len(ledger["controls"]))
    ledger["budget_cells_consumed"] = len(ledger["arms"])
    for tier in TIERS:
        (tier_dir / f"tier_{tier}x.json").write_text(json.dumps(
            {k: v for k, v in ledger.items() if k != "gates"} | {"_tier": tier},
            indent=1, default=str))
    (out_dir / "scored_ledger.json").write_text(json.dumps(ledger, indent=1, default=str))
    return ledger


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["dry", "scored"], required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    if args.mode == "dry":
        rep = run_dry(out)
        print(json.dumps({"non_vacuous_all": rep["non_vacuous_all"],
                          "ids_distinct": rep["ids_distinct"]}))
    else:
        led = run_scored(out)
        print(json.dumps({"candidates_passing_G1_G7": led["candidates_passing_G1_G7"],
                          "budget_cells_consumed": led["budget_cells_consumed"],
                          "observed_scored_denominator": led["observed_scored_denominator"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
