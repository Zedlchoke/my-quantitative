# PLAN — NFL-WINPROB-WALKFWD-V1 (retrospective walk-forward OOS preparation, $0)

- cycle_id: NFL-WINPROB-WALKFWD-V1 · asset: shared · ACTIVE_LIGHT, budget 0/3 scored arms,
  GO phrase registered but NOT typed: `GO NFL WINPROB WALKFWD V1 SCORED REPLAY`
- owner authority 2026-10-07 (this chat): open ONE separate cycle to research and prepare a
  historical walk-forward OOS evaluation of NFL win probability. The live prospective cycle
  NFL-WINPROB-NG-SCORED-V1 (cadence, ledger, executor, dashboard) is NOT touched, edited,
  backfilled or re-pinned by this cycle — cited read-only only. $0 budget; no odds columns;
  no profit/edge inference; no S1, betting, purchases, push or merge. This round STOPS before
  the owner typed-GO gate and before ANY real OOS metric is computed.

## 1. Inheritance (pinned bytes; re-measured at bootstrap)

- Frozen arm specs = NFL-WINPROB-NG-SCORED-V1 FREEZE_PACKET.md (file sha256
  `9978a950cfa52f531c6cc1ccf650ca46cfcecb5a0d38c8468f6a66381ef70f6e`) with arm-config digests
  B0 `bea17ae4…aa5aa`, B1_STAR `5c97475c…cbf32a`, C3 `f7cde498…ecc74e`, C3_TWIN
  `c86b3710…36361`; arm code freeze sha `7ec4c539394e68538f74df327d85fa2a477c6eb7`
  (arms.py `19dddd3f…`, select.py `8f733d45…`, boot.py `0674b95f…`); selection ledger
  `ff698d5d…` (38 rows). Any deviation from these specs in this cycle is a NEW registered
  trial, never an amendment.
- Fielded arms for the scored replay (frozen): **B0** (constant p_home 0.571399049390),
  **B1_STAR** (own-Elo K=40, HCA=0, γ=2/3, μ=1500, tie update S=0.5), **C3** (B1_STAR +
  offseason EPA prior, config C3_T050 θ=50, z from prior-season pbp, γ=2/3). **C3_TWIN**
  (time-shuffled z, seed 20261005) = diagnostic-only, never a budget arm. C3 is fielded only
  if Lane A's PIT re-verification reconfirms PASS_PIT_SEASON_GRAIN; otherwise the C3 slot is
  released, budget drops to 2, and the release is recorded.
- Data pins (carry or re-measure): games.csv snapshot sha256
  `486d72273c0d9650756176fc016a0852c65ad6f030f443805c20cb35e387a9fc` (this cycle FREEZES this
  snapshot as its schedule/result authority); nflverse-data LICENSE sha256
  `2a82ac9bbc3e3ee066908381e8d373896db5a6025d083fbd59692fe9ccfb9111`; pbp 2000–2017 pinned
  (nfl-ng-scored-v1 manifest `bd53215d…`); pbp 2021–2025 archived read-only under
  `~/.my-quantitative-data/nfl-nflverse-v1/`; pbp 2018–2020 MISSING locally — Lane A
  downloads them fresh ($0, CC BY 4.0) with full provenance.
- Predecessor exposure (evidence of the past, cite-only):
  NFL-WINPROB-SCORED-V1 (TERMINAL, INCONCLUSIVE) already ran a per-season walk-forward on
  TEST 2019–2025 with 9 observed arms, including the B1-c spec (K=40, HCA=0) ≡ B1_STAR
  (pooled RS LL 0.6407) and an expanding-train B0 (pooled RS LL 0.6935, 1,865 RS rows).
  NFL-WINPROB-NG-PREP/SCORED selection read ZERO 2019+ outcome rows (asserted + audited);
  C3 has never been evaluated on any real outcome outside TRAIN 2000–2018 inner folds.

## 2. Exposure classification law (binding vocabulary)

Every artifact and every metric row of this cycle carries exactly one window class:

| window | class | binding statement |
|---|---|---|
| 2000–2018 | `TRAIN_INTERNAL` | Selection territory of both predecessor programs (grids, inner folds 2014–2018, C3 z-table, B0 rate). Fully exposed; never presented as OOS. |
| 2019–2025 | `RETROSPECTIVE_WALK_FORWARD` | Program-spent: outcomes observed and scored by NFL-WINPROB-SCORED-V1 (cite-only anchors). Virgin ONLY w.r.t. the C3 arm (never read by NG selection). NEVER called a new holdout; never pooled with prospective evidence; never a selection surface. |
| 2026+ | `PROSPECTIVE_2026` | Owned exclusively by NFL-WINPROB-NG-SCORED-V1. This cycle reads nothing from its prediction ledger for any metric; may reference its existence/counts only. |

Claim-law: a C3 win on `RETROSPECTIVE_WALK_FORWARD` supports/refutes the frozen mechanism
hypothesis under process discipline; it can never mint a fresh-holdout claim. Strong program
language still requires ≥2 completed prospective seasons from the live 2026 cycle. B0/B1_STAR
rows in this cycle are REPLICATION/consistency evidence, not new discoveries.

## 3. Walk-forward skeleton laws (frozen here; Lane C elaborates edge cases, never weakens)

1. Replay territory: seasons 2019–2025, regular season scored, playoffs scored separately
   (never pooled into RS aggregates); ties excluded from scoring with per-season counts
   disclosed (TIE LAW, S=0.5 update).
2. Ordering: games processed in kickoff-UTC order derived from the frozen snapshot
   (`gameday`+`gametime`, `America/New_York` via zoneinfo → UTC). State visible to a
   prediction = only games whose kickoff UTC is STRICTLY before the current batch's kickoff
   (completed games). Identical-kickoff games form ONE batch: every game in a batch is
   predicted from the same state; none of them updates state before the others.
3. Season boundary: C3 offseason prior applied before each lineage's first prediction of
   season s, computed from season s−1 completed REG games only (season-grain PIT,
   months of margin); ratings otherwise carry per B1_STAR law. 2000-season start μ=1500;
   the frozen 574-entry z-table (2001–2018 boundaries) is inherited verbatim; boundaries
   2019–2025 recomputed by the SAME formula from pinned pbp seasons (2018–2024).
4. Moved/postponed/cancelled (classification law): replay uses the frozen snapshot's FINAL
   scheduled state; a game whose played week/date differs from its nominal week schedule is
   labelled `MOVED_GAME_DISCLOSED` and scored at its final kickoff; a game with no final
   result (e.g. canceled 2022 BUF@CIN) = `NOT_SCORED_CANCELLED`, disclosed, never imputed;
   a game missing from the result join = `NOT_SCORED_NO_ACTUAL_DATA`. No inference from
   absence; every exclusion is counted in the freeze-consistent vocabulary.
5. Outcome-blind record law: the replay prediction ledger (`nfl_walkfwd_ledger@1`, adapted
   from `nfl_ng_ledger@1` with provenance) contains NO outcome columns, is append-only,
   hash-chained from a GENESIS anchored on this cycle's freeze packet, and must be fully
   written, committed and sha-pinned BEFORE the scoring pass joins outcomes. The scored pass
   (post-GO, one shot) reads the ledger + frozen snapshot read-only and emits metrics once.
   The recorded_at < kickoff law is a PROSPECTIVE-only law and is deliberately NOT asserted
   here; its replacement is the process law above, and every row carries
   `window_class=RETROSPECTIVE_WALK_FORWARD` so no row can ever be presented as a pre-game
   forecast.
6. Metrics (frozen): primary mean log loss on scored REG rows; secondary Brier, 10-bin
   reliability, calibration slope (binomial GLM, logit link) with band [0.85, 1.15];
   per-season columns ALWAYS alongside pooled; playoffs separate; paired ΔLL on identical
   game sets with 95% CI by kickoff-calendar-date cluster bootstrap, 10,000 resamples,
   percentile CI, **seed 20261007 frozen** (not a tuning knob); Δ<0 favors the arm.
7. Same-game-set law: B0/B1_STAR/C3 (and C3_TWIN diagnostics) are scored on the IDENTICAL
   row set; any row excluded for one arm is excluded for all, with counts.
8. REPLAY_CONSISTENCY gate (machinery elimination, frozen): the replay's B1_STAR pooled RS
   LL on 2019–2025 must reproduce the predecessor's B1-c anchor 0.6407 within pre-registered
   float tolerance (byte-identical if per-row anchors are recoverable; else max-abs-diff
   tolerance frozen by Lane C from the row-set reconciliation). B0 replication note: the
   predecessor's B0 was expanding-train (per-fold rate), this cycle's B0 is the frozen
   constant — the consistency comparison for B0 is definitional, expected to differ, and is
   documented as such, NOT a gate. Failure of the B1_STAR gate ⇒ MACHINERY_SUSPECT: scoring
   halts, nothing is published, remediation requires a new registered round.
9. Decision/elimination conditions for C3 on RETROSPECTIVE_WALK_FORWARD (frozen before the
   scored run; no re-tuning, no threshold relaxation, no metric/baseline substitution):
   - SUPPORT: pooled ΔLL(C3, B1_STAR) 95% CI entirely < 0 AND per-season ΔLL < 0 on ≥ 4 of
     7 seasons AND calibration slope in band.
   - REFUTE: pooled ΔLL(C3, B1_STAR) CI entirely > 0, OR pooled ΔLL(C3, B0) CI entirely > 0.
   - Else INCONCLUSIVE (all decision CIs include 0): no language upgrade anywhere.
   - Twin law: if C3_TWIN (shuffled-z) also shows CI entirely < 0 vs B1_STAR, the C3 signal
     is MACHINERY_SUSPECT regardless of the gates above.
   - Single-season slices are descriptive only. No outcome-based early stopping exists
     because the pass is one-shot.
10. Trial accounting: exactly one scored pass = 3 budget cells (B0, B1_STAR, C3) over the
    frozen territory; a deterministic re-run (reproduction twin, byte-identical, mandatory)
    is NOT a new trial; C3_TWIN is not a trial. Total budget 0/3 now; the pass consumes 3.

## 4. Tasks this round (all STOP before GO; zero real metrics)

1. Lane A — DATA/PIT: freeze-verify the games.csv snapshot (sha must equal 486d7227… or the
   divergence is a BLOCKED_DATA stop with disclosure); download pbp 2018–2020 fresh with
   URL+timestamp+bytes+sha256 each + ATTRIBUTION; re-verify license sha live; coverage
   census per season 2000–2026 (rows, REG/POST split, finals completeness, ties, neutral
   sites, moved-game census 2019–2025, same-kickoff batch census); pbp↔games lineage/EPA
   population audit 2018–2024 (C3 inputs); snapshot reconciliation vs the predecessor's
   scored row counts (255/255/271/269/272/272/271 RS by season); PIT verdict per feature
   class (schedule/result = final-snapshot post-hoc, pbp = PASS_PIT_SEASON_GRAIN offseason
   role only, injuries/weather/in-season-pbp/odds = NOT_RUN_PIT/BANNED carried); rights
   posture re-stated. Deliverables: lanes/A_DATA/{DOWNLOAD_MANIFEST.md+json,
   COVERAGE_TABLE.md, PIT_VERDICTS.md, DATA_AUDIT_WALKFWD.md, VERDICT_TABLE.md}.
2. Lane C — PROTOCOL: full walk-forward law doc elaborating §3 edge cases (DST fixtures,
   London/Mexico neutral games, Saturday/Tuesday slues, flex moves, bye weeks, COVID 2020
   moves); exposure classification table with per-window evidence citations (which artifact
   observed what, paths+shas); metrics/gates/elimination consolidation verbatim; trial
   budget statement; REPLAY_CONSISTENCY tolerance derivation; OWNER_GO_PACKET.md draft
   (exactly one scored pass, what runs, what it can/cannot conclude, trial cost 3).
   Deliverables: lanes/C_PROTOCOL/{PROTOCOL_WALKFWD.md, EXPOSURE_TABLE.md,
   OWNER_GO_PACKET.md}.
3. Lane S — SYNTH REHEARSAL: build the replay harness (arm math PORTED from frozen
   T_SELECT code with provenance; replay ledger `nfl_walkfwd_ledger@1` adapted from
   `nfl_ng_ledger@1`, source sha disclosed) + synthetic test battery on FAKE games only:
   as-of strictness (no game trains on itself/later kickoff), same-kickoff batching,
   season-boundary prior application, DST/timezone derivations (Sep vs Nov ET, UTC
   cross-check), moved/cancelled/missing-data classification, ledger hash-chain + tamper
   detection, θ=0 designed-null ≡ B1_STAR bit-for-bit, C3_TWIN determinism, full-pipeline
   rerun byte-identical, missing-input fail-closed. ZERO real-data rows anywhere; sandbox
   ledger paths only. Deliverables: lanes/S_SYNTH/{harness code, DRYRUN_REPORT.md,
   SELFTEST.log, VERDICT_TABLE.md}.
4. Controller — integrate lanes, write lanes/F_FREEZE/FREEZE_PACKET.md (bind arms, digests,
   windows, laws, metrics, gates, budget, GO packet) + freeze_digests.json + code freeze
   addendum; register the cycle (already done at bootstrap) and re-pin head; NO real rows.
5. Lane A7 — INDEPENDENT PRELAUNCH AUDIT at final HEAD: bytes vs claims, sha chain
   (base→code→freeze), synthetic battery re-run, exposure-table citations verified, PIT
   verdicts re-checked, no-real-metrics assertion, live-cycle isolation verified (NG-scored
   files/ledger untouched), boundary compliance (0/3 scored, GO not typed). Verdict honest.
   Deliverables: lanes/A7_PRELAUNCH/{A7_PRELAUNCH_VERDICT.md} + handoff.

## 5. Boundaries

- This round computes NO metric on real outcomes and writes NO real prediction rows. The
  scored pass happens only after: freeze committed + A7 verdict + owner types
  `GO NFL WINPROB WALKFWD V1 SCORED REPLAY` at this cycle's own gate (P-8 two-key).
- No edits ever to: NFL-WINPROB-NG-SCORED-V1 files/worktree/ledger/cadence, any TERMINAL
  cycle's artifacts, SPORTS-PAPERTRADE-* ledgers. Citation is read-only with sha.
- Quarantine carried: odds columns quarantined at load; in-season pbp features NOT_RUN_PIT;
  injuries/weather NOT_RUN_PIT; external forecasts BANNED; no PnL/betting/edge vocabulary
  anywhere (calibration/forecasting vocabulary only).
- Root checkout = control plane only. Lane work in the exact worktree
  `/Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-walkfwd-v1/integration`
  (branch orca/nfl-winprob-walkfwd-v1-integration), allowed write paths per dispatch packet.
  Data under `~/.my-quantitative-data/nfl-walkfwd-v1/`. Registry writes only via researchctl
  (CAS). No git from lanes; controller commits by pathspec. Heavy lock (FREE_PROVEN at
  bootstrap) taken around any heavy run; NOT_RUN_RESOURCE_CONFLICT if held; never kill
  foreign workers.

## 6. Artifacts

`lanes/{A_DATA,C_PROTOCOL,S_SYNTH,F_FREEZE,A7_PRELAUNCH,DISPATCH}/` in the integration
worktree; control state under `research/control/NFL-WINPROB-WALKFWD-V1/` (worktree side);
data under `~/.my-quantitative-data/nfl-walkfwd-v1/`. Every lane ends with handoff JSON
`zcode_orch_v3_handoff@1` at its dispatch handoff_path.

## 7. Terminal outcomes (negative-first)

PRELAUNCH_READY_PENDING_OWNER_GO (all lanes + A7 honest PASS, GO not typed, 0/3 scored) |
BLOCKED_DATA_RIGHTS | BLOCKED_TOOLING | TECHABORT_*. The GO phrase is owner-only, typed
verbatim at this cycle's own gate after reading the A7 verdict; agents never type it,
paraphrase it, or treat any state as GO.
