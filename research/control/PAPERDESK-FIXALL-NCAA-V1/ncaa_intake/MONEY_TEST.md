# NCAA Basketball — Money Test (CBBD closing lines vs the frozen model)

*Run: 2026-10-21 · Research only; no betting. Unlocks the money question left in the
THIẾU DỮ LIỆU box by REPORT.md §2/§6, using the user's own free CollegeBasketballData
(CBBD) API key (supplied in chat for this run; stored nowhere — passed to the API
client only via the `CBBD_API_KEY` environment variable; it appears in no file).*

## Verdict, plainly

- **Men: FAIL — market not beaten.** On 11,305 identical games, the frozen GBM's
  log loss is **0.5377** vs the closing market's **0.5236** (Δ = −0.0141 in the
  market's favour, paired **t = −7.00**). The frozen gate (REPORT.md §5, criterion 4)
  requires the model to beat the closing line at t ≥ +3.2; the model instead loses
  decisively. Per the frozen wording, this is recorded as **"market not beaten."**
- **Women: BLOCKED — not run.** The women's CBBD API host could not be reached from
  this environment at all (see §4). No women's lines, no women's numbers. The women's
  money question stays in the THIẾU DỮ LIỆU box for a purely technical reason.
- **CLV: not certified, and not computable here.** The gate's second prong (mean
  CLV > 0) requires prices captured *before* the close. A closing-line archive
  structurally cannot supply that, so no CLV number is reported — none was
  manufactured. (Moot for the edge claim anyway: the log-loss prong already fails,
  and the gate requires both prongs.)

## 1. What the API actually returned

- **Auth: OK.** The key authenticates against `api.collegebasketballdata.com`
  (Bearer). Rate limits were never hit at this run's pace (~40 requests total).
- **Endpoint used:** `GET /lines` with `season` + `startDateRange`/`endDateRange`.
- **Providers actually present in the archive** (census over all 18,866 distinct
  games pulled for seasons 2024–2026, counted *before* any gate computation):

  | Provider | Game-records | With both moneylines | With opening spread |
  |---|---|---|---|
  | **ESPN BET** | 12,007 | **11,536** | 3,037 |
  | Bovada | 4,952 | 4,451 | 4,927 |
  | Draft Kings | 4,505 | 1,611 | 4,422 |

- **Provider rule:** REPORT.md is silent on provider choice, so per the run's
  instructions the gate uses the **single most-complete provider — ESPN BET** —
  selected on moneyline coverage alone, before any log loss was computed. The other
  providers were not used for the gate (no provider shopping).
- **Fields per line record:** `provider`, `spread`, `overUnder` (the final/closing
  values — the CBBD data dictionary describes these as the "final spread value"),
  `homeMoneyline`, `awayMoneyline`, `spreadOpen`, `overUnderOpen`. **There are no
  moneyline-open fields and no timestamps** in any record. Game records carry
  date/time, team ids and school names, conferences, and final scores.
- **Line type verification:** each game has exactly one record per provider — the
  final line the book posted for that game (no intra-game series). This is the
  closing-line archive the odds hunt (ODDS_HUNT.md §2) documented, now pulled
  first-hand instead of via the deleted GitHub mirror.

### Pull mechanics (two API traps, both handled and verified)

1. **Silent 3,000-game cap.** A whole-season `/lines` request returns exactly the
   season's first 3,000 games (Nov–early Jan) with no warning; the `seasonType`
   parameter is ignored. First pulls are preserved under `cbbd_lines/capped_superseded/`
   and were **not** used. The archive was instead pulled in monthly slices
   (~500–1,600 games each, all under the cap) and de-duplicated by `gameId`
   (18,866 distinct games: 18,518 regular + 348 postseason).
2. **`endDateRange` is midnight-exclusive for timed games** (verified by split-month
   recounts: a Nov 1–15 query omits all Nov-15 games tipped after 00:00 UTC). All
   slices were therefore re-pulled with the end date extended +1 day
   (`cbbd_lines/men_lines_<season>_<slice>_v2.json`).

## 2. Coverage and join (men)

Frozen eval population: **16,894** regular-season games (`evalrows_men_2024/25/26.csv`,
all `season_type = 2`), each carrying the frozen `p_gbm` and `p_elo`.

Join method: CBBD team ids bridged to ESPN names via the CBBD teams files (2024/2025/2026)
plus the team-name strings inside the line records, with four evidence-based aliases
(App State; St. Francis (PA) for ESPN's "Saint Francis Red Flash"/"Red Wolves" — same
ESPN team id, renamed; IU Indianapolis for "IUPUI Jaguars"). Dates matched at UTC
offset 0 or +1 day (US evening tips fall on the next UTC date). Every joined game's
CBBD final score was checked against the frozen outcome `y`: **0 mismatches**.

| Stage | Games | % of eval |
|---|---|---|
| Eval games | 16,894 | 100% |
| Team names matched | 16,894 | 100% |
| Game present in CBBD lines pull | 16,863 | 99.8% |
| …with an ESPN BET record | 11,734 | 69.5% |
| …with a complete moneyline pair (**priced sample**) | **11,305** | **66.9%** |

Priced per season: **2024: 5,146 · 2025: 5,197 · 2026: 962**. The 2026 shortfall is
the archive's, not the join's: ESPN BET records in CBBD stop after **2025-12-02**
(946 priced games in Nov 2025, 16 in early Dec, none after). The 2026 subsample is
therefore early-season only — noted wherever it appears below. The pooled verdict
is carried by the two complete seasons.

## 3. The gate (REPORT.md §5, criterion 4 — log-loss prong)

Method: market probabilities = the two ESPN BET closing moneylines de-vigged by
proportional normalization (median overround 1.040). Per-game log losses computed
identically for market, frozen GBM and frozen Elo on the same 11,305 games
(probabilities clipped at 1e-6). Paired t on per-game (LL_market − LL_model);
positive t favours the model. Gate bars: n ≥ 1,000 and t ≥ +3.2 with model LL < market LL.

| Sample | n | Market LL | GBM LL | Δ (mkt − GBM) | t (GBM) | Elo LL | Δ (mkt − Elo) | t (Elo) |
|---|---|---|---|---|---|---|---|---|
| **Pooled** | **11,305** | **0.5236** | **0.5377** | **−0.0141** | **−7.00** | 0.5761 | −0.0525 | −21.70 |
| 2024 | 5,146 | 0.5290 | 0.5452 | −0.0162 | −6.09 | 0.5763 | −0.0472 | −14.01 |
| 2025 | 5,197 | 0.5198 | 0.5366 | −0.0168 | −6.31 | 0.5780 | −0.0582 | −17.62 |
| 2026 (early-season only) | 962 | 0.5156 | 0.5036 | +0.0121 | +0.99 | 0.5651 | −0.0495 | −3.86 |

- n ≥ 1,000: **yes** (11,305).
- Model LL < market LL at t ≥ 3.2: **no — the model loses**, significantly, in both
  complete seasons. The 2026 subsample nominally favours the GBM (+0.0121) but is
  small, early-season-only (provider feed ends 2025-12-02), and nowhere near the
  bar (t = +0.99 < 3.2). It does not rescue the gate and is reported for completeness.
- **Gate verdict (LL prong): FAIL.** Combined with the uncertifiable CLV prong
  (§5), the frozen criterion-4 outcome is: **market not beaten.**

For scale: the frozen GBM beats the frozen Elo by ~0.037 LL on prediction quality
(FROZEN_TEST_RESULTS.md) — and the closing market beats the GBM by about a third of
that margin again. Beating Elo was never the money question; this is.

## 4. Women — blocked, stated exactly

The women's sibling API (`api.collegewomensbasketballdata.com`) was tried ~25 times
(`/teams` and `/lines`, all three seasons, with retries): the environment's proxy
dropped the connection on **every** attempt, while the men's host works through the
same proxy in the same minutes. No women's line was ever received, so **no women's
coverage or gate numbers exist** — this is a network reachability failure in this
environment, not evidence about what the women's archive contains. If the key is
ever run from an environment that can reach that host, the identical procedure
(same slices, same join, same gate) applies unchanged; the women's evalrows
(16,035 games) are already on disk.

## 5. CLV and the betting simulation — read the labels

- **CLV: NOT COMPUTED.** Certifying closing-line value needs the price you could
  actually have taken *before* the close, timestamped. This archive holds final
  lines only (no moneyline opens at all; opening spreads exist for a minority of
  records). Reporting a "CLV" from it would be fabrication.
- **Descriptive only (not CLV):** on the 2,630 priced games where ESPN BET also
  carries an opening spread, the closing spread moved on average **1.08 points**
  (absolute) from the open, mean signed move −0.13 points (home perspective).
  This describes line movement; it certifies nothing about beatability.
- **⚠️ UPPER-BOUND SIMULATION — at-close ROI.** Flat 1-unit bets at the archive's
  **final** prices, on every game where the model's probability exceeds the
  de-vigged market probability (one side per game). These prices are the closing
  prices themselves — **in real time you cannot bet at the close after seeing it**,
  so this simulation is an *upper bound* on any real strategy, included only
  because even it is informative:

  | Model | Bets | Win rate | ROI per bet | Total (units) |
  |---|---|---|---|---|
  | Frozen GBM | 11,305 | 51.5% | **−6.2%** | −704.5 |
  | Frozen Elo | 11,305 | 31.2% | −12.8% | −1,451.6 |

  Even the impossible-at-close upper bound loses money — fully consistent with
  the log-loss verdict.

## 6. Tournament (descriptive only — not a gate)

The frozen tournament showcase never saved per-game GBM predictions, so no GBM
market comparison is possible without re-running the frozen pipeline (not done).
The saved Elo probabilities (`predictions_men.csv`, postseason rows) joined to
ESPN BET lines for **194 of 348** tournament games (2024–2026): market LL **0.5568**
vs Elo LL **0.6099** (Δ = −0.0531, t = −2.82). Descriptive context only — the sample
is far below the gate's 1,000-game minimum and the showcase was never a money test.

## 7. Files

- Raw pulls: `cbbd_lines/men_lines_<season>_<slice>_v2.json` (used) ·
  `cbbd_lines/capped_superseded/` (first capped pulls, unused, kept for provenance) ·
  `cbbd_lines/men_teams_<season>.json`.
- Joined data: `cbbd_lines/men_joined_all.csv`, `cbbd_lines/men_joined_priced.csv`.
- Machine-readable results: `cbbd_lines/money_gate_results.json`.
- No file in this directory contains the API key.

## 8. Bottom line for the program board

The NCAA prediction program stays exactly as strong as the frozen test showed
(the GBM genuinely out-predicts Elo and the naive rate). The **money** question is
now answered for men, with a named book's real closing lines at full power:
**the closing market beats the frozen model — market not beaten (FAIL)**. For
women the money question remains THIẾU DỮ LIỆU, blocked only by this
environment's inability to reach the women's API host.
