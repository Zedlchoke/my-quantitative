"""F5 structured doctor waivers (MARKET-DATA-PLANE-V2 freeze, finding F5).

A waiver is a structured, individually-identified, append-only record that
classifies a single known doctor HIGH finding. It NEVER suppresses a
finding silently: the doctor relabels an exactly-waived HIGH finding as
WAIVED_HIGH (severity retained, still visible, never PASS, never dropped).

Record fields (all mandatory, frozen names):

    finding_kind                  doctor finding kind this waiver applies to
    severity                      LOW | MEDIUM | HIGH (waived findings retain
                                  their severity)
    finding_digest                sha256 hex of the EXACT finding detail str
    classification                human/owner classification of the finding
    evidence_reference            pointer to the evidence justifying it
    approver_authority            the authority that approved the waiver
    created_utc                   UTC ISO8601 Z-form
    expiry_utc_or_terminal_event  a UTC-Z timestamp OR a terminal-event
                                  reference (e.g. "TERMINAL:<cycle id>");
                                  terminal-event refs are governed by
                                  terminal reconciliation, not wall clock
    status                        ACTIVE | EXPIRED | SUPERSEDED | RESOLVED
    waiver_id                     64-hex content id: sha256 of the canonical
                                  JSON of the record minus waiver_id
    supersedes                    optional 64-hex waiver_id this record
                                  supersedes (append-only transition)

APPEND-ONLY TRANSITION (freeze): superseding a waiver appends TWO records,
never edits one -- the waiver_id is a content id (status included), so the
superseded record keeps its historical bytes and the retirement is itself
appended:
  1. a NEW record with status SUPERSEDED carrying ``supersedes: <old
     waiver_id>`` (the retirement record "on the old record id"), and
  2. a NEW ACTIVE record with ``supersedes: <retirement record
     waiver_id>`` (the replacement).
The chain is therefore W1 ACTIVE <- W2 SUPERSEDED <- W3 ACTIVE. Because the
old record's bytes still say ACTIVE, the loader and :func:`waiver_applies`
treat any record referenced by another record's ``supersedes`` as
effectively superseded, regardless of its recorded status.

COHERENCE (enforced by :func:`load_waivers`, fail closed):
  - waiver_ids are unique content ids; a duplicate is a store error;
  - a SUPERSEDED record must be referenced by some other record's
    ``supersedes``;
  - every ``supersedes`` target must exist in the store (and never be the
    record itself);
  - an ACTIVE record may not be superseded by an EXPIRED one;
  - no unknown fields, no unbound waiver_id, no dangling references.

Store layout (freeze): one waiver record per JSON file under
research/control/doctor_waivers/*.json. The loader validates every record
and raises WaiverStoreError on ANY malformed record - fail closed.

V2 ships the mechanism only: it creates NO waiver for foreign-cycle
findings (no authority).
"""
from __future__ import annotations

import datetime
import hashlib
import json
import re
from pathlib import Path

WAIVER_ID = "waiver_id"
SUPERSEDES = "supersedes"

WAIVER_FIELDS = (
    "finding_kind",
    "severity",
    "finding_digest",
    "classification",
    "evidence_reference",
    "approver_authority",
    "created_utc",
    "expiry_utc_or_terminal_event",
    "status",
)
WAIVER_OPTIONAL_FIELDS = (SUPERSEDES,)
WAIVER_STATUSES = ("ACTIVE", "EXPIRED", "SUPERSEDED", "RESOLVED")
WAIVER_SEVERITIES = ("LOW", "MEDIUM", "HIGH")

_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class WaiverValidationError(ValueError):
    """A single waiver record is malformed (fail closed)."""


class WaiverStoreError(ValueError):
    """The waiver store is incoherent or unreadable (fail closed)."""


# ------------------------------------------------------------------ digests

def finding_digest(detail: str) -> str:
    """sha256 hex of the exact finding detail string a waiver applies to."""
    if not isinstance(detail, str):
        raise WaiverValidationError("finding detail must be a string")
    return hashlib.sha256(detail.encode("utf-8")).hexdigest()


def _canonical_content_bytes(record: dict) -> bytes:
    body = {k: v for k, v in record.items() if k != WAIVER_ID}
    return json.dumps(body, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def content_id(record: dict) -> str:
    """64-hex content id of the record minus waiver_id."""
    return hashlib.sha256(_canonical_content_bytes(record)).hexdigest()


# ------------------------------------------------------------- validation

def validate_waiver(record: dict) -> dict:
    """Validate one waiver record; return a validated COPY with waiver_id.

    Raises WaiverValidationError on any schema violation. When the record
    already carries a waiver_id it must match the recomputed content id
    (binding check). The input dict is never mutated.
    """
    if not isinstance(record, dict):
        raise WaiverValidationError("waiver record must be an object")
    allowed = set(WAIVER_FIELDS) | {WAIVER_ID, *WAIVER_OPTIONAL_FIELDS}
    unknown = sorted(set(record) - allowed)
    if unknown:
        raise WaiverValidationError(f"unknown field(s) {unknown}")
    missing = [f for f in WAIVER_FIELDS if f not in record]
    if missing:
        raise WaiverValidationError(f"missing required field(s) {missing}")

    for f in ("finding_kind", "classification", "evidence_reference",
              "approver_authority"):
        if not (isinstance(record[f], str) and record[f].strip()):
            raise WaiverValidationError(f"{f} must be a non-empty string")
    if record["severity"] not in WAIVER_SEVERITIES:
        raise WaiverValidationError(
            f"severity must be one of {WAIVER_SEVERITIES}, "
            f"got {record['severity']!r}")
    if not (isinstance(record["finding_digest"], str)
            and _HEX64.match(record["finding_digest"])):
        raise WaiverValidationError(
            f"finding_digest must be 64-hex sha256, "
            f"got {record['finding_digest']!r}")
    if not _UTC.match(record["created_utc"] or ""):
        raise WaiverValidationError(
            f"created_utc must be UTC ISO8601 Z-form, "
            f"got {record['created_utc']!r}")
    expiry = record["expiry_utc_or_terminal_event"]
    if not (isinstance(expiry, str) and expiry.strip()):
        raise WaiverValidationError(
            "expiry_utc_or_terminal_event must be a non-empty string "
            "(UTC-Z timestamp or terminal-event reference)")
    if record["status"] not in WAIVER_STATUSES:
        raise WaiverValidationError(
            f"status must be one of {WAIVER_STATUSES}, got {record['status']!r}")
    if SUPERSEDES in record:
        sup = record[SUPERSEDES]
        if not (isinstance(sup, str) and _HEX64.match(sup)):
            raise WaiverValidationError(
                f"supersedes must be a 64-hex waiver_id, got {sup!r}")

    # created <= expiry when the expiry is a wall-clock timestamp
    created = _parse_utc(record["created_utc"])
    expiry_dt = _parse_utc(expiry)
    if created is not None and expiry_dt is not None and created > expiry_dt:
        raise WaiverValidationError(
            f"created_utc {record['created_utc']} is after expiry {expiry}")

    minted = content_id(record)
    if WAIVER_ID in record and record[WAIVER_ID] != minted:
        raise WaiverValidationError(
            f"waiver_id {record[WAIVER_ID]!r} does not match the recomputed "
            f"content id {minted!r} (record tampered or mis-minted)")
    out = dict(record)
    out[WAIVER_ID] = minted
    return out


def _parse_utc(text: str):
    if not isinstance(text, str) or not _UTC.match(text):
        return None
    return datetime.datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=datetime.timezone.utc)


# --------------------------------------------------------------- effectivity

def is_active_and_unexpired(record: dict, now=None) -> bool:
    """True iff status is ACTIVE and the waiver has not expired.

    A UTC-Z expiry is compared against ``now`` (default: current UTC time).
    A terminal-event reference expiry never times out on the wall clock --
    it is governed by the cycle's terminal reconciliation.
    """
    if record.get("status") != "ACTIVE":
        return False
    expiry = record.get("expiry_utc_or_terminal_event") or ""
    expiry_dt = _parse_utc(expiry)
    if expiry_dt is None:
        return True  # terminal-event reference: not wall-clock expiring
    moment = now or datetime.datetime.now(datetime.timezone.utc)
    return moment <= expiry_dt


def waiver_applies(waivers, kind: str, detail: str, now=None) -> bool:
    """True iff some waiver exactly covers this finding.

    Exact match required: finding_kind equal AND finding_digest equal to
    the sha256 of the exact detail string; the waiver must be ACTIVE,
    unexpired, and not superseded by another record in the set (an ACTIVE
    record referenced by another record's ``supersedes`` is effectively
    retired). Malformed waiver entries never apply (fail closed) and are
    skipped, never raised, so a bad waiver cannot crash the diagnostic.
    """
    try:
        digest = finding_digest(detail)
    except WaiverValidationError:
        return False
    records = []
    for w in waivers or []:
        try:
            records.append(validate_waiver(w))
        except WaiverValidationError:
            continue
    superseded_ids = {r[SUPERSEDES] for r in records if r.get(SUPERSEDES)}
    for validated in records:
        if validated["status"] != "ACTIVE":
            continue
        if validated[WAIVER_ID] in superseded_ids:
            continue  # effectively retired by an appended transition record
        if validated["finding_kind"] != kind:
            continue
        if validated["finding_digest"] != digest:
            continue
        if is_active_and_unexpired(validated, now):
            return True
    return False


# -------------------------------------------------------------------- store

def load_waivers(paths: list) -> list:
    """Load + validate a waiver store (one record per JSON file).

    Fails closed: any malformed record raises WaiverStoreError naming the
    path. Store-level coherence is enforced across the whole set (see the
    module docstring). Returns every validated record in input order; the
    historical bytes of a superseded waiver stay visible in the result and
    :func:`waiver_applies` is the effective-status layer.
    """
    validated = []  # (path, record)
    for p in paths or []:
        path = Path(p)
        try:
            raw = json.loads(path.read_bytes().decode("utf-8"))
        except FileNotFoundError as exc:
            raise WaiverStoreError(f"{path}: missing waiver file") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise WaiverStoreError(f"{path}: malformed waiver JSON "
                                   f"({exc})") from exc
        try:
            validated.append((path, validate_waiver(raw)))
        except WaiverValidationError as exc:
            raise WaiverStoreError(f"{path}: {exc}") from exc

    # waiver_ids are unique content ids; a duplicate is a store error
    by_id = {}
    for path, rec in validated:
        wid = rec[WAIVER_ID]
        if wid in by_id:
            raise WaiverStoreError(
                f"duplicate waiver_id {wid} ({by_id[wid]} vs {path})")
        by_id[wid] = path

    for path, rec in validated:
        sup = rec.get(SUPERSEDES)
        if sup is not None:
            if sup not in by_id:
                raise WaiverStoreError(
                    f"{path}: supersedes dangling waiver_id {sup}")
            if sup == rec[WAIVER_ID]:
                raise WaiverStoreError(f"{path}: waiver supersedes itself")

    for path, rec in validated:
        wid = rec[WAIVER_ID]
        if rec["status"] == "SUPERSEDED":
            referenced = any(r.get(SUPERSEDES) == wid
                             for _, r in validated if r is not rec)
            if not referenced:
                raise WaiverStoreError(
                    f"{path}: SUPERSEDED waiver {wid} is not referenced by "
                    "any supersedes transition record")
        if rec["status"] == "EXPIRED" and rec.get(SUPERSEDES) in by_id:
            target = next(r for _, r in validated
                          if r[WAIVER_ID] == rec[SUPERSEDES])
            if target["status"] == "ACTIVE":
                raise WaiverStoreError(
                    f"{path}: EXPIRED waiver may not supersede ACTIVE "
                    f"waiver {rec[SUPERSEDES]}")

    return [rec for _, rec in validated]
