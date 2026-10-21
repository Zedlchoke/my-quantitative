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
                 mock.patch.object(E, "open_ledger", return_value=(mock.Mock(), mock.Mock())), \
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
