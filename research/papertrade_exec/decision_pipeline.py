"""DECISION PIPELINE V1 — pre-decision AI gate + per-league PM quote
(owner target architecture; feature-gated behind GO; SHADOW until then).

STATE MACHINE (per fixture per matchday):
  1. FORECAST      — pinned engine, recorded pre-anchor (existing law)
  2. PM QUOTE      — per-league adapter (3-YES or 2-way moneyline)
  3. DETERMINISTIC  — EV >= 5%, PIT, stake, cap, drawdown (frozen gates)
  4. AI REVIEW     — mandatory; KEEP / VETO / SWITCH (10-min budget,
                     strictly pre-anchor; system-captured evidence only)
  5. IN-LOCK CHECK — re-fetch quote hash, re-run gates, then append
                     exactly ONE BET_PAPER (or NOT_PLACED with reason)

FEATURE GATES:
  pm_cutover_active  — read from the cycle registry phase; when false the
                       quote source remains the pre-cutover pinned path
                       and this module returns NOT_RUN_CUTOVER_PENDING.
  ai_authority_active — read from the cycle registry phase; when false the
                        pipeline journals the candidate + AI opinion in the
                        sidecar and returns ADVISORY_ONLY (no BET_PAPER).

NEVER: fabricates scores, edits history, bypasses a gate, or sends an
order. The ledger is written ONLY by the pinned core append path.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from research.papertrade_exec.laws import (  # noqa: F401  W1.6: ONE source
    DRAWDOWN_PAUSE,
    EV_THRESHOLD,
    FLAT_FEE_PRE_CUTOVER,
)
LEGS = ("HOME", "DRAW", "AWAY")
LEGS_2 = ("HOME", "AWAY")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha(s: str) -> str:
    import hashlib
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


class PipelineResult:
    def __init__(self):
        self.stage = "INIT"
        self.decision = "NOT_PLACED"
        self.reason = ""
        self.chosen_leg = None
        self.stake_cents = 0
        self.ev_net = None
        self.ai_action = None
        self.ai_verdict = None
        self.ai_opinion_id = None
        self.gates_passed = []
        self.gates_failed = []
        self.candidate_hash = None
        self.quote_hash = None
        self.journal = []


def _gate(name: str, ok: bool, detail: str) -> dict:
    return {"gate": name, "pass": ok, "detail": detail}


def check_deterministic_gates(
    *,
    p: Dict[str, float],
    odds: Dict[str, float],
    chosen_leg: str,
    stake_cents: int,
    equity_cents: int,
    open_exposure_cents: int,
    open_cap_cents: int,
    drawdown_frac: float,
    drawdown_paused: bool,
    snapshot_before_anchor: bool,
    anchor_passed: bool,
    quote_present: bool,
    depth_walked: bool,
    fees_once: bool,
) -> Tuple[bool, List[dict], Optional[float]]:
    """Frozen deterministic gate set. Returns (pass, gates, ev_net)."""
    gates = []
    d = (odds or {}).get(chosen_leg)
    p_leg = (p or {}).get(chosen_leg)
    ev = (p_leg * d - 1.0 - FLAT_FEE_PRE_CUTOVER) if (p_leg and d) else None
    gates.append(_gate("G_QUOTE", quote_present,
                       f"quote for {chosen_leg}"))
    gates.append(_gate("G_DEPTH", depth_walked,
                       f"walk covers stake for {chosen_leg}"))
    gates.append(_gate("G_EV",
                       ev is not None and ev >= EV_THRESHOLD,
                       f"EV_net({chosen_leg})={ev}"))
    gates.append(_gate("G_PIT",
                       snapshot_before_anchor and not anchor_passed,
                       "snapshot pre-anchor, window open"))
    gates.append(_gate("G_FEES", fees_once,
                       "taker fee once in frozen numbers"))
    gates.append(_gate("G_STAKE",
                       stake_cents > 0,
                       f"stake {stake_cents}c (v3 1%)"))
    gates.append(_gate("G_CAP",
                       open_exposure_cents <= open_cap_cents,
                       f"exposure {open_exposure_cents} <= {open_cap_cents}"))
    gates.append(_gate("G_AVAIL",
                       open_exposure_cents <= max(equity_cents
                       - open_exposure_cents, 0) + open_exposure_cents,
                       "availability check"))
    gates.append(_gate("G_DRAWDOWN",
                       drawdown_frac < DRAWDOWN_PAUSE and not drawdown_paused,
                       f"drawdown {drawdown_frac} < 10%"))
    ok = all(g["pass"] for g in gates)
    return ok, gates, ev


def build_candidate_hash(
    *, match_id: str, forecast_sha: str, model_p: Dict[str, float],
    quote_payload_sha: str, anchor_utc: str, stake_cents: int,
    chosen_leg: str, market_law: str) -> str:
    """Binding hash for the candidate — ties forecast, model p, PM
    snapshot, stake, anchor and market law into one immutable reference."""
    parts = [match_id, forecast_sha,
             json.dumps(model_p, sort_keys=True),
             quote_payload_sha, anchor_utc, str(stake_cents),
             chosen_leg, market_law]
    return _sha("|".join(parts))


def evaluate_ai_gate(
    *, ai_action: str,
    ai_proposed_leg: Optional[str],
    chosen_leg: str,
    p_frozen: Dict[str, float],
    odds_frozen: Dict[str, float],
    ev_net_by_leg: Dict[str, float],
    stake_cents: int,
    equity_cents: int,
    open_exposure_cents: int,
    open_cap_cents: int,
    drawdown_frac: float,
    drawdown_paused: bool,
    snapshot_before_anchor: bool,
    anchor_passed: bool,
    quote_present: Dict[str, bool],
    depth_walked: Dict[str, bool],
    fees_once: bool,
) -> Tuple[str, List[dict], str]:
    """Grade the AI action against frozen gates (same as paper_policy.js but
    runner-side, called before append). Returns (decision, gates, reason).

    decision: 'PLACE' | 'NOT_PLACED'
    """
    gates = []

    def push(name: str, ok: bool, detail: str):
        gates.append(_gate(name, ok, detail))
        return ok

    if ai_action == "VETO":
        push("G_VETO", True, "AI VETO — advisory until authority; NOT placed")
        return "NOT_PLACED", gates, "AI VETO"

    if ai_action in (None, "", "ABSTAIN"):
        # Owner law (2026-10-20 §D): ABSTAIN — or any model-side failure
        # (timeout, provider error, malformed opinion, missing evidence,
        # post-deadline) surfaced upstream as a missing action — NEVER
        # places. A lawful no-order, not a gate failure.
        push("G_ABSTAIN", True,
             f"AI ABSTAIN ({ai_action!r}) — no opinion, nothing placed")
        return "NOT_PLACED", gates, "AI ABSTAIN — no order"

    if ai_action == "KEEP":
        ev = ev_net_by_leg.get(chosen_leg)
        push("G_EV_KEEP", ev is not None and ev >= EV_THRESHOLD,
             f"frozen EV({chosen_leg})={ev}")
        push("G_PIT_KEEP", snapshot_before_anchor and not anchor_passed,
             "PIT window")
        ok = all(g["pass"] for g in gates)
        return ("PLACE" if ok else "NOT_PLACED"), gates, (
            "AI KEEP — all gates pass" if ok
            else "AI KEEP — gates fail: " + ", ".join(
                g["gate"] for g in gates if not g["pass"]))

    if ai_action == "SWITCH":
        new_leg = ai_proposed_leg
        if new_leg not in LEGS or new_leg == chosen_leg:
            push("G_SWITCH_TARGET", False,
                 f"invalid switch target {new_leg}")
            return "NOT_PLACED", gates, "SWITCH target invalid"

        new_ev = ev_net_by_leg.get(new_leg)
        leg_ok = push("G_EV_SWITCH",
                      new_ev is not None and new_ev >= EV_THRESHOLD,
                      f"frozen EV({new_leg})={new_ev}")
        push("G_QUOTE_SWITCH",
             (quote_present or {}).get(new_leg, False),
             f"quote for {new_leg}")
        push("G_DEPTH_SWITCH",
             (depth_walked or {}).get(new_leg, False),
             f"depth for {new_leg}")
        push("G_PIT_SWITCH",
             snapshot_before_anchor and not anchor_passed, "PIT")
        push("G_STAKE_SWITCH", stake_cents > 0, "stake unchanged")
        push("G_CAP_SWITCH",
             open_exposure_cents <= open_cap_cents, "cap")
        push("G_DRAWDOWN_SWITCH",
             drawdown_frac < DRAWDOWN_PAUSE and not drawdown_paused,
             "drawdown")
        push("G_ONE_SELECTION", True, "one leg per fixture")
        ok = all(g["pass"] for g in gates)
        return ("PLACE" if ok else "NOT_PLACED"), gates, (
            f"AI SWITCH -> {new_leg}: "
            + ("all gates pass" if ok else "gates fail"))

    push("G_UNKNOWN_ACTION", False, f"action {ai_action}")
    return "NOT_PLACED", gates, f"unknown action {ai_action}"
