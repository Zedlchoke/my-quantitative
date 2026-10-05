"""Lane A (NBA-WINPROB-NG-PREP-V1) — BDL spot-sample cross-check vs hoopR.

Law (dispatch DISPATCH_A_DATA.md + plan):
- SPOT SAMPLE ONLY: <=25 matched games, >=5 seasons, must include 2016/2020/2026.
- Targeted dates[] queries; hard 5 req/min (>=13s spacing); $0; no bulk download.
- Key via bdl_adapter (env -> Keychain), value NEVER printed/stored anywhere.
- Every request URL-pattern recorded (Authorization header is not part of URL).
- Field-level verdict: date / home / away / score / tip_utc. Any mismatch is a
  data-contract BLOCKER candidate, never silently absorbed.

Redacted per-request summaries -> ~/.my-quantitative-data/nba-ng-prep-v1/bdl_spotcheck/
Aggregate report -> lanes/A_DATA/BDL_CROSSCHECK_A_DATA.json
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).parent))
from bdl_adapter import BDLClient, BDLKeyUnavailable

HOOPR = Path.home() / ".my-quantitative-data/nba-hoopr-v1/raw"
OUTDIR = Path.home() / ".my-quantitative-data/nba-ng-prep-v1/bdl_spotcheck"
OUTJSON = Path(__file__).parent / "BDL_CROSSCHECK_A_DATA.json"
OUTDIR.mkdir(parents=True, exist_ok=True)

MAX_REQ = 12
INTERVAL_S = 13.0
MAX_GAMES_TOTAL = 25
MAX_GAMES_PER_DATE = 2
TIP_TOL_S = 60.0

# hoopR abbreviation -> BDL abbreviation (measured divergences, run-2 diagnosis:
# NY/NO/WSH/GS/UTAH/SA differ; all other 24 franchises identical)
ABBR_MAP = {"NY": "NYK", "NO": "NOP", "WSH": "WAS", "WAS": "WAS",
            "GS": "GSW", "UTAH": "UTA", "SA": "SAS"}


def bdl_abbr(a: str) -> str:
    return ABBR_MAP.get(a, a)

SEASON_QUERY_DATES = {
    # season_file -> probe date (local), deterministic mid-winter pick made offline
    2016: "2015-12-18",
    2017: "2016-12-23",
    2018: "2017-12-22",
    2019: "2018-11-16",
    2020: "2019-12-20",
    2021: "2021-01-08",
    2022: "2021-12-18",
    2023: "2022-11-25",
    2024: "2023-12-18",
    2025: "2024-12-23",
    2026: "2025-12-20",
}


def load_hoopr() -> pd.DataFrame:
    frames = []
    for s in SEASON_QUERY_DATES:
        df = pd.read_csv(HOOPR / f"nba_schedule_{s}.csv", dtype=str, keep_default_na=False)
        df["season_file"] = s
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    df = df[df["status_type_completed"].str.lower() == "true"]
    df = df[~df["notes_headline"].str.lower().str.contains("all-star|rising stars", na=False)]
    return df


def main() -> int:
    report = {
        "schema": "bdl_crosscheck_a_data@1",
        "cycle": "NBA-WINPROB-NG-PREP-V1",
        "lane": "A_DATA",
        "ran_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "budget": {
            "max_requests": MAX_REQ, "min_interval_s": INTERVAL_S,
            "max_games_total": MAX_GAMES_TOTAL, "max_games_per_date": MAX_GAMES_PER_DATE,
            "tip_tolerance_s": TIP_TOL_S,
        },
        "requests": [],
        "games": [],
        "summary": {},
    }
    try:
        c = BDLClient()
    except BDLKeyUnavailable:
        report["summary"] = {"verdict": "NOT_RUN_BDL_CROSSCHECK", "reason": "key unavailable"}
        OUTJSON.write_text(json.dumps(report, indent=1))
        print("NOT_RUN_BDL_CROSSCHECK: key unavailable")
        return 3

    hoop = load_hoopr()
    n_games = 0
    for i, (season, qdate) in enumerate(sorted(SEASON_QUERY_DATES.items())):
        if i >= MAX_REQ or n_games >= MAX_GAMES_TOTAL:
            break
        if i > 0:
            time.sleep(INTERVAL_S)
        # NOTE: BDLClient.base already ends in "/v1" — path must NOT repeat it.
        url_pattern = f"/games?dates[]={qdate}"
        day = hoop[(hoop["season_file"] == season) & (hoop["game_date"] == qdate)]
        entry = {
            "season_file": season, "query_date": qdate, "url_pattern": url_pattern,
            "hoopr_games_on_date": int(len(day)),
        }
        try:
            req_t0 = time.time()
            import urllib.request
            req = urllib.request.Request(f"{c.base}{url_pattern}", headers={"Authorization": c._key})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
            games = data.get("data", [])
            entry["http"] = 200
            entry["latency_s"] = round(time.time() - req_t0, 2)
            entry["bdl_games_returned"] = int(len(games))
            # redacted per-request artifact (no key material; game summaries only)
            red = [
                {k: g.get(k) for k in ("id", "date", "datetime", "season", "status",
                                       "home_team_score", "visitor_team_score")}
                | {"home": (g.get("home_team") or {}).get("abbreviation"),
                   "visitor": (g.get("visitor_team") or {}).get("abbreviation")}
                for g in games
            ]
            (OUTDIR / f"resp_{season}_{qdate}.json").write_text(json.dumps(red, indent=1))

            taken = 0
            for _, r in day.sort_values("game_id").iterrows():
                if taken >= MAX_GAMES_PER_DATE or n_games >= MAX_GAMES_TOTAL:
                    break
                g = next(
                    (x for x in games
                     if (x.get("home_team") or {}).get("abbreviation") == bdl_abbr(r["home_abbreviation"])
                     and (x.get("visitor_team") or {}).get("abbreviation") == bdl_abbr(r["away_abbreviation"])),
                    None,
                )
                rec = {
                    "season_file": season,
                    "game_id_hoopr": r["game_id"],
                    "query_date": qdate,
                    "hoopr": {
                        "game_date_local": r["game_date"],
                        "home_abbr": r["home_abbreviation"], "away_abbr": r["away_abbreviation"],
                        "home_score": int(r["home_score"]), "away_score": int(r["away_score"]),
                        "tip_utc": pd.Timestamp(r["start_date"]).isoformat().replace("+00:00", "Z"),
                    },
                }
                if g is None:
                    rec["verdict"] = "UNMATCHED"
                    rec["bdl_id"] = None
                else:
                    bdl_dt = (g.get("datetime") or "")
                    checks = {
                        "date": (g.get("date") or "") == r["game_date"],
                        "home": True,
                        "away": True,
                        "score": (g.get("home_team_score") == int(r["home_score"])
                                  and g.get("visitor_team_score") == int(r["away_score"])),
                    }
                    try:
                        t_bdl = datetime.fromisoformat(bdl_dt.replace("Z", "+00:00"))
                        t_hr = pd.Timestamp(r["start_date"]).to_pydatetime()
                        checks["tip_utc"] = abs((t_bdl - t_hr).total_seconds()) <= TIP_TOL_S
                        rec["tip_delta_s"] = abs((t_bdl - t_hr).total_seconds())
                    except Exception:
                        checks["tip_utc"] = "PARSE_FAIL"
                    rec["bdl_id"] = g.get("id")
                    rec["bdl"] = {
                        "date": g.get("date"), "datetime_utc": bdl_dt,
                        "home_abbr": (g.get("home_team") or {}).get("abbreviation"),
                        "away_abbr": (g.get("visitor_team") or {}).get("abbreviation"),
                        "home_score": g.get("home_team_score"),
                        "away_score": g.get("visitor_team_score"),
                    }
                    rec["checks"] = checks
                    rec["verdict"] = "MATCH" if all(v is True for v in checks.values()) else "MISMATCH"
                    if rec["verdict"] == "MISMATCH":
                        rec["blocker_candidate"] = True
                report["games"].append(rec)
                n_games += 1
                taken += 1
        except Exception as e:
            entry["http"] = "ERROR"
            entry["error"] = str(e)[:200]
        report["requests"].append(entry)

    v = [g["verdict"] for g in report["games"]]
    report["summary"] = {
        "requests_made": len(report["requests"]),
        "games_checked": len(report["games"]),
        "seasons_covered": sorted({g["season_file"] for g in report["games"]}),
        "match": v.count("MATCH"),
        "mismatch": v.count("MISMATCH"),
        "unmatched": v.count("UNMATCHED"),
        "match_rate": round(v.count("MATCH") / len(v), 4) if v else None,
        "verdict": "PASS" if v and v.count("MISMATCH") == 0 else "BLOCKER_CANDIDATE",
    }
    OUTJSON.write_text(json.dumps(report, indent=1))
    print(json.dumps(report["summary"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
