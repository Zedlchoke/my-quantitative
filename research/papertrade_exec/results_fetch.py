"""Settlement result sources for SPORTS-PAPERTRADE-EXEC-V1 (ERRATUM_EXEC_5 D-2).

Law: a settle attempt may only be PROPOSED for a match whose source record is
FINAL (completed=true), carries both scores, and matches the ledger identity
1:1 (event id equality BY CONSTRUCTION + team identity through the PINNED
team-name crosswalk). Anything less returns an inconclusive record and the bet
stays OPEN — no inference, no backfill. Postponed/cancelled is recognized from
the structured ESPN status fields (`status.type.name` / `state`) — never from
a free-text guess alone — and maps to the frozen VOID refund results.

ESPN (NBA/WNBA) is free and keyless; The Odds API /scores (SOCCER) costs one
credit and reuses the pinned client's quota/key hygiene via a thin subclass.
Key bytes never leave the pinned client (only its fingerprint may surface).

PAPERDESK-FIXALL-NCAA-V1 (owner 2026-10-21):
  * W0.1 — team identity goes through research/papertrade_exec/team_names.py
    (one normalization + one sha-pinned crosswalk). The old abbreviation ==
    full-name string compare is the root cause that kept every NBA bet OPEN.
  * W0.6 — scoreboard scan window widened to [D-1, D+2] around the ledger
    kickoff date D: D-1 absorbs ESPN US-Eastern date slippage vs UTC,
    D+1/D+2 catch postponements/reschedules up to +48h (beyond that the bet
    ages into the stuck-alarm/dead-letter plane of ops_service W0.3).
    Postponed/cancelled recognition reads the STRUCTURED status fields
    (`status.type.name` e.g. STATUS_POSTPONED / STATUS_CANCELED /
    STATUS_SUSPENDED, `state`, `completed`) in addition to the legacy
    description/detail substrings; a FINAL event found on a different date is
    reported as rescheduled (inconclusive, kept OPEN with the new date).
"""
from __future__ import annotations

import hashlib
import json
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from research.papertrade_exec import team_names

ESPN_BASE = ("https://site.api.espn.com/apis/site/v2/sports/basketball/"
             "{league}/scoreboard?dates={date}")
ESPN_LEAGUE_PATH = {"WNBA": "wnba", "NBA": "nba"}
# W0.6 scan window: ledger kickoff date D plus offsets D-1 (ET slippage),
# D+1, D+2 (reschedules up to +48h).
ESPN_DATE_OFFSETS = (0, 1, -1, -2)
SETTLE_GRACE_HOURS = 3          # never propose a settle before kickoff+3h
SOCCER_RETRY_MIN_SECONDS = 6 * 3600

# Structured ESPN status names that are terminal non-FINAL outcomes
# (recognize-by-field, not by free text alone — W0.6).
ESPN_POSTPONED_STATUS = {"STATUS_POSTPONED", "STATUS_SUSPENDED"}
ESPN_CANCELLED_STATUS = {"STATUS_CANCELED", "STATUS_CANCELLED"}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_ts(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc)


def persist_evidence(data_root: Path, sandbox: bool, name: str,
                     meta: dict, body: bytes) -> Path:
    """Append-only evidence snapshot: raw bytes + meta (sha-bound)."""
    root = Path(data_root) / ("sandbox/ops" if sandbox else "ops") / \
        "results" / "evidence"
    root.mkdir(parents=True, exist_ok=True)
    (root / f"{name}.json").write_bytes(body)
    meta = {"evidence_sha256": hashlib.sha256(body).hexdigest(), **meta}
    (root / f"{name}.meta.json").write_text(json.dumps(meta, indent=1,
                                                       sort_keys=True))
    return root / f"{name}.json"


def map_completed_to_result(home_score: int, away_score: int,
                            outcomes: list[str]) -> str | None:
    """Pure: final score -> frozen settle result token (None = indeterminate,
    keep OPEN). outcomes: ["HOME","AWAY"] or ["HOME","DRAW","AWAY"]."""
    if "DRAW" in outcomes:
        if home_score == away_score:
            return "DRAW"
        return "HOME" if home_score > away_score else "AWAY"
    if home_score == away_score:
        return None                     # NBA/WNBA: a completed tie is not a
    return "HOME" if home_score > away_score else "AWAY"  # settleable result


# ------------------------------------------------------------------- ESPN ----

def _espn_get(path_league: str, date_compact: str) -> tuple[dict, bytes, int]:
    url = ESPN_BASE.format(league=path_league, date=date_compact)
    req = urllib.request.Request(url, headers={"User-Agent": "research/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        body = r.read()
        return json.loads(body), body, 200


def _espn_find_event(payload: dict, match_id: str) -> dict | None:
    for e in payload.get("events", []):
        if str(e.get("id")) == str(match_id):
            return e
    return None


def fetch_espn_results(*, league: str, date: str, match_ids: list[str],
                       ledger_rows: list[dict], data_root: Path,
                       sandbox: bool, now_utc: str | None = None
                       ) -> tuple[dict, list[dict]]:
    """Returns (settleable, inconclusive). settleable entries map match_id ->
    {"result": HOME/AWAY/VOID-*, "source_ref": identity string}. Inconclusive
    entries carry {"match_id", "why"} and NEVER settle. Only match_ids listed
    AND present as BET_PAPER decisions with kickoff+grace passed are bounds —
    the caller (ops_service) pre-filters; this function still refuses any
    match_id absent from ledger_rows (identity bounds, fail-closed)."""
    path = ESPN_LEAGUE_PATH[league]
    dec = {r["match_id"]: r for r in ledger_rows
           if r.get("type") == "DECISION" and r.get("status") == "BET_PAPER"}
    target = {m: dec[m] for m in match_ids if m in dec}
    unknown = sorted(set(match_ids) - set(dec))
    if unknown:
        raise ValueError(f"refusing settle fetch for non-BET_PAPER/unknown "
                         f"match ids {unknown} (identity bounds)")
    fetched_at = now_utc or utc_now()
    events: dict[str, dict] = {}
    event_dates: dict[str, str] = {}
    for d in sorted({r["kickoff_utc"][:10] for r in target.values()}):
        dt = _parse_ts(d + "T00:00:00Z")
        for offset in ESPN_DATE_OFFSETS:   # W0.6: D-1 .. D+2 scan window
            compact = (dt - timedelta(days=offset)).strftime("%Y%m%d")
            payload, body, status = _espn_get(path, compact)
            persist_evidence(
                data_root, sandbox,
                f"espn_{path}_{compact}_{fetched_at.replace(':', '')}",
                {"provider": "espn", "endpoint": ESPN_BASE.format(
                    league=path, date=compact), "http_status": status,
                 "fetched_at_utc": fetched_at}, body)
            for m in target:
                ev = _espn_find_event(payload, m)
                if ev is not None:
                    events.setdefault(m, ev)
                    event_dates.setdefault(m, compact)
    settleable, inconclusive = {}, []
    for m, row in target.items():
        ev = events.get(m)
        if ev is None:
            inconclusive.append({"match_id": m,
                                 "why": "event id not found on source boards "
                                        "(kept OPEN)"})
            continue
        comp = ev["competitions"][0]
        st = comp["status"]["type"]
        detail = str(st.get("detail", ""))
        state = str(st.get("state", ""))
        status_name = str(st.get("name", "")).upper()
        desc = str(st.get("description", "")).upper()
        abbr = {c["homeAway"]: c.get("team", {}).get("abbreviation")
                for c in comp["competitors"]}
        scores = {c["homeAway"]: c.get("score") for c in comp["competitors"]}
        # W0.1 identity cross-check: id equality (by construction above) +
        # BOTH team names resolved through the pinned crosswalk; any
        # unresolved name is fail-closed (kept OPEN + incident, no guessing).
        ok_h, why_h = team_names.same_team(abbr.get("home") or "",
                                           row["home"], league)
        ok_a, why_a = team_names.same_team(abbr.get("away") or "",
                                           row["away"], league)
        if not (ok_h and ok_a):
            inconclusive.append({"match_id": m,
                                 "why": f"identity mismatch: source "
                                        f"{abbr} != ledger {row['home']}/"
                                        f"{row['away']} ({why_h}; {why_a}) "
                                        "(kept OPEN)"})
            continue
        board_day = event_dates.get(m, "")
        ledger_day = row["kickoff_utc"][:10].replace("-", "")
        rescheduled = bool(board_day) and board_day != ledger_day
        if st.get("completed") is True:
            if rescheduled:
                inconclusive.append({"match_id": m,
                                     "why": f"event found FINAL on board day "
                                            f"{board_day} != ledger kickoff "
                                            f"day {ledger_day} (rescheduled; "
                                            "kept OPEN for explicit review)"})
                continue
            try:
                hs, as_ = int(scores["home"]), int(scores["away"])
            except (TypeError, ValueError, KeyError):
                inconclusive.append({"match_id": m,
                                     "why": "completed but scores unreadable "
                                            "(kept OPEN)"})
                continue
            res = map_completed_to_result(hs, as_, ["HOME", "AWAY"])
            if res is None:
                inconclusive.append({"match_id": m,
                                     "why": "completed tie score; no settleable "
                                            "outcome (kept OPEN)"})
                continue
            settleable[m] = {
                "result": res,
                "source_ref": (f"espn_scoreboard wnba_nba path={path} "
                               f"event={m} completed=true detail={detail!r} "
                               f"home={row['home']}:{hs} away={row['away']}:"
                               f"{as_} fetched_at={fetched_at}"),
            }
        elif (status_name in ESPN_POSTPONED_STATUS
              or "POSTPON" in desc or "POSTPON" in detail.upper()
              or state == "postponed"):
            settleable[m] = {
                "result": "POSTPONED_NO_RESCHEDULE",
                "source_ref": (f"espn_scoreboard event={m} "
                               f"status={status_name or 'postponed'} "
                               f"detail={detail!r} fetched_at={fetched_at}"),
            }
        elif (status_name in ESPN_CANCELLED_STATUS
              or "CANCEL" in desc or "CANCEL" in detail.upper()
              or state == "cancelled"):
            settleable[m] = {
                "result": "CANCELLED",
                "source_ref": (f"espn_scoreboard event={m} "
                               f"status={status_name or 'cancelled'} "
                               f"detail={detail!r} fetched_at={fetched_at}"),
            }
        elif rescheduled:
            inconclusive.append({"match_id": m,
                                 "why": f"event found on board day {board_day} "
                                        f"!= ledger kickoff day {ledger_day} "
                                        f"(state={state!r}; rescheduled; "
                                        "kept OPEN)"})
        else:
            inconclusive.append({"match_id": m,
                                 "why": f"source not FINAL (state={state!r}, "
                                        f"detail={detail!r}); kept OPEN"})
    return settleable, inconclusive


# --------------------------------------------------- The Odds API /scores ----

def make_scores_client(odds_mod, quota, key_path=None):
    """Thin subclass of the PINNED OddsClient adding the /scores endpoint.
    Key hygiene + quota precheck/journal are inherited unchanged; scores cost
    one credit (precheck conservatively at 1)."""
    class _ScoresClient(odds_mod.OddsClient):
        def get_scores(self, sport_key: str, days_from: int = 3):
            return self._get(f"/v4/sports/{sport_key}/scores",
                             f"daysFrom={days_from}", 1)
    if key_path is not None:
        return _ScoresClient(key_path=Path(key_path), quota=quota)
    return _ScoresClient(quota=quota)


def fetch_soccer_scores(*, odds_mod, quota, client, sport_keys: list[str],
                        match_ids: list[str], ledger_rows: list[dict],
                        data_root: Path, sandbox: bool
                        ) -> tuple[dict, list[dict]]:
    """SOCCER settle proposal source: The Odds API /scores (1 credit per
    sport-key call, quota precheck). Same identity law as ESPN. Snapshots
    persisted like the events capture. Any QuotaSkip/KeyHalted propagates to
    the caller (journal + keep OPEN — never bypass the quota law)."""
    dec = {r["match_id"]: r for r in ledger_rows
           if r.get("type") == "DECISION" and r.get("status") == "BET_PAPER"}
    target = {m: dec[m] for m in match_ids if m in dec}
    unknown = sorted(set(match_ids) - set(dec))
    if unknown:
        raise ValueError(f"refusing scores fetch for non-BET_PAPER/unknown "
                         f"match ids {unknown} (identity bounds)")
    fetched_at = utc_now()
    settleable, inconclusive = {}, []
    seen: dict[str, dict] = {}
    for key in sport_keys:
        body, hdrs = client.get_scores(key)          # pinned hygiene + quota
        persist_evidence(
            data_root, sandbox, f"oddapi_scores_{key}_{fetched_at.replace(':', '')}",
            {"provider": "the-odds-api", "endpoint": f"/v4/sports/{key}/scores",
             "fetched_at_utc": fetched_at,
             "x_requests_used": hdrs.get("x-requests-used"),
             "x_requests_remaining": hdrs.get("x-requests-remaining")}, body)
        for ev in json.loads(body):
            if str(ev.get("id")) in target:
                seen[str(ev.get("id"))] = ev
    for m, row in target.items():
        ev = seen.get(m)
        if ev is None:
            inconclusive.append({"match_id": m,
                                 "why": "event id absent from /scores payload "
                                        "(kept OPEN)"})
            continue
        if ev.get("completed") is not True:
            inconclusive.append({"match_id": m,
                                 "why": "source completed!=true (kept OPEN)"})
            continue
        sc = ev.get("scores") or []
        by_name = {s.get("name"): s.get("score") for s in sc}
        try:
            hs = int(by_name[ev["home_team"]])
            as_ = int(by_name[ev["away_team"]])
        except (KeyError, TypeError, ValueError):
            inconclusive.append({"match_id": m,
                                 "why": "completed but team scores unreadable "
                                        "(kept OPEN)"})
            continue
        res = map_completed_to_result(hs, as_, ["HOME", "DRAW", "AWAY"])
        if res is None:
            inconclusive.append({"match_id": m,
                                 "why": "indeterminate FT mapping (kept OPEN)"})
            continue
        last_update = ev.get("last_update", "")
        # league-phase-only guard lives in the caller (stage law); the raw
        # identity string keeps the evidence auditable.
        settleable[m] = {
            "result": res,
            "source_ref": (f"the-odds-api/v4 scores event={m} completed=true "
                           f"home={ev['home_team']}:{hs} "
                           f"away={ev['away_team']}:{as_} "
                           f"last_update={last_update} "
                           f"fetched_at={fetched_at}"),
        }
    return settleable, inconclusive
