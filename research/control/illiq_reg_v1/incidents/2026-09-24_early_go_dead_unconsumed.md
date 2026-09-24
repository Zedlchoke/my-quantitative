# INCIDENT — RETRACTED & CORRECTED: the GO was at its gate, not early

- cycle: ILLIQ-REG-V1 · branch orca/illiq-reg-v1-integration
- original record (this file, first version): classified the owner's phrase
  `GO ILLIQ REG V1 SCORED EXECUTION` as typed BEFORE A7 prelaunch and
  therefore dead unconsumed.

## What was wrong

The Lead session that wrote the first version was operating on STALE CONTEXT:
it had last measured the worktree at its own bootstrap commit `58b93de3` and
did not re-measure before classifying. In fact, between bootstrap and the
owner's phrase, the implementation lane and an independent A7 had completed
gates §10.3–§10.5 and committed them on this branch:

- `b9ae22df` — full gate-series build run under the heavy lock
  (`gate_series.json`, sha256 `e09187f9…`, determinism: two locked runs
  byte-identical) + sanitized dry-run PASS (non-vacuous, no PnL fields);
- `eb86951e` — implementation handoff;
- `research/control/illiq_reg_v1/a7_prelaunch/a7_prelaunch_illiq_reg_v1.json`
  — A7 prelaunch verdict **AUTHORIZED**, 0 blocking / 6 non-blocking,
  audit_utc 2026-09-24T05:09:04Z, head audited `eb86951e`, written BEFORE the
  owner's phrase reached this thread.

## Corrected classification

The owner's phrase arrived AFTER the A7 prelaunch artifact existed and AFTER
the A7's own "gate to the next step" instruction ("STOP per plan §10.6/§12:
the owner must type the exact fresh phrase…"). The phrase matches the
registered GO phrase verbatim. **The two keys are therefore complete and the
GO is validly consumable at its own gate (plan §10.6/§12).** It was NOT
early; no phrase died.

## Lessons recorded

1. Re-measure the checkout before classifying any state (handbook §4.1) —
   the first version of this file violated that and was itself an incident.
2. Untracked new artifacts in the cycle namespace are a signal of lane
   activity (P-17), not noise: measure, read, then conclude.
- outcome-data exposure: none throughout (no cell had run at either time).
- prevention: this correction is committed on the branch next to the GO
  consumption record so the audit trail shows both the error and its repair.
