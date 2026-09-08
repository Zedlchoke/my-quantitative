# A7 terminal audit — STOCKS-FREE-V12 (fresh context)

Verdict: **STOCKS_FREE_V12_TERMINAL_CONFIRMED_BLOCKED_DATA_OR_SELECTION**
(unresolved HIGH/CRITICAL blocking the terminal: **0**; 1 HIGH process-only
finding recorded, verdict-neutral).

## What was recomputed from bytes (not trusted from prose)

1. **Chain** — all 19 named commits exist on
   `orca/stocks-free-v12-integration` in the claimed order; every commit
   touches only its claimed files; a98f831 = 121 restored files + 1 artifact;
   d6ed0c9 is control-plane only. INC-V12-2's "hashes unchanged" verified from
   the 7d0ac2d diff (values identical, formatting/timestamp only).
2. **P0 census** — 4/4 durable-asset pins re-hashed MATCH by A7; all nine
   cross-check values recomputed from the V11 census at 9d3a061 and EQUAL
   (timing_layer_rows 5,453,478 even matches the V11 histogram total the
   artifact conservatively left as prior=null). INC-V12-1 confirmed against
   the round-2 lock registry (P0_CENSUS_LANE FINISHED 01:24:03→01:27:08Z,
   digest e1f98aa4, which the staged summary re-hashes to).
3. **P1 kernel** — beyond the required 12-file sample, ALL 121 manifest files
   verify byte-exact against BOTH the 9d3a061 blobs and the manifest shas;
   re-ran the two kernel suites targeted: 8 + 33 = 41 passed. Full repo suite
   not run (heavy cap).
4. **D2 gate (decisive)** — A7 re-ran the module ONCE under the machine-wide
   heavy lock via the wrapper: FINISHED, x2 BYTE_IDENTICAL within the run.
   Recorded staging pass files both hash to exactly c3e27a88…; A7's fresh
   audit vs the committed audit differs in exactly 7 run-stamp hunks
   (built_at_utc ×2, pass digests, git HEAD, lock times) with every measured
   value byte-equal — cross-run determinism proven at content level.
   - 6/6 proposal hashes re-hashed MATCH (files = d1 pins = audit pins).
   - A6 field-coverage kill reproduced by A7's own grep on the pinned panel:
     Revenues 6 / RevenueFromContract… 11 / COGS 0 / CostOfRevenue 0 vs
     Assets 337,241.
   - Kill logic adjudicated against the frozen bars: A4-H2's razor
     (0.2085 > frozen 0.20, margin −0.0085) measured under the proposal's own
     verbatim exposure formula; veto 12's 460-day cut equals V11's own
     falsified anchor statistic (checked in the V11 module at 9d3a061);
     A5-H1's 0.9923 > 0.98 self-subsumption kill is the declared rule on
     29,867 genuine common pairs; A5-H2's "control unrunnable" is a genuine
     design failure under the declared control definition (disjoint
     (entity, date) key spaces) and would also block under the module's
     shadowed union-grid path; A6 is fail-closed on an empty decision stream.
   - Module hygiene: no hardcoded verdicts, no PnL/returns, `_synth_ctx()`
     isolated to `--selfcheck`, pin mismatches exit 2, attestations sign wave
     b3524024, proposals contain gate definitions only.
5. **Counters & law** — budget 0/6 slots dead (zero scored cells exist);
   stocks 39/39; program 233/236 as-of-intake matches ledger commit 0474d9c
   wording per P-9; S1 SEALED_UNTOUCHED; workers 0; no upstream and no remote
   refs created (no push); diagnostic gate honestly NOT_RUN (prelaunch never
   reached); registry rows well-formed except F-1 below. Root registry
   untouched by A7 (validation run on copies against the worktree git).
6. **Label** — BLOCKED_DATA_OR_SELECTION is the correct fail-closed outcome:
   A4/A5 died at measured selection gates, A6 died on measured staged-data
   field coverage; REJECT_ALL would presume scored cells that do not exist;
   BLOCKED_PRELAUNCH and INCOMPLETE_NOT_PROMOTABLE do not describe a completed
   arc with zero selectable families.

## Findings (6; none verdict-changing)

- **F-1 HIGH (process, verdict-neutral)** — two staged registry rows
  (SFV12-A4-H1/H2) use primary_failure code `D2_NOVELTY_BLOCK`, which is not
  in the validator's SIGNATURE_CODES (`ANCESTRY_RHO_BLOCK` is the established
  code). Reproduced: root registry 55 entries PASS; with the six rows appended
  exactly 2 errors. The Lead must correct the two codes in the pending
  Lead-side root append or the mandated `--verify` will fail. A7 repaired
  nothing.
- **F-2 MEDIUM** — terminal report says "one FAILED release" for the D2 lock;
  the registry records EIGHTEEN FAILED releases, all with stderr tails honored
  (discipline exceeded; prose inaccurate).
- **F-3 MEDIUM** — the module shadows `identifiability_weights` (dead
  union-grid first definition); adjudicated verdict-invariant for all six
  proposals.
- **F-4 LOW** — A6 identifiability sub-label PASS alongside DESIGN_FAILURE
  control-runnability (overall verdict still BLOCKED).
- **F-5 LOW** — INC-V12-2/3/4 are disclosed in the event log rather than
  incidents.md (which holds only INC-V12-1).
- **F-6 LOW** — cross-run pass digest differs from the recorded digest by
  construction (embedded built_at_utc); recorded so the two digests are not
  misread as a determinism failure.

## A7 re-run record

Lock acquired 2026-09-08T07:44:23Z, released 07:50:35Z, FINISHED, registry-
recorded; pass digests fb433ebd… (both passes identical). The wrapper's
expected overwrite of the audit JSON with a fresh composed one happened; the
fresh summary verdicts equal the recorded ones; the d5ff2e2 committed version
remains the audit-of-record and is recoverable from git.
