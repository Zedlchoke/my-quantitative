# PLAN — NBA-WINPROB-NG-SCORED-V1 (NBA team-level next-gen win-prob prospective cycle, $0)

- cycle_id: NBA-WINPROB-NG-SCORED-V1 · asset: shared · ACTIVE_LIGHT, budget 0/9 arms scored,
  GO phrase registered but NOT typed: `GO NBA WINPROB NG SCORED V1 PROSPECTIVE`
- owner authority 2026-10-06 (this chat, dispatch packet §8 gate 1): REGISTRATION
  authorization for the team-level successor of NBA-WINPROB-NG-PREP-V1 per
  `research/control/NBA-WINPROB-NG-PREP-V1/SUCCESSOR_PACKET_SCORED.md` — plan, freeze,
  baseline, candidate arms, harness, synthetic dry-run, PIT check and A7 MAY be completed;
  **STOP before the Owner typed-GO gate** (P-8 two-key: A7 verdict first, then owner types
  the GO phrase verbatim at this cycle's own gate). This instruction is explicitly NOT a
  typed GO; no probability row for any real game is recorded this round; no retrospective
  predictions are created, ever.
- Hard boundaries (verbatim owner round): no scored cells, no reads of OOS outcomes, no S1,
  no paper/live/betting, no data purchases, no push/merge/rebase/history-rewrite, no
  self-typed GO. Scored count at close of this round MUST be 0.
- Player-feature ban (NBA-PLAYERFEAT-SCORED-V1 negatives preserved explicitly): the TEAM
  baseline machinery stays strictly separate from the player-feature research line
  (NBA-PLAYERFEAT-SCORED-V1) — no player-level input enters any arm of this cycle; and NO
  OOS-based parameter selection exists anywhere — every free parameter is selected
  train-internal (selection era 2018–2021) and frozen before any OOS look.

## Inheritance (read from bytes; re-measured at bootstrap 2026-10-06 — nothing inherited on trust)

- Prep-cycle verdict chain: NBA-WINPROB-NG-PREP-V1 PREP_COMPLETE_PENDING_OWNER_DECISIONS
  (PREP_SUMMARY.md) + post-fix re-verification VERIFICATION_PASS at 4a7ea926; successor
  packet §4 freeze hashes re-measured against live bytes at THIS cycle's bootstrap — all
  six pins reproduce exactly (see FREEZE packet for the fresh sha256 table; universe
  14,254 = 14,168 played + 19 exhibitions + 67 postponed re-measured with zero residue;
  pbp hole = 14 played games re-measured game-for-game vs ERRATUM_PBP_GAP_R1.md).
- Baseline law: B1* = B1-d own-Elo **K=32, HCA=100, γ=0.75**, binary updates — carried
  VERBATIM from NBA-WINPROB-SCORED-V1 (TERMINAL, NO_PROGRAM_PASS; spent-window evidence:
  pooled RS LL 0.5987 vs B0 0.6769, n=8,369, ΔLL −0.0782 [−0.0875, −0.0687]; HCA alive
  −0.0215 [−0.0271, −0.0157]; calibration slope 0.9894/0.8606 both in [0.85, 1.15]).
  B1* constants are FROZEN — never re-tuned. Any new mechanism must beat B1*, never merely B0.
- Dead-arm law: additive logistic-over-Elo feature layers (terminal T1 FAIL, dead in BOTH
  terminal cycles); MOV/blowout-weighted Elo (re-grid of a dead family); any re-grid of
  K/HCA/rest/form on 2009–2015; 538 forecasts; closing/market odds; current-game box
  scores — cited, never re-fit.
- Spent-window law: seasons 2009–2015 (538 nbaallelo window) are SPENT — citable context,
  never scoreable, no re-grid of K/HCA/rest/form there in any arm or diagnostic.
- Window law (frozen by PROTOCOL_DRAFT_NBA_NG.md §1, inherited verbatim): WARM-UP = seasons
  2016, 2017 (streams run, never scored, never selection metrics); TRAIN-INTERNAL
  SELECTION = seasons 2018–2021, 4 rolling-origin folds; frozen split cutoff
  **2021-08-01T00:00:00Z** (tip-UTC; sits in the off-season gap); WALK-FORWARD OOS = frozen
  list **[2022, 2023, 2024, 2025, 2026]** expanding folds; PROSPECTIVE ONLY = 2026–27+
  (season 2027) unplayed-at-freeze games via append-only ledger rows with `written_at_utc`
  STRICTLY < tip UTC; single-batch scoring, no interim OOS peeks.
- Candidate mechanisms (frozen specs in `lanes/B_MECHANISMS/MECHANISMS_NBA_NG.md` of the
  prep cycle): NB-H1 SOS-adjusted Elo (β train-only; null parent β=0 = B1*); NB-H2
  home/away split ratings (λ; null λ=0; capacity kill if mean ‖R_h−R_a‖ < 10 Elo);
  NB-H3 fatigue×venue joint block as modulated away-HCA (θ≡0 null; ONE joint ΔLL, never
  per-term); NB-H4 pace/efficiency train-only rating-init (w=0 null; release-only if the
  data-rights gate fails). NB-H2/NB-H3 force HCA=0 on `neutral_site==true` Cup rows.
- Metrics + uncertainty (inherited verbatim): log loss primary; Brier + reliability +
  calibration slope [0.85, 1.15] secondary; paired per-game ΔLL with date-cluster block
  bootstrap, 10,000 resamples, seed 20261005, percentile CI, per fold AND pooled; T1/T2/T3
  gate shapes and R1–R3 reject predicates per PROTOCOL_DRAFT_NBA_NG.md §6 (fold-majority
  bar ≥ 3 of 5); playoffs + play-in + Cup final reported separately; RS headline only;
  anomaly sensitivity segments per protocol §9.
- Data: hoopR/sportsdataverse corpus at `~/.my-quantitative-data/nba-hoopr-v1/` (HOME-level
  shared store, EXTEND-ONLY, read-only for this cycle) + pbp 2016–2025 at
  `~/.my-quantitative-data/nba-ng-prep-v1/pbp_2016_2025/`; rights CC BY 4.0 (producer,
  verbatim "data, code, and documentation") + MIT (release store); upstream ESPN NBA API;
  internal research only. The ROOT-level untracked `my-quantitative/.my-quantitative-data/`
  is FOREIGN content — never read, never bundled.
- Supersession annotations baked in (prep verifier D2/D6/D7): (i) the prep lane-A artifact
  `measure_schedule_corpus.{py,json}` carries a SUPERSEDED intermediate dedupe law
  (abbrev/regex exhibition filter, kept_total 14,184; RS 2020=1,061 / 2021=1,081) — the
  spec's headline-based law is the ONLY authority (14,168 played; RS 2020=1,059 /
  2021=1,080); its numbers are never re-derived or cited as law; (ii) the spec §2 ET-home
  count 6,632 was a subset (NY home rows missed) — corrected exhaustiveness is 7,104 rows,
  0 offset mismatches, conclusion unchanged; (iii) protocol fold names S1–S4 are RETIRED
  (collision with the sealed S1 store name): selection folds are renamed **SEL-F1..SEL-F4**
  and OOS folds **F1..F5** in every artifact of this cycle.

## Arm table (≤9 scored slots; slots 8–9 RELEASED pre-look, never reallocated)

| # | Arm | Class | Status | Null parent | Falsifier (frozen) |
|---|-----|-------|--------|-------------|--------------------|
| 1 | B0 constant home-win rate, per-fold train-only refit | PRIMARY | committed | — | reference floor (T3) |
| 2 | B1* K=32/HCA=100/γ=0.75 verbatim | PRIMARY | committed | — | mandatory baseline; reference-beater required |
| 3 | NB-H1 SOS-adjusted Elo (β grid, train-only) | PRIMARY | candidate | β=0 (= B1*) | REJECT iff pooled 95% paired date-cluster CI of ΔLL vs B1* includes 0 OR ≥ half folds non-negative; shuffled-SOS twin must show nothing |
| 4 | NB-H2 home/away split ratings (λ grid, train-only) | PRIMARY | candidate | λ=0 (= B1*) | same CI gate; split-collapse (mean ‖R_h−R_a‖ < 10 Elo) = capacity kill; venue-permutation twin must destroy the gain |
| 5 | NB-H3 fatigue×venue joint block (b2b/3in4/travel/tz, away-restricted modulated HCA) | PRIMARY | candidate | θ≡0 (= B1*) | CI gate on the JOINT block (one ΔLL, never per-term); shuffled travel/rest twins mandatory |
| 6 | NB-H4 pace/efficiency train-only rating-init | PRIMARY | candidate-gated | w=0 (= B1*) | CI gate; release-only if the freeze-time data-rights/PIT gate fails; shuffled-prior twin |
| 7 | H-C3 availability/injury | PRIMARY | **NOT_RUN_PIT — slot stays empty** | — | activates ONLY if a rights+timestamp-proven archive clears the 5-step audit (MECHANISMS_NBA_NG.md §4) BEFORE freeze; else released |
| 8 | reserve | — | **RELEASED (pre-look rule)** | — | never reallocated |
| 9 | reserve | — | **RELEASED (pre-look rule)** | — | never reallocated |

- Diagnostic class (registered pre-look, outside the 9-slot budget, never candidate wins):
  NC-H1 shuffled-SOS twin; NC-H2 venue-permutation twin; NC-H3 shuffled travel/rest twins;
  NC-H4 shuffled-prior twin; B1-HCA0 ablation (K=32, HCA=0, γ=0.75) for new-window baseline
  validity. Twins preserve per-team/per-season marginals (verified pre-look).
- Kill tests pre-OOS: every arm must survive its train-internal split first (train ΔLL vs
  B1* > −0.001 or flat/sign-flipping response ⇒ KILL, slot RELEASED); a control beating its
  parent ⇒ machinery audit + arm UN-SCORED (protocol §6.1).
- Spread features (`game_spread`/`home_favorite`/`home_team_spread`): UNVERIFIED_PIT ⇒
  diagnostic-only at most, never a mechanism; BDL = cross-check spot source only (≤25-game
  re-check sample at freeze, free tier ≤5 req/min), never primary.

## Tasks (owner round 2026-10-06; stop before GO)

1. Registration + plan: this plan committed on
   `orca/nba-winprob-ng-scored-v1-integration`, copied to ROOT `plans/`, cycle registered
   via researchctl (CAS, budget-max 9, GO phrase registered-not-consumed) — exactly two
   ROOT writes, both by explicit pathspec, tracked ROOT_DIRTY=0 asserted before each.
2. Freeze packet: `research/control/NBA-WINPROB-NG-SCORED-V1/FREEZE/` pinning the fresh
   re-measured §4 hashes (byte-pinned), data laws (universe filter/dedupe, tip-UTC
   Eastern-only canonicalization, 14-hole tolerate-never-impute, spread diagnostic-only,
   BDL spot-check ≤25 games), B1* verbatim constants, arm table with null parents and
   frozen falsifiers, metrics/uncertainty laws, fold renames, supersession annotations —
   all committed BEFORE any OOS look.
3. Harness + synthetic: implement the pipeline per PROTOCOL_DRAFT_NBA_NG.md (B0, B1*
   mandatory; NB-H1..H4 as data rights allow; null parents; shuffled twins) with synthetic
   fixtures proving: no-lookahead mutation probe, DST boundary, fold force-flat,
   tolerate-14-hole. Then the EXACT-ARM synthetic dry-run (quarantined, synthetic data
   only, zero scored cells, record IDs pairwise distinct, empty book = fail) under the
   machine-wide heavy lock (NOT_RUN_RESOURCE_CONFLICT if held; retry; never kill foreign
   workers). $0: no purchases, no network fetches beyond what the freeze sanctions
   (prefer zero).
4. PIT + A7: re-run the PIT audit laws over the frozen data paths (no-lookahead,
   append-only, tip-UTC; spread stays diagnostic-only) and record results; then an A7
   prelaunch-style audit round at the final lane HEAD (independent-style audit script +
   evidence + verdict committed in-tree, NFL/WNBA A7_R6 precedent): registration
   correctness, freeze hash re-verification, harness/synthetic/dry-run evidence, PIT, and
   that NO scored cell was computed and NO OOS outcome read. 0 unresolved HIGH/CRITICAL
   for PASS; any gate FAIL/NOT_RUN ⇒ release the affected arm, never force GO-ready.

## Boundaries

- No scored computation, no OOS outcome reads, no metrics on real outcomes this round
  (schema/coverage counting and PIT audits on frozen paths are allowed; win-prob metrics on
  real games are not). No S1, no paper/live, no betting language, no purchases, no push, no
  merge to main, no edits to frozen artifacts/ledgers of any cycle. Registry writes only
  via researchctl (CAS); on conflict: re-measure + retry, never overwrite.
- Root checkout = control plane only. Lane work in the exact worktree/branch named above.
  Data outside git stays at the HOME-level store; foreign ROOT-level
  `.my-quantitative-data/` untouched and unbundled. Language law: calibration/forecasting
  vocabulary only — no PnL/betting/edge words.

## Artifacts

`research/control/NBA-WINPROB-NG-SCORED-V1/` (FREEZE/, SYNTH/, DRYRUN/, PIT/, A7/,
handoffs/) in the integration worktree; handoff JSON `zcode_orch_v3_handoff@1` at
`research/control/NBA-WINPROB-NG-SCORED-V1/handoffs/20261006_team_cycle_prep_handoff.json`.

## Terminal outcomes (negative-first)

PRELAUNCH_READY_PENDING_OWNER_GO (all gates PASS, GO not typed) | GATE_FAIL_<GATE>
(FAIL/NOT_RUN recorded, affected arms released) | BLOCKED_DATA_RIGHTS | BLOCKED_TOOLING |
NOT_RUN_RESOURCE_CONFLICT (lock held past retries) | TECHABORT_*. The GO phrase
`GO NBA WINPROB NG SCORED V1 PROSPECTIVE` is typed ONLY by the owner at this cycle's own
gate after reading the A7 verdict; it is never typed, paraphrased or consumed by any agent.
Nothing survives from any earlier cycle (P-8); NBA-WINPROB-SCORED-V1's GO was consumed and
extinguished 2026-10-05.
