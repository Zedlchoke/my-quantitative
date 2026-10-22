"""NEW-LAW SHADOW evaluator (PAPERDESK UPGRADE V2 U7) — LOG ONLY.

Computes what the FROZEN new-era law (research/control/
PAPERDESK-FIXALL-NCAA-V1/NEW_LAW_SPEC_FROZEN_V1.md, sha registered in its
header) WOULD do for the same inputs a real decision sees — forecast p,
PM quote legs, Pinnacle reference quote, chosen leg — and journals one
line per candidate to <data>/ops/shadow_new_law.jsonl (sandbox:
<data>/sandbox/ops/shadow_new_law.jsonl). It changes NO production
decision, writes no ledger row, reads no gate: pure parallel bookkeeping
so the new era can be scored on FUTURE data once the owner GO lands.

Constants below mirror the frozen spec verbatim. The blend weight is NOT a
fit — the spec freezes the fitting PROTOCOL, so the shadow journals the
blend COMPONENTS (p_model, p_pin_novig) plus the blended EV at the
provisional identity weight 0.5, clearly labeled; any locked w can be
re-applied offline from the journal.

All failures are NO_RUN records with a reason — never invented, never
retried, never a production effect.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from research.papertrade_exec.clv_plane import no_vig_probabilities

SCHEMA = "shadow_new_law@1"
JOURNAL_NAME = "shadow_new_law.jsonl"

# FROZEN (spec §2): sharp-price margin, PM-fee-adjusted.
SHARP_PRICE_MARGIN = 0.03
# FROZEN (spec §4): disagreement-scaled edge threshold.
EDGE_BASE = 0.05
EDGE_DISAGREEMENT_K = 0.5
# PM taker fee law (pinned): 0.05*p*(1-p) per share, applied ONCE.
PM_TAKER_FEE = 0.05
# NOT A FIT (spec §3): provisional identity weight until the owner's
# locked fit exists; the components travel in every record.
PROVISIONAL_W = 0.5


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def shadow_journal_path(data_root: Path, sandbox: bool = False) -> Path:
    return Path(data_root) / ("sandbox/ops" if sandbox else "ops") / \
        JOURNAL_NAME


def _logit(p: float) -> float:
    return math.log(p / (1.0 - p))


def _logit_inv(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def evaluate(*, p: dict, pm_odds: dict | None, pin_odds: dict | None,
             chosen_leg: str | None,
             w: float = PROVISIONAL_W) -> dict:
    """The NEW law for ONE candidate. p = model probabilities;
    pm_odds/pin_odds = DECIMAL quote legs (PM = the price being taken,
    pin = the no-vig reference); chosen_leg = the leg the decision froze
    (None -> the shadow still evaluates the best leg honestly)."""
    rec = {"w_provisional": w, "edge_base": EDGE_BASE,
           "edge_k": EDGE_DISAGREEMENT_K,
           "sharp_price_margin": SHARP_PRICE_MARGIN}
    legs = sorted((p or {}).keys())
    if not chosen_leg:
        best = None
        for leg in legs:                       # honest best-leg scan
            r = evaluate(p=p, pm_odds=pm_odds, pin_odds=pin_odds,
                         chosen_leg=leg, w=w)
            if r.get("action") == "TAKE" and \
                    (best is None or
                     (r.get("ev_blend") or -9) > (best.get("ev_blend") or -9)):
                best = r
        if best is not None:
            best["leg_selection"] = "shadow_best_leg"
        return best or {"action": "NO_RUN",
                        "why": "no evaluable leg (chosen_leg absent)",
                        **rec}
    leg = str(chosen_leg)
    if leg not in (p or {}):
        return {"action": "NO_RUN", "why": f"leg {leg} absent from model p",
                **rec}
    p_model = float(p[leg])
    nv = no_vig_probabilities(pin_odds or {})
    if nv is None or leg not in nv:
        return {"action": "NO_RUN",
                "why": "pinnacle reference degenerate or leg absent", **rec}
    try:
        dec = float((pm_odds or {})[leg])
    except (KeyError, TypeError, ValueError):
        return {"action": "NO_RUN", "why": "pm quote leg absent", **rec}
    if not dec > 1.0:
        return {"action": "NO_RUN", "why": f"degenerate pm decimal {dec}",
                **rec}
    p_pin = float(nv[leg])
    p_pm = 1.0 / dec
    p_pm_eff = p_pm + PM_TAKER_FEE * p_pm * (1.0 - p_pm)   # fee once
    rec.update({"leg": leg, "p_model": round(p_model, 6),
                "pin_novig": {k: round(v, 6) for k, v in nv.items()},
                "pm_decimal": round(dec, 6), "p_pm": round(p_pm, 6),
                "p_pm_fee_adjusted": round(p_pm_eff, 6),
                "p_pin_leg": round(p_pin, 6)})
    # §2 sharp-price gate: take the PM price only when BETTER than the
    # no-vig pin reference by the frozen margin (fee-adjusted).
    if p_pm_eff > p_pin * (1.0 - SHARP_PRICE_MARGIN):
        return {"action": "SKIP", "why": "SHARP_PRICE_GATE",
                **rec}
    # §3 blended probability: log-odds blend of MODEL and PIN no-vig —
    # NEVER the PM price being taken.
    p_blend = _logit_inv(w * _logit(min(max(p_model, 1e-9), 1 - 1e-9))
                         + (1.0 - w) * _logit(min(max(p_pin, 1e-9),
                                                  1 - 1e-9)))
    disagreement = abs(p_model - p_pin)
    threshold = EDGE_BASE + EDGE_DISAGREEMENT_K * disagreement
    ev_blend = p_blend - p_pm_eff
    rec.update({"p_blend": round(p_blend, 6),
                "disagreement": round(disagreement, 6),
                "threshold": round(threshold, 6),
                "ev_blend": round(ev_blend, 6)})
    rec["action"] = "TAKE" if ev_blend >= threshold else "SKIP"
    rec["why"] = ("EDGE_OK" if rec["action"] == "TAKE" else "EDGE_BELOW")
    return rec


def shadow_key(league: str, match_id: str, leg: str, result: dict) -> str:
    """Dedup key: the same (league, match, leg, frozen inputs) is shadowed
    ONCE — an hourly tick never floods the journal with repeats."""
    basis = json.dumps({"league": league, "match_id": match_id,
                        "leg": leg,
                        "p": result.get("p_model"),
                        "pm": result.get("pm_decimal"),
                        "pin": result.get("p_pin_leg")}, sort_keys=True)
    return hashlib.sha256(basis.encode()).hexdigest()[:16]


def shadow_recent_decisions(*, ledger_rows, data_root, sandbox: bool = False,
                            now_utc: datetime | None = None) -> dict:
    """Walk the verified ledger rows and journal ONE shadow record per
    FORECAST match that has a chosen leg + both quote planes (the same
    inputs a real decision froze). Read-only over the ledger; the journal
    is the only write. Returns a summary for the ops tick."""
    now_utc = now_utc or datetime.now(timezone.utc)
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=timezone.utc)
    jpath = shadow_journal_path(data_root, sandbox)
    jpath.parent.mkdir(parents=True, exist_ok=True)
    seen: set = set()
    if jpath.exists():
        for line in jpath.read_text().splitlines():
            try:
                seen.add(json.loads(line).get("shadow_key"))
            except json.JSONDecodeError:
                continue
    fc: dict = {}
    bets: dict = {}
    pin_q: dict = {}
    pm_q: dict = {}
    for r in ledger_rows or []:
        mid = str(r.get("match_id") or "")
        t = r.get("type")
        if t == "FORECAST":
            fc[mid] = r
        elif t == "DECISION" and r.get("status") == "BET_PAPER":
            bets[mid] = r
        elif t == "MARKET_QUOTE" and r.get("odds"):
            is_pin = str(r.get("bookmaker")) == "pinnacle"
            idx = pin_q if is_pin else pm_q
            prev = idx.get(mid)
            if prev is None or str(r.get("fetch_ts_utc") or "") >= \
                    str(prev.get("fetch_ts_utc") or ""):
                idx[mid] = r
    summary = {"evaluated": 0, "take": 0, "skip": 0, "no_run": 0,
               "journal": str(jpath)}
    for mid, f in sorted(fc.items()):
        bet = bets.get(mid) or {}
        p_vec = f.get("p") or {}
        leg = bet.get("chosen_leg")
        if not leg and p_vec:
            leg = sorted(p_vec.items(),
                         key=lambda kv: -float(kv[1] or 0))[0][0]
        if not leg:
            continue
        pq = pin_q.get(mid) or {}
        mq = pm_q.get(mid) or {}
        try:
            res = evaluate(p=f.get("p") or {},
                           pm_odds=(mq.get("odds") or {}) or None,
                           pin_odds=(pq.get("odds") or {}) or None,
                           chosen_leg=leg)
        except Exception as e:                 # never break the tick
            res = {"action": "NO_RUN",
                   "why": f"evaluate error: {type(e).__name__}: {e}"[:200]}
        key = shadow_key(str(f.get("league") or ""), mid, str(leg), res)
        if key in seen:
            continue
        seen.add(key)
        row = {"schema": SCHEMA, "ts_utc": _now(),
               "league": f.get("league") or "", "match_id": mid,
               "shadow_key": key,
               "note": "SHADOW ONLY — no production decision (U7)",
               **res}
        with open(jpath, "a") as fh:
            fh.write(json.dumps(row, sort_keys=True, default=str) + "\n")
        summary["evaluated"] += 1
        summary[row["action"].lower()] += 1
    return summary
