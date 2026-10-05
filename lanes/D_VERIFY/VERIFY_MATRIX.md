# VERIFY MATRIX — Lane D_VERIFY · WINPROB-PLAYERFEAT-PREP-V1 · 2026-10-05

Claim (source) → D_VERIFY measurement (own code) → verdict.
Machine evidence: `*_output.json` in this directory.

## A. NBA — lane A_NBA_FEAT

| # | lane claim | D_VERIFY measurement (own code) | verdict |
|---|---|---|---|
| A1 | 8 new season CSVs + 3 predecessor + 11 schedules + parquet + csv.gz sha256 pins (FEATURE_TABLE_MANIFEST.json) | 40/40 sha256 match (`hash_output.json`) | MATCH |
| A2 | schedule 14,254 rows; played 14,187 | 14,254 / 14,187 (`nba_join_output.json`) | MATCH |
| A3 | played-join 1.0000 in 8 seasons; 0.9992 in 2017/2018/2019 | 1.0000 ×8; 0.999237/0.999239/0.999239 | MATCH |
| A4 | 3 box-less FINAL games 400900132/400975285/401070917 | all 3 STATUS_FINAL + scores, 0 box rows, exact ids | MATCH |
| A5 | 0 orphan box games; 0 dup (game_id,athlete_id) | 0 / 0 | MATCH |
| A6 | tip semantics: game_date_time==start_date UTC 14,254/14,254 | 0 mismatches / 14,254 | MATCH |
| A7 | feature table 28,374 rows, 18 cols, per-season counts | 28,374 rows; per-season 2×played all 11 seasons | MATCH |
| A8 | independent recompute <1e-12 on all scalars | OWN rebuild of all 28,374 rows: 0 int-col mismatches; max scalar diff 6.66e-16 (`nba_recompute_output.json`) | MATCH |
| A9 | ≥6 sampled rows incl. neutral + trade guard | 9 rows sampled (401704641 neutral tg=0; 6 random 2016–2026; Mills targets 401705570 LAC+UTA) — all exact | MATCH |
| A10 | Patty Mills 2025 stale-DNP case (401705243) | found in bytes: UTA DNP scaffold 2025-01-30 after last UTA appearance 2025-01-28; 36 LAC rows | MATCH |
| A11 | trade guard load-bearing ("no absence fabricated") | counterfactual guard-off: 4 rows would flip c_abs_out 0→1 in 2025; guard-on == lane 2,648/2,648 (`nba_guard_counterfactual_output.json`) | MATCH |
| A12 | 1,688 neutral rows; scalars zero iff neutral | 1,688; invariant 0 violations both directions | MATCH |
| A13 | ZERO outcome columns | 0 banned names in 18-col schema; numeric ranges sane (max `a_top5_share` 0.837, `c_abs_streak` ≤10); no score-like column | MATCH |
| A14 | absence paths exercised (c_abs_out rate 0.1077, streak tail 10) | 2,875 rows c_abs_out=1; 550 rows streak>0 (max 10) — all matched | MATCH |

## B. WNBA — lane B_WNBA_FEAT

| # | lane claim | D_VERIFY measurement (own code) | verdict |
|---|---|---|---|
| B1 | 8/8 corpus re-hash + parquet sha `ceaf10ba…f7bf` 826,415 B | 8/8 sha+bytes (`wnba_hash_fix.json`); parquet match | MATCH |
| B2 | universe 5,988 games, 25 per-season counts exact | 5,988; all 25 counts identical (`wnba_output.json`) | MATCH |
| B3 | join rates 2002 5.9% pb / 99.6% gr | 16/271 = 5.90% / 270/271 = 99.63% | MATCH |
| B4 | join rates 2003 76.1%, 2004 90.3%, 2013 100%, 2026 100% | 194/255 = 76.08%; 214/237 = 90.30%; 221/221; 341/341 | MATCH |
| B5 | 2002 minutes 100% null (legacy `--`) | 344/344 rows `"--"` in legacy `min` col | MATCH |
| B6 | CON 2013 worked example b5=1002.0 b3=601.0, priors 200/201/200/199/202 | own-code reproduction identical, same 5 game_ids, strict tips | MATCH |
| B7 | CON 2014 continuity c=0.405477=2769/6829, roster 12, game-2 400539470 v2 | own lineage impl: 2769/6829 = 0.4054766, roster 12, g2 strictly after g1 | MATCH |
| B8 | expansion neutral: GSV25 46 rows, TOR26 44, POR_PDX26 44; 2002 542 `no_prior_in_corpus` | 46/46, 44/44, 44/44 all `expansion_no_prior`; 542/542 | MATCH |
| B9 | IND 2013 absence 0.644 (target 400496780, recent 400445897) | own code: 0.64408, same top5 set {803,125,1003,851,860} | MATCH |
| B10 | strict tip inequality 0 violations / 11,976 rows | own scan: 0 violations (b3/b5/c_recent) | MATCH |
| B11 | deterministic rebuild identical sha | re-ran lane's script (temp copy, redirected OUT_DIR): identical sha+bytes, rc 0 (`wnba_rebuild_output.json`) | MATCH |
| B12 | ZERO outcome columns; 0 dups (game_id, team_side) | 0 banned names in 40-col whitelist; 0 dups | MATCH |
| B13 | computed counts: continuity 5,907; B(k=3) 5,778; B(k=5) 5,778; C 5,778 | 5,907 ✓; **b3 = 6,124**; b5 5,778 ✓; c 5,778 ✓ | MINOR-1 (b3 doc) |
| B14 | neutral reason counts continuity: 5,168/542/202/157 | identical 5,168/542/202/157 | MATCH |

## C. NFL — lane C_NFL_CROSSWALK

| # | lane claim | D_VERIFY measurement (own code) | verdict |
|---|---|---|---|
| C1 | players.parquet sha 485b1980…, 3,389,574 B; timestamp.json sha 23955f4e… | both match; predecessor 5 files match pins | MATCH |
| C2 | schema 24,844×39; gsis 0-null unique; pfr non-null 22,679 | identical | MATCH |
| C3 | weekly GSIS join 1.0 / 1.0 / 1.0 (2,001/2,024/1,512), 0 dups | identical (`nfl_output.json`) | MATCH |
| C4 | snap PFR join 0.997259 (6 ids/54 rows) / 0.998213 (3 ids/8 rows) | 0.9972590 (same 6 ids) / 0.9982132 (same 3 ids) | MATCH |
| C5 | round-trip 1,475/1,512 = 0.975529 (pfr-holders 0.978117); 4 named pfr-null | 0.9755291 / 0.9781167; same 4 names | MATCH |
| C6 | 32/32 teams; ACT∧2026 = 1,731 (52–55/team) | 32; 1,731; 52–55 | MATCH |
| C7 | ≥3 named spot checks incl. pfr-null | 4 checks: Cody White, Alec Anderson, Basil Okoye, Peter Woods — all pfr_id NULL, ACT, last_season 2026; top-8 QBs both ids + in snap26 | MATCH |

## D. Adjudication + boundaries

| # | item | D_VERIFY measurement | verdict |
|---|---|---|---|
| D1 | Lane C LIFT recommendation | crosswalk joins verified independently (C3–C5) | **CONFIRM LIFT** |
| D2 | residual blockers named | NOT_RUN_PIT target-game status + ≤1-week snap lag + release-cadence carried verbatim in lanes' docs | CONFIRMED CARRIED |
| D3 | NOT_RUN_PIT law respected by A/B | no target-game status inputs in either builder (full-table recompute + 0 strict-inequality violations); `active`/`reason` absent from WNBA schema | RESPECTED |
| D4 | 0 scored computation in lanes/ | grep `log_loss|brier|win_prob(|calibrat|sklearn|predict_proba|accuracy_score|roc_auc` on .py: 0 computation hits (2 design-mention lines only) | PASS |
| D5 | write-scope audit | `git status --porcelain`: only `?? lanes/D_VERIFY/` + `?? lanes/DISPATCH/DISPATCH_D_VERIFY.md`; HEAD = 8ad8785b (dispatch sha); branch correct | PASS |
| D6 | ≤3 URL re-fetches, $0, no keys | 0 fetches by D_VERIFY; no keys; $0 | PASS |
