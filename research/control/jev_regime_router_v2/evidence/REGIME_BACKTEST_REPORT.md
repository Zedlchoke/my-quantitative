# JRV2 — REGIME BACKTEST REPORT (18 frozen scored cells, after costs)

Run: one atomic process 2026-09-23T00:25Z under heavy lock, code frozen at
`b1b1494a` BEFORE any outcome; owner GO `GO JEV REGIME V2 SCORED BACKTEST`
(Scored_GO authority sha `a7794ac8…`). Cached decisions only — zero provider
calls. Reproduction: independent rerun, **54/54 tier files byte-identical;
summary differs only in wall-clock timestamps (ALL_MATCH)**. Engine identity +
fold reconciliation asserted OK on every cell x arm x tier. Trial accounting
18/18 observed. Cost tiers 1.0x/1.5x/2.0x per frozen contract.

## Base-tier (1.0x) results — net PnL after costs, equity 100,000

### BTC_H1 (buy-hold ref −132)

| Arm | Net | Trades | PF | Sharpe | MaxDD | Folds (net) |
|---|---|---|---|---|---|---|
| ALWAYS_ON_MEAN_REVERSION | **−53,132** | 391 | 0.59 | −1.31 | −53.9% | all < 0 |
| RANDOM_MATCHED_ROUTER (median seed) | −74,277 | 820 | 0.49 | −2.05 | −74.6% | — |
| DETERMINISTIC_PLUS_JEV_CONFIRMATION | −81,761 | 760 | 0.32 | −3.16 | −83.1% | — |
| JEV_ONLY_ROUTER | −88,140 | 978 | 0.38 | −3.53 | −89.0% | −40,997 / −37,419 / −4,923 / −4,802 |
| ALWAYS_ON_TREND | −91,535 | 1,386 | 0.37 | −4.11 | −92.2% | — |
| DETERMINISTIC_REGIME_ROUTER | −96,654 | 1,793 | 0.34 | −4.41 | −96.9% | — |

### BTC_H4 (buy-hold ref −482)

| Arm | Net | Trades | PF | Sharpe | MaxDD |
|---|---|---|---|---|---|
| ALWAYS_ON_MEAN_REVERSION | **−53,901** | 374 | 0.58 | −0.69 | −54.5% |
| DETERMINISTIC_PLUS_JEV_CONFIRMATION | −77,672 | 859 | 0.46 | −1.33 | −77.7% |
| RANDOM_MATCHED_ROUTER | −83,957 | 992 | 0.41 | −1.35 | −84.0% |
| JEV_ONLY_ROUTER | −85,274 | 1,060 | 0.44 | −1.60 | −85.3% |
| DETERMINISTIC_REGIME_ROUTER | −88,145 | 1,175 | 0.41 | −1.62 | −89.0% |
| ALWAYS_ON_TREND | −89,499 | 1,269 | 0.40 | −1.98 | −90.3% |

### SPY_D1 (buy-hold ref +8,405)

| Arm | Net | Trades | PF | Sharpe | MaxDD | Conc |
|---|---|---|---|---|---|---|
| ALWAYS_ON_TREND | **+19,813** | 143 | 1.14 | 0.23 | −28.9% | 0.69 (>0.50 kill) |
| ALWAYS_ON_MEAN_REVERSION | −924 | 18 | 0.98 | 0.03 | −25.0% | 0.81 |
| RANDOM_MATCHED_ROUTER | −30,015 | 275 | 0.72 | −0.57 | −31.6% | 1.0 |
| DETERMINISTIC_REGIME_ROUTER | −31,877 | 213 | 0.63 | −0.68 | −33.1% | 1.0 |
| DETERMINISTIC_PLUS_JEV_CONFIRMATION | −32,384 | 194 | 0.59 | −0.72 | −33.5% | 1.0 |
| JEV_ONLY_ROUTER | −51,623 | 343 | 0.59 | −1.02 | −51.9% | 1.0; folds −25,488/+4,985/−14,810/−16,310 |

## The seven questions

1. **Jev vs always-on after costs?** NO — JEV_ONLY loses to ALWAYS_ON_MR on all
   three cells (margins −35,008 / −31,373 / −50,700) and to ALWAYS_ON_TREND on
   SPY (−71,436).
2. **Jev vs deterministic router?** Marginal on BTC (+8,514 / +2,871) but both
   deeply negative; on SPY Jev is far WORSE (−19,747). "Less bad" among losers
   is not incremental value.
3. **Jev vs random matched?** NO — loses on all three cells (−13,863 / −1,317 /
   −21,608). DISCLOSED WEAKNESS: the random null was flagged `null_invalid`
   (Q-11 movement check) on all cells, so this comparison is weakened — but
   conclusions 1 and 2 do not depend on the null.
4. **Trades Jev blocked (skipped-trade)?** Skipped-trade fractions ≈ −7.4%
   (H1) / +1.6% (H4) / −5.3% (SPY) — blocking was not systematically harmful
   or helpful; the damage comes from what it DID trade, not what it skipped.
5. **Regime intelligence vs trading less?** Trading less helped (JEV trades
   978 vs DETERMINISTIC 1,793 on H1 yet loses only slightly less); the info
   content itself added nothing — SPY occupancy UPTREND 70% yet JEV routed
   TREND_LONG lost −51.6k while ALWAYS_ON_TREND made +19.8k: the switching
   (34 switches + fold force-flat churn at 20 bps/fill) destroyed the trend
   capture. Switching costs are decisive: every arm degrades monotonically
   at 1.5x/2.0x tiers (JEV_ONLY H1: −88.1k → −93.4k → −96.3k).
6. **Stable across folds/assets?** Consistently NEGATIVE — JEV_ONLY fold nets
   are < 0 in 11/12 cell-folds (only SPY fold-2 positive). The negative
   verdict is the stable finding; no single-fold dependency anywhere.
7. **Switching cost attrition?** Yes — gross edges (where any) are consumed by
   12 bps/side BTC and 10 bps/fill SPY at the routers' turnover; CONFIRM arm
   (fewer switches) beats DETERMINISTIC on BTC (+14.9k/+10.5k) precisely by
   trading less, and matches it on SPY (−507).

Confirm-arm diagnostics: Jev agreed with the deterministic law only 39.9%
(H1) / 62.0% (H4) / 56.1% (SPY) — the two classifiers see different markets;
neither routing of them was profitable.

## Strategy × Jev-regime matrix

Diagnostic ONLY (frozen mapping untouched): `scored_summary.json` per-arm
occupancy/timeline blocks. No remapping was performed or proposed in-cycle.

## Verdict basis (vocabulary: plan §evaluation_contract)

`JEV_INCREMENTAL_VALUE_SUPPORTED` requires: net-positive after costs; beats
always-on, deterministic, random; not single-fold/asset dependent; reproduction
match; clean A7. **Every precondition fails on every cell (net-negative
everywhere for JEV_ONLY; loses to always-on and random everywhere).** The
honest verdict is `JEV_NO_INCREMENTAL_VALUE` — uniform across cells and folds.
The single positive arm of the whole run (SPY ALWAYS_ON_TREND +19,813) is a
BASELINE, not a Jev claim, and carries concentration 0.69 > 0.50 (kill bar) —
it is reported, not promoted (and this cycle has no promotion authority).

## Five-year-old summary

Jev nhìn thời巨星 tiết giờ khá ổn (không còn "không rõ" 100% như V1). Nhưng
khi ta giao tiền theo nó: tài khoản XẤU hơn so với bậc thang đơn giản nhất
(luôn chạy một chiến lược) và thua cả xúc xắc bắt chước nó. Nó không thông
hơn luật đơn giản — và chính lúc nó "đúng hướng 70%" trên SPY, việc liên
tribal đổi ý + phí chặt ở mỗi lần đổi khiến nó mất trắng phần xu hướng mà
chiến lược luôn-bật bắt được. Không đáng mở prospective-shadow cho JEV router
hiện tại.
