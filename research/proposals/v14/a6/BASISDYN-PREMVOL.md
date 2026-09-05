# A14-V14-A6-BASISDYN-PREMVOL — Premium-Instability Unwind Overhang (basis second moment)

lane: d1-a6-proposals (outcome-blind proposal, Phase V14-D1) — cycle CRYPTO-V14
axis: AXIS-2 basis dynamics (time-series conditioning on how the mark-index
premium is VARYING — never on its cross-sectional level or dispersion, which is
AXIS-1's variable)
wave SHA: `V14_PROPOSAL_WAVE_SHA = c3e3c90561efc972c487a99951ca0f6031ab4fa34907d1c10890d1795b4da4a8`

---

## 1. Hypothesis ID + mechanism

**Hypothesis ID: `A14-V14-A6-BASISDYN-PREMVOL`**

Mechanism (own words): on Binance USD-M perpetuals the premium — the perp-side
mark relative to the index — prices the discounted stream of expected funding
(He–Manela–Ross–von Wachter). The VOLATILITY of the premium through time is
therefore a direct observable of leverage-demand INSTABILITY: when a name's
premium whipsaws relative to its own trailing norm, its funding expectations
are unstable, which happens when the standing book is crowded with fast
leveraged positioning that repeatedly decouples mark from index. Names in this
state carry an unwind overhang: deleveraging and liquidation flow hits the
perp side repeatedly over subsequent funding settlements, so the HIGH
premium-vol cross-section underperforms over the following week, while LOW
premium-vol names (stable funding expectations, uncrowded books, cheap
continuity) outperform relatively. Economic counterparty: crowded fast
leverage (forced seller/buyer on deleveraging) versus the stability-demanding
holder who avoids or is compensated for bearing unwind-flow exposure. Why the
edge can exist after costs: the conditioning statistic is a slowly-moving
30d-scale regime variable producing low-churn weekly books whose gross effect
must clear weekly round-trip costs under the frozen schedule or the family is
rejected as cost-infeasible with no fee carve-out. Predicted sign: **long the
5 symbols with the LOWEST trailing 30d premium volatility** (perp
outperformance following premium-calm regimes). Honest two-sided note: classic
basis-risk/asset-pricing logic (Figlewski 1984; risk premium for bearing basis
instability) would predict the OPPOSITE sign; this proposal preregisters the
unwind-overhang sign only, and a falsified sign must never be flipped (that
would be the forbidden OILEV-V2/LOT rescue pattern). Null that kills it:
premium volatility carries no incremental cross-sectional information beyond
price volatility — observed as anchor excess <= 0 in >= 2/3 folds. Funding
NEVER enters the signal in any arm; it is charged only as a holding cost.

## 2. Falsifiable prediction

The anchor arm (PREMVOL-30D) must, after BASE costs under the remediated
kernel: (a) earn positive buy-and-hold-BTC-matched excess in >= 2/3
chronological folds; (b) earn positive BTC-beta-context (beta-adjusted) excess
in >= 2/3 folds; (c) pass all frozen Stage-A gates; (d) be supported by the
neighbour (PREMVOL-90D: same sign, same excess gates); and (e) NOT be
reproduced by the causal negative control (PRICEVOL-30D) under the
preregistered rule of section 6.

**FALSIFIED if any of:** excess <= 0 in >= 2 folds on either gate; PRICEVOL-30D
reproduces the anchor (rule in section 6); the 90d neighbour fails to show the
same-sign positive excess; any Stage-A gate fails; the drop-one perturbation is
vacuous or flips the family verdict; the cost floor is breached in base or
stress. Any single falsifier rejects the family. No window retune, sign flip,
cost exemption or universe carve-out may be attempted afterwards — such a
rescue is itself forbidden (inventory rule).

## 3. Literature pointers

Retrieval disclosure (binding honesty note): this D1 lane is FORBIDDEN network
fetches by its cycle instructions, so unlike V13 no query log or retrieval UTC
is claimed. Citations below are from prior model knowledge, each flagged
verified-confidence or thin. A9-F/A7-N should re-verify before selection.

| # | Citation | Confidence + use |
|---|----------|------------------|
| L1 | Figlewski, S. (1984), "Hedging Performance and Basis Risk in Stock Index Futures", Journal of Finance 39(3), 657–664. | HIGH. Establishes basis (futures-cash differential) variance as a risk dimension DISTINCT from outright price volatility. Frame anchor: premium volatility is a separable second-moment statistic, not a rescaled price vol. REJECT as template: equity index futures hedging, no perp conditioning study. |
| L2 | He, S., Manela, A., Ross, O. & von Wachter, V. (2022), "Fundamentals of Perpetual Futures", arXiv:2205.09217. | HIGH (existence, from knowledge; exact arXiv id re-verify). Perp premium = discounted expected future funding; premium second moments therefore measure funding-expectation instability — the premise linking premium vol to leverage-demand instability. REJECT as template: pricing theory, no cross-sectional after-cost test. |
| L3 | Makarov, I. & Schoar, A. (2020), "Trading and Arbitrage in Cryptocurrency Markets", Journal of Financial Economics 135(2), 293–319. | HIGH. Limited arbitrage capital leaves crypto relative-value deviations persistent and unstable; supports that premium instability is a slow-moving state variable, not noise. REJECT as template: venue-arbitrage measurement, no trading rule. |
| L4 | Nagel, S. (2012), "Evaporating Liquidity", Review of Financial Studies 25(7), 2005–2039. | HIGH. Funding-liquidity contraction degrades liquidity-provision capacity — the channel through which crowded, unstable books impose unwind flow on the perp side. Caveat: return-based measurement; PREMVOL's conditioning is premium-series-based. |
| L5 | Bessembinder, J. (1992), RFS 5(4) 637–667; De Roon, Nijman & Veld (2000), JF 55(3). | HIGH. Futures premia carry positioning-structure components beyond beta — the general frame that non-price positioning state variables can be priced. Caveat: no hedger/speculator classification in the authorized data; premium vol is a coarse observable proxy. |

**Honest thinness statement:** no published study conditioning cross-sectional
crypto perp returns on PREMIUM volatility (as distinct from price volatility)
is known to this agent. The literature directly on point is thin to absent;
prior uncertainty is high; the preregistered falsification gates, not the
priors, decide.

## 4. PIT observable — EVIDENCED availability stamp

**Dataset authority cited in full:** `research/control/v14_run/p1_a3/availability_evidence_table.json` (A3, generated 2026-09-04T23:42:17Z), source_id
`basis_mark_index_derivable_route`, classification **EVIDENCED_AVAILABLE**,
classification basis: relative to the 15m conditioning clock over the screen
window, rows exist at screen start (2025-08-22T00:00Z) for all 4 probed symbols
on all three routes, at screen end, and back to listing era (BTC first rows
2019-12); documented semantics archived (provider pages via Internet Archive
snapshots). Corroborating route `basis_futures_data` (/futures/data/basis,
fields `basis`, `basisRate`, `annualizedBasisRate`) is likewise
EVIDENCED_AVAILABLE with measured anchors at 2024-08-20 and 2023-01-01;
documented-vs-measured discrepancy D1 recorded with resolution "D2/A9-F must
re-verify before any scored use". NOT_RUN/UNAVAILABLE is never inferred from
silence (L-V12-5).

Primary observable (frozen): **`/fapi/v1/premiumIndexKlines`, field `close`
of the 15m premium-index bucket** — a relative perp-vs-index premium rate,
scale-free across symbols. Param style `symbol=`; `limit` max 1500 (documented
weight table archived). The derivable route `/fapi/v1/markPriceKlines`
(`symbol=`) and `/fapi/v1/indexPriceKlines` (**requires `pair=`; `symbol=`
measured HTTP 400 — evidence-table discrepancy D2**) is reserved as the
preregistered integrity cross-check, never a signal input. The
`/futures/data/basis` endpoint is NOT the signal input (period-aligned bucket
stamps with no stated update lag — weaker PIT class than kline open-time
stamping); its EVIDENCED_AVAILABLE status is cited as corroboration, and its
measured pagination quirk (backward walk repeats the latest page; forward
startTime pagination or point anchors honor ranges exactly) is recorded for
the staging plan.

Availability semantics (frozen PIT authority, p_freeze_v14): kline buckets are
stamped by OPEN time ("Klines are uniquely identified by their open time",
archived doc excerpts); a bucket's close value is complete only at close time
(bar-close availability class). **Frozen lag convention for this family: a
premium bucket with open time o and interval I = 15m is readable at decision
stamp T iff o + I < T — only fully-closed prior buckets, STRICTLY before the
stamp.** At Monday 00:00:00Z the last readable bucket is the one closing
23:45:00Z Sunday; the 23:45→00:00 bucket is excluded to leave zero margin for
stamp jitter (stricter than the frozen `close_time <= T` bound, never looser).
A decision at T can never read a row whose `available_time_utc > T`; retrieval
time never substitutes for availability (fusion `VintageSeries.select`).

Signal definition (anchor): with P_s(t) the premium-index close of the last
readable bucket at t, over the trailing 30d of strictly-closed prior buckets,

`sigma_prem_s(T) = std{ P_s(t_i) − P_s(t_{i−1}) }` over all consecutive
15m-bucket premium changes in the window

— a standardized SECOND MOMENT of the premium series. No premium level, no
cross-sectional dispersion, no price return, no OI, no volume and no funding
term enters the ranking. (Standardization across symbols is unnecessary: the
premium kline is already a relative rate.)

## 5. Universe, warmup, decision clock, holding, fills

Conform to frozen conventions: universe eligibility per V12 selection_freeze
authority (cited in p_freeze_v14, sha256 0b3b0865…); folds F0/F1/F2 with 1-day
purge; blind-S0 screen window 2025-08-22..2026-08-21; warmup inside the
authorized window 2024-08-20..2026-08-21.

- **Universe**: the 20 frozen required symbols (data_manifest required_symbol_set:
  1000PEPE, AAVE, ACE, ADA, AVAX, BCH, BNB, BOME, BTC, DOGE, ENA, ETH, LINK,
  NEAR, ONG, SOL, SUI, WLD, XRP, ZEC — all USDT pairs) MINUS BTCUSDT
  (benchmark/context only) = 19 tradable USD-M perpetuals. Per-stamp
  eligibility: a complete trailing premium-kline history — strictly-closed
  buckets covering 30d (anchor) / 90d (neighbour) vol window + 90d beta —
  with stamps <= T. Ineligible symbols excluded that stamp; the book
  renormalizes at equal weight 1/N; N >= 4 satisfies |w| <= 0.30 by
  construction; N < 4 scales gross down. Coverage honesty: P2 measured
  screen-start/end anchors on 4 symbols (BTC/ETH/SOL/XRP); the remaining 15
  tradable names inherit the same EVIDENCED_AVAILABLE classification but their
  per-symbol anchors were not probed — A9-F re-verification at D2 is a named
  item, and any symbol lacking full coverage is excluded per-stamp,
  fail-closed, never synthesized (L-V12-5).
- **Warmup**: binding requirement 90d (BTC-beta context; equals the neighbour
  vol window), + 30d anchor vol window; satisfied entirely from authorized
  pre-screen history 2024-08-20..2025-08-22 (368 days) before the blind-S0
  window.
- **Decision clock**: every Monday 00:00:00Z (weekly-or-slower; 52/365d <= the
  frozen 60 discretionary-decisions floor). Book carried unchanged between
  stamps; force-flat only at fold boundaries.
- **Folds**: F0 2025-08-22..2025-12-21, F1 2025-12-22..2026-04-21,
  F2 2026-04-22..2026-08-21, chronological with the frozen 1-day purge (first
  decision stamp of each fold strictly after the purge boundary).
- **One declared execution lag**: orders sized at T from strictly-closed prior
  buckets fill at the close of the first completed 15m bar with close time
  STRICTLY AFTER the decision stamp = Monday 00:15:00Z. Stressed schedule adds
  +1 event delay -> Monday 00:30:00Z.
- **Holding**: 7d intended; full target-book rebalance at each stamp only
  (satisfies the >= 3d median-holding floor). The 30d-scale regime statistic
  makes the held book low-churn (adjacent-week rank overlap expected high);
  churn is measured, never assumed.

## 6. Arms — anchor + neighbour + causal negative control (exactly 3)

| Arm | Construction | Role |
|-----|--------------|------|
| **PREMVOL-30D** (anchor) | Rank 19 eligible symbols ASCENDING on sigma_prem_s(T); long the 5 LOWEST premium-vol names at 0.20 each, gross 1.0. | The mechanism (premium-instability unwind overhang: low premium-vol outperforms). |
| **PREMVOL-90D** (neighbour) | Same mechanism, vol window 90d. | Justified adjacent parameterization: leverage-demand regimes persist at quarterly scale; 90d averages over more funding cycles and matches the frozen `neighbour_90d`-scale warmup; inside the authorized warmup window. |
| **PRICEVOL-30D** (causal negative control) | IDENTICAL pipeline applied to price: trailing 30d realized volatility of daily log returns from authorized 15m bars (PIT bar-close stamps); rank ascending; long the 5 LOWEST price-vol names. | Closest rival explanation: "low premium-vol names outperform simply because they are low-volatility names" — plain vol-level sorting, which is a measured shadow-adjacent rival (stocks V4 vol-level control; V12 BAB lineage). The rival is deliberately placed in the CONTROL seat, never proposed as the mechanism. |

**Preregistered control rule (the control MUST NOT reproduce the anchor):**
control reproduction is defined as: the PRICEVOL-30D arm passes after-cost
expectancy > 0 AND its per-fold buy-and-hold-excess SIGNS match the anchor's
in >= 2/3 folds. If reproduction occurs, the causal attribution FAILS: the
residual anchor edge belongs to ordinary price-vol sorting, not premium
instability, and **BASISDYN-PREMVOL is INELIGIBLE for selection even if the
anchor itself passes every Stage-A gate.** The control arm tests a rival; it
is never promotable from this proposal.

## 7. Incremental test (benchmark / BTC-beta context)

- **Buy-and-hold benchmark**: BTCUSDT buy-and-hold at matched gross from the
  same authorized bars under the same fusion availability stamps, per-fold
  weekly excess.
- **BTC-beta context**: trailing 90d daily beta of the arm vs BTC (frozen
  `beta_90d` warmup, PIT-stamped authorized bars); beta-adjusted excess per
  fold.
- **Gate (frozen)**: BOTH excess measures positive in >= 2/3 folds.
- **What incremental means for this family specifically**: the premium's
  second-moment statistic must carry return information BEYOND (i) BTC
  direction (beta gate) and (ii) the two rival conditionings placed in the
  control seat: price volatility (section 6) polices "plain low-vol sorting";
  the premium LEVEL and its cross-sectional dispersion are deliberately absent
  from every arm signal — a level/dispersion-conditioned basis claim belongs
  to AXIS-1/A5 and is not this family. A raw pass with a beta-context failure
  is BTC beta in disguise -> REJECT (mission Q2 demands incremental
  information, not leveraged beta).

## 8. Costs under the REMEDIATED kernel, turnover, sample floors

- **Costs on fills ONLY** — never per holding-day, never per stamp on open
  positions (L-V14-0 remediation, pinned by tests/test_v14_p1_cost_once.py);
  real perp-metadata tick sizes (no uniform stubs); native funding settlements
  while held enter EXACTLY ONCE as a COST, never a signal or sidecar; scored
  cells report cost broken out by fills vs holding terms.
- **Base schedule**: generic adapter fee + slippage per fill. **Stress**: fee
  x1.5, +2 adverse ticks (instrument tick sizes), +1 event delay (fill moves
  00:15Z -> 00:30Z).
- **Turnover floors (frozen, binding, never relaxed)**: <= 60 discretionary
  decisions/365d (52 scheduled, ~50 live after purge); median intended holding
  >= 3d (7d); base cost drag <= 8%/yr of gross; stressed <= 12%; no symbol
  > 25% of one-way turnover (equal 0.20 weights bound each name at ~20% of
  gross per side by construction); |w| <= 0.30 at every stamp; gross <= 1.0.
  A 30d-scale regime statistic should churn less than a 72h-change statistic;
  churn is nonetheless MEASURED at D2 feasibility, and if the drag floors fail
  the family is REJECTED cost-infeasible (failure table), never rescued.
- **Sample floors (numeric)**: >= 48 live decision stamps with non-empty books
  over the screen window (of ~50 post-purge scheduled); exactly 5 held names
  per live stamp when N >= 4 eligible, i.e. >= 240 symbol-holding-weeks per
  arm; a zero-position baseline is REFUSED at publication (L-V11-4); any arm
  below the floor is refused, not scored.

## 9. Drop-one design (non-vacuous, held max-|weight|)

At each decision stamp the perturbed schedule drops the single HELD symbol
with MAXIMUM |weight| for that holding span. With equal weights all 5 held
names tie at |w| = 0.20; the tie-break is frozen ex ante and outcome-blind:
**lexicographically first symbol id among held max-|weight| names.** The
remaining 4 names renormalize to 0.25 each (<= 0.30 cap). Non-vacuousness: the
dropped symbol must have held positions over the span (guaranteed — drops are
selected only from held names) and the perturbation must change the book
(5 names -> 4 renormalized). Family gates require non-vacuous drop-one symbol
survival AND fold survival (dropping any single fold must not flip the family
verdict) — L-V11-7 discipline.

## 10. Failure interpretation

| Failure mode | Meaning | Action |
|---|---|---|
| Cost floor breached (base or stress) | Instability-avoidance not harvestable at frozen costs | REJECT cost-infeasible; no fee exemption, no clock retune (rescue forbidden). |
| Anchor excess <= 0 in >= 2 folds | Unwind-overhang sign wrong on this window (consistent with the classic risk-premium reading of basis risk, L1) | REJECT; sign flip forbidden — the OPPOSITE sign is never re-proposed from this outcome (L-V12-1/L-V11-3 pattern). |
| PRICEVOL-30D reproduces the anchor | Attribution failure: edge is plain price-vol sorting (shadow-adjacent rival), not premium instability | REJECT as INELIGIBLE; a vol-level claim can never be re-proposed from this outcome. |
| Neighbour fails while anchor passes | Parameter fragility across vol windows | REJECT family; neighbour never promoted alone. |
| Beta-context fails while raw passes | BTC beta in disguise (low-vol longs = low-beta longs) | REJECT — no incremental information. |
| Drop-one vacuous or verdict flips | Not robust to held-book composition | REJECT. |
| Premium-kline coverage gaps force N < 4 persistently | Data problem, not economics | Report as BLOCKED_DATA candidate; no redesign inside this cycle (L-V12-5). |

Mechanism falsification (not merely losing money): if per-fold anchor excess
is negative while PRICEVOL-30D ALSO fails, the specific observed pattern —
neither premium volatility nor price volatility ranks carry positive weekly
excess on this universe — falsifies the claimed unwind-overhang channel itself
on this window, independent of profitability.

## 11. Source-to-test map (endpoint -> field -> staging plan; NO downloads now)

| Field (endpoint) | Test use |
|---|---|
| `premiumIndexKlines.close` (15m, `symbol=`) | Anchor + neighbour signal ONLY: sigma_prem over trailing 30d/90d of strictly-closed prior buckets. |
| staged 15m bars (`crypto_bars`, bar-close availability) | PRICEVOL-30D causal control's daily log-return realized vol; fill marks; BTC buy-and-hold benchmark; 90d beta context. |
| `markPriceKlines.close` / `indexPriceKlines.close` (15m; `pair=` for index per discrepancy D2) | Preregistered integrity cross-check for A9-F/I-lane (premium route coherence); never a signal. |
| `crypto_funding` (`fundingTime` settlement stamp) | Holding cost ONLY, applied to `[ts_opened, ts_closed]`, settled natively exactly once. |
| instrument metadata tick sizes | Stress slippage floor (+2 ticks), real per-symbol ticks. |
| BTCUSDT bars | Benchmark + beta only; never tradable in the book. |

**Staging plan (V14-I; nothing fetched in D1)**: symbols = 19 tradable
(basis-premium route); window = 2024-08-20..2026-08-21 (warmup + screen);
granularity = 15m (the P2-probed depth); ~70,176 buckets/symbol at 96/day =
47 pages at limit 1500 -> ~893 requests for the premium route (the bars,
funding and metadata are already authorized staged sets — no new pull);
optional cross-check route +2 x 893 only if A9-F requires it; documented kline
weight table ([500,1000] -> 5 units/request, archived) and the A3 lane pacing
reference (0.55s sleep, observed max 48 weight/min) bound the pull; forward
`startTime` pagination only.

## 12. Forbidden-packet self-check

Inspected classes (research/control/v14_run/forbidden_family_inventory.json)
and verdicts:

- **V1-VOLCOMP (closest class — honest proximity note)**: V1-VOLCOMP is
  volatility-COMPRESSION BREAKOUT CONTINUATION on price (plus V9 dollar-volume
  shock continuation): low vol precedes an upward continuation bet.
  PREMVOL conditions on the volatility of the PREMIUM series (not price), has
  NO breakout premise and NO continuation direction claim, and predicts
  cross-sectional relative performance (low premium-vol outperforms), not a
  directional event. The vol variable lives in a different series entirely;
  the price-vol rival sits in the CONTROL seat with a must-not-reproduce rule.
- **V12-BAB-LOWBETA (second-closest — honest proximity note)**: BAB sorted on
  90d BETA and died after native costs/funding. PREMVOL never sorts on beta;
  beta appears only in the frozen context gate. PRICEVOL-30D in the control
  seat polices the residual "it's just low-vol/low-beta sorting" attribution;
  if it reproduces, this proposal is rejected, so it cannot profit from the
  BAB corpse.
- **V6/V1-CARRY-FUNDING**: funding never enters any arm signal (cost only); no
  carry yield is collected or faded; the premium SECOND MOMENT is not a funding
  level or funding change. Declared outcome-blind novelty condition: if A7-N
  measures |rho| > 0.20 between the PREMVOL-30D weekly rank and the frozen V6
  CARRY-3D rank OR its REVERSE-3D control, INELIGIBLE.
- **WEEKLY-REVERSAL / MR-RESCUE**: no past-return term of any horizon in the
  anchor or neighbour signal; no reversal or renamed-rejected-baseline claim.
- **V12-OILEV-V2 / V11-OILEVER-DELEV / V13-OITD**: no open-interest term in
  any arm (level, flow, term structure, positioning-duration); not a sign
  flip, horizon tweak, carve-out or renaming of any OI family. Declared
  novelty condition: |rho| > 0.20 vs the frozen OILEV-V2 anchor OR its
  inverted control -> INELIGIBLE.
- **V13-LIQEPIS (inspected per instruction)**: LIQEPIS conditioned on the
  time-SHAPE of turnover (burst concentration of dollar volume). PREMVOL uses
  NO volume, turnover or liquidity term anywhere; its second moment is of the
  premium series. Different input series, different statistic, different
  mechanism; no liquidity-episode story is claimed.
- **V11-ILLIQ-AMIHUD / V10-M01**: no Amihud ratio, no price impact, no
  aggressor/imbalance flow.
- **V9-TS-TREND / V4-XSECT-MOM / V8R-XSECT-REVERSAL / V11-LOTTERY-MAX-SKEW**:
  no price-return moment of any horizon (return vol appears ONLY in the
  control arm, operationalizing the rival the mechanism must defeat).
- **V12-ILLIQ-REPLICATION**: not the frozen replication brief; no window
  substitution.
- **DATA-GATED**: uses only the P2 EVIDENCED_AVAILABLE basis/mark-index route
  + already-authorized bars/funding/metadata; no new source, key, signup;
  zero downloads performed in D1.
- **Shadow region: NOT entered.** The predicted sign derives from the
  unwind-overhang mechanism, not from any measured control-arm observation
  (inverted OI-flow +0.758, V11 LOT inversion, vol-level sorting); the vol-
  sorting shadow-adjacent rival is deliberately placed in the causal control
  seat — the opposite of promoting it. Preregistered EXPLORATORY.
- **Wave diversity honesty**: both files in this lane sit on AXIS-2; if this
  family is selected, the sibling BASISDYN-PREMREV is a same-cluster second
  family and is INELIGIBLE under plan Section 1.2 even if otherwise clean.
  Within the lane, PREMVOL (second moment, 30d/90d regime scale) and PREMREV
  (first difference, 24h/72h flow scale) are distinct mechanisms and are
  expected to rank anti-correlated, not duplicates.

## 13. Outcome-blind attestation

```
OUTCOME-BLIND ATTESTATION
lane: d1-a6-proposals  proposal: A14-V14-A6-BASISDYN-PREMVOL
cycle: CRYPTO-V14  wave SHA: c3e3c90561efc972c487a99951ca0f6031ab4fa34907d1c10890d1795b4da4a8
I wrote this mechanism and its falsification conditions before any return,
metric or ranking exists, without access to any per-arm outcome file, and I
will not modify this proposal after outcomes exist.
utc: 2026-09-05T00:32:32Z  agent: A6 (d1-a6-proposals)
```
