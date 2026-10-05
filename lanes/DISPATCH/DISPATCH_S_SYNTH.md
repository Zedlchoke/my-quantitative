# DISPATCH — Lane S_SYNTH (NFL-WINPROB-NG-SCORED-V1, wave 4) — SYNTHETIC TESTS + DRY-RUN

ROLE: test/dry-run lane. Port the predecessor ledger tooling into this cycle, extend with
successor-level synthetic tests, and rehearse the full record pipeline on SYNTHETIC games in
a SANDBOX ledger. The real prediction ledger must NOT exist when you finish.
ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-ng-scored-v1/integration
BRANCH: orca/nfl-winprob-ng-scored-v1-integration · DISPATCH SHA: e08e4c423f64c06012be9ad63bfe1a9769d175a4
ALLOWED PATHS (write): lanes/S_SYNTH/**, research/control/NFL-WINPROB-NG-SCORED-V1/ledger/**
(the ported tool + its tests), sandbox data under ~/.my-quantitative-data/nfl-ng-scored-v1/
sandbox/, + lanes/DISPATCH/handoff_S_SYNTH.json.
READ-ONLY: everything else (incl. the predecessor worktree holding the source tool).
FORBIDDEN: git; creating/writing any REAL ledger path (the real ledger file must not exist at
handoff); touching lanes/T_SELECT code (test it, never modify it); real game data as dry-run
inputs; metrics on real outcomes; betting vocabulary.
SOURCE TOOL (port from): /Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-ng-prep-v1/
integration/research/control/NFL-WINPROB-NG-PREP-V1/ledger/{nfl_ng_ledger.py,
test_ledger_synthetic.py, README.md} — record each file's sha256 before/after port (port must
be byte-identical or changes documented line-by-line in PORT_NOTES.md; prefer byte-identical).
TASKS:
1. Port tool + tests; run the full predecessor synthetic suite → expect 42/42 PASS (exit 0).
   If any test fails after a byte-identical port, STOP with TECHABORT evidence.
2. Successor synthetic tests (new file test_successor_synthetic.py):
   a. Designed-null prediction equivalence: using lanes/T_SELECT/arms.py UNMODIFIED, on ≥3
      synthetic game streams, arms configured with β=0/λ=0∧h=0/θ=0/δ=0 must produce p_home
      arrays byte-identical (max |Δp| = 0) to B1*.
   b. Frozen-config determinism: C3 θ=50 on a fixed synthetic stream twice → identical bytes.
   c. As-of fixtures: a game predicted at t must not see a result with kickoff ≥ t (inject a
      canary later-kickoff result; assert it is absent from the prediction inputs).
   d. Kickoff-margin validator: batch rows with recorded_at within 6h of kickoff → rejected
      per the freeze margin law (if the tool exposes margin config; else test the timestamp
      law recorded_at < kickoff strictly).
   e. Hash-chain tamper: mutate one sandbox ledger byte → chain validation fails loudly.
3. SANDBOX DRY-RUN: generate a synthetic week of games (SYNTH_-prefixed game_ids, synthetic
   team lineages, synthetic kickoffs in the far future 2027+ so no real-game collision is
   possible); compute p_home for the 3 fielded arms (B0 const; B1* replay over a synthetic
   prior stream; C3 θ=50 with synthetic prior-season EPA z inputs); write rows into
   ~/.my-quantitative-data/nfl-ng-scored-v1/sandbox/prediction_ledger_sandbox.jsonl via the
   PORTED tool (sandbox GENESIS from a sandbox digest — NOT the freeze GENESIS digest
   ae99a803…, never reuse it); verify chain validates; exact-arm identity: (game,arm) rows
   pairwise distinct; row count = games × arms; zero real game_ids (assert prefix).
   Confirm the REAL ledger path (research/control/NFL-WINPROB-NG-SCORED-V1/ledger/
   prediction_ledger.jsonl or wherever the tool's default real path resolves) does NOT exist
   at the end (record the checked paths + absence).
4. DRYRUN_REPORT.md: every command + exit code + counts + the real-path absence assertions.
   VERDICT_TABLE.md: PASS/FAIL/NOT_RUN per check.
HANDOFF: zcode_orch_v3_handoff@1 at lanes/DISPATCH/handoff_S_SYNTH.json (task_id
nfl-winprob-ng-scored-v1-S-SYNTH, dispatch_sha=actual_start_sha=e08e4c42…, commit_sha=null).
STOP CONDITIONS: predecessor suite not green after byte-identical port; any designed-null
mismatch (TECHABORT — do not touch arms.py, report); accidental real-ledger creation (delete
nothing — STOP and report the incident).
