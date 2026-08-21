"""Parquet data-catalog helpers for the crypto-futures system."""

from __future__ import annotations

from pathlib import Path

from nautilus_trader.adapters.binance.common.types import BinanceBar
from nautilus_trader.model.data import BarType
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.objects import Quantity
from nautilus_trader.persistence.catalog import ParquetDataCatalog


def _normalise_volume_precision(bar: BinanceBar, size_precision: int) -> BinanceBar:
    """Re-quantize a bar's volume to the instrument's size precision.

    Binance klines often carry fewer decimals than the instrument's ``stepSize``
    (e.g. volume "22932.178" vs size precision 4), which the matching engine
    rejects. Normalising on load keeps backtests valid.
    """
    if bar.volume.precision == size_precision:
        return bar
    volume = Quantity.from_str(f"{bar.volume.as_decimal():.{size_precision}f}")
    return BinanceBar(
        bar_type=bar.bar_type,
        open=bar.open,
        high=bar.high,
        low=bar.low,
        close=bar.close,
        volume=volume,
        quote_volume=bar.quote_volume,
        count=bar.count,
        taker_buy_base_volume=bar.taker_buy_base_volume,
        taker_buy_quote_volume=bar.taker_buy_quote_volume,
        ts_event=bar.ts_event,
        ts_init=bar.ts_init,
    )


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
        bars = self._catalog.query(
            data_cls=BinanceBar,
            identifiers=[str(bar_type)],
        )
        if not bars:
            return bars

        parsed = bar_type if isinstance(bar_type, BarType) else BarType.from_str(bar_type)
        instrument = self.instrument(parsed.instrument_id)
        if instrument is None:
            return bars

        size_precision = instrument.size_precision
        return [_normalise_volume_precision(b, size_precision) for b in bars]
