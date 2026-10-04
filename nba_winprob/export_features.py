"""Export normalized games + per-arm Elo pre-ratings + PIT features.

Deterministic data transform only: NO metric, no log loss, no outcome
evaluation exists in this script (that is the successor scored cycle's job
behind its own gate). Reads derived/games.csv (build_dataset output), runs
the frozen B1 arm constants, writes derived/features.csv.

Usage: python -m nba_winprob.export_features --games <derived>/games.csv --out <derived>
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

from .elo import run_elo
from .features import compute_features
from .protocol import ARMS, ELO_GAMMA, ELO_INIT


def load_games(path):
    games = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            games.append({
                "src_game_id": r["src_game_id"],
                "gameorder": int(r["gameorder"]),
                "date": r["date"],
                "season": int(r["season"]),
                "lg": r["lg"],
                "is_playoffs": r["is_playoffs"] == "True",
                "home_lineage": r["home_lineage"],
                "away_lineage": r["away_lineage"],
                "home_win": r["home_win"] == "True",
            })
    return games


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    games = load_games(args.games)
    b1_arms = [a for a in ARMS if a.kind == "B1"]
    elo_by_arm = {}
    for arm in b1_arms:
        rows, _final = run_elo(games, K=arm.K, HCA=arm.HCA,
                               gamma=ELO_GAMMA, init=ELO_INIT)
        elo_by_arm[arm.arm_id] = {r["src_game_id"]: r for r in rows}

    base_feats = compute_features(games, list(elo_by_arm[b1_arms[0].arm_id].values()))

    fields = ["src_game_id", "gameorder", "date", "season", "is_playoffs",
              "home_lineage", "away_lineage",
              "rest_diff", "b2b_home", "b2b_away", "form_home", "form_away",
              "rest_home", "rest_away"]
    for arm in b1_arms:
        fields += [f"elo_diff_{arm.arm_id}", f"p_home_{arm.arm_id}"]

    os.makedirs(args.out, exist_ok=True)
    out_path = os.path.join(args.out, "features.csv")
    n = 0
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for feat in base_feats:
            row = {k: feat[k] for k in fields if k in feat}
            for arm in b1_arms:
                er = elo_by_arm[arm.arm_id][feat["src_game_id"]]
                row[f"elo_diff_{arm.arm_id}"] = er["r_home_pre"] - er["r_away_pre"]
                row[f"p_home_{arm.arm_id}"] = er["p_home"]
            w.writerow(row)
            n += 1

    summary = {
        "n_games": len(games),
        "n_feature_rows": n,
        "b1_arms": [{"arm_id": a.arm_id, "K": a.K, "HCA": a.HCA} for a in b1_arms],
        "mechanics_only": "no outcome metric computed by design (PREP cycle budget 0)",
        "note": "is_playoffs/home_win booleans serialized as True/False strings",
        "features_csv_sha256": _sha256_file(out_path),
    }
    with open(os.path.join(args.out, "FEATURES_MANIFEST.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
