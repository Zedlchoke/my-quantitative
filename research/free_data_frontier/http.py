"""HTTP acquisition kernel: redaction, request identity, rate limiting,
bounded retry, disk floor, atomic writes, sha256, HTTP metadata capture.

Every stored URL/header is redacted; credentials exist only in memory at
request construction time.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import time
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

from .contract import (
    DEFAULT_TIMEOUT_SECONDS,
    DISK_FLOOR_BYTES,
    LARGE_DOWNLOAD_READ_TIMEOUT_SECONDS,
    UNKNOWN_SIZE_REFUSE_ABOVE_BYTES,
    DiskFloorError,
    PARSER_VERSION,
    iso_utc,
)

REDACTED = "<redacted>"
REDACTED_PARAM_NAMES = {"api_key", "apikey", "key", "token", "access_token", "auth"}
REDACTED_HEADER_NAMES = {"authorization", "x-api-key", "cookie", "set-cookie"}


def redact_query(url: str) -> str:
    """Redact credential query params from a URL (values never stored)."""
    parsed = urllib.parse.urlsplit(url)
    if not parsed.query:
        return url
    pairs = []
    for chunk in parsed.query.split("&"):
        name, sep, _value = chunk.partition("=")
        if name.lower() in REDACTED_PARAM_NAMES:
            pairs.append(f"{name}{sep}{REDACTED}")
        else:
            pairs.append(chunk)
    return urllib.parse.urlunsplit(parsed._replace(query="&".join(pairs)))


def redact_headers(headers: Optional[Dict[str, str]]) -> Dict[str, str]:
    """Redact credential headers; also replace any embedded secret-looking
    contact value with a length descriptor so manifests carry no PII."""
    out: Dict[str, str] = {}
    for name, value in sorted((headers or {}).items()):
        lowered = name.lower()
        if lowered in REDACTED_HEADER_NAMES:
            out[name] = REDACTED
        elif "@" in value:  # contact-style User-Agent values stay out of Git
            out[name] = f"<redacted:contact:len={len(value)}>"
        else:
            out[name] = value
    return out


def canonical_request_identity(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]],
    body: Optional[bytes] = None,
) -> Tuple[str, str]:
    """Deterministic request identity over redacted canonical fields."""
    redacted_url = redact_query(url)
    redacted_headers = redact_headers(headers)
    canonical = {
        "method": method.upper(),
        "url": redacted_url,
        "headers": redacted_headers,
        "body_sha256": hashlib.sha256(body or b"").hexdigest(),
    }
    blob = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest(), redacted_url


class RateLimiter:
    """Minimum-interval limiter between requests for one host family."""

    def __init__(self, min_interval_seconds: float) -> None:
        if min_interval_seconds <= 0:
            raise ValueError("min_interval_seconds must be positive")
        self.min_interval = min_interval_seconds
        self._last: Optional[float] = None

    def wait(self) -> None:
        now = time.monotonic()
        if self._last is not None:
            remaining = self.min_interval - (now - self._last)
            if remaining > 0:
                time.sleep(remaining)
        self._last = time.monotonic()


class RetryPolicy:
    """Bounded retry: network errors, timeouts, 429 and 5xx only."""

    def __init__(self, max_attempts: int = 3, backoff_base_seconds: float = 1.0) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        self.max_attempts = max_attempts
        self.backoff_base = backoff_base_seconds

    def retryable_status(self, status: int) -> bool:
        return status == 429 or 500 <= status < 600

    def sleep_backoff(self, attempt: int) -> None:
        time.sleep(self.backoff_base * (2 ** (attempt - 1)))


class DiskGuard:
    """Refuse downloads that would leave under DISK_FLOOR_BYTES free."""

    def __init__(self, floor_bytes: int = DISK_FLOOR_BYTES) -> None:
        self.floor_bytes = floor_bytes

    def free_bytes(self, path: Path) -> int:
        return shutil.disk_usage(str(path)).free

    def assert_download_fits(
        self, dest_root: Path, content_length: Optional[int]
    ) -> Dict[str, Any]:
        free = self.free_bytes(dest_root)
        if content_length is None:
            # Unknown size: refuse anything plausibly large (fail closed).
            if free - UNKNOWN_SIZE_REFUSE_ABOVE_BYTES < self.floor_bytes:
                raise DiskFloorError(
                    f"unknown-size download and free={free} too close to floor"
                )
            return {"free_before": free, "content_length": None, "verdict": "UNKNOWN_SIZE_ALLOWED"}
        if free - content_length < self.floor_bytes:
            raise DiskFloorError(
                f"download of {content_length} bytes would leave {free - content_length} "
                f"free (< floor {self.floor_bytes})"
            )
        return {"free_before": free, "content_length": content_length, "verdict": "FITS"}


class AtomicSink:
    """Stream bytes to a temp file in the destination dir, hash, fsync,
    atomically replace. Enforces the floor incrementally while streaming."""

    def __init__(
        self,
        dest: Path,
        disk_guard: DiskGuard,
        max_bytes: Optional[int] = None,
    ) -> None:
        self.dest = dest
        self.disk_guard = disk_guard
        self.max_bytes = max_bytes
        self.bytes_written = 0
        self.sha256 = hashlib.sha256()
        self._tmp: Optional[Path] = None
        self._handle = None

    def __enter__(self) -> "AtomicSink":
        self.dest.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            prefix=f".{self.dest.name}.", suffix=".part", dir=str(self.dest.parent)
        )
        self._tmp = Path(tmp_name)
        self._handle = os.fdopen(fd, "wb")
        return self

    def write(self, chunk: bytes) -> None:
        if not chunk:
            return
        self.bytes_written += len(chunk)
        if self.max_bytes is not None and self.bytes_written > self.max_bytes:
            raise DiskFloorError(
                f"download exceeded declared cap {self.max_bytes} at {self.bytes_written}"
            )
        self._handle.write(chunk)
        self.sha256.update(chunk)

    def commit(self) -> Tuple[str, int]:
        self._handle.flush()
        os.fsync(self._handle.fileno())
        self._handle.close()
        if self.disk_guard.free_bytes(self.dest.parent) < self.disk_guard.floor_bytes:
            self._tmp.unlink(missing_ok=True)
            raise DiskFloorError("free space fell below floor; download aborted")
        os.replace(str(self._tmp), str(self.dest))
        return self.sha256.hexdigest(), self.bytes_written

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._handle is not None and not self._handle.closed:
            self._handle.close()
        if self._tmp is not None and self._tmp.exists():
            self._tmp.unlink(missing_ok=True)


@dataclass
class RetrievalResult:
    request_id: str
    url_redacted: str
    http_status: Optional[int]
    content_type: Optional[str]
    content_length: Optional[int]
    retrieved_time_utc: str
    raw_path: Optional[Path]
    raw_sha256: Optional[str]
    bytes_written: int
    response_headers_redacted: Dict[str, str]
    attempts: int = 1
    notes: List[str] = field(default_factory=list)
    error: Optional[str] = None


def retrieve(
    method: str,
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    body: Optional[bytes] = None,
    session: Optional[requests.Session] = None,
    limiter: Optional[RateLimiter] = None,
    retry: Optional[RetryPolicy] = None,
    dest: Optional[Path] = None,
    disk_guard: Optional[DiskGuard] = None,
    max_bytes: Optional[int] = None,
    timeout: Tuple[float, float] = DEFAULT_TIMEOUT_SECONDS,
    verify_content_length: bool = False,
) -> RetrievalResult:
    """One bounded, redacted, rate-limited, retried HTTP retrieval.

    dest=None -> response held in memory (JSON/inventory use, bounded by
    max_bytes). dest=path -> streamed to an atomic sink.
    """
    retry = retry or RetryPolicy()
    guard = disk_guard or DiskGuard()
    sess = session or requests.Session()
    request_id, url_redacted = canonical_request_identity(method, url, headers, body)
    last_error: Optional[str] = None
    last_status: Optional[int] = None

    if dest is not None and verify_content_length:
        head = sess.head(url, headers=headers, timeout=timeout, allow_redirects=True)
        length_header = head.headers.get("Content-Length")
        guard.assert_download_fits(
            dest.parent, int(length_header) if length_header else None
        )

    for attempt in range(1, retry.max_attempts + 1):
        if limiter is not None:
            limiter.wait()
        try:
            response = sess.request(
                method,
                url,
                headers=headers,
                data=body,
                timeout=timeout,
                stream=dest is not None,
            )
            last_status = response.status_code
            if not response.ok:
                if retry.retryable_status(response.status_code) and attempt < retry.max_attempts:
                    response.close()
                    retry.sleep_backoff(attempt)
                    continue
                return RetrievalResult(
                    request_id=request_id,
                    url_redacted=url_redacted,
                    http_status=response.status_code,
                    content_type=response.headers.get("Content-Type"),
                    content_length=_int_header(response.headers.get("Content-Length")),
                    retrieved_time_utc=iso_utc(time.time()),
                    raw_path=None,
                    raw_sha256=None,
                    bytes_written=0,
                    response_headers_redacted=redact_headers(dict(response.headers)),
                    attempts=attempt,
                    error=f"HTTP {response.status_code}",
                )
            if dest is None:
                payload = response.content
                if max_bytes is not None and len(payload) > max_bytes:
                    return RetrievalResult(
                        request_id=request_id,
                        url_redacted=url_redacted,
                        http_status=response.status_code,
                        content_type=response.headers.get("Content-Type"),
                        content_length=len(payload),
                        retrieved_time_utc=iso_utc(time.time()),
                        raw_path=None,
                        raw_sha256=None,
                        bytes_written=0,
                        response_headers_redacted=redact_headers(dict(response.headers)),
                        attempts=attempt,
                        error=f"payload {len(payload)} exceeds max_bytes {max_bytes}",
                    )
                return RetrievalResult(
                    request_id=request_id,
                    url_redacted=url_redacted,
                    http_status=response.status_code,
                    content_type=response.headers.get("Content-Type"),
                    content_length=len(payload),
                    retrieved_time_utc=iso_utc(time.time()),
                    raw_path=None,
                    raw_sha256=hashlib.sha256(payload).hexdigest(),
                    bytes_written=len(payload),
                    response_headers_redacted=redact_headers(dict(response.headers)),
                    attempts=attempt,
                )
            guard.assert_download_fits(
                _ensure_dir(dest.parent),
                _int_header(response.headers.get("Content-Length")),
            )
            sink_timeout = (
                timeout[0],
                max(timeout[1], LARGE_DOWNLOAD_READ_TIMEOUT_SECONDS),
            )
            response.timeout = sink_timeout  # requests honors this while streaming
            with AtomicSink(dest, guard, max_bytes=max_bytes) as sink:
                for chunk in response.iter_content(chunk_size=1024 * 512):
                    sink.write(chunk)
                digest, written = sink.commit()
            return RetrievalResult(
                request_id=request_id,
                url_redacted=url_redacted,
                http_status=response.status_code,
                content_type=response.headers.get("Content-Type"),
                content_length=_int_header(response.headers.get("Content-Length")),
                retrieved_time_utc=iso_utc(time.time()),
                raw_path=dest,
                raw_sha256=digest,
                bytes_written=written,
                response_headers_redacted=redact_headers(dict(response.headers)),
                attempts=attempt,
            )
        except (requests.ConnectionError, requests.Timeout) as exc:
            last_error = f"{type(exc).__name__}"
            if attempt < retry.max_attempts:
                retry.sleep_backoff(attempt)
                continue
    return RetrievalResult(
        request_id=request_id,
        url_redacted=url_redacted,
        http_status=last_status,
        content_type=None,
        content_length=None,
        retrieved_time_utc=iso_utc(time.time()),
        raw_path=None,
        raw_sha256=None,
        bytes_written=0,
        response_headers_redacted={},
        attempts=retry.max_attempts,
        error=last_error or "retries exhausted",
    )


def two_pull_equality(
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    session: Optional[requests.Session] = None,
    limiter: Optional[RateLimiter] = None,
    max_bytes: int = 64 * 1024 * 1024,
) -> Dict[str, Any]:
    """Re-pull an allegedly immutable object and compare digests."""
    first = retrieve(
        "GET", url, headers=headers, session=session, limiter=limiter, max_bytes=max_bytes
    )
    if first.error:
        return {"verdict": "NOT_RUN", "reason": first.error}
    second = retrieve(
        "GET", url, headers=headers, session=session, limiter=limiter, max_bytes=max_bytes
    )
    if second.error:
        return {"verdict": "NOT_RUN", "reason": second.error}
    equal = first.raw_sha256 == second.raw_sha256
    return {
        "verdict": "IDENTICAL" if equal else "MUTATED",
        "first_sha256": first.raw_sha256,
        "second_sha256": second.raw_sha256,
    }


def _int_header(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_record(
    result: RetrievalResult,
    *,
    source_id: str,
    dataset_id: str,
    authority_status: str,
    event_time_utc: Optional[str] = None,
    effective_time_utc: Optional[str] = None,
    available_time_utc: Optional[str] = None,
    available_time_evidence: Optional[str] = None,
    vintage: Optional[str] = None,
    notes: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Plan section 5 record. retrieved_time never becomes available_time."""
    from .contract import validate_record

    record = {
        "source_id": source_id,
        "dataset_id": dataset_id,
        "canonical_request_id": result.request_id,
        "source_url_redacted": result.url_redacted,
        "retrieved_time_utc": result.retrieved_time_utc,
        "http_status": result.http_status,
        "content_type": result.content_type,
        "content_length": result.content_length,
        "raw_path": str(result.raw_path) if result.raw_path else None,
        "raw_sha256": result.raw_sha256 or "NOT_APPLIED",
        "parser_version": PARSER_VERSION,
        "authority_status": authority_status,
        "event_time_utc": event_time_utc,
        "effective_time_utc": effective_time_utc,
        "available_time_utc": available_time_utc,
        "available_time_evidence": available_time_evidence,
        "vintage": vintage,
        "retrieval_time_only": available_time_utc is None,
        "notes": notes or [],
    }
    if result.error:
        record["notes"] = list(record["notes"]) + [f"error={result.error}"]
    return validate_record(record)
