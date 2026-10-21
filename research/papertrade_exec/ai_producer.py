"""HEADLESS AI V2 PRODUCER (PAPERDESK-FIXALL-NCAA-V1, owner AI-authority
GO consumed 2026-10-21) — the runner-side twin of the JS producer: for
every PENDING_AI candidate it (1) collects REAL evidence through the same
ai_research collector, (2) calls the CONFIGURED provider (model/endpoint
from config ai_provider; key from the macOS Keychain — never in repo), and
(3) writes the STRICT {verdict: ALLOW|VETO} hash-locked opinion the gate
consumes. The model NEVER supplies numbers; garbage output is INVALID
(stays pending, stored under .invalid/); provider failure NEVER becomes a
verdict (the candidate keeps waiting — owner QD2 law).

RATE LAW: at most one provider attempt per pending entry per
PROVIDER_RETRY_MIN_MINUTES (decide re-marks the pending queue every
cadence pass; the producer paces itself).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from research.papertrade_exec import ai_gate_v2 as G
from research.papertrade_exec import ai_research

PROVIDER_RETRY_MIN_MINUTES = 5
PROVIDER_TIMEOUT_S = 60


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_v2(raw: str) -> dict:
    """The STRICT v2 law (mirror of apps/paperdesk/main/ai_v2_producer.js
    parseV2): exactly one JSON object; verdict in {ALLOW, VETO}; anything
    else (SWITCH/CHALLENGE/ALTERNATIVE/ABSTAIN/garbage) is invalid;
    ALLOW with zero cited sources is invalid (insufficient evidence is a
    refusal, never an approval)."""
    parsed = None
    try:
        a, b = raw.find("{"), raw.rfind("}")
        if 0 <= a < b:
            parsed = json.loads(raw[a:b + 1])
    except json.JSONDecodeError:
        parsed = None
    if not isinstance(parsed, dict):
        return {"ok": False, "why": "output not parseable as one JSON object"}
    verdict = str(parsed.get("verdict") or "").strip().upper()
    if verdict not in G.AI_VERDICTS:
        return {"ok": False,
                "why": (f"verdict {verdict!r} outside {G.AI_VERDICTS} — "
                        "not actionable under owner law")}
    codes = [str(c)[:60] for c in (parsed.get("reason_codes") or [])]
    if not codes:
        return {"ok": False, "why": "missing reason_codes"}
    summary = str(parsed.get("summary") or "")[:600].strip()
    if not summary:
        return {"ok": False, "why": "missing summary"}
    sources = []
    for s in parsed.get("sources") or []:
        if isinstance(s, dict) and s.get("url"):
            sources.append({"url": str(s["url"])[:400],
                            "excerpt": str(s.get("excerpt") or "")[:280],
                            "fetched_at_utc": _now()})
    if verdict == "ALLOW" and not sources:
        return {"ok": False,
                "why": ("ALLOW with zero cited sources — insufficient "
                        "evidence is a refusal, never an approval")}
    return {"ok": True, "verdict": verdict, "reason_codes": codes,
            "summary": summary, "sources": sources}


def keychain_key(key_ref: str) -> str:
    """`key_ref` format: '<keychain service> / <account>' (config law).
    Key bytes NEVER enter repo/logs — they travel only in-memory to the
    provider call."""
    ref = " ".join(key_ref.split())
    if "/" in ref:
        service, account = [x.strip() for x in ref.rsplit("/", 1)]
    else:
        service, account = ref, ref
    out = subprocess.run(["/usr/bin/security", "find-generic-password",
                          "-s", service, "-a", account, "-w"],
                         capture_output=True, text=True, timeout=15)
    key = (out.stdout or "").strip()
    if out.returncode != 0 or not key:
        raise RuntimeError("keychain lookup failed for "
                           f"{service}/{account}: {out.stderr.strip()[:120]}")
    return key


def _post_chat(endpoint: str, key: str, model: str, system: str,
               payload: str) -> str:
    """Provider transport seam (tests stub THIS)."""
    body = json.dumps({"model": model, "temperature": 0,
                       "messages": [{"role": "system", "content": system},
                                    {"role": "user", "content": payload}]})
    req = urllib.request.Request(endpoint, data=body.encode(), method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=PROVIDER_TIMEOUT_S) as r:
        env = json.loads(r.read().decode("utf-8"))
    content = ((env.get("choices") or [{}])[0].get("message") or {})\
        .get("content")
    if not content:
        raise RuntimeError("empty choices envelope")
    return content


PROMPT_SHA_LINE = "sha256 (measured"


def registered_prompt_sha(worktree_root: Path) -> tuple[str, str, str]:
    """U0/M1: the registered sha is sha256 over the prompt file with the
    digest VALUE on the 'sha256 (measured...' line replaced by EMPTY —
    the freeze formula documented in the file itself. Returns
    (sha, system_text, erratum_note)."""
    p = Path(worktree_root) / "research" / "papertrade_exec" / \
        "AI_PROMPT_V2.md"
    text = p.read_text()
    lines = text.splitlines()
    sha_line = next((l for l in lines if l.startswith(PROMPT_SHA_LINE)), None)
    blanked = text.replace(sha_line, sha_line.split(": ")[0] + ": ") \
        if sha_line else text
    return (hashlib.sha256(blanked.encode()).hexdigest(),
            text,
            "erratum U0/M1: the previously registered 4365381d… was NOT "
            "reproducible from the delivered file; re-measured and "
            "re-registered with the documented digest-blanked formula")


def _frozen_prompt(worktree_root: Path) -> dict:
    import re
    sha, text, _err = registered_prompt_sha(worktree_root)
    m = re.search(r"```\n([\s\S]*?)\n```", text)
    return {"version": "AI_PROMPT_V2",
            "sha256": sha,
            "system": m.group(1) if m else text}


def _build_user_payload(entry: dict, research: dict) -> str:
    ctx = entry.get("context") or {}
    return json.dumps({
        "fixture": {k: ctx.get(k) for k in
                    ("league", "match_id", "home", "away", "kickoff_utc",
                     "competition")},
        "chosen_leg": ctx.get("chosen_leg"),
        "frozen": {"p": ctx.get("p_frozen"), "odds": ctx.get("odds_frozen"),
                   "ev_net": ctx.get("ev_net_by_leg"),
                   "stake_cents": ctx.get("stake_cents"),
                   "note": ("FROZEN — you never change numbers, never "
                            "switch legs")},
        "candidate_hash": entry.get("candidate_hash"),
        "anchor_utc": entry.get("anchor_utc"),
        "captured_sources": research.get("sources") or [],
        "evidence_note": ("These are the ONLY lawful citations; citing "
                          "anything else is fabrication and your verdict "
                          "will be discarded."),
    }, indent=1)


def produce_for_pending(data_root: Path, *, worktree_root: Path,
                        provider_transport=None, keychain_reader=None,
                        min_retry_minutes: int = PROVIDER_RETRY_MIN_MINUTES
                        ) -> dict:
    """Produce v2 opinions for the PENDING_AI queue. Returns a summary;
    per-entry outcomes land in the gate_events journal. Provider transport
    and keychain reader are injectable seams for the battery."""
    data_root = Path(data_root)
    from research.papertrade_exec import execute
    cfg = execute.load_config()
    prov = cfg.get("ai_provider") or {}
    endpoint = prov.get("endpoint") or \
        "https://openrouter.ai/api/v1/chat/completions"
    models = [prov.get("model_id")] + list(prov.get("fallback_models") or [])
    models = [m for m in models if m]
    key_ref = prov.get("key_ref") or "com.myquant.paperdesk / openrouter-api-key"
    prompt = _frozen_prompt(worktree_root)
    pending = G._load_pending(data_root)
    now_dt = datetime.now(timezone.utc)
    summary = {"reviewed": 0, "written": 0, "invalid": 0,
               "provider_failed": 0, "rate_limited": 0}
    out_dir = G.ai_review_dir(data_root) / "opinions_v2"
    out_dir.mkdir(parents=True, exist_ok=True)
    for mid, entry in sorted(pending.items()):
        summary["reviewed"] += 1
        # an opinion for THIS hash already exists: decide will consume it
        try:
            op, _why = G.load_opinion_for(data_root, mid,
                                          entry.get("candidate_hash"))
            if op is not None:
                summary["rate_limited"] += 1
                continue
        except Exception:
            pass
        # the producer paces ITSELF (decide refreshes last_attempt_utc on
        # every pass, so the producer keeps its own attempt stamp)
        try:
            last = entry.get("producer_attempt_utc")
            if last:
                age = (now_dt - datetime.strptime(
                    last, "%Y-%m-%dT%H:%M:%SZ").replace(
                        tzinfo=timezone.utc)).total_seconds() / 60.0
                if age < min_retry_minutes:
                    summary["rate_limited"] += 1
                    continue
        except (ValueError, TypeError):
            pass
        pending[mid]["producer_attempt_utc"] = _now()
        G._save_pending(data_root, pending)
        research = ai_research.collect_evidence(
            league=(entry.get("context") or {}).get("league") or "",
            match_id=mid,
            home=(entry.get("context") or {}).get("home") or "",
            away=(entry.get("context") or {}).get("away") or "",
            journal_dir=G.ai_review_dir(data_root) / "evidence")
        payload = _build_user_payload(entry, research)
        raw, model, errors = None, None, []
        for m in models:
            try:
                if provider_transport is not None:
                    raw = provider_transport(m, prompt["system"], payload)
                else:
                    key = (keychain_reader or keychain_key)(key_ref)
                    raw = _post_chat(endpoint, key, m, prompt["system"],
                                     payload)
                model = m
                break
            except Exception as e:
                errors.append(f"{m}: {type(e).__name__}: {e}")
        if raw is None:
            summary["provider_failed"] += 1
            G.gate_event(data_root, "PROVIDER_FAILED", match_id=mid,
                         errors="; ".join(errors)[:400])
            continue
        parsed = parse_v2(raw)
        if not parsed["ok"]:
            bad = out_dir / ".invalid"
            bad.mkdir(exist_ok=True)
            (bad / f"{mid}_{entry.get('candidate_hash')}.json").write_text(
                json.dumps({"match_id": mid,
                            "candidate_hash": entry.get("candidate_hash"),
                            "invalid_why": parsed["why"],
                            "raw": str(raw)[:2000], "model_id": model,
                            "prompt_version": prompt["version"],
                            "prompt_sha256": prompt["sha256"],
                            "created_at_utc": _now()}, indent=1,
                           sort_keys=True))
            summary["invalid"] += 1
            G.gate_event(data_root, "OPINION_INVALID", match_id=mid,
                         why=parsed["why"][:200])
            continue
        # U0/H1 citation law: ONLY sources whose URL is in the actually
        # captured set survive — a model-invented URL is dropped ENTIRELY
        # (never re-stamped, never salvaged). ALLOW with zero surviving
        # sources is INVALID (insufficient evidence).
        captured = {s["url"]: s for s in (research.get("sources") or [])}
        sources = [captured[s["url"]] for s in parsed["sources"]
                   if s["url"] in captured]
        if parsed["verdict"] == "ALLOW" and not sources:
            bad = out_dir / ".invalid"
            bad.mkdir(exist_ok=True)
            (bad / f"{mid}_{entry.get('candidate_hash')}.json").write_text(
                json.dumps({"match_id": mid,
                            "candidate_hash": entry.get("candidate_hash"),
                            "invalid_why": ("ALLOW with zero CAPTURED "
                                "sources after the citation filter — all "
                                "model citations were fabricated "
                                "(U0/H1)"),
                            "raw": str(raw)[:2000], "model_id": model,
                            "prompt_version": prompt["version"],
                            "prompt_sha256": prompt["sha256"],
                            "created_at_utc": _now()}, indent=1,
                           sort_keys=True))
            summary["invalid"] += 1
            G.gate_event(data_root, "OPINION_INVALID", match_id=mid,
                         why="citation filter emptied an ALLOW (U0/H1)")
            continue
        opinion = {"match_id": mid,
                   "candidate_hash": entry.get("candidate_hash"),
                   "verdict": parsed["verdict"],
                   "reason_codes": parsed["reason_codes"],
                   "summary": parsed["summary"],
                   "sources": sources,
                   "model_id": model, "provider":
                       prov.get("provider") or "openrouter",
                   "prompt_version": prompt["version"],
                   "prompt_sha256": prompt["sha256"],
                   "created_at_utc": _now()}
        path = G.record_opinion(data_root, opinion)
        summary["written"] += 1
        G.gate_event(data_root, "OPINION_PRODUCED", match_id=mid,
                     verdict=opinion["verdict"], model=model,
                     opinion=str(path.name))
    return summary
