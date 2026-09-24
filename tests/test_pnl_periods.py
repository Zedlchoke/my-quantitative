"""Daily/Weekly PNL tab tests (owner rule 2026-09-23).

Synthetic cases pin the calendar conventions exactly:

- mọi ranh giới kỳ đóng tại 00:00 (12 giờ đêm) giờ Việt Nam (UTC+7),
  i.e. 17:00Z của ngày trước;
- tuần bắt đầu 00:00 thứ Tư (bucket = [T4 00:00, T4 kế 00:00) VN);
- chuỗi cộng dồn: PnL kỳ = mark cuối kỳ − mark gần nhất trước đầu kỳ,
  kỳ đầu nối từ vốn gốc seed; tổng các ngày = PnL tháng = tổng các
  tuần (tính chất cộng性地 đúng khi mọi mark status OK);
- kỳ không có mark hợp lệ thì KHÔNG có số (fail-closed).

Fixture-runtime cases re-assert the same invariants against the REAL
engine snapshot served through the app envelope (skip when this
machine has no PROSPECTIVE-SHADOW-V1 runtime).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from dashboard_app.pnl import build_pnl_periods
from dashboard_app.page import PAGE_HTML_BYTES
from dashboard_app.store import SnapshotStore

FAMILIES = (
    "XSECT-FUND-CARRY-7D",
    "ILLIQ-AMIHUD-28D-W",
    "BASISLV-PREMFADE-28D",
)
SEED_TS = "2026-09-14T23:48:01Z"

# September 2026 ground truth: 15=Tue, 16=Wed, 30=Wed, Oct 1=Thu.
# 17:00Z == 00:00 (12 giờ đêm) giờ VN của ngày kế tiếp.
BOUNDARY_POINTS = (
    ("2026-09-15T16:59:59Z", 300_100.0),  # 23:59:59 VN Tue 15/09
    ("2026-09-15T17:00:00Z", 300_200.0),  # 00:00 VN Wed 16/09
    ("2026-09-16T10:00:00Z", 300_500.0),
    ("2026-09-30T16:59:59Z", 301_000.0),  # 23:59:59 VN Wed 30/09
    ("2026-09-30T17:00:00Z", 301_100.0),  # 00:00 VN Thu 01/10
)
NOW_AFTER_ALL = datetime(2026, 10, 1, 0, 0, 0, tzinfo=timezone.utc)


def _valuation(points) -> dict:
    return {
        "families": {
            fam: {"seeds": [{"ts_utc": SEED_TS, "equity": 100_000.0}]}
            for fam in FAMILIES
        },
        "combined": {
            "series": [
                {"ts": ts, "status": "OK", "equity": eq} for ts, eq in points
            ]
        },
    }


def _by_key(rows) -> dict:
    return {row["key"]: row for row in rows}


# ----------------------------------------------------------------------
# Ranh giới ngày / tuần / tháng tại 00:00 giờ VN
# ----------------------------------------------------------------------
def test_day_month_week_roll_at_vn_midnight():
    pp = build_pnl_periods(
        _valuation(BOUNDARY_POINTS), now_dt=NOW_AFTER_ALL
    )
    daily = _by_key(pp["daily"])
    # 16:59:59Z Tue vẫn là ngày 15/09 VN; 17:00:00Z đã là 16/09 VN
    assert daily["2026-09-15"]["pnl_usdt"] == pytest.approx(100.0, abs=1e-9)
    assert daily["2026-09-15"]["start_from_seed"] is True
    # 16/09 chain từ mark cuối TRƯỚC 00:00 VN (16:59:59Z của 15/09):
    # mark 17:00:00Z đã thuộc ngày 16/09
    assert daily["2026-09-16"]["pnl_usdt"] == pytest.approx(400.0, abs=1e-9)
    assert daily["2026-09-16"]["start_mark_utc"] == "2026-09-15T16:59:59Z"
    assert daily["2026-09-16"]["marks"] == 2
    # tháng đổi tại 00:00 VN ngày 1: mark 17:00:00Z 30/09 thuộc tháng 10
    assert "2026-09-30" in daily and "2026-10-01" in daily
    assert daily["2026-09-30"]["pnl_usdt"] == pytest.approx(500.0, abs=1e-9)
    assert daily["2026-10-01"]["pnl_usdt"] == pytest.approx(100.0, abs=1e-9)

    monthly = _by_key(pp["monthly"])
    assert monthly["2026-09"]["pnl_usdt"] == pytest.approx(1_000.0, abs=1e-9)
    assert monthly["2026-09"]["end_equity"] == pytest.approx(301_000.0, abs=1e-9)
    assert monthly["2026-10"]["pnl_usdt"] == pytest.approx(100.0, abs=1e-9)
    assert monthly["2026-10"]["start_mark_utc"] == "2026-09-30T16:59:59Z"

    weekly = _by_key(pp["weekly"])
    # tuần bắt đầu thứ Tư: 15/09 (Ba) thuộc tuần T4 09/09;
    # 16/09 (T4) mở tuần mới; 01/10 (Năm) thuộc tuần T4 30/09
    assert set(weekly) == {
        "2026-09-09", "2026-09-16", "2026-09-30",
    }
    assert weekly["2026-09-09"]["pnl_usdt"] == pytest.approx(100.0, abs=1e-9)
    # tuần T4 16/09 chain từ mark cuối trước 00:00 VN thứ Tư (16:59:59Z)
    assert weekly["2026-09-16"]["pnl_usdt"] == pytest.approx(400.0, abs=1e-9)
    # chuỗi nhảy cóc qua tuần 23/09 trống: nối từ mark 16/09
    assert weekly["2026-09-30"]["pnl_usdt"] == pytest.approx(600.0, abs=1e-9)
    assert weekly["2026-09-30"]["start_mark_utc"] == "2026-09-16T10:00:00Z"


def test_bucket_windows_and_weekday_anchor():
    pp = build_pnl_periods(_valuation(BOUNDARY_POINTS))
    for row in pp["weekly"]:
        start = datetime.strptime(row["start_local_date"], "%Y-%m-%d").date()
        end = datetime.strptime(
            row["end_local_date_exclusive"], "%Y-%m-%d"
        ).date()
        assert start.weekday() == 2, "tuần phải bắt đầu thứ Tư"
        assert (end - start).days == 7
        # start_utc == 00:00 VN của thứ Tư == 17:00Z của thứ Ba
        start_utc = datetime.strptime(row["start_utc"], "%Y-%m-%dT%H:%M:%SZ")
        assert start_utc.weekday() == 1 and start_utc.hour == 17
    for row in pp["monthly"]:
        assert row["start_local_date"].endswith("-01")


# ----------------------------------------------------------------------
# Tính chất cộng性地 chuỗi
# ----------------------------------------------------------------------
def test_chain_additivity_daily_month_week():
    pp = build_pnl_periods(_valuation(BOUNDARY_POINTS))
    total_move = 301_100.0 - 300_000.0
    for kind in ("daily", "weekly", "monthly"):
        rows = pp[kind]
        assert sum(r["pnl_usdt"] for r in rows) == pytest.approx(
            total_move, abs=1e-9
        ), kind
    # chuỗi liên tục: start kỳ sau == end kỳ trước (kỳ trống bị bỏ qua)
    for kind in ("daily", "weekly", "monthly"):
        rows = pp[kind]
        for prev, cur in zip(rows, rows[1:]):
            assert cur["start_equity"] == pytest.approx(
                prev["end_equity"], abs=1e-9
            )
            assert cur["start_mark_utc"] == prev["end_mark_utc"]


def test_gap_day_has_no_row_and_next_day_chains_back():
    points = (
        ("2026-09-21T02:00:00Z", 300_400.0),  # Mon
        # 22/09: không có mark nào
        ("2026-09-23T02:00:00Z", 300_600.0),  # Wed
    )
    pp = build_pnl_periods(_valuation(points))
    daily = _by_key(pp["daily"])
    assert set(daily) == {"2026-09-21", "2026-09-23"}
    assert daily["2026-09-21"]["pnl_usdt"] == pytest.approx(400.0, abs=1e-9)
    # ngày 23 nối thẳng về mark cuối ngày 21 (không nội suy ngày 22)
    assert daily["2026-09-23"]["pnl_usdt"] == pytest.approx(200.0, abs=1e-9)
    assert daily["2026-09-23"]["start_mark_utc"] == "2026-09-21T02:00:00Z"


# ----------------------------------------------------------------------
# Fail-closed đầu vào
# ----------------------------------------------------------------------
def test_non_ok_and_non_finite_points_are_excluded():
    series = [
        {"ts": "2026-09-16T02:00:00Z", "status": "OK", "equity": 300_100.0},
        {"ts": "2026-09-16T02:05:00Z",
         "status": "UNAVAILABLE_FAIL_CLOSED", "equity": None},
        {"ts": "2026-09-16T02:10:00Z", "status": "OK",
         "equity": float("nan")},
        {"ts": "not-a-timestamp", "status": "OK", "equity": 999_999.0},
        {"ts": "2026-09-16T02:15:00Z", "status": "OK", "equity": 300_200.0},
    ]
    valuation = {
        "families": {
            fam: {"seeds": [{"ts_utc": SEED_TS, "equity": 100_000.0}]}
            for fam in FAMILIES
        },
        "combined": {"series": series},
    }
    pp = build_pnl_periods(valuation)
    assert pp["point_count"] == 2
    daily = _by_key(pp["daily"])
    # cả hai mark dùng được đều nằm trong ngày 16/09 VN
    assert set(daily) == {"2026-09-16"}
    assert daily["2026-09-16"]["marks"] == 2
    assert daily["2026-09-16"]["pnl_usdt"] == pytest.approx(200.0, abs=1e-9)


def test_no_seed_baseline_first_period_is_none_not_zero():
    valuation = {
        "families": {fam: {"seeds": []} for fam in FAMILIES},
        "combined": {
            "series": [
                {"ts": ts, "status": "OK", "equity": eq}
                for ts, eq in BOUNDARY_POINTS[:3]
            ]
        },
    }
    pp = build_pnl_periods(valuation)
    assert pp["baseline_equity"] is None
    daily = _by_key(pp["daily"])
    assert daily["2026-09-15"]["pnl_usdt"] is None
    assert daily["2026-09-15"]["pnl_pct"] is None
    # kỳ sau vẫn chain được từ mark của kỳ đầu (không cần baseline)
    assert daily["2026-09-16"]["pnl_usdt"] == pytest.approx(400.0, abs=1e-9)


def test_empty_series_yields_empty_periods():
    pp = build_pnl_periods({"families": {}, "combined": {"series": []}})
    assert pp["daily"] == [] and pp["weekly"] == [] and pp["monthly"] == []
    assert pp["last_mark_utc"] is None


def test_open_flag_depends_on_now():
    before_end = datetime(2026, 9, 16, 12, 0, 0, tzinfo=timezone.utc)
    pp = build_pnl_periods(
        _valuation(BOUNDARY_POINTS[:3]), now_dt=before_end
    )
    daily = _by_key(pp["daily"])
    assert daily["2026-09-16"]["open"] is True
    assert daily["2026-09-15"]["open"] is False
    pp_closed = build_pnl_periods(
        _valuation(BOUNDARY_POINTS), now_dt=NOW_AFTER_ALL
    )
    assert _by_key(pp_closed["daily"])["2026-09-30"]["open"] is False


# ----------------------------------------------------------------------
# Envelope + trang (real runtime; skip khi máy không có runtime)
# ----------------------------------------------------------------------
def _make_store(paths, engine) -> SnapshotStore:
    return SnapshotStore(paths, engine=engine)


def _assert_chain_invariants(pp) -> None:
    assert pp["schema"] == "shv1_pnl_periods_v1"
    assert pp["tz"] == "Asia/Ho_Chi_Minh"
    total_flows = sum(
        f["amount_usdt"] or 0.0 for f in pp.get("capital_flows") or []
    )
    for kind in ("daily", "weekly", "monthly"):
        rows = pp[kind]
        for prev, cur in zip(rows, rows[1:]):
            assert cur["start_equity"] == pytest.approx(
                prev["end_equity"], abs=1e-6
            )
        for row in rows:
            if row["pnl_usdt"] is not None:
                flows = row.get("capital_flows_usdt") or 0.0
                assert row["pnl_usdt"] == pytest.approx(
                    row["end_equity"] - row["start_equity"] - flows, abs=1e-6
                )
    if pp["baseline_equity"] is not None:
        total = (
            pp["daily"][-1]["end_equity"]
            - pp["baseline_equity"]
            - total_flows
        )
        for kind in ("daily", "weekly", "monthly"):
            assert sum(r["pnl_usdt"] for r in pp[kind]) == pytest.approx(
                total, abs=1e-6
            ), kind


def test_envelope_carries_pnl_periods(fixture_runtime, engine):
    paths, ctx = fixture_runtime
    store = _make_store(paths, engine)
    now = ctx["last_mark_ts"]
    store.refresh(now_iso=now)
    env = store.envelope(now_iso=now)
    pp = env["app"]["pnl_periods"]
    _assert_chain_invariants(pp)
    assert pp["daily"], "fixture marks must span at least one VN day"
    assert pp["daily"][-1]["open"] is True
    assert pp["weekly"] and pp["monthly"]
    for row in pp["weekly"]:
        start = datetime.strptime(row["start_local_date"], "%Y-%m-%d").date()
        assert start.weekday() == 2


def test_page_html_contains_pnl_tab_surface():
    assert b"Daily/Weekly PNL" in PAGE_HTML_BYTES
    assert b'id="main-pnl"' in PAGE_HTML_BYTES
    assert b'id="calgrid"' in PAGE_HTML_BYTES
    assert b"renderPnl" in PAGE_HTML_BYTES
