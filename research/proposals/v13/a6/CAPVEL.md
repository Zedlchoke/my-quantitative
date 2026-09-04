# A13-V13-A6-CAPVEL — Committed-Capital Book-Turnover Premium

lane: a6 (outcome-blind proposal, Phase D1) — cycle CRYPTO-V13
schema: v13_proposal_v1 — sibling JSON: `CAPVEL.json` (same content, structured)

---

## 1. Hypothesis ID + mechanism

**Hypothesis ID: `A13-V13-A6-CAPVEL`**

Mechanism (own words): on Binance USD-M perpetuals, the ratio of traded volume
to open interest — the **book turnover** — measures how many days of average
trading are needed to rotate the standing position stock. When daily volume is
large relative to the open-interest stock, price discovery is dominated by
short-horizon flow (intraday leverage churn, scalping) whose holding horizon
ends within hours; the marginal price-setter must exit into the same thin
standing book it helped create, market-making inventory turns rapidly and
carries high adverse selection per unit of inventory, and the standing
open-interest stock provides little committed two-sided interest for liquidity
providers to lay inventory against. When volume is small relative to the
standing stock, the book is dominated by **committed capital** that has already
absorbed its entry impact, does not face self-unwinding pressure, and provides
standing two-sided depth. Economic counterparty: short-horizon liquidity
demanders versus committed position holders and the market makers who finance
inventory against the standing stock. Why the edge can exist: the composition
of holding horizons in a derivatives market is a persistent structural property
(28d-scale), not news, and the literature on positioning-structure premia
(Bessembinder 1992; De Roon–Nijman–Veld 2000) shows futures risk premia carry a
positioning-structure component that is distinct from systematic beta risk.
Expected sign: **the 5 symbols with the LOWEST 28d book turnover outperform the
cross-section mean and BTC buy-and-hold after costs** (a selection premium for
committed-capital names). Funding never appears in the signal; it is a
holding cost only.

## 2. Falsifiable prediction

The anchor arm (CAPVEL-28D) must, after BASE costs: (a) earn positive
buy-and-hold-BTC-matched excess in >= 2/3 chronological folds; (b) earn
positive BTC-beta-context (beta-adjusted) excess in >= 2/3 folds; (c) pass all
frozen Stage-A gates; (d) be supported by the neighbour (CAPVEL-56D: same sign,
same excess gates); and (e) NOT be reproduced by the causal control
(VOLLEVEL-28D) under the preregistered rule of section 6.

**FALSIFIED if any of:** excess <= 0 in >= 2 folds on either gate; the
volume-level control reproduces the anchor (rule in section 6); the 56d
neighbour fails to show the same-sign positive excess; any Stage-A gate fails;
the drop-one perturbation is vacuous or flips the family verdict. Any single
falsifier rejects the family. No window retune, sign flip, cost exemption or
universe carve-out may be attempted afterwards — such a rescue is itself
forbidden (inventory rule).

## 3. Literature (queries + retrieval UTC logged; pass completed BEFORE any candidate return would have been computed — none was)

| # | Query | Retrieval UTC | Verdict + reason |
|---|-------|---------------|------------------|
| L1 | "open interest to volume ratio cryptocurrency perpetual futures return predictability" | 2026-09-04T11:10:27Z | ACCEPT: Giagkiozis & Said, "Reconciling Open Interest with Traded Volume in Perpetual Swaps" (Ledger / arXiv 2310.14973) — OI is systematically misquoted by some large derivatives exchanges, severity varies by venue; direct transfer caveat for ANY OI-conditioned signal. REJECT: BitMEX/MetaMask/Coinbase/TradingView practitioner pages — educational, no falsifiable claims. |
| L2 | "bitcoin futures open interest price movement predictability cross-section" | 2026-09-04T11:11:50Z | ACCEPT (context only): ML mid-price forecasting on BTC futures reaches 55–65% daily/minute accuracy (PMC8296834) — OI-family features carry information. REJECT as design template: ML classification, no PIT discipline, no cost model, not cross-sectional. |
| L3 | "trading volume concentration Herfindahl index stock returns informed trading liquidity" | 2026-09-04T11:15:12Z | ACCEPT (method provenance, for sibling LIQPRO): MDPI JRFM 17(8):325 surveys HHI/Gini volume-concentration measures; IJEFR 2021 finds Gini volume-concentration events followed by abnormal returns in equities. REJECT for direct transfer: equities, event-study design, no perp OI/funding structure. |
| L4 | "market maker inventory risk premium liquidity provision returns asset pricing" | 2026-09-04T11:17:00Z | ACCEPT: "Returns from liquidity provision in cryptocurrency markets" (Journal of Banking & Finance, 2025, S0378426625000317) — a liquidity-provision premium exists in crypto markets. CRITICAL caveat: it is operationalized via short-reversal returns; CAPVEL conditions on NO return term, so the channel is asserted, not guaranteed — the falsification tests carry the weight. |
| L5 | "hedging pressure risk premium futures markets open interest theory Bessembinder" | 2026-09-04T11:17:21Z | ACCEPT: Bessembinder 1992 (RFS 5(4) 637–667) — futures risk premia contain a hedging-pressure (positioning) component beyond systematic risk; De Roon–Nijman–Veld 2000 (JF 55(3)); Basu & Miffre 2013 (JBF) price normalized hedging pressure cross-sectionally. REJECT for direct operationalization: CFTC-style trader classification is unavailable in the authorized crypto data — CAPVEL proxies positioning structure with the observable volume/OI aggregate only. |
| L6 | "bitcoin perpetual futures liquidation cascade open interest deleveraging empirical study" | 2026-09-04T11:19:05Z | ACCEPT (context): arXiv 2608.03616 — seven perp liquidation cascades 2022–2025; OI "clears hard" after cascades; Oct 2025 cascade anatomy (ResearchGate 396645981). REJECT as mechanism template: those designs condition on OI CHANGE (flow/deleveraging) — that family is forbidden this cycle (V12-OILEV-V2 / V11-OILEVER-DELEV); CAPVEL conditions on a stock-relative LEVEL ratio and never on OI differences. |
| L7 | "Nagel evaporating liquidity short-term reversal returns market maker compensation" | 2026-09-04T11:20:10Z | ACCEPT: Nagel 2012 (RFS 25(7) 2005–2039) — liquidity-provision compensation is priced and rises when funding liquidity contracts. Used only as the economic-channel anchor; its measurement is return-based, ours is not. |
| L8 | WebFetch arXiv 2310.14973 abstract | 2026-09-04T11:21:30Z | ACCEPT: primary-source confirmation of the OI-misquotation claim (implausible OI on some venues; delayed liquidation messages on others; validate OI against traded volume). |

**Transfer caveats (binding for interpretation):** (1) equities-to-perp transfer:
24/7 trading, no auction structure, and an explicit open-interest stock that
equities lack; concentration/churn levels are not comparable across the two
settings. (2) OI reporting quality (Giagkiozis–Said): single-venue (Binance
USD-M) design removes cross-venue artifacts but not reporting error; we
therefore use OI only inside slowly-varying 28d/56d aggregates, never as a
fast signal. (3) The crypto liquidity-provision premium (L4) is measured
through reversal strategies; CAPVEL's signal is return-free, so it tests a
different, stricter claim. (4) Hedging-pressure theory (L5) requires hedger vs
speculator classification that does not exist in the authorized data; CAPVEL's
book-turnover proxy is a coarser structural statistic — the hypothesis is a
genuine test, not a replication. (5) No published cross-sectional study of
volume/OI churn on Binance USD-M was found (L1, L2): prior uncertainty is
high and the falsification gates, not the priors, decide.

## 4. PIT observable (fusion-record availability semantics)

Decision stamps are Monday 00:00:00Z. A decision at T reads ONLY records with
`available_time_utc <= T` (retrieval time never substitutes for availability;
as-of selection via the frozen fusion `VintageSeries.select` rank
`available_time_utc <= vintage_time_utc <= retrieved_time_utc`):

- `crypto_bars` fields `volume`, `close` (15m, unit BASE/USDT): available at the
  bar close boundary (`ts_event`); a bar is completed at T iff `T >= ts_event`.
  Used for daily traded base volume (signal numerator) and dollar-volume
  deflation (control), benchmark series, and beta context.
- `crypto_open_interest` field `open_interest` (unit BASE): available at the OI
  snapshot stamp (`timestamp` / `create_time`). Daily cadence; the last
  snapshot available at Monday 00:00Z is Sunday's. Used ONLY as the signal
  denominator — never differenced.
- `crypto_mark_price` field `mark_price`: available at the mark snapshot stamp;
  cost marks only, never a signal input.
- `crypto_funding` field `funding_rate`: available at the settlement stamp
  (`fundingTime`); mixed 8h/4h/1h cadences; applied to a holding span only when
  the settlement lies in `[ts_opened, ts_closed]`; COST ONLY.
- Instrument tick sizes (metadata): slippage floor for the stress schedule.

Signal definition (anchor): `book_turnover_t,s = mean_daily_traded_base_volume(T-28d..T) / mean_daily_OI(T-28d..T)`
— a dimensionless, sign-free, scale-free LEVEL ratio. Cross-sectionally ranked;
no price-difference, no return, no funding term enters the ranking.

## 5. Universe, warmup, decision clock, holding, fills

- **Universe**: the 20 frozen required symbols MINUS BTCUSDT (benchmark/context
  only) = 19 tradable USD-M perpetuals. Per-stamp eligibility: complete
  trailing 28d (anchor) / 56d (neighbour) of completed 15m bars AND >= 26
  (>= 52) daily OI snapshots with stamps <= T. Ineligible symbols are excluded
  that stamp; the book renormalizes across eligible names with equal weights
  1/N (N = eligible count); with N >= 4 the weight cap 0.30 is satisfied by
  construction (1/4 = 0.25); with N < 4 gross is scaled down to keep |w| <= 0.30
  at every stamp by construction.
- **Warmup**: binding requirement 90d (BTC-beta context), per the frozen
  warmup table (`anchor_28d`, `neighbour_56d`, `beta_90d`, `binding_max: 90`);
  satisfied from authorized pre-screen history 2024-08-20..2025-08-22 before
  the blind-S0 window 2025-08-22..2026-08-21.
- **Decision clock**: every Monday 00:00:00Z (weekly-or-slower; 52/365d <= the
  frozen 60 discretionary-decisions floor). Book carried unchanged between
  stamps; forced-flat only at fold boundaries (frozen convention).
- **Folds**: F0/F1/F2 chronological over the blind-S0 screen window
  2025-08-22..2026-08-21 with the frozen 1-day purge (first decision stamp of
  each fold strictly after the purge boundary).
- **One declared execution lag**: orders fill at the close of the first
  completed 15m bar with close time STRICTLY AFTER the decision stamp, i.e.
  Monday 00:15:00Z. Stressed schedule adds +1 event delay -> Monday 00:30:00Z.
- **Holding**: 7d intended (weekly cadence; satisfies the >= 3d median-holding
  floor); full target-book rebalance at each stamp only.

## 6. Arms — anchor + neighbour + causal negative control (exactly 3)

| Arm | Construction | Role |
|-----|--------------|------|
| **CAPVEL-28D** (anchor) | Rank 19 eligible symbols ascending on `book_turnover_28d`; long the 5 lowest at 0.20 each, gross 1.0. | The mechanism. |
| **CAPVEL-56D** (neighbour) | Same mechanism, formation window 56d. | Justified parameter: positioning-regime persistence is multi-scale and a 56d aggregate further dilutes OI reporting noise (L1/L8 caveat) while staying inside the frozen warmup table (`neighbour_56d`). |
| **VOLLEVEL-28D** (causal negative control) | IDENTICAL pipeline, ranking instead on the log 28d mean daily DOLLAR-VOLUME level alone (the OI denominator removed); long the 5 lowest-volume names. | Closest rival explanation: "the edge is just avoiding big/active (size-liquidity) names", not positioning-relative churn. |

**Preregistered control rule (the control MUST NOT reproduce the anchor):**
control reproduction is defined as: the VOLLEVEL-28D arm passes after-cost
expectancy > 0 AND its per-fold buy-and-hold-excess SIGNS match the anchor's
in >= 2/3 folds. If reproduction occurs, the causal attribution FAILS: any
residual anchor edge belongs to the volume-level/size rival effect, not to
positioning-relative book turnover, and **CAPVEL is INELIGIBLE for selection
even if the anchor itself passes every Stage-A gate.**

## 7. Incremental test vs buy-and-hold and BTC-beta context

- **Buy-and-hold benchmark**: BTCUSDT buy-and-hold at matched gross from the
  same authorized bars under the same fusion availability stamps, evaluated
  per fold on the arm's weekly excess.
- **BTC-beta context**: trailing 90d daily beta of the arm vs BTC (estimated
  from authorized bars with PIT stamps; warmup per frozen `beta_90d`),
  beta-adjusted excess per fold.
- **Gate (frozen)**: BOTH excess measures positive in >= 2/3 folds. A raw
  pass with a beta-context failure means the returns are BTC beta in disguise
  -> REJECT (mission Q2 demands incremental information, not leveraged beta).

## 8. Costs, floors, concentration, drop-one

- **Base costs**: generic adapter fee + slippage on fills only; native funding
  settlements while held enter exactly once as a COST (never a signal, never a
  sidecar). **Stress**: fee x1.5, +2 adverse ticks (instrument tick sizes), +1
  event delay.
- **Floors (frozen)**: <= 60 discretionary decisions/365d (52 scheduled);
  median intended holding >= 3d (7d); base cost drag <= 8%/yr of gross;
  stressed <= 12%; no symbol > 25% of one-way turnover; |w| <= 0.30 at every
  stamp by construction (equal weights 0.20 over 5 names); gross <= 1.0.
- **Concentration**: largest-symbol positive-PnL share <= 0.70 is enforced as
  the frozen Stage-A concentration gate; the equal-weight quintile construction
  structurally bounds the per-swap notional at 0.20 of gross. Residual
  single-symbol turnover-share risk is DETECTED by the frozen feasibility
  floor, never relaxed.
- **Sample floors**: 52 scheduled stamps/yr; the frozen minimum-activity
  convention applies (a zero-position baseline is refused at publication); a
  stamp with fewer than 4 eligible symbols carries the book unchanged and is
  still counted as a decision.
- **Drop-one design (frozen)**: at each decision stamp the perturbed schedule
  drops the single HELD symbol with MAXIMUM |weight| for that holding span; a
  flat book makes the stamp's drop VACUOUS. Family gates require non-vacuous
  drop-one symbol survival AND fold survival (dropping any single fold must not
  flip the family verdict).

## 9. Failure interpretation

| Failure mode | Meaning | Action |
|---|---|---|
| Cost floor breached (base or stress) | Weekly selection churn too expensive at frozen costs | REJECT as cost-infeasible; no fee retune/exemption. |
| Anchor excess <= 0 in >= 2 folds | Predicted sign wrong on this window | REJECT; sign flip forbidden (OILEV-V2/V6 rescue pattern). |
| VOLLEVEL-28D reproduces the anchor | Attribution failure: edge is volume-level, not positioning structure | REJECT CAPVEL as ineligible; a pure volume-level claim would need its own outcome-blind proposal, not this one. |
| Neighbour fails while anchor passes | Parameter fragility; mechanism unsupported | REJECT family; the neighbour may never be promoted alone. |
| Beta-context fails while raw passes | BTC beta in disguise | REJECT — no incremental information (mission Q2 unmet). |
| Drop-one vacuous or verdict flips | Not robust to held-book composition | REJECT. |
| Persistent OI coverage gaps force eligibility < 4 | Data problem, not economics | Report as BLOCKED_DATA candidate; no redesign inside this cycle. |

## 10. Source-to-test map (every input field -> exact test use)

| Field (dataset) | Test use |
|---|---|
| `bars.volume` + `bars.close` (`crypto_bars`, 15m) | Daily traded base volume and dollar-volume for the anchor/neighbour churn ranking (anchor numerator), the VOLLEVEL control's volume-level ranking, benchmark and beta-context series, fill marks. |
| `open_interest` (`crypto_open_interest`, daily) | Denominator of `book_turnover` only (LEVEL; never differenced) for anchor + neighbour. |
| `mark_price` (`crypto_mark_price`) | Cost/valuation marks only. |
| `funding_rate` (`crypto_funding`) | Holding cost only, applied to `[ts_opened, ts_closed]`. |
| tick sizes (instrument metadata) | Stress-slippage floor (+2 ticks). |
| BTCUSDT bars | Buy-and-hold benchmark + 90d beta context only; never tradable in the book. |

## 11. Ancestry map vs the forbidden inventory (why this is NOT a variant, inversion, rescue or renaming)

- **V12-OILEV-V2** (OI-deleveraging; sign falsified by its own inverted
  control): OILEV-V2 conditions on OI FLOW (deleveraging/change direction).
  CAPVEL contains NO OI difference or change term anywhere — OI enters only as
  a LEVEL denominator; the ranked quantity is volume/OI, whose sign carries no
  OI-direction information. Not a sign flip, horizon tweak, cap raise, universe
  carve-out, threshold relaxation or renaming. **Self-preregistered novelty
  condition (declared outcome-blind): if A7-N measures rank correlation
  |rho| > 0.20 between the CAPVEL weekly signal and the frozen OILEV-V2 anchor
  signal OR its inverted control on the common window, CAPVEL is INELIGIBLE.**
- **V11-OILEVER-DELEV**: same reasoning; no deleveraging-event conditioning;
  the 0.30 cap is respected by construction; no post-score renormalization.
- **V6/V1-CARRY-FUNDING**: funding never enters the signal (cost only); no
  crowding-premium-from-funding story; not a carry rescue.
- **V11-ILLIQ-AMIHUD**: Amihud is |return| / dollar-volume (price impact).
  CAPVEL has NO return term; its numerator is volume and its denominator is
  OI. Not a monotone transform, replication identity or variant.
- **V4-XSECT-MOM / V9-TS-TREND / V8R-XSECT-REVERSAL / WEEKLY-REVERSAL**: the
  signal contains no past-return term of any horizon.
- **V1-VOLCOMP (incl. V9 dollar-volume shock continuation)**: no compression,
  no breakout, no volume-spike event; the signal is a 28d mean LEVEL ratio
  ranked cross-sectionally, with no continuation premise.
- **V11-LOTTERY-MAX-SKEW**: no return-distribution moment (MAX/LOT/skew) used.
- **V12-BAB-LOWBETA**: no beta-sorted construction; beta appears only in the
  frozen context gate, never in the book.
- **V10-M01-AGGRESSOR-ABSORPTION**: no aggressor/trade-imbalance flow (not
  available in the authorized data and not used).
- **V12-ILLIQ-REPLICATION**: this is not the frozen replication brief; window
  substitution is not attempted.
- **DATA-GATED**: uses only the four authorized datasets + instrument metadata;
  no new source, key, signup or download.
- **Shadow region: NOT entered.** The predicted sign (long low-churn) is none
  of the measured shadow observations (inverted OI-flow +0.758, V11 LOT
  inversion, vol-level sorting control); the mechanism is stated in its own
  words, is preregistered EXPLORATORY (not confirmatory), and nevertheless
  carries its own causal negative control and the |rho| <= 0.20 novelty
  condition declared above.

## 12. Section 1.1 front-door disclosures

Not applicable — this proposal does NOT enter the shadow-effect region. The
section 1.1 disclosure requirement is answered explicitly: no part of CAPVEL's
sign claim derives from, or is justified by, a V12/V11 control-arm observation;
the family is preregistered exploratory; the causal control (section 6) and
novelty condition (section 11) are carried voluntarily.

## 13. Outcome-blind attestation

See the signed attestation block at the end of this file.

---

```
OUTCOME-BLIND ATTESTATION
lane: a6  proposal: A13-V13-A6-CAPVEL
I wrote this mechanism and its falsification conditions before computing any
return, metric or ranking, and without access to any scored artifact or
outcome file.
utc: 2026-09-04T11:17:21Z  agent: A6
```
