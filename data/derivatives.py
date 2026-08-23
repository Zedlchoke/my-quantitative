"""Binance USD-M funding, open-interest and mark-price research data."""

from __future__ import annotations

import json
from datetime import datetime
from datetime import timezone
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request
from urllib.request import urlopen

from data.universe import FAPI_BASE_URL


_OI_PERIOD_MS = {
    "5m": 5 * 60_000,
    "15m": 15 * 60_000,
    "30m": 30 * 60_000,
    "1h": 60 * 60_000,
    "2h": 2 * 60 * 60_000,
    "4h": 4 * 60 * 60_000,
    "6h": 6 * 60 * 60_000,
    "12h": 12 * 60 * 60_000,
    "1d": 24 * 60 * 60_000,
}


def _request(path: str, params: dict[str, object], *, base_url: str) -> Any:
    url = f"{base_url.rstrip('/')}{path}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "my-quantitative-derivatives/1.0"})
    with urlopen(request, timeout=30.0) as response:  # noqa: S310 - caller-controlled test URL
        return json.load(response)


def fetch_funding_history(
    symbol: str,
    *,
    start_ms: int,
    end_ms: int,
    base_url: str = FAPI_BASE_URL,
) -> list[dict]:
    """Fetch all funding settlements in an inclusive interval."""
    rows: list[dict] = []
    cursor = start_ms
    while cursor <= end_ms:
        page = _request(
            "/fapi/v1/fundingRate",
            {"symbol": symbol, "startTime": cursor, "endTime": end_ms, "limit": 1000},
            base_url=base_url,
        )
        if not page:
            break
        rows.extend(page)
        next_cursor = int(page[-1]["fundingTime"]) + 1
        if next_cursor <= cursor:
            raise RuntimeError("Funding pagination did not advance")
        cursor = next_cursor
        if len(page) < 1000:
            break
    return rows


def fetch_open_interest_history(
    symbol: str,
    *,
    start_ms: int,
    end_ms: int,
    period: str = "15m",
    base_url: str = FAPI_BASE_URL,
) -> list[dict]:
    """Fetch all available OI history in the interval.

    Binance caps each response at 500 rows and retains only a short rolling
    history, so the cursor must advance explicitly to avoid silently returning
    only about five days of 15-minute observations.
    """
    rows: list[dict] = []
    cursor_end = end_ms
    try:
        period_ms = _OI_PERIOD_MS[period]
    except KeyError as exc:
        raise ValueError(f"Unsupported open-interest period: {period}") from exc
    while cursor_end >= start_ms:
        page = _request(
            "/futures/data/openInterestHist",
            {
                "symbol": symbol,
                "period": period,
                "startTime": start_ms,
                "endTime": cursor_end,
                "limit": 500,
            },
            base_url=base_url,
        )
        if not page:
            break
        rows = page + rows
        # This endpoint returns the most recent page ending at ``endTime``.
        # Walk backwards one full bucket from the first returned observation.
        next_end = int(page[0]["timestamp"]) - period_ms
        if next_end >= cursor_end:
            raise RuntimeError("Open-interest pagination did not advance")
        cursor_end = next_end
        if len(page) < 500:
            break
    # Binance can round the requested boundaries to period buckets.
    return [row for row in rows if start_ms <= int(row["timestamp"]) <= end_ms]


def fetch_mark_price_klines(
    symbol: str,
    *,
    start_ms: int,
    end_ms: int,
    interval: str = "15m",
    base_url: str = FAPI_BASE_URL,
) -> list[list]:
    rows: list[list] = []
    cursor = start_ms
    while cursor <= end_ms:
        page = _request(
            "/fapi/v1/markPriceKlines",
            {
                "symbol": symbol,
                "interval": interval,
                "startTime": cursor,
                "endTime": end_ms,
                "limit": 1500,
            },
            base_url=base_url,
        )
        if not page:
            break
        rows.extend(page)
        next_cursor = int(page[-1][0]) + 1
        if next_cursor <= cursor:
            raise RuntimeError("Mark-price pagination did not advance")
        cursor = next_cursor
        if len(page) < 1500:
            break
    return rows


def funding_cashflow(*, side: str, position_notional: Decimal, funding_rate: Decimal) -> Decimal:
    """Funding paid/received at one settlement; negative means an account cost."""
    normalized = side.upper()
    if normalized not in {"LONG", "SHORT"}:
        raise ValueError("side must be LONG or SHORT")
    direction = Decimal("-1") if normalized == "LONG" else Decimal("1")
    return direction * position_notional * funding_rate


def write_derivatives_bundle(
    output_dir: str | Path,
    symbol: str,
    *,
    funding: list[dict],
    open_interest: list[dict],
    mark_price_klines: list[list],
) -> Path:
    path = Path(output_dir) / symbol
    path.mkdir(parents=True, exist_ok=True)
    captured_at = datetime.now(timezone.utc).isoformat()
    payloads = {
        "funding.json": {"captured_at": captured_at, "symbol": symbol, "rows": funding},
        "open_interest.json": {"captured_at": captured_at, "symbol": symbol, "rows": open_interest},
        "mark_price_klines.json": {
            "captured_at": captured_at,
            "symbol": symbol,
            "rows": mark_price_klines,
        },
    }
    for name, payload in payloads.items():
        with (path / name).open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
    return path


def write_funding_history(
    output_dir: str | Path,
    symbol: str,
    *,
    requested_start_ms: int,
    requested_end_ms: int,
    rows: list[dict],
) -> Path:
    """Write a funding-only bundle with explicit requested coverage metadata."""
    path = Path(output_dir) / symbol
    path.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "symbol": symbol,
        "requested_start_ms": requested_start_ms,
        "requested_end_ms": requested_end_ms,
        "rows": rows,
    }
    output = path / "funding.json"
    with output.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    return output
