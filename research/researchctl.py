#!/usr/bin/env python3
"""researchctl - the one documented operator entrypoint for cycle control (SHV1 sec7.1).

    python3 research/researchctl.py cycle list
    python3 research/researchctl.py cycle doctor [--json]
    python3 research/researchctl.py cycle pause <cycle> --reason "<why>"
    python3 research/researchctl.py cycle resume <cycle>          (dry-run by default)
    python3 research/researchctl.py cycle register --cycle ID --plan PATH --branch B \
            [--head SHA] [--asset A] [--lifecycle PLANNED_NOT_STARTED] [--reason R]
    python3 research/researchctl.py cycle update --cycle ID [--head SHA] \
            [--lifecycle L] [--reason R]
    python3 research/researchctl.py cycle reconcile [--dry-run] [--execute]
    python3 research/researchctl.py job list | job cancel <id>    (H3 scheduler,
            reconciled with machine-wide heavy-lock ownership; MDP-V1 M0)
    python3 research/researchctl.py locks inspect                 (HELD_PROVEN |
            FREE_PROVEN | CONTROL_STATE_DRIFT + evidence; MDP-V1 M0)
    python3 research/researchctl.py program counters

Cycle IDs resolve ONLY through the canonical registry (plans/CYCLE_REGISTRY.json)
- never from worktree existence. Writes go through governance.atomic_io
(validate -> tmp -> fsync -> rename -> read-back -> event journal) with a
compare-and-swap on the previous content sha256. EVERY registry-mutating
command regenerates plans/ACTIVE_CYCLES.json as the deterministic projection
of the canonical NON-TERMINAL records (governance.cycle_registry.save); the
projection is never hand-edited.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "research"))

from governance import atomic_io, cycle_registry, doctor  # noqa: E402

REGISTRY_PATH = REPO / "plans" / "CYCLE_REGISTRY.json"

_ASSET_BY_PREFIX = (("CRYPTO", "crypto"), ("STOCKS", "stocks"), ("FOREX", "forex"))


def _git(*args: str, cwd: Path = REPO) -> str:
    return subprocess.run(("git", "-C", str(cwd)) + args,
                          capture_output=True, text=True, check=True).stdout.strip()


def _git_opt(*args: str, cwd: Path) -> str:
    """git output or '' on failure (measurement must never guess)."""
    try:
        return _git(*args, cwd=cwd)
    except subprocess.CalledProcessError:
        return ""


def _load_registry() -> dict:
    return cycle_registry.load(REGISTRY_PATH)


def _derive_asset(cycle_id: str, explicit: str | None) -> str:
    if explicit:
        return explicit
    for prefix, asset in _ASSET_BY_PREFIX:
        if cycle_id.startswith(prefix):
            return asset
    raise SystemExit(
        f"refused: cannot derive asset for {cycle_id!r} - pass --asset explicitly"
    )


def _measure_heads(reg: dict) -> tuple:
    """Measured branch head per cycle with an existing integration worktree.

    Returns (measured, unmeasurable): a cycle is unmeasurable when it has no
    worktree on record or git refuses to answer — never guessed, never faked.
    """
    measured, unmeasurable = {}, []
    for rec in reg["cycles"]:
        wt = rec.get("integration_worktree")
        if not wt:
            unmeasurable.append(rec["cycle_id"])
            continue
        head = _git_opt("rev-parse", "HEAD", cwd=Path(wt))
        if head and cycle_registry._HEX40.match(head):
            measured[rec["cycle_id"]] = head
        else:
            unmeasurable.append(rec["cycle_id"])
    return measured, unmeasurable


# ---------------------------------------------------------------- cycle list
def cmd_cycle_list(args) -> int:
    reg = _load_registry()
    width = 16
    print(f"{'CYCLE':<{width}} {'LIFECYCLE':<24} {'BUDGET':<8} HEAD      BRANCH")
    for rec in reg["cycles"]:
        print(f"{rec['cycle_id']:<{width}} {rec['lifecycle']:<24} "
              f"{rec['budget']['used']}/{rec['budget']['max']:<6} "
              f"{rec['head'][:7]}  {rec['branch'] or '-'}")
        for w in rec.get("adapter_warnings", []):
            print(f"    ! {w}")
    if args.verbose:
        for rec in reg["cycles"]:
            print(f"\n== {rec['cycle_id']} ==")
            print(json.dumps({k: rec[k] for k in (
                "plan", "phase", "next_authorized_action", "hard_stop_reason",
                "pause_packet", "s1", "go_phrase_state")}, indent=1, ensure_ascii=False))
    return 0


# ---------------------------------------------------------------- cycle doctor
def cmd_cycle_doctor(args) -> int:
    """Read-only consistency diagnostics (sec7.6), severity-labeled (M0).

    Delegates to governance.doctor.check so the CLI and the module can never
    diverge: projection vs canonical NON-TERMINAL records (+ projection byte
    equality), worktree/branch/head authority, legacy states, budgets, S1
    seal, heartbeats, live workers, heavy-lock ownership, frozen artifacts.
    Findings are labeled; doctor never repairs.
    """
    if getattr(args, "json", False):
        print(json.dumps({"findings": doctor.check_detailed(root=REPO)},
                         indent=1, ensure_ascii=False))
    else:
        print(doctor.render(doctor.check(root=REPO)))
    return 0  # findings are diagnostics; exit code reflects tool success, severity is labeled


# ---------------------------------------------------------------- cycle pause/resume
def cmd_cycle_pause(args) -> int:
    reg = _load_registry()
    prev_sha = atomic_io.sha256_file(REGISTRY_PATH)
    cycle_registry.transition(reg, args.cycle, "PAUSED_MAINTENANCE",
                              reason=args.reason, hard_stop_reason=args.hard_stop_reason or "OPERATOR_REQUESTED")
    reg["write_token"] = f"pause:{args.cycle}:{args.reason[:60]}"
    new_sha = cycle_registry.save(REGISTRY_PATH, reg, expect_prev_sha=prev_sha)
    print(f"paused {args.cycle} (registry sha {new_sha[:12]}); legacy state files untouched")
    return 0


def cmd_cycle_resume(args) -> int:
    reg = _load_registry()
    rec = cycle_registry.resolve(reg, args.cycle)
    if not getattr(args, "execute_live", False):
        print(json.dumps({
            "mode": "DRY_RUN (SHV1 sec10: SHV1 does not authorize scored execution; "
                    "no state was changed)",
            "cycle": rec["cycle_id"],
            "resume_checklist": [
                "SHV1 verdict SYSTEM_HARDENING_V1_PASS from independent A7",
                "re-measure integration HEAD/tree/workers/locks",
                "compare scientific hashes against the pause packet",
                "verify budget, denominators, S1 seal",
                "rerun the cycle's applicable cheap gates",
                "fresh owner GO at the cycle's own prelaunch (P-8; no carry across pause)",
            ],
            "next_safe_action": rec["next_authorized_action"],
            "pause_packet": rec["pause_packet"],
        }, indent=1, ensure_ascii=False))
        return 0
    if rec["lifecycle"] not in cycle_registry.PAUSED:
        print(f"refused: {rec['cycle_id']} is {rec['lifecycle']}, not paused", file=sys.stderr)
        return 2
    prev_sha = atomic_io.sha256_file(REGISTRY_PATH)
    cycle_registry.transition(reg, args.cycle, "ACTIVE_LIGHT", reason=args.reason or "resume")
    reg["write_token"] = f"resume:{args.cycle}"
    cycle_registry.save(REGISTRY_PATH, reg, expect_prev_sha=prev_sha)
    print(f"resumed {args.cycle} to ACTIVE_LIGHT (registry only; scored execution still "
          f"requires the cycle's own gates + fresh owner GO per P-8)")
    return 0


# ------------------------------------------------- cycle register/update/reconcile
def cmd_cycle_register(args) -> int:
    """Register a NEW planned cycle through the atomic CAS + journal path.

    The plan file must exist in this tree; the head is optional (an omitted
    head records the unmeasured placeholder until the first reconcile/update).
    The projection is regenerated by the same save.
    """
    plan = Path(args.plan)
    if not plan.is_absolute():
        plan = REPO / plan
    if not plan.exists():
        print(f"refused: plan file does not exist: {args.plan}", file=sys.stderr)
        return 2
    asset = _derive_asset(args.cycle, args.asset)
    reg = _load_registry()
    prev_sha = atomic_io.sha256_file(REGISTRY_PATH)
    rec, new_sha = cycle_registry.register_cycle(
        REGISTRY_PATH, reg, prev_sha=prev_sha, cycle_id=args.cycle, plan=args.plan,
        branch=args.branch, head=args.head, lifecycle=args.lifecycle, asset=asset,
        worktree=args.worktree or "", budget_max=args.budget_max,
        go_phrase=args.go_phrase or "", reason=args.reason,
    )
    print(json.dumps({
        "registered": rec["cycle_id"],
        "lifecycle": rec["lifecycle"],
        "head": rec["head"],
        "head_note": (None if args.head else
                      "unmeasured placeholder; run `cycle reconcile --execute` or "
                      "`cycle update --head` once the branch exists"),
        "registry_sha256": new_sha,
        "projection": "regenerated from canonical non-terminal records",
    }, indent=1, ensure_ascii=False))
    return 0


def cmd_cycle_update(args) -> int:
    """Update a cycle's measured HEAD and/or lifecycle atomically.

    Touches only the requested fields (+ bookkeeping); enforces the
    transition table (TERMINAL is absorbing; closing kills the GO phrase
    per P-8); records every applied change as an append-only journal event.
    """
    if args.head is None and args.lifecycle is None and args.phase is None \
            and args.workers is None and args.active_heavy is None \
            and getattr(args, "worktree", None) is None:
        print("refused: nothing to update (pass --head and/or --lifecycle)", file=sys.stderr)
        return 2
    reg = _load_registry()
    prev_sha = atomic_io.sha256_file(REGISTRY_PATH)
    changes, new_sha = cycle_registry.update_cycle(
        REGISTRY_PATH, reg, prev_sha=prev_sha, cycle_id=args.cycle,
        head=args.head, lifecycle=args.lifecycle, reason=args.reason,
        phase=args.phase, worktree=args.worktree,
        workers=None if args.workers is None else int(args.workers),
        active_heavy=None if args.active_heavy is None
        else args.active_heavy == "true",
    )
    print(json.dumps({
        "cycle": args.cycle,
        "changes": changes or ["NO-OP (already current)"],
        "registry_sha256": new_sha,
        "projection": "regenerated from canonical non-terminal records" if changes else "untouched",
    }, indent=1, ensure_ascii=False))
    return 0


def cmd_cycle_reconcile(args) -> int:
    """Compare the canonical registry to measured branch heads + projection.

    Default is a DRY-RUN diff (writes nothing). --execute performs all
    updates as ONE compare-and-swap save plus append-only journal events;
    drift is recorded, never normalized silently, and legacy state files are
    never rewritten. A concurrent writer makes --execute fail closed on the
    CAS (re-run to converge).
    """
    execute = bool(getattr(args, "execute", False))
    reg = _load_registry()
    measured, unmeasurable = _measure_heads(reg)
    prev_sha = atomic_io.sha256_file(REGISTRY_PATH)
    if not execute:
        plan = cycle_registry.plan_reconciliation(reg, measured)
        plan["mode"] = "DRY_RUN"
        plan["projection_drift"] = cycle_registry.projection_drift(REGISTRY_PATH, reg)
        plan["unmeasurable"] = unmeasurable
        plan["note"] = ("dry-run: nothing written; re-run with --execute to apply all "
                        "head updates as one CAS save + journal events and regenerate "
                        "the projection")
        print(json.dumps(plan, indent=1, ensure_ascii=False))
        return 0
    report, new_sha = cycle_registry.reconcile_registry(
        REGISTRY_PATH, reg, prev_sha=prev_sha, measured_heads=measured,
        reason=args.reason or "operator reconcile",
    )
    report["mode"] = report.get("mode", "EXECUTED")
    report["unmeasurable"] = unmeasurable
    report["registry_sha256"] = new_sha
    print(json.dumps(report, indent=1, ensure_ascii=False))
    return 0


# ---------------------------------------------------------------- jobs / locks / counters
def cmd_job_list(args) -> int:
    """ONE reconciled view: scheduler journal UNION live heavy-lock registry.

    Every row is labeled with its source ("scheduler" / "heavy_lock"); the
    heavy-lock row carries liveness evidence (pid alive, process-start token
    match). A dead-pid or token-mismatch lock row is surfaced as
    CONTROL_STATE_DRIFT - never dropped silently (MDP-V1 M0).
    """
    try:
        from governance import scheduler
    except ImportError:
        print("scheduler module not present in this tree (lands with SHV1 H3/H5)")
        return 3
    print(json.dumps(scheduler.reconciled_jobs(), indent=1, ensure_ascii=False))
    return 0


def cmd_job_cancel(args) -> int:
    try:
        from governance import scheduler
    except ImportError:
        print("scheduler module not present in this tree (lands with SHV1 H3/H5)")
        return 3
    print(scheduler.cancel_job(args.job_id))
    return 0


def cmd_locks_inspect(args) -> int:
    """Tri-state inspection: HELD_PROVEN | FREE_PROVEN | CONTROL_STATE_DRIFT.

    HELD_PROVEN proves the exact live holder (pid alive + process-start
    token match + flock actually held); FREE_PROVEN requires no registry row
    AND a free flock; every ambiguous state is CONTROL_STATE_DRIFT. Ambiguous
    NEVER becomes FREE. Read-only: never reclaims, never repairs.
    """
    from governance import heavy_lock

    report = heavy_lock.inspect()
    runtime = Path(report["evidence"]["registry_path"]).parent
    report["runtime_dir"] = str(runtime)
    hist = runtime / heavy_lock.HISTORY_NAME
    if hist.exists():
        lines = hist.read_text(encoding="utf-8").splitlines()
        report["last_history_rows"] = [json.loads(l) for l in lines[-3:] if l.strip()]
    print(json.dumps(report, indent=1, ensure_ascii=False))
    return 0


def cmd_program_counters(args) -> int:
    led = (REPO / "research" / "wayfinder" / "HYPOTHESIS_LEDGER.md").read_text(encoding="utf-8")
    line = next((l for l in led.splitlines() if "Program total:" in l), "")
    print(json.dumps({
        "ledger_line": line.strip(),
        "authority": "HYPOTHESIS_LEDGER.md (P-9: the only cross-asset denominator authority)",
        "s1": "SEALED_UNTOUCHED everywhere",
    }, indent=1, ensure_ascii=False))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="researchctl")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("cycle")
    csub = p.add_subparsers(dest="cycle_cmd", required=True)
    c = csub.add_parser("list"); c.add_argument("-v", "--verbose", action="store_true"); c.set_defaults(fn=cmd_cycle_list)
    c = csub.add_parser("doctor"); c.add_argument("--json", action="store_true"); c.set_defaults(fn=cmd_cycle_doctor)
    c = csub.add_parser("pause"); c.add_argument("cycle"); c.add_argument("--reason", required=True)
    c.add_argument("--hard-stop-reason", default=None); c.set_defaults(fn=cmd_cycle_pause)
    c = csub.add_parser("resume"); c.add_argument("cycle"); c.add_argument("--reason", default="")
    c.add_argument("--execute-live", action="store_true"); c.set_defaults(fn=cmd_cycle_resume)
    c = csub.add_parser("register")
    c.add_argument("--cycle", required=True, help="new cycle ID (exact, unique)")
    c.add_argument("--plan", required=True, help="plan path (must exist in this tree)")
    c.add_argument("--branch", required=True, help="integration branch")
    c.add_argument("--head", default=None, help="measured branch HEAD sha (optional; unmeasured placeholder when omitted)")
    c.add_argument("--asset", default=None, help="crypto|stocks|forex (derived from the cycle ID prefix when omitted)")
    c.add_argument("--lifecycle", default="PLANNED_NOT_STARTED",
                   choices=cycle_registry.REGISTERABLE_LIFECYCLES)
    c.add_argument("--worktree", default="", help="integration worktree path (empty while planned)")
    c.add_argument("--budget-max", type=int, default=6)
    c.add_argument("--go-phrase", default="", help="registered GO phrase (a GO is still typed only at its own gate, P-8)")
    c.add_argument("--reason", default="register planned cycle")
    c.set_defaults(fn=cmd_cycle_register)
    c = csub.add_parser("update")
    c.add_argument("--cycle", required=True)
    c.add_argument("--head", default=None, help="new measured branch HEAD sha (40-hex)")
    c.add_argument("--lifecycle", default=None, choices=cycle_registry.LIFECYCLE)
    c.add_argument("--phase", default=None, help="free-text measured phase label")
    c.add_argument("--worktree", default=None,
                   help="integration worktree absolute path (binds the structured "
                        "integration_worktree field; required for head measurement)")
    c.add_argument("--workers", default=None, help="live worker count (non-negative int)")
    c.add_argument("--active-heavy", default=None, choices=["true", "false"],
                   help="whether the cycle currently owns the machine-wide heavy slot")
    c.add_argument("--reason", default="operator update")
    c.set_defaults(fn=cmd_cycle_update)
    c = csub.add_parser("reconcile")
    c.add_argument("--execute", action="store_true",
                   help="apply all updates as one CAS save + journal events (default: dry-run diff)")
    c.add_argument("--dry-run", action="store_true", help="explicit dry-run (default)")
    c.add_argument("--reason", default="operator reconcile")
    c.set_defaults(fn=cmd_cycle_reconcile)

    p = sub.add_parser("job")
    jsub = p.add_subparsers(dest="job_cmd", required=True)
    j = jsub.add_parser("list"); j.set_defaults(fn=cmd_job_list)
    j = jsub.add_parser("cancel"); j.add_argument("job_id"); j.set_defaults(fn=cmd_job_cancel)

    p = sub.add_parser("locks"); p.add_argument("rest", nargs="?", default="inspect"); p.set_defaults(fn=cmd_locks_inspect)
    p = sub.add_parser("program"); cpsub = p.add_subparsers(dest="prog_cmd", required=True)
    c = cpsub.add_parser("counters"); c.set_defaults(fn=cmd_program_counters)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
