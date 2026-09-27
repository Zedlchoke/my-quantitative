"""A2 event set + anchor book: value floor, amendment drop, officer/director
gate, unpriced-row drop (r3 AMB-6), open-anchored sequencing (r3 D-1), hold 10."""

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import NO_CA, FakeStore, TempExDates, make_panel, write_xml, weekday_sessions  # noqa: E402

from engine_x.a2_books import build_a2_book  # noqa: E402

# Long grid so the DVmed60 floor (>=30 trailing sessions) passes for
# January 2024 events.
SESSIONS = weekday_sessions("2023-11-01", "2024-02-15")


def _panel(volumes=None):
    return make_panel("TEST", [(d, 100.0, 101.0) for d in SESSIONS],
                      volumes=volumes)


def _n4(tmp_path):
    p = tmp_path / "n4.jsonl"
    p.write_text(json.dumps({"ticker": "TEST", "cik": "CIK0000000001",
                             "bucket": "ALIVE_EVIDENCED"}) + "\n")
    return str(p)


def _stream(tmp_path, rows):
    p = tmp_path / "form4_stream.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return str(p)


OD_OWNER = {"cik": "CIK0000000009", "name": "BOSS", "director": 1, "officer": 0}
OTHER_OWNER = {"cik": "CIK0000000010", "name": "OTHER", "director": 0, "officer": 0}


def _row(accession, acceptance, tdate, code="P", direction="A", shares="5000"):
    return {"cik": "CIK0000000001", "accession": accession, "acceptance": acceptance,
            "filing_date": tdate, "transaction_date": tdate, "transaction_code": code,
            "direction": direction, "shares": shares, "owner_cik": None,
            "owner_name": "BOSS", "table": "nonDerivative"}


def test_value_floor_and_sequencing(tmp_path):
    # 5000 sh @ $21 = $105,000 >= floor. Acceptance 2024-01-02T23:30Z (18:30
    # ET, after close) -> A2 entry = first open STRICTLY after = 01-03;
    # exit = 10th session from 01-03 = 01-16.
    x = write_xml(str(tmp_path), "CIK0000000001", "ACC1", "4",
                  [OD_OWNER], [{"code": "P", "date": "2024-01-02",
                                "shares": "5000", "price": "21.0"}])
    assert os.path.exists(x)
    s = _stream(tmp_path, [_row("ACC1", "2024-01-02T23:30:00.000Z", "2024-01-02")])
    records, census, excluded, drops = build_a2_book(
        s, str(tmp_path), _n4(tmp_path), FakeStore({"TEST": _panel()}), NO_CA)
    assert census["event_set"]["events_above_floor"] == 1
    assert len(records) == 1
    r = records[0]
    assert r["event_id"] == "EMV1-A2:CIK0000000001:2024-01-02"
    assert r["entry_session"] == "2024-01-03"          # first open after instant
    assert r["exit_session"] == "2024-01-16"           # +9 sessions
    assert r["hold_sessions"] == 10 and r["direction"] == "LONG"
    assert r["buy_value"] == 105000.0


def test_value_below_floor_excluded_from_event_set(tmp_path):
    # 4000 * $21 = $84,000 < $100,000 floor -> not an event
    x = write_xml(str(tmp_path), "CIK0000000001", "ACC1", "4",
                  [OD_OWNER], [{"code": "P", "date": "2024-01-02",
                                "shares": "4000", "price": "21.0"}])
    s = _stream(tmp_path, [_row("ACC1", "2024-01-02T23:30:00.000Z", "2024-01-02")])
    records, census, excluded, drops = build_a2_book(
        s, str(tmp_path), _n4(tmp_path), FakeStore({"TEST": _panel()}), NO_CA)
    assert census["event_set"]["events_above_floor"] == 0 and records == []


def test_exact_floor_boundary_inclusive(tmp_path):
    # 5000 @ $20 = exactly $100,000 -> >= floor -> included
    x = write_xml(str(tmp_path), "CIK0000000001", "ACC1", "4",
                  [OD_OWNER], [{"code": "P", "date": "2024-01-02",
                                "shares": "5000", "price": "20.0"}])
    s = _stream(tmp_path, [_row("ACC1", "2024-01-02T23:30:00.000Z", "2024-01-02")])
    records, census, *_ = build_a2_book(
        s, str(tmp_path), _n4(tmp_path), FakeStore({"TEST": _panel()}), NO_CA)
    assert census["event_set"]["events_above_floor"] == 1


def test_amendment_accession_dropped(tmp_path):
    x = write_xml(str(tmp_path), "CIK0000000001", "ACC1", "4/A",
                  [OD_OWNER], [{"code": "P", "date": "2024-01-02",
                                "shares": "9000", "price": "20.0"}])
    s = _stream(tmp_path, [_row("ACC1", "2024-01-02T23:30:00.000Z", "2024-01-02")])
    records, census, *_ = build_a2_book(
        s, str(tmp_path), _n4(tmp_path), FakeStore({"TEST": _panel()}), NO_CA)
    assert census["event_set"]["amendment_accessions"] == 1
    assert census["event_set"]["events_above_floor"] == 0


def test_non_officer_director_filing_dropped(tmp_path):
    x = write_xml(str(tmp_path), "CIK0000000001", "ACC1", "4",
                  [OTHER_OWNER], [{"code": "P", "date": "2024-01-02",
                                   "shares": "9000", "price": "20.0"}])
    s = _stream(tmp_path, [_row("ACC1", "2024-01-02T23:30:00.000Z", "2024-01-02")])
    records, census, *_ = build_a2_book(
        s, str(tmp_path), _n4(tmp_path), FakeStore({"TEST": _panel()}), NO_CA)
    assert census["event_set"]["non_od_accessions"] == 1
    assert census["event_set"]["events_above_floor"] == 0


def test_unpriced_xml_row_dropped_not_imputed(tmp_path):
    """r3 AMB-6 CANONICAL: an unpriced XML row drops + counts — the
    pre-r3 panel-close fallback is removed (no imputation)."""
    x = write_xml(str(tmp_path), "CIK0000000001", "ACC1", "4",
                  [OD_OWNER], [{"code": "P", "date": "2024-01-02",
                                "shares": "5000", "price": "0"}])
    s = _stream(tmp_path, [_row("ACC1", "2024-01-02T23:30:00.000Z", "2024-01-02")])
    records, census, excluded, drops = build_a2_book(
        s, str(tmp_path), _n4(tmp_path), FakeStore({"TEST": _panel()}), NO_CA)
    assert census["event_set"]["rows_no_price"] == 1
    assert census["event_set"]["events_above_floor"] == 0
    assert records == []
    assert any(d["reason"] == "A2_ROW_UNPRICED" for d in drops)


def test_dv_floor_excludes_at_book_stage(tmp_path):
    # dv = 101 * 100 = $10,100 << $2M -> BELOW_DV_FLOOR_AT_DECISION
    vols = [100.0] * len(SESSIONS)
    x = write_xml(str(tmp_path), "CIK0000000001", "ACC1", "4",
                  [OD_OWNER], [{"code": "P", "date": "2024-01-02",
                                "shares": "5000", "price": "21.0"}])
    s = _stream(tmp_path, [_row("ACC1", "2024-01-02T23:30:00.000Z", "2024-01-02")])
    records, census, excluded, *_ = build_a2_book(
        s, str(tmp_path), _n4(tmp_path), FakeStore({"TEST": _panel(volumes=vols)}), NO_CA)
    assert records == []
    assert census["excluded_by_reason"].get("BELOW_DV_FLOOR_AT_DECISION") == 1


def test_issuer_day_aggregates_two_filings_and_earliest_acceptance(tmp_path):
    x1 = write_xml(str(tmp_path), "CIK0000000001", "ACC1", "4",
                   [OD_OWNER], [{"code": "P", "date": "2024-01-02",
                                 "shares": "3000", "price": "20.0"}])
    x2 = write_xml(str(tmp_path), "CIK0000000001", "ACC2", "4",
                   [{"cik": "CIK0000000011", "name": "CFO", "director": 0, "officer": 1}],
                   [{"code": "P", "date": "2024-01-02",
                     "shares": "2000", "price": "20.0"}])
    s = _stream(tmp_path, [
        _row("ACC1", "2024-01-03T01:00:00.000Z", "2024-01-02"),
        _row("ACC2", "2024-01-02T21:00:00.000Z", "2024-01-02"),
    ])
    records, census, *_ = build_a2_book(
        s, str(tmp_path), _n4(tmp_path), FakeStore({"TEST": _panel()}), NO_CA)
    assert census["event_set"]["events_above_floor"] == 1
    r = records[0]
    assert r["buy_value"] == 100000.0
    assert r["acceptance_utc"] == "2024-01-02T21:00:00.000Z"  # earliest (AMB-04)
    assert r["cluster_size"] == 2                             # distinct insiders


def test_a2_during_session_acceptance_enters_next_day(tmp_path):
    # acceptance mid-session Wed 01-03 12:00 ET (17:00Z): Wed 09:30 open is
    # BEFORE the instant -> first open strictly after = Thu 01-04 open;
    # exit = 01-04 + 9 sessions = 01-17.
    x = write_xml(str(tmp_path), "CIK0000000001", "ACC1", "4",
                  [OD_OWNER], [{"code": "P", "date": "2024-01-02",
                                "shares": "5000", "price": "21.0"}])
    s = _stream(tmp_path, [_row("ACC1", "2024-01-03T17:00:00.000Z", "2024-01-02")])
    records, census, excluded, drops = build_a2_book(
        s, str(tmp_path), _n4(tmp_path), FakeStore({"TEST": _panel()}), NO_CA)
    r = records[0]
    assert r["entry_session"] == "2024-01-04"
    assert r["exit_session"] == "2024-01-17"
    assert r["stratum"] == "S2"  # clock stratum recorded descriptively


def test_a2_ca_exclusion_applies(tmp_path):
    x = write_xml(str(tmp_path), "CIK0000000001", "ACC1", "4",
                  [OD_OWNER], [{"code": "P", "date": "2024-01-02",
                                "shares": "5000", "price": "21.0"}])
    ex = TempExDates({"TEST": ({"2024-01-10"}, set())})
    s = _stream(tmp_path, [_row("ACC1", "2024-01-02T23:30:00.000Z", "2024-01-02")])
    records, census, excluded, _ = build_a2_book(
        s, str(tmp_path), _n4(tmp_path), FakeStore({"TEST": _panel()}), ex)
    assert records == []
    assert census["excluded_by_reason"].get("CA_EXCLUSION") == 1
    assert excluded[0]["reason"] == "CA_EXCLUSION"


def test_f1_substrate_fact_zero(tmp_path):
    """Known F1=0: substrate starts 2018-01; an F1-dated event cannot exist."""
    # (documented fact — the builder never sees 2017 acceptances because the
    # pinned stream starts 2018-01-02; enforced here by the fold mapping.)
    from engine_x.a2_books import fold_of
    assert fold_of("2017-12-31") == "F1"
    assert fold_of("2018-01-02") == "F2"
    assert fold_of("2021-01-01") == "F3"
    assert fold_of("2023-01-01") == "F4"
