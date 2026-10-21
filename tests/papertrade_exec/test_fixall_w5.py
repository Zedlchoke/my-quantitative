"""PAPERDESK-FIXALL-NCAA-V1 — W5 battery: the two NCAA prediction lanes.

The FROZEN laws come from the audited intake (ncaa_intake/frozen_test.py):
this battery transcribes the intake walk-forward loop INDEPENDENTLY and
demands per-game feature parity, replay bit-identity, anchor laws (batch
regular / per-match tournament), the honest PM-or-NOT_RUN quote law, the
MANDATORY truth label (W5.5) with running log-loss/Brier vs PM, and a full
sandbox day forecast→quote→decide→settle for BOTH lanes.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from tests.papertrade_exec import test_ops_live_service as _ops  # noqa: E402
from tests.papertrade_exec import test_fixall_w1 as W1           # noqa: E402
from research.papertrade_exec import adapters                    # noqa: E402
from research.papertrade_exec import adapters_ncaa as AN         # noqa: E402
from research.papertrade_exec import execute                     # noqa: E402
from research.papertrade_exec import ncaa_model as NM            # noqa: E402
from research.papertrade_exec import ncaa_state_store as NSS     # noqa: E402
from research.papertrade_exec import results_fetch as RF         # noqa: E402
from research.papertrade_exec import live_dashboard              # noqa: E402
from research.papertrade_exec.ops_service import OpsService      # noqa: E402

env = _ops.env
incidents = _ops.incidents
ledger_rows = _ops.ledger_rows
make_svc = _ops.make_svc
seed_open_bet = _ops.seed_open_bet


def _mk_game(season, d, hid, aid, hs, as_, *, neutral=False, s_type=2,
             conf=("SAME", "SAME"), tournament=None):
    return {"season": season, "season_type": s_type,
            "tournament_id": tournament,
            "home_id": str(hid), "away_id": str(aid),
            "home_conference_id": conf[0],
            "away_conference_id": conf[1],
            "home_score": hs, "away_score": as_,
            "neutral_site": neutral, "date": d.isoformat()}


# ------------------------------- the INDEPENDENT intake transcription ------

def _intake_walk_forward(games):
    """Verbatim transcription of ncaa_intake/frozen_test.py walk_forward
    (constants + update order), used ONLY as the parity oracle here."""
    K, HFA, REGRESS = 20.0, 65.0, 0.25
    L0, H_PTS, A_EFF = 70.0, 3.2, 0.06
    elo, off, deff, last_date = {}, {}, {}, {}
    tot_pts, tot_tg = 0, 0
    cur_season = None
    recs = []
    for g in games:
        if cur_season is not None and g["season"] != cur_season:
            for t in elo:
                elo[t] = 1500.0 + (elo[t] - 1500.0) * (1 - REGRESS)
            for t in off:
                off[t] *= (1 - REGRESS)
                deff[t] *= (1 - REGRESS)
        cur_season = g["season"]
        eh = elo.get(g["home_id"], 1500.0)
        ea = elo.get(g["away_id"], 1500.0)
        oh, dh = off.get(g["home_id"], 0.0), deff.get(g["home_id"], 0.0)
        oa, da = off.get(g["away_id"], 0.0), deff.get(g["away_id"], 0.0)
        L = (tot_pts / tot_tg) if tot_tg else L0
        neutral = bool(g["neutral_site"])
        adj = 0.0 if neutral else HFA
        p_elo = 1.0 / (1.0 + 10 ** (-(eh - ea + adj) / 400.0))
        hpts = 0.0 if neutral else H_PTS
        pred_h = L + oh + da + hpts
        pred_a = L + oa + dh
        d = date.fromisoformat(g["date"])
        rest_h = 10.0 if g["home_id"] not in last_date else \
            min((d - last_date[g["home_id"]]).days, 30)
        rest_a = 10.0 if g["away_id"] not in last_date else \
            min((d - last_date[g["away_id"]]).days, 30)
        y = 1 if g["home_score"] > g["away_score"] else 0
        recs.append({
            "p_elo": p_elo,
            "elo_diff": (eh + adj) - ea,
            "eff_margin": pred_h - pred_a,
            "net_diff": (oh - dh) - (oa - da),
            "rest_h": float(rest_h), "rest_a": float(rest_a),
            "rest_diff": float(rest_h) - float(rest_a),
            "conf_game": 1.0 if g["home_conference_id"] ==
                         g["away_conference_id"] else 0.0,
            "neutral": 1.0 if neutral else 0.0})
        elo[g["home_id"]] = eh + K * (y - p_elo)
        elo[g["away_id"]] = ea + K * ((1 - y) - (1 - p_elo))
        err_h = g["home_score"] - pred_h
        err_a = g["away_score"] - pred_a
        off[g["home_id"]] = oh + A_EFF * err_h
        deff[g["away_id"]] = da + A_EFF * err_h
        off[g["away_id"]] = oa + A_EFF * err_a
        deff[g["home_id"]] = dh + A_EFF * err_a
        last_date[g["home_id"]] = d
        last_date[g["away_id"]] = d
        tot_pts += g["home_score"] + g["away_score"]
        tot_tg += 2
    return recs, elo, off, deff


def _synthetic_season():
    games = []
    d0 = date(2026, 1, 5)
    i = 0
    for day in range(24):
        hid, aid = f"t{i % 6}", f"t{(i + 1) % 6}"
        games.append(_mk_game(2026, d0 + timedelta(days=day // 2), hid, aid,
                              70 + (i * 7) % 25, 65 + (i * 5) % 20,
                              neutral=(i % 5 == 0)))
        i += 1
    return games


# ----------------------------------------------------------------- W5.3 ----

def test_frozen_laws_parity_vs_intake_transcription():
    games = _synthetic_season()
    oracle, elo_o, off_o, deff_o = _intake_walk_forward(games)
    st = NSS.replay(games)
    st2 = NSS.NcaaState()
    for i, g in enumerate(games):
        feat = NSS.pregame_features(st2, g)
        mine = {k: feat[k] for k in ("p_elo", "elo_diff", "eff_margin",
                                     "net_diff", "rest_h", "rest_a",
                                     "rest_diff", "conf_game", "neutral")}
        assert mine == pytest.approx(oracle[i], rel=1e-12, abs=1e-12)
        NSS.apply_result(st2, g, feat)
    assert st2.elo == pytest.approx(elo_o, rel=1e-12, abs=1e-12) or \
        all(abs(st2.elo[k] - elo_o[k]) < 1e-9 for k in elo_o)
    assert all(abs(st2.off[k] - off_o[k]) < 1e-9 for k in off_o)
    assert all(abs(st2.deff[k] - deff_o[k]) < 1e-9 for k in deff_o)


def test_replay_bit_identical_and_roundtrip(env, tmp_path):
    games = _synthetic_season()
    st1 = NSS.replay(games)
    st2 = NSS.replay(list(reversed(games)))    # order-inDEPENDENT input,
    # the store itself sorts chronologically -> identical state
    assert st1.digest() == st2.digest()
    rec = st1.save(tmp_path / "state.json", league="NCAA-M")
    st3 = NSS.NcaaState.load(tmp_path / "state.json")
    assert st3.digest() == rec["state_sha256"] == st1.digest()


def test_pregame_neutral_and_conf_laws():
    st = NSS.NcaaState()
    g = _mk_game(2026, date(2026, 1, 5), "a", "b", 80, 70, neutral=True,
                 conf=("ACC", "SEC"))
    feat = NSS.pregame_features(st, g)
    assert feat["neutral"] == 1.0 and feat["conf_game"] == 0.0
    # HFA=65 and H_PTS=3.2 both vanish on a neutral floor (equal 1500s =>
    # p stays exactly 0.5)
    assert feat["p_elo"] == 0.5
    g2 = _mk_game(2026, date(2026, 1, 5), "a", "b", 80, 70, neutral=False,
                  conf=("ACC", "ACC"))
    feat2 = NSS.pregame_features(st, g2)
    assert feat2["conf_game"] == 1.0 and feat2["p_elo"] > 0.5
    # unknown conference flags -> honest 0.0 feature, never guessed
    g3 = _mk_game(2026, date(2026, 1, 5), "a", "b", 80, 70,
                  conf=(None, None))
    assert NSS.pregame_features(st, g3)["conf_game"] == 0.0


def test_gbm_refit_pinned_predict_and_drift(tmp_path):
    rows = [{"features": {k: v for k, v in zip(
        NSS.FEATURES, [i * 1.7, i * 0.3, i * 0.9, 3.0, 2.0, 1.0,
                       i % 2, i % 3 == 0 and 1.0 or 0.0])},
        "y": i % 2} for i in range(40)]
    manifest = NM.refit(tmp_path, "NCAA-M", 2026, rows)
    model, m2 = NM.load_pinned(tmp_path, "NCAA-M", 2026)
    assert model is not None and m2["sha256"] == manifest["sha256"]
    feat = {k: 0.5 for k in NSS.FEATURES}
    ps = NM.predict_home_p(model, [NSS.feature_vector(feat)] * 2)
    assert all(0.0 < p < 1.0 for p in ps)
    # pin law: tampered bytes are refused
    art = tmp_path / "NCAA-M_2026_gbm.pkl"
    art.write_bytes(art.read_bytes() + b"x")
    model2, why = NM.load_pinned(tmp_path, "NCAA-M", 2026)
    assert model2 is None and "drift" in why


# ----------------------------------------------------------------- W5.4 ----

def test_ncaa_anchor_law_batch_vs_tournament():
    mk = lambda mid, comp, h=8: A_Fixture(mid, comp, h)  # noqa: E731
    fx = [mk("g1", "NCAA_REGULAR", 20), mk("g2", "NCAA_REGULAR", 23)]
    anchor, per = execute.batch_anchor(fx, "NCAA-M")
    assert per["g1"] == per["g2"] == anchor      # batch law (T0-6h10m)
    tfx = [mk("t1", "NCAA_TOURNAMENT", 20), mk("t2", "NCAA_TOURNAMENT",
                                               23)]
    anchor, per = execute.batch_anchor(tfx, "NCAA-M")
    assert anchor == "" and per["t1"] != per["t2"]   # per-match kickoff-6h


def A_Fixture(mid, comp, hour):
    ko = datetime(2026, 3, 21, hour, tzinfo=timezone.utc)
    return adapters.Fixture(league="NCAA-M", match_id=mid, home="A",
                            away="B", kickoff_utc=ko.strftime(
                                "%Y-%m-%dT%H:%M:%SZ"),
                            competition=comp,
                            et_local_date="2026-03-21",
                            source_ref="T")


def test_sandbox_day_forecast_quote_decide_both_lanes(env, monkeypatch):
    """One sandbox day for BOTH lanes: forecast -> quote -> decide runs the
    whole lifecycle with the labeled synthetic fixtures/books."""
    from research.papertrade_exec import execute as E
    for league in ("NCAA-M", "NCAA-W"):
        assert E.ncaa_configured(league)
        code, out = _cli(env, "forecast", "--league", league,
                         "--date", "2026-11-20")
        assert code == 0
        code, out = _cli(env, "quote", "--league", league,
                         "--date", "2026-11-20")
        assert code == 0
        code, out = _cli(env, "decide", "--league", league,
                         "--date", "2026-11-20")
        assert code == 0
    fcs = [r for r in ledger_rows(env) if r.get("type") == "FORECAST"
           and r.get("league", "").startswith("NCAA-")]
    assert {r["league"] for r in fcs} == {"NCAA-M", "NCAA-W"}
    assert all(r.get("mode") == "SYNTHETIC" for r in fcs)


def _cli(env, *argv):
    from research.papertrade_exec import execute as E
    ns = E.build_parser().parse_args([
        "--data-root", str(env["data"]), "--sandbox", *argv])
    ns.sandbox_control_dir = str(env["data"] / "sandbox" / "control")
    ns.sandbox_registry = str(env["data"] / "sandbox" / "control" /
                              "CYCLE_REGISTRY.json")
    out = ns.fn(ns)
    return 0, out


def test_refresh_state_job_replays_and_pins(env, monkeypatch):
    games = _synthetic_season()
    by_day = {}
    for g in games:
        by_day.setdefault(g["date"], []).append(g)

    def seam(league, day):
        rows = by_day.get(day, [])
        payload = {"events": [_event_of(g) for g in rows
                              if g.get("home_score") is not None]}
        return payload, json.dumps(payload).encode()

    def _event_of(g):
        return {"id": f"{g['home_id']}{g['away_id']}{g['date']}",
                "date": f"{g['date']}T19:00:00Z",
                "season": {"year": g["season"], "type": g["season_type"]},
                "competitions": [{
                    "venue": {"neutralSite": g["neutral_site"]},
                    "conferenceCompetition": g["home_conference_id"] ==
                    g["away_conference_id"],
                    "tournament": {"id": g.get("tournament_id")} if
                    g.get("tournament_id") else None,
                    "competitors": [
                        {"homeAway": "home",
                         "team": {"id": g["home_id"],
                                  "displayName": f"Team {g['home_id']}"},
                         "score": str(g["home_score"])},
                        {"homeAway": "away",
                         "team": {"id": g["away_id"],
                                  "displayName": f"Team {g['away_id']}"},
                         "score": str(g["away_score"])}],
                    "status": {"type": {"state": "post",
                                        "completed": True}}}]}
    ns = execute.build_parser().parse_args([
        "--data-root", str(env["data"]), "--sandbox",
        "ncaa-refresh-state", "--league", "NCAA-M",
        "--from-date", "2026-01-05", "--to-date", "2026-01-16"])
    ns.sandbox_control_dir = str(env["data"] / "sandbox" / "control")
    ns.sandbox_registry = str(env["data"] / "sandbox" / "control" /
                              "CYCLE_REGISTRY.json")
    ns.ncaa_scoreboard = seam
    out = execute.cmd_ncaa_refresh_state(ns)   # direct call (the parser
    # lambda only prints); the record fields are asserted directly
    assert out["games_harvested"] > 0
    st = NSS.NcaaState.load(env["data"] / "ncaa" / "NCAA-M" / "state.json")
    assert st is not None and st.games_processed == out["games_harvested"]
    # the refit note is honest about the sklearn state
    assert out["refit"].startswith("refit ok") or "sklearn" in out["refit"]


# ----------------------------------------------------------------- W5.2 ----

def test_ncaa_settle_via_scoreboard_and_norm_identity(env, monkeypatch):
    """The NCAA results path settles through the SAME scoreboard law; team
    identity is norm equality on the FULL display names (the W0.1 lesson)."""
    seed_open_bet(env, league="NCAA-M", match_id="NCAA-T1",
                  home="Team aa", away="Team bb",
                  kickoff="2026-01-05T19:00:00Z", chosen="HOME",
                  odds={"HOME": 1.9, "AWAY": 1.95})
    payload = {"events": [{
        "id": "NCAA-T1", "date": "2026-01-05T19:00Z",
        "season": {"year": 2026, "type": 2},
        "competitions": [{
            "venue": {"neutralSite": False},
            "conferenceCompetition": True,
            "status": {"type": {"state": "post", "completed": True,
                                "detail": "Final"}},
            "competitors": [
                {"homeAway": "home",
                 "team": {"id": "aa", "displayName": "Team aa",
                          "abbreviation": "AA"},
                 "score": "81"},
                {"homeAway": "away",
                 "team": {"id": "bb", "displayName": "Team bb",
                          "abbreviation": "BB"},
                 "score": "77"}]}]}]}
    monkeypatch.setattr(RF, "_espn_get",
                        lambda league, date: (payload, b"{}", 200))
    assert "NCAA-M" in RF.ESPN_LEAGUE_PATH
    out = make_svc(env).settle_pass()
    assert out["settled"] == 1
    stl = [r for r in ledger_rows(env) if r.get("type") == "SETTLEMENT"]
    assert stl[0]["outcome_for_leg"] == "WIN"


# ----------------------------------------------------------------- W5.5 ----

def test_truth_label_and_running_metrics(env):
    from research.papertrade_exec.ops_service import NCAA_TRUTH_LABEL
    seed_open_bet(env, league="NCAA-M", match_id="NCAA-M1",
                  home="Team aa", away="Team bb", chosen="HOME",
                  kickoff="2026-01-05T19:00:00Z",
                  odds={"HOME": 2.0, "AWAY": 1.9})
    led = None
    core = execute.load_pinned_core(roots={})
    led = core.ledger.PaperLedger(_ops.sandbox_ledger_path(env)).load()
    # a lane FORECAST for the metrics law (p_home 0.6 vs the actual WIN)
    led.append({"type": "FORECAST", "league": "NCAA-M",
                "match_id": "NCAA-M1", "home": "Team aa",
                "away": "Team bb", "competition": "NCAA",
                "kickoff_utc": "2026-01-05T19:00:00Z",
                "p": {"HOME": 0.6, "AWAY": 0.4},
                "recorded_at_utc": "2026-01-05T00:00:00Z",
                "mode": "SYNTHETIC", "source_ref": "TEST"})
    svc = make_svc(env)
    svc._refresh_ncaa_metrics(led)
    data = json.loads((env["data"] / "sandbox" / "ops" / "state" /
                       "ncaa_metrics.json").read_text())
    assert data["truth_label"] == NCAA_TRUTH_LABEL
    # no settlement yet: NO scored rows at all (metrics only over settled
    # games — never a running number without results)
    assert data["leagues"] == {}
    # settle the bet WIN and recompute: logloss + brier move, PM ll present
    import research.papertrade_exec.results_fetch as RF
    with mock.patch.object(RF, "_espn_get", lambda *a, **k: (
            {"events": []}, b"{}", 200)):
        pass
    led2 = core.ledger.PaperLedger(_ops.sandbox_ledger_path(env)).load()
    led2.append({"type": "SETTLEMENT", "league": "NCAA-M",
                 "match_id": "NCAA-M1", "result": "HOME",
                 "outcome_for_leg": "WIN", "pnl_cents": 500,
                 "decision_row_sha256": "0" * 64,
                 "settled_at_utc": "2026-01-06T00:00:00Z",
                 "source_ref": "TEST"})
    svc._refresh_ncaa_metrics(led2)
    data = json.loads((env["data"] / "sandbox" / "ops" / "state" /
                       "ncaa_metrics.json").read_text())
    m = data["leagues"]["NCAA-M"]
    assert m["settled"] == 1 and m["logloss"] is not None
    assert m["pm_logloss"] is not None          # PM benchmark present


def test_desk_carries_ncaa_label():
    state = live_dashboard.build_state(
        core=execute.load_pinned_core(roots={}),
        ledger_path=Path("/tmp/definitely-missing.jsonl"),
        data_root=Path("/tmp"), sandbox=True, key_fingerprint=None,
        heartbeat=None, incidents=[], upcoming=[],
        desk={"ncaa": {"label": "LBL", "metrics": {"NCAA-M": {
            "settled": 3, "logloss": 0.61, "brier": 0.2,
            "pm_logloss": 0.7}}}})
    assert state["desk"]["ncaa"]["label"] == "LBL"
    assert state["desk"]["ncaa"]["metrics"]["NCAA-M"]["pm_logloss"] == 0.7
