---
name: test-router
description: Select the smallest relevant pytest commands for changed crypto protocol, strategy, UI, stocks, forex, or Claude configuration files, then escalate without hiding NOT RUN suites.
allowed-tools: Bash, Read, Grep, Glob
---

# Test router

Pass changed paths to the deterministic router:

```bash
python3 .claude/skills/test-router/scripts/route_tests.py <changed-file>...
```

Run the returned targeted commands from the correct clean worktree. After every
A1 cherry-pick run that lane's frozen test command, not only the router output.

Escalation order:

1. syntax/static check for changed scripts;
2. directly mapped unit tests;
3. protocol compatibility/reconciliation for shared research code;
4. integration/golden tests required by the PLAN;
5. full `.venv/bin/python -m pytest -q` only when the PLAN requires it, alone
   with no scoring/reproduction worker.

An absent future stocks/forex test path is `NOT_RUN` and blocks its declared
gate; do not substitute a nearby crypto test.
