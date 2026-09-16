"""Bounded public WebSocket capture: shared async capture engine.

Sequence/gap accounting per channel; per-message client receive timestamps;
disconnect/reconnect metrics. Captured samples are prospective history that
starts when the collector runs — they never imply historical coverage.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


@dataclass
class ChannelStats:
    messages: int = 0
    gaps: int = 0
    last_sequence: Optional[int] = None
    first_recv_utc: Optional[str] = None
    last_recv_utc: Optional[str] = None
    bytes: int = 0


@dataclass
class CaptureSummary:
    source_id: str
    endpoint: str
    channels: List[str]
    started_utc: str = ""
    ended_utc: str = ""
    connect_ok: bool = False
    connect_error: Optional[str] = None
    subscriptions: Dict[str, str] = field(default_factory=dict)  # channel -> ack/err
    disconnects: int = 0
    total_messages: int = 0
    total_bytes: int = 0
    per_channel: Dict[str, ChannelStats] = field(default_factory=dict)
    raw_path: Optional[str] = None
    raw_sha256: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "endpoint": self.endpoint,
            "channels": self.channels,
            "started_utc": self.started_utc,
            "ended_utc": self.ended_utc,
            "connect_ok": self.connect_ok,
            "connect_error": self.connect_error,
            "subscriptions": self.subscriptions,
            "disconnects": self.disconnects,
            "total_messages": self.total_messages,
            "total_bytes": self.total_bytes,
            "per_channel": {
                name: {
                    "messages": stats.messages,
                    "gaps": stats.gaps,
                    "last_sequence": stats.last_sequence,
                    "first_recv_utc": stats.first_recv_utc,
                    "last_recv_utc": stats.last_recv_utc,
                    "bytes": stats.bytes,
                }
                for name, stats in self.per_channel.items()
            },
            "raw_path": self.raw_path,
            "raw_sha256": self.raw_sha256,
        }


class WsCapture:
    """One bounded capture session over one endpoint.

    Subclass hooks: subscribe_messages(), classify(payload), sequence_of().
    Writes raw JSONL: one line per message = {"recv_utc", "channel", "seq",
    "payload"}. Gap accounting: sequence regressions or jumps > 1 count as
    gaps for channels that expose a numeric sequence.
    """

    def __init__(
        self,
        source_id: str,
        endpoint: str,
        channels: List[str],
        raw_path: Path,
        max_bytes: int = 256 * 1024 * 1024,
    ) -> None:
        self.summary = CaptureSummary(
            source_id=source_id, endpoint=endpoint, channels=channels
        )
        self.raw_path = raw_path
        self.max_bytes = max_bytes
        self._handle = None
        self._sha = __import__("hashlib").sha256()

    async def run(self, minutes: float) -> CaptureSummary:
        import hashlib

        self.raw_path.parent.mkdir(parents=True, exist_ok=True)
        self.summary.started_utc = now_iso()
        deadline = asyncio.get_event_loop().time() + minutes * 60.0
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(
                    self.summary.endpoint,
                    heartbeat=20,
                    timeout=aiohttp.ClientWSTimeout(ws_close=10),
                    max_msg_size=8 * 1024 * 1024,
                ) as ws:
                    self.summary.connect_ok = True
                    self._handle = self.raw_path.open("wb")
                    for message in self.subscribe_messages():
                        await ws.send_str(json.dumps(message))
                    while asyncio.get_event_loop().time() < deadline:
                        remaining = deadline - asyncio.get_event_loop().time()
                        try:
                            msg = await asyncio.wait_for(ws.receive(), timeout=max(remaining, 0.1))
                        except asyncio.TimeoutError:
                            break
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            self._on_text(msg.data)
                        elif msg.type == aiohttp.WSMsgType.BINARY:
                            self._on_text(msg.data.decode("utf-8", errors="replace"))
                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            self.summary.disconnects += 1
                            break
        except Exception as exc:  # network/DNS/TLS failures recorded, not raised
            self.summary.connect_error = f"{type(exc).__name__}: {exc}"[:300]
            self.summary.connect_ok = False
        finally:
            if self._handle is not None:
                self._handle.flush()
                self._handle.close()
                digest = hashlib.sha256(self.raw_path.read_bytes()).hexdigest()
                self.summary.raw_path = str(self.raw_path)
                self.summary.raw_sha256 = digest
                self.summary.total_bytes = self.raw_path.stat().st_size
        self.summary.ended_utc = now_iso()
        return self.summary

    def _on_text(self, text: str) -> None:
        try:
            payload = json.loads(text)
        except ValueError:
            payload = {"unparsed": text[:200]}
        channel = self.classify(payload)
        stats = self.summary.per_channel.setdefault(channel, ChannelStats())
        seq = self.sequence_of(payload)
        if seq is not None and stats.last_sequence is not None:
            if self.is_gap(stats.last_sequence, seq):
                stats.gaps += 1
        if seq is not None:
            stats.last_sequence = seq
        stats.messages += 1
        stats.bytes += len(text)
        if stats.first_recv_utc is None:
            stats.first_recv_utc = now_iso()
        stats.last_recv_utc = now_iso()
        self.summary.total_messages += 1
        if self._handle is not None:
            line = json.dumps(
                {"recv_utc": now_iso(), "channel": channel, "seq": seq, "payload": payload},
                separators=(",", ":"),
            ).encode("utf-8")
            self._handle.write(line + b"\n")

    # -- subclass hooks -------------------------------------------------
    def is_gap(self, previous: int, current: int) -> bool:
        """Default continuity rule: next must be previous+1. Subclasses may
        override for sequence spaces with different semantics (e.g. Deribit
        change_id is a global monotonic counter — only regressions are gaps)."""
        return current != previous + 1

    def subscribe_messages(self) -> List[Dict[str, Any]]:
        return []

    def classify(self, payload: Dict[str, Any]) -> str:
        return "unknown"

    def sequence_of(self, payload: Dict[str, Any]) -> Optional[int]:
        return None
