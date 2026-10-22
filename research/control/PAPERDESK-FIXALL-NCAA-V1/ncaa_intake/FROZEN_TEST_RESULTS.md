# FROZEN TEST RESULTS — NCAA College Basketball (Men + Women)

**Program type:** prediction-quality only. The beat-the-market question is NOT tested here (see verdict (c)).
**Spec:** `REPORT.md` §3/§5, frozen before this run. Implemented in `frozen_test.py` (regular-season engine) and `tournament_showcase.py` (tournament slice). Metrics: `frozen_metrics.json`, `tournament_metrics.json`.
**Run date:** 2026-10-21. Eval seasons: 2024, 2025, 2026 (the three most recent completed seasons at run time; the 2026 season is verified complete in the source data — final games 2026-04-05/06).
**Status of verdicts: PROVISIONAL** — per the standing rule set 2026-10-21, every verdict requires an independent audit (spec compliance / full effort / remaining paths) before it counts as final.

---

## Method compliance (frozen rules, as run)

- **Population:** D1-vs-D1 games (both teams carry an ESPN conference id), completed, non-tied, from the sportsdataverse ESPN schedule releases, seasons 2016–2026.
- **Frozen Elo (pilot-identical):** K=20, home-court +65 Elo (0 at neutral sites), 25% regression toward 1500 between seasons, new teams start at 1500. Probabilities recorded **pre-game**; ratings update only after each game.
- **Efficiency features:** adjusted offensive/defensive ratings rebuilt game-by-game in the same walk-forward pass (see Deviation 1), plus rest days, conference-game flag, neutral-site flag. All features are point-in-time — no end-of-season snapshot is used in-season anywhere.
- **GBM challenger:** `HistGradientBoostingClassifier`, all sklearn defaults, `random_state=0`, no tuning. Trained per eval season Y on regular-season games of seasons < Y only; frozen feature list (elo_diff, eff_margin, net_diff, rest_h, rest_a, rest_diff, conf_game, neutral).
- **Naive baseline:** constant home-win probability estimated from all games in seasons < Y (pilot rule).
- **Internal validation:** the frozen run reproduces the deep-check pilot's 2025 numbers to 4 decimal places for both genders (men: Elo LL 0.5710, naive LL 0.6516, n=5,641; women: Elo LL 0.5276, naive LL 0.6715, n=5,160). The pipeline is the pilot pipeline, extended — not a rewrite.

---

## MEN — regular season (the evaluation engine)

| Season | n | Elo LL | GBM LL | Naive LL | Elo Brier | GBM Brier | Naive Brier | Elo acc | GBM acc |
|---|---|---|---|---|---|---|---|---|---|
| 2024 | 5,606 | 0.5756 | 0.5446 | 0.6539 | 0.1957 | 0.1842 | 0.2306 | 70.2% | 71.9% |
| 2025 | 5,641 | 0.5710 | 0.5301 | 0.6516 | 0.1937 | 0.1792 | 0.2295 | 71.3% | 72.3% |
| 2026 | 5,647 | 0.5726 | 0.5333 | 0.6554 | 0.1946 | 0.1814 | 0.2313 | 70.5% | 71.5% |
| **Pooled** | **16,894** | **0.5731** | **0.5360** | **0.6536** | **0.1947** | **0.1816** | **0.2305** | **70.7%** | **71.9%** |

All three models are scored on identical games. Naive constant ≈ 0.640 home-win rate each season.

**Kill lines (men):**
- GBM average log-loss gain vs frozen Elo: **+0.0371** (line: ≥ 0.005) ✓; GBM seasons lost to Elo: **0 of 3** (line: must not lose 2 of 3) ✓ → ML layer passes.
- Best model (GBM) pooled log loss 0.5360 vs naive 0.6536 → margin **0.1177** (line: ≥ 0.03) ✓ → program passes.

## WOMEN — regular season (the evaluation engine)

| Season | n | Elo LL | GBM LL | Naive LL | Elo Brier | GBM Brier | Naive Brier | Elo acc | GBM acc |
|---|---|---|---|---|---|---|---|---|---|
| 2024 | 5,395 | 0.5389 | 0.4785 | 0.6705 | 0.1800 | 0.1591 | 0.2388 | 73.5% | 76.4% |
| 2025 | 5,160 | 0.5276 | 0.4661 | 0.6715 | 0.1753 | 0.1554 | 0.2393 | 74.4% | 75.9% |
| 2026 | 5,480 | 0.5360 | 0.4696 | 0.6745 | 0.1792 | 0.1564 | 0.2407 | 72.9% | 75.9% |
| **Pooled** | **16,035** | **0.5343** | **0.4715** | **0.6722** | **0.1782** | **0.1570** | **0.2396** | **73.6%** | **76.1%** |

Naive constant ≈ 0.607 home-win rate each season.

**Kill lines (women):**
- GBM average log-loss gain vs frozen Elo: **+0.0628** (line: ≥ 0.005) ✓; GBM seasons lost to Elo: **0 of 3** ✓ → ML layer passes.
- Best model (GBM) pooled log loss 0.4715 vs naive 0.6722 → margin **0.2008** (line: ≥ 0.03) ✓ → program passes.

---

## Tournament showcase (spec slice — judged ONLY by the seed-only Brier rule)

Pooling is satisfiable: 2024 + 2025 + 2026 tournaments = **201 games per gender** (≥ 3 tournaments, ≥ 190 games). Seed-only baseline = logistic regression on (away seed − home seed), fit on the 2016–2023 tournaments (men: n=466, coefficient 0.145; women: n=449, coefficient 0.271). Seeds are public facts sourced per-year (see Deviation 3); every tournament team in the data was matched 1:1 to its seed.

**Pooled Brier, 2024–2026 tournaments (lower is better):**

| Gender | Frozen Elo | GBM | Seed-only | GBM beats seed? | Elo beats seed? |
|---|---|---|---|---|---|
| Men (n=201) | 0.1947 | **0.1711** | 0.1765 | **YES** (+0.0053) | NO |
| Women (n=201) | 0.1626 | **0.1110** | 0.1266 | **YES** (+0.0156) | NO |

Per-season Brier (GBM vs seed-only): men — 2024: 0.1952 vs 0.1935 (loses), 2025: 0.1577 vs 0.1634 (wins), 2026: 0.1605 vs 0.1726 (wins). Women — GBM wins all three seasons (0.1241/0.1084/0.1004 vs 0.1251/0.1225/0.1320).
Context (pooled log loss / accuracy): men — GBM 0.5060 / 73.1%, seed-only 0.5286 / 75.6%, Elo 0.5737 / 73.6% (seed-only actually picks more men's winners straight-up; the GBM's probabilities are better calibrated, which is what the spec's Brier rule measures). Women — GBM 0.3422 / 83.6%, seed-only 0.3970 / 80.1%, Elo 0.4987 / 75.1%.

**Showcase ruling:** the tournament claim stands **for the GBM layer only**, in both genders. The frozen Elo alone fails the seed-only rule in both genders and makes no tournament claim. The men's GBM margin is thin (+0.0053 Brier, carried by 2 of 3 tournaments) — it passes the frozen rule as written, but it is not a robust margin.

---

## TERMINAL VERDICTS (provisional, pending independent audit)

**(a) ML layer — ALIVE, both genders.** The frozen GBM challenger beats the frozen Elo by +0.0371 (men) and +0.0628 (women) average log loss across the three eval seasons, winning all 6 gender-seasons. Both pre-registered kill lines are passed by wide margins.

**(b) Prediction program — ALIVE, both genders.** The best model beats the naive constant-home-rate baseline by 0.1177 (men) and 0.2008 (women) pooled log loss, far beyond the 0.03 kill line. The program also holds a (GBM-only) tournament showcase pass against the seed-only baseline in both genders.

**(c) Money question — THIẾU DỮ LIỆU (data-blocked), unchanged.** No free, lawful archive of NCAA closing odds exists (verified in the deep-check: the "18 years of odds" GitHub repo is a Gumroad funnel with a 50-row sample; OddsPortal is ToS-grey). Nothing in this run manufactures a market claim: prediction quality vs a naive baseline and vs seeds says nothing about beating a closing line. Unlock path is unchanged — ≥ 1 season of forward-recorded closing lines (≥ 1,000 lined games) or a user-side purchase/account action.

---

## Deviations and data notes (explicit)

1. **Adjusted efficiency rebuilt in points space (the one implementation deviation).** The spec calls for rebuilt adjusted efficiency ratings; the ESPN schedule feed carries no play-by-play/possession data, so per-possession efficiency could not be wired. The rebuild was done game-by-game from final scores: an expanding league mean (points per team-game), team offensive/defensive deviations adjusted for opponent and location (+3.2 pts home if not neutral), update step 0.06, 25% between-season regression — the same walk-forward pass and regression trigger as the Elo. Features remain strictly point-in-time; no leakage is introduced. A future v2 with true per-possession efficiency would be a NEW pre-registered spec, not a retune of this one.
2. **Eval seasons = 2024/2025/2026**, per the spec's "three most recent completed seasons at run time." The 2026 season is complete in the source data for both genders.
3. **Seeds sourced from Wikipedia tournament articles** (the spec's sanctioned public source; the Kaggle file is account-gated and no account was created). All 20 tournaments 2016–2026 parsed and validated (correct seed multisets) and matched 1:1 to ESPN team ids, with three documented no-game exceptions: men 2017 New Orleans and Wake Forest (their March 14, 2017 First Four games are absent from the ESPN source release itself — verified against the raw parquet; the men's 2017 tournament slice therefore has 65 games in the data) and men 2021 VCU (COVID no-contest — the game was never played).
4. **No other deviations.** No post-tip features anywhere (any such feature would void the run); GBM untuned with sklearn defaults; kill lines applied exactly as pre-registered.

## Files produced by this run

`frozen_test.py`, `tournament_showcase.py`, `predictions_men.csv`, `predictions_women.csv`, `evalrows_{men,women}_{2024,2025,2026}.csv`, `frozen_metrics.json`, `tournament_metrics.json`, `games_men_full.csv`, `games_women_full.csv`, `espn/*.parquet` (raw source), `seeds/seeds_raw.csv`, `seeds/seeds_matched.csv`, `seeds_fetch.py`, `match_seeds.py`.
