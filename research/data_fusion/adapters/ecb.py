"""ECB Data API (SDMX-JSON) adapter: euro-area reference statistics.

DISCOVERY_ONLY.  The ECB data payload carries no historical availability
timestamp of any kind: ``header.prepared`` is message *metadata* (when the
SDMX message was assembled) and never substitutes for availability evidence.
Records are therefore refused outright unless the caller supplies
owner-captured ``ReleaseEvidence``; date-only evidence may only produce the
conservative end-of-UTC-day upper bound.  A passing ECB adapter never
authorizes scoring or any strategy family (carry included).
"""

from __future__ import annotations

from ..authority import AuthorityStatus
from .base import (
    MISSING_AVAILABLE_TIME_EVIDENCE,
    SCHEMA_INVARIANT_VIOLATED,
    SCHEMA_TIMESTAMP_INVALID,
    AdapterError,
    AdapterNote,
    AdapterOutput,
    AvailabilityBasis,
    RawResponse,
    RateLimitPolicy,
    ReleaseEvidence,
    RequestSpec,
    SourceAdapter,
    extract_sdmx_json_series,
    midnight_utc,
    parse_date,
    parse_utc,
    require_keys,
    require_mapping,
    require_str,
    sdmx_series_id,
    timings_from_evidence,
    validate_response,
)

ECB_PREPARED_TIME_NOT_AVAILABILITY_PROOF = "ECB_PREPARED_TIME_NOT_AVAILABILITY_PROOF"
ECB_AVAILABILITY_NOT_EXACT = "ECB_AVAILABILITY_NOT_EXACT"
ECB_DATA_NOT_CARRY_AUTHORIZATION = "ECB_DATA_NOT_CARRY_AUTHORIZATION"

_BASE = "https://data-api.ecb.europa.eu/service"
_SDMX_CONTENT_TYPES = ("application/vnd.sdmx.data+json", "application/json")


class EcbAdapter(SourceAdapter):
    source_id = "ECB_SDMX"
    parser_version = "ecb-adapter-1.0.0"
    license_id = "ecb-statistical-terms-v1"
    entitlement_id = "anonymous-no-key"
    authority_status = AuthorityStatus.DOCUMENTED_CANDIDATE

    @classmethod
    def default_rate_limit(cls) -> RateLimitPolicy:
        return RateLimitPolicy(
            source_id=cls.source_id,
            documented_limit="ECB data API fair use; no published per-second quota",
            min_interval_seconds=1.0,
            max_retries=2,
            retry_backoff_seconds=2.0,
            retry_status_codes=(429, 500, 502, 503),
        )

    def build_series_request(
        self,
        dataflow: str,
        series_key: str,
        *,
        start_period: str | None = None,
        end_period: str | None = None,
    ) -> RequestSpec:
        flow = dataflow.strip().upper()
        key = series_key.strip()
        if not flow.isalnum():
            raise AdapterError(SCHEMA_INVARIANT_VIOLATED, f"dataflow {dataflow!r} must be alphanumeric")
        if not key or any(character.isspace() or character in "?#" for character in key):
            raise AdapterError(SCHEMA_INVARIANT_VIOLATED, f"series key {series_key!r} is not deterministic")
        query: list[tuple[str, str]] = []
        for name, value in (("startPeriod", start_period), ("endPeriod", end_period)):
            if value is not None:
                parse_date(value, name)
                query.append((name, value))
        return RequestSpec(
            source_id=self.source_id,
            url=f"{_BASE}/data/{flow}/{key}",
            query=tuple(query),
            headers=(("accept", "application/vnd.sdmx.data+json"),),
        )

    def parse_series(
        self,
        response: RawResponse,
        *,
        dataflow: str,
        release_evidence: ReleaseEvidence | None,
        unit: str,
    ) -> AdapterOutput:
        if release_evidence is None:
            raise AdapterError(
                MISSING_AVAILABLE_TIME_EVIDENCE,
                "ECB payloads carry no historical availability; owner-supplied evidence is required",
            )
        validate_response(response, allowed_content_types=_SDMX_CONTENT_TYPES)
        payload = response.json()
        rows = extract_sdmx_json_series(payload)
        if not rows:
            raise AdapterError(SCHEMA_INVARIANT_VIOLATED, "payload carries no observations")

        # header.prepared is validated for shape only: it is message metadata,
        # deliberately never read back as an availability timestamp.
        header = require_mapping(payload["header"], "sdmx.header")
        require_keys(header, {"id", "prepared"}, "sdmx.header")
        parse_utc(require_str(header, "prepared", "sdmx.header"), "sdmx.header.prepared")

        series_keys = {row["series_key"] for row in rows}
        if len(series_keys) != 1:
            raise AdapterError(
                SCHEMA_INVARIANT_VIOLATED,
                f"one request must resolve to exactly one series, got {sorted(series_keys)}",
            )
        resolved = sdmx_series_id(payload, next(iter(series_keys)))
        entity_id = f"ECB:{dataflow.strip().upper()}:{resolved}"

        records: list = []
        seen: set[str] = set()
        for row in rows:
            if row["time_period"] in seen:
                raise AdapterError(
                    "DUPLICATE_RECORD_ID", f"observation {row['time_period']} appears twice in TIME_PERIOD"
                )
            seen.add(row["time_period"])
            day = parse_date(row["time_period"], "TIME_PERIOD")
            timings = timings_from_evidence(
                midnight_utc(day), release_evidence, effective_time_utc=midnight_utc(day)
            )
            records.append(
                self.make_record(
                    dataset_id="sdmx_series",
                    entity_id=entity_id,
                    field_name="observation",
                    value=row["value"],
                    unit=unit,
                    timings=timings,
                    retrieved_time_utc=response.retrieved_time_utc,
                    request_id=response.request_id,
                    raw_sha256=response.sha256_hex(),
                )
            )

        notes = [
            AdapterNote(
                ECB_PREPARED_TIME_NOT_AVAILABILITY_PROOF,
                "SDMX header.prepared is message metadata and is never used as availability",
            ),
            AdapterNote(
                ECB_DATA_NOT_CARRY_AUTHORIZATION,
                "ECB data does not authorize scoring or any strategy, including carry",
            ),
        ]
        if release_evidence.basis is AvailabilityBasis.DATE_ONLY_UPPER_BOUND:
            notes.append(
                AdapterNote(
                    ECB_AVAILABILITY_NOT_EXACT,
                    f"availability is the end-of-UTC-day upper bound from {release_evidence.captured_from!r}, "
                    "not an exact release time",
                )
            )
        return self.make_output(
            dataset_id="sdmx_series",
            request_id=response.request_id,
            response=response,
            records=records,
            notes=notes,
        )
