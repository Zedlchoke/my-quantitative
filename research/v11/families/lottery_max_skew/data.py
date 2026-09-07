"""Read-only loaders for the staged snapshot (catalog_live_crypto +
funding_data/scan_2026) feeding the LOT family plugins.

The staged snapshot is READ-ONLY: nothing here writes, downloads, mutates or
caches to disk.  Reads are retried with a byte-level ``BytesIO`` fallback
because concurrent sibling lanes intermittently make whole-file reads fail
with ``OSError(EOVERFLOW)`` on this host; a retry never changes bytes.
"""

from __future__ import annotations

import io
import json
import time
from pathlib import Path
from typing import Optional, Sequence

import pyarrow.parquet as pq

from research.adapter_v10.protocol import SettlementPoint
from research.v11.families.lottery_max_skew.plugin import BarEvent, MarketInputs
from research.v11.families.lottery_max_skew.strategy import DailyFrame, aggregate_daily

#: Staged snapshot roots (read-only; frozen staging amendments A1).
DEFAULT_CATALOG_ROOT = Path("/Users/hoangminhlong/my-quantitative/catalog_live_crypto")
DEFAULT_FUNDING_ROOT = Path("/Users/hoangminhlong/my-quantitative/funding_data/scan_2026")

BAR_DIR_SUFFIX = "-15-MINUTE-LAST-EXTERNAL"
PERP_SUFFIX = "-PERP.BINANCE"
#: The catalog stores 128-bit scaled decimals (raw int scaled by 1e16).
PRICE_SCALE = 10**16
_MS_TO_NS = 1_000_000


def _read_parquet(path: Path, attempts: int = 10):
    """Robust whole-file parquet read (retry + byte-level fallback)."""
    last: Exception = RuntimeError("unreachable")
    for attempt in range(attempts):
        try:
            return pq.read_table([str(path)])
        except OSError as exc:  # intermittent EOVERFLOW under sibling load
            last = exc
            time.sleep(0.25 * (attempt + 1))
        except Exception:
            raise
    for attempt in range(attempts):
        try:
            raw = open(path, "rb").read()
            return pq.ParquetFile(io.BytesIO(raw)).read()
        except OSError as exc:
            last = exc
            time.sleep(0.25 * (attempt + 1))
    raise last


def staged_symbol_names(catalog_root: Path = DEFAULT_CATALOG_ROOT) -> list[str]:
    """Staged 15m-bar instrument ids (e.g. ``BTCUSDT-PERP.BINANCE``)."""
    root = Path(catalog_root) / "data" / "binance_bar"
    names = sorted(
        p.name[: -len(BAR_DIR_SUFFIX)]
        for p in root.iterdir()
        if p.name.endswith(BAR_DIR_SUFFIX)
    )
    if not names:
        raise RuntimeError(f"no staged bar directories under {root}")
    return names


def _load_bars(instrument_id: str, catalog_root: Path) -> tuple[list[BarEvent], list[float]]:
    """Merge EVERY staged parquet shard of the instrument (a symbol may be
    staged as several date-ranged shards; reading only the first would
    silently truncate its history and fake a delisting).  Rows are sorted by
    close stamp and exact-duplicate stamps are dropped deterministically
    (first shard wins), so the merge is a pure function of the shard set."""
    directory = (
        Path(catalog_root) / "data" / "binance_bar" / f"{instrument_id}{BAR_DIR_SUFFIX}"
    )
    files = sorted(directory.rglob("*.parquet"))
    if not files:
        raise RuntimeError(f"no staged parquet under {directory}")
    rows: list[tuple[int, float, float, float]] = []
    for path in files:
        table = _read_parquet(path)
        ts = table.column("ts_event").to_pylist()
        opens = table.column("open").to_pylist()
        closes = table.column("close").to_pylist()
        qv = table.column("quote_volume").to_pylist()
        rows.extend(
            (
                int(ts[i]),
                float(int.from_bytes(opens[i], "little", signed=True)) / PRICE_SCALE,
                float(int.from_bytes(closes[i], "little", signed=True)) / PRICE_SCALE,
                float(qv[i]),
            )
            for i in range(len(ts))
        )
    rows.sort(key=lambda r: r[0])
    bars: list[BarEvent] = []
    quote_volumes: list[float] = []
    previous: Optional[int] = None
    for ts_event_ns, open_px, close_px, quote_volume in rows:
        if previous is not None and ts_event_ns == previous:
            continue  # deterministic dedupe of an overlapping shard seam
        previous = ts_event_ns
        bars.append(
            BarEvent(ts_event_ns=ts_event_ns, open=open_px, close=close_px)
        )
        quote_volumes.append(quote_volume)
    return bars, quote_volumes


def load_market_inputs(
    *,
    catalog_root: Path = DEFAULT_CATALOG_ROOT,
    funding_root: Path = DEFAULT_FUNDING_ROOT,
) -> MarketInputs:
    """Load the read-only staged snapshot into injectable market inputs.

    Returns daily frames, 15m bar events, native funding settlements and
    instrument tick sizes for the full staged cohort (BTCUSDT included: it is
    the benchmark context leg, excluded from every tradeable book).
    """
    catalog_root = Path(catalog_root)
    funding_root = Path(funding_root)
    daily_by_symbol: dict[str, DailyFrame] = {}
    bars_by_symbol: dict[str, list[BarEvent]] = {}
    settlements_by_symbol: dict[str, tuple[SettlementPoint, ...]] = {}
    tick_sizes: dict[str, float] = {}
    symbols: list[str] = []

    for instrument_id in staged_symbol_names(catalog_root):
        bars, quote_volumes = _load_bars(instrument_id, catalog_root)
        enriched = [
            {
                "ts_event_ns": bar.ts_event_ns,
                "close": bar.close,
                "quote_volume": quote_volumes[i],
            }
            for i, bar in enumerate(bars)
        ]
        daily_by_symbol[instrument_id] = aggregate_daily(enriched)
        bars_by_symbol[instrument_id] = bars
        symbols.append(instrument_id)

    settlements_by_symbol.update(load_funding_settlements(funding_root, symbols))
    tick_sizes.update(load_tick_sizes(catalog_root, symbols))
    missing = sorted(set(symbols) - set(settlements_by_symbol))
    if missing:
        raise RuntimeError(f"no staged funding.json for {missing}")
    return MarketInputs(
        daily_by_symbol=daily_by_symbol,
        bars_by_symbol=bars_by_symbol,
        settlements_by_symbol=settlements_by_symbol,
        tick_sizes=tick_sizes,
        symbols=symbols,
    )


BENCH_ID = "BTCUSDT-PERP.BINANCE"


def load_funding_settlements(
    funding_root: Path = DEFAULT_FUNDING_ROOT, symbols: Sequence[str] | None = None
) -> dict[str, tuple[SettlementPoint, ...]]:
    """Native funding rows -> per-instrument PIT settlement points."""
    funding_root = Path(funding_root)
    out: dict[str, tuple[SettlementPoint, ...]] = {}
    for instrument_id in symbols or sorted(
        p.name + PERP_SUFFIX for p in funding_root.iterdir() if (p / "funding.json").exists()
    ):
        base = instrument_id[: -len(PERP_SUFFIX)]
        path = funding_root / base / "funding.json"
        if not path.exists():
            continue
        doc = json.loads(path.read_text())
        rows = sorted(doc["rows"], key=lambda r: int(r["fundingTime"]))
        out[instrument_id] = tuple(
            SettlementPoint(
                publish_ts_ns=int(row["fundingTime"]) * _MS_TO_NS,
                value=float(row["fundingRate"]),
            )
            for row in rows
        )
    return out


def load_tick_sizes(
    catalog_root: Path = DEFAULT_CATALOG_ROOT, symbols: Sequence[str] | None = None
) -> dict[str, float]:
    """Instrument-def price increments (tick sizes) for the staged cohort."""
    root = Path(catalog_root) / "data" / "crypto_perpetual"
    out: dict[str, float] = {}
    for directory in sorted(root.iterdir()):
        instrument_id = directory.name
        if symbols is not None and instrument_id not in symbols:
            continue
        files = sorted(directory.rglob("*.parquet"))
        if not files:
            continue
        table = _read_parquet(files[0])
        row = table.to_pylist()[0]
        out[instrument_id] = float(row["price_increment"])
    return out


_CACHED: dict[str, MarketInputs] = {}


def get_cached_market_inputs(
    *,
    catalog_root: Path = DEFAULT_CATALOG_ROOT,
    funding_root: Path = DEFAULT_FUNDING_ROOT,
) -> MarketInputs:
    """Process-wide cached load (tests/artifact scripts share one read)."""
    key = f"{catalog_root}|{funding_root}"
    if key not in _CACHED:
        _CACHED[key] = load_market_inputs(
            catalog_root=catalog_root, funding_root=funding_root
        )
    return _CACHED[key]


__all__ = [
    "BENCH_ID",
    "DEFAULT_CATALOG_ROOT",
    "DEFAULT_FUNDING_ROOT",
    "PERP_SUFFIX",
    "PRICE_SCALE",
    "get_cached_market_inputs",
    "load_funding_settlements",
    "load_market_inputs",
    "load_tick_sizes",
    "staged_symbol_names",
]
