"""FRED/ALFRED vintage adapter (DISCOVERY_ONLY, key-gated).

ALFRED's ``realtime_start`` is the vintage date of an observation.  Vintage
dates are date-only, so availability uses the end of the vintage day as a
conservative upper bound and never claims an exact wire release time.  The
adapter is key-gated: requests require an ``api_key`` argument, but the key
is carried outside the canonical request identity, cache paths and logs, and
is never written anywhere.  The source stays ``CANDIDATE_NOT_AUTHORIZED``
until the owner provisions and authorizes a key.
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
    reject_unknown_keys,
    require_keys,
    require_mapping,
    require_str,
    timings_from_evidence,
)

FRED_VINTAGE_DATE_ONLY_NOT_EXACT_RELEASE_TIME = "FRED_VINTAGE_DATE_ONLY_NOT_EXACT_RELEASE_TIME"
FRED_MISSING_VALUE_MARKED_DOT = "FRED_MISSING_VALUE_MARKED_DOT"
FRED_KEY_GATED_CANDIDATE = "FRED_KEY_GATED_CANDIDATE"

_BASE = "https://api.stlouisfed.org"
_OBS_ALLOWED_KEYS = frozenset({"realtime_start", "realtime_end", "date", "value"})


class FredAdapter(SourceAdapter):
    source_id = "FRED_ALFRED"
    parser_version = "fred-adapter-1.0.0"
    license_id = "fred-terms-of-use-v1"
    entitlement_id = "api-key-required-not-provisioned"
    authority_status = AuthorityStatus.CANDIDATE_NOT_AUTHORIZED
    forbidden_fields = ("analyst_consensus", "wire_release_timestamp")

    @classmethod
    def default_rate_limit(cls) -> RateLimitPolicy:
        return RateLimitPolicy(
            source_id=cls.source_id,
            documented_limit="FRED API: 120 requests/minute with a key",
            min_interval_seconds=0.6,
            max_retries=2,
            retry_backoff_seconds=1.5,
            retry_status_codes=(429, 500, 502, 503),
        )

    @staticmethod
    def normalize_series_id(series_id: str) -> str:
        text = series_id.strip().upper()
        if not text or any(not (character.isalnum() or character == "_") for character in text):
            raise AdapterError(
                "SCHEMA_INVARIANT_VIOLATED", f"series id {series_id!r} is not a FRED series id"
            )
        return text

    def build_vintagedates_request(self, series_id: str, *, api_key: str) -> RequestSpec:
        if not api_key or not api_key.strip():
            raise AdapterError("CREDENTIAL_REQUIRED", "FRED requests require an api_key argument")
        return RequestSpec(
            source_id=self.source_id,
            url=f"{_BASE}/fred/series/vintagedates",
            query=(("file_type", "json"), ("series_id", self.normalize_series_id(series_id))),
            credential_query=(("api_key", api_key),),
        )

    def build_alfred_observations_request(
        self,
        series_id: str,
        *,
        api_key: str,
        realtime_start: str | None = None,
        realtime_end: str | None = None,
    ) -> RequestSpec:
        if not api_key or not api_key.strip():
            raise AdapterError("CREDENTIAL_REQUIRED", "FRED requests require an api_key argument")
        query: list[tuple[str, str]] = [("file_type", "json"), ("series_id", self.normalize_series_id(series_id))]
        for name, value in (("realtime_start", realtime_start), ("realtime_end", realtime_end)):
            if value is not None:
                parse_date(value, name)
                query.append((name, value))
        return RequestSpec(
            source_id=self.source_id,
            url=f"{_BASE}/alfred/series/observations",
            query=tuple(query),
            credential_query=(("api_key", api_key),),
        )

    @staticmethod
    def _refuse_error_payload(payload: object) -> None:
        if isinstance(payload, dict) and ("error_code" in payload or "error_message" in payload):
            code = payload.get("error_code", "unknown")
            message = payload.get("error_message", "no message")
            raise AdapterError("UPSTREAM_ERROR_PAYLOAD", f"FRED API error {code}: {message}")

    def parse_vintagedates(self, response: RawResponse, *, series_id: str) -> AdapterOutput:
        payload = response.json()
        self._refuse_error_payload(payload)
        if not isinstance(payload, list) or not payload:
            raise AdapterError("SCHEMA_VALUE_TYPE_MISMATCH", "vintagedates payload must be a non-empty list")
        entity_id = f"FRED:{self.normalize_series_id(series_id)}"
        records: list = []
        seen: set[str] = set()
        for index, entry in enumerate(payload):
            day = parse_date(entry, f"vintagedates[{index}]")
            if entry in seen:
                raise AdapterError("DUPLICATE_RECORD_ID", f"vintage date {entry!r} appears twice")
            seen.add(entry)
            evidence = ReleaseEvidence(
                captured_from="ALFRED vintage date (date only)",
                available_time_utc=end_of_utc_day(day),
                basis=AvailabilityBasis.DATE_ONLY_UPPER_BOUND,
            )
            timings = timings_from_evidence(midnight_utc(day), evidence)
            records.append(
                self.make_record(
                    dataset_id="vintagedates",
                    entity_id=entity_id,
                    field_name="vintage_date",
                    value=day.isoformat(),
                    unit="DATE",
                    timings=timings,
                    retrieved_time_utc=response.retrieved_time_utc,
                    request_id=response.request_id,
                    raw_sha256=response.sha256_hex(),
                )
            )
        notes = [
            AdapterNote(
                FRED_VINTAGE_DATE_ONLY_NOT_EXACT_RELEASE_TIME,
                "vintage dates are date-only; exact wire release times are never claimed",
            ),
            AdapterNote(
                FRED_KEY_GATED_CANDIDATE,
                "source remains CANDIDATE_NOT_AUTHORIZED until the owner authorizes a key",
            ),
        ]
        return self.make_output(
            dataset_id="vintagedates",
            request_id=response.request_id,
            response=response,
            records=records,
            notes=notes,
        )

    def parse_observations(
        self, response: RawResponse, *, series_id: str, unit: str
    ) -> AdapterOutput:
        payload = response.json()
        self._refuse_error_payload(payload)
        if not isinstance(payload, list) or not payload:
            raise AdapterError("SCHEMA_VALUE_TYPE_MISMATCH", "observations payload must be a non-empty list")
        entity_id = f"FRED:{self.normalize_series_id(series_id)}"
        records: list = []
        seen: set[tuple[str, str]] = set()
        missing_dot = 0
        for index, entry in enumerate(payload):
            context = f"observations[{index}]"
            row = require_mapping(entry, context)
            require_keys(row, {"realtime_start", "date", "value"}, context)
            reject_unknown_keys(row, _OBS_ALLOWED_KEYS, context)
            vintage_day = parse_date(require_str(row, "realtime_start", context), f"{context}.realtime_start")
            obs_day = parse_date(require_str(row, "date", context), f"{context}.date")
            key = (row["date"], row["realtime_start"])
            if key in seen:
                raise AdapterError("DUPLICATE_RECORD_ID", f"duplicate observation {key}")
            seen.add(key)
            raw_value = row["value"]
            if raw_value == ".":
                missing_dot += 1
                value = None
            else:
                try:
                    value = float(raw_value)
                except (TypeError, ValueError):
                    raise AdapterError(
                        "SCHEMA_VALUE_TYPE_MISMATCH", f"{context}.value is not numeric: {raw_value!r}"
                    )
            evidence = ReleaseEvidence(
                captured_from="ALFRED vintage date (date only)",
                available_time_utc=end_of_utc_day(vintage_day),
                basis=AvailabilityBasis.DATE_ONLY_UPPER_BOUND,
            )
            timings = timings_from_evidence(
                midnight_utc(obs_day), evidence, effective_time_utc=midnight_utc(obs_day)
            )
            records.append(
                self.make_record(
                    dataset_id="alfred_observations",
                    entity_id=entity_id,
                    field_name="observation",
                    value=value,
                    unit=unit,
                    timings=timings,
                    retrieved_time_utc=response.retrieved_time_utc,
                    request_id=response.request_id,
                    raw_sha256=response.sha256_hex(),
                )
            )
        notes = [
            AdapterNote(
                FRED_VINTAGE_DATE_ONLY_NOT_EXACT_RELEASE_TIME,
                "vintage dates are date-only; exact wire release times are never claimed",
            ),
            AdapterNote(
                FRED_KEY_GATED_CANDIDATE,
                "source remains CANDIDATE_NOT_AUTHORIZED until the owner authorizes a key",
            ),
        ]
        if missing_dot:
            notes.append(
                AdapterNote(FRED_MISSING_VALUE_MARKED_DOT, f"{missing_dot} observations carry '.' and map to null")
            )
        return self.make_output(
            dataset_id="alfred_observations",
            request_id=response.request_id,
            response=response,
            records=records,
            notes=notes,
        )
