"""Shared context and helpers for HTTP source adapters."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests

from ..contract import CredentialMissing, PARSER_VERSION, SchemaRefusal
from ..http import DiskGuard, RateLimiter, redact_headers


@dataclass
class SourceContext:
    raw_root: Path
    control_dir: Path
    session: requests.Session
    limiters: Dict[str, RateLimiter]
    disk_guard: DiskGuard
    presence: Dict[str, str]
    secret_loader: Callable[[str], str]
    default_timeout: Tuple[float, float] = (10.0, 60.0)

    def limiter_for(self, name: str, min_interval: float) -> RateLimiter:
        if name not in self.limiters:
            self.limiters[name] = RateLimiter(min_interval)
        return self.limiters[name]

    def source_dir(self, source_id: str) -> Path:
        path = self.raw_root / source_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def require_present(self, name: str) -> str:
        if self.presence.get(name) != "PRESENT":
            raise CredentialMissing(f"{name} MISSING; fail closed")
        return self.secret_loader(name)


class SourceRun:
    """Accumulates records + summary verdict for one source in one run."""

    def __init__(self, source_id: str, census: Dict[str, Any]) -> None:
        self.source_id = source_id
        self.records: List[Dict[str, Any]] = []
        self.census = census
        self.events: List[Dict[str, Any]] = []
        self.notes: List[str] = []

    def add(self, record: Dict[str, Any]) -> None:
        self.records.append(record)

    def event(self, kind: str, detail: Dict[str, Any]) -> None:
        self.events.append({"kind": kind, "detail": detail})

    def summarize(self) -> Dict[str, Any]:
        from ..contract import source_verdict

        verdict = source_verdict(
            [r for r in self.records if r["raw_path"]], self.source_id
        )
        if any(r["authority_status"].startswith("BLOCKED") for r in self.records):
            blocked = sorted({r["authority_status"] for r in self.records})
            if verdict["status"] == "PASS_INVENTORY_ONLY":
                verdict["status"] = blocked[0]
        return {
            "source_id": self.source_id,
            "status": verdict["status"],
            "objects": verdict["objects"],
            "parser_version": PARSER_VERSION,
            "records": self.records,
            "events": self.events,
            "notes": self.notes,
            "census": self.census,
        }


def strict_json_probe(payload: bytes, required: List[str], what: str) -> Any:
    """Parse JSON and require top-level keys (schema refusal otherwise)."""
    try:
        data = json.loads(payload)
    except (ValueError, UnicodeDecodeError) as exc:
        raise SchemaRefusal(f"{what}: not JSON ({exc})") from exc
    if isinstance(data, dict):
        missing = [key for key in required if key not in data]
        if missing:
            raise SchemaRefusal(f"{what}: missing keys {missing}")
    elif isinstance(data, list):
        if required and not data:
            raise SchemaRefusal(f"{what}: unexpectedly empty list")
    else:
        raise SchemaRefusal(f"{what}: unexpected top-level type {type(data).__name__}")
    return data


def session_with_headers(headers: Dict[str, str]) -> requests.Session:
    sess = requests.Session()
    sess.headers.update(headers)
    return sess
