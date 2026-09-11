"""V3 calendar contract tests (plan section 6 mandatory tests)."""

import pytest

from research.platform_v3.calendar_engine import (
    CalendarAuthorityError,
    CrossCheckEvidence,
    EquityRoutingRefused,
    OfficialDiscrepancyBlocked,
    SessionManifestBuilder,
    next_valid_session,
    package_pin,
)


@pytest.fixture(scope="module")
def pin():
    return package_pin()


@pytest.fixture(scope="module")
def builder(pin):
    return SessionManifestBuilder(pin)


def test_pin_is_content_addressed(pin):
    assert pin.package_version
    assert len(pin.package_source_digest) == 64


def test_session_manifest_shape_and_identity(builder):
    m1 = builder.build("XNYS", "stocks", "2026-07-01", "2026-07-10",
                       "America/New_York", generated_at_utc="t1")
    m2 = builder.build("XNYS", "stocks", "2026-07-01", "2026-07-10",
                       "America/New_York", generated_at_utc="t2")
    # generated-at excluded from identity
    assert m1["canonical_content_digest"] == m2["canonical_content_digest"]
    assert m1["calendar_package"]["version"]
    assert len(m1["calendar_package"]["source_digest"]) == 64
    assert all(s["open_utc"] and s["close_utc"] for s in m1["sessions"])


def test_us_federal_vs_exchange_holiday_difference(builder):
    # Columbus Day (2026-10-12): federal holiday, XNYS OPEN.
    m = builder.build("XNYS", "stocks", "2026-10-05", "2026-10-16",
                      "America/New_York")
    labels = {s["session"] for s in m["sessions"]}
    assert "2026-10-12" in labels


def test_early_close_flagged(builder):
    # 2025-11-28 (day after Thanksgiving) is an XNYS early close.
    m = builder.build("XNYS", "stocks", "2025-11-24", "2025-11-28",
                      "America/New_York")
    by_label = {s["session"]: s for s in m["sessions"]}
    assert by_label["2025-11-28"]["early_close"] is True
    assert by_label["2025-11-25"]["early_close"] is False


def test_weekend_non_session(builder):
    m = builder.build("XNYS", "stocks", "2026-07-11", "2026-07-12",
                      "America/New_York")
    assert m["sessions"] == []  # Sat + Sun


def test_lunch_break_market_fixture(builder):
    # XJPX has a lunch break; session rows carry break fields.
    m = builder.build("JPX", "stocks", "2026-07-06", "2026-07-10",
                      "Asia/Tokyo")
    assert m["sessions"], "expected Tokyo sessions"
    s = m["sessions"][0]
    assert s["break_start_utc"] is not None
    assert s["break_end_utc"] is not None


def test_release_to_next_valid_session(builder):
    assert next_valid_session(
        __import__("exchange_calendars").get_calendar(
            "XNYS", start="2026-07-01", end="2026-07-10"),
        "2026-07-03",  # Friday July 3 2026 = observed holiday, closed
    ) == "2026-07-06"


def test_package_upgrade_changes_digest(builder):
    m = builder.build("XNYS", "stocks", "2026-07-01", "2026-07-10",
                      "America/New_York")
    # simulate an upgraded package: same name, different content digest
    from research.platform_v3.calendar_engine import CalendarPin
    upgraded = SessionManifestBuilder(
        CalendarPin("exchange_calendars", "9.9.9", "f" * 64))
    m2 = upgraded.build("XNYS", "stocks", "2026-07-01", "2026-07-10",
                        "America/New_York")
    assert (m["calendar_package"]["source_digest"]
            != m2["calendar_package"]["source_digest"])
    # and the gate blocks on digest change
    assert m["canonical_content_digest"] != m2["canonical_content_digest"]


def test_official_discrepancy_fails_closed(builder):
    cc = CrossCheckEvidence(
        status="DISAGREEMENT", source_id="nyse-official",
        evidence_digest="a" * 64)
    with pytest.raises(OfficialDiscrepancyBlocked):
        builder.build("XNYS", "stocks", "2026-07-01", "2026-07-10",
                      "America/New_York", cross_check=cc)


def test_absent_cross_check_recorded_honestly(builder):
    m = builder.build("XNYS", "stocks", "2026-07-01", "2026-07-10",
                      "America/New_York")
    assert m["official_cross_check"]["status"] == "ABSENT"
    verdict = SessionManifestBuilder.verify_official_cross_check(m)
    assert verdict == "PASS_ABSENT_RECORDED"


def test_forex_and_crypto_refuse_equity_routing(builder):
    with pytest.raises(EquityRoutingRefused):
        builder.build("XNYS", "forex", "2026-07-01", "2026-07-10",
                      "America/New_York")
    with pytest.raises(EquityRoutingRefused):
        builder.build("XNYS", "crypto", "2026-07-01", "2026-07-10",
                      "America/New_York")
