# FOREX frontier pre-cycle survey (proposal-side)

- task: `fxf-researcher-frontier-1`, cycle `FOREX-PRECYCLE-SURVEY` (NOT registered)
- base SHA: `53d2d152c5c5ad61a772c81e3437d1dfd22a0d05` (main, verified equal to
  HEAD at start; no git writes performed)
- date: 2026-09-15. No returns/PnL computed anywhere. No returns computation
  is proposed by this document; all numbers quoted are recorded kill evidence
  from prior terminals, never re-derived here.
- role: RESEARCHER, proposal-side only. A separate independent critic owns the
  kill attempt; nothing here is self-certified.
- reading compliance: MAP.md (all FOREX entries V2..V9, NG1..NG4), LESSONS.md
  (P-1..P-24, Q-1..Q-16), HYPOTHESIS_LEDGER.md §D/§E.2, FAMILY_FAILURES.jsonl
  (all forex rows parsed), PLAN_forex_ng1..ng4, terminal reports read from the
  integration branches (`orca/forex-ng{1,3,4}-integration:research/control/
  forex_ng*_run/...` — the .worktrees/ copies were removed by the
  owner-ordered 2026-09-12 cleanup; evidence lives in branches per the
  cleanup manifest `research/control/WORKTREE_CLEANUP_2026-09-12.json`).

---

## 1. Dead-family inventory (the forex ancestry this survey must differ from)

29 forex family rows in `research/wayfinder/FAMILY_FAILURES.jsonl`
(parsed programmatically; FOREX-NG2 scored zero proposals — P0 census kill —
so it contributes no family rows, only a frontier deferral).

| # | family_id | ledger row | kill reason (primary) |
|---|---|---|---|
| 1 | FOREX-F1 paid-source-era | §D, entry 2026-09-07 | SOURCE_ACCESS_OR_LICENSE_BLOCKED (never scored; no FX data authority) |
| 2 | FXFV1-A3-P1 London-open continuation | §D V1 | EXPECTANCY_NONPOSITIVE (−2.35/trade, PF 0.849, cost-dominated, 11,459 trades) |
| 3 | FXFV1-A3-P2 Late-NY fade | §D V1 | EXPECTANCY_NONPOSITIVE (6/6 REJECT) |
| 4 | FXFV2-A4-P1 Tokyo-range→London expansion | §D V2 | EXPECTANCY_NONPOSITIVE (−3.804/trade; break-even −0.40bps: gross already negative) |
| 5 | FXFV2-A4-P2 London-AM break+retest | §D V2 | CONTROL_REPRODUCED_MECHANISM (placebo ≈ anchor) |
| 6 | FXFV3-A5-P1 family1 | §D V3 | EXPECTANCY_NONPOSITIVE (all arms) |
| 7 | FXFV3-A6-P1 vol-gated policy-rate carry | §D V3/V3R | DATA_AUTHORITY_INVALIDATED (BIS availability inferred; PF 1.2825 under evidenced books but STRESS_TIER_FAIL; carry front door later closed by measurement at V4 D2, rho 0.997–1.000) |
| 8 | FXFV4-A6-P1 commodity-bloc risk-off basket | §D V4 | STRESS_TIER_FAIL (whisper-positive PF 1.0142, all robustness bars fail) |
| 9 | FXFV4-family2 | §D V4 | EXPECTANCY_NONPOSITIVE (−14.83) |
| 10 | FXFV5-A6-P1 pre-release avoidance | §D V5 | CONTROL_OUTEARNED_ANCHOR (+7d sham calendar #10) |
| 11 | FXFV6-A4-P1 own-economy CPI reaction-direction | §D V6 | PF razor (1.0979 vs 1.10, margin −0.0021) + concentration/BE/LOPO — robustness death of a sham-NEGATIVE (genuine-calendar-information) anchor |
| 12 | FXFV6-A6-P2 USD-PC1 gated reversal | §D V6 | EXPECTANCY_NONPOSITIVE |
| 13 | FXFV7-A4-P1 cross-economy spillover | §D V7 | FALSIFIED-BY-CONTROL #12 (+7d sham reproduces; reaction-direction class CLOSED both economy sides) |
| 14 | FXFV7-A6-P2 EURUSD lead-lag diffusion | §D V7 | CONTROL_OUTEARNED_ANCHOR (own-lag: lead content NEGATIVE information) |
| 15 | FXFV8-A5-P1 inflation-compensation dispersion | §D V8 | FALSIFIED-BY-CONTROL #14 (DGS10 LEVEL out-earns 4.01x — nominal-yield-level exposure) |
| 16 | FXFV9-A4-P1 | ledger V9 row | ANCESTRY_RHO_BLOCK 0.2599 vs V8 nominal-level shadow |
| 17 | FXFV9-A4-P2 | ledger V9 row | ANCESTRY_RHO_BLOCK 0.4842 |
| 18 | FXFV9-A5-P1 PPP-deviation | ledger V9 row | ANCESTRY_RHO_BLOCK 0.3034 (frozen-representation re-measure, P-12 origin) |
| 19 | FXFV9-A5-P2 | ledger V9 row | ANCESTRY_RHO_BLOCK 0.3119 |
| 20 | FXNG1-A5-P1 release-order print drift | ledger NG1 row | EXPECTANCY_NONPOSITIVE (−9.81/trade; negative at gross; NOT a V7 re-clock) |
| 21 | FXNG1-A4-P2 CPI acceleration | ledger NG1 row | FALSIFIED-BY-CONTROL #15 (CTL-DGS10LEVEL out-earns) |
| 22 | FXNG3-A4-P1 CA revision sign drift | ledger NG3 row | ANCESTRY_RHO_BLOCK 0.2138 vs release-order shadow |
| 23 | FXNG3-A4-P2 CA revision magnitude | ledger NG3 row | ANCESTRY_RHO_BLOCK 1.0 (book = 8 events, all v2-2018) |
| 24 | FXNG3-A5-P1 CA differential | ledger NG3 row | CONTROL_SELF_SUBSUMPTION CTL-V7NODIFF 1.0 (V7 re-clock; Q-11 INVALID NULL distinction recorded) |
| 25 | FXNG3-A5-P2 CA revision transfer | ledger NG3 row | ANCESTRY_RHO_BLOCK 0.8932 vs day-of-week |
| 26 | FXNG4-A4-P1 EZ print-deviation | ledger NG4 row | ANCESTRY_RHO_BLOCK 0.8883 vs generic day-of-week (33/37 events = Fridays) |
| 27 | FXNG4-A4-P2 EZ trailing-YoY | ledger NG4 row | ANCESTRY_RHO_BLOCK 0.8908 vs dow |
| 28 | FXNG4-A5-P1 EZ-US revision differential | ledger NG4 row | ANCESTRY_RHO_BLOCK 0.8896 vs dow + 0.4429 vs V9 PPP |
| 29 | FXNG4-A5-P2 EZ-US magnitude diff | ledger NG4 row | ANCESTRY_RHO_BLOCK 0.8896 vs dow + PPP |

Plus V1/V2 rows cross-referenced above (V1=2, V2=2, V3=2, V4=2, V5=1, V6=2,
V7=2, V8=1, V9=4, NG1=2, NG3=4, NG4=4, F1=1 → 29).

### Closed classes (the shape of the wall)

- **Session/intraday price geometry** (V1, V2): cost-dominated, gross already
  negative in places.
- **Carry / policy-rate differential** (V3, V4 front door): data-authority
  invalidated + measured rho 0.997–1.000 vs invalidated ancestors.
- **Release-calendar reaction/avoidance/spillover/lead-lag** (V5, V6, V7):
  reaction-direction class closed on BOTH sides of the economy boundary;
  V6 near-miss died on robustness (sham control negative there — genuine
  calendar information, untradable at the frozen gates).
- **Yield/inflation-LEVEL forms** (V8, NG1): the DGS10 nominal-level control
  killed twice (#14, #15) — it is now program law that every yield/inflation
  lane carries it; it remains "the program's most lethal control".
- **CPI information family** (V9, NG1, NG2, NG3, NG4): print-deviation,
  release-order, revision dynamics, PPP-deviation, EZ vintaged — measured
  exhausted. RECORDED LAW (FOREX-NG3 close): re-entry needs a NEW evidenced
  information source (owner data decision). Revival tricks forbidden:
  lookback/threshold/timeframe/name changes, filter additions, same-data-new-story.
- **Cross-asset shadows that shadow the forex plane**: #16 (RATES-NG1 clock-only
  shadow out-earned the curve anchor — release-calendar geometry repeated);
  #17 (COMMODITIES-NG1: bare CoT release-clock control out-earned every
  positioning arm); crypto V15 positioning-metric family deaths; crypto
  NG1/NG2 exogenous-clock frontier dead.

### What the repo already has (data-plane inventory)

- S2 FRED keyed vintaged classes: DFII10, DFII5, T10YIE, T5YIE, DGS10
  (mandatory control series), CPIAUCSL — CADS pin `07d1e0d5…` (5 files).
- S3 vintaged CPI archives + announcement ledgers: GB `ons_d7bt`, CA
  `canada_allitems` + `statcan_18100004`, AU `abs_640101`, US
  `fred_cpiaucsl_rt`; print calendars GB/CA/AU/NZ/US + EMU v2/CA v3 ledger
  pins. Tail-trim law: vintaged feeds end ~2025-03..2025-06.
- Spot plane: Twelve Data daily bars under the OWNER'S EXISTING entitlement —
  EURUSD pinned at NG4 (5000 bars, probe PASSED) plus the ng1 4-pair grid
  (GBPUSD/USDCAD/AUDUSD/NZDUSD), 1842-day 16:00-NY grid. Keys present in
  gitignored `.env` (names only verified: TWELVE_DATA_API_KEY, EODHD_API_KEY,
  FRED_API_KEY — values never read in this task).
- EODHD entitlement: EOD family-1 only; fundamentals/calendar 403 measured at
  STOCKS-NG3 — irrelevant to FX (no FX fundamentals use proposed).
- New-assets-generation sources (sibling planes, NOT yet on the forex plane):
  CFTC CoT bulk archives (commodities NG1 census staged 2016–2026),
  CBOE VIX family, Treasury.gov daily par yields.
- Denominators at survey time: forex 48/48, program 257/260, 0 survivors (P-9).

---

## 2. Source-class survey (honest; several classes killed AT SURVEY)

| candidate class | survey verdict | why |
|---|---|---|
| OIS / term-SOFR / real-rate differentials (FRED keyed door open) | **KILLED AT SURVEY** | yield-LEVEL lane: DGS10-level control killed #14/#15; V3/V4 carry closed at rho 0.997–1.000; re-parameterization = rescue (Q-3) |
| Trade-balance / current-account release conditioning | **KILLED AT SURVEY** | reaction-direction class closed both economy sides (V7 #12); release-calendar geometry killer (#16/#17); trade data revised-in-place → V9 HIGH vintaged law + NG2/NG3 revision-dynamics closures |
| Sovereign bond auction calendars | **KILLED AT SURVEY** | RATES-NG1 auction lanes already D2-VETOED by momentum/calendar shadows on the sibling plane; #16 class |
| ECB/BIS daily fixings as price panel | **KILLED AT SURVEY** | price-geometry observable = V1/V2 dead class; a new vendor of the same observable class is same-data-new-story |
| Cross-market lead-lag (entitled equity/futures → FX) | **KILLED AT SURVEY** | V7 A6-P2 measured lead content as NEGATIVE information (own-lag control out-earns); class closed on this plane |
| FX-intervention disclosures (Japan MoF etc.) | **KILLED AT SURVEY** | episodic coverage: clustered quarters with zero events — Q-6 recent-window floor dies by construction; timing = news-driven reaction re-clock |
| Retail-sentiment / broker-positioning vendors | **BLOCKED** | needs account + key signup — forbidden by this cycle's boundaries |
| Central-bank statement TEXT timing alone | **subsumed into D2** | timing-only = clock-geometry dead class (#16/#17); text CONTENT is the candidate (D2) |
| **CFTC CoT currency-futures positioning** | **CANDIDATE D1** | positioning observable never measured on the forex plane; free/official; cross-asset #17 shadow is the named kill-candidate (disclosed, not hidden) |
| **Central-bank statement text-content shift** | **CANDIDATE D2** | semantic observable class never measured anywhere in 260 program cells; Fed channel probe-proven; cross-CB channels partially unverified (evidence recorded) |
| **TIC cross-border flow census** | **CANDIDATE D3 (ranked last)** | flow-census observable never measured in program; official/free; mechanism weak under 1.5-month lag — disclosed |

---

## 3. D1 — FX-COT: CFTC currency-futures positioning on TD spot

**Causal hypothesis (who is forced / who is slow).** The weekly CoT census
reports the aggregated book of leveraged funds, hedgers, and the small
nonreporting class per currency futures market. Leveraged futures books face
hard margin constraints: when the noncommercial book is crowded (extreme net
length/short measured against open interest), adverse moves force
de-risking — liquidations that dealers hedge by trading the OTC spot leg,
so the futures crowd becomes the forced trader and spot inherits the flow.
The slow trader is the small nonreporting cohort and the slow-moving
asset-manager cohort (disaggregated/TFF split) whose rebalance horizon is
days-to-weeks; the weekly census timing means between two Tuesdays the crowd
state is fixed while price moves — a measurable state the spot book can be
conditioned on. Mechanism claim is about the STATE of the crowd (crowding
extremes / build-vs-fade regimes), not about reacting to the CoT release
itself — the release-clock shadow exists precisely to separate these.

**Sources (official, documented).**
- CFTC Commitments of Traders main page (cadence, depth, release timing):
  https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm — VERIFIED
  (fetched 2026-09-15): weekly Tuesday-as-of; published Friday 15:30 ET;
  Legacy depth from 1986-01-15; Disaggregated + Traders-in-Financial-Futures
  from 2006-06-13; FAQ 6: "historical data is not updated once published"
  (no revisions); FAQ: holidays can shift the schedule (release-schedule page).
- Bulk archive channel (the measured-live door):
  `https://www.cftc.gov/files/dea/history/deacot{YYYY}.zip` (legacy
  futures-only, one zip per year); disaggregated/TFF equivalents on the same
  /files/dea/history/ tree. This is the exact channel COMMODITIES-NG1's
  audited census consumed 2026-09-12 (census artifact on
  `orca/commodities-ng1-integration`).
- Release schedule page:
  https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm
  (only 13 months listed — a P0 per-cycle re-pin item, not a blocker).

**Access/entitlement status: DOCUMENTED_CANDIDATE.** Data free, keyless,
official. Tradeable legs: TD spot under the owner's EXISTING entitlement
(EURUSD probe-proven at NG4; 4-pair grid pinned at NG1). No new entitlements.
No accounts, no keys touched in this survey.

**Historical depth.** Documented: legacy 1986-01-15→; disaggregated/TFF
2006-06-13→. Measured here: deacot2025.zip HEAD 200 (2.39MB,
last-modified 2026-09-11 — weekly-fresh) + ranged 2KB GET verified zip magic;
deacot2016.zip HEAD 200 (1.71MB). Pre-2016 depth asserted-from-official-doc,
UNMEASURED in this survey (probe budget) — a P0 canary set (one legacy-year
zip + dead/never-existed market-code controls per P-7) is required before any
freeze.

**Availability/publication timing.** Tuesday state → Friday 15:30 ET release
(official text); holiday-shifted weeks follow the official schedule page —
conservative rule: decision clock advances only after the bytes exist (the
V3/V5 evidenced-availability law; P-1: per-event evidence, no asserted bounds).
No revisions after publication (FAQ 6) — the cleanest revision behavior of
any candidate surveyed. Timezone: US ET with standard DST hazards; the
existing 16:00-NY grid absorbs the Friday release same-day.

**Entity + recent-window coverage.** Currency-futures entities with
established report codes: EUR (099741), JPY (097741), CAD (090741), GBP
(096742), CHF (092741), AUD (232741), NZD (112741) + USD-index (098662).
Weekly cadence: ~104 reports per entity in 24 months — sufficient for a
state-conditioned book under the Q-6 recent-window floors IF the design does
not require rare extreme states (a decile-threshold book funds ~10 books per
entity-window; a tail-extreme-only design does not — declared as a design
constraint, not a post-hoc fix).

**Transaction costs.** Existing frozen contract applies unchanged: measured
spot spreads at stress tier, 1.5bps/side × {1.0, 1.5, 2.0} ladder, tier 2.0
PRIMARY (NG1 frozen set; Q-8 measured-never-stated). Rollover/financing: the
V8/V9 dual-book kernel inherits; weekly-state → multi-day holds make
financing realistic and non-optional.

**Falsifiers + ancestry controls.**
- MANDATORY (cross-asset, the named kill-candidate): the bare CoT
  release-clock control — a book that trades the release calendar with NO
  positioning input must NOT out-earn the anchor (#17 fired exactly this way
  on commodities ETP legs). books_distinct must be MEASURED, not assumed
  (P-20).
- MANDATORY (program law): DGS10 nominal-level control on any lane adjacent
  to USD rates exposure (#14/#15 law).
- Price-only shadow: position-state must decorrelate from price-momentum
  form (crowding is not momentum in new words) — measured pooled |rho| ≤ 0.20
  vs the full 25+ shape inventory incl. V4 commodity bloc + V15 elite-level
  forms, on the P-12 committed representation.
- Staleness sham: +1-week / +2-week delayed-state books must NOT reproduce
  the anchor (if they do, it is slow exposure, not information — Q-11
  distinction recorded).
- Q-6 recent-window feasibility floor; invalid-null autocorrelation check on
  the weekly state (Q-11).

**Why it differs from every dead forex family.** Rows 1–29 all consumed
price geometry (1–5, 12, 14), policy-carry (7–9), release-calendar
reaction forms (10, 11, 13, 16–21, 26–29), yield/inflation levels (15, 18–19),
or CPI revision structure (22–25). NONE consumed a positioning census. The
CoT state is a new information source on this plane (owner-data-law satisfied
— the source itself is free/official, so no purchase decision is required;
the decision that IS required from the owner is ratifying cross-asset
ancestry: whether #17's commodities-plane kill extends to a new instrument
plane). Not a revival trick: no dead form is re-parameterized; the observable
class (who holds what, at what crowding) has never been measured on forex.

**Weakest point (self-assessment).** The #17 shadow. The most recent
audited evidence in the program says positioning input added nothing over
release-calendar geometry — on the commodities ETP plane. If the FX CoT
state's entire conditioning information collapses into "trade on Friday
afternoons", D2 kills it exactly as designed and the direction dies at
selection, not at scored cost. Secondary: weekly state × daily grid means
state-staleness is structural; the staleness sham must be run first, and if
a +2-week delayed book reproduces the anchor, the crowd state is just slow
exposure. Tertiary: FX futures open interest is small vs OTC spot — the
futures crowd may be too small to force spot (mechanism-size doubt a critic
should press).

---

## 4. D2 — CB-statement text-content shift on TD spot (semantic observable)

**Causal hypothesis.** G10 policy statements change the expected policy path.
The fastest money reprices within seconds — uncapturable at a daily grid
(Q-1 law: the value lives in the un-executable first bar), so the direction
must be the post-decision DRIFT. The slow money is mandate-constrained:
benchmark-hugging allocators, corporate hedgers executing policy-based
budgets, and consensus-anchored discretionary flow adjust over days; when a
statement's language shifts materially WITHOUT a rate change (no explicit
print to anchor on), the fast repricing is smaller and the underreaction
window longer. The observable is the measured CHANGE in statement language
vs the frozen prior statement of the same bank — a deterministic,
pre-registered featurization (declared before any outcome; no post-hoc
embedding choice), not "sentiment" judged by a model after the fact.

**Sources (official, documented).**
- Fed: https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm —
  VERIFIED (2026-09-15): 8 FOMC decisions/yr in both 2025 and 2026; minutes
  timing documented (+3 weeks).
- Fed statement press releases: stable pattern
  `https://www.federalreserve.gov/newsevents/pressreleases/monetary{YYYYMMDD}a.htm`
  — VERIFIED live for 2025-07-30 (title + body text extracted: "maintain the
  target range for the federal funds rate at 4-1/4 to 4-1/2 percent") and
  for 2016-01-27 (old-date canary). Keyless.
- Statement time-of-day: 14:00 ET convention — ASSERTED, not evidenced here
  (P-1 discipline): per-event P0 evidence table required (exact same standard
  crypto-NG2 applied to BLS instants).
- Other G10 banks (ECB, BoE, BoC, RBA, RBNZ, SNB, BoJ): official press-release
  archives exist publicly, but THIS SURVEY COULD NOT VERIFY them from this
  host: ECB index fetched but monetary-policy anchors not found in retained
  bytes + 2 archive URL guesses 404; BoE page served a bot-challenge
  ("Page not found" title on HTTP 200). Recorded as evidence in
  probes/PROBE_MANIFEST.json. Any cross-CB lane REQUIRES per-CB P0 channel
  verification (declared-UA or controller-channel retrieval, canaries incl.
  an old-date statement) before selection.

**Access/entitlement status: DOCUMENTED_CANDIDATE (Fed channel proven;
cross-CB breadth UNVERIFIED — per-CB P0 evidence required).** Free, keyless,
official. Tradeable legs already entitled (TD spot). No signup anywhere.

**Historical depth.** Fed: 2016 proven by probe; the documented press-release
archive extends earlier (P0 census must evidence the exact back-start).
Statement HTML is stable (not revised in place; corrections rare — P0 spot
checks required).

**Availability/publication timing.** Decision-day intraday (FOMC 14:00 ET
asserted) → same-day visible on the 16:00-NY decision grid; ECB/BoE/etc.
release in their own daytime — all same-day on a daily grid. DST hazards
standard. Statements effectively unrevised (verify at P0).

**Entity + recent-window coverage.** FOMC: 8 decisions/yr → 16 in 24 months
(thin ALONE — the crypto-NG1 8-instant precedent says this is at the floor).
Pooled 8-CB design: ~120–130 decisions/24 months — sufficient pooled, but
pooling imports the day-of-week geometry hazard that killed NG4 (all FOMC =
Wednesdays; all ECB = Thursdays): a mandatory dow-balanced design constraint
and a generic-dow shadow must be in the battery from D1.

**Transaction costs.** Same frozen spot ladder (1.5bps/side × {1.0,1.5,2.0},
tier 2.0 PRIMARY) on TD spot; drift-books are multi-day → financing via the
inherited dual-book kernel.

**Falsifiers + ancestry controls.**
- MANDATORY: decision-day clock-only shadow (Q-7) — a book that trades every
  decision day regardless of text content; text gets credit only for what
  remains above the clock.
- MANDATORY: V7/V6-ancestry falsification control — the book conditioned on
  rate-change SIGN / print-direction alone (the closed reaction-direction
  class); the text-shift book must beat or decorrelate from it at D2
  (measured rho; NG3's CTL-V7NODIFF self-subsumption test is the template).
- MANDATORY: DGS10 nominal-level control (hawkish text ≈ rate-path repricing
  ≈ yield exposure — #14/#15 law).
- Day-of-week generic shadow + dow-balanced book (NG4 killer).
- Sham-statement control: randomized text-shifts preserving the release
  calendar (V5 sham-calendar discipline).
- Q-6: per-CB and pooled recent-window floors frozen BEFORE D1 (the NG2
  census-informed-floor discipline, design-from-census not floor-shopping).

**Why it differs from every dead forex family.** Every one of the 29 dead
rows consumed NUMERIC observables (prices, yields, CPI index levels/prints/
revisions) or calendric structure. No program cell has ever consumed the
CONTENT of policy text as the information variable. It is not a re-clock of
the CPI family (NG3 law): different information source (policy guidance vs
inflation prints), different releasing institution, different observable
class. The risk that it is a re-clock of the REACTION-DIRECTION class (V6/V7)
is exactly what the ancestry battery measures — if rho fires, it dies at D2
pre-score, which is the system working.

**Weakest point (self-assessment).** The lineage risk: a post-decision drift
book IS a reaction-direction book unless the text observable demonstrably
adds content the sign of the decision does not carry. V6 showed
release-direction conditioning carries genuine calendar information but died
on robustness gates (PF razor, concentration, break-even); if the text-shift
book concentrates into the same rate-change events, it will inherit V6's
death certificate at D2. Secondary: featurization degrees of freedom — any
after-the-fact featurizer choice is a rescue; the featurizer must be frozen
before any outcome sight, and the freeze discipline is itself a design risk
(claims of "deterministic" featurization get audited hard). Tertiary: only
the Fed channel is probe-proven; the pooled design dies at P0 if ≥3 CB
channels fail verification from this host.

---

## 5. D3 — TIC cross-border flow census (official, monthly, ranked last)

**Causal hypothesis.** TIC form C/SLT record monthly cross-border net
purchases of long-term US securities, split official vs private. Foreign
official institutions (reserve managers) are the slowest real-money
participant in FX — quasi-government mandates with month-to-quarter horizons
and persistent accumulation waves; sustained official net-buying waves are
the flow counterpart of structural USD demand (or, for private waves, of
yield-seeking carry). The book conditions on the DIRECTION/PERSISTENCE of
the official-vs-private split, published with lag — the claim is that
persistence is months-long, so a 1.5-month-lagged census still carries state.

**Sources (official, documented).**
- TIC system page: https://home.treasury.gov/data/treasury-international-
  capital-tic-system — VERIFIED (2026-09-15): monthly transactions forms
  (B, C, D, SLT), press-release archive, new CSLT dataset (announced
  2026-05-21).
- Release dates page (canonical):
  https://home.treasury.gov/data/treasury-international-capital-tic-system/
  release-dates-of-tic-data/ — VERIFIED with official text: monthly data
  "updated each month on the 11th business day plus 0 to 3 days";
  "Beginning with the release on 3-15-2021, there is a 1.5 month lag between
  the release date and the as-of date". (Two guessed URLs 404'd before the
  canonical was found from the main-page menu — evidence retained.)

**Access/entitlement status: DOCUMENTED_CANDIDATE.** Free, keyless, official.
Tradeable legs already entitled (TD spot). CSV availability for the monthly
forms NOT verified in this survey (main page does not document formats; the
data pages were not crawled per probe budget) — a P0 item.

**Historical depth.** Not stated on the main page (the page only notes
quarterly "Capital Movements" tables pre-2014 in the Treasury Bulletin) —
UNMEASURED here; the documented press-release archive implies years-to-decades
but per-form depth needs a P0 census (fail-closed if shallow).

**Availability/publication timing.** Now EVIDENCED: 11th business day +0–3
days, 1.5-month as-of lag → the observable is ≥1.5 months stale at
availability by construction. No DST hazard (business-day convention);
revisions: TIC data are revised monthly (the release-dates page carries a
REVISIONS section) — a vintaged-retrieval discipline (V9 law) applies if
used.

**Entity + recent-window coverage.** One reporting aggregate (US), split by
instrument/category: monthly cadence → 24 observations in 24 months.
Event-design floors die by construction; only a slowly-updating
characteristic-book design is even admissible, and Q-6 recent-window floors
are marginal at best.

**Transaction costs.** Same frozen spot ladder; monthly state → long holds
→ financing dominates; the dual-book kernel must carry realistic
rollover — the V3/V9 rollover-accounting history says this is a real risk,
not a footnote.

**Falsifiers + ancestry controls.**
- Staleness sham (the primary falsifier): a +60-day / +90-day delayed-state
  book must NOT reproduce the anchor. Given the 1.5-month lag, a delayed book
  reproducing the anchor is the expected outcome — this direction is honest
  about the possibility that its primary falsifier is also its most likely
  verdict.
- DGS10 nominal-level control (private flows are yield-seeking → the book is
  plausibly a disguised yield-level exposure — #14/#15 law).
- Exposure-form shadow + pooled rho vs full inventory; vintaged retrieval
  only (revised-in-place forbidden, V9 HIGH law).

**Why it differs from every dead forex family.** A flow-census observable
(who bought what, cross-border, official-vs-private) has never been measured
in any program family on any plane. Not CPI (NG3 law), not release-calendar
geometry (though it IS release-based, the information claimed is the flow
state, not the calendar), not price geometry, not yield level (controls
enforce this).

**Weakest point (self-assessment).** The mechanism is weak on its face: a
1.5-month-lagged monthly census of what slow money already did is the
definition of stale information; the most likely falsifier outcome is the
staleness sham reproducing the anchor. Coverage (24 monthly observations in
the recent window) is marginal against the Q-6 floors. This direction is
presented for completeness of the survey, ranked last, and a critic should
kill it freely — its survey value is mainly that it bounds the class
("official slow-money flow censuses") so the next survey need not re-derive it.

---

## 6. Ranking and owner-decision items

**Rank: D1 (FX-COT) > D2 (CB statement text) > D3 (TIC).**

D1 ranks first because: (a) its data channel is measured-live from THIS repo's
own audited pipeline lineage (COMMODITIES-NG1 census), not just documented;
(b) its observable class is untouched on the forex plane while its cross-asset
killer (#17) is already identified, named, and cheap to run as a D2 kill;
(c) zero new entitlements — data keyless, legs under the existing TD
entitlement; (d) weekly cadence + no-revision behavior gives the cleanest
availability evidence of the three.

Owner decisions to flag (not assumed by this lane):
1. Whether the cross-asset ancestry (#17 / V15 positioning kills) binds the
   forex plane (registry/ledger policy question — planes have been treated as
   separate ancestry domains so far).
2. Cross-CB P0 verification resources for D2 (per-CB channel checks under a
   disclosed UA policy, as V9 did for SEC).
3. Any new entitlement, if a critic proposes one — this survey requires NONE.

## 7. Survey limitations (disclosed)

- Worktree terminal reports were read from git branches, not from
  `.worktrees/...` paths (cleaned 2026-09-12; the MAP's paths are stale —
  flagged, not fixed: outside this lane's write scope).
- No returns, correlations, or rho values were computed in this survey; every
  kill number quoted is from recorded terminals.
- CFTC Socrata API 403 from this host (both channels); bulk-file channel
  proven instead. ECB/BoE unverified from this host. All recorded in
  probes/PROBE_MANIFEST.json with raw bytes + sha256.
- Pre-2016 CoT depth, FOMC time-of-day, TIC CSV formats, TIC depth, and
  non-Fed CB statement archives are ASSERTED-from-documentation, not probed —
  each is a named P0 evidence item for any future cycle (P-1: no asserted
  bounds ever authorized).
