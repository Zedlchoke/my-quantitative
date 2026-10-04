"""Build the nfl-nflverse-v1 normalized dataset from raw games.csv.

Laws: kickoff-grain as-of (gametime US/Eastern -> UTC via zoneinfo, with a
documented safe fallback); seasons >= 2000 (1999 lacks gametime — lane B);
finished games only (2026 futures excluded); betting columns QUARANTINED
(never read); lineage continuity via the frozen rename map (lane B census).

Usage: python -m nfl_winprob.build_dataset --raw <games.csv> --out <derived_dir>
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import sys
from collections import defaultdict
from zoneinfo import ZoneInfo

from .protocol import KICKOFF_GRAIN_SAFE_FROM_SEASON

ET = ZoneInfo("America/New_York")

# frozen franchise-continuity map (lane B census; 35 abbrevs -> lineages)
RENAME_MAP = {
    "STL": "Rams", "LA": "Rams",
    "SD": "Chargers", "LAC": "Chargers",
    "OAK": "Raiders", "LV": "Raiders",
}
EXPECTED_LINEAGE_COUNT = 32  # controller correction 2026-10-04: lane B proposed 31 by
# merging CLE+BAL into one row; standard NFL franchise-continuity convention
# (and lane B's own note that CLE/BAL is a protocol decision) keeps CLE
# (Browns, continuous) and BAL (Ravens, 1996+) as SEPARATE lineages -> 32.

QUARANTINED_COLUMNS = ("away_moneyline", "home_moneyline", "spread_line",
                       "away_spread_odds", "home_spread_odds", "total_line",
                       "under_odds", "over_odds")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_kickoff(gameday: str, gametime: str) -> dt.datetime:
    d = dt.date.fromisoformat(gameday.strip())
    hh, mm = gametime.strip().split(":")
    local = dt.datetime(d.year, d.month, d.day, int(hh), int(mm), tzinfo=ET)
    return local.astimezone(dt.timezone.utc)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    required = ["game_id", "season", "game_type", "week", "gameday", "gametime",
                "away_team", "away_score", "home_team", "home_score", "location"]
    rows = []
    with open(args.raw, newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        missing = set(required) - set(rdr.fieldnames or [])
        if missing:
            print(f"BUILD FAIL: missing columns {sorted(missing)}", file=sys.stderr)
            return 2
        for r in rdr:
            rows.append(r)

    games = []
    skipped = {"pre2000": 0, "unfinished": 0, "bad_time": 0}
    for r in rows:
        season = int(r["season"])
        if season < KICKOFF_GRAIN_SAFE_FROM_SEASON:
            skipped["pre2000"] += 1
            continue
        hs, as_ = (r["home_score"] or "").strip(), (r["away_score"] or "").strip()
        if not hs or not as_:
            skipped["unfinished"] += 1
            continue
        try:
            kickoff = parse_kickoff(r["gameday"], r["gametime"])
        except Exception:
            skipped["bad_time"] += 1
            continue
        home_pts, away_pts = int(float(hs)), int(float(as_))
        games.append({
            "game_id": r["game_id"],
            "season": season,
            "week": int(r["week"]) if r["week"] else 0,
            "game_type": r["game_type"],
            "is_playoffs": r["game_type"] != "reg",
            "kickoff_utc": kickoff.isoformat(),
            "home_lineage": RENAME_MAP.get(r["home_team"], r["home_team"]),
            "away_lineage": RENAME_MAP.get(r["away_team"], r["away_team"]),
            "home_team": r["home_team"], "away_team": r["away_team"],
            "home_pts": home_pts, "away_pts": away_pts,
            "home_win": home_pts > away_pts,
            "tie": home_pts == away_pts,
            "neutral": r["location"].strip().lower() == "neutral",
        })

    games.sort(key=lambda g: (g["kickoff_utc"], g["game_id"]))

    # assertions
    ids = set()
    for g in games:
        if g["game_id"] in ids:
            print(f"BUILD FAIL: duplicate game_id {g['game_id']}", file=sys.stderr)
            return 2
        ids.add(g["game_id"])
    lineages = {g["home_lineage"] for g in games} | {g["away_lineage"] for g in games}
    n_ties = sum(1 for g in games if g["tie"])
    n_neutral = sum(1 for g in games if g["neutral"])
    # quarantine proof: this script never touches betting columns
    src = open(__file__, encoding="utf-8").read()
    for col in QUARANTINED_COLUMNS:
        assert src.count(col) == 1, f"quarantine leak: {col}"  # only the tuple above

    os.makedirs(args.out, exist_ok=True)
    out_path = os.path.join(args.out, "games_nfl.csv")
    fields = ["game_id", "season", "week", "game_type", "is_playoffs", "kickoff_utc",
              "home_lineage", "away_lineage", "home_team", "away_team",
              "home_pts", "away_pts", "home_win", "tie", "neutral"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(games)

    lin_rows = []
    stats = defaultdict(lambda: [9999, 0, 0])
    for g in games:
        for side in ("home_lineage", "away_lineage"):
            s = stats[g[side]]
            s[0] = min(s[0], g["season"]); s[1] = max(s[1], g["season"]); s[2] += 1
    for lin, (first, last, n) in sorted(stats.items()):
        lin_rows.append({"lineage_id": lin, "first_season": first, "last_season": last, "n_games": n})
    with open(os.path.join(args.out, "lineages_nfl.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["lineage_id", "first_season", "last_season", "n_games"])
        w.writeheader()
        w.writerows(lin_rows)

    manifest = {
        "dataset_id": "nfl-nflverse-v1",
        "built_at_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "source_raw": os.path.abspath(args.raw),
        "source_sha256": sha256_file(args.raw),
        "n_source_rows": len(rows),
        "n_games": len(games),
        "skipped": skipped,
        "n_lineages": len(lin_rows),
        "n_ties": n_ties,
        "n_neutral": n_neutral,
        "expected_lineage_count": EXPECTED_LINEAGE_COUNT,
        "lineage_count_ok": len(lin_rows) == EXPECTED_LINEAGE_COUNT,
        "quarantined_columns": list(QUARANTINED_COLUMNS),
        "kickoff_tz": "America/New_York (zoneinfo; documented ET semantics per lane B)",
        "test_seasons_frozen": [2019, 2020, 2021, 2022, 2023, 2024, 2025],
        "train_seasons_range": [2000, 2018],
        "outputs": [{"file": "games_nfl.csv", "sha256": sha256_file(out_path), "rows": len(games)},
                    {"file": "lineages_nfl.csv", "sha256": sha256_file(os.path.join(args.out, "lineages_nfl.csv")), "rows": len(lin_rows)}],
    }
    with open(os.path.join(args.out, "BUILD_MANIFEST_NFL.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)
    print(json.dumps({k: manifest[k] for k in
                      ("n_games", "skipped", "n_lineages", "lineage_count_ok", "n_ties", "n_neutral")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
