"""Current snapshot store: latest live datum per symbol (plan §6).

Every datum carries the full contract: provider, symbol, value fields,
provider_timestamp_utc, received_at_utc, age_seconds, status
(HEALTHY|STALE|GAP_DETECTED|RATE_LIMITED|DISCONNECTED|NOT_SUBSCRIBED),
stale_reason, source, surface_state (the FULL 7-state §5 surface
value; DEGRADED/RECOVERing surfaces still serve fresh data as HEALTHY
with surface_state disclosing the transition, while RATE_LIMITED/
DISCONNECTED surfaces force the datum to their own status),
provenance, canonical_current (true iff fresh).

Staleness thresholds [LEAD-FROZEN]: STALE after 10 s without a stream
message; GAP_DETECTED during a detected inter-message gap > 10 s on a
1 s stream; DISCONNECTED while the WS is down and no message > 10 s.
Last-known values ARE served but only with status STALE and
canonical_current: false — an old price is never presented as current.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .timeutils import NowMs, default_now_ms, ms_to_iso_z

PROVIDER = "binance_fapi"
STALE_AFTER_MS = 10_000
GAP_MS = 10_000  # 1 s stream silent for >10 s = gap

DATUM_STATUSES = (
    "HEALTHY",
    "STALE",
    "GAP_DETECTED",
    "RATE_LIMITED",
    "DISCONNECTED",
    "NOT_SUBSCRIBED",
)


@dataclass
class SymbolDatum:
    symbol: str
    mark_price: Optional[float] = None
    index_price: Optional[float] = None
    funding_rate: Optional[float] = None
    next_funding_time_ms: Optional[int] = None
    provider_ts_ms: Optional[int] = None
    received_at_ms: Optional[int] = None
    last_event_e_ms: Optional[int] = None   # venue event time for dedup/order
    gap_flagged: bool = False
    duplicates_seen: int = 0
    out_of_order_seen: int = 0
    message_count: int = 0
    source_kind: str = "ws"  # 'ws' | 'rest' (truth law: label the source)

    def apply_rest_mark(
        self,
        provider_ts_ms: int,
        mark: Optional[float],
        index: Optional[float],
        funding_rate: Optional[float],
        received_at_ms: int,
    ) -> None:
        """Apply one REST premiumIndex observation (plan §4 fallback
        probe path; labeled rest in payloads). Only applies when NEWER
        than the last WS event (no stale overwrite)."""
        if self.last_event_e_ms is not None and provider_ts_ms <= self.last_event_e_ms:
            return
        self.last_event_e_ms = provider_ts_ms
        self.mark_price = mark
        self.index_price = index
        self.funding_rate = funding_rate
        self.provider_ts_ms = provider_ts_ms
        self.received_at_ms = received_at_ms
        self.gap_flagged = False
        self.source_kind = "rest"

    def apply_ws_event(
        self,
        event_e_ms: int,
        mark: Optional[float],
        index: Optional[float],
        funding_rate: Optional[float],
        next_funding_ms: Optional[int],
        received_at_ms: int,
    ) -> str:
        """Apply one WS mark-price event. Returns 'applied'|'duplicate'|
        'out_of_order'."""
        self.message_count += 1
        if self.last_event_e_ms is not None:
            if event_e_ms == self.last_event_e_ms:
                self.duplicates_seen += 1
                return "duplicate"
            if event_e_ms < self.last_event_e_ms:
                self.out_of_order_seen += 1
                return "out_of_order"  # stale replay: not applied
        self.last_event_e_ms = event_e_ms
        self.mark_price = mark
        self.index_price = index
        self.funding_rate = funding_rate
        self.next_funding_time_ms = next_funding_ms
        self.provider_ts_ms = event_e_ms
        self.received_at_ms = received_at_ms
        self.gap_flagged = False
        self.source_kind = "ws"
        return "applied"


class SnapshotStore:
    """Latest live data per symbol + staleness computation."""

    def __init__(
        self,
        now_ms: NowMs = default_now_ms,
        stale_after_ms: int = STALE_AFTER_MS,
    ):
        self.now_ms = now_ms
        self.stale_after_ms = stale_after_ms
        self.data: Dict[str, SymbolDatum] = {}

    def datum(self, symbol: str) -> SymbolDatum:
        if symbol not in self.data:
            self.data[symbol] = SymbolDatum(symbol=symbol)
        return self.data[symbol]

    def mark_gaps(self, symbols: List[str]) -> List[str]:
        """Flag symbols whose stream went silent > GAP_MS (wall-clock
        gap diagnostic — WS carries no venue sequence; plan §4(7))."""
        now = self.now_ms()
        flagged: List[str] = []
        for sym in symbols:
            d = self.data.get(sym)
            if d is None or d.provider_ts_ms is None:
                continue
            if now - d.provider_ts_ms > GAP_MS:
                if not d.gap_flagged:
                    d.gap_flagged = True
                    flagged.append(sym)
        return flagged

    def build_payload(
        self,
        symbol: str,
        surface_state: str,
        ws_connected: bool,
        subscribed: bool = True,
    ) -> Dict[str, Any]:
        """The full §6 datum contract for one symbol."""
        now = self.now_ms()
        d = self.data.get(symbol)
        if d is None or d.received_at_ms is None:
            return {
                "provider": PROVIDER,
                "symbol": symbol,
                "value": None,
                "provider_timestamp_utc": None,
                "received_at_utc": None,
                "age_seconds": None,
                "status": "NOT_SUBSCRIBED" if not subscribed else "STALE",
                "stale_reason": (
                    "not_subscribed" if not subscribed else "no_data_yet"
                ),
                "source": None,
                "surface_state": surface_state,
                "provenance": None,
                "canonical_current": False,
            }
        age_ms = now - d.provider_ts_ms
        age_s = max(0, age_ms / 1000.0)
        if surface_state == "RATE_LIMITED":
            status, reason = "RATE_LIMITED", "upstream rate limited"
        elif not ws_connected:
            status, reason = "DISCONNECTED", "ws disconnected"
        elif d.gap_flagged:
            status, reason = "GAP_DETECTED", "inter-message gap >10s"
        elif age_ms > self.stale_after_ms:
            status, reason = "STALE", f"no stream message for {age_s:.1f}s"
        else:
            status, reason = "HEALTHY", None
        return {
            "provider": PROVIDER,
            "symbol": symbol,
            "value": d.mark_price,
            "mark_price": d.mark_price,
            "index_price": d.index_price,
            "funding_rate": d.funding_rate,
            "next_funding_time_utc": (
                ms_to_iso_z(d.next_funding_time_ms)
                if d.next_funding_time_ms
                else None
            ),
            "provider_timestamp_utc": ms_to_iso_z(d.provider_ts_ms),
            "received_at_utc": ms_to_iso_z(d.received_at_ms),
            "age_seconds": round(age_s, 3),
            "status": status,
            "stale_reason": reason,
            "source": (
                f"{symbol.lower()}@markPrice@1s"
                if getattr(d, "source_kind", "ws") == "ws"
                else "GET /fapi/v1/premiumIndex"
            ),
            "surface_state": surface_state,
            "provenance": (
                "ws_event" if getattr(d, "source_kind", "ws") == "ws"
                else "rest_premium_index"
            ),
            "canonical_current": status == "HEALTHY",
        }

    def stale_symbols(self, symbols: List[str]) -> List[str]:
        out = []
        now = self.now_ms()
        for sym in symbols:
            d = self.data.get(sym)
            if d is None or d.provider_ts_ms is None:
                out.append(sym)
            elif now - d.provider_ts_ms > self.stale_after_ms:
                out.append(sym)
        return out

    def ws_stats(self) -> dict:
        return {
            "duplicates_seen": sum(x.duplicates_seen for x in self.data.values()),
            "out_of_order_seen": sum(
                x.out_of_order_seen for x in self.data.values()
            ),
            "messages_total": sum(
                x.message_count for x in self.data.values()
            ),
        }
