"""V4-P1 A2 -- publication/accounting regression: 8 hand-computed invariants.

Phase V4-P1 (PLAN_stocks_v4.md).  Prior cycles V2/V3 showed these are
result-level hazards, so each invariant below is proven on a TINY SYNTHETIC
fixture whose expected numbers are computed BY HAND and written literally in
comments/assertions -- never derived from the production code.

The eight invariants:

1.  CASH is not a symbol (never in symbols/weights/turnover/concentrations).
2.  Cost is charged exactly once per fill (no sidecar double-charge).
3.  One named turnover convention: sum(|delta weight|) over tradable legs.
4.  Canonical artifact digest == sha256 of the exact artifact bytes.
5.  Append-only correction entries never alter observed/published counters.
6.  Observed increments exactly once; replays increment neither counter.
7.  Zero-position and out-of-contract cells are refused (fail closed).
8.  Simultaneous ledger appends serialize (A1 single-writer contract).

Production modules are NOT modified by this file.  Where an invariant is not
currently enforced by existing code (item 8: the production ledger has no
locking primitive), the frozen contract is encoded as a test-local helper
inside THIS file and proven there -- this is the regression/contract proof
phase, not an implementation phase.

No scored metrics, no data downloads, no network: every fixture is synthetic
accounting arithmetic (the same hand-fixture style as
tests/assets/stocks/test_accounting.py and tests/stocks_free_v3).
"""

from __future__ import annotations

import fcntl
import json
import os
import threading
from datetime import date

import pytest

from research.assets.stocks.accounting import (
    CostBreakdown,
    FillRecord,
    IdentityLedger,
    ObservableEvent,
)
from research.assets.stocks.factory import (
    CASH_SYMBOL,
    GatedTrialLedger,
    assert_drop_one_allowed,
    assert_reconciles,
    etf_leg_turnover,
    fill_cost,
    normalize_entry_targets,
    publication_metrics,
    select_drop_one_symbol,
    value_book,
)
from research.assets.stocks.portfolio import SharedCapitalReplay
from research.assets.stocks.universe import MembershipRecord, MembershipTable
from research.stocks_free_v2.harness import (
    CANONICAL_JSON_KW,
    TrialLedger,
    canonical_json,
    sha256_file,
    sha256_hex,
)

TS = "2026-01-05T15:00:00Z"


# =========================================================================== #
# INVARIANT 1 -- CASH is not a symbol
# =========================================================================== #
def test_p1_01a_cash_never_counts_in_turnover():
    """Hand fixture: CASH deltas are invisible to the turnover sum.

    before = {AAA: 0.5, CASH: 0.5};  after = {AAA: 0.25, CASH: 0.25, BBB: 0.5}
    ETF-leg deltas: |0.25-0.5| + |0.5-0.0| = 0.25 + 0.5 = 0.75
    CASH delta:     |0.25-0.5|      = 0.25   (must NOT be added)
    A naive all-legs sum would give 1.00; the convention gives exactly 0.75.
    All weights are binary-exact, so float arithmetic is exact here.
    """
    before = {"AAA": 0.5, "CASH": 0.5}
    after = {"AAA": 0.25, "CASH": 0.25, "BBB": 0.5}
    observed = etf_leg_turnover(before, after)
    assert observed == 0.75, observed
    assert observed != 1.0  # the double-counting CASH signature must not appear
    # Weights themselves never carry CASH as a tradable leg after normalization.
    targets, cash = normalize_entry_targets(
        {"entry_type": "FILL", "fill_date": "D1", "targets": dict(after)}
    )
    assert set(targets) == {"AAA", "BBB"} and CASH_SYMBOL not in targets
    assert cash == 0.25


def test_p1_01b_cash_leg_must_agree_or_is_honored_fail_closed():
    """An explicit CASH leg inside targets is split out, never a symbol.

    targets {AAA: 0.6, CASH: 0.4}, cash_weight 0.4 -> ({AAA: 0.6}, 0.4).
    Disagreement (CASH 0.5 vs cash_weight 0.4) raises; silence is a defect.
    """
    targets, cash = normalize_entry_targets(
        {"entry_type": "FILL", "fill_date": "D1",
         "targets": {"AAA": 0.6, "CASH": 0.4}, "cash_weight": 0.4}
    )
    assert targets == {"AAA": 0.6} and cash == 0.4
    with pytest.raises(ValueError, match="CASH"):
        normalize_entry_targets(
            {"entry_type": "FILL", "fill_date": "D1",
             "targets": {"AAA": 0.5, "CASH": 0.5}, "cash_weight": 0.4}
        )


def test_p1_01c_cash_excluded_from_symbols_and_held_positions():
    """An A5-style book (explicit CASH leg): CASH contributes nothing and is
    not a symbol.  Hand fixture: sessions D1..D3, AAA 100 -> 110 -> 121
    (+10% per session), fill at D1 into {AAA: 0.5, CASH: 0.5}, cost 100 bps.

    D1: turnover |0.5-0.0| = 0.5; cost = 1.0*0.5*100/1e4 = 0.005;
        equity = 1.0 - 0.005 = 0.995
    D2: r = 110/100 - 1 = +0.10; equity = 0.995*(1 + 0.5*0.10) = 1.04475
        contribution AAA = 0.995*0.5*0.10 = 0.04975
    D3: r = 121/110 - 1 = +0.10; equity = 1.04475*1.05 = 1.0969875
        contribution AAA += 1.04475*0.5*0.10 = 0.0522375 -> 0.1019875
    """
    result = value_book(
        entries=[{"entry_type": "FILL", "fill_date": "D1",
                  "targets": {"AAA": 0.5, "CASH": 0.5}, "cash_weight": 0.5}],
        raw_close={"AAA": {"D1": 100.0, "D2": 110.0, "D3": 121.0}},
        distributions={}, split_factors={},
        sessions=["D1", "D2", "D3"], cost_bps=100.0,
    )
    assert set(result.symbol_contribution) == {"AAA"}   # CASH is not a symbol
    assert CASH_SYMBOL not in result.symbol_contribution
    assert result.total_cost == 0.005
    assert result.equity_curve["D3"] == pytest.approx(1.0969875, rel=1e-12)
    assert_reconciles(result)  # identity still closes with the CASH leg present
    # Held-position counter for the publication gate: CASH is not a position.
    all_cash = [{"entry_type": "FILL", "fill_date": "D1",
                 "targets": {"CASH": 1.0}, "cash_weight": 1.0}]
    assert publication_metrics(all_cash)["n_held_positions"] == 0


def test_p1_01d_drop_one_refuses_cash_as_a_leg():
    """CASH can never be selected or dropped as a tradable leg."""
    weights = {"AAA": 0.5, "CASH": 0.5}
    contribution = {"AAA": 0.2, "CASH": 0.9}  # CASH "contribution" is a decoy
    assert select_drop_one_symbol(contribution, weights) == "AAA"
    with pytest.raises(ValueError, match="CASH is not a tradable leg"):
        assert_drop_one_allowed("CASH", contribution, weights)


# =========================================================================== #
# INVARIANT 2 -- cost charged exactly once per fill
# =========================================================================== #
def test_p1_02a_factory_path_charges_cost_once_per_fill():
    """Hand fixture: AAA 100 -> 110 -> 121, all-in at D1, cost 100 bps.

    D1: turnover = |1.0 - 0.0| = 1.0 (CASH start leg excluded by definition);
        cost = 1.0 * 1.0 * 100 / 10_000 = 0.01; equity = 1.0 - 0.01 = 0.99
        (a double charge would leave 1.0 - 0.02 = 0.98)
    D2: r = +0.10 -> equity = 0.99 * 1.10 = 1.089;  contrib += 0.99*0.10 = 0.099
    D3: r = +0.10 -> equity = 1.089 * 1.10 = 1.1979; contrib += 1.089*0.10
        = 0.1089 -> 0.2079
    total_pnl = 1.1979 - 1.0 = 0.1979; total_cost = 0.01 (once)
    residual = fsum(0.2079, -0.01, -0.1979) = 0
    """
    result = value_book(
        entries=[{"entry_type": "FILL", "fill_date": "D1",
                  "targets": {"AAA": 1.0}, "cash_weight": 0.0}],
        raw_close={"AAA": {"D1": 100.0, "D2": 110.0, "D3": 121.0}},
        distributions={}, split_factors={},
        sessions=["D1", "D2", "D3"], cost_bps=100.0,
    )
    # hand-computed equity curve, literally
    assert result.equity_curve["D1"] == pytest.approx(0.99, rel=1e-12)
    assert result.equity_curve["D2"] == pytest.approx(1.089, rel=1e-12)
    assert result.equity_curve["D3"] == pytest.approx(1.1979, rel=1e-12)
    # exactly ONE charge: equity reflects c once and the accumulator says c once
    assert abs(result.equity_curve["D1"] - 0.98) > 1e-3  # double-charge signature
    assert result.total_cost == 0.01
    assert result.fill_costs == [("D1", 1.0, 0.01)]
    assert result.symbol_contribution["AAA"] == pytest.approx(0.2079, rel=1e-12)
    assert result.total_pnl == pytest.approx(0.1979, rel=1e-12)
    assert abs(result.attribution_residual) <= 1e-12
    assert_reconciles(result)  # accumulator == fsum(per-fill costs), no sidecar


def test_p1_02b_ledger_path_charges_cost_once_per_fill():
    """IdentityLedger hand fixture (all binary-exact numbers):

    starting_equity 1000.0; BUY 2 @ 10.0; cost = 1.0+0.5+0.25+0.25 = 2.0.
    cash = 1000 - 2*10 - 2 = 978.0          (c deducted ONCE)
    equity at fill (mark at fill price) = 978 + 2*10 = 998.0 = 1000 - 2.0
    (a double charge would show 996.0)
    Terminal mark 11.0 -> equity = 978 + 2*11 = 1000.0;
    terminal_pnl = 2*(11-10) = 2.0; lhs = 1000-1000 = 0; rhs = 2-2 = 0.
    """
    ledger = IdentityLedger(starting_equity=1000.0)
    cost = CostBreakdown(commission=1.0, spread=0.5, slippage=0.25, market_impact=0.25)
    assert cost.total() == 2.0
    ledger.apply_fill(FillRecord(symbol="AAA", side="BUY", quantity=2.0,
                                 price=10.0, timestamp_utc=TS, cost=cost))
    assert ledger.cash == 978.0
    assert ledger.position_qty("AAA") == 2.0
    # equity right after the fill, marked at the fill price: one charge of c
    assert ledger.cash + 2.0 * 10.0 == 998.0
    # no bucket is doubled and the buckets sum to exactly one c
    assert ledger.bucket("commissions") == 1.0
    assert ledger.bucket("spread") == 0.5
    assert ledger.bucket("slippage") == 0.25
    assert ledger.bucket("market_impact") == 0.25
    charged = (ledger.bucket("commissions") + ledger.bucket("spread")
               + ledger.bucket("slippage") + ledger.bucket("market_impact"))
    assert charged == 2.0 == cost.total()
    # identity closes on the terminal mark: terminal_pnl 2.0 vs costs 2.0
    ledger.mark_terminal("AAA", ObservableEvent(timestamp_utc=TS, price=11.0,
                                                executable=True))
    assert ledger.mark_to_market_equity() == 1000.0
    terms = ledger.identity_terms()
    assert terms.terminal_pnl == 2.0
    assert terms.residual == 0.0
    ledger.assert_closed()


def test_p1_02c_fill_cost_formula_hand_value():
    """The one-fill cost formula, hand value: 5000 * 0.3 * (25+5) / 1e4 = 4.5."""
    assert fill_cost(5000.0, 0.3, 25.0, 5.0) == 4.5


# =========================================================================== #
# INVARIANT 3 -- ONE named turnover convention
# =========================================================================== #
def test_p1_03_turnover_is_sum_of_abs_delta_weights_single_convention():
    """Hand fixture (binary-exact weights):

    before = {AAA: 0.5, BBB: 0.25, CASH: 0.25}
    after  = {AAA: 0.25, BBB: 0.5}            (implied CASH 0.25)
    sum(|delta|) over tradable legs = |0.25-0.5| + |0.5-0.25| = 0.25 + 0.25
                                    = 0.50
    """
    before = {"AAA": 0.5, "BBB": 0.25, "CASH": 0.25}
    after = {"AAA": 0.25, "BBB": 0.5}
    assert etf_leg_turnover(before, after) == 0.5
    # unchanged book -> exactly zero
    assert etf_leg_turnover(before, {"AAA": 0.5, "BBB": 0.25}) == 0.0
    # liquidation to cash charges the ETF leg ONCE (a naive CASH-inclusive
    # sum would count 1.0 twice and report 2.0)
    assert etf_leg_turnover({"AAA": 1.0}, {"CASH": 1.0}) == 1.0
    # the single named convention: exactly one production function owns it,
    # named etf_leg_turnover, keyed on the named CASH_SYMBOL constant.
    assert etf_leg_turnover.__name__ == "etf_leg_turnover"
    assert CASH_SYMBOL == "CASH"


# =========================================================================== #
# INVARIANT 4 -- canonical digest hashes exact artifact bytes
# =========================================================================== #
# sha256 of b'{"a":1,"b":2}' (the canonical serialization), computed
# independently of the production code:
DIGEST_ABC = "43258cff783fe7036d8a43033f830adfc60ec037382473548ac742b888292777"
# sha256 of b'{"a":2,"b":2}'  (same shape, one value changed):
DIGEST_CHANGED = "4c7aa83dd9f6db52730112f713f1abff872153fa5b30b2dbff4e1ecb26280c3c"
# sha256 of b'{"artifact":{"a":1,"b":2}}'  (a wrapper: DIFFERENT bytes):
DIGEST_WRAPPER = "2908614cdac219ee2722be3866c63b1cc069244398800c9bc1b4347a380faea8"

ARTIFACT = {"b": 2, "a": 1}


def test_p1_04a_canonical_json_is_sorted_compact_exact_bytes():
    assert CANONICAL_JSON_KW == {"sort_keys": True, "separators": (",", ":")}
    assert canonical_json(ARTIFACT) == '{"a":1,"b":2}'


def test_p1_04b_digest_equals_sha256_of_exact_disk_bytes(tmp_path):
    ledger = TrialLedger()  # production digest authority
    assert ledger.publish("cell|K1", ARTIFACT) is True
    recorded = [e["artifact_digest"] for e in ledger.entries
                if "artifact_digest" in e]
    assert recorded == [DIGEST_ABC]
    # the exact bytes that would be written to disk hash to the same digest
    payload_bytes = canonical_json(ARTIFACT).encode("utf-8")
    path = tmp_path / "artifact.json"
    path.write_bytes(payload_bytes)
    assert sha256_file(str(path)) == DIGEST_ABC
    assert sha256_hex(payload_bytes) == DIGEST_ABC
    # changing one value changes the digest
    assert sha256_hex(canonical_json({"b": 2, "a": 2}).encode("utf-8")) \
        == DIGEST_CHANGED
    assert DIGEST_CHANGED != DIGEST_ABC
    # a wrapper object hashes DIFFERENT bytes: never equal to the artifact digest
    assert sha256_hex(canonical_json({"artifact": ARTIFACT}).encode("utf-8")) \
        == DIGEST_WRAPPER
    assert DIGEST_WRAPPER != DIGEST_ABC


# =========================================================================== #
# INVARIANT 5 -- append-only correction does not alter counters
# =========================================================================== #
def test_p1_05_correction_append_keeps_counters_frozen(tmp_path):
    """Hand-counted: after one compute + one publish the counters are
    (observed=1, published=1) with 3 entries.  Appending correction/repin
    entries changes NOTHING in the counters; the original entries are
    preserved byte-for-dict (append-only)."""
    ledger = TrialLedger(str(tmp_path / "ledger.json"))
    key = "US_ETF_CASH|V4|ARM_X|synthetic"
    ledger.compute_recorded(key)               # observed 1, entries 1
    assert ledger.publish(key, ARTIFACT) is True  # published 1, entries 3
    before_entries = list(ledger.entries)
    assert ledger.observed == 1 and len(ledger.published_keys) == 1
    assert len(before_entries) == 3
    # append-only corrections (a digest repin and a figure correction)
    ledger.entries.append({"key": key, "event": "DIGEST_REPIN",
                           "old_digest": DIGEST_ABC, "new_digest": DIGEST_CHANGED})
    ledger.entries.append({"key": key, "event": "CORRECTION_APPEND_ONLY",
                           "field": "figure", "delta": "A7T-O1"})
    # counters did not move
    assert ledger.observed == 1
    assert len(ledger.published_keys) == 1
    assert key in ledger.published_keys
    # append-only: the original three entries are unchanged prefixes
    assert ledger.entries[:3] == before_entries
    assert len(ledger.entries) == 5
    # persistence round-trip keeps the frozen counters
    ledger.save()
    reloaded = TrialLedger(ledger.path)
    assert reloaded.observed == 1
    assert len(reloaded.published_keys) == 1
    assert len(reloaded.entries) == 5


# =========================================================================== #
# INVARIANT 6 -- observed once; replays increment neither counter
# =========================================================================== #
def test_p1_06_observed_once_and_replays_are_zero_delta():
    """Hand-counted: observed = 1 after one compute_recorded; published = 1
    after the first publication; two identical replays move NEITHER."""
    ledger = GatedTrialLedger()
    key = "US_ETF_CASH|V4|ARM_R|synthetic"
    metrics = {"n_fill_events": 2, "n_held_positions": 2}
    ledger.compute_recorded(key)
    assert ledger.observed == 1
    assert ledger.publish_result(key, ARTIFACT, **metrics) is True
    assert ledger.observed == 1 and len(ledger.published_keys) == 1
    # two identical replays: zero delta on both counters
    assert ledger.publish_result(key, ARTIFACT, **metrics) is False
    assert ledger.publish_result(key, ARTIFACT, **metrics) is False
    assert ledger.observed == 1
    assert len(ledger.published_keys) == 1
    replay_events = [e["event"] for e in ledger.entries
                     if e.get("event") == "REPLAY_ZERO_DELTA"]
    assert len(replay_events) == 2


# =========================================================================== #
# INVARIANT 7 -- zero-position and out-of-contract cells are refused
# =========================================================================== #
def test_p1_07a_zero_position_publication_is_refused():
    """A zero-event or zero-held-position result is refused, the refusal is
    recorded append-only, the key stays unpublished, and observed keeps its
    single pre-publication increment (observed-vs-published semantics)."""
    ledger = GatedTrialLedger()
    key = "US_ETF_CASH|V4|ARM_EMPTY|synthetic"
    ledger.compute_recorded(key)
    assert ledger.publish_result(key, ARTIFACT,
                                 n_fill_events=1, n_held_positions=0) is False
    assert key not in ledger.published_keys
    assert ledger.observed == 1 and len(ledger.published_keys) == 0
    refusal = [e for e in ledger.entries
               if e.get("event") == "PUBLICATION_REFUSED_ZERO_RESULT"]
    assert len(refusal) == 1 and refusal[0]["reasons"] == ["ZERO_HELD_POSITIONS"]

    ledger2 = GatedTrialLedger()
    key2 = "US_ETF_CASH|V4|ARM_NOEVENT|synthetic"
    ledger2.compute_recorded(key2)
    assert ledger2.publish_result(key2, ARTIFACT,
                                  n_fill_events=0, n_held_positions=3) is False
    assert ledger2.observed == 1 and len(ledger2.published_keys) == 0
    refusal2 = [e for e in ledger2.entries
                if e.get("event") == "PUBLICATION_REFUSED_ZERO_RESULT"]
    assert refusal2[0]["reasons"] == ["ZERO_FILL_EVENTS"]
    # non-int counts are a contract violation, not a zero result
    with pytest.raises(ValueError):
        ledger2.publish_result(key2, ARTIFACT,
                               n_fill_events=True, n_held_positions=1)
    assert publication_metrics([]) == {"n_fill_events": 0, "n_held_positions": 0}


# --- frozen cell contract (test-local; production has no cell validator) ---- #
class CellContractError(ValueError):
    """A publication cell outside its frozen contract."""


def assert_cell_in_contract(cell, *, allowed_arm_ids, allowed_universe_ids,
                            membership, as_of):
    """FROZEN A1 contract, encoded here for the regression proof:

    * ``arm_id`` must be one of the allowed arm ids of the run contract;
    * ``universe_id`` must be one of the allowed universes;
    * every held security must be an EFFECTIVE member of that universe on
      the as-of decision date (no backfill, no cross-universe leakage).
    """
    if cell["arm_id"] not in allowed_arm_ids:
        raise CellContractError(
            f"cell arm {cell['arm_id']!r} is not in the run contract")
    if cell["universe_id"] not in allowed_universe_ids:
        raise CellContractError(
            f"cell universe {cell['universe_id']!r} is not in the run contract")
    members = membership.members_as_of(as_of, universe_id=cell["universe_id"])
    leaked = [s for s in cell["held"] if s not in members]
    if leaked:
        raise CellContractError(
            f"held securities {leaked!r} are not members of "
            f"{cell['universe_id']!r} as of {as_of!r}")


@pytest.fixture()
def membership():
    return MembershipTable([
        MembershipRecord(security_id="SEC_A", universe_id="U1",
                         effective_from=date(2026, 1, 1)),
        MembershipRecord(security_id="SEC_X", universe_id="U2",
                         effective_from=date(2026, 1, 1)),
    ])


def test_p1_07b_out_of_contract_cells_are_refused(membership):
    as_of = date(2026, 6, 30)
    contract = dict(allowed_arm_ids=("ARM_OK", "ARM_B"),
                    allowed_universe_ids=("U1",))
    # in-contract cell is accepted
    assert_cell_in_contract({"arm_id": "ARM_OK", "universe_id": "U1",
                             "held": ["SEC_A"]},
                            membership=membership, as_of=as_of, **contract)
    # wrong arm id -> refused
    with pytest.raises(CellContractError, match="ARM_EVIL"):
        assert_cell_in_contract({"arm_id": "ARM_EVIL", "universe_id": "U1",
                                 "held": ["SEC_A"]},
                                membership=membership, as_of=as_of, **contract)
    # wrong universe id -> refused
    with pytest.raises(CellContractError, match="universe"):
        assert_cell_in_contract({"arm_id": "ARM_OK", "universe_id": "U2",
                                 "held": ["SEC_X"]},
                                membership=membership, as_of=as_of, **contract)
    # right universe, security NOT a member of it -> refused
    with pytest.raises(CellContractError, match="SEC_X"):
        assert_cell_in_contract({"arm_id": "ARM_OK", "universe_id": "U1",
                                 "held": ["SEC_X"]},
                                membership=membership, as_of=as_of, **contract)
    # membership is effective-dated: before the effective_from -> refused
    with pytest.raises(CellContractError, match="SEC_A"):
        assert_cell_in_contract({"arm_id": "ARM_OK", "universe_id": "U1",
                                 "held": ["SEC_A"]},
                                membership=membership,
                                as_of=date(2025, 12, 31), **contract)
    # the production replay substrate likewise refuses unknown arms
    replay = SharedCapitalReplay(starting_equity=1000.0)
    replay.register_arm("ARM_OK")
    with pytest.raises(ValueError, match="ARM_EVIL"):
        replay.require_arm("ARM_EVIL")
    with pytest.raises(ValueError, match="already registered"):
        replay.register_arm("ARM_OK")


# =========================================================================== #
# INVARIANT 8 -- simultaneous appends serialize (A1 single-writer contract)
# =========================================================================== #
# Production ledgers (TrialLedger/GatedTrialLedger) carry no locking
# primitive; the A1 single-writer contract is therefore encoded here as a
# test-local ledger helper and proven: claims are made ONLY under an
# exclusive flock, so two in-process emulations can never claim the same
# serial slot.
class _SerialSlotLedger:
    """Append serialization guard: one serial slot per successful claim."""

    def __init__(self, directory: str) -> None:
        self.lock_path = os.path.join(directory, "ledger.lock")
        self.state_path = os.path.join(directory, "ledger.serials.json")

    def claim_next_serial(self, writer: str) -> int | None:
        with open(self.lock_path, "a+") as lock_fd:
            fcntl.flock(lock_fd, fcntl.LOCK_EX)  # single-writer critical section
            try:
                if os.path.exists(self.state_path):
                    with open(self.state_path) as f:
                        state = json.load(f)
                else:
                    state = {"holders": {}, "next_serial": 1}
                if writer in state["holders"]:
                    return None  # a writer may never hold two slots
                serial = state["next_serial"]
                state["holders"][writer] = serial
                state["next_serial"] = serial + 1
                tmp = self.state_path + ".tmp"
                with open(tmp, "w") as f:
                    json.dump(state, f)
                os.replace(tmp, self.state_path)
                return serial
            finally:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)


def test_p1_08a_same_serial_slot_cannot_be_claimed_twice(tmp_path):
    ledger = _SerialSlotLedger(str(tmp_path))
    first = ledger.claim_next_serial("W1")
    assert first == 1  # hand-counted: first claim takes slot 1
    second = ledger.claim_next_serial("W2")
    assert second == 2  # W2 can NEVER receive slot 1; it serializes behind
    assert first != second
    assert ledger.claim_next_serial("W1") is None  # no double-claim per writer
    with open(ledger.state_path) as f:
        state = json.load(f)
    assert state["holders"] == {"W1": 1, "W2": 2}
    assert state["next_serial"] == 3


def test_p1_08b_concurrent_claims_serialize_to_distinct_slots(tmp_path):
    """Two truly simultaneous claimants (threads released by one barrier):
    the claimed serials must be exactly {1, 2} -- pairwise distinct, so no
    serial slot was ever double-claimed."""
    ledger = _SerialSlotLedger(str(tmp_path))
    barrier = threading.Barrier(2)
    results: dict[str, int | None] = {}
    errors: list[BaseException] = []

    def _claim(writer: str) -> None:
        try:
            barrier.wait(timeout=10)
            results[writer] = ledger.claim_next_serial(writer)
        except BaseException as exc:  # pragma: no cover - surface to assert
            errors.append(exc)

    threads = [threading.Thread(target=_claim, args=(w,))
               for w in ("WA", "WB")]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    assert errors == []
    assert sorted(results) == ["WA", "WB"]
    assert None not in results.values()
    # the frozen contract: pairwise distinct slots, exactly {1, 2}
    assert sorted(results.values()) == [1, 2]
    assert len(set(results.values())) == len(results)
