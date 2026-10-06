# COST_STATE_VERIFY — CAL-COST lane, round FUTURES-5SYM-PRESCORED-20261005

Generated 2026-10-05. No network for the cost side; no new fee numbers introduced. Worktree
`/Users/hoangminhlong/my-quantitative/.worktrees/futures-5sym-prescored/prep`, HEAD at lane start
`b051d61e3a8d061412e1837bfc046a419e16dd10`.

## 1. Re-hash of the 3 key A7 files (fee_a7/ of FUTURES-SIX-SCORED-GATE-PREP-20261004)

Recomputed `shasum -a 256` at this worktree, 2026-10-05:

| file | recomputed sha256 | recorded comparator | verdict |
|---|---|---|---|
| `A7_FEE_REAUDIT.md` | `2c1095d63af35dda4b231e60d5ef63b71953ddfc207e9ebb02dc4e9884e211ad` | `research/control/FUTURES-5SYM-PRESCORED-20261005/intake/authority_matrix.json` (two entries: fee-A7 authorization evidence + pending-slot citation) records exactly `2c1095d6…ad` | **MATCH** |
| `a7_fee_digest.json` | `fa697c691d2914fd927d083321e1750b36ed919120c94ff181172233d327982e` | no external digest of this file is recorded anywhere in the worktree (grep across `research/` + `plans/` = only A7_FEE_REAUDIT's hash matched; the file cannot contain its own hash) | **NO RECORDED COMPARATOR — hash recorded here as the new baseline**; internal integrity spot-checked below |
| `a7_validator_report.json` | `a9078769531a752b2a6d0e9ceefcffe0ffdd16aa34ffb57b173a41f5dafd6722` | no byte-digest recorded; content comparator committed inside `a7_fee_digest.json` step4: "per_check_vs_committed_report: 37/37 IDENTICAL to p0_verify_validator_report.json" | **BYTE: no comparator; CONTENT: 37/37 statuses identical** (see §2) |

## 2. Comparators executed this lane (all local, zero network)

1. **Content-compare `a7_validator_report.json` vs committed
   `FUTURES-OVERNIGHT-PREP-20261003/fees_erratum/verify/p0_verify_validator_report.json`:**
   extracted 37 check statuses from each — **37 vs 37, 0 mismatches** (verdict of
   `a7_fee_digest.json` step4 reproduced independently at this worktree).
2. **Internal-integrity spot-check of digests recorded INSIDE `a7_fee_digest.json`** (4/4 MATCH):
   - `validate_fee_sources.py` →
     `FUTURES-OVERNIGHT-PREP-20261003/fees_erratum/impact/validate_fee_sources.py` =
     `fdead766f84521337ff4b7af3a861437a24317831bda9874494fc2c8fe780050` == step4.script_sha256 — MATCH
   - `archive_CME.php.html` → `…/fees_erratum/source/archive_CME.php.html` =
     `0f726c52…9e85` == step1 source record — MATCH
   - `fees_corrected.json` → `…/fees_erratum/source/fees_corrected.json` =
     `7cd65f25…aca8` == step1 source record — MATCH
   - `A7_SPEC.md` → `FUTURES-ES-V1-PACKET/audit/a7_spec/A7_SPEC.md` =
     `0ce63a0d…f5d0` == step1 supporting record — MATCH
3. **Downstream citation integrity (new this lane):** `fx_ja/COST_CONTRACT_6J_6A.md` L33 cites
   `fx_ja/6j_orientation_recheck.json` sha `6ca0baeb…`; recomputed =
   `6ca0baebe85abc7df9204f70252da44e72e0e396751a5114561640a25331ae54` — MATCH, and the file carries
   `rt_usd: 67.42` / `bp_of_notional: 8.4499` (L123-124) with headline "T1/1-tick RT $67.42 =
   8.4499 bp of $79,787.50".

**Overall verdict: FEE STATE UNCHANGED AND VERIFIED** — 3/3 files hash-stable against their best
available comparators; 0 drift; 0 new fee numbers.

## 3. Dual-variant cost-freeze law (RESTATEMENT, citation-only — nothing altered)

Source of record: `fee_a7/a7_fee_digest.json` step3.spec_family + step8.e4_both_variants;
`fee_a7/A7_FEE_REAUDIT.md` (verdict AUTHORIZED_WITH_FINDINGS, 0 HIGH/CRITICAL).

- **As-published SPEC prints** (`21.006 / 33.506 / 46.006`) carry the stale exchange cell 1.386
  (footnote-glued render: base 1.38 + marker 6) — **never consumable**; byte-identical stale lines
  remain UNDER REVIEW in the SPEC (digest step8.stale_lines_byte_identical L100/L101/L104).
- **Variant A (NFA basis):** reg 0.02 default (0.01 window 2014-10-01→2017-12-31) → all-in
  **2.25/side**; ES S1/S2/S3 per side 21.00 / 33.50 / 46.00 (RT 42.00 / 67.00 / 92.00); NQ S1/S2/S3
  per side 23.50 / 28.50 / 33.50.
- **Variant B (IBKR-offset basis):** reg 0.01 throughout → all-in **2.24/side**; ES 20.99 / 33.49 /
  45.99 (RT 41.98 / 66.98 / 91.98); NQ 23.49 / 28.49 / 33.49.
- Variant delta: −0.01/side = −0.02/RT. Both bases agree at 0.01 inside the window.
- **e.1–e.4 (sub-rulings incl. variant selection) remain UNRULED — owner slot; no lane may pick.**
  Language law in force: MODELED COST everywhere; "measured/complete cost" forbidden;
  VERIFIED_VS_ACCOUNT=NOT_RUN labels required (A7 step-7 scan: 0 positive uses).

## 4. Per-symbol modeled RT floors (citation-only)

| symbol | modeled RT floor | committed citation |
|---|---|---|
| 6J | **$67.42 RT T1/1-tick = 8.4499 bp** | `FUTURES-5SYM-PRESCORED-20261005/fx_ja/COST_CONTRACT_6J_6A.md` L33 ← `FUTURES-SIX-READINESS-20261004/fx_ja/6j_orientation_recheck.json` (sha `6ca0baeb…`, L123-124/201) |
| 6A | era law: **era1 T1/1-tick RT $104.92; era2 reference RT $54.92 (8.20 bp)** | `FUTURES-K6GATE-PREP-20261004/fx_ja/fxja_k6_gates.json` L79/L81 (`era1_T1_1tick_RT_usd`, `era2_reference_RT_usd`); era-2-only cost models may not back-cast into 2020 windows (fail-closed, per authority matrix) |
| 6E | **modeled RT 3.6–6.3 bp** | `FUTURES-SIX-ADOPT-PREP-20261004/hypo/HYPOTHESES_R2.md` L254; `FUTURES-K6GATE-PREP-20261004/fx_eb/FXEB_K6_GATES.md` L290; `FUTURES-5SYM-PRESCORED-20261005/fx_eb/COST_CONTRACT_6E_6B.md` L58 |
| 6B | **modeled RT 6.3–11.2 bp** | same three citations (L254 / L291 / L70) |
| NQ | all-in per side 2.25 (A) / 2.24 (B) + ES/NQ S1-S3 ladders as §3 | `fee_a7/a7_fee_digest.json` step3/step8 |

## 5. Reproduction commands (as run; all exit 0)

```bash
shasum -a 256 research/control/FUTURES-SIX-SCORED-GATE-PREP-20261004/fee_a7/A7_FEE_REAUDIT.md \
  research/control/FUTURES-SIX-SCORED-GATE-PREP-20261004/fee_a7/a7_fee_digest.json \
  research/control/FUTURES-SIX-SCORED-GATE-PREP-20261004/fee_a7/a7_validator_report.json
shasum -a 256 research/control/FUTURES-OVERNIGHT-PREP-20261003/fees_erratum/impact/validate_fee_sources.py
shasum -a 256 research/control/FUTURES-SIX-READINESS-20261004/fx_ja/6j_orientation_recheck.json
# status-extraction compare (python): 37 vs 37, 0 mismatches — logic embedded in lane report §2
grep -c "2c1095d63af35dda" research/control/FUTURES-5SYM-PRESCORED-20261005/intake/authority_matrix.json  # 2
```
