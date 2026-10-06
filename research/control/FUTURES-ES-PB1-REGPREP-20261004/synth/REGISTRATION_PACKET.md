# REGISTRATION_PACKET — FUTURES-ES-PB1-V1 (ES, PB1-only, 24 identities)

- Round: **FUTURES-ES-PB1-REGPREP-20261004** (controller, over lane
  FREEZE-AUDIT outputs). Status: **PACKED FOR OWNER REGISTRATION. NOT
  REGISTERED. This packet registers nothing and authorizes nothing.**
- Cost freeze: **CLOSED — D3 = Variant A** signed by owner
  (`auth/D3_RECORDED.json`, quote verbatim "tôi chọn 2.25$"). Fee layer:
  MODELED COST, basis frozen A, documentation-A7 clean
  (AUTHORIZED_WITH_FINDINGS, 0 HIGH/CRITICAL), **VERIFIED_VS_ACCOUNT =
  NOT_RUN** (unchanged). e.1-e.3 remain OPEN — e.1 FX-scoped, e.2 geography-scoped (unused under Variant A), e.3 NYMEX-scoped —
  **non-blocking for this cycle** (A7_EXECUTION_PACKET §4 quoted in
  freeze/REGISTRATION_READINESS.md).
- CYCLE-1 status transitions here: ~~BLOCKED_COST_FREEZE~~ →
  **GATED_ON_REGISTRATION** (the D3 blocker is discharged; prior-round
  docs stand as history, superseded by this packet by reference).

## 1. What the owner registers (one action, at ROOT, owner-run or
explicitly owner-delegated root session — the CURRENT authority text
does NOT include registration; this packet exists so the action is
single-step when the owner chooses)

| Field | Value |
|---|---|
| cycle_id (proposed) | `FUTURES-ES-PB1-V1` |
| scope | ES only; PB1 OVN pair (M-A/M-B) parent family ONLY |
| identities | **24** = P-A 8 + P-B 8 + FOMC 4 + C1-C4 4 (verbatim transcription: `freeze/identity_table_24.json`; composition reconciled vs census + Option ES-0, zero discrepancy) |
| chain of record | ES baseline chain per SPEC_PB1_ES §1 (68/68 expiries re-derived; 66/66 data-side; panel pin `7ae6de2d…` byte-stable) |
| cost contract | Variant A frozen: fees **2.25/side**; all-in **21.00 / 33.50 / 46.00**; RT 42.00/67.00/92.00; window 2014-10-01→2017-12-31 = 20.99/33.49/45.99; stress ladder ×1.0/×1.5/×2.0; BBO NOT_RUN conservative fill law |
| PIT/exclude set | 7 law components pinned (`freeze/pit_exclude_set.json`): FOMC 132-day exclude; BLS vintage + D5 pin; holiday fail-closed (ES 2026 CAL-CLOSE); RTH-core <60% coverage; roll/expiry laws; 4-fold + warmup 252 |
| freeze set | **34 sha256 pins, AUTHORITATIVE manifest `freeze/freeze_pins_v2.json`** (supersession: `freeze/PIN_SUPERSESSION.md`; v1 = lane-time history; 1 disclosed delta: D3_RECORDED wording-only); SPEC_PB1_ES pin `445f7499…b7073` MATCH |
| budget | 24 identities (== frozen cap; no D4 amendment needed) |
| plan pointer | `research/control/FUTURES-ES-V1-PACKET/PLAN_futures_es_v1.md` (with §6 GO-string disposition §5 below) |
| worktree/branch at registration | controller's next integration worktree, to be created FROM the registered freeze by the owner's registration session (not pre-created here) |

## 2. Gate sequence after registration (two-key law, CYCLE_LAUNCH_DRAFT §6 verbatim order)

1. **Registration at ROOT** (owner) — freeze set + all §1 pins re-hashed
   into the selection freeze; drift vs this packet ⇒ BLOCKED.
2. **Prelaunch A7 — key 1 of 2** (independent fresh-context audit;
   program = `synth/PRELAUNCH_A7_SPEC.md` in this round): identity
   enumeration vs frozen 24; cost arithmetic vs the Variant-A pinned
   table; PIT/exclude coverage; budget accounting; freeze integrity;
   no-measured-cost language scan. Verdict required: 0 HIGH/CRITICAL
   unresolved.
3. **Exact-arm dry-run** (post-registration by law;
   `synth/DRYRUN_SPEC.md`): single-shot rehearsal, budget counters
   untouched, output quarantined descriptive-only; byte-exact identity
   enumeration + cost recomputation match required.
4. **Typed owner GO — key 2 of 2**, at the registered cycle's own gate:
   see §5 canonical string. Early/paraphrased GO = intent only, dies
   unconsumed. Then: scored under heavy lock + reproduction twin +
   terminal A7 (pre-decided terminal outcomes).

## 3. What this packet does NOT do

No registration, no GO, no scoring, no dry-run, no S1/order/purchase/
push/merge, no registry/ledger writes, no D9/PB2/PB3/D8/caps touched.
NQ + 6E/6B/6J/6A keep their own gates unchanged.

## 4. e-ruling ledger after D3=A

| ruling | state | blocks |
|---|---|---|
| e.4 (= D3) | **CLOSED — Variant A** (owner quote recorded) | nothing further |
| e.1 | OPEN (FX alias corroboration) | FX cost-bearing cells only |
| e.2 | OPEN (account-geography basis) | geography-sensitive modeling only |
| e.3 | OPEN (NYMEX reg epoch) | CL/NG cells only |

## 5. F-A5 disposition — canonical GO string (registered once, exact-match forever)

FREEZE-AUDIT found the historical PLAN §6 prints `GO FUTURES ES V1
SCORED EXECUTION` while this packet's proposal uses cycle id
`FUTURES-ES-PB1-V1`. The GO law is `GO <REGISTERED-CYCLE-ID> SCORED
EXECUTION` — the string is determined by whatever id the owner actually
registers. **Canonical rule (this packet): the GO phrase = the exact
registered cycle id substituted into `GO <REGISTERED-CYCLE-ID> SCORED
EXECUTION`; the PLAN §6 example is a historical illustration, superseded
by reference (append-only; the PLAN file is untouched).** If the owner
prefers the PLAN's spelling, register that id instead — one id, one
string, no aliases.

## 6. Minimal owner action to reach the next gate

> Register `FUTURES-ES-PB1-V1` at ROOT per §1 (or explicitly delegate
> the root registration session). Nothing else is missing on the ES
> path: after registration the prelaunch A7 and dry-run can run, and the
> final gate is the typed GO phrase of §5.

— End REGISTRATION_PACKET. Preparation, not authorization; no signature
of the owner is inferred beyond D3=A as recorded.
