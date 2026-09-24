"""Regression: the H1 append edge must keep the ts column datetimelike.

Root cause of the 2026-09-24 daemon death (daemon.log crash #4, at the
06:00Z hour boundary): the seed parquet stores ms-unit timestamps
(datetime64[ms, UTC]) while every live/replayed append is a ns-unit
Timestamp; pd.concat cannot unify ms/ns and silently degraded the whole
ts column to object, so the FROZEN engine's .dt accessor raised
AttributeError inside H1Plane at the first closed H1 bar. The daemon
had never survived one hour roll.

Pins: seed_bars normalizes to datetime64[ns, UTC] at the ingest edge;
on_closed_bar and restore() appends keep the column tz-aware datetime
and the frozen signal computes. Engine semantics untouched.
"""
import pandas as pd
import pytest

import fx_shadow_core as C
import shadow_daemon as SD

PAIR = "EURUSD"


def _ms_seed_parquet(tmp_path, n=48):
    """A seed corpus byte-shaped like the real derived/bars1h.parquet:
    ms-unit tz-aware ts index + the six price columns."""
    idx = pd.date_range("2026-08-01", periods=n, freq="h", tz="UTC")
    idx = idx.astype("datetime64[ms, UTC]")
    base = 1.10
    df = pd.DataFrame(
        {
            "b_o": [base] * n, "b_h": [base + 0.002] * n,
            "b_l": [base - 0.002] * n, "b_c": [base + 0.001] * n,
            "a_o": [base + 0.0001] * n, "a_c": [base + 0.0011] * n,
        },
        index=idx,
    )
    df.index.name = "ts"
    derived = tmp_path / "derived"
    derived.mkdir(parents=True)
    df.to_parquet(derived / "bars1h.parquet")
    return tmp_path


@pytest.fixture
def book(tmp_path, monkeypatch):
    root = _ms_seed_parquet(tmp_path)
    monkeypatch.setitem(SD.SEED_DERIVED, PAIR, root)
    j = SD.Journal(tmp_path / "journal.jsonl")
    return SD.PairBook(PAIR, 1e-4, j)


def _closed_bar(h0_ts):
    return C.LiveBar(h0_ts, 1.1005, 1.1006).as_row()


def test_seed_ts_is_normalized_to_ns_utc(book):
    assert isinstance(book.df["ts"].dtype, pd.DatetimeTZDtype)
    assert str(book.df["ts"].dtype) == "datetime64[ns, UTC]"


def test_on_closed_bar_keeps_ts_datetimelike_and_computes_signal(book):
    # This is the exact crash site: append -> frozen engine .dt accessor.
    h0 = int(book.seed_last_ts) + C.HOUR
    book.on_closed_bar(_closed_bar(h0))
    assert isinstance(book.df["ts"].dtype, pd.DatetimeTZDtype), (
        "append degraded ts to object dtype — the 06:00Z crash would recur"
    )
    assert book.last_target in (-1, 0, 1)
    book.on_closed_bar(_closed_bar(h0 + C.HOUR))
    assert isinstance(book.df["ts"].dtype, pd.DatetimeTZDtype)
    assert len(book.df) == 50


def test_restore_replayed_bars_keeps_ts_datetimelike(book):
    h0 = int(book.seed_last_ts) + C.HOUR
    bar = _closed_bar(h0)
    import json
    line = json.dumps({
        "event": "bar_closed", "pair": PAIR, "bar_ts": bar["ts"],
        "b_o": bar["b_o"], "b_h": bar["b_h"], "b_l": bar["b_l"],
        "b_c": bar["b_c"], "a_o": bar["a_o"], "a_c": bar["a_c"],
    })
    rep = C.replay_journal([line], seed_last_ts={PAIR: 0})
    restored = book.restore(rep["pairs"][PAIR])
    assert restored == 1
    assert isinstance(book.df["ts"].dtype, pd.DatetimeTZDtype)
    assert book.last_target in (-1, 0, 1)
