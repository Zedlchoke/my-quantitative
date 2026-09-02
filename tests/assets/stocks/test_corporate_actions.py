"""Synthetic-golden tests for the corporate-actions engine (owner: A4, SD2).

Hard-coded goldens: a 2:1 split ex-date halving raw prices and doubling
shares, a cash-dividend ex-date diverging the total-return research path
from the raw fill path, an explicit (never implicit) adjustment policy,
canonical order-independent manifest digests, and fail-closed BTO/AMC
earnings timing.  The suite performs zero repo writes.
"""

from __future__ import annotations

import dataclasses
from datetime import date, datetime, timezone

import pytest

from research.assets.stocks.calendar import US_EQUITY_REGULAR_V1
from research.assets.stocks.corporate_actions import (
    ACTION_CASH_DIVIDEND,
    ACTION_SPLIT,
    EARNINGS_AMC,
    EARNINGS_BTO,
    EARNINGS_UNKNOWN,
    CorporateAction,
    CorporateActionEngine,
    EarningsTiming,
    POLICY_RAW,
    POLICY_TOTAL_RETURN,
    PricePoint,
    classify_earnings_timestamp,
    corporate_action_manifest_digest,
    resolve_effective_at,
    sort_actions,
)

UTC = timezone.utc

# Golden digests over the sorted immutable action records below.
GOLDEN_MANIFEST_DIGEST = (
    "2a1bc75c4df92716457edc14369debd83163e9546da54f724f0efd11008b4d10"
)
GOLDEN_TEST_ONLY_DIGEST = (
    "6ab7292c01f128a31ad73c8eeeea1c463e12e922013005ef89b39f8e7558c17d"
)


def utc(*args: int) -> datetime:
    return datetime(*args, tzinfo=UTC)


def make_actions() -> list[CorporateAction]:
    return [
        CorporateAction(
            security_id="TEST",
            action_type=ACTION_SPLIT,
            ex_date=date(2024, 6, 10),
            split_ratio=2.0,
            declared_date=date(2024, 5, 16),
            record_date=date(2024, 6, 10),
            action_id="TEST-SPLIT-2024",
            label="2-for-1 forward split",
        ),
        CorporateAction(
            security_id="TEST",
            action_type=ACTION_CASH_DIVIDEND,
            ex_date=date(2024, 3, 15),
            cash_amount=1.0,
            declared_date=date(2024, 2, 15),
            record_date=date(2024, 3, 15),
            payment_date=date(2024, 3, 28),
            action_id="TEST-DIV-2024Q1",
            label="quarterly cash dividend",
        ),
    ]


def make_engine(policy=POLICY_TOTAL_RETURN, actions=None) -> CorporateActionEngine:
    return CorporateActionEngine(
        make_actions() if actions is None else actions,
        calendar=US_EQUITY_REGULAR_V1,
        price_adjustment_policy=policy,
    )


def make_points() -> list[PricePoint]:
    return [
        PricePoint(utc(2024, 3, 14, 21, 0), 100.0),  # last close before dividend ex
        PricePoint(utc(2024, 3, 15, 20, 0), 99.0),  # dividend ex-day close, raw drops
        PricePoint(utc(2024, 6, 7, 20, 0), 100.0),  # last close before split ex
        PricePoint(utc(2024, 6, 10, 20, 0), 50.0),  # split ex-day close, raw halves
    ]


# --- record construction: immutable and fail-closed ------------------------------ #
def test_action_records_are_immutable():
    action = make_actions()[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        action.split_ratio = 3.0  # type: ignore[misc]


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"action_type": "MERGER"}, "action_type must be one of"),
        (
            {
                "action_type": ACTION_CASH_DIVIDEND,
                "split_ratio": None,
                "cash_amount": None,
            },
            "cash_amount must be a real number",
        ),
        ({"action_type": ACTION_SPLIT, "split_ratio": 1.0}, "no-op"),
        ({"action_type": ACTION_SPLIT, "split_ratio": -2.0}, "must be > 0"),
        (
            {"action_type": ACTION_SPLIT, "split_ratio": None, "cash_amount": 0.5},
            "SPLIT must not carry cash_amount",
        ),
        (
            {"action_type": ACTION_CASH_DIVIDEND, "split_ratio": 2.0},
            "must not carry split_ratio",
        ),
        (
            {"action_type": ACTION_SPLIT, "cash_amount": 0.5},
            "SPLIT must not carry cash_amount",
        ),
    ],
)
def test_malformed_actions_fail_closed(kwargs, match):
    base = {
        "security_id": "TEST",
        "action_type": ACTION_SPLIT,
        "ex_date": date(2024, 6, 10),
        "split_ratio": 2.0,
    }
    with pytest.raises(ValueError, match=match):
        CorporateAction(**{**base, **kwargs})


def test_effective_at_utc_must_be_tz_aware_and_on_ex_date():
    with pytest.raises(ValueError, match="tz-aware"):
        CorporateAction(
            security_id="TEST",
            action_type=ACTION_SPLIT,
            ex_date=date(2024, 6, 10),
            split_ratio=2.0,
            effective_at_utc=datetime(2024, 6, 10, 13, 30),  # naive
        )
    with pytest.raises(ValueError, match="must equal ex_date"):
        CorporateAction(
            security_id="TEST",
            action_type=ACTION_SPLIT,
            ex_date=date(2024, 6, 10),
            split_ratio=2.0,
            effective_at_utc=utc(2024, 6, 11, 13, 30),
        )


def test_with_effective_at_returns_immutable_copy():
    action = make_actions()[0]
    copy = action.with_effective_at(utc(2024, 6, 10, 14, 0))
    assert copy is not action
    assert copy.effective_at_utc == utc(2024, 6, 10, 14, 0)
    assert action.effective_at_utc is None


# --- ex/effective timestamp resolution --------------------------------------------- #
def test_effective_moment_defaults_to_ex_date_open():
    split, div = make_actions()
    # 2024-06-10 and 2024-03-15 are EDT sessions: open 09:30 ET == 13:30Z.
    assert resolve_effective_at(split, US_EQUITY_REGULAR_V1) == utc(2024, 6, 10, 13, 30)
    assert resolve_effective_at(div, US_EQUITY_REGULAR_V1) == utc(2024, 3, 15, 13, 30)


def test_effective_moment_fails_closed_on_non_session_ex_date():
    action = CorporateAction(
        security_id="TEST",
        action_type=ACTION_SPLIT,
        ex_date=date(2024, 7, 4),  # market holiday
        split_ratio=2.0,
    )
    with pytest.raises(ValueError, match="not a session day"):
        resolve_effective_at(action, US_EQUITY_REGULAR_V1)


# --- manifest digest: canonical sha256 over sorted records -------------------------- #
def test_manifest_digest_matches_pinned_golden_and_is_order_independent():
    actions = make_actions()
    digest = corporate_action_manifest_digest(actions)
    assert digest == GOLDEN_MANIFEST_DIGEST
    assert corporate_action_manifest_digest(list(reversed(actions))) == digest


def test_manifest_digest_is_sensitive_to_every_relevant_change():
    base = make_actions()
    tweaked = make_actions()
    tweaked[1] = dataclasses.replace(tweaked[1], cash_amount=1.01)
    assert corporate_action_manifest_digest(tweaked) != corporate_action_manifest_digest(base)

    re_dated = make_actions()
    re_dated[0] = dataclasses.replace(re_dated[0], ex_date=date(2024, 6, 7))
    assert corporate_action_manifest_digest(re_dated) != corporate_action_manifest_digest(base)

    re_labeled = make_actions()
    re_labeled[0] = dataclasses.replace(re_labeled[0], label="3-for-1 forward split")
    assert corporate_action_manifest_digest(re_labeled) != corporate_action_manifest_digest(base)


def test_engine_manifest_digest_full_vs_per_security():
    engine = make_engine()
    assert engine.corporate_action_manifest_digest() == GOLDEN_MANIFEST_DIGEST
    assert engine.corporate_action_manifest_digest("TEST") == GOLDEN_MANIFEST_DIGEST
    other = CorporateAction(
        security_id="OTHER",
        action_type=ACTION_SPLIT,
        ex_date=date(2024, 6, 10),
        split_ratio=3.0,
    )
    mixed = make_engine(actions=make_actions() + [other])
    assert mixed.corporate_action_manifest_digest() != GOLDEN_MANIFEST_DIGEST
    assert mixed.corporate_action_manifest_digest("TEST") == GOLDEN_MANIFEST_DIGEST
    # Records come back in canonical (ex_date) order regardless of input order.
    assert mixed.actions_for("TEST") == sort_actions(make_actions())


# --- policy is explicit, never implicit ---------------------------------------------- #
def test_price_adjustment_policy_is_required_and_never_implicit():
    with pytest.raises(TypeError):
        CorporateActionEngine(make_actions(), calendar=US_EQUITY_REGULAR_V1)  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="never implicit"):
        CorporateActionEngine(
            make_actions(), calendar=US_EQUITY_REGULAR_V1, price_adjustment_policy=None
        )
    with pytest.raises(ValueError, match="must be one of"):
        make_engine(policy="ADJUSTED")
    assert make_engine(policy=POLICY_RAW).price_adjustment_policy == POLICY_RAW
    assert make_engine(policy=POLICY_TOTAL_RETURN).price_adjustment_policy == POLICY_TOTAL_RETURN


def test_engine_requires_calendar():
    with pytest.raises(ValueError, match="calendar is required"):
        CorporateActionEngine(make_actions(), calendar=None, price_adjustment_policy=POLICY_RAW)


# --- split application golden --------------------------------------------------------- #
def test_two_for_one_split_halves_price_and_doubles_shares():
    engine = make_engine()
    split = next(
        action
        for action in engine.actions_for("TEST")
        if action.action_type == ACTION_SPLIT
    )
    moment = engine.effective_moment(split)
    assert moment == utc(2024, 6, 10, 13, 30)  # ex-date session open, EDT
    application = engine.apply_to_position(
        "TEST", shares=10, raw_price_per_share=100.0, at_utc=moment
    )
    assert application.shares_before == 10
    assert application.shares_after == 20  # 2:1 doubles shares
    assert application.value_before == pytest.approx(1000.0)
    assert application.value_after == pytest.approx(1000.0)  # value preserved
    event = application.cash_events[0]
    assert event.reference_price_before == 100.0
    assert event.reference_price_after == 50.0  # raw prices halve
    assert event.cash_to_position == 0.0
    with pytest.raises(ValueError, match="no TEST action is effective exactly"):
        engine.apply_to_position(
            "TEST", shares=10, raw_price_per_share=100.0, at_utc=utc(2024, 6, 9, 13, 30)
        )


def test_split_factors_between_dates():
    engine = make_engine()
    assert (
        engine.share_multiplier_between("TEST", utc(2024, 6, 1), utc(2024, 6, 11)) == 2.0
    )
    assert (
        engine.price_adjustment_factor_between("TEST", utc(2024, 6, 1), utc(2024, 6, 11))
        == 0.5
    )
    assert (
        engine.share_multiplier_between("TEST", utc(2024, 6, 11), utc(2024, 6, 30)) == 1.0
    )


def test_dividend_application_accrues_cash_without_touching_shares():
    engine = make_engine()
    div = next(
        action
        for action in engine.actions_for("TEST")
        if action.action_type == ACTION_CASH_DIVIDEND
    )
    assert div.action_type == ACTION_CASH_DIVIDEND
    moment = engine.effective_moment(div)
    application = engine.apply_to_position(
        "TEST", shares=20, raw_price_per_share=50.0, at_utc=moment
    )
    assert application.shares_after == 20
    assert application.cash_events[0].cash_to_position == pytest.approx(20.0)
    assert application.cash_events[0].cash_amount == pytest.approx(1.0)


# --- raw fill path vs total-return research path ---------------------------------------- #
def test_total_return_path_diverges_from_raw_path_at_event_boundaries():
    engine = make_engine(policy=POLICY_TOTAL_RETURN)
    path = engine.price_path("TEST", make_points())
    adjusted = [point.adjusted_close for point in path]
    # Dividend factor (1 - 1/100) and split factor (1/2) applied pre-event.
    assert adjusted == pytest.approx([49.5, 49.5, 50.0, 50.0])
    assert [point.raw_close for point in path] == [100.0, 99.0, 100.0, 50.0]
    assert path[0].cumulative_factor == pytest.approx(0.495)
    assert path[-1].cumulative_factor == pytest.approx(1.0)
    # The total-return path is continuous across the split boundary where
    # the raw fill path halves: 50.0 -> 50.0.


def test_raw_policy_returns_prices_untouched():
    engine = make_engine(policy=POLICY_RAW)
    path = engine.price_path("TEST", make_points())
    for point in path:
        assert point.adjusted_close == point.raw_close
        assert point.cumulative_factor == 1.0


def test_total_return_adjustment_without_previous_close_fails_closed():
    engine = make_engine(policy=POLICY_TOTAL_RETURN)
    only_ex_day = [PricePoint(utc(2024, 3, 15, 20, 0), 99.0)]
    with pytest.raises(ValueError, match="requires a raw close strictly before"):
        engine.price_path("TEST", only_ex_day)


# --- reconciliation helper --------------------------------------------------------------- #
def test_reconciliation_explains_raw_vs_total_return_divergence():
    engine = make_engine(policy=POLICY_TOTAL_RETURN)
    records = engine.reconcile_raw_vs_total_return("TEST", make_points())
    assert [record.ex_date for record in records] == [date(2024, 3, 15), date(2024, 6, 10)]

    dividend, split = records
    assert dividend.action_type == ACTION_CASH_DIVIDEND
    assert dividend.raw_return == pytest.approx(-0.01)  # raw path drops by the dividend
    assert dividend.total_return == pytest.approx(0.0)  # research path does not
    assert dividend.dividend_yield == pytest.approx(0.01)
    assert dividend.explained is True
    assert dividend.boundary_prev_utc == utc(2024, 3, 14, 21, 0)

    assert split.action_type == ACTION_SPLIT
    assert split.raw_return == pytest.approx(-0.5)  # raw price halves
    assert split.total_return == pytest.approx(0.0)  # adjusted path is flat
    assert split.price_factor == pytest.approx(2.0)
    assert split.explained is True


def test_reconciliation_fails_closed_on_missing_boundary():
    engine = make_engine()
    records = engine.reconcile_raw_vs_total_return(
        "TEST", [PricePoint(utc(2024, 6, 10, 20, 0), 50.0)]
    )
    assert all(record.explained is False for record in records)
    assert all("fail closed" in record.note for record in records)


# --- earnings timing: BTO / AMC / UNKNOWN fail-closed ------------------------------------- #
def test_earnings_bto_and_amc_goldens_on_edt_session():
    cal = US_EQUITY_REGULAR_V1
    # 2024-03-15: EDT session [13:30Z, 20:00Z) == [09:30, 16:00) ET.
    assert classify_earnings_timestamp(utc(2024, 3, 15, 12, 0), cal).value == EARNINGS_BTO
    assert classify_earnings_timestamp(utc(2024, 3, 15, 21, 30), cal).value == EARNINGS_AMC
    # Exactly at the close classifies AMC; exactly at the open is ambiguous.
    assert classify_earnings_timestamp(utc(2024, 3, 15, 20, 0), cal).value == EARNINGS_AMC
    assert (
        classify_earnings_timestamp(utc(2024, 3, 15, 13, 30), cal).value == EARNINGS_UNKNOWN
    )


def test_earnings_unknown_fails_closed_with_reason():
    cal = US_EQUITY_REGULAR_V1
    inside = classify_earnings_timestamp(utc(2024, 3, 15, 15, 0), cal)
    assert inside.value == EARNINGS_UNKNOWN
    assert inside.is_classified is False
    assert "inside the regular session" in inside.reason
    with pytest.raises(ValueError, match="unclassified"):
        inside.require_classified()

    weekend = classify_earnings_timestamp(utc(2024, 3, 16, 14, 0), cal)
    assert weekend.value == EARNINGS_UNKNOWN
    assert "non-session ET date 2024-03-16" in weekend.reason

    holiday = classify_earnings_timestamp(utc(2025, 1, 9, 14, 0), cal)  # Carter mourning day
    assert holiday.value == EARNINGS_UNKNOWN

    with pytest.raises(ValueError, match="tz-aware"):
        classify_earnings_timestamp(datetime(2024, 3, 15, 12, 0), cal)  # naive


def test_est_session_earnings_boundaries_use_dst_correct_bounds():
    cal = US_EQUITY_REGULAR_V1
    # 2024-01-16: EST session [14:30Z, 21:00Z).
    assert classify_earnings_timestamp(utc(2024, 1, 16, 14, 0), cal).value == EARNINGS_BTO
    assert classify_earnings_timestamp(utc(2024, 1, 16, 14, 29), cal).value == EARNINGS_BTO
    assert classify_earnings_timestamp(utc(2024, 1, 16, 14, 30), cal).value == EARNINGS_UNKNOWN
    assert classify_earnings_timestamp(utc(2024, 1, 16, 21, 0), cal).value == EARNINGS_AMC


def test_engine_bound_earnings_classification_and_timing_value_object():
    engine = make_engine()
    assert engine.classify_earnings(utc(2024, 3, 15, 12, 0)).value == EARNINGS_BTO
    assert engine.classify_earnings(utc(2024, 3, 15, 21, 30)).value == EARNINGS_AMC
    timing = EarningsTiming(EARNINGS_BTO)
    assert timing.require_classified() == EARNINGS_BTO
    with pytest.raises(ValueError, match="non-empty reason"):
        EarningsTiming(EARNINGS_UNKNOWN)
    with pytest.raises(ValueError, match="must not carry a reason"):
        EarningsTiming(EARNINGS_AMC, reason="should not be here")
    with pytest.raises(ValueError, match="must be one of"):
        EarningsTiming("INTRADAY")


# --- no repo writes: the module exposes nothing that persists ------------------------------ #
def test_engine_records_do_not_alias_inputs():
    actions = make_actions()
    engine = make_engine(actions=actions)
    assert engine.actions is not actions
    assert engine.actions == sort_actions(actions)
