"""Adversarial battery for the SPORTS-PAPERTRADE-EXEC-V1 LIVE SERVICE layer
(ERRATUM_EXEC_5): sandbox-only, deterministic — DST/anchor windows, quota
fail-closed, crash/restart, idempotency, concurrent supervisor, non-FINAL
scores, settlement math, dashboard stale/tamper, live HTTP surface.

The runner's own refusal laws are battery-tested (test_exec_battery.py, 51
tests); these tests cover the supervisor/dashboard layer AROUND it. Nothing
here touches the real ledger, the real registry, or any API key."""
from __future__ import annotations

import fcntl
import json
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from research.papertrade_exec import BlockError, execute               # noqa
from research.papertrade_exec import live_dashboard, results_fetch, ops_service  # noqa
from research.papertrade_exec.ops_service import OpsService            # noqa

NOW_FMT = "%Y-%m-%dT%H:%M:%SZ"


def iso_z(dt: datetime) -> str:
    return dt.strftime(NOW_FMT)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ------------------------------------------------------------------- helpers --

@pytest.fixture()
def env(tmp_path):
    """Pristine SANDBOX env with the only fabricated gate copies allowed
    (sandbox control dir + sandbox registry mirror; the real control dir and
    the real registry are never touched)."""
    data = tmp_path / "sandbox-data"
    ctrl = data / "sandbox" / "control"
    ctrl.mkdir(parents=True)
    (ctrl / "GO_TOKEN.json").write_text(json.dumps({
        "go_phrase_typed_by_owner": "GO SPORTS PAPERTRADE EXEC V1 RUN ALL",
        "typed_at_utc": "2026-10-07T00:00:00Z",
        "transcribed_by": "TEST-SANDBOX-FABRICATION (not an owner GO)",
        "registry_consumption_note": "SANDBOX copy only; real phase untouched",
    }))
    reg = json.loads((REPO / "plans" / "CYCLE_REGISTRY.json").read_text())
    cycles = reg.get("cycles", reg)
    row = cycles.get("SPORTS-PAPERTRADE-EXEC-V1") if isinstance(cycles, dict) \
        else next(c for c in cycles
                  if c.get("cycle_id") == "SPORTS-PAPERTRADE-EXEC-V1")
    row["phase"] = "ACTIVE (EXEC_GO_CONSUMED [SANDBOX TEST COPY])"
    (ctrl / "CYCLE_REGISTRY.json").write_text(json.dumps(reg, indent=1))
    return {"data": data, "ctrl": ctrl}


def make_svc(env, **kw) -> OpsService:
    return OpsService(data_root=env["data"], sandbox=True,
                      serve=False, once=True, **kw)


def sandbox_ledger_path(env) -> Path:
    return env["data"] / "sandbox" / "sandbox_ledger.jsonl"


def seed_open_bet(env, *, league="WNBA", match_id="401918297T",
                  home="AAA", away="BBB", kickoff="2026-10-07T23:30:00Z",
                  competition="SEMI", chosen="HOME",
                  odds=None) -> dict:
    """Fabricate a labeled SANDBOX chain: GENESIS + FORECAST + QUOTE +
    BET_PAPER decision with kickoff in the past (settle-due)."""
    core = execute.load_pinned_core(roots={})
    led = core.ledger.PaperLedger(sandbox_ledger_path(env)).load()
    led.genesis(plan_sha256="ops-test-sandbox", sandbox=True)
    outcomes = ["HOME", "DRAW", "AWAY"] if league == "SOCCER" \
        else ["HOME", "AWAY"]
    odds = odds or {k: v for k, v in zip(outcomes,
                                         (1.79, 3.5, 2.04))}
    led.append({"type": "FORECAST", "league": league, "match_id": match_id,
                "home": home, "away": away, "competition": competition,
                "kickoff_utc": kickoff, "p": {k: 1 / len(outcomes)
                                              for k in outcomes},
                "model_id": "TEST_SYNTHETIC", "model_constants": {},
                "recorded_at_utc": "2026-10-01T00:00:00Z",
                "mode": "SYNTHETIC",
                "source_ref": "TEST-SANDBOX-FABRICATION"})
    led.append({"type": "MARKET_QUOTE", "league": league,
                "match_id": match_id, "home": home, "away": away,
                "competition": competition, "kickoff_utc": kickoff,
                "odds": odds, "bookmaker": "pinnacle", "market": "h2h",
                "fetch_ts_utc": "2026-10-01T00:05:00Z",
                "source_last_update_utc": "2026-10-01T00:04:00Z",
                "commence_time_utc": kickoff, "payload_sha256": "0" * 64,
                "key_fingerprint": None,
                "source_ref": "TEST-SANDBOX-FABRICATION"})
    dec = {"type": "DECISION", "league": league, "match_id": match_id,
           "home": home, "away": away, "competition": competition,
           "kickoff_utc": kickoff, "decided_at_utc": "2026-10-01T00:06:00Z",
           "model_id": "TEST_SYNTHETIC", "model_constants": {},
           "stake_cents": 500, "chosen_leg": chosen, "p_frozen": {},
           "odds_frozen": odds,
           "ev_net_by_leg": {k: 0.06 for k in outcomes},
           "quote_meta": None, "forecast_meta": None,
           "status": "BET_PAPER", "reason": "TEST-SANDBOX-FABRICATION"}
    led.append_decision(dec, recheck=lambda d: d)
    return dec


def ledger_rows(env) -> list[dict]:
    p = sandbox_ledger_path(env)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def incidents(env) -> list[dict]:
    p = env["data"] / "sandbox" / "ops" / "state" / "incidents.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def espn_payload(match_id, *, completed, home_abbr="AAA", away_abbr="BBB",
                 home_score="100", away_score="98", state="post",
                 detail="Final") -> dict:
    st = {"state": state, "completed": completed, "detail": detail}
    return {"events": [{
        "id": match_id, "date": "2026-10-07T23:30Z", "name": "BBB at AAA",
        "competitions": [{"status": {"type": st},
                          "competitors": [
                              {"homeAway": "home",
                               "team": {"abbreviation": home_abbr},
                               "score": home_score},
                              {"homeAway": "away",
                               "team": {"abbreviation": away_abbr},
                               "score": away_score}]}]}]}


# ------------------------------------------------------- DST / anchor windows --

def test_dst_fall_back_and_spring_forward_anchors_and_windows():
    """Anchor math (UTC) and ET-local-date mapping must survive both 2026 DST
    transitions; the policy window arithmetic never crosses the anchor."""
    from research.papertrade_exec import adapters as A
    mk = lambda mid, h, m: A.Fixture(  # noqa: E731
        league="WNBA", match_id=mid, home="H", away="A",
        kickoff_utc=iso_z(datetime(2026, 11, 1, h, m, tzinfo=timezone.utc)),
        competition="SEMI",
        source_ref="TEST-SANDBOX-FABRICATION",
        et_local_date=A.et_local_date(datetime(2026, 11, 1, h, m,
                                               tzinfo=timezone.utc)))
    fx = [mk("x1", 4, 0), mk("x2", 8, 0)]   # 00:00 EDT -> 03:00 EST Nov 1
    anchor, per = execute.batch_anchor(fx, "WNBA")
    assert anchor == "2026-10-31T21:50:00Z"          # T0-6h10m, UTC exact
    assert per["x1"] == anchor and per["x2"] == anchor
    assert {f.et_local_date for f in fx} == {"2026-11-01"}
    # spring forward 2027-03-14
    dt = datetime(2027, 3, 14, 7, 0, tzinfo=timezone.utc)
    assert A.et_local_date(dt) == "2027-03-14"       # 03:00 EDT, no gap crash
    # window eligibility: inside lookahead -> True; beyond -> False; past -> False
    now = utcnow()
    f_in = {"anchor_utc": iso_z(now + timedelta(hours=2)),
            "eligible_now": True}
    f_far = {"anchor_utc": iso_z(now + timedelta(hours=72)),
             "eligible_now": True}
    f_past = {"anchor_utc": iso_z(now - timedelta(hours=2)),
              "eligible_now": False}
    look = {"NBA": 24, "WNBA": 24, "SOCCER": 48}
    assert OpsService.window_eligible(f_in, "WNBA", now, look)
    assert not OpsService.window_eligible(f_far, "WNBA", now, look)
    assert not OpsService.window_eligible(f_past, "WNBA", now, look)


def test_map_completed_to_result_all_shapes():
    rf = results_fetch.map_completed_to_result
    assert rf(101, 98, ["HOME", "AWAY"]) == "HOME"
    assert rf(98, 101, ["HOME", "AWAY"]) == "AWAY"
    assert rf(99, 99, ["HOME", "AWAY"]) is None      # completed tie: no settle
    assert rf(2, 1, ["HOME", "DRAW", "AWAY"]) == "HOME"
    assert rf(1, 1, ["HOME", "DRAW", "AWAY"]) == "DRAW"
    assert rf(0, 2, ["HOME", "DRAW", "AWAY"]) == "AWAY"


# ------------------------------------------------------------------- settle --

def test_settle_final_score_settles_once_idempotent(env, monkeypatch):
    seed_open_bet(env)
    monkeypatch.setattr(results_fetch, "_espn_get",
                        lambda league, date: (
                            espn_payload("401918297T", completed=True), b"{}",
                            200))
    svc = make_svc(env)
    out = svc.settle_pass()
    assert out["settled"] == 1
    rows = ledger_rows(env)
    stl = [r for r in rows if r["type"] == "SETTLEMENT"]
    assert len(stl) == 1
    assert stl[0]["outcome_for_leg"] == "WIN"
    assert stl[0]["pnl_cents"] == int(round(500 * (1.79 - 1.0)))   # +395
    assert "espn_scoreboard" in stl[0]["source_ref"] and \
        "401918297T" in stl[0]["source_ref"]
    # crash/restart: a FRESH supervisor instance re-derives from disk and
    # must NOT settle twice (append-only duplicate refusal law).
    svc2 = make_svc(env)
    out2 = svc2.settle_pass()
    assert out2["settled"] == 0 and out2["attempted"] == 0
    assert len([r for r in ledger_rows(env)
                if r["type"] == "SETTLEMENT"]) == 1


def test_settle_nonfinal_score_keeps_open(env, monkeypatch):
    seed_open_bet(env)
    monkeypatch.setattr(results_fetch, "_espn_get",
                        lambda league, date: (
                            espn_payload("401918297T", completed=False,
                                         state="in", detail="2nd Quarter"),
                            b"{}", 200))
    svc = make_svc(env, settle_grace_hours=3)
    out = svc.settle_pass()
    assert out["settled"] == 0 and out["kept_open"] >= 1
    assert not [r for r in ledger_rows(env)
                if r["type"] == "SETTLEMENT"]
    kinds = [i["kind"] for i in incidents(env)]
    assert "SETTLE_KEEP_OPEN" in kinds
    assert any("not FINAL" in i["detail"] for i in incidents(env))


def test_settle_identity_mismatch_fail_closed(env, monkeypatch):
    seed_open_bet(env)
    monkeypatch.setattr(results_fetch, "_espn_get",
                        lambda league, date: (
                            espn_payload("401918297T", completed=True,
                                         home_abbr="ZZ", away_abbr="YY"),
                            b"{}", 200))
    svc = make_svc(env)
    out = svc.settle_pass()
    assert out["settled"] == 0
    assert any("identity mismatch" in i["detail"] for i in incidents(env))
    assert not [r for r in ledger_rows(env) if r["type"] == "SETTLEMENT"]


def test_settle_missing_event_keeps_open(env, monkeypatch):
    seed_open_bet(env)
    monkeypatch.setattr(results_fetch, "_espn_get",
                        lambda league, date: ({"events": []}, b"{}", 200))
    svc = make_svc(env)
    out = svc.settle_pass()
    assert out["settled"] == 0
    assert any("not found on source boards" in i["detail"]
               for i in incidents(env))


def test_settle_soccer_quota_error_fail_closed(env, monkeypatch):
    """A quota/key law breach during the /scores capture must journal and keep
    the bet OPEN — never bypass the frozen quota law."""
    seed_open_bet(env, league="SOCCER", match_id="soc-test",
                  home="ENG", away="CRO",
                  kickoff="2026-10-01T18:00:00Z",
                  competition="soccer_uefa_nations_league",
                  odds={"HOME": 1.7, "DRAW": 3.6, "AWAY": 5.0})
    stage = execute.soccer_stage_law("soccer_uefa_nations_league",
                                     "2026-10-01")
    assert stage["bet_eligible"], "fixture must be stage-eligible"
    core = execute.load_pinned_core(roots={})
    oc = core.odds_client                # pinned module, loaded via the pin

    class _Quota:
        def precheck(self, cost):
            raise oc.QuotaSkip("quota guard: today 4/4 (test)")

        def record(self, **kw):
            raise AssertionError("record must not run after precheck refusal")

    class _Client:
        def get_scores(self, key, days_from=3):
            self.quota.precheck(1)
            raise AssertionError("unreachable")

        fingerprint = "0" * 12
        quota = _Quota()

    monkeypatch.setattr(ops_service.execute, "_odds_for",
                        lambda args: (oc, _Quota(), _Client()))
    monkeypatch.setattr(results_fetch, "make_scores_client",
                        lambda odds_mod, quota, key_path=None: _Client())
    svc = make_svc(env)
    out = svc.settle_pass()
    assert out["settled"] == 0
    assert any(i["kind"] == "SETTLE_FETCH_ERROR" and "QuotaSkip" in i["detail"]
               for i in incidents(env))
    assert not [r for r in ledger_rows(env) if r["type"] == "SETTLEMENT"]


def test_settle_tampered_ledger_fail_closed(env):
    seed_open_bet(env)
    p = sandbox_ledger_path(env)
    p.write_text(p.read_text().replace('"stake_cents":500',
                                       '"stake_cents":501', 1))
    svc = make_svc(env)
    out = svc.settle_pass()
    assert out == {"attempted": 0, "settled": 0, "kept_open": 0}
    assert any(i["kind"] == "SETTLE_SKIP" and "BLOCKED_TAMPER" in i["detail"]
               for i in incidents(env))


# ---------------------------------------------------------------- concurrent --

def test_concurrent_supervisor_single_instance(env):
    svc = make_svc(env)
    lock_path = svc.ops / "service.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fh = open(lock_path, "a+")
    fcntl.flock(fh, fcntl.LOCK_EX)          # a first supervisor holds it
    with pytest.raises(SystemExit) as ei:
        make_svc(env).run_forever()
    assert ei.value.code == 3
    fcntl.flock(fh, fcntl.LOCK_UN)


def test_restart_resumes_and_journals_cleanly(env, monkeypatch):
    monkeypatch.setattr(results_fetch, "_espn_get",
                        lambda league, date: (
                            espn_payload("401918297T", completed=True), b"{}",
                            200))
    make_svc(env).run_forever()             # single tick via once=True
    rows_after_first = len(ledger_rows(env))
    svc2 = make_svc(env)                    # simulated post-crash relaunch
    svc2.run_forever()
    assert len(ledger_rows(env)) == rows_after_first   # no duplicate rows
    starts = [i for i in incidents(env) if i["kind"] == "SERVICE_START"]
    assert len(starts) == 2                 # both launches journaled


# ------------------------------------------------------------------- cadence --

def _fake_plan_report(league, date, fixtures):
    return {"date": date, "leagues": {league: {
        "fixtures": fixtures, "count": len(fixtures)}}}


def _fixture(mid, anchor_dt, *, forecast=False, quote=False, decided=False):
    return {"match_id": mid, "home": "AAA", "away": "BBB",
            "competition": "SEMI", "source": "test",
            "tip_utc": iso_z(anchor_dt + timedelta(hours=6, minutes=10)),
            "et_local_date": "2026-10-20",
            "anchor_utc": iso_z(anchor_dt), "anchor_open_now": True,
            "teams_known": True, "stage_bet_eligible": True,
            "forecast_present": forecast, "quote_present": quote,
            "already_decided": decided, "eligible_now": True}


def test_cadence_window_invokes_chain_respects_lookahead(env, monkeypatch):
    now = utcnow()
    inside = _fixture("in-window", now + timedelta(hours=2))
    outside = _fixture("far-window", now + timedelta(hours=72))
    called = []

    def fake_plan(ns):
        called.append(("plan", ns.league, ns.date))
        if ns.league == "WNBA" and ns.date == now.date().isoformat():
            return _fake_plan_report("WNBA", ns.date, [inside, outside])
        return _fake_plan_report(ns.league, ns.date, [])

    for name in ("forecast", "quote", "decide"):
        def fake_cmd(ns, _name=name):
            called.append((_name, ns.league, ns.date))
            return {"league": ns.league, "date": ns.date}
        monkeypatch.setattr(ops_service.execute, f"cmd_{name}", fake_cmd)
    monkeypatch.setattr(ops_service.execute, "cmd_plan", fake_plan)

    svc = make_svc(env, lookahead_hours={"WNBA": 24, "NBA": 24, "SOCCER": 48})
    svc.cadence_pass()
    assert ("forecast", "WNBA", now.date().isoformat()) in called
    assert ("quote", "WNBA", now.date().isoformat()) in called
    assert ("decide", "WNBA", now.date().isoformat()) in called
    kinds = [i["kind"] for i in incidents(env)]
    assert {"CADENCE_FORECAST_OK", "CADENCE_QUOTE_OK",
            "CADENCE_DECIDE_OK"} <= set(kinds)


def test_cadence_anchor_passed_stops_chain(env, monkeypatch):
    now = utcnow()
    fx = _fixture("late", now + timedelta(hours=1))
    called = []

    def fake_plan(ns):
        if ns.league != "WNBA" or ns.date != now.date().isoformat():
            return _fake_plan_report(ns.league, ns.date, [])
        return _fake_plan_report("WNBA", ns.date, [fx])

    def fake_forecast(ns):
        called.append("forecast")
        raise BlockError("BLOCKED_ANCHOR_PASSED",
                         "anchor deadline passed (test)",
                         execute.EXIT_BLOCKED_ANCHOR)

    def fake_quote(ns):
        called.append("quote")
        return {}

    def fake_decide(ns):
        called.append("decide")
        return {}

    monkeypatch.setattr(ops_service.execute, "cmd_plan", fake_plan)
    monkeypatch.setattr(ops_service.execute, "cmd_forecast", fake_forecast)
    monkeypatch.setattr(ops_service.execute, "cmd_quote", fake_quote)
    monkeypatch.setattr(ops_service.execute, "cmd_decide", fake_decide)
    svc = make_svc(env)
    svc.cadence_pass()
    assert called == ["forecast"]           # chain stops: NOT_RUN evidence
    assert any(i["kind"] == "CADENCE_FORECAST_BLOCKED" and
               "BLOCKED_ANCHOR_PASSED" in i["detail"] for i in incidents(env))


# ----------------------------------------------------------------- dashboard --

def test_dashboard_state_tamper_withholds_financials(env):
    seed_open_bet(env)
    svc = make_svc(env)
    ok_state = svc.state_fn()
    assert ok_state["chain"]["ok"] is True
    assert ok_state["mode"] == "SANDBOX"
    assert ok_state["wallet"]["open_exposure_cents"] == 500
    p = sandbox_ledger_path(env)
    p.write_text(p.read_text().replace("TEST_SYNTHETIC", "TAMPERED_X", 1))
    tampered = svc.state_fn()
    assert tampered["chain"]["ok"] is False
    assert tampered["wallet"] == {} and tampered["matches"] == []


def test_dashboard_state_stale_and_missing_heartbeat(env):
    seed_open_bet(env)
    svc = make_svc(env)
    no_hb = svc.state_fn()
    assert no_hb["service"].get("heartbeat_age_s") is None
    old = (utcnow() - timedelta(hours=2)).strftime(NOW_FMT)
    (svc.state_dir / "heartbeat.json").write_text(
        json.dumps({"ts_utc": old, "pid": 1}))
    stale = svc.state_fn()
    assert stale["service"]["heartbeat_age_s"] > 7000


def test_enrich_matches_groups_and_open_flag():
    rows = [
        {"type": "GENESIS", "at_utc": "t0", "wallet_cents": 100000,
         "sandbox": True, "plan_sha256": "x", "row_sha256": "g1"},
        {"type": "FORECAST", "league": "WNBA", "match_id": "m1",
         "home": "AAA", "away": "BBB", "competition": "SEMI",
         "kickoff_utc": "k", "p": {"HOME": 0.6, "AWAY": 0.4},
         "model_id": "B1_WNBA", "mode": "ENGINE", "recorded_at_utc": "r",
         "source_ref": "s", "row_sha256": "f1"},
        {"type": "DECISION", "league": "WNBA", "match_id": "m1",
         "status": "BET_PAPER", "stake_cents": 500, "chosen_leg": "HOME",
         "row_sha256": "d1"},
        {"type": "SETTLEMENT", "league": "WNBA", "match_id": "m1",
         "decision_row_sha256": "d1", "result": "HOME",
         "outcome_for_leg": "WIN", "pnl_cents": 395,
         "settled_at_utc": "s1", "source_ref": "src", "row_sha256": "s2"},
    ]
    out = live_dashboard.enrich_matches(rows)
    assert len(out) == 1
    m = out[0]
    assert m["forecast"]["p"]["HOME"] == 0.6
    assert m["decision"]["status"] == "BET_PAPER"
    assert m["settlement"]["pnl_cents"] == 395
    assert m["is_open"] is False


# --------------------------------------------------------------- live server --

def test_live_server_binds_localhost_and_serves(env):
    seed_open_bet(env)
    svc = make_svc(env)
    payload = {"mode": "SANDBOX", "chain": {"ok": True, "errors": []},
               "generated_at_utc": "2026-10-08T00:00:00Z"}
    srv = live_dashboard.serve(lambda: payload, port=0)
    port = srv.server_address[1]
    assert srv.server_address[0] == "127.0.0.1"      # never a public bind
    try:
        with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/", timeout=5) as r:
            html = r.read().decode()
        assert "paper desk" in html and "SANDBOX" in html
        assert "AUTO_REFRESH_SECONDS=8" in html       # 8s <= 10s refresh law
        with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/api/state", timeout=5) as r:
            state = json.loads(r.read())
        assert state == payload
        with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/healthz", timeout=5) as r:
            assert json.loads(r.read()) == {"ok": True}
    finally:
        srv.shutdown()
