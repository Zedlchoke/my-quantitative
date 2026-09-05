# A7 PRELAUNCH AUDIT HANDOFF — cycle FOREX-FREE-V4

Auditor: A7 (independent prelaunch auditor; audit-only — no repair, no scored
run, no PnL computed). Branch `orca/forex-free-v4-q-a7-prelaunch`, base
`eec23cc2542fa8404c2315b14aaf77bfc5b0eff1` (verified HEAD). Audit UTC
2026-09-05T12:24:35Z (`stamp_source: machine_date_u`). Machine-readable
record: `a7_prelaunch_v4.json` (same directory).

> Note on this file: it previously held the A7-N/A9-F handoffs merged by the
> 1deef21 cherry-pick WITH unresolved conflict markers (finding F-A7-1). A7-N
> prose is recoverable at `git show 52c307a:research/audits/forex_free_v4/AUDIT_HANDOFF.md`;
> A9-F has its own clean handoff in `A9_F_AUDIT_HANDOFF.md`. This file is now
> the A7 prelaunch handoff.

## VERDICT: `FOREX_FREE_V4_S0_LAUNCH_REFUSED` (plan label: BLOCKED_PRELAUNCH)

- C1–C7, C9, C10: **9/10 PASS** on independent byte recompute.
- C8: **FAIL** on one sub-verification (conflict markers present).
- Unresolved HIGH/CRITICAL: **0**. Blocking findings: **1** (MEDIUM F-A7-1).
- The mandate is conjunctive: EVERY check must pass. It does not, so the
  launch authorization is refused despite a clean computational chain.

## Per-check one-liners (all recomputed from bytes; scripts under `scripts/`)

- **C1 FREEZE CHAIN PASS** — w4_freeze.json 19/19 code hashes recompute; V3
  kernel 7/7 hash-equal to w3_freeze.json; freeze commit expands exactly to
  `80d35096054e33689d7081c11fd5b7cf9379b49c`; w4 bytes identical
  80d3509→eec23cc; post-freeze diff touches only `forex_free_v4_run`
  control artifacts. (The freeze pins AMBIGUITIES.md in its marker-laden
  state — see F-A7-1.)
- **C2 SELECTION/IDENTITY PASS** — 2 families x 3 arms; budget 0/6; both
  proposal sha256 match (e827c904…, 6b4dbb7b…); 6 dry-run arm digests
  pairwise distinct; A1 rulings implemented: family2 eligibility =
  precomputed `first_readable_decision_utc` (fail-closed), family1
  `Z_STD_DDOF = 1` (family1.py:144), control = proposal's frozen mapping
  table verbatim (SHAM_AREA), drop-one = frozen 8-scenario harness.
- **C3 DATA/PIT PASS** — ledger sha256 `ae5e1f2e…cd6bd4` (220 rows),
  byte-identical across integration/audit trees; first 159 lines = base pin
  `169b9e44…f8cf895` byte-exact; all 61 appended rows are
  UNEVIDENCED→EVIDENCED upgrades of keys already in the base (61/61, zero
  non-monotone); A-2 recompute: on ALL keepers first_readable = first 16:00
  NY bar ≥ max(effective, available), 0 mismatches, 87 pre-announcement
  rows; evidenced vintages 8/8; snapshots 156/156; r-reproduce twin 8/8 +
  156/156 hash-identical; zero code writes into data_raw.
- **C4 KERNEL PASS** — fold grid `(2020-03-01, 2022-05-01, 2024-07-01,
  2026-09-02)` verbatim at scored_runner.py:144-145 (family2 mirrors);
  `book_stress` re-books the SAME trades per frozen tier ladder (1.0/1.5/2.0),
  asserts gross price PnL bit-identical across tiers, fails closed on row
  collision — genuine tiered re-booking, never rescaling.
- **C5 DRY-RUN HYGIENE PASS** — 6 arms, 6 distinct trial_ids and record_ids;
  scored/real_pnl/published all false; sanitized ledgers BYTE-IDENTICAL
  integration vs r-reproduce (`a70b924d…a073`, 6 records); twin reports
  differ in 3 runtime-metadata fields only; leak scan recursively walks every
  dict/list leaf with a strict key allowlist + forced zero placeholders on
  all outcome-suspect key names (1316 fields, 0 leaks) — my independent
  re-scan of the ledger confirms all outcome leaves are zero/None/False.
  Residual (LOW, recorded): string CONTENTS are not scanned, so a numeric
  payload hidden in an allowlisted string field (e.g. gate_reasons) would
  evade the key-name regex; mitigated by projection-built records and
  fail-closed unknown keys.
- **C6 LAUNCH-GATE REFUSAL PASS** — the exact mandated scored-mode CLI
  refuses: exit 1, no report, no ledger, nothing computed. All five gates
  verified live: W4 hash branch genuinely recomputes code hashes; S0 absence
  refuses; fresh-GO refuses the extinguished 03:41 OWNER_INTENT GO on BOTH
  bounds (must postdate S0 AND the P-8 reclassification 03:46:40Z) in the
  realistic attack; budget 0/6; S1 `SEALED_UNTOUCHED` + no opened marker.
  See probes in `scored_refusal_probe.json`.
- **C7 S1 SEAL PASS** — survivors_lock.json byte-identical to the V3R tree
  (`06e2aba1…9685`); V4 code only reads the state flag and the opened-marker
  existence; never touches the sealed artifact.
- **C8 FINDINGS REGISTER FAIL (one item)** — A4 HIGHs MOOT (REJECTED at
  selection); A5-P2 HIGH MOOT (DATA_BLOCKED); family1 emission defect
  FIXED-VERIFIED (f048ada/41933c3 pre-freeze; both regression tests present
  and passing: mid-stream-exit emission with exact bar stamps + end-to-end
  entries==decisions invariant); CA Saturday row FAIL-SAFE CORRECT (CA
  2020-03-27 → first_readable 2020-03-28T20:00Z = first NY decision bar after
  the end-of-day bound); A-2 adjudication + code + tests AGREE. The
  conflict-marker sub-check FAILS → F-A7-1.
- **C9 WORKERS/RESOURCES PASS** — 0 standing python/pytest workers; 37 Gi
  disk free.
- **C10 BOUNDARIES PASS** — plan terminal outcomes present (all five labels +
  section-10 launch rule); no paper/live/orders/network in V4 code (only
  benign prose, e.g. simulated broker-rollover financing formula); no push
  (no origin counterpart for this branch).

## Findings

| id | severity | status | summary |
|---|---|---|---|
| F-A7-1 | MEDIUM | UNRESOLVED | Conflict markers survive at HEAD in freeze-pinned `research/assets/forex_free_v4/AMBIGUITIES.md` (:1/:102/:206, from 223397f) and were present in the prior AUDIT_HANDOFF.md (from the later A9-F cherry-pick 1deef21 — the incident's "never git add an unmerged path" procedure violated again). The incident artifact's claim "AMBIGUITIES.md … no marker exposure" is FALSE against tree bytes. Zero score impact (documentation only; A1 adjudication independently fixes the semantics; code verified verbatim), but the record integrity fails and the C8 sub-check fails. Remediation (A1): deliberate marker resolution + incident-record correction + re-verified commit; then a trivial delta audit can authorize. |
| F-A7-2 | LOW | OPEN | W4 gate cannot pass on the frozen artifact as-is (`freeze_token` key absent; "W4_FREEZE_TOKEN_MISMATCH: freeze_token=None"). Launch requires an explicit arming edit to w4_freeze.json — fail-closed, but it must be a committed, logged post-freeze control-artifact change. |
| F-A7-3 | LOW | OPEN | The fresh-GO P-8 bound is conditional on `owner_intent_reclassification.json` existing; without it a stale GO is bounded only by the S0 timestamp (probe-documented). Real tree has the file and refuses the stale GO on both bounds. Hardening: make the reclass record mandatory for scored mode. |

Closed register items (verified, not blocking): A4 fold/window HIGHs MOOT;
A5-P2 monthly-clock HIGH MOOT; family1 emission defect FIXED with two
meaningful regression tests passing; CA Saturday-stamp row fail-safe correct;
family2 A-2 adjudication implemented and mutation-tested.

## What the owner should do

1. A1 clears F-A7-1 (two markdown files + incident-record correction +
   compile/suite re-verify), optionally folds in F-A7-2 (freeze_token arming)
   and F-A7-3 (mandatory reclass record) in the same remediation commit.
2. A7 delta audit re-verifies ONLY the touched files (deep chain stays valid —
   every hash/digest/twin re-verified in this audit covers the untouched
   artifacts).
3. Then, per PLAN §10: A7 issues `FOREX_FREE_V4_S0_LAUNCH_AUTHORIZED`
   (0 HIGH/CRITICAL) → owner types the FRESH exact-phrase
   `GO FOREX V4 SCORED EXECUTION` AFTER the S0 artifact exists (the 03:41 GO
   stays extinguished; the driver enforces both timestamp bounds).
