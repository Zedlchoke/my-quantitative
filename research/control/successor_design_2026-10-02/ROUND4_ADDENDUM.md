# ROUND4_ADDENDUM — successor_design_2026-10-02 (co-owner round 4; v3 @ 1f61b489 + this addendum)

Round 4 accepted the v3 packet's load-bearing content (verifier
ALL TOTALS MATCH; Poisson count feasibility independently confirmed —
noting counts ≠ effect/net/DD power) and directed CONCRETE deliverables
under existing analysis authority instead of another full-packet round.
This addendum records the five corrections' dispositions and the two new
measured findings; the deliverables live in their own files.

## Corrections (dispositions)

- **C1 (Poisson framing)** — applied to SAMPLE_FEASIBILITY_MATRIX header:
  model-based estimates under an independence assumption; clustering /
  zero-inflation make true P(unmet) uncertain in EITHER direction at a
  given threshold; figures are ordering guidance, NOT bounds. Denominators
  frozen per estimand; ≥20/3/100 carry exact law/unit; NO re-denomination
  (entry→decision, per-leg→battery) anywhere.
- **C2 (pooling)** — "rescue path" language replaced: the pooled 2-symbol
  read is DESCRIPTIVE; satisfies no per-symbol floor, rescues no LEARN
  grid, and is NOT shared-mechanism evidence (heterogeneity, per-symbol
  floor failures, cross-symbol dependency retained).
- **C3 (DAILY impact)** — matrix now says **IMPACT_ON_VERDICT_NOT_MEASURED**
  (counting the 3 fires does not bound the full-path effect; no replay or
  bound exists); terminal verdict stands, reliability on the
  floor-eligibility mechanics qualified — neither overturned nor
  re-affirmed. Protocol §1.1: this packet does NOT interpret the
  directive's scope and does NOT ratify history; PERMISSION vs STATISTICAL
  EXPOSURE axes kept separate; append-only DAILY incident erratum PROPOSED
  as owner action, frozen artifacts and registry untouched.
- **C4 (verifier/config uniqueness + comparators + stress)** — manifest
  carries three ROUND-4 NOTEs: (i) verifier sums symbolic IDs — config
  uniqueness is proven only at FREEZE-2 by the exact-arm dry-run, incl. the
  J3=∞ collapse (guard-IN ≡ SLATE; crossed ≡ LOL configs) which must be
  detected, typed, and not double-executed; (ii) B1S is same-ADMITTED-legs
  and measures hygiene-on-admitted-set ONLY — the retirement-vs-original
  comparison belongs to the exploratory replay program's B1_ORIG12
  (EXPLORATORY_REPLAY_LAUNCH_DRAFT; design §5 row scoped); (iii) static
  stress re-pricing assumes path invariance — cost-keyed rules (spend-cap
  guard) require full re-runs; prelaunch spec declares per arm.
- **C5 (HANDOFF pointer)** — satisfied by the two-commit pattern: work
  commit first, then a HANDOFF.json update commit recording the work
  commit's REAL full SHA (no self-referential SHA); paths verified.

## New measured findings (round 4)

1. **Docket A §0 swap-sign defect (quantified; forensics lane).** The
   docket's excursion identity "Σnet = fills + swap" ADDS a positive-cost
   swap: reported Σnets 602,943.11 / 689,713.59 are overstated by exactly
   1×swap; the true identity fills − swap equals engine
   `per_symbol_fold_records` at **$0.000 on all 6 arm×symbol cells**
   (600,082.92 / 687,284.31), and the docket's "2,860.19 (0.48%) fold-edge
   mark convention residual" is exactly **2×swap** — no fold-edge residual
   exists. Impact: absolute USDJPY Σnets in docket A (incl. pooled W/L/B
   sums) overstated 0.2–0.5%; W/L/B classification and all relative
   statements unaffected (c and medians shift negligibly; no conclusion in
   this packet changes — dossiers/complementarity already cite the engine
   numbers). The docket file is a committed 2026-10-01 artifact and is NOT
   edited; this addendum + `forensics/verification_checks.json` are the
   correction of record. `JOURNAL_CENSUS_AND_RECONCILIATION.md` §4 inherits
   the docket wording — corrected reading: "journal symbol nets (fills −
   swap)".
2. **J3 guard grid is statically degenerate (forensics histogram).** All
   627 fired defers sit at r = spend/cap ∈ [1.00, 1.41] (POLICY n=331 med
   1.03 q95 1.11 max 1.20; B1 n=296 med 1.06 max 1.41; cap constant
   $2,836.97 on all rows). ZERO rows ≥ 1.5× ⇒ RULE_SLATE's grid
   {1.5, 2.0, ∞} admits identical defer sets (331/296; 8/8 folds ≥ 3; min
   fold 15/12). The register's NOT-ESTIMABLE flag is resolved: a
   differentiating grid must sit inside [1.00, 1.41] (m=1.1 → 5%/27%
   firing; m=1.2 → 0%/15%), or the hypothesis collapses to binary
   remove-vs-keep-at-cap. Endogeneity (counterfactual cap re-binds the
   spend path) and selection (r observed on fired defers only) caveats
   carried. Register A-H1 updated.
3. **Session/DST (descriptive).** USDJPY NY-long decision bucket: 172 rows,
   67 GMT / 105 BST (61% vs 58% calendar share) — no phase concentration;
   EUR h12/16: 60 rows, 55% BST, votes near-symmetric. The London-close
   overlay shows the bucket sits +1..+5h post-close in winter vs +2..+6h in
   summer (NY-local 11–16 vs 12–17) — **bare-UTC session rules are
   phase-ambiguous, validating the DST-derived session-mark law** (HN-1
   trigger). No causal claim.

## Deliverables (files; all analysis-only, nothing executed)

| id | file | content |
|---|---|---|
| A | `forensics/TRADE_FORENSICS_BRIEF.md` | inventory/reconciliation of W/L/BE/blocked by symbol×arm×fold with cost labels; feature-at-entry vs post-outcome field coverage (MAE/MFE, per-fill spread, realized-vol typed NOT_RUN_INPUT_MISSING + adapter specs); per-leg what-killed-it |
| B | `forensics/GUARD_AND_SESSION_FORENSICS.md` (+4 machine-evidence JSONs, deterministic `forensics_build.py`) | guard spend-band histogram; J3 node counts; session/DST alignment; two-sided descriptive tables (attribution-on-exposed-path, not marginal PnL) |
| C | `tblabels/TB_LABELS_EXECUTION_PREP.md` + `tblabels/producer_skeleton.py` | registration-ready TB-LABELS producer spec (barrier definitions with file:line cites; AMBIGUOUS_ORDER law — SL-first only as derived field per the frozen design's law, ambiguity rate a first-class gate; quote-side/fill-lag per FILL_ACCOUNTING_SPEC; DST-aware London-close via the engine's zone law; censoring; firewall §2a; budget = 0 scored rows) + refuse-to-run skeleton |
| D | `EXPLORATORY_REPLAY_LAUNCH_DRAFT.md` | small full-path LOL/LORO program on exposed folds: 13 identities / 104 rows (REPLAY_ORIG12 + ADMIT11 + 7 LOL + 4 stress), priority Q1 S014 sign-conflict / Q2 S026 blend / Q3 retirement-vs-original (B1_ORIG12 comparator B1S lacks); INF/ECO + immutable journals + path-invariance stress law + engine-equivalence reconciliation vs PC12A B1 + independent audit; STOP before registration/GO |

Boundaries held this round: 0 engine runs, 0 new PnL replays, 0 sealed/S1
bytes, 0 registrations, 0 orders; owner dirty tree and futures lane
untouched; frozen artifacts (docket A, DAILY) not edited — corrections of
record live here.

— end round-4 addendum —
