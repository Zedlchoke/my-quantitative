"""G2 verified competition routing and G4 retry of failed boards."""
from research.papertrade_exec import ai_research as R


def test_g2_verified_soccer_paths_and_unknown_journal(tmp_path, monkeypatch):
    expected = {"soccer_uefa_nations_league": "soccer/uefa.nations",
                "soccer_fifa_world_cup_group": "soccer/fifa.world",
                "soccer_uefa_euro_group": "soccer/uefa.euro",
                "soccer_fifa_world_cup_qualifiers": "soccer/fifa.worldq.uefa",
                "soccer_uefa_euro_qualifiers": "soccer/uefa.euroq"}
    assert R.SOCCER_PATH_BY_COMPETITION == expected
    monkeypatch.setattr(R, "_get_json", lambda *_a, **_k:
                        (_ for _ in ()).throw(AssertionError("network")))
    out = R.collect_evidence(league="SOCCER", competition="unknown",
                             match_id="M1", home="A", away="B",
                             journal_dir=tmp_path)
    assert "no verified ESPN path for competition unknown" in out["why"]
    assert out["sources"] == []
    assert list(tmp_path.glob("evidence_M1_*.json"))


def test_g4_failed_board_expires_and_retry_is_journaled(monkeypatch):
    R._BOARD_CACHE.clear()
    now = [0.0]
    calls = []
    monkeypatch.setattr(R.time, "monotonic", lambda: now[0])
    def transport(url):
        calls.append(url)
        if len(calls) == 1:
            raise OSError("transient")
        return {"events": [{"id": "ok"}]}
    monkeypatch.setattr(R, "_get_json", transport)
    q = []
    assert R._board_payload("basketball/nba", "20261023", q) is None
    now[0] = 119
    assert R._board_payload("basketball/nba", "20261023", q) is None
    assert len(calls) == 1
    now[0] = 120
    good = R._board_payload("basketball/nba", "20261023", q)
    assert good["events"][0]["id"] == "ok" and len(calls) == 2
    now[0] = 500
    assert R._board_payload("basketball/nba", "20261023", q) == good
    assert len(calls) == 2
    assert any("first ERROR" in x for x in q)
    assert any("failed cached" in x for x in q)
    assert any("retry OK" in x for x in q)
    R._BOARD_CACHE.clear()
