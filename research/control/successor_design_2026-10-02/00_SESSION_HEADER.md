# successor_design_2026-10-02 — Journal census, successor hypothesis register & composite policy design

**STATUS HEADER — READ FIRST.**

- **Preparation-only session** (owner dispatch 2026-10-02): journal analysis,
  hypothesis register, portfolio architecture and successor protocol DRAFT.
  No new strategy backtest was run, no scored cell, no S1, no paper/live/
  orders, no registration, no registry hand-edit, no reuse of any TERMINAL
  cycle's budget. GO phrases of closed cycles are dead (P-8).
- **Everything quantitative below is either**
  `[M]` measured from committed artifacts (path cited),
  `[derived]` arithmetic on those artifacts under a stated convention, or
  `[NR]` not established. Missing evidence is `NOT_RUN`, never inferred PASS.
- **Exposure law:** the PC12A 8 test folds (2022-01-07→2025-12-26) are
  EXPOSED and can never serve as validation; the DAILY-EXPLORATORY-V1 8
  exploratory folds (2022-09-30→2026-09-24) are exposure-adjacent
  (EXPLORATORY labels, DECLARED costs). Every rule number quoted from them is
  hypothesis-generating only and is labeled POST_OUTCOME where the trigger
  shape was chosen after seeing those folds.
- **Conventions inherited:** USDJPY journal magnitudes are at-par JPY
  quote-CCY units (DP §13 — pooled cross-symbol sums are
  convention-limited; within-symbol and within-arm contrasts are
  invariant). Costs are DECLARED bands (`PROVISIONAL_PENDING_COST_AUTHORITY`)
  except measured spread cells C1–C3. DAILY findings are exploratory-only
  under DECLARED costs; its C2 clock-shadow control was SUBSTITUTED by
  REPORT20_PAIR (A7 TF-1) and must never be described as having run.

## Session intake snapshot (measured 2026-10-02)

- Root `main @ 0aeb2ce5be0c70e47bc7f02563b37e426d7eb815` (verified);
  dirty tree = owner files only (SIXSOURCE ibkr_fx ×3, FUTURES-DATA-10SYMS,
  SANDBOX-OVERFIT, SLEEVE-FX5) — untouched by this session.
- Worktrees measured: PC12A integration `c93123db` (TERMINAL), DAILY prep
  `e1872377` (TERMINAL, matches registry head). Heavy lock `FREE_PROVEN`;
  no scored/diag workers. Registry: both cycles TERMINAL; S1 SEALED_UNTOUCHED
  is the registry assertion — DAILY's own journals contradict it (tail-dated
  fills; protocol §1.1 recorded lineage defect).
- Prior-artifact base of this packet:
  `research/control/terminal_review_2026-10-01/` (DECISION_PACKET v2,
  3 symbol dockets, RULE_SLATE, GATING_VS_SIZING, daily_successor/),
  `research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/` (scored journals,
  metrics, PASS_BARS_V2), `.worktrees/pc12a-daily-exploratory-prep/research/
  control/DAILY-EXPLORATORY-V1/` (battery + terminal decision).

## Files in this packet

| file | content |
|---|---|
| `JOURNAL_CENSUS_AND_RECONCILIATION.md` | trade census over all 38 Stage-C arms + 85 DAILY journals; dedup law; blocked/deferred inventory |
| `SYMBOL_DOSSIERS.md` | per-symbol win/loss/breakeven/blocked dossiers (3 journaled symbols + thin/blocked classes) |
| `COMPLEMENTARITY_AND_FAILURE_MAP.md` | co-loss weeks, exposure overlap, per-leg solo books, failure modes map |
| `HYPOTHESIS_REGISTER.md` | every prior hypothesis (incl. benched) → keep / amend / refuted-by-evidence / data-blocked; new hypotheses with anti-hypotheses |
| `COMPOSITE_POLICY_DESIGN.md` | successor coordination architecture (eligibility, per-symbol on/off, weighting, caps, FLAT law) — DRAFT, not run (v2: budget recomputed, risk caps, cost law) |
| `SUCCESSOR_PROTOCOL_DRAFT.md` | exposure-lineage verdicts per axis, two-freeze law, GO-gated illustrative calendar, purge/warmup tables, two-track path, owner menu (v3) |
| `SAMPLE_FEASIBILITY_MATRIX.md` | per-hypothesis/per-arm sample-power matrix + INF/ECO floor-causality law + T1–T4 test spec (v3, F1) |
| `ERRATUM_V2.md` / `ERRATUM_V3.md` | itemized corrections (round 2: budget/calendar/selection/claims/costs; round 3: sample-power, freeze timing, sealed lineage, residual contradictions, canonical budget) |
| `SKEPTIC_REVIEW.md` / `SKEPTIC_REVIEW_V2.md` / `SKEPTIC_REVIEW_V3.md` | independent verification records (v1 census; v2 revision; v3 invariants) |
| `BAO_CAO_TIENG_VIET.md` | plain-Vietnamese report: what is known / unknown / next |
| `HANDOFF.json` | structured handoff artifact (schema `zcode_orch_v3_handoff@1`) |
| `ROUND4_ADDENDUM.md` | round-4 corrections disposition (C1–C5) + two new measured findings (docket-A swap-sign; J3 grid static degeneracy) |
| `forensics/` | deliverables A+B: TRADE_FORENSICS_BRIEF, GUARD_AND_SESSION_FORENSICS, forensics_build.py + 4 machine-evidence JSONs (committed c081ac16) |
| `tblabels/` | deliverable C: TB_LABELS_EXECUTION_PREP + refuse-to-run producer_skeleton.py |
| `EXPLORATORY_REPLAY_LAUNCH_DRAFT.md` | deliverable D: small full-path LOL/LORO exploratory program (13 ids / 104 rows), STOP before registration/GO |
| `analysis/` | `census_and_complementarity.py` + `census.json` + `complementarity.json`; `calendar_variants.py` + `calendar_variants.json` (anchor_status_v3: PENDING/ILLUSTRATIVE + GO-gate; validated against DAILY fold windows); `arm_manifest.json` + `verify_arm_manifest.py` (canonical budget, machine-verified) |

## Corrections this packet makes to the prior review record

1. **Docket B §9 called the `*_MO_*` arms "minus-one/plus-one arms." They
   are SOLO single-leg arms** (journal header `legs` has exactly 1 leg;
   verified all 24). No minus-one (portfolio-minus-leg) arm exists anywhere
   on disk. Every per-leg portfolio counterfactual remains `[NR]` (consistent
   with DP corr-3).
2. **Three different S026 numbers circulate and are NOT interchangeable**:
   portfolio entry-trigger attribution +825k/+822k (docket A), in-portfolio
   leg attribution `paper_fold_net_by_leg` +1,637,143 (B1 metrics), solo-arm
   +9,203 (B1_MO_USDJPY-S026). Same for S014: netted attribution −222k/−320k
   vs **solo +109,448 positive**. Attribution law must be named with every
   per-leg number (see HYPOTHESIS_REGISTER H-J3 amendment).
3. **The `heat_events_by_symbol` key is ABSENT from B1_ALWAYS_ON
   metrics.json** (POLICY has 2,319/568/524 events). Exposure statements
   are POLICY-side only, disclosed as proxy. Joint EURUSD×USDJPY
   in-position time = 22.92% of the window (machine-computed,
   `complementarity.json`).

— end header —
