# V11 A5 proposal 1 — V11-A5-ILLIQ-PREMIUM (cross-sectional illiquidity premium on USD-M perpetuals)

Producer: D1-A5 (outcome-blind; no candidate returns, PnL, PF, Sharpe or ranking accessed for any V11 mechanism). Literature search completed BEFORE this freeze; see `a5_search_log.json`. Bootstrap HEAD `0684914b7bf64a5b9b8eeaa82529a2d11a8a251d`, branch `orca/v11d-a5-proposals`.

## 1. Primary-source citations with claim-to-test mapping

| id | source (verified identity) | exact claim used | claim-to-test mapping in this repo |
|---|---|---|---|
| AMH02 | Amihud, Y. (2002), "Illiquidity and stock returns: cross-section and time-series effects", *Journal of Financial Markets* 5(1), 31–56 | Expected returns rise cross-sectionally with the price-impact ratio ILLIQ = mean(\|r\|/dollar volume); illiquid assets carry a return premium paid by immediacy-demanding flow | Compute ILLIQ per symbol from COMPLETED 15m bars (sum \|15m log return\| / sum dollar volume, aggregated to daily UTC closes, 28d trailing window); test whether the high-ILLIQ-minus-low-ILLIQ weekly book earns a positive net spread in the frozen snapshot |
| BMRT21 | Brauneis, A., Mestel, R., Riordan, R., Theissen, E. (2021), "How to measure the liquidity of cryptocurrency markets?", *Journal of Banking & Finance* vol. 124, art. 106107 (PII S0378426620303022) | Low-frequency, transaction-based liquidity proxies (Amihud-type) adequately capture actual high-frequency crypto liquidity | Validity pillar for computing the illiquidity characteristic from 15m bars instead of order-book snapshots (which the frozen staged snapshot does not contain); the repo test is whether the bar-computed measure produces a STABLE cross-sectional ranking (rank persistence diagnostic) |
| LEI22 | Leirvik, T. (2022), "Cryptocurrency returns and the volatility of liquidity", *Finance Research Letters* 44, art. 102031, DOI 10.1016/j.frl.2021.102031 | Cryptocurrency returns are cross-sectionally related to liquidity (dynamics) | Prior that the liquidity-return link exists in crypto specifically; repo test = sign of the anchor book spread (neighbour direction: liquidity-dynamics variant noted as robustness, not a scored arm) |
| LOUSHU | Lou, X. (U. Delaware), Shu, T. (U. Georgia), "Why is the Amihud (2002) illiquidity measure priced?", SSRN 2291942 / AFA 2015 (published variant "Price impact or trading volume: why is the Amihud (2002) measure priced?") | CONFOUND: in equities the Amihud spread is largely explained by its short-horizon reversal (price-impact-decomposition) component | NOT mechanism evidence. Mandates the predeclared reversal-orthogonality diagnostic (section 7) and sharpens the causal negative control; the mechanism claim dies if the anchor spread is fully absorbed by lagged-reversal exposure |
| BNDS4 | Binance USD-M futures market data endpoints — frozen packet source S4 (klines with volume, OI, mark price, funding history) | Official semantics for completed 15m bars incl. volume, used for PIT feature construction | Data-contract pillar: all features are computable from the frozen staged snapshot with no new external data |

Commentary/vendor pages (alphaarchitect, bitsgap), a USU graduate report, and preprints (Moreno Muñoz & de la O González 2022 UC3M) were logged as leads only, never mechanism evidence (see search log).

## 2. Economic mechanism + expected counterparty

Holders of illiquid assets are compensated for providing immediacy and bearing holding-period illiquidity risk: impatient traders cross spreads and move price against themselves, transferring a premium to patient suppliers of capacity (Amihud 2002 mechanism). In a Binance USD-M perpetual panel, high-Amihud coins are those where a given notional flow moves price a lot relative to traded volume; a patient book that holds these coins and shorts the liquid majors is the counterparty to immediacy-demanding flow (retail takers, forced liquidators, index/funding-flow executors). Expected counterparty: impatient, liquidity-consuming traders in the illiquid leg who systematically pay for immediacy, plus sellers of liquid majors who pay little premium. This is a capacity-provision premium, NOT a bet on past price direction and NOT funding-rate selection.

## 3. Required observable fields + PIT clock

- Fields (all in frozen staged snapshot): completed 15m bars (close, quote/base volume) per symbol; BTC perp bars for the beta anchor; mark price for valuation fills; funding settlements for pass-through cost accounting only.
- Transformation: completed 15m bars → daily UTC close aggregates; ILLIQ_i(t) = sum over trailing 28d of |15m log return| divided by same-window sum of dollar volume; winsorised at the 1%/99% cross-sectional percentiles each formation date.
- PIT clock: features computed ONLY from bars with close timestamp strictly before the decision instant; ONE declared execution lag — orders execute at the first fill price strictly after the decision instant (no same-bar fill); rank inputs are the daily aggregates of the last completed UTC day strictly before the decision.

## 4. Universe + benchmark role

- Universe: all USD-M perpetual symbols in the frozen staged snapshot passing a PIT tradability floor — at least 60 completed days of history and median daily dollar volume above the cross-sectional median of the staged universe on the formation date (keeps short legs executable and costs sane; the premium is then harvested RELATIVE within the tradable pool). Listing/survivorship handled by the repo's PIT snapshot (delisted symbols stay in history).
- Benchmark role: BTC perp is the market/beta anchor (context-only, per `GenericStrategyBase.benchmark_context_symbols`); the family's scored object is the dollar-neutral long-minus-short spread, so the benchmark enters only as (a) the beta-neutralisation target and (b) A7-N orthogonality reference, never as a scored long position.

## 5. Schedule, holding period, turnover rationale

- Schedule: weekly decision grid (Monday 00:00 UTC on the completed-bar clock) → 52 discretionary decisions/365d ≤ 60 floor.
- Holding: 7d intended holding; minimum completed span is one week by construction → median intended holding ≥ 7d ≥ 3d floor.
- Turnover rationale: quintile-bucket book with ENTRY/EXIT BUFFER BANDS (a symbol enters an extreme bucket only if its rank is strictly inside the bucket's inner band; it is held until its rank exits the bucket's outer band). Expected one-way turnover ≈ 0.30 of book per decision; even a full 100% bucket swap costs ≤ 2.0 × ~6 bps/side ≈ 12 bps/week ≈ 6.2%/yr of gross at the frozen cost floor, inside the ≤8% base / ≤12% stressed floors; buffers reduce this materially. Equal-weight buckets with a per-symbol weight cap 1/(2·N_bucket) spread turnover so no symbol exceeds 25% of one-way turnover (pre-declared A3 pre-check).

## 6. Target construction + risk neutralisation

- Target: equal-weight LONG top-ILLIQ-quintile (illiquid leg) minus equal-weight SHORT bottom-ILLIQ-quintile (liquid leg); dollar-neutral book (gross ≈ 2.0 in weight units).
- Risk neutralisation: per-leg BTC-beta adjustment using the repo's rolling 90d daily beta convention (weights scaled so long-leg and short-leg betas to BTC offset); no residual-return construction is used for SORTING (sorting characteristic is the liquidity level itself) — this keeps the mechanism distinct from the reserved residual-risk seed, which sorts ON residual risk.

## 7. Arms (anchor + theoretically-justified neighbour + causal negative control)

- ANCHOR `ILLIQ-AMIHUD-28D-W`: high-minus-low Amihud ILLIQ bucket book, 28d formation, weekly rebalance, buffered.
- NEIGHBOUR `ILLIQ-ROLLSPREAD-28D-W`: same mechanism, alternative theoretically-derived illiquidity estimate — Roll (1984) implied effective spread from negative first-order serial covariance of intraday 15m price changes over the trailing 28d, aggregated to daily. Justification: it prices the SAME immediacy-provision mechanism through an orthogonal microstructure estimator; a spread that survives only in one estimator is estimator noise, not premium.
- CAUSAL NEGATIVE CONTROL `ILLIQ-AMIHUD-28D-W-INV`: sign-INVERTED anchor (long liquid / short illiquid). Falsification: any positive after-cost spread on the inverted book destroys the mechanism claim.
- Predeclared diagnostic (not a scored arm): reversal-orthogonality — regress anchor-book membership on lagged 1d and 7d return ranks (Lou–Shu confound); the A7-N lane checks the spread is not fully absorbed by lagged-reversal exposure (banned-family guard).

## 8. Expected sign + falsification conditions

- Expected sign: anchor `ILLIQ-AMIHUD-28D-W` net spread > 0 after native funding and adapter costs; `ILLIQ-ROLLSPREAD-28D-W` same sign; `ILLIQ-AMIHUD-28D-W-INV` ≤ 0.
- Falsified if ANY of: (i) inverted control earns a positive after-cost spread; (ii) A3 schedule-only cost gate FAIL/UNAVAILABLE; (iii) spread concentrated in one fold or one symbol (Stage-A concentration gates); (iv) reversal-orthogonality diagnostic shows the anchor spread collapses after lagged-reversal control (then the correct verdict is "Amihud-reversal artifact", family rejected); (v) roll-spread neighbour sign flips while anchor "works" (estimator-inconsistent → reject).

## 9. Funding / cost treatment

- Funding: native settlements accrued while held under `LONG_PAYS_POSITIVE_RATE` (long leg pays positive rate, short leg receives); funding is pure cost pass-through and is NOT a signal, NOT a filter, NOT neutralised as a feature. No funding-based sorting anywhere in the family (no carry contamination).
- Costs: adapter `rebalance_cost_between` (taker fee floor + adverse tick slippage per side) at baseline and fee×1.5/+2-tick stressed cells via the A3 gate; illiquid-leg fills declared at strictly-later mark-derived fill prices; fail-closed on missing prices.

## 10. Ancestry / proximity + orthogonality argument

- V10 M01 (REJECTED): M01 was high-turnover aggressor-FLOW absorption from intraday trade prints (6916 positions/3 folds, ~100% cost-driven loss). This family shares NO mechanism (capacity provision vs flow absorption), NO signal object (bar-level volume-price ratio vs aggressor prints), NO cadence (weekly vs intraday); expected orthogonality ρ ≈ 0, verified by A7-N against the M01 published series.
- Banned families: not trend/momentum (sorts on a liquidity LEVEL, not past returns); not reversal (sorting characteristic is orthogonal to price direction BY CONSTRUCTION and the Lou–Shu-motivated reversal-orthogonality diagnostic is predeclared — if the premium is reversal in disguise, the family is REJECTED, not rescued); not volume-shock continuation (volume appears only as the DENOMINATOR of a slow level characteristic; no shock event, no continuation bet); not weekly reversal (no return signal at all); not funding carry (funding is pass-through only); not crowding rescue (no prior rejected family is being revived — see 12).
- Reserved seeds: SEED-DEFENSIVE-RESIDUAL-RISK sorts on residual VOLATILITY of returns; SEED-LOTTERY-MAX-SKEW sorts on residual MAX/SKEW of returns. This family sorts on a LIQUIDITY characteristic (|r|/volume) — a microstructure object, not a return-distribution moment. Known correlation (illiquid coins are volatile and lottery-like) is handled by A7-N: predeclared rank-orthogonality ρ vs both seeds must be below the frozen orthogonality gate, and residual-vol/MAX ranks enter the diagnostic regression as controls. If the "illiquidity premium" is indistinguishable from the low-vol or MAX premium in the snapshot, the family dies at A7-N — which is the honest test, not a rescue.

## 11. Data readiness + implementation estimate

- Readiness: 15m bars with volume are the base staged product (S4 semantics); BTC bars and funding settlements present; mark price for fills; OI NOT required. No new external data. Coverage risk: volume fields for older symbols — fail-closed (missing input ⇒ A3 UNAVAILABLE_FAIL_CLOSED, never synthesized).
- Estimate: one plugin on `GenericStrategyBase` (identity, universe, schedule, targets, fills, marks, settlements) + feature module for ILLIQ/Roll-spread ≈ 1.5–2 engineering days incl. PIT no-leak fixtures; A3 artifacts straightforward from the schedule.

## 12. Why it is not a rescue of a previously rejected family

M01's loss was ~100% transaction costs at ~zero gross edge; nothing in this family reuses M01's flow signals or intraday cadence (section 10) — the only shared word is "liquidity", and M01 absorbed FLOW while this family EARNS the standing illiquidity premium at weekly cadence, where the A3 schedule gate is the very mechanism that killed M01 and must be passed BEFORE scoring. No V1–V10 rejected family in the provided lessons used an Amihud-type characteristic. The banned/reserved lists are all return-shape or flow-shape families; a microstructure characteristic-premium family is a genuinely new mechanism class for this sprint, and its rejection conditions are predeclared to catch the two known ways it could be a disguised old family (reversal artifact; low-vol/MAX proxy).
