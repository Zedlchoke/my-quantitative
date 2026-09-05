# A14-V14-A5-BASISLV-WIDTHGATE — Cross-sectional premium-dispersion regime gate (information-content conditioning)

Lane: a5 (d1-a5-proposals) | Cycle: CRYPTO-V14 Phase D1 | AXIS-1 basis level / carry structure
Wave SHA: `c3e3c90561efc972c487a99951ca0f6031ab4fa34907d1c10890d1795b4da4a8`
Outcome-blind proposal: no computation performed, no per-arm outcome file accessed, none sought.
Status: NEW mechanism, conditioning space = cross-sectional mark/index-vs-perp premium
DISPERSION across names as the conditioning state (the width of the crowding/carry premium
cross-section), gating a same-direction premium-level book. Dataset authority:
`research/control/v14_run/p1_a3/availability_evidence_table.json` — source
`basis_mark_index_derivable_route` (endpoints `/fapi/v1/markPriceKlines`,
`/fapi/v1/indexPriceKlines`, `/fapi/v1/premiumIndexKlines`) classified
**EVIDENCED_AVAILABLE** (measured rows at the 2025-08-22 screen start on all 4 probed symbols
on all three routes, screen end probed on BTCUSDT, listing-era first rows, open-time kline
stamping archived; discrepancy D2 — indexPriceKlines requires pair= — recorded and carried).

## 1. Hypothesis ID and mechanism

Hypothesis ID: `A14-V14-A5-BASISLV-WIDTHGATE`

The cross-sectional WIDTH of perp premia — the spread of per-symbol mark/index premium levels
across names at a decision stamp — measures how much of the market's premium state is
name-specific versus common. When premia are compressed across the cross-section, the premium
is essentially one market-wide leverage-sentiment factor: every perp carries nearly the same
gap to its index, differences between names are dominated by microstructure jitter, and a
cross-sectional premium rank holds no name-level information — such a book harvests only
costs and common-factor noise. When premia are wide, leverage demand is fragmented and
name-specific: individual names carry idiosyncratic crowded longs (or discounts) from
name-level attention, hedging imbalances, and per-name arbitrage capacity limits; the
cross-sectional ordering of premia then contains name-level unwind information (the R-squared
logic of Roll 1988 — name-specific variation is where name-specific pricing lives — applied
to the premium cross-section; the spread-breadth logic of Stambaugh, Yu & Yuan 2015 — wide
cross-sectional arbitrage spreads mark where mispricing is actionable).

Mechanism: scale a same-direction premium-level book (long the low-premium tier, short the
high-premium tier of the 28d mean mark/index premium) by the dispersion state — FULL weight in
stamps where the cross-sectional IQR of trailing mean premia exceeds the trailing median of
strictly-prior stamp IQRs (a median split with NO tuned constant), FLAT otherwise. The claim
is an information-CONTENT claim about WHEN the premium cross-section is informative, not a new
directional claim about the premium itself.

Predicted sign (declared ex ante): the GATED book earns positive BTC-beta-context excess in
>= 2/3 folds, and — the mechanism-specific sharpening — it earns MORE excess than the ungated
book in >= 2/3 folds (dispersion identifies the stamps where the premium ordering works).
Killing nulls: (a) the narrow-state gate control reproduces the anchor's incremental result —
dispersion direction carries no information; (b) the gated book fails the redundancy guard
(does not exceed the ungated book) — dispersion adds nothing beyond the level ranking and this
family is a redundant twin of `A14-V14-A5-BASISLV-PREMFADE` (cluster-padding guard, declared
ex ante).

Honest adjacency disclosure: this proposal and `BASISLV-PREMFADE` share the assigned AXIS-1
and the same inside book; they are distinct FALSIFIABLE mechanisms (level-unwind vs
dispersion-information-content), each with its own control that can kill it independently.
Under the plan's wave-diversity rule at most one family per lane can be selected anyway. If
A7-N measures them as one cluster, at most one proceeds — that is the designed outcome of the
diversity machinery, not a defect to engineer around.

## 2. Falsifiable prediction

After base costs, the `BASISLV-WIDTHGATE-28D` anchor earns positive BTC-beta-context weekly
excess in >= 2/3 frozen folds AND its excess exceeds the ungated premium-level book's excess
in >= 2/3 folds; the 56D neighbour supports the same pattern; the narrow-state control does
NOT reproduce. The hypothesis is FALSIFIED if any of: (a) the anchor's beta-context excess is
not positive in >= 2/3 folds; (b) the redundancy guard fails (gated excess <= ungated excess
in >= 2/3 folds) — dispersion carries no information beyond the level ranking; family
rejected even if the anchor is positive; (c) the narrow-state control (gate open in the
NARROW-dispersion state) ALSO passes the incremental gate — the direction of the dispersion
state carries no information; family rejected and the control never promotable; (d) the
neighbour flips the pattern (dispersion state is not persistent enough to condition on);
(e) the anchor passes base but fails stress (execution artifact); (f) price-only expectancy
<= 0 with total expectancy positive only via funding credits (carry-harvest artifact, same
declared clause as the sibling proposal).

## 3. Literature (citations from verified knowledge; transfer caveats)

No network fetch was performed in this lane (D1 hard constraint). Citations are canonical
works cited from verified model knowledge with full authors/venue; A9-F/D2 may verify at
audit. Direct literature on cross-sectional premium-dispersion gating in crypto perps is
THIN — stated honestly; the proposal is mechanism-driven with preregistered falsification.

| # | Citation | Role | Verdict + reason |
|---|----------|------|------------------|
| L1 | Roll (1988), "R²", Journal of Finance 43(2), 541-566 | Primary mechanism (analogy, declared) | ACCEPT as analogy only: low firm-specific return variation marks common-factor dominance where selection carries no name information; high name-specific variation marks where it does. Applied here to the premium cross-section rather than returns. |
| L2 | Stambaugh, Yu & Yuan (2015), "Arbitrage Asymmetry and the Idiosyncratic Volatility Puzzle", Journal of Finance 70(5), 1903-1948 | Primary mechanism | ACCEPT: mispricing lives in the wide end of the cross-sectional arbitrage-spread distribution; supports that a WIDE premium cross-section marks actionable name-level content while a compressed one marks common sentiment. |
| L3 | Shleifer & Vishny (1997), "The Limits of Arbitrage", Journal of Finance 52(1), 35-55 | Supporting mechanism | ACCEPT: name-specific premia persist where arbitrage capacity is name-level segmented; when the cross-section compresses, remaining differences are too small relative to arbitrage noise to be informative. |
| L4 | Makarov & Schoar (2020), "Trading and arbitrage in cryptocurrency markets", Journal of Financial Economics 135(2), 293-319 | Crypto transfer | ACCEPT: crypto premia persist under segmented arbitrage; the perp premium cross-section is therefore a meaningful information object, not pure noise. |
| L5 | Direct evidence that cross-sectional premium dispersion conditions premium-level predictability on Binance USDT-M perps | Gap | NOT RETRIEVED — honestly reported: this lane performs no web retrieval; to its verified knowledge no canonical peer-reviewed result tests dispersion-gated premium conditioning on crypto perps. Mechanism-driven with preregistered falsification. |

Transfer caveats: L1 is a returns-R² result applied by analogy (declared; the analogy itself
is what the narrow-state control tests — if the analogy is wrong the control fires); L2 is
equity mispricing-spread evidence at monthly horizons (transfer: 15m-resolved premium
cross-section on 19 liquid perps is a different object; persistence is what the 56d neighbour
tests); L4 is venue-vs-venue, not perp-vs-index (same arbitrage-capacity logic, different
leg).

## 4. PIT observable (fusion-record availability semantics; EVIDENCED availability stamps)

Decision instant T = Monday 00:00:00Z. A decision at T reads ONLY rows with
`available_time_utc <= T` (p_freeze_v14.v14_specific_freezes.pit_authority;
research/data_fusion/crypto_compat.py semantics).

- Signal route: mark/index premium per 15m bucket computed from `/fapi/v1/markPriceKlines`
  (param symbol=) close divided by `/fapi/v1/indexPriceKlines` (param **pair=** — measured
  HTTP 400 on symbol=, discrepancy D2) close, minus 1: m_b = markClose_b / indexClose_b − 1.
  EVIDENCED_AVAILABLE per `availability_evidence_table.json` source
  `basis_mark_index_derivable_route` (rows at screen start on all 4 probed symbols on all
  three routes; screen end probed on BTCUSDT; earliest rows listing-era; documented open-time
  kline identity and weight table archived).
- Lag convention frozen (bar-close availability class, per the evidence table's publication
  semantics "Klines are uniquely identified by their open time; a bucket's close value is
  complete only at close time"): a bucket covering [t_open, t_open+15m) is available at
  t_close = t_open + 15m; a decision at T uses ONLY fully-closed prior buckets with
  t_close <= T; the last admissible bucket for a Monday 00:00Z stamp is [Sun 23:45, Mon 00:00).
  No partial bucket is ever read.
- Staging identity check: m_b vs `/fapi/v1/premiumIndexKlines` close (same bucket grid) must
  agree within a declared relative tolerance; violations flag the symbol fail-closed at
  staging. (premiumIndexKlines taken as documented cross-check only.)
- Per-name level: b_i(T) = mean of m_b over the trailing 2688 (anchor) / 5376 (neighbour)
  completed buckets; EVERY slot must exist and be available; one missing slot refuses the
  symbol at that stamp (fail-closed, no back-fill — L-V12-5).
- Dispersion state (CROSS-SECTIONAL, not time-series): D(T) = interquartile range (IQR) of
  b_i(T) across the eligible names at stamp T (IQR chosen over std for outlier robustness,
  declared). Gate rule with NO tuned constant: gate OPEN iff D(T) > median of the strictly
  prior stamp D values (expanding window; requires >= 6 prior stamps, stamps with fewer
  priors are flat and counted in a refusal counter). By construction a stationary median split
  opens the gate in approximately half the stamps; measured open frequency is reported by A9-F
  pre-score from the dispersion series (no PnL).
- BTCUSDT (bars): benchmark buy-and-hold + 90d beta context only, never ranked.
- Funding settlements (`crypto_funding`, settlement-stamp availability): native cost/credit on
  held legs exactly once per settlement, identical across arms; NEVER a signal input.

Depth-evidence caveat (carried obligation): P2 depth was measured on BTCUSDT / ETHUSDT /
SOLUSDT / XRPUSDT; per-symbol depth re-verification for all 19 ranked names is a mandatory
staging prerequisite ("D2/A9-F must re-verify before any scored use" — evidence table D1
resolution). indexPriceKlines pagination uses pair= (D2). Forward pagination only for
statistics endpoints; klines endpoints use standard startTime paging.

## 5. Universe, warmup, clock, holding, execution (frozen conventions)

- Universe: the 20 staged REQUIRED_SYMBOLS
  (research/audits/v12p/a3_s0_snapshot_authorization.json) minus BTCUSDT = 19 tradable names.
  Eligibility at T: full completed-bucket coverage of the formation window (fail-closed) plus
  the binding 90-day beta warmup; universe eligibility per the V12 selection_freeze authority
  cited in p_freeze_v14.json inherited_conventions[1]
  (research/control/v12_run/selection_freeze.json, sha256 0b3b0865...).
- Warmup: binding maximum 90 days (beta context, from already-authorized bars); premium-level
  formation 28d (2688 buckets, anchor) / 56d (5376 buckets, neighbour); gate history >= 6
  prior weekly stamps. First screen stamp 2025-08-25; earliest required kline data 2025-06-30
  (56d before first stamp) — entirely inside the authorized window 2024-08-20..2026-08-21.
- Decision clock: weekly, every Monday 00:00:00Z (52 decisions in the 364-day blind-S0 window
  2025-08-22..2026-08-21 <= 60 floor). Folds: frozen F0 2025-08-22..2025-12-21,
  F1 2025-12-22..2026-04-21, F2 2026-04-22..2026-08-21, 1-day purge, force-flat at boundaries;
  ~17 decisions per fold.
- Holding: intended 7 days (>= 3d floor); force-flat at fold boundaries; FLAT by design in
  narrow-dispersion states (no positions carried across a gate transition except at the
  Monday stamp — book changes only at stamps).
- Execution lag (ONE, declared): fills at the close of the first completed 15m bar strictly
  after T (Monday 00:15:00Z bar close); stress adds +1 event delay (Monday 00:30:00Z close).
- Book (in OPEN state): long lowest-premium tercile / short highest-premium tercile — sides of
  size floor(N_eligible/3), equal weight 1/(2·floor(N_eligible/3)) per leg, gross 1.0; ties
  broken by symbol id ascending (declared a priori); middle tercile flat. Minimum 12 eligible
  names for an open stamp to trade; max |weight| = 1/8 = 0.125 <= 0.30 at every stamp by
  construction (L-V11-2 co-design satisfied). BTCUSDT never ranked.

## 6. Arms (exactly 3): anchor + neighbour + causal negative control

- ANCHOR — `BASISLV-WIDTHGATE-28D`: levels b_i over 2688 buckets (28d); dispersion state
  D(T) from the same 28d levels; gate per section 4; book as in section 5 when open, flat
  when narrow.
- NEIGHBOUR — `BASISLV-WIDTHGATE-56D`: identical mechanism, levels b_i over 5376 buckets
  (56d), dispersion D(T) from those 56d levels, same median-split gate rule. Justification:
  the information-content claim requires the premium dispersion state to be a persistent,
  well-defined regime rather than an artifact of one formation window; 56d is in the frozen
  warmup table and is the pre-declared sibling of the 28d anchor.
- CAUSAL NEGATIVE CONTROL — `BASISLV-WIDTHGATE-28D-NARROW`: identical construction with the
  gate INVERTED — open iff D(T) < trailing median (trade only in the compressed-dispersion
  state). This is a preregistered sign/state-inverted perturbation: if dispersion is genuine
  information content, the compressed state must NOT reproduce the anchor.
- Preregistered control rule: the control MUST NOT reproduce the anchor — if
  `BASISLV-WIDTHGATE-28D-NARROW` passes the same incremental gate (BTC-beta-context excess
  positive in >= 2/3 folds), the dispersion state direction carries no information, the anchor
  FAILS and the family is rejected; the control is never promotable to a family regardless of
  its own result (L-V12-1: inverted-control wins are falsification artifacts, never
  candidates).
- Ungated diagnostic (NOT a scored arm): the identical book without the gate, computed on the
  same stamps solely to evaluate the redundancy guard in sections 2 and 7; it consumes no
  scored cell and is declared here so the guard is not a post-hoc comparison.
- Beta/funding separation (all arms): identical universe, fills, native funding accounting;
  funding is a cost/credit, never a signal; the incremental gate is BTC-beta adjusted.

## 7. Incremental test vs buy-and-hold and BTC-beta context

- Benchmark: BTCUSDT buy-and-hold over the same stamps (same clock, same fold boundaries).
- Beta context: weekly arm excess adjusted by beta from trailing 90d of completed daily bars
  (frozen convention).
- Incremental means, for this family: (i) after-cost excess OVER the beta-matched benchmark
  attributable to trading ONLY when the premium cross-section is wide (the standard frozen
  gate), and (ii) the mechanism-specific sharpening — that gating adds value OVER the same
  book ungated (the redundancy guard of section 6).
- Binding gate (Stage-A, unrelaxed): anchor BTC-beta-context excess positive in >= 2/3 folds;
  raw excess vs buy-and-hold also positive in >= 2/3 folds; gated excess > ungated diagnostic
  excess in >= 2/3 folds (redundancy guard); neighbour same pattern; narrow-state control must
  NOT pass the incremental gate per section 6.

## 8. Costs under the remediated kernel, floors, concentration, drop-one

- Costs (L-V14-0 remediated kernel, binding): charged on FILLS ONLY — exactly once per fill,
  never per holding-day, never per stamp on open positions; real perp-metadata tick sizes per
  symbol (no uniform stubs); native funding settlements on held legs exactly once per
  settlement; scored cells report cost broken out by fills vs holding terms. Base schedule +
  stress = fee x1.5, +2 adverse ticks (per-symbol tick size), +1 event delay. Feasibility
  (base drag <= 8%/yr of gross; stressed <= 12%/yr) evaluated by A9-F from schedule artifacts
  only — no cost number computed in this proposal. Gate transitions add exit-only fills on
  close-to-flat stamps; these are fills like any other and are charged once.
- Turnover (numeric bound): open-state rebalances trade at most 24 fills per decision as in
  the sibling proposal; close-to-flat stamps add at most 12 exit fills; hard upper bound
  <= 36 fills per decision per arm, <= 1,872 fills/window/arm at 52 decisions (expected far
  lower; measured at score time and reported in the fills-term cost column).
- Sample floors (numeric): >= 52 weekly decisions per arm; gate OPEN in >= 26 stamps across
  the window and >= 8 stamps per fold (a stationary median split opens ~half by construction;
  measured deviation reported by A9-F pre-score from the dispersion series — if measured open
  frequency is < 50% of stamps overall the arm is design-infeasible => BLOCKED_PRELAUNCH,
  never a scored zero-position cell); >= 15 decisions per fold; >= 12 eligible names per open
  stamp (below that the stamp refuses and the refusal is counted); if depth re-verification
  leaves < 12 eligible names on average over the window, verdict BLOCKED_DATA (data failure,
  not a mechanism rejection). Zero-position arms refused at publication (L-V11-4).
- Concentration: max |weight| <= 0.30 by construction; no symbol > 25% of turnover (checked by
  A9-F); largest symbol positive-PnL share <= 0.70 gate inherited.
- Drop-one design (non-vacuous): identify the fold-stamp with the largest held |weight| (an
  open-state stamp by definition); under equal weights all held legs tie, so the pre-declared
  outcome-free tie-break applies: drop the held leg with the largest |b_i(T)| at that stamp.
  By construction the dropped symbol held >= 1 position (non-vacuousness, L-V11-7).
  Renormalize the remaining 2k−1 legs to gross 1.0 and re-run the anchor. The family survives
  only if the anchor's fold-sign pattern, the redundancy guard and the control rule's outcome
  are unchanged; otherwise the edge is symbol-specific and the family is rejected.

## 9. Failure interpretation

- Anchor fails the incremental gate: trading only in wide-dispersion states earns nothing
  after costs; premium-dispersion information content is absent; family rejected (no
  parameter search, no gate-threshold tuning — the threshold is structural).
- Anchor positive but fails the redundancy guard (does not beat the ungated book): dispersion
  adds nothing beyond the level ranking; the family is a redundant twin of
  `BASISLV-PREMFADE` and is rejected by its own preregistered clause even though positive —
  this is the cluster-padding guard firing exactly as designed.
- Narrow-state control also passes the gate: the dispersion direction carries no information
  (the R²/Stambaugh-Yuan analogy is wrong here); family rejected; control never promotable.
- Anchor positive, neighbour flips: the dispersion state is formation-window fragile — not
  the persistent regime the mechanism requires; family rejected.
- Anchor passes base but fails stress: execution artifact; family rejected.
- Fold-concentration failure (> 50% of positives in one fold): one dispersion episode drives
  everything; family rejected.
- Symbol-concentration failure (largest symbol > 0.70 of positive PnL): single-name artifact;
  family rejected.
- Price-only negative with total positive only via funding credits: carry-harvest artifact;
  family rejected (declared ex ante).
- Gate open-frequency far from 50%, or depth re-verification failures: design/data failure —
  BLOCKED_PRELAUNCH or BLOCKED_DATA, not a mechanism rejection.

## 10. Source-to-test map (staging plan; NO downloads performed in this lane)

| Input (endpoint / field) | Availability stamp | Exact test use | Staging plan |
|---|---|---|---|
| `/fapi/v1/markPriceKlines`, symbol=<SYM>, interval=15m: close | bucket close time (bar-close class; frozen lag convention section 4) | numerator of m_b; b_i levels (2688/5376 buckets); cross-sectional IQR D(T); gate | 19 symbols, 2025-06-30T00:00Z..2026-08-21T23:59Z (56d before first stamp + screen); ~40.1k buckets/symbol; limit=1500 => ~27 req/symbol => ~513 requests |
| `/fapi/v1/indexPriceKlines`, **pair**=<SYM>, interval=15m: close (D2: pair= required) | bucket close time | denominator of m_b; same uses | 19 symbols, same window; limit=1500 => ~27 req/symbol => ~513 requests |
| `/fapi/v1/premiumIndexKlines`, symbol=<SYM>, interval=15m: close | bucket close time | staging identity cross-check vs mark/index ratio (fail-closed flag on violation); not a signal input | 19 symbols, same window; ~27 req/symbol => ~513 requests |
| Depth re-verification point anchors | as measured (evidence table D1/D2) | per-symbol depth proof for all 19 names before scored use | startTime+endTime limit=1 anchors at 2025-06-30 and 2026-08-21 per symbol per route => ~114 requests; failing symbols dropped fail-closed; < 12 eligible => BLOCKED_DATA |
| `crypto_bars` 15m completed (authorized, staged) | bar close time | weekly benchmark, 90d beta, fill prices, holding PnL, fold boundaries | already staged/authorized; no new fetch |
| `crypto_funding` settlements (authorized, staged) | settlement stamp | native cost/credit on held legs, once per settlement, all arms identically | already staged/authorized; no new fetch |
| perp instrument metadata tick sizes | static metadata | +2-tick stress unit per symbol (remediated kernel) | staged; no new fetch |
| (explicitly NOT used) open interest, /futures/data/basis route for the signal, quarterly-contract basis, funding rate as signal, per-name premium time-series variance | — | declared out of scope: bounds the conditioning space, keeps the A6/AXIS-2 boundary (no basis dynamics/volatility), and avoids V13-OITD adjacency | — |

Estimated new-request total ≈ 1,653 requests (~2,000-9,000 documented weight units across the
kline weight table; 0.55s sleep ≈ 19 min). Estimates only; no fetch performed by this lane.

## 11. Forbidden-packet self-check (every inventory class inspected)

| Class | Inspected; why this proposal is not a variant/rescue |
|---|---|
| V10-M01-AGGRESSOR-ABSORPTION | No aggressor side, order-flow panel or absorption variable; premium is a price-gap from mark/index kline routes. Clean. |
| V11-LOTTERY-MAX-SKEW | No return moments anywhere (no MAX, skew, lottery, idio-vol). Clean. |
| V11-ILLIQ-AMIHUD | No \|return\|/dollar-volume impact ratio; the frozen ILLIQ replication brief is untouched. Clean. |
| V11-OILEVER-DELEV | No open-interest input; no cap change (0.30 satisfied at 0.125 max by construction). Clean. |
| V4-XSECT-MOM | No past-return term in any signal or in the gate. HONEST RISK NOTE: premium levels correlate mechanically with recent appreciation, so ranks may correlate with momentum ranks; the defense is structural (no return in the signal) plus the binding A7-N rank-correlation gate vs all rejected momentum ancestors — if rho > 0.20 this proposal is INELIGIBLE and should be found so. |
| V6/V1-CARRY-FUNDING | Adjacent neighborhood DECLARED (same disclosure as the sibling proposal): signal field is the mark/index kline gap, NOT funding settlements; funding enters only as an identical native cost; the gate has no carry input. Guard rails preregistered: price-only failure clause (section 9); the state-inverted control; binding A7-N rho gate vs V6/V1 rows. If A7-N rules a V6 rescue, this proposal is INELIGIBLE and should be found so. |
| V1-VOLCOMP | No volatility compression, breakout or continuation claim. The dispersion variable is the CROSS-SECTIONAL spread across names at a stamp — not volatility through time and not compression. Clean. |
| V8R-XSECT-REVERSAL | No price-reversal signal; no past-return term. Same correlation caveat as the V4 row; A7-N gate accepted. |
| V9-TS-TREND | No time-series trend feature or dead-zone book. Clean. |
| WEEKLY-REVERSAL / MR-RESCUE | Not a renamed rejected baseline: the inside book is a premium-level ordering (no return term), the mechanism claim is about WHEN it is informative, and both the state-inverted control and the redundancy guard can kill it. Clean. |
| V12-OILEV-V2 | No OI input of any kind; no sign flip, horizon tweak, universe carve-out or renaming of OILEV-V2. The +0.758 shadow is inverted-OI-FLOW — a different variable; this proposal declares itself OUTSIDE the shadow region (section 12). Clean. |
| V12-BAB-LOWBETA | No beta-sorted book; beta only as identical context adjustment. Clean. |
| V12-ILLIQ-REPLICATION | Untouched; no window substitution; no re-opening. Clean. |
| DATA-GATED | Only EVIDENCED_AVAILABLE routes cited (mark/index/premium klines + already-authorized bars/funding); free keyless Binance public endpoints; no external, paid or asserted-unevidenced source. Clean. |
| V13-OITD-TERM-STRUCTURE | No open-interest term structure, no positioning-duration variable; quarterly-contract basis explicitly DECLARED OUT OF SCOPE (section 10). Clean. |
| V13-LIQEPIS | No volume input, no episodicity/Herfindahl, no liquidity-provision variable. Clean. |

Lane-axis discipline: the conditioning variable is CROSS-SECTIONAL dispersion of premium
LEVELS across names at each stamp (AXIS-1 scope: "level and dispersion as conditioning"). No
per-name premium CHANGE, momentum, reversion, or premium VOLATILITY through time enters any
signal; the trailing median of past CROSS-SECTIONAL IQRs is a normalization of the same
cross-sectional statistic (the gate threshold), not a time-series basis-dynamics feature —
the AXIS-2 boundary (A6's lane) is declared and respected. A7-N cross-cluster correlation
measurement is accepted as binding.

Mutual-redundancy honesty: this proposal shares its inside book with
`A14-V14-A5-BASISLV-PREMFADE` by design; the redundancy guard (sections 2/6/7) makes the
dispersion mechanism falsifiable independently of the level mechanism, and under the
wave-diversity rule at most one of the two can be selected. If A7-N measures the pair as one
cluster, that finding is correct and expected to bind.

## 12. Shadow-region posture (voluntary)

The recorded shadow observations (inverted OI-flow +0.758 in the V12 OILEV-V2-INV control;
V11 LOT inversion; stocks vol-level sorting) involve different variables; no prior control
arm ever measured the cross-sectional perp-premium dispersion. This proposal declares itself
OUTSIDE the shadow region. If A1/A7-N classify it into the shadow region anyway, the front
door is pre-accepted: mechanism in its own words, confirmatory status recorded in verdict and
denominator, own causal negative control (section 6), A7-N |rho| <= 0.20 vs the frozen
OILEV-V2 anchor AND its inverted control accepted as an eligibility condition, Stage-A gates
unrelaxed.

## 13. Outcome-blind attestation

```
OUTCOME-BLIND ATTESTATION
lane: a5 (d1-a5-proposals)  proposal: A14-V14-A5-BASISLV-WIDTHGATE
wave SHA: c3e3c90561efc972c487a99951ca0f6031ab4fa34907d1c10890d1795b4da4a8
I wrote this mechanism, its arms and its falsification conditions before any
return, metric or ranking was computed, without access to any per-arm outcome
file or scored artifact, and I will not modify this proposal after outcomes
exist. No backtest, PnL, data download or network fetch was performed.
utc: 2026-09-05T00:33:36Z  agent: a5
```
