# DISPATCH — Lane PIPE (NFL-WINPROB-NG-SCORED-V1, wave B) — REAL RECORD PIPELINE + FREEZE ERRATUM

ROLE: implementation + freeze-remediation lane. Build the REAL prediction-record pipeline
(real schedule read → state warmup with pre-game-valid info only → batch probabilities →
≥6h margin check → append-only ledger write) and test it END-TO-END ON SYNTHETIC FIXTURES
ONLY before GO. Also resolve two documented freeze defects via an ERRATUM: the ATL@NO
wording contradiction and the missing state-carry law (selection caps 2018/2017).
ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-ng-scored-v1/integration
BRANCH: orca/nfl-winprob-ng-scored-v1-integration · DISPATCH SHA: ecf8371abf7839ca49e9245c99f8aa7386d48fdd
ALLOWED PATHS (write): lanes/PIPE/**, research/control/NFL-WINPROB-NG-SCORED-V1/recorder/**,
sandbox fixtures under ~/.my-quantitative-data/nfl-ng-scored-v1/{recorder_sandbox,raw_pbp_2018_2020}/,
+ lanes/DISPATCH/handoff_PIPE.json. You also WRITE the ERRATUM into lanes/FREEZE_ERRATUM_R2/
(the controller moves/commits it — do NOT edit lanes/F_FREEZE/FREEZE_PACKET.md in place;
append-only discipline).
FORBIDDEN: git; computing or recording p_home for ANY real game (warmup state and counts
only — no per-game probability values for real games anywhere in your outputs); creating the
real ledger; modifying lanes/T_SELECT or lanes/F_FREEZE files; touching 2019+ outcomes for
any evaluation purpose (state-carry update of completed games is NOT evaluation — see law
below); S1; purchases; betting vocabulary.

## Task 1 — pbp 2018–2020 download (state-carry input)
Download play_by_play_{2018,2019,2020}.parquet (release `pbp`) into ~/.my-quantitative-data/
nfl-ng-scored-v1/raw_pbp_2018_2020/ with full provenance (url/http/downloaded_utc/bytes/
sha256) extending the A_DATA manifest format. License pin applies (2a82ac9b…; re-fetch once,
byte-identical expected). Purpose: recorder warmup applies C3 boundary priors for seasons
2019–2026, requiring prior-season pbp 2018–2025 (2021–2025 already in the archive, read-only).

## Task 2 — RECORDER pipeline (research/control/NFL-WINPROB-NG-SCORED-V1/recorder/)
record_batch.py (+ modules) implementing, in order:
(a) SCHEDULE LOAD: read the versioned games.csv snapshot (path + sha256 pinned; the frozen
    r1 snapshot for fixtures; at real record time a fresh snapshot is pulled and its sha +
    pull time enter inputs_digest — implement the pull function but DO NOT execute it now).
(b) STATE WARMUP (state-carry law): replay ALL completed games (final scores present,
    kickoff strictly < batch timestamp) through the FROZEN arms: B1* K=40 HCA=0 γ=2/3
    updates; C3 θ=50 boundary priors from prior-season REG pbp EPA z (pbp 2000–2025 pinned).
    HARD LEGALITY ASSERTS: any game with kickoff ≥ batch timestamp carrying a score ⇒ ABORT
    (corrupt/stale snapshot); no metric/LL is computed on ANY game during warmup; arm params
    are read-only constants (assert equality with the freeze digests).
(c) BATCH PREDICT: for the target week's games (all REG+POST games of that week from the
    snapshot), compute p_home per fielded arm from the warmed state with identical-kickoff
    exclusion inside the batch (same-kickoff games never inform each other).
(d) MARGIN CHECK: refuse unless batch_write_time + 6h ≤ first kickoff of the batch (fail
    loud, nothing written).
(e) LEDGER APPEND: via the ported nfl_ng_ledger tool (research/control/NFL-WINPROB-NG-
    SCORED-V1/ledger/nfl_ng_ledger.py), to a TARGET PATH argument. Real path only AFTER GO —
    all your runs use sandbox paths.
(f) --selftest: hand-computed fixtures (margin arithmetic; kickoff-UTC canonicalization;
    state-carry counts; identical-kickoff exclusion; abort-on-future-score).
(g) WARMUP-ONLY REAL SMOKE CHECK (--mode warmup-check): run stages (a)+(b) on the REAL
    frozen snapshot with batch_time = your run time; emit ONLY aggregate counts (games
    processed per season, ratings-initialized lineages, prior applied per boundary) and
    assert results — ZERO probability values for real games emitted or written; report
    goes in your lane dir only. This validates the 2018-cap resolution on real bytes
    without producing predictions.
(h) END-TO-END SYNTHETIC FIXTURES (--mode e2e-synth): synthetic schedule file in the REAL
    games.csv format (SYNTH_ ids, 2027+ kickoffs, synthetic completed history incl. 2+
    completed synthetic seasons so C3 priors exercise), synthetic pbp-free prior z inputs
    via a synthetic prior table OR synthetic pbp fixture in the real schema — run the FULL
    pipeline → margin gate → sandbox ledger append → chain validation. ≥3 fixture scenarios:
    nominal week; margin-violation refusal (batch < 6h before kickoff ⇒ refuse, nothing
    written); future-score abort (doctored snapshot row with score on a future game ⇒ ABORT).
    Determinism: double-run byte-identical.

## Task 3 — FREEZE ERRATUM (lanes/FREEZE_ERRATUM_R2/ERRATUM_R2.md + freeze_digests_r2.json)
(1) ATL@NO RESOLUTION (per registered Option B; window unchanged): FREEZE_PACKET §4 currently
    says pre-week-5 games "become capturable ONLY if the capture rule is satisfied for them
    before their own kickoff" — this wrongly admits week-4 capture and contradicts the gate
    brief's forfeit-by-design. Erratum: capturable weeks = week 5 (first kickoff 2026-10-09)
    onward ONLY; 2026_04_ATL_NO and all pre-week-5 games are NOT_RUN prospective forever
    (forfeit-by-design under Option B); the ≥6h margin rule applies within the capturable
    window; the registered window is NOT changed by this erratum (it enforces it).
(2) STATE-CARRY LAW (resolves the 2018/2017 selection caps): T_SELECT's SEASON_MAX_GAMES=2018
    / SEASON_MAX_PBP=2017 caps are PERMANENT for selection (selection closed; SPENT window
    2019–2025 never re-selected). The RECORDER is a separate module with its own load law:
    it consumes completed-game outcomes (final scores) through the batch timestamp for
    rating/prior updates ONLY — this is the as-of law's admissible information set, not
    evaluation; no LL/metric is computed on any SPENT-window game; arm parameters are
    immutable constants from the freeze. pbp 2018–2020 files are state-carry inputs (pinned
    in freeze_digests_r2).
(3) RECORDER FREEZE: sha256 of record_batch.py + modules at handoff; RECORDER_FREEZE_SHA =
    the integration HEAD containing them (measured by controller two-step addendum — same
    precedent as CODE_FREEZE_ADDENDUM); recorder provenance of pbp 2018–2020.
(4) Updated GENESIS payload digest: recompute the canonical GENESIS payload sha256 with the
    UPDATED freeze digest (placeholder created_at=POST_GO_TIMESTAMP, code_freeze_sha=the
    real 7ec4c539… value now known, recorder_freeze_sha=PENDING_CONTROLLER_ADDENDUM
    placeholder) — pin as GENESIS_PAYLOAD_DIGEST_R2 superseding ae99a803… (state that the
    old digest is superseded and why).
Re-run the FULL S_SYNTH suites (predecessor 42 + successor 16) against the current tree after
your changes — record results (they must remain green; you add tests, you never weaken them).

## Deliverables
lanes/PIPE/{PIPELINE_REPORT.md (design + laws + test matrix + warmup-check counts + e2e
fixture results), VERDICT_TABLE.md}; research/control/.../recorder/**; lanes/FREEZE_ERRATUM_R2/**.
HANDOFF: zcode_orch_v3_handoff@1 at lanes/DISPATCH/handoff_PIPE.json (task_id
nfl-winprob-ng-scored-v1-PIPE, dispatch_sha=actual_start_sha=ecf8371a…, commit_sha=null).
STOP CONDITIONS: license divergence on re-fetch; any fixture producing real-game
probabilities (design bug — fix before continuing); ledger tool suite regression.
