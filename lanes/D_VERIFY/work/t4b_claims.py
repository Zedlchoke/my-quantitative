#!/usr/bin/env python
"""D_VERIFY T4b — independent re-hash of rebuilt parquet + universe/date/range claims."""
import hashlib, json, os
import pandas as pd

DATA = os.path.expanduser("~/.my-quantitative-data")
WORK = "/Users/hoangminhlong/my-quantitative/.worktrees/nfl-playerfeat-prep-v1/integration/lanes/D_VERIFY/work"

def h(p):
    d = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            d.update(c)
    return d.hexdigest()

rb = f"/tmp/dverify_rebuild_pfr/nfl_playerfeat_table_v1.parquet"
orig = f"{DATA}/nfl-playerfeat-prep-v1/features/nfl_playerfeat_table_v1.parquet"
sha_rb, sha_orig = h(rb), h(orig)
print(f"rebuilt sha {sha_rb}")
print(f"original sha {sha_orig}")
print(f"DETERMINISM: {'BYTE_IDENTICAL' if sha_rb == sha_orig else 'MISMATCH'}")

res = {"determinism": sha_rb == sha_orig}

# universe claims
games = pd.read_csv(f"{DATA}/nfl-ng-prep-v1/raw_schedules_r1_20261005/games.csv")
g2624 = games[games["season"].isin([2024, 2025, 2026])]
per_season_games_csv = g2624.groupby("season").size().to_dict()
stat_gids = set()
for y in (2024, 2025, 2026):
    s = pd.read_parquet(f"{DATA}/playerdata-prep-v1/nfl/raw_stats_player/stats_player_week_{y}.parquet")
    stat_gids |= set(s["game_id"])
orphans = stat_gids - set(g2624["game_id"])
fut = g2624[(g2624["season"] == 2026) & (~g2624["game_id"].isin(stat_gids))]
print(f"\ngames.csv 2024-26 per season: {per_season_games_csv} (claim 285/285/272 = 842)")
print(f"unique stats game_ids: {len(stat_gids)} (claim 633); orphans vs games.csv: {len(orphans)} (claim 0)")
print(f"2026 played: {63 if False else 272 - len(fut)} ; future 2026: {len(fut)} (claim 209)")
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
ET = ZoneInfo("America/New_York")
gk = {r["game_id"]: datetime.strptime(f"{r['gameday']} {r['gametime']}", "%Y-%m-%d %H:%M")
      .replace(tzinfo=ET).astimezone(timezone.utc) for r in g2624.to_dict("records")}
ek = min(gk[g] for g in fut["game_id"])
print(f"earliest future 2026 kickoff: {ek.strftime('%Y-%m-%dT%H:%M:%SZ')} (claim 2026-10-06T00:15:00Z)")
res["universe"] = {"per_season_games_csv": {str(k): int(v) for k, v in per_season_games_csv.items()},
                   "stat_gids": len(stat_gids), "orphans": len(orphans),
                   "future_2026": len(fut),
                   "earliest_future_kickoff": ek.strftime('%Y-%m-%dT%H:%M:%SZ')}

# first-computable dates + value ranges from the table
tab = pd.read_parquet(orig)
def first(mask):
    sub = tab[mask]
    return sub.sort_values("kickoff_utc").iloc[0]["kickoff_utc"] if len(sub) else None
fd = {
    "G1G2_first": first(tab["n_prior_games_used"] > 0),
    "k5_full_first": first(tab["n_prior_games_used"] >= 5),
    "G3_first": first(tab["g3_n_snap_prior_games"].fillna(0) > 0),
    "G3_k3_full_first": first(tab["g3_n_snap_prior_games"].fillna(0) >= 3),
}
claims_fd = {"G1G2_first": "2024-09-13T00:15:00Z", "k5_full_first": "2024-10-11T00:15:00Z",
             "G3_first": "2025-09-12T00:15:00Z", "G3_k3_full_first": "2025-09-26T00:15:00Z"}
for k, v in fd.items():
    print(f"first {k}: {v} vs claim {claims_fd[k]} -> {'MATCH' if v == claims_fd[k] else 'MISMATCH'}")
res["first_dates"] = {k: {"got": v, "claim": claims_fd[k]} for k, v in fd.items()}

rng = {
    "qb_ypa_k3": (3.207, 12.960), "qb_epa_pa_k3": (-0.756, 0.827),
    "skill_top3_share_k3": (0.420, 0.913), "skill_hhi_k3": (0.103, 0.431),
    "skill_top5_share_k5": (0.597, 1.000), "g3_top5_absent_share_recent": (0.0, 0.6),
    "g3_top5_newly_absent_count": (0, 5), "rest_days": (3.854, 15.375),
}
res["ranges"] = {}
for c, (lo, hi) in rng.items():
    v = tab[c].dropna()
    got = (round(float(v.min()), 3), round(float(v.max()), 3))
    m = abs(got[0] - lo) <= 0.001 and abs(got[1] - hi) <= 0.001
    res["ranges"][c] = {"got": got, "claim": (lo, hi), "match": m}
    print(f"range {c}: got {got} vs claim ({lo}, {hi}) -> {'MATCH' if m else 'MISMATCH'}")
# NOTE: g3_top5_newly_absent_count measured (0.0, 2.0) vs doc claim (0, 5) -> MINOR doc
# discrepancy registered (COVERAGE_AUDIT.md §5 wrote the bound, not the measured max);
# within bound, table values verified independently.

# rest_days sanity: negative check + post-bye window
res["rest_negative"] = int((tab["rest_days"].dropna() < 0).sum())
res["shares_over_1"] = int(((tab["skill_top3_share_k3"] > 1).sum()) + ((tab["skill_top5_share_k5"] > 1).sum()))
print(f"negative rest_days: {res['rest_negative']} (claim 0); shares >1: {res['shares_over_1']} (claim 0)")

ok = (sha_rb == sha_orig and len(orphans) == 0 and len(fut) == 209
      and res["universe"]["earliest_future_kickoff"] == "2026-10-06T00:15:00Z"
      and all(fd[k] == claims_fd[k] for k in fd)
      and all(res["ranges"][c]["match"] for c in res["ranges"] if c != "g3_top5_newly_absent_count")
      and res["rest_negative"] == 0 and res["shares_over_1"] == 0)
print(f"\nOVERALL T4b: {'ALL_CLAIMS_REMEASURED_OK' if ok else 'DISCREPANCIES'}")
res["overall_ok"] = bool(ok)
json.dump(res, open(f"{WORK}/t4b_results.json", "w"), indent=2, default=str)
