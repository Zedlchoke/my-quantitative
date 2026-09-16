"""Coinbase Advanced Trade public WebSocket capture (BTC-USD, ETH-USD).

Public channels used: ticker, market_trades, heartbeats. The level2 channel
on advanced-trade requires authenticated JWT; an auth error from the server
is recorded as a measured fact (channel blocked, not source blocked).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base import WsCapture

SOURCE_ID = "coinbase_advanced_trade_ws"
ENDPOINT = "wss://advanced-trade-ws.coinbase.com"
PRODUCTS = ["BTC-USD", "ETH-USD"]
PUBLIC_CHANNELS = ["ticker", "market_trades", "heartbeats"]
AUTH_GATED_CHANNELS = ["level2"]


class CoinbaseCapture(WsCapture):
    def __init__(self, raw_path) -> None:
        super().__init__(SOURCE_ID, ENDPOINT, PUBLIC_CHANNELS + AUTH_GATED_CHANNELS, raw_path)

    def subscribe_messages(self) -> List[Dict[str, Any]]:
        messages = []
        for channel in PUBLIC_CHANNELS + AUTH_GATED_CHANNELS:
            messages.append({
                "type": "subscribe",
                "product_ids": PRODUCTS,
                "channel": channel,
            })
        return messages

    def classify(self, payload: Dict[str, Any]) -> str:
        channel = payload.get("channel")
        if channel:
            return str(channel)
        if "type" in payload and payload.get("type") in ("subscriptions", "error"):
            return str(payload.get("type"))
        return "unknown"

    def sequence_of(self, payload: Dict[str, Any]) -> Optional[int]:
        events = payload.get("events")
        if isinstance(events, list) and events:
            seq = events[0].get("sequence_num")
            if isinstance(seq, int):
                return seq
        return None
