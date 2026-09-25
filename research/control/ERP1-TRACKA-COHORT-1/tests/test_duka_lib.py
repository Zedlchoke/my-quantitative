"""Fixture tests: bi5 layouts + the 20-vs-24 byte trap (duka_lib port).

Ancestor lineage: the trap is documented in duka_lib — tick (20B) and
candle (24B) records share the LZMA container, so SOME payloads pass both
layout asserts; content cross-checks (probe_pair.py) are therefore
mandatory, and the layout asserts must fire whenever the record size
cannot divide the payload.
"""
import lzma
import struct

import pytest

import duka_lib as D

SCALE = 1e5


def _candle_payload(n, scale=SCALE):
    out = b""
    for i in range(n):
        # sec, o, c, l, h, vol ; keep o/h/l/c consistent so decode works
        o = 100000 + i
        out += struct.pack(">5if", i * 60, o, o + 5, o - 5, o + 10, 1.5)
    return out


def _tick_payload(n):
    out = b""
    for i in range(n):
        out += struct.pack(">5i", i * 1000, 100010, 100000, 1, 1)
    return out


def test_candle_roundtrip_24_byte_layout():
    raw = lzma.compress(_candle_payload(1440))
    recs = D.decode_candle_records(raw)
    assert len(recs) == 1440
    sec, o, c, l, h, v = recs[0]
    assert (sec, o, c, l, h) == (0, 100000, 100005, 99995, 100010)
    assert abs(v - 1.5) < 1e-6
    scaled = D.decode_min_candles(raw, SCALE)
    assert scaled[0]["open"] == pytest.approx(1.0)
    assert scaled[1]["high"] == pytest.approx(1.00001 + 10 / SCALE)


def test_tick_roundtrip_20_byte_layout():
    raw = lzma.compress(_tick_payload(3600))
    recs = D.decode_tick_records(raw)
    assert len(recs) == 3600
    assert recs[10] == (10000, 100010, 100000, 1, 1)
    scaled = D.decode_ticks(raw, SCALE)
    ms, a, b, av, bv = scaled[0]
    assert (ms, av, bv) == (0, 1, 1)
    assert a == pytest.approx(1.0001) and b == pytest.approx(1.0)


def test_layout_trap_240_bytes_passes_both_asserts():
    """240 PLAIN bytes is divisible by 20 AND 24: layout asserts alone
    cannot catch a cross-decode — this is why probe_pair.py cross-checks
    content."""
    plain = _candle_payload(10)
    assert len(plain) % 20 == 0 and len(plain) % 24 == 0
    p = lzma.compress(plain)
    assert len(D.decode_candle_records(p)) == 10  # right decode


def test_layout_asserts_fire_on_non_multiples():
    bad_candle = lzma.compress(b"\x00" * (24 * 5 + 4))  # len%24 != 0 (and %20 != 0)
    with pytest.raises(AssertionError):
        D.decode_candle_records(bad_candle)
    bad_tick = lzma.compress(b"\x00" * (20 * 5 + 3))
    with pytest.raises(AssertionError):
        D.decode_tick_records(bad_tick)
    # a tick-grid payload that is NOT a candle multiple must raise on the
    # candle decoder even though it is a valid tick payload
    ticks = lzma.compress(_tick_payload(11))  # 220 bytes: %20==0, %24!=0
    assert len(D.decode_tick_records(ticks)) == 11
    with pytest.raises(AssertionError):
        D.decode_candle_records(ticks)


def test_empty_payload_decodes_empty():
    assert D.decode_candle_records(b"") == []
    assert D.decode_tick_records(b"") == []
    assert D.decompress(b"") == b""


def test_paths_parametrized_by_symbol():
    assert D.candle_path("AUDUSD", 2024, 10, 27, "BID") == \
        "/datafeed/AUDUSD/2024/09/27/BID_candles_min_1.bi5"
    assert D.tick_path("USDCAD", 2024, 1, 3, 21) == \
        "/datafeed/USDCAD/2024/00/03/21h_ticks.bi5"
