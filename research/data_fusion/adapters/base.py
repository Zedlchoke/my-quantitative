"""Adapter foundation shared by every free data source adapter.

Adapters are network-free at test time: all HTTP interaction goes through an
injected transport, and fixtures carry recorded or hand-written bytes.  A
passing adapter never raises a source's authority; authority stays with
``research.data_fusion.authority`` and the owner.  Discovery here is
DISCOVERY_ONLY: HTTP 200 from a public endpoint is not authorization.

Fail-closed contracts implemented here:

- requests are HTTPS-only GET with a deterministic canonical identity;
- credentials are never part of request identity, cache paths or logs;
- missing historical availability evidence refuses records outright;
- date-only evidence may only produce a conservative upper bound, never an
  exact availability claim;
- schema mismatches are rejected, never silently coerced.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from enum import Enum
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, ClassVar, Iterable, Protocol
import urllib.parse

from ..models import NormalizedRecord, canonical_json_bytes, require_utc


# ---------------------------------------------------------------------------
# Stable reason-code vocabulary
# ---------------------------------------------------------------------------

NON_HTTPS_REQUEST_REFUSED = "NON_HTTPS_REQUEST_REFUSED"
NON_GET_METHOD_REFUSED = "NON_GET_METHOD_REFUSED"
CREDENTIAL_REQUIRED = "CREDENTIAL_REQUIRED"
CREDENTIAL_IN_REQUEST_IDENTITY = "CREDENTIAL_IN_REQUEST_IDENTITY"
HTTP_STATUS_UNEXPECTED = "HTTP_STATUS_UNEXPECTED"
CONTENT_TYPE_UNEXPECTED = "CONTENT_TYPE_UNEXPECTED"
RESPONSE_BODY_NOT_JSON = "RESPONSE_BODY_NOT_JSON"
MISSING_AVAILABLE_TIME_EVIDENCE = "MISSING_AVAILABLE_TIME_EVIDENCE"
NON_EXACT_AVAILABLE_TIME_FORBIDDEN = "NON_EXACT_AVAILABLE_TIME_FORBIDDEN"
SCHEMA_FIELD_MISSING = "SCHEMA_FIELD_MISSING"
SCHEMA_UNKNOWN_FIELD = "SCHEMA_UNKNOWN_FIELD"
SCHEMA_VALUE_TYPE_MISMATCH = "SCHEMA_VALUE_TYPE_MISMATCH"
SCHEMA_TIMESTAMP_INVALID = "SCHEMA_TIMESTAMP_INVALID"
SCHEMA_INVARIANT_VIOLATED = "SCHEMA_INVARIANT_VIOLATED"
DUPLICATE_RECORD_ID = "DUPLICATE_RECORD_ID"
FORBIDDEN_INFERENCE_FIELD = "FORBIDDEN_INFERENCE_FIELD"
UPSTREAM_ERROR_PAYLOAD = "UPSTREAM_ERROR_PAYLOAD"


class AdapterError(ValueError):
    """Fail-closed adapter refusal carrying a stable reason code."""

    def __init__(self, code: str, message: str | None = None) -> None:
        self.code = code
        super().__init__(message if message is not None else code)


# ---------------------------------------------------------------------------
# Strict parsing helpers
# ---------------------------------------------------------------------------


def parse_utc(value: str, context: str) -> datetime:
    if not isinstance(value, str):
        raise AdapterError(SCHEMA_VALUE_TYPE_MISMATCH, f"{context} must be an ISO-8601 string")
    text = value.strip()
    if not text:
        raise AdapterError(SCHEMA_TIMESTAMP_INVALID, f"{context} is empty")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        raise AdapterError(SCHEMA_TIMESTAMP_INVALID, f"{context} is not ISO-8601: {value!r}")
    try:
        return require_utc(parsed, context)
    except ValueError as exc:
        raise AdapterError(SCHEMA_TIMESTAMP_INVALID, str(exc))


def parse_date(value: str, context: str) -> date:
    if not isinstance(value, str):
        raise AdapterError(SCHEMA_VALUE_TYPE_MISMATCH, f"{context} must be a YYYY-MM-DD string")
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        raise AdapterError(SCHEMA_TIMESTAMP_INVALID, f"{context} is not YYYY-MM-DD: {value!r}")


def midnight_utc(day: date) -> datetime:
    return datetime.combine(day, time(0, 0, 0), tzinfo=timezone.utc)


def end_of_utc_day(day: date) -> datetime:
    return datetime.combine(day, time(23, 59, 59), tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Availability evidence
# ---------------------------------------------------------------------------


class AvailabilityBasis(str, Enum):
    EXACT = "EXACT"
    DATE_ONLY_UPPER_BOUND = "DATE_ONLY_UPPER_BOUND"


@dataclass(frozen=True, slots=True)
class ReleaseEvidence:
    """Owner-supplied historical availability evidence.

    Adapters never invent availability; they may only consume evidence that
    an owner captured from a release calendar or equivalent proof.
    """

    captured_from: str
    available_time_utc: datetime
    basis: AvailabilityBasis

    def __post_init__(self) -> None:
        if not self.captured_from.strip():
            raise AdapterError(MISSING_AVAILABLE_TIME_EVIDENCE, "captured_from must name the evidence source")
        require_utc(self.available_time_utc, "available_time_utc")


def date_only_evidence(captured_from: str, day: date) -> ReleaseEvidence:
    """Conservative evidence for date-only proof: end of the UTC day.

    Nothing dated only by ``day`` can be treated as available earlier than
    that, so the upper bound can never cause future-knowledge leakage.
    """

    return ReleaseEvidence(
        captured_from=captured_from,
        available_time_utc=end_of_utc_day(day),
        basis=AvailabilityBasis.DATE_ONLY_UPPER_BOUND,
    )


@dataclass(frozen=True, slots=True)
class Timings:
    event_time_utc: datetime
    available_time_utc: datetime
    effective_time_utc: datetime | None
    vintage_time_utc: datetime
    availability_basis: AvailabilityBasis

    def require_exact_availability(self) -> "Timings":
        if self.availability_basis is not AvailabilityBasis.EXACT:
            raise AdapterError(
                NON_EXACT_AVAILABLE_TIME_FORBIDDEN,
                "exact market availability is required but evidence is date-only",
            )
        return self


def timings_from_evidence(
    event_time_utc: datetime,
    evidence: ReleaseEvidence | None,
    *,
    effective_time_utc: datetime | None = None,
) -> Timings:
    if evidence is None:
        raise AdapterError(
            MISSING_AVAILABLE_TIME_EVIDENCE,
            "no historical availability evidence was supplied; records are refused",
        )
    require_utc(event_time_utc, "event_time_utc")
    return Timings(
        event_time_utc=event_time_utc,
        available_time_utc=evidence.available_time_utc,
        effective_time_utc=effective_time_utc,
        vintage_time_utc=evidence.available_time_utc,
        availability_basis=evidence.basis,
    )


# ---------------------------------------------------------------------------
# Requests and responses
# ---------------------------------------------------------------------------

_FORBIDDEN_HEADER_NAMES = frozenset(
    {"authorization", "proxy-authorization", "cookie", "x-api-key", "api-key"}
)


@dataclass(frozen=True, slots=True)
class RequestSpec:
    """Deterministic HTTPS-only GET request.

    ``credential_query`` travels with the request but is excluded from the
    canonical payload, the request identity and every cache path.
    """

    source_id: str
    url: str
    query: tuple[tuple[str, str], ...] = ()
    headers: tuple[tuple[str, str], ...] = ()
    credential_query: tuple[tuple[str, str], ...] = ()
    method: str = "GET"

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise AdapterError(SCHEMA_INVARIANT_VIOLATED, "source_id must be non-empty")
        if self.method != "GET":
            raise AdapterError(NON_GET_METHOD_REFUSED, f"only GET is allowed, got {self.method!r}")
        parsed = urllib.parse.urlsplit(self.url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise AdapterError(NON_HTTPS_REQUEST_REFUSED, f"url is not HTTPS: {self.url!r}")
        for key, value in self.query + self.headers + self.credential_query:
            if not key:
                raise AdapterError(SCHEMA_INVARIANT_VIOLATED, "empty query/header key")
        for name, _ in self.headers:
            if name.lower() in _FORBIDDEN_HEADER_NAMES:
                raise AdapterError(
                    CREDENTIAL_IN_REQUEST_IDENTITY,
                    f"credential-like header {name!r} is refused",
                )
        credential_values = {value for _, value in self.credential_query}
        if credential_values and any(value in credential_values for _, value in self.query):
            raise AdapterError(
                CREDENTIAL_IN_REQUEST_IDENTITY,
                "a credential value leaked into the canonical query",
            )

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "method": self.method,
            "query": sorted(self.query),
            "source_id": self.source_id,
            "url": self.url,
        }

    def request_id(self) -> str:
        return sha256(canonical_json_bytes(self.canonical_payload())).hexdigest()

    def full_url(self) -> str:
        pairs = self.query + self.credential_query
        if not pairs:
            return self.url
        return f"{self.url}?{urllib.parse.urlencode(pairs)}"


class HttpTransport(Protocol):
    """Anything that can return recorded bytes for a request; no real I/O in tests."""

    def fetch(self, request: RequestSpec, retrieved_time_utc: datetime) -> "RawResponse": ...


@dataclass(frozen=True, slots=True)
class RawResponse:
    request_id: str
    url: str
    status: int
    reason: str
    headers: tuple[tuple[str, str], ...]
    body: bytes
    retrieved_time_utc: datetime

    def __post_init__(self) -> None:
        require_utc(self.retrieved_time_utc, "retrieved_time_utc")
        if not isinstance(self.body, bytes):
            raise AdapterError(SCHEMA_VALUE_TYPE_MISMATCH, "response body must be bytes")

    def sha256_hex(self) -> str:
        return sha256(self.body).hexdigest()

    def header(self, name: str) -> str | None:
        lowered = name.lower()
        for key, value in self.headers:
            if key.lower() == lowered:
                return value
        return None

    def json(self) -> Any:
        try:
            return json.loads(self.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AdapterError(RESPONSE_BODY_NOT_JSON, f"body is not JSON: {exc}")


def validate_response(
    response: RawResponse,
    *,
    expected_status: int = 200,
    allowed_content_types: tuple[str, ...],
) -> None:
    if response.status != expected_status:
        raise AdapterError(
            HTTP_STATUS_UNEXPECTED,
            f"expected HTTP {expected_status}, got {response.status} ({response.reason})",
        )
    content_type = (response.header("content-type") or "").split(";")[0].strip().lower()
    if content_type not in {item.lower() for item in allowed_content_types}:
        raise AdapterError(
            CONTENT_TYPE_UNEXPECTED,
            f"content-type {content_type!r} not in {sorted(allowed_content_types)}",
        )


@dataclass(frozen=True, slots=True)
class RateLimitPolicy:
    """Declared retrieval politeness; adapters never silently exceed it."""

    source_id: str
    documented_limit: str
    min_interval_seconds: float
    max_retries: int
    retry_backoff_seconds: float
    retry_status_codes: tuple[int, ...] = ()

    def should_retry(self, status: int, attempt: int) -> bool:
        if attempt >= self.max_retries:
            return False
        return status in self.retry_status_codes

    def describe(self) -> str:
        return (
            f"{self.source_id}: documented limit {self.documented_limit!r}; "
            f"client min interval {self.min_interval_seconds}s; "
            f"retry up to {self.max_retries}x on {self.retry_status_codes} "
            f"with {self.retry_backoff_seconds}s backoff"
        )


class RawCacheStore:
    """Local raw-byte cache rooted outside every Git work tree.

    The caller owns the root path; adapters never write inside the repository
    and raw cache files are never committed.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def path_for(self, source_id: str, request_id: str) -> Path:
        return self.root / source_id / f"{request_id}.raw"

    def store(self, source_id: str, request_id: str, body: bytes) -> Path:
        path = self.path_for(source_id, request_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        return path

    def load(self, source_id: str, request_id: str) -> bytes | None:
        path = self.path_for(source_id, request_id)
        if not path.exists():
            return None
        return path.read_bytes()


# ---------------------------------------------------------------------------
# Schema helpers (rejection, never coercion)
# ---------------------------------------------------------------------------


def require_mapping(value: Any, context: str) -> dict:
    if not isinstance(value, dict):
        raise AdapterError(SCHEMA_VALUE_TYPE_MISMATCH, f"{context} must be an object")
    return value


def require_keys(mapping: dict, required: Iterable[str], context: str) -> None:
    missing = sorted(set(required) - set(mapping))
    if missing:
        raise AdapterError(SCHEMA_FIELD_MISSING, f"{context} is missing fields {missing}")


def reject_unknown_keys(mapping: dict, allowed: Iterable[str], context: str) -> None:
    unknown = sorted(set(mapping) - set(allowed))
    if unknown:
        raise AdapterError(SCHEMA_UNKNOWN_FIELD, f"{context} has unknown fields {unknown}")


def require_str(mapping: dict, key: str, context: str) -> str:
    value = mapping[key]
    if not isinstance(value, str) or not value.strip():
        raise AdapterError(SCHEMA_VALUE_TYPE_MISMATCH, f"{context}.{key} must be a non-empty string")
    return value


def require_number(mapping: dict, key: str, context: str) -> float | int:
    value = mapping[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AdapterError(SCHEMA_VALUE_TYPE_MISMATCH, f"{context}.{key} must be numeric")
    return value


def require_str_list(mapping: dict, key: str, context: str) -> list[str]:
    value = mapping[key]
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise AdapterError(SCHEMA_VALUE_TYPE_MISMATCH, f"{context}.{key} must be a list of strings")
    return value


# ---------------------------------------------------------------------------
# Adapter base and output
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AdapterNote:
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class AdapterOutput:
    source_id: str
    dataset_id: str
    request_id: str
    raw_path: str
    raw_sha256: str
    retrieved_time_utc: datetime
    parser_version: str
    records: tuple[NormalizedRecord, ...]
    notes: tuple[AdapterNote, ...]

    def note_codes(self) -> tuple[str, ...]:
        return tuple(note.code for note in self.notes)


class SourceAdapter:
    """Base class for source adapters.

    Subclasses declare identity constants and implement ``build_*`` /
    ``parse_*`` methods.  ``forbidden_fields`` names dataset fields this
    source must never be mapped to (inference guards from the registry).
    """

    source_id: ClassVar[str]
    parser_version: ClassVar[str]
    license_id: ClassVar[str]
    entitlement_id: ClassVar[str]
    forbidden_fields: ClassVar[tuple[str, ...]] = ()

    def __init__(
        self,
        *,
        rate_limit: RateLimitPolicy | None = None,
        cache: RawCacheStore | None = None,
    ) -> None:
        self.rate_limit = rate_limit or self.default_rate_limit()
        self.cache = cache

    @classmethod
    def default_rate_limit(cls) -> RateLimitPolicy:
        raise NotImplementedError

    def refuse_forbidden_field(self, field_name: str) -> None:
        if field_name in self.forbidden_fields:
            raise AdapterError(
                FORBIDDEN_INFERENCE_FIELD,
                f"{self.source_id} must never produce field {field_name!r}",
            )

    def raw_path_for(self, request_id: str) -> str:
        return f"{self.source_id.lower()}/{request_id}.raw"

    def make_record(
        self,
        *,
        dataset_id: str,
        entity_id: str,
        field_name: str,
        value: Any,
        unit: str,
        timings: Timings,
        retrieved_time_utc: datetime,
        request_id: str,
        raw_sha256: str,
    ) -> NormalizedRecord:
        self.refuse_forbidden_field(field_name)
        return NormalizedRecord(
            source_id=self.source_id,
            dataset_id=dataset_id,
            entity_id=entity_id,
            field=field_name,
            value=value,
            unit=unit,
            event_time_utc=timings.event_time_utc,
            available_time_utc=timings.available_time_utc,
            effective_time_utc=timings.effective_time_utc,
            vintage_time_utc=timings.vintage_time_utc,
            retrieved_time_utc=retrieved_time_utc,
            raw_path=self.raw_path_for(request_id),
            raw_sha256=raw_sha256,
            license_id=self.license_id,
            entitlement_id=self.entitlement_id,
            normalizer_version=self.parser_version,
        )

    def make_output(
        self,
        *,
        dataset_id: str,
        request_id: str,
        response: RawResponse,
        records: list[NormalizedRecord],
        notes: list[AdapterNote],
    ) -> AdapterOutput:
        return AdapterOutput(
            source_id=self.source_id,
            dataset_id=dataset_id,
            request_id=request_id,
            raw_path=self.raw_path_for(request_id),
            raw_sha256=response.sha256_hex(),
            retrieved_time_utc=response.retrieved_time_utc,
            parser_version=self.parser_version,
            records=tuple(records),
            notes=tuple(notes),
        )


# ---------------------------------------------------------------------------
# Shared SDMX-JSON helpers (ECB data API, BIS data API)
# ---------------------------------------------------------------------------


def extract_sdmx_json_series(payload: Any) -> list[dict[str, Any]]:
    """Extract (series_key, time_period, value) rows from an SDMX-JSON payload."""
    root = require_mapping(payload, "sdmx")
    require_keys(root, {"header", "dataSets", "structure"}, "sdmx")
    structure = require_mapping(root["structure"], "sdmx.structure")
    require_keys(structure, {"dimensions"}, "sdmx.structure")
    dimensions = require_mapping(structure["dimensions"], "sdmx.structure.dimensions")
    require_keys(dimensions, {"observation"}, "sdmx.structure.dimensions")
    observation_dims = dimensions["observation"]
    if not isinstance(observation_dims, list) or not observation_dims:
        raise AdapterError(SCHEMA_FIELD_MISSING, "sdmx observation dimensions must be non-empty")
    time_dim = require_mapping(observation_dims[0], "sdmx.observation[0]")
    require_keys(time_dim, {"id", "values"}, "sdmx.observation[0]")
    if require_str(time_dim, "id", "sdmx.observation[0]") != "TIME_PERIOD":
        raise AdapterError(
            SCHEMA_INVARIANT_VIOLATED,
            "first observation dimension must be TIME_PERIOD",
        )
    periods: list[str] = []
    for index, value in enumerate(time_dim["values"]):
        entry = require_mapping(value, f"sdmx.observation[0].values[{index}]")
        require_keys(entry, {"id"}, f"sdmx.observation[0].values[{index}]")
        periods.append(require_str(entry, "id", f"sdmx.observation[0].values[{index}]"))

    data_sets = root["dataSets"]
    if not isinstance(data_sets, list) or not data_sets:
        raise AdapterError(SCHEMA_FIELD_MISSING, "sdmx dataSets must be non-empty")

    rows: list[dict[str, Any]] = []
    for set_index, dataset in enumerate(data_sets):
        dataset_map = require_mapping(dataset, f"sdmx.dataSets[{set_index}]")
        require_keys(dataset_map, {"series"}, f"sdmx.dataSets[{set_index}]")
        series_map = require_mapping(dataset_map["series"], f"sdmx.dataSets[{set_index}].series")
        for series_key, series in series_map.items():
            series_entry = require_mapping(series, f"sdmx.series[{series_key}]")
            require_keys(series_entry, {"observations"}, f"sdmx.series[{series_key}]")
            observations = require_mapping(
                series_entry["observations"], f"sdmx.series[{series_key}].observations"
            )
            for obs_index, observation in observations.items():
                try:
                    position = int(obs_index)
                except ValueError:
                    raise AdapterError(
                        SCHEMA_INVARIANT_VIOLATED,
                        f"observation index {obs_index!r} is not an integer",
                    )
                if position < 0 or position >= len(periods):
                    raise AdapterError(
                        SCHEMA_INVARIANT_VIOLATED,
                        f"observation index {position} outside TIME_PERIOD range",
                    )
                if not isinstance(observation, list) or not observation:
                    raise AdapterError(
                        SCHEMA_VALUE_TYPE_MISMATCH,
                        f"observation {series_key}/{obs_index} must be a non-empty array",
                    )
                raw_value = observation[0]
                if raw_value is not None and isinstance(raw_value, bool):
                    raise AdapterError(SCHEMA_VALUE_TYPE_MISMATCH, "observation value must be numeric")
                if raw_value is not None and not isinstance(raw_value, (int, float)):
                    raise AdapterError(SCHEMA_VALUE_TYPE_MISMATCH, "observation value must be numeric")
                rows.append(
                    {
                        "series_key": series_key,
                        "time_period": periods[position],
                        "value": raw_value,
                    }
                )
    return rows


def sdmx_series_id(payload: dict, series_key: str) -> str:
    """Resolve a positional SDMX series key to its dotted dimension id."""
    structure = require_mapping(payload["structure"], "sdmx.structure")
    dimensions = require_mapping(structure["dimensions"], "sdmx.structure.dimensions")
    require_keys(dimensions, {"series"}, "sdmx.structure.dimensions")
    series_dims = dimensions["series"]
    if not isinstance(series_dims, list):
        raise AdapterError(SCHEMA_VALUE_TYPE_MISMATCH, "sdmx series dimensions must be a list")
    parts = series_key.split(":")
    if len(parts) != len(series_dims):
        raise AdapterError(
            SCHEMA_INVARIANT_VIOLATED,
            f"series key {series_key!r} does not match {len(series_dims)} dimensions",
        )
    resolved: list[str] = []
    for index, (part, dimension) in enumerate(zip(parts, series_dims)):
        dim_map = require_mapping(dimension, f"sdmx.series[{index}]")
        require_keys(dim_map, {"values"}, f"sdmx.series[{index}]")
        values = dim_map["values"]
        if not isinstance(values, list):
            raise AdapterError(SCHEMA_VALUE_TYPE_MISMATCH, f"sdmx.series[{index}].values must be a list")
        try:
            position = int(part)
        except ValueError:
            raise AdapterError(SCHEMA_INVARIANT_VIOLATED, f"series key part {part!r} is not an integer")
        if position < 0 or position >= len(values):
            raise AdapterError(
                SCHEMA_INVARIANT_VIOLATED,
                f"series key position {position} out of range in dimension {index}",
            )
        value_map = require_mapping(values[position], f"sdmx.series[{index}].values[{position}]")
        require_keys(value_map, {"id"}, f"sdmx.series[{index}].values[{position}]")
        resolved.append(require_str(value_map, "id", f"sdmx.series[{index}].values[{position}]"))
    return ".".join(resolved)
