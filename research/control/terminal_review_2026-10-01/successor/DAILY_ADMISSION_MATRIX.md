# DAILY_ADMISSION_MATRIX — PC12A successor daily-track admission analysis (PREPARATION ONLY)

**Status header — read first.** Admission analysis for the successor
daily-track cohort, prepared 2026-10-01 by the DAILY-TRACK admission
analyst. Read-only input survey plus this one output file. No scored runs,
no engine execution, no registry / eligibility / GO / ledger writes, no
network, no S1 touch, no purchases. Nothing here admits, raises, or
registers anything: **every candidate below remains BLOCKED until a
registered successor amendment carries it (lane D-7 / D-DAILY-9 below).**
Missing evidence is `NOT_RUN`, never inferred `PASS` (mission invariant).

## 0. The owner's framing, made operational

Two different questions, never to be merged:

- **SIGNAL-SIDE PRICE** — a daily series usable as a *decision input*
  (e.g. XAUUSD close feeding an FX rule, RBRTE feeding an oil-CAD gate).
  Requirements: measured span-complete price panel (or official archive)
  with provenance + a lawful availability class for the decision clock.
- **EXECUTABLE VEHICLE** — a thing we can *lawfully backtest fills and
  costs on* (FX-spot CASH for pairs; CMDTY spot for metals; a **certified
  futures chain** for energy). Requirements: frozen instrument identity,
  BID/ASK panel for fill simulation, measured or declared costs, and for
  futures a per-month history + declared roll/adjustment rule +
  entitlement.

An asset can be **signal-admitted while execution-blocked** (all three
energy names today). No eligibility upgrade anywhere in this file is
inferred from data existence: a PASS always carries its own citation.

**Verdict vocabulary (Matrix B):** `ADMITTABLE-AS` (signal inputs measured
AND execution vehicle executable-class; admission still requires owner
registration + declarations) · `SIGNAL-ONLY` (signal measured; the traded
vehicle's execution side is blocked) · `BLOCKED` (a required input series
or gate has no evidence on file).

## Citation key

- `@cbae7556` = branch `orca/pc12a-7asset-unblock-20261001`, commit
  `cbae7556`, directory
  `research/control/PC12A-7ASSET-DATA-UNBLOCK-2026-10-01/` (data lane
  session 2; read via `git show cbae7556:<path>`; the data lane owns this
  branch — nothing was written there by this analysis).
- `@87e65f00` = root checkout `main` @ `87e65f00acdf12a09720be72fce76ce8ed2d33bf`,
  directory `research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/ibkr_capability_probe_2026-09-30/`
  (plus `terminal_review_2026-10-01/` sibling artifacts cited inline).
- Corpus = `research/control/FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1/symbols/*.md`
  (committed root side).
- Eligibility = `…/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/eligibility/PORTFOLIO_ELIGIBILITY_1200.tsv@87e65f00`.
- Key sha256 anchors: NZDUSD aggregate `c681402b…`, USDCHF `7fbd3a80…`,
  XAUUSD `02445884…`, XAGUSD `492dfbc0…`
  (`IDENTITY_FREEZE_2026-09-30.json@87e65f00`, 12-file recipe per asset);
  XAU TD archive `49c2684e…` (same freeze, `xau_overlap_vs_td_archive`).
  Session-2 raw evidence files sha-pinned in `MANIFEST_IBKR_RO.json@cbae7556`
  (12/12) and `MANIFEST_RAW.json@cbae7556`.

---

## 1. MATRIX A — per symbol × 5 gates

Summary table; cell-by-cell evidence with citations follows.

| symbol | price | PIT availability | costs | vehicle / roll | coverage |
|---|---|---|---|---|---|
| **NZDUSD** | **PASS** | **NOT_RUN** (owner declaration pending; sub-evidence measured) | **NOT_RUN** (statement absent; spread MEASURED) | **PASS** (FX-spot CASH; roll n/a) | **PASS** |
| **USDCHF** | **PASS** | **NOT_RUN** (same class) | **NOT_RUN** (same) | **PASS** (FX-spot CASH; roll n/a) | **PASS** |
| **XAUUSD** | **PASS** | **NOT_RUN** (thresholds UNFROZEN; lag ASSUMED per freeze law) | **NOT_RUN** (statement absent; spread MEASURED) | **PASS** (CMDTY SMART; roll n/a) | **PASS** |
| **XAGUSD** | **PASS, panel-only** (research use gated by PIT FAIL) | **FAIL** (no archive; browser paths measured-blocked) | **NOT_RUN** (statement absent; spread MEASURED) | **PASS** (CMDTY SMART; roll n/a) | **PASS** (panel; no archive exists to cross-cover) |
| **BRENT** | signal **PASS** / execution **FAIL** | **NOT_RUN** (channel serving 1bd MEASURED; historical vintage availability unmeasured; adoption pending) | **NOT_RUN** (statement absent; front spread MEASURED-SAMPLE) | **FAIL** (chain not certified; entitlement FAIL) | signal **PASS** / CONTFUT panel **FAIL** pre-2025 |
| **WTI** | signal **PASS** / execution **FAIL** | **NOT_RUN** (same class as BRENT) | **NOT_RUN** (same; front spread MEASURED-SAMPLE) | **FAIL** (same class) | signal **PASS** / CONTFUT **FAIL** pre-2025 |
| **NATGAS** | signal **PASS** / execution **FAIL** | **NOT_RUN** (same class) | **NOT_RUN** (same; front spread MEASURED-SAMPLE) | **FAIL** (same class; AECO/TTF additionally non-IBKR) | signal **PASS** / CONTFUT **FAIL** pre-2025 |

### NZDUSD

- **price PASS** — IBKR HMDS D1 BID/ASK 1553 days/side, 2020-10-02→2026-09-30,
  0 holes >5d, max calendar gap 4d, DV-verified; aggregate sha `c681402b…`
  (`IDENTITY_FREEZE_2026-09-30.json@87e65f00` `assets.NZDUSD.panel_daily`,
  `aggregate.sha256`; `GATE_TABLE_V2_7ASSETS.md@cbae7556` row 1). Two free
  archives on file for cross-check (FRED H.10 DEXUSNZ, ECB cross).
- **PIT NOT_RUN** (no inferred PASS) — basis class `MEASURED_BASIS`
  (IBKR mid vs FRED p50 9.38 / ECB 21.52 bps;
  `XCHECK_REPORT.json@cbae7556` `overlaps`, `per_year_basis_abs_p50_bps`).
  Availability: same-evening closed-bar + forming next-fx-day bar
  **MEASURED point-1** at 2026-09-30 22:52 ET on BID
  (`AVAILABILITY_EVIDENCE.json@cbae7556` obs 1, source
  `d1b_spot_metals_bid_channel.json`, sha `5cde7f15…` @
  `MANIFEST_IBKR_RO.json@cbae7556`); next-day persistence
  `PREPARED_NOT_RUN` (point-2 protocol); IBKR historical-bar availability
  `LAG_NOT_MEASURED` (no vintages). FRED FX channel measured ≥3bd stale
  (2 manifested obs, ends 2026-09-25 at 2026-09-30ET retrieval;
  `FRED_STALENESS_POINT2.json@cbae7556` + `retrieval_staleness` in
  `XCHECK_REPORT.json@cbae7556`) → historical cross-check only, never a
  timely signal. Per amendment taxonomy
  (`DRAFT_AMENDMENT_SUCCESSOR.md@cbae7556` §2; lane OWNER_PACKET D-1c):
  honest PIT PASS only under an owner `LAG_DECLARED_BY_OWNER` declaration
  or a funded vintage measurement — **decision pending, so NOT_RUN**.
- **costs NOT_RUN** — spread **MEASURED** p50 0.88 / p90 18.65 / max
  239.07 bps over 1553d (`IDENTITY_FREEZE_2026-09-30.json@87e65f00`
  `assets.NZDUSD.spread_daily`); commission/swap/slippage
  `NOT_RUN_STATEMENT` (no IBKR Activity/Flex statement on file; lane D-5 /
  D-DAILY-4). After-cost evaluation gates stay fail-closed
  (`DRAFT_AMENDMENT_SUCCESSOR.md@cbae7556` §4).
- **vehicle PASS** — FX-spot CASH IDEALPRO, identity frozen as-reported
  (conId 39453441, NZD.USD, minTick 5e-05, US/Eastern); spot ⇒ roll/chain
  n/a (`IDENTITY_FREEZE_2026-09-30.json@87e65f00`
  `assets.NZDUSD.identity_as_reported`; F-4 as-reported caveat,
  `GATE_TABLE_7ASSETS.md@87e65f00`). Caveat carried, not a FAIL: live
  streaming entitlement for NZDUSD specifically was NOT directly measured
  (sixsource erratum measured the five majors only — external evidence,
  labeled; `AVAILABILITY_EVIDENCE.json@cbae7556` `channel_notes`).
- **coverage PASS** — archive cover of IBKR panel: FRED 96.01%, ECB
  98.71%; isolation days 1 (2022-12-26); longest covered streak 1552d;
  weekday histogram symmetric (`COVERAGE_REPORT.json@cbae7556`
  `assets.NZDUSD`). Intraday interior scans remain NOT_RUN (out of daily
  scope; `ERRATUM_LABELS_2026-09-30.md@87e65f00`).

### USDCHF

Identical shape; deltas only:

- **price PASS** — 1553 d/side, aggregate sha `7fbd3a80…`
  (`IDENTITY_FREEZE_2026-09-30.json@87e65f00` `assets.USDCHF`;
  `GATE_TABLE_V2_7ASSETS.md@cbae7556` row 2). ERRATUM-1 on record: FRED
  DEXSZUS needs no inversion (byte-proven 0.8286 vs 0.8278;
  `OWNER_PACKET.md@cbae7556` ERRATUM-1).
- **PIT NOT_RUN** — `MEASURED_BASIS` FRED p50 9.32 / ECB 18.43 bps;
  same-evening point-1 measured; same declaration-pending law as NZDUSD
  (`XCHECK_REPORT.json@cbae7556` `overlaps`;
  `AVAILABILITY_EVIDENCE.json@cbae7556` obs 1).
- **costs NOT_RUN** — spread MEASURED p50 4.51 / p90 16.02 / max 216.10
  bps; statement absent (`IDENTITY_FREEZE…assets.USDCHF.spread_daily`).
- **vehicle PASS** — CASH IDEALPRO conId 12087820 USD.CHF; roll n/a;
  same five-major entitlement caveat.
- **coverage PASS** — FRED 96.01% / ECB 98.71%, isolation 1 day,
  streak 1552 (`COVERAGE_REPORT.json@cbae7556` `assets.USDCHF`).

### XAUUSD

- **price PASS** — IBKR D1 BID/ASK 1544 d/side 2020-10-02→2026-09-30,
  0 holes, aggregate sha `02445884…` + TD archive cross-panel (1705d
  archive, 99.22% cover of panel) (`IDENTITY_FREEZE…assets.XAUUSD`;
  `COVERAGE_REPORT.json@cbae7556` `assets.XAUUSD`).
- **PIT NOT_RUN** — `MEASURED_BASIS`: TD overlap n=1531 (2020-10-02→
  2026-09-16), abs p50 3.2462 / p95 26.5142 bps, signed mean +0.3359 USD,
  exact-reproduced from IDENTITY_FREEZE and re-verified session 2
  (`XCHECK_REPORT.json@cbae7556` `overlaps`; `GATE_TABLE_V2…@cbae7556`
  row 3). But `pit_lag = ASSUMED_NEXT_BUSINESS_DAY`, `pit_status =
  NOT_MEASURED`, `basis_acceptance = NOT_RUN_THRESHOLDS_UNFROZEN`
  (`IDENTITY_FREEZE…xau_overlap_vs_td_archive`). Basis-acceptance law
  drafted in panel-σ units, XAU σ to be computed at freeze
  (`DRAFT_AMENDMENT_SUCCESSOR.md@cbae7556` §3; lane D-1b). Forming-bar
  point-1 measured with the FX four (`AVAILABILITY_EVIDENCE.json@cbae7556`
  obs 1). Canonical archive location unpinned (finding F-2; lane D-6 /
  D-DAILY-6).
- **costs NOT_RUN** — spread MEASURED p50 5.52 / p90 18.61 / max 74.17 bps
  (n=1543; one crossed-book day 2025-05-23 excluded by a≥b rule —
  disclosed, not smoothed); statement absent
  (`IDENTITY_FREEZE…assets.XAUUSD.spread_daily` + `spread_caveats`).
- **vehicle PASS** — CMDTY XAUUSD SMART USD "London Gold" conId 69067924,
  minTick 0.01, identity frozen as-reported; spot ⇒ roll n/a. Usable as
  the executable-venue exhibit in a future amendment, not an eligibility
  change today (`IDENTITY_FREEZE…assets.XAUUSD.identity_as_reported`;
  `GATE_TABLE_7ASSETS.md@87e65f00` §XAUUSD).
- **coverage PASS** — TD 99.22% cover; isolation days 12 (2025-04-15/16 +
  the 2026-09-17→09-30 tail, i.e. post-TD-archive-end); streak 1531d
  (`COVERAGE_REPORT.json@cbae7556` `assets.XAUUSD`). The 12-day tail is
  TD-coverage, not an IBKR panel hole.

### XAGUSD

- **price PASS, panel-only** — IBKR D1 BID/ASK 1544 d/side, aggregate sha
  `492dfbc0…` (`IDENTITY_FREEZE…assets.XAGUSD`); usable as panel only —
  the PIT gate blocks research use (`GATE_TABLE_V2_7ASSETS.md@cbae7556`
  row 4 labels the cell exactly this way).
- **PIT FAIL** — `FAIL_PIT_NO_ARCHIVE`: no independent spot-level archive
  reachable. Session-2 real-browser attempts measured-blocked: stooq
  served "Access denied" (13-byte body) to a real browser session; LBMA
  Cloudflare hard-block in-browser; TwelveData plan-blocked; SLV proxy
  r 0.9827 is proxy-class only
  (`XAG_BROWSER_ATTEMPTS_2026-10-01.json@cbae7556`, provenance class
  TRANSCRIPT_DERIVED_RECORD — bytes not captured at attempt time;
  `XCHECK_REPORT.json@cbae7556` `proxies`). Owner paths B/C or an owner
  manual drop from a different network/session remain (lane D-2 /
  D-DAILY-5).
- **costs NOT_RUN** — spread MEASURED p50 10.35 / p90 40.83 / max 162.81
  bps (widest p50 of the four — cost-gate relevant); statement absent
  (`IDENTITY_FREEZE…assets.XAGUSD.spread_daily`).
- **vehicle PASS** — CMDTY XAUUSD-family: XAGUSD SMART USD conId 77124483,
  minTick 0.0005, identity frozen; roll n/a. Note: **zero triage rows need
  only XAGUSD** (`GATE_TABLE_7ASSETS.md@87e65f00` §XAGUSD) — this vehicle
  is frozen for future cohorts, not for the 7 candidates.
- **coverage PASS (panel)** — daily panel structurally usable; archive
  cross-cover `n/a — no archive exists` (`COVERAGE_REPORT.json@cbae7556`
  `assets.XAGUSD`).

### BRENT (signal) / COIL futures (execution)

- **price: signal PASS / execution FAIL** — signal: EIA v2 RBRTE official
  daily, 1512d span-complete 2020-10-01→2026-09-29, 0 holes >5d,
  SINGLE-SOURCE-COMPILATION with DUAL-CHANNEL-RETRIEVAL-CONFIRMED FRED
  mirror (exactly equal at source precision 1511/1511 aligned dates, max
  abs diff 0.0 — retrieval confirmation, not verification)
  (`XCHECK_REPORT.json@cbae7556` `energy`, `mirror_value_equality`;
  `MANIFEST_RAW.json@cbae7556`; lane OWNER_PACKET D-3). Execution: no
  certified chain (vehicle cell below) ⇒ CONTFUT/ADJUSTED_LAST channels
  not admissible as an executable price series.
- **PIT NOT_RUN** — energy channel serving lag **1 business day
  MEASURED** (FRED mirror 2 manifested obs ending 2026-09-29 + EIA direct
  1 obs through 2026-09-29; `AVAILABILITY_EVIDENCE.json@cbae7556` obs 4/5;
  `COVERAGE_REPORT.json@cbae7556` `fred_serving_lag_observations`).
  ADJUSTED_LAST forming 10-01 bar present at 02:51Z (obs 7). Historical
  vintage availability of EIA series NOT_MEASURED; T+1-open usability is
  drafted, adoption is owner-gated (lane D-3 / D-DAILY-7) ⇒ NOT_RUN as a
  PIT PASS.
- **costs NOT_RUN** — front spread **MEASURED-SAMPLE**: COIL front p50
  12.60 / p90 32.95 / max 58.62 bps, n=29, last-30-D1-bars window to
  2026-09-30, **front-month quotes only** (`COVERAGE_REPORT.json@cbae7556`
  `measurable_cost_addendum.fronts.BRENT_COIL_front`; raw
  `d3_energy_front_bidask_30d.json` sha `8b3ddf43…` @
  `MANIFEST_IBKR_RO.json@cbae7556`). Commission/swap: NOT_RUN_STATEMENT.
  Sample label must stand until a longer pull lands
  (`DRAFT_AMENDMENT_SUCCESSOR.md@cbae7556` §4).
- **vehicle FAIL** — certified chain requires per-month FUT history +
  declared roll/adjustment rule + entitlement + costs. Measured-negative:
  (i) expired outright months 16/16 unresolved — `includeExpired=True`
  returned EMPTY contract details, prior probe shape error 200
  (`d2_expired_month_resolution.json` sha `03e689cf…` @
  `MANIFEST_IBKR_RO.json@cbae7556`; `ERRATUM_LABELS_2026-09-30.md@87e65f00`
  quarterly loop); (ii) ADJUSTED_LAST serves 6y but max abs divergence vs
  TRADES $1.73 over 6y — a genuine back-adjusted roll chain would diverge
  by tens of dollars ⇒ **NOT a certified chain**
  (`ENERGY_ADJUSTED_ANALYSIS.json@cbae7556` `assets.BRENT.adj_vs_trades`,
  generated by `energy_adjusted_analysis.py@cbae7556`); (iii) roll rule
  not exposed in contract details (`d5_contfut_details_rollcheck.json`
  sha `ee853636…`); (iv) entitlement FAIL (live 354 not subscribed;
  D4 re-probe technical NOT_RUN — hung worker, thread-guard failure;
  prior FAIL stands) (`AVAILABILITY_EVIDENCE.json@cbae7556`
  `channel_notes`; `GATE_TABLE_7ASSETS.md@87e65f00` §BRENT).
- **coverage: signal PASS / CONTFUT panel FAIL pre-2025** — EIA covers
  97.55% of CONTFUT days with 0 holes >5d as the signal calendar;
  CONTFUT itself is flat-OHLC-synthetic majority 2020–22 (100%), 95.3%
  2023, 57.9% 2024, 0% 2025+ (`COVERAGE_REPORT.json@cbae7556`
  `assets.BRENT`). Boundary discrepancy to fix at registration: the draft
  amendment text says CONTFUT "not admitted before 2023 (BRENT/WTI) /
  late-2022 (NATGAS)" while the session-2 skeptic round states the
  corrected boundary as 2025-01-01 / 2024-01-01
  (`DRAFT_AMENDMENT_SUCCESSOR.md@cbae7556` §5 vs
  `SESSION_REPORT.md@cbae7556` session-2 rev-2 item 4). The flat-by-year
  table is the measurement; the boundary sentence must be re-derived from
  it at registration (D-DAILY-9 carries this).

### WTI (signal) / CL futures (execution)

Same class as BRENT; deltas: signal EIA RWTC 1494d (mirror 1492/1492
equal); front spread CL p50 3.23 / p90 4.43 / max 5.02 bps n=30
(`COVERAGE_REPORT.json@cbae7556` `fronts.WTI_CL_front`); chain FAIL
identical 16/16 class; ADJUSTED_LAST max div $1.11, first divergence
2024-11-29 (`ENERGY_ADJUSTED_ANALYSIS.json@cbae7556`
  `assets.WTI.adj_vs_trades`); CONTFUT echoes front conId 304037511
  (CLX6) — single month, not a chain
  (`ERRATUM_LABELS_2026-09-30.md@87e65f00` CONTFUT table); EIA covers
  97.9% of CONTFUT days; flat 100% 2020-22 → 42.5% 2024 → 0% 2025+
  (`COVERAGE_REPORT.json@cbae7556` `assets.WTI`). Entitlement 10168 /
  no delayed quote (`GATE_TABLE_7ASSETS.md@87e65f00` §WTI).

### NATGAS (signal) / NG futures (execution)

Same class; deltas: signal EIA RNGWHHD 1496d — **first Henry-Hub archive
on file** (mirror 1496/1496 equal); front spread NG p50 6.54 / p90 7.02 /
max 10.05 bps n=30; ADJUSTED_LAST max div $0.057 (cents-scale), first
divergence 2021-11-22; EIA covers 98.03% of CONTFUT days; flat boundary
EARLIER: 100% 2020, 97.2% 2021, 87.4% 2022, 39.3% 2023, 0.4% 2024, 0%
2025+ (`COVERAGE_REPORT.json@cbae7556` `assets.NATGAS`;
`ENERGY_ADJUSTED_ANALYSIS.json@cbae7556` `assets.NATGAS`). CONTFUT
echoes front NGX26 conId 269460170; entitlement 354/10167
(`ERRATUM_LABELS…@87e65f00`; `GATE_TABLE_7ASSETS.md@87e65f00` §NATGAS).
AECO and TTF are **not IBKR instruments at all** — those legs need
owner-named gas-hub sources regardless of any IBKR chain decision.

---

## 2. MATRIX B — per candidate (the 7 NEW-DAILY-CANDIDATE rows)

Rows: `LEG_RESOLUTION_MATRIX.tsv@87e65f00` class NEW-DAILY-CANDIDATE
(lines 34/63/83/99/149/163/167); statuses `BLOCKED pending plan
amendment` — unchanged by this analysis. Corpus mechanisms cited from
`FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1/symbols/*.md`.

| # | candidate | signal inputs (Matrix-A row) | execution vehicle (Matrix-A row) | JOINT verdict | single missing item |
|---|---|---|---|---|---|
| 1 | **AUDUSD-S081** (I-STATARB, MULTIWEEK) | AUDUSD D1 (evidenced H1-staged panel) + **NZDUSD** D1 closes (row: price PASS, coverage PASS, PIT NOT_RUN-declaration-pending) | AUDUSD FX-spot (evidenced) + **NZDUSD FX-spot** (vehicle PASS) — 1:1 two-leg trade | **ADMITTABLE-AS** daily-track pair-trade candidate (pre-cost; future registered amendment) | Owner PIT availability declaration for the NZDUSD panel (lane D-1c) + registration (D-7); after-cost gates additionally fail-closed pending the statement (D-5) |
| 2 | **USDJPY-S063** (G-XASSET, MULTIWEEK) | USDJPY D1 (evidenced) + VIX (evidenced, G-PIT-V2) + **XAUUSD D1 close as SIGNAL** (row: price PASS, basis MEASURED, thresholds UNFROZEN) | **USDJPY FX-spot** — gold is NOT the traded vehicle | **ADMITTABLE-AS** — XAU used signal-side only | XAU cross-check law freeze (D-1b, σ-computed bar + exclusion-zone log) and canonical pin (D-6) + registration (D-7) |
| 3 | **AUDUSD-S100** (J-REGIME_OPT, DAILY) | VIX>30 (evidenced) + **XAUUSD 20d-high (SIGNAL)** + AUDUSD 20d-low (evidenced) | **AUDUSD FX-spot** — gold is NOT the traded vehicle | **ADMITTABLE-AS** — XAU signal-side only | Same as #2 |
| 4 | **USDJPY-S083** (I-STATARB, WEEKLY) | USDJPY D1 + 6 JPY-cross inputs; NZDJPY/CHFJPY **synthetic** = NZDUSD/USDCHF × USDJPY D1 closes (rows: NZDUSD & USDCHF price PASS, coverage PASS, PIT NOT_RUN-declaration-pending) | **USDJPY FX-spot** | **ADMITTABLE-AS** (basket-residual fade; synthetic crosses declared in the rule text) | Owner PIT availability declaration for NZDUSD+USDCHF panels (D-1c) + registration (D-7) |
| 5 | **EURUSD-S006** (A-TREND, MULTIWEEK) | 7 USD-pair 20d rank: 5 evidenced + **NZDUSD + USDCHF** D1 closes | **EURUSD FX-spot** | **ADMITTABLE-AS** | Same as #4 |
| 6 | **EURUSD-S061** (G-XASSET, DAILY) | 7-pair anti-USD basket regression, D1 closes (5 evidenced + NZDUSD + USDCHF) | **EURUSD FX-spot** | **ADMITTABLE-AS** | Same as #4 |
| 7 | **EURUSD-S085** (I-STATARB, MULTIWEEK) | Kalman hedge ratio vs 7-pair basket, D1 closes (5 evidenced + NZDUSD + USDCHF) | **EURUSD FX-spot** | **ADMITTABLE-AS** | Same as #4 |

Corpus mechanisms (for the successor rule text; all D1-close rules):

- S081: AUDNZD z(60d) > ±2 AND OU half-life <20d → long AUDUSD + short
  NZDUSD 1:1; close z=0.3, stop z>3, hold ≤ 2×half-life
  (`symbols/AUDUSD.md` S81). 2026 RBA/RBNZ divergence is the family's own
  named break risk — half-life filter mandatory.
- S063: VIX Δ5d > +4 AND z(USDJPY ret + β·gold ret) > 1.5σ → short USDJPY
  beta-weighted; exit VIX<20 (`symbols/USDJPY.md` S63).
- S100: VIX>30 + gold>20d-high + AUDUSD<20d-low within 2 days → exit
  longs / optional tight-stop short scalp (`symbols/AUDUSD.md` S100).
- S083: JPY-effective index from 6 crosses (EUR/AUD/NZD/CAD/CHF/GBP vs
  JPY); |z|>2 of USDJPY residual vs basket fit → fade 1 week, stop z>3
  (`symbols/USDJPY.md` S83).
- S006/S061/S085: 20d cross-sectional rank / basket-regression residual
  z(20d)>2 fade / Kalman adaptive ±2.5σ deviation fade
  (`symbols/EURUSD.md` S6, S61, S85).

**The signal-vs-vehicle note the owner asked for, stated plainly:**
USDJPY-S063 and AUDUSD-S100 use the **XAU daily close as a SIGNAL for an
FX-pair trade**. That is signal-admissible on the measured IBKR XAU
panel + TD cross-check *without XAUUSD being the executable vehicle of
the trade* — the trades are USDJPY / AUDUSD FX-spot. XAU's own
vehicle/cost caveats would bind only if a future rule traded gold
itself. Symmetrically, an energy name can price a signal (EIA archive)
while its futures vehicle stays execution-blocked (§4).

Family-history honesty items carried into any registration: rows 3–7 are
`FAMILY_HISTORY_NEGATIVE` and rows 2–7 `PRIOR_NOT_SCORED` at park
(`LEG_RESOLUTION_MATRIX.tsv@87e65f00`); none of that changes under
admission analysis — it is ancestor-label context under directive #2, and
the negative-close-first law stands.

---

## 3. EIA signal inputs — energy dailies as FX/metals-leg signals

The three official dailies — **RBRTE (Brent), RWTC (WTI), RNGWHHD (Henry
Hub)** — are span-complete 2020-10-01→2026-09-29, 0 holes >5d, sha-pinned
in `MANIFEST_RAW.json@cbae7556`, with channel serving lag **1 business
day MEASURED** (EIA direct 1 obs + FRED mirror 2 manifested obs; the
FRED FX ≥3bd staleness does NOT afflict the energy mirrors). Adoption
label if the owner takes D-3 Option A: `SINGLE-SOURCE-COMPILATION,
DUAL-CHANNEL-RETRIEVAL-CONFIRMED` — mirror equality is retrieval
confirmation, not verification (lane OWNER_PACKET D-3 correction of
wording). For a D1 clock this means: usable for **T+1-open** decisions
(`DRAFT_AMENDMENT_SUCCESSOR.md@cbae7556` §2), not same-day rules.

Corpus legs that could consume them (grep of
`PORTFOLIO_ELIGIBILITY_1200.tsv@87e65f00` for oil/energy-signal legs on
FX pairs; joint verdicts per this matrix's law):

**Newly data-addressable by the EIA dailies (the data lane's own list,
`GATE_TABLE_V2_7ASSETS.md@cbae7556` "genuinely opened" item 1):**

| leg | energy signal needed | traded vehicle | joint verdict | missing item |
|---|---|---|---|---|
| USDJPY-S065 (LNG/NATGAS exposure) | NATGAS 10d ret + Brent-flat filter → RNGWHHD + RBRTE | USDJPY FX-spot (evidenced) | **ADMITTABLE-AS** energy-signal daily candidate | D-3 adoption + registration (D-7); corpus discloses HH-as-JKM-proxy bias in-rule |
| USDCAD-S090 (NATGAS/WTI ratio break) | RNGWHHD / RWTC ratio | USDCAD FX-spot (evidenced H1-staged) | **ADMITTABLE-AS** | Same |
| EURUSD-S063 (TTF−Henry Hub EA shock) | Henry-Hub leg → RNGWHHD; **TTF leg NOT EIA** | EURUSD FX-spot (evidenced) | **BLOCKED** | Owner-named TTF source (non-IBKR, non-EIA; D-4-adjacent owner action) |

**Already signal-evidenced via G-PIT-V3 (Brent−WTI channel, frozen
weekly-Friday available_at rule; daily-clock consumers carry a
staleness-adaptation duty — `poolB/grouping/GROUPING_PROPOSAL.md@87e65f00`
note 8).** The EIA dailies offer these rows a *daily-clock channel with
measured 1bd serving* as an alternative or cross-check; swapping channels
re-freezes their staleness rule — owner action, not inference:

- USDCAD-S001, S008, S013, S017, S028, S063 (named signal-only WTI-daily
  consumers in `GATE_TABLE_7ASSETS.md@87e65f00` §WTI) — signal evidenced;
  verdict unchanged **ADMITTABLE-AS** on their existing evidenced panels;
  EIA adoption optional (D-DAILY-7 scope decision).
- USDJPY-S064 (Brent 20d ret ToT), USDCAD-S069 (Brent−WTI spread),
  EURUSD-S062 (Brent 3-day lead-lag — needs a *daily* oil clock the
  weekly-frozen G-PIT-V3 rule cannot serve), NZDUSD-S065 (oil-trend risk
  gate), USDCHF-S065 (oil-spike haven bid), GBPUSD-S068 (oil-CAD
  confirmation filter) — EIA-servable signal legs on evidenced or
  newly-measured pairs; verdict **ADMITTABLE-AS** conditional on D-3
  adoption + the traded pair's own Matrix-A gates (NZDUSD/USDCHF rows
  carry the declaration-pending PIT cell; GBPUSD/USDCAD/AUDUSD/USDJPY/
  EURUSD evidenced).

**Energy-signal legs the EIA dailies CANNOT clear (no inference):**

- USDCAD-S062, S081, S089 (USDCAD–WTI pairs trades with **short-WTI
  execution legs**) — WTI *signal* is measured (RWTC), but the traded
  vehicle includes WTI futures ⇒ **SIGNAL-ONLY / EXECUTION-BLOCKED**
  pending a certified chain (§4).
- USDCAD-S005 (CL1–CL6 curve), USDCAD-S098 (6M curve-slope regime) —
  need the **futures curve**, which a spot daily is not ⇒ **BLOCKED**
  on the chain (D-4).
- USDCAD-S084 (Brent lead-lag minute-scale) — needs intraday energy ⇒
  **BLOCKED** (daily archive structurally insufficient; M1 corpus
  NOT_RUN_SIZE_CAP).
- USDCAD-S065 (NATGAS AECO spill) — AECO is a non-IBKR, non-EIA hub ⇒
  **BLOCKED** on an owner-named AECO source.
- NZDUSD-S068 (dairy/oil ToT), EURUSD-S058 (OPEC+ event), USDCAD-S031
  (carry + oil hedge) — macro-PIT inputs unevidenced
  (`NEEDS_MACRO_PIT_UNEVIDENCED` in the eligibility row) ⇒ **BLOCKED**
  on those inputs; the oil leg alone is not the rule.

---

## 4. Futures execution-block statement (BRENT / WTI / NATGAS)

**Law.** A certified energy chain requires ALL of: (a) per-month FUT
history reaching the cohort window; (b) a declared roll + adjustment
rule; (c) exchange data entitlement; (d) measured or declared costs
across the chain. (Gate key: `GATE_TABLE_7ASSETS.md@87e65f00` §per-asset
chain/roll/entitlement/costs rows; amendment footer.)

**Today's measured state — every leg of that law fails or is absent:**

1. **Per-month history: FAIL.** Expired outright months 16/16 unresolved
   — `includeExpired=True` returns empty contract details; the prior
   probe's error-200 shape is the second negative resolution shape
   (`d2_expired_month_resolution.json` sha `03e689cf…` @
   `MANIFEST_IBKR_RO.json@cbae7556`). Self-built chain has no IBKR path.
2. **Roll/adjustment rule: FAIL.** Contract details expose no adjust*
   field (`d5_contfut_details_rollcheck.json` sha `ee853636…`);
   ADJUSTED_LAST serves 6y but diverges from TRADES by at most
   **$1.73 (BRENT) / $1.11 (WTI) / $0.057 (NATGAS)** over 6y — a genuine
   back-adjusted chain would diverge by tens of dollars ⇒ REJECTED_AS_CHAIN
   (`ENERGY_ADJUSTED_ANALYSIS.json@cbae7556`;
   `DRAFT_AMENDMENT_SUCCESSOR.md@cbae7556` §1 table row ADJUSTED_LAST).
3. **Entitlement: FAIL.** Live error 354/10168, delayed no positive
   quote; D4 re-probe technical NOT_RUN (hung worker; prior FAIL stands)
   (`GATE_TABLE_7ASSETS.md@87e65f00`; `AVAILABILITY_EVIDENCE.json@cbae7556`
   `channel_notes`).
4. **Costs: NOT_RUN.** Only front-month BID/ASK 29–30d SAMPLE exists
   (COIL 12.60 / CL 3.23 / NG 6.54 bps p50) — no chain-wide cost basis, no
   statement.

Additional disqualifier for any CONTFUT-based panel: flat-OHLC synthetic
majority pre-2025 (BRENT/WTI) / pre-2024 (NATGAS) per the flat-by-year
table (`COVERAGE_REPORT.json@cbae7556`).

**Consequence.** BRENT, WTI, NATGAS remain **EXECUTION-BLOCKED
regardless of signal admission**. Their EIA signal rows (§3) may feed
FX/metals-leg rules; no energy *vehicle* may be backtested for fills
lawfully today. This matches the frozen position: "no honest amendment
scope exists until the chain source is named" (`GATE_TABLE_7ASSETS.md@
87e65f00` §BRENT footer).

**Exactly what a certified chain would require (owner actions, one
line each):** name a licensed-vendor or exchange-direct back-adjusted
series with a *documented roll + adjustment rule* (IBKR API paths are
measured exhausted); enable the ICE (IPE) and/or NYMEX market-data
subscriptions on the account; export the Activity/Flex statement covering
futures commission/swap. The weaker fallback the owner may instead
declare: an owner-accepted CONTFUT convention with the synthetic-bar
disclosure carried in any number that survives — that is a declaration,
never a measurement.

---

## 5. Lawful reversible next steps (preparation for a FUTURE registered cycle; no scored cells)

Per admitted-symbol / candidate class, all reversible, none consuming
gates:

1. **Per-symbol join-contract config drafts** (NZDUSD, USDCHF, XAUUSD;
   XAGUSD pending D-2): pin panel-of-record = IBKR HMDS D1 BID/ASK by
   aggregate sha (`c681402b… / 7fbd3a80… / 02445884… / 492dfbc0…`),
   archives by manifest sha, roles per lane D-1a Option A. Draft-only —
   no freeze executes before registration.
2. **Engine daily-clock adapter spec** (paper, no code against scored
   paths): decision clock T+1-open after the 17:00 ET D1 close; consume
   only observables whose availability class ≥ decision clock (IBKR
   panel: same-evening measured point-1 + declared persistence after
   point-2; EIA energy: 1bd serving; ECB/FRED FX: cross-check only;
   FRED FX never T+1). Carries the `INTRADAY_FORMING_MEASURED /
   PERSISTENCE_NOT_RUN` label law from `AVAILABILITY_EVIDENCE.json@cbae7556`.
3. **Availability point-2 execution note**: the prepared identical D1b
   re-run next business day closes the persistence bracket; it is
   PREPARED_NOT_RUN and must be owner- or successor-cycle-executed
   (a self-firing IBKR connector was judged outside the lane's scope).
4. **PIT freeze drafts** in panel-σ units (abs p50 ≤ 1σ, p95 ≤ 5σ,
   |mean| ≤ 0.5σ; σ NZDUSD 64.64 / USDCHF 49.62 bps measured
   `XCHECK_REPORT.json@cbae7556` `panel_volatility`; XAU/XAG σ computed
   at freeze) with exclusion-zone logging and named corruption modes —
   text ready for D-1b, frozen only by the owner.
5. **Energy signal config drafts** for RBRTE/RWTC/RNGWHHD labeled
   `SINGLE-SOURCE-COMPILATION, DUAL-CHANNEL-RETRIEVAL-CONFIRMED`, sample
   labels on the 29–30d front spreads, plus the §3 consumer list with
   per-leg staleness-rule placeholders (T+1-open).
6. **Trial-ledger pre-registration skeleton** for the daily-track cohort
   (identity list, fold calendar ≈ 10×26w per RULE_SLATE §6 daily-cohort
   row, floors inherited) — labels only, zero scored rows.
7. **Corpus-to-config translation notes** for the 7 candidates (rule
   text quotes in §2), including the S083 synthetic-cross declaration
   and the S100 kill-switch (non-standalone) framing.

All of the above is marked: preparation for a future registered cycle;
nothing herein is an admission, a gate consumption, or a scored cell.

---

## 6. Owner decision list D-DAILY-1..n (each ONE action; exact evidence/declaration required)

| id | action | exact requirement |
|---|---|---|
| **D-DAILY-1** | Execute the prepared availability point-2 re-run | Identical D1b script, next business day; lands `last5` diff evidence closing the same-evening persistence bracket (`AVAILABILITY_EVIDENCE.json@cbae7556` `point2_protocol`) |
| **D-DAILY-2** | Freeze the cross-check gate law (lane D-1b) | Declare tripwire in panel-σ units (1σ/5σ/0.5σ or owner-altered multipliers), σ from `panel_volatility` + XAU/XAG σ computed at freeze; log measured distributions beside the bar with pass/fail per archive and named corruption modes (exclusion-zone logging) |
| **D-DAILY-3** | Declare availability semantics (lane D-1c) | For each consumed series, one of: `LAG_DECLARED_BY_OWNER (DECLARED, NOT MEASURED)` label, or fund a vintage/publish-timestamp measurement; fixes IBKR-panel PIT class for NZDUSD/USDCHF/XAUUSD/XAGUSD |
| **D-DAILY-4** | Export the IBKR Activity/Flex statement (lane D-5) | One export to `~/.my-quantitative-data/ibkr_statement/` covering NZDUSD/USDCHF/XAUUSD/XAGUSD commission + swap; converts cost cells from NOT_RUN_STATEMENT to measured; after-cost gates stay fail-closed until it lands |
| **D-DAILY-5** | XAGUSD source decision (lane D-2) | Browser paths are measured-blocked in this environment (stooq Access-denied, LBMA Cloudflare — `XAG_BROWSER_ATTEMPTS_2026-10-01.json@cbae7556`); choose: owner manual drop from a different network/session, or declare IBKR panel-of-record (Option B), or accept SLV proxy as cross-check (Option C, weakest). No row in the 7 candidates needs XAG, so silence keeps XAG fail-closed without blocking the cohort |
| **D-DAILY-6** | Pin the XAU archive canonical location (lane D-6) | Pin forex-ng6 staging path (sha `49c2684e…`) + manifested copy under a `research/control/` data home (recommended pin + copy) |
| **D-DAILY-7** | Adopt EIA energy dailies as signal-side archive (lane D-3 Option A) | Manifest-pinned admission of RBRTE/RWTC/RNGWHHD labeled `SINGLE-SOURCE-COMPILATION, DUAL-CHANNEL-RETRIEVAL-CONFIRMED`; activates §3 rows USDJPY-S065, USDCAD-S090 (+ optional daily-clock channel for the G-PIT-V3 consumers, whose staleness rule must then be re-frozen) |
| **D-DAILY-8** | Energy chain decision (lane D-4) — decide or explicitly keep blocked | Name licensed/exchange-direct back-adjusted chain source + documented roll/adjustment rule + enable ICE/NYMEX subscriptions, OR record the decision that energy execution stays BLOCKED (signal-only) — one action either way |
| **D-DAILY-9** | Register the successor daily-track cycle (lane D-7) | Register the amendment naming OWNER_PACKET v2 + GATE_UPDATE v2 + GATE_TABLE_V2 + frozen manifests + this matrix as preregistration inputs; at registration, correct the DRAFT_AMENDMENT §5 CONTFUT boundary sentence against the flat-by-year table (2023/late-2022 text vs 2025/2024 correction — discrepancy flagged in §1 BRENT coverage above); any GO is typed at that cycle's own gate |
| **D-DAILY-10** (hygiene, non-admission) | Rotate `EIA_API_KEY` | Standing INC-1 disclosure: one key echo into a local transcript, never committed; rotation recommended (lane OWNER_PACKET incident block) |

---

## Boundary compliance (this analysis)

Read-only except this one file
(`terminal_review_2026-10-01/successor/DAILY_ADMISSION_MATRIX.md`); data
lane branch never written (all lane evidence via `git show cbae7556:…`);
no network; no scored computation; no registry/eligibility/GO/ledger/
FAMILY_FAILURES write; S1 untouched; no orders, purchases, or keys. All
labels PASS / FAIL / NOT_RUN carry their own artifact citation; no PASS
was inferred from another cell's evidence.

— end of matrix —

## REV-3 DELTA (data lane @d722f5d5, integrated 2026-10-01 — read-only lane, laws inherited)

1. **Availability point-2 EXECUTED** (2026-10-01T04:00:32–34Z, Thu 00:00
   ET): the 2026-09-30 closed bar PERSISTED with closes landed on ALL 7
   instruments; forming 10-01 bar live on the 4 FX/metals. Class upgrades
   to **PERSISTENCE_PRESENCE_MEASURED_2pts** on the availability cells of
   Matrix A. **Value-stability across points stays NOT_MEASURED** (point-1
   stored dates only; point-2 landed closes — one future re-run closes the
   gap; `ibkr_point2_probe.py` ships in-repo, never self-scheduled).
2. **Energy TRADES forming-bar absence is a CHANNEL property** (10-01
   sessions were already open per d5 hours; ADJUSTED_LAST serves the
   forming bar) — NOT session closure; no closure inference drawn.
3. **Hard laws inherited verbatim** (HANDOFF_TO_PORTFOLIO_CHAT.md §Hard laws; also encoded in DRAFT_AMENDMENT_SUCCESSOR.md):
   proxies (SLV/GLD), CONTFUT (TRADES or ADJUSTED_LAST) and EIA spot are
   NEVER executable futures prices — signal-side/proxy only; CONTFUT not
   admissible as price evidence before 2025-01-01 (BRENT/WTI) /
   2024-01-01 (NATGAS); FRED FX is never a timely signal source (≥3bd
   measured — historical cross-check only); PIT PASS only under evidenced
   or DECLARED availability; pre-cost results are not survival evidence.
4. **XAG**: SGE (last lawful free candidate) serves HTML templates only —
   free-path verdict unchanged: MEASURED-BLOCKED on every lawful path.
5. **Standing headline: 0/7 fully admitted** — unchanged until OI-1
   (availability law), OI-2 (statement), OI-3/OI-4 (archives), OI-5
   (certified chain) resolve; per-gate cells above carry the detail.
6. Gate-delta table vs the 09-30 baseline and OI-1..OI-6 owner checklist:
   see the lane's HANDOFF_TO_PORTFOLIO_CHAT.md + OWNER_INPUT_CHECKLIST.md
   (branch orca/pc12a-7asset-unblock-20261001 @d722f5d5) — the checklist
   is now the OWNER_DECISION_TABLE's authority for data items.
