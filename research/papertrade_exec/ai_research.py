"""AI research tools (PAPERDESK-FIXALL-NCAA-V1 W4.3; enriched U5; evidence-
collector fix cycle 2026-10-22, owner plan F1–F7).

Before an ALLOW is lawful the AI layer must have ACTUALLY gathered
evidence: news/heads-ups for both teams (48h window), each source stored
as a citation (url + fetched_at_utc + excerpt). Zero sources is a LAWFUL
refusal reason ("insufficient evidence") — never silently an approval.

SOURCES (allow-list, read-only public GETs, no keys):
  * ESPN news API for the fixture's sport: recent headlines naming either
    team (48h window), each with a link and a published timestamp;
  * the fixture's league scoreboard record(s). F4 (owner plan 2026-10-22):
    the board days are the ET date of kickoff PLUS its two adjacent days
    ([D-1, D, D+1] in America/New_York) — journaled per query; a board
    without the event is journaled honestly as a zero-source query, never
    invented;
  * per-team injuries from the ESPN CORE API team injuries endpoint. F2:
    an item that is a bare {"$ref": …} is RESOLVED with exactly ONE hop
    GET (hard cap 1; every hop journaled) and the resolved payload is
    mined for the citation; an unresolvable ref is journaled as a
    zero-source query, never invented;
  * F1: WSL addresses ESPN as "soccer/eng.w.1" (the generic "soccer" slug
    is dead: news 404 / board errors — DIAGNOSIS 2026-10-22), and the
    fixture is matched on the board by TEAM-NAME token match (the lane's
    FD-* match ids are NOT in ESPN's id space — id matching is kept only
    for lanes whose ids ARE ESPN ids, e.g. NBA/NCAA);
  * F3: the ROSTER layer is REMOVED (site roster returns athletes=0;
    ?season= param 0; core athletes 404; teams endpoint 0 — all live-
    checked 2026-10-22). The removal is journaled in every collection;
    the news filter runs on team names only;
  * F5: WSL self-captures exactly two extra hosts: the match's Polymarket
    GAMMA event page (https://gamma-api.polymarket.com/events?id=…,
    threaded by the caller from the ledger MARKET_QUOTE event_id) and the
    official league page (https://wslfootball.com/fixtures/). No other
    host is fetchable; every self-capture is journaled verbatim-shaped
    and a failure is an honest zero.
Everything else is refused by the allow-list — the model cannot invent
URLs into the citation record (the gate drops uncited claims).

All transport goes through _get_json/_get_text (tests stub them; no real
network in the battery). The closed allow-list law is unchanged: the
model may only cite captured URLs — enforced upstream by the U0 filter.
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
              "SOCCER": "soccer", "WSL": "soccer/eng.w.1",
              "NCAA-M": "basketball/mens-college-basketball",
              "NCAA-W": "basketball/womens-college-basketball"}
NEWS_WINDOW_H = 48

# F5 (owner plan 2026-10-22): the ONLY hosts the collector may self-capture
# beyond its internally-constructed ESPN endpoints — the match's Polymarket
# GAMMA event page and the official WSL league page. Exactly +2 hosts.
GAMMA_HOST = "gamma-api.polymarket.com"
_OFFICIAL_PAGE_BY_LEAGUE = {"WSL": "https://wslfootball.com/fixtures/"}
_EXTRA_ALLOWED_HOSTS = {GAMMA_HOST, "wslfootball.com"}
_PAGE_MAX_BYTES = 3_000_000

ROSTER_REMOVAL_NOTE = (
    "roster layer removed by COORDINATOR PLAN 2026-10-22 F3 (site roster "
    "returns athletes=0; ?season= param 0; core athletes 404; teams "
    "endpoint 0 — all live-checked); news filter runs on team names only")

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


def _get_text(url: str, *, timeout: int = 20,
              max_bytes: int = _PAGE_MAX_BYTES) -> str:
    """F5 self-capture transport: public https ONLY, host allow-listed to
    the F5 pair, byte-capped; cleaned of scripts/styles/tags by the
    free-research cleaner (imported — no cycle)."""
    p = urllib.parse.urlsplit(url)
    host = (p.hostname or "").lower()
    if p.scheme != "https" or host not in _EXTRA_ALLOWED_HOSTS:
        raise ValueError(f"host {host!r} outside the F5 allow-list")
    req = urllib.request.Request(url, headers={
        "User-Agent": "PaperDesk-research/1",
        "Accept": "text/html,application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read(max_bytes)
    from research.papertrade_exec.ai_free_research import clean_html
    text = clean_html(raw.decode("utf-8", "replace"), max_chars=200_000)
    if not text.strip():
        raise ValueError("page carried no readable text after cleaning")
    return text


def _norm(s: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "", str(s).casefold())


def _hit(name: str, text: str) -> bool:
    n = _norm(name)
    return bool(n) and n in _norm(text)


def _name_tokens(name: str) -> frozenset:
    """F1 name-matching tokens: lowercase words with the women-marker
    tokens (women/w/wfc) dropped, so 'Brighton & Hove Albion Women'
    matches the lane's 'Brighton & Hove Albion'."""
    stop = {"women", "w", "wfc"}
    import re
    words = re.findall(r"[a-z0-9]+", str(name).casefold())
    return frozenset(w for w in words if w not in stop)


def _names_match(a: str, b: str) -> bool:
    ta, tb = _name_tokens(a), _name_tokens(b)
    return bool(ta and tb) and (ta == tb or ta <= tb or tb <= ta)


def _event_competitors(event: dict) -> list[str]:
    comp = (event.get("competitions") or [{}])[0]
    out = []
    for c in comp.get("competitors") or []:
        if isinstance(c, dict):
            out.append(str((c.get("team") or {}).get("displayName") or ""))
    return out


def _find_event(board: dict, match_id: str,
                home: str | None = None,
                away: str | None = None):
    """F1: the fixture's event on one board — by ESPN event id when the
    match id IS an ESPN id (all-digits), otherwise by BOTH team names
    (token match after women-marker stripping). Returns (event, how) or
    (None, None); the caller journals `how`."""
    if str(match_id).isdigit():
        for ev in board.get("events", []):
            if str(ev.get("id")) == str(match_id):
                return ev, f"id={match_id}"
        return None, None
    if home and away:
        for ev in board.get("events", []):
            comps = _event_competitors(ev)
            if len(comps) != 2:
                continue
            if (_names_match(home, comps[0]) and
                    _names_match(away, comps[1])) or \
               (_names_match(home, comps[1]) and
                    _names_match(away, comps[0])):
                return ev, (f"names={home!r}|{away!r} -> "
                            f"event {ev.get('id')} "
                            f"({_event_competitors(ev)})")
    return None, None


def _team_ids_of(team_ids) -> list[str]:
    """Accept {'home': id, 'away': id} or a 2-sequence (home, away)."""
    if isinstance(team_ids, dict):
        return [str(team_ids.get("home") or ""), str(team_ids.get("away") or "")]
    if isinstance(team_ids, (list, tuple)):
        vals = list(team_ids)[:2]
        return [str(vals[0]) if len(vals) > 0 else "",
                str(vals[1]) if len(vals) > 1 else ""]
    return ["", ""]


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


def _board_days(kickoff_utc) -> tuple[list[str], str | None]:
    """F4 (owner plan 2026-10-22): the board days are the ET DATE of the
    kickoff plus its two adjacent days — [D-1, D, D+1] in
    America/New_York, deduplicated, oldest first. Returns
    (days, et_date_string|None)."""
    if not kickoff_utc:
        return [], None
    try:
        from zoneinfo import ZoneInfo
        dt = datetime.fromisoformat(str(kickoff_utc).replace("Z", "+00:00"))
        et = dt.astimezone(ZoneInfo("America/New_York")).date()
    except (ValueError, TypeError, OSError):
        legacy = _board_date(kickoff_utc)
        return ([legacy] if legacy else []), None
    days = sorted({(et + timedelta(offset)).strftime("%Y%m%d")
                   for offset in (-1, 0, 1)})
    today = et.strftime("%Y%m%d")
    # the MATCH day first (most likely to carry the event), then the
    # adjacent days as fallbacks (F4: tra ngày đấu + 2 ngày lân cận)
    ordered = [today] + [d for d in days if d != today]
    return ordered, et.strftime("%Y-%m-%d")


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
                    kickoff_utc: str | None = None,
                    home: str | None = None,
                    away: str | None = None) -> dict | None:
    """U5 wiring + F1/F4: ESPN team ids for one fixture, resolved on the
    F4 board days by EVENT ID when the match id is an ESPN id, otherwise
    by BOTH TEAM NAMES (FD-* lane ids are never ESPN ids). Returns
    {'home': id, 'away': id} or None (unknown league, unparsable
    kickoff, event absent, or the board carrying no resolvable
    competitor pair) — ids are NEVER invented."""
    path = SPORT_PATH.get(league)
    days, _et = _board_days(kickoff_utc)
    if not path or not days:
        return None
    for day in days:
        board = _board_payload(path, day)
        if not isinstance(board, dict):
            continue
        ev, _how = _find_event(board, match_id, home, away)
        if ev is None:
            continue
        comp = (ev.get("competitions") or [{}])[0]
        ids: dict = {}
        for c in comp.get("competitors") or []:
            if not isinstance(c, dict):
                continue
            side, tid = c.get("homeAway"), (c.get("team") or {}).get("id")
            if side in ("home", "away") and tid is not None:
                ids[side] = str(tid)
        if "home" in ids and "away" in ids:
            return ids
    return None


def _injuries_url(path: str, team_id: str) -> str | None:
    """U5 injuries endpoint (core API, keyless). Needs a two-part site
    path (sport/slug); a bare sport with no league slug has no URL — the
    caller journals the skip honestly instead."""
    parts = path.split("/")
    if len(parts) != 2 or not team_id:
        return None
    sport, slug = parts
    return (f"{ESPN_CORE_API}/sports/{sport}/leagues/{slug}"
            f"/teams/{team_id}/injuries")


def _resolve_injury_item(item: dict, queries: list,
                         fetched_at: datetime,
                         url: str) -> dict | None:
    """F2: ONE injury item -> a readable shape. A bare {"$ref": ...} is
    resolved with EXACTLY ONE hop GET (hard cap 1; the hop is journaled);
    an unresolvable ref returns None — journaled, never invented."""
    if not isinstance(item, dict):
        return None
    if item.get("$ref") and len(item) == 1:
        ref = str(item["$ref"]).split("?")[0]
        try:
            resolved = _get_json(ref)
            queries.append(f"core $ref hop (cap 1) -> {ref.rsplit('/', 1)[-1]}"
                           f" OK items_resolved=1")
            item = resolved if isinstance(resolved, dict) else {}
        except Exception as e:
            queries.append(f"core $ref hop (cap 1) -> "
                           f"{ref.rsplit('/', 1)[-1]} ERROR "
                           f"{type(e).__name__} (0 sources, never "
                           f"invented)")
            return None
    athlete = item.get("athlete") if isinstance(item.get("athlete"),
                                                dict) else {}
    name = str(athlete.get("displayName") or athlete.get("fullName")
               or "").strip()
    status = item.get("status")
    if isinstance(status, dict):                    # live shapes vary:
        stext = str(status.get("type") or status.get("description")
                    or "").strip()                  # dict {type: …}
    else:
        stext = str(status or "").strip()           # plain "Out"
    details = item.get("details") if isinstance(item.get("details"),
                                                dict) else {}
    dtext = str(details.get("detail") or details.get("type")
                or "").strip()
    short = str(item.get("shortComment") or "").strip()
    excerpt = short or " — ".join(x for x in (name, stext, dtext) if x)
    if not excerpt:
        return None
    pub = str(item.get("lastUpdate") or item.get("date") or "")[:19]
    return {
        "url": url,
        "fetched_at_utc": fetched_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "excerpt": excerpt[:280],
        "published_utc": (pub + "Z") if pub else "",
        "kind": "injuries"}


def _injury_sources(url: str, payload: dict, fetched_at: datetime,
                    queries: list) -> list:
    """Each injury item -> one citation {url, fetched_at_utc, excerpt,
    published_utc, kind: 'injuries'}; bare-$ref items are resolved with
    ONE hop (F2). Items that still carry no readable text are skipped —
    never invented."""
    out = []
    for item in payload.get("items") or []:
        src = _resolve_injury_item(item, queries, fetched_at, url)
        if src:
            out.append(src)
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


def _gamma_source(gamma_event_url: str | None, queries: list,
                  fetched_at: datetime) -> list:
    """F5: the match's Polymarket GAMMA event page — threaded by the
    caller (ledger MARKET_QUOTE event_id). Host-allow-listed; an absent
    URL or a failed fetch is an honest zero, never invented."""
    if not gamma_event_url:
        queries.append("gamma_event skipped: no gamma_event_url provided "
                       "by caller (0 sources, journaled)")
        return []
    try:
        p = urllib.parse.urlsplit(gamma_event_url)
        if p.scheme != "https" or (p.hostname or "").lower() != GAMMA_HOST:
            raise ValueError("host outside the F5 allow-list")
        env = _get_json(gamma_event_url)
        event = (env if isinstance(env, list) else [env] if
                 isinstance(env, dict) else [{}])[0] or {}
        title = str(event.get("title") or "")
        desc = str(event.get("description") or "")
        excerpt = " — ".join(x for x in (title, desc) if x)[:280]
        if not excerpt:
            raise ValueError("gamma event carried no readable text")
        queries.append(f"gamma_event OK id-in-url results=1")
        return [{"url": gamma_event_url, "fetched_at_utc":
                 fetched_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "excerpt": excerpt,
                 "published_utc": str(event.get("startDate") or "")[:19]
                 + ("Z" if event.get("startDate") else ""),
                 "kind": "gamma_event"}]
    except Exception as e:
        queries.append(f"gamma_event ERROR {type(e).__name__}: "
                       f"{str(e)[:120]} (0 sources, never invented)")
        return []


def _league_official_source(league: str, home: str, away: str,
                            queries: list, fetched_at: datetime) -> list:
    """F5: the official league page (WSL: wslfootball.com/fixtures/) —
    host-allow-listed; the excerpt is the window around the first team-
    name hit so the citation names the fixture. An absent mapping or an
    unreadable page is an honest zero."""
    page = _OFFICIAL_PAGE_BY_LEAGUE.get(league)
    if not page:
        return []
    try:
        text = _get_text(page)
        idx = -1
        for name in (home, away):
            if name:
                idx = _norm(text).find(_norm(name))
                if idx >= 0:
                    break
        excerpt = text[max(0, idx - 120): idx + 160].strip() if idx >= 0 \
            else text[:280]
        queries.append(f"league_official OK {page} chars={len(text)} "
                       f"team_name_hit={'yes' if idx >= 0 else 'no'}")
        return [{"url": page, "fetched_at_utc":
                 fetched_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "excerpt": excerpt[:280], "published_utc": "",
                 "kind": "league_official"}]
    except Exception as e:
        queries.append(f"league_official ERROR {type(e).__name__}: "
                       f"{str(e)[:120]} (0 sources, never invented)")
        return []


def collect_evidence(*, league: str, match_id: str, home: str, away: str,
                     journal_dir: Path | None = None,
                     kickoff_utc: str | None = None,
                     team_ids=None,
                     gamma_event_url: str | None = None) -> dict:
    """Gather allow-listed evidence for one fixture. Returns
    {queries: [...], sources: [{url, fetched_at_utc, excerpt,
    published_utc, kind}]} — the citations travel verbatim into the
    opinion record.

    Params:
      kickoff_utc — ISO kickoff; F4 board days = ET date ±1;
      team_ids    — {'home': id, 'away': id} (or (home_id, away_id));
        absent ids are looked up on the F4 board (by event id, or by team
        names for non-ESPN id spaces — F1);
      gamma_event_url — F5: the match's Polymarket GAMMA event URL
        (https://gamma-api.polymarket.com/events?id=…), threaded by the
        caller from the ledger MARKET_QUOTE event_id. Absent → the skip
        is journaled honestly.
    """
    fetched_at = datetime.now(timezone.utc)
    out: dict = {"league": league, "match_id": match_id,
                 "queries": [], "sources": []}
    path = SPORT_PATH.get(league)
    if not path:
        out["why"] = f"no research path for league {league}"
        return out

    # F3: the roster layer is REMOVED (law in ROSTER_REMOVAL_NOTE) — the
    # removal is journaled in every collection.
    out["queries"].append(ROSTER_REMOVAL_NOTE)

    # U5 wiring + F1: ids absent -> resolve on the F4 board days (by event
    # id, or by team names for non-ESPN id spaces). A lookup that finds
    # nothing keeps the layers honestly dormant.
    home_id, away_id = _team_ids_of(team_ids)
    if not home_id or not away_id:
        looked = lookup_team_ids(league=league, match_id=match_id,
                                 kickoff_utc=kickoff_utc,
                                 home=home or None, away=away or None)
        if looked:
            home_id = looked.get("home") or home_id
            away_id = looked.get("away") or away_id
            out["team_ids_lookup"] = "board"

    # 1) league news feed, filtered to items naming either team, inside
    #    the 48h window (injury/lineup/rota news surface there).
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
            if not (_hit(home, text) or _hit(away, text)):
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
                          f"teams={home}|{away}")

    # 2) F4 scoreboard status: the ET(kickoff) board days ±1 (journaled);
    #    the event is found by id (ESPN id spaces) or by BOTH team names
    #    (F1 — FD-* lane ids are not ESPN ids).
    days, et_date = _board_days(kickoff_utc)
    if not days:
        out["scoreboard_note"] = "kickoff_utc unparsable — no board days"
    out["queries"].append(
        f"F4 board days (et_date={et_date}) = {days}")
    seen_days = []
    for day in days:
        if day in seen_days:
            continue
        seen_days.append(day)
        board_url = (f"{ESPN_SITE_BOARD}/{path}/scoreboard?dates={day}")
        found_day = False
        try:
            board = _board_payload(path, day)   # cached; None on error
            if board is None:
                raise OSError("board fetch failed (cached)")
            ev, how = _find_event(board, match_id, home or None,
                                  away or None)
            if ev is not None:
                comp = (ev.get("competitions") or [{}])[0]
                found = str(((comp.get("status") or {})
                             .get("type") or {}).get("detail", ""))[:280]
                out["sources"].append({
                    "url": f"{board_url}#event={ev.get('id')}",
                    "fetched_at_utc": fetched_at
                    .strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "excerpt": found,
                    "published_utc": "",
                    "kind": "scoreboard_status"})
                out.setdefault("scoreboard_matches", []).append(
                    f"dates={day}: {how}")
                found_day = True        # ONE status citation per fixture
            else:
                out.setdefault("scoreboard_notes", []).append(
                    f"dates={day}: event absent from board "
                    f"(journaled, 0 sources)")
        except Exception as e:
            out.setdefault("scoreboard_notes", []).append(
                f"dates={day}: ERROR {type(e).__name__}: {e}"[:200])
        out["queries"].append(f"{path}/scoreboard?dates={day}")
        if found_day:
            break

    # 3) U5/F2 per-team injuries (core API, keyless): bare-$ref items are
    #    resolved with ONE journaled hop; a failed/absent endpoint is
    #    journaled as a zero-source query — never invented.
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
            got = _injury_sources(url, payload, fetched_at, out["queries"])
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

    # 4) F5 WSL self-captures: the match's Gamma event page + the official
    #    league page — exactly +2 hosts, honest zeros on any failure.
    out["sources"].extend(_gamma_source(gamma_event_url, out["queries"],
                                        fetched_at))
    out["sources"].extend(_league_official_source(league, home, away,
                                                  out["queries"],
                                                  fetched_at))

    if journal_dir is not None:
        journal_dir = Path(journal_dir)
        journal_dir.mkdir(parents=True, exist_ok=True)
        stamp = fetched_at.strftime("%Y%m%dT%H%M%SZ")
        (journal_dir / f"evidence_{match_id}_{stamp}.json").write_text(
            json.dumps(out, indent=1, sort_keys=True))
    return out
