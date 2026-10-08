# PLAN — NBA-WINPROB-HCAL1-PROSPECTIVE-PREP-V1 (H-CAL1 prospective dual-recording PREP, $0)

- cycle_id: NBA-WINPROB-HCAL1-PROSPECTIVE-PREP-V1 · asset: shared · ACTIVE_LIGHT,
  budget max **2** arms (B1_STAR verbatim + H-CAL1 prospective; scoring later
  consumes from the same arms) · GO phrase registered but NOT typed:
  **`GO NBA WINPROB HCAL1 V1 PROSPECTIVE`** (owner-only, verbatim, at this
  cycle's own gate after A7).
- owner authority 2026-10-08 (second round, this chat): prepare the H-CAL1
  prospective test as its OWN cycle, separate from the NFL remediation cycle.
  B1* stays verbatim; H-CAL1 = single logit shrinkage with c=0.71 selected from
  TRAIN 2018–2021 ONLY. Every 2022–2026 number — including LL 0.630650 — is
  labeled **RETROSPECTIVE_DIAGNOSTIC_EXPOSED** (≡ the TUNE-PREP cycle's
  RETROSPECTIVE_DIAGNOSTIC_NOT_OOS label): never a new OOS, never a c re-selection
  input. This round's scope: plan → registration → implementation/control probes →
  freeze → synthetic rehearsal → independent A7 → decision packet. **STOP before
  every scored/real-game step and before the owner GO.** No change to the running
  paper model (NBA-WINPROB-PROSPECTIVE-PREP-V1 / SPORTS-PAPERTRADE-EXEC-V1);
  using H-CAL1 for bet decisions needs its own separate owner decision + gate.

## Inheritance (frozen pins; re-measured from bytes at this cycle's bootstrap)

- TUNE-PREP cycle SPORTS-WINPROB-TUNE-PREP-V1 TERMINAL at a7694a70 (registry):
  `FREEZE_PACKET_NBA.md`, `lanes/L_NBA/COEFF_FREEZE.json` (sha e00f6981…351f,
  c*=0.71, spec ERRATUM E1 sha af4362fe…9445, V1 run INVALID-never-consumed),
  `lanes/L_NBA/SPEC_FREEZE_H-CAL1.md`, `lanes/L_NBA/PROSPECTIVE_PROTOCOL_DRAFT.md`
  (ledger law §2, budget §3, evidence §4 — inherited verbatim), parity result
  (6,605/6,605 bit-exact vs TERMINAL ledger 7c267ec3…).
- B1* = own-Elo K=32/HCA=100/γ=0.75, constants FROZEN forever; null parent c=1.
- Windows: warm-up 2016–17; SEL 2018–2021 (consumed); 2022–2026 EXPOSED
  (RETROSPECTIVE_DIAGNOSTIC_EXPOSED forever); **fresh evidence = 2026–27+
  prospective only**. Dead-arm veto list unchanged (additive feature layers,
  MOV Elo, K/HCA/rest/form re-grids on 2009–2015, 538 forecasts, market odds as
  features, current-game box scores, player/team UN_SCORED arms).
- Data: `~/.my-quantitative-data/nba-hoopr-v1/` + `~/.my-quantitative-data/
  nba-ng-prep-v1/pbp_2016_2025/` read-only; hoopR CC BY 4.0 + MIT attribution.
  New ledger plane: `~/.my-quantitative-data/nba-hcal1-prospective-v1/`.

## Round tasks (STOP at PRELAUNCH_READY_PENDING_OWNER_GO; zero real-game rows)

1. **L-PIPE** — implementation + synthetic: port the B1* streaming engine
   (source: TUNE-PREP `lanes/L_NBA/code/b1_pipeline.py` d11eeb10… + NG-scored
   harness, byte-pinned provenance) into this cycle's tree; add H-CAL1 as
   p′=σ(0.71·logit p) with c loaded from a frozen coeff file (never inlined);
   implement the dual append-only chain ledger (`nba_hcal1_ledger@1`: both arms
   one row-pair per game, written_at_utc STRICTLY < tip_utc, arm_id, game_id,
   p, c, model_freeze_ref, prev_sha/row_sha chain, duplicate (game,arm)
   refusal, no-backfill refusal, missing-schedule fail-closed). Synthetic
   battery on FAKE games only: c=1 identity bit-parity vs B1* (max |Δp|=0.0),
   no-lookahead mutation probe, same-tip batch law, DST/tip-UTC canonicalization,
   chain tamper detection, full-pipeline rerun byte-identical, malformed input
   fail-closed. Schedule-refresh law DESIGN only ($0 rights-cleared source class
   per-run with provenance; no live ingestion this round). ZERO real 2026–27 rows.
2. **L-PROTO** — freeze + packet: FREEZE_PACKET.md pinning coefficient identity,
   ledger law, as-of law (date/tip-UTC grain inherited), universe/dedupe law,
   metrics (LL primary; Brier + calibration slope [0.85,1.15]; paired ΔLL
   date-cluster bootstrap 10,000, seed frozen by this cycle pre-look), interim-look
   ban (no scoring before season-1 end; single-batch per season), trial budget
   (2 arms; controls uncapped: c=1 parity, placebo, annual repro twin), decision
   conditions for the 2026–27 evaluation (directional gates + KEEP_B1STAR default;
   adoption into the paper chain is a SEPARATE owner decision), exposure table
   (2022–2026 = RETROSPECTIVE_DIAGNOSTIC_EXPOSED with LL 0.630650 quoted verbatim),
   OWNER_GO_PACKET.md (exact phrase, what one post-GO command runs, what it can
   never do).
3. Controller: sequential cherry-pick → freeze commit → **A7** fresh-context at
   final HEAD (hashes chain, synthetic re-run, PIT/as-of, no real rows, paper
   isolation byte-check, registry coherence) → decision packet → STOP.

## Boundaries

$0; no accounts/keys/purchases; no S1; no push/merge/rebase; registry writes only
via researchctl CAS; heavy lock machine-wide (bounded recheck ≥60s; never kill
foreign workers; a Q1-futures automation fires 13:30Z daily and the NFL NG cadence
00:00 local — expect brief contention); calibration vocabulary only, no
PnL/betting/edge; WNBA/soccer/paper programs untouched (byte-unchanged); missing
evidence = NOT_RUN_*; lanes write only their lane dirs + handoffs; handoff JSON
`zcode_orch_v3_handoff@1` at each handoff_path.

## Worktrees / branches

Integration `.worktrees/nba-winprob-hcal1-prospective-prep-v1/integration` on
`orca/nba-winprob-hcal1-prospective-prep-v1-integration`; lanes `…/lane-pipe`,
`…/lane-proto` on `orca/nbahc1-lane-pipe`, `orca/nbahc1-lane-proto`. Base SHA =
this plan's commit on main.

## Artifacts

`research/control/NBA-WINPROB-HCAL1-PROSPECTIVE-PREP-V1/` in each worktree:
`DISPATCH/`, `handoffs/`, `lanes/{L_PIPE,L_PROTO,A7}/`; at integration:
`FREEZE_PACKET.md`, `OWNER_GO_PACKET.md`, `EXPOSURE_TABLE.md`, `SYNTH_REPORT.md`,
`A7_PRELAUNCH_VERDICT.md`, `DECISION_PACKET.md`. Ledger plane (empty this round):
`~/.my-quantitative-data/nba-hcal1-prospective-v1/` (genesis + synthetic sandbox
only).

## Terminal outcomes (negative-first)

**PRELAUNCH_READY_PENDING_OWNER_GO** (all gates PASS, GO not typed, 0 real rows) |
BLOCKED_TOOLING | BLOCKED_DATA_RIGHTS | NOT_RUN_* | TECHABORT_*. The GO phrase is
owner-only; agents never type or paraphrase it. Nothing survives from any earlier
cycle's gate (P-8).
