#!/usr/bin/env python3
"""Offline behavior tests for hook_pre_tool.py (run from repo root).

Covers the 2026-09-11 scoped push rule: root-Lead pushes are allowed under
the owner standing delegation; lane worktree pushes (.worktrees/ in command
or cwd) are denied; all other absolute denies keep firing.
"""
import json
import subprocess

H = "plugins/quant-research-orchestrator/scripts/hook_pre_tool.py"
ROOT = "/Users/hoangminhlong/my-quantitative"
PUSH = "git push"

cases = [
    ("T1 root push -> ALLOW", "Bash", {"command": PUSH + " origin main"}, ROOT, False),
    ("T2 lane-cwd push -> DENY", "Bash", {"command": PUSH}, ROOT + "/.worktrees/v17/a3-data", True),
    ("T3 lane -C push -> DENY", "Bash",
     {"command": "git -C " + ROOT + "/.worktrees/v17/a3-data push origin b"}, ROOT, True),
    ("T4 reset --hard -> DENY", "Bash", {"command": "git reset --hard HEAD"}, ROOT, True),
    ("T5 status -> ALLOW", "Bash", {"command": "git status --short"}, ROOT, False),
    ("T6 merge main -> DENY", "Bash", {"command": "git merge orca/x-branch main"}, ROOT, True),
    ("T7 root fetch -> ALLOW", "Bash", {"command": "git fetch origin"}, ROOT, False),
    ("T8 plain push cwd missing -> ALLOW(root default)", "Bash",
     {"command": PUSH}, "", False),
]

fails = 0
for name, tool, tinput, cwd, expect_deny in cases:
    payload = json.dumps({"tool_name": tool, "tool_input": tinput, "cwd": cwd})
    r = subprocess.run(["python3", H], input=payload, capture_output=True, text=True)
    out = r.stdout.strip()
    denied = '"permissionDecision": "deny"' in out
    ok = denied == expect_deny
    fails += 0 if ok else 1
    print(("PASS " if ok else "FAIL ") + name)
    if out:
        print("      " + out[:160])

print(f"\n{len(cases) - fails}/{len(cases)} pass")
raise SystemExit(1 if fails else 0)
