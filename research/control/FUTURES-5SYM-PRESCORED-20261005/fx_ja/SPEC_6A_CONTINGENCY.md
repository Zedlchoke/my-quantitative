# SPEC_6A_CONTINGENCY — Australian Dollar futures (CME 6A) CONTINGENCY-ONLY spec DRAFT

> **CONTINGENCY-ONLY BANNER (binding).** **6A is PB3 PARK — 0 budget, 0
> identities, 0 scheduled work.** Everything below is a contingency annex
> draft: it activates ONLY after (i) an owner **PB3 lift** AND (ii) ratification
> of **D8** (6A era-aware tick/cost law) — plus, for any scored cell, the
> standing **D9** cease-guard law and fee A7 (D2). Until then the frozen
> 26-ID contingency table of `budget/identity_tables.json` (§6 here) is
> carried VERBATIM and **must not be expanded**. This annex is PREP-only:
> 0 scored runs, 0 PnL, outcome-blind. `NO_GO_REGISTER / NO_GO_SCORE /
> NO_GO_ORDER` in force. Structure follows the ES precedent
> `SPEC_PB1_ES.md` / `SPEC_6J.md` so a post-lift freeze can consume it
> section-for-section.
>
> Lane FXJA, round FUTURES-5SYM-PRESCORED-20261005, worktree
> `/Users/hoangminhlong/my-quantitative/.worktrees/futures-5sym-prescored/prep`
> (branch `prep/futures-5sym-prescored-20261005`, base `ffed828f…`). Missing
> evidence = NOT_RUN, never inferred PASS. New decision IDs prefixed **P5-**.

---

## §1 Instrument identity — VERIFIED, TICK CONFLICT RESOLVED_PER_ERA (measured)

| item | value | evidence of record |
|---|---|---|
| Symbol / venue | 6A, CME Globex | `FUTURES-DEEPRESEARCH-V2-20261003/dossiers_v2/6A_DEEP_v2.md` (sha256 `76d32f1c776ceaa614315e08f959d3ab6034b345ca9b4a3ad014e0741e7ac832`) |
| Multiplier | **100,000 AUD** | `fx_ja/6a_tick_adjudication.json` (FUTURES-SIX-READINESS-20261004, sha256 `06367e674d6288714a7f6d3bc5d04920bd7be4e6372ac2f5cb533f280e83282d`): definitions `unit_of_measure_qty` decoded + S1_IDENTITY '100000' |
| Quote orientation | **USD per AUD; 6A UP = AUD stronger** | same artifact `quote_orientation` field |
| **TICK — ERA LAW** | **Era 1 (2020-01-02..2020-11-20, 231 sessions): grid 1e-04 USD/AUD = $10.00/tick. Era 2 (from 2020-11-23): grid 5e-05 = $5.00/tick.** | **VERIFIED exactly as the committed law states** (`6a_tick_adjudication.json:adjudication`): era-1 zero odd 5e-05-multiple closes anywhere in **327k+ closes** (odd share 0.000 every month Jan–Oct 2020), era-1 increment GCD = 100,000 int-nano; era-2 odd prints in **~49% of closes** in every chunk (first odd print session **2020-11-23**), era-wide GCD = 50,000 int-nano in all four vendor chunks; vendor `min_price_increment` = 5e-05 in all 72 definition rows 2023-10+ (consistent with era 2). Every close lies on the 5e-5 grid (1e-4 is a subset) — no pricing inconsistency. The BREAK sits in the weekend **2020-11-20 → 2020-11-23** (CME FX tick-halving window). The official rulebook page remains **BLOCKED_TRANSPORT**; the label is data-side **PROVISIONAL pending D8** — the adjudication is from data and stays so labeled |

**Verification status: the dispatch's tentative "0.0001=$10 era-1 vs
0.00005=$5 era-2" is confirmed verbatim by the committed evidence.** The
baseline's "5e-05 used throughout = $5.00/tick" is correct only from
2020-11-23; tick-denominated cost/spread models must be era-aware.

## §2 TICK-ERA LAW (D8 pending ratification) — cost-bearing consequences

- **Era-aware cost (D-2 audit delivered,
  `FUTURES-K6GATE-PREP-20261004/fx_ja/aud_d2_tickera.json`, sha256 `14426cfb13ca7605f042895003c98c25b2a0d0227c33fc182bd3fd000fea3729`):**
  era-1 RT T1/1-tick **$104.92 = 15.18 bp** (15.1794 exact) of notional
  $69,120 (representative era-1 median held-session close 0.6912; final
  era-1 session close 0.7306 as sensitivity); era-2 reference of record RT
  T1/1-tick **$54.92 = 8.20 bp** (8.2019 recomputed exact) @ 0.6696
  (notional $66,960). Ratio ≈ **×1.85, not ×2** — the fee layer
  (2.46/side T1) is tick-invariant while tick-denominated components
  (spread proxy, slippage) double in era-1.
- **NO-BACK-CAST LAW (fail-closed default until D8 is ruled): era-2-only
  cost models may NOT back-cast into 2020-era windows.** No 6A spec may pool
  across the boundary silently; every 6A cost/spread/slippage model must
  branch on the era boundary (CYCLE_LAUNCH_DRAFT §3 "6A era-aware tick law
  (D8, REQUIRED spec element)"; HYPOTHESES_R2 AF4 f8).
- **Step test (same-date 6J placebo; descriptive only, no significance test
  at n=10 vs 10):** 6A unconditional close-to-close micro-increment halves
  in USD exactly at the boundary (step USD ×0.50, ticks ×1.00); unchanged-grid
  6J is flat (×1.00 / ×1.00) on identical date sets — the measured
  micro-increment is grid-bound on 6A and date-stable on 6J; the 2020 COVID
  confound does not move the 6J placebo (`aud_d2_tickera.json:step_ii`).
  This is the AF4 K2 substrate; **no AF4/6A verdict is issued** (overlay is
  contingency-only).

## §3 Session / calendar / roll / chain laws (contingency bindings)

- Session template 17:00 CT Sun → 16:00 CT Fri, 60-min break honored
  2020–2026 (dossier §7); Mar/Jun-2023 measured clean (23/22 traded weekday
  sessions, zero missing weekdays). Holiday session TIMES NOT_IN_CORPUS for
  every year (same open cell as 6J) — holiday-shortened sessions EXCLUDED
  fail-closed by bar-count/coverage rules.
- Panel of record: **2,703,211 outright 1m bars** 2020-01 → 2026-10-01 on 86
  contracts; 1,584 `6BU5` vendor-contaminant bars excluded by documented
  rule; 914 instrument-7084 (`6AM5`) pre-activation strays excluded;
  171,473 calendar-spread bars kept strictly separate; 0.0% zero-volume
  front minutes; 2026-10-01 partial tail (~2h).
- **Roll/chain: k=5 MEASURED — 27 rolls, span 2020-03-17 (6AH0→6AM0) ..
  2026-09-14 (6AU6→6AZ6), 1,746 held sessions, 32 quarterly contracts**
  (`fx_ja/6a_roll_measured.json`, sha256 `4172d2881a65e3310cdcd9c39a1549be5faa50897136d1b157ae6d96bb9da302`).
  **Baseline-code k=5 has 2 CEASE-GUARD VIOLATIONS**: 2024-12-17 (held dead
  6AZ4 while 6AH5 traded 55,675 lots) and 2026-06-16 (held dead 6AM6 while
  6AU6 traded 55,533) — the exact 6J-2022-09-20 pathology, on 6A, twice;
  exchange open both days. **Explicit cease-guard variant: 27 rolls, 0
  violations**, identical switch dates except the two above land 1 session
  earlier; 21/27 rolls fire the cease-guard trigger (abrupt), 6/27 the
  volume crossover (gradual). Calendar-rule cross-reference: declared
  calendar rule = 27 rolls; k=5 crossover dates land ~9–15d (median 11)
  after the declared roll dates — **roll-rule choice is material to timing,
  disclosed, never silently normalized** (RMM K6(c)).
- **Standing chain law (law-pending): the explicit cease-guard variant IS
  the standing chain-builder for 6A per the ADOPT-D9 proposal (extended to
  6A; 3-symbol evidence incl. 6A ×2), UNTIL D9 is ratified — then any
  builder must measure and disclose guard violations first (fail-closed
  default).** Chain choice must not flip any sign; switch-day returns
  spread-adjusted; "decided at close t, effective t+1" verbatim (DC §1.3).
- Expiry pointers **62/68 → 66/68** after CAL-JANQ (+4 single-vintage 2026
  quarters from the re-verified Sep-2023 capture: ADH26 16 Mar 2026, ADM26
  15 Jun 2026, ADU26 14 Sep 2026, ADZ26 14 Dec 2026). Residual NOT_OBTAINED:
  **exactly 2023Q1 (Mar) and 2023Q2 (Jun)** — derivation FORBIDDEN; absence
  evidence: `Future/37` captures are pre-span + 2023-09-16 (post-expiry),
  `Download.xls?productId=37` = zero archived captures (0-byte CDX, 2
  attempts; CAL_JANQ §4).

## §4 Event law (6A-specific)

- **RBA:** `rba/cash_rate_gate.html` (sha-verified in the readiness lane)
  carries **395 dated decisions 1990-08-02..2026-09-30**; 2023–2026 = 33
  dated decisions (11/8/8/6), 12 changes. **PASS_EVIDENCED at DATE
  granularity; decision TIME is not carried by the file** — the 14:30-Sydney
  anchor stays the DECLARED convention of 6A_DEEP §4.1 (the only off-Tuesday
  case, 2020-03-19 COVID emergency cut, is flagged and the effective_date − 1
  AU-business-day rule lands correctly). 2026 remaining meetings (v1-FACT):
  Nov 3, Dec 8. Surprise classification NOT_RUN (weak change-vs-hold proxy
  measured: 59 vs 29 ticks).
- **FOMC context:** 147 archived statements 2011-01→2026-09; ±5' volume 8.2×,
  |1m ret| 6.2× on 6A — the US-rates common factor is LARGER than RBA's on
  this symbol; AF1 base-excludes FOMC statement days.
- DFF vintages (AF2): 16 year-end snapshots + latest; NOT a dense PIT series;
  vintage sensitivity (K2) declared. ABS CPI/Labour-Force historical dates
  NOT_RUN; China Caixin/NBS calendars NOT_RUN (**AF3's own K4 kills its base
  spec without a China calendar** — standing, unchanged).
- Sydney/Shanghai local-clock laws (AF1/AF3 hosts): Australia/Sydney
  DST-correct bucketing load-bearing; Asia/Shanghai for the China window.

## §5 Conditioning law — AF4 (tick-regime conditioning + 6J same-date control)

AF4 (HYPOTHESES_R2 §3) is the **T3 conditioning overlay**: hosts AF1/AF3,
**0 standalone identities**, era label = deterministic from the measured
2020-11-20/23 boundary (conventional anchor, disclosed). Law: host evaluable
days split era-1 vs era-2; **era-1 (231 sessions) is a DESCRIPTIVE-ONLY
stratum forever** — any fold structure fails the ≥5-per-fold floor
(pre-declared; K3 expected-failure stated a priori). Refutation conditions
carry verbatim: **K1** host anatomy identical across eras ⇒ overlay dead
(null = identity with host, NOT a host failure); **K2** 6J date-placebo
shifts too ⇒ date/crisis artifact, dead (6J tick measured CONSTANT —
increment GCD 500 int-nano in the 2020-03, 2023-01 and 2026-07 sampled eras,
`6j_identity.json`); **K3** era-1 too thin ⇒ stays descriptive forever unless
the owner extends the 2020 panel; **K4** discontinuity concentrated in a
single week ⇒ single-event artifact, dead. Secondary negative = 6E/6B once
D-2 step (iii) proves their tick constancy (**NOT_RUN — FXEB lane's step**).
Direction deliberately NOT asserted (two-sided overlay).

## §6 Frozen 26-ID contingency table (carried VERBATIM)

From `FUTURES-SIX-SCORED-GATE-PREP-20261004/budget/identity_tables.json`
(sha256 `1a96b8eafcc80c9ec549a34e06cb704db4a240af80bb6488ab2bbc46e6e9246a`),
symbol entry `6A` — reproduced verbatim, **do not expand**:

```json
{
 "symbol": "6A",
 "cap_status": "PB3 PARK => 0 budget (HYPOTHESES_R2 sec 8; CENSUS_FINAL sec 4); contingency lines only, all zero until PB3 lift + D8 (dispatch standing ruling)",
 "options": [
  {
   "id": "6A-CONTINGENCY",
   "description": "contingency-only table (NOT an option to sign today; activates only on PB3 lift + D8)",
   "total": 0,
   "total_if_ever_lifted": 26,
   "total_full_grid_if_ever_lifted": 52,
   "identities_by_category": {
    "AF1_minimal_core": 8,
    "AF1_controls": 3,
    "AF2_differential_overlay": 0,
    "AF3_minimal_core": 8,
    "AF3_controls": 3,
    "AF4_tick_regime_overlay": 0,
    "RMM_6A_contingency": 4,
    "controls_total_if_lifted": 6,
    "clock_only_shadow_arms_if_lifted": 2,
    "grid_factorization": "AF1 11 (8+3) + AF2 0 + AF3 11 (8+3) + AF4 0 + RMM 4 = 26 contingency (CENSUS_FINAL sec 1 AF rows; HYPOTHESES_R2 sec 8)"
   },
   "convention": "CONV_B_ESNQ_MINIMAL (6J6A lane)",
   "signature_text": "none today; on lift: JPY_AUD_HYPOTHESES AF1/AF3 sections + HYPOTHESES_R2 sec 3 AF4 + sec 2 RMM 6A leg",
   "signatures_required": [
    "owner PB3 lift + D8 (precondition for ANY nonzero count; today total = 0)"
   ],
   "gates": [
    "K0 thin-n kill PRE-REGISTERED, inherited (CENSUS_FINAL sec 1 AF1 row)",
    "AF2/AF4 = T3 overlays, 0 standalone identities (H-G law; HYPOTHESES_R2 sec 3/8)",
    "AF4 era-1 stratum 231 sessions - fold floor fails, descriptive forever unless panel extended (HYPOTHESES_R2 sec 3 K3)",
    "D-2 tick-era audit: era-aware 6A cost recomputation mandatory before any era-1 host scoring (HYPOTHESES_R2 sec 3 field 8, sec 5 D-2)",
    "RMM K2 power honesty transfers (modeled RT ~8.2bp 6A; era tick caveat $10/tick pre-2020-11-23)"
   ],
   "multiple_comparison_honesty": "0 today by ruling; 26 is the fully-lifted contingency ceiling, not an option.",
   "census_citations": [
    "CENSUS_FINAL sec 1 rows 'AF1 RBA decision-minute' (8+3=11), 'AF2 differential overlay' (0), 'AF3 bimodal structure' (8+3=11), 'PB3 PARK - contingency only'",
    "HYPOTHESES_R2 sec 8 ('6A: PB3 PARK => 0 budget; RMM-6A leg 4 IDs and AF4 0 IDs are CONTINGENCY-ONLY census lines')"
   ]
  }
 ]
}
```

Host-family minimums for reference (JPY_AUD_HYPOTHESES): **AF1** RBA
decision-minute (67 meetings 2020-01..2026-09; ±5' 9.0× volume / 4.8× |ret|;
**K0 thin-n kill PRE-REGISTERED** — fold floor likely fails at n=67, the
family may only ever be scored as a single-stratum cell or pooled eras);
**AF3** bimodal US+Sydney session structure (secondary peak 19:00–20:00 CT
1.19–1.27 bp; modal slot 11:30 Sydney 2.35% of daily volume; K4
Shanghai-window contamination kill without a China calendar); **AF2** and
**AF4** are T3 overlays at 0 identities. Power honesty carried: AF1 per-event
signal scale ±5' 4.35 bp < one RT (era-2 8.2 bp) — power-starved, K2 is the
EXPECTED outcome, stated as such.

## §7 Cost contract pointer

Full per-era ladders (S1/S2/S3 × 1.0/1.5/2.0) in `COST_CONTRACT_6J_6A.md`.
Labels bind everywhere: MODELED COST / UNDER REVIEW /
VERIFIED_VS_ACCOUNT=NOT_RUN; BBO NOT_RUN (D5); conservative fill law.

## §8 Status

**Today: 0 identities, 0 budget, 0 scheduled anything.** The activation
checklist (owner, not this lane): PB3 lift → D8 ratification (Option A
ratify the measured boundary / Option B demand the exchange document) → D9
cease-guard standard → fee A7 (D2) → ABS/China calendar acquisition decision
(AF3 K4) → then, and only then, this annex becomes a freeze candidate at a
future cycle's own gate. See `GAPS_AND_DECISIONS_6J_6A.md` P5-D5.

— End SPEC_6A_CONTINGENCY draft. 0 PnL, 0 scored runs, 0 network; write
surface confined to `research/control/FUTURES-5SYM-PRESCORED-20261005/fx_ja/**`.
