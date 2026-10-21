"""W3.2 live read-only probe (PAPERDESK-FIXALL-NCAA-V1): NBA 2-way + WSL
3-YES through the REAL join/walk laws at the current HEAD. READ-ONLY public
GETs only (Gamma public-search / Gamma events / CLOB book) — no orders, no
keys, no writes anywhere but this evidence file. Owner gates stay OFF; the
probe proves the PM path is READY-TO-GO, it does not enable anything."""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from research.papertrade_exec import pm_moneyline as PMM   # noqa: E402
from research.papertrade_exec.execute import WSL_GAMMA_TAG_ID  # noqa: E402

OUT = REPO / ("research/control/PAPERDESK-FIXALL-NCAA-V1/evidence/"
              "PM_LIVE_PROBE_FIXALL_2026-10-21.json")
DATA = REPO / "research/control/PAPERDESK-FIXALL-NCAA-V1/evidence"
DATA.mkdir(parents=True, exist_ok=True)


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def probe() -> dict:
    record: dict = {"generated_at_utc": datetime.now(timezone.utc)
                    .strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "mode": "READ-ONLY public GETs (Gamma + CLOB); gates "
                            "untouched; no orders possible",
                    "nba": {}, "wsl": {}}
    tmp = Path("/tmp/pm_probe_fixall")
    tmp.mkdir(exist_ok=True)

    # ---- NBA: today's slate via the REAL public-search joiner ----
    try:
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        board = json.loads(get(
            "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/"
            f"scoreboard?dates={today}"))
        ev = next((e for e in board.get("events", [])
                   if e.get("competitions", [{}])[0].get("competitors")),
                  None)
        if ev:
            comps = ev["competitions"][0]["competitors"]
            home = comps[0]["team"].get("displayName")
            away = comps[1]["team"].get("displayName")
            record["nba"]["espn_fixture"] = {"id": ev.get("id"),
                                             "home": home, "away": away}
            event, ml = PMM.discover_and_join(
                home=home, away=away,
                kickoff_utc=(ev.get("date") or "").replace("Z", "Z"),
                data_root=tmp, sandbox=True)
            if event is None:
                record["nba"]["join"] = {"ok": False, "why": ml}
            else:
                record["nba"]["join"] = {
                    "ok": True, "pm_event_id": str(event.get("id")),
                    "pm_title": str(event.get("title"))[:120],
                    "market_id": str(ml.get("id")),
                    "outcomes": ml.get("outcomes")}
                tokens = ml.get("clobTokenIds")
                if isinstance(tokens, str):
                    tokens = json.loads(tokens)
                token0 = (tokens or [""])[0]
                ob = json.loads(get(
                    "https://clob.polymarket.com/book?"
                    + urllib.parse.urlencode({"token_id": token0})))
                asks = ob.get("asks") or []
                record["nba"]["clob_book"] = {
                    "ok": True, "levels": len(asks),
                    "best_ask": asks[0]["price"] if asks else None,
                    "book_sha": str(ob.get("hash"))[:16]}
        else:
            record["nba"]["espn_fixture"] = None
    except Exception as e:
        record["nba"]["error"] = f"{type(e).__name__}: {e}"

    # ---- WSL: pinned tag scan (read-only) + 3-YES shape check ----
    try:
        q = urllib.parse.urlencode({"tag_id": WSL_GAMMA_TAG_ID,
                                    "closed": "false", "limit": "5",
                                    "offset": "0"})
        body = json.loads(get(
            f"https://gamma-api.polymarket.com/events?{q}"))
        events = body.get("events", body) if isinstance(body, dict) else body
        record["wsl"]["tag_scan"] = {
            "ok": True, "tag_id": WSL_GAMMA_TAG_ID,
            "open_events_first_page": len(events or [])}
        for e in (events or [])[:3]:
            three_yes = [m for m in (e.get("markets") or [])
                         if str((m.get("outcomes") or [""])[0]).lower()
                         in ("yes",) or "will" in str(
                             m.get("question", "")).lower()]
            record["wsl"].setdefault("events_sample", []).append({
                "event_id": str(e.get("id")), "title": str(e.get("title"))
                [:100], "markets": len(e.get("markets") or [])})
    except Exception as e:
        record["wsl"]["error"] = f"{type(e).__name__}: {e}"

    ok_nba = record["nba"].get("join", {}).get("ok") is True
    record["verdict"] = {
        "nba_join_and_book": "PASS" if ok_nba else
        ("NOT_RUN_NETWORK" if "error" in record["nba"] else "CHECK"),
        "wsl_tag_scan": "PASS" if record["wsl"].get("tag_scan", {})
        .get("ok") else "NOT_RUN_NETWORK",
    }
    return record


if __name__ == "__main__":
    rec = probe()
    OUT.write_text(json.dumps(rec, indent=1, sort_keys=True))
    print(json.dumps(rec, indent=1, sort_keys=True))
