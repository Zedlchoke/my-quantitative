"""V5 sanitizing shim: real SEC companyfacts bytes -> frozen adapter schema.

The frozen Data Fusion core (MULTISOURCE_DATA_CORE_SHA c6a0576) was validated
against hand-written fixtures only; live SEC payloads contain entries the
frozen strict schema refuses (null label/description metadata, empty fp/form
strings, null vals, byte-identical duplicate facts).  The core must stay
byte-identical to its freeze, so STOCKS-FREE-V5 pre-processes real bytes here
instead of patching it.

Contract:

- raw bytes are never modified on disk and remain SHA-pinned by the fetch log;
- every transformation is content-conservative (drops only entries the frozen
  adapter would reject; metadata nulls deleted from metadata keys only);
- every drop is counted per file and surfaced to the caller - nothing is
  silently coerced, nothing inferred;
- the sanitized payload then goes through the FROZEN ``SecAdapter`` unchanged,
  so record semantics (availability upper bounds, vintage ranks, duplicate
  detection) stay the audited fusion ones.

Shim version is recorded as the normalizer front-stage: records produced via
this path carry provenance raw_sha256 -> sanitize-1 -> sec-adapter-1.0.0.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

SANITIZER_VERSION = "sec-companyfacts-sanitize-1.0.0"


@dataclass(slots=True)
class SanitizeStats:
    dropped_null_val: int = 0
    dropped_empty_fp: int = 0
    dropped_empty_form: int = 0
    dropped_malformed_dates: int = 0
    dropped_filed_before_end: int = 0
    dropped_duplicate_identical: int = 0
    dropped_duplicate_conflicting: int = 0
    deleted_null_label: int = 0
    deleted_null_description: int = 0
    dropped_null_entry: int = 0

    def total_dropped(self) -> int:
        return (
            self.dropped_null_val
            + self.dropped_empty_fp
            + self.dropped_empty_form
            + self.dropped_malformed_dates
            + self.dropped_filed_before_end
            + self.dropped_duplicate_identical
            + self.dropped_duplicate_conflicting
            + self.dropped_null_entry
        )

    def as_dict(self) -> dict[str, int]:
        return {
            "dropped_null_val": self.dropped_null_val,
            "dropped_empty_fp": self.dropped_empty_fp,
            "dropped_empty_form": self.dropped_empty_form,
            "dropped_malformed_dates": self.dropped_malformed_dates,
            "dropped_filed_before_end": self.dropped_filed_before_end,
            "dropped_duplicate_identical": self.dropped_duplicate_identical,
            "dropped_duplicate_conflicting": self.dropped_duplicate_conflicting,
            "deleted_null_label": self.deleted_null_label,
            "deleted_null_description": self.deleted_null_description,
            "dropped_null_entry": self.dropped_null_entry,
            "total_dropped": self.total_dropped(),
        }


def _fact_key(entry: dict[str, Any]) -> tuple:
    return (entry.get("accn"), entry.get("end"), entry.get("filed"), entry.get("val"))


def _looks_like_date(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 10:
        return False
    head, mid, tail = value[:4], value[5:7], value[8:10]
    return (
        head.isdigit() and mid.isdigit() and tail.isdigit()
        and value[4] == "-" and value[7] == "-"
    )


def sanitize_companyfacts(payload: dict[str, Any]) -> tuple[dict[str, Any], SanitizeStats]:
    """Return an adapter-conformant deep copy plus drop statistics.

    Structural corruption (missing cik/facts, non-mapping facts) is NOT
    repaired here - it propagates so the frozen adapter fails the file
    outright, which is the correct fail-closed behaviour.
    """
    stats = SanitizeStats()
    clean = deepcopy(payload)
    facts = clean.get("facts")
    if not isinstance(facts, dict):
        return clean, stats
    for taxonomy in list(facts):
        tags = facts[taxonomy]
        if not isinstance(tags, dict):
            continue
        for tag in list(tags):
            meta = tags[tag]
            if not isinstance(meta, dict):
                continue
            if meta.get("label") is None:
                meta.pop("label", None)
                stats.deleted_null_label += 1
            if meta.get("description") is None:
                meta.pop("description", None)
                stats.deleted_null_description += 1
            units = meta.get("units")
            if not isinstance(units, dict):
                continue
            for unit in list(units):
                entries = units[unit]
                if not isinstance(entries, list):
                    continue
                kept: list[dict[str, Any]] = []
                seen: dict[tuple, Any] = {}
                for entry in entries:
                    if not isinstance(entry, dict):
                        stats.dropped_null_entry += 1
                        continue
                    value = entry.get("val")
                    if isinstance(value, bool) or not isinstance(value, (int, float)):
                        stats.dropped_null_val += 1
                        continue
                    if not isinstance(entry.get("fp"), str) or not entry.get("fp", "").strip():
                        stats.dropped_empty_fp += 1
                        continue
                    if not isinstance(entry.get("form"), str) or not entry.get("form", "").strip():
                        stats.dropped_empty_form += 1
                        continue
                    if not _looks_like_date(entry.get("end")) or not _looks_like_date(entry.get("filed")):
                        stats.dropped_malformed_dates += 1
                        continue
                    if entry.get("filed") < entry.get("end"):
                        # real SEC payloads occasionally carry a filed date
                        # earlier than the period end (XBRL tagging defect);
                        # the frozen adapter fails the whole file on this, so
                        # the shim drops the defective fact, counted, and the
                        # file survives
                        stats.dropped_filed_before_end += 1
                        continue
                    key = (entry.get("accn"), entry.get("end"), entry.get("filed"))
                    if key in seen:
                        if seen[key] == value:
                            stats.dropped_duplicate_identical += 1
                        else:
                            stats.dropped_duplicate_conflicting += 1
                            # conflicting duplicate: drop BOTH (fail-visible)
                            for index, previous in enumerate(kept):
                                if (previous.get("accn"), previous.get("end"), previous.get("filed")) == key:
                                    kept.pop(index)
                                    break
                        continue
                    seen[key] = value
                    kept.append(entry)
                units[unit] = kept
    return clean, stats


__all__ = ["SANITIZER_VERSION", "SanitizeStats", "sanitize_companyfacts"]
