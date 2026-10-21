"""NCAA fixtures/results adapter (PAPERDESK-FIXALL-NCAA-V1 W5.2).

ESPN college-basketball public scoreboard is BOTH the fixture source and
the results source for the two NCAA lanes (NCAA-M / NCAA-W — two lanes,
never one). Identity law (the W0.1 lesson, applied from day one): team
identity is the ESPN `displayName` run through `team_names.norm` equality
in every comparison; the ESPN team id travels with every row as the stable
state-store key; names are NEVER compared raw.

Conference law: the feed's `conferenceCompetition` flag is the conf_game
signal; when the flag is absent the feature is 0.0 AND the row records
`conference_unknown: true` (honest feature gap — never guessed).
Neutral law: `venue.neutralSite` when present, else False; the frozen
feature `neutral` and the HFA/H_PTS laws read exactly this value.
"""
from __future__ import annotations

import hashlib
import json
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ESPN_CB_BASE = ("https://site.api.espn.com/apis/site/v2/sports/basketball/"
                "{path}/scoreboard?dates={day}")
ESPN_LEAGUE_PATH = {"NCAA-M": "mens-college-basketball",
                    "NCAA-W": "womens-college-basketball"}
NOW_FMT = "%Y-%m-%dT%H:%M:%SZ"


def et_local_date(tip: datetime) -> str:
    # US/Eastern calendar date (the dossier §6.3 tz law); fixed 5h offset is
    # wrong across DST — use the same zoneinfo path as the exec adapters.
    from zoneinfo import ZoneInfo
    return tip.astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")


NCAA_LEAGUE_MODEL = {
    "model_id": "NCAA_FROZEN_V1",
    "constants": {"K": 20.0, "HFA": 65.0, "REGRESS": 0.25, "L0": 70.0,
                  "H_PTS": 3.2, "A_EFF": 0.06},
    "outcomes": ["HOME", "AWAY"],
    "disclosure": ("PREDICTION-PAPER lane (owner QD3): the audited frozen "
                   "model (ncaa_intake, CONFIRMED on the prediction test, "
                   "6/6 seasons) has NO proven money edge — men LOST to the "
                   "closing line in the money test; women untested. The "
                   "dashboard truth label is mandatory (W5.5)."),
    "forecast_gate": ("PAPERDESK-FIXALL-NCAA-V1 W5; state store + pinned "
                      "GBM artifact per season; frozen constants "
                      "NEVER re-tuned"),
}


def register_ncaa_league_law(core, league: str) -> None:
    """In-memory LEAGUE_MODELS registration (the WSL adapter pattern,
    idempotent, conflict-refusing) — the pinned package bytes are NEVER
    touched."""
    spec = {**NCAA_LEAGUE_MODEL}
    existing = core.LEAGUE_MODELS.get(league)
    if existing is not None and existing != spec:
        raise ValueError(f"NCAA league law conflict for {league}")
    core.LEAGUE_MODELS[league] = spec


def fetch_scoreboard(league: str, day: str) -> tuple[dict, bytes]:
    path = ESPN_LEAGUE_PATH[league]
    url = ESPN_CB_BASE.format(path=path, day=day.replace("-", ""))
    req = urllib.request.Request(url, headers={"User-Agent":
                                               "research/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        body = r.read()
    return json.loads(body), body


def _parse_teams(league: str, ev: dict, payload_sha: str) -> dict | None:
    comps = ev.get("competitions") or []
    if not comps:
        return None
    comp = comps[0]
    competitors = comp.get("competitors") or []
    if len(competitors) != 2:
        return None
    by_side = {c.get("homeAway"): c for c in competitors}
    home, away = by_side.get("home"), by_side.get("away")
    if not home or not away:
        return None
    ht, at = home.get("team") or {}, away.get("team") or {}
    tip = str(ev.get("date") or "").replace("Z", "Z")
    try:
        tip_dt = datetime.strptime(tip[:19], "%Y-%m-%dT%H:%M:%S")\
            .replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    neutral = bool(((comp.get("venue") or {}).get("neutralSite")))
    conference_competition = comp.get("conferenceCompetition")
    season = (ev.get("season") or {})
    game = {
        "league": league, "match_id": str(ev.get("id")),
        "season": season.get("year"),
        "season_type": season.get("type"),
        "tournament_id": (comp.get("tournament") or {}).get("id"),
        "home_id": str(ht.get("id")), "away_id": str(at.get("id")),
        "home": ht.get("displayName") or ht.get("name"),
        "away": at.get("displayName") or at.get("name"),
        "kickoff_utc": tip_dt.strftime(NOW_FMT),
        "date": tip_dt.strftime("%Y-%m-%d"),
        "neutral_site": neutral,
        # conference law: flag known or honestly unknown
        "home_conference_id": (ht.get("conferenceId") or None)
        if not isinstance(conference_competition, bool)
        else ("SAME" if conference_competition else "DIFF"),
        "away_conference_id": (at.get("conferenceId") or None)
        if not isinstance(conference_competition, bool)
        else ("SAME" if conference_competition else "DIFF"),
        "conference_unknown": not isinstance(conference_competition, bool)
        and not (ht.get("conferenceId") and at.get("conferenceId")),
        "conf_game_flag": conference_competition,
        "state": str(((comp.get("status") or {}).get("type") or {})
                     .get("state", "")),
        "completed": bool(((comp.get("status") or {}).get("type") or {})
                          .get("completed")),
        "home_score": home.get("score"),
        "away_score": away.get("score"),
        "source_ref": (f"espn_cb_scoreboard league={league} "
                       f"payload_sha={payload_sha[:16]} "
                       f"event={ev.get('id')}"),
    }
    if game["home_conference_id"] == "SAME":
        game["away_conference_id"] = "SAME"
    return game


def games_from_payload(league: str, payload: dict, body: bytes) -> list[dict]:
    sha = hashlib.sha256(body).hexdigest()
    out = []
    for ev in payload.get("events", []):
        g = _parse_teams(league, ev, sha)
        if g is not None:
            out.append(g)
    return out


def completed_games(games: list[dict]) -> list[dict]:
    """Scored rows for the state store (FINAL only; ints coerced)."""
    rows = []
    for g in games:
        if not g.get("completed"):
            continue
        try:
            g = {**g, "home_score": int(g["home_score"]),
                 "away_score": int(g["away_score"])}
        except (TypeError, ValueError):
            continue
        rows.append(g)
    return rows


def upcoming_fixtures(games: list[dict], day: str):
    """Fixture-shaped rows for the desk (scheduled games of `day`)."""
    from research.papertrade_exec.adapters import Fixture
    out = []
    for g in games:
        if g["kickoff_utc"][:10] != day:
            continue
        if g["completed"] or "TBD" in (g["home"], g["away"]):
            continue
        stage = "NCAA_TOURNAMENT" if (g.get("tournament_id") or
                                      (g.get("season_type") not in
                                       (None, 2, "2"))) else "NCAA_REGULAR"
        out.append(Fixture(
            league=g["league"], match_id=g["match_id"],
            home=g["home"], away=g["away"],
            kickoff_utc=g["kickoff_utc"], competition=stage,
            et_local_date=et_local_date(datetime.strptime(
                g["kickoff_utc"], NOW_FMT)),
            source_ref=g["source_ref"],
            note=json.dumps({"neutral": g["neutral_site"],
                             "conf_game_flag": g.get("conf_game_flag"),
                             "conference_unknown":
                                 g.get("conference_unknown"),
                             "season": g.get("season"),
                             "season_type": g.get("season_type"),
                             "home_id": g["home_id"],
                             "away_id": g["away_id"],
                             "home_conference_id":
                                 g.get("home_conference_id"),
                             "away_conference_id":
                                 g.get("away_conference_id"),
                             "date": g["kickoff_utc"][:10]})))
    out.sort(key=lambda x: (x.kickoff_utc, x.match_id))
    return out
