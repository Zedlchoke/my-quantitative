"""Build the nba-538-v1 normalized dataset from the raw 538 CSV.

Implements lanes/B_dataset/DATASET_SCHEMA.md sec2 (dedup rule + build-time
assertions A1-A8, adapted) with stdlib csv only. 538 elo/forecast columns are
written ONLY to the quarantined side table f538_reference.csv; the canonical
games table never carries them (A15 quarantine law).

Usage:
  python -m nba_winprob.build_dataset --raw <nbaallelo.csv> --out <derived_dir>

The raw file stays outside git (~/.my-quantitative-data/nba-538-v1/raw/); the
derived dir is also outside git; only manifests/hashes land in the repo.
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

EXPECTED_SHA256 = "d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_date(s: str) -> dt.date:
    return dt.datetime.strptime(s.strip(), "%m/%d/%Y").date()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    # A8: byte re-check of the source before every build.
    got_sha = sha256_file(args.raw)
    if got_sha != EXPECTED_SHA256:
        print(f"BUILD FAIL A8: sha256 mismatch {got_sha} != {EXPECTED_SHA256}", file=sys.stderr)
        return 2

    rows = []
    with open(args.raw, newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        header = rdr.fieldnames
        for r in rdr:
            rows.append(r)

    required = {"gameorder", "game_id", "lg_id", "_iscopy", "year_id", "date_game",
                "seasongame", "is_playoffs", "team_id", "fran_id", "pts",
                "opp_id", "opp_fran", "opp_pts", "game_location", "game_result"}
    missing = required - set(header or [])
    if missing:
        print(f"BUILD FAIL: missing columns {sorted(missing)}", file=sys.stderr)
        return 2

    by_game = defaultdict(list)
    for r in rows:
        by_game[r["game_id"]].append(r)

    n_source_rows = len(rows)            # A1
    n_games = len(by_game)
    if n_source_rows != 2 * n_games:
        print(f"BUILD FAIL A1: {n_source_rows} != 2*{n_games}", file=sys.stderr)
        return 2

    games = []
    f538_rows = []
    for gid, pair in by_game.items():
        if len(pair) != 2:
            print(f"BUILD FAIL A2: game {gid} has {len(pair)} rows", file=sys.stderr)
            return 2
        g0 = next((r for r in pair if r["_iscopy"] == "0"), None)
        g1 = next((r for r in pair if r["_iscopy"] == "1"), None)
        if g0 is None or g1 is None:
            print(f"BUILD FAIL A2: game {gid} _iscopy pair broken", file=sys.stderr)
            return 2
        # A3 mirror checks
        if g0["pts"] != g1["opp_pts"] or g0["opp_pts"] != g1["pts"]:
            print(f"BUILD FAIL A3: pts mirror {gid}", file=sys.stderr)
            return 2
        if g0["team_id"] != g1["opp_id"] or g0["opp_id"] != g1["team_id"]:
            print(f"BUILD FAIL A3: id swap {gid}", file=sys.stderr)
            return 2
        if g0["fran_id"] != g1["opp_fran"] or g0["opp_fran"] != g1["fran_id"]:
            print(f"BUILD FAIL A3: fran swap {gid}", file=sys.stderr)
            return 2
        loc0, loc1 = g0["game_location"], g1["game_location"]
        if (loc0 == "H" and loc1 != "A") or (loc0 == "A" and loc1 != "H"):
            # N-N pairs keep site=N for both; H must pair with A
            if not (loc0 == "N" and loc1 == "N"):
                print(f"BUILD FAIL A3: location inversion {gid} {loc0}/{loc1}", file=sys.stderr)
                return 2
        res0, res1 = g0["game_result"], g1["game_result"]
        if res0 == res1:
            print(f"BUILD FAIL A3: result inversion {gid}", file=sys.stderr)
            return 2
        try:
            d = parse_date(g0["date_game"])
        except ValueError:
            print(f"BUILD FAIL A5: unparseable date {gid} {g0['date_game']!r}", file=sys.stderr)
            return 2
        season = int(g0["year_id"])
        home_pts, away_pts = int(g0["pts"]), int(g1["pts"])
        home_win = home_pts > away_pts
        # A4: designated-row result consistency
        if (res0 == "W") != home_win:
            print(f"BUILD FAIL A4: result vs pts {gid}", file=sys.stderr)
            return 2
        # A6: months Oct..Jun; calendar year in {season-1, season}
        if d.month not in (10, 11, 12, 1, 2, 3, 4, 5, 6):
            print(f"BUILD FAIL A6: month {gid} {d}", file=sys.stderr)
            return 2
        if d.year not in (season - 1, season):
            print(f"BUILD FAIL A6: year/season {gid} {d} {season}", file=sys.stderr)
            return 2
        note = (g0.get("notes") or "").strip()
        g = {
            "src_game_id": gid,
            "gameorder": int(g0["gameorder"]),
            "date": d.isoformat(),
            "season": season,
            "lg": g0["lg_id"],
            "is_playoffs": g0["is_playoffs"] == "1",
            "site": "N" if loc0 == "N" else "H",
            "home_lineage": g0["fran_id"],
            "away_lineage": g1["fran_id"],
            "home_team_id": g0["team_id"],
            "away_team_id": g1["team_id"],
            "home_seasongame": int(g0["seasongame"]),
            "away_seasongame": int(g1["seasongame"]),
            "home_pts": home_pts,
            "away_pts": away_pts,
            "home_win": home_win,
            "margin_home": home_pts - away_pts,
            "total_pts": home_pts + away_pts,
            "is_forfeit": "forfeit" in note.lower(),
            "is_protest_completion": ("rotested" in note) or ("ompletion" in note),
            "is_tiebreaker": note == "Tiebreaker",
            "is_round_robin": note == "Round Robin",
            "alt_venue": note.startswith("at "),
            "note": note,
        }
        games.append(g)
        for perspective, r in (("designated", g0), ("other", g1)):
            f538_rows.append({
                "src_game_id": gid,
                "perspective": perspective,
                "lineage": r["fran_id"],
                "elo_i": r["elo_i"], "elo_n": r["elo_n"],
                "opp_elo_i": r["opp_elo_i"], "opp_elo_n": r["opp_elo_n"],
                "win_equiv": r["win_equiv"], "forecast": r["forecast"],
            })

    games.sort(key=lambda g: (g["date"], g["gameorder"]))

    # A5: PK uniqueness + dense gameorder + monotone (date, gameorder)
    seen_ids = set()
    orders = []
    prev_key = None
    for g in games:
        if g["src_game_id"] in seen_ids:
            print(f"BUILD FAIL A5: duplicate game_id {g['src_game_id']}", file=sys.stderr)
            return 2
        seen_ids.add(g["src_game_id"])
        orders.append(g["gameorder"])
        key = (g["date"], g["gameorder"])
        if prev_key is not None and key <= prev_key:
            print(f"BUILD FAIL A5: non-monotone order at {g['src_game_id']}", file=sys.stderr)
            return 2
        prev_key = key
    if sorted(orders) != list(range(1, n_games + 1)):
        print("BUILD FAIL A5: gameorder not dense 1..N", file=sys.stderr)
        return 2

    # lane-B pair-level integrity, CORRECTED by controller measurement
    # 2026-10-04: same-pair same-date repeats == 5 (4 protested-game
    # completion days + the genuine 1954-03-08 MLH doubleheader); team-date
    # doubles == 12 across 6 dates (the 6th is 2008-03-07 Hawks & Heat,
    # different opponents). Lane B's schema said "pair repeats == 6" — that
    # number is the team-double DATE count, not the same-pair count.
    pairdate = defaultdict(int)
    teamdate = defaultdict(int)
    for g in games:
        pairdate[(g["home_lineage"], g["away_lineage"], g["date"])] += 1
        teamdate[(g["home_lineage"], g["date"])] += 1
        teamdate[(g["away_lineage"], g["date"])] += 1
    n_pair_repeats = sum(1 for v in pairdate.values() if v > 1)
    n_team_doubles = sum(1 for v in teamdate.values() if v > 1)
    if n_pair_repeats != 5:
        print(f"BUILD FAIL: same-pair same-date repeat count {n_pair_repeats} != 5", file=sys.stderr)
        return 2
    if n_team_doubles != 12:
        print(f"BUILD FAIL: team-date double count {n_team_doubles} != 12", file=sys.stderr)
        return 2

    # lineages dimension table (continuity: team_id -> single fran_id)
    tid2fran = defaultdict(set)
    lineage_seasons = defaultdict(list)
    lineage_games = defaultdict(int)
    for r in rows:
        tid2fran[r["team_id"]].add(r["fran_id"])
    for t, frans in tid2fran.items():
        if len(frans) != 1:
            print(f"BUILD FAIL lineage: team_id {t} maps to {sorted(frans)}", file=sys.stderr)
            return 2
    for g in games:
        lineage_seasons[g["home_lineage"]].append(g["season"])
        lineage_seasons[g["away_lineage"]].append(g["season"])
        lineage_games[g["home_lineage"]] += 1
        lineage_games[g["away_lineage"]] += 1
    lineage_rows = []
    frans = {}
    for t, fr_set in sorted(tid2fran.items()):
        fr = next(iter(fr_set))  # singleton asserted above
        frans.setdefault(fr, []).append(t)
    for fran, tids in sorted(frans.items()):
        ss = lineage_seasons[fran]
        lineage_rows.append({
            "lineage_id": fran,
            "team_ids": ";".join(tids),
            "first_season": min(ss), "last_season": max(ss),
            "n_games": lineage_games[fran],
        })
    if len(lineage_rows) != 53:
        print(f"BUILD FAIL lineage: {len(lineage_rows)} != 53 lineages", file=sys.stderr)
        return 2

    # participants long view (schema sec6)
    participants = []
    for g in games:
        participants.append({
            "src_game_id": g["src_game_id"], "gameorder": g["gameorder"],
            "date": g["date"], "season": g["season"], "lg": g["lg"],
            "is_playoffs": g["is_playoffs"], "lineage": g["home_lineage"],
            "role": "home", "opp_lineage": g["away_lineage"],
            "pts_for": g["home_pts"], "pts_against": g["away_pts"],
            "win": g["home_win"], "seasongame": g["home_seasongame"],
            "site": g["site"],
        })
        participants.append({
            "src_game_id": g["src_game_id"], "gameorder": g["gameorder"],
            "date": g["date"], "season": g["season"], "lg": g["lg"],
            "is_playoffs": g["is_playoffs"], "lineage": g["away_lineage"],
            "role": "away", "opp_lineage": g["home_lineage"],
            "pts_for": g["away_pts"], "pts_against": g["home_pts"],
            "win": (not g["home_win"]), "seasongame": g["away_seasongame"],
            "site": g["site"],
        })

    os.makedirs(args.out, exist_ok=True)

    def write_csv(name, fieldnames, data):
        path = os.path.join(args.out, name)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(data)
        return name, sha256_file(path), len(data)

    outputs = []
    outputs.append(write_csv("games.csv",
        ["src_game_id", "gameorder", "date", "season", "lg", "is_playoffs", "site",
         "home_lineage", "away_lineage", "home_team_id", "away_team_id",
         "home_seasongame", "away_seasongame", "home_pts", "away_pts",
         "home_win", "margin_home", "total_pts", "is_forfeit",
         "is_protest_completion", "is_tiebreaker", "is_round_robin",
         "alt_venue", "note"], games))
    outputs.append(write_csv("lineages.csv",
        ["lineage_id", "team_ids", "first_season", "last_season", "n_games"], lineage_rows))
    outputs.append(write_csv("participants.csv",
        ["src_game_id", "gameorder", "date", "season", "lg", "is_playoffs",
         "lineage", "role", "opp_lineage", "pts_for", "pts_against", "win",
         "seasongame", "site"], participants))
    outputs.append(write_csv("f538_reference.csv",  # QUARANTINED (A15)
        ["src_game_id", "perspective", "lineage", "elo_i", "elo_n",
         "opp_elo_i", "opp_elo_n", "win_equiv", "forecast"], f538_rows))

    manifest = {
        "dataset_id": "nba-538-v1",
        "built_at_utc": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "source_raw": os.path.abspath(args.raw),
        "source_sha256": got_sha,
        "n_source_rows": n_source_rows,
        "n_games": n_games,
        "n_lineages": len(lineage_rows),
        "test_seasons_frozen": [2009, 2010, 2011, 2012, 2013, 2014, 2015],
        "train_seasons_range": [1947, 2008],
        "assertions": "A1-A8 + same-pair-date==5 + team-date-doubles==12 + lineage==53 PASSED (build reached write; controller-corrected counts, see source comment)",
        "outputs": [{"file": f, "sha256": s, "rows": n} for f, s, n in outputs],
    }
    with open(os.path.join(args.out, "BUILD_MANIFEST.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)
    print(json.dumps(manifest, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
