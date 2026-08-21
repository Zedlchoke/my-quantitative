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
    """Fetch OI history; Binance only retains this endpoint for about one month."""
    return _request(
        "/futures/data/openInterestHist",
        {
            "symbol": symbol,
            "period": period,
            "startTime": start_ms,
            "endTime": end_ms,
            "limit": 500,
        },
        base_url=base_url,
    )


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
