#!/usr/bin/env python
"""D_VERIFY own-code hash verification. Re-hashes bytes and compares to the
claims in lane manifests. INDEPENDENT of lane code — reads manifests only as claims."""
import hashlib, json, gzip, os, sys

HOME = os.path.expanduser("~")
WT = "/Users/hoangminhlong/my-quantitative/.worktrees/winprob-playerfeat-prep-v1/integration"

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

out = {"nba": [], "wnba": [], "nfl": []}

# ---------- NBA: all 22 inputs from A's FEATURE_TABLE_MANIFEST.json + outputs ----------
man = json.load(open(f"{WT}/lanes/A_NBA_FEAT/FEATURE_TABLE_MANIFEST.json"))
for ent in man["inputs_sha256"]:
    p = ent["file"]
    got = sha256(p)
    out["nba"].append({"file": p, "claimed": ent["sha256"], "measured": got,
                       "match": got == ent["sha256"], "bytes": os.path.getsize(p)})
for ent in man["outputs"]:
    p = ent["file"]
    got = sha256(p)
    out["nba"].append({"file": p, "claimed": ent["sha256"], "measured": got,
                       "match": got == ent["sha256"], "bytes": os.path.getsize(p),
                       "claimed_bytes": ent["bytes"]})

# ---------- WNBA: corpus re-hash vs download_manifest_r2.json ----------
r2 = json.load(open(f"{HOME}/.my-quantitative-data/wnba-prep-v1/roster_audit/download_manifest_r2.json"))
# figure out manifest structure
files_by_name = {}
def walk(o):
    if isinstance(o, dict):
        if "sha256" in o and ("path" in o or "file" in o or "name" in o):
            files_by_name[o.get("path") or o.get("file") or o.get("name")] = o
        for v in o.values():
            walk(v)
    elif isinstance(o, list):
        for v in o:
            walk(v)
walk(r2)
CLAIM_WNBA = ["player_box_2002.csv", "player_box_2013.csv", "player_box_2020.csv",
              "player_box_2026.csv", "game_rosters_2002.csv", "game_rosters_2013.csv",
              "game_rosters_2019.csv", "game_rosters_2026.csv"]
base = f"{HOME}/.my-quantitative-data/wnba-prep-v1/roster_audit/"
for name in CLAIM_WNBA:
    p = base + name
    got = sha256(p)
    claimed = None
    for k, v in files_by_name.items():
        if k and k.endswith(name):
            claimed = v
            break
    if claimed is None:
        out["wnba"].append({"file": name, "claimed": "NOT_FOUND_IN_MANIFEST", "measured": got, "match": False})
    else:
        csha = claimed.get("sha256"); cbytes = claimed.get("bytes") or claimed.get("size")
        out["wnba"].append({"file": name, "claimed": csha, "measured": got,
                            "match": got == csha, "bytes": os.path.getsize(p),
                            "claimed_bytes": cbytes, "manifest_key": k if False else claimed.get("path") or claimed.get("file") or claimed.get("name")})
# WNBA output parquet
pwn = f"{HOME}/.my-quantitative-data/playerfeat-prep-v1/wnba/features/wnba_player_features_2002_2026.parquet"
out["wnba"].append({"file": pwn, "claimed": "ceaf10ba33e705b9569a11cec2aa33e1875e372c35d643ed5d80d5e757ffc7bf",
                    "measured": sha256(pwn), "bytes": os.path.getsize(pwn)})
out["wnba"][-1]["match"] = out["wnba"][-1]["measured"] == out["wnba"][-1]["claimed"]

# ---------- NFL: players.parquet + timestamp.json ----------
pnfl = f"{HOME}/.my-quantitative-data/playerfeat-prep-v1/nfl/raw_players/players.parquet"
out["nfl"].append({"file": pnfl, "claimed": "485b198070f831ed3a9098b991cd4b5dd97407e23a08fe31629d18dc304885e2",
                   "measured": sha256(pnfl), "bytes": os.path.getsize(pnfl), "claimed_bytes": 3389574})
out["nfl"][-1]["match"] = out["nfl"][-1]["measured"] == out["nfl"][-1]["claimed"]
tsj = f"{HOME}/.my-quantitative-data/playerfeat-prep-v1/nfl/raw_players/timestamp.json"
out["nfl"].append({"file": tsj, "claimed": "23955f4e32cd7899d6c50bb478438161b89d974058eeee81fef1d1c33042f4b4",
                   "measured": sha256(tsj)})
out["nfl"][-1]["match"] = out["nfl"][-1]["measured"] == out["nfl"][-1]["claimed"]

# predecessor NFL inputs used by C (5 files) — re-hash for Task 3 integrity
PRED = [
    (f"{HOME}/.my-quantitative-data/playerdata-prep-v1/nfl/raw_stats_player/stats_player_week_2024.parquet", None),
    (f"{HOME}/.my-quantitative-data/playerdata-prep-v1/nfl/raw_stats_player/stats_player_week_2025.parquet", None),
    (f"{HOME}/.my-quantitative-data/playerdata-prep-v1/nfl/raw_stats_player/stats_player_week_2026.parquet", None),
    (f"{HOME}/.my-quantitative-data/playerdata-prep-v1/nfl/raw_snap_counts/snap_counts_2025.parquet", None),
    (f"{HOME}/.my-quantitative-data/playerdata-prep-v1/nfl/raw_snap_counts/snap_counts_2026.parquet", None),
]
pred_man = json.load(open(f"{WT}/lanes/C_NFL_CROSSWALK/download_manifest_C_NFL_CROSSWALK.json"))
pred_claims = {}
def walk2(o):
    if isinstance(o, dict):
        if "sha256" in o:
            key = o.get("file") or o.get("path") or o.get("name")
            if key:
                pred_claims[os.path.basename(str(key))] = o["sha256"]
        for v in o.values():
            walk2(v)
    elif isinstance(o, list):
        for v in o:
            walk2(v)
walk2(pred_man)
for p, _ in PRED:
    got = sha256(p)
    cl = pred_claims.get(os.path.basename(p))
    out["nfl"].append({"file": p, "claimed": cl, "measured": got, "match": (cl == got) if cl else "NO_CLAIM"})

tot = 0; ok = 0
for lane, rows in out.items():
    for r in rows:
        tot += 1
        good = r.get("match") is True
        ok += 1 if good else 0
        flag = "OK " if good else "FAIL"
        print(f"[{flag}] {lane}: {os.path.basename(r['file'])} claimed={str(r.get('claimed'))[:16]}.. measured={r['measured'][:16]}..")
print(f"\nTOTAL {ok}/{tot} hash checks match")
json.dump(out, open("/Users/hoangminhlong/my-quantitative/.worktrees/winprob-playerfeat-prep-v1/integration/lanes/D_VERIFY/hash_output.json", "w"), indent=1)
