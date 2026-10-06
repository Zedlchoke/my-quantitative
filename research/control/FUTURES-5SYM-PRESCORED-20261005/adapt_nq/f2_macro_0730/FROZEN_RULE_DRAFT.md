# FROZEN_RULE_DRAFT — NQ-F2 MACRO-0730 (PROPOSED — never an approved freeze)

- Round **FUTURES-5SYM-PRESCORED-20261005**, wave-3, lane **ADAPT-NQ**, 2026-10-05.
- **STATUS: PROPOSED / DRAFT-PENDING-OWNER** — rule TEXT AS CODE ENFORCES IT for the
  synthetic-sandbox adapter in this directory. Not an approved freeze; no scored run; no
  real-data execution. Outcome-blind: SIGNALS + intended ORDER INTENT on synthetic fixtures only.
- Parents: `../../nq/SPEC_NQ.md` §4/§6/§7 · `../../nq/CALENDAR_PIT_POLICY_NQ.md` §5/§6 (BLS
  vintage law, D5 pin) · `../../nq/COST_CONTRACT_NQ.md` · `../../nq/IDENTITY_BUDGET_NQ.md` §1/§3 ·
  `../../hypo/CENSUS_5SYM.md` NQ-F2 row · `../../exec/RUNNER_COMPAT_NQ.md` RC-3.3/RC-3.4 ·
  `../../exec/symbol_contracts.json` (NQ row).
- Family: **NQ-F2 MACRO-0730-NQ** — 08:30-ET US print discharge into the pre-RTH thin book;
  mechanism M-NQ-MS (arms CONT vs REV on the 07:30-CT release-minute spike); K6 PASS both eras
  (scoring-era spike 4.51x; 2010-16 cell 4.39x; canceled-day falsifier clean; `NQ_K6_GATES.md` §5).
- Shared machinery (PIT reads, session law, H1..H5 exclusions, cost ladder, decision slots,
  fold/warmup, tick binding) is identical to `../f1_fomc_era/FROZEN_RULE_DRAFT.md` §1/§4/§6/§8/§9
  and lives in `../nq_common.py`; only family-specific law is restated here.

## 1. Observables and their timestamp-availability law (PIT)

| observable | definition as coded | knowable at (PIT) |
|---|---|---|
| BLS release stamps | injected `calendar.bls_vintage[]` = `{series, scheduled_date, known_by, status}` — keyed to the FIRST-PUBLISHED VINTAGE as of the decision date (`known_by`); **current-calendar inference FORBIDDEN** (standing ruling) — a row with `known_by > decision date` does NOT exist at decision time and never qualifies | a scheduled day qualifies only when `known_by <= scheduled_date` at decision time |
| anchor minute | **07:30 CT** (08:30 ET embargo) 1m bar of a qualifying release session | the anchor bar is consumed only after it closes (decision time 07:31 CT) |
| trigger sign | `sign(close(07:30 bar) - open(07:30 bar))`; `TRIGGER_WINDOW_BARS = 1` **[DRAFT-CODE]** | close of the anchor bar |
| canceled-expected stratum | rows `status == "canceled"` with `known_by <= D` (2025/2026 lapse anomalies: CPI Oct-ref Nov-13 CANCELED; Sep-ref Oct-15→24; Jan-26 ref Feb-11→**13**; recurs per CALENDAR §5) | at decision date D |
| ATR(20) | as F1 (prior 20 held sessions, strict past, held-contract-only) | as F1 |
| D5 pin | CPI **2026-02-13** (January-2026 release, embargo 08:30 a.m. ET; two independent BLS artifacts) MUST be present as a scheduled vintage row in ANY evaluation whose panel touches 2026 — absent ⇒ `REFUSED_D5_PIN_MISSING` (RC-3.4) | panel-span check at build time |

NOT available (inherited NOT_RUN, never conditioned on): surprise/consensus content; actual
publish latency. Price-sign designs only.

## 2. Signal definition

- **Universe (scored core)**: CPI release days in the **scoring era 2023-01-01..2026-09-30**
  (era confinement = the committed K6 anatomy gate, census F2 §3/§12 — a measured law, not an
  owner slot). EMPSIT/NFP days are observable strata; the CONV-B minimal core is CPI-only
  (IDENTITY_BUDGET §1: "minimal 8 (CPI, S2)").
- **Era gate**: any session outside the scoring era ⇒ signal is computed (descriptive anatomy)
  but order_intent refuses with `ERA_GATED` (pre-2016 measured-descriptive-only law).
- **tail / arms**: as F1 — tail = release-minute realized sign; `CONT` continuation vs `REV`
  reversal, both registered simultaneously.
- **controls**: `SHDW` non-release 07:30-CT clock (NC-6 class; single-seed seed 20261002,
  reading (a)); `ALW` always-on release-day clock (signal ignored); `FLAT` zero-trade anchor.
  Family-specific negatives carried by the owning docs: NC-6b canceled-day falsifier (the
  vintage-law-enabled negative — routed to `CANCELED_CONTROL`, never pooled into release
  cells) and the 2017-20 null era as the built-in family negative.

## 3. Entry / exit / holding horizon

- **D0 entry**: open of the 07:31-CT bar (first bar after the release minute; conservative fill
  law). **D30 entry**: open of the 08:01-CT bar.
- **exit**: TP = entry ± 2 x SL_distance / SL = entry ∓ 1.0 x ATR(20); same-bar TP/SL ⇒ **SL
  priority**; else mandatory flat at era-correct close (measured last 1m bar close). Intraday.

## 4. Session / event / calendar exclusions (fail-closed)

Identical to F1 §4 (`H1`/`H2_H3_2026_DUBIOUS`/`H4_EARLY_CLOSE_NOT_TRANSCRIBED`/
`H5_QUARTER_UNPROVEN`), with the family-specific additions:

| code | law |
|---|---|
| `FOMC_STANDING_OUTSIDE` | a CPI day that is also a base-FOMC statement day is EXCLUDED (standing-outside law applies to F2's base arms — contrast F1, whose universe is those days) |
| `CANCELED_CONTROL_STRATUM` | canceled-but-expected BLS days: separate negative-control stratum, never pooled into release cells (CALENDAR §5 lapse-anomaly law) |
| `ERA_GATED` | outside scoring era 2023-01-01..2026-09-30 (committed era confinement) |
| `REFUSED_D5_PIN_MISSING` | hard refusal when a 2026-spanning evaluation lacks the CPI 2026-02-13 pin |

## 5. Roll / cease-guard handling

As F1 §5 (held-contract-only fills; cache_v3 consumption gated by P5-NQ1; no chain construction
in the adapter; NEW-4 audit binds the run, not this family's signals).

## 6. Tick / multiplier / cost binding points

As F1 §6 verbatim (tick 0.25 pt / $5.00 / mult 20 / long_base_sign +1 from
`exec/symbol_contracts.json`; P5-NQ4 $2.50 refusal; Variant-A basis-only default while P5-NQ3
unsigned; MODELED-COST labels). Proportional-move honesty carried (census F2 §8): NQ needs a
larger per-trade move at half ES's per-tick dollar.

## 7. Identity enumeration (exact DRAFT IDs, quoted from IDENTITY_BUDGET_NQ.md §3)

NQ-F2 = 8 core + 3 controls = **minimal 11** (CONV-B; full grid 48 incl. CPI+NFP — the full
grid is NOT in the minimal set and binds only at an owner-signed ceiling):

```
FBNQ1-F2-CONT-UP-D0-S2   FBNQ1-F2-CONT-UP-D30-S2   FBNQ1-F2-CONT-DN-D0-S2   FBNQ1-F2-CONT-DN-D30-S2
FBNQ1-F2-REV-UP-D0-S2    FBNQ1-F2-REV-UP-D30-S2    FBNQ1-F2-REV-DN-D0-S2    FBNQ1-F2-REV-DN-D30-S2
FBNQ1-F2-SHDW-D0-S2      FBNQ1-F2-ALW-D0-S2        FBNQ1-F2-FLAT
```

Option binding (NQ-A/B/C) raises `RefusedPendingOwnerDecision("P5-NQ2")` while unsigned; NQ-D
refuses unconditionally (`EXPWITCH_DEAD_AT_GATE`).

## 8. Fold / warmup application

As F1 §8 (folds F1..F4; warmup = 252 held sessions at each fold head; folds are evaluation
multipliers, never identity multipliers; S1 sealed).

## 9. Owner-pending law — namespaced decision slots

As F1 §9 (P5-NQ1 real-data gate; P5-NQ2 option binding; P5-NQ3 Variant-B cost; P5-NQ4 tick
defect; P5-NQ6 2026 posture). F2 additionally consumes the D5 pin as a MEASURED law (not an
owner slot): its absence is a refuse, never a default.

— End FROZEN_RULE_DRAFT (PROPOSED). Nothing herein freezes, registers, scores, or ratifies.
