#!/usr/bin/env python
"""D_VERIFY T3c — G2 usage recompute for KC row 2024_11_KC_BUF (PIT_AUDIT §2 numbers)."""
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import pandas as pd

DATA = os.path.expanduser("~/.my-quantitative-data")
ET = ZoneInfo("America/New_York")
games = pd.read_csv(f"{DATA}/nfl-ng-prep-v1/raw_schedules_r1_20261005/games.csv")
gmeta = {r["game_id"]: r for r in games[games["season"] == 2024].to_dict("records")}
gk = {gid: datetime.strptime(f"{r['gameday']} {r['gametime']}", "%Y-%m-%d %H:%M")
      .replace(tzinfo=ET).astimezone(timezone.utc) for gid, r in gmeta.items()}
stats = pd.read_parquet(f"{DATA}/playerdata-prep-v1/nfl/raw_stats_player/stats_player_week_2024.parquet")
stats = stats[stats["player_id"].notna()]
stat_gids = set(stats["game_id"])

gid = "2024_11_KC_BUF"
tko = gk[gid]
kc_priors = sorted({(gk[g], g) for g in stat_gids
                    if gmeta[g]["away_team"] == "KC" or gmeta[g]["home_team"] == "KC"}
                   & {(k, g) for k, g in gk.items() if False} | set()) if False else \
    sorted({(gk[g], g) for g in stat_gids
            if (gmeta[g]["away_team"] == "KC" or gmeta[g]["home_team"] == "KC") and gk[g] < tko})
priors = [g for _, g in kc_priors]
w3 = set(priors[-3:])
sk = stats[(stats["season"] == 2024) & (stats["team"] == "KC")
           & stats["position_group"].isin(["WR", "RB", "TE"])]
r3 = sk[sk["game_id"].isin(w3)]
usage = (r3["targets"].fillna(0) + r3["carries"].fillna(0)).groupby(r3["player_id"]).sum()
tot = float(usage.sum())
ranked = usage.sort_values(ascending=False)
top3 = ranked.head(3)
shares = (usage / tot).sort_values(ascending=False)
print(f"U_tot(k3) = {tot} (claim 189)")
for pid, u in top3.items():
    nm = r3.loc[r3["player_id"] == pid, "player_display_name"].iloc[0]
    print(f"  top: {pid} {nm} usage={u}")
print(f"top3 sum = {top3.sum()} -> share = {top3.sum()/tot:.5f} (claim 131/189 = 0.69312)")
print(f"hhi = {(shares**2).sum():.5f} (claim 0.22208)")
print(f"usage_pg_k3 = {tot/3} (claim 63.0)")
w5 = set(priors[-5:])
r5 = sk[sk["game_id"].isin(w5)]
usage5 = (r5["targets"].fillna(0) + r5["carries"].fillna(0)).groupby(r5["player_id"]).sum()
tot5 = float(usage5.sum())
shares5 = usage5 / tot5
print(f"top5_share_k5 = {shares5.sort_values(ascending=False).head(5).sum():.5f} (claim 0.79299)")
tab = pd.read_parquet(f"{DATA}/nfl-playerfeat-prep-v1/features/nfl_playerfeat_table_v1.parquet")
tr = tab[(tab["game_id"] == gid) & (tab["side"] == "away")].iloc[0]
print(f"\ntable: top3={tr['skill_top3_share_k3']:.5f} hhi={tr['skill_hhi_k3']:.5f} "
      f"usage_pg={tr['skill_usage_pg_k3']} top5_k5={tr['skill_top5_share_k5']:.5f}")
