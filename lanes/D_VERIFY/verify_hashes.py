#!/usr/bin/env python
"""Lane D independent hash verification. Read-only; writes report JSON to lanes/D_VERIFY/."""
import json, hashlib, os, sys

HOME_DATA = os.path.expanduser("~/.my-quantitative-data")
OUT = {}

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def check(base, rel, expect_bytes, expect_sha, label):
    p = os.path.join(base, rel)
    if not os.path.exists(p):
        return {"label": label, "file": rel, "verdict": "MISSING"}
    size = os.path.getsize(p)
    sha = sha256_file(p)
    return {
        "label": label, "file": rel,
        "size_ok": size == expect_bytes, "measured_bytes": size, "claimed_bytes": expect_bytes,
        "sha_ok": sha == expect_sha, "measured_sha256": sha, "claimed_sha256": expect_sha,
        "verdict": "MATCH" if (size == expect_bytes and sha == expect_sha) else "MISMATCH",
    }

# ---- NBA (full) vs lane A machine manifest ----
nba_man = json.load(open(f"{HOME_DATA}/playerdata-prep-v1/nba/download_manifest.json"))
OUT["nba"] = [check(f"{HOME_DATA}/playerdata-prep-v1/nba", d["file"], d["bytes"], d["sha256"], d["file"])
              for d in nba_man["downloads"]]

# ---- NFL (full) vs lane C machine manifest ----
nfl_man = json.load(open(os.path.expanduser(
    "~/my-quantitative/.worktrees/winprob-playerdata-prep-v1/integration/lanes/C_NFL/download_manifest_C_NFL.json")))
OUT["nfl"] = [check(f"{HOME_DATA}/playerdata-prep-v1/nfl", d["path"], d["bytes"], d["sha256"], d["path"])
              for d in nfl_man["files"]]

# ---- WNBA (spot sample >=4: player_box 2002, 2013, 2026; game_rosters 2002, 2013, 2026) ----
wnba_man = json.load(open(f"{HOME_DATA}/wnba-prep-v1/roster_audit/download_manifest_r2.json"))
files_by_name = {os.path.basename(name): f for name, f in wnba_man["files"].items()}
sample = ["player_box_2002.csv", "player_box_2013.csv", "player_box_2026.csv",
          "game_rosters_2002.csv", "game_rosters_2013.csv", "game_rosters_2026.csv"]
OUT["wnba_sample"] = []
for name in sample:
    if name not in files_by_name:
        OUT["wnba_sample"].append({"label": name, "verdict": "NOT_IN_PRIOR_MANIFEST"})
        continue
    f = files_by_name[name]
    sha_claim = (f.get("sha256_local") or "").replace("sha256:", "")
    r = check(f"{HOME_DATA}/wnba-prep-v1/roster_audit", name, f.get("bytes"), sha_claim, f"{name} vs prior-cycle manifest r2")
    r["pull_utc"] = f.get("pull_utc")
    OUT["wnba_sample"].append(r)

OUT["wnba_manifest_file_count"] = len(wnba_man["files"])
json.dump(OUT, open(os.path.expanduser(
    "~/my-quantitative/.worktrees/winprob-playerdata-prep-v1/integration/lanes/D_VERIFY/verify_hashes_output.json"), "w"), indent=1)

for grp in ("nba", "nfl"):
    for r in OUT[grp]:
        print(grp.upper(), r["verdict"], r["file"], r.get("measured_bytes"), r.get("size_ok"), r.get("sha_ok"))
for r in OUT["wnba_sample"]:
    print("WNBA", r["verdict"], r.get("label"), r.get("measured_bytes"), r.get("size_ok"), r.get("sha_ok"))
