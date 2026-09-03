"""Deterministic rate-limited downloader for the stocks-free-v1 lane (A2, Z1).

Implements PLAN_stocks_free.md section 4.1 items 4, 12, 13:
- deterministic fetch of public files into the repo-external staging area
  (raw payloads never enter Git);
- SHA-256 per file (checksum manifest input);
- polite rate limiting per host, bounded retries with exponential backoff,
  explicit polite User-Agent, strictly serial (no parallel hammering);
- two-pull revision comparison. A >=1h spacing between pulls is not possible
  within one session, so the module implements and tests the comparison logic
  and the lane runs two IMMEDIATE pulls: byte equality is expected for static
  endpoints and any divergence is recorded as revision-delta evidence, never
  silently dropped.

Transport is injectable so unit tests run fully offline.
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Dict, Optional, Tuple
from urllib.parse import urlsplit

POLITE_USER_AGENT = (
    "stocks-free-v1-research-audit/1.0 "
    "(zero-cost academic-style research; no redistribution; "
    "python-urllib; serial, rate-limited)"
)

# Transient HTTP statuses worth a retry; 429 is retried a bounded number of
# times with backoff because hammering is exactly what must be avoided.
RETRYABLE_STATUS = frozenset({408, 425, 429, 500, 502, 503, 504})


@dataclass(frozen=True)
class DownloadResult:
    url: str
    status: Optional[int]
    path: str
    sha256: str
    size_bytes: int
    fetched_at_utc: str
    elapsed_s: float
    attempts: int
    content_type: str
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class TwoPullRecord:
    """Comparison of two pulls of the same static URL."""

    url: str
    sha256_pull_a: str
    sha256_pull_b: str
    size_a: int
    size_b: int
    fetched_a_utc: str
    fetched_b_utc: str
    byte_equal: bool
    sha_equal: bool
    interval_s: float
    note: str

    def to_dict(self) -> dict:
        return asdict(self)


Transport = Callable[[urllib.request.Request], Tuple[int, str, bytes]]
"""Returns (http_status, content_type, body). May raise OSError/URLError."""


def make_default_transport(timeout_s: float = 30.0) -> Transport:
    """Real HTTP transport built on python-urllib (stdlib only)."""
    opener = urllib.request.build_opener()

    def _call(req: urllib.request.Request):
        try:
            with opener.open(req, timeout=timeout_s) as resp:
                return resp.status, resp.headers.get("Content-Type", ""), resp.read()
        except urllib.error.HTTPError as err:  # surface status for retry logic
            content_type = err.headers.get("Content-Type", "") if err.headers else ""
            body = err.read() if err.fp is not None else b""
            return err.code, content_type, body

    return _call


class Downloader:
    """Serial, polite, checksumming downloader into ``base_dir``."""

    def __init__(
        self,
        base_dir,
        log_path=None,
        min_interval_s: float = 2.0,
        max_retries: int = 3,
        backoff_base_s: float = 1.5,
        timeout_s: float = 30.0,
        user_agent: str = POLITE_USER_AGENT,
        transport: Optional[Transport] = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
        utcnow: Callable[[], str] = None,
    ) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = Path(log_path) if log_path else None
        self.min_interval_s = float(min_interval_s)
        self.max_retries = int(max_retries)
        self.backoff_base_s = float(backoff_base_s)
        self.timeout_s = float(timeout_s)
        self.user_agent = user_agent
        self._transport: Transport = transport or make_default_transport(timeout_s)
        self._sleep = sleep
        self._clock = clock
        from datetime import datetime, timezone

        self._utcnow = utcnow or (
            lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        )
        self._last_fetch_by_host: Dict[str, float] = {}
        self.log_entries: list = []

    # ------------------------------------------------------------------ core
    def _polite_wait(self, host: str) -> None:
        last = self._last_fetch_by_host.get(host)
        if last is not None:
            remaining = self.min_interval_s - (self._clock() - last)
            if remaining > 0:
                self._sleep(remaining)

    def _mark_host(self, host: str) -> None:
        self._last_fetch_by_host[host] = self._clock()

    def _log(self, entry: dict) -> None:
        self.log_entries.append(entry)
        if self.log_path is not None:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, sort_keys=True) + "\n")

    def fetch(self, url: str, rel_path: str, max_bytes: Optional[int] = None) -> DownloadResult:
        """Fetch ``url`` to ``base_dir/rel_path`` with retries; return evidence."""
        dest = (self.base_dir / rel_path).resolve()
        if self.base_dir.resolve() not in dest.parents:
            raise ValueError(f"rel_path escapes staging base: {rel_path}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        host = urlsplit(url).netloc
        status: Optional[int] = None
        content_type = ""
        body = b""
        note = ""
        attempts = 0
        started = self._clock()
        while attempts <= self.max_retries:
            attempts += 1
            self._polite_wait(host)
            try:
                req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
                status, content_type, body = self._transport(req)
            except (urllib.error.URLError, OSError, TimeoutError) as exc:
                status, content_type, body = None, "", b""
                note = f"transport-error: {type(exc).__name__}: {exc}"[:300]
            self._mark_host(host)
            if status is not None and status == 200:
                note = ""
                break
            if attempts <= self.max_retries and (
                status is None or status in RETRYABLE_STATUS
            ):
                backoff = self.backoff_base_s * (2 ** (attempts - 1))
                self._log(
                    {
                        "event": "retry",
                        "url": url,
                        "attempt": attempts,
                        "status": status,
                        "note": note,
                        "backoff_s": backoff,
                    }
                )
                self._sleep(backoff)
            else:
                break
        elapsed = self._clock() - started
        if status == 200:
            if max_bytes is not None and len(body) > max_bytes:
                note = f"payload {len(body)}B exceeds max_bytes={max_bytes}; not written"
                sha256 = ""
                size = len(body)
            else:
                dest.write_bytes(body)
                sha256 = sha256_bytes(body)
                size = len(body)
        else:
            # evidence preservation: a non-200 response body (bot challenge,
            # fabricated 404, rate-limit text) is part of the access evidence
            sha256, size = "", 0
            if body:
                evidence = dest.with_suffix(f"{dest.suffix}.status{status}.body")
                evidence.write_bytes(body)
                note = (note or f"final status {status}") + (
                    f"; response body preserved as {evidence.name}"
                )
        result = DownloadResult(
            url=url,
            status=status,
            path=str(dest) if status == 200 and not note else "",
            sha256=sha256,
            size_bytes=size,
            fetched_at_utc=self._utcnow(),
            elapsed_s=round(elapsed, 4),
            attempts=attempts,
            content_type=content_type,
            note=note or ("" if status == 200 else f"final status {status}: {note}"),
        )
        self._log({"event": "fetch", **result.to_dict()})
        return result

    # ------------------------------------------------------------- two-pull
    def two_pull_immediate(self, url: str, rel_path_fmt: str) -> TwoPullRecord:
        """Pull the same static URL twice back-to-back and compare bytes.

        Honest limitation: a >=1h spacing is impossible within one session.
        Static endpoints are expected to be byte-identical; any divergence is
        recorded as revision-delta evidence, never silently dropped.
        """
        stamp = self._utcnow()
        a = self.fetch(url, rel_path_fmt.format(pull="a", stamp=stamp))
        b = self.fetch(url, rel_path_fmt.format(pull="b", stamp=stamp))
        return compare_two_pulls(
            a,
            b,
            note=(
                "immediate back-to-back pulls (>=1h spacing impossible "
                "in-session); byte equality expected for static endpoints; "
                "divergence would be recorded as revision-delta evidence"
            ),
        )


def compare_two_pulls(a: DownloadResult, b: DownloadResult, note: str = "") -> TwoPullRecord:
    """Pure comparison of two :class:`DownloadResult` records."""
    sha_equal = bool(a.sha256) and a.sha256 == b.sha256
    return TwoPullRecord(
        url=a.url,
        sha256_pull_a=a.sha256,
        sha256_pull_b=b.sha256,
        size_a=a.size_bytes,
        size_b=b.size_bytes,
        fetched_a_utc=a.fetched_at_utc,
        fetched_b_utc=b.fetched_at_utc,
        byte_equal=sha_equal and a.size_bytes == b.size_bytes,
        sha_equal=sha_equal,
        interval_s=0.0,
        note=note,
    )


def sha256_bytes(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def write_checksum_manifest(paths, out_path, base_dir=None) -> list:
    """Write a JSON checksum manifest for ``paths``; return the manifest rows."""
    import datetime as _dt

    rows = []
    for p in sorted(Path(x) for x in paths):
        rows.append(
            {
                "file": str(p.relative_to(base_dir)) if base_dir else str(p),
                "sha256": sha256_file(p),
                "size_bytes": p.stat().st_size,
            }
        )
    manifest = {
        "schema": "stocks_free_v1/checksum_manifest@1",
        "generated_at_utc": _dt.datetime.now(_dt.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "files": rows,
    }
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return rows
