"""Feature PIT tests: rest/B2B/form + no-lookahead mutation + same-day law."""
from nba_winprob.elo import run_elo
from nba_winprob.features import compute_features


def g(gameorder, date, season, home, away, home_win, playoffs=False):
    return {"src_game_id": f"G{gameorder:04d}", "gameorder": gameorder, "date": date,
            "season": season, "home_lineage": home, "away_lineage": away,
            "home_win": home_win, "is_playoffs": playoffs}


def feats(games):
    elo_out, _ = run_elo(games, K=32, HCA=0)
    return compute_features(games, elo_out)


def test_rest_b2b_form_golden():
    games = [
        g(1, "2012-01-01", 2012, "A", "X", True),    # A W (RS)
        g(2, "2012-01-02", 2012, "A", "Y", True),    # A W on a back-to-back
        g(3, "2012-01-04", 2012, "A", "Z", True, playoffs=True),  # playoff: rest sees it, form does not
        g(4, "2012-01-06", 2012, "A", "B", True),    # A home, rested
    ]
    f = feats(games)
    f4 = f[3]
    assert f4["rest_home"] == 2            # 01-06 minus playoff game 01-04
    assert f4["b2b_home"] == 0
    assert abs(f4["form_home"] - 0.5) < 1e-12  # 2 RS wins in season -> 1.0 - 0.5
    # away team B has no history: rest cap 10, form 0
    assert f4["rest_away"] == 10
    assert f4["form_away"] == 0.0
    # the 01-02 game itself was a B2B for A
    f2 = f[1]
    assert f2["rest_home"] == 1
    assert f2["b2b_home"] == 1


def test_form_current_season_only_and_cap():
    games = [
        g(1, "2011-05-01", 2011, "A", "X", True),
        g(2, "2012-01-01", 2012, "A", "Y", False),   # prior-season W must not count
        g(3, "2012-01-03", 2012, "A", "Z", True),
    ]
    f = feats(games)
    # A's 2012 form before 01-03: one RS loss -> 0.0 - 0.5 = -0.5
    assert abs(f[2]["form_home"] - (-0.5)) < 1e-12


def test_no_lookahead_mutation_property():
    """Flip a result on date d: features of all games with date <= d must be
    byte-identical (strictly-before law + same-day exclusion); only later
    games may change."""
    games = [
        g(1, "2012-01-01", 2012, "A", "B", True),
        g(2, "2012-01-01", 2012, "C", "D", False),
        g(3, "2012-01-02", 2012, "A", "C", True),
        g(4, "2012-01-05", 2012, "B", "D", False),
        g(5, "2012-01-05", 2012, "A", "B", True),   # mutation target (same date as g4)
        g(6, "2012-01-07", 2012, "C", "A", False),
    ]
    base = feats(games)
    mut_games = [dict(x) for x in games]
    mut_games[4]["home_win"] = False            # flip g5 on 01-05
    mut = feats(mut_games)
    for idx in (0, 1, 2):                       # dates 01-01, 01-02
        assert base[idx] == mut[idx]
    for idx in (3, 4):                          # same-date 01-05 rows (incl. target row itself:
        # the target's own features are computed from strictly-earlier state)
        assert base[idx] == mut[idx]
    # later game may legitimately change (A's form/elo shifted by the flip)
    changed = [k for k in base[5] if base[5][k] != mut[5][k]]
    assert changed  # expected: elo_diff/form of the 01-07 game


def test_sameday_games_never_inform_each_other_features():
    games = [
        g(1, "2012-01-01", 2012, "A", "B", True),
        g(2, "2012-01-03", 2012, "C", "D", True),
        g(3, "2012-01-03", 2012, "E", "F", False),
    ]
    base = feats(games)
    mut_games = [dict(x) for x in games]
    mut_games[2]["home_win"] = True
    mut = feats(mut_games)
    assert base[1] == mut[1]   # C-D features exclude E-F (same date)
