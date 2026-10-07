# PLAN — WNBA-MONEY-BACKTEST-PREP-V1 (pre-money odds backtest PREP, $0 data budget)

- cycle_id: `WNBA-MONEY-BACKTEST-PREP-V1` · asset: shared · PLANNED_NOT_STARTED →
  ACTIVE_LIGHT on registration · **budget 0 scored by law** · GO phrase REGISTERED,
  NOT typed: `GO WNBA MONEY BACKTEST PREP V1 SCORED RUN`
- Owner instruction 2026-10-07 (this chat): separate WNBA lane, parallel to the
  win-probability PREP cycle. Do everything valid to prepare a VERIFIABLE
  pre-money backtest with **$0 data budget**; keep scored/GO at this cycle's own
  gate. Do NOT touch, wait on, or reuse any feature/arm of the win-probability
  task (`WNBA-WINPROB-PROSPECTIVE-PREP-V1` — prelaunch-ready pending ITS owner
  GO, and `WNBA-PLAYERFEAT-SCORED-V1` TERMINAL).

## 1. Single forecast authority (frozen, verbatim, never re-tuned)

- **B1-WNBA frozen** (inherited from WNBA-PLAYERFEAT-SCORED-V1 TERMINAL):
  own-Elo **K=32, HCA=50, gamma=0.65**. OOS 2020–2026, n=1,773/arm, pooled LL
  **0.6116031**, ΔLL vs B0 = −0.085856, 95% paired tip-date-cluster bootstrap CI
  [−0.103702, −0.067931], folds 0/7, slope 1.0467.
- Forecast bytes (sha256 pinned at this cycle's freeze):
  `.worktrees/wnba-playerfeat-scored-v1/integration/lanes/EXEC/real_20261006/
  predictions_b1_wnba.csv` (columns: game_id, season, tip_utc, p_home,
  p_home_hex, home_win, neutral, flags) + `results.json` (census/gates).
- **Label law:** these forecasts are `RECONSTRUCTED_RETROSPECTIVE` — computed
  post-hoc under the locked walk-forward law; **never** prospective OOS, never
  live-recorded at tip time. Every output of this cycle carries that label.

## 2. Odds data gate (fail-closed, BEFORE any PnL)

Required: free historical WNBA odds with **proven true pre-tip timestamps**,
documented license, per-row provenance (book, two-sided moneyline market,
decimal/US odds, line timestamp, game/teams, tip time, result, settlement
rule). Measured coverage per season 2020–2026: match rate to universe, missing,
stale quotes, line changes, duplicates, postponements. **Forbidden:** inferring
odds from scores/closing-only prices without line timestamps; scraping in
violation of source ToS; purchases, accounts, credentials.
- If no reliable+authorized source: **`NOT_RUN_ODDS`** — report blocker, STOP
  before PnL, and hand the owner a **prospective odds-capture plan (2027+)**
  as the replacement path. This is a valid terminal outcome, negative-first.

## 3. As-of reconciliation law (reconstruction + odds join)

- Decision anchor default: **≥6h before that ET game-day's first tip** (the
  frozen WNBA prospective cadence as the DEFAULT, its coverage must be
  MEASURED from the odds data, not assumed). If measured pre-anchor coverage
  fails, fall back to a **pre-registered, pre-PnL-look** anchor (e.g. last
  quote before a fixed hour pre-tip) — chosen and frozen BEFORE any PnL run,
  with the choice justified only by coverage numbers, never by PnL.
- Odds → implied probabilities via **no-vig normalization** (two-sided ML only);
  vig/overround measured and journaled per row; settlement rule stored per row.
- Join keys: game_id crosswalk where possible (team abbrev + ET date fallback);
  every match/stale/duplicate/postponed case journaled, none silently dropped.

## 4. Policy freeze shape (0..N bets; parameters pre-registered, not PnL-fit)

- Bet side i iff `EV_i = p_B1,i × dec_odds_i − 1 > ev_threshold` (pre-registered)
  AND B1 not-too-uncertain (pre-registered margin guard `|p_B1,i −
  p_market_novig,i| >= delta_min`); **p>60% alone is never a bet rule**.
- Mandatory baselines: `NO_BET`, `market-only-no-vig`, `flat-stake`.
- Risk candidates (frozen before PnL, small grid, all reported — no winner
  selection on 2020–2026 PnL): flat 0.25% / 0.5% bankroll per bet; fractional
  Kelly f* with tiny fractions {0.05, 0.10} × per-bet cap ≤1% × per-day cap.
  Parameter choice: train-internal logic only (simulator + synthetic + fixture
  math); **no optimization on any real 2020–2026 PnL**, which is only computed
  post-GO as a full-slate diagnostic.
- Journal law: every game and every intent row — selected / rejected (reason) /
  missing-or-stale odds / blocked / deferred / settled / fees-limits / stake /
  bankroll before-after. Report: turnover, net ROI, total PnL, max drawdown,
  longest losing streak, uncertainty CI (tip-date-cluster bootstrap, seed pinned
  at freeze), per-season stability, and sensitivity to worse fill (odds shade).

## 5. Simulator + adversarial law (built BEFORE any real-PnL run)

Adversarial battery (each a PASS/FAIL gate on the harness): odds sides swapped;
stale quotes; postponed/canceled games; timestamps after tip; push/void;
duplicates; overround extremes; low bankroll; multiple same-day games; data
drift (schema/units). Deterministic seeds; byte-comparable outputs. An
independent verifier re-runs the suite from bytes/hashes at a detached tree.

## 6. Gates + scored boundary

- Gate order: odds-data gate (§2) → as-of/reconciliation gate (§3) →
  rights gate (per-source license + provenance evidence) → simulator/adversarial
  gate (§5) → freeze packet (code+data+policy+anchor+seed+CI spec, final SHAs) →
  independent A7 prelaunch audit → **owner typed GO at THIS cycle's gate only**
  → scored historical backtest (full-slate diagnostic, RECONSTRUCTED_RETROSPECTIVE).
- Before typed GO: **zero PnL on real outcomes.** The scored run is a
  qualification diagnostic of the pipeline, never evidence of a live edge
  (forecasts are reconstructed; the market was live when they were not).
- Budget: registry budget-max 0 until freeze; a raise (if any) goes through
  registry CAS at freeze time with the pre-registered arm list (small, e.g.
  ≤8 policy arms + 3 baselines), disclosed in the decision packet.

## 7. Hard boundaries

No S1 access, no paper/live betting, no accounts, no purchases, no credentials
in logs/git, no push, no merge to main, no writes to any other cycle's
ledger/registry rows (the only registry write by this cycle is its own row via
researchctl CAS). Terminal outcomes negative-first: `NOT_RUN_ODDS`,
`BLOCKED_DATA`, `PRELAUNCH_READY_PENDING_OWNER_GO`, `REJECT_*`, `TECHABORT_*`.
