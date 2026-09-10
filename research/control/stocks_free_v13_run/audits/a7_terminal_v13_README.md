# A7 TERMINAL AUDIT — STOCKS-FREE-V13 (independent, fresh-context)

Audited commit: `43c1fcc` (cycle branch head; audit lane: `.worktrees/stocks-free-v13/r-a7-terminal`, branch `orca/v13-r-a7-terminal2`)
Auditor: A7_TERMINAL_STOCKS_V13 — audit ONLY, no repairs; every number recomputed from bytes; reproduction re-executed END-TO-END in the auditor's OWN twin; negative paths exercised LIVE.

## VERDICT: `CONFIRM_STOCKS_FREE_V13_REJECT_MECHANICAL`

0 unresolved HIGH/CRITICAL. All seven audit items PASS. The terminal claim is substantively
confirmed: the sole selected family **SFV13-A6-P1** (dividend-policy transition, EODHD
dividends) died mechanically at Stage-A rule-order gate 3, with 0 survivors, budget 3/6
(3 slots dead forever), S1 sealed.

### Label adjudication (binding for the close)

`SFV13_A6_P1_REJECT_MECHANICAL` is a legitimate **family-level** verdict label but is NOT
among the plan's five allowed **cycle-level** outcomes (PLAN_stocks_v13.md L122–128). The
close-sync must record **`STOCKS_FREE_V13_REJECT_ALL`** with the mechanical qualifier as
prose ("rule-order 3 first-fail; drop-one-fold and SPY-excess also fail; PF 1.4449
sham-loses informative coherence") — precedent: the crypto V13 ledger row records
`V13_REJECT_ALL ... mechanical reject`. (MEDIUM finding F-A7T-1, verdict-neutral.)

## What was verified (all PASS)

1. **Full chain** — all claimed shas exist with claimed content; `git log --ancestry-path
   fce8312..43c1fcc` = 55 commits, single lineage. P0a census recomputed from bytes:
   1562+398 = 1960 entities, 17072+10382 = 27454 pairs, dead-share 0.6218, verdict
   FUNDABLE; P0b `MACRO_REPIN_ALL_MATCH`; P1 kernel 121/121 byte-exact + regression 41
   passed; D2 determinism x2 same-sha with five measured kills re-read (A4-P1 0.232,
   A4-P2 0.2402, A5-P1 DGS10 rho 0.9059, A5-P2 0.2667, A6-P2 fail-closed 0/15) and
   A6-P1 ELIGIBLE (novelty 0.0752); erratum E1 legitimate (pre-selection, pre-PnL, killed
   nothing); two owner-GO events with the first extinguished unconsumed by INC-V13-14 and
   the second CONSUMED_AT_GATE_V2 binding; INC-V13-15 rerun under the standing GO.
2. **Scored recompute** — 158/158 checks to full persisted precision across 3 arms x 2
   variants: anchor expectancy 0.002142933176 / PF 1.444881 / folds 1-positives
   (F1 +0.0932 PF 4.669, F2 −0.0137 PF 0.8225, F3 −0.0217 PF 0.2101); stress +0.00018 /
   PF 1.030974; sham −0.002930 / PF 0.431839 / 0-3; neighbour +0.000160 / PF 1.033411.
   Rule-order adjudication correct (rule 3 first-fail; rules 1–2 pass). Drop-one symbol
   +0.000595 (worst CIK0000073887) PASS; drop-one fold −0.001310 FAIL; SPY-excess 0/3
   folds FAIL, sum −0.261132 over exactly 20 active periods (5/20 positive) — all exact.
   Control-reproduction ratio c/a = −1.36712324 exact, opposite-sign no-kill correct.
   Self-subsumption 0.02567919 corroborated by the D2 identifiability measurement AND by
   the byte-identical own-twin re-run.
3. **Reproduction** — auditor's OWN twin at `620c864`: staging copies sha-verified
   2168/2168 (div) + 2168/2168 (splits) against substrate_manifest.json; scored re-run
   with IDENTICAL argv + env exited 0; **12/12 payload files BYTE-IDENTICAL**,
   **family_verdicts.json BYTE-IDENTICAL** (4e291228…), execution_ledger differs only in
   the 2 declared-volatile path leaves. **ALL_MATCH independently confirmed.**
4. **Data authority** — three NAMED pins re-hashed MATCH at the machine paths (panel
   6759… 1.4G, v10_timing b147… 2.3G, v10_revision 7110… 459M). V9 price cache
   unrecoverable INDEPENDENTLY verified: `stocks-free-v9_staging.tar.gz` has 0
   staging_prices entries (the v8 archive's 424 files are the pre-death 410-filer era).
   Coverage gate truthful: **FAIL_COVERAGE 2140/2178, 0 missing, 38 named thin/invalid**,
   ratio 0.9826; erratum F-2 recorded in selection_freeze.errata. P-3 single substrate:
   D2 vetoes and books consume the same re-staged price series.
5. **Ledger/denominators** — no V13 row on main (pre-append, no double-append); stocks
   39/39; program 236/239 on main (V13 intake snapshot was 233/236; the intervening
   FX-V8 close moved it — see F-A7T-3); S1 SEALED; budget 3/6, 3 slots dead; DSR
   non-exercisable acceptable at REJECT; per-period series persisted (P-11).
6. **Incidents INC-V13-1..16** — 16/16 with repair + impact disclosure (12 named in
   event_log.jsonl — INC-V13-6 folded into the INC-5 note; 11/12/13 in 446dd72; 14 in
   f77e61f + delta-affirm 0aca223). No unexplained incident, zero scientific impact.
7. **Negative paths (live)** — without env: exit 2 two-key refusal, pre-lock; with env +
   foreign lock holder: exit 3 NOT_RUN_RESOURCE_CONFLICT, zero tree mutation.

## Findings

| id | severity | summary |
|---|---|---|
| F-A7T-1 | MEDIUM | record the close outcome as `STOCKS_FREE_V13_REJECT_ALL` + mechanical qualifier (REJECT_MECHANICAL is not an allowed cycle-level name); verdict-neutral |
| F-A7T-2 | LOW | terminal verdict prose: neighbour PF "1.0331" should read 1.033411; conclusion unchanged |
| F-A7T-3 | INFO | brief's "233/236 pre-append" is the intake snapshot; main reads 236/239 post-FX-V8; V13 close appends to 239/242 |
| F-A7T-4 | NOTE | frozen data_authority prose keeps the false coverage claim, corrected via F-2 erratum (append-only, correct handling) |

## Handoff

CONFIRM terminal. Close directive: `STOCKS_FREE_V13_REJECT_ALL` (mechanical qualifier in
prose); stocks 39→42, program →239/242; budget 3/6 with 3 slots dead forever; no
survivor; S1 SEALED; per-period series persisted for future DSR trials.
