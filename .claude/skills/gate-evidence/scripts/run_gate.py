#!/usr/bin/env python3
"""Run a command and write a machine-readable gate record plus logs."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path


def git(*args: str) -> str:
    proc = subprocess.run(["git", *args], text=True, capture_output=True, check=False)
    return proc.stdout.strip() if proc.returncode == 0 else "UNAVAILABLE"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate-id", required=True)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--expected", required=True)
    parser.add_argument("--observed", default="derived from exit code and logs")
    parser.add_argument("--evidence-dir", required=True)
    parser.add_argument("--not-run-reason")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    evidence_dir = Path(args.evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    record_path = evidence_dir / f"{args.gate_id}.json"
    stdout_path = evidence_dir / f"{args.gate_id}.stdout.log"
    stderr_path = evidence_dir / f"{args.gate_id}.stderr.log"
    if record_path.exists() and not args.overwrite:
        print(f"Refusing to overwrite {record_path}; pass --overwrite explicitly", file=sys.stderr)
        return 2

    head = git("rev-parse", "HEAD")
    branch = git("branch", "--show-current") or "DETACHED"
    before = git("status", "--porcelain=v1")
    started = dt.datetime.now(dt.timezone.utc)
    if args.not_run_reason:
        exit_code = None
        out = ""
        err = args.not_run_reason
        status = "NOT_RUN"
    elif not command:
        exit_code = None
        out = ""
        err = "No command supplied"
        status = "NOT_RUN"
    else:
        proc = subprocess.run(command, text=True, capture_output=True, check=False)
        exit_code, out, err = proc.returncode, proc.stdout, proc.stderr
        status = "PASS" if proc.returncode == 0 and not before else "FAIL"
    after = git("status", "--porcelain=v1")
    if status == "PASS" and after:
        status = "FAIL"
        err += "\nGate command left the worktree dirty."
    finished = dt.datetime.now(dt.timezone.utc)
    stdout_path.write_text(out, encoding="utf-8")
    stderr_path.write_text(err, encoding="utf-8")
    record = {
        "schema_version": 1,
        "gate_id": args.gate_id,
        "measured_at_utc": finished.isoformat().replace("+00:00", "Z"),
        "duration_seconds": round((finished - started).total_seconds(), 6),
        "owner": args.owner,
        "integration_sha": head,
        "branch": branch,
        "command": command,
        "exit_code": exit_code,
        "status": status,
        "expected": args.expected,
        "observed": args.observed if status != "NOT_RUN" else args.not_run_reason or err,
        "tree_clean_before": not bool(before),
        "tree_clean_after": not bool(after),
        "stdout_log": str(stdout_path),
        "stderr_log": str(stderr_path),
    }
    record_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
