"""FX0 quote-data goldens (owner: A3, PLAN_forex.md sections 7-A3, 8, 15).

Hand-computed, self-contained synthetic tests for the F1 data lane:

- loader: valid bid/ask and OHLC records, missing sides, crossed spreads,
  staleness, naive/non-UTC timestamps, duplicates, unsorted events, unknown
  symbols, exact midpoint derivation, weekend gaps passed through unfilled,
  and a rejection reason code on every rejected row;
- data audit: gap classification against a TEST_ONLY synthetic
  SessionCalendar defined HERE (no forex calendar module is imported — a
  sibling lane owns it), accepted/rejected counts, reason codes and a
  sha256-over-canonical-JSON checksum manifest;
- provider: entitlement/authority decisions fail closed, and midpoint-only
  sources are DIAGNOSTIC_ONLY and never promotable.

All timestamps are fixed UTC instants; wall-clock time is never read.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError
from datetime import date, datetime, time, timedelta, timezone

import pytest

import research.assets.forex.loader as loader_module
from research.assets.common.calendar import Session, SessionCalendar
from research.assets.common.contracts import canonical_json
from research.assets.forex import provider
from research.assets.forex.data_audit import (
    GAP_IN_SESSION,
    GAP_NON_SESSION,
    audit_quote_batch,
    find_gaps,
)
from research.assets.forex.loader import (
    CROSSED_SPREAD,
    DUPLICATE_EVENT,
    INGEST_BEFORE_EVENT,
    MALFORMED_RECORD,
    MALFORMED_TIMESTAMP,
    MISSING_ASK,
    MISSING_BID,
    NAIVE_TIMESTAMP,
    NON_FINITE_PRICE,
    NON_UTC_TIMESTAMP,
    OHLC_INVALID,
    REASON_CODES,
    STALE_QUOTE,
    UNKNOWN_SYMBOL,
    UNSORTED_EVENTS,
    QuoteBatch,
    QuoteRow,
    load_quotes,
    midpoint,
)

UTC = timezone.utc

# Fixed synthetic timeline.  2026-08-28 is a Friday, 2026-08-30 a Sunday,
# 2026-08-31 a Monday, 2026-08-27 a Thursday (hand-checked).
T_THU_1000 = datetime(2026, 8, 27, 10, 0, tzinfo=UTC)
T_THU_1200 = datetime(2026, 8, 27, 12, 0, tzinfo=UTC)
T_FRI_2000 = datetime(2026, 8, 28, 20, 0, tzinfo=UTC)
T_FRI_2001 = datetime(2026, 8, 28, 20, 1, tzinfo=UTC)
T_FRI_2100 = datetime(2026, 8, 28, 21, 0, tzinfo=UTC)
T_SUN_2105 = datetime(2026, 8, 30, 21, 5, tzinfo=UTC)
T_MON_2100 = datetime(2026, 8, 31, 21, 0, tzinfo=UTC)

MAX_AGE = timedelta(minutes=5)

# Hand-computed exact-binary goldens: 1.0, 1.0625, 1.125 are exactly
# representable, so the midpoints below are exact in IEEE-754 doubles.
BID = 1.0
ASK = 1.0625
MID = 1.03125  # (1.0 + 1.0625) / 2

BID_OHLC = {"o": 1.0, "h": 1.0625, "l": 1.0, "c": 1.0625}
ASK_OHLC = {"o": 1.0625, "h": 1.125, "l": 1.0625, "c": 1.125}
# per-field mids: o=(1.0+1.0625)/2=1.03125, h=(1.0625+1.125)/2=1.09375
BAR_MIDS = {"o": 1.03125, "h": 1.09375, "l": 1.03125, "c": 1.09375}


_KEY_ALIASES = {"event": "event_ts_utc", "ingest": "ingest_ts_utc"}


def make_row(**overrides):
    record = {
        "symbol": "EURUSD",
        "event_ts_utc": T_FRI_2000,
        "ingest_ts_utc": T_FRI_2000,
        "bid": BID,
        "ask": ASK,
    }
    for key, value in overrides.items():
        record[_KEY_ALIASES.get(key, key)] = value
    return record


def load(records, *, max_age=MAX_AGE, as_of=T_FRI_2001):
    return load_quotes(records, max_age=max_age, as_of_utc=as_of)


# --- loader: acceptance ------------------------------------------------------ #
def test_valid_bid_ask_rows_pass():
    batch = load(
        [
            make_row(event=T_FRI_2000, ingest=T_FRI_2000),
            make_row(event=T_FRI_2001, ingest=T_FRI_2001),
        ]
    )
    assert batch.accepted_count == 2
    assert batch.rejected_count == 0
    assert batch.accepted_count + batch.rejected_count == 2
    first = batch.rows[0]
    assert first.symbol == "EURUSD"
    assert first.event_ts_utc == T_FRI_2000
    assert first.ingest_ts_utc == T_FRI_2000
    assert first.bid == BID and first.ask == ASK
    assert not first.is_bar


def test_valid_ohlc_bar_passes_and_bar_midpoints_are_exact():
    record = make_row(bid_ohlc=BID_OHLC, ask_ohlc=ASK_OHLC)
    del record["bid"]
    del record["ask"]
    batch = load([record])
    assert batch.accepted_count == 1 and batch.rejected_count == 0
    row = batch.rows[0]
    assert row.is_bar
    mids = row.bar_midpoints()
    for key in ("o", "h", "l", "c"):
        assert getattr(mids, key) == BAR_MIDS[key]


def test_zero_spread_locked_quote_is_not_crossed():
    batch = load([make_row(bid=1.0625, ask=1.0625)])
    assert batch.accepted_count == 1
    assert batch.rows[0].midpoint == 1.0625


# --- loader: rejections (fail closed, reason coded) -------------------------- #
def test_missing_bid_side_rejected():
    batch = load([make_row(bid=None)])
    assert batch.accepted_count == 0
    assert [r.reason_code for r in batch.rejected] == [MISSING_BID]
    assert batch.accepted_count + batch.rejected_count == 1


def test_missing_ask_side_rejected():
    batch = load([make_row(ask=None)])
    assert batch.accepted_count == 0
    assert [r.reason_code for r in batch.rejected] == [MISSING_ASK]


def test_missing_ohlc_side_rejected():
    record = make_row()
    del record["bid"]
    del record["ask"]
    record["ask_ohlc"] = ASK_OHLC
    batch = load([record])
    assert batch.accepted_count == 0
    assert [r.reason_code for r in batch.rejected] == [MISSING_BID]


def test_crossed_spread_rejected():
    batch = load([make_row(bid=1.0625, ask=1.0)])
    assert batch.accepted_count == 0
    assert [r.reason_code for r in batch.rejected] == [CROSSED_SPREAD]


def test_crossed_ohlc_spread_rejected():
    record = make_row()
    del record["bid"]
    del record["ask"]
    # min ask (1.0) < max bid (1.0625) -> crossed even though scalars absent
    record["bid_ohlc"] = BID_OHLC
    record["ask_ohlc"] = {"o": 1.0, "h": 1.125, "l": 1.0, "c": 1.125}
    batch = load([record])
    assert [r.reason_code for r in batch.rejected] == [CROSSED_SPREAD]


def test_stale_quote_rejected_and_exact_max_age_boundary_passes():
    as_of = T_FRI_2100
    stale = load([make_row(event=T_FRI_2100 - timedelta(minutes=10), ingest=T_FRI_2100 - timedelta(minutes=10))], as_of=as_of)
    assert [r.reason_code for r in stale.rejected] == [STALE_QUOTE]
    assert stale.accepted_count == 0
    # exactly max_age old is not stale (strictly-beyond rule)
    boundary = load(
        [make_row(event=T_FRI_2100 - MAX_AGE, ingest=T_FRI_2100 - MAX_AGE)],
        as_of=as_of,
    )
    assert boundary.accepted_count == 1 and boundary.rejected_count == 0


def test_naive_timestamp_rejected():
    naive_event = datetime(2026, 8, 28, 20, 0)  # no tzinfo
    batch = load([make_row(event=naive_event)])
    assert [r.reason_code for r in batch.rejected] == [NAIVE_TIMESTAMP]


def test_non_utc_timestamp_rejected():
    plus_two = timezone(timedelta(hours=2))
    batch = load([make_row(event=datetime(2026, 8, 28, 22, 0, tzinfo=plus_two))])
    assert [r.reason_code for r in batch.rejected] == [NON_UTC_TIMESTAMP]


def test_malformed_timestamp_rejected():
    batch = load([make_row(event=20260828)])
    assert [r.reason_code for r in batch.rejected] == [MALFORMED_TIMESTAMP]


def test_ingest_before_event_rejected():
    batch = load(
        [make_row(event=T_FRI_2001, ingest=T_FRI_2001 - timedelta(minutes=1))]
    )
    assert [r.reason_code for r in batch.rejected] == [INGEST_BEFORE_EVENT]


def test_duplicate_event_rejected_and_first_instance_kept():
    batch = load(
        [
            make_row(event=T_FRI_2000, ask=ASK),
            make_row(event=T_FRI_2000, ask=1.078125),  # same event timestamp
        ]
    )
    assert batch.accepted_count == 1
    assert [r.reason_code for r in batch.rejected] == [DUPLICATE_EVENT]
    assert batch.rows[0].ask == ASK  # the first occurrence is kept, order preserved


def test_unsorted_events_rejected_without_silent_reordering():
    batch = load(
        [
            make_row(event=T_FRI_2001, ingest=T_FRI_2001),
            make_row(event=T_FRI_2000, ingest=T_FRI_2000),  # regresses
        ]
    )
    assert batch.accepted_count == 1
    assert [r.reason_code for r in batch.rejected] == [UNSORTED_EVENTS]
    assert batch.rows[0].event_ts_utc == T_FRI_2001  # input order preserved


def test_unknown_symbol_fails_closed():
    for symbol in ("EURGBP", "eurusd", "EURUSDX", "", None):
        batch = load([make_row(symbol=symbol)])
        assert batch.accepted_count == 0
        assert [r.reason_code for r in batch.rejected] == [UNKNOWN_SYMBOL]


def test_pinned_expected_symbol_rejects_mismatch():
    batch = load_quotes(
        [make_row(symbol="USDJPY")],
        max_age=MAX_AGE,
        as_of_utc=T_FRI_2001,
        symbol="EURUSD",
    )
    assert [r.reason_code for r in batch.rejected] == [UNKNOWN_SYMBOL]


def test_malformed_record_and_non_finite_price_rejected():
    batch = load([42])
    assert [r.reason_code for r in batch.rejected] == [MALFORMED_RECORD]
    batch = load([make_row(ask=float("nan"))])
    assert [r.reason_code for r in batch.rejected] == [NON_FINITE_PRICE]


def test_invalid_ohlc_and_mixed_forms_rejected():
    record = make_row()
    del record["bid"]
    del record["ask"]
    record["bid_ohlc"] = {"o": 1.0, "h": 1.0625, "l": 1.0}  # missing "c"
    record["ask_ohlc"] = ASK_OHLC
    batch = load([record])
    assert [r.reason_code for r in batch.rejected] == [OHLC_INVALID]
    mixed = make_row(bid_ohlc=BID_OHLC, ask_ohlc=ASK_OHLC)  # keeps scalar bid/ask too
    batch = load([mixed])
    assert [r.reason_code for r in batch.rejected] == [MALFORMED_RECORD]


# --- loader: midpoint discipline --------------------------------------------- #
def test_midpoint_equals_half_sum_exactly_where_defined():
    assert midpoint(BID, ASK) == MID
    assert midpoint(1.0, 2.0) == 1.5
    batch = load([make_row()])
    assert batch.rows[0].midpoint == MID


def test_midpoint_is_the_only_named_midpoint_surface():
    mid_names = [n for n in dir(loader_module) if "mid" in n.lower()]
    assert mid_names == ["midpoint"]
    # an OHLC-form row has no single midpoint: derivation is per-field only
    record = make_row()
    del record["bid"]
    del record["ask"]
    record["bid_ohlc"] = BID_OHLC
    record["ask_ohlc"] = ASK_OHLC
    row = load([record]).rows[0]
    with pytest.raises(ValueError):
        row.midpoint  # noqa: B018  (property must raise, not silently substitute)
    assert row.bar_midpoints().o == BAR_MIDS["o"]


def test_loader_has_no_gap_filling_api():
    forbidden = [
        name
        for name in dir(loader_module)
        if any(tok in name.lower() for tok in ("fill", "synth", "interpol"))
    ]
    assert forbidden == []


def test_loader_requires_explicit_staleness_parameters():
    records = [make_row()]
    with pytest.raises(TypeError):
        load_quotes(records, max_age=MAX_AGE)  # as_of_utc is required
    with pytest.raises(ValueError):
        load_quotes(records, max_age=timedelta(0), as_of_utc=T_FRI_2001)
    with pytest.raises(ValueError):
        load_quotes(records, max_age=MAX_AGE, as_of_utc=datetime(2026, 8, 28, 20, 0))


# --- weekend gaps: passed through unfilled ------------------------------------ #
def test_weekend_gap_passed_through_unfilled():
    records = [
        make_row(event=T_FRI_2000, ingest=T_FRI_2000),
        make_row(event=T_SUN_2105, ingest=T_SUN_2105),
    ]
    batch = load(records, max_age=timedelta(days=7), as_of=T_MON_2100)
    # exactly the two supplied rows: nothing synthesized into the weekend
    assert batch.accepted_count == 2 and batch.rejected_count == 0
    assert [row.event_ts_utc for row in batch.rows] == [T_FRI_2000, T_SUN_2105]


# --- every rejection carries a reason code ------------------------------------ #
def test_every_rejection_carries_reason_code_and_full_vocabulary_is_reachable():
    records = [
        make_row(event=T_FRI_2001, ingest=T_FRI_2001),  # accepted (sets last_ts)
        make_row(event=T_FRI_2000, ingest=T_FRI_2000),  # UNSORTED_EVENTS
        make_row(event=T_FRI_2001, ingest=T_FRI_2001),  # DUPLICATE_EVENT
        42,                                             # MALFORMED_RECORD
        make_row(symbol="EURGBP"),                      # UNKNOWN_SYMBOL
        make_row(event=20260828),                       # MALFORMED_TIMESTAMP
        make_row(event=datetime(2026, 8, 28, 20, 0)),   # NAIVE_TIMESTAMP
        make_row(
            event=datetime(2026, 8, 28, 22, 0, tzinfo=timezone(timedelta(hours=2)))
        ),                                              # NON_UTC_TIMESTAMP
        make_row(event=T_FRI_2001, ingest=T_FRI_2000),  # INGEST_BEFORE_EVENT
        make_row(bid=None),                             # MISSING_BID
        make_row(ask=None),                             # MISSING_ASK
        make_row(ask=float("nan")),                     # NON_FINITE_PRICE
        make_row(bid=1.0625, ask=1.0),                  # CROSSED_SPREAD
        make_row(event=T_THU_1200, ingest=T_THU_1200),  # STALE_QUOTE
    ]
    ohlc_record = make_row(event=T_FRI_2001 + timedelta(minutes=2), ingest=T_FRI_2001 + timedelta(minutes=2))
    del ohlc_record["bid"]
    del ohlc_record["ask"]
    ohlc_record["bid_ohlc"] = {"o": 1.0, "h": 1.0625, "l": 1.0}  # OHLC_INVALID
    ohlc_record["ask_ohlc"] = ASK_OHLC
    records.append(ohlc_record)
    mixed = make_row(event=T_FRI_2001 + timedelta(minutes=3), ingest=T_FRI_2001 + timedelta(minutes=3))
    mixed["bid_ohlc"] = BID_OHLC
    mixed["ask_ohlc"] = ASK_OHLC
    records.append(mixed)  # MALFORMED_RECORD (mixed forms)

    batch = load(records, max_age=timedelta(hours=2), as_of=T_FRI_2100)
    assert batch.accepted_count == 1
    assert batch.accepted_count + batch.rejected_count == len(records)
    observed = {r.reason_code for r in batch.rejected}
    assert observed == set(REASON_CODES)  # every code is reachable in one batch
    for rejection in batch.rejected:
        assert rejection.reason_code in REASON_CODES
        assert isinstance(rejection.reason_code, str) and rejection.reason_code.strip()
        assert rejection.detail.strip()
    by_reason = batch.rejected_by_reason()
    assert list(by_reason) == sorted(by_reason)  # sorted mapping
    assert by_reason[UNSORTED_EVENTS] == 1 and by_reason[DUPLICATE_EVENT] == 1


# --- TEST_ONLY synthetic session calendar (defined HERE, injected) ------------ #
class TestOnlyForexWeekdayCalendar(SessionCalendar):
    """Mon-Fri sessions [00:00, 20:00) UTC; closed Sat/Sun. TEST ONLY."""

    @property
    def calendar_id(self) -> str:
        return "TEST_ONLY_FX_WEEKDAY_2000Z"

    def is_session_day(self, day: date) -> bool:
        return day.weekday() < 5

    def holidays(self, start: date, end: date) -> tuple[date, ...]:
        if end < start:
            raise ValueError("end date precedes start date")
        return ()

    def session_bounds(self, day: date) -> Session | None:
        if day.weekday() >= 5:
            return None
        start = datetime.combine(day, time.min, tzinfo=UTC)
        return Session(start_utc=start, end_utc=start + timedelta(hours=20))

    def early_close_cutoff_utc(self, day: date) -> datetime | None:
        return None


def test_synthetic_calendar_is_explicitly_test_only():
    calendar = TestOnlyForexWeekdayCalendar()
    assert calendar.calendar_id.startswith("TEST_ONLY_")
    assert calendar.is_test_only()
    assert not calendar.is_session_day(date(2026, 8, 29))  # Saturday
    assert calendar.session_bounds(date(2026, 8, 28)) == Session(
        start_utc=datetime(2026, 8, 28, 0, 0, tzinfo=UTC),
        end_utc=datetime(2026, 8, 28, 20, 0, tzinfo=UTC),
    )


def test_weekend_gap_classified_non_session_by_injected_calendar():
    records = [
        make_row(event=T_FRI_2000, ingest=T_FRI_2000),  # == Friday session end
        make_row(event=T_SUN_2105, ingest=T_SUN_2105),  # Sunday: closed
    ]
    batch = load(records, max_age=timedelta(days=7), as_of=T_MON_2100)
    report = audit_quote_batch(batch, calendar=TestOnlyForexWeekdayCalendar(), max_gap=timedelta(hours=1))
    assert len(report.gaps) == 1
    gap = report.gaps[0]
    # Fri 20:00 -> Sun 21:05 = 2 days + 65 minutes = 176700 s (hand-computed)
    assert gap.duration_seconds == 176700.0
    assert gap.classification == GAP_NON_SESSION
    assert gap.filled is False
    assert report.gaps_by_classification() == {GAP_NON_SESSION: 1}
    assert report.calendar_is_test_only is True


def test_in_session_gap_classified_by_injected_calendar():
    records = [
        make_row(event=T_THU_1000, ingest=T_THU_1000),  # Thursday 10:00
        make_row(event=T_THU_1200, ingest=T_THU_1200),  # Thursday 12:00
    ]
    batch = load(records, max_age=timedelta(days=7), as_of=T_THU_1200)
    report = audit_quote_batch(batch, calendar=TestOnlyForexWeekdayCalendar(), max_gap=timedelta(hours=1))
    assert len(report.gaps) == 1
    gap = report.gaps[0]
    assert gap.duration_seconds == 7200.0  # hand-computed: 10:00 -> 12:00
    assert gap.classification == GAP_IN_SESSION
    assert gap.filled is False


def test_audit_counts_reason_codes_and_checksum_manifest():
    records = [
        make_row(event=T_FRI_2000, ingest=T_FRI_2000),  # accepted
        make_row(bid=1.0625, ask=1.0),                  # CROSSED_SPREAD
        make_row(event=T_FRI_2000, ingest=T_FRI_2000),  # DUPLICATE_EVENT
    ]
    batch = load(records)
    calendar = TestOnlyForexWeekdayCalendar()
    report = audit_quote_batch(batch, calendar=calendar, max_gap=timedelta(hours=1))
    assert report.accepted_count == 1 and report.rejected_count == 2
    assert dict(report.rejected_by_reason) == {CROSSED_SPREAD: 1, DUPLICATE_EVENT: 1}
    assert report.duplicate_count == 1
    assert report.symbols == ("EURUSD",)
    assert report.checksum == hashlib.sha256(
        canonical_json(dict(report.manifest)).encode("utf-8")
    ).hexdigest()
    again = audit_quote_batch(batch, calendar=calendar, max_gap=timedelta(hours=1))
    assert again.checksum == report.checksum  # deterministic
    json.loads(canonical_json(dict(report.manifest)))  # manifest is JSON-safe


def test_audit_requires_calendar_instance_and_sorted_batch():
    batch = load([make_row(), make_row(event=T_FRI_2001, ingest=T_FRI_2001)])
    with pytest.raises(TypeError):
        audit_quote_batch(batch, calendar=None, max_gap=timedelta(hours=1))
    with pytest.raises(TypeError):
        audit_quote_batch(batch, calendar=object(), max_gap=timedelta(hours=1))
    with pytest.raises(TypeError):
        audit_quote_batch(batch.rows, calendar=TestOnlyForexWeekdayCalendar(), max_gap=timedelta(hours=1))
    with pytest.raises(ValueError):
        audit_quote_batch(batch, calendar=TestOnlyForexWeekdayCalendar(), max_gap=timedelta(0))
    # hand-built unsorted batch (bypassing the loader) must fail closed
    bad = QuoteBatch(
        rows=(
            QuoteRow(symbol="EURUSD", event_ts_utc=T_FRI_2001, ingest_ts_utc=T_FRI_2001, bid=BID, ask=ASK),
            QuoteRow(symbol="EURUSD", event_ts_utc=T_FRI_2000, ingest_ts_utc=T_FRI_2000, bid=BID, ask=ASK),
        ),
        rejected=(),
    )
    with pytest.raises(ValueError):
        find_gaps(bad, calendar=TestOnlyForexWeekdayCalendar(), max_gap=timedelta(hours=1))


# --- provider identity and entitlement (fail-closed) --------------------------- #
SCHEMA_DIGEST_A = hashlib.sha256(b"provider-schema-doc-A").hexdigest()


def _identity(**overrides):
    fields = {
        "provider_id": "OWNER_DEALER_FEED",
        "schema_digest": SCHEMA_DIGEST_A,
        "quote_mode": provider.QUOTE_MODE_BID_ASK,
        "owner_authorized": True,
        "venue_scope": "SINGLE_DEALER",
    }
    fields.update(overrides)
    return provider.ProviderIdentity(**fields)


def test_no_provider_recorded_is_unavailable_fail_closed():
    decision = provider.classify_provider(None)
    assert decision.status == "UNAVAILABLE_FAIL_CLOSED"
    assert decision.promotable is False
    assert decision.reason.strip()


def test_unauthorized_provider_is_unavailable_fail_closed():
    decision = provider.classify_provider(_identity(owner_authorized=False))
    assert decision.status == "UNAVAILABLE_FAIL_CLOSED"
    assert decision.promotable is False


def test_midpoint_only_sources_are_diagnostic_only_and_never_promotable():
    assert provider.MIDPOINT_ONLY_PROMOTABLE is False
    for owner_authorized in (True, False):
        decision = provider.classify_provider(
            _identity(
                quote_mode=provider.QUOTE_MODE_MIDPOINT_ONLY,
                owner_authorized=owner_authorized,
            )
        )
        assert decision.status == "DIAGNOSTIC_ONLY"
        assert decision.promotable is False  # never promotable, no exceptions


def test_owner_authorized_bid_ask_provider_is_promotable():
    decision = provider.classify_provider(_identity())
    assert decision.status == "PROMOTABLE"
    assert decision.promotable is True
    assert provider.require_promotable(decision) is decision


def test_require_promotable_fails_closed_on_non_promotable():
    for decision in (
        provider.classify_provider(None),
        provider.classify_provider(_identity(owner_authorized=False)),
        provider.classify_provider(
            _identity(quote_mode=provider.QUOTE_MODE_MIDPOINT_ONLY)
        ),
    ):
        with pytest.raises(ValueError):
            provider.require_promotable(decision)


def test_provider_records_are_frozen_and_validated():
    identity = _identity()
    with pytest.raises(FrozenInstanceError):
        identity.provider_id = "OTHER"  # type: ignore[misc]
    with pytest.raises(ValueError):
        _identity(quote_mode="MID")  # unknown quote mode
    with pytest.raises(ValueError):
        _identity(schema_digest="not-a-digest")
    with pytest.raises(ValueError):
        _identity(owner_authorized="yes")  # bool required
    # entitlement decisions enforce their own invariant: promotable iff PROMOTABLE
    with pytest.raises(ValueError):
        provider.EntitlementDecision(
            status="UNAVAILABLE_FAIL_CLOSED", promotable=True, reason="x"
        )
    with pytest.raises(ValueError):
        provider.EntitlementDecision(status="WHATEVER", promotable=False, reason="x")
    with pytest.raises(ValueError):
        provider.EntitlementDecision(
            status="PROMOTABLE", promotable=True, reason="  "
        )
