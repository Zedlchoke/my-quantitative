"""REAL-CSV path tests (AMENDMENT_1 A4): schema/row-count/end-to-end load of
the frozen derived files — NO metric on real outcomes is computed here."""
import os

import pytest

DATA = os.path.expanduser("~/.my-quantitative-data/nba-538-v1/derived")
GAMES = os.path.join(DATA, "games.csv")
FEATURES = os.path.join(DATA, "features.csv")

pytestmark = pytest.mark.skipif(
    not (os.path.exists(GAMES) and os.path.exists(FEATURES)),
    reason="derived NBA files not present on this machine")


def test_real_features_header_has_plain_elo_diff():
    import csv as _csv
    with open(FEATURES, newline="", encoding="utf-8") as f:
        header = next(_csv.reader(f))
    assert "elo_diff" in header                      # D1 regression guard
    for arm in ("B1-a", "B1-b", "B1-c", "B1-d"):
        assert f"elo_diff_{arm}" in header and f"p_home_{arm}" in header
    assert "home_win" not in header and "pts" not in header


def test_real_csv_load_rows_end_to_end():
    from nba_winprob.run_evaluation import load_rows
    rows = load_rows(GAMES, FEATURES)                # would KeyError before D1 fix
    assert len(rows) == 63157
    r0 = rows[0]
    assert {"elo_diff", "rest_diff", "b2b_home", "b2b_away", "form_home", "form_away"} <= set(r0["features"])
    assert all(0.0 < r0["p_b1"][a] < 1.0 for a in r0["p_b1"])


def test_real_row_counts_per_split():
    from nba_winprob.run_evaluation import load_rows
    seasons = {}
    for r in load_rows(GAMES, FEATURES):
        seasons.setdefault(r["season"], [0, 0])
        seasons[r["season"]][0 if not r["is_playoffs"] else 1] += 1
    rs = sum(v[0] for v in seasons.values())
    po = sum(v[1] for v in seasons.values())
    assert rs + po == 63157
    test_rs = sum(seasons[s][0] for s in range(2009, 2016))
    test_po = sum(seasons[s][1] for s in range(2009, 2016))
    assert test_rs == 8369 and test_po == 587          # lane-B frozen split
