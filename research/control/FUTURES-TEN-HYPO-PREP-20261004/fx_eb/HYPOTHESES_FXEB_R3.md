# HYPOTHESES_FXEB_R3 — round-3 outcome-blind hypothesis search, 6E / 6B (lane FXEB)

- Task: **FUTURES-TEN-HYPO-PREP-20261004**, lane **FXEB** (symbols 6E, 6B).
  Generated 2026-10-04 UTC. Worktree
  `/Users/hoangminhlong/my-quantitative/.worktrees/futures-ten-hypo/prep` @
  HEAD **`a4a882658e09092b5b282b666b30a3cfc5ac3418`** (measured via the one
  permitted `git -C <worktree> rev-parse HEAD`; == dispatch base_sha), branch
  `prep/futures-ten-hypo-20261004`.
- Class: PREP hypothesis dossier. **0 PnL, 0 returns, 0 scored runs, 0 sweeps,
  0 selection by any return statistic, 0 conditional-on-signal measurements.**
  Every parameter **[PROVISIONAL]**. Missing evidence is **NOT_RUN**, never
  PASS. No registration, no trial creation; NO_GO_REGISTER / NO_GO_SCORE /
  NO_GO_ORDER restated. **PB2 HOLD restated, never reopened.** The P3
  quarantine worktree (`.worktrees/futures-behavior/prep` @ b583c33a) was
  NEVER accessed.
- Search verdict up front: **0 NEW families** (target ≤3; an honest zero —
  the dead London-window corpus made this the hardest court in the program,
  and every generated candidate hit a specific, cited wall). **12 candidates
  adjudicated: 1 CONSTRUCTION-ONLY, 7 DUPLICATE-VETO, 2 DATA-BLOCKED,
  2 NOT_NEW/subsumed.** Carried register (FX-F1..F6, RMM 6E/6B legs):
  unchanged, see `CARRIED_STATUS.md`.
- Taxonomy: **FACT** (primary source + date + capture + sha256) /
  **OBSERVED** (script + window on committed artifacts, cited `file:field`) /
  **MECHANISM_HYPOTHESIS** / **INFERENCE** / **DERIVED** (arithmetic from
  named measured inputs) / **NOT_RUN** / **NOT_OBTAINED** /
  **BLOCKED_TRANSPORT**. Forbidden words: "measured cost", "complete cost",
  any "edge" claim.

---

## 0. Evidence base consumed before writing (read-only)

1. Baseline hypo: `FUTURES-OVERNIGHT-PREP-20261003/hypo/6e_6b/
   FX_HYPOTHESES.md` (662 lines, FX-F1..F6 + §7 cost table + §8 census 648)
   and `hypo/cross/RANKING_FRAMEWORK.md` (the 5-dim D1–D5 0-3 anchors,
   aggregation + tie-break law).
2. Court: `FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/deep/6e_6b/
   PB2_ANCESTRY_COURT_DRAFT.md` in full (§a dead-corpus anatomy; §b three-part
   distinguishability test every NEW candidate must pass; §c placebo/power
   court; §d dependency list).
3. R2 exemplar: `FUTURES-SIX-ADOPT-PREP-20261004/hypo/HYPOTHESES_R2.md`
   (RMM = the quality bar; W1/W2/W3 wall taxonomy) +
   `packet/CYCLE_LAUNCH_DRAFT.md` §1–§3, §5, §8 (chains of record, cost
   contract, controls, D1–D12).
4. Readiness: `FUTURES-SIX-READINESS-20261004/fx_eb/DATA_READINESS_6E.md`
   (expiries 66/68; holiday 34/42; roll 27 switches, lead 13–19d) and
   `DATA_READINESS_6B.md` (expiries 62/68; **holiday grid 0/42
   NOT_OBTAINED**; roll lead 17d).
5. Dead inventory: `research/wayfinder/FAMILY_FAILURES.jsonl` — **all 173
   rows scanned**; the 41 forex rows enumerated individually (per-arm books,
   kill codes, reopening conditions). Load-bearing dead rows for this lane:
   FXFV1-A3-P1/P2, FXFV2-A4-P1/P2, FXFV3-A6-P1-family2, FXFV4-A6-P1,
   FXFV5-A6-P1, FXFV6-A6-P1/P2, FXFV7-A4-P1/A6-P2, FXFV8-A5-P1, FXFV9-A4/A5,
   FXNG1-A4-P2/A5-P1, FXNG3-*, FXNG4-*, FXOS-04, TRACKA1-M1/M2/M3,
   TRACKA2-P3A/P3B/P4A/P4B/C1C2C3, DTPFX1-A1-MEFIX-VARIANT, DEV1-DS03/DS05,
   PC12A-DIAGLEG.
6. Committed analysis JSONs (cited `file:field`, nothing recomputed):
   `FUTURES-DEEPRESEARCH-V2-20261003/analysis/6E_a2_sessions.json`,
   `6B_a2_sessions.json`, `6E_a4_events.json`, `6B_a4_events.json`,
   `6B_a6_gilts.json`, `6E_a1_regimes.json` (dispersion inputs for all MDE
   arithmetic), `FUTURES-SIX-READINESS-20261004/fx_eb/
   cost_roll_events/cost_roll_events_fxeb.json`.
7. Root read-only: `research/control/FUTURES-DATA-10SYMS-V1/FINAL_REPORT.md`
   (6E/6B spread proxy 3 ticks = $18.75; IBKR true-volume era ~14 months on
   the 10SYMS capture set) — cited "root main d8cf8eca".

New source research this lane (logged, `fetch_log.jsonl`, 5 URL attempts +
2 searches; ≤2 per (url,method); ≤30 total): 4 raw captures saved with
sha256 (`SHA256SUMS_lane.txt`):

- `captures/cme_specs_6E_archive20210301.html`
  (`9f1c2ec96b8aa95cc85342a1fe11f023b1914dbcc0b3ed772e764858ec6e72af`) —
  archived CME Euro FX spec page (web.archive.org replay of
  cmegroup.com, BLOCKED_HTTP_403 live): **125,000 Euro**; min fluctuation
  **0.00005 = $6.25**; Settlement Method **Deliverable**; trading terminates
  **9:16 a.m. CT on the second business day prior to the third Wednesday** of
  the contract month; page contains **NO fixing-anchor language** (settlement
  detail delegated to a separate "EUR/USD Futures Settlement Procedures"
  page).
- `captures/cme_specs_6B_archive20210301.html`
  (`108381e036da0a1dd869de28261a7dfca6e2d50c931a14fdda74c7abbe306074`) —
  archived CME British Pound spec page: **62,500 British pounds**; min
  fluctuation **0.0001 USD per GBP = $6.25**; **Deliverable**; terminates 9:16
  a.m. CT 2nd business day pre 3rd Wednesday; NO fixing-anchor language on
  the page; links "GBP/USD Futures Settlement Procedures" and "Deliverable
  Futures - Final Settlement".
- `captures/ecb_accounts_20261004.html`
  (`e3992d3112f1527fc452e96b76c4cd1cb86bdc92b837d37c3d57233cabc00d7c`) —
  live ecb.europa.eu accounts page: "The accounts are typically published
  four weeks after the meetings"; **no time-of-day convention stated**; next
  release 2026-10-08.
- `captures/ons_releasecalendar_20261004.html`
  (`2fb374a577a9bb1309dea204b55871d6f95b981726d00f2400184bc924897498`) —
  live ons.gov.uk release calendar: visible listings stamped **9:30am**; **no
  policy time-of-day sentence**; no CPI entry visible on the fetched page.

The WM/Reuters 4pm-London settlement-anchor question (dispatch design space)
could NOT be closed at primary-source level: the specs pages delegate to
settlement-procedures documents not reachable this lane; web-search results
are SECONDARY summaries only and the specific CME advisory was not located ⇒
the fixing-anchor detail is recorded **NOT_CAPTURED_PRIMARY
(BLOCKED_TRANSPORT for cmegroup.com live)**. Nothing below depends on it.

---

## 1. Search result and closure

**0 NEW families are proposed.** The gap between 0 and the ≤3 cap is
deliberate and evidenced. The two design spaces the dispatch flagged as
"may live" were adjudicated first and both failed the court §b test:

1. **WM/Reuters fixing-window flow on 6E/6B — DUPLICATE-VETO (C-01)**. The
   dead corpus already REPRESENTED this mechanism class and killed it twice:
   `TRACKA2-P4A-FIXCERT-01` (forex, SELECTION_REJECTION,
   DECLARED_BAND_BELOW_MEASURED_COST — "Fix-window geometry is real but the
   harvestable band after taker costs is negative on the Dukascopy paper
   book") with a **binding reopening condition**: "owner amendment with a NEW
   economic basis (cheaper measured execution or larger evidenced premium);
   parameter re-tunes are barred"; and `DTPFX1-A1-MEFIX-VARIANT` (forex,
   SELECTION_REJECTION, VARIANT_SAME_FAMILY — month-end WMR rebalancing is a
   calendar re-gate of the same decision law; "0/3 anti-variant identity axes
   move (payer, information layer, risk shape) vs the required >=2"; owner
   law 2026-09-26: "adding an observable is not a new mechanism"). The
   reopening condition is **unmet on both prongs**: (i) *cheaper measured
   execution* — the futures vehicle is NOT cheaper per notional (court §b4 /
   FX_HYPOTHESES §7: 6E modeled RT 3.6–6.3 bp ≥ dead 3.0 bp proxy; 6B
   6.3–11.2 bp; and ours is only MODELED — no measured execution evidence
   exists, BBO NOT_RUN); (ii) *larger evidenced premium* — no premium-size
   evidence on any venue this program holds, and the dead cycle's banked
   fix-window spread census (fix-window p50 = mid-month ±0.1 pip) already
   removed the "fix-window microstructure premium" story. A 6E/6B leg is a
   venue re-parameterization of a closed class — barred without owner
   amendment. The **settlement-anchor fact itself** is separately classified
   CONSTRUCTION-ONLY (C-02).
2. **ECB/BoE speaker-minutes differentiation — NOT_NEW/DUPLICATE-VETO
   (C-06, C-07)**. BoE minutes have no separate day-set since the Aug-2015
   restructure (minutes publish WITH the decision — inside FX-F2's MPC
   day-set). ECB accounts are a separate day-set but: n≈55 events over the
   panel ⇒ court-method MDE ≈ **17.5 bp** (6E) vs modeled RT 3.6–6.3 bp (the
   same power starvation the court called unrecoverable for FX-F2-6E); **zero
   measured anatomy** in any committed artifact (no accounts-day volume
   spike is measured anywhere in `6E_a4_events.json`); publication
   time-of-day NOT evidenced (capture above); and the mechanism predicts its
   own null (the accounts follow full price discovery of the decision by
   four weeks). Remaining candidates (own-economy UK/euro-area releases,
   gilt auctions, lead-lag, round-levels, options-expiry hedging,
   gilt-stress overlay, month-end rebalancing) each died on one of three
   walls, mirrors of R2's W1/W2/W3:
   - **W1′ ancestry/owner-law veto** — the dead FX corpus (V5–V9, NG1–NG4,
     TRACKA2/DTPFX) already represents release-event, fix-window, lead-lag
     and range-adjacent classes; venue/minute/venue-resolution changes are
     re-clocks, not new mechanisms (owner law 2026-09-26; Q-3 umbrella).
   - **W2′ standing law** — roll/curve/carry/settlement = construction or
     structural overlays (DC §1.3 + H-G law); calendar mechanisms require
     the sham-calendar control as a house standard (FXFV5 lesson).
   - **W3′ power/cost honesty** — at every defensible event count in the
     remaining unoccupied day-sets (n ≈ 55–340), the court-method MDE
     (12.97×√(100/n) bp 6E / 15.38×√(100/n) bp 6B) sits at or above the full
     modeled RT cost (3.6–6.3 / 6.3–11.2 bp); the dead own-economy release
     class's measured break-even (3.475 bp, FXFV6) is 1.8–3.2× BELOW the 6B
     cost floor — the cost wall tightens, not loosens, on futures.

---

## 2. Candidate adjudications (every candidate, its wall)

### C-01 `FIX-FLOW` — London fixing-window flow on 6E/6B — **DUPLICATE-VETO**

Dispatch design space #1, adjudicated first. Mechanism as postulated
[MECHANISM_HYPOTHESIS, never measured here]: WM/Reuters 4pm-London rebalancing
flow pressures the underlying spot into the fix; the futures book inherits the
intraday signature via arb; tradable claim = drift into / reversal after the
fix window.

Wall (specific):
- Dead rows: `TRACKA2-P4A-FIXCERT-01` (SELECTION_REJECTION,
  DECLARED_BAND_BELOW_MEASURED_COST, RC binding) + `DTPFX1-A1-MEFIX-VARIANT`
  (SELECTION_REJECTION, VARIANT_SAME_FAMILY, month-end re-gate; banked
  fix-window spread census: p50 = mid-month ±0.1 pip; "the fix-family barrier
  is premium-evidence + venue, not the spread bucket").
- Court §b test FAILS: the dead spot corpus CAN represent this mechanism
  class (it was F-0 class-passed there — "fix-participant payer distinct" —
  and killed on cost, not concept). A futures leg changes venue+cost base
  only = the parameter re-tune class the RC bars.
- RC prong (i) unmet: court §b4 arithmetic — 6E modeled RT 3.6–6.3 bp and 6B
  6.3–11.2 bp are NOT below the dead 3.0 bp proxy (and "measured execution"
  evidence does not exist on our side: BBO NOT_RUN, fees VERIFIED_VS_ACCOUNT
  NOT_RUN).
- Settlement-mechanics adjacency: any claim that trades "because CME settles
  to the fix" is construction, not alpha (C-02 below).

### C-02 `SETTLE-ANCHOR` — CME FX final settlement fixing anchor — **CONSTRUCTION-ONLY**

Captured facts [FACT, sha256-pinned]: 6E/6B are **deliverable** contracts
terminating 9:16 a.m. CT on the second business day prior to the third
Wednesday; settlement procedures are separate exchange documents
(captures above). The final-settlement fixing convention (WM/Reuters 4pm
London class) is SECONDARY-sourced only this lane — NOT_CAPTURED_PRIMARY,
BLOCKED_TRANSPORT. Classification: settlement/termination mechanics are
**construction rules** under DC §1.3 (the same law that holds roll timing and
the session clock as construction, never alpha). Any settlement-week
calendar effect is a construction-constrained trading-day fact (adjusted by
the roll law already in the chains), not a hypothesis family; a tradable
"settlement-window" claim collapses into C-01's vetoed class. 0 identities.

### C-03 `ME-QE-REBAL` — month-end / quarter-end IMM rebalancing flow — **DUPLICATE-VETO**

Same payer as C-01 (benchmark/rebalancing flow into a fix window); the dead
corpus's month-end variant `DTPFX1-A1-MEFIX-VARIANT` was killed as a calendar
re-gate of the fix-certainty class (skeleton test). Quarter-end IMM is the
same re-gate one clock further out, and the IMM roll calendar itself is
construction (DC §1.3). Sham-calendar control (FXFV5 house standard) would
additionally own the calendar-geometry null. **VOID.**

### C-04 `UK-REL` — UK-morning own-economy releases on 6B (07:00-London class) — **DUPLICATE-VETO** (with DATA-BLOCKED component)

Dispatch design space #3 ("occupied by FX-F3? check"): checked — FX-F3's
day-set and anchor are US-8:30 ET only; UK releases are genuinely outside its
day-set, and the 07:00-London minute is outside FX-F1's 08:00–11:00 range
window. The candidate still dies, on the dead corpus's own-economy release
class plus power/cost honesty:

- Dead rows: `FXFV6-A6-P1` own-economy CPI reaction-direction drift —
  SCIENTIFIC_REJECTION on robustness (PF 1.0979 vs 1.10 razor;
  BREAK_EVEN_BPS_OVER_FLOOR **3.475 bp vs 1.5 bp floor**; pair concentration
  GBPUSD 0.4257) with the measured counter-fact "SHAM CONTROL NEGATIVE while
  the anchor EARNS: release-DIRECTION conditioning carries GENUINE calendar
  information" — i.e. the class's gross scale was ~3.5 bp on spot; the 6B
  modeled RT floor is **6.3–11.2 bp = 1.8–3.2× that break-even**. Also
  `FXNG1-A4-P2` (CPI-acceleration form dead; DGS10-level control out-earned),
  `FXFV7-A4-P1` (release-sign spillover dead; sham ≈ anchor).
- Power [DERIVED, court §c3 method, 6B σ 54.9 bp]: single-type n≈81 (UK CPI
  ~12/yr × 6.75y) ⇒ MDE ≈ **17.1 bp**; pooled UK-type n≈340 ⇒ MDE ≈ **8.3 bp**
  — at or above the full modeled RT at every defensible n; per-type strata
  3–5× cost (exploratory-only by the court's own convention).
- Data wall: **no ONS/UK-release calendar exists in any committed artifact**
  (the captured live ONS page states no time-of-day policy and shows 9:30am
  listings; the in-corpus 07:00-London anchor would be a DECLARED CONVENTION
  like JF1's BoJ anchor, PIT build = dated-vintage captures NOT_RUN).
- Anatomy wall: no committed 6B artifact measures any release-minute spike at
  07:00 London (the 6B a2/a4 files cover BoE-1200 and FOMC anchors only) —
  the anatomy-first census gate would be the family's first step, and the
  cost/power walls above bind even if the anatomy exists.

### C-05 `EA-REL` — euro-area morning releases on 6E (11:00-CET HICP/PMI class) — **DUPLICATE-VETO**

Mirror of C-04 on 6E with a stricter geometry wall: `FXNG4-A4-P1/P2` +
`FXNG4-A5-P1/P2` (EZ print-deviation families) died on **ANCESTRY_RHO_BLOCK
vs generic_dow_tue (0.888–0.891)** — "33/37 EZ v2-days are Fridays (2019
re-referencing cluster) so books stack on weekday geometry". Same cost/power
walls as C-04 (6E RT 3.6–6.3 bp; n≈80/type ⇒ MDE ≈ 14.5 bp). **VOID.**

### C-06 `ECB-ACCTS` — ECB accounts-day delayed path transmission on 6E — **DUPLICATE-VETO**

Nearest live inventory: FX-F2 (event-conditioned central-bank day-sets; ECB
stratum already declared). Distinct day-set (accounts publish ~4 weeks after
the meeting — captured FACT above), but: n≈55 ⇒ MDE ≈ **17.5 bp** (6E) =
the FX-F2-6E power starvation the court already labeled unrecoverable; **zero
measured anatomy** (no committed artifact shows any accounts-day signature);
publication minute NOT evidenced (capture states no time convention);
mechanism self-null risk (accounts trail full price discovery; the ECB page
describes them as summary records, not new information events). If FX-F2 is
ever re-opened, accounts days belong as a declared intensity stratum, not a
family. **VOID as NEW.**

### C-07 `BOE-MINS/SPEAKERS` — BoE minutes + speaker diary events on 6B — **NOT_NEW (subsumed) / PIT-blocked**

BoE minutes have been published WITH the Monetary Policy Summary on decision
day since the 2015 restructure ⇒ no separate day-set exists; the "minutes"
space IS FX-F2's MPC day-set (30/32 dated decisions in panel). Speaker/MPR
diary events: cancellation/relocation risk makes the as-scheduled diary
PIT-fragile (the BLS vintage law analog has no in-corpus artifact), no
in-corpus minute anchors, no measured anatomy, and the event class reduces to
FX-F2 strata. **Subsumed; no family.**

### C-08 `GILT-AUCT` — UK gilt auction days on 6B — **DATA-BLOCKED**

Mechanism [MECHANISM_HYPOTHESIS]: scheduled DMO supply changes dealer
inventory ⇒ GBP hedging flow around 11:00-London auction results. This is the
lane's strongest capturable-data candidate — and it still dies on data +
power: **no DMO auction calendar in any committed artifact** (a dmo.gov.uk
vintage build is a NOT_RUN preregistration dependency, mirroring the sibling
lane's JGB-auction finding); **zero measured anatomy** in `6B_a2_sessions.json`
/ `6B_a4_events.json` (auction-day volume signature unknown, NOT_RUN); power
[DERIVED]: n≈160 (≈24/yr × 6.75y) ⇒ 6B MDE ≈ **12.2 bp** vs modeled RT
6.3–11.2 bp — at/above the full cost floor at the only defensible pooled n.
Recorded as the first verdict to revisit IF an owner ever funds a primary
GBP-flow mechanism source at auction times (same disposition as FXJA's
JGB-AUCT).

### C-09 `6E-6B-LEADLAG` — cross-symbol lead-lag (6E leads 6B) — **DUPLICATE-VETO**

`FXFV7-A6-P2` "EURUSD lead-lag diffusion" — SCIENTIFIC_REJECTION (anchor
−8.41/trade; **own-lag control out-earned the anchor**; USD-drift corr +0.025).
A 6E→6B cross-lead family on the futures venue is the same lead-lag signal
class at a venue change — re-clock, barred (Q-3). **VOID.**

### C-10 `ROUND-LEVEL` — round-number / big-figure level triggers on 6E/6B — **DUPLICATE-VETO (owner-law class closure)**

Nearest live/dead class: the range-edge absorption family is closed **against
gated variants** — `TRACKA2-C1C2C3-REGATED-RANGEFADE` (VARIANT_SAME_FAMILY;
"only a mechanism with a NEW payer + new information layer (F-0 three tests)
can carry a range-adjacent trigger"; owner law 2026-09-26). Round-levels are
range-adjacent levels; the claimed NEW payer (option knock-out dealers at
big figures) has **no evidence instrument in this program** (no barrier/
strike/OI data — NOT_RUN), so the new-payer proof cannot even be staged.
**VOID.**

### C-11 `OPT-EXPIRY` — 10am-NY FX options expiry hedging flow on 6E/6B — **DATA-BLOCKED**

The mechanism's conditioning variable (near-the-money expiring strikes/OI) is
NOT_RUN data — no options OI artifact exists. Without it the "family"
degenerates to an every-weekday 10:00-ET clock exposure — which is exactly
what C2-always-in controls own, not a mechanism family. BBO NOT_RUN
compounds fill honesty. **BLOCKED.**

### C-12 `GILT-STRESS-OVL` — 6B gilt-stress conditioning overlay — **NOT_NEW (subsumed by existing strata law)**

Measured anatomy exists — `6B_a6_gilts.json`: era corr(6B ret, Δgilt-10y)
ranges −0.247..+0.172; full-window corr −0.125; mini-budget coupling corr
**−0.675** (n=4 days, 2022-09-23..28); `gilt_stress_days_2022` n_stress=**9**
(vs n_calm=92; median |ret| 1.396% vs 0.318%). Wall: n_stress=9 fails every
fold/stratum floor (JF1 ≥5-per-fold class law); BoE yield-curve data carries
a **declared publication lag** (PIT-usable only ≥1 business day later —
file's own `declared_lag_note`); daily-corr → intraday-overlay transfer is
INFERENCE (the FX-F6 transfer problem); and 2022 stress windows are ALREADY a
declared stratum in carried FX-F3 §9. **Subsumed; 0 identities.**

### Observed-anatomy note (not a candidate; feeds controls)

`6E_a2_sessions.json:ecb_window_baseline_median_volume_by_minute_ct` shows a
persistent median-volume elevation at minute 420 (**07:00 CT** median 271 vs
~100–150 in minutes 415–440's neighborhood, 149→271 across 415→420) in the
ECB-window baseline table. **Attribution NOT_RUN** (weekday/event mix of the
baseline is not decomposed in the artifact; 07:00 CT = 13:00 London in
DST-aligned winter weeks). Recorded so it is consumed by the carried
families' **C2 always-on / clock-only shadow arms** (CYCLE_LAUNCH_DRAFT §5
clock-only shadow law) rather than spawning an unowned "clock-elevation"
family — an unattributed clock elevation is F1/F3 adjacency by construction
and is precisely what the shadow controls exist to absorb.

---

## 3. Ancestry-check table (court §b test applied to every candidate)

Scan basis: all **173** FAMILY_FAILURES.jsonl rows read this lane (41 forex
rows enumerated); dead FX session corpus per PB2_ANCESTRY_COURT_DRAFT §a
(V1-A3-P1 London-open continuation −2.353/PF 0.849/11,459 trades;
V2-A4-P1 Tokyo→London −3.80; V2-A4-P2 London-AM break+retest −3.09; six
cells 12/12 EXPECTANCY_NONPOSITIVE); program warning (NQ_DEEPFOUR_V3_ADDENDUM
§10; DAYTRADER-100 FX session books cost-marginal die at ×2.0).

| candidate | nearest dead entries (family_id + class) | distinguishability (can the dead corpus represent the mechanism class?) | verdict |
|---|---|---|---|
| C-01 FIX-FLOW | TRACKA2-P4A-FIXCERT-01 (SELECTION_REJECTION, DECLARED_BAND_BELOW_MEASURED_COST, binding RC); DTPFX1-A1-MEFIX-VARIANT (VARIANT_SAME_FAMILY); FXFV2-A4-P2 (SCIENTIFIC_REJECTION, London-window session) | **YES — represented and killed**: fix-certainty payer was class-passed on spot; kills were cost-based; futures leg = venue/cost re-tune barred by the RC (court §b4: futures NOT cheaper) | DUPLICATE-VETO |
| C-02 SETTLE-ANCHOR | (no dead row — standing law) | n/a — DC §1.3: settlement/termination mechanics = construction, never alpha | CONSTRUCTION-ONLY, 0 IDs |
| C-03 ME-QE-REBAL | DTPFX1-A1-MEFIX-VARIANT (VARIANT_SAME_FAMILY, month-end re-gate of fix class); FXFV5-A6-P1 (sham-calendar house standard origin) | YES — calendar re-gate of a represented class; IMM calendar itself construction (DC §1.3) | DUPLICATE-VETO |
| C-04 UK-REL | FXFV6-A6-P1 (own-economy CPI reaction; razor PF death; genuine calendar info, cost-unharvestable); FXNG1-A4-P2; FXFV7-A4-P1 | YES — own-economy release-reaction class represented on spot (V6/NG1); venue+minute change without new payer = re-clock; break-even 3.475 bp vs 6B floor 6.3–11.2 bp | DUPLICATE-VETO (+calendar NOT in corpus) |
| C-05 EA-REL | FXNG4-A4-P1/P2, A5-P1/P2 (ANCESTRY_RHO_BLOCK vs generic_dow_tue 0.888–0.891) | YES — EZ print-deviation class represented and killed on weekday geometry | DUPLICATE-VETO |
| C-06 ECB-ACCTS | (nearest LIVE inventory: FX-F2, not dead) + FXFV5/V7 event-family lessons | Partially — V1/V2 corpus could not represent event conditioning, but FX-F2 OWNS that class; accounts = FX-F2 stratum by K1-type reclassification | DUPLICATE-VETO (power n≈55, MDE≈17.5 bp; zero anatomy) |
| C-07 BOE-MINS/SPEAKERS | FX-F2's MPC day-set (live); no dead row needed | n/a — no separate day-set exists (minutes-with-decision); speaker diary PIT-fragile, no anchors | NOT_NEW (subsumed) |
| C-08 GILT-AUCT | (none — no supply-event family in the dead corpus) | Yes, distinguishable in principle — but conditioning calendar NOT in corpus; anatomy NOT_RUN; MDE ≈ 12.2 bp ≥ cost | DATA-BLOCKED |
| C-09 6E-6B-LEADLAG | FXFV7-A6-P2 (lead-lag diffusion; own-lag control out-earns) | YES — same lead-lag signal class; venue re-clock | DUPLICATE-VETO |
| C-10 ROUND-LEVEL | TRACKA2-C1C2C3-REGATED-RANGEFADE (VARIANT_SAME_FAMILY; range-adjacent class closed vs gated variants; new-payer proof required) | YES — range-adjacent level class represented; new-payer (knock-out) evidence instrument NOT_RUN | DUPLICATE-VETO |
| C-11 OPT-EXPIRY | (none) | n/a — conditioning data (strikes/OI) NOT_RUN; degenerates to clock exposure (C2 territory) | DATA-BLOCKED |
| C-12 GILT-STRESS-OVL | FX-F3 §9 declared stress strata (live); FXFV8-A5-P1 lesson (regime exposures resolve to level controls) | n/a — measured daily anatomy exists but n_stress=9, declared-lag PIT, transfer INFERENCE; already a declared stratum | NOT_NEW (subsumed) |

---

## 4. Trial-identity estimates [PROVISIONAL]

- **Delta from this lane: 0 identities.** No NEW family, no diagnostic legs
  proposed, no strata added (C-06 would be an FX-F2 stratum only if that
  family ever reopens — 0 surface now).
- Inherited 6E/6B surface (restated, uncapped): **648 program-hypothetical**
  (288 base = 4 families × 2 symbols × 36; +360 declared strata contingency)
  + RMM Role B **+8** if legalized (NQ-F4 Role-B convention) ⇒ **656**. No FX
  cap is defined by any standing ruling — an explicit owner ceiling is
  required before any registration; PB2 HOLD stands.
- Controls remain NOT counted as trial identities (court §c4 convention
  inherited; placebo-budget ruling pointer CYCLE_LAUNCH_DRAFT §4).

## 5. Provisional D1–D5 (RANKING_FRAMEWORK anchors, applied mechanically)

Applied to the two strongest rejected candidates to show the vetoes are not
hiding package quality (0-15 scale; carried-family scores in RANKING_FRAMEWORK
§3 remain the synthesis lane's inputs, unchanged here):

| candidate | D1 evidence | D2 mechanism | D3 falsifiability | D4 PIT | D5 floor | total | reading |
|---|---|---|---|---|---|---|---|
| C-01 FIX-FLOW (had it lived) | 1 (no on-symbol fix-minute anatomy; dead spot census only) | 1 (same payer as dead class; venue rename) | 1 (binding RC unmet; no reachable power statement) | 2 (fix calendar regular/PIT-able; no in-corpus artifact) | 1 (floor computable; MDE NOT_RUN) | **6** | below every carried row (min 8) — veto-consistent |
| C-08 GILT-AUCT (had it lived) | 1 (zero anatomy on 6B auction days) | 2 (actors/timing named; no distinguishing negative yet) | 1 (MDE ≈ 12.2 bp ≥ cost; calendar preregistration dependency NOT_RUN) | 1 (DMO vintages NOT_RUN) | 1 (floor computable; MDE NOT_RUN) | **6** | the lane's revisit-first candidate; blocked on data, not transport |
| C-04 UK-REL (had it lived) | 1 (no 07:00-London release-minute anatomy in corpus) | 2 (actors/timing named; dead class adjacency = honest 2) | 1 (MDE 8.3–17.1 bp ≥ 6B cost) | 1 (ONS calendar NOT in corpus; anchor would be declared convention) | 1 (floor computable; MDE NOT_RUN) | **6** | dead-class cost wall decisive (3.475 bp break-even vs 6.3–11.2 bp floor) |
| C-06 ECB-ACCTS (had it lived) | 1 (zero anatomy) | 2 (FX-F2-adjacent mechanism, negative undefined) | 1 (MDE ≈ 17.5 bp = known-unrecoverable class) | 1 (publication minute NOT evidenced — capture) | 1 (floor computable; MDE NOT_RUN) | **6** | FX-F2 stratum, not a family |

No D1–D5 score was applied to any carried family this lane (register in
`CARRIED_STATUS.md`; scores unchanged from RANKING_FRAMEWORK §3 / HYPOTHESES_R2
§7).

## 6. NOT_RUN / NOT_OBTAINED register (this lane)

1. CME final-settlement fixing-anchor language — NOT_CAPTURED_PRIMARY
   (cmegroup.com live BLOCKED_HTTP_403; settlement-procedures documents not
   reachable; search results secondary only). Specs-page identity facts ARE
   captured (sha256). Nothing depends on it (C-02 is construction by DC §1.3).
2. Fix-window anatomy on 6E/6B (any minute-level fix-window signature) —
   NOT_RUN and **stay NOT_RUN**: the class is closed by the dead corpus's
   binding RC; measuring it would be prep spent on a barred mechanism.
3. 07:00-London UK-release minute anatomy on 6B; 11:00-CET euro-area release
   anatomy on 6E — NOT_RUN (anatomy-first gate never executed; walls C-04/
   C-05 bind regardless).
4. ONS/UK release-calendar vintage build; DMO gilt-auction calendar build;
   ECB accounts publication-minute evidence — NOT_RUN (C-04/C-08/C-06 data
   walls; no purchase/signup proposed anywhere).
5. Attribution of the 07:00-CT median-volume elevation
   (`6E_a2_sessions.json:ecb_window_baseline_median_volume_by_minute_ct`,
   minute 420 = 271) — NOT_RUN; owned by carried families' C2/shadow controls.
6. Carried NOT_RUNs unchanged: fee account verification (A7), BBO/fill
   realism, FX-F4 6B gap-std anatomy, surprise vintages, CIP vintages +
   real-time SOFR source decision (owner), 6B holiday grid 0/42, 6E ECU26/
   ECZ26 + 6B 2023Q1–2024Q2 expiry cells, D1–D12 all open.

## 7. Sources

- Local artifacts (sha-pinned in their own lanes): FX_HYPOTHESES.md,
  RANKING_FRAMEWORK.md, PB2_ANCESTRY_COURT_DRAFT.md, HYPOTHESES_R2.md,
  CYCLE_LAUNCH_DRAFT.md, DATA_READINESS_6E/6B.md,
  `cost_roll_events_fxeb.json`, 6E/6B a1/a2/a4/a6 analysis JSONs,
  FAMILY_FAILURES.jsonl (all 173 rows), root FINAL_REPORT.md
  ("root main d8cf8eca").
- New captures this lane (sha256 in `SHA256SUMS_lane.txt`; attempts in
  `fetch_log.jsonl`): `captures/cme_specs_6E_archive20210301.html`,
  `captures/cme_specs_6B_archive20210301.html` (web.archive.org replays of
  cmegroup.com — BLOCKED_HTTP_403 live, routing law followed),
  `captures/ecb_accounts_20261004.html` (ecb.europa.eu direct),
  `captures/ons_releasecalendar_20261004.html` (ons.gov.uk direct).
- Machine mirror: `hypotheses_fxeb_r3.json` (schema hypotheses_fxeb_r3@1).

— End HYPOTHESES_FXEB_R3.md. Zero PnL/returns entered any cell; 5 URL fetch
attempts + 2 searches, all logged; zero git beyond the one permitted
rev-parse + the two status calls; 0 NEW families, 12 adjudications, every
ancestry check cited; missing evidence is NOT_RUN, never PASS. No
registration, no trial creation — proposals and vetoes on paper only.
