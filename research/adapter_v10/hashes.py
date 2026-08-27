"""Deterministic hashing + atomic artifact writing helpers (G1).

Hashes reuse the repo-wide byte-stable serialiser
(:func:`research.pit_hooks_v10.canonical_repr`) so two independent builds of
the same adapter run MUST agree byte-for-byte. Writes are tmp + fsync +
``os.replace`` so a reader never observes a torn artifact.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import Any, Mapping


def canonical_text(payload: Any) -> str:
    """Byte-stable JSON text for any plain-JSON adapter payload."""
    from research.pit_hooks_v10 import canonical_repr

    return canonical_repr(payload)


def payload_sha256(payload: Any) -> str:
    """sha256 over :func:`canonical_text` -- the deterministic output hash."""
    return hashlib.sha256(canonical_text(payload).encode("utf-8")).hexdigest()


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_json(
    payload: Mapping[str, Any], path: str | Path, *, indent: int = 1
) -> Path:
    """Write sorted human-diffable JSON atomically; returns the final path."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(dict(payload), indent=indent, sort_keys=True, default=str) + "\n"
    tmp = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
    with open(tmp, "w", encoding="utf-8") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, target)
    return target


__all__ = ["atomic_write_json", "canonical_text", "file_sha256", "payload_sha256"]
