"""V10R D1: fail-closed data-coverage pins for the PIT daily-close panel.

Regression surface: Sprint V10P prelaunch gate ``G05_COVERAGE_SHORTFALL_HIGH``
(``research/audits/v10p/a7_prelaunch_v10p.json``). Staged ETHUSDT bars ended
``2026-08-20T02:29:59.999Z`` against a preregistered window ending
``2026-08-21T00:00:00Z`` -- 86 bars / 21.5h short -- and
``research.panel.build_daily_closes`` silently emitted a terminal "daily
close" sourced from that stale bar while ``coverage_report`` merely counted
it (raised nothing).

Pins (V10R Option A companion fix, tolerance = 1 bar interval):

* a boundary whose newest bar at-or-before it is older than
  ``boundary - BAR_INTERVAL_NS`` raises ``research.panel.DataUnavailable``;
  the rule applies to EVERY boundary, not only the terminal one;
* a boundary with NO bar at-or-before it still emits nothing (warmup
  semantics, unchanged) and never raises;
* ``coverage_report`` raises on a stale terminal close and reports measurable
  freshness evidence;
* ``build_btc_benchmark`` inherits all of it (same code path).

Fixtures obey production invariants -- 15-minute cadence, ``ts_event`` is the
bar CLOSE stamp at millisecond precision (``...:59.999Z``), reads are
point-in-time (``ts_event <= boundary``) -- and never weaken an assertion to
pass.
"""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from research.panel import (
    BAR_INTERVAL_NS,
    BENCHMARK_SYMBOL,
    DataUnavailable,
    build_btc_benchmark,
    build_daily_closes,
    coverage_report,
    load_bars_15m,
    parse_iso_ns,
)

DAY_NS = 86_400_000_000_000
BAR_NS = BAR_INTERVAL_NS  # 15-minute catalog cadence
#: Exchange stamps bar CLOSEs at millisecond precision (``...:59.999Z``), so
#: the bar closing interval ``k`` is stamped ``interval_end - 1ms``.
_BAR_LAG_NS = 1_000_000
_SCALE = 10 ** 16

#: T0 = 2026-08-19T00:00:00Z -- the V10P preregistered window start.
T0 = parse_iso_ns("2026-08-19T00:00:00Z")
WINDOW_START = "2026-08-19T00:00:00Z"
WINDOW_END = "2026-08-21T00:00:00Z"  # terminal boundary C*
STALE_BAR_ISO = "2026-08-20T02:29:59.999Z"  # last bar actually staged in V10P
STALE_BAR_NS = parse_iso_ns(STALE_BAR_ISO)
#: 15-minute slots since T0; slot k is the bar whose CLOSE is T0 + k*BAR_NS.
STALE_SLOT = (STALE_BAR_NS + _BAR_LAG_NS - T0) // BAR_NS  # == 106
FULL_TAIL_SLOT = 2 * 96  # slot 192 closes 2026-08-20T23:59:59.999Z
EXPECTED_STALENESS_BARS = 86


# --------------------------------------------------------------------------- #
# Fixtures (production-shaped nautilus bar catalog)
# --------------------------------------------------------------------------- #
def slot_close_ns(slot: int) -> int:
    """``ts_event`` of the bar closing slot ``slot`` (interval end - 1ms)."""
    return T0 + slot * BAR_NS - _BAR_LAG_NS


def grid(first_slot: int, last_slot: int) -> list[int]:
    """Contiguous 15-minute slot run ``first_slot..last_slot`` inclusive."""
    return list(range(first_slot, last_slot + 1))


_SCHEMA = pa.schema(
    [
        ("open", pa.binary(16)),
        ("high", pa.binary(16)),
        ("low", pa.binary(16)),
        ("close", pa.binary(16)),
        ("volume", pa.binary(16)),
        ("ts_event", pa.uint64()),
    ]
)


def _enc(value: float) -> bytes:
    return int(round(value * _SCALE)).to_bytes(16, "little", signed=True)


def write_bars(root: Path, symbol: str, slots: list[int]) -> list[int]:
    """Write one bar per slot (close price derived from the slot index).

    Returns the written ``ts_event`` stamps so tests can assert the fixture
    obeys production invariants.
    """
    bar_dir = root / "data" / "binance_bar" / f"{symbol}-15-MINUTE-LAST-EXTERNAL"
    bar_dir.mkdir(parents=True, exist_ok=True)
    stamps = [slot_close_ns(s) for s in slots]
    assert stamps == sorted(stamps)
    assert len(set(stamps)) == len(stamps)
    for ts in stamps:  # close stamp, 1ms before an epoch-aligned 15m edge
        assert (ts + _BAR_LAG_NS - T0) % BAR_NS == 0
    closes = [100.0 + s / 100.0 for s in slots]
    table = pa.table(
        {
            "open": [_enc(c - 0.5) for c in closes],
            "high": [_enc(c + 1.0) for c in closes],
            "low": [_enc(c - 1.0) for c in closes],
            "close": [_enc(c) for c in closes],
            "volume": [_enc(10.0)] * len(slots),
            "ts_event": stamps,
        },
        schema=_SCHEMA,
    )
    pq.write_table(table, bar_dir / "part-0.parquet")
    return stamps


def _prefix_daily_closes(
    bars: list[tuple[int, float, float, float, float, float]],
    boundaries: list[int],
) -> list[tuple[int, float]]:
    """Replicate the PRE-FIX (V10P) selection being regression-tested.

    Last bar at-or-before each boundary however old it is -- the behaviour
    that published the stale terminal close. Used only to build the panel
    that ``coverage_report`` must now reject.
    """
    out: list[tuple[int, float]] = []
    for cutoff in boundaries:
        prior = [b for b in bars if b[0] <= cutoff]
        if prior:
            out.append((prior[-1][0], prior[-1][4]))
    return out


BOUNDARIES = [T0, T0 + DAY_NS, T0 + 2 * DAY_NS]  # 08-19, 08-20, 08-21 midnights


# --------------------------------------------------------------------------- #
# Regression: the exact V10P defect
# --------------------------------------------------------------------------- #
def test_v10p_defect_build_daily_closes_raises(tmp_path: Path):
    """Bars end 2026-08-20T02:29:59.999Z, window ends 2026-08-21T00:00:00Z.

    ``build_daily_closes`` must raise ``DataUnavailable`` instead of emitting
    a terminal close for the 2026-08-21T00:00:00Z boundary, and the error
    must name the symbol, the boundary, the stale bar and the staleness.
    """
    stamps = write_bars(tmp_path, "ETHUSDT", grid(1, STALE_SLOT))
    assert stamps[-1] == STALE_BAR_NS  # fixture matches the audited V10P tail

    with pytest.raises(DataUnavailable) as excinfo:
        build_daily_closes(
            str(tmp_path), ["ETHUSDT"], WINDOW_START, WINDOW_END
        )
    msg = str(excinfo.value)
    assert "ETHUSDT" in msg
    assert "2026-08-21T00:00:00.000Z" in msg  # the unservable boundary
    assert STALE_BAR_ISO in msg  # the stale bar it would have re-labelled
    assert f"{EXPECTED_STALENESS_BARS} bar(s)" in msg
    assert f"{EXPECTED_STALENESS_BARS * 0.25:.2f}h" in msg

    # No close is emitted for the 2026-08-21T00:00:00Z boundary -- nor is any
    # close sourced from the stale bar. Same catalog, window stopped before
    # the defective boundary: only the interior day close comes back.
    truncated = build_daily_closes(
        str(tmp_path), ["ETHUSDT"], WINDOW_START, "2026-08-20T00:00:00Z"
    )
    emitted = truncated["ETHUSDT"]
    assert [ts for ts, _ in emitted] == [slot_close_ns(96)]
    assert all(ts != STALE_BAR_NS for ts, _ in emitted)


def test_v10p_defect_coverage_report_raises(tmp_path: Path):
    """``coverage_report`` must fail closed on the same stale terminal close."""
    write_bars(tmp_path, "ETHUSDT", grid(1, STALE_SLOT))
    bars = load_bars_15m(
        str(tmp_path), ["ETHUSDT"], WINDOW_START, WINDOW_END
    )["ETHUSDT"]
    assert bars[-1][0] == STALE_BAR_NS
    # Panel exactly as the pre-fix build_daily_closes emitted it.
    defective_panel = {"ETHUSDT": _prefix_daily_closes(bars, BOUNDARIES)}
    assert [ts for ts, _ in defective_panel["ETHUSDT"]] == [
        slot_close_ns(96),
        STALE_BAR_NS,  # <- the 2026-08-21T00:00:00Z "close", 86 bars stale
    ]

    with pytest.raises(DataUnavailable) as excinfo:
        coverage_report(defective_panel, WINDOW_START, WINDOW_END)
    msg = str(excinfo.value)
    assert "ETHUSDT" in msg
    assert f"window_end {WINDOW_END}" in msg
    assert STALE_BAR_ISO in msg
    assert f"{EXPECTED_STALENESS_BARS} bar(s)" in msg


# --------------------------------------------------------------------------- #
# Positive control: a fully covered tail is accepted
# --------------------------------------------------------------------------- #
def test_full_coverage_tail_emits_terminal_close(tmp_path: Path):
    """Terminal bar closing 2026-08-20T23:59:59.999Z -> terminal close, no raise."""
    stamps = write_bars(tmp_path, "ETHUSDT", grid(1, FULL_TAIL_SLOT))
    assert stamps == [slot_close_ns(s) for s in grid(1, FULL_TAIL_SLOT)]
    assert all(b - a == BAR_NS for a, b in zip(stamps, stamps[1:]))  # 15m cadence
    assert stamps[-1] == parse_iso_ns("2026-08-20T23:59:59.999Z")

    panel = build_daily_closes(
        str(tmp_path), ["ETHUSDT"], WINDOW_START, WINDOW_END
    )
    series = panel["ETHUSDT"]
    assert [ts for ts, _ in series] == [
        slot_close_ns(96),  # 2026-08-20T00:00:00Z boundary
        slot_close_ns(FULL_TAIL_SLOT),  # 2026-08-21T00:00:00Z boundary
    ]
    assert all(ts <= C for (ts, _), C in zip(series, BOUNDARIES[1:]))  # PIT

    report = coverage_report(panel, WINDOW_START, WINDOW_END)  # must not raise
    fresh = report["freshness"]["ETHUSDT"]
    assert fresh == {
        "last_close_bar_ts": "2026-08-20T23:59:59.999Z",
        "staleness_bars": 0,
        "fresh": True,
    }
    assert report["bar_coverage"] == {"ETHUSDT": 2}


# --------------------------------------------------------------------------- #
# Warmup semantics: no bar at-or-before a boundary emits nothing, never raises
# --------------------------------------------------------------------------- #
def test_warmup_boundary_with_no_earlier_bar_emits_nothing(tmp_path: Path):
    """Window-start boundary (and any boundary before the first bar) is absent."""
    write_bars(tmp_path, "ETHUSDT", grid(97, FULL_TAIL_SLOT))  # day 1 only
    panel = build_daily_closes(
        str(tmp_path), ["ETHUSDT"], WINDOW_START, WINDOW_END
    )
    series = panel["ETHUSDT"]  # boundaries 08-19 and 08-20 emit NOTHING
    assert [ts for ts, _ in series] == [slot_close_ns(FULL_TAIL_SLOT)]

    # Degenerate warmup: no bars at all -> empty series, still no raise.
    empty = build_daily_closes(
        str(tmp_path), ["ADAUSDT"], WINDOW_START, WINDOW_END
    )
    assert empty == {"ADAUSDT": []}


# --------------------------------------------------------------------------- #
# The staleness rule covers EVERY boundary, not just the terminal one
# --------------------------------------------------------------------------- #
def test_mid_window_gap_raises_on_that_interior_boundary(tmp_path: Path):
    """A hole immediately before an interior midnight is the same defect."""
    write_bars(tmp_path, "ETHUSDT", grid(1, 95) + grid(107, FULL_TAIL_SLOT))
    with pytest.raises(DataUnavailable) as excinfo:
        build_daily_closes(
            str(tmp_path), ["ETHUSDT"], WINDOW_START, WINDOW_END
        )
    msg = str(excinfo.value)
    assert "2026-08-20T00:00:00.000Z" in msg  # INTERIOR boundary, not the tail
    assert slot_close_ns(95) == parse_iso_ns("2026-08-19T23:44:59.999Z")
    assert "2026-08-19T23:44:59.999Z" in msg
    assert "1 bar(s) (0.25h) stale" in msg


def test_one_bar_short_of_full_coverage_is_already_stale(tmp_path: Path):
    """Tolerance is exactly one interval: the bar at C - 15m does not count."""
    write_bars(tmp_path, "ETHUSDT", grid(1, 191))  # tail ends 23:44:59.999
    assert slot_close_ns(191) == parse_iso_ns("2026-08-20T23:44:59.999Z")
    with pytest.raises(DataUnavailable) as excinfo:
        build_daily_closes(
            str(tmp_path), ["ETHUSDT"], WINDOW_START, WINDOW_END
        )
    assert "2026-08-21T00:00:00.000Z" in str(excinfo.value)
    assert "1 bar(s) (0.25h) stale" in str(excinfo.value)


# --------------------------------------------------------------------------- #
# build_btc_benchmark inherits the fail-closed rule (same code path)
# --------------------------------------------------------------------------- #
def test_build_btc_benchmark_inherits_fail_closed(tmp_path: Path):
    stale_root = tmp_path / "stale"
    full_root = tmp_path / "full"
    write_bars(stale_root, BENCHMARK_SYMBOL, grid(1, STALE_SLOT))
    with pytest.raises(DataUnavailable):
        build_btc_benchmark(str(stale_root), WINDOW_START, WINDOW_END)

    write_bars(full_root, BENCHMARK_SYMBOL, grid(1, FULL_TAIL_SLOT))
    bench = build_btc_benchmark(str(full_root), WINDOW_START, WINDOW_END)
    assert [ts for ts, _ in bench[BENCHMARK_SYMBOL]] == [
        slot_close_ns(96),
        slot_close_ns(FULL_TAIL_SLOT),
    ]


# --------------------------------------------------------------------------- #
# coverage_report freshness evidence + existing-key backward compatibility
# --------------------------------------------------------------------------- #
def test_coverage_report_freshness_block_and_legacy_keys(tmp_path: Path):
    write_bars(tmp_path, "ETHUSDT", grid(1, FULL_TAIL_SLOT))
    panel = build_daily_closes(
        str(tmp_path), ["ETHUSDT"], WINDOW_START, WINDOW_END
    )
    report = coverage_report(panel, WINDOW_START, WINDOW_END)
    assert set(report) == {
        "bar_coverage",
        "benchmark_coverage",
        "funding_coverage",
        "metadata_coverage",
        "freshness",
    }
    assert report["bar_coverage"] == {"ETHUSDT": 2}
    assert report["benchmark_coverage"] == {BENCHMARK_SYMBOL: 0}
    assert report["funding_coverage"] == {}
    assert report["metadata_coverage"] == {"ETHUSDT": False}

    # An EMPTY series stays exempt from the stale-tail raise and reports
    # measurable non-freshness instead of disappearing from the block.
    report2 = coverage_report({"ADAUSDT": []}, WINDOW_START, WINDOW_END)
    assert report2["bar_coverage"] == {"ADAUSDT": 0}
    assert report2["freshness"] == {
        "ADAUSDT": {"last_close_bar_ts": None, "staleness_bars": None, "fresh": False}
    }
