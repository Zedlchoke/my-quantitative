"""PAPERDESK UPGRADE V2 — U5 battery: RICHER AI EVIDENCE.
ERRATUM (evidence-collector fix cycle, owner plan 2026-10-22 F1–F7):
the collector law changed and this battery was re-based on it —
  F1  WSL addresses ESPN as "soccer/eng.w.1" (generic "soccer" is dead:
      news 404 / board errors); non-ESPN match ids (the WSL lane's FD-*)
      are matched on the board by BOTH TEAM NAMES (token match after
      women-marker stripping) — id matching stays for ESPN-id lanes;
  F2  a bare {"$ref": …} injuries item is resolved with EXACTLY ONE hop
      GET (hard cap 1, hop journaled); unresolvable => honest zero;
  F3  the ROSTER layer is REMOVED (site roster returns athletes=0 —
      live-checked); the removal is journaled in every collection and no
      /roster URL is ever fetched;
  F4  board days = the ET date of kickoff ±1 day, journaled per query;
  F5  WSL self-captures exactly +2 hosts: the match's Polymarket GAMMA
      event page (caller-threaded URL) and the official league page
      (wslfootball.com/fixtures/); host-allow-listed; failures honest.

Covers, with FULLY STUBBED transport (ai_research._get_json/_get_text
monkeypatched — never real network).
"""
from __future__ import annotations

import sys
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from research.papertrade_exec import ai_research as AR   # noqa: E402

NOW = datetime.now(timezone.utc)
KICK_TOMORROW = (NOW + timedelta(days=1))\
    .replace(hour=6, minute=0, second=0, microsecond=0)\
    .strftime("%Y-%m-%dT%H:%M:%SZ")


@pytest.fixture(autouse=True)
def _reset_board_cache():
    AR._BOARD_CACHE.clear()          # integrator wiring: boards cached
    yield
    AR._BOARD_CACHE.clear()


def _iso_ahead(hours: float) -> str:
    return (NOW + timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _f4_days(kickoff_iso: str) -> list[str]:
    dt = datetime.fromisoformat(kickoff_iso.replace("Z", "+00:00"))
    et = dt.astimezone(ZoneInfo("America/New_York")).date()
    return sorted({(et + timedelta(o)).strftime("%Y%m%d")
                   for o in (-1, 0, 1)})


def _news_item(headline: str, link: str, *, published: str | None = None,
               description: str = "") -> dict:
    return {"published": published or _iso_ahead(-1),
            "headline": headline, "description": description,
            "lastModified": published or _iso_ahead(-1),
            "links": {"web": {"href": link}}}


NEWS = {"articles": [
    _news_item("Oklahoma City Thunder grind out a road win",
               "https://www.espn.com/nba/story/_/id/101"),
    _news_item("Oklahoma City Thunder star (knee) listed out for Wednesday",
               "https://www.espn.com/nba/story/_/id/102"),
    _news_item("Front-office chatter around the league at the deadline",
               "https://www.espn.com/nba/story/_/id/103"),
]}

# F2: the REAL core-API shape — a bare $ref that resolves on a second GET
INJURY_REF = ("https://sports.core.api.espn.com/v2/sports/basketball/"
              "leagues/nba/injuries/9001")
INJURIES = {
    "16": {"items": [{"$ref": INJURY_REF + "?lang=en"}]},
    "7": {"items": []},
}
INJURY_RESOLVED = {
    "athlete": {"$ref": "https://sports.core.api.espn.com/v2/sports/"
                "basketball/leagues/nba/seasons/2027/athletes/1"},
    "status": "Out",                       # live shape: plain string
    "details": {"type": "Knee", "location": "Knee", "side": "Right"},
    "shortComment": "Williams (knee) is out for Wednesday's game.",
    "lastUpdate": "2026-10-20T15:30:00Z",
}

WSL_BOARD_EVENT = {
    "id": "401922222",
    "date": "2026-10-24T11:45Z",
    "competitions": [{
        "competitors": [
            {"homeAway": "home", "team": {"displayName": "Brighton & Hove"
                                          " Albion Women", "id": "36001"}},
            {"homeAway": "away", "team": {"displayName": "West Ham United"
                                          " Women", "id": "36002"}},
        ],
        "status": {"type": {"detail": "Sat, October 24 at 11:45 AM UTC"}},
    }],
}


def _stub_get_json(calls: list):
    def fake(url: str, timeout: int = 15) -> dict:
        calls.append(url)
        if "/news?" in url:
            return NEWS
        if "/injuries" in url and "/injuries/" in url:
            # F2: a $ref hop (single injury resource)
            if url.split("?")[0] == INJURY_REF:
                return INJURY_RESOLVED
            raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
        if "/injuries" in url:
            tid = url.rsplit("/teams/", 1)[1].split("/")[0]
            if tid in INJURIES:
                return INJURIES[tid]
            raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
        if "/scoreboard?" in url:
            day = url.split("dates=")[1].split("&")[0]
            if "eng.w.1" in url:
                if day in _f4_days(KICK_TOMORROW):
                    return {"events": [WSL_BOARD_EVENT]}
                return {"events": []}
            if day in _f4_days(KICK_TOMORROW):
                return {"events": [{
                    "id": "401777",
                    "competitions": [{"status": {"type": {
                        "detail": "Thu, October 22 at 12:10 AM UTC"}}}]}]}
            return {"events": []}
        if url.startswith("https://gamma-api.polymarket.com/events"):
            return [{"title": "Brighton and Hove Albion WFC vs. West Ham"
                     " United FC",
                     "description": "This event is for the upcoming"
                     " Women's Super League game.",
                     "startDate": "2026-10-24T11:45:00Z"}]
        raise AssertionError(f"unexpected URL in stub router: {url}")
    return fake


def _stub_get_text(calls: list):
    def fake(url: str, timeout: int = 20, max_bytes: int = 3_000_000) -> str:
        calls.append(url)
        if url == "https://wslfootball.com/fixtures/":
            return ("Brighton & Hove Albion Women v West Ham United Women"
                    " — Saturday 24 October, 11:45 UTC, Broadfield Stadium"
                    " — WSL Football fixtures and results")
        raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
    return fake


# --------------------------------- 1) F4 scoreboard board days --------------

def test_f4_board_days_are_et_date_plus_adjacent(monkeypatch):
    calls: list = []
    monkeypatch.setattr(AR, "_get_json", _stub_get_json(calls))
    out = AR.collect_evidence(league="NBA", match_id="401777",
                              home="Oklahoma City Thunder",
                              away="Golden State Warriors",
                              kickoff_utc=KICK_TOMORROW)
    days = _f4_days(KICK_TOMORROW)
    assert len(days) == 3                            # D-1, D, D+1 (ET)
    et_day = (datetime.fromisoformat(KICK_TOMORROW.replace("Z", "+00:00"))
              .astimezone(ZoneInfo("America/New_York")).date()
              .strftime("%Y%m%d"))
    # the MATCH day is queried FIRST, then adjacent days as fallbacks;
    # found on the first hit => exactly ONE status citation, and the
    # 3-day window is journaled regardless
    board_calls = [u for u in calls if "/scoreboard?" in u]
    assert any(f"dates={et_day}" in u for u in board_calls)
    assert any(f"dates={et_day}" in q for q in out["queries"])
    day_qs = " ".join(q for q in out["queries"] if "F4 board days" in q)
    assert all(d in day_qs for d in days)            # all 3 days journaled
    ev = [s for s in out["sources"]
          if s["kind"] == "scoreboard_status"
          and "event=401777" in s["url"]]
    assert len(ev) == 1
    assert ev[0]["excerpt"] == "Thu, October 22 at 12:10 AM UTC"
    for s in out["sources"]:
        assert s["url"] and s["fetched_at_utc"] and "excerpt" in s \
            and "published_utc" in s


def test_f4_unparsable_kickoff_means_no_board_days(monkeypatch):
    calls: list = []
    monkeypatch.setattr(AR, "_get_json", _stub_get_json(calls))
    out = AR.collect_evidence(league="NBA", match_id="401777",
                              home="Oklahoma City Thunder",
                              away="Golden State Warriors",
                              kickoff_utc="not-a-date")
    assert not [u for u in calls if "/scoreboard?" in u]
    assert "unparsable" in (out.get("scoreboard_note") or "")


# --------------------------------- 2) F3 roster layer REMOVED ---------------

def test_f3_roster_layer_removed_and_journaled(monkeypatch):
    calls: list = []
    monkeypatch.setattr(AR, "_get_json", _stub_get_json(calls))
    out = AR.collect_evidence(league="NBA", match_id="401777",
                              home="Oklahoma City Thunder",
                              away="Golden State Warriors",
                              kickoff_utc=KICK_TOMORROW,
                              team_ids={"home": "16", "away": "7"})
    assert not [u for u in calls if u.endswith("/roster")]
    assert any("roster layer removed" in q for q in out["queries"])
    # the news filter still runs on TEAM names
    assert "https://www.espn.com/nba/story/_/id/101" in \
        [s["url"] for s in out["sources"] if s["kind"] == "news_48h"]
    assert not hasattr(AR, "_ROSTER_CACHE")


# --------------------------------- 3) F2 injuries with $ref resolution ------

def test_f2_bare_ref_injury_resolved_with_one_journaled_hop(monkeypatch):
    calls: list = []
    monkeypatch.setattr(AR, "_get_json", _stub_get_json(calls))
    out = AR.collect_evidence(league="NBA", match_id="401777",
                              home="Oklahoma City Thunder",
                              away="Golden State Warriors",
                              kickoff_utc=KICK_TOMORROW,
                              team_ids={"home": "16", "away": "7"})
    core = "https://sports.core.api.espn.com/v2/sports/basketball/" \
           "leagues/nba/teams"
    inj = [s for s in out["sources"] if s["kind"] == "injuries"]
    assert len(inj) == 1
    assert inj[0]["url"] == f"{core}/16/injuries"
    assert inj[0]["excerpt"] == \
        "Williams (knee) is out for Wednesday's game."
    assert inj[0]["published_utc"] == "2026-10-20T15:30:00Z"
    hops = [q for q in out["queries"] if "$ref hop (cap 1)" in q]
    assert len(hops) == 1 and "OK" in hops[0]        # the hop is journaled
    assert sum(1 for u in calls if u.startswith(INJURY_REF)) == 1
    # away team 7 has zero items: journaled, nothing invented
    qs = [q for q in out["queries"]
          if "/injuries" in q and "teams/7" in q and "items=0" in q]
    assert qs


def test_f2_unresolvable_ref_is_an_honest_zero(monkeypatch):
    calls: list = []
    stub = _stub_get_json(calls)

    def failing_ref(url: str, timeout: int = 15) -> dict:
        calls.append(url)
        if url.split("?")[0] == INJURY_REF:
            raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
        return stub(url, timeout)

    monkeypatch.setattr(AR, "_get_json", failing_ref)
    out = AR.collect_evidence(league="NBA", match_id="401777",
                              home="Oklahoma City Thunder",
                              away="Golden State Warriors",
                              kickoff_utc=KICK_TOMORROW,
                              team_ids={"home": "16", "away": "7"})
    assert not [s for s in out["sources"] if s["kind"] == "injuries"]
    assert any("$ref hop (cap 1)" in q and "ERROR" in q
               for q in out["queries"])
    assert any("never invented" in q for q in out["queries"])


def test_injuries_skipped_without_verified_competition_or_team_ids(monkeypatch):
    calls: list = []
    monkeypatch.setattr(AR, "_get_json", _stub_get_json(calls))
    out = AR.collect_evidence(league="SOCCER", match_id="701",
                              home="Arsenal", away="Chelsea",
                              kickoff_utc=KICK_TOMORROW,
                              team_ids={"home": "1", "away": "2"})
    assert "no verified ESPN path for competition" in out["why"]
    assert not [u for u in calls if "/injuries" in u]
    out2 = AR.collect_evidence(league="NBA", match_id="401777",
                               home="Oklahoma City Thunder",
                               away="Golden State Warriors",
                               kickoff_utc=KICK_TOMORROW, team_ids=None)
    assert not [u for u in calls if "/injuries" in u and "teams/" in u]


# --------------------------------- 4) F1 WSL: eng.w.1 + name matching -------

def test_f1_wsl_slug_and_name_based_board_match(monkeypatch):
    calls: list = []
    monkeypatch.setattr(AR, "_get_json", _stub_get_json(calls))
    ids = AR.lookup_team_ids(league="WSL", match_id="FD-2026-M48",
                             kickoff_utc=KICK_TOMORROW,
                             home="Brighton & Hove Albion",
                             away="West Ham United")
    assert ids == {"home": "36001", "away": "36002"}   # by NAME, not FD-*
    assert any("eng.w.1/scoreboard" in u for u in calls)
    out = AR.collect_evidence(league="WSL", match_id="FD-2026-M48",
                              home="Brighton & Hove Albion",
                              away="West Ham United",
                              kickoff_utc=KICK_TOMORROW)
    st = [s for s in out["sources"]
          if s["kind"] == "scoreboard_status"]
    assert len(st) == 1
    assert st[0]["excerpt"] == "Sat, October 24 at 11:45 AM UTC"
    assert out.get("team_ids_lookup") == "board"
    assert any("names=" in q for q in out.get("scoreboard_matches", []))


# --------------------------------- 5) F5 self-captures (+2 hosts only) ------

def test_f5_gamma_and_official_page_captured(monkeypatch):
    calls: list = []
    monkeypatch.setattr(AR, "_get_json", _stub_get_json(calls))
    monkeypatch.setattr(AR, "_get_text", _stub_get_text(calls))
    out = AR.collect_evidence(league="WSL", match_id="FD-2026-M48",
                              home="Brighton & Hove Albion",
                              away="West Ham United",
                              kickoff_utc=KICK_TOMORROW,
                              gamma_event_url="https://gamma-api."
                              "polymarket.com/events?id=1212928")
    kinds = [s["kind"] for s in out["sources"]]
    assert "gamma_event" in kinds and "league_official" in kinds
    g = [s for s in out["sources"] if s["kind"] == "gamma_event"][0]
    assert g["url"].endswith("id=1212928")
    assert "Brighton and Hove Albion WFC" in g["excerpt"]
    lo = [s for s in out["sources"] if s["kind"] == "league_official"][0]
    assert lo["url"] == "https://wslfootball.com/fixtures/"
    assert "West Ham" in lo["excerpt"]               # window names the tie


def test_f5_absent_gamma_and_off_host_are_honest_zeros(monkeypatch):
    calls: list = []
    monkeypatch.setattr(AR, "_get_json", _stub_get_json(calls))
    monkeypatch.setattr(AR, "_get_text", _stub_get_text(calls))
    out = AR.collect_evidence(league="WSL", match_id="FD-2026-M48",
                              home="Brighton & Hove Albion",
                              away="West Ham United",
                              kickoff_utc=KICK_TOMORROW,
                              gamma_event_url=None)
    assert "gamma_event skipped" in " ".join(out["queries"])
    # NBA has no official-page mapping: no wslfootball fetch for NBA
    n_before = len([u for u in calls if "wslfootball" in u])
    out2 = AR.collect_evidence(league="NBA", match_id="401777",
                               home="Oklahoma City Thunder",
                               away="Golden State Warriors",
                               kickoff_utc=KICK_TOMORROW)
    assert not [s for s in out2["sources"]
                if s["kind"] in ("league_official", "gamma_event")]
    assert len([u for u in calls if "wslfootball" in u]) == n_before
    # a gamma URL OUTSIDE the F5 host allow-list is refused, journaled
    out3 = AR.collect_evidence(league="WSL", match_id="FD-2026-M48",
                               home="Brighton & Hove Albion",
                               away="West Ham United",
                               kickoff_utc=KICK_TOMORROW,
                               gamma_event_url="https://evil.example.com/"
                               "events?id=1")
    assert not [s for s in out3["sources"] if s["kind"] == "gamma_event"]
    assert any("gamma_event ERROR" in q and "allow-list" in q
               for q in out3["queries"])


# --------------------------------- 6) evidence stats ------------------------

def test_evidence_stats_news_only_world(monkeypatch):
    """SIMULATED (re-based after F3): the filter is team-name-only; stats
    stay honest over {candidate: [news sources]}."""
    monkeypatch.setattr(AR, "_get_json", _stub_get_json([]))
    by_c = {}
    for i, (home, away) in enumerate([
            ("Oklahoma City Thunder", "Golden State Warriors"),
            ("San Antonio Spurs", "Portland Trail Blazers"),
            ("Miami Heat", "Denver Nuggets")]):
        out = AR.collect_evidence(league="NBA", match_id=f"m{i}",
                                  home=home, away=away,
                                  kickoff_utc=KICK_TOMORROW)
        by_c[f"m{i}"] = [{"url": s["url"]} for s in out["sources"]
                         if s["kind"] == "news_48h"]
    st = AR.collect_evidence_stats(by_c)
    assert st["candidates"] == 3
    assert st["candidates_with_sources"] == 1        # only the OKC pair
    assert st["share_with_sources"] == pytest.approx(1 / 3)
    assert AR.collect_evidence_stats({})["share_with_sources"] == 0.0
