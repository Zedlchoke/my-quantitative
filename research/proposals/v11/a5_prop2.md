# V11 A5 proposal 2 — V11-A5-OI-HEDGEPRESSURE (open-interest positioning premium on USD-M perpetuals)

Producer: D1-A5 (outcome-blind; no candidate returns, PnL, PF, Sharpe or ranking accessed for any V11 mechanism). Literature search completed BEFORE this freeze; see `a5_search_log.json`. Bootstrap HEAD `0684914b7bf64a5b9b8eeaa82529a2d11a8a251d`, branch `orca/v11d-a5-proposals`.

## 1. Primary-source citations with claim-to-test mapping

| id | source (verified identity) | exact claim used | claim-to-test mapping in this repo |
|---|---|---|---|
| BES92 | Bessembinder, H. (1992), "Systematic risk, hedging pressure, and risk premiums in futures markets", *Review of Financial Studies* 5(4), 637–667 (Oxford Academic 1590884; JSTOR 2962144) | Futures expected returns deviate from spot risk premium according to hedging pressure: the side of the market dominated by non-speculative hedging pressure earns a premium at the expense of the opposite side | Classical mechanism pillar: positioning pressure is priced in futures. Repo test: sign of the weekly low-minus-high ΔOI book net spread in the frozen snapshot (speculative build-up pays, counterparty earns) |
| DNV00 | de Roon, F.A., Nijman, T.E., Veld, C. (2000), "Hedging pressure effects in futures markets", *Journal of Finance* 55(3), 1437–1456, DOI 10.1111/0022-1082.00253 | "Futures risk premia depend on both hedging pressure and returns on underlying assets" (abstract, verified) | Theory pillar for a hedging-pressure-sorted cross-sectional book; repo test = anchor spread sign and its consistency with the sign-flipped pressure control |
| BMI13 | Basu, D., Miffre, J. (2013), *Journal of Banking & Finance* (PII S0378426613001283) | Hedging pressure is a systematic, cross-sectionally priced factor in futures risk premiums (supporting citation, identity via publisher URL) | Prior that pressure-sorting generalises across futures markets; repo test = cross-sectional stability of the spread across folds (never a gate waiver) |
| DOA23 | Dunbar, K., Owusu-Amoako, J. (2023), "Role of hedging on crypto returns predictability", *Finance Research Letters* vol. 55 (PII S1544612323003811; Fayetteville State University repository) | "The hedging factor has a statistically significant and economically important effect on the predictability of crypto returns" | Crypto-specific pricing of positioning pressure. Repo test: the same pressure mechanism, re-earned on USD-M perps with venue OI as the PIT-implementable proxy (CFTC long/short splits are NOT available in the frozen snapshot — transfer disclosed) |
| BNDS4 | Binance USD-M futures market data endpoints — frozen packet source S4 (klines, funding history, open interest, mark price) | Official semantics for OI snapshots and completed 15m bars | Data-contract pillar: ΔOI characteristic computed from the staged OI series on the completed-bar clock; no new external data |

Leads only, never evidence: Baur et al. (2022, *Journal of Futures Markets*, CFTC positioning — data class not in snapshot); Park (2017, IRFA); vendor commentary (bitsgap) rejected outright.

## 2. Economic mechanism + expected counterparty

Hedging-pressure theory: when one side of a futures market is dominated by traders trading for directional/leveraged reasons rather than risk transfer, the OPPOSITE side earns a premium for taking the other side (Bessembinder 1992; de Roon et al. 2000). In USD-M perpetuals the tradable observable for positioning pressure is OPEN INTEREST: a fast OI build-up in a coin (ΔOI strongly positive vs its own OI base) marks leveraged speculative position accumulation; wind-down (negative ΔOI) marks leveraged-long liquidation/loss of speculative interest. The book takes the counterparty side: SHORT high-ΔOI (pressure payer) / LONG low-or-negative-ΔOI (pressure receiver). Expected counterparty: leveraged directional traders who pile into fast OI build-ups and wind down at a loss (forced deleveraging, over-leveraged latecomers), transferring premium to the patient opposite side. The mechanism is positioning-contrarian, NOT price-reversal: the sorting variable is the change in OPEN POSITIONS, never the change in price.

## 3. Required observable fields + PIT clock

- Fields (all in frozen staged snapshot): per-symbol OI snapshot series; completed 15m bars (for the daily grid, tradability floor and beta anchor); mark price for fills; funding settlements for pass-through cost accounting only.
- Transformation: OI resampled to daily UTC last-observation on the completed-bar grid; HP_i(t) = (OI_i,t − OI_i,t−28d) / mean(OI_i over trailing 28d). Winsorised 1%/99% cross-sectionally.
- PIT clock: features from snapshots strictly before the decision instant; one declared execution lag; fills strictly after the decision instant. OI snapshot cadence is whatever the frozen staging carries (15m–1d); the daily-last resample is robust to any cadence ≥1 snapshot/day; if a symbol's OI series is missing or stale at formation, the symbol is DROPPED (fail-closed, no synthesis — L-V10P-COVERAGE lesson).

## 4. Universe + benchmark role

- Universe: staged USD-M perps with ≥60d of OI history in the snapshot at formation (PIT listing rule) and median daily dollar volume above the staged-universe cross-sectional median (tradability floor for the short leg).
- Benchmark role: BTC perp = beta anchor (context-only); the scored object is the dollar-neutral long-minus-short book, beta-adjusted per leg with the repo's 90d rolling daily beta convention; BTC never enters the target book.

## 5. Schedule, holding period, turnover rationale

- Schedule: weekly decision grid (Monday 00:00 UTC) → 52 discretionary decisions/365d ≤ 60 floor.
- Holding: 7d intended holding; minimum completed span one week → median intended holding ≥ 3d floor satisfied by construction.
- Turnover rationale: tercile-bucket book (pressure characteristic is noisier than a liquidity level → fewer, wider buckets) with entry/exit buffer bands; expected one-way turnover ≈ 0.25–0.35 of book per decision. Worst case full swap ≈ 2.0 one-way × ~6 bps/side ≈ 12 bps/week ≈ 6.2%/yr of gross at the frozen floor — inside ≤8% base and ≤12% stressed; buffers only reduce it. Equal weights with per-symbol cap 1/(2·N_bucket) keep max symbol turnover share < 25% (pre-declared A3 pre-check).

## 6. Target construction + risk neutralisation

- Target: equal-weight LONG low/negative 28d ΔOI tercile minus equal-weight SHORT high ΔOI tercile; dollar-neutral (gross ≈ 2.0).
- Risk neutralisation: per-leg BTC-beta offset (90d rolling daily beta, house convention); ΔOI is cross-sectionally standardised at formation so no single high-OI-notional symbol dominates weights; explicit weight cap guards the A3 symbol-share floor.

## 7. Arms (anchor + theoretically-justified neighbour + causal negative control)

- ANCHOR `OI-HP-28D-W`: low-minus-high ΔOI/OI bucket book, 28d formation, weekly hold.
- NEIGHBOUR `OI-HP-VOLSCL-28D-W`: same mechanism, pressure normalised by market activity instead of OI base — ΔOI(28d)/mean daily dollar volume(28d) — the dimensionless "positioning change per unit of trading activity" variant. Justification: hedging-pressure ratios in BES92/DNV00/BMI13 are scale-free; scaling by activity (rather than OI stock) is the theoretically adjacent normalisation; a spread that survives only one normalisation is scaling noise, not a premium.
- CAUSAL NEGATIVE CONTROL `OI-HP-28D-W-INV`: sign-INVERTED anchor (long high-ΔOI / short low-ΔOI). Falsification: any positive after-cost spread on the inverted book destroys the mechanism claim (it would mean raw OI momentum pays, i.e. the opposite pricing).

## 8. Expected sign + falsification conditions

- Expected sign: anchor `OI-HP-28D-W` net spread > 0 after native funding and adapter costs; neighbour same sign; inverted control ≤ 0.
- Falsified if ANY of: (i) inverted control earns a positive after-cost spread; (ii) A3 schedule gate FAIL/UNAVAILABLE; (iii) fold- or symbol-concentration (Stage-A gates); (iv) anchor positive only when ΔOI is computed jointly with price direction (mechanism is OI-only; if the spread exists only with the price-direction interaction, it is a trend proxy → reject); (v) neighbour sign flip while anchor "works" (normalisation artifact → reject).

## 9. Funding / cost treatment

- Funding: native settlements accrued while held (`LONG_PAYS_POSITIVE_RATE`), pure pass-through; funding is NOT sorted on, NOT filtered on, and NOT used as the pressure proxy — the pressure characteristic is ΔOI alone, which is what keeps this family separate from funding carry.
- Costs: adapter `rebalance_cost_between` at baseline and fee×1.5/+2-tick stressed cells via the A3 gate; missing fill prices fail closed.

## 10. Ancestry / proximity + orthogonality argument

- V10 M01 (REJECTED): M01 consumed aggressor TRADE FLOW (realised executed volume prints, intraday). This family consumes OPEN INTEREST (the stock of OPEN positions — trades that have NOT offset), at weekly cadence. Different data object, different horizon, different mechanism (positioning counterparty vs flow absorption); expected orthogonality ρ ≈ 0, checked by A7-N against the M01 published series.
- Banned families: not trend/momentum (no past-RETURN signal enters any feature — falsification condition (iv) makes this testable); not reversal (no price-mean-reversion term; if the premium is really price reversal, the sign test on the OI-only book will not consistently produce it — and the A7-N orthogonality check vs weekly reversal is predeclared); not volume-shock continuation (OI is open-position stock, not traded volume; and the bet is against build-up, not for it); not funding carry (funding is pass-through only; characteristic is OI); not crowding rescue (see 12); not weekly reversal (holding is a weekly-SET book on a slow characteristic).
- Reserved seeds: seeds sort on residual return moments (vol, MAX/skew). This family sorts on a POSITIONING quantity that is not a function of the return distribution at all. Cross-sectional correlation between ΔOI and those moments is an empirical question handled by the predeclared A7-N rank-orthogonality ρ gate; if the OI premium is indistinguishable from a lottery/low-vol proxy, the family dies at A7-N.

## 11. Data readiness + implementation estimate

- Readiness: OI series are part of the staged snapshot (S4 semantics); bars, mark, funding present. Risks: (a) OI snapshot cadence/coverage per symbol is NOT verified by this lane — the Q phase must confirm ≥1 snapshot/day per universe symbol over the scored window, else the family is UNAVAILABLE_FAIL_CLOSED (no synthesis); (b) stale-OI detection rule predeclared (drop symbol if last snapshot older than 48h at formation).
- Estimate: one plugin + OI daily-resample/HP feature module + PIT fixtures ≈ 1.5–2 engineering days; A3 artifacts from the weekly schedule.

## 12. Why it is not a rescue of a previously rejected family

No V1–V10 family in the provided lessons used open interest; M01 used aggressor flow (a flow primitive), and the banned funding-carry/crowding space used funding RATES. The OI stock-change characteristic is a new data leg for this sprint, the cadence is weekly (M01's killer), and the two ways this could be a disguised old family — price-trend proxy and crowding/funding proxy — each have a predeclared rejection test: falsification condition (iv) (OI-only feature contract) and the funding pass-through-only rule plus A7-N orthogonality ρ. If those tests show the spread belongs to an old mechanism, the family is rejected, not rescued.
