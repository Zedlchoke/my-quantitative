---
description: Terminal reconciliation and closeout for the orchestration cycle
---

Close ZCODE-ORCHESTRATION-V3 honestly:

1. `orchestrator_terminal_check` must show all tasks TERMINAL; every open
   blocker resolved or explicitly owner-escalated; workers 0; heavy lock
   FREE_PROVEN (`researchctl locks inspect`).
2. Reconcile committed evidence under
   research/control/ZCODE-ORCHESTRATION-V3/orchestration/:
   dispatch_manifest.json, handoffs/*.json, integration_events.jsonl,
   terminal_reconciliation.json.
3. Verify every gate in the plan matrix (Z3-G0..G10) has a verdict PASS, FAIL
   or NOT_RUN backed by command + exit code + SHA + artifact path. Missing
   evidence stays NOT_RUN — never inferred PASS.
4. Write the terminal report (verdict from the plan's closed list, version
   pins, install instructions, test evidence, canary digests, recovery proof,
   limitations, workers/trees).
5. Update the canonical registry ONLY through researchctl/canonical path
   (lifecycle TERMINAL via the proper transition; this kills any GO state per
   P-8). Commit control-plane files by exact pathspec. No push, no merge to
   main without explicit owner authority.
6. Report the terminal verdict + next owner-authorized path to the owner.
