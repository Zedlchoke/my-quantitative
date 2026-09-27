"""R2-4 timezone law: ET conversion, strata boundaries, DST, weekend bucket.

Includes the three lane_s S7 fixtures (after-close, pre-open, DST
fall-back) reproduced from the fixture JSONs, plus a spring-forward case
and hand-computed boundary instants.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import load_s7_fixture  # noqa: E402

from engine_x.tzlaw import (  # noqa: E402
    STRATUM_S1, STRATUM_S2, STRATUM_S3, STRATUM_S4, clock_facts,
    session_close_instant, session_open_instant,
)
from engine_x.panel import NamePanel  # noqa: E402


# ---- S7 fixture a: after-close ------------------------------------------

def test_s7_a_after_close():
    fx = load_s7_fixture("fixture_a_after_close.json")
    f = clock_facts(fx["acceptance_utc"])
    assert f.et_local == fx["expected"]["et_local"]
    assert f.et_offset_hours == -4
    assert f.is_weekend is False
    assert f.stratum == "S3"
    # sequencing: 18:30 ET Mon -> Monday close (16:00) already past
    p = NamePanel("FAKE", [{"date": d, "open": 10, "close": 10, "volume": 1}
                           for d in ("2024-06-07", "2024-06-10", "2024-06-11",
                                     "2024-06-12", "2024-06-13", "2024-06-14",
                                     "2024-06-17", "2024-06-18", "2024-06-19")])
    from engine_x.tzlaw import parse_acceptance
    ds = p.first_session_with_close_after(int(parse_acceptance(fx["acceptance_utc"]).timestamp()))
    assert ds == "2024-06-11", fx["expected"]["direction_session_expected_date"]
    assert p.next_session_after(ds) == "2024-06-12"
    assert p.session_at_offset("2024-06-12", 4) == "2024-06-18"


# ---- S7 fixture b: pre-open ----------------------------------------------

def test_s7_b_pre_open():
    fx = load_s7_fixture("fixture_b_pre_open.json")
    f = clock_facts(fx["acceptance_utc"])
    assert f.et_local == fx["expected"]["et_local"]
    assert f.et_offset_hours == -4
    assert f.stratum == "S1"
    from engine_x.tzlaw import parse_acceptance
    p = NamePanel("FAKE", [{"date": d, "open": 10, "close": 10, "volume": 1}
                           for d in ("2024-06-06", "2024-06-07", "2024-06-10",
                                     "2024-06-11", "2024-06-12", "2024-06-13",
                                     "2024-06-14", "2024-06-17", "2024-06-18")])
    ds = p.first_session_with_close_after(int(parse_acceptance(fx["acceptance_utc"]).timestamp()))
    assert ds == "2024-06-10"
    assert p.next_session_after(ds) == "2024-06-11"
    assert p.session_at_offset("2024-06-11", 4) == "2024-06-17"


# ---- S7 fixture c: DST fall-back, weekend --------------------------------

def test_s7_c_dst_fall_back():
    fx = load_s7_fixture("fixture_c_dst_fall_back.json")
    f = clock_facts(fx["acceptance_utc"])
    assert f.et_local == fx["expected"]["et_local"]      # pins the -05:00 OFFSET
    assert f.et_offset_hours == -5
    assert f.is_weekend is True
    assert f.weekend_bucket is True
    assert f.weekday == "Sunday"
    assert f.stratum == "S3"
    from engine_x.tzlaw import parse_acceptance
    p = NamePanel("FAKE", [{"date": d, "open": 10, "close": 10, "volume": 1}
                           for d in ("2025-10-31", "2025-11-03", "2025-11-04",
                                     "2025-11-05", "2025-11-06", "2025-11-07",
                                     "2025-11-10", "2025-11-11")])
    ds = p.first_session_with_close_after(int(parse_acceptance(fx["acceptance_utc"]).timestamp()))
    assert ds == "2025-11-03"
    assert p.next_session_after(ds) == "2025-11-04"


# ---- spring forward (Sunday 2025-03-09) ----------------------------------

def test_spring_forward_offset():
    f = clock_facts("2025-03-09T07:30:00.000Z")
    assert f.et_local == "2025-03-09T03:30:00-04:00"   # 02:30 would-be EST -> 03:30 EDT
    assert f.et_offset_hours == -4
    assert f.is_weekend is True
    assert f.stratum == "S1"


# ---- hand-computed stratum boundaries (half-open intervals) --------------

def test_stratum_boundaries_edt():
    # 09:30 ET exactly -> S2 (S1 is [00:00,09:30))
    assert clock_facts("2024-06-10T13:30:00.000Z").stratum == STRATUM_S2
    # 09:29:59 ET -> S1
    assert clock_facts("2024-06-10T13:29:59.000Z").stratum == STRATUM_S1
    # 16:00 ET exactly -> S3 (S2 is [09:30,16:00))
    assert clock_facts("2024-06-10T20:00:00.000Z").stratum == STRATUM_S3
    # 15:59:59 ET -> S2
    assert clock_facts("2024-06-10T19:59:59.000Z").stratum == STRATUM_S2
    # 20:00 ET exactly -> S4 (S3 is [16:00,20:00))
    assert clock_facts("2024-06-11T00:00:00.000Z").stratum == STRATUM_S4
    # 19:59:59 ET -> S3
    assert clock_facts("2024-06-10T23:59:59.000Z").stratum == STRATUM_S3
    # midnight ET -> S1
    assert clock_facts("2024-06-10T04:00:00.000Z").stratum == STRATUM_S1


def test_weekend_flag_est():
    f = clock_facts("2024-06-15T15:00:00.000Z")  # Saturday 11:00 ET
    assert f.is_weekend is True and f.weekend_bucket is True
    assert f.stratum == STRATUM_S2  # clock stratum still recorded


def test_open_close_instants():
    assert session_close_instant("2024-06-10").isoformat() == "2024-06-10T16:00:00-04:00"
    assert session_open_instant("2024-06-10").isoformat() == "2024-06-10T09:30:00-04:00"
