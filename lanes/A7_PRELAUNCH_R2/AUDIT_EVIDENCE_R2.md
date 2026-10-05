# AUDIT_EVIDENCE_R2 — A7_PRELAUNCH_R2 re-audit, cycle NFL-WINPROB-NG-SCORED-V1

Auditor: A7 independent re-auditor. HEAD audited `1e41b8dd2cc7888b41bdb412ba882896376b65c2`
(== dispatch SHA). Interpreter for every command:
`/Users/hoangminhlong/my-quantitative/.venv/bin/python`. Git: READ-ONLY commands only
(rev-parse/cat-file/log/status/rev-list). All probe outputs under
`lanes/A7_PRELAUNCH_R2/tmp/`; no audited artifact modified. Recorder mode re-runs executed
in-process with the module's output-path globals (`LANE_DIR`, `RECORDER_SANDBOX`, `E2E_DIR`)
redirected into this lane's tmp before invocation — audited code bytes and PIPE evidence bytes
untouched (PIPE sandbox ledger re-hashed after my runs: `cf92d600…` == pre-run value).

## R2-1 — SHA chain (exit 0 each)

```
git cat-file -t {f55dab66,ecf8371a,46bd3b54,3e52b7b1,1e41b8dd}  -> commit (x5)
git log --format='%H %P %s' -n1 1e41b8dd -> parent 3e52b7b1…  (ERRATUM_R2 controller addendum)
git log --format='%H %P %s' -n1 3e52b7b1 -> parent 46bd3b54…  (Lane PIPE)
git log --format='%H %P %s' -n1 46bd3b54 -> parent ecf8371a…  (Lane INV_C2)
git log --format='%H %P %s' -n1 ecf8371a -> parent 25df9a9a…  (Control PRELAUNCH_READY_PENDING_OWNER_GO)
git rev-list --merges f55dab66..1e41b8dd | wc -l  -> 0
git rev-list --count f55dab66..1e41b8dd           -> 14 (linear)
[ "$(git rev-parse HEAD)" = 1e41b8dd2cc7888b41bdb412ba882896376b65c2 ] -> YES
git rev-parse --abbrev-ref @{u} -> fatal: no upstream configured (never pushed)
git status --porcelain -> only '?? lanes/DISPATCH/DISPATCH_A7_PRELAUNCH_R2.md' (by design)
```

## R2-2 — ERRATUM_R2 coherence

- Predecessor Option B (read from bytes,
  `nfl-winprob-ng-prep-v1/.../NFL-WINPROB-NG-PREP-V1/OWNER_DECISION_PACKET.md` L17–19):
  "week-5 slate (from 2026-10-09) becomes the first prospective window".
- ERRATUM_R2.md §1: capturable = week 5 onward ONLY; opener `2026_05_TB_DAL`
  2026-10-09T00:15:00Z; pre-week-5 (incl. `2026_04_ATL_NO`) NOT_RUN prospective forever;
  ≥6h margin within the window; "The registered window is NOT changed by this erratum".
- Window identity: `2026-10-09T00:15:00Z` occurrences — FREEZE_PACKET.md 1, ERRATUM_R2.md 3
  (restatements of the same instant); plan kickoff measurement identical.
- Defective sentence confirmed present in the unchanged packet §4 and superseded by the
  erratum (append-only; packet on-disk sha256 `9978a950…` == pin ⇒ bytes untouched).
- Standing OWNER_GATE_BRIEF.md already disposed `2026_04_ATL_NO` as "forfeit-by-design …
  NOT_RUN prospective forever like the 63" — consistent with erratum §1.2.
- File digests (recomputed): FREEZE_PACKET.md `9978a950cfa52f531c6cc1ccf650ca46cfcecb5a0d38c8468f6a66381ef70f6e`;
  ERRATUM_R2.md `98681cde8f638b6a3686b4bc7cdd4286babd576343b1b5dacf3653f6e9939356` ==
  freeze_digests_r2.json `erratum.sha256`; freeze_digests_r2.json itself
  `d62f2a2a4da816d6d7b90277d5c735e4cd36224ca52d1e7932a1976b4a9a1cde` (controller to pin at
  next CAS write — the file cannot contain its own digest).

## R2-3 — State-carry law

- Caps (frozen `lanes/T_SELECT/arms.py`): `SEASON_MAX_GAMES = 2018` (L26), filter L137,
  assert L140; `SEASON_MAX_PBP = 2017` (L27), loop bound L377, assert L382. arms.py sha256
  `19dddd3ff2bec808e549981473e0523b4178cfd8c7c0db7c08b7e41a86d7d3e8` == freeze §9 pin;
  select.py `8f733d45…`, boot.py `0674b95f…` == §9 pins.
- Recorder separation + warmup law (code-read, all five modules):
  - `schedule.py` L135–137: warm mask = `(ko < batch_ts) & (home_score.notna() & away_score.notna())`
    — completed games only; L108–117 `future_score_violations` = kickoff ≥ batch AND scored
    → `FutureScoreAbort` (L31), raised BEFORE any compute in both `mode_warmup_check`
    (record_batch.py L681–685) and `_run_batch_scenario` (L466–468).
  - `pipeline.py` `warmup_aggregates` returns counts only; no `log(`/metric/LL exists in the
    warmup path; `format_p_home` is reached only from `predict_target_week`, which
    `mode_warmup_check` never calls. `_assert_synth_only` (record_batch.py L88–96) is invoked
    in the batch path (L473).
  - `frozen_refs.py`: sha-asserted read-only imports (arms.py `19dddd3f…`, ledger tool
    `6fb0a1d4…`); `verify_arm_config_digests()` recomputes §1.1 digests == pins every run
    (exercised in all three of my recorder runs).
- pbp 2018–2020 provenance: on-disk sha256s == pins (2e6f2dce…/60c30670…/8889f5d8…), byte
  sizes == pins (19,072,097 / 19,119,729 / 19,286,459), PAR1 magic verified by me ×3,
  DOWNLOAD_MANIFEST.json present; license `rights/nflverse-data_LICENSE.md` and
  `provenance/nflverse-data_LICENSE_refetch_PIPE_20261005.md` BOTH sha256
  `2a82ac9bbc3e3ee066908381e8d373896db5a6025d083fbd59692fe9ccfb9111` == pin, 18,651 B each.
- My independent warmup-check re-run on the frozen snapshot (486d7227… pin verified by the
  loader): exit 0; `completed_games_total=7080`, `games_2026_absorbed=63`,
  `future_unplayed=209`, `future_with_score_violations=0`, `lineages_initialized=32`,
  `z_table_entries=830`, `probabilities_emitted=0`, 0 `p_home` fields — equals PIPE's
  2026-10-05T12:21:39Z run on every count.

## R2-4 — Recorder tests re-run at THIS SHA

- `record_batch.py --mode selftest` → exit 0, 10/10 PASS (arm-config digest equality; margin
  arithmetic; kickoff canonicalization; hand Elo/prior; warmup counts; exclusion canaries;
  future-score abort; fresh-pull guard; p-format guard; prefix bit-equivalence; tool identity +
  genesis distinctness). stdout archived `tmp/selftest_stdout.json`.
- `--mode e2e-synth` re-run (harness `tmp/run_e2e_synth_redirect.py`, outputs redirected):
  exit 0. Scenario 1: 24 rows, margin 173.0h, fixture sha `e4a3fa70d3ded5c8cbc30f74b836977bdceb896b2069649525e3fbbbdfbafab3`
  and ledger sha `cf92d600e7bf337f00bd593a7c45d9f6cfa09161244e6ff8f9848713a45a308a` —
  byte-identical to PIPE's pinned evidence; determinism double-run BYTE-IDENTICAL; scenario 2
  margin 5.98h → `MarginRefusal` + nothing-written assert PASS; scenario 3 doctored
  future-score (`SYNTH_2030_W3_G01`) → `FutureScoreAbort` + nothing-written assert PASS;
  `real_ledger_paths_existing: []`; chain intact; scoring rehearsal 24×`VALID_PROSPECTIVE`.
  Evidence `tmp/e2e_rerun/e2e_rerun_evidence.json`.
- Zero-probability greps: `p_home` field count in `lanes/PIPE/warmup_check_evidence.json` = 0;
  `"probabilities_emitted": 0`; my rerun sandbox ledger: 24 rows, all `game_id` values
  `SYNTH_2030_W3_G01..08` ×3 arms, 0 non-SYNTH rows; real-game-id regex
  `[0-9]{4}_[0-9]{2}_[A-Z]{2,3}_[A-Z]{2,3}` across lanes/PIPE + lanes/A7_PRELAUNCH_R2/tmp +
  recorder_sandbox: exactly ONE hit — prose schedule-fact mention of `2026_04_ATL_NO` in
  PIPELINE_REPORT.md (no probability value associated). No real game_id carries a probability
  anywhere.

## R2-5 — GENESIS R2 digest

```
canonical V2 (sorted keys, ',' ':' separators, ensure_ascii=false, UTF-8):
{"arm_set_ids":["B0","B1_STAR","C3"],"code_freeze_sha":"7ec4c539…","created_at":"POST_GO_TIMESTAMP",
 "cycle_id":"NFL-WINPROB-NG-SCORED-V1","diagnostic_arm_ids":["C3_TWIN"],"freeze_digest":"9978a950…",
 "recorder_freeze_sha":"PENDING_CONTROLLER_ADDENDUM","schema":"nfl_ng_scored_v1_genesis@1"}
sha256 -> bd94eb77d35077ac7bc1761a2c61031a1cdf2f53c6d8be181de5ddfcefd51483  == pin (MATCH)
R1 cross-check (§6 fields, code_freeze_sha=PENDING_CONTROLLER_ADDENDUM, no recorder field):
sha256 -> ae99a803dfcc280e85d46bdc192a5b1a042320af127f688d66481ba3f1aaa3e7  == R1 pin (MATCH)
canonical string == freeze_digests_r2.json genesis_r2.canonical_payload_v2 literal: True
```

## R2-6 — INV_C2 integration

- CONTROLLER_ADDENDUM.md (commit 1e41b8dd): RECORDER_FREEZE_SHA
  `3e52b7b1de64c8e2f04867cee37524886c6b3111` = the PIPE commit (verified ==
  `git rev-parse 3e52b7b1`); disclosure binds twin adjudication (vs reference AND vs own
  parent, MACHINERY_SUSPECT only when twin beats own parent with parent slope in
  [0.85,1.15]) and states "gates T1-T3/R1-R3, arms, windows and grids are UNCHANGED".
- Bytes unchanged: FREEZE_PACKET.md `9978a950…` (gate text §7 intact — T1 grep found;
  slot 4 C2 KILL+MACHINERY_SUSPECT; slot 5 C3 FIELD); arm files == §9 pins;
  `SELECTION_LEDGER.jsonl` == `ff698d5d85e6144022bca7475daa3c2054ea92adc7a167549488e290fcedfd5a`
  (INV_C2 changed nothing it investigated); event_log `erratum_r2_landed 2026-10-05T14:07:40Z`.

## R2-7 — Suites (mine, at THIS SHA)

```
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider \
  research/control/NFL-WINPROB-NG-SCORED-V1/ledger/test_ledger_synthetic.py -> 42 passed (0.30s) exit 0
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider \
  lanes/S_SYNTH/test_successor_synthetic.py                                -> 16 passed (0.92s) exit 0
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider \
  lanes/PIPE/test_recorder_synthetic.py                                    -> 3 passed (1.37s) exit 0
```

Side-effect disclosure (N5): the PIPE pytest suite invokes the recorder CLI as a subprocess,
which regenerated `lanes/PIPE/e2e_synth_evidence.json` (only wall-clock `ran_utc` changed;
all shas/counts/verdicts byte-identical — deterministic fixtures). The exact committed bytes
were restored from `git show HEAD:lanes/PIPE/e2e_synth_evidence.json`
(sha256 `d8aa004eb818e6ba76b6a0456d30f6f0e29387bbcf26397f7443ca9fc66f2475` == committed blob;
post-restore `git status`: file unmodified). Substantive re-run evidence for the recorder
comes from the auditor's OWN redirected runs (R2-4), which reproduce PIPE's pinned claims
byte-exactly.

## R2-8 — Boundaries

- Real ledger absence: `find` worktree → 0 `prediction_ledger*`/`predictions_…2026*`; data-dir
  top-level `*.jsonl` → 0; only `recorder_sandbox/e2e/run{1,2}/predictions_NFL-WINPROB-NG-SCORED-V1-PIPETEST_2030.jsonl`
  (SYNTH sandbox; sha `cf92d600…` == claim, re-hashed UNTOUCHED after my redirected runs).
- state.json: phase `PRELAUNCH_READY_PENDING_OWNER_GO`; budget `0/9`; `s1 SEALED_UNTOUCHED`;
  go_phrase "(registered, NOT typed; P-8 two-key)"; workers 0.
- GO-phrase grep (worktree, md/json/py/jsonl): 8 files — plans/PLAN, state.json,
  freeze_digests.json, FREEZE_PACKET.md (§10 boundary text), handoff_F_FREEZE.json,
  handoff_A7_PRELAUNCH.json, A7_PRELAUNCH_VERDICT.md, OWNER_GATE_BRIEF.md. Zero in the new
  INV_C2/PIPE/FREEZE_ERRATUM_R2 lanes. No push (no upstream, R2-1).
- Betting vocabulary: only negative boundary statements ("no betting vocabulary") — compliant.

## R2-9 — Designed-null + cap probes (script `tmp/r2_9_null_and_cap_probe.py`, results `tmp/r2_9_results.json`)

- arms.py pin asserted at import; own 12-row stream (2025/2026, same-kickoff batch, tie,
  neutral, short-rest row, z-prior boundary):

```
C1_B000 max|Δp| = 0.0            .tobytes() equal: true    (power C1_B025  Δp 3.757e-4)
C2_NULL max|Δp| = 0.0            .tobytes() equal: true    (power C2_h25   Δp 1.562e-2)
C3_T000 max|Δp| = 0.0            .tobytes() equal: true    (power C3_T050  Δp 6.218e-2)
C4_D000 max|Δp| = 0.0            .tobytes() equal: true    (power C4_D025  Δp 1.562e-2)
doctored 2019 row: n_dropped_over_ceiling=1, rows surviving 2, max season 2018, season_leak false;
backstop assert on unfiltered frame -> "season > SEASON_MAX_GAMES leaked" (loud, fired);
odds bait columns quarantined at load: ["home_moneyline","spread_line"]
```

- Note: first run's C4 power check was vacuous due to MY stream construction (no short-rest
  away row); C4_D000 identity held in both runs; stream patched (my own tmp) → nonzero power.
  Auditor-owned fix only; no audited artifact touched.
