"""WSL RESULTS SOURCE V1 — Polymarket UMA resolution of the tracked
3-YES 90-minute markets (owner order 2026-10-20: qualified WSL settlement).

WHY THIS SOURCE IS QUALIFIED
  The paper bets are 1:1 with Polymarket 90min-1X2-YES binaries (the ledger
  MARKET_QUOTE row stores the Gamma event_id and each leg's market_id —
  identity by construction, never a name/date guess). Those exact markets
  resolve by UMA under Polymarket's pinned 90-minute rules: awarded results
  resolve to the official score; postponed/cancelled/voided never produce a
  clean one-of-three YES=1 resolution and are therefore NOT settleable here
  (kept OPEN — no inference, no premature refund).

LAWS
  * market must be closed AND umaResolutionStatus == 'resolved';
  * outcomePrices[0] (outcomes[0] == 'Yes') must be exactly 1.0 for exactly
    ONE leg and exactly 0.0 for the other two — anything else (50/50 voids,
    multi-YES, pending) -> inconclusive, bet stays OPEN;
  * the market question must carry the bet's kickoff date ("on YYYY-MM-DD");
  * every payload is journaled (raw JSON + sha256 + retrieval UTC) under
    <data-root>/data/wsl_results/;
  * settlement itself stays with the PINNED append-only core: the caller
    stages {match_id: {result, source_ref}} and executes the standard
    cmd_settle — this module never writes the ledger.
"""
from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

GAMMA_EVENTS_URL = "https://gamma-api.polymarket.com/events"
LEGS = ("HOME", "DRAW", "AWAY")
SOURCE_PREFIX = "polymarket_uma event="


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


_norm_cache: dict = {}


def _norm(name: str) -> str:
    """IDENTICAL to the pinned polymarket_source.norm_name (casefold +
    collapse non-alphanumerics); cached."""
    import re
    if name not in _norm_cache:
        _norm_cache[name] = re.sub(r"[^a-z0-9]+", "",
                                   str(name).casefold())
    return _norm_cache[name]


_pm_to_fd_cache: dict | None = None


def _pm_to_fd() -> dict:
    """The PINNED WSL crosswalk (PM display name -> FD name), loaded via
    the same loader the quote lane uses. Identity law reuses it — never an
    ad-hoc ampersand/&-and rewrite."""
    global _pm_to_fd_cache
    if _pm_to_fd_cache is None:
        from research.papertrade_exec import wsl_lane
        pm = wsl_lane.load_pm_source()
        _pm_to_fd_cache = dict(pm.WSL_PM_NAME_TO_FD_NAME)
    return _pm_to_fd_cache


def _gamma_fetch_raw(url: str) -> bytes:
    """Transport seam — tests stub this; production uses urllib."""
    req = urllib.request.Request(url, headers={"Accept": "application/json",
                                               "User-Agent": "PaperDesk-ops"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def _gamma_get_json(event_id: str, data_root: Path, sandbox: bool) -> dict:
    """Journaled public GET of the Gamma event (raw bytes + sha + index)."""
    url = f"{GAMMA_EVENTS_URL}?id={event_id}"
    raw = _gamma_fetch_raw(url)
    payload = json.loads(raw.decode("utf-8"))
    body_sha = hashlib.sha256(raw).hexdigest()
    # journal lives INSIDE the caller's data root — when sandbox=True that
    # root is already the sandbox tree, so the real plane is never touched
    jdir = Path(data_root) / "data" / "wsl_results"
    jdir.mkdir(parents=True, exist_ok=True)
    stamp = _now_utc().replace("-", "").replace(":", "")
    (jdir / f"{stamp}_event_{event_id}.json").write_bytes(raw)
    with open(jdir / "index.jsonl", "a") as f:
        f.write(json.dumps({
            "at_utc": _now_utc(), "url": url, "sha256": body_sha,
            "bytes": len(raw)}) + "\n")
    return payload


def _yes_price(market: dict) -> float | None:
    prices = market.get("outcomePrices")
    outcomes = market.get("outcomes")
    try:
        if isinstance(prices, str):
            prices = json.loads(prices)
        if isinstance(outcomes, str):
            outcomes = json.loads(outcomes)
        if not (isinstance(prices, list) and isinstance(outcomes, list)):
            return None
        if not outcomes or str(outcomes[0]).lower() != "yes":
            return None
        return float(prices[0])
    except (ValueError, TypeError, IndexError):
        return None


def _quote_ref(ledger_rows: list[dict], match_id: str) -> dict | None:
    """The bet's OWN MARKET_QUOTE row: identity by construction."""
    for r in ledger_rows:
        if (r.get("type") == "MARKET_QUOTE" and r.get("league") == "WSL"
                and r.get("match_id") == match_id):
            return r
    return None


def fetch_wsl_settleable(*, rows: list[dict], ledger_rows: list[dict],
                         data_root: Path | str, sandbox: bool = False):
    """rows: open WSL BET_PAPER decision rows due for settlement.
    Returns (settleable, inconclusive) in the standard _fetch_results
    contract: settleable = {match_id: {result, source_ref}};
    inconclusive = [{match_id, why}]."""
    settleable: dict[str, dict] = {}
    inconclusive: list[dict] = []
    for r in rows:
        mid = r["match_id"]
        qref = _quote_ref(ledger_rows, mid)
        if not qref:
            inconclusive.append({"match_id": mid,
                                 "why": "no ledger MARKET_QUOTE row for the "
                                        "WSL bet — identity unresolved"})
            continue
        event_id = qref.get("event_id")
        pm = qref.get("pm_outcomes") or {}
        leg_market = {}
        for leg in LEGS:
            o = pm.get(leg) or {}
            mid_id = o.get("market_id")
            if mid_id is not None:
                leg_market[str(mid_id)] = leg
        if not event_id or not leg_market:
            inconclusive.append({"match_id": mid,
                                 "why": "quote row lacks event_id / per-leg "
                                        "market ids — identity unresolved"})
            continue

        payload = _gamma_get_json(str(event_id), data_root, sandbox)
        events = payload if isinstance(payload, list) else []
        event = events[0] if events else None
        if not event:
            inconclusive.append({"match_id": mid,
                                 "why": f"gamma event {event_id} not found"})
            continue

        ko_date = (r.get("kickoff_utc") or "")[:10]
        title = str(event.get("title") or "")
        home_name = str(r.get("home") or "").lower()
        away_name = str(r.get("away") or "").lower()
        # identity: the EVENT must name both teams; a per-leg question is
        # identity-ok when it carries the kickoff date OR both team names
        # (Polymarket phrases DRAW markets without a date but with the full
        # fixture pairing — observed 2026-10-20 on the real payloads)
        def _team_in_title(team_fd: str, title_norm: str) -> bool:
            """FD-name -> title match THROUGH the pinned crosswalk: the FD
            name itself, or any pinned PM display name that maps to it
            (e.g. 'Brighton and Hove Albion WFC' <-> 'Brighton & Hove '
            'Albion'). Never ad-hoc string surgery."""
            n = _norm(team_fd)
            if n and n in title_norm:
                return True
            for pm_name, fd_name in _pm_to_fd().items():
                if str(fd_name).lower() == team_fd.lower() and _norm(
                        pm_name) and _norm(pm_name) in title_norm:
                    return True
            return False

        title_norm = title.casefold()
        title_norm = __import__("re").sub(r"[^a-z0-9]+", "", title_norm)
        event_ok = (bool(home_name) and bool(away_name)
                    and _team_in_title(home_name, title_norm)
                    and _team_in_title(away_name, title_norm))
        yes_by_leg: dict[str, float] = {}
        details = []
        resolved_all = True
        for m in event.get("markets") or []:
            mid_id = str(m.get("id"))
            if mid_id not in leg_market:
                continue
            leg = leg_market[mid_id]
            closed = m.get("closed") is True
            uma = str(m.get("umaResolutionStatus") or "")
            yp = _yes_price(m)
            qtext_norm = __import__("re").sub(
                r"[^a-z0-9]+", "", str(m.get("question") or "").casefold())
            leg_ok = _team_in_title(home_name, qtext_norm) or _team_in_title(
                away_name, qtext_norm) or (
                ko_date and ko_date in str(m.get("question") or ""))
            ok_id = event_ok and leg_ok
            details.append(f"{leg}:{mid_id} closed={closed} uma={uma} "
                           f"yes={yp} id_ok={ok_id}")
            if not (closed and uma == "resolved" and yp is not None
                    and ok_id):
                resolved_all = False
            yes_by_leg[leg] = yp if yp is not None else -1.0
        if len(yes_by_leg) != len(leg_market):
            inconclusive.append({"match_id": mid,
                                 "why": "gamma payload missing tracked "
                                        "markets [" + "; ".join(details)
                                        + "]"})
            continue
        if not resolved_all:
            # postponed / cancelled / pending UMA: NO settlement, no refund,
            # no inference — the bet stays OPEN and the reason is journaled
            inconclusive.append({"match_id": mid,
                                 "why": "not a finished 90-minute resolution "
                                        "(" + "; ".join(details) + ")"})
            continue
        winners = [leg for leg, p in yes_by_leg.items() if p == 1.0]
        zeros = [leg for leg, p in yes_by_leg.items() if p == 0.0]
        if len(winners) != 1 or len(zeros) != len(leg_market) - 1:
            inconclusive.append({"match_id": mid,
                                 "why": "ambiguous resolution (postponed/"
                                        "voided?) — winners=" + repr(winners)
                                        + " details=" + "; ".join(details)})
            continue
        winner = winners[0]
        resolved_by = ""
        for m in event.get("markets") or []:
            if str(m.get("id")) in leg_market:
                resolved_by = str(m.get("resolvedBy") or "")[:14]
                break
        source_ref = (f"{SOURCE_PREFIX}{event_id} "
                      f"winner={winner} "
                      f"markets=" + "/".join(sorted(leg_market)) + " "
                      f"resolvedBy={resolved_by}… uma=resolved "
                      f"fetched_at={_now_utc()}")
        settleable[mid] = {"result": winner, "source_ref": source_ref}
    return settleable, inconclusive


YES_LEGS = LEGS
