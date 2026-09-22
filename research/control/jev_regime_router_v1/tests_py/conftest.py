"""Shared synthetic fixtures for jrv1 tests. NO production outcome data."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

PKG = Path(__file__).resolve().parent.parent / "jrv1"
sys.path.insert(0, str(PKG.parent))

from jrv1.data import Bars, DAY, MIN15, HOUR  # noqa: E402
from jrv1.freezes import Freezes, default_cycle_dir  # noqa: E402


@pytest.fixture(scope="session")
def fz() -> Freezes:
    return Freezes(default_cycle_dir())


def make_bars(closes, highs=None, lows=None, opens=None, volumes=None, start_ts=1_700_000_000_000_000_000, step_ns=MIN15):
    """Build Bars from price lists (defaults: high=low=open=close)."""
    c = np.asarray(closes, dtype=np.float64)
    n = len(c)
    h = np.asarray(highs, dtype=np.float64) if highs is not None else c.copy()
    l = np.asarray(lows, dtype=np.float64) if lows is not None else c.copy()
    o = np.asarray(opens, dtype=np.float64) if opens is not None else c.copy()
    v = np.asarray(volumes, dtype=np.float64) if volumes is not None else np.ones(n)
    ts_close = start_ts + step_ns * np.arange(1, n + 1, dtype=np.int64)
    return Bars(
        ts_open=ts_close - step_ns,
        ts_close=ts_close,
        open=o,
        high=h,
        low=l,
        close=c,
        volume=v,
    )


def make_exec_grid(rows, start_ts=1_699_999_200_000_000_000):
    """rows: list of (minute_offset, o, h, l, c, v) minute offsets from start.

    start_ts must be a clean 15m boundary for hour alignment tests.
    """
    ts_open = np.array([start_ts + int(m) * 60 * 1_000_000_000 for m, *_ in rows], dtype=np.int64)
    ts_close = ts_open + MIN15
    arr = np.array([[r[1], r[2], r[3], r[4], r[5]] for r in rows], dtype=np.float64)
    return Bars(ts_open=ts_open, ts_close=ts_close, open=arr[:, 0], high=arr[:, 1], low=arr[:, 2], close=arr[:, 3], volume=arr[:, 4])
