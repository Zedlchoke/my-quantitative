# A7 PRELAUNCH AUDIT — STOCKS-FREE-V13 (independent, fresh-context)

Audited commit: `5b0f48e` (audit lane: detached worktree `.worktrees/stocks-free-v13/q-a7-prelaunch`)
Auditor: A7_STOCKS_V13_PRELAUNCH — audit ONLY; every number recomputed from bytes; negative paths exercised LIVE.

## VERDICT: `STOCKS_V13_S0_LAUNCH_AUTHORIZED`

0 unresolved HIGH/CRITICAL. 2 MEDIUM + 2 LOW + 1 NOTE, none blocking the S0 scored-execution
authorization of the sole selected family **SFV13-A6-P1** (dividend-policy transition state).
Per P-8, authorization only becomes effective when the OWNER types the FRESH phrase
`GO STOCKS V13 SCORED EXECUTION` AND sets `STOCKS_V13_LAUNCH_AUTHORIZED=1` (both verified
live to be strictly required — three refusal probes exited 2 with the lock untouched).

## What was verified (all PASS)

1. **Selection/freeze chain** — rubric frozen at `c7995e1` (2026-09-08T14:42:39Z), ancestry
   vs all three D1 proposal commits proven with `git merge-base --is-ancestor` (5/5 exit 0).
   `selection_freeze.json`: 1 family, 3 cells, budget 3/6 (3 dead forever). Proposal
   sha256 **re-hashed from bytes: `c5958b96...ef7d` MATCH**. D2 audit sha MATCH.
2. **D2 + erratum E1** — determinism byte-identical x2 (same sha). Five INELIGIBLE verdicts
   re-read from bytes and matching the freeze (A4-P1 0.232 / A4-P2 0.2402 vs vol_level;
   A5-P1 DGS10 rho 0.9059 unidentifiable; A5-P2 0.2667; A6-P2 fail-closed 0/15). A6-P1
   PASS: novelty 0.0752, identifiability 0.0257, 22818 pairs / 897 entities / 27 dates.
   **E1 adjudicated LEGITIMATE**: A1 authority, internally-evidenced scrivener's error,
   pre-selection AND pre-PnL, disclosed everywhere, owner override recorded — and it killed
   nothing (A4 still died on novelty under the corrected observable).
3. **Runner spec fidelity** (`research/assets/stocks/v13_a6p1_family_runner.py`) —
   no lookahead (all inputs strictly `< D`, fill first session strictly `> D`, return from
   the fill close); costs charged exactly once per side (stress x2 on both sides);
   fold-boundary force-flat with cost (fills beyond fold end void the period); dead-leg
   exit-at-last-close with no post-series price; SPY-excess scaled EX ANTE by frozen gross
   1.0 with exact-bar joins; sham determinism (sha256 hex-sort, no RNG, multiset audit
   true); gate arithmetic per Q1–Q7 including the BINDING MDD 0.15 row (0.20 carried as
   secondary), expectancy rule-order first, PF +inf documented, exact drop-one from legs;
   P-11: 27/27 periods per arm incl. abstain rows.
4. **Fixtures** — `/Users/hoangminhlong/.venv/bin/python -m pytest
   tests/assets/stocks/test_v13_a6p1_runner.py -q` → **20 passed, exit 0**. The suite pins
   the spec (no-lookahead mutation, cost-once, dead-leg, fold force-flat, sham determinism
   + independent hash re-derivation, gates/margins hand-computed, two-key refusal,
   LockBusy exit 3 single-attempt, leak scan, dry-run/scored structure equality).
5. **Data** — full substrate manifest re-hashed: `78c4fb1a...` MATCH. Form-4 XMLs
   345,150 (seeded sample 5/5 MATCH). eodhd_div 2168 (5/5 MATCH). Prices: FULL
   `verify_price_manifest()` → **2153/2153 MATCH, 0 missing**. INC-V13-11 re-stage
   disclosure is prominent (event log + freeze + script docstring; A1-adjudicated
   unpinned-input re-stage, P-3 single substrate).
6. **Dry-run** — sanitized (0 non-null PnL-class fields anywhere; gates WITHHELD),
   record IDs pairwise distinct (recomputed + fail-closed writer), 27/27 periods per arm
   x 6 files, counters reproduced from artifacts (47,444 scheduled exits / 330 dead-legs /
   2,474 voids), ledger input digests match the committed bytes exactly. The P-11 fix diff
   (`02664fc → f3fc176`) is exactly the 15-line abstain-row persistence block.
7. **Budget/authorization** — GO `REGISTERED_NOT_CONSUMED` (cycle_state + registry + p3);
   no scored artifact exists anywhere; S1 `SEALED_UNTOUCHED`; runner has no network imports.

## Live negative-path probes (all PASS)

| Probe | Expected | Observed |
|---|---|---|
| GO phrase without env flag | refuse, exit 2, lock untouched | exit 2, `SCORED EXECUTION REFUSED ... two-key; P-8` |
| env flag =1, wrong phrase | refuse, exit 2 | exit 2 |
| env value `true` (not `1`), exact phrase | refuse, exit 2 (strict equality) | exit 2 |
| LockBusy with REAL flock held by auditor | exit 3, `NOT_RUN_RESOURCE_CONFLICT`, single attempt | exit 3, stderr names the holder (`A7_PRELAUNCH_AUDIT_LOCKPROBE pid 84713`), no writes |

## Findings (none blocking)

- **F-1 MEDIUM — stale stream pin.** `substrate_manifest_digest` pins the form4 stream at
  427,096 rows / `784414de...`; the live (integration) stream is 546,039 rows /
  `6ac2cd5b...` after the INC-V13-12/13 deterministic reparse of the UNCHANGED XML bytes
  (XMLs 5/5 MATCH; count exact). The digest's own "any drift = SUBSTRATE_DRIFT fail-closed"
  rule is therefore formally violated and was not flagged; there is no INC-V13-12/13
  event-log entry (disclosure exists only in the `446dd72` commit message). Proven benign
  here: E1's quoted code histogram matches the live stream EXACTLY row-for-row (D2 verifiably
  measured this vintage) and the selected family's scored path never reads the stream.
  → Re-pin + append the missing event before ANY future form4_stream lane.
- **F-2 MEDIUM — freeze prose vs artifact on the price gate.** `selection_freeze.json`
  says "coverage gate PASS 2178/2178 + 12 benchmarks"; the cited manifest truthfully
  records `FAIL_COVERAGE` (2140/2178 restored, 0 missing, 38 named thin/invalid series,
  ratio 0.9826; the script's PASS rule requires zero invalid). Nothing consumed the false
  claim — D2 measured the real 2140 (ge63 2139), the runner treats missing series as
  measured exclusions, and all staged bytes sha-verify. → A1 erratum correcting the prose
  before the next freeze-consuming step.
- **F-3 LOW** — `verify_price_manifest()` is not wired into the scored path (full verify
  passed in this audit; ledger pins the manifest sha). Recommended at scored execution.
- **F-4 LOW** — `LOCK_ROLE` hardcoded `A8_DRYRUN`; a scored run would register the lock
  under the dry-run role vs Q6's `E_SCORED_EXECUTION` bookkeeping (Q6 itself: the role
  string is not the authorization mechanism). Recommended before scored execution.
- **F-5 NOTE** — `code_freeze_sha()` is dead code.

## Handoff

- Verdict: `STOCKS_V13_S0_LAUNCH_AUTHORIZED` — owner must now type FRESH
  `GO STOCKS V13 SCORED EXECUTION` + `STOCKS_V13_LAUNCH_AUTHORIZED=1` (P-8; no carry-over).
- Test rerun: 20 passed / 0 failed, exit 0.
- Tree: clean apart from these two audit artifacts, committed by explicit pathspec on
  branch `orca/v13-q-a7-prelaunch2` (the prescribed name `orca/v13-q-a7-prelaunch` was
  taken by a foreign older repo generation — tip `a7595cb` 2026-09-04, diverged at
  `b8876ef`, a different program with "6 arms / 1966 tests"; left untouched per
  audit-only discipline; suffix per the repo's own `-prelaunch2/3` precedent).
