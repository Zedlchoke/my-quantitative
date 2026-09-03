# Z2 A7 — independent data-authority audit (STOCKS_FREE_V1)

Lane: `orca/stocks-free-v1-z2-a7-data`, bootstrap `5cf5577dd6a6214612a43eae78e15c2c67b57d2e`.
Access date for every probe below: **2026-09-03 (UTC)**. A7 recomputed every
decisive claim adversarially, in both directions, from this worktree. Raw probe
bodies stayed outside Git (PLAN 2); digests and short excerpts are recorded in
`independent_probes.json`.

## Verdict

```text
CONFIRM_BLOCKED
DATA_AUTHORIZATION_DENIED_BLOCKED_FREE_DATA_AUTHORITY
required closure: STOCKS_FREE_V1_BLOCKED_FREE_DATA_AUTHORITY
```

Zero HIGH/CRITICAL objections; launch condition (every required FD gate PASS)
cannot be met, so no authorization string is earned.

## 1. Decisive claims — independent results

| A1/A2 claim | A7 probe | result |
|---|---|---|
| stooq.com: JS SHA-256 PoW wall; fabricated 404s; no data/terms to non-browser clients | fresh curl of CSV endpoint, homepage, both terms candidates | **CONFIRMED byte-exactly**: 796 B PoW challenge (difficulty-4 hash loop visible in body) on CSV + homepage; both terms URLs 404 with body digest `03fa6d7ffcac…` identical to the lane captures |
| SSGA: terms URLs are JS SPA shells; license unjudgeable | curl with browser UA + tag-strip text measurement; adverse JS-rendering fetch | **CONFIRMED and STRENGTHENED**: `/us/en/intermediary/terms-of-use` → 133 072 B landing shell, digest `ec71ca1d…` byte-identical to lane capture, 0 occurrences of "terms"; `/legal/terms-of-use` → 47 211 B location-redirect shell, digest `c0641229…` byte-identical, 0 "terms"; even a JS-rendering fetcher receives only the **homepage** at the terms URL |
| SSGA XLSX remain freely downloadable, no account | fresh same-day re-download of navhist-SPY + distributions | **CONFIRMED**: HTTP 200, byte-identical sha256 to both lane pulls (three-way two-pull determinism) |
| Massive/NDL account-gated; Yahoo DIAGNOSTIC_ONLY; FRED cash-rate only | registry + captured terms review | **NOT CONTRADICTED** (see `verdict.json`) |
| no boundary-compliant cohort OHLCV source remains | adversarial missed-source sweep (below) | **CONFIRMED** |

**Adverse addition (MEDIUM objection).** The operative SSGA license sentence
*is* capturable by non-browser clients — it is embedded in the footer of every
downloaded workbook, including the staged files:
*"The whole or any part of this work may not be reproduced, copied or
transmitted or any of its contents disclosed to third parties without SSGA's
express written consent."*
It is adverse to FD0 item 3 (local storage / derived research): SSGA cannot
ground FD0 under the most favorable reading. The A2 registry's empty
`terms_excerpt` and "no terms text obtainable" narrative under-state this;
the block stands a fortiori, but the record is incomplete.

## 2. Missed-source sweep (task 2c) — no path to FD0 found

| candidate | probe result | disposition |
|---|---|---|
| iShares (BlackRock) price-history export | HTTP 200 but **2.2 MB HTML bot interstitial served with a fake Excel content-type**; not a zip/XLSX; terms candidate 404 SPA | bot-walled; files are close-level NAV/market-price anyway (no OHLCV/volume) |
| Invesco (QQQ product page) | **HTTP 406** to non-browser client | bot-walled; JS-gated downloads; same close-level limitation |
| Nasdaq public historical API | 200 JSON envelope, `totalRecords=0`, `rows=null`; Nasdaq terms prohibit extraction | no data served; license adverse |
| FRED SP500 | served no-account, but **close-only, rolling 10-year window** (head rolls off daily), index level, "Source: S&P DJI" citation without Public Domain marking | not cohort OHLCV; not deterministic 8y+ coverage |
| Vanguard price history | login-gated | account boundary |
| free-tier commercial APIs (Alpha Vantage, Tiingo, Finnhub, TwelveData, EODHD, Massive/NDL) | account + API key required | `EXCLUDED_ACCOUNT_REQUIRED` per PLAN 2 |
| SEC/EDGAR, exchange publications (NYSE/Cboe DataShop), Kaggle/GitHub mirrors | no daily ETF OHLCV / fee- or account-gated / not OFFICIAL (PLAN 4.1 item 1) | excluded by classification |

Structural fact confirmed: ETF issuers publish close-level NAV/market-price and
distribution records, never daily OHLCV; the big issuer download endpoints are
bot-walled; every OHLCV provider is account-gated or license-adverse.

## 3. Evidence integrity — recomputed

- A2 `checksum_manifest_staging.json`: **32/32** entries recomputed (sha256 +
  size) against `staging-data/stocks_free_v1_z1_a2/` — 0 missing, 0 mismatch.
- A3 declared digests (`ssga_download_evidence.json`): **4/4** match
  `staging-cohort/` files.
- Independent recomputation from the raw staged workbooks (own stdlib OOXML
  parser, not lane code): NAV 5 727 rows 2003-12-01..2026-09-01; 135 SPY
  distributions 1993-03-19..2026-06-18; 43 ex-dates missing from NAV, all
  pre-2003-12; SPY price-only growth **7.076299** and TR growth **10.742821**
  — **exactly** the declared values; 92 distributions applied. The declared
  `ordinary_dividend_sum_per_share` 111.37158 vs auditor 111.49158 is fully
  explained by the label being ordinary-only (auditor includes ST/LT gain
  columns).

## 4. Mandated read-only batteries — rerun from this worktree

```text
.venv/bin/python -m pytest tests/stocks_free_v1 -q            => 110 passed (exit 0)
.venv/bin/python -m pytest tests/assets/common tests/assets/stocks -q => 290 passed (exit 0)
```

Both counts match the FD gate records.

## 5. Objections

- **MEDIUM** — z1_a2 `source_evidence_registry.json` (SSGA entry): embedded
  workbook license text not recorded; FD0 rationale "no terms text obtainable"
  is partially inaccurate (see §1). Does not change the verdict direction.
- **LOW** — FD8 gate record `evidence_paths` holds a placeholder string
  ("logs to be attached on commit"), not a real path.
- **LOW** — z1_a2 README artifact table shows 11 of the 32 manifest files;
  manifest remains the complete record.

## 6. Why REFUTE_BLOCKED is impossible within the boundary

FD0 needs a zero-account source with proven terms covering cohort daily OHLCV.
Every candidate is (i) bot-walled (stooq, iShares, Invesco), (ii) license-
unprovable **and adverse** (SSGA), (iii) account-gated (Massive/NDL/all
free-tier APIs/Vanguard), (iv) diagnostic-only (Yahoo), or (v) wrong
instrument/window (FRED close-only rolling index). Breaking any leg requires
owner authorization (real-browser capture, account creation, or license
acceptance) — i.e., outside the frozen zero-cost boundary. Per PLAN 9 the
cycle must close `STOCKS_FREE_V1_BLOCKED_FREE_DATA_AUTHORITY` without
weakening gates and without proposals.

## Files

- `independent_probes.json` — machine-readable probe records (URLs, digests,
  byte counts, excerpts), sweep summary
- `verdict.json` — gate-by-gate A7 verdicts, objections, authorization string
