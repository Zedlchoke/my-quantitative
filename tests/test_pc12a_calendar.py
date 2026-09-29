"""PC12A calendar service: 286-Friday fold calendar, DST session marks,
Wednesday x3 swap calendar, roll/reopen windows."""

import datetime as dt

from research.pc12a import calendar_service as cal

UTC = dt.timezone.utc


def d(y, m, dd):
    return dt.date(y, m, dd)


def ts(y, m, dd, h, mm=0):
    return dt.datetime(y, m, dd, h, mm, tzinfo=UTC)


def test_decision_fridays_286_exact_bounds():
    fr = cal.decision_fridays()
    assert len(fr) == 286
    assert fr[0] == d(2021, 1, 8)
    assert fr[-1] == d(2026, 6, 26)
    assert all(f.weekday() == 4 for f in fr)


def test_fold_calendar_arithmetic_52_8x26_embargo_26_sealed():
    folds = cal.fold_calendar()
    assert len(folds) == 8
    fr = cal.decision_fridays()
    for k, f in enumerate(folds):
        assert f.test_start == fr[52 + 26 * k]
        assert f.test_end == fr[52 + 26 * (k + 1) - 1]
        # expanding train ends one FULL week (embargo) before the test fold
        assert f.train_end == fr[52 + 26 * k - 2]
        assert f.train_start == fr[0]
    sealed_start, sealed_end = cal.sealed_tail()
    assert sealed_start == fr[260]
    assert sealed_end == fr[285]
    assert folds[-1].test_end < sealed_start  # sealed tail EXCLUDED


def test_session_marks_dst_correct_london():
    # winter (GMT = UTC): London 08:00 local == 08:00Z
    win = cal.session_windows_utc(d(2024, 1, 17))
    lon = [w for w in win if w[2] == "London"][0]
    assert lon[0] == ts(2024, 1, 17, 8, 0)
    assert lon[1] == ts(2024, 1, 17, 12, 0)
    # summer (BST = UTC+1): London 08:00 local == 07:00Z
    sumr = cal.session_windows_utc(d(2024, 7, 17))
    lon2 = [w for w in sumr if w[2] == "London"][0]
    assert lon2[0] == ts(2024, 7, 17, 7, 0)
    assert lon2[1] == ts(2024, 7, 17, 11, 0)


def test_session_marks_dst_correct_newyork():
    # winter (EST = UTC-5): NY 09:30 local == 14:30Z
    win = cal.session_windows_utc(d(2024, 1, 17))
    ny = [w for w in win if w[2] == "NewYork"][0]
    assert ny[0] == ts(2024, 1, 17, 14, 30)
    assert ny[1] == ts(2024, 1, 17, 21, 0)
    # summer (EDT = UTC-4): NY 09:30 local == 13:30Z
    sumr = cal.session_windows_utc(d(2024, 7, 17))
    ny2 = [w for w in sumr if w[2] == "NewYork"][0]
    assert ny2[0] == ts(2024, 7, 17, 13, 30)
    assert ny2[1] == ts(2024, 7, 17, 20, 0)


def test_dst_seams_shift_on_the_right_sunday():
    # US DST starts 2024-03-10, EU (London) on 2024-03-31:
    # 2024-03-20 is inside the divergent window (US on DST, UK not yet)
    w = cal.session_windows_utc(d(2024, 3, 20))
    lon = [x for x in w if x[2] == "London"][0]
    ny = [x for x in w if x[2] == "NewYork"][0]
    assert lon[0] == ts(2024, 3, 20, 8, 0)      # still GMT
    assert ny[0] == ts(2024, 3, 20, 13, 30)     # already EDT
    # after both switched: 2024-04-10
    w2 = cal.session_windows_utc(d(2024, 4, 10))
    lon2 = [x for x in w2 if x[2] == "London"][0]
    assert lon2[0] == ts(2024, 4, 10, 7, 0)     # BST
    # autumn divergence: EU ends 2024-10-27, US 2024-11-03
    w3 = cal.session_windows_utc(d(2024, 10, 30))
    lon3 = [x for x in w3 if x[2] == "London"][0]
    ny3 = [x for x in w3 if x[2] == "NewYork"][0]
    assert lon3[0] == ts(2024, 10, 30, 8, 0)    # back to GMT
    assert ny3[0] == ts(2024, 10, 30, 13, 30)   # still EDT


def test_swap_calendar_wednesday_x3_no_fri_sat_events():
    assert cal.SWAP_CALENDAR == {"Sun": 1, "Mon": 1, "Tue": 1, "Wed": 3,
                                 "Thu": 1, "Fri": 0, "Sat": 0}
    # one full week (Fri 2024-06-07 20:00 -> Fri 2024-06-14 20:00)
    ev = cal.swap_events_between(ts(2024, 6, 7, 20), ts(2024, 6, 14, 20))
    assert [e.multiplier for e in ev] == [1, 1, 1, 3, 1]  # Sun..Thu
    assert sum(e.multiplier for e in ev) == 7             # 7 pip-nights
    assert [e.weekday for e in ev] == ["Sun", "Mon", "Tue", "Wed", "Thu"]
    wed = [e for e in ev if e.weekday == "Wed"][0]
    assert wed.wed_x3 and wed.ts_utc == ts(2024, 6, 12, 22)
    # boundary semantics: events at 22:00 exactly belong to (start, end]
    ev2 = cal.swap_events_between(ts(2024, 6, 9, 21, 59),
                                  ts(2024, 6, 9, 22, 0))
    assert len(ev2) == 1


def test_rollover_and_reopen_windows():
    assert cal.is_in_rollover_window(ts(2024, 6, 5, 21, 30))
    assert cal.is_in_rollover_window(ts(2024, 6, 5, 22, 30))
    assert not cal.is_in_rollover_window(ts(2024, 6, 5, 20, 59))
    assert not cal.is_in_rollover_window(ts(2024, 6, 5, 23, 0))
    # C2 charge window is the declared (21:00, 22:00]
    assert not cal.is_in_roll_charge_window(ts(2024, 6, 5, 21, 0))
    assert cal.is_in_roll_charge_window(ts(2024, 6, 5, 21, 30))
    assert cal.is_in_roll_charge_window(ts(2024, 6, 5, 22, 0))
    assert not cal.is_in_roll_charge_window(ts(2024, 6, 5, 22, 1))
    assert cal.is_hard_flat_instant(ts(2024, 6, 5, 19, 55))
    assert not cal.is_hard_flat_instant(ts(2024, 6, 5, 19, 54))
