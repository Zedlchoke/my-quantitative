"""Temporal identity mappings; current symbols are never projected backward."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .models import require_utc


class IdentityConflict(ValueError):
    """Multiple canonical identities claim one alias at a point in time."""

    code = "IDENTITY_CONFLICT_MULTIPLE_CANONICAL"

    def __init__(
        self, message: str = "multiple canonical identities for the requested alias"
    ) -> None:
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class TemporalAlias:
    namespace: str
    alias: str
    canonical_id: str
    valid_from_utc: datetime
    valid_to_utc: datetime | None
    available_time_utc: datetime
    source_id: str
    raw_sha256: str

    def __post_init__(self) -> None:
        for field in ("namespace", "alias", "canonical_id", "source_id"):
            if not getattr(self, field).strip():
                raise ValueError(f"{field} must be non-empty")
        require_utc(self.valid_from_utc, "valid_from_utc")
        if self.valid_to_utc is not None:
            require_utc(self.valid_to_utc, "valid_to_utc")
            if self.valid_to_utc <= self.valid_from_utc:
                raise ValueError("valid_to_utc must be after valid_from_utc")
        require_utc(self.available_time_utc, "available_time_utc")
        if len(self.raw_sha256) != 64 or any(c not in "0123456789abcdef" for c in self.raw_sha256):
            raise ValueError("raw_sha256 must be lowercase 64-hex")

    def active_at(self, when: datetime) -> bool:
        point = require_utc(when, "when")
        return (
            self.available_time_utc <= point
            and self.valid_from_utc <= point
            and (self.valid_to_utc is None or point < self.valid_to_utc)
        )


def resolve_identity(
    aliases: list[TemporalAlias], namespace: str, alias: str, when: datetime
) -> str | None:
    matches = [
        row.canonical_id
        for row in aliases
        if row.namespace == namespace and row.alias == alias and row.active_at(when)
    ]
    unique = set(matches)
    if len(unique) > 1:
        raise IdentityConflict(f"multiple canonical identities for {namespace}:{alias}")
    return next(iter(unique)) if unique else None
