"""FREE-DATA-FRONTIER-V1 contract: statuses, records, disk floor, PIT semantics.

Data-engineering cycle only. No strategy scoring, no PnL, no S1 access, no
orders. A reachable URL is never evidence of research authorization or
point-in-time usability.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

CYCLE_ID = "FREE-DATA-FRONTIER-V1"
PARSER_VERSION = "free_data_frontier@1"

# Per plan section 3 + BLOCKED_DEPENDENCY from plan section 6 (streams).
SOURCE_STATUSES = frozenset(
    {
        "PASS_SAMPLE",
        "PASS_INVENTORY_ONLY",
        "BLOCKED_TERMS",
        "BLOCKED_CREDENTIAL",
        "BLOCKED_SCHEMA",
        "BLOCKED_NETWORK",
        "BLOCKED_DEPENDENCY",
        "NOT_RUN_RESOURCE_CONFLICT",
    }
)

DISK_FLOOR_BYTES = 15 * 1024**3  # 15 GiB must remain free after any download
SEC_MAX_REQUESTS_PER_SECOND = 8.0  # strictly below the published 10 req/s
DEFAULT_TIMEOUT_SECONDS = (10.0, 60.0)  # (connect, read)
LARGE_DOWNLOAD_READ_TIMEOUT_SECONDS = 300.0
UNKNOWN_SIZE_REFUSE_ABOVE_BYTES = 50 * 1024 * 1024  # unknown-size fail-closed bar

# Record fields required by plan section 5.
RECORD_REQUIRED_FIELDS = (
    "source_id",
    "dataset_id",
    "canonical_request_id",
    "source_url_redacted",
    "retrieved_time_utc",
    "http_status",
    "content_type",
    "content_length",
    "raw_path",
    "raw_sha256",
    "parser_version",
    "authority_status",
    "event_time_utc",
    "effective_time_utc",
    "available_time_utc",
    "available_time_evidence",
    "vintage",
    "retrieval_time_only",
    "notes",
)

_ISO_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$")


class ContractError(Exception):
    """Base error for contract violations; always fail closed."""


class SchemaRefusal(ContractError):
    """Response does not match the preregistered schema shape."""


class DiskFloorError(ContractError):
    """A download would breach the 15 GiB free-space floor."""


class CredentialMissing(ContractError):
    """A required environment credential is absent (value never read here)."""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def iso_utc(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_iso_utc(value: str, field: str) -> str:
    if not isinstance(value, str) or not _ISO_UTC_RE.match(value):
        raise SchemaRefusal(f"{field} is not a canonical UTC timestamp: {value!r}")
    return value


def validate_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Strict schema probe for a retrieval record; raises SchemaRefusal."""
    missing = [f for f in RECORD_REQUIRED_FIELDS if f not in record]
    if missing:
        raise SchemaRefusal(f"retrieval record missing fields: {missing}")
    unknown = set(record) - set(RECORD_REQUIRED_FIELDS)
    if unknown:
        raise SchemaRefusal(f"retrieval record has unknown fields: {sorted(unknown)}")
    for field in ("source_id", "dataset_id", "canonical_request_id", "raw_sha256"):
        if not isinstance(record[field], str) or not record[field]:
            raise SchemaRefusal(f"{field} must be a non-empty string")
    if record["raw_sha256"] != "NOT_APPLIED" and (
        not isinstance(record["raw_sha256"], str) or len(record["raw_sha256"]) != 64
    ):
        raise SchemaRefusal("raw_sha256 must be a 64-char digest or NOT_APPLIED")
    validate_iso_utc(record["retrieved_time_utc"], "retrieved_time_utc")
    if record["authority_status"] not in SOURCE_STATUSES:
        raise SchemaRefusal(f"unknown authority_status: {record['authority_status']}")
    if record["retrieval_time_only"] is True and record["available_time_utc"] is not None:
        raise SchemaRefusal(
            "retrieval_time_only=True contradicts a present available_time_utc"
        )
    if record["available_time_utc"] is not None:
        validate_iso_utc(record["available_time_utc"], "available_time_utc")
        if not record["available_time_evidence"]:
            raise SchemaRefusal(
                "available_time_utc requires available_time_evidence (P-1)"
            )
    if record["event_time_utc"] is not None:
        validate_iso_utc(record["event_time_utc"], "event_time_utc")
    if record["effective_time_utc"] is not None:
        validate_iso_utc(record["effective_time_utc"], "effective_time_utc")
    for field in ("http_status",):
        if record[field] is not None and not isinstance(record[field], int):
            raise SchemaRefusal(f"{field} must be int or null")
    for field in ("content_length",):
        if record[field] is not None and not isinstance(record[field], int):
            raise SchemaRefusal(f"{field} must be int or null")
    if record["raw_path"] is not None and "/raw/" not in record["raw_path"]:
        raise SchemaRefusal("raw_path must live under the raw data root")
    return record


def availability_semantics(record: Dict[str, Any]) -> str:
    """PIT classification; retrieved time never becomes available time."""
    if record["available_time_utc"] is not None and record["available_time_evidence"]:
        return "PIT_EVIDENCED"
    return "RETRIEVAL_TIME_ONLY"


def source_verdict(rows: List[Dict[str, Any]], source_id: str) -> Dict[str, Any]:
    """Aggregate per-source status: PASS_SAMPLE requires at least one raw object."""
    if not rows:
        return {"source_id": source_id, "status": "PASS_INVENTORY_ONLY", "objects": 0}
    statuses = {r["authority_status"] for r in rows}
    if "PASS_SAMPLE" in statuses:
        overall = "PASS_SAMPLE"
    elif "BLOCKED_SCHEMA" in statuses:
        overall = "BLOCKED_SCHEMA"
    elif "BLOCKED_NETWORK" in statuses:
        overall = "BLOCKED_NETWORK"
    else:
        overall = "PASS_INVENTORY_ONLY"
    return {"source_id": source_id, "status": overall, "objects": len(rows)}
