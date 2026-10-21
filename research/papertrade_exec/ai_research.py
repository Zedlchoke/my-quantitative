"""AI research tools (PAPERDESK-FIXALL-NCAA-V1 W4.3).

Before an ALLOW is lawful the AI layer must have ACTUALLY gathered
evidence: news/heads-ups for both teams (48h window), each source stored
as a citation (url + fetched_at_utc + excerpt). Zero sources is a LAWFUL
refusal reason ("insufficient evidence") — never silently an approval.

SOURCES (allow-list, read-only public GETs, no keys):
  * ESPN news API for the fixture's sport: recent headlines naming either
    team (injury/lineup/rota items surface there), each with a link and a
    published timestamp;
  * the fixture's own league scoreboard record (roster/status context).
Everything else is refused by the allow-list — the model cannot invent
URLs into the citation record (the gate drops uncited claims).
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ESPN_SITE_API = "https://site.web.api.espn.com/apis/site/v2/sports"

SPORT_PATH = {"NBA": "basketball/nba", "WNBA": "basketball/wnba",
              "SOCCER": "soccer", "WSL": "soccer",
              "NCAA-M": "basketball/mens-college-basketball",
              "NCAA-W": "basketball/womens-college-basketball"}
NEWS_WINDOW_H = 48


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


def collect_evidence(*, league: str, match_id: str, home: str, away: str,
                     journal_dir: Path | None = None) -> dict:
    """Gather allow-listed evidence for one fixture. Returns
    {queries: [...], sources: [{url, fetched_at_utc, excerpt, kind}]} —
    the citations travel verbatim into the opinion record."""
    fetched_at = datetime.now(timezone.utc)
    out: dict = {"league": league, "match_id": match_id,
                 "queries": [], "sources": []}
    path = SPORT_PATH.get(league)
    if not path:
        out["why"] = f"no research path for league {league}"
        return out

    # 1) league news feed, filtered to items naming either team inside the
    #    48h window (injury / lineup / roster news surface here).
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

    # 2) the scoreboard record for the event (status/venue context).
    try:
        today = fetched_at.strftime("%Y%m%d")
        board = _get_json(
            f"https://site.api.espn.com/apis/site/v2/sports/{path}/"
            f"scoreboard?dates={today}")
        for ev in board.get("events", []):
            if str(ev.get("id")) == str(match_id):
                comp = ev["competitions"][0]
                out["sources"].append({
                    "url": f"https://site.api.espn.com/apis/site/v2/"
                           f"sports/{path}/scoreboard?dates={today}"
                           f"#event={match_id}",
                    "fetched_at_utc": fetched_at
                    .strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "excerpt": str(comp.get("status", {}).get(
                        "type", {}).get("detail", ""))[:280],
                    "kind": "scoreboard_status"})
                break
    except Exception as e:
        out["scoreboard_error"] = f"{type(e).__name__}: {e}"
    out["queries"].append(f"{path}/scoreboard?dates=today event={match_id}")

    if journal_dir is not None:
        journal_dir = Path(journal_dir)
        journal_dir.mkdir(parents=True, exist_ok=True)
        stamp = fetched_at.strftime("%Y%m%dT%H%M%SZ")
        (journal_dir / f"evidence_{match_id}_{stamp}.json").write_text(
            json.dumps(out, indent=1, sort_keys=True))
    return out
