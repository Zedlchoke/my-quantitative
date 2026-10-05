"""T2c — clean targeted cross-check: BDL vs hoopR (co-owner-reviewed protocol).

Budget: ≤6 requests, ≤5/min (13s interval), $0. No bulk download.
Key from Keychain at runtime; never in this file, stdout beyond PRESENT/ABSENT,
logs, or artifacts. Responses inspected in-memory; only sanitized aggregates saved.

Protocol (per co-owner):
- Pick 5 finished hoopR games from widely-separated seasons
- Query BDL by dates[]=<local_date> (array syntax, 1 req per game)
- Match on: date + home team identity + away team identity + score + tip UTC
- No guessing IDs or years — BDL season derived from hoopR ending-year − 1
  (verified from docs: "season" param = starting year)
"""
from __future__ import annotations
import csv, datetime as dt, json, sys, time, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bdl_adapter import BDLClient, BDLKeyUnavailable

HOOPR_DIR = Path.home() / ".my-quantitative-data/nba-hoopr-v1/raw"
OUT = Path(__file__).parent / "BDL_T2C_CROSSCHECK.json"
MAX_REQ = 6
INTERVAL = 13.0

# BDL team names may differ slightly from ESPN display names
TEAM_NAME_MAP = {
    "Portland Trail Blazers": "Portland Trail Blazers",
    "LA Clippers": "LA Clippers", "Los Angeles Clippers": "LA Clippers",
    "New Orleans Pelicans": "New Orleans Pelicans",
    "Oklahoma City Thunder": "Oklahoma City Thunder",
    "Golden State Warriors": "Golden State Warriors",
    "Washington Wizards": "Washington Wizards",
    "Charlotte Hornets": "Charlotte Hornets",
    "Sacramento Kings": "Sacramento Kings",
    "San Antonio Spurs": "San Antonio Spurs",
}

def normalize_team(name: str) -> str:
    if not name:
        return ""
    name = name.strip()
    for k, v in TEAM_NAME_MAP.items():
        if name.lower() == k.lower():
            return v
    return name

def pick_targets(n=5):
    """Pick n finished games from widely-separated hoopR seasons."""
    by_season = {}
    for f in sorted(HOOPR_DIR.glob("nba_schedule_*.csv")):
        for r in csv.DictReader(open(f, newline="", encoding="utf-8")):
            if (r.get("status_type_state") == "post"
                and r.get("home_score") and r.get("away_score")
                and r.get("game_date") and r.get("home_display_name")
                and r.get("away_display_name")):
                season = int(r["season"])
                by_season.setdefault(season, []).append(r)
    # pick from evenly-spaced seasons
    seasons = sorted(by_season.keys())
    if not seasons:
        return []
    step = max(1, len(seasons) // n)
    picked = []
    for i in range(0, len(seasons), step):
        s = seasons[i]
        games = by_season[s]
        # pick middle-of-season game
        g = games[len(games) // 2]
        picked.append({
            "hoopr_season_ending": s,
            "bdl_season_starting": s - 1,
            "game_date_local": g["game_date"],
            "home": normalize_team(g["home_display_name"]),
            "away": normalize_team(g["away_display_name"]),
            "home_score": int(g["home_score"]),
            "away_score": int(g["away_score"]),
            "tip_utc": g.get("date"),  # UTC timestamp from hoopR
            "hoopr_home_abbr": g.get("home_abbreviation"),
            "hoopr_away_abbr": g.get("away_abbreviation"),
        })
        if len(picked) >= n:
            break
    return picked

def main() -> int:
    report = {"schema": "bdl_t2c_crosscheck@1",
              "ran_at_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
              "budget": {"max_requests": MAX_REQ, "interval_s": INTERVAL},
              "requests_made": 0, "targets": [], "results": [], "summary": {}}
    try:
        c = BDLClient()
    except BDLKeyUnavailable:
        report["summary"] = {"verdict": "NOT_RUN_KEY_NOT_LOADED"}
        OUT.write_text(json.dumps(report, indent=1))
        print("NOT_RUN: key not in runtime")
        return 3

    targets = pick_targets(5)
    report["targets"] = targets
    report["summary"]["n_targets"] = len(targets)

    for i, t in enumerate(targets):
        if report["requests_made"] >= MAX_REQ:
            report["summary"]["note"] = f"budget cap {MAX_REQ} reached at target {i+1}"
            break
        if i > 0:
            time.sleep(INTERVAL)
        try:
            # Use dates[] array syntax for targeted single-date lookup
            url = f"{c.base}/games?dates[]={t['game_date_local']}"
            req = urllib.request.Request(url, headers={"Authorization": c._key})
            report["requests_made"] += 1
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
            games = data.get("data", [])
            entry = dict(t)
            entry["bdl_http"] = "200"
            entry["bdl_games_on_date"] = len(games)

            # Match: same date + home team + away team (by normalized name)
            match = None
            for g in games:
                bdl_home = normalize_team((g.get("home_team") or {}).get("full_name", ""))
                bdl_away = normalize_team((g.get("visitor_team") or g.get("away_team") or {}).get("full_name", ""))
                if bdl_home == t["home"] and bdl_away == t["away"]:
                    match = g
                    break

            if match:
                bdl_hs = match.get("home_team_score")
                bdl_as = match.get("visitor_team_score") or match.get("away_team_score")
                bdl_dt = match.get("datetime")
                entry["bdl_match"] = "MATCHED by home+away identity"
                entry["bdl_home_score"] = bdl_hs
                entry["bdl_away_score"] = bdl_as
                entry["bdl_datetime_utc"] = bdl_dt
                # Compare
                checks = {
                    "date": match.get("date") == t["game_date_local"],
                    "home_team": True,  # already matched above
                    "away_team": True,
                    "score": bdl_hs == t["home_score"] and bdl_as == t["away_score"],
                }
                if bdl_dt and t["tip_utc"]:
                    # BDL gives ISO-UTC; hoopR gives UTC with Z suffix
                    bdl_ts = bdl_dt.replace("Z", "+00:00") if bdl_dt.endswith("Z") else bdl_dt
                    hoop_ts = t["tip_utc"].replace("Z", "+00:00") if t["tip_utc"].endswith("Z") else t["tip_utc"]
                    try:
                        checks["tip_utc"] = abs((dt.datetime.fromisoformat(bdl_ts) -
                                                 dt.datetime.fromisoformat(hoop_ts)).total_seconds()) < 60
                    except (ValueError, TypeError):
                        checks["tip_utc"] = "PARSE_FAIL"
                else:
                    checks["tip_utc"] = "MISSING_DATA"
                entry["checks"] = checks
                entry["verdict"] = "MATCH" if all(v is True for v in checks.values()) else (
                    "PARTIAL_MATCH" if checks["date"] and checks["home_team"] else "MISMATCH")
            else:
                entry["bdl_match"] = "NOT_FOUND on this date"
                entry["verdict"] = "UNMATCHED"
                entry["bdl_teams_on_date"] = [
                    f"{(g.get('home_team') or {}).get('full_name','?')} vs "
                    f"{(g.get('visitor_team') or {}).get('full_name','?')}" for g in games[:5]]
            report["results"].append(entry)
        except Exception as e:
            report["requests_made"] += 1
            report["results"].append({**t, "bdl_http": "ERROR", "error": str(e)[:150], "verdict": "ERROR"})

    verdicts = [r.get("verdict") for r in report["results"]]
    report["summary"].update({
        "match": verdicts.count("MATCH"),
        "partial": verdicts.count("PARTIAL_MATCH"),
        "mismatch": verdicts.count("MISMATCH"),
        "unmatched": verdicts.count("UNMATCHED"),
        "error": verdicts.count("ERROR"),
        "requests_consumed": report["requests_made"],
    })
    OUT.write_text(json.dumps(report, indent=1))
    print(json.dumps(report["summary"], indent=1))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
