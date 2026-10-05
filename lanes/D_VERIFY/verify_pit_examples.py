#!/usr/bin/env python
"""Lane D INDEPENDENT recompute of the three PIT worked examples (NBA MIL, WNBA CON, NFL KC)."""
import os, json
import pandas as pd

out = {}

# ---------- NBA: game 401307387 MIL@WSH tip 2021-03-15T23:00Z, prior-5 MIL minutes-mass ----------
SCHED = os.path.expanduser("~/.my-quantitative-data/nba-hoopr-v1/raw")
BOX = os.path.expanduser("~/.my-quantitative-data/playerdata-prep-v1/nba/player_box_raw")
s21 = pd.read_csv(os.path.join(SCHED, "nba_schedule_2021.csv"), low_memory=False)
b21 = pd.read_csv(os.path.join(BOX, "player_box_2021.csv"), low_memory=False,
                  usecols=["game_id","athlete_id","team_id","team_name","minutes"])
tgt = s21[s21["game_id"] == 401307387].iloc[0]
tip_t = pd.to_datetime(tgt["game_date_time"], utc=True, format="mixed")
mil_ids = {15}  # MIL team_id measured from target-game box rows (team_abbreviation MIL)
s21["tip"] = pd.to_datetime(s21["game_date_time"], utc=True, format="mixed")
mil_games = s21[s21["home_id"].isin(mil_ids) | s21["away_id"].isin(mil_ids)]
prior = mil_games[mil_games["tip"] < tip_t].sort_values("tip").tail(5)
pg = []
for _, row in prior.iterrows():
    gid = row["game_id"]
    mins = b21[(b21["game_id"] == gid) & (b21["team_id"].isin(mil_ids))]["minutes"].dropna()
    pg.append((gid, str(row["tip"]), float(mins.sum())))
mean5 = sum(x[2] for x in pg) / len(pg) if pg else None
out["nba_mil"] = {
    "target_game": 401307387, "tip_utc": str(tip_t),
    "mil_team_ids": sorted(int(t) for t in mil_ids),
    "prior5": [{"game_id": int(g), "tip_utc": t, "mil_minutes_total": m} for g, t, m in pg],
    "strict_inequality_ok": all(pd.Timestamp(t) < tip_t for _, t, _ in pg),
    "target_absent_from_prior": 401307387 not in [g for g, _, _ in pg],
    "minutes_mass_mean": round(mean5, 4) if mean5 is not None else None,
    "claimed": {"tips": "02-28,03-03,03-05,03-12,03-14", "per_game": [240.0,240.0,240.0,238.0,239.0], "mean": 239.4},
}
print("NBA:", json.dumps(out["nba_mil"], indent=1))

# ---------- WNBA: CON team_id 18, 2013 target 400445816 tip 2013-07-06T23:00Z ----------
ESPN = os.path.expanduser("~/.my-quantitative-data/wnba-v1/raw/espn_schedules")
CORPUS = os.path.expanduser("~/.my-quantitative-data/wnba-prep-v1/roster_audit")
s = pd.read_csv(os.path.join(ESPN, "wnba_schedule_2013.csv"), low_memory=False)
s["tip"] = pd.to_datetime(s["date"], utc=True, format="ISO8601")
tgt2 = s[s["game_id"] == 400445816].iloc[0]
tip2 = tgt2["tip"]
b13 = pd.read_csv(os.path.join(CORPUS, "player_box_2013.csv"), low_memory=False,
                  usecols=["game_id","team_id","athlete_id","minutes"])
prior2 = s[(s["tip"] < tip2) & ((s["home_id"] == 18) | (s["away_id"] == 18))].sort_values("tip").tail(5)
pg2 = []
for _, row in prior2.iterrows():
    gid = row["game_id"]
    mins = b13[(b13["game_id"] == gid) & (b13["team_id"] == 18)]["minutes"].dropna()
    pg2.append({"game_id": int(gid), "tip_utc": str(row["tip"]), "con_minutes_total": float(mins.sum()),
                "players_with_minutes": int((mins > 0).sum())})
out["wnba_con"] = {
    "target_game": 400445816, "tip_utc": str(tip2),
    "prior5": pg2,
    "strict_inequality_ok": all(pd.Timestamp(p["tip_utc"]) < tip2 for p in pg2),
    "target_absent_from_prior": 400445816 not in [p["game_id"] for p in pg2],
    "claimed": {"ids": [400445826,400445854,400445709,400445771,400445798],
                "tips": "06-14T23:30Z,06-16T21:00Z,06-23T19:00Z,06-29T23:00Z,07-02T23:00Z",
                "minutes": [200.0,201.0,200.0,199.0,202.0]},
}
print("WNBA:", json.dumps(out["wnba_con"], indent=1))

# ---------- NFL: 2024_11_KC_BUF kickoff 2024-11-17T21:25Z, Mahomes prior-3 ----------
GAMES = os.path.expanduser("~/.my-quantitative-data/nfl-nflverse-v1/raw/games.csv")
SP = os.path.expanduser("~/.my-quantitative-data/playerdata-prep-v1/nfl/raw_stats_player")
g = pd.read_csv(GAMES, low_memory=False)
g["ko_et"] = pd.to_datetime(g["gameday"]) + pd.to_timedelta(g["gametime"] + ":00")
g["ko_utc"] = g["ko_et"].dt.tz_localize("America/New_York", nonexistent="shift_forward", ambiguous="NaT").dt.tz_convert("UTC")
tgt3 = g[g["game_id"] == "2024_11_KC_BUF"].iloc[0]
ko_t = tgt3["ko_utc"]
kc = g[((g["home_team"] == "KC") | (g["away_team"] == "KC")) & (g["season"] == 2024)]
prior3 = kc[kc["ko_utc"] < ko_t].sort_values("ko_utc").tail(3)
sp = pd.read_parquet(os.path.join(SP, "stats_player_week_2024.parquet"))
mah = sp[sp["player_id"] == "00-0033873"]
rows = []
for _, row in prior3.iterrows():
    gid = row["game_id"]
    m = mah[mah["game_id"] == gid]
    rows.append({"game_id": gid, "kickoff_utc": str(row["ko_utc"]), "week": int(row["week"]),
                 "passing_yards": None if m.empty else int(m["passing_yards"].iloc[0]),
                 "passing_tds": None if m.empty else int(m["passing_tds"].iloc[0]),
                 "passing_interceptions": None if m.empty else int(m["passing_interceptions"].iloc[0]),
                 "attempts": None if m.empty else int(m["attempts"].iloc[0])})
tot = {k: sum(r[k] or 0 for r in rows) for k in ("passing_yards","passing_tds","passing_interceptions","attempts")}
out["nfl_kc"] = {
    "target_game": "2024_11_KC_BUF", "kickoff_utc": str(ko_t),
    "prior3": rows, "totals": tot,
    "strict_inequality_ok": all(pd.Timestamp(r["kickoff_utc"]) < ko_t for r in rows),
    "target_absent_from_prior": "2024_11_KC_BUF" not in [r["game_id"] for r in rows],
    "claimed": {"ids": ["2024_08_KC_LV","2024_09_TB_KC","2024_10_DEN_KC"],
                "kos": ["2024-10-27T20:25Z","2024-11-05T01:15Z","2024-11-10T18:00Z"],
                "totals": {"passing_yards": 819, "passing_tds": 6, "passing_interceptions": 1, "attempts": 124}},
}
print("NFL:", json.dumps(out["nfl_kc"], indent=1))

with open(os.path.expanduser("~/my-quantitative/.worktrees/winprob-playerdata-prep-v1/integration/lanes/D_VERIFY/verify_pit_examples_output.json"), "w") as f:
    json.dump(out, f, indent=1)
