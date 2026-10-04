"""NFL synthetic fixtures: golden Elo (K/HCA/neutral/tie/reversion), kickoff
no-lookahead mutation, rename continuity, rest/short-week/form, leakage grep."""
import math
import os

from nfl_winprob.elo import run_elo, expected_home
from nfl_winprob.features import compute_features
from nfl_winprob.evaluate import main as evaluate_main


def g(n, kickoff, season, home, away, home_win, tie=False, neutral=False, playoffs=False):
    return {"game_id": f"G{n:04d}", "kickoff_utc": kickoff, "season": season,
            "home_lineage": home, "away_lineage": away, "home_win": home_win,
            "tie": tie, "neutral": neutral, "is_playoffs": playoffs}


def feats(games):
    elo_out, _ = run_elo(games, K=20, HCA=65)
    return compute_features(games, elo_out)


def test_golden_single_game_k20():
    out, final = run_elo([g(1, "2010-09-12T17:00:00+00:00", 2010, "A", "B", True)], K=20, HCA=0)
    r = out[0]
    assert abs(r["p_home"] - 0.5) < 1e-12
    assert abs(r["r_home_post"] - 1510.0) < 1e-9
    assert abs(r["r_away_post"] - 1490.0) < 1e-9


def test_golden_hca65():
    p = expected_home(1500.0, 1500.0, 65.0)
    assert abs(p - 1.0 / (1.0 + 10 ** (-65.0 / 400.0))) < 1e-12
    assert abs(p - 0.5925) < 1e-3  # golden: 10^-(0.1625) = 0.6877; 1/1.6877 = 0.5925


def test_neutral_zero_hca():
    games = [g(1, "2010-09-12T17:00:00+00:00", 2010, "A", "B", True, neutral=True)]
    out, _ = run_elo(games, K=20, HCA=65)
    assert abs(out[0]["p_home"] - 0.5) < 1e-12  # HCA suppressed on neutral site


def test_tie_update_half():
    # unequal ratings, tie -> both move toward each other with S=0.5
    games = [g(1, "2010-09-12T17:00:00+00:00", 2010, "A", "B", False, tie=True)]
    games[0]["home_win"] = False
    out, _ = run_elo(games, K=20, HCA=0)
    # equal ratings tie -> p=0.5, S=0.5 -> no movement at all
    assert abs(out[0]["r_home_post"] - 1500.0) < 1e-9
    # now with a rating gap: A=1510,B=1490 from a prior win, then a tie
    games2 = [g(1, "2010-09-12T17:00:00+00:00", 2010, "A", "B", True),
              g(2, "2010-09-19T17:00:00+00:00", 2010, "A", "B", False, tie=True)]
    out2, _ = run_elo(games2, K=20, HCA=0)
    p2 = out2[1]["p_home"]
    assert abs(out2[1]["r_home_post"] - (1510.0 + 20 * (0.5 - p2))) < 1e-9


def test_season_reversion_two_thirds():
    games = [g(1, "2010-12-12T17:00:00+00:00", 2010, "A", "B", True),
             g(2, "2011-09-11T17:00:00+00:00", 2011, "A", "B", True)]
    out, _ = run_elo(games, K=30, HCA=0)
    a1 = out[0]["r_home_post"]
    assert abs(out[1]["r_home_pre"] - (1500.0 + (2.0 / 3.0) * (a1 - 1500.0))) < 1e-9


def test_kickoff_no_lookahead_mutation():
    games = [
        g(1, "2012-09-09T17:00:00+00:00", 2012, "A", "B", True),
        g(2, "2012-09-09T21:00:00+00:00", 2012, "C", "D", True),   # same day, later KO
        g(3, "2012-09-16T17:00:00+00:00", 2012, "A", "C", True),
        g(4, "2012-09-23T17:00:00+00:00", 2012, "B", "D", True),   # mutation target
        g(5, "2012-09-30T17:00:00+00:00", 2012, "B", "C", False),  # involves B: sees the flip
    ]
    base = feats(games)
    mut = [dict(x) for x in games]
    mut[3]["home_win"] = False
    mut_feats = feats(mut)
    for idx in (0, 1, 2, 3):   # kickoff <= target: byte-identical
        assert base[idx] == mut_feats[idx]
    changed = [k for k in base[4] if base[4][k] != mut_feats[4][k]]
    assert changed  # later game sees the flipped result


def test_rename_continuity_stl_la():
    games = [g(1, "2015-11-01T17:00:00+00:00", 2015, "Rams", "X", True),
             g(2, "2015-11-08T17:00:00+00:00", 2015, "Rams", "Y", True),
             g(3, "2016-09-11T17:00:00+00:00", 2016, "Rams", "Z", True)]
    out, _ = run_elo(games, K=20, HCA=0)
    r2 = out[1]["r_home_post"]
    assert abs(out[2]["r_home_pre"] - (1500.0 + (2.0 / 3.0) * (r2 - 1500.0))) < 1e-9


def test_rest_shortweek_form_bye():
    games = [
        g(1, "2012-09-09T17:00:00+00:00", 2012, "A", "X", True),
        g(2, "2012-09-13T23:00:00+00:00", 2012, "A", "Y", True),   # Sun->Thu short week (4d)
        g(3, "2012-09-30T17:00:00+00:00", 2012, "A", "Z", True),   # after bye (17d rest)
        g(4, "2012-10-07T17:00:00+00:00", 2012, "A", "B", True),
    ]
    f = feats(games)
    assert f[1]["rest_home"] == 4 and f[1]["short_week_home"] == 1
    assert f[2]["rest_home"] == 16          # bye week (floor-days: 16d18h -> 16), uncapped
    assert abs(f[3]["form_home"] - 0.5) < 1e-12   # 3/3 wins -> 1.0 - 0.5
    assert f[3]["rest_away"] == 20          # B never played -> cap


def test_form_regular_season_only_and_current_season():
    games = [
        g(1, "2011-12-25T17:00:00+00:00", 2011, "A", "X", True),
        g(2, "2012-09-09T17:00:00+00:00", 2012, "A", "Y", False),
        g(3, "2012-09-16T17:00:00+00:00", 2012, "A", "Z", True),
        g(4, "2013-01-06T17:00:00+00:00", 2012, "A", "W", True, playoffs=True),
        g(5, "2013-09-08T17:00:00+00:00", 2013, "A", "V", True),
    ]
    f = feats(games)
    # game3: current-season prior = 1 loss -> form -0.5 (2011 game excluded)
    assert abs(f[2]["form_home"] - (-0.5)) < 1e-12
    # game5: prior season games (incl. playoff) do not count for 2013 form
    assert f[4]["form_home"] == 0.0


FORBIDDEN_TOKENS = ("spread_line", "moneyline", "total_line", "over_odds", "under_odds")


def test_static_leakage_grep():
    pkg_dir = os.path.join(os.path.dirname(__file__), "..")
    for fname in ("elo.py", "features.py", "protocol.py", "evaluate.py"):
        with open(os.path.join(pkg_dir, fname), encoding="utf-8") as f:
            src = f.read()
        for tok in FORBIDDEN_TOKENS:
            assert tok not in src, f"{fname} references quarantined odds token {tok}"


def test_evaluate_refuses(capsys):
    assert evaluate_main([]) == 3
