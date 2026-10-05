#!/usr/bin/env python
"""D_VERIFY own-code NBA re-join: schedule universe vs player_box per season,
box-less FINAL games reproduction, dup check, tip-semantics check, outcome-column scan.
INDEPENDENT implementation from the plan/spec text."""
import os, json
import pandas as pd

HOME = os.path.expanduser("~")
SEASONS = list(range(2016, 2027))
SCHED = f"{HOME}/.my-quantitative-data/nba-hoopr-v1/raw/nba_schedule_{{y}}.csv"

def box_path(y):
    # 2016/2021/2026 come from predecessor store; others from this cycle
    if y in (2016, 2021, 2026):
        return f"{HOME}/.my-quantitative-data/playerdata-prep-v1/nba/player_box_raw/player_box_{y}.csv"
    return f"{HOME}/.my-quantitative-data/playerfeat-prep-v1/nba/player_box_raw/player_box_{y}.csv"

res = {"per_season": {}, "boxless_final_games": [], "dups_total": 0, "null_athlete_rows": {}}
tot_sched = 0; tot_played = 0; tot_join_games = 0
for y in SEASONS:
    s = pd.read_csv(SCHED.format(y=y), low_memory=False)
    b = pd.read_csv(box_path(y), low_memory=False)
    played = s[(s["status_type_name"] == "STATUS_FINAL") & s["home_score"].notna() & s["away_score"].notna()]
    played_ids = set(played["game_id"].astype(int))
    box_ids = set(b["game_id"].astype(int))
    join_rate = len(played_ids & box_ids) / len(played_ids) if len(played_ids) else None
    missing = sorted(played_ids - box_ids)
    orphan = sorted(box_ids - played_ids)
    dups = int(b.duplicated(subset=["game_id", "athlete_id"]).sum())
    null_ath = int(b["athlete_id"].isna().sum())
    # tip semantics: game_date_time == start_date after UTC normalization
    tip = pd.to_datetime(s["game_date_time"], utc=True, format="mixed")
    start = pd.to_datetime(s["start_date"], utc=True, format="mixed")
    tip_mismatch = int((tip != start).sum())
    # season label check: ending-year convention (game dates within the season window)
    dmin, dmax = str(s["game_date"].min()), str(s["game_date"].max())
    res["per_season"][str(y)] = {
        "schedule_rows": int(len(s)), "played_games": int(len(played)),
        "box_game_ids": int(len(box_ids)), "join_rate": join_rate,
        "played_missing_box": missing, "orphan_box_games": orphan,
        "dups_game_athlete": dups, "null_athlete_rows": null_ath,
        "tip_vs_start_mismatch": tip_mismatch,
        "game_date_min": dmin, "game_date_max": dmax,
    }
    if missing:
        # confirm each is FINAL with scores (box-less yet played)
        for gid in missing:
            row = played[played["game_id"].astype(int) == gid]
            res["boxless_final_games"].append({
                "game_id": int(gid), "season": y,
                "status": row["status_type_name"].iloc[0],
                "home_score": float(row["home_score"].iloc[0]), "away_score": float(row["away_score"].iloc[0]),
                "season_type": int(row["season_type"].iloc[0]),
            })
    tot_sched += len(s); tot_played += len(played); tot_join_games += len(played_ids & box_ids)
    res["dups_total"] += dups
    if null_ath: res["null_athlete_rows"][str(y)] = null_ath

res["totals"] = {"schedule_rows": tot_sched, "played_games": tot_played, "joined_played_games": tot_join_games}

# ---- outcome-column scan on the feature table ----
FT = f"{HOME}/.my-quantitative-data/playerfeat-prep-v1/nba/features/nba_player_features_2016_2026.parquet"
t = pd.read_parquet(FT)
res["table"] = {"rows": int(len(t)), "columns": list(t.columns)}
BAD_TOKENS = ["score", "winner", "win", "loss", "margin", "outcome", "result", "pts_",
              "points", "total_", "home_score", "away_score", "spread", "odds", "prob"]
schema_hits = [c for c in t.columns for tok in BAD_TOKENS if tok in c.lower()]
res["table"]["schema_name_hits"] = schema_hits
# content scan: any float column that looks like a raw score (integer values > 80 outside known scalars)
content_scan = {}
for c in t.columns:
    if t[c].dtype.kind in "fi" and c not in ("season", "season_type", "team_id", "opponent_id",
                                             "team_games_so_far", "n_prior_games_used", "b_form_top3_n"):
        v = pd.to_numeric(t[c], errors="coerce").dropna()
        if len(v):
            content_scan[c] = {"min": float(v.min()), "max": float(v.max()), "mean": float(v.mean())}
res["table"]["numeric_column_ranges"] = content_scan
res["table"]["dups_game_team"] = int(t.duplicated(subset=["game_id", "team_id"]).sum())
res["table"]["neutral_rows"] = int(t["feature_neutral"].sum())
res["table"]["per_season_rows"] = {str(k): int(v) for k, v in t.groupby("season").size().items()}

OUT = "/Users/hoangminhlong/my-quantitative/.worktrees/winprob-playerfeat-prep-v1/integration/lanes/D_VERIFY/nba_join_output.json"
json.dump(res, open(OUT, "w"), indent=1, default=str)
for y in SEASONS:
    r = res["per_season"][str(y)]
    print(y, "sched", r["schedule_rows"], "played", r["played_games"], "join", round(r["join_rate"], 6),
          "missing", r["played_missing_box"], "orphan", r["orphan_box_games"], "dups", r["dups_game_athlete"],
          "tip_mismatch", r["tip_vs_start_mismatch"])
print("boxless:", res["boxless_final_games"])
print("table:", res["table"]["rows"], "rows,", len(res["table"]["columns"]), "cols, schema_hits:", schema_hits)
print("ranges:", json.dumps(content_scan, indent=1))
print("dups(game,team):", res["table"]["dups_game_team"], "neutral:", res["table"]["neutral_rows"])
print("per_season_rows:", res["table"]["per_season_rows"])
