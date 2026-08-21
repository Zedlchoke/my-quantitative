"""Historical-data download pipeline.

Downloads instrument definitions and external bars from Binance (USD-M/COIN-M
perpetual, Testnet/Demo by default) into a local ``ParquetDataCatalog`` for later
backtesting. Supports multiple symbols in one pass.
"""

from __future__ import annotations

import pandas as pd

from nautilus_trader.adapters.binance.common.constants import BINANCE
from nautilus_trader.adapters.binance.common.enums import BinanceAccountType
from nautilus_trader.adapters.binance.common.enums import BinanceEnvironment
from nautilus_trader.adapters.binance.common.types import BinanceBar
from nautilus_trader.adapters.binance.config import BinanceDataClientConfig
from nautilus_trader.adapters.binance.config import BinanceInstrumentProviderConfig
from nautilus_trader.adapters.binance.factories import BinanceLiveDataClientFactory
from nautilus_trader.backtest.node import BacktestNode
from nautilus_trader.model.data import BarType
from nautilus_trader.model.identifiers import ClientId
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.persistence.config import DataCatalogConfig

from config.settings import DataDownloadSettings
from config.settings import MarketSettings


def _binance_account_type(value: str) -> BinanceAccountType:
    try:
        return BinanceAccountType[value]
    except KeyError as exc:
        raise ValueError(f"Invalid Binance account type: {value}") from exc


def _binance_environment(value: str) -> BinanceEnvironment:
    try:
        return BinanceEnvironment[value.upper()]
    except KeyError as exc:
        raise ValueError(f"Invalid Binance environment: {value}") from exc


def download_historical_data(
    market: MarketSettings,
    data: DataDownloadSettings,
    client_id: str = BINANCE,
) -> dict[str, object]:
    """Download instrument + bars for every symbol in ``market.symbols``.

    Returns a summary dict with per-symbol bar counts.
    """
    instrument_ids = [
        InstrumentId.from_str(market.instrument_id(symbol)) for symbol in market.symbols
    ]
    bar_types = [BarType.from_str(market.bar_type(symbol)) for symbol in market.symbols]
    environment = _binance_environment(data.environment)

    provider = BinanceInstrumentProviderConfig(
        load_all=False,
        load_ids=frozenset(instrument_ids),
    )
    data_config = BinanceDataClientConfig(
        account_type=_binance_account_type(market.account_type),
        environment=environment,
        instrument_provider=provider,
    )

    node = BacktestNode(configs=[])
    node.add_data_client_factory(client_id, BinanceLiveDataClientFactory)
    node.setup_download_engine(
        catalog_config=DataCatalogConfig(path=data.catalog_path),
        data_clients={client_id: data_config},
    )

    # The download engine leaves its kernel clock at 0 (so every bar looks
    # "incomplete") and the instrument provider unloaded. Bring both up directly
    # instead of calling connect(), which schedules a background refresh task
    # that cannot run in the synchronous download engine.
    engine = node.get_engine("download")
    engine.kernel.clock.set_time(pd.Timestamp.now("UTC").value)
    bclient = next(
        c for c in engine.kernel.data_engine._clients.values() if str(c.id) == client_id
    )
    bclient._instrument_provider.load_ids(instrument_ids)

    # Register a directly-constructed catalog: `DataCatalogConfig.as_catalog()`
    # percent-encodes spaces in Windows paths and breaks writes.
    engine.kernel.data_engine._catalogs.clear()
    engine.kernel.data_engine.register_catalog(
        ParquetDataCatalog(path=data.catalog_path),
        "catalog_0",
    )

    end = pd.Timestamp(data.end) if data.end else pd.Timestamp.now("UTC")
    start = (
        pd.Timestamp(data.start)
        if data.start
        else end - pd.Timedelta(days=data.lookback_days)
    )

    cid = ClientId(client_id)
    for instrument_id, bar_type in zip(instrument_ids, bar_types, strict=True):
        node.download_data("request_instrument", instrument_id=instrument_id, client_id=cid)
        try:
            node.download_data(
                "request_bars",
                bar_type=bar_type,
                start=start,
                end=end,
                client_id=cid,
            )
        except Exception as exc:  # noqa: BLE001
            # Re-downloading a symbol that already has bars in the catalog raises
            # a "non-disjoint intervals" error; treat it as already-cached.
            if "non-disjoint" in str(exc):
                print(f"  {instrument_id.symbol}: bars already cached, skipping")
                continue
            raise

    catalog = ParquetDataCatalog(path=data.catalog_path)
    per_symbol: dict[str, object] = {}
    for symbol, bar_type in zip(market.symbols, bar_types, strict=True):
        bars = catalog.query(data_cls=BinanceBar, identifiers=[str(bar_type)])
        per_symbol[symbol] = {"bars_written": len(bars), "bar_type": str(bar_type)}

    return {
        "symbols": list(market.symbols),
        "start": str(start),
        "end": str(end),
        "per_symbol": per_symbol,
    }
