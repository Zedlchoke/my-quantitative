"""Own-Elo engine under the NFL kickoff-grain as-of law (PROTOCOL_EVAL_NFL.md).

Law: predictions for game G use rating state as of all games with kickoff
strictly before kickoff(G) (global sort by kickoff; per-team lookups are
therefore strictly-before). Season reversion R <- 1500 + gamma*(R-1500)
before a lineage's first game of a new season. Neutral-site games: HCA = 0
in prediction AND update. Ties: excluded from scoring (build flags them) but
INCLUDED in the rating stream with S = 0.5 per protocol.
"""
from __future__ import annotations

from collections import defaultdict

from .protocol import ELO_GAMMA, ELO_INIT


def expected_home(r_home: float, r_away: float, hca: float) -> float:
    return 1.0 / (1.0 + 10 ** (-(r_home + hca - r_away) / 400.0))


def run_elo(games, K: float, HCA: float, gamma: float = ELO_GAMMA, init: float = ELO_INIT):
    """games: dicts with kickoff_utc, season, home_lineage, away_lineage,
    home_win, tie, neutral. Returns (per-game rows sorted by kickoff, finals).

    As-of law (PROTOCOL_EVAL_NFL §2): all updates with kickoff strictly before
    kickoff(G) are applied before predicting G; games with IDENTICAL kickoff
    timestamps never inform each other — predictions for a whole identical-
    kickoff batch are computed from the frozen prior state, then updates apply.
    """
    games = sorted(games, key=lambda g: (g["kickoff_utc"], g["game_id"]))
    R: dict[str, float] = defaultdict(lambda: init)
    seen_season: dict[str, int] = {}
    out = []
    i, n = 0, len(games)
    while i < n:
        ko = games[i]["kickoff_utc"]
        j = i
        preds = []
        while j < n and games[j]["kickoff_utc"] == ko:
            g = games[j]
            for lin in (g["home_lineage"], g["away_lineage"]):
                last = seen_season.get(lin)
                if last is None or last < g["season"]:
                    if last is not None:
                        R[lin] = 1500.0 + gamma * (R[lin] - 1500.0)
                    seen_season[lin] = g["season"]
            hca = 0.0 if (g.get("neutral") and HCA) else HCA
            rh, ra = R[g["home_lineage"]], R[g["away_lineage"]]
            preds.append((g, rh, ra, expected_home(rh, ra, hca)))
            j += 1
        for g, rh, ra, p in preds:
            s = 0.5 if g.get("tie") else (1.0 if g["home_win"] else 0.0)
            R[g["home_lineage"]] = rh + K * (s - p)
            R[g["away_lineage"]] = ra + K * ((1.0 - s) - (1.0 - p))
            out.append({
                "game_id": g.get("game_id"), "kickoff_utc": g["kickoff_utc"],
                "season": g["season"], "p_home": p,
                "r_home_pre": rh, "r_away_pre": ra,
                "r_home_post": R[g["home_lineage"]], "r_away_post": R[g["away_lineage"]],
            })
        i = j
    return out, dict(R)
