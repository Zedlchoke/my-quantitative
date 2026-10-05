# A7_PRELAUNCH_VERDICT_R2 — NFL-WINPROB-NG-SCORED-V1 (fresh re-audit, post-ERRATUM_R2 tree)

- Lane: `A7_PRELAUNCH_R2` (independent auditor, RE-AUDIT; prior A7 PASS at ecf8371a NOT inherited)
  · Written: 2026-10-05 (UTC)
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-ng-scored-v1/integration`
  · Branch `orca/nfl-winprob-ng-scored-v1-integration` · HEAD audited
  `1e41b8dd2cc7888b41bdb412ba882896376b65c2` (== dispatch SHA). Interpreter throughout:
  `/Users/hoangminhlong/my-quantitative/.venv/bin/python`. Method: every checklist item recomputed
  from bytes at THIS SHA; probes read-only; outputs only under `lanes/A7_PRELAUNCH_R2/tmp/`;
  no audited artifact modified (recorder mode re-runs were executed with module output paths
  redirected into this lane's tmp; the PIPE sandbox bytes were left untouched and re-hashed equal).
  Command/exit-code detail: `AUDIT_EVIDENCE_R2.md` (same directory).

## VERDICT: A7_PRELAUNCH_R2_PASS

Zero blocking findings across R2-1..R2-9. The changed tree (INV_C2 + PIPE + FREEZE_ERRATUM_R2 +
recorder + controller addendum) reconciles with the standing frozen chain; every recomputation
matched its pin exactly. The prelaunch gate remains ready for the owner typed-GO decision
(P-8 two-key: this verdict first, then the owner types
`GO NFL WINPROB NG SCORED V1 PROSPECTIVE` verbatim at this cycle's own gate — never an agent).

## Per-check table

| # | check | verdict | decisive evidence (all recomputed at 1e41b8dd) |
|---|---|---|---|
| R2-1 | SHA chain base f55dab66 → … → ecf8371a (prior A7 control state) → INV_C2 46bd3b54 (= 3e52b7b1^) → PIPE 3e52b7b1 → ERRATUM addendum 1e41b8dd; linear; clean tree | **PASS** | All 5 named commits exist (`git cat-file -t`=commit), single-parent each, 0 merges in `f55dab66..1e41b8dd` (14 commits, linear); parentage verified: 1e41b8dd→3e52b7b1→46bd3b54→ecf8371a→25df9a9a; HEAD == dispatch sha; no upstream configured (never pushed); `git status` clean except the untracked R2 dispatch packet (by design) |
| R2-2 | ERRATUM_R2 coherence: ATL@NO resolution == registered Option B; OWNER_GATE_BRIEF text governs consistently; registered window NOT widened | **PASS** | Predecessor OWNER_DECISION_PACKET Option B verbatim: "week-5 slate (from 2026-10-09) becomes the first prospective window" — erratum §1 restates and ENFORCES it (capturable = week 5 onward ONLY; opener `2026_05_TB_DAL` 2026-10-09T00:15:00Z appears identically in FREEZE_PACKET §4 and ERRATUM_R2, 1 occurrence each; 3 in erratum incl. deadline restatements); the defective §4 sentence ("becomes capturable ONLY if … before its own kickoff") is superseded, closing the week-4 loophole — the erratum only NARROWS capture, never widens; `2026_04_ATL_NO` + all pre-week-5 = NOT_RUN prospective forever; standing `OWNER_GATE_BRIEF.md` already carried the identical forfeit-by-design disposition ("week 5 is the first target; … NOT_RUN prospective forever like the 63"); FREEZE_PACKET bytes unchanged on disk = pin `9978a950…`; ERRATUM_R2.md bytes = pin `98681cde…` (freeze_digests_r2 `erratum.sha256`); ≥6h margin restated as applying WITHIN the window; week-5 batch deadline 2026-10-08T18:15:00Z |
| R2-3 | State-carry law: T_SELECT caps intact; recorder separate; warmup consumes completed games only with future-score ABORT; NO metric in warmup; pbp 2018–2020 provenance complete | **PASS** | Caps grep-intact in frozen `arms.py` (`SEASON_MAX_GAMES = 2018` L26 with hard filter L137 + assert L140; `SEASON_MAX_PBP = 2017` L27 with loop bound L377 + assert L382); arms.py sha == pin `19dddd3f…`, select.py/boot.py == §9 table pins; recorder is a separate consumer with its own load law (ERRATUM §2; `schedule.py` warm mask = both scores present AND kickoff strictly < batch ts, L135–137; `future_score_violations` = kickoff ≥ batch AND scored → hard `FutureScoreAbort` BEFORE any compute, wired in both modes); no logarithm/metric/LL anywhere in the warmup path (pipeline.py warmup_aggregates returns counts only; grep of recorder modules shows no `log(` on game data; my independent warmup re-run emitted 0 probabilities); pbp 2018–2020 on disk: sha256 == pins (2e6f2dce/60c30670/8889f5d8), bytes == pins, PAR1 magic ×3 verified by me, manifest present; license copies (rights + PIPE refetch) both == pin `2a82ac9b…` 18,651 B |
| R2-4 | Recorder tests re-run at THIS SHA: --selftest + --mode e2e-synth (all 3 scenarios) + warmup-check zero-probability grep | **PASS** | My `--mode selftest`: exit 0, 10/10 PASS. My `--mode e2e-synth` (in-process, output paths redirected to my tmp): exit 0; scenario 1 nominal 24 rows / margin 173.0h, fixture sha `e4a3fa70…` and ledger sha `cf92d600…` BYTE-IDENTICAL to PIPE's pinned claims; determinism double-run byte-identical; scenario 2 margin 5.98h → `MarginRefusal`, nothing written (dir empty assert); scenario 3 doctored future-score → `FutureScoreAbort`, nothing written; real-ledger paths existing = []; scoring rehearsal 24×`VALID_PROSPECTIVE`. My independent `--mode warmup-check` on the frozen snapshot (486d7227 verified): exit 0, 7,080 completed / 63 in 2026 / 209 future / 32 lineages / 830 z / `probabilities_emitted: 0` — matches PIPE exactly. Greps: `p_home` fields in warmup evidence = 0; ledger rows all `SYNTH_*` (0 non-SYNTH rows); real-game-id regex across PIPE lane + my tmp + sandbox = exactly ONE prose mention (PIPELINE_REPORT.md names `2026_04_ATL_NO` as a kickoff fact, no probability attached); ZERO real game_ids in any output byte carrying probability values |
| R2-5 | GENESIS R2: recompute canonical payload digest from erratum's stated canonical form | **PASS** | Recomputed sha256 of the canonical V2 payload (sorted keys, `,`/`:` separators, ensure_ascii=false, UTF-8; `code_freeze_sha=7ec4c539…` real, `created_at=POST_GO_TIMESTAMP`, `recorder_freeze_sha=PENDING_CONTROLLER_ADDENDUM`) = `bd94eb77d35077ac7bc1761a2c61031a1cdf2f53c6d8be181de5ddfcefd51483` == pin exactly; my canonical string == the erratum's literal twin byte-for-byte; R1 supersession cross-check: §6-fields payload (no recorder_freeze_sha, code_freeze_sha=PENDING) recomputes to `ae99a803…` == R1 pin exactly; supersession reason (two byte-level payload changes) verified from bytes; recorder selftest asserts sandbox genesis ≠ R1 and ≠ S_SYNTH genesis; freeze packet `freeze_digest` input unchanged |
| R2-6 | INV_C2 verdict integration: addendum discloses twin-adjudication guidance WITHOUT changing gates/arms/windows; C2 stays OUT; C3 ADMIT untouched | **PASS** | CONTROLLER_ADDENDUM.md (committed at 1e41b8dd) adds disclosure only: "gates T1-T3/R1-R3, arms, windows and grids are UNCHANGED"; FREEZE_PACKET bytes unchanged (= §7 gate text intact, T1 grep found; §1 arm table intact incl. slot 4 C2 KILL+MACHINERY_SUSPECT and slot 5 C3 FIELD); arm-config digests unchanged (recomputed == pins by the recorder's `verify_arm_config_digests` in both of my runs); frozen arm files byte-identical to §9 pins; SELECTION_LEDGER.jsonl on disk == pin `ff698d5d…` (INV_C2 modified nothing it investigated); windows unchanged (2026-10-09T00:15:00Z present in packet §4 verbatim); event_log records `erratum_r2_landed 2026-10-05T14:07:40Z` matching the addendum; the guidance direction matches INV_C2 §7's own remediation proposal (adjudicate vs parent + slope context) and C2 remains OUT on three independent grounds stated in both INV_C2 §6 and the addendum |
| R2-7 | Full suites re-run at THIS SHA | **PASS** | My runs (PYTHONDONTWRITEBYTECODE=1, no cacheprovider — audited tree untouched): predecessor ledger suite `test_ledger_synthetic.py` **42/42 passed** exit 0 (0.30s); successor suite `test_successor_synthetic.py` **16/16 passed** exit 0 (0.92s); PIPE additions `test_recorder_synthetic.py` **3/3 passed** exit 0 (1.37s). Nothing weakened; additions only |
| R2-8 | Boundaries: real ledger absent; zero real-game probabilities; GO registered-not-typed; budget 0/9; no push | **PASS** | Worktree-wide find: 0 `prediction_ledger*`/`predictions_NFL-WINPROB-NG-SCORED-V1_2026*` files; data-dir top level 0 `*.jsonl`; only SYNTH sandbox ledgers exist (`…-PIPETEST_2030.jsonl`, sha `cf92d600…` == claim; PIPE sandbox re-hashed UNTOUCHED after my runs); state.json: `phase=PRELAUNCH_READY_PENDING_OWNER_GO`, `budget_scored 0/9`, `s1=SEALED_UNTOUCHED`, GO phrase "(registered, NOT typed; P-8 two-key)", workers 0; GO-phrase worktree grep = 8 files, all registered/boundary/verdict contexts, ZERO occurrences in the new INV_C2/PIPE/ERRATUM lanes; no upstream → no push; betting vocabulary absent (only negative boundary statements); zero real-game probability rows anywhere (R2-4 grep) |
| R2-9 | Designed-null + cap probes: independent re-run on MY OWN stream via frozen arms.py; doctored 2019-row probe | **PASS** | arms.py sha == pin asserted at import; my own 12-row stream (2 seasons 2025/2026, 6 lineages, same-kickoff batch, tie, neutral, short-rest row, C3 prior boundary): C1_B000 / C2_NULL (replay_c2 λ=0,h=0) / C3_T000 (replay_elo θ=0 with non-trivial z_table) / C4_D000 all **max |Δp| = 0.0 exactly AND `.tobytes()` equal** vs B1*; power checks all NONZERO (null not vacuous): C1_B025 3.76e-4, C2_h25 1.56e-2, C3_T050 6.22e-2, C4_D025 1.56e-2. Doctored 2019 row in a 3-row CSV: **dropped at load** (`n_dropped_over_ceiling=1`, 2 rows survive, max season 2018, no leak); backstop assert demonstrated loud on an unfiltered frame ("season > SEASON_MAX_GAMES leaked"); odds bait columns quarantined at load |

## Blockers

None.

## Disclosed notes (non-blocking)

- **N1 (window floor is caller-law, not a recorder assert).** The frozen recorder's
  `select_target_games(sched, batch_ts, target_season, target_week)` takes the week from its
  caller and contains no `week >= 5` assertion; the week-5-onward floor of ERRATUM_R2 §1 is
  enforced by the erratum law + the controller's batch choice + the ≥6h margin (code-enforced),
  and the frozen-code law forbids patching the recorder now (any change = new registered trial).
  The post-GO controller MUST select target weeks ≥ 5 only. Stated in OWNER_GATE_BRIEF_R2.md.
- **N2 (probe-construction fix, auditor-owned).** My first R2-9 run had a vacuous C4 power
  check (my synthetic stream gave no away team a ≤6-day rest); C4_D000 bit-identity held in
  both runs; I patched MY OWN stream (one lineage's week-1 game) and re-ran — final C4_D025
  power 1.56e-2. No audited artifact touched at any point.
- **N3 (R1 pin retained by design).** `freeze_digests.json` still carries the superseded R1
  pin `ae99a803…` and `frozen_refs.FREEZE_GENESIS_DIGEST_R1` is used only as a negative
  assertion (must NOT appear in any sandbox byte — verified 0 occurrences). The erratum's
  supersession + the addendum's "R1 digest ae99a803... superseded" statement govern; R1 must
  never anchor a ledger. Coherent append-only supersession, no silent edit.
- **N4 (owner-gate brief mechanics under the erratum).** The standing OWNER_GATE_BRIEF.md's
  generic "a week is capturable iff its batch lands on time AFTER your GO" sentence is
  consistent with the erratum only when read together with its explicit week-4 forfeit
  sentence; `OWNER_GATE_BRIEF_R2.md` (this lane) restates the floor explicitly so no
  week-4 path can be misread post-erratum.
- **N5 (auditor incident, disclosed + remediated in place).** My R2-7 re-run of
  `lanes/PIPE/test_recorder_synthetic.py` regenerated `lanes/PIPE/e2e_synth_evidence.json`
  as a subprocess side effect (the test invokes the recorder CLI without redirection; only
  the wall-clock `ran_utc` field differed — every sha/count/verdict byte-identical, since the
  fixtures are deterministic). Remediated immediately: the exact committed bytes were
  restored from `git show HEAD:…` (sha256 `d8aa004eb818e6ba76b6a0456d30f6f0e29387bbcf26397f7443ca9fc66f2475`,
  verified == committed blob) and `git status` confirms the file is no longer modified.
  No audited content changed at any point; final tree = only this lane's outputs + the
  dispatch packet + handoff, all untracked (by design).

## What this verdict does NOT do

It does not type, paraphrase, or consume the GO phrase; it does not open the prospective window
(capture opens only via the §4 capture rule as amended by ERRATUM_R2 §1, AFTER owner GO); it
does not validate any outcome claim (none exists — budget 0/9, zero real-game probabilities).
Terminal outcome on this evidence: **PRELAUNCH_READY_PENDING_OWNER_GO**, now with the erratum
amendments (week-5-onward-only capture; state-carry law; recorder freeze; GENESIS R2 anchor)
verified load-bearing at THIS SHA.
