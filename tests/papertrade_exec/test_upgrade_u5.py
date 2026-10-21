"""PAPERDESK UPGRADE V2 — U5 battery: RICHER AI EVIDENCE.

Covers, with FULLY STUBBED transport (ai_research._get_json monkeypatched
— never real network):
  1. scoreboard fetched by the MATCH's kickoff date PLUS today's board
     when the two differ; every board journaled; the event's status
     detail is the source excerpt; an absent event journaled honestly;
  2. the roster-name news filter: a headline naming a FIRST+LAST player
     from either team's roster passes even without the team name; roster
     fetched at most once per (league, team_id, day);
  3. per-team injuries from the ESPN core API (keyless): one citation per
     injury entry (url/fetched_at/excerpt/published), an erroring variant
     journaled honestly as a zero-source query — never invented;
  4. collect_evidence_stats + the SIMULATED before/after comparison:
     the OLD team-name-only filter drops a star-player injury headline,
     the NEW roster filter keeps it (shares computed from stub payloads).
"""
from __future__ import annotations

import sys
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from research.papertrade_exec import ai_research as AR   # noqa: E402

NOW = datetime.now(timezone.utc)
# a T-6h10m-style decision for TOMORROW's match: always a different
# calendar day than the run's "today", whatever time the battery runs.
KICK_TOMORROW = (NOW + timedelta(days=1))\
    .replace(hour=6, minute=0, second=0, microsecond=0)\
    .strftime("%Y-%m-%dT%H:%M:%SZ")
KICK_TODAY = NOW.replace(hour=23, minute=0, second=0, microsecond=0)\
    .strftime("%Y-%m-%dT%H:%M:%SZ")


@pytest.fixture(autouse=True)
def _reset_roster_cache():
    AR._ROSTER_CACHE.clear()
    AR._BOARD_CACHE.clear()          # integrator wiring: boards cached too
    yield
    AR._ROSTER_CACHE.clear()
    AR._BOARD_CACHE.clear()


def _iso_ahead(hours: float) -> str:
    return (NOW + timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _news_item(headline: str, link: str, *, published: str | None = None,
               description: str = "") -> dict:
    return {"published": published or _iso_ahead(-1),
            "headline": headline, "description": description,
            "lastModified": published or _iso_ahead(-1),
            "links": {"web": {"href": link}}}


NEWS = {"articles": [
    _news_item("Oklahoma City Thunder grind out a road win",
               "https://www.espn.com/nba/story/_/id/101"),
    _news_item("Jalen Williams (knee) listed out for Wednesday",
               "https://www.espn.com/nba/story/_/id/102"),
    _news_item("Front-office chatter around the league at the deadline",
               "https://www.espn.com/nba/story/_/id/103"),
]}

ROSTERS = {
    "16": {"team": {"athletes": [
        {"displayName": "Jalen Williams"},
        {"displayName": "Chet"}]                # single word: never matches
    }},
    "7": {"team": {"athletes": [
        {"firstName": "Mikal", "lastName": "Bridges"}]}},
    "25": {"team": {"athletes": []}},
    "31": {"team": {"athletes": [{"displayName": "Jalen Williams"}]}},
    "19": {"team": {"athletes": []}},
    "28": {"team": {"athletes": []}},
}

INJURIES = {
    "16": {"count": 1, "items": [{
        "id": "9001", "athlete": {"displayName": "Jalen Williams"},
        "status": {"type": "Out"},
        "details": {"detail": "Knee"},
        "lastUpdate": "2026-10-20T15:30:00Z"}]},
}


def _stub_get_json(calls: list):
    def fake(url: str, timeout: int = 15) -> dict:
        calls.append(url)
        if "/news?" in url:
            return NEWS
        if url.endswith("/roster"):
            tid = url.rsplit("/teams/", 1)[1].split("/")[0]
            if tid in ROSTERS:
                return ROSTERS[tid]
            raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
        if "/injuries" in url:
            tid = url.rsplit("/teams/", 1)[1].split("/")[0]
            if tid in INJURIES:
                return INJURIES[tid]
            raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
        if "/scoreboard?" in url:
            # only the kickoff-day board carries the event
            day = url.split("dates=")[1].split("&")[0]
            if day == KICK_TOMORROW.replace("-", "")[:8]:
                return {"events": [{
                    "id": "401777",
                    "competitions": [{"status": {"type": {
                        "detail": "Thu, October 22 at 12:10 AM UTC"}}}]}]}
            return {"events": []}
        raise AssertionError(f"unexpected URL in stub router: {url}")
    return fake


CANDIDATES = [
    # (home, away, team_ids) — c1 hit by TEAM name; c2 only by the ROSTER
    # player name; c3 by nothing (true negative)
    ("Oklahoma City Thunder", "Golden State Warriors",
     {"home": "16", "away": "7"}),
    ("San Antonio Spurs", "Portland Trail Blazers",
     {"home": "25", "away": "31"}),
    ("Miami Heat", "Denver Nuggets", {"home": "19", "away": "28"}),
]


# --------------------------------- 1) scoreboard by kickoff date ------------

def test_scoreboard_fetched_for_kickoff_date_and_today(monkeypatch):
    calls: list = []
    monkeypatch.setattr(AR, "_get_json", _stub_get_json(calls))
    out = AR.collect_evidence(league="NBA", match_id="401777",
                              home="Oklahoma City Thunder",
                              away="Golden State Warriors",
                              kickoff_utc=KICK_TOMORROW)
    kick_day = KICK_TOMORROW.replace("-", "")[:8]
    today = NOW.strftime("%Y%m%d")
    assert kick_day != today                       # T-6h10m: two boards
    board_calls = [u for u in calls if "/scoreboard?" in u]
    assert any(f"dates={kick_day}" in u for u in board_calls)
    assert any(f"dates={today}" in u for u in board_calls)
    qs = [q for q in out["queries"] if "scoreboard" in q]
    assert any(f"dates={kick_day}" in q for q in qs)
    assert any(f"dates={today}" in q for q in qs)
    ev = [s for s in out["sources"]
          if s["kind"] == "scoreboard_status"
          and f"dates={kick_day}#event=401777" in s["url"]]
    assert len(ev) == 1
    assert ev[0]["excerpt"] == "Thu, October 22 at 12:10 AM UTC"
    # every source keeps the full citation tuple
    for s in out["sources"]:
        assert s["url"] and s["fetched_at_utc"] and "excerpt" in s \
            and "published_utc" in s
    # today's board has no such event: journaled honestly, 0 invented
    notes = " ".join(out.get("scoreboard_notes", []))
    assert f"dates={today}" in notes and "absent" in notes
    assert not [s for s in out["sources"]
                if s["kind"] == "scoreboard_status"
                and f"dates={today}" in s["url"]]


def test_scoreboard_single_fetch_when_kickoff_is_today(monkeypatch):
    calls: list = []
    monkeypatch.setattr(AR, "_get_json", _stub_get_json(calls))
    out = AR.collect_evidence(league="NBA", match_id="401777",
                              home="Oklahoma City Thunder",
                              away="Golden State Warriors",
                              kickoff_utc=KICK_TODAY)
    board_calls = [u for u in calls if "/scoreboard?" in u]
    assert len(board_calls) == 1
    assert len([q for q in out["queries"] if "scoreboard" in q]) == 1


def test_unparsable_kickoff_falls_back_to_today_only(monkeypatch):
    calls: list = []
    monkeypatch.setattr(AR, "_get_json", _stub_get_json(calls))
    out = AR.collect_evidence(league="NBA", match_id="401777",
                              home="Oklahoma City Thunder",
                              away="Golden State Warriors",
                              kickoff_utc="not-a-date")
    board_calls = [u for u in calls if "/scoreboard?" in u]
    assert len(board_calls) == 1                   # today only, no guessing
    assert "unparsable" in (out.get("scoreboard_note") or "")


# --------------------------------- 2) roster-name news filter ---------------

def test_roster_name_keeps_star_player_headline(monkeypatch):
    calls: list = []
    monkeypatch.setattr(AR, "_get_json", _stub_get_json(calls))
    out = AR.collect_evidence(league="NBA", match_id="401777",
                              home="San Antonio Spurs",
                              away="Portland Trail Blazers",
                              kickoff_utc=KICK_TOMORROW,
                              team_ids={"home": "25", "away": "31"})
    news_urls = [s["url"] for s in out["sources"]
                 if s["kind"] == "news_48h"]
    assert "https://www.espn.com/nba/story/_/id/102" in news_urls
    # OLD behavior (team_ids absent -> roster layer inactive): dropped
    out_old = AR.collect_evidence(league="NBA", match_id="401777",
                                  home="San Antonio Spurs",
                                  away="Portland Trail Blazers",
                                  kickoff_utc=KICK_TOMORROW)
    assert "https://www.espn.com/nba/story/_/id/102" not in \
        [s["url"] for s in out_old["sources"]
         if s["kind"] == "news_48h"]


def test_roster_fetched_once_per_day(monkeypatch):
    calls: list = []
    monkeypatch.setattr(AR, "_get_json", _stub_get_json(calls))
    for _ in range(2):
        AR.collect_evidence(league="NBA", match_id="401777",
                            home="San Antonio Spurs",
                            away="Portland Trail Blazers",
                            kickoff_utc=KICK_TOMORROW,
                            team_ids={"home": "25", "away": "31"})
    roster_calls = [u for u in calls if u.endswith("/roster")]
    assert sorted(roster_calls) == sorted(set(roster_calls))
    assert len(roster_calls) == 2                  # one per team, not 4


def test_roster_fetch_error_journaled_and_cached(monkeypatch):
    calls: list = []
    monkeypatch.setattr(AR, "_get_json", _stub_get_json(calls))
    out = AR.collect_evidence(league="NBA", match_id="401777",
                              home="Oklahoma City Thunder",
                              away="Golden State Warriors",
                              kickoff_utc=KICK_TOMORROW,
                              team_ids={"home": "16", "away": "77"})
    assert "away" in out.get("roster_errors", {})   # 404 journaled
    assert not any("roster" in s["kind"] for s in out["sources"])
    n_before = len([u for u in calls if u.endswith("/roster")])
    AR.collect_evidence(league="NBA", match_id="401777",
                        home="Oklahoma City Thunder",
                        away="Golden State Warriors",
                        kickoff_utc=KICK_TOMORROW,
                        team_ids={"home": "16", "away": "77"})
    assert len([u for u in calls if u.endswith("/roster")]) == n_before


# --------------------------------- 3) per-team injuries ----------------------

def test_injuries_sources_and_honest_404(monkeypatch):
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
    assert len(inj) == 1                           # only team 16 has items
    assert inj[0]["url"] == f"{core}/16/injuries"
    assert inj[0]["excerpt"] == "Jalen Williams — Out — Knee"
    assert inj[0]["published_utc"] == "2026-10-20T15:30:00Z"
    assert inj[0]["fetched_at_utc"]
    # away team 7 injuries 404: journaled as an ERROR query, 0 invented
    assert "away" in out.get("injuries_errors", {})
    assert "404" in out["injuries_errors"]["away"]
    err_qs = [q for q in out["queries"]
              if "injuries" in q and "ERROR" in q]
    assert any("teams/7" in q for q in err_qs)
    assert len(inj) == 1                           # still no invented away row


def test_injuries_skipped_without_slug_or_team_ids(monkeypatch):
    calls: list = []
    monkeypatch.setattr(AR, "_get_json", _stub_get_json(calls))
    out = AR.collect_evidence(league="SOCCER", match_id="701",
                              home="Arsenal", away="Chelsea",
                              kickoff_utc=KICK_TOMORROW,
                              team_ids={"home": "1", "away": "2"})
    notes = " ".join(out.get("injuries_notes", []))
    assert "no league slug" in notes
    assert not [u for u in calls if "/injuries" in u]
    out2 = AR.collect_evidence(league="NBA", match_id="401777",
                               home="Oklahoma City Thunder",
                               away="Golden State Warriors",
                               kickoff_utc=KICK_TOMORROW, team_ids=None)
    notes2 = " ".join(out2.get("injuries_notes", []))
    assert "no team_id" in notes2
    assert not [u for u in calls if "/injuries" in u]


# --------------------------------- 4) evidence stats (SIMULATED comparison) -

def _news_source_count(out: dict) -> int:
    return len([s for s in out["sources"] if s["kind"] == "news_48h"])


def test_evidence_stats_before_after_simulated(monkeypatch):
    """SIMULATED: same stubbed world, three candidates. OLD collector
    behavior = team-name-only filter (team_ids=None). NEW = roster names
    active. The star-player injury headline (id/102) is dropped before,
    kept after. Coverage is scoped to NEWS sources — the ONLY layer the
    filter changes (scoreboard gives every candidate a source either way).
    """
    monkeypatch.setattr(AR, "_get_json", _stub_get_json([]))
    old_by_c, new_by_c = {}, {}
    for i, (home, away, tids) in enumerate(CANDIDATES):
        old = AR.collect_evidence(league="NBA", match_id=f"m{i}",
                                  home=home, away=away,
                                  kickoff_utc=KICK_TOMORROW, team_ids=None)
        new = AR.collect_evidence(league="NBA", match_id=f"m{i}",
                                  home=home, away=away,
                                  kickoff_utc=KICK_TOMORROW, team_ids=tids)
        old_by_c[f"m{i}"] = ([{"url": s["url"]} for s in old["sources"]
                              if s["kind"] == "news_48h"])
        new_by_c[f"m{i}"] = ([{"url": s["url"]} for s in new["sources"]
                              if s["kind"] == "news_48h"])
        assert _news_source_count(old) <= _news_source_count(new)
    st_old = AR.collect_evidence_stats(old_by_c)
    st_new = AR.collect_evidence_stats(new_by_c)
    assert st_old["candidates"] == 3 == st_new["candidates"]
    assert st_old["candidates_with_sources"] == 1      # team-name only
    assert st_new["candidates_with_sources"] == 2      # + roster name
    assert st_old["share_with_sources"] == pytest.approx(1 / 3)
    assert st_new["share_with_sources"] == pytest.approx(2 / 3)
    # the star-player injury headline is kept by BOTH candidates whose
    # rosters name the player (c1 home roster 16 carries Jalen Williams
    # too — realistic: the injured star plays for c1's home team)
    assert st_new["total_sources"] == st_old["total_sources"] + 2
    assert st_old["candidates_without_sources"] == 2
    # degenerate input is honest
    assert AR.collect_evidence_stats({})["share_with_sources"] == 0.0
