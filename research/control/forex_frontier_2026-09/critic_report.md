# Critic report — adversarial falsification of FOREX frontier proposals

- task: `fxf-critic-frontier-1`, cycle `FOREX-PRECYCLE-SURVEY` (NOT registered)
- role: CRITIC (independent kill attempt; not the researcher; not a code auditor)
- base SHA: `dfc2ae9c71dbb335d16fec424e8c4cb651c10209` (main; verified HEAD at
  start and at close; no git writes performed)
- date: 2026-09-15. No returns/PnL/rho computed by this critic; every kill
  number quoted is from recorded program authorities, every external claim
  re-verified with the critic's own light fetches (§1).
- target under review: `research/control/forex_frontier_2026-09/
  survey_report.md` + `probes/PROBE_MANIFEST.json` (researcher output,
  fxf-researcher-frontier-1 @ 53d2d152).

---

## 1. Critic-verification log (my own fetches — evidence, not borrowed claims)

All fetches light (HEAD / ranged <=1KB / single-page GET), sequential, keyless,
no accounts, no registrations. Files in /tmp (outside repo; not lane artifacts).

| # | claim checked | my probe | result |
|---|---|---|---|
| V1 | `deacot2025.zip` live + fresh (researcher: HEAD 200, 2,392,119 bytes, last-modified 2026-09-11 19:27:54 GMT) | HEAD + ranged GET bytes 0-1023 from critic host | **MATCH to the second**: HTTP 200, content-length 2,392,119, last-modified Fri, 11 Sep 2026 19:27:54 GMT, accept-ranges: bytes; ranged GET 206, 1024 bytes, starts `PK\x03\x04` (xxd: `504b 0304 1400 0000`). My digest (first 1KB, critic-verification): `ea849ab9913bbf0853f91fda31f31212f4771155bb3b539c771410d2c14baa55` |
| V2 | CFTC release schedule "Friday 15:30 ET, Tuesday as-of, holiday delay 1-2 days" | GET ReleaseSchedule page (48,314 bytes, HTTP 200) | **VERIFIED verbatim**: "released at 3:30 p.m. Eastern time... usually released on Friday... usually includes data from the previous Tuesday... Federal holidays may delay release by one or two days" |
| V3 | CFTC FAQ-6 no-revision claim + depth claims (legacy 1986-01-15; TFF/disaggregated 2006-06-13) | GET CoT index page (84,985 bytes, HTTP 200) | **VERIFIED verbatim**: "6. Corrected Data — Do you perform backdated COT updates...? No, historical data is not updated once published."; "Legacy Report has data available back to January 15, 1986"; "Disaggregated Reports and Trader in Financial Futures... back to June 13, 2006". NOTE: same page advertises a **Special Announcements section** — a corrections class exists alongside FAQ-6; P0 must census it (see G-A3) |
| V4 | Fed 2025-07-30 statement text (researcher: 82,323 bytes; rate-range sentence) | GET monetary20250730a.htm | **MATCH**: HTTP 200, 82,323 bytes served; "maintain the target range for the federal funds rate at 4-1/4 to 4-1/2 percent" present; title matches |
| V5 | TIC timing + revisions (researcher: 11th business day +0-3d; 1.5-month lag since 2021-03-15; REVISIONS section) | GET canonical release-dates page (111,182 bytes, HTTP 200) | **VERIFIED verbatim**: "updated each month on the 11th business day plus 0 to 3 days"; "Beginning with the release on 3-15-2021, there is a 1.5 month lag between the release date and the as-of date"; REVISIONS section present; releases 4 p.m. Washington DC time; "that date will be revised after offices reopen" |

Verdict on probe evidence: all 5 spot-checks reproduce the researcher's claims
exactly (content-length to the byte, timestamps to the second). The 11 local
probe files re-hashed by me: **11/11 digests match PROBE_MANIFEST.json**
(independently recomputed with `shasum -a 256`). The manifest's claimed
statuses (Socrata 403 both channels; bulk door live; Fed channel proven; ECB /
BoE unverified from host) are internally consistent with the retained bytes.
I found **no fabrication and no inflation** in the researcher's access claims.

## 2. Ancestry verification (the researcher's counts and kills)

- **29 forex rows**: recounted programmatically from
  `research/wayfinder/FAMILY_FAILURES.jsonl` (109 total rows): 29 rows with
  forex asset/cycle (F1=1, V1=2, V2=2, V3=2, V4=2, V5=1, V6=2, V7=2, V8=1,
  V9=4, NG1=2, NG3=4, NG4=4). Matches the survey table row-for-row, including
  the per-row kill reasons I spot-read in full (FXFV6 PF razor 1.0979;
  FXFV7-A4-P1 sham #12; FXFV8 DGS10 4.01x #14; FXNG3-A5-P1 CTL-V7NODIFF rho
  1.0; FXNG4-A4-P1 rho 0.8883 vs generic_dow_tue with 33/37 Fridays).
- **#16 / #17**: read in full. #16 = RATESNG1-A5-P1-ARM-AGGRESSIVE
  (CONTROL_OUT_EARNS_CLOCK_RE_CLOCK: clock-only shadow +94.16 vs +72.42);
  #17 = COMMNG1-A4-P2 NEUTRAL/TAILWIDE/WINDOWSHORT
  (CONTROL_OUT_EARNS_RELEASE_CLOCK: bare CoT release-clock control out-earned
  every positioning arm; all three arms negative after costs). Both closed
  2026-09-14, one day before this survey. The survey describes them
  accurately, including their plane scope ("measured-closed **on this
  substrate**").
- **Denominators**: ledger re-stamps confirm forex 48/48, program 257/260
  published/observed, 0 survivors (P-9) — matches the survey.
- **Closed-class law**: FOREX-NG3 row: CPI-information family on the pinned
  plane measured-exhausted; re-entry needs a NEW evidenced information source.
  NG2's frozen floor precedent: AU revision census 26 < 30 usable events → P0
  census kill. V9 HIGH law: current-vintage revised-in-place tables forbidden
  on this plane — vintaged channel mandatory.

## 3. Adjudication of the flagged open question: do #17/V15 legally bind the forex plane?

**Verdict: NO as a measured ancestry veto; YES as a mandatory declared
falsifier.** Reasoning, not vibe:

1. **Program law is measurement-keyed, not resemblance-keyed.** Every
   ANCESTRY_RHO_BLOCK in the ledger fires on a measured |rho| against a named
   dead shadow measured ON THE SAME PLANE on the declared representation
   (P-12): FXNG4 vs same-plane generic dow (0.8883); CNG1/CNG2 vs same-plane
   dead FOMC/vol forms; FXNG3 vs same-plane release-order. No family in 109
   rows was ever killed by transitive import of a foreign plane's closure.
2. **Direct precedent on point.** COMMODITIES-NG1 proposed CoT positioning
   *after* CRYPTO-V15's positioning-metric deaths (ELITE-SIZE-ASYM
   control-out-earn #11, TAKER-SAT plain negative) and was allowed to reach
   its own measured D2/E kill. The program's practice is: cross-plane deaths
   inform the battery (P-24: "the localization transfers" — the *falsifier*
   transfers), never auto-kill.
3. **Scope of the closures.** #17's own measured_summary scopes it: "crowd-carry
   positioning frontier measured-closed **on this substrate**" (commodity ETP
   legs). #16 is auction-release geometry on rates ETPs. Neither names the
   forex plane. The ledger's rescue definition ("re-testing it, or any
   parameter/top-K/universe/relaxed-gate variant of it") is keyed to the
   rejected family; D1 is not a variant of COMMNG1-A4-P2 (different legs,
   universe, plane).
4. **What DOES bind, contractually.** P-24's consequence: "Every D1 battery
   declares its killers before measurement." The #17 mechanism (bare release
   clock beats positioning input) is the *declared-killer template* D1 must
   carry — and the owner should ratify exactly this status in the plan's
   ancestry section: **#17 transfers to FOREX-NG5 as a mandatory control
   template, NOT as a measured veto.** Bayesian honesty: with three
   positioning-flavored families dead program-wide (V15 x2, COMMNG1 x3 arms),
   the modal outcome for D1 is a measured replication of #17 at D2/E. That is
   a prior to price the cycle's budget against, not a legal bar.

The researcher's treatment (disclose the shadow, mandatory control, owner
decision flagged) is correct. I would have failed them if they had claimed #17
auto-killed or auto-cleared D1; they claimed neither.

## 4. D1 — FX-COT: attacked on all ten axes

1. **Snooping / multiple-testing (260 cells, 0 survivors).** Moderate.
   Constructs are numeric and low-DOF (crowding z, build-vs-fade); the program
   deflation machinery (DSR/PBO, frozen gates, novelty bars) applies.
   Residual channel the survey does not name: CoT crowding strategies have a
   large *published* literature — researcher knowledge of published
   CoT-backtest results is itself a selection pressure. Mitigated by the
   falsifier battery, not eliminable. Not a kill.
2. **Retrospective labels.** None: crowding states are computed from the
   point-in-time weekly census; no hindsight-constructed observable. The
   availability discipline (per-release bytes-exist evidence, P-1) is
   correctly declared.
3. **Revision behavior of the source.** Verified by me (V1/V3): FAQ-6 "no,
   historical data is not updated once published" — the cleanest revision
   behavior of any source this program has surveyed. Caveat found by me: the
   Special Announcements corrections class exists on the same page → P0 census
   (G-A3). Not a kill.
4. **Release-clock leakage (the NG4 kill, rho 0.89).** STRUCTURAL AND SEVERE —
   this is D1's modal death. CoT books enter at/after the Friday 15:30 ET
   release on the 16:00-NY grid: the book's calendar signature is
   Friday-clustered (holiday-delayed weeks push to Mon/Tue) — the *exact*
   geometry class that killed NG4 (33/37 Fridays, rho 0.8883 vs
   generic_dow_tue). AND the #17 kill says on the same source's calendar the
   clock control out-earned positioning input outright. The survey's battery
   has the #17 clock control but lists **generic day-of-week only implicitly**
   (inside the "25+ shape inventory"). This must be an explicitly named
   mandatory veto (G-D2-1b). Kill-class exposure, not a survey kill — the D2
   gate is designed to fire exactly here, cheaply, pre-score.
5. **Timezone/DST.** Benign: release and grid are both ET; DST transitions
   co-move; holiday-shifted weeks need per-event evidence (P-1, declared).
6. **Q-6 recent-window population.** Adequate with the declared design
   constraint: weekly cadence ~104/entity/24mo funds decile-state books;
   tail-extreme-only designs die and the researcher correctly pins that as a
   design constraint, not a post-hoc fix.
7. **Proxy contamination — the real attack, and the survey's battery is
   incomplete here.** Net noncommercial currency-futures positioning is a
   documented co-mover of interest-rate differentials (leveraged length
   follows carry). Carry is a CLOSED family on this plane twice over (V3
   invalidated at PF 1.2825 measured; V4 front door re-entry rho 0.997–1.000;
   FXFV8-A4-P2 already D2-vetoed at 0.3831 vs a carry_unconditional shadow).
   The survey's mandatory controls list DGS10 *LEVEL* (program law #14/#15) —
   but a LEVEL control does NOT catch a *differential* form. A
   **policy-rate-differential direction shadow is mandatory and missing as an
   explicit named veto** (G-D2-1c; the FXFV8-A4-P2 veto is the template).
   Additionally the mechanism-size doubt the researcher flags as tertiary is
   in my view primary for the *causal story*: CME currency-futures OI is
   roughly 2–3 orders of magnitude below OTC G10 spot turnover — the futures
   crowd cannot *force* spot; the honest claim is state-conditioning, and the
   plan must contain no forcing language (G-Scope-2).
8. **Carry/roll/financing realism.** Weekly state → multi-day holds →
   rollover/financing is first-order, not a footnote (V3 rollover history).
   Inherited dual-book kernel plus a **P-21 preregistered financing-inclusive
   cost ceiling measured at P2** are required (G-E-1). Existing spot ladder
   (1.5bps/side x {1.0,1.5,2.0}, tier 2.0 PRIMARY) carries unchanged.
9. **Dead-ancestor collision.** None of the 29 rows consumed a positioning
   census; D1 is not a relabel, lookback change, or re-parameterization of any
   forex family. Nearest ancestors are cross-plane (#17 same source+calendar;
   V15 positioning metrics) — adjudicated in §3: mandatory controls, not
   vetoes. The NG3 "new evidenced information source" law is satisfied (free/
   official source, new to this plane).
10. **History/depth for 3 folds.** Verified from the source (V3): legacy
    1986-01-15→, disaggregated/TFF 2006-06-13→; bulk zips for old and recent
    years live (mine + theirs). 5000-bar TD EURUSD (~20y) covers the
    disaggregated era. Open item: **per-year market-code continuity** — legacy
    market codes are not guaranteed stable across decades (a currency can
    appear under more than one code across eras); a per-year code census with
    dead/never-existed code controls (P-7) is a P0 gate (G-A1). One unverified
    researcher assertion remains: "COMMODITIES-NG1 census staged 2016–2026" —
    plausible (consistent with the ledger row and the 2016 HEAD canary) but
    the branch census is outside my read scope; non-load-bearing.

**D1 VERDICT: PASS_SOURCE_GATE + PASS_MATERIALLY_NEW** — with the gate set in
§7 pinned into any plan. Honest expectation: modal terminal is a D2/E kill by
the clock, dow, or carry shadow; the direction merits a plan precisely because
that kill is cheap, pre-declared, and pre-score.

## 5. D2 — CB statement text-content: attacked on all ten axes

1. **Snooping/multiple-testing.** SEVERE — the direction's deepest problem.
   Any text featurization has large degrees of freedom (vocabulary, weighting,
   thresholds, contrast definition) against a pooled ~120-130 decisions/24mo
   event budget; and the researchers have seen public FX outcomes — statement
   language episodes (forward-guidance eras, "patient", "transitory",
   dot-plot language) are public knowledge, so a "pre-registered" featurizer
   written today can encode hindsight the program's cell accounting never
   sees. The program has no precedent for freezing a *text* featurizer
   outcome-blind; any plan must require a parameter-free, auditable,
   mechanical featurizer frozen before any outcome sight (G-D2-Featurizer).
   Not survivable as proposed ("deterministic featurization" is asserted, not
   specified).
2. **Retrospective labels.** Statement bytes are point-in-time (fine), but the
   observable construction is retrospective until (1) is solved.
3. **Revision behavior.** Statements effectively unrevised — low risk; P0 spot
   checks declared. Not a kill axis.
4. **Release-clock leakage (NG4 kill).** Worst-case geometry: FOMC = 100%
   Wednesdays, ECB/BoE = Thursdays — pooling builds a book whose day-of-week
   signature is deterministic-by-institution, the extreme of the NG4
   33/37-Fridays class (rho 0.8883 kill). The declared dow-balanced constraint
   + generic-dow shadow is the right medicine, but note the cost: dow-balancing
   pushes toward a constant-presence book, i.e., the clock control absorbs
   most of the tradeable surface. Structural squeeze.
5. **Timezone/DST.** Cross-CB instants (ECB 14:15 CET, BoJ inside/outside the
   NY day) need per-event PIT instants; declared as P0. Standard.
6. **Q-6 recent-window population — the decisive gate, and it fails today.**
   Two forms: (a) Fed-only: 8 decisions/yr → 16/24mo, ~5-6 per fold. The
   on-plane precedent floor is FOREX-NG2's own frozen census floor (AU 26 < 30
   usable events → P0 census kill). 16 < 30: dies Q-6 by the program's own
   bar. (b) Pooled 8-CB (~120-130/24mo): passes Q-6 but **requires channels
   that are UNVERIFIED FROM THIS HOST** — the researcher's own probes: ECB
   index served but no monetary-policy anchors in retained bytes + 2 archive
   guesses 404; BoE served a bot-challenge "Page not found" title on HTTP 200;
   6 of 8 banks unattempted. The only population-adequate design has no
   evidenced source gate today.
7. **Proxy contamination — the pincer.** Condition on ALL decisions → the book
   rhos with the decision-sign book (the closed V6/V7 reaction-direction
   class; V7 #12 closed it on BOTH economy sides; FXNG3-A5-P1's CTL-V7NODIFF
   rho 1.0 is the closure template). Condition on no-change statements only
   (where text is the only information) → the population collapses under the
   floors of (6). Escape requires text-shift to be demonstrably orthogonal to
   decision-sign on a pooled population that barely clears the floors with all
   banks included. No demonstrated escape exists at survey.
8. **Costs.** Same ladder; drift books multi-day → financing inherited. Not
   the kill axis.
9. **Dead-ancestor collision.** Materially new observable class (no program
   cell ever consumed policy-text content) — but the closest ancestor (V6/V7
   reaction-direction) is the pincer in (7). Not a relabel; the ancestry risk
   is real and measured at D2 by design.
10. **History/depth.** Fed 2016 probe-proven (verified by me, V4, plus their
    old-date canary); cross-CB depth unverified; FOMC 14:00 ET asserted
    (correctly flagged P-1).

**D2 VERDICT: FAIL.** Kill named: **source gate insufficient for the only
population-adequate design** (cross-CB channels unverified/blocked from this
host) **and the Fed-only form dies Q-6** (16 < the program's own 30-event
census floor, FOREX-NG2 precedent) **with an ancestry-population pincer**
(V6/V7 reaction-direction vs no-change-subset collapse) **and an
unbounded-featurizer snooping exposure** the program has no machinery to
audit yet. Conditional revival path (owner authority, a future survey): per-CB
P0 channel verification (declared-UA/controller channel, old-date canaries)
passing for >=5 CBs; a frozen parameter-free featurizer specified at plan
level; the no-change-subset population shown >= floors pooled. Until then: no
plan.

## 6. D3 — TIC flow census: attacked on all ten axes

1. Snooping: modest; moot given the rest. 2. Retrospective labels: mechanical,
   fine. 3. **Revision behavior — the kill**: TIC monthly data are revised
   (verified by me, V5: REVISIONS section; revised-after-reopen text). The V9
   HIGH law on this plane forbids current-vintage revised-in-place
   consumption; a vintaged channel is mandatory — and **no PIT-vintage archive
   for TIC is evidenced anywhere** (FRED/ALFRED carry no TIC vintages; the
   survey does not even claim one). Plausibly impossible → dies at P0 under
   the plane's own law. 4. Release-clock: 11th business day business-day
   clock; weak dow signature; not the killer. 5. Timezone: benign. 6. **Q-6:
   24 monthly observations/24mo** — event designs die by construction;
   characteristic-book only; marginal even then. 7. **Proxy contamination**:
   private flows are yield-seeking → a carry proxy (closed V3/V4 family); a
   1.5-month-lagged monthly state is the definition of stale — the survey's
   own primary falsifier (staleness sham) is its most likely verdict, as the
   researcher honestly concedes. 8. Costs: monthly → long holds → financing
   dominates (V3 rollover history). 9. Dead-ancestor collision: carry family
   via the private-flow leg; no forex family consumed flow censuses — new in
   class, dead in expectation. 10. History/depth: per-form depth and CSV
   formats unverified (disclosed).

**D3 VERDICT: FAIL.** Kill named: **revised-in-place data with no evidenced
PIT-vintage channel (V9 HIGH law) + staleness sham as the modal verdict by
construction (1.5-month lag, verified from the source) + Q-6 marginality.**
The researcher ranked it last and invited the kill; concur. Q-10 reopening
condition to record at close: a PIT-vintaged TIC channel evidenced + a
demonstrated staleness escape would reopen the class ("official slow-money
flow censuses at TIC cadence") for the next survey.

## 7. Overall recommendation and the P0 gates the plan must pin

**Open FOREX-NG5 with D1 (FX-COT) only.** D2 and D3 fail at survey; record
their closures with the reopening conditions above so the next blind-proposal
packet is forbidden by condition (Q-10).

Mandatory gates to pin in the plan (the plan will be written from this list):

- **G-A1 (P0 census canaries).** One pre-2016 legacy-year zip full pull; per-year
  market-code validation table for all 7 currency futures + USD-index across
  the used span (codes are not guaranteed stable across eras); dead/
  never-existed market-code controls per P-7.
- **G-A2 (availability evidence, P-1).** Per-release bytes-exist table incl.
  holiday-delayed weeks (release can slip 1-2 days — verified from the source).
  Socrata door is 403 from this host (verified twice by the researcher);
  bulk channel is the only door; the release-schedule page is a rolling
  ~13-month window → per-cycle re-pin item.
- **G-A3 (corrections census).** CFTC Special Announcements class censused and
  classified alongside the FAQ-6 no-revision claim (which I verified verbatim).
- **G-D2-1 (named mandatory vetoes, all measured on the frozen 16:00-NY
  representation — P-12; V9's 0.3034-vs-0.1062 recompute is the proof case):**
  (a) bare CoT release-clock book, same grid/hold/cost geometry — kill if it
  out-earns the anchor or books_distinct is unmeasurable (P-20 fail-closed
  None); (b) **generic day-of-week shadow as an explicit named veto** — the
  CoT calendar is Friday-clustered by construction and NG4's rho 0.8883 class
  is the exact killer (survey battery has this only implicitly — now explicit);
  (c) **policy-rate-differential direction shadow** — the survey battery's
  gap; DGS10-LEVEL does not cover the differential form; FXFV8-A4-P2's
  carry_unconditional veto (0.3831) is the template; (d) DGS10 nominal-LEVEL
  control (#14/#15 program law); (e) price-only momentum shadow pool,
  pooled |rho| <= 0.20 vs the full same-plane shape inventory.
- **G-D2-2 (staleness sham).** +1w/+2w delayed-state books must NOT reproduce
  the anchor; Q-11 INVALID-NULL distinction explicit in the verdict.
- **G-D2-3 (floors before D1).** Q-6 recent-window floors frozen from a census,
  design-constrained to decile-state books (no tail-extreme-only designs).
- **G-E-1 (cost ceiling, P-21).** Financing-inclusive worst-case round-trip
  ceiling measured at P2, preregistered; weekly holds make rollover first-order.
- **G-Scope-1 (budget ordering).** No scored cell before every G-D2-1 veto has
  run; the plan's ancestry section records the owner ruling that #17/V15
  transfer as mandatory control templates, not measured vetoes (§3).
- **G-Scope-2 (mechanism honesty).** Record the futures-vs-OTC size asymmetry;
  the claim is state-conditioning; no "forced liquidation of spot" causal
  language in the plan.

Scope discipline: budget exposure after the D2 battery (the commodities
3/6-cell pattern is the right shape); the expected terminal is a measured
replication of the #17/#16 class — acceptable under Q-16/P-19 economics only
because the kill executes pre-score at near-zero scored cost.

## 8. Biggest residual risk

**Scope-creep into scored budget before the vetoes fire.** D1's modal outcome
is death by its own pre-declared controls (clock, dow, or carry shadow — three
independent mechanisms all point the same way, and #17 fired exactly this way
one day before this survey). If the plan lets any scored cell run before
G-D2-1(a)-(e) complete, the program pays full scored cost to re-learn a
one-day-old lesson. The single most protective sentence the Lead can write
into the plan: "No E-stage cell is funded unless the five G-D2-1 vetoes have
all run measured and the anchor survives all five."

## 9. Critic limitations

- I verified researcher claims (5 independent fetches, 11/11 local digests,
  ancestry counts, ledger/lesson rows, NG-plan gate text) but did not re-read
  the integration-branch terminal reports (root checkout lacks .worktrees per
  the 2026-09-12 cleanup; the ledger + FAMILY_FAILURES rows I read directly
  are the P-9 authority).
- "COMMODITIES-NG1 census staged 2016–2026" and the CoT market-code list are
  researcher assertions I did not independently verify (branch census out of
  scope) — both are folded into G-A1 as P0 evidence requirements.
- No rho/returns were computed by this critic; the D1 carry-proxy contamination
  argument rests on program kill evidence (V3/V4/FXFV8-A4-P2) plus documented
  market structure, and will be settled by the G-D2-1(c) measurement, as it
  should be.
