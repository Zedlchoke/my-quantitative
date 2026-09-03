# A8 lane evidence log — V12 blind mechanism proposals

Lane: A8 (lane 3), role outcome-blind proposer.
Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/crypto/v12/d1-a8-proposals`
Branch: `orca/v12d-a8-proposals`, HEAD verified `aca3f49e41aea976dcc300652bff835e798aeb2d`, porcelain empty at lane start.

Session UTC anchor: lane started ~2026-09-03T11:55Z; final write ~2026-09-03T12:35Z
(clock verified by HTTP `Date: Thu, 03 Sep 2026 12:31:08 GMT` header mid-session and
`date -u` = `2026-09-03T12:34:42Z` before writing deliverables). Individual retrieval
stamps below are recorded to the minute within this session window.

## 1. Isolation posture

Read (allowed set only):

* `research/proposals/v12/blind_input_packet.md` + `.json` (mandatory first read).
* `research/v12/data_contract.py`, `research/v12/load_validation.py` (schema, PIT rules,
  warmup conventions, Monday-00:00Z clock helpers).
* `research/adapter_v10/protocol.py`, `base.py`, `facade.py`, `benchmarks.py`, `stress.py`
  (interfaces only: `StressSpec`, `CostModel`, `TargetBook`, `FillRecord` strict-later
  semantics, `LONG_PAYS_POSITIVE_RATE`, weight cap 0.30, stress cells, flat-hard gate).
* `research/v11/cost_feasibility.py` (schedule-only feasibility gate + frozen floor table).
* `research/control/v12_run/forbidden_family_inventory.json` (mechanism-level only).

Not read (attested): `research/control/v11_run/*` except the forbidden inventory;
`research/audits/*`; `research/proposals/v12/illiq_replication_brief.*`;
`research/proposals/v12/oilever_v2_brief.*`; other lanes' directories; anything about S1;
any V11 metrics/verdict artifacts. No returns, PnL, PF, Sharpe, rankings or backtests were
computed; all schedule-level numbers in the proposals are design arithmetic (decision
counts, span lengths, weight algebra), the same class the schedule-only feasibility gate
consumes.

## 2. Literature queries (query string, retrieval UTC, verdict, reason)

Search backend: WebSearch (rate-limited; several 429 retries logged implicitly — only the
queries that produced retrievable content are listed as accepted; the repeated identical
retries are collapsed).

| # | Query | Retrieval UTC (approx) | Verdict | Use / reason |
|---|-------|------------------------|---------|--------------|
| 1 | `Frazzini Pedersen "Betting Against Beta" Journal of Financial Economics 2014 DOI` | 2026-09-03 ~12:07Z | ACCEPT | Anchor claim for a8_prop1. Verified: Frazzini & Pedersen (2014), "Betting Against Beta", *Journal of Financial Economics* 111(1), 1-25, DOI `10.1016/j.jfineco.2013.10.005` (ScienceDirect page retrieved). Claim used: leverage-/margin-constrained investors overweight high-beta assets, depressing their risk-adjusted returns; a long-low-beta / short-high-beta factor earns positive risk-adjusted returns across asset classes including futures. Parameter mapping: 90d trailing beta warmup mirrors the frozen `beta_90d` warmup declared in `data_contract.py`; weekly slow-covariance formation -> low turnover. |
| 2 | `Hvidkjaer "small trades and the cross-section of stock returns" ... DOI` | 2026-09-03 ~12:10Z | ACCEPT (with venue correction) | Anchor claim for a8_prop2. Verified: Hvidkjaer (2008), "Small Trades and the Cross-Section of Stock Returns", *Review of Financial Studies* 21(3), 1123-1151, DOI `10.1093/rfs/hhn049`. NOTE: earlier drafts cite JFQA; the verified venue is RFS — citation corrected in the proposal. Claim used: small-trade order imbalance predicts subsequent negative returns (uninformed retail flow is contrarian-predictive). |
| 3 | `Ang Chen Xing "Downside Risk" Review of Financial Studies 2006 DOI` | 2026-09-03 ~12:14Z | ACCEPT | Neighbour-arm claim for a8_prop1. Verified: Ang, Chen & Xing (2006), "Downside Risk", *RFS* 19(4), 1191-1239, DOI `10.1093/rfs/hhj035`. Claim used: systematic downside covariance carries a distinct premium -> downside-beta sort is the theoretically justified neighbour of the beta sort. |
| 4 | `cryptocurrency beta anomaly "betting against beta" OR "low beta" cross-section...` | 2026-09-03 ~12:12Z | PARTIAL / CAVEAT-ONLY | Search backend rate-limited (429) on every retry; no primary source retrieved. The backend's unsourced fallback narrative reported that the beta anomaly's transfer to crypto is CONTESTED (some samples find a positive risk-return relation). Recorded as an honest transfer caveat inside a8_prop1 (not as evidence FOR the mechanism). Follow-up dedicated searches below. |
| 5 | `Liu Tsyvinski Wu "Common Risk Factors in Cryptocurrency" ... DOI` | 2026-09-03 ~12:20Z | ACCEPT (DOI pattern-inferred, flagged) | Caveat/ancestry source for a8_prop1. Verified citation: Liu, Tsyvinski & Wu (2022), "Common Risk Factors in Cryptocurrency", *Journal of Finance* 77(2), 1133-1177 (JSTOR page retrieved); DOI `10.1111/jofi.13121` inferred from the Wiley pattern and NOT independently resolved — flagged in the log and in the proposal as inferred. Claim used: the documented priced crypto factors are market, size, momentum; a beta-sorted spread is NOT one of them (so prop1 is not a duplicate factor), and beta sorts may correlate with size (caveat). |
| 6 | `retail investors cryptocurrency returns small trades participation evidence paper` | 2026-09-03 ~12:24Z | ACCEPT | Crypto-transfer caveat sources for a8_prop2. Retrieved: Kogan, Kogan, Makarov, Marinova & Szydlowski (2023), "Are Cryptos Different? Evidence from Retail Trading", NBER WP 31317 (working paper — marked as such, used ONLY as a transfer caveat, not as an anchor claim); JPMorgan Chase Institute "Crypto investor waves since 2017" (industry report — caveat only). |
| 7 | `Barclay Warner "stealth trading and volatility" ... 1993 DOI` | 2026-09-03 ~12:28Z | ACCEPT | Neighbour-arm claim for a8_prop2. Verified: Barclay & Warner (1993), "Stealth trading and volatility: Which trades move prices?", *Journal of Financial Economics* 34(3), 281-305, DOI `10.1016/0304-405X(93)90029-B`. Claim used: informed traders camouflage in medium-size trades; ticket-size mix separates informed from uninformed participation -> large/medium-ticket share arm is the theoretically justified neighbour. |
| 8 | Venue docs, `developers.binance.com .../Kline-Candlestick-Data` + `.../Get-Funding-Rate-History` (WebFetch) | 2026-09-03 ~12:29Z | REJECT (retrieval) | SPA pages returned empty content to the fetcher. |
| 9 | Venue docs, `binance-docs.github.io/apidocs/futures/en/` (curl) | 2026-09-03 12:31:08Z (HTTP Date header) | REJECT (retrieval) | Page is a 325-byte meta-refresh redirect to `developers.binance.com/docs/derivatives` (SPA). |
| 10 | Official `binance/binance-api-postman` collection, `Binance Derivatives Trading USDS Futures API.json` (raw.githubusercontent.com, official Binance GitHub org) | 2026-09-03 ~12:32Z | ACCEPT (partial) | Confirms official endpoint existence and paths for the fields the packet already freezes: `/fapi/v1/klines` (Kline/Candlestick Data), `/fapi/v1/fundingRate` + `/fapi/v1/fundingInfo` (funding history/info), `/fapi/v1/openInterest` + `/futures/data/openInterestHist` (OI). The collection carries no example-response bodies, so field-level quotes were NOT retrievable from it; field content is taken from the frozen packet/data-contract declaration instead. |
| 11 | `academy.binance.com/en/articles/what-are-perpetual-futures-contracts` (WebFetch, then redirect to `www.binance.com/en/academy/...`) | 2026-09-03 ~12:33Z | REJECT (retrieval) | 301 redirect to www.binance.com; target returned empty content to the fetcher (bot-blocked). The funding-mechanics claim used in the proposals (long pays positive rate; 8h baseline cadence with 4h/1h exceptions) is therefore cited from the LOCAL frozen sources only: `data_contract.py` (native `fundingTime` settlements, 4h phases documented, PIT rule) and the adapter's `LONG_PAYS_POSITIVE_RATE` convention. No external venue claim is relied on that was not retrievable. |

Network availability statement: network was PARTIALLY available. WebSearch worked
(with heavy 429 rate-limiting). binance.com / developers.binance.com rendered pages were
bot-blocked (SPA); raw.githubusercontent.com and publisher/SSRN pages were reachable.
No claim in either proposal rests on a source that failed retrieval, except where
explicitly marked "caveat, unsourced fallback narrative" (item 4) which is used against
the mechanism, not for it.

## 3. Rejected mechanism candidates (pre-registration hygiene)

| Candidate | Why rejected before proposal |
|-----------|------------------------------|
| Funding-rate conditioning / funding mean-reversion books | Mechanism-adjacent to forbidden `V6/V1-CARRY-FUNDING` (funding carry/crowding rescues). Excluded on sight. |
| OI-level, OI/volume, OI-concentration signals | `V11-OILEVER-DELEV` family is RESERVED (OILEV-V2 preregistered identity); any OI-shaped book risks being judged an OI variant. Both proposals use zero OI fields. |
| Idiosyncratic-vol / low-vol anomaly | Direct sibling of `V11-LOTTERY-MAX-SKEW` (lottery demand is proxied by idio-vol). Excluded. A8 keeps only SYSTEMATIC covariance (beta to BTC), which the inventory does not cover and which FP2014 anchors in a different variable class. |
| Ordinary momentum / 52-week-high / breakout-range | Forbidden (`V4-XSECT-MOM`, `V1-VOLCOMP`). Excluded on sight. |
| Weekly reversal / short-term reversal books | Forbidden (`WEEKLY-REVERSAL / MR-RESCUE`). Excluded on sight. |
| Aggressor/taker-flow or order-flow-imbalance signals | Forbidden (`V10-M01-AGGRESSOR-ABSORPTION`). a8_prop2 deliberately uses only DIRECTION-LESS bar aggregates (quote volume, trade count). |
| Amihud-style impact ratios (`|r|`/dollar-volume) | Reserved (`V11-ILLIQ-AMIHUD`). a8_prop2's ticket mix = dollar-volume / trade count: NO price term appears in the signal, so no price-impact ratio is formed. Distinction argued explicitly in the proposal. |
| Session-of-day / weekend seasonality books | Decision clock is weekly Monday 00:00Z; session timing cannot be expressed without violating the clock. Excluded. |
| Static size / listing-age tilt | 19-name universe spans a narrow size range; book is quasi-static and proxies an un-hedgeable alt beta. Weak mechanism; excluded. |
| Volatility-managed timing overlay (Moreira-Muir style) | No cross-sectional counterparty; collapses into a market-timing bet on BTC. Excluded. |

## 4. Parameter mapping rationale (shared design skeleton)

* Decision clock: Monday 00:00:00Z weekly — directly from the packet and
  `ceil_to_monday_00z_ns` in `data_contract.py`; 52 stamps/yr satisfies the frozen
  `<=60` decisions/365d floor by schedule arithmetic (force-flat terminal row counted
  separately, per `cost_feasibility.KIND_FORCED_FLAT`).
* Warmup 90d: matches `beta_90d` binding warmup already declared in `data_contract.py`
  (`warmup_days_required.binding_max = 90`), so both proposals inherit a warmup the data
  contract asserts is satisfiable from pre-window history.
* Books: extreme-quintile legs over 19 tradable names (BTCUSDT context-only per
  `ILLIQ_BENCHMARK_SYMBOL` exclusion convention) -> 4 names per leg -> per-name weight
  0.25 <= 0.30 by construction, with a final pure-rescaling clamp `w -> w * min(1,
  0.30/max|w|)` that only shrinks (never a post-score renormalisation; it is part of the
  deterministic target-book constructor, applied BEFORE the stamp is emitted).
* BTC-beta neutralisation: leg-scale ratio c_L/c_S = mean|short-leg beta| : mean|long-leg
  beta| s.t. sum(w*beta) = 0; beta used ONLY as a risk constraint (prop2) and as the
  signal (prop1), estimated on completed bars strictly before the stamp.
* Turnover guards (both proposals): quintile-band hysteresis (enter at extreme quintile,
  exit only when leaving the adjacent band), max 2 replacements per leg per stamp, no
  re-entry within 1 stamp of exit, per-symbol hard cap of 6 exits/365d. Under a weekly
  clock every completed span is a multiple of 7d >= 7d, so the `>=3d` median-holding
  floor holds by construction. The per-symbol turnover-share and cost-drag floors are
  verified by the schedule-only feasibility gate on the emitted target books; the
  constructor's churn caps exist so no single symbol can plausibly dominate turnover.
* Costs: plugin declares `CostModel` with the repo's frozen taker-fee floor and per-symbol
  tick sizes (1e-7..1e-2 declared in the packet); transition cost via the adapter's
  `rebalance_cost_between`; funding accrual native, `LONG_PAYS_POSITIVE_RATE`, settlements
  strictly inside `(ts_opened, ts_closed]` (PIT rule from `load_validation.py`); stress
  cells `fee_slippage_x1_5`, `plus_2_ticks`, `plus_1_event_delay` per `stress.py`.
* Fills: one declared execution lag — target emitted at stamp T, filled at the first
  strict-later 15m event (`FillStatusVocabulary.APPLIED` / `NO_EVENT_AT_BOUNDARY`
  semantics); stress adds +1 event delay.
* Controls: every family = anchor + theoretically-justified neighbour + causal negative
  control (sign-flipped arm as the primary causal control on the identical data
  pipeline; symbol-permutation placebo as secondary, book-shape-preserving). Controls
  share the anchor's cost stack so a control "win" after fees falsifies the anchor.

## 5. Deliverables produced by this lane

* `research/proposals/v12/a8/a8_prop1.json` / `a8_prop1.md` — BAB-PERP (systematic
  beta-mispricing family; anchor FP2014, neighbour ACX2006 downside-beta).
* `research/proposals/v12/a8/a8_prop2.json` / `a8_prop2.md` — TICKET-MIX CONTRARIAN
  (participation-mix family; anchor Hvidkjaer 2008, neighbour Barclay-Warner 1993).
* This log.
