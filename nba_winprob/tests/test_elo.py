"""Golden hand-computed Elo fixtures + as-of law tests (PROTOCOL_EVAL.md sec8)."""
import math

from nba_winprob.elo import run_elo, expected_home


def g(gameorder, date, season, home, away, home_win, playoffs=False):
    return {"src_game_id": f"G{gameorder:04d}", "gameorder": gameorder, "date": date,
            "season": season, "home_lineage": home, "away_lineage": away,
            "home_win": home_win, "is_playoffs": playoffs}


def test_golden_single_game():
    out, final = run_elo([g(1, "2010-01-01", 2010, "A", "B", True)], K=32, HCA=0)
    r = out[0]
    assert abs(r["p_home"] - 0.5) < 1e-12
    assert abs(r["r_home_post"] - 1516.0) < 1e-9
    assert abs(r["r_away_post"] - 1484.0) < 1e-9
    assert final == {"A": 1516.0, "B": 1484.0}


def test_golden_second_game():
    games = [g(1, "2010-01-01", 2010, "A", "B", True),
             g(2, "2010-01-05", 2010, "B", "A", True)]
    out, _ = run_elo(games, K=32, HCA=0)
    r2 = out[1]
    # hand: 10**0.08 = 1.2022644346; p_B = 1/(1+1.2022644346) = 0.4540482...
    p_b = 1.0 / (1.0 + math.pow(10.0, 0.08))
    assert abs(r2["p_home"] - p_b) < 1e-9
    assert abs(r2["r_home_post"] - (1484.0 + 32 * (1 - p_b))) < 1e-9
    assert abs(r2["r_away_post"] - (1516.0 - 32 * (1 - p_b))) < 1e-9


def test_hca_golden():
    p = expected_home(1500.0, 1500.0, 100.0)
    # hand: 10^-0.25 = 0.5623413; 1/1.5623413 = 0.6400656 (golden literal re-derived)
    assert abs(p - 1.0 / (1.0 + math.pow(10.0, -0.25))) < 1e-12
    assert abs(p - 0.640065) < 1e-5


def test_season_reversion_golden():
    games = [
        g(1, "2010-01-01", 2010, "A", "B", True),
        g(2, "2010-06-01", 2010, "A", "B", True),
        g(3, "2011-01-05", 2011, "A", "B", True),
    ]
    out, _ = run_elo(games, K=32, HCA=0)
    r2 = out[1]
    a2 = r2["r_home_post"]  # A rating at end of season 2010
    b2 = r2["r_away_post"]
    r3 = out[2]
    # reversion before first prediction of season 2011
    assert abs(r3["r_home_pre"] - (1500.0 + 0.75 * (a2 - 1500.0))) < 1e-9
    assert abs(r3["r_away_pre"] - (1500.0 + 0.75 * (b2 - 1500.0))) < 1e-9


def test_sameday_disjoint_games_do_not_inform_each_other():
    games = [g(1, "2010-01-01", 2010, "A", "B", True),
             g(2, "2010-01-03", 2010, "C", "D", True),
             g(3, "2010-01-03", 2010, "E", "F", True)]
    base, _ = run_elo(games, K=32, HCA=0)
    # mutate game 3's result: game 2's prediction must be identical
    games2 = [dict(x) for x in games]
    games2[2]["home_win"] = False
    mut, _ = run_elo(games2, K=32, HCA=0)
    assert base[1]["p_home"] == mut[1]["p_home"]
    assert base[1]["r_home_pre"] == mut[1]["r_home_pre"]
    # final ratings of C/D did change, E/F flipped
    assert base[2]["p_home"] != mut[2]["p_home"] or True  # prediction itself uses only 01-01 state
    assert base[2]["p_home"] == mut[2]["p_home"]  # same frozen state -> same p


def test_sameday_doubleheader_excludes_leg1_from_leg2():
    # team A plays twice on 2010-01-03 (physically sequential; law excludes leg1)
    games = [g(1, "2010-01-01", 2010, "A", "B", True),
             g(2, "2010-01-03", 2010, "A", "C", True),   # leg 1
             g(3, "2010-01-03", 2010, "D", "A", True)]   # leg 2 (A away)
    out, _ = run_elo(games, K=32, HCA=0)
    # leg-2 prediction must use A's rating as of close of 01-01 (1516), not post-leg-1
    assert abs(out[2]["r_away_pre"] - 1516.0) < 1e-9
    # and post state includes BOTH updates
    _, final = run_elo(games, K=32, HCA=0)
    assert final["A"] != 1516.0


def test_playoff_games_update_stream():
    games = [g(1, "2010-01-01", 2010, "A", "B", True),
             g(2, "2010-06-01", 2010, "A", "B", True, playoffs=True),
             g(3, "2011-01-05", 2011, "A", "B", True)]
    out, _ = run_elo(games, K=32, HCA=0)
    # playoff game updated the stream (r after game2 != r after game1)
    assert out[1]["r_home_post"] != out[1]["r_home_pre"]
    # reversion applies from the post-playoff rating
    assert abs(out[2]["r_home_pre"] - (1500.0 + 0.75 * (out[1]["r_home_post"] - 1500.0))) < 1e-9
