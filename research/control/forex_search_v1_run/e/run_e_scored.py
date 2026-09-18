#!/usr/bin/env python
"""FOREX-SEARCH-V1 E-lane SCORED runner (lane fsearch-e, plan §9 E).

The scored execution authorized by the owner GO phrase
`GO FOREX SEARCH V1 SCORED EXECUTION` typed at this cycle's own gate
(recorded in the cycle registry at 029fa5d5) after A7 prelaunch
AUTHORIZED 0 HIGH/CRITICAL (d4350dcd). AT MOST 3 scored cells: the three
frozen S-selected arms on the real pinned P-13 archive. D2 is SKIPPED per
owner amendment §3b (R0 NOT_RUN — never computed, never inferred).

MANDATORY ORDER (fail-closed at every step):
  1. machine-wide heavy lock (governance.heavy_lock — poll 60s backoff,
     bounded; NOT_RUN_RESOURCE_CONFLICT otherwise; never kills a holder)
  2. staging: fresh /tmp extraction of the P-13 archive members, every
     member digest verified against p0/manifest_pin.json AND the
     plan-frozen prefixes in p0_census.PAIR_SOURCES; tarball digests
     verified against SHA256SUMS.txt + the pin; ng1 copy byte-identity
     re-verified; the frozen GO-gated loader (i_engine.load_staging_legs)
     re-verifies everything a second time (runtime redirection of the
     p0_census.STAGING attribute ONLY — no frozen file is edited)
  3. positions freeze gate: rebuilt positions digests MUST equal
     85c8f875…/57eed8b9…/7eee7cf0… (s/selection_freeze.json) —
     INPUT_MISMATCH is a fail-closed stop
  4. E run: the 3 arms through the frozen engines — dual books
     (price-only; conservatively-financed 1.5 bps/fill x2 fills + 1.7
     bps/night x1 rollover; STRESS 2.0 on everything), per-fold
     force-flat, per-period per-session series persisted (P-11),
     controls (CLOCK-ONLY, CTL-COMPLEMENT, R4 trend-only, weekday fired
     census, serial-clustering census, USD basket, P-20 re-check)
  5. adjudication: adjudicate.py full battery (ordered first-binding
     kills R1–R6, K6 NOT_ADJUDICABLE, dual-books, Stage-A with the DSR
     gate N=33 alpha 0.10 computed before any survivor name, PBO NOT_RUN
     + R0 NOT_RUN labels verbatim, budget counter 3/3)
  6. lock released (FINISHED / FAILED / TECHABORT with note)
  7. terminal outcome: the §11 prewritten names via adjudicate_cycle —
     a REJECT_ALL is a correct kill, a success of governance.

NO engine/adjudicate/manifest edit of any kind: the frozen modules are
consumed read-only; this file only ORCHESTRATES them and persists the
scored artifacts under e/.
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # keep p0/, i/ byte-clean (read-only lanes)

import hashlib
import json
import os
import platform
import tarfile
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/forex-search-v1/integration")
RUN = WT / "research/control/forex_search_v1_run"
E_DIR = RUN / "e"
I_DIR = RUN / "i"
GOV_DIR = WT / "research"

DISPATCH_SHA = "d4350dcdf3c34dc161cb91a0634efd1617aaea6c"
BRANCH = "orca/forex-search-v1-integration"
GO_PHRASE = "GO FOREX SEARCH V1 SCORED EXECUTION"
GO_AUTHORITY = ("owner-typed exact GO phrase at this cycle's own gate; "
                "recorded in plans/CYCLE_REGISTRY.json at commit 029fa5d5 "
                "after A7 prelaunch AUTHORIZED 0 HIGH/CRITICAL (d4350dcd)")
STRESS = 2.0
LOCK_POLL_BACKOFF_S = 60
LOCK_POLL_MAX_S = 300  # outer shell poll observes FREE first; safety net only

sys.path.insert(0, str(GOV_DIR))
sys.path.insert(0, str(I_DIR))

from governance import heavy_lock  # noqa: E402
import i_engine as eng  # noqa: E402
import adjudicate as adj  # noqa: E402


class StopRun(Exception):
    """Fail-closed stop with the incident code carried to the handoff."""

    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def sha256_obj(obj) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def git_head() -> str:
    import subprocess
    out = subprocess.run(["git", "-C", str(WT), "rev-parse", "HEAD"],
                         capture_output=True, text=True, check=True)
    return out.stdout.strip()


# ------------------------------------------------------------------- staging

def verify_and_extract_staging(runlog: dict) -> tuple[Path, dict]:
    """Fresh /tmp extraction + full digest verification of the P-13 pin.

    Verifies (a) every tarball listed in manifest_pin.json against
    SHA256SUMS.txt and the pinned expected digests, (b) every needed
    member's sha256 against the pin AND the plan-frozen prefix in
    p0_census.PAIR_SOURCES, (c) ng1 copy byte-identity. Returns the fresh
    staging dir + a verification record. Nothing outside /tmp is written.
    """
    pc = eng.p0()
    pin = json.loads((eng.P0_DIR / "manifest_pin.json").read_text())
    sums_path = Path(pin["archive_root"]) / "SHA256SUMS.txt"
    expected_sums = {}
    for line in sums_path.read_text().splitlines():
        if line.strip():
            d, name = line.split()
            expected_sums[name] = d
    tarball_rows = {}
    for name, expect in sorted(pin["tarball_sha256_vs_SHA256SUMS"].items()):
        f = Path(pin["archive_root"]) / name
        dig = sha256_file(f)
        row = {"expected_pin": expect["expected"], "expected_sums": expected_sums.get(name),
               "measured": dig,
               "match_pin": dig == expect["expected"],
               "match_sums": dig == expected_sums.get(name)}
        if not (row["match_pin"] and row["match_sums"]):
            raise StopRun("FROZEN_SHA_MISMATCH", f"tarball digest drift: {name}")
        tarball_rows[name] = row
    runlog["tarball_digests_verified"] = tarball_rows

    needed = {}   # member -> {leg, expect}
    for leg in eng.LEGS:
        archive, member, expect = pc.PAIR_SOURCES[leg]
        needed[member] = {"leg": leg, "expect": expect, "archive": archive}
    ng1 = {"AUDUSD": "data_raw/forex_ng1_spot/AUDUSD.json",
           "GBPUSD": "data_raw/forex_ng1_spot/GBPUSD.json",
           "NZDUSD": "data_raw/forex_ng1_spot/NZDUSD.json",
           "USDCAD": "data_raw/forex_ng1_spot/USDCAD.json"}
    for leg, member in ng1.items():
        # the ng1 byte-identical COPIES are served from the ng1 spot_ctl
        # archive (measured member layout 2026-09-18), not from the v9 pair
        # archive pinned in pin["pairs"][leg]["archive"]
        needed[member] = {"leg": f"{leg}(ng1 copy)",
                          "expect": pin["pairs"][leg]["sha256"],
                          "archive": "forex-ng1_spot_ctl.tar.gz"}

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    fresh = Path(f"/tmp/fsearch_p0_staging_e_{stamp}")
    fresh.mkdir(parents=True, exist_ok=False)
    member_rows = {}
    by_archive = {}
    for member, meta in needed.items():
        by_archive.setdefault(meta["archive"], []).append((member, meta))
    for archive, members in sorted(by_archive.items()):
        with tarfile.open(Path(pin["archive_root"]) / archive, "r:gz") as tar:
            names = set(tar.getnames())
            for member, meta in members:
                if member not in names:
                    raise StopRun("INPUT_MISMATCH",
                                  f"member {member} absent from {archive}")
                src = tar.extractfile(member)
                if src is None:
                    raise StopRun("INPUT_MISMATCH",
                                  f"member {member} is not a file in {archive}")
                data = src.read()
                dest = fresh / member
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
                dig = hashlib.sha256(data).hexdigest()
                base_leg = meta["leg"].replace("(ng1 copy)", "")
                ok_pin = dig == pin["pairs"][base_leg]["sha256"]
                ok_plan = dig == meta["expect"]
                member_rows[member] = {"leg": meta["leg"], "archive": archive,
                                       "sha256": dig,
                                       "match_manifest_pin": bool(ok_pin),
                                       "match_plan_frozen_prefix": bool(ok_plan)}
                if not (ok_pin and ok_plan):
                    raise StopRun("FROZEN_SHA_MISMATCH",
                                  f"member digest drift: {member}")
    # ng1 byte-identity vs the pinned v9 copies (pin law re-measured)
    ng1_identity = {}
    for leg, member in ng1.items():
        v9 = pin["pairs"][leg]["member"]
        ng1_identity[leg] = sha256_file(fresh / member) == sha256_file(fresh / v9)
    if not all(ng1_identity.values()):
        raise StopRun("INPUT_MISMATCH", f"ng1 copy identity broken: {ng1_identity}")
    runlog["staging_members_verified"] = member_rows
    runlog["ng1_copy_identity_remeasured"] = ng1_identity
    runlog["fresh_staging_dir"] = str(fresh)
    return fresh, pin


# ---------------------------------------------------------------------- main

def main() -> int:
    t0 = time.monotonic()
    runlog: dict = {"schema": "fsearch_e_run_log@1", "started_utc": utcnow(),
                    "steps": []}

    def step(name: str, **kw):
        runlog["steps"].append({"step": name, "at_utc": utcnow(),
                                "elapsed_s": round(time.monotonic() - t0, 3),
                                **kw})

    # -- 0. frozen checkout + GO authorization (fail-closed preflight)
    measured_head = git_head()
    if measured_head != DISPATCH_SHA:
        print(json.dumps({"stop": "FROZEN_SHA_MISMATCH",
                          "detail": f"HEAD {measured_head} != {DISPATCH_SHA}"}))
        return 2
    step("preflight_head", head=measured_head, branch=BRANCH)
    os.environ["FOREX_SEARCH_V1_GO_PHRASE"] = GO_PHRASE  # owner-typed phrase
    lock = None
    stop: StopRun | None = None
    fatal: str | None = None
    verdict_payload: dict | None = None
    try:
        # -- 1. heavy lock (machine-wide; poll, never kill)
        deadline = time.monotonic() + LOCK_POLL_MAX_S
        while True:
            try:
                lock = heavy_lock.acquire(
                    cycle_id="FOREX-SEARCH-V1",
                    role="SCORED_E_RUN_HEAVY",
                    worktree=str(WT),
                    command=[sys.executable, str(Path(__file__).resolve())],
                    expected_artifacts=[
                        "research/control/forex_search_v1_run/e/e_run_verdict.json",
                        "research/control/forex_search_v1_run/e/p11_series/",
                        "research/control/forex_search_v1_run/e/cells/"])
                break
            except heavy_lock.LockBusyError as e:
                if time.monotonic() >= deadline:
                    raise StopRun("NOT_RUN_RESOURCE_CONFLICT", str(e)) from e
                time.sleep(LOCK_POLL_BACKOFF_S)
        step("heavy_lock_acquired", role="SCORED_E_RUN_HEAVY")

        # -- 2. staging verify + fresh extraction; frozen loader re-verifies
        fresh_dir, pin = verify_and_extract_staging(runlog)
        step("staging_verified", fresh_dir=str(fresh_dir))
        pc = eng.p0()
        pc.STAGING = fresh_dir  # runtime redirection ONLY — no frozen file edited
        legs = eng.load_staging_legs()  # GO-gated; re-verifies every digest
        step("frozen_staging_loader_ok", legs=eng.LEGS)

        # calendar + folds rebuilt and compared to the frozen artifacts
        freeze = eng.load_freeze()
        cal = pc.calendar_census(legs)
        master = cal["master_calendar"]
        master_sha = sha256_obj(master)
        frz_master_sha = freeze["inputs"]["master_calendar"]["sha256"]
        if master_sha != frz_master_sha or len(master) != \
                freeze["inputs"]["master_calendar"]["len"]:
            raise StopRun("INPUT_MISMATCH",
                          f"rebuilt master calendar {master_sha}/{len(master)} "
                          f"!= frozen {frz_master_sha}/"
                          f"{freeze['inputs']['master_calendar']['len']}")
        folds = pc.make_folds(master)
        frozen_folds = json.loads((eng.P0_DIR / "folds_freeze.json").read_text())
        if json.dumps(folds, sort_keys=True) != json.dumps(frozen_folds, sort_keys=True):
            raise StopRun("INPUT_MISMATCH", "rebuilt folds != frozen folds_freeze.json")
        step("calendar_folds_verified", master_sha=master_sha,
             boundaries=folds["boundaries_index"])

        # -- 3. positions freeze gate + -- 4/5. books, controls, adjudication
        arm_ctxs, positions_by_arm, arm_records = [], {}, []
        p20_frozen = freeze["p20_matrix_selected"]
        for sel in sorted(freeze["selections"], key=lambda s: s["rank"]):
            cfg = sel["config_manifest_excerpt_verbatim"]
            cid = sel["config_id"]
            t_arm = time.monotonic()
            pos = eng.build_positions(cfg, legs, master, folds, eng.LEGS)
            rebuilt_digest = eng.positions_digest(pos, eng.LEGS)
            gate_ok = rebuilt_digest == sel["positions_digest"]
            if not gate_ok:
                raise StopRun("INPUT_MISMATCH",
                              f"{cid} rebuilt positions digest {rebuilt_digest} "
                              f"!= frozen {sel['positions_digest']}")
            trades = eng.build_trades(pos, legs, master, folds, eng.LEGS)
            price, financed = eng.ladder_bps(trades, STRESS)
            dual = eng.dual_books_check(trades, STRESS)
            price_summ = eng.summarize_book(price, trades)
            fin_summ = eng.summarize_book(financed, trades)

            # controls (same grid/warmup/gating/ladder)
            comp_pos = eng.build_control_positions("complement", cfg, legs,
                                                   master, folds, eng.LEGS)
            comp_trades = eng.build_trades(comp_pos, legs, master, folds, eng.LEGS)
            co_pos = eng.build_control_positions("clock_only", cfg, legs,
                                                 master, folds, eng.LEGS)
            co_trades = eng.build_trades(co_pos, legs, master, folds, eng.LEGS)
            trend_only_trades = None
            if cid != "FSS-CLOCK-COND-MONTHPOS-SECOND-LONG":  # R4 NOT_ADJUDICABLE
                to_pos = eng.build_control_positions("trend_only", cfg, legs,
                                                     master, folds, eng.LEGS)
                trend_only_trades = eng.build_trades(to_pos, legs, master,
                                                     folds, eng.LEGS)
            weekday = eng.weekday_share_of_firings(pos, master, eng.LEGS)
            serial = eng.serial_clustering_census(pos, eng.LEGS)
            mut = eng.pit_mutated_positions(cfg, legs, master, folds, eng.LEGS)

            # USD basket + R6 correlations (financed stress-primary daily bps)
            usd = eng.usd_basket_series(legs, master, eng.LEGS)
            fin_daily = eng.daily_pnl_series(trades, financed, master)
            per_leg_corr, per_leg_status = {}, {}
            for ln in eng.LEGS:
                rho, status = eng.pearson(
                    eng.daily_pnl_series(trades, financed, master, ln),
                    usd["per_leg_usd_side_bps"][ln])
                per_leg_corr[ln], per_leg_status[ln] = rho, status
            pooled_corr, pooled_status = eng.pearson(fin_daily, usd["basket_bps"])

            # rebuilt fired census counts (integrity disclosure vs the pin)
            fold_of = {mi: pc.fold_of(folds, mi) for mi in range(len(master))}
            fired_by_fold = {1: 0, 2: 0, 3: 0}
            for ln in eng.LEGS:
                for mi in np.nonzero(pos[ln])[0]:
                    fired_by_fold[fold_of[int(mi)]] += 1

            ctx = {
                "config_id": cid,
                "family": cfg["family"],
                "trades": trades,
                "stress": STRESS,
                "folds": folds,
                "master": master,
                "complement_trades": comp_trades,
                "trend_only_trades": trend_only_trades,
                "trend_only_definition": cfg.get("r4_trend_only_book"),
                "clock_only_trades": co_trades,
                "weekday_census": weekday,
                "usd": {"per_leg_corr": per_leg_corr, "pooled_corr": pooled_corr,
                        "per_leg_status": per_leg_status,
                        "pooled_status": pooled_status,
                        "construction": "financed stress-2.0 daily bps of the "
                                        "arm vs the same-leg USD-side "
                                        "open->close basket series "
                                        "(i_engine.usd_basket_series); pooled "
                                        "= all-leg daily series vs the "
                                        "equal-weighted USD basket"},
                "shadows": None,  # no macro source acquired this cycle: NOT_RUN kill-only
                "mutated_positions": mut,
                "serial_clustering": serial,
            }
            arm_verdict = adj.adjudicate_arm(ctx)
            arm_ctxs.append(ctx)
            positions_by_arm[cid] = pos

            # informational (frozen functions, clearly labelled) — Stage-A
            # itself adjudicates ONLY ordered-battery survivors.
            p11 = adj.p11_per_period_series(ctx)
            dsr_info = adj.dsr_gate(p11, n_trials=adj.DSR_FROZEN_GRID_N,
                                    alpha=adj.DSR_ALPHA)
            mdd_fin = eng.max_drawdown_frac(fin_daily)
            gross_mean = (float(np.mean([t["gross_bps"] for t in trades]))
                          if trades else None)
            first_binding = next(
                (r["rule"] for r in arm_verdict["ordered_rules"]
                 if r["verdict"] == "KILL"), None)
            arm_records.append({
                "config_id": cid, "family": cfg["family"],
                "rank": sel["rank"],
                "positions_digest_rebuilt": rebuilt_digest,
                "positions_digest_frozen": sel["positions_digest"],
                "positions_freeze_gate": "PASS" if gate_ok else "INPUT_MISMATCH",
                "fired_by_fold_rebuilt": {str(k): v for k, v in fired_by_fold.items()},
                "fired_by_fold_frozen": sel["config_manifest_excerpt_verbatim"]
                                          ["p0_fired_census"]["fired_by_fold"],
                "n_trades": len(trades),
                "books_stress_2_0": {
                    "price_only": price_summ,
                    "conservatively_financed": fin_summ,
                    "worst_case_round_trip_bps": eng.WORST_CASE_ROUND_TRIP_BPS,
                    "informational_mdd_financed_frac": mdd_fin,
                    "informational_mean_gross_bps": gross_mean,
                    "informational_dsr_n33_alpha0_10": dsr_info,
                    "informational_note": ("Stage-A (MDD/concentration/fold-"
                                           "positive-share/DSR) adjudicates "
                                           "ONLY ordered-battery survivors; "
                                           "informational_* rows are frozen-"
                                           "function recomputations recorded "
                                           "for the audit trail, never a "
                                           "rescue")},
                "dual_books": dual,
                "usd_status": {"per_leg": per_leg_status, "pooled": pooled_status},
                "first_binding_kill": first_binding,
                "arm_verdict": arm_verdict,
                "p11_persisted_digest": p11.get("series_digest"),
                "elapsed_s": round(time.monotonic() - t_arm, 3),
            })
            lock.heartbeat(extra={"arm_done": cid})
            step("arm_scored", config_id=cid, n_trades=len(trades),
                 first_binding_kill=first_binding)

        # cycle adjudication + P-20 re-check from the REBUILT series
        cycle = adj.adjudicate_cycle(arm_ctxs, positions_by_arm, eng.LEGS,
                                     frozen_matrix=p20_frozen)
        step("cycle_adjudicated", outcome=cycle["proposed_outcome_name"])

        # -- persist artifacts
        (E_DIR / "cells").mkdir(parents=True, exist_ok=True)
        (E_DIR / "p11_series").mkdir(parents=True, exist_ok=True)
        for rec in arm_records:
            cell = {
                "schema": "fsearch_e_cell_record@1",
                "cycle": "FOREX-SEARCH-V1", "lane": "fsearch-e",
                "scored_cell": True, "go_phrase": GO_PHRASE,
                "go_authority": GO_AUTHORITY,
                "base_sha": DISPATCH_SHA,
                "config_id": rec["config_id"],
                "stress_multiplier_primary": STRESS,
                "cell": rec,
            }
            blob = json.dumps(cell, indent=1, sort_keys=True) + "\n"
            p = E_DIR / "cells" / f"cell_rank{rec['rank']}_{rec['config_id']}.json"
            p.write_text(blob)
            rec["cell_record_path"] = str(p)
            rec["cell_record_sha256"] = sha256_file(p)
            # P-11 per-period series file (persisted for DSR reproducibility)
            ctx = next(c for c in arm_ctxs if c["config_id"] == rec["config_id"])
            p11 = adj.p11_per_period_series(ctx)
            p11["config_id"] = rec["config_id"]
            p11["survivor_stage_a_adjudicated"] = \
                rec["arm_verdict"]["stage_a"]["verdict"] == "PASS"
            p11["law"] = adj.P11_LAW
            bp = (E_DIR / "p11_series" / f"p11_{rec['config_id']}.json")
            bp.write_text(json.dumps(p11, indent=1, sort_keys=True) + "\n")
            rec["p11_file_path"] = str(bp)
            rec["p11_file_sha256"] = sha256_file(bp)

        # frozen P-11 batch writer: applicable only when EVERY arm carries a
        # Stage-A subgates block (i.e. no arm was killed before Stage-A)
        p11_batch = None
        try:
            p11_batch = {
                "path": str(E_DIR / "p11_series_all_arms.json"),
                "sha256": adj.persist_p11_series(cycle["arms"],
                                                 E_DIR / "p11_series_all_arms.json")}
        except Exception as e:  # KeyError on non-survivor arms — expected
            p11_batch = {"applicable": False,
                         "reason": f"frozen batch writer requires stage_a "
                                   f"subgates on every arm ({type(e).__name__}); "
                                   f"per-arm P-11 files under e/p11_series/ are "
                                   f"the persisted series"}

        verdict_payload = {
            "schema": "fsearch_e_run_verdict@1",
            "cycle": "FOREX-SEARCH-V1",
            "real_cycle": "FOREX-SEARCH-V1",
            "orchestration_cycle": "ZCODE-ORCHESTRATION-V3",
            "lane": "fsearch-e",
            "role": "quant-implementer",
            "phase": "E (scored execution, plan §9)",
            "base_sha": DISPATCH_SHA,
            "measured_head": measured_head,
            "branch": BRANCH,
            "go_authorization": {"go_phrase": GO_PHRASE,
                                 "authority": GO_AUTHORITY,
                                 "scored_cells_authorized_max": 3},
            "scored_cell_budget": cycle["scored_cell_budget"],
            "staging_verification": {k: runlog[k] for k in (
                "tarball_digests_verified", "staging_members_verified",
                "ng1_copy_identity_remeasured", "fresh_staging_dir")},
            "master_calendar_sha256": master_sha,
            "fold_boundaries": folds["boundaries_index"],
            "positions_freeze_gate": "PASS (all three rebuilt digests equal the "
                                     "frozen 85c8f875/57eed8b9/7eee7cf0 digests)",
            "arms": arm_records,
            "cycle_verdict": cycle,
            "terminal_outcome_name": cycle["proposed_outcome_name"],
            "terminal_outcome_note": (
                "prewritten §11 name from the frozen adjudicator; every result "
                "carries R0_NOT_RUN + PBO_NOT_RUN + the §3/§4-F4 disclosures "
                "verbatim (labels); a REJECT_ALL is a correct kill — a success "
                "of governance"),
            "p11_batch_writer": p11_batch,
            "environment": {"python": platform.python_version(),
                            "numpy": np.__version__,
                            "platform": platform.platform()},
            "run_log": runlog,
            "labels": adj.verdict_labels(),
            "finished_utc": utcnow(),
        }
        out = E_DIR / "e_run_verdict.json"
        out.write_text(json.dumps(verdict_payload, indent=1, sort_keys=True) + "\n")
        step("verdict_written", path=str(out), sha256=sha256_file(out))
        lock.heartbeat(extra={"outcome": cycle["proposed_outcome_name"]})
        print(json.dumps({"ok": True,
                          "terminal_outcome": cycle["proposed_outcome_name"],
                          "survivors": cycle["survivors"],
                          "budget": cycle["scored_cell_budget"],
                          "verdict_path": str(out)}, indent=1))
        return 0
    except StopRun as e:
        stop = e
        step("STOP", code=e.code, detail=e.detail)
        print(json.dumps({"ok": False, "stop": e.code, "detail": e.detail}))
        return 3
    except Exception as e:  # unexpected defect on real data -> TECHABORT
        fatal = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
        step("FATAL", error=fatal[-4000:])
        print(json.dumps({"ok": False, "stop": "TECHABORT",
                          "detail": fatal[-2000:]}))
        return 4
    finally:
        if lock is not None:
            if stop is not None:
                lock.release(status="TECHABORT" if stop.code != "NOT_RUN_RESOURCE_CONFLICT"
                             else "FAILED",
                             note=f"{stop.code}: {stop.detail}"[:1000])
            elif fatal is not None:
                lock.release(status="TECHABORT", note=fatal[-1000:])
            else:
                lock.release(status="FINISHED",
                             note=(verdict_payload or {}).get("terminal_outcome_name",
                                                              "no verdict payload")[:500])
            runlog["lock_released_utc"] = utcnow()
        # persist the run log whatever happened (fail-closed evidence)
        try:
            (E_DIR / "e_run_log.json").write_text(
                json.dumps(runlog, indent=1, sort_keys=True) + "\n")
        except OSError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
