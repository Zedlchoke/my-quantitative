# Stale store-row disclosure — 2026-09-17 (Lead A1, STRATEGY-SEARCH program session)

`.runtime/orchestrator_v3/tasks.json` (gitignored runtime; NOT authority)
contains 9 non-terminal rows that are dead coordination state from TERMINAL
cycles:

```text
fibv1-a3, fibv1-a4, fibv1-a5, fibv1-a7-plan-audit   (FOREX-INTRA-BIDASK-V1,
  TERMINAL BLOCKED_TRANSPORT 558b366c — close recorded "waves A3/A4/A5 +
  D2 MOOT undispatched")
fxf-a3, fxf-a4, fxf-a5, fxf-a6                       (FX-FUTURES-FRONTIER-V1,
  TERMINAL BLOCKED_TRANSPORT 7decfce3 — close recorded "waves a3-a6 + D2
  MOOT undispatched")
deu-a7-cycle-audit                                    (DATA-EDGE-UNLOCK-V1,
  TERMINAL — already disclosed as INC-DEU-1 stale store row at its close)
fsearch-r-2                                           (FOREX-SEARCH-V1,
  TERMINAL REJECT_ALL 2a6f59c6 — R reproduction WAIVED by explicit owner
  instruction 2026-09-18; lane was DISPATCHED and polling for the heavy
  lock when stopped, held nothing, disturbed no worker; DISPATCHED ->
  TECHABORT refused by the store API same as the REGISTERED rows above)
```

Facts measured this session:

- Authority is `plans/CYCLE_REGISTRY.json`; all three owning cycles are
  TERMINAL there. The store is the single-cycle ZCODE-ORCHESTRATION-V3
  label and its historical rows are recorded-not-normalized (INC-DEU-1
  precedent).
- `orchestrator_record_blocker` refuses REGISTERED/READY -> terminal
  ("no backward moves; re-dispatch = new task"); these rows were never
  dispatched, so no legal store exit exists. Fabricated dispatch
  lifecycles were considered and REJECTED as worse than the staleness.
- `/lead-resume` reconstructs from the registry + git state, never from
  these rows. The Stop hook's in-flight nag on these rows stands down
  after 3 continuations by design.

If the owner ever wants the store normalized, the precedented route is a
deliberate maintenance pass in a fresh Lead session walking each row
READY -> DISPATCHED -> HANDOFF_READY -> VALIDATING -> REJECTED with a
truthful "stale-row reconciliation, no work performed" handoff
(negative-control class, canary-p8-bad-handoff lineage) — never silent
deletion, never history rewrite.

Session close-state: STRATEGY-SEARCH program registered (STOCKS-SEARCH-V1
1b688960, FOREX-SEARCH-V1 8a3eb27a, both PLANNED_NOT_STARTED 0/3, S1
SEALED, GO phrases REGISTERED_NOT_CONSUMED); all 8 of this session's
audit tasks INTEGRATED with commits; heavy lock FREE_PROVEN; tree clean
except `.zcode/` tooling.
