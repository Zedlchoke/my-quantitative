#!/usr/bin/env python
"""Lane D INDEPENDENT NFL coverage recompute."""
import os, json
import pandas as pd

SP = os.path.expanduser("~/.my-quantitative-data/playerdata-prep-v1/nfl/raw_stats_player")
SC = os.path.expanduser("~/.my-quantitative-data/playerdata-prep-v1/nfl/raw_snap_counts")
GAMES = os.path.expanduser("~/.my-quantitative-data/nfl-nflverse-v1/raw/games.csv")
report = {}

games = pd.read_csv(GAMES, low_memory=False)
game_ids = set(games["game_id"].astype(str))

for y in (2024, 2025, 2026):
    df = pd.read_parquet(os.path.join(SP, f"stats_player_week_{y}.parquet"))
    ids = set(df["game_id"].astype(str))
    dups = int(df.duplicated(["player_id","game_id"]).sum())
    join = ids & game_ids
    # placeholder rows: all-zero stat rows with NaN player
    stat_cols = [c for c in df.columns if c not in ("player_id","player_name","player_display_name","position","position_group","headshot_url","season","week","season_type","game_id","team","opponent_team")]
    num = df[stat_cols].select_dtypes("number")
    ph = df[(df["player_id"].isna()) & (num.fillna(0).abs().sum(axis=1) == 0)]
    weeks = sorted(df["week"].unique().tolist())
    r = {
        "season": y, "rows": len(df), "cols": df.shape[1],
        "distinct_games": len(ids), "joined": len(join), "orphans": len(ids - game_ids),
        "weeks": weeks, "dup_player_game": dups,
        "placeholder_rows_nanplayer_allzero": len(ph),
        "season_types": df["season_type"].value_counts().to_dict(),
    }
    report[f"week_{y}"] = r
    print(json.dumps(r, indent=1))

rp = pd.read_parquet(os.path.join(SP, "stats_player_regpost_2025.parquet"))
report["regpost_2025"] = {"rows": len(rp), "cols": rp.shape[1],
                          "season_types": rp["season_type"].value_counts().to_dict() if "season_type" in rp else None}
print("regpost_2025:", report["regpost_2025"])

sc = pd.read_parquet(os.path.join(SC, "snap_counts_2025.parquet"))
ids = set(sc["game_id"].astype(str))
report["snap_2025"] = {"rows": len(sc), "cols": sc.shape[1], "distinct_games": len(ids),
                       "joined": len(ids & game_ids), "dup_pfr_game": int(sc.duplicated(["pfr_player_id","game_id"]).sum()) if "pfr_player_id" in sc else None}
print("snap_2025:", report["snap_2025"])
sc6 = pd.read_parquet(os.path.join(SC, "snap_counts_2026.parquet"))
ids6 = set(sc6["game_id"].astype(str))
report["snap_2026"] = {"rows": len(sc6), "cols": sc6.shape[1], "distinct_games": len(ids6), "joined": len(ids6 & game_ids)}
print("snap_2026:", report["snap_2026"])

# schema drift check across the 3 weekly files
cols = []
for y in (2024, 2025, 2026):
    cols.append(list(pd.read_parquet(os.path.join(SP, f"stats_player_week_{y}.parquet")).columns))
report["schema_drift_none"] = cols[0] == cols[1] == cols[2]
print("schema identical across 2024/2025/2026:", report["schema_drift_none"])

# 2026 prospective-window claim: all 63 game_ids kicked off before download moment 2026-10-05T07:18Z
g26 = games[games["game_id"].isin(set(pd.read_parquet(os.path.join(SP, f"stats_player_week_2026.parquet"))["game_id"].astype(str)))]
report["games2026_gameday_range"] = [str(g26["gameday"].min()), str(g26["gameday"].max())]
print("2026 in-stats gameday range:", report["games2026_gameday_range"])
future = games[(~games["game_id"].isin(set(g26["game_id"]))) & (games["season"] == 2026)]
report["future_2026_games"] = len(future)
print("2026 games without stats (future):", len(future))

with open(os.path.expanduser("~/my-quantitative/.worktrees/winprob-playerdata-prep-v1/integration/lanes/D_VERIFY/verify_coverage_nfl_output.json"), "w") as f:
    json.dump(report, f, indent=1)
