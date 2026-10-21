"""B1R fail-closed battery (SOCCER-INTL-B1R-PAPER-SWITCH-V1 law; owner
instruction 2026-10-10; ERRATUM_2 E-1 disposition 2). After the pinned
switch_ts a SOCCER DECISION grounds ONLY in a validated B1R_SOCCER forecast
row; a B1-only match journals NOT_RUN_NO_B1R_FORECAST (stake 0, terminal).
Offline + deterministic; sandbox ledgers only; the REAL ledger is asserted
byte-unchanged across every test here."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from research.papertrade_exec import (  # noqa: E402
    EXIT_PIN_DRIFT, GO_PHRASE, BlockError, execute, adapters as A)
from research.papertrade_exec.execute import main as cli  # noqa: E402

NOW = "2026-10-06T00:00:00Z"
SOC_DAY = "2026-10-12"         # synthetic rehearsal fixtures (battery law)
REAL_LEDGER = Path(os.path.expanduser(
    "~/.my-quantitative-data/sports-papertrade-exec-v1/ledger/"
    "paper_ledger.jsonl"))


@pytest.fixture()
def real_ledger_untouched():
    """The REAL ledger is never written by this battery — sha asserted."""
    before = hashlib.sha256(REAL_LEDGER.read_bytes()).hexdigest()
    yield before
    assert hashlib.sha256(REAL_LEDGER.read_bytes()).hexdigest() == before, \
        "REAL ledger changed during a sandbox battery — violation"


@pytest.fixture()
def fresh_guard_globals():
    """Reset the module-level guard caches around each test."""
    execute._B1R_SWITCH_VERIFIED = False
    execute._B1R_MAP = None
    yield
    execute._B1R_SWITCH_VERIFIED = False
    execute._B1R_MAP = None


@pytest.fixture()
def env(tmp_path):
    """Pristine sandbox env (same fabrication law as the exec battery: the
    sandbox control copy is the ONLY fabricated GO here)."""
    data = tmp_path / "sandbox-data"
    ctrl = data / "sandbox" / "control"
    ctrl.mkdir(parents=True)
    (ctrl / "GO_TOKEN.json").write_text(json.dumps({
        "go_phrase_typed_by_owner": GO_PHRASE,
        "typed_at_utc": "2026-10-07T00:00:00Z",
        "transcribed_by": "TEST-SANDBOX-FABRICATION (not an owner GO)",
        "registry_consumption_note": "SANDBOX copy only; real phase untouched",
    }))
    reg = json.loads((REPO / "plans" / "CYCLE_REGISTRY.json").read_text())
    cycles = reg.get("cycles", reg)
    row = cycles.get("SPORTS-PAPERTRADE-EXEC-V1") if isinstance(cycles, dict) \
        else next(c for c in cycles
                  if c.get("cycle_id") == "SPORTS-PAPERTRADE-EXEC-V1")
    row["phase"] = "ACTIVE (EXEC_GO_CONSUMED_VIA_SPORTS-PAPERTRADE-EXEC-V1 " \
                   "[SANDBOX TEST COPY])"
    (ctrl / "CYCLE_REGISTRY.json").write_text(json.dumps(reg, indent=1))
    return {"data": data, "ctrl": ctrl}


@pytest.fixture()
def capcli(capsys):
    def _run(env_, *argv, sandbox=True, now=NOW):
        args = ["--data-root", str(env_["data"])]
        if sandbox:
            args += ["--sandbox", "--now", now]
        code = cli(args + list(argv))
        raw = capsys.readouterr().out
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"_raw": raw}
        return code, parsed
    return _run


# ------------------------------------------------------------------ helpers --

def _core():
    return execute.load_pinned_core(roots={})


def _open_ledger(env_):
    led = _core().ledger.PaperLedger(
        env_["data"] / "sandbox" / "sandbox_ledger.jsonl")
    led.load()
    return led


def _genesis(env_):
    """Fresh sandbox ledger + genesis (re-opened every time)."""
    led = _open_ledger(env_)
    if not led.rows:
        led.genesis(plan_sha256="b1r-battery", created_at_utc=NOW,
                    sandbox=True)
    return _open_ledger(env_)


def ledger_rows(env_):
    p = env_["data"] / "sandbox" / "sandbox_ledger.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def rows_of(env_, type_, status=None):
    return [r for r in ledger_rows(env_)
            if r.get("type") == type_ and (status is None or r.get("status") == status)]


def _anchor_of(fx) -> str:
    from datetime import datetime, timedelta, timezone
    ko = datetime.strptime(fx.kickoff_utc, "%Y-%m-%dT%H:%M:%SZ")\
        .replace(tzinfo=timezone.utc)
    return (ko - timedelta(seconds=execute.SOCCER_LEAD_SECONDS))\
        .strftime("%Y-%m-%dT%H:%M:%SZ")


def _inject_b1_control(env_, fx, p=None) -> dict:
    """A lawful B1 control FORECAST row (the pre-switch row shape: no
    model_id, model_version_sha soccer_b1_replay). Re-opens the ledger so
    the on-disk tail is always the append base (the shared core refuses a
    stale in-memory chain)."""
    led = _open_ledger(env_)
    row = {
        "type": "FORECAST", "league": "SOCCER",
        "match_id": fx.match_id, "competition": fx.competition,
        "home": fx.home, "away": fx.away, "kickoff_utc": fx.kickoff_utc,
        "recorded_at_utc": NOW, "anchor_utc": _anchor_of(fx),
        "model_version_sha": "soccer_b1_replay",
        "p": p or A.synthetic_three_way_p(fx.match_id),
        "source_ref": "soccer_b1_replay (battery control)", "mode": "ENGINE",
        "fixture_source": fx.source_ref,
    }
    return led.append(row)


def _inject_b1r_via_emission(env_, fx) -> dict:
    """Append the B1R twin through the REAL emission path (control already
    present)."""
    led = _open_ledger(env_)
    ns = argparse.Namespace(sandbox=True, sandbox_registry=str(
        env_["data"] / "sandbox" / "control" / "CYCLE_REGISTRY.json"))
    execute.b1r_switch_ts_verified(ns.sandbox_registry)
    emitted = execute.emit_b1r_forecasts(led, [fx], NOW)
    assert len(emitted) == 1, emitted
    return next(r for r in _open_ledger(env_).rows
                if r.get("row_sha256") == emitted[0]["row_sha256"])


def _inject_quote(env_, fx, odds=None) -> dict:
    led = _open_ledger(env_)
    p = A.synthetic_three_way_p(fx.match_id)
    row = {
        "type": "MARKET_QUOTE", "league": "SOCCER", "match_id": fx.match_id,
        "home": fx.home, "away": fx.away, "kickoff_utc": fx.kickoff_utc,
        "bookmaker": "SYNTHETIC_BOOK (rehearsal)", "market": "h2h",
        "odds": odds or A.synthetic_odds(fx.match_id, p),
        "fetch_ts_utc": NOW, "source_last_update_utc": NOW,
        "commence_time_utc": fx.kickoff_utc,
        "payload_sha256": hashlib.sha256(fx.match_id.encode()).hexdigest(),
        "key_fingerprint": "sandbox-synthetic-00", "mode": "SYNTHETIC",
        "source_ref": "SYNTHETIC_ODDS_REHEARSAL (battery)",
    }
    return led.append(row)


# ------------------------------------------------------------------- tests --

def decs_for(env_, fx):
    return [r for r in rows_of(env_, "DECISION")
            if r.get("match_id") == fx.match_id]



def test_switch_ts_verified_against_registry(env, fresh_guard_globals):
    """The pinned switch_ts must match the B1R cycle's registry GO record;
    a tampered registry blocks loudly (fail-closed, nothing inferred)."""
    reg_real = REPO / "plans" / "CYCLE_REGISTRY.json"
    assert execute.b1r_switch_ts_verified(reg_real) is True
    reg = json.loads(reg_real.read_text())
    cycles = reg.get("cycles", reg)
    row = cycles.get(execute.B1R_SWITCH_CYCLE) if isinstance(cycles, dict) \
        else next(c for c in cycles
                  if c.get("cycle_id") == execute.B1R_SWITCH_CYCLE)
    row["go_phrase_state"] = "OWNER_GO_TYPED_LIVE 2020-01-01T00:00:00Z wrong"
    tampered = env["data"] / "tampered_registry.json"
    tampered.write_text(json.dumps(reg))
    execute._B1R_SWITCH_VERIFIED = False
    with pytest.raises(BlockError) as ei:
        execute.b1r_switch_ts_verified(tampered)
    assert ei.value.code == "BLOCKED_B1R_SWITCH_TS_UNVERIFIED"


def test_emission_appends_b1r_twin_and_is_idempotent(env, fresh_guard_globals,
                                                     real_ledger_untouched):
    """GO-packet step 1: a B1 control row gets exactly one B1R twin via the
    frozen adapter; rerun adds nothing (duplicate law T3)."""
    fx = execute.synthetic_soccer_fixtures(SOC_DAY)[0]
    _genesis(env)
    b1 = _inject_b1_control(env, fx)
    reg = str(env["data"] / "sandbox" / "control" / "CYCLE_REGISTRY.json")
    execute.b1r_switch_ts_verified(reg)
    emitted = execute.emit_b1r_forecasts(_open_ledger(env), [fx], NOW)
    assert len(emitted) == 1
    led2 = _open_ledger(env)
    twin = next(r for r in led2.rows
                if r.get("model_id") == "B1R_SOCCER")
    assert twin["control_ref_row_sha256"] == b1["row_sha256"]
    assert twin["map_sha256"] == execute.B1R_MAP_INNER_SHA
    assert twin["model_version_sha"] == "soccer_b1r_v1"
    assert twin["recorded_at_utc"] == NOW
    # byte-exact frozen transform (T6)
    m = execute.b1r_map()
    t = execute._b1r_adapter().b1r_transform(
        b1["p"]["HOME"], b1["p"]["DRAW"], b1["p"]["AWAY"], m)
    assert twin["p"] == t
    # idempotent: second emission pass appends nothing
    assert execute.emit_b1r_forecasts(led2, [fx], NOW) == []
    assert len([r for r in _open_ledger(env).rows
                if r.get("model_id") == "B1R_SOCCER"]) == 1


def test_emission_refuses_after_anchor(env, fresh_guard_globals,
                                       real_ledger_untouched):
    """No backfill: when the anchor has passed, emission must not create a
    late B1R row (the B1 control row stays alone; decide will refuse)."""
    fx = execute.synthetic_soccer_fixtures(SOC_DAY)[0]
    _genesis(env)
    _inject_b1_control(env, fx)
    execute.b1r_switch_ts_verified(str(
        env["data"] / "sandbox" / "control" / "CYCLE_REGISTRY.json"))
    late = _anchor_of(fx)                       # at the anchor == refused
    assert execute.emit_b1r_forecasts(_open_ledger(env), [fx], late) == []
    assert [r for r in _open_ledger(env).rows
            if r.get("model_id") == "B1R_SOCCER"] == []


def test_decide_b1_only_journals_not_run_no_b1r(env, capcli,
                                                fresh_guard_globals,
                                                real_ledger_untouched):
    """THE core law: a B1-only match is NEVER silently decided on B1 — the
    decision is NOT_RUN_NO_B1R_FORECAST, stake 0, terminal."""
    fx = execute.synthetic_soccer_fixtures(SOC_DAY)[0]
    _genesis(env)
    _inject_b1_control(env, fx)
    _inject_quote(env, fx)                      # quote present: still refused
    code, out = capcli(env, "decide", "--league", "SOCCER", "--date", SOC_DAY)
    assert code == 0, out
    decs = decs_for(env, fx)
    assert len(decs) == 1
    d = decs[0]
    assert d["status"] == "NOT_RUN_NO_B1R_FORECAST"
    assert d["stake_cents"] == 0 and d["chosen_leg"] is None
    assert "CONTROL-ONLY" in d["reason"]
    assert rows_of(env, "DECISION", "BET_PAPER") == []


def test_decide_success_path_cites_b1r_row(env, capcli, fresh_guard_globals,
                                           real_ledger_untouched):
    """Success: valid control + twin + quote -> the decision proceeds and
    cites the exact B1R row (model_id B1R_SOCCER + map pin + control ref)."""
    fx = execute.synthetic_soccer_fixtures(SOC_DAY)[0]
    _genesis(env)
    _inject_b1_control(env, fx)
    _inject_b1r_via_emission(env, fx)
    _inject_quote(env, fx, odds={"HOME": 3.0, "DRAW": 3.0, "AWAY": 3.0})
    code, out = capcli(env, "decide", "--league", "SOCCER", "--date", SOC_DAY)
    assert code == 0, out
    decs = decs_for(env, fx)
    assert len(decs) == 1
    d = decs[0]
    assert d["status"] in ("BET_PAPER", "NO_EDGE")
    assert d["model_id"] == "B1R_SOCCER"
    twin = next(r for r in ledger_rows(env)
                if r.get("model_id") == "B1R_SOCCER")
    assert d["decision_forecast_row_sha256"] == twin["row_sha256"]
    assert d["map_sha256"] == execute.B1R_MAP_INNER_SHA
    assert d["control_ref_row_sha256"] == twin["control_ref_row_sha256"]
    # the frozen p the decision used IS the B1R transform
    assert d["p_frozen"] == twin["p"]


def test_decide_b1r_recorded_after_anchor_refused(env, capcli, fresh_guard_globals,
                                                  real_ledger_untouched):
    """A B1R row stamped at/after its anchor is not a decision basis."""
    fx = execute.synthetic_soccer_fixtures(SOC_DAY)[0]
    _genesis(env)
    b1 = _inject_b1_control(env, fx)
    execute.b1r_switch_ts_verified(str(
        env["data"] / "sandbox" / "control" / "CYCLE_REGISTRY.json"))
    led = _open_ledger(env)
    ad = execute._b1r_adapter()
    m = execute.b1r_map()
    (row,) = ad.build_forecast_rows(b1, m)
    row["recorded_at_utc"] = _anchor_of(fx)      # AT the anchor == refused
    led.append(row)
    _inject_quote(env, fx)
    code, out = capcli(env, "decide", "--league", "SOCCER", "--date", SOC_DAY)
    decs = decs_for(env, fx)
    assert len(decs) == 1 and \
        decs[0]["status"] == "NOT_RUN_NO_B1R_FORECAST"
    assert "anchor" in decs[0]["reason"]


def test_decide_wrong_map_pin_refused(env, capcli, fresh_guard_globals,
                                      real_ledger_untouched):
    """A B1R row whose map_sha256 drifted from the frozen pin is refused."""
    fx = execute.synthetic_soccer_fixtures(SOC_DAY)[0]
    _genesis(env)
    b1 = _inject_b1_control(env, fx)
    execute.b1r_switch_ts_verified(str(
        env["data"] / "sandbox" / "control" / "CYCLE_REGISTRY.json"))
    led = _open_ledger(env)
    ad = execute._b1r_adapter()
    m = execute.b1r_map()
    (row,) = ad.build_forecast_rows(b1, m)
    row["recorded_at_utc"] = NOW
    row["map_sha256"] = "f" * 64                 # drifted pin
    led.append(row)
    _inject_quote(env, fx)
    capcli(env, "decide", "--league", "SOCCER", "--date", SOC_DAY)
    decs = decs_for(env, fx)
    assert len(decs) == 1 and \
        decs[0]["status"] == "NOT_RUN_NO_B1R_FORECAST"
    assert "map_sha256" in decs[0]["reason"]


def test_decide_transform_mismatch_refused(env, capcli, fresh_guard_globals,
                                           real_ledger_untouched):
    """T4/T6 at decision time: a B1R row that is NOT the byte-exact frozen
    transform of its control B1 p is refused (same-snapshot law)."""
    fx = execute.synthetic_soccer_fixtures(SOC_DAY)[0]
    _genesis(env)
    b1 = _inject_b1_control(env, fx)
    execute.b1r_switch_ts_verified(str(
        env["data"] / "sandbox" / "control" / "CYCLE_REGISTRY.json"))
    led = _open_ledger(env)
    ad = execute._b1r_adapter()
    m = execute.b1r_map()
    (row,) = ad.build_forecast_rows(b1, m)
    row["recorded_at_utc"] = NOW
    row["p"] = {"HOME": row["p"]["HOME"] - 0.01,
                "DRAW": row["p"]["DRAW"] + 0.01,
                "AWAY": row["p"]["AWAY"]}       # not the frozen transform
    led.append(row)
    _inject_quote(env, fx)
    capcli(env, "decide", "--league", "SOCCER", "--date", SOC_DAY)
    decs = decs_for(env, fx)
    assert len(decs) == 1 and \
        decs[0]["status"] == "NOT_RUN_NO_B1R_FORECAST"
    assert "byte-exact" in decs[0]["reason"]


def test_decide_control_payload_mismatch_refused(env, capcli, fresh_guard_globals,
                                                 real_ledger_untouched):
    """T4: the twin's recorded control payload must equal the control row's
    p (same snapshot/derivation) — a mismatch refuses."""
    fx = execute.synthetic_soccer_fixtures(SOC_DAY)[0]
    _genesis(env)
    b1 = _inject_b1_control(env, fx)
    execute.b1r_switch_ts_verified(str(
        env["data"] / "sandbox" / "control" / "CYCLE_REGISTRY.json"))
    led = _open_ledger(env)
    ad = execute._b1r_adapter()
    m = execute.b1r_map()
    (row,) = ad.build_forecast_rows(b1, m)
    row["recorded_at_utc"] = NOW
    row["p_control_b1"] = {"HOME": 0.4, "DRAW": 0.3, "AWAY": 0.3}
    led.append(row)
    _inject_quote(env, fx)
    capcli(env, "decide", "--league", "SOCCER", "--date", SOC_DAY)
    decs = decs_for(env, fx)
    assert len(decs) == 1 and \
        decs[0]["status"] == "NOT_RUN_NO_B1R_FORECAST"
    assert "p_control_b1" in decs[0]["reason"]


def test_decide_control_ref_unresolvable_refused(env, capcli, fresh_guard_globals,
                                                 real_ledger_untouched):
    """A B1R row whose control_ref points nowhere (or at a non-B1 row) is
    refused — 'B1 control exists but twin broken' family."""
    fx = execute.synthetic_soccer_fixtures(SOC_DAY)[0]
    _genesis(env)
    b1 = _inject_b1_control(env, fx)
    execute.b1r_switch_ts_verified(str(
        env["data"] / "sandbox" / "control" / "CYCLE_REGISTRY.json"))
    led = _open_ledger(env)
    ad = execute._b1r_adapter()
    m = execute.b1r_map()
    (row,) = ad.build_forecast_rows(b1, m)
    row["recorded_at_utc"] = NOW
    row["control_ref_row_sha256"] = "e" * 64    # resolves to nothing
    led.append(row)
    _inject_quote(env, fx)
    capcli(env, "decide", "--league", "SOCCER", "--date", SOC_DAY)
    decs = decs_for(env, fx)
    assert len(decs) == 1 and \
        decs[0]["status"] == "NOT_RUN_NO_B1R_FORECAST"
    assert "resolve" in decs[0]["reason"]


def test_decide_duplicate_b1r_rows_refused(env, capcli, fresh_guard_globals,
                                           real_ledger_untouched):
    """Two B1R rows for one match are ambiguous — fail-closed, never pick."""
    fx = execute.synthetic_soccer_fixtures(SOC_DAY)[0]
    _genesis(env)
    b1 = _inject_b1_control(env, fx)
    execute.b1r_switch_ts_verified(str(
        env["data"] / "sandbox" / "control" / "CYCLE_REGISTRY.json"))
    led = _open_ledger(env)
    ad = execute._b1r_adapter()
    m = execute.b1r_map()
    for stamp in (NOW, "2026-10-06T00:00:01Z"):
        (row,) = ad.build_forecast_rows(b1, m)
        row["recorded_at_utc"] = stamp
        led.append(row)                          # deliberate battery duplicate
    _inject_quote(env, fx)
    capcli(env, "decide", "--league", "SOCCER", "--date", SOC_DAY)
    decs = decs_for(env, fx)
    assert len(decs) == 1 and \
        decs[0]["status"] == "NOT_RUN_NO_B1R_FORECAST"
    assert "ambiguous" in decs[0]["reason"]


def test_decide_already_decided_is_terminal(env, capcli, fresh_guard_globals,
                                            real_ledger_untouched):
    """A decided match is never re-decided, with or without a B1R row."""
    fx = execute.synthetic_soccer_fixtures(SOC_DAY)[0]
    _genesis(env)
    _inject_b1_control(env, fx)
    _inject_quote(env, fx)
    code, _ = capcli(env, "decide", "--league", "SOCCER", "--date", SOC_DAY)
    first = decs_for(env, fx)
    assert len(first) == 1 and \
        first[0]["status"] == "NOT_RUN_NO_B1R_FORECAST"
    # the decision is terminal; a later twin append cannot reopen it —
    # emission itself skips decided matches, and decide must still skip
    execute.b1r_switch_ts_verified(str(
        env["data"] / "sandbox" / "control" / "CYCLE_REGISTRY.json"))
    assert execute.emit_b1r_forecasts(_open_ledger(env), [fx], NOW) == []
    code, out = capcli(env, "decide", "--league", "SOCCER", "--date", SOC_DAY)
    assert code == 0
    assert any(sk["match_id"] == fx.match_id
               for sk in out.get("skipped", []))
    assert len(decs_for(env, fx)) == 1          # nothing re-appended


def test_decide_restart_idempotent(env, capcli, fresh_guard_globals,
                                   real_ledger_untouched):
    """Service restart = stateless re-derivation: a second decide run after
    a lawful decision appends nothing (row count + tail sha stable)."""
    fx = execute.synthetic_soccer_fixtures(SOC_DAY)[0]
    _genesis(env)
    _inject_b1_control(env, fx)
    _inject_b1r_via_emission(env, fx)
    _inject_quote(env, fx)
    capcli(env, "decide", "--league", "SOCCER", "--date", SOC_DAY)
    rows1 = ledger_rows(env)
    tail1 = rows1[-1]["row_sha256"]
    capcli(env, "decide", "--league", "SOCCER", "--date", SOC_DAY)
    rows2 = ledger_rows(env)
    assert len(rows2) == len(rows1) and rows2[-1]["row_sha256"] == tail1


def test_map_file_drift_blocks_loudly(env, fresh_guard_globals,
                                      real_ledger_untouched, monkeypatch):
    """T1: a drifted MAP FILE is a HARD block (never a per-match NOT_RUN,
    never a decision)."""
    ad = execute._b1r_adapter()

    def _drifted(path=ad.MAP_PATH):
        raise ad.Refuse("MAP_PIN_DRIFT_FILE_SHA")

    monkeypatch.setattr(ad, "load_map_verified", _drifted)
    execute._B1R_MAP = None
    with pytest.raises(BlockError) as ei:
        execute.b1r_map()
    assert ei.value.code == "BLOCKED_B1R_MAP_PIN"
    assert ei.value.exit_code == EXIT_PIN_DRIFT


def test_rerun_forecast_emits_nothing_new(env, capcli, fresh_guard_globals,
                                          real_ledger_untouched):
    """forecast rerun on a match that already has control+twin: no second
    twin, no second control (append-only idempotency at the CLI level)."""
    fx = execute.synthetic_soccer_fixtures(SOC_DAY)[0]
    _genesis(env)
    _inject_b1_control(env, fx)
    _inject_b1r_via_emission(env, fx)
    code, out = capcli(env, "forecast", "--league", "SOCCER",
                       "--date", SOC_DAY)
    assert code == 0
    fcs = rows_of(env, "FORECAST")
    assert len([r for r in fcs
                if r.get("model_id") == "B1R_SOCCER"]) == 1
    assert len([r for r in fcs
                if r.get("model_version_sha") == "soccer_b1_replay"]) == 1


def test_run_day_sandbox_soccer_journals_no_b1r(env, capcli,
                                                fresh_guard_globals,
                                                real_ledger_untouched):
    """Full sandbox chain on synthetic fixtures (no B1R rows anywhere):
    every SOCCER decision is the terminal NOT_RUN_NO_B1R_FORECAST journal —
    the whole-desk run stays OK while soccer refuses lawfully."""
    code, out = capcli(env, "run-day", "--date", SOC_DAY)
    assert code == 0, out
    soc = out["leagues"]["SOCCER"]
    assert soc["status"] == "OK"
    # WSL lane refuses at its sandbox quote seam and is contained per-league
    # (never a crashed batch, never a swallowed safety code)
    assert out["leagues"]["WSL"]["status"] == "BLOCKED_NO_QUOTE_PLUMBING"
    assert len(soc["decide"]["journaled"]) == 3
    decs = rows_of(env, "DECISION", "NOT_RUN_NO_B1R_FORECAST")
    assert len(decs) == 3
    assert all(d["stake_cents"] == 0 and d["chosen_leg"] is None
               for d in decs)
    assert rows_of(env, "DECISION", "BET_PAPER") == []   # soccer-only day
