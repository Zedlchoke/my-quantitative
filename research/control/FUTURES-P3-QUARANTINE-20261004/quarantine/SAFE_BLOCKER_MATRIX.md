# SAFE_BLOCKER_MATRIX — per-symbol × dimension matrix, quarantine-safe rebuild

> **SAFE BASELINE = `d7fc6231`** (2026-10-03T22:40:10Z) · **QUARANTINED LAYER =
> `0225b3c2`** (2026-10-03T23:49:47Z, P3-BROWSER-CAL).
> This matrix is rebuilt from baseline artifacts ONLY (`synth/BLOCKER_MATRIX.md`
> + `synth/blocker_matrix.json` @ d7fc6231, backed by P2A/P2B/P2C/P0 results at
> `72c9bc5b` and DEEPFOUR at `a8cd06f2`, all independently verified by
> SYNTH-VERIFY/P0-VERIFY). Every cell that P3-BROWSER-CAL claimed is marked
> **NOT_OBTAINED / PENDING_ADJUDICATION** — it may not raise coverage, gates,
> matrices, or hypotheses until the owner adjudicates the transport in writing
> (see TRANSPORT_QUARANTINE.md, VERDICT: QUARANTINED_POLICY_BREACH).

Task FUTURES-P3-QUARANTINE-20261004 · Lane Q1-QUAR-AUDIT · 2026-10-04 UTC.
Machine companion: `safe_blocker_matrix.json`. Legend as baseline: CLOSED /
PARTIAL / NOT_OBTAINED / NOT_RUN / BLOCKED. All cost rows remain MODELED COST,
`VERIFIED_VS_ACCOUNT=NOT_RUN`, UNDER REVIEW until a new A7.

| Symbol | Expiry calendar authority | Holiday/hours authority | Event PIT | BBO/exec realism | Cost authority (corrected fees; account D2 NOT_RUN) | Data rights/coverage | Roll rule measured | Open defects (headline) |
|---|---|---|---|---|---|---|---|---|
| **ES** | **CLOSED 68/68** q 2010-2026 (42 product + 26 family rolldates; P2A dual archived captures, NQ cross-check identical) — SAFE | PARTIAL: family holidays 2010-2026; **2026 product Globex times NOT_OBTAINED** (widget-only; settlement PDFs = settlement-PRICE times). P3's claimed 2026 schedule + 12 deviation days + ESZ26 18 Dec 2026 = **NOT_OBTAINED / PENDING_ADJUDICATION** | CLOSED-PREP: BLS 204+204 all-08:30 PASS_EVIDENCED + 2025 vintage law; FOMC day-level; surprise NOT_RUN | NOT_RUN program-wide (bbo-1m ≠ intrabar fill, D5 law); O1M depth present | **2.24 tier-1 UPHELD** (0.85+1.38+0.00+0.01; glue defect adjudicated); account NOT_RUN | PASS in-hand: 4,204 sessions 2010-2026, 0 integrity violations | OBSERVED 61/66 + 66/66 no-dev>3 | BLOCKED_TRIAL_BUDGET (minimal 36 vs cap 24, headroom 0); 2026 times NOT_OBTAINED; SPEC §5 arithmetic UNDER REVIEW until new A7 |
| **NQ** | CLOSED 68/68 (parent A1) — SAFE | PARTIAL: 17/17 years holidays; 2026 product times NOT_OBTAINED. P3's claimed 2026 schedule + deviations + NQZ26 18 Dec 2026 = **NOT_OBTAINED / PENDING_ADJUDICATION** | CLOSED-PREP: same BLS law; minute arms 2016+ only | NOT_RUN; O1M depth present | **2.24 tier-1 UPHELD**; account NOT_RUN | PARTIAL: 6.69M bars/4,219 sessions; full-era rebuild hard precondition | BLOCKED-INFERENCE: phantom drift 4-5%/yr (roll-gap corr 0.999) → Role-A audit standing law | Sibling only after cost/clock gate + rebuild; stale `cpa_nfp_status` block flagged |
| **6E** | PARTIAL **52/68** (2010-2022 complete incl. ECH12; 2023-2026 NOT_OBTAINED, routes exhausted — P2B). P3's ECZ26 14 Dec 2026 + 19 supersets 2027-2031 = **NOT_OBTAINED / PENDING_ADJUDICATION** | PARTIAL: 2010-2016 product-level (A2) + 2017-2023 partial; 2024-25 NOT_OBTAINED | CLOSED-PREP: FOMC 58/58; ECB 55; BLS 8:30 class + vintage law | NOT_RUN | **2.46 tier-1 UPHELD** (FX row alias-mapped PARTIAL); account NOT_RUN | PASS in-hand (v2 panel re-verified) | NOT_RUN this round (inherited v2 panel) | PB2 HOLD (census ≥500-trigger gate); FX-F5 owner-gated; no FX cap defined |
| **6B** | PARTIAL 52/68 (as 6E). P3's BPZ26 + supersets = **NOT_OBTAINED / PENDING_ADJUDICATION** | PARTIAL (as 6E) | CLOSED-PREP: MPC 56 PIT; BLS class | NOT_RUN; RT 6.3-11.2bp vs dead-corpus 3.0bp | **2.46 tier-1 UPHELD**; account NOT_RUN | PASS in-hand (M4 +1 date disclosed) | NOT_RUN this round | 6B reopen-gap anatomy NOT_RUN (FX-F4 gate); PB2 HOLD; no cap |
| **6J** | PARTIAL 52/68. P3's J1Z26 + supersets = **NOT_OBTAINED / PENDING_ADJUDICATION** | PARTIAL (as 6E) | PARTIAL: BoJ 54 decision DATES FACT, no minute stamps; MOF lag-law ex-post; 1m-vol 0.455× cleared | NOT_RUN; window book 35.8% thinner measured → delay adjudication binding | **2.46 tier-1 UPHELD**; spread proxy $25 high-biased; account NOT_RUN | PASS in-hand: 2,843,938 bars/95 contracts; MOF 386-op SOURCE_TIDY_RESOLVED | NOT_RUN this round | SECONDARY: 3 gates (orientation proof, BBO ruling, cost A7); no 6J cap; BoJ minute stamps = owner decision; stale 6J_a4_events key |
| **6A** | PARTIAL 52/68. P3's ADZ26 + supersets = **NOT_OBTAINED / PENDING_ADJUDICATION** | PARTIAL (as 6E) | CLOSED-PREP: RBA calendar PASS_EVIDENCED 1990→2026-09; DFF vintage-fragile | NOT_RUN; tick 5e-5 vs 1e-4 UNADJUDICATED | **2.46 tier-1 UPHELD**; spread proxy $20 high-biased; account NOT_RUN | PASS in-hand (v2 panel) | **BLOCKED: roll rule DECLARED-EXTRAPOLATION (k=5 never measured)** | **PB3 PARK**; K0 thin-n kill (n=67) inherited by any reopen |
| **CL** | CLOSED: rule verbatim + 183 months Apr2010-Feb2027 incl. sub-rules (parent A3) — SAFE | PARTIAL: energy family 2011-2015 **52/55 in-universe** (F-7 corrected); 2017-2023 partial. P3's 2025 Thanksgiving/Christmas product times = **NOT_OBTAINED / PENDING_ADJUDICATION** | PARTIAL: WPSR 790 vintages PIT + Cushing 790/790 recomputed; release clock FACT; no free consensus (measured) | **NOT_RUN_DATA_ABSENT: zero comm O1M at vendor root** (measured); IBKR 14-22mo daily/H1 only | **2.36 tier-1 UPHELD** (1.50+0.01); account NOT_RUN | **NOT_QUALIFIED_V2** — owner data decision gates all | PARTIAL: rule verbatim; v1-window panel | No registration path; naive-expectation freeze; daily-only delay axis |
| **NG** | CLOSED: rule verbatim + 240 months — SAFE | PARTIAL (as CL). P3's 2025 Thanksgiving/Christmas product times = **NOT_OBTAINED / PENDING_ADJUDICATION** | PARTIAL: WNGSR 1,205 vintages + The-Desk 369 medians — r-1 unsigned blocker (column-confirmed); Thu-10:00 bucket 25.3% | NOT_RUN_DATA_ABSENT (zero O1M) | **2.46 tier-1 UPHELD**; account NOT_RUN | NOT_QUALIFIED_V2 | PARTIAL (as CL) | NG-F1 NOT_RUN_BLOCKED_R1; NG-F2 error-leg NOT_RUN_DATA_ABSENT |
| **GC** | PARTIAL: Aug2013 → **Dec2023** (+11 new incl. GCZ23 chain); 2024-2026 NOT_OBTAINED (static era ended 2018-02/04). P3's GCV26/GCX26/GCZ26 + superset to GCM32 = **NOT_OBTAINED / PENDING_ADJUDICATION** | PARTIAL: metals grids as CL. P3's 2025 Thanksgiving/Christmas product times = **NOT_OBTAINED / PENDING_ADJUDICATION** | PARTIAL: Treasury/LBMA/CoT free legs $0-testable; daily-only | NOT_RUN_DATA_ABSENT; settlement-derived bar defect | **2.51 tier-1 UPHELD** (1.65+0.01; genuine 1.60→1.65 revision both epochs captured) | NOT_QUALIFIED_V2; single 14-22mo window; serial re-fetch unblocks declared-roll | PARTIAL: roll-migration observable measured (5/6+1 rolls) | No registration path; owner data decision |
| **SI** | PARTIAL: Mar2015 → **Dec2022** (+7 new to SIZ22); 2023-2026 NOT_OBTAINED. P3's SIV26/SIX26/SIZ26 + superset to SIN31 = **NOT_OBTAINED / PENDING_ADJUDICATION** | PARTIAL (as GC). P3's 2025 Thanksgiving/Christmas product times = **NOT_OBTAINED / PENDING_ADJUDICATION** | PARTIAL (as GC); single squeeze regime | NOT_RUN_DATA_ABSENT | **2.51 tier-1 UPHELD**; account NOT_RUN | NOT_QUALIFIED_V2 (44→93 ratio, 1 decoupling) | PARTIAL: rule verbatim 2 eras (SI 12:25 vs GC 12:30 CT offset confirmed) | Curve flip never observed in-window; depth ≥2y for power |
| **6F** | NOT_RUN_DATA_ABSENT (all dims) | NOT_RUN_DATA_ABSENT | NOT_RUN_DATA_ABSENT | NOT_RUN_DATA_ABSENT | NOT_RUN_DATA_ABSENT | NOT_RUN_DATA_ABSENT (no data owned) | NOT_RUN_DATA_ABSENT | Standing ruling **6F NOT_RUN_DATA_ABSENT — unchanged** |

## Quarantine overlay (explicit cell list — sole authority: TRANSPORT_QUARANTINE.md §3)

Cells #1-#28 there, summarized per dimension:
- Holiday/hours: ES/NQ 2026 product session-times + deviation days; CL/NG/GC/SI
  2025 Thanksgiving/Christmas product times → **NOT_OBTAINED / PENDING_ADJUDICATION**.
- Expiry calendar: FX Dec-2026 quarterlies + 2027-2031 supersets (×4 symbols);
  GC/SI remaining-2026 months + supersets; ESZ26/NQZ26 Dec-2026 dates →
  **NOT_OBTAINED / PENDING_ADJUDICATION**.
- Bonus metadata (live productIds; widget window list) → same status.
Nothing else changes vs the safe baseline.

## Standing rulings attached (unchanged)

NO_GO_REGISTER · NO_GO_SCORE · NO_GO_ORDER; ES 24 identities FROZEN (headroom
0); NQ sibling-after-cost/clock-gate; PB2 HOLD; PB3 PARK; 6F
NOT_RUN_DATA_ABSENT; CL/NG/GC/SI PROVISIONAL-only (no vendor O1M). Every fee
value MODELED COST; VERIFIED_VS_ACCOUNT=NOT_RUN on all 10 codes; fees UNDER
REVIEW until a new A7 (P0 erratum UPHELD_IN_FULL). Fee corrections 10/10
upheld at baseline; BLS PIT vintage law in force (event calendars keyed to
vintage as-of decision date).

## Count corrections carried from the baseline matrix (SYNTH-VERIFY measurements)

1. Energy/metals 2011-2015: **52/55 in-universe** (12-cell raw grid contains
   anachronistic Juneteenth placeholders); lane headline "43/45" = arithmetic
   slip, corrected (finding F-7, MEDIUM).
2. All other P2A/P2B/P2C/P0 headline counts independently reproduced at
   baseline: ES 68/68 + 5 dates byte-grepped; FX 208/272 = 4×52; GC +11 / SI
   +7; 6 dated BLS claims pinned; single April-2016 row; fees 10/10.

— End of SAFE_BLOCKER_MATRIX.md.
