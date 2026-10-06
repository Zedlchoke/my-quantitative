"""Instrument definitions for the 10-symbol universe.

Provenance of every field is recorded. Two independent sources are used:

  S1  = OBSERVED from IBKR secdef via TWSAPI on 2026-10-02
        (research/control/FUTURES-DATA-10SYMS-V1/S1_IDENTITY.json —
        multiplier/minTick live from the exchange definition; NOT re-derivable
        from raw bars, per the data lane's S9 verifier caveat C4).
  SPECS = PUBLISHED public spec dossier compiled 2026-10-02
        (research/control/FUTURES-DATA-10SYMS-V1/costs/SPECS_MARGINS_PUBLIC_2026-10-02.md;
        NinjaTrader/AMP/Wikipedia/TradingCharts with URLs; official CME pages
        were transport-blocked -> FX outright tick adjudication is NOT_RUN
        against the CME rulebook).

Quote conventions that MUST NOT be assumed away:
  * 6J is quoted USD per JPY (~0.0063, the *inverse* of USDJPY spot ~157).
    Multiplier 12,500,000 JPY; minTick 5e-7 USD/JPY = 6.25 USD per tick.
    No inversion anywhere in accounting: a +1-tick move is +6.25 USD on one
    long contract.
  * SI is the COMEX 5000-oz trading class SI (NOT SIL 1000-oz).
  * 6E/6B/6A are USD per unit of foreign currency (same family convention).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .taxonomy import CostProvenance, Evidence, EvidenceTag, PolicyError

S1_EVIDENCE = Evidence(
    tag=EvidenceTag.OBSERVED,
    script="research/control/FUTURES-DATA-10SYMS-V1/fut10_probe.py (stage identity)",
    window="2026-10-02, IBKR secdef active chains, front contracts of 10 symbols",
    note="multiplier/minTick taken from live secdef; not re-derivable from raw bars",
)

SPECS_EVIDENCE = Evidence(
    tag=EvidenceTag.FACT,
    source="research/control/FUTURES-DATA-10SYMS-V1/costs/SPECS_MARGINS_PUBLIC_2026-10-02.md",
    accessed_utc="2026-10-02",
    note="public broker/mirror sources with URLs; CME rulebook transport-blocked",
)

MONTH_CODES = "FGHJKMNQUVXZ"  # Jan..Dec futures month codes
MONTH_OF_CODE = {c: i + 1 for i, c in enumerate(MONTH_CODES)}


@dataclass(frozen=True)
class MarginQuote:
    maintenance_usd: float
    initial_usd: float
    provenance: CostProvenance
    source: str
    as_of: str
    note: str = ""


@dataclass(frozen=True)
class InstrumentSpec:
    symbol: str
    exchange: str                    # IBKR primary exchange (secdef)
    trading_class: str               # e.g. SI (5000oz), NOT SIL
    contract_unit: str               # human description (PUBLISHED/SPECS)
    multiplier: float                # underlying units per contract (S1)
    min_tick: float                  # minimum price increment (S1)
    quote_convention: str
    currency: str = "USD"            # margin/cash currency; quotes are USD-based
    timezone: str = ""               # timeZoneId from secdef/raw header
    listed_cycle: str = ""           # month codes normally listed
    last_trade_rule: str = ""        # PUBLISHED rule text (SPECS)
    settlement: str = ""             # cash / physical
    fx_tick_conflict_note: str = ""  # non-empty where sources conflict
    evidence: dict = field(default_factory=dict)

    @property
    def tick_value_usd(self) -> float:
        """USD value of one minimum tick on one contract."""
        return self.multiplier * self.min_tick

    def validate(self) -> "InstrumentSpec":
        if self.tick_value_usd <= 0:
            raise PolicyError(f"{self.symbol}: non-positive tick value")
        if self.symbol == "6J":
            # 6J orientation guard: quoted USD per JPY, ~0.0063, never inverted.
            if not (0.001 < 0.0063 < 0.1):
                raise PolicyError("unreachable")
            if abs(self.tick_value_usd - 6.25) > 1e-9:
                raise PolicyError(
                    "6J tick value must be $6.25 (12,500,000 JPY x 5e-7 USD/JPY); "
                    "a different number means someone inverted the quote"
                )
        if self.symbol == "SI" and self.trading_class != "SI":
            raise PolicyError("SI must use 5000oz trading class SI, not SIL 1000oz")
        if self.symbol == "SI" and self.multiplier != 5000:
            raise PolicyError("SI multiplier must be 5000 oz")
        return self


_NT = "https://ninjatrader.com/pricing/margins (as of 2026-08-31)"
_AMP = "https://www.ampfutures.com/trading-info/margins/ (fetched 2026-10-02)"


def _margins(maint: float, init: float, note: str = "") -> MarginQuote:
    return MarginQuote(
        maintenance_usd=maint, initial_usd=init,
        provenance=CostProvenance.PUBLISHED, source=f"NinjaTrader {_NT}; AMP {_AMP}",
        as_of="2026-08-31 / 2026-10-02",
        note=note or "broker-published, within ~2% across the two sources; "
                     "CME SPAN official NOT_RUN (transport-blocked)",
    )


_INSTRUMENTS: dict[str, InstrumentSpec] = {}


def _add(spec: InstrumentSpec) -> None:
    _INSTRUMENTS[spec.symbol] = spec.validate()


_add(InstrumentSpec(
    symbol="NQ", exchange="CME", trading_class="NQ",
    contract_unit="$20 x Nasdaq-100 index",
    multiplier=20, min_tick=0.25,
    quote_convention="index points (USD-denominated)",
    timezone="US/Central", listed_cycle="HMUZ",
    last_trade_rule="3rd Friday of contract month",
    settlement="cash",
))

_add(InstrumentSpec(
    symbol="ES", exchange="CME", trading_class="ES",
    contract_unit="$50 x S&P 500 index",
    multiplier=50, min_tick=0.25,
    quote_convention="index points (USD-denominated)",
    timezone="US/Central", listed_cycle="HMUZ",
    last_trade_rule="3rd Friday of contract month",
    settlement="cash",
))

_add(InstrumentSpec(
    symbol="CL", exchange="NYMEX", trading_class="CL",
    contract_unit="1,000 barrels WTI crude",
    multiplier=1000, min_tick=0.01,
    quote_convention="USD per barrel (CAN BE NEGATIVE — April-2020 style; "
                     "arithmetic PnL only, no log returns)",
    timezone="US/Eastern", listed_cycle="all 12 months",
    last_trade_rule="3 business days before the 25th calendar day of the month "
                    "prior to the contract month",
    settlement="physical (Cushing)",
))

_add(InstrumentSpec(
    symbol="NG", exchange="NYMEX", trading_class="NG",
    contract_unit="10,000 mmBtu natural gas",
    multiplier=10000, min_tick=0.001,
    quote_convention="USD per mmBtu",
    timezone="US/Eastern", listed_cycle="all 12 months",
    last_trade_rule="third last business day of the month prior to contract month",
    settlement="physical (Henry Hub)",
))

_add(InstrumentSpec(
    symbol="GC", exchange="COMEX", trading_class="GC",
    contract_unit="100 troy oz gold",
    multiplier=100, min_tick=0.1,
    quote_convention="USD per troy oz",
    timezone="US/Eastern", listed_cycle="GJMQVZ (+consecutive)",
    last_trade_rule="1:30pm ET third last business day of contract month",
    settlement="physical",
))

_add(InstrumentSpec(
    symbol="SI", exchange="COMEX", trading_class="SI",
    contract_unit="5,000 troy oz silver (tradingClass SI — NOT SIL 1000oz)",
    multiplier=5000, min_tick=0.005,
    quote_convention="USD per troy oz",
    timezone="US/Eastern", listed_cycle="FHKNVZ (+consecutive)",
    last_trade_rule="1:25pm ET third last business day of contract month",
    settlement="physical",
))

_add(InstrumentSpec(
    symbol="6E", exchange="CME", trading_class="6E",
    contract_unit="125,000 EUR",
    multiplier=125000, min_tick=5e-05,
    quote_convention="USD per EUR (inverse of EURUSD spot convention)",
    timezone="US/Central", listed_cycle="HMUZ (+serials listed)",
    last_trade_rule="10:16am ET, 2 business days before 3rd Wednesday of month",
    settlement="physical",
    fx_tick_conflict_note="half-tick (AMP/NT, matches IBKR secdef 5e-05) vs legacy "
                          "full-tick sources; CME rulebook adjudication NOT_RUN",
))

_add(InstrumentSpec(
    symbol="6J", exchange="CME", trading_class="6J",
    contract_unit="12,500,000 JPY",
    multiplier=12500000, min_tick=5e-07,
    quote_convention="USD per JPY (~0.0063 = 1/USDJPY ~157). NOT inverted; "
                     "PnL needs NO USDJPY conversion anywhere.",
    timezone="US/Central", listed_cycle="HMUZ (+serials listed)",
    last_trade_rule="10:16am ET, 2 business days before 3rd Wednesday of month",
    settlement="physical",
    fx_tick_conflict_note="half-tick (AMP/NT, matches IBKR secdef 5e-07 = $6.25) "
                          "vs legacy full-tick; CME rulebook adjudication NOT_RUN",
))

_add(InstrumentSpec(
    symbol="6B", exchange="CME", trading_class="6B",
    contract_unit="62,500 GBP",
    multiplier=62500, min_tick=0.0001,
    quote_convention="USD per GBP",
    timezone="US/Central", listed_cycle="HMUZ (+serials listed)",
    last_trade_rule="2 business days before 3rd Wednesday of contract month",
    settlement="physical",
    fx_tick_conflict_note="0.0001 (AMP/IBKR) vs 0.0002 outright (TK legacy); "
                          "CME rulebook adjudication NOT_RUN",
))

_add(InstrumentSpec(
    symbol="6A", exchange="CME", trading_class="6A",
    contract_unit="100,000 AUD",
    multiplier=100000, min_tick=5e-05,
    quote_convention="USD per AUD",
    timezone="US/Central", listed_cycle="HMUZ (+serials listed)",
    last_trade_rule="2 business days before 3rd Wednesday of contract month",
    settlement="physical",
    fx_tick_conflict_note="0.00005 (AMP/IBKR, $5.00) vs 0.0001 (ITG legacy, $10); "
                          "CME rulebook adjudication NOT_RUN",
))


MARGINS: dict[str, MarginQuote] = {
    "NQ": _margins(42248.33, 46473.17),
    "ES": _margins(26028.77, 28631.65),
    "CL": _margins(8021.09, 8823.20),
    "NG": _margins(2814.83, 3096.32),
    "GC": _margins(22391.00, 24630.10),
    "SI": _margins(33498.00, 36847.80),
    "6E": _margins(2400.00, 2640.00),
    "6J": _margins(2800.00, 3080.00),
    "6B": _margins(2000.00, 2200.00),
    "6A": _margins(1900.00, 2090.00),
}


def get_instrument(symbol: str) -> InstrumentSpec:
    try:
        return _INSTRUMENTS[symbol]
    except KeyError:
        raise KeyError(
            f"no InstrumentSpec for '{symbol}'. Known: {sorted(_INSTRUMENTS)}. "
            "Verify specs per instrument, never assume."
        ) from None


def all_symbols() -> list[str]:
    return sorted(_INSTRUMENTS)


def spec_evidence(symbol: str) -> dict:
    """Provenance bundle for one symbol's static specs."""
    get_instrument(symbol)  # raises on unknown
    return {
        "multiplier_minTick_timeZone": S1_EVIDENCE.to_dict(),
        "unit_cycle_lastTrade margins": SPECS_EVIDENCE.to_dict(),
        "margin_quote": {
            "provenance": MARGINS[symbol].provenance.value,
            "source": MARGINS[symbol].source,
            "as_of": MARGINS[symbol].as_of,
            "note": MARGINS[symbol].note,
            "cme_span_official": "NOT_RUN (CME transport-blocked 2026-10-02)",
        },
    }
