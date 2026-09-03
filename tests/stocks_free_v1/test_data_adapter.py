"""Offline tests for the deterministic downloader (A2).

Transport is injected, so no test touches the network.
"""

import hashlib
import urllib.error
import urllib.request

import pytest

from research.stocks_free_v1.data_adapter import (
    DownloadResult,
    Downloader,
    compare_two_pulls,
    make_default_transport,
    sha256_bytes,
    write_checksum_manifest,
)


class FakeTransport:
    """Scriptable transport: returns queued (status, ctype, body) responses."""

    def __init__(self, responses, fail_first=0, error_first=0):
        self.responses = list(responses)
        self.calls = []
        self.fail_first = fail_first  # HTTP error statuses to emit first
        self.error_first = error_first  # transport exceptions to raise first

    def __call__(self, req):
        self.calls.append(req.full_url)
        if self.error_first > 0:
            self.error_first -= 1
            raise urllib.error.URLError("simulated connection reset")
        if self.fail_first > 0:
            self.fail_first -= 1
            return 503, "text/html", b"overloaded"
        if not self.responses:
            raise AssertionError("unexpected extra call")
        return self.responses.pop(0)


@pytest.fixture()
def clock_and_sleep():
    class Fake:
        def __init__(self):
            self.t = 0.0
            self.sleeps = []

        def clock(self):
            return self.t

        def sleep(self, s):
            self.sleeps.append(s)
            self.t += s

    return Fake()


def _dl(tmp_path, transport, clock_and_sleep, min_interval_s=0.0, **kw):
    return Downloader(
        base_dir=tmp_path / "staging",
        log_path=tmp_path / "logs" / "downloads.jsonl",
        transport=transport,
        sleep=clock_and_sleep.sleep,
        clock=clock_and_sleep.clock,
        utcnow=lambda: "2026-09-03T00:00:00Z",
        min_interval_s=min_interval_s,
        **kw,
    )


def test_fetch_writes_file_and_sha256(tmp_path, clock_and_sleep):
    body = b"Date,Close\n2026-01-02,100.0\n"
    transport = FakeTransport([(200, "text/csv", body)])
    dl = _dl(tmp_path, transport, clock_and_sleep)
    res = dl.fetch("https://example.com/data.csv", "raw/data.csv")
    assert res.status == 200
    assert res.attempts == 1
    assert res.sha256 == hashlib.sha256(body).hexdigest()
    assert res.size_bytes == len(body)
    written = (tmp_path / "staging" / "raw" / "data.csv").read_bytes()
    assert written == body
    assert dl.log_path.exists()
    assert '"event": "fetch"' in dl.log_path.read_text(encoding="utf-8")


def test_retry_on_503_then_success(tmp_path, clock_and_sleep):
    body = b"ok-payload"
    transport = FakeTransport([(200, "text/csv", body)], fail_first=2)
    dl = _dl(tmp_path, transport, clock_and_sleep, max_retries=3, backoff_base_s=0.0)
    res = dl.fetch("https://example.com/data.csv", "raw/data.csv")
    assert res.status == 200 and res.attempts == 3
    # two retries were backed off
    assert len(clock_and_sleep.sleeps) >= 2


def test_retries_exhausted_records_failure_without_write(tmp_path, clock_and_sleep):
    transport = FakeTransport([], fail_first=10)
    dl = _dl(tmp_path, transport, clock_and_sleep, max_retries=2, backoff_base_s=0.0)
    res = dl.fetch("https://example.com/data.csv", "raw/never.csv")
    assert res.status == 503
    assert res.sha256 == ""
    assert res.path == ""
    assert not (tmp_path / "staging" / "raw" / "never.csv").exists()
    assert any(e.get("event") == "retry" for e in dl.log_entries)


def test_transport_error_retries(tmp_path, clock_and_sleep):
    body = b"recovered"
    transport = FakeTransport([(200, "text/csv", body)], error_first=1)
    dl = _dl(tmp_path, transport, clock_and_sleep, max_retries=2, backoff_base_s=0.0)
    res = dl.fetch("https://example.com/data.csv", "raw/data.csv")
    assert res.status == 200 and res.attempts == 2


def test_rate_limit_per_host_is_polite(tmp_path, clock_and_sleep):
    transport = FakeTransport(
        [(200, "text/csv", b"a"), (200, "text/csv", b"b")]
    )
    dl = _dl(tmp_path, transport, clock_and_sleep, min_interval_s=2.0)
    dl.fetch("https://example.com/a.csv", "raw/a.csv")
    dl.fetch("https://example.com/b.csv", "raw/b.csv")
    # a wait of ~2.0s was inserted between the two same-host fetches
    assert any(1.0 < s <= 2.0 for s in clock_and_sleep.sleeps), clock_and_sleep.sleeps


def test_rel_path_cannot_escape_staging(tmp_path, clock_and_sleep):
    dl = _dl(tmp_path, FakeTransport([(200, "text/csv", b"x")]), clock_and_sleep)
    with pytest.raises(ValueError):
        dl.fetch("https://example.com/x.csv", "../escape.csv")


def test_non_200_is_not_written(tmp_path, clock_and_sleep):
    transport = FakeTransport([(404, "text/html", b"nope")])
    dl = _dl(tmp_path, transport, clock_and_sleep, max_retries=0)
    res = dl.fetch("https://example.com/missing.csv", "raw/missing.csv")
    assert res.status == 404
    assert res.sha256 == ""
    assert not (tmp_path / "staging" / "raw" / "missing.csv").exists()
    # but the response body is preserved as access evidence
    evidence = tmp_path / "staging" / "raw" / "missing.csv.status404.body"
    assert evidence.read_bytes() == b"nope"
    assert "status404" in res.note


def test_compare_two_pulls_equal_and_divergent():
    a = DownloadResult("u", 200, "p", "ab" * 32, 10, "2026-09-03T00:00:00Z", 0.1, 1, "text/csv")
    b = DownloadResult("u", 200, "p", "ab" * 32, 10, "2026-09-03T00:00:05Z", 0.1, 1, "text/csv")
    rec = compare_two_pulls(a, b, note="immediate pulls; >=1h impossible in-session")
    assert rec.byte_equal and rec.sha_equal
    c = DownloadResult("u", 200, "p", "cd" * 32, 11, "2026-09-03T01:00:00Z", 0.1, 1, "text/csv")
    rec2 = compare_two_pulls(a, c)
    assert not rec2.byte_equal and not rec2.sha_equal  # revision-delta evidence


def test_two_pull_immediate_uses_downloader(tmp_path, clock_and_sleep):
    transport = FakeTransport(
        [(200, "text/csv", b"same"), (200, "text/csv", b"same")]
    )
    dl = _dl(tmp_path, transport, clock_and_sleep, min_interval_s=0.0)
    rec = dl.two_pull_immediate("https://example.com/static.csv", "raw/{pull}-{stamp}.csv")
    assert rec.byte_equal
    assert transport.calls == ["https://example.com/static.csv"] * 2


def test_sha256_file_and_manifest(tmp_path):
    p = tmp_path / "f.bin"
    p.write_bytes(b"manifest-payload")
    out = tmp_path / "manifest.json"
    rows = write_checksum_manifest([p], out)
    assert rows[0]["sha256"] == sha256_bytes(b"manifest-payload")
    assert rows[0]["size_bytes"] == len(b"manifest-payload")
    assert out.exists()


def test_default_transport_factory_returns_callable():
    t = make_default_transport(timeout_s=1.0)
    assert callable(t)
