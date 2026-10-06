# CARRIED_STATUS — ESNQ occupied-family inventory as re-measured at R3

- Task **FUTURES-TEN-HYPO-PREP-20261004**, lane **ESNQ**. Generated 2026-10-04 UTC.
- Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-ten-hypo/prep`
  @ HEAD `a4a882658e09092b5b282b666b30a3cfc5ac3418` (== dispatch base_sha; one
  permitted `git rev-parse HEAD`; no other git). Specs are **unchanged** — this
  file re-measures STATUS only, never re-opens or edits any frozen/registered
  construction.
- Baseline of record: `research/control/FUTURES-OVERNIGHT-PREP-20261003/hypo/
  es_nq/ESNQ_HYPOTHESES.md` + `RANKING_INPUT.md` (8 families + PB1 context),
  census `FUTURES-OVERNIGHT-PREP-20261003/synth/CENSUS_FINAL.md`, round-2
  updates `FUTURES-SIX-ADOPT-PREP-20261004/hypo/HYPOTHESES_R2.md` §4.
- Standing rulings restated, never reopened: `NO_GO_REGISTER / NO_GO_SCORE /
  NO_GO_ORDER`; **ES cap 24 identities FROZEN, headroom 0 → any new ES family
  is born BLOCKED_TRIAL_BUDGET (D4 open)**; schedulability flag for every ES
  row = BLOCKED_TRIAL_BUDGET; **NQ: only the cache_v3 chain is consumable
  (canonical CANDIDATE pending D9 ratification; pre-v3 caches DEPRECATED)**;
  fees MODELED / `VERIFIED_VS_ACCOUNT=NOT_RUN` / UNDER REVIEW until
  owner-authorized fee A7 (A7 NOT_RUN; D2 open); BBO NOT_RUN everywhere
  (conservative fill law); **D1-D12 all open — no lane self-ratifies**.

## Status table

| family | class | current status | blockers (unchanged unless noted) |
|---|---|---|---|
| **PB1 OVN pair (M-A/M-B)** | parent, ES | REGISTERED scope, A-r4 **24 identities FROZEN, headroom 0**; NO_GO stands; SPEC_PB1_ES r3 untouched | fees-account D2; calendar D3 (2026 Globex holiday session times NOT_OBTAINED ⇒ 2026 dubious days excluded fail-closed); prelaunch A7; registration freeze. [Baseline ESNQ §0.5, CENSUS_FINAL §1 row 1, SPEC r3] |
| **ES-F1 FOMC-RES** | T1, ES | specified, ranked 11 (program rubric), **BLOCKED_TRIAL_BUDGET** (minimal 11 vs headroom 0) | D4 (cap) is the binding wall; executable at 0 identities: F1-K6 anatomy pre-gate. Anatomy/kill-set unchanged (91 timed events, multi-era buckets). [ESNQ RI §2-§3] |
| **ES-F2 MACRO-0730** | T1, ES | specified, ranked 11, **BLOCKED_TRIAL_BUDGET** (minimal 11) | D4; 0-cost legs: F2-K6 per-era spike anatomy; canceled-day falsifier subset (2025 vintage) descriptive-only. BLS PIT calendar + vintage law PASS (unchanged). [ESNQ RI §2-§3] |
| **ES-F3 COT-CROWD** | T1+T3 gated, ES | specified, ranked 10, **BLOCKED_TRIAL_BUDGET** (minimal 7) | D4; stage-1 session-granularity vol leg (Q1∪Q5 vs Q3, strict-past quintiles) executable at **0 identities** — the round's only wholly-uncapped ES leg. TFF/disaggregated NOT_RUN (100% null) stands. [ESNQ RI §2-§3] |
| **ES-F4 RUN-REV** | T4, ES | specified, ranked 11, **BLOCKED_TRIAL_BUDGET** (minimal 7) | D4; F4-K6 intraday-placement gate 0-cost. acf1/VR 7-era anatomy unchanged. [ESNQ RI §2-§3] |
| **NQ-F1 FOMC-ERA** | T1, NQ | specified, ranked 11, **CTG** (no NQ cap defined) | fee A7 (D2) before any cost-bearing cell; 2026 Globex times NOT_OBTAINED + early closes 2011/2021-25 NOT_TRANSCRIBED (exclude fail-closed); chain = cache_v3 only (D9); K6 anatomy gate. [ESNQ RI; CYCLE_LAUNCH §1-§3] |
| **NQ-F2 MACRO-0730-NQ** | T1, NQ | specified, ranked 11, **CTG** | same NQ gates; scoring era gated to 2023-26 on committed anatomy (K6); thin-power pre-registered (~160 event days). [ESNQ RI §2-§3] |
| **NQ-F3 RUN-REV-NQ** | T4, NQ | specified, ranked 10, **CTG** — **STATUS UPDATE (R2 §4-2)**: the hard precondition "full-era rebuild on the alias-recovered series" is now **executable** — cache_v3 exists and is digest-verified (66 rolls; crash roll 2020-03-19 NQH0→NQM0; cg variant byte-identical ⇒ 0 cease-guard violations post-repair). NOT claimed done: a1/a2 aggregate tables beyond the chain remain hole-era until re-run | cost A7 (D2); calendar 2026; D9 ratification; K3 concentration now honestly measurable on real 2020 data (recovered −34.12% DD window); trial-ceiling arithmetic before any packet |
| **NQ-F4 ROLLWK** | T5, NQ | specified, ranked 9, **CTG** — **STATUS UPDATE (R2 §4-3)**: Role-A audit discharge path exists via the RMM Role-A construction ledger (shared construction: per-roll mode classification + switch-day jump audit on the v3 chain INCLUDING the crash roll; cite `FUTURES-SIX-ADOPT-PREP-20261004/hypo/HYPOTHESES_R2.md` §4 item 3 and D-1 CEASE-SYNC diag) | Role B still gated on the NOT_RUN roll-week × session-type interaction (K6) + an owner DC §1.3 boundary ruling (declared, not self-ratified); Role A standing audit is law regardless of ranking |

## Inheritance notes (what R3 changes — and does not)

1. **Nothing above is re-specified, re-scored in substance, or unblocked by
   this lane.** The two NQ status updates above are transcriptions of R2 §4
   (adoption-round proposals), not new rulings; both remain CTG and both
   still require the owner rulings they name.
2. **R3 adds one NEW family (ESNQ-F5 `EXPWITCH`, legs ES+NQ)** — see
   `HYPOTHESES_ESNQ_R3.md`. The ES leg is **born BLOCKED_TRIAL_BUDGET**
   (standing law); it consumes 0 identities in PREP and creates no budget
   surface until an owner amendment. The NQ leg is CTG contingency.
3. Occupied-class closure for R3 candidates: the R2-era vetoes (NQ volume/
   participation-shock = dead `XSECT-VOLSHK-S15` class; NQ OVN-tail third
   overlap = PB1 territory + §0.5-1; NQ roll-microstructure duplicate =
   NQ-F4 class) are **re-applied unchanged**; R3's new candidates were
   screened against all three plus the full 173-row `FAMILY_FAILURES.jsonl`
   inventory (all rows re-scanned this lane).

— End CARRIED_STATUS.md. Status re-measurement only; 0 PnL; 0 registrations;
missing evidence is NOT_RUN, never PASS.
