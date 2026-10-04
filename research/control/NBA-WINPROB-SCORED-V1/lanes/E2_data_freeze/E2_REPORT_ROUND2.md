# E2 REPORT — ROUND 2 (DELTA) — data/freeze re-verification after AMENDMENT_1

- Cycle: NBA-WINPROB-SCORED-V1
- Lane: E2_data_freeze (round 2, fresh context, everything re-measured)
- Date: 2026-10-04
- Worktree: /Users/hoangminhlong/my-quantitative/.worktrees/nba-winprob-scored-v1/integration
- Branch: orca/nba-winprob-scored-v1-integration
- Measured HEAD: `227e3faa81c1cb3d8a458c6d5d47a32a104a7f4d` (tree clean)
- Pinned code_freeze_sha (manifest v2): `2c64b6f34b0b2cf46db7243418f5b929a6a5b4c8` = HEAD~1
- Python: /Users/hoangminhlong/my-quantitative/.venv/bin/python (all commands)

## VERDICT (one line)

**DELTA PASS with ONE LAUNCH-BLOCKING FINDING**: all remediation targets of
AMENDMENT_1 (features rebuild with plain `elo_diff`, real-CSV tests, selftest v2,
hardened gates) are green; BUT the freeze-v2 commit changed
`nba_winprob/make_freeze_manifest.py` AFTER the pinned code_freeze_sha, so the
runner's own drift gate refuses at current HEAD — controller must re-pin (or
revert) before A7 round 2 can authorize.

## 1. FREEZE_MANIFEST.json (schema @2) + git freeze scope — MIXED

PASS:
- `schema` = `nba_winprob_scored_freeze@2`. `supersedes` block present:
  code_freeze_sha `39b1115632d06b159c5c78a470d2d0bff3cb8386`, reason
  "AMENDMENT_1 remediation (owner-independent rejection; 0 outcomes ever
  computed)", old_manifest = `research/control/NBA-WINPROB-SCORED-V1/FREEZE_MANIFEST.SUPERSEDED_BLOCKED.json`.
- Both supersede artifacts exist: `FREEZE_MANIFEST.SUPERSEDED_BLOCKED.json`
  (verified content: schema @1, code_freeze 39b11156, features sha
  `644cd740a5006c33fb0cf093244644fb02c6ffea6e680962ec624554ea3cf799`) and
  `SUPERSEDED_NOTE.md` ("SUPERSEDED_BLOCKED (handbook §24) — 2026-10-04 ... 0
  outcomes ever computed (ledger 9 PREREGISTERED / 0 COMPUTED)").
- `code_freeze_sha` 2c64b6f3... is a commit in history (HEAD~1); commit message
  is the AMENDMENT_1 remediation (D1-D4 fixes, 33/33 tests, selftest v2).
- Ledger cross-check: TRIAL_LEDGER.jsonl = 9 PREREGISTERED / 0 COMPUTED —
  pre-outcome state confirmed; results/ dir empty.
- amendment_digest `e7531c7e47f2e6e92235e3ccd5f4078365346e78518d0a10217a9d3f343e53bc`
  matches recomputed sha256 of AMENDMENT_1.md; protocol_digest
  `c058760d...` matches lanes/C_protocol/PROTOCOL_EVAL.md.

FAIL (strict letter of the check):
- `git diff --name-only 2c64b6f3..HEAD` = **two** paths:
  `nba_winprob/make_freeze_manifest.py` (+30/−23) and
  `research/control/NBA-WINPROB-SCORED-V1/FREEZE_MANIFEST.json`.
  So "diff touches ONLY research/control/**" and "nba_winprob/ byte-unchanged
  since 2c64b6f3" are FALSE as written.
- Mitigating scope: the ONLY nba_winprob/ file that changed is the manifest
  GENERATOR itself (updated in HEAD 227e3faa to emit schema @2 — the commit is
  titled "freeze v2"; manifest was generated with worktree HEAD at 2c64b6f3 per
  its commit message "code_freeze <this-commit-parent HEAD measured at
  generation>"). Every evaluation-path file (run_evaluation.py, elo.py,
  features.py, export_features.py, evaluate.py, protocol.py, build_dataset.py,
  all tests) is byte-identical to the freeze sha.
- CONSEQUENCE (launch-blocking): `check_launch_gates` (run_evaluation.py
  L307-312) computes `git diff --name-only <code_freeze_sha> HEAD` and refuses
  on ANY `nba_winprob/` path. Measured live (see §4c): gate emits
  `CODE DRIFT (nba_winprob/ immutable): ['nba_winprob/make_freeze_manifest.py']`
  and `post-freeze drift outside allowlist: ['nba_winprob/make_freeze_manifest.py']`.
  As landed, evaluation CANNOT launch. Remediation is controller-level: commit
  the generator change first, re-generate the manifest with code_freeze_sha =
  that commit (nba_winprob/ then immutable from the pin), or revert the
  generator delta. E2 does not merge/rewrite; flagging only.

## 2. Data + attribution hashes — PASS (KEY DELTA CONFIRMED)

Recomputed sha256 (streamed, 1 MiB chunks) of every manifest entry:

| entry | pinned | recomputed | match |
|---|---|---|---|
| raw_nbaallelo | d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc | same | YES |
| games | e24d9a3b1feb5f9e5b0408c1e0c93d34c2137f174788667dd082754ec636f098 | same | YES |
| lineages | c8cdd58ac9105eacd2d39d3737cc62ab08a61667cd15b93011b04695650061c1 | same | YES |
| participants | fd7cb5394e09b6d7c649507b1a410143fd1de21127ec56a6d81c0ee01285c1bf | same | YES |
| features | c86f104d9c30a67f4735592d31308dab3c95d55998d80d51822d2679e50fc86b | same | YES |
| attribution (ATTRIBUTION.md) | e134e20cca04d76a6bb23dbfb3c44b80b0cec0e8679c1945fc7246d824fb490a | same | YES |

KEY DELTA: features.csv pin = `c86f104d...` and the recomputed on-disk hash
EQUALS it; the OLD hash `644cd740...` (still visible in the SUPERSEDED_BLOCKED
manifest) does NOT match the on-disk file. The freeze therefore pins the
REBUILT features.csv, not the pre-remediation file. 6 hand-verified hashes, 0
mismatches.

## 3. Real-CSV regression proof — PASS

- Header (verified by column enumeration): plain **`elo_diff` at column 8**;
  columns 9-15 rest_diff/b2b_home/b2b_away/form_home/form_away/rest_home/
  rest_away; then the four suffixed pairs at columns 16-23:
  `elo_diff_B1-a`/`p_home_B1-a`, `elo_diff_B1-b`/`p_home_B1-b`,
  `elo_diff_B1-c`/`p_home_B1-c`, `elo_diff_B1-d`/`p_home_B1-d`. 63,157 data
  rows + header (63,158 lines).
- `cd <worktree> && .venv/bin/python -m pytest nba_winprob/tests -q` →
  **33 passed in 40.51s** (includes nba_winprob/tests/test_real_csv_path.py —
  the A4 real-CSV schema/rows/load_rows tests, no outcome metrics).
- `.venv/bin/python -m nba_winprob.run_evaluation --synthetic-selftest ...` →
  `SELFTEST PASS v2: 9 arms, 7 comparisons (pooled+per-fold), verdicts emitted,
  fold reliability/slope present, bootstrap deterministic; no real data touched.`
  exit 0. (Selftest prints PROGRAM_PASS=false / REJECT=true on synthetic
  fixtures — that is the fixture outcome, not a pipeline failure; the v2 banner
  and exit 0 are the acceptance signals.)

## 4. Refusal behavior — PASS with one exit-code delta

- 4a `python -m nba_winprob.evaluate` (no manifest) → **exit 3**, stderr
  "REFUSED: no --freeze-manifest. NBA-WINPROB-PREP-V1 has budget 0 scored
  cells and no GO phrase by law ...". PASS.
- 4b `python -m nba_winprob.run_evaluation --freeze-manifest <real v2
  manifest>` with NO `--go-record` → **exit 2, NOT 3** (delta): argparse has
  `--go-record` as `required=True`, so it exits with the usage error ("error:
  the following arguments are required: --go-record") BEFORE check_launch_gates
  runs. The refusal is still absolute (evaluation cannot run without a GO
  record), but the specified exit code 3 + "GO-record reason" from the gate is
  unreachable on this path. Cosmetic/spec deviation; controller may align
  (make the flag optional and let the gate emit reason + exit 3) or accept
  argparse's 2. No evaluation occurred.
- 4c same command with a malformed GO record (valid JSON, phrase
  "GO WRONG PHRASE") → **exit 3** with reasons:
  `GO record phrase mismatch` (target check PASSES), plus the expected
  not-yet-satisfied launch conditions surfaced by the same run:
  CODE DRIFT (see §1), post-freeze allowlist drift (same file), and
  `A7 prelaunch report missing: .../audits/AUDIT_PRELAUNCH_ROUND2.md` (round-2
  A7 pending — by design at this stage; audits/ still holds only round-1
  AUDIT_PRELAUNCH.md). No evaluation occurred; ledger untouched.

## 5. Rights re-check (2 fetches, 2026-10-04) — PASS → DATA_RIGHTS_OK

- Fetch 1: https://raw.githubusercontent.com/fivethirtyeight/data/master/README.md
  → sentence intact verbatim: "Unless otherwise noted, our data sets are
  available under the Creative Commons Attribution 4.0 International License"
  (continues with code under MIT). Matches ATTRIBUTION.md quote.
- Fetch 2: https://raw.githubusercontent.com/fivethirtyeight/data/master/nba-elo/README.md
  → provenance intact verbatim: "Game information is from
  Basketball-Reference.com." (plus team_id note "from Basketball Reference").
  Dataset confirmed as the Historical NBA game-level log behind nbaallelo.csv.
- Both conditions of the usage boundary (CC BY 4.0 disclosure + BRef
  provenance disclosure) remain satisfiable; local ATTRIBUTION.md carries the
  mandatory attribution string unchanged (hash pinned in manifest, §2).

## 6. Plan immutability + amendment — PASS

- `/Users/hoangminhlong/my-quantitative/plans/PLAN_nba_winprob_scored_v1.md`:
  git blob at root commit a92e16eb = `d6bd9a2437556e689225b50f52a4057480ff1ad7`;
  `git hash-object` of the current file = same blob; root repo status clean for
  that path; a92e16eb ("G0 bootstrap ... owner directive 2026-10-04 round 2
  explicitly NOT a typed GO") is the ONLY commit touching the plan and is an
  ancestor of root main HEAD (5fb4bb76). Plan UNCHANGED since G0.
- AMENDMENT_1.md lives only inside the worktree control dir (not a plan edit);
  its recomputed sha256 equals manifest `amendment_digest` (§1). Amendments are
  registered as A1-A4 in the amendment; hypotheses/arms/folds/thresholds
  unchanged per its own text.
- Note: the integration branch does not track plans/ (control-plane
  separation) — `plans/PLAN_nba_winprob_scored_v1.md` is absent from the
  integration branch tree by design; verification was done against the root
  repo where the plan is authority.

## Pending launch conditions (not E2 defects, restate for A7 round 2)

1. CODE DRIFT finding of §1 must be resolved (controller re-pin or revert).
2. `audits/AUDIT_PRELAUNCH_ROUND2.md` must exist and contain
   A7_PRELAUNCH_AUTHORIZED (A7 round 2, fresh).
3. Structured owner GO record (phrase/cycle_id/typed_by=owner/typed_at) — none
   exists; go_phrase_state REGISTERED_NOT_CONSUMED.
4. Heavy lock FREE_PROVEN at launch; clean tree (currently clean).

## Evidence command log (all run 2026-10-04, venv python)

- git: rev-parse HEAD → 227e3faa81c1...; cat-file -t 2c64b6f3 → commit;
  diff --name-only 2c64b6f3..HEAD; diff --stat 2c64b6f3..HEAD -- nba_winprob/;
  root repo: cat-file/rev-parse a92e16eb:plans/...; hash-object plan;
  merge-base --is-ancestor (YES for root main).
- sha256 recompute over manifest["data"] + attribution: 6/6 MATCH.
- pytest nba_winprob/tests -q → 33 passed in 40.51s.
- run_evaluation --synthetic-selftest → SELFTEST PASS v2, exit 0.
- evaluate (no manifest) → exit 3; run_evaluation (no --go-record) → exit 2;
  run_evaluation (wrong-phrase GO) → exit 3.
- WebFetch x2 (538 root README; nba-elo README) — both license/provenance
  sentences intact.
