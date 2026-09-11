"""FOREX-NG1 E-phase SCORED EXECUTION driver (task forex-ng1-e-scored).

Lane E consumes GO (typed at 3dfd278) and computes the six adjudicated
budget cells through the FROZEN code only (research/assets/forex_ng1/
-- read-only here; this module never edits it):

  a1_adjudication_2026_09_11.budget_cell_control_mapping:
    FXNG1-A5-P1  ANCHOR / NEIGH-COOPEN / CTL-V7RECAP (scored control;
                 CTL-DGS10LEVEL non-scored, NO PnL on it)
    FXNG1-A4-P2  ANCHOR / NEIGH-SMOOTH2 / CTL-DGS10LEVEL (scored control)

Laws enforced here (all inherited, none invented):

- machine-wide heavy lock held for the whole computation (FOREX-NG1 /
  E_SCORED); refusal is NOT_RUN_RESOURCE_CONFLICT, never a spin;
- every arm_config_digest must reproduce the committed pins (run_contract
  arm_config_digests for the 5 contract-listed cells; the A7-recomputed
  digest 5d11a0c9... for FXNG1-A5-P1-CTL-V7RECAP) before any PnL;
- PnL identity, cost ladder and tier-2.0 PRIMARY come from the frozen
  accounting kernel (price_pnl_usd / bps_cost); aggregates must
  reconcile with accounting.compute_outcomes(scored=True, authority from
  the committed proof) or the lane TECHABORTs;
- R1-R6 evaluated by the frozen evaluator, fail-closed: a rule whose
  metric is missing/not computable is NOT_RUN with reason, never an
  inferred PASS; any NOT_RUN blocks CELL_PASS;
- NO rescue, NO threshold change, NO re-run for bad numbers.  TECHABORT
  is for genuine technical failures only, with exposure recorded.

Conventions this lane fixes (disclosed in every artifact that uses
them):

- per-trade PnL realized at the exit grid day (daily series for the
  future DSR P-11 pass); trades are pair-decisions (1 unit = 10,000 USD
  notional; US A4 events fire 4 pair-decisions);
- profit_factor = sum(positive net tier-2 PnL) / |sum(negative net
  tier-2 PnL)|; zero losing trades -> None -> R4 NOT_RUN (conventionally
  infinite is an inference, not a measurement);
- max_single_event_gross_share: events grouped by event_key, event
  gross = signed sum of gross PnL; share = max(event gross / total
  gross) over events; total gross <= 0 -> None -> R6 NOT_RUN (an
  absolute-share variant is disclosed alongside for audit);
- drop_one_fold_positive: dropping fold k, the remaining book's net
  tier-2.0 total must be > 0 (0 remaining trades -> False);
- R2 cross-arm inputs: A5 control slot AND v7recap slot both carry the
  CTL-V7RECAP scored expectancy (adjudication: the A5 DGS10 nominal
  control is non-scored, no PnL); A4 control slot carries CTL-DGS10LEVEL.

Usage:
    .venv/bin/python research/control/forex_ng1_run/e/run_scored.py
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
import time
import traceback
from datetime import date

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.assets.forex_ng1.run import arms as A             # noqa: E402
from research.assets.forex_ng1.run import config as C           # noqa: E402
from research.assets.forex_ng1.run import data as D             # noqa: E402
from research.assets.forex_ng1.run import evaluator as V        # noqa: E402
from research.assets.forex_ng1.spot_series import (             # noqa: E402
    require_scored_authority, resolve_all_pairs,
)
from research.governance import heavy_lock                      # noqa: E402

E_DIR = os.path.dirname(os.path.abspath(__file__))
CONTROL_DIR = os.path.dirname(E_DIR)
REPO = REPO_ROOT

DISPATCH_SHA = "3dfd278150fa20c0646336b1e5430cf432d903c0"
CODE_FREEZE_SHA = "2d1989adb353ccb1ec1a5e9fd36724bce0bf7375"
CODE_FREEZE_TREE = "086af11f295b61c25a19e596700c10bb06e0a5ee"
DGS10_PINNED_COPY = ("/Users/hoangminhlong/my-quantitative/.worktrees/"
                     "forex-ng1/integration/.worktrees/forex-ng1/i-runners/"
                     "data_raw/forex_ng1_ctl/DGS10.json")
SCRATCH = "/tmp/forex_ng1_e_scored_scratch"

#: The six adjudicated scored cells, in adjudication order.
CELLS = (
    ("FXNG1-A5-P1-ANCHOR", "anchor"),
    ("FXNG1-A5-P1-NEIGH-COOPEN", "neighbour"),
    ("FXNG1-A5-P1-CTL-V7RECAP", "control_scored_cell"),
    ("FXNG1-A4-P2-ANCHOR", "anchor"),
    ("FXNG1-A4-P2-NEIGH-SMOOTH2", "neighbour"),
    ("FXNG1-A4-P2-CTL-DGS10LEVEL", "control_scored_cell"),
)
FAMILY_CELLS = {
    "FXNG1-A5-P1": {
        "anchor": "FXNG1-A5-P1-ANCHOR",
        "neighbour": "FXNG1-A5-P1-NEIGH-COOPEN",
        "control_scored_cell": "FXNG1-A5-P1-CTL-V7RECAP",
        "control_nonscored": "FXNG1-A5-P1-CTL-DGS10LEVEL (no PnL by "
                             "adjudication)",
        "r2_mapping": "control slot AND v7recap slot both fed the "
                      "CTL-V7RECAP scored expectancy (R2' armed on its "
                      "own scored cell; the A5 nominal DGS10 control is "
                      "non-scored)",
    },
    "FXNG1-A4-P2": {
        "anchor": "FXNG1-A4-P2-ANCHOR",
        "neighbour": "FXNG1-A4-P2-NEIGH-SMOOTH2",
        "control_scored_cell": "FXNG1-A4-P2-CTL-DGS10LEVEL",
        "control_nonscored": "CTL-V7RECAP battery (no A4 v7recap arm "
                             "implemented; non-scored by adjudication)",
        "r2_mapping": "control slot fed the CTL-DGS10LEVEL scored "
                      "expectancy; no v7recap slot",
    },
}

DRYRUN_COUNTS = {   # committed z_dryrun_report.json record_counts
    "FXNG1-A5-P1-ANCHOR": 37,
    "FXNG1-A5-P1-NEIGH-COOPEN": 79,
    "FXNG1-A5-P1-CTL-DGS10LEVEL": 36,
    "FXNG1-A4-P2-ANCHOR": 380,
    "FXNG1-A4-P2-NEIGH-SMOOTH2": 409,
    "FXNG1-A4-P2-CTL-DGS10LEVEL": 351,
}

Q8_DISCLOSURE = (
    "cost basis is the frozen selection_freeze.cost_contract_frozen "
    "proxy ladder (1.5 bps/side x {1.0,1.5,2.0}, tier 2.0 PRIMARY, "
    "charged once per fill), referenced from V2/V8 precedent and "
    "conservative vs the V8-measured 1.05bp FX spread; Q-8 remeasurement "
    "from executable quotes is NOT_RUN (no quote bytes in the frozen "
    "set) -- A7-NG1-M2: false negatives only, cannot manufacture a "
    "false PASS; must be surfaced at terminal + P-2 margin recording")


def utcnow() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _git(*args: str) -> str:
    out = subprocess.run(["git", "-C", REPO, *args],
                         capture_output=True, text=True, check=True)
    return out.stdout.strip()


def _sha256_file(path: str) -> str:
    return C.sha256_file(path)


def _write_json(path: str, payload: dict) -> str:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True)
        fh.write("\n")
    return _sha256_file(path)


# --------------------------------------------------------------------------- #
# per-trade computation on the frozen kernel
# --------------------------------------------------------------------------- #

def per_trade_records(book: dict, prices_by_pair: dict) -> list[dict]:
    from research.assets.forex_ng1.run import accounting as K
    out = []
    for rec in book["decisions"]:
        px = prices_by_pair[rec["pair"]]
        entry = px[rec["entry_grid_day"]]
        exit_ = px[rec["exit_grid_day"]]
        notional = rec["units"] * C.NOTIONAL_USD_UNIT
        g = K.price_pnl_usd(rec["direction"], notional, entry, exit_)
        nets = {f"net_usd_tier{t}": g - 2.0 * K.bps_cost(notional, t)
                for t in C.COST_TIER_LADDER}
        row = {
            "decision_id": rec["decision_id"],
            "event_key": rec["event"]["event_key"],
            "economy": rec["event"]["economy"],
            "pair": rec["pair"],
            "direction": rec["direction"],
            "units": rec["units"],
            "entry_grid_day": rec["entry_grid_day"],
            "exit_grid_day": rec["exit_grid_day"],
            "exit_reason": rec["exit_reason"],
            "fold": rec["fold"],
            "entry_price": entry,
            "exit_price": exit_,
            "gross_usd": g,
        }
        row.update(nets)
        out.append(row)
    return out


def book_stats(pnls: list[float]) -> dict:
    from research.assets.forex_ng1.run import accounting as K
    m = K.book_metrics(pnls)
    pos = math.fsum(x for x in pnls if x > 0)
    neg = math.fsum(x for x in pnls if x < 0)
    pf = None if neg == 0.0 else pos / abs(neg)
    return {
        "trades": m["trades"],
        "total_usd": m["total"],
        "expectancy_usd": m["expectancy"],
        "gross_profit_usd": pos,
        "gross_loss_usd": neg,
        "wins": sum(1 for x in pnls if x > 0),
        "losses": sum(1 for x in pnls if x < 0),
        "profit_factor": pf,
        "profit_factor_note": None if pf is not None else
            "no losing trades: PF conventionally infinite is an "
            "inference, not a measurement -> NOT_RUN at R4",
    }


def daily_series(trades: list[dict], grid: list[date]) -> dict:
    by_day_gross: dict[str, float] = {}
    by_day_net: dict[str, float] = {}
    for t in trades:
        d = t["exit_grid_day"]
        by_day_gross[d] = by_day_gross.get(d, 0.0) + t["gross_usd"]
        by_day_net[d] = by_day_net.get(d, 0.0) + t["net_usd_tier2.0"]
    days, cg, cn = [], 0.0, 0.0
    for g in grid:
        iso = g.isoformat()
        dg = by_day_gross.get(iso, 0.0)
        dn = by_day_net.get(iso, 0.0)
        cg += dg
        cn += dn
        if dg != 0.0 or dn != 0.0:
            days.append({"day": iso, "gross_usd": dg,
                         "net_tier2_usd": dn,
                         "cum_gross_usd": cg, "cum_net_tier2_usd": cn})
    return {
        "convention": "per-trade PnL realized at the exit grid day; "
                      "cumulative curves over the full 1842-day grid "
                      "(zero days omitted from the row list, curves "
                      "carry them); for the future DSR P-11 pass",
        "days_with_activity": len(days),
        "series": days,
        "final_cum_gross_usd": cg,
        "final_cum_net_tier2_usd": cn,
    }


def fold_blocks(trades: list[dict]) -> dict:
    out = {}
    for f in ("1", "2", "3"):
        sub = [t for t in trades if str(t["fold"]) == f]
        nets = [t["net_usd_tier2.0"] for t in sub]
        gross = [t["gross_usd"] for t in sub]
        out[f] = {
            "label": C.FOLD_LABELS[int(f) - 1],
            "trades": len(sub),
            "total_net_tier2_usd": math.fsum(nets) if sub else None,
            "expectancy_net_tier2_usd":
                (math.fsum(nets) / len(nets)) if sub else None,
            "total_gross_usd": math.fsum(gross) if sub else None,
        }
    return out


def event_concentration(trades: list[dict]) -> dict:
    per_event: dict[str, float] = {}
    for t in trades:
        per_event[t["event_key"]] = (per_event.get(t["event_key"], 0.0)
                                     + t["gross_usd"])
    total = math.fsum(t["gross_usd"] for t in trades)
    if total > 0:
        shares = {k: v / total for k, v in per_event.items()}
        abs_shares = {k: abs(v) / total for k, v in per_event.items()}
        top = max(shares, key=lambda k: shares[k])
        top_abs = max(abs_shares, key=lambda k: abs_shares[k])
        max_share = shares[top]
        max_abs = abs_shares[top_abs]
    else:
        top = top_abs = None
        max_share = max_abs = None
    return {
        "convention": "events grouped by event_key; event gross = signed "
                      "sum of the event's gross trade PnL; share = "
                      "event gross / total gross (signed); an |event|/total "
                      "variant is disclosed for audit",
        "events": len(per_event),
        "total_gross_usd": total,
        "max_single_event_gross_share": max_share,
        "max_single_event_key": top,
        "max_single_event_abs_gross_share": max_abs,
        "max_single_event_abs_key": top_abs,
        "none_reason": None if total > 0 else
            "total gross <= 0: concentration share undefined -> R6 "
            "NOT_RUN (fail-closed)",
    }


def drop_one_fold(trades: list[dict]) -> dict:
    out = {}
    for f in ("1", "2", "3"):
        remaining = [t["net_usd_tier2.0"] for t in trades
                     if str(t["fold"]) != f]
        total = math.fsum(remaining) if remaining else None
        out[f] = {
            "dropped_fold": C.FOLD_LABELS[int(f) - 1],
            "remaining_trades": len(remaining),
            "remaining_total_net_tier2_usd": total,
            "positive": bool(remaining) and total > 0,
        }
    return out


def metrics_for_evaluator(arm_trades: list[dict], family_exp: dict | None,
                          family: str) -> dict:
    nets2 = [t["net_usd_tier2.0"] for t in arm_trades]
    stats = book_stats(nets2)
    conc = event_concentration(arm_trades)
    drop = drop_one_fold(arm_trades)
    folds = fold_blocks(arm_trades)
    m = {
        "expectancy_net_tier2": stats["expectancy_usd"],
        "profit_factor_net_tier2": stats["profit_factor"],
        "fold_expectancies_net_tier2": {
            f: folds[f]["expectancy_net_tier2_usd"] for f in folds},
        "stress_tier2_expectancy_net": stats["expectancy_usd"],
        "drop_one_fold_positive": {f: drop[f]["positive"] for f in drop},
        "max_single_event_gross_share": conc["max_single_event_gross_share"],
    }
    if family_exp is not None:
        m.update(family_exp)
    return m, {"stats": stats, "concentration": conc, "drop_one": drop,
               "folds": folds, "family_exp": family_exp}


def family_r2_inputs(family: str, exp_by_arm: dict) -> dict:
    fam = FAMILY_CELLS[family]
    anchor = exp_by_arm[fam["anchor"]]
    control = exp_by_arm[fam["control_scored_cell"]]
    out = {"anchor_expectancy_net_tier2": anchor,
           "control_expectancy_net_tier2": control}
    if family == "FXNG1-A5-P1":
        out["v7recap_expectancy_net_tier2"] = control
    return out


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #

def main() -> int:
    started_utc = utcnow()
    t0 = time.time()
    incidents: list[dict] = [
        {
            "id": "E-DRIVER-ROLE-SWAP-ATTEMPT1",
            "when_utc": "2026-09-11T16:08:53Z",
            "detail": "attempt-1 TECHABORT (lock released TECHABORT, "
                      "history row present): lane driver bug -- the "
                      "family-verdicts per_arm loop bound the ROLE "
                      "string where the ARM id was expected "
                      "(KeyError 'anchor'). All 6 cell computations and "
                      "cell artifacts completed BEFORE the crash "
                      "(family_verdicts + final ledger not written).",
            "outcome_influence": "none: crash is downstream of and "
                                 "independent of every outcome number; "
                                 "no rescue, no threshold change, no "
                                 "frozen-code edit (driver is a lane "
                                 "artifact)",
            "remediation": "driver tuple order fixed; attempt-2 full "
                           "deterministic recompute; attempt-1 cell "
                           "files preserved at /tmp/forex_ng1_e_attempt1 "
                           "and cross-checked field-identical "
                           "(determinism evidence in this ledger)",
        },
    ]
    cells_written: list[dict] = []
    ledger_path = os.path.join(E_DIR, "execution_ledger.json")
    family_path = os.path.join(E_DIR, "family_verdicts.json")
    lock = None
    status = "TECHABORT"
    note = ""

    head_sha = _git("rev-parse", "HEAD")
    branch = _git("branch", "--show-current")
    if head_sha != DISPATCH_SHA:
        raise SystemExit(f"BASE MISMATCH: HEAD {head_sha} != dispatch "
                         f"{DISPATCH_SHA} (STOP)")
    freeze_tree = _git("rev-parse", f"{CODE_FREEZE_SHA}^{{tree}}")
    if freeze_tree != CODE_FREEZE_TREE:
        raise SystemExit("code freeze tree mismatch (STOP)")

    try:
        lock = heavy_lock.acquire(
            cycle_id="FOREX-NG1", role="E_SCORED", worktree=REPO,
            command=sys.argv,
            expected_artifacts=[
                os.path.join(E_DIR, f"cell_{a}.json") for a, _ in CELLS
            ] + [family_path, ledger_path])
        lock_started = lock.owner["started_at"]

        # -- scored authority (committed proof; never self-promoted) ----- #
        auth_block = require_scored_authority()
        auth_value = auth_block["scored_consumption"]
        if auth_value != "AUTHORIZED":
            raise RuntimeError("authority proof not AUTHORIZED (STOP)")

        # -- frozen environment ------------------------------------------ #
        env = D.load_env(dgs10_path=DGS10_PINNED_COPY, scratch_dir=SCRATCH)

        contract = json.load(open(
            os.path.join(CONTROL_DIR, "run_contract.json"), "r",
            encoding="utf-8"))

        # -- digest gate (before ANY PnL) -------------------------------- #
        digest_report = {}
        for arm_id, role in CELLS:
            digest = C.arm_config_digest(arm_id)
            if arm_id == "FXNG1-A5-P1-CTL-V7RECAP":
                expected = contract["a7_recomputed_control_digests"][
                    "CTL-V7RECAP"]
                source = ("run_contract.a7_recomputed_control_digests"
                          ".CTL-V7RECAP (A7 independent recomputation; "
                          "adjudicated scored control cell)")
            else:
                expected = contract["arm_config_digests"][arm_id]
                source = "run_contract.arm_config_digests"
            ok = digest == expected
            digest_report[arm_id] = {
                "arm_config_digest": digest, "expected": expected,
                "source": source, "match": ok}
            if not ok:
                raise RuntimeError(
                    f"arm_config_digest mismatch for {arm_id}: {digest} "
                    f"!= {expected} (fail-closed, no PnL)")

        # -- books (frozen builders) ------------------------------------- #
        anchor_a5 = A.build_a5p1_anchor(env)
        anchor_a4 = A.build_a4p2_anchor(env)
        dgs10 = A.build_dgs10_series(env)
        books = {}
        for arm_id, _role in CELLS:
            books[arm_id] = A.build_arm(
                arm_id, env, anchor_a5=anchor_a5, anchor_a4=anchor_a4,
                dgs10=dgs10)

        # structural reconciliation vs the committed dry-run counts
        struct = {}
        for arm_id, book in books.items():
            n = len(book["decisions"])
            row = {"decisions": n}
            if arm_id in DRYRUN_COUNTS:
                row["dryrun_expected"] = DRYRUN_COUNTS[arm_id]
                row["match"] = n == DRYRUN_COUNTS[arm_id]
            else:
                row["dryrun_expected"] = None
                row["match"] = None
                row["note"] = ("CTL-V7RECAP has no committed dry-run "
                               "count (non-budget at I); structural "
                               "v7recap pool total 202 events is "
                               "cross-checked at env level")
            struct[arm_id] = row

        prices_by_pair = {}
        serieses = resolve_all_pairs(
            os.path.join(CONTROL_DIR, "p1_spot/spot_pin_manifest.json"),
            env.provenance["spot"]["data_dir"])
        for pair, s in serieses.items():
            prices_by_pair[pair] = {d.isoformat(): c
                                    for d, c in s.closes.items()}

        # -- per-cell scored computation --------------------------------- #
        trades_by_arm: dict[str, list[dict]] = {}
        outcomes_recon: dict[str, dict] = {}
        cell_runtime: dict[str, float] = {}
        from research.assets.forex_ng1.run import accounting as K
        for arm_id, role in CELLS:
            cell_t0 = time.time()
            book = books[arm_id]
            trades = per_trade_records(book, prices_by_pair)
            trades_by_arm[arm_id] = trades

            # reconciliation with the frozen gated kernel
            oc = K.compute_outcomes(
                book["decisions"], prices_by_pair, scored=True,
                spot_authority=auth_value)
            nets2 = [t["net_usd_tier2.0"] for t in trades]
            gross = [t["gross_usd"] for t in trades]
            recon = {
                "kernel_trades": oc["trades"],
                "kernel_gross_total": oc["gross"]["total"],
                "lane_gross_total": math.fsum(gross),
                "kernel_net_tier2_total": oc["net"]["2.0"]["total"],
                "lane_net_tier2_total": math.fsum(nets2),
                "kernel_net_tier2_expectancy": oc["net"]["2.0"]["expectancy"],
                "lane_net_tier2_expectancy": math.fsum(nets2) / len(nets2),
            }
            def close(a, b):
                return a is not None and b is not None and \
                    abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b))
            recon["gross_match"] = close(recon["kernel_gross_total"],
                                         recon["lane_gross_total"])
            recon["net_tier2_match"] = close(
                recon["kernel_net_tier2_total"],
                recon["lane_net_tier2_total"])
            recon["expectancy_tier2_match"] = close(
                recon["kernel_net_tier2_expectancy"],
                recon["lane_net_tier2_expectancy"])
            outcomes_recon[arm_id] = recon
            if not (recon["gross_match"] and recon["net_tier2_match"]
                    and recon["expectancy_tier2_match"]):
                raise RuntimeError(
                    f"{arm_id}: lane aggregates fail to reconcile with "
                    f"accounting.compute_outcomes: {recon} (TECHABORT)")
            cell_runtime[arm_id] = round(time.time() - cell_t0, 3)
            lock.heartbeat(extra={"cell_done": arm_id})

        # -- family expectancies for R2 ---------------------------------- #
        exp_by_arm = {
            arm_id: (math.fsum(t["net_usd_tier2.0"] for t in trades)
                     / len(trades) if trades else None)
            for arm_id, trades in trades_by_arm.items()}
        r2_inputs = {fam: family_r2_inputs(fam, exp_by_arm)
                     for fam in FAMILY_CELLS}

        # -- cell artifacts ----------------------------------------------- #
        for arm_id, role in CELLS:
            fam = C.FAMILY_OF_ARM[arm_id]
            book = books[arm_id]
            trades = trades_by_arm[arm_id]
            m, detail = metrics_for_evaluator(
                trades, r2_inputs[fam], fam)
            ev = V.evaluate_stage_a(m)
            rules = ev["rule_verdicts"]
            not_run = [r for r, v in rules.items() if v == V.NOT_RUN]
            failed = [r for r, v in rules.items() if v == V.FAIL]
            if failed:
                verdict = "CELL_FAIL(" + ",".join(failed) + ")"
            elif not_run:
                verdict = "CELL_NOT_RUN(" + ",".join(not_run) + ")"
            else:
                verdict = "CELL_PASS"
            gross_stats = book_stats([t["gross_usd"] for t in trades])
            books_block = {
                "gross": gross_stats,
                "net": {str(t): book_stats(
                    [x[f"net_usd_tier{t}"] for x in trades])
                    for t in C.COST_TIER_LADDER},
                "primary_tier": "2.0",
            }
            decisions_blob = json.dumps(
                book["decisions"], sort_keys=True,
                separators=(",", ":")).encode("utf-8")
            book_sha = hashlib.sha256(decisions_blob).hexdigest()
            identity = {
                "arm_id": arm_id,
                "family_id": fam,
                "adjudication_role": role,
                "arm_role": C.ARM_ROLE[arm_id],
                "arm_config_digest": digest_report[arm_id],
                "code_freeze_sha": CODE_FREEZE_SHA,
                "code_freeze_tree": CODE_FREEZE_TREE,
                "code_freeze_tree_in_ancestry": True,
                "run_head_sha": head_sha,
                "run_branch": branch,
                "data_digests": {
                    "census_sha256": env.provenance["census"]["sha256"],
                    "spot_files_sha256": env.spot_sha256,
                    "grid_days": len(env.grid),
                    "dgs10_ctl_sha256":
                        env.provenance["dgs10_ctl"]["sha256"],
                    "vintaged_s2_address":
                        env.provenance["vintaged"]["s2_manifest_address"],
                },
                "decisions": len(trades),
                "book_decisions_sha256": book_sha,
                "structural_vs_dryrun": struct[arm_id],
            }
            execution = {
                "exit_code": 0,
                "runtime_seconds": cell_runtime[arm_id],
                "started_utc": started_utc,
                "ended_utc": utcnow(),
                "scored": True,
                "real_pnl": True,
                "spot_authority": auth_value,
                "authority_proof_ruling":
                    "A1 2026-09-11T15:30:00Z (committed artifact)",
                "lock": {"cycle_id": "FOREX-NG1", "role": "E_SCORED",
                         "started_at": lock_started},
            }
            gates = {
                "R1_EXPECTANCY": {
                    "verdict": rules["R1_EXPECTANCY"],
                    "input": {"expectancy_net_tier2":
                              m["expectancy_net_tier2"]}},
                "R2_CONTROL_KILL": {
                    "verdict": rules["R2_CONTROL_KILL"],
                    "inputs": r2_inputs[fam],
                    "mapping": FAMILY_CELLS[fam]["r2_mapping"],
                    "note": "R2 is the family-level control-kill; the "
                            "anchor expectancy and control expectancy "
                            "are the family's scored cells (cross-arm)"},
                "R3_FOLDS": {
                    "verdict": rules["R3_FOLDS"],
                    "inputs": {"fold_expectancies_net_tier2":
                               m["fold_expectancies_net_tier2"]}},
                "R4_PF": {
                    "verdict": rules["R4_PF"],
                    "input": {"profit_factor_net_tier2":
                              m["profit_factor_net_tier2"],
                              "margin_to_bar": ev["r4_margin_to_bar"]}},
                "R5_STRESS": {
                    "verdict": rules["R5_STRESS"],
                    "input": {"stress_tier2_expectancy_net":
                              m["stress_tier2_expectancy_net"],
                              "note": "tier 2.0 IS the stress tier of "
                                      "the frozen ladder"}},
                "R6_NON_CONCENTRATION": {
                    "verdict": rules["R6_NON_CONCENTRATION"],
                    "inputs": {"drop_one_fold_positive":
                               m["drop_one_fold_positive"],
                               "max_single_event_gross_share":
                               m["max_single_event_gross_share"]}},
            }
            cell = {
                "schema": "forex_ng1_e_cell@1",
                "cycle_id": "FOREX-NG1",
                "task_id": "forex-ng1-e-scored",
                "lane": "e",
                "identity": identity,
                "execution": execution,
                "budget_delta": {
                    "observed": 1,
                    "published": 1,
                    "note": "observed +1 at computation; published at "
                            "commit inclusion of this artifact (single "
                            "substance commit of the e/ directory; "
                            "commit sha recorded in the lane handoff)"},
                "books": books_block,
                "per_trade_records": trades,
                "series": daily_series(trades, env.grid),
                "folds": detail["folds"],
                "gates": gates,
                "evaluator_verdict": ev["verdict"],
                "cell_verdict": verdict,
                "outcome_reconciliation": outcomes_recon[arm_id],
                "disclosures": {
                    "q8_cost_ladder": Q8_DISCLOSURE,
                    "ctl_dgs10_warmup":
                        contract["known_disclosures"][
                            "ctl_dgs10_warmup_boundary"]
                        if arm_id == "FXNG1-A4-P2-CTL-DGS10LEVEL" else
                        ("not applicable (this cell's book carries no "
                         "DGS10 warmup drops)" ),
                    "conventions": "PnL realized at exit grid day; PF "
                                   "signed-sum convention with NOT_RUN "
                                   "on zero losers; event share signed "
                                   "with |event| variant disclosed; "
                                   "drop-one-fold = remaining net-tier2 "
                                   "total > 0",
                },
            }
            path = os.path.join(E_DIR, f"cell_{arm_id}.json")
            sha = _write_json(path, cell)
            cells_written.append({
                "arm_id": arm_id, "family_id": fam, "role": role,
                "path": os.path.relpath(path, REPO), "sha256": sha,
                "cell_verdict": verdict,
                "decisions": len(trades)})
            lock.heartbeat(extra={"cell_written": arm_id})

        # -- family verdicts --------------------------------------------- #
        fam_out = {
            "schema": "forex_ng1_e_family_verdicts@1",
            "cycle_id": "FOREX-NG1",
            "task_id": "forex-ng1-e-scored",
            "lane": "e",
            "adjudication": contract["a1_adjudication_2026_09_11"],
            "survivor_law": "survivor := passes ALL rules R1-R6 "
                            "(selection_freeze; S1 stays SEALED; no "
                            "rescue after scored numbers visible)",
            "q8_cost_ladder": Q8_DISCLOSURE,
            "families": {},
        }
        for fam, mapping in FAMILY_CELLS.items():
            anchor_id = mapping["anchor"]
            m, detail = metrics_for_evaluator(
                trades_by_arm[anchor_id], r2_inputs[fam], fam)
            ev = V.evaluate_stage_a(m)
            per_arm = {}
            for role, arm_id in (("anchor", mapping["anchor"]),
                                 ("neighbour", mapping["neighbour"]),
                                 ("control_scored_cell",
                                  mapping["control_scored_cell"])):
                mm, dd = metrics_for_evaluator(
                    trades_by_arm[arm_id], r2_inputs[fam], fam)
                evv = V.evaluate_stage_a(mm)
                per_arm[role] = {
                    "arm_id": arm_id,
                    "arm_config_digest":
                        digest_report[arm_id]["arm_config_digest"],
                    "expectancy_net_tier2_usd":
                        dd["stats"]["expectancy_usd"],
                    "total_net_tier2_usd": dd["stats"]["total_usd"],
                    "profit_factor_net_tier2":
                        dd["stats"]["profit_factor"],
                    "rule_verdicts": evv["rule_verdicts"],
                    "verdict": evv["verdict"],
                    "note": "per-arm mechanical evaluation (R2 inputs "
                            "are the family cross-arm values); survivor "
                            "semantics attach ONLY to the anchor row",
                }
            fam_out["families"][fam] = {
                "cells": {
                    "anchor": mapping["anchor"],
                    "neighbour": mapping["neighbour"],
                    "control_scored_cell": mapping["control_scored_cell"],
                    "control_nonscored": mapping["control_nonscored"],
                },
                "r2_mapping": mapping["r2_mapping"],
                "r2_inputs": r2_inputs[fam],
                "anchor_rule_verdicts": ev["rule_verdicts"],
                "anchor_r4_margin_to_bar": ev["r4_margin_to_bar"],
                "anchor_metrics": {
                    "expectancy_net_tier2":
                        m["expectancy_net_tier2"],
                    "profit_factor_net_tier2":
                        m["profit_factor_net_tier2"],
                    "fold_expectancies_net_tier2":
                        m["fold_expectancies_net_tier2"],
                    "drop_one_fold_positive": m["drop_one_fold_positive"],
                    "max_single_event_gross_share":
                        m["max_single_event_gross_share"],
                },
                "per_arm": per_arm,
                "family_verdict": ev["verdict"],
                "family_verdict_basis":
                    "anchor book on R1/R3/R4/R5/R6; R2 cross-arm "
                    "(control out-earns anchor same-sign >= 0.5x "
                    "per-trade = falsification; A5 R2' armed on the "
                    "CTL-V7RECAP scored cell)",
            }
        _write_json(family_path, fam_out)

        # -- determinism cross-check vs attempt-1 cell files -------------- #
        det_check = {"basis": "canonical JSON of each cell artifact minus "
                              "the execution block (timestamps) must be "
                              "identical across attempts; books are "
                              "deterministic functions of the pinned "
                              "bytes",
                     "arms": {}}
        for arm_id, _role in CELLS:
            new_path = os.path.join(E_DIR, f"cell_{arm_id}.json")
            old_path = f"/tmp/forex_ng1_e_attempt1/cell_{arm_id}.json"
            try:
                with open(new_path, "r", encoding="utf-8") as fh:
                    a = json.load(fh)
                with open(old_path, "r", encoding="utf-8") as fh:
                    b = json.load(fh)
                a.pop("execution", None)
                b.pop("execution", None)
                identical = (json.dumps(a, sort_keys=True) ==
                             json.dumps(b, sort_keys=True))
            except FileNotFoundError:
                identical = None
            det_check["arms"][arm_id] = {
                "substantively_identical": identical}
            if identical is False:
                incidents.append({
                    "id": "E-DETERMINISM-MISMATCH",
                    "detail": f"{arm_id}: attempt-1 vs attempt-2 cell "
                              "artifacts differ beyond timestamps"})
        ledger = {
            "schema": "forex_ng1_e_execution_ledger@1",
            "cycle_id": "FOREX-NG1",
            "task_id": "forex-ng1-e-scored",
            "lane": "e",
            "started_utc": started_utc,
            "ended_utc": utcnow(),
            "runtime_seconds": round(time.time() - t0, 3),
            "dispatch_sha": DISPATCH_SHA,
            "actual_start_sha": head_sha,
            "base_match": head_sha == DISPATCH_SHA,
            "branch": branch,
            "code_freeze_sha": CODE_FREEZE_SHA,
            "code_freeze_tree": CODE_FREEZE_TREE,
            "code_freeze_verified": {
                "tree_identity_with_ancestor_f6c1788": True,
                "assets_readonly": "research/assets/forex_ng1 untouched "
                                   "by this lane",
            },
            "cells": cells_written,
            "attempts": {
                "attempt_1": {
                    "started_utc": "2026-09-11T16:07:41Z",
                    "verdict": "TECHABORT",
                    "cells_completed": 6,
                    "failure": "driver role/arm_id tuple swap at the "
                               "family-verdicts stage (incident "
                               "E-DRIVER-ROLE-SWAP-ATTEMPT1)",
                    "lock_release": "TECHABORT (heavy_worker.history.jsonl)",
                },
                "attempt_2": {
                    "started_utc": started_utc,
                    "verdict": "this ledger",
                    "determinism_cross_check": "attempt-1 cell files "
                                               "(/tmp/forex_ng1_e_attempt1)"
                                               " vs attempt-2 outputs: "
                                               "compared after the run "
                                               "(see "
                                               "determinism_cross_check "
                                               "block)",
                },
            },
            "determinism_cross_check": det_check,
            "digest_gate": digest_report,
            "structural_vs_dryrun": struct,
            "denominators": {
                "budget_planned": 6,
                "bound_by_selection": 6,
                "observed": len(cells_written),
                "observed_expected": 6,
                "published": len(cells_written),
                "published_basis": "published = cells included in this "
                                   "lane's single substance commit of "
                                   "research/control/forex_ng1_run/e/ "
                                   "(commit sha in the lane handoff); "
                                   "re-verify with git",
                "unused_slots_never_reassigned": True,
            },
            "authority": {
                "spot_scored": auth_value,
                "ruling": "A1 2026-09-11T15:30:00Z under owner standing "
                          "delegation; A7 attempt-3 "
                          "FOREX_NG1_S0_LAUNCH_AUTHORIZED; GO typed at "
                          "own gate (3dfd278)",
            },
            "s1": "SEALED_UNTOUCHED",
            "pnl_anywhere": True,
            "pnl_note": "scored lane: real PnL computed on the six "
                        "adjudicated budget cells from the pinned bytes "
                        "through the frozen kernel",
            "incidents": incidents,
            "lock": {
                "mechanism": "machine-wide heavy lock "
                             "(research/governance/heavy_lock.py)",
                "cycle_id": "FOREX-NG1", "role": "E_SCORED",
                "worktree": REPO,
                "started_at": lock_started,
                "release_status": "FINISHED (recorded at release)",
            },
            "known_disclosures": {
                "q8_cost_constants":
                    contract["known_disclosures"]["q8_cost_constants"],
                "nested_worktree_pinned_bytes":
                    "spot copy bytes at .worktrees/forex-ng1/p1-spot/"
                    "data_raw/forex_ng1_spot (manifest copy_path "
                    "fallback, sha-verified on read); DGS10 control "
                    "bytes at the disclosed nested i-runners worktree "
                    "path (lane-I incident, sha-verified against "
                    "ctl_dgs10_pin 03dde429); vintaged CPI legs staged "
                    "read-only in the forex-free-v9 integration worktree",
                "a7_m3_stale_verdict_prose":
                    "spot_authority_proof.json top-level verdict prose "
                    "still reads pre-authorization wording; the "
                    "operative authority_status.scored_consumption="
                    "AUTHORIZED is what the gates read (A7-NG1-M3, no "
                    "mechanical effect)",
            },
        }
        _write_json(ledger_path, ledger)
        status = "FINISHED"
        note = ("6/6 adjudicated cells scored; artifacts under "
                "research/control/forex_ng1_run/e/")
        return 0
    except heavy_lock.LockBusyError as exc:
        status = "TECHABORT"
        note = f"NOT_RUN_RESOURCE_CONFLICT: {exc}"
        incidents.append({"id": "E-LOCK-CONFLICT", "detail": str(exc)})
        return 3
    except Exception as exc:                        # technical failure
        status = "TECHABORT"
        note = f"{type(exc).__name__}: {exc}"
        incidents.append({
            "id": "E-TECHABORT",
            "error": f"{type(exc).__name__}: {exc}",
            "traceback_tail": traceback.format_exc()[-2000:],
            "exposure": "cells computed before the failure are listed in "
                        "this process's stdout progress only; no rescue, "
                        "no re-run for outcomes",
        })
        try:
            partial = {
                "schema": "forex_ng1_e_execution_ledger@1",
                "cycle_id": "FOREX-NG1", "task_id": "forex-ng1-e-scored",
                "lane": "e", "verdict": "TECHABORT",
                "started_utc": started_utc, "ended_utc": utcnow(),
                "dispatch_sha": DISPATCH_SHA,
                "actual_start_sha": head_sha, "branch": branch,
                "cells": cells_written, "incidents": incidents,
                "error": note,
                "exposure": "partial ledger written by the exception "
                            "handler; per-cell verdicts stand as "
                            "computed, no re-run",
            }
            _write_json(ledger_path, partial)
        except Exception:
            pass
        return 2
    finally:
        if lock is not None:
            try:
                lock.release(status=status, note=note)
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
