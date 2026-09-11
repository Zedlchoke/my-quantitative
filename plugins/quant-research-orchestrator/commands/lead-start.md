---
description: Start the ZCODE-ORCHESTRATION-V3 Lead controller loop for this session
---

You are the primary Lead/A1 controller for ZCODE-ORCHESTRATION-V3
(plans/PLAN_zcode_orchestration_v3.md — read it in full first if not already in
context). Start the controller loop:

1. Reconcile repository truth: `pwd`, branch, full HEAD, `git status
   --porcelain=v1`, worktree list. Read plans/CYCLE_REGISTRY.json (canonical).
2. Call the `orchestrator` MCP `orchestrator_intake`, then
   `orchestrator_waiting_summary` and `orchestrator_terminal_check`.
3. Verify: heavy lock state via
   `.venv/bin/python research/researchctl.py locks inspect`; zero foreign
   workers; no unexplained dirty tree (classify any per handbook §4.4).
4. Read research/control/ZCODE-ORCHESTRATION-V3/orchestration/ phase reports
   and .runtime/orchestrator_v3/events.jsonl tail (last 20 events).
5. Print a first report: measured time, cwd/branch/HEAD, dirty state, workers,
   registry phase, gates observed, blockers, GO/NO_GO for the next step.
6. Dispatch every READY task (orchestrator_list_ready) within the slot cap
   (8GB host: Lead + max 3 light lanes; one heavy at a time machine-wide),
   using the dispatch-packet skill for each packet. Foreground for fast
   reads, background for the rest.

Boundaries: no S1, no scoring, no GO, no push, no merge to main, no internal
ZCode databases, no nested subagents, no killing foreign workers. Owner is
notified only at true authority blockers or the terminal verdict.
