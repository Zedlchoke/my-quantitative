"""FOREX-NG1 P1-SPOT tests (dispatch item 6).

Hand-computed classes, per the dispatch:

1. a small self-made fixture (10 bars, written under /tmp): 16:00-NY
   close selection on the weekday decision grid;
2. DST boundary of the decision clock: the fall-back weekend instant
   gap (73h), the spring-forward weekend gap (71h), and the place where
   the "2x wall-clock hour" ambiguity actually lives on a fall-back day
   (the repeated 01:00-01:59 local hour) with 16:00-NY resolving to a
   single deterministic UTC instant;
3. fail-closed integrity: a one-byte sha drift refuses to serve;
   a duplicate bar timestamp refuses to serve;
4. canary: fabricated dates are found=False, a nonexistent pair is
   refused, a real weekend bar is served by lookup but excluded from
   the weekday grid;
5. authority: the committed proof records CANDIDATE_NOT_AUTHORIZED for
   scored consumption and require_scored_authority refuses.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from datetime import date, datetime, timedelta, timezone

import pytest

from research.assets.forex_ng1 import spot_series as ss

# --------------------------------------------------------------------- #
# fixture: 10 hand-made weekday bars spanning the 2023 fall-back weekend
# (fall-back instant: 2023-11-05 02:00 EDT -> 01:00 EST)
# --------------------------------------------------------------------- #

HAND_BARS = [
    # (iso date, close)  -- hand-set, strictly ascending dates
    ("2023-10-30", 1.1000),   # Mon, EDT
    ("2023-10-31", 1.1100),   # Tue, EDT
    ("2023-11-01", 1.1200),   # Wed, EDT
    ("2023-11-02", 1.1300),   # Thu, EDT
    ("2023-11-03", 1.1400),   # Fri, EDT  (16:00 EDT == 20:00Z)
    ("2023-11-06", 1.1500),   # Mon, EST  (16:00 EST == 21:00Z)
    ("2023-11-07", 1.1600),   # Tue, EST
    ("2023-11-08", 1.1700),   # Wed, EST
    ("2023-11-09", 1.1800),   # Thu, EST
    ("2023-11-10", 1.1900),   # Fri, EST
]
WEEKEND_BAR = ("2023-11-04", 1.9999)   # Sat: real bar, grid-excluded


def _payload(bars, *, symbol="GBP/USD", interval="1day", status="ok"):
    return {
        "meta": {"symbol": symbol, "interval": interval,
                 "currency_base": "British Pound",
                 "currency_quote": "US Dollar",
                 "type": "Physical Currency"},
        "values": [   # provider contract: newest-first storage
            {"datetime": d, "open": str(c - 0.0010), "high": str(c + 0.0020),
             "low": str(c - 0.0020), "close": str(c)}
            for d, c in sorted(bars, reverse=True)],
        "status": status,
    }


def _write_fixture(bars, *, payload_kwargs=None):
    """Write fixture file + pin manifest under /tmp; return (dir, paths)."""
    tmp = tempfile.mkdtemp(prefix="forex_ng1_p1spot_")
    data_dir = f"{tmp}/data"
    manifest_path = f"{tmp}/spot_pin_manifest.json"
    import os
    os.makedirs(data_dir)
    payload = _payload(bars, **(payload_kwargs or {}))
    fname = "GBPUSD.json"
    with open(f"{data_dir}/{fname}", "w", encoding="utf-8") as fh:
        json.dump(payload, fh)
    digest = ss.sha256_file(f"{data_dir}/{fname}")
    manifest = {
        "schema": ss.PIN_MANIFEST_SCHEMA,
        "files": {"GBPUSD": {
            "file": fname,
            "copy_path_absolute": f"{data_dir}/{fname}",
            "copy_sha256": digest,
            "bars": len(bars)}},
    }
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh)
    return tmp, manifest_path, data_dir


@pytest.fixture
def fixture_dir():
    tmp, manifest_path, data_dir = _write_fixture(
        HAND_BARS + [WEEKEND_BAR])
    yield tmp, manifest_path, data_dir
    shutil.rmtree(tmp, ignore_errors=True)


def _resolve(manifest_path, data_dir):
    return ss.resolve_spot_series("GBPUSD", manifest_path, data_dir)


# --------------------------------------------------------------------- #
# 1. 16:00-NY close selection on the weekday decision grid
# --------------------------------------------------------------------- #

def test_close_selection_and_grid_hand_computed(fixture_dir):
    _tmp, manifest_path, data_dir = fixture_dir
    s = _resolve(manifest_path, data_dir)
    # all 10 weekday bars + the Saturday bar are pinned bytes
    assert s.bars == 11
    assert s.first_day == date(2023, 10, 30)
    assert s.last_day == date(2023, 11, 10)
    # the weekday decision grid excludes the Saturday bar
    grid = s.window_days(date(2023, 10, 30), date(2023, 11, 10))
    assert grid == [date.fromisoformat(d) for d, _ in HAND_BARS]
    # hand-computed: the served close at each grid day is that day's bar
    for d, c in HAND_BARS:
        got = s.lookup_close(d)
        assert got["found"] is True
        assert got["close"] == pytest.approx(c, abs=1e-9)
    # grid endpoints' decision instants (both EDT here; EST from 11-06)
    assert ss.instant_iso(ss.ny_decision_instant_utc(grid[0])) \
        == "2023-10-30T20:00:00Z"
    assert ss.instant_iso(ss.ny_decision_instant_utc(grid[-1])) \
        == "2023-11-10T21:00:00Z"


def test_common_grid_intersects_pair_calendars(fixture_dir):
    _tmp, manifest_path, data_dir = fixture_dir
    a = _resolve(manifest_path, data_dir)
    # a second "pair" from the same bytes minus the 11-07 bar
    tmp2, m2, d2 = _write_fixture(
        [b for b in HAND_BARS if b[0] != "2023-11-07"] + [WEEKEND_BAR])
    try:
        b = ss.resolve_spot_series("GBPUSD", m2, d2)
        common = ss.common_weekday_grid(
            {"A": a, "B": b}, date(2023, 10, 30), date(2023, 11, 10))
        assert common == [date.fromisoformat(d)
                          for d, _ in HAND_BARS if d != "2023-11-07"]
    finally:
        shutil.rmtree(tmp2, ignore_errors=True)


# --------------------------------------------------------------------- #
# 2. DST boundaries (hand-computed UTC instants and gaps)
# --------------------------------------------------------------------- #

def test_fall_back_weekend_instant_gap_is_73h():
    # Fri 2023-11-03 16:00 EDT = 20:00Z; Mon 2023-11-06 16:00 EST = 21:00Z
    fri = ss.ny_decision_instant_utc(date(2023, 11, 3))
    mon = ss.ny_decision_instant_utc(date(2023, 11, 6))
    assert fri == datetime(2023, 11, 3, 20, 0, tzinfo=timezone.utc)
    assert mon == datetime(2023, 11, 6, 21, 0, tzinfo=timezone.utc)
    assert (mon - fri).total_seconds() / 3600 == pytest.approx(73.0)
    # 3 calendar days = 72h; the fall-back adds exactly one hour


def test_spring_forward_weekend_instant_gap_is_71h():
    # Fri 2024-03-08 16:00 EST = 21:00Z; Mon 2024-03-11 16:00 EDT = 20:00Z
    fri = ss.ny_decision_instant_utc(date(2024, 3, 8))
    mon = ss.ny_decision_instant_utc(date(2024, 3, 11))
    assert fri == datetime(2024, 3, 8, 21, 0, tzinfo=timezone.utc)
    assert mon == datetime(2024, 3, 11, 20, 0, tzinfo=timezone.utc)
    assert (mon - fri).total_seconds() / 3600 == pytest.approx(71.0)


def test_fall_back_day_two_wall_clock_hours_live_at_1am_not_16():
    """The fall-back day 2023-11-05 carries ONE doubled wall-clock hour
    (01:00-01:59 EDT then EST); 16:00-NY occurs exactly once. A naive
    fixed-offset converter would entertain two candidates for 16:00
    (20:00Z assuming -4, 21:00Z assuming -5); zoneinfo resolves the
    single truth: after the 02:00->01:00 fold the day is EST, so
    16:00 local == 21:00Z."""
    doubled = datetime(2023, 11, 5, 1, 30, tzinfo=ss.NY_TZ)
    first_occurrence = doubled.replace(fold=0).astimezone(timezone.utc)
    second_occurrence = doubled.replace(fold=1).astimezone(timezone.utc)
    assert first_occurrence == datetime(2023, 11, 5, 5, 30,
                                        tzinfo=timezone.utc)   # EDT -4
    assert second_occurrence == datetime(2023, 11, 5, 6, 30,
                                         tzinfo=timezone.utc)  # EST -5
    inst = ss.ny_decision_instant_utc(date(2023, 11, 5))
    assert inst == datetime(2023, 11, 5, 21, 0, tzinfo=timezone.utc)
    local_at_16 = datetime(2023, 11, 5, 16, 0, tzinfo=ss.NY_TZ)
    assert local_at_16.utcoffset() == timedelta(hours=-5)  # EST, once
    # and the mapping is a total function: same day in, same instant out
    assert ss.ny_decision_instant_utc(date(2023, 11, 5)) == inst


# --------------------------------------------------------------------- #
# 3. fail-closed integrity
# --------------------------------------------------------------------- #

def test_sha_mismatch_one_byte_refuses_to_serve():
    # flip exactly one digit inside a close value of a valid fixture:
    # the oldest bar's close 1.1 -> 1.2 (one byte, value-changing)
    tmp, manifest_path, data_dir = _write_fixture(HAND_BARS)
    try:
        path = f"{data_dir}/GBPUSD.json"
        raw = open(path, "r", encoding="utf-8").read()
        needle = '"close": "1.1"'
        idx = raw.index(needle)
        raw2 = (raw[:idx] + '"close": "1.2"' + raw[idx + len(needle):])
        assert sum(a != b for a, b in zip(raw, raw2)) == 1  # one byte
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(raw2)
        with pytest.raises(ss.SpotIntegrityError):
            ss.resolve_spot_series("GBPUSD", manifest_path, data_dir)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_missing_pinned_file_refuses_to_serve():
    tmp, manifest_path, data_dir = _write_fixture(HAND_BARS)
    try:
        import os
        os.remove(f"{data_dir}/GBPUSD.json")
        with pytest.raises(ss.SpotIntegrityError):
            ss.resolve_spot_series("GBPUSD", manifest_path, data_dir)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_duplicate_timestamp_refuses_to_serve():
    dup = HAND_BARS + [("2023-11-08", 9.9999)]   # duplicate bar date
    tmp, manifest_path, data_dir = _write_fixture(dup)
    try:
        with pytest.raises(ss.SpotStructureError, match="DUPLICATE"):
            ss.resolve_spot_series("GBPUSD", manifest_path, data_dir)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_provider_status_not_ok_refuses():
    tmp, manifest_path, data_dir = _write_fixture(
        HAND_BARS, payload_kwargs={"status": "error"})
    try:
        with pytest.raises(ss.SpotStructureError):
            ss.resolve_spot_series("GBPUSD", manifest_path, data_dir)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_wrong_interval_refuses():
    tmp, manifest_path, data_dir = _write_fixture(
        HAND_BARS, payload_kwargs={"interval": "1h"})
    try:
        with pytest.raises(ss.SpotStructureError):
            ss.resolve_spot_series("GBPUSD", manifest_path, data_dir)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------- #
# 4. canary (fabricated data must never be served or inferred)
# --------------------------------------------------------------------- #

def test_canary_fabricated_dates_not_found(fixture_dir):
    _tmp, manifest_path, data_dir = fixture_dir
    s = _resolve(manifest_path, data_dir)
    # Sunday inside coverage (no Sunday bar pinned)
    assert s.lookup_close("2023-11-05")["found"] is False
    # future date beyond the pinned span
    assert s.lookup_close("2030-01-02")["found"] is False
    # date before the pinned span
    assert s.lookup_close("2023-10-02")["found"] is False
    # absent weekday (not in the 10-bar fixture)
    assert s.lookup_close("2023-11-13")["found"] is False


def test_canary_weekend_bar_served_by_lookup_but_excluded_from_grid(
        fixture_dir):
    _tmp, manifest_path, data_dir = fixture_dir
    s = _resolve(manifest_path, data_dir)
    got = s.lookup_close(WEEKEND_BAR[0])
    assert got["found"] is True                  # honest to the bytes
    assert got["close"] == pytest.approx(WEEKEND_BAR[1], abs=1e-9)
    assert date.fromisoformat(WEEKEND_BAR[0]) not in s.window_days(
        date(2023, 10, 30), date(2023, 11, 10))


def test_canary_nonexistent_pair_refused(fixture_dir):
    _tmp, manifest_path, data_dir = fixture_dir
    for fake in ("XXXUSD", "GBPXXX", "EURUSD"):
        with pytest.raises(ss.SpotIntegrityError):
            ss.resolve_spot_series(fake, manifest_path, data_dir)


# --------------------------------------------------------------------- #
# 5. authority gate (fail-closed; no self-promotion)
# --------------------------------------------------------------------- #

def test_committed_proof_records_candidate_not_authorized():
    block = ss.spot_authority_status()
    assert block["status"] == "DOCUMENTED_CANDIDATE"
    assert block["scored_consumption"] == "CANDIDATE_NOT_AUTHORIZED"


def test_scored_authority_refused_by_default():
    with pytest.raises(ss.SpotAuthorityError, match="CANDIDATE"):
        ss.require_scored_authority()


def test_scored_authority_passes_only_on_recorded_authorization(tmp_path):
    proof = {
        "schema": ss.AUTHORITY_PROOF_SCHEMA,
        "authority_status": {"status": "AUTHORIZED",
                             "scored_consumption": "AUTHORIZED"},
    }
    p = tmp_path / "proof.json"
    p.write_text(json.dumps(proof), encoding="utf-8")
    assert ss.require_scored_authority(str(p))["scored_consumption"] \
        == "AUTHORIZED"
