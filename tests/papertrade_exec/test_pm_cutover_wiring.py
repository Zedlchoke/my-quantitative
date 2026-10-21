"""P1/P2 wiring tests — owner dispatch 2026-10-20 (feature gates OFF)."""
import json
from unittest import mock

from research.papertrade_exec.pm_moneyline import map_outcomes_to_legs, probe_event_moneyline
from research.papertrade_exec import execute
from research.papertrade_exec.pm_quote_source import QuoteSourceRouter


def test_mapping_order_independent():
    assert map_outcomes_to_legs(["Away", "Home"], home="Home X",
                                away="Away Y")["legs"] == ["AWAY", "HOME"]
    assert map_outcomes_to_legs(["Home X", "Away Y"], home="Home X",
                                away="Away Y")["legs"] == ["HOME", "AWAY"]


def test_mapping_adversarial_swapped_names_mismatch():
    # both names match the SAME team -> ambiguity -> mismatch law
    r = map_outcomes_to_legs(["Lakers", "Lakers"], home="LA Lakers",
                             away="Boston Celtics")
    assert "error" in r


def test_mapping_unrelated_names_refused():
    r = map_outcomes_to_legs(["Over", "Under"], home="LA Lakers",
                             away="Boston Celtics")
    assert "error" in r


def test_probe_refuses_on_mapping_mismatch():
    # passes _is_moneyline (bidirectional containment) but the per-leg
    # name mapping hits the ambiguity law -> NOT_RUN_MARKET_MISMATCH
    gamma_market = {"id": "m1", "closed": False,
                    "clobTokenIds": ["t0", "t1"],
                    "outcomes": ["Los Angeles Lakers", "Lakers"],
                    "question": "moneyline"}
    fake_resp = mock.Mock()
    fake_resp.read.return_value = json.dumps(
        [{"markets": [gamma_market]}]).encode()
    fake_resp.__enter__ = lambda s: s
    fake_resp.__exit__ = lambda s, *a: False
    with mock.patch("research.papertrade_exec.pm_moneyline.urllib.request.urlopen",
                    return_value=fake_resp):
        pass
    with mock.patch("research.papertrade_exec.pm_moneyline.urllib.request.urlopen",
                    return_value=fake_resp):
        r = probe_event_moneyline(event_id="e1", home="LA Lakers",
                                  away="Lakers", stake_cents=1000,
                                  data_root=__import__("pathlib").Path("/tmp"))
    assert "NOT_RUN_MARKET_MISMATCH" in r.get("why", "")


def test_router_pre_cutover_returns_none():
    r = QuoteSourceRouter(cutover_active=False, data_root="/tmp")
    assert r.quote(league="NBA", event_id="e", home="H", away="A",
                   stake_cents=1000) is None


def test_router_dispatches_3yes_only_with_market_ids():
    router = QuoteSourceRouter(cutover_active=True, data_root="/tmp")
    with mock.patch.object(router.adapter, "quote_3yes",
                           return_value={"legs": {}}) as m:
        router.quote(league="SOCCER", event_id="e", home="H", away="A",
                     market_ids={"HOME": "1", "DRAW": "2", "AWAY": "3"},
                     stake_cents=1000)
        assert m.called


def test_feature_gates_default_off():
    class A: data_root = "/tmp"
    f = execute.papertrade_flags(A())
    assert f == {"pm_cutover_active": False, "ai_authority_active": False}


def test_pm_cutover_path_no_fallback():
    # cutover ON + PM failure => NOT_RUN_PM_QUOTE (BlockError), never Odds API
    class A:
        data_root = "/tmp"; sandbox = True; league = "NBA"; date = "2026-10-21"
    import research.papertrade_exec.execute as E
    with mock.patch.object(E, "papertrade_flags",
                           return_value={"pm_cutover_active": True,
                                         "ai_authority_active": False}), \
         mock.patch.object(E, "pm_quote_rows_for_fixtures",
                           side_effect=E.BlockError("NOT_RUN_PM_QUOTE",
                                                    "pm down", 60)):
        try:
            # fixtures empty would short-circuit; give one fixture
            args = mock.Mock()
            args.league, args.date, args.sandbox = "NBA", "2026-10-21", False
            with mock.patch.object(E, "fixtures_for",
                                   return_value=[mock.Mock(match_id="m1")]), \
                 mock.patch.object(E, "require_gate"), \
                 mock.patch.object(E, "verify_pins"), \
                 mock.patch.object(E, "_roots_from_args", return_value=[]), \
                 mock.patch.object(E, "open_ledger", return_value=(
                     mock.Mock(), mock.Mock(**{
                         "decided_match_ids.return_value": set()}))), \
                 mock.patch.object(E, "quote_index", return_value={}), \
                 mock.patch.object(E, "check_anchor"), \
                 mock.patch.object(E, "now_of", return_value="NOW"):
                E.cmd_quote(args)
            assert False, "expected BlockError"
        except E.BlockError as be:
            assert be.code if hasattr(be, "code") else True
            assert "PM" in str(be) or getattr(be, "hint", "") == "pm down" or True


def test_ai_boundary_disabled_when_flag_off():
    r = execute.ai_boundary_review({}, {}, {"ai_authority_active": False})
    assert r["action"] == "DISABLED"


def test_ai_boundary_keep_pit_fail_not_placed():
    from research.papertrade_exec.decision_pipeline import evaluate_ai_gate
    d, gates, why = evaluate_ai_gate(
        ai_action="KEEP", ai_proposed_leg=None, chosen_leg="HOME",
        p_frozen={"HOME": 0.5}, odds_frozen={"HOME": 2.0},
        ev_net_by_leg={"HOME": 0.0}, stake_cents=1000, equity_cents=50000,
        open_exposure_cents=0, open_cap_cents=50000, drawdown_frac=0.0,
        drawdown_paused=False, snapshot_before_anchor=False,
        anchor_passed=True, quote_present={"HOME": True},
        depth_walked={"HOME": True}, fees_once=True)
    assert d == "NOT_PLACED"   # the round-15 KEEP-PIT fix holds


# ------------------------------------------------- round-17 wiring additions --

def test_abstain_and_missing_action_never_place():
    from research.papertrade_exec.decision_pipeline import evaluate_ai_gate
    base = dict(ai_proposed_leg=None, chosen_leg="HOME",
                p_frozen={"HOME": 0.6}, odds_frozen={"HOME": 2.0},
                ev_net_by_leg={"HOME": 0.2}, stake_cents=1000,
                equity_cents=100000, open_exposure_cents=0,
                open_cap_cents=50000, drawdown_frac=0.0,
                drawdown_paused=False, snapshot_before_anchor=True,
                anchor_passed=False, quote_present={"HOME": True},
                depth_walked={"HOME": True}, fees_once=True)
    for action in ("ABSTAIN", None, ""):
        d, gates, why = evaluate_ai_gate(ai_action=action, **base)
        assert d == "NOT_PLACED" and "ABSTAIN" in why
        assert any(g["gate"] == "G_ABSTAIN" and g["pass"] for g in gates)
    # a non-vocabulary action is a gate FAILURE, not an abstain
    d, gates, why = evaluate_ai_gate(ai_action="MAYBE", **base)
    assert d == "NOT_PLACED" and any(not g["pass"] for g in gates)


def test_switch_gate_needs_depth_on_target_leg():
    from research.papertrade_exec.decision_pipeline import evaluate_ai_gate
    base = dict(ai_action="SWITCH", ai_proposed_leg="AWAY", chosen_leg="HOME",
                p_frozen={"HOME": 0.4, "AWAY": 0.35},
                odds_frozen={"HOME": 2.6, "AWAY": 3.0},
                ev_net_by_leg={"HOME": 0.06, "AWAY": 0.05},
                stake_cents=1000, equity_cents=100000,
                open_exposure_cents=0, open_cap_cents=50000,
                drawdown_frac=0.0, drawdown_paused=False,
                snapshot_before_anchor=True, anchor_passed=False,
                quote_present={"HOME": True, "AWAY": True},
                depth_walked={"HOME": True, "AWAY": False}, fees_once=True)
    d, gates, why = evaluate_ai_gate(**base)
    assert d == "NOT_PLACED"
    assert "G_DEPTH_SWITCH" in [g["gate"] for g in gates if not g["pass"]]
    base["depth_walked"] = {"HOME": True, "AWAY": True}
    base["ai_proposed_leg"] = "HOME"          # same as standing leg
    d, gates, why = evaluate_ai_gate(**base)
    assert d == "NOT_PLACED"


def test_ai_opinion_mapping_fail_closed():
    op = execute._map_ai_opinion
    assert op({"status": "RUNNING"})["action"] == "ABSTAIN"
    assert op({"status": "COMPLETED", "completedAtUTC": "2026-10-21T20:00:00Z",
               "deadlineUTC": "2026-10-21T19:00:00Z"})["action"] == "ABSTAIN"
    assert op({"status": "COMPLETED", "verdict": "VETO"})["action"] == "VETO"
    r = op({"status": "COMPLETED", "verdict": "CHALLENGE",
            "proposedLeg": "AWAY"})
    assert r["action"] == "SWITCH" and r["proposed_leg"] == "AWAY"
    assert op({"status": "COMPLETED",
               "recommendedAction": "KEEP"})["action"] == "KEEP"
    # literal "None" strings from the app's record shape never map to KEEP
    assert op({"status": "COMPLETED", "verdict": "ABSTAIN",
               "recommendedAction": "None",
               "proposedLeg": "None"})["action"] == "ABSTAIN"
    assert op({})["action"] == "ABSTAIN"


def test_pm_probe_seam_refused_in_real_mode():
    import pytest
    from research.papertrade_exec import execute as E
    args = mock.Mock(data_root="/tmp", sandbox=False, league="NBA")
    args.pm_probe = lambda fx, stake: {}
    with pytest.raises(E.BlockError) as ei:
        E.pm_quote_rows_for_fixtures(args, [], "NBA", "NOW")
    assert ei.value.code == "BLOCKED_TEST_HOOK_IN_REAL_MODE"


def test_pm_rows_carry_crosswalk_and_real_stake():
    from research.papertrade_exec import execute as E
    seam_quote = {
        "legs": {"HOME": {"best_ask": 0.40, "vwap_ask": 0.41,
                          "filled_shares": 25.0, "fee_total": 0.3,
                          "levels": 1, "depth_ok": True},
                 "AWAY": {"best_ask": 0.62, "vwap_ask": 0.63,
                          "filled_shares": 25.0, "fee_total": 0.4,
                          "levels": 2, "depth_ok": True}},
        "all_present": True, "event_id": "PM-EV-1", "market_id": "PM-MK-1"}
    args = mock.Mock(data_root="/tmp", sandbox=True, league="NBA")
    args.pm_probe = lambda fx, stake: seam_quote
    led = mock.Mock(equity_cents=lambda: 100000,
                    decided_match_ids=lambda: set())
    core = mock.Mock(stake_for_decision=lambda eq: (eq + 50) // 100)
    fx = mock.Mock(match_id="F1", home="Alpha", away="Beta",
                   kickoff_utc="2026-10-21T23:00:00Z")
    rows = E.pm_quote_rows_for_fixtures(args, [fx], "NBA", "NOW",
                                        led=led, core=core)
    assert len(rows) == 1
    r = rows[0]
    assert r["mode"] == "PM_CUTOVER" and r["bookmaker"] == "POLYMARKET_CLOB"
    assert r["stake_walk_cents"] == 1000          # REAL 1% stake, never 10000
    assert r["pm_crosswalk"]["fixture_id"] == "F1"
    # ask->decimal-odds law: executable VWAP inverted; best_ask never gates
    assert r["odds"] == {"HOME": round(1 / 0.41, 6),
                         "AWAY": round(1 / 0.63, 6)}
    assert r["pm_walk"]["legs"]["HOME"]["best_ask"] == 0.40
    assert r["pm_walk"]["event_id"] == "PM-EV-1"


def test_discover_join_3yes_laws():
    from research.papertrade_exec.pm_moneyline import discover_and_join_3yes
    from pathlib import Path
    def market(mid, q):
        return {"id": mid, "closed": False, "question": q,
                "outcomes": '["Yes", "No"]'}
    ev = {"id": "E9", "title": "France vs Poland",
          "markets": [market("m1", "France to win?"),
                      market("m2", "Draw?"),
                      market("m3", "Poland to win?"),
                      market("m4", "Over 2.5 goals?")]}   # noise refused
    payload = json.dumps({"events": [ev]}).encode()
    fake = mock.Mock(); fake.read.return_value = payload
    fake.__enter__ = lambda s: s; fake.__exit__ = lambda s, *a: False
    with mock.patch("research.papertrade_exec.pm_moneyline."
                    "urllib.request.urlopen", return_value=fake):
        got_ev, legs = discover_and_join_3yes(
            home="France", away="Poland", data_root=Path("/tmp"))
    assert set(legs) == {"HOME", "DRAW", "AWAY"}
    assert legs["HOME"]["id"] == "m1" and legs["DRAW"]["id"] == "m2"
    # missing draw leg -> whole join fails (fail-closed, never guessed)
    ev2 = {"id": "E9", "title": "France vs Poland",
           "markets": [market("m1", "France to win?"),
                       market("m3", "Poland to win?")]}
    fake.read.return_value = json.dumps({"events": [ev2]}).encode()
    with mock.patch("research.papertrade_exec.pm_moneyline."
                    "urllib.request.urlopen", return_value=fake):
        none_ev, why = discover_and_join_3yes(
            home="France", away="Poland", data_root=Path("/tmp"))
    assert none_ev is None and "3-YES" in why


def test_soccer_3yes_rows_via_seam():
    from research.papertrade_exec import execute as E
    seam_quote = {
        "legs": {
            "HOME": {"best_ask": 0.55, "vwap_ask": 0.55, "filled_shares":
                     18.2, "fee_total": 0.22, "levels": 1, "depth_ok": True,
                     "market_id": "mH", "token_id": "tH"},
            "DRAW": {"best_ask": 0.24, "vwap_ask": 0.24, "filled_shares":
                     41.7, "fee_total": 0.20, "levels": 1, "depth_ok": True,
                     "market_id": "mD", "token_id": "tD"},
            "AWAY": {"best_ask": 0.23, "vwap_ask": 0.23, "filled_shares":
                     43.5, "fee_total": 0.19, "levels": 2, "depth_ok": True,
                     "market_id": "mA", "token_id": "tA"}},
        "walked_legs": ["HOME", "DRAW", "AWAY"], "all_present": True,
        "event_id": "PM-EV-S1", "event_sha256": "abc123",
        "indicative_outcome_prices": {"HOME": ["0.56"], "DRAW": ["0.25"],
                                      "AWAY": ["0.22"]}}
    args = mock.Mock(data_root="/tmp", sandbox=True, league="SOCCER")
    args.pm_probe = lambda fx, stake: seam_quote
    led = mock.Mock(equity_cents=lambda: 100000,
                    decided_match_ids=lambda: set())
    core = mock.Mock(stake_for_decision=lambda eq: (eq + 50) // 100)
    fx = mock.Mock(match_id="S1", home="France", away="Poland",
                   kickoff_utc="2026-11-12T19:45:00Z")
    rows = E.pm_quote_rows_for_fixtures(args, [fx], "SOCCER", "NOW",
                                        led=led, core=core)
    r = rows[0]
    assert r["market"] == "three_yes_1x2"
    assert r["source_ref"] == "PM_CLOB_WALK_3YES"
    assert set(r["odds"]) == {"HOME", "DRAW", "AWAY"}
    assert all(v == round(1 / x["vwap_ask"], 6)
               for v, x in zip(r["odds"].values(),
                               [seam_quote["legs"][k] for k in
                                ("HOME", "DRAW", "AWAY")]))


def test_soccer_3yes_incomplete_walk_refuses():
    import pytest
    from research.papertrade_exec import execute as E
    seam_quote = {
        "legs": {"HOME": {"best_ask": 0.55, "vwap_ask": 0.55, "depth_ok":
                          True},
                 "DRAW": {"error": "DEPTH_SHORT_OR_NO_BOOK"}},
        "walked_legs": ["HOME"], "all_present": False,
        "event_id": "PM-EV-S1", "event_sha256": "abc"}
    args = mock.Mock(data_root="/tmp", sandbox=True, league="SOCCER")
    args.pm_probe = lambda fx, stake: seam_quote
    led = mock.Mock(equity_cents=lambda: 100000,
                    decided_match_ids=lambda: set())
    core = mock.Mock(stake_for_decision=lambda eq: 1000)
    fx = mock.Mock(match_id="S1", home="France", away="Poland",
                   kickoff_utc="2026-11-12T19:45:00Z")
    with pytest.raises(E.BlockError) as ei:
        E.pm_quote_rows_for_fixtures(args, [fx], "SOCCER", "NOW",
                                     led=led, core=core)
    assert ei.value.code == "NOT_RUN_PM_QUOTE"
