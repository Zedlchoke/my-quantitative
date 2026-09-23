# P0 FEASIBILITY — CRYPTO-HISTORICAL-REPLICATION-3F-V1 (measured 2026-09-23)

All numbers below are MEASURED, not asserted. Raw probe artifacts in `p0_probe/`:
`vision_census_wave1.json`, `vision_census_wave2.json`, `fapi_depth_probe.json`,
`vision_fapi_wave3.json` (+ the probe scripts, read-only HEAD/GET, spaced
0.35s–1.3s; ≤8 fapi calls in wave2, ≤20 in wave3, chosen to respect the
shared-IP budget consumed by LIVE-DATA-GATEWAY-V1 / PROSPECTIVE-SHADOW-V1).

## 1. Dataset floors (measured)

| Dataset | Channel (replication primary) | Measured floor | Evidence artifact |
|---|---|---|---|
| klines 15m (close+quote_volume) | vision monthly zips (cross-check: fapi REST) | BTC/ETH/XRP/LINK/ADA/BCH 2020-01; BNB/ZEC 2020-02; DOGE 2020-07; SOL/AVAX 2020-09; AAVE/NEAR 2020-10; 1000PEPE/SUI 2023-05; WLD 2023-07; ONG 2023-11; ACE 2023-12; BOME 2024-03; ENA 2024-04 | wave2 `klines_15m_first_month_v2` |
| klines 15m fapi REST | (alternative channel) | serves 2019-09-09 for BTCUSDT (first row volume-0 padded) | wave2 `klines_btcusdt_20190909` |
| funding settlements | fapi `/fapi/v1/fundingRate` (V8/V11/V14 precedent channel) | **global floor 2020-07-18T08:00:00.001Z** (BTC/ETH/XRP/LINK/ADA/BNB/DOGE/BCH/ZEC all identical first settlement); per-listing floors after: SOL 2020-09-13, AVAX 2020-09-22, NEAR 2020-10-14, AAVE 2020-10-16; 2023+ listings as listed | wave3 `funding_earliest_by_symbol` |
| fundingRate vision monthly | cross-check only | archives from 2020-01 (BTCUSDT) | wave1 `btcusdt_fundingRate_monthly_first` + S3 key listing |
| basis 15m (`/futures/data/basis`, PERPETUAL) | primary for BASISLV (V14 frozen signal route) | BTCUSDT rows at 2020-06-01; **empty at 2019-11-25 (n=0)**; SOLUSDT rows at 2020-10-01; rows at 2024-08-22 (S0R head) | wave2 `basis_btcusdt_20200601`, wave3 `basis_btcusdt_20191125` |
| indexPriceKlines | fapi REST (cross-check for BASISLV) | BTCUSDT rows at 2020-06-01 | wave2 `indexPriceKlines_btcusdt_20200601` |
| markPriceKlines / indexPriceKlines vision monthly | cross-check | archives from 2020-01 (S3 key listing, BTCUSDT) | S3 XML listing 2026-09-23 |
| klines archive contiguity | spot check | 2020-06 / 2021-12 / 2023-06 / 2024-07 all HTTP 200 | wave3 `btcusdt_klines_month_spot` |

`onboardDate` (exchangeInfo, CURRENT metadata — corroboration only, never PIT
authority) matches every archive floor to the month. Measured beats stated;
the archive census is the PIT proxy, onboardDate only corroborates.

## 2. 2019 verdict: NOT_RUN for all three families

Measured reasons, any one of which is decisive under the frozen identities:
1. **Universe unsatisfiable**: um futures tradeable names from the frozen sets
   in 2019-Q4 = BTCUSDT (benchmark, excluded) + ETHUSDT + BCHUSDT ≤ 2 names.
   ILLIQ needs ≥10 eligible, BASISLV ≥12, XSECT all 7 (DOGE lists 2020-07,
   SOL 2020-09). (wave2 census + exchangeInfo)
2. **Funding floor 2020-07-18** — no settled funding exists earlier on the
   authorized channel. (wave3)
3. **Basis endpoint empty at 2019-11** — BASISLV signal unavailable. (wave3)

Earliest feasible dates are in §3 below. 2019 must not be described as run,
failed, or blocked-on-a-single-cause: it is `NOT_RUN_DATA` +
`NOT_RUN_IDENTITY_UNIVERSE` with the three causes above.

## 3. Per-family earliest feasible envelope (frozen law applied to measured floors)

Warmup/floors applied per frozen engine constants; final stamp-level proof is
the P0 full census (post-registration), which can only move starts LATER, and
if any scheduled stamp fails eligibility that partial fold becomes
`NOT_RUN_IDENTITY` with the failing stamps listed.

| Family | Binding constraints | Earliest full-year fold | Earliest partial fold (conditional) |
|---|---|---|---|
| XSECT-FUND-CARRY-7D (7 symbols) | all-7 listed (SOL 2020-09-14) + funding floor 2020-07-18 + 7d settled-funding mean warmup | 2021 | 2020-10-05..2020-12-31 |
| ILLIQ-AMIHUD-28D-W (20 staged symbols, BTC excluded) | ≥10 eligible after 28d listing-age formation filter (AVAX 2020-10-21 aged, SOL 2020-10-12 aged; 8 older names) + funding floor | 2021 | 2020-10-26..2020-12-31 |
| BASISLV-PREMFADE-28D (19 staged symbols, BTC excluded) | ≥12 eligible (AAVE aged 2020-11-13, NEAR aged 2020-11-12 reach 12) + funding floor + basis floor (≥2020-06 measured) | 2021 | 2020-11-16..2020-12-31 |

By 2021-01 every fold month satisfies universe floors for all three families;
2024 partial capped at **2024-08-19T00:00Z** so the replication never overlaps
the authorized/staged windows starting 2024-08-20 (V12 A3 non-overlap law).
2024-08-20..2026-08-21 is OUT OF SCOPE for this cycle.

## 4. Acquisition cost estimate (for the resource plan; light lock etiquette)

- 15m klines: 20 symbols × ~56 months ≈ 1,100 vision zips ≈ 2–3 GB, CDN
  static (no fapi weight), paced, sha256 per file.
- Funding: 20 symbols paginated fapi REST (data/derivatives.py precedent),
  ≤1000 rows/page ≈ 60–80 calls/symbol-year worst case; pacing law ≤6 req/min
  with yielding; total small.
- Basis 15m: ~4.5y × 96 buckets/day × 19 symbols ≈ 3.2M rows via
  `/futures/data/basis` paging (limit 500) ≈ 6.4k calls → at ≤6/min ≈ 18h
  wall clock under heavy lock with etiquette windows. Cross-check with vision
  indexPriceKlines monthly zips (bulk, cheap).
- V14 staged-basis byte-equality re-check: restage 2025-06-30..2026-08-21 and
  sha256-compare against `staged_basis_manifest.json` (3867bdca…) before any
  equivalence run.

## 5. Honest gaps / open items

- Exact basis-availability start between 2019-11-25 and 2020-06-01 not yet
  bracketed (irrelevant if all folds start ≥2020-10; bracket anyway in the
  full census).
- vision 2020-01..2020-06 fundingRate zips exist while fapi shows no
  settlements before 2020-07-18 → conflict policy frozen fail-closed: fapi is
  primary; if vision cross-check shows settlements fapi lacks, the affected
  window becomes `BLOCKED_DATA` resolution pre-PnL (no silent merge).
- V11 staged snapshot, V14 staged basis parquets, V6
  `results/portfolio_v6/*` and the two backup tarballs that held them are
  DELETED from disk (manifests survive). Equivalence strategy per plan §5.
