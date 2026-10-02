# EXPLORATORY_REPLAY_LAUNCH_DRAFT — successor_design_2026-10-02 v4 deliverable D (NOT RUN; nothing registers today)

A SMALL, self-contained full-path replay program over the EXPOSED PC12A
folds (2022-01-07→2025-12-26) whose outputs are (a) the marginal-leg
estimates the 12-leg battery can never produce on its own calendar, and
(b) the membership-election evidence (S014/S017/S002-JPY) for the next
FREEZE-1. **This is exploratory work on burned data: every output is
hypothesis-generating, EXPLORATORY-labeled, and can never be independent
validation.** Draft stops reviewable BEFORE registration/GO.

## 1. The question set (priority-ordered by the feasibility matrix)

| # | question | arm pair (contrast) | power (matrix) | why it matters |
|---|---|---|---|---|
| Q1 | **S014 sign conflict** — is the meanrev leg a blend-bleeder (trig −222k/−320k) or a positive leg mistimed in-book (solo +109k, pfold +35k)? | `REPLAY_ADMIT11` vs `REPLAY_ADMIT11_X_S014` | 18.0 decisions/fold, ~29 entries/4y — the diagnostic is the FULL-PATH DELTA, not a count floor | the only leg whose attribution sign flips by law; decides the S014 membership election at the next FREEZE-1 |
| Q2 | **S026 blend question** — cascade value exists only blended (solo +9.2k vs trig +825k)? | `REPLAY_ADMIT11` vs `..._X_S026` | 118.25/fold — best-powered | bounds the "workhorse" claim; feeds any future guard/gating design |
| Q3 | **Retirement value of S017** (and the E-floor saves S003/S023/S002-JPY) | `REPLAY_ORIG12` vs `REPLAY_ADMIT11` | S017 ~4.9/fold → the contrast is DESCRIPTIVE-ONLY (pre-typed NOT_RUN_THIN as a refutation; the delta is reported two-sided as a prior) | measures exactly what B1S cannot (round-4 note): retirement vs the ORIGINAL 12-leg always-on book |
| Q4 | trend-core contributions | `..._X_S003`, `..._X_S023`, `..._X_S002JPY` | 5.9 / 1.0 / 5.1 per fold — thin; descriptive with typed thinness | E-floor save/block decomposition |
| Q5 | EUR/GBP cores (cheap, powered) | `..._X_S013`, `..._X_S002GBP` | 14.9 / 30.6 per fold | completeness of the blend decomposition |

Q1–Q3 are the priority set (attribution conflict + best power + the
comparator B1S lacks). Q4–Q5 ride the same execution at marginal cost;
each thin cell is pre-typed per the matrix (S023 essentially NOT_RUN_THIN).

## 2. Arm manifest (exact, unique configurations; exploratory identities)

All arms share: the successor engine (quote-CCY ledger, per-leg exposure +
MAE/MFE journal fields, INF/ECO floors), the exposed calendar (8 folds,
force-flat), component-cost labels (measured C1–C3 cells + DECLARED
U2/U3/U4), tier ×1.0 primary.

| arm_id | composition | folds | rows | tier notes |
|---|---|---|---|---|
| REPLAY_ORIG12 | always-on, ORIGINAL 12 legs (incl. S017), no hygiene rules | 8 | 8 | the retirement comparator; also reconciles against the PC12A B1 arm as an engine-equivalence check (see §5) |
| REPLAY_ADMIT11 | always-on, admitted 11 legs (S017 retired), no hygiene rules | 8 | 8 | the same-legs comparator (= successor B1S composition, exposed-side) |
| REPLAY_ADMIT11_X_S014 | ADMIT11 minus S014 | 8 | 8 | Q1 |
| REPLAY_ADMIT11_X_S026 | ADMIT11 minus S026 | 8 | 8 | Q2 |
| REPLAY_ADMIT11_X_S013 | minus S013 | 8 | 8 | Q5 |
| REPLAY_ADMIT11_X_S002GBP | minus GBP-S002 | 8 | 8 | Q5 |
| REPLAY_ADMIT11_X_S003 | minus S003 | 8 | 8 | Q4 (typed thin) |
| REPLAY_ADMIT11_X_S023 | minus S023 | 8 | 8 | Q4 (pre-typed NOT_RUN_THIN expected) |
| REPLAY_ADMIT11_X_S002JPY | minus S002-JPY | 8 | 8 | Q4 |
| STRESS15_ORIG12 / STRESS15_ADMIT11 | ×1.5 re-price of the two baselines | 8 | 16 | static re-price — PATH-INVARIANT (no cost-keyed rules in these arms; round-4 law) |
| STRESS20_ORIG12 / STRESS20_ADMIT11 | ×2.0 re-price (reporting) | 8 | 16 | same |
| **totals** | **13 identities** | | **104 rows** | exploratory ledger; 0 scored-battery rows |

Optional (owner-flagged, adds 2 identities/16 rows): guard-IN exploratory
pair `REPLAY_ADMIT11_GUARDIN(m)` at the LEARN-proxy multiplier — NOT
recommended in v1 of this program (its feasibility needs the forensics
histogram first; keep the program minimal).

Degeneracy pre-check (round-4 law): the exact-arm dry-run must verify
pairwise-distinct config digests; no arm here collapses into another by
construction (no J3 node present).

## 3. Laws carried over verbatim (no re-litigation)

- **INF/ECO floors** (SAMPLE_FEASIBILITY_MATRIX): no fold-total ever
  suppresses a trade; thin cells typed at fold close.
- **Immutable journals**: `journal_row@1` lineage, hash-chained, with
  rejected-opportunity rows; every output carries
  `EXPLORATORY_EXPOSED_FOLDS` + cost-component labels.
- **Attribution law**: the marginal estimate for leg L is
  `delta(L) = REPLAY_ADMIT11 − REPLAY_ADMIT11_X_L` — a full-path
  difference (netting/caps/costs replayed), never per-leg PnL arithmetic.
  Each delta is reported with its two-sided table (added-winners /
  added-losers at c_pair) and per-fold provenance; deltas on exposed folds
  are PRIORS for the next registration, nothing more.
- **Costs/stress**: component labels; stress re-price only where
  path-invariant (declared per arm above); any future cost-keyed rule
  requires full re-run.
- **Selection**: nothing here selects anything — membership elections
  happen at the NEXT cycle's FREEZE-1 using these priors.

## 4. Tests + audit (meaningful, not decorative)

1. Engine-equivalence reconciliation: REPLAY_ORIG12 vs the committed PC12A
   B1_ALWAYS_ON — per-fold net/DD/fill-count deltas quantified and
   EXPLAINED (expected nonzero: new engine adds quote-CCY + per-leg
   journaling; any unexplained divergence is a blocker, tolerance declared
   at freeze).
2. Determinism: byte-identical re-run of one arm.
3. INF/ECO causality suite T1–T4 (truncation + mutation + separation +
   cold-start).
4. Book identity: quote-CCY residual ≤ 1e-9 per arm; journal hash-chain
   verify.
5. Independent audit (A7-style, fresh context): recompute deltas from
   journals, verify arm uniqueness digests, confirm no validation language
   anywhere.

## 5. Budget + gating sequence (STOP point)

Exploratory budget: **13 identities / 104 rows** (+ optional guard pair
15/120) on its OWN registered cycle line — proposed name
`EXPLORATORY-REPLAY-V1`. Sequence: owner reviews THIS draft → plan write →
registration (FREEZE-1: arm manifest, laws §3, tolerances) → engine
implementation + T1–T4 → freeze (FREEZE-2: code SHA + manifests) → A7
prelaunch → owner GO → execute → report + A7-style audit → TERMINAL with
EXPLORATORY labels. **Nothing in this draft runs today.** No sealed bytes,
no S1, no validation claims, no orders.

Dependencies: none on TB-LABELS (independent); the forensics histogram
(deliverable B) is only needed if the optional guard pair is elected.

— end replay launch draft —
