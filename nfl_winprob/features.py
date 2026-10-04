"""PIT features under the NFL kickoff-grain as-of law (PROTOCOL_EVAL_NFL.md).

f1 elo_diff = R_home − R_away (HCA not added; intercept carries home effect)
f2 rest_diff = rest_days(home) − rest_days(away); rest_days = min(20, days
   since team's most recent completed game with kickoff strictly before);
   none -> 20 (cap; byes 13-14d stay uncapped)
f3/f4 short_week_{home,away} = 1{rest_days <= 6}
f5/f6 form_{home,away} = ((wins + 0.5*ties)/games − 0.5) over last <=4 completed
REGULAR-season games of the current season strictly before kickoff; none -> 0
(REMEDIATION 2026-10-04: ties now count half a win per PROTOCOL_EVAL_NFL §2
f5 — the old code credited 0).
"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict

from .protocol import FORM_WINDOW, REST_CAP, SHORT_WEEK_DAYS


def _ts(s):
    if isinstance(s, dt.datetime):
        return s
    return dt.datetime.fromisoformat(s)


def compute_features(games, elo_results):
    games = sorted(games, key=lambda g: (g["kickoff_utc"], g["game_id"]))
    elo_pre = {r["game_id"]: r for r in elo_results}
    history: dict[str, list] = defaultdict(list)  # (kickoff_ts, season, is_playoffs, win, tie)
    out = []
    for g in games:
        row = elo_pre[g["game_id"]]
        ko = _ts(g["kickoff_utc"])

        def rest_days(lineage: str) -> int:
            h = history.get(lineage) or []
            k = len(h) - 1
            while k >= 0:
                if h[k][0] < ko:
                    return min(REST_CAP, (ko - h[k][0]).days)
                k -= 1
            return REST_CAP

        def form(lineage: str, season) -> float:
            h = history.get(lineage) or []
            credit = games_n = 0.0
            k = len(h) - 1
            while k >= 0 and games_n < FORM_WINDOW:
                t, s, po, win, tie = h[k]
                if s < season:
                    break
                if t < ko and s == season and not po:
                    credit += 1.0 if win else (0.5 if tie else 0.0)
                    games_n += 1
                k -= 1
            return (credit / games_n - 0.5) if games_n else 0.0

        rh, ra = row["r_home_pre"], row["r_away_pre"]
        rest_h, rest_a = rest_days(g["home_lineage"]), rest_days(g["away_lineage"])
        out.append({
            "game_id": g["game_id"], "kickoff_utc": g["kickoff_utc"],
            "season": g["season"], "is_playoffs": g.get("is_playoffs", False),
            "home_lineage": g["home_lineage"], "away_lineage": g["away_lineage"],
            "elo_diff": rh - ra,
            "rest_home": rest_h, "rest_away": rest_a, "rest_diff": rest_h - rest_a,
            "short_week_home": 1 if rest_h <= SHORT_WEEK_DAYS else 0,
            "short_week_away": 1 if rest_a <= SHORT_WEEK_DAYS else 0,
            "form_home": form(g["home_lineage"], g["season"]),
            "form_away": form(g["away_lineage"], g["season"]),
        })
        history[g["home_lineage"]].append((ko, g["season"], bool(g.get("is_playoffs", False)), bool(g["home_win"]), bool(g.get("tie", False))))
        history[g["away_lineage"]].append((ko, g["season"], bool(g.get("is_playoffs", False)), (not bool(g["home_win"])), bool(g.get("tie", False))))
    return out


FEATURE_COLUMNS = ["elo_diff", "rest_diff", "short_week_home", "short_week_away", "form_home", "form_away"]
