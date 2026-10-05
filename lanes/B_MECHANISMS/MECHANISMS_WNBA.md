# MECHANISMS_WNBA — Lane B, WNBA-WINPROB-PREP-V1 (fresh-league mechanism adjudication)

- lane: B_MECHANISMS · task: wbap-b-mech · date: 2026-10-05 · owner round 2026-10-05
- scope: research + protocol design ONLY. No downloads, no outcome computation, no git
  operations, no edits to any frozen artifact. This document proposes; it authorizes nothing.
- language law (inherited): calibration/forecasting vocabulary only — no PnL/betting/edge.
- worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/wnba-winprob-prep-v1/integration`
  · branch `orca/wnba-winprob-prep-v1-integration` · dispatch_sha (measured HEAD at lane
  start) = `673b4f27e4abdefc5c54839febac29185dd6e794`

## 0. Independence law (load-bearing) and evidence base

WNBA is a FRESH program on its OWN data. No NBA data, hypothesis, parameter, or verdict is
WNBA evidence. Every NBA/NFL number in this document is CITED as cross-league context that
shapes priors and design inheritance — never imported as WNBA proof. The NBA spent-window
prohibition (2009–2015) does not bind WNBA windows, but the same train-only discipline does:
every WNBA parameter is selected train-internal and frozen before any evaluation look.

Evidence inputs (read-only, immutable history):

1. `winprob-ng-prep-v1` lane C `MECHANISMS.md` — H-C5 (continuity-modulated carryover) + F10
   + the terminal-cycle fact base (NBA B1* K=32/HCA=100; NFL B1* K=40/HCA=0; additive
   logistic-over-Elo layers T1-FAIL in both leagues; calibration machinery).
2. `winprob-ng-prep-v1` lane B `WNBA_SOURCE_AUDIT.md` — VERDICT PASS (data layer): wehoop/
   sportsdataverse release store as PRIMARY; ESPN schedules 2002–2026 (6,029 rows), stats-side
   schedules 1997–2026 (7,009 rows, 100% scored rows), 2025 box/pbp sample; rename map;
   timezone flavors; filter law; NOT_RUN_PIT story; rights table.
3. Plan `plans/PLAN_wnba_winprob_prep_v1.md` + dispatch `lanes/DISPATCH/DISPATCH_B_MECHANISMS.md`.
4. Lane A of THIS cycle: `../A_DATA/` contained ONLY `measure_a.py` (in-flight measurement
   script) at lane start — no spec, no census, no PIT audit, no handoff. Dependency status:
   **PENDING_LANE_A**; this lane proceeds from the plan + the prior cycle's lane-D-verified
   corpus facts and flags every claim that Lane A's census supersedes on landing.

## 1. Corpus facts this lane builds on (coverage counting from the prior cycle's audit, verified by its lane D; Lane A re-measures)

- Results (scores) exist for ALL seasons 1997–2026: stats-side schedules carry
  `home_pts`/`away_pts` on 100% of played rows; ESPN schedules carry scores with
  `status_type_state=='post'` marking played. Unplayed rows are pre-filled 0–0 — never
  filter on score presence.
- Per-season ESPN rows: 2002:272 … 2019:221, 2020:147 (COVID "Wubble", a real season),
  2021:211, 2022:241, 2023:263, 2024:264, 2025:312 (288 type-2 + 24 playoffs), 2026:360
  (incl. TBD if-necessary placeholders; season in progress at owner round).
- Modern RS ≈ 220–260 games/season pre-2025; ~25 usable seasons ⇒ ≈ 5.1k RS games in the
  2002–2025 core window; ≈ 6.0k adding 1997–2001 (stats-side results, ≈950 RS rows). The
  dispatch's "≈5.5–6k" is the full-history upper range; the core-window number is ≈5.1k.
- Filter law (mandatory, Lane A applies with measured counts): keep
  `status_type_state=='post'`; drop the single Forfeit (2018-08-03, recorded 0–0) and
  Postponed rows; drop/flag All-Star alias rows (EAST/WEST/ALL/DEL/PAR/CLA/COOP/WNBASTARS);
  drop TBD placeholders; Commissioner's Cup rows (2021+, embedded in RS) flagged for a
  separate report; playoffs (`season_type=3`) separate; 2020 kept as real.
- Franchise rename/relocation spine (stats-side abbreviations stable; join via
  display_name / `wnba_crosswalk`, NEVER raw ESPN abbreviations — measured unreliable
  pre-2011, incl. the 2002 all-16-Detroit-rows-labeled-`TUL` artifact): UTA→SAN→DAL;
  ORL→CON; DET→TUL→(merge into DAL 2016); LAS→LVA 2018; defunct CHA/CLE/HOU/SAC/MIA/POR;
  expansion ATL 2008, CHI 2006, GSV 2025, TOR+PDX 2026.
- Roster assets: `espn_wnba_game_rosters` release (2002–2026, 29.0 MB) NOT yet pulled;
  2025 player_box sample: `starter` median 10.0 rows/game (= 5v5 derivable), 1,224 DNP rows,
  `active`/`did_not_play`/`starter`/free-text `reason` fields — all POST-GAME facts.
- PIT story: release assets are current-state snapshots with NO publication-time columns.
- Rights: sportsdataverse-data release store — data badge CC BY 4.0 + repo code MIT
  (nflverse-family pattern; internal research use with `ATTRIBUTION.md`; maintainer
  confirmation required only before external redistribution); NO direct scraping of
  wnba.com / stats.wnba.com / ESPN; Sports Reference FAIL 5(11); balldontlie WNBA
  BLOCKED_NO_KEY (+ paid for modeling-relevant endpoints); no 538, no market odds.

## 2. PIT / rights matrix (WNBA, as of this lane)

| input class | knowable pre-game? | rights | verdict |
|---|---|---|---|
| game results + dates (schedules, both sides) | yes, strictly-prior games only | CC BY 4.0 release store | USABLE (train-only as-of law) |
| season-start roster MEMBERSHIP (`espn_wnba_game_rosters`, first recorded game per team-season) | membership is a season-start fact in the world; asset has no publish timestamps → PIT audit needed | CC BY 4.0 release store (asset not yet pulled) | **PENDING_LANE_A census + PIT audit** (W-H2 gate) |
| player_box `active`/`did_not_play`/`starter`/`reason` | NO — post-game facts | CC BY 4.0 | FORBIDDEN as pre-game features, any arm, any cycle |
| injury/availability feed | n/a | no dedicated feed exists in any wehoop-family release | **NOT_RUN_PIT** (no rights-verified archive with publish timestamps) |
| box scores / PBP (team/player) | post-game compiled | CC BY 4.0 | train-only aggregates only; NEVER current-game |
| 538 forecasts, closing/market odds | banned by plan | — | BANNED |

## 3. Advanced hypotheses (≤3 per dispatch)

Common machinery (inherited shapes, not parameters): log loss primary; Brier + reliability +
calibration slope band [0.85, 1.15] secondary; paired **date-cluster** bootstrap (clusters =
canonical game date under the Lane A tip-UTC law) for all pooled ΔLL CIs; sign convention
**negative ΔLL favors the arm**; evaluated on regular-season games under the filter law,
Cup rows and playoffs reported separately per the Lane C law; train-internal rolling-origin
selection for every free parameter, frozen at successor-cycle registration before any
held-out look.

FROZEN falsifier template (applies verbatim to every arm below): **REJECT iff the pooled 95%
CI of ΔLL(arm, parent) includes 0, or ≥ half of test folds are non-negative** (paired
date-cluster bootstrap). A time-shuffled negative control that also beats its parent
un-scores the candidate pending a machinery audit — that is a fail of the comparison
machinery, not a pass of the mechanism.

---

### W-H1 — Fresh WNBA Elo baseline (B1-WNBA): own train-only K/HCA selection — priority 1

- **Mechanism.** A pairwise win/loss rating with exponential updates is the smallest model
  that converts game outcomes into a calibrated pre-game probability. The WNBA's structure
  (40-game season, ~12 opponents met 3–4×, high roster churn, frequent roster movement)
  predicts faster in-season rating convergence than the NBA's 82-game season and a weaker
  prior-season signal — both are properties of the SAME engine, selected on WNBA data.
- **Operationalization (exact).** Standard Elo with logistic scale fixed by convention:
  `p_home = 1/(1+10^(-(R_home − R_away + HCA)/400))`; update `R ← R + K·(outcome − p)`;
  ratings initialized at league mean 1500 at franchise entry; between seasons carried with a
  GLOBAL shrinkage `R_start = league_mean + ρ0·(R_end_prev − league_mean)` (ρ0 selected
  train-only — this is the parent law W-H2 modulates). Free parameters: **K, HCA, ρ0**,
  selected by rolling-origin grid INSIDE the train sub-window (Lane C defines the split);
  grid must include HCA=0 and bracket generously (e.g. K ∈ [8, 48]; HCA ∈ [0, 150] Elo pts)
  so the data, not a league import, chooses. New-franchise entries start at league mean.
  Era law (1997–2001 stats-side-results-only seasons): Lane C freezes either exclusion from
  feature arms or a schedules-only baseline arm; W-H1 is defined under both variants and
  inherits Lane C's frozen choice.
- **$0 source + rights.** Results feed = `wnba_stats_schedules` (1997–2026) +
  `espn_wnba_schedules` (2002–2026) release assets, sportsdataverse-data store, CC BY 4.0
  badge + MIT repo license; corpus already on disk at `~/.my-quantitative-data/wnba-v1/`
  (EXTEND-ONLY) with sha256 manifest + ATTRIBUTION.md. No new downloads required.
- **As-of law.** Prediction for game g uses only strictly-prior completed games under the
  canonical tip-UTC clock (Lane A); no current-game information of any kind.
- **HCA prior expectation (honest, to be measured — NOT assumed).** Home advantage is
  near-universal in basketball, so the prior is HCA > 0, but the MAGNITUDE is unknown for
  the WNBA and must be selected train-only. Cross-league context only: the NBA's frozen
  HCA=100 was alive there, while the NFL REJECTED its constant HCA — league-specific HCA
  demonstrably varies, which is exactly why a WNBA value may not be imported. Structural
  differences (denser schedule, more repeat matchups, different travel patterns, and a
  mid-sample travel-regime change from commercial to charter flights in the 2020s) mean the
  grid must be able to select anywhere in [0, 150], including small values.
- **FROZEN falsifier (vs designed-null parent B0 = constant home-win rate, fit train-only).**
  REJECT the fresh-Elo family for WNBA iff pooled 95% CI of ΔLL(B1-WNBA, B0) includes 0 or
  ≥ half folds non-negative. Additionally: if the train-internal grid optimum is degenerate
  (K → 0, ratings never move ⇒ engine collapses to B0 + constant), the family is dead on
  WNBA data — NOT_RUN before any held-out window is spent.
- **Negative control.** Within-season outcome-permutation twin: shuffle game outcomes within
  each season (preserving per-team game counts and the date marginals), re-run the frozen
  grid engine; the shuffled engine must NOT beat B0 with CI excluding 0, else machinery
  audit and W-H1 un-scored.
- **Capacity / power (honest).** Core window 2002–2025 ≈ 5.1k RS games (≈24 season folds,
  min fold = 2020 Wubble ≈ 140 RS games); full-history variant ≈ 6.0k. Cross-league context
  for expected effect size: NBA ΔLL(B1*, B0) = −0.0782 over 8,369 games; NFL −0.0528 over
  1,865. If the WNBA family effect is of the same order (0.05–0.08), the paired CI
  (~±0.01 half-width at n≈5–6k, scaled from terminal-cycle widths) resolves it comfortably.
  A ≥ half-folds-negative condition needs ≥13 of ~24 folds negative — demanding but
  well-populated.
- **Train-internal kill test.** Train-internal ΔLL vs B0 CI must exclude 0 on the rolling-
  origin split before any held-out season is touched; else NOT_RUN, slot released.

---

### W-H2 — H-C5 continuity-modulated rating carryover — priority 2, **GATED on Lane A**

- **Mechanism (from prior-cycle H-C5/F10, re-adjudicated fresh for WNBA).** A 40-game season
  plus high roster churn (free agency, overseas contracts, retirements, a long overseas
  offseason) weakens prior-season rating priors, and the weakening should be TEAM-SPECIFIC:
  a team returning its rotation carries its prior rating; a rebuilt team should be shrunk
  hard toward league mean. A single global ρ0 (the W-H1 parent law) mis-specifies this by
  construction. Continuity — the share of prior-season rotation load returning — is the
  natural moderator and is season-start knowable.
- **Operationalization (exact).** `R_start_i(s) = league_mean + ρ·c_i(s)·(R_end_i(s−1) −
  league_mean)`, with `c_i(s)` = minutes-weighted share of team i's prior-season (s−1)
  player-minutes attributable to players on i's season-s opening roster (roster MEMBERSHIP
  from `espn_wnba_game_rosters`; prior-season minutes from player_box/box aggregates —
  strictly historical facts). Continuity enters LINEARLY (no exponents/transforms — frozen
  against term-fishing); single ρ selected train-only on the same grid machinery as W-H1.
  Expansion team-seasons (no prior season exists: CHI 2006, ATL 2008, GSV 2025, TOR/PDX
  2026) start at league mean in BOTH arms — they contribute no continuity contrast and
  cannot bias the comparison. Relocated-but-continuous franchises (UTA→SAN 2003; LAS→LVA
  2018; the DET→TUL→DAL 2016 merge tree) are handled by the canonical franchise keys from
  the rename map, with continuity measured empirically from actual roster overlap — no
  behavioral assumption. Prediction shape and in-season updates otherwise identical to W-H1.
- **$0 source + rights.** `espn_wnba_game_rosters` release asset (2002–2026, 29.0 MB, not
  yet pulled) + 2025-sample-verified player_box depth (median 23 rows/game), same
  CC BY 4.0 release store. One pull, recorded in a download manifest.
- **As-of law.** (i) Prior-season minutes: strictly completed prior-season games — clean.
  (ii) Season-s opening roster: roster membership attached to a team's first recorded game
  of season s is a season-start fact in the world, but the release asset is a current-state
  snapshot without publish timestamps. Two frozen variants, Lane A's PIT audit selects:
  **(v1)** use the game-1 roster membership for all games of season s (defensible: a team's
  game-day roster list is set before tip and membership — unlike `active`/`DNP`/`starter` —
  embeds no outcome information); **(v2)** conservative fallback — apply continuity from
  game 2 onward, league-default ρ0 behavior for game 1. POST-GAME fields (`active`,
  `did_not_play`, `starter`, `reason`) are forbidden as inputs in both variants.
- **Gate (hard).** NOT_RUN unless Lane A's census clears: per-season roster coverage of
  `espn_wnba_game_rosters` (≥ ~90% of team-seasons 2003+ present), rename-safe joins via
  crosswalk/display_name, and a PIT verdict on variant v1 vs v2. Eligible evaluation window
  shrinks to seasons with (s−1) minutes + season-s rosters ⇒ **2003+** ⇒ ≈ 4.9k RS games,
  ≈ 23 season folds. Lane A did not exist at lane start (only `measure_a.py` in flight) —
  gate is PENDING_LANE_A; if the census fails, the slot is released, never reallocated
  mid-program.
- **FROZEN falsifier (vs designed-null parent = W-H1 with the GLOBAL ρ0 law).** The claim
  under test is team-specific modulation, so the parent is the same engine with scalar ρ0
  (nested case c ≡ constant). REJECT iff pooled 95% CI of ΔLL(W-H2, ρ0-parent) includes 0
  or ≥ half folds non-negative. **Capacity kill:** if c_i shows near-zero cross-team
  variance within early seasons (exact numeric threshold frozen at protocol registration,
  before any evaluation look), the moderator cannot act — automatic drop.
- **Negative control.** Permute c_i across teams WITHIN each season (preserves marginals,
  destroys team alignment); the shuffled-continuity arm must not beat the ρ0-parent with CI
  excluding 0.
- **Capacity / power (honest).** Effects concentrate at season boundaries: the discriminating
  window is roughly the first 8–10 games of each season (where priors dominate before
  in-season updates wash the difference out) ⇒ ≈ 60–70 games/season × ~23 folds ≈ 1.4–1.6k
  games inside the sensitive window, with residual (attenuated) effect over the rest of each
  season. Paired ΔLL of two near-identical Elo engines has low variance (terminal-cycle
  precedent: NBA correlated-arm CIs ~±0.002–0.003 at n≈8.4k ⇒ ~±0.003–0.004 at n≈5k), so a
  true pooled effect ≥ ~0.004 is resolvable; smaller true effects will be honestly REJECTED
  by the frozen falsifier, not passed. This is stated as a real risk: the mechanism may be
  real and still unresolvable at WNBA capacity.
- **Train-internal kill test.** ρ and the v1/v2 variant selected train-internal only; if
  train-internal ΔLL vs the ρ0-parent CI includes 0, stop before any held-out season.

---

### W-H3 — Schedule-strength (SOS) decomposition under a short season — priority 3

- **Mechanism (WNBA-structure-specific prediction).** A rating level absorbs the quality of
  whoever a team happened to play; Elo's opponent-scaled updates correct this only slowly.
  The correction speed scales with games played: a 34–40-game schedule washes out schedule
  imbalance roughly half as fast as the NBA's 82 (and the WNBA plays opponents 3–4× with
  divisional weighting, so within-season cross-team SOS dispersion is real, not
  hypothetical). The structure-specific prediction: schedule-imbalance mispricing PERSISTS
  LONGER in the WNBA than the NBA context would suggest, with the largest effect early in
  each season. This is a REPLACEMENT-rating mechanism (`R̃ = R − β·(SOS − mean)` entering
  the logistic), NOT an additive feature stapled to elo_diff — that additive shape is dead
  in both terminal leagues and is banned here.
- **Operationalization (exact).** `SOS_i(t)` = mean of opponent pre-tip rating over i's
  COMPLETED games in the current season to date; the adjustment term is 0 for every team's
  game 1 (SOS undefined — PIT-clean by construction). Input rating
  `R̃_i = R_i − β·(SOS_i − league_mean_SOS)`; `p = σ((R̃_home − R̃_away + HCA)/400_scale)`
  with HCA and the W-H1 ρ0 law at their frozen train-only values; single β selected
  train-only (sign unconstrained, though the mechanism predicts soft-schedule teams
  overrated ⇒ β > 0). Engine otherwise identical to W-H1.
- **$0 source + rights.** Same results feed as W-H1 (already on disk, CC BY 4.0 store). No
  new data.
- **As-of law.** SOS computed from strictly-prior completed games only, under the canonical
  clock; opponent ratings are the pre-tip values at each completed game.
- **FROZEN falsifier (vs designed-null parent = W-H1).** REJECT iff pooled 95% CI of
  ΔLL(W-H3, W-H1) includes 0 or ≥ half folds non-negative.
- **Negative control.** Permute SOS_i across teams within each season (preserves marginals);
  shuffled-SOS arm must not beat W-H1 with CI excluding 0.
- **Capacity / power (honest).** Acts on every game with ≥1 completed game of season
  context; effect concentrated early-season. Full core window ≈ 5.1k RS games, ≈ 24 folds.
  Resolvable pooled-effect floor ~±0.003–0.004 (same correlated-arm machinery as W-H2);
  cross-league context for magnitude does not exist (H-C1 was accepted as a proposal for
  NBA/NFL but never scored — there is NO dead verdict here, only an untested one), so the
  prior is weaker than W-H2's; it is ranked third for that reason, not for cost (it is the
  cheapest: one β fit + one Elo re-run on existing data).
- **Train-internal kill test.** Train-internal β fit on the rolling-origin split; no
  train-internal gain over W-H1 (CI includes 0) ⇒ stop before held-out seasons. Capacity
  precondition: within-season cross-team SOS dispersion must be material by mid-season
  (threshold frozen at registration) — in a near-balanced schedule the moderator cannot act.

---

## 4. Explicit REJECTS (with reasons)

1. **Additive logistic-over-Elo layers (rest/form/any feature stack on elo_diff)** — BANNED.
   Dead shape per BOTH terminal cycles: NBA T1 FAIL −0.0010 [−0.0033, +0.0013]; NFL
   +0.0017 [−0.0053, +0.0088] (cited as context; the shape itself is program-banned). New
   signal enters as rating-INPUT (W-H2, W-H3) or a new pre-game information source — never
   as an additive layer.
2. **MOV-weighted / blowout-weighted Elo variants** — REJECT. Re-grid of the dead Elo-update
   family; adds no new information source; would burn one of ≤3 mechanism slots re-litigating
   a spent mechanism family.
3. **538 forecasts; closing/market odds** — BANNED by plan (and non-$0 / rights-restricted
   besides).
4. **Current-game box scores as features** — BANNED. Leakage by construction; box coverage
   also starts only 2003 (ESPN side). Train-only historical aggregates remain allowed only
   as rating priors, per the as-of law.
5. **Any NBA-derived parameter presented as WNBA evidence** (e.g., adopting K=32/HCA=100
   without WNBA-internal selection) — INDEPENDENCE-LAW VIOLATION. NBA K=32/HCA=100 is
   citable context and at most a grid-centering hint; the WNBA values are selected
   train-only by W-H1 or the hypothesis dies.
6. **b2b / congestion / travel fatigue × away as a scored arm** — REJECT under mechanism-
   first scrutiny. (i) The nearest context (NBA rest MAIN effects) added ~nothing; the
   interaction reframing was already ranked lowest-priority there. (ii) WNBA-specific
   regime instability: league travel moved from commercial to charter flights across the
   early 2020s, so one pooled historical coefficient is mis-specified across the sample;
   splitting eras halves an already thin sub-population (b2b-away ≈ 15–25% of a 34–40-game
   schedule ⇒ ~800–1,200 games pooled, less per era). (iii) W-H2 already owns the
   season-boundary/load-modulation slot; W-H3 owns the early-season slot; a third slot spent
   on the lowest-prior pattern is poor trial-budget discipline. Not permanently dead: a
   prospective re-proposal after W-H1/W-H2 verdicts, with era-restricted framing, is allowed
   in a later cycle.
7. **Expansion-team initialization prior** — REJECT (capacity starvation). ~5 franchise
   entrances in 30 seasons ≈ ~170 games; no train-only fit of an expansion prior is
   possible with any power. W-H1/W-H2 already treat new franchises at league mean.
8. **Overseas-contract / pre-game availability features** — NOT_RUN_PIT. No dedicated
   injury/availability feed exists in any wehoop-family release; no rights-verified archive
   with publish timestamps; `player_box` DNP/active/starter are POST-GAME facts. The
   offseason-churn PART of the overseas mechanism is already absorbed by W-H2's continuity
   moderator; the in-season acute-availability part stays NOT_RUN_PIT.
9. **Repeat-matchup "familiarity" / many-meetings interactions** — REJECT. No distinct
   mechanism beyond what ratings already encode after 3–4 meetings; adjacent to the dead
   additive-layer shape.

## 5. Roster / availability law (binding on successor cycles)

- Roster/availability features stay **NOT_RUN_PIT** unless Lane A clears a rights-verified
  archive with publish timestamps (or a Lane-A-adjudicated PIT variant for W-H2 v1/v2).
- Post-game DNP/active/starter/reason fields are **never** pre-game features — any arm, any
  cycle, no exceptions.
- W-H2 consumes roster MEMBERSHIP only (season-start), never game-night availability.

## 6. Hand-off notes to Lane C (protocol draft)

- Arm budget sketch (≤9, frozen before any test look): B0; W-H1 (+its ρ0 law); W-H2
  (gated); W-H3; negative-control diagnostics per arm (reported, never counted as wins);
  reserve slot must be pre-specified in the freeze document or released. This lane advanced
  exactly 3 candidates; if Lane A kills the W-H2 gate, the slot is RELEASED, not reallocated.
- Era law dependency: Lane C freezes 1997–2001 handling (excluded vs schedules-only
  baseline arm); W-H1 is defined under both variants.
- Fold law: season-level walk-forward folds; min fold population ≈ 140 RS games (2020);
  ≥ half-folds-negative ⇒ ≥13 of ~24 folds (core window).
- Playoffs, Cup, All-Star rows separate from the RS headline; 2026 data is prospective
  (append-only ledger rows timestamped strictly before tip UTC).
- Calibration slope band [0.85, 1.15] inherited; T1/T2/T3 gate shapes inherited as machinery.

## 7. What remains NOT_RUN and why

- W-H2: **PENDING_LANE_A** (roster census + PIT variant verdict; asset not yet pulled).
- Injury/availability: **NOT_RUN_PIT** (§4.8).
- All WNBA numbers in this document are coverage/schema counts from the prior cycle's
  audit; **no win-prob metric, no Elo run, no log loss was computed in this lane** — every
  predicted effect is a PREDICTION carrying its falsifier for the successor scored cycle
  (proposed name WNBA-WINPROB-SCORED-V1; requires fresh registration + freeze + A7 + owner
  typed GO at its own gate; this cycle registers and consumes no GO).

## 8. Provenance

- No downloads, no computation on outcomes, no git operations performed by this lane.
- Files left untracked in `lanes/B_MECHANISMS/` (controller lands).
- dispatch_sha = actual_start_sha = `673b4f27e4abdefc5c54839febac29185dd6e794`
  (measured `git rev-parse HEAD`, branch `orca/wnba-winprob-prep-v1-integration`).
