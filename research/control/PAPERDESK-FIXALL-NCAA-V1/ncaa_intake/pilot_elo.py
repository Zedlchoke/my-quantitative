# -*- coding: utf-8 -*-
"""Pilot: walk-forward Elo on sportsdataverse (ESPN) schedules.
Men + women. Train history = seasons 2016-2024, evaluation = 2025 regular season,
predictions strictly pre-game (walk-forward inside the eval season too).
Elo spec frozen for the pilot: K=20, home advantage +65 Elo (0 if neutral),
between-season regression 25% toward 1500, new teams enter at 1500.
Baselines: constant home-win-rate probability estimated from TRAIN seasons only.
"""
import json
import numpy as np
import pandas as pd
from sportsdataverse.mbb import load_mbb_schedule
from sportsdataverse.wbb import load_wbb_schedule

TRAIN_SEASONS = list(range(2016, 2025))
EVAL_SEASON = 2025
K, HFA, REGRESS = 20.0, 65.0, 0.25

def prep(df):
    df = df[df["status_type_completed"] == True].copy()
    df = df.dropna(subset=["home_score", "away_score"])
    df = df[df["home_score"] != df["away_score"]]
    # D1-vs-D1 proxy: both teams carry a conference id in ESPN data
    df = df[df["home_conference_id"].notna() & df["away_conference_id"].notna()]
    df["date"] = pd.to_datetime(df["game_date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df[["date", "season", "season_type", "home_id", "away_id",
               "home_score", "away_score", "neutral_site"]]

def run_elo(games, eval_season):
    elo = {}
    preds = []          # (date, p_home, y_home, season_type)
    train_home_wins, train_games = 0, 0
    cur_season = None
    for g in games.itertuples(index=False):
        if cur_season is not None and g.season != cur_season:
            for t in elo:
                elo[t] = 1500.0 + (elo[t] - 1500.0) * (1 - REGRESS)
        cur_season = g.season
        eh = elo.get(g.home_id, 1500.0)
        ea = elo.get(g.away_id, 1500.0)
        adj = 0.0 if g.neutral_site else HFA
        p = 1.0 / (1.0 + 10 ** (-(eh - ea + adj) / 400.0))
        y = 1 if g.home_score > g.away_score else 0
        if g.season == eval_season:
            preds.append((g.date, p, y, g.season_type))
        else:
            train_home_wins += y; train_games += 1
        e_home = y  # expected score for home = y (1 win / 0 loss)
        elo[g.home_id] = eh + K * (e_home - p)
        elo[g.away_id] = ea + K * ((1 - y) - (1 - p))
    base_rate = train_home_wins / max(train_games, 1)
    return pd.DataFrame(preds, columns=["date", "p", "y", "season_type"]), base_rate

def metrics(p, y):
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    y = np.asarray(y, float)
    return {
        "n": int(len(y)),
        "logloss": float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))),
        "brier": float(np.mean((p - y) ** 2)),
        "accuracy": float(np.mean((p > 0.5) == (y == 1))),
    }

out = {}
for name, loader in (("men", load_mbb_schedule), ("women", load_wbb_schedule)):
    frames = []
    for s in TRAIN_SEASONS + [EVAL_SEASON]:
        try:
            frames.append(loader(seasons=[s], return_as_pandas=True))
        except Exception as e:
            print(f"{name} season {s} FAILED: {type(e).__name__} {str(e)[:80]}")
    raw = pd.concat(frames, ignore_index=True)
    games = prep(raw)
    games.to_csv(f"games_{name}.csv", index=False)
    pr, base = run_elo(games, EVAL_SEASON)
    reg = pr[pr["season_type"] == 2]                     # regular season only
    jan = reg[reg["date"] >= f"{EVAL_SEASON}-01-01"]
    res = {
        "games_loaded_total": int(len(games)),
        "eval_regular_season": metrics(reg["p"], reg["y"]),
        "eval_regular_season_from_jan1": metrics(jan["p"], jan["y"]),
        "baseline_const_home_rate": metrics(np.full(len(reg), base), reg["y"]),
        "train_home_win_rate": float(base),
        "eval_home_win_rate": float(reg["y"].mean()),
    }
    out[name] = res
    print(name, json.dumps(res, indent=1))

json.dump(out, open("pilot_results.json", "w"), indent=1)
print("saved pilot_results.json")
