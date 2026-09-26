# EVENTS_failres_REPORT — PIT primary-source event timeline, ERP1-TRACKA-COHORT-1

Labels: **DIAGNOSTIC_OUTCOME_EXPOSED** (the fold windows are outcome-exposed for the RANGEEXP family) · **FAILURE_ROOT_CAUSE_RESEARCH** · **EVENTS_OVERLAY_ONLY — NOT_CAUSAL_EVIDENCE**

Lane: `failres-events` (pit-event-data-lane) · Cycle: `ERP1-TRACKA-COHORT-1` · Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/erp1-tracka-cohort-1/failres-events` · Branch: `orca/erp1-ta1-failres-events` · Base/actual start SHA: `05168bfebc0dc53f8cc2e6b2a7f0cb79bc80b0a9`

Companion artifacts (same directory):
- `failres_events_timeline.jsonl` — 131 events + 1 header line (schema `failres_events/timeline@1`)
- `failres_events_PROVENANCE.json` — per-event URL status, fetch log (13 entries), search log (10 entries), schema `failres_events/provenance@1`

This lane is **outcome-blind**: no PnL, no price data, no diag outputs were read. The timeline exists only so a later lane can run event-day vs non-event-day splits. Nobody downstream may call any co-occurrence found here causal (law already written; re-stated in section 4).

---

## 1. Method, source classes, timestamp verification honesty

**Method.** For every event we record `event_time_utc` (when the thing happened / release instant), `publication_time_utc` (when the world could first read it — normally equal to event_time for scheduled releases), `available_time_utc` (when a PIT researcher with internet could FIRST know the event would happen at that time), `time_precision` (EXACT / APPROX_MINUTES / APPROX_HOURS / DATE_ONLY), `expected_vs_actual`, a `primary_source_url`, `source_class`, `timestamp_basis` and `fetch_status`. All timestamps UTC with explicit DST handling.

**Timestamp conventions — each verified from primary or contemporaneous sources, not pattern-guessed:**

| Series | Convention | Verification basis |
|---|---|---|
| FOMC statement | 14:00 ET = 18:00Z (EDT) / 19:00Z (EST); presser 14:30 ET | 6 statement pages fetched this session; each states "For release at 2:00 p.m. EDT/EST" (monetary20220615a, 20211103a, 20210616a, 20220727a, 20221214a, 20240918a); all 34 FOMC events dated from the fetched federalreserve.gov FOMC calendar |
| US CPI / NFP | 08:30 ET = 12:30Z (EDT) / 13:30Z (EST) | 3 BLS archive pages fetched; each carries "Transmission of material in this release is embargoed until 8:30 a.m. (ET) <date>" (cpi_11102021, cpi_06102022, cpi_01122022) |
| ECB (until 2022-06-09) | decision 13:45 CET/CEST, presser 14:30 CET/CEST | ECB pr220627 (27 Jun 2022) states the previous timing explicitly; mp220721 page fetch confirms the NEW format live |
| ECB (from 2022-07-21) | decision 14:15 CET/CEST, presser 14:45 CET/CEST | ECB press release 27 Jun 2022 "New times for ECB's monetary policy decisions and press conferences" (effective 21 Jul 2022); mp220721 fetched page text: "press conference starting at 14:45 CET today" |
| Eurostat HICP flash | 11:00 Brussels = 09:00Z (CEST) / 10:00Z (CET) | Flash dates verified from Eurostat euro-indicators releases: 96/2022 (31 Aug 2022), 106/2022 (29 Jul 2022), 98/2022 (1 Jul 2022), 107/2022 (confirms 31 May), March final (confirms 1 Apr) — **note the intra-window calendar inconsistency, section 3** |

**Source-class counts (131 events):**

| source_class | n | What it means here |
|---|---|---|
| PRIMARY | 110 | Issuer document or canonical issuer schedule (Fed statements, BLS archives, ECB press releases, Eurostat releases, FDIC, BoJ statement PDFs, Executive Order 14257). Of these, **10 events had their page fetched and content/time verified this session** (`PRIMARY_PAGE_VERIFIED_FETCHED`, `PRIMARY_PAGE_VERIFIED_SEARCH`); the rest cite canonical issuer URLs/standing schedules verified on sibling pages. |
| WIRE_CONTEMPORANEOUS | 9 | Contemporaneous wire/major-media accounts of un-scheduled events (invasion, Nord Stream statements, parity breach, TTF record, US election call, French dissolution/no-confidence). Reuters/Bloomberg pages are paywalled; where the surfaced URL slug was reconstructed from the surfaced title it is flagged `SEARCH_SURFACED_URL_SLUG_RECONSTRUCTED`. |
| SECONDARY_RECONSTRUCTION | 12 | Later/secondary sources (Wikipedia etc.) or date-level-only events: Evergrande risk-off, German election 2021, Nord Stream June/July flow mechanics (operator pages unreachable), TTF peak minute-level, sabotage minute attribution, SVB minute, UBS-CS minute, German coalition collapse, German fiscal package 2025, debt ceiling 2023. |

**Honest verification statement:** roughly **10 of 131 timestamps were verified minute-exact from a fetched primary page**; ~95 rely on the issuer's standing schedule verified at the level of fetched sibling samples plus canonical URLs (Fed 14:00 ET convention ×6 fetched, BLS 08:30 ET ×3 fetched, ECB 14:15/13:45 formats ×2 verified, Eurostat 11:00 Brussels ×5 release IDs cross-checked); ~17 are wire- or secondary-based with explicit `time_precision` downgrades. No timestamp was invented: every imprecise time carries `time_precision ∈ {APPROX_MINUTES, APPROX_HOURS, DATE_ONLY}` and a note.

**DST was handled per-event, from the fetched primary pages, not from a rule of thumb.** Worked example that changes results: the dispatch's default ("FOMC 19:00Z in EST") applied to **2021-11-03 would be wrong** — US DST ended 2021-11-07, so the taper statement was released **18:00Z** (page says "2:00 p.m. EDT"). Similar traps: US CPI is 13:30Z from Nov through early Mar (EST) but 12:30Z otherwise; ECB decisions moved 30 minutes mid-F2 when the format changed on 2022-07-21.

---

## 2. Timeline tables per window

Full machine-readable detail (including `available_time_utc`, `expected_vs_actual`, URLs, precision flags) is in `failres_events_timeline.jsonl`. Counts: **F1 = 26, F2 = 40, F3 = 20, F5 = 29, F6 = 16.**

### F1 — 2021-01-01 .. 2021-10-31 (26 events, detail)

| Date (UTC) | Event | Time | Note |
|---|---|---|---|
| 2021-01-13 | US CPI (Dec) | 13:30Z | +1.4% — reflation baseline |
| 2021-01-21 | ECB hold | 12:45Z | PEPP flexibility |
| 2021-01-27 | FOMC hold | 19:00Z (EST) | deep accommodation |
| 2021-02-10 / 03-10 | US CPI | 13:30Z | +1.4 / +1.7 — base effects start |
| 2021-03-11 | ECB: PEPP acceleration | 12:45Z | "significantly higher pace" to cap yields |
| 2021-03-17 | FOMC hold | 18:00Z (EDT) | dots unchanged; SLR week |
| 2021-04-13 | US CPI (Mar) | 12:30Z | +2.6% vs ~1.7% exp |
| 2021-04-22 | ECB hold | 11:45Z | PEPP Q2 pace kept |
| 2021-04-28 | FOMC hold | 18:00Z | "not yet time" to discuss taper |
| 2021-05-12 | US CPI (Apr) | 12:30Z | **+4.2% vs ~3.6% — first big surprise** |
| 2021-06-10 | ECB hold (forecasts up) | 11:45Z | "transitory" framing |
| 2021-06-10 | US CPI (May) | 12:30Z | +5.0% vs ~4.7% |
| 2021-06-16 | FOMC hold — **dot shift** | 18:00Z | 2 hikes priced by 2023; hawkish pivot; USD breakout leg begins |
| 2021-07-08 | ECB strategy review | 12:30Z presser | symmetric 2% target; structurally dovish EUR |
| 2021-07-13 | US CPI (Jun) | 12:30Z | +5.4% vs ~4.9% |
| 2021-07-22 | ECB hold (new guidance) | 11:45Z | dovish reset post-review |
| 2021-07-28 | FOMC hold | 18:00Z | taper discussions "well advanced" |
| 2021-08-11 | US CPI (Jul) | 12:30Z | +5.4% vs ~5.3% |
| 2021-09-09 | ECB: PEPP recalibration | 11:45Z | "moderately lower pace" Q4; financing-conditions criterion |
| 2021-09-14 | US CPI (Aug) | 12:30Z | +5.3% in line |
| 2021-09-16→20 | Evergrande risk-off | ~00:00Z Sep 20 | global risk-off Monday; USD bid |
| 2021-09-22 | FOMC hold — taper signal | 18:00Z | "may soon be warranted" |
| 2021-09-26 | German federal election | 16:00Z | polls close 18:00 CEST, exit polls at close; SPD first |
| 2021-10-13 | US CPI (Sep) | 12:30Z | +5.4% vs ~5.3% — cements Nov taper |
| 2021-10-28 | ECB hold | 11:45Z | Lagarde: hike conditions "very unlikely" in 2022 |

**F1 regime summary:** Fed overtightening *expectations* (dot shift 16 Jun, taper path) against an ECB that repeatedly reaffirmed accommodation; EURUSD ground down from ~1.20+ to ~1.16 across the window. Event density is low; the notable risk-off cluster is Evergrande (Sep 16-20).

### F2 — 2021-11-01 .. 2022-08-31 (40 events, deepest; includes dispatch-assigned 2022-09-01..13 items)

| Date (UTC) | Event | Time | Note |
|---|---|---|---|
| 2021-11-03 | **FOMC: taper announced** | **18:00Z (EDT!)** | $10B/$5B monthly cuts; no tantrum (pre-announced) |
| 2021-11-10 | US CPI (Oct) | 13:30Z | **6.2% vs 5.9% — shock** |
| 2021-12-10 | US CPI (Nov) | 13:30Z | 6.8% vs 6.7% |
| 2021-12-16 | ECB: PEPP wind-down modalities | 12:45Z | APP step-up 40/30/20B |
| 2022-01-12 | US CPI (Dec) | 13:30Z | 7.0% (in line); core 5.5% |
| 2022-01-26 | FOMC hold | 19:00Z | "soon appropriate" to hike |
| 2022-02-03 | ECB hold — Lagarde pushback | 12:45Z | hike "very unlikely" in 2022 |
| 2022-02-10 | US CPI (Jan) | 13:30Z | 7.5% vs ~7.3% — hot |
| 2022-02-21 | Putin recognizes DNR/LNR | 19:35Z | kremlin.ru dateline 22:35 MSK; sanctions begin |
| 2022-02-24 | **Russia invades Ukraine** | ~03:00Z | address 06:00 MSK; strikes within minutes; max risk-off, EUR sold |
| 2022-03-02 | EZ HICP flash (Feb) | 10:00Z | 5.8% record at the time |
| 2022-03-10 | US CPI (Feb) | 13:30Z | 7.9% vs 7.8% |
| 2022-03-10 | **ECB: accelerated APP exit + Ukraine flexibility** | 12:45Z | drops "very unlikely"; EUR short-covering rally |
| 2022-03-16 | **FOMC +25bps liftoff** | 18:00Z | to 0.25-0.50% |
| 2022-04-01 | EZ HICP flash (Mar) | 09:00Z | 7.5% |
| 2022-04-12 | US CPI (Mar) | 12:30Z | 8.5% vs 8.4% |
| 2022-04-14 | ECB: APP net end 1 Jul | 12:45Z | rates "some time after" |
| 2022-05-02 | EZ HICP flash (Apr) | 09:00Z | 7.5% |
| 2022-05-11 | US CPI (Apr) | 12:30Z | 8.3% vs ~8.2% — deceleration miss, core hot |
| 2022-05-31 | EZ HICP flash (May) | 09:00Z | 8.1% |
| 2022-06-09 | ECB guidance: 21 Jul +25, possible bigger in Sep | 11:45Z | fragmentation spreads blow out same day |
| 2022-06-10 | **US CPI (May): 8.6% vs 8.3%** | 12:30Z | forced the 75bp Fed; seeds of parity |
| 2022-06-14/15 | **Nord Stream 1 cut to ~40%** | flows 04:00Z Jun 15 | announcement Jun 14 (~1 day ahead); energy shock |
| 2022-06-15 | **FOMC +75bps** | 18:00Z | largest since 1994; EURUSD 1.0441 low Jun 17 |
| 2022-07-01 | EZ HICP flash (Jun) | 09:00Z | 8.6% |
| 2022-07-11→21 | NS1 zero flows (10-day maintenance) | 06:00Z Jul 11 | announced ~mid-June; parity fear window |
| 2022-07-13 | **US CPI (Jun): 9.1% vs 8.8%** | 12:30Z | cycle peak print; EURUSD < parity same hour |
| 2022-07-14 | **EURUSD breaks parity** (20-yr low) | ~07:00Z | market-level event; first sub-parity prints 13 Jul post-CPI (feed-dependent) |
| 2022-07-21 | **NS1 restarts at 40%** | ~05:00Z | same morning as ECB |
| 2022-07-21 | **ECB +50bps + TPI** (surprise size) | 12:15Z | first hike in 11 yrs; negative rates end 27 Jul; anti-fragmentation tool |
| 2022-07-25→27 | **NS1 cut to 20%** | flows 04:00Z Jul 27 | Gazprom announcement Jul 25; 2-day announcement→flow gap |
| 2022-07-27 | FOMC +75bps | 18:00Z | "slower pace at some point" — dollar top of leg |
| 2022-07-29 | EZ HICP flash (Jul) | 09:00Z | 8.9% — **released 29 Jul, not 1 Aug** |
| 2022-08-05 | US NFP (Jul): +528k vs ~250k | 12:30Z | kills recession narrative; USD up |
| 2022-08-10 | US CPI (Jul) | 12:30Z | 8.5% vs 8.7% — first dovish surprise; risk rally |
| 2022-08-19 | NS1 3-day stop announced (Aug 31-Sep 2) | ~15:00Z | 12 days before flow stop |
| 2022-08-26 | **TTF record ~EUR 340/MWh** | intraday | energy terms-of-trade worst ever |
| 2022-09-02 | **NS1 indefinite halt announced** | ~17:00Z | scraps scheduled 01:00Z Sep 3 resumption (Reuters); EURUSD <1.00 within days |
| 2022-09-08 | **ECB +75bps** | 12:15Z | largest ever at the time |
| 2022-09-13 | US CPI (Aug) | 12:30Z | 8.3% vs 8.1% — hawkish shock ends relief rally |

**F2 regime summary:** the window stacks three adverse channels on EURUSD — (i) Fed-ECB rate differential (Fed front-runs and outsizes; ECB arrives late and half-size until Jul 21), (ii) energy terms-of-trade (NS1 flow cuts Jun 15 / Jul 27 / Sep 2; TTF record Aug 26), (iii) risk-off (invasion Feb 24). The Jul 21-27 micro-window alone contains NS1 restart, ECB +50/TPI, NS1 20% cut, FOMC +75 and a flash HICP — the densest event cluster in the dataset.

### F3 — 2022-09-14 .. 2023-06-30 (20 events, COARSE)

FOMC: 2022-09-21 +75 (18:00Z) · 2022-11-02 +75 (18:00Z EDT) · 2022-12-14 +50 (19:00Z, verified page) · 2023-02-01 +25 (19:00Z) · 2023-03-22 +25 (18:00Z) · 2023-05-03 +25 (18:00Z) · 2023-06-14 skip/hold (18:00Z).
ECB: 2022-10-27 +75 (12:15Z CEST) · 2022-12-15 +50 + QT (13:15Z) · 2023-02-02 +50 (13:15Z) · 2023-03-16 +50 (13:15Z) · 2023-05-04 +25 (12:15Z) · 2023-06-15 +25 (12:15Z).
Specials: UK mini-budget 2022-09-23 (GBP record low Mon 26th) · **Nord Stream sabotage 2022-09-26** (detonations 00:03Z & 17:03Z; public confirmation evening 26th–27th) · HICP flash 10.6% 2022-10-31 (09:00Z) · **US CPI dovish shock 2022-11-10** (7.7% vs 8.0%, 13:30Z — huge risk rally) · **SVB failure 2023-03-10** (~17:00Z, FDIC pr23019) · **UBS–Credit Suisse 2023-03-19** (~22:30Z Sunday, before Asia open) · US debt-ceiling deal 2023-05-27 / signed 2023-06-03.

### F5 — 2024-05-01 .. 2025-02-28 (29 events, detail)

| Date (UTC) | Event | Time | Note |
|---|---|---|---|
| 2024-05-01 | FOMC hold + QT slowdown | 18:00Z | hawkish hold |
| 2024-05-15 | US CPI (Apr) | 12:30Z | softer m/m — relief |
| 2024-06-06 | **ECB -25bps** (first cut, before Fed) | 12:15Z | hawkish-cut framing |
| 2024-06-09 | **Macron dissolves Assembly** | 19:00Z address | Sunday; priced at Mon open; OAT premium blowout |
| 2024-06-30 / 07-07 | French elections R1/R2 | 16:00Z exit polls | hung parliament |
| 2024-06-12 | US CPI (May) soft | 12:30Z | **same day as FOMC** |
| 2024-06-12 | FOMC hold; dots 1 cut | 18:00Z | stacked window |
| 2024-07-11 | US CPI (Jun) −0.1% m/m | 12:30Z | Sept-cut odds jump |
| 2024-07-31 | FOMC hold; "Sept on the table" | 18:00Z | |
| 2024-07-31 | **BoJ +~15bps + taper** | ~03:00Z | carry-unwind seed (time approx) |
| 2024-08-05 | **Yen-carry unwind crash** | Tokyo open | Nikkei −12.4%, VIX >65; global whipsaw |
| 2024-08-14 | US CPI (Jul) | 12:30Z | 2.9% vs 3.0% |
| 2024-09-11 | US CPI (Aug) | 12:30Z | 2.5% vs 2.6% — seals 50bp debate |
| 2024-09-12 | **ECB -25bps** | 12:15Z | day after CPI, day before FOMC — triple stack |
| 2024-09-18 | **FOMC −50bps** | 18:00Z | to 4.75-5.00% (verified page) |
| 2024-10-10 | US CPI (Sep) | 12:30Z | core 3.6% hot miss |
| 2024-10-17 | ECB -25bps | 12:15Z | |
| 2024-11-05→06 | **US election; AP call** | **10:34Z Nov 6** | AP call 5:34 a.m. ET = 10:34Z (NOT 05:34Z); EURUSD −~1.8% Nov 6 |
| 2024-11-06 | German coalition collapse | ~18:00Z | Scholz fires Lindner — same day as US call |
| 2024-11-07 | FOMC −25bps | 19:00Z | post-election |
| 2024-11-13 | US CPI (Oct) | 13:30Z | in line |
| 2024-12-04 | **Barnier government falls** (331 votes) | ~18:30Z | first no-confidence win since 1962; OAT spread |
| 2024-12-11 | US CPI (Nov) | 13:30Z | in line |
| 2024-12-12 | ECB −25bps | 13:15Z | |
| 2024-12-18 | **FOMC −25bps hawkish-cut** | 19:00Z | dots 2 cuts 2025 (from 4); USD +1.2% day |
| 2025-01-15 | US CPI (Dec) | 13:30Z | m/m +0.4% hot; DXY ~110 area |
| 2025-01-24 | BoJ +25bps | ~03:30Z | time approx |
| 2025-01-29 | FOMC hold | 19:00Z | |
| 2025-01-30 | ECB −25bps (day after Fed hold) | 13:15Z | maximal differential widening; EURUSD ~1.038 |
| 2025-02-12 | US CPI (Jan) hot | 13:30Z | window closes USD-bid |

### F6 — 2025-03-01 .. 2025-12-31 (16 events, COARSE)

FOMC: hold 2025-03-19 (18:00Z) · hold 2025-05-07 · hold 2025-06-18 · hold 2025-07-30 · **−25 2025-09-17** · −25 2025-10-29 (QT ends Dec 1) · −25 2025-12-10 (19:00Z).
ECB: −25 2025-03-06 (13:15Z) · hold 2025-04-17 (12:15Z) · **−25 to 2.00% 2025-06-05** · hold 2025-07-24 · hold 2025-09-11 · hold 2025-10-30 · hold 2025-12-18 (13:15Z).
Specials: **German fiscal package 2025-03-04/05** (announced evening Mar 4, detail Mar 5; Bundestag vote Mar 18) — EURUSD +~3-4% Mar 5; **"Liberation Day" tariffs 2025-04-02** (EO 14257, Rose Garden ~20:00Z; EURUSD **rose** ~2% next day despite EU-tariff exposure — channel inversion); **90-day tariff pause 2025-04-09** (~17:20Z Truth Social; S&P +9.5% day; EURUSD chop >1.10).

---

## 3. PIT discipline notes (where the timestamps bite)

**(a) available_time << event_time — scheduled releases (the majority, 95+ events).** FOMC meeting dates are published ~6-18 months ahead (the Fed publishes next-year calendars mid-year); BLS CPI dates are on the annual schedule months ahead; ECB annual meeting calendar is published the prior December; Eurostat release calendar is rolling. For all of these, `available_time` is the schedule-publication date (approximated at month-level, flagged), and the true PIT information edge is zero about the *timing* and only about the *content* surprise. Overlay consequence: a strategy that is "surprised" on FOMC day was not surprised by the *date* — only by `expected_vs_actual`.

**(b) available_time < event_time by 1-2 days — operator announcements (Nord Stream flow changes).** The June 14 announcement → June 15 flow cut; July 25 announcement → July 27 cut; August 19 announcement → August 31 stop; September 2 evening announcement → the already-scheduled 01:00Z September 3 resumption that never came (Reuters). Energy events have an **announcement PIT and a flow PIT that differ**; any overlay that dates the July event only on the 27th misses that the market had 36 hours to reprice.

**(c) available_time == event_time (or later) — un-scheduled shocks.** Invasion Feb 24 2022 (~03:00Z address, strikes within minutes — nothing to know earlier except the buildup); **Nord Stream sabotage Sep 26 2022 (detonations 00:03Z and 17:03Z, public confirmation only hours later — the inverse case: the event precedes its own observability)**; the AP election call (formal marker 10:34Z Nov 6 2024, but markets had repriced from live results for 8+ hours before the "official" call); UBS-CS announced deliberately ~22:30Z Sunday before Asia's Monday open.

**(d) Intra-window convention changes (the classic PIT trap).** ECB moved decisions 13:45→14:15 CET and pressers 14:30→14:45 CET effective **21 July 2022** (pr220627, 27 Jun 2022) — a researcher using one constant ECB time across F2 is wrong by 30 minutes for every post-Jul-21 meeting. Fed/BLS times shift by one hour with US DST twice inside several windows (verified: 2021-11-03 statement was EDT/18:00Z, not EST/19:00Z). Eurostat flash dates are **not** a fixed pattern: July 2022 flash landed 29 July, two days *before* month end; August 2022 on 31 August; May 2022 on 31 May. Any overlay keying "first-of-month flash" will mis-stamp.

**(e) Reconstruction risk flagged explicitly (12 events).** Nord Stream operator statements: Nord Stream AG/Gazprom operator pages are unreachable this session; flow mechanics are reconstructed from contemporaneous wires + encyclopedic summary (`SECONDARY_RECONSTRUCTION`), with minute-level announcement times marked APPROX_HOURS. TTF record peak is date-level only. BoJ release minutes approximated (canonical statement PDF cited). Kremlin.ru timed out this session — invasion and DNR/LNR timings rest on contemporaneous multi-outlet wire reporting (03:00 GMT / 22:35 MSK), with the Kremlin transcript cited as the primary reference and the fetch failure logged as an incident.

**(f) One dispatch input corrected during verification.** The AP 2024 race call is **5:34 a.m. ET Nov 6 = 10:34Z**, not 05:34Z; and the euro's first sub-parity prints occurred **13 July 2022** after the US CPI release, with the decisive 20-yr-low break on 14 July — the timeline records both, with the market-level event flagged as having no single publication instant.

---

## 4. Non-causality statement (binding on downstream overlay)

This artifact is **EVENTS_OVERLAY_ONLY — NOT_CAUSAL_EVIDENCE**. It documents, with primary-source timestamps, when information became available. It does **not** establish that any event caused any PnL outcome, and the overlay lane may NOT:

- claim causal transmission from event to fold loss on the basis of co-occurrence or same-day timing alone;
- treat `expected_vs_actual` "surprises" as exogenous instruments without modelling anticipation (markets price in advance; several FOMC days moved mostly on the *presser*, 30 minutes after the statement);
- aggregate "event days" as a homogeneous class (a 12:30Z CPI, a 12:15Z ECB cut, and a 19:00Z hawkish dot-plot hit entirely different parts of the 07:00-18:00 UTC strategy window; the JSONL timestamps allow but do not perform that split).

What the overlay lane MAY legitimately conclude from this timeline: that a fold window is dense (F2) vs sparse (F1) in adverse-EUR events; that specific negative folds coincide with same-day macro releases (e.g., CPI at 12:30Z inside the 07:00-18:00 UTC holding window) which a PIT filter could have conditioned on; and that event-day vs non-event-day PnL splits are well-identified using `available_time_utc`. Correlation observed downstream stays correlation.

---

## 5. Known limitations

1. **Consensus figures** are secondary (Reuters poll values reported in contemporaneous coverage; not archived from a paywalled terminal by this lane). Marked inline where used; `null` where not confidently reconstructable (all 2021 Jan-Mar CPI, several 2022 months, all Eurostat flashes).
2. **Wire timestamps are approximate** (±1-2 hours) where the paywalled Reuters/Bloomberg first-move time could not be read: NS1 June 14/July 25/August 19 announcements, TTF peak minute, sabotage public-confirmation instant, UBS-CS release minute, Macron/Barnier announcement minutes. All carry APPROX precision flags.
3. **Operator primary pages unreachable**: Nord Stream AG site defunct/unreachable; Gazprom statements only via wires → `SECONDARY_RECONSTRUCTION` for flow mechanics. GASSO/OPAL not consulted.
4. **kremlin.ru fetch failed** (connect timeout, incident logged); invasion timing rests on contemporaneous wire consensus (03:00 GMT), the Kremlin transcript cited as reference.
5. **Canonical-URL items not individually fetched**: ~95 scheduled events cite canonical Fed/BLS/ECB/Eurostat URLs whose time conventions were verified on fetched sibling samples rather than per-page (disclosed per-event via `fetch_status`). A handful of ECB press-release hash-URLs for 2021/2024 could not be resolved by search and cite the ECB's standing monetary-policy-decisions page instead.
6. **2025 Fed/ECB decision details** (F6 coarse) are from public record and official calendars; statement pages were not re-fetched per event (marked in `expected_vs_actual`).
7. **SNB** events dropped for lack of a verifiable release-minute primary source within budget (dispatch made them optional "if primary-sourced"); BoJ included with approximated times.
8. **F2 window boundary**: dispatch assigned the 2022-09-01..13 items (NS1 halt Sep 2, ECB Sep 8, CPI Sep 13) to F2; the JSONL validates F2 membership with the extended bound (2021-11-01..2022-09-13) and the header documents this.

---

*End of report. Artifacts: `failres_events_timeline.jsonl` (131 events + header), `failres_events_PROVENANCE.json` (fetch/search logs + per-event status), this report. Labels: DIAGNOSTIC_OUTCOME_EXPOSED · FAILURE_ROOT_CAUSE_RESEARCH · EVENTS_OVERLAY_ONLY — NOT_CAUSAL_EVIDENCE.*
