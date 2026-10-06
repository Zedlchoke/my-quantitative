# IDENTITY_BUDGET_NQ — trial-budget / ceiling OPTIONS for NQ (draft; option arithmetic only — recommends nothing)

- Round **FUTURES-5SYM-PRESCORED-20261005**, lane **NQ**, 2026-10-05. DRAFT-PENDING-OWNER.
- Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-5sym-prescored/prep`
  @ `ffed828f73fa19fa0ff4aee3ac1b441909a43940`. No commits, no registrations, no trial creation.
- **0 scored runs exist anywhere on NQ** (P-9 ledger law: `IDENTITY_TABLES.md` §7.1, sha256
  `750858ab…f6e6`). Every identity below is **hypothetical**; the observed NQ scored denominator
  is exactly **0**. This document registers nothing, sets no ceiling, signs nothing.
- **Source of every number**: `research/control/FUTURES-SIX-SCORED-GATE-PREP-20261004/budget/
  IDENTITY_TABLES.md` §4 (NQ ceiling options) — which itself derives from CENSUS_FINAL §1/§4 NQ
  rows and CANDIDATE_CENSUS §2/§4. This file re-states §4 with per-family decomposition, explicit
  DRAFT identity enumeration, and the gates each option still needs. **Convention: CONV-B**
  (per family: minimal-core + 3 scored controls, controls counted inside minimal; the clock-only
  shadow is 1 of the 3 under reading (a)). Machine mirror: `identity_budget_nq.json` (same lane).
- **Standing rulings restated (never reopened)**: no NQ numeric cap exists in standing rulings —
  an **explicit owner NQ ceiling signature is REQUIRED before any registration**
  (`IDENTITY_TABLES.md` §0.2, §4); placebo-budget ruling slot is EMPTY (§7.3 — C1-style
  single-seed/single-delay is the standing default; ≥100-seed expansion = separate owner ruling);
  ES cap 24 FROZEN is ES-only and untouched by this file.

## 1. Per-family decomposition (CONV-B; every row cites IDENTITY_TABLES §4)

| family | mechanisms (owning doc) | minimal | decomposition | full-grid (census) | family K6 status |
|---|---|---|---|---|---|
| **NQ-F1 FOMC-ERA** | M-NQ-CONT (persistence) + M-NQ-UNW (reversion) — `esnq_hypotheses.json::families[NQ-F1]`, sha256 `68e21c56…6605` | **11** | 8 core S2 (2 arms × 2 tails × 2 delays) + 3 controls | 24 | **K6 PASS** (h0_30 2.230× ≥ 2.0, m60_0 0.686× ≤ 0.85, n=85; `NQ_K6_GATES.md` §1, sha256 `364f0412…2781`) |
| **NQ-F2 MACRO-0730** | M-NQ-MS (arms CONT vs REV on the 07:30 CT thin-book spike; scored only in anatomy-reproducing eras) | **11** | 8 core S2 + 3 controls | 48 | **K6 PASS** (scoring era 2023-26 spike 4.51× ≥ 2.0; `NQ_K6_GATES.md` §5) |
| **NQ-F3 RUN-REV** | M-NQ-RR (post-k-run fade) vs M-NQ-RG (trend competitor) | **7** | 4 core S2 (2 arms × 2 tails, single delay) + 3 controls | 8 | Hard precondition **DONE (descriptive)**: full-era rebuild executable-in-principle on cache_v3 and executed as descriptive aggregates — ret series == `nq_held_daily_v3` (max diff 0.0, n=4,218); 2020 DD 34.12% == addendum figure; depleted 77→27 (`NQ_K6_GATES.md` §4; `nq_f3_rebuild_a1a2.json`, sha256 `3d25d69a…be07`). NOT a scored outcome |
| **NQ-F4 ROLLWK** | role_A_construction (standing NEW-4 law, 0 identities) + role_B_family (roll-week OVN thinning) | **7** | 4 core S2 + 3 controls (Role B only) | 4 (Role B) | Role-A audit law binding on all runs; Role-B K6 interaction = scored-side, **NOT_RUN** by law (`NQ_K6_GATES.md` §0.6 item 7) |
| **EXPWITCH NQ leg** | M-HEDGE-PERSIST / M-HEDGE-FADE (`HYPOTHESES_ESNQ_R3.md` §2, sha256 `9dfe7b12…d288`) | **+7** | 4 core + 3 controls | +12 | **DEAD-AT-GATE — F5-K6 part (ii) FAIL** (35/66 expiry Fridays carry RTH 15-min gaps, vendor-granularity era-wide; part (i) PASS 1.271/1.184 and 1.142/1.159 but the AND-law fails) — `NQ_K6_GATES.md` §2; excluded from every slate, not re-litigated |

Family minimal aggregates: F1+F2 = 22; +F3 = 29; +F4 = 36 (== the published NQ aggregate minimal,
CENSUS §4); +EXPWITCH = 43 (census-published ceiling-of-options — **no lawful path while the leg is
dead-at-gate**).

## 2. The options (option arithmetic ONLY — nothing here is recommended)

| option | identity | total (minimal) | full-grid equivalent | what the increment buys | extra gates beyond the common list (§4) |
|---|---|---|---|---|---|
| **NQ-A** | F1+F2 only (macro/event pair) | **22** = 11 + 11 | 72 = 24 + 48 | the two event-anchored families; carried package scores 11/11 (CANDIDATE_CENSUS §2 NQ row via IDENTITY_TABLES §4) | none beyond common |
| **NQ-B** | +F3 (run-rev) | **29** = 22 + 7 | 80 | NQ-F3; rebuild precondition now executable-in-principle on cache_v3 (DONE-descriptive; the family's own K6 scored gates still apply at its cycle) | none beyond common; F3 hard precondition is evidence-satisfied at the data layer (recorded fact, not a GO) |
| **NQ-C** | +F4 (rollwk Role B) | **36** = 29 + 7 | 84 | NQ-F4 Role B (4 core IDs); equals the published NQ aggregate minimal 36 | none beyond common; NEW-4 audit binds every run |
| **NQ-D** | +EXPWITCH NQ leg | **43** = 36 + 7 | 96 = 84 + 12 | expiration-Friday leg; MDE 38.7 bp — power-marginal, disclosed | **UNAVAILABLE in this packet**: the leg is DEAD-AT-GATE (P5-NQ5 would be the owner's data-plane route; until ruled, NQ-D has no lawful path and is NOT re-litigated here) |

Honesty lines (carried from `IDENTITY_TABLES.md` §4/§7.4, unchanged): NQ-C is the largest option
that still reconciles 1:1 with a published aggregate (36); NQ-D (43) is the census
ceiling-of-options, not a default, and is additionally gate-dead on its EXPWITCH leg; every option
above NQ-A weakens per-cell multiple-comparison protection in proportion to its cell count; **this
file presents arithmetic only and recommends nothing** — the trade-off is the owner's.

## 3. Explicit identity enumeration (DRAFT grammar — IDs are coded strings, frozen only at a future registration freeze)

Grammar: `FBNQ1-<FAM>-<ARM>-<TAIL>-<DELAY>-<TIER>`; controls `FBNQ1-<FAM>-SHDW-…`,
`FBNQ1-<FAM>-ALW-…`, `FBNQ1-<FAM>-FLAT`. Arms: `CONT`/`REV` (both registered simultaneously,
falsification-by-competitor); tails `UP`/`DN` (sign of the family's trigger-window move; the exact
trigger-window constant freezes from the owning family doc at registration — **[DRAFT-CODE]**);
delays `D0` = first 1m bar after the trigger (conservative fill = that bar's open), `D30` = 30 min
after; tier `S2` (the CONV-B core tier). Shadows: single-seed/single-delay (seed 20261002, PB1 C1
law), **reading (a)** — 1 of the 3 controls; under owner reading (b) each option total +1 per
family block. `FBNQ1` is a DRAFT cycle token; the registered cycle ID replaces it verbatim.

- **NQ-F1 (11)**: `FBNQ1-F1-CONT-UP-D0-S2` · `FBNQ1-F1-CONT-UP-D30-S2` · `FBNQ1-F1-CONT-DN-D0-S2`
  · `FBNQ1-F1-CONT-DN-D30-S2` · `FBNQ1-F1-REV-UP-D0-S2` · `FBNQ1-F1-REV-UP-D30-S2` ·
  `FBNQ1-F1-REV-DN-D0-S2` · `FBNQ1-F1-REV-DN-D30-S2` · controls `FBNQ1-F1-SHDW-D0-S2` ·
  `FBNQ1-F1-ALW-D0-S2` · `FBNQ1-F1-FLAT`
- **NQ-F2 (11)**: same 8+3 shape on the 07:30 CT anchor: `FBNQ1-F2-{CONT,REV}-{UP,DN}-{D0,D30}-S2`
  (8) + `FBNQ1-F2-SHDW-D0-S2` · `FBNQ1-F2-ALW-D0-S2` · `FBNQ1-F2-FLAT`
- **NQ-F3 (7)**: 4 core `FBNQ1-F3-{CONT,REV}-{UP,DN}-D0-S2` (single delay, S2, k-run conditioning
  on the held daily series per family law) + `FBNQ1-F3-SHDW-D0-S2` · `FBNQ1-F3-ALW-D0-S2` ·
  `FBNQ1-F3-FLAT`
- **NQ-F4 Role B (7)**: 4 core `FBNQ1-F4-{CONT,REV}-{UP,DN}-D0-S2` (roll-week vs matched
  non-roll-week conditioning) + `FBNQ1-F4-SHDW-D0-S2` · `FBNQ1-F4-ALW-D0-S2` · `FBNQ1-F4-FLAT`
- **EXPWITCH NQ leg (+7 census shape)**: **NOT MINTED** — the leg is dead-at-gate; no IDs exist in
  this packet for it, and none may be minted without the owner's P5-NQ5 data-plane ruling plus a
  fresh family-law path. (The census's +7/+12 lines stand as published history; they are not
  consumed here.)

Shadow arms per option (reading (a)): NQ-A 2, NQ-B 3, NQ-C 4 (`IDENTITY_TABLES.md` §7.2).

## 4. Gates every option still needs (common list — all OWNER-side, none executable by a lane)

1. **ADOPT-D9 Option A** — cease-guard standing law + NQ cache_v3 canonicalization
   (`D8_D9_DECISION_SHEET.md`, sha256 `b1d6079f…f8ae`). Until ruled: cache_v3 stays
   canonical-CANDIDATE; the freeze builder hard-refuses (`FREEZE_BUILDER_SPEC_NQ.md` §5).
2. **Owner NQ ceiling signature** — no cap exists anywhere (§0.2 law); the signature must name the
   option (A/B/C) and the **clock-shadow reading (a)/(b)** (`IDENTITY_TABLES.md` §2.1).
3. **Cost posture** — fee A7 executed AUTHORIZED_WITH_FINDINGS (0 HIGH/0 CRITICAL,
   `A7_FEE_REAUDIT.md`, sha256 `2c1095d6…11ad`); still open: the **D3 regulatory-basis ruling**
   (Variant A 2.25/side vs B 2.24/side — `COST_FREEZE_ERRATUM.md` §2; fail-closed default = A
   basis-only). No scored cell passes any cost gate before D3.
4. **Calendar-2026 residuals** — NQ 2026 product-code holiday deviations 0/10
   (BLOCKED_TRANSPORT re-confirmed 2026-10-04); advisory class 10/10 (Good Friday closed at CLASS
   level only, no Equity row) ⇒ 2026 dubious days stay EXCLUDE fail-closed unless the owner rules a
   bounded permitted-route extension (D12 posture; **P5-NQ6**).
5. **Placebo-budget ruling slot** (with any option): single-seed/single-delay stands by default;
   ≥100-seed expansion = explicit owner ruling (`IDENTITY_TABLES.md` §7.3).

Option-specific: none — every family gate that is measurable in PREP has been measured (F1 PASS,
F2 PASS, F3 precondition DONE-descriptive, F4 Role-B + EXPWITCH NQ leg are the two scored-side or
dead legs accounted above). The K6 verdicts adjudicate only their pre-declared conditions and
promote nothing.

## 5. What this file is NOT

Not a registration, not a schedule, not a GO, not a ceiling, not a placebo ruling, not a D9/D3
ruling, not a recommendation. It is the exact option set with explicit arithmetic and explicit
enumeration an owner may sign at a future registration. Machine mirror:
`identity_budget_nq.json` (same totals; validated same-file write).

— End IDENTITY_BUDGET_NQ. 0 PnL, 0 network, 0 scored trials; write surface confined to nq/** +
dispatch/handoff_NQ.json.
