# COST_CONTRACT_6J_6A — per-symbol, per-era modeled cost ladders (DRAFT)

- Lane FXJA, round FUTURES-5SYM-PRESCORED-20261005. **Labels binding on
  EVERY cell below: MODELED COST / UNDER REVIEW /
  VERIFIED_VS_ACCOUNT=NOT_RUN.** The words "measured cost" and "complete
  cost" are FORBIDDEN. **BBO NOT_RUN (D5 law)** — spread is a high-biased
  close-proxy, slippage is a declared research assumption (D1 class), no
  fill/queue claim exists. 0 PnL; arithmetic only.
- Fee layer (both symbols; FEES_CORRECTED §2 FX row, P0-VERIFY upheld,
  FX fee-group mapping PARTIAL): **T1 2.46 / T2 2.26 / T3 2.06 / T4 1.86
  USD/side**, tick-invariant across the 6A eras.
- Stress law (DC §1.7 / CYCLE_LAUNCH_DRAFT §3): the ×1.0 column is the gate
  number; **×1.5 / ×2.0 apply to (spread + declared slippage) only — the fee
  layer is invariant.** ×1.0 cells are committed re-derivations (cited);
  ×1.5/×2.0 columns are **DERIVED** arithmetic on committed inputs (no new
  measurement; recomputable from the formulas below).
- Dual-variant A/B fee law (COST_FREEZE_ERRATUM, correction of record, sha256
  `cf83bc2d41bd6a302523d8acea770b8bff553903aa752c17098eebba53f09ae8`): applies
  to the ES/NQ regulatory cell (NFA-basis Variant A vs IBKR-offset Variant B,
  D3). **For 6J/6A the FX fee row is not the contested cell** — the FX all-in
  2.46 composition (0.85 + 1.60 + 0.01) is single-sourced; the erratum's
  standing law carried here is: **stale/glued prints (1.386-class,
  21.006-class) are NEVER consumable**, and no silent D3 default exists.

## §1 6J ladder (notional of record $79,787.50 = 12,500,000 × 0.006383, price re-measured from the raw 2026 tail, last bar 2026-09-30 23:59Z)

Spread close-proxy **$25.00/side** (4 ticks × $6.25; 20d median; HIGH-BIASED,
DC §1.7 6J column). Slippage S1/S2/S3 = 1/2/3 ticks × $6.25/side. Per-side =
fee + m × (spread + slippage); RT = 2 × per-side; bp = RT / notional × 10⁴.

| tier × stress | per-side USD | RT USD | bp of notional | provenance |
|---|---|---|---|---|
| T1 · S1 · ×1.0 | 33.71 | **67.42** | **8.4499** | COMMITTED (`fx_ja/6j_orientation_recheck.json`, sha `6ca0baeb…`) |
| T1 · S2 · ×1.0 | 39.96 | 79.92 | 10.0166 | COMMITTED (same table) |
| T1 · S3 · ×1.0 | 46.21 | 92.42 | 11.5833 | COMMITTED (same table) |
| T1 · S1 · ×1.5 | 49.335 | 98.67 | 12.3666 | DERIVED |
| T1 · S2 · ×1.5 | 58.71 | 117.42 | 14.7166 | DERIVED |
| T1 · S3 · ×1.5 | 68.085 | 136.17 | 17.0666 | DERIVED |
| T1 · S1 · ×2.0 | 64.96 | 129.92 | 16.2833 | DERIVED |
| T1 · S2 · ×2.0 | 77.46 | 154.92 | 19.4166 | DERIVED |
| T1 · S3 · ×2.0 | 89.96 | 179.92 | 22.5499 | DERIVED |

Full committed T1–T4 × slip{1,2,3} table (24 cells): `6j_orientation_recheck.json:round_trip_table_at_claim_notional_79787_50`
— T2 8.3998/9.9665/11.5331 bp, T3 8.3497/9.9163/11.4830 bp, T4
8.2995/9.8662/11.4329 bp at ×1.0. **Committed tier range 8.30–12.10 bp**
(T4/slip1 low; T1/slip3 12.1018 bp at the band-LOW price 0.0061095,
notional $76,368.75; at the band-HIGH price 0.0099205, notional $124,006.25,
T1/slip1 = 5.4368 bp — notional-price sensitivity is committed in
`band_sensitivity_T1`). Session-of-day floor (JF1-7/JF3-8, PROVISIONAL):
Tokyo-window entry fills carry +1 tick additional slippage assumption
(entry-side only); the ×1.5/×2.0 ladder above is the table-level stress and
the session floor stacks on top of it as declared, never instead of it.

## §2 6A era-2 ladder (from 2020-11-23; notional of record $66,960 = 100,000 × 0.6696)

Spread close-proxy **$20.00/side** (4 ticks × $5.00, post-break; DC §1.7 6A
column). Slippage S1/S2/S3 = 1/2/3 ticks × $5.00/side. Era-2 reference of
record: **RT T1/1-tick $54.92 = 8.20 bp** (8.2019 recomputed exact,
DATA_READINESS_6A Dim 6; validation PASS in the D-2 audit).

| tier × stress | per-side USD | RT USD | bp of notional | provenance |
|---|---|---|---|---|
| T1 · S1 · ×1.0 | 27.46 | **54.92** | **8.2019** | COMMITTED (`aud_d2_tickera.json` era-2 reference recomputed; DATA_READINESS_6A) |
| T1 · S2 · ×1.0 | 32.46 | 64.92 | 9.6953 | DERIVED |
| T1 · S3 · ×1.0 | 37.46 | 74.92 | 11.1888 | DERIVED |
| T1 · S1 · ×1.5 | 39.96 | 79.92 | 11.9355 | DERIVED |
| T1 · S2 · ×1.5 | 47.46 | 94.92 | 14.1756 | DERIVED |
| T1 · S3 · ×1.5 | 54.96 | 109.92 | 16.4158 | DERIVED |
| T1 · S1 · ×2.0 | 52.46 | 104.92 | 15.6691 | DERIVED |
| T1 · S2 · ×2.0 | 62.46 | 124.92 | 18.6559 | DERIVED |
| T1 · S3 · ×2.0 | 72.46 | 144.92 | 21.6428 | DERIVED |

**Valid ONLY for sessions ≥ 2020-11-23.**

## §3 6A era-1 ladder (2020-01-02..2020-11-20, 231 sessions; $10.00/tick; notional base $69,120 = 100,000 × 0.6912, median era-1 held-session close measured)

Spread close-proxy **$40.00/side** (4 ticks × $10.00 — the D-2
operationalization "spread proxy and tick components double"). Slippage
S1/S2/S3 = 1/2/3 ticks × $10.00/side. **Headline COMMITTED: RT T1/1-tick
$104.92 = 15.1794 bp** (the D-2 audit's ×1.85-not-×2 law: the fee layer is
tick-invariant).

| tier × stress | per-side USD | RT USD | bp of notional ($69,120 @ 0.6912) | provenance |
|---|---|---|---|---|
| T1 · S1 · ×1.0 | 52.46 | **104.92** | **15.1794** | COMMITTED (`aud_d2_tickera.json:step_i_era1_cost_surface.era1_table_median_px`) |
| T1 · S2 · ×1.0 | 62.46 | 124.92 | 18.0729 | COMMITTED (same table) |
| T1 · S3 · ×1.0 | 72.46 | 144.92 | 20.9664 | COMMITTED (same table) |
| T1 · S1 · ×1.5 | 77.46 | 154.92 | 22.4132 | DERIVED |
| T1 · S2 · ×1.5 | 92.46 | 184.92 | 26.7535 | DERIVED |
| T1 · S3 · ×1.5 | 107.46 | 214.92 | 31.0937 | DERIVED |
| T1 · S1 · ×2.0 | 102.46 | 204.92 | 29.6470 | DERIVED |
| T1 · S2 · ×2.0 | 122.46 | 244.92 | 35.4340 | DERIVED |
| T1 · S3 · ×2.0 | 142.46 | 284.92 | 41.2211 | DERIVED |

Price-base sensitivity (committed in the audit): era-1 final session close
0.7306 (2020-11-20) ⇒ notional $73,060 ⇒ T1/S1/×1.0 = 14.3608 bp. Full
T2–T4 × slip tables for both price bases: `aud_d2_tickera.json`.

**NO-BACK-CAST LAW (binding until D8 ruled): era-2 cost models may NOT be
back-cast into 2020-era windows.** Any 6A computation that touches sessions
≤ 2020-11-20 must branch to the §3 table; pooling across 2020-11-20/23
without an explicit era split is a spec violation, fail-closed. The boundary
label is data-side PROVISIONAL (official rulebook page BLOCKED_TRANSPORT;
D8 Option A ratifies the measured boundary, Option B demands the exchange
document).

## §4 Shared laws

1. **Conservative fill law** (D5): fill = next-bar open; no limit/queue
   claims; spread is a close-proxy; SL-priority on same-bar TP/SL. BBO/
   true spread/queue/fill-probability NOT_RUN on both symbols.
2. **Threshold honesty (pre-committed)**: 6J RT 8.5–14.7 bp vs JF1 MPM-day
   median |return| 57 bp — not automatically cost-dead, but per-event MDE at
   n=54 (13–19 bp) sits at/above cost (K2 live). 6A era-2 RT 8.2 bp vs AF1
   ±5' signal scale 4.35 bp — per-event signal BELOW one RT; K2 is the
   EXPECTED AF1 outcome (stated a priori). RMM-class legs: MDE ≈12.5 bp at
   n≈108 — power-marginal by construction.
3. **Forbidden-word scan**: "measured cost" / "complete cost" must not appear
   in any downstream output; enforced at freeze by the A7 language scan
   (CYCLE_LAUNCH_DRAFT §6 step 2).
4. **Freeze binding**: the cost table consumed at a future registration is
   the sha-pinned table in the selection freeze; drift vs this contract's
   committed sources ⇒ BLOCKED, never silent reuse.

— End COST_CONTRACT_6J_6A. All ×1.0 cells cite committed artifacts; every
×1.5/×2.0 cell is DERIVED by the formula fee + m×(spread+slippage), ×2 for
RT, ÷ notional ×10⁴ for bp.
