# FROZEN_RULE_DRAFT — NQ-F3 RUN-REV-NQ (PROPOSED — never an approved freeze)

- Round **FUTURES-5SYM-PRESCORED-20261005**, wave-3, lane **ADAPT-NQ**, 2026-10-05.
- **STATUS: PROPOSED / DRAFT-PENDING-OWNER** — rule TEXT AS CODE ENFORCES IT for the
  synthetic-sandbox adapter in this directory. Not an approved freeze; no scored run; outcome-blind
  (SIGNALS + intended ORDER INTENT on synthetic fixtures only).
- Parents: `../../nq/SPEC_NQ.md` §6/§7 · `../../nq/IDENTITY_BUDGET_NQ.md` §1/§3 ·
  `../../hypo/CENSUS_5SYM.md` NQ-F3 row · `../../exec/RUNNER_COMPAT_NQ.md` RC-2.5/RC-6.2 ·
  `../../exec/symbol_contracts.json` (NQ row).
- Family: **NQ-F3 RUN-REV-NQ** — horizon-dependent daily-close reversion on the repaired chain;
  mechanisms M-NQ-RR (post-k-run fade) vs M-NQ-RG (trend competitor); hard precondition DONE
  (descriptive): the full-era rebuild harness is the committed K6 machinery
  `research/control/FUTURES-K6GATE-PREP-20261004/nq/k6_compute_m34.py` +
  `nq_f3_rebuild_a1a2.json` (rebuilt ret series == `nq_held_daily_v3`, max diff 0.0, n=4,218;
  2020 DD 34.12%; depleted 77→27) — **referenced, NOT duplicated** by this adapter.
- Shared machinery (PIT reads, session law, H1..H5 + FOMC exclusions, cost ladder, decision
  slots, fold/warmup, tick binding) = `../f1_fomc_era/FROZEN_RULE_DRAFT.md` §4/§6/§8/§9 via
  `../nq_common.py`; only family-specific law is restated.

## 1. Observables and their timestamp-availability law (PIT)

| observable | definition as coded | knowable at (PIT) |
|---|---|---|
| held daily close series | era-correct held-session closes from the injected panel aggregates (`sessions[].close`, held-contract-only — the `nq_held_daily_v3` class) | session t's close is knowable at t's measured session end |
| same-sign run length | consecutive same-sign close-to-close returns ending at session t (`run_len(t)`) | at t's session close |
| trigger | `run_len(t) >= K and run_len(t-1) < K` (first crossing; K = **5** [DRAFT-CODE/PROVISIONAL per census F3 §5]) | t's session close |
| roll switch dates | injected `panel.rolls[]` (the k=5 volume-crossover chain law, decided t-1, held from t) | chain data |

Nothing external required (census F3 §4). The daily→session mapping remains INFERENCE-grade
(D2=2 carried) — disclosed, never upgraded by this adapter.

## 2. Signal definition

- **Universe**: all held sessions; the run census runs on the full held series.
- **tail**: `UP` = 5-consecutive-UP-close run; `DN` = 5-consecutive-DOWN-close run.
- **arms**: `CONT` (trend competitor M-NQ-RG: enter in the run direction) vs `REV`
  (M-NQ-RR: enter opposite), both registered simultaneously; single delay **D0**.
- **controls**: `SHDW` clock-only (seed 20261002, reading (a), entry on no-signal sessions);
  `ALW` always-in (enter every eligible session open, direction +1); `FLAT` zero trades.
  NC-4 no-run days / NC-4b sign-shuffled labels / NC-7 ES-contrast are owning-doc negatives
  carried at the family layer (not adapter arms).

## 3. Entry / exit / holding horizon (multi-day, T4 class)

- **entry**: OPEN of the first held session after the trigger session (next session open,
  aggregate open on the 0.25 tick grid; conservative fill).
- **exit**: CLOSE of the entry session + **K held sessions** (fixed k-day horizon,
  `EXIT_HORIZON_SESSIONS = 5` [DRAFT-CODE]); no TP/SL in the minimal core (per family doc:
  "fixed k-day horizon or TP/SL" — the minimal-core law codes the fixed horizon).
- **roll/cease-guard handling (chain law)**: an intent whose holding window (entry, exit]
  contains a roll switch date, or whose entry/exit session IS a switch session, is dropped with
  `ROLL_CROSS_UNADJUSTED` — the corr-0.999 phantom-drift law requires spread-adjusted
  switch-day returns (chain data; the adapter performs no spread adjustment and refuses rather
  than fabricating one). Cease-guard consumption is P5-NQ1-gated (no real chain in PREP).

## 4. Session / event / calendar exclusions (fail-closed)

`H1`/`H2_H3_2026_DUBIOUS`/`H4_EARLY_CLOSE_NOT_TRANSCRIBED`/`H5_QUARTER_UNPROVEN` +
`FOMC_STANDING_OUTSIDE` applied to the ENTRY session (base-arm day-level law). Plus:

| code | law |
|---|---|
| `ROLL_CROSS_UNADJUSTED` | §3 roll law |
| `HORIZON_BEYOND_PANEL` | exit session does not exist in the injected panel |
| `K3_2020_CONCENTRATION` | not an exclusion — the pre-declared stratum flag on any intent whose trigger sits in 2020-03..04 (G6 law) |
| `ATR_WARMUP_INSUFFICIENT` | fewer than K+1 prior closes (no run can be measured) |

## 5. Tick / multiplier / cost binding

As F1 §6 (tick 0.25 / $5.00 / mult 20; Variant-A basis-only default while P5-NQ3 unsigned;
MODELED-COST labels). Multi-day holding ⇒ one RT per round trip — no intra-horizon
mark-to-model claims (census F3 §8).

## 6. Identity enumeration (exact DRAFT IDs, quoted from IDENTITY_BUDGET_NQ.md §3)

NQ-F3 = 4 core + 3 controls = **minimal 7** (CONV-B; full grid 8, k ∈ {3,5} — only k=5 is in
the minimal core):

```
FBNQ1-F3-CONT-UP-D0-S2   FBNQ1-F3-CONT-DN-D0-S2   FBNQ1-F3-REV-UP-D0-S2   FBNQ1-F3-REV-DN-D0-S2
FBNQ1-F3-SHDW-D0-S2      FBNQ1-F3-ALW-D0-S2       FBNQ1-F3-FLAT
```

Option binding raises `RefusedPendingOwnerDecision("P5-NQ2")` while unsigned; NQ-D refuses
unconditionally (`EXPWITCH_DEAD_AT_GATE`).

## 7. Fold / warmup application

As F1 §8. The F3 rebuild precondition (meas_nq harness) supplies the descriptive substrate;
folds F1..F4 map onto the rebuilt series at any future freeze; warmup = 252 held sessions at
each fold head (RC-5.2), never contributing scored statistics.

## 8. Owner-pending law — decision slots

As F1 §9 (P5-NQ1 real-chain gate — the rebuilt v3 series itself is D9-blocked for real
consumption; P5-NQ2 ceiling; P5-NQ3 cost basis; P5-NQ4 tick defect; P5-NQ5 EXPWITCH refusal;
P5-NQ6 2026 posture).

— End FROZEN_RULE_DRAFT (PROPOSED). Nothing herein freezes, registers, scores, or ratifies.
