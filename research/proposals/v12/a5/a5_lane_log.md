# A5 lane evidence log — V12 blind mechanism proposals

Lane: A5. Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/crypto/v12/d1-a5-proposals`
Branch: `orca/v12d-a5-proposals`. Bootstrap SHA verified: `aca3f49e41aea976dcc300652bff835e798aeb2d`
(pwd, HEAD, branch, porcelain-empty all verified before any read; log opened after identity check).

Isolation attestation:

- Read: `research/proposals/v12/blind_input_packet.{md,json}` (first read after identity check),
  `research/v12/data_contract.py`, `research/v12/load_validation.py`,
  `research/adapter_v10/{protocol,base,facade,benchmarks,stress}.py`,
  `research/v11/cost_feasibility.py`, `research/control/v12_run/forbidden_family_inventory.json`.
- NOT read: `research/control/v11_run/*`, `research/audits/*`, S1 material, other lanes'
  directories, any V11 metrics/verdicts beyond the mechanism-level forbidden inventory.
  The filenames `research/proposals/v12/{illiq_replication_brief,oilever_v2_brief}.*` appeared
  in a directory listing only; the files were NOT opened (reserved families).
- No returns, PnL, PF, Sharpe, ranking, or backtest computed anywhere in this lane. All
  proposal content is construction rules and PIT discipline; every floor check is deferred to
  the schedule-only gate (`research/v11/cost_feasibility.py`) by the scoring lanes.

## 1. Literature search log (every query + retrieval UTC)

All retrievals on 2026-09-03 UTC. The generic WebSearch tool returned repeated HTTP 429
rate-limit errors in the first window; retries succeeded from ~12:29Z onward. Primary-source
metadata was verified against the CrossRef REST API (`api.crossref.org`) and the arXiv export
API (`export.arxiv.org`); DOI correctness was checked for every accepted source.

| # | Retrieval UTC (start) | Tool | Query / endpoint | Outcome |
|---|---|---|---|---|
| 1 | 2026-09-03T12:19:31Z | WebSearch | Frazzini Pedersen "Betting Against Beta" JFE 2014 DOI | 429 rate-limit; retry loop returned embedded summary + DOI link 10.1016/j.jfineco.2013.10.005 (DOI independently re-verified in item 5 — accepted only after that check) |
| 2 | 2026-09-03T12:19:31Z | WebSearch | betting against beta cryptocurrency low-beta anomaly perpetual futures | 429 rate-limit, no results |
| 3 | 2026-09-03T12:19:31Z | WebSearch | Hvidkjaer 2008 "small trades" cross-section DOI | 429 rate-limit; embedded model-provided DOI 10.1111/j.1540-6261.2008.01356.x — REJECTED after verification (see item 6) |
| 4 | 2026-09-03T12:20–12:22Z | WebFetch | api.crossref.org/works/10.1016/j.jfineco.2013.10.005 | ACCEPTED: Frazzini & Pedersen, "Betting against beta", JFE 111(1):1–25, 2014 |
| 5 | 2026-09-03T12:20–12:22Z | WebFetch | api.crossref.org/works/10.1111/j.1540-6261.2008.01356.x | REJECTED for Hvidkjaer: resolves to Hackbarth & Morellec, "Stock Returns in Mergers and Acquisitions", JF 63(3), 2008 — DOI mismatch caught; a correct DOI was found by bibliographic search (item 8) |
| 6 | 2026-09-03T12:22:23Z | WebFetch | api.crossref.org bibliographic: "Small Trades and the Cross-Section of Stock Returns" Hvidkjaer | ACCEPTED: Hvidkjaer, RFS 21(3):1123–1151, 2008, DOI 10.1093/rfs/hhn049 (author rendered "Soeren"; NOT Journal of Finance as first recalled — venue corrected) |
| 7 | 2026-09-03T12:23:10Z (after 20s spacing) | WebFetch | api.crossref.org bibliographic: "Downside Risk" Ang Chen Xing RFS | first attempt 429; retry ACCEPTED: Ang, Chen & Xing, "Downside Risk", RFS 19(4):1191–1239, 2006, DOI 10.1093/rfs/hhj035 |
| 8 | 2026-09-03T12:24:40Z | WebFetch | api.crossref.org query: betting against beta cryptocurrency anomaly | NO crypto-specific BAB hit in top results; surfaced critique literature: Novy-Marx & Velikov "Betting Against Betting Against Beta" (SSRN 3300965, 2018, working paper), Buchner & Wagner (FRL 2016). Logged as caveats, not primary claims |
| 9 | 2026-09-03T12:25:43Z | WebFetch | api.crossref.org bibliographic: low volatility anomaly cryptocurrency bitcoin beta | ACCEPTED: Pyo & Jang, "Revisiting the low-volatility anomaly in cryptocurrency markets", Finance Research Letters, 2026, DOI 10.1016/j.frl.2026.109851 |
| 10 | 2026-09-03T12:26:47Z | WebSearch | "average trade size" OR "small trades" cryptocurrency returns predictor Binance study | SUCCESS. Surfaced: (a) FRL tick-by-tick informed-trading crypto paper; (b) EFMA 2025 working paper linking avg trade size to crypto cross-section; (c) arXiv quarter-hour effect paper; (d) secondary blogs (rejected, see §3) |
| 11 | 2026-09-03T12:28:18Z | WebFetch | api.crossref.org bibliographic: "How Wise Are Crowds" Kelley Tetlock | ACCEPTED: Kelley & Tetlock, JF 68(3):1229–1265, 2013, DOI 10.1111/jofi.12028 |
| 12 | 2026-09-03T12:29:01Z | WebFetch | api.crossref.org bibliographic: "Informed trading and cryptocurrencies ... tick-by-tick data" | ACCEPTED (metadata): Natashekara & Sampath, FRL 61:104909, 2024, DOI 10.1016/j.frl.2023.104909. Abstract NOT retrievable (ScienceDirect 403; Semantic Scholar abstract null; RePEc search page did not render) — claim usage restricted accordingly (§2) |
| 13 | 2026-09-03T12:30:01Z | WebSearch | "beta anomaly" OR "betting against beta" bitcoin cryptocurrency cross-section | SUCCESS. Surfaced Seabe et al. MDPI Mathematics 2024 (crypto BAB-type factor investing), Asness–Frazzini–Gormsen–Pedersen "Betting Against Correlation" (JFE), AQR dataset page (secondary, rejected) |
| 14 | 2026-09-03T12:31:05Z | WebFetch | api.crossref.org/works/10.3390/math12091351 | ACCEPTED: Seabe, Moutsinga & Pindza, "Optimizing Cryptocurrency Returns: A Quantitative Study on Factor-Based Investing", Mathematics 12(9):1351, 2024 |
| 15 | 2026-09-03T12:31:48Z | WebFetch | api.crossref.org bibliographic: "Betting Against Correlation" Asness Frazzini Pedersen | ACCEPTED: Asness, Frazzini, Gormsen & Pedersen, "Betting against correlation: Testing theories of the low-risk effect", JFE 135(3):629–652, 2020, DOI 10.1016/j.jfineco.2019.07.003 |
| 16 | 2026-09-03T12:32–12:33Z | WebFetch | sciencedirect.com abstract page S1544612323012813 | REJECTED (HTTP 403) |
| 17 | 2026-09-03T12:32–12:33Z | WebFetch | arxiv.org/html/2607.09426v2 | timeout; retried via export.arxiv.org API (item 18) |
| 18 | 2026-09-03T12:33Z | WebFetch | export.arxiv.org/api/query?id_list=2607.09426 | ACCEPTED: Chan Kim & Peter Reinhard Hansen, "The Quarter-Hour Effect: Periodic Algorithmic Trading and Return Predictability in Cryptocurrency Futures", arXiv:2607.09426. Six Binance perpetual contracts; volume/volatility bursts at one-minute/five-minute/quarter-hour marks; "trade-size roundness declines sharply" during bursts; opening order imbalance predicts returns over 4–12 hours |
| 19 | 2026-09-03T12:33Z | WebFetch | developers.binance.com derivatives general-info; binance.com FAQ 360033162192 | REJECTED: page content empty/not retrievable (no quotable official text). Transfer caveats that would have used leverage-bracket specifics are instead stated qualitatively and anchored on the packet's own schema facts (tick sizes 1e-7..1e-2, fee fields in instrument metadata) |
| 20 | 2026-09-03T12:34Z | WebFetch | efmaefm.org 2025 working-paper PDF (Financial Uncertainty and the Cross-Section of Cryptocurrency Returns) | REJECTED: TLS verification failure + non-peer-reviewed working paper; used nowhere |
| 21 | 2026-09-03T12:34Z | WebFetch | api.semanticscholar.org DOI 10.1016/j.frl.2023.104909 | ACCEPTED for identity only (title/authors/year/venue); abstract null — same restriction as item 12 |

Literature search COMPLETED before any proposal content was finalized; no candidate-return
computation was performed at any point (none is permitted).

## 2. Accepted sources and the exact claim each supports

### Prop 1 (V12-A5-P1-BAB-LOWBETA — leverage-constraint beta pricing)

- **[S1] Frazzini & Pedersen (2014), "Betting against beta", JFE 111(1):1–25, DOI 10.1016/j.jfineco.2013.10.005** — verified via CrossRef (item 4). Claim used: leverage-constrained investors tilt portfolios toward high-beta assets, bidding down those assets' risk-adjusted returns; a factor long low-beta / short high-beta (levered to unit beta in the original) earns positive risk-adjusted returns across asset classes. Supports: (i) the mechanism family (leverage-constraint pricing of systematic beta), (ii) the expected sign (long low-beta quintile / short high-beta quintile), (iii) the 90-day daily-beta estimation horizon as a slow, beta=systematic-risk statistic (annual-to-quarterly horizon consistent with the paper's formation).
- **[S2] Asness, Frazzini, Gormsen & Pedersen (2020), "Betting against correlation: Testing theories of the low-risk effect", JFE 135(3):629–652, DOI 10.1016/j.jfineco.2019.07.003** — verified via CrossRef (item 15). Claim used: the low-risk effect decomposes into a correlation channel (BAC) and a volatility channel, with the correlation channel the theoretically distinguishing component; assets whose co-movement with the market is highest — especially in bad states — carry the low-risk-effect short side. Supports the prop-1 neighbour (downside-correlation sort) as a THEORETICALLY JUSTIFIED neighbour inside the same family, not a parameterization of the anchor.
- **[S3] Ang, Chen & Xing (2006), "Downside Risk", RFS 19(4):1191–1239, DOI 10.1093/rfs/hhj035** — verified via CrossRef (item 7). Claim used: downside (semibeta) risk is a distinct, priced risk statistic relative to unconditional beta. Logged as the alternative neighbour candidate; the adopted neighbour is the S2 downside-correlation sort (closer to the accepted 2020 decomposition). Kept in the log because prop-1's falsification diagnostics reference downside-vs-unconditional beta separation.
- **[S4] Seabe, Moutsinga & Pindza (2024), "Optimizing Cryptocurrency Returns: A Quantitative Study on Factor-Based Investing", Mathematics 12(9):1351, DOI 10.3390/math12091351** — verified via CrossRef (item 14). Claim used: BAB-type/low-volatility factor construction has been transplanted to cryptocurrency factor investing, i.e., the crypto cross-section is a feasible habitat for the mechanism. Transfer evidence only — no sign claim is imported from it.
- **[S5] Pyo & Jang (2026), "Revisiting the low-volatility anomaly in cryptocurrency markets", Finance Research Letters, DOI 10.1016/j.frl.2026.109851** — verified via CrossRef (item 9). Claim used: the low-risk/low-volatility anomaly is documented (and re-confirmed) in cryptocurrency markets. Transfer evidence for the family's sign in crypto; caveat recorded: low-VOLATILITY sorts are adjacent to but distinct from BETA sorts; prop 1 sorts on beta, and the anchor's ancestry mapping argues that distinction explicitly.
- **[S6] Novy-Marx & Velikov (2018), "Betting Against Betting Against Beta" (SSRN working paper 3300965)** — surfaced in item 8; NOT peer-reviewed; logged as a caveat only: published BAB premia are sensitive to implementation and microstructure; motivates prop-1's requirement that the anchor's spread not be concentrated in the beta-tilt residual and its sign-flip control.

### Prop 2 (V12-A5-P2-MIX-ORDERSIZE — participant-mix / order-size composition)

- **[S7] Hvidkjaer (2008), "Small Trades and the Cross-Section of Stock Returns", RFS 21(3):1123–1151, DOI 10.1093/rfs/hhn049** — verified via CrossRef (item 6; initially mis-attributed DOI and venue, corrected by verification). Claim used: small-trade (retail-like) buy pressure is followed by significant subsequent underperformance, while large-trade pressure is not — order-size composition identifies a participant mix whose demand overprices. Supports: mechanism family, expected sign (short names with falling average trade size = rising retail-like share; long names with rising average trade size), and the neighbour estimator (share-of-bars statistic as a bucket analogue).
- **[S8] Kelley & Tetlock (2013), "How Wise Are Crowds? Insights from Retail Orders and Stock Returns", JF 68(3):1229–1265, DOI 10.1111/jofi.12028** — verified via CrossRef (item 11). Claim used: order-size-based classification separates retail from institutional flow, and retail order imbalance contains predictive content beyond institutions'. Supports the economic counterparty definition (retail cohort trading smaller clips) and the choice of quote-volume/trade-count as the observable mix proxy when client-level data are unavailable.
- **[S9] Natashekara & Sampath (2024), "Informed trading and cryptocurrencies. New evidence using tick-by-tick data", FRL 61:104909, DOI 10.1016/j.frl.2023.104909** — metadata verified via CrossRef + Semantic Scholar (items 12, 21); abstract NOT retrievable. Claim used (restricted to identity-level): trade-size-based informed-vs-retail classification has been applied to cryptocurrency markets. No specific empirical sign is imported from this source; the crypto sign claim rests on S7+S8 transfer reasoning plus S10's venue evidence. Logged as supporting/contextual.
- **[S10] Kim & Hansen (2026), "The Quarter-Hour Effect: Periodic Algorithmic Trading and Return Predictability in Cryptocurrency Futures", arXiv:2607.09426** — verified via arXiv export API (items 17–18). Used as a TRANSFER CAVEAT for prop 2 (and a minor caveat for prop 1): on Binance perpetuals, volume and volatility burst at one-minute/five-minute/quarter-hour marks driven by algorithmic trading, and trade-size roundness statistics distort during bursts — therefore prop 2's formation statistic is aggregated at bar level over multi-week windows (never single bars) and the mechanism-destroying placebo controls for any residual volume/count-driven artifact. Their intraday order-imbalance predictability claim is explicitly NOT used (see §3, R6).
- **[S11] Novy-Marx & Velikov (2018)** (same as S6) — caveat reused for prop 2 falsification design: microstructure implementation details can absorb small premia; motivates the placebo and the hysteresis/cooldown turnover guards.

## 3. Rejected sources and reasons

- **R1** — WebSearch embedded 429 summaries: treated as unverified; every fact drawn from them was re-verified against CrossRef/arXiv before acceptance (items 1–3, 10, 13 partially rate-limited).
- **R2** — DOI 10.1111/j.1540-6261.2008.01356.x recalled for Hvidkjaer: resolves to Hackbarth & Morellec (2008) — REJECTED; correct DOI found by bibliographic search (item 5–6).
- **R3** — AQR dataset/journal-article pages, Alpha Architect, Quantpedia: secondary/vendor commentary — REJECTED as primary sources (no DOI/stable peer-reviewed claim).
- **R4** — Buchner & Wagner (2015/2016) BAB critique: relevant critique literature but the adopted falsification design does not depend on it; logged only (S6 covers the caveat role).
- **R5** — EFMA 2025 working paper (avg trade size vs crypto uncertainty beta): non-peer-reviewed and TLS verification failed — REJECTED; not used anywhere.
- **R6** — Kim & Hansen (2026) intraday claim "opening order imbalance predicts returns over 4–12 hours": REJECTED as a mechanism basis — it is an intraday signed-flow phenomenon, adjacent to the forbidden aggressor-absorption class (V10-M01) and far outside the weekly decision clock. Only their algorithmic-burst/trade-size-distortion caveat is used (S10).
- **R7** — Binance leverage-bracket FAQ/developer pages: content not retrievable (empty renders); no official quote available, so no leverage-specific numeric caveat is asserted anywhere in the proposals.
- **R8** — Pursiainen & Toczynski (2022, SSRN) and Ante et al. (2020, SSRN) retail-crypto papers: surfaced but working papers without verified relevance to order-size cross-sections; not used.

## 4. Parameter mapping rationale (literature -> design)

- **90-day trailing window (both proposals):** taken from the frozen data contract
  (`research/v12/data_contract.py` declares `beta_90d` as the binding 90-day warmup and
  `warmup_report` makes satisfiability checkable from pre-window history). NOT retuned from
  any rejected family; it is the only warmup horizon the contract declares, which removes a
  degree of researcher freedom.
- **Weekly Monday 00:00:00Z decision stamps:** packet convention; equals 52 discretionary
  decisions/365d by schedule construction (floor: <= 60) — compliance is by construction,
  verified later by the schedule-only gate.
- **Quintile books, equal-within-leg, leg gross 0.5:** the packet's eligible book shapes;
  `w_i = min(0.30, 0.5/n_leg)` guarantees `max|weight| <= 0.30` for every leg size >= 2 and
  the uniform-shrink rule covers n_leg = 1 — cap compliance is by construction, not by
  post-score clipping (post-score renormalisation is itself forbidden for OILEV; we avoid
  any post-score adjustment everywhere).
- **Two-stamp hysteresis (enter/exit only after two consecutive stamps in/out of band) and
  a 28-day per-symbol re-entry cooldown:** turnover-control construction chosen so that
  (i) median intended holding is 28d (floor >= 3d) by design, and (ii) no single symbol can
  dominate one-way turnover (floor <= 25%) because any symbol is bounded to at most one
  entry/exit cycle per 28d while eight-or-more leg slots share the turnover. The schedule
  gate verifies both floors; the lane only fixes the construction.
- **Beta-neutralisation primitive:** legs scaled so the book's BTC beta sums to zero using
  the same trailing 90d daily beta used for eligibility; whole-book uniform shrink keeps the
  cap. Prop 1 uses the beta rank as SIGNAL and the neutralisation as risk control; prop 2
  uses the same neutralisation purely as a risk primitive (signal has no beta content).
- **One declared execution lag:** fill at the first completed 15m bar strictly after the
  00:00Z stamp (bar 00:00–00:15Z, fill recorded at its close 00:15Z), matching the adapter's
  strict-later `FILLED_NEXT_EVENT` semantics; the stress cell adds +1 event delay on top.
- **Funding:** never a formation input (avoids V6/V1-CARRY adjacency); native accrual while
  held with the repo convention `LONG_PAYS_POSITIVE_RATE`, PIT rule "settlement ts within
  [ts_opened, ts_closed]" per `load_validation.py`. Prop 1 carries an explicit carry-confound
  probe in its falsification conditions because the BAB short leg (high-beta alts) may
  coincide with positive-funding symbols.
- **Negative controls:** prop 1 = sign-flipped anchor (sign-destroying; the leverage-constraint
  theory predicts the flipped book should NOT earn the anchor's spread); prop 2 =
  trade-count-permuted placebo (mechanism-destroying; permuting each symbol's 15m trade counts
  within its own 90d formation window preserves every marginal distribution but destroys the
  temporal participant-mix signal — if the placebo book tracks the anchor, the true driver is
  volume/count level, i.e., volume-shock/illiquidity adjacency, and the family is falsified).

## 5. Mechanism-family selection vs the forbidden inventory (why these two)

Candidate families considered and dropped before proposal: funding-level or funding-volatility
cross-sections (V6/V1-CARRY adjacency), any OI-based signal (V11-OILEVER reserved family),
idiosyncratic volatility/skew/MAX statistics (V11-LOTTERY adjacency), Amihud/Roll-style impact
or spread proxies (V11-ILLIQ reserved), 52-week-high anchoring (maps to momentum taxonomy),
round-number support/resistance (sign-ambiguous, breakout/reversal adjacency), weekend/session
seasonality (incompatible with the Monday 00:00Z clock), any signal needing off-exchange data
(DATA-GATED). The two adopted families were selected because (i) each has a verified
primary-source claim with a clear economic counterparty and sign, (ii) each is constructible
purely from the packet schema (15m bars incl. quote-volume and trade counts; BTC as benchmark),
and (iii) each is mechanism-level distinct from every forbidden class (full mapping in the
proposal ancestry sections).

## 6. Assumptions and open items

- Funding rate VALUES are assumed present alongside `fundingTime` in the staged funding
  bundles (the data contract shows settlement timestamps; the packet lists "funding
  settlements" as a field). If rates are absent, funding is a cadence-only cost and both
  proposals remain constructible (funding would then drop out of the cost pass-through);
  neither proposal's signal depends on funding values.
- The 15m bar schema carries a `trades` (count) column per the packet; if the staged bars
  lack it, prop 2's formation statistic is not constructible and prop 2 should be withdrawn
  (its JSON records this dependency as a fail-closed precondition).
- No network fetch of market data was performed (prohibited); all data knowledge comes from
  the schema/contract files.
