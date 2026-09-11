"""Telemetry: OpenTelemetry traces/metrics with a no-op default.

Frozen V3 observability contract (plan section 7):

- stable identifiers: trace_id, cycle_id, phase_id, lane_id, job_id,
  run_id, dataset_id, gate_id;
- the DEFAULT library behavior is no-op (API tracer, no SDK configured);
  the SDK is injected only at the controller boundary;
- the only supported exporter is LOCAL JSONL (gitignored runtime dir);
  there is no network exporter;
- redaction denylist is applied to every attribute and event; denied
  keys never reach the exporter;
- telemetry must be disable-able without changing research outputs
  (noninterference test compares scientific bytes on/off).

Forbidden telemetry: API keys, tokens, cookies, request headers, env
dumps, raw provider rows, S1 paths/identities, PnL/PF/Sharpe/drawdown or
unpublished outcome metrics, prompts/transcripts.
"""

from __future__ import annotations

import json
import os
import re
import threading
from typing import Any, Mapping

SCHEMA_VERSION = "v3_telemetry@1"

#: Denylist substrings (lowercase) for attribute/event keys.
KEY_DENYLIST = (
    "api_key", "apikey", "authorization", "cookie", "password", "secret",
    "token", "credential", "private_key", "pnl", "profit", "sharpe",
    "drawdown", "expectancy", "profit_factor", "stress_pnl", "breakeven",
    "outcome", "prompt", "transcript",
)

#: S1 path fragments that must never appear in telemetry values.
S1_PATH_FRAGMENTS = ("/s1/", "s1_sealed", "sealed_s1")

_URL_SECRET_RE = re.compile(r"[?&](key|token|sig|signature|api_key|apikey)=",
                             re.IGNORECASE)

_ENV_SHAPE_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
ENV_MAP_KEYS = ("env", "environ", "environment", "os_environ")


class RedactionError(Exception):
    pass


def _is_env_map_shaped(mapping: Mapping) -> bool:
    keys = list(mapping.keys())
    if any(str(k).lower() in ENV_MAP_KEYS for k in keys):
        return True
    return bool(keys) and all(
        _ENV_SHAPE_RE.match(str(k)) for k in keys
    )


def redact_value(value: Any) -> Any:
    """Redact a single value: URLs with query secrets, S1 paths, env-like
    maps and raw payload snippets are dropped/redacted."""
    if isinstance(value, str):
        if any(frag in value.lower() for frag in S1_PATH_FRAGMENTS):
            return "[REDACTED_S1_PATH]"
        if _URL_SECRET_RE.search(value):
            return "[REDACTED_URL_SECRET]"
        if len(value) > 512:  # raw payload snippet guard
            return "[REDACTED_LONG_VALUE]"
        return value
    if isinstance(value, Mapping):
        if _is_env_map_shaped(value):
            return "[REDACTED_MAP]"  # environment dumps dropped wholesale
        return redact_attributes(value)
    if isinstance(value, (list, tuple)):
        if len(value) > 64:
            return "[REDACTED_LIST]"
        return [redact_value(v) for v in value]
    return value


def redact_attributes(attrs: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in attrs.items():
        k_lower = key.lower()
        if any(tok in k_lower for tok in KEY_DENYLIST):
            out[key] = "[REDACTED_KEY]"
            continue
        out[key] = redact_value(value)
    return out


class Telemetry:
    """Telemetry facade.  Subclasses: NoopTelemetry (default) and
    JsonlTelemetry (local exporter, controller boundary only)."""

    kind = "noop"

    def span_start(self, name: str, **attrs: Any) -> Any:  # pragma: no cover
        raise NotImplementedError

    def span_end(self, span: Any, status: str = "OK") -> None:  # pragma: no cover
        raise NotImplementedError

    def event(self, name: str, **attrs: Any) -> None:  # pragma: no cover
        raise NotImplementedError


class NoopTelemetry(Telemetry):
    """Default: no SDK, no files, no output.  Research outputs unchanged."""

    kind = "noop"

    class _NoopSpan:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def span_start(self, name: str, **attrs: Any) -> Any:
        return NoopTelemetry._NoopSpan()

    def span_end(self, span: Any, status: str = "OK") -> None:
        return None

    def event(self, name: str, **attrs: Any) -> None:
        return None


class JsonlTelemetry(Telemetry):
    """Append-only LOCAL JSONL exporter under a gitignored runtime dir."""

    kind = "jsonl"

    def __init__(self, path: str, trace_id: str,
                 identifiers: Mapping[str, str] | None = None):
        self._path = path
        self._trace_id = trace_id
        self._identifiers = dict(identifiers or {})
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        if not os.environ.get("V3_TELEMETRY_DISABLE", ""):
            self._fh = open(path, "a", encoding="utf-8")
        else:  # globally disabled: behaves exactly like the no-op
            self._fh = None
            self.kind = "jsonl-disabled"

    def _write(self, record: Mapping[str, Any]) -> None:
        if self._fh is None:
            return
        payload = {
            "schema_version": SCHEMA_VERSION,
            "trace_id": self._trace_id,
            **{k: v for k, v in self._identifiers.items()},
            **redact_attributes(record),
        }
        with self._lock:
            self._fh.write(
                json.dumps(payload, sort_keys=True, default=str) + "\n"
            )
            self._fh.flush()

    class _JsonlSpan:
        def __init__(self, outer: "JsonlTelemetry", name: str,
                     attrs: dict[str, Any]):
            self._outer = outer
            self._name = name
            self._attrs = attrs

        def __enter__(self):
            self._outer._write({"event": "span_start", "name": self._name,
                                "attributes": self._attrs})
            return self

        def __exit__(self, exc_type, exc, tb):
            status = "ERROR" if exc_type else "OK"
            self._outer._write({"event": "span_end", "name": self._name,
                                "status": status})
            return False

    def span_start(self, name: str, **attrs: Any) -> Any:
        return JsonlTelemetry._JsonlSpan(self, name, dict(attrs))

    def span_end(self, span: Any, status: str = "OK") -> None:
        return None  # spans self-close via context manager

    def event(self, name: str, **attrs: Any) -> None:
        self._write({"event": name, "attributes": dict(attrs)})

    def close(self) -> None:
        if self._fh is not None:
            self._fh.close()
            self._fh = None


def telemetry_from_env(path: str, trace_id: str,
                       identifiers: Mapping[str, str] | None = None
                       ) -> Telemetry:
    """Controller boundary: enable JSONL telemetry only when explicitly
    configured; default stays no-op."""
    if os.environ.get("V3_TELEMETRY", "") == "jsonl":
        return JsonlTelemetry(path, trace_id, identifiers)
    return NoopTelemetry()
