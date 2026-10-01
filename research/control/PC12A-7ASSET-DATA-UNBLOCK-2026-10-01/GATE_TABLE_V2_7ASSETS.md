# GATE_TABLE_V2_7ASSETS — session 2 (2026-10-01, owner-directed lane continuation)

Session 2 of `PC12A-7ASSET-DATA-UNBLOCK-2026-10-01`, branch
`orca/pc12a-7asset-unblock-20261001`, base `8b8c24a5` (session-1 chain
`f947fc19`→`eaea0116`→`8b8c24a5`). Baseline: OWNER_PACKET v2 + GATE_UPDATE v2
+ XCHECK_REPORT v2 + their corrections (fixing ≠ publication; FRED FX channel
stale ≥3bd; EIA/FRED = shared-source). Labels: `PASS` / `FAIL` / `NOT_RUN_*`
with evidence; no inferred PASS. New evidence files (all sha256 in
`MANIFEST_IBKR_RO.json` / `MANIFEST_RAW.json`):
`d1b_spot_metals_bid_channel.json`, `d1_lastbars_availability_point1_FIXED.json`,
`d2_expired_month_resolution.json`, `d3_energy_front_bidask_30d.json`,
`d4_entitlement_timeout_guarded.json` (+ hung prior attempt disclosed),
`d5_contfut_details_rollcheck.json`, `d6_full_adjusted_last.json`,
`COVERAGE_REPORT.json`, `ENERGY_ADJUSTED_ANALYSIS.json`,
`AVAILABILITY_EVIDENCE.json` (this session's access-time ledger).

## The 7 × 5 gate table

Legend per column: **price** = usable daily price series w/ provenance ·
**PIT/avail** = availability/lag evidence class · **cost** = measured vs
statement-needed · **vehicle/roll** = tradable vehicle + roll/chain rule ·
**coverage** = daily-clock cohort usability.

| asset | price | PIT / availability | cost | vehicle / roll | coverage |
|---|---|---|---|---|---|
| **NZDUSD** | **PASS** IBKR D1 BID/ASK 6y (1553d) + 2 archives | **MEASURED_BASIS** (FRED p50 9.38 / ECB 21.52 bps); same-evening closed-bar availability **MEASURED point-1** (just-closed 09-30 bar retrievable 22:52 ET; energy 22:31 ET ~5.5h after 17:00 ET close) + forming next-fx-day bar present; next-day persistence = point-2 PREPARED_NOT_RUN; FRED FX channel ≥3bd stale (2 obs) — historical-cross-check-only | spread **MEASURED** (p50 0.88 bps 6y); commission/swap/slippage **NOT_RUN_STATEMENT** | FX-spot CASH IDEALPRO — n/a roll | **PASS** daily: 96.0/98.7% archive cover, 1 isolation day, 1552-day streak |
| **USDCHF** | **PASS** same shape (1553d) | **MEASURED_BASIS** (9.32 / 18.43 bps); rest identical to NZDUSD | spread **MEASURED** (p50 4.51 bps); rest NOT_RUN_STATEMENT | FX-spot — n/a | **PASS** daily: 96.0/98.7%, 1 isolation day, 1552-day streak |
| **XAUUSD** | **PASS** IBKR D1 + TD archive (99.2% cover) | **MEASURED_BASIS** (TD p50 3.2462 bps exact-reproduced); GLD proxy r 0.9857 (proxy-class); lag ASSUMED per XAU freeze law; forming-bar point-1 measured | spread **MEASURED** (p50 5.52 bps); rest NOT_RUN_STATEMENT | CMDTY SMART (identity frozen) — n/a roll | **PASS** daily: 99.2% TD cover, 12 isolation days, 1531-day streak |
| **XAGUSD** | **PASS, panel-only** IBKR D1 panel (1544d) — research use blocked by the PIT gate (see PIT cell) | **FAIL_PIT_NO_ARCHIVE** still: spot-level archive absent; stooq = "Access denied" served TO a real browser; LBMA = Cloudflare hard-block in-browser (both recorded in XAG_BROWSER_ATTEMPTS_2026-10-01.json, TRANSCRIPT_DERIVED_RECORD class - bytes not captured at attempt time); TwelveData plan-blocked; SLV proxy r 0.9827 (proxy-class only) | spread **MEASURED** (p50 10.35 bps — widest of four); rest NOT_RUN_STATEMENT | CMDTY SMART — n/a roll | **PASS** daily panel; PIT gate blocks research use |
| **BRENT** | signal **PASS** (EIA RBRTE official, 1512d, 0 holes>5d, dual-channel retrieval-confirmed single-source); execution **FAIL** | EIA/FRED energy channel 1-business-day serving lag (**2 obs measured**); ADJUSTED_LAST forming bar exists (2026-10-01 bar at 22:51 ET); closed-bar lag NOT_MEASURED | front spread **MEASURED-SAMPLE** (COIL p50 12.60 / p90 32.95 bps, 29d); commission/swap NOT_RUN_STATEMENT | **FAIL chain**: expired months 16/16 unresolved (`includeExpired=True` returned EMPTY contract details; the prior probe's error-200 shape is the second resolution shape — both negative); ADJUSTED_LAST channel exists but adjustment is dollar-scale-small (max div vs TRADES: $1.73 BRENT / $1.11 WTI / $0.057 NG over 6y — a genuine roll chain would diverge by tens of dollars) → NOT a certified back-adjusted chain; roll rule not exposed (D5: no adjust* field) | EIA covers 97.6% of CONTFUT days; CONTFUT flat-OHLC 100% 2020-22 → 0% 2025 (synthetic backfill boundary quantified per year) |
| **WTI** | signal **PASS** (EIA RWTC, 1494d); execution **FAIL** | same class as BRENT | front spread **MEASURED-SAMPLE** (CL p50 3.23 / p90 4.43 bps, 30d) | **FAIL chain** (same 16/16 error-200 class; COIL/CL/NG all) | EIA 97.9%; flat 100% 2020-22 → 0% 2025 |
| **NATGAS** | signal **PASS** (EIA RNGWHHD — **first HH archive on file**); execution **FAIL** | same class | front spread **MEASURED-SAMPLE** (NG p50 6.54 / p90 7.02 bps, 30d) | **FAIL chain**; AECO/TTF additionally non-IBKR (owner-named sources) | EIA 98.0%; flat boundary EARLIER: 97.2% '21 → 0% '25 |

## Gates actually OPENED vs merely more data

**Genuinely opened (state change, evidence-backed):**
1. **Energy signal-side price gate** — from "BLOCKED_NO_PRICE_DATA / no
   archive" (NATGAS) and "REPORT_ONLY" breadth to official span-complete
   daily archives for all three, plus measured channel serving lag. The
   class-(b)-style daily signal inputs for USDJPY-S065, USDCAD-S090,
   EURUSD-S063 (Henry-Hub leg) are now *data-ready pending amendment* (not
   admitted).
2. **Energy front spread measurement** — F-3 (REPORT_ONLY retry numbers)
   superseded by landed raw BID/ASK (29-30d) + computed spreads.
3. **IBKR HMDS D1 same-evening closed-bar availability (point-1)** — the
   just-closed 2026-09-30 bars (FX close 17:00 ET) were retrievable on all 7
   instruments at 22:31–22:52 ET; FX BID additionally served the forming
   2026-10-01 bar. Next-day persistence: point-2 PREPARED_NOT_RUN. Class: INTRADAY_FORMING_MEASURED;
   closed-bar availability still NOT_MEASURED (point-2 script prepared:
   identical re-run next business day).
4. **Coverage gates for the daily cohort** — interior-gap/weekday/streak/
   isolation quantified per asset; no hidden >5d holes; FX/XAU daily cohort
   structurally usable at D1 clock without any M1 pretense.

**Measured-NEGATIVE (gates proven shut, not merely untried):**
5. Expired outright months (self-built chain): 16/16 error 200 incl.
   `includeExpired=True` — no IBKR path, two resolution shapes.
6. ADJUSTED_LAST as certified chain: channel serves 6y but divergence vs TRADES
   is at most $1.73 (Brent) / $1.11 (WTI) / $0.057 (NG) over 6y — far below genuine
   roll-gap adjustment scale; roll rule still absent (ENERGY_ADJUSTED_ANALYSIS.json,
   generated by energy_adjusted_analysis.py).
7. XAG legal-browser paths: stooq "Access denied" in real browser; LBMA
   Cloudflare block in-browser. Both measured; no bypass attempted.
8. FRED fredgraph FX channel as a timely signal source: ≥3 business-day
   serving staleness at two observations (its historical cross-check value
   is unaffected).

**More data only (no gate motion):** CONTFUT details re-dump (D5), flat-by-
year quantification (refines F-1), D4 entitlement re-probe (technical
NOT_RUN — hung once, thread-guard failed on asyncio; prior PC12A FAIL stands
for energy; FX-spot live entitlement exists per the sixsource session's
measured erratum, external evidence, labeled).

## Availability evidence ledger (access-time)

| observation | at (UTC / ET) | result |
|---|---|---|
| IBKR HMDS BID D1, 4 spot/metals | 2026-10-01T02:52Z / 09-30 22:52 ET | closed 09-30 bar AND forming 10-01 (next fx day) both present |
| IBKR HMDS TRADES D1, 3 energy fronts | 2026-10-01T02:31Z / 09-30 22:31 ET | CLOSED 09-30 bar present (sessions closed 17:00 ET per d5 hours) |
| FRED fredgraph FX | 2026-10-01T01:25Z and 03:5xZ (both manifested) | series ends 2026-09-25 both times (≥3bd stale) |
| FRED fredgraph energy | same two manifested points | ends 2026-09-29 both times (1bd) |
| EIA v2 API | 2026-10-01T01:30Z (manifest) | RBRTE/RWTC/RNGWHHD through 2026-09-29 |
| ECB eurofxref hist | 2026-10-01T01:02Z (03:02 CEST) | fixing 2026-09-30 present (next-morning availability at access; single point) |
| ADJUSTED_LAST BRENT | 2026-10-01T02:51Z | forming 10-01 bar present (ICE 10-01 session in progress) |

Point-2 protocol (closes the closed-bar lag bracket): identical script
re-run on the next business day; PREPARED, not self-scheduled (owner or
successor cycle runs it; a scheduled self-firing IBKR connector was judged
outside this lane's authority).

## What still requires the owner (unchanged law, updated evidence)

Statement export (costs), PIT threshold freeze + availability declaration
(D-1b law), XAG archive naming (D-2 — browser paths now measured-blocked,
so options B/C or an owner manual download elsewhere), certified roll-chain
source + exchange subscriptions (D-4 — IBKR-only paths now measured
exhausted), XAU pin (D-6), successor registration (D-7; draft appended).
