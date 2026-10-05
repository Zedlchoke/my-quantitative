# VERDICT TABLE — Lane B_WNBA_FEAT · WINPROB-PLAYERFEAT-PREP-V1 · 2026-10-05

Negative-first. PASS requires evidence measured from bytes this session; missing evidence =
NOT_RUN, never inferred PASS. No scored computation occurred in this lane (0 scored;
calibration/forecasting vocabulary only).

| # | check | verdict | evidence |
|---|---|---|---|
| 1 | Corpus spot re-hash ≥6 files vs `download_manifest_r2.json` (incl. player_box + game_rosters, 2002-era + 2026) | **PASS** | 8/8 sha256 + byte-size match (pb 2002/2013/2020/2026, gr 2002/2013/2019/2026); manifest `inputs.spot_rehash.all_match=true` |
| 2 | Game universe re-derivation = predecessor's 5,988 (ESPN-side law) | **PASS** | 5,988 total; per-season list identical row-by-row (271…341); `espn_universe.cross_check_predecessor.match=true` |
| 3 | Per-season coverage audit 2002–2026 (player_box + game_rosters join rates) | **PASS** | pb 5.9% (2002) → 76.1% (2003) → ≥90.3% (2004+) → 100% (2013+); gr ≥99.2% all seasons; full table COVERAGE_AUDIT §3 |
| 4 | Group A continuity (W-H2 linkage, v2 as-of law, lineage joins, expansion law) | **PASS** | 5,907 computed rows (2014–2026); neutral+reason otherwise; v2 enforced (game-1 rows always neutral, flag only on game-1 rows); c ∈ [0.124, 0.974] |
| 5 | Group B minutes-mass/load k ∈ {3,5} both computed, selection deferred | **PASS** | both `b3_*` and `b5_*` columns emitted; 5,778 computed rows each (2013+, full windows); no selector present |
| 6 | Group C top-player form + absence proxy (null-minutes uniform; `active`/`reason` never used) | **PASS** | 5,778 computed rows; top-5 from trailing-10 (≥5 gate); absence ∈ [0, 0.839]; `active`/`reason` absent from schema |
| 7 | Strict tip-time inequality everywhere (as-of law `tip_utc_strict_lt_v1`) | **PASS** | per-row assertions: 0 violations across `b3/b5/c` window metadata on 11,976 rows |
| 8 | One row per (game_id, team side) for every universe game; row exists when neutral | **PASS** | 11,976 = 2 × 5,988; per-season counts asserted |
| 9 | NO outcome columns anywhere | **PASS** | exact column whitelist (40 cols) asserted; banned-name scan (score/winner/outcome/result/margin) = 0 hits |
| 10 | Determinism (no run timestamps in table; reproducible bytes) | **PASS** | two independent full builds → identical parquet sha256 `ceaf10ba33e705b9569a11cec2aa33e1875e372c35d643ed5d80d5e757ffc7bf` (826,415 B) |
| 11 | Leak guard: reproduce predecessor CON 2013 worked example from bytes | **PASS** | target 400445816 tip 2013-07-06T23:00Z; prior-5 = 200/201/200/199/202 min (games 400445826/…854/…709/…771/…798); b5 total 1002.0, b3 601.0 — asserted in selftest |
| 12 | Lineage coverage (20-key table only; never raw abbreviations) | **PASS** | 0 unmapped universe teams; 0 team_id→multi-franchise violations; DAL tree (DET 2002–09 + TUL 2010–15 = `team_id` 3) and LVA tree (UTA id 15; SAN/LVA id 17) asserted |
| 13 | Neutral-flag behavior (expansion both arms, 2002, pre-2013 floors, game-1 v2) | **PASS** | all neutral checks in selftest PASS (counts: expansion 202, no_prior_in_corpus 542, floor 5168, game1_v2 157) |
| 14 | Opening-roster v1 | **NOT_RUN_PIT** (by law, restated) | no pre-tip publish timestamps on the game-1 sheet; v2 is the only built variant (FEATURE_SPEC §2) |
| 15 | Target-game roster/starter/DNP/active/reason as features | **NOT_RUN_PIT / FORBIDDEN** (restated) | never read; absent from schema |
| 16 | Injury/availability feed | **NOT_RUN_PIT** (restated) | no dated archive exists in any rights-cleared corpus |
| 17 | 1997–2001 era | **NOT_RUN (out of scope)** | no player-level data exists in the corpus; packet law |
| 18 | Scored computation / win-prob / calibration metric | **NOT_RUN (out of authority)** | 0 scored; feature construction only |
| 19 | Compute budget ≤30 min | **PASS** | full build + selftest ≈ 4.1–4.9 min wall clock |
| 20 | Writes confined to lane dir + `~/.my-quantitative-data/playerfeat-prep-v1/wnba/` | **PASS** | outputs: parquet + this lane's docs only; corpus untouched (hashes unchanged before/after) |

**Lane verdict: PREP_WORK_COMPLETE (feature-prep only; registers no GO, consumes no GO).**
Blocking conditions encountered: none (no hash mismatch, no leakage suspicion, no budget
exceedance). Residual laws carried to successors: k-selection deferred (Group B), v1
restated NOT_RUN_PIT, minutes-weighted consumption eligible 2013+ (Group B/C) / season 2014+
(continuity), `active`/`reason` unusable.
