# DATACOST critic REPORT — ECONOMIC-ROBUSTNESS-PROGRAM-V1 (plan_review)

- Role: quant-datacost-critic (data & cost critic, read-only)
- Cycle: ECONOMIC-ROBUSTNESS-PROGRAM-V1 (umbrella plan, pre-freeze)
- Dispatch/measured HEAD: `7343dde57fe86b38d205b0bec5e8af92a4c4404d` (verified via `git rev-parse`)
- Measured: 2026-09-25. No files modified, no commit, no network downloads, no S1,
  no scored computation. Every number below traces to an existing committed artifact
  (paths in §7) or to explicit arithmetic on guidance thresholds (§1.3, §2.2, §4).
- Sibling artifacts in this directory: SKEPTIC_track_falsification_REPORT.md,
  EXPLORER_state_remeasure_REPORT.md (both read as of 2026-09-25 09:0x; no conflict).

---

## 0. Executive verdict per track

| Track | Verdict | One-line reason |
|---|---|---|
| A — FX intraday liquidity provision (RANGEFADE-class) | **MEASURABLE_WITH_GAPS** | Data + measured spread curves exist and are sha-pinned; all 10 broker cost components UNMEASURED (lane F BLOCKED, third census); paper-shadow cost book is sufficient **only** for paper-tier prospective evidence under 5 conditions (§1.2). |
| B — delta-neutral crypto basis/carry | **MEASURABLE_WITH_GAPS** (funding/basis legs); **BLOCKED** (borrow / margin / liquidation / historical OI) | Funding + klines/mark/index/premium PIT-usable multi-year; basis PIT-bounded (empty pre-2019-11); borrow never measured anywhere in repo; liquidationSnapshot ZERO coverage (404); no margin engine exists. Carry/cost arithmetic says viable only at ≥ ~3–5 week low-turnover holds (§2.2). |
| C — forced-flow/event premiums (crypto) | **BLOCKED** for historical scored use; prospective-collection-first only | No crypto flow source is both historical and PIT-authorizable today: liquidation 404/ZERO, OI retrospective-only (~41.6h REST), keyless WS collectors 34min << 14-day floors, Coinbase l2_data + Deribit trades keyless-rejected. Even the stocks FTD flow source landed PASS_D2_CONTROL_ONLY, not direct signal (§3). |

Default evidence guidance: 5 keep, 5 keep-with-modification, 1 too loose as written
(daily ≥100), 1 needs structural re-specification (H4 "2 volatility regimes"), plus
one missing meta-law (derived-n power law) — full item-by-item table in §4 and the
three most important corrections in §5.

---

## 1. TRACK A — FX intraday liquidity provision (RANGEFADE-class)

### 1.1 What is actually measured (data authority, verified)

- Dukascopy M1 bid/ask corpora: EURUSD 2021–2025 **3,652/3,652 day files, 0 missing**
  + 2026-H1 **362 files, 0 missing** (130,911 valid 15m bars / 30,550 H1; spread
  p50 **0.3 pips**, session/rollover spread census BUILD_PASS); GBPUSD/USDJPY
  **4,014 files/pair, 0 missing** (spread p50 **0.8 / 0.5 pips**; USDJPY 1e-3 price
  scale proven by probe-vs-ticks). `OWNER_DIRECTIVE_SOURCE_AUTHORIZATION` recorded
  with `TCU_RISK_DISCLOSED` (raw bytes machine-local, sha manifests committed).
  Evidence: `research/wayfinder/MAP.md` (EURUSD-OPEN-SEARCH-V1/V2, FX-MAJORS rows);
  `plans/PLAN_fx_rangefade_2m_shadow_v1.md` (TrueFX 15s live-marks seam disclosed).
- Cost authority: DATA-EDGE-UNLOCK-V1 Lane F final verdict
  **`BLOCKED_BROKER_COST_AUTHORITY`** — zero account-bound bytes in the authorized
  evidence space; all ten components UNMEASURED
  (`.../data_edge_unlock_v1/lane_f/f_cost_authority_dossier.json`); stress multiplier
  **2.0 FROZEN pre-outcome** (`FROZEN_2.0_PRIMARY`; frozen_at before any spread
  distribution existed). FOREX-NG7 P0-F4 precedent (blob sha-pinned): TD is a vendor,
  not a broker; "a citable FINANCING band was hunted across the entire authorized
  evidence space and NONE exists"; spread/commission/swap `measurable_from_td=false`.
  The terminal label is the standing state:
  `DATA_EDGE_UNLOCK_V1_PASS_D2_CONTROL_ONLY__BLOCKED_BROKER_COST_AUTHORITY__WAITING_COVERAGE`.
- Realized program facts that bear on the gate: V2 holdout +274.0 pips PF 1.31 /
  +217.1 PF 1.24, **both alive at 2.0× cost stress**, 87 trades (~15/month);
  SHORT_ALWAYS +314.0 on the same window (short-beta control mandatory, still
  unmounted in the running sleeve — review A1); V1's 48-trial campaign: 5/48
  positive at cost, 4/48 at 1.5×, 3/48 at 2.0×, and the single gate-eligible family
  FAILED its one frozen holdout look — dev edge was selection luck.

### 1.2 (a) Is a paper-shadow cost book (measured spread + declared fee buffer) sufficient for prospective evidence without broker cost authority?

**Verdict: YES — for paper-tier prospective evidence only, under five binding
conditions. It is NOT sufficient for any scored-GO / real-money inference, and the
umbrella plan must say so explicitly.**

Rationale. The lane F PASS minimum (A7 F-C1, binding) requires financing components
measured from account-bound bytes; that channel does not exist, so no Track A child
can produce measured commission/financing this cycle. But the RANGEFADE design is
intraday and flat by 20:00 UTC — it carries **zero overnight financing by
construction**. That is categorically different from the forbidden "substitution of
swap by 0": nothing is substituted; the exposure does not exist, and it can be
fixture-enforced. On the components that do bind intraday (spread, increment,
min-size, fee), the repo already holds vendor-measured spread curves (upper-bound
material) plus a frozen 2.0 stress multiplier. The maximum achievable evidence
quality today is therefore a declared-cost book with measured-spread inputs — which
is exactly the F-C1 fallback: "any component left stated-class must be listed
verbatim in the verdict with its stress coverage."

The five binding conditions for sufficiency:

1. **Verdict class bounded.** Output can only ever be
   `CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION` (paper tier). No paper PASS may
   promote to S1/shadow-promotion-with-real-money-inference without Lane F
   `PASS_BROKER_COST_AUTHORITY` (FOREX-NG8 stays closed per standing law).
2. **Structural-zero financing enforced, not assumed.** Flat-by-20:00 UTC must be a
   force-flat fixture in the executor (the V1 pandas force-flat bug — caught by a
   hand fixture before any outcome — is the precedent for why a fixture, not a
   comment, is required). Weekend holds likewise.
3. **Per-session spread, not global p50.** A range-edge fade fills precisely when
   spreads widen (the fade target is an extension event). The executor must charge
   the measured session/rollover spread curve at event time (sha-pinned census),
   not the 0.3-pip global median; the frozen ×2.0 stress then applies to the
   per-regime medians (lane F application_rule).
4. **Adverse selection declared unmeasurable.** Liquidity-provision fill quality
   (queue position, pick-off) is not observable in M1 bid/ask corpora. It must be
   named declared-class in every verdict, stress-covered, and never converted into
   a measured number by assumption.
5. **Marks vs fills seam disclosed.** TrueFX 15s live quotes are indicative marks
   (`TCU_RISK_DISCLOSED`); fills simulated against Dukascopy bars + the seam must
   be disclosed in each report (already the shadow plan's design; carry it forward).

### 1.3 (b) Minimum power analysis: '100 closed round trips + six months' vs the review's 52-week claim

The review's claim (SHADOW-PAPER-REVIEW-V1/REVIEW.md §2.2) is correct and
generalizes. With `SE(SR_hat) ≈ 1/√n` per decision (small-SR limit):

- 52 weeks of daily decisions: n = 252 → SE = 0.063 → 2σ detectable daily SR 0.126
  → **annualized ≈ 0.126 × √252 = 2.0** — matches the review.
- **n = 100 round trips: SE(SR_RT) = 1/√100 = 0.10 → 2σ detectable per-trade SR
  = 0.20.** At a 50% win rate that is exactly a **PF ≈ 1.5** edge
  (PF 1.5 → SR_RT 0.200; PF 1.4 → 0.167; PF 1.3 → 0.130, win=PF·loss, loss=L).
- Annualized at observed cadence: EURUSD RANGEFADE-V2 realized ≈ 174 RT/yr
  (87 in 6 months); detectable 0.20 × √174 ≈ **2.6 annualized**; at the review's
  expected ~350 RT/yr (both FX sleeves), 0.20 × √350 ≈ **3.7** for a 6-month
  sample of ~175.
- **Fixed-window law (i.i.d. approximation): within a fixed calendar window the
  2σ-detectable annualized Sharpe is ≈ 2/√T_years and does not depend on trade
  count**: 6 months → **2.83**; 12 months → 2.00; 2 years → 1.41. More trades in
  the same window sharpen the per-trade estimate, but the calendar length caps what
  the annualized number can statistically exclude. (Trade overlap/vol clustering
  only make this worse, never better.)
- Consequence for the edge class the review names (PF 1.3–1.5): detection needs
  n ≈ 100 (PF 1.5) to **n ≈ 236 (PF 1.3)**, i.e. ~7–16 months at the realized
  cadence. **The 100-RT/6-month gate sits exactly at the PF-1.5 boundary and cannot
  statistically confirm a PF-1.3 edge; a positive-but-below-2σ result is
  INCONCLUSIVE, not a fail and not a pass.**

### 1.4 (c) Exact cost components a Track-A child must measure/bound before any scored cell

From the frozen lane F ten-component table (`f_cost_authority_dossier.json`), the
child's pre-freeze cost book must state measured-vs-declared per component:

| # | Component | Required child treatment |
|---|---|---|
| 1 | Executable bid/ask spread | MEASURED (vendor class): per-session/rollover spread curves from the sha-pinned Dukascopy census; ×2.0 frozen stress applies |
| 2 | Commission | DECLARED buffer, stress-covered; listed verbatim in the verdict (F-C1) |
| 3,4 | Overnight financing long AND short | ZERO **by construction** (force-flat fixture) — documented as construction, never as swap=0 substitution |
| 5 | Triple-swap/weekend accrual | N/A by construction (no weekend holds; fixture-enforced) |
| 6 | Rollover clock/timezone | MEASURED behavior: rollover spread spike handling in the executor (census has the rollover window) |
| 7 | Minimum size | DECLARED; stress-covered |
| 8 | Price increment | MEASURED (EURUSD 1e-5 pip scale; USDJPY 1e-3 probe-proven) |
| 9 | Margin | Report-only, never a profit input (lane F doctrine) |
| 10 | Stress multiplier | 2.0, already FROZEN pre-outcome (lane F component 10, `FROZEN_2.0_PRIMARY`) — child must adopt it unchanged or freeze stricter, never looser |

Plus two child-specific items the lane F table does not cover: (i) event-time fill
realism (spread-at-event vs p50, condition 3 above); (ii) the cost-law identity pin
— the running shadow found the sleeve identity says 6 bps/side while the executor
computes 5 bps + 1 tick (review O2); a Track A child must pin ONE law before its
first fill or every later PnL attaches to the wrong cost law.

---

## 2. TRACK B — delta-neutral crypto basis/carry

### 2.1 (a) MEASURABLE TODAY vs BLOCKED (with repo paths)

MEASURABLE NOW (keyless, PIT-usable multi-year, staged/cross-checked):

1. **Funding** — full Vision fundingRate archive 2020-01..2026-08 (80 monthly files,
   sha-pinned `bear_opportunity_recon_2026-09/data_a2/funding_sha256.json`) + fapi
   pagination precedent + REST backfill 2019-09-10..2019-12-31; **7,643 settlements
   decoded** (`funding_in_downtrend.json`). Channel pinning + conflict policy frozen
   in `plans/PLAN_crypto_historical_replication_3f_v1.md` §4 (fapi primary, vision
   cross-check; any disagreement → symbol-month EXCLUDED, fail-closed, no silent
   merge). Recon A2: PIT_USABLE.
2. **Klines / mark / index / premium klines** — PIT_USABLE 2020-01→2026-08/09,
   byte-pinned, deterministic (recon A2 measured inventory; CHR3F §4 vision-monthly
   + fapi cross-check staging).
3. **Basis** — `/futures/data/basis` PERPETUAL 15m (the V14 frozen signal route) +
   indexPriceKlines cross-check; bulk staging ≈6.4k calls ≈18h under heavy lock
   (CHR3F §4). **PIT-bounded: endpoint empty before 2019-11** (CHR3F §3: 2019 fold
   = `NOT_RUN_DATA` + `NOT_RUN_IDENTITY_UNIVERSE`, ≤2 tradeable names).
4. **Spot leg data** — Vision spot klines (keyless) — the spot side of a
   delta-neutral book is measurable on the same staging plane.

UNMEASURED (no artifact measures it; blocks specific variants):

5. **Spot-margin borrow rates/availability** — NOT in the repo; no artifact measured
   it. `data_a2/short_feasibility.md` §2: a perp short needs **no stock-loan/borrow**,
   but a spot-margin short "would instead require measured borrow availability +
   borrow fees + rebate" — none measured anywhere. Any levered/borrow-based Track B
   variant is NOT executable as scored evidence today. (Searched: no borrow-rate
   artifact exists in research/control/ or research/hypotheses/.)
6. **Margin schedules / liquidation engine** — PSV1 accounting had **no margin
   engine** (linear costs, no equity path) and short_feasibility §3 enumerates the
   mandatory additions (maintenance-margin schedule → liquidation price; gap-vs-touch
   trigger law; ADL/partial-liq/insurance-fund interactions — all unmodeled). Margin
   is report-only per lane F doctrine (component 8).

BLOCKED (zero coverage / 404 / prospective-only):

7. **Historical liquidation prints** — um `liquidationSnapshot` 404 probed at
   2019-10, 2020-03-12 (daily), 2020-06, 2021-06 → **ZERO coverage**
   (`audits_a7/a7_recon_audit.md`; `data_a2/s3_structure.json`:
   "no liquidationSnapshot prefix under um/ or cm/").
8. **Multi-year PIT OI / order book** — none. `metrics` is retrospective-only daily
   publication; REST OI ≈41.6h lookback (recon A2). OI history rebuilt from REST
   would be overwritten data, not PIT.
9. **Cross-venue L2/trade streams** — prospective only: lane C ran
   **02:57:31Z→03:31:43Z ≈ 34 minutes << 14-day floors** (`floors_met: false`),
   Coinbase `l2_data` keyless-rejected ("authentication failure"), Deribit trades
   keyless-rejected (error 13778) — the depth/trade observables are not even
   collectable keyless on 2 of 3 venues
   (`data_edge_unlock_v1/lane_c/terminal_waiting_coverage.json`).

### 2.2 (b) Round-trip cost vs funding carry — is the ratio viable, at what holding period?

Cost side (analytic on frozen laws, not a scored cell):

- Delta-neutral book = 2 legs × open/close = **4 taker fills**. Fee-only RT =
  4 × 5 bps = **20 bps**. Executor law adds 1 tick/fill: on BTCUSDT a 0.1-USDT tick
  is ≈0.0002–0.001 bps — negligible; on low-price alt perps the tick term is
  material. Realized XSECT shadow ratio slip/fee = 56.40/246.43 ≈ 23% → a
  realistic all-in RT is **≈ 20–25 bps** (stress ×1.5 → 30–37.5 bps).

Carry side (repo-measured; short perp RECEIVES positive funding):

- In-downtrend mean **+3.709e-5/8h = 0.371 bps/8h = 1.11 bps/day = 7.79 bps/week**
  (≈ +4.06%/yr) — `funding_in_downtrend.json`.
- Altcoin snapshot band (NOTES.md §13.5, 30-day bullish window, self-flagged as
  NOT causal): **0.281–0.593 bps/settlement × 21 settlements/wk = 5.9–12.5 bps/wk**
  (0.84–1.78 bps/day).
- Full-window mean +1.073e-4/8h ≈ 11.7%/yr — the number behind BTC-H4-EDGE-SEARCH's
  **11.798%/yr = 7.824× the frozen 1.377e-5 constant** (≈1.51%/yr); it includes the
  bull regime, so it overstates a defensive carry book's expectation ~2.6× vs the
  in-DT mean.

Breakeven arithmetic (carry ÷ cost):

- **20–25 bps RT ÷ 1.11 bps/day ≈ 18–23 days** (in-DT funding); at 1.5× stress
  (30–37.5 bps) ≈ **27–34 days**. Altcoin band: 11–24 days at base, 17–36 days at
  1.5×.
- **Verdict: the carry/cost ratio is viable only for low-turnover holds of roughly
  ≥ 3–5 weeks.** Weekly-rebalance churn is structurally unviable, which is exactly
  what the shadow already realized: XSECT booked **cost 302.83 (fee 246.43 +
  slip 56.40) vs funding +4.60 over 10 decisions / 48 fills — a 66:1 cost:carry
  inversion**, cost run-rate ~11%/yr against ~1.7%/yr of carry
  (SHADOW-PAPER-REVIEW-V1 sleeve table + lane_crypto_sleeves REPORT). Review A2's
  hysteresis amendment is the right structural response; the umbrella guidance
  should state the breakeven horizon law so children pre-size turnover.
- Funding-sign risk bound: **24.7% of in-downtrend settlements are NEGATIVE** and
  the worst single in-DT settlement is **−0.30% of notional (cap-binding) ≈ 2.5
  perp-side fee round trips in one 8h tick**. The breakeven horizon is a mean, not
  a floor: any carry child must add a funding-PATH stress (worst-settlement ×
  horizon, negative-run persistence), not just fee ×1.5.

### 2.3 (c) Survivorship / PIT traps for venue-level basis data

1. **Three different funding floors**: fapi settlements start 2020-07-18; Vision
   monthly archive starts 2020-01; A2 REST backfill reaches 2019-09-10. CHR3F §4's
   frozen conflict rule (vision shows pre-2020-07-18 settlements fapi lacks →
   symbol-month EXCLUDED) means a naive union silently inflates history. Any Track B
   history claim must name which floor it uses.
2. **Basis endpoint empty before 2019-11**; the 2019 fold is `NOT_RUN_DATA` +
   `NOT_RUN_IDENTITY_UNIVERSE`. Pre-2019 basis backtests are impossible from this
   venue — never reconstructed.
3. **Universe survivorship**: PIT listing eligibility from the measured first-archive
   month (P0 census); `onboardDate` corroboration only; no current-membership
   reconstruction; Y2023+ listings (PEPE/SUI/WLD/ONG/ACE) enter/exit by the frozen
   PIT law (CHR3F §3/§4).
4. **Venue/instrument survivorship**: `/futures/data/basis` PERPETUAL reflects the
   surviving venue's currently-listed perps at query time — delisted contracts
   vanish silently. The basis universe must be intersected with listing windows, and
   cross-venue basis claims additionally inherit that only surviving venues expose
   APIs at all.
5. **Overwritten REST surfaces**: REST OI ≈41.6h lookback and `metrics`
   retrospective-only — anything not archived at the time is not PIT.
6. **Snapshot bias**: NOTES §13.5's altcoin funding table explicitly flags its own
   30-day window as bullish/crowded — usable as a magnitude sanity check, never as
   carry expectation.
7. **Venue rule truncation**: the ±0.3% funding cap binds in extremes — a real,
   venue-native truncation that must be preserved in any tail model.
8. **Event-irreversibility**: BASISLV's 286-bar vendor gap burned one event_id
   permanently — staging holes are unrecoverable at the decision level, so coverage
   floors must be checked BEFORE the first decision stamp, not after.

---

## 3. TRACK C — forced-flow/event premiums directly observable

**Question: which observable flow source is BOTH directly observable AND
PIT-authorizable for historical scored use today?**

**Answer: NONE in the crypto forced-flow/event class.** Each candidate measured:

| Candidate | Directly observable (historical)? | PIT-authorizable? | Evidence |
|---|---|---|---|
| Binance liquidation prints | NO — `liquidationSnapshot` ZERO coverage, 404 at every probed vintage | n/a | `bear_opportunity_recon_2026-09/audits_a7/a7_recon_audit.md`, `data_a2/s3_structure.json` |
| Multi-year PIT OI / order book | NO — metrics retrospective-only; REST OI ≈41.6h | NO (overwritten data) | recon A2 |
| Keyless WS (Coinbase/Kraken/Deribit) | NO — streams begin at connect; 3/3 FDF proofs are prospective-only ("begin prospective history; do not imply historical", `PLAN_free_data_frontier_v1.md`) | Prospective only, and floors unmet: **34min << 14-day floors** (303/336 + 152/168 STRICT, ≥4 cells/control/fold, ≥4 weekend days, STRESS bar else NOT_RUN_COVERAGE) | `lane_c/terminal_waiting_coverage.json` |
| Cross-venue / ETF flow | Not acquired, not measured | NOT gated — "separate data-authority cycle required" | MAP.md bear-recon row |
| SEC FTD (stocks forced-flow adjacent) | YES — 434 zips 2009-07..2026-08 local | **Only as control**: Lane S terminal = `PASS_D2_CONTROL_ONLY` (direct historical use stays RETROSPECTIVE_ONLY; no STOCKS-NG7) | DATA-EDGE-UNLOCK-V1 terminal label |

The bear recon already closed the mechanism layer on top of this:
`NO_ELIGIBLE_PROPOSAL` — both proposed forced-flow mechanisms vetoed pre-PnL
(VETOED_FICTIONAL_COUNTERPARTY; VETOED ×3 incl. preregistered neighbour control
firing opposite), with the standing reopening condition "a materially new evidenced
information source (real liquidation/OI tape from an authorized venue) or an owner
plan naming a changed killer".

**Consequence for the umbrella plan (stated as the track's gate):** Track C child
cycles **must be prospective-collection-first with a coverage floor before any
proposal lane**. Concretely: adopt the frozen Lane C contract numbers as the
pre-proposal floor — **≥303 of 336 H1 valid triads total and ≥152 of 168 per 7-day
fold (STRICT), ≥4 cells/control/fold, ≥4 weekend days populated, ≥1 STRESS-crossing
bar else the event cell is NOT_RUN_COVERAGE fail-closed, outcome-independent
stopping rule, collector never adjusted after any result** — and the CNG4 60-day
floor remains the successor's bar. Note the depth caveat: Coinbase `l2_data` and
Deribit trades are keyless-rejected, so the plan's floor currently certifies only
ticker/trades(Kraken)/book(Kraken+Deribit) health, not full depth-of-book — the
forced-flow observable itself may need a new source authorization, which is an owner
action, not a lane action.

---

## 4. Default evidence guidance — item-by-item verdict

Reference claim (review §2.2, verified arithmetic): a 52-week window resolves
annualized Sharpe ≥ ~2.0 at 2σ; fixed-window law 2/√T_years (6m → 2.83, 1y → 2.00,
2y → 1.41); per-trade detection n ≥ (2/SR*)².

| # | Guidance item | Verdict | Reason / adjustment |
|---|---|---|---|
| 1 | FX intraday ≥100 closed RT + 6 months | **KEEP the floor, add two laws** | n=100 detects SR_RT 0.20 = PF≈1.5 at 50% WR — exactly the top of the review's PF 1.3–1.5 class; PF 1.3 needs n≈236 (~7–16 months at realized cadence). (i) derived-n law: child freezes n_floor = ceil((2/SR*)²) from a preregistered SR*; (ii) window ≥12 months for annual event seasonality (NFP/FOMC/quarter-end/Dec liquidity — 6 months covers half the cycle); a floor-only positive that is <2σ is INCONCLUSIVE, not PASS. |
| 2 | H4 ≥50 closed trades + 2 volatility regimes | **TOO LOOSE as written; regime clause needs re-specification** | n=50 detects only SR_RT 0.283 (PF≈1.75) — above the whole PF 1.3–1.5 class; and BTC-H4-TWO-REGIME measured the regime side: 14,589 H4 bars → 15 state changes in 6.7y → merged episodes 5/6/5, **ALL states FAIL floors 20/3/100 → every state-gated arm NOT_RUN_THIN**. Raise n to ≥100 (detects SR_RT 0.20); re-specify "2 regimes" as either (a) regime exposure disclosed + regime as CONTROL (never a scored cell) unless preregistered floors pass, or (b) fail-closed NOT_RUN_THIN with no relaxation (already owner law). BANDRIDGE's 0-fills-under-positive-cost shows the H4 class cannot even accumulate trades at current cost laws — cost identity must be pinned first (O2). |
| 3 | Daily ≥100 valid decisions | **TOO LOOSE / internally inconsistent** | n=100 daily → 2σ annualized ≈ 3.17, *stricter* than the 52-week 2.0 the same guidance cites. Either raise to ≥252 valid decisions (one full year → the 2.0 bar, matching the review) or keep 100 explicitly labeled a smoke floor whose verdicts top out at INCONCLUSIVE. As written it silently changes the detectable-edge bar between tracks. |
| 4 | Weekly ≥52 valid decisions | **KEEP** | Exactly the review's 2.0-resolution bar (2/√52 weekly → 2.0 annualized). Add the honesty clause: for the measured PF 1.35–1.36 weekly class (V11/V14), weekly SR ≈ 0.1 → ~400 weeks needed — one clean year can neither confirm nor kill; the XAUUSD O3 time-law precedent (kill-unfundable law instead of waiting for statistics) is the template for thin-cadence sleeves. |
| 5 | Positive under base cost | **KEEP** | Necessary condition; engine cost honesty already proven (RANDOM_MATCHED −8,948.6 pips in V1). |
| 6 | Non-negative under 1.5× cost unless stricter child contract | **KEEP, add per-track stress specification** | The generic ×1.5 is the wrong stress for two of three tracks: FX must use the frozen spread ×2.0 multiplier (lane F component 10); crypto carry books must add funding-PATH stress (24.7% negative in-DT settlements; worst −0.30% single settlement = 2.5 fee RTs) — fee ×1.5 alone does not stress the actual risk (XSECT: positive under base fee, −298.22 realized on turnover). CHR3F's ×1.5/+2 ticks/+1 event delay is the directional precedent. |
| 7 | Report 2× | **KEEP** | Real discriminating power measured: V1 survival 5/48 → 4/48 → 3/48 across 1×/1.5×/2×; USDJPY dies at 2× while GBPUSD/EURUSD-V2 holdouts stay alive — the 2× column is what separated robust from thin candidates. |
| 8 | Majority positive chronological folds | **KEEP with floors wired** | 3-fold majority = 2 is weak, so bind folds to the CNG4 contract floors (≥4 cells/control/fold) and prefer ≥4 folds where sample allows. The fold machinery is measured to work: 6/6 folds positive carried GBPUSD; fold-structure failures (V14 3/3 positive but fold-share gate) caught elsewhere. |
| 9 | Top fold/event contribution ≤50% unless preregistered | **KEEP — most productive gate in the program** | Measured kills: V11 0.7055, V14 0.5110, XSECT 51.66%, BTC-H4-EDGE lane C 0.7294/0.7117 — the fourth occurrence of the "single-regime money" pattern. Do not loosen; the preregistered-alternative escape hatch already exists. |
| 10 | Beat simple baseline + causal control | **KEEP, enumerate the mandatory controls per track** | FX: SHORT_ALWAYS short-beta control (ancestor MANDATORY; +314.0 pips on the same V2 holdout window; currently UNMOUNTED in the running sleeve = largest FX compliance gap) + JPY carry-beta control for USDJPY (LONG_ALWAYS +532.5 dominates the carry-rally window). Crypto: block-shuffled causal control (G6 precedent: shuffled gate out-earned the gated book on both BTC cells) + RANDOM_MATCHED + a pre-score funding-accounting declaration (frozen 1.377e-5 vs full-window 1.073e-4 vs in-DT 3.709e-5 — which number, stated before scoring). |
| 11 | DSR across all trials | **KEEP** | Trial accounting is live and load-bearing (program ledger 400/403 union; V14 family DSR 0.00224 at N=146; FX DSR-N bound ≤80 with program-cumulative 260-at-0.05 still reported). The umbrella plan must restate that DSR denominators include every child-cycle trial from RT #1 (no "exploratory" exemptions). |
| 12 | PBO where variant/fold structure supports it | **KEEP, define the minimum structure** | PBO/CSCV on thin structures is noise. Minimum supporting structure to state in the plan: ≥2 frozen variants × ≥6 chronological folds; below that, record "PBO NOT_SUPPORTED_STRUCTURE" rather than a computed number. DSR alone is not a substitute (different failure mode). |
| 13 | Independent reproduction before S1/shadow promotion | **KEEP** | Working as designed: S1 reproduction 12/12 byte-exact (EURUSD-RANGEEXP), detached twin ALL_MATCH/byte-identical (TWO-REGIME, BTC-H4-EDGE), and the A7 prelaunch REFUSE arc (V1 r1 refused → remediated → r2 authorized) proves the gate bites. |

Missing meta-item to add (the owner's "subject to pre-freeze power analysis" made
concrete): every child plan pre-freezes (i) expected decision/RT cadence,
(ii) SR* = minimum interesting per-trade edge, (iii) n_floor = ceil((2/SR*)²),
(iv) calendar months ≥12 for assets with annual seasonality, (v) the fixed-window
disclosure that no window shorter than (2/SR_annual_min)² years can statistically
confirm that annualized Sharpe.

---

## 5. The three most important corrections to the default guidance

1. **Make the power law explicit and cadence-aware (fixes items 1–3).** Replace
   round-number floors with the derived-n law n_floor = ceil((2/SR*)²) at a
   preregistered SR*, plus the fixed-window law SR_annual_min ≈ 2/√T_years. Today's
   guidance is internally inconsistent: 100 daily decisions implies a 3.17 annualized
   detection bar while the same document cites 2.0 for 52 weeks; 100 FX round trips
   detect only PF≈1.5-class per-trade edges; and H4 at n=50 detects PF≈1.75 — above
   every edge class the program has actually produced (V1 gate-eligible candidate
   was PF 1.14; holdout survivors PF 1.24–1.64). Consequence to write into the plan:
   at floor-level n, a <2σ positive is INCONCLUSIVE — it must not be recorded as a
   PASS, and a negative at floor-level n against a thin edge must be recorded as
   UNRESOLVED (multi-year continuation or time-law), not as a mechanism kill.
2. **Stress must match the binding risk per track, not a generic 1.5× fee
   multiplier (fixes item 6).** The measured failure mode of the live program is not
   fee uncertainty — it is (a) turnover × cost for carry books (XSECT: 66:1
   cost:carry realized, ~11%/yr drag vs ~1.7%/yr carry) and (b) funding-sign path
   risk (24.7% negative in-DT settlements; −0.30% worst settlement = 2.5 fee RTs in
   one 8h tick), plus (c) event-time spread for range fades. The umbrella guidance
   should therefore require: FX → frozen spread ×2.0 on per-regime/session medians;
   crypto carry → funding-path stress + turnover budget derived from the ≥3–5 week
   breakeven horizon; directional H4 → the CHR3F ×1.5/+2 ticks/+1 event delay law.
   And it should pin the cost-law identity (6 bps vs 5 bps + 1 tick) as a pre-fill
   freeze item for every child.
3. **Gate Track C (and any venue-native crypto child) on prospective coverage
   floors BEFORE proposal lanes are allowed, and say what the floors do not cover.**
   No crypto flow source is historical-and-PIT-authorizable today (liquidation 404/
   ZERO; OI overwritten; WS 34min << floors; Coinbase depth + Deribit trades
   keyless-rejected). The umbrella plan should bind Track C children to the frozen
   Lane C contract floors (≥303/336 + ≥152/168 STRICT, ≥4 cells/control/fold, ≥4
   weekend days, STRESS-event bar else NOT_RUN_COVERAGE, 60-day successor bar,
   outcome-independent stopping) as a precondition for any proposal lane, and must
   disclose that the currently-collectable keyless channels do not include the
   depth-of-book observable the forced-flow thesis needs — that gap is an owner
   source-authorization decision, not something a child cycle can measure into
   existence.

---

## 6. Minor corrections / disclosures for the umbrella plan author

- The 52-week ≈ 2.0 claim is an i.i.d. approximation; vol clustering and trade
  overlap widen SE (factor up to ~√(1+2Σρ)), i.e. real detectable thresholds are
  *higher* — the guidance errs optimistic, never pessimistic, so the floors are
  lower bounds on what must be collected.
- Lane C's 34-minute run means its terminals are STARTED/STARTED_WITH_CHANNEL_
  DEGRADATION, not validated coverage; the A7 terminal itself flagged stats-vs-
  manifest mismatches on 2 of 3 venues (FND-2). The umbrella plan should cite the
  contract floors as the authority and the 34-minute run only as a liveness proof.
- Funding numbers have three live candidates in repo artifacts (frozen 1.377e-5,
  full-window 1.073e-4 ≈ 11.8%/yr, in-DT 3.709e-5 ≈ 4.06%/yr). The 7.8× disclosure
  is program law now; the umbrella plan should require each child to name its
  funding number pre-score rather than inheriting any of the three silently.
- Altcoin funding 0.281–0.593 bps/settlement (NOTES §13.5) is a 30-day bullish
  snapshot on 6 symbols — carry children on alts need their own multi-year funding
  restage before any carry expectation is quoted.

## 7. Evidence index (all paths relative to repo root, HEAD 7343dde5)

- `plans/PLAN_data_edge_unlock_v1.md` (§3 lane F ten components + PASS minimum;
  §4 lane C 14-day floors 303/336, 152/168, ≥4 cells, ≥4 weekend days, STRESS bar)
- `.worktrees/data-edge-unlock-v1/integration/research/control/data_edge_unlock_v1/
  lane_f/f_cost_authority_dossier.json` (BLOCKED; ten-component table; stress 2.0
  FROZEN_2.0_PRIMARY) and `.../audits/a7_terminal_data_edge_unlock_v1.json`
  (terminal label PASS_D2_CONTROL_ONLY__BLOCKED_BROKER_COST_AUTHORITY__WAITING_
  COVERAGE; FND-1..6)
- `.worktrees/data-edge-unlock-v1/integration/research/control/data_edge_unlock_v1/
  lane_c/terminal_waiting_coverage.json` (34min << 14 days; Coinbase l2_data
  keyless-rejected; Deribit trades error 13778; floors_met false)
- `.runtime/orchestrator_v3/inbox/deu-f-handoff.json` (lane F handoff, owner
  deliverable options)
- `research/wayfinder/MAP.md` (EURUSD-OPEN-SEARCH-V1: 3,652 files, spread p50 0.3,
  OWNER_DIRECTIVE_SOURCE_AUTHORIZATION + TCU_RISK_DISCLOSED, 48-trial campaign
  5/4/3 survival; V2: +2026-H1 362 files, holdout PF 1.31/1.24 alive at 2×, 87
  trades, SHORT_ALWAYS +314.0; FX-MAJORS: 4,014 files/pair, 0.8/0.5 pips, USDJPY
  dies at 2×, JPY carry-beta control; DATA-EDGE lane C row; bear recon row)
- `research/control/SHADOW-PAPER-REVIEW-V1/REVIEW.md` (7-sleeve table incl. XSECT
  −298.22 = fee 246.43 + slip 56.40 vs funding +4.60, 10 decisions/48 fills; §2.2
  52-week ≈ 2.0 at 2σ claim; §2.5 declared-vs-measured cost book; O1–O6, A1–A4)
- `research/control/SHADOW-PAPER-REVIEW-V1/lane_crypto_sleeves/REPORT.md` +
  `HANDOFF.json` (Σfee/Σslip/Σfunding row; funding 11.798%/yr from
  `btc_h4_edge_search_v1/freezes/feasibility_census.json`)
- `research/wayfinder/HYPOTHESIS_LEDGER.md` (BTC-H4-EDGE-SEARCH-V1 row: 11.798%/yr
  = 7.824× frozen 1.377e-5; V14 DSR 0.00224 N=146)
- `plans/PLAN_crypto_historical_replication_3f_v1.md` (§2 frozen identity/costs
  taker 5bps + 1 tick, stress ×1.5/+2 ticks/+1 delay; §3 windows: 2019
  NOT_RUN_DATA + NOT_RUN_IDENTITY_UNIVERSE, funding floor 2020-07-18, basis empty
  2019-11; §4 data authority + conflict policy + PIT listing law)
- `research/control/bear_opportunity_recon_2026-09/RECON_ADJUDICATION.md`,
  `data_a2/short_feasibility.md`, `data_a2/funding_in_downtrend.json`,
  `data_a2/funding_sha256.json`, `data_a2/s3_structure.json`,
  `audits_a7/a7_recon_audit.md` (liquidationSnapshot ZERO/404; funding 7,643
  settlements; in-DT +3.709e-5/8h, 24.7% negative, worst −0.30%; no-borrow perp
  short; margin-engine gaps; OI ≈41.6h)
- `NOTES.md` §13.5 (altcoin funding 0.281–0.593 bps/settlement, bullish-window
  disclaimer), §13.6/13.7 (TradFi history gates)
- `plans/PLAN_free_data_frontier_v1.md` (streams "begin prospective history; do
  not imply historical")
- `research/control/forex_search_v1/audits/a7_plan_forex_search_v1_r3.json`
  (FOREX-NG7 F4 lineage, cost/financing bands with stress-2.0 primary)

## 8. Honest limitations

- All arithmetic in §1.3/§2.2/§4 is closed-form on published constants (SE ≈ 1/√n
  small-SR limit; PF→SR at 50% WR; linear carry accrual). It ignores higher
  moments, autocorrelation and overlap — all of which push detectable thresholds
  UP, so no conclusion above flips direction.
- The PF→SR mapping assumes a two-outcome symmetric-loss distribution; real trade
  PnLs will shift n_floor by tens of percent, not by an order of magnitude.
- The XSECT realized cost figures are a 10-decision snapshot of a running sleeve
  (review's own limitation) — used here only as a realized-ratio corroboration of
  the analytic 20–25 bps RT, never as an expectation.
- I did not re-measure any corpus or re-run any collector (read-only dispatch); all
  corpus/file counts are quoted from the committed census artifacts named in §7.
