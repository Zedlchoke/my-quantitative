"""AI research tools (PAPERDESK-FIXALL-NCAA-V1 W4.3; enriched U5).

Before an ALLOW is lawful the AI layer must have ACTUALLY gathered
evidence: news/heads-ups for both teams (48h window), each source stored
as a citation (url + fetched_at_utc + excerpt). Zero sources is a LAWFUL
refusal reason ("insufficient evidence") — never silently an approval.

SOURCES (allow-list, read-only public GETs, no keys):
  * ESPN news API for the fixture's sport: recent headlines naming either
    team (injury/lineup/rota items surface there), each with a link and a
    published timestamp — U5: a headline naming a FIRST+LAST player name
    from either team's roster also passes, even without the team name;
  * the fixture's own league scoreboard record(s) — U5: fetched for the
    MATCH's kickoff date AND (when different) today's board, so a T-6h
    decision for tomorrow's match has a real status source. Every board
    fetch is journaled; a board without the event is journaled honestly
    as a query with zero sources, never invented;
  * U5: per-team injuries from the ESPN CORE API team injuries endpoint
    (keyless JSON): https://sports.core.api.espn.com/v2/sports/{sport}/
    leagues/{slug}/teams/{team_id}/injuries — each injury entry becomes a
    citation; a 404 is journaled as a zero-source query, never invented.
Everything else is refused by the allow-list — the model cannot invent
URLs into the citation record (the gate drops uncited claims).

All transport goes through _get_json (tests stub it; no real network in
the battery). The closed allow-list law is unchanged: the model may only
cite captured URLs — enforced upstream by the U0 citation filter.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ESPN_SITE_API = "https://site.web.api.espn.com/apis/site/v2/sports"
ESPN_SITE_BOARD = "https://site.api.espn.com/apis/site/v2/sports"
ESPN_CORE_API = "https://sports.core.api.espn.com/v2"

SPORT_PATH = {"NBA": "basketball/nba", "WNBA": "basketball/wnba",
              "SOCCER": "soccer", "WSL": "soccer",
              "NCAA-M": "basketball/mens-college-basketball",
              "NCAA-W": "basketball/womens-college-basketball"}
NEWS_WINDOW_H = 48

# U5: roster names are fetched ONCE per (league, team_id, day) — module
# cache, keyed exactly that way. Value: tuple of normalized "firstlast"
# full names (first+last only). Errors are cached too (the once-per-day
# cap is strict; a failed fetch is not retried the same day).
_ROSTER_CACHE: dict = {}

# U5 wiring (integrator): scoreboard boards are cached per (path, day) for
# the process lifetime — the team-id lookup and the status fetch share ONE
# GET per board (the evidence journal records which). Errors are cached as
# None so a failing board is not re-dialed.
_BOARD_CACHE: dict = {}


def _get_json(url: str, timeout: int = 15) -> dict:
    req = urllib.request.Request(url, headers={
        "Accept": "application/json", "User-Agent": "PaperDesk-research/1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _norm(s: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "", str(s).casefold())


def _hit(name: str, text: str) -> bool:
    n = _norm(name)
    return bool(n) and n in _norm(text)


def _team_ids_of(team_ids) -> list[str]:
    """Accept {'home': id, 'away': id} or a 2-sequence (home, away)."""
    if isinstance(team_ids, dict):
        return [str(team_ids.get("home") or ""), str(team_ids.get("away") or "")]
    if isinstance(team_ids, (list, tuple)):
        vals = list(team_ids)[:2]
        return [str(vals[0]) if len(vals) > 0 else "",
                str(vals[1]) if len(vals) > 1 else ""]
    return ["", ""]


def _roster_full_names(league: str, path: str, team_id: str,
                       fetched_at: datetime, queries: list) -> tuple:
    """Normalized 'firstlast' full names for one team (roster endpoint),
    fetched at most once per (league, team_id, day) via the module cache.
    Returns (names_tuple, error_str_or_None)."""
    day = fetched_at.strftime("%Y%m%d")
    key = (league, str(team_id), day)
    url = (f"{ESPN_SITE_API}/{path}/teams/{team_id}/roster")
    if key in _ROSTER_CACHE:
        names, err = _ROSTER_CACHE[key]
        queries.append(f"site {path}/teams/{team_id}/roster day={day} "
                       f"cache=hit")
        return names, err
    names, err = (), None
    try:
        payload = _get_json(url)
        team = payload.get("team") if isinstance(payload.get("team"), dict) \
            else payload
        for a in (team.get("athletes") or []):
            if not isinstance(a, dict):
                continue
            full = str(a.get("displayName") or a.get("fullName") or
                       " ".join(str(a.get(k) or "") for k in
                                ("firstName", "lastName"))).strip()
            n = _norm(full)
            if " " in full.strip() or (a.get("firstName") and
                                       a.get("lastName")):
                if n and n not in names:
                    names += (n,)
        queries.append(f"site {path}/teams/{team_id}/roster day={day} "
                       f"cache=miss athletes={len(names)}")
    except Exception as e:                     # honest: cache the failure
        err = f"{type(e).__name__}: {e}"
        queries.append(f"site {path}/teams/{team_id}/roster day={day} "
                       f"cache=miss ERROR {err[:200]}")
    _ROSTER_CACHE[key] = (names, err)
    return names, err


def _roster_hit(text: str, roster_names) -> bool:
    t = _norm(text)
    return any(n and n in t for n in (roster_names or ()))


def _board_date(kickoff_utc) -> str | None:
    """'YYYYMMDD' board-date for an ISO kickoff (Z or offset); None on
    unparsable input (never guessed)."""
    if not kickoff_utc:
        return None
    try:
        dt = datetime.fromisoformat(str(kickoff_utc).replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).strftime("%Y%m%d")
    except (ValueError, TypeError):
        return None


def _board_payload(path: str, day: str) -> dict | None:
    """Cached scoreboard GET (one fetch per (path, day) per process; a
    failed fetch is cached as None and never re-dialed)."""
    key = (path, str(day))
    if key in _BOARD_CACHE:
        return _BOARD_CACHE[key]
    payload = None
    try:
        payload = _get_json(
            f"{ESPN_SITE_BOARD}/{path}/scoreboard?dates={day}")
    except Exception:
        payload = None
    _BOARD_CACHE[key] = payload
    return payload


def lookup_team_ids(*, league: str, match_id: str,
                    kickoff_utc: str | None = None) -> dict | None:
    """U5 wiring: ESPN team ids for one fixture, looked up on the MATCH's
    kickoff-date board by event id (the SAME board the status layer uses —
    one shared GET via the cache). Returns {'home': id, 'away': id} or
    None (unknown league, unparsable kickoff, event absent, or the board
    carrying no resolvable competitor pair) — ids are NEVER invented."""
    path = SPORT_PATH.get(league)
    day = _board_date(kickoff_utc)
    if not path or not day:
        return None
    board = _board_payload(path, day)
    if not isinstance(board, dict):
        return None
    for ev in board.get("events", []):
        if str(ev.get("id")) != str(match_id):
            continue
        comp = (ev.get("competitions") or [{}])[0]
        ids: dict = {}
        for c in comp.get("competitors") or []:
            if not isinstance(c, dict):
                continue
            side, tid = c.get("homeAway"), (c.get("team") or {}).get("id")
            if side in ("home", "away") and tid is not None:
                ids[side] = str(tid)
        return ids if ("home" in ids and "away" in ids) else None
    return None


def _injuries_url(path: str, team_id: str) -> str | None:
    """U5 injuries endpoint (core API, keyless). Needs a two-part site
    path (sport/slug); 'soccer' alone has no league slug, so no URL is
    invented — the caller journals the skip honestly instead."""
    parts = path.split("/")
    if len(parts) != 2 or not team_id:
        return None
    sport, slug = parts
    return (f"{ESPN_CORE_API}/sports/{sport}/leagues/{slug}"
            f"/teams/{team_id}/injuries")


def _injury_sources(url: str, payload: dict, fetched_at: datetime) -> list:
    """Each injury item -> one citation {url, fetched_at_utc, excerpt,
    published_utc, kind: 'injuries'}. Items that carry no readable text
    (pure $ref shapes) are skipped — never invented."""
    out = []
    for i, item in enumerate(payload.get("items") or []):
        if not isinstance(item, dict):
            continue
        athlete = item.get("athlete") if isinstance(item.get("athlete"),
                                                    dict) else {}
        name = str(athlete.get("displayName") or athlete.get("fullName")
                   or "").strip()
        status = item.get("status") if isinstance(item.get("status"),
                                                  dict) else {}
        stext = str(status.get("type") or status.get("description")
                    or "").strip()
        details = item.get("details") if isinstance(item.get("details"),
                                                    dict) else {}
        dtext = str(details.get("detail") or details.get("type")
                    or "").strip()
        excerpt = " — ".join(x for x in (name, stext, dtext) if x)
        if not excerpt:
            continue
        pub = str(item.get("lastUpdate") or "")[:19]
        out.append({
            "url": url,
            "fetched_at_utc": fetched_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "excerpt": excerpt[:280],
            "published_utc": (pub + "Z") if pub else "",
            "kind": "injuries"})
    return out


def collect_evidence_stats(sources_by_candidate: dict) -> dict:
    """U5: evidence-coverage stats over {candidate_key: [sources]}.
    Used for the before/after SIMULATED comparison of the roster-name
    news filter (handover) and for ongoing coverage monitoring."""
    items = list((sources_by_candidate or {}).items())
    n = len(items)
    with_src = sum(1 for _k, s in items if s)
    return {
        "candidates": n,
        "candidates_with_sources": with_src,
        "candidates_without_sources": n - with_src,
        "share_with_sources": round(with_src / n, 6) if n else 0.0,
        "total_sources": sum(len(s or []) for _k, s in items)}


def collect_evidence(*, league: str, match_id: str, home: str, away: str,
                     journal_dir: Path | None = None,
                     kickoff_utc: str | None = None,
                     team_ids=None) -> dict:
    """Gather allow-listed evidence for one fixture. Returns
    {queries: [...], sources: [{url, fetched_at_utc, excerpt,
    published_utc, kind}]} — the citations travel verbatim into the
    opinion record.

    U5 params (optional, callers wired by the integrator):
      kickoff_utc — ISO kickoff; the scoreboard is fetched for the MATCH
        date AND for today when the two differ;
      team_ids    — {'home': id, 'away': id} (or (home_id, away_id));
        enables the roster-name news filter and the per-team injuries
        source. Absent ids simply skip those layers — never invented.
    """
    fetched_at = datetime.now(timezone.utc)
    out: dict = {"league": league, "match_id": match_id,
                 "queries": [], "sources": []}
    path = SPORT_PATH.get(league)
    if not path:
        out["why"] = f"no research path for league {league}"
        return out

    home_id, away_id = _team_ids_of(team_ids)
    # U5 wiring (integrator): ids absent -> look them up on the MATCH's
    # kickoff-date board (shared cached GET with the status layer below).
    # A lookup that finds nothing keeps the layers honestly dormant.
    if not home_id or not away_id:
        looked = lookup_team_ids(league=league, match_id=match_id,
                                 kickoff_utc=kickoff_utc)
        if looked:
            home_id = looked.get("home") or home_id
            away_id = looked.get("away") or away_id
            out["team_ids_lookup"] = "kickoff_board"

    # 0) U5 rosters (at most one fetch per team per day; module cache) —
    #    feed the news filter with first+last player names.
    roster_names: tuple = ()
    for label, tid in (("home", home_id), ("away", away_id)):
        if not tid:
            continue
        names, err = _roster_full_names(league, path, tid, fetched_at,
                                        out["queries"])
        roster_names += names
        if err:
            out.setdefault("roster_errors", {})[label] = err

    # 1) league news feed, filtered to items naming either team OR a
    #    first+last roster player name, inside the 48h window (injury /
    #    lineup / roster news surface here — often naming only the player).
    try:
        news = _get_json(f"{ESPN_SITE_API}/{path}/news?limit=50")
        items = (news.get("articles") or news.get("headlines") or [])
        cutoff = fetched_at - timedelta(hours=NEWS_WINDOW_H)
        for it in items:
            ds = str(it.get("published") or it.get("lastModified") or "")
            try:
                pub = datetime.strptime(ds[:19], "%Y-%m-%dT%H:%M:%S")\
                    .replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            text = " ".join(str(it.get(k) or "") for k in
                            ("headline", "description"))
            if pub < cutoff:
                continue
            if not (_hit(home, text) or _hit(away, text)
                    or _roster_hit(text, roster_names)):
                continue
            link = ((it.get("links") or {}).get("web") or {})\
                .get("href") or ""
            if not link:
                continue
            out["sources"].append({
                "url": link, "fetched_at_utc": fetched_at
                .strftime("%Y-%m-%dT%H:%M:%SZ"),
                "excerpt": text[:280],
                "published_utc": ds[:19] + "Z",
                "kind": "news_48h"})
    except Exception as e:                     # network fail: honest empty
        out["news_error"] = f"{type(e).__name__}: {e}"
    out["queries"].append(f"{path}/news?limit=50 window=48h "
                          f"teams={home}|{away} "
                          f"roster_names={len(roster_names)}")

    # 2) U5 scoreboard status: the MATCH's kickoff-date board AND (when
    #    different) today's board. Every board fetch is journaled as a
    #    query; the event's status detail is the excerpt of each source.
    today = fetched_at.strftime("%Y%m%d")
    kick_day = _board_date(kickoff_utc)
    board_days = [d for d in (kick_day, today) if d]
    if kick_day is None and kickoff_utc:
        out["scoreboard_note"] = \
            f"kickoff_utc unparsable, fell back to today's board only"
    seen_days = []
    for day in board_days:
        if day in seen_days:
            continue
        seen_days.append(day)
        board_url = (f"{ESPN_SITE_BOARD}/{path}/scoreboard?dates={day}")
        try:
            board = _board_payload(path, day)   # cached; None on error
            if board is None:
                raise OSError("board fetch failed (cached)")
            found = None
            for ev in board.get("events", []):
                if str(ev.get("id")) == str(match_id):
                    comp = (ev.get("competitions") or [{}])[0]
                    found = str(((comp.get("status") or {})
                                 .get("type") or {}).get("detail", ""))[:280]
                    break
            if found is not None:
                out["sources"].append({
                    "url": f"{board_url}#event={match_id}",
                    "fetched_at_utc": fetched_at
                    .strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "excerpt": found,
                    "published_utc": "",
                    "kind": "scoreboard_status"})
            else:
                out.setdefault("scoreboard_notes", []).append(
                    f"dates={day}: event {match_id} absent from board "
                    f"(journaled, 0 sources)")
        except Exception as e:
            out.setdefault("scoreboard_notes", []).append(
                f"dates={day}: ERROR {type(e).__name__}: {e}"[:200])
        out["queries"].append(f"{path}/scoreboard?dates={day} "
                              f"event={match_id}")

    # 3) U5 per-team injuries (core API, keyless). One entry per injury
    #    item; a failed/absent endpoint is journaled as a zero-source
    #    query — never invented.
    for label, tid in (("home", home_id), ("away", away_id)):
        url = _injuries_url(path, tid) if tid else None
        if url is None:
            if tid:
                out.setdefault("injuries_notes", []).append(
                    f"{label}: no core injuries URL for path {path!r} "
                    f"(no league slug) — journaled, 0 sources")
            else:
                out.setdefault("injuries_notes", []).append(
                    f"{label}: no team_id provided by caller — skipped, "
                    f"0 sources")
            continue
        try:
            payload = _get_json(url)
            got = _injury_sources(url, payload, fetched_at)
            out["sources"].extend(got)
            out["queries"].append(
                f"core {url.split('/v2/', 1)[-1]} team={tid} "
                f"items={len(payload.get('items') or [])} "
                f"sources={len(got)}")
        except Exception as e:
            out.setdefault("injuries_errors", {})[label] = \
                f"{type(e).__name__}: {e}"[:200]
            out["queries"].append(
                f"core {url.split('/v2/', 1)[-1]} team={tid} ERROR "
                f"{type(e).__name__} (0 sources, never invented)")

    if journal_dir is not None:
        journal_dir = Path(journal_dir)
        journal_dir.mkdir(parents=True, exist_ok=True)
        stamp = fetched_at.strftime("%Y%m%dT%H%M%SZ")
        (journal_dir / f"evidence_{match_id}_{stamp}.json").write_text(
            json.dumps(out, indent=1, sort_keys=True))
    return out
