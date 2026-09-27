"""A1 arm composition: strata membership, WKND inclusion (r3 AMB-1), dedup
identity, DVmed60 floor at book stage, direction-tie exclusion (r3 AMB-11)."""

import sys, os, json, gzip
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import FakeStore, NO_CA, make_panel, weekday_sessions, TempExDates  # noqa: E402

from engine_x.a1_books import build_a1_book, load_a1_events  # noqa: E402

# Long grid so the DVmed60 floor (>=30 trailing sessions) passes for
# mid-January 2024 events.
SESSIONS = weekday_sessions("2023-11-01", "2024-01-31")


def _panel(volumes=None):
    return make_panel("TEST", [(d, 100.0, 101.0) for d in SESSIONS],
                      volumes=volumes)


def _events_file(tmp_path, rows):
    p = tmp_path / "a1_events.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return str(p)


def _ev(acceptance_utc, cik="CIK0000000001", form="10-Q", accession="A1"):
    return {"cik": cik, "ticker": "TEST", "form": form,
            "accession": accession, "acceptance_utc": acceptance_utc,
            "filing_date": acceptance_utc[:10], "report_date": "-"}


def test_weekend_acceptance_is_anchor_member_stratum_wknd(tmp_path):
    # Saturday 2024-01-06 18:30 ET (23:30Z): r3 AMB-1 — anchor member with
    # stratum label WKND; still excluded from N2 (S2-only).
    path = _events_file(tmp_path, [_ev("2024-01-06T23:30:00.000Z")])
    anchor = build_a1_book(path, FakeStore({"TEST": _panel()}), NO_CA, "anchor")
    n2 = build_a1_book(path, FakeStore({"TEST": _panel()}), NO_CA, "n2")
    assert anchor.census["booked"] == 1
    assert anchor.census["weekend_bucket_booked"] == 1
    assert anchor.records[0]["stratum"] == "WKND"
    assert anchor.records[0]["weekend_bucket"] is True
    assert n2.records == []
    assert n2.census["booked"] == 0


def test_s2_event_not_in_anchor_but_in_n2(tmp_path):
    # Wed 2024-01-03 15:00 ET (20:00Z) -> S2
    path = _events_file(tmp_path, [_ev("2024-01-03T20:00:00.000Z")])
    anchor = build_a1_book(path, FakeStore({"TEST": _panel()}), NO_CA, "anchor")
    n2 = build_a1_book(path, FakeStore({"TEST": _panel()}), NO_CA, "n2")
    assert anchor.records == []
    assert len(n2.records) == 1
    rec = n2.records[0]
    assert rec["stratum"] == "S2"
    assert rec["direction_session"] == "2024-01-03"
    assert rec["entry_session"] == "2024-01-04"
    assert rec["exit_session"] == "2024-01-10"


def test_dedup_identity_one_event_per_issuer_acceptance(tmp_path):
    # two forms at the same acceptance instant collapse to ONE event
    rows = [_ev("2024-01-02T23:30:00.000Z", form="10-K", accession="B"),
            _ev("2024-01-02T23:30:00.000Z", form="10-Q", accession="A")]
    events = load_a1_events(_events_file(tmp_path, rows))
    assert len(events) == 1
    assert events[0]["form"] == "10-K"  # lexicographically smallest form wins (AMB-12)


def test_distinct_issuers_same_instant_are_two_events(tmp_path):
    rows = [_ev("2024-01-02T23:30:00.000Z", cik="CIK0000000001", accession="A"),
            _ev("2024-01-02T23:30:00.000Z", cik="CIK0000000002", accession="B")]
    events = load_a1_events(_events_file(tmp_path, rows))
    assert len(events) == 2


def test_anchor_book_record_shape(tmp_path):
    run = build_a1_book(_events_file(tmp_path, [_ev("2024-01-02T23:30:00.000Z")]),
                        FakeStore({"TEST": _panel()}), NO_CA, "anchor")
    assert run.census["booked"] == 1
    r = run.records[0]
    for k in ("event_id", "cik", "ticker", "form", "acceptance_utc", "stratum",
              "direction_session", "direction", "entry_session", "entry_price",
              "exit_session", "exit_price", "exclusions_applied", "delisting_exit",
              "dv_band_class", "dvmed60_decision", "cost_entry_bps_x1",
              "cost_exit_bps_x1", "ticker_reuse_risk"):
        assert k in r, k
    assert r["event_id"] == "EMV1-A1:CIK0000000001:2024-01-02T23:30:00.000Z"
    assert r["direction"] == "LONG"
    assert r["entry_price"] == 100.0 and r["exit_price"] == 101.0
    assert r["delisting_exit"] is False
    # dv = 101 * 1e6 per bar >= $50M -> band A, open band 3.35x
    assert r["dv_band_class"] == "A"
    assert r["cost_entry_bps_x1"] == 33.5
    assert r["cost_exit_bps_x1"] == 10.0
    assert r["ticker_reuse_risk"] is False


def test_direction_tie_excluded_counted(tmp_path):
    # r3 AMB-11 CANONICAL: close == open on the direction session -> excluded
    p = make_panel("TEST", [(d, 100.0, 100.0) for d in SESSIONS])
    run = build_a1_book(_events_file(tmp_path, [_ev("2024-01-02T23:30:00.000Z")]),
                        FakeStore({"TEST": p}), NO_CA, "anchor")
    assert run.census["booked"] == 0
    assert run.census["excluded_by_reason"].get("ZERO_DIRECTION_SESSION_MOVE") == 1
    assert run.records == []


def test_dv_floor_excludes_at_book_stage(tmp_path):
    # dv = 101 * 100 = $10,100 << $2M floor -> BELOW_DV_FLOOR_AT_DECISION
    vols = [100.0] * len(SESSIONS)
    run = build_a1_book(_events_file(tmp_path, [_ev("2024-01-02T23:30:00.000Z")]),
                        FakeStore({"TEST": _panel(volumes=vols)}), NO_CA, "anchor")
    assert run.census["booked"] == 0
    assert run.census["excluded_by_reason"].get("BELOW_DV_FLOOR_AT_DECISION") == 1


def test_ca_excluded_event_leaves_book_and_is_counted(tmp_path):
    ex = TempExDates({"TEST": ({"2024-01-09"}, set())})
    run = build_a1_book(_events_file(tmp_path, [_ev("2024-01-03T20:00:00.000Z")]),
                        FakeStore({"TEST": _panel()}), ex, "n2")
    assert run.census["booked"] == 0
    assert run.census["excluded_by_reason"].get("CA_EXCLUSION") == 1


def test_ca_exdate_on_non_session_day_inside_window(tmp_path):
    # Saturday 2024-01-13 sits inside the calendar window [01-04 .. 01-16]
    # of an S2 event booked on 01-03 with H=8? (H=5 window is 01-04..01-10,
    # so use an acceptance whose window covers the weekend 01-13/01-14.)
    ex = TempExDates({"TEST": ({"2024-01-13"}, set())})  # Saturday, no bar
    # acceptance Thu 01-11 15:00 ET (16:00Z) -> direction 01-11, entry
    # 01-12, H=5 window 01-12..01-18 covers Sat 01-13 (calendar interval)
    run = build_a1_book(_events_file(tmp_path, [_ev("2024-01-11T16:00:00.000Z")]),
                        FakeStore({"TEST": _panel()}), ex, "n2")
    assert run.census["booked"] == 0
    assert run.census["excluded_by_reason"].get("CA_EXCLUSION") == 1
