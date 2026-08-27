"""V10P-R G2 blocker BG-3/G15: staged per-symbol funding -> holding-span accrual.

Scope (PLAN.md section ``G2 -- funding, cache and resource authority``):

* Generic loader for STAGED per-symbol funding settlements, delegating the
  on-disk bundle layout to the existing :func:`research.funding_pit.load_funding_bundle`
  (``<bundles_dir>/<SYMBOL>/funding.json``) so the staging convention is reused,
  not reimplemented.
* Symbol-NATIVE settlement cadence. Nothing in this module derives, assumes or
  imputes a uniform 8h cadence: every funding interval used for accrual is
  ``[previous THIS-symbol settlement stamp, this settlement stamp]`` taken from
  the staged rows themselves. When a span touches the FIRST staged stamp of a
  symbol the preceding interval is UNKNOWN and the event is skipped with an
  explicit audit reason instead of guessing a period.
* PIT safety. Each settlement carries a publication instant
  (``publishTimeMs``/``publish_time_ms`` when staged, otherwise the settlement
  stamp itself). A settlement is NEVER applied before it was published:
  ``publish_ns <= observed_through_ns`` is required, where
  ``observed_through_ns`` is the caller's forward simulation clock. A
  settlement staged with a late publication becomes applicable only once the
  simulation clock passes the publication instant, while the CASH impact is
  still stamped at the settlement stamp and only lands inside the holding
  span.
* Sign convention ``LONG_PAYS_POSITIVE_RATE``::

      cashflow = -side_sign * rate * |qty| * mark(settlement) * held_fraction

  side_sign is +1 for long and -1 for short, so a long PAYS a positive rate
  (negative cashflow) and a short RECEIVES it. ``held_fraction`` is the
  fraction of that symbol's native funding interval actually held::

      held_fraction =
          clip((min(stamp, exit) - max(interval_start, entry)) /
               (stamp - interval_start), 0, 1)

  so accrual derives directly from ``rate * notional * held_fraction`` with no
  dependence on any other implementation helper.

Boundary rules (tested in ``tests/test_g2_funding_v10.py``, G15):

* a settlement stamp strictly AFTER ``entry_ns`` and AT-OR-BEFORE ``exit_ns``
  accrues (holder at the settle instant);
* entering exactly AT a stamp does not pay that just-completed epoch;
* exiting exactly AT a stamp pays the full preceding epoch (held_fraction 1);
* nothing accrues outside ``[entry_ns, exit_ns]``;
* nothing accrues before the staged publication instant.

This module owns no production wiring: it does not modify
``research/portfolio_engine.py`` (its union-grid loop stays untouched) nor any
other existing module. Callers wrap their engine around
:meth:`accrue_span`/:func:`accrue_schedule`.
"""

from __future__ import annotations

import math
from bisect import bisect_left
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

__all__ = [
    "APPLIED_EVENT_KIND",
    "PUBLICATION_MODEL",
    "REQUIRED_BUNDLE_KEYS",
    "SIGN_CONVENTION",
    "SKIPPED_BEFORE_OR_AT_ENTRY",
    "SKIPPED_AFTER_EXIT_BOUND",
    "SKIPPED_INVALID_MARK",
    "SKIPPED_NOT_YET_PUBLISHED",
    "SKIPPED_NO_NATIVE_PREDECESSOR",
    "AppliedFundingEvent",
    "FundingSettlementBook",
    "FundingStagingError",
    "HoldingSpan",
    "ScheduleAccrualResult",
    "SkippedFundingEvent",
    "SpanAccrualResult",
    "StagedSettlement",
    "accrue_schedule",
    "accrue_span",
    "load_staged_books",
    "parse_settlement_rows",
    "schedule_result_totals",
    "side_sign_from_qty",
    "spans_from_stepwise_positions",
]

#: Module/schema tag written into derived artifacts.
MODULE_TAG = "v10p.g2.funding.v1"

#: Frozen sign convention. Long pays a positive rate; short receives it.
SIGN_CONVENTION = "LONG_PAYS_POSITIVE_RATE"

#: How the publication instant is derived for a staged row.
PUBLICATION_MODEL = (
    "publish_field_when_present_else_settlement_stamp_ms_epoch_ns"
)

#: Bundle contract inherited from research.funding_pit.load_funding_bundle.
REQUIRED_BUNDLE_KEYS = frozenset({"requested_start_ms", "requested_end_ms", "rows"})

APPLIED_EVENT_KIND = "funding_settlement_payment"

#: Skip-reason codes surfaced (and audited) instead of silently dropping rows.
SKIPPED_NOT_YET_PUBLISHED = "not_yet_published_at_observed_through"
SKIPPED_NO_NATIVE_PREDECESSOR = "no_native_predecessor_interval"
SKIPPED_INVALID_MARK = "mark_unavailable"
SKIPPED_BEFORE_OR_AT_ENTRY = "settlement_not_after_entry"
SKIPPED_OUTSIDE_HOLDING_SPAN = "outside_holding_span"

_NS_PER_MS = 1_000_000


class FundingStagingError(ValueError):
    """Fail-closed staging violation (malformed rows, conflicting stamps...)."""


# --------------------------------------------------------------------------- #
# staged rows
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class StagedSettlement:
    """One staged funding settlement as an observable point-in-time fact."""

    symbol: str
    settlement_ns: int
    rate: float
    publish_ns: int
    source: str | None = None


def _require_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FundingStagingError(
            f"{field_name} must be integer epoch ms, got {value!r}"
        )
    as_float = float(value)
    if not math.isfinite(as_float) or as_float != int(as_float):
        raise FundingStagingError(f"{field_name} must be integral ms, got {value!r}")
    return int(as_float)


def _resolve_publish_ns(row: Mapping[str, Any]) -> int | None:
    for candidate in ("publishTimeMs", "publish_time_ms", "publishTime"):
        if candidate in row and row[candidate] is not None:
            return _require_int(row[candidate], candidate) * _NS_PER_MS
    return None


def parse_settlement_rows(
    symbol: str,
    rows: Sequence[Mapping[str, Any]],
    *,
    source: str | None = None,
) -> list[StagedSettlement]:
    """Validate staged rows into a sorted list of :class:`StagedSettlement`.

    Contract: ``fundingTime`` (epoch ms) and ``fundingRate`` (decimal) follow
    the ``research.funding_pit`` bundle convention. An explicit publication
    field is honoured when present, else publication == settlement stamp.
    Duplicate stamps are collapsed ONLY when their rates agree bit-for-bit;
    disagreeing duplicates raise (fail closed) because the accrual would then
    depend on iteration order.
    """
    out: dict[int, StagedSettlement] = {}
    for i, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise FundingStagingError(
                f"{symbol} row #{i} is not a mapping: {type(row).__name__}"
            )
        stamp_ms = _require_int(row.get("fundingTime"), f"{symbol}[{i}].fundingTime")
        raw_rate = row.get("fundingRate")
        try:
            rate = float(str(raw_rate))
        except (TypeError, ValueError) as exc:
            raise FundingStagingError(
                f"{symbol}[{i}].fundingRate not parseable: {raw_rate!r}"
            ) from exc
        if not math.isfinite(rate):
            raise FundingStagingError(f"{symbol}[{i}].fundingRate not finite: {rate}")
        stamp_ns = stamp_ms * _NS_PER_MS
        publish_ns = _resolve_publish_ns(row)
        item = StagedSettlement(
            symbol=str(symbol),
            settlement_ns=stamp_ns,
            rate=rate,
            publish_ns=publish_ns if publish_ns is not None else stamp_ns,
            source=source,
        )
        prior = out.get(item.settlement_ns)
        if prior is not None:
            if prior.rate != item.rate or prior.publish_ns != item.publish_ns:
                raise FundingStagingError(
                    f"{symbol}: duplicate settlement stamp {item.settlement_ns} "
                    f"with conflicting values "
                    f"(rate {prior.rate} vs {item.rate}) -> fail closed"
                )
            continue
        out[item.settlement_ns] = item
    return [out[ns] for ns in sorted(out)]


# --------------------------------------------------------------------------- #
# loader (delegates bundle layout to research.funding_pit)
# --------------------------------------------------------------------------- #
def load_staged_books(
    bundles_dir: str | Path,
    symbols: Sequence[str] | None = None,
    *,
    require_all: bool = True,
) -> dict[str, "FundingSettlementBook"]:
    """Load one :class:`FundingSettlementBook` per symbol from a staged dir.

    Layout delegation: ``research.funding_pit.load_funding_bundle`` performs the
    read + metadata check, so the V10 staged layout cannot drift away from the
    audited convention. ``symbols=None`` discovers every staged symbol directory
    present under ``bundles_dir``.

    ``require_all=True`` (default) fails closed when a REQUESTED symbol has no
    staged bundle. ``require_all=False`` records an EMPTY book for such symbols
    so callers can proceed explicitly aware of the gap.
    """
    from research.funding_pit import load_funding_bundle

    root = Path(bundles_dir)
    if symbols is None:
        if not root.is_dir():
            raise FundingStagingError(f"bundles_dir not found: {root}")
        targets = sorted(child.name for child in root.iterdir() if child.is_dir())
    else:
        targets = [str(sym) for sym in symbols]
    if not targets:
        raise FundingStagingError("no symbols requested/staged")

    books: dict[str, FundingSettlementBook] = {}
    for sym in targets:
        path = root / sym / "funding.json"
        if not path.exists():
            if require_all:
                raise FundingStagingError(
                    f"missing staged funding bundle for {sym}: {path}"
                )
            books[sym] = FundingSettlementBook(sym, [])
            continue
        payload = load_funding_bundle(root, sym)
        rows = parse_settlement_rows(sym, payload["rows"], source=str(path))
        books[sym] = FundingSettlementBook(sym, rows)
    return books


# --------------------------------------------------------------------------- #
# per-symbol book
# --------------------------------------------------------------------------- #
class FundingSettlementBook:
    """Ascending per-symbol settlement series with PIT-visible lookup.

    Cadence is whatever the staged stamps say: the interval charged at stamp
    ``S_i`` is ``[S_{i-1}, S_i]`` OF THE SAME SYMBOL. No global grid, no 8h
    assumption anywhere.
    """

    def __init__(self, symbol: str, settlements: Sequence[StagedSettlement]) -> None:
        self.symbol = str(symbol)
        items = sorted(settlements, key=lambda s: s.settlement_ns)
        for left, right in zip(items, items[1:]):
            if left.settlement_ns == right.settlement_ns:
                raise FundingStagingError(
                    f"{self.symbol}: duplicate settlement stamp {right.settlement_ns}"
                )
        self._items: tuple[StagedSettlement, ...] = tuple(items)
        self.stamps: tuple[int, ...] = tuple(s.settlement_ns for s in items)
        self.rates: tuple[float, ...] = tuple(s.rate for s in items)
        self.publish_stamps: tuple[int, ...] = tuple(s.publish_ns for s in items)

    @property
    def n_settlements(self) -> int:
        return len(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def native_interval_start(self, index: int) -> int | None:
        """Start of the funding interval settled by ``index`` (this symbol)."""
        if index <= 0 or index >= len(self._items):
            return None
        return self._items[index - 1].settlement_ns

    def count_published_at_or_before(self, observed_through_ns: int) -> int:
        """Number of settlements whose publication the observer already saw."""
        return bisect_left(self.publish_stamps, int(observed_through_ns) + 1)


# --------------------------------------------------------------------------- #
# accrual
# --------------------------------------------------------------------------- #
def side_sign_from_qty(qty_signed: float) -> int:
    """+1 long, -1 short, else raise (zero exposure carries no funding)."""
    qty = float(qty_signed)
    if not math.isfinite(qty):
        raise FundingStagingError(f"qty_signed not finite: {qty_signed!r}")
    if qty > 0:
        return 1
    if qty < 0:
        return -1
    raise FundingStagingError("qty_signed == 0 carries no funding leg")


@dataclass(frozen=True)
class AppliedFundingEvent:
    """A booked funding payment inside a holding span."""

    kind: str
    symbol: str
    settlement_ns: int
    publish_ns: int
    rate: float
    qty_signed: float
    mark_price: float
    notional_usdt: float
    interval_start_ns: int
    interval_end_ns: int
    held_fraction: float
    cashflow_usdt: float
    sign_convention: str

    @staticmethod
    def order_key(event: "AppliedFundingEvent") -> tuple[str, int]:
        return (event.symbol, event.settlement_ns)


@dataclass(frozen=True)
class SkippedFundingEvent:
    """A settlement the span deliberately did NOT book, with the reason."""

    symbol: str
    settlement_ns: int
    publish_ns: int
    rate: float
    reason: str


@dataclass
class SpanAccrualResult:
    """Accrual outcome of ONE holding span for ONE symbol."""

    symbol: str
    entry_ns: int
    exit_ns: int
    qty_signed: float
    side_sign: int
    sign_convention: str
    events: list[AppliedFundingEvent] = field(default_factory=list)
    skipped: list[SkippedFundingEvent] = field(default_factory=list)

    @property
    def total_cashflow_usdt(self) -> float:
        return math.fsum(e.cashflow_usdt for e in self.events)


@dataclass
class ScheduleAccrualResult:
    """Aggregated accrual over a whole execution schedule."""

    events: list[AppliedFundingEvent] = field(default_factory=list)
    skipped: list[SkippedFundingEvent] = field(default_factory=list)
    per_span: list[SpanAccrualResult] = field(default_factory=list)
    sign_convention: str = SIGN_CONVENTION

    @property
    def total_cashflow_usdt(self) -> float:
        return math.fsum(e.cashflow_usdt for e in self.events)

    def cashflow_by_symbol(self) -> dict[str, float]:
        out: dict[str, list[float]] = {}
        for event in self.events:
            out.setdefault(event.symbol, []).append(event.cashflow_usdt)
        return {sym: math.fsum(vals) for sym, vals in sorted(out.items())}


MarkFn = Callable[[str, int], float | None]


def accrue_span(
    book: FundingSettlementBook,
    *,
    entry_ns: int,
    exit_ns: int,
    qty_signed: float,
    mark_fn: MarkFn,
    observed_through_ns: int,
    on_missing_mark: str = "raise",
) -> SpanAccrualResult:
    """Accrue one holding span against one symbol's staged settlement book.

    See the module docstring for the frozen boundary rules. ``on_missing_mark``
    selects the fail-closed behaviour when the mark resolver cannot supply a
    usable price at a due settlement: ``"raise"`` aborts (production-precedent
    behaviour of ``research.portfolio_engine.apply_funding_stamp``), ``"skip"``
    records a ``SkippedFundingEvent`` so callers can report incompleteness.
    """
    if entry_ns > exit_ns:
        raise FundingStagingError(
            f"{book.symbol}: entry_ns {entry_ns} after exit_ns {exit_ns}"
        )
    if on_missing_mark not in ("raise", "skip"):
        raise FundingStagingError(f"unknown on_missing_mark={on_missing_mark!r}")
    side = side_sign_from_qty(qty_signed)
    result = SpanAccrualResult(
        symbol=book.symbol,
        entry_ns=int(entry_ns),
        exit_ns=int(exit_ns),
        qty_signed=float(qty_signed),
        side_sign=side,
        sign_convention=SIGN_CONVENTION,
    )
    for index, item in enumerate(book._items):
        stamp = item.settlement_ns
        if stamp <= entry_ns or stamp > exit_ns:
            # Outside the holding span: nothing booked. A stamp landing EXACTLY
            # on the entry instant is audited explicitly -- entering at the settle
            # stamp means the just-completed epoch was never held.
            if stamp == entry_ns:
                result.skipped.append(
                    SkippedFundingEvent(
                        symbol=item.symbol,
                        settlement_ns=stamp,
                        publish_ns=item.publish_ns,
                        rate=item.rate,
                        reason=SKIPPED_BEFORE_OR_AT_ENTRY,
                    )
                )
            continue
        if item.publish_ns > observed_through_ns:
            result.skipped.append(
                SkippedFundingEvent(
                    symbol=item.symbol,
                    settlement_ns=stamp,
                    publish_ns=item.publish_ns,
                    rate=item.rate,
                    reason=SKIPPED_NOT_YET_PUBLISHED,
                )
            )
            continue
        interval_start = book.native_interval_start(index)
        if interval_start is None:
            result.skipped.append(
                SkippedFundingEvent(
                    symbol=item.symbol,
                    settlement_ns=stamp,
                    publish_ns=item.publish_ns,
                    rate=item.rate,
                    reason=SKIPPED_NO_NATIVE_PREDECESSOR,
                )
            )
            continue
        interval_end = stamp
        lo = max(interval_start, result.entry_ns)
        hi = min(interval_end, result.exit_ns)
        period = interval_end - interval_start
        held_fraction = ((hi - lo) / period) if hi > lo else 0.0
        held_fraction = min(max(held_fraction, 0.0), 1.0)
        mark = mark_fn(book.symbol, stamp)
        if mark is None:
            if on_missing_mark == "raise":
                raise FundingStagingError(
                    f"{book.symbol}: no observable mark at settlement {stamp} "
                    "(fail closed); pass on_missing_mark='skip' to defer"
                )
            result.skipped.append(
                SkippedFundingEvent(
                    symbol=item.symbol,
                    settlement_ns=stamp,
                    publish_ns=item.publish_ns,
                    rate=item.rate,
                    reason=SKIPPED_INVALID_MARK,
                )
            )
            continue
        mark_value = float(mark)
        if not math.isfinite(mark_value) or mark_value <= 0.0:
            if on_missing_mark == "raise":
                raise FundingStagingError(
                    f"{book.symbol}: invalid mark {mark_value} at settlement {stamp}"
                )
            result.skipped.append(
                SkippedFundingEvent(
                    symbol=item.symbol,
                    settlement_ns=stamp,
                    publish_ns=item.publish_ns,
                    rate=item.rate,
                    reason=SKIPPED_INVALID_MARK,
                )
            )
            continue
        notional = abs(result.qty_signed) * mark_value
        cashflow = -side * item.rate * notional * held_fraction
        result.events.append(
            AppliedFundingEvent(
                kind=APPLIED_EVENT_KIND,
                symbol=book.symbol,
                settlement_ns=stamp,
                publish_ns=item.publish_ns,
                rate=item.rate,
                qty_signed=result.qty_signed,
                mark_price=mark_value,
                notional_usdt=notional,
                interval_start_ns=interval_start,
                interval_end_ns=interval_end,
                held_fraction=held_fraction,
                cashflow_usdt=cashflow,
                sign_convention=SIGN_CONVENTION,
            )
        )
    return result


# --------------------------------------------------------------------------- #
# execution-schedule adapters
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class HoldingSpan:
    """One executed holding leg of the schedule (signed quantity)."""

    symbol: str
    entry_ns: int
    exit_ns: int
    qty_signed: float


def accrue_schedule(
    spans: Sequence[HoldingSpan],
    books: Mapping[str, FundingSettlementBook],
    *,
    mark_fn: MarkFn,
    observed_through_ns: int,
    on_missing_mark: str = "raise",
) -> ScheduleAccrualResult:
    """Accrue every schedule leg; totals reconcile by symbol and in aggregate."""
    result = ScheduleAccrualResult()
    for span in spans:
        book = books.get(span.symbol)
        if book is None:
            raise FundingStagingError(
                f"no staged settlement book for scheduled symbol {span.symbol}"
            )
        per_span = accrue_span(
            book,
            entry_ns=span.entry_ns,
            exit_ns=span.exit_ns,
            qty_signed=span.qty_signed,
            mark_fn=mark_fn,
            observed_through_ns=observed_through_ns,
            on_missing_mark=on_missing_mark,
        )
        result.per_span.append(per_span)
        result.events.extend(per_span.events)
        result.skipped.extend(per_span.skipped)
    result.events.sort(key=lambda e: (e.symbol, e.settlement_ns))
    result.skipped.sort(key=lambda s: (s.symbol, s.settlement_ns))
    return result


def schedule_result_totals(
    result: ScheduleAccrualResult,
) -> dict[str, Any]:
    """Flat reconciliation payload for runner/report consumption."""
    return {
        "total_cashflow_usdt": result.total_cashflow_usdt,
        "cashflow_by_symbol": result.cashflow_by_symbol(),
        "applied_events": len(result.events),
        "skipped_events": len(result.skipped),
        "skipped_reasons": {
            reason: sum(1 for s in result.skipped if s.reason == reason)
            for reason in sorted({s.reason for s in result.skipped})
        },
        "sign_convention": result.sign_convention,
    }


def spans_from_stepwise_positions(
    symbol: str,
    points: Sequence[tuple[int, float]],
) -> list[HoldingSpan]:
    """Turn a stepwise ``(ts_ns, qty_signed)`` series into holding spans.

    A change at ``t`` closes the previous span AT ``t`` and opens the new one at
    ``t``. Exiting exactly at a settlement therefore pays the completed epoch
    and the re-entering leg starts fresh with no double charge for the same
    interval (see accrue_span boundary rules). A trailing position spans up to
    the last reported timestamp.
    """
    ordered = [(int(ts), float(qty)) for ts, qty in points]
    for (prev_ts, _), (ts, _) in zip(ordered, ordered[1:]):
        if ts <= prev_ts:
            raise FundingStagingError(
                f"{symbol}: stepwise positions not ascending ({ts} <= {prev_ts})"
            )
    spans: list[HoldingSpan] = []
    current_qty: float | None = None
    current_entry: int | None = None
    for ts, qty in ordered:
        if current_qty is None or qty != current_qty:
            if current_qty not in (None,) and current_qty != 0.0:
                assert current_entry is not None
                spans.append(
                    HoldingSpan(symbol, current_entry, ts, current_qty)
                )
            current_entry = ts
            current_qty = qty
    if current_qty not in (None, 0.0) and current_entry is not None and ordered:
        spans.append(HoldingSpan(symbol, current_entry, ordered[-1][0], current_qty))
    return [s for s in spans if s.exit_ns > s.entry_ns]
