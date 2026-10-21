"""HEADLESS AI V2 PRODUCER (PAPERDESK-FIXALL-NCAA-V1, owner AI-authority
GO consumed 2026-10-21; U3 STRONGEST-FIRST MODEL CASCADE 2026-10-21) —
the runner-side twin of the JS producer: for every PENDING_AI candidate
it (1) collects REAL evidence through the same ai_research collector,
(2) calls the CONFIGURED provider chain (model_id + fallback_models from
config ai_provider, in EXACTLY that config order = strongest-first; key
from the macOS Keychain — never in repo), and (3) writes the STRICT
{verdict: ALLOW|VETO} hash-locked opinion the gate consumes. The model
NEVER supplies numbers; garbage output is INVALID (stays pending, stored
under .invalid/); provider failure NEVER becomes a verdict (the candidate
keeps waiting — owner QD2 law).

U3 CASCADE LAWS (owner order 2026-10-21):
  * CONFIG-FIRST (QD4): the slot order IS the config order — model_id
    first, then fallback_models verbatim. The producer never re-orders.
  * ONE MODEL PER REQUEST: each provider call names exactly ONE model —
    OpenRouter never receives an internal fallback array.
  * SLOT STATE MACHINE: every model slot is UP | COOLDOWN | HALF_OPEN,
    persisted ATOMICALLY (tmp+os.replace under an fcntl.flock, M8) in
    ai_review/cascade_state.json. A pass requests the FIRST available
    slot; COOLDOWN and CONFIG_BROKEN slots are skipped.
  * HTTP TRIGGERS (typed transport exception carrying .status):
      429        -> slot COOLDOWN max(Retry-After, 15 min); fall to the
                    next slot for that candidate;
      402        -> ALL paid slots (ids not ending ':free') COOLDOWN
                    (indefinite, until a successful balance check) +
                    AI_LOW_BALANCE owner alarm; free slots keep running;
      5xx/timeout-> fall; slot COOLDOWN 10 min doubling per consecutive
                    failure, capped at 4 h;
      garbage    -> retry the SAME model ONCE with a JSON-law suffix
                    appended to the user payload; still bad -> fall and
                    count a soft fail (3 within 1 h -> COOLDOWN 30 min);
      400/404    -> CONFIG_BROKEN (removed until config change) +
                    AI_CONFIG_BROKEN event for the owner;
      401/403    -> AI_KEY_ALARM event + ALL slots COOLDOWN 30 min.
    A COOLDOWN that expires becomes HALF_OPEN: the next REAL scoring
    attempt on that slot is the TRIAL — success -> UP + counters reset;
    failure -> COOLDOWN doubled. Every transition journals a CASCADE_SLOT
    gate event (model, from->to, trigger).
  * BALANCE CLOCK: check_balance (GET /api/v1/key) runs at producer
    start and on 402; below ai_provider.low_balance_usd -> AI_LOW_BALANCE
    and paid slots are held until a successful balance check.
  * BUDGET CLOCK: one producer round tracks elapsed time and stops
    (remaining candidates stay pending) when ai_provider.
    max_budget_seconds is exceeded.

RATE LAW: at most one provider attempt per pending entry per
PROVIDER_RETRY_MIN_MINUTES (decide re-marks the pending queue every
cadence pass; the producer paces itself).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from research.papertrade_exec import ai_gate_v2 as G
from research.papertrade_exec import ai_research

PROVIDER_RETRY_MIN_MINUTES = 5
PROVIDER_TIMEOUT_S = 60

# --- U3 cascade constants (owner order 2026-10-21) ------------------------
SLOT_UP = "UP"
SLOT_COOLDOWN = "COOLDOWN"
SLOT_HALF_OPEN = "HALF_OPEN"

CASCADE_FILE = "cascade_state.json"

RATE_LIMIT_COOLDOWN_MIN = 15        # 429 floor
TRANSIENT_COOLDOWN_MIN = 10         # 5xx/timeout base
TRANSIENT_COOLDOWN_CAP_MIN = 240    # 4 h cap
KEY_ALARM_COOLDOWN_MIN = 30         # 401/403 -> all slots
SOFT_FAIL_LIMIT = 3                 # garbage outputs within ...
SOFT_FAIL_WINDOW_MIN = 60           # ... 1 h -> ...
SOFT_FAIL_COOLDOWN_MIN = 30         # ... 30 min cooldown

KEY_ENDPOINT_SUFFIX = "/chat/completions"
DEFAULT_KEY_ENDPOINT = "https://openrouter.ai/api/v1/key"

RETRY_SUFFIX = ("\n\nYour previous reply was not valid JSON under the "
                "schema. Reply again with EXACTLY one JSON object.")

TRIGGER_RATE_LIMITED = "HTTP_429"
TRIGGER_LOW_BALANCE = "HTTP_402"
TRIGGER_TRANSIENT = "HTTP_5XX_OR_TIMEOUT"
TRIGGER_CONFIG_BROKEN = "HTTP_400_OR_404"
TRIGGER_KEY_ALARM = "HTTP_401_OR_403"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _now_dt() -> datetime:
    return datetime.now(timezone.utc)


def _fmt_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc)


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


class ProviderHTTPError(Exception):
    """Typed transport failure (U3): carries the HTTP `.status` when the
    code is reachable (urllib HTTPError.code), plus a parsed
    `.retry_after` (seconds) for 429. status=None means the failure was
    below HTTP (timeout / connection refused / empty envelope)."""

    def __init__(self, message: str, status: int | None = None,
                 retry_after: float | None = None):
        super().__init__(message)
        self.status = status
        self.retry_after = retry_after


def _post_chat(endpoint: str, key: str, model: str, system: str,
               payload: str) -> str:
    """Provider transport seam (tests stub THIS). ONE model per request —
    the body never carries a fallback array; `data_collection: deny` +
    `require_parameters: true` ride on EVERY request body (U3)."""
    body = json.dumps({"model": model, "temperature": 0,
                       "data_collection": "deny",
                       "require_parameters": True,
                       "messages": [{"role": "system", "content": system},
                                    {"role": "user", "content": payload}]})
    req = urllib.request.Request(endpoint, data=body.encode(), method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=PROVIDER_TIMEOUT_S) as r:
            env = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:            # noqa:  status reachable
        ra = None
        try:
            ra = float(e.headers.get("Retry-After")) \
                if e.headers and e.headers.get("Retry-After") else None
        except (TypeError, ValueError):
            ra = None
        raise ProviderHTTPError(f"HTTP {e.code} from provider",
                                status=e.code, retry_after=ra) from e
    except (TimeoutError, socket_timeout_types()) as e:
        raise ProviderHTTPError(f"transport timeout: {type(e).__name__}",
                                status=None) from e
    except urllib.error.URLError as e:
        reason = getattr(e, "reason", None)
        if isinstance(reason, socket_timeout_types()) or \
                isinstance(e, TimeoutError):
            raise ProviderHTTPError(
                f"transport timeout: {type(reason).__name__}",
                status=None) from e
        raise ProviderHTTPError(
            f"transport failure: {type(e.__cause__ or e).__name__}: {e}",
            status=None) from e
    content = ((env.get("choices") or [{}])[0].get("message") or {})\
        .get("content")
    if not content:
        raise ProviderHTTPError("empty choices envelope", status=None)
    return content


def socket_timeout_types() -> tuple:
    """Timeout exception families across CPython versions (kept as a
    function so the except-clause stays a single expression)."""
    import socket
    return (socket.timeout,)


def classify_failure(exc: BaseException) -> str:
    """HTTP trigger classification (U3): from the typed transport
    exception's .status, or urllib's HTTPError.code where reachable.
    Anything below HTTP (timeout, connection refused, empty envelope)
    classifies TRANSIENT — the slot falls and cools, never poisons."""
    status = getattr(exc, "status", None)
    if not isinstance(status, int):
        code = getattr(exc, "code", None)          # raw urllib HTTPError
        status = code if isinstance(code, int) else None
    if isinstance(status, int):
        if status in (400, 404):
            return TRIGGER_CONFIG_BROKEN
        if status in (401, 403):
            return TRIGGER_KEY_ALARM
        if status == 402:
            return TRIGGER_LOW_BALANCE
        if status == 429:
            return TRIGGER_RATE_LIMITED
        if status >= 500:
            return TRIGGER_TRANSIENT
        return TRIGGER_TRANSIENT                    # other 4xx: fall, no poison
    return TRIGGER_TRANSIENT


# --------------------------------------------------------- cascade state ----

def _is_free(model: str) -> bool:
    """U3 owner law, verbatim: free-tier slot == model id ending ':free'.
    Everything else is a PAID slot (note: 'openrouter/free' does not end
    with ':free' and is therefore PAID under this law — the letter of the
    order is implemented deterministically)."""
    return str(model).endswith(":free")


def _new_slot() -> dict:
    return {"state": SLOT_UP, "cooldown_until_utc": None,
            "cooldown_reason": None, "consecutive_failures": 0,
            "last_cooldown_min": None, "config_broken": False,
            "soft_fails_utc": []}


def cascade_state_path(data_root: Path, *,
                       sandbox: bool = False) -> Path:
    return G.ai_review_dir(data_root, sandbox) / CASCADE_FILE


def load_cascade(data_root: Path, *, sandbox: bool = False) -> dict:
    try:
        raw = json.loads(cascade_state_path(data_root,
                                            sandbox=sandbox).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        raw = {}
    slots = raw.get("slots") if isinstance(raw, dict) else None
    return {"slots": {str(k): {**_new_slot(), **(v or {})}
                      for k, v in (slots or {}).items()},
            "updated_utc": (raw or {}).get("updated_utc")}


def save_cascade(data_root: Path, cascade: dict, *,
                 sandbox: bool = False) -> None:
    """M8: the cascade state file is written ATOMICALLY (tmp+os.replace)
    under the companion .lock flock — a crash can never leave a partial
    state file, and concurrent producer/ops passes serialize."""
    G.atomic_write_json(cascade_state_path(data_root, sandbox=sandbox),
                        {"slots": cascade["slots"],
                         "updated_utc": _now()})


def _transition(data_root: Path, cascade: dict, model: str, to_state: str,
                trigger: str, *, sandbox: bool = False,
                cooldown_min: float | None = None,
                hold: bool = False, now_dt: datetime | None = None) -> None:
    """One slot transition + its CASCADE_SLOT gate event (model, from->to,
    trigger). cooldown_min>0 sets an expiry; hold=True cools INDEFINITELY
    (until the named external revival — e.g. a balance check)."""
    now_dt = now_dt or _now_dt()
    slot = cascade["slots"].setdefault(model, _new_slot())
    frm = slot.get("state") or SLOT_UP
    if cooldown_min is not None:
        slot["cooldown_until_utc"] = _fmt_dt(
            now_dt + timedelta(minutes=float(cooldown_min)))
        slot["cooldown_reason"] = trigger
        slot["last_cooldown_min"] = float(cooldown_min)
    elif hold:
        slot["cooldown_until_utc"] = None          # expires NEVER by clock
        slot["cooldown_reason"] = trigger
    if to_state == SLOT_UP:
        slot["cooldown_until_utc"] = None
        slot["cooldown_reason"] = None
    slot["state"] = to_state
    G.gate_event(data_root, "CASCADE_SLOT", sandbox=sandbox, model=model,
                 from_state=frm, to_state=to_state, trigger=trigger)


def _promote_expired(data_root: Path, cascade: dict, *,
                     sandbox: bool = False,
                     now_dt: datetime | None = None) -> None:
    """COOLDOWN whose clock expired -> HALF_OPEN (the next REAL scoring
    attempt on that slot is the trial). Slots on an indefinite hold
    (cooldown_until_utc None) never promote by clock."""
    now_dt = now_dt or _now_dt()
    for model, slot in cascade["slots"].items():
        if slot.get("state") != SLOT_COOLDOWN:
            continue
        until = slot.get("cooldown_until_utc")
        if not until:
            continue
        try:
            if _parse(until) <= now_dt:
                _transition(data_root, cascade, model, SLOT_HALF_OPEN,
                            "cooldown_expired", sandbox=sandbox,
                            now_dt=now_dt)
        except (ValueError, TypeError):
            continue


def _first_available(cascade: dict, skip: set | None = None) -> str | None:
    """The FIRST available slot in config (strongest-first) order:
    CONFIG_BROKEN and COOLDOWN slots are skipped; UP and HALF_OPEN slots
    are available (HALF_OPEN's request is the trial). `skip` removes
    slots this candidate already fell from (garbage law: fall to the
    NEXT slot, never re-dial the same model within one candidate)."""
    skip = skip or set()
    for model in cascade.get("_order") or []:
        if model in skip:
            continue
        slot = cascade["slots"].get(model) or _new_slot()
        if slot.get("config_broken"):
            continue
        if slot.get("state") == SLOT_COOLDOWN:
            continue
        return model
    return None


def _record_success(data_root: Path, cascade: dict, model: str, *,
                    sandbox: bool = False,
                    now_dt: datetime | None = None) -> None:
    now_dt = now_dt or _now_dt()
    slot = cascade["slots"].setdefault(model, _new_slot())
    was_trial = slot.get("state") == SLOT_HALF_OPEN
    slot["consecutive_failures"] = 0
    slot["soft_fails_utc"] = []
    _transition(data_root, cascade, model, SLOT_UP,
                "trial_success" if was_trial else "opinion_produced",
                sandbox=sandbox, now_dt=now_dt)


def _prune_soft_fails(slot: dict, now_dt: datetime) -> None:
    horizon = now_dt - timedelta(minutes=SOFT_FAIL_WINDOW_MIN)
    fresh = []
    for ts in slot.get("soft_fails_utc") or []:
        try:
            if _parse(ts) >= horizon:
                fresh.append(ts)
        except (ValueError, TypeError):
            continue
    slot["soft_fails_utc"] = fresh


def _record_soft_fail(data_root: Path, cascade: dict, model: str, *,
                      sandbox: bool = False,
                      now_dt: datetime | None = None) -> None:
    """Garbage output (after the one same-model retry): fall for the
    candidate AND count a soft fail; 3 within 1 h -> COOLDOWN 30 min."""
    now_dt = now_dt or _now_dt()
    slot = cascade["slots"].setdefault(model, _new_slot())
    _prune_soft_fails(slot, now_dt)
    slot["soft_fails_utc"].append(_fmt_dt(now_dt))
    if len(slot["soft_fails_utc"]) >= SOFT_FAIL_LIMIT and \
            slot.get("state") != SLOT_COOLDOWN:
        _transition(data_root, cascade, model, SLOT_COOLDOWN,
                    "soft_fails_3_in_1h", sandbox=sandbox,
                    cooldown_min=SOFT_FAIL_COOLDOWN_MIN, now_dt=now_dt)


def _apply_transport_trigger(data_root: Path, cascade: dict,
                             models: list[str], model: str, trigger: str,
                             exc: BaseException, *, sandbox: bool = False,
                             now_dt: datetime | None = None,
                             balance_transport=None,
                             low_balance_usd: float = 0.0,
                             endpoint: str = "", key: str | None = None,
                             check_balance_on_402: bool = True) -> None:
    """U3 trigger table — mutates slots + journals the owner events."""
    now_dt = now_dt or _now_dt()
    slot = cascade["slots"].setdefault(model, _new_slot())
    if trigger == TRIGGER_CONFIG_BROKEN:
        slot["config_broken"] = True               # removed until config change
        _transition(data_root, cascade, model, SLOT_COOLDOWN,
                    TRIGGER_CONFIG_BROKEN, sandbox=sandbox, hold=True,
                    now_dt=now_dt)
        G.gate_event(data_root, "AI_CONFIG_BROKEN", sandbox=sandbox,
                     model=model,
                     status=getattr(exc, "status", None),
                     trigger="HTTP 400/404 — slug dead or malformed request; "
                             "slot removed until a config change")
    elif trigger == TRIGGER_KEY_ALARM:
        for m in models:
            _transition(data_root, cascade, m, SLOT_COOLDOWN,
                        TRIGGER_KEY_ALARM, sandbox=sandbox,
                        cooldown_min=KEY_ALARM_COOLDOWN_MIN, now_dt=now_dt)
        G.gate_event(data_root, "AI_KEY_ALARM", sandbox=sandbox,
                     model=model, status=getattr(exc, "status", None),
                     trigger="HTTP 401/403 — key refused; ALL slots "
                             f"cooldown {KEY_ALARM_COOLDOWN_MIN} min "
                             "(owner alarm)")
    elif trigger == TRIGGER_LOW_BALANCE:
        for m in models:
            if not _is_free(m):
                _transition(data_root, cascade, m, SLOT_COOLDOWN,
                            TRIGGER_LOW_BALANCE, sandbox=sandbox,
                            hold=True, now_dt=now_dt)
        bal = None
        if check_balance_on_402 and (balance_transport is not None or
                                     key):
            bal = check_balance(endpoint, key or "",
                                transport=balance_transport)
        G.gate_event(data_root, "AI_LOW_BALANCE", sandbox=sandbox,
                     model=model, status=402,
                     balance_usd=bal,
                     trigger="HTTP 402 — ALL paid slots held until a "
                             "successful balance check; free slots keep "
                             "running (owner alarm)")
    elif trigger == TRIGGER_RATE_LIMITED:
        slot["consecutive_failures"] = \
            int(slot.get("consecutive_failures") or 0) + 1
        ra_min = None
        ra = getattr(exc, "retry_after", None)
        if isinstance(ra, (int, float)) and ra > 0:
            ra_min = float(ra) / 60.0
        mins = max(ra_min or 0.0, RATE_LIMIT_COOLDOWN_MIN)
        _transition(data_root, cascade, model, SLOT_COOLDOWN,
                    TRIGGER_RATE_LIMITED, sandbox=sandbox,
                    cooldown_min=mins, now_dt=now_dt)
    else:                                          # TRANSIENT (5xx/timeout)
        slot["consecutive_failures"] = \
            int(slot.get("consecutive_failures") or 0) + 1
        mins = min(TRANSIENT_COOLDOWN_MIN *
                   (2 ** (int(slot["consecutive_failures"]) - 1)),
                   TRANSIENT_COOLDOWN_CAP_MIN)
        _transition(data_root, cascade, model, SLOT_COOLDOWN,
                    TRIGGER_TRANSIENT, sandbox=sandbox,
                    cooldown_min=mins, now_dt=now_dt)
    save_cascade(data_root, cascade, sandbox=sandbox)


def _trial_failure_cooldown(data_root: Path, cascade: dict, model: str, *,
                            sandbox: bool = False,
                            now_dt: datetime | None = None,
                            trigger: str = "half_open_trial_failed") -> None:
    """A failed HALF_OPEN trial: COOLDOWN doubled (cap 4 h)."""
    now_dt = now_dt or _now_dt()
    slot = cascade["slots"].setdefault(model, _new_slot())
    slot["consecutive_failures"] = \
        int(slot.get("consecutive_failures") or 0) + 1
    base = float(slot.get("last_cooldown_min") or TRANSIENT_COOLDOWN_MIN)
    mins = min(base * 2.0, float(TRANSIENT_COOLDOWN_CAP_MIN))
    _transition(data_root, cascade, model, SLOT_COOLDOWN, trigger,
                sandbox=sandbox, cooldown_min=mins, now_dt=now_dt)
    save_cascade(data_root, cascade, sandbox=sandbox)


# --------------------------------------------------------- balance clock ----

def key_endpoint_for(endpoint: str) -> str:
    ep = str(endpoint or "")
    if ep.endswith(KEY_ENDPOINT_SUFFIX):
        return ep[: -len(KEY_ENDPOINT_SUFFIX)] + "/key"
    return ep.rstrip("/") + "/key"


def _default_balance_transport(url: str, key: str) -> dict:
    req = urllib.request.Request(
        url, method="GET",
        headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


def check_balance(endpoint: str, key: str, *,
                  transport=None) -> float | None:
    """BALANCE CLOCK (U3): GET the provider key endpoint with Bearer;
    returns the USD remaining on the key, or None when the provider
    reports an unlimited key or the check itself fails (a failed check
    must never crash the producer and never revives a held slot)."""
    url = key_endpoint_for(endpoint)
    try:
        env = (transport or _default_balance_transport)(url, key)
    except Exception:
        return None
    data = env.get("data") if isinstance(env, dict) else None
    if not isinstance(data, dict):
        return None
    for k in ("limit_remaining", "total_remaining", "remaining"):
        v = data.get(k)
        if isinstance(v, (int, float)):
            return float(v)
    limit, usage = data.get("limit"), data.get("usage")
    if isinstance(limit, (int, float)) and \
            isinstance(usage, (int, float)):
        return float(limit) - float(usage)
    return None                                    # unlimited / opaque


# ------------------------------------------------------------ prompt seam ----

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
                        balance_transport=None,
                        sandbox: bool = False,
                        min_retry_minutes: int = PROVIDER_RETRY_MIN_MINUTES
                        ) -> dict:
    """Produce v2 opinions for the PENDING_AI queue through the
    strongest-first slot cascade. Returns a summary; per-entry outcomes
    land in the gate_events journal. The provider transport, keychain
    reader and balance transport are injectable seams for the battery;
    `sandbox` (M6) routes the ENTIRE ai_review plane (opinions, pending,
    events, cascade state, evidence) under <data-root>/sandbox/ai_review
    so a rehearsal never touches the real plane."""
    data_root = Path(data_root)
    from research.papertrade_exec import execute
    cfg = execute.load_config()
    prov = cfg.get("ai_provider") or {}
    endpoint = prov.get("endpoint") or \
        "https://openrouter.ai/api/v1/chat/completions"
    # CONFIG-FIRST (QD4): the config order IS the strongest-first order.
    models = [prov.get("model_id")] + list(prov.get("fallback_models") or [])
    models = [m for m in models if m]
    key_ref = prov.get("key_ref") or "com.myquant.paperdesk / openrouter-api-key"
    low_balance = float(prov.get("low_balance_usd") or 0.0)
    budget_s = float(prov.get("max_budget_seconds") or 0.0)
    prompt = _frozen_prompt(worktree_root)
    pending = G._load_pending(data_root, sandbox=sandbox)
    now_dt = _now_dt()
    summary = {"reviewed": 0, "written": 0, "invalid": 0,
               "provider_failed": 0, "rate_limited": 0,
               "budget_stopped": False, "left_pending": 0}
    out_dir = G.ai_review_dir(data_root, sandbox) / "opinions_v2"
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- cascade state + BALANCE CLOCK at producer start -----------------
    cascade = load_cascade(data_root, sandbox=sandbox)
    cascade["_order"] = models
    key = None
    if provider_transport is None:
        try:
            key = (keychain_reader or keychain_key)(key_ref)
        except Exception:
            key = None                              # honest degrade below
    balance = None
    if balance_transport is not None or provider_transport is None:
        balance = check_balance(endpoint, key or "",
                                transport=balance_transport) \
            if key is not None or balance_transport is not None else None
    cascade_changed = False
    if balance is not None:
        if balance < low_balance:
            for m in models:
                slot = cascade["slots"].setdefault(m, _new_slot())
                if not _is_free(m) and \
                        slot.get("cooldown_reason") != TRIGGER_LOW_BALANCE:
                    _transition(data_root, cascade, m, SLOT_COOLDOWN,
                                TRIGGER_LOW_BALANCE, sandbox=sandbox,
                                hold=True, now_dt=now_dt)
                    cascade_changed = True
            G.gate_event(data_root, "AI_LOW_BALANCE", sandbox=sandbox,
                         balance_usd=balance,
                         trigger=f"balance {balance:.2f} USD < "
                                 f"low_balance_usd {low_balance:.2f} — paid "
                                 "slots held until a successful balance "
                                 "check (owner alarm)")
        else:
            for m in models:                        # successful check revives
                slot = cascade["slots"].setdefault(m, _new_slot())
                if slot.get("state") == SLOT_COOLDOWN and \
                        slot.get("cooldown_reason") == TRIGGER_LOW_BALANCE:
                    slot["consecutive_failures"] = 0
                    _transition(data_root, cascade, m, SLOT_UP,
                                "balance_check_ok", sandbox=sandbox,
                                now_dt=now_dt)
                    cascade_changed = True
    if cascade_changed or True:
        save_cascade(data_root, cascade, sandbox=sandbox)

    t0 = time.monotonic()

    def _attempt(model: str, system: str, pay: str) -> str:
        if provider_transport is not None:
            return provider_transport(model, system, pay)
        return _post_chat(endpoint, key, model, system, pay)

    for mid, entry in sorted(pending.items()):
        # BUDGET CLOCK: once the round's budget is spent, the remaining
        # candidates stay pending (never killed, never half-reviewed).
        if budget_s and (time.monotonic() - t0) >= budget_s:
            summary["budget_stopped"] = True
            break
        summary["reviewed"] += 1
        # an opinion for THIS hash already exists: decide will consume it
        try:
            op, _why = G.load_opinion_for(data_root, mid,
                                          entry.get("candidate_hash"),
                                          sandbox=sandbox)
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
                age = (now_dt - _parse(last)).total_seconds() / 60.0
                if age < min_retry_minutes:
                    summary["rate_limited"] += 1
                    continue
        except (ValueError, TypeError):
            pass
        pending[mid]["producer_attempt_utc"] = _now()
        G._save_pending(data_root, pending, sandbox=sandbox)
        # Integrator wiring (U5/U6 handover): the pending CONTEXT already
        # carries kickoff_utc (apply_ai_gate_v2) and may carry team_ids —
        # thread both so the collector fetches the MATCH-date board and the
        # roster/injuries layers activate. Absent values stay honestly
        # absent (the collector looks ids up on the kickoff board itself).
        _ctx = entry.get("context") or {}
        research = ai_research.collect_evidence(
            league=_ctx.get("league") or "",
            match_id=mid,
            home=_ctx.get("home") or "",
            away=_ctx.get("away") or "",
            journal_dir=G.ai_review_dir(data_root, sandbox) / "evidence",
            kickoff_utc=_ctx.get("kickoff_utc"),
            team_ids=_ctx.get("team_ids"))
        payload = _build_user_payload(entry, research)
        _promote_expired(data_root, cascade, sandbox=sandbox, now_dt=_now_dt())
        raw_used: str | None = None
        model: str | None = None
        errors: list[str] = []
        last_garbage: dict | None = None
        tried: set = set()      # slots this candidate already fell from
        while True:
            slot_model = _first_available(cascade, skip=tried)
            if slot_model is None:
                break                            # every slot down: silence
            slot = cascade["slots"].setdefault(slot_model, _new_slot())
            is_trial = slot.get("state") == SLOT_HALF_OPEN
            try:
                raw = _attempt(slot_model, prompt["system"], payload)
            except Exception as e:
                errors.append(f"{slot_model}: {type(e).__name__}: {e}")
                trig = classify_failure(e)
                _apply_transport_trigger(
                    data_root, cascade, models, slot_model, trig, e,
                    sandbox=sandbox, now_dt=_now_dt(),
                    balance_transport=balance_transport,
                    low_balance_usd=low_balance, endpoint=endpoint,
                    key=key, check_balance_on_402=balance_transport
                    is not None or provider_transport is None)
                if trig == TRIGGER_KEY_ALARM:
                    break                        # ALL slots down now
                continue                         # fall to the next slot
            parsed = parse_v2(raw)
            if not parsed["ok"]:
                # GARBAGE LAW: retry the SAME model ONCE with the JSON-law
                # suffix appended to the user payload.
                try:
                    raw_retry = _attempt(slot_model, prompt["system"],
                                         payload + RETRY_SUFFIX)
                except Exception as e2:
                    errors.append(f"{slot_model} (retry): "
                                  f"{type(e2).__name__}: {e2}")
                    trig = classify_failure(e2)
                    if is_trial:
                        _trial_failure_cooldown(
                            data_root, cascade, slot_model, sandbox=sandbox,
                            now_dt=_now_dt())
                    else:
                        _apply_transport_trigger(
                            data_root, cascade, models, slot_model, trig, e2,
                            sandbox=sandbox, now_dt=_now_dt(),
                            balance_transport=balance_transport,
                            low_balance_usd=low_balance, endpoint=endpoint,
                            key=key,
                            check_balance_on_402=balance_transport
                            is not None or provider_transport is None)
                    if trig == TRIGGER_KEY_ALARM:
                        break
                    continue
                parsed = parse_v2(raw_retry)
                if not parsed["ok"]:
                    # still garbage: fall for this candidate + soft fail
                    last_garbage = {"model": slot_model, "raw": raw_retry,
                                    "why": parsed["why"]}
                    tried.add(slot_model)   # the NEXT slot, never re-dial
                    if is_trial:
                        _trial_failure_cooldown(
                            data_root, cascade, slot_model, sandbox=sandbox,
                            now_dt=_now_dt())
                    else:
                        _record_soft_fail(data_root, cascade, slot_model,
                                          sandbox=sandbox,
                                          now_dt=_now_dt())
                    continue
                model = slot_model               # retry succeeded
                raw_used = raw_retry
                break
            model = slot_model                    # first attempt was valid
            raw_used = raw
            break
        save_cascade(data_root, cascade, sandbox=sandbox)
        if model is None:
            if last_garbage is not None:
                # every reachable slot answered garbage: the candidate
                # keeps WAITING (QD2) — the garbage is stored under
                # .invalid/ for the scorecard, never consumed.
                bad = out_dir / ".invalid"
                bad.mkdir(exist_ok=True)
                (bad / f"{mid}_{entry.get('candidate_hash')}.json").write_text(
                    json.dumps({"match_id": mid,
                                "candidate_hash":
                                    entry.get("candidate_hash"),
                                "invalid_why": last_garbage["why"],
                                "raw": str(last_garbage["raw"])[:2000],
                                "model_id": last_garbage["model"],
                                "prompt_version": prompt["version"],
                                "prompt_sha256": prompt["sha256"],
                                "created_at_utc": _now()}, indent=1,
                               sort_keys=True))
                summary["invalid"] += 1
                G.gate_event(data_root, "OPINION_INVALID", sandbox=sandbox,
                             match_id=mid,
                             why=last_garbage["why"][:200])
            else:
                summary["provider_failed"] += 1
                G.gate_event(data_root, "PROVIDER_FAILED", sandbox=sandbox,
                             match_id=mid,
                             errors="; ".join(errors)[:400])
            continue
        parsed = parse_v2(raw_used)
        if not parsed["ok"]:                      # defensive; unreachable
            summary["provider_failed"] += 1
            G.gate_event(data_root, "PROVIDER_FAILED", sandbox=sandbox,
                         match_id=mid,
                         errors=f"{model}: post-loop parse miss")
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
                            "raw": str(raw_used)[:2000],
                            "model_id": model,
                            "prompt_version": prompt["version"],
                            "prompt_sha256": prompt["sha256"],
                            "created_at_utc": _now()}, indent=1,
                           sort_keys=True))
            summary["invalid"] += 1
            G.gate_event(data_root, "OPINION_INVALID", sandbox=sandbox,
                         match_id=mid,
                         why="citation filter emptied an ALLOW (U0/H1)")
            continue
        _record_success(data_root, cascade, model, sandbox=sandbox,
                        now_dt=_now_dt())
        save_cascade(data_root, cascade, sandbox=sandbox)
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
        path = G.record_opinion(data_root, opinion, sandbox=sandbox)
        summary["written"] += 1
        G.gate_event(data_root, "OPINION_PRODUCED", sandbox=sandbox,
                     match_id=mid, verdict=opinion["verdict"],
                     model=model, opinion=str(path.name))
    if summary["budget_stopped"]:
        summary["left_pending"] = max(0, len(pending) -
                                      summary["reviewed"])
    return summary
