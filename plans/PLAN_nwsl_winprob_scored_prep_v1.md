# PLAN — NWSL-WINPROB-SCORED-PREP-V1 (scored successor PREP: seasonal walk-forward, NWSL-fresh arms, owner-frozen design; $0; STOP before Owner GO and before any scored OOS)

- cycle_id: NWSL-WINPROB-SCORED-PREP-V1 · asset: shared · ACTIVE_LIGHT ·
  budget max **3** scored cells (consumed ONLY by the single post-GO scored
  pass; this round consumes **0**) · GO phrase registered, NOT typed:
  **`GO NWSL WINPROB SCORED PREP V1 SEASONAL RUN`** (owner-only, verbatim,
  fresh, at this cycle's own gate after A7).
- Owner authority 2026-10-15 (this chat): successor PREP opened on the
  NWSL-WINPROB-PREP-V1 decision packet (`research/control/NWSL-WINPROB-PREP-V1/DECISION_PACKET_20261015.md`),
  with seven owner-frozen design decisions bound verbatim below. Scope:
  data prep, models, freeze packet, synthetic rehearsal, A7 prelaunch.
  **NOT a scored GO, NOT a paper GO.** No scored OOS, no P&L, no NWSL paper
  scope, no edits to other leagues/ledger/wallet/dashboard/cadence, no
  purchases, no push/merge. Missing evidence = NOT_RUN.
- Non-duplication: registry holds no NWSL scored-successor cycle; this plan
  is its first registration.

## Owner design decisions (frozen; a freeze packet may tighten, never loosen)

1. **Warm-up starts 2016.** 2013–2015 are OUT until backfilled and verified
   1:1 by a future decision; no silent inclusion. If history length makes the
   model infeasible ⇒ `NOT_RUN_DATA`, stated.
2. **2020 fully excluded** from the default set; the 41 Challenge Cup/Fall
   Series nwslR rows are disclosed separately, never mixed into the
   regular-season stream.
3. **ESPN is the score authority 2016+.** Every moved/relocated/awarded/
   genuinely-disputed row needs a per-row resolution table with a third
   source; unresolved rows are EXCLUDED from target and feature stream under
   the frozen law (counts disclosed). The two round-2 dispositions stand:
   the 2016 Championship ET-semantics row is resolved by the 90-minute label
   law; the 2017 Championship orientation flip is resolved by ESPN authority
   (nwslR defect, ESPN wins).
4. **TRAIN/selection = valid seasons before 2023** (warm-up 2016–2018 ratings
   only; train-internal selection 2019–2022). **The OOS game-ID list
   (2023–2025) is frozen before any OOS metric exists.** Finished-2026 rows
   are separate historical artifacts (never in this scored pass); unplayed
   2026 rows are prospective only; no historical row is ever called
   prospective.
5. **Arms: B0-NWSL (constant 3-way, train seasons only) + B1-NWSL
   (Elo/Davidson, NWSL-fitted grid, train-internal selection).** H-TRAVEL and
   H-EXPANSION are selected/rejected ONLY by train-internal diagnostics under
   a preregistered trial budget; a locked spec may occupy the third scored
   cell (B1+LOCKED_SPEC) only if frozen before any OOS read; otherwise budget
   drops to 2 and the release is recorded. Designed nulls, lookahead checks,
   and the expansion-equivalence check are mandatory. **No hypothesis may be
   added after any OOS number is seen.**
6. **Polymarket `prices-history` = presence/price-movement research ONLY.**
   It is NOT evidence of executable asks, depth, fees, or execution P&L.
   Any future paper leg requires real order-book capture strictly pre-anchor
   and the shared-wallet gates (separate owner decision; out of scope here).
7. **Freeze packet** pins: franchise-lineage identity, match set, code +
   hashes, 90-minute target law, PIT laws, folds, trial budget, LL/RPS/
   calibration gates, missing-data handling, and the ONE scored pass.
   Synthetic rehearsal + independent A7 must include refusal cases: lookahead,
   playoff mislabel, home/away flip, 2020 contamination, and prices-history
   misused as an executable quote.

## Corpus (inherited pins; re-measured at bootstrap)

- ESPN year scoreboards 2013–2026 (sha256 in
  `~/.my-quantitative-data/nwsl-winprob-prep-v1/harvest_20261015/MANIFEST.json`;
  2024 = 3b4527e6…, 2026 = 6e38a441…), refreshed-and-rehashed at freeze.
- nwslR `matches.csv` fb6addf8… (cross-check/orientation audit only, never a
  score authority); SoccerStatsUS tarball 6a252fd2… (tertiary resolution
  source for pre-2020 disputed rows, CC BY 4.0).
- Exposure binding: `COUNT_EXPOSED_BY_CENSUS_20261015` — every historical
  number is partially-exposed-window evidence (count level), never called
  untouched-OOS. Outcome-level statistics on valid seasons are computed only
  by (a) train-internal selection runs (S0-by-design, journaled) and (b) the
  one post-GO scored pass.

## Frozen data laws (this plan; freeze packet elaborates, never weakens)

- Identity: franchise-lineage id under a lineage table MEASURED from the ESPN
  bytes (per-season display-name census + rebrand years: Sky Blue→Gotham,
  Seattle Reign/OL Reign, FCKC→Utah→KC Current, WNY→NC Courage,
  Chicago Red Stars→Chicago Stars; expansion: Bay FC 2024, Boston Legacy 2026).
  ESPN home/away orientation is authoritative everywhere.
- Match set: ESPN rows 2016–2019 + 2021–2026 with finished statuses; every
  exclusion counted (`NOT_SCORED_POSTPONED`, `EXCLUDED_2020_BY_LAW`,
  `EXCLUDED_UNRESOLVED_DISPUTE`, `NOT_SCORED_FUTURE_2026`).
- Target: 90-minute H/D/A by the deterministic label law (Full Time = final
  score is the 90-min result; ET/Pens/Golden Goal = DRAW-90 by competition
  law; the ET score is never used as a 90-min score). Playoff rows are
  scored in a separate block, never pooled into regular-season aggregates.
- Batching: kickoff-UTC order; identical-kickoff games form ONE batch — every
  game predicted from the same pre-batch state; ratings update after batch
  close. (ESPN kickoff UTC present on every row.)
- Third-party resolution table: per-row for the 2017-06-17 and 2021-09-04
  disputes (SoccerStatsUS bytes for the 2017 row; the 2021 row has no
  authorized third source at $0 ⇒ excluded unless a lane proves one).
- Missing data: a row missing kickoff UTC, venue-city (when the frozen spec
  requires it), or a score fails closed (`NOT_RUN_ROW_<reason>`), counted.

## Windows / arms / budget (exact)

- Warm-up 2016–2018 (ratings only, never scored) · train-internal selection
  2019–2022 (season blocks 2019/2020-excluded/2021/2022) · chrono scored OOS
  = the FROZEN game-ID list of 2023–2025 finished rows · 2026-finished =
  historical artifact block (not scored here) · 2026-unplayed = prospective.
- B0-NWSL: constant 3-way from train seasons only (value of record frozen at
  freeze). B1-NWSL: Elo/Davidson 3-way, NWSL-only grid
  K∈{8,12,16,24,32} × ν∈{0.30,0.45,0.60,0.80} × HCA∈{0,25,50,75,100},
  selected by block-average LL on 2019–2022 with MIN_VALID 100 per block;
  update `R += K(S−E)`, strengths base-10 `10^(R/400)`, Davidson 3-way with
  tie ν, HCA added to home strength. Men's/other-league parameters EXCLUDED.
- H-TRAVEL (≤6 specs): away-team travel burden (great-circle distance from
  previous venue; timezone shift) from completed games only; trained +
  selected train-internal. H-EXPANSION (≤4 specs): expansion-team prior/K
  uplift by franchise age. Designed nulls: within-day shuffled travel pairs;
  expansion-equivalence (identical params for non-expansion ≡ B1 bit-for-bit
  on those rows). Diagnostic trial budget: ≤10 + nulls, journaled
  (`NWSL_DIAGNOSTIC_TRIAL_LEDGER.jsonl`, append-only); scored budget stays
  0 this round.
- Locked-spec rule (frozen before any run): a hypothesis locks ONLY if its
  pooled train-internal ΔLL CI (date-cluster bootstrap 10,000, seed frozen at
  freeze) excludes 0 and is negative vs B1's winner, AND exceeds the capacity
  note (|ΔLL| < 0.005 = INCONCLUSIVE, stated); else **KEEP_B1** and the third
  scored cell is released (budget → 2).
- Metrics + falsification: pooled + per-season multi-class LL primary; RPS,
  Brier macro, 10-bin reliability, calibration slope [0.85, 1.15]; argmax
  accuracy DESCRIPTIVE only; per-season + regular/playoff separation always;
  MKT reference (de-vig) only where lawful PIT snapshots exist — none in this
  cycle ⇒ the market lane is reported as research-only or NOT_RUN.
  An arm FAILS to beat B0 unless pooled ΔLL ≤ −0.01 nats AND ΔRPS ≤ −0.005.
  REJECT_ALL is a valid terminal.

## Round tasks (this round consumes 0 scored)

1. L-DATA — corpus build + lineage census + exclusion ledger + third-party
   table + **OOS game-ID freeze (hash-pinned before any OOS metric)** +
   2026 split artifacts.
2. L-ENGINE — B0/B1 implementation + synthetic battery on FAKE games:
   lookahead mutation refusal, playoff mislabel refusal, home/away flip
   refusal, 2020 contamination refusal, prices-history-as-quote refusal,
   day-batch leakage refusal, chain tamper, missing-data fail-closed,
   designed-null bit-parity, full-rerun byte-identity. ZERO real scored rows.
3. L-SELECT — train-internal selection run (heavy lock; S0-by-design,
   journaled): B0 value, B1 grid winner + digests, TRAVEL/EXPANSION lock
   decision per the frozen rule.
4. L-FREEZE — FREEZE_PACKET.md + OWNER_GO_PACKET.md (exact phrase, what the
   one post-GO pass runs and can never do) + freeze digests.
5. Controller integrates; **A7** independent fresh-context at final HEAD
   (hash chain, battery re-run incl. all five owner refusal cases, PIT laws,
   isolation of every other cycle, registry coherence) → decision packet →
   STOP.

## Boundaries

$0; no network beyond re-hashing existing pinned bytes (any refresh is a
read-only GET of the same pinned URLs with sha-compare to the pins; a drift
is `NOT_RUN_REPRODUCTION` for the affected source, never silently re-pinned);
no purchases/accounts; no S1; no push/merge/rebase; registry writes only via
researchctl CAS; heavy lock machine-wide (never kill foreign workers);
calibration/forecasting vocabulary only — no PnL/betting/edge claims; prices-
history is research-only (owner decision 6); NWSL paper scope untouched
(`NOT_RUN_NWSL_PAPER_HOOKUP` stands); other cycles read-only; handoff JSON
`zcode_orch_v3_handoff@1` at each handoff_path.

## Worktrees / artifacts

Integration `.worktrees/nwsl-winprob-scored-prep-v1/integration` on
`orca/nwsl-winprob-scored-prep-v1-integration`. Data plane
`~/.my-quantitative-data/nwsl-winprob-scored-prep-v1/`. Control artifacts:
`research/control/NWSL-WINPROB-SCORED-PREP-V1/` — `EXCLUSION_LEDGER.md`,
`LINEAGE_TABLE.md`, `OOS_FREEZE_<sha>.json`, `FREEZE_PACKET.md`,
`OWNER_GO_PACKET.md`, `SYNTH_REPORT.md`, `DIAGNOSTIC_TRIAL_LEDGER.jsonl`,
`A7_PRELAUNCH_VERDICT.md`, `DECISION_PACKET.md`.

## Terminal outcomes (negative-first)

**PRELAUNCH_READY_PENDING_OWNER_GO** (all lanes + A7 honest PASS real & refusal
paths, GO not typed, 0 scored) | **NOT_RUN_DATA** (history too short / exclusions
break feasibility — stated, nothing scored) | **SELECTION_NEGATIVE_KEEP_B1**
(hypotheses fail TRAIN — a valid outcome; B0/B1 proceed to freeze) |
PRELAUNCH_BLOCKED_<gate> | NOT_RUN_* | TECHABORT_*. The GO phrase is
owner-only; agents never type or paraphrase it; nothing survives from any
earlier cycle's gate (P-8).
