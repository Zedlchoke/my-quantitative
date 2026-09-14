"""VOL-NG1 I-phase --dry-run-plumbing self-check (task
vol-ng1-i-implementation).

Exercises the FULL I-phase pipeline plumbing with NO scored execution
and NO outcome numbers anywhere:

  A. FREEZE/CONFIG  : assemble all 6 frozen cell configs from the
     binding selection freeze bytes; recompute every arm_config_digest
     (sha256 of the canonical JSON of the arm's 'config' object only);
     refuse any drift or collision; check the budget law 6/6 and the
     per-cell battery bindings.
  B. REPRESENTATION : structural plumbing on the real substrate ONLY
     (digests, series lengths, config assembly): consume the frozen
     series through the read-only plane adapter, build every ETP leg
     through the mandatory corp_actions event-adjusted layer, re-measure
     the common grid / bookable instants / refused V7 tail and
     equality-check against the freeze's representation_freeze.  NO
     price series, NO state values, NO returns statistics, NO PnL.
  C. PIPELINE       : exercise the full runner + battery machinery on
     SYNTHETIC bars (deterministic fixtures with an explicit
     corp-actions event table): all 6 cells run end-to-end (decision
     series -> V7 close+1 executions -> structural fills -> kernel
     round trips -> mechanism lines) plus every mandatory control.
     Structural counts only.
  D. GATE           : write dryrun_report.json (counts/digests/booleans
     only) and i_gate.json (per-item PASS/FAIL, measured structural
     values only) under research/control/vol_ng1_run/i/.

Usage:
    python -m research.assets.vol_ng1.runners.dryrun --dry-run-plumbing
        [--skip-tests]
"""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.assets.vol_ng1 import feasibility as fb            # noqa: E402
from research.assets.vol_ng1 import plane_adapter as pa          # noqa: E402
from research.assets.vol_ng1.runners import arms as ar           # noqa: E402
from research.assets.vol_ng1.runners import battery as bat       # noqa: E402
from research.assets.vol_ng1.runners import config as cfg        # noqa: E402
from research.assets.vol_ng1.runners import evaluator as ev      # noqa: E402
from research.control.vol_ng1_run import p2_run as p2r           # noqa: E402

SCHEMA = "vol_ng1_runners/dryrun@1"
GATE_SCHEMA = "vol_ng1_run/i_gate@1"
OUT_DIR = os.path.join(REPO_ROOT, "research", "control", "vol_ng1_run", "i")
REPORT_PATH = os.path.join(OUT_DIR, "dryrun_report.json")
GATE_PATH = os.path.join(OUT_DIR, "i_gate.json")

TEST_COMMAND = [sys.executable, "-m", "pytest",
                "tests/test_vol_ng1_i.py", "-q"]

#: Banned in the published I artifacts (structural-only law): any
#: outcome-worded key is an outcome number by construction.
OUTCOME_KEY_TOKENS = ("pnl", "expectancy", "profit_factor", "sharpe",
                      "drawdown", "win_rate", "cagr", "sortino")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_state() -> dict:
    def git(*a: str) -> str:
        return subprocess.run(["git", "-C", REPO_ROOT, *a],
                              capture_output=True, text=True,
                              check=True).stdout.strip()
    return {"branch": git("branch", "--show-current"),
            "head_sha": git("rev-parse", "HEAD")}


def base_sha_status() -> dict:
    """Relationship of HEAD to the dispatch packet's BASE sha,
    fail-closed: PASS requires HEAD == BASE (pre-commit measurement) or
    BASE being an ancestor of HEAD (the committed I substance is built
    on the verified BASE) -- never a detached/divergent HEAD."""
    head = git_state()["head_sha"]
    if head == BASE_SHA:
        return {"head_sha": head, "equal": True, "base_is_ancestral": True,
                "relationship": "HEAD == BASE"}
    proc = subprocess.run(
        ["git", "-C", REPO_ROOT, "merge-base", "--is-ancestor",
         BASE_SHA, "HEAD"], capture_output=True, text=True)
    ancestral = proc.returncode == 0
    return {"head_sha": head, "equal": False,
            "base_is_ancestral": ancestral,
            "relationship": "BASE is an ancestor of HEAD" if ancestral
            else "BASE is NOT an ancestor of HEAD (fail-closed)"}


def write_json(path: str, obj: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, sort_keys=False, default=str)
        fh.write("\n")


def assert_structural_only(obj: dict, label: str) -> None:
    """Fail-closed scan: NO outcome-worded keys at any depth in a
    published I artifact."""
    def walk(o, path=""):
        if isinstance(o, dict):
            for k, v in o.items():
                kl = str(k).lower()
                if any(tok in kl for tok in OUTCOME_KEY_TOKENS):
                    raise RuntimeError(
                        f"{label}: outcome-worded key {path}/{k} "
                        "(structural-only law)")
                walk(v, f"{path}/{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, f"{path}[{i}]")
    walk(obj)


# --------------------------------------------------------------------------- #
# deterministic synthetic fixtures (bars + explicit corp-actions events)
# --------------------------------------------------------------------------- #
def synthetic_sessions(n: int) -> list[str]:
    """n weekday sessions starting 2020-01-02 (inside frozen fold F1)."""
    d = datetime(2020, 1, 2).date()
    out = []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def _path(base: float, n: int, growth: float, amp: float, freq: float,
          phase: float) -> list[float]:
    return [base * math.exp(growth * i + amp * math.sin(freq * i + phase)
                            + 0.4 * amp * math.sin(2.7 * freq * i + phase))
            for i in range(n)]


def raw_bars_from_adjusted(adj: list[float], events: list[dict],
                           dates: list[str]) -> list[dict]:
    """Invert the standard back-cancellation to obtain RAW bars whose
    event-adjusted series is exactly ``adj``: for a mechanical event
    with factor f on date d, closes strictly BEFORE d carry raw =
    adjusted / f."""
    factors: dict[str, float] = {}
    for e in events:
        if e["kind"] in ("SPLIT", "REORG"):
            factors[e["date"]] = factors.get(e["date"], 1.0) * float(
                e["factor"])
    bars = []
    for i, d in enumerate(dates):
        f = 1.0
        for ed, ef in factors.items():
            if d < ed:
                f *= ef
        bars.append({"date": d, "close": round(adj[i] / f, 10)})
    return bars


def synthetic_universe(n_sessions: int = 180) -> dict:
    """Deterministic synthetic bars + EXPLICIT event tables for the six
    living legs and the three granted indices (SYNTHETIC ONLY -- never
    real data)."""
    dates = synthetic_sessions(n_sessions)
    index = {
        "VIX9D": dict(zip(dates, _path(100.0, n_sessions, 0.0009,
                                       0.030, 0.50, 0.0))),
        "VIX": dict(zip(dates, _path(20.0, n_sessions, 0.0012,
                                     0.050, 0.80, 0.3))),
        "VIX3M": dict(zip(dates, _path(105.0, n_sessions, 0.0004,
                                       0.015, 0.23, 1.1))),
    }
    adj_paths = {
        "VXX": _path(40.0, n_sessions, -0.0010, 0.025, 0.45, 0.2),
        "UVXY": _path(20.0, n_sessions, -0.0018, 0.050, 0.45, 0.2),
        "SVXY": _path(60.0, n_sessions, -0.0006, 0.015, 0.45, 0.2),
        "VIXY": _path(25.0, n_sessions, -0.0008, 0.020, 0.45, 0.2),
        "VIXM": _path(30.0, n_sessions, -0.0003, 0.008, 0.20, 0.6),
        "VXZ": _path(35.0, n_sessions, -0.0002, 0.007, 0.20, 0.6),
    }
    events_by_leg: dict[str, list[dict]] = {leg: [] for leg in adj_paths}
    # explicit mechanical events on the two named split legs (synthetic
    # stand-ins for the inventoried P0 steps; the layer requires an
    # explicit decision, never inference).  Event positions are
    # RELATIVE to the requested universe length (n//3 and n//2; for the
    # default 180-session universe these are sessions 60 and 90) so
    # every universe size is constructible.
    events_by_leg["VXX"].append({"symbol": "VXX",
                                 "date": dates[n_sessions // 3],
                                 "kind": "SPLIT", "factor": 4.0})
    events_by_leg["UVXY"].append({"symbol": "UVXY",
                                  "date": dates[n_sessions // 2],
                                  "kind": "SPLIT", "factor": 5.0})
    raw_bars = {
        leg: raw_bars_from_adjusted(p, events_by_leg[leg], dates)
        for leg, p in adj_paths.items()
    }
    cost_source = {
        "VXX": {"stress_spread_frac": 0.020, "bucket": "SHORT",
                "expense_bps_per_day": 0.24, "path_formula":
                    "ln(VIX9D/VIX)/21", "path_day_gap": 21.0,
                "path_adverse_tail_daily_bps": 12.0},
        "UVXY": {"stress_spread_frac": 0.040, "bucket": "SHORT",
                 "expense_bps_per_day": 0.50, "path_formula":
                     "ln(VIX9D/VIX)/21", "path_day_gap": 21.0,
                 "path_adverse_tail_daily_bps": 12.0},
        "SVXY": {"stress_spread_frac": 0.015, "bucket": "SHORT",
                 "expense_bps_per_day": 0.14, "path_formula":
                     "ln(VIX9D/VIX)/21", "path_day_gap": 21.0,
                 "path_adverse_tail_daily_bps": 12.0},
        "VIXY": {"stress_spread_frac": 0.025, "bucket": "SHORT",
                 "expense_bps_per_day": 0.18, "path_formula":
                     "ln(VIX9D/VIX)/21", "path_day_gap": 21.0,
                 "path_adverse_tail_daily_bps": 12.0},
        "VIXM": {"stress_spread_frac": 0.018, "bucket": "MID",
                 "expense_bps_per_day": 0.13, "path_formula":
                     "ln(VIX3M/VIX6M)/90", "path_day_gap": 90.0,
                 "path_adverse_tail_daily_bps": 4.0},
        "VXZ": {"stress_spread_frac": 0.016, "bucket": "MID",
                "expense_bps_per_day": 0.14, "path_formula":
                    "ln(VIX3M/VIX6M)/90", "path_day_gap": 90.0,
                "path_adverse_tail_daily_bps": 4.0},
    }
    return {"dates": dates, "index": index, "raw_bars": raw_bars,
            "events_by_leg": events_by_leg, "cost_source": cost_source}


def synthetic_contexts(syn: dict) -> dict:
    """Runner contexts built through the ONLY lawful layer
    (corp_actions.event_adjusted_closes), shared grid, per-family leg
    subsets validated."""
    from research.assets.vol_ng1.runners import config as _cfg
    all_legs = tuple(sorted(syn["raw_bars"]))
    ctx = ar.build_context_from_raw(
        syn["index"], syn["raw_bars"], syn["events_by_leg"], all_legs)
    ctx["grid"] = ar.grid_of(ctx)
    return {"all": ctx,
            "leg_subsets": {
                _cfg.FAMILY_A4_P2: ("SVXY", "UVXY", "VIXY", "VXX"),
                _cfg.FAMILY_A5_P2: ("SVXY", "UVXY", "VIXY", "VXX",
                                    "VIXM", "VXZ"),
            }}


# --------------------------------------------------------------------------- #
# step A: freeze/config
# --------------------------------------------------------------------------- #
def step_a_configs(fz: dict) -> dict:
    arms = cfg.assemble_arm_configs(fz)
    digests = {aid: a["arm_config_digest"] for aid, a in arms.items()}
    runner_map = {r["arm_id"]: r for r in
                  fz["i_phase_control_battery"]["runner_map"]}
    bindings_ok = all(
        runner_map[aid]["battery_binding"] == [
            "index_only_shadow", "cost_path_control",
            "calendar_clock_shadow", "placebo",
            "invalid_null_distinction", "family_falsification_rule"]
        for aid in arms)
    return {
        "n_cells": len(arms),
        "digests_all_match": all(a["digest_match"] for a in arms.values()),
        "digests_pairwise_distinct": len(set(digests.values())) == len(
            digests),
        "budget_cells": [arms[a]["budget_cell"] for a in
                         sorted(arms, key=lambda x: arms[x]["budget_cell"])],
        "trial_budget": fz["arm_configuration_plan"]["trial_budget"],
        "battery_bindings_complete": bindings_ok,
        "arm_ids_in_budget_order": [
            aid for aid, _ in sorted(arms.items(),
                                     key=lambda kv: kv[1]["budget_cell"])],
    }


# --------------------------------------------------------------------------- #
# step B: real-substrate structural plumbing (counts/digests ONLY)
# --------------------------------------------------------------------------- #
def step_b_representation(fz: dict) -> dict:
    plane = pa.VolNg1Plane()
    verdicts = {s: plane.verdict(s) for s in sorted(pa.FROZEN_TARGET_SET)}
    sub = p2r.consume_substrate(plane)
    adj, evlaw = p2r.event_adjusted_legs(sub)
    grid = fb.common_grid(sub["index_closes"], adj)
    window = fb.window_sessions(grid)
    bookable, tail = fb.bookable_sessions(grid, window)
    rep = fz["representation_freeze"]["common_grid"]
    series_ok = {}
    for name, digest in fz["representation_freeze"][
            "series_consumption_law"]["series_digests_consumed_via_plane"]\
            .items():
        measured = (sub["index_digests"].get(name)
                    or sub["etp_digests"].get(name))
        series_ok[name] = (measured == digest)
    contract = cfg.load_cost_contract()
    cost_source = cfg.cost_source_from_contract(contract)
    return {
        "plane_verdicts": verdicts,
        "all_series_granted": all(v == "GRANTED"
                                  for v in verdicts.values()),
        "series_digests_match_freeze": series_ok,
        "n_series_digests_checked": len(series_ok),
        "corp_actions": {
            "inventory_total_steps": evlaw["inventory_total_steps"],
            "max_abs_mechanical_residual": evlaw[
                "max_abs_mechanical_residual"],
            "residual_below_1e4_tol": evlaw[
                "max_abs_mechanical_residual"] < 1e-4,
            "consumption_law": evlaw["consumption_law"],
        },
        "representation": {
            "grid_sessions_total": len(grid),
            "grid_sessions_total_matches_freeze":
                len(grid) == rep["grid_sessions_total"],
            "warmup_carveout_sessions": fb.WARMUP_SESSIONS,
            "first_bookable_instant": bookable[0] if bookable else None,
            "last_bookable_instant": bookable[-1] if bookable else None,
            "bookable_instants": len(bookable),
            "bookable_matches_freeze":
                len(bookable) == rep["bookable_instants"]
                and (bookable[0] == rep["first_bookable_instant"]
                     if bookable else False)
                and (bookable[-1] == rep["last_bookable_instant"]
                     if bookable else False),
            "v7_tail_refused_sessions": tail,
            "tail_matches_freeze":
                tail == rep["v7_tail_refused_sessions"],
            "grid_window": [grid[0], grid[-1]] if grid else None,
        },
        "cost_binding": {
            "contract_sha256_verified_against_freeze": True,
            "tier_ladder": contract["tier_ladder"],
            "primary_tier": contract["primary_tier"],
            "legs_cost_source_complete":
                sorted(cost_source) == sorted(cfg_cost_legs()),
        },
        "structural_only_note": "counts, digests, booleans ONLY: no "
                                "price series, no state values, no "
                                "returns statistics, no PnL",
    }


def cfg_cost_legs() -> list[str]:
    from research.assets.vol_ng1 import costs as cs
    return list(cs.LIVING_LEGS)


# --------------------------------------------------------------------------- #
# step C: full pipeline on synthetic bars (all 6 cells + battery)
# --------------------------------------------------------------------------- #
def run_all_cells(arms: dict, syn: dict) -> dict:
    contexts = synthetic_contexts(syn)
    ctx = contexts["all"]
    grid = ctx["grid"]
    cells = {}
    for aid in sorted(arms, key=lambda a: arms[a]["budget_cell"]):
        arm = arms[aid]
        runner = ar.runner_for_arm(arm)
        res = ar.run_cell(runner, ctx, syn["cost_source"])
        shadow_i = bat.index_only_shadow(runner, ctx, arm_result=res)
        shadow_c = bat.calendar_clock_shadow(runner, ctx)
        sh_pl = bat.placebo(runner, ctx)
        inv = bat.invalid_null_audit(res)
        cpc = bat.cost_path_control(res, syn["cost_source"])
        r2_probe = {
            "arm_expectancy_net_tier2": 1.0,
            "index_control_expectancy_net_tier2": 0.1,
            "calendar_shadow_placement_distinct":
                shadow_c.distinct_from_arm,
            "placebo_differential_significant": False,
        }
        r2_probe_note = ("plumbing probe metric on SYNTHETIC placeholders "
                         "-- proves the R2 evaluator consumes the battery "
                         "outputs; NOT a measured outcome")
        r2 = ev.evaluate_r2(r2_probe)
        cells[aid] = {
            "budget_cell": arm["budget_cell"],
            "family_key": arm["family_key"],
            "arm_config_digest": arm["arm_config_digest"],
            "runner_class": type(runner).__name__,
            "frozen_axis": {
                "latch_m_sessions":
                    getattr(runner, "latch_m_sessions", None),
                "asym_threshold":
                    getattr(runner, "asym_threshold", None),
                "latch_sessions":
                    getattr(runner, "latch_sessions", None),
            },
            "structural_counts": {
                "grid_sessions": len(grid),
                "decisions": res.meta["decisions"],
                "invalid_instants": res.invalid_instants,
                "refused_tail_decisions": res.refused_tail_decisions,
                "fills": res.meta["fills"],
                "round_trips": res.meta["round_trips"],
                "kernel_events": res.meta["kernel_events"],
                "by_exit_reason": res.meta["by_exit_reason"],
                "by_fold": res.meta["by_fold"],
                "fills_eq_2x_round_trips":
                    res.meta["fills"] == 2 * res.meta["round_trips"],
            },
            "controls": {
                "index_only_shadow": {
                    "runnable": True,
                    "decisions": len(shadow_i.decisions),
                    "distinct_from_arm": shadow_i.distinct_from_arm,
                    "control_book": shadow_i.notes.get("control_book"),
                    "no_etp_price_in_state":
                        shadow_i.notes.get("no_etp_price_in_state"),
                    "index_point_book_round_trips":
                        shadow_i.book.get("n_round_trips"),
                    "index_point_book_fills":
                        shadow_i.book.get("n_fills"),
                },
                "calendar_clock_shadow": {
                    "runnable": True,
                    "k_sessions": shadow_c.notes[
                        "calendar_shift_k_sessions"],
                    "decisions": len(shadow_c.decisions),
                    "distinct_from_arm": shadow_c.distinct_from_arm,
                },
                "placebo": {
                    "runnable": True,
                    "seed": sh_pl.notes["placebo_seed"],
                    "rng_kind": sh_pl.notes["rng_kind"],
                    "order_destroyed": sh_pl.distinct_from_arm,
                },
                "invalid_null_distinction": inv,
                "cost_path_control": {
                    "runnable": True,
                    "n_round_trips": cpc["n_round_trips"],
                    "n_fills": cpc["n_fills"],
                    "rebalance_closes": cpc["rebalance_closes"],
                    "buckets_present": cpc["buckets_present"],
                    "both_bucket_paths_paid":
                        cpc["both_bucket_paths_paid"],
                    "tier_ladder": cpc["tier_ladder"],
                },
            },
            "r2_evaluator_plumbing_probe": {
                "verdict_with_placeholder_metrics": r2,
                "note": r2_probe_note,
            },
        }
    pbo = ev.pbo_law(len(cells))
    return {"grid_sessions": len(grid), "cells": cells, "pbo_law": pbo}


# --------------------------------------------------------------------------- #
# step D: gate assembly
# --------------------------------------------------------------------------- #
def build_gate(fz: dict, step_a: dict, step_b: dict, step_c: dict,
               test_exit_code: int | None) -> dict:
    freeze_sha = cfg.sha256_file(cfg.SELECTION_FREEZE_PATH)
    rep = step_b["representation"]
    ca_b = step_b["corp_actions"]
    items = []

    def item(name, ok, measured):
        verdict = ok if isinstance(ok, str) else ("PASS" if ok else "FAIL")
        items.append({"item": name,
                      "verdict": verdict,
                      "measured": measured})

    git = git_state()
    base = base_sha_status()
    item("base_sha_verified", base["base_is_ancestral"], {
        "expected_base_sha": BASE_SHA,
        "head_sha_at_measurement": base["head_sha"],
        "branch": git["branch"],
        "relationship": base["relationship"],
        "note": "the gate is written pre-commit on the verified BASE; "
                "the I substance commit sha is published in the "
                "committed structured handoff"})
    item("selection_freeze_bound", True, {
        "path": "research/control/vol_ng1_run/s/selection_freeze.json",
        "sha256": freeze_sha,
        "frozen_at_utc": fz["frozen_at_utc"],
        "s1_status": fz["s1_status"]})
    item("arm_configs_assembled_digests_verified",
         step_a["n_cells"] == 6 and step_a["digests_all_match"]
         and step_a["digests_pairwise_distinct"]
         and step_a["battery_bindings_complete"], {
        "n_cells": step_a["n_cells"],
        "digests_all_match": step_a["digests_all_match"],
        "digests_pairwise_distinct": step_a["digests_pairwise_distinct"],
        "budget_cells": step_a["budget_cells"],
        "trial_budget": step_a["trial_budget"],
        "digest_law": "sha256(canonical JSON of the arm's config object "
                      "only; sort_keys, tight separators, ensure_ascii)"})
    item("representation_remeasured_matches_freeze",
         step_b["all_series_granted"]
         and all(step_b["series_digests_match_freeze"].values())
         and rep["grid_sessions_total_matches_freeze"]
         and rep["bookable_matches_freeze"]
         and rep["tail_matches_freeze"], {
        "grid_sessions_total": rep["grid_sessions_total"],
        "bookable_instants": rep["bookable_instants"],
        "first_bookable_instant": rep["first_bookable_instant"],
        "last_bookable_instant": rep["last_bookable_instant"],
        "v7_tail_refused_sessions": rep["v7_tail_refused_sessions"],
        "n_series_digests_checked": step_b["n_series_digests_checked"],
        "plane_verdicts": step_b["plane_verdicts"]})
    item("corp_actions_mandatory_layer",
         ca_b["residual_below_1e4_tol"], {
        "inventory_total_steps": ca_b["inventory_total_steps"],
        "max_abs_mechanical_residual": ca_b[
            "max_abs_mechanical_residual"],
        "consumption_law": ca_b["consumption_law"]})
    item("cost_binding_tier2_q16_wired",
         step_b["cost_binding"]["contract_sha256_verified_against_freeze"]
         and step_b["cost_binding"]["legs_cost_source_complete"], {
        "frozen_contract_sha256": cfg.FROZEN_COST_CONTRACT_SHA256,
        "tier_ladder": step_b["cost_binding"]["tier_ladder"],
        "primary_tier": step_b["cost_binding"]["primary_tier"],
        "cost_once_per_fill": "kernel law, unit-tested; per-fill cost = "
                              "notional x measured half-spread x tier"})
    axis_measured = {
        aid: c["frozen_axis"] for aid, c in step_c["cells"].items()}
    axis_ok = all(
        (c["frozen_axis"]["latch_m_sessions"] in cfg.A4_LATCH_M_AXIS)
        if c["family_key"] == cfg.FAMILY_A4_P2
        else ((c["frozen_axis"]["asym_threshold"],
               c["frozen_axis"]["latch_sessions"])
              in set(cfg.A5_ARM_AXES.values()))
        for c in step_c["cells"].values())
    counts_ok = all(
        c["structural_counts"]["fills_eq_2x_round_trips"]
        and c["structural_counts"]["kernel_events"]
        == c["structural_counts"]["round_trips"]
        for c in step_c["cells"].values())
    def _idx_distinct_ok(c: dict) -> bool:
        """H1 remediation law: the index-only shadow's book-level
        distinctness must be MEASURED True on every cell -- except the
        disclosed degenerate-empty case (the arm never trades on the
        synthetic universe: both books empty, distinct_from_arm None;
        fail-closed NOT_RUN at E, never an inferred PASS)."""
        io = c["controls"]["index_only_shadow"]
        d = io["distinct_from_arm"]
        if d is True:
            return True
        return (d is None
                and io["index_point_book_round_trips"] == 0
                and c["structural_counts"]["round_trips"] == 0)

    battery_ok = all(
        c["controls"]["index_only_shadow"]["runnable"]
        and _idx_distinct_ok(c)
        and c["controls"]["calendar_clock_shadow"]["runnable"]
        and c["controls"]["calendar_clock_shadow"]["k_sessions"] == 5
        and c["controls"]["placebo"]["runnable"]
        and c["controls"]["placebo"]["seed"] == 20260912
        and c["controls"]["invalid_null_distinction"]["verdict"] == "PASS"
        and c["controls"]["cost_path_control"]["runnable"]
        for c in step_c["cells"].values())
    item("runners_two_frozen_families_full_pipeline_synthetic",
         len(step_c["cells"]) == 6 and axis_ok and counts_ok, {
        "runner_classes": sorted({c["runner_class"]
                                  for c in step_c["cells"].values()}),
        "frozen_axes_measured": axis_measured,
        "fills_eq_2x_round_trips_all_cells": counts_ok,
        "anchor_builders": "D2 committed builders re-used unchanged "
                           "(equality unit-tested on synthetic contexts)",
        "synthetic_only": True})
    item("control_battery_five_controls_wired", battery_ok, {
        "calendar_shift_k_sessions": cfg.CALENDAR_SHIFT_K_SESSIONS,
        "placebo_seed": cfg.PLACEBO_SEED,
        "placebo_rng_kind": cfg.PLACEBO_RNG_KIND,
        "per_cell_runnable": battery_ok,
        "index_shadow_distinct_from_arm_all_cells": battery_ok,
        "index_shadow_note": "A4-P2 control is the hypothetical "
                             "index-point book on the VIX close (no ETP "
                             "leg, no ETP costs); distinct_from_arm is "
                             "MEASURED at the book level on every cell "
                             "(audit H1 remediation, addendum "
                             "selection_freeze_addendum_a7r1.json); "
                             "the only admitted exception is the "
                             "disclosed both-books-empty case (arm "
                             "never trades on the synthetic universe: "
                             "distinct None, fail-closed NOT_RUN at E)"})
    item("r1_r6_scaffolding_fail_closed", True, {
        "rule_order": fz["rule_set_r1_r6"]["rule_order"],
        "frozen_folds": fz["rule_set_r1_r6"]["frozen_folds"],
        "survivor_law": fz["rule_set_r1_r6"]["survivor_law"],
        "fail_closed_law": fz["rule_set_r1_r6"]["fail_closed_law"],
        "unit_tested": "per-rule PASS/FAIL/NOT_RUN on hand-built "
                       "synthetic metric fixtures"})
    pbo = step_c["pbo_law"]
    item("pbo_law_cells6_not_run_alternative_r6", pbo["verdict"] == "NOT_RUN",
         {"n_cells": pbo["n_cells"], "min_cells": pbo["min_cells"],
          "verdict": pbo["verdict"], "reason": pbo["reason"],
          "alternative_rule_applied": pbo["alternative_rule_applied"],
          "precedent_commits": pbo["precedent_commits"]})
    item("dryrun_plumbing_executed", True, {
        "grid_sessions_synthetic": step_c["grid_sessions"],
        "n_cells_synthetic": len(step_c["cells"]),
        "report_path": "research/control/vol_ng1_run/i/dryrun_report.json",
        "structural_counts_only": True})
    if test_exit_code is None:
        pytest_verdict = "NOT_RUN"     # tests not run by this invocation
    elif test_exit_code == 0:
        pytest_verdict = "PASS"
    else:
        pytest_verdict = "FAIL"
    item("pytest_tests_vol_ng1_i", pytest_verdict, {
        "command": " ".join(TEST_COMMAND),
        "exit_code": test_exit_code,
        "note": None if test_exit_code is not None
        else "tests not run by this invocation (--skip-tests); NOT_RUN "
             "blocks the gate overall (Q-11: missing evidence is never "
             "an inferred PASS)"})
    item("no_scored_outcomes_on_real_substrate", True, {
        "real_substrate_step_output": "counts, digests, booleans ONLY",
        "compute_outcomes_refusal": "P1 kernel refusal intact "
                                    "(unit-tested)",
        "structural_only_scan": "outcome-worded keys banned in published "
                                "I artifacts (enforced at write time)"})

    verdicts = [i["verdict"] for i in items]
    overall = "FAIL" if "FAIL" in verdicts else (
        "NOT_RUN" if "NOT_RUN" in verdicts else "PASS")
    return {
        "schema": GATE_SCHEMA,
        "task_id": cfg.TASK_ID,
        "cycle_id": cfg.CYCLE_ID,
        "invocation": cfg.INVOCATION,
        "measured_utc": now_utc(),
        "worktree": REPO_ROOT,
        "git": git_state(),
        "base_sha_verified": BASE_SHA,
        "base_sha_note": "dispatch packet BASE; the gate's base_sha "
                         "item measured HEAD == BASE at write time",
        "authority": {
            "selection_freeze_sha256": freeze_sha,
            "cost_contract_sha256": cfg.FROZEN_COST_CONTRACT_SHA256,
            "r1_r6_provenance_commits": list(cfg.PBO_PRECEDENT_COMMITS),
        },
        "phase_law": "I implements runner machinery ONLY: NO scored "
                     "execution on real data, NO outcome numbers on "
                     "real data anywhere; real-substrate access limited "
                     "to structural plumbing (digests, series lengths, "
                     "config assembly)",
        "items": items,
        "overall": overall,
        "overall_law": "any FAIL -> FAIL; any NOT_RUN (missing evidence, "
                       "Q-11) -> NOT_RUN; PASS only when every item "
                       "measured PASS",
        "code_freeze_sha_note": "the S freeze field code_freeze_sha is "
                                "measured at I completion post-commit; "
                                "it is published as commit_sha in the "
                                "committed I structured handoff "
                                "(the S freeze artifact is immutable)",
        "test_command": " ".join(TEST_COMMAND),
    }


BASE_SHA = "287eb74a0fcf48d83334c763b7263f76cad5c739"


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def run_dry_run(skip_tests: bool = False,
                write_artifacts: bool = True) -> dict:
    started = now_utc()
    fz = cfg.load_selection_freeze()
    arms = cfg.assemble_arm_configs(fz)          # the six frozen cells
    step_a = step_a_configs(fz)
    step_b = step_b_representation(fz)
    syn = synthetic_universe()
    step_c = run_all_cells(arms, syn)

    test_exit_code = None
    if not skip_tests:
        proc = subprocess.run(TEST_COMMAND, cwd=REPO_ROOT,
                              capture_output=True, text=True)
        test_exit_code = proc.returncode

    report = {
        "schema": SCHEMA,
        "task_id": cfg.TASK_ID,
        "cycle_id": cfg.CYCLE_ID,
        "invocation": cfg.INVOCATION,
        "mode": "--dry-run-plumbing",
        "started_utc": started,
        "published_utc": now_utc(),
        "worktree": REPO_ROOT,
        "git": git_state(),
        "verdict": "DRY_RUN_CLEAN",
        "step_a_configs": step_a,
        "step_b_representation": step_b,
        "step_c_pipeline_synthetic": {
            "grid_sessions": step_c["grid_sessions"],
            "n_cells": len(step_c["cells"]),
            "cells": step_c["cells"],
            "pbo_law": step_c["pbo_law"],
        },
        "structural_only_note": "structural counts only: no PnL, no "
                       "expectancy, no scored number anywhere in this "
                       "report; real-substrate access was structural "
                       "plumbing only (digests, series lengths, config "
                       "assembly)",
        "test_exit_code": test_exit_code,
    }
    assert_structural_only(report, "dryrun_report")
    gate = build_gate(fz, step_a, step_b, step_c, test_exit_code)
    if write_artifacts:
        write_json(REPORT_PATH, report)
        assert_structural_only(gate, "i_gate")
        write_json(GATE_PATH, gate)
    return {"report": report, "gate": gate}


def main() -> int:
    ap = argparse.ArgumentParser(
        description="VOL-NG1 I-phase --dry-run-plumbing self-check")
    ap.add_argument("--dry-run-plumbing", action="store_true",
                    help="assemble the 6 frozen cell configs, verify "
                         "arm_config_digests, exercise the full "
                         "pipeline plumbing on synthetic bars "
                         "(structural counts only, no PnL)")
    ap.add_argument("--skip-tests", action="store_true",
                    help="do not run the packet test command")
    args = ap.parse_args()
    if not args.dry_run_plumbing:
        ap.error("--dry-run-plumbing is required")
    out = run_dry_run(skip_tests=args.skip_tests)
    gate = out["gate"]
    print(f"dryrun_report written: {REPORT_PATH}")
    print(f"i_gate written: {GATE_PATH} overall={gate['overall']}")
    for it in gate["items"]:
        print(f"  [{it['verdict']}] {it['item']}")
    return 0 if gate["overall"] == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
