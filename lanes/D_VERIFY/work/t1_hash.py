#!/usr/bin/env python
"""D_VERIFY T1 — independent re-hash of manifest inputs + output parquet."""
import hashlib, json, os, sys

DATA = os.path.expanduser("~/.my-quantitative-data")
MAN = ("/Users/hoangminhlong/my-quantitative/.worktrees/nfl-playerfeat-prep-v1/"
       "integration/lanes/B_BUILD/FEATURE_TABLE_MANIFEST.json")

def h(path):
    d = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            d.update(chunk)
    return d.hexdigest()

targets = {
    "raw_stats_player/stats_player_week_2024.parquet": f"{DATA}/playerdata-prep-v1/nfl/raw_stats_player/stats_player_week_2024.parquet",
    "raw_stats_player/stats_player_week_2025.parquet": f"{DATA}/playerdata-prep-v1/nfl/raw_stats_player/stats_player_week_2025.parquet",
    "raw_stats_player/stats_player_week_2026.parquet": f"{DATA}/playerdata-prep-v1/nfl/raw_stats_player/stats_player_week_2026.parquet",
    "raw_snap_counts/snap_counts_2025.parquet": f"{DATA}/playerdata-prep-v1/nfl/raw_snap_counts/snap_counts_2025.parquet",
    "raw_snap_counts/snap_counts_2026.parquet": f"{DATA}/playerdata-prep-v1/nfl/raw_snap_counts/snap_counts_2026.parquet",
    "raw_players/players.parquet": f"{DATA}/playerfeat-prep-v1/nfl/raw_players/players.parquet",
    "OUTPUT nfl_playerfeat_table_v1.parquet": f"{DATA}/nfl-playerfeat-prep-v1/features/nfl_playerfeat_table_v1.parquet",
}

man = json.load(open(MAN))
claims = dict(man["inputs_sha256"])
claims["OUTPUT nfl_playerfeat_table_v1.parquet"] = man["output"]["sha256"]

results = {}
ok = True
for name, path in sorted(targets.items()):
    actual = h(path)
    claimed = claims.get(name)
    match = (actual == claimed)
    ok &= match
    results[name] = {"actual": actual, "claimed": claimed, "match": match,
                     "bytes": os.path.getsize(path)}
    print(f"[{'MATCH' if match else 'MISMATCH'}] {name}\n  actual {actual}\n  claimed {claimed}")

print(f"\nOVERALL: {'ALL_HASHES_MATCH' if ok else 'HASH_MISMATCH_FOUND'}")
json.dump(results, open("/Users/hoangminhlong/my-quantitative/.worktrees/nfl-playerfeat-prep-v1/integration/lanes/D_VERIFY/work/t1_hash_results.json", "w"), indent=2)
sys.exit(0 if ok else 1)
