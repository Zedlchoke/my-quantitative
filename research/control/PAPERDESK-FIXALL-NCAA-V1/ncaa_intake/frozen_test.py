# -*- coding: utf-8 -*-
"""FROZEN TEST — NCAA basketball (men + women), prediction-quality program.
Implements ~/workspace/sports_ml/ncaa/REPORT.md spec exactly:

- Walk-forward, point-in-time features only. Ratings update after each game.
- Frozen Elo: K=20, HFA +65 (0 if neutral), 25% between-season regression to 1500,
  new teams at 1500; logistic map p = 1/(1+10^(-(diff+adj)/400)). (Pilot-identical.)
- Adjusted efficiency rebuilt game-by-game from final scores (points space,
  opponent+location adjusted; PBP per-possession wiring NOT available in the
  schedule feed — documented deviation, see FROZEN_TEST_RESULTS.md):
  L = expanding league mean pts/team-game (init 70.0); H_PTS = 3.2 if not neutral;
  pred_h = L + O_h + D_a + H; pred_a = L + O_a + D_h; step A = 0.06;
  O/D deviations regress 25% toward 0 at season change (same trigger as Elo).
- Naive baseline per eval season Y: constant home-win-rate over ALL games in
  seasons < Y (pilot rule).
- GBM challenger: sklearn HistGradientBoostingClassifier, all defaults,
  random_state=0; trained on regular-season games of seasons < Y only;
  features frozen (differentials + context), computed pre-game.
- Eval seasons: 2024, 2025, 2026 (three most recent completed at run time).
- Regular season (season_type==2) is the evaluation engine.
Outputs: predictions_all.csv, metrics.json
"""
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

EVAL_SEASONS = [2024, 2025, 2026]
HISTORY_START = 2016
K, HFA, REGRESS = 20.0, 65.0, 0.25
L0, H_PTS, A_EFF = 70.0, 3.2, 0.06
FEATURES = ["elo_diff", "eff_margin", "net_diff", "rest_h", "rest_a",
            "rest_diff", "conf_game", "neutral"]


def load_games(name):
    """Pilot games (2016-2025, pilot row order) + 2026 rows, enriched with
    conference ids / tournament_id / names from the full rebuilt table."""
    core = pd.read_csv(f"games_{name}.csv", parse_dates=["date"])
    full = pd.read_csv(f"games_{name}_full.csv", parse_dates=["date"])
    extra_cols = ["home_conference_id", "away_conference_id", "tournament_id",
                  "home_display_name", "away_display_name"]
    keys = ["date", "home_id", "away_id", "home_score", "away_score"]
    full_x = full[keys + extra_cols].drop_duplicates(subset=keys)
    core = core.merge(full_x, on=keys, how="left", validate="one_to_one")
    add26 = full[full["season"] == 2026][
        ["date", "season", "season_type", "home_id", "away_id", "home_score",
         "away_score", "neutral_site"] + extra_cols]
    out = pd.concat([core, add26], ignore_index=True)
    out = out.sort_values("date", kind="mergesort").reset_index(drop=True)
    return out


def walk_forward(games):
    """Single chronological pass. Returns per-game pre-game records."""
    elo, off, deff, last_date = {}, {}, {}, {}
    tot_pts, tot_tg = 0, 0
    recs = []
    cur_season = None
    for g in games.itertuples(index=False):
        if cur_season is not None and g.season != cur_season:
            for t in elo:
                elo[t] = 1500.0 + (elo[t] - 1500.0) * (1 - REGRESS)
            for t in off:
                off[t] *= (1 - REGRESS)
                deff[t] *= (1 - REGRESS)
        cur_season = g.season
        eh = elo.get(g.home_id, 1500.0)
        ea = elo.get(g.away_id, 1500.0)
        oh, dh = off.get(g.home_id, 0.0), deff.get(g.home_id, 0.0)
        oa, da = off.get(g.away_id, 0.0), deff.get(g.away_id, 0.0)
        L = (tot_pts / tot_tg) if tot_tg else L0
        neutral = bool(g.neutral_site)
        adj = 0.0 if neutral else HFA
        p_elo = 1.0 / (1.0 + 10 ** (-(eh - ea + adj) / 400.0))
        hpts = 0.0 if neutral else H_PTS
        pred_h = L + oh + da + hpts
        pred_a = L + oa + dh
        d = g.date
        rest_h = 10.0 if g.home_id not in last_date else min((d - last_date[g.home_id]).days, 30)
        rest_a = 10.0 if g.away_id not in last_date else min((d - last_date[g.away_id]).days, 30)
        y = 1 if g.home_score > g.away_score else 0
        recs.append({
            "date": d, "season": g.season, "season_type": g.season_type,
            "tournament_id": g.tournament_id, "home_id": g.home_id, "away_id": g.away_id,
            "home_name": g.home_display_name, "away_name": g.away_display_name,
            "y": y, "p_elo": p_elo,
            "elo_diff": (eh + adj) - ea,
            "eff_margin": pred_h - pred_a,
            "net_diff": (oh - dh) - (oa - da),
            "rest_h": float(rest_h), "rest_a": float(rest_a),
            "rest_diff": float(rest_h) - float(rest_a),
            "conf_game": 1.0 if g.home_conference_id == g.away_conference_id else 0.0,
            "neutral": 1.0 if neutral else 0.0,
        })
        # ---- updates (post-game) ----
        elo[g.home_id] = eh + K * (y - p_elo)
        elo[g.away_id] = ea + K * ((1 - y) - (1 - p_elo))
        err_h = g.home_score - pred_h
        err_a = g.away_score - pred_a
        off[g.home_id] = oh + A_EFF * err_h
        deff[g.away_id] = da + A_EFF * err_h
        off[g.away_id] = oa + A_EFF * err_a
        deff[g.home_id] = dh + A_EFF * err_a
        last_date[g.home_id] = d
        last_date[g.away_id] = d
        tot_pts += g.home_score + g.away_score
        tot_tg += 2
    return pd.DataFrame(recs)


def metrics(p, y):
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    y = np.asarray(y, float)
    return {"n": int(len(y)),
            "logloss": float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))),
            "brier": float(np.mean((p - y) ** 2)),
            "accuracy": float(np.mean((p > 0.5) == (y == 1)))}


def run_gender(name):
    games = load_games(name)
    rec = walk_forward(games)
    rec.to_csv(f"predictions_{name}.csv", index=False)
    reg = rec[rec["season_type"] == 2]
    out = {"eval": {}, "pooled": {}}
    pooled_rows = {"elo": [], "gbm": [], "naive": []}
    for Y in EVAL_SEASONS:
        train = reg[reg["season"] < Y]
        ev = reg[reg["season"] == Y].copy()
        gbm = HistGradientBoostingClassifier(random_state=0)
        gbm.fit(train[FEATURES].to_numpy(), train["y"].to_numpy())
        ev["p_gbm"] = gbm.predict_proba(ev[FEATURES].to_numpy())[:, 1]
        ev.to_csv(f"evalrows_{name}_{Y}.csv", index=False)
        naive_rate = float(rec[rec["season"] < Y]["y"].mean())  # all game types, pilot rule
        res = {
            "elo": metrics(ev["p_elo"], ev["y"]),
            "gbm": metrics(ev["p_gbm"], ev["y"]),
            "naive": metrics(np.full(len(ev), naive_rate), ev["y"]),
            "naive_rate": naive_rate,
            "home_win_rate": float(ev["y"].mean()),
        }
        out["eval"][Y] = res
        for m in pooled_rows:
            pooled_rows[m].append(ev[["y"]].assign(
                p=ev["p_elo"] if m == "elo" else ev["p_gbm"] if m == "gbm" else naive_rate))
        print(name, Y, json.dumps(res))
    pooled = {m: metrics(pd.concat(v)["p"], pd.concat(v)["y"]) for m, v in pooled_rows.items()}
    out["pooled"] = pooled
    # kill criteria
    elo_ll = np.mean([out["eval"][Y]["elo"]["logloss"] for Y in EVAL_SEASONS])
    gbm_ll = np.mean([out["eval"][Y]["gbm"]["logloss"] for Y in EVAL_SEASONS])
    gbm_losses = sum(1 for Y in EVAL_SEASONS
                     if out["eval"][Y]["gbm"]["logloss"] >= out["eval"][Y]["elo"]["logloss"])
    best = min(pooled["elo"]["logloss"], pooled["gbm"]["logloss"])
    out["kill"] = {
        "gbm_avg_ll_gain_vs_elo": float(elo_ll - gbm_ll),
        "gbm_seasons_lost": int(gbm_losses),
        "ml_layer_alive": bool((elo_ll - gbm_ll) >= 0.005 and gbm_losses < 2),
        "best_pooled_ll": float(best),
        "naive_pooled_ll": pooled["naive"]["logloss"],
        "program_margin_vs_naive": float(pooled["naive"]["logloss"] - best),
        "program_alive": bool((pooled["naive"]["logloss"] - best) >= 0.03),
    }
    print(name, "KILL:", json.dumps(out["kill"]))
    return out


if __name__ == "__main__":
    results = {name: run_gender(name) for name in ("men", "women")}
    json.dump(results, open("frozen_metrics.json", "w"), indent=1)
    print("saved frozen_metrics.json")
