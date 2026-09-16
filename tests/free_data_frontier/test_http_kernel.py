import hashlib
import http.server
import threading
import time
from pathlib import Path

import pytest

from research.free_data_frontier.contract import DiskFloorError
from research.free_data_frontier.http import (
    AtomicSink,
    DiskGuard,
    RateLimiter,
    RetryPolicy,
    retrieve,
    two_pull_equality,
)

DISK_FLOOR = 15 * 1024**3


class FakeResponse:
    def __init__(self, status=200, headers=None, body=b"", chunks=None):
        self.status_code = status
        self.headers = headers or {}
        self._body = body
        self._chunks = chunks
        self.closed = False

    @property
    def ok(self):
        return 200 <= self.status_code < 300

    @property
    def content(self):
        return self._body

    def iter_content(self, chunk_size=512 * 1024):
        if self._chunks is not None:
            yield from self._chunks
        else:
            yield self._body

    def close(self):
        self.closed = True


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, headers=None, data=None, timeout=None, stream=False):
        self.calls.append((method, url))
        return self.responses.pop(0)

    def head(self, url, headers=None, timeout=None, allow_redirects=True):
        return FakeResponse(headers={"Content-Length": "4"})


def test_retry_on_500_then_success():
    session = FakeSession(
        [FakeResponse(500), FakeResponse(200, body=b"data")]
    )
    policy = RetryPolicy(max_attempts=3, backoff_base_seconds=0.0)
    result = retrieve("GET", "https://x/y", session=session, retry=policy)
    assert result.http_status == 200
    assert result.raw_sha256 == hashlib.sha256(b"data").hexdigest()
    assert result.attempts == 2


def test_no_retry_on_client_error():
    session = FakeSession([FakeResponse(404)])
    policy = RetryPolicy(max_attempts=3, backoff_base_seconds=0.0)
    result = retrieve("GET", "https://x/y", session=session, retry=policy)
    assert result.http_status == 404
    assert result.error == "HTTP 404"
    assert len(session.calls) == 1


def test_retries_exhausted_records_error():
    session = FakeSession([FakeResponse(503), FakeResponse(503)])
    policy = RetryPolicy(max_attempts=2, backoff_base_seconds=0.0)
    result = retrieve("GET", "https://x/y", session=session, retry=policy)
    assert result.http_status == 503
    assert result.attempts == 2
    assert result.error


def test_rate_limiter_enforces_minimum_interval():
    limiter = RateLimiter(min_interval_seconds=0.05)
    start = time.monotonic()
    limiter.wait()
    limiter.wait()
    elapsed = time.monotonic() - start
    assert elapsed >= 0.05


def test_rate_limiter_invalid_interval_rejected():
    with pytest.raises(ValueError):
        RateLimiter(min_interval_seconds=0)


def test_atomic_download_writes_and_hashes(tmp_path):
    dest = tmp_path / "raw" / "obj.bin"
    payload = b"atomic-bytes" * 1000
    session = FakeSession([FakeResponse(200, body=payload)])
    result = retrieve(
        "GET",
        "https://x/blob",
        session=session,
        dest=dest,
        disk_guard=DiskGuard(),
    )
    assert dest.is_file()
    assert result.bytes_written == len(payload)
    assert result.raw_sha256 == hashlib.sha256(payload).hexdigest()
    assert not list(tmp_path.rglob("*.part"))


def test_atomic_download_no_leftover_on_failure(tmp_path):
    dest = tmp_path / "raw" / "obj.bin"
    guard = DiskGuard()

    class ExplodingSink(AtomicSink):
        def write(self, chunk):
            raise DiskFloorError("mid-stream breach")

    original = AtomicSink.__enter__

    with pytest.raises(DiskFloorError):
        with AtomicSink(dest, guard, max_bytes=10) as sink:
            sink.write(b"0123456789ABCDEF")  # exceeds max_bytes cap
    assert not dest.exists()
    assert not list(tmp_path.rglob("*.part"))


def test_disk_floor_refuses_when_download_breaches_floor(tmp_path):
    guard = DiskGuard(floor_bytes=DISK_FLOOR)
    free = guard.free_bytes(tmp_path)
    too_big = free - DISK_FLOOR + 1024  # would leave floor - 1KiB
    with pytest.raises(DiskFloorError):
        guard.assert_download_fits(tmp_path, too_big)


def test_disk_floor_allows_fit(tmp_path):
    guard = DiskGuard(floor_bytes=DISK_FLOOR)
    free = guard.free_bytes(tmp_path)
    small = 1024
    if free - small < DISK_FLOOR:  # pragma: no cover - only on absurdly full disk
        pytest.skip("disk below floor already")
    report = guard.assert_download_fits(tmp_path, small)
    assert report["verdict"] == "FITS"


def test_disk_floor_unknown_size_fail_closed(tmp_path):
    guard = DiskGuard(floor_bytes=DISK_FLOOR)
    free = guard.free_bytes(tmp_path)
    if free > DISK_FLOOR + 50 * 1024 * 1024:
        # plenty of room: unknown-size path allows, but records UNKNOWN_SIZE
        report = guard.assert_download_fits(tmp_path, None)
        assert report["verdict"] == "UNKNOWN_SIZE_ALLOWED"
    else:
        with pytest.raises(DiskFloorError):
            guard.assert_download_fits(tmp_path, None)


def test_max_bytes_cap_enforced_in_memory(tmp_path):
    session = FakeSession([FakeResponse(200, body=b"x" * 100)])
    result = retrieve(
        "GET", "https://x/y", session=session, max_bytes=10, retry=RetryPolicy(1)
    )
    assert result.error and "max_bytes" in result.error


def test_two_pull_equality_identical():
    session = FakeSession([FakeResponse(200, body=b"same"), FakeResponse(200, body=b"same")])
    report = two_pull_equality(
        "https://x/f", session=session, limiter=RateLimiter(0.001)
    )
    assert report["verdict"] == "IDENTICAL"


def test_two_pull_equality_detects_mutation():
    session = FakeSession([FakeResponse(200, body=b"one"), FakeResponse(200, body=b"two")])
    report = two_pull_equality(
        "https://x/f", session=session, limiter=RateLimiter(0.001)
    )
    assert report["verdict"] == "MUTATED"
