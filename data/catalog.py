"""Parquet data-catalog helpers for the crypto-futures system."""

from __future__ import annotations

from pathlib import Path

from nautilus_trader.adapters.binance.common.types import BinanceBar
from nautilus_trader.model.data import BarType
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.persistence.catalog import ParquetDataCatalog


class Catalog:
    """Thin wrapper around ``ParquetDataCatalog`` with the specifics of the
    Binance adapter baked in (bars are stored as ``BinanceBar``)."""

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        # Constructed directly (not via `DataCatalogConfig.as_catalog`) because
        # that path percent-encodes spaces in Windows paths and breaks writes.
        self._catalog = ParquetDataCatalog(path=self.path)

    @property
    def raw(self) -> ParquetDataCatalog:
        return self._catalog

    def instrument(self, instrument_id: str | InstrumentId) -> Instrument | None:
        instruments = self._catalog.instruments(instrument_ids=[str(instrument_id)])
        return instruments[0] if instruments else None

    def bars(self, bar_type: str | BarType) -> list[BinanceBar]:
        return self._catalog.query(
            data_cls=BinanceBar,
            identifiers=[str(bar_type)],
        )
