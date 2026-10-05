# PLAN — NFL-WINPROB-NG-SCORED-V1 (NFL next-gen win-prob prospective cycle, Option B, $0)

- cycle_id: NFL-WINPROB-NG-SCORED-V1 · asset: shared · ACTIVE_LIGHT, budget 0/9 arms scored,
  GO phrase registered but NOT typed: `GO NFL WINPROB NG SCORED V1 PROSPECTIVE`
- owner authority 2026-10-05 (this chat): prepare and complete the successor cycle per **Option B**
  of `NFL-WINPROB-NG-PREP-V1/OWNER_DECISION_PACKET.md` — plan, registration, freeze, synthetic
  tests, dry-run and A7 prelaunch MAY be completed per the applicable gates; **STOP before the
  Owner typed-GO gate** (P-8 two-key: A7 verdict first, then owner types the GO phrase verbatim
  at this cycle's own gate). No probability rows for real games are recorded this round; no
  retrospective predictions are created, ever. Keep the TEAM baseline machinery strictly separate
  from the player-feature research line (WINPROB-PLAYERFEAT-PREP-V1) — no player-level input
  enters any arm of this cycle.
- Hard boundaries (verbatim owner round): no scored backtest on evaluation windows, no S1, no
  paper/live/betting, no data purchases, no push/merge, no self-typed GO. Train-internal
  selection on TRAIN 2000–2018 is the gate-sanctioned path this cycle runs (freeze §7 item 2 of
  the predecessor packet: selection results computed inside the successor cycle on TRAIN);
  nothing on 2019–2025 (SPENT, cite-only) and nothing on 2026+ outcomes.
- Kickoff re-measurement at bootstrap (controller, fresh snapshot `raw_schedules_r1_20261005/
  games.csv`, sha256 486d7227…, snapshot mtime 2026-10-05T07:15:37Z, measured 08:49Z): 2026 REG
  272 scheduled / 63 played all-final (NOT_RUN prospective forever) / 209 future 0-scored /
  earliest future kickoff 2026-10-06T00:15:00Z `2026_04_ATL_NO`; week-5 slate opens
  2026-10-09T00:15:00Z `2026_05_TB_DAL`. Option B consequence (predecessor packet): week-5 slate
  is the first prospective window target; the launch clock must complete freeze+A7+GO before
  each week's first kickoff for that week to be capturable.

## Inheritance (read from bytes; re-measured at bootstrap)

- Baseline law: B1* = B1-c own-Elo K=40 HCA=0 γ=2/3 FROZEN (NFL-WINPROB-SCORED-V1 TERMINAL,
  INCONCLUSIVE; B1* pooled RS LL 0.6407 vs B0 0.6935, ΔLL −0.0528 [−0.0676, −0.0380]). New
  mechanisms must beat B1*, never merely B0.
- Dead-arm law: MOV-weighted Elo; K/HCA/rest/form re-grids; additive logistic-over-elo_diff;
  in-season pbp features; 538/odds/current-box — cited, never re-fit.
- Window law: TRAIN = complete seasons 2000–2018 (1999 excluded, gametime 100% missing);
  2019–2025 SPENT (cite-only); 2026+ PROSPECTIVE ONLY from real freeze/prediction timestamps
  (played-before-record = NOT_RUN prospective permanently, count disclosed at freeze).
- Candidate mechanisms (frozen specs in `NFL-WINPROB-NG-PREP-V1/lanes/B_MECHANISMS/
  MECHANISMS_NFL_NG.md`): C1 SOS-adjusted Elo (β grid {0,25,50,75,100}, designed null β=0);
  C2 home/away split rating (λ, γ_d, h, designed null λ=0); C3 offseason EPA prior train-only
  (θ, designed null θ=0; requires pbp audit back through train — else NOT_RUN_PIT, slot
  released); C4 short-week×away one-cell δ≥0 (CONDITIONAL on G-INT train-internal gate;
  expected released). Successor protocol (rolling-origin inner folds = last 5 TRAIN seasons
  2014..2018 expanding; selection ledger counts every evaluated config; B1*/B0 exempt) frozen in
  `lanes/C_PROTOCOL/PROTOCOL_NFL_NG.md` + `LEDGER_SCHEMA.md`.
- Ledger law: `nfl_ng_ledger@1` (predecessor lane E, 42/42 SYNTHETIC + 4 adversarial probes):
  append-only JSONL, flock+fsync, sha256 chain from freeze GENESIS, no outcome columns,
  recorded_at_utc < kickoff_utc enforced at append AND at scoring vs actual kickoffs; O-2 row
  classes (row-level NOT_RUN, NOT_SCORED_NO_ACTUAL_DATA). Ledger file for real rows is created
  ONLY after owner GO; this round writes no real rows.
- Data: games.csv/schedules + teams (nfl-ng-prep-v1, r1 snapshot pinned), pbp 2021–2025
  (nfl-nflverse-v1 archive, read-only). pbp 2000–2017 for C3 train priors must be downloaded
  fresh here with full provenance. Rights: nflverse-data CC BY 4.0 (sha 2a82ac9b… pinned);
  underlying league/ESPN publication-commercial rights remain UNVERIFIED — internal research
  only, fail-closed.

## Tasks (owner round 2026-10-05; stop before GO)

1. Lane A — SUCCESSOR DATA: download pbp 2000–2017 (18 per-season parquets, `pbp` release) to
   `~/.my-quantitative-data/nfl-ng-scored-v1/raw_pbp_2000_2017/` with URL+version+timestamp+
   bytes+sha256 each + ATTRIBUTION.md; verify license text unchanged vs pinned copy; audit pbp
   coverage/season completeness + team-abbreviation lineage vs games.csv; freeze TRAIN season
   list + neutral-site flag status (`location` column, HCA=0 law) + kickoff fallback X = not
   activated (2000–2026 kickoff-capable); fresh 2026 played/future recount at audit time;
   SUCCESSOR_DATA_AUDIT.md. No metrics computed.
2. Lane T — TRAIN-INTERNAL SELECTION (heavy lock required around runs): implement B0/B1* replay
   + C1/C2/C3(±C4-gate) per frozen specs on TRAIN 2000–2018 ONLY; designed-null bit-for-bit
   equivalence vs B1* proven before any other number is believed; rolling-origin inner folds
   2014..2018; every evaluated grid point into a selection ledger; negative controls
   (time-shuffled twins per candidate; venue-label permutation for C2); G-ENTRY / G-INT /
   G-PIT verdicts per protocol §6; SELECTION_REPORT.md freezing β/λ/γ_d/h/θ/δ (or slot
   releases). ZERO reads of 2019+ outcome data (assert + audit-hook in code). C3 runs only if
   lane A's pbp audit passes; else NOT_RUN_PIT slot release recorded.
3. Lane F — FREEZE PACKET: bind every §7 open item of the predecessor draft: final arm
   enumeration (slots 1–9 with released slots named; slot 7 RESERVE = RELEASED unless owner
   names one before freeze — owner instruction names none ⇒ released, documented), selection
   results from lane T, recorder = this cycle's controller (single writer), cadence = weekly
   batch, margin = ≥6h before week's first kickoff UTC, GENESIS payload digest (computed and
   pinned; the real GENESIS row is written only after GO), candidate-ranking rule = lowest
   pooled prospective LL among fielded candidate slots, metrics/gates/R1–R3/power language
   verbatim from the predecessor protocol/freeze draft, O-2 vocabulary, postponement laws.
   FREEZE_PACKET.md + arm_config_digest per fielded arm + code freeze SHA binding.
4. Lane S — SYNTHETIC TESTS + DRY-RUN: port the ledger tool + its 42 synthetic tests into this
   cycle's tree (provenance note: source commit) and re-run green; add successor-level
   synthetic tests: designed-null arms produce byte-identical p_home vs B1* on synthetic
   fixtures; as-of strict-inequality fixtures; kickoff-margin validator; hash-chain tamper
   detection. DRY-RUN: full record-pipeline rehearsal on synthetic games into a SANDBOX ledger
   file (never the real ledger path; real ledger must not exist); exact-arm identity checks;
   zero real-game rows, zero real-ledger writes. DRYRUN_REPORT.md with exit codes.
5. Lane A7 — INDEPENDENT PRELAUNCH AUDIT (after controller integration of A/T/F/S; never
   repairs): re-verify SHA chain (base→code freeze→freeze packet), re-run designed-null
   equivalence, audit no-2019+ access, confirm real ledger absent, rights re-check, selection
   ledger completeness, freeze §7 completeness, boundary compliance (0 arms scored, no GO
   typed), power language present. Verdict PASS_REFUSED-style honest (A7_PRELAUNCH_VERDICT.md).

## Boundaries

- No scored evaluation on any window; train-internal selection on TRAIN only. No S1, no
  paper/live, no betting language, no purchases, no push, no merge to main, no edits to frozen
  artifacts/ledgers of any cycle. Registry writes only via researchctl (CAS). Lanes never write
  the real prediction ledger; no lane computes win-prob for any real game. Language law:
  calibration/forecasting vocabulary only.
- Root checkout = control plane only. Lane work in the exact worktree/branch named in dispatch
  packets. Data outside git under `~/.my-quantitative-data/nfl-ng-scored-v1/`. Heavy selection
  runs take the global lock (NOT_RUN_RESOURCE_CONFLICT if held; retry with backoff; never kill
  foreign workers).

## Artifacts

`lanes/A_DATA/ · lanes/T_SELECT/ · lanes/F_FREEZE/ · lanes/S_SYNTH/ · lanes/A7_PRELAUNCH/ ·
lanes/DISPATCH/` under the integration worktree; each lane ends with handoff JSON
`zcode_orch_v3_handoff@1` at its handoff_path. Control state under
`research/control/NFL-WINPROB-NG-SCORED-V1/`.

## Terminal outcomes (negative-first)

PRELAUNCH_READY_PENDING_OWNER_GO (all lanes + A7 PASS, GO not typed) | SELECTION_NEGATIVE_ALL_
CANDIDATES_FAILED (program stop per protocol §6.3 — no prospective launch; negative result with
selection ledgers as evidence) | BLOCKED_DATA_RIGHTS | BLOCKED_TOOLING | TECHABORT_*. The GO
phrase `GO NFL WINPROB NG SCORED V1 PROSPECTIVE` is typed ONLY by the owner at this cycle's own
gate after reading the A7 verdict; it is never typed, paraphrased or consumed by any agent.
