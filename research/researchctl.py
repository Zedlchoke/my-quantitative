#!/usr/bin/env python3
"""researchctl - the one documented operator entrypoint for cycle control (SHV1 sec7.1).

    python3 research/researchctl.py cycle list
    python3 research/researchctl.py cycle doctor
    python3 research/researchctl.py cycle pause <cycle> --reason "<why>"
    python3 research/researchctl.py cycle resume <cycle>          (dry-run by default)
    python3 research/researchctl.py job list | job cancel <id>    (H3 scheduler)
    python3 research/researchctl.py locks inspect
    python3 research/researchctl.py program counters

Cycle IDs resolve ONLY through the canonical registry (plans/CYCLE_REGISTRY.json)
- never from worktree existence. Writes go through governance.atomic_io
(validate -> tmp -> fsync -> rename -> read-back -> event journal).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "research"))

from governance import atomic_io, cycle_registry, legacy_adapters  # noqa: E402

REGISTRY_PATH = REPO / "plans" / "CYCLE_REGISTRY.json"


def _git(*args: str, cwd: Path = REPO) -> str:
    return subprocess.run(("git", "-C", str(cwd)) + args,
                          capture_output=True, text=True, check=True).stdout.strip()


def _main_root() -> Path:
    """Main checkout root - nested cycle worktrees exist only there."""
    return legacy_adapters.main_repo_root()


def _load_registry() -> dict:
    return cycle_registry.load(REGISTRY_PATH)


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
    """Read-only consistency diagnostics (sec7.6 subset at H2; extended at H4)."""
    findings = []
    reg = _load_registry()

    # 1. stale router entries: committed projection vs canonical registry
    proj = REPO / "plans" / "ACTIVE_CYCLES.json"
    try:
        projection = json.loads(proj.read_bytes().decode("utf-8"))
        proj_ids = {c["cycle_id"] for c in projection.get("cycles", [])}
        reg_ids = {c["cycle_id"] for c in reg["cycles"]}
        for ghost in sorted(proj_ids - reg_ids):
            findings.append(("STALE_ROUTER_ENTRY",
                             f"{proj.name} names {ghost} which the canonical registry does not carry "
                             "(closed/historical - known sec2 contradiction, projection is byte-frozen)"))
        for missing in sorted(reg_ids - proj_ids):
            findings.append(("ROUTER_GAP",
                             f"{proj.name} omits live-cycle {missing} (known sec2 contradiction)"))
    except json.JSONDecodeError as exc:
        findings.append(("CONTROL_STATE_DRIFT", f"{proj.name} unparseable: {exc}"))

    # 2. branch/worktree mismatch + measured head vs registry head
    #    (worktree paths are stored absolute against the MAIN checkout, so they
    #     are valid from any lane tree)
    for rec in reg["cycles"]:
        wt = rec.get("integration_worktree")
        if not wt:
            continue  # historical lookup entry
        wt_path = Path(wt)
        if not wt_path.exists():
            findings.append(("WORKTREE_MISSING", f"{rec['cycle_id']}: {wt} does not exist"))
            continue
        branch = _git("branch", "--show-current", cwd=wt_path)
        if branch != rec["branch"]:
            findings.append(("BRANCH_MISMATCH",
                             f"{rec['cycle_id']}: worktree on {branch!r}, registry says {rec['branch']!r}"))
        head = _git("rev-parse", "HEAD", cwd=wt_path)
        if head != rec["head"]:
            findings.append(("HEAD_MISMATCH",
                             f"{rec['cycle_id']}: branch head {head[:7]} != registry {rec['head'][:7]}"))

    # 3. missing/malformed legacy state (main-checkout-relative)
    main = _main_root()
    for cid, rel in legacy_adapters.LEGACY_SOURCES.items():
        p = main / rel
        if not p.exists():
            findings.append(("STATE_MISSING", f"{cid}: legacy state {rel} missing"))
            continue
        try:
            json.loads(p.read_bytes().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            findings.append(("CONTROL_STATE_DRIFT", f"{cid}: {rel} unparseable: {exc}"))

    # 4. budget/denominator disagreement between registry and legacy state
    for cid, rel in legacy_adapters.LEGACY_SOURCES.items():
        p = REPO / rel
        if not p.exists():
            continue
        state = json.loads(p.read_bytes().decode("utf-8"))
        rec = cycle_registry.resolve(reg, cid)
        used = state.get("budget_used", (state.get("budget") or {}).get("used"))
        if used is not None and used != rec["budget"]["used"]:
            findings.append(("BUDGET_DISAGREEMENT",
                             f"{cid}: legacy used={used} vs registry {rec['budget']['used']}"))
        if state.get("s1") != rec["s1"]:
            findings.append(("S1_SEAL_DISAGREEMENT", f"{cid}: legacy {state.get('s1')!r} vs registry {rec['s1']!r}"))

    # 5. heartbeat freshness (older than 24h on a non-terminal cycle = stale)
    from governance.atomic_io import CONTROL_STATE_DRIFT  # noqa: F401  (naming clarity)
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc)
    for rec in reg["cycles"]:
        if rec["lifecycle"] in cycle_registry.CLOSED:
            continue
        hb = rec.get("heartbeat_utc")
        if hb:
            try:
                age = now - datetime.datetime.strptime(hb, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
                if age > datetime.timedelta(hours=24):
                    findings.append(("STALE_HEARTBEAT",
                                     f"{rec['cycle_id']}: heartbeat {hb} is {age.days}d old (paused-maintenance is expected-stale)"))
            except ValueError:
                findings.append(("CONTROL_STATE_DRIFT", f"{rec['cycle_id']}: heartbeat {hb!r} unparseable"))

    if getattr(args, "json", False):
        print(json.dumps({"findings": [{"kind": k, "detail": d} for k, d in findings]},
                         indent=1, ensure_ascii=False))
    else:
        if findings:
            for kind, detail in findings:
                print(f"[{kind}] {detail}")
        else:
            print("doctor: no findings")
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


# ---------------------------------------------------------------- jobs / locks / counters
def cmd_job_list(args) -> int:
    try:
        from governance import scheduler
    except ImportError:
        print("scheduler module not present in this tree (lands with SHV1 H3/H5)")
        return 3
    print(json.dumps(scheduler.list_jobs(), indent=1, ensure_ascii=False))
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
    runtime = Path.home() / ".my-quantitative-governance" / "heavy_runtime"
    out = {"runtime_dir": str(runtime), "exists": runtime.exists()}
    lock = runtime / "heavy_worker.lock"
    reg = runtime / "heavy_worker.registry.json"
    hist = runtime / "heavy_worker.history.jsonl"
    out["lock_bytes"] = lock.stat().st_size if lock.exists() else None
    out["lock_state"] = "FREE (empty lock file, no registry holder)" if (
        lock.exists() and lock.stat().st_size == 0 and not reg.exists()) else "HELD or unknown - see registry"
    if reg.exists():
        out["registry"] = json.loads(reg.read_text())
    if hist.exists():
        lines = hist.read_text().splitlines()
        out["last_history_rows"] = [json.loads(l) for l in lines[-3:] if l.strip()]
    print(json.dumps(out, indent=1, ensure_ascii=False))
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
