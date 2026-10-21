"""AI GATE V2 — THE single AI authority boundary (PAPERDESK-FIXALL-NCAA-V1
W4, owner work package 2026-10-21).

Owner spec (QĐ2/QĐ4 + W4.1–W4.6):
  * ONE gate, in the decide path, for EVERY league (WSL included) — the JS
    pieces only display and collect.
  * Every BET_PAPER candidate MUST have an AI review bound to ITS candidate
    hash before the append; any price/EV/model change changes the hash and
    voids the old review.
  * Exactly two lawful verdicts: ALLOW | VETO. Anything else (SWITCH,
    CHALLENGE, ALTERNATIVE, ABSTAIN, garbage, missing) is INVALID — never
    actionable.
  * Silence is NOT death: no valid verdict while the review window is open
    => the candidate sits PENDING_AI (visible on the dashboard) and is
    re-reviewed every cadence pass until (anchor - 30min); past that
    deadline => NOT_PLACED_AI_NO_VERDICT terminal + incident. The AI layer
    never kills a bet inside the silence window.
  * Research is REAL: an opinion is only valid with sources actually
    captured (url + fetched_at + excerpt); zero sources is a LAWFUL reason
    to refuse (insufficient evidence), recorded as such.

FILES (under <data-root>/ai_review/):
  opinions_v2/<match_id>_<candidate_hash>.json   hash-locked opinions
  pending.json                                   the PENDING_AI queue
  gate_events.jsonl                              append-only gate journal

This module NEVER writes the ledger; the decide path appends.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

AI_VERDICTS = ("ALLOW", "VETO")
PENDING_WINDOW_MIN = 30          # re-review until anchor - 30min
PROVIDER_DOWN_ALARM_MIN = 30     # pending this long => high alarm to owner

PROMPT_VERSION = "AI_PROMPT_V2"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc)


def ai_review_dir(data_root: Path) -> Path:
    return Path(data_root) / "ai_review"


def candidate_hash_for(dec: dict, fc_row: dict | None,
                       quote_row: dict | None) -> str:
    """The SAME binding hash law as decision_pipeline.build_candidate_hash —
    fixture + forecast + model p + quote snapshot + anchor + stake + leg +
    market law. Any number change => a different hash => the old opinion is
    void (W4.2)."""
    from research.papertrade_exec.decision_pipeline import \
        build_candidate_hash
    fc_sha = (fc_row or {}).get("row_sha256") or ""
    return build_candidate_hash(
        match_id=str(dec.get("match_id")),
        forecast_sha=fc_sha,
        model_p=dict(dec.get("p_frozen") or {}),
        quote_payload_sha=str((quote_row or {}).get("payload_sha256")
                              or ""),
        anchor_utc=str(dec.get("anchor_utc") or ""),
        stake_cents=int(dec.get("stake_cents") or 0),
        chosen_leg=str(dec.get("chosen_leg")),
        market_law=str((quote_row or {}).get("market") or ""))


def validate_opinion(op: dict) -> tuple[bool, str]:
    """Hard schema: {verdict: ALLOW|VETO, reason_codes: [..], summary,
    sources: [{url, fetched_at_utc, excerpt}]}. Verdicts outside the two
    (SWITCH/CHALLENGE/ALTERNATIVE/ABSTAIN/…) are INVALID — never mapped,
    never salvaged."""
    if not isinstance(op, dict):
        return False, "opinion is not an object"
    verdict = str(op.get("verdict") or "").strip().upper()
    if verdict not in AI_VERDICTS:
        return False, (f"verdict {verdict!r} outside the lawful set "
                       f"{AI_VERDICTS} (SWITCH/CHALLENGE/ALTERNATIVE/"
                       "ABSTAIN are not actionable under owner law)")
    if verdict == "ALLOW" and not op.get("reason_codes"):
        return False, "ALLOW without reason_codes"
    if verdict == "VETO" and not op.get("reason_codes"):
        return False, "VETO without reason_codes"
    if not str(op.get("summary") or "").strip():
        return False, "missing summary"
    sources = op.get("sources")
    if not isinstance(sources, list):
        return False, "sources missing"
    for s in sources:
        if not isinstance(s, dict) or not s.get("url") or \
                not s.get("fetched_at_utc"):
            return False, ("a source lacks url/fetched_at_utc (citations "
                           "law)")
    if verdict == "ALLOW" and not sources:
        return False, ("ALLOW with ZERO captured sources — insufficient "
                       "evidence is a refusal reason, not an approval")
    if not op.get("candidate_hash"):
        return False, "opinion not bound to a candidate hash"
    if not op.get("prompt_sha256"):
        return False, "opinion missing the frozen prompt hash"
    return True, "valid"


def load_opinion_for(data_root: Path, match_id: str,
                     candidate_hash: str) -> tuple[dict | None, str]:
    """The hash-locked opinion, validated. Returns (opinion|None, why)."""
    d = ai_review_dir(data_root) / "opinions_v2"
    f = d / f"{match_id}_{candidate_hash}.json"
    if not f.exists():
        return None, f"no opinion bound to candidate hash {candidate_hash[:12]}"
    try:
        op = json.loads(f.read_text())
    except json.JSONDecodeError as e:
        return None, f"opinion unreadable: {e}"
    if str(op.get("candidate_hash")) != str(candidate_hash):
        return None, "opinion hash mismatch (stale review)"
    ok, why = validate_opinion(op)
    if not ok:
        return None, why
    return op, "valid"


def record_opinion(data_root: Path, op: dict) -> Path:
    """Write (or overwrite) the hash-locked opinion file. The JS sidecar
    produces the opinion; this is the sanctioned writer (schema-checked
    before persist — an invalid opinion is stored under .invalid/ for the
    scorecard, never consumed by the gate)."""
    d = ai_review_dir(data_root) / "opinions_v2"
    d.mkdir(parents=True, exist_ok=True)
    ok, why = validate_opinion(op)
    if not ok:
        bad = d / ".invalid"
        bad.mkdir(exist_ok=True)
        p = bad / f"{op.get('match_id')}_{op.get('candidate_hash')}.json"
        p.write_text(json.dumps({"invalid_reason": why, **op}, indent=1,
                                sort_keys=True, default=str))
        raise ValueError(f"invalid opinion refused: {why}")
    p = d / f"{op['match_id']}_{op['candidate_hash']}.json"
    p.write_text(json.dumps(op, indent=1, sort_keys=True, default=str))
    return p


# ------------------------------------------------------------- pending law --

def _pending_path(data_root: Path) -> Path:
    return ai_review_dir(data_root) / "pending.json"


def _load_pending(data_root: Path) -> dict:
    try:
        return json.loads(_pending_path(data_root).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_pending(data_root: Path, pending: dict) -> None:
    p = _pending_path(data_root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(pending, indent=1, sort_keys=True, default=str))


def gate_event(data_root: Path, kind: str, **fields) -> None:
    p = ai_review_dir(data_root) / "gate_events.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a") as f:
        f.write(json.dumps({"ts_utc": _now(), "kind": kind, **fields},
                           sort_keys=True, default=str) + "\n")


def pending_marker(data_root: Path, match_id: str, candidate_hash: str,
                   anchor_utc: str, detail: str) -> None:
    """Record/refresh the PENDING_AI entry (the dashboard 'chờ AI' block
    reads this). The bet stays UNDECIDED — retried on the next cadence
    pass (the 15-min cadence throttle is the re-review rhythm)."""
    pending = _load_pending(data_root)
    prev = pending.get(match_id) or {}
    pending[match_id] = {
        "candidate_hash": candidate_hash,
        "anchor_utc": anchor_utc,
        "first_pending_utc": prev.get("first_pending_utc") or _now(),
        "last_attempt_utc": _now(),
        "attempts": int(prev.get("attempts") or 0) + 1,
        "last_detail": detail[:240],
    }
    _save_pending(data_root, pending)
    gate_event(data_root, "PENDING_AI", match_id=match_id,
               candidate_hash=candidate_hash, detail=detail[:200])


def clear_pending(data_root: Path, match_id: str, outcome: str) -> None:
    pending = _load_pending(data_root)
    if match_id in pending:
        del pending[match_id]
        _save_pending(data_root, pending)
    gate_event(data_root, outcome, match_id=match_id)


def pending_alarm_owners(data_root: Path) -> list[dict]:
    """PENDING entries older than PROVIDER_DOWN_ALARM_MIN — the ops layer
    turns these into AI_PROVIDER_DOWN alarms (the whole AI layer failing
    is a W4.4 owner alarm, never a silent bet-killer)."""
    pending = _load_pending(data_root)
    now = _now()
    out = []
    for mid, e in pending.items():
        try:
            delta = _parse(now) - _parse(e["first_pending_utc"])
            age_min = delta.total_seconds() / 60.0
        except (KeyError, ValueError):
            continue
        if age_min >= PROVIDER_DOWN_ALARM_MIN:
            out.append({"match_id": mid, "age_min": round(age_min, 1),
                        **e})
    return out


def review_deadline_passed(anchor_utc: str, now: str) -> bool:
    """The review window closes at anchor - PENDING_WINDOW_MIN."""
    try:
        return _parse(now) >= _parse(anchor_utc) - \
            timedelta(minutes=PENDING_WINDOW_MIN)
    except (ValueError, TypeError):
        return True                          # malformed anchor: fail-closed


def ai_gate_block(op: dict | None, why: str, decision: str,
                  candidate_hash: str) -> dict:
    """The evidence block embedded in the DECISION row (audit trail)."""
    return {"gate": "ai_gate_v2", "decision": decision,
            "candidate_hash": candidate_hash,
            "opinion_verdict": (op or {}).get("verdict"),
            "opinion_why": why[:240],
            "opinion_sources": [s.get("url") for s in
                                ((op or {}).get("sources") or [])][:8],
            "prompt_version": PROMPT_VERSION,
            "model_id": (op or {}).get("model_id")}
