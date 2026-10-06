# PLAN — SPORTS-WINPROB-DISCOVERY-PREP-V1 (multi-sport win-prob DISCOVERY + DATA QUALIFICATION + PREP, $0)

- cycle_id: SPORTS-WINPROB-DISCOVERY-PREP-V1 · asset: shared · budget 0/0
  (ZERO scored cells — none are possible in this cycle) · registered 2026-10-06.
- owner authority 2026-10-06 (this chat): explicit instruction to expand the
  pre-match win-probability research line (NBA / WNBA / NFL precedent) to as
  many feasible sports and competitions as possible. This round is
  **DISCOVERY + DATA QUALIFICATION + PREP ONLY**: inventory with evidence,
  realistic qualification (sample then full corpus where size/sanity allow),
  per-league forecast-target design, feasibility ranking, PREP packets for a
  shortlist. It is explicitly **NOT** an authorization for scored execution,
  new OOS, real forecasts of any real game, or any GO.
- Overlap fence (owner): NBA, WNBA and NFL are EXCLUDED from survey scope —
  they are owned by live cycles (NBA-WINPROB-*-V1, WNBA-WINPROB-*-V1,
  NFL-WINPROB-*-V1 and their successors). This cycle never touches their
  worktrees, ledgers, registries, data dirs or automations.
- This cycle has **NO GO phrase and no scored-execution phase**: it ends in a
  report + proposals. Successor cycles (one per shortlist league, umbrella
  PREP where justified) are PROPOSED here and REGISTERED only later, each by
  its own owner instruction. Mass scored registration is forbidden.

## Hard boundaries (all lanes)

$0; no account creation, no API keys, no tier upgrades, no quota evasion; no
scored/OOS computation; no real-game probability anywhere; no S1; no paper/
live/betting language; no push, no merge, no rebase, no history rewrite; no
writes to other cycles' frozen artifacts/ledgers/registries; no credentials
already present in prompts/logs/git; missing evidence = NOT_RUN (or
TBD_PREP), never inferred PASS; language law: calibration/forecasting
vocabulary only. WNBA constants (K=32/HCA=50/γ=0.65) are cycle-inheritance
and are NEVER transported to another sport; every design here is per-sport
and built from that sport's own data/mechanism.

## Data plane

Bulk bytes live OUTSIDE git under
`~/.my-quantitative-data/sports-winprob-discovery-v1/<source_id>/…` with a
per-source `manifest.json` (sha256 per file, size, retrieval URL, retrieval
UTC, license URL + verbatim license snippet, attribution string) and
`ATTRIBUTION.md`. Only manifests/code/reports enter the worktree. The
root-level `.my-quantitative-data/` directory is FOREIGN content (owner
rule, WNBA plan precedent): never read, never bundled. Politeness: light
fetches only (≤10 MB per source per lane run, sequential, identify a UA
string, back off on 429/5xx); anything larger or slower than ~2 minutes
takes the machine-wide heavy lock via
`governance.heavy_lock.acquire(cycle_id=…, role=…, worktree=…, command=…)` —
refusal = NOT_RUN_RESOURCE_CONFLICT, never spin, never kill foreign workers.

## Lanes (worktree per agent; integration is controller-only)

1. L0 `lane-sources` — CROSS-SPORT SOURCE + RIGHTS INVENTORY (web evidence,
   no bulk download): for every sport group below, enumerate candidate free
   sources (repo URL, license bytes, underlying-data rights separately,
   update cadence, historical depth, format, cost/limits) and classify each
   `DOCUMENTED_CANDIDATE → AUTHORIZED_INTERNAL_RESEARCH (internal research
   only) | UNAVAILABLE_FAIL_CLOSED | REJECTED_LICENSE`. Free ≠ authorized.
   Output: SOURCE_INVENTORY.md + RIGHTS_MATRIX.csv (evidence: URL + quote +
   date for every rights claim).
2. L1 `lane-soccer` — ASSOCIATION FOOTBALL (men + women): top domestic
   leagues (EPL/La Liga/Serie A/Bundesliga/Ligue 1 + at least 3 more),
   continental cups (UCL/UEL), World Cup; women (WSL/D1 Arkema + available
   analogues). Candidate seeds (verify, then widen): football-data.co.uk
   CSV archives, openfootball GitHub, martj42 international-results GitHub.
   3-way (home/draw/away) targets; draw handling law per league.
3. L2 `lane-hoops` — BASKETBALL OTHER THAN NBA/WNBA: NCAA D1 men + women,
   Euroleague, FIBA windows, other leagues if free corpus exists. 2-way.
4. L3 `lane-bathock` — BAT-AND-BALL + ICE: MLB, NPB, KBO (if corpus), NHL,
   other hockey leagues if free corpus. 2-way.
5. L4 `lane-racquet` — RACQUET + FIELD: tennis ATP/WTA/Challenger (2-way
   match target), cricket (international/T20 leagues, cricsheet et al.),
   rugby union/league, volleyball, plus one wild-card sport if a corpus
   exists. Match/team targets per sport law.
6. L5 `lane-verify` — INDEPENDENT VERIFIER (quant-auditor, fresh context,
   dispatched LAST against integration HEAD; writes audit namespace only,
   never repairs): re-measures league counts vs manifests, re-reads license
   bytes for every AUTHORIZED claim, re-checks hashes on spot samples,
   re-checks PIT/as-of claims (pre-match feature law), boundary compliance
   (0 scored cells, no forecasts, $0, no WNBA constants transported,
   registry coherence), and critiques the ranking/shortlist. Verdict
   PASS / PASS_WITH_FINDINGS / FAIL with per-claim evidence.

Lanes L1–L4 per league, minimum evidence set: sport, competition, seasons/
years covered, finished-game count n (measured from downloaded bytes, not
vendor-stated), teams/participants, future schedule availability, update
cadence, source URL/version/hash, cost/account/limit evidence, repo license
AND underlying-data rights separately, provenance (who publishes, how),
re-downloadability (deterministic?). Qualification checks: byte hash vs
manifest, schema drift across seasons, duplicate game IDs, postponed/
cancelled/neutral/playoff/draw/tie handling, timezone of timestamps,
final-score sanity, schedule↔result join rate, per-season coverage,
missingness profile, identity crosswalk (team name → canonical id).
Design targets (DESIGN, not computed): target type, strictly pre-match
feature set with as-of/publish-time law, warmup/train/chronological-OOS/
prospective splits, log loss/Brier/calibration metrics, baseline comparator
(B0 train-internal constant; B1 per-sport Elo/Bradley-Terry sketch — sport's
own K/HCA/home-advantage estimation, never WNBA's), null-test design, trial
budget, leakage gates, operational cadence. Lanes L1–L4 compute ONLY
descriptive QC statistics; no model fitting, no probability computation, no
baseline constants — those belong to each successor cycle's own gates.
Per-league verdict vocabulary: PASS / CONDITIONAL / FAIL / NOT_RUN (+
NOT_RUN_RESOURCE / NOT_RUN_SOURCE / NOT_RUN_RIGHTS with a concrete size or
blocker estimate). Data maturity vocabulary (report exactly one):
inventory-only | sample-validated | full-data-qualified | PREP-complete.

## Gate sequence

plan commit + `researchctl cycle register` (CAS, this tree) → worktrees
created (integration + lanes) → task registration + dispatch packets →
lanes L0–L4 (parallel, independent trees) → handoff validation
(zcode_orch_v3_handoff@1 at each handoff_path; store + git + test re-run) →
sequential cherry-pick into integration → controller assembly
(DISCOVERY_RANKING.md, SHORTLIST.md, per-league PREP_PACKET_*.md) →
independent verifier L5 on integration HEAD → owner report → cycle TERMINAL
close (two-half: integration chain + control-plane landing). Registry writes
only via researchctl (CAS); on conflict re-measure + retry, never overwrite.

## Artifacts

`research/control/SPORTS-WINPROB-DISCOVERY-PREP-V1/` in each worktree:
`DISPATCH/` (packets + task records), `handoffs/` (one JSON per lane),
`lanes/<LANE>/` (reports, manifests, designs), and at integration:
`DISCOVERY_RANKING.md`, `SHORTLIST.md`, `PREP_PACKET_*.md`,
`A7_DISCOVERY_VERDICT.md`. Data bytes + manifests-of-record live under
`~/.my-quantitative-data/sports-winprob-discovery-v1/` (outside git);
worktree copies of manifests are the git-visible evidence.

## Terminal outcomes (negative-first)

DISCOVERY_PREP_COMPLETE_PROPOSALS_ONLY (clean close; successors proposed,
NOT registered) | DISCOVERY_THIN_<n>_QUALIFIED (honest thin close) |
NOT_RUN_RESOURCE_CONFLICT | BLOCKED_DATA_RIGHTS | TECHABORT_*. No GO exists
for this cycle; every successor cycle needs a fresh owner instruction, its
own plan, its own registration and its own gate.
