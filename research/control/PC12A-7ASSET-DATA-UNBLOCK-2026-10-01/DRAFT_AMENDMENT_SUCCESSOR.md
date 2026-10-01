# DRAFT_AMENDMENT_SUCCESSOR — daily-clock 7-asset data cohort (NOT registered)

**Status: DRAFT for the owner. Nothing here is registered, no cycle is
opened, no GO exists, no leg is admitted.** Registration is owner-only
(OWNER_PACKET v2 D-7). This draft turns the two data sessions' evidence into
the preregistration text a successor plan would carry. Written 2026-10-01 on
branch `orca/pc12a-7asset-unblock-20261001`.

## 0. Scope

One daily-clock (D1) cross-asset data cohort over the seven assets
NZDUSD, USDCHF, XAUUSD, XAGUSD, BRENT, WTI, NATGAS, window
2020-10-01..2026-09-30 (extendable forward), for the 7 triage rows of
LEG_RESOLUTION_MATRIX class (b) plus the energy signal-side legs
(USDJPY-S065 NATGAS+Brent, USDCAD-S090 NATGAS/WTI ratio, EURUSD-S063
Henry-Hub leg; TTF/AECO excluded). H1/M1 legs remain NOT_RUN and are NOT in
scope; futures execution legs remain BLOCKED (owner D-4) and are NOT in
scope.

## 1. Data contracts (all manifest-pinned, sha256)

| series | role | authority status |
|---|---|---|
| IBKR HMDS D1 BID/ASK (4 spot/metals, 131-file raw dir + identity freeze) | panel-of-record (execution-side simulation) | AUTHORIZED_INTERNAL_RESEARCH pending owner D-1 freeze |
| FRED H.10 DEXUSNZ/DEXSZUS | CROSS_CHECK archive (historical; channel lag ≥3bd — never a timely signal) | DOCUMENTED_CANDIDATE |
| ECB eurofxref crosses | CROSS_CHECK archive (calendar coverage 98.7%) | DOCUMENTED_CANDIDATE |
| TD XAUUSD archive (sha 49c2684e…) | CROSS_CHECK for XAUUSD (99.2% cover; canonical pin = owner D-6) | DOCUMENTED_CANDIDATE |
| EIA v2 RBRTE/RWTC/RNGWHHD (+ FRED mirror, retrieval-confirmed) | energy signal-side, SINGLE-SOURCE-COMPILATION label | DOCUMENTED_CANDIDATE (official channel) |
| SLV.US/GLD.US (EODHD, owner entitlement) | proxy-class second checks only — never panels-of-record | CANDIDATE_NOT_AUTHORIZED |
| IBKR ADJUSTED_LAST CONTFUT | NOT admitted: adjustment cents-level, roll rule absent (measured) | REJECTED_AS_CHAIN |
| XAGUSD independent archive | NONE — absent until owner D-2 resolves; note this environment's browser paths measured-blocked (XAG_BROWSER_ATTEMPTS record) — an owner drop must come from a different network/session | UNAVAILABLE_FAIL_CLOSED |

## 2. Availability protocol (per GATE_TABLE_V2 ledger)

- Execution panel (IBKR D1): same-evening closed-bar availability MEASURED
  (point-1: just-closed bars retrievable ~5.5h after close on all 7
  instruments; FX BID also served the forming next-fx-day bar); next-day
  persistence/stability bracket closes with the prepared point-2 re-run
  (owner/successor executes next business day). Until point-2 + owner
  declaration, panel availability carries
  `SAME_EVENING_MEASURED / PERSISTENCE_NOT_RUN (point-2 prepared)`.
- Signal archives: EIA energy = 1-business-day serving (EIA direct 1 obs;
  FRED mirror 2 manifested obs); ECB = next-morning at access (1 obs,
  stated schedule); FRED FX = HISTORICAL cross-check only — channel lag
  ≥3 business days (2 manifested obs) means it can never serve T+1 on any
  schedule in this environment.
- Any D1-close signal rule must use observables whose availability class is
  ≥ the decision clock (e.g. EIA energy usable for T+1-open decisions;
  ECB/FRED FX usable for T+1 only as cross-check). Rules needing same-day
  archives must state the DECLARED-NOT-MEASURED label explicitly.

## 3. Cross-check gate law (per OWNER_PACKET v2 D-1b, unchanged)

Tripwire in panel-volatility units: abs p50 ≤ 1σ AND abs p95 ≤ 5σ AND
|signed mean| ≤ 0.5σ (σ = panel daily-return σ: NZDUSD 64.64, USDCHF
49.62 bps; XAU/XAG σ to be computed at freeze). Exclusion-zone logging at
freeze: measured distributions beside the bar, pass/fail per archive stated
on the day of freezing. Substitute-panel role: FRED-only tight bars;
ECB fails tight bars → disclosed-secondary demotion, bar unmoved.

## 4. Cost floor (what the amendment may assume as measured)

Spreads measured: NZDUSD 0.88 / USDCHF 4.51 / XAUUSD 5.52 / XAGUSD 10.35
bps (6y daily); energy fronts 12.60 (COIL) / 3.23 (CL) / 6.54 (NG) bps
(29-30d SAMPLE — must be labeled sample until a longer pull lands).
Commission/swap/slippage: NOT_RUN_STATEMENT — all after-cost evaluation
gates stay fail-closed until the owner exports the IBKR Activity/Flex
statement (D-5). Pre-cost-only results are NOT admissible as survival
evidence.

## 5. Coverage laws

Daily cohort calendar = IBKR panel (FX/metals) with archive coverage
96.0-99.2%, isolation days ≤12, longest covered streak ≥1531 days; energy
signal calendar = EIA (0 holes >5d). CONTFUT panels are NOT admitted as
price evidence before 2023 (BRENT/WTI) / late-2022 (NATGAS) — flat-OHLC
synthetic majority per COVERAGE_REPORT flat-by-year table; the amendment
must cite it if any CONTFUT-dependent number survives.

## 6. Trial accounting, seals, GO

Every scored computation enters the trial ledger per owner law; S1 stays
SEALED_UNTOUCHED; GO phrase fresh at this cycle's own gate after A7
prelaunch (P-8). Successor registration, plan file location and budget are
owner decisions (D-7).

## 7. Owner decisions this draft depends on (one per line)

D-1 threshold freeze + availability declaration · D-2 XAG archive ·
D-3 energy signal-side adoption · D-4 chain source (out of scope here,
keeps execution legs blocked) · D-5 statement export · D-6 XAU pin ·
D-7 registration of this draft.
