# DECISION_PACKET_INDEX — D2/D3/D4 (FEE-ES lane, round FUTURES-SIX-ADOPT-PREP-20261004, 2026-10-04)

**NO RULING EXISTS AS OF 2026-10-04. NOTHING IN THIS PACKET IS RATIFIED.** Standing defaults hold:
fee A7 **NOT_RUN** · ES cap **24** (headroom 0) · fees **UNDER REVIEW**
(MODELED COST / VERIFIED_VS_ACCOUNT=NOT_RUN). "cho agent làm đi" (PREP) does not ratify any of
D2/D3/D4. Every ruling must be written by the owner; each sheet below follows the template:
context → options → consequence → fail-closed default → exact action authorized → actions
remaining forbidden.

| # | sheet | context (1 line) | options | headline consequence | fail-closed default | exact action authorized by a YES | actions remaining forbidden |
|---|---|---|---|---|---|---|---|
| **D2** | `D2_QUANT_SHEET.md` + `A7_EXECUTION_PACKET.md` | Fee erratum re-audit packeted (21 inputs, all re-hashed 21/21 MATCH in this worktree) but never run; 25-site propagation surface (22 frozen + 3 living); SPEC §5 exit blocked at step 1 of 4 | A: authorize now · B: defer | A unblocks re-derivation of 10 codes × 4 tiers from raw bytes + closure of the 3 stale §5 lines; B keeps every cost gate open (max residual exposure $0.01/side, unbounded time) | NOT_RUN persists; fees UNDER REVIEW | Run the 9-check read-only A7 per the packet at the authorizing round's HEAD; write only its own dir + handoff | Scoring, GO, ledger/registry writes, orders, edits to frozen files, "fixing" §5 inside the A7 |
| **D3** | `D3_QUANT_SHEET.md` (= A7 ruling e.4) | SPEC §5 NFA 0.02 (21.00/33.50/46.00) vs hypo/es_nq offset 0.01 (20.99/33.49/45.99; NQ 23.49-family): $0.01/side, $0.02/RT = 0.0476%/0.0299%/0.0217% of tier RT cost = 0.00038 bp of $260k ES notional; 53 offset-basis value sites (41 all-in + 12 fee) vs 0 NFA sites outside SPEC | A: NFA 0.02 (conservative, no SPEC edit) · B: offset 0.01 (account-realistic, needs dated SPEC annotation) | A annotates 53 sites superseded; B reverses a frozen spec line; either closes A7 check 8 and legalizes cost-gate arithmetic | Divergence stays OPEN; no cost gate may consume either number | One written line naming the canonical reg basis for modeled all-ins (foldable into D2's writing) | Any cost-gate pass/fail adjudication before the ruling; in-place edits of hypo/es_nq or SPEC |
| **D4** | `D4_QUANT_SHEET.md` | ES minimal demand 36 (F1 11 + F2 11 + F3 7 + F4 7) vs frozen cap 24, headroom 0 — all ES families BLOCKED_TRIAL_BUDGET | A: raise to 36 (all four fit exactly) · A′: 28 / 30 / 32 (28 → F1+F2; 29-35 → F1+F2+F4; 30 and 32 identical) · B: keep 24 (none fit) | A = +12 scored IDs = +50% ES ceiling = +2.3% of the program's 513 ledgered scored trials; placebo-budget ruling (CENSUS_PROPOSAL §3) can multiply controls afterward | Cap stays 24; only 0-identity legs run (F3 stage-1 vol leg, K6 pre-gates, X-1..X-5) | One written owner amendment setting the ceiling number + ordering the ceiling re-check | Registration, scheduling, or any scored cell before the written amendment; re-tparam after K2 kills |

Dependencies: D3 can be ruled with or ahead of D2 (the A7's check 8 consumes it). D4 is
independent of D2/D3. None of the three unlocks a scored cell by itself — NO_GO_REGISTER /
NO_GO_SCORE / NO_GO_ORDER, PB2 HOLD, PB3 PARK and the two-key GO law all still apply afterwards.

Evidence base (all read-only, this worktree unless noted): `FUTURES-SIX-READINESS-20261004/es/{es_fee_status,es_trial_census}.json`,
`verify/fee_a7_status.json`, `synth/OWNER_DECISIONS.md`; `FUTURES-OVERNIGHT-PREP-20261003/fees_erratum/**`
(21 inputs sha-pinned), `hypo/es_nq/*`, `hypo/cross/CENSUS_PROPOSAL.md`, `synth/{CENSUS_FINAL,BLOCKER_MATRIX}.md`;
`FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md` + `audit/a7_spec/*`; sibling (read-only):
`FUTURES-P3-QUARANTINE-20261004/{fee_a7_readiness/*, synth/OWNER_DECISIONS.md, synth/FINAL_SAFE_BLOCKER_MATRIX.md}`.

— FEE-ES proposes; the owner decides; the controller commits. End of index.
