"""Adversarial battery for SPORTS-PAPERTRADE-EXEC-V1 (offline, deterministic,
sandbox-only). REAL fixture identity (pinned WNBA schedule snapshot + NBA ESPN
payloads); probabilities and odds are SYNTHETIC and labeled; outcomes are
masked (no results used except the explicit rehearsal results file for the
settlement law). Nothing here types a GO; the real gate refuses (covered)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from research.papertrade_exec import (  # noqa: E402
    EXIT_BLOCKED_ANCHOR, EXIT_BLOCKED_KEY, EXIT_BLOCKED_NO_GO, EXIT_BLOCKED_TAMPER,
    EXIT_HEAD_DRIFT, EXIT_OK, EXIT_PIN_DRIFT, GO_PHRASE, BlockError,
    execute, adapters as A)
from research.papertrade_exec.execute import main as cli  # noqa: E402

NOW = "2026-10-06T00:00:00Z"
WNBA_DAY = "2026-10-09"        # SF Game 3: ATL @ NY  2026-10-09T23:30:00Z (real tip)
NBA_DAY = "2026-10-23"         # current frozen upcoming slate in live corpus
SOC_DAY = "2026-10-12"         # synthetic rehearsal fixtures

WNBA_SCHEDULE = Path(os.path.expanduser(
    "~/.my-quantitative-data/wnba-2026-remainder-v1/refresh_20261007/"
    "wnba_schedule_2026.csv"))
NBA_PAYLOADS = Path(os.path.expanduser(
    "~/.my-quantitative-data/nba-winprob-prospective-prep-v1/"
    "espn_schedule_2026_27"))
NBA_HARNESS = Path("/Users/hoangminhlong/my-quantitative/.worktrees/"
                   "nba-winprob-ng-scored-v1/integration/research/control/"
                   "NBA-WINPROB-NG-SCORED-V1/harness")

CORE_PKG = Path("/Users/hoangminhlong/my-quantitative/.worktrees/"
                "sports-papertrade-v1/integration/research/papertrade")
WNBA_ROOT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/"
                 "wnba-2026-remainder-v1/integration")
SOCCER_ROOT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/"
                   "soccer-intl-winprob-prospective-prep-v1/integration")


# ------------------------------------------------------------------- helpers --

@pytest.fixture()
def env(tmp_path, monkeypatch):
    """Pristine sandbox env: data root, sandbox control dir + GO-consumed
    registry copy (the ONLY fabricated GO in the battery — sandbox copies
    only; the real control dir is never touched)."""
    # Old synthetic quote generation predates source IDs. Supply explicit
    # fixture IDs only inside this sandbox fixture; production emitters and
    # the W1.4 predicate are exercised unchanged.
    from tests.papertrade_exec.quote_identity_fixtures import identity_fields
    ledger_class = _core().ledger.PaperLedger
    original_append = ledger_class.append
    def append_with_test_identity(self, row, *args, **kwargs):
        if row.get("type") == "MARKET_QUOTE" and row.get("mode") == "SYNTHETIC":
            row = {**row, **identity_fields(row["match_id"])}
        return original_append(self, row, *args, **kwargs)
    monkeypatch.setattr(ledger_class, "append", append_with_test_identity)
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
        else next(c for c in cycles if c.get("cycle_id") == "SPORTS-PAPERTRADE-EXEC-V1")
    row["phase"] = "ACTIVE (EXEC_GO_CONSUMED_VIA_SPORTS-PAPERTRADE-EXEC-V1 [SANDBOX TEST COPY])"
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


def ledger_rows(env_):
    p = env_["data"] / "sandbox" / "sandbox_ledger.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def rows_of(env_, type_, status=None):
    return [r for r in ledger_rows(env_)
            if r.get("type") == type_ and (status is None or r.get("status") == status)]


# ---------------------------------------------------------------- success path --

def test_wnba_census_15_games_and_pinned_anchors(env):
    census = A.wnba_census(WNBA_SCHEDULE)
    assert len(census) == 15, "FREEZE_PACKET §5 census: exactly 15 remaining games"
    by_id = {g["game_id"]: g for g in census}
    assert by_id["401918297"]["per_game_anchor_utc"] == "2026-10-07T17:20:00Z"
    assert by_id["401918298"]["per_game_anchor_utc"] == "2026-10-07T19:20:00Z"
    assert by_id["401918299"]["tip_utc"] == "2026-10-09T23:30:00Z"


def test_wnba_engine_entry_wired_contract(env):
    """Lane B's landed entry (wnba26_predict, contract-compatible with the
    dispatch's predict_matches shape) replays B1-WNBA over completed 2026
    rows and predicts the day's remaining fixtures. PURE: nothing is stored;
    this proves the WIRED_ENGINE_READY claim without creating rows."""
    predict_path = A.wnba_engine_available(WNBA_ROOT)
    assert predict_path is not None, "Lane B predict entry absent"
    completed = A.wnba_completed_rows(WNBA_SCHEDULE)
    upcoming = A.wnba_raw_upcoming(WNBA_SCHEDULE, WNBA_DAY)
    assert len(upcoming) == 1 and upcoming[0]["id"] == "401918299"
    res = A.wnba_engine_predict(predict_path, completed, upcoming)
    assert {r["match_id"] for r in res} == {"401918299"}
    r = res[0]
    assert 0.0 < r["p_home"] < 1.0 and abs(r["p_home"] + r["p_away"] - 1.0) < 1e-9
    assert len(r["state_digest"]) == 64
    res2 = A.wnba_engine_predict(predict_path, completed, upcoming)
    assert res2[0]["p_home"] == r["p_home"]
    assert res2[0]["state_digest"] == r["state_digest"]
    # the wiring probe (what the rehearsal report quotes) says READY
    wiring = execute.probe_engine("WNBA", execute.PINNED_ROOTS)
    assert wiring["entry_status"] == "WIRED_ENGINE_READY", wiring
    wiring_s = execute.probe_engine("SOCCER", execute.PINNED_ROOTS)
    assert wiring_s["entry_status"] == "WIRED_ENGINE_READY", wiring_s
    # Lane C engine contract proof (in-memory only, nothing stored)
    replay_path = A.soccer_engine_available(SOCCER_ROOT)
    res = A.soccer_engine_replay(
        replay_path,
        [A.Fixture("SOCCER", "XWALK-PROBE-1", "USA", "Czechia",
                   "2026-10-12T18:00:00Z", "crosswalk-probe", "2026-10-12", "syn")],
        Path(os.path.expanduser("~/.my-quantitative-data/"
                                "soccer-intl-winprob-prospective-prep-v1/"
                                "corpus/results.csv")),
        "2026-10-12")
    r = res[0]
    assert r["match_id"] == "XWALK-PROBE-1"
    assert abs(r["p_home"] + r["p_draw"] + r["p_away"] - 1.0) < 1e-9
    res2 = A.soccer_engine_replay(
        replay_path,
        [A.Fixture("SOCCER", "XWALK-PROBE-1", "USA", "Czechia",
                   "2026-10-12T18:00:00Z", "crosswalk-probe", "2026-10-12", "syn")],
        Path(os.path.expanduser("~/.my-quantitative-data/"
                                "soccer-intl-winprob-prospective-prep-v1/"
                                "corpus/results.csv")),
        "2026-10-12")
    assert res2[0]["p_home"] == r["p_home"]


def test_run_day_chains_three_leagues_sandbox(env, capcli):
    code, out = capcli(env, "run-day", "--date", WNBA_DAY)
    assert code == EXIT_OK, out
    lg = out["leagues"]
    # CAPITAL-V3 §4: WSL is the fourth chain league (config registers
    # sport_keys.WSL); the fixture-free day still exercises its lane. The
    # sandbox WSL quote seam is battery-injected only — unwired it is a
    # per-league BLOCKED_NO_QUOTE_PLUMBING report, never a crashed batch.
    assert set(lg) == {"NBA", "WNBA", "SOCCER", "WSL"}
    assert lg["WSL"]["status"] == "BLOCKED_NO_QUOTE_PLUMBING"
    assert lg["WNBA"]["status"] == "OK" and len(lg["WNBA"]["decide"]["journaled"]) == 1
    assert lg["NBA"]["status"] == "OK" and lg["NBA"]["forecast"].get("fixtures") == 0
    assert lg["SOCCER"]["status"] == "OK" and len(lg["SOCCER"]["decide"]["journaled"]) == 3
    reports = list((env["data"] / "sandbox").parent.rglob("run_day_*.json")) \
        if False else list((env["data"] / "runs").glob("run_day_*.json"))
    assert not reports, "run-day reports go to the sandbox tree, not runs/"
    all_rows = ledger_rows(env)
    assert any(r["type"] == "GENESIS" and r["sandbox"] for r in all_rows)


def test_run_day_refuses_missing_token(env, capcli):
    # world-independent form (the real control dir is post-GO by design): the
    # missing-token refusal on a tmp control dir via the sandbox seam
    reg = json.loads((REPO / "plans" / "CYCLE_REGISTRY.json").read_text())
    cycles = reg.get("cycles", reg)
    if isinstance(cycles, dict):
        row = cycles.get("SPORTS-PAPERTRADE-EXEC-V1")
        if row is not None:
            row["phase"] = "READY_PENDING_ONE_OWNER_GO"
    else:
        for c in cycles:
            if c.get("cycle_id") == "SPORTS-PAPERTRADE-EXEC-V1":
                c["phase"] = "READY_PENDING_ONE_OWNER_GO"
    (env["ctrl"] / "CYCLE_REGISTRY.json").write_text(json.dumps(reg, indent=1))
    (env["ctrl"] / "GO_TOKEN.json").unlink(missing_ok=True)
    code, out = capcli(env, "run-day", "--date", WNBA_DAY)
    assert code == EXIT_BLOCKED_NO_GO and out["blocked"] == "BLOCKED_NO_GO"


def test_forecast_reports_wiring_status(env, capcli):
    code, out = capcli(env, "forecast", "--league", "WNBA", "--date", WNBA_DAY)
    assert code == EXIT_OK
    assert out["wiring"]["entry_status"] == "WIRED_ENGINE_READY"
    assert out["written"] == ["401918299"]
    # rehearsal rows stay synthetic even with the engine wired
    fc = rows_of(env, "FORECAST")[0]
    assert fc["mode"] == "SYNTHETIC"


def test_plan_is_readonly_with_real_tips(env, capcli):
    code, out = capcli(env, "plan", "--date", WNBA_DAY)
    assert code == EXIT_OK
    fx = out["leagues"]["WNBA"]["fixtures"]
    assert len(fx) == 1 and fx[0]["match_id"] == "401918299"
    assert fx[0]["tip_utc"] == "2026-10-09T23:30:00Z"          # REAL tip
    assert fx[0]["anchor_utc"] == "2026-10-09T17:20:00Z"       # T0-6h10m
    # eligibility obeys the PIT law against the REAL clock (the fixture day
    # ages past the anchor as wall time advances; the law, not a constant):
    from datetime import datetime, timezone as _tz
    now_dt = datetime.now(_tz.utc)
    anchor_dt = A.parse_tip(fx[0]["anchor_utc"])
    assert fx[0]["eligible_now"] is bool(now_dt < anchor_dt)
    code, out = capcli(env, "plan", "--date", NBA_DAY)
    nba = out["leagues"]["NBA"]["fixtures"]
    assert len(nba) >= 10                                       # opening slate
    assert all(f["tip_utc"].startswith("2026-10-23T") or
               f["tip_utc"].startswith("2026-10-24T") for f in nba)
    assert not (env["data"] / "sandbox" / "sandbox_ledger.jsonl").exists(), \
        "plan must not create a ledger"


def test_nba_engine_replay_via_scored_harness_synthetic_inputs(env):
    completed = [{"game_id": f"SYN-{i:03d}", "season": 2026, "season_type": 2,
                  "game_date_time": f"2026-0{i%9+1}-15T19:00:00.000Z",
                  "home": f"T{i:02d}H"[:3], "away": f"T{i:02d}A"[:3],
                  "home_score": i % 2, "away_score": (i + 1) % 2}
                 for i in range(1, 41)]
    upcoming = [A.Fixture("NBA", "SYN-UP-1", "T41", "T42",
                          "2026-10-21T23:00:00Z", "regular-season", "2026-10-21",
                          "syn")]
    res = A.nba_engine_replay_synthetic(
        Path("/Users/hoangminhlong/my-quantitative/.worktrees/"
             "nba-winprob-ng-scored-v1/integration/research/control/"
             "NBA-WINPROB-NG-SCORED-V1/harness"), completed, upcoming)
    assert len(res) == 1
    p = res[0]["p_home"]
    assert 0.0 < p < 1.0
    res2 = A.nba_engine_replay_synthetic(
        Path("/Users/hoangminhlong/my-quantitative/.worktrees/"
             "nba-winprob-ng-scored-v1/integration/research/control/"
             "NBA-WINPROB-NG-SCORED-V1/harness"), completed, upcoming)
    assert res2[0]["p_home"] == p, "engine replay must be deterministic"


def test_success_path_end_to_end_sandbox(env, capcli):
    # --- WNBA (real fixture, synthetic p/odds) -------------------------------
    assert capcli(env, "forecast", "--league", "WNBA", "--date", WNBA_DAY)[0] == EXIT_OK
    code, q = capcli(env, "quote", "--league", "WNBA", "--date", WNBA_DAY)
    assert code == EXIT_OK and q["written"] == ["401918299"]
    code, d = capcli(env, "decide", "--league", "WNBA", "--date", WNBA_DAY)
    assert code == EXIT_OK and len(d["journaled"]) == 1
    # --- NBA (real fixtures, synthetic p/odds) -------------------------------
    capcli(env, "forecast", "--league", "NBA", "--date", NBA_DAY)
    capcli(env, "quote", "--league", "NBA", "--date", NBA_DAY)
    code, d = capcli(env, "decide", "--league", "NBA", "--date", NBA_DAY)
    assert code == EXIT_OK and len(d["journaled"]) >= 10
    # --- SOCCER (synthetic fixtures + three-way) ------------------------------
    capcli(env, "forecast", "--league", "SOCCER", "--date", SOC_DAY)
    capcli(env, "quote", "--league", "SOCCER", "--date", SOC_DAY)
    code, d = capcli(env, "decide", "--league", "SOCCER", "--date", SOC_DAY)
    assert code == EXIT_OK and len(d["journaled"]) == 3

    fcs, qts, decs = rows_of(env, "FORECAST"), rows_of(env, "MARKET_QUOTE"), \
        rows_of(env, "DECISION")
    expected = 1 + len(A.load_nba_fixtures(NBA_PAYLOADS, NBA_DAY)) + 3
    assert len(fcs) == expected and len(qts) == len(fcs) and len(decs) == len(fcs)
    # zero real probabilities: every FORECAST row is labeled synthetic
    assert all(r["mode"] == "SYNTHETIC"
               and r["model_version_sha"] == "SYNTHETIC_ADAPTER_NOT_ENGINE"
               and "SYNTHETIC" in r["source_ref"] for r in fcs)
    assert all(r["mode"] == "SYNTHETIC" for r in qts)
    bets = rows_of(env, "DECISION", "BET_PAPER")
    noedge = rows_of(env, "DECISION", "NO_EDGE")
    assert bets and noedge, "deterministic book must exercise both paths"
    for b in bets:
        # CAPITAL-V3 stake law (owner GO consumed 2026-10-10T12:43:51Z):
        # stake = 1% of equity cent-rounded half-up; the fixed 500c v2 law
        # is dead (the sandbox genesis 100000c -> 1000c first stake).
        assert b["stake_law"] == "v3-1pct"
        assert b["stake_cents"] == (b["equity_at_decision_cents"] + 50) // 100
        assert b["ev_net_by_leg"][b["chosen_leg"]] >= 0.05
    assert rows_of(env, "DECISION", "BLOCKED_NO_GO") == []
    gen = ledger_rows(env)[0]
    assert gen["type"] == "GENESIS" and gen["sandbox"] is True


def test_settle_win_and_postpone_refund_then_dashboard_sandbox_banner(env, capcli):
    capcli(env, "forecast", "--league", "NBA", "--date", NBA_DAY)
    capcli(env, "quote", "--league", "NBA", "--date", NBA_DAY)
    capcli(env, "decide", "--league", "NBA", "--date", NBA_DAY)
    bets = rows_of(env, "DECISION", "BET_PAPER")
    assert len(bets) >= 2
    results = {bets[0]["match_id"]: {"result": bets[0]["chosen_leg"],
                                     "source_ref": "REHEARSAL_RESULT_FILE"},
               bets[1]["match_id"]: {"result": "POSTPONED_NO_RESCHEDULE",
                                     "source_ref": "REHEARSAL_POSTPONE_NOTICE"}}
    res_path = env["data"] / "results.json"
    res_path.write_text(json.dumps(results))
    code, out = capcli(env, "settle", "--league", "NBA", "--date", NBA_DAY,
                       "--results", str(res_path))
    assert code == EXIT_OK
    by_mid = {s["match_id"]: s for s in out["settled"]}
    assert by_mid[bets[0]["match_id"]]["outcome_for_leg"] in ("WIN", "LOSE")
    assert by_mid[bets[1]["match_id"]]["outcome_for_leg"] == "REFUND"
    assert by_mid[bets[1]["match_id"]]["pnl_cents"] == 0
    settled = rows_of(env, "SETTLEMENT")
    assert len(settled) == 2
    # refund released open exposure
    from research.papertrade_exec import load_pinned_package
    core = load_pinned_package("spt_core", "paper_core")
    led = core.ledger.PaperLedger(env["data"] / "sandbox" / "sandbox_ledger.jsonl").load()
    assert led.verify_chain()[0]
    # dashboard with SANDBOX banner
    outdir = env["data"] / "dash"
    code, out = capcli(env, "dashboard", "--out", str(outdir))
    assert code == EXIT_OK and out["sandbox"] is True
    html = (outdir / "index.html").read_text()
    assert "SANDBOX LEDGER" in html and "TEST ARTIFACT" in html
    summary = json.loads((outdir / "summary.json").read_text())
    assert summary["sandbox"] is True and summary["chain_ok"] is True


def test_idempotent_rerun_no_duplicate_rows(env, capcli):
    for lg, day in (("WNBA", WNBA_DAY), ("SOCCER", SOC_DAY)):
        capcli(env, "forecast", "--league", lg, "--date", day)
        capcli(env, "quote", "--league", lg, "--date", day)
        capcli(env, "decide", "--league", lg, "--date", day)
    n1 = len(ledger_rows(env))
    f1 = len(rows_of(env, "FORECAST")); d1 = len(rows_of(env, "DECISION"))
    for lg, day in (("WNBA", WNBA_DAY), ("SOCCER", SOC_DAY)):
        code, out = capcli(env, "forecast", "--league", lg, "--date", day)
        assert out.get("skipped_existing"), "second forecast run must skip"
        capcli(env, "quote", "--league", lg, "--date", day)
        code, out = capcli(env, "decide", "--league", lg, "--date", day)
        assert out["skipped"], "second decide run must skip decided matches"
    n2 = len(ledger_rows(env))
    assert n1 == n2 and len(rows_of(env, "FORECAST")) == f1 \
        and len(rows_of(env, "DECISION")) == d1


# ------------------------------------------------------------------- refusals --

def test_refuse_forecast_missing_go_token(env, capcli):
    (env["ctrl"] / "GO_TOKEN.json").unlink()
    code, out = capcli(env, "forecast", "--league", "WNBA", "--date", WNBA_DAY)
    assert code == EXIT_BLOCKED_NO_GO and out["blocked"] == "BLOCKED_NO_GO"
    assert ledger_rows(env) == []


def test_refuse_wrong_go_phrase(env, capcli):
    (env["ctrl"] / "GO_TOKEN.json").write_text(json.dumps({
        "go_phrase_typed_by_owner": "GO WNBA WINPROB PROSPECTIVE V1 PREDICTIONS",
        "typed_at_utc": "2026-10-07T00:00:00Z", "transcribed_by": "x",
        "registry_consumption_note": "retired phrase must be accepted nowhere"}))
    code, out = capcli(env, "forecast", "--league", "WNBA", "--date", WNBA_DAY)
    assert code == EXIT_BLOCKED_NO_GO and "verbatim" in out["detail"]
    assert ledger_rows(env) == []


def test_refuse_registry_not_consumed(env, capcli):
    # tmp registry WITHOUT GO_CONSUMED (world-independent: the real one may be
    # GO_CONSUMED post-GO; the law under test is token-without-consumption refusal)
    reg = json.loads((REPO / "plans" / "CYCLE_REGISTRY.json").read_text())
    cycles = reg.get("cycles", reg)
    if isinstance(cycles, dict):
        row = cycles.get("SPORTS-PAPERTRADE-EXEC-V1")
        if row is not None:
            row["phase"] = "READY_PENDING_ONE_OWNER_GO"
    else:
        for c in cycles:
            if c.get("cycle_id") == "SPORTS-PAPERTRADE-EXEC-V1":
                c["phase"] = "READY_PENDING_ONE_OWNER_GO"
    (env["ctrl"] / "CYCLE_REGISTRY.json").write_text(json.dumps(reg, indent=1))
    code, out = capcli(env, "forecast", "--league", "WNBA", "--date", WNBA_DAY)
    assert code == EXIT_BLOCKED_NO_GO and "GO_CONSUMED" in out["detail"]


def test_refuse_gate_missing_token(env, capcli):
    # world-independent form (post-GO the real control dir HAS the token by
    # design): the law under test is the missing-token refusal on a tmp control
    # dir + a registry that lacks GO_CONSUMED
    reg = json.loads((REPO / "plans" / "CYCLE_REGISTRY.json").read_text())
    cycles = reg.get("cycles", reg)
    if isinstance(cycles, dict):
        row = cycles.get("SPORTS-PAPERTRADE-EXEC-V1")
        if row is not None:
            row["phase"] = "READY_PENDING_ONE_OWNER_GO"
    else:
        for c in cycles:
            if c.get("cycle_id") == "SPORTS-PAPERTRADE-EXEC-V1":
                c["phase"] = "READY_PENDING_ONE_OWNER_GO"
    (env["ctrl"] / "CYCLE_REGISTRY.json").write_text(json.dumps(reg, indent=1))
    (env["ctrl"] / "GO_TOKEN.json").unlink(missing_ok=True)
    code, out = capcli(env, "forecast", "--league", "WNBA", "--date", WNBA_DAY)
    assert code == EXIT_BLOCKED_NO_GO and "absent" in out["detail"]
    assert not (env["data"] / "ledger").exists(), "no ledger without gate"


def test_refuse_head_drift(env, capcli):
    code, out = capcli(env, "verify-pins", "--expect-head",
                       "0" * 40, sandbox=False)
    assert code == EXIT_HEAD_DRIFT and out["blocked"] == "HEAD_DRIFT"
    own = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                         capture_output=True, text=True).stdout.strip()
    code, out = capcli(env, "verify-pins", "--expect-head", own, sandbox=False)
    assert code == EXIT_OK and out["self_head"] == own


def test_refuse_pin_drift(env, capcli, tmp_path):
    tampered = tmp_path / "papertrade_tampered"
    shutil.copytree(CORE_PKG, tampered)
    p = tampered / "risk.py"
    p.write_text(p.read_text() + "\n# tampered byte\n")
    code, out = capcli(env, "forecast", "--league", "WNBA", "--date", WNBA_DAY,
                       "--paper_core_root", str(tampered))
    assert code == EXIT_PIN_DRIFT and out["blocked"] == "BLOCKED_PIN_DRIFT"
    assert "risk.py" in out["detail"]
    assert ledger_rows(env) == [], "nothing written on pin drift"


def test_verify_pins_reports_optional_entries(env, capcli):
    code, out = capcli(env, "verify-pins", sandbox=False)
    assert code == EXIT_OK
    assert out["files"]["wnba26/predict.py"]["status"] in (
        "OK", "ABSENT_OPTIONAL", "PRESENT_UNPINNED_OPTIONAL")
    assert out["files"]["soccer/replay.py"]["status"] in (
        "OK", "ABSENT_OPTIONAL", "PRESENT_UNPINNED_OPTIONAL")
    assert out["data"]["wnba_schedule_2026_csv"]["status"] == "OK"
    assert out["data"]["nba_espn_schedule_2026_27"]["status"] == "OK"


def test_refuse_forecast_at_and_after_anchor(env, capcli):
    # WNBA 2026-10-09 batch anchor = 2026-10-09T17:20:00Z (exclusive deadline)
    for now in ("2026-10-09T17:20:00Z", "2026-10-09T18:00:00Z"):
        code, out = capcli(env, "forecast", "--league", "WNBA",
                           "--date", WNBA_DAY, now=now)
        assert code == EXIT_BLOCKED_ANCHOR
        assert out["blocked"] == "BLOCKED_ANCHOR_PASSED"
    assert not any(r["type"] == "FORECAST" for r in ledger_rows(env))


def test_odds_updated_after_capture_stale_price(env, capcli):
    capcli(env, "forecast", "--league", "WNBA", "--date", WNBA_DAY)
    core = _core()
    led = core.ledger.PaperLedger(env["data"] / "sandbox" / "sandbox_ledger.jsonl")
    led.load()
    p = A.synthetic_two_way_p("401918299")
    led.append({"type": "MARKET_QUOTE", "league": "WNBA", "match_id": "401918299",
                "home": "NY", "away": "ATL", "kickoff_utc": "2026-10-09T23:30:00Z",
                "bookmaker": "SYNTHETIC_BOOK (rehearsal)", "market": "h2h",
                "odds": A.synthetic_odds("401918299", p),
                "fetch_ts_utc": NOW, "source_last_update_utc": "2026-10-06T05:00:00Z",
                "commence_time_utc": "2026-10-09T23:30:00Z",
                "payload_sha256": "0" * 64, "key_fingerprint": "sandbox-synthetic-00",
                "mode": "SYNTHETIC"})
    code, out = capcli(env, "decide", "--league", "WNBA", "--date", WNBA_DAY)
    assert code == EXIT_OK
    dec = rows_of(env, "DECISION")[0]
    assert dec["status"] == "STALE_PRICE", dec["reason"]


def _core():
    from research.papertrade_exec import load_pinned_package
    return load_pinned_package("spt_core", "paper_core")


def test_decide_missing_odds_no_quote(env, capcli):
    capcli(env, "forecast", "--league", "WNBA", "--date", WNBA_DAY)
    code, out = capcli(env, "decide", "--league", "WNBA", "--date", WNBA_DAY)
    assert code == EXIT_OK
    dec = rows_of(env, "DECISION")[0]
    assert dec["status"] == "NO_QUOTE"


def test_soccer_missing_draw_leg_refused(env, capcli):
    # B1R law: inject the lawful control+twin pair per fixture so each match
    # reaches the quote evaluation (a B1-only match stops at
    # NOT_RUN_NO_B1R_FORECAST before the quote law applies — the dedicated
    # battery lives in test_b1r_fail_closed.py).
    capcli(env, "forecast", "--league", "SOCCER", "--date", SOC_DAY)
    reg = str(env["data"] / "sandbox" / "control" / "CYCLE_REGISTRY.json")
    execute.b1r_switch_ts_verified(reg)
    led = _core().ledger.PaperLedger(env["data"] / "sandbox" / "sandbox_ledger.jsonl")
    led.load()
    for f in execute.synthetic_soccer_fixtures(SOC_DAY):
        p = A.synthetic_three_way_p(f.match_id)
        led.append({"type": "FORECAST", "league": "SOCCER",
                    "match_id": f.match_id, "competition": f.competition,
                    "home": f.home, "away": f.away,
                    "kickoff_utc": f.kickoff_utc, "recorded_at_utc": NOW,
                    "anchor_utc": f.kickoff_utc,   # battery shortcut: 1:1 rows
                    "model_version_sha": "soccer_b1_replay",
                    "p": p, "source_ref": "battery B1 control", "mode": "ENGINE",
                    "fixture_source": f.source_ref})
    led2 = _core().ledger.PaperLedger(env["data"] / "sandbox" / "sandbox_ledger.jsonl")
    led2.load()
    emitted = execute.emit_b1r_forecasts(
        led2, execute.synthetic_soccer_fixtures(SOC_DAY), NOW)
    assert len(emitted) == 3, emitted
    led3 = _core().ledger.PaperLedger(env["data"] / "sandbox" / "sandbox_ledger.jsonl")
    led3.load()
    for i, f in enumerate(execute.synthetic_soccer_fixtures(SOC_DAY)):
        p = A.synthetic_three_way_p(f.match_id)
        odds = {k: v for k, v in A.synthetic_odds(f.match_id, p).items()
                if k != "DRAW"}
        led3.append({"type": "MARKET_QUOTE", "league": "SOCCER",
                     "match_id": f.match_id, "home": f.home, "away": f.away,
                     "kickoff_utc": f.kickoff_utc,
                     "bookmaker": "SYNTHETIC_BOOK (rehearsal)", "market": "h2h",
                     "odds": odds, "fetch_ts_utc": NOW,
                     "source_last_update_utc": NOW,
                     "commence_time_utc": f.kickoff_utc,
                     # W1.4: distinct snapshots — one payload sha must never
                     # price two fixtures (the collision guard is law now)
                     "payload_sha256": ("1" * 63 + str(i)),
                     "key_fingerprint": "sandbox-synthetic-00", "mode": "SYNTHETIC"})
    code, out = capcli(env, "decide", "--league", "SOCCER", "--date", SOC_DAY)
    assert code == EXIT_OK
    decs = rows_of(env, "DECISION")
    assert len(decs) == 3 and all(d["status"] == "NO_QUOTE" for d in decs)
    assert all("missing required legs" in d["reason"] for d in decs)


def test_duplicate_match_second_decision_blocked(env):
    """Core law: a second DECISION draft for a decided match is
    BLOCKED_DUPLICATE_SELECTION (the runner's decide skips such matches, so
    the duplicate never even reaches the ledger — covered by the idempotence
    test; here the law itself)."""
    core = _core()
    led = core.ledger.PaperLedger(
        Path(env["data"]) / "sandbox" / "sandbox_ledger.jsonl")
    led.genesis(plan_sha256="dup-test", created_at_utc="2026-10-01T00:00:00Z",
                sandbox=True)
    risk = core.risk
    fc = {"recorded_at_utc": NOW, "p": {"HOME": 0.6, "AWAY": 0.4},
          "model_version_sha": "syn", "source_ref": "syn"}
    qt = {"bookmaker": "b", "market": "h2h", "odds": {"HOME": 2.2, "AWAY": 1.75},
          "fetch_ts_utc": NOW, "source_last_update_utc": NOW,
          "commence_time_utc": "2026-10-20T23:00:00Z", "payload_sha256": "2" * 64,
          "key_fingerprint": "sandbox-synthetic-00"}
    dec = risk.evaluate_match(led, league="NBA", match_id="DUP-1",
                              competition="SYN", home="H", away="A",
                              kickoff_utc="2026-10-20T23:00:00Z", now_utc=NOW,
                              forecast=fc, quote=qt, crosswalk_ok=True, go_ok=True)
    assert dec["status"] == "BET_PAPER", dec
    led.append_decision(dec, recheck=risk.in_lock_recheck(led, NOW, True))
    dec2 = risk.evaluate_match(led, league="NBA", match_id="DUP-1",
                               competition="SYN", home="H", away="A",
                               kickoff_utc="2026-10-20T23:00:00Z", now_utc=NOW,
                               forecast=fc, quote=qt, crosswalk_ok=True, go_ok=True)
    assert dec2["status"] == "BLOCKED_DUPLICATE_SELECTION"


def test_21st_bet_open_exposure_cap_in_lock(env):
    """Reuse the CORE sandbox builder and top the book up to exactly the
    100.00 USD open cap (17 open after its 3 settlements + 3 fillers = 20
    open bets), then push a 21st BET_PAPER through decide -> in-lock recheck
    journals BLOCKED_OPEN_EXPOSURE (row kept, stake zeroed)."""
    from research.papertrade_exec import load_pinned_package
    core = load_pinned_package("spt_core", "paper_core")
    led_path = core.sandbox.build_sandbox_ledger(
        env["data"] / "sandbox" / "sandbox_ledger.jsonl", scenario="full")
    led = core.ledger.PaperLedger(led_path).load()
    assert led.open_exposure_cents() == 8_500  # 17 open x 500 after settlements
    risk = core.risk
    fillers = [(f"SYN-FILL-{i}", f"2026-10-15T2{i}:00:00Z") for i in range(1, 4)]
    for mid, ko in fillers:
        execute_modify_ledger_add_fc_qt(led, "NBA", mid, ko,
                                        p={"HOME": 0.7, "AWAY": 0.3},
                                        odds={"HOME": 2.2, "AWAY": 1.75})
        fc = next(r for r in led.rows if r["type"] == "FORECAST" and r["match_id"] == mid)
        qt = next(r for r in led.rows if r["type"] == "MARKET_QUOTE" and r["match_id"] == mid)
        dec = risk.evaluate_match(led, league="NBA", match_id=mid,
                                  competition="rehearsal", home="SYN-H", away="SYN-A",
                                  kickoff_utc=ko, now_utc="2026-10-05T00:00:00Z",
                                  forecast=fc, quote=qt, crosswalk_ok=True,
                                  go_ok=True)
        assert dec["status"] == "BET_PAPER"
        led.append_decision(dec, recheck=risk.in_lock_recheck(led, "2026-10-05T00:00:00Z", True))
    assert led.open_exposure_cents() == 10_000, "20 open bets = exactly the cap"
    # the 21st bet: draft passes, in-lock recheck refuses, row journaled
    execute_modify_ledger_add_fc_qt(led, "NBA", "SYN-21ST",
                                    "2026-10-15T23:30:00Z",
                                    p={"HOME": 0.7, "AWAY": 0.3},
                                    odds={"HOME": 2.2, "AWAY": 1.75})
    fc = next(r for r in led.rows if r["type"] == "FORECAST"
              and r["match_id"] == "SYN-21ST")
    qt = next(r for r in led.rows if r["type"] == "MARKET_QUOTE"
              and r["match_id"] == "SYN-21ST")
    dec = risk.evaluate_match(led, league="NBA", match_id="SYN-21ST",
                              competition="rehearsal", home="SYN-H21", away="SYN-A21",
                              kickoff_utc="2026-10-15T23:30:00Z",
                              now_utc="2026-10-05T00:00:00Z",
                              forecast=fc, quote=qt, crosswalk_ok=True, go_ok=True)
    # the cap fires (evaluate pre-check and/or the in-lock recheck — both are
    # the same law; the row is JOURNALED either way, never skipped)
    led.append_decision(dec, recheck=risk.in_lock_recheck(led, "2026-10-05T00:00:00Z", True))
    row = next(r for r in led.rows if r["type"] == "DECISION"
               and r["match_id"] == "SYN-21ST")
    assert row["status"] == "BLOCKED_OPEN_EXPOSURE"
    assert row["stake_cents"] == 0
    assert led.open_exposure_cents() == 10_000   # 21st bet did NOT add exposure
    ok, errs = led.verify_chain()
    assert ok


def execute_modify_ledger_add_fc_qt(led, league, mid, ko, p, odds):
    rec = "2026-10-04T06:00:00Z"
    led.append({"type": "FORECAST", "league": league, "match_id": mid,
                "kickoff_utc": ko, "recorded_at_utc": rec,
                "model_version_sha": "SYNTHETIC_ADAPTER_NOT_ENGINE",
                "p": p, "source_ref": "SYNTHETIC_ADAPTER_REHEARSAL",
                "mode": "SYNTHETIC"})
    led.append({"type": "MARKET_QUOTE", "league": league, "match_id": mid,
                "home": "SYN-H21", "away": "SYN-A21", "kickoff_utc": ko,
                "bookmaker": "SYNTHETIC_BOOK (rehearsal)", "market": "h2h",
                "odds": odds, "fetch_ts_utc": "2026-10-04T06:00:00Z",
                "source_last_update_utc": "2026-10-04T06:00:00Z",
                "commence_time_utc": ko, "payload_sha256": "3" * 64,
                "key_fingerprint": "sandbox-synthetic-00", "mode": "SYNTHETIC"})


def test_quota_exhausted_journals_quota_skip(env):
    core = _core()
    odds_mod = core.odds_client
    led = core.ledger.PaperLedger(
        env["data"] / "sandbox" / "sandbox_ledger.jsonl")
    led.load()
    led.genesis(plan_sha256="quota-test", created_at_utc="2026-10-01T00:00:00Z",
                sandbox=True)
    fx = execute.synthetic_soccer_fixtures(SOC_DAY)
    journaled = execute.journal_quota_skip(
        led, fx, NOW, "quota guard: today 4/4 month 120/120 + cost 1 exceeds "
        "standing caps; journaled QUOTA_SKIP, no call", {})
    assert journaled == [f.match_id for f in fx]
    rows = rows_of(env, "DECISION", "QUOTA_SKIP")
    assert len(rows) == 3 and all("no call" in r["reason"] for r in rows)
    ok, _ = led.verify_chain()
    assert ok


def test_key_missing_and_wrong_mode_blocked(env, capcli, tmp_path):
    missing = tmp_path / "nope_key"
    code, out = capcli(env, "key-check", "--key-path", str(missing), sandbox=False)
    assert code == EXIT_BLOCKED_KEY and out["blocked"] == "BLOCKED_KEY"
    bad = tmp_path / "loose_key"
    bad.write_text("notarealkey\n")
    bad.chmod(0o644)
    code, out = capcli(env, "key-check", "--key-path", str(bad), sandbox=False)
    assert code == EXIT_BLOCKED_KEY and "0600" in out["detail"]
    good = tmp_path / "ok_key"
    good.write_text("sandbox-only-fake-key\n")
    good.chmod(0o600)
    code, out = capcli(env, "key-check", "--key-path", str(good), sandbox=False)
    assert code == EXIT_OK and len(out["key_fingerprint"]) == 12


def test_ledger_tamper_refuses_decide_and_dashboard(env, capcli):
    capcli(env, "forecast", "--league", "WNBA", "--date", WNBA_DAY)
    capcli(env, "quote", "--league", "WNBA", "--date", WNBA_DAY)
    p = env["data"] / "sandbox" / "sandbox_ledger.jsonl"
    lines = p.read_text().splitlines()
    row = json.loads(lines[1])
    row["source_ref"] = "TAMPERED"
    lines[1] = json.dumps(row, sort_keys=True, separators=(",", ":"))
    p.write_text("\n".join(lines) + "\n")
    code, out = capcli(env, "decide", "--league", "WNBA", "--date", WNBA_DAY)
    assert code == EXIT_BLOCKED_TAMPER and out["blocked"] == "BLOCKED_TAMPER"
    code, out = capcli(env, "dashboard")
    assert code == EXIT_BLOCKED_TAMPER


def test_soccer_fixtures_from_events_shape():
    payload = json.dumps([
        {"id": "ev1", "home_team": "Italy", "away_team": "Germany",
         "commence_time": "2026-10-12T18:00:00Z"},
        {"id": "ev2", "home_team": "France", "away_team": "Spain",
         "commence_time": "2026-10-12T20:45:00Z"}]).encode()
    fx = A.soccer_fixtures_from_events(payload, "soccer_uefa_nations_league")
    assert [f.match_id for f in fx] == ["ev1", "ev2"]
    assert fx[0].kickoff_utc == "2026-10-12T18:00:00Z"


def test_dashboard_never_lists_hidden_rows_and_counts_not_run(env, capcli):
    # B1R law (owner 2026-10-10): a B1-only sandbox soccer match journals
    # NOT_RUN_NO_B1R_FORECAST (stake 0, terminal) — the dashboard census
    # must count it like every NOT_RUN family (cause-bucket display for
    # statuses newer than the pinned core follows the NOT_RUN_STAGE_LAW
    # precedent: status census yes, cause strip no).
    capcli(env, "forecast", "--league", "SOCCER", "--date", SOC_DAY)
    code, out = capcli(env, "decide", "--league", "SOCCER", "--date", SOC_DAY)
    outdir = env["data"] / "dash2"
    capcli(env, "dashboard", "--out", str(outdir))
    summary = json.loads((outdir / "summary.json").read_text())
    assert summary["status_counts"].get("NOT_RUN_NO_B1R_FORECAST", 0) == 3
    assert summary["status_counts"].get("NO_QUOTE", 0) is not None
    decs = rows_of(env, "DECISION")
    assert all(d["stake_cents"] == 0 for d in decs)


# ------------------------------------------------- NBA rewire (EXEC-NBA-REWIRE) --

NBA26_ROOT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/"
                  "nba-winprob-prospective-prep-v1/integration")
NBA_WIN_START, NBA_WIN_END = "2026-10-23", "2026-10-24"
NBA_ANCHOR = "2026-10-20T12:50:00Z"   # earliest tip 2026-10-20T19:00Z - 6h10m


def _nba_pins_composite() -> str:
    return json.loads((REPO / "research" / "papertrade_exec" / "pins.json")
                      .read_text())["data"]["nba_espn_schedule_2026_27"][
        "composite_sha256"]


def _copy_payload_subset(dst: Path, days=("20261020", "20261021")) -> Path:
    """Pristine COPY of two frozen per-date payloads + their .meta records
    (a small internally-consistent corpus for loader-law tests)."""
    dst.mkdir(parents=True, exist_ok=True)
    for day in days:
        for suffix in ("json", "meta"):
            shutil.copy2(NBA_PAYLOADS / f"scoreboard_{day}.{suffix}",
                         dst / f"scoreboard_{day}.{suffix}")
    return dst


def _reseal_meta(payload: Path) -> None:
    """Rewrite the sibling .meta sha256 to match the (modified) bytes — the
    corpus stays internally consistent so the TAMPER layer is not what fires;
    the completed-only LAW is what must hold."""
    meta = payload.with_name(payload.stem + ".meta")
    lines = [line for line in meta.read_text().splitlines()
             if not line.startswith("sha256=")]
    meta.write_text("\n".join(lines) + "\nsha256="
                    + hashlib.sha256(payload.read_bytes()).hexdigest() + "\n")


def test_nba_prospective_engine_success_opening_window(env):
    """EXEC-NBA-REWIRE success path: the REAL engine (Lane D loader+predict,
    pinned nba26 bytes, frozen ESPN payloads ONLY — never the scored bind
    corpus) over the opening window. AGE-INDEPENDENT since the W1.3 fix:
    the corpus lawfully ages through the refresh-manifest chain (completed
    games ARE the point of the refresh), so counts/anchor derive from the
    corpus at run time. IN-MEMORY ONLY: nothing is persisted by this test."""
    fx = A.load_nba_fixtures_window(NBA_PAYLOADS, NBA_WIN_START, NBA_WIN_END)
    assert len(fx) >= 1                      # the window keeps >=1 scheduled
    anchor, _ = execute.batch_anchor(fx, "NBA")
    predict_path = A.nba_engine_available(NBA26_ROOT)
    assert predict_path is not None
    wiring = execute.probe_engine("NBA", execute.PINNED_ROOTS)
    assert wiring["entry_status"] == "WIRED_ENGINE_READY", wiring
    res = A.nba_engine_predict(NBA_PAYLOADS, anchor, anchor,
                               expected_composite_sha=_nba_pins_composite(),
                               predict_path=predict_path)
    by = {r["match_id"]: r for r in res}
    window = [by[f.match_id] for f in fx]
    assert len(window) == len(fx)
    lmod, _ = A.nba_engine_modules(predict_path)
    completed = lmod.load_completed(NBA_PAYLOADS, anchor)
    r0_p = 1.0 / (1.0 + 10.0 ** (-100.0 / 400.0))
    for r in window:
        assert abs(r["p_home"] + r["p_away"] - 1.0) < 1e-9
        assert len(r["state_digest"]) == 64 and r["model_id"] == "B1_STAR"
        if not completed:
            # zero FINAL games -> every rating at R0=1500 (the lawfully
            # correct cold-start state; the W1.3 refresh guarantees this
            # branch is NOT the production steady state any more)
            assert abs(r["p_home"] - r0_p) < 1e-9
    res2 = A.nba_engine_predict(NBA_PAYLOADS, anchor, anchor,
                                expected_composite_sha=_nba_pins_composite(),
                                predict_path=predict_path)
    assert res2 == res, "engine path must be deterministic"


def test_nba_outcome_leak_injected_completed_row_ignored(tmp_path):
    """Loader law (leak-impossible by construction): a completed row with
    tip >= anchor — strictly-equal or later — must not move any p or the
    state digest. Injected into an internally-consistent COPY (meta resealed
    so the composite/tamper layer is NOT what is under test)."""
    predict_path = A.nba_engine_available(NBA26_ROOT)
    dst = _copy_payload_subset(tmp_path / "leak_corpus")
    base = A.nba_engine_predict(dst, NBA_ANCHOR, NBA_ANCHOR,
                                predict_path=predict_path)
    base_by = {r["match_id"]: (r["p_home"], r["state_digest"]) for r in base}
    payload = dst / "scoreboard_20261020.json"
    data = json.loads(payload.read_text())
    src = next(e for e in data["events"] if e["id"] == "401909089")
    for i, (tip, scores) in enumerate(
            (("2026-10-20T23:00Z", ("112", "104")),        # tip > anchor
             (NBA_ANCHOR.replace(":00:00Z", "Z"), ("1", "0")))):  # tip == anchor
        ev = json.loads(json.dumps(src))
        ev["id"] = f"99990999{i}"                          # fresh id: no dedupe conflict
        ev["date"] = tip
        ev["status"]["type"]["state"] = "post"
        ev["status"]["type"]["completed"] = True
        for c, s in zip(ev["competitions"][0]["competitors"], scores):
            c["score"] = s
        data["events"].append(ev)
        payload.write_text(json.dumps(data))
        _reseal_meta(payload)
        after = A.nba_engine_predict(dst, NBA_ANCHOR, NBA_ANCHOR,
                                     predict_path=predict_path)
        after_by = {r["match_id"]: (r["p_home"], r["state_digest"])
                    for r in after}
        assert after_by == base_by, f"leak via tip {tip} changed predictions"


def test_nba_adapter_refuses_tampered_payload_dir(tmp_path):
    """Byte-tamper a copied payload WITHOUT resealing its .meta -> the adapter
    refuses fail-closed (BLOCKED_NBA_PAYLOAD_TAMPER)."""
    predict_path = A.nba_engine_available(NBA26_ROOT)
    dst = _copy_payload_subset(tmp_path / "tampered_corpus")
    payload = dst / "scoreboard_20261020.json"
    payload.write_bytes(payload.read_bytes() + b"\n")      # bytes != meta sha
    with pytest.raises(BlockError) as ei:
        A.nba_engine_predict(dst, NBA_ANCHOR, NBA_ANCHOR,
                             expected_composite_sha=_nba_pins_composite(),
                             predict_path=predict_path)
    assert ei.value.code == "BLOCKED_NBA_PAYLOAD_TAMPER"


def test_nba_adapter_pin_drift_blocked(tmp_path):
    """nba26 entry bytes drifted from the pins -> BLOCKED_PIN_DRIFT_ENTRY in
    the wiring probe; real-mode compute_forecasts refuses BLOCKED_PIN_DRIFT
    BEFORE any corpus touch (refresh can never run on a drifted entry)."""
    pkg = tmp_path / "wt" / "research" / "papertrade_nba"
    shutil.copytree(NBA26_ROOT / "research" / "papertrade_nba", pkg,
                    ignore=shutil.ignore_patterns("__pycache__"))
    pp = pkg / "predict.py"
    pp.write_text(pp.read_text() + "\n# drifted byte\n")
    roots = dict(execute.PINNED_ROOTS)
    roots["nba26_root"] = pkg.parents[1]          # .../wt (holds research/papertrade_nba)
    wiring = execute.probe_engine("NBA", roots)
    assert wiring["entry_status"] == "BLOCKED_PIN_DRIFT_ENTRY", wiring
    fx = A.load_nba_fixtures_window(NBA_PAYLOADS, NBA_WIN_START, NBA_WIN_END)
    args = argparse.Namespace(sandbox=False, to_date=None,
                              paper_core_root=None, wnba26_root=None,
                              nba_harness_root=None,
                              nba26_root=str(roots["nba26_root"]),
                              soccer_root=None)
    with pytest.raises(BlockError) as ei:
        execute.compute_forecasts(args, "NBA", fx)
    assert ei.value.code == "BLOCKED_PIN_DRIFT"


def test_nba_refresh_prego_refused_and_postgo_manifest_chain(tmp_path):
    """Refresh plumbing, offline: PRE-GO refuses (BLOCKED_NO_GO, nothing
    written); POST-GO (go_ok=True, fake fetch — NO network) writes bytes +
    .meta and appends the self-hashed manifest chain anchored at the corpus's
    own composite; verification accepts the chained extension and fails
    closed on unrecorded bytes."""
    from research.papertrade_exec import nba_payload_composite
    dst = _copy_payload_subset(tmp_path / "refresh_corpus")
    anchor = nba_payload_composite(dst)
    with pytest.raises(BlockError) as ei:
        A.nba_incremental_refresh(dst, "2026-10-20", "2026-10-22", go_ok=False,
                                  fetch_fn=lambda d: b"{}",
                                  anchor_composite=anchor)
    assert ei.value.code == "BLOCKED_NO_GO"
    assert not (dst / A.NBA_REFRESH_MANIFEST).exists()

    calls = []

    def fake_fetch(day: str) -> bytes:
        calls.append(day)
        return json.dumps({"events": [], "day": day}, sort_keys=True).encode() + b"\n"

    rep = A.nba_incremental_refresh(dst, "2026-10-20", "2026-10-22",
                                    go_ok=True, fetch_fn=fake_fetch,
                                    anchor_composite=anchor,
                                    now_utc="2026-10-22T00:00:00Z")
    assert calls == ["20261020", "20261021", "20261022"]
    assert [a["action"] for a in rep["fetched"]] == ["refresh", "refresh", "create"]
    verdict = A.nba_payload_verdict(dst, anchor)
    assert verdict["ok"], verdict
    assert verdict["effective_composite"] == rep["effective_composite"]
    # unrecorded extra payload (valid bytes + meta, but no manifest record):
    # fail closed — the manifest must lawfully account for every byte
    extra = dst / "scoreboard_20261023.json"
    extra.write_bytes(b'{"events": []}\n')
    (dst / "scoreboard_20261023.meta").write_text(
        "url=x\nfetched_at_utc=now\nbytes=14\nsha256="
        + hashlib.sha256(extra.read_bytes()).hexdigest()
        + "\nhttp_status=200\n")
    verdict2 = A.nba_payload_verdict(dst, anchor)
    assert not verdict2["ok"]
    assert "manifest" in verdict2["why"]


def test_nba_window_forecast_stale_after_anchor(env, capcli):
    """The batch anchor (earliest tip minus 6h10m, exclusive) is a hard
    deadline: at it the whole command refuses. The anchor derives from the
    corpus at run time (age-independent after the W1.3 refresh law)."""
    fx = A.load_nba_fixtures_window(NBA_PAYLOADS, NBA_WIN_START, NBA_WIN_END)
    anchor, _ = execute.batch_anchor(fx, "NBA")
    from datetime import datetime as _dt, timedelta as _td, timezone as _tz
    a_dt = _dt.strptime(anchor, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=_tz.utc)
    at = anchor                                    # == anchor (exclusive)
    after = (a_dt + _td(minutes=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
    for now in (at, after):
        code, out = capcli(env, "forecast", "--league", "NBA",
                           "--date", NBA_WIN_START, "--to-date", NBA_WIN_END,
                           now=now)
        assert code == EXIT_BLOCKED_ANCHOR
        assert out["blocked"] == "BLOCKED_ANCHOR_PASSED"
    assert rows_of(env, "FORECAST") == []


def test_nba_window_success_chain_sandbox(env, capcli):
    """Full chain forecast -> quote -> decide on the 8-row real opening
    window, SANDBOX, outcome-masked: fixture identity REAL (frozen payloads),
    persisted p/odds SYNTHETIC and labeled; duplicate decide is a no-op."""
    fx = A.load_nba_fixtures_window(NBA_PAYLOADS, NBA_WIN_START,
                                    NBA_WIN_END)
    n = len(fx)
    assert n >= 1                          # age-independent window size
    code, out = capcli(env, "plan", "--league", "NBA", "--date", NBA_WIN_START,
                       "--to-date", NBA_WIN_END)
    assert code == EXIT_OK and out["leagues"]["NBA"]["count"] == n
    code, out = capcli(env, "forecast", "--league", "NBA",
                       "--date", NBA_WIN_START, "--to-date", NBA_WIN_END)
    assert code == EXIT_OK and len(out["written"]) == n
    assert out["wiring"]["entry_status"] == "WIRED_ENGINE_READY"
    capcli(env, "quote", "--league", "NBA", "--date", NBA_WIN_START,
           "--to-date", NBA_WIN_END)
    code, d = capcli(env, "decide", "--league", "NBA",
                     "--date", NBA_WIN_START, "--to-date", NBA_WIN_END)
    assert code == EXIT_OK and len(d["journaled"]) == n
    fcs = [r for r in rows_of(env, "FORECAST") if r["league"] == "NBA"]
    assert len(fcs) == n
    assert all(r["mode"] == "SYNTHETIC"
               and r["model_version_sha"] == "SYNTHETIC_ADAPTER_NOT_ENGINE"
               and "SYNTHETIC" in r["source_ref"] for r in fcs)
    assert all(r["fixture_source"].startswith("espn_schedule_2026_27/")
               for r in fcs)
    assert sorted(r["kickoff_utc"] for r in fcs)[0] == \
        min(f.kickoff_utc for f in fx)     # age-independent earliest tip
    # duplicate-bet law at runner level: a second decide is a full no-op
    code, d2 = capcli(env, "decide", "--league", "NBA",
                      "--date", NBA_WIN_START, "--to-date", NBA_WIN_END)
    assert code == EXIT_OK and d2["journaled"] == [] and \
        len(d2["skipped"]) == n
    assert len(rows_of(env, "DECISION")) == n


def test_nba_gate_missing_token_refusal(env, capcli):
    """Missing GO: the NBA path refuses identically on a control dir without
    the token (world-independent; the real dir is post-GO by design)."""
    reg = json.loads((REPO / "plans" / "CYCLE_REGISTRY.json").read_text())
    cycles = reg.get("cycles", reg)
    if isinstance(cycles, dict):
        row = cycles.get("SPORTS-PAPERTRADE-EXEC-V1")
        if row is not None:
            row["phase"] = "READY_PENDING_ONE_OWNER_GO"
    else:
        for c in cycles:
            if c.get("cycle_id") == "SPORTS-PAPERTRADE-EXEC-V1":
                c["phase"] = "READY_PENDING_ONE_OWNER_GO"
    (env["ctrl"] / "CYCLE_REGISTRY.json").write_text(json.dumps(reg, indent=1))
    (env["ctrl"] / "GO_TOKEN.json").unlink(missing_ok=True)
    code, out = capcli(env, "forecast", "--league", "NBA",
                       "--date", NBA_WIN_START, "--to-date", NBA_WIN_END)
    assert code == EXIT_BLOCKED_NO_GO and out["blocked"] == "BLOCKED_NO_GO"
    code, out = capcli(env, "run-day", "--date", "2026-10-21")
    assert code == EXIT_BLOCKED_NO_GO
    assert not (env["data"] / "ledger").exists()


# ------------------------------------------- SOCCER real path (events wiring) --

SOC_EVENT_DAY = "2026-11-12"   # REAL UNL fixture day: England vs Croatia 19:45Z


def _events_payload(events: list[dict]) -> bytes:
    return json.dumps(events).encode()


def _fake_odds_env(events: list[dict]):
    """Offline fake client + the REAL pinned exception classes (no network,
    no key). Records every call like the core client records quota."""
    from research.papertrade_exec import load_pinned_package
    core = load_pinned_package("spt_core", "paper_core")
    odds_mod = core.odds_client
    calls = []

    class FakeClient:
        fingerprint = "sandbox-fake-00"

        def get_events(self, sport_key: str):
            calls.append(("events", sport_key))
            return _events_payload(events), {"x-requests-remaining": "493"}

        def get_odds(self, sport_key: str, **kw):
            calls.append(("odds", sport_key))
            raise AssertionError("get_odds not expected in this test")

    return odds_mod, FakeClient(), calls


def test_soccer_events_schema_hardening():
    good = {"id": "ev1", "sport_key": "soccer_uefa_nations_league",
            "sport_title": "UEFA Nations League",
            "commence_time": "2026-11-12T19:45:00Z",
            "home_team": "England", "away_team": "Croatia"}
    # happy path (real observed schema, extra keys tolerated)
    fx = A.soccer_fixtures_from_events(_events_payload([good]), "k",
                                       snapshot_sha="a" * 64)
    assert fx[0].match_id == "ev1" and fx[0].home == "England"
    assert fx[0].kickoff_utc == "2026-11-12T19:45:00Z"
    assert "@aaaaaaaaaaaa#" in fx[0].source_ref
    # non-list payload
    with pytest.raises(BlockError) as ei:
        A.soccer_fixtures_from_events(b'{"events": []}', "k")
    assert ei.value.code == "BLOCKED_FIXTURES_SCHEMA"
    # required field missing / empty
    for mutated in ({**good, "away_team": ""}, {k: v for k, v in good.items()
                                                if k != "commence_time"},
                    {**good, "id": 42}):
        with pytest.raises(BlockError) as ei:
            A.soccer_fixtures_from_events(_events_payload([mutated]), "k")
        assert ei.value.code == "BLOCKED_FIXTURES_SCHEMA"
    # unparseable commence_time
    with pytest.raises(BlockError) as ei:
        A.soccer_fixtures_from_events(
            _events_payload([{**good, "commence_time": "not-a-time"}]), "k")
    assert ei.value.code == "BLOCKED_FIXTURES_SCHEMA"
    # exact duplicate collapses; conflicting duplicate refuses
    fx = A.soccer_fixtures_from_events(_events_payload([good, dict(good)]), "k")
    assert len(fx) == 1
    with pytest.raises(BlockError) as ei:
        A.soccer_fixtures_from_events(
            _events_payload([good, {**good, "home_team": "Scotland"}]), "k")
    assert ei.value.code == "BLOCKED_FIXTURES_DUPLICATE"
    # two different ids in one (commence_time, team-set) slot -> ambiguous
    with pytest.raises(BlockError) as ei:
        A.soccer_fixtures_from_events(
            _events_payload([good, {**good, "id": "ev2"}]), "k")
    assert ei.value.code == "BLOCKED_FIXTURES_DUPLICATE"


def test_soccer_real_fixtures_fake_client_day_filter_snapshot(env):
    odds_mod, client, calls = _fake_odds_env([
        {"id": "engcro", "home_team": "England", "away_team": "Croatia",
         "commence_time": "2026-11-12T19:45:00Z"},
        {"id": "otherday", "home_team": "Italy", "away_team": "Spain",
         "commence_time": "2026-11-13T19:45:00Z"}])
    args = argparse.Namespace(data_root=str(env["data"]))
    fx = execute.real_soccer_fixtures(args, SOC_EVENT_DAY,
                                      client=client, odds_mod=odds_mod)
    # the union runs across EVERY registered sport key (config law: the list
    # grows only by an explicit config commit — it grew to 5 on 2026-10-07)
    expected_keys = execute.load_config()["sport_keys"]["SOCCER"]
    assert calls == [("events", k) for k in expected_keys]
    assert [f.match_id for f in fx] == ["engcro"], "day filter is kickoff-UTC"
    snap = env["data"] / "data" / "events_soccer_uefa_nations_league.json"
    meta = json.loads((env["data"] / "data" /
                       "events_soccer_uefa_nations_league.meta.json").read_text())
    import hashlib as _h
    assert meta["sha256"] == _h.sha256(snap.read_bytes()).hexdigest()
    assert snap.read_bytes() == _events_payload([
        {"id": "engcro", "home_team": "England", "away_team": "Croatia",
         "commence_time": "2026-11-12T19:45:00Z"},
        {"id": "otherday", "home_team": "Italy", "away_team": "Spain",
         "commence_time": "2026-11-13T19:45:00Z"}])
    assert fx[0].source_ref.startswith(
        "the_odds_api/events/soccer_uefa_nations_league@"
        + meta["sha256"][:12] + "#engcro")


def test_soccer_real_fixtures_network_failure_loud(env):
    odds_mod, _c, _calls = _fake_odds_env([])

    class Boom:
        fingerprint = "x"

        def get_events(self, key):
            raise OSError("network down")

    with pytest.raises(BlockError) as ei:
        execute.real_soccer_fixtures(argparse.Namespace(data_root=str(env["data"])),
                                     SOC_EVENT_DAY, client=Boom(),
                                     odds_mod=odds_mod)
    assert ei.value.code == "BLOCKED_ODDS_API"


def test_soccer_extension_crosswalk_laws(env, monkeypatch):
    ext = REPO / "research" / "papertrade_exec" / \
        "PROVIDER_NAME_CROSSWALK_EXTENSION.csv"
    replay_path = A.soccer_engine_available(SOCCER_ROOT / "integration")
    if replay_path is None:      # resolve via pinned roots like production
        replay_path = A.soccer_engine_available(execute.PINNED_ROOTS["soccer_root"])
    # 1) the committed extension verifies and extends the pinned seed
    mod, mapping = A.soccer_extension_crosswalk(replay_path, ext)
    assert len(mapping) >= 8 + 2, "seed 8 + at least the 2 evidenced pairs"
    assert "England" in mapping and mapping["England"] == "England"
    assert "Croatia" in mapping and mapping["Croatia"] == "Croatia"
    # 2) tampered extension bytes WITHOUT a deliberate re-pin -> the sha law
    #    refuses (the committed pin points at the true extension bytes)
    tampered = env["data"] / "tampered_ext.csv"
    tampered.write_bytes(ext.read_bytes() + b"Evil,Evil,x,y,z\n")
    with pytest.raises(BlockError) as ei:
        A.soccer_extension_crosswalk(replay_path, tampered)
    assert ei.value.code == "BLOCKED_PIN_DRIFT"
    # 3) bytes that do NOT extend the pinned seed verbatim -> refused even
    #    when their own sha is what the pin says (frozen anchor is prefix law;
    #    a deliberate re-pin cannot launder a seed rewrite)
    shrunk = env["data"] / "shrunk_ext.csv"
    shrunk.write_bytes(b"provider_name,corpus_name,evidence,v,s\n"
                       b"England,England,x,y,EXTENDED\n")
    import hashlib as _h
    monkeypatch.setattr(A, "load_pins",
                        lambda: _pins_with_ext_sha(_h.sha256(
                            shrunk.read_bytes()).hexdigest()))
    with pytest.raises(BlockError) as ei:
        A.soccer_extension_crosswalk(replay_path, shrunk)
    assert ei.value.code == "BLOCKED_PIN_DRIFT" and "prefix" in ei.value.detail
    # 4) the split never lets an unresolved name reach the engine
    fxs = [A.Fixture("SOCCER", "m1", "England", "Croatia",
                     "2026-11-12T19:45:00Z", "k", "2026-11-12", "s"),
           A.Fixture("SOCCER", "m2", "Atlantis", "Croatia",
                     "2026-11-12T20:00:00Z", "k", "2026-11-12", "s")]
    resolvable, missed = A.soccer_crosswalk_split(mod, mapping, fxs)
    assert [f.match_id for f in resolvable] == ["m1"]
    assert len(missed) == 1 and missed[0][0].match_id == "m2" \
        and "Atlantis" in missed[0][1]


def _pins_with_ext_sha(sha: str) -> dict:
    import research.papertrade_exec as pkg
    pins = json.loads((REPO / "research" / "papertrade_exec" / "pins.json")
                      .read_text())
    pins["data"]["soccer_crosswalk_extension_csv"]["sha256"] = sha
    return pins


def test_soccer_forecast_real_engine_in_memory_only(env):
    """Real-mode compute_forecasts for SOCCER: pinned engine + extension
    crosswalk over the REAL fixture identity, IN MEMORY (nothing persisted;
    sandbox runs never enter this branch)."""
    fx = A.Fixture("SOCCER", "engcro-probe", "England", "Croatia",
                   "2026-11-12T19:45:00Z", "soccer_uefa_nations_league",
                   SOC_EVENT_DAY, "the_odds_api/events/x#engcro-probe")
    args = argparse.Namespace(sandbox=False, to_date=None,
                              paper_core_root=None, wnba26_root=None,
                              nba_harness_root=None, nba26_root=None,
                              soccer_root=None)
    drafts, wiring = execute.compute_forecasts(args, "SOCCER", [fx])
    assert wiring["entry_status"] == "WIRED_ENGINE_READY"
    assert wiring["engine_mode"] == "ENGINE" and wiring["crosswalk_miss"] == []
    d = drafts[0]
    assert set(d["p"]) == {"HOME", "DRAW", "AWAY"}
    assert abs(sum(d["p"].values()) - 1.0) < 1e-9
    assert d["mode"] == "ENGINE"
    drafts2, _ = execute.compute_forecasts(args, "SOCCER", [fx])
    assert drafts2[0]["p"] == d["p"], "engine path deterministic"
    # unresolved provider name -> journaled NOT_RUN draft absent, miss recorded
    fx_bad = A.Fixture("SOCCER", "atl-probe", "Atlantis", "Croatia",
                       "2026-11-12T20:00:00Z", "soccer_uefa_nations_league",
                       SOC_EVENT_DAY, "the_odds_api/events/x#atl-probe")
    drafts3, wiring3 = execute.compute_forecasts(args, "SOCCER", [fx_bad])
    assert drafts3 == [] and len(wiring3["crosswalk_miss"]) == 1
    m = wiring3["crosswalk_miss"][0]
    assert m["match_id"] == "atl-probe" and "Atlantis" in m["reason"]


def test_crosswalk_miss_decision_shape_and_terminal(env):
    core = _core()
    led = core.ledger.PaperLedger(
        env["data"] / "sandbox" / "sandbox_ledger.jsonl")
    led.load()
    led.genesis(plan_sha256="xw-test", created_at_utc="2026-10-01T00:00:00Z",
                sandbox=True)
    fx = A.Fixture("SOCCER", "atl-probe", "Atlantis", "Croatia",
                   "2026-11-12T20:00:00Z", "soccer_uefa_nations_league",
                   SOC_EVENT_DAY, "the_odds_api/events/x#atl-probe")
    row = execute.crosswalk_miss_decision(
        fx, {"reason": "CrosswalkMissError: provider name 'Atlantis' ..."},
        NOW)
    assert row["status"] == "CROSSWALK_MISS" and row["stake_cents"] == 0
    assert "Atlantis" in row["reason"]
    led.append_decision(row)
    assert "atl-probe" in led.decided_match_ids(), \
        "CROSSWALK_MISS is terminal: decide must skip it (no re-decision)"
    ok, _ = led.verify_chain()
    assert ok


def test_quote_write_plan_rerun_and_decided_safety():
    rows = [{"type": "MARKET_QUOTE", "match_id": "m1"},
            {"type": "MARKET_QUOTE", "match_id": "m2"},
            {"type": "MARKET_QUOTE", "match_id": "m3"}]
    journals = [{"type": "DECISION", "match_id": "m4", "status": "NO_QUOTE"},
                {"type": "DECISION", "match_id": "m5", "status": "NO_QUOTE"}]
    plan_w = execute._quote_write_plan(rows, journals, existing={"m2": {}},
                                       decided={"m3", "m5"})
    assert [r["match_id"] for r in plan_w["write"]] == ["m1"]
    assert plan_w["skipped_existing"] == ["m2"]
    assert plan_w["skipped_decided"] == ["m3"]
    assert [j["match_id"] for j in plan_w["journal"]] == ["m4"]
    # rerun after applying: everything already decided/existing -> no-op
    decided2 = {"m3", "m5", "m4"}
    existing2 = {"m1": {}, "m2": {}}
    plan_w2 = execute._quote_write_plan(rows, journals, existing2, decided2)
    assert plan_w2["write"] == [] and plan_w2["journal"] == []


# ------------------------------------- stage/venue law + cross-key dedup (2026-10-07 expansion) --

def test_soccer_stage_law_classification():
    league = execute.soccer_stage_law("soccer_uefa_nations_league", "2026-11-12")
    assert league["bet_eligible"] is True
    assert league["stage"] == "LEAGUE_PHASE_HOME_AWAY"
    ko = execute.soccer_stage_law("soccer_uefa_nations_league", "2027-03-25")
    assert ko["bet_eligible"] is False
    assert ko["stage"] == "KNOCKOUT_ET_POSSIBLE"
    unknown_key = execute.soccer_stage_law("soccer_some_club_league", "2026-11-12")
    assert unknown_key["bet_eligible"] is False and \
        unknown_key["stage"] == "UNKNOWN_STAGE"
    uncovered = execute.soccer_stage_law("soccer_uefa_nations_league", "2026-12-15")
    assert uncovered["bet_eligible"] is False and "outside every" in \
        uncovered["reason"]


def test_soccer_stage_law_blocks_engine_before_crosswalk(env):
    """Real-mode compute_forecasts: a knockout-window fixture (ET possible ->
    model 90/120-min target vs bookmaker 90-min h2h mismatch) never reaches
    the crosswalk or the engine; a league-phase fixture does."""
    ko_fx = A.Fixture("SOCCER", "ko-probe", "England", "Croatia",
                      "2027-03-25T19:45:00Z", "soccer_uefa_nations_league",
                      "2027-03-25", "the_odds_api/events/x#ko-probe")
    lg_fx = A.Fixture("SOCCER", "lg-probe", "England", "Croatia",
                      "2026-11-12T19:45:00Z", "soccer_uefa_nations_league",
                      "2026-11-12", "the_odds_api/events/x#lg-probe")
    args = argparse.Namespace(sandbox=False, to_date=None,
                              paper_core_root=None, wnba26_root=None,
                              nba_harness_root=None, nba26_root=None,
                              soccer_root=None)
    drafts, wiring = execute.compute_forecasts(args, "SOCCER", [ko_fx])
    assert drafts == []
    assert len(wiring["stage_law_miss"]) == 1
    m = wiring["stage_law_miss"][0]
    assert m["status"] == "NOT_RUN_STAGE_LAW" and m["stage"] == "KNOCKOUT_ET_POSSIBLE"
    assert wiring["crosswalk_miss"] == [], "stage-missed fixture never crosswalked"
    drafts2, wiring2 = execute.compute_forecasts(args, "SOCCER", [lg_fx])
    assert wiring2["stage_law_miss"] == [] and len(drafts2) == 1


def test_stage_law_journal_terminal(env):
    core = _core()
    led = core.ledger.PaperLedger(
        env["data"] / "sandbox" / "sandbox_ledger.jsonl")
    led.load()
    led.genesis(plan_sha256="stage-test", created_at_utc="2026-10-01T00:00:00Z",
                sandbox=True)
    fx = A.Fixture("SOCCER", "ko-probe", "England", "Croatia",
                   "2027-03-25T19:45:00Z", "soccer_uefa_nations_league",
                   "2027-03-25", "the_odds_api/events/x#ko-probe")
    row = execute.stage_law_decision(
        fx, {"stage": "KNOCKOUT_ET_POSSIBLE",
             "reason": "B1 90/120-min full-time target vs 90-min h2h"}, NOW)
    assert row["status"] == "NOT_RUN_STAGE_LAW" and row["stake_cents"] == 0
    assert "KNOCKOUT_ET_POSSIBLE" in row["reason"]
    led.append_decision(row)
    assert "ko-probe" in led.decided_match_ids(), "terminal: decide must skip"
    ok, _ = led.verify_chain()
    assert ok


def test_cross_key_slot_collision_refused(env, monkeypatch):
    """The same real match listed under two registered sport keys with
    different event ids must refuse (1:1 ambiguity); genuinely different
    matches union."""
    odds_mod, _c, _calls = _fake_odds_env([])

    class TwoKeyClient:
        fingerprint = "sandbox-two-key"
        payloads = {
            "key_a": [{"id": "evA", "home_team": "England",
                       "away_team": "Croatia",
                       "commence_time": "2026-11-12T19:45:00Z"}],
            "key_b": [{"id": "evB", "home_team": "England",
                       "away_team": "Croatia",
                       "commence_time": "2026-11-12T19:45:00Z"}],
        }

        def get_events(self, key):
            return json.dumps(self.payloads[key]).encode(), {}

    monkeypatch.setattr(execute, "_soccer_sport_keys",
                        lambda: ["key_a", "key_b"])
    # W1.1 poll gate: these synthetic keys are ACTIVE for this test (the
    # slot-collision law, not the poll gate, is the subject here).
    monkeypatch.setattr(execute, "_key_window_active",
                        lambda key, day: True)
    with pytest.raises(BlockError) as ei:
        execute.real_soccer_fixtures(
            argparse.Namespace(data_root=str(env["data"])), SOC_EVENT_DAY,
            client=TwoKeyClient(), odds_mod=odds_mod)
    assert ei.value.code == "BLOCKED_FIXTURES_DUPLICATE"
    assert "key_a" in ei.value.detail and "key_b" in ei.value.detail

    # genuinely different matches across keys union (day-filtered)
    class GoodClient(TwoKeyClient):
        payloads = {
            "key_a": [{"id": "evA", "home_team": "England",
                       "away_team": "Croatia",
                       "commence_time": "2026-11-12T19:45:00Z"}],
            "key_b": [{"id": "evB", "home_team": "Scotland",
                       "away_team": "Wales",
                       "commence_time": "2026-11-12T19:45:00Z"},
                      {"id": "evC", "home_team": "Italy",
                       "away_team": "Spain",
                       "commence_time": "2026-11-13T19:45:00Z"}],
        }

    fx = execute.real_soccer_fixtures(
        argparse.Namespace(data_root=str(env["data"])), SOC_EVENT_DAY,
        client=GoodClient(), odds_mod=odds_mod)
    assert [f.match_id for f in fx] == ["evA", "evB"], "day filter holds"


def test_soccer_competition_report_breakdown(env, capcli):
    """The exec-owned supplement reports BET / NO_BET / NOT_RUN per soccer
    competition next to the pinned dashboard build."""
    core = _core()
    ledp = env["data"] / "sandbox" / "sandbox_ledger.jsonl"
    led = core.ledger.PaperLedger(ledp).load()
    led.genesis(plan_sha256="comp-report", created_at_utc="2026-10-01T00:00:00Z",
                sandbox=True)
    led.append({"type": "FORECAST", "league": "SOCCER",
                "match_id": "m1", "competition": "soccer_uefa_nations_league",
                "kickoff_utc": "2026-11-12T19:45:00Z", "p": {}, "mode": "ENGINE",
                "recorded_at_utc": NOW, "model_version_sha": "x", "source_ref": "x"})
    led.append_decision({"type": "DECISION", "league": "SOCCER", "match_id": "m1",
                         "competition": "soccer_uefa_nations_league",
                         "home": "England", "away": "Croatia",
                         "kickoff_utc": "2026-11-12T19:45:00Z",
                         "decided_at_utc": NOW, "status": "NO_EDGE",
                         "stake_cents": 0, "chosen_leg": None})
    led.append_decision({"type": "DECISION", "league": "SOCCER", "match_id": "m2",
                         "competition": "soccer_uefa_nations_league",
                         "home": "Scotland", "away": "Wales",
                         "kickoff_utc": "2026-11-12T20:00:00Z",
                         "decided_at_utc": NOW, "status": "NOT_RUN_STAGE_LAW",
                         "reason": "stage", "stake_cents": 0, "chosen_leg": None})
    outdir = env["data"] / "dash-comp"
    code, out = capcli(env, "dashboard", "--out", str(outdir))
    assert code == EXIT_OK
    rep = json.loads((outdir / "soccer_by_competition.json").read_text())
    unl = rep["competitions"]["soccer_uefa_nations_league"]
    assert unl["matches"] == 2 and unl["forecasts"] == 1
    assert unl["bet"] == 0 and unl["no_bet"] == 1 and unl["not_run_blocked"] == 1
    assert out["soccer_by_competition"]["soccer_uefa_nations_league"]["no_bet"] == 1


def test_journal_quota_skip_never_rejournals_decided(env):
    core = _core()
    led = core.ledger.PaperLedger(
        env["data"] / "sandbox" / "sandbox_ledger.jsonl")
    led.load()
    led.genesis(plan_sha256="qs-test", created_at_utc="2026-10-01T00:00:00Z",
                sandbox=True)
    fx = execute.synthetic_soccer_fixtures(SOC_DAY)
    first = execute.journal_quota_skip(led, fx, NOW, "cap", {})
    assert len(first) == 3
    decided = led.decided_match_ids()
    second = execute.journal_quota_skip(led, fx, NOW, "cap again", {},
                                        decided=decided)
    assert second == [], "same-day rerun must not duplicate QUOTA_SKIP rows"
    assert len([r for r in led.rows if r["type"] == "DECISION"]) == 3
    ok, _ = led.verify_chain()
    assert ok


def test_in_lock_recheck_for_uses_pinned_core(env):
    """Regression (ERRATUM_EXEC_3 incident): the real quote journal-append
    path crashed on `from research.papertrade import risk` — a module name
    that never exists in this worktree (the core is pinned as spt_core).
    The exact call site — append_decision(recheck=in_lock_recheck_for(...)) —
    must work against the sandbox gate seams."""
    core = _core()
    ledp = env["data"] / "sandbox" / "sandbox_ledger.jsonl"
    led = core.ledger.PaperLedger(ledp).load()
    led.genesis(plan_sha256="rlc-test", created_at_utc="2026-10-01T00:00:00Z",
                sandbox=True)
    args = argparse.Namespace(sandbox=True, data_root=str(env["data"]),
                              sandbox_control_dir=str(env["ctrl"]),
                              sandbox_registry=str(env["ctrl"] /
                                                   "CYCLE_REGISTRY.json"),
                              paper_core_root=None, wnba26_root=None,
                              nba_harness_root=None, nba26_root=None,
                              soccer_root=None)
    recheck = execute.in_lock_recheck_for(led, args, NOW)
    assert callable(recheck)
    j = {"type": "DECISION", "league": "SOCCER",
         "match_id": "journal-append-probe",
         "competition": "soccer_uefa_nations_league", "home": "England",
         "away": "Croatia", "kickoff_utc": "2026-11-12T19:45:00Z",
         "decided_at_utc": NOW, "status": "NO_QUOTE",
         "reason": "unit probe of the exact crash site", "stake_cents": 0,
         "chosen_leg": None}
    stored = led.append_decision(j, recheck=recheck)
    assert stored["status"] == "NO_QUOTE"
    ok, _ = led.verify_chain()
    assert ok


def test_soccer_dashboard_counts_crosswalk_miss(env, capcli):
    """Dashboard NOT_RUN counters: a CROSSWALK_MISS decision lands under the
    identity_crosswalk cause (ledger-visible, never dropped)."""
    core = _core()
    ledp = env["data"] / "sandbox" / "sandbox_ledger.jsonl"
    led = core.ledger.PaperLedger(ledp).load()
    led.genesis(plan_sha256="xw-dash", created_at_utc="2026-10-01T00:00:00Z",
                sandbox=True)
    fx = A.Fixture("SOCCER", "atl-dash", "Atlantis", "Croatia",
                   "2026-11-12T20:00:00Z", "soccer_uefa_nations_league",
                   SOC_EVENT_DAY, "the_odds_api/events/x#atl-dash")
    led.append_decision(execute.crosswalk_miss_decision(
        fx, {"reason": "CrosswalkMissError: 'Atlantis' has no crosswalk entry"},
        NOW))
    outdir = env["data"] / "dash-xw"
    code, _ = capcli(env, "dashboard", "--out", str(outdir))
    assert code == EXIT_OK
    summary = json.loads((outdir / "summary.json").read_text())
    assert summary["status_counts"].get("CROSSWALK_MISS", 0) == 1
    assert summary["not_run_by_cause"].get("identity_crosswalk", 0) == 1



def _v2_opinion_from_pending(env, verdict, reason=None):
    """The production v2 rhythm: decide pass 1 writes the PENDING queue
    (the runner owns the candidate hash); the producer binds the opinion
    to EXACTLY that hash; decide pass 2 consumes it."""
    from research.papertrade_exec import ai_gate_v2 as G
    from research.papertrade_exec.ai_producer import registered_prompt_sha
    reg = registered_prompt_sha(
        Path(__file__).resolve().parents[2])[0]
    pending = G._load_pending(env["data"], sandbox=True)
    assert pending, "decide pass 1 must record the PENDING queue"
    written = []
    for mid, entry in pending.items():
        G.record_opinion(env["data"], {
            "match_id": mid,
            "candidate_hash": entry["candidate_hash"],
            "verdict": verdict,
            "reason_codes": reason or [f"R-{verdict}"],
            "summary": "reviewed with captured sources",
            "sources": [{"url": "https://example.com/wire",
                         "fetched_at_utc": "2026-10-08T09:00:00Z",
                         "excerpt": "headline"}],
            "model_id": "battery-model", "provider": "battery",
            "prompt_version": "AI_PROMPT_V2",
            "prompt_sha256": reg,
            "created_at_utc": "2026-10-08T09:00:00Z"},
            sandbox=True)   # U4-M6: decide consumed the sandbox plane
        written.append(mid)
    return written

def test_pm_cutover_ai_gate_sandbox_chain(env, capcli, monkeypatch):
    """Round-17 DoD rehearsal: the production CLI chain with BOTH gates ON
    (sandbox-only flip; the committed config stays OFF) — PM seam quote ->
    crosswalk + converted odds in the ledger -> AI ABSTAIN demotes the
    candidate -> AI KEEP (fully-gated) places -> AI VETO refuses. The Odds
    API capture path is never touched (no fallback seam exists)."""
    monkeypatch.setattr(execute, "papertrade_flags",
                        lambda args: {"pm_cutover_active": True,
                                      "ai_authority_active": True})
    probe = {
        "401918299": {
            "legs": {
                "HOME": {"best_ask": 0.40, "vwap_ask": 0.40,
                         "filled_shares": 25.0, "fee_total": 0.3,
                         "levels": 1, "depth_ok": True},
                "AWAY": {"best_ask": 0.62, "vwap_ask": 0.62,
                         "filled_shares": 25.0, "fee_total": 0.4,
                         "levels": 1, "depth_ok": True}},
            "all_present": True, "event_id": "PM-EV-W1",
            "market_id": "PM-MK-W1"}}
    probe_file = env["data"] / "pm_probe.json"
    probe_file.write_text(json.dumps(probe))
    monkeypatch.setenv("PAPERTRADE_PM_PROBE_JSON", str(probe_file))

    assert capcli(env, "forecast", "--league", "WNBA",
                  "--date", WNBA_DAY)[0] == EXIT_OK
    code, q = capcli(env, "quote", "--league", "WNBA", "--date", WNBA_DAY)
    assert code == EXIT_OK and q["mode"] == "PM_CUTOVER_SANDBOX_SEAM"
    assert q["written"] == ["401918299"]
    qt = rows_of(env, "MARKET_QUOTE")[0]
    assert qt["bookmaker"] == "POLYMARKET_CLOB" and \
        qt["market"] == "moneyline_2way"
    assert qt["pm_crosswalk"]["fixture_id"] == "401918299"
    assert qt["stake_walk_cents"] == 1000       # 1% of the 100000c genesis
    assert qt["odds"]["HOME"] == round(1 / 0.40, 6)   # executable VWAP law

    # --- W4.4 silence law: NO valid hash-locked opinion inside the window
    # => PENDING_AI — the candidate stays UNDECIDED (never demoted, never
    # killed); the queue carries the candidate hash for the producer.
    code, d = capcli(env, "decide", "--league", "WNBA", "--date", WNBA_DAY)
    assert code == EXIT_OK and len(d["journaled"]) == 1
    assert d["journaled"][0]["status"] == "PENDING_AI"
    from research.papertrade_exec import ai_gate_v2 as G
    pending = G._load_pending(env["data"], sandbox=True)
    assert "401918299" in pending and pending["401918299"]["candidate_hash"]
    assert rows_of(env, "DECISION", "BET_PAPER") == []


def test_pm_cutover_ai_keep_veto_scenarios(env, capcli, monkeypatch):
    monkeypatch.setattr(execute, "papertrade_flags",
                        lambda args: {"pm_cutover_active": True,
                                      "ai_authority_active": True})
    probe = {
        "401918299": {
            "legs": {
                "HOME": {"best_ask": 0.40, "vwap_ask": 0.40,
                         "filled_shares": 25.0, "fee_total": 0.3,
                         "levels": 1, "depth_ok": True},
                "AWAY": {"best_ask": 0.62, "vwap_ask": 0.62,
                         "filled_shares": 25.0, "fee_total": 0.4,
                         "levels": 1, "depth_ok": True}},
            "all_present": True, "event_id": "PM-EV-W1",
            "market_id": "PM-MK-W1"}}
    probe_file = env["data"] / "pm_probe.json"
    probe_file.write_text(json.dumps(probe))
    monkeypatch.setenv("PAPERTRADE_PM_PROBE_JSON", str(probe_file))
    capcli(env, "forecast", "--league", "WNBA", "--date", WNBA_DAY)
    capcli(env, "quote", "--league", "WNBA", "--date", WNBA_DAY)
    # decide pass 1 => PENDING + hash; producer binds an ALLOW opinion to
    # EXACTLY that hash; decide pass 2 places.
    capcli(env, "decide", "--league", "WNBA", "--date", WNBA_DAY)
    _v2_opinion_from_pending(env, "ALLOW")
    code, d = capcli(env, "decide", "--league", "WNBA", "--date", WNBA_DAY)
    assert code == EXIT_OK
    assert d["journaled"][0]["status"] == "BET_PAPER"
    dec = rows_of(env, "DECISION", "BET_PAPER")[0]
    assert dec["ai_gate"]["decision"] == "PLACE"
    assert dec["ai_gate"]["opinion_verdict"] == "ALLOW"
    # frozen numbers untouched by the AI (it supplied NO numbers)
    assert dec["p_frozen"]["HOME"] == 0.707
    assert dec["odds_frozen"]["HOME"] == round(1 / 0.40, 6)
    # in-law append: stake = 1% of genesis equity
    assert dec["stake_cents"] == 1000 and dec["stake_law"] == "v3-1pct"



def test_pm_cutover_ai_veto_refusal(env, capcli, monkeypatch):
    """A PASSING deterministic candidate + AI VETO => terminal
    NOT_PLACED_AI_GATE (the AI can stop a bet; it can never start one)."""
    monkeypatch.setattr(execute, "papertrade_flags",
                        lambda args: {"pm_cutover_active": True,
                                      "ai_authority_active": True})
    probe_file = env["data"] / "pm_probe.json"
    probe_file.write_text(json.dumps({"401918299": {
        "legs": {"HOME": {"best_ask": 0.40, "vwap_ask": 0.40,
                          "filled_shares": 25.0, "fee_total": 0.3,
                          "levels": 1, "depth_ok": True},
                 "AWAY": {"best_ask": 0.62, "vwap_ask": 0.62,
                          "filled_shares": 25.0, "fee_total": 0.4,
                          "levels": 1, "depth_ok": True}},
        "all_present": True, "event_id": "PM-EV-W1",
        "market_id": "PM-MK-W1"}}))
    monkeypatch.setenv("PAPERTRADE_PM_PROBE_JSON", str(probe_file))
    capcli(env, "forecast", "--league", "WNBA", "--date", WNBA_DAY)
    capcli(env, "quote", "--league", "WNBA", "--date", WNBA_DAY)
    capcli(env, "decide", "--league", "WNBA", "--date", WNBA_DAY)
    _v2_opinion_from_pending(env, "VETO", reason=["INJURY_RISK"])
    code, d = capcli(env, "decide", "--league", "WNBA", "--date", WNBA_DAY)
    assert code == EXIT_OK
    assert d["journaled"][0]["status"] == "NOT_PLACED_AI_VETO"
    dec = rows_of(env, "DECISION", "NOT_PLACED_AI_VETO")[0]
    assert dec["ai_gate"]["opinion_verdict"] == "VETO"
    assert dec["ai_gate"]["hypothetical_stake_cents"] == 1000
    assert dec["stake_cents"] == 0 and dec["chosen_leg"] is None
    assert rows_of(env, "DECISION", "BET_PAPER") == []
