# FROZEN_RULE_DRAFT — 6J RMM Role-B leg, M-COMPRESS (PROPOSED — never an approved freeze; MACHINERY ONLY, J-C only)

- Round **FUTURES-5SYM-PRESCORED-20261005**, wave-3, lane **ADAPT-FXJA**, 2026-10-05.
- **STATUS: PROPOSED / DRAFT-PENDING-OWNER / MACHINERY-ONLY.** The RMM 6J leg
  exists ONLY inside option **J-C**, which requires the owner 6J ceiling
  (**P5-FXJA-D1**) AND the **DC §1.3 boundary ruling** (**P5-FXJA-D2**) —
  never self-ratified. Any Role-B trade intent refuses (even on synthetic
  fixtures). No scored run, no real-data execution, no registration.
- Parents: `../../fx_ja/SPEC_6J.md` §5 (chain/cease-guard/2022-09-20 law case) ·
  `../../hypo/CENSUS_5SYM.md` RMM dossier (Role-A ledger CLOSED 19 abrupt /
  8 gradual; Role-B NEEDS_EVIDENCE; K1–K7 kill set) ·
  `../../fx_ja/IDENTITY_BUDGET_6J.md` §2 RMM block ·
  `../../fx_ja/GAPS_AND_DECISIONS_6J_6A.md` §(b) P5-FXJA-D1/D2.
- Family: **RMM Roll-Migration Mode, 6J leg** — does a COMPRESSED (cease-guard)
  quarterly migration leave a mode-dependent post-switch pressure signature
  (M-COMPRESS-REV vs M-COMPRESS-CONT) that gradual (crossover) rolls do NOT
  show? The mode × post-switch-drift interaction has NEVER been measured —
  that measurement is the family's named missing evidence (anatomy-first gate
  before any Role-B freeze).

## 1. Observables and their timestamp-availability law (PIT)

| observable | definition as coded | knowable at (PIT) |
|---|---|---|
| switch tables | injected `roll_rows[]` (synthetic mirror of the measured 27-roll chain; `rmm_mode_ledger.json` 19/8) | strict past at each switch close |
| mode label | `cease_guard_no_bars` → ABRUPT; `k5_crossover` → GRADUAL (`fc.build_roll_chain`) | decided at close t, **effective t+1** (DC §1.3 timing law, verbatim) |
| cease-guard | held contract dead (< 25% bars or ≈0 volume) while the rule has not switched ⇒ force-switch at that session's close | at the close of the dead session |
| switch-session move | signed move on the RECEIVING contract, 6J price terms | close of the switch session |
| event-stacking | switch session overlapping a BoJ/FOMC/ECB/MPC decision window ⇒ `X_EVENT_STACKING_CENTRAL_BANK` EXCLUDE | calendar knowledge |

**QUOTE-DIRECTION LAW:** 6J UP = yen STRONG (orientation proof sha
`6ca0baeb…`); the switch-move tail and both arm signs are in 6J price terms.

## 2. Signal definition (machinery — never activated)

Signal day = switch session t. Arms `MCOMPRESS-REV` (reversion) and
`MCOMPRESS-CONT` (continuation) of the receiving contract's switch-session
move, both tails. Universe = the 27 measured 6J rolls. **EXCLUDE**: event-
stacked switch sessions; the extremal abrupt stratum (6J 2022-09-20 + the two
6A dates) is descriptive-only, n=3 fails any ≥5-per-fold floor (pre-declared,
`fc.fold_floor_check(3)`). Family-specific negative = the gradual-mode rolls
(K3). Chain law: scoring MUST use the explicit cease-guard variant chain;
switch-day returns spread-adjusted; chain choice must not flip any sign
(RMM K6(a) — asserted in the chain builder).

## 3. Entry / exit / holding horizon (law sketch — REFUSED while unsigned)

Entry = open of the first 1m bar after t close (conservative fill); delays
D1/D30M; TP 2×SL, SL 1.0×ATR(20); time exit = switch+K sessions (K=5
[PROVISIONAL]). **`order_intent` raises `RefusedPendingOwnerDecision` on
P5-FXJA-D1 (ceiling first) and then P5-FXJA-D2 (DC §1.3) — including on
synthetic panels. The C1 block-shuffle placebo layer sits OUTSIDE the +4
(≥100 seeds would be a separate owner ruling).**

## 4. Exclusions

`X_EVENT_STACKING_CENTRAL_BANK` · `X_ROLL_CEASE_GUARD` (the 2022-09-20
baseline held-dead day) · host calendar inventory (`H_QUARTER_UNPROVEN`,
`H_HOLIDAY_TIMES_NOT_OBTAINED`, `H_PARTIAL_TAIL`) · `SWITCH_SESSION_FLAT`
(undefined tail) · `NO_RECEIVING_CONTRACT_BARS_UPTO_ASOF`.

## 5. Roll / cease-guard law (the core deliverable of this fixture)

- **Baseline k=5** keeps the 09-20 row (held=6JU2) but the bar-level chain
  drops the session (U2: zero bars, 0 lots) — the artifact sits INSIDE the
  September-2022 intervention week, flagged, never a base stratum.
- **Explicit cease-guard variant** force-switches U2→6JZ2 at the 09-20 close,
  **effective 09-21** ("decided at close t, effective t+1" verbatim).
- `fc.measure_and_disclose_guard_violations` emits the disclosure record the
  ADOPT-D9 law-pending default requires (measure and disclose FIRST).
- 6A carries 2 baseline violations (2024-12-17, 2026-06-16) ⇒ the explicit
  cease-guard variant is the MANDATORY chain-builder there (SPEC_6A §3).

## 6. Tick / multiplier / cost binding points

Host 6J binding (tick 5e-07 = $6.25; 12.5M JPY; MODELED COST labels; RT band
8.5–14.7 bp; ramp-session fills carry no claim beyond the tier triple — BBO
NOT_RUN). RMM K2 power honesty: MDE ≈ 12.5 bp-class at n≈108 pooled FX events
— power-marginal by construction; a null there is the pre-registered K2 death.

## 7. Identity enumeration (exact DRAFT IDs, quoted from IDENTITY_BUDGET_6J.md §2 RMM block — J-C only, +4)

```
FB6J1-RMM-MCOMPRESS-REV-D1    FB6J1-RMM-MCOMPRESS-REV-D30M
FB6J1-RMM-MCOMPRESS-CONT-D1   FB6J1-RMM-MCOMPRESS-CONT-D30M
```

Controls INSIDE the +4: none (gradual rolls are the family negative; the
extremal stratum is descriptive-only). C1 block-shuffle ≥100-seed layer:
OUTSIDE the +4, owner ruling if ever budgeted.

## 8. Fold / warmup law

Event-clock universe (27 switches), not session folds; extremal stratum
pre-declared fold-floor failure; K5 era-concentration is a view (0 IDs).

## 9. Owner-pending law — namespaced slots + fail-closed refusal

| slot | law | refusal behavior |
|---|---|---|
| `P5-FXJA-D1` | owner 6J ceiling (no cap exists) | `bind_option_6j("J-C")` refuses; `order_intent` refuses FIRST on D1 |
| `P5-FXJA-D2` | DC §1.3 boundary ruling (iff J-C) | `order_intent` refuses — even on synthetic fixtures (never self-ratified) |

Real-data adapter execution: **NOT_RUN**. Interaction measurement
(mode × post-switch-drift): **NOT_RUN** — the named missing evidence.
