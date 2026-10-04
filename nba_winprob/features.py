"""PIT features under the v1 date-grain as-of law (PROTOCOL_EVAL.md sec2 B2).

f1 elo_diff   = R_home − R_away (as-of; HCA deliberately NOT added)
f2 rest_diff  = rest_days(home) − rest_days(away)
f3 b2b_home   = 1{rest_days(home) ≤ 1}
f4 b2b_away   = 1{rest_days(away) ≤ 1}
f5 form_home  = (win_rate − 0.5) over last ≤10 completed REGULAR-SEASON games
               of the current season strictly before date(G); none → 0
f6 form_away  analogous

rest_days(team, G) = min(10, G.date − date of team's most recent completed
game strictly before date(G)); no prior completed game → 10 (cap).

All lookups are strictly-before-date; same-day games never inform each other
(doubleheaders lose leg-1 information by law — conservative, documented).
"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict

from .protocol import FORM_WINDOW, REST_CAP


def _d(s):
    return s if isinstance(s, dt.date) else dt.date.fromisoformat(s)


def compute_features(games, elo_results):
    """games sorted/unsorted dicts (same keys as run_elo input); elo_results
    keyed by (gameorder) or aligned via index — we match by src_game_id when
    present, else by (date, gameorder). Returns list of feature dicts aligned
    with the SORTED game order, one per game.
    """
    games = sorted(games, key=lambda g: (g["date"], g["gameorder"]))
    elo_pre = {}
    for row in elo_results:
        key = row.get("src_game_id") or (row["date"], row["gameorder"])
        elo_pre[key] = row

    # per-lineage completed-game logs, appended ONLY after each date batch
    history: dict[str, list] = defaultdict(list)  # (date, season, is_playoffs, win)
    out = []
    i, n = 0, len(games)
    while i < n:
        d = games[i]["date"]
        batch = []
        j = i
        while j < n and games[j]["date"] == d:
            batch.append(games[j])
            j += 1
        for g in batch:
            key = g.get("src_game_id") or (g["date"], g["gameorder"])
            row = elo_pre[key]

            def rest_days(lineage: str) -> int:
                h = history.get(lineage) or []
                k = len(h) - 1
                while k >= 0:
                    pd = h[k][0]
                    if pd < _d(d):
                        return min(REST_CAP, (_d(d) - pd).days)
                    k -= 1
                return REST_CAP

            def form(lineage: str, season) -> float:
                h = history.get(lineage) or []
                wins = games_n = 0
                taken = 0
                k = len(h) - 1
                while k >= 0 and taken < FORM_WINDOW:
                    pd, ps, popo, pwin = h[k]
                    if ps < season:
                        break
                    if pd < _d(d) and ps == season and not popo:
                        wins += 1 if pwin else 0
                        games_n += 1
                        taken += 1
                    k -= 1
                return (wins / games_n - 0.5) if games_n else 0.0

            rh, ra = row["r_home_pre"], row["r_away_pre"]
            rest_h, rest_a = rest_days(g["home_lineage"]), rest_days(g["away_lineage"])
            out.append({
                "src_game_id": g.get("src_game_id"),
                "gameorder": g["gameorder"], "date": g["date"],
                "season": g["season"], "is_playoffs": g.get("is_playoffs", False),
                "home_lineage": g["home_lineage"], "away_lineage": g["away_lineage"],
                "elo_diff": rh - ra,
                "rest_home": rest_h, "rest_away": rest_a,
                "rest_diff": rest_h - rest_a,
                "b2b_home": 1 if rest_h <= 1 else 0,
                "b2b_away": 1 if rest_a <= 1 else 0,
                "form_home": form(g["home_lineage"], g["season"]),
                "form_away": form(g["away_lineage"], g["season"]),
            })
        # apply the whole date batch to history AFTER predictions/features
        for g in batch:
            history[g["home_lineage"]].append(
                (_d(g["date"]), g["season"], bool(g.get("is_playoffs", False)), bool(g["home_win"])))
            history[g["away_lineage"]].append(
                (_d(g["date"]), g["season"], bool(g.get("is_playoffs", False)), not bool(g["home_win"])))
        i = j
    return out


FEATURE_COLUMNS = ["elo_diff", "rest_diff", "b2b_home", "b2b_away", "form_home", "form_away"]
