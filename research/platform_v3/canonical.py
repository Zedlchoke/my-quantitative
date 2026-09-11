"""Canonical serialization + digest helpers shared by all V3 components.

A canonical digest is sha256 over canonical JSON (sorted keys, compact
separators, UTF-8).  Timestamps / generated-at fields are excluded from
scientific identity by callers; this module never strips them implicitly.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


def canonical_bytes(obj: Any) -> bytes:
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        default=str,
    ).encode("utf-8")


def canonical_digest(obj: Any) -> str:
    return hashlib.sha256(canonical_bytes(obj)).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


__all__ = ["canonical_bytes", "canonical_digest", "sha256_bytes", "sha256_file"]
