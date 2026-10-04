"""Own-Elo engine under the v1 as-of law (PROTOCOL_EVAL.md sec2 B1).

Law (controller reconciliation of lane C sec0/sec2 vs lane B schema sec6 —
the STRICTER reading wins): predictions for every game on date d use rating
state as of the close of date d-1; ALL updates for date d are applied only
after every prediction for date d (date-batched; same-day games never inform
each other). File/state ordering is (date, gameorder) for determinism.

- One rating stream per franchise lineage; relocations carry the rating.
- Every lineage starts at ELO_INIT at its first completed game.
- Season-boundary rule, applied lazily before a lineage's first prediction of
  a new season: R <- 1500 + GAMMA * (R - 1500).
- Update on EVERY completed game (regular + playoff), binary result, no MOV.

538 elo columns are never read here (cross-check table is quarantined in
build_dataset as f538_reference.csv).
"""
from __future__ import annotations

import math
from collections import defaultdict

from .protocol import ELO_GAMMA, ELO_INIT


def expected_home(r_home: float, r_away: float, hca: float) -> float:
    return 1.0 / (1.0 + 10 ** (-(r_home + hca - r_away) / 400.0))


def run_elo(games, K: float, HCA: float, gamma: float = ELO_GAMMA, init: float = ELO_INIT):
    """games: iterable of dicts with keys date, gameorder, season,
    home_lineage, away_lineage, home_win (bool). Sorted or unsorted; we sort.

    Returns list aligned with sorted games of dicts:
      {src keys..., p_home, r_home_pre, r_away_pre, r_home_post, r_away_post}
    plus final ratings dict.
    """
    games = sorted(games, key=lambda g: (g["date"], g["gameorder"]))
    R: dict[str, float] = defaultdict(lambda: init)
    seen_season: dict[str, int] = {}
    out = []
    i = 0
    n = len(games)
    while i < n:
        d = games[i]["date"]
        j = i
        # --- prediction phase for date d (state frozen at close of d-1) ---
        preds = []
        while j < n and games[j]["date"] == d:
            g = games[j]
            for lin in (g["home_lineage"], g["away_lineage"]):
                last = seen_season.get(lin)
                if last is None or last < g["season"]:
                    if last is not None:
                        R[lin] = 1500.0 + gamma * (R[lin] - 1500.0)
                    seen_season[lin] = g["season"]
            rh, ra = R[g["home_lineage"]], R[g["away_lineage"]]
            p = expected_home(rh, ra, HCA)
            preds.append((g, rh, ra, p))
            j += 1
        # --- update phase for date d ---
        for g, rh, ra, p in preds:
            s = 1.0 if g["home_win"] else 0.0
            R[g["home_lineage"]] = rh + K * (s - p)
            R[g["away_lineage"]] = ra + K * ((1.0 - s) - (1.0 - p))
            out.append({
                "src_game_id": g.get("src_game_id"),
                "gameorder": g["gameorder"], "date": g["date"],
                "season": g["season"], "is_playoffs": g.get("is_playoffs", False),
                "p_home": p,
                "r_home_pre": rh, "r_away_pre": ra,
                "r_home_post": R[g["home_lineage"]], "r_away_post": R[g["away_lineage"]],
            })
        i = j
    return out, dict(R)


def log10_elo_expected(r_diff: float) -> float:
    """Elo expected score for a raw rating difference (no HCA). Test helper."""
    return 1.0 / (1.0 + 10 ** (-(r_diff) / 400.0))
