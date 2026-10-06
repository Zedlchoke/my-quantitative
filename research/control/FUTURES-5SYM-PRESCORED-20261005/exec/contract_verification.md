# CONTRACT_VERIFICATION — symbol_contracts.json vs per-symbol lane evidence

- Cycle **FUTURES-5SYM-PRESCORED-20261005**, wave 3, lane **CONTRACTS**, 2026-10-05.
- Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-5sym-prescored/prep`,
  branch `prep/futures-5sym-prescored-20261005`, HEAD measured `b2d086ca50996c628ec0373c4a3e8c2f2387c742`
  (one `git rev-parse HEAD` at lane start). No commits, no network, no other worktrees.
- Subject: `research/control/FUTURES-5SYM-PRESCORED-20261005/exec/symbol_contracts.json`
  sha256 `66bea4930b5faa087faa69ae29f7dd046cb69dd041435c815262a17c51b5b759`.
  **This lane edited NO value in that file.** Machine-readable twin:
  `contract_verification.json` (same directory).
- Locks: light reads only. Start: `researchctl.py locks inspect` → **FREE_PROVEN** (exit 0).
  End-of-lane line recorded in `dispatch/handoff_CONTRACTS.json`. No heavy job was run; the
  canonical lock was never needed.

## Method

Every field of every symbol row was compared against the per-symbol lane SPEC dossiers
(`nq/SPEC_NQ.md`, `fx_eb/SPEC_6E.md`, `fx_eb/SPEC_6B.md`, `fx_ja/SPEC_6J.md`,
`fx_ja/SPEC_6A_CONTINGENCY.md`, plus `research/control/FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md`
for the ES-compat row), and each SPEC claim was traced ONE level down: **≥2 raw citations
spot-verified per symbol**, every one read by this lane in this worktree:

| symbol | raw citations spot-verified (all hashes recomputed, match SPEC cites) |
|---|---|
| NQ | `HYPOTHESES_ESNQ_R3.md` L228-229 ("NQ: mult 20, tick 0.25 ($5.00/tick)"); `esnq_hypotheses.json::cost_law` slippage 5.00/10.00/15.00 = {1,2,3}×$5.00 + bindings "mult 20, tick 0.25 ($5.00)"; ROOT `S6_FRONT_SPREADS.json` NQ full-spread $32.50 (read-only root light read, disclosed by SPEC_NQ as outside this worktree) ⇒ 32.50/6.5 = $5.00/tick; `DATA_READINESS_NQ.md` L57 defect line confirmed |
| 6E | `DATA_READINESS_6E.md` §1 (EUR 125,000, 0.00005 = $6.25, USD-per-EUR); `fx_eb_readiness.json` 6E.dims; `tick_constancy_6e6b.json` 6E: GCD = 50,000 int-nano, close-on-grid 1.0 in all 5 windows incl. the 2020-11-23 pre/post pair, verdict **CONSTANT** |
| 6B | `DATA_READINESS_6B.md` §1 (GBP 62,500, 0.0001 = $6.25); `fx_eb_readiness.json` 6B.dims; `tick_constancy_6e6b.json` 6B: GCD = 100,000 int-nano × 5 windows, verdict **CONSTANT**; arithmetic 62,500 × 1e-4 = 6.25 |
| 6J | `6j_identity.json` (min_price_increment 500 int-nano unique across all 72 definition rows; unit 12.5M JPY decoded; GCD 500 in 2020-03 / 2023-01 / 2026-07; 1e-6 grid fails 48.49% on-grid); `6j_orientation_recheck.json` (2024-07-11: 6JU4 +1.7284% while implied USDJPY 160.04→157.32 — 6J UP = yen stronger; burst +105 ticks 12:42Z, 17,448 lots) |
| 6A | `6a_tick_adjudication.json` (RESOLVED_PER_ERA: era-1 2020-01-02..2020-11-20, 231 sessions, grid 1e-04 = $10.00/tick, zero odd 5e-05 prints in 327k+ closes; from 2020-11-23 grid 5e-05 = $5.00/tick, odd prints ~49%, era-wide GCD 50,000 × 4 vendor chunks; break weekend 2020-11-20→2020-11-23); `aud_d2_tickera.json` (era-1 RT $104.92 vs era-2 $54.92 — arithmetic corroborates $10 vs $5 per tick; 6J placebo flat ×1.00) |
| ES | `SPEC_PB1_ES.md` §1 (mult 50, tick 0.25 = $12.50); `HYPOTHESES_ESNQ_R3.md` L228 (independent second source); `DATA_READINESS_ES.md` Dim 1 (third source) |

All 12 SPEC-cited sha256 prefixes recomputed by this lane match exactly (445f7499, fc14b69c,
c7ea807b, 555ab253, c342e872, 6ca0baeb, 06367e67, b6b9927e, adc15c67, 14426cfb, 9dfe7b12,
68e21c56) — the committed evidence chain is intact.

## Result — 72 verification units: 67 MATCH · 1 MISMATCH · 4 PENDING

Counting convention: 12 units per symbol (tick_size, tick_value_usd, multiplier, exchange,
quote_ccy, base_ccy, long_base_sign, quote_direction_note, session_mask_spec.tz, .rth, .note,
era_table). Full per-field detail with paths + sha256: `contract_verification.json`.

| symbol | MATCH | MISMATCH | PENDING | runner-consumed numbers |
|---|---|---|---|---|
| ES (compat) | 12 | 0 | 0 | all MATCH |
| NQ | 11 | 1 (session_mask rth close bound) | 0 | all MATCH |
| 6E | 11 | 0 | 1 (session_mask rth) | all MATCH |
| 6B | 11 | 0 | 1 (session_mask rth) | all MATCH |
| 6J | 11 | 0 | 1 (session_mask rth) | all MATCH (incl. quote-direction law, T18 basis) |
| 6A | 11 | 0 | 1 (session_mask rth) | all MATCH — BOTH era rows, incl. boundary 2020-11-23 |

Arithmetic invariants `tick_value_usd / tick_size == multiplier` hold on all 7 era rows
(ES, NQ, 6E, 6B, 6J, 6A-era1, 6A-era2).

## Findings for the controller (no contract value was edited)

1. **F1 — MISMATCH (descriptive-only field):** NQ `session_mask_spec.rth` = "08:30-15:00".
   The 08:30 CT open matches; the flat **15:00 close has no NQ evidence and contradicts the
   committed era-correct close law** (`nq/CALENDAR_PIT_POLICY_NQ.md`: RTH span = "08:30 CT →
   era-correct close" — 16:15 CT through 2015-09-18, 16:00 CT from 2015-09-21, era-A Friday
   class 15:15 CT; also `RUNNER_COMPAT_NQ.md` RC-2.4). The field is descriptive-only —
   `scored_runner_v2` consumes bars as a plain ordered series and never filters by session
   mask — so runner behavior is unaffected. A corrected value must come from the NQ lane.
2. **F2 — PENDING ×4:** `session_mask_spec.rth` = "07:20-14:00" on 6E/6B/6J/6A has **zero
   committed evidence** (repo grep: the only occurrences of "07:20" are the contracts file
   itself and an unrelated first_bar timestamp). The FX session law of record is the Globex
   17:00→16:00 CT template; 6E/6B weekly-hours verbatim captures are structurally
   NOT_OBTAINED. Fail-closed: keep PENDING; never silently inherit into a freeze.
3. **F3 — posture supersession (recorded, not edited):** the ES row's "carried-unverified"
   caveat is discharged — SPEC_PB1_ES §1 + HYPOTHESES_ESNQ_R3 L228 + DATA_READINESS_ES Dim 1
   all carry the numbers (12/12 MATCH). The row stays compatibility-only (not a target symbol).
4. **F4:** `DATA_READINESS_NQ.md` L57 prints "NQ tick 0.25 pt / $2.50" — confirmed present;
   it is the pointer-line defect SPEC_NQ flags as **P5-NQ4** (never consumable). The contract's
   $5.00/tick stands on the three-source triangulation, all three sources read by this lane.
5. **F5 — disclosed limitations carried:** NQ identity remains PASS_ARITHMETIC_TRIANGULATED
   (no vendor definition capture in repo — SPEC_NQ disclosure); 6A official rulebook page
   BLOCKED_TRANSPORT (the era split is a data-side adjudication, PROVISIONAL pending D8).
6. **F6 — dispatch bookkeeping:** `DISPATCH_MANIFEST_WAVE3.json` carries `base_sha
   0732f22e…` while the dispatch packet and the measured HEAD are `b2d086ca…`. This lane used
   the measured HEAD as `actual_start_sha` and the packet-stated base as `dispatch_sha`.
7. **F7:** `exec/SYMBOL_COMPAT_MATRIX.md` untouched per instruction; its all-OPEN status is
   superseded **by reference** by this verification — contract numbers verified, session-mask
   descriptive fields F1/F2 remain open.

## Proposed evidence-backed view

`exec/symbol_contracts_verified.json` has been authored (PROPOSED, owner review): a
value-identical copy of `symbol_contracts.json` plus a `verification_evidence` block per row
(per-field verdicts, evidence paths + sha256). All original keys/values — including every
`PLACEHOLDER-PENDING-PER-SYMBOL-LANE` string — are preserved byte-for-value; the runner keeps
reading `symbol_contracts.json` unchanged until the controller swaps the file. Adoption is a
controller decision; this lane changes no runner behavior.

— End CONTRACT_VERIFICATION. PREP-only; nothing herein registers, schedules, scores, or
ratifies anything.
