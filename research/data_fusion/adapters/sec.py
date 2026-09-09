"""SEC EDGAR adapter: Submissions and Company Facts (DISCOVERY_ONLY).

Lane owner: A2 stocks.  Coded against the A1-owned shared foundation in
``research.data_fusion.adapters.base``.

Endpoints (anonymous, no key, no account):

- ``https://data.sec.gov/submissions/CIK##########.json``
- ``https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json``

Fail-closed contracts owned by this module:

- CIK is normalized deterministically to 10 digits before it enters a URL,
  so request identity is stable across caller spellings;
- SEC fair access (max 10 requests/second, declared User-Agent) is encoded
  as a :class:`RateLimitPolicy`; the production User-Agent must be
  owner-approved before any real retrieval, so the built requests carry a
  DISCOVERY_ONLY placeholder;
- ``filingDate`` is date-only evidence: available_time is the end of the
  filed UTC day as a conservative *upper bound*, never an exact market
  availability claim (note ``SEC_FILED_DATE_ONLY_NOT_EXACT_AVAILABILITY``);
- ``acceptanceDateTime`` proves EDGAR acceptance only.  It may seed the
  event/effective time but is never used as availability evidence (note
  ``SEC_ACCEPTANCE_TIME_NOT_DISSEMINATION_PROOF``);
- duration facts (entries carrying ``start``) are skipped, not coerced into
  instants (note ``SEC_DURATION_FACTS_SKIPPED_V1``);
- schema problems (unknown record keys, missing required keys, duplicate
  accession numbers or facts, malformed or non-UTC timestamps) are rejected
  with stable reason codes instead of being silently coerced.  Envelope
  keys outside the parsed records are tolerated so cosmetic upstream
  additions cannot break parsing of well-formed records;
- retrieved_time never substitutes for available_time.
"""

from __future__ import annotations

from datetime import date
import re
from typing import Any, ClassVar

from ..authority import AuthorityStatus
from .base import (
    AdapterError,
    AdapterNote,
    AdapterOutput,
    AvailabilityBasis,
    DUPLICATE_RECORD_ID,
    RateLimitPolicy,
    RawResponse,
    ReleaseEvidence,
    RequestSpec,
    SCHEMA_FIELD_MISSING,
    SCHEMA_INVARIANT_VIOLATED,
    SCHEMA_TIMESTAMP_INVALID,
    SCHEMA_UNKNOWN_FIELD,
    SCHEMA_VALUE_TYPE_MISMATCH,
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
    validate_response,
)

SEC_FILED_DATE_ONLY_NOT_EXACT_AVAILABILITY = "SEC_FILED_DATE_ONLY_NOT_EXACT_AVAILABILITY"
SEC_ACCEPTANCE_TIME_NOT_DISSEMINATION_PROOF = "SEC_ACCEPTANCE_TIME_NOT_DISSEMINATION_PROOF"
SEC_DURATION_FACTS_SKIPPED_V1 = "SEC_DURATION_FACTS_SKIPPED_V1"

_BASE = "https://data.sec.gov"
# Placeholder only: SEC fair access requires a declared contact UA; the
# production UA must be owner-approved before any real retrieval happens.
_DISCOVERY_USER_AGENT = "data-fusion-v1 DISCOVERY_ONLY (owner UA pending)"

_ACCESSION_RE = re.compile(r"^\d{10}-\d{2}-\d{6}$")
_URL_CIK_RE = re.compile(r"/CIK(\d{10})\.json$")

_SUBMISSIONS_REQUIRED_KEYS = frozenset({"cik", "filings"})
_FILINGS_ALLOWED_KEYS = frozenset({"recent", "files"})
_FILINGS_REQUIRED_KEYS = frozenset({"recent"})

# Documented column-oriented record set of submissions.filings.recent.
_RECENT_KNOWN_COLUMNS = frozenset(
    {
        "accessionNumber",
        "filingDate",
        "reportDate",
        "acceptanceDateTime",
        "act",
        "fileNumber",
        "form",
        "items",
        "size",
        "isXBRL",
        "isInlineXBRL",
        "primaryDocument",
        "primaryDocDescription",
    }
)
_RECENT_REQUIRED_COLUMNS = frozenset(
    {"accessionNumber", "filingDate", "reportDate", "form", "primaryDocument"}
)
# Columns parsed into records; all must be string lists.
_RECENT_STRING_COLUMNS = frozenset(
    {
        "accessionNumber",
        "filingDate",
        "reportDate",
        "acceptanceDateTime",
        "form",
        "primaryDocument",
    }
)

_FACT_ALLOWED_KEYS = frozenset(
    {"start", "end", "val", "accn", "fy", "fp", "form", "filed", "frame"}
)
_FACT_REQUIRED_KEYS = frozenset({"end", "val", "accn", "fy", "fp", "form", "filed"})
_FACT_META_ALLOWED_KEYS = frozenset({"label", "description", "units"})


class SecAdapter(SourceAdapter):
    """Adapter for SEC EDGAR company submissions and XBRL company facts."""

    source_id = "SEC_EDGAR"
    parser_version = "sec-adapter-1.0.0"
    license_id = "sec-public-domain-v1"
    entitlement_id = "anonymous-no-key"
    authority_status = AuthorityStatus.DOCUMENTED_CANDIDATE
    forbidden_fields: ClassVar[tuple[str, ...]] = ()

    @classmethod
    def default_rate_limit(cls) -> RateLimitPolicy:
        return RateLimitPolicy(
            source_id=cls.source_id,
            documented_limit=(
                "SEC fair access: no more than 10 requests/second, "
                "declared User-Agent with owner contact"
            ),
            min_interval_seconds=0.5,
            max_retries=2,
            retry_backoff_seconds=1.0,
            retry_status_codes=(403, 429, 500, 502, 503),
        )

    # -- request construction ------------------------------------------------

    @staticmethod
    def normalize_cik(cik: str | int) -> str:
        """Normalize any caller spelling of a CIK to exactly 10 digits."""

        if isinstance(cik, bool):
            raise AdapterError(SCHEMA_INVARIANT_VIOLATED, "CIK must be digits, got bool")
        digits = str(cik).strip()
        if digits.upper().startswith("CIK"):
            digits = digits[3:]
        if not digits.isascii() or not digits.isdigit() or not 1 <= len(digits) <= 10:
            raise AdapterError(
                SCHEMA_INVARIANT_VIOLATED,
                f"CIK must be 1-10 ASCII digits, got {cik!r}",
            )
        return digits.zfill(10)

    def build_submissions_request(self, cik: str | int) -> RequestSpec:
        cik10 = self.normalize_cik(cik)
        return RequestSpec(
            source_id=self.source_id,
            url=f"{_BASE}/submissions/CIK{cik10}.json",
            headers=(("User-Agent", _DISCOVERY_USER_AGENT),),
        )

    def build_company_facts_request(self, cik: str | int) -> RequestSpec:
        cik10 = self.normalize_cik(cik)
        return RequestSpec(
            source_id=self.source_id,
            url=f"{_BASE}/api/xbrl/companyfacts/CIK{cik10}.json",
            headers=(("User-Agent", _DISCOVERY_USER_AGENT),),
        )

    # -- shared helpers -------------------------------------------------------

    @staticmethod
    def _entity_id(cik: Any) -> str:
        if isinstance(cik, bool) or not isinstance(cik, (int, str)):
            raise AdapterError(SCHEMA_VALUE_TYPE_MISMATCH, "companyfacts.cik must be an integer or digit string")
        if isinstance(cik, str):
            return f"CIK{SecAdapter.normalize_cik(cik)}"
        if cik < 0:
            raise AdapterError(SCHEMA_VALUE_TYPE_MISMATCH, "companyfacts.cik must be non-negative")
        return f"CIK{SecAdapter.normalize_cik(cik)}"

    @staticmethod
    def _cik_from_url(url: str) -> str | None:
        match = _URL_CIK_RE.search(url)
        return match.group(1) if match else None

    def _check_url_entity(self, response: RawResponse, entity_id: str, context: str) -> None:
        url_cik = self._cik_from_url(response.url)
        if url_cik is not None and f"CIK{url_cik}" != entity_id:
            raise AdapterError(
                SCHEMA_INVARIANT_VIOLATED,
                f"{context}: body CIK {entity_id} does not match requested CIK{url_cik}",
            )

    @staticmethod
    def _filing_evidence(filed_day: date, captured_from: str) -> ReleaseEvidence:
        return ReleaseEvidence(
            captured_from=captured_from,
            available_time_utc=end_of_utc_day(filed_day),
            basis=AvailabilityBasis.DATE_ONLY_UPPER_BOUND,
        )

    # -- submissions ----------------------------------------------------------

    def parse_submissions(self, response: RawResponse) -> AdapterOutput:
        validate_response(response, allowed_content_types=("application/json",))
        content = require_mapping(response.json(), "submissions")
        require_keys(content, _SUBMISSIONS_REQUIRED_KEYS, "submissions")
        entity_id = self._entity_id(content["cik"])
        self._check_url_entity(response, entity_id, "submissions")

        filings = require_mapping(content["filings"], "submissions.filings")
        require_keys(filings, _FILINGS_REQUIRED_KEYS, "submissions.filings")
        reject_unknown_keys(filings, _FILINGS_ALLOWED_KEYS, "submissions.filings")
        recent = require_mapping(filings["recent"], "submissions.filings.recent")
        require_keys(recent, _RECENT_REQUIRED_COLUMNS, "filings.recent")
        reject_unknown_keys(recent, _RECENT_KNOWN_COLUMNS, "filings.recent")

        columns: dict[str, list[str]] = {}
        for column in sorted(recent):
            value = recent[column]
            if not isinstance(value, list):
                raise AdapterError(
                    SCHEMA_VALUE_TYPE_MISMATCH, f"filings.recent.{column} must be a list"
                )
            if column in _RECENT_STRING_COLUMNS:
                columns[column] = require_str_list(recent, column, "filings.recent")
        lengths = {column: len(values) for column, values in columns.items()}
        if len(set(lengths.values())) != 1:
            raise AdapterError(
                SCHEMA_INVARIANT_VIOLATED,
                f"filings.recent columns have unequal lengths: {lengths}",
            )
        # Known-but-unconsumed columns (act, fileNumber, items, size, isXBRL,
        # isInlineXBRL, primaryDocDescription) must align as well.
        expected_len = lengths["accessionNumber"]
        for column, value in recent.items():
            if column not in _RECENT_STRING_COLUMNS and len(value) != expected_len:
                raise AdapterError(
                    SCHEMA_INVARIANT_VIOLATED,
                    f"filings.recent.{column} length {len(value)} does not match "
                    f"{expected_len}",
                )

        accessions = columns["accessionNumber"]
        filing_dates = columns["filingDate"]
        report_dates = columns["reportDate"]
        forms = columns["form"]
        documents = columns["primaryDocument"]
        acceptance = columns.get("acceptanceDateTime", [""] * len(accessions))

        records: list = []
        notes: list[AdapterNote] = [
            AdapterNote(
                SEC_FILED_DATE_ONLY_NOT_EXACT_AVAILABILITY,
                "availability is the end of the filed UTC day: a conservative "
                "upper bound, never an exact market availability claim",
            )
        ]
        seen_accessions: set[str] = set()
        any_acceptance = False
        for index, accession in enumerate(accessions):
            if accession in seen_accessions:
                raise AdapterError(
                    DUPLICATE_RECORD_ID, f"accession {accession!r} appears twice in filings.recent"
                )
            seen_accessions.add(accession)
            if not _ACCESSION_RE.fullmatch(accession):
                raise AdapterError(
                    SCHEMA_INVARIANT_VIOLATED,
                    f"filings.recent.accessionNumber[{index}] is not NNNNNNNNNN-NN-NNNNNN: {accession!r}",
                )
            filed_day = parse_date(filing_dates[index], f"filings.recent.filingDate[{index}]")
            if not forms[index].strip():
                raise AdapterError(
                    SCHEMA_VALUE_TYPE_MISMATCH, f"filings.recent.form[{index}] is empty"
                )
            if report_dates[index].strip():
                report_day = parse_date(report_dates[index], f"filings.recent.reportDate[{index}]")
                if report_day > filed_day:
                    raise AdapterError(
                        SCHEMA_INVARIANT_VIOLATED,
                        f"filings.recent.reportDate[{index}] {report_day} is after filingDate {filed_day}",
                    )
            if documents[index].strip() == "":
                raise AdapterError(
                    SCHEMA_VALUE_TYPE_MISMATCH,
                    f"filings.recent.primaryDocument[{index}] is empty",
                )
            available = end_of_utc_day(filed_day)
            acceptance_text = acceptance[index].strip()
            if acceptance_text:
                any_acceptance = True
                event_time = parse_utc(
                    acceptance_text, f"filings.recent.acceptanceDateTime[{index}]"
                )
                if event_time > available:
                    raise AdapterError(
                        SCHEMA_INVARIANT_VIOLATED,
                        f"acceptanceDateTime[{index}] {event_time.isoformat()} is after the "
                        "end-of-filed-day availability upper bound",
                    )
            else:
                event_time = midnight_utc(filed_day)
            timings = timings_from_evidence(
                event_time,
                self._filing_evidence(filed_day, "SEC submissions filingDate (date only)"),
                effective_time_utc=event_time,
            )
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
                    "acceptanceDateTime is EDGAR acceptance only; it is never "
                    "treated as proof of public dissemination",
                )
            )
        return self.make_output(
            dataset_id="submissions",
            request_id=response.request_id,
            response=response,
            records=records,
            notes=notes,
        )

    # -- company facts --------------------------------------------------------

    def parse_company_facts(self, response: RawResponse) -> AdapterOutput:
        validate_response(response, allowed_content_types=("application/json",))
        content = require_mapping(response.json(), "companyfacts")
        require_keys(content, {"cik", "facts"}, "companyfacts")
        entity_id = self._entity_id(content["cik"])
        self._check_url_entity(response, entity_id, "companyfacts")
        facts = require_mapping(content["facts"], "companyfacts.facts")

        records: list = []
        seen_fact_keys: set[tuple] = set()
        skipped_duration = 0
        for taxonomy in sorted(facts):
            tags = require_mapping(facts[taxonomy], f"facts[{taxonomy}]")
            for tag in sorted(tags):
                meta = require_mapping(tags[tag], f"facts[{taxonomy}][{tag}]")
                require_keys(meta, {"units"}, f"facts[{taxonomy}][{tag}]")
                for label_key in ("label", "description"):
                    if label_key in meta and not isinstance(meta[label_key], str):
                        raise AdapterError(
                            SCHEMA_VALUE_TYPE_MISMATCH,
                            f"facts[{taxonomy}][{tag}].{label_key} must be a string",
                        )
                reject_unknown_keys(meta, _FACT_META_ALLOWED_KEYS, f"facts[{taxonomy}][{tag}]")
                units = require_mapping(meta["units"], f"facts[{taxonomy}][{tag}].units")
                for unit_name in sorted(units):
                    fact_list = units[unit_name]
                    if not isinstance(fact_list, list):
                        raise AdapterError(
                            SCHEMA_VALUE_TYPE_MISMATCH,
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
                        records.append(
                            self._instant_fact_record(
                                response,
                                entity_id=entity_id,
                                taxonomy=taxonomy,
                                tag=tag,
                                unit_name=unit_name,
                                context=context,
                                entry=entry,
                                seen_fact_keys=seen_fact_keys,
                            )
                        )

        notes = [
            AdapterNote(
                SEC_FILED_DATE_ONLY_NOT_EXACT_AVAILABILITY,
                "availability is the end of the filed UTC day: a conservative "
                "upper bound, never an exact market availability claim",
            )
        ]
        if skipped_duration:
            notes.append(
                AdapterNote(
                    SEC_DURATION_FACTS_SKIPPED_V1,
                    f"{skipped_duration} duration facts carry a period start and "
                    "are not mapped as instants in V1",
                )
            )
        return self.make_output(
            dataset_id="company_facts",
            request_id=response.request_id,
            response=response,
            records=records,
            notes=notes,
        )

    def _instant_fact_record(
        self,
        response: RawResponse,
        *,
        entity_id: str,
        taxonomy: str,
        tag: str,
        unit_name: str,
        context: str,
        entry: dict,
        seen_fact_keys: set[tuple],
    ):
        end_day = parse_date(require_str(entry, "end", context), f"{context}.end")
        filed_day = parse_date(require_str(entry, "filed", context), f"{context}.filed")
        if filed_day < end_day:
            raise AdapterError(
                SCHEMA_INVARIANT_VIOLATED,
                f"{context}.filed {filed_day} precedes period end {end_day}",
            )
        accn = require_str(entry, "accn", context)
        if not _ACCESSION_RE.fullmatch(accn):
            raise AdapterError(
                SCHEMA_INVARIANT_VIOLATED,
                f"{context}.accn is not NNNNNNNNNN-NN-NNNNNN: {accn!r}",
            )
        if not require_str(entry, "fp", context).strip():
            raise AdapterError(SCHEMA_VALUE_TYPE_MISMATCH, f"{context}.fp is empty")
        if not require_str(entry, "form", context).strip():
            raise AdapterError(SCHEMA_VALUE_TYPE_MISMATCH, f"{context}.form is empty")
        fiscal_year = entry["fy"]
        if isinstance(fiscal_year, bool) or not isinstance(fiscal_year, int):
            raise AdapterError(SCHEMA_VALUE_TYPE_MISMATCH, f"{context}.fy must be an integer")
        value = require_number(entry, "val", context)
        if "frame" in entry and not isinstance(entry["frame"], str):
            raise AdapterError(SCHEMA_VALUE_TYPE_MISMATCH, f"{context}.frame must be a string")

        fact_key = (taxonomy, tag, unit_name, accn, end_day, filed_day)
        if fact_key in seen_fact_keys:
            raise AdapterError(DUPLICATE_RECORD_ID, f"duplicate company fact {fact_key}")
        seen_fact_keys.add(fact_key)

        event_time = midnight_utc(end_day)
        timings = timings_from_evidence(
            event_time,
            self._filing_evidence(filed_day, "SEC company facts filed date (date only)"),
            effective_time_utc=event_time,
        )
        return self.make_record(
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
