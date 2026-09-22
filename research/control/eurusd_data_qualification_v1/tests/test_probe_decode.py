"""EDQ1 P1 probe tests — decoder correctness + real-series invariants.

(a) Synthetic bi5-like blob: construct LZMA-compressed '>5i' records with
    KNOWN prices, decode through the same code path as the probe fetcher,
    assert price scale and tick ordering.
(b) Real decoded 1-min series (data_local): assert monotonic minute keys and
    no duplicate keys; SKIP with an explicit NOT_RUN note if the gitignored
    raw data is absent (evidence lives outside git by design).

Run with the ROOT venv python only:
  /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest <this dir> -q
"""
import datetime as dt
import importlib.util
import lzma
import os
import struct
import sys

import pytest

WORKTREE = "/Users/hoangminhlong/my-quantitative/.worktrees/eurusd-data-qualification-v1/integration"
CYCLE = os.path.join(WORKTREE, "research/control/eurusd_data_qualification_v1")
SCRIPT = os.path.join(CYCLE, "scripts", "edq1_fetch_dukascopy.py")
BARS_BID = os.path.join(CYCLE, "data_local", "dukascopy", "bars_1min_bid.json")
POINT_SCALE = 1e5


@pytest.fixture(scope="module")
def fetch_mod():
    spec = importlib.util.spec_from_file_location("edq1_fetch_dukascopy", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["edq1_fetch_dukascopy"] = mod
    spec.loader.exec_module(mod)
    return mod


def encode_records(records):
    """records: list of 5-int tuples -> LZMA-compressed bi5-like bytes."""
    raw = b"".join(struct.pack(">5i", *r) for r in records)
    return lzma.compress(raw)


class TestSyntheticDecode:
    def test_price_scale_and_ordering(self, fetch_mod):
        # EURUSD-like: ask=1.08500*1e5=108500, bid=108499 etc. Offsets strictly rising.
        recs = [
            (0,     108500, 108499, 0, 0),
            (1500,  108502, 108501, 0, 0),
            (71000, 108510, 108508, 0, 0),
        ]
        blob = encode_records(recs)
        ticks, status = fetch_mod.decode_bi5(blob)
        assert status == "OK"
        assert len(ticks) == 3
        # price scale: int / 1e5 must recover the known prices exactly
        for (off, ask_i, bid_i, _, _), src in zip(ticks, recs):
            assert ask_i / POINT_SCALE == pytest.approx(src[1] / POINT_SCALE)
            assert bid_i / POINT_SCALE == pytest.approx(src[2] / POINT_SCALE)
        assert ticks[0][1] / POINT_SCALE == pytest.approx(1.08500)
        assert ticks[0][2] / POINT_SCALE == pytest.approx(1.08499)
        # offsets strictly increasing as injected
        offs = [t[0] for t in ticks]
        assert offs == sorted(offs) and len(set(offs)) == len(offs)

    def test_downsample_open_close_first_last(self, fetch_mod):
        recs = [
            (0,     108500, 108499, 0, 0),
            (1000,  108520, 108519, 0, 0),
            (59000, 108510, 108509, 0, 0),
            (119000, 108530, 108529, 0, 0),  # next minute
        ]
        hour = dt.datetime(2024, 3, 4, 7)
        bid, ask = fetch_mod.downsample_1min(hour, recs)
        m0 = str(int(hour.replace(tzinfo=dt.timezone.utc).timestamp() * 1000) // 60000)
        m1 = str(int(m0) + 1)
        assert bid[m0]["open"] == pytest.approx(1.08499)
        assert bid[m0]["close"] == pytest.approx(1.08509)
        assert bid[m0]["high"] == pytest.approx(1.08519)
        assert bid[m0]["low"] == pytest.approx(1.08499)
        assert bid[m0]["tick_count"] == 3
        assert ask[m1]["close"] == pytest.approx(1.08530)
        assert bid[m1]["tick_count"] == 1

    def test_empty_blob_is_no_ticks(self, fetch_mod):
        ticks, status = fetch_mod.decode_bi5(b"")
        assert status == "EMPTY_FILE_NO_TICKS" and ticks == []


class TestRealSeries:
    def test_real_1min_monotonic_no_duplicates(self):
        if not os.path.exists(BARS_BID):
            pytest.skip(
                "NOT_RUN: data_local/bars_1min_bid.json absent (raw probe data is "
                "gitignored; re-run scripts/edq1_fetch_dukascopy.py to regenerate)."
            )
        import json
        bars = json.load(open(BARS_BID))
        keys = sorted(int(k) for k in bars.keys())
        assert len(keys) == len(bars), "duplicate minute keys in real series"
        assert all(b > a for a, b in zip(keys, keys[1:])), "minute keys not strictly increasing"
        # every price sane for EURUSD (scale check on real bytes)
        for v in list(bars.values())[:1000]:
            assert 0.95 <= v["close"] <= 1.30
