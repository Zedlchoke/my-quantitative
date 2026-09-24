"""Combined-history composition across a mid-program sleeve mount.

Pins the owner rules of 2026-09-24 (sleeve 4 BTC4H-BANDRIDGE):

- Lịch sử TRƯỚC thời điểm mount giữ nguyên là chuỗi 3 sleeve sáng lập
  ($300,000 vốn gốc) — không bị xóa, không bị viết lại;
- sleeve mounted sau góp mặt từ mark đầu tiên của nó và khoản vốn
  +$100,000 là CAPITAL FLOW — không bao giờ hiện thành lợi nhuận;
- strict per-timestamp: một sleeve đã mount thiếu mark hợp lệ tại một
  mốc => combined point là GAP (fail-closed, không cộng từng phần,
  không nội suy);
- tất cả số liệu lấy từ API hiện có (per-family series + seeds của
  engine snapshot) — không bịa.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from dashboard_app.pnl import (
    build_pnl_periods,
    compose_combined_history,
)

FOUNDING = (
    "XSECT-FUND-CARRY-7D",
    "ILLIQ-AMIHUD-28D-W",
    "BASISLV-PREMFADE-28D",
)
LATE = "BTC4H-BANDRIDGE"
SEED_TS = "2026-09-14T23:48:01Z"


def _fam(points, seed_equity=100_000.0, seed_ts=SEED_TS):
    return {
        "seeds": [{"ts_utc": seed_ts, "equity": seed_equity}],
        "series": [
            {"ts": ts, "status": st, "equity": eq} for ts, eq, st in points
        ],
    }


def _valuation_3plus1(late_first="2026-09-24T01:10:00Z"):
    """3 founding sleeves with marks 09-15..09-24; the late sleeve has
    marks only from ``late_first`` (flat at seed: 0 fill)."""
    return {
        "families": {
            FOUNDING[0]: _fam([
                ("2026-09-15T02:10:00Z", 100_000.0, "OK"),
                ("2026-09-16T02:10:00Z", 99_900.0, "OK"),
                ("2026-09-23T23:55:00Z", 99_800.0, "OK"),
                ("2026-09-24T01:10:00Z", 99_850.0, "OK"),
                ("2026-09-24T03:55:00Z", 99_712.20, "OK"),
            ]),
            FOUNDING[1]: _fam([
                ("2026-09-15T02:10:00Z", 100_000.0, "OK"),
                ("2026-09-16T02:10:00Z", 100_100.0, "OK"),
                ("2026-09-23T23:55:00Z", 98_900.0, "OK"),
                ("2026-09-24T01:10:00Z", 98_950.0, "OK"),
                ("2026-09-24T03:55:00Z", 98_781.06, "OK"),
            ]),
            FOUNDING[2]: _fam([
                ("2026-09-15T02:10:00Z", 100_000.0, "OK"),
                ("2026-09-16T02:10:00Z", 100_000.0, "OK"),
                ("2026-09-23T23:55:00Z", 99_900.0, "OK"),
                ("2026-09-24T01:10:00Z", 100_000.0, "OK"),
                ("2026-09-24T03:55:00Z", 100_000.0, "OK"),
            ]),
            LATE: _fam([
                (late_first, 100_000.0, "OK"),
                ("2026-09-24T03:55:00Z", 100_000.0, "OK"),
            ]),
        },
        "combined": {"series": []},
    }


def _ts(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(
        timezone.utc
    )


# ----------------------------------------------------------------------
# History preservation + flow semantics
# ----------------------------------------------------------------------
def test_pre_mount_history_is_the_3_sleeve_series():
    hist = compose_combined_history(_valuation_3plus1())
    assert hist["mode"] == "families"
    assert set(hist["founding_families"]) == set(FOUNDING)
    assert hist["baseline_equity"] == pytest.approx(300_000.0)
    by_ts = {p["ts"]: p for p in hist["series"]}
    # trước mount: strict sum của ĐÚNG 3 sleeve sáng lập
    p = by_ts["2026-09-16T02:10:00Z"]
    assert p["status"] == "OK"
    assert p["equity"] == pytest.approx(300_000.0)
    assert set(p["contributions"]) == set(FOUNDING)
    assert LATE not in p.get("contributions", {})


def test_late_sleeve_enters_exactly_at_its_first_mark():
    hist = compose_combined_history(_valuation_3plus1())
    by_ts = {p["ts"]: p for p in hist["series"]}
    before = by_ts["2026-09-23T23:55:00Z"]
    after = by_ts["2026-09-24T01:10:00Z"]
    assert before["equity"] == pytest.approx(298_600.0)
    assert after["equity"] == pytest.approx(398_800.0)
    assert set(after["contributions"]) == set(FOUNDING) | {LATE}


def test_capital_flow_is_recorded_and_not_profit():
    hist = compose_combined_history(_valuation_3plus1())
    assert len(hist["capital_flows"]) == 1
    flow = hist["capital_flows"][0]
    assert flow["family_id"] == LATE
    assert flow["amount_usdt"] == pytest.approx(100_000.0)
    assert flow["ts_utc"] == "2026-09-24T01:10:00Z"
    # ngày mount: PnL phải TRỪ vốn thêm — không được thành +$100k
    pp = build_pnl_periods(_valuation_3plus1())
    daily = {r["key"]: r for r in pp["daily"]}
    d24 = daily["2026-09-24"]
    end_eq = 99_712.20 + 98_781.06 + 100_000.0 + 100_000.0  # 398,493.26
    # mark 2026-09-23T23:55Z là 06:55 giờ VN 24/09 → thuộc bucket 24/09;
    # bucket 24/09 nối từ mark cuối bucket 16/09 (equity 300,000)
    assert d24["start_equity"] == pytest.approx(300_000.0)
    assert d24["capital_flows_usdt"] == pytest.approx(100_000.0)
    assert d24["pnl_usdt"] == pytest.approx(end_eq - 300_000.0 - 100_000.0)
    assert d24["pnl_usdt"] == pytest.approx(-1_506.74, abs=0.01)
    assert d24["pnl_usdt"] < 1_000  # không biến vốn thành lợi nhuận
    # cộng tính: tổng PnL các ngày = last_end − baseline − tổng flow
    total = sum(r["pnl_usdt"] for r in pp["daily"])
    assert total == pytest.approx(
        pp["daily"][-1]["end_equity"] - 300_000.0 - 100_000.0
    )


def test_gap_when_a_mounted_sleeve_misses_a_mark():
    val = _valuation_3plus1()
    val["families"][FOUNDING[1]]["series"] = [
        p for p in val["families"][FOUNDING[1]]["series"]
        if p["ts"] != "2026-09-24T01:10:00Z"
    ]
    hist = compose_combined_history(val)
    by_ts = {p["ts"]: p for p in hist["series"]}
    gap = by_ts["2026-09-24T01:10:00Z"]
    assert gap["status"] == "UNAVAILABLE_FAIL_CLOSED"
    assert gap["equity"] is None
    assert FOUNDING[1] in gap["reason"]


def test_no_partial_history_within_founding_tolerance_skew():
    val = _valuation_3plus1()
    # một sleeve sáng lập start lệch 30s (trong tolerance 60s): mốc
    # trước khi đủ mặt founding phải là GAP, không cộng từng phần
    val["families"][FOUNDING[2]]["series"][0]["ts"] = "2026-09-15T02:10:30Z"
    hist = compose_combined_history(val)
    by_ts = {p["ts"]: p for p in hist["series"]}
    first = by_ts["2026-09-15T02:10:00Z"]
    assert first["status"] == "UNAVAILABLE_FAIL_CLOSED"
    assert "founding" in first["reason"]
    complete = by_ts["2026-09-16T02:10:00Z"]
    assert complete["status"] == "OK"


def test_misaligned_founding_seeds_fail_closed_baseline():
    val = _valuation_3plus1()
    val["families"][FOUNDING[2]]["seeds"] = [
        {"ts_utc": "2026-09-15T00:00:00Z", "equity": 100_000.0}
    ]
    hist = compose_combined_history(val)
    # baseline từ seed lệch dấu thời gian => không có baseline (chuỗi
    # vẫn chạy, bucket đầu không có số)
    assert hist["baseline_equity"] is None
    pp = build_pnl_periods(val)
    assert pp["baseline_equity"] is None


def test_late_sleeve_without_seed_record_fails_closed_pnl():
    val = _valuation_3plus1()
    del val["families"][LATE]["seeds"]
    hist = compose_combined_history(val)
    flow = hist["capital_flows"][0]
    assert flow["amount_usdt"] is None
    pp = build_pnl_periods(val)
    daily = {r["key"]: r for r in pp["daily"]}
    # bucket chứa flow không định lượng được => KHÔNG có số
    assert daily["2026-09-24"]["pnl_usdt"] is None


def test_flat_late_sleeve_reproduces_engine_total():
    """Consistency with the engine's strict-sum combined NOW number."""
    val = _valuation_3plus1()
    hist = compose_combined_history(val)
    last = [p for p in hist["series"] if p["status"] == "OK"][-1]
    engine_combined = sum(
        f["series"][-1]["equity"] for f in val["families"].values()
    )
    assert last["equity"] == pytest.approx(engine_combined)


# ----------------------------------------------------------------------
# Fallback: old envelope without per-family series
# ----------------------------------------------------------------------
def test_combined_only_fallback_keeps_old_behaviour():
    val = {
        "families": {
            fid: {"seeds": [{"ts_utc": SEED_TS, "equity": 100_000.0}]}
            for fid in FOUNDING
        },
        "combined": {
            "series": [
                {"ts": "2026-09-16T02:00:00Z", "status": "OK", "equity": 300_100.0},
                {"ts": "2026-09-16T02:05:00Z", "status": "OK", "equity": 300_200.0},
            ]
        },
    }
    hist = compose_combined_history(val)
    assert hist["mode"] == "combined_only"
    assert hist["baseline_equity"] == pytest.approx(300_000.0)
    assert hist["capital_flows"] == []
    pp = build_pnl_periods(val)
    assert pp["daily"][0]["pnl_usdt"] == pytest.approx(200.0)


def test_empty_valuation_yields_empty_history():
    hist = compose_combined_history({})
    assert hist["series"] == [] and hist["capital_flows"] == []
    pp = build_pnl_periods({})
    assert pp["daily"] == [] and pp["weekly"] == [] and pp["monthly"] == []
