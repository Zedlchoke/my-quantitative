# Memo — Edge watchlist W3 (A4 research, sprint 2026-08-23)

Author: agent A4 · Branch `wt/research-analysis` · Scan analyzed:
`results/scan_matrix/20260823T051806Z` (main-repo artifact, read-only).

**Scope guard:** zero changes to `config/*.yaml`, `strategy_*.py`, `backtest/`,
`risk/`. All numbers below reproduce via
`research/analyze_edge_stability.py` (command at §6). No parameter tuning was
done or proposed; gates in §5 are *research filters to validate signal-only*,
frozen before W3 forward data.

---

## 1. Window-level gate screen (EDGE definition v2)

Sources: per-combo JSONs + `report.json` (`pf_after`, official aggregate PF).

| combo | trades | exp_af | PF (official) | folds+ | PnL_af | buy&hold | PnL>BH |
|---|---|---|---|---|---|---|---|
| reclaim_mr NEARUSDT | 182 | +0.148 | 1.463 | 4/6 | +26.95 | −152.43 | YES |
| reclaim_mr ETHUSDT ⚠ | 149 | −0.151 | 0.611 | 4/6 | −22.44 | +246.69 | NO |
| trend_pullback BOMEUSDT | 780 | +0.128 | 3.353 | 4/6 | +99.72 | −51.84 | YES |
| markdown_breakdown ADAUSDT | 348 | +0.039 | 1.143 | 4/6 | +13.64 | +228.03 | NO |
| reclaim_mr SOLUSDT | 179 | +0.037 | 1.179 | 3/6 | +6.68 | −36.33 | YES |

⚠ ETH reclaim_mr = cautionary control (see §4.5).

---

## 2. Method

1. Fold windows from artifact `cells[]` (6 equal WF folds over
   2024-08-23→2026-08-23); quarter assigned by UTC midpoint of each fold
   (folds span 4 months ⇒ they cross quarter boundaries; both spanned quarters
   are reported).
2. Regime labels: daily bars resampled from the 15m catalog
   (`catalog_live_crypto`, 70,079 bars/symbol), classified with
   `regime_wyckoff.classify_wyckoff_row` + frozen `WyckoffConfig`
   (EMA50/200, ADX14, 20d return, 60d range position). Day *i* uses only
   completed days `< i` (same semantics as `WyckoffDailyTracker`). The config
   requires ≥205 daily bars of history ⇒ the first 121 days of the window
   (until 2025-03-16) are labeled `warmup`, **not** force-labeled. Folds F0 and
   most of F1 are therefore partially/entirely unlabeled — reported as-is.
3. Concentration test: losing folds are “concentrated” if their
   (mid-quarter, dominant-phase) pairs number ≤2.

---

## 3. Combo × fold × quarter × regime × PnL (PnL after funding)

### 3.1 reclaim_mr NEARUSDT — exp_af +0.148, PF 1.463

| fold | window | quarters | trades | pnl_af | exp_af | PF | WR | ± | dominant phase | phase mix (days, labeled/warmup) |
|---|---|---|---|---|---|---|---|---|---|---|
| F0 | 08-23→12-22 | 2024Q3–Q4 | 35 | **−41.06** | −1.173 | 0.64 | 0.26 | − | warmup | warmup:121 |
| F1 | 12-22→04-23 | 2024Q4–2025Q2 | 37 | +6.38 | +0.172 | 1.06 | 0.41 | + | markdown 64% | md:25 tr:5 acc:9 warm:83 |
| F2 | 04-23→08-23 | 2025Q2–Q3 | 29 | **−17.18** | −0.592 | 0.82 | 0.38 | − | transition 60% | tr:73 md:42 acc:7 |
| F3 | 08-23→12-22 | 2025Q3–Q4 | 21 | +9.55 | +0.455 | 1.20 | 0.43 | + | markdown 54% | md:65 tr:49 acc:7 |
| F4 | 12-22→04-23 | 2025Q4–2026Q2 | 25 | +34.05 | +1.362 | 1.75 | 0.60 | + | transition 55% | tr:67 md:54 acc:1 |
| F5 | 04-23→08-23 | 2026Q2–Q3 | 35 | +35.21 | +1.006 | 1.53 | 0.49 | + | transition 72% | tr:88 mk:18 acc:9 md:7 |

NEAR quarterly context: 2024Q4 net +1.6% with −57.6% intra-quarter maxDD
(crash-and-recover chop); 2025Q2 net −19.0%, DD −47.0%. Winner mid-quarters:
2025Q1 (−52.6%), 2025Q4 (−46.6%), 2026Q1 (−27.0%), 2026Q2 (+49.7%).

**Losing-fold structure:** F0 = window-start warmup era (unclassifiable by
frozen daily config; NEAR −41.8% DD quarter); F2 = 2025Q2 grind-down,
94% of labeled days markdown+transition, zero meaningful accumulation days.
Concentration: **YES** (2 distinct quarter-phase pairs).

Observable separator (descriptive, n=2 losers): losers sit in quarters where
intra-quarter maxDD ≥ 2.5× |net quarter return| (2024Q4: 57.6/1.6 = 36×;
2025Q2: 47.0/19.0 = 2.47×), all four winner mid-quarters ≤ 2.06× (65.7/52.6;
56.5/46.6; 55.6/27.0; 63.1/49.7). Threshold 2.2 proposed **post-hoc** —
unvalidated, forward-test only.

### 3.2 trend_pullback BOMEUSDT — exp_af +0.128, PF 3.353

| fold | window | quarters | trades | pnl_af | exp_af | PF | WR | ± | dominant phase | phase mix |
|---|---|---|---|---|---|---|---|---|---|---|
| F0 | 08-23→12-22 | 2024Q3–Q4 | 168 | +23.04 | +0.137 | 1.06 | 0.39 | + | warmup | warmup:121 |
| F1 | 12-22→04-23 | 2024Q4–2025Q2 | 143 | +47.88 | +0.335 | 1.16 | 0.34 | + | markdown 72% | md:28 tr:9 acc:2 warm:83 |
| F2 | 04-23→08-23 | 2025Q2–Q3 | 140 | +45.36 | +0.324 | 1.16 | 0.36 | + | transition 57% | tr:70 md:47 acc:5 |
| F3 | 08-23→12-22 | 2025Q3–Q4 | 115 | +25.83 | +0.225 | 1.11 | 0.37 | + | markdown 71% | md:86 tr:33 acc:2 |
| F4 | 12-22→04-23 | 2025Q4–2026Q2 | 110 | **−21.84** | −0.199 | 0.91 | 0.37 | − | markdown 52% | md:64 tr:46 acc:12 |
| F5 | 04-23→08-23 | 2026Q2–Q3 | 104 | **−20.54** | −0.197 | 0.91 | 0.31 | − | transition 49% | tr:60 md:37 acc:22 mk:3 |

BOME context: 2025Q4 −68.1% crash quarter; 2026Q1 −35.4%; 2026Q2 +5.8%.

**Losing-fold structure:** F4+F5 = the two most recent folds (2026Q1, 2026Q2),
back-to-back after the −68% 2025Q4 capitulation; PF steps down monotonically
1.16→1.11→0.91 across F2→F5. Concentration: **YES** (2 pairs) — but the
conditioning variable is **time, not an observable regime label**: phase mixes
of losing F4/F5 overlap heavily with winning F1/F3 (markdown-dominant folds
appear on both sides). No frozen-label separator exists; this is consistent
with **structural decay after the 2025Q4 crash**, not an avoidable regime.

### 3.3 markdown_breakdown ADAUSDT — exp_af +0.039, PF 1.143

| fold | window | quarters | trades | pnl_af | exp_af | PF | WR | ± | dominant phase | phase mix |
|---|---|---|---|---|---|---|---|---|---|---|
| F0 | 08-21→12-21 | 2024Q3–Q4 | 99 | **−65.17** | −0.658 | 0.78 | 0.38 | − | warmup | warmup:122 |
| F1 | 12-21→04-21 | 2024Q4–2025Q2 | 81 | +37.64 | +0.465 | 1.15 | 0.47 | + | transition 59% | tr:23 md:10 acc:5 mk:1 warm:82 |
| F2 | 04-21→08-21 | 2025Q2–Q3 | 28 | +29.22 | +1.044 | 1.47 | 0.57 | + | transition 47% | tr:57 mk:30 md:28 |
| F3 | 08-21→12-21 | 2025Q3–Q4 | 47 | +9.76 | +0.208 | 1.07 | 0.45 | + | transition 43% | tr:53 md:52 mk:14 |
| F4 | 12-21→04-21 | 2025Q4–2026Q2 | 51 | **−30.20** | −0.592 | 0.81 | 0.39 | − | markdown 50% | md:60 tr:38 acc:23 |
| F5 | 04-21→08-21 | 2026Q2–Q3 | 42 | +32.38 | +0.771 | 1.32 | 0.50 | + | transition 46% | tr:56 md:42 acc:24 |

ADA context: 2024Q4 **+140.1%** rip (F0 shorts destroyed by upside breakout);
2026Q1 −32.2% but squeeze-like (breakdown shorts fail inside labeled markdown,
F4 −30.20). Concentration mechanically YES (2024Q4-warmup, 2026Q1-markdown)
but hard gates fail regardless (§5).

### 3.4 reclaim_mr SOLUSDT — exp_af +0.037, PF 1.179

| fold | window | quarters | trades | pnl_af | exp_af | PF | WR | ± | dominant phase | phase mix |
|---|---|---|---|---|---|---|---|---|---|---|
| F0 | 08-21→12-21 | 2024Q3–Q4 | 35 | **−7.75** | −0.221 | 0.90 | 0.31 | − | warmup | warmup:122 |
| F1 | 12-21→04-21 | 2024Q4–2025Q2 | 35 | +10.09 | +0.288 | 1.12 | 0.40 | + | markdown 51% | md:20 tr:10 acc:9 warm:82 |
| F2 | 04-21→08-21 | 2025Q2–Q3 | 31 | +20.28 | +0.654 | 1.36 | 0.42 | + | transition 67% | tr:82 md:24 mk:11 |
| F3 | 08-21→12-21 | 2025Q3–Q4 | 23 | +13.56 | +0.590 | 1.31 | 0.48 | + | transition 50% | tr:61 mk:29 md:25 dist:7 |
| F4 | 12-21→04-21 | 2025Q4–2026Q2 | 27 | **−26.82** | −0.993 | 0.53 | 0.30 | − | transition 45% | tr:55 md:50 acc:16 |
| F5 | 04-21→08-21 | 2026Q2–Q3 | 28 | **−2.69** | −0.096 | 0.93 | 0.39 | − | transition 70% | tr:85 md:33 acc:4 |

**Losing-fold structure:** F0/F4/F5 spread over three separate periods
(2024Q4, 2026Q1, 2026Q2) with different dominant labels ⇒ scattered, **NOT
concentrated** (3 distinct pairs). Matches NOTES §15.1.3/§16: SOL MR is
borderline noise.

### 3.5 reclaim_mr ETHUSDT — cautionary control

Losing F0 (−40.84, warmup era) + F3 (−16.85, 2025Q4 transition-dominant):
concentration test **passes** (2 pairs) — yet window exp_af is **negative**
(−0.151, PF 0.611, PnL −22.44 vs BH +246.69). Demonstrates: losing-fold
concentration is necessary-but-not-sufficient; total expectancy and BH
comparison remain binding. Confirms §18.1 reading (“ETH edge mỏng phụ thuộc
giai đoạn”).

---

## 4. Slippage ×1.5 stress

**Engine finding:** no supported rerun path exists without editing forbidden
files. `research/scan_matrix.py` CLI exposes no slippage flag; the fill model
is Nautilus' compiled `OneTickSlippageFillModel` (deterministic 1 tick/fill,
no magnitude parameter); `BacktestSettings` only permits swapping to
`probabilistic` (random slip *probability*, different semantics). Analytic
path used per task instructions.

**Formula** (upper-bound, hence conservative):

```
qty_per_trade   = max_notional / mean_close          (= 300 USDT cap always binds)
Δexp_per_trade  = (mult − 1) × 2 fills × tick_size × qty
stressed_exp    = exp_after_funding − Δexp_per_trade
stressed_pnl    = pnl_after_funding − Δexp_per_trade × trades
```

With mult=1.5 ⇒ extra half-tick per fill ⇒ one extra tick per round trip.

| combo | tick | mean close | qty ub | Δexp/trade | exp_af | stressed exp | pnl_af | stressed pnl | survives? |
|---|---|---|---|---|---|---|---|---|---|
| reclaim_mr NEAR | 0.001 | 2.8013 | 107.09 | 0.1071 | +0.1481 | **+0.0410** | +26.95 | +7.46 | YES |
| reclaim_mr ETH | 0.01 | 2744.01 | 0.1093 | 0.0011 | −0.1506 | −0.1517 | −22.44 | −22.60 | NO (already neg.) |
| trend_pullback BOME | 1e-7 | 0.0024904 | 120,463.5 | 0.0120 | +0.1278 | **+0.1158** | +99.72 | +90.32 | YES |
| markdown_breakdown ADA | 0.0001 | 0.540161 | 555.39 | 0.0555 | +0.0392 | **−0.0164** | +13.64 | −5.69 | NO — flips |
| reclaim_mr SOL | 0.01 | 145.47 | 2.0623 | 0.0206 | +0.0373 | +0.0167 | +6.68 | +2.99 | YES (other gates fail) |

Caveat documented: current-model tick cost is tiny vs taker fee (e.g. BOME
tick 1e-7 on ~0.0025 ≈ 0.0004 bp/tick) — the ×1.5 stress multiplies a very
small base; real-market impact for a 300 USDT alt perp order is plausibly
larger than modeled. Stress is necessary, not sufficient, evidence.

---

## 5. Verdicts

| combo | verdict | why (one line) |
|---|---|---|
| reclaim_mr NEARUSDT | **KEEP (conditional)** | exp +0.148/PF 1.463, beats BH, survives slippage ×1.5 (+0.041); both losing folds confined to high-chop quarters (maxDD≥2.5×\|net ret\|: 2024Q4 36×, 2025Q2 2.47×) vs ≤2.06× in all winner quarters. |
| trend_pullback BOMEUSDT | **KEEP (conditional, decay-flag)** | exp +0.128/PF 3.353, beats BH, survives slippage (+0.116); 4 consecutive positive folds then both losses in the 2 latest folds (2026Q1/Q2) after the −68% 2025Q4 crash — concentrated but time-conditioned; no observable regime separator ⇒ decay suspect until proven otherwise. |
| markdown_breakdown ADAUSDT | **DROP** | PF 1.143 < 1.2 and slippage ×1.5 flips exp negative (−0.016); PnL +13.64 vs BH +228.03 (17× gap); losing folds = 2024Q4 +140% short-squeeze quarter and 2026Q1 squeeze-markdown. |
| reclaim_mr SOLUSDT | **DROP** | 3/6 folds+, PF 1.179 < 1.2, losses scattered across 3 distinct quarter-phase pairs (2024Q4, 2026Q1, 2026Q2) ⇒ noise, confirming §15.1.3. |
| reclaim_mr ETHUSDT | reference only | Passes concentration yet window exp −0.151 ⇒ concentration alone is not edge; keep as control, no action. |

## 6. Reproduce

```bash
/Users/hoangminhlong/my-quantitative/.venv/bin/python -m research.analyze_edge_stability \
    --scan-dir results/scan_matrix/20260823T051806Z \
    --catalog ./catalog_live_crypto
```

Writes machine-readable summary to `--out` (default
`results/edge_stability/edge_stability_summary.json`). Read-only elsewhere.

---

## 7. Proposed W3 signal-only watchlist (needs A1 approval; no YAML/live changes)

| # | combo | rule for W3 (signal-only, paper) |
|---|---|---|
| 1 | reclaim_mr NEARUSDT | Collect all signals; tag each with current daily Wyckoff phase + trailing-90d DD/\|net-ret\| ratio. Pre-registered evaluation: exp_af on tagged subset where ratio ≤ 2.2 must stay > 0 over the W3 window; otherwise discard candidate at W4 review. Threshold 2.2 is post-hoc (n=2) — validation, not tuning. |
| 2 | trend_pullback BOMEUSDT | Collect all signals with phase tags; primary test is survival: combined W3+W4 signal exp_af > 0 required to keep the candidate (decay check). No regime gate claimed — none is supported by the data. |
| — | ADA / SOL / new legs | Not watchlisted (§5). ETH forward-test leg unchanged per §16.4/§18.1. |

Kill-switches (both candidates): any week with signal exp_af ≤ −0.5 USDT/trade
over ≥10 trades pauses collection pending A1 review; no live orders at any
point (Testnet guard untouched).

## 8. Risks / limitations

1. Warmup hole: frozen Wyckoff config needs 205 daily bars; window start
   (2024-08→2025-03) is unlabeled, so F0 losers are characterized by quarterly
   price stats, not phase labels.
2. Concentration separator for NEAR derived from 2 losing observations;
   BOME shows concentration can be pure decay. Both proposals are framed as
   forward validations with pre-registered kill criteria.
3. Slippage stress is analytic and upper-bounds *quantity*, not *market
   depth* effects; tick-based models understate real alt-perp impact.
4. Multiple testing: 58 combos screened; survivors here already failed the
   BH-FDR gate in the original scan (q=1.0). W3/W4 forward windows are the
   actual out-of-sample test.
