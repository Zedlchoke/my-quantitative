# IDENTITY_BUDGET_6J — trial-budget ceiling DRAFT for owner signature (lane FXJA)

- Round **FUTURES-5SYM-PRESCORED-20261005**, lane **FXJA**, 2026-10-05 UTC.
- Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-5sym-prescored/prep`
  @ base `ffed828f73fa19fa0ff4aee3ac1b441909a43940`. Class: PREP budget draft.
  **0 PnL, 0 scored runs, 0 registrations, 0 network. This document registers
  nothing, sets no ceiling, and executes nothing** — it decomposes the
  committed option set so the owner signature can be exact.
- Primary source: `FUTURES-SIX-SCORED-GATE-PREP-20261004/budget/IDENTITY_TABLES.md`
  §5 (sha256 `750858ab60b8930a7ffd94f9c451c56f770d3efcfd43d2f6db9ad5438b15f6e6`)
  + machine mirror `budget/identity_tables.json` (sha256 `1a96b8eafcc80c9ec549a34e06cb704db4a240af80bb6488ab2bbc46e6e9246a`).
  Convention: **CONV-B (ESNQ minimal)** — per family, minimal = 8 minimal-core
  S2 identities + **3 scored controls inside the total** (IDENTITY_TABLES §2).
  Machine mirror of THIS document: `IDENTITY_BUDGET_6J.json` (same totals).

## §0 Standing rulings restated (never reopened)

1. **No 6J cap exists anywhere** (CENSUS_FINAL §4) — an explicit **owner
   ceiling signature is REQUIRED before any 6J registration**. The dispatch
   instruction 2026-10-05 (PREP authorization) is NOT that signature.
2. **6A is PB3 PARK** — no 6J option below touches 6A; the 6A contingency
   lives in `SPEC_6A_CONTINGENCY.md` §6 (frozen 26-ID table, not expanded).
3. **Placebo-budget ruling slot EMPTY**: C1-style single-seed/single-delay
   (ES precedent, SPEC_PB1_ES §6 C1 row, seed 20261002 at that cycle) is the
   standing default; any ≥100-seed expansion is an owner ruling
   (IDENTITY_TABLES §7.3) — never silently added here.
4. **Scored trials to date on 6J: 0** (observed-search disclosure,
   IDENTITY_TABLES §7.1). Every identity below is hypothetical.

## §1 Option set (committed totals, reproduced exactly)

| option | total (minimal) | composition | what the increment buys |
|---|---|---|---|
| **J-A** | **29** | JF1 11 + JF3 11 + JF2 7 (single host) | the three committed 6J families, JF2 conditioned on one host |
| **J-B** | **36** | JF1 11 + JF3 11 + JF2 7 × 2 (both hosts) | + JF2 second host block |
| **J-C** | **33** on J-A / **40** on J-B | + **4 RMM Role-B IDs** per HYPOTHESES_R2 §8 (NQ-F4 Role-B convention, additive law) | roll-migration-mode leg; legality requires the **owner DC §1.3 boundary ruling** (declared, not self-ratified) |

Full-grid context (not option totals, census-internal tension flagged for the
owner — no option uses it): census aggregate row says "96 full (24×4)" while
the family rows decompose to 24+8+24 = 56 (IDENTITY_TABLES §5) — the tension
is disclosed, never resolved silently.

## §2 Explicit identity enumeration (CONV-B; ID-string skeletons frozen at registration)

Control convention inside every family block (3 scored controls, reading (a)):
`PLA` = C1-class clock-only shadow, single-seed/single-delay (1 of the 3);
`ALW` = C2 always-on; `CLK` = C3 family-specific negative clock. Additional
C3′/C3″/C4 cells are **evaluation views, never identities** (fold law).

**JF1 block — 11** (BoJ MPM window; anchor = 12:00–15:30 JST window close,
convention-only law per SPEC_6J §6):

| # | ID skeleton |
|---|---|
| 1–8 | `FB6J1-JF1-{DRIFT,REV}-{UP,DN}-{D1,D30M}-S2` (8 = 2 arms × 2 tails × 2 mandatory delays @ tier S2) |
| 9 | `FB6J1-PLA-JF1` (C1 shadow; seeded random-sign at identical window times) |
| 10 | `FB6J1-ALW-JF1` (C2 always-in-window on all non-event days) |
| 11 | `FB6J1-CLK-JF1` (C3 weekday-matched non-event clock) |

Views (0 IDs): C3′ regime-change-vs-ordinary-MPM split (subset n=6–7 fails
the ≥5/fold floor — descriptive forever); C4 delay-pair adjudication;
±45-min K3 anchor ladder (all 7 variants reported, none selectable).

**JF3 block — 11** (Tokyo-morning 09:00–11:30 JST range-break):

| # | ID skeleton |
|---|---|
| 1–8 | `FB6J1-JF3-{CONT,FADE}-{UP,DN}-{D1,D30M}-S2` |
| 9 | `FB6J1-PLA-JF3` |
| 10 | `FB6J1-ALW-JF3` |
| 11 | `FB6J1-CLK-JF3` (MPM/MOF days removed) |

Views (0 IDs): C3″ DST-mismatch falsifier (clock-law kill); Tokyo-window
≥80%-bars coverage rule EXCLUDE list.

**JF2 block — 7 per host** (MOF disclosure-lagged regime overlay on the host
window; **threshold constant owner-gated** — the "distance-to-highest-
USDJPY-acted-upon" zone threshold must be fixed a priori by the owner before
this block can freeze; K=63 trailing-session window PROVISIONAL):

| # | ID skeleton (shown for host JF1; identical shape for host JF3) |
|---|---|
| 1–4 | `FB6J1-JF2-{DRIFT|CONT,REV|FADE}-{UP,DN}-REG-S2` (4 = regime-state condition on the host's 2 arms × 2 tails @ S2) |
| 5 | `FB6J1-PLA-JF2` (C3′ disclosure-date label shuffle; single-seed single-shuffle unless the placebo ruling adds budget) |
| 6 | `FB6J1-ALW-JF2` (host always-on inside disclosed-regime state) |
| 7 | `FB6J1-CLK-JF2` (C3″ pre-2022 null-era clock — the label must read non-regime throughout 2020-01..2022-08) |

Views (0 IDs): K2 lag-law violation probe (same-day leak); K4 era
concentration; 11th "unverified 2026-07-30 window" stays a SEPARATE
price-only label, never merged (0 IDs).

**RMM 6J leg — +4 (J-C only)** (roll-migration mode, Role B; event clock =
explicit cease-guard-variant switch session; universe = the 27 measured 6J
rolls):

| # | ID skeleton |
|---|---|
| 1–2 | `FB6J1-RMM-MCOMPRESS-REV-{D1,D30M}` |
| 3–4 | `FB6J1-RMM-MCOMPRESS-CONT-{D1,D30M}` |

Views/controls (0 IDs inside the +4): extremal abrupt stratum (2022-09-20 6J
+ the two 6A dates) descriptive-only, n=3 fails any fold floor (pre-declared);
gradual-mode rolls are the family-specific negative (K3); C1 block-shuffle
placebo layer sits OUTSIDE the +4 — budgeting it is the §7.3-style owner
ruling (≥100 seeds × leg would add ≥100 IDs; not proposed here). Chain law:
scoring MUST use the explicit cease-guard variant chain and spread-adjust
switch-day returns (RMM K6); event-stacking EXCLUDE where switch sessions
overlap BoJ/FOMC/ECB/MPC decision windows.

**Option totals check**: J-A = 11+11+7 = **29**; J-B = 11+11+7+7 = **36**;
J-C = 29+4 = **33** or 36+4 = **40**. ✔ matches IDENTITY_TABLES §5 exactly.

## §3 Signature list (what the owner would sign, in full)

1. **Owner 6J ceiling signature — REQUIRED first (no cap exists).** The
   signature must name: (i) the option **J-A / J-B / J-C**; (ii) the
   **clock-shadow reading (a) or (b)** — all totals above use reading (a)
   (the shadow arm is 1 of the 3 counted controls; under (b) add +1 per
   family block: J-A 30 / J-B 38 / J-C 34/41) (IDENTITY_TABLES §2.1).
2. **DC §1.3 boundary ruling** — required **iff J-C**: that a migration-mode
   microstructure hypothesis (abrupt vs gradual) is distinguishable from
   "roll timing as construction" under DC §1.3's roll≠alpha law (NQ-F4 Role
   B precedent cited; GC-F2 construction-only precedent). Never
   self-ratified.
3. **BBO ruling** — BBO is **NOT_RUN (D5 law)** on 6J; single-level BBOMsg
   cannot prove fill/queue. The signature accepts the conservative fill law
   (fill = next-bar open; close-proxy spread; SL-priority; no limit/queue
   claims) as the fill model of record — or funds a BBO study (absent today).
4. **Cost A7 posture** — every cost cell is MODELED COST / UNDER REVIEW /
   VERIFIED_VS_ACCOUNT=NOT_RUN until the owner-authorized fee A7 (D2) runs
   clean (0 HIGH/CRITICAL unresolved) as the prelaunch-A7 precondition. No
   scored cell passes any cost gate before that.
5. **JF2 threshold constant** (if any JF2 block is inside the signed option):
   owner fixes the zone threshold a priori (PARAM-GAP, 6J_DEEP §7-H5).
6. **Placebo ruling** (attached to any option): single-seed/single-delay
   publication law binds until an explicit ≥100-seed ruling.
7. **BoJ stamps** remain NOT_IN_CORPUS (owner decision stands; JF1 stays
   window-convention-only) — restated inside the signature, not a new ask.

## §4 Honesty lines (committed verbatim obligations)

- 29 is the **smallest lawful 6J surface ever stated**; every increment
  above it converts a hypothetical census line into scored cells and dilutes
  per-cell multiple-comparison protection (census-gate argument,
  IDENTITY_TABLES §7.4). No option is recommended — the owner owns the
  trade-off.
- **RMM K2 clause transfers**: MDE ≈ 12.5 bp-class at n≈108 FX events vs
  modeled RT ≈8.5–14.7 bp (6J) — power-marginal by construction; a null at
  this n is the pre-registered K2 death, NOT evidence of absence.
- JF1 per-event MDE at n=54 ≈ 13–19 bp — at/above the modeled RT band; K2
  live risk stated. JF3 needs a window-move scale well above ~10 bp.
- 6J full-grid aggregate tension (96 vs 56) disclosed §1, unused.
- Folds multiply evaluation, never identities (SPEC_PB1_ES §7 law).

— End IDENTITY_BUDGET_6J. Machine mirror: `IDENTITY_BUDGET_6J.json`.
