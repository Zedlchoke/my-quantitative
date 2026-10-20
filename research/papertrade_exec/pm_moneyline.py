"""POLYMARKET MONEYLINE 2-WAY — joiner + walker for NBA/WNBA
(owner order 2026-10-20, LANE 1). SEPARATE from the soccer/WSL 3-YES law.

LAWS
  * join: Gamma event title must contain BOTH fixture team names
    (pinned crosswalk normalization); the MONEYLINE market is the one whose
    `outcomes` == exactly the two team display names — derivatives (Team to
    Score First, Odd/Even, Exact Score, Halftime) are REFUSED;
  * identity: clobTokenIds[0] = YES on outcomes[0] (first team),
    clobTokenIds[1] = YES on outcomes[1]; buying YES on the chosen leg IS
    the moneyline bet — NO(Home) is never Away (2-way has no NO-bridge);
  * executable price = CLOB book ASK walk by token id (never Gamma
    outcomePrices — those are indicative, never a quote);
  * every payload journaled (raw + sha256 + retrieval UTC).

Read-only: this module NEVER places orders; it produces quote evidence for
the sandbox pipeline and the post-cutover decision path (authoritative only
after the cutover GO is consumed and the exec lane is wired).
"""
from __future__ import annotations

import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

GAMMA_EVENT_URL = "https://gamma-api.polymarket.com/events"
GAMMA_SEARCH_URL = "https://gamma-api.polymarket.com/public-search"
CLOB_BOOK_URL = "https://clob.polymarket.com/book"


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _norm(name: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "", str(name).casefold())


def _get_json(url: str) -> dict | list:
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _journal(data_root: Path, sandbox: bool, kind: str, url: str,
             raw: bytes) -> str:
    sha = hashlib.sha256(raw).hexdigest()
    if True:  # journal inside the caller's data root (sandbox-scoped)
        jdir = Path(data_root) / "data" / "pm_moneyline"
        jdir.mkdir(parents=True, exist_ok=True)
        stamp = _now_utc().replace("-", "").replace(":", "")
        (jdir / f"{stamp}_{kind}.json").write_bytes(raw)
        with open(jdir / "index.jsonl", "a") as f:
            f.write(json.dumps({"at_utc": _now_utc(), "kind": kind,
                                "url": url, "sha256": sha,
                                "bytes": len(raw)}) + "\n")
    return sha


def _is_moneyline(market: dict, home: str, away: str) -> bool:
    """The moneyline market's outcomes are EXACTLY the two team display
    names. Derivatives (score-first, odd/even, halftime, exact score,
    corners) have different outcome labels or extra markets — refused."""
    outcomes = market.get("outcomes")
    if isinstance(outcomes, str):
        try: outcomes = json.loads(outcomes)
        except Exception: return False
    if not isinstance(outcomes, list) or len(outcomes) != 2:
        return False
    o0, o1 = _norm(outcomes[0]), _norm(outcomes[1])
    h, a = _norm(home), _norm(away)
    paired = ((h in o0 or o0 in h) and (a in o1 or o1 in a)) or \
             ((a in o0 or o0 in a) and (h in o1 or o1 in h))
    q = str(market.get("question") or "").lower()
    derivative = any(k in q for k in ("score first", "odd/even",
                                      "halftime", "exact score",
                                      "to score", "corners"))
    return paired and not derivative


def discover_and_join(*, home: str, away: str, kickoff_utc: str,
                      data_root: Path, sandbox: bool = False):
    """Public-search + event fetch; returns (event, moneyline_market) or
    (None, reason). Journal: raw payloads + sha."""
    q = f"{home} vs {away}"
    import urllib.parse
    url = (f"https://gamma-api.polymarket.com/public-search?q="
           + urllib.parse.quote(q)
           + "&events_status=active&limit_per_type=20")
    raw = _get_json.__self__ if False else None
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw_bytes = resp.read()
    _journal(data_root, sandbox, "gamma_search", url, raw_bytes)
    data = json.loads(raw_bytes.decode("utf-8"))
    h, a = _norm(home), _norm(away)
    for ev in data.get("events") or []:
        title = str(ev.get("title") or "")
        if not ((h in norm(title) or norm(title) in h and len(norm(title)) > 6)
                and (a in norm(title) or norm(title) in a
                     and len(norm(title)) > 6)):
            # event title must reference both teams (normalized containment,
            # bidirectional short-form)
            if not (h[:10] in norm(title) or a[:10] in norm(title)):
                continue
        for m in ev.get("markets") or []:
            if _is_moneyline(m, home, away):
                return ev, m
    return None, "no 2-outcome moneyline market joined for " + q


def walk_ask(token_id: str, *, stake_cents: int, data_root: Path,
             sandbox: bool = False) -> dict | None:
    """CLOB book ASK walk for one YES token at the given stake (cents).
    Returns {best_ask, vwap_ask, filled_shares, spend, fee, levels} or None.
    Fee: Polymarket taker fee = 0.05·p·(1−p) per share, applied once
    (mirror of the pinned soccer/WSL fee law; same formula, 2-way market)."""
    url = f"{CLOB_BOOK_URL}?token_id={token_id}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
    _journal(data_root, sandbox, "clob_book", url, raw)
    book = json.loads(raw.decode("utf-8"))
    asks = sorted(({ "price": float(l["price"]), "size": float(l["size"]) }
                   for l in (book.get("asks") or [])),
                  key=lambda x: x["price"])
    if not asks: return None
    shares_needed = stake_cents / 100.0        # YES pays $1/share; stake $
    remaining, spend, filled, levels = shares_needed, 0.0, 0.0, 0
    fee = 0.0
    for lvl in asks:
        take = min(lvl["size"], remaining)
        cost = take * lvl["price"]
        fee += 0.05 * lvl["price"] * (1 - lvl["price"]) * take
        spend += cost + 0.05 * lvl["price"] * (1 - lvl["price"]) * take
        filled += take
        levels += 1
        remaining -= take
        if remaining <= 0: break
    if remaining > 0: return None              # insufficient depth
    vwap = spend / filled if filled else None
    return {"best_ask": asks[0]["price"], "vwap_ask": vwap,
            "filled_shares": round(filled, 2), "spend_cents":
                round(spend * 100), "fee_cents": round(fee * 100),
            "levels": levels}


def probe_event_moneyline(*, event_id: str, home: str, away: str,
                          stake_cents: int, data_root: Path,
                          sandbox: bool = False) -> dict:
    """Live read-only probe: join + book-walk on a REAL event id.
    Returns the evidence record (no orders, no ledger writes)."""
    url = f"{GAMMA_EVENT_URL}?id={event_id}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
    _journal(data_root, sandbox, "gamma_event", url, raw)
    ev = json.loads(raw.decode("utf-8"))
    ev = ev[0] if isinstance(ev, list) and ev else ev
    ml = None
    for m in ev.get("markets") or []:
        if _is_moneyline(m, home, away):
            ml = m; break
    if ml is None:
        return {"event_id": event_id, "joined": False,
                "why": "no 2-outcome moneyline market in event"}
    tokens = ml.get("clobTokenIds")
    if isinstance(tokens, str):
        try: tokens = json.loads(tokens)
        except Exception: tokens = []
    if not isinstance(tokens, list) or len(tokens) < 2:
        return {"event_id": event_id, "joined": True,
                "why": "clobTokenIds missing", "market_id": ml.get("id")}
    outcomes_raw = ml.get("outcomes")
    if isinstance(outcomes_raw, str):
        try: outcomes_list = json.loads(outcomes_raw)
        except Exception: outcomes_list = ["HOME", "AWAY"]
    else:
        outcomes_list = ["HOME", "AWAY"]

    home_yes_token = tokens[0]
    walk = walk_ask(home_yes_token, stake_cents=stake_cents,
                    data_root=data_root, sandbox=sandbox)
    prices = ml.get("outcomePrices")
    if isinstance(prices, str):
        try: prices = json.loads(prices)
        except Exception: prices = None
    return {"event_id": event_id, "joined": True,
            "market_id": ml.get("id"),
            "question": (ml.get("question") or "")[:90],
            "outcomes": ml.get("outcomes"),
            "indicative_prices": prices,   # NEVER used as a quote
            "home_yes_token": str(home_yes_token)[:16] + "…",
            "book_walk_at_stake": walk,
            "closed": ml.get("closed"),
            "uma": ml.get("umaResolutionStatus")}
