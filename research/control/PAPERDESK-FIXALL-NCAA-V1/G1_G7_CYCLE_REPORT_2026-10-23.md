# PaperDesk AI data G1–G7 — cycle report, stopped at A7/G3

Date: 2026-10-23. Owner addendum at 09:15 ICT supersedes the Task 0 mirror heuristic, accepts the 846 frozen replay, and opens bounded Task 0B. This report describes the integration worktree; it does **not** claim production adoption or final acceptance.

## Task 0 and Task 0B

The original Task 0 report and predictor probe are preserved as historical records. Under the owner's correction, the live ESPN predictor and “mirror” count are not a frozen swap test. Replay 846 is bit exact at HOME 0.6433001912350018, with Washington home and Toronto away. `TASK0B_REPLAY_2026-10-23.md` records manifest-verified frozen payload SHA `fc28f4c479ab1b9e81fd3cebce7b6a37c83853a3023769f8cc81747b757ce2d7` and exact replay of 845 HOME 0.5974957068827914 (Orlando id 19 home, Minnesota id 16 away) and 847 HOME 0.5516501258554483 (Miami id 14 home, Detroit id 8 away). Equal-rating HCA alone yields HOME 0.6400649998028851. Task 0B **PASS** under the owner gate; the home/away assignment suspicion for the shared slate code path is closed. No engine, HCA, or prior was changed.

## Implemented in the integration worktree

| Task | Change and regression check | Present status |
|---|---|---|
| G1 | `ai_producer.py` takes `pm_event_id` only from the exact candidate MARKET_QUOTE and builds the pinned Gamma URL; absence keeps an honest skip. New pending markers carry `quote_row_sha256` from `execute.py`; equal-odds ambiguity in older markers fails closed. `test_ai_data_g1_g5.py`. | Code/test PASS; post-change production package NOT_RUN. |
| G3 | `ai_research.py` stamps every packet with its own `collector_sha256`; test compares with file bytes. | **FAIL**: production PID 8972 imports root collector SHA `3608dff8d64e4b2a38e639a5a3d489e1f6350f1d2bec7792bb5e7f5a5511d437`, whereas the edited worktree collector has a different SHA. Two runnable copies remain. Root is owner/bootstrap space and was not overwritten. |
| G5 | Injury time normalization uses one terminal Z and seconds; adds `age_days` and `stale` (>21 days) without dropping old items. Tests cover timestamp shapes and stale item. | Code/test PASS; first post-change production package NOT_RUN. |
| G6 | Producer passes ledger quote and adds `market_block` and `team_block` to the AI candidate payload. NBA collector copies PM HOME/AWAY numbers and captures ESPN summary, standings, team schedules with raw response URLs/times. Results are restricted to final games before collection and kickoff. `test_ai_data_g6.py` checks synthetic field provenance and time restriction. | Code/test PASS; production acceptance NOT_RUN. NBA live smoke below is not a slate run. ESPN structured fields for other leagues are explicitly journaled unavailable. |
| G2 | Generic SOCCER path replaced with competition map for the five keys in `config.json`; unknown competition emits `no verified ESPN path for competition <X>` with 0 ESPN sources. `test_ai_data_g2_g4.py`. | Code/test PASS; live slug checks were made during implementation but not preserved as a standalone raw probe artifact for A7, so G2 evidence gate remains NOT_RUN. |
| G4 | Failed board cache entries expire after 120 monotonic seconds; successful results persist. Retry/failure are journaled. `test_ai_data_g2_g4.py`. | Code/test PASS; production acceptance NOT_RUN. |
| G7-i | `ai_research.py` fetches the latest linked official NBA injury PDF issued before collection, validates host/signature/size, extracts the two-team section through native macOS PDFKit helper `nba_injury_pdf.js`, hashes and journals the raw PDF. `test_ai_data_g7.py`. | Code/test PASS; live smoke succeeded, but post-change production acceptance NOT_RUN. |

`ops_service.py` now supplies actual ledger MARKET_QUOTE history to the producer. Existing battery fixtures in `test_exec_battery.py` were updated to the current 23–24 October NBA window; the older 20–21 October fixtures had become final and caused time-dependent test failures. `test_upgrade_u5.py` now expects the explicit SOCCER competition route. No AI prompt, EV, stake, anchor, engine, or model law changed.

## Live probes and their limits

During implementation, ESPN site news and board endpoints returned HTTP 200 and a real event for the five configured competitions: Nations League `soccer/uefa.nations` (event 401861093), World Cup group `soccer/fifa.world` (760415), Euro group `soccer/uefa.euro` (690573), World Cup qualifiers `soccer/fifa.worldq.uefa` (724835), Euro qualifiers `soccer/uefa.euroq` (655247). The checks were not saved as raw payloads/status records in the control folder, so A7 correctly labels their independent verification NOT_RUN.

The ESPN NBA summary probe used `https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event=401909846`: actual fields found were `predictor.homeTeam/awayTeam.gameProjection`, `pickcenter[0].spread`, `overUnder`, `homeTeamOdds.moneyLine`, and `awayTeamOdds.moneyLine`. Standings and schedule were fetched from ESPN site endpoints in the two smoke packets below. These ESPN fields are live values, not frozen at forecast; absence or ID mismatch is journaled and omitted.

Read-only smoke from the **integration code**, outside the production cadence, produced:

| Candidate | Smoke evidence file | news_48h | injuries | gamma_event | league_official | official_injury_report |
|---|---|---:|---:|---:|---:|---:|
| 401909846 | `/Users/hoangminhlong/.my-quantitative-data/sports-papertrade-exec-v1/research_g6g7_smoke_20261023/evidence_401909846_20261023T023031Z.json` | 1 | 5 | 1 | 0 | 2 |
| 401909843 | `/Users/hoangminhlong/.my-quantitative-data/sports-papertrade-exec-v1/research_g6g7_smoke_20261023/evidence_401909843_20261023T023047Z.json` | 1 | 6 | 1 | 0 | 2 |

The smoke captured two PM legs, ESPN predictor and pickcenter, both team standings/schedules, and official PDF sections. The raw PDF is retained beside the smoke files. For 843, ESPN schedule available during the smoke gave both teams a prior final on October 21 ET and `rest_days=1`, `back_to_back=false`; the prompt's suggested October 22 B2B example was not assumed true. These files are diagnostic probes and cannot satisfy the required **first real post-fix slate** plus V3 research journal. A7 did not verify the smoke independently.

## G7-ii diagnosis, no rule change

`window_eligible` opens the candidate window 24 hours before anchor, and `cadence_pass` runs forecast/quote/decide once eligible. For the October 23 NBA slate, anchor was `2026-10-23T13:50Z`; forecast was recorded `2026-10-22T13:50:12Z`, pending AI at `14:05:20Z`, opinion at `14:10:33Z`, and VETO consumption beginning `14:21:38Z` through about `14:37Z`. Thus the D-1 lookahead and runner cadence explain the early research; the observed logs do not establish a manual owner decision. Proposed owner choice: retain D-1 and add a fresh review at anchor for previously ALLOW candidates, with a new VETO prevailing; or move decide to anchor. Neither was implemented.

## Verification and stop

- Prompt freeze-law SHA before and after: `c2c4fd464f0413a054d94cb2f555f1e9325ed3b78111142b551026f3e2a0c890`. The file's raw SHA is a different quantity because the registered digest is computed with its own value blanked. No prompt diff.
- Targeted G tests: 7 passed. Full `tests/papertrade_exec` battery, two consecutive runs after the last code edit: **323 passed / exit 0** (59.61 s; 54.88 s). `git diff --check`: exit 0. These are integration-worktree tests, not production proof.
- Independent A7 report: `a7/A7_AI_DATA_G1_G7_VERDICT_2026-10-23.md`, verdict **FAIL G3 / NOT READY FOR ACCEPTANCE**. It also marks post-change real slate, V3 journal, full source counts, and independently preserved G2 slug proof NOT_RUN. The A7 read is of the dirty integration tree and does not authorize deployment.
- Required production evidence and journal for the first slate after adoption: **NOT_RUN**. No final acceptance claim. Root production collector remains old, and its running process has not been changed or restarted.

The stop point is binding. Further action requires the authorized root adoption/integration workflow, production process version verification, first real slate capture, and fresh A7 review of the exact adopted tree. This report requests no GO for engine or trading changes.

## Changed paths prepared in the worktree

`research/papertrade_exec/ai_producer.py`, `ai_research.py`, `execute.py`, `ops_service.py`, new `nba_injury_pdf.js`; `tests/papertrade_exec/test_exec_battery.py`, `test_upgrade_u5.py`, new `test_ai_data_g1_g5.py`, `test_ai_data_g2_g4.py`, `test_ai_data_g6.py`, `test_ai_data_g7.py`; this report and Task 0/0B records. The owner addendum file is pre-existing owner input and is not claimed as an agent edit.
