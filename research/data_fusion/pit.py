"""Point-in-time selection across append-only revisions."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from .models import NormalizedRecord, require_utc


class AmbiguousVintageError(ValueError):
    """Two distinct records claim the same point-in-time rank."""

    code = "AMBIGUOUS_VINTAGE_RANK"

    def __init__(self, message: str = "conflicting records have identical PIT rank") -> None:
        super().__init__(message)


def vintage_rank(record: NormalizedRecord) -> tuple[datetime, datetime, datetime]:
    return (
        record.available_time_utc,
        record.vintage_time_utc,
        record.retrieved_time_utc,
    )


@dataclass(frozen=True, slots=True)
class VintageSeries:
    """Append-only revision set for exactly one logical key.

    Appending never mutates earlier revisions.  A vintage rank is filled at
    most once: re-appending byte-identical content is idempotent, while
    different content at the same rank fails closed instead of overwriting.
    """

    key: tuple[str, str, str]
    records: tuple[NormalizedRecord, ...] = ()

    @classmethod
    def started_by(cls, record: NormalizedRecord) -> "VintageSeries":
        return cls(record.logical_key, (record,))

    def append(self, record: NormalizedRecord) -> "VintageSeries":
        if record.logical_key != self.key:
            raise ValueError("record logical key does not match series key")
        rank = vintage_rank(record)
        for existing in self.records:
            if vintage_rank(existing) == rank:
                if existing.canonical_bytes() == record.canonical_bytes():
                    return self
                raise AmbiguousVintageError("append would overwrite an existing vintage")
        return VintageSeries(self.key, (*self.records, record))

    def select(
        self, decision_time: datetime, *, require_effective: bool = True
    ) -> NormalizedRecord | None:
        return select_asof(self.records, decision_time, require_effective=require_effective)


def select_asof(
    records: Iterable[NormalizedRecord],
    decision_time: datetime,
    *,
    require_effective: bool = True,
) -> NormalizedRecord | None:
    decision = require_utc(decision_time, "decision_time")
    eligible = [r for r in records if r.eligible_at(decision, require_effective=require_effective)]
    if not eligible:
        return None
    keys = {r.logical_key for r in eligible}
    if len(keys) != 1:
        raise ValueError("select_asof accepts exactly one logical key")
    eligible.sort(
        key=lambda r: (
            r.available_time_utc,
            r.vintage_time_utc,
            r.retrieved_time_utc,
            r.raw_sha256,
        )
    )
    winner = eligible[-1]
    same_rank = [r for r in eligible if vintage_rank(r) == vintage_rank(winner)]
    if len({r.canonical_bytes() for r in same_rank}) > 1:
        raise AmbiguousVintageError("conflicting records have identical PIT rank")
    return winner


def asof_join(
    records: Iterable[NormalizedRecord],
    decision_times: Iterable[datetime],
    *,
    require_effective: bool = True,
) -> dict[datetime, dict[tuple[str, str, str], NormalizedRecord]]:
    grouped: dict[tuple[str, str, str], list[NormalizedRecord]] = defaultdict(list)
    for record in records:
        grouped[record.logical_key].append(record)
    output: dict[datetime, dict[tuple[str, str, str], NormalizedRecord]] = {}
    for raw_decision in decision_times:
        decision = require_utc(raw_decision, "decision_time")
        row: dict[tuple[str, str, str], NormalizedRecord] = {}
        for key, candidates in grouped.items():
            selected = select_asof(candidates, decision, require_effective=require_effective)
            if selected is not None:
                row[key] = selected
        output[decision] = row
    return output
