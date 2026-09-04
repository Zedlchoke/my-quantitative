"""Static discovery registry. Entries are candidates, never implicit authority."""

from __future__ import annotations

from dataclasses import dataclass

from .authority import AuthorityStatus


@dataclass(frozen=True, slots=True)
class SourceSpec:
    source_id: str
    asset_classes: tuple[str, ...]
    capabilities: tuple[str, ...]
    official_url: str
    terms_url: str | None
    account_or_key_required: bool
    status: AuthorityStatus
    forbidden_inference: tuple[str, ...] = ()


SOURCES: tuple[SourceSpec, ...] = (
    SourceSpec("TRUEFX", ("forex",), ("top_of_book_bid_ask",), "https://www.truefx.com/truefx-historical-downloads-2/", "https://www.truefx.com/truefx-terms-and-conditions/", False, AuthorityStatus.CANDIDATE_NOT_AUTHORIZED, ("generic_market_swap",)),
    SourceSpec("BIS_CBPOL", ("forex", "macro"), ("policy_rates",), "https://data.bis.org/topics/CBPOL", "https://www.bis.org/terms_conditions.htm", False, AuthorityStatus.DOCUMENTED_CANDIDATE),
    SourceSpec("ECB_SDMX", ("forex", "macro"), ("exchange_rates", "macro_series"), "https://data.ecb.europa.eu/help/getting-data-web-services-sdmx-0", None, False, AuthorityStatus.DOCUMENTED_CANDIDATE),
    SourceSpec("FRED_ALFRED", ("forex", "stocks", "macro"), ("macro_series", "vintages", "release_dates"), "https://fred.stlouisfed.org/docs/api/fred/", "https://fred.stlouisfed.org/docs/api/terms_of_use.html", True, AuthorityStatus.CANDIDATE_NOT_AUTHORIZED, ("analyst_consensus", "exact_wire_release_timestamp")),
    SourceSpec("SEC_EDGAR", ("stocks",), ("company_facts", "submissions", "filing_clock"), "https://www.sec.gov/search-filings/edgar-application-programming-interfaces", "https://www.sec.gov/about/webmaster-frequently-asked-questions", False, AuthorityStatus.DOCUMENTED_CANDIDATE),
    SourceSpec("SEC_13F", ("stocks",), ("institutional_holdings",), "https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets", None, False, AuthorityStatus.DOCUMENTED_CANDIDATE, ("real_time_institutional_position",)),
    SourceSpec("FINRA_SHORT", ("stocks",), ("short_interest", "short_sale_volume"), "https://www.finra.org/finra-data/browse-catalog/short-sale-volume", "https://www.finra.org/finra-data/terms-of-use", False, AuthorityStatus.DOCUMENTED_CANDIDATE, ("borrow_fee", "utilization", "short_sale_volume_equals_short_interest")),
    SourceSpec("ALPHA_VANTAGE_EARNINGS", ("stocks",), ("earnings", "analyst_estimates", "surprise"), "https://www.alphavantage.co/documentation/", "https://www.alphavantage.co/terms_of_service/", True, AuthorityStatus.CANDIDATE_NOT_AUTHORIZED, ("point_in_time_estimate_without_revision_audit",)),
    SourceSpec("MASSIVE_BASIC", ("stocks",), ("prices_2y", "corporate_actions"), "https://massive.com/pricing?product=stocks", None, True, AuthorityStatus.CANDIDATE_NOT_AUTHORIZED, ("eight_year_coverage",)),
    SourceSpec("TWELVE_DATA", ("stocks", "forex"), ("prices", "reference_data"), "https://twelvedata.com/pricing", None, True, AuthorityStatus.CANDIDATE_NOT_AUTHORIZED),
)


def by_id(source_id: str) -> SourceSpec:
    matches = [source for source in SOURCES if source.source_id == source_id]
    if len(matches) != 1:
        raise KeyError(source_id)
    return matches[0]
