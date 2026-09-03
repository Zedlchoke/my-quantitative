# Provider comparison — Stocks DA0 discovery (access date 2026-09-03 UTC)

Authority: `requirement_coverage_matrix.json` + `provider_longlist.json` in
this directory. No coverage cell here may be read as a gate PASS; all R01–R19
verdicts remain `UNAVAILABLE_FAIL_CLOSED` until real ingestion acceptance.

## Retail / self-service candidates

| Provider | Product focus | Public pricing | Individual | Vietnam | Discovery verdict |
|---|---|---|---|---|---|
| **Norgate Data** | US EOD 1990+/1950+, delisted (25,222), **historical index constituents** (S&P 500 from 1957, NDX 1993, Russell 1990), CA at ex-date, halts since 1950, Python API | Dynamic calculator; search snapshot Diamond USD 787.50/12mo; Platinum exact figure unresolved | Yes (self-service) | No geo restriction documented; USD wire/ACH rails — VN wire unverified | **DOCUMENTED_CANDIDATE** |
| **Massive (ex-Polygon.io)** | 20+y trades/quotes/aggregates; dividends with `declaration_date`+`ex_dividend_date`; splits; ticker-events (experimental); delisted via `active=false`; market holidays | **$0 / $29 / $79 / $199 per month** (annual −20%); Advanced "non-pros only" | Yes (individual plans) | No geo restriction documented; card payment unverified for VN | **DOCUMENTED_CANDIDATE** |
| **Sharadar SEP** (Nasdaq Data Link) | EOD prices + CA + reference, 20k+ companies from 1998, active+delisted, "nearly free of survivorship bias" (vendor claim) | Behind "View Pricing" → pricing check required | Yes (NDL accounts) | Self-service; VN payment unverified | **PARTIAL_CANDIDATE** |
| **ORTEX** | **Modelled** short interest / CTB / availability, intraday estimates | Checkout-tiered, not captured | Retail plans exist | Unverified | **NOT_SUITABLE** (estimates ≠ official lend records; can never be borrow authority) |

## Institutional (CONTACT_SALES) candidates

| Provider | What it adds | Pricing | Individual/VN | Verdict |
|---|---|---|---|---|
| **S3 Partners** | Borrow fee/utilization/positioning history, 65k+ securities | CONTACT_SALES (Snowflake/AWS marketplace) | Institutional process; individual likely ineligible; VN unknown | **CONTACT_REQUIRED** |
| **FIS Astec Analytics** | Intraday securities-lending data (SLD), 45k+ instruments, via Nasdaq Data Link | CONTACT_SALES | Same | **CONTACT_REQUIRED** |
| **S&P Global MI (ex-IHS Markit) Securities Finance** | Borrow/fee/utilization/lending histories | CONTACT_SALES | Same | **CONTACT_REQUIRED** |
| **CRSP (WRDS)** | Gold-standard security master, delistings, survivorship-free history, index membership research files | Institutional/academic subscription | Individual only via university affiliation | **CONTACT_REQUIRED** |

## Free official sources (usable immediately, with curation)

| Source | Contributes | Cost | Verdict |
|---|---|---|---|
| **S&P DJI** official press releases / index communications | **Announcement + effective timestamps** for index add/delete — exactly F1's R06 | Free archive (commercial feed: sales) | **PARTIAL_CANDIDATE** (DIY curation; archive depth + licensing unresolved) |
| **SSGA SPY** official issuer page | NAV history + distributions → SPY total-return inputs (R10) | Free | **DOCUMENTED_CANDIDATE** |
| **FINRA** Equity Short Interest | Official bi-monthly short positions (context; NOT fee/utilization history) | Free | **PARTIAL_CANDIDATE** |

## The two structural gaps

1. **R06 (announcement vs effective, index changes):** no retail price vendor
   documents announcement timestamps for index reconstitutions. Norgate's
   constituent history is effective-dated only. The only accessible official
   authority is S&P DJI's own announcement archive — requiring a curated DIY
   collection whose licensing and machine-readability are unresolved.
2. **R11/R12 (borrow availability/fee/utilization history):** every real
   authority found is institutional (S3, Astec, S&P Global MI). The only
   retail-accessible product (Ortex) publishes modelled estimates and was
   therefore ruled NOT_SUITABLE as a borrow authority. Family F2 has **no
   discovered path** for an individual researcher today.
