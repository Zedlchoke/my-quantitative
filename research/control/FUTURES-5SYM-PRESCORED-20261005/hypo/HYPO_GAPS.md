# HYPO_GAPS — missing evidence for NEEDS_EVIDENCE candidates, closing lanes, and P5-* owner-decision slots

- Round: **FUTURES-5SYM-PRESCORED-20261005**, lane **HYPO**. Every gap
  below is a NAMED missing measurement, dataset, or ruling — never an
  inferred PASS. Lanes referenced: **CALCOST** (calendar/cost gap
  closure, permitted routes), **NQ**, **FXEB**, **FXJA** (per-symbol
  PRE-SCORED packet lanes). 0-identity PREP items are marked as such.

## 1. Evidence gaps per NEEDS_EVIDENCE candidate (and the lane that could close each)

| # | candidate / gap | what is missing | closing lane | identities | notes |
|---|---|---|---|---|---|
| G1 | **NQ-F4 Role-B**: roll-week × session-type interaction | the interaction measurement (never run; it IS the K6 gate) | **NQ** | 0 (PREP-legal descriptive) | mechanical from committed v3 switch tables + session types; Role-A audit law stands |
| G2 | **RMM (all legs)**: mode × post-switch-drift interaction | the family's own defining measurement; anatomy-first gate before any Role-B freeze | **FXEB** (6E/6B) + **FXJA** (6J/6A) | 0 | mode labels now DERIVED on all legs (`rmm_mode_ledger.json`); the interaction itself NOT_RUN; block-shuffle placebo stays scored-side |
| G3 | **FX-F5 (6E/6B)**: CIP-vintage sensitivity quantification | year-end ALFRED as-of recomputation of the differential regime on the 27 rolls; the 0.20 rho bar vs the V8/V9 nominal/PPP shadows | **CALCOST** | 0 | the owner real-time SOFR decision (court §d row 7) remains a SIGNATURE regardless of the quantification outcome |
| G4 | **FX-F6 (6E)**: fwd-21d-vol → intraday-sign transfer | the transfer measurement itself | **FXEB** | 0 | release-clock control mandatory in any scored future (rows 107–109 precedent) |
| G5 | **JF2**: zone-threshold constant | owner must fix a priori (PARAM-GAP, 6J_DEEP §7-H5) | **owner** (P5-OD-4); **FXJA** preps the label machinery | 0 | lag-law discipline unchanged |
| G6 | **6B holiday grid 0/42 NOT_OBTAINED** | official CME FX holiday times 2024–2025 | **CALCOST** (permitted routes only; ≤2 attempts/URL; blocked ⇒ BLOCKED_TRANSPORT) | 0 | fail-closed exclusion set stands until landed |
| G7 | **FX quarterly expiries 2023–2026** (64 cells) | official cells; IMM-rule derivation FORBIDDEN | **CALCOST** (permitted routes) | 0 | untouched by current family windows; carried residual |
| G8 | **FX-F4**: M2c-corrected r = RT/MDE refresh | re-derivation of the reopen-gap power/cost arithmetic at the corrected scale (ratio ≈0.16) | **FXEB** (with CALCOST) | 0 | binding consumption law of the erratum; any freeze re-derives first |
| G9 | **AF2**: K2 vintage-flip test (≥3/16 material-roll flips ⇒ dead) | ALFRED year-end as-of recomputation on the 16 material rolls | **CALCOST** | 0 | same quantification machinery as G3 |
| G10 | **AU-REL / CN-REL**: ABS historical release dates; China release calendars | the datasets themselves | **owner acquisition** (P5-OD-3 class); CALCOST documents the fail-closed exclusion inventories meanwhile | 0 | DATA-BLOCKED dossier-grade; AF3's K4 boundary inherits |
| G11 | **NQ dispersion proxy defect** | session-σ re-derivation on the recovered v3 series (pre-recovery defect disclosed) | **NQ** | 0 | feeds any NQ MDE refresh (NQ-F2/NQ-F3 inherit) |
| G12 | **BBO / true spread** (everywhere) | owner data-plane decision; NOT_RUN by law | **owner** | — | conservative fill law binds every fill spec until ruled |

Standing blockers that are SIGNATURES, not evidence (cited, not
re-minted): **ADOPT-D2** fee A7 (all cost numbers stay MODELED/UNDER
REVIEW); **ADOPT-D9** cache_v3 canonicalization + cease-guard
adoption; **ADOPT-D8** 6A tick-era law; **ADOPT-D12** calendar-2026
residuals; **PB2 HOLD** / **PB3 PARK** (lifts = separate owner
rulings); **NQ/6J/FX ceilings** (no cap exists — owner creates one;
IDENTITY_TABLES §4–§6 is the option set); placebo-budget convention
(CENSUS_FINAL §5 slot EMPTY).

## 2. NEW owner-decision slots minted this round (P5-* namespace; defaults fail-closed)

| slot | decision | why it is new | fail-closed default |
|---|---|---|---|
| **P5-OD-1** | EXPWITCH post-gate disposition: accept the F5-K6 death as final for this program generation, OR re-adjudicate the pre-declared gate as an explicit disclosed amendment (vendor-gap resolution is an owner DATA-PLANE decision, never a lane re-parameterization) | K6GATE's both-legs gate outcome created this question; the ten-hypo OD-1 admitted EXPWITCH as a proposal, and predates the gate result | **stays DEAD**; 0 identities; the descriptive anatomy artifacts remain committed evidence |
| **P5-OD-2** | BoJ intraday decision-stamp acquisition (upgrade JF1's lawful 12:00–15:30 JST window-convention anchor to a minute anchor) | described in prior dossiers as "owner acquisition NOT_RUN" without a decision ID; minted so the upgrade path is addressable | **NOT acquired**; window convention remains the lawful anchor (K3 delivered anchor-insensitivity makes this non-blocking) |
| **P5-OD-3** | ABS (Australia) + China release-calendar acquisition (unlocks AU-REL/CN-REL dossiers and resolves AF3's K4 contamination boundary) | same class as P5-OD-2; no prior ID | **NOT acquired**; AU-REL/CN-REL stay NEEDS_EVIDENCE (data); AF3's K4 law stands |
| **P5-OD-4** | JF2 zone-threshold constant ("distance-to-highest-USDJPY-acted-upon" label) — must be fixed a priori before any JF2-conditioned host evaluation | PARAM-GAP existed unnamed; minted for addressability | **unfixed**; JF2 stays NEEDS_EVIDENCE; hosts evaluate unconditioned |

Rules honored: prior decisions cited by original IDs only (ADOPT-D8/
D9/D12, SIXGATE-OD-1..7, BEHAV-D1..7, TEN-HYPO OD-1..4); nothing here
ratifies, lifts, or renumbers anything; the P5 slots are PROPOSALS for
the owner packet (SYNTH wave), not self-ratified openings.

## 3. What the CALCOST lane should pick up first (HYPO lane's input to the work queue)

1. G8 (FX-F4 M2c-corrected arithmetic refresh) — smallest, binding.
2. G3+G9 (CIP-vintage quantification, shared machinery, FX+6A).
3. G6+G7 (holiday times 2024-25; expiries 2023-26) via permitted
   routes only.
4. Fail-closed exclusion inventories per symbol (G10/G12 documented as
   NOT_RUN, never assumed).

## 4. NQ / FXEB / FXJA packet-lane inputs from this census

- **NQ**: G1 (NQ-F4 interaction) + G11 (dispersion re-derivation) are
  the two 0-ID items that change family readiness; K6 PASS artifacts
  (`m1_fomc_anatomy_v3.json`, `m5_0730_era_v3.json`,
  `nq_f3_rebuild_a1a2.json`) are the precondition evidence to cite.
- **FXEB**: G2 (RMM 6E/6B interaction), G4 (FX-F6 transfer), G8 (M2c
  refresh); the court census + gap-std artifacts are cited, never
  re-run as scored.
- **FXJA**: G2 (RMM 6J/6A legs), G5 machinery prep (P5-OD-4); JF1-K3
  and D-2 artifacts cited; PB3 PARK preserved in every 6A line.

— End HYPO_GAPS.md.
