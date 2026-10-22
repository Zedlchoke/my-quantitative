"""PAPERDESK UPGRADE V2 — U3 battery: STRONGEST-FIRST MODEL CASCADE.

Owner order 2026-10-21, QD4 config-first:
  U3.1  config ai_provider IS the chain: model_id anthropic/claude-opus-5.5
        head + the owner's fallback order verbatim; max_budget_seconds=600;
        low_balance_usd=10.0 (the producer never re-orders, never
        hard-wires a model);
  U3.2  slot state machine UP|COOLDOWN|HALF_OPEN persisted ATOMICALLY in
        ai_review/cascade_state.json; each pass requests the FIRST
        available slot only (ONE model per request — OpenRouter never
        receives an internal fallback array);
  U3.3  HTTP triggers: 429 -> COOLDOWN max(Retry-After, 15m); 402 -> ALL
        paid slots held (free slots keep producing) + AI_LOW_BALANCE;
        5xx/timeout -> fall + COOLDOWN 10m doubling per consecutive
        failure capped 4h; garbage -> retry SAME model once with the
        JSON-law suffix, then fall + soft fail (3 in 1h -> COOLDOWN 30m);
        400/404 -> CONFIG_BROKEN (removed until config change) +
        AI_CONFIG_BROKEN; 401/403 -> AI_KEY_ALARM + ALL slots COOLDOWN
        30m; expired COOLDOWN -> HALF_OPEN trial (success -> UP +
        reset, failure -> COOLDOWN doubled);
  U3.4  every request body carries data_collection=deny +
        require_parameters=true;
  U3.5  balance clock (check_balance at start and on 402) below
        low_balance_usd -> AI_LOW_BALANCE;
  U3.6  budget clock: a round stops when max_budget_seconds is exceeded —
        remaining candidates stay pending;
  QD2   silence law: ALL slots down => candidates stay pending, producer
        returns, no opinion, no crash. U0 citation filter + parse_v2 laws
        stay intact.

All provider contact goes through the injected transport seam — the
battery never touches the network. Slug verification against the LIVE
OpenRouter models list is PENDING (no network budget); a dead slug
surfaces at runtime as 400/404 -> CONFIG_BROKEN, which is the safe
behavior (tested here synthetically).
"""
from __future__ import annotations

import json
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from research.papertrade_exec import ai_gate_v2 as G          # noqa: E402
from research.papertrade_exec import ai_producer as P         # noqa: E402
from research.papertrade_exec import ai_research              # noqa: E402
from research.papertrade_exec import execute                  # noqa: E402

ANTHROPIC_HEAD = "anthropic/claude-opus-5.5"
OWNER_ORDER = [
    "openai/gpt-5.6-sol",
    "anthropic/claude-sonnet-5.5",
    "google/gemini-3.1-pro-preview",
    "deepseek/deepseek-v4-pro-0813",
    "x-ai/grok-4.7",
    "minimax/minimax-m3.1-flash:free",
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "thinkingmachines/inkling:free",
    "openrouter/free",
]

NOW_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _iso(dt: datetime) -> str:
    return dt.strftime(NOW_FMT)


@pytest.fixture()
def env(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    return {"data": data}


@pytest.fixture()
def cfg():
    """The REAL committed config (QD4: the battery asserts the owner's
    chain, it never re-fabricates one)."""
    return execute.load_config()


def _wire_cfg(monkeypatch, cfg, *, models=None, budget=None, low=None):
    prov = dict(cfg["ai_provider"])
    if models is not None:
        prov["model_id"], prov["fallback_models"] = \
            models[0], list(models[1:])
    if budget is not None:
        prov["max_budget_seconds"] = budget
    if low is not None:
        prov["low_balance_usd"] = low
    monkeypatch.setattr(execute, "load_config",
                        lambda: {**cfg, "ai_provider": prov})
    return prov


def _valid(verdict="VETO", sources=()):
    return json.dumps({"verdict": verdict,
                       "reason_codes": ["R-CASCADE"],
                       "summary": "reviewed on synthetic evidence",
                       "sources": list(sources)})


def _garbage():
    return "I reviewed the match and I think the home team will win."


_SEQ = {"n": 0}


def _fresh_hash() -> str:
    _SEQ["n"] += 1
    return format(_SEQ["n"], "064x")


def _mark_pending(data, match_id="m1", candidate_hash=None):
    chash = candidate_hash or _fresh_hash()
    anchor = _iso(datetime.now(timezone.utc) + timedelta(hours=6))
    G.pending_marker(
        data, match_id, chash, anchor, "battery candidate",
        context={"league": "NBA", "match_id": match_id, "home": "H",
                 "away": "A", "kickoff_utc": anchor,
                 "competition": "NBA", "chosen_leg": "HOME",
                 "p_frozen": {"HOME": 0.55}, "odds_frozen": {"HOME": 2.0},
                 "ev_net_by_leg": {"HOME": 0.06}, "stake_cents": 500})
    return chash


def _produce(env, monkeypatch, *, transport, models, balance_transport=None,
             min_retry_minutes=0, budget=None, low=None, sandbox=False,
             mark=True):
    if mark:
        _mark_pending(env["data"])
    _wire_cfg(monkeypatch, execute.load_config(), models=models, budget=budget,
              low=low)
    monkeypatch.setattr(ai_research, "collect_evidence",
                        lambda **kw: {"sources": [
                            {"url": "https://example.com/wire",
                             "fetched_at_utc": _iso(datetime.now(
                                 timezone.utc)),
                             "excerpt": "headline"}]})
    return P.produce_for_pending(
        env["data"], worktree_root=REPO, provider_transport=transport,
        balance_transport=balance_transport,
        sandbox=sandbox, min_retry_minutes=min_retry_minutes,
        fr_over={"enabled": False})   # free-research battery is its own file


def _load_cfg():
    return execute.load_config()


def _events(data, sandbox=False, kind=None):
    p = G.ai_review_dir(data, sandbox) / "gate_events.jsonl"
    if not p.exists():
        return []
    rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    return [r for r in rows if kind is None or r.get("kind") == kind]


def _slot(data, model, sandbox=False):
    return P.load_cascade(data, sandbox=sandbox)["slots"].get(model)


def _cooldown_minutes_left(slot) -> float:
    until = _load_pending_until(slot)
    dt = datetime.strptime(until, NOW_FMT).replace(tzinfo=timezone.utc)
    return (dt - datetime.now(timezone.utc)).total_seconds() / 60.0


def _load_pending_until(slot):
    return slot["cooldown_until_utc"]


# ------------------------------------------------------------------ U3.1 ----

def test_config_is_the_strongest_first_chain(cfg):
    """QD4 config-first: model_id head + fallback order verbatim + the two
    U3 knobs. ERRATUM (R0b, owner orders 2026-10-22): #1 the HEAD stage
    became deepseek/deepseek-v4.1-flash-1017 (per-stage reasoning effort
    max); #2 the chain is DeepSeek-ONLY — ONE fallback
    deepseek/deepseek-v4.1-flash (no plain deepseek-v4.1 slug exists on
    the live OpenRouter list; the desk pinned the live flash variant).
    The whole multi-vendor chain was removed by order #2. Slugs are NOT
    verified against the live models list here; a dead slug dies as
    CONFIG_BROKEN at runtime (see the 404 test below)."""
    prov = cfg["ai_provider"]
    assert prov["model_id"] == "deepseek/deepseek-v4.1-flash-1017"
    assert prov["fallback_models"] == ["deepseek/deepseek-v4.1-flash"]
    assert prov["max_budget_seconds"] == 600
    assert prov["low_balance_usd"] == 10.0
    assert prov["reasoning_effort_by_model"] == \
        {"deepseek/deepseek-v4.1-flash-1017": "max"}


def test_producer_walks_config_order_strongest_first(env, monkeypatch, cfg):
    """The first pass must REQUEST the head model first (one model per
    call, config order — never a re-order, never an array)."""
    calls = []

    def transport(model, system, payload):
        calls.append(model)
        return _valid()

    out = _produce(env, monkeypatch, transport=transport,
                   models=[ANTHROPIC_HEAD] + OWNER_ORDER)
    assert out["written"] == 1
    assert calls == [ANTHROPIC_HEAD]           # head slot alone suffices
    assert _slot(env["data"], ANTHROPIC_HEAD)["state"] == P.SLOT_UP


# ------------------------------------------------------------------ U3.2 ----

def test_one_model_per_request_body_never_a_fallback_array(env, monkeypatch,
                                                           cfg):
    """U3.4 + the one-model law: the wire body names exactly ONE model and
    carries data_collection=deny + require_parameters=true."""
    captured = {}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps(
                {"choices": [{"message": {"content": _valid()}}]})\
                .encode("utf-8")

    def fake_urlopen(req, timeout=None):
        captured["body"] = json.loads(req.data.decode("utf-8"))
        return _Resp()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    raw = P._post_chat("https://x/api/v1/chat/completions", "k", "m1",
                       "sys", "payload")
    assert raw.startswith("{")
    body = captured["body"]
    assert body["model"] == "m1"
    assert "models" not in body and "fallbacks" not in body
    assert body["data_collection"] == "deny"
    assert body["require_parameters"] is True


def test_cascade_state_file_is_atomic_and_persistent(env, monkeypatch, cfg):
    """U3.2/M8: the slot file exists, parses, leaves no .tmp behind and
    keeps its companion .lock; a second producer pass READS the persisted
    state (head skipped while COOLDOWN)."""
    def transport(model, system, payload):
        if model == ANTHROPIC_HEAD:
            raise P.ProviderHTTPError("429", status=429, retry_after=900)
        return _valid()

    _produce(env, monkeypatch, transport=transport,
             models=[ANTHROPIC_HEAD, OWNER_ORDER[5]])
    p = P.cascade_state_path(env["data"])
    assert p.exists()
    state = json.loads(p.read_text())
    assert ANTHROPIC_HEAD in state["slots"]
    assert not list(p.parent.glob("*.tmp"))
    assert (p.parent / "cascade_state.json.lock").exists()
    # persistence: the head is skipped on the NEXT pass (still COOLDOWN)
    _mark_pending(env["data"], candidate_hash="1" * 64)
    calls = []

    def transport2(model, system, payload):
        calls.append(model)
        return _valid()

    _produce(env, monkeypatch, transport=transport2,
             models=[ANTHROPIC_HEAD, OWNER_ORDER[5]], mark=False)
    assert ANTHROPIC_HEAD not in calls


# ------------------------------------------------------------------ U3.3 ----

def test_429_falls_to_next_slot_and_cools_max_retry_after_15m(env,
                                                              monkeypatch,
                                                              cfg):
    def transport(model, system, payload):
        if model == ANTHROPIC_HEAD:
            raise P.ProviderHTTPError("rate limited", status=429,
                                      retry_after=60)   # 1 min < 15m floor
        return _valid()

    out = _produce(env, monkeypatch, transport=transport,
                   models=[ANTHROPIC_HEAD, OWNER_ORDER[0]])
    assert out["written"] == 1
    slot = _slot(env["data"], ANTHROPIC_HEAD)
    assert slot["state"] == P.SLOT_COOLDOWN
    left = _cooldown_minutes_left(slot)
    assert 14.0 <= left <= 15.0                 # max(Retry-After=1m, 15m)
    ev = _events(env["data"], kind="CASCADE_SLOT")
    assert any(e["model"] == ANTHROPIC_HEAD and
               e["trigger"] == P.TRIGGER_RATE_LIMITED and
               e["from_state"] == P.SLOT_UP and
               e["to_state"] == P.SLOT_COOLDOWN for e in ev)


def test_402_holds_paid_slots_free_slots_still_produce(env, monkeypatch,
                                                       cfg):
    paid, paid2, free = OWNER_ORDER[0], OWNER_ORDER[1], OWNER_ORDER[5]
    calls = []

    def transport(model, system, payload):
        calls.append(model)
        if model in (paid, paid2):
            raise P.ProviderHTTPError("payment required", status=402)
        return _valid()

    out = _produce(env, monkeypatch, transport=transport,
                   models=[paid, paid2, free])
    assert out["written"] == 1
    # the FIRST 402 holds ALL paid slots at once — paid2 is never dialed;
    # the candidate falls straight through to the free slot
    assert calls == [paid, free]
    for m in (paid, paid2):
        slot = _slot(env["data"], m)
        assert slot["state"] == P.SLOT_COOLDOWN
        assert slot["cooldown_until_utc"] is None        # indefinite hold
        assert slot["cooldown_reason"] == P.TRIGGER_LOW_BALANCE
    assert _slot(env["data"], free)["state"] == P.SLOT_UP
    kinds = [e["kind"] for e in _events(env["data"])]
    assert "AI_LOW_BALANCE" in kinds


def test_5xx_transient_cooldown_10m_then_doubling_cap_4h(env, monkeypatch,
                                                         cfg):
    def transport(model, system, payload):
        if model == ANTHROPIC_HEAD:
            raise P.ProviderHTTPError("boom", status=503)
        return _valid()

    _produce(env, monkeypatch, transport=transport,
             models=[ANTHROPIC_HEAD, OWNER_ORDER[0]])
    slot = _slot(env["data"], ANTHROPIC_HEAD)
    assert slot["state"] == P.SLOT_COOLDOWN
    assert slot["consecutive_failures"] == 1
    assert 9.0 <= _cooldown_minutes_left(slot) <= 10.0
    # expire the cooldown -> HALF_OPEN -> a failed trial DOUBLES (20m)
    slot["cooldown_until_utc"] = _iso(datetime.now(timezone.utc) -
                                      timedelta(seconds=1))
    P.save_cascade(env["data"], {"slots": {ANTHROPIC_HEAD: slot}})
    _mark_pending(env["data"], candidate_hash="2" * 64)
    _produce(env, monkeypatch, transport=transport,
             models=[ANTHROPIC_HEAD, OWNER_ORDER[0]], mark=False)
    slot = _slot(env["data"], ANTHROPIC_HEAD)
    assert slot["state"] == P.SLOT_COOLDOWN     # trial failed again
    assert slot["consecutive_failures"] == 2
    assert 19.0 <= _cooldown_minutes_left(slot) <= 20.0
    # cap law: 4h ceiling no matter how many consecutive failures pile up
    slot["consecutive_failures"] = 50
    slot["cooldown_until_utc"] = _iso(datetime.now(timezone.utc) -
                                      timedelta(seconds=1))
    P.save_cascade(env["data"], {"slots": {ANTHROPIC_HEAD: slot}})
    _mark_pending(env["data"], candidate_hash="3" * 64)
    _produce(env, monkeypatch, transport=transport,
             models=[ANTHROPIC_HEAD, OWNER_ORDER[0]], mark=False)
    slot = _slot(env["data"], ANTHROPIC_HEAD)
    assert _cooldown_minutes_left(slot) <= P.TRANSIENT_COOLDOWN_CAP_MIN


def test_timeout_is_transient(env, monkeypatch, cfg):
    def transport(model, system, payload):
        if model == ANTHROPIC_HEAD:
            raise P.ProviderHTTPError("read timed out", status=None)
        return _valid()

    _produce(env, monkeypatch, transport=transport,
             models=[ANTHROPIC_HEAD, OWNER_ORDER[0]])
    slot = _slot(env["data"], ANTHROPIC_HEAD)
    assert slot["state"] == P.SLOT_COOLDOWN
    assert slot["cooldown_reason"] == P.TRIGGER_TRANSIENT
    assert 9.0 <= _cooldown_minutes_left(slot) <= 10.0
    assert _slot(env["data"], OWNER_ORDER[0])["state"] == P.SLOT_UP


def test_garbage_retries_same_model_once_with_suffix_then_falls(env,
                                                                monkeypatch,
                                                                cfg):
    head_calls = []

    def transport(model, system, payload):
        if model == ANTHROPIC_HEAD:
            head_calls.append(payload)
            return _garbage()
        return _valid()

    out = _produce(env, monkeypatch, transport=transport,
                   models=[ANTHROPIC_HEAD, OWNER_ORDER[5]])
    assert out["written"] == 1
    assert len(head_calls) == 2                 # SAME model, ONE retry
    assert head_calls[1].endswith(P.RETRY_SUFFIX)
    assert head_calls[0] != head_calls[1]
    slot = _slot(env["data"], ANTHROPIC_HEAD)
    assert slot["state"] == P.SLOT_UP           # soft fail, no cooldown yet
    assert len(slot["soft_fails_utc"]) == 1
    # the opinion came from the fallback slot
    ops = (G.ai_review_dir(env["data"]) / "opinions_v2").glob("m1_*.json")
    op = json.loads(next(ops).read_text())
    assert op["model_id"] == OWNER_ORDER[5]


def test_garbage_3_soft_fails_within_1h_cooldowns_30m(env, monkeypatch,
                                                      cfg):
    for i in range(3):
        _mark_pending(env["data"], candidate_hash=f"{i}" * 64)

        def transport(model, system, payload):
            if model == ANTHROPIC_HEAD:
                return _garbage()
            return _valid()

        out = _produce(env, monkeypatch, transport=transport,
                       models=[ANTHROPIC_HEAD, OWNER_ORDER[5]], mark=False)
        assert out["written"] == 1
    slot = _slot(env["data"], ANTHROPIC_HEAD)
    assert slot["state"] == P.SLOT_COOLDOWN
    assert slot["cooldown_reason"] == "soft_fails_3_in_1h"
    assert 29.0 <= _cooldown_minutes_left(slot) <= 30.0
    # the 4th pass never asks the head (cool) and still produces
    _mark_pending(env["data"], candidate_hash="9" * 64)
    out = _produce(env, monkeypatch, transport=transport,
                   models=[ANTHROPIC_HEAD, OWNER_ORDER[5]], mark=False)
    assert out["written"] == 1


def test_404_config_broken_removed_until_config_change(env, monkeypatch,
                                                       cfg):
    calls = []

    def transport(model, system, payload):
        calls.append(model)
        if model == ANTHROPIC_HEAD:
            raise P.ProviderHTTPError("no endpoint for that model",
                                      status=404)
        return _valid()

    out = _produce(env, monkeypatch, transport=transport,
                   models=[ANTHROPIC_HEAD, OWNER_ORDER[0]])
    assert out["written"] == 1
    slot = _slot(env["data"], ANTHROPIC_HEAD)
    assert slot["config_broken"] is True
    assert slot["state"] == P.SLOT_COOLDOWN
    assert slot["cooldown_until_utc"] is None    # no clock: never re-tried
    assert "AI_CONFIG_BROKEN" in [e["kind"] for e in _events(env["data"])]
    # the NEXT pass never dials the broken slug again (removed until
    # config change) — the safe pending-slug behavior
    calls.clear()
    _mark_pending(env["data"], candidate_hash="4" * 64)
    _produce(env, monkeypatch, transport=transport,
             models=[ANTHROPIC_HEAD, OWNER_ORDER[0]], mark=False)
    assert ANTHROPIC_HEAD not in calls


def test_401_key_alarm_all_slots_cooldown_30m(env, monkeypatch, cfg):
    def transport(model, system, payload):
        if model == ANTHROPIC_HEAD:
            raise P.ProviderHTTPError("bad key", status=403)
        return _valid()

    out = _produce(env, monkeypatch, transport=transport,
                   models=[ANTHROPIC_HEAD, OWNER_ORDER[0]])
    assert out["written"] == 0 and out["provider_failed"] == 1
    assert "AI_KEY_ALARM" in [e["kind"] for e in _events(env["data"])]
    for m in (ANTHROPIC_HEAD, OWNER_ORDER[0]):
        slot = _slot(env["data"], m)
        assert slot["state"] == P.SLOT_COOLDOWN
        assert slot["cooldown_reason"] == P.TRIGGER_KEY_ALARM
        assert 29.0 <= _cooldown_minutes_left(slot) <= 30.0


# ------------------------------------------------------------ HALF_OPEN ----

def test_half_open_trial_success_climbs_back_to_up(env, monkeypatch, cfg):
    answers = {"head_fail": True}

    def transport(model, system, payload):
        if model == ANTHROPIC_HEAD and answers["head_fail"]:
            raise P.ProviderHTTPError("boom", status=500)
        return _valid()

    _produce(env, monkeypatch, transport=transport,
             models=[ANTHROPIC_HEAD, OWNER_ORDER[0]])
    slot = _slot(env["data"], ANTHROPIC_HEAD)
    slot["cooldown_until_utc"] = _iso(datetime.now(timezone.utc) -
                                      timedelta(seconds=1))
    P.save_cascade(env["data"], {"slots": {ANTHROPIC_HEAD: slot}})
    _mark_pending(env["data"], candidate_hash="5" * 64)
    answers["head_fail"] = False                # provider recovered
    out = _produce(env, monkeypatch, transport=transport,
                   models=[ANTHROPIC_HEAD, OWNER_ORDER[0]], mark=False)
    assert out["written"] == 1
    slot = _slot(env["data"], ANTHROPIC_HEAD)
    assert slot["state"] == P.SLOT_UP           # trial success
    assert slot["consecutive_failures"] == 0    # counters reset
    assert slot["cooldown_until_utc"] is None
    ev = _events(env["data"], kind="CASCADE_SLOT")
    assert any(e["model"] == ANTHROPIC_HEAD and
               e["from_state"] == P.SLOT_HALF_OPEN and
               e["to_state"] == P.SLOT_UP and
               e["trigger"] == "trial_success" for e in ev)


def test_half_open_trial_garbage_failure_doubles_cooldown(env, monkeypatch,
                                                          cfg):
    answers = {"head": "fail-transport"}

    def transport(model, system, payload):
        if model == ANTHROPIC_HEAD:
            if answers["head"] == "fail-transport":
                raise P.ProviderHTTPError("boom", status=500)
            return _garbage()                   # UP but now garbage
        return _valid()

    _produce(env, monkeypatch, transport=transport,
             models=[ANTHROPIC_HEAD, OWNER_ORDER[0]])
    slot = _slot(env["data"], ANTHROPIC_HEAD)
    slot["cooldown_until_utc"] = _iso(datetime.now(timezone.utc) -
                                      timedelta(seconds=1))
    P.save_cascade(env["data"], {"slots": {ANTHROPIC_HEAD: slot}})
    _mark_pending(env["data"], candidate_hash="6" * 64)
    answers["head"] = "garbage"                 # trial returns garbage
    _produce(env, monkeypatch, transport=transport,
             models=[ANTHROPIC_HEAD, OWNER_ORDER[0]], mark=False)
    slot = _slot(env["data"], ANTHROPIC_HEAD)
    assert slot["state"] == P.SLOT_COOLDOWN
    assert slot["cooldown_reason"] == "half_open_trial_failed"
    assert 19.0 <= _cooldown_minutes_left(slot) <= 20.0   # 2x the 10m base


# ------------------------------------------------------------------ U3.5 ----

def test_balance_below_low_balance_alarms_and_holds_paid_at_start(
        env, monkeypatch, cfg):
    paid, free = OWNER_ORDER[0], OWNER_ORDER[5]

    def balance_transport(url, key):
        assert url == "https://openrouter.ai/api/v1/key"
        return {"data": {"limit_remaining": 4.2}}

    _produce(env, monkeypatch,
             transport=lambda m, s, p: _valid(),
             models=[paid, free],
             balance_transport=balance_transport, low=10.0)
    slot = _slot(env["data"], paid)
    assert slot["state"] == P.SLOT_COOLDOWN
    assert slot["cooldown_until_utc"] is None
    assert slot["cooldown_reason"] == P.TRIGGER_LOW_BALANCE
    assert _slot(env["data"], free)["state"] == P.SLOT_UP
    lows = [e for e in _events(env["data"]) if e["kind"] == "AI_LOW_BALANCE"]
    assert lows and lows[0]["balance_usd"] == 4.2
    # a SUCCESSFUL check above the floor revives the held paid slot
    _mark_pending(env["data"], candidate_hash="7" * 64)

    def balance_ok(url, key):
        return {"data": {"limit_remaining": 25.0}}

    _produce(env, monkeypatch, transport=lambda m, s, p: _valid(),
             models=[paid, free], balance_transport=balance_ok, low=10.0,
             mark=False)
    assert _slot(env["data"], paid)["state"] == P.SLOT_UP


def test_check_balance_parses_shapes_and_never_crashes():
    assert P.check_balance("https://x/api/v1/chat/completions", "k",
                           transport=lambda u, k:
                           {"data": {"limit_remaining": 12.5}}) == 12.5
    assert P.check_balance("https://x/api/v1/chat/completions", "k",
                           transport=lambda u, k:
                           {"data": {"limit": 100, "usage": 37.5}}) == 62.5
    assert P.check_balance("https://x/api/v1/chat/completions", "k",
                           transport=lambda u, k:
                           {"data": {"limit": None}}) is None  # unlimited

    def _boom(url, key):
        raise OSError("network down")
    assert P.check_balance("https://x/api/v1/chat/completions", "k",
                           transport=_boom) is None


# ------------------------------------------------------------------ U3.6 ----

def test_budget_clock_stops_round_and_leaves_candidates_pending(
        env, monkeypatch, cfg):
    _mark_pending(env["data"], "m1", "a" * 64)
    _mark_pending(env["data"], "m2", "b" * 64)
    import time as _t

    def transport(model, system, payload):
        _t.sleep(0.12)                          # one request burns the round
        return _valid()

    out = _produce(env, monkeypatch, transport=transport,
                   models=[ANTHROPIC_HEAD], budget=0.05, mark=False)
    assert out["budget_stopped"] is True
    assert out["written"] == 1                  # m1 only
    assert out["left_pending"] >= 1
    pending = G._load_pending(env["data"])
    assert "m2" in pending                      # stays pending, never killed
    # the skipped candidate carries NO producer attempt stamp (the next
    # pass is not throttled by a round that never reviewed it)
    assert pending["m2"].get("producer_attempt_utc") is None


# ------------------------------------------------------------- QD2 laws ----

def test_all_slots_down_candidates_stay_pending_producer_returns(
        env, monkeypatch, cfg):
    def transport(model, system, payload):
        raise P.ProviderHTTPError("429", status=429)

    _mark_pending(env["data"], "m1", "a" * 64)
    out = _produce(env, monkeypatch, transport=transport,
                   models=[ANTHROPIC_HEAD, OWNER_ORDER[0]], mark=False)
    assert out["written"] == 0 and out["provider_failed"] == 1
    assert "m1" in G._load_pending(env["data"])   # silence law: still queued
    # second pass: all slots still down (429 floor 15m) -> honest failure,
    # no crash, no opinion
    _mark_pending(env["data"], "m1", "b" * 64)
    out = _produce(env, monkeypatch, transport=transport,
                   models=[ANTHROPIC_HEAD, OWNER_ORDER[0]], mark=False)
    assert out["written"] == 0 and out["provider_failed"] == 1
    assert "m1" in G._load_pending(env["data"])


def test_u0_citation_filter_survives_the_cascade(env, monkeypatch, cfg):
    """The U0/H1 law is intact: an ALLOW whose model citations were
    fabricated (not in the captured set) is INVALID after the cascade."""
    def transport(model, system, payload):
        return _valid("ALLOW", sources=[{"url": "https://invented.example",
                                         "excerpt": "made up"}])

    out = _produce(env, monkeypatch, transport=transport,
                   models=[ANTHROPIC_HEAD])
    assert out["invalid"] == 1 and out["written"] == 0
    assert "m1" in G._load_pending(env["data"])   # candidate keeps waiting
    invalids = list((G.ai_review_dir(env["data"]) / "opinions_v2" /
                     ".invalid").glob("m1_*.json"))
    assert invalids and "U0/H1" in json.loads(
        invalids[0].read_text())["invalid_why"]


def test_parse_v2_laws_intact():
    ok = P.parse_v2(_valid("VETO"))
    assert ok["ok"] and ok["verdict"] == "VETO"
    bad = P.parse_v2('{"verdict": "SWITCH", "reason_codes": ["R"], '
                     '"summary": "s"}')
    assert not bad["ok"]
    assert not P.parse_v2(_garbage())["ok"]
