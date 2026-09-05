# A14-V14-A6-BASISDYN-PREMREV — Premium-Overhang Reversion (basis first-difference)

lane: d1-a6-proposals (outcome-blind proposal, Phase V14-D1) — cycle CRYPTO-V14
axis: AXIS-2 basis dynamics (time-series conditioning on how the mark-index
premium is MOVING — never on its cross-sectional level or dispersion, which is
AXIS-1's variable)
wave SHA: `V14_PROPOSAL_WAVE_SHA = c3e3c90561efc972c487a99951ca0f6031ab4fa34907d1c10890d1795b4da4a8`

---

## 1. Hypothesis ID + mechanism

**Hypothesis ID: `A14-V14-A6-BASISDYN-PREMREV`**

Mechanism (own words): on Binance USD-M perpetuals the premium — the perp-side
mark price relative to the underlying index — is anchored to the index by
funding-carry arbitrage: when the perp trades rich, carry sellers short it
against the index; when it trades cheap, reverse-carry buyers enter. That
arbitrage capital is balance-sheet-limited and acts at funding-cycle
granularity, so a large premium MOVE does not close instantly: leveraged
positioning that chased the move is stopped out or deleveraged over the
following funding settlements, and that forced exit flow pushes the perp
further toward (often through) the index. The exploitable residual is the
unwind overhang: after a large standardized premium rise the perp continues to
UNDERPERFORM the index; after a large standardized premium fall it continues
to OUTPERFORM. Economic counterparty: fast leveraged premium-chasers versus
basis-arbitrage capital that closes the gap over 1–3 days. Why the edge can
exist after costs: the claim is about repeatable positioning-unwind flow over
multi-day horizons (Makarov–Schoar document that crypto relative-value
deviations converge slowly, not instantly), not a tick-level arbitrage; the
predicted gross effect must clear weekly round-trip costs or the family is
rejected as cost-infeasible with no fee carve-out. Predicted sign: **long the
5 symbols with the most NEGATIVE trailing standardized 72h premium change**
(fresh premium collapse → perp outperformance); names with the most positive
change are the ones NOT held (predicted perp underperformance). Null that kills
it: 72h premium changes carry no information about next-week perp excess
returns (convergence is instant, or no overhang exists) — observed as anchor
excess <= 0 in >= 2/3 folds. Funding NEVER enters the signal in any arm; it is
charged only as a holding cost under the native settlement convention.

## 2. Falsifiable prediction

The anchor arm (PREMREV-72H) must, after BASE costs under the remediated
kernel: (a) earn positive buy-and-hold-BTC-matched excess in >= 2/3
chronological folds; (b) earn positive BTC-beta-context (beta-adjusted) excess
in >= 2/3 folds; (c) pass all frozen Stage-A gates; (d) be supported by the
neighbour (PREMREV-24H: same sign, same excess gates); and (e) NOT be
reproduced by the causal negative control (IDXREV-72H) under the preregistered
rule of section 6.

**FALSIFIED if any of:** excess <= 0 in >= 2 folds on either gate; IDXREV-72H
reproduces the anchor (rule in section 6); the 24h neighbour fails to show the
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
| L1 | Makarov, I. & Schoar, A. (2020), "Trading and Arbitrage in Cryptocurrency Markets", Journal of Financial Economics 135(2), 293–319. | HIGH. Documents persistent law-of-one-price violations across crypto venues and futures-spot bases, and that arbitrage capital is limited so deviations converge slowly. Primary support for the premise that premium deviations close over days, not ticks. REJECT as design template: venue-arbitrage study, no perp premium-dynamics conditioning, no after-cost trading rule. |
| L2 | He, S., Manela, A., Ross, O. & von Wachter, V. (2022), "Fundamentals of Perpetual Futures", arXiv:2205.09217. | HIGH (existence, from knowledge; exact arXiv id re-verify). Derives no-arbitrage perp pricing: the perp price equals the index minus the discounted stream of expected funding, so the premium is anchored to the index and its deviations are governed by funding expectations. Frame support for both the reversion premise and the sibling PREMVOL proposal. REJECT as template: theory/pricing paper, no cross-sectional after-cost test. |
| L3 | Nagel, S. (2012), "Evaporating Liquidity", Review of Financial Studies 25(7), 2005–2039. | HIGH. Short-term reversal profits are compensation for liquidity provision and rise when funding liquidity contracts. Channel anchor: the overhang harvest is a liquidity-provision-like compensation against forced unwind flow. Caveat: Nagel's measurement is price-return-based; PREMREV conditions on the premium (perp-vs-index differential) change, a different variable. |
| L4 | Koijen, R., Moskowitz, T., Pedersen, L.H. & Vrugt, E. (2018), "Carry", Journal of Financial Economics 127(2), 197–225. | HIGH, cited for CONTRAST ONLY: the carry literature conditions on the LEVEL of the forward-spot basis as a standing yield. PREMREV conditions on the standardized first DIFFERENCE of the premium over 72h — a flow statistic, not a yield. The level-based funding-carry operationalization is exactly the forbidden V6 family; this proposal is not it (see self-check). |
| L5 | Bessembinder, J. (1992), "Systematic Risk, Hedging Pressure, and Risk Premiums in Futures Markets", Review of Financial Studies 5(4), 637–667; De Roon, F., Nijman, T. & Veld, C. (2000), Journal of Finance 55(3). | HIGH. Futures premia contain a positioning-structure component beyond systematic risk — the general frame that non-price positioning information can be priced in futures. Caveat: no hedger/speculator classification exists in the authorized data; the premium-change statistic is a coarse observable proxy. |

**Honest thinness statement:** no published cross-sectional or time-series
after-cost study of premium-CHANGE conditioning on Binance USD-M perpetuals is
known to this agent. Prior uncertainty is high; the preregistered
falsification gates, not the priors, decide.

## 4. PIT observable — EVIDENCED availability stamp

**Dataset authority cited in full:** `research/control/v14_run/p1_a3/availability_evidence_table.json` (A3, generated 2026-09-04T23:42:17Z), source_id
`basis_mark_index_derivable_route`, classification **EVIDENCED_AVAILABLE**,
classification basis: relative to the 15m conditioning clock over the screen
window, rows exist at screen start (2025-08-22T00:00Z) for all 4 probed symbols
on all three routes, at screen end, and back to listing era (BTC first rows
2019-12); documented semantics archived (provider pages via Internet Archive
snapshots). Corroborating route `basis_futures_data` (/futures/data/basis) is
likewise EVIDENCED_AVAILABLE with measured anchors at 2024-08-20 and
2023-01-01, with documented-vs-measured discrepancy D1 recorded and the
resolution "D2/A9-F must re-verify before any scored use". NOT_RUN/UNAVAILABLE
is never inferred from silence (L-V12-5).

Primary observable (frozen): **`/fapi/v1/premiumIndexKlines`, field `close`
of the 15m premium-index bucket** — a relative perp-vs-index premium rate,
scale-free across symbols. Param style `symbol=`; `limit` max 1500 (documented
weight table archived). The derivable route `/fapi/v1/markPriceKlines`
(`symbol=`) and `/fapi/v1/indexPriceKlines` (**requires `pair=`; `symbol=`
measured HTTP 400 — evidence-table discrepancy D2**) is reserved as the
preregistered integrity cross-check for A9-F/I-lane verification, never a
signal input. The `/futures/data/basis` endpoint is NOT the signal input: its
bucket-stamp semantics are "period-aligned, no stated update lag" (evidence
table), weaker for PIT than the kline open-time class; its EVIDENCED_AVAILABLE
status is cited as corroboration of the same premium structure, and its
measured quirk (backward pagination repeats the latest page; use forward
startTime pagination or point anchors) is recorded for the staging plan.

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
readable bucket at t, and sigma_chg_s the trailing 30d standard deviation of
consecutive 72h premium changes (all from strictly-closed prior buckets),

`m_s(T) = (P_s(T) − P_s(T − 72h)) / sigma_chg_s(T)`

— a standardized premium FIRST DIFFERENCE. No premium level, no
cross-sectional dispersion, no price return, no OI, no volume and no funding
term enters the ranking. Price enters nowhere in the signal; the index enters
nowhere in the anchor signal (the premium kline is the perp-side observable).

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
  buckets covering 72h formation + 30d standardization window + 90d beta —
  with stamps <= T. Ineligible symbols are excluded that stamp; the book
  renormalizes across eligible names at equal weight 1/N (N = eligible count);
  N >= 4 satisfies |w| <= 0.30 by construction (1/4 = 0.25); N < 4 scales gross
  down to keep |w| <= 0.30 at every stamp. Coverage honesty: P2 measured
  screen-start/end anchors on 4 symbols (BTC/ETH/SOL/XRP); the remaining 15
  tradable names inherit the same EVIDENCED_AVAILABLE classification but their
  per-symbol anchors were not probed — A9-F re-verification at D2 is a named
  item, and any symbol lacking full coverage is excluded per-stamp,
  fail-closed, never synthesized (L-V12-5).
- **Warmup**: binding requirement 90d (BTC-beta context) + 30d standardization
  + 72h formation; satisfied entirely from authorized pre-screen history
  2024-08-20..2025-08-22 (368 days) before the blind-S0 window.
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
  (satisfies the >= 3d median-holding floor).

## 6. Arms — anchor + neighbour + causal negative control (exactly 3)

| Arm | Construction | Role |
|-----|--------------|------|
| **PREMREV-72H** (anchor) | Rank 19 eligible symbols ASCENDING on m_s(T); long the 5 most negative standardized 72h premium changes at 0.20 each, gross 1.0. | The mechanism (premium-overhang reversion). |
| **PREMREV-24H** (neighbour) | Same mechanism and standardization, formation window 24h (3 funding settlements at the native 8h cadence). | Justified adjacent parameterization: the convergence channel operates at funding-cycle-to-multi-day horizon; 24h tests the fast end of the same mechanism, inside the frozen warmup table. |
| **IDXREV-72H** (causal negative control) | IDENTICAL pipeline applied to `/fapi/v1/indexPriceKlines` (`pair=`) 15m close: standardized 72h INDEX-price change (same 30d standardization), long the 5 most negative. | Closest rival explanation: "the edge is ordinary reversal in the underlying price rebadged" — exactly the forbidden WEEKLY-REVERSAL/MR-RESCUE class. The index series contains NO perp positioning information (it is the external spot reference), so a premium-information mechanism must NOT be reproducible by it. |

**Preregistered control rule (the control MUST NOT reproduce the anchor):**
control reproduction is defined as: the IDXREV-72H arm passes after-cost
expectancy > 0 AND its per-fold buy-and-hold-excess SIGNS match the anchor's
in >= 2/3 folds. If reproduction occurs, the causal attribution FAILS: the
residual anchor edge belongs to generic underlying reversal, not premium
information, and **BASISDYN-PREMREV is INELIGIBLE for selection even if the
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
  first-difference statistic must carry return information BEYOND (i) BTC
  direction (beta gate) and (ii) the two rival conditionings placed in the
  control seat: the index-price change (section 6) polices "ordinary reversal";
  the premium LEVEL is deliberately absent from every arm signal — a
  level-conditioned basis claim belongs to AXIS-1/A5 and is not this family.
  A raw pass with a beta-context failure is BTC beta in disguise -> REJECT
  (mission Q2 demands incremental information, not leveraged beta).

## 8. Costs under the REMEDIATED kernel, turnover, sample floors

- **Costs on fills ONLY** — never per holding-day, never per stamp on open
  positions (L-V14-0 remediation, pinned by tests/test_v14_p1_cost_once.py);
  real perp-metadata tick sizes (no uniform stubs; sub-cent symbols slip by
  real ticks, not 0.01); native funding settlements while held enter EXACTLY
  ONCE as a COST, never a signal or sidecar; scored cells report cost broken
  out by fills vs holding terms.
- **Base schedule**: generic adapter fee + slippage per fill. **Stress**: fee
  x1.5, +2 adverse ticks (instrument tick sizes), +1 event delay (fill moves
  00:15Z -> 00:30Z).
- **Turnover floors (frozen, binding, never relaxed)**: <= 60 discretionary
  decisions/365d (52 scheduled, ~50 live after purge); median intended holding
  >= 3d (7d); base cost drag <= 8%/yr of gross; stressed <= 12%; no symbol
  > 25% of one-way turnover (equal 0.20 weights bound each name at ~20% of
  gross per side by construction); |w| <= 0.30 at every stamp; gross <= 1.0.
  Weekly 5-name rebalance implies one-way turnover ~1.0 gross/week — the drag
  floors are expected to be the binding feasibility risk for this anchor; if
  they fail, the family is REJECTED cost-infeasible (failure table), never
  rescued by a fee carve-out or slower-clock post-hoc.
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
| Cost floor breached (base or stress) | Overhang not harvestable at weekly clock and frozen costs | REJECT cost-infeasible; no fee exemption, no clock retune (rescue forbidden). |
| Anchor excess <= 0 in >= 2 folds | Convergence instant / no overhang: the null | REJECT; sign flip forbidden (OILEV-V2 / V6 rescue pattern; L-V12-1). |
| IDXREV-72H reproduces the anchor | Attribution failure: edge is ordinary underlying reversal (forbidden class), not premium information | REJECT as INELIGIBLE; an ordinary-reversal claim can never be re-proposed from this outcome. |
| Neighbour fails while anchor passes | Parameter fragility at the fast horizon | REJECT family; neighbour never promoted alone. |
| Beta-context fails while raw passes | BTC beta in disguise | REJECT — no incremental information. |
| Drop-one vacuous or verdict flips | Not robust to held-book composition | REJECT. |
| Premium-kline coverage gaps force N < 4 persistently | Data problem, not economics | Report as BLOCKED_DATA candidate; no redesign inside this cycle (L-V12-5). |

Mechanism falsification (not merely losing money): if per-fold anchor excess
is negative while IDXREV-72H ALSO fails, the specific observed pattern —
premium changes uninformative AND index changes uninformative at weekly
horizon on this universe — falsifies the claimed convergence-overhang channel
itself on this window.

## 11. Source-to-test map (endpoint -> field -> staging plan; NO downloads now)

| Field (endpoint) | Test use |
|---|---|
| `premiumIndexKlines.close` (15m, `symbol=`) | Anchor + neighbour signal ONLY: P_s(T), 72h change, 30d standardization (strictly-closed prior buckets). |
| `indexPriceKlines.close` (15m, `pair=`) | IDXREV-72H causal control signal ONLY (never the anchor; `pair=` param per discrepancy D2). |
| `markPriceKlines.close` (15m, `symbol=`) | Preregistered integrity cross-check for A9-F/I-lane (premium route coherence); never a signal. |
| staged 15m bars (`crypto_bars`, bar-close availability) | Fill marks, BTC buy-and-hold benchmark, 90d beta context. |
| `crypto_funding` (`fundingTime` settlement stamp) | Holding cost ONLY, applied to `[ts_opened, ts_closed]`, settled natively exactly once. |
| instrument metadata tick sizes | Stress slippage floor (+2 ticks), real per-symbol ticks. |
| BTCUSDT bars | Benchmark + beta only; never tradable in the book. |

**Staging plan (V14-I; nothing fetched in D1)**: symbols = 19 tradable
(basis-premium route); window = 2024-08-20..2026-08-21 (warmup + screen);
granularity = 15m (the P2-probed depth); ~70,176 buckets/symbol at 96/day =
47 pages at limit 1500 -> ~893 requests per staging lane for the premium
route; optional cross-check route +2 x 893 (mark + index klines) only if A9-F
requires it; documented kline weight table ([500,1000] -> 5 units/request,
archived) and the A3 lane pacing reference (0.55s sleep, observed max 48
weight/min) bound the pull; forward `startTime` pagination only (the
/futures/data/basis backward-pagination repeat quirk is archived and avoided
by using the kline route as primary).

## 12. Forbidden-packet self-check

Inspected classes (research/control/v14_run/forbidden_family_inventory.json)
and verdicts:

- **V6/V1-CARRY-FUNDING (closest class — honest proximity note)**: V6 is
  funding-carry LEVEL conditioning (collect the standing funding yield) and
  its inverse. PREMREV conditions on the standardized 72h premium CHANGE; the
  funding series never enters any arm signal (cost only); no carry or
  crowding-premium-from-funding story is claimed (L4 cites the carry literature
  for contrast, not adoption). Because premium and funding are mechanically
  linked through the funding formula, rank proximity is plausible: **declared
  outcome-blind novelty condition — if A7-N measures |rho| > 0.20 between the
  PREMREV-72H weekly rank and the frozen V6 CARRY-3D rank OR its REVERSE-3D
  control on the common window, this proposal is INELIGIBLE.**
- **WEEKLY-REVERSAL / MR-RESCUE (closest rival — policed by the causal
  control)**: ordinary reversal conditions on past PRICE returns. PREMREV's
  signal contains no price return term in anchor or neighbour; the
  index-change rival is placed in the IDXREV-72H control seat with the
  preregistered must-not-reproduce rule — if it reproduces, the proposal is
  rejected as a rebadged reversal.
- **V12-OILEV-V2 / V11-OILEVER-DELEV / V13-OITD**: no open-interest term in
  any arm (level, flow, term structure, days-to-positioning); not a sign flip,
  horizon tweak, carve-out or renaming of any OI family. Declared novelty
  condition: |rho| > 0.20 vs the frozen OILEV-V2 anchor OR its inverted
  control -> INELIGIBLE.
- **V13-LIQEPIS / V11-ILLIQ-AMIHUD / V10-M01**: no volume, turnover, Amihud
  or aggressor/imbalance term anywhere; liquidity-episode structure is not
  measured.
- **V9-TS-TREND / V4-XSECT-MOM / V8R-XSECT-REVERSAL**: the anchor/neighbour
  rank uses no past return of any horizon on any price series; momentum/
  reversal claims in PRICE space are absent from the mechanism.
- **V1-VOLCOMP (incl. V9 dollar-volume shock)**: no compression, no breakout,
  no volume-shock event; no continuation premise on price.
- **V11-LOTTERY-MAX-SKEW**: no return-distribution moment (MAX/LOT/skew).
- **V12-BAB-LOWBETA**: no beta-sorted construction; beta appears only in the
  frozen context gate.
- **V12-ILLIQ-REPLICATION**: not the frozen replication brief; no window
  substitution.
- **DATA-GATED**: uses only the P2 EVIDENCED_AVAILABLE basis/mark-index route
  + already-authorized bars/funding/metadata; no new source, key, signup;
  zero downloads performed in D1.
- **Shadow region: NOT entered.** The predicted sign derives from the
  convergence-overhang mechanism, not from any measured control-arm
  observation (inverted OI-flow +0.758, V11 LOT inversion, vol-level sorting);
  preregistered EXPLORATORY; causal control and novelty conditions carried
  voluntarily.
- **Wave diversity honesty**: both files in this lane sit on AXIS-2; if this
  family is selected, the sibling BASISDYN-PREMVOL is a same-cluster second
  family and is INELIGIBLE under plan Section 1.2 even if otherwise clean.

## 13. Outcome-blind attestation

```
OUTCOME-BLIND ATTESTATION
lane: d1-a6-proposals  proposal: A14-V14-A6-BASISDYN-PREMREV
cycle: CRYPTO-V14  wave SHA: c3e3c90561efc972c487a99951ca0f6031ab4fa34907d1c10890d1795b4da4a8
I wrote this mechanism and its falsification conditions before any return,
metric or ranking exists, without access to any per-arm outcome file, and I
will not modify this proposal after outcomes exist.
utc: 2026-09-05T00:32:32Z  agent: A6 (d1-a6-proposals)
```
