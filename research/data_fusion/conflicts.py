"""Explicit source roles and no cross-source gap patching."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from .models import NormalizedRecord


class SourceRole(str, Enum):
    PRIMARY = "PRIMARY"
    CROSS_CHECK = "CROSS_CHECK"
    DIAGNOSTIC = "DIAGNOSTIC"
    UNAVAILABLE = "UNAVAILABLE"


class ConflictError(ValueError):
    """Fail-closed conflict refusal carrying a stable reason code."""

    def __init__(self, code: str, message: str | None = None) -> None:
        self.code = code
        super().__init__(message if message is not None else code)


@dataclass(frozen=True, slots=True)
class SourcePolicy:
    dataset_id: str
    field: str
    roles: dict[str, SourceRole]

    def primary_source(self) -> str:
        primaries = [source for source, role in self.roles.items() if role is SourceRole.PRIMARY]
        if not primaries:
            raise ConflictError(
                "NO_PRIMARY_SOURCE_DECLARED",
                "policy must declare exactly one PRIMARY source",
            )
        if len(primaries) > 1:
            raise ConflictError(
                "MULTIPLE_PRIMARY_SOURCES",
                "policy must declare exactly one PRIMARY source",
            )
        return primaries[0]


def resolve_primary(
    records: Iterable[NormalizedRecord], policy: SourcePolicy
) -> tuple[list[NormalizedRecord], dict[str, list[NormalizedRecord]]]:
    primary_id = policy.primary_source()
    matching = [r for r in records if r.dataset_id == policy.dataset_id and r.field == policy.field]
    primary = [r for r in matching if r.source_id == primary_id]
    checks: dict[str, list[NormalizedRecord]] = {}
    for source_id, role in policy.roles.items():
        if role in (SourceRole.CROSS_CHECK, SourceRole.DIAGNOSTIC):
            checks[source_id] = [r for r in matching if r.source_id == source_id]
    return primary, checks
