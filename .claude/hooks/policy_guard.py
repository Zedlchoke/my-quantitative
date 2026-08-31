#!/usr/bin/env python3
"""Block a small, explicit set of destructive shell commands.

Claude Code sends one JSON object on stdin. Exit 2 is required to block a
PreToolUse call; every unrecognised or ordinary command is left to Claude
Code's normal permission flow.
"""

from __future__ import annotations

import json
import re
import sys


BLOCKED = (
    (re.compile(r"(^|[;&|]\s*)rm\s+[^\n;&|]*-[^\n;&|]*r[^\n;&|]*f", re.I), "recursive forced deletion"),
    (re.compile(r"\bgit\s+reset\s+--hard\b", re.I), "git hard reset"),
    (re.compile(r"\bgit\s+clean\s+-[^\s]*f[^\s]*(?:d|x)|\bgit\s+clean\s+-[^\s]*(?:d|x)[^\s]*f", re.I), "forced git clean"),
    (re.compile(r"\bgit\s+checkout\s+--\s", re.I), "destructive checkout restore"),
    (re.compile(r"\bgit\s+restore\b(?![^\n;&|]*--staged\b)", re.I), "unstaged file restore"),
    (re.compile(r"\bgit\s+push\b[^\n;&|]*(?:--force(?:-with-lease)?|-f\b)", re.I), "forced git push"),
    (re.compile(r"\bgit\s+branch\s+-D\b", re.I), "forced branch deletion"),
    (re.compile(r"\bgit\s+worktree\s+(?:remove|prune)\b", re.I), "worktree removal"),
    (re.compile(r"\bgit\s+reflog\s+expire\b", re.I), "reflog expiration"),
)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Policy guard could not parse hook input: {exc}", file=sys.stderr)
        return 2

    tool_name = str(payload.get("tool_name", ""))
    if tool_name not in {"Bash", "PowerShell"}:
        return 0
    command = str(payload.get("tool_input", {}).get("command", ""))
    for pattern, reason in BLOCKED:
        if pattern.search(command):
            print(
                f"Blocked by repository policy: {reason}. "
                "Use a recoverable, explicit alternative or obtain owner direction.",
                file=sys.stderr,
            )
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
