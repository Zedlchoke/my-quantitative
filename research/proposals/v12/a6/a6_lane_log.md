# A6 lane evidence log (V12 D1, outcome-blind)

- Lane: `a6` — role A6, V12 blind mechanism proposal lane 2.
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/crypto/v12/d1-a6-proposals`
- Branch: `orca/v12d-a6-proposals`, HEAD verified `aca3f49e41aea976dcc300652bff835e798aeb2d`, porcelain empty at lane start (verified 2026-09-03).
- Outcome blindness: no returns, PnL, PF, Sharpe, ranking or backtest computed at any point; no V11 scored artifact, no `research/control/v11_run/*` (except the forbidden inventory), no `research/audits/*`, no other lane's directory, no `illiq_replication_brief`/`oilever_v2_brief`, nothing about S1 was read. Literature search was completed BEFORE proposals were finalized (all retrieval timestamps below precede the first `Write` of any proposal file).

## 1. Local (in-repo) sources read (all read-only, all allowed)

| # | Path | When (UTC, approx.) | Used for |
|---|------|---------------------|----------|
| L1 | `research/proposals/v12/blind_input_packet.md` | 2026-09-03 ~12:15Z | isolation contract, schema, floors, ineligible classes, required fields |
| L2 | `research/proposals/v12/blind_input_packet.json` | 2026-09-03 ~12:15Z | machine-checkable floors + `required_proposal_fields` |
| L3 | `research/control/v12_run/forbidden_family_inventory.json` | 2026-09-03 ~12:16Z | ancestry mapping (mechanism-level only) |
| L4 | `research/v12/data_contract.py` | 2026-09-03 ~12:16Z | frozen windows, 20-symbol set (BTC context-only), 15m bars, funding cadence, PIT/warmup helpers |
| L5 | `research/v12/load_validation.py` | 2026-09-03 ~12:16Z | fail-closed PIT rules (completed bars, funding span applicability) |
| L6 | `research/adapter_v10/protocol.py` | 2026-09-03 ~12:16Z | `StressSpec`, `CostModel`, `TargetBook`, `DEFAULT_WEIGHT_CAP_MAX=0.30`, strict-later fills |
| L7 | `research/adapter_v10/base.py` | 2026-09-03 ~12:17Z | `rebalance_cost_between` cost arithmetic, `LONG_PAYS_POSITIVE_RATE` funding accrual |
| L8 | `research/adapter_v10/benchmarks.py` | 2026-09-03 ~12:17Z | `flat_hard` gate, `benchmark_symbols_excluded` (BTC context-only) |
| L9 | `research/adapter_v10/stress.py` | 2026-09-03 ~12:17Z | six-cell stress surface, family-derived cell lists |
| L10 | `research/v11/cost_feasibility.py` | 2026-09-03 ~12:17Z | frozen floors (60 decisions/365d, median holding >=3d, base drag <=8%, stressed <=12%, symbol turnover share <=25%), schedule-only feasibility gate |

Rejected reads (not attempted): every path named in the packet's `must_not_read` list; the only `research/control/v11_run/` artifact consulted was the V12 forbidden inventory as instructed.

## 2. Web literature search — queries, retrieval UTC, verdicts

Search backend note: the WebSearch backend returned HTTP 429 rate-limit errors on several queries (retries recorded below); where a query failed it was retried later or replaced by a direct WebFetch of a primary/DOI URL. "ACCEPTED" = used as a claim-bearing anchor; "REJECTED" = consulted but not used, with reason.

| # | Query / URL | Retrieval UTC (approx.) | Verdict |
|---|-------------|-------------------------|---------|
| W1 | WebSearch: `Barber Huang Odean Schwarz "Attention-Induced Trading and Returns" Robinhood Journal of Finance` | 2026-09-03 12:18Z | backend 429; fallback summary only — superseded by W2 |
| W2 | WebSearch: `"Attention-Induced Trading and Returns" Barber Odean Schwarz Journal of Finance 2022 abstract` | 2026-09-03 ~12:22Z | ACCEPTED — confirms Barber, Huang, Odean, Schwarz (2022), *Journal of Finance* 77(6):3141–3190, DOI 10.1111/jofi.13183, SSRN abstract_id=3715077; claim: periods of intense attention-induced retail buying are followed by negative abnormal returns |
| W3 | WebFetch `https://doi.org/10.1111/jofi.13183` | 2026-09-03 ~12:19Z | DOI resolves (302 -> Wiley `onlinelibrary.wiley.com/doi/10.1111/jofi.13183`); Wiley page itself returns 403 to plain fetch (paywall) — DOI registration verified |
| W4 | WebFetch `https://www.nber.org/papers/w28351` | 2026-09-03 ~12:20Z | REJECTED — wrong paper (zoning/segregation, Shertzer-Twinam-Walsh). My recollection of the NBER number for the Barber et al. working paper was wrong; the published JF version (W2/W3) is used instead. Logged to keep the accept/reject trail honest |
| W5 | WebSearch: `Kelley Tetlock "How Wise Are Crowds" retail orders stock returns Journal of Finance trade size small trades` | 2026-09-03 ~12:24Z | ACCEPTED — Kelley & Tetlock (2013), *Journal of Finance* 68(3):1229–1265, DOI 10.1111/jofi.12028 (Wiley URL `onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12028`); claim: retail flow identified via order size/type; aggressive (market-order) retail flow produces temporary price pressure that subsequently reverses |
| W6 | WebSearch: `cryptocurrency retail investors attention returns trade size "number of trades" Binance empirical study` | 2026-09-03 ~12:25Z | ACCEPTED (two of the hits): Ozdamar et al. (2022), "Retail vs institutional investor attention in the cryptocurrency market", *Journal of International Financial Markets, Institutions and Money* vol 81 (RePEc: `ideas.repec.org/a/eee/intfin/v81y2022ics1042443122001469.html`) — retail vs institutional attention have distinct, separable return/liquidity effects in crypto (transferability). Smales (2021), "Investor Attention in Cryptocurrency Markets", SSRN abstract_id=3889923 — attention co-moves with returns contemporaneously (caveat for lagged cross-sectional transfer) |
| W7 | WebSearch: `"Crypto Wash Trading" Cong Li Tang Yang Management Science DOI inflation trade counts` | 2026-09-03 ~12:28Z | ACCEPTED (caveat source) — Cong, Li, Tang, Yang (2023), "Crypto Wash Trading", *Management Science* 69(11):6427–6454, DOI 10.1287/mnsc.2021.02709, SSRN abstract_id=3530220; claim: exchange-reported trade counts/volumes can be materially inflated on unregulated venues; measurement caveat for trade-count-based statistics |
| W8 | WebSearch: `Gatev Goetzmann Rouwenhorst "Pairs Trading: Performance of a Relative-Value Arbitration Rule" Review of Financial Studies 2006` | 2026-09-03 ~12:18Z | backend 429 + fallback; ACCEPTED after cross-check — Gatev, Goetzmann, Rouwenhorst (2006), *RFS* 19(3):797–827, DOI 10.1093/rfs/hhj020; claim: relative-value pair rule (divergence threshold, convergence exit) earned spreads robust to conservative execution assumptions |
| W9 | WebSearch: `pairs trading cryptocurrency cointegration relative value perpetual futures study` | 2026-09-03 ~12:26Z | MIXED — accepted Tadi & Kortchmeski (W10); REJECTED as anchors: Quantpedia overview (not primary), Frontiers 2026 deep-learning pairs paper (parameter-mining design, not a mechanism anchor), VSE copula WP (alternative design, not used), businessperspectives "long-short story" (journal quality not verified); noted as background only |
| W10 | WebFetch `https://arxiv.org/abs/2109.10662` | 2026-09-03 ~12:27Z | ACCEPTED — Tadi & Kortchmeski (2021), "Evaluation of Dynamic Cointegration-Based Pairs Trading Strategy in the Cryptocurrency Market", arXiv:2109.10662 (also *Studies in Economics and Finance*); claims: Engle-Granger/KSS cointegration gates usable in crypto; Ornstein-Uhlenbeck half-life of the spread informs the lookback window; realistic execution (delayed fills, quoted size) materially matters |
| W11 | WebFetch `https://doi.org/10.1080/14697680903124632` | 2026-09-03 ~12:27Z | DOI resolves (302 -> tandfonline) — Avellaneda & Lee (2010), "Statistical arbitrage in the US equities market", *Quantitative Finance* 10(7):761–782; claim: stat-arb spread mean reversion with Ornstein-Uhlenbeck calibration; thresholds tied to estimated reversion dynamics |
| W12 | WebFetch `https://doi.org/10.2307/1913236` | 2026-09-03 ~12:28Z | DOI resolves (302 -> JSTOR stable/1913236) — Engle & Granger (1987), "Co-Integration and Error Correction", *Econometrica* 55(2); claim: error-correction representation justifies estimating a long-run equilibrium and trading the stationary residual |
| W13 | WebFetch `https://raw.githubusercontent.com/binance/binance-spot-api-docs/master/rest-api.md` | 2026-09-03 ~12:29Z | ACCEPTED (official Binance API documentation) — kline payload field 8 (0-based) = "Number of trades"; quote asset volume field 7; `15m` is a supported interval. Futures parity: developers.binance.com USDS-M futures market-data catalog documents the same `count`/`numberOfTrades` field on `GET /fapi/v1/klines` |
| W14 | WebSearch: `Binance USDS-M futures API "Kline/Candlestick" response "Number of trades" field kline documentation` | 2026-09-03 ~12:29Z | ACCEPTED — official developers.binance.com USDS-M futures REST catalog page confirms kline `count` = number of trades |
| W15 | WebSearch: `Binance official documentation funding fee settlement time "fundingTime" every 8 hours 00:00 08:00 16:00 UTC perpetual` | 2026-09-03 ~12:31Z | ACCEPTED — official docs document `fundingTime` (int64) on `GET /fapi/v1/fundingRate`; baseline 8h settlement at 00:00/08:00/16:00 UTC with per-symbol deviations (4h on some symbols) — matches the packet's "mixed 8h/4h/1h cadences" data schema |
| W16 | WebFetch `https://developers.binance.com/docs/derivatives/.../Kline-Candlestick-Data` and `https://binance-docs.github.io/apidocs/futures/en/` | 2026-09-03 ~12:19–12:23Z | REJECTED as retrieval routes — JS-rendered / redirect stub, empty bodies; superseded by W13/W14 (raw GitHub markdown + catalog pages) |

Sources consulted and used (accepted): 10 distinct primary/official sources (W2 Barber et al. 2022; W5 Kelley-Tetlock 2013; W6 Ozdamar et al. 2022 + Smales 2021; W7 Cong et al. 2023; W8 Gatev et al. 2006; W10 Tadi-Kortchmeski 2021; W11 Avellaneda-Lee 2010; W12 Engle-Granger 1987; W13/W14 Binance kline docs; W15 Binance funding docs). Rejected routes/sources: W4 (wrong NBER paper), W9 non-primary items, W16 (render-failed routes), plus the 429-failed raw queries (W1).

## 3. Parameter mapping: which claim supports which parameter

### Proposal 1 — A6-P1-OSCOMP (order-size composition)

| Parameter | Value | Supporting claim |
|-----------|-------|------------------|
| Signal statistic | trailing 28d `sum(quote_volume)/sum(trade_count)` per symbol, cross-sectional ranks | Kelley-Tetlock (2013): trade size is the standard retail-flow classifier; Barber et al. (2022): attention-induced retail buying -> negative subsequent abnormal returns (expected sign) |
| Formation window 28d | weekly clock, 4-week holding | Barber et al. (2022): the underperformance following intense buying is concentrated over the following days-to-weeks (a 20-business-day horizon in the paper); 28d formation + 4-week holding brackets the documented horizon without retuning any forbidden family |
| Holding / rebalance | re-form every 4th Monday | floors: 13 discretionary decisions/365d <= 60; median intended holding 28d >= 3d by construction |
| Expected direction | long high-avg-ticket, short low-avg-ticket | Barber et al. (2022) (retail-heavy names underperform); Kelley-Tetlock (2013) (aggressive retail pressure reverses). Crypto transfer supported by Ozdamar et al. (2022) |
| Caveat — contemporaneous attention | sign must be tested at lag | Smales (2021): attention co-moves positively with contemporaneous crypto returns; the transfer to lagged returns is exactly what the falsification condition tests |
| Caveat — trade-count quality | statistics from Binance USD-M only | Cong et al. (2023): reported counts can be inflated on unregulated venues; Binance is the venue with the strongest integrity pressure; native kline `count` field documented (Binance API docs, W13/W14) |
| PIT fields | completed 15m bars only (`quote_volume`, `trades`), strictly before stamp | data_contract/load_validation PIT rules; Binance docs: both fields are native kline payloads (no derived/external data — not DATA-GATED) |
| Beta neutralisation | 90d trailing daily BTC beta, leg-gross split, no BTC leg | BTC is benchmark-context-only (data_contract `ILLIQ_BENCHMARK_SYMBOL`, packet); protocol `DEFAULT_WEIGHT_CAP_MAX=0.30` respected by 0.25-leg construction |

### Proposal 2 — A6-P2-RVX (cointegration error-correction relative value)

| Parameter | Value | Supporting claim |
|-----------|-------|------------------|
| Family | relative-value cointegration stat-arb | Engle-Granger (1987) error-correction representation; Gatev et al. (2006) relative-value rule with convergence exits |
| Pair universe | 8 pre-registered same-sector substitute pairs | Gatev et al. (2006): pairs are formed on prior economic/similarity grounds, not on in-sample performance; sector-cluster registration avoids pair mining |
| Activation gate | trailing 56d Engle-Granger residual ADF at 10%, hedge ratio in [0.25, 4] | Tadi-Kortchmeski (2021): EG-type cointegration gates are usable in crypto markets; sanity bound avoids degenerate hedge ratios |
| Formation window (anchor) | fixed 56d daily closes | Gatev et al. (2006) 12-month formation analog, compressed to 56d to match crypto's faster regime turnover (transfer caveat: crypto cointegration is less persistent than equity cointegration) |
| Formation window (neighbour) | max(28d, ceil(2 x OU half-life of spread)) | Avellaneda-Lee (2010): OU calibration of spread reversion; Tadi-Kortchmeski (2021): half-life informs the lookback window |
| Entry / exit thresholds | enter |z| >= 2.0, exit |z| <= 0.5 or 8w max | Gatev et al. (2006) 2-sigma divergence/convergence rule; Avellaneda-Lee (2010) threshold entry |
| Execution | weekly stamps only, strict-later fill, no intraweek actions | Tadi-Kortchmeski (2021): delayed, realistic execution is material; the packet's weekly clock freezes decisions to Mondays 00:00Z |
| Costs | native funding both legs, mixed cadences | Binance funding docs (W15); data_contract funding PIT rule; funding NEVER enters the signal (not a carry family) |
| Negative control | randomized pair->symbol permutation placebo | mechanism-destroying control in the packet's vocabulary: destroys the economic-substitute structure while preserving book shape, gross, thresholds, turnover schedule |

## 4. Ancestry screening notes (mechanism-level, vs forbidden inventory only)

For both proposals the screening input was ONLY `research/control/v12_run/forbidden_family_inventory.json` (class ids + forbidden text). No verdict/metric text from any scored artifact was read.

- `V10-M01-AGGRESSOR-ABSORPTION`: both signals are sign-agnostic (trade counts; price levels). No order-sign, taker-split or absorption statistic exists in either proposal. Clean.
- `V11-LOTTERY-MAX-SKEW`: neither proposal computes MAX, skewness, or any return-shape statistic. Clean.
- `V11-ILLIQ-AMIHUD` (reserved): proposal 1's statistic is `dollar_volume / trade_count` (ticket size). Amihud is `|return| / dollar_volume` (price impact per dollar). The two share no functional form; proposal 1 uses NO return input anywhere in its signal. Declared and defended in the proposal's not-a-rescue section; mechanism expectation (attention-driven overpricing decay) is not an illiquidity-premium claim.
- `V11-OILEVER-DELEV` (reserved): open interest is unused as a signal in both proposals. Clean.
- `V4-XSECT-MOM`: no past-return term in either signal statistic. Clean.
- `V6/V1-CARRY-FUNDING`: funding appears only as a held-cost (native settlements) in both; never as signal or sizing input. Clean.
- `V1-VOLCOMP` / volume-shock continuation: proposal 1's neighbour arm uses the first difference of average ticket size (a composition change), not a volume-level shock, and makes no continuation claim. Proposal 2 uses no volume at all. Clean.
- `WEEKLY-REVERSAL / MR-RESCUE`: proposal 2 is the only adjacency. Declared transparently: the rejected class is single-name reversal on own past returns; the RV statistic is a two-name cointegration residual with no own-return term, holding is state-dependent (threshold + max-holding), and the preregistered mechanism-destroying control (pair randomization) separates the two mechanism classes by construction. Flagged for A7-N to adjudicate; if adjudicated a rescue, the family dies — no fallback parameterization is offered.
- `DATA-GATED`: both proposals consume only staged fields (bars incl. `quote_volume`+`trades`, native funding settlements, tick sizes, and prices derivable from bars). No external or purchased data.

## 5. Assumptions recorded

1. All 19 non-BTC names in `REQUIRED_SYMBOLS` were listed on Binance USD-M before the window start (2025-08-22); newest (ACEUSDT) listed Dec 2024. Eligibility is still enforced per-stamp by the >=9-name fail-closed rule, so the proposal is safe even if a name gaps.
2. Pre-window bar history exists to serve 90d beta warmup at the first stamp (the data contract's warmup machinery evaluates exactly this); if it does not, the first served stamp simply moves later — the schedule rule is stated, not assumed.
3. The adapter's declared `CostModel` floors (taker bps + 1 adverse tick) apply as-is; my drag statements are worst-case turnover bounds in weight-units x the declared per-side rate, never measured outcomes.
4. Per family exactly 3 scored cells (anchor, neighbour, causal control) -> 6 of the 9-cell sprint budget; secondary/placebo diagnostics beyond the causal control are declared non-scored.
5. Environment note: this agent shell's default cwd was a different worktree directory (`d1-a8-proposals`), but the lane's worktree identity check was executed against the assigned path `/d1-a6-proposals` and passed exactly (pwd, HEAD, branch, empty porcelain).
