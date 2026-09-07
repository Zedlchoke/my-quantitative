"""Offline fixtures for adapter tests: no network, no wall-clock time."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from research.data_fusion.adapters.base import RawResponse, RequestSpec

FIXTURES = Path(__file__).parent / "fixtures"
UTC = timezone.utc

# Fixed retrieval instant keeps every adapter output deterministic.
RETRIEVED_TIME = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


def fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def fixture_text(name: str) -> str:
    return fixture_bytes(name).decode("utf-8")


def response_for(
    request: RequestSpec,
    body: bytes,
    *,
    content_type: str = "application/json",
    status: int = 200,
    reason: str = "OK",
    retrieved_time_utc: datetime | None = None,
) -> RawResponse:
    return RawResponse(
        request_id=request.request_id(),
        url=request.full_url(),
        status=status,
        reason=reason,
        headers=(("content-type", content_type),),
        body=body,
        retrieved_time_utc=retrieved_time_utc or RETRIEVED_TIME,
    )


class OfflineTransport:
    """Returns recorded fixture bytes; performs no network I/O."""

    def __init__(self, payload: bytes, *, content_type: str = "application/json") -> None:
        self.payload = payload
        self.content_type = content_type
        self.requested: list[RequestSpec] = []

    def fetch(self, request: RequestSpec, retrieved_time_utc: datetime) -> RawResponse:
        self.requested.append(request)
        return response_for(
            request, self.payload, content_type=self.content_type, retrieved_time_utc=retrieved_time_utc
        )


@pytest.fixture
def retrieved_time() -> datetime:
    return RETRIEVED_TIME
