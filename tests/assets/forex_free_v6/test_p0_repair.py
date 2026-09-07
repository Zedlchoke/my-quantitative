"""FOREX-FREE-V6 P0 repair tests (lane p0-a2-repair).

Synthetic fixtures ONLY — no production outcome data, no network, no PnL.

Covers the three mandated targets (PLAN_forex_v6.md section 3 P0a/P0b):
  1. DST boundary conversion (a March and a November date, plus the
     spring-forward / fall-back instants) for the America/Toronto 08:30
     StatCan convention: EDT -> 12:30Z, EST -> 13:30Z.
  2. Append-only invariant: the inherited base pins (V5 announcement
     ledgers, v2 CA calendar) re-hash EXACTLY to their pinned values
     after the P0a/P0b builds.
  3. Invariance-checker logic on a tiny synthetic calendar: same-side-
     of-a-daily-boundary checking, including a deliberately boundary-
     crossing stamp that must flip (mirroring the real 3 WDS change-
     event rows found by the P0b proof).

Run ONLY this file:
  /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest \
      tests/assets/forex_free_v6/test_p0_repair.py -q
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

REPO = Path(__file__).resolve().parents[3]
RUN_DIR = REPO / "research/control/forex_free_v6_run"
V5_DIR = REPO / "research/control/forex_free_v5_run"
TORONTO = ZoneInfo("America/Toronto")

# Inherited pins (A1 re-verified; must hold after every P0 build)
PIN_LEDGER_BASE = "ae5e1f2e64b8aa7c08472755bd73857543aa89b72ea81b70ad5c5d81e7cd6bd4"
PIN_LEDGER_V5_EXT = "cf1f01a7ec2d3d7506892c045139910937147df49d3742cc4ec72b36d20fd902"
PIN_CA_CAL_V2 = "088b0ba80f0580e39ab17832872a93e3dce15bc077ffafa2f87800b4c7115eaa"


def _load_builder(name: str):
    spec = importlib.util.spec_from_file_location(name, RUN_DIR / name)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------- helpers

def toronto_0830_to_utc(d: date) -> datetime:
    """The P0b conversion under test: 08:30 America/Toronto -> UTC."""
    return datetime(d.year, d.month, d.day, 8, 30, tzinfo=TORONTO).astimezone(timezone.utc)


def ny_boundary_utc(d: date) -> datetime:
    """Daily 16:00 America/New_York decision boundary (DST-correct)."""
    return datetime(d.year, d.month, d.day, 16, 0, tzinfo=ZoneInfo("America/New_York")).astimezone(timezone.utc)


def known_at(stamp_utc: datetime, boundary_utc: datetime) -> bool:
    return stamp_utc <= boundary_utc


# --------------------------------------------- 1. DST boundary conversion

@pytest.mark.parametrize(
    "d,expected_hhmm,expected_tzname",
    [
        # a MARCH date: pre-2025 spring-forward (DST starts 2025-03-09),
        # 2025-03-12 is EDT -> 08:30 EDT == 12:30Z
        (date(2025, 3, 12), "12:30", "EDT"),
        # a NOVEMBER date: after the 2025-11-02 fall-back, EST -> 13:30Z
        (date(2025, 11, 19), "13:30", "EST"),
        # spring-forward day itself: 08:30 local is after the 02:00 switch
        (date(2025, 3, 9), "12:30", "EDT"),
        # a deep-winter EST date
        (date(2025, 1, 15), "13:30", "EST"),
    ],
)
def test_toronto_0830_dst_conversion(d, expected_hhmm, expected_tzname):
    got = toronto_0830_to_utc(d)
    assert got.strftime("%H:%M") == expected_hhmm
    # tz label sanity via the local instant
    assert datetime(d.year, d.month, d.day, 8, 30, tzinfo=TORONTO).tzname() == expected_tzname
    assert got.date() == d, "conversion must not roll the UTC calendar date"


def test_toronto_0830_matches_p0b_builder_on_synthetic_dates():
    """The production conversion function agrees with the reference math."""
    b = _load_builder("p0b_ca_tz_v3_builder.py")
    for d in (date(2025, 3, 12), date(2025, 11, 19)):
        c = b.convert_row(f"{d.isoformat()}T08:30")
        assert c["true_dt"] == toronto_0830_to_utc(d)
        assert c["scheduled_0830"] is True
    # a non-08:30 verbatim WDS time converts at +4h on an EDT date
    c = b.convert_row("2021-07-23T18:56")
    assert c["true_dt"] == datetime(2021, 7, 23, 22, 56, tzinfo=timezone.utc)
    assert c["scheduled_0830"] is False


# ------------------------------------------------- 2. append-only pins

@pytest.mark.parametrize(
    "relpath,pin",
    [
        ("research/control/forex_free_v5_run/announcement_ledger.jsonl", PIN_LEDGER_BASE),
        ("research/control/forex_free_v5_run/announcement_ledger_v5_extension.jsonl", PIN_LEDGER_V5_EXT),
        ("research/control/forex_free_v5_run/ca_statcan_cpi_release_dates.json", PIN_CA_CAL_V2),
    ],
)
def test_base_pins_unchanged_after_p0_builds(relpath, pin):
    p = REPO / relpath
    assert p.exists(), f"inherited evidence file missing: {relpath}"
    assert hashlib.sha256(p.read_bytes()).hexdigest() == pin


def test_p0a_repair_ledger_only_adds_and_copies_base_verbatim():
    """Repair ledger ADDs 9 rows; base values are verbatim base-ledger values."""
    base = {json.loads(l)["decision_id"]: json.loads(l)
            for l in (V5_DIR / "announcement_ledger.jsonl").read_text().splitlines() if l.strip()}
    rows = [json.loads(l) for l in (RUN_DIR / "announcement_ledger_v6_emu_repair.jsonl").read_text().splitlines() if l.strip()]
    assert len(rows) == 9
    assert all(r["row_type"] == "REPAIR_V2" for r in rows)
    for r in rows:
        b = base[r["decision_id"]]
        assert r["base_ledger"]["base_value_new"] == b["new_value"]
        assert r["base_ledger"]["base_value_old"] == b["old_value"]
        # every evidenced row records BOTH series side by side
        if r["verdict"] == "EVIDENCED_VALUE_MATCH":
            assert r["evidenced"]["primary_table"]["mro"] != r["evidenced"]["primary_table"]["dfr"]
            assert isinstance(r["value_match_mro"], bool) and isinstance(r["value_match_dfr"], bool)
    # the 9-row run diagnosis: 2 MRO-anchored then 7 DFR-anchored
    diag = [r["base_series_diagnosis"] for r in rows]
    assert diag == ["MRO_CONFIRMED", "MRO_CONFIRMED"] + ["DFR_SUSPECTED_CONFIRMED"] * 7


# ------------------------- 3. invariance checker on a tiny synthetic calendar

def _synthetic_calendar():
    """Three synthetic rows mirroring the real stamp families:
    A: scheduled 08:30 local on an EDT date (invariant expected)
    B: scheduled 08:30 local on an EST date (invariant expected)
    C: verbatim 18:56 local change event (MUST flip the same-day boundary)
    """
    return [
        {"row": "A_edt_0830", "local": (date(2025, 7, 15), 8, 30)},
        {"row": "B_est_0830", "local": (date(2025, 1, 15), 8, 30)},
        {"row": "C_change_1856", "local": (date(2025, 7, 15), 18, 56)},
    ]


def _stamp_v2(local):
    d, hh, mm = local
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=timezone.utc)  # ET mislabeled as UTC


def _stamp_v3(local):
    d, hh, mm = local
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=TORONTO).astimezone(timezone.utc)


def test_synthetic_invariance_checker():
    days = [date(2025, 7, 14) + timedelta(days=i) for i in range(4)]
    boundaries = [ny_boundary_utc(d) for d in days]
    results = {}
    for row in _synthetic_calendar():
        v2, v3 = _stamp_v2(row["local"]), _stamp_v3(row["local"])
        flips = [b for b in boundaries if (v2 <= b) != (v3 <= b) and min(v2, v3) < b <= max(v2, v3)]
        results[row["row"]] = flips
    # scheduled 08:30 rows: same side of EVERY boundary (both EDT and EST cases)
    assert results["A_edt_0830"] == []
    assert results["B_est_0830"] == []
    # the boundary-crossing change event flips exactly the same-day boundary
    flips = results["C_change_1856"]
    assert len(flips) == 1
    assert flips[0] == ny_boundary_utc(date(2025, 7, 15))
    # and the flip is directional: v2 said known-before-boundary, v3 says after
    b = flips[0]
    assert known_at(_stamp_v2(_synthetic_calendar()[2]["local"]), b)
    assert not known_at(_stamp_v3(_synthetic_calendar()[2]["local"]), b)


def test_p0b_v3_files_and_proof_exist_and_count_107():
    cal = json.load((RUN_DIR / "ca_statcan_cpi_release_dates_v3.json").open())
    pr = json.load((RUN_DIR / "p0a_cpi_prints_ca_v3.json").open())
    proof = json.load((RUN_DIR / "p0b_ca_tz_invariance_proof.json").open())
    assert len(cal) == len(pr) == 107
    # every v3 prints row keeps the v2 value as an audit field
    assert all("available_time_utc_v2_recorded" in r for r in pr)
    # proof counts consistent
    assert proof["proof"]["rows_checked"] == 107
    assert proof["proof"]["scheduled_rows_all_invariant"] is True
