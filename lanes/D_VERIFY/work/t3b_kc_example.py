#!/usr/bin/env python
"""D_VERIFY T3b — standalone KC-side recompute of the 2024_11_KC_BUF worked example."""
import json, os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import pandas as pd

DATA = os.path.expanduser("~/.my-quantitative-data")
WORK = "/Users/hoangminhlong/my-quantitative/.worktrees/nfl-playerfeat-prep-v1/integration/lanes/D_VERIFY/work"
ET = ZoneInfo("America/New_York")

games = pd.read_csv(f"{DATA}/nfl-ng-prep-v1/raw_schedules_r1_20261005/games.csv")
gmeta = {r["game_id"]: r for r in
         games[games["season"].isin([2024, 2025, 2026])].to_dict("records")}
gk = {}
for gid, r in gmeta.items():
    gk[gid] = datetime.strptime(f"{r['gameday']} {r['gametime']}", "%Y-%m-%d %H:%M") \
        .replace(tzinfo=ET).astimezone(timezone.utc)

stats = pd.concat(
    [pd.read_parquet(f"{DATA}/playerdata-prep-v1/nfl/raw_stats_player/stats_player_week_{y}.parquet")
     for y in (2024, 2025, 2026)], ignore_index=True)
stats = stats[stats["player_id"].notna()]
stat_gids = set(stats["game_id"])

# KC 2024 corpus games + QB rows
kc_games = sorted([(gk[g], g) for g in stat_gids
                   if g.startswith("2024")
                   and (gmeta[g]["away_team"] == "KC" or gmeta[g]["home_team"] == "KC")])
qb = stats[(stats["season"] == 2024) & (stats["team"] == "KC") & (stats["position"] == "QB")]

gid = "2024_11_KC_BUF"
tko = gk[gid]
priors = [(ko, g) for ko, g in kc_games if ko < tko]
n_prior = len(priors)
print("KC 2024 corpus priors of", gid, "target kickoff", tko.isoformat())
for ko, g in priors:
    print(f"  prior {g}  {ko.isoformat()}")
print(f"n_prior_games_used = {n_prior} (claim 9; wk6 bye skipped)")

last = priors[-1]
rest = (tko - last[0]).total_seconds() / 86400.0
print(f"last prior {last[1]} rest_days={rest:.5f} (claim 7.1424)")

def agg(gids):
    yds = td = i = att = epa = 0.0
    for r in qb.to_dict("records"):
        if r["game_id"] not in gids:
            continue
        yds += float(r["passing_yards"]) if pd.notna(r["passing_yards"]) else 0.0
        td += float(r["passing_tds"]) if pd.notna(r["passing_tds"]) else 0.0
        i += float(r["passing_interceptions"]) if pd.notna(r["passing_interceptions"]) else 0.0
        att += float(r["attempts"]) if pd.notna(r["attempts"]) else 0.0
        epa += float(r["passing_epa"]) if pd.notna(r["passing_epa"]) else 0.0
    return yds, td, i, att, epa

all_pg = {g for _, g in priors}
sy, _, _, _, se = agg(all_pg)
std_yds, std_epa = sy / n_prior, se / n_prior
w3 = {g for _, g in priors[-3:]}
y3, td3, i3, a3, e3 = agg(w3)
print(f"\nprior-3 window {sorted(w3)}")
print(f"qb_yds_k3={y3} (claim 819)  qb_td_k3={td3} (6)  qb_int_k3={i3} (1)  qb_att_k3={a3} (124)")
print(f"qb_ypa_k3={y3/a3:.5f} (6.60484)  qb_epa_k3={e3:.5f} (30.55991)  qb_epa_pa_k3={e3/a3:.5f} (0.24645)")
print(f"qb_yds_std_pg={std_yds:.5f} (245.33333 = 2208/9)  qb_epa_std_pg={std_epa:.5f} (3.33435)")
print(f"qb_yds_form_k3={y3/3 - std_yds:+.5f} (+27.66667)  qb_epa_form_k3={e3/3 - std_epa:+.5f} (+6.85229)")
w5 = {g for _, g in priors[-5:]}
y5, _, _, a5, _ = agg(w5)
print(f"k5 window {sorted(w5)}: qb_yds_k5={y5} (1304)  qb_att_k5={a5} (190)")

# compare vs table row
tab = pd.read_parquet(f"{DATA}/nfl-playerfeat-prep-v1/features/nfl_playerfeat_table_v1.parquet")
tr = tab[(tab["game_id"] == gid) & (tab["side"] == "away")].iloc[0].to_dict()
checks = [
    ("side/team", ("away", tr["side"]), tr["team"] == "KC"),
    ("n_prior_games_used", n_prior, int(tr["n_prior_games_used"]) == n_prior == 9),
    ("rest_days", round(rest, 5), abs(float(tr["rest_days"]) - rest) < 1e-9),
    ("qb_yds_k3", y3, float(tr["qb_yds_k3"]) == y3 == 819.0),
    ("qb_td_k3", td3, float(tr["qb_td_k3"]) == td3 == 6.0),
    ("qb_int_k3", i3, float(tr["qb_int_k3"]) == i3 == 1.0),
    ("qb_att_k3", a3, float(tr["qb_att_k3"]) == a3 == 124.0),
    ("qb_epa_k3", round(e3, 5), abs(float(tr["qb_epa_k3"]) - e3) < 1e-4),
    ("qb_ypa_k3", round(y3 / a3, 5), abs(float(tr["qb_ypa_k3"]) - y3 / a3) < 1e-6),
    ("qb_yds_std_pg", round(std_yds, 5), abs(float(tr["qb_yds_std_pg"]) - std_yds) < 1e-6),
    ("qb_yds_form_k3", round(y3 / 3 - std_yds, 5),
     abs(float(tr["qb_yds_form_k3"]) - (y3 / 3 - std_yds)) < 1e-6),
    ("qb_yds_k5", y5, float(tr["qb_yds_k5"]) == y5 == 1304.0),
    ("qb_att_k5", a5, float(tr["qb_att_k5"]) == a5 == 190.0),
    ("flag_g3_no_snap_prior", 1, int(tr["flag_g3_no_snap_prior"]) == 1
     and pd.isna(tr["g3_top5_absent_share_recent"])),
]
ok = True
for name, mine, match in checks:
    ok &= bool(match)
    print(f"  [{'OK' if match else 'FAIL'}] {name}: mine={mine} table={tr.get(name) if name in tr else ''}")

res = json.load(open(f"{WORK}/t3_results.json"))
res["kc_worked_example_away"] = {
    "n_prior": n_prior, "rest": rest, "yds_k3": y3, "td_k3": td3, "int_k3": i3,
    "att_k3": a3, "checks_ok": bool(ok)}
json.dump(res, open(f"{WORK}/t3_results.json", "w"), indent=2, default=str)
print("\nKC WORKED EXAMPLE:", "VERIFIED (all match, incl. 819/6/1/124)" if ok else "MISMATCH")
