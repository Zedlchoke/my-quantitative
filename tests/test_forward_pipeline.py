"""Regression tests for the W1 tail-overlap trap in the forward-test pipeline.

NOTES section 12: Binance write-intervals extend ~9min past the last bar
close; fetching an overlapping range makes the download engine silently skip
bars, so W1's ETH catalog stalled at 2026-08-21 while downloads "passed".

Guards under test (scripts/forward_lib.py):
1. fetch-start must be >= last-bar close + 16min (never overlap);
2. bars_written == 0 while now - last_bar > 1h must FAIL LOUD.
"""

from __future__ import annotations

import dataclasses
from types import SimpleNamespace

import pandas as pd
import pytest

from scripts.forward_lib import (
    FETCH_BUFFER_MINUTES,
    STALE_MAX_MINUTES,
    StaleForwardDataError,
    compute_fetch_start,
    evaluate_staleness,
    fetch_disjoint_tail,
    is_safe_fetch_start,
)

SYMBOL = "ETHUSDT"
BAR_TYPE = f"{SYMBOL}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
T = pd.Timestamp("2026-08-21T14:00:00+00:00")  # last catalog bar close


def _ns(ts: pd.Timestamp) -> int:
    return int(ts.value)


class _FakeBar(SimpleNamespace):
    """Just enough of a Nautilus bar for forward_lib (ts_event in ns)."""


class FakeCatalog:
    def __init__(self, bars: list[_FakeBar]):
        self._bars = bars

    def bars(self, bar_type: str) -> list[_FakeBar]:
        assert bar_type == BAR_TYPE
        return list(self._bars)


def _settings(catalog_path: str = "/tmp/fake-catalog"):
    from config.settings import DataDownloadSettings, MarketSettings

    market = MarketSettings(symbols=(SYMBOL,))
    data = DataDownloadSettings(catalog_path=catalog_path)
    return SimpleNamespace(market=market, data=data)


# --------------------------------------------------------------------------- #
# Trap 1: fetch window must clear the ~9min write-interval of the last bar
# --------------------------------------------------------------------------- #
def test_fetch_start_is_at_least_last_bar_plus_buffer():
    start = compute_fetch_start(T)
    assert start == T + pd.Timedelta(minutes=FETCH_BUFFER_MINUTES)
    assert start >= T + pd.Timedelta(minutes=16)


def test_fetch_start_clears_binance_write_interval():
    # The trap: intervals extend ~9min past close; anything <= T+9min overlaps
    # and gets silently skipped. The computed start must be strictly beyond it.
    start = compute_fetch_start(T)
    assert start > T + pd.Timedelta(minutes=9)


@pytest.mark.parametrize(
    ("start", "safe"),
    [
        (T + pd.Timedelta(minutes=5), False),   # W1 bug: overlapping request
        (T + pd.Timedelta(minutes=9), False),   # exactly at write-interval edge
        (T + pd.Timedelta(minutes=15), False),  # still inside buffer
        (T + pd.Timedelta(minutes=16), True),   # minimum safe start
        (T + pd.Timedelta(hours=1), True),
    ],
)
def test_is_safe_fetch_start(start, safe):
    assert is_safe_fetch_start(T, start) is safe


def test_naive_timestamp_is_treated_as_utc():
    naive = T.tz_localize(None)
    assert compute_fetch_start(naive) == compute_fetch_start(T)


# --------------------------------------------------------------------------- #
# Trap 2: 0 new bars while the market moved on must fail loud
# --------------------------------------------------------------------------- #
def test_zero_new_bars_after_one_hour_stale_raises():
    with pytest.raises(StaleForwardDataError) as excinfo:
        evaluate_staleness(
            SYMBOL, T, new_bars=0, now=T + pd.Timedelta(hours=2),
        )
    msg = str(excinfo.value)
    assert "0 new bars" in msg and SYMBOL in msg  # explicit, not silent


def test_zero_new_bars_within_grace_period_does_not_raise():
    evaluate_staleness(
        SYMBOL, T, new_bars=0, now=T + pd.Timedelta(minutes=STALE_MAX_MINUTES - 5),
    )


def test_new_bars_present_never_raises_even_when_very_stale():
    evaluate_staleness(
        SYMBOL, T, new_bars=3, now=T + pd.Timedelta(hours=48),
    )


def test_negative_or_missing_new_bars_counts_as_zero():
    with pytest.raises(StaleForwardDataError):
        evaluate_staleness(SYMBOL, T, new_bars=-1, now=T + pd.Timedelta(hours=2))


# --------------------------------------------------------------------------- #
# Integration: fetch_disjoint_tail wiring (no network)
# --------------------------------------------------------------------------- #
def test_disjoint_tail_requests_start_at_last_bar_plus_16min():
    """Reproduce the overlap trap end-to-end: the downloader MUST be asked to
    fetch from T+16min, never from an overlapping earlier timestamp."""
    captured = {}

    def fake_downloader(market, data):
        captured["start"] = pd.Timestamp(data.start)
        return {"per_symbol": {SYMBOL: {"bars_written": 100}}}  # catalog grew

    settings = _settings()
    report = fetch_disjoint_tail(
        settings,
        downloader=fake_downloader,
        catalog_factory=lambda _: FakeCatalog([_FakeBar(ts_event=_ns(T))]),
        now=T + pd.Timedelta(hours=3),
        log=lambda _: None,
    )

    assert captured["start"] == T + pd.Timedelta(minutes=16)
    assert is_safe_fetch_start(T, captured["start"])
    assert report[SYMBOL]["new_bars"] == 99  # 100 total minus 1 pre-existing


def test_disjoint_tail_fails_loud_when_downloader_writes_nothing(caplog):
    """The exact W1 failure mode: request 'succeeds' but 0 bars land and the
    exchange is >1h ahead -> StaleForwardDataError, never silent success."""
    stale_now = T + pd.Timedelta(hours=2)

    def fake_downloader(market, data):  # silently writes nothing
        return {"per_symbol": {SYMBOL: {"bars_written": 1}}}

    settings = _settings()
    with pytest.raises(StaleForwardDataError):
        fetch_disjoint_tail(
            settings,
            downloader=fake_downloader,
            catalog_factory=lambda _: FakeCatalog([_FakeBar(ts_event=_ns(T))]),
            now=stale_now,
            log=lambda _: None,
        )


def test_disjoint_tail_reports_current_when_catalog_up_to_date():
    calls = []

    def fake_downloader(market, data):  # pragma: no cover - must not run
        calls.append(data.start)

    report = fetch_disjoint_tail(
        _settings(),
        downloader=fake_downloader,
        catalog_factory=lambda _: FakeCatalog(
            [_FakeBar(ts_event=_ns(pd.Timestamp.now("UTC") - pd.Timedelta(minutes=2)))]
        ),
        log=lambda _: None,
    )
    assert calls == []  # no overlapping request was even attempted
    assert report[SYMBOL]["status"] == "current"


def test_disjoint_tail_skips_empty_catalog_without_raising():
    report = fetch_disjoint_tail(
        _settings(),
        downloader=lambda m, d: {},
        catalog_factory=lambda _: FakeCatalog([]),
        log=lambda _: None,
    )
    assert report[SYMBOL]["status"] == "empty"


def test_unexpected_download_errors_propagate():
    def boom(market, data):  # pragma: no cover - exercised via raise
        raise RuntimeError("network exploded")

    with pytest.raises(RuntimeError, match="network exploded"):
        fetch_disjoint_tail(
            _settings(),
            downloader=boom,
            catalog_factory=lambda _: FakeCatalog([_FakeBar(ts_event=_ns(T))]),
            now=T + pd.Timedelta(hours=3),
            log=lambda _: None,
        )
