# PLAN — NFL-WINPROB-SCORED-V1 (scored evaluation of the frozen NFL protocol)

- cycle_id: NFL-WINPROB-SCORED-V1 · asset: shared · successor of NFL-WINPROB-PREP-V1
  (integration base 9639706ffe631b5a2b77df1830ae6c7df13c0ea1, post-remediation tip)
- budget: 9 scored arms max · GO phrase REGISTERED NOT CONSUMED (P-8)

## 0. Owner authority boundary
Owner round-3 directive (2026-10-04): independent checks rejected both programs'
readiness; remediate per handbook §24, re-verify, and prepare BOTH for scoring.
The owner's stated intention to score is INTENT ONLY — not the typed GO for either
cycle; no real-outcome metric until each cycle has a NEW freeze, NEW A7, and the
owner's exact GO phrase at that cycle's own gate. Old A7/A7-PASS reports are NOT
authority. Boundaries: no S1, no push/merge, no accounts/keys/purchases, no
betting; only synthetic tests + real-data schema/row-count/hash checks pre-GO.

## 1. Inheritance (frozen; semantic changes forbidden)
Inherited VERBATIM from lanes/NFL_C_protocol/PROTOCOL_EVAL_NFL.md: hypotheses H1-H3,
9-arm budget (B0; B1 K{20,40}x HCA{0,65} gamma 2/3; B2 variants), kickoff-grain
as-of law (identical-kickoff exclusion), TIE LAW (ties excluded from scoring and
training; S=0.5 rating update; 0.5 form credit), neutral-site HCA=0, walk-forward
by season, metrics (log loss primary; Brier; 10-bin reliability; calibration
slope; paired ΔLL with kickoff-date-clustered bootstrap, seed 20261005),
T1-T3/R1-R3 thresholds, negative terminal outcomes, NOT_RUN register.
Frozen split: TEST 2019..2025, TRAIN 2000..2018 (PREP_SUMMARY_NFL decisions 1-5
+ ERRATUM remediation: game_type normalization, tie-0.5 form, kickoff batching).

## 2. Amendments (pre-outcome, preregistered before any scoring)
A1 f1 STREAM FROZEN: `elo_diff` (unsuffixed) = B1-a stream (K=20, HCA=0),
identical for all B2 variants. Exported column exists post-remediation.
A2 RUNNER PARITY with NBA v2: per-fold AND pooled reliability/slope/CI; 11
registered comparisons (adds B1-a..d vs B0 demanded by the H1 falsification
rule — comparisons are not arms; budget unchanged); T1-T3/R1-R3/hypothesis
verdicts emitted; hardened launch gates (pinned paths, required ledger, fixed
results dir, structured GO record, clean tree, A7 artifact, FREE lock).
A3 TIE DISCLOSURE: ties excluded from scoring/training rows with counts
disclosed per fold and pooled in fold_meta.

## 3. Data authority
nflverse-data releases only (CC BY 4.0; internal research; attribution chain
in raw/ATTRIBUTION.md). Raw + derived outside git under
~/.my-quantitative-data/nfl-nflverse-v1/. Quarantined: odds columns, pbp-derived
features, injuries (NOT_RUN_PIT). STOP RULE: BLOCKED_DATA_RIGHTS on any failed
rights re-check.

## 4. Gates
G0 bootstrap · G1 data/freeze verification (new, independent) · G2 runner +
synthetic fixtures + REAL-CSV path tests (schema/row-count/load; NO metrics)
· G3 freeze v1 (pinned paths/ledger/results/a7) + ledger seed 9 arms ·
G4 A7 prelaunch ROUND-1 fresh (old PREP-era verdicts not authority) ·
G5 owner GO at this cycle's own gate: "GO NFL WINPROB SCORED V1 EVALUATION".

## 5. Terminal outcomes
NEGATIVE-TERMINAL calibration (R1-R3 verbatim) · BLOCKED_DATA_RIGHTS ·
TECHABORT_*. Positive = calibration claim only; no PnL/betting/edge language.
