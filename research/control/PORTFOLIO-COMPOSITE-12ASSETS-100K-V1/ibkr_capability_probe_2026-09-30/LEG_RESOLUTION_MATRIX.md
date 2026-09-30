# LEG_RESOLUTION_MATRIX — 294 triage rows vs what the IBKR probe delivered

Lane DV, cycle PORTFOLIO-COMPOSITE-12ASSETS-100K-V1 (UNREGISTERED draft —
analysis only; no eligibility/registry write). Machine-readable companion:
`LEG_RESOLUTION_MATRIX.tsv` (294 rows, one per gid in
`poolB/grouping/mechanization_triage_292.tsv`, columns gid / symbol / family
/ horizon / tier / label / class / probe_assets / note).

## Classification law

Every one of the 294 EXPLORATORY_CANDIDATE rows was read against the probe's
deliverables (D1 BID/ASK on NZDUSD/USDCHF/XAUUSD/XAGUSD 2020-10-02→
2026-09-30; CONTFUT 6Y TRADES on COIL/CL/NG without roll rule; M1/H1 samples
only). Where the triage reason was insufficient, the corpus row
(`PORTFOLIO-ROUTER-12ASSETS-100K-V1/census/parts/census_*.tsv`:
`mechanism`, `signal_available_at`, `required_pit_data`) was read directly.

Classes:

- **(a) ALREADY-RUNNABLE — 150 rows, UNCHANGED.** The triage's T1 (75) +
  T2 (75). These run on the 5 evidenced pairs: INTRADAY-horizon runnable
  rows exist only on the 3 M1 pairs (EURUSD 8, GBPUSD 25, USDJPY 11); the
  AUDUSD/USDCAD runnable rows are DAILY+ horizons on staged H1 panels. The
  probe changes none of them. (Rows citing "WTI/Brent daily close evidenced
  G-PIT-V3" consume the existing PIT-dossier archive, not the probe's
  CONTFUT — F-1 shows why that must stay separate.)
- **(b) NEW-DAILY-CANDIDATE — 7 rows.** Rule computable on daily BID/ASK of
  the probed spot/metals (signal at D1 close, vehicle FX-spot, no intraday
  feature). **All 7 remain BLOCKED pending the plan amendment — NOT
  admitted; no leg's status is raised by this document** (identity-freeze
  header carries the same law).
- **(c) STILL-NOT_RUN — 128 rows.** The probe does not provide what the
  rule needs: M1/intraday granularity beyond samples, other FX pairs
  (SEK/NOK), equities/bonds/rates/gilts, commodities other than the 4
  probed (copper, iron ore), consensus/surprise vintages, news tags,
  positioning/OI/IV/risk-reversal series, or 5-second tick data.
- **(d) FUTURES-BLOCKED — 9 rows.** Need the BRENT/WTI/NATGAS tradable
  chain: futures curve (CL1–CL6, 6M slope), an execution leg (short WTI),
  or NATGAS/TTF/AECO prices. The probe's CONTFUT is not a certified chain
  (single-month localSymbol; CL/NG echo the front conId; expired FUT
  error 200; 41–63% flat-OHLC synthetic bars; no adjustment method).

## Counts

| class | rows |
|---|---|
| (a) ALREADY-RUNNABLE | **150** |
| (c) STILL-NOT_RUN | **128** |
| (b) NEW-DAILY-CANDIDATE (BLOCKED pending amendment) | **7** |
| (d) FUTURES-BLOCKED | **9** |
| total | 294 |

| symbol | (a) runnable | (b) new-daily | (c) still-not_run | (d) futures-blocked |
|---|---|---|---|---|
| EURUSD | 28 | 3 | 24 | 1 |
| GBPUSD | 49 | 0 | 31 | 0 |
| USDJPY | 27 | 2 | 21 | 1 |
| USDCAD | 24 | 0 | 21 | 7 |
| AUDUSD | 22 | 2 | 31 | 0 |

## (b) NEW-DAILY-CANDIDATE — named per probed asset (BLOCKED, do NOT admit)

| probed asset | triage rows whose missing input it covers |
|---|---|
| **NZDUSD** (D1) | AUDUSD-S081 (AUDNZD 60d z-band + OU; NZDUSD is both signal and execution leg) · EURUSD-S006 (7-pair anti-USD 20d rank) · EURUSD-S061 (6-pair basket-residual fade) · EURUSD-S085 (Kalman 7-pair hedge deviation) · USDJPY-S083 (6-cross JPY basket; NZDJPY derivable) |
| **USDCHF** (D1) | EURUSD-S006 · EURUSD-S061 · EURUSD-S085 · USDJPY-S083 (CHFJPY derivable) |
| **XAUUSD** (D1) | AUDUSD-S100 (VIX>30 + gold 20d-high + AUDUSD 20d-low tail switch) · USDJPY-S063 (gold–JPY safe-haven residual; VIX already evidenced) |
| **XAGUSD** (D1) | **none** — no triage row needs only silver. EURUSD-S068 names HG copper and its source explicitly flags the XAG proxy as unverified; it stays (c) unless the owner accepts the proxy (a corpus decision, not a probe delivery) |

Boundary rows that look metal/FX-adjacent but stay blocked (honesty list):
EURUSD-S082 (EURCHF now derivable from USDCHF, but the geopolitics news-tag
and SNB-absence inputs remain unevidenced) · GBPUSD-S067 and USDCAD-S064
(need S&P in addition to gold) · AUDUSD-S095 (XAU **and** SPX) · USDCAD-S070
(copper + gold) · AUDUSD-S007 / GBPUSD-S085 / USDJPY-S088 (also need
SEK/NOK).

## (d) FUTURES-BLOCKED — named per futures venue

| venue | rows |
|---|---|
| **WTI** | USDCAD-S005 (CL1–CL6 curve) · S062 (short-WTI execution leg) · S081 (cointegration execution leg) · S089 (S62 overlay) · S098 (6M slope) |
| **WTI + NATGAS** | USDCAD-S090 (ratio CUSUM) · EURUSD-S063 (TTF + Henry Hub; TTF not an IBKR-US instrument) |
| **NATGAS** | USDCAD-S065 (AECO additionally non-IBKR) |
| **NATGAS + BRENT** | USDJPY-S065 (Brent leg already evidenced G-PIT-V3; NATGAS chain absent) |

## Verification note

The 7 (b) rows and 9 (d) rows were assigned by reading the corpus row of
each (fields `mechanism` / `signal_available_at` / `required_pit_data`),
not by keyword alone; the (b) set is exactly the rows whose
`required_pit_data` reduces to D1 closes of {AUDUSD, EURUSD, USDJPY} plus
the probed pairs and nothing else. All other T3 rows keep their triage
reason as the (c) note, verbatim, prefixed "input not delivered by the
probe:". Reproducible from `LEG_RESOLUTION_MATRIX.tsv`.
