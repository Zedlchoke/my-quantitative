"""ECB Data API (SDMX) adapter: official euro-area reference data (DISCOVERY_ONLY).

The SDMX payload carries no historical availability timestamp.  A message
``prepared`` time is retrieval-like metadata and never substitutes for
availability: parsing refuses records unless an owner-supplied
``ReleaseEvidence`` is provided.  ECB data never auto-unlocks a strategy.
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
    extract_sdmx_json_series,
    midnight_utc,
    parse_date,
    parse_utc,
    require_keys,
    require_mapping,
    require_str,
    sdmx_series_id,
    timings_from_evidence,
)

ECB_PREPARED_TIME_NOT_AVAILABILITY_PROOF = "ECB_PREPARED_TIME_NOT_AVAILABILITY_PROOF"
ECB_AVAILABILITY_NOT_EXACT = "ECB_AVAILABILITY_NOT_EXACT"
ECB_DATA_NOT_CARRY_AUTHORIZATION = "ECB_DATA_NOT_CARRY_AUTHORIZATION"

_BASE = "https://data-api.ecb.europa.eu/service"


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
            raise AdapterError("SCHEMA_INVARIANT_VIOLATED", f"dataflow {dataflow!r} must be alphanumeric")
        if not key or any(character.isspace() or character in "?#" for character in key):
            raise AdapterError("SCHEMA_INVARIANT_VIOLATED", f"series key {series_key!r} is not deterministic")
        query: list[tuple[str, str]] = []
        for name, value in (("startPeriod", start_period), ("endPeriod", end_period)):
            if value is not None:
                parse_date(value, name)
                query.append((name, value))
        return RequestSpec(source_id=self.source_id, url=f"{_BASE}/data/{flow}/{key}", query=tuple(query))

    def parse_series(
        self,
        response: RawResponse,
        *,
        dataflow: str,
        release_evidence: ReleaseEvidence | None,
        unit: str,
    ) -> AdapterOutput:
        payload = response.json()
        rows = extract_sdmx_json_series(payload)
        header = require_mapping(payload["header"], "sdmx.header")
        require_keys(header, {"id", "prepared"}, "sdmx.header")
        parse_utc(require_str(header, "prepared", "sdmx.header"), "sdmx.header.prepared")

        resolved = sdmx_series_id(payload, rows[0]["series_key"]) if rows else ""
        entity_id = f"ECB:{dataflow.strip().upper()}:{resolved}" if resolved else "ECB:UNKNOWN"

        records: list = []
        seen: set[tuple[str, str]] = set()
        for row in rows:
            day = parse_date(row["time_period"], "TIME_PERIOD")
            if row["time_period"] in seen:
                raise AdapterError("DUPLICATE_RECORD_ID", f"observation {row['time_period']} appears twice")
            seen.add(row["time_period"])
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
                "SDMX header.prepared is message metadata and never substitutes for availability",
            ),
            AdapterNote(
                ECB_DATA_NOT_CARRY_AUTHORIZATION,
                "ECB data does not authorize any strategy, including carry",
            ),
        ]
        if release_evidence is not None and release_evidence.basis is AvailabilityBasis.DATE_ONLY_UPPER_BOUND:
            notes.append(
                AdapterNote(
                    ECB_AVAILABILITY_NOT_EXACT,
                    f"availability comes from {release_evidence.captured_from!r} as an upper bound",
                )
            )
        return self.make_output(
            dataset_id="sdmx_series",
            request_id=response.request_id,
            response=response,
            records=records,
            notes=notes,
        )
