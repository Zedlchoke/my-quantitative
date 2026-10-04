"""Export per-arm Elo pre-ratings + PIT features (mechanics only, no metric).

Usage: python -m nfl_winprob.export_features --games <derived>/games_nfl.csv --out <derived>
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os

from .elo import run_elo
from .features import compute_features
from .protocol import ARMS, ELO_GAMMA, ELO_INIT


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    games = []
    with open(args.games, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            games.append({
                "game_id": r["game_id"], "season": int(r["season"]),
                "week": int(r["week"]), "game_type": r["game_type"],
                "is_playoffs": r["is_playoffs"] == "True",
                "kickoff_utc": r["kickoff_utc"],
                "home_lineage": r["home_lineage"], "away_lineage": r["away_lineage"],
                "home_pts": int(r["home_pts"]), "away_pts": int(r["away_pts"]),
                "home_win": r["home_win"] == "True", "tie": r["tie"] == "True",
                "neutral": r["neutral"] == "True",
            })
    b1 = [a for a in ARMS if a.kind == "B1"]
    elo_by_arm = {}
    for arm in b1:
        rows, _ = run_elo(games, K=arm.K, HCA=arm.HCA, gamma=ELO_GAMMA, init=ELO_INIT)
        elo_by_arm[arm.arm_id] = {r["game_id"]: r for r in rows}
    feats = compute_features(games, list(elo_by_arm[b1[0].arm_id].values()))

    fields = ["game_id", "kickoff_utc", "season", "is_playoffs",
              "home_lineage", "away_lineage",
              "elo_diff",  # AMENDMENT (pre-scored): unsuffixed f1 = B1-a stream (K=20, HCA=0)
              "rest_diff", "short_week_home", "short_week_away",
              "form_home", "form_away", "rest_home", "rest_away"]
    for arm in b1:
        fields += [f"elo_diff_{arm.arm_id}", f"p_home_{arm.arm_id}"]
    os.makedirs(args.out, exist_ok=True)
    out_path = os.path.join(args.out, "features_nfl.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for ft in feats:
            row = {k: ft[k] for k in fields if k in ft}
            er_a = elo_by_arm["B1-a"][ft["game_id"]]
            row["elo_diff"] = er_a["r_home_pre"] - er_a["r_away_pre"]
            for arm in b1:
                er = elo_by_arm[arm.arm_id][ft["game_id"]]
                row[f"elo_diff_{arm.arm_id}"] = er["r_home_pre"] - er["r_away_pre"]
                row[f"p_home_{arm.arm_id}"] = er["p_home"]
            w.writerow(row)
    summary = {
        "n_games": len(games), "n_feature_rows": len(feats),
        "b1_arms": [{"arm_id": a.arm_id, "K": a.K, "HCA": a.HCA} for a in b1],
        "mechanics_only": "no outcome metric computed by design (PREP cycle budget 0)",
        "features_csv_sha256": _sha256_file(out_path),
        "built_at_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
    }
    with open(os.path.join(args.out, "FEATURES_MANIFEST_NFL.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
