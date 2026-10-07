# PLAN — WNBA-WINPROB-IMPROVE-PREP-V1 (WNBA win-prob improvement PREP, $0)

- cycle_id: WNBA-WINPROB-IMPROVE-PREP-V1 · asset: shared · budget 0/0 (ZERO scored
  cells; diagnostic trials live only in this cycle's own ledger) · registered 2026-10-07.
- owner authority 2026-10-07 (this chat): explicit instruction to run a WNBA
  win-probability IMPROVEMENT PREP round, max three mechanism hypotheses, with data /
  PIT-rights / mechanism / independent-verifier lanes and per-lane
  `zcode_orch_v3_handoff@1` handoffs. Primary metric **log loss**; Brier, calibration
  and pick accuracy are reported, never optimized alone. This instruction is
  explicitly **NOT a typed GO**: no real forecast of any real game, no scored cells,
  no betting language, no S1, no purchases, no push/merge/rebase.
- Baseline (immutable frozen inheritance, NEVER recomputed as a verdict):
  **B1-WNBA verbatim (own-Elo K=32/HCA=50/γ=0.65; pooled OOS 2020–2026 LL 0.611603,
  n=1,773)** from TERMINAL WNBA-PLAYERFEAT-SCORED-V1 (head 73c0315a; B0 floor
  0.603755; ΔLL vs B0 −0.085856 CI [−0.103702,−0.067931]). Engine byte pins:
  `arms.py` 82263eab…, `harness.py` b9446f76…; feature table ceaf10ba… (826,415 B);
  crosswalk e4115f04…; ATTRIBUTION.md 1068e5c7… — all re-hashed MATCH at
  registration (2026-10-07, live bytes).
- Preserved cycles (read-only inheritance): WNBA-PLAYERFEAT-SCORED-V1 TERMINAL at
  73c0315a; WNBA-WINPROB-PROSPECTIVE-PREP-V1 PRELAUNCH_READY_PENDING_OWNER_GO at
  9ed717c4 (GO phrase `GO WNBA WINPROB PROSPECTIVE V1 PREDICTIONS`
  REGISTERED_NOT_CONSUMED belongs to THAT cycle, not this one). B1 results/params are
  never modified by this cycle.

## Prior-round boundary (what is burned)

AMD1 Annex R (23/24 diagnostic trials: H2 margin-of-victory + recency, CAL
recalibration, H3 roster/continuity priors) is **burned evidence** — every pooled
ΔLL CI includes 0; improvement below 0.611603 is HYPOTHESIS-unsupported. The three
families below are NEW mechanisms and must not re-litigate burned families
(novelty/ancestry law). Seasons 2020–2026 and all 23 prior trials are EXPOSED: any
further computation touching them is **RETROSPECTIVE DIAGNOSTIC — NOT OOS** and is
labeled as such on every artifact. Honest selection/lock evidence comes from
evaluation seasons **≤ 2019** ONLY; the lock rule below may never read 2020–2026.

## Hypotheses (owner-ordered; ≤3; each gated before any trial runs)

- **H-EFF — team strength as offensive/defensive efficiency per 100 possessions**,
  opponent-adjusted, shrunk toward league mean at low sample counts; rolling from
  COMPLETED games only. Primary build needs multi-season team box scores
  (FGA/ORB/TO/FTA → possessions); release store carries 2025–2026 only, so seasons
  2002–2024 require a $0/no-auth ESPN public-API per-season pull (same channel class
  as the stored 2002–2026 schedules) under the machine-wide heavy lock, provenance
  URL+timestamp+sha256 per file. Fail-closed: measured per-season field coverage; if
  possessions inputs are unavailable for a season, that season drops out (measured
  join rate) and the family may be NOT_RUN_COVERAGE — with one pre-registered
  degraded variant (points-based eff, existing bytes only) disclosed, never
  substituted silently. Forbidden: any stat from the target game or from any game
  not completed before the forecast time.
- **H-SCHED — calendar: rest days, game density, travel, neutral site**, built ONLY
  from played games (facts known once completed) + conservative tip-lag exclusion.
  The schedule store (2002–2026, venue/city/neutral_site/tip-UTC columns) is local.
  As-of law: features for game g use only games with tip_utc + LAG ≤ tip_utc(g)
  (LAG conservative, pinned in freeze). Reschedule-announcement timing is NOT
  evidenced in any held bytes: an "announced-but-unplayed schedule as known at
  forecast time" variant is therefore NOT_RUN_PIT (never built). Neutral site has
  only ~6 universe rows — disclosed, never a spec driver.
- **H-STATUS — key player status / expected lineups**: GATED. Opens only if a $0
  source with suitable rights AND archived publish timestamps strictly before each
  game's tip is proven from bytes. Known candidate sources (WNBA.com injury reports,
  news feeds) carry no timestamped historical archive in held stores; the lane must
  run and document a real search, then either prove the gate or record
  **NOT_RUN_PIT**. The target game's own lineups/DNP are forbidden as features,
  always.

For each hypothesis the data lane records one table row set: source, rights,
time coverage, join rate vs the frozen 7,010-row stream (warm-up 1,022 + universe
5,988), publish-timestamp evidence, expected mechanism, leakage risk, and a
falsifiable test.

## Design (pre-registered; simple first, variants capped)

- Rolling-origin walk-forward mirroring AMD1 §R.3: origins 2006–2026 pinned;
  selection per origin uses ONLY the 4 immediately-prior universe seasons;
  ties → parent; stream state continues chronologically from the 1997 warm-up.
- Parity law BEFORE any trial: (i) frozen B1-verbatim replay must match the closed
  run's `predictions_b1_wnba.csv` p_home_hex bit-for-bit on 2020–2026; (ii) the
  augmented engine with feature scaffolding but zero features must be bit-identical
  to B1-verbatim prediction-by-prediction on all 7,010 rows. Any mismatch ⇒
  BLOCKED_TOOLING, nothing runs.
- Metrics: paired per-game ΔLL vs B1-verbatim (negative favors the arm), tip-date
  cluster bootstrap 10,000 resamples, **seed 20261007 pinned once for this cycle**,
  95% percentile CI, per-origin + pooled; honest window (evaluation seasons ≤ 2019)
  and exposed window (2020–2026, retrospective label) reported separately; Brier,
  10-bin reliability, calibration slope, pick accuracy reported alongside.
- **Lock rule (fixed before any run)**: a family locks a spec only if its pooled
  honest-window ΔLL CI excludes 0 and is negative (beats B1), AND its effect
  exceeds the capacity note (pooled |ΔLL| < ~0.01 is INCONCLUSIVE — stated, not
  stretched); otherwise the cycle locks **KEEP_B1**. 2020–2026 results are never an
  input to this rule.
- Trial budget: pre-registered ≤12 specs (≤6 H-EFF, ≤6 H-SCHED) + ≤6 conditional
  H-STATUS if its gate opens; hard cap 24 diagnostic trials total in this cycle's
  append-only `DIAGNOSTIC_TRIAL_LEDGER.jsonl` (deviation = new logged trial; no
  silent retries). Scored budget stays 0/0.
- Linkage: any locked mechanism spec can reach the released slots 3–9 of
  WNBA-WINPROB-PROSPECTIVE-PREP-V1 ONLY via a future owner-authorized amendment to
  THAT cycle; confirmation evidence is prospective 2027+ forecasts recorded
  pre-tip and paired against B1 under the successor's own typed GO. This cycle
  runs none of that.

## Lanes (worktree per lane; integration controller-only)

1. L-DATA `lane-data` — SOURCE TABLES + REFRESH: re-hash inherited pins; build the
   per-hypothesis source/rights/coverage/join/timestamp/mechanism/leakage/falsifier
   tables; pull espn_wnba_team_boxscores seasons 2002–2024 ($0, no auth, heavy lock,
   politeness caps, per-file sha256 + provenance) into
   `~/.my-quantitative-data/wnba-winprob-improve-prep-v1/`; measure per-season field
   coverage + join rate vs the frozen stream; refresh-provenance manifest. No
   feature computation.
2. L-PIT `lane-pit` — RIGHTS + AS-OF LAWS: (a) rights from LOCAL bytes + any new
   pull ($0 evidence); (b) prove the efficiency as-of law (completed-games +
   tip-lag exclusion; mutation test proves late-arriving stats cannot touch earlier
   forecasts); (c) prove the schedule as-of law (played-games-only; same-day/lag
   exclusion; reschedule disclosure; announced-schedule variant = NOT_RUN_PIT);
   (d) run + document the H-STATUS source search; verdict per family:
   PIT_PASS or NOT_RUN_PIT with the exact reason. Laws bind L-MECH designs.
3. L-MECH `lane-mech` — MECHANISM + EVALUATION (gated by L-PIT verdicts): parity
   harness first; pre-registered spec sets (additive-argument continuity with the
   frozen engine, like the closed cycle's arg law; no engine re-tuning); run the
   walk-forward under the heavy lock; maintain the diagnostic trial ledger; apply
   the lock rule; produce LOCKED_<spec> or LOCKED_KEEP_B1 with the full PASS/FAIL/
   NOT_RUN table.
4. L-VERIFY `lane-verify` — INDEPENDENT VERIFIER (fresh context, dispatched LAST on
   integration HEAD; writes audit namespace only, never repairs): re-measure
   coverage/join numbers from bytes, re-run parity anchors, attack both as-of laws
   (hunt a leak or unprovable step), re-verify trial ledger arithmetic + cap,
   boundary compliance ($0, no GO, no scored cells, other cycles untouched,
   registry coherent). Verdict PASS / PASS_WITH_FINDINGS / FAIL.

## Hard boundaries (all lanes)

$0; no accounts/API keys/paid tiers; no scored computation on any window (scored
counter 0/0; diagnostic trials only in this cycle's ledger); no real-game
probability for any 2027+ game; no GO (this cycle has none); no S1; no
push/merge/rebase/history-rewrite; no writes to other cycles' artifacts/ledgers/
registries (WNBA-PLAYERFEAT-SCORED-V1 frozen at 73c0315a; WNBA-WINPROB-PROSPECTIVE-
PREP-V1 frozen at 9ed717c4 — both read-only); root checkout = control plane; lane
work only in the exact worktrees/branches named below; registry writes only via
researchctl (CAS; on conflict re-measure + retry, never overwrite); data bytes
outside git under `~/.my-quantitative-data/wnba-winprob-improve-prep-v1/` with
sha256 manifests; ROOT-LEVEL `.my-quantitative-data/` is FOREIGN — never read;
heavy runs take the machine-wide lock (refusal = NOT_RUN_RESOURCE_CONFLICT; never
kill foreign workers); missing evidence = NOT_RUN_*, never inferred PASS.

## Worktrees / branches

Integration: `.worktrees/wnba-winprob-improve-prep-v1/integration` on
`orca/wnba-winprob-improve-prep-v1-integration`. Lane worktrees under the same
directory: `lane-data`, `lane-pit`, `lane-mech`, `lane-verify` on
`orca/wip-v1-lane-data`, `orca/wip-v1-lane-pit`, `orca/wip-v1-lane-mech`,
`orca/wip-v1-lane-verify`.

## Gate sequence

plan commit (this commit) + `researchctl cycle register` (CAS) → worktrees →
dispatch packets + handoff paths → L-DATA ∥ L-PIT → L-MECH (consumes L-PIT
verdicts; freezes subject to them) → handoff validation (`zcode_orch_v3_handoff@1`)
→ sequential cherry-pick → controller assembly (SOURCE_TABLES.md, PIT_VERDICT.md,
MECH_REPORT.md + lock decision, PREP_VERDICT.md) → L-VERIFY on integration HEAD →
owner report → TERMINAL close (two-half). Stop before GO, always.

## Artifacts

`research/control/WNBA-WINPROB-IMPROVE-PREP-V1/` in each worktree: `DISPATCH/`,
`handoffs/`, `lanes/{L_DATA,L_PIT,L_MECH,L_VERIFY}/`; at integration:
`SOURCE_TABLES.md`, `PIT_VERDICT.md`, `MECH_REPORT.md`, `PREP_VERDICT.md`,
`DIAGNOSTIC_TRIAL_LEDGER.jsonl` (append-only), `A7_PREP_AUDIT.md` (verifier).
Data + manifests under `~/.my-quantitative-data/wnba-winprob-improve-prep-v1/`.

## Terminal outcomes (negative-first)

PREP_COMPLETE_LOCKED_KEEP_B1 (no family beats B1 on the honest window — the
expected outcome; never force an arm) | PREP_COMPLETE_LOCKED_<spec>_HYPOTHESIS
(honest-window CI excludes 0, negative; still HYPOTHESIS until 2027+ confirmation
under the successor's own GO) | PREP_PARTIAL_<gap> | NOT_RUN_COVERAGE_<family> |
NOT_RUN_PIT_<family> (stated, never silently) | BLOCKED_DATA_RIGHTS |
NOT_RUN_RESOURCE_CONFLICT | TECHABORT_*. No GO phrase exists for this cycle; any
successor's GO is typed only by the owner at that successor's own gate.
