# VERIFY_MATRIX — D_VERIFY · NFL-PLAYERFEAT-PREP-V1 · 2026-10-05

Every row measured by this lane's own code (`work/*.py`), builder reused only for the
determinism re-execution. Claim source: FEATURE_TABLE_MANIFEST.md+json, COVERAGE_AUDIT.md,
PIT_AUDIT.md, VERDICT_TABLE.md, handoff_B_BUILD.json.

| # | claim / check | verifier method | claimed | measured | verdict |
|---|---|---|---|---|---|
| 1 | stats_player_week_2024 sha | own re-hash (`t1_hash.py`) | `847569d1…55c1` | identical | MATCH |
| 2 | stats_player_week_2025 sha | 〃 | `2a461bec…ff10` | identical | MATCH |
| 3 | stats_player_week_2026 sha | 〃 | `49bc644e…6179` | identical | MATCH |
| 4 | snap_counts_2025 sha | 〃 | `47220218…ce20` | identical | MATCH |
| 5 | snap_counts_2026 sha | 〃 | `fae0627d…8273` | identical | MATCH |
| 6 | players.parquet sha | 〃 | `485b1980…85e2` | identical | MATCH |
| 7 | output parquet sha / 1,266×44 | 〃 + schema read | `f1bc6b4a…7c4f57`, 1,266×44 | identical, 1,266×44 | MATCH |
| 8 | GSIS join 2024/25/26 = 1.0 | own join (`t2_join.py`) | 2001, 2024, 1512 players, rate 1.0 | same | MATCH |
| 9 | PFR join 2025 = 0.997259 | 〃 | 2183/2189, 6 unresolved ids | same ids+rate | MATCH |
| 10 | PFR join 2026 = 0.998213 | 〃 | 1676/1679, 3 ids | same ids+rate | MATCH |
| 11 | placeholder rows excluded = 48 | own count | 48 (22+22+4) | 22/22/4 | MATCH |
| 12 | row universe 633 games / 1,266 rows | own recount | 633 / 1,266 | same; 0 orphans; 0 dup (gid,side) | MATCH |
| 13 | games.csv 2024–26 = 842 (285/285/272) | own recount | 842 | same | MATCH |
| 14 | 209 future 2026 games, no rows | own recount | 209 | same | MATCH |
| 15 | earliest future kickoff 2026-10-06T00:15:00Z | own tz derivation | same | same | MATCH |
| 16 | kickoff strict-inequality as-of, full table | own full recount (kickoff_utc, n_prior, rest_days, g3_n, pfr-null flag, all 1,266 rows) | 0 mismatches | 0 mismatches on every counter; rest dev 0.0 | MATCH |
| 17 | KC worked example 2024_11_KC_BUF: prior-3 = 819/6/1/124, n_prior 9, rest 7.1424 | own recompute from bytes (`t3b`) | per PIT_AUDIT §2 | 819.0/6.0/1.0/124.0, 9, 7.14236 | MATCH |
| 18 | KC derived: ypa 6.60484, epa 30.55991, epa_pa 0.24645, std 245.33333/3.33435, form +27.66667/+6.85229, k5 1304/190 | 〃 | per PIT_AUDIT §2 | all equal | MATCH |
| 19 | KC G2: U_tot 189, Hunt 74/Kelce 40/Hopkins 17, top3 0.69312, hhi 0.22208, usage_pg 63.0, top5_k5 0.79299 | own recompute (`t3c`) | per PIT_AUDIT §2 | all equal | MATCH |
| 20 | bye-week fixture 2024_07_KC_SF: wks 5/4/3, yds_k3 793, rest 12.8403, n_prior 5 | own deep recompute, 44-col compare | per S5 | identical, 0 diffs | MATCH |
| 21 | neutral opener row (96-row cohort) | deep recompute 2026_01_ARI_LAC + count | 96 no-prior rows; G1/G2/rest NaN | identical; 96; all NaN; n_prior 0 | MATCH |
| 22 | pfr-null exclusion row (82-row cohort) | deep recompute 2026_02_LV_LAC + per-row flag recount | 82 flagged; canary WhitCo05/Cody White | identical; 82; canary facts exact (pfr NULL, 3 rows LV wks1–3, LV wk2–4 flagged) | MATCH |
| 23 | n_w=1 G3 absent share = 0.0 by construction | full-table scan | documented exception | all 64 n_w=1 rows = 0.0 | MATCH |
| 24 | flag counts 96 / 634 / 82 / 0 / 192 / 350 | own recount | same | same | MATCH |
| 25 | per-season coverage table | own recount | 2024: 570/32/570/0/64/128, 538, 0; 2025: 570/32/32/74/64/128, 538, 538; 2026: 126/32/32/8/64/94, 94, 94 | identical | MATCH |
| 26 | 0 outcome columns (schema + content) | whitelist compare + banned-token scan + dtype/content scan | 0 | 0; exact 44-col whitelist; no stray object cols | MATCH |
| 27 | NaN-never-0 neutral rules | forward+converse NaN checks | spec §7 | 96 rows all NaN; 634 rows G3 NaN; converse holds | MATCH |
| 28 | trunc flag semantics k3 {1,2}, k5 {1..4} | own recount | spec §7 | holds | MATCH |
| 29 | sort law (kickoff_utc, game_id, side); asof version constant | own check | spec §9 | holds; constant | MATCH |
| 30 | determinism: rebuild byte-identical | fresh-process `build_features.py --outdir /tmp/dverify_rebuild_pfr` | sha `f1bc6b4a…7c4f57` | identical sha | MATCH |
| 31 | first-computable dates (4) | own recount from table | 2024-09-13 / 2024-10-11 / 2025-09-12 / 2025-09-26 Z | identical | MATCH |
| 32 | value-range sanity (COVERAGE_AUDIT §5), 8 columns | own min/max | per doc | 7 of 8 exact; `g3_top5_newly_absent_count` doc max 5 vs measured 2 | **MINOR-1** |
| 33 | PIT_AUDIT §2 wording "BUF at KC" | game_id convention + games.csv away/home | n/a | 2024_11_KC_BUF is KC **away** at BUF; prose direction wrong, numbers correct (team==KC row) | **MINOR-2** |
| 34 | 0 scored computation in lanes/ | grep over lanes/ | 0 | 0 (only ban-list/boundary text) | MATCH |
| 35 | isolation: NFL-WINPROB-NG-SCORED-V1 clean+untouched | read-only `git status --porcelain` | clean | clean (empty output) | MATCH |
| 36 | write scope of B_BUILD | porcelain of own worktree | lanes/B_BUILD + data dir only | only dispatch packet + lanes untracked; no out-of-scope writes | MATCH |
| 37 | shipped manifest/selftest == lane copies | shasum | identical | identical (973173f5…, 2446d573…) | MATCH |
| 38 | NOT_RUN_PIT law (no target-game status) | schema + content provenance (T4 #26, T3 recompute) | no such column/value | confirmed absent | MATCH |
