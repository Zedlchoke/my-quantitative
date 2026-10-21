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

import hashlib
import json
import urllib.request

from .pm_moneyline import walk_ask
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
        # BOTH legs walked separately via their own CLOB tokens
        # (P0 fix: no AWAY=1−HOME approximation, no hardcoded depth_ok)
        legs_result = result.get("legs") or {}
        if not legs_result.get("HOME", {}).get("best_ask") or            not legs_result.get("AWAY", {}).get("best_ask"):
            return None   # either leg's walk failed — insufficient depth
        return {
            "legs": {
                leg: {
                    "best_ask": legs_result[leg].get("best_ask"),
                    "vwap_ask": legs_result[leg].get("vwap_ask"),
                    "filled_shares": legs_result[leg].get("filled_shares"),
                    "fee_total": legs_result[leg].get("fee_total"),
                    "levels": legs_result[leg].get("levels"),
                    "depth_ok": True,  # walk succeeded (spend covered)
                }
                for leg in ("HOME", "AWAY")
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
        """SOCCER/WSL: 3-YES H/D/A from the same event. For EACH leg the
        market's YES token (by outcome NAME, never by position) is walked
        on the CLOB book at the REAL stake. outcomePrices is carried as
        indicative only and NEVER enters EV or decisions.
        Returns {"legs": {leg: walk...}, "all_present": bool, ...} or None
        (None = cannot join / hard refusal — caller maps to NOT_RUN)."""
        try:
            req = urllib.request.Request(
                f"https://gamma-api.polymarket.com/events?id={event_id}",
                headers={"Accept": "application/json", "User-Agent":
                         "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
            raw_sha = hashlib.sha256(raw).hexdigest()
            payload = json.loads(raw.decode("utf-8"))
        except Exception:
            return None
        events = payload if isinstance(payload, list) else []
        event = events[0] if events else None
        if not event:
            return None
        markets_by_id = {str(m.get("id")): m for m in event.get("markets") or []}
        legs, indicative = {}, {}
        for leg, mid in market_ids.items():
            m = markets_by_id.get(str(mid))
            if not m:
                legs[leg] = {"error": "MARKET_NOT_IN_EVENT", "market_id": mid}
                continue
            if m.get("closed") is True:
                legs[leg] = {"error": "MARKET_CLOSED", "market_id": mid}
                continue
            outs = m.get("outcomes")
            if isinstance(outs, str):
                try: outs = json.loads(outs)
                except Exception: outs = []
            # YES token by NAME (owner law): find the literal "Yes" outcome
            yes_idx = [i for i, o in enumerate(outs or [])
                       if str(o).strip().lower() == "yes"]
            if len(outs or []) != 2 or len(yes_idx) != 1:
                legs[leg] = {"error": "NOT_2WAY_YES_NO", "market_id": mid}
                continue
            tokens = m.get("clobTokenIds")
            if isinstance(tokens, str):
                try: tokens = json.loads(tokens)
                except Exception: tokens = []
            if not isinstance(tokens, list) or len(tokens) != 2:
                legs[leg] = {"error": "TOKENS_MISSING", "market_id": mid}
                continue
            walk = walk_ask(tokens[yes_idx[0]],
                            stake_cents=stake_cents,
                            data_root=self.data_root,
                            sandbox=self.sandbox)
            prices = m.get("outcomePrices")
            if isinstance(prices, str):
                try: prices = json.loads(prices)
                except Exception: prices = None
            indicative[leg] = prices        # display-only, never a quote
            if walk is None:
                legs[leg] = {"error": "DEPTH_SHORT_OR_NO_BOOK",
                             "market_id": mid,
                             "yes_token": str(tokens[yes_idx[0]])}
                continue
            walk["market_id"] = mid
            legs[leg] = walk
        walked = [leg for leg, v in legs.items()
                  if isinstance(v, dict) and v.get("best_ask") is not None]
        if len(walked) < 2:
            return None    # fail-closed: not enough walked legs to quote
        return {"legs": legs, "walked_legs": walked,
                "all_present": len(walked) == 3,
                "event_id": event_id, "event_sha256": raw_sha,
                "indicative_outcome_prices": indicative}


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
