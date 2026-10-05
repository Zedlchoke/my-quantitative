# PREP_SUMMARY — NFL-WINPROB-NG-PREP-V1 (controller synthesis; 2026-10-05)

Status: PREP_COMPLETE_PENDING_OWNER_DECISIONS. Budget 0 scored, no GO phrase (P-8).
Evidence chain: plan 08ab2175 → registry 91f86ae6 → wave fce0b14f (dispatch packets +
prospective epoch 2026-10-05T03:13:51Z) → lanes landed 71c04cf5 → verify + this summary
at b0b5b8fc + controller commit. Lane handoffs: lanes/{A_DATA,B_MECHANISMS,C_PROTOCOL,D_VERIFY}/handoff_*.json.

## Verdicts (from lane artifacts; verifier D PASS 10/10, 0 blocking)

- DATA (lane A; artifacts f2e800c8+b0750891): nflverse rights PASS — CC BY 4.0 re-verified
  verbatim from held upstream bytes (LICENSE sha256 2a82ac9b…; §4 quote verbatim; D2-a minor:
  two §1 quotes are paraphrases labelled verbatim — reported, rights verdict unaffected).
  Coverage 1999–2026 measured (7,548 games; kickoff-UTC complete 2000–2026; 15 ties; 102
  neutral; franchise moves measured; 2022 BUF@CIN cancel omitted = zero unfinished rows;
  pbp 2021–2025 reconciles 247,284 plays). 2026 vs epoch: 272 scheduled REG; 63
  played-before-epoch → NOT_RUN prospective (62 scored + 1 in-flight boundary DET@CAR);
  209 future, 0 scored; earliest future kickoff 2026-10-06T00:15:00Z (2026_04_ATL_NO).
  Injuries: NOT_RUN_PIT — current nflverse injuries schema has NO timestamp column;
  depth_charts/weekly_rosters also unproven; no retro-fill ever.
- MECHANISMS (lane B; 3810e2c4+dda6852c): exactly 3 candidates + 1 conditional —
  C1 SOS-adjusted Elo, C2 home/away split rating, C3 offseason EPA prior (train-only),
  C4 short-week×away (conditional, gated on train-internal slice CI; power predicts
  starvation). All replacement-rating shape with designed-null parents reproducing B1*.
  Rejects: MOV-weighted Elo, K/HCA/rest/form re-grids, additive-over-elo_diff features,
  in-season pbp, injuries, 538/odds/current-box. Power: MDD(80%) 1 season 0.026–0.056,
  2 seasons 0.019–0.039, train-internal ~0.006–0.013 → plausible effects (0.002–0.010)
  are starved prospectively; train-internal adjudication FIRST, prospective accrual after.
  Lane-B rights statuses were written PENDING_LANE_A (parallel execution): RESOLVED by
  lane A's landed audit — nflverse CC BY 4.0 PASS for results/schedules/pbp (train-only
  for pbp-derived EPA), injuries NOT_RUN_PIT as above.
- PROTOCOL (lane C; 02fc0434+4bb14932): TRAIN = audited complete seasons < 2019
  (placeholder 2000–2018; exact list is a freeze-packet fact from lane A coverage);
  2019–2025 cite-only (spent); 2026+ prospective only from ledger timestamps.
  Rolling-origin train-internal selection with disclosed selection ledger, frozen
  pre-look. ≤9 arms: B0, B1* (K=40/HCA=0/γ=2/3, mandatory), ≤3 lane-B candidates,
  conditional interaction slot (G-INT gate), ONE named reserve, 2 slots released.
  Log loss primary; Brier/10-bin/slope band [0.85,1.15]; paired ΔLL date-cluster
  bootstrap 10,000 resamples seed 20261005 (inherited); T1–T3/R1–R3; playoffs separate;
  ≥2-new-season rule (~≥540 games) + no outcome-based prospective early-stop.
  Prediction ledger nfl_ng_ledger@1: append-only JSONL, no outcome columns,
  recorded_at_utc < kickoff_utc enforced at append AND scoring, sha256 hash chain from
  freeze GENESIS, postponement rules, SYNTHETIC examples only.
- VERIFY (lane D; 6a09045a+d79ff685): D-1..D-10 all PASS; 1 minor defect (D2-a) +
  observations (handoff_B workers:1; two-commit backfill disclosed) — none blocking.

## Downloads ($0 only; outside git)

~/.my-quantitative-data/nfl-ng-prep-v1/ — 14 sha256-pinned files (license/datasets docs,
fresh 2026 schedules compile, injuries 2025+2026, teams crosswalk, audit script); existing
nfl-nflverse-v1 archive byte-untouched (re-hashed, all match). No accounts/keys/purchases.

## Next authorized path (requires owner; this cycle registers/consumes no GO)

1. Owner decides successor scored cycle registration (fresh cycle id, freeze, A7, typed GO
   at its own gate). 2. Freeze packet binds: TRAIN season list (lane A), candidate arms
   (lane B C1–C3 + conditional C4), protocol+ledger (lane C), reserve identity, recorder
   cadence (weekly ≥6h margin placeholder before first kickoff UTC; earliest opportunity
   2026-10-06T00:15:00Z week-4 remainder). 3. Prospective ledger opens only inside the
   successor cycle; every 2026 game played before its freeze stays NOT_RUN prospective.

## Addendum r1 (owner follow-up round, 2026-10-05)

- D2-a REMEDIATED (lane A r1, ADJUDICATION): two §1 license quotes replaced with true verbatim
  text from the pinned LICENSE bytes ("exercise the Licensed Rights… reproduce and Share…";
  attribution "(s)" restored) + dated ERRATUM; verifier r2 confirmed 2-hunk diff only, rights
  verdict unaffected.
- 2026 recount (07:16:19Z, verifier-r2 reproduced 07:23:28Z): 272 / 63 played all-final /
  209 future 0-scored / earliest future kickoff 2026-10-06T00:15:00Z (2026_04_ATL_NO).
- LEDGER TOOL landed (lane E): research/control/NFL-WINPROB-NG-PREP-V1/ledger/ —
  nfl_ng_ledger@1 append-only, hash-chained, no outcome columns, pre-kickoff law enforced at
  append AND scoring; 42/42 SYNTHETIC tests (verifier r2 re-ran + 4 adversarial probes).
- Verifier r2: PASS 6/6, 0 defects (VERIFICATION_R2.md; observations O-1 registry-head
  housekeeping done this commit round, O-2 R10 vocabulary restated in FREEZE_PACKET_DRAFT §4,
  O-3 in-chat round-2 dispatch recorded in event log).
- NEW controller artifacts: FREEZE_PACKET_DRAFT.md + OWNER_DECISION_PACKET.md (this round).
- Still: 0 scored, no GO, $0, no real-game prediction written anywhere.
