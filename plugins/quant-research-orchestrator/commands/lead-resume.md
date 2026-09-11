---
description: Resume the controller loop from durable artifacts after compaction or restart
---

You are the primary Lead/A1 controller resuming ZCODE-ORCHESTRATION-V3 after a
session compaction or restart. Chat history is NOT authority; artifacts are.

1. Re-read plans/PLAN_zcode_orchestration_v3.md sections 3, 8 and 13 plus the
   latest phase reports under
   research/control/ZCODE-ORCHESTRATION-V3/orchestration/.
2. Measure git truth (HEAD, branch, dirty, worktrees) and the heavy lock
   (`researchctl locks inspect`). Reconcile against
   .runtime/orchestrator_v3/tasks.json + events.jsonl — never against
   remembered chat.
3. Call `orchestrator_waiting_summary`. For each in-flight task:
   - DISPATCHED/RUNNING with a dead/absent heartbeat -> re-dispatch as a NEW
     attempt only within max_attempts, else TECHABORT (honest state).
   - HANDOFF_READY -> `orchestrator_validate_handoff`, then validate git +
     test evidence yourself (the artifact is authority, prose is not).
   - VALIDATING -> finish validation; integrate ONE commit at a time with
     targeted gates, then `orchestrator_mark_integrated` (zero double
     integration: check the commit is not already an ancestor of HEAD).
4. Never re-run an already-integrated task. Never integrate two tasks in one
   commit. Never trust a handoff whose dispatch_sha != actual_start_sha.
5. Continue the controller-loop skill from step 4 with the reconciled queue.
