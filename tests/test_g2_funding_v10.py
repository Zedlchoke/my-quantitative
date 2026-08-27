"""V10P-R G2 blockers BG-3 + G15: staged funding accrual, independently reconciled.

G15 discipline: every expected number below is HAND COMPUTED here from
``rate * notional * held_fraction`` with literal operands, WITHOUT importing any
derivation helper from ``research.funding_settlements_v10`` -- only the
implementation under test is imported. The audits:

* FIXTURE L (long/short mirror) : partial + full intervals, positive AND negative
  rate, plus a margin-denominated cross view.
* FIXTURE H                     : symbol-native cadence (A: 8h grid, B: 12h grid),
  asymmetric accrual over identical wall-clock holding.
* FIXTURE P (PIT bounds)        : late-published settlement never applied before
  its staged publication instant; unknown first interval never imputed;
  entry/exit boundary semantics; missing-mark fail-closed behaviour.

All epochs are epoch NANOSECONDS end to end.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from research.funding_settlements_v10 import (
    SKIPPED_BEFORE_OR_AT_ENTRY,
    SKIPPED_INVALID_MARK,
    SKIPPED_NOT_YET_PUBLISHED,
    SKIPPED_NO_NATIVE_PREDECESSOR,
    AppliedFundingEvent,
    FundingSettlementBook,
    FundingStagingError,
    HoldingSpan,
    SIGN_CONVENTION,
    accrue_schedule,
    accrue_span,
    load_staged_books,
    parse_settlement_rows,
    schedule_result_totals,
    side_sign_from_qty,
    spans_from_stepwise_positions,
)

NS_PER_MS = 1_000_000
DAY_NS = 86_400_000 * NS_PER_MS
HOUR_NS = 3_600 * NS_PER_MS


def _ns(iso: str) -> int:
    dt = datetime.fromisoformat(iso).replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1_000_000_000)


def _write_bundle(root, symbol: str, rows_ms: list[dict]) -> None:
    """Stage a bundle exactly like research.funding_pit expects (epoch ms)."""
    d = root / symbol
    d.mkdir(parents=True, exist_ok=True)
    stamps = [int(r["fundingTime"]) for r in rows_ms]
    (d / "funding.json").write_text(
        json.dumps(
            {
                "requested_start_ms": min(stamps),
                "requested_end_ms": max(stamps) + DAY_NS // NS_PER_MS,
                "rows": rows_ms,
            }
        )
    )


def _book(symbol: str, settled_rows: list[tuple[int, float, int | None]]) -> FundingSettlementBook:
    """Build a book from ``(settlement_ns, rate, publish_ns_or_None)`` rows."""
    payload = []
    for settlement_ns, rate, publish_ns in settled_rows:
        row: dict = {
            "fundingTime": settlement_ns // NS_PER_MS,
            "fundingRate": repr(float(rate)),
        }
        if publish_ns is not None:
            row["publishTimeMs"] = publish_ns // NS_PER_MS
        payload.append(row)
    return FundingSettlementBook(symbol, parse_settlement_rows(symbol, payload))


def _constant_mark(price: float):
    def _mark(symbol: str, stamp_ns: int) -> float | None:
        return price

    return _mark


# =========================================================================== #
# BG-3 loader contract (staged bundle layout from research.funding_pit)
# =========================================================================== #
def test_loader_reads_staged_bundles_with_native_cadence(tmp_path):
    day = _ns("2026-03-02T00:00:00")
    _write_bundle(
        tmp_path,
        "AAUSDT",
        [  # native 8h cadence, epochs in MS on disk
            {"fundingTime": day // NS_PER_MS, "fundingRate": "0.0004"},
            {"fundingTime": (day + 8 * HOUR_NS) // NS_PER_MS, "fundingRate": "0.0010"},
            {"fundingTime": (day + 16 * HOUR_NS) // NS_PER_MS, "fundingRate": "-0.0050"},
        ],
    )
    _write_bundle(
        tmp_path,
        "BBUSDT",
        [  # deliberately NON-8h native cadence: 00:00 + 12:00 only
            {"fundingTime": day // NS_PER_MS, "fundingRate": "0.0007"},
            {"fundingTime": (day + 12 * HOUR_NS) // NS_PER_MS, "fundingRate": "0.0020"},
        ],
    )
    books = load_staged_books(tmp_path)
    assert sorted(books) == ["AAUSDT", "BBUSDT"]
    assert books["BBUSDT"].n_settlements == 2
    assert books["BBUSDT"].native_interval_start(1) == day
    assert books["AAUSDT"].stamps == (
        day,
        day + 8 * HOUR_NS,
        day + 16 * HOUR_NS,
    )
    # Publication defaults to the settlement stamp when no explicit field.
    req = load_staged_books(tmp_path, ["AAUSDT"], require_all=False)
    assert req["AAUSDT"].publish_stamps[0] == day


def test_loader_fail_closed_on_missing_bundle_and_bad_rows(tmp_path):
    _write_bundle(
        tmp_path,
        "OKUSDT",
        [{"fundingTime": _ns("2026-03-02T00:00:00") // NS_PER_MS, "fundingRate": "0"}],
    )
    with pytest.raises(FundingStagingError):
        load_staged_books(tmp_path, ["MISSINGUSDT"])
    empty = load_staged_books(tmp_path, ["MISSINGUSDT"], require_all=False)
    assert empty["MISSINGUSDT"].n_settlements == 0

    with pytest.raises(FundingStagingError):  # non-finite rate
        parse_settlement_rows("X", [{"fundingTime": 0, "fundingRate": "nan"}])
    with pytest.raises(FundingStagingError):  # conflicting duplicate stamp
        parse_settlement_rows(
            "X",
            [
                {"fundingTime": 5, "fundingRate": "0.001"},
                {"fundingTime": 5, "fundingRate": "0.002"},
            ],
        )
    collapsed = parse_settlement_rows(  # identical restage collapses idempotently
        "X",
        [
            {"fundingTime": 5, "fundingRate": "0.001"},
            {"fundingTime": 5, "fundingRate": "0.001"},
        ],
    )
    assert len(collapsed) == 1


# =========================================================================== #
# G15 FIXTURE L -- LONG vs SHORT, partial + full interval, +/- rate
# =========================================================================== #
FIXTURE_MARK_PRICE = 50_000.0                       # USDT per unit
FIXTURE_QTY = 2.0                                   # units
# Hand value: 50_000 USDT/unit * 2 units = 100_000 USDT exposure
FIXTURE_NOTIONAL_HAND = 100_000.0
FIXTURE_RATE_POSITIVE = 0.0100                      # 1% per 8h epoch (deliberately big)
FIXTURE_RATE_NEGATIVE = -0.0050
FIXTURE_MARGIN_RATE = 0.05                          # initial-margin cross view


def _long_short_book():
    day = _ns("2026-03-02T00:00:00")
    book = _book(
        "LBXUSDT",
        [
            (day, 0.0, None),
            (day + 8 * HOUR_NS, FIXTURE_RATE_POSITIVE, None),
            (day + 16 * HOUR_NS, FIXTURE_RATE_NEGATIVE, None),
        ],
    )
    return book, day


def test_g15_long_pays_positive_rate_hand_computed():
    book, day = _long_short_book()
    entry = day + 6 * HOUR_NS          # enters mid-way through the 00->08 epoch
    exit_ = day + 20 * HOUR_NS
    res = accrue_span(
        book,
        entry_ns=entry,
        exit_ns=exit_,
        qty_signed=FIXTURE_QTY,
        mark_fn=_constant_mark(FIXTURE_MARK_PRICE),
        observed_through_ns=exit_,
    )
    # INDEPENDENT hand derivation:
    #   notional               = 50_000 * 2                                        = 100_000 USDT
    #   E1@08:00 epoch 00->08 : held fraction (08:00 - 06:00)/8h                  = 0.25
    #       payment = -(+1 side) * 0.0100 * 100_000 * 0.25                       = -250.000000
    #   E2@16:00 epoch 08->16 : held fraction 1.0 (whole epoch held)
    #       payment = -(+1 side) * (-0.0050) * 100_000 * 1.0                     = +500.000000
    #   net cashflow                                                               = +250.000000
    expected_e1_hand = -(FIXTURE_NOTIONAL_HAND * FIXTURE_RATE_POSITIVE * 0.25)
    expected_e2_hand = -(FIXTURE_NOTIONAL_HAND * FIXTURE_RATE_NEGATIVE * 1.0)
    assert round(expected_e1_hand, 9) == -250.000000
    assert round(expected_e2_hand, 9) == +500.000000
    assert len(res.events) == 2
    assert res.events[0].cashflow_usdt == pytest.approx(-250.000000, abs=1e-9)
    assert res.events[1].cashflow_usdt == pytest.approx(+500.000000, abs=1e-9)
    assert res.total_cashflow_usdt == pytest.approx(+250.000000, abs=1e-9)
    # Margin-denominated cross view: +250 net against 100_000 * 0.05 = 5_000 margin.
    assert res.total_cashflow_usdt / (FIXTURE_NOTIONAL_HAND * FIXTURE_MARGIN_RATE) == pytest.approx(0.05)


def test_g15_short_receives_positive_rate_mirror_hand_computed():
    book, day = _long_short_book()
    entry = day + 6 * HOUR_NS
    exit_ = day + 20 * HOUR_NS
    res = accrue_span(
        book,
        entry_ns=entry,
        exit_ns=exit_,
        qty_signed=-FIXTURE_QTY,
        mark_fn=_constant_mark(FIXTURE_MARK_PRICE),
        observed_through_ns=exit_,
    )
    # INDEPENDENT hand derivation (short receives what long pays):
    #   E1 = -(-1) * 0.0100 * 100_000 * 0.25 = +250.000000
    #   E2 = -(-1) * (-0.0050) * 100_000 * 1.0 = -500.000000 ; net = -250.000000
    assert [round(e.cashflow_usdt, 9) for e in res.events] == [+250.000000, -500.000000]
    assert round(res.total_cashflow_usdt, 9) == -250.000000


def test_g15_zero_rate_books_nothing_and_convention_is_frozen():
    day = _ns("2026-03-02T00:00:00")
    flat = _book(
        "FLATUSDT",
        [(day, 0.0, None), (day + 8 * HOUR_NS, 0.0, None)],
    )
    res = accrue_span(
        flat,
        entry_ns=day + 1 * HOUR_NS,
        exit_ns=day + 9 * HOUR_NS,
        qty_signed=1.0,
        mark_fn=_constant_mark(1_000.0),
        observed_through_ns=day + 9 * HOUR_NS,
    )
    assert res.total_cashflow_usdt == 0.0 and len(res.events) == 1
    assert {e.sign_convention for e in res.events} == {SIGN_CONVENTION}
    # Epoch 00->08 held from 01:00 => (08:00 - 01:00)/8h = 0.875.
    assert round(res.events[0].held_fraction, 12) == 0.875
    with pytest.raises(FundingStagingError):
        side_sign_from_qty(0.0)


# =========================================================================== #
# G15 FIXTURE H -- heterogeneous symbol-native cadence
# =========================================================================== #
HETERO_MARK = 200_000.0     # USDT per unit
HETERO_QTY = 1.0            # hand value: notional 200_000 USDT per leg
HETERO_RATE_A = 0.0010      # XA 8h cadence rate
HETERO_RATE_B = 0.0020      # XB 12h cadence rate


def _hetero_books() -> tuple[dict[str, FundingSettlementBook], int]:
    day = _ns("2026-03-02T00:00:00")
    xa = _book(
        "XAUSDT",
        [
            (day, 0.0004, None),
            (day + 8 * HOUR_NS, HETERO_RATE_A, None),
            (day + 16 * HOUR_NS, HETERO_RATE_A, None),
        ],
    )
    xb = _book(  # native 12h cadence
        "XBUSDT",
        [
            (day, 0.0007, None),
            (day + 12 * HOUR_NS, HETERO_RATE_B, None),
        ],
    )
    return {"XAUSDT": xa, "XBUSDT": xb}, day


def test_g15_heterogeneous_native_cadence_accrues_at_own_boundaries():
    books, day = _hetero_books()
    entry = day                          # enter exactly ON the shared 00:00 stamp
    exit_ = day + 20 * HOUR_NS
    out = accrue_schedule(
        [
            HoldingSpan("XAUSDT", entry, exit_, HETERO_QTY),
            HoldingSpan("XBUSDT", entry, exit_, HETERO_QTY),
        ],
        books,
        mark_fn=_constant_mark(HETERO_MARK),
        observed_through_ns=exit_,
    )
    # INDEPENDENT hand derivation:
    #   XA (8h cadence; stamps 08:00/16:00 inside span):
    #       08:00 epoch 00->08, fully held => 0.0010 * 200_000 * 1.0 paid = -200.000000
    #       16:00 epoch 08->16, fully held => 0.0010 * 200_000 * 1.0 paid = -200.000000
    #       net = -400.000000
    #   XB (NATIVE 12h cadence; single stamp 12:00 inside span):
    #       12:00 epoch 00->12, fully held => 0.0020 * 200_000 * 1.0 paid = -400.000000
    #       net = -400.000000
    # Under a wrongly-assumed uniform 8h grid XB would have been charged at
    # 08:00 AND 16:00 instead of once at 12:00.
    per_symbol = out.cashflow_by_symbol()
    assert round(per_symbol["XAUSDT"], 9) == -400.000000
    assert round(per_symbol["XBUSDT"], 9) == -400.000000
    xb_events = [e for e in out.events if e.symbol == "XBUSDT"]
    assert [e.settlement_ns for e in xb_events] == [day + 12 * HOUR_NS]
    assert [round(e.held_fraction, 12) for e in xb_events] == [1.0]
    xa_stamps = [e.settlement_ns for e in out.events if e.symbol == "XAUSDT"]
    assert xa_stamps == [day + 8 * HOUR_NS, day + 16 * HOUR_NS]
    totals = schedule_result_totals(out)
    assert round(totals["total_cashflow_usdt"], 9) == -800.000000


def test_g15_asymmetric_same_wallclock_span_settles_per_symbol_only():
    """Identical wall-clock holding, different symbols => different settlements."""
    books, day = _hetero_books()
    entry = day + 15 * HOUR_NS
    exit_ = day + 17 * HOUR_NS
    out = accrue_schedule(
        [
            HoldingSpan("XAUSDT", entry, exit_, -HETERO_QTY),   # SHORT
            HoldingSpan("XBUSDT", entry, exit_, -HETERO_QTY),   # SHORT
        ],
        books,
        mark_fn=_constant_mark(HETERO_MARK),
        observed_through_ns=exit_,
    )
    # INDEPENDENT hand derivation:
    #   XA settles 16:00 on its own epoch 08->16: held (16:00-15:00)/8h = 0.125
    #       short RECEIVES +0.0010 * 200_000 * 0.125                         = +25.000000
    #   XB has NO stamp in (15:00, 17:00] under its 12h cadence
    #       => zero events, zero accrual regardless of any assumed grid      = 0.000000
    per_symbol = out.cashflow_by_symbol()
    assert round(per_symbol["XAUSDT"], 9) == +25.000000
    assert per_symbol.get("XBUSDT", 0.0) == 0.0
    assert [e.symbol for e in out.events] == ["XAUSDT"]


# =========================================================================== #
# G15 FIXTURE P -- PIT bounds
# =========================================================================== #
PIT_MARK = 125_000.0        # notional 125_000 USDT for qty 1.0
PIT_RATE = 0.0008


def _pit_book() -> tuple[FundingSettlementBook, int]:
    day = _ns("2026-03-03T00:00:00")
    book = _book(
        "PTUSDT",
        [
            (day, 0.0, None),
            (day + 8 * HOUR_NS, PIT_RATE, day + 9 * HOUR_NS),  # published LATE
        ],
    )
    return book, day


def test_g15_no_accrual_before_publication_instant():
    book, day = _pit_book()
    common = dict(
        entry_ns=day + 7 * HOUR_NS,
        exit_ns=day + 10 * HOUR_NS,
        qty_signed=1.0,
        mark_fn=_constant_mark(PIT_MARK),
    )
    early = accrue_span(book, observed_through_ns=day + 8 * HOUR_NS + 30 * 60_000_000, **common)
    assert early.events == [] and early.total_cashflow_usdt == 0.0
    assert [s.reason for s in early.skipped] == [SKIPPED_NOT_YET_PUBLISHED]

    late = accrue_span(book, observed_through_ns=day + 10 * HOUR_NS, **common)
    # INDEPENDENT hand derivation once published:
    #   epoch 00:00->08:00, held (08:00 - 07:00)/8h = 0.125
    #   payment = -(+1) * 0.0008 * 125_000 * 0.125                            = -12.500000
    assert len(late.events) == 1
    assert round(late.events[0].held_fraction, 12) == 0.125
    assert round(late.total_cashflow_usdt, 9) == -12.500000


def test_g15_first_bundle_stamp_has_unknown_interval_never_imputed():
    day = _ns("2026-03-04T00:00:00")
    book = _book("FIRSTUSDT", [(day + 8 * HOUR_NS, 0.005, None)])
    res = accrue_span(
        book,
        entry_ns=day,
        exit_ns=day + 9 * HOUR_NS,
        qty_signed=1.0,
        mark_fn=_constant_mark(1_000.0),
        observed_through_ns=day + 9 * HOUR_NS,
    )
    # No staged predecessor exists: cadence may NOT be guessed (never assumed
    # uniform 8h), so the event is surfaced as skipped and worth nothing.
    assert res.events == [] and res.total_cashflow_usdt == 0.0
    assert [s.reason for s in res.skipped] == [SKIPPED_NO_NATIVE_PREDECESSOR]


@pytest.mark.parametrize("entry_hour", [0.0, 8.0])
def test_g15_entry_boundary_semantics(entry_hour):
    day = _ns("2026-03-05T00:00:00")
    book = _book(
        "BNUSDT", [(day, 0.0, None), (day + 8 * HOUR_NS, 0.001, None)]
    )
    entry = day + int(entry_hour * HOUR_NS)
    res = accrue_span(
        book,
        entry_ns=entry,
        exit_ns=day + 10 * HOUR_NS,
        qty_signed=1.0,
        mark_fn=_constant_mark(1_000.0),
        observed_through_ns=day + 10 * HOUR_NS,
    )
    if entry_hour == 8.0:
        # Entering exactly AT the settle stamp: the just-completed epoch was
        # never held -> audited boundary skip, zero value.
        assert res.events == [] and res.total_cashflow_usdt == 0.0
        assert [s.reason for s in res.skipped] == [SKIPPED_BEFORE_OR_AT_ENTRY]
    else:
        # Entry at exactly 00:00 == that stamp -> audited boundary skip; the
        # 08:00 stamp covers the fully-held 00->08 epoch:
        #   -0.001 * (1000 USDT notional) * 1.0 = -1.000000.
        assert [(s.reason) for s in res.skipped] == [SKIPPED_BEFORE_OR_AT_ENTRY]
        assert round(res.total_cashflow_usdt, 9) == -1.000000
        assert round(res.events[0].held_fraction, 12) == 1.0


def test_g15_exit_exactly_at_settlement_pays_full_epoch():
    day = _ns("2026-03-06T00:00:00")
    book = _book("EXUSDT", [(day, 0.0, None), (day + 8 * HOUR_NS, 0.001, None)])
    res = accrue_span(
        book,
        entry_ns=day,
        exit_ns=day + 8 * HOUR_NS,          # close AT the settle stamp
        qty_signed=1.0,
        mark_fn=_constant_mark(1_000.0),
        observed_through_ns=day + 8 * HOUR_NS,
    )
    # Whole preceding epoch held -> FULL charge: 0.001 * 1_000 = -1.000000.
    assert round(res.total_cashflow_usdt, 9) == -1.000000
    assert round(res.events[0].held_fraction, 12) == 1.0


def test_g15_no_accrual_outside_holding_span():
    day = _ns("2026-03-06T12:00:00")
    book = _book(
        "OSPUSDT",
        [
            (day, 0.0, None),
            (day + 4 * HOUR_NS, 0.0020, None),    # before entry
            (day + 20 * HOUR_NS, 0.0020, None),   # after exit
        ],
    )
    res = accrue_span(
        book,
        entry_ns=day + 6 * HOUR_NS,
        exit_ns=day + 16 * HOUR_NS,
        qty_signed=3.0,
        mark_fn=_constant_mark(1_000.0),
        observed_through_ns=day + 22 * HOUR_NS,
    )
    assert res.events == [] and res.skipped == [] and res.total_cashflow_usdt == 0.0


def test_g15_missing_mark_fails_closed_or_skips_explicitly():
    day = _ns("2026-03-07T00:00:00")
    book = _book("MKUSDT", [(day, 0.0, None), (day + 4 * HOUR_NS, 0.001, None)])
    with pytest.raises(FundingStagingError):
        accrue_span(
            book,
            entry_ns=day,
            exit_ns=day + 5 * HOUR_NS,
            qty_signed=1.0,
            mark_fn=lambda sym, ts: None,
            observed_through_ns=day + 5 * HOUR_NS,
        )
    skipped_res = accrue_span(
        book,
        entry_ns=day,
        exit_ns=day + 5 * HOUR_NS,
        qty_signed=1.0,
        mark_fn=lambda sym, ts: None,
        observed_through_ns=day + 5 * HOUR_NS,
        on_missing_mark="skip",
    )
    # 00:00 stamp == entry (audited boundary skip) + 04:00 mark unavailable.
    assert [s.reason for s in skipped_res.skipped] == [
        SKIPPED_BEFORE_OR_AT_ENTRY,
        SKIPPED_INVALID_MARK,
    ]
    assert skipped_res.total_cashflow_usdt == 0.0


# =========================================================================== #
# BG-3 execution-schedule adapters
# =========================================================================== #
def test_spans_from_stepwise_positions_split_at_changes():
    day = _ns("2026-03-08T00:00:00")
    points = [
        (day, 0.0),
        (day + 1 * HOUR_NS, 2.0),
        (day + 7 * HOUR_NS, -2.0),   # flip long->short exactly at 07:00
        (day + 11 * HOUR_NS, 0.0),   # flat again
    ]
    spans = spans_from_stepwise_positions("SUSDT", points)
    assert [(s.entry_ns, s.exit_ns, s.qty_signed) for s in spans] == [
        (day + 1 * HOUR_NS, day + 7 * HOUR_NS, 2.0),
        (day + 7 * HOUR_NS, day + 11 * HOUR_NS, -2.0),
    ]


def test_accrue_schedule_reconciles_by_symbol_and_aggregate():
    books, day = _hetero_books()
    exit_ = day + 20 * HOUR_NS
    out = accrue_schedule(
        [
            HoldingSpan("XAUSDT", day, exit_, HETERO_QTY),
            HoldingSpan("XBUSDT", day, exit_, HETERO_QTY),
        ],
        books,
        mark_fn=_constant_mark(HETERO_MARK),
        observed_through_ns=exit_,
    )
    totals = schedule_result_totals(out)
    assert totals["sign_convention"] == SIGN_CONVENTION
    # Applied: XA 08:00 + XA 16:00 + XB 12:00. Both symbols' shared 00:00 stamp
    # equals the entry instant -> audited boundary skip each, worth nothing.
    assert totals["applied_events"] == 3 and totals["skipped_events"] == 2
    assert totals["skipped_reasons"] == {SKIPPED_BEFORE_OR_AT_ENTRY: 2}
    assert sum(totals["cashflow_by_symbol"].values()) == pytest.approx(
        totals["total_cashflow_usdt"], abs=1e-9
    )
    assert round(totals["total_cashflow_usdt"], 9) == -800.000000
    assert all(isinstance(e, AppliedFundingEvent) for e in out.events)


def test_accrue_schedule_requires_book_for_scheduled_symbol():
    day = _ns("2026-03-09T00:00:00")
    with pytest.raises(FundingStagingError):
        accrue_schedule(
            [HoldingSpan("GHOSTUSDT", day, day + HOUR_NS, 1.0)],
            {},
            mark_fn=_constant_mark(1.0),
            observed_through_ns=day + HOUR_NS,
        )


def test_adjacent_legs_do_not_double_charge_the_settlement_instant():
    """Leg A closes AT a settlement, leg B reopens AT it: charged once total."""
    day = _ns("2026-03-10T00:00:00")
    book = _book("ADJUSDT", [(day, 0.0, None), (day + 4 * HOUR_NS, 0.0020, None)])
    leg_a = accrue_span(
        book,
        entry_ns=day,
        exit_ns=day + 4 * HOUR_NS,     # exits AT the settlement -> pays in full
        qty_signed=1.0,
        mark_fn=_constant_mark(1_000.0),
        observed_through_ns=day + 8 * HOUR_NS,
    )
    leg_b = accrue_span(
        book,
        entry_ns=day + 4 * HOUR_NS,    # opens AT the same settlement -> owes none
        exit_ns=day + 8 * HOUR_NS,
        qty_signed=-1.0,
        mark_fn=_constant_mark(1_000.0),
        observed_through_ns=day + 8 * HOUR_NS,
    )
    combined = leg_a.total_cashflow_usdt + leg_b.total_cashflow_usdt
    # Full charge (-0.0020 * 1_000 = -2.0) plus the re-entering short contributing
    # nothing for that same epoch: exactly one charge across the seam.
    assert round(combined, 9) == -2.000000
    assert len(leg_b.events) == 0
