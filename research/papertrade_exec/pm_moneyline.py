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



def _team_name_hit(name: str, title_norm: str) -> bool:
    """Candidate retrieval only (identity is the market-outcome law):
    the pinned full name OR its single-word short form ("Orlando Magic" ->
    "magic") must appear in the normalized title."""
    n = _norm(name)
    if n and (n in title_norm or (title_norm in n and len(title_norm) >= 4)):
        return True
    words = str(name).split()
    short = _norm(words[-1]) if len(words) > 1 else n
    return len(short) >= 4 and short in title_norm


def _search_variants(home: str, away: str) -> list[str]:
    """Query variants tried in order: full names, then the single-word
    short forms Polymarket titles actually use ("Magic vs Hawks" -> event
    'Hawks vs. Magic', observed live 2026-10-21)."""
    out = [f"{home} vs {away}"]
    hs = home.split()[-1] if " " in home else home
    as_ = away.split()[-1] if " " in away else away
    if [hs, as_] != [home, away]:
        out.append(f"{hs} vs {as_}")
    return out


def discover_and_join(*, home: str, away: str, kickoff_utc: str,
                      data_root: Path, sandbox: bool = False):
    """Public-search + event fetch; returns (event, moneyline_market) or
    (None, reason). Journal: raw payloads + sha. Identity law: the event
    title must reference BOTH pinned team names (normalized, bidirectional
    short-form); the moneyline market's own outcomes must be exactly the two
    team names (_is_moneyline). Position is never trusted downstream."""
    import urllib.parse
    for q in _search_variants(home, away):
        url = (f"https://gamma-api.polymarket.com/public-search?q="
               + urllib.parse.quote(q)
               + "&events_status=active&limit_per_type=20")
        req = urllib.request.Request(url, headers={
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw_bytes = resp.read()
        _journal(data_root, sandbox, "gamma_search", url, raw_bytes)
        data = json.loads(raw_bytes.decode("utf-8"))
        for ev in data.get("events") or []:
            title = _norm(ev.get("title"))
            if not (_team_name_hit(home, title) and
                    _team_name_hit(away, title)):
                continue   # BOTH teams must appear — order never trusted
            for m in ev.get("markets") or []:
                if _is_moneyline(m, home, away):
                    return ev, m
    return None, "no 2-outcome moneyline market joined for " +         f"{home} vs {away}"


def discover_and_join_3yes(*, home: str, away: str, data_root: Path,
                           sandbox: bool = False):
    """SOCCER/WSL cutover joiner: ONE Gamma event carrying EXACTLY the three
    YES/NO markets (HOME win / Draw / AWAY win). Returns
    (event, {leg: market}) or (None, reason). A market joins a leg only by
    its question text referencing that leg uniquely (pinned name / 'draw');
    ambiguous or missing legs fail the whole join (fail-closed, never
    guessed)."""
    import urllib.parse
    for q in _search_variants(home, away):
        url = (f"https://gamma-api.polymarket.com/public-search?q="
               + urllib.parse.quote(q)
               + "&events_status=active&limit_per_type=20")
        req = urllib.request.Request(url, headers={
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw_bytes = resp.read()
        _journal(data_root, sandbox, "gamma_search", url, raw_bytes)
        data = json.loads(raw_bytes.decode("utf-8"))
        joined = _join_3yes_in_event(data, home, away)
        if joined is not None:
            return joined
    return None, "no 3-YES event joined for " + f"{home} vs {away}"


def _join_3yes_in_event(data: dict, home: str, away: str):
    """Scan one search response for the FIRST event carrying exactly the
    three YES/NO legs. Returns (event, legs) or None."""
    for ev in data.get("events") or []:
        title = _norm(ev.get("title"))
        if not (_team_name_hit(home, title) and
                _team_name_hit(away, title)):
            continue
        legs, used = {}, set()
        for m in ev.get("markets") or []:
            if m.get("closed") is True:
                continue
            outs = m.get("outcomes")
            if isinstance(outs, str):
                try:
                    outs = json.loads(outs)
                except Exception:
                    outs = []
            if not (isinstance(outs, list) and len(outs) == 2 and
                    {str(o).strip().lower() for o in outs} == {"yes", "no"}):
                continue                      # only 2-way YES/NO markets
            question = _norm(m.get("question"))
            in_home, in_away = (_team_name_hit(home, question),
                                _team_name_hit(away, question))
            if in_home and not in_away and "HOME" not in used:
                legs["HOME"], _ = m, used.add("HOME")
            elif in_away and not in_home and "AWAY" not in used:
                legs["AWAY"], _ = m, used.add("AWAY")
            elif "draw" in question and "DRAW" not in used:
                legs["DRAW"], _ = m, used.add("DRAW")
        if set(legs) == {"HOME", "DRAW", "AWAY"}:
            return ev, legs
    return None


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
    raw_sha = _journal(data_root, sandbox, "clob_book", url, raw)
    snapshot_utc = _now_utc()
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
            "levels": levels, "snapshot_utc": snapshot_utc,
            "book_sha256": raw_sha, "token_id": str(token_id),
            "depth_short_cents": 0}


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
        except Exception: outcomes_list = []
    else:
        outcomes_list = outcomes_raw or []

    # Mapping law (owner 2026-10-20): token->leg by the market's OWN outcome
    # NAME matched against the pinned crosswalk team names; position is
    # NEVER trusted. Any mismatch/reversal/ambiguity => NOT_RUN_MARKET_MISMATCH.
    mapping = map_outcomes_to_legs(outcomes_list, home=home, away=away)
    if mapping.get("error"):
        return {"event_id": event_id, "joined": True,
                "market_id": ml.get("id"),
                "why": "NOT_RUN_MARKET_MISMATCH: " + mapping["error"],
                "outcomes": ml.get("outcomes"),
                "indicative_prices": None}
    legs_result = {}
    all_ok = True
    for i, leg_name in enumerate(outcomes_list[:2]):
        leg = mapping["legs"][i]
        token = tokens[i]
        walk = walk_ask(token, stake_cents=stake_cents,
                        data_root=data_root, sandbox=sandbox)
        if walk is None:
            legs_result[leg] = {"error": "walk failed",
                                "token": str(token)[:16] + "…"}
            all_ok = False
        else:
            legs_result[leg] = walk
    prices = ml.get("outcomePrices")
    if isinstance(prices, str):
        try: prices = json.loads(prices)
        except Exception: prices = None
    return {"event_id": event_id, "joined": True,
            "market_id": ml.get("id"),
            "question": (ml.get("question") or "")[:90],
            "outcomes": ml.get("outcomes"),
            "token_map": mapping.get("map"),
            "indicative_prices": prices,   # NEVER used as a quote
            "legs": legs_result,
            "all_legs_walked": all_ok,
            "closed": ml.get("closed"),
            "uma": ml.get("umaResolutionStatus")}


def map_outcomes_to_legs(outcomes_list, *, home: str, away: str) -> dict:
    """Owner mapping law: each outcome NAME must resolve to exactly one of
    {HOME, AWAY} by normalized containment against the pinned team names;
    both legs must be present, distinct tokens implied by distinct names.
    Returns {"legs": [leg0, leg1], "map": {outcome: leg}} or {"error": ...}."""
    if not isinstance(outcomes_list, list) or len(outcomes_list) != 2:
        return {"error": f"expected 2 outcomes, got {outcomes_list!r}"}
    h, a = _norm(home), _norm(away)
    if not h or not a or h == a:
        return {"error": "crosswalk home/away unresolved or identical"}
    legs, mp = [], {}
    for o in outcomes_list:
        on = _norm(o)
        in_home = (h in on) or (on in h and len(on) >= 4)
        in_away = (a in on) or (on in a and len(on) >= 4)
        if in_home and not in_away:
            legs.append("HOME"); mp[str(o)] = "HOME"
        elif in_away and not in_home:
            legs.append("AWAY"); mp[str(o)] = "AWAY"
        else:
            return {"error": f"outcome {o!r} ambiguous vs ({home!r}, {away!r})"}
    if sorted(legs) != ["AWAY", "HOME"]:
        return {"error": f"legs not exactly one HOME + one AWAY: {legs!r}"}
    return {"legs": legs, "map": mp}
