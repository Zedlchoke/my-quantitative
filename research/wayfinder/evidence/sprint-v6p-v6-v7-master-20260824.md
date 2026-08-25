# Sprint V6P → V6 → V7 Master Evidence Report — 2026-08-25

```text
V6P_VERDICT                   = V6P_PASS_V6_AUTHORIZED (20/20 gates; A7 postfreeze audit PASS, 0 unresolved HIGH/CRIT)
V6_PIPELINE_VERDICT           = VALID (FG0/FG1/hash/full-surface-repro/matrix COMPLETE/append-only true)
V6_FAMILY_VERDICT             = V6P_PASS_V6_CANDIDATE_FAIL
V6_BEST_CANDIDATE_OR_NONE     = NONE
V7_AUTHORIZATION_VERDICT      = NOT_AUTHORIZED (A04 wiring-integrity + A08 attestation + A10 <180min)
V7_PIPELINE_VERDICT           = NOT_RUN
V7_FAMILY_VERDICT             = NOT_RUN (spec remains frozen for a future sprint)
V7_BEST_CANDIDATE_OR_NONE     = NONE
CROSS_FAMILY_LOCKED_CANDIDATE = NONE
NEW_SCORED_TRIALS_USED        = 4 / 8 (all V6; zero V7)
GLOBAL_LEDGER_COUNT           = see experiments.jsonl tail (append-only verified true)
S1_STATUS                     = NOT_STARTED
LIVE_MONEY_STATUS             = UNCHANGED_DISABLED
FINAL_HEAD                    = fbd2e9d (plus uncommitted declared-exempt provenance pair + control journals committed at shutdown)
ACTIVE_OWNED_WORKERS          = none after shutdown (heartbeat sampler PID 22074 terminated by exact pid)
UNRESOLVED_FINDINGS           = 0 HIGH/CRITICAL; residual MEDIUMs recorded in audits (F-1 corrected my 7D MDD claim)
NEXT_SAFE_ACTION              = future sprint: wire divergence dispatcher on a fresh pre-registered basis and re-evaluate V7 with full budget
```

## What this sprint proved

1. **V6P repair held up adversarially.** All fifteen N-findings addressed: continuous-capital WFA (fold carry exact, GOLDEN matches hand-computed −174.89776), RISK_MODE_V1 active every bar (75,731-row census, gross≤1.00/net≤0.10), complete funding/cost/terminal/exposure/accounting artifact set, measured XG1 (no scored boolean fallback), unconditional family-aware stresses (13 variants × real runs), external-reader hash verification CLEAN, matrix reconciliation v3 COMPLETE, full-surface reproductions all-match, independent A7 audit PASS.
2. **Worktree topology corrected by owner order**: shared-checkout deviation REVOKED_BY_OWNER; six isolated role worktrees at one bootstrap; gate chain v1(7/8)→v3(8/8) preserved append-only with explicit correction events.
3. **V6 family ran honestly within its frozen budget** (exactly four scored launches): 1D mechanism-fail (−5,680), 3D edge-too-weak (PF 1.0117), 7D best (+20,581, PF 1.157) but **top-fold concentration 51.66% > 50%** hard-fails FG3 — A7 corrected my earlier misattribution to MDD (actual 8.84%, passes); reverse control lost as expected (−20,103). No eligible candidate; nothing locked.
4. **V7 blocked for two independent, honest reasons**: implementing the dispatcher only after seeing V6 results would breach pre-registration blindness (A04), and the frozen time budget fell below the 180-minute floor (A10). The divergence spec stays hashed and untouched.

## Failure taxonomy (learning loop)

data/PIT: none outstanding · execution: none · accounting: none · risk/concentration: 7D top-fold >50% · edge strength: 3D PF<1.10 · mechanism: 1D negative-carry regime mismatch · multiple-testing: DSR not estimable at n=3-fold series (honest nulls).

## Exact next action for the owner

Open a future sprint with: (a) wire `funding_price_divergence` dispatcher branch BEFORE any results exist (restores blindness), (b) freeze a fresh attestation, (c) run V7's four scored trials with the full remaining budget of 4. Do not reuse or relabel anything from V6.
