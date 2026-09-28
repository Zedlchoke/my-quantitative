"""Tests for pr12a100k loaders (Lane I1a). All fixtures are tiny synthetic
files under tests/fixtures/ (regenerate with ``python gen_fixtures.py``),
EXCEPT the optional ANC real-panel smoke test which skips when the panel is
absent. No test touches the network or the full 37MB corpora.
"""

import os
import sys

import numpy as np
import pandas as pd
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

import loaders  # noqa: E402

FIX = os.path.join(HERE, "fixtures")
PTS = 1e-5  # fixture price scale (EURUSD, 1e5 points)


# ---------------------------------------------------------------------------
# (i) macro parsing + '.' missing handling
# ---------------------------------------------------------------------------

def test_macro_fredgraph_parse_and_missing():
    s, meta = loaders.load_macro_series(
        os.path.join(FIX, "macro", "dgs10_mini.csv"), "fredgraph_csv"
    )
    assert meta["series_name"] == "DGS10"
    assert list(s.index) == list(pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-05"]))
    assert s.loc["2026-01-01"] == 4.23
    assert np.isnan(s.loc["2026-01-02"])  # '.' -> missing, not zero
    assert s.loc["2026-01-05"] == 4.31
    assert meta["n_missing"] == 1 and meta["n_obs"] == 3
    assert len(meta["sha256"]) == 64


def test_macro_effr_parse_and_revisions():
    s, meta = loaders.load_macro_series(
        os.path.join(FIX, "macro", "effr_mini.json"), "nyfed_effr_json"
    )
    assert meta["series_name"] == "EFFR"
    assert s.loc["2026-01-01"] == 4.33
    assert s.loc["2026-01-02"] == 4.30
    assert s.loc["2026-01-05"] == 4.29  # numeric percentRate accepted too
    assert meta["n_revisions"] == 1
    assert meta["revisions"] == [("2026-01-02", True)]


# ---------------------------------------------------------------------------
# (ii) PIT guard: value published T+1 never visible at T
# ---------------------------------------------------------------------------

def test_asof_pit_t_plus_1():
    obs = pd.Series(
        [1.0, 2.0, 3.0],
        index=pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"]),
    )
    # value observed 2026-01-02 (2.0) has available_at 2026-01-03 under T+1d
    assert np.isnan(loaders.asof(obs, "2026-01-01 23:59", rule="T+1d"))
    assert loaders.asof(obs, "2026-01-02 23:59", rule="T+1d") == 1.0  # only 1.0 visible
    assert loaders.asof(obs, "2026-01-03 00:00", rule="T+1d") == 2.0  # 2.0 just became visible
    assert loaders.asof(obs, "2026-01-04 12:00", rule="T+1d") == 3.0
    # same-day rule sees the observation on its own date
    assert loaders.asof(obs, "2026-01-02 00:00", rule="T+0d") == 2.0
    assert loaders.asof(obs, "2026-01-01 23:59", rule="T+0d") == 1.0
    # tz-aware decision stamps are accepted (converted to UTC)
    assert loaders.asof(obs, pd.Timestamp("2026-01-03T01:00:00+02:00"), "T+1d") == 1.0


def test_asof_missing_and_negative_spread_fail_loud():
    obs = pd.Series([1.0], index=pd.to_datetime(["2026-01-01"]))
    assert np.isnan(loaders.asof(obs, "2025-12-31", rule="T+1d"))  # nothing visible yet
    with pytest.raises(ValueError):
        loaders.asof(obs, "2026-01-02", rule="T+1b")  # unknown rule
    dup = pd.Series([1.0, 2.0], index=pd.to_datetime(["2026-01-01", "2026-01-01"]))
    with pytest.raises(ValueError):
        loaders.asof(dup, "2026-01-05", rule="T+1d")


# ---------------------------------------------------------------------------
# M1 decode + union + tradable flag
# ---------------------------------------------------------------------------

def test_bi5_fixture_decode_union_and_tradable():
    df, meta = loaders.load_fx_m1(
        "EURUSD", start="2021-11-07", end="2021-11-08", root=os.path.join(FIX, "bi5")
    )
    assert meta["files"] == {"BID": 2, "ASK": 2}
    # 2021-11-07 has 1440 minutes + 2021-11-08 hour 0 has 60 -> 1500 rows
    assert len(df) == 1500
    assert str(df.index.min()) == "2021-11-07 00:01:00+00:00"  # close-stamped minutes
    assert str(df.index.max()) == "2021-11-08 01:00:00+00:00"

    # minute 00:00 of 2021-11-07 (stamped 00:01): p=119000 pts
    row = df.loc["2021-11-07 00:01:00+00:00"]
    assert row["bid_o"] == pytest.approx(119000 * PTS)
    assert row["bid_c"] == pytest.approx(119001 * PTS)
    assert row["bid_l"] == pytest.approx((119000 - 1) * PTS)
    assert row["bid_h"] == pytest.approx((119000 + 2) * PTS)
    assert row["ask_o"] == pytest.approx((119000 + 2) * PTS)
    assert row["mid_o"] == pytest.approx((119000 + 1) * PTS)
    assert row["spread_open"] == pytest.approx(2 * PTS)
    assert bool(row["tradable"]) is True

    # flat zero-volume minute 12:00 (stamped 12:01) is kept but not tradable
    flat = df.loc["2021-11-07 12:01:00+00:00"]
    assert flat["bid_o"] == flat["bid_c"] == flat["bid_l"] == flat["bid_h"]
    assert bool(flat["tradable"]) is False
    assert meta["tradable_rows"] == 1499

    df_t, meta_t = loaders.load_fx_m1(
        "EURUSD", start="2021-11-07", end="2021-11-08",
        root=os.path.join(FIX, "bi5"), tradable_only=True,
    )
    assert len(df_t) == 1499
    assert not (df_t.index == pd.Timestamp("2021-11-07 12:01:00+00:00")).any()


# ---------------------------------------------------------------------------
# (iii) M1 -> H1 hand-computed fixture
# ---------------------------------------------------------------------------

def expected_h1(hour_of_day: int, day: str) -> dict:
    """Closed-form expectation from the generator rules (independent re-derive).

    For hour h: minute p ranges over 119000+h*60 .. 119000+h*60+59.
      bid_o = p_first, bid_c = p_last+1, bid_h = p_last+2, bid_l = p_first-1
      ask = bid + 2 points everywhere; volume 10/minute.
    """
    p0 = 119000 + hour_of_day * 60
    p1 = p0 + 59
    return {
        "bid_o": p0 * PTS,
        "bid_c": (p1 + 1) * PTS,
        "bid_h": (p1 + 2) * PTS,
        "bid_l": (p0 - 1) * PTS,
        "ask_o": (p0 + 2) * PTS,
        "ask_c": (p1 + 3) * PTS,
        "ask_h": (p1 + 4) * PTS,
        "ask_l": (p0 + 1) * PTS,
        "mid_o": (p0 + 1) * PTS,
        "mid_c": (p1 + 2) * PTS,
        "spread_open": 2 * PTS,
        "spread_close": 2 * PTS,
        "spread_mean": 2 * PTS,
        "volume": 600.0,
        "n_minutes": 60,
        "label": pd.Timestamp(f"{day} {hour_of_day:02d}:00:00+00:00") + pd.Timedelta(hours=1),
    }


def test_resample_h1_hand_computed():
    df, _ = loaders.load_fx_m1(
        "EURUSD", start="2021-11-07", end="2021-11-07", root=os.path.join(FIX, "bi5")
    )
    h1 = loaders.resample_bars(df, "h")
    for hod in (0, 1, 2, 23):
        exp = expected_h1(hod, "2021-11-07")
        row = h1.loc[exp["label"]]
        for key, val in exp.items():
            if key == "label":
                continue
            assert row[key] == pytest.approx(val, abs=1e-12), (hod, key)
    # hour 12 contains the flat minute: open from minute 12:00, volume 590
    exp = expected_h1(12, "2021-11-07")
    row = h1.loc[exp["label"]]
    assert row["bid_o"] == pytest.approx((119000 + 12 * 60) * PTS)  # flat minute open
    assert row["volume"] == pytest.approx(590.0)
    assert row["n_minutes"] == 60


# ---------------------------------------------------------------------------
# (iv) DST boundary days: 23 / 25 hour resample counts
# ---------------------------------------------------------------------------

def test_resample_dst_23_hours_march():
    # 2021-03-14 fixture has the 02:00 hour absent (US spring-forward day):
    # the resampler must yield exactly 23 H1 bars, dropping the empty bucket
    # instead of fabricating a 24th.
    df, _ = loaders.load_fx_m1(
        "EURUSD", start="2021-03-14", end="2021-03-14", root=os.path.join(FIX, "bi5")
    )
    assert len(df) == 23 * 60
    h1 = loaders.resample_bars(df, "h")
    day_bars = h1[(h1.index > pd.Timestamp("2021-03-14 00:00:00+00:00"))
                  & (h1.index <= pd.Timestamp("2021-03-15 00:00:00+00:00"))]
    assert len(day_bars) == 23
    labels = {ts.strftime("%H:%M") for ts in day_bars.index}
    assert "03:00" not in labels  # the (02:00, 03:00] bucket has no minutes
    assert "01:00" in labels and "00:00" in labels  # hour 23 -> next-day label
    assert day_bars["n_minutes"].sum() == 23 * 60
    # D1 rollup: one close-stamped daily bar labeled next midnight, 1380 min
    d1 = loaders.resample_bars(df, "d")
    assert list(d1.index) == [pd.Timestamp("2021-03-15 00:00:00+00:00")]
    assert d1.iloc[0]["n_minutes"] == 1380


def test_resample_dst_25_hours_november():
    # 2021-11-07 full day + 2021-11-08 hour 0: the [Nov7 00:00, Nov8 01:00)
    # span spans 25 wall-clock hours; the resampler must produce 25 H1 bars.
    df, _ = loaders.load_fx_m1(
        "EURUSD", start="2021-11-07", end="2021-11-08", root=os.path.join(FIX, "bi5")
    )
    h1 = loaders.resample_bars(df, "h")
    span = h1[(h1.index > pd.Timestamp("2021-11-07 00:00:00+00:00"))
              & (h1.index <= pd.Timestamp("2021-11-08 01:00:00+00:00"))]
    assert len(span) == 25
    assert span["n_minutes"].sum() == 25 * 60
    # D1: two close-stamped bars — Nov7 day (1440 min, labeled Nov8 00:00)
    # and the Nov8 hour-0 remnant (60 min, labeled Nov9 00:00).
    d1 = loaders.resample_bars(df, "d")
    assert list(d1.index) == [pd.Timestamp("2021-11-08 00:00:00+00:00"),
                              pd.Timestamp("2021-11-09 00:00:00+00:00")]
    assert list(d1["n_minutes"]) == [1440, 60]
    assert d1.iloc[0]["bid_c"] == pytest.approx((119000 + 1439 + 1) * PTS)


# ---------------------------------------------------------------------------
# (v) fail-closed: malformed / missing inputs raise
# ---------------------------------------------------------------------------

def test_fail_closed_missing_macro_file():
    with pytest.raises(FileNotFoundError):
        loaders.load_macro_series(os.path.join(FIX, "macro", "nope.csv"), "fredgraph_csv")


def test_fail_closed_unknown_macro_format():
    with pytest.raises(ValueError):
        loaders.load_macro_series(os.path.join(FIX, "macro", "dgs10_mini.csv"), "csv")


def test_fail_closed_bad_fredgraph_header():
    with pytest.raises(ValueError, match="observation_date"):
        loaders.load_macro_series(os.path.join(FIX, "macro", "bad_header.csv"), "fredgraph_csv")


def test_fail_closed_bad_fredgraph_value():
    with pytest.raises(ValueError, match="unparsable value"):
        loaders.load_macro_series(os.path.join(FIX, "macro", "bad_value.csv"), "fredgraph_csv")


def test_fail_closed_bad_effr_record():
    with pytest.raises(ValueError, match="missing fields"):
        loaders.load_macro_series(os.path.join(FIX, "macro", "bad_effr.json"), "nyfed_effr_json")


def test_fail_closed_missing_fx_corpus_dir():
    with pytest.raises(FileNotFoundError):
        loaders.load_fx_m1("EURUSD", root=os.path.join(FIX, "does_not_exist"))


def test_fail_closed_empty_fx_range():
    with pytest.raises(ValueError, match="no .bi5 files"):
        loaders.load_fx_m1("EURUSD", start="1999-01-01", end="1999-01-02",
                           root=os.path.join(FIX, "bi5"))


def test_fail_closed_corrupt_bi5_payload():
    with open(os.path.join(FIX, "bi5", "corrupt", "not24.bi5"), "rb") as fh:
        raw = fh.read()
    with pytest.raises(ValueError, match="multiple of 24"):
        loaders.decode_bi5_minutes(raw, 1e5, pd.Timestamp("2021-01-01"))


def test_fail_closed_empty_bi5_payload():
    with pytest.raises(ValueError, match="empty"):
        loaders.decode_bi5_minutes(b"", 1e5, pd.Timestamp("2021-01-01"))


def test_fail_closed_unknown_symbol_and_rule():
    with pytest.raises(ValueError):
        loaders.load_fx_m1("XYZUSD")
    with pytest.raises(ValueError):
        loaders.load_fx_h1("EURUSD")  # no ANC panel for M1 symbols
    with pytest.raises(ValueError):
        loaders.resample_bars(pd.DataFrame(index=pd.DatetimeIndex([], tz="UTC")), "h")


# ---------------------------------------------------------------------------
# optional real-panel smoke tests (skip when the big corpora are absent)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not os.path.isfile(loaders.FX_PANELS["AUDUSD"]["panel_path_glob"]),
    reason="real ANC panel not present in this checkout",
)
def test_real_anc_h1_close_shift_smoke():
    df, meta = loaders.load_fx_h1("AUDUSD")
    assert str(df.index.tz) == "UTC"
    # source is open-stamped 2021-01-03 23:00 -> close-shifted to 2021-01-04 00:00
    assert df.index.min() == pd.Timestamp("2021-01-04 00:00:00+00:00")
    assert len(df) == 30420
    assert df.index.is_monotonic_increasing and not df.index.has_duplicates
    assert (df["spread_open"] > 0).all()
