"""AI SCORECARD V2 (PAPERDESK-FIXALL-NCAA-V1 W4.5; truth laws re-based by
UPGRADE V2 U2, owner work package 2026-10-21) — the condition for the AI
layer to be trusted, computed WEEKLY from the ledger + the hash-locked
opinions (+ optional results plane + gate-event journal):

TRUTH LAWS (U2):
  1. VETO-class ACTUAL results come from the RESULTS PLANE: the ledger's
     SETTLEMENT row for the match when present; otherwise the caller-passed
     `results_by_mid` (dict match_id -> result token, e.g. from the
     ESPN/UMA plane). A blocked match never settles (that IS the H2 root:
     no decision row -> no settlement), so the settlement alone can never
     score the VETO class. A veto with NO obtainable final result is
     UNSCORED: excluded from the review denominator, reported separately as
     `unscored_vetoes`.
  2. Headline: `ai_layer_value_cents = −vetoed_hypothetical_pnl_cents` —
     counterfactual-correct: what the AI layer SAVED. The data value
     `net_value_of_ai_layer_cents = placed_realized − vetoed_hypothetical`
     is kept alongside. The downgrade proposal is gated on
     `DOWNGRADE_MIN_SCORED = 100` counted ONLY over vetoes with a real
     final result (`veto_scored_actual`) — suggest-only, owner decides.
  3. Also counted: `not_placed_no_verdict` decisions (silence law) with
     their hypothetical PnL when the frozen gate-block evidence is present;
     `invalid_opinions` (files under opinions_dir/.invalid); gate events
     from `<data_root>/ai_review/gate_events.jsonl` when the caller passes
     `gate_events_path` — verdicts aggregated per model.
  4. Breakdowns: per league (decision rows), per model (opinion model_id),
     per reason_code (incl. the share of INSUFFICIENT_EVIDENCE).

The hypothetical money uses THE FROZEN SETTLE LAW (pinned risk.settle):
win +stake·(d−1); lose −stake; VOID/PUSH/CANCELLED/POSTPONED refund 0 —
stake/leg/odds frozen at VETO time in the decision row's ai_gate block.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

DOWNGRADE_MIN_SCORED = 100          # veto_scored_actual gate (suggest-only)

_VOID_RESULTS = ("VOID", "PUSH", "CANCELLED", "POSTPONED_NO_RESCHEDULE")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _result_pnl(stake_cents: int, decimal_odds: float,
                result: str, leg: str, actual_result: str) -> int:
    """The frozen settle law, applied hypothetically: win +stake*(d-1);
    lose -stake; VOID/PUSH/CANCELLED/POSTPONED refund 0."""
    if result in _VOID_RESULTS:
        return 0
    won = (leg == actual_result)
    return int(round(stake_cents * (decimal_odds - 1))) if won \
        else -int(stake_cents)


def _load_gate_events(path: Path | None) -> dict:
    """gate_events.jsonl -> {total, kinds, verdicts_by_model} (best-effort;
    a missing/unreadable journal is reported, never fatal)."""
    out = {"source": str(path) if path else None, "read": False,
           "total": 0, "kinds": {}, "verdicts_by_model": {}}
    if not path:
        return out
    kinds: Counter = Counter()
    by_model: dict = {}
    n = 0
    try:
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                n += 1
                kinds[str(e.get("kind"))] += 1
                if e.get("kind") == "OPINION_PRODUCED":
                    model = str(e.get("model") or "unknown")
                    verdict = str(e.get("verdict") or "").strip().upper()
                    slot = by_model.setdefault(model, Counter())
                    slot[verdict or "UNKNOWN"] += 1
    except OSError:
        return out
    out.update({"read": True, "total": n,
                "kinds": dict(kinds),
                "verdicts_by_model": {m: dict(v) for m, v in
                                      sorted(by_model.items())}})
    return out


def compute_scorecard(*, ledger_rows: list[dict], opinions_dir: Path,
                      min_scored_for_downgrade: int = DOWNGRADE_MIN_SCORED,
                      results_by_mid: dict | None = None,
                      gate_events_path: Path | None = None) -> dict:
    """Compute the AI-layer scorecard under the U2 truth laws. Read-only;
    never writes the ledger; suggests, never acts."""
    opinions_dir = Path(opinions_dir)
    opinions = []
    for f in sorted(opinions_dir.glob("*.json")):
        try:
            op = json.loads(f.read_text())
        except json.JSONDecodeError:
            continue
        if isinstance(op, dict):
            v = str(op.get("verdict") or "").strip().upper()
            if v:
                op = dict(op)
                op["verdict"] = v                     # canonical (L1 law)
            opinions.append(op)
    invalid_opinions = len(list((opinions_dir / ".invalid")
                                .glob("*.json")))
    by_hash = {op.get("candidate_hash"): op for op in opinions
               if op.get("candidate_hash")}

    # --- results plane: ledger SETTLEMENT rows win; the caller's
    # results_by_mid (ESPN/UMA plane) fills the matches the ledger cannot
    # know (a blocked match never settles — H2 root).
    results: dict = {}
    for r in ledger_rows:
        if r.get("type") == "SETTLEMENT" and r.get("match_id"):
            results[r["match_id"]] = r.get("result")
    for mid, res in (results_by_mid or {}).items():
        results.setdefault(str(mid), res)
    settle_by_decision = {}
    for r in ledger_rows:
        if r.get("type") == "SETTLEMENT" and r.get("decision_row_sha256"):
            settle_by_decision[r["decision_row_sha256"]] = r

    allow_entries: list[dict] = []
    veto_scored_entries: list[dict] = []
    unscored_vetoes: list[dict] = []
    no_verdict_rows: list[dict] = []
    per_league: dict = {}
    per_model: dict = {}
    reason_codes: Counter = Counter()

    def _slot(idx, key, league=None):
        return idx.setdefault(key, {"reviews": 0, "allow_placed": 0,
                                    "veto_scored": 0, "veto_unscored": 0,
                                    "league": league})

    for dec in ledger_rows:
        if dec.get("type") != "DECISION":
            continue
        status = dec.get("status")
        league = dec.get("league")
        mid = dec.get("match_id")
        gate = dec.get("ai_gate") or {}

        # --- silence law class (NOT_PLACED_AI_NO_VERDICT): counted, never
        # in the veto denominator; hypothetical PnL when the frozen
        # gate-block evidence shape is present.
        if status == "NOT_PLACED_AI_NO_VERDICT":
            leg = gate.get("hypothetical_leg")
            stake = gate.get("hypothetical_stake_cents")
            odds = gate.get("hypothetical_decimal_odds")
            result = results.get(mid)
            has_evidence = bool(leg and stake and odds)
            row = {"match_id": mid, "league": league,
                   "has_hypothetical_evidence": has_evidence}
            if has_evidence and result:
                row["hypothetical_pnl_cents"] = _result_pnl(
                    int(stake), float(odds), result, leg, result)
            no_verdict_rows.append(row)
            continue

        chash = gate.get("candidate_hash")
        if not chash:
            continue
        op = by_hash.get(chash)
        if not op:
            continue                                  # gated, opinion absent
        verdict = op.get("verdict")
        lslot = _slot(per_league, str(league or "unknown"), league)
        mslot = per_model.setdefault(str(op.get("model_id") or "unknown"),
                                     {"reviews": 0, "allow": 0, "veto": 0})
        for code in (op.get("reason_codes") or []):
            reason_codes[str(code)] += 1
        lslot["reviews"] += 1
        mslot["reviews"] += 1

        if verdict == "ALLOW" and status == "BET_PAPER":
            sha = dec.get("row_sha256")
            st = settle_by_decision.get(sha)
            pnl = st.get("pnl_cents") if st else None
            entry = {"match_id": mid, "league": league,
                     "model_id": op.get("model_id"),
                     "status": status, "pnl_cents": pnl,
                     "opinion_created_at_utc": op.get("created_at_utc")}
            lslot["allow_placed"] += 1
            mslot["allow"] += 1
            allow_entries.append(entry)
        elif verdict == "VETO":
            # the vetoed candidate's own frozen evidence (stake/leg/odds at
            # VETO time) + the RESULTS PLANE final result
            leg = gate.get("hypothetical_leg")
            stake = gate.get("hypothetical_stake_cents")
            odds = gate.get("hypothetical_decimal_odds")
            result = results.get(mid)
            entry = {"match_id": mid, "league": league,
                     "model_id": op.get("model_id"), "status": status,
                     "result": result, "hypothetical_leg": leg,
                     "opinion_created_at_utc": op.get("created_at_utc")}
            if not result:
                entry["unscored_why"] = "no final result on the results " \
                                        "plane (no settlement; none " \
                                        "supplied)"
                unscored_vetoes.append(entry)
                lslot["veto_unscored"] += 1
                continue
            if leg and stake and odds:
                entry["hypothetical_pnl_cents"] = _result_pnl(
                    int(stake), float(odds), result, leg, result)
            else:
                entry["hypothetical_pnl_cents"] = 0
                entry["hypothetical_evidence"] = "missing in the frozen " \
                                                 "gate block (scored 0)"
            veto_scored_entries.append(entry)
            lslot["veto_scored"] += 1
            mslot["veto"] += 1

    # --- headline (U2 law 2) ------------------------------------------------
    placed_real = sum(e["pnl_cents"] for e in allow_entries
                      if isinstance(e.get("pnl_cents"), int))
    veto_hypo = sum(e["hypothetical_pnl_cents"] for e in veto_scored_entries
                    if isinstance(e.get("hypothetical_pnl_cents"), int))
    no_verdict_hypo = sum(r["hypothetical_pnl_cents"]
                          for r in no_verdict_rows
                          if isinstance(r.get("hypothetical_pnl_cents"),
                                        int))
    allow_settled = sum(1 for e in allow_entries
                        if isinstance(e.get("pnl_cents"), int))
    veto_scored_actual = len(veto_scored_entries)

    reason_total = sum(reason_codes.values())
    insuff = reason_codes.get("INSUFFICIENT_EVIDENCE", 0)

    out = {
        "generated_at_utc": _now(),
        "schema": "ai_scorecard@2",
        "reviews_scored": allow_settled + veto_scored_actual,
        "allow_placed": len(allow_entries),
        "allow_settled": allow_settled,
        "allow_open": len(allow_entries) - allow_settled,
        "veto_reviewed": veto_scored_actual + len(unscored_vetoes),
        "veto_scored_actual": veto_scored_actual,
        "unscored_vetoes": len(unscored_vetoes),
        "unscored_veto_match_ids": [e.get("match_id") for e in
                                    unscored_vetoes][:100],
        "veto_rate_scored": (veto_scored_actual /
                             (allow_settled + veto_scored_actual))
            if (allow_settled + veto_scored_actual) else None,
        "placed_realized_pnl_cents": placed_real,
        "vetoed_hypothetical_pnl_cents": veto_hypo,
        "net_value_of_ai_layer_cents": placed_real - veto_hypo,
        "ai_layer_value_cents": -veto_hypo,
        "law": ("ai_layer_value = −(what the VETOED set would have netted) "
                "= what the AI layer SAVED (positive = saved); "
                "net_value = placed realized − vetoed hypothetical (U2 "
                "headline/data pair)"),
        # U2 law 3: the other honest classes
        "not_placed_no_verdict": {
            "count": len(no_verdict_rows),
            "with_evidence_shape": sum(
                1 for r in no_verdict_rows
                if r.get("has_hypothetical_evidence")),
            "scored_hypothetical": sum(
                1 for r in no_verdict_rows
                if isinstance(r.get("hypothetical_pnl_cents"), int)),
            "hypothetical_pnl_cents": no_verdict_hypo,
            "match_ids": [r.get("match_id") for r in
                          no_verdict_rows][:100],
        },
        "invalid_opinions": invalid_opinions,
        "gate_events": _load_gate_events(
            Path(gate_events_path) if gate_events_path else None),
        # U2 law 4: breakdowns
        "per_league": per_league,
        "per_model": per_model,
        "per_reason_code": {
            "codes": dict(reason_codes.most_common()),
            "total": reason_total,
            "INSUFFICIENT_EVIDENCE": insuff,
            "INSUFFICIENT_EVIDENCE_share": (insuff / reason_total)
                if reason_total else None,
        },
    }

    # --- downgrade proposal (suggest-only; U2 denominator law) --------------
    if veto_scored_actual >= min_scored_for_downgrade:
        veto_bad = veto_hypo < 0          # the vetoed set would have LOST
        out["downgrade_proposal"] = {
            "eligible": True,
            "suggest_demote_to_shadow": (not veto_bad) and veto_hypo >= 0,
            "law": ("after >= 100 SCORED VETO reviews (veto_scored_actual, "
                    "vetoes with a real final result only — unscored "
                    "vetoes never count): if the VETO class is not better "
                    "than ALLOW (vetoed hypothetical net >= 0), PROPOSE "
                    "demotion to SHADOW — owner decides, system suggests "
                    "only (W4.5, U2)"),
            "denominator": {"veto_scored_actual": veto_scored_actual,
                            "unscored_vetoes_excluded":
                                len(unscored_vetoes)},
            "evidence_cents": {"placed_real": placed_real,
                               "vetoed_hypothetical": veto_hypo},
        }
    else:
        out["downgrade_proposal"] = {
            "eligible": False,
            "scored": veto_scored_actual,
            "needed": min_scored_for_downgrade,
            "law": ("denominator = veto_scored_actual (vetoes with a real "
                    "final result only); unscored_vetoes excluded (U2)"),
        }
    return out
