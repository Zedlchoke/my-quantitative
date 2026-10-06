"""Trade/OHLC classification, 1m->1d session aggregation, settlement vs
trade-price separation.

Rules:
  * trade classification uses only what the DOCS define: trades schema
    action is always 'T'; in mbp-1 only action 'T' records are trades;
    side is the aggressor; flags carry venue data-quality bits. Anything
    finer (venue condition codes not present in the record) is NOT_RUN.
  * bar aggregation 1m -> 1d buckets by SESSION DATE (session.session_date_of),
    with explicit session boundaries; bars whose ts falls in the 16:00-17:00
    maintenance break are rejected (fail-closed, not silently binned).
  * negative prices are preserved exactly (integer nanos arithmetic;
    no log returns anywhere — see futbt.accounting's log tripwire).
  * settlement prices come from statistics stat_type=3 keyed by ts_ref
    trading date, kept SEPARATE from trade-derived closes; preliminary vs
    final handled as revisions (final supersedes preliminary, both kept);
    the `actual` flag carries GLBX stat_flags bit 1 (1 = actual, 0 =
    theoretical; verified against the GLBX.MDP3 spec, see spec.py header).
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from ..taxonomy import PolicyError
from . import spec as S
from .ingest import Bar, ContractRegistry, Statistic, Trade
from .session import session_date_of, utc_to_exchange

NS = 1_000_000_000


class TradeConditionError(PolicyError):
    pass


def classify_trade(t: Trade) -> dict:
    """Explicit, doc-bounded classification of a trades-schema record."""
    if not t.is_trade():
        raise TradeConditionError(
            f"record at ts={t.ts_event} has action {t.action!r}; the trades "
            "schema is defined to carry action 'T' only — this is a schema "
            "surprise, refusing to classify")
    side_ch = t.side if isinstance(t.side, str) else chr(t.side or ord("N"))
    side = {"A": "sell_aggressor", "B": "buy_aggressor",
            "N": "unspecified"}.get(side_ch, "unspecified")
    return {
        "is_trade": True,
        "aggressor": side,
        "flags_last": bool(t.flags & (1 << 7)),
        "price_nanos": t.price,
    }


def _local_hhmm(ts: int) -> tuple[int, int]:
    loc = utc_to_exchange(ts)
    return loc.hour, loc.minute


@dataclass(frozen=True)
class SessionBar:
    raw_symbol: str
    session_date: str
    open: int
    high: int
    low: int
    close: int
    volume: int
    n_bars: int
    first_ts: int
    last_ts: int


def aggregate_1m_to_session(bars_1m: list[Bar], raw_symbol: str
                            ) -> list[SessionBar]:
    """Aggregate 1m bars into one bar per session, boundaries explicit.

    Bars in the 16:00-17:00 CT maintenance break do not belong to any
    session and raise (schema surprise), they are never silently binned."""
    ordered = sorted(bars_1m, key=lambda b: b.ts_event)
    by_session: dict[dt.date, list[Bar]] = {}
    for b in ordered:
        hh, _ = _local_hhmm(b.ts_event)
        if hh == 16:
            raise PolicyError(
                f"1m bar at ts={b.ts_event} falls in the 16:00-17:00 CT "
                "maintenance break — no session assignment; refusing to bin")
        by_session.setdefault(session_date_of(b.ts_event), []).append(b)
    out = []
    for d, day in sorted(by_session.items()):
        out.append(SessionBar(
            raw_symbol=raw_symbol, session_date=d.isoformat(),
            open=day[0].open,
            high=max(b.high for b in day),
            low=min(b.low for b in day),
            close=day[-1].close,
            volume=sum(b.volume for b in day),
            n_bars=len(day), first_ts=day[0].ts_event, last_ts=day[-1].ts_event))
    return out


@dataclass(frozen=True)
class SettlementRecord:
    raw_symbol: str
    session_date: str           # from ts_ref (the trading date it describes)
    published_ts: int
    price: int
    final: bool
    actual: bool                # GLBX stat_flags bit 1: 1=actual, 0=theoretical


def settlement_series(statistics: list[Statistic], registry: ContractRegistry,
                      raw_symbol: str) -> list[SettlementRecord]:
    """Separate SETTLEMENT prices (statistics stat_type=3) from trade data.

    Keyed by ts_ref trading date; publication order preserved so PIT views
    can reconstruct what was known when (preliminary then final).

    ts_ref convention: the reference trading date rendered as a timestamp at
    UTC midnight, so the session date is the UTC date of ts_ref (NOT the
    exchange-local date, which would be the previous calendar day)."""
    ident = registry.require(raw_symbol=raw_symbol)
    rows = [s for s in statistics
            if s.instrument_id == ident.instrument_id
            and s.stat_type == 3
            and s.update_action == 1]        # STAT_UPDATE_NEW
    rows.sort(key=lambda s: (s.ts_ref, s.ts_event))
    out = []
    for s in rows:
        d = dt.datetime.fromtimestamp(s.ts_ref / NS, tz=dt.timezone.utc).date()
        out.append(SettlementRecord(
            raw_symbol=raw_symbol, session_date=d.isoformat(),
            published_ts=s.ts_event, price=s.price,
            final=bool(s.stat_flags & S.STAT_FLAG_FINAL),
            actual=bool(s.stat_flags & S.STAT_FLAG_ACTUAL)))
    return out


@dataclass(frozen=True)
class SettlementVsTrade:
    session_date: str
    trade_close: int
    settlement: int
    diff_nanos: int
    diff_ticks: float
    final: bool


def compare_settlement_vs_trade(session_bars: list[SessionBar],
                                settlements: list[SettlementRecord],
                                tick_nanos: int) -> list[SettlementVsTrade]:
    """Per-session diff (in ticks) of trade close vs FINAL settlement.

    Preliminary settlements never enter the comparison — only final values
    are venue-official. Missing either side -> session skipped from the
    comparison and reported by QA, not fabricated."""
    final_by_date = {s.session_date: s for s in settlements if s.final}
    bars_by_date = {b.session_date: b for b in session_bars}
    out = []
    for d in sorted(set(final_by_date) & set(bars_by_date)):
        b, s = bars_by_date[d], final_by_date[d]
        out.append(SettlementVsTrade(
            session_date=d, trade_close=b.close, settlement=s.price,
            diff_nanos=s.price - b.close,
            diff_ticks=(s.price - b.close) / tick_nanos, final=True))
    return out


def require_no_negative_log(prices: list[int]) -> None:
    """Tripwire: nothing in this adapter may take logs of prices, since CL
    went negative in 2020; any log attempt must hard-fail upstream too."""
    for p in prices:
        if p <= 0:
            raise PolicyError(
                "negative/zero price present (CL April-2020 regime): log "
                "transforms are forbidden on this series")
