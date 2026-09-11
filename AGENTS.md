# AGENTS.md — my-quantitative workspace router

Compact router. NOT a manual: read the applicable plan in full before work.

## Mission invariant

Evidence-first quantitative research factory. A profitable number is not a
valid result unless identity, data, costs, trial accounting, gates and
reproduction all reconcile. Missing evidence is `NOT_RUN`, never inferred
`PASS`.

## Authority pointers (read in this order)

1. Latest explicit owner instruction.
2. The applicable plan in `plans/` (highest registered live cycle wins — check
   `plans/CYCLE_REGISTRY.json`, the ONLY writable cycle authority).
3. `CLAUDE.md` (full operating contract) and `HOW_TO_BE_A_LEAD_ENGINEER.md`
   (handbook: authority order, worktree discipline, gates, handoffs).
4. Frozen manifests/ledgers; historical plans are evidence of the past, never
   current truth — always re-measure the checkout.

## Worktree / branch / lock boundaries

- Root checkout = bootstrap/owner space. Lane work happens ONLY in the exact
  worktree + branch named by the cycle registry / dispatch packet.
- Every git command names its repo explicitly (`git -C <absolute path> ...`).
  Verify `pwd` + branch + full HEAD before committing. Stage by pathspec;
  `git add -A` is forbidden.
- One heavy job machine-wide: global lock via
  `.venv/bin/python research/researchctl.py locks inspect`.
  `NOT_RUN_RESOURCE_CONFLICT` if held. Never kill a foreign worker.
- NEVER: push, merge to `main`, history rewrite, S1 access, scoring or typed
  GO without the cycle's own gate + owner, credentials in prompts/logs/git,
  writes to ZCode internal databases.

## Structured handoff (subagents)

End every delegated task by writing the handoff JSON (schema
`zcode_orch_v3_handoff@1`, see the quant-research-orchestrator plugin's
structured-handoff skill) to the exact `handoff_path` in your dispatch packet.
Chat prose is advisory; the artifact is authority. Lanes never merge, rebase,
push, touch ledgers/registries or other lanes.

## Re-measure state (commands)

```bash
.venv/bin/python research/researchctl.py cycle list
.venv/bin/python research/researchctl.py cycle doctor --json
.venv/bin/python research/researchctl.py locks inspect
# orchestrator MCP (plugin): orchestrator_waiting_summary / terminal_check
tail -20 .runtime/orchestrator_v3/events.jsonl   # if a cycle uses orchestration v3
```

Orchestration cycle: `ZCODE-ORCHESTRATION-V3` — plan
`plans/PLAN_zcode_orchestration_v3.md`, evidence under
`research/control/ZCODE-ORCHESTRATION-V3/orchestration/`.
