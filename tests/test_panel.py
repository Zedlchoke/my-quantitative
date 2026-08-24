"""Tests for the PIT daily-close panel builder (Sprint V4, owner A2)."""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from research.panel import (
    BENCHMARK_SYMBOL,
    build_btc_benchmark,
    build_daily_closes,
    coverage_report,
    load_bars_15m,
)

DAY_NS = 86_400_000_000_000
BAR_NS = 900_000_000_000
# 2025-08-18T00:00:00Z — a UTC midnight, epoch-aligned.
T0 = 1_755_475_200_000_000_000
_SCALE = 10 ** 16


def _enc(value: float) -> bytes:
    return int(round(value * _SCALE)).to_bytes(16, "little", signed=True)


def _bar_rows(stamps: list[int], closes: list[float]) -> dict[str, list]:
    n = len(stamps)
    return {
        "open": [_enc(c - 0.5) for c in closes],
        "high": [_enc(c + 1.0) for c in closes],
        "low": [_enc(c - 1.0) for c in closes],
        "close": [_enc(c) for c in closes],
        "volume": [_enc(10.0)] * n,
        "quote_volume": ["1000.0"] * n,
        "count": [1] * n,
        "taker_buy_base_volume": ["5.0"] * n,
        "taker_buy_quote_volume": ["500.0"] * n,
        "ts_event": stamps,
        "ts_init": stamps,
    }


def _write_symbol(root: Path, symbol: str, stamps, closes, parts: int = 1) -> None:
    bar_dir = root / "data" / "binance_bar" / f"{symbol}-15-MINUTE-LAST-EXTERNAL"
    bar_dir.mkdir(parents=True, exist_ok=True)
    schema = pa.schema(
        [
            ("open", pa.binary(16)),
            ("high", pa.binary(16)),
            ("low", pa.binary(16)),
            ("close", pa.binary(16)),
            ("volume", pa.binary(16)),
            ("quote_volume", pa.string()),
            ("count", pa.uint64()),
            ("taker_buy_base_volume", pa.string()),
            ("taker_buy_quote_volume", pa.string()),
            ("ts_event", pa.uint64()),
            ("ts_init", pa.uint64()),
        ]
    )
    chunk = max(1, len(stamps) // parts)
    start_part = len(list(bar_dir.glob("part-*.parquet")))
    for p in range(parts):
        lo, hi = p * chunk, (len(stamps) if p == parts - 1 else (p + 1) * chunk)
        table = pa.table(_bar_rows(stamps[lo:hi], closes[lo:hi]), schema=schema)
        pq.write_table(table, bar_dir / f"part-{start_part + p}.parquet")


def _grid_stamps(day_indices: list[int], slot_offset_ns: int) -> list[int]:
    """Stamps of one intra-day bar slot (offset from midnight) per day."""
    return [T0 + d * DAY_NS + slot_offset_ns for d in day_indices]


def test_daily_close_is_last_bar_at_or_before_boundary(tmp_path: Path):
    # One bar late on each of days 0..2 (23:45 slot close stamp).
    offset = BAR_NS * 95 - 1  # 23:44:59.999999999-style closing stamp
    stamps = _grid_stamps([0, 1, 2], offset)
    closes = [101.5, 102.5, 103.5]
    _write_symbol(tmp_path, "ETHUSDT", stamps, closes)
    panel = build_daily_closes(str(tmp_path), ["ETHUSDT"], "2025-08-18", "2025-08-21")
    series = panel["ETHUSDT"]
    assert len(series) == 3
    for k, (ts, px) in enumerate(series):
        assert ts == T0 + k * DAY_NS + offset  # literal ts_event of the bar
        assert px == pytest.approx(closes[k])
    # Boundary selection is by ts_event <= midnight: the emitted stamp is the
    # last bar BEFORE each midnight, never at/after it.
    assert all(ts < T0 + (k + 1) * DAY_NS for k, (ts, _) in enumerate(series))


def test_pit_guarantee_later_bar_never_changes_earlier_day(tmp_path: Path):
    offset = BAR_NS * 95 - 1
    base_days = [0, 1, 2]
    base_closes = [100.0, 101.0, 102.0]
    _write_symbol(tmp_path, "ETHUSDT", _grid_stamps(base_days, offset), base_closes)
    before = build_daily_closes(str(tmp_path), ["ETHUSDT"], "2025-08-18", "2025-08-21")

    # Backfill an EARLIER bar (mid-day 1) in a new part file, and append a
    # day-3 bar: neither may alter any previously emitted daily close.
    _write_symbol(
        tmp_path,
        "ETHUSDT",
        [T0 + DAY_NS + BAR_NS * 40 - 1, T0 + 3 * DAY_NS + BAR_NS * 40 - 1],
        [42.0, 999.0],
        parts=1,
    )
    after = build_daily_closes(str(tmp_path), ["ETHUSDT"], "2025-08-18", "2025-08-21")
    assert after["ETHUSDT"] == before["ETHUSDT"]
    # Widening the window only APPENDS the new final-day close.
    after_wide = build_daily_closes(
        str(tmp_path), ["ETHUSDT"], "2025-08-18", "2025-08-22"
    )
    assert after_wide["ETHUSDT"] == before["ETHUSDT"] + [
        (T0 + 3 * DAY_NS + BAR_NS * 40 - 1, pytest.approx(999.0))
    ]


def test_boundary_with_no_bar_by_cutoff_is_absent(tmp_path: Path):
    # Bars start mid-day-1; boundaries at/before them emit nothing.
    offset = BAR_NS * 50 - 1
    _write_symbol(tmp_path, "ETHUSDT", _grid_stamps([1, 2], offset), [50.0, 51.0])
    panel = build_daily_closes(str(tmp_path), ["ETHUSDT"], "2025-08-18", "2025-08-21")
    series = panel["ETHUSDT"]
    assert [ts for ts, _ in series] == [
        T0 + d * DAY_NS + offset for d in (1, 2)
    ]


def test_eth_trimmed_start_and_coverage_report(tmp_path: Path):
    offset = BAR_NS * 95 - 1
    # BTC full history; ETH trimmed (starts day 1).
    _write_symbol(tmp_path, "BTCUSDT", _grid_stamps([0, 1, 2], offset), [50000.0] * 3)
    _write_symbol(tmp_path, "ETHUSDT", _grid_stamps([1, 2], offset), [3000.0, 3100.0])
    symbols = ["BTCUSDT", "ETHUSDT"]
    panel = build_daily_closes(str(tmp_path), symbols, "2025-08-18", "2025-08-21")
    report = coverage_report(panel, "2025-08-18", "2025-08-21")
    assert report["BTCUSDT"]["days_present"] == 3
    assert report["BTCUSDT"]["first_day"] == "2025-08-18"
    assert report["BTCUSDT"]["last_day"] == "2025-08-20"
    assert report["ETHUSDT"]["days_present"] == 2
    assert report["ETHUSDT"]["first_day"] == "2025-08-19"
    assert report["ETHUSDT"]["last_day"] == "2025-08-20"
    # Empty symbol reports zeros/nulls rather than disappearing.
    report2 = coverage_report({"ADAUSDT": []}, "2025-08-18", "2025-08-20")
    assert report2["ADAUSDT"] == {"days_present": 0, "first_day": None, "last_day": None}


def test_build_btc_benchmark_shape(tmp_path: Path):
    offset = BAR_NS * 95 - 1
    _write_symbol(tmp_path, "BTCUSDT", _grid_stamps([0, 1], offset), [50000.0, 51000.0])
    bench = build_btc_benchmark(str(tmp_path), "2025-08-18", "2025-08-20")
    assert set(bench) == {BENCHMARK_SYMBOL}
    assert len(bench[BENCHMARK_SYMBOL]) == 2


def test_load_bars_15m_decodes_prices(tmp_path: Path):
    offset = BAR_NS * 95 - 1
    _write_symbol(tmp_path, "ETHUSDT", _grid_stamps([0], offset), [123.25])
    bars = load_bars_15m(str(tmp_path), ["ETHUSDT"], "2025-08-18", "2025-08-19")
    ts, o, h, low, c, v = bars["ETHUSDT"][0]
    assert ts == T0 + offset
    assert (o, h, low, c, v) == pytest.approx((122.75, 124.25, 122.25, 123.25, 10.0))


def test_panel_determinism_across_part_layouts(tmp_path: Path):
    offset = BAR_NS * 95 - 1
    stamps = _grid_stamps([0, 1, 2, 3], offset)
    closes = [10.0, 11.0, 12.0, 13.0]

    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    _write_symbol(root_a, "ETHUSDT", stamps, closes, parts=1)
    _write_symbol(root_b, "ETHUSDT", stamps, closes, parts=4)
    panel_a = build_daily_closes(str(root_a), ["ETHUSDT"], "2025-08-18", "2025-08-21")
    panel_b = build_daily_closes(str(root_b), ["ETHUSDT"], "2025-08-18", "2025-08-21")
    assert panel_a == panel_b


def test_window_validation(tmp_path: Path):
    with pytest.raises(ValueError):
        build_daily_closes(str(tmp_path), ["X"], "2025-08-20", "2025-08-19")
