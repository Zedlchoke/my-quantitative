---
name: agent-handoff
description: Produce a compact machine-readable lane or audit handoff with identity, ownership, commit, diff, tests, evidence, blockers, and exact next action for A1.
allowed-tools: Bash, Read, Grep, Glob
---

# Agent handoff

Copy [handoff.template.json](assets/handoff.template.json) into the manifest's
assigned handoff path and replace every placeholder. Before returning, verify:

```bash
git rev-parse HEAD
git branch --show-current
git status --porcelain=v1
git diff --check HEAD^ HEAD
```

The lane should return one focused commit and an empty porcelain status. Record
every test as PASS/FAIL/NOT_RUN with command and exit code. Do not claim the full
suite, integration, A7 authorization, publication, or downstream gates unless
this agent actually owned and ran them.

If no commit was produced, set it to null and explain the blocker. A handoff does
not grant A1 permission to overlook out-of-scope files or failed gates.
