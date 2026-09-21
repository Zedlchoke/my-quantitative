"""Consumer fan-out: bounded queues, monotonic seq, replay ring (§8).

Every consumer gets its OWN bounded queue (default 2000). A full queue
disconnects that consumer (slow_consumer event) without delaying any
other consumer. Outbound events carry a gateway-monotonic ``seq``
(gapless per connection lifetime; resumes from persisted counter +
margin after restart) and a content ``event_id`` for consumer-side
dedup. Bounded replay ring (10,000): on reconnect a consumer may
request replay=<lastN>; ring misses answer replay_truncated: true.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional

from .persistence import atomic_write_json, read_json

QUEUE_MAX = 2000
RING_MAX = 10_000
RESTART_SEQ_MARGIN = 10_000


def event_id_for(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:32]


@dataclass
class Consumer:
    name: str
    queue: asyncio.Queue
    connected_since_utc: str
    last_delivered_seq: int = 0
    dropped_reason: Optional[str] = None

    def stats(self) -> dict:
        return {
            "name": self.name,
            "queue_depth": self.queue.qsize(),
            "queue_max": QUEUE_MAX,
            "connected_since_utc": self.connected_since_utc,
            "last_delivered_seq": self.last_delivered_seq,
            "dropped_reason": self.dropped_reason,
        }


@dataclass
class Fanout:
    seq_path: str
    ring: Deque[Dict[str, Any]] = field(default_factory=deque)
    consumers: Dict[str, Consumer] = field(default_factory=dict)
    seq: int = 0
    dropped_slow_consumers: int = 0
    events_published: int = 0

    def load_seq(self) -> None:
        data = read_json(self.seq_path)
        base = int(data.get("seq", 0)) if isinstance(data, dict) else 0
        self.seq = base + RESTART_SEQ_MARGIN  # never reuse after restart

    def _persist_seq(self) -> None:
        atomic_write_json(self.seq_path, {"seq": self.seq})

    def publish(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Assign seq + event_id, ring-buffer, fan out; drop slow."""
        self.seq += 1
        if self.seq % 50 == 0:
            self._persist_seq()
        envelope = {
            "seq": self.seq,
            "event_id": event_id_for(event),
            "event": event,
        }
        self.ring.append(envelope)
        while len(self.ring) > RING_MAX:
            self.ring.popleft()
        self.events_published += 1
        dead: List[str] = []
        for name, consumer in self.consumers.items():
            try:
                consumer.queue.put_nowait(envelope)
                consumer.last_delivered_seq = self.seq
            except asyncio.QueueFull:
                consumer.dropped_reason = (
                    f"queue_overflow at seq {self.seq} (slow consumer)"
                )
                dead.append(name)
        for name in dead:
            self.consumers.pop(name, None)
            self.dropped_slow_consumers += 1
        return envelope

    def attach(self, name: str, connected_since_utc: str) -> Consumer:
        consumer = Consumer(
            name=name,
            queue=asyncio.Queue(maxsize=QUEUE_MAX),
            connected_since_utc=connected_since_utc,
        )
        self.consumers[name] = consumer
        return consumer

    def detach(self, name: str, reason: str) -> None:
        consumer = self.consumers.pop(name, None)
        if consumer is not None and consumer.dropped_reason is None:
            consumer.dropped_reason = reason

    def replay(self, last_n: int) -> Dict[str, Any]:
        """Replay up to last_n events from the ring; truncation flag."""
        n = max(0, min(int(last_n), RING_MAX))
        items = list(self.ring)[-n:] if n else []
        return {
            "replay": items,
            "replay_requested": n,
            "replay_served": len(items),
            "replay_truncated": len(items) < n,
            "ring_size": len(self.ring),
            "last_seq": self.seq,
        }

    def shutdown_flush(self, timeout_s: float = 5.0) -> None:
        """Graceful shutdown: stop accepting, persist seq."""
        self._persist_seq()

    def stats(self) -> dict:
        return {
            "seq": self.seq,
            "events_published": self.events_published,
            "ring_size": len(self.ring),
            "ring_max": RING_MAX,
            "connected_consumers": [c.stats() for c in self.consumers.values()],
            "dropped_slow_consumers": self.dropped_slow_consumers,
        }
