# ES Fee Sources — Public-Reference Component & Tier Table (Lane D2-FEESRC)

Cycle: FUTURES-DATACONTRACT-QUAL-V1 · Lane: D2-FEESRC · Run date: 2026-10-03
Access session (UTC): ~07:55–08:10 · Worktree: `prep/futures-behavior-10syms-20261002` @ `73abf15c` (no commits)

**Framing: MODELED_COST.** Everything below comes from PUBLIC fee-schedule sources. Nothing
is a measured cost from any account. **D2 account verification is NOT_RUN**; the Co-Owner is
obtaining redacted account documentation separately. **Every row: SOURCE=PUBLIC_REFERENCE,
VERIFIED_VS_ACCOUNT=NOT_RUN.** Public sources are REFERENCE ONLY — nothing here states or
implies account documentation has been seen. **D6 market-data re-fetch does NOT substitute
for account fee evidence** (D6 covers data-plane freshness, not fees).

Owner boundary update (mid-run, applied): the table maps onto IBKR's published pricing-plan
structure (Fixed vs Tiered x monthly volume tiers); the account's actual plan/tier is UNKNOWN,
so all plan/tier variants are enumerated and none is picked as "the" fee.

---

## 1. Method

1. Attempt the normal public routes for each source: WebFetch and mcp web_reader; record
   every status honestly (including 403 / timeout / network-500).
2. Keep only verbatim-extractable numbers; label each source
   LIVE_OFFICIAL / ARCHIVED_OFFICIAL / PUBLIC_MIRROR with URL + access date.
3. No inference: where a PDF's text extraction cannot bind values to columns, the document is
   recorded but no per-cell value is asserted.
4. Historical availability (2010–2026) decided by obtainability evidence only
   (dated official PDFs on live host + Wayback availability-API probes); where nothing
   year-specific is obtainable, the year is marked CURRENT_SCHEDULE_AS_APPROXIMATION and no
   past fee is inferred.

## 2. Attempt log (all routes tried)

| # | Target | Route | Result |
|---|--------|-------|--------|
| 1 | IBKR `commissions-futures.php` | WebFetch | **HTTP 403** (x2 — consistent with prior cycle measurement) |
| 2 | IBKR `commissions-futures.php` | web_reader | **SUCCESS, full render** (x2, incl. no_cache) |
| 3 | CME `company/fees.html` | WebFetch | timeout 60s |
| 4 | CME `company/fees.html`, `trading/fees/` | web_reader | network-500 (x3) — CME live HTML unreachable via all routes |
| 5 | CME `company/files/cme-fee-schedule-2025-02-01.pdf` | WebFetch | timeout 60s |
| 6 | CME dated PDFs 2025-02-01 / 2020-10-01 / 2026-02-01 | web_reader | **SUCCESS** (official PDFs on live host) |
| 7 | CME dated PDFs 2010-06-01 / 2015-12-01 (guessed names) | web_reader | network-500 (x2; not evidence of nonexistence) |
| 8 | TradeStation exchange-fees page | WebFetch | HTTP 403 |
| 9 | TradeStation exchange-fees page | web_reader | **SUCCESS** (public mirror) |
| 10 | IBKR `accounts/fees/CME.php` | web_reader | **SUCCESS** (official per-product pass-through table) |
| 11 | NFA Bylaw-1301 CFTC filing PDF | web_reader | **SUCCESS** (official fee timeline) |
| 12 | `web.archive.org/cdx` (IBKR/CME URLs) | WebFetch | connect timeout (x2) |
| 13 | `web.archive.org/cdx` | web_reader | network-500 (x3) — Wayback CDX/direct fetch blocked this session |
| 14 | `archive.org/wayback/available` (9 exact-URL probes) | WebFetch | **SUCCESS** (availability facts only; see §5) |
| 15 | WebSearch (CME ES fee, NFA fee, IBKR PDFs) | WebSearch | leads only — surfaced S2/S5/S6; the search summarizer's "$1.55" claim appears in NO fetched source and is NOT adopted |

## 3. Source register

| ID | Provenance | Publisher / what | URL | Access (UTC) | Status |
|----|-----------|------------------|-----|--------------|--------|
| S1 | LIVE_OFFICIAL | IBKR public futures commissions page (tier table + ES worked examples) | https://www.interactivebrokers.com/en/pricing/commissions-futures.php?re=amer | 2026-10-03 ~08:01 | FETCHED_FULL |
| S2 | LIVE_OFFICIAL | IBKR "Fees Charged to Offset CME (Electronic-Globex) Exchange and Regulatory Fees Paid by IBKR" (per-product; ES 1.386 / 0.011) | https://www.interactivebrokers.com/en/accounts/fees/CME.php | 2026-10-03 ~08:07 | FETCHED_FULL |
| S3 | LIVE_OFFICIAL | CME Fee Schedule PDF, effective 2025-02-01 (equity section incl. E-mini Equity Index) | https://www.cmegroup.com/company/files/cme-fee-schedule-2025-02-01.pdf | 2026-10-03 ~07:58 | fetched; per-cell values NOT extractable (column scrambling) |
| S4a | LIVE_OFFICIAL (dated file on live host) | CME Fee Schedule PDF, effective 2020-10-01 | https://www.cmegroup.com/company/files/cme-fee-schedule-2020-10-01.pdf | 2026-10-03 ~08:00 | fetched; same extraction limit |
| S4b | LIVE_OFFICIAL (dated file on live host) | CME Fee Schedule PDF, effective 2026-02-01 | https://www.cmegroup.com/company/files/cme-fee-schedule-2026-02-01.pdf | 2026-10-03 ~08:00 | fetched; same extraction limit |
| S5 | LIVE_OFFICIAL | NFA Bylaw 1301 filing to CFTC (2017-11-17): NFA assessment-fee timeline | https://www.nfa.futures.org/news/PDF/CFTC/2010-2019/20171117-Bylaw-1301-FCM-Assessment-Fee-Increase.pdf | 2026-10-03 ~08:07 | FETCHED_FULL |
| S6 | PUBLIC_MIRROR | TradeStation public exchange-fee table (non-member; ES $1.38/side) | https://www.tradestation.com/pricing/exchange-execution-and-clearing-fees/ | 2026-10-03 ~08:05 | FETCHED_FULL; no fee effective date on page |
| S7 | ARCHIVED_OFFICIAL (prior extraction) | Prior cycle fetch of S1 page, 2026-10-02T01:28:41Z | file: `research/control/FUTURES-DATA-10SYMS-V1/costs/IBKR_futures_commissions_2026-10-02.json` (root checkout) | read 2026-10-03 08:09 | READ; ES all-in 2.24 stays DOC_EXAMPLE_NOT_ACCOUNT_VERIFIED |

## 4. ES component & tier table (USD, per contract, per side)

### 4.1 IBKR commission by plan/tier (S1, verbatim)

Plan structure as published: **two variants — "Tiered" and "Fixed."** No Lite/Pro-specific
futures commission table appears in the fetched page text (Lite/Pro does not add a third
futures fee table on that page). Tiers = monthly cumulative contracts across ALL futures/FOPs
regardless of exchange, applied **marginally**.

| Row | Plan | Monthly volume tier (contracts) | IBKR execution fee | Plan add-ons (as published) | SOURCE | VERIFIED_VS_ACCOUNT |
|-----|------|--------------------------------|--------------------|------------------------------|--------|---------------------|
| C1 | Tiered | ≤ 1,000 | **0.85** | + Exchange Fees + Regulatory Fees + Overnight Position Fees | PUBLIC_REFERENCE (S1) | NOT_RUN |
| C2 | Tiered | 1,001–10,000 | **0.65** | same | PUBLIC_REFERENCE (S1) | NOT_RUN |
| C3 | Tiered | 10,001–20,000 | **0.45** | same | PUBLIC_REFERENCE (S1) | NOT_RUN |
| C4 | Tiered | > 20,000 | **0.25** | same | PUBLIC_REFERENCE (S1) | NOT_RUN |
| C5 | Fixed | no volume tiers published | **0.85** | + Exchange Fees + Regulatory Fees | PUBLIC_REFERENCE (S1) | NOT_RUN |

The account's actual plan/tier is UNKNOWN; all variants enumerated, none selected.

### 4.2 Exchange / regulatory / clearing components

| Row | Component | Value | Published by | Bundled vs pass-through | SOURCE | VERIFIED_VS_ACCOUNT |
|-----|-----------|-------|--------------|-------------------------|--------|---------------------|
| X1 | Exchange (CME Globex, ES futures, non-member regular) | **1.386** | IBKR offset table | PASS-THROUGH OFFSET ("fee to offset exchange and regulatory fees paid by IBKR"; tiered-plan footnote: not a direct pass-through, can exceed IBKR's costs) | PUBLIC_REFERENCE (S2) | NOT_RUN |
| X1m | Exchange — mirror cross-reference | **1.38** | TradeStation (non-member; execution+clearing combined column) | exchange pass-through as presented by mirror | PUBLIC_REFERENCE (S6) | NOT_RUN |
| X1o | Exchange — official CME tariff cell | **no value asserted** | CME fee-schedule PDFs obtained (eff. 2020-10-01 / 2025-02-01 / 2026-02-01) | official tariff; per-cell extraction unreliable → no inference | PUBLIC_REFERENCE (S3/S4) | NOT_RUN |
| X2 | Regulatory (NFA assessment etc., ES, non-member regular) | **0.011** | IBKR offset table | PASS-THROUGH OFFSET | PUBLIC_REFERENCE (S2) | NOT_RUN |
| X2n | NFA assessment (official timeline) | **0.02** → **0.01** (2014-10-01) → **0.02** (2018-01-01) | NFA CFTC filing | regulatory assessment collected by FCM; post-2018 changes not covered by any official doc fetched (open item) | PUBLIC_REFERENCE (S5) | NOT_RUN |
| X3 | Clearing | **0.00** (per IBKR ES example line) | IBKR worked example | separate zero line; TradeStation folds clearing into its 1.38 | PUBLIC_REFERENCE (S1) | NOT_RUN |
| X4 | Overnight Position Fee (Tiered plan only) | **NOT_FETCHED** (JS tables never rendered) | IBKR | add-on unique to Tiered; amount unknown | PUBLIC_REFERENCE (S1, availability noted) | NOT_RUN |

### 4.3 Worked examples / modeled all-in (single side, ≤1,000 tier)

| Row | Label | Plan | Expression | USD | SOURCE | VERIFIED_VS_ACCOUNT |
|-----|-------|------|------------|-----|--------|---------------------|
| E1 | DOC_EXAMPLE_NOT_ACCOUNT_VERIFIED | Tiered | verbatim: "0.85 + Exchange 1.38 + Clearing 0.00 + Regulatory 0.00 = USD 2.24" (printed total; components as printed sum to 2.23 — recorded as printed) | **2.24** (as printed) | PUBLIC_REFERENCE (S1) | NOT_RUN |
| E2 | DOC_EXAMPLE_NOT_ACCOUNT_VERIFIED | Fixed | verbatim: "0.85 + Exchange 1.38 + Clearing 0.00 + Regulatory 0.01 = USD 2.24" | **2.24** | PUBLIC_REFERENCE (S1) | NOT_RUN |
| E3 | COMPUTED_FROM_PUBLIC_COMPONENTS | Tiered ≤1k / Fixed | 0.85 (S1) + 1.386 (S2) + 0.011 (S2) | **2.247** | PUBLIC_REFERENCE (S1+S2) | NOT_RUN |
| E4 | MODELED_COST per plan | all tiers | 2.247 (≤1k, both plans); 2.047 / 1.847 / 1.647 at tiers 2/3/4 (execution 0.65/0.45/0.25 + same components) | see col. left | PUBLIC_REFERENCE (S1+S2) | NOT_RUN |

Round-trip = 2 x single side under this framing. Overnight Position Fee excluded (NOT_FETCHED).
Spread/implied/BTIC/EFP order types carry different published offsets (S2 rows listed in the JSON).

## 5. Historical availability 2010–2026 (availability only; no past fee inferred)

Wayback CDX/direct snapshot fetch was BLOCKED this session (WebFetch connect-timeout;
web_reader network-500). The lightweight `archive.org/wayback/available` API worked
(exact-URL, closest-snapshot) and is the probe channel. Probe results verbatim:

- IBKR `/en/pricing/commissions-futures.php`: @2010 → empty; @2021-06 → closest **2022-01-19** (200);
  @2022 → **2022-01-19** (200); @2023 → **2023-03-25** (200); @2025 → **2025-05-28** (200). Live 2026.
- IBKR old URL `/en/p.php?f=commissions`: @2010, @2015 → empty (exact-URL only).
- IBKR `/en/accounts/fees/CME.php`: @2012 → snapshot **2008-06-21** (200) (pre-scope; content not fetched).
- CME `/company/fees.html`: @2010, @2015 → empty (exact-URL only).

| Year | IBKR commission page | CME exchange schedule | NFA fee |
|------|----------------------|------------------------|---------|
| 2010 | NOT_FOUND_via_probe → approximation needed | NOT_CONFIRMED → approximation needed | official (0.02) |
| 2011 | NOT_FOUND_via_probe → approximation | NOT_CONFIRMED → approximation | official (0.02) |
| 2012 | NOT_FOUND_via_probe → approximation | NOT_CONFIRMED → approximation | official (0.02) |
| 2013 | NOT_FOUND_via_probe → approximation | NOT_CONFIRMED → approximation | official (0.02) |
| 2014 | NOT_FOUND_via_probe → approximation | NOT_CONFIRMED → approximation | official (0.02 → 0.01 @10-01) |
| 2015 | NOT_FOUND_via_probe → approximation | NOT_CONFIRMED → approximation | official (0.01) |
| 2016 | NOT_PROBED → approximation | NOT_CONFIRMED → approximation | official (0.01) |
| 2017 | NOT_PROBED → approximation | NOT_CONFIRMED → approximation | official (0.01) |
| 2018 | NOT_PROBED → approximation | NOT_CONFIRMED → approximation | official (0.02 @01-01, last official doc fetched) |
| 2019 | NOT_PROBED → approximation | NOT_CONFIRMED → approximation | partial-official |
| 2020 | NOT_PROBED (nothing nearer than 2022 found) → approximation | **AVAILABLE** (official PDF eff. 2020-10-01, fetched; cells not extractable) | partial-official |
| 2021 | NOT_FOUND_via_probe → approximation | NOT_CONFIRMED → approximation | partial-official |
| 2022 | **AVAILABLE** (Wayback 2022-01-19, content not fetched) | NOT_CONFIRMED → approximation | partial-official |
| 2023 | **AVAILABLE** (Wayback 2023-03-25, content not fetched) | NOT_CONFIRMED → approximation | partial-official |
| 2024 | NOT_PROBED → approximation | NOT_CONFIRMED → approximation | partial-official |
| 2025 | **AVAILABLE** (Wayback 2025-05-28, content not fetched) | **AVAILABLE** (official PDF eff. 2025-02-01) | partial-official |
| 2026 | **AVAILABLE** (live, fetched 10-02 + 10-03) | **AVAILABLE** (official PDF eff. 2026-02-01) | partial-official |

Approximation warning: using the current schedule for past years is KNOWN-WRONG in at least
two documented ways — the NFA fee changed at 2014-10-01 and 2018-01-01 (S5), and public
references exist to CME fee increases inside the window (e.g. one effective 2022-02-01,
surfaced by search, not fetched). Any approximation must stay MODELED_COST with these caveats.

## 6. Limitations

1. **No account verification**: every row VERIFIED_VS_ACCOUNT=NOT_RUN; D2 account
   verification NOT_RUN. Nothing here is "measured" or "complete."
2. CME official per-cell ES tariff values could not be extracted (PDF text column
   scrambling); ES exchange/regulatory figures are IBKR's published offset rates,
   cross-referenced by one dated-access public mirror (TradeStation, undated fees).
3. Overnight Position Fee amounts (Tiered plan) NOT_FETCHED — JS tables never rendered
   in either session (2026-10-02, 2026-10-03).
4. IBKR per-product page renders the Non-Members Regular (default) view; member/incentive
   rate alternates exist but were not rendered.
5. Historical IBKR snapshots exist for 2022/2023/2025 but content was not retrievable
   (web.archive.org blocked); no historical IBKR number is asserted.
6. Post-2018 NFA fee status unresolved from official sources this session; one conflicting
   unverified mirror claim ($0.01 as of 2026-07-01) recorded in the JSON and NOT adopted.
7. Wayback probes are exact-URL closest-match facts, not coverage proofs for other URL
   forms (CME fee pages lived under multiple URL shapes over the years).
8. One accidental unrelated tool call occurred mid-session (a tianyancha code-table lookup
   fired in a parallel batch by mistake); no writes, no contribution to this deliverable —
   noted for transparency.
