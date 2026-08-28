"""Tests for the PIT daily-close panel builder (Sprint V4, owner A2).

Fixtures are production-shaped (Sprint V10R lesson d): a 15-minute bar
cadence, ``ts_event`` is the bar CLOSE stamp at millisecond precision
(``...:59.999Z``), and every day a window serves carries its terminal bar
(slot 95, closing ``23:59:59.999``), so no boundary's newest bar is more than
one interval old. Align the fixture, never the assertion.
"""

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
    iso_utc,
    load_bars_15m,
)

DAY_NS = 86_400_000_000_000
BAR_NS = 900_000_000_000
# 2025-08-18T00:00:00Z — a UTC midnight, epoch-aligned.
T0 = 1_755_475_200_000_000_000
_SCALE = 10 ** 16
# Exchange stamps a bar's CLOSE at millisecond precision (``...:59.999Z``).
_BAR_LAG_NS = 1_000_000
# ``ts_event`` of a day's LAST 15m bar (slot 95): one millisecond before the
# next UTC midnight, i.e. 23:59:59.999.
_TERMINAL_OFFSET_NS = BAR_NS * 96 - _BAR_LAG_NS


def write_funding_bundle(root: Path, symbol: str,
                         rows: list[tuple[int, str]]) -> None:
    d = root / symbol
    d.mkdir(parents=True, exist_ok=True)
    import json

    payload = {
        "requested_start_ms": 0,
        "requested_end_ms": 4_000_000_000_000,
        "rows": [{"fundingTime": ms, "fundingRate": rate} for ms, rate in rows],
    }
    (d / "funding.json").write_text(json.dumps(payload))


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


def _day_grid(day: int, terminal_close: float, first_slot: int = 0,
              last_slot: int = 95) -> tuple[list[int], list[float]]:
    """One day's production-shaped slot run: contiguous 15m slots
    ``first_slot..last_slot`` (0-based), ``ts_event`` = interval end - 1ms, so
    slot 95 closes ``23:59:59.999`` and carries ``terminal_close``."""
    midnight = T0 + day * DAY_NS
    stamps = [midnight + (s + 1) * BAR_NS - _BAR_LAG_NS
              for s in range(first_slot, last_slot + 1)]
    for ts in stamps:  # fixture must obey the production cadence invariant
        assert (ts + _BAR_LAG_NS - midnight) % BAR_NS == 0
    if last_slot == 95:
        assert stamps[-1] == midnight + _TERMINAL_OFFSET_NS
    closes = [_filler_close(day, s) for s in range(first_slot, last_slot)]
    return stamps, closes + [terminal_close]


def _full_days(day_indices: list[int],
               terminal_closes: list[float]) -> tuple[list[int], list[float]]:
    """Full 96-bar grid for each day; slot 95 carries ``terminal_closes[k]``."""
    stamps: list[int] = []
    closes: list[float] = []
    for d, tc in zip(day_indices, terminal_closes):
        day_stamps, day_closes = _day_grid(d, tc)
        stamps.extend(day_stamps)
        closes.extend(day_closes)
    return stamps, closes


def _filler_close(day: int, slot: int) -> float:
    """Deterministic interior-slot close. Never a multiple of 0.5 (fraction is
    always ``(2k + 1) / 32``), so it can never equal a pinned terminal close."""
    return 40.0 + 0.0625 * (day * 96 + slot) + 0.03125


def test_daily_close_is_last_bar_at_or_before_boundary(tmp_path: Path):
    # Full 96-bar production grid on days 0..2: the emitted close must be the
    # day's LAST bar (terminal slot 95), not merely some bar at-or-before.
    terminal_closes = [101.5, 102.5, 103.5]
    stamps, closes = _full_days([0, 1, 2], terminal_closes)
    _write_symbol(tmp_path, "ETHUSDT", stamps, closes)
    panel = build_daily_closes(str(tmp_path), ["ETHUSDT"], "2025-08-18", "2025-08-21")
    series = panel["ETHUSDT"]
    assert len(series) == 3
    for k, (ts, px) in enumerate(series):
        assert ts == T0 + k * DAY_NS + _TERMINAL_OFFSET_NS  # literal ts_event of the day's last bar
        assert px == pytest.approx(terminal_closes[k])
    # Boundary selection is by ts_event <= midnight: the emitted stamp is the
    # last bar BEFORE each midnight, never at/after it.
    assert all(ts < T0 + (k + 1) * DAY_NS for k, (ts, _) in enumerate(series))


def test_pit_guarantee_later_bar_never_changes_earlier_day(tmp_path: Path):
    base_days = [0, 1, 2]
    base_closes = [100.0, 101.0, 102.0]
    stamps, closes = _full_days(base_days, base_closes)
    _write_symbol(tmp_path, "ETHUSDT", stamps, closes)
    before = build_daily_closes(str(tmp_path), ["ETHUSDT"], "2025-08-18", "2025-08-21")

    # Backfill an EARLIER bar (mid-day-1 slot 40) in a new part file, and
    # append day 3's terminal bar: neither may alter a previously emitted
    # daily close.
    backfill = T0 + DAY_NS + BAR_NS * 40 - _BAR_LAG_NS  # mid-day-1 slot 40
    day3_terminal = T0 + 3 * DAY_NS + _TERMINAL_OFFSET_NS
    _write_symbol(
        tmp_path,
        "ETHUSDT",
        [backfill, day3_terminal],
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
        (day3_terminal, pytest.approx(999.0))
    ]


def test_boundary_with_no_bar_by_cutoff_is_absent(tmp_path: Path):
    # Bars start mid-day-1 (slot 40); boundaries at/before them emit nothing.
    # Day 1 still carries its terminal bar, so its own boundary is servable --
    # warmup absence must not trip the staleness raise.
    stamps, closes = _day_grid(1, 50.0, first_slot=40)
    day2_stamps, day2_closes = _day_grid(2, 51.0)
    stamps += day2_stamps
    closes += day2_closes
    _write_symbol(tmp_path, "ETHUSDT", stamps, closes)
    panel = build_daily_closes(str(tmp_path), ["ETHUSDT"], "2025-08-18", "2025-08-21")
    series = panel["ETHUSDT"]
    assert [ts for ts, _ in series] == [
        T0 + d * DAY_NS + _TERMINAL_OFFSET_NS for d in (1, 2)
    ]
    assert [px for _, px in series] == pytest.approx([50.0, 51.0])


def test_eth_trimmed_start_and_coverage_report(tmp_path: Path):
    # BTC full history (days 0..2); ETH trimmed (starts day 1). Full grids.
    btc_stamps, btc_closes = _full_days([0, 1, 2], [50000.0] * 3)
    eth_stamps, eth_closes = _full_days([1, 2], [3000.0, 3100.0])
    _write_symbol(tmp_path, "BTCUSDT", btc_stamps, btc_closes)
    _write_symbol(tmp_path, "ETHUSDT", eth_stamps, eth_closes)
    symbols = ["BTCUSDT", "ETHUSDT"]
    panel = build_daily_closes(str(tmp_path), symbols, "2025-08-18", "2025-08-21")
    report = coverage_report(panel, "2025-08-18", "2025-08-21")
    assert set(report) == {
        "bar_coverage", "benchmark_coverage",
        "funding_coverage", "metadata_coverage",
        "freshness",  # V10R D1 measurable freshness evidence
    }
    assert report["bar_coverage"] == {"BTCUSDT": 3, "ETHUSDT": 2}
    assert report["benchmark_coverage"] == {"BTCUSDT": 3}
    assert report["funding_coverage"] == {}  # bundles dir not supplied
    assert report["metadata_coverage"] == {"BTCUSDT": False, "ETHUSDT": False}
    # Both tails end on their terminal bar: measurably fresh.
    last_terminal = iso_utc(T0 + 3 * DAY_NS - _BAR_LAG_NS)
    assert report["freshness"] == {
        "BTCUSDT": {
            "last_close_bar_ts": last_terminal, "staleness_bars": 0, "fresh": True,
        },
        "ETHUSDT": {
            "last_close_bar_ts": last_terminal, "staleness_bars": 0, "fresh": True,
        },
    }
    # Empty symbol reports zero days rather than disappearing.
    report2 = coverage_report({"ADAUSDT": []}, "2025-08-18", "2025-08-20")
    assert report2["bar_coverage"] == {"ADAUSDT": 0}


def test_coverage_blocks_distinct_reason_code_inputs(tmp_path: Path):
    """F06 prep: benchmark vs funding vs bar vs metadata are separate blocks
    so XG0 can emit distinct reason codes."""
    # Days 0..2 fully covered: boundaries 08-19/08-20/08-21 each resolve to
    # their own terminal bar -> days_present counts 3 served boundaries.
    stamps, closes = _full_days([0, 1, 2], [50000.0] * 3)
    _write_symbol(tmp_path, "BTCUSDT", stamps, closes)
    panel = build_daily_closes(str(tmp_path), ["BTCUSDT"], "2025-08-18", "2025-08-21")

    bundle_root = tmp_path / "funding"
    write_funding_bundle(
        bundle_root, "BTCUSDT",
        [(T0 // 1_000_000, "0.0001"), ((T0 + DAY_NS) // 1_000_000, "0.0002")],
    )
    report = coverage_report(
        panel, "2025-08-18", "2025-08-21",
        funding_bundles_dir=str(bundle_root),
        metadata_symbols=["BTCUSDT"],
    )
    # BTC's bar coverage is measured on its own days, benchmark context
    # mirrors it, funding and metadata stay separate blocks
    assert report["bar_coverage"] == {"BTCUSDT": 3}
    # benchmark context mirrors the same bar coverage
    assert report["benchmark_coverage"] == {BENCHMARK_SYMBOL: 3}
    # funding settlements tracked separately (2 settlements, span)
    fc = report["funding_coverage"]["BTCUSDT"]
    assert fc["settlements"] == 2
    assert fc["first"] == "2025-08-18"
    assert fc["last"] == "2025-08-19"
    assert report["metadata_coverage"] == {"BTCUSDT": True}

    # missing bundle file -> zero settlements, nulls (fail-closed evidence)
    empty_root = tmp_path / "no_bundles"
    empty_root.mkdir()
    report2 = coverage_report(
        {"ETHUSDT": []}, "2025-08-18", "2025-08-20",
        benchmark_symbol=None,
        funding_bundles_dir=str(empty_root),
    )
    assert report2["benchmark_coverage"] == {}
    assert report2["funding_coverage"]["ETHUSDT"] == {
        "settlements": 0, "first": None, "last": None,
    }


def test_build_btc_benchmark_shape(tmp_path: Path):
    stamps, closes = _full_days([0, 1], [50000.0, 51000.0])
    _write_symbol(tmp_path, "BTCUSDT", stamps, closes)
    bench = build_btc_benchmark(str(tmp_path), "2025-08-18", "2025-08-20")
    assert set(bench) == {BENCHMARK_SYMBOL}
    assert len(bench[BENCHMARK_SYMBOL]) == 2
    # Days 0 and 1 close on their terminal bars (the window-start boundary is
    # warmup: day 0's first bar is after the 08-18 midnight).
    assert [ts for ts, _ in bench[BENCHMARK_SYMBOL]] == [
        T0 + d * DAY_NS + _TERMINAL_OFFSET_NS for d in (0, 1)
    ]


def test_load_bars_15m_decodes_prices(tmp_path: Path):
    offset = BAR_NS * 95 - 1
    _write_symbol(tmp_path, "ETHUSDT", _grid_stamps([0], offset), [123.25])
    bars = load_bars_15m(str(tmp_path), ["ETHUSDT"], "2025-08-18", "2025-08-19")
    ts, o, h, low, c, v = bars["ETHUSDT"][0]
    assert ts == T0 + offset
    assert (o, h, low, c, v) == pytest.approx((122.75, 124.25, 122.25, 123.25, 10.0))


def test_panel_determinism_across_part_layouts(tmp_path: Path):
    stamps, closes = _full_days([0, 1, 2, 3], [10.0, 11.0, 12.0, 13.0])
    expected_stamps = [T0 + d * DAY_NS + _TERMINAL_OFFSET_NS for d in (0, 1, 2)]
    expected_closes = [10.0, 11.0, 12.0]  # day 3 lies beyond the window end

    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    _write_symbol(root_a, "ETHUSDT", stamps, closes, parts=1)
    _write_symbol(root_b, "ETHUSDT", stamps, closes, parts=4)
    panel_a = build_daily_closes(str(root_a), ["ETHUSDT"], "2025-08-18", "2025-08-21")
    panel_b = build_daily_closes(str(root_b), ["ETHUSDT"], "2025-08-18", "2025-08-21")
    assert panel_a == panel_b
    assert [ts for ts, _ in panel_a["ETHUSDT"]] == expected_stamps
    assert [px for _, px in panel_a["ETHUSDT"]] == pytest.approx(expected_closes)


def test_window_validation(tmp_path: Path):
    with pytest.raises(ValueError):
        build_daily_closes(str(tmp_path), ["X"], "2025-08-20", "2025-08-19")
