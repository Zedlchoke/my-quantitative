"""PC12A panel loader round-trip + coverage gates (synthetic .bi5 bytes)."""

import datetime as dt
import lzma
import struct

import numpy as np
import pytest

from research.pc12a import panels

SYMS = ("EURUSD", "GBPUSD", "USDJPY")


def _make_day(symbol, seed=7):
    return panels.synthetic_day_bytes(symbol, dt.date(2024, 6, 5),
                                      mid_level={"EURUSD": 1.085,
                                                 "GBPUSD": 1.27,
                                                 "USDJPY": 156.2}[symbol],
                                      seed=seed)


@pytest.mark.parametrize("symbol", SYMS)
def test_bi5_round_trip(symbol):
    bid_bytes, ask_bytes = _make_day(symbol)
    day = panels.load_day_from_bytes(symbol, dt.date(2024, 6, 5), bid_bytes,
                                     ask_bytes)
    assert len(day.bid.sec) == 1440
    assert np.array_equal(day.bid.sec, np.arange(0, 86400, 60))
    spec = panels.PAIR_SPECS[symbol]
    # prices decode into a sane band for the pair
    assert day.mid_open.min() > 0
    if symbol == "USDJPY":
        assert 100.0 < day.mid_close.mean() < 200.0
    else:
        assert 0.5 < day.mid_close.mean() < 2.0
    # ask >= bid everywhere (audit: 0 negative-spread minutes)
    assert (day.ask.open >= day.bid.open).all()
    assert (day.ask.close >= day.bid.close).all()
    # OHLC invariant holds on both sides
    for side in (day.bid, day.ask):
        assert (side.low <= np.minimum(side.open, side.close)).all()
        assert (side.high >= np.maximum(side.open, side.close)).all()
    # volume column is the float32 activity proxy (not a count)
    assert day.bid.volume.dtype == np.float64
    assert (day.bid.volume >= 0).all()


def test_record_struct_is_24_bytes_big_endian():
    assert panels.RECORD_STRUCT.size == 24
    packed = panels.RECORD_STRUCT.pack(60, 108500, 108520, 108490, 108530,
                                       12.5)
    assert len(packed) == 24
    t, o, c, l, h, v = panels.RECORD_STRUCT.unpack(packed)
    assert (t, o, c, l, h, v) == (60, 108500, 108520, 108490, 108530, 12.5)


def test_price_divisors_per_audit():
    assert panels.PAIR_SPECS["EURUSD"].price_divisor == 1e5
    assert panels.PAIR_SPECS["GBPUSD"].price_divisor == 1e5
    assert panels.PAIR_SPECS["USDJPY"].price_divisor == 1e3
    assert panels.PAIR_SPECS["EURUSD"].pip_size == 0.0001
    assert panels.PAIR_SPECS["USDJPY"].pip_size == 0.01


def test_truncated_payload_fails_closed():
    bid, ask = _make_day("EURUSD")
    bad = bid[:-10]
    with pytest.raises(panels.PanelError):
        panels.load_day_from_bytes("EURUSD", dt.date(2024, 6, 5), bad, ask)


def test_corrupt_payload_fails_closed():
    with pytest.raises(panels.PanelError):
        panels.decode_bi5(b"not-lzma-at-all")


def test_negative_spread_rejected():
    sec = np.arange(0, 86400, 60, dtype=np.int64)
    n = len(sec)
    vol = np.full(n, 5.0)
    # ask strictly BELOW bid on every bar -> integrity trip
    bid = panels.compress_bi5(panels.encode_bi5(
        sec, np.full(n, 108510), np.full(n, 108510), np.full(n, 108510),
        np.full(n, 108510), vol))
    ask = panels.compress_bi5(panels.encode_bi5(
        sec, np.full(n, 108500), np.full(n, 108500), np.full(n, 108500),
        np.full(n, 108500), vol))
    with pytest.raises(panels.PanelError):
        panels.load_day_from_bytes("EURUSD", dt.date(2024, 6, 5), bid, ask)


def test_carry_forward_day_is_excluded_from_tradable():
    sec = np.arange(0, 86400, 60, dtype=np.int64)
    n = len(sec)
    flat = np.full(n, 108500, dtype=float)
    zero = np.zeros(n)
    bid = panels.compress_bi5(panels.encode_bi5(sec, flat, flat, flat, flat,
                                                zero))
    ask = panels.compress_bi5(panels.encode_bi5(sec, flat + 2, flat + 2,
                                                flat + 2, flat + 2, zero))
    day = panels.load_day_from_bytes("EURUSD", dt.date(2021, 5, 22), bid,
                                     ask)
    assert day.tradable_mask().sum() == 0  # weekend carry-forward


def test_synthetic_day_is_deterministic():
    a = _make_day("EURUSD", seed=3)
    b = _make_day("EURUSD", seed=3)
    assert a[0] == b[0] and a[1] == b[1]


def test_lzma_alone_format():
    bid, _ = _make_day("EURUSD")
    payload = lzma.decompress(bid)
    assert len(payload) == 1440 * 24
    # first record fields decode as documented order (t, o, c, l, h, v)
    t, o, c, l, h, v = struct.unpack(">5I f", payload[:24])
    assert t == 0 and l <= min(o, c) <= max(o, c) <= h and v >= 0
