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

import fcntl
import hashlib
import json
import os
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


def ai_review_dir(data_root: Path, sandbox: bool = False) -> Path:
    """M6 (U4): the ai_review plane honors the SANDBOX separation — a
    sandbox decide/producer/ops NEVER touches a byte of the real plane.
    sandbox=True  -> <data-root>/sandbox/ai_review
    sandbox=False -> <data-root>/ai_review  (the REAL plane; default)."""
    base = Path(data_root)
    if sandbox:
        return base / "sandbox" / "ai_review"
    return base / "ai_review"


def atomic_write_json(path: Path, obj) -> None:
    """M8 (U4): the durable-writer law for plane state files (pending.json,
    cascade_state.json): write tmp + os.replace (atomic on POSIX) while
    holding an fcntl.flock on a companion <name>.lock file, so concurrent
    writers (decide pass, producer pass, ops tick) serialize instead of
    interleaving partial files. A crash mid-write leaves the previous
    bytes intact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(path.suffix + ".lock")
    with open(lock_path, "a+") as lf:
        fcntl.flock(lf.fileno(), fcntl.LOCK_EX)
        try:
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_text(json.dumps(obj, indent=1, sort_keys=True,
                                      default=str))
            os.replace(tmp, path)
        finally:
            fcntl.flock(lf.fileno(), fcntl.LOCK_UN)


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
        if not str(s.get("excerpt") or "").strip():
            return False, ("a source lacks an excerpt (citations law — "
                           "url+time alone is not a citation, U0)")
    if verdict == "ALLOW" and not sources:
        return False, ("ALLOW with ZERO captured sources — insufficient "
                       "evidence is a refusal reason, not an approval")
    if not op.get("candidate_hash"):
        return False, "opinion not bound to a candidate hash"
    if not op.get("prompt_sha256"):
        return False, "opinion missing the frozen prompt hash"
    return True, "valid"


def load_opinion_for(data_root: Path, match_id: str,
                     candidate_hash: str,
                     sandbox: bool = False) -> tuple[dict | None, str]:
    """The hash-locked opinion, validated. Returns (opinion|None, why)."""
    d = ai_review_dir(data_root, sandbox) / "opinions_v2"
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
    op = dict(op)
    op["verdict"] = str(op["verdict"]).strip().upper()   # L1: canonical
    # U0/M1 prompt-hash consumption gate (version-aware since R3): the
    # opinion's prompt sha must equal the REGISTERED sha OF ITS OWN
    # prompt_version (digest-blanked formula) — a stale/re-hashed prompt
    # voids the opinion; an unknown version fails closed.
    try:
        from research.papertrade_exec.ai_producer import \
            registered_prompt_sha
        reg_sha, _, _ = registered_prompt_sha(
            Path(__file__).resolve().parents[1].parent,
            version=str(op.get("prompt_version") or "AI_PROMPT_V2"))
    except Exception:
        return None, "registered prompt sha unmeasurable — fail-closed"
    if str(op.get("prompt_sha256") or "") != reg_sha:
        return None, (f"opinion prompt_sha {str(op.get('prompt_sha256'))[:12]}"
                      f"… != registered {reg_sha[:12]}… — prompt era "
                      "mismatch, opinion void (U0/M1)")
    return op, "valid"


def record_opinion(data_root: Path, op: dict,
                   sandbox: bool = False) -> Path:
    """Write (or overwrite) the hash-locked opinion file. The JS sidecar
    produces the opinion; this is the sanctioned writer (schema-checked
    before persist — an invalid opinion is stored under .invalid/ for the
    scorecard, never consumed by the gate)."""
    d = ai_review_dir(data_root, sandbox) / "opinions_v2"
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

def _pending_path(data_root: Path, sandbox: bool = False) -> Path:
    return ai_review_dir(data_root, sandbox) / "pending.json"


def _load_pending(data_root: Path, sandbox: bool = False) -> dict:
    try:
        return json.loads(_pending_path(data_root, sandbox).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_pending(data_root: Path, pending: dict,
                  sandbox: bool = False) -> None:
    # M8: atomic tmp+os.replace under the companion .lock flock.
    atomic_write_json(_pending_path(data_root, sandbox), pending)


def gate_event(data_root: Path, kind: str, sandbox: bool = False,
               **fields) -> None:
    p = ai_review_dir(data_root, sandbox) / "gate_events.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a") as f:
        f.write(json.dumps({"ts_utc": _now(), "kind": kind, **fields},
                           sort_keys=True, default=str) + "\n")


def pending_marker(data_root: Path, match_id: str, candidate_hash: str,
                   anchor_utc: str, detail: str,
                   context: dict | None = None,
                   sandbox: bool = False) -> None:
    """Record/refresh the PENDING_AI entry (the dashboard 'chờ AI' block
    reads this). The bet stays UNDECIDED — retried on the next cadence
    pass (the 15-min cadence throttle is the re-review rhythm). The
    candidate CONTEXT travels in the entry so the headless producer can
    review without re-deriving anything; the producer's own pacing stamp
    survives decide's re-marks."""
    pending = _load_pending(data_root, sandbox)
    prev = pending.get(match_id) or {}
    pending[match_id] = {
        "candidate_hash": candidate_hash,
        "anchor_utc": anchor_utc,
        "first_pending_utc": prev.get("first_pending_utc") or _now(),
        "last_attempt_utc": _now(),
        "attempts": int(prev.get("attempts") or 0) + 1,
        "producer_attempt_utc": prev.get("producer_attempt_utc"),
        "context": context or prev.get("context") or {},
        "last_detail": detail[:240],
    }
    _save_pending(data_root, pending, sandbox)
    gate_event(data_root, "PENDING_AI", sandbox=sandbox, match_id=match_id,
               candidate_hash=candidate_hash, detail=detail[:200])


def clear_pending(data_root: Path, match_id: str, outcome: str,
                  sandbox: bool = False) -> None:
    pending = _load_pending(data_root, sandbox)
    if match_id in pending:
        del pending[match_id]
        _save_pending(data_root, pending, sandbox)
    gate_event(data_root, outcome, sandbox=sandbox, match_id=match_id)


def pending_alarm_owners(data_root: Path,
                         sandbox: bool = False) -> list[dict]:
    """PENDING entries older than PROVIDER_DOWN_ALARM_MIN — the ops layer
    turns these into AI_PROVIDER_DOWN alarms (the whole AI layer failing
    is a W4.4 owner alarm, never a silent bet-killer)."""
    pending = _load_pending(data_root, sandbox)
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
