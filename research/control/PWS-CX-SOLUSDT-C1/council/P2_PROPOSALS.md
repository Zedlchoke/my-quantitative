# P2_PROPOSALS — blind proposer P2 — PWS-CX-SOLUSDT-C1 council (outcome-blind)

- Author: BLIND PROPOSER P2 (independent of P1; no coordination, no P1 artifacts read).
- Blindness posture: no outcome/PnL artifacts consulted (none exist for this cycle);
  raw data planes not opened. Cost-book inputs used, per dispatch scope: C1 machine
  census artifacts `C1_machine_FUNDING_STATS_SOLUSDT.json` /
  `C1_machine_KLINE_CENSUS_SOLUSDT.json` (descriptive, pre-outcome, same evidence
  class as the spread-by-hour census the dispatch lists as available), plus control
  documents: `plans/PLAN_pws_program_v1.md` (§1.2, §2.2–2.3, §7),
  `plans/PLAN_pws_cx_solusdt_c1.md`, `research/control/SRLV-PROGRAM-V1/
  OUTCOME_EXPOSURE_MAP.md` §2+§4, `research/control/SRLV-PROGRAM-V1/
  DATACOST_FEASIBILITY_MATRIX.md`, `plans/PLAN_srlv_program_v1.md` (F-0 §2.3,
  PIT §3, kill §10), `research/wayfinder/FAMILY_FAILURES.jsonl` (crypto rows),
  `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/forex_program/
  OWNER_NOTE_cohort2_lessons_2026-09-26.md`.
- Lane angle (decorrelation from P1): premium IS the funding stream, or payer is a
  flow observable in allowed data — funding-capture / carry-shaped books,
  settlement-calendar risk-transfer, cross-plane (1h↔funding) state conditioning.
  Constraints honored: unlevered 1x only; funding-carry ancestors
  (XSECT sleeve COST_DOMINATED ~77:1 cost:carry @ ~0.62x/day turnover) ⇒ any SOL
  carry must be LOW-TURNOVER BY CONSTRUCTION with per-episode ceiling law; price-only
  clause applies; SRLVCX1-M1-SETTLE-RESOLVE fence (settlement-adjacent
  sweep-then-absorption REJECT_ALL, inverted out-earning; same-skeleton variants dead
  regardless of pair; P-28: inverted out-earn = kill, never signal).

## 0. Measured arithmetic that gates this whole lane (from C1 funding census, sha-pinned sources)

- SOLUSDT funding: 6,580 settlements 2020-09-13..2026-08-21 (fapi, nominal 8h;
  FTX-week emergency cadence anomaly 2022-11-09..2022-11-18: 101 spacings of 1–4h).
- **Unconditional funding premium on SOL ≈ zero**: overall mean +0.014 bps/settlement,
  6-year sum +0.91% total; median +0.86 bps/settlement; neg share 28.6%.
  An always-hold-receiver book earns ≈ +0.9% gross over 6 years against an RT
  taker cost of order 10–30 bps per episode — the unconditional carry skeleton is
  dead on the MEASURED distribution before any scoring (this independently
  re-confirms the XSECT 77:1 cost:carry retirement on SOL-specific numbers).
- Conditional tails are the only carrier: 2022 mean −3.25 bps/settlement
  (downtrend state −4.97 bps/settlement, neg share 59%); 2021 mean +2.61
  bps/settlement (longs pay); single settlements reach −200 bps (2022-11-09T20:00Z,
  FTX week) and +33.2 bps (2021-02-10); 2023 min −92.7 bps; 2021 min −75 bps;
  2025 min −30.3 bps. Conclusion: only REGIME-CONDITIONED capture can clear the
  cost bill; every unconditional or fixed-window shape dies at F-5/K-COST pre-PnL.

## 1. SUBMITTED PROPOSAL (rank 1 of 1)

### P2-1 — TAILPAYER-RUN-REGIME CAPTURE (SOLUSDT, unlevered, two-sided)

One-sentence mechanism: when the settled funding series shows a persistent one-sided
payment regime (run of ≥K settlements paid by one side, run-mean ≥ θ), hold the
RECEIVING side until the settled series exits the regime (sign flip) or a hard
settlement-count cap T_max — premium collected is the funding stream itself;
price PnL is reported separately and is NOT part of the mechanism claim.

#### 1.1 The ten mandatory fields (umbrella §5.3)

1. **Payer.** The levered crowd positioned on the losing-crowding side of the
   SOLUSDT perp, which pays funding mechanically at every settlement it remains
   positioned. Why they MUST pay (not merely "usually pay"): funding is a
   contractual cash transfer while a position is held; the payer's alternatives
   (unwind, or hedge spot) are exactly the actions whose crowding produced the
   payment — unwinding is the regime's end, and partial unwinds are staggered by
   venue caps and risk limits, which is what makes payments persist in runs.
   Self-arbitrage exists and is the mechanism's exit: when the payer crowd
   unwinds enough, settled sign flips — the book exits precisely when the payer
   finishes arbitraging. No fictional counterparty: the payer's existence and
   persistence are evidenced by the measured payment series itself (negative
   settlements are the payer's signed receipts), not by narrative.
2. **Premium.** The funding stream itself: per-settlement cash received while
   held. Measured scale on SOL: regime means from −4.97 bps/settlement (2022
   downtrend state) to +2.61 bps/settlement (2021), tail settlements −200 bps
   (FTX week) to +33 bps; entry is gated (field 9 ceiling law) to regimes whose
   run-mean ≥ θ, with θ pinned so run-mean × H_min ≥ full RT stress cost.
   **Price-only clause (mandatory statement): the design target is that NET edge
   = funding credit only.** Price PnL during holds is fully borne (unlevered 1x)
   and dwarfs per-settlement credits in magnitude; the freeze must pre-register
   the decomposition (funding received / paid per settlement, price PnL, costs —
   Q-14 tách bạch). If scored net edge is price-driven, the identity is
   MIS-SPECIFIED (not the proposed carry mechanism) and is killed as spec-fail —
   this is a pre-registered spec check, declared before outcome.
3. **Persistence.** Regime persistence, not point-in-time: a run state is
   expected to persist multiple settlements (venue caps + staggered unwinds).
   Decay mode is observable, not assumed: the run ends at the first settled
   sign flip (or magnitude collapse below θ_renew), which is the exit trigger.
   Time-normalization pin (PIT, pre-registered): because of the FTX-week
   cadence anomaly (101 spacings of 1–4h between 2022-11-09T16:00Z and
   2022-11-18T08:00Z), runs are counted in settlements AND must span ≥ K×6h
   wall-clock to constitute one regime; the FTX week therefore counts as a
   bounded set of episodes, not one windfall run, and cannot dominate by
   cadence stacking.
4. **Risk transferred.** The book holds the full price risk of SOLUSDT (unlevered
   1x) for the regime duration; funding credits (order 1–30 bps/settlement) do
   NOT hedge price risk — the premium bought is small relative to hourly
   volatility, and the mechanism claims only the payment stream. What is
   transferred to the book: the payer crowd's regime-duration exposure to price
   moves adverse to the RECEIVING side (a short-payer regime pays the book to
   hold long into falling markets — that price risk IS the service the payer
   buys). Symmetric by construction (long receiver when shorts pay; short
   receiver when longs pay) ⇒ G8 short-capability satisfied in the anchor
   definition (child plan §2.3 option (a)).
5. **PIT observable + availability evidence.** Settled funding series only for
   the state variable (rate r_s observable AT fundingTime s; next-interval rate
   = PREDICTED ≠ observable — no predicted-rate input anywhere); 1h kline
   completes for the fill clock. Availability: funding floor 2020-09-13
   (6,580 settlements, census sha-pinned in C1_machine_FUNDING_STATS_SOLUSDT.json,
   fapi sources H1+H2 sha256 pinned; Vision cross-check NOT_RUN for SOL —
   disclosed open data-gate item, conflict rule applicable if staged); klines
   52,145 bars 2020-09-14..2026-08-31 with 120 missing bars in two 2022 gap
   windows (no entry with incomplete bars; force-flat across gaps). No
   order-book/liquidation/OI inputs; no sweep/zone geometry anywhere ⇒
   PROXY_NOT_ORDERBOOK label not required for this mechanism (state that
   explicitly in freeze); FUNDING_PATH_STRESSED applies (funding measured
   per-settlement while held, dual-book vs frozen constant).
6. **Holding horizon.** State-contingent: enter on the 1h bar following the
   K-th confirming settlement; hold until (i) first settled sign flip, OR
   (ii) T_max = 42 settlements (≈14 days) hard cap, OR (iii) run-mean decays
   below θ_renew (renewal floor) — all three exits pinned at freeze. Expected
   realized hold: multi-day (est. 1–3 weeks), unmeasured by this lane
   (implementer measures flip hazard at C4; freeze may only raise n).
7. **Capacity.** Unlevered 1x, single venue, single pair (SINGLE_VENUE_PANEL);
   bounded by SOLUSDT perp top-of-book at taker; research-scale capacity
   trivially available; no maker-fill assumption (taker world).
8. **Costs at base + stress (decomposition, taker world).**
   - Fee: 5 bps/side taker = 10 bps RT (DECLARED book, CHR3F convention).
   - Adverse tick: 1/side; price-dependent for SOL (tick 0.01 USDT vs price
     path): negligible at ≥$10 (≤0.1 bp/side), material at 2020 floor prices
     (≥33 bp/side at $1.5) — engine must charge actual per-fill price; pinned
     as MEASURE_AT_C1 from staged klines, stress-banded, never assumed away.
   - Spread: per-fill-hour census from bookTicker/aggTrades — NOT_RUN today ⇒
     **fail-closed: identity is BLOCKED (K-COST, cost auditor) unless the census
     verifies at C1; no number is filled in.**
   - Funding: MEASURED per-settlement path while held (dual book vs frozen
     constant); funding-path stress: SOL distribution re-measured at C1 — do
     NOT inherit BTC/ETH 24.7%/−0.30% constants (measured SOL worst already
     known deeper: −200 bps single settlement).
   - Gap/outage/latency: DECLARED bands ×1.5/×2.0 (venue outage precedent
     418; the two 2022 kline gap windows included in gap-band accounting).
   - **Base RT ≈ 10 bps + tick(actual) + spread(census); stress ×1.5/×2.0 ⇒
     order 15–20 bps → 20–30+ bps.**
   - **Ceiling law (construction, binding):** episode enters ONLY IF
     r̄_run × H_min ≥ RT_stress, with H_min = 3 settlements and RT_stress the
     stressed book; negative expected ceiling ⇒ VETO before scoring (K-COST).
     At measured mild-regime scales (median 0.86 bps/settlement) this gate
     rejects most regimes by arithmetic — that is the intended low-turnover
     construction that answers the XSECT COST_DOMINATED ancestor: turnover is
     endogenous to the gate (only regimes that pre-pay the bill are traded),
     not a rebalance cadence.
9. **Falsifier + control-that-must-not-reproduce.**
   - F-0 court: self-applied in §1.2; skeptic VETO stands.
   - F-1 ancestry: |rho| ≤ 0.20 on the frozen representation vs crypto
     failure-memory shadows (funding-LEVEL carry proxy, CARRY-1D/3D/7D
     reconstruction, TRACKB1-CLASSA, V17 FUNDJUMP event form, H-FUNDCROWD,
     plus §4 fence set). **Honest pre-declaration: this is the single most
     likely pre-PnL kill — a run-gated carry will correlate with funding-LEVEL
     reconstructions; V17 FUNDJUMP already died at rho 0.2439 vs the level
     proxy. If rho fires, the identity dies at zero scored cells — the cheap
     kill the owner note prescribes; no re-labeling rescue.**
   - F-2: funding-settlement timing / kline clock alignment; M-class truncation
     byte-identical for the run-state variable (panel-truncation replay,
     future-mutation, independent implementation — SRLV §3.6).
   - F-5 cost ceiling: per-episode on measured SOL distribution (above).
   - **Controls that must NOT reproduce:** (i) block-shuffled-settlement sham
     book (preserve marginal magnitude distribution incl. tails, destroy
     sign-run structure) must NOT earn ≥0.5× anchor net (K-CTRL); (ii)
     unconditional always-hold-receiver book (the dead CARRY/XSECT form) must
     NOT reach ≥0.5× anchor net — measured arithmetic predicts ≈ 0.9% gross /
     6y, i.e., it should reproduce nothing (gate incrementality test); (iii)
     clock-only calendar book (same UTC fill hours, sign randomized) must NOT
     reproduce.
   - Inverted control: hold the PAYER side during the same regimes; must not
     out-earn anchor (K-CTRL / P-28 — an inverted out-earn is a kill, never a
     re-read signal).
   - K-CONC: top-fold (per-year and leave-one-fold-out) share of positive PnL
     ≤ 0.50, statistic frozen with trial freeze (§5.14 concession, sha-pinned).
     **Honest pre-declaration: deep payments concentrate in 2022 (esp. FTX
     week); K-CONC is the second most likely kill and is NOT relaxable.**
   - K-POWER/K-THIN: floors ≥100 closed RT + occupancy floors (child may only
     raise n). **Third most likely outcome: hard θ gate yields too few
     episodes ⇒ NOT_RUN_THIN — acceptable, cheap, pre-PnL.**
10. **Controls + baseline.** Anchor (two-sided regime book) + ≤2 neighbours
    (N1: θ floor-anchored vs trailing-quantile-anchored definition, same
    everything else; N2: vol-state throttle variant — position to zero when
    trailing 1h realized-vol regime exceeds a frozen percentile band; vol as
    STATE only, incrementality test §2.4 applies, clock-only shadow Q-11
    non-vacuous required) + causal control (block-shuffle sham, above) +
    inverted control (payer side) + baseline set (cash 0% + long SOL with the
    same cost book + TREND_LF; short-beta reference arm as reference, not
    scored cell). Baseline beat margin ≥2× required of anchor (K-CTRL).

#### 1.2 F-0 self-court (honest)

- **Skeleton test.** Strip the run-gate observable, keep trigger/direction/exit
  shape: "hold the receiving side of funding" = the unconditional-carry shape of
  CARRY-1D/3D/7D and the retired XSECT sleeve — same family shape. The
  mechanism's claim is therefore precisely that the GATE adds the mechanism:
  conditional tail regimes pay; the unconditional form does not (measured:
  +0.91% gross over 6 years). Verdict: SURVIVES only as conditional-carry with
  gate-incrementality as the load-bearing falsifier (controls ii/iii above);
  differences vs each named ancestor ≥2 dimensions: vs CARRY-1D/3D/7D —
  information layer (settled run-path statistic vs level windows) + risk shape
  (single-pair directional state-contingent hold vs cross-sectional
  fixed-window book); vs XSECT COST_DOMINATED — risk shape (turnover
  endogenous to per-episode ceiling gate vs 0.62x/day rebalance) + payer
  conditioning (tail regimes only); vs TRACKB1-CLASSA level-gated carry —
  information layer (run persistence vs level) + risk shape (directional
  single-pair vs delta-neutral basket).
- **Payer test.** PASS — contractual mechanical transfer while positioned;
  self-arbitrage (unwind) is observable as the regime end and is the exit;
  payer evidenced by the payment series itself (no fictional counterparty —
  this is the distinction from the BTC-BEAR vetoes).
- **Information test.** PASS — settled-funding path state is not contained in
  clock, trend, or spread (Q-7); the unconditional premium being ≈0 on the
  measured series is itself evidence the information is in the CONDITIONING,
  not the level.
- Net F-0 verdict: **SURVIVES, submitted**, with rho-vs-funding-level shadows
  and K-CONC declared as the two most likely pre-PnL terminations.

#### 1.3 Expected fill-hours profile

Entries only in the 1h bars following settlement confirmations (00/08/16 UTC
± cadence anomalies), i.e., ≤3 candidate entry hours/day; exits at settlement
hours or T_max bar. With a hard θ gate, expected episodes are sparse — order
tens, not hundreds, over 2020-09..2026-08 (unmeasured; occupancy floor
decides). Occupancy well under 1% of the 52,145 1h bars; turnover ≪0.62x/day
by construction (a handful of RTs per year). If episodes < ~100 closed RT ⇒
NOT_RUN_THIN (declared acceptable outcome).

#### 1.4 Anti-variant law statement (master §2.3)

One identity submitted by this lane; no intra-slate pairwise distance applies.
Distance vs every named dead family ≥2 of (payer, information layer, risk
shape) as itemized in §1.2. The two draft variants that failed the F-0 court
against dead families are recorded as withdrawals (§3), not submitted as
filler.

---

## 2. (no second or third submission)

The lane angle admits, on the allowed data, exactly one mechanism-distinct
identity. Drafted candidates P2-2 and P2-3 were self-killed at F-0 (§3). The
measured SOL funding arithmetic (§0) independently closes every unconditional
or fixed-window funding shape at the cost ceiling before PnL, and every
non-funding payer story in the allowed data lands on a fenced family
(aggressor flow, sweep/absorption, calendar-clock) — manufacturing additional
submissions would violate the anti-variant law and P-27 ("adding an observable
is not a new mechanism"), not serve the council.

## 3. Withdrawn ideas (one-line reasons)

1. **P2-2 TAILPAYMENT-OVERSHT FIXED-HORIZON CAPTURE** (enter receiver side for
   exactly H settlements after a |rate| ≥ frozen tail-quantile settlement) —
   WITHDRAWN: vs dead CARRY-1D/3D/7D the trigger difference is a filter/gate
   with identical direction (receiver side), identical exit shape (fixed
   window) and identical payer ⇒ ONE identity by master §2.3
   (VETO_VARIANT_SAME_FAMILY); lives legitimately only as a P2-1 neighbour
   config if the council wants it.
2. **P2-3 REGIME-FLIP UNWIND-CONTINUATION** (trade WITH the flip at regime end,
   hours-scale, payer = residual unwinding crowd) — WITHDRAWN: rescues
   settlement-adjacency by reversal, banned verbatim (master §1.2 +
   SRLVCX1-M1-SETTLE-RESOLVE fence + LESSON P-28: inverted out-earn = kill,
   never signal).
3. **Settlement-clock continuation book** — WITHDRAWN: clock-only skeleton
   reproduces it (K-CTRL), and settlement-adjacency continuation is the
   SETTLE-RESOLVE dead fence regardless of pair.
4. **Taker-flow provision premium** (fade/absorb aggressor imbalance from
   kline taker-buy split) — WITHDRAWN: maker-only provision banned in taker
   world; as taker the "payer" story collapses into spread payment (fictional
   counterparty) and the aggressor/absorption family is dead (M01
   AGGRESSOR-ABSORPTION, V15 TAKER-SAT).
5. **Funding-sign-gated buy-and-hold (long SOL only when shorts pay)** —
   WITHDRAWN: baseline-clone (K-CTRL vs long-SOL baseline) + long-biased (G8)
   + single-dimension filter on the long side of P2-1.
6. **Payment-dispersion regime book** (trade receiver side when funding
   dispersion is elevated) — WITHDRAWN: same payer + same risk shape as P2-1,
   information layer is a second-moment statistic of the same series ⇒ 1
   dimension vs P2-1 (anti-variant law).
7. **Cap-proximity tail book** (trade only near ±venue funding cap) —
   WITHDRAWN: parameter subset of the P2-1 tail gate (a θ choice), not a
   mechanism; cap level is a venue parameter with PIT-provenance problems.
8. **Distress-divergence price gate** (P2-1 entry additionally requires price
   making N-bar lows while payments run) — WITHDRAWN: single-dimension
   price-filter on P2-1's entry; variant, not identity.
9. **Weekend-bounded carry holds** — WITHDRAWN: exit-shape/calendar variant of
   P2-1 (1 dimension); weekend buckets remain disclosure items in freeze, and
   V17 WKNDLIQ ancestry fence risk (rho 0.56 vs dvol shadows) adds nothing
   new.

## 4. Open data-gate items this proposal inherits (fail-closed, disclosed)

1. Spread census NOT_RUN for SOL — P2-1 is BLOCKED at K-COST unless it
   verifies (dispatch-level: "spread census (cost book only)"; child plan §2.1
   fail-closed).
2. Vision funding cross-check NOT_RUN for SOL (no archive; budget went to
   spread census) — conflict rule (any row diff ⇒ symbol-month EXCLUDED)
   applicable if staged later; until then SOL funding is single-source fapi
   with sha-pinned manifests (internal-consistency note in C1 file: H1+H2 are
   the same fapi campaign, NOT independent sources).
3. Funding series ends 2026-08-21 vs klines 2026-08-31 (10.3-day tail
   uncovered) — freeze must pin the force-flat/episode-truncation rule for the
   uncovered tail.
4. FTX-week cadence anomaly (101 spacings 1–4h) — handled by the
   time-normalized run definition (§1 field 3); M-class truncation for the
   run-state variable at F-2.
5. SOL-specific funding-path stress distribution must be re-measured at C1 —
   BTC/ETH constants (24.7% negative in downtrend; worst −0.30%/8h) are NOT
   inherited (measured SOL tail is deeper: −2% single settlement).

## 5. Lane-level honest expectation

Modal outcomes for P2-1, in likelihood order: (1) F-1 ancestry kill vs
funding-level shadows; (2) K-CONC fold-concentration kill (2022/FTX
concentration); (3) K-THIN occupancy floor failure (hard gate ⇒ too few
episodes); (4) survival to scored dev with the F-5 ceiling gate live. All
four are cheap, pre-PnL or low-cell outcomes — the intended use of a
registry-first proposer lane. A profitable-looking number would not be a
valid result unless every reconciliation above holds.
