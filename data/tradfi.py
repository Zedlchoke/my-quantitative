"""TradFi underlying-session gates sourced from Binance's trading schedule."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from typing import Any
from urllib.request import Request
from urllib.request import urlopen

from data.universe import FAPI_BASE_URL


@dataclass(frozen=True)
class TradingSession:
    start_ms: int
    end_ms: int
    session_type: str


class TradfiSessionGate:
    """Fail-closed gate for one Binance TradFi underlying market."""

    def __init__(self, sessions: list[TradingSession], allowed_sessions: tuple[str, ...]) -> None:
        self.sessions = sorted(sessions, key=lambda item: item.start_ms)
        self.allowed_sessions = {value.upper() for value in allowed_sessions}

    @classmethod
    def from_payload(
        cls,
        payload: dict[str, Any],
        *,
        market_type: str,
        allowed_sessions: tuple[str, ...] = ("REGULAR",),
    ) -> "TradfiSessionGate":
        market = payload.get("marketSchedules", {}).get(market_type, {})
        sessions = [
            TradingSession(
                start_ms=int(row["startTime"]),
                end_ms=int(row["endTime"]),
                session_type=str(row["type"]).upper(),
            )
            for row in market.get("sessions", [])
        ]
        return cls(sessions, allowed_sessions)

    def session_at(self, timestamp_ms: int) -> str | None:
        for session in self.sessions:
            if session.start_ms <= timestamp_ms < session.end_ms:
                return session.session_type
        return None

    def allows(self, timestamp_ns: int) -> bool:
        session = self.session_at(timestamp_ns // 1_000_000)
        return session is not None and session in self.allowed_sessions


def fetch_trading_schedule(*, base_url: str = FAPI_BASE_URL) -> dict[str, Any]:
    request = Request(
        f"{base_url.rstrip('/')}/fapi/v1/tradingSchedule",
        headers={"User-Agent": "my-quantitative-tradfi/1.0"},
    )
    with urlopen(request, timeout=20.0) as response:  # noqa: S310 - fixed API host
        payload = json.load(response)
    if not isinstance(payload, dict) or "marketSchedules" not in payload:
        raise ValueError("Unexpected Binance trading-schedule response")
    return payload


def schedule_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "exchange_update_time": payload.get("updateTime"),
        "markets": sorted(payload.get("marketSchedules", {})),
    }
