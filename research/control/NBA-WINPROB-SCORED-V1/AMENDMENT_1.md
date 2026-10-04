# AMENDMENT 1 — NBA-WINPROB-SCORED-V1 (pre-outcome, §24 remediation)

Trigger: owner-reported independent verification (2026-10-04, round 3) rejected
readiness; controller re-measured and CONFIRMED every defect. No real-outcome
metric was ever computed (TRIAL_LEDGER: 9 PREREGISTERED / 0 COMPUTED), so per
handbook §24 this is a pre-scoring remediation: freeze 39b11156 is marked
SUPERSEDED_BLOCKED; nothing about hypotheses/arms/folds/thresholds changes.

## Confirmed defects (measured)
D1 export_features wrote only elo_diff_B1-a..d; run_evaluation.load_rows needs
    a plain `elo_diff` column -> KeyError on the real CSV; the synthetic suite
    never exercised the real-CSV path.
D2 Protocol §4 output incompleteness: fold-level reliability dropped at
    serialization; calibration slope only pooled; paired ΔLL/CI only pooled;
    §6 T1-T3/R1-R3 and hypothesis verdicts never emitted.
D3 Launch-gate gaps: --games/--features not forced to the manifest-pinned
    paths; --ledger optional; --out arbitrary; GO record only grepped for
    phrase+cycle; no dirty-tree / A7-artifact / canonical-registry / lock check.
D4 B2's f1 did not specify WHICH Elo stream (K/HCA) feeds it.

## Amendments (all preregistered BEFORE any outcome)
A1 f1 STREAM FROZEN: `elo_diff` (unsuffixed) is exported as the B1-a stream
   (K=16, HCA=0) — identical for all four B2 variants. Rationale: K=16 is the
   slow bracket already used by two B1 arms; HCA does not enter f1 by protocol
   (intercept carries home effect); no outcome was consulted. features.csv is
   rebuilt with the added column; new sha256 pinned in FREEZE v2.
A2 RUNNER COMPLETENESS: per-fold AND pooled outputs for reliability bins,
   calibration slope, and every registered paired ΔLL with date-cluster
   bootstrap CI; §6 gate verdicts (T1-T3, R1-R3, INCONCLUSIVE) and hypothesis
   verdicts (H1: B1 arms vs B0; H2: B1(K,100) vs B1(K,0) paired; H3: B2-a vs
   B2-b) are computed and emitted. No thresholds change — they are §6 verbatim.
A3 HARDENED LAUNCH GATES: manifest pins absolute games/features paths (inputs
   MUST equal them), the required ledger path, the fixed results dir, and the
   expected A7 report path; GO record must be structured JSON with phrase ==
   the exact phrase, cycle_id, typed_by == "owner", typed_at ISO; worktree
   must be git-clean; A7 report must exist and contain A7_PRELAUNCH_AUTHORIZED;
   machine heavy lock must be FREE_PROVEN at launch.
A4 REAL-CSV PATH TESTS (pre-GO, no metrics): tests load the real features.csv
   (schema/row-count/columns + load_rows end-to-end) without computing any
   outcome metric — schema/row-count/hash checks only, per owner instruction.

Freeze v2 (new code_freeze_sha + new features sha256) supersedes 39b11156;
E2-delta and A7-delta (round 2, fresh) must re-authorize before any GO.
