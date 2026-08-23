"""Regression tests for the W1 silent-skip trap in incremental fetching.

All scenarios run on synthetic timestamps with a fake catalog and a mocked
downloader - no network access.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field

import pandas as pd
import pytest

from config.settings import DataDownloadSettings, MarketSettings
from data.incremental import (
    DEFAULT_WRITE_BUFFER_MINUTES,
    IncrementalPipelineError,
    expected_latest_closed_bar,
    fetch_tail,
)

BASE = pd.Timestamp("2026-08-01T00:00:00Z")
STEP_NS = 15 * 60 * 1_000_000_000
CLOSE_OFFSET_NS = 999_999  # close stamp sits ~1ms before the next open (Binance convention)


def _close_ns(bar_index: int) -> int:
    """ns timestamp of the close stamp of bar #bar_index (0-based)."""
    return int(BASE.value) + (bar_index + 1) * STEP_NS - CLOSE_OFFSET_NS


@dataclass
class FakeBar:
    ts_event: int


@dataclass
class FakeCatalog:
    bars_by_type: dict[str, list[FakeBar]] = field(default_factory=dict)

    def bars(self, bar_type: str):
        return list(self.bars_by_type.get(bar_type, []))

    def append(self, bar_type: str, count: int, start_index: int) -> None:
        existing = self.bars_by_type.setdefault(bar_type, [])
        offset = len(existing)
        for i in range(count):
            existing.append(FakeBar(ts_event=_close_ns(start_index + offset + i)))


@pytest.fixture()
def market() -> MarketSettings:
    return MarketSettings(symbols=("SOLUSDT",))


@pytest.fixture()
def data_settings() -> DataDownloadSettings:
    return DataDownloadSettings(catalog_path="./catalog_test")


NOW = pd.Timestamp("2026-08-20T10:07:30Z")


def test_expected_latest_closed_bar_honours_write_buffer():
    # 10:07:30 - 9 min buffer = 09:58:30 -> floored onto the 15m grid = 09:45.
    expected = expected_latest_closed_bar("15m", now=NOW)
    assert expected == pd.Timestamp("2026-08-20T09:45:00Z")
    assert expected.tz is not None

    shorter = expected_latest_closed_bar(
        "15m", now=NOW, write_buffer_minutes=2.0
    )
    # 10:07:30 - 2 min = 10:05:30 -> floored onto the 15m grid = 10:00.
    assert shorter == pd.Timestamp("2026-08-20T10:00:00Z")

    naive_now = expected_latest_closed_bar("15m", now="2026-08-20 10:07:30")
    assert naive_now == expected


def test_catalog_current_requires_no_download(market, data_settings):
    catalog = FakeCatalog()
    # Newest written bar closes at 09:44:59.1 on 2026-08-20 == expectation at
    # NOW (09:45 grid point minus the 1ms adapter offset).
    catalog.append(
        "SOLUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL", 10, start_index=1853
    )

    def boom(*_args, **_kwargs):  # pragma: no cover - must not be called
        raise AssertionError("download must not run when catalog is current")

    result = fetch_tail(
        catalog,
        market,
        data_settings,
        "SOLUSDT",
        download_fn=boom,
        now=NOW,
    )
    assert result["status"] == "CATALOG_CURRENT"
    assert result["bars_fetched"] == 0
    assert result["bars_written"] == 0
    assert result["first_ts"] == pd.Timestamp(_close_ns(1853), unit="ns", tz="UTC").isoformat()
    assert result["last_ts"] == pd.Timestamp(_close_ns(1862), unit="ns", tz="UTC").isoformat()


def test_stale_catalog_with_zero_written_bars_raises(market, data_settings):
    """The W1 trap: exchange has newer closed bars, downloader writes nothing.

    The old weekly-forward script printed 'already up to date'; this must raise
    with the contract reason code instead.
    """
    catalog = FakeCatalog()
    catalog.append("SOLUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL", 10, start_index=0)

    calls = []

    def silent_skip(market_s, data_s):
        calls.append((market_s.symbols, data_s.start, data_s.end))
        return {"symbols": ["SOLUSDT"], "per_symbol": {"SOLUSDT": {"bars_written": 0}}}

    with pytest.raises(IncrementalPipelineError) as excinfo:
        fetch_tail(
            catalog,
            market,
            data_settings,
            "SOLUSDT",
            download_fn=silent_skip,
            now=NOW,
        )
    assert excinfo.value.reason_code == "catalog_not_current"
    # Tail request must target only the disjoint tail for the single symbol.
    assert calls[0][0] == ("SOLUSDT",)
    assert calls[0][2] is None
    requested_start = pd.Timestamp(calls[0][1])
    last_close = pd.Timestamp(_close_ns(9), unit="ns", tz="UTC")
    assert requested_start > last_close


def test_overlapping_request_must_not_silently_pass(market, data_settings):
    """A non-disjoint rejection contradicts our staleness check: raise."""
    catalog = FakeCatalog()
    catalog.append("SOLUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL", 10, start_index=0)

    def overlap(_market_s, _data_s):
        raise RuntimeError("invalid request: intervals non-disjoint with catalog")

    with pytest.raises(IncrementalPipelineError) as excinfo:
        fetch_tail(
            catalog,
            market,
            data_settings,
            "SOLUSDT",
            download_fn=overlap,
            now=NOW,
        )
    assert excinfo.value.reason_code == "catalog_not_current"


def test_successful_tail_fetch_reports_written_bars(market, data_settings):
    catalog = FakeCatalog()
    catalog.append("SOLUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL", 10, start_index=0)
    bar_type = "SOLUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"

    def real_fetch(_market_s, data_s):
        start = pd.Timestamp(data_s.start)
        first_new_index = int((start.value - BASE.value) // STEP_NS) - 1
        tail = [FakeBar(ts_event=_close_ns(first_new_index + i)) for i in range(5)]
        catalog.bars_by_type[bar_type].extend(tail)
        return {
            "symbols": ["SOLUSDT"],
            "per_symbol": {"SOLUSDT": {"bars_written": 5}},
        }

    result = fetch_tail(
        catalog,
        market,
        data_settings,
        "SOLUSDT",
        download_fn=real_fetch,
        now=NOW,
    )
    assert result["status"] == "FETCHED"
    assert result["bars_fetched"] == 5
    assert result["bars_written"] == 5
    assert result["last_ts"] == pd.Timestamp(_close_ns(14), unit="ns", tz="UTC").isoformat()


def test_seam_gap_is_detected_as_skipped_bar(market, data_settings):
    """If a fetch leaves a hole at the seam (e.g. one bar skipped), raise."""
    catalog = FakeCatalog()
    catalog.append("SOLUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL", 10, start_index=0)
    bar_type = "SOLUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"

    def skipping_fetch(_market_s, _data_s):
        # Skip one interval at the seam: write bars starting two steps ahead.
        tail = [FakeBar(ts_event=_close_ns(11 + i)) for i in range(4)]
        catalog.bars_by_type[bar_type].extend(tail)
        return {"per_symbol": {"SOLUSDT": {"bars_written": 4}}}

    with pytest.raises(IncrementalPipelineError) as excinfo:
        fetch_tail(
            catalog,
            market,
            data_settings,
            "SOLUSDT",
            download_fn=skipping_fetch,
            now=NOW,
        )
    assert excinfo.value.reason_code == "catalog_not_current"
    assert "seam" in excinfo.value.message.lower()


def test_empty_catalog_raises_for_full_download_first(market, data_settings):
    catalog = FakeCatalog()

    with pytest.raises(IncrementalPipelineError) as excinfo:
        fetch_tail(
            catalog,
            market,
            data_settings,
            "SOLUSDT",
            download_fn=lambda *_: {"per_symbol": {}},
            now=NOW,
        )
    assert excinfo.value.reason_code == "catalog_not_current"


def test_default_write_buffer_constant():
    # Documented ~9 minute lag; keep it frozen so expectations stay comparable.
    assert DEFAULT_WRITE_BUFFER_MINUTES == 9.0


def test_error_carries_contract_reason_code_only():
    err = IncrementalPipelineError("catalog_not_current", "x")
    assert isinstance(err, RuntimeError)
    with pytest.raises(ValueError):
        IncrementalPipelineError("made_up_code", "x")
