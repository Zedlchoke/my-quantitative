#!/usr/bin/env python
"""Lane D INDEPENDENT WNBA coverage recompute (own code, not measure_b.py).
Universe law (from GAME_UNIVERSE_SPEC §4 as restated in lane B COVERAGE_SCHEMA §1):
  ESPN schedules 2002-2026: keep status_type_state=='post'; drop rows whose
  status_type_name mentions Forfeit/Postponed; drop All-Star alias rows
  (home or away abbreviation in the alias set). Join player_box/game_rosters on game_id."""
import os, glob, json
import pandas as pd

ESPN = os.path.expanduser("~/.my-quantitative-data/wnba-v1/raw/espn_schedules")
CORPUS = os.path.expanduser("~/.my-quantitative-data/wnba-prep-v1/roster_audit")
ALIAS = {"EAST","WEST","ALL","USA","DEL","PAR","WIL","STE","CLA","COL","SPO","COOP","WNBASTARS"}

uni_rows = []
for p in sorted(glob.glob(os.path.join(ESPN, "wnba_schedule_20*.csv"))):
    y = int(os.path.basename(p)[14:18])
    s = pd.read_csv(p, low_memory=False)
    post = s[s["status_type_state"] == "post"]
    n0 = len(post)
    dropped_forfeit = post[post["status_type_name"].str.contains("Forfeit", case=False, na=False)]
    dropped_postponed = post[post["status_type_name"].str.contains("Postponed", case=False, na=False)]
    post2 = post[~post["status_type_name"].str.contains("Forfeit|Postponed", case=False, na=False)]
    alias_mask = post2["home_abbreviation"].isin(ALIAS) | post2["away_abbreviation"].isin(ALIAS)
    n_alias = int(alias_mask.sum())
    uni = post2[~alias_mask]
    uni_rows.append({"season": y, "raw_rows": len(s), "post": n0,
                     "dropped_forfeit": dropped_forfeit["game_id"].tolist(),
                     "dropped_postponed": dropped_postponed["game_id"].tolist(),
                     "dropped_alias": n_alias, "universe": len(uni),
                     "game_ids": set(uni["game_id"].astype(int))})

tot = sum(r["universe"] for r in uni_rows)
print("UNIVERSE total 2002-2026:", tot)

pb = pd.concat([pd.read_csv(os.path.join(CORPUS, f"player_box_{y}.csv"), low_memory=False,
                            usecols=["game_id"]) for y in range(2002, 2027)], ignore_index=True)
gr = pd.concat([pd.read_csv(os.path.join(CORPUS, f"game_rosters_{y}.csv"), low_memory=False,
                            usecols=["game_id"]) for y in range(2002, 2027)], ignore_index=True)
pb_games = set(pb["game_id"].astype(int))
gr_games = set(gr["game_id"].astype(int))
print("player_box distinct games:", len(pb_games), " game_rosters distinct games:", len(gr_games))

uni_ids = set().union(*[r["game_ids"] for r in uni_rows])
cov_pb = pb_games & uni_ids
cov_gr = gr_games & uni_ids
print("player_box covered:", len(cov_pb), f"= {len(cov_pb)/len(uni_ids)*100:.2f}% of universe")
print("game_rosters covered:", len(cov_gr), f"= {len(cov_gr)/len(uni_ids)*100:.2f}%")
print("player_box extras (in file not universe):", len(pb_games - uni_ids))
print("rosters extras:", len(gr_games - uni_ids))

season_of = {}
for r in uni_rows:
    for g in r["game_ids"]:
        season_of[g] = r["season"]

SPOT = [2002, 2004, 2013, 2026]
report = {"universe_total": tot, "per_season_universe": {r["season"]: r["universe"] for r in uni_rows},
          "dropped_forfeit": [g for r in uni_rows for g in r["dropped_forfeit"]],
          "dropped_postponed": [g for r in uni_rows for g in r["dropped_postponed"]],
          "total_alias_dropped": sum(r["dropped_alias"] for r in uni_rows),
          "pb_games": len(pb_games), "pb_covered": len(cov_pb),
          "pb_rate": round(len(cov_pb)/len(uni_ids)*100, 2),
          "gr_games": len(gr_games), "gr_covered": len(cov_gr),
          "pb_extras": len(pb_games - uni_ids), "gr_extras": len(gr_games - uni_ids),
          "spot": {}}
for y in SPOT:
    u = uni_rows[y-2002]["game_ids"]
    pb_y = {g for g in pb_games if season_of.get(g) == y} & u
    # season_of only has universe games; player_box games in season y that are in universe:
    pb_y_cov = len({g for g in cov_pb if season_of[g] == y})
    gr_y_cov = len({g for g in cov_gr if season_of[g] == y})
    report["spot"][y] = {"universe": len(u), "pb_covered": pb_y_cov,
                         "pb_rate_pct": round(pb_y_cov/len(u)*100, 1),
                         "gr_covered": gr_y_cov}
    print(f"SEASON {y}: universe={len(u)} player_box_covered={pb_y_cov} ({pb_y_cov/len(u)*100:.1f}%) rosters={gr_y_cov}")

out = os.path.expanduser("~/my-quantitative/.worktrees/winprob-playerdata-prep-v1/integration/lanes/D_VERIFY/verify_coverage_wnba_output.json")
report["per_season_universe"] = {str(k): v for k, v in report["per_season_universe"].items()}
report["spot"] = {str(k): v for k, v in report["spot"].items()}
with open(out, "w") as f:
    json.dump(report, f, indent=1)
print("WROTE", out)
