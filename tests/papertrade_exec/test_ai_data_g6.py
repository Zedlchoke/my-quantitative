"""G6 structured context: exact quote copy and strictly past ESPN results."""
from datetime import datetime, timezone

from research.papertrade_exec import ai_research as R


def test_g6_market_and_team_blocks_use_verified_fields(monkeypatch):
    quote = {"row_sha256": "row", "fetch_ts_utc": "2026-10-22T13:50:00Z",
             "odds": {"HOME": 2.2, "AWAY": 1.7},
             "pm_walk": {"legs": {
                 "HOME": {"best_ask": .44, "vwap_ask": .455,
                          "depth_ok": True, "fee_cents": 13},
                 "AWAY": {"best_ask": .57, "vwap_ask": .588,
                          "depth_ok": True, "fee_cents": 13}}}}
    summary = {"predictor": {"homeTeam": {"id": "30",
                                            "gameProjection": "50.4"},
                             "awayTeam": {"id": "1",
                                          "gameProjection": "49.6"}},
               "pickcenter": [{"details": "CHA -1.5", "spread": 1.5,
                               "overUnder": 230.5,
                               "homeTeamOdds": {"moneyLine": -110},
                               "awayTeamOdds": {"moneyLine": 100}}]}
    standings = {"children": [{"name": "Eastern Conference",
        "standings": {"entries": [
            {"team": {"id": tid}, "stats": [
                {"name": "wins", "value": 1},
                {"name": "losses", "value": 0},
                {"name": "playoffSeed", "value": 2}]}
            for tid in ("30", "1")]}}]}
    def schedule(tid):
        return {"events": [
            {"id": "prior", "date": "2026-10-22T23:00Z",
             "competitions": [{"status": {"type": {"completed": True}},
                               "competitors": [
                {"homeAway": "home", "team": {"id": tid},
                 "score": {"value": 110}},
                {"homeAway": "away", "team": {"id": "99"},
                 "score": {"value": 100}}]}]},
            {"id": "future", "date": "2026-10-23T23:00Z",
             "competitions": [{"status": {"type": {"completed": False}},
                               "competitors": []}]}]}
    def get(url, *_a, **_k):
        if "/summary?" in url: return summary
        if "/standings?" in url: return standings
        if "/teams/30/schedule" in url: return schedule("30")
        if "/teams/1/schedule" in url: return schedule("1")
        raise AssertionError(url)
    monkeypatch.setattr(R, "_get_json", get)
    out = {"league": "NBA", "queries": []}
    R._nba_context(out, "401909843", "2026-10-23T23:00:00Z", "30", "1",
                   quote, datetime(2026, 10, 23, 2, tzinfo=timezone.utc))
    assert out["market_block"]["pm_legs"]["HOME"]["decimal_odds"] == 2.2
    assert out["market_block"]["pm_legs"]["AWAY"]["vwap_ask"] == .588
    assert out["market_block"]["espn"]["predictor_home_pct"] == 50.4
    assert out["market_block"]["espn"]["home_moneyline"] == -110
    assert len(out["context_fetches"]) == 4
    for side in ("HOME", "AWAY"):
        b = out["team_block"][side]
        assert b["standings"]["wins"] == 1
        assert [g["event_id"] for g in b["last_five"]] == ["prior"]
        assert b["rest_days"] == 0 and b["back_to_back"] is True
