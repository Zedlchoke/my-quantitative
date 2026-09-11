"""CADS: content-addressed data store (plan section 7A.1).

An object's name IS its integrity proof: the address is the sha256 of the
content.  Layout:

    <store_root>/objects/ab/abc123...   object bytes (gitignored)
    <store_root>/pins.jsonl             append-only pin journal (atomic)
    <store_root>/events.jsonl           append-only event journal (atomic)

APIs: register / pin / resolve / verify / restore.

Invariants:
- atomic writes everywhere (temp file + os.replace);
- every inherited-pin consumer resolves through the store, never through
  worktree paths;
- a mismatched re-hash is an incident + fail-closed, never a silent fix;
- malformed store state raises ControlStateDrift.
"""

from __future__ import annotations

import json
import os
import tempfile
from typing import Any, Mapping

from .canonical import sha256_bytes, sha256_file

SCHEMA_VERSION = "v3_cads@1"


class CADSError(Exception):
    pass


class CADSIntegrityError(CADSError):
    """Corruption detected: incident + fail-closed (never auto-fixed)."""


class ControlStateDrift(CADSError):
    """Malformed store state: journal line unparseable or unknown shape."""


def _atomic_append(path: str, record: Mapping[str, Any]) -> None:
    """Append one JSON line via an atomic temp-file replace of the whole
    journal (append-only semantics with crash-safe replacement)."""
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    prefix = "tmp_" + os.path.basename(path) + "."
    if os.path.exists(path):
        with open(path, "rb") as fh:
            data = fh.read()
    else:
        data = b""
    data = data + (json.dumps(record, sort_keys=True, default=str)
                   .encode("utf-8") + b"\n")
    fd, tmp = tempfile.mkstemp(prefix=prefix, dir=directory)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def _read_journal(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ControlStateDrift(
                    f"journal {path} line {lineno} malformed: {exc}"
                ) from exc
    return rows


class CADS:
    def __init__(self, store_root: str):
        self.root = store_root
        self.objects_dir = os.path.join(store_root, "objects")
        self.pins_path = os.path.join(store_root, "pins.jsonl")
        self.events_path = os.path.join(store_root, "events.jsonl")
        os.makedirs(self.objects_dir, exist_ok=True)

    # -- internal ------------------------------------------------------- #
    def _object_path(self, address: str) -> str:
        if len(address) != 64 or any(
            c not in "0123456789abcdef" for c in address
        ):
            raise CADSError(f"malformed CADS address: {address!r}")
        return os.path.join(self.objects_dir, address[:2], address)

    def _object_bytes(self, address: str) -> bytes | None:
        path = self._object_path(address)
        if not os.path.exists(path):
            return None
        with open(path, "rb") as fh:
            return fh.read()

    # -- APIs ------------------------------------------------------------ #
    def register(self, data: bytes) -> str:
        """Idempotent: registering identical bytes returns the same
        address and does not duplicate storage."""
        address = sha256_bytes(data)
        path = self._object_path(address)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            fd, tmp = tempfile.mkstemp(
                prefix="tmp_obj_", dir=os.path.dirname(path)
            )
            try:
                with os.fdopen(fd, "wb") as out:
                    out.write(data)
                    out.flush()
                    os.fsync(out.fileno())
                os.replace(tmp, path)
            finally:
                if os.path.exists(tmp):
                    os.remove(tmp)
            _atomic_append(self.events_path, {
                "schema_version": SCHEMA_VERSION,
                "event": "REGISTER", "address": address,
                "bytes": len(data),
            })
        return address

    def pin(self, address: str, metadata: Mapping[str, Any]) -> None:
        """Append a pin record binding an address to series metadata."""
        if self._object_bytes(address) is None:
            raise CADSError(f"cannot pin absent object: {address}")
        _atomic_append(self.pins_path, {
            "schema_version": SCHEMA_VERSION,
            "event": "PIN", "address": address,
            "metadata": dict(metadata),
        })

    def resolve(self, address: str) -> bytes:
        """Resolve an address to bytes; verify integrity on every resolve.

        A mismatched re-hash raises CADSIntegrityError (incident +
        fail-closed): the store never returns drifted bytes.
        """
        data = self._object_bytes(address)
        if data is None:
            raise CADSError(f"CADS object absent: {address}")
        actual = sha256_bytes(data)
        if actual != address:
            raise CADSIntegrityError(
                f"CADS object {address} re-hashed to {actual}: "
                "corruption incident, fail-closed"
            )
        return data

    def verify(self, address: str) -> str:
        """Read-only integrity probe.  Returns PRESENT_VERIFIED,
        PRESENT_CORRUPT, or ABSENT."""
        data = self._object_bytes(address)
        if data is None:
            return "ABSENT"
        return ("PRESENT_VERIFIED" if sha256_bytes(data) == address
                else "PRESENT_CORRUPT")

    def restore(self, address: str, backup_object_path: str) -> None:
        """Restore an object from a backup file (read/restore only).

        The backup bytes are verified against the address BEFORE the
        restore; a mismatch refuses the restore (never a blind copy).
        """
        digest = sha256_file(backup_object_path)
        if digest != address:
            raise CADSIntegrityError(
                f"restore refused: backup {backup_object_path} hashes to "
                f"{digest}, not {address}"
            )
        path = self._object_path(address)
        if os.path.exists(path) and sha256_file(path) == address:
            return  # already intact
        fd, tmp = tempfile.mkstemp(
            prefix="tmp_restore_", dir=os.path.dirname(path)
        )
        try:
            with os.fdopen(fd, "wb") as out, open(backup_object_path, "rb") as src:
                out.write(src.read())
                out.flush()
                os.fsync(out.fileno())
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
        _atomic_append(self.events_path, {
            "schema_version": SCHEMA_VERSION,
            "event": "RESTORE", "address": address,
            "source": "backup",
        })

    # -- journals --------------------------------------------------------- #
    def pins(self) -> list[dict]:
        return _read_journal(self.pins_path)

    def events(self) -> list[dict]:
        return _read_journal(self.events_path)
