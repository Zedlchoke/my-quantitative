"""SEC EDGAR adapter: Company Facts and Submissions (DISCOVERY_ONLY).

Contract notes:
- SEC fair access requires a declared User-Agent and low request rates; the
  production User-Agent must be owner-approved before any retrieval.
- ``filed`` dates are date-only evidence.  A filing's exact market
  availability is never claimed from a date: records carry an end-of-day UTC
  upper bound and an explicit note.  ``acceptanceDateTime`` proves EDGAR
  acceptance, not public dissemination, and is never used as availability.
"""

from __future__ import annotations

from ..authority import AuthorityStatus
from .base import (
    AdapterError,
    AdapterNote,
    AdapterOutput,
    AvailabilityBasis,
    RateLimitPolicy,
    RawResponse,
    ReleaseEvidence,
    RequestSpec,
    SourceAdapter,
    end_of_utc_day,
    midnight_utc,
    parse_date,
    parse_utc,
    reject_unknown_keys,
    require_keys,
    require_mapping,
    require_number,
    require_str,
    require_str_list,
    timings_from_evidence,
)

SEC_FILED_DATE_ONLY_NOT_EXACT_AVAILABILITY = "SEC_FILED_DATE_ONLY_NOT_EXACT_AVAILABILITY"
SEC_ACCEPTANCE_TIME_NOT_DISSEMINATION_PROOF = "SEC_ACCEPTANCE_TIME_NOT_DISSEMINATION_PROOF"
SEC_DURATION_FACTS_SKIPPED_V1 = "SEC_DURATION_FACTS_SKIPPED_V1"

_BASE = "https://data.sec.gov"
_DISCOVERY_USER_AGENT = "data-fusion-v1 DISCOVERY_ONLY (owner UA pending)"

_FACT_ALLOWED_KEYS = frozenset({"start", "end", "val", "accn", "fy", "fp", "form", "filed", "frame"})
_FACT_REQUIRED_KEYS = frozenset({"end", "val", "accn", "fy", "fp", "form", "filed"})
_RECENT_ALLOWED_KEYS = frozenset(
    {
        "accessionNumber",
        "filingDate",
        "reportDate",
        "acceptanceDateTime",
        "form",
        "primaryDocument",
        "primaryDocDescription",
        "isXBRL",
        "isInlineXBRL",
        "size",
        "items",
    }
)
_RECENT_REQUIRED_KEYS = frozenset(
    {"accessionNumber", "filingDate", "reportDate", "form", "primaryDocument"}
)


class SecAdapter(SourceAdapter):
    source_id = "SEC_EDGAR"
    parser_version = "sec-adapter-1.0.0"
    license_id = "sec-public-domain-v1"
    entitlement_id = "anonymous-no-key"
    authority_status = AuthorityStatus.DOCUMENTED_CANDIDATE

    @classmethod
    def default_rate_limit(cls) -> RateLimitPolicy:
        return RateLimitPolicy(
            source_id=cls.source_id,
            documented_limit="SEC fair access: max 10 requests/second with declared User-Agent",
            min_interval_seconds=0.2,
            max_retries=2,
            retry_backoff_seconds=1.0,
            retry_status_codes=(403, 429, 500, 502, 503),
        )

    @staticmethod
    def normalize_cik(cik: str | int) -> str:
        digits = str(cik).strip()
        if digits.startswith("CIK"):
            digits = digits[3:]
        if not digits.isdigit() or not 1 <= len(digits) <= 10:
            raise AdapterError("SCHEMA_INVARIANT_VIOLATED", f"CIK must be 1-10 digits, got {cik!r}")
        return digits.zfill(10)

    def build_submissions_request(self, cik: str | int) -> RequestSpec:
        return RequestSpec(
            source_id=self.source_id,
            url=f"{_BASE}/submissions/CIK{self.normalize_cik(cik)}.json",
            headers=(("User-Agent", _DISCOVERY_USER_AGENT),),
        )

    def build_company_facts_request(self, cik: str | int) -> RequestSpec:
        return RequestSpec(
            source_id=self.source_id,
            url=f"{_BASE}/api/xbrl/companyfacts/CIK{self.normalize_cik(cik)}.json",
            headers=(("User-Agent", _DISCOVERY_USER_AGENT),),
        )

    def parse_submissions(self, response: RawResponse) -> AdapterOutput:
        content = require_mapping(response.json(), "submissions")
        require_keys(content, {"cik", "entityType", "filings"}, "submissions")
        filings = require_mapping(content["filings"], "submissions.filings")
        require_keys(filings, {"recent"}, "submissions.filings")
        recent = require_mapping(filings["recent"], "submissions.filings.recent")
        require_keys(recent, _RECENT_REQUIRED_KEYS, "filings.recent")
        reject_unknown_keys(recent, _RECENT_ALLOWED_KEYS, "filings.recent")

        accessions = require_str_list(recent, "accessionNumber", "filings.recent")
        filing_dates = require_str_list(recent, "filingDate", "filings.recent")
        report_dates = require_str_list(recent, "reportDate", "filings.recent")
        forms = require_str_list(recent, "form", "filings.recent")
        documents = require_str_list(recent, "primaryDocument", "filings.recent")
        acceptance = recent.get("acceptanceDateTime", [])
        if not isinstance(acceptance, list) or not all(isinstance(item, str) for item in acceptance):
            raise AdapterError("SCHEMA_VALUE_TYPE_MISMATCH", "acceptanceDateTime must be a string list")
        lengths = {len(accessions), len(filing_dates), len(report_dates), len(forms), len(documents), len(acceptance)}
        if len(lengths) != 1:
            raise AdapterError("SCHEMA_INVARIANT_VIOLATED", "filings.recent columns have unequal length")

        entity_id = f"CIK{self.normalize_cik(content['cik'])}"
        records: list = []
        notes: list[AdapterNote] = [
            AdapterNote(
                SEC_FILED_DATE_ONLY_NOT_EXACT_AVAILABILITY,
                "availability uses the end of the filed UTC day as a conservative upper bound",
            )
        ]
        seen_accessions: set[str] = set()
        any_acceptance = False
        for index, accession in enumerate(accessions):
            if accession in seen_accessions:
                raise AdapterError("DUPLICATE_RECORD_ID", f"accession {accession!r} appears twice")
            seen_accessions.add(accession)
            filed_day = parse_date(filing_dates[index], f"filings.recent.filingDate[{index}]")
            available = end_of_utc_day(filed_day)
            acceptance_text = acceptance[index].strip() if index < len(acceptance) else ""
            if acceptance_text:
                any_acceptance = True
                event_time = parse_utc(acceptance_text, f"filings.recent.acceptanceDateTime[{index}]")
            else:
                event_time = available
            timings = timings_from_evidence(
                event_time,
                ReleaseEvidence(
                    captured_from="SEC submissions filingDate (date only)",
                    available_time_utc=available,
                    basis=AvailabilityBasis.DATE_ONLY_UPPER_BOUND,
                ),
            )
            if report_dates[index].strip():
                parse_date(report_dates[index], f"filings.recent.reportDate[{index}]")
            records.append(
                self.make_record(
                    dataset_id="submissions",
                    entity_id=entity_id,
                    field_name="filing",
                    value=accession,
                    unit="ACCESSION_ID",
                    timings=timings,
                    retrieved_time_utc=response.retrieved_time_utc,
                    request_id=response.request_id,
                    raw_sha256=response.sha256_hex(),
                )
            )
        if any_acceptance:
            notes.append(
                AdapterNote(
                    SEC_ACCEPTANCE_TIME_NOT_DISSEMINATION_PROOF,
                    "acceptanceDateTime is EDGAR acceptance, not proof of public dissemination",
                )
            )
        return self.make_output(
            dataset_id="submissions",
            request_id=response.request_id,
            response=response,
            records=records,
            notes=notes,
        )

    def parse_company_facts(self, response: RawResponse) -> AdapterOutput:
        content = require_mapping(response.json(), "companyfacts")
        require_keys(content, {"cik", "facts"}, "companyfacts")
        entity_id = f"CIK{self.normalize_cik(content['cik'])}"
        facts = require_mapping(content["facts"], "companyfacts.facts")

        records: list = []
        seen_fact_keys: set[tuple] = set()
        skipped_duration = 0
        for taxonomy in sorted(facts):
            tags = require_mapping(facts[taxonomy], f"companyfacts.facts[{taxonomy}]")
            for tag in sorted(tags):
                meta = require_mapping(tags[tag], f"companyfacts.facts[{taxonomy}][{tag}]")
                require_keys(meta, {"label", "units"}, f"facts[{taxonomy}][{tag}]")
                reject_unknown_keys(meta, {"label", "description", "units"}, f"facts[{taxonomy}][{tag}]")
                units = require_mapping(meta["units"], f"facts[{taxonomy}][{tag}].units")
                for unit_name in sorted(units):
                    fact_list = units[unit_name]
                    if not isinstance(fact_list, list):
                        raise AdapterError(
                            "SCHEMA_VALUE_TYPE_MISMATCH",
                            f"facts[{taxonomy}][{tag}].units[{unit_name}] must be a list",
                        )
                    for index, fact in enumerate(fact_list):
                        context = f"facts[{taxonomy}][{tag}].units[{unit_name}][{index}]"
                        entry = require_mapping(fact, context)
                        require_keys(entry, _FACT_REQUIRED_KEYS, context)
                        reject_unknown_keys(entry, _FACT_ALLOWED_KEYS, context)
                        if "start" in entry:
                            skipped_duration += 1
                            continue
                        end_day = parse_date(require_str(entry, "end", context), f"{context}.end")
                        filed_day = parse_date(require_str(entry, "filed", context), f"{context}.filed")
                        value = require_number(entry, "val", context)
                        available = end_of_utc_day(filed_day)
                        timings = timings_from_evidence(
                            midnight_utc(end_day),
                            ReleaseEvidence(
                                captured_from="SEC company facts filed date (date only)",
                                available_time_utc=available,
                                basis=AvailabilityBasis.DATE_ONLY_UPPER_BOUND,
                            ),
                        )
                        fact_key = (taxonomy, tag, unit_name, end_day, str(entry["accn"]), filed_day)
                        if fact_key in seen_fact_keys:
                            raise AdapterError(
                                "DUPLICATE_RECORD_ID", f"duplicate company fact {fact_key}"
                            )
                        seen_fact_keys.add(fact_key)
                        records.append(
                            self.make_record(
                                dataset_id="company_facts",
                                entity_id=entity_id,
                                field_name=f"{taxonomy}:{tag}",
                                value=value,
                                unit=unit_name,
                                timings=timings,
                                retrieved_time_utc=response.retrieved_time_utc,
                                request_id=response.request_id,
                                raw_sha256=response.sha256_hex(),
                            )
                        )
        notes = [
            AdapterNote(
                SEC_FILED_DATE_ONLY_NOT_EXACT_AVAILABILITY,
                "availability uses the end of the filed UTC day as a conservative upper bound",
            )
        ]
        if skipped_duration:
            notes.append(
                AdapterNote(
                    SEC_DURATION_FACTS_SKIPPED_V1,
                    f"{skipped_duration} duration facts carry a period start and are not mapped in V1",
                )
            )
        return self.make_output(
            dataset_id="company_facts",
            request_id=response.request_id,
            response=response,
            records=records,
            notes=notes,
        )
