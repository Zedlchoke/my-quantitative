"""FOREX-FREE-V2 accounting kernel goldens (F2-P1, A2 lane).

Every expected number below is a HAND-COMPUTED literal with the arithmetic
written in the comment next to it.  Fixtures are SYNTHETIC_TEST_ONLY; no
real-market PnL, no network, no new data authority.

Frozen conventions under test (V1 terminal authority carried unchanged):
  pnl_usd = direction * notional_usd * (exit_price / entry_price - 1)
            direction = +1 LONG, -1 SHORT; notional = 10000 USD-units.
  cost    = notional * (1.5 bps * tier) / 10000, once per fill side.

Hand math for the three golden round trips (notional 10000 USD-units):

  T1 EUR/USD LONG, entry 1.1000 -> exit 1.1550, tier 1.0:
     gross: 1.1550 / 1.1000 = 1.05 exactly -> 10000 * (1.05 - 1) = +500.00 USD
     cost/side: 10000 * (1.5 * 1.0) / 10000 = 1.50 -> round trip 3.00
     net: 500.00 - 3.00 = 497.00

  T2 USD/JPY SHORT (a LOSING short: price rose), entry 150.00 -> exit 151.50,
     tier 1.5:
     gross: -1 * 10000 * (151.50 / 150.00 - 1) = -10000 * 0.01 = -100.00 USD
     cost/side: 10000 * (1.5 * 1.5) / 10000 = 2.25 -> round trip 4.50
     net: -100.00 - 4.50 = -104.50

  T3 GBP/USD LONG, entry == exit == 1.2700 (EXACTLY FLAT), tier 2.0:
     gross: 10000 * (1.2700 / 1.2700 - 1) = 10000 * 0 = 0.0 (exact in IEEE:
            x/x == 1.0 for finite positive x, so pnl == 0.0 exactly)
     cost/side: 10000 * (1.5 * 2.0) / 10000 = 3.00 -> round trip 6.00
     net: 0.00 - 6.00 = -6.00

  Book totals: pnl 500 + (-100) + 0 = 400.00 gross;
               costs 3.00 + 4.50 + 6.00 = 13.50 (all exact in binary);
               net 400.00 - 13.50 = 386.50;
               turnover 3 entry fills x 10000 + 3 exit fills x 10000 = 60000.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import threading

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from research.assets.forex_free_v2 import accounting as A  # noqa: E402

NOTIONAL = 10000.0

# Hand-computed golden literals (arithmetic in the module docstring).
T1_PNL = 500.00        # EUR/USD LONG tier 1.0
T2_PNL = -100.00       # USD/JPY SHORT tier 1.5
T3_PNL = 0.00          # GBP/USD LONG tier 2.0, exactly flat
T1_COST_RT = 3.00      # 1.50 + 1.50
T2_COST_RT = 4.50      # 2.25 + 2.25
T3_COST_RT = 6.00      # 3.00 + 3.00
BOOK_COST_RT = 13.50   # 3.00 + 4.50 + 6.00
BOOK_PNL = 400.00      # 500 - 100 + 0
BOOK_NET = 386.50      # 400 - 13.50


def _open(book, tid, pair, side, price, tier, ts="2026-01-05T10:00:00+00:00"):
    return book.open_position(trade_id=tid, pair=pair, side=side,
                              notional_usd=NOTIONAL, price=price,
                              ts_utc=ts, cost_tier=tier)


def _round_trip(book, tid, pair, side, entry, exit_, tier):
    _open(book, tid, pair, side, entry, tier, ts="2026-01-05T10:00:00+00:00")
    return book.close_position(tid, exit_, ts_utc="2026-01-05T15:00:00+00:00")


def _golden_book():
    book = A.PositionBook()
    _round_trip(book, "T1-EURUSD", "EUR/USD", "LONG", 1.1000, 1.1550, 1.0)
    _round_trip(book, "T2-USDJPY", "USD/JPY", "SHORT", 150.00, 151.50, 1.5)
    _round_trip(book, "T3-GBPUSD", "GBP/USD", "LONG", 1.2700, 1.2700, 2.0)
    return book


# --- golden round trips -------------------------------------------------------- #
def test_positive_trade_golden():
    book = A.PositionBook()
    closed = _round_trip(book, "T1-EURUSD", "EUR/USD", "LONG", 1.1000, 1.1550, 1.0)
    # 10000 * (1.1550/1.1000 - 1) = 10000 * 0.05 = +500.00
    assert closed.pnl_usd == pytest.approx(T1_PNL, rel=1e-9)
    # costs are exact binary numbers: 10000*(1.5*1.0)/10000 = 1.50 per side
    assert closed.entry_cost_usd == T1_COST_RT / 2 == 1.50
    assert closed.exit_cost_usd == 1.50
    # net = 500.00 - 1.50 - 1.50 = 497.00
    assert closed.net_pnl_usd == pytest.approx(497.00, abs=1e-9)
    assert book.total_cost_usd == 3.00
    assert book.open_trade_ids == []


def test_negative_trade_golden():
    book = A.PositionBook()
    closed = _round_trip(book, "T2-USDJPY", "USD/JPY", "SHORT", 150.00, 151.50, 1.5)
    # short lost: -1 * 10000 * (151.50/150.00 - 1) = -10000 * 0.01 = -100.00
    assert closed.pnl_usd == pytest.approx(T2_PNL, rel=1e-9)
    # 10000*(1.5*1.5)/10000 = 2.25 per side, 4.50 round trip
    assert closed.entry_cost_usd == 2.25 and closed.exit_cost_usd == 2.25
    # net = -100.00 - 4.50 = -104.50
    assert closed.net_pnl_usd == pytest.approx(-104.50, abs=1e-9)
    assert book.total_cost_usd == 4.50


def test_exactly_flat_trade_golden():
    book = A.PositionBook()
    closed = _round_trip(book, "T3-GBPUSD", "GBP/USD", "LONG", 1.2700, 1.2700, 2.0)
    # x/x - 1 == 0 exactly in IEEE for finite positive x
    assert closed.pnl_usd == 0.0
    # costs are still charged both sides: 3.00 + 3.00 = 6.00
    assert closed.entry_cost_usd == 3.00 and closed.exit_cost_usd == 3.00
    assert book.total_cost_usd == T3_COST_RT == 6.00
    # net = 0.00 - 6.00 = -6.00 exactly
    assert closed.net_pnl_usd == -6.00
    assert book.net_usd_total == -6.00


def test_golden_book_totals():
    book = _golden_book()
    assert len(book.fills) == 6          # 3 round trips x 2 legs
    assert len(book.closed_trades) == 3
    assert [t.pnl_usd for t in book.closed_trades] == \
        pytest.approx([T1_PNL, T2_PNL, T3_PNL], rel=1e-9)
    assert book.pnl_usd_total == pytest.approx(BOOK_PNL, rel=1e-9)   # 400.00
    assert book.total_cost_usd == BOOK_COST_RT                        # 13.50 exact
    assert book.net_usd_total == pytest.approx(BOOK_NET, abs=1e-9)   # 386.50


# --- missing bar / NO_TRADE sentinel -------------------------------------------- #
def test_missing_bar_produces_no_position_and_no_cost():
    book = A.PositionBook()
    sentinel = book.record_no_trade(pair="EUR/USD", ts_utc="2026-01-05T10:00:00+00:00",
                                    reason="MISSING_BAR")
    assert sentinel.pair == "EUR/USD" and sentinel.reason == "MISSING_BAR"
    # NO fill, NO position, NO cost, NO turnover, NO trade count
    assert book.fills == []
    assert book.open_trade_ids == []
    assert book.closed_trades == []
    assert book.total_cost_usd == 0.0
    assert turnover_is_zero(A.turnover_from_fills(book.fills))
    assert A.trades_from_fills(book.fills)["round_trips"] == 0
    assert A.trades_from_fills(book.fills)["open_positions"] == 0


def test_no_trade_sentinel_leaves_fills_reconciliation_unchanged():
    book = _golden_book()
    before_turnover = A.turnover_from_fills(book.fills)
    before_trades = A.trades_from_fills(book.fills)
    book.record_no_trade(pair="USD/JPY", ts_utc="2026-01-06T10:00:00+00:00",
                         reason="NO_TRADE_NO_SIGNAL")
    # a sentinel never appends a Fill: reconciliation is provably unchanged
    assert len(book.fills) == 6
    assert A.turnover_from_fills(book.fills) == before_turnover
    assert A.trades_from_fills(book.fills) == before_trades
    assert len(book.no_trades) == 1


def turnover_is_zero(turnover):
    return (turnover["entry_notional_usd"] == 0.0
            and turnover["exit_notional_usd"] == 0.0
            and turnover["total_notional_usd"] == 0.0
            and turnover["n_entry_fills"] == 0
            and turnover["n_exit_fills"] == 0)


# --- cost charged exactly once per side, all three tiers ------------------------- #
@pytest.mark.parametrize("tier,per_side,round_trip", [
    (1.0, 1.50, 3.00),   # 10000 * (1.5 * 1.0) / 10000 = 1.50 per side
    (1.5, 2.25, 4.50),   # 10000 * (1.5 * 1.5) / 10000 = 2.25 per side
    (2.0, 3.00, 6.00),   # 10000 * (1.5 * 2.0) / 10000 = 3.00 per side
])
def test_cost_charged_exactly_once_per_side_all_tiers(tier, per_side, round_trip):
    # helper agrees with the hand math first
    assert A.bps_cost(NOTIONAL, tier) == per_side
    book = A.PositionBook()
    _round_trip(book, f"T-{tier}", "EUR/USD", "LONG", 1.1000, 1.1550, tier)
    entry_fills = [f for f in book.fills if f.leg == "ENTRY"]
    exit_fills = [f for f in book.fills if f.leg == "EXIT"]
    # EXACTLY one cost-bearing fill per side -> exactly 2 cost entries per RT
    assert len(entry_fills) == 1 and len(exit_fills) == 1
    assert all(f.cost_usd > 0 for f in book.fills)
    # sum of cost entries matches the hand math exactly
    assert sum(f.cost_usd for f in book.fills) == round_trip
    assert entry_fills[0].cost_usd == per_side and exit_fills[0].cost_usd == per_side
    # tier is stamped on both fills; the exit reuses the tier bound at entry
    assert entry_fills[0].cost_tier == tier and exit_fills[0].cost_tier == tier
    assert book.total_cost_usd == round_trip


def test_bps_cost_rejects_unknown_tier():
    with pytest.raises(A.PositionBookError, match="BAD_COST_TIER"):
        A.bps_cost(NOTIONAL, 1.7)


# --- rejections (book state unchanged) ------------------------------------------- #
def test_double_open_rejected():
    book = A.PositionBook()
    _open(book, "T1", "EUR/USD", "LONG", 1.1000, 1.0)
    with pytest.raises(A.PositionBookError, match="DOUBLE_OPEN"):
        _open(book, "T1", "EUR/USD", "LONG", 1.1000, 1.0)
    assert len(book.fills) == 1


def test_trade_id_reuse_after_close_rejected():
    book = A.PositionBook()
    _round_trip(book, "T1", "EUR/USD", "LONG", 1.1000, 1.1550, 1.0)
    with pytest.raises(A.PositionBookError, match="TRADE_ID_REUSED"):
        _open(book, "T1", "EUR/USD", "LONG", 1.1000, 1.0)


def test_double_close_rejected():
    book = A.PositionBook()
    _open(book, "T1", "EUR/USD", "LONG", 1.1000, 1.0)
    book.close_position("T1", 1.1550, ts_utc="2026-01-05T15:00:00+00:00")
    with pytest.raises(A.PositionBookError, match="DOUBLE_CLOSE"):
        book.close_position("T1", 1.1550, ts_utc="2026-01-05T16:00:00+00:00")


def test_close_unknown_id_rejected():
    book = A.PositionBook()
    with pytest.raises(A.PositionBookError, match="UNKNOWN_TRADE_ID"):
        book.close_position("GHOST", 1.1000, ts_utc="2026-01-05T15:00:00+00:00")


@pytest.mark.parametrize("bad", [0.0, -10000.0])
def test_nonpositive_notional_rejected(bad):
    book = A.PositionBook()
    with pytest.raises(A.PositionBookError, match="BAD_NOTIONAL"):
        book.open_position(trade_id="T1", pair="EUR/USD", side="LONG",
                           notional_usd=bad, price=1.1000,
                           ts_utc="2026-01-05T10:00:00+00:00", cost_tier=1.0)


@pytest.mark.parametrize("bad", [0.0, -1.1])
def test_nonpositive_price_rejected(bad):
    book = A.PositionBook()
    with pytest.raises(A.PositionBookError, match="BAD_PRICE"):
        book.open_position(trade_id="T1", pair="EUR/USD", side="LONG",
                           notional_usd=NOTIONAL, price=bad,
                           ts_utc="2026-01-05T10:00:00+00:00", cost_tier=1.0)
    _open(book, "T1", "EUR/USD", "LONG", 1.1000, 1.0)
    with pytest.raises(A.PositionBookError, match="BAD_PRICE"):
        book.close_position("T1", 0.0, ts_utc="2026-01-05T15:00:00+00:00")


def test_bad_side_tier_pair_and_timestamp_rejected():
    book = A.PositionBook()
    with pytest.raises(A.PositionBookError, match="BAD_SIDE"):
        _open(book, "T1", "EUR/USD", "BUY", 1.1000, 1.0)
    with pytest.raises(A.PositionBookError, match="BAD_COST_TIER"):
        _open(book, "T1", "EUR/USD", "LONG", 1.1000, 1.7)
    with pytest.raises(A.PositionBookError, match="BAD_PAIR"):
        _open(book, "T1", "USD", "LONG", 1.1000, 1.0)  # cash is never a pair
    with pytest.raises(ValueError):
        _open(book, "T1", "EUR/USD", "LONG", 1.1000, 1.0, ts="not-a-timestamp")
    assert book.fills == []  # nothing mutated


# --- turnover and trade counts reconcile strictly from fills ---------------------- #
def test_turnover_and_trade_count_reconcile_from_fills():
    book = _golden_book()
    turnover = A.turnover_from_fills(book.fills)
    # 3 entry fills x 10000 + 3 exit fills x 10000
    assert turnover["n_entry_fills"] == 3 and turnover["n_exit_fills"] == 3
    assert turnover["entry_notional_usd"] == 30000.0
    assert turnover["exit_notional_usd"] == 30000.0
    assert turnover["total_notional_usd"] == 60000.0

    trades = A.trades_from_fills(book.fills)
    assert trades["n_fills"] == 6
    assert trades["round_trips"] == 3
    assert trades["open_positions"] == 0
    assert trades["trade_ids_closed"] == ["T1-EURUSD", "T2-USDJPY", "T3-GBPUSD"]
    assert trades["trade_ids_open"] == []
    assert trades["pairs"] == ["EUR/USD", "GBP/USD", "USD/JPY"]
    # cost total reconciles from the same fills: 3.00 + 4.50 + 6.00
    assert book.total_cost_usd == 13.50


def test_open_position_counts_as_open_not_round_trip():
    book = A.PositionBook()
    _open(book, "ONLY", "EUR/USD", "LONG", 1.1000, 1.0)
    trades = A.trades_from_fills(book.fills)
    assert trades["round_trips"] == 0 and trades["open_positions"] == 1
    assert trades["trade_ids_open"] == ["ONLY"]
    turnover = A.turnover_from_fills(book.fills)
    assert turnover["entry_notional_usd"] == 10000.0 and turnover["exit_notional_usd"] == 0.0


def test_malformed_fill_sequences_fail_closed():
    good_entry = A.Fill(trade_id="T1", pair="EUR/USD", side="LONG",
                        notional_usd=NOTIONAL, price=1.1000,
                        ts_utc="2026-01-05T10:00:00+00:00", leg="ENTRY",
                        cost_tier=1.0, cost_usd=1.5)
    orphan_exit = A.Fill(trade_id="T2", pair="EUR/USD", side="LONG",
                         notional_usd=NOTIONAL, price=1.1550,
                         ts_utc="2026-01-05T15:00:00+00:00", leg="EXIT",
                         cost_tier=1.0, cost_usd=1.5)
    with pytest.raises(A.PositionBookError, match="ORPHAN_EXIT"):
        A.trades_from_fills([orphan_exit])
    with pytest.raises(A.PositionBookError, match="DUPLICATE_ENTRY"):
        A.trades_from_fills([good_entry, good_entry])


# --- USD cash exclusion from concentration (V1 convention) ------------------------ #
def test_usd_cash_excluded_and_real_pair_shares_sum_to_one():
    # hand math: positive parts are 500, 150, 100; total 750 (USD's 999
    # excluded). shares: 500/750 = 0.666667, 150/750 = 0.200000,
    # 100/750 = 0.133333 (round 6); 0.666667+0.2+0.133333 = 1.000000.
    pnl_by_pair = {"EUR/USD": 500.0, "USD/JPY": 150.0, "GBP/USD": 100.0,
                   "USD": 999.0}
    shares = A.pair_concentration(pnl_by_pair)
    assert "USD" not in shares                      # cash never a pair
    assert shares == {"EUR/USD": 0.666667, "USD/JPY": 0.2, "GBP/USD": 0.133333}
    assert sum(shares.values()) == pytest.approx(1.0, abs=1e-9)


def test_negative_pair_zero_share_and_denominator_excludes_usd():
    # hand math: GBP/USD loses so its positive part is 0; the denominator is
    # the sum of positive parts of REAL pairs only = 500 + 150 = 650 (GBP's
    # -80 contributes 0; USD's 999 is excluded entirely).
    # shares: 500/650 = 0.769230769... -> 0.769231, 150/650 = 0.230769230...
    # -> 0.230769 (round 6); GBP/USD = 0/650 = 0.0.
    shares = A.pair_concentration({"EUR/USD": 500.0, "USD/JPY": 150.0,
                                   "GBP/USD": -80.0, "USD": 999.0})
    assert "USD" not in shares
    assert shares == {"EUR/USD": 0.769231, "USD/JPY": 0.230769, "GBP/USD": 0.0}


def test_no_positive_pnl_gives_none_shares():
    # V1 parity: total positive part 0 -> every share None
    assert A.pair_concentration({"EUR/USD": -10.0, "USD/JPY": 0.0}) == \
        {"EUR/USD": None, "USD/JPY": None}


# --- canonical digests over exact artifact bytes ----------------------------------- #
RECORD = {"trade_id": "T1-EURUSD", "pair": "EUR/USD", "side": "LONG",
          "notional_usd": 10000.0, "entry": 1.1, "exit": 1.155,
          "pnl_usd": 500.0}


def test_canonical_json_bytes_shape():
    raw = A.canonical_json_bytes(RECORD)
    assert isinstance(raw, bytes)
    assert raw.decode("utf-8") == json.dumps(RECORD, sort_keys=True,
                                             separators=(",", ":"),
                                             ensure_ascii=False)
    # sorted keys: "entry" < "exit" < "notional_usd" < "pair" < "pnl_usd" ...
    assert raw.index(b'"entry"') < raw.index(b'"pair"')


def test_digest_stable_and_byte_sensitive():
    d1 = A.digest_of(RECORD)
    d2 = A.digest_of(dict(RECORD))       # equal content -> same digest
    assert d1 == d2
    assert d1 == hashlib.sha256(A.canonical_json_bytes(RECORD)).hexdigest()
    changed = dict(RECORD, pnl_usd=500.1)  # one character changed: 500.0 -> 500.1
    assert A.canonical_json_bytes(changed) != A.canonical_json_bytes(RECORD)
    assert A.digest_of(changed) != d1    # one changed byte -> different digest
    assert len(d1) == 64


def test_digest_equals_sha256_of_exact_ledger_bytes(tmp_path):
    path = tmp_path / "ledger.jsonl"
    publisher = A.AtomicJsonlPublisher(path)
    observed, published = publisher.publish_once(RECORD)
    assert (observed, published) == (1, 1)
    raw = path.read_bytes()
    lines = [line for line in raw.split(b"\n") if line]
    assert len(lines) == 1
    # the line IS the canonical bytes of the record (plus the newline)
    assert lines[0] == A.canonical_json_bytes(RECORD)
    assert raw == A.canonical_json_bytes(RECORD) + b"\n"
    # therefore the record digest equals sha256 of the exact bytes written
    assert A.digest_of(RECORD) == hashlib.sha256(lines[0]).hexdigest()


# --- once-only publication ---------------------------------------------------------- #
def test_publish_once_is_once_only(tmp_path):
    path = tmp_path / "ledger.jsonl"
    publisher = A.AtomicJsonlPublisher(path)
    assert publisher.publish_once(RECORD) == (1, 1)   # first publish: (1, 1)
    assert publisher.publish_once(RECORD) == (0, 0)   # replay: zero delta no-op
    assert len([l for l in path.read_bytes().split(b"\n") if l]) == 1

    other = dict(RECORD, trade_id="T2-USDJPY")        # different record
    assert publisher.publish_once(other) == (1, 1)    # published exactly once
    assert publisher.publish_once(other) == (0, 0)
    assert publisher.publish_once(RECORD) == (0, 0)
    lines = [l for l in path.read_bytes().split(b"\n") if l]
    assert len(lines) == 2
    assert {hashlib.sha256(l).hexdigest() for l in lines} == \
        {A.digest_of(RECORD), A.digest_of(other)}
    # once-only survives a fresh publisher instance over the same ledger
    assert A.AtomicJsonlPublisher(path).publish_once(RECORD) == (0, 0)
    assert len([l for l in path.read_bytes().split(b"\n") if l]) == 2


def test_parallel_append_serialized_through_one_publisher(tmp_path):
    path = tmp_path / "parallel.jsonl"
    publisher = A.AtomicJsonlPublisher(path)
    n = 8
    barrier = threading.Barrier(n)
    results = {}

    def work(i):
        record = {"writer": i, "tag": f"parallel-record-{i}"}
        barrier.wait()  # maximize contention on the single publisher
        results[i] = (record, publisher.publish_once(record))

    threads = [threading.Thread(target=work, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # every record was published exactly once: (observed_delta=1, published_now=1)
    assert all(r == (1, 1) for _, r in results.values())
    lines = [l for l in path.read_bytes().split(b"\n") if l]
    assert len(lines) == n                                   # exactly 8 lines
    parsed = [json.loads(l) for l in lines]                  # all valid JSON
    assert {p["writer"] for p in parsed} == set(range(n))
    digests = {hashlib.sha256(l).hexdigest() for l in lines}
    assert len(digests) == n                                 # 8 unique digests
    # and each digest is the digest of the exact record bytes
    expected = {A.digest_of(rec) for rec, _ in results.values()}
    assert digests == expected


# --- UNAVAILABLE_FAIL_CLOSED beyond the identity design ------------------------------ #
def test_conversion_beyond_identity_fails_closed():
    # identity path: USD -> USD is the only conversion in the frozen design
    assert A.convert_to_usd_identity(250.0, from_currency="USD") == 250.0
    assert A.convert_to_usd_identity(-104.5) == -104.5
    # any other source currency would require an FX-rate authority that does
    # not exist in this design -> fail closed
    with pytest.raises(A.UnavailableFailClosed, match="UNAVAILABLE_FAIL_CLOSED"):
        A.convert_to_usd_identity(15000.0, from_currency="JPY")
    with pytest.raises(A.UnavailableFailClosed) as exc:
        A.convert_to_usd_identity(1.0, from_currency="EUR")
    assert exc.value.reason == "UNAVAILABLE_FAIL_CLOSED"


def test_close_path_uses_only_the_identity_conversion():
    # the book's PnL path routes through convert_to_usd_identity: the golden
    # numbers are unchanged and no conversion beyond the identity is possible
    book = A.PositionBook()
    closed = _round_trip(book, "T1-EURUSD", "EUR/USD", "LONG", 1.1000, 1.1550, 1.0)
    assert closed.pnl_usd == pytest.approx(500.00, rel=1e-9)
