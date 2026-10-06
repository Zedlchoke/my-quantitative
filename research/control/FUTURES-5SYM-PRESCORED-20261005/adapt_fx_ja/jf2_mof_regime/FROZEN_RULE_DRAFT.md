# FROZEN_RULE_DRAFT — 6J-JF2 MOF INTERVENTION-REGIME CONDITIONING (PROPOSED — never an approved freeze; MACHINERY ONLY)

- Round **FUTURES-5SYM-PRESCORED-20261005**, wave-3, lane **ADAPT-FXJA**, 2026-10-05.
- **STATUS: PROPOSED / DRAFT-PENDING-OWNER / MACHINERY-ONLY.** This adapter
  builds the disclosure-lag label machinery + host conditioning. **The JF2
  block cannot freeze** while the owner zone-threshold constant
  (**P5-HYPO-OD4**) is unfixed; `jf2_freeze_check()` refuses. No scored run,
  no real-data execution, no registration. Outcome-blind.
- Parents: `../../fx_ja/SPEC_6J.md` §6 (MOF ex-post-only + lag law; DC §1.4) ·
  `../../fx_ja/CALENDAR_PIT_POLICY_6J_6A.md` §3 ·
  `../../fx_ja/IDENTITY_BUDGET_6J.md` §2 JF2 block · `../../hypo/HYPO_GAPS.md`
  (P5-HYPO-OD4) · `../../hypo/CENSUS_5SYM.md` JF2 dossier.
- Family: **JF2 MOF Intervention-Regime Conditioning** — overlay; 0 own
  signal; 7 identities PER HOST (4 REG-conditioned cores + 3 controls),
  census row NEEDS_EVIDENCE (owner constant).

## 1. Observables and their timestamp-availability law (PIT)

| observable | definition as coded | knowable at (PIT) |
|---|---|---|
| MOF op dates + amounts | injected `calendar.mof_ops[]` = `{op_date, disclosure_date, amount_jpy_bn}` (synthetic mirror of the 386-row tidy; the 81-row `.bak` is FORBIDDEN evidence, ERRATUM M-1) | **only from the DISCLOSURE date** (~1 month monthly / quarterly daily detail) |
| regime label | REGIME when a VISIBLE op's op_date falls in the trailing **K=63 held sessions [PROVISIONAL]** of the session, else NON_REGIME | evaluated at `asof`; ops with `disclosure_date > asof` are INVISIBLE |
| same-day op knowledge | **FORBIDDEN** — `fc.require_same_day_op_visibility()` always refuses (`REFUSED_MOF_LAG_LAW_VIOLATION`) | never |
| pre-2022 null era | 2020-01..2022-08 must read NON_REGIME throughout (`fc.jf2_null_era_check`) — any op inside is a construction bug (C3″) | calendar audit |
| host signal | the JF1/JF3 host's own window law (this adapter delegates) | host law |

The 2026-07-30 window is NOT MOF-verified — price anatomy only, never merged
into the op set (SPEC_6J §6); the JF1 exclusion engine carries it as
`X_UNVERIFIED_OP_WINDOW_PRICE_ONLY`.

## 2. Signal definition

**NONE of its own** (census JF2 §5). The regime state SPLITS the host's
universes: REG-conditioned identities evaluate the host arm only where the
disclosure-lagged label = REGIME. Controls: `PLA` = C3′ disclosure-date label
shuffle (single-seed single-shuffle, `shuffle_disclosure_labels(seed=20261002)`;
≥100-seed expansions are separate owner rulings); `ALW` = host always-on inside
the disclosed regime; `CLK` = C3″ pre-2022 null-era clock (must be non-regime;
never trades — negative control).

## 3. Entry / exit / holding horizon

Inherited from the HOST (JF1 draft §3: window-close decision, D1/D30M entries,
TP 2×SL, SL 1.0×window-ATR(20), session-close time exit). JF2 adds no fill,
no exit, no holding law of its own. Host gates: JF2 sits behind the host's
exclusions + warmup + the 6J ceiling.

## 4. Exclusions

Host exclusions bind wholesale (JF1 draft §4). JF2-specific:
`REGIME_CONDITION_NOT_MET` (label NON_REGIME on a REG core — NO-TRADE, not an
exclusion of the host), `NULL_ERA_CONTAMINATED` (CLK construction-bug guard),
`SHUFFLED_REGIME_CONDITION_NOT_MET` (C3′ placebo non-regime).

## 5. Roll / cease-guard handling

Host law (JF1 draft §5) binds; nothing JF2-specific.

## 6. Tick / multiplier / cost binding points

Host binding (tick 5e-07 = $6.25, 12.5M JPY; MODELED COST labels; the
Tokyo-fill session floor). No JF2 cost layer exists (0 own fills).

## 7. Identity enumeration (exact DRAFT IDs, quoted from IDENTITY_BUDGET_6J.md §2 JF2 block — per host)

```
FB6J1-JF2-DRIFT-UP-REG-S2   FB6J1-JF2-DRIFT-DN-REG-S2
FB6J1-JF2-REV-UP-REG-S2     FB6J1-JF2-REV-DN-REG-S2
FB6J1-PLA-JF2               FB6J1-ALW-JF2               FB6J1-CLK-JF2
```

4 + 3 = **7 per host** (J-A: 1 host; J-B: both hosts). Views (0 IDs): K2
lag-law violation probe (same-day leak — the refusing helper), K4 era
concentration, the unverified 2026-07-30 price-only label.

## 8. Fold / warmup law

Host folds (SPEC_6J §8) + the K4 era-concentration view. The C3″ null era
(2020-01..2022-08) must show ZERO in-window ops — any "effect" there is a
construction bug, never a signal.

## 9. Owner-pending law — namespaced slots + fail-closed refusal

| slot | law | refusal behavior |
|---|---|---|
| `P5-HYPO-OD4` | JF2 zone-threshold constant ("distance-to-highest-USDJPY-acted-upon" zone) fixed a priori | `fc.jf2_zone_threshold()` refuses; `jf2_freeze_check()` refuses — the block cannot freeze |
| `P5-FXJA-D1` | 6J ceiling | real-data gate on every panel read (`require_synthetic`) |
| (carried) | MOF lag law | `fc.require_same_day_op_visibility()` always refuses |

Real-data adapter execution: **NOT_RUN**. This family stays MACHINERY-ONLY
this wave.
