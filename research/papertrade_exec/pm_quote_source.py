"""Per-league Polymarket quote adapter registry (LANE 1, owner order).

Feature-gated behind the cutover GO: BEFORE the GO is consumed the
production quote source remains the pre-cutover pinned path (Odds API for
NBA/WNBA/soccer; Polymarket 3-YES for WSL which is already live). AFTER
the GO this module dispatches the per-league PM adapter.

Each adapter returns a normalised QuoteResult:
  {legs: {leg: {best_ask, d_eff, ev_net, depth_ok}}, all_present, ...}

The deterministic gate evaluator (decision_pipeline.check_deterministic_gates)
consumes this unchanged regardless of source — the cutover changes WHERE
the numbers come from, not HOW they are graded.
"""
from __future__ import annotations

import json
import urllib.request
from typing import Any, Dict, Optional, Tuple

from research.papertrade_exec.pm_moneyline import (
    probe_event_moneyline,
)

USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36")


class PMQuoteAdapter:
    """Per-league Polymarket quote adapter — sandbox/feature-gate only."""

    def __init__(self, *, data_root, sandbox: bool = False):
        self.data_root = data_root
        self.sandbox = sandbox

    # ------------------------------------------------------- 2-way (NBA/WNBA)
    def quote_moneyline_2way(
        self, *, event_id: str, home: str, away: str,
        stake_cents: int,
    ) -> Optional[Dict[str, Any]]:
        """NBA/WNBA: 2-outcome moneyline. Returns legs dict or None."""
        try:
            result = probe_event_moneyline(
                event_id=event_id, home=home, away=away,
                stake_cents=stake_cents, data_root=self.data_root,
                sandbox=self.sandbox)
        except Exception:
            return None
        if not result.get("joined"):
            return None
        walk = result.get("book_walk_at_stake")
        if not walk:
            return None
        # For 2-way moneyline the HOME token is tokens[0] (the probed leg).
        # The AWAY leg's 1 - VWAP is the implied AWAY ask (approximation for
        # display only; the executable AWAY walk would use tokens[1]).
        best = walk.get("best_ask", 0)
        vwap = walk.get("vwap_ask", 0)
        return {
            "legs": {
                "HOME": {"best_ask": best, "vwap_ask": vwap,
                         "depth_ok": True, "levels": walk.get("levels", 0)},
                "AWAY": {"best_ask": round(1.0 - best, 4),
                         "vwap_ask": round(1.0 - vwap, 4),
                         "depth_ok": True, "levels": walk.get("levels", 0),
                         "note": "approx from HOME ask (2-outcome complement)"},
            },
            "all_present": True,
            "event_id": event_id,
            "market_id": result.get("market_id"),
        }

    # ----------------------------------------------------- 3-YES (SOCCER/WSL)
    def quote_3yes(
        self, *, event_id: str, market_ids: Dict[str, str],
        stake_cents: int,
    ) -> Optional[Dict[str, Any]]:
        """SOCCER/WSL: 3-YES H/D/A from the same event. Returns legs or None.
        market_ids: {"HOME": "...", "DRAW": "...", "AWAY": "..."}"""
        try:
            req = urllib.request.Request(
                f"https://gamma-api.polymarket.com/events?id={event_id}",
                headers={"Accept": "application/json", "User-Agent":
                         "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except Exception:
            return None
        events = payload if isinstance(payload, list) else []
        event = events[0] if events else None
        if not event:
            return None
        markets_by_id = {str(m.get("id")): m for m in event.get("markets") or []}
        legs = {}
        for leg, mid in market_ids.items():
            m = markets_by_id.get(str(mid))
            if not m:
                continue
            closed = m.get("closed") is True
            prices = m.get("outcomePrices")
            if isinstance(prices, str):
                try: prices = json.loads(prices)
                except Exception: prices = []
            outs = m.get("outcomes")
            if isinstance(outs, str):
                try: outs = json.loads(outs)
                except Exception: outs = []
            if outs and str(outs[0]).lower() == "yes" and prices:
                legs[leg] = {
                    "best_ask": float(prices[0]) if prices else None,
                    "market_id": mid,
                    "closed": closed,
                }
        if len(legs) < 2:
            return None
        return {"legs": legs, "all_present": len(legs) == 3,
                "event_id": event_id}


class QuoteSourceRouter:
    """Routes quote requests to the correct adapter per league, respecting
    the cutover state. BEFORE cutover GO: returns None (caller falls back
    to the pinned pre-cutover path). AFTER: dispatches to PM adapter."""

    def __init__(self, *, cutover_active: bool, data_root,
                 sandbox: bool = False):
        self.cutover_active = cutover_active
        self.adapter = PMQuoteAdapter(data_root=data_root,
                                      sandbox=sandbox)

    def quote(self, *, league: str, event_id: str,
              home: str, away: str,
              market_ids: Optional[Dict[str, str]] = None,
              stake_cents: int = 0) -> Optional[Dict[str, Any]]:
        if not self.cutover_active:
            return None   # pre-cutover: caller uses pinned source
        if league in ("NBA", "WNBA"):
            return self.adapter.quote_moneyline_2way(
                event_id=event_id, home=home, away=away,
                stake_cents=stake_cents)
        if league in ("SOCCER", "WSL") and market_ids:
            return self.adapter.quote_3yes(
                event_id=event_id, market_ids=market_ids,
                stake_cents=stake_cents)
        return None
