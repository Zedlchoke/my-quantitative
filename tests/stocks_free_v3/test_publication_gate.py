"""Trial publication gate: zero-event/zero-position results are refused (A2).

Frozen semantics (PLAN_stocks.md section 9 A2, deliverable 8), pinned here:

* observed-versus-published: the compute is RECORDED (observed +1) before
  publication is attempted — including when publication is then REFUSED;
* a refused result never enters published_keys and never increments the
  published counter; the refusal is recorded in the append-only entries;
* replays of an already-published key increment NEITHER counter (zero delta);
* the inherited counters behave exactly like the V2 harness TrialLedger
  (single implementation: GatedTrialLedger subclasses it unchanged).

Hand fixture counts (from the A4/A5 books in test_factory_valuation):
A4 book -> n_fill_events 2, n_held_positions 2 (fills hold 1 then 2 ETFs).
All-cash book (targets {CASH:1.0}) -> n_held_positions 0 -> refused.
Empty book -> n_fill_events 0 -> refused.
"""
import pytest

from research.assets.stocks.factory import GatedTrialLedger, publication_metrics
from research.stocks_free_v2.harness import TrialLedger

from tests.stocks_free_v3.test_factory_valuation import _entries_a4, _entries_a5


def test_publication_metrics_hand_counts():
    assert publication_metrics(_entries_a4()) == {"n_fill_events": 2,
                                                  "n_held_positions": 2}
    assert publication_metrics(_entries_a5()) == {"n_fill_events": 2,
                                                  "n_held_positions": 1}
    assert publication_metrics([]) == {"n_fill_events": 0, "n_held_positions": 0}
    # all-cash book: a decision fill that never holds an ETF
    all_cash = [{"entry_type": "FILL", "fill_date": "2020-01-06",
                 "targets": {"CASH": 1.0}, "cash_weight": 1.0}]
    assert publication_metrics(all_cash) == {"n_fill_events": 1,
                                             "n_held_positions": 0}
    # FORCE_FLAT alone is bookkeeping, not a decision event
    assert publication_metrics(_entries_a4()[2:]) == {"n_fill_events": 0,
                                                      "n_held_positions": 0}


def test_valid_result_publishes_once_and_replays_zero_delta():
    ledger = GatedTrialLedger()
    key = "US_ETF_CASH|V3|ARM_X|synthetic"
    ledger.compute_recorded(key)
    assert ledger.observed == 1
    assert ledger.publish_result(key, {"pnl": 0.1},
                                 **publication_metrics(_entries_a4())) is True
    assert len(ledger.published_keys) == 1 and ledger.observed == 1
    # replay: neither counter moves
    assert ledger.publish_result(key, {"pnl": 0.1},
                                 **publication_metrics(_entries_a4())) is False
    assert ledger.observed == 1 and len(ledger.published_keys) == 1
    events = [e["event"] for e in ledger.entries if "event" in e]
    assert events[-1] == "REPLAY_ZERO_DELTA"


def test_zero_event_result_refused_but_compute_still_recorded():
    ledger = GatedTrialLedger()
    key = "US_ETF_CASH|V3|ARM_EMPTY|synthetic"
    ledger.compute_recorded(key)                      # observed recorded FIRST
    ok = ledger.publish_result(key, {"pnl": 0.0}, n_fill_events=0,
                               n_held_positions=0)
    assert ok is False
    assert ledger.observed == 1                       # observed delta preserved
    assert key not in ledger.published_keys           # never published
    assert len(ledger.published_keys) == 0
    assert ledger.refusals == [{"key": key,
                                "reasons": ["ZERO_FILL_EVENTS",
                                            "ZERO_HELD_POSITIONS"]}]
    refusal = [e for e in ledger.entries if e["event"] == "PUBLICATION_REFUSED_ZERO_RESULT"]
    assert len(refusal) == 1 and refusal[0]["key"] == key


def test_zero_position_result_refused():
    ledger = GatedTrialLedger()
    key = "US_ETF_CASH|V3|ARM_ALLCASH|synthetic"
    ledger.compute_recorded(key)
    all_cash = [{"entry_type": "FILL", "fill_date": "2020-01-06",
                 "targets": {"CASH": 1.0}, "cash_weight": 1.0}]
    ok = ledger.publish_result(key, {"pnl": 0.0}, **publication_metrics(all_cash))
    assert ok is False
    assert ledger.observed == 1 and ledger.published_keys == set()
    assert ledger.refusals[0]["reasons"] == ["ZERO_HELD_POSITIONS"]


def test_refused_key_can_be_republished_only_with_a_valid_result():
    """The refused RESULT is dead; a later valid result for the same key publishes."""
    ledger = GatedTrialLedger()
    key = "US_ETF_CASH|V3|ARM_RETRY|synthetic"
    ledger.compute_recorded(key)
    assert ledger.publish_result(key, {"bad": True}, n_fill_events=0,
                                 n_held_positions=0) is False
    assert ledger.publish_result(key, {"good": True}, n_fill_events=3,
                                 n_held_positions=2) is True
    assert ledger.published_keys == {key}
    # ...and a further replay of the now-published key is a zero delta
    assert ledger.publish_result(key, {"good": True}, n_fill_events=3,
                                 n_held_positions=2) is False
    assert ledger.observed == 1


def test_gate_requires_int_counts():
    ledger = GatedTrialLedger()
    with pytest.raises(ValueError, match="int count"):
        ledger.publish_result("k", {}, n_fill_events=1.5, n_held_positions=1)
    with pytest.raises(ValueError, match="int count"):
        ledger.publish_result("k", {}, n_fill_events=True, n_held_positions=1)


def test_inherited_counters_match_v2_trial_ledger():
    """Same op sequence on both ledgers -> identical observed/published state."""
    gated, plain = GatedTrialLedger(), TrialLedger()
    for ledger in (gated, plain):
        ledger.compute_recorded("k1")
        ledger.compute_recorded("k2")
        ledger.publish("k1", {"a": 1})
        ledger.publish("k1", {"a": 1})          # replay
    assert gated.observed == plain.observed == 2
    assert gated.published_keys == plain.published_keys == {"k1"}
    # publication entries carry a digest, not an "event" -- filter to events
    gated_events = [e["event"] for e in gated.entries if "event" in e]
    plain_events = [e["event"] for e in plain.entries if "event" in e]
    assert gated_events == plain_events == [
        "COMPUTE_RECORDED", "COMPUTE_RECORDED", "FIRST_PUBLICATION",
        "REPLAY_ZERO_DELTA"]
