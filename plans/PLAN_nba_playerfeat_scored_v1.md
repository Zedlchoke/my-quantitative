# PLAN — NBA-PLAYERFEAT-SCORED-V1 (NBA player-feature win-prob scored successor, $0)

- cycle_id: NBA-PLAYERFEAT-SCORED-V1 · asset: shared · ACTIVE_LIGHT, budget 0/9 arms scored,
  GO phrase registered NOT typed: `GO NBA PLAYERFEAT SCORED V1 EVALUATION`
- owner authority 2026-10-05 (this chat): bring the NBA program to GO-READY — registration,
  freeze, implementation, synthetic fixtures, exact-arm dry-run and independent A7 per gate;
  **STOP before owner typed GO**. No scored/OOS computation this round: the walk-forward OOS
  window is frozen here and evaluated only after GO. Train-internal selection on the 2018–2021
  selection window is the gate-sanctioned path (freeze completion requires frozen φ params);
  nothing on OOS seasons, nothing on the spent window.
- Hard boundaries: no GO typed by agents; no OOS evaluation; no S1; no paper/live/betting; no
  purchases; no push/merge; no backfill; no edits to frozen artifacts/ledgers. Language law:
  calibration/forecasting vocabulary only. Underlying ESPN/league rights unverified — internal
  research only, fail-closed.

## Inheritance (re-measured 2026-10-05)

- Feature table (WINPROB-PLAYERFEAT-PREP-V1, lane A + D verified): 28,374 rows = 2×14,187
  played games 2016–2026 at `~/.my-quantitative-data/playerfeat-prep-v1/nba/features/`
  (sha-pinned in FEATURE_TABLE_MANIFEST; as-of `asof_v1_strict_tip_utc`; 0 outcome columns;
  neutral flags; 19 exhibition rows flagged `is_exhibition`; 3 box-less FINAL games 2017–19
  carry neutral features with n_prior disclosed; 33 identity-less 2026 rows excluded at build).
- Baseline law: **B1\* = B1-d own-Elo K=32 HCA=100 γ=0.75** carried VERBATIM from
  NBA-WINPROB-SCORED-V1 (TERMINAL, NO_PROGRAM_PASS) — mandatory arm, never re-tuned. B0
  constant floor refit train-only. Diagnostic ablation B1-HCA0 (outside budget).
- Windows (frozen proposal inherited verbatim from NBA-WINPROB-NG-PREP-V1
  SUCCESSOR_PACKET_SCORED.md §1): WARM-UP 2016–2017 (streams run, never scored);
  TRAIN-INTERNAL SELECTION 2018–2021 (4 rolling-origin folds; cutoff 2021-08-01T00:00Z);
  WALK-FORWARD OOS [2022, 2023, 2024, 2025, 2026] — POST-GO ONLY (hard season cap ≤2021 for
  every real-data computation this round; OOS mode requires a GO token that does not exist and
  is exercised only on synthetic fixtures); SPENT 2009–2015 citable never scoreable; PROSPECTIVE
  2026-27+ = future ledger work, out of scope here.
- Dead-shape law: additive logistic features over elo_diff are DEAD (both terminal cycles).
  Player features enter INSIDE the rating argument as pre-game rating adjustments
  (R̃ = R + φ·x, standardized x), designed-null φ=0 ≡ B1* bit-for-bit. T1 team-rest/form
  ancestry veto: no rest-days/win-loss-form re-entry; time-shuffled twins are the design guard.
- Metrics/uncertainty (inherited machinery): LL primary; Brier + reliability + calibration
  slope band [0.85, 1.15]; paired ΔLL with kickoff/tip-date-clustered bootstrap, 10,000
  resamples, seed 20261005; fold-majority bar ≥3/5; single-batch OOS scoring law (no interim
  peeks) — all bound at freeze for the post-GO read.

## Tasks (owner round 2026-10-05; stop before GO)

1. Lane T — IMPLEMENTATION + TRAIN-INTERNAL SELECTION: implement the evaluation harness
   (modes: `select` = real data capped season≤2021; `evaluate-oos` = refuses real data
   without GO token, synthetic fixtures only; `--selftest` hand-computed fixtures incl. Elo
   update, HCA=100 argument, season-boundary γ=0.75 reversion, designed-null φ=0 ≡ B1*
   byte-identity, feature standardization, neutral-rule behavior, leakage canaries). Replay
   B0/B1* on WARM-UP+SELECTION windows; feature arms PF-A (rotation concentration: top5_share/
   load deviation), PF-B (top-3 form-vs-self), PF-C (lagged absence with trade guard) — each
   ALONE, rating-input shape, x standardized (mean/sd frozen from warm-up+early-train, pinned
   at freeze); pre-registered grids φ ∈ {−50,−25,0,25,50} per arm (15 configs, all counted);
   4 rolling-origin folds over 2018–2021; selection criterion pooled inner LL; tie-break
   simpler config. Time-shuffled twins per arm (diagnostic, outside budget; twin beating
  parent ⇒ MACHINERY_SUSPECT, arm UN-SCORED). G-ENTRY per arm (ADMIT: pooled inner ΔLL vs
   B1* point <0 AND slope in band AND twin clean). SELECTION_LEDGER.jsonl + SELECTION_REPORT.md
   with frozen φ per arm (or slot release). No OOS access (asserted).
2. Lane S — SYNTHETIC FIXTURES + EXACT-ARM DRY-RUN: extend with successor-level fixtures:
   designed-null byte-identity on ≥3 synthetic streams; determinism double-run; neutral/
   missing-box behavior; exhibition exclusion; identical-game-set law; `evaluate-oos` mode
   refusal without GO token; full harness rehearsal on synthetic OOS-like streams (sandbox
   outputs only); exact-arm identity (pairwise distinct record ids; non-vacuous). DRYRUN_
   REPORT.md with commands/exit codes.
3. Lane A7 — INDEPENDENT PRELAUNCH AUDIT (fresh context; after controller integration):
   SHA chain; designed-null re-run; season-cap probes (doctored 2022 row must fail loud);
   selection-ledger completeness + independent recompute of ≥2 configs; freeze completeness;
   boundaries (0 scored, no OOS values anywhere, GO not typed); OWNER_GATE_BRIEF.md.
   Verdict PASS | REFUSED.

## Boundaries

- Lanes write only in their lane dirs (+ sandbox data under `~/.my-quantitative-data/
  nba-playerfeat-scored-v1/`); feature table + all prior corpora read-only; no git by lanes;
  registry via researchctl from root (controller); CAS on conflict.
- Every freeze-affecting change: pin new SHA → re-run dry-run → fresh-context A7 → registry
  reconcile. Missing evidence = NOT_RUN, never inferred PASS.

## Artifacts

`lanes/T_SELECT/ · lanes/S_SYNTH/ · lanes/A7_PRELAUNCH/ · lanes/DISPATCH/` under the
integration worktree; control state under `research/control/NBA-PLAYERFEAT-SCORED-V1/`.

## Terminal outcomes (negative-first)

PRELAUNCH_READY_PENDING_OWNER_GO | SELECTION_NEGATIVE_ALL_CANDIDATES_FAILED | BLOCKED_DATA_
RIGHTS | BLOCKED_TOOLING | TECHABORT_*. GO phrase typed ONLY by the owner at this cycle's own
gate after the A7 verdict; never typed, paraphrased or consumed by any agent.
