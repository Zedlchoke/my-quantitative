"""BID/ASK synchronization: book-time joins, non-simultaneity taxonomy,
crossed/locked quote flagging.

Core honesty rule: a bar-side spread proxy is NOT an executable quote.
Every spread/quote artifact produced here carries a `simultaneity` tag
from the taxonomy below, and `require_executable()` raises unless the
record is an EXACT or BOOK_TIME book-time join within the staleness
threshold. Even then it characterizes the MARKET state, not our fills
(PUBLISHED market state != MEASURED user costs).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..taxonomy import PolicyError
from .ingest import Bar, Quote, Trade

DEFAULT_STALENESS_NS = 1_000_000_000     # 1s: quote older than this = STALE


class Simultaneity(str, Enum):
    EXACT = "EXACT"                # quote and trade share the same book time
    BOOK_TIME = "BOOK_TIME"        # last book state strictly before the trade
    STALE = "STALE"                # book-time lead exceeds the threshold
    NO_QUOTE = "NO_QUOTE"          # no quote at/before the trade
    BAR_PROXY = "BAR_PROXY"        # bar-side proxy, inherently non-simultaneous


class BboState(str, Enum):
    NORMAL = "NORMAL"
    LOCKED = "LOCKED"              # bid == ask
    CROSSED = "CROSSED"            # bid > ask
    UNDEFINED = "UNDEFINED"        # sentinel prices present


@dataclass(frozen=True)
class JoinedTrade:
    trade: Trade
    quote_ts: int | None
    bid_px: int | None
    ask_px: int | None
    simultaneity: Simultaneity
    quote_lead_ns: int | None      # trade.ts_recv - quote.ts_recv (>=0)

    def spread_nanos(self) -> int | None:
        if self.bid_px is None or self.ask_px is None:
            return None
        return self.ask_px - self.bid_px


def classify_bbo(bid: int | None, ask: int | None) -> BboState:
    # UNDEF_PRICE (i64::MAX) is the sentinel for "no price", not a huge
    # positive bid — it must classify UNDEFINED, never CROSSED.
    from . import spec as S
    if (bid is None or ask is None or bid < 0 or ask < 0
            or bid == S.UNDEF_PRICE or ask == S.UNDEF_PRICE):
        return BboState.UNDEFINED
    if bid > ask:
        return BboState.CROSSED
    if bid == ask:
        return BboState.LOCKED
    return BboState.NORMAL


def join_book_time(trades: list[Trade], quotes: list[Quote],
                   staleness_ns: int = DEFAULT_STALENESS_NS
                   ) -> list[JoinedTrade]:
    """As-of join on book time: each trade pairs with the last quote whose
    ts_recv <= trade.ts_recv (the executable state the venue would have
    shown; per docs the TBBO/mbp-1 BBO on a trade record is the book
    immediately BEFORE the trade's effect)."""
    qs = sorted(quotes, key=lambda q: q.ts_recv)
    ts_sorted = sorted(trades, key=lambda t: t.ts_recv)
    out: list[JoinedTrade] = []
    qi = 0
    last = None
    for t in ts_sorted:
        while qi < len(qs) and qs[qi].ts_recv <= t.ts_recv:
            last = qs[qi]
            qi += 1
        if last is None:
            out.append(JoinedTrade(t, None, None, None, Simultaneity.NO_QUOTE, None))
            continue
        lead = t.ts_recv - last.ts_recv
        kind = (Simultaneity.EXACT if lead == 0
                else Simultaneity.BOOK_TIME if lead <= staleness_ns
                else Simultaneity.STALE)
        out.append(JoinedTrade(t, last.ts_recv, last.bid_px, last.ask_px,
                               kind, lead))
    return out


def require_executable(j: JoinedTrade, what: str = "fill path") -> None:
    if j.simultaneity not in (Simultaneity.EXACT, Simultaneity.BOOK_TIME):
        raise PolicyError(
            f"{what}: quote is {j.simultaneity.value} (lead="
            f"{j.quote_lead_ns}ns) — not an executable quote; bar-side or "
            "stale proxies must never fill")
    if classify_bbo(j.bid_px, j.ask_px) is not BboState.NORMAL:
        raise PolicyError(
            f"{what}: BBO is {classify_bbo(j.bid_px, j.ask_px).value}; "
            "crossed/locked books are not fillable states")


@dataclass(frozen=True)
class BarSpreadProxy:
    """Per-bar BBO proxy built from bars (close) + as-of quotes. Carries
    the non-simultaneity taxonomy — always BAR_PROXY regardless of data
    density, because a bar close is an interval aggregate, not a quote."""
    bar: Bar
    bid_px: int | None
    ask_px: int | None
    simultaneity: Simultaneity
    bbo_state: BboState
    quote_lead_ns: int | None

    def spread_nanos(self) -> int | None:
        if self.bid_px is None or self.ask_px is None:
            return None
        return self.ask_px - self.bid_px


def bar_spread_proxy(bars: list[Bar], quotes: list[Quote],
                     staleness_ns: int = DEFAULT_STALENESS_NS
                     ) -> list[BarSpreadProxy]:
    qs = sorted(quotes, key=lambda q: q.ts_recv)
    out = []
    for b in sorted(bars, key=lambda b: b.ts_event):
        # bar END = start + 1 interval minute; quote as-of bar end
        bar_end = b.ts_event + 60_000_000_000
        last = None
        for q in qs:
            if q.ts_recv <= bar_end:
                last = q
            else:
                break
        if last is None:
            out.append(BarSpreadProxy(b, None, None, Simultaneity.BAR_PROXY,
                                      BboState.UNDEFINED, None))
        else:
            lead = bar_end - last.ts_recv
            out.append(BarSpreadProxy(
                b, last.bid_px, last.ask_px, Simultaneity.BAR_PROXY,
                classify_bbo(last.bid_px, last.ask_px), lead))
    return out


def crossed_quote_stats(quotes: list[Quote]) -> dict:
    counts = {s.value: 0 for s in BboState}
    examples: dict[str, int] = {}
    for q in quotes:
        st = classify_bbo(q.bid_px, q.ask_px)
        counts[st.value] += 1
        if st in (BboState.CROSSED, BboState.LOCKED):
            examples.setdefault(st.value, q.ts_recv)
    total = len(quotes)
    return {
        "n_quotes": total,
        **counts,
        "crossed_locked_fraction": (
            (counts["CROSSED"] + counts["LOCKED"]) / total if total else 0.0),
        "first_example_ts": examples,
    }
