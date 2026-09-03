# Z1 A2 — free-source evidence, downloader, reconciliation, gap audit

Lane: `orca/stocks-free-v1-z1-data` (A2 of stocks-free-v1, wave Z1).
Access date for every capture below: **2026-09-03 (UTC)**. All raw payloads
live outside Git under `staging-data/stocks_free_v1_z1_a2/`; this directory
holds only manifests, digests, logs, short terms excerpts and findings.

## 1. Per-source verdict table (PLAN 4.1 items 1-3)

| source | role | account | verdict | decisive captured fact |
|---|---|---|---|---|
| stooq.com daily CSV | daily OHLCV | no | `EXCLUDED_LICENSE_UNPROVEN` | JS SHA-256 proof-of-work "verify your browser" page (796 B) to curl-like clients; fabricated identical 404 body (271 B) for every URL incl. homepage to python-urllib. No content or terms obtainable without a real browser; lane does not bypass anti-bot verification. |
| SSGA SPDR fund-data (official issuer) | NAV history, premium/discount, distributions | no | `EXCLUDED_LICENSE_UNPROVEN` | Zero-cost ACCESS proven (XLSX files downloaded without account); but every terms-of-use URL candidate (5 tried) serves a JS SPA shell or redirect landing with no terms text, so the license test of PLAN 4.1 item 3 cannot be judged and is not invented. |
| FRED fredgraph.csv (DFF, SOFR) | cash-rate daily series | no | `CANDIDATE` (conditional) | Full terms text captured: public non-commercial/educational/personal use at no cost; DFF series page marked "Public Domain: Citation Requested"; automation ambiguity recorded (robots/scraping prohibited except under FRED API terms, which require an account -> excluded elsewhere). Narrow admission: on-demand single-series downloads of public-domain-marked series, citation kept. |
| Yahoo Finance chart API | diagnostic OHLCV/adjclose | no | `DIAGNOSTIC_ONLY` | Captured ToS grant only a personal, revocable, non-transferable license "for the sole purpose of enabling you to use and enjoy the benefit of the Services" — no redistribution/pipeline rights. Access also flaky (repeated 429, then 200). |
| Massive (ex-Polygon.io) free tier | daily OHLCV | YES | `EXCLUDED_ACCOUNT_REQUIRED` | Pricing page (captured) requires "Create account" + API key before any data. Zero price, account boundary still applies (PLAN 2). |
| Nasdaq Data Link free | supplementary | YES | `EXCLUDED_ACCOUNT_REQUIRED` | Programmatic access requires registered account + personal API token; terms page itself is an SPA shell to non-browser clients (digest recorded). |

Registry of record: `research/stocks_free_v1/source_evidence.py`
(JSON dump: `source_evidence_registry.json`, integrity problems: none).

## 2. Real-download results (deterministic downloader; staged, digested)

Downloader: `research/stocks_free_v1/data_adapter.py` — serial, >=2 s per-host
interval, 3 retries exponential backoff, polite UA, SHA-256 per file, JSONL
log (`download_log.jsonl` here; raw bodies of failed responses preserved as
evidence).

| artifact (staging path) | bytes | sha256 (12) | notes |
|---|---|---|---|
| ssga/navhist-us-en-spy.xlsx | 276 544 | `5e055d2239eb` | 5 727 daily NAV rows, 2003-12-01..2026-09-01 |
| ssga/navhist-us-en-xle.xlsx | 269 467 | `46c466f3ba9a` | 5 727 rows, same window |
| ssga/navhist-us-en-xlf.xlsx | 268 851 | `9d58c5752d96` | 5 727 rows, same window |
| ssga/navhist-us-en-xlu.xlsx | 265 180 | `58835cbf257e` | 5 727 rows, same window |
| ssga/pdhist-us-en-spy.xlsx | 30 074 | `0b1e518d8dd9` | daily premium/discount |
| ssga/spdr-etf-historical-distributions.xlsx | 575 400 | `1b952f87ca60` | 13 174 distribution records, all SPDR ETFs |
| fred/fredgraph_dff.csv | 423 611 | `cd772cb72828` | 26 361 obs, 1954-07-01..2026-09-01, 0 empty cells |
| fred/fredgraph_sofr.csv | 34 782 | `9965fc5a461e` | 2 102 obs, 2018-04-03..2026-09-01, 94 empty cells recorded |
| yahoo/spy_chart_dec2024.json | 3 527 | `44d227572f82` | 21 bars + 1 div event (DIAGNOSTIC_ONLY) |
| stooq/spy_us_csv_curlfp.html | 796 | `51d7e6f7b867` | PoW challenge page (blocker evidence) |
| stooq/*python-urllib 404 bodies* | 271 | `03fa6d7ffcac` | identical fabricated 404 for every URL |

Full manifest: `checksum_manifest_staging.json` (32 files);
digest index: `staging_digest_index.json`.

Note: stooq OHLCV for SPY + sector ETFs — the originally planned sample —
could NOT be downloaded (see verdict table). The multi-instrument sample was
instead taken from issuer-official SSGA NAV histories (SPY, XLE, XLF, XLU).

## 3. Two-pull determinism (PLAN 4.1 item 13)

>=1 h spacing is impossible in-session; the module implements and unit-tests
the comparison and the lane ran two IMMEDIATE pulls per URL. Static endpoints
were expected byte-identical; divergence would be recorded as revision delta.

| url | pull A sha | pull B sha | equal |
|---|---|---|---|
| SSGA navhist-us-en-spy.xlsx | `5e055d2239eb` | `5e055d2239eb` | YES |
| FRED fredgraph.csv?id=DFF | `cd772cb72828` | `cd772cb72828` | YES |
| stooq SPY CSV | 404 body `03fa6d7ffcac` | 404 body `03fa6d7ffcac` | no data (blocked) |

Deterministic single-shot downloads confirmed for SSGA and FRED.

## 4. Reconciliation findings (PLAN 4.1 items 7/10/14/15)

Method (`research/stocks_free_v1/reconciliation.py`, stdlib-only OOXML
parser): total-return index reconstructed from raw NAV + issuer distribution
records with declared convention `f_t = (nav_t + dist_t)/nav_{t-1}` (ex-date
reinvestment at same-session NAV).

- SPY reconstructed TR index 2003-12-01..2026-09-01: 10.7428 vs price-only
  7.0763 -> cumulative reinvested distribution effect +51.8% (plausible for
  ~23y of SPY dividends; internal consistency check PASS).
- Independent diagnostic cross-check vs Yahoo adjusted close (Dec 2024
  window, 21 common dates, declared tolerance 0.5% relative): max rel diff
  0.114%, 0 conflicts -> PASS. (Diagnostic source only; not load-bearing.)
- Distribution coverage conflicts (recorded, not silently dropped): SPY 43
  ex-dates have no NAV observation, XLE/XLF/XLU 19 each — all are ex-dates
  before the 2003-12-01 start of the issuer NAV-history workbooks (issuer
  files do NOT provide full-inception NAV; distribution history itself goes
  back to 1993/1999).
- Session-convention gap audit (`gap_audit.py` with the owner frozen
  calendar `USEquityRegularCalendar` injected as predicate): 2010-01-01+
  window CLEAN for all four funds (no missing sessions, duplicates,
  disorder, non-positive NAV). Full 2003+ window: 56 weekday-predicate
  MISSING_SESSION findings per fund in the 2003-2009 tail — below the
  frozen calendar table horizon (2010-2030) the owner predicate
  intentionally fails closed, so only a weaker weekday approximation was
  available there; flagged, not silently accepted.
- FRED DFF: 0 gaps vs calendar-daily convention. SOFR: 94 empty value cells
  recorded (published-but-empty days), 0 calendar gaps.

Full JSON: `real_download_findings.json`.

## 5. Honest gate position

- FD0_ZERO_COST_LICENSE: FAIL as of this session — the only zero-account
  price/NAV sources either deny non-browser clients (stooq) or serve no
  capturable license text (SSGA). FRED passes narrowly for the cash-rate
  role. Per PLAN 9, if the free stack cannot pass, the cycle closes
  `STOCKS_FREE_V1_BLOCKED_FREE_DATA_AUTHORITY` rather than weakening gates.
- Owner-unblock options (recorded, not taken): authorize a real-browser
  session to capture SSGA terms text and stooq terms/challenge-free export,
  or authorize account creation for an account-gated provider.

## 6. Files

- `source_evidence_registry.json` — machine-readable registry dump
- `checksum_manifest_staging.json`, `staging_digest_index.json`
- `download_log.jsonl`, `results_index.json`, `results_index_2.json`
- `real_download_findings.json` — reconciliation/gap-audit/coverage results
- code: `research/stocks_free_v1/{source_evidence,data_adapter,reconciliation,gap_audit}.py`
- tests: `tests/stocks_free_v1/test_*.py` (offline; no network needed)
