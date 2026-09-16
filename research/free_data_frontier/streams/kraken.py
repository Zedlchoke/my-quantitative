"""Kraken Futures public WebSocket capture (wss://futures.kraken.com/ws/v1).

Feeds: ticker, trade, book (snapshot + delta with crc continuity), heartbeat
for PF_XBTUSD and PF_ETHUSD.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base import WsCapture

SOURCE_ID = "kraken_futures_ws"
ENDPOINT = "wss://futures.kraken.com/ws/v1"
PRODUCTS = ["PF_XBTUSD", "PF_ETHUSD"]


class KrakenFuturesCapture(WsCapture):
    def __init__(self, raw_path) -> None:
        super().__init__(SOURCE_ID, ENDPOINT, ["ticker", "trade", "book", "heartbeat"], raw_path)

    def subscribe_messages(self) -> List[Dict[str, Any]]:
        # MEASURED wire format: Futures v1 rejects {"op": ...} with
        # "Bad websocket message"; {"event": "subscribe"} is accepted.
        return [
            {"event": "subscribe", "feed": "ticker", "product_ids": PRODUCTS},
            {"event": "subscribe", "feed": "trade", "product_ids": PRODUCTS},
            {"event": "subscribe", "feed": "book", "product_ids": PRODUCTS},
            {"event": "subscribe", "feed": "heartbeat"},
        ]

    def classify(self, payload: Dict[str, Any]) -> str:
        feed = payload.get("feed")
        if feed:
            name = str(feed)
            # book_snapshot / book_delta both belong to the book channel.
            if name.startswith("book"):
                return "book"
            return name
        if "event" in payload:
            return f"event_{payload.get('event')}"
        return "unknown"

    def sequence_of(self, payload: Dict[str, Any]) -> Optional[int]:
        # Kraken Futures book deltas carry a crc32 checksum; snapshot clears
        # continuity. Use message time as gap-free; crc continuity is judged
        # at analysis time, not capture time.
        return None
