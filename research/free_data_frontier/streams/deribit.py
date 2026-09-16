"""Deribit public market-data capture (wss://www.deribit.com/ws/api/v2).

Channels: book.{instrument}.raw, ticker.{instrument}.raw for BTC-PERPETUAL /
ETH-PERPETUAL, plus the volatility-index surface via the public subscription
channel volatility-index (and public/get_volatility_index_data is NOT used —
only stream data in this collector).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base import WsCapture

SOURCE_ID = "deribit_public_ws"
ENDPOINT = "wss://www.deribit.com/ws/api/v2"
INSTRUMENTS = ["BTC-PERPETUAL", "ETH-PERPETUAL"]


class DeribitCapture(WsCapture):
    def __init__(self, raw_path) -> None:
        super().__init__(
            SOURCE_ID,
            ENDPOINT,
            [f"book.{i}.raw" for i in INSTRUMENTS]
            + [f"ticker.{i}.raw" for i in INSTRUMENTS]
            + ["volatility-index"],
            raw_path,
        )
        self._request_id = 100

    def subscribe_messages(self) -> List[Dict[str, Any]]:
        channels = [f"book.{i}.raw" for i in INSTRUMENTS]
        channels += [f"ticker.{i}.raw" for i in INSTRUMENTS]
        channels += ["volatility-index.btc_volatility", "volatility-index.eth_volatility"]
        self._request_id += 1
        return [
            {
                "jsonrpc": "2.0",
                "id": self._request_id,
                "method": "public/subscribe",
                "params": {"channels": channels},
            },
            {"jsonrpc": "2.0", "id": self._request_id + 500, "method": "public/set_heartbeat",
             "params": {"interval": 10}},
        ]

    def classify(self, payload: Dict[str, Any]) -> str:
        params = payload.get("params")
        if isinstance(params, dict):
            channel = params.get("channel")
            if channel:
                name = str(channel)
                if name.startswith("volatility_index") or name.startswith("volatility-index"):
                    return "volatility_index"
                return name.split(".")[0]
        if "method" in payload:
            return f"rpc_{payload.get('method')}"
        if "result" in payload or "error" in payload:
            return "rpc_response"
        if payload.get("type") == "heartbeat" or "test" in payload:
            return "heartbeat"
        return "unknown"

    def sequence_of(self, payload: Dict[str, Any]) -> Optional[int]:
        params = payload.get("params")
        if isinstance(params, dict) and isinstance(params.get("data"), dict):
            change_id = params["data"].get("change_id")
            if isinstance(change_id, int):
                return change_id
        return None
