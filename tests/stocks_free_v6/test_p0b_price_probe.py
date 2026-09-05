"""V6-P0b (A3) tests: parse fixture, hash-pinning round-trip, fail-loud.

All fixtures are SYNTHETIC; no test performs network I/O and no credential
is ever read or printed (CLAUDE.md discipline).
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

import pytest

from research.assets.stocks.p0b_fetch import (
    PoliteFetcher,
    RawFetchError,
    classify_content,
)
from research.assets.stocks.p0b_parse import (
    DailyBar,
    StooqParseError,
    daily_log_returns,
    parse_stooq_daily_csv,
    split_window_continuity,
)
from research.assets.stocks.p0b_pit_scan import PitStoreError, verify_pin

# --------------------------------------------------------------------------- #
# parse fixture
# --------------------------------------------------------------------------- #

FIXTURE_CSV = (
    "Date,Open,High,Low,Close,Volume\n"
    "2018-04-04,55.10,55.80,54.90,55.60,3200000\n"
    "2018-04-05,55.60,56.10,55.40,56.00,2950000\n"
    "2018-04-06,56.00,56.05,54.20,54.30,4100000\n"
)


def test_parse_fixture_enforces_convention():
    bars = parse_stooq_daily_csv(FIXTURE_CSV)
    assert [b.date for b in bars] == [date(2018, 4, 4), date(2018, 4, 5), date(2018, 4, 6)]
    assert bars[0] == DailyBar(date(2018, 4, 4), 55.10, 55.80, 54.90, 55.60, 3200000)
    rets = daily_log_returns(bars)
    assert len(rets) == 2
    import math

    assert rets[0][0] == date(2018, 4, 5)
    assert abs(rets[0][1] - math.log(56.00 / 55.60)) < 1e-12


@pytest.mark.parametrize(
    "bad_csv",
    [
        "",  # empty
        "<!DOCTYPE html><html>challenge</html>",  # html
        "This site requires JavaScript to verify your browser. /__verify",  # anti-bot
        "Close,Date\n2018-04-04,55\n",  # wrong header
        "Date,Open,High,Low,Close,Volume\n04/04/2018,55,56,54,55.6,1\n",  # bad date fmt
        "Date,Open,High,Low,Close,Volume\n2018-04-04,55,56,54,55.6,x\n",  # bad volume
        "Date,Open,High,Low,Close,Volume\n2018-04-04,55,50,54,55.6,1\n",  # high<low
        "Date,Open,High,Low,Close,Volume\n2018-04-05,55,56,54,55.6,1\n2018-04-04,55,56,54,55.6,1\n",  # unsorted
        "Date,Open,High,Low,Close,Volume\n2018-04-04,-1,56,54,55.6,1\n",  # non-positive
    ],
)
def test_parse_failures_are_loud(bad_csv):
    with pytest.raises(StooqParseError):
        parse_stooq_daily_csv(bad_csv)


# --------------------------------------------------------------------------- #
# adjustment detection
# --------------------------------------------------------------------------- #


def _series(around: date, pre_close: float, post_close: float, span: int = 5):
    rows = []
    for i in range(-span, span + 1):
        d = date.fromordinal(around.toordinal() + i)
        close = pre_close if i < 0 else post_close
        rows.append(f"{d.isoformat()},{close * 0.99:.2f},{close * 1.01:.2f},{close * 0.98:.2f},{close:.2f},1000")
    return "Date,Open,High,Low,Close,Volume\n" + "\n".join(rows) + "\n"


def test_split_window_detects_raw_discontinuity():
    split_day = date(2020, 8, 31)
    bars = parse_stooq_daily_csv(_series(split_day, 500.0, 125.0))  # 4:1 raw drop
    out = split_window_continuity(bars, date(2020, 8, 20), date(2020, 9, 10), 4.0)
    assert out["verdict"] == "RAW_LIKE_DISCONTINUITY"


def test_split_window_detects_adjusted_continuity():
    split_day = date(2020, 8, 31)
    bars = parse_stooq_daily_csv(_series(split_day, 125.0, 126.0))  # no drop
    out = split_window_continuity(bars, date(2020, 8, 20), date(2020, 9, 10), 4.0)
    assert out["verdict"] == "NO_RAW_DISCONTINUITY_ADJUSTED_LIKE"


def test_split_window_without_data_fails_closed():
    bars = parse_stooq_daily_csv(_series(date(2019, 1, 10), 100.0, 101.0, span=3))
    out = split_window_continuity(bars, date(2020, 8, 20), date(2020, 9, 10), 2.0)
    assert out["verdict"] == "NO_DATA_IN_WINDOW"


# --------------------------------------------------------------------------- #
# hash-pinning round-trip
# --------------------------------------------------------------------------- #


def test_sha256_file_round_trip(tmp_path):
    target = tmp_path / "store.jsonl"
    payload = b'{"k": "v"}\n' * 100
    target.write_bytes(payload)
    from research.assets.stocks.p0b_pit_scan import sha256_file

    observed = sha256_file(target)
    assert observed == hashlib.sha256(payload).hexdigest()
    # tamper -> pin mismatch
    target.write_bytes(payload + b"tamper\n")
    with pytest.raises(PitStoreError):
        verify_pin(target, observed)


def test_verify_pin_missing_file(tmp_path):
    with pytest.raises(PitStoreError):
        verify_pin(tmp_path / "absent.jsonl", "0" * 64)


# --------------------------------------------------------------------------- #
# fetch fail-loud semantics (no network: classify + fetcher error paths)
# --------------------------------------------------------------------------- #


def test_classify_content_sniffs_challenge_not_status():
    assert classify_content(b"<!DOCTYPE html><html>requires JavaScript to verify your browser") == "challenge"
    assert classify_content(b"Date,Open,High,Low,Close,Volume\n") == "csv"
    assert classify_content(b"") == "empty"
    assert classify_content(b"<!DOCTYPE html><html><body>x</body>") == "html_page"
    assert classify_content(b'{"a": 1}') == "json"


class _FakeResponse:
    def __init__(self, body: bytes, status: int = 200):
        self._body = body
        self.status = status

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_fetcher_fail_loud_on_challenge(tmp_path, monkeypatch):
    fetcher = PoliteFetcher(tmp_path, min_spacing_s=0.0)
    challenge = (
        b"<!DOCTYPE html><html>This site requires JavaScript to verify your "
        b"browser. /__verify nonce"
    )
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda req, timeout: _FakeResponse(challenge, 200)
    )
    with pytest.raises(RawFetchError) as exc:
        fetcher.fetch("https://stooq.com/q/d/l/?s=x.us&i=d", "x.csv", expect="csv")
    assert "challenge" in str(exc.value)
    # offending bytes are archived as evidence
    assert (tmp_path / "x.csv").read_bytes() == challenge
    assert fetcher.log[-1]["ok"] is False


def test_fetcher_fail_loud_on_empty_and_status(tmp_path, monkeypatch):
    fetcher = PoliteFetcher(tmp_path, min_spacing_s=0.0)
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda req, timeout: _FakeResponse(b"", 200)
    )
    with pytest.raises(RawFetchError):
        fetcher.fetch("https://example.com/empty", "empty.csv", expect="csv")

    class _ErrResponse:
        status = 404

        def read(self):
            return b""

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    monkeypatch.setattr(
        "urllib.request.urlopen", lambda req, timeout: _ErrResponse()
    )
    with pytest.raises(RawFetchError) as exc:
        fetcher.fetch("https://example.com/missing", "missing.csv", expect="csv")
    assert "non-200" in str(exc.value)


def test_fetcher_ok_path_pins_hash(tmp_path, monkeypatch):
    fetcher = PoliteFetcher(tmp_path, min_spacing_s=0.0)
    body = b"Date,Open,High,Low,Close,Volume\n2018-04-04,1,1,1,1,0\n"
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda req, timeout: _FakeResponse(body, 200)
    )
    rec = fetcher.fetch("https://stooq.com/q/d/l/?s=ok.us&i=d", "ok.csv", expect="csv")
    assert rec["ok"] is True
    assert rec["sha256"] == hashlib.sha256(body).hexdigest()
    manifest = fetcher.write_manifest()
    files = json.loads(manifest.read_text())["files"]
    assert files["ok.csv"] == rec["sha256"]
