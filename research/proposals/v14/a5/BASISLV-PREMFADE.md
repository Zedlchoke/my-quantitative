# A14-V14-A5-BASISLV-PREMFADE — Cross-sectional perp-premium level fade (crowding-unwind conditioning)

Lane: a5 (d1-a5-proposals) | Cycle: CRYPTO-V14 Phase D1 | AXIS-1 basis level / carry structure
Wave SHA: `c3e3c90561efc972c487a99951ca0f6031ab4fa34907d1c10890d1795b4da4a8`
Outcome-blind proposal: no computation performed, no per-arm outcome file accessed, none sought.
Status: NEW mechanism, conditioning space = cross-sectional mark/index-vs-perp premium LEVEL
(the crowding/carry premium level, ranked across symbols). Dataset authority:
`research/control/v14_run/p1_a3/availability_evidence_table.json` — source
`basis_futures_data` (endpoint `/futures/data/basis`, contractType=PERPETUAL) classified
**EVIDENCED_AVAILABLE** (measured point anchors at the 2025-08-22 screen start and 2026-08-21
screen end on all 4 probed symbols, deeper brackets at 2024-08-20 and 2023-01-01, documented
semantics archived; documented-vs-measured discrepancy D1 recorded and carried below).

## 1. Hypothesis ID and mechanism

Hypothesis ID: `A14-V14-A5-BASISLV-PREMFADE`

On a USD-M perpetual the gap between the perp's price and the underlying index — the basis —
is the shadow price of leveraged directional demand. When leveraged traders crowd long a name,
their marginal flow lifts the perp above the index; when they crowd short, the perp sags below
it. This premium is observable per symbol at 15-minute resolution directly from the venue's
basis route (`futuresPrice` vs `indexPrice`; the endpoint also reports `basis`, `basisRate`,
`annualizedBasisRate`). The mechanism conditions on the cross-sectional LEVEL of this premium:
a name whose perp has traded at a persistently elevated premium over the trailing 28 days
carries a crowded leveraged-long book, and the conditioning claim is that this crowding is a
negative state variable for the next week's relative return.

Why the edge survives costs: (i) unwind risk — leveraged perp positions are margin-funded;
a persistent premium extension marks late-stage leverage, and deleveraging episodes force
perp sales back toward the index, so the unwind itself is the forward return
(Brunnermeier & Pedersen 2009 funding-liquidity spirals); (ii) limits of arbitrage —
premium compression toward the index is performed by arbitrageurs whose capital is finite
and who explicitly avoid crowded, expensive trades (Shleifer & Vishny 1997; Makarov & Schoar
2020 document that crypto premia persist across venues precisely because arbitrage capacity
is segmented), so the premium does not vanish instantly and retains predictive content at a
weekly horizon; (iii) the crowding is name-level, not market-level — the book is long/short
beta-hedged and the ranking is cross-sectional, so the claimed information is the RELATIVE
premium, not a market-wide sentiment tilt.

Predicted sign (declared ex ante): a NEGATIVE relation between trailing mean perp premium
level and forward weekly relative return — long the low/discount-premium tier, short the
high/premium tier. The null that kills it: after costs, zero or positive relation — in
particular, if the sign-inverted control (long the high-premium tier) passes the same
incremental gate, the premium ordering carries no directional crowding information and the
mechanism is falsified (factory-standard rule, L-V11-3 / L-V12-1).

Honest prior-sign disclosure: the futures-carry literature records the OPPOSITE prior
(Koijen, Moskowitz, Pedersen & Vrugt 2018: high carry — a high basis — is REWARDED across
asset classes). The declared sign here follows the crowding-unwind mechanism specific to
leveraged, retail-dominated perpetual markets, not from the carry literature. If the data
sides with the carry prior, the anchor fails its gates and the inverted control is a recorded
falsification artifact — never a promotable family and never rescuable by renaming
(V6/V1-CARRY-FUNDING adjacency handled in section 11).

## 2. Falsifiable prediction

After base costs, the `BASISLV-PREMFADE-28D` anchor earns positive BTC-beta-context weekly
excess in at least 2 of the 3 frozen chronological folds, its 56D neighbour supports the same
sign, and the sign-inverted control does NOT pass the same gate. The hypothesis is FALSIFIED
if any of: (a) the anchor's beta-context excess is not positive in >= 2/3 folds; (b) the
sign-inverted control (long HIGH premium / short LOW premium) ALSO passes the incremental
gate — then the ordering carries no directional information and any anchor result is a
generic tilt artifact; the anchor is rejected and the control is never promotable; (c) the
neighbour flips sign (the premium level is formation-window fragile, not the persistent
crowding state the mechanism requires); (d) the anchor passes base but fails stress — the
measured effect is a spread/slippage execution artifact; (e) price-only expectancy <= 0 while
total expectancy is positive only through native funding credits — the mechanism is then a
carry harvest, not a price-unwind mechanism, and the family is rejected as declared ex ante
(section 11, V6 adjacency).

## 3. Literature (citations from verified knowledge; transfer caveats)

No network fetch was performed in this lane (D1 hard constraint). Citations below are
canonical works cited from verified model knowledge with full authors/venue; A9-F/D2 may
verify bibliographic details at audit. Crypto-perp basis-level cross-sectional evidence in
the peer literature is THIN — stated honestly; the a priori sign is declared from the
mechanism, not from any fetched empirical result.

| # | Citation | Role | Verdict + reason |
|---|----------|------|------------------|
| L1 | Koijen, Moskowitz, Pedersen & Vrugt (2018), "Carry", Journal of Financial Economics 127(2), 197-225 | Lineage contrast, OPPOSITE prior | ACCEPT as prior-sign disclosure only: carry (spot-futures basis) predicts returns positively across traditional asset classes. This proposal declares the reverse sign for leveraged perps and preregisters its own falsification if the carry world obtains. No design element taken. |
| L2 | Brunnermeier & Pedersen (2009), "Market Liquidity and Funding Liquidity", Review of Financial Studies 22(6), 2201-2238 | Primary mechanism | ACCEPT: margin-funding spirals link leveraged position crowding to forced price-moving unwinds; grounds the unwind channel by which a premium LEVEL predicts negative forward returns. |
| L3 | Shleifer & Vishny (1997), "The Limits of Arbitrage", Journal of Finance 52(1), 35-55 | Primary mechanism | ACCEPT: arbitrageurs under-commit against crowded trades, letting premia persist long enough to carry weekly predictive content rather than being arbitraged to zero instantly. |
| L4 | Makarov & Schoar (2020), "Trading and arbitrage in cryptocurrency markets", Journal of Financial Economics 135(2), 293-319 | Crypto transfer | ACCEPT: documented persistence of large crypto premia across venues and segmented arbitrage; supports that a perp-vs-index premium is a slow, informative state variable in crypto rather than pure microstructure noise. |
| L5 | Direct cross-sectional evidence on Binance USDT-M perp basis LEVEL and forward returns | Gap | NOT RETRIEVED — honestly reported: this lane performs no web retrieval; to its verified knowledge no canonical peer-reviewed result establishes the cross-sectional sign of perp basis LEVEL on Binance USDT-M perps. The proposal is therefore mechanism-driven with preregistered falsification, which is exactly the posture the cycle requires. |

Transfer caveats: L2 is equity-market funding-liquidity theory (transfer: perps institutionalize
margin funding continuously via native settlement, strengthening the channel but changing the
microstructure); L4 studies venue-vs-venue premia, not perp-vs-index premia (transfer: same
limits-of-arbitrage logic, different leg); L1's opposite prior means a positive result for the
inverted control must be read as falsification, never as "carry works".

## 4. PIT observable (fusion-record availability semantics; EVIDENCED availability stamps)

Decision instant T = Monday 00:00:00Z. A decision at T reads ONLY rows with
`available_time_utc <= T` (p_freeze_v14.v14_specific_freezes.pit_authority;
research/data_fusion/crypto_compat.py semantics). Retrieval time never substitutes for
availability.

- Signal route: endpoint `/futures/data/basis`, `contractType=PERPETUAL`, `period=15m`,
  `pair=<SYMBOL>` (param style per evidence table `basis_futures_data.measured`: pair=;
  measured schema fields `futuresPrice`, `indexPrice`, `basis`, `basisRate`,
  `annualizedBasisRate`, `contractType`, `pair`, `timestamp`). EVIDENCED_AVAILABLE per
  `availability_evidence_table.json` (classification_basis: measured point anchors at screen
  start/end, 4/4 probed symbols, brackets to 2024-08-20 and 2023-01-01; documented pair /
  contractType / period / limit semantics archived).
- Lag convention frozen: a period bucket covering [t_open, t_open+15m) is treated available at
  its close time t_close = t_open + 15m (conservative bar-close availability class, matching the
  evidence table's publication-lag semantics "period-aligned buckets; latest observed bucket
  advances with query time"). A decision at T uses ONLY fully-closed prior buckets with
  t_close <= T; the last admissible bucket for a Monday 00:00Z stamp is [Sun 23:45, Mon 00:00).
  No partial bucket is ever read.
- Per-bucket premium: p_b = (futuresPrice − indexPrice) / indexPrice, computed from archived
  fields. Staging identity check: computed p_b vs the endpoint's own `basisRate` must agree
  within a declared relative tolerance; any violation flags the symbol fail-closed at staging.
- Signal: b_i(T) = mean of p_b over the trailing 2688 (anchor) / 5376 (neighbour) completed
  buckets; EVERY slot must exist and be available; one missing slot refuses the symbol at that
  stamp (fail-closed, no back-fill, no synthesized tail — L-V12-5).
- BTCUSDT (bars): benchmark buy-and-hold + 90d beta context only, never ranked.
- Funding settlements (`crypto_funding`, available at settlement stamp): native cost/credit on
  held legs exactly once per settlement, identical across arms; NEVER a signal input.

Depth-evidence caveat (D1, carried verbatim as an obligation): P2 measured basis-route depth on
BTCUSDT / ETHUSDT / SOLUSDT / XRPUSDT only; per-symbol depth re-verification for all 19 ranked
names is a mandatory staging prerequisite ("D2/A9-F must re-verify before any scored use" —
availability_evidence_table.json, discrepancy D1 resolution). Forward pagination only
(discrepancy D3: backward endTime walks repeat the latest page and are invalid).

## 5. Universe, warmup, clock, holding, execution (frozen conventions)

- Universe: the 20 staged REQUIRED_SYMBOLS (research/audits/v12p/a3_s0_snapshot_authorization.json:
  1000PEPE/AAVE/ACE/ADA/AVAX/BCH/BNB/BOME/BTC/DOGE/ENA/ETH/LINK/NEAR/ONG/SOL/SUI/WLD/XRP/ZEC
  USDT) minus BTCUSDT = 19 tradable names. Eligibility at T: full completed-bucket coverage of
  the formation window (fail-closed) plus the binding 90-day beta warmup. Universe eligibility
  per the V12 selection_freeze authority cited in p_freeze_v14.json inherited_conventions[1]
  (research/control/v12_run/selection_freeze.json, sha256 0b3b0865...).
- Warmup: binding maximum 90 days (beta context, from already-authorized bars); anchor premium
  formation 28d (2688 buckets); neighbour 56d (5376 buckets). First screen stamp 2025-08-25
  (V12 downstream obligation); earliest required basis data 2025-06-30 (56d before first
  stamp) — entirely inside the authorized window 2024-08-20..2026-08-21.
- Decision clock: weekly, every Monday 00:00:00Z (52 decisions in the 364-day blind-S0 window
  2025-08-22..2026-08-21 <= 60 floor). Folds: frozen F0 2025-08-22..2025-12-21,
  F1 2025-12-22..2026-04-21, F2 2026-04-22..2026-08-21, 1-day purge, force-flat at boundaries
  (V12 frozen fold contract); ~17 decisions per fold.
- Holding: intended 7 days (>= 3d floor); force-flat at fold boundaries.
- Execution lag (ONE, declared): fills at the close of the first completed 15m bar strictly
  after T (Monday 00:15:00Z bar close); stress adds +1 event delay (Monday 00:30:00Z close).
- Book: long the lowest premium tercile, short the highest tercile — sides of size
  floor(N_eligible/3) each, equal weight 1/(2·floor(N_eligible/3)) per leg, gross 1.0; ties
  broken by symbol id ascending (declared a priori); middle tercile flat. Minimum 12 eligible
  names for a stamp to trade; max |weight| = 1/8 = 0.125 <= 0.30 at every stamp by
  construction (L-V11-2 co-design satisfied). BTCUSDT never ranked.

## 6. Arms (exactly 3): anchor + neighbour + causal negative control

- ANCHOR — `BASISLV-PREMFADE-28D`: b_i over trailing 2688 completed 15m buckets (28d); book as
  in section 5 (long low-premium tier / short high-premium tier).
- NEIGHBOUR — `BASISLV-PREMFADE-56D`: same mechanism and book, formation window 5376 buckets
  (56d). Justification: the crowding state must be persistent for the unwind mechanism to be a
  level effect rather than a spike artifact; 56d is in the frozen warmup table and is the
  pre-declared sibling of the 28d anchor. If the mechanism exists only at one formation window
  it is not the declared persistent-crowding mechanism and the family fails.
- CAUSAL NEGATIVE CONTROL — `BASISLV-PREMFADE-28D-INV`: identical construction and book with
  the sign inverted (long HIGH premium / short LOW premium). Factory-standard causal negative
  control (same pattern as the frozen OILEV-V2 inverted control and BAB inverted control).
- Preregistered control rule: the control MUST NOT reproduce the anchor — if
  `BASISLV-PREMFADE-28D-INV` passes the same incremental gate (BTC-beta-context excess
  positive in >= 2/3 folds), the premium ordering carries no directional crowding information,
  the anchor FAILS and the family is rejected; the control is never promotable to a family
  regardless of its own result (L-V12-1: inverted-control wins are falsification artifacts,
  never candidates).
- Beta/funding separation (all arms): identical universe, fills, and identical native funding
  accounting; funding is a cost/credit, never a signal; the incremental gate is BTC-beta
  adjusted; anchor-minus-control difference is premium-direction information, not carry or beta.

## 7. Incremental test vs buy-and-hold and BTC-beta context

- Benchmark: BTCUSDT buy-and-hold over the same stamps (same clock, same fold boundaries).
- Beta context: weekly arm excess adjusted by beta from trailing 90d of completed daily bars
  (frozen convention).
- Incremental means, for this family: after-cost excess return OVER the beta-matched benchmark
  attributable to the cross-sectional premium ordering — i.e. what remains of anchor returns
  after removing (i) the BTC buy-and-hold leg and (ii) the 90d-BTC-beta exposure of the book.
- Binding gate (Stage-A, unrelaxed): anchor BTC-beta-context excess positive in >= 2/3 folds;
  raw excess vs buy-and-hold also positive in >= 2/3 folds for the family to advance; neighbour
  same sign; control must NOT pass per section 6.

## 8. Costs under the remediated kernel, floors, concentration, drop-one

- Costs (L-V14-0 remediated kernel, binding): charged on FILLS ONLY — exactly once per fill,
  never per holding-day, never per stamp on open positions; real perp-metadata tick sizes per
  symbol (no uniform stubs); native funding settlements on held legs exactly once per
  settlement; scored cells report cost broken out by fills vs holding terms. Base schedule +
  stress = fee x1.5, +2 adverse ticks (per-symbol tick size), +1 event delay. Feasibility
  (base drag <= 8%/yr of gross; stressed <= 12%/yr) is evaluated by A9-F from schedule
  artifacts only — no cost number is computed in this proposal.
- Turnover (numeric bound): each weekly decision trades at most the legs that change ranks;
  hard upper bound 2 x floor(N/3) exits + 2 x floor(N/3) entries <= 24 fills per decision per
  arm, i.e. <= 1,248 fills/window/arm at 52 decisions (expected far lower; measured at score
  time and reported in the fills-term cost column).
- Sample floors (numeric): >= 52 weekly decisions per arm in the screen window; >= 15 decisions
  per fold; >= 12 eligible names per trading stamp (below that the stamp refuses and the
  refusal is counted); if refusals leave < 15 traded stamps in any fold or the eligible
  universe averages < 12 names over the window, the verdict is BLOCKED_DATA (a data failure,
  not a mechanism rejection). Zero-position arms refused at publication (L-V11-4).
- Concentration: max |weight| <= 0.30 by construction; no symbol > 25% of turnover (checked by
  A9-F); largest symbol positive-PnL share <= 0.70 gate inherited.
- Drop-one design (non-vacuous): identify the fold-stamp with the largest held |weight|; under
  equal weights all held legs tie, so the pre-declared outcome-free tie-break applies: drop the
  held leg with the largest |b_i(T)| (the most extreme premium expression — strongest
  mechanism instantiation) at that stamp. By construction the dropped symbol held >= 1 position
  (non-vacuousness, L-V11-7). Renormalize the remaining 2k−1 legs to gross 1.0 and re-run the
  anchor. The family survives only if the anchor's fold-sign pattern and the control rule's
  outcome are unchanged; otherwise the edge is symbol-specific and the family is rejected.

## 9. Failure interpretation

- Anchor fails the incremental gate in all folds: no after-cost premium-level information at
  the weekly horizon; the crowding-unwind mechanism is absent or arbitraged away; family
  rejected (no parameter search, no window or universe retune).
- Anchor positive but sign-inverted control also passes: the ordering carries no directional
  information; the anchor result is a tilt/cost artifact; family rejected; control never
  promotable. NOTE: this outcome is exactly the Koijen-carry world of section 1 — it is a
  falsification, and the inverted arm becomes a recorded shadow observation only, never a
  candidate (L-V11-3, L-V12-1).
- Price-only expectancy <= 0 with total expectancy positive only via funding credits: the
  mechanism is a carry harvest, not a price-unwind mechanism; family rejected as V6-adjacent
  carry harvesting (declared ex ante, section 11).
- Anchor positive, neighbour negative or sign-flipped: premium level is formation-window
  fragile — not the persistent crowding state the mechanism requires; family rejected.
- Anchor passes base but fails stress: spread/slippage execution artifact; family rejected.
- Fold-concentration failure (> 50% of positives in one fold): one deleveraging episode drives
  everything; not a persistent mechanism; family rejected.
- Symbol-concentration failure (largest symbol > 0.70 of positive PnL): single-name artifact;
  family rejected.
- High refusal rate / depth re-verification failures: BLOCKED_DATA, not a mechanism rejection.

## 10. Source-to-test map (staging plan; NO downloads performed in this lane)

| Input (endpoint / field) | Availability stamp | Exact test use | Staging plan |
|---|---|---|---|
| `/futures/data/basis`, contractType=PERPETUAL, period=15m, pair=<SYM>: fields futuresPrice, indexPrice (+ basis, basisRate as identity cross-check) | bucket close time (bar-close class; frozen lag convention section 4) | p_b per bucket; b_i over 2688/5376 buckets; tercile ranking; fail-closed gap refusal | 19 symbols, 2025-07-28T00:00Z..2026-08-21T23:59Z (28d before first stamp + screen); ~37.3k buckets/symbol; limit=500 forward pagination (D3) => ~75 req/symbol => ~1,425 requests total (documented weight 0; 0.55s sleep ≈ 13 min) |
| Depth re-verification point anchors | as measured (evidence table D1) | per-symbol depth proof for all 19 names before scored use | startTime+endTime limit=1 anchors at 2025-06-30 and 2026-08-21 per symbol => 38 requests; failing symbols dropped fail-closed; < 12 eligible => BLOCKED_DATA |
| `crypto_bars` 15m completed (authorized, staged) | bar close time | weekly benchmark, 90d beta, fill prices, holding PnL | already staged/authorized; no new fetch |
| `crypto_funding` settlements (authorized, staged) | settlement stamp | native cost/credit on held legs, once per settlement, all arms identically | already staged/authorized; no new fetch |
| perp instrument metadata tick sizes | static metadata | +2-tick stress unit per symbol (remediated kernel) | staged; no new fetch |
| (explicitly NOT used) open interest, mark/index klines for the signal, premiumIndexKlines, quarterly-contract basis (CURRENT_QUARTER/NEXT_QUARTER), funding rate as signal | — | declared out of scope to bound the conditioning space and keep A6/V13-OITD separation | — |

## 11. Forbidden-packet self-check (every inventory class inspected)

| Class | Inspected; why this proposal is not a variant/rescue |
|---|---|
| V10-M01-AGGRESSOR-ABSORPTION | No aggressor side, order-flow panel, or absorption variable; premium is a price-gap from public mark/index routes. Clean. |
| V11-LOTTERY-MAX-SKEW | No return moments anywhere (no MAX, skew, lottery, idio-vol). Only the perp-index price gap. Clean. |
| V11-ILLIQ-AMIHUD | No \|return\|/dollar-volume impact ratio; the frozen ILLIQ replication brief is untouched. Clean. |
| V11-OILEVER-DELEV | No open-interest input; no cap change (0.30 satisfied at 0.125 max by construction). Clean. |
| V4-XSECT-MOM | No past-return term in the signal. HONEST RISK NOTE: premium level correlates mechanically with recent appreciation, so the anchor rank may empirically correlate with momentum ranks; the defense is structural (signal contains no return) plus the accepted A7-N rank-correlation gate vs all rejected momentum ancestors — if rho > 0.20 this proposal is INELIGIBLE and should be found so. |
| V6/V1-CARRY-FUNDING | CLOSEST CLASS — declared adjacency. The V6 forbidden class is funding-RATE carry/crowding rescues (V6 horizons 1/3/7d and their inverse), and its signal field is funding settlements. Here the signal is the perp-vs-index premium from the price route (a distinct, unclipped, continuous information source; funding is clipped, settlement-quantized, and enters ONLY as an identical native cost), and the declared sign FADES the premium whereas V6 harvested carry. Residual risk: economically adjacent neighborhood. Guard rails preregistered: (i) price-only failure clause (section 9) rejects a funding-credit-driven result; (ii) the inverted control fires on the carry world; (iii) A7-N rho gate vs the V6/V1 rows accepted as binding. If A7-N rules this a V6 rescue, this proposal is INELIGIBLE and should be found so. |
| V1-VOLCOMP | No volatility compression, no breakout, no continuation claim. Clean. |
| V8R-XSECT-REVERSAL | No price-reversal signal; ranking variable is the premium gap, not past returns. Same honest correlation caveat as V4 row; A7-N gate accepted. |
| V9-TS-TREND | No time-series trend feature or dead-zone book. Clean. |
| WEEKLY-REVERSAL / MR-RESCUE | Not a renamed rejected baseline: no return term, no Bollinger/RSI/VHF machinery; mechanism is premium crowding, falsifiable by its own inverted control. Clean. |
| V12-OILEV-V2 | No OI input of any kind; not a sign flip, horizon tweak, universe carve-out or renaming of OILEV-V2. The +0.758 shadow observation is inverted-OI-FLOW — a different variable; this proposal declares itself OUTSIDE the shadow region (section 12). Clean. |
| V12-BAB-LOWBETA | No beta-sorted book; beta only as identical context adjustment. Not a beta-model retune. Clean. |
| V12-ILLIQ-REPLICATION | Untouched; no window substitution; no re-opening. Clean. |
| DATA-GATED | Only EVIDENCED_AVAILABLE routes cited (basis route + already-authorized bars/funding); free keyless Binance public endpoints; no external, paid or asserted-unevidenced source. Clean. |
| V13-OITD-TERM-STRUCTURE | No open-interest term structure and no positioning-duration variable. Quarterly-contract calendar basis (CURRENT_QUARTER/NEXT_QUARTER) is explicitly DECLARED OUT OF SCOPE in section 10 to avoid any OITD adjacency. Clean. |
| V13-LIQEPIS | No volume input, no episodicity/Herfindahl, no liquidity-provision variable. Clean. |

Lane-axis discipline: this is a LEVEL/dispersion-state proposal (AXIS-1). No basis CHANGE,
momentum, reversion or basis VOLATILITY through time enters any signal (AXIS-2 boundary,
A6's lane) — declared so the wave-diversity rule can operate; A7-N cross-cluster
correlation measurement is accepted as binding.

## 12. Shadow-region posture (voluntary)

The recorded shadow observations (inverted OI-flow +0.758 in the V12 OILEV-V2-INV control;
V11 LOT inversion; stocks vol-level sorting) involve different variables; no prior control arm
ever measured the perp-index premium level. This proposal declares itself OUTSIDE the shadow
region and claims no prior-sign disclosure beyond section 1's literature-prior disclosure. If
A1/A7-N classify it into the shadow region anyway, the front door is pre-accepted: mechanism
stated in its own words, confirmatory status recorded in verdict and denominator, own causal
negative control (section 6), A7-N rho gate |rho| <= 0.20 vs the frozen OILEV-V2 anchor AND
its inverted control accepted as an eligibility condition, Stage-A gates unrelaxed.

## 13. Outcome-blind attestation

```
OUTCOME-BLIND ATTESTATION
lane: a5 (d1-a5-proposals)  proposal: A14-V14-A5-BASISLV-PREMFADE
wave SHA: c3e3c90561efc972c487a99951ca0f6031ab4fa34907d1c10890d1795b4da4a8
I wrote this mechanism, its arms and its falsification conditions before any
return, metric or ranking was computed, without access to any per-arm outcome
file or scored artifact, and I will not modify this proposal after outcomes
exist. No backtest, PnL, data download or network fetch was performed.
utc: 2026-09-05T00:33:36Z  agent: a5
```
