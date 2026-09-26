# Phase C1 — Data gate report — PWS-CX-BNBUSDT-C1 (BNBUSDT data plane)

- Cycle: `PWS-CX-BNBUSDT-C1` · Lane: PIT/DATA AUDITOR (`c1c2-data-pit`) ·
  Date: 2026-09-26.
- Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/pws-cx-bnbusdt-c1/integration`,
  branch `orca/pws-cx-bnbusdt-c1-integration`, start HEAD
  `363cf282d6f3b08b9c8d2f449debdb0e056cf49b`.
- Structure/rigor mirrors the frozen precedent
  `PWS-CX-SOLUSDT-C1/C1_data_gate_REPORT.md`. Every number below was
  **recomputed by this lane from raw bytes downloaded this cycle** (79 Vision
  zips, 2,711,409 bytes; one fapi paginated scan) — nothing on schema trust.
- All downloads: keyless public endpoints, polite pacing (1 s/zip, 0.5 s/fapi
  page).

## 0. Verdict table

| Component | Verdict | Evidence anchor |
|---|---|---|
| Klines corpus (Vision um 1h, 79 months) | **PASS** | 79/79 zips staged + sha256-manifested; 57,472 bars; 0 duplicate open times; ideal grid == actual grid (**0 missing bars, 0 gaps**); floor exact 2020-02-10T08:00Z |
| Funding series (fapi single scan) | **PASS WITH CAVEATS** | n=7,261, floor exact 2020-02-10T08:00Z, full distribution census computed; caveats: Vision cross-check NOT_RUN (no budget), scan extends past klines corpus end (tail beyond 2026-08-31 must be clipped by consumers), single-campaign source |
| Spread census (Vision bookTicker) | **NOT_RUN_DISK_CONSTRAINT** (fail-closed) | `df -g /` at dispatch start **and** at inventory build: 7 GB available (capacity 228 GB, used 17 GB, 70%) < 25 GB required by child plan §2.1. No download attempted. No substitution from any other pair's census. |
| License posture | **PASS** | Keyless Vision public archive + keyless fapi public endpoint; Binance Vision ToU pdf captured by SOLUSDT child, **cited by sha, not copied** (`94d6f61a39b5f821ef1d38f968aea1f2aa136e374f2061a2131db9a6af96bc3b`); no credentials anywhere in any artifact |

Gate conclusion: klines + funding planes are usable for cost-book and freeze
work **with the disclosed caveats binding**; the spread component is
NOT_RUN ⇒ **cost gate is fail-closed** (K-COST/BLOCKED for scored execution
per child plan §2.1/§C4): no scoring may proceed on a claimed measured
per-hour spread for BNBUSDT this cycle.

## 1. Klines corpus — PASS

Source: Binance Vision keyless public archive, futures/um monthly klines 1h
BNBUSDT, `data_local/vision/klines_um_BNBUSDT_1h/` (79 zips, 2,711,409 bytes
total, UNTRACKED; sha256 for every zip in `data_local/INVENTORY.md` and inside
the machine census + `klines_um_BNBUSDT_1h_MANIFEST.json`).

| Measure | Value |
|---|---|
| n_zips | 79 (2020-02 .. 2026-08) |
| 404s recorded | 2020-01 (pre-listing), 2026-09..2026-12 (current month not yet published / future months) — actual availability honestly recorded |
| total_bars | 57,472 |
| duplicate_open_times | 0 |
| first_open_utc | **2020-02-10T08:00:00Z** |
| last_open_utc | 2026-08-31T23:00:00Z |
| ideal_grid_bars | 57,472 |
| missing_bars_total | **0** |
| gaps | **none** |
| monthly_bars | 2020-02 = 472 (partial listing month: 08:00Z start), all later months = full 744/720 (leap-Feb 2024 = 696), 2026-08 = 744 |

- **Floor check: `floor_match: true`.** First bar 2020-02-10T08:00Z is the
  first full hourly bar after the 2020-02-10 listing (matches the DATACOST
  floor and the `ETHUSDT-OPEN-SEARCH-V2` registry-recorded BNB floor
  2020-02-10 independently).
- **Missing windows: NONE.** Unlike the SOLUSDT corpus (120 missing bars in
  two 2022 maintenance windows), the BNBUSDT 1h grid is gapless from listing
  to 2026-08-31T23:00Z. Bar-grid consumers need no gap policy inside the
  corpus window.
- Power-analysis input: 8,760 bars/year nominal (8,784 in leap 2024);
  57,472 bars over the 6.557-year listing-to-corpus-end span.

## 2. Funding series — PASS WITH CAVEATS

Source: Binance fapi `/fapi/v1/fundingRate`, single paginated keyless scan
2020-02-01 .. 2026-09-26T14:18Z (now), 8 pages × ≤1000 rows, raw saved at
`data_local/funding/fapi_scan_BNBUSDT_2026-09-26.json`
(sha256 `464da8832d53bf0454f286d8ef3566a357a69d93336de5aa5d2835876c0dc893`,
7,261 rows). Machine file:
`C1_machine_FUNDING_STATS_BNBUSDT.json`
(sha256 `853b4f4453290af46f1e3ac5dbb25365d9d084eea42042a58d60ed9d9a5c0e9d`).

### 2.1 Headline (rate in bps = rate × 1e4)

| Statistic | Value |
|---|---|
| n_settlements | 7,261 (0 duplicate fundingTimes) |
| first / last fundingTime | 2020-02-10T08:00:00Z / 2026-09-26T08:00:00.001Z |
| floor check | `floor_match: true` (first settlement = listing day 08:00Z, exactly co-incident with first 1h bar) |
| mean_rate | −3.776e-07 (**−0.00378 bps**/settlement) |
| median_rate | exactly 0 (3,601/7,261 = 49.6% of settlements are exact zeros) |
| sum_rate | −0.00274199 (**−27.42 bps** cumulative over 6.6 y — sign-flip-fair pair) |
| neg_share | 0.239361 |
| worst / max | **−0.00584369 (−58.44 bps)** at 2020-03-13T08:00Z (COVID crash) / **+0.00441898 (+44.19 bps)** at 2021-02-20T16:00Z |
| per-year n | 2020: 977 (partial) · 2021: 1,095 · 2022: 1,095 · 2023: 1,095 · 2024: 1,098 (leap) · 2025: 1,095 · 2026: 806 (through Sep 26) |

### 2.2 Interval-regime census (anomalous spacing)

**Zero non-8h spacings in the entire series.** Every one of the 7,260
settlement gaps is exactly 8h (±1 s ms-offset tolerance). BNBUSDT did **not**
receive the FTX-week emergency funding-interval increase that SOLUSDT shows
(101 anomalous spacings confined to 2022-11-09..18) — verified, disclosed as a
**pair-contrast fact**, not assumed. Consequence: nominal-8h path accounting is
valid for BNBUSDT as-measured; per-timestamp accounting remains the law
anyway (safety against future cadence changes after the capture date).

### 2.3 Distribution census for ceiling×power math (skeptic inputs)

Same-sign maximal-run census (consecutive settlements of one sign):

| Runs | length ≥3 | ≥5 | ≥8 | longest |
|---|---|---|---|---|
| positive | 187 | 108 | 64 | **63** (2024-11-19T00:00Z .. 2024-12-09T16:00Z ≈ 21 days of positive carry) |
| negative | 166 | 94 | 55 | **46** (2022-05-09T16:00Z .. 2022-05-24T16:00Z ≈ 15.3 days, LUNA window) |

Theta sweep — rolling mean of previous K=3 completed settlements (PIT), count
of settlements where mean ≥ +θ / ≤ −θ (θ in bps; of 7,258 evaluable):

| θ (bps) | pos-side triggers (share) | neg-side triggers (share) |
|---|---|---|
| 1 | 1,195 (16.46%) | 1,396 (19.23%) |
| 2 | 816 (11.24%) | 916 (12.62%) |
| 3 | 604 (8.32%) | 655 (9.02%) |
| 4 | 458 (6.31%) | 501 (6.90%) |

Both sides disclosed; negative-side triggers outnumber positive-side at every
θ (fat left tail of the 3-mean), while the cumulative mass is
sign-balanced (sum ≈ −27 bps over 6.6 y).

Deep-print census: **no capped |rate| prints at all** — zero settlements with
|rate| ≥ 75 bps, hence zero prints in the −200 bps clamp class; worst absolute
print is 58.44 bps. BNBUSDT funding has never hit its exchange clamp in the
measured window (contrast: SOLUSDT worst −200 bps inside FTX week).

Year-share of negative-payment mass (of total negative mass):
2020 25.50% · 2021 15.47% · 2022 20.22% · 2023 19.20% · 2024 14.26% ·
2025 5.29% · 2026 0.07% — negative mass is concentrated in 2020-2023 and has
nearly vanished in 2025-26 (relevant for any payer-side ceiling priced off
recent history).

### 2.4 Caveats (binding)

1. `cross_check_vision: NOT_RUN` — **kept NOT_RUN, not fabricated** (dispatch:
   no budget). The series is a single-campaign fapi scan; downstream must
   never describe it as dual-source verified. The conflict rule (any row diff
   ⇒ symbol-month EXCLUDED) stays armed if a Vision funding series is staged
   later.
2. **Scan tail**: the scan runs to 2026-09-26 (now) while the klines corpus
   ends 2026-08-31T23:00Z. Consumers evaluating on the corpus must clip
   funding to their evaluation window; the extra 26 days of settlements are
   measured and available but outside the staged price corpus.
3. 3,601 exact-zero settlements (49.6%) make the median exactly 0 — mean-based
   carry arithmetic must not be replaced by median reasoning.

## 3. Spread census — NOT_RUN_DISK_CONSTRAINT (fail-closed)

- `df -g /` recorded twice this cycle (dispatch start 21:14+07 and inventory
  build): Filesystem `/` capacity 228 GB, used 17 GB, **available 7 GB** —
  below the ≥25 GB precondition written in the child plan (§2.1; SOLUSDT
  precedent staged ~12 GB for a 6-month stratified sample).
- **No bookTicker bytes were downloaded.** The component is recorded
  `NOT_RUN_DISK_CONSTRAINT`, fail-closed: per-hour fill-spread for BNBUSDT is
  UNMEASURED this cycle; the cost gate may not consume a spread number, and
  **substituting another pair's census is forbidden** (child plan §2.1).
- BNB-specific note for any later re-run: SOLUSDT's keyless bookTicker
  availability (2023-05..2024-04 only) is a SOLUSDT archive fact; BNBUSDT
  availability was **not probed** (probing would only be useful once disk
  budget exists) — record `UNKNOWN`, not `BLOCKED_404`.

## 4. License posture — PASS

- Klines: Binance Vision keyless public archive; Terms of Use **captured by
  the SOLUSDT child** at
  `.worktrees/pws-cx-solusdt-c1/integration/research/control/PWS-CX-SOLUSDT-C1/licenses/Binance_Vision-Terms_of_Use.pdf`,
  sha256 `94d6f61a39b5f821ef1d38f968aea1f2aa136e374f2061a2131db9a6af96bc3b` —
  **cited here, deliberately not copied** (same source, same terms).
- Funding: fapi public endpoint `/fapi/v1/fundingRate`, keyless, captured
  2026-09-26 by this lane. No authenticated or paid source touched; no API key
  material exists in any artifact of this lane.

## 5. Power-analysis inputs (for trial sizing downstream)

| Quantity | Value |
|---|---|
| 1h bars total / per year | 57,472 / 8,760 nominal (gapless) |
| Funding settlements total / per year | 7,261 / 1,095 nominal strict-8h (measured: zero cadence anomalies) |
| Funding span | 2020-02-10T08:00Z .. 2026-09-26T08:00Z (6.627 y; clip to corpus end for joint use) |
| Spread samples | **0 — NOT_RUN_DISK_CONSTRAINT** |
| Same-sign run exposure | longest +63 / −46 settlements; 64/55 runs ≥8 |

## 6. Fail-closed items

- Spread census: **NOT_RUN_DISK_CONSTRAINT** (df evidence §3) — cost gate
  fail-closed for scored execution (child plan §C4 already encodes this).
- Funding Vision cross-check: **NOT_RUN** (no budget) — series stays
  single-campaign; conflict rule armed.
- BNBUSDT bookTicker archive availability: **UNKNOWN** (not probed; see §3).
- Machine-file audit note: the funding machine file's `sum_rate` field was
  corrected post-write after this lane caught a variable-clobber bug in its
  first computation (recomputed from raw scan bytes; the fix is recorded
  inside the machine file itself, `stats.overall._audit_note`). All other
  fields were unaffected (computed before the clobber).

## 7. Artifact sha256 table

| Artifact | sha256 |
|---|---|
| `C1_machine_KLINE_CENSUS_BNBUSDT.json` | `463d3083108c055c8b0a1f8e7f1e969c2dfbb0183ce3d567a96fd4c873d5e259` |
| `C1_machine_FUNDING_STATS_BNBUSDT.json` | `853b4f4453290af46f1e3ac5dbb25365d9d084eea42042a58d60ed9d9a5c0e9d` |
| `data_local/vision/klines_um_BNBUSDT_1h_MANIFEST.json` | `a9b3ec9b8c31ffc7ebbe70620381a1f8f17f0f4fd4339de75a1203c9d85bf176` |
| `data_local/funding/fapi_scan_BNBUSDT_2026-09-26.json` | `464da8832d53bf0454f286d8ef3566a357a69d93336de5aa5d2835876c0dc893` |
| `data_local/INVENTORY.md` (df evidence + all 79 zip shas) | `20616dd2f3387491b3e98686c6d6aa058e86e0ed10c0d50bf264076477b8866c` |
| `C2_EXPOSURE_VERIFICATION.md` | `dbb973a17ff2690ba9c4c27ba67326fdfa3227004428e7401f1fa51ebcbd7578` |
| Binance Vision ToU pdf (cited, SOLUSDT child path) | `94d6f61a39b5f821ef1d38f968aea1f2aa136e374f2061a2131db9a6af96bc3b` |

The 79 klines zips + funding scan JSON stay **UNTRACKED**
(`data_local/` never git-added); each byte-pinned in `data_local/INVENTORY.md`.

— Lane `c1c2-data-pit`, PIT/DATA AUDITOR, 2026-09-26.
