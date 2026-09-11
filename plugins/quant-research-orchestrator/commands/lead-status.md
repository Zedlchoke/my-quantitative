---
description: Reconcile and report current orchestration state without changing anything
---

Report the current ZCODE-ORCHESTRATION-V3 state. READ-ONLY:

1. Measure: `git -C <repo> rev-parse HEAD`, branch, `git status --porcelain=v1`,
   `git worktree list`.
2. Read plans/CYCLE_REGISTRY.json; run
   `.venv/bin/python research/researchctl.py cycle doctor --json` and
   `.venv/bin/python research/researchctl.py locks inspect`.
3. Call `orchestrator_waiting_summary` and `orchestrator_terminal_check` on the
   orchestrator MCP. Tail the last 20 rows of
   .runtime/orchestrator_v3/events.jsonl.
4. Report a table: task_id / role / status / attempt / heartbeat age /
   handoff state; ready queue; blockers; registry phase; heavy lock verdict.
5. Label every inconsistency CONTROL_STATE_DRIFT with evidence — do not
   repair, do not guess. Missing runtime state is CONTROL_STATE_DRIFT, never
   an empty queue.
