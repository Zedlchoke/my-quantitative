# VERIFICATION REPORT — Lane D_VERIFY · WINPROB-PLAYERFEAT-PREP-V1 · 2026-10-05

Independent verifier. All numbers below were re-measured from bytes with D_VERIFY's OWN
code (`scripts/v1..v6_*.py`); lane scripts were read only as claims. 0 URL re-fetches,
$0, no keys, no git writes, no repairs. Interpreter
`/Users/hoangminhlong/my-quantitative/.venv/bin/python` only.

## Overall verdict: **VERIFIED_WITH_MINOR**

- 0 BLOCKER · 0 MAJOR · 1 MINOR · 2 INFO (see DISCREPANCY_REGISTER.md)
- Adjudication (Task 4, owner-mandated): **CONFIRM** lane C's LIFT recommendation of the
  predecessor NFL HOLD — with residual blockers carried by name (see §4).

## 1. NBA (lane A_NBA_FEAT) — verdict PASS

| check | my measurement | lane claim | verdict |
|---|---|---|---|
| Re-hash | 40/40 sha256 match: all 22 manifest inputs (8 new-season CSVs + 3 predecessor box + 11 schedules) + parquet + csv.gz | all pinned | MATCH |
| Re-join (own code, 11 seasons incl. 2017/2018/2019) | 14,254 schedule rows; 14,187 played; join 1.0000 in 8 seasons, 0.999237/0.999239/0.999239 in 2017/2018/2019; 0 orphan box games; 0 dup (game_id, athlete_id); tip==start UTC on 14,254/14,254 | 1.0000 ×8, 0.9992 ×3, 0 dups, 0 orphans | MATCH |
| 3 box-less FINAL games | 400900132 (2017, 142–139), 400975285 (2018, 108–105), 401070917 (2019, 131–117) all STATUS_FINAL + scores, 0 box rows | same 3 game_ids | MATCH |
| Independent feature recompute | OWN implementation of FEATURE_SPEC as-of law (strict `<` tip inequality) rebuilt all **28,374** rows: 0 key diffs, **0 mismatches on all 10 integer columns across all rows**, max abs scalar diff **6.66e-16** (`a_top5_share_k5` 0.0, `a_load_top5_k5` 6.7e-16, `b_form_top3` 0.0) | <1e-12 tolerance | MATCH (≤6.7e-16) |
| Sampled rows (9, incl. required cases) | neutral early-season (401704641/25, tg=0); 2016/2017/2019/2021/2023/2026 random; Patty Mills trade-guard targets 401705570 (LAC id 12 + UTA id 26) — all exact | ≥6 rows | MATCH |
| Trade guard bytes | Mills 2025: 82 box rows, 36 LAC, last usable UTA appearance 2025-01-28, stale UTAH DNP scaffold row **401705243** (2025-01-30) found in bytes; counterfactual (guard off, own code): **4** 2025 rows would flip `c_abs_out` 0→1; guard-on matches lane table 2,648/2,648 | guard load-bearing, no absence fabricated | MATCH |
| Absence paths exercised | `c_abs_out=1` on 2,875 rows; `c_abs_streak>0` on 550 rows (tail to 10) — all matched by my recompute | 0.1077 rate / streak tail 10 | MATCH |
| Neutral rule | 1,688 neutral rows; zero-iff-neutral invariant 0 violations in BOTH directions (my scan) | 1,688 / asserted | MATCH |
| Outcome-column scan | 18-column whitelist schema: 0 score/winner/margin/outcome-like names; numeric ranges sane (`a_*`∈[0,0.84], `b_form`∈[−0.246,0.240], `c_abs_streak`≤10); no score-like content column | ZERO outcome columns | MATCH |
| Per-season rows / dups | 2 × played per season, all 11 seasons; 0 dup (game_id, team_id) | 28,374 total | MATCH |

## 2. WNBA (lane B_WNBA_FEAT) — verdict PASS with 1 MINOR doc discrepancy

| check | my measurement | lane claim | verdict |
|---|---|---|---|
| Re-hash | 8/8 corpus files (pb 2002/2013/2020/2026 + gr 2002/2013/2019/2026) sha256 + bytes match `download_manifest_r2.json`; output parquet sha `ceaf10ba…f7bf` 826,415 B matches | 8/8 + parquet pin | MATCH |
| Universe law (own code) | 5,988 games; all 25 per-season counts identical (271,255,237,238,257,242,259,242,220,224,223,221,222,225,220,219,220,220,147,210,240,261,263,311,341) | 5,988 exact | MATCH |
| Join rates (own code) | pb: 2002 16/271=5.9%, 2003 194/255=76.08%, 2004 214/237=90.30%, 2013 221/221=100%, 2026 341/341=100%; gr 2002 270/271=99.6%, rest 100% | same | MATCH |
| 2002 minutes | legacy `min` col: 344/344 rows are string `"--"` = 100% null | 100% null | MATCH |
| CON 2013 worked example (own code) | prior-5 = 400445826/854/709/771/798 with 200/201/200/199/202 min → b5=1002.0, b3=601.0, window last tip 2013-07-02T23:00Z < target tip | identical | MATCH |
| CON 2014 continuity (own code, 20-key lineage) | game-1 400539461 (2014-05-16T23Z), game-2 400539470 strictly after; matched 2769 / total 6829 → **c = 0.4054766**, roster 12 | c=0.405477=2769/6829 | MATCH |
| Expansion / 2002 neutrality | GSV 2025: 46/46 rows `expansion_no_prior`, c all NA; POR_PDX 2026: 44/44; TOR 2026: 44/44; 2002: 542/542 `no_prior_in_corpus`, 0 minutes-computed | same | MATCH |
| IND 2013 absence (own code) | target 400496780 (IND id 5), recent 400445897 strictly prior, top5 {803,125,1003,851,860}, **c_absence_share = 0.64408** | 0.644 | MATCH |
| Strict as-of inequality (own scan, 11,976 rows) | 0 violations on b3/b5 window-last-tip and c recent-game tip | 0 / 11,976 | MATCH |
| Deterministic rebuild (lane's code, temp dir) | re-ran `build_features.py` copy → parquet sha **identical** `ceaf10ba…f7bf`, 826,415 B, rc 0 | same sha | MATCH |
| Outcome-column scan | 40-column whitelist: 0 banned-name hits; 0 dup (game_id, team_side); no wall-clock columns | ZERO outcome columns | MATCH |
| Computed-row counts | continuity 5,907 ✓; b5 5,778 ✓; c form 5,778 ✓; **b3 = 6,124** (not 5,778) — see MINOR-1 | 5,907 / 5,778 / 5,778 | b3 MISMATCH (doc only) |

## 3. NFL crosswalk (lane C_NFL_CROSSWALK) — verdict PASS

| check | my measurement | lane claim | verdict |
|---|---|---|---|
| Re-hash | players.parquet `485b1980…304885e2` 3,389,574 B; timestamp.json `23955f4e…`; 5 predecessor inputs all match predecessor pins | same | MATCH (7/7) |
| Schema | 24,844 × 39; gsis_id 0 null / 24,844 unique; pfr_id non-null 22,679; latest_team 32 distinct | same | MATCH |
| Weekly stats GSIS join | 2024: 2,001/2,001 = 1.0; 2025: 2,024/2,024 = 1.0; 2026: 1,512/1,512 = 1.0; dups 0 all | 1.0 / 1.0 / 1.0 | MATCH |
| snap_counts PFR join (`pfr_player_id`) | 2025: 2,183/2,189 = **0.9972590** (unmatched ids AndeAl01, CartNa00, HallGa01, JohnIs03, OkoyCJ00, WhitCo05 = 54 rows); 2026: 1,676/1,679 = **0.9982132** (AndeAl01, OkoyCJ00, WhitCo05 = 8 rows); dups 0 | 0.997259 / 0.998213, same id censuses | MATCH |
| Round-trip 2026 | 1,512 stats GSIS → 1,508 with crosswalk pfr → 1,475 in snap26 → **0.9755291** (vs pfr-holders 0.9781167); pfr-null = Cody White, Alec Anderson, Basil Okoye, Peter Woods | 0.975529 / 0.978117, same 4 names | MATCH |
| Freshness | ACT ∧ last_season 2026 = **1,731**; per-team 52–55; 32/32 teams; stats 2026 weeks 1–4 | 1,731 / [52,55] / 32 | MATCH |
| Named spot checks (4) | Cody White (00-0035891) pfr NULL ACT LV; Alec Anderson (00-0037428) pfr NULL ACT BUF; Basil Okoye pfr NULL; Peter Woods pfr NULL; top-8 QBs by 2026 pass yds all have both ids and appear in snap26 | same 4 names + top-8 QB claim | MATCH |

## 4. ADJUDICATION (owner-mandated): **CONFIRM LIFT**

My independent joins reproduce lane C's measurements exactly (100% GSIS all three seasons;
99.73%/99.82% PFR; 97.55% round-trip). CONFIRMING LIFT means exactly and only:

1. **Crosswalk blocker (predecessor blocker 2) is CLEARED by measurement** — players.parquet
   downloaded, rights-checked (CC BY 4.0 license re-fetch byte-identical per lane log), and
   joins verified independently by this lane.
2. **Residual blockers stay named and carry forward:**
   - target-game injury/active/DNP/starter status = **NOT_RUN_PIT** (a LAW: no pre-game
     publish timestamps exist in any of these sources — verified: lanes A/B/C embed no
     target-game status fields anywhere; NBA/WNBA builders read only strictly-prior rows,
     verified by full-table recompute + strict-inequality scans with 0 violations).
   - snap_counts 2026 in-season lag ≤1 week (snap build 2026-10-02 vs stats 2026-10-05).
   - release-cadence (not row-level) availability; frozen sha256s are the evidence anchors.

## 5. Boundaries — verdict PASS

- Grep of `lanes/` for `log_loss|brier|win_prob(|calibrat` + `logloss|roc_auc|auc|sklearn|
  predict_proba|accuracy_score`: **0 computation hits**. Only design-mention hits
  (B's header docstring, BANSPECT banned-column tuple, NOT_RUN declarations in .md).
- 0 scored anywhere (NBA/WNBA tables contain no outcome columns; schema + content scans above).
- Write-scope audit (read-only `git status --porcelain` observation): HEAD =
  `8ad8785bb1332540d0a3e92ca3feed14f92c3116` = dispatch sha, branch
  `orca/winprob-playerfeat-prep-v1-integration`; untracked = `lanes/D_VERIFY/` (this lane)
  + `lanes/DISPATCH/DISPATCH_D_VERIFY.md` (packet) only. A/B/C artifacts already committed
  by controller. No unexpected paths.

## Machine outputs

`hash_output.json` (40/40), `nba_join_output.json`, `nba_recompute_output.json`,
`nba_guard_counterfactual_output.json`, `wnba_output.json`, `wnba_hash_fix.json`,
`wnba_rebuild_output.json`, `nfl_output.json`. Scripts: `scripts/v1..v6_*.py`.
