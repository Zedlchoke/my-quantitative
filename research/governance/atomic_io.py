"""Transactional JSON state IO for control-plane files (SHV1 sec7.3).

Protocol, in order:
1. schema validation BEFORE write;
2. write to a sibling temporary file;
3. fsync where supported;
4. atomic rename (os.replace);
5. post-write read-back and validation (bytes must match);
6. caller appends an event describing the transition (see cycle_registry).

Concurrency: an flock sidecar serializes writers and a compare-and-swap on the
previous content sha256 fails closed against lost updates. Malformed, truncated
or stale state is CONTROL_STATE_DRIFT - never a recoverable default.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
from typing import Callable, Optional

CONTROL_STATE_DRIFT = "CONTROL_STATE_DRIFT"


class SchemaValidationError(ValueError):
    """Object failed schema validation before write (or after read)."""


class ControlStateDrift(RuntimeError):
    """Malformed / truncated / stale control state - fail closed."""


class WriteLockBusy(RuntimeError):
    """Another writer holds the sidecar flock within the allowed wait."""


def sha256_file(path: os.PathLike | str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_bytes(obj) -> bytes:
    return (json.dumps(obj, indent=1, ensure_ascii=False) + "\n").encode("utf-8")


def atomic_write_json(
    path: os.PathLike | str,
    obj,
    *,
    schema_validator: Callable[[dict], None],
    expect_prev_sha: Optional[str] = None,
    lock_timeout: float = 5.0,
) -> str:
    """Write obj to path transactionally; returns the new content sha256.

    Fails closed without touching the file on: schema violation, CAS mismatch
    (expect_prev_sha given and current bytes differ), or sidecar lock busy.
    """
    path = Path(path)
    schema_validator(obj)
    payload = canonical_bytes(obj)

    lock_path = path.with_name(path.name + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise WriteLockBusy(
                f"{path.name}: sidecar lock held by another writer ({exc})"
            ) from exc
        if path.exists():
            current = hashlib.sha256(path.read_bytes()).hexdigest()
            if expect_prev_sha is not None and current != expect_prev_sha:
                raise ControlStateDrift(
                    f"{path.name}: CAS mismatch (expected prev {expect_prev_sha[:12]}, "
                    f"found {current[:12]}) - concurrent writer detected"
                )
        tmp_path = path.with_name(f"{path.name}.tmp.{os.getpid()}")
        with open(tmp_path, "wb") as fh:
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, path)
        # 5. post-write read-back: bytes and schema must both match
        readback = path.read_bytes()
        if readback != payload:
            raise ControlStateDrift(f"{path.name}: post-write readback bytes differ")
        schema_validator(json.loads(readback.decode("utf-8")))
        return hashlib.sha256(readback).hexdigest()
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def load_json_strict(
    path: os.PathLike | str,
    *,
    schema_validator: Optional[Callable[[dict], None]] = None,
) -> dict:
    """Load a control JSON; any malformation is CONTROL_STATE_DRIFT."""
    path = Path(path)
    if not path.exists():
        raise ControlStateDrift(f"{path.name}: missing control state")
    raw = path.read_bytes()
    try:
        obj = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ControlStateDrift(f"{path.name}: unparseable control state ({exc})") from exc
    if not isinstance(obj, dict):
        raise ControlStateDrift(f"{path.name}: control state is not a JSON object")
    if schema_validator is not None:
        schema_validator(obj)
    return obj


def append_event(events_path: os.PathLike | str, event: dict) -> None:
    """Append-only transition journal (sec7.3 item 6). Never rewrites history."""
    import datetime

    path = Path(events_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {"utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    row.update(event)
    lock_path = path.with_name(path.name + ".lock")
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def read_events(events_path: os.PathLike | str) -> list:
    path = Path(events_path)
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows
