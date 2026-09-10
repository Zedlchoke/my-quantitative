"""Tests for portable RSS normalization (lane A4, finding F4).

Run:  /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest
tests/test_mdp_perf_portable.py -q   (from the lane worktree root)

Asserts the F4 conversions EXACTLY: darwin ru_maxrss is BYTES, linux
ru_maxrss is KiB (x1024), unknown units yield null bytes/MiB plus a visible
UNMEASURABLE note, and MiB = bytes / 1048576.  The heavy benchmark that
consumes these fields (perf_bench_v2.py) is deliberately NOT run here.
"""

from __future__ import annotations

import resource
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

from market_data_plane import perf_metrics  # noqa: E402

MIB = 1048576


def test_normalize_rss_darwin_bytes_exact():
    out = perf_metrics.normalize_rss("darwin", 1293058048)
    assert out["peak_rss_raw"] == 1293058048
    assert out["peak_rss_raw_unit"] == "bytes"
    assert out["peak_rss_bytes"] == 1293058048
    # 1293058048 / 1048576 = 1233.15625 exactly (dyadic)
    assert out["peak_rss_mib"] == 1293058048 / MIB
    assert out["peak_rss_mib"] == 1233.15625
    assert out["note"] == ""


def test_normalize_rss_linux_kib_exact():
    out = perf_metrics.normalize_rss("linux", 1234567)
    assert out["peak_rss_raw"] == 1234567
    assert out["peak_rss_raw_unit"] == "kib"
    assert out["peak_rss_bytes"] == 1234567 * 1024
    assert out["peak_rss_bytes"] == 1264196608
    # 1264196608 / 1048576 = 1205.6318359375 exactly (647/1024 is dyadic)
    assert out["peak_rss_mib"] == 1264196608 / MIB
    assert out["peak_rss_mib"] == 1205.6318359375
    assert out["note"] == ""


def test_normalize_rss_platform_token_variants():
    assert perf_metrics.normalize_rss("linux2", 8)["peak_rss_raw_unit"] == "kib"
    assert perf_metrics.normalize_rss("Darwin", 8)["peak_rss_raw_unit"] == "bytes"
    assert perf_metrics.normalize_rss("win32", 8)["peak_rss_raw_unit"] == "unknown"
    assert perf_metrics.normalize_rss("freebsd", 8)["peak_rss_raw_unit"] == "unknown"


def test_normalize_rss_unknown_unit_null_bytes_and_visible_note():
    out = perf_metrics.normalize_rss("win32", 999)
    assert out["peak_rss_raw"] == 999
    assert out["peak_rss_raw_unit"] == "unknown"
    assert out["peak_rss_bytes"] is None
    assert out["peak_rss_mib"] is None
    assert "UNMEASURABLE" in out["note"]
    assert "win32" in out["note"]
    # never a guess, never a silent zero
    assert out["peak_rss_bytes"] != 0
    assert out["peak_rss_mib"] != 0


def test_normalize_rss_input_validation():
    with pytest.raises(ValueError, match="plain int"):
        perf_metrics.normalize_rss("darwin", "1293058048")
    with pytest.raises(ValueError, match="plain int"):
        perf_metrics.normalize_rss("darwin", True)
    with pytest.raises(ValueError, match=">= 0"):
        perf_metrics.normalize_rss("darwin", -1)


def test_peak_rss_now_monkeypatched_darwin_and_linux(monkeypatch):
    fake = types.SimpleNamespace(ru_maxrss=1293058048)
    monkeypatch.setattr(resource, "getrusage",
                        lambda who: types.SimpleNamespace(ru_maxrss=fake.ru_maxrss))
    assert perf_metrics.peak_rss_now("darwin") == {
        "peak_rss_raw": 1293058048,
        "peak_rss_raw_unit": "bytes",
        "peak_rss_bytes": 1293058048,
        "peak_rss_mib": 1233.15625,
        "note": "",
    }
    monkeypatch.setattr(
        resource, "getrusage",
        lambda who: types.SimpleNamespace(ru_maxrss=1234567))
    out = perf_metrics.peak_rss_now("linux")
    assert out["peak_rss_raw_unit"] == "kib"
    assert out["peak_rss_bytes"] == 1264196608
    assert out["peak_rss_mib"] == 1205.6318359375


def test_peak_rss_now_unknown_platform_still_visible(monkeypatch):
    monkeypatch.setattr(resource, "getrusage",
                        lambda who: types.SimpleNamespace(ru_maxrss=42))
    out = perf_metrics.peak_rss_now("plan9")
    assert out["peak_rss_raw"] == 42
    assert out["peak_rss_bytes"] is None
    assert "UNMEASURABLE" in out["note"]
