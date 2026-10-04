# VERIFICATION_REPORT — NFL-WINPROB-SCORED-V1 (independent verifier, fresh context)

- verifier role: E2 data/freeze verification (G1), independent from PREP era
- date: 2026-10-04
- worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-scored-v1/integration`
- branch: `orca/nfl-winprob-scored-v1-integration`
- measured HEAD: `2ddef0863b37ca7edd7dd21ce4887ab3958fb888`
- authority note: PREP-era G4/G5 PASS verdicts were REOPENED by the owner's
  independent rejection and are NOT authority. Everything below was re-measured
  from bytes in this worktree and the pinned data root. This verifier never
  repairs; findings are recorded only.
- VERDICT: **VERIFICATION_PASS — 7/7 checks PASS, 0 HIGH, 0 CRITICAL, 3 LOW.**

## 1. Worktree state, commit scope, diff allowlist — PASS

- `git rev-parse HEAD` = `2ddef0863b37ca7edd7dd21ce4887ab3958fb888`; branch
  `orca/nfl-winprob-scored-v1-integration`; `git status --porcelain` empty (clean).
- Lineage verified: `9639706f` (remediated PREP tip) IS ancestor of HEAD.
- Commit log: `8cd0e1bc` (runner + freeze v1 + tests, 5 files, +891 lines:
  `nfl_winprob/make_freeze_manifest.py`, `nfl_winprob/run_evaluation.py`,
  `nfl_winprob/tests/test_scored_runner.py`, `FREEZE_MANIFEST.json`,
  `TRIAL_LEDGER.jsonl`) then `2ddef086` (freeze regen).
- `git diff --name-only 8cd0e1bc..HEAD` = exactly
  `research/control/NFL-WINPROB-SCORED-V1/FREEZE_MANIFEST.json` (2 insertions,
  2 deletions: `created_utc`, `code_freeze_sha` 9639706f → 8cd0e1bc) — inside
  `post_freeze_allowlist` (`research/control/NFL-WINPROB-SCORED-V1/**`,
  `results/**`). Zero files under `nfl_winprob/` changed since the code freeze
  commit (`grep -c "^nfl_winprob/"` on the diff = 0).

## 2. Hash chain recomputed — PASS

All sha256 recomputed 2026-10-04 from the pinned files; every value matches
`FREEZE_MANIFEST.json` (schema `nfl_winprob_scored_freeze@1`):

| file | recomputed | manifest | match |
|---|---|---|---|
| `~/.my-quantitative-data/nfl-nflverse-v1/raw/games.csv` | `f1e8fe781400c12874de639b10ce9f3badf7ad48640dfd7fff085c6f5e85248e` | same | YES |
| `~/.my-quantitative-data/nfl-nflverse-v1/derived/games_nfl.csv` | `f7909fa514dccdcba678bc5c2fbb01a31f9fa3159785ca33a0d96c8032151565` | same | YES |
| `~/.my-quantitative-data/nfl-nflverse-v1/derived/lineages_nfl.csv` | `977a43e22649e83387b4ff281d06e85fda4d42a577bcc0eb90910f5e0447aff0` | same | YES |
| `~/.my-quantitative-data/nfl-nflverse-v1/derived/features_nfl.csv` | `4ee2175eb549fda2bc1db48353272d51a6a528fb1a3d0f1b1a6b83f724f28982` | same (`4ee2175e…`) | YES |
| `~/.my-quantitative-data/nfl-nflverse-v1/raw/ATTRIBUTION.md` | `b18529758d62284a1711ce1ecbb9061ff1fee735a35c8a8aeac346d7e103aedc` | same | YES |

- Raw provenance is unchanged since PREP: `f1e8fe78…` appears verbatim in
  `raw/ATTRIBUTION.md` file-inventory table (pulled 2026-10-04T12:31:39Z) and in
  the PREP-era lane D verification record. Raw untouched.
- `lanes/NFL_C_protocol/PROTOCOL_EVAL_NFL.md` sha256 =
  `5b035a1c60bec899d48221e3e28fb28933a2735f630a8477f9b11ecac2f67c31` — matches
  manifest `protocol_digest`.

## 3. Remediation re-measured from bytes — PASS

Measured directly from `derived/games_nfl.csv` (schema: `game_type` normalized
lowercase + `game_type_raw` uppercase mirror) and `raw/games.csv`:

- total rows **7,066** (expected 7,066) — OK
- game_type: **reg = 6,768 / post = 298 / other = 0** — OK (remediation fix 1:
  the pre-remediation build marked all 7,066 games playoffs; measured now 6,768/298)
- `is_playoffs` consistency: **0 mismatches** under post→True / reg→False;
  `game_type_raw` mirror exact (REG=6768, WC=116, DIV=104, CON=52, SB=26 → 298
  post; 0 mirror mismatches) — OK
- ties = **15** (every tie row has home_pts == away_pts; zero equal-score rows
  left unflagged) — OK
- neutral = **95** — OK
- TEST window 2019–2025: derived **1,960 rows = 1,871 reg + 89 post** (raw
  census identical: 1,871 REG + 89 post); ties in window = **6**; scoring rows
  per TIE LAW = **1,865 reg-scoring + 89 post** (1,871 − 6 = 1,865) — OK
- lineages: **32**, `CLE` and `BAL` present as separate lineage ids; all 32
  lineage ids used by games (0 unused) — OK

## 4. Determinism (temp-dir rebuild; real derived untouched) — PASS

`cd <worktree> && .venv/bin/python -m nfl_winprob.build_dataset --raw
~/.my-quantitative-data/nfl-nflverse-v1/raw/games.csv --out /tmp/nflv2` then
`python -m nfl_winprob.export_features --games /tmp/nflv2/games_nfl.csv --out /tmp/nflv2`:

- build census: n_games 7,066; skipped pre2000 259 / unfinished 223 / bad_time 0;
  n_lineages 32 (lineage_count_ok true); n_ties 15; n_neutral 95
- `/tmp/nflv2/games_nfl.csv` = `f7909fa5…1565` (byte-identical to pinned)
- `/tmp/nflv2/lineages_nfl.csv` = `977a43e2…aff0` (byte-identical to pinned)
- `/tmp/nflv2/features_nfl.csv` = **`4ee2175e…98982` — byte-identical to the
  frozen features sha `4ee2175e5…` in the manifest. Determinism holds.**
- (The two `*_MANIFEST_NFL.json` artifacts embed `built_at_utc` timestamps and
  are not hash-pinned; the three data artifacts are the authority.)

## 5. Tests, selftest, refusal behavior — PASS

- `python -m pytest nfl_winprob/tests -q` → **23 passed** (30.4s). Named
  coverage confirmed by inspection: adversarial fixtures
  `test_same_kickoff_games_never_inform_each_other`,
  `test_same_kickoff_mutation_isolation`, `test_tie_update_half`,
  `test_tie_counts_half_win_in_form`, `test_form_regular_season_only_and_current_season`,
  `test_game_type_normalization`; real-CSV path tests
  `test_real_features_header` (asserts `elo_diff`/`p_home_{B1-*}` present and
  no `spread`/`moneyline`/`home_win`/`pts` tokens in the pinned features
  header) and `test_real_csv_load_and_split_counts` (asserts 7,066 rows,
  6,768/298, and TIE-LAW splits 1,865/89/6 against the real pinned files).
- `python -m nfl_winprob.run_evaluation --synthetic-selftest …` → prints
  `SELFTEST PASS: 9 arms, 11 comparisons (pooled+per-fold), verdicts emitted,
  fold reliability/slope present, bootstrap deterministic; no real data
  touched.` — exit 0. (The trailing JSON `PROGRAM_PASS:false / REJECT:true` is
  the verdict struct computed on RANDOM synthetic data — mechanics validation
  only; all in-function asserts passed. Expected by design, not a failure.)
- `python -m nfl_winprob.evaluate` → REFUSED on real outcomes, **exit 3**.
- `python -m nfl_winprob.run_evaluation --freeze-manifest <manifest> --go-record
  <nonexistent>` → `REFUSED — launch gates failed` listing (a) A7 prelaunch
  report missing, (b) no GO record — **exit 3** (captured without pipe masking).
  At audit time the A7-missing reason is expected (this audit did not exist
  yet); after `audits/AUDIT_PRELAUNCH.md` lands, the only remaining refusal
  reason is the absent structured GO record — see §7 of the A7 report.

## 6. Hygiene: no real-outcome metric; odds quarantine; raw untouched — PASS

- Token sweep (`spread|moneyline|vegas|closing|odds|bookmaker|betting`) over
  `elo.py`, `features.py`, `protocol.py`, `evaluate.py`, `export_features.py`,
  `run_evaluation.py`: **zero hits**. The only occurrences in the package are
  (a) `build_dataset.py` `QUARANTINED_COLUMNS` (the quarantine proof — betting
  columns named in order to be dropped) and (b) prohibition text inside
  `PROTOCOL_EVAL_NFL.md` leakage laws. Both are lawful mentions, not uses.
- Outcome columns (`home_pts`, `away_pts`, `home_win`, `tie`) are read only as
  realized outcomes (labels y, Elo updates, form). The exported features header
  (verified on the pinned file) contains no outcome column:
  `game_id, kickoff_utc, season, is_playoffs, home_lineage, away_lineage,
  elo_diff, rest_diff, short_week_home, short_week_away, form_home, form_away,
  rest_home, rest_away, elo_diff_{B1-a..d}, p_home_{B1-a..d}`.
- `results/` under the cycle control dir is empty (no metric artifact exists).
- Raw untouched: §2 hash chain (pull record → PREP verification → freeze
  manifest → this recompute, all `f1e8fe78…`).

## 7. Rights — DATA_RIGHTS_OK

One fetch performed 2026-10-04:
`https://raw.githubusercontent.com/nflverse/nflverse-data/main/LICENSE.md` →
Creative Commons Attribution 4.0 International (CC BY 4.0), including the Sui
Generis Database Rights extract/reuse grant (§4) and attribution conditions
(§3). Consistent with `ATTRIBUTION.md` and manifest `license` field. STOP RULE
not triggered.

## Findings (verifier records, never repairs)

- **LOW-1** `nfl_winprob/run_evaluation.py` `append_trial_rows` writes post-GO
  COMPUTED ledger rows with schema string `nba_winprob_trial_ledger@1` (line
  ~407) while the seeded PREREGISTERED rows use `nfl_winprob_trial_ledger@1`
  (NBA adaptation remnant). Post-GO bookkeeping label only; pre-GO accounting
  unaffected (0 COMPUTED today). Fixing it post-freeze would be a code change
  requiring a new code commit + freeze-manifest regen — owner's call, not this
  verifier's.
- **LOW-2** NBA copy remnants in `check_launch_gates`: the explicit drift
  prefix check looks for `nba_winprob/` (dead reference; package is
  `nfl_winprob/`) and one refusal message says "need freeze v2
  post-AMENDMENT_1" (message text only; the actual schema check
  `nfl_winprob_scored_freeze@1` is correct). Compensating control verified:
  the `post_freeze_allowlist` check flags ANY `nfl_winprob/` change as
  outside-allowlist drift, so the drift gate remains effective.
- **LOW-3** `plans/CYCLE_REGISTRY.json` records `head: 9639706f…` for
  NFL-WINPROB-SCORED-V1 (last write 13:33:09Z, before the two cycle commits);
  measured HEAD is `2ddef086…`. Recorded-not-normalized drift; registry is
  outside this verifier's write scope.

## Verdict

**VERIFICATION_PASS** — 7/7 checks PASS, 0 HIGH, 0 CRITICAL, 3 LOW. The
remediated package reproduces from bytes: hashes chain, counts reconcile,
rebuild is deterministic to the frozen features sha, tests and refusals behave
as registered, and no real-outcome metric exists anywhere pre-GO.
