"""WS sequence/gap accounting and stream classifier tests (hermetic)."""

from pathlib import Path

from research.free_data_frontier.streams.base import WsCapture
from research.free_data_frontier.streams.coinbase import CoinbaseCapture
from research.free_data_frontier.streams.deribit import DeribitCapture
from research.free_data_frontier.streams.kraken import KrakenFuturesCapture


class SeqCapture(WsCapture):
    def __init__(self, raw_path):
        super().__init__("test_src", "wss://example", ["ch"], raw_path)

    def classify(self, payload):
        return "ch"

    def sequence_of(self, payload):
        return payload.get("seq")


def test_gap_accounting_counts_jumps(tmp_path):
    capture = SeqCapture(tmp_path / "s.jsonl")
    for seq in (1, 2, 4, 5, 9):
        capture._on_text(f'{{"seq": {seq}}}')
    stats = capture.summary.per_channel["ch"]
    # jumps 2->4 and 5->9 are two gaps
    assert stats.gaps == 2
    assert stats.messages == 5
    assert stats.last_sequence == 9


def test_gap_accounting_no_false_positive_on_first(tmp_path):
    capture = SeqCapture(tmp_path / "s.jsonl")
    capture._on_text('{"seq": 100}')
    assert capture.summary.per_channel["ch"].gaps == 0


def test_capture_summary_jsonl_written_and_hashed(tmp_path):
    capture = SeqCapture(tmp_path / "s.jsonl")

    async def fake_run():
        capture.summary.started_utc = "2026-09-16T00:00:00.000Z"
        capture.raw_path.parent.mkdir(parents=True, exist_ok=True)
        capture._handle = capture.raw_path.open("wb")
        capture._on_text('{"seq": 1}')
        import hashlib

        capture._handle.flush()
        capture._handle.close()
        capture.summary.raw_path = str(capture.raw_path)
        capture.summary.raw_sha256 = hashlib.sha256(capture.raw_path.read_bytes()).hexdigest()
        capture.summary.total_bytes = capture.raw_path.stat().st_size
        capture.summary.ended_utc = "2026-09-16T00:01:00.000Z"
        return capture.summary

    import asyncio

    summary = asyncio.new_event_loop().run_until_complete(fake_run())
    assert Path(summary.raw_path).is_file()
    assert summary.raw_sha256
    assert summary.total_bytes > 0


def test_coinbase_classifier_routes_channels(tmp_path):
    capture = CoinbaseCapture(tmp_path / "c.jsonl")
    assert capture.classify({"channel": "ticker"}) == "ticker"
    assert capture.classify({"channel": "market_trades"}) == "market_trades"
    assert capture.classify({"type": "error", "message": "level2 requires authentication"}) == "error"
    assert capture.classify({}) == "unknown"


def test_coinbase_level2_subscription_sent_and_auth_gated(tmp_path):
    capture = CoinbaseCapture(tmp_path / "c.jsonl")
    channels = [m["channel"] for m in capture.subscribe_messages()]
    assert "level2" in channels  # attempted; server-side auth refusal is recorded
    assert "heartbeats" in channels


def test_kraken_classifier_groups_book_feeds(tmp_path):
    capture = KrakenFuturesCapture(tmp_path / "k.jsonl")
    assert capture.classify({"feed": "book_snapshot", "product_id": "PF_XBTUSD"}) == "book"
    assert capture.classify({"feed": "book_delta", "product_id": "PF_XBTUSD"}) == "book"
    assert capture.classify({"feed": "trade", "product_id": "PF_ETHUSD"}) == "trade"
    assert capture.classify({"feed": "heartbeat"}) == "heartbeat"
    subs = capture.subscribe_messages()
    feeds = [m["feed"] for m in subs]
    assert feeds.count("book") == 1 and "trade" in feeds and "heartbeat" in feeds


def test_deribit_classifier_and_change_id(tmp_path):
    capture = DeribitCapture(tmp_path / "d.jsonl")
    assert capture.classify(
        {"params": {"channel": "book.BTC-PERPETUAL.raw", "data": {"change_id": 7}}}
    ) == "book"
    assert capture.classify(
        {"params": {"channel": "volatility_index.btc_volatility", "data": {}}}
    ) == "volatility_index"
    assert capture.sequence_of(
        {"params": {"channel": "book.BTC-PERPETUAL.raw", "data": {"change_id": 41}}}
    ) == 41
    subs = capture.subscribe_messages()
    assert subs[0]["method"] == "public/subscribe"
    assert any("BTC-PERPETUAL" in ch for ch in subs[0]["params"]["channels"])
