"""BIS WS_CBPOL policy-rate adapter (SDMX-JSON over the BIS data API).

BIS CBPOL observations are keyed by the *effective* date of a policy rate,
so ``effective_time_utc`` equals the observation's midnight UTC.  Effective-
ness is not availability: the payload carries no historical release time,
so records fail closed without owner-captured ``ReleaseEvidence`` and
date-only evidence only ever yields the end-of-UTC-day upper bound.  A
policy-rate series never self-authorizes a carry strategy
(``BIS_POLICY_RATE_NOT_CARRY_AUTHORIZATION``).
"""

from __future__ import annotations

from ..authority import AuthorityStatus
from .base import (
    MISSING_AVAILABLE_TIME_EVIDENCE,
    SCHEMA_INVARIANT_VIOLATED,
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
    sdmx_series_id,
    timings_from_evidence,
    validate_response,
)

BIS_EFFECTIVE_DATE_SEMANTICS = "BIS_EFFECTIVE_DATE_SEMANTICS"
BIS_AVAILABILITY_NOT_EXACT = "BIS_AVAILABILITY_NOT_EXACT"
BIS_POLICY_RATE_NOT_CARRY_AUTHORIZATION = "BIS_POLICY_RATE_NOT_CARRY_AUTHORIZATION"

_BASE = "https://data.bis.org/api/v2"
_SDMX_CONTENT_TYPES = ("application/vnd.sdmx.data+json", "application/json")


class BisAdapter(SourceAdapter):
    source_id = "BIS_CBPOL"
    parser_version = "bis-adapter-1.0.0"
    license_id = "bis-terms-public-v1"
    entitlement_id = "anonymous-no-key"
    authority_status = AuthorityStatus.DOCUMENTED_CANDIDATE

    @classmethod
    def default_rate_limit(cls) -> RateLimitPolicy:
        return RateLimitPolicy(
            source_id=cls.source_id,
            documented_limit="BIS public data API fair use; no published per-second quota",
            min_interval_seconds=1.0,
            max_retries=2,
            retry_backoff_seconds=2.0,
            retry_status_codes=(429, 500, 502, 503),
        )

    def build_policy_rate_request(
        self,
        series_key: str,
        *,
        start_period: str | None = None,
        end_period: str | None = None,
    ) -> RequestSpec:
        key = series_key.strip()
        if not key or any(character.isspace() or character in "?#" for character in key):
            raise AdapterError(SCHEMA_INVARIANT_VIOLATED, f"series key {series_key!r} is not deterministic")
        query: list[tuple[str, str]] = []
        for name, value in (("startPeriod", start_period), ("endPeriod", end_period)):
            if value is not None:
                parse_date(value, name)
                query.append((name, value))
        return RequestSpec(
            source_id=self.source_id,
            url=f"{_BASE}/data/dataflow/BIS/WS_CBPOL/1.0/{key}",
            query=tuple(query),
            headers=(("accept", "application/vnd.sdmx.data+json"),),
        )

    def parse_policy_rates(
        self,
        response: RawResponse,
        *,
        release_evidence: ReleaseEvidence | None,
        unit: str = "PERCENT_PER_ANNUM",
    ) -> AdapterOutput:
        if release_evidence is None:
            raise AdapterError(
                MISSING_AVAILABLE_TIME_EVIDENCE,
                "BIS payloads carry no historical availability; owner-supplied evidence is required",
            )
        validate_response(response, allowed_content_types=_SDMX_CONTENT_TYPES)
        payload = response.json()
        rows = extract_sdmx_json_series(payload)
        if not rows:
            raise AdapterError(SCHEMA_INVARIANT_VIOLATED, "payload carries no observations")

        series_keys = {row["series_key"] for row in rows}
        if len(series_keys) != 1:
            raise AdapterError(
                SCHEMA_INVARIANT_VIOLATED,
                f"one request must resolve to exactly one series, got {sorted(series_keys)}",
            )
        resolved = sdmx_series_id(payload, next(iter(series_keys)))
        entity_id = f"BIS:WS_CBPOL:{resolved}"

        records: list = []
        seen: set[str] = set()
        for row in rows:
            if row["time_period"] in seen:
                raise AdapterError(
                    "DUPLICATE_RECORD_ID", f"observation {row['time_period']} appears twice in TIME_PERIOD"
                )
            seen.add(row["time_period"])
            effective_day = parse_date(row["time_period"], "TIME_PERIOD")
            # CBPOL dates are effective dates: effectiveness == observation date.
            timings = timings_from_evidence(
                midnight_utc(effective_day),
                release_evidence,
                effective_time_utc=midnight_utc(effective_day),
            )
            records.append(
                self.make_record(
                    dataset_id="policy_rates",
                    entity_id=entity_id,
                    field_name="policy_rate",
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
                BIS_EFFECTIVE_DATE_SEMANTICS,
                "CBPOL observation dates are policy-rate effective dates; effective time == event time",
            ),
            AdapterNote(
                BIS_POLICY_RATE_NOT_CARRY_AUTHORIZATION,
                "BIS policy rates do not authorize scoring and never auto-unlock a carry strategy",
            ),
        ]
        if release_evidence.basis is AvailabilityBasis.DATE_ONLY_UPPER_BOUND:
            notes.append(
                AdapterNote(
                    BIS_AVAILABILITY_NOT_EXACT,
                    f"availability is the end-of-UTC-day upper bound from {release_evidence.captured_from!r}, "
                    "not an exact release time",
                )
            )
        return self.make_output(
            dataset_id="policy_rates",
            request_id=response.request_id,
            response=response,
            records=records,
            notes=notes,
        )
