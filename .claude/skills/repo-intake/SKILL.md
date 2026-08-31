---
name: repo-intake
description: Re-measure repository identity, dirtiness, worktrees, active research workers, plans, and Python before any quant-repo implementation, dispatch, scoring, audit, or status claim.
allowed-tools: Bash, Read, Grep, Glob
---

# Repository intake

Run this before planning or writing:

```bash
python3 .claude/skills/repo-intake/scripts/repo_snapshot.py --plan <PLAN.md>
```

Use `--require-clean`, `--expected-branch`, or `--expected-head` when the task
packet freezes them. Treat a nonzero exit or any mismatch as a named blocker.

Then read the selected PLAN completely and inspect its current authority files.
The script deliberately does not infer run clocks, denominators, gate PASS, or
S1 state: obtain those from current machine-readable artifacts and reconcile
them explicitly. Preserve pre-existing dirty files as owner changes.
