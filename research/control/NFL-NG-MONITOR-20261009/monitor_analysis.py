#!/usr/bin/env python
"""DESCRIPTIVE_MONITORING — NFL-WINPROB-NG-SCORED-V1 monitor, 2026-10-09.

Owner-directed descriptive monitoring round. READ-ONLY on the ledger and all
other cycles' files. Calibration vocabulary only: accuracy / log loss / Brier
are DESCRIPTORS of recorded forecasts on FINAL games only. This monitoring
consumes NO scored-cell budget of any cycle and modifies NO ledger.

Strict FINAL rule: a game counts FINAL only if the snapshot row carries
non-empty integer scores for BOTH teams (and derived result/total populated).
Ambiguous rows would be classified NOT_RUN_STATUS_AMBIGUOUS (none occurred).
"""
import csv
import datetime as dt
import hashlib
import json
import math
import os

DATA = "/Users/hoangminhlong/.my-quantitative-data/nfl-ng-monitor-20261009"
LEDGER = ("/Users/hoangminhlong/.my-quantitative-data/nfl-ng-scored-v1/"
          "predictions_NFL-WINPROB-NG-SCORED-V1_2026.jsonl")
STAGING = ("/Users/hoangminhlong/my-quantitative/research/control/"
           "NFL-NG-MONITOR-20261009")

ARMS = ["B0", "B1_STAR", "C3"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_score(v):
    """Return int score, or None if absent/blank."""
    if v is None:
        return None
    v = str(v).strip()
    if v == "":
        return None
    try:
        return int(v)
    except ValueError:
        return None


def main():
    # ---------- provenance ----------
    prov = {
        "snapshot_urls": [
            "https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv",
            "https://github.com/nflverse/nflverse-data/releases/download/schedules/timestamp.json",
        ],
        "retrieval_utc": "2026-10-09T10:58:11Z",
        "sha256": {
            "games.csv": sha256(f"{DATA}/games.csv"),
            "timestamp.json": sha256(f"{DATA}/timestamp.json"),
        },
        "timestamp_json_content": json.load(open(f"{DATA}/timestamp.json")),
        "ledger_path": LEDGER,
        "ledger_sha256": sha256(LEDGER),
    }
    print("PROVENANCE:", json.dumps(prov, indent=2))
    with open(f"{DATA}/provenance_monitor_20261009.json", "w") as f:
        json.dump(prov, f, indent=2)

    # ---------- ledger (READ-ONLY) ----------
    rows = [json.loads(l) for l in open(LEDGER)]
    assert all(r["cycle_id"] == "NFL-WINPROB-NG-SCORED-V1" for r in rows)
    games = {}
    for r in rows:
        games.setdefault(r["game_id"], []).append(r)

    # census: per arm per week
    census = {}
    for r in rows:
        wk = r["game_id"].split("_")[1]
        census.setdefault((r["arm_id"], wk), 0)
        census[(r["arm_id"], wk)] += 1
    print("CENSUS per arm per week:", {f"{a}_w{w}": n for (a, w), n in sorted(census.items())})

    # ---------- snapshot join ----------
    with open(f"{DATA}/games.csv") as f:
        snap = {r["game_id"]: r for r in csv.DictReader(f)}

    join_rows = []
    n_final = n_pending = n_missing = n_ambiguous = 0
    final_rows = []
    anomalies = []

    for gid in sorted(games):
        lrows = {r["arm_id"]: r for r in games[gid]}
        s = snap.get(gid)
        if s is None:
            n_missing += 1
            anomalies.append({"game_id": gid, "issue": "missing_snapshot_row",
                              "classification": "NOT_RUN_JOIN_FAILURE"})
            status = "NOT_RUN_JOIN_FAILURE"
            outcome = None
        else:
            a_sc, h_sc = parse_score(s["away_score"]), parse_score(s["home_score"])
            if a_sc is None and h_sc is None:
                status = "PENDING_NOT_FINAL"
                outcome = None
                n_pending += 1
            elif a_sc is not None and h_sc is not None and \
                    str(s.get("result", "")).strip() != "" and str(s.get("total", "")).strip() != "":
                # strict FINAL: both integer scores + derived result/total present
                status = "FINAL"
                outcome = 1 if h_sc > a_sc else (0 if h_sc < a_sc else None)
                n_final += 1
                if outcome is None:  # tie — not decidable for binary home outcome
                    anomalies.append({"game_id": gid, "issue": "tie_score",
                                      "classification": "NOT_RUN_STATUS_AMBIGUOUS"})
                    n_ambiguous += 1
            else:
                # mixed/partial state — refuse to guess
                status = "NOT_RUN_STATUS_AMBIGUOUS"
                outcome = None
                n_ambiguous += 1
                anomalies.append({"game_id": gid,
                                  "issue": f"partial score state away={s['away_score']!r} home={s['home_score']!r} result={s.get('result')!r}",
                                  "classification": "NOT_RUN_STATUS_AMBIGUOUS"})

        # sanity: ledger home/away identity vs snapshot
        ident_ok = None
        if s is not None:
            ident_ok = (s["home_team"] == lrows["B0"]["home_team"]
                        and s["away_team"] == lrows["B0"]["away_team"])
            if not ident_ok:
                anomalies.append({"game_id": gid, "issue": "home/away identity mismatch ledger vs snapshot",
                                  "classification": "ANOMALY_IDENTITY"})

        join_rows.append({
            "game_id": gid,
            "week": gid.split("_")[1],
            "season": lrows["B0"]["season"],
            "home_team": lrows["B0"]["home_team"],
            "away_team": lrows["B0"]["away_team"],
            "kickoff_utc_ledger": lrows["B0"]["kickoff_utc"],
            "gameday_snapshot": (s or {}).get("gameday", ""),
            "gametime_snapshot_local": (s or {}).get("gametime", ""),
            "status": status,
            "away_score": (s or {}).get("away_score", ""),
            "home_score": (s or {}).get("home_score", ""),
            "outcome_home_win": "" if outcome is None else outcome,
            "p_home_B0": lrows["B0"]["p_home"],
            "p_home_B1_STAR": lrows["B1_STAR"]["p_home"],
            "p_home_C3": lrows["C3"]["p_home"],
            "identity_ok": "" if ident_ok is None else str(ident_ok),
        })
        if status == "FINAL" and outcome is not None:
            final_rows.append((gid, outcome, join_rows[-1]))

    # ---------- descriptive metrics on FINAL set ----------
    metrics = {}
    for arm in ARMS:
        lls, briers, hits = [], [], []
        for gid, y, jr in final_rows:
            p = float(jr[f"p_home_{arm}"])
            eps = 1e-15
            p_c = min(max(p, eps), 1 - eps)
            lls.append(-(y * math.log(p_c) + (1 - y) * math.log(1 - p_c)))
            briers.append((p - y) ** 2)
            hits.append(1.0 if (p > 0.5) == bool(y) else 0.0)
        n = len(final_rows)
        metrics[arm] = {
            "n": n,
            "log_loss_mean": sum(lls) / n if n else None,
            "brier_mean": sum(briers) / n if n else None,
            "argmax_accuracy": sum(hits) / n if n else None,
            "sum_log_loss": sum(lls) if n else None,
            "sum_brier": sum(briers) if n else None,
        }

    print("STATUS COUNTS:", {"FINAL": n_final, "PENDING_NOT_FINAL": n_pending,
                             "NOT_RUN_JOIN_FAILURE": n_missing,
                             "NOT_RUN_STATUS_AMBIGUOUS": n_ambiguous})
    print("FINAL TABLE:")
    for gid, y, jr in final_rows:
        print(" ", gid, "outcome_home_win=", y, jr)
    print("METRICS:", json.dumps(metrics, indent=2))
    print("ANOMALIES:", anomalies)

    # ---------- write joined CSVs ----------
    cols = list(join_rows[0].keys())
    for dest in (DATA, STAGING):
        os.makedirs(dest, exist_ok=True)
        with open(f"{dest}/joined_monitor_20261009.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(join_rows)

    results = {
        "provenance": prov,
        "census": {f"{a}_w{w}": n for (a, w), n in sorted(census.items())},
        "status_counts": {"FINAL": n_final, "PENDING_NOT_FINAL": n_pending,
                          "NOT_RUN_JOIN_FAILURE": n_missing,
                          "NOT_RUN_STATUS_AMBIGUOUS": n_ambiguous},
        "final_games": [{"game_id": gid, "outcome_home_win": y,
                         "away_score": jr["away_score"], "home_score": jr["home_score"]}
                        for gid, y, jr in final_rows],
        "metrics": metrics,
        "anomalies": anomalies,
    }
    with open(f"{DATA}/monitor_results_20261009.json", "w") as f:
        json.dump(results, f, indent=2)
    print("WROTE joined CSVs to", DATA, "and", STAGING)


if __name__ == "__main__":
    main()
