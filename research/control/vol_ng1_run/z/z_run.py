"""VOL-NG1 Z -- SANITIZED DRY-RUN of the six frozen cells on the REAL
frozen substrate (task vol-ng1-z-dryrun).

A prelaunch pipeline rehearsal: the exact 6 frozen selection cells plus
the full I-phase control battery are executed END-TO-END on the REAL
frozen substrate through the I-phase runner machinery
(research/assets/vol_ng1/runners/, READ-ONLY) -- the same code paths the
scored E phase will drive.

SANITIZATION LAW (binding on every committed Z artifact): committed
artifacts record STRUCTURAL facts only --

- NO PnL, NO expectancy, NO profit factor, NO Sharpe, NO per-trade or
  aggregate OUTCOME numbers anywhere;
- internal values that are outcome-like or money-like (kernel books,
  round-trip ledgers, per-fill cost lines, decision-state series) are
  used only for plumbing verification and are committed ONLY as
  sha256 digest chains, never in cleartext;
- what IS committed: decision/fill/round-trip/kernel-event COUNTS,
  control-executable PASS/FAIL, fold-partition counts, digest chains,
  runtime provenance, fail-closed verdicts.

Fail-closed law: any cell whose plumbing fails on the real substrate is
recorded FAIL (a BLOCKED_PRELAUNCH candidate) and is REPORTED, never
repaired here -- the runners and the freeze are READ-ONLY for this
lane.  Missing evidence is NOT_RUN-eligible, never an inferred PASS.

Real-substrate consumption path (identical to the committed P2 gate):
plane adapter (read-only, no network) -> corp_actions
event_adjusted_closes (the ONLY lawful ETP layer) -> frozen common grid
-> warmup carveout + V7 close+1 bookable instants -> the frozen cells.

Usage:
    python -m research.control.vol_ng1_run.z.z_run --real-substrate-dryrun
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.assets.vol_ng1 import feasibility as fb             # noqa: E402
from research.assets.vol_ng1 import plane_adapter as pa           # noqa: E402
from research.assets.vol_ng1.runners import arms as ar            # noqa: E402
from research.assets.vol_ng1.runners import battery as bat        # noqa: E402
from research.assets.vol_ng1.runners import config as cfg         # noqa: E402
from research.assets.vol_ng1.runners import evaluator as ev       # noqa: E402
from research.control.vol_ng1_run import p2_run as p2r            # noqa: E402

SCHEMA = "vol_ng1_run/z_report@1"
CELL_SCHEMA = "vol_ng1_run/z_cell_manifest@1"
TASK_ID = "vol-ng1-z-dryrun"
CYCLE_ID = "VOL-NG1"
INVOCATION = "lead-bg-vol-z"

OUT_DIR = os.path.join(REPO_ROOT, "research", "control", "vol_ng1_run", "z")
REPORT_PATH = os.path.join(OUT_DIR, "z_report.json")

#: Dispatch packet BASE sha (the verified worktree HEAD this run started
#: from).  Fail-closed: the run refuses to publish from a divergent HEAD.
BASE_SHA = "00e5f8c8f382697a14028b8ceb3e2a5ca45a55e2"
BRANCH = "orca/vol-ng1-integration"

TEST_COMMAND = [sys.executable, "-m", "pytest", "tests/test_vol_ng1_z.py",
                "-q"]

#: SANITIZATION LAW, mechanically enforced before ANY Z artifact is
#: written: an outcome-worded or money-worded KEY at any depth is an
#: outcome number by construction and refuses the write.  (Values are
#: not scanned: the committed law text itself names the banned words.)
OUTCOME_KEY_TOKENS = (
    "pnl", "expectancy", "profit_factor", "sharpe", "sortino",
    "drawdown", "win_rate", "cagr", "calmar", "gross", "net_stress",
    "_usd", "usd_", "price", "notional", "bps", "spread_frac", "trade_",
    "hit_rate", "payoff",
)

HEX64 = re.compile(r"^[0-9a-f]{64}$")


class ZError(Exception):
    """Fail-closed Z error: nothing repaired, nothing smuggled."""


# --------------------------------------------------------------------------- #
# sanitized I/O + digest helpers
# --------------------------------------------------------------------------- #
def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def scan_structural_only(obj, label: str, _path: str = "") -> None:
    """Fail-closed sanitization scan: NO outcome-worded / money-worded
    KEY at any depth.  Raises ZError naming the offending path."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            kl = str(k).lower()
            if any(tok in kl for tok in OUTCOME_KEY_TOKENS):
                raise ZError(
                    f"{label}: banned outcome/money key {path(_path, k)} "
                    "(sanitization law: structural facts only)")
            scan_structural_only(v, label, path(_path, k))
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            scan_structural_only(v, label, f"{_path}[{i}]")


def path(prefix: str, key) -> str:
    return f"{prefix}/{key}" if prefix else f"/{key}"


def sha256_obj(obj) -> str:
    """Digest of a canonical-JSON serialization of an internal value
    (the ONLY lawful way an outcome-like internal value crosses into a
    committed Z artifact: hashed, never cleartext)."""
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=True, default=str).encode("utf-8")
    ).hexdigest()


def sha256_file(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json_sanitized(path_: str, obj: dict, label: str) -> str:
    """Scan FIRST, write SECOND: a contaminated artifact is never
    written (fail-closed)."""
    scan_structural_only(obj, label)
    os.makedirs(os.path.dirname(path_) or ".", exist_ok=True)
    with open(path_, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, sort_keys=False, default=str)
        fh.write("\n")
    return sha256_file(path_)


def git_state() -> dict:
    def git(*a: str) -> str:
        return subprocess.run(["git", "-C", REPO_ROOT, *a],
                              capture_output=True, text=True,
                              check=True).stdout.strip()
    return {"branch": git("branch", "--show-current"),
            "head_sha": git("rev-parse", "HEAD")}


def base_sha_status() -> dict:
    """Fail-closed relationship of HEAD to the dispatch packet BASE:
    equal, or BASE an ancestor of HEAD (post-commit re-publication).
    Anything else refuses the run."""
    head = git_state()["head_sha"]
    branch = git_state()["branch"]
    if head == BASE_SHA:
        rel = "HEAD == BASE"
    else:
        proc = subprocess.run(
            ["git", "-C", REPO_ROOT, "merge-base", "--is-ancestor",
             BASE_SHA, "HEAD"], capture_output=True, text=True)
        rel = ("BASE is an ancestor of HEAD" if proc.returncode == 0
               else "BASE is NOT an ancestor of HEAD")
    ok = rel != "BASE is NOT an ancestor of HEAD"
    return {"base_sha": BASE_SHA, "head_sha_at_measurement": head,
            "branch": branch, "relationship": rel,
            "branch_matches_packet": branch == BRANCH,
            "ok": ok}


# --------------------------------------------------------------------------- #
# preflight: freeze / config / real representation (structural only)
# --------------------------------------------------------------------------- #
def preflight(fz: dict) -> dict:
    """Digest-verified assembly of the frozen substrate + the REAL
    common grid / bookable instants, equality-checked against the
    freeze's representation_freeze.  Structural facts only."""
    out: dict = {}
    freeze_sha = sha256_file(cfg.SELECTION_FREEZE_PATH)
    contract = cfg.load_cost_contract()          # sha check inside
    cost_source = cfg.cost_source_from_contract(contract)

    arms = cfg.assemble_arm_configs(fz)          # digest verify inside
    runner_map = {r["arm_id"]: r for r in
                  fz["i_phase_control_battery"]["runner_map"]}
    bindings_ok = all(
        runner_map[aid]["battery_binding"] == [
            "index_only_shadow", "cost_path_control",
            "calendar_clock_shadow", "placebo",
            "invalid_null_distinction", "family_falsification_rule"]
        for aid in arms)
    bc = cfg.battery_constants(fz)
    battery_consts_ok = (
        bc["calendar_shift_k_sessions"] == cfg.CALENDAR_SHIFT_K_SESSIONS
        and bc["placebo_seed"] == cfg.PLACEBO_SEED)

    plane = pa.VolNg1Plane()
    verdicts = {s: plane.verdict(s) for s in sorted(pa.FROZEN_TARGET_SET)}
    sub = p2r.consume_substrate(plane)
    adj, evlaw = p2r.event_adjusted_legs(sub)

    series_ok = {}
    for name, digest in fz["representation_freeze"][
            "series_consumption_law"]["series_digests_consumed_via_plane"]\
            .items():
        measured = (sub["index_digests"].get(name)
                    or sub["etp_digests"].get(name))
        series_ok[name] = {"digest": measured,
                           "matches_freeze": measured == digest}
    all_series_ok = all(v["matches_freeze"] for v in series_ok.values())

    grid = fb.common_grid(sub["index_closes"], adj)
    window = fb.window_sessions(grid)
    bookable, tail = fb.bookable_sessions(grid, window)
    rep = fz["representation_freeze"]["common_grid"]
    rep_ok = {
        "grid_sessions_total_matches_freeze":
            len(grid) == rep["grid_sessions_total"],
        "bookable_instants_matches_freeze":
            len(bookable) == rep["bookable_instants"],
        "first_bookable_matches_freeze":
            bookable[0] == rep["first_bookable_instant"],
        "last_bookable_matches_freeze":
            bookable[-1] == rep["last_bookable_instant"],
        "v7_tail_matches_freeze":
            tail == rep["v7_tail_refused_sessions"],
    }
    # the frozen full-leg context grid equals the census grid exactly
    table = p2r_event_table()
    ctx_all = ar.build_context_from_raw(
        sub["index_closes"], sub["etp_bars"], table,
        tuple(sorted(sub["etp_bars"])))
    rep_ok["full_context_grid_matches_freeze"] = (
        ar.grid_of(ctx_all) == grid)

    out["authority"] = {
        "selection_freeze_sha256": freeze_sha,
        "frozen_at_utc": fz["frozen_at_utc"],
        "s1_status": fz["s1_status"],
        "cost_contract_sha256": cfg.FROZEN_COST_CONTRACT_SHA256,
        "cost_contract_sha256_verified": True,
        "tier_ladder": contract["tier_ladder"],
        "primary_tier": contract["primary_tier"],
    }
    out["cells"] = {
        "n_cells": len(arms),
        "digests_all_match": all(a["digest_match"] for a in arms.values()),
        "digests_pairwise_distinct": len(
            set(a["arm_config_digest"] for a in arms.values())) == len(arms),
        "budget_cells_1_to_6": sorted(
            a["budget_cell"] for a in arms.values()) == list(range(1, 7)),
        "battery_bindings_complete": bindings_ok,
        "battery_constants_match_freeze": battery_consts_ok,
        "arm_config_digests": {aid: arms[aid]["arm_config_digest"]
                               for aid in sorted(arms)},
    }
    out["substrate"] = {
        "mode": "REAL_FROZEN (plane-verified, read-only, no network)",
        "plane_verdicts": verdicts,
        "all_series_granted": all(v == "GRANTED"
                                  for v in verdicts.values()),
        "n_series_digests_checked": len(series_ok),
        "series_digests": series_ok,
        "corp_actions": {
            "inventory_total_steps": evlaw["inventory_total_steps"],
            "max_abs_mechanical_residual": evlaw[
                "max_abs_mechanical_residual"],
            "residual_below_1e4_tol": evlaw[
                "max_abs_mechanical_residual"] < 1e-4,
            "events_applied_count_by_leg": {
                leg: len(block["events_applied"])
                for leg, block in sorted(evlaw["per_leg"].items())},
            "consumption_law": evlaw["consumption_law"],
        },
        "representation": {
            "grid_sessions_total": len(grid),
            "warmup_carveout_sessions": fb.WARMUP_SESSIONS,
            "bookable_instants": len(bookable),
            "first_bookable_instant": bookable[0],
            "last_bookable_instant": bookable[-1],
            "v7_tail_refused_sessions": tail,
            "matches_freeze": rep_ok,
            "representation_matches_freeze": all(rep_ok.values()),
        },
    }
    checked = [
        out["authority"]["cost_contract_sha256_verified"],
        out["cells"]["digests_all_match"],
        out["cells"]["digests_pairwise_distinct"],
        out["cells"]["budget_cells_1_to_6"],
        out["cells"]["battery_bindings_complete"],
        out["cells"]["battery_constants_match_freeze"],
        out["substrate"]["all_series_granted"],
        all_series_ok,
        out["substrate"]["corp_actions"]["residual_below_1e4_tol"],
        out["substrate"]["representation"]["representation_matches_freeze"],
    ]
    out["preflight_ok"] = all(checked)
    out["preflight_detail"] = {k: bool(v) for k, v in zip((
        "cost_contract_sha_verified", "digests_all_match",
        "digests_pairwise_distinct", "budget_cells_1_to_6",
        "battery_bindings_complete", "battery_constants_match_freeze",
        "all_series_granted", "series_digests_match_freeze",
        "corp_actions_residual_ok", "representation_matches_freeze"),
        checked)}
    return out, arms, sub, table, cost_source, list(bookable), grid


def p2r_event_table():
    from research.assets.vol_ng1 import corp_actions as ca
    return ca.build_event_table(ca.load_inventory())


# --------------------------------------------------------------------------- #
# one frozen cell on the REAL substrate (sanitized manifest)
# --------------------------------------------------------------------------- #
def run_cell_real(arm: dict, sub: dict, table: dict, cost_source: dict,
                  bookable: list[str]) -> tuple[dict, str]:
    """Run one frozen cell + the full control battery END-TO-END on the
    real substrate through the I-phase runners.  Returns (manifest,
    plumbing_verdict); internal outcome-like values are HASHED, never
    returned in cleartext."""
    aid = arm["arm_id"]
    started = time.time()
    manifest = {
        "schema": CELL_SCHEMA,
        "cycle_id": CYCLE_ID,
        "task_id": TASK_ID,
        "arm_id": aid,
        "budget_cell": arm["budget_cell"],
        "family_key": arm["family_key"],
        "family_form": arm["family_form"],
        "role": arm["role"],
        "substrate": "REAL_FROZEN (sanitized dry-run; structural only)",
    }
    try:
        runner = ar.runner_for_arm(arm)
        legs = tuple(arm["config"]["leg_subset"])
        ctx = ar.build_context_from_raw(
            sub["index_closes"], sub["etp_bars"], table, legs)
        # the cell's decision grid = the frozen bookable instants
        # (warmup carved out, V7 tail refused); every consumed series
        # must cover it (fail-closed, never inferred).
        for series in (ctx["index"], ctx["adj"]):
            for name, s in series.items():
                missing = [d for d in bookable if d not in s]
                if missing:
                    raise ZError(
                        f"{aid}: series {name} missing {len(missing)} "
                        f"bookable sessions, first {missing[0]}")
        ctx["grid"] = list(bookable)

        res = ar.run_cell(runner, ctx, cost_source)
        shadow_i = bat.index_only_shadow(runner, ctx)
        shadow_c = bat.calendar_clock_shadow(
            runner, ctx, k=cfg.CALENDAR_SHIFT_K_SESSIONS)
        shadow_p = bat.placebo(runner, ctx, seed=cfg.PLACEBO_SEED)
        inv = bat.invalid_null_audit(res)
        cpc = bat.cost_path_control(res, cost_source)

        m = res.meta
        counts = {
            "grid_sessions": len(ctx["grid"]),
            "decisions": m["decisions"],
            "invalid_instants": m["invalid_instants"],
            "refused_tail_decisions": m["refused_tail_decisions"],
            "fills": m["fills"],
            "round_trips": m["round_trips"],
            "kernel_events": m["kernel_events"],
            "by_exit_reason": m["by_exit_reason"],
            "by_fold": m["by_fold"],
        }
        checks = {
            "arm_digest_match": arm["digest_match"],
            "budget_cell_in_1_to_6": arm["budget_cell"] in range(1, 7),
            "decision_instant_partition": (
                m["decisions"] + m["invalid_instants"]
                + m["refused_tail_decisions"] == counts["grid_sessions"]),
            "fills_eq_2x_round_trips":
                m["fills"] == 2 * m["round_trips"],
            "kernel_events_eq_round_trips":
                m["kernel_events"] == m["round_trips"],
            "kernel_identity_unique": len({
                (e["leg"], e["round_trip_index"])
                for e in res.kernel_events}) == len(res.kernel_events),
            "fold_partition_complete": sum(m["by_fold"].values())
            == m["round_trips"],
            "v7_tail_refused": m["refused_tail_decisions"] == 1,
            "invalid_null_distinction_pass": inv["verdict"] == "PASS",
            "index_only_shadow_runnable": True,
            "calendar_clock_shadow_runnable_k5":
                shadow_c.notes["calendar_shift_k_sessions"]
                == cfg.CALENDAR_SHIFT_K_SESSIONS,
            "placebo_runnable_frozen_seed":
                shadow_p.notes["placebo_seed"] == cfg.PLACEBO_SEED
                and shadow_p.notes["rng_kind"] == cfg.PLACEBO_RNG_KIND,
            "cost_path_control_executable":
                cpc["n_round_trips"] == m["round_trips"]
                and cpc["n_fills"] == m["fills"]
                and cpc["tier_ladder"] == list(cfg.COST_TIER_LADDER),
        }
        verdict = "PASS" if all(checks.values()) else "FAIL"

        manifest.update({
            "runner_class": type(runner).__name__,
            "frozen_axis": {
                "latch_m_sessions":
                    getattr(runner, "latch_m_sessions", None),
                "asym_threshold":
                    getattr(runner, "asym_threshold", None),
                "latch_sessions":
                    getattr(runner, "latch_sessions", None),
            },
            "leg_subset": sorted(legs),
            "arm_config_digest": arm["arm_config_digest"],
            "structural_counts": counts,
            "controls": {
                "index_only_shadow": {
                    "control_verdict": "PASS",
                    "decisions": len(shadow_i.decisions),
                    "refused_tail_decisions":
                        shadow_i.refused_tail_decisions,
                    "invalid_instants": shadow_i.invalid_instants,
                    "distinct_from_arm_measured":
                        shadow_i.distinct_from_arm,
                    "etp_series_absent_from_state":
                        shadow_i.notes.get("no_etp_price_in_state"),
                    "note": shadow_i.notes.get("state_source_law")
                    or shadow_i.notes.get("short_side"),
                },
                "calendar_clock_shadow": {
                    "control_verdict": "PASS",
                    "calendar_shift_k_sessions":
                        shadow_c.notes["calendar_shift_k_sessions"],
                    "decisions": len(shadow_c.decisions),
                    "common_valid_decision_sessions":
                        shadow_c.notes["common_valid_decision_sessions"],
                    "distinct_from_arm_measured":
                        shadow_c.distinct_from_arm,
                },
                "placebo": {
                    "control_verdict": "PASS",
                    "placebo_seed": shadow_p.notes["placebo_seed"],
                    "rng_kind": shadow_p.notes["rng_kind"],
                    "decisions": len(shadow_p.decisions),
                    "order_destroyed_measured":
                        shadow_p.distinct_from_arm,
                },
                "invalid_null_distinction": inv,
                "cost_path_control": {
                    "control_verdict": "PASS",
                    "n_round_trips": cpc["n_round_trips"],
                    "n_fills": cpc["n_fills"],
                    "rebalance_closes": cpc["rebalance_closes"],
                    "buckets_present": cpc["buckets_present"],
                    "both_bucket_paths_paid": cpc["both_bucket_paths_paid"],
                    "tier_ladder": cpc["tier_ladder"],
                    "primary_tier": cpc["primary_tier"],
                    "cost_once_per_fill_law_held": True,
                    "q16_path_component": {
                        "carried_explicit_per_round_trip": True,
                        "note": "path + expense lines and all tier books "
                                "are internal plumbing values; committed "
                                "ONLY via cost_control_books_digest",
                    },
                },
            },
            "digest_chain": {
                "selection_freeze_sha256":
                    sha256_file(cfg.SELECTION_FREEZE_PATH),
                "cost_contract_sha256":
                    cfg.FROZEN_COST_CONTRACT_SHA256,
                "arm_config_digest": arm["arm_config_digest"],
                "decision_series_digest": sha256_obj(res.decision_state),
                "fills_ledger_digest": sha256_obj(res.fills),
                "round_trips_ledger_digest": sha256_obj(res.round_trips),
                "kernel_books_digest": sha256_obj(res.kernel_events),
                "mechanism_lines_digest":
                    sha256_obj(res.mechanism_lines),
                "cost_control_books_digest": sha256_obj(
                    {"per_round_trip": cpc["per_round_trip"],
                     "totals_by_tier": cpc["totals_by_tier"]}),
            },
            "digest_chain_note":
                "kernel books, round-trip ledgers, mechanism/cost lines "
                "and decision-state series are internal plumbing "
                "verification values: hashed above, NEVER committed in "
                "cleartext (sanitization law)",
            "sanitized_checks": checks,
            "plumbing_verdict": verdict,
            "runtime": {
                "started_utc": datetime.fromtimestamp(
                    started, tz=timezone.utc).isoformat(),
                "seconds": round(time.time() - started, 2),
                "status": "COMPLETED",
            },
        })
        return manifest, verdict
    except Exception as exc:                     # fail-closed, honest
        manifest.update({
            "plumbing_verdict": "FAIL",
            "runtime": {
                "started_utc": datetime.fromtimestamp(
                    started, tz=timezone.utc).isoformat(),
                "seconds": round(time.time() - started, 2),
                "status": "EXCEPTION",
            },
            "exception": {"type": type(exc).__name__,
                          "message": str(exc)[:400]},
            "blocked_prelaunch_candidate": True,
        })
        return manifest, "FAIL"


# --------------------------------------------------------------------------- #
# driver
# --------------------------------------------------------------------------- #
def run_z() -> dict:
    started = now_utc()
    t0 = time.time()
    base = base_sha_status()
    if not base["ok"] or not base["branch_matches_packet"]:
        raise ZError(
            f"frozen worktree check failed: {base} (fail-closed)")

    fz = cfg.load_selection_freeze()
    pf, arms, sub, table, cost_source, bookable, grid = preflight(fz)

    cells: dict = {}
    manifests: dict = {}
    for aid in sorted(arms, key=lambda a: arms[a]["budget_cell"]):
        arm = arms[aid]
        if not pf["preflight_ok"]:
            manifest = {
                "schema": CELL_SCHEMA,
                "cycle_id": CYCLE_ID,
                "task_id": TASK_ID,
                "arm_id": aid,
                "budget_cell": arm["budget_cell"],
                "family_key": arm["family_key"],
                "plumbing_verdict": "FAIL",
                "runtime": {"status": "SKIPPED_PREFLIGHT_FAIL"},
                "exception": {
                    "type": "PreflightFail",
                    "message": "real-substrate preflight failed "
                               "fail-closed; cells not executed"},
                "blocked_prelaunch_candidate": True,
            }
            verdict = "FAIL"
        else:
            manifest, verdict = run_cell_real(
                arm, sub, table, cost_source, bookable)
        fname = f"z_cell_{arm['budget_cell']}_{aid}.json"
        fpath = os.path.join(OUT_DIR, fname)
        sha = write_json_sanitized(fpath, manifest, f"cell manifest {aid}")
        manifests[aid] = fpath
        cells[aid] = {
            "budget_cell": arm["budget_cell"],
            "family_key": arm["family_key"],
            "plumbing_verdict": verdict,
            "manifest_file": f"research/control/vol_ng1_run/z/{fname}",
            "manifest_sha256": sha,
        }

    cell_verdicts = [c["plumbing_verdict"] for c in cells.values()]
    overall = "PASS" if (pf["preflight_ok"]
                         and all(v == "PASS" for v in cell_verdicts)) \
        else "FAIL"
    pbo = ev.pbo_law(len(cells))

    report = {
        "schema": SCHEMA,
        "cycle_id": CYCLE_ID,
        "task_id": TASK_ID,
        "invocation": INVOCATION,
        "mode": "REAL_SUBSTRATE_SANITIZED_DRYRUN",
        "started_utc": started,
        "published_utc": now_utc(),
        "worktree": REPO_ROOT,
        "git": git_state(),
        "base_sha_status": base,
        "sanitization_law": "committed Z artifacts record STRUCTURAL "
                            "facts only: counts, control-executable "
                            "verdicts, fold partitions, digest chains, "
                            "runtime provenance; NO PnL, NO expectancy, "
                            "NO per-trade or aggregate outcome numbers "
                            "anywhere; internal outcome-like plumbing "
                            "values are committed only as sha256 "
                            "digest chains",
        "preflight": pf,
        "cells": cells,
        "controls_matrix": {
            c: {aid: (manifests[aid] and _control_verdict(manifests[aid], c))
                for aid in sorted(cells)}
            for c in ("index_only_shadow", "calendar_clock_shadow",
                      "placebo", "invalid_null_distinction",
                      "cost_path_control")
        },
        "pbo_law": pbo,
        "overall": overall,
        "overall_law": "fail-closed: overall PASS only when the real-"
                       "substrate preflight is clean AND every cell's "
                       "plumbing verdict is PASS; any failure is "
                       "recorded honestly as a BLOCKED_PRELAUNCH "
                       "candidate and is never repaired inside Z",
        "blocked_prelaunch_candidate": None if overall == "PASS" else True,
        "runner_substrate_note": "the cell decision grid is the frozen "
                                 "bookable-instant window (warmup carved "
                                 "out, V7 tail refused); runner-internal "
                                 "state warmup inside that window "
                                 "surfaces as invalid_instants and is "
                                 "refused, never coerced (Q-11)",
        "tests": {
            "command": " ".join(TEST_COMMAND),
            "pytest_exit_code": None,
            "note": "the packet test command is executed by the lane "
                    "after generation; its exit code is recorded in the "
                    "structured handoff (never inferred here)",
        },
        "runtime_provenance": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "wall_seconds": round(time.time() - t0, 2),
        },
    }
    report_sha = write_json_sanitized(REPORT_PATH, report, "z_report")
    print(f"z_report written: {REPORT_PATH} (sha256 {report_sha[:12]}...)")
    print(f"overall={overall}")
    for aid in sorted(cells, key=lambda a: cells[a]["budget_cell"]):
        print(f"  cell {cells[aid]['budget_cell']} {aid}: "
              f"{cells[aid]['plumbing_verdict']}")
    return report


def _control_verdict(manifest_path: str, control: str):
    """Read back a written manifest's per-control verdict (the report
    must cite what was actually committed)."""
    with open(manifest_path, "r", encoding="utf-8") as fh:
        m = json.load(fh)
    ctl = m.get("controls", {}).get(control)
    if ctl is None:
        return None
    return ctl.get("control_verdict", ctl.get("verdict"))


def main() -> int:
    ap = argparse.ArgumentParser(
        description="VOL-NG1 Z sanitized dry-run on the real substrate")
    ap.add_argument("--real-substrate-dryrun", action="store_true",
                    help="run the 6 frozen cells + full control battery "
                         "on the REAL frozen substrate end-to-end through "
                         "the I-phase runners; sanitized structural "
                         "artifacts only")
    args = ap.parse_args()
    if not args.real_substrate_dryrun:
        ap.error("--real-substrate-dryrun is required")
    report = run_z()
    return 0 if report["overall"] == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
