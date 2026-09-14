"""PIT mutation tests: completed-bar cutoffs, funding windows, fill lag (G2).

No network: the REST client is driven with an injected fetch function
over canned kline bytes. Decision stamp: Monday 2026-01-05T00:00:00Z.
Bars (15m): opens 23:00..00:00; the 23:45 bar closes exactly at the
decision; the 00:00 bar closes 00:15 (the virtual fill reference).
"""

import datetime as dt
import json

import pytest

from research.shadow_v1 import data_feed
from research.shadow_v1.accounting import (
    CURRENT_CONSERVATIVE_COST,
    BookCostParams,
    SleeveAccount,
)
from research.shadow_v1.data_feed import (
    DataBlocked,
    KeylessBinanceFuturesClient,
    feature_eligible_bucket,
    require_complete_bars,
    select_fill_bar,
)

DECISION = "2026-01-05T00:00:00Z"
SYMBOL = "BTCUSDT"

# opens 23:00 .. 00:00 on 2026-01-04/05 UTC, close prices below
OPENS = ["23:00", "23:15", "23:30", "23:45", "00:00"]
CLOSES = [100.0, 100.5, 99.5, 100.0, 101.0]


def _open_ms(hhmm, day=4):
    hh, mm = hhmm.split(":")
    return int(
        dt.datetime(
            2026, 1, day, int(hh), int(mm), tzinfo=dt.timezone.utc
        ).timestamp()
        * 1000
    )


def _kline_row(open_ms, close_price):
    step = 900_000
    return [
        open_ms, "1", "1", "1", str(close_price), "1.0",
        open_ms + step - 1, "10.0", 10, "1.0", "1.0", "1.0",
    ]


def _rows(opens=None, closes=None):
    opens = opens or OPENS
    closes = closes or CLOSES
    rows = []
    for open_str, close in zip(opens, closes):
        day = 5 if open_str == "00:00" else 4
        rows.append(_kline_row(_open_ms(open_str, day), close))
    return rows


def _client(rows):
    def fetch_fn(url):
        return json.dumps(rows).encode()

    return KeylessBinanceFuturesClient(fetch_fn=fetch_fn)


def test_completed_bars_respect_feature_cutoff():
    client = _client(_rows())
    bars = client.get_completed_bars(
        SYMBOL, "15m",
        "2026-01-04T22:45:00Z", "2026-01-05T00:00:00Z",
        DECISION,
    )
    closes = [b.close_time_utc for b in bars]
    # the 00:00 bar closes 00:15 > decision cutoff -> excluded
    assert closes == [
        "2026-01-04T23:15:00Z",
        "2026-01-04T23:30:00Z",
        "2026-01-04T23:45:00Z",
        "2026-01-05T00:00:00Z",
    ]
    assert len(client.last_fetch_records) >= 1
    rec = client.last_fetch_records[0]
    assert set(rec.as_dict()) == {"url", "fetched_at_utc", "response_sha256"}


def test_feature_eligibility_strictly_before_decision():
    # bar closing exactly AT the decision is NOT feature-eligible
    assert feature_eligible_bucket("2026-01-04T23:45:00Z", "15m", DECISION) is False
    assert feature_eligible_bucket("2026-01-04T23:30:00Z", "15m", DECISION) is True
    # a bar closing after the decision is never feature-eligible
    assert feature_eligible_bucket("2026-01-05T00:00:00Z", "15m", DECISION) is False


def test_moving_bar_close_after_cutoff_excludes_it_and_blocks():
    # move the 23:45 bar 16 minutes late: its close lands after the cutoff
    shifted = _rows(opens=["23:00", "23:15", "23:30", "23:46", "00:00"])
    client = _client(shifted)
    bars = client.get_completed_bars(
        SYMBOL, "15m",
        "2026-01-04T22:45:00Z", "2026-01-05T00:00:00Z",
        DECISION,
    )
    # the 23:46 bar closes 00:01 > cutoff (excluded); the 00:00 bar
    # closes 00:15 > end_inclusive (excluded)
    assert [b.open_time_utc for b in bars] == [
        "2026-01-04T23:00:00Z",
        "2026-01-04T23:15:00Z",
        "2026-01-04T23:30:00Z",
    ]
    # a full completed window is required downstream -> the gap blocks
    with pytest.raises(DataBlocked) as excinfo:
        require_complete_bars(
            bars, "15m", "2026-01-04T23:00:00Z", "2026-01-05T00:00:00Z",
        )
    assert "23:45" in str(excinfo.value)


def test_fill_uses_first_completed_bar_strictly_after_decision():
    client = _client(_rows())
    bars = client.get_completed_bars(
        SYMBOL, "15m",
        "2026-01-04T22:45:00Z", "2026-01-05T00:15:00Z",
        "2026-01-05T00:15:00Z",
    )
    fill_bar = select_fill_bar(bars, DECISION)
    assert fill_bar.open_time_utc == "2026-01-05T00:00:00Z"
    assert fill_bar.close_time_utc == "2026-01-05T00:15:00Z"
    assert fill_bar.close_price == 101.0


def test_mutating_decision_bar_close_does_not_change_fill_price():
    rows = _rows()
    mutated = json.loads(json.dumps(rows))
    # the decision bar (open 23:45, close == decision) has its close mutated
    for row in mutated:
        if row[0] == _open_ms("23:45"):
            row[4] = "999.0"
    client = _client(mutated)
    bars = client.get_completed_bars(
        SYMBOL, "15m",
        "2026-01-04T22:45:00Z", "2026-01-05T00:15:00Z",
        "2026-01-05T00:15:00Z",
    )
    fill_bar = select_fill_bar(bars, DECISION)
    assert fill_bar.close_price == 101.0  # unchanged: fill lag is PIT-safe


def test_mutating_fill_bar_close_does_change_fill_reference():
    rows = json.loads(json.dumps(_rows()))
    for row in rows:
        if row[0] == _open_ms("00:00", day=5):
            row[4] = "555.0"
    client = _client(rows)
    bars = client.get_completed_bars(
        SYMBOL, "15m",
        "2026-01-04T22:45:00Z", "2026-01-05T00:15:00Z",
        "2026-01-05T00:15:00Z",
    )
    assert select_fill_bar(bars, DECISION).close_price == 555.0


def test_no_completed_bar_after_decision_blocks():
    bars = data_feed.Bar(
        symbol=SYMBOL, interval="15m",
        open_time_utc="2026-01-04T23:45:00Z",
        close_time_utc="2026-01-05T00:00:00Z",
        close_price=100.0, quote_volume=1.0,
    )
    with pytest.raises(DataBlocked):
        select_fill_bar([bars], DECISION)


def test_client_refuses_non_allowlisted_path():
    client = KeylessBinanceFuturesClient(fetch_fn=lambda url: b"[]")
    with pytest.raises(DataBlocked):
        client.get_json("/fapi/v1/order", {"symbol": SYMBOL})


def test_transport_failure_raises_data_blocked():
    def broken_fetch(url):
        raise OSError("connection refused")

    client = KeylessBinanceFuturesClient(fetch_fn=broken_fetch)
    with pytest.raises(DataBlocked):
        client.get_completed_bars(
            SYMBOL, "15m",
            "2026-01-04T22:45:00Z", "2026-01-05T00:00:00Z",
            DECISION,
        )


def test_settled_funding_cutoff_and_window():
    settlements = [
        {"fundingTime": _open_ms("23:00", 4), "fundingRate": "0.0001", "markPrice": "100"},
        {"fundingTime": _open_ms("08:00", 5), "fundingRate": "0.0002", "markPrice": "101"},
        {"fundingTime": _open_ms("16:00", 5), "fundingRate": "-0.0001", "markPrice": "102"},
    ]
    client = KeylessBinanceFuturesClient(fetch_fn=lambda url: json.dumps(settlements).encode())
    got = client.get_settled_funding(
        SYMBOL, "2026-01-04T00:00:00Z", "2026-01-05T12:00:00Z",
        "2026-01-05T00:00:00Z",  # cutoff = decision
    )
    # only settlements with fundingTime <= decision cutoff
    assert [s.funding_time_utc for s in got] == ["2026-01-04T23:00:00Z"]


# ---------------------------------------------------------------------------
# funding settlement booking window (accounting side of PIT)
# ---------------------------------------------------------------------------

OPEN_TS = "2026-01-05T00:15:00Z"  # ts_opened (fill time)
CLOSE_TS = "2026-01-12T00:15:00Z"  # ts_closed


def _held_account():
    acct = SleeveAccount(
        sleeve_id="sleeve_pit",
        books={CURRENT_CONSERVATIVE_COST: BookCostParams(0.0005, 1.0)},
    )
    acct.apply_fill("BTCUSDT", "buy", 0.5, 80_000.0, 0.10, OPEN_TS)
    return acct


def test_funding_before_ts_opened_never_booked():
    acct = _held_account()
    res = acct.apply_funding("BTCUSDT", "2026-01-05T00:00:00Z", 0.0001, 80_000.0)
    assert res.booked is False and res.reason == "outside_holding_window"
    assert acct.books[CURRENT_CONSERVATIVE_COST].funding_cashflow == 0.0


def test_funding_at_or_after_ts_closed_never_booked():
    acct = _held_account()
    acct.apply_fill("BTCUSDT", "sell", 0.5, 81_000.0, 0.10, CLOSE_TS)
    res = acct.apply_funding("BTCUSDT", CLOSE_TS, 0.0001, 81_000.0)
    assert res.booked is False and res.reason == "no_open_position"


def test_funding_inside_window_booked_exactly_once():
    acct = _held_account()
    inside = "2026-01-09T08:00:00Z"
    assert OPEN_TS <= inside < CLOSE_TS
    res = acct.apply_funding("BTCUSDT", inside, 0.0001, 80_000.0)
    assert res.booked is True
    dup = acct.apply_funding("BTCUSDT", inside, 0.0001, 80_000.0)
    assert dup.booked is False and dup.reason == "already_booked"
    assert acct.books[CURRENT_CONSERVATIVE_COST].funding_cashflow == res.cashflow
