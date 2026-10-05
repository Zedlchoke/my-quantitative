# VERIFICATION_REPORT — D_VERIFY · NFL-PLAYERFEAT-PREP-V1 · 2026-10-05

Independent verifier lane. Never repaired; recomputed from bytes with its OWN code
(scripts in `lanes/D_VERIFY/work/`, written fresh from `FEATURE_SPEC.md` — the builder's
functions were not reused for any verdict value; the builder was re-EXECUTED only for the
determinism reproduction, as permitted by the dispatch). Interpreter:
`/Users/hoangminhlong/my-quantitative/.venv/bin/python` only. No URL fetches, $0.

## Scope verified

Subject: `~/.my-quantitative-data/nfl-playerfeat-prep-v1/features/nfl_playerfeat_table_v1.parquet`
(claimed sha `f1bc6b4a…7c4f57`, 1,266 × 44) + the B_BUILD lane artifacts
(FEATURE_SPEC.md, FEATURE_TABLE_MANIFEST.md+json, COVERAGE_AUDIT.md, PIT_AUDIT.md,
VERDICT_TABLE.md, build_features.py, handoff_B_BUILD.json).

## T1 — Input + output re-hash: PASS (7/7)

All six manifest inputs and the output parquet re-hashed with verifier-owned code
(`work/t1_hash.py`): every sha256 equals the manifest pin, including the output
`f1bc6b4a8c7f5c36457aaa393666ca90cc446cc6f934c3ea55f739b5de7c4f57`. Zero mismatches.

## T2 — Join rates re-measured: PASS (5/5 + censuses)

Own code (`work/t2_join.py`): stats GSIS→crosswalk 2001/2001, 2024/2024, 1512/1512 = 1.0
for 2024/2025/2026 (placeholder rows 22/22/4 = 48, matching the claimed exclusion count);
snap PFR→crosswalk 2183/2189 = 0.997259 (2025), 1676/1679 = 0.998213 (2026); unresolved
censuses exactly {AndeAl01, CartNa00, HallGa01, JohnIs03, OkoyCJ00, WhitCo05} (2025) and
{AndeAl01, OkoyCJ00, WhitCo05} (2026). All match the manifest and predecessor D_VERIFY.

## T3 — Independent row recompute: PASS (7 rows deep-recomputed + full-table as-of recount)

Verifier's own as-of implementation (`work/t3_recompute.py`, `t3b_kc_example.py`,
`t3c_g2_kc.py`): independent kickoff-UTC derivation (gameday+gametime → America/New_York →
UTC), strict-inequality prior selection, per-(season,team) accumulation, explicit window
slicing, python-loop sums.

- **Full-table recount (all 1,266 rows):** kickoff_utc strings, n_prior_games_used,
  rest_days (max abs dev 0.0), g3_n_snap_prior_games, flag_g3_pfr_null_excluded —
  **0 mismatches on every counter**.
- **KC worked example 2024_11_KC_BUF (KC = away side):** from stats bytes — priors list
  = weeks 1–5,7–10 (wk6 bye skipped), n_prior = 9, rest_days 7.14236, prior-3
  = **819 yds / 6 TD / 1 INT / 124 att** exactly; ypa 6.60484, epa 30.55991,
  epa_pa 0.24645, std_pg 245.33333/3.33435, form +27.66667/+6.85229, k5 1304 yds/190 att.
  G2: U_tot 189, top-3 Hunt 74 / Kelce 40 / Hopkins 17 → 131/189 = 0.69312, hhi 0.22208,
  usage_pg 63.0, top5_k5 0.79299. Every scalar matches PIT_AUDIT §2 and the table row.
- **Bye-week row 2024_07_KC_SF (KC, away):** n_prior 5, rest 12.84028, window wks 5/4/3,
  qb_yds_k3 793 — identical to table (0 column diffs across all 44 cols).
- **Neutral opener 2026_01_ARI_LAC (ARI):** n_prior 0, G1/G2/rest all NaN, flags correct —
  identical (0 diffs). Part of the 96-row no-prior cohort (count verified below).
- **pfr-null exclusion row 2026_02_LV_LAC (LV):** flag_g3_pfr_null_excluded = 1, G3 n = 1,
  absent share 0.0 — identical. Canary confirmed independently: crosswalk gsis 00-0035891
  (Cody White) pfr_id NULL; WhitCo05 = 3 snap-2026 rows (LV, wks 1–3); LV 2026 rows
  wk2–4 flagged, wk1 no-snap flagged.
- **n_w=1 case 2025_02_WAS_GB (WAS)** and **2026_04_PIT_CLE (CLE, n=3)** — identical (0 diffs).

## T4 — Missing-data rules, outcome ban, determinism: PASS

`work/t4_rules.py`, `t4b_claims.py`:

- Schema = exact 44-column whitelist (keys 7 + as-of 4 + G1 20 + G2 4 + G3 3 + flags 6);
  1,266 × 44; 0 duplicate (game_id, side); rows sorted by (kickoff_utc, game_id, side);
  `asof_rule_version` constant `asof-1.0.0-nfl-playerfeat-prep-v1`; all flags binary;
  kickoff strings ISO-Z format.
- **Outcome columns: 0** — banned-token scan 0 hits; no object columns beyond keys/as-of;
  all numeric content recomputed provenance-verified (full as-of layer + 7 deep rows).
- Flag counts vs manifest: no_prior **96/96**, g3_no_snap **634/634**, g3_pfr_null **82/82**,
  g2_zero_usage **0/0**, trunc k3 **192/192**, k5 **350/350**; per-season splits all match
  (570/570/126 rows; 538/538/94 G1G2-with-prior; G3 computable 0/538/94).
- Neutral behavior: all 96 no-prior rows have G1/G2/rest NaN and n_prior = 0; all 634
  no-snap rows have G3 NaN (all 570 rows of 2024 flagged); converse holds (all 1,170
  with-prior rows have non-NaN G1/G2; all 632 with-snap rows have non-NaN G3);
  all 64 n_w=1 rows have absent share exactly 0.0 (documented exception); trunc flags
  consistent with n_prior ∈ {1,2} / {1..4}; negative rest_days 0; shares >1: 0.
- **Determinism: fresh-process rebuild via the lane's `build_features.py` into
  `/tmp/dverify_rebuild_pfr` → sha `f1bc6b4a…7c4f57`, byte-identical to shipped.**
- Universe re-measured: games.csv 2024–26 = 285/285/272 = 842; unique stats game_ids 633;
  0 orphans; 2026 played 63 / future 209; earliest future kickoff 2026-10-06T00:15:00Z;
  first-computable dates 2024-09-13 / 2024-10-11 / 2025-09-12 / 2025-09-26 (all Z) — match.
- Shipped `FEATURE_TABLE_MANIFEST.json` / `selftest_results.json` byte-identical to the
  lane copies.

## T5 — Boundary audit: PASS

- Scored-pattern grep over `lanes/` (win_prob/brier/log_loss/calibrat/moneyline/odds/
  bet/kelly/stake/…): every hit is a ban-list declaration, boundary statement, dispatch
  text, or this verifier's own ban-list constant. **0 scored-metric computation.**
- Isolation: `git -C …/nfl-winprob-ng-scored-v1/integration status --porcelain` →
  **empty (clean)**; read-only observation only; no writes from this cycle.
- Write scope (own worktree porcelain): only `lanes/DISPATCH/DISPATCH_D_VERIFY.md`
  (orchestrator) and `lanes/D_VERIFY/` (this lane) untracked; B_BUILD artifacts already
  controller-committed. No out-of-scope writes.
- Stray empty dir `lanes/"B_BUILD lanes"/D_VERIFY/` (created 18:48 at dispatch time,
  before both lanes ran; empty) — pre-existing orchestrator path artifact, untouched by
  this lane, registered INFO.

## Verdict

**VERIFIED_WITH_MINOR** — the table itself is fully verified (all hashes, joins, as-of
law, worked examples, missing-data rules, determinism, boundary compliance reproduce
exactly). Two MINOR documentation inaccuracies inside B_BUILD audit prose are registered
(`DISCREPANCY_REGISTER.md`); neither affects any table value, the manifest, or the
NOT_RUN_PIT law.

Discrepancy counts: BLOCKER 0 · MAJOR 0 · MINOR 2 · INFO 2.
