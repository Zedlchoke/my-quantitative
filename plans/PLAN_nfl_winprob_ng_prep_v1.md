# PLAN — NFL-WINPROB-NG-PREP-V1 (next-gen NFL win-prob research PREP, $0)

- cycle_id: NFL-WINPROB-NG-PREP-V1 · asset: shared · ACTIVE_LIGHT, budget 0 scored, NO GO phrase
- owner authority 2026-10-05 (this chat): research/PREP + bookkeeping ONLY — explicitly NOT a GO
  for any scored cycle and NOT authority to run any metric on new outcomes. No S1/paper/live/
  betting/data purchases/push/merge. Futures threads and NBA/WNBA cycles untouched. Frozen
  sources, results, ledgers of NFL-WINPROB-PREP-V1 / NFL-WINPROB-SCORED-V1 (TERMINAL) and all
  other cycles are immutable history — this cycle never edits them.

## Inheritance (read from bytes; re-measured at bootstrap)

- NFL-WINPROB-SCORED-V1 = TERMINAL, INCONCLUSIVE: 9/9 arms observed per TRIAL_LEDGER;
  H1 alive, H2 (HCA constant) / H3 (rest/short-week mains) REJECTED; repro twin byte-identical;
  A7 terminal CONFIRM; GO consumed then extinguished at close (registry 2026-10-05).
- Baseline law: NFL B1* = B1-c own-Elo K=40 HCA=0 (pooled LL 0.6407 vs B0 0.6935,
  ΔLL −0.0528 [−0.0676, −0.0380]). Any new mechanism must beat B1*, not merely B0.
- Spent-window law: TEST 2019..2025 is spent. No re-grid of K/HCA/rest/form mains on it, ever;
  no 2019–2025 reuse as a new hypothesis-testing window. Genuinely new NFL evidence = 2026
  forward only, and 2026 is PROSPECTIVE ONLY from the real freeze/prediction timestamp.
- Prospective law: every 2026 game already played BEFORE the cycle freeze/prediction timestamp
  is NOT_RUN for prospective scoring and must never be presented as a pre-game forecast.
  Prediction ledger rows are append-only, timestamped strictly before kickoff UTC.
- Input evidence: WINPROB-NG-PREP-V1 lanes/C_MECHANISMS/MECHANISMS.md (H-C1 SOS-Elo,
  H-C2 home/away split, H-C3 availability NOT_RUN_PIT, H-C4 fatigue×venue interactions,
  F9 NFL offseason EPA prior) — proposals, not authority; this cycle re-adjudicates for NFL.

## Tasks (owner round 2026-10-05)

1. Lane A — DATA: audit nflverse $0 rights (CC BY 4.0 text, provenance, attribution chain),
   coverage 2000–2026 (schedule/result/kickoff UTC schema, team-ID crosswalk, neutral-site,
   tie/cancel/forfeit handling), classify 2026 games played-before-freeze vs future, verify
   publish/as-of story per asset. Injury/availability data ONLY if rights AND per-record
   publish timestamps are PIT-proven; else NOT_RUN_PIT. Downloads $0-only, outside git under
   ~/.my-quantitative-data/ with URL/version/pull-time/sha256. No metrics computed.
2. Lane B — MECHANISMS: from the B1* baseline propose AT MOST 2–3 genuinely new NFL mechanisms,
   prioritizing (a) SOS-adjusted Elo, (b) home/away split rating, (c) offseason EPA prior
   (train-only, pbp is post-game compiled); short-week×away interaction ONLY as a conditional
   candidate gated on train-internal strength (design-level, no outcome runs in PREP).
   No re-grid of rejected HCA/rest mains. Each mechanism: $0 source + rights, as-of law,
   falsifier, negative control, power estimate (~270 regular-season games/season; ≥2 seasons
   for strong conclusions), capacity check. Replacement-rating shape preferred; additive
   logistic-over-Elo is dead per both terminal cycles.
3. Lane C — PROTOCOL: train-internal selection design (rolling-origin inside TRAIN
   2000–2018-equivalent new-cycle split), prospective append-only prediction ledger recorded
   strictly before kickoff UTC, frozen ≤9-arm budget including B0 + B1*, log loss primary,
   Brier + calibration slope/reliability secondary, paired date-cluster bootstrap uncertainty,
   playoffs separate, stop rules, ≥2-new-season condition before any strong NFL conclusion.
4. Lane D — independent verifier AFTER controller synthesis: bytes vs claims, rights, PIT,
   trial accounting (0 scored), registry/head/worktree/lock/clean-tree coherence. Never repairs.

## Boundaries

- No scored computation, no metrics on real outcomes, no S1, no paper/live, no betting,
  no purchases, no push, no merge to main, no edits to frozen artifacts/ledgers of any cycle.
- Root checkout = control plane only. Lane work in the exact worktrees/branches named in the
  dispatch packets. Registry writes only via researchctl (CAS); on concurrent modification:
  re-measure + CAS retry, never overwrite.
- Language law: calibration/forecasting vocabulary only — no PnL/betting/edge language.

## Artifacts

lanes/A_DATA/ · lanes/B_MECHANISMS/ · lanes/C_PROTOCOL/ · lanes/D_VERIFY/ · lanes/DISPATCH/
(each lane ends with handoff JSON zcode_orch_v3_handoff@1 at its dispatch handoff_path).
New data outside git under ~/.my-quantitative-data/nfl-ng-prep-v1/.

## Terminal outcomes (negative-first)

PREP_COMPLETE_PENDING_OWNER_DECISIONS | BLOCKED_DATA_RIGHTS | BLOCKED_TOOLING | TECHABORT_*.
Any scored successor requires fresh registration + freeze + A7 + owner typed GO at its own
gate. This cycle registers no GO phrase and consumes none.
