# BLOCKER — registry typed-field sync for TERMINAL scored cycles (T1, 2026-10-05)

## Measured drift (from bytes, both cycles)
CYCLE_REGISTRY.json rows for NBA-WINPROB-SCORED-V1 / NFL-WINPROB-SCORED-V1,
after the 2026-10-05 scored closeout:

| Field | Registry value (before T1) | Authority truth | Source of truth |
|---|---|---|---|
| lifecycle | ACTIVE_LIGHT | TERMINAL | phase text + terminal artifacts — FIXED via CAS `cycle update --lifecycle TERMINAL` (journal event recorded) |
| go_phrase_state | REGISTERED_NOT_CONSUMED | consumed at own gate 2026-10-05T00:26:44Z then extinguished at close (P-8) | GO_RECORDED.json + commit timeline — FIXED automatically by the transition writer's P-8 terminal-GO-death invariant (now "DEAD (consumed or extinguished ...)") |
| budget.used | 0 | 9 | TRIAL_LEDGER.jsonl (9 COMPUTED PRIMARY each) — P-9: ledger is the denominator authority; registry field UNSYNCED |
| s0 | OPEN | OPEN (convention for scored cycles in this registry) | NOT drift by convention; still no CLI path to assert it |

This is CONTROL-STATE-DRIFT class (§3.1: registry typed fields and phase text disagree;
§32 two-half close checklist item "budget_used đúng (qua researchctl/canonical save, CAS)"
cannot be completed with the current CLI). It is NOT cosmetic and the ledger must NOT be
edited to legitimize the registry — the ledger is the authority, the registry lags.

## Why the remaining fields cannot be fixed through the sanctioned CLI today
`researchctl cycle update` exposes only: --head --lifecycle --phase --workers
--active-heavy --reason. `governance.cycle_registry.update_cycle()` likewise accepts only
head/lifecycle/phase/workers/active_heavy. There is NO path (CLI or library function) for
budget_used or s0. Precedent: BTC-COMBO6-SCORED-V1 recorded the same limitation ("registry
budget_used=0 stale by tooling limit, disclosed ...; TRIAL_LEDGER carries truth per P-9").

## Proposal (tested, NOT applied to the live registry)
`closeout_fields_proposal.py` adds `update_closeout_fields()` — a governance-library writer
(same atomic CAS + append-only journal as researchctl) that updates ONLY budget.used and/or
s0 with validation (0 <= used <= max; s0 in {OPEN, CLOSED}); fails closed on CAS mismatch.
`tests/test_closeout_fields_proposal.py` proves on a COPY of the live registry: fields
update; journal event appended; invalid values refused; no other fields touched; CAS
mismatch refused. Independent verification of these tests: lane D.

## Owner decision required (fail-closed default: fields stay stale, disclosed)
Option 1 (recommended): accept the proposal as a researchctl CLI flag (--budget-used/--s0
wired to update_cycle) via one tool commit; then sync both cycles' budget.used=9 (s0 stays
OPEN by convention) through the CLI.
Option 2: authorize a one-shot run of the proposal script against the live registry
(governance.save path — sanctioned library, CAS + journal; still outside researchctl).
Option 3: leave stale with this BLOCKER as the standing disclosure.
No option edits any ledger or historical artifact.
