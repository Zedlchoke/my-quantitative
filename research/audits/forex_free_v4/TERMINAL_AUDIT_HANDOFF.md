# FOREX-FREE-V4 — A7 TERMINAL AUDIT HANDOFF

- Auditor: A7-terminal (independent)
- Audit UTC: 2026-09-05T13:39:25Z (machine_date_u)
- Audited head: `e89fa4922935282a49d0583231aaa1af2290b33a` (orca/forex-free-v4-integration)
- Audit branch: `orca/forex-free-v4-r-a7-terminal` (one commit on top of the audited head)
- Machine-readable result: `a7_terminal_v4.json` (same directory)
- Recompute script: `scripts/a7_recompute_gates.py` (exit 0)

## VERDICT: CONFIRM_FOREX_FREE_V4_REJECT_ALL

The recorded terminal verdict is **upheld**. Every check reconciles from bytes;
no missed positive exists.

## What was recomputed (and how)

1. **Ancestry + freeze chain — PASS.**
   - `announcement_ledger_base_v1.jsonl` sha256 = pinned `169b9e44…`; the 159-row
     base prefix of `announcement_ledger.jsonl` is byte-identical to it
     (159 + 61 appended upgrades = 220 rows); extended pin `ae5e1f2e…` matches file bytes.
   - W4 freeze driver-five 5/5, full W4R view 19/19, W4R 19/19 vs tree bytes.
   - W4→W4R delta git-verified = `research/assets/forex_free_v4/AMBIGUITIES.md` only
     (`78c4cd78…`→`23500972…`; tree matches W4R). Zero `.py` delta.
   - V3 kernel 7/7 invariant: tree == `w3_freeze.json` == W4/W4R view.
   - Data: 156/156 price digests + 8/8 evidenced vintages vs manifests.

2. **Two-key launch legality — PASS.**
   - S0 `FOREX_FREE_V4_S0_LAUNCH_AUTHORIZED`, 0 HIGH/CRITICAL, 12:42:30Z.
   - `owner_fresh_go.json` verbatim is exactly `GO FOREX V4 SCORED EXECUTION`
     at 12:53:08Z — postdates S0 and the 03:46:40Z P-8 reclassification.
   - The driver hard-enforces the exact phrase and both postdate bounds
     (`exec_driver_v4.py` lines 84, 546–575).
   - Pre-GO refusal probe (12:50:53Z): shorthand `FRESH GO` refused — the gate was live.

3. **Scored recomputation (the heart) — PASS, zero discrepancies.**
   The hash-frozen kernel's own `stage_a_gates()`/`mechanism_sanity()` applied to
   each published row's own numbers reproduces every recorded verdict and reason
   for all 6 cells. Every marginal gate re-derived by hand — no gate that should
   have passed was recorded failed, and none that should have failed passed.

| cell | fin-adj expectancy | PF | gates | recomputed gate_reasons (exact match) |
|---|---|---|---|---|
| family1:anchor | **+0.6754** | 1.0142 | FAIL (6) | PF_BELOW_1.10, FEWER_THAN_2_POSITIVE_POPULATED_FOLDS, POPULATED_FOLD_PF_BELOW_0.80, MDD_ABOVE_FROZEN_CEILING, STRESS_TIER_2.0_FAIL, DROPOUT_SURVIVAL_BELOW_6_OF_8 |
| family1:neighbour | +1.7800 | 1.0379 | FAIL (4) | PF_BELOW_1.10, FEWER_THAN_2_POSITIVE_POPULATED_FOLDS, POPULATED_FOLD_PF_BELOW_0.80, MDD_ABOVE_FROZEN_CEILING |
| family1:control | -7.6647 | 0.8498 | FAIL (8) | EXPECTANCY_NONPOSITIVE, PF_BELOW_1.10, FEWER_THAN_2_POSITIVE_POPULATED_FOLDS, POPULATED_FOLD_PF_BELOW_0.80, MDD_ABOVE_FROZEN_CEILING, STRESS_TIER_1.5_FAIL, STRESS_TIER_2.0_FAIL, DROPOUT_SURVIVAL_BELOW_6_OF_8 |
| family2:anchor | **-14.8276** | 0.8288 | FAIL (8) | EXPECTANCY_NONPOSITIVE, PF_BELOW_1.10, INCREMENTAL_ALPHA_NOT_POSITIVE, FEWER_THAN_2_POSITIVE_POPULATED_FOLDS, POSITIVE_FOLD_SHARE_ABOVE_50PCT, STRESS_TIER_1.5_FAIL, STRESS_TIER_2.0_FAIL, DROPOUT_SURVIVAL_BELOW_6_OF_8 |
| family2:neighbour | -30.2214 | 0.6719 | FAIL (9) | EXPECTANCY_NONPOSITIVE, PF_BELOW_1.10, FEWER_THAN_2_POSITIVE_POPULATED_FOLDS, POPULATED_FOLD_PF_BELOW_0.80, MDD_ABOVE_FROZEN_CEILING, POSITIVE_FOLD_SHARE_ABOVE_50PCT, STRESS_TIER_1.5_FAIL, STRESS_TIER_2.0_FAIL, DROPOUT_SURVIVAL_BELOW_6_OF_8 |
| family2:control | -46.2667 | 0.5535 | FAIL (9) | EXPECTANCY_NONPOSITIVE, PF_BELOW_1.10, FEWER_THAN_2_POSITIVE_POPULATED_FOLDS, POPULATED_FOLD_PF_BELOW_0.80, MDD_ABOVE_FROZEN_CEILING, POSITIVE_FOLD_SHARE_ABOVE_50PCT, STRESS_TIER_1.5_FAIL, STRESS_TIER_2.0_FAIL, DROPOUT_SURVIVAL_BELOW_6_OF_8 |

   Mechanism sanity (recomputed): family1 clean — control does NOT reproduce
   (-7.66) AND ran (650 decisions); family2 fires NEIGHBOUR_DOES_NOT_SUPPORT_ANCHOR
   (neighbour -30.22). Positive-gate passes preserved: f1:anchor expectancy>0,
   incremental alpha +8.45>0, price-only +2.62 same sign (no financing inversion),
   tier1.5 stress passes, fold-share 0.400 and concentration 0.253 within ceilings;
   f2:anchor MDD 2044.14 ≤ 2500 correctly NOT failed.

4. **Data semantics — PASS (hand-traced).**
   - family1: z-window strictly-prior valid NY-days; decision at completed
     16:00-NY close; hand-traced first anchor event (2020-05-01T20:00Z,
     S/z recomputed to 1e-12) fills at the NEXT weekday 16:00-NY daily bar open
     (2020-05-04T20:00Z, 0.64314997 AUD/USD) verified against raw H1 bytes;
     Sunday thin bars excluded; 4-day fill-lag ceiling enforced.
   - family2: eligibility = precomputed `first_readable_decision_utc`, null fails
     closed; dedupe 220→159; boundary trace on the NZ 1.75→1.5 cut gives as-of
     reads 1.75 / 1.75 / 1.5 at (avail-1s / avail / effective) — no lookahead;
     source row EVIDENCED with archive sha256.
   - W4 dry-run decision counts (660/620/650; 184/200/169) equal scored n_decisions.

5. **Reproduction — PASS.** Twin ledger (r-reproduce @ 22e4ed8) byte-identical:
   `65725edc024826c51a2464c7bcc4e70cfcd19992b2f602feaa4cae80d4fef3a4`; twin report
   matches this audit's recomputation cell-for-cell.

6. **Denominators/budget — PASS.** 6 rows, all real_pnl+published, 0 dry-run,
   0 TECHABORT (the two event_log grep hits are the phrase "TECHABORT discipline"
   in narrative text), budget 6/6 (ledger-derived), program 18 (6+6+6 rows
   verified in V1/V2/V3 ledgers) + 6 = 24.

7. **Boundaries — PASS.** `survivors_lock.json` blob `5f7fcc38…` byte-identical
   from V3 close (8f674f1) through the audited head; S1 never opened;
   `research/wayfinder/SURVIVORS.md` last touched by the V3R sync (S-1 CLOSED,
   invalidated) — no V4 commit touches it, no survivor claimed; no push
   (origin carries only the V4 seed 5d30828; local 26 ahead); no paper/live/order
   artifacts.

8. **Statistics — PASS.** The terminal verdict's program statement
   (24 cells, 0 V4 survivors) matches the recomputed counts exactly.

## Findings (5 informational, 0 blocking)

1. **A7T-V4-1** `PLAN_forex_v4.md` is on main (4eafdb7), not in the v4 branch
   tree; frozen gate semantics match the kernel constants — bookkeeping note.
2. **A7T-V4-2** USD-drift gate skipped for both family2 cells (54/58 days < 60)
   — frozen inherited fail-open semantic ("otherwise it cannot fail");
   decision-irrelevant here; record as latent for future cycles.
3. **A7T-V4-3** Two PnL bases coexist per row: `financing_adjusted_pnl_usd`
   (all booked trades; f2 anchor -4302.03, quoted in the verdict) vs
   `base.total_pnl`/gates (post-purge scored book; -1112.07 over 75 trades).
   Both digest-covered and consistent; label the basis when quoting.
4. **A7T-V4-4** V2 ledger rows carry published=False/observed=True (old schema);
   the 18-cell denominator counts computed outcomes. No V4 effect.
5. **A7T-V4-5** `run_contract.json` budget.used frozen at 0; driver counts
   consumed cells from the ledger, so 6/6 is correct. Cosmetic.

## Bottom line for the Lead

FOREX-FREE-V4 closes legitimately as **FOREX_FREE_V4_REJECT_ALL**: launch was
two-key legal, all six scored cells are negative under the frozen Stage-A gates
with exact gate-reason provenance, reproduction is byte-identical on the twin,
denominators are 18+6=24 with zero TECHABORT, S1 stays sealed and no survivor
was claimed. No correction to the terminal verdict is required.
