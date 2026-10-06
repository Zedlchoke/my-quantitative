# FROZEN_RULE_DRAFT — FX-F3 US-8:30 Spillover (PROPOSED — never an approved freeze)

- Round **FUTURES-5SYM-PRESCORED-20261005**, wave-3, lane **ADAPT-FXEB**, 2026-10-05.
- **STATUS: PROPOSED / CONDITIONAL-ON-PB2-LIFT. PB2 HOLD stands** (`PB2_HOLD_RESTATE.md`
  sha256 `88386aa3…5a75b`). Rule TEXT AS CODE ENFORCES IT for `adapter.py`; NOT an
  approved freeze; no scored run, no real-data execution, no registration. Outcome-blind.
- Parents: `../../fx_eb/SPEC_6E.md` §5/§8/§9 · `../../fx_eb/SPEC_6B.md` §5/§8/§9 ·
  `../../fx_eb/CALENDAR_PIT_POLICY_6E_6B.md` §4 (BLS vintage law BLSV §5) ·
  `../../fx_eb/COST_CONTRACT_6E_6B.md` · `../../fx_eb/IDENTITY_BUDGET_6E_6B.md` §2/§4/§6 ·
  `../../hypo/CENSUS_5SYM.md` FX-F3 dossier · `../../exec/symbol_contracts.json` 6E/6B rows.
- Family: **FX-F3 US-8:30 Spillover** — US print into the still-open London book.
  Committed anatomy (descriptive): 07:30-CT median volume ×1.95 minute-prior, present
  1,732/1,746 sessions; the 06:30–08:00 CT block carries 15.58% of session RV on 12.5%
  of volume (6E). MDE ≈ 10.1 bp (6E) / 12.0 bp (6B) at pooled known-type n≈165 —
  detectable only for effects ~1.6–3× full modeled cost. Latency (schedule vs actual
  feed) NOT_RUN; release-type census beyond CPI+EMPSIT NOT_RUN. The 2025 canceled-expected
  days are natural negative-control strata (the information arrived as NON-arrival).

## 1. Observables and their timestamp-availability law (PIT)

| observable | definition as coded | knowable at (PIT) |
|---|---|---|
| BLS schedule vintage | injected `calendar.bls_vintage[]` = `{date, series: CPI\|EMPSIT\|<other>, status: scheduled\|canceled_expected, release_et: "08:30", vintage_asof, provenance}` mirroring `bls_dates.json` (204/204 rows 2010–2026, all 08:30 ET) | day level, 00:00 CT |
| vintage PIT law | a stamp is consumable at date D only if `vintage_asof <= D`; a postdated stamp ⇒ `PIT_VINTAGE_POSTDATED` (blocking) — current-calendar inference FORBIDDEN | as-of D |
| anchor bar | the **07:30 CT** bar (minute 450) of a known-type release session (08:30 ET = 07:30 CT; DST-safe: both US clocks shift together) | consumed only after it closes |
| release-minute sign | `sign(close(07:30) − close(07:29))` — the 1m close-to-close move | close of the 07:30 bar |
| spike ratio | 07:30 volume / median volume of the 6 prior bars (×1.95 class) — DESCRIPTIVE only | after the anchor closes |
| ATR(20) | prior-20 held-session ranges, strict past | at decision time |

## 2. Signal definition

- **Universe (base)**: CPI + EMPSIT-known days, pooled (the declared "US-hard-data 8:30
  class" design claim), vintage-correct as-of D.
- **tail**: `UP`/`DN` from the release-minute sign; 0 ⇒ `TRIGGER_FLAT`.
- **arms**: `SC` = continuation (sign carry), `SD` = fade. Both registered.
- **controls**: `C1-SHADOW` clock placebo on non-release weekdays; `C2-ALW` always-in at
  07:31 (clock vs information); `C3-ANCHOR` flat floor. Family-specific negatives:
  (a) weekday-matched non-event clock; (b) **expected-but-canceled 2025 days** (if the
  effect appears equally there it is a calendar artifact); (c) the unclassified-8:30
  stratum must show WEAKER sign-carry (never pooled into base).

## 3. Entry / exit / holding horizon

- **D0 = open of the 07:31 CT bar**; D1B = 07:32; D30M = D0 + 30 minutes (08:01).
  Conservative next-bar-open fill; BBO NOT_RUN (D5).
- **exit (whichever first)**: TP = entry ± 2 × SL_distance; SL = entry ∓ 1.0 × ATR(20);
  same-bar SL-priority; else mandatory flat at the 16:00 CT close. Intraday.

## 4. Session / event / calendar exclusions (fail-closed)

| code | law |
|---|---|
| `CANCELED_NEGATIVE_CONTROL` | expected-but-canceled days are NOT event days — negative-control stratum, no base trade |
| `UNCLASSIFIED_830_STRATUM` | non-CPI/EMPSIT 8:30 stamps (PPI/retail sales/GDP/claims — census NOT_RUN) — separately reportable stratum, NEVER pooled into base |
| `DOUBLE_EVENT_RECLASS_F2` | known-type day overlapping an FX-F2 day-set (ECB/MPC/FOMC) — base-excluded; if an "effect" survives only with central-bank overlap included it reclassifies to FX-F2 (rejection condition iii) |
| `NO_EVENT_STAMP` | no vintage stamp ⇒ no trade (clock-only control class lives outside the base) |
| `PIT_VINTAGE_POSTDATED` | stamp vintage as-of later than the decision date ⇒ refuse (vintage law) |
| `ANCHOR_BAR_ABSENT` / `TRIGGER_FLAT` / `ATR_WARMUP_INSUFFICIENT` | structural NO-TRADEs |
| `H6E_*` / `HOL_GRID_ABSENT_0OF42_DECLARED` / `QUARTER_NOT_OBTAINED_ROLL_ANCHOR` | shared holiday/quarter posture (F1 draft §4; 6B declaration never blocks) |

## 5. Roll / cease-guard handling

Held-contract-only fills; roll law law-pending (k=5 + cease-guard, D9-extension); no
additional roll exclusion on this family.

## 6. Tick / multiplier / cost binding

As F1 draft §6 (`fx_common.load_fx_contract`; the symbol's own tick grid and modeled RT
band; consumable cost refuses while P5-FXEB-OD6/OD7 unsigned; spike-minute fills are the
family's own subject — slippage-tier sensitivity is first-order, disclosed).

## 7. Identity enumeration (exact DRAFT IDs, quoted from IDENTITY_BUDGET_6E_6B.md §4.1/§4.2)

FX-F3 = 8 core + 3 controls = **11 per leg** (CONV-D; per-release-type strata n≈82 are
exploratory with MDE 14–17 bp — contingencies, never the base 11):

```
FXF3-6E-SC-UP-D0-S2  FXF3-6E-SC-UP-D1B-S2  FXF3-6E-SC-DN-D0-S2  FXF3-6E-SC-DN-D1B-S2
FXF3-6E-SD-UP-D0-S2  FXF3-6E-SD-UP-D1B-S2  FXF3-6E-SD-DN-D0-S2  FXF3-6E-SD-DN-D1B-S2
FXF3-6E-C1-SHADOW    FXF3-6E-C2-ALW        FXF3-6E-C3-ANCHOR
FXF3-6B-SC-UP-D0-S2  FXF3-6B-SC-UP-D1B-S2  FXF3-6B-SC-DN-D0-S2  FXF3-6B-SC-DN-D1B-S2
FXF3-6B-SD-UP-D0-S2  FXF3-6B-SD-UP-D1B-S2  FXF3-6B-SD-DN-D0-S2  FXF3-6B-SD-DN-D1B-S2
FXF3-6B-C1-SHADOW    FXF3-6B-C2-ALW        FXF3-6B-C3-ANCHOR
```

## 8. Fold / warmup application

As F1 draft §8 (shared fold boundaries; warmup FAMILY_60 default vs ES_252 switchable;
`bind_warmup_law` refuses on P5-FXEB-OD10). The BLS vintage regime 2025 is a declared
K-view on this family's own day-sets.

## 9. Owner-pending law — namespaced decision slots

Same slot table as the F1 draft §9 (OD1..OD11). F3-specific standing disclosures:
publish-latency NOT_RUN (declared limitation, owner-gated); release-type census beyond
CPI+EMPSIT NOT_RUN.

## 10. K-views

Era split 2020-22 vs 2023-26; BLS vintage regime 2025; DST-mismatch split; 6B
London-share-drift split (drift directly modulates this family's receiving book).

— End FROZEN_RULE_DRAFT (PROPOSED). Nothing herein freezes, registers, scores, or ratifies.
