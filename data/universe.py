"""Point-in-time Binance USD-M research universe discovery.

The scanner deliberately stores both accepted and rejected contracts.  This makes
the universe reproducible and prevents a later backtest from silently using only
symbols which survived until the present day.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any
from urllib.request import Request
from urllib.request import urlopen


FAPI_BASE_URL = "https://fapi.binance.com"
TRADFI_UNDERLYING_TYPES = {
    "EQUITY",
    "KR_EQUITY",
    "HK_EQUITY",
    "CN_EQUITY",
    "PREMARKET",
    "COMMODITY",
}


@dataclass(frozen=True)
class UniverseFilters:
    """Liquidity and history gates applied before strategy research."""

    quote_asset: str = "USDT"
    min_onboard_days: int = 365
    min_quote_volume_24h: float = 50_000_000.0
    min_trades_24h: int = 10_000
    include_crypto: bool = True
    include_tradfi: bool = False


def _get_json(path: str, *, base_url: str = FAPI_BASE_URL, timeout: float = 20.0) -> Any:
    request = Request(
        f"{base_url.rstrip('/')}{path}",
        headers={"User-Agent": "my-quantitative-universe/1.0"},
    )
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed API host
        return json.load(response)


def fetch_exchange_snapshot(*, base_url: str = FAPI_BASE_URL) -> tuple[dict, list[dict]]:
    """Fetch the two public endpoints required to construct a USD-M universe."""
    exchange_info = _get_json("/fapi/v1/exchangeInfo", base_url=base_url)
    tickers = _get_json("/fapi/v1/ticker/24hr", base_url=base_url)
    if not isinstance(exchange_info, dict) or not isinstance(tickers, list):
        raise ValueError("Unexpected Binance universe response shape")
    return exchange_info, tickers


def _asset_class(symbol: dict) -> str:
    contract_type = str(symbol.get("contractType", ""))
    underlying_type = str(symbol.get("underlyingType", "")).upper()
    if contract_type == "TRADIFI_PERPETUAL" or underlying_type in TRADFI_UNDERLYING_TYPES:
        return "tradfi"
    return "crypto"


def _cluster(base_asset: str, asset_class: str, underlying_type: str) -> str:
    if asset_class == "tradfi":
        return underlying_type.lower() or "tradfi"
    base = base_asset.upper()
    groups = {
        "crypto_major": {"BTC", "ETH"},
        "layer1": {"BNB", "SOL", "ADA", "AVAX", "SUI", "TRX", "DOT", "NEAR", "APT"},
        "payments": {"XRP", "LTC", "BCH"},
        "meme": {"DOGE", "SHIB", "PEPE", "BONK", "FLOKI"},
        "infrastructure": {"LINK", "FIL", "AR", "GRT"},
    }
    for name, members in groups.items():
        if base in members:
            return name
    return "crypto_other"


def build_universe_snapshot(
    exchange_info: dict,
    tickers: list[dict],
    *,
    filters: UniverseFilters | None = None,
    as_of: datetime | None = None,
) -> dict[str, Any]:
    """Join contract metadata with 24-hour liquidity and apply auditable gates."""
    rules = filters or UniverseFilters()
    captured_at = as_of or datetime.now(timezone.utc)
    if captured_at.tzinfo is None:
        captured_at = captured_at.replace(tzinfo=timezone.utc)
    captured_ms = int(captured_at.timestamp() * 1000)
    ticker_by_symbol = {str(row.get("symbol")): row for row in tickers}

    rows: list[dict[str, Any]] = []
    for raw in exchange_info.get("symbols", []):
        symbol = str(raw.get("symbol", ""))
        ticker = ticker_by_symbol.get(symbol, {})
        onboard_ms = int(raw.get("onboardDate") or captured_ms)
        onboard_days = max(0.0, (captured_ms - onboard_ms) / 86_400_000)
        quote_volume = float(ticker.get("quoteVolume") or 0.0)
        trades = int(ticker.get("count") or 0)
        asset_class = _asset_class(raw)
        contract_type = str(raw.get("contractType", ""))
        underlying_type = str(raw.get("underlyingType", "")).upper()

        reasons: list[str] = []
        if raw.get("status") != "TRADING":
            reasons.append("not_trading")
        if raw.get("quoteAsset") != rules.quote_asset:
            reasons.append("wrong_quote_asset")
        if contract_type not in {"PERPETUAL", "TRADIFI_PERPETUAL"}:
            reasons.append("not_perpetual")
        if asset_class == "crypto" and not rules.include_crypto:
            reasons.append("crypto_disabled")
        if asset_class == "tradfi" and not rules.include_tradfi:
            reasons.append("tradfi_disabled")
        if onboard_days < rules.min_onboard_days:
            reasons.append("insufficient_history")
        if quote_volume < rules.min_quote_volume_24h:
            reasons.append("low_quote_volume")
        if trades < rules.min_trades_24h:
            reasons.append("low_trade_count")

        base_asset = str(raw.get("baseAsset", ""))
        rows.append(
            {
                "symbol": symbol,
                "pair": str(raw.get("pair", symbol)),
                "base_asset": base_asset,
                "quote_asset": str(raw.get("quoteAsset", "")),
                "margin_asset": str(raw.get("marginAsset", "")),
                "contract_type": contract_type,
                "underlying_type": underlying_type,
                "asset_class": asset_class,
                "cluster": _cluster(base_asset, asset_class, underlying_type),
                "status": str(raw.get("status", "")),
                "onboard_date_ms": onboard_ms,
                "onboard_days": round(onboard_days, 2),
                "quote_volume_24h": quote_volume,
                "trade_count_24h": trades,
                "price_change_pct_24h": float(ticker.get("priceChangePercent") or 0.0),
                "eligible": not reasons,
                "rejection_reasons": reasons,
            },
        )

    rows.sort(key=lambda row: (-row["quote_volume_24h"], row["symbol"]))
    eligible = [row for row in rows if row["eligible"]]
    return {
        "schema_version": 1,
        "captured_at": captured_at.isoformat(),
        "source": "Binance USD-M public REST API",
        "filters": asdict(rules),
        "eligible_symbols": [row["symbol"] for row in eligible],
        "eligible_count": len(eligible),
        "total_contracts": len(rows),
        "contracts": rows,
    }


def write_snapshot(snapshot: dict[str, Any], output_path: str | Path) -> Path:
    """Atomically write a snapshot so interrupted scans never leave partial JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(snapshot, handle, indent=2, sort_keys=True)
            handle.write("\n")
        Path(tmp_name).replace(path)
    except Exception:
        Path(tmp_name).unlink(missing_ok=True)
        raise
    return path


def scan_universe(
    *,
    filters: UniverseFilters | None = None,
    output_path: str | Path,
    base_url: str = FAPI_BASE_URL,
) -> dict[str, Any]:
    exchange_info, tickers = fetch_exchange_snapshot(base_url=base_url)
    snapshot = build_universe_snapshot(exchange_info, tickers, filters=filters)
    write_snapshot(snapshot, output_path)
    return snapshot
