"""Time normalization: venue ms epochs <-> ISO-Z strings (plan §6)."""

from __future__ import annotations

import datetime as dt
import time
from typing import Callable

NowMs = Callable[[], int]


def default_now_ms() -> int:
    return int(time.time() * 1000)


def monotonic_ms() -> int:
    return int(time.monotonic() * 1000)


def ms_to_iso_z(moment_ms: int) -> str:
    moment = dt.datetime.fromtimestamp(moment_ms / 1000.0, tz=dt.timezone.utc)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def iso_z_to_ms(text: str) -> int:
    return int(
        dt.datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ")
        .replace(tzinfo=dt.timezone.utc)
        .timestamp()
        * 1000
    )


def now_iso_z(now_ms: NowMs = default_now_ms) -> str:
    return ms_to_iso_z(now_ms())


def parse_http_date_ms(text: str) -> int | None:
    """Parse an HTTP-date Retry-After value to ms; None if unparsable."""
    try:
        moment = dt.datetime.strptime(text.strip(), "%a, %d %b %Y %H:%M:%S GMT")
        return int(moment.replace(tzinfo=dt.timezone.utc).timestamp() * 1000)
    except (ValueError, AttributeError):
        return None
