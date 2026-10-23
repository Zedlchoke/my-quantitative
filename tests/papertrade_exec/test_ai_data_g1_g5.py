"""Focused G1/G3/G5 checks with no network or production writes."""
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from research.papertrade_exec import ai_research as R
from research.papertrade_exec import ai_producer as P
from research.papertrade_exec.ops_service import OpsService


def test_g1_gamma_url_only_from_quote_crosswalk(tmp_path, monkeypatch):
    rows = [
        {"type": "MARKET_QUOTE", "match_id": "846", "event_id": "wrong",
         "odds": {"HOME": 2.62, "AWAY": 1.53},
         "pm_crosswalk": {"pm_event_id": "1202604"}},
        {"type": "MARKET_QUOTE", "match_id": "missing", "event_id": "999"},
        {"type": "MARKET_QUOTE", "match_id": "unsafe",
         "pm_crosswalk": {"pm_event_id": "1&other=2"}},
    ]
    service = SimpleNamespace(_ledger_state=lambda: (None,
                                                       SimpleNamespace(rows=rows),
                                                       None))
    quotes = OpsService._market_quotes_for_pending(service)
    quote = P._candidate_quote(
        quotes, "846", {"odds_frozen": {"HOME": 2.62, "AWAY": 1.53}})
    assert quote is rows[0]
    ambiguous = [rows[0], {**rows[0], "row_sha256": "other"}]
    assert P._candidate_quote({"846": ambiguous}, "846",
                              {"odds_frozen": rows[0]["odds"]}) is None
    assert P._candidate_quote({"846": ambiguous}, "846",
                              {"odds_frozen": rows[0]["odds"],
                               "quote_row_sha256": "other"}) is ambiguous[1]
    assert P._gamma_url_from_quote(quote) == \
        "https://gamma-api.polymarket.com/events?id=1202604"
    assert P._gamma_url_from_quote(rows[1]) is None
    assert P._gamma_url_from_quote(rows[2]) is None
    seen = []
    monkeypatch.setattr(P.ai_research, "collect_evidence", lambda **kwargs:
                        seen.append(kwargs) or {"queries": [], "sources": []})
    entry = {"context": {"league": "NBA", "home": "Washington Wizards",
                         "away": "Toronto Raptors",
                         "odds_frozen": rows[0]["odds"]}}
    P._collect_candidate_evidence(entry, "846", tmp_path, True, quotes)
    assert seen[-1]["gamma_event_url"] == \
        "https://gamma-api.polymarket.com/events?id=1202604"
    P._collect_candidate_evidence(entry, "missing", tmp_path, True, quotes)
    assert seen[-1]["gamma_event_url"] is None
    queries = []
    assert R._gamma_source(None, queries,
                           datetime(2026, 10, 23, tzinfo=timezone.utc)) == []
    assert "0 sources" in queries[0]


def test_g3_collector_stamp_matches_executing_file(monkeypatch):
    monkeypatch.setattr(R, "_get_json", lambda *_a, **_k: {})
    out = R.collect_evidence(league="UNMAPPED", match_id="x",
                             home="H", away="A")
    assert out["collector_sha256"] == hashlib.sha256(
        Path(R.__file__).read_bytes()).hexdigest()


def test_g5_injury_timestamps_age_and_stale():
    at = datetime(2026, 10, 23, 12, tzinfo=timezone.utc)
    for raw, expected in (("2026-10-22T03:40Z", "2026-10-22T03:40:00Z"),
                          ("2026-10-22T03:40:13Z", "2026-10-22T03:40:13Z")):
        q = []
        src = R._resolve_injury_item(
            {"lastUpdate": raw, "shortComment": "Out"}, q, at, "https://x")
        assert src["published_utc"] == expected
        assert isinstance(src["age_days"], float)
        assert src["stale"] is False
    old = R._resolve_injury_item(
        {"lastUpdate": "2026-07-30T03:40Z", "shortComment": "ACL"},
        [], at, "https://x")
    assert old["stale"] is True and old["age_days"] > 21
    q = []
    bad = R._resolve_injury_item(
        {"lastUpdate": "bad", "shortComment": "Out"}, q, at, "https://x")
    assert bad["published_utc"] == "" and bad["age_days"] is None
    assert "unparsable" in q[0]
