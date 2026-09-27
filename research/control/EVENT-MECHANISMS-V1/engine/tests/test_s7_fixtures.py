"""E6(a) — S7 fixtures 3/3 must reproduce from code (never from the doc)."""
import json
from datetime import datetime, date, time

import pytest

from emv1 import clock
from emv1.panel import NameSeries
from emv1.book import build_decision
from emv1 import config as C

FIXTURE_DIR = C.STAGING + "/fixtures"


def weekday_panel(ticker: str, d0: str, d1: str, open_price=10.0) -> NameSeries:
    """Synthetic name with a bar on every weekday in [d0, d1]; all bars
    up-closes (LONG direction) with controlled open prices."""
    import datetime as dt
    ns = NameSeries(ticker)
    d = date.fromisoformat(d0)
    end = date.fromisoformat(d1)
    while d <= end:
        if d.weekday() < 5:
            ds = d.isoformat()
            ns.dates.append(ds)
            ns.idx[ds] = len(ns.dates) - 1
            o = open_price
            c = open_price + 1.0
            ns.open.append(o)
            ns.high.append(c + 0.5)
            ns.low.append(o - 0.5)
            ns.close.append(c)
            ns.vol.append(1_000_000.0)
            ns.dv.append(c * 1_000_000.0)
            ns.fill_ok.append(True)
        d += dt.timedelta(days=1)
    return ns


class MiniPanel:
    def __init__(self, ns):
        self.names = {ns.ticker: ns}

    def get(self, t):
        return self.names.get(t)


def run_fixture(fname, corp_actions=None):
    fx = json.load(open(f"{FIXTURE_DIR}/{fname}"))
    inst = clock.parse_acceptance_utc(fx["acceptance_utc"])
    et, off = clock.to_et(inst)
    stratum, is_weekend = clock.stratum_of(et)
    ns = weekday_panel("TEST", "2024-04-01", "2024-06-30") \
        if "2024-06" in fx["acceptance_utc"] else \
        weekday_panel("TEST", "2025-08-01", "2025-11-14")
    rec, exc = build_decision(
        event_id="FX", family_id=C.FAMILY_A1, arm_id="A1-ANCHOR",
        cik="CIK0000000001", ticker="TEST", form="10-Q",
        acceptance_utc=fx["acceptance_utc"], instant_et=et,
        hold_sessions=fx["expected"]["hold_sessions"],
        panel=MiniPanel(ns), corp_actions=corp_actions or {},
        stratum=stratum, bucket=stratum, is_weekend=is_weekend)
    return fx, rec, exc, et, off, stratum, is_weekend


def test_fixture_a_after_close():
    fx, rec, exc, et, off, stratum, is_weekend = run_fixture("fixture_a_after_close.json")
    assert exc is None and rec is not None
    exp = fx["expected"]
    assert stratum == exp["stratum"] == "S3"
    assert round(off) == exp["et_offset_hours"] == -4
    assert is_weekend is False
    assert et.isoformat() == exp["et_local"]
    assert rec["direction_session"] == exp["direction_session_expected_date"] == "2024-06-11"
    assert rec["entry_session"] == exp["entry_session_expected_date"] == "2024-06-12"
    assert rec["exit_session"] == "2024-06-18"
    assert rec["direction"] == "LONG"


def test_fixture_b_pre_open():
    fx, rec, exc, et, off, stratum, is_weekend = run_fixture("fixture_b_pre_open.json")
    assert exc is None and rec is not None
    exp = fx["expected"]
    assert stratum == exp["stratum"] == "S1"
    assert round(off) == exp["et_offset_hours"] == -4
    assert rec["direction_session"] == exp["direction_session_expected_date"] == "2024-06-10"
    assert rec["entry_session"] == exp["entry_session_expected_date"] == "2024-06-11"
    assert rec["exit_session"] == "2024-06-17"


def test_fixture_c_dst_fall_back():
    fx, rec, exc, et, off, stratum, is_weekend = run_fixture("fixture_c_dst_fall_back.json")
    assert exc is None and rec is not None
    exp = fx["expected"]
    assert stratum == exp["stratum"] == "S3"
    assert round(off) == exp["et_offset_hours"] == -5  # EST in effect after fall-back
    assert is_weekend is True  # weekend bucket separate, never collapsed
    assert rec["direction_session"] == exp["direction_session_expected_date"] == "2025-11-03"
    assert rec["entry_session"] == exp["entry_session_expected_date"] == "2025-11-04"
