"""A1 arm composition: strata membership, weekend bucketing, dedup identity."""

import sys, os, json, gzip
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import FakeStore, NO_CA, make_panel, TempExDates  # noqa: E402

from engine_x.a1_books import build_a1_book, load_a1_events  # noqa: E402

SESSIONS = ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05",
            "2024-01-08", "2024-01-09", "2024-01-10", "2024-01-11",
            "2024-01-12", "2024-01-15"]


def _panel():
    return make_panel("TEST", [(d, 100.0, 101.0) for d in SESSIONS])


def _events_file(tmp_path, rows):
    p = tmp_path / "a1_events.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return str(p)


def test_weekend_acceptance_goes_to_separate_bucket_not_anchor(tmp_path):
    # Saturday 2024-01-06 18:30 ET (23:30Z): clock stratum S3 but weekend
    ev = {"cik": "CIK0000000001", "ticker": "TEST", "form": "10-Q",
          "accession": "A1", "acceptance_utc": "2024-01-06T23:30:00.000Z",
          "filing_date": "2024-01-06", "report_date": "2024-01-01"}
    path = _events_file(tmp_path, [ev])
    run = build_a1_book(path, FakeStore({"TEST": _panel()}), NO_CA, "anchor")
    assert run.census["booked"] == 0
    assert run.census["weekend_bucket_candidates"] == 1
    assert run.excluded[0]["reason"] == "WEEKEND_BUCKET_SEPARATE"
    assert run.records == []


def test_s2_event_not_in_anchor_but_in_n2(tmp_path):
    # Wed 2024-01-03 15:00 ET (20:00Z) -> S2
    ev = {"cik": "CIK0000000001", "ticker": "TEST", "form": "10-Q",
          "accession": "A2", "acceptance_utc": "2024-01-03T20:00:00.000Z",
          "filing_date": "2024-01-03", "report_date": "2024-01-01"}
    path = _events_file(tmp_path, [ev])
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
    rows = [
        {"cik": "CIK0000000001", "ticker": "TEST", "form": "10-K",
         "accession": "B", "acceptance_utc": "2024-01-02T23:30:00.000Z",
         "filing_date": "2024-01-02", "report_date": "2024-01-01"},
        {"cik": "CIK0000000001", "ticker": "TEST", "form": "10-Q",
         "accession": "A", "acceptance_utc": "2024-01-02T23:30:00.000Z",
         "filing_date": "2024-01-02", "report_date": "2024-01-01"},
    ]
    events = load_a1_events(_events_file(tmp_path, rows))
    assert len(events) == 1
    assert events[0]["form"] == "10-K"  # lexicographically smallest form wins (AMB-12)


def test_distinct_issuers_same_instant_are_two_events(tmp_path):
    rows = [
        {"cik": "CIK0000000001", "ticker": "TEST", "form": "10-Q",
         "accession": "A", "acceptance_utc": "2024-01-02T23:30:00.000Z",
         "filing_date": "2024-01-02", "report_date": "-"},
        {"cik": "CIK0000000002", "ticker": "TEST", "form": "10-Q",
         "accession": "B", "acceptance_utc": "2024-01-02T23:30:00.000Z",
         "filing_date": "2024-01-02", "report_date": "-"},
    ]
    events = load_a1_events(_events_file(tmp_path, rows))
    assert len(events) == 2


def test_anchor_book_record_shape(tmp_path):
    ev = {"cik": "CIK0000000001", "ticker": "TEST", "form": "10-K",
          "accession": "A", "acceptance_utc": "2024-01-02T23:30:00.000Z",
          "filing_date": "2024-01-02", "report_date": "2023-12-31"}
    run = build_a1_book(_events_file(tmp_path, [ev]),
                        FakeStore({"TEST": _panel()}), NO_CA, "anchor")
    assert run.census["booked"] == 1
    r = run.records[0]
    for k in ("event_id", "cik", "ticker", "form", "acceptance_utc", "stratum",
              "direction_session", "direction", "entry_session", "entry_price",
              "exit_session", "exit_price", "exclusions_applied", "delisting_exit"):
        assert k in r
    assert r["event_id"] == "EMV1-A1:CIK0000000001:2024-01-02T23:30:00.000Z"
    assert r["direction"] == 1
    assert r["entry_price"] == 100.0 and r["exit_price"] == 101.0
    assert r["delisting_exit"] is False


def test_ca_excluded_event_leaves_book_and_is_counted(tmp_path):
    ex = TempExDates({"TEST": ({"2024-01-09"}, set())})
    ev = {"cik": "CIK0000000001", "ticker": "TEST", "form": "10-Q",
          "accession": "A", "acceptance_utc": "2024-01-03T20:00:00.000Z",
          "filing_date": "2024-01-03", "report_date": "-"}
    run = build_a1_book(_events_file(tmp_path, [ev]),
                        FakeStore({"TEST": _panel()}), ex, "n2")
    assert run.census["booked"] == 0
    assert run.census["excluded_by_reason"].get("CA_EXCLUSION") == 1
