# SELECTION REPORT — NBA-PLAYERFEAT-SCORED-V1 · Lane T_SELECT

- Generated (run start): 2026-10-05T12:26:40Z · mode: `select` (TRAIN-INTERNAL ONLY) · seed 20261005
- Windows: WARM-UP 2016–2017 (streams run, never scored) · SELECTION FOLDS 2018–2021 (4 rolling-origin, expanding) · **OOS 2022–2026 NEVER TOUCHED** — hard cap `SEASON_MAX_REAL=2021` enforced at load; future schedule files never opened: ['nba_schedule_2022.csv', 'nba_schedule_2023.csv', 'nba_schedule_2024.csv', 'nba_schedule_2025.csv', 'nba_schedule_2026.csv']
- Feature table sha256 verified before use: `b3ca0e3b2eff1d1c918d56fb626e06998903c0f69253b41b67166dc8859885cb` (== FEATURE_TABLE_MANIFEST)
- Lock observations: BEFORE run `2026-10-05T12:26:40Z` verdict `FREE_PROVEN` (attempt 0) · AFTER run `2026-10-05T12:26:45Z` verdict `FREE_PROVEN`

## DESIGNED-NULL (gate-before-belief)

phi=0 configs must reproduce B1* p_home **bit-for-bit** (max |Δp| == 0.0) on the full fold stream (4599 rows) before any other number is believed.

| arm | max \|Δp\| vs B1* | verdict |
|---|---|---|
| PF-A | 0.0 | PASS |
| PF-B | 0.0 | PASS |
| PF-C | 0.0 | PASS |

## B0 constant (floor)

Refit law (protocol verbatim): per fold, home-win rate over REG played rows of all complete seasons strictly before the fold season (2016 onward; warm-up rows are train rows, never scored rows).

| fold season | B0 constant (train home-win rate) |
|---|---|
| 2018 | 0.5861788617886179 |
| 2019 | 0.583739837398374 |
| 2020 | 0.5859756097560975 |
| 2021 | 0.5798628533199531 |

- Reference (uncriterion) pooled-window home-win rate over fold rows: 0.5679495542509241; simple mean of fold constants 0.5839392905657607.

## B1* (carried VERBATIM, never re-tuned)

- Own-Elo K=32, HCA=100, γ=0.75, μ=1500; new lineages start 1500; season-boundary reversion `R ← 1500 + 0.75·(R − 1500)` before a lineage's first prediction of a new season; date-grain same-day exclusion (all predictions of a UTC date from pre-date state; updates applied after all predictions of that date) — terminal protocol semantics inherited; HCA applied everywhere (frozen neutral-site law, counts disclosed below); stream updates on played regular + playoff games (season_type ∈ {2,3}); play-in (season_type=5) and exhibitions never update the stream (matches the frozen feature-table prior law).
- Stream: 7556 updates, 180 season reversions over 7572 played games 2016–2021.
- Pooled fold LL (2018–2021 REG, n=4599): 0.6383266072624096 · calibration slope 0.780102170044627

## Standardization moments (pinned)

- Population: team-side rows of REG played non-exhibition games, tip_utc < 2021-08-01T00:00Z (warm-up+train) · ddof=0

| column | mu | sd |
|---|---|---|
| a_load_top5_k5 | 0.002502705443298247 | 0.025207685286711294 |
| a_top5_share_k5 | 0.6122604312438397 | 0.16381590030562224 |
| b_form_top3 | 0.003496551819368701 | 0.04394149457310874 |
| c_abs_out | 0.11290551069556594 | 0.316477260399763 |
| c_abs_streak | 0.034636634084147896 | 0.2900902212160311 |

Group composition (single φ per arm; multi-column groups enter as the sum of their standardized columns — recorded design decision): PF-A = z(a_top5_share_k5) + z(a_load_top5_k5); PF-B = z(b_form_top3); PF-C = z(c_abs_out) + z(c_abs_streak).

## Grid + folds (pre-registered, immutable)

- φ ∈ {-50, -25, 0, 25, 50} per arm; each arm ALONE (never stacked); 15 configs, all counted. Criterion: pooled mean LL over fold rows. Tie-break: fewer active params, then lexicographic config id.
- Fold rows: REG (season_type=2) played non-exhibition games of seasons [2018, 2019, 2020, 2021]: {'2018': 1230, '2019': 1230, '2020': 1059, '2021': 1080} (total 4599).
- Exhibitions excluded from rows with counts: {'total_in_window': 9, 'in_fold_seasons': 7, 'rows_excluded_2x': 14}. Play-in played games present but never scored/updated: 7. Playoff rows scored with the same frozen models, reported SEPARATELY (never in the criterion): n=332.
- Box-less FINAL games (neutral features) REMAIN in rows: ids [400975285, 401070917] (2017 sibling 400900132 sits in warm-up, not scored).
- Neutral-site flag measured (`neutral_site=true` inside fold rows): 9; per the frozen protocol HCA is applied everywhere (declared limitation; conditional switching would be a new trial).

## Verdicts (G-ENTRY per arm)

ADMIT: pooled inner ΔLL(arm, B1*) point < 0 AND calibration slope ∈ [0.85, 1.15] AND time-shuffled twin not winning. CI entirely > 0 ⇒ KILL. Twin beats parent ⇒ MACHINERY_SUSPECT, arm UN-SCORED. Bootstrap: tip-DATE-clustered, 10,000 resamples, seed 20261005, percentile CI.

| arm | selected φ | pooled LL | ΔLL vs B1* (95% CI) | slope | twin LL (wins?) | verdict |
|---|---|---|---|---|---|---|
| PF-A | — | 0.638327 | +0.000000 [+0.000000, +0.000000] | 0.780102170044627 | 0.638327 (clean) | **NOT_ADMITTED** (point_dell_not_negative, slope_out_of_band) |
| PF-B | — | 0.638327 | +0.000000 [+0.000000, +0.000000] | 0.780102170044627 | 0.638327 (clean) | **NOT_ADMITTED** (point_dell_not_negative, slope_out_of_band) |
| PF-C | — | 0.638327 | +0.000000 [+0.000000, +0.000000] | 0.780102170044627 | 0.638327 (clean) | **NOT_ADMITTED** (point_dell_not_negative, slope_out_of_band) |

## Frozen φ (ADMITTED arms)

- None — all candidate arms failed G-ENTRY (see verdicts above).

## Diagnostics (outside budget)

- B1-HCA0 ablation: pooled fold LL 0.6428161170449253; ΔLL(B1*, B1-HCA0) = +0.004490 [-0.003291, +0.012047] (Δ < 0 favors HCA=100; H2 direction check only).
- Time-shuffled twins (feature pair swapped across team-sides per game by seeded coin, seed 20261005): on each arm's SELECTED config (= φ 0 for all three arms, where the swap is an identity): PF-A 0.638327, PF-B 0.638327, PF-C 0.638327 — none wins. Extra diagnostic on each arm's best NON-zero config (twin cannot rescue it either): PF-A φ=-25 parent 0.643365 vs twin 0.641190 (WINS); PF-B φ=25 parent 0.642574 vs twin 0.641048 (WINS); PF-C φ=-25 parent 0.643030 vs twin 0.644586 (no win).

## Negative-first reading

- Every non-zero φ in all three grids INCREASES pooled fold LL vs B1* (ΔLL > 0, CIs entirely > 0 at |φ| ≥ 25); each arm's grid minimum is its own φ=0 designed null, i.e. the arm degenerates to B1*. G-ENTRY fails on `point_dell_not_negative` (point ΔLL = 0.0, not < 0) — no kill fired (no CI of a SELECTED config is entirely > 0, since the selected config IS the null); no twin fired. **Slot release: no φ frozen for any PF arm; the rating-input shape carries no train-internal player-feature gain at the pre-registered grid scales.**

## Feature-table reconciliation (read-only bytes)

- sha256 verified == FEATURE_TABLE_MANIFEST; capped table 15,144 rows (seasons 2016–2021) after slicing the manifest-exact 13,230 future rows (2022–2026) — accounting asserted equal to the manifest per-season table, so any doctored row shifts it and aborts.
- Neutral rows in the capped window per season: {2016: 152, 2017: 152, 2018: 154, 2019: 154, 2020: 154, 2021: 152} (matches FEATURE_TABLE_MANIFEST rows for 2016–2021).
- Manifest composition wording note: the three box-less FINAL games' OWN rows measure `feature_neutral=0` in bytes (their features derive from prior games); box-less-ness means they contribute 0 usable rows to LATER games' prior windows. Per-season neutral counts reconcile exactly regardless; bytes are authority.

## Budget / fit accounting

- Ledger rows on real fold rows: 18 = 15 PF candidate configs (all counted) + B0 + B1* (references) + B1-HCA0 (diagnostic row). Twin computations (outside budget): 6 = 3 on selected configs + 3 on best-non-zero configs. B0 refits: 4 constants. Elo replays: 2 streams (B1*, B1-HCA0) — PF arms share the B1* stream (φ enters only the argument). Designed-null checks: 3. Every evaluated config has a SELECTION_LEDGER.jsonl row.

## Data-shape observations

- Schedule rows loaded (2016–2021 only): 7616; played: 7572; postponed/not played: 44.
- Language law: calibration/forecasting vocabulary only; no betting vocabulary anywhere.
- No OOS season, no GO token, and no scored OOS number exists in this lane.
