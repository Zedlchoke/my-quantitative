# IDENTITY_BUDGET_6E_6B — FX-A 44 / FX-B 66 / FX-C 96 (CONV-D) decomposed PER SYMBOL

- Round **FUTURES-5SYM-PRESCORED-20261005**, lane **FXEB**, 2026-10-05. PREP-only:
  **0 PnL, 0 scored runs, 0 registrations. Every identity below is hypothetical; the
  observed scored-trial denominator on 6E/6B is exactly 0** (IDENTITY_TABLES §7.1).
- **CONDITIONAL-ON-PB2-LIFT DRAFT — PB2 HOLD (6E/6B) stands.** Every option below
  exists ONLY if the owner lifts PB2; that lift is NOT treated as given and is not
  requested here. Machine mirror: `IDENTITY_BUDGET_6E_6B.json` (same totals).
- Source of the option set: `FUTURES-SIX-SCORED-GATE-PREP-20261004/budget/IDENTITY_TABLES.md`
  §6 (sha256 `750858ab…f6e6`) — FX-A 44 / FX-B 66 / FX-C 96 CONV-D, census-native
  (CONV-C) disclosure 32/48/72 **never summed with CONV-D**. This document decomposes
  those totals PER SYMBOL with explicit ID strings and the signatures each option
  requires. No new identity class is invented; the only new enumeration is the
  per-symbol ID-string list (DRAFT naming, fixed at any future registration freeze).

## 1. Conventions (restated, binding)

- **CONV-D** (proposed conversion, requires owner signature — IDENTITY_TABLES §2/§6):
  per family per leg = **8 minimal-core S2** (2 arms × 2 tails × 2 delays @ tier S2)
  + **3 scored controls** (C1-class clock-only shadow single-seed/single-delay per PB1
  C1 law; C2 always-on; C3 anchor) = **11**.
- **CONV-C** (FX census-native): 0 scored controls counted; full-grid 36/leg/family
  (arms 2 × tails 2 × delays 3 × tiers 3); totals 32/48/72. **Never summed with CONV-D
  or with any other lane** (CENSUS_FINAL §1/§5 hygiene).
- Clock-shadow reading **(a)** (shadow is 1 of the 3 controls) is the declared default;
  reading **(b)** (shadow additive, +1 per family block) is the owner alternative — the
  FX ceiling signature MUST name (a) or (b) (IDENTITY_TABLES §2.1). All totals below use
  reading (a).
- Census unit (CONV-C full-grid law): 1 identity = (family, symbol, arm, tail, delay,
  tier) (`fx_census_recount.json`, sha256 `bf2f5e7d…4bbcc`).

## 2. Families and legs (per-symbol)

| family | 6E leg | 6B leg | day-set relation |
|---|---|---|---|
| FX-F2 Policy-Decision Resolution | FOMC anchor (13:00 CT; ×17.24 vol spike) + ECB stratum | MPC anchor (12:00 London, minute-720; ×18.7) + FOMC stratum | exactly F1's excluded days |
| FX-F3 US-8:30 Spillover | CPI/EMPSIT-known days | same stamps on 6B | the ×1.95 spike inside F1's trigger window |
| FX-F1 London-Range Absorption | census-gated ≥500: **PASS 6E 1,362** | **PASS 6B 1,342** | base excludes event days |
| FX-F4 Globex Reopen Gap + RMM Role-B | weekday reopens n=1,282 (gap std 0.0304%; Sunday 317 stratum) | weekday reopens n=1,283 (gap std 0.0400% — MEASURED; holiday gate stands) | evening-open segment |

F5/F6 are overlays (0 standalone IDs; ×2 regimes on ONE chosen host leg as declared
contingency) — they carry NO option-total cells below, matching IDENTITY_TABLES §6.

## 3. Per-symbol CONV-D decomposition

Per family per leg = 11 CONV-D ⇒ per symbol per family-block = 11. RMM Role-B adds
**4 IDs/leg** (HYPOTHESES_R2 §8; legality requires the owner **DC §1.3 boundary
ruling** — HYPOTHESES_R2 §2/§9.7; carried, never self-ratified).

| option | 6E subtotal | 6B subtotal | total | arithmetic |
|---|---|---|---|---|
| **FX-A** (F2+F3) | **22** = (8+3)×2 | **22** = (8+3)×2 | **44** | 32 core + 12 controls |
| **FX-B** (+F1) | **33** = (8+3)×3 | **33** | **66** | 48 core + 18 controls |
| **FX-C** (+F4 + RMM) | **48** = (8+3)×4 + 4 RMM | **48** | **96** | 64 core + 24 controls + 8 RMM |

Census-native disclosure (CONV-C, never summed): 4-family core 36×4×2 = 288 full-grid;
CONV-C option-equivalent cores 32/48/72 (8×2/8×3/8×4 family-legs).

## 4. Explicit per-symbol identity enumeration (ID strings — DRAFT naming)

ID grammar (fixed at freeze): `FXF<n>-<SYM>-<ARM>-<TAIL>-<DELAY>-<TIER>[-<STRAatum>]`
with ARM ∈ {RC,RD} for F2 (resolution-drift vs spike-reversal), {SC,SD} for F3 (spill
continuation vs fade), {HC,HD} for F1 (H-C continuation vs H-D fade), {GC,GD} for F4;
TAIL ∈ {UP,DN}; DELAY ∈ {D0,D1B,D30M}; TIER ∈ {S1,S2,S3}. Controls:
`FXF<n>-<SYM>-C1-SHADOW`, `-C2-ALW`, `-C3-ANCHOR`. RMM: `FXRMM-<SYM>-RB<k>` k=1..4.

**Core-S2 delay-slot draft** [DRAFT — the CONV-D signature must fix it, P5-OD3]:
the 8-core takes 2 of the 3 delay slots at S2. Default draft = **{D0, D1B}** (the
spike-decay artifact pair: fills sit inside the decaying ×17.24/×18.7 volume spike, so
the +1-bar variant is the first-order microstructure detector, `FX_HYPOTHESES.md` §2.5);
D30M becomes the declared full-grid extension. Alternative = {D0, D30M} (ES P-A shape).
Nothing is scored either way today.

### 4.1 6E (examples show the pattern; the full string set is the cross-product)

- FX-F2-6E core 8: `FXF2-6E-{RC,RD}-{UP,DN}-{D0,D1B}-S2` (8) + controls
  `FXF2-6E-C1-SHADOW`, `FXF2-6E-C2-ALW`, `FXF2-6E-C3-ANCHOR` (3) = 11.
  ECB-day stratum (+8 core-class cells at S2-D0/D1B in full-grid) = declared contingency,
  NOT in the 11.
- FX-F3-6E core 8: `FXF3-6E-{SC,SD}-{UP,DN}-{D0,D1B}-S2` + 3 controls = 11.
- FX-F1-6E core 8: `FXF1-6E-{HC,HD}-{UP,DN}-{D0,D1B}-S2` + 3 controls = 11 (census gate
  PASS precondition met; court §b1.1 anatomy NOT_RUN still gates any scored spec).
- FX-F4-6E core 8: `FXF4-6E-{GC,GD}-{UP,DN}-{D0,D1B}-S2` + 3 controls = 11; Sunday
  stratum (`-SUN`) = contingency; RMM `FXRMM-6E-RB1..RB4` (+4, DC §1.3 ruling).
- 6E subtotals: FX-A 22, FX-B 33, FX-C 48 (incl. RMM).

### 4.2 6B

- FX-F2-6B core 8: `FXF2-6B-{RC,RD}-{UP,DN}-{D0,D1B}-S2` + 3 controls = 11 (MPC base;
  change/hold strata descriptive, pooled base).
- FX-F3-6B core 8: `FXF3-6B-{SC,SD}-{UP,DN}-{D0,D1B}-S2` + 3 controls = 11.
- FX-F1-6B core 8: `FXF1-6B-{HC,HD}-{UP,DN}-{D0,D1B}-S2` + 3 controls = 11 (census gate
  PASS; London-drift split is a built-in falsifier view).
- FX-F4-6B core 8: `FXF4-6B-{GC,GD}-{UP,DN}-{D0,D1B}-S2` + 3 controls = 11 — **carries
  the standing holiday-gate block (0/42 grid)** + RMM `FXRMM-6B-RB1..RB4` (+4, DC §1.3).
- 6B subtotals: FX-A 22, FX-B 33, FX-C 48 (incl. RMM).

## 5. Signatures each option requires (ALL of them, every option)

1. **PB2-lift signature** (owner; dispatch `pb2_pb3` absolute; PB2_HOLD_RESTATE). Not
   given; not assumed.
2. **FX ceiling signature** (no cap exists — CENSUS_FINAL §4) **naming CONV-D vs
   census-native** and the option (FX-A/B/C).
3. **CONV-D convention signature** (the owner signs the convention, not just the number
   — IDENTITY_TABLES §6), including the core delay-slot assignment (P5-OD3).
4. **Clock-shadow reading (a)/(b)** named in the ceiling signature (§2.1).
5. FX-C only: **owner DC §1.3 boundary ruling** for RMM Role-B legality (carried from
   HYPOTHESES_R2 §2/§9.7).
6. Placebo-budget ruling slot: **EMPTY** — single-seed/single-delay C1 is the standing
   default; any ≥100-seed expansion is a separate owner ruling (IDENTITY_TABLES §7.3).

## 6. Gates per family (post-lift, before any scored cell)

- FX-F1: court census ≥500 PASS both (K6GATE M1); power floor vs cost; ancestry court;
  **1m trigger-time anatomy (court §b1.1) NOT_RUN — required BEFORE any scored
  registration**; exit-horizon decomposition (court §b1.4) NOT_RUN.
- FX-F2: power honesty MDE ≈17.0 bp (6E, n=58) / ≈20.6 bp (6B, n=56) vs cost floors
  3.6–6.3 / 6.3–11.2 bp — power-starved by construction; vintage law; latency NOT_RUN.
- FX-F3: MDE ≈10.1/12.0 bp at pooled known-type n≈165; BLS vintage regime 2025 binding;
  full 8:30 release-type census NOT_RUN (base restricted to CPI+EMPSIT).
- FX-F4: 6E borderline cost viability; **6B leg cost-weakest (RT 6.3–11.2 bp) with the
  holiday stand-aside BLOCKED on the 0/42 grid**; threshold value NOT_RUN.
- RMM (FX-C): DC §1.3 ruling; its C1 ≥100-seed layer sits OUTSIDE the +4 (unbudgeted
  pending the placebo ruling).

## 7. Honesty lines (restated from IDENTITY_TABLES §6, unchanged)

The four-family native core sums to 288 (+8 RMM = 296) inside the census's uncapped
≈648 all-in aggregate; every FX option buys identities that are power-marginal against
the modeled cost floors — **the identity count is the LEAST of the FX costs**. No option
is recommended here; the owner owns the trade-off. This document registers nothing.

— End IDENTITY_BUDGET_6E_6B.md.
