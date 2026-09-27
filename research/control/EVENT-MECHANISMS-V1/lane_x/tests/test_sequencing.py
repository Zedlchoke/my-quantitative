"""A1 sequencing + R2-2/R2-3 book laws on hand-computed synthetic panels."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import NO_CA, TempExDates, make_panel  # noqa: E402

from engine_x.sequencing import build_event_record  # noqa: E402
from engine_x.tzlaw import clock_facts  # noqa: E402

# Synthetic name: 10 sessions 2024-01-02 .. 2024-01-15 (Mon-Fri grid),
# open=100, close=101 everywhere (up bars) unless overridden.
SESSIONS = ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05",
            "2024-01-08", "2024-01-09", "2024-01-10", "2024-01-11",
            "2024-01-12", "2024-01-15"]


def base_panel(**overrides):
    bars = [(d, o, c) for d, (o, c) in
            zip(SESSIONS, [(100.0, 101.0)] * len(SESSIONS))]
    return make_panel("TEST", bars, **overrides)


def test_mid_session_acceptance_sequencing():
    # Tuesday 2024-01-03 12:00 ET (17:00Z, EST) -> direction = 01-03
    # (close after acceptance), entry = 01-04 open=100, exit = 01-10 close=101
    res = build_event_record(base_panel(), NO_CA, "2024-01-03T17:00:00.000Z",
                             hold=5, direction_rule="a1")
    assert res.status == "BOOKED"
    assert res.direction_session == "2024-01-03"
    assert res.direction == 1
    assert res.entry_session == "2024-01-04"
    assert res.entry_price == 100.0
    assert res.exit_session == "2024-01-10"
    assert res.exit_price == 101.0
    assert res.delisting_exit is False


def test_after_close_acceptance_shifts_direction_to_next_day():
    # Tue 2024-01-02 18:30 ET (23:30Z, EST) -> Tue close (16:00) already past
    # -> direction = Wed 01-03, entry = Thu 01-04, exit = 01-10 (5 sessions
    # from 01-04: 01-04,01-05,01-08,01-09,01-10).
    res = build_event_record(base_panel(), NO_CA, "2024-01-02T23:30:00.000Z",
                             hold=5, direction_rule="a1")
    assert res.direction_session == "2024-01-03"
    assert res.entry_session == "2024-01-04"
    assert res.exit_session == "2024-01-10"


def test_direction_down_and_flat():
    bars = [(d, o, c) for d, (o, c) in
            zip(SESSIONS, [(100.0, 99.0)] * 4 + [(100.0, 100.0)] + [(100.0, 101.0)] * 5)]
    p = make_panel("TEST", bars)
    res = build_event_record(p, NO_CA, "2024-01-02T17:00:00.000Z",
                             hold=5, direction_rule="a1")
    assert res.direction == -1
    bars_flat = [(d, o, c) for d, (o, c) in
                 zip(SESSIONS, [(100.0, 100.0)] * len(SESSIONS))]
    res2 = build_event_record(make_panel("TEST", bars_flat), NO_CA,
                              "2024-01-02T17:00:00.000Z", hold=5, direction_rule="a1")
    assert res2.direction == 0


def test_delisting_exit_truncates_to_last_bar():
    # name ends 2024-01-08; entry 01-03, hold 5 needs 01-09 but panel ends -> exit 01-08
    p = make_panel("TEST", [(d, 100.0, 101.0) for d in SESSIONS[:5]])
    res = build_event_record(p, NO_CA, "2024-01-02T17:00:00.000Z",
                             hold=5, direction_rule="a1")
    assert res.status == "BOOKED"
    assert res.entry_session == "2024-01-03"
    assert res.exit_session == "2024-01-08"
    assert res.delisting_exit is True


def test_no_sessions_after_acceptance_dropped():
    p = make_panel("TEST", [(d, 100.0, 101.0) for d in SESSIONS[:2]])
    res = build_event_record(p, NO_CA, "2024-01-08T17:00:00.000Z",
                             hold=5, direction_rule="a1")
    assert res.status == "DROPPED"
    assert res.reason == "NO_POST_ACCEPTANCE_SESSION"


def test_entry_exactly_at_close_resolves_next_day():
    # acceptance exactly 16:00:00 ET Tuesday -> close NOT strictly after
    # -> direction = Wednesday (AMB-10)
    res = build_event_record(base_panel(), NO_CA, "2024-01-02T21:00:00.000Z",
                             hold=5, direction_rule="a1")
    assert res.direction_session == "2024-01-03"


def test_ca_exclusion_div_inside_window():
    # window entry 01-04 .. exit 01-10; div ex-date 2024-01-09 -> excluded
    ex = TempExDates({"TEST": (set(), set())})
    ex._cache["TEST"] = ({"2024-01-09"}, set())
    res = build_event_record(base_panel(), ex, "2024-01-03T17:00:00.000Z",
                             hold=5, direction_rule="a1")
    assert res.status == "EXCLUDED"
    assert res.reason == "CA_EXCLUSION"
    assert res.ca_detail["div_ex_dates"] == ["2024-01-09"]


def test_ca_exclusion_boundary_dates_inclusive():
    # split ex-date exactly ON the entry date -> excluded (inclusive window)
    ex = TempExDates({"TEST": (set(), set())})
    ex._cache["TEST"] = (set(), {"2024-01-04"})
    res = build_event_record(base_panel(), ex, "2024-01-03T17:00:00.000Z",
                             hold=5, direction_rule="a1")
    assert res.status == "EXCLUDED"
    # ex-date the day BEFORE entry -> clean
    ex2 = TempExDates({"TEST": (set(), set())})
    ex2._cache["TEST"] = (set(), {"2024-01-03"})
    res2 = build_event_record(base_panel(), ex2, "2024-01-03T17:00:00.000Z",
                              hold=5, direction_rule="a1")
    assert res2.status == "BOOKED"


def test_b1_entry_extreme_print_excludes():
    # entry bar 01-04: prior close 101 -> 1100 is 10.9x, ratio-1 = 9.89 >= 9
    bars = [(d, 100.0, 101.0) for d in SESSIONS]
    bars[2] = ("2024-01-04", 100.0, 1100.0)
    res = build_event_record(make_panel("TEST", bars), NO_CA,
                             "2024-01-03T17:00:00.000Z", hold=5, direction_rule="a1")
    assert res.status == "EXCLUDED"
    assert res.reason == "B1_ENTRY_EXTREME_PRINT"


def test_b1_both_directions_down():
    # symmetric law (AMB-16): prior close 101 -> 5 is a 20.2x down-print,
    # prev/cur - 1 = 19.2 >= 9 -> extreme (the literal |cur/prev - 1| formula
    # could never fire downward with positive prices; R2-2 says both directions)
    bars = [(d, 100.0, 101.0) for d in SESSIONS]
    bars[2] = ("2024-01-04", 100.0, 5.0)
    res = build_event_record(make_panel("TEST", bars), NO_CA,
                             "2024-01-03T17:00:00.000Z", hold=5, direction_rule="a1")
    assert res.status == "EXCLUDED"
    assert res.reason == "B1_ENTRY_EXTREME_PRINT"


def test_b1_not_fired_on_moderate_moves():
    # 101 -> 900 is 8.91x, ratio-1 = 8.91-1 = 7.91 < 9 -> NOT extreme
    bars = [(d, 100.0, 101.0) for d in SESSIONS]
    bars[2] = ("2024-01-04", 100.0, 900.0)
    res = build_event_record(make_panel("TEST", bars), NO_CA,
                             "2024-01-03T17:00:00.000Z", hold=5, direction_rule="a1")
    assert res.status == "BOOKED"


def test_x1_entry_zero_volume_excludes():
    vols = [1_000_000.0] * len(SESSIONS)
    vols[2] = 0.0
    res = build_event_record(base_panel(volumes=vols), NO_CA,
                             "2024-01-03T17:00:00.000Z", hold=5, direction_rule="a1")
    assert res.status == "EXCLUDED"
    assert res.reason == "X1_ENTRY_ZERO_VOLUME"


def test_exit_zero_volume_rolls_forward():
    # exit would be 01-10 (index 6); make 01-10 volume 0 -> exit rolls to 01-11
    vols = [1_000_000.0] * len(SESSIONS)
    vols[6] = 0.0
    res = build_event_record(base_panel(volumes=vols), NO_CA,
                             "2024-01-03T17:00:00.000Z", hold=5, direction_rule="a1")
    assert res.status == "BOOKED"
    assert res.exit_session == "2024-01-11"
    assert res.exit_rolled is True
    assert res.notes == ["EXIT_ROLLED_B1X1"]


def test_exdate_index_case_insensitive_lookup():
    """Regression: stems are resolved case-insensitively (79 case-differing
    names in the estate, e.g. panel `EV_OLD2` vs file `EV_old2`)."""
    from helpers import _WT_ROOT
    from engine_x.divsplits import ExDateIndex
    ex = ExDateIndex(
        os.path.join(_WT_ROOT, ".staging_eventmech", "integration",
                     ".staging_sec_v13", "eodhd_div"),
        os.path.join(_WT_ROOT, ".staging_eventmech", "integration",
                     ".staging_sec_v13", "eodhd_splits"))
    d, s = ex.ex_dates("ABT")
    assert len(d) > 100 and len(s) >= 7
    assert ex.contamination("ABT", "2024-01-02", "2024-03-01")["contaminated"] is True
    d2, s2 = ex.ex_dates("EV_OLD2")
    assert len(d2) > 0 and len(s2) > 0
