#!/usr/bin/env python3
"""Emit a read-only JSON snapshot of the current research checkout."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def run(args: list[str], cwd: Path) -> tuple[int, str]:
    proc = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    return proc.returncode, proc.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", default="PLAN.md")
    parser.add_argument("--expected-branch")
    parser.add_argument("--expected-head")
    parser.add_argument("--require-clean", action="store_true")
    args = parser.parse_args()

    code, root_text = run(["git", "rev-parse", "--show-toplevel"], Path.cwd())
    if code:
        print(json.dumps({"status": "BLOCKED", "reason": "NOT_A_GIT_REPOSITORY"}))
        return 2
    root = Path(root_text).resolve()
    _, head = run(["git", "rev-parse", "HEAD"], root)
    _, branch = run(["git", "branch", "--show-current"], root)
    _, status = run(["git", "status", "--porcelain=v1"], root)
    _, worktrees = run(["git", "worktree", "list", "--porcelain"], root)
    _, python_version = run([str(root / ".venv/bin/python"), "--version"], root) if (root / ".venv/bin/python").exists() else (1, "")

    _, process_text = run(["ps", "-axo", "pid=,command="], root)
    worker_terms = ("portfolio_runner", "matrix_runner", "optimize", "reproduction_harness")
    workers = [line.strip() for line in process_text.splitlines() if any(term in line for term in worker_terms) and str(os.getpid()) not in line]

    mismatches: list[str] = []
    plan_path = (root / args.plan).resolve()
    if not plan_path.is_file() or root not in plan_path.parents:
        mismatches.append("PLAN_MISSING_OR_OUTSIDE_REPO")
    if args.expected_branch and branch != args.expected_branch:
        mismatches.append("BRANCH_MISMATCH")
    if args.expected_head and head != args.expected_head:
        mismatches.append("HEAD_MISMATCH")
    if args.require_clean and status:
        mismatches.append("DIRTY_TREE")

    report = {
        "status": "GO" if not mismatches else "BLOCKED",
        "mismatches": mismatches,
        "root": str(root),
        "cwd": str(Path.cwd().resolve()),
        "plan": str(plan_path),
        "head": head,
        "branch": branch or "DETACHED",
        "clean": not bool(status),
        "porcelain": status.splitlines(),
        "python": python_version or "MISSING_.venv/bin/python",
        "active_research_workers": workers,
        "worktree_porcelain": worktrees.splitlines(),
        "not_measured": ["run_clock", "published_denominator", "observed_denominator", "gate_verdicts", "S1_access"],
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not mismatches else 2


if __name__ == "__main__":
    raise SystemExit(main())
