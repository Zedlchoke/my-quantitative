#!/usr/bin/env python3
"""Verify a linked worktree without mutating it."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def git(path: Path, *args: str) -> tuple[int, str]:
    proc = subprocess.run(["git", "-C", str(path), *args], text=True, capture_output=True, check=False)
    return proc.returncode, proc.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True)
    parser.add_argument("--branch")
    parser.add_argument("--head", required=True)
    parser.add_argument("--require-clean", action="store_true")
    parser.add_argument("--detached", action="store_true")
    args = parser.parse_args()
    path = Path(args.path).resolve()
    failures = []
    if not path.is_dir():
        failures.append("PATH_MISSING")
        actual_head = actual_branch = status = ""
    else:
        head_code, actual_head = git(path, "rev-parse", "HEAD")
        branch_code, actual_branch = git(path, "branch", "--show-current")
        status_code, status = git(path, "status", "--porcelain=v1")
        if head_code or branch_code or status_code:
            failures.append("NOT_A_VALID_WORKTREE")
    if len(args.head) != 40 or any(c not in "0123456789abcdefABCDEF" for c in args.head):
        failures.append("EXPECTED_HEAD_NOT_FULL_SHA")
    if actual_head and actual_head != args.head:
        failures.append("HEAD_MISMATCH")
    if args.detached and actual_branch:
        failures.append("EXPECTED_DETACHED")
    if not args.detached and args.branch and actual_branch != args.branch:
        failures.append("BRANCH_MISMATCH")
    if args.require_clean and status:
        failures.append("DIRTY_TREE")
    print(json.dumps({
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "path": str(path),
        "head": actual_head,
        "branch": actual_branch or "DETACHED",
        "clean": not bool(status),
        "porcelain": status.splitlines(),
    }, indent=2, sort_keys=True))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
