"""Immutable normalized observations with strict PIT provenance."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import PurePosixPath
import re
from typing import Any


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def require_utc(value: datetime, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    if value.utcoffset().total_seconds() != 0:
        raise ValueError(f"{field} must be UTC")
    return value.astimezone(timezone.utc)


def require_relative_path(value: str, field: str) -> str:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{field} must be a non-empty relative POSIX path")
    return value


def canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


@dataclass(frozen=True, slots=True)
class NormalizedRecord:
    source_id: str
    dataset_id: str
    entity_id: str
    field: str
    value: str | int | float | bool | None
    unit: str
    event_time_utc: datetime
    available_time_utc: datetime
    effective_time_utc: datetime | None
    vintage_time_utc: datetime
    retrieved_time_utc: datetime
    raw_path: str
    raw_sha256: str
    license_id: str
    entitlement_id: str
    normalizer_version: str

    def __post_init__(self) -> None:
        for name in (
            "source_id",
            "dataset_id",
            "entity_id",
            "field",
            "unit",
            "license_id",
            "entitlement_id",
            "normalizer_version",
        ):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        require_utc(self.event_time_utc, "event_time_utc")
        require_utc(self.available_time_utc, "available_time_utc")
        if self.effective_time_utc is not None:
            require_utc(self.effective_time_utc, "effective_time_utc")
        require_utc(self.vintage_time_utc, "vintage_time_utc")
        require_utc(self.retrieved_time_utc, "retrieved_time_utc")
        if self.available_time_utc > self.retrieved_time_utc:
            raise ValueError("available_time_utc cannot be after retrieval")
        if self.vintage_time_utc > self.retrieved_time_utc:
            raise ValueError("vintage_time_utc cannot be after retrieval")
        require_relative_path(self.raw_path, "raw_path")
        if not _SHA256_RE.fullmatch(self.raw_sha256):
            raise ValueError("raw_sha256 must be lowercase 64-hex")
        if isinstance(self.value, float) and not math.isfinite(self.value):
            raise ValueError("value must be finite")

    @property
    def logical_key(self) -> tuple[str, str, str]:
        return (self.dataset_id, self.entity_id, self.field)

    def eligible_at(self, decision_time: datetime, *, require_effective: bool = True) -> bool:
        decision = require_utc(decision_time, "decision_time")
        if self.available_time_utc > decision:
            return False
        if require_effective and self.effective_time_utc is not None:
            return self.effective_time_utc <= decision
        return True

    def canonical_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in (
            "event_time_utc",
            "available_time_utc",
            "effective_time_utc",
            "vintage_time_utc",
            "retrieved_time_utc",
        ):
            value = payload[key]
            payload[key] = value.isoformat().replace("+00:00", "Z") if value is not None else None
        return payload

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.canonical_payload())
