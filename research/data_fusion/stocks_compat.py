"""Stocks-compatibility aggregation helpers over frozen Data Fusion records.

This module proves the aggregation *mechanics* only.  It is a pure function
of its arguments: no I/O, no wall-clock time, no filer-universe construction
and no persistence.  Building or authorizing a filer universe is P2/A3
authority work and deliberately out of scope here.

Determinism contract (fixed rules, byte-stable output):

- entity ids are traversed in sorted order, so float summation order is
  fixed regardless of caller record order;
- sector keys are normalized by one fixed rule (strip + uppercase) and the
  output mapping is built in sorted sector order;
- each entity contributes at most one value: the latest vintage that is
  eligible at the as-of instant, selected by the shared PIT selector in
  :mod:`research.data_fusion.pit` (never a caller-supplied "current" value);
- the canonical byte form is produced by
  :func:`research.data_fusion.models.canonical_json_bytes` (sorted keys,
  no whitespace, no NaN).

Survivorship contract: the filer set at ``as_of`` is exactly the set of
entities holding at least one record whose ``available_time_utc <= as_of``.
It is derived from availability evidence at each as-of instant, never from a
fixed modern membership list; entities that are not yet available, and
entities with no sector mapping, are excluded explicitly and reported.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Iterable, Mapping

from .models import NormalizedRecord, canonical_json_bytes, require_utc
from .pit import select_asof

__all__ = ["sector_mean_asof", "sector_mean_asof_bytes"]


def sector_mean_asof(
    records: Iterable[NormalizedRecord],
    *,
    as_of: datetime,
    sector_of: Mapping[str, str],
    field: str,
    dataset_id: str = "company_facts",
) -> dict[str, Any]:
    """Aggregate filer-level instant facts to sector means as of one instant.

    A decision at ``as_of`` sees only records whose ``available_time_utc``
    is at or before it; a decision can never read a future-vintage row.
    """

    decision = require_utc(as_of, "as_of")

    by_entity: dict[str, list[NormalizedRecord]] = defaultdict(list)
    for record in records:
        if record.dataset_id == dataset_id and record.field == field:
            by_entity[record.entity_id].append(record)

    rows_by_sector: dict[str, list[tuple[str, float]]] = defaultdict(list)
    unmapped: list[str] = []
    for entity_id in sorted(by_entity):
        selected = select_asof(by_entity[entity_id], decision)
        if selected is None:
            # The entity is not part of the as-of filer set yet: availability
            # has not happened, so it cannot enter any cohort.
            continue
        sector = sector_of.get(entity_id)
        if sector is None or not str(sector).strip():
            unmapped.append(entity_id)
            continue
        rows_by_sector[str(sector).strip().upper()].append(
            (entity_id, float(selected.value))
        )

    sectors: dict[str, Any] = {}
    for sector_key in sorted(rows_by_sector):
        rows = sorted(rows_by_sector[sector_key])
        values = [value for _, value in rows]
        sectors[sector_key] = {
            "count": len(rows),
            "mean": sum(values) / len(rows),
            "entity_ids": [entity_id for entity_id, _ in rows],
        }
    return {
        "as_of": decision.isoformat().replace("+00:00", "Z"),
        "dataset_id": dataset_id,
        "field": field,
        "sectors": sectors,
        "unmapped_entity_ids": sorted(unmapped),
    }


def sector_mean_asof_bytes(
    records: Iterable[NormalizedRecord],
    *,
    as_of: datetime,
    sector_of: Mapping[str, str],
    field: str,
    dataset_id: str = "company_facts",
) -> bytes:
    """Canonical byte form of :func:`sector_mean_asof` (deterministic)."""

    return canonical_json_bytes(
        sector_mean_asof(
            records,
            as_of=as_of,
            sector_of=sector_of,
            field=field,
            dataset_id=dataset_id,
        )
    )
