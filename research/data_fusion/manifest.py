"""Deterministic manifests binding normalized data to raw bytes."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import PurePosixPath
import re

from .authority import AuthorityStatus
from .models import canonical_json_bytes


_SHA = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_AUTHORITY_STATUS = frozenset(status.value for status in AuthorityStatus)


@dataclass(frozen=True, slots=True)
class RawFileEvidence:
    path: str
    sha256: str
    bytes: int

    def __post_init__(self) -> None:
        p = PurePosixPath(self.path)
        if not self.path or p.is_absolute() or ".." in p.parts:
            raise ValueError("path must be relative and traversal-free")
        if not _SHA.fullmatch(self.sha256):
            raise ValueError("sha256 must be lowercase 64-hex")
        if self.bytes < 0:
            raise ValueError("bytes must be non-negative")


@dataclass(frozen=True, slots=True)
class SourceManifest:
    source_id: str
    dataset_id: str
    schema_version: str
    normalizer_version: str
    authority_status: str
    license_id: str
    entitlement_id: str
    files: tuple[RawFileEvidence, ...]

    def __post_init__(self) -> None:
        for field in (
            "source_id",
            "dataset_id",
            "schema_version",
            "normalizer_version",
            "authority_status",
            "license_id",
            "entitlement_id",
        ):
            if not getattr(self, field).strip():
                raise ValueError(f"{field} must be non-empty")
        if self.authority_status not in _ALLOWED_AUTHORITY_STATUS:
            raise ValueError("authority_status must be a documented authority status")
        paths = [f.path for f in self.files]
        if len(paths) != len(set(paths)):
            raise ValueError("manifest contains duplicate paths")

    def canonical_payload(self) -> dict:
        payload = asdict(self)
        payload["files"] = sorted(payload["files"], key=lambda item: item["path"])
        return payload

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.canonical_payload())

    def digest(self) -> str:
        return sha256(self.canonical_bytes()).hexdigest()
