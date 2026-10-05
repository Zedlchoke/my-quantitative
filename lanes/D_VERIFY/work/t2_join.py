#!/usr/bin/env python
"""D_VERIFY T2 — independent re-join rates (GSIS weekly stats; PFR snap counts)."""
import json, os
import pandas as pd

DATA = os.path.expanduser("~/.my-quantitative-data")
OUT = "/Users/hoangminhlong/my-quantitative/.worktrees/nfl-playerfeat-prep-v1/integration/lanes/D_VERIFY/work/t2_join_results.json"

# Build crosswalk map my own way: gsis_id non-null, dedupe, pfr_id index
cw = pd.read_parquet(f"{DATA}/playerfeat-prep-v1/nfl/raw_players/players.parquet")
cw2 = cw[cw["gsis_id"].notna()].drop_duplicates("gsis_id")
gsis_set = set(cw2["gsis_id"])
pfr_map = cw2[cw2["pfr_id"].notna()].drop_duplicates("pfr_id").set_index("pfr_id")["gsis_id"]
pfr_set = set(pfr_map.index)

res = {"stats_gsis": {}, "snap_pfr": {}}
for y in (2024, 2025, 2026):
    s = pd.read_parquet(f"{DATA}/playerdata-prep-v1/nfl/raw_stats_player/stats_player_week_{y}.parquet")
    n_placeholder = int(s["player_id"].isna().sum())
    ids = set(s.loc[s["player_id"].notna(), "player_id"])
    resolved = ids & gsis_set
    res["stats_gsis"][str(y)] = {
        "players": len(ids), "resolved": len(resolved),
        "rate": round(len(resolved) / len(ids), 6),
        "placeholder_rows": n_placeholder,
    }
    print(f"stats {y}: unique players={len(ids)} resolved={len(resolved)} "
          f"rate={len(resolved)/len(ids):.6f} placeholder_rows={n_placeholder}")

for y in (2025, 2026):
    s = pd.read_parquet(f"{DATA}/playerdata-prep-v1/nfl/raw_snap_counts/snap_counts_{y}.parquet")
    ids = set(s.loc[s["pfr_player_id"].notna(), "pfr_player_id"])
    resolved = ids & pfr_set
    res["snap_pfr"][str(y)] = {
        "players": len(ids), "resolved": len(resolved),
        "rate": round(len(resolved) / len(ids), 6),
        "unresolved": sorted(ids - pfr_set),
    }
    print(f"snap {y}: unique pfr players={len(ids)} resolved={len(resolved)} "
          f"rate={len(resolved)/len(ids):.6f} unresolved={sorted(ids - pfr_set)}")

# claims from FEATURE_TABLE_MANIFEST.json
claims = {
    "stats_gsis": {"2024": (2001, 1.0), "2025": (2024, 1.0), "2026": (1512, 1.0)},
    "snap_pfr": {"2025": (2189, 2183, 0.997259), "2026": (1679, 1676, 0.998213)},
    "unresolved_2025": sorted(["AndeAl01", "CartNa00", "HallGa01", "JohnIs03", "OkoyCJ00", "WhitCo05"]),
    "unresolved_2026": sorted(["AndeAl01", "OkoyCJ00", "WhitCo05"]),
}
ok = True
for y, (pn, rate) in claims["stats_gsis"].items():
    r = res["stats_gsis"][y]
    m = (r["players"] == pn and r["rate"] == rate)
    ok &= m
    print(f"claim stats {y}: players={pn} rate={rate} -> {'MATCH' if m else 'MISMATCH got ' + str(r)}")
for y, (pn, rs, rate) in claims["snap_pfr"].items():
    r = res["snap_pfr"][y]
    m = (r["players"] == pn and r["resolved"] == rs and r["rate"] == rate)
    ok &= m
    print(f"claim snap {y}: players={pn} resolved={rs} rate={rate} -> {'MATCH' if m else 'MISMATCH got ' + str(r)}")
m25 = res["snap_pfr"]["2025"]["unresolved"] == claims["unresolved_2025"]
m26 = res["snap_pfr"]["2026"]["unresolved"] == claims["unresolved_2026"]
ok &= m25 and m26
print(f"unresolved 2025 census -> {'MATCH' if m25 else 'MISMATCH'}; unresolved 2026 census -> {'MATCH' if m26 else 'MISMATCH'}")
print(f"OVERALL: {'JOIN_RATES_VERIFIED' if ok else 'JOIN_RATE_DISCREPANCY'}")
json.dump(res, open(OUT, "w"), indent=2)
