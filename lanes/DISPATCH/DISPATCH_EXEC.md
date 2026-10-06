# DISPATCH — Lane EXEC (WNBA-PLAYERFEAT-SCORED-V1) — REAL OOS RUNNER + WINDOW RESOLUTION + ERRATUM_R1

ROLE: implementation lane. Complete the REAL OOS evaluation runner so it executes post-GO
(authority from registry), and settle the OOS window per the "7 complete seasons" law WITHOUT
touching OOS outcomes. Pre-GO the runner is proven ONLY on synthetic data (exactly 2 arms
B0/B1-WNBA); real-data runs refuse until a live GO exists in the registry.
ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/wnba-playerfeat-scored-v1/integration
BRANCH: orca/wnba-playerfeat-scored-v1-integration · DISPATCH SHA: 3bbd2b79190a162d1386f65e2a9c8ffb91d6c455
ALLOWED PATHS (write): lanes/EXEC/**, research/control/WNBA-PLAYERFEAT-SCORED-V1/runner/**,
lanes/FREEZE_ERRATUM_R1/**, sandbox ~/.my-quantitative-data/wnba-playerfeat-scored-v1/
{exec_sandbox,exec_fixtures}/, + lanes/DISPATCH/handoff_EXEC.json.
FORBIDDEN: git; computing OOS metrics on REAL 2019+ data (any season beyond warm-up/train
caps) under ANY fixture — the pass-path proof uses synthetic OOS seasons only; modifying
lanes/T_SELECT or lanes/S_SYNTH files; betting vocabulary; touching OOS outcome values to
decide the window (schedule/tip-time facts only).

## Task 1 — WINDOW RESOLUTION (documented, from bytes; no outcome reads)
Law (plan, inherited packet): OOS = final 7 COMPLETE seasons at the successor's data freeze;
pin was [2020..2026]. Measure completeness from SCHEDULE facts in the frozen corpus
(~/.my-quantitative-data/wnba-prep-v1/roster_audit/ + the frozen feature table's tip_utc
columns): for season 2026, count universe-law games with tip_utc > freeze instant
(2026-10-05T12:10Z state heartbeat; use the feature-table build instant as the freeze
anchor and disclose). Controller pre-measurement from the frozen feature table: 2026 = 682
rows / 341 games, tip range 2026-05-08T23:30Z → 2026-10-03T01:00Z, ZERO future tips → 2026
COMPLETE at freeze → OOS = [2020, 2021, 2022, 2023, 2024, 2025, 2026] exactly as frozen.
Your job: re-verify from the RAW corpus (game_rosters/player_box dates or the underlying
schedule the table was built from), document the determination in WINDOW_RESOLUTION.md
(facts, counts, tip maxima per season 2024/2025/2026, the law quote, the conclusion); if your
raw-bytes measurement CONTRADICTS the controller's (any future-tipped 2026 game), STOP and
record the discrepancy as a freeze contradiction for the controller (do not resolve it
yourself). Also state: at post-GO run time the runner re-asserts every OOS game has tip_utc
< run time (a game still in the future at run time would mean the corpus was stale — refuse).

## Task 2 — Runner (research/control/WNBA-PLAYERFEAT-SCORED-V1/runner/run_oos.py)
Argument-driven (--registry path defaults REAL plans/CYCLE_REGISTRY.json; --source real|synth;
--seasons list; --out results dir). GATE CHAIN, each audited + distinct exit codes, nothing
computed on refusal:
G1 AUTHORITY: registry row WNBA-PLAYERFEAT-SCORED-V1; PASS iff lifecycle ACTIVE_* AND
   go_phrase_state starts with `OWNER_GO_TYPED_LIVE` (canonical convention — identical to the
   NFL ERRATUM_R3 convention; defined here in ERRATUM_R1: when the owner types
   `GO WNBA PLAYERFEAT SCORED V1 EVALUATION` at the gate, the controller records
   `OWNER_GO_TYPED_LIVE <utc-iso> at head <40-hex>`; all other states refuse). Registered
   phrase equality check included.
G2 FREEZE COHERENCE: worktree HEAD == registry head; arms.py sha256 == T_SELECT-era pin
   (recorded in ERRATUM_R1); B1-WNBA config constants in code == frozen K=32/HCA=50/γ=0.65
   and B0 == 0.603755 (assert both); no φ parameters present (feature arms released — assert
   the runner CANNOT arm them: no acceptance path).
G3 LOCK: researchctl locks inspect FREE_PROVEN (retry 3×60s; refuse on conflict).
G4 WINDOW: seasons argument == [2020..2026] exactly (refuse any other list incl. 2019 or
   missing years); at run time assert every OOS game tip_utc < run time; data source = the
   frozen corpus paths; any missing season/game set ⇒ refuse with census (no silent shrink).
G5 SINGLE BATCH: one process computes all arms on the identical game set; exact-arm record
   ids pairwise distinct; non-vacuous (≥1 row per arm).
On ALL-PASS with --source real: load corpus, replay warm-up 1997–2001 + stream 2002–2019
(train/stream), predict OOS 2020–2026 with the 2 arms, compute frozen metrics (LL primary;
Brier; 10-bin reliability; calibration slope; paired ΔLL B1-WNBA vs B0 with tip-date-cluster
bootstrap 10,000 resamples seed 20261005), apply the frozen falsifier language (packet §3
REJECT-vs-B0 rule), write results JSON + markdown to --out. In YOUR testing --source real is
never run past G1 against the real registry (it must refuse); the pass-path proof uses
--source synth with synthetic OOS seasons (2027/2028 synthetic, corpus-format fixtures).

## Task 3 — Synthetic proof + exact-arm dry-run (lanes/EXEC/test_runner_gates.py)
Fixture cases (distinct exit codes, nothing-computed on refusal): (a) REAL registry as-is ⇒
G1 refuse pre-read (audit hook proves no real data read); (b) fixture GO-typed-live +
--source synth + synthetic seasons [2027, 2028] + sandbox out ⇒ FULL PASS: 2 arms, identical
game sets, metrics computed + hand-fixture cross-check (small closed-form example), ΔLL
bootstrap smoke, exact-arm identity, non-vacuous, deterministic double-run; (c) CONSUMED /
DEAD / wrong-phrase states ⇒ refuse; (d) head mismatch ⇒ G2 refuse; (e) B1 config tamper
(HCA=51) ⇒ G2 refuse; (f) φ-arming attempt (attempting to add a feature arm) ⇒ G2 refuse;
(g) lock-conflict injection (or NOT_RUN_LOCK_SIM disclosure) ⇒ G3; (h) wrong seasons list
(2019..2025) ⇒ G4 refuse; (i) future-tipped synthetic game ⇒ G4 refuse; (j) empty season ⇒
G4 refuse with census. Re-run lanes/T_SELECT --selftest (must stay 14/14) + S_SYNTH suites.

## Task 4 — ERRATUM_R1 (lanes/FREEZE_ERRATUM_R1/ERRATUM_R1.md + freeze_digests_r1.json)
(1) authority ruling: execution-surface addition via ERRATUM; arm code untouched; (2) runner
module sha256 pins; RUNNER_FREEZE_SHA = controller two-step addendum (PENDING placeholder);
(3) canonical GO-recording convention (same string law as NFL); (4) gate-chain spec G1–G5;
(5) WINDOW_RESOLUTION binding: OOS = [2020..2026] with the measured facts; windows/arms/
metrics unchanged.

## Deliverables
lanes/EXEC/{RUNNER_REPORT.md, VERDICT_TABLE.md}; runner + gate tests; WINDOW_RESOLUTION.md;
ERRATUM_R1 files.
HANDOFF: zcode_orch_v3_handoff@1 at lanes/DISPATCH/handoff_EXEC.json (task_id
wnba-playerfeat-scored-v1-EXEC, dispatch_sha=actual_start_sha=3bbd2b79…, commit_sha=null).
STOP CONDITIONS: raw-bytes window contradiction (report, don't resolve); unimplementable gate
(record BLOCKED_TOOLING); existing suite regression.
