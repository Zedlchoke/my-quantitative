"""AI SCORECARD (PAPERDESK-FIXALL-NCAA-V1 W4.5) — the condition for the AI
layer to be trusted, computed WEEKLY from the ledger + the hash-locked
opinions + the CLV plane:

  * every ALLOW-placed bet  -> its real outcome + CLV;
  * every VETO              -> the HYPOTHETICAL outcome had the bet been
    placed (stake law at the candidate's own frozen quote; the real final
    result from the ledger) — the money the AI kept or the money it cost;
  * aggregates: reviews, VETO rate, NET VALUE of the AI layer
    (PnL kept = placed realized − what the VETOED set would have netted).

DOWNGRADE LAW (suggest-only): after >= 100 SCORED reviews, if the VETO
class is not meaningfully better than the ALLOW class, the scorecard
WRITES A PROPOSAL to demote AI authority back to SHADOW — only the owner
ever decides (the system suggests, never acts).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _result_pnl(stake_cents: int, decimal_odds: float,
                result: str, leg: str, actual_result: str) -> int:
    """The frozen settle law, applied hypothetically: win +stake*(d-1);
    lose -stake; VOID/PUSH/CANCELLED/POSTPONED refund 0."""
    if result in ("VOID", "PUSH", "CANCELLED", "POSTPONED_NO_RESCHEDULE"):
        return 0
    won = (leg == actual_result)
    return int(round(stake_cents * (decimal_odds - 1))) if won \
        else -int(stake_cents)


def compute_scorecard(*, ledger_rows: list[dict], opinions_dir: Path,
                      min_scored_for_downgrade: int = 100) -> dict:
    opinions = []
    for f in sorted(Path(opinions_dir).glob("*.json")):
        try:
            opinions.append(json.loads(f.read_text()))
        except json.JSONDecodeError:
            continue
    by_hash = {op.get("candidate_hash"): op for op in opinions
               if op.get("candidate_hash")}
    decisions = [r for r in ledger_rows if r.get("type") == "DECISION"]
    settlements = {}
    for r in ledger_rows:
        if r.get("type") == "SETTLEMENT":
            settlements[r.get("decision_row_sha256")] = r
    quotes_by_mid = {}
    for r in ledger_rows:
        if r.get("type") == "MARKET_QUOTE":
            quotes_by_mid.setdefault(r.get("match_id"), r)

    # results per match (from the SETTLEMENT source law: result token)
    results_by_mid = {}
    for r in ledger_rows:
        if r.get("type") == "SETTLEMENT":
            results_by_mid[r.get("match_id")] = r.get("result")

    scored, veto_scored, allow_scored = [], [], []
    for dec in decisions:
        gate = dec.get("ai_gate") or {}
        chash = gate.get("candidate_hash")
        if not chash:
            continue
        op = by_hash.get(chash)
        if not op:
            continue
        mid = dec.get("match_id")
        result = results_by_mid.get(mid)
        entry = {"match_id": mid, "verdict": op.get("verdict"),
                 "status": dec.get("status"),
                 "result": result,
                 "opinion_created_at_utc": op.get("created_at_utc")}
        if op.get("verdict") == "ALLOW" and \
                dec.get("status") == "BET_PAPER":
            # the placed bet's realized PnL via its own settlement row
            sha = next((r.get("decision_row_sha256") for r in ledger_rows
                        if r.get("type") == "SETTLEMENT"
                        and r.get("match_id") == mid), None)
            entry["pnl_cents"] = (settlements.get(sha) or {})                .get("pnl_cents")
            allow_scored.append(entry)
            scored.append(entry)
        elif op.get("verdict") == "VETO":
            # hypothetical: what would the vetoed candidate have done?
            # the gate froze the candidate's stake/leg/odds at VETO time
            leg = gate.get("hypothetical_leg")
            stake = gate.get("hypothetical_stake_cents")
            odds = gate.get("hypothetical_decimal_odds")
            if result and leg and stake and odds:
                entry["hypothetical_pnl_cents"] = _result_pnl(
                    int(stake), float(odds), result, leg, result)
            veto_scored.append(entry)
            scored.append(entry)

    placed_real = sum(e.get("pnl_cents") or 0 for e in allow_scored
                      if isinstance(e.get("pnl_cents"), int))
    veto_hypo = sum(e.get("hypothetical_pnl_cents") or 0
                    for e in veto_scored
                    if isinstance(e.get("hypothetical_pnl_cents"), int))
    n = len(scored)
    out = {
        "generated_at_utc": _now(),
        "schema": "ai_scorecard@1",
        "reviews_scored": n,
        "allow_placed": len(allow_scored),
        "veto_reviewed": len(veto_scored),
        "veto_rate": (len(veto_scored) / n) if n else None,
        "placed_realized_pnl_cents": placed_real,
        "vetoed_hypothetical_pnl_cents": veto_hypo,
        "net_value_of_ai_layer_cents": placed_real - veto_hypo,
        "law": "net = placed realized − what the VETOED set would have "
               "netted (positive = the AI layer added value)",
    }
    if n >= min_scored_for_downgrade:
        veto_bad = veto_hypo < 0          # the vetoed set would have LOST
        out["downgrade_proposal"] = {
            "eligible": True,
            "suggest_demote_to_shadow": (not veto_bad) and veto_hypo >= 0,
            "law": ("after >= 100 scored reviews: if the VETO class is "
                    "not better than ALLOW (net kept <= 0), PROPOSE "
                    "demotion to SHADOW — owner decides, system suggests "
                    "only (W4.5)"),
            "evidence_cents": {"placed_real": placed_real,
                               "vetoed_hypothetical": veto_hypo},
        }
    else:
        out["downgrade_proposal"] = {"eligible": False,
                                     "scored": n,
                                     "needed": min_scored_for_downgrade}
    return out
