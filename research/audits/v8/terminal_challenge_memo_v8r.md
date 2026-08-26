# A7 Terminal Challenge Memo — Sprint V8R

- **Author:** A7 (independent terminal auditor)
- **UTC:** 2026-08-26T03:11:17Z
- **Scope:** four finalized scored V8 trials + defect archive + family verdict + V8X §8 gate assessment
- **Machine-readable companion:** `research/audits/v8/a7_terminal_audit.json`

## 1. Verdict

**AUDIT: PASS. Terminal recommendation: `V8_REJECT_ALL_CANDIDATE`.**

"PASS" certifies the *process*: the evidence chain is intact, artifacts are internally
consistent, hashes recompute, provenance pins are identical and verifiable, the defect
archive is honest, and nothing was found that undermines the recorded outcomes. The
*strategies* failed — clearly and reproducibly — and REJECT is the honest scientific
outcome.

## 2. What was independently verified (not trusted)

1. **Finalizer internal consistency, all four trials.** FG2 measured values equal
   `canonical_metrics.json` exactly (`net_pnl`, `profit_factor`, folds); FG4 MDD equals
   canonical MDD; scorecard group arithmetic sums to stated totals (42 / 30 / 36 / 57)
   with `band=null`, `score_meaningful=false` — correct, since a hard-gate failure can
   never be rescued by score. Stress-manifest variant PnLs tie out to FG5 measurements.
2. **Hashes recomputed by this auditor.** Every file listed in each trial's
   `final_gate_result.source_hashes` (8/trial) and every entry in `artifact_hashes.json`
   (22/trial) was re-hashed: **0 mismatches across 120 checks**.
3. **Provenance pins identical x4.** All launch manifests pin
   `baseline_sha256=738f1985…`, `attestation_sha256=1789ca7f…`,
   `git_commit_at_launch=a1f86d185867378a3721d2d39585e4427166f27c`, preflight PASS.
   The pinned baseline/attestation files exist in all four exec trees and hash-match the pins.
4. **Reproduction.** Each `reproduction_report.json` references its on-disk
   `results/reproduction_v8/VERIFY-V8-*/comparison.json`; all four exist with
   `all_match=true` over 21 comparison checks from a separate rerun process, including
   byte-identical artifact sha256s (spot-read VERIFY-V8-WREV-3D in full).
5. **NOT_TESTED/SKIP legitimacy.**
   - FG1 `funding_sign_matches_hypothesis: NOT_TESTED` — legitimate: `direction`
     absent from resolved contract (integration finding **R7**); fail-closed kept.
   - FG7 `a7_no_unresolved_high_critical: NOT_TESTED` — correct fail-closed on missing
     audit payload at finalize time; closed by this audit (0 high / 0 critical).
   - FG8 `SKIPPED` x4 — legitimate per the documented rule embedded in every gate
     result: `min_weekly_rebalances` absent from contract ⇒ SKIPPED honestly, not a
     silent pass.
6. **Family budget honored.** Every manifest declares `declared_family_trials: 4`;
   exactly four scored trials exist; abort archives contain no scored artifacts.

## 3. Defect-archive honesty (PROVDEFECT)

The archived attempt
(`XSECT-WMOM-7D-CONTROL.PROVDEFECT-V8R-20260826T024539Z`) exists with its full artifact
set and its own registry shard `.PROVDEFECT` file. Its manifest honestly records
`preflight: NOT_ENFORCED` with null baseline/attestation pins — the exact operator env
omission claimed. The event log entry (`PROV_ENFORCEMENT_DEFECT_ARCHIVE`) states class,
supersession, and `pnl_informed_decisions: false`.

Downstream non-use is confirmed structurally: the clean relaunch started one second
after the archive event (02:45:39Z → 02:45:40Z); the active registry shard contains a
single row appended post-relaunch pointing only to the active path; no active-trial
artifact references PROVDEFECT. Identical metrics between archive and active dir are the
expected signature of a deterministic rerun over identical frozen argv — not evidence of
reuse; the archived attempt itself was scored `DIAGNOSTIC_ONLY`.

Three PRELAUNCHABORT archives (A/B/C) are likewise honestly logged with
`zero_scored_confirmed: true`.

## 4. Family-level sanity check → REJECT

| Lookback | total_pnl | PF | PF≥1.10 | PnL>0 |
|---|---:|---:|---|---|
| WREV-3D | −3,264.88 | 0.9871 | NO | NO |
| WREV-7D | −26,097.10 | 0.8749 | NO | NO |
| WREV-14D | −8,118.52 | 0.9613 | NO | NO |

All three reversal lookbacks fail both family-pair conditions ⇒ zero passing adjacent
pairs under §7.2 ⇒ **`V8_REJECT_ALL_CANDIDATE`**. The momentum control (+5,973.69)
outperformed every reversal treatment, independently corroborating mechanism failure —
while itself remaining NOT_ELIGIBLE (PF 1.017 < 1.10; fold F3 = −35,728.21; MDD 29.1%).

## 5. Adversarial findings & residuals R1–R7

- **R1 (closed):** pre-launch aborts A/B/C — honestly logged, zero scored, archives inspected.
- **R2 (closed):** PROVDEFECT provenance omission — archived, superseded by clean relaunch,
  no downstream use. Honest.
- **R3 (residual, LOW):** sub-dollar experiment-level accounting identity residuals
  ($0.34 / $0.81 / $0.08 / −$0.77) vs the strict 1e-4 tolerance make
  `engine_accounting.all_ok=false`; disclosed inside `accounting_reconciliation.json`
  but not gated by any FG criterion. Fold-level identities reconcile to ~1e-10;
  funding reconciliation residuals ~1e-14. Immaterial on ~$10M+ turnover.
- **R4 (residual, LOW):** `dirty_worktree_at_launch: true` in all manifests — recorded
  honestly; determinism rests on frozen-artifact hashes plus all-match independent
  reruns, so provenance stands.
- **R5 (residual, LOW):** control's manifest flags (`negative_control: false`,
  `reverse: false`) vs finalizer control designation via matrix config
  (`v8_meta.is_control=true`); cosmetic metadata nuance, unambiguous in finalizer output.
- **R6 (closed):** FG7 audit-payload NOT_TESTED at finalize time — expected sequencing,
  now closed by this audit.
- **R7 (open by design, integration finding):** `direction`/FG1 funding-sign semantics
  absent for the weekly-reversal hypothesis; inherited V7 thresholds block intentionally
  omits it; NOT_TESTED fails closed. To be resolved in the next sprint's contract, not
  retrofitted here.

No HIGH or CRITICAL unresolved findings.

## 6. Why the reject verdict is trustworthy

Every number that produced the reject was (a) computed before scoring by frozen code at
a pinned head, (b) reproduced bit-for-bit by an independent process, (c) hash-chained
into finalizer inputs that this auditor re-verified, and (d) cross-corroborated across
siblings (e.g., the control's PnL appears as the threshold value in WREV-3D's FG1 row —
the gates actually consumed sibling results). Failures are multi-dimensional (PF, PnL,
fold signs, MDD 25–47% vs 10% cap, stress survival, single-point dependencies) and point
in the same direction as the economics: buying short-term losers in this universe did
not pay after costs. DSR/PBO were unavailable and scored zero without interpolation
(fail-closed), so nothing was inflated.

## 7. V8X crypto gate (§8 sub-gates)

| Sub-gate | Assessment |
|---|---|
| Prereg before first scored | **MET** — `v8x_spec_freeze.json` 2026-08-25T23:53:10Z, sha-pinned, predates first scored run 02:31:13Z |
| Corrected universe audit pass | **MET** — V1–V4 violations fixed; performance-blind top-10; byte-reproducible; tests pass |
| Engine contract supports cohort-10 | **UNMET** — no resolved V8X run contract anywhere |
| V8X own baseline/attestation | **UNMET** — none under `research/audits/v8x/` |
| V8X own frozen trial budget | **UNMET** — no V8X-specific budget artifact |

⇒ **`V8X_CRYPTO_NOT_STARTED_GATE_BLOCKED`.**

---
*A7 audited read-only; no production artifact modified; no backtest rerun.*
