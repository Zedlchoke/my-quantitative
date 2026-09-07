"""V6-P0b (A3): fail-loud, polite, hash-pinned HTTP retrieval for price evidence.

Design contract (PLAN_stocks_v6 section 6 P0b + handbook section 11):

* every retrieval is recorded with url, http status, sha256, byte count and
  retrieved_time_utc; raw bytes are archived under the gitignored
  ``.staging_prices_v6/`` tree — no raw bytes are ever committed;
* FAIL-LOUD: a non-200 status, an empty body, or a body that does not match
  the expected content class raises :class:`RawFetchError` — an HTTP 200 that
  actually carries an anti-bot challenge page is the canonical trap and is
  detected by content sniffing, not by status code alone;
* POLITE: a minimum spacing between requests to the same host (default
  2.0 s) is enforced in-process; no cookie jar is maintained; the User-Agent
  is an honest research-probe string;
* NO credentials, NO signup, NO click-through acceptance — anything that
  requires those is out of scope by hard boundary (PLAN_stocks_v6 section
  15; handbook section 11.4).

Anti-bot gates are NOT bypassed. When a challenge page is detected the
retrieval is archived as evidence and recorded as a failure with
``blocked_by_bot_verification`` semantics; solving or forging the gate is an
owner decision, never an agent action.
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

USER_AGENT = "quant-research-evidence-probe/1.0 (research-cycle STOCKS-FREE-V6 P0b; no redistribution)"
MIN_REQUEST_SPACING_S = 2.0

CHALLENGE_MARKERS = (
    "requires JavaScript to verify your browser",
    "/__verify",
    "captcha",
    "Just a moment",
)

CONTENT_CLASSES = ("csv", "html_page", "challenge", "json", "binary", "unknown")


class RawFetchError(RuntimeError):
    """A retrieval failed loudly (status, empty body, wrong content class)."""

    def __init__(self, message: str, record: dict):
        super().__init__(message)
        self.record = record


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def classify_content(body: bytes) -> str:
    head = body[:4096].lstrip()
    lowered = body[:8192].lower()
    if any(m.lower().encode() in lowered for m in CHALLENGE_MARKERS):
        return "challenge"
    if not body:
        return "empty"
    text = head.decode("latin-1", errors="replace")
    if text.startswith("<!DOCTYPE") or text.startswith("<html"):
        return "html_page"
    first_line = text.splitlines()[0] if text.splitlines() else ""
    if set(first_line.strip().lower().split(",")) == {"date", "open", "high", "low", "close", "volume"}:
        return "csv"
    if text.lstrip().startswith("{") or text.lstrip().startswith("["):
        return "json"
    return "binary"


class PoliteFetcher:
    """Minimal urllib fetcher with spacing, sniffing and sha256 pinning."""

    def __init__(
        self,
        archive_dir: Path,
        min_spacing_s: float = MIN_REQUEST_SPACING_S,
        timeout_s: float = 45.0,
    ):
        self.archive_dir = Path(archive_dir)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.min_spacing_s = min_spacing_s
        self.timeout_s = timeout_s
        self._last_request_ts: Dict[str, float] = {}
        self.log: List[dict] = []

    def _respect_spacing(self, host: str) -> None:
        last = self._last_request_ts.get(host)
        if last is not None:
            wait = self.min_spacing_s - (time.monotonic() - last)
            if wait > 0:
                time.sleep(wait)
        self._last_request_ts[host] = time.monotonic()

    def fetch(
        self,
        url: str,
        dest_name: str,
        expect: Optional[str] = None,
        archive_on_failure: bool = True,
    ) -> dict:
        """Fetch ``url``, archive raw bytes, verify expected content class.

        Returns the retrieval record. Raises :class:`RawFetchError` on any
        failure mode; when ``archive_on_failure`` is true the offending bytes
        are still archived (and hashed) as evidence before raising.
        """
        host = urllib.request.urlsplit(url).netloc
        self._respect_spacing(host)
        record = {
            "url": url,
            "dest_name": dest_name,
            "retrieved_time_utc": _now_utc(),
            "http_status": None,
            "size_bytes": 0,
            "sha256": None,
            "content_class": "unknown",
            "expected_class": expect,
            "ok": False,
            "error": None,
            "transport": "urllib; no cookies; no credentials",
            "user_agent": USER_AGENT,
        }
        dest = self.archive_dir / dest_name
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                body = resp.read()
                record["http_status"] = resp.status
        except urllib.error.HTTPError as exc:
            record["http_status"] = exc.code
            body = b""
            record["error"] = f"HTTPError {exc.code}: {exc.reason}"
        except Exception as exc:  # transport-level failure
            body = b""
            record["error"] = f"{type(exc).__name__}: {exc}"

        record["size_bytes"] = len(body)
        record["sha256"] = hashlib.sha256(body).hexdigest() if body else None
        record["content_class"] = classify_content(body)

        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(body)

        if record["error"] is not None:
            if not archive_on_failure:
                dest.unlink(missing_ok=True)
            self.log.append(record)
            raise RawFetchError(record["error"], record)
        if record["http_status"] != 200:
            self.log.append(record)
            raise RawFetchError(f"non-200 status {record['http_status']} for {url}", record)
        if not body:
            self.log.append(record)
            raise RawFetchError(f"empty body for {url} (fail-loud, never skipped)", record)
        if record["content_class"] == "challenge":
            self.log.append(record)
            raise RawFetchError(
                "anti-bot challenge page served instead of content; gate NOT bypassed "
                "(owner decision required for any scripted access)",
                record,
            )
        if expect is not None and record["content_class"] != expect:
            self.log.append(record)
            raise RawFetchError(
                f"content class mismatch for {url}: expected {expect}, got {record['content_class']}",
                record,
            )
        record["ok"] = True
        self.log.append(record)
        return record

    def write_manifest(self, manifest_path: Optional[Path] = None) -> Path:
        """sha256 manifest over everything archived so far (recomputed from disk)."""
        return write_dir_manifest(self.archive_dir, manifest_path)


def write_dir_manifest(
    archive_dir: Path, manifest_path: Optional[Path] = None
) -> Path:
    """sha256 manifest over every file under ``archive_dir`` (recomputed from disk).

    Gitignored staging; the manifest pins raw evidence bytes so any consumer
    can verify integrity without committing the bytes themselves.
    """
    archive_dir = Path(archive_dir)
    manifest_path = manifest_path or (archive_dir / "sha256_manifest.json")
    files = {}
    for p in sorted(archive_dir.rglob("*")):
        if p.is_file() and p.name != manifest_path.name:
            files[str(p.relative_to(archive_dir))] = hashlib.sha256(
                p.read_bytes()
            ).hexdigest()
    payload = {
        "schema": "stocks_free_v6_run/p0b_raw_manifest@1",
        "generated_at_utc": _now_utc(),
        "note": "gitignored staging; hashes pin raw evidence bytes",
        "files": files,
    }
    manifest_path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    return manifest_path
