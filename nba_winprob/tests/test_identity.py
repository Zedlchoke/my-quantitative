"""Franchise-continuity + leakage static tests (PROTOCOL_EVAL.md sec8.1/8.3)."""
import os

from nba_winprob.elo import run_elo


def g(gameorder, date, season, home, away, home_win):
    return {"src_game_id": f"G{gameorder:04d}", "gameorder": gameorder, "date": date,
            "season": season, "home_lineage": home, "away_lineage": away,
            "home_win": home_win, "is_playoffs": False}


def test_rename_continuity_via_lineage_key():
    """SEA->OKC within one lineage 'Thunder': the rating stream survives the
    team_id change (lineage key), with only the season reversion applied."""
    games = [
        g(1, "2008-04-01", 2008, "Thunder", "Spurs", True),   # SEA era
        g(2, "2008-04-03", 2008, "Thunder", "Lakers", True),
        g(3, "2009-01-01", 2009, "Thunder", "Jazz", True),    # OKC era, same lineage
    ]
    out, final = run_elo(games, K=32, HCA=0)
    r2 = out[1]["r_home_post"]
    r3 = out[2]["r_home_pre"]
    assert abs(r3 - (1500.0 + 0.75 * (r2 - 1500.0))) < 1e-9   # carried + reverted once
    assert "Thunder" in final


def test_two_lineages_independent():
    games = [
        g(1, "2008-01-01", 2008, "Hornets", "Pelicans", True),
        g(2, "2008-01-03", 2008, "Hornets", "Pelicans", True),
    ]
    out, _ = run_elo(games, K=32, HCA=0)
    # naming traps documented by lane B: 'Hornets' = Bobcats lineage,
    # 'Pelicans' = original CHH/NOH lineage — distinct rating streams.
    assert out[1]["r_home_pre"] > 1500.0
    assert out[1]["r_away_pre"] < 1500.0


FORBIDDEN_TOKENS = ("forecast", "elo_i", "opp_elo", "win_equiv")


def test_static_leakage_grep():
    """C sec8.1 static test: model-side sources must not reference the
    quarantined 538 columns (they live only in build_dataset's f538 side table)."""
    pkg_dir = os.path.join(os.path.dirname(__file__), "..")
    for fname in ("elo.py", "features.py", "protocol.py", "evaluate.py"):
        path = os.path.join(pkg_dir, fname)
        with open(path, encoding="utf-8") as f:
            src = f.read()
        for tok in FORBIDDEN_TOKENS:
            assert tok not in src, f"{fname} references quarantined token {tok}"
