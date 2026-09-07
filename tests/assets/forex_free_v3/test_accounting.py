"""FOREX-FREE-V3 accounting kernel goldens (V3-P1, A2 lane) -- F1 remediation.

Every expected number below is a HAND-COMPUTED literal with the arithmetic
written in the comment next to it.  Fixtures are SYNTHETIC_TEST_ONLY; no
real-market PnL, no network, no new data authority.

Frozen conventions under test (inherited unchanged from V1/V2):
  pnl_usd = direction * notional_usd * (exit_price / entry_price - 1)
            direction = +1 LONG, -1 SHORT; notional = 10000 USD-units.
  cost    = notional * (1.5 bps * tier) / 10000, once per fill side,
            tier in {1.0, 1.5, 2.0}.  Costs are never softened.

THE FIXTURE (one round trip, F1 golden):
  F  EUR/USD LONG, notional 10000 USD-units, entry 1.1000 -> exit 1.1050:
     gross: 10000 * (1.1050/1.1000 - 1) = 10000 * 0.0045454545... = 500/11
          = +45.454545454545... USD (IEEE repr 45.45454545454408)
     per-side booked cost: base 10000*(1.5*1.0)/10000 = 1.50 USD
                           tier1.5 10000*(1.5*1.5)/10000 = 2.25 USD
                           tier2.0 10000*(1.5*2.0)/10000 = 3.00 USD
     round-trip cost:      3.00 / 4.50 / 6.00 USD
     booked net:           45.4545... - 3.00 = +42.4545... (42.45454545454408)
                           45.4545... - 4.50 = +40.9545... (40.95454545454408)
                           45.4545... - 6.00 = +39.4545... (39.45454545454408)
     F1 hand deltas:       net(tier1.5) - net(base)  = -1.50 USD EXACTLY
                           net(tier2.0) - net(base)  = -3.00 USD EXACTLY
                           net(tier2.0) - net(tier1.5) = -1.50 USD EXACTLY
     (all exact in binary: 1.5, 2.25, 3.0 and their doubles are exact
     floats, and the gross is the SAME float at every tier, so the deltas
     are exact float subtractions.  This is the anti-V2-defect pin: in V2
     all three booked stress rows were byte-identical to base.)

  Break-even bps (derived from the SAME cost kernel, see the kernel
  docstring): b* = (G/n) * 10000 / (2 * N) with G = 500/11, n = 1, N =
  10000: b* = 45.4545.../2 = 22.7272727272... bps per side -> 22.727273
  at the 6-decimal publication convention.  Check: at b* the per-side
  cost is 10000 * b*/10000 = b* USD, the round trip 2*b* = 45.4545... =
  the gross -> net exactly 0.  Headroom vs the frozen band: 22.727273 bps
  clears base 1.5 bps, tier1.5 2.25 bps and tier2.0 3.0 bps.

V2 defect being remediated (V3 lessons V3-L1/V3-L2): V2 booked "stress"
rows never applied the tier multipliers (tier1.5 == base byte-identical;
tier2.0 measured fill delay only at base costs).  The V3 kernel re-books
the same trades at the tier's per-side cost and refuses to return a stress
book whose tier rows collide.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from research.assets.forex_free_v3 import accounting as A  # noqa: E402

NOTIONAL = 10000.0

# Hand-computed golden literals for THE FIXTURE (arithmetic in the module docstring).
F_GROSS = 500.0 / 11            # +45.454545454545...  (float repr 45.45454545454408)
F_COST_RT_BASE = 3.00           # 1.50 + 1.50
F_COST_RT_T15 = 4.50            # 2.25 + 2.25
F_COST_RT_T20 = 6.00            # 3.00 + 3.00
F_NET_BASE = F_GROSS - 3.00     # +42.454545454545...
F_NET_T15 = F_GROSS - 4.50      # +40.954545454545...
F_NET_T20 = F_GROSS - 6.00      # +39.454545454545...
F_DELTA_T15 = -1.50             # net(t1.5) - net(base), EXACT in binary
F_DELTA_T20 = -3.00             # net(t2.0) - net(base), EXACT in binary
F_BREAK_EVEN_BPS = 22.727273    # (500/11)/2 rounded to 6 decimals

ENTRY_TS = "2026-01-05T10:00:00+00:00"
EXIT_TS = "2026-01-05T15:00:00+00:00"


def _fixture_spec(tid="F1", pair="EUR/USD", side="LONG",
                  entry=1.1000, exit_=1.1050, notional=NOTIONAL):
    return A.TradeSpec(trade_id=tid, pair=pair, side=side, notional_usd=notional,
                       entry_price=entry, exit_price=exit_,
                       entry_ts_utc=ENTRY_TS, exit_ts_utc=EXIT_TS)


def _fixture_specs(n=3):
    """Non-empty trade set: n distinct round trips of the F1 fixture shape."""
    return [_fixture_spec(tid=f"F{i + 1}") for i in range(n)]


def _book_fixture_round_trip(book, tier=1.0, tid="F1"):
    book.open_position(trade_id=tid, pair="EUR/USD", side="LONG",
                       notional_usd=NOTIONAL, price=1.1000,
                       ts_utc=ENTRY_TS, cost_tier=tier)
    return book.close_position(tid, 1.1050, ts_utc=EXIT_TS)


# --- the F1 fixture golden: identity PnL and once-per-side costs ---------------- #
def test_fixture_gross_pnl_identity_golden():
    book = A.PositionBook()
    closed = _book_fixture_round_trip(book)
    # 10000 * (1.1050/1.1000 - 1) = 500/11 = +45.4545454545... USD
    assert closed.pnl_usd == pytest.approx(F_GROSS, rel=1e-12)
    # per-side cost at base tier: 10000 * 1.5 / 10000 = 1.50 USD, charged ONCE per side
    assert closed.entry_cost_usd == 1.50
    assert closed.exit_cost_usd == 1.50
    assert book.total_cost_usd == F_COST_RT_BASE == 3.00
    # net = 45.4545... - 3.00 = +42.4545...
    assert closed.net_pnl_usd == pytest.approx(F_NET_BASE, rel=1e-12)
    assert book.open_trade_ids == []
    assert len(book.fills) == 2  # exactly one ENTRY fill + one EXIT fill


def test_fixture_reconciles_strictly_from_fills():
    book = A.PositionBook()
    _book_fixture_round_trip(book)
    turnover = A.turnover_from_fills(book.fills)
    assert turnover["n_entry_fills"] == 1 and turnover["n_exit_fills"] == 1
    assert turnover["entry_notional_usd"] == 10000.0
    assert turnover["exit_notional_usd"] == 10000.0
    assert turnover["total_notional_usd"] == 20000.0
    trades = A.trades_from_fills(book.fills)
    assert trades["round_trips"] == 1 and trades["open_positions"] == 0
    assert trades["trade_ids_closed"] == ["F1"] and trades["pairs"] == ["EUR/USD"]


# --- booked cost per side at every tier of the frozen ladder --------------------- #
@pytest.mark.parametrize("tier,per_side,round_trip", [
    (1.0, 1.50, 3.00),   # 10000 * (1.5 * 1.0) / 10000 = 1.50 per side
    (1.5, 2.25, 4.50),   # 10000 * (1.5 * 1.5) / 10000 = 2.25 per side
    (2.0, 3.00, 6.00),   # 10000 * (1.5 * 2.0) / 10000 = 3.00 per side
])
def test_booked_cost_per_side_all_tiers(tier, per_side, round_trip):
    # the cost kernel agrees with the hand math first
    assert A.bps_cost(NOTIONAL, tier) == per_side
    book = A.PositionBook()
    closed = _book_fixture_round_trip(book, tier=tier)
    assert closed.entry_cost_usd == per_side and closed.exit_cost_usd == per_side
    assert closed.entry_cost_usd + closed.exit_cost_usd == round_trip
    assert book.total_cost_usd == round_trip
    # both fills stamp the tier; the exit reuses the tier bound at entry
    assert all(f.cost_tier == tier for f in book.fills)


def test_break_even_shares_the_same_cost_primitive():
    # bps_cost is per_side_cost_usd at 1.5*tier bps -- ONE kernel, not two formulas
    for tier in A.COST_TIERS:
        assert A.bps_cost(NOTIONAL, tier) == A.per_side_cost_usd(NOTIONAL, 1.5 * tier)
    with pytest.raises(A.PositionBookError, match="BAD_COST_TIER"):
        A.bps_cost(NOTIONAL, 1.7)
    with pytest.raises(A.PositionBookError, match="BAD_BPS"):
        A.per_side_cost_usd(NOTIONAL, -1.0)


# --- F1 FIX: book_stress re-books at the tier cost and moves booked PnL ---------- #
def test_book_stress_golden_and_hand_computed_deltas():
    results = A.book_stress(_fixture_specs())
    assert sorted(results) == [1.0, 1.5, 2.0]
    for tier, net, rt_cost in ((1.0, F_NET_BASE, F_COST_RT_BASE),
                               (1.5, F_NET_T15, F_COST_RT_T15),
                               (2.0, F_NET_T20, F_COST_RT_T20)):
        r = results[tier]
        assert r.n_trades == 3
        # gross PnL is tier-invariant: the SAME trades, only the cost changed
        assert r.gross_price_pnl_usd == pytest.approx(3 * F_GROSS, rel=1e-12)
        # round-trip cost AT the tier: 3.00 / 4.50 / 6.00 per round trip
        assert r.round_trip_cost_usd == pytest.approx(3 * rt_cost, rel=1e-12)
        # booked net PnL RECOMPUTED at the tier's per-side cost
        assert r.net_pnl_usd == pytest.approx(3 * net, rel=1e-12)
        assert r.expectancy_usd == pytest.approx(net, rel=1e-9)
        assert r.metrics["trades"] == 3
        assert r.metrics["total_pnl"] == pytest.approx(3 * net, rel=1e-9)
    # F1 hand deltas, EXACT in binary: tier1.5 costs exactly 1.50 more per
    # round trip, tier2.0 exactly 3.00 more, against an identical gross.
    # Whole-book deltas over the 3-trade fixture: 3 x (-1.50) = -4.50 and
    # 3 x (-3.00) = -9.00 (each trade's delta is exact in binary, and so is
    # their triple).
    assert results[1.5].cost_component_delta_vs_base_usd == 3 * F_DELTA_T15
    assert results[2.0].cost_component_delta_vs_base_usd == 3 * F_DELTA_T20
    assert results[2.0].net_pnl_usd - results[1.5].net_pnl_usd == pytest.approx(3 * F_DELTA_T15, abs=1e-9)
    # per ROUND TRIP, on a single-trade fixture: exactly -1.50 / -3.00
    single = A.book_stress([_fixture_spec()])
    assert single[1.5].cost_component_delta_vs_base_usd == F_DELTA_T15
    assert single[2.0].cost_component_delta_vs_base_usd == F_DELTA_T20
    assert single[1.0].cost_component_delta_vs_base_usd == 0.0
    # the tier delta is a PURE COST component: it equals minus the extra cost
    assert results[1.5].cost_component_delta_vs_base_usd == -(results[1.5].round_trip_cost_usd
                                                              - results[1.0].round_trip_cost_usd)
    assert results[2.0].cost_component_delta_vs_base_usd == -(results[2.0].round_trip_cost_usd
                                                              - results[1.0].round_trip_cost_usd)


def test_anti_v2_defect_booked_stress_rows_pairwise_distinct():
    """THE V2 terminal MEDIUM (F1) regression pin.

    V2 shipped tier1.5 booked rows byte-identical to base and tier2.0 at
    base costs.  In V3, for the non-empty trade set, the booked rows of
    base / tier1.5 / tier2.0 are pairwise distinct -- and book_stress
    itself FAILS CLOSED (STRESS_ROWS_NOT_DISTINCT) rather than ever
    returning a colliding stress book.
    """
    results = A.book_stress(_fixture_specs())
    base, t15, t20 = results[1.0], results[1.5], results[2.0]
    assert base.booked_rows != t15.booked_rows
    assert base.booked_rows != t20.booked_rows
    assert t15.booked_rows != t20.booked_rows
    # and per single trade the net strictly decreases with the tier
    assert base.net_pnl_usd > t15.net_pnl_usd > t20.net_pnl_usd
    # the kernel's own certification ran inside book_stress (no exception above);
    # calling it on the certified result again is a no-op
    A.assert_stress_rows_distinct(results)
    # tampered book whose tier1.5 rows equal base rows (the V2 defect, injected):
    # the helper refuses it instead of certifying
    tampered = dict(results)
    tampered[1.5] = dataclasses.replace(t15, booked_rows=base.booked_rows,
                                        net_pnl_usd=base.net_pnl_usd)
    with pytest.raises(A.PositionBookError, match="STRESS_ROWS_NOT_DISTINCT"):
        A.assert_stress_rows_distinct(tampered)
    # the guarantee is defined for a NON-EMPTY trade set only
    with pytest.raises(A.PositionBookError, match="EMPTY_TRADE_SET"):
        A.book_stress([])
    with pytest.raises(A.PositionBookError, match="BAD_STRESS_TIERS"):
        A.book_stress(_fixture_specs(), tiers=(1.0, 1.5))


def test_fill_delay_events_recorded_separately_never_blended():
    """V3-L2: cost-tier multipliers and fill-delay stress stay separated."""
    delay = {"F1": 1, "F3": 2}
    with_delay = A.book_stress(_fixture_specs(), fill_delay_events=delay)
    without = A.book_stress(_fixture_specs())
    for tier in A.COST_TIERS:
        # delay metadata is carried verbatim on every tier result ...
        assert with_delay[tier].fill_delay_events == delay
        # ... but changes NO booked number: delay stress is not a cost
        assert with_delay[tier].net_pnl_usd == without[tier].net_pnl_usd
        assert with_delay[tier].gross_price_pnl_usd == without[tier].gross_price_pnl_usd
        assert with_delay[tier].round_trip_cost_usd == without[tier].round_trip_cost_usd
        assert with_delay[tier].booked_rows == without[tier].booked_rows
    assert without[1.0].fill_delay_events is None
    with pytest.raises(A.PositionBookError, match="BAD_FILL_DELAY_EVENTS"):
        A.book_stress(_fixture_specs(), fill_delay_events={"GHOST": 1})
    with pytest.raises(A.PositionBookError, match="BAD_FILL_DELAY_EVENTS"):
        A.book_stress(_fixture_specs(), fill_delay_events={"F1": -1})


# --- dual book: separate immutable price-only / financing-adjusted columns ------- #
def test_dual_book_columns_separate_and_immutable():
    adjustment = {"F1": 0.75}   # carried parameter; the formula is frozen in P3
    dual = A.book_dual([_fixture_spec()], financing_adjustment_usd=adjustment)
    row = dual[0]
    # price-only book: gross minus the base-tier round-trip cost
    assert row.gross_price_pnl_usd == pytest.approx(F_GROSS, rel=1e-12)
    assert row.round_trip_cost_usd == 3.00
    assert row.price_only_pnl_usd == pytest.approx(F_GROSS - 3.00, rel=1e-12)
    # financing-adjusted book: price-only PLUS the carried adjustment
    assert row.financing_adjustment_usd == 0.75
    assert row.financing_adjusted_pnl_usd == pytest.approx(F_GROSS - 3.00 + 0.75, rel=1e-12)
    # the two columns are SEPARATE immutable fields on a frozen record
    assert row.price_only_pnl_usd != row.financing_adjusted_pnl_usd
    with pytest.raises(dataclasses.FrozenInstanceError):
        row.price_only_pnl_usd = 0.0
    with pytest.raises(dataclasses.FrozenInstanceError):
        row.financing_adjusted_pnl_usd = 0.0


def test_financing_adjustment_is_a_carried_parameter_not_computed():
    # zero adjustment: the columns carry equal values but stay separate fields
    zero = A.book_dual([_fixture_spec()], financing_adjustment_usd=0.0)[0]
    assert zero.financing_adjustment_usd == 0.0
    assert zero.financing_adjusted_pnl_usd == zero.price_only_pnl_usd
    # a scalar applies to every trade; a negative adjustment lowers the book
    neg = A.book_dual(_fixture_specs(2), financing_adjustment_usd=-2.5)
    assert all(t.financing_adjustment_usd == -2.5 for t in neg)
    assert neg[0].financing_adjusted_pnl_usd == pytest.approx(F_GROSS - 3.00 - 2.5, rel=1e-12)
    # a mapping must cover EVERY trade id (fail closed) and stay finite
    with pytest.raises(A.PositionBookError, match="BAD_FINANCING_ADJUSTMENT"):
        A.book_dual(_fixture_specs(2), financing_adjustment_usd={"F1": 1.0})
    with pytest.raises(A.PositionBookError, match="BAD_FINANCING_ADJUSTMENT"):
        A.book_dual([_fixture_spec()], financing_adjustment_usd=float("nan"))


def test_scored_record_digest_covers_both_columns_and_mutation_fails_validation():
    dual = A.book_dual([_fixture_spec()], financing_adjustment_usd={"F1": 0.75})
    record = A.build_scored_record(dual, record_id="CELL:F:tier1.0")
    # separate top-level columns, hand-pinned at the 10-decimal convention
    assert record["price_only_pnl_usd"] == pytest.approx(F_GROSS - 3.00, rel=1e-9)
    assert record["financing_adjusted_pnl_usd"] == pytest.approx(F_GROSS - 3.00 + 0.75, rel=1e-9)
    assert record["n_trades"] == 1 and record["real_pnl"] is True and record["dry_run"] is False
    # intact record validates against its digest
    digest = A.digest_of(record)
    A.validate_scored_record(record, digest)
    # ANY post-digest mutation of a digest-covered column fails validation
    mutated_price = dict(record, price_only_pnl_usd=record["price_only_pnl_usd"] + 1.0)
    with pytest.raises(A.PositionBookError, match="DUAL_BOOK_VIOLATION"):
        A.validate_scored_record(mutated_price, digest)
    mutated_fin = dict(record, financing_adjusted_pnl_usd=-1e9)
    with pytest.raises(A.PositionBookError, match="DUAL_BOOK_VIOLATION"):
        A.validate_scored_record(mutated_fin, digest)
    dropped = {k: v for k, v in record.items() if k != "financing_adjusted_pnl_usd"}
    with pytest.raises(A.PositionBookError, match="DUAL_BOOK_VIOLATION"):
        A.validate_scored_record(dropped, digest)
    # the two columns are digest-covered: changing either changes the digest
    assert A.digest_of(mutated_price) != digest
    assert A.digest_of(mutated_fin) != digest


# --- break-even bps, hand-checked on the fixture --------------------------------- #
def test_break_even_bps_golden_on_fixture():
    gross = [_book_fixture_round_trip(A.PositionBook()).pnl_usd]
    # b* = (500/11) * 10000 / (2 * 10000) = 22.7272727... -> 22.727273 (6 dp)
    assert A.break_even_bps(gross) == F_BREAK_EVEN_BPS
    # at the break-even the SAME cost kernel zeroes the booked net exactly:
    # per-side cost b* USD each side -> round trip 2*b* == the gross
    raw_be = math.fsum(gross) / (1 * 2 * NOTIONAL) * 10000.0
    assert 2 * A.per_side_cost_usd(NOTIONAL, raw_be) == gross[0]
    assert gross[0] - 2 * A.per_side_cost_usd(NOTIONAL, raw_be) == 0.0
    # below break-even the book is profitable, above it unprofitable
    net_below = gross[0] - 2 * A.per_side_cost_usd(NOTIONAL, 1.5)     # base 1.5 bps
    assert net_below > 0
    net_above = gross[0] - 2 * A.per_side_cost_usd(NOTIONAL, 22.73)   # just above b*
    assert net_above < 0
    # empty book has no break-even; the frozen band fits inside the headroom
    assert A.break_even_bps([]) is None
    assert F_BREAK_EVEN_BPS > 3.0  # clears base 1.5, tier1.5 2.25 and tier2.0 3.0 bps


# --- once-only publication under flock ------------------------------------------- #
RECORD = {"record_id": "CELL:F:tier1.0", "price_only_pnl_usd": 42.4545454545,
          "financing_adjusted_pnl_usd": 43.2045454545}


def test_publish_once_only_same_digest_refused(tmp_path):
    path = tmp_path / "ledger.jsonl"
    publisher = A.AtomicJsonlPublisher(path)
    assert publisher.publish_once(RECORD) == (1, 1)   # first publish: written now
    assert publisher.publish_once(RECORD) == (0, 0)   # SAME digest: refused, no line
    assert publisher.publish_once(dict(RECORD)) == (0, 0)  # equal content, same digest
    lines = [l for l in path.read_bytes().split(b"\n") if l]
    assert len(lines) == 1
    other = dict(RECORD, record_id="CELL:F:tier1.5")  # different record
    assert publisher.publish_once(other) == (1, 1)
    assert publisher.publish_once(other) == (0, 0)
    lines = [l for l in path.read_bytes().split(b"\n") if l]
    assert len(lines) == 2
    # each line IS the canonical bytes of its record, so it is self-verifying
    assert lines[0] == A.canonical_json_bytes(RECORD)
    assert {hashlib.sha256(l).hexdigest() for l in lines} == \
        {A.digest_of(RECORD), A.digest_of(other)}
    # once-only survives a fresh publisher instance over the same ledger
    assert A.AtomicJsonlPublisher(path).publish_once(RECORD) == (0, 0)
    assert len([l for l in path.read_bytes().split(b"\n") if l]) == 2


def test_scored_publisher_flips_published_flag_pre_digest(tmp_path):
    path = tmp_path / "scored.jsonl"
    publisher = A.ScoredLedgerPublisher(path)
    dual = A.book_dual([_fixture_spec()], financing_adjustment_usd=0.75)
    record = A.build_scored_record(dual, record_id="CELL:F:tier1.0")
    assert record["published"] is False
    # dry-run / unreal records are refused before anything is written
    with pytest.raises(A.PositionBookError, match="REAL_PNL_REQUIRED_FOR_SCORED_PUBLICATION"):
        publisher.publish_scored_once(dict(record, dry_run=True))
    assert not path.exists()
    observed, published = publisher.publish_scored_once(record)
    assert (observed, published) == (1, 1)
    lines = [l for l in path.read_bytes().split(b"\n") if l]
    assert len(lines) == 1
    written = json.loads(lines[0].decode("utf-8"))
    # V3-L4: the WRITTEN row carries published=true, flipped BEFORE digesting,
    # and the self-verifying line digest covers it and both book columns
    assert written["published"] is True
    assert hashlib.sha256(lines[0]).hexdigest() == A.digest_of(written)
    A.validate_scored_record(written, hashlib.sha256(lines[0]).hexdigest())
    # replaying the same record is a zero-delta no-op (same flipped digest)
    assert publisher.publish_scored_once(record) == (0, 0)
    assert len([l for l in path.read_bytes().split(b"\n") if l]) == 1


# --- cash accounting is separate from pair accounting (inherited convention) ----- #
def test_cash_is_never_a_pair_and_excluded_from_concentration():
    book = A.PositionBook()
    with pytest.raises(A.PositionBookError, match="BAD_PAIR"):
        book.open_position(trade_id="C1", pair="USD", side="LONG",
                           notional_usd=NOTIONAL, price=1.0,
                           ts_utc=ENTRY_TS, cost_tier=1.0)
    with pytest.raises(A.PositionBookError, match="BAD_PAIR"):
        A.TradeSpec(trade_id="C1", pair="USD", side="LONG", notional_usd=NOTIONAL,
                    entry_price=1.0, exit_price=1.0,
                    entry_ts_utc=ENTRY_TS, exit_ts_utc=EXIT_TS)
    with pytest.raises(A.PositionBookError, match="BAD_PAIR"):
        A.PositionBook().record_no_trade(pair="USD", ts_utc=ENTRY_TS, reason="CASH_BAR")
    assert book.fills == []  # rejected before any state changed
    # USD is the cash currency: it never enters the concentration denominator
    shares = A.pair_concentration({"EUR/USD": F_GROSS, "USD": 999.0})
    assert "USD" not in shares
    assert shares == {"EUR/USD": 1.0}
    assert A.pair_concentration({"EUR/USD": -10.0}) == {"EUR/USD": None}


def test_conversion_beyond_identity_fails_closed():
    assert A.convert_to_usd_identity(42.45, from_currency="USD") == 42.45
    with pytest.raises(A.UnavailableFailClosed, match="UNAVAILABLE_FAIL_CLOSED"):
        A.convert_to_usd_identity(1.0, from_currency="EUR")
