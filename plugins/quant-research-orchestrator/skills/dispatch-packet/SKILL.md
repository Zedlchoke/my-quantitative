---
name: dispatch-packet
description: "Build a self-sufficient 2-8KB dispatch packet for one quant subagent: role, objective, exact base SHA + absolute worktree + branch, allowed/forbidden paths, frozen inputs with hashes, required outputs, test commands, stop conditions, commit rules, handoff path and format. Use before every Agent dispatch in this repo."
---

# Dispatch packet builder

A packet must be self-sufficient: the subagent may not see AGENTS.md
(quant-explorer runtime exception) or project memory. Include exactly:

```text
ROLE:            quant-explorer | quant-implementer | quant-reproducer | quant-auditor
CYCLE / TASK:    ZCODE-ORCHESTRATION-V3 / <task_id>
OBJECTIVE:       one paragraph, no scope creep
BASE:            full 40-char dispatch SHA + absolute worktree + branch
VERIFY FIRST:    pwd / git branch --show-current / git rev-parse HEAD must match
ALLOWED PATHS:   exact list (implementer/auditor writes)
FORBIDDEN PATHS: plans/CYCLE_REGISTRY.json, plans/ACTIVE_CYCLES.json,
                 research/wayfinder/HYPOTHESIS_LEDGER.md, other lanes, S1 paths
REQUIRED INPUTS: path + sha256 (reproducer must verify before use)
DELIVERABLES:    required outputs + the exact handoff_path to write
TEST COMMANDS:   exact targeted commands (never the full suite)
STOP CONDITIONS: SCOPE_ESCAPE_REQUIRED / FROZEN_SHA_MISMATCH / INPUT_MISMATCH /
                 PACKET_INSUFFICIENT — stop and report, never improvise
COMMIT RULES:    one focused commit, pathspec staging only, no push/merge/rebase
HANDOFF FORMAT:  zcode_orch_v3_handoff@1 field list (see structured-handoff skill)
```

Rules:

- 2-8 KB. No unrelated terminal histories, no scored outcomes for proposal
  lanes, no "how to pass" guidance for A7 — claim + evidence only.
- Every hash and path is measured by YOU (the Lead) before dispatch, never
  invented.
- Register the task first (orchestrator_register_task), then
  orchestrator_mark_dispatched with the invocation id, then dispatch.
- For quant-explorer add: "your runtime does NOT inject AGENTS.md; this packet
  is your boundary" (built-in Explore exception).
