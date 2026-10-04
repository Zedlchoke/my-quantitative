# E2_REPORT — Data / Freeze Verification — NBA-WINPROB-SCORED-V1

- lane: E2_data_freeze (independent re-measurement, no controller artifacts reused)
- date: 2026-10-04
- worktree: /Users/hoangminhlong/my-quantitative/.worktrees/nba-winprob-scored-v1/integration
- branch: orca/nba-winprob-scored-v1-integration · HEAD 670eb76b81c710d31d0d691bb74f96986dae3858 · working tree clean (no uncommitted changes)
- interpreter: /Users/hoangminhlong/my-quantitative/.venv/bin/python (note: /Users/hoangminhlong/.venv/bin/python named in the dispatch does not exist; repo-root venv used)
- writes: this lane directory only; no git mutations; no downloads beyond the two rights re-check fetches

## Verification table

| # | Item | Verdict | Evidence |
|---|------|---------|----------|
| 1a | FREEZE_MANIFEST.json data hashes | PASS | Recomputed sha256 of all 5 data files + attribution; all match manifest exactly: raw/nbaallelo.csv d46ed354…616bc; derived/games.csv e24d9a3b…f098; derived/lineages.csv c8cdd58a…c1c1; derived/participants.csv fd7cb539…1bf (fd7cb5394e09b6d7c649507b1a410143fd1de21127ec56a6d81c0ee01285c1bf); derived/features.csv 644cd740…f799 (644cd740a5006c33fb0cf093244644fb02c6ffea6e680962ec624554ea3cf799); raw/ATTRIBUTION.md e134e20c…490a (e134e20cca04d76a6bb23dbfb3c44b80b0cec0e8679c1945fc7246d824fb490a) — 6/6 match, zero drift |
| 1b | code_freeze_sha in history + nba_winprob/ immutable | PASS | 39b1115632d06b159c5c78a470d2d0bff3cb8386 resolves (type=commit, "NBA-WINPROB-SCORED-V1 implementation (G2)"); `git diff --name-only 39b11156..HEAD -- nba_winprob/` → EMPTY (0 files changed); working tree clean ⇒ nba_winprob/ byte-identical from freeze to HEAD per drift_law |
| 2a | 9 arms == protocol.py ARMS | PASS | Programmatic equality True: [{B0,B0,null,null,[]}, {B1-a,B1,16,0,[]}, {B1-b,B1,16,100,[]}, {B1-c,B1,32,0,[]}, {B1-d,B1,32,100,[]}, {B2-a,B2,null,null,[elo_diff,rest_diff,b2b_home,b2b_away,form_home,form_away]}, {B2-b,B2,null,null,[elo_diff,form_home,form_away]}, {B2-c,B2,null,null,[elo_diff,rest_diff,b2b_home,b2b_away]}, {B2-d,B2,null,null,[elo_diff]}]; len(ARMS)==9 asserted in protocol.py:41 |
| 2b | test_seasons | PASS | Manifest [2009,2010,2011,2012,2013,2014,2015] == protocol.TEST_SEASONS; train_seasons_range [1947,2008] == protocol (1947, 2008) |
| 2c | go_phrase + state | PASS | Manifest go_phrase == "GO NBA WINPROB SCORED V1 EVALUATION" == protocol.SUCCESSOR_GO_PHRASE (exact); go_phrase_state == "REGISTERED_NOT_CONSUMED" |
| 2d | protocol_digest | PASS | sha256(lanes/C_protocol/PROTOCOL_EVAL.md) = c058760d6e77863fd7f5912ccfebad64755a26c1dd76e8946496f244f9a451f7 == manifest protocol_digest; on-disk file identical to HEAD blob (`git show HEAD:…` rehash equal; `git diff HEAD -- <path>` empty). Note: path is repo-root-relative (worktree_root/lanes/C_protocol/), not under research/control/ — consistent with plan sec1 wording |
| 2e | constants (bonus) | PASS | Manifest constants {logit_l2:1.0, rng_seed:20261004, elo_init:1500.0, elo_gamma:0.75} == protocol.LOGIT_L2/RNG_SEED/ELO_INIT/ELO_GAMMA |
| 3 | Identity recount (games.csv, own python) | PASS | 63,157 data rows (==63,157); seasons 1947..2015 (min/max exact); last date 2015-06-16 (max over date column); distinct home_lineage∪away_lineage = 53 (==53) |
| 4a | features.csv leakage surface | PASS | Header (22 cols): src_game_id,gameorder,date,season,is_playoffs,home_lineage,away_lineage,rest_diff,b2b_home,b2b_away,form_home,form_away,rest_home,rest_away,elo_diff_B1-a,p_home_B1-a,elo_diff_B1-b,p_home_B1-b,elo_diff_B1-c,p_home_B1-c,elo_diff_B1-d,p_home_B1-d. NO home_win / pts / margin / forecast / elo_i / opp_elo / win_equiv (outcome columns home_pts/away_pts/home_win/margin_home/total_pts exist only in games.csv, not features.csv). Only keys + rest/form/b2b + elo_diff_*/p_home_B1-* |
| 4b | Test suite | PASS | `pytest nba_winprob/tests -q` (cwd=worktree, repo venv) → **29 passed**, 18 warnings (datetime.utcnow deprecation only), 90.59s |
| 4c | Refusal gates | PASS (see note D1) | `python -m nba_winprob.evaluate` (no args) → "REFUSED: no --freeze-manifest … explicitly NOT a typed GO … NOT_RUN", exit **3**. `python -m nba_winprob.run_evaluation` with `--out` inside this lane dir and no manifest/go-record → "REFUSED — launch gates failed: freeze manifest unreadable…", exit **3**, zero bytes written. No-args invocation exits 2 (argparse: `--out` required) — see D1 |
| 5 | Rights re-check | DATA_RIGHTS_OK | (a) github.com/fivethirtyeight/data root README still states: "Unless otherwise noted, our data sets are available under the Creative Commons Attribution 4.0 International License" (code MIT); repo license badge CC-BY-4.0. (b) nba-elo/README.md still states: "Game information is from Basketball-Reference.com" (and team_id "from Basketball Reference"). Both sentences present and unchanged ⇒ CC BY 4.0 basis + BRef provenance intact; no BLOCKED_DATA_RIGHTS trigger |
| 6 | Plan reconciliation | PASS | /Users/hoangminhlong/my-quantitative/plans/PLAN_nba_winprob_scored_v1.md sec2 "Reconciliation of inoperative assumptions (documentation only)" records the superseded "data ends 2022-23" drafting assumption (byte audit: data ends 2015-06-16), §3/§10.2 placeholder seasons → 2009..2015, §7 NOT_RUN row re-read, and §8.4/§8.7 2019-20/2020-21 bubble-era segments → N/A with no semantic substitution. Sec3 "Data authority" records owner CONDITIONAL acceptance (internal research only, attribution/provenance mandatory) and the STOP RULE: rights re-check failure ⇒ BLOCKED_DATA_RIGHTS, halt, report to owner |

## Bonus consistency checks (not required, supporting)

- TRIAL_LEDGER.jsonl: exactly 9 rows, all status PREREGISTERED (B0, B1-a..d, B2-a..d), 0 observed — consistent with G3 and go_phrase_state REGISTERED_NOT_CONSUMED.
- Manifest predecessor_tip b5b5084753d213dfd793488d3c009cf4380e0323 matches the plan's stated integration base.
- games.csv itself contains outcome columns (home_pts/away_pts/home_win/margin_home) as expected for the raw identity table; the scored feature surface (features.csv) excludes them (item 4a).

## Defects / observations

- D1 (minor, informational — no action required for G1): the dispatch expected `python -m nba_winprob.run_evaluation` with no args to exit 3; it actually exits 2 because argparse enforces required `--out` before the launch gates run (run_evaluation.py:322,338-343). The refusal property itself is intact and stronger than the literal check: there is no argument vector that reaches evaluation without passing `check_launch_gates`, and the gate path (with `--out` supplied) returns exit 3 with zero writes. `nba_winprob.evaluate` no-args exits 3 exactly as specified. Optional hardening (post-GO, out of E2 scope): reorder so missing --out still routes through the refusal path.
- D2 (environment note): /Users/hoangminhlong/.venv/bin/python from the dispatch packet does not exist; the repo venv at /Users/hoangminhlong/my-quantitative/.venv/bin/python was used throughout.

## Final verdict

**E2_PASS** — freeze manifest hashes 6/6, code freeze immutability, manifest internals (arms/seasons/go_phrase/protocol_digest/constants), data identity census, leakage surface, refusal gates, rights re-check (DATA_RIGHTS_OK), and plan reconciliation all verified against independent re-measurement. No BLOCKED_DATA_RIGHTS trigger. G1 data/freeze gate evidence is green from lane E2's side; scored execution remains NOT_RUN pending A7 + owner GO at this cycle's own gate.
