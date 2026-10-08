# PLAN — SPORTS-WINPROB-TUNE-PREP-V1 (four-league win-prob TUNE PREP umbrella, $0, ZERO scored)

- cycle_id: SPORTS-WINPROB-TUNE-PREP-V1 · asset: shared · budget **0/0 scored**
  (no scored cell is possible in this cycle; diagnostics live in this cycle's own
  ledger) · registered 2026-10-08 · **NO GO phrase exists for this cycle.**
- owner authority 2026-10-08 (this chat, verbatim intent): open ONE umbrella PREP
  cycle to research win-probability improvement for NBA, WNBA, men's international
  football and NFL. This is PREP ONLY: data re-verification, valid TRAIN-INTERNAL
  build/tune, freeze/decision packets; **STOP before every new scored OOS and
  before any Owner GO.** Data budget $0. Never modify models or ledgers of
  TERMINAL cycles; never modify the running SPORTS-PAPERTRADE-EXEC-V1 program
  (wallet 1,000 USD, 5.00 stake, 100.00 open cap, EV gate and odds quota
  unchanged); no real betting; no data purchases; no push/merge; no self-typed GO.
- Per-league immutable baselines, targets, universes, as-of/PIT laws, data rights
  and TRAIN/EXPOSED/FRESH windows are inherited from the cycles below and are
  NEVER cross-compared: no direct log-loss comparison between 2-way and 3-way
  targets or between different windows. At most TWO new MECHANISM hypotheses per
  league, named and frozen BEFORE any measurement. KEEP_BASELINE and NOT_RUN are
  valid conclusions; nobody is required to find a "winner".
- Tuning ONLY on rolling-origin TRAIN-INTERNAL folds whose games are known before
  the target games. Never use: target-game data, post-capture odds, paper results,
  or any already-exposed OOS to choose features, parameters, thresholds or stakes.
- Log loss is PRIMARY; Brier, calibration slope/reliability, per-season/per-fold
  results and paired ΔLL + CI are SECONDARY; soccer adds RPS. Baseline and
  candidate are always scored on the IDENTICAL game set; missingness and power
  are reported. Designed-null, shuffled twin and reproduction checks apply.
- Two questions are kept SEPARATE: (1) is the probability better than the
  baseline; (2) does that probability make better DECISIONS on real timestamped
  odds. A log-loss win is never called a betting edge; synthetic/proxy odds are
  sensitivity analysis only.
- Every previously-exposed experiment stays EXPOSED/DIAGNOSTIC forever; it is
  never re-labeled fresh OOS.

## Inheritance (all re-measured from bytes at bootstrap 2026-10-08; cite-only)

- **NBA** — NBA-WINPROB-NG-SCORED-V1 TERMINAL (registry head a76dadb1, run
  final c17af775, FINAL_STATUS.json): B1* = own-Elo K=32/HCA=100/γ=0.75;
  OOS 2022–2026 pooled LL **0.639953** n=6,605, slope **0.8107** (below the
  [0.85,1.15] band → overconfident; standing disclosure). Warm-up 2016–2017;
  TRAIN-INTERNAL SELECTION = 2018–2021 (folds SEL-F1..SEL-F4, cutoff
  2021-08-01T00:00:00Z); OOS folds F1..F5 = [2022..2026]; PROSPECTIVE 2026–27+.
  Dead arms (never resurrected by renaming): additive logistic-over-Elo feature
  layers, MOV/blowout Elo, K/HCA/rest/form re-grids on 2009–2015 (spent window),
  538 forecasts, market odds as features, current-game box scores,
  player-feature and team-feature UN_SCORED arms of NBA-PLAYERFEAT-SCORED-V1.
  Live paper forecast for NBA is owned by NBA-WINPROB-PROSPECTIVE-PREP-V1
  (head 82542aa8) — read-only to this cycle.
- **WNBA** — B1-WNBA verbatim K=32/HCA=50/γ=0.65; OOS 2020–2026 LL **0.611603**
  n=1,773, slope 1.0467 (WNBA-PLAYERFEAT-SCORED-V1 TERMINAL 73c0315a). Burned
  evidence: AMD1 Annex R (23/24 trials) AND WNBA-WINPROB-IMPROVE-PREP-V1
  TERMINAL f5bf73e (H-EFF-P +0.001240 CI [−0.000348,+0.003047]; H-SCHED
  +0.000515 CI [−0.000464,+0.001492]; H-EFF primary NOT_RUN_RIGHTS_PENDING_OWNER;
  H-STATUS NOT_RUN_PIT; LOCKED_KEEP_B1). 2020–2026 is EXPOSED diagnostic —
  never a selection surface; honest selection evidence is ≤2019 only. Engine
  pins arms.py 82263eab…/harness.py b9446f76…/feature table ceaf10ba…/crosswalk
  e4115f04…. WNBA-WINPROB-PROSPECTIVE-PREP-V1 (9ed717c4, GO
  REGISTERED_NOT_CONSUMED) owns 2027+ confirmation — amendment path only,
  owner-only; untouched here.
- **SOCCER** — SOCCER-INTL-WINPROB-SCORED-V1 TERMINAL 6d3e659b (report
  21ae40f8): chrono OOS [2001-01-01, 2023-01-01) n=20,708 3-way: B0 1.049906,
  **B1 (Elo/Davidson) 0.912037**, **V1 (HCA=80) 0.909325**; ΔLL V1−B1 −0.0027
  does NOT by itself prove V1 superiority. Same-day exclusion as-of law proven
  in SOCCER-INTL-WINPROB-PREP-V1 (27bb57f2); kickoff times never fabricated.
  Held-out 2023+ is PARTIALLY REVEALED — never again a clean holdout. Target
  corpus records the 90/120-minute score; the market 1X2 is 90 minutes — the
  compatibility question is THIS cycle's check. Prospective chain:
  SOCCER-INTL-WINPROB-PROSPECTIVE-PREP-V1 (1ca5cd7d, B1 K=48/ν=0.6/HCA=65,
  wired read-only into SPORTS-PAPERTRADE-EXEC-V1) + SOCCER-APIFOOTBALL-PREP-V1R3
  (9c239eec, odds probe) — untouched.
- **NFL** — NFL-WINPROB-WALKFWD-V1 ACTIVE_LIGHT 0/3 at a938ba1: owner GO was
  typed 2026-10-07T13:38Z, Phase R ledger 7,840 rows pinned a94830e1…, Phase S
  halted **PHASE_S_MACHINERY_SUSPECT** (event log 14:45Z): REPLAY_CONSISTENCY
  FAIL |d|=9.81e-3 vs the B1-c anchor 0.6407 (0/7 seasons); documented root
  cause: predecessor NFL-WINPROB-SCORED-V1 fold machinery is REG-only /
  ties-excluded / per-season expanding (n_train 4839+255/271/…) vs the frozen
  continuous REG+POST tie-S=0.5 walk. C3 therefore has NO valid verdict; 0.6407
  is an exposed predecessor anchor, not a target to chase. 2019–2025 is
  program-spent (EXPOSED); B1 diagnostic 0.650520 is exposed. Prospective NFL
  2026 and the weeks 5–7 ledger (129 rows, chain head 67e89b2e) belong to
  NFL-WINPROB-NG-SCORED-V1 — read-only citation, never backfilled or reforecast.

## Lane scopes (owner-ordered)

1. **L-NBA** — re-verify B1* from bytes; one simple calibration mechanism
   hypothesis frozen before measurement (e.g. a single logit shrink/temperature
   coefficient), fitted/selected ONLY inside selection folds 2018–2021 via a
   nested time evaluation; the fitted coefficient is frozen, then OOS 2022–2026
   is QUOTED (retrospective disclosure, never a coefficient input, never new
   OOS). No resurrection of killed/UN_SCORED player-feature or team-feature arms
   under new names. Write the prospective 2026–27+ protocol; do NOT modify the
   running paper forecast.
2. **L-WNBA** — read WNBA-WINPROB-IMPROVE-PREP-V1 in full; no re-running of
   burned grids. As-of error diagnostics on 2020–2026 (playoff vs early-season
   vs mismatch segments) are EXPOSED diagnostic only, never model selection.
   Propose a NEW mechanism only if a $0 source with rights AND pre-tip
   timestamp/PIT evidence is proven from bytes; otherwise KEEP_B1 plus a fresh
   prospective-check design (that design goes through the owner, never into the
   running paper).
3. **L-SOCCER** — check target-corpus compatibility (90/120-minute recorded
   score vs the market 1X2 90-minute definition): identify which games and
   competitions are compatible; if ambiguous → **NOT_RUN_TARGET**; labels are
   never changed after seeing results. The corpus is date-only → the proven
   same-day exclusion law stays. Held-out 2023+ is partially revealed, never a
   clean holdout. Any proposed draw/HCA (or other) tune is selected
   train-internal and frozen BEFORE any new evaluation; the running soccer paper
   is not modified.
4. **L-NFL** — no new LL OOS claim. Write a STANDALONE successor remediation
   plan that resolves the predecessor-vs-NG machinery difference (REG-only /
   ties-excluded / per-season expanding vs REG+POST / tie=0.5 continuous),
   self-anchoring on exactly the machine NG used to select C3, with
   designed-null/twin and an explicit estimand definition; NO "fix the machine
   to chase 0.6407 after seeing results". 2019–2025 is EXPOSED at program level;
   the B1 diagnostic 0.650520 is exposed; C3 has no valid verdict. Prospective
   NFL 2026 and the weeks 5–7 ledger are another cycle: read-only, no backfill,
   no reforecast.
5. **L-VERIFY** — independent fresh-context verifier, dispatched LAST on
   integration HEAD, audit namespace only, never repairs: re-measures hashes,
   PIT, rights, split/exposure labels, trial budget, null/twin, no-OOS-selection,
   no paper mutation (SPORTS-PAPERTRADE-EXEC-V1 ledger + NFL NG weeks 5–7 chain
   byte-unchanged), heavy lock and registry/head coherence. Reports
   **PASS / FAIL / NOT_RUN PER LEAGUE** — never a single aggregated "GO-ready"
   label for all four.

## Assembly deliverables (controller, at integration)

- `FOUR_LEAGUE_TABLE.md`: per league — baseline, data/rights, exposed parts,
  still-valid hypotheses, TRAIN-INTERNAL results, blockers, recommendation
  KEEP / TUNE / HOLD.
- `FREEZE_PACKET_<LEAGUE>.md` ×4 + trial budget for each scored successor +
  an explicit statement of which new-evidence windows truly remain usable
  (per league; expected: prospective-only almost everywhere).
- `SHADOW_ODDS_RECON_PLAN.md`: per-league plan to reconcile probabilities
  against REAL timestamped odds in shadow mode; no change to any running paper
  order; quota/keys of SPORTS-PAPERTRADE-EXEC-V1 untouched.
- `PREP_VERDICT.md` → terminal outcome; `DIAGNOSTIC_TRIAL_LEDGER.jsonl`
  (append-only merge of per-lane ledgers; mechanism-fit rows capped ≤2 per
  league; null/twin/parity rows logged with class=CONTROL and do not consume the
  mechanism cap); `A7_PREP_AUDIT.md` (verifier).

## Hard boundaries (all lanes)

$0; no accounts/keys/tiers/purchases; ZERO scored cells (scored counter 0/0);
no real-game probability for any unplayed game; no GO exists; no S1; no
push/merge/rebase/history-rewrite; TERMINAL cycles' artifacts/ledgers and the
running SPORTS-PAPERTRADE-EXEC-V1 + NFL-WINPROB-NG-SCORED-V1 programs are
READ-ONLY (citation with sha; byte-unchanged); registry writes only via
researchctl (CAS; on conflict re-measure + retry, never overwrite); missing
evidence = NOT_RUN_*, never inferred PASS; calibration/forecasting vocabulary
only (no PnL/betting/edge claims); WNBA constants never transported to another
sport; root-level `.my-quantitative-data/` is FOREIGN — never read. Data bytes
stay OUTSIDE git: reads from the existing HOME-level stores
(`~/.my-quantitative-data/nba-*`, `wnba-*`, `soccer-*`, `nfl-*`), new derived
bytes only under `~/.my-quantitative-data/sports-winprob-tune-prep-v1/<lane>/`
with sha256 manifests. Heavy runs take the machine-wide heavy lock
(`governance.heavy_lock.acquire`; refusal → one bounded recheck ≥60s →
NOT_RUN_RESOURCE_CONFLICT; never spin, never kill foreign workers; expected
compute is light, <2 min).

## Worktrees / branches (created from the plan-commit HEAD on main)

- integration `.worktrees/sports-winprob-tune-prep-v1/integration` on
  `orca/spt-tune-prep-v1-integration`
- lanes `…/lane-nba|lane-wnba|lane-soccer|lane-nfl` on
  `orca/spt-tune-prep-v1-lane-nba|lane-wnba|lane-soccer|lane-nfl`
- lanes write ONLY `research/control/SPORTS-WINPROB-TUNE-PREP-V1/lanes/<LANE>/`
  + `handoffs/<lane>.json` in their own worktree; no git from lanes — the
  controller lands commits by pathspec (NBA-WINPROB-PREP-V1 precedent).

## Gate sequence

plan commit (this commit) + `researchctl cycle register` (CAS, budget-max 0, no
GO phrase) → worktrees → dispatch packets + handoff paths → L-NBA ∥ L-WNBA ∥
L-SOCCER ∥ L-NFL (independent, disjoint paths) → handoff validation
(`zcode_orch_v3_handoff@1` at each handoff_path) → sequential cherry-pick into
integration → controller assembly (four-league table + freeze packets + shadow
odds plan + verdict) → L-VERIFY fresh-context on integration HEAD → owner
report → stop at PREP_COMPLETE_PENDING_OWNER_SCORED_DECISION.

## Terminal outcomes (negative-first)

**PREP_COMPLETE_PENDING_OWNER_SCORED_DECISION** (expected stop: packets
complete; scored successors unregistered; NO GO created or consumed) |
PREP_PARTIAL_<gap> | NOT_RUN_TARGET_<league> | NOT_RUN_PIT_<league> |
BLOCKED_DATA_RIGHTS | NOT_RUN_RESOURCE_CONFLICT | TECHABORT_*. Every scored
successor needs its own owner instruction, plan, registration and gate; this
cycle never mints one.
