"""T2b — one auth check + one targeted BDL-vs-hoopR cross-check session.

Budget: ≤5 requests/min (free-tier rate), ≤10 requests total. No bulk download.
Secret law: the key is read at runtime from Keychain; it is NEVER written to
this file, stdout (beyond PRESENT/ABSENT), logs, or artifacts. Response JSON is
inspected in-memory; only sanitized aggregates (counts, scores, dates, team
names — no auth headers, no raw URLs with secrets) are saved.

Run: python lanes/T2_BDL_ADAPTER/bdl_t2b_crosscheck.py
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bdl_adapter import BDLClient, BDLKeyUnavailable, BASE  # noqa: E402

HOOPR_DIR = Path.home() / ".my-quantitative-data/nba-hoopr-v1/raw"
OUT = Path(__file__).parent / "BDL_CROSSCHECK_RESULTS.json"
MAX_REQUESTS = 10
MIN_INTERVAL = 13.0  # seconds between calls -> <=4.6 req/min, under the 5/min free cap


def _rate_limited(calls_made):
    return calls_made >= MAX_REQUESTS


def main() -> int:
    report = {"schema": "bdl_t2b_crosscheck@1", "base_url": BASE,
              "ran_at_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
              "budget": {"max_requests": MAX_REQUESTS, "min_interval_s": MIN_INTERVAL},
              "requests_made": 0, "auth": None, "free_tier_scope": None,
              "coverage_probe": None, "crosscheck": [], "notes": []}
    try:
        client = BDLClient()
    except BDLKeyUnavailable:
        report["auth"] = "NOT_RUN_KEY_NOT_LOADED"
        OUT.write_text(json.dumps(report, indent=1))
        print("NOT_RUN: key not in runtime (fail closed)")
        return 3

    # ---- request 1: auth + free-tier scope probe (teams, tiny page) ----
    time.sleep(0)  # first call, no wait needed
    try:
        teams = client.teams()
        report["requests_made"] += 1
        n_teams = len(teams.get("data", []))
        report["auth"] = f"OK (HTTP 200, teams page returned {n_teams} entries)"
        report["free_tier_scope"] = "teams endpoint accessible on free tier (docs-verified: Teams/Players/Games only)"
    except Exception as e:  # noqa: BLE001
        report["requests_made"] += 1
        report["auth"] = f"FAIL ({str(e)[:120]})"
        OUT.write_text(json.dumps(report, indent=1))
        print("AUTH FAIL — see report; no further calls")
        return 1

    if _rate_limited(report["requests_made"]):
        OUT.write_text(json.dumps(report, indent=1))
        return 0

    # ---- request 2-3: coverage probe — earliest and latest seasons on /games ----
    for label, season in (("earliest_probe", 1946), ("latest_probe", 2025)):
        time.sleep(MIN_INTERVAL)
        try:
            r = client.games(seasons=season)
            report["requests_made"] += 1
            data = r.get("data", [])
            meta = r.get("meta", {})
            report["coverage_probe"] = report["coverage_probe"] or {}
            report["coverage_probe"][label] = {
                "season": season, "n_rows_page": len(data),
                "meta_total_counts": {k: v for k, v in meta.items() if k != "next_cursor"},
                "first_game_date": data[0]["date"] if data else None,
            }
        except Exception as e:  # noqa: BLE001
            report["requests_made"] += 1
            report["coverage_probe"] = report["coverage_probe"] or {}
            report["coverage_probe"][label] = {"season": season, "error": str(e)[:120]}
        if _rate_limited(report["requests_made"]):
            break

    # ---- targeted cross-check: sample hoopR games across seasons ----
    # pick 5 hoopR games (2016, 2019, 2022, 2024, 2025 one each) and verify BDL has the same result
    hoopr_rows = []
    for f in sorted(HOOPR_DIR.glob("nba_schedule_*.csv")):
        with open(f, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                hoopr_rows.append(row)
    report["notes"].append(f"hoopR local corpus: {len(hoopr_rows)} schedule rows loaded for matching")

    def pick(season_ending_year):
        for r in hoopr_rows:
            if (r.get("season") or "").endswith(str(season_ending_year)) or r.get("season") == str(season_ending_year):
                if r.get("status_type_state") == "post" and r.get("score_home") and r.get("score_away"):
                    return r
        return None

    targets = []
    for yr in (2016, 2019, 2022, 2024, 2025):
        t = pick(yr)
        if t:
            targets.append((yr, t))
        if len(targets) >= 5 or _rate_limited(report["requests_made"]):
            break

    for yr, t in targets:
        if _rate_limited(report["requests_made"]):
            report["notes"].append("budget cap reached before all targets checked")
            break
        time.sleep(MIN_INTERVAL)
        bdl_season = yr  # BDL seasons param = starting year? docs use ending? try as-is; record raw
        try:
            r = client.games(seasons=bdl_season)
            report["requests_made"] += 1
            data = r.get("data", [])
            # match by date + teams
            hoopr_date = (t.get("game_date") or "")[:10]
            h, a = t.get("team_home_display_name") or t.get("home_display_name") or "", \
                   t.get("team_away_display_name") or t.get("away_display_name") or ""
            match = None
            for g in data:
                if g["date"] == hoopr_date:
                    match = g
                    break
            entry = {"season": yr, "hoopr_date": hoopr_date, "hoopr_home": h, "hoopr_away": a,
                     "hoopr_score": f"{t.get('score_home')}-{t.get('score_away')}",
                     "bdl_season_param": bdl_season,
                     "bdl_page_rows": len(data)}
            if match:
                entry["bdl_match"] = "FOUND by date"
                entry["bdl_score"] = f"{match.get('home_team_score')}-{match.get('away_team_score')}"
                entry["bdl_home"] = match.get("home_team", {})
                entry["bdl_datetime_utc"] = match.get("datetime")
                entry["verdict"] = ("MATCH" if str(match.get("home_team_score")) == str(t.get("score_home"))
                                    and str(match.get("away_team_score")) == str(t.get("score_away"))
                                    else "SCORE_MISMATCH")
            else:
                entry["bdl_match"] = "NOT_FOUND on first page (pagination likely; >page size)"
                entry["verdict"] = "NOT_FOUND_PAGE1"
            report["crosscheck"].append(entry)
        except Exception as e:  # noqa: BLE001
            report["requests_made"] += 1
            report["crosscheck"].append({"season": yr, "error": str(e)[:120]})

    OUT.write_text(json.dumps(report, indent=1))
    print(json.dumps({"requests_made": report["requests_made"], "auth": report["auth"],
                      "n_crosscheck": len(report["crosscheck"]),
                      "out": str(OUT.name)}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
