"""Machine-readable free-data source evidence registry (A2, Z1).

Implements PLAN_stocks_free.md section 4.1 items 1-3: provider identity and
official URLs, zero-cost attestation (captured terms URL + access date plus a
SHORT excerpt only), account requirement, and a verdict from a closed enum.

Honesty contract
----------------
License conclusions are never invented. A verdict of
``EXCLUDED_LICENSE_UNPROVEN`` is recorded whenever the terms could not be
captured in-session (anti-bot verification, JavaScript single-page-app
shells served instead of terms text) or whenever the captured terms are
silent or ambiguous about research use, local storage and derived research.
Such a failure is a valid, honest result and feeds
``STOCKS_FREE_V1_BLOCKED_FREE_DATA_AUTHORITY``.

Every excerpt stored here is intentionally short (a few sentences), with the
canonical URL and the UTC access date, so no substantial copyrighted text is
reproduced. Full captured snapshots live OUTSIDE Git in the staging area;
their SHA-256 digests are recorded per source and in the z1_a2 audit
manifest (``research/audits/stocks_free_v1/z1_a2/``).

Session access facts (2026-09-03, all captures by the lane's deterministic
downloader in ``data_adapter.py``; sha256 of every staged snapshot is in the
audit manifest):
- stooq.com serves a JavaScript SHA-256 proof-of-work "verify your browser"
  page (796 bytes) to curl-like clients and a fabricated 404 page (271
  bytes, same body for every URL including the homepage) to python-urllib
  clients. No content, including terms, is obtainable without a real
  browser. The lane does not bypass anti-bot verification.
- ssga.com fund-data XLSX files download without account (zero-cost access
  proven), but every terms-of-use URL candidate serves a JavaScript SPA
  shell or a redirect landing with no terms text, so the license itself
  could not be captured.
- fred.stlouisfed.org serves full terms text and data with no account;
  curl's HTTP/2 stack is stalled by the host edge while python-urllib works.
- Yahoo serves data intermittently (HTTP 429 repeatedly observed, later
  200); terms text captured in full.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Tuple

VERDICTS = frozenset(
    {
        "CANDIDATE",
        "EXCLUDED_ACCOUNT_REQUIRED",
        "EXCLUDED_PAID",
        "EXCLUDED_LICENSE_UNPROVEN",
        "DIAGNOSTIC_ONLY",
    }
)

VERDICT_CANDIDATE = "CANDIDATE"
VERDICT_EXCLUDED_ACCOUNT_REQUIRED = "EXCLUDED_ACCOUNT_REQUIRED"
VERDICT_EXCLUDED_PAID = "EXCLUDED_PAID"
VERDICT_EXCLUDED_LICENSE_UNPROVEN = "EXCLUDED_LICENSE_UNPROVEN"
VERDICT_DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"


@dataclass(frozen=True)
class SourceCandidate:
    """Evidence record for one candidate data source."""

    source_id: str
    identity: str
    role: str
    official_urls: Tuple[str, ...]
    terms_url: str
    terms_accessed_utc: str
    terms_excerpt: str
    account_required: bool
    verdict: str
    rationale: str
    access_blocker: str = ""
    evidence_digests: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    """(label, sha256) pairs for captured snapshots stored outside Git."""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["official_urls"] = list(self.official_urls)
        d["evidence_digests"] = [list(p) for p in self.evidence_digests]
        return d


D_SSGA_TERMS_SHELL_A = "ec71ca1dd063f73dfcbdd8678df495189b7a41b5bd7ddf17de0291e558bd3b91"
D_SSGA_TERMS_SHELL_B = "c06412295da384ad0751e7e3ba35be39659c77a35616e745c243361c48d49ab1"
D_SSGA_TERMS_404_C = "942021f98f4718a4277ba371f581b4b7b0c4dce77189f2d6a8fa95338defd83c"
D_STOOQ_CHALLENGE = "51d7e6f7b86779eb5b94250704aacfd34f8c23335f7e7dbcdd807e769b087e05"
D_STOOQ_FABRICATED_404 = "03fa6d7ffcac125ba680b7558912f278abec5a5685a4fee3c26a023b32354115"
D_FRED_TERMS = "bfb7e709faa09b0414aaaeb066f02c96ba7a2dadb9e8ab92d8e32c5a7c67efec"
D_FRED_DFF_PAGE = "29f5b302533e5028ade82b766bdf1d6de620e7ea2a79394d1b9c6c7ed030e8e6"
D_YAHOO_TERMS = "0154194106f6f2d0fc6fd6f0ca865aa793bbe9637ca6d1b2d8adba722af8c6cf"
D_MASSIVE_PRICING = "77e53f0e6d69796be5334cbbba306cac7359ed2b5bdfda9cf0c7b53eeae85c73"
D_NASDAQ_TERMS_SHELL = "f4ad31e0fc9a39ad0ae8c8eb6bc929782e113d8025ab6c7eede3c4c13ee4f3e3"

SOURCE_CANDIDATES: Tuple[SourceCandidate, ...] = (
    SourceCandidate(
        source_id="stooq_daily_csv",
        identity="stooq.com free daily historical CSV export endpoint "
        "(https://stooq.com/q/d/l/?s=<sym>&d1=YYYYMMDD&d2=YYYYMMDD&i=d)",
        role="daily OHLCV price bars",
        official_urls=(
            "https://stooq.com/",
            "https://stooq.com/q/d/l/?s=spy.us&d1=20240102&d2=20240110&i=d",
        ),
        terms_url="https://stooq.com/ (terms page not reachable in-session; "
        "candidate terms URLs https://stooq.com/page/?s=terms and "
        "https://stooq.com/doc/terms/?c=en both returned HTTP 404)",
        terms_accessed_utc="2026-09-03",
        terms_excerpt="",
        account_required=False,
        verdict=VERDICT_EXCLUDED_LICENSE_UNPROVEN,
        rationale="No terms text could be captured in-session, so the "
        "zero-cost/license test (PLAN 4.1 items 2-3) cannot be passed. Every "
        "programmatic request from this lane - homepage, CSV export and both "
        "guessed terms URLs - was denied to non-browser clients: curl-like "
        "clients receive an HTTP 200 JavaScript SHA-256 proof-of-work 'verify "
        "your browser' challenge page (796 bytes, digest recorded); "
        "python-urllib clients receive a fabricated HTTP 404 page (271 bytes, "
        "identical body for every URL including the homepage). The lane does "
        "not bypass anti-bot verification, so no data and no terms were "
        "obtainable without a real browser session.",
        access_blocker="client-fingerprint denial: JS proof-of-work "
        "challenge (curl fingerprint) or fabricated 404 (python-urllib "
        "fingerprint) for every URL including the homepage",
        evidence_digests=(
            ("stooq_challenge_page_curl_fingerprint.html", D_STOOQ_CHALLENGE),
            ("stooq_fabricated_404_python_urllib.body", D_STOOQ_FABRICATED_404),
        ),
    ),
    SourceCandidate(
        source_id="ssga_spdr_official",
        identity="State Street Global Advisors (SSGA, now State Street "
        "Investment Management) official SPDR ETF fund-data library: NAV "
        "history, premium/discount history and the SPDR ETF historical "
        "distributions workbook",
        role="issuer-official daily NAV, premium/discount and cash-"
        "distribution records",
        official_urls=(
            "https://www.ssga.com/us/en/intermediary/etfs/"
            "spdr-sp-500-etf-trust-fund-spy",
            "https://www.ssga.com/us/en/intermediary/library-content/products/"
            "fund-data/etfs/us/navhist-us-en-spy.xlsx",
            "https://www.ssga.com/us/en/intermediary/library-content/products/"
            "fund-data/etfs/us/pdhist-us-en-spy.xlsx",
            "https://www.ssga.com/us/en/intermediary/library-content/products/"
            "fund-data/etfs/us/spdr-etf-historical-distributions.xlsx",
        ),
        terms_url="https://www.ssga.com/legal/terms-of-use (and candidates "
        "/us/en/intermediary/terms-of-use, /us/en/intermediary/legal, "
        "/us/en/intermediary/legal/terms-of-use, "
        "/legal-information/terms-of-use)",
        terms_accessed_utc="2026-09-03",
        terms_excerpt="",
        account_required=False,
        verdict=VERDICT_EXCLUDED_LICENSE_UNPROVEN,
        rationale="Zero-cost ACCESS is proven: issuer fund-data XLSX files "
        "downloaded directly over HTTPS with no account, no credentials and "
        "no payment (digests recorded), and the issuer fund page is the "
        "authoritative identity/inception evidence. But the zero-cost "
        "LICENSE test is NOT passed: every terms-of-use URL candidate serves "
        "a JavaScript SPA shell (127 KB of markup, ~12 KB navigation-only "
        "text) or a redirect landing page with no terms text to a "
        "non-browser client. Per PLAN 4.1 item 3 and the lane honesty rule, "
        "terms that cannot be captured cannot be judged, so the verdict is "
        "EXCLUDED_LICENSE_UNPROVEN, not CANDIDATE. The downloaded files "
        "remain primary audit evidence for items 7/10 (distributions, NAV "
        "reconciliation) but cannot ground an accepted-source claim on their "
        "own; owner may separately authorize browser-based terms capture.",
        access_blocker="terms text not capturable in-session (SPA shells / "
        "redirect landings without body text); data endpoints themselves "
        "work without account",
        evidence_digests=(
            ("navhist-us-en-spy.xlsx",
             "5e055d2239eb72ec3c6f193aa17d21f43d50083c7d32471561f249c31fa1fcbc"),
            ("spdr-etf-historical-distributions.xlsx",
             "1b952f87ca60ece4080b446d6c3b580f640d893ed33641797a2dd22dd61beca9"),
            ("ssga_terms_shell_landings.html", D_SSGA_TERMS_SHELL_A),
            ("ssga_terms_shell_redirect.html", D_SSGA_TERMS_SHELL_B),
            ("ssga_terms_404_statestreet.body", D_SSGA_TERMS_404_C),
        ),
    ),
    SourceCandidate(
        source_id="fred_fredgraph_csv",
        identity="FRED (Federal Reserve Bank of St. Louis) fredgraph.csv "
        "direct graph export, e.g. "
        "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFF",
        role="cash-rate daily series (DFF/SOFR) for explicit cash yield",
        official_urls=(
            "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFF",
            "https://fred.stlouisfed.org/series/DFF",
        ),
        terms_url="https://fred.stlouisfed.org/legal/terms-of-use",
        terms_accessed_utc="2026-09-03",
        terms_excerpt="'FRED provides data and data services to the public "
        "for non-commercial, educational, and personal uses subject to a few "
        "prohibitions.' ... 'You are free to access and use FRED at no "
        "cost' ... series DFF page marks 'Public Domain: Citation "
        "Requested' ... but the terms also prohibit: 'use of any data "
        "mining, mirroring, robots, scraping, or similar data-gathering or "
        "extraction methods except as expressly allowed by the terms of use "
        "applicable to the FRED API' and require attribution ('be sure to "
        "mention FRED as the service from which you retrieved the data and "
        "keep any copyright notices').",
        account_required=False,
        verdict=VERDICT_CANDIDATE,
        rationale="No-account, no-payment access verified in-session "
        "(full-history CSV served to a single polite GET; curl HTTP/2 "
        "stalls at the host edge while python-urllib succeeds - recorded in "
        "the download log). Terms text captured in full (digest recorded). "
        "CANDIDATE is conditional and narrow: (a) only series explicitly "
        "marked 'Public Domain: Citation Requested' (DFF verified; SOFR to "
        "be verified at admission); (b) citation and copyright notices kept; "
        "(c) refresh policy must be on-demand single-series downloads in the "
        "manner of the site's own download button, NOT scheduled robots-style "
        "re-fetching, because automated extraction without the FRED API "
        "(whose terms of use and API key require an account - excluded "
        "elsewhere) is prohibited by the captured text. This automation-"
        "cadence ambiguity is recorded rather than resolved; final admission "
        "is the A3/A7 call under PLAN 4.1 item 3.",
        evidence_digests=(
            ("fred_terms_of_use.html", D_FRED_TERMS),
            ("fred_series_dff_page.html", D_FRED_DFF_PAGE),
            ("fredgraph_dff.csv",
             "cd772cb7282863eada9c5a9d3776703745dcc6f5aa1a8d80f238715abc79918c"),
        ),
    ),
    SourceCandidate(
        source_id="yahoo_finance_chart",
        identity="Yahoo Finance public chart JSON API "
        "(query1/query2.finance.yahoo.com/v8/finance/chart/<SYMBOL>)",
        role="diagnostic cross-check of daily OHLCV/adjusted close only",
        official_urls=(
            "https://finance.yahoo.com/",
            "https://query1.finance.yahoo.com/v8/finance/chart/SPY",
        ),
        terms_url="https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html",
        terms_accessed_utc="2026-09-03",
        terms_excerpt="'Subject to your continuing compliance with these "
        "Terms, we grant you a personal, royalty-free, non-transferable, "
        "non-assignable, revocable, and non-exclusive license to use the "
        "software and APIs we may provide to you as part of the Services. "
        "This license is for the sole purpose of enabling you to use and "
        "enjoy the benefit of the Services we provide, in the manner "
        "permitted by these Terms.'",
        account_required=False,
        verdict=VERDICT_DIAGNOSTIC_ONLY,
        rationale="The captured Yahoo Terms of Service grant only a "
        "personal, revocable license to use the service; they do not "
        "authorize redistribution, local caching as a research dataset, or "
        "use as a load-bearing research input. Yahoo is therefore recorded "
        "as DIAGNOSTIC_ONLY: at most an independent cross-check per PLAN 4.1 "
        "item 14, never an accepted source. Additionally, access is flaky "
        "for non-browser clients: repeated HTTP 429 responses were observed "
        "before a successful 200 in-session.",
        access_blocker="intermittent HTTP 429 (Too Many Requests) on both "
        "query1 and query2 hosts",
        evidence_digests=(
            ("yahoo_terms.html", D_YAHOO_TERMS),
            ("spy_chart_dec2024.json",
             "44d227572f82e3b0b04a13d9bc9f96e2b873a705963f0a5589e1202af491dd0e"),
        ),
    ),
    SourceCandidate(
        source_id="massive_polygon_free_tier",
        identity="Massive (formerly Polygon.io) free tier for US equity/"
        "ETF aggregates",
        role="daily OHLCV candidate - EXCLUDED before any download",
        official_urls=(
            "https://massive.com/pricing",
            "https://polygon.io/pricing",
        ),
        terms_url="https://massive.com/pricing",
        terms_accessed_utc="2026-09-03",
        terms_excerpt="Pricing page (captured) presents 'Choose an asset "
        "class' plan tabs with 'Create account Sign in' as the access "
        "action; polygon.io/pricing redirects to massive.com/pricing "
        "(digests differ by one byte).",
        account_required=True,
        verdict=VERDICT_EXCLUDED_ACCOUNT_REQUIRED,
        rationale="The free tier is advertised at zero monetary cost but "
        "requires creating an account and obtaining an API key before any "
        "data is served. Account creation requires separate owner "
        "authorization (PLAN section 2); the lane therefore never fetched "
        "data from it and records it as EXCLUDED_ACCOUNT_REQUIRED.",
        evidence_digests=(
            ("massive_pricing.html", D_MASSIVE_PRICING),
            ("polygon_pricing.html",
             "47faf59a6747cfe14e9247da847984272d415082db55f2943b2ae5ac3cfa9f4b"),
        ),
    ),
    SourceCandidate(
        source_id="nasdaq_data_link_free",
        identity="Nasdaq Data Link (formerly Quandl) free lookups",
        role="supplementary daily data candidate - EXCLUDED before any "
        "download",
        official_urls=("https://data.nasdaq.com/",),
        terms_url="https://data.nasdaq.com/terms",
        terms_accessed_utc="2026-09-03",
        terms_excerpt="",
        account_required=True,
        verdict=VERDICT_EXCLUDED_ACCOUNT_REQUIRED,
        rationale="Programmatic access requires a registered account and a "
        "personal API token even for free datasets. Account creation "
        "requires separate owner authorization (PLAN section 2); recorded "
        "as EXCLUDED_ACCOUNT_REQUIRED without any authenticated fetch. Note: "
        "the captured terms URL serves a JavaScript SPA shell to non-browser "
        "clients (digest recorded), so the terms TEXT was also not "
        "readable in-session; the account requirement itself is the "
        "documented, disqualifying access condition.",
        access_blocker="account + API token required for programmatic "
        "access; terms page is an SPA shell to non-browser clients",
        evidence_digests=(("nasdaq_data_link_terms_shell.html", D_NASDAQ_TERMS_SHELL),),
    ),
)


def validate_registry(registry: Tuple[SourceCandidate, ...] = SOURCE_CANDIDATES) -> list:
    """Return a list of registry integrity problems (empty list = valid).

    Invariants:
    - verdict is from the closed enum;
    - identity, official_urls, terms_url and access date are present;
    - every CANDIDATE has a non-empty captured terms excerpt;
    - every EXCLUDED_ACCOUNT_REQUIRED has account_required=True;
    - EXCLUDED_LICENSE_UNPROVEN carries an explicit blocker;
    - excerpts are short (no substantial copyrighted text in Git).
    """
    problems = []
    for sc in registry:
        if sc.verdict not in VERDICTS:
            problems.append(f"{sc.source_id}: verdict {sc.verdict!r} not in enum")
        if not sc.identity or not sc.official_urls:
            problems.append(f"{sc.source_id}: missing identity/official_urls")
        if not sc.terms_url or not sc.terms_accessed_utc:
            problems.append(f"{sc.source_id}: missing terms capture provenance")
        if sc.verdict == VERDICT_CANDIDATE and not sc.terms_excerpt:
            problems.append(
                f"{sc.source_id}: CANDIDATE without captured terms excerpt"
            )
        if sc.verdict == VERDICT_EXCLUDED_ACCOUNT_REQUIRED and not sc.account_required:
            problems.append(
                f"{sc.source_id}: EXCLUDED_ACCOUNT_REQUIRED with "
                "account_required=False"
            )
        if (
            sc.verdict == VERDICT_EXCLUDED_LICENSE_UNPROVEN
            and not sc.access_blocker
        ):
            problems.append(
                f"{sc.source_id}: license-unproven verdict without recorded "
                "blocker evidence"
            )
        if len(sc.terms_excerpt) > 2000:
            problems.append(f"{sc.source_id}: terms excerpt exceeds 2000 chars")
    return problems


def registry_to_json(registry: Tuple[SourceCandidate, ...] = SOURCE_CANDIDATES) -> dict:
    """Serialize the registry to a JSON-compatible dict."""
    return {
        "schema": "stocks_free_v1/source_evidence@1",
        "verdict_enum": sorted(VERDICTS),
        "sources": [sc.to_dict() for sc in registry],
        "integrity_problems": validate_registry(registry),
    }


def write_registry_json(path, registry: Tuple[SourceCandidate, ...] = SOURCE_CANDIDATES) -> dict:
    """Write the registry JSON document and return it."""
    doc = registry_to_json(registry)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return doc
