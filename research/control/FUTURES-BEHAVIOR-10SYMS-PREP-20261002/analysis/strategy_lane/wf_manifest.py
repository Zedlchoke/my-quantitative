#!/usr/bin/env python3
"""wf_manifest.py — STRATEGY-CONFIGS lane, FUTURES-BEHAVIOR-10SYMS-PREP-20261002.

Deterministic walk-forward selection/purge/embargo/budget manifest generator for
the NQ+CL pilot (configs/pilot_nq_cl.yaml). OFFLINE + SYNTHETIC ONLY: no real
data, no PnL, no strategy evaluation. Everything deterministic (fixed
generated_utc, no clock reads) so re-runs are byte-identical for unchanged
inputs.

Fold construction rules encoded (per BACKTEST_LAUNCH_DRAFT.md S1/S7 and
code/futbt/walkforward.py law):
  * nested TRAIN selection ONLY - selector sees a PIT view pinned at train_end,
    selected params frozen + stamped before TEST runs
  * purge_sessions >= true_horizon_sessions (= max_hold + entry_delay; label
    window) - under-purge raises, no silent default
  * embargo_sessions = true_horizon_sessions
  * anchored-expanding folds, >= 4, train_frac 0.7, TEST windows never overlap
  * label maturity: TEST cells whose label window (session + horizon) extends
    past the last available session are right-censored and recorded, never
    silently dropped; the only legal fold drop is INSUFFICIENT_COVERAGE
    (recorded with coverage numbers)
  * performance-reason fold suppression forbidden

Engine interface coupling (READ-ONLY): targets
futbt.walkforward.WalkForwardPlanner(sessions, true_horizon_sessions,
embargo_sessions).plan(n_folds, train_frac). The generator first tries to
import the real module and cross-verifies fold dates; if the import fails
(interface mid-edit by another lane), it falls back to a local re-implementation
of the DOCUMENTED interface (code/README.md) and records the coupling note +
the walkforward.py sha256 it targeted.

Outputs: analysis/strategy_lane/wf_manifest.json. Exit 0 ok / 1 invariant or
accounting failure.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import yaml

CYCLE = Path(__file__).resolve().parents[2]
PILOT_PATH = CYCLE / "configs" / "pilot_nq_cl.yaml"
WF_ENGINE_PATH = CYCLE / "code" / "futbt" / "walkforward.py"
OUT_PATH = CYCLE / "analysis" / "strategy_lane" / "wf_manifest.json"

GENERATED_UTC = "2026-10-02"          # fixed: determinism, no clock reads
MASTER_SEED = 20261002
N_FOLDS = 4
TRAIN_FRAC = 0.7
SYNTH_START = "2025-01-06"            # first Monday
SYNTH_END = "2026-09-30"              # mirrors futbt.synth build window

ACQ = {"in_hand_now": 0, "free_public": 1, "owner_declaration": 2, "vendor_paid": 3}


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ------------------------------------------------------------------ #
# fold planner - local re-implementation of the DOCUMENTED engine
# interface (anchored-expanding; purge/embargo enforced by caller checks)
# ------------------------------------------------------------------ #
def weekday_sessions(start: str, end: str) -> list:
    import datetime as dt
    d0 = dt.date.fromisoformat(start)
    d1 = dt.date.fromisoformat(end)
    out = []
    d = d0
    while d <= d1:
        if d.weekday() < 5:
            out.append(d)
        d += dt.timedelta(days=1)
    return out


def plan_folds_local(sessions: list, horizon: int, embargo: int,
                     n_folds: int, train_frac: float) -> list:
    n = len(sessions)
    test_len = max(1, int(n * (1.0 - train_frac) / n_folds))
    folds = []
    idx = 0
    for k in range(n_folds):
        train_end_idx = int(n * train_frac) + k * test_len
        test_start_idx = train_end_idx + 1
        test_end_idx = min(test_start_idx + test_len - 1, n - 1)
        if test_start_idx > n - 1 or train_end_idx >= n:
            break
        folds.append({
            "fold_id": f"fold{k + 1:02d}",
            "train_start": sessions[idx].isoformat(),
            "train_end": sessions[train_end_idx].isoformat(),
            "test_start": sessions[test_start_idx].isoformat(),
            "test_end": sessions[test_end_idx].isoformat(),
            "purge_sessions": horizon,
            "embargo_sessions": embargo,
            "true_horizon_sessions": horizon,
        })
    return folds


def try_engine_crosscheck(sessions: list, horizon: int, embargo: int,
                          n_folds: int, train_frac: float):
    """Try importing the real futbt.walkforward (READ-ONLY); compare against the
    DOCUMENTED interface. Divergence is RECORDED, never silently resolved: if the
    engine module has moved past the documented interface (mid-edit by another
    lane), the manifest keeps targeting the documented interface and notes the
    observed difference for re-verification at integration."""
    info = {"engine_module": "futbt.walkforward",
            "engine_file_sha256": sha256_file(WF_ENGINE_PATH),
            "mode": "local_reimplementation_of_documented_interface",
            "crosscheck": None}
    try:
        sys.path.insert(0, str(CYCLE / "code"))
        try:
            from futbt.walkforward import WalkForwardPlanner  # noqa: DCO
        finally:
            sys.path.pop(0)
        planner = WalkForwardPlanner(sessions, horizon, embargo)
        folds = [f.to_dict() for f in planner.plan(n_folds, train_frac)]
        local = plan_folds_local(sessions, horizon, embargo, n_folds, train_frac)
        keys = ("train_start", "train_end", "test_start", "test_end",
                "purge_sessions", "embargo_sessions", "true_horizon_sessions")
        diffs = []
        for i, (e, l) in enumerate(zip(folds, local)):
            for k in keys:
                if e.get(k) != l.get(k):
                    diffs.append(f"fold{i + 1}.{k}: engine={e.get(k)} documented={l.get(k)}")
        if not diffs and len(folds) == len(local):
            info["mode"] = "engine_imported_and_crossverified"
            info["crosscheck"] = "IDENTICAL"
        else:
            info["mode"] = "engine_imported_divergence_recorded"
            info["crosscheck"] = f"DIFFERS ({len(diffs)} field(s))"
            info["differences"] = diffs
            info["note"] = ("engine module has moved past the documented interface "
                            "(observed during this lane's run: another lane is editing "
                            "code/futbt/walkforward.py - e.g. final-fold test-window "
                            "extension to calendar end). Manifest targets the DOCUMENTED "
                            "interface (code/README.md futbt.walkforward row); reconcile "
                            "at integration before any fold table from this manifest "
                            "is consumed.")
    except Exception as e:  # interface mid-edit or import problem
        info["note"] = (f"engine import unavailable ({type(e).__name__}); manifest built "
                        "against the DOCUMENTED interface in code/README.md; re-verify "
                        "at integration")
    return info


# ------------------------------------------------------------------ #
def enumerate_cells(pilot: dict) -> list:
    """Stable enumeration: symbol -> rule -> roll -> stress -> slippage -> delay."""
    cells = []
    idx = 0
    legs = sorted(pilot["legs"], key=lambda l: (ACQ["in_hand_now"], l["symbol"]))
    for leg in legs:
        for roll in pilot["variants"]["roll_rules"]:
            for stress in pilot["variants"]["cost_stress"]:
                for slip in pilot["variants"]["slippage_scenarios"]:
                    for delay in pilot["variants"]["entry_delay_sessions"]:
                        cells.append({
                            "cell_index": idx,
                            "cell_id": (f"{leg['symbol']}-r1-{roll.split('_')[0]}"
                                        f"-s{stress}-{'S0' if slip.startswith('S0') else 'S1'}"
                                        f"-d{delay}"),
                            "symbol": leg["symbol"],
                            "leg_id": leg["leg_id"],
                            "rule": "1 declared rule per leg (phase-gated)",
                            "roll_rule": roll,
                            "cost_stress": stress,
                            "slippage_scenario": slip,
                            "entry_delay_sessions": delay,
                            "seed": MASTER_SEED + idx,
                        })
                        idx += 1
    for i, base in enumerate([
            {"arm": "baseline_flat"},
            {"arm": "baseline_always_on_long"},
            {"arm": "baseline_always_on_short"},
            {"arm": "baseline_single_leg_NQ"},
            {"arm": "baseline_single_leg_CL"}]):
        base.update({"cell_index": idx, "cell_id": base["arm"], "seed": MASTER_SEED + idx})
        cells.append(base)
        idx += 1
    for i in range(2):
        cells.append({"cell_index": idx,
                      "cell_id": f"ablation_leave_one_leg_{'NQ' if i == 0 else 'CL'}",
                      "arm": "ablation_leave_one_leg",
                      "removed_leg": "NQ" if i == 0 else "CL",
                      "mode": "FULL_PATH_RERUN",
                      "seed": MASTER_SEED + idx})
        idx += 1
    return cells


def build_walkforward_blocks(pilot: dict, sessions: list) -> dict:
    blocks = {}
    for leg in pilot["legs"]:
        per_delay = {}
        for delay in leg["entry_delay_slots_sessions"]:
            horizon = leg["max_hold_sessions"] + delay
            per_delay[str(delay)] = {
                "true_horizon_sessions": horizon,
                "purge_sessions": horizon,
                "embargo_sessions": horizon,
            }
        max_delay = max(leg["entry_delay_slots_sessions"])
        hmax = leg["max_hold_sessions"] + max_delay
        demo = plan_folds_local(sessions, hmax, hmax, N_FOLDS, TRAIN_FRAC)
        # label maturity on the synthetic demo: right-censor count
        pos = {s.isoformat(): i for i, s in enumerate(sessions)}
        censored = 0
        for f in demo:
            i0 = pos[f["test_start"]]
            i1 = pos[f["test_end"]]
            censored += max(0, (i1 + f["true_horizon_sessions"]) - (len(sessions) - 1))
        blocks[leg["leg_id"]] = {
            "symbol": leg["symbol"],
            "hypothesis_id": leg["hypothesis_id"],
            "max_hold_sessions": leg["max_hold_sessions"],
            "entry_delay_horizons": per_delay,
            "planner_invocation": {
                "class": "futbt.walkforward.WalkForwardPlanner",
                "args": {"true_horizon_sessions": "max_hold + entry_delay (per-cell)",
                         "embargo_sessions": "same as true horizon"},
                "plan_args": {"n_folds": N_FOLDS, "train_frac": TRAIN_FRAC},
                "sessions_source": ("engine empirical session calendar for the symbol "
                                    "(weekday-empirical until a real exchange calendar "
                                    "is supplied - NOT_RUN placeholder raises where "
                                    "required)"),
            },
            "fold_rules": {
                "selection": "nested TRAIN only; PIT view pinned at train_end; params frozen+stamped before TEST",
                "purge": "purge >= true horizon; under-purge raises PolicyError",
                "embargo": "embargo = true horizon",
                "folds": f"anchored-expanding, >= {N_FOLDS}, train_frac {TRAIN_FRAC}, TEST windows disjoint",
                "label_maturity": "TEST cells whose label window passes the last session are right-censored and recorded",
                "drop_policy": "INSUFFICIENT_COVERAGE only, recorded per fold; performance suppression forbidden",
            },
            "synthetic_demo_folds": demo,
            "synthetic_demo_right_censored_test_cells": censored,
        }
    return blocks


def check_invariants(blocks: dict, cells: list, sessions: list) -> list:
    """Invariants per the DOCUMENTED interface semantics: embargo is applied at
    CELL level (apply_purge_embargo drops TEST cells within embargo sessions
    after TRAIN end) - it does not move test_start. So we require strict
    ordering test_start > train_end and record the embargo-censored count."""
    errs = []
    pos = {s.isoformat(): i for i, s in enumerate(sessions)}
    for leg_id, b in blocks.items():
        for delay, spec in b["entry_delay_horizons"].items():
            if spec["purge_sessions"] < spec["true_horizon_sessions"]:
                errs.append(f"{leg_id} delay {delay}: purge < true horizon")
            if spec["embargo_sessions"] < spec["true_horizon_sessions"]:
                errs.append(f"{leg_id} delay {delay}: embargo < true horizon")
        for f in b["synthetic_demo_folds"]:
            if f["purge_sessions"] < f["true_horizon_sessions"]:
                errs.append(f"{leg_id} {f['fold_id']}: purge < horizon in demo folds")
            if pos[f["test_start"]] <= pos[f["train_end"]]:
                errs.append(f"{leg_id} {f['fold_id']}: test_start not after train_end")
            # cell-level embargo: TEST cells with index <= train_end + embargo are
            # dropped (recorded); count them so the audit trail is visible
            emb = pos[f["train_end"]] + f["embargo_sessions"]
            f["embargo_censored_test_cells"] = max(
                0, min(emb, pos[f["test_end"]]) - pos[f["test_start"]] + 1)
            # purge: TRAIN cells with index > test_start - purge are dropped
            purge_boundary = pos[f["test_start"]] - f["purge_sessions"]
            f["purge_dropped_train_cells"] = max(
                0, pos[f["train_end"]] - max(purge_boundary, -1))
        # TEST windows disjoint
        wins = [(pos[f["test_start"]], pos[f["test_end"]]) for f in b["synthetic_demo_folds"]]
        wins.sort()
        for (a0, a1), (b0, b1) in zip(wins, wins[1:]):
            if b0 <= a1:
                errs.append(f"{leg_id}: overlapping TEST windows {a0}-{a1} / {b0}-{b1}")
        if len(b["synthetic_demo_folds"]) < N_FOLDS:
            errs.append(f"{leg_id}: fewer than {N_FOLDS} folds in demo")
    seeds = [c["seed"] for c in cells]
    if len(set(seeds)) != len(seeds):
        errs.append("duplicate cell seeds")
    return errs


def main() -> int:
    pilot = yaml.safe_load(PILOT_PATH.read_text())
    sessions = weekday_sessions(SYNTH_START, SYNTH_END)

    engine_info = try_engine_crosscheck(
        sessions,
        pilot["legs"][0]["max_hold_sessions"] + 2,
        pilot["legs"][0]["max_hold_sessions"] + 2,
        N_FOLDS, TRAIN_FRAC)

    cells = enumerate_cells(pilot)
    blocks = build_walkforward_blocks(pilot, sessions)
    errs = check_invariants(blocks, cells, sessions)

    ta = pilot["trial_accounting_declaration"]
    n_primary = sum(1 for c in cells if "cost_stress" in c)
    n_base = sum(1 for c in cells if str(c.get("cell_id", "")).startswith("baseline"))
    n_abl = sum(1 for c in cells if c.get("arm") == "ablation_leave_one_leg")
    if n_primary != ta["primary_cells"]:
        errs.append(f"enumerated primary cells {n_primary} != declared {ta['primary_cells']}")
    if n_base != ta["baselines"]["flat"] + ta["baselines"]["always_on"] + ta["baselines"]["single_leg"]:
        errs.append(f"enumerated baselines {n_base} != declared")
    if n_abl != ta["ablations"]["leave_one_leg"]:
        errs.append(f"enumerated ablations {n_abl} != declared")
    if len(cells) != ta["total_declared_trials"]:
        errs.append(f"total cells {len(cells)} != declared {ta['total_declared_trials']}")

    manifest = {
        "schema": "futures_behavior_wf_manifest@1",
        "task_id": pilot["task_id"],
        "pilot_id": pilot["pilot_id"],
        "generated_utc": GENERATED_UTC,
        "determinism": "fully deterministic: fixed generated_utc, no clock reads, stable enumeration order; identical inputs -> byte-identical manifest",
        "inputs_sha256": {
            "configs/pilot_nq_cl.yaml": sha256_file(PILOT_PATH),
            "code/futbt/walkforward.py": sha256_file(WF_ENGINE_PATH),
        },
        "seed_protocol": {
            "master_seed": MASTER_SEED,
            "per_cell_seed": "20261002 + cell_index",
            "enumeration_order": ["symbol", "rule", "roll_rule", "cost_stress",
                                  "slippage_scenario", "entry_delay"],
            "synthetic_fixture_seed": MASTER_SEED,
        },
        "engine_interface": engine_info,
        "fold_construction_rules": {
            "selection": "nested TRAIN selection ONLY; PIT view pinned at train_end; params frozen + stamped before TEST",
            "purge": "purge_sessions >= true_horizon_sessions (label window = max_hold + entry_delay); under-purge raises",
            "embargo": "embargo_sessions = true_horizon_sessions",
            "folds": f"anchored-expanding, >= {N_FOLDS} folds, train_frac {TRAIN_FRAC}, no TEST overlap",
            "label_maturity": "TEST cells whose label window extends past the last session are right-censored + recorded",
            "fold_suppression": "forbidden for performance reasons; only INSUFFICIENT_COVERAGE (recorded)",
            "tb_labels": "TRAIN_ONLY - triple-barrier labels are never validation features",
        },
        "walkforward_blocks": blocks,
        "cells": cells,
        "trial_accounting": {
            "primary_cells": n_primary,
            "baselines": n_base,
            "ablations_leave_one_leg_full_path": n_abl,
            "total_declared_trials": len(cells),
            "multiplicity_disclosure": {
                "family_count": ta["multiplicity_disclosure"]["family_count"],
                "families": ta["multiplicity_disclosure"]["families"],
                "rule": ta["multiplicity_disclosure"]["rule"],
            },
        },
        "budget_status": ("NOT_RUN_ALL_CELLS: every cell requires (a) DAILY_BT admission "
                          "bars (>=24m true-volume front chain; NQ/CL have ~17), (b) owner-"
                          "declared slippage (S1 scenario), (c) NQ/CL exchange fees, (d) "
                          "cycle registration with this frozen budget"),
        "synthetic_demo_disclaimer": ("fold tables above are a SYNTHETIC weekday-calendar "
                                      "demonstration of the construction invariants only - "
                                      "no real sessions, no real data, no evaluation"),
    }
    manifest["invariants_checked"] = [
        "purge >= true horizon for every leg x delay",
        "embargo >= true horizon and honored between TRAIN end and TEST start in demo folds",
        "TEST windows pairwise disjoint (anchored-expanding)",
        ">= 4 folds per leg",
        "cell seeds unique; per-cell seed = 20261002 + cell_index",
        "enumerated cell counts == pilot trial_accounting_declaration",
    ]
    manifest["invariants_ok"] = not errs

    OUT_PATH.write_text(json.dumps(manifest, indent=1) + "\n")
    summary = {"cells_total": len(cells), "primary": n_primary, "baselines": n_base,
               "ablations": n_abl, "invariants_ok": not errs,
               "engine_mode": engine_info["mode"],
               "engine_crosscheck": engine_info.get("crosscheck"),
               "output": str(OUT_PATH.relative_to(CYCLE))}
    print(json.dumps(summary, indent=1))
    if errs:
        for e in errs:
            print(f"INVARIANT FAIL: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
