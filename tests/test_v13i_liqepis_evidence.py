"""V13 I lane (i-family-2) -- invariants, cost/funding-once, determinism,
real-snapshot schedule feasibility, drop-one and dummy-publication dry-run
for A13-V13-A5-LIQEPIS (plan section 9 evidence items d, f, g, h, i, j).

Inherited conventions exercised here (v13_p_freeze.json, byte-for-byte
pointers into the V12 freezes):

* (f) cap/gross/net/cash invariants -- ``|weight| <= 0.30`` at every stamp,
  ``gross <= 1.0``, dollar-neutral net, ``net + cash_line == 1`` with cash
  NEVER a tradable symbol, force-flat spans clamped at fold end boundaries;
* (g) cost-once and funding-settlement-once -- a transition is charged
  exactly once per side-delta (recomputation is identical, zero deltas cost
  nothing), a native funding settlement accrues EXACTLY ONCE per held span
  under ``start < ts <= end``, funding is a COST (``LONG_PAYS_POSITIVE_RATE``)
  and never a signal, and the sign-inverted causal control mirrors the
  anchor's funding cashflows EXACTLY with opposite sign;
* stress cell inherited from L-V11-1: fee x1.5 / +2 adverse ticks / +1 event
  delay over the baseline, on the family's own folds contract;
* (d) deterministic double generation -- byte-identical canonical JSON on a
  synthetic world and on the read-only real snapshot;
* (h) schedule-only feasibility on the REAL snapshot -- decisions per fold,
  purge, eligibility/refusals, turnover estimate, holding durations; NO PnL,
  no returns, no cost numbers on real data anywhere;
* (i) non-vacuous drop-one -- the selected symbol is the HELD max-|weight|
  symbol (pin-exact tie-breaks), the renormalization preserves gross 1.0
  and dollar neutrality per :data:`DROP_ONE_PIN`;
* (j) dummy publication dry-run into a namespaced TEMPORARY ledger --
  publish (DUMMY constants), zero-position refusal, out-of-contract
  refusal, exact replay with ZERO counter delta; ZERO scored metrics.

Real data are READ-ONLY workspace files; every real-data test is skipped
when the workspace snapshot is absent.  No scored metric exists in this
lane: the dry-run metrics are fixed DUMMY constants.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.adapter_v10.protocol import PositionSpan, StressSpec
from research.v13.families.liqepis.audits import (
    DEFAULT_LEDGER_PATH,
    DRYRUN_DUMMY_METRICS_KIND,
    build_plugins,
    build_schedule_records,
    evidence_double_generation,
    evidence_drop_one,
    evidence_schedule_feasibility,
    require_temporary_ledger,
    run_dummy_publication_dryrun,
    tradeable_universe_symbols,
)
from research.v13.families.liqepis.frozen_identity import (
    LIQEPIS_ARM_CONFIG_DIGESTS,
    frozen_arm_digest_report,
)
from research.v13.families.liqepis.gate_runner import evaluate_family_gate
from research.v13.families.liqepis.plugin import (
    STRESS_CELL_NAME,
    LiqepisPlugin,
    family_stress_cell,
)
from research.v13.families.liqepis.strategy import (
    ANCHOR_ARM,
    ARM_IDS,
    BAR_INTERVAL_NS,
    CONTROL_ARM,
    DAY_NS,
    DROP_ONE_PIN,
    F1_PURGED_STAMP_ISO,
    FOLD_WINDOWS,
    HOLDING_DAYS,
    LEGS_PER_SIDE,
    NEIGHBOUR_ARM,
    PER_NAME_WEIGHT,
    PURGE_DAYS,
    cash_reconciliation,
    compute_targets_at,
    effective_schedule,
    fold_assignments,
    fold_end_ns,
    force_flat_span_end,
    parse_iso_utc,
    schedule_drop_one,
    build_drop_one_book,
    select_drop_one_symbol_at,
    stamp_calendar,
)

from tests.test_v13i_liqepis_goldens import build_world, load_fixture

DATA_ROOT = Path("/Users/hoangminhlong/my-quantitative/catalog_live_crypto/data")

_requires_data = pytest.mark.skipif(
    not DATA_ROOT.is_dir(), reason="read-only workspace data absent"
)


def _fixture_plugin(*, arm_id: str, settlements=None) -> LiqepisPlugin:
    """Anchor/neighbour/control plugin on the tiny synthetic fixture world."""
    fixture = load_fixture()
    world, _stamp, universe = build_world(fixture)
    bars = dict(world)
    bars["BTCUSDT"] = world["SYM00"]  # benchmark context bars (never traded)
    return LiqepisPlugin(
        arm_id=arm_id,
        bars_by_symbol=bars,
        settlements_by_symbol=settlements or {},
        tick_sizes={sym: 0.01 for sym in universe},
    )


# --------------------------------------------------------------------------- #
# (f) cap / gross / net / cash invariants + force-flat at fold boundaries
# --------------------------------------------------------------------------- #
def test_book_invariants_hold_on_every_fixture_stamp() -> None:
    fixture = load_fixture()
    world, stamp, universe = build_world(fixture)
    # exercise the fixture stamp AND its four later (in-window) stamps
    for offset in range(0, 5):
        at = stamp + offset * BAR_INTERVAL_NS
        for arm in (ANCHOR_ARM, NEIGHBOUR_ARM, CONTROL_ARM):
            book = compute_targets_at(
                arm, bars_by_symbol=world, stamp_ns=at, universe=universe
            )
            weights = {sym: float(w) for sym, w in book["weights"]}
            assert "BTCUSDT" not in weights  # benchmark never held
            max_abs = max(abs(w) for w in weights.values())
            assert max_abs <= 0.30 + 1e-12
            gross = sum(abs(w) for w in weights.values())
            assert gross <= 1.0 + 1e-9
            rec = cash_reconciliation(weights)
            assert rec["cash_is_tradable_symbol"] is False
            assert rec["net_plus_cash_is_one"] is True
            assert rec["reconciles"] is True
            assert rec["n_positions"] == 12
            # dollar-neutral tercile book: equal |w| per name, signed by leg
            assert abs(max_abs - PER_NAME_WEIGHT) < 1e-12


def test_force_flat_spans_clamp_at_fold_end_boundaries() -> None:
    calendar = stamp_calendar()
    fold_ends = {
        parse_iso_utc(f"{end}T00:00:00Z") for _l, _s, end in FOLD_WINDOWS
    }
    for stamp in calendar:
        intended = stamp + HOLDING_DAYS * DAY_NS
        clamped = force_flat_span_end(stamp, holding_days=HOLDING_DAYS)
        # the span never crosses its own fold's end boundary
        assert clamped <= fold_end_ns(stamp)
        assert clamped == min(intended, fold_end_ns(stamp))
    # exact clamps: a stamp 3 days before a fold end is pulled back to it,
    # a stamp far from the boundary runs its full 7-day holding span
    f1_end = parse_iso_utc("2025-12-21T00:00:00Z")
    near_end = f1_end - 3 * DAY_NS
    assert force_flat_span_end(near_end) == f1_end
    far_from_end = parse_iso_utc("2025-09-01T00:00:00Z")
    assert force_flat_span_end(far_from_end) == far_from_end + HOLDING_DAYS * DAY_NS
    # every fold end is a force-flat boundary and the purge zone is 1 day
    assert fold_ends == {
        parse_iso_utc("2025-12-21T00:00:00Z"),
        parse_iso_utc("2026-04-21T00:00:00Z"),
        parse_iso_utc("2026-08-21T00:00:00Z"),
    }
    assert PURGE_DAYS == 1


def test_frozen_fold_calendar_with_one_day_purge_is_pinned() -> None:
    calendar = stamp_calendar()
    assert len(calendar) == 52
    assert calendar[0] == parse_iso_utc("2025-08-25T00:00:00Z")
    effective, purged_by_fold = effective_schedule(calendar)
    assert len(effective) == 51
    assert purged_by_fold == {
        "F1": [parse_iso_utc(F1_PURGED_STAMP_ISO)]
    }
    assignments = fold_assignments(calendar)
    counts = {label: len(members) for _i, label, members, _p in assignments}
    assert counts == {"F0": 17, "F1": 17, "F2": 17}
    # effective = calendar minus the purged stamp, order preserved
    purged_all = {t for stamps in purged_by_fold.values() for t in stamps}
    assert [t for t in calendar if t not in purged_all] == effective


# --------------------------------------------------------------------------- #
# (g) cost-once and funding-settlement-once (+ control funding mirror)
# --------------------------------------------------------------------------- #
def test_stress_cell_is_the_inherited_x1_5_plus2ticks_plus1delay() -> None:
    plugin = _fixture_plugin(arm_id=ANCHOR_ARM)
    baseline = plugin.baseline_stress()
    stress = family_stress_cell(baseline)
    assert STRESS_CELL_NAME == "fee_x1_5_plus2ticks_plus1delay"
    assert stress.fee_multiplier == 1.5
    assert stress.tick_slip_ticks == baseline.tick_slip_ticks + 2
    assert stress.event_delay_events == baseline.event_delay_events + 1


def test_rebalance_cost_charged_exactly_once_per_transition() -> None:
    plugin = _fixture_plugin(arm_id=ANCHOR_ARM)
    fixture = load_fixture()
    world, stamp, universe = build_world(fixture)
    first = compute_targets_at(
        ANCHOR_ARM, bars_by_symbol=world, stamp_ns=stamp, universe=universe
    )
    prices = {sym: 1.0 for sym in universe}
    baseline = plugin.baseline_stress()
    w1 = {sym: float(w) for sym, w in first["weights"]}
    # a full 100% flip costs exactly gross x rate, charged ONCE
    flipped = {sym: -w for sym, w in w1.items()}
    once = plugin.rebalance_cost_between(
        w1, flipped, prices=prices, stress=baseline
    )
    again = plugin.rebalance_cost_between(
        w1, flipped, prices=prices, stress=baseline
    )
    assert once == again  # deterministic, no double counting
    model = plugin.cost_model()
    tick = 0.01  # the injected tick size
    traded_notional = 2.0  # flipping 12 legs of 1/12 each trades 2x gross
    # baseline rate = taker fee floor + adverse-tick floor slippage
    base_rate = model.taker_fee_bps * 1e-4 + int(model.adverse_tick_slip_floor) * tick
    assert once == pytest.approx(traded_notional * base_rate, abs=1e-9)
    # a no-op rebalance trades nothing and costs nothing
    assert (
        plugin.rebalance_cost_between(w1, w1, prices=prices, stress=baseline)
        == 0.0
    )
    # the inherited stress cell scales the fee by exactly x1.5 (+2 ticks)
    stressed = plugin.rebalance_cost_between(
        w1, flipped, prices=prices, stress=family_stress_cell(baseline)
    )
    stress_rate = (
        model.taker_fee_bps * 1e-4 * 1.5
        + (int(model.adverse_tick_slip_floor) + 2) * tick
    )
    assert stressed == pytest.approx(traded_notional * stress_rate, abs=1e-9)
    assert stressed > once  # the stress cell is strictly more expensive


def test_funding_settlement_accrues_exactly_once_as_a_cost() -> None:
    fixture = load_fixture()
    stamp = int(fixture["stamp_ns"])
    settlements = {
        # three native settlements: one strictly inside the span, one at the
        # span END (accrues: start < ts <= end), one after (excluded)
        "SYM00": [
            {"kind": "funding", "publish_ts_ns": stamp + DAY_NS, "value": 0.0001},
            {"kind": "funding", "publish_ts_ns": stamp + 7 * DAY_NS, "value": 0.0002},
            {"kind": "funding", "publish_ts_ns": stamp + 8 * DAY_NS, "value": 0.0004},
        ],
    }
    plugin = _fixture_plugin(arm_id=ANCHOR_ARM, settlements=settlements)
    span = PositionSpan(
        symbol="SYM00",
        signed_weight=PER_NAME_WEIGHT,  # a LONG leg
        start_ns=stamp,
        end_ns=stamp + 7 * DAY_NS,
    )
    flows = plugin.funding_cashflows_for_spans([span])
    assert len(flows) == 2  # exactly once per settlement inside the span
    assert [f["publish_ts_ns"] for f in flows] == [
        stamp + DAY_NS,
        stamp + 7 * DAY_NS,
    ]
    # LONG_PAYS_POSITIVE_RATE: a long leg PAYS (+rate) -> negative cashflow
    for flow, rate in zip(flows, (0.0001, 0.0002)):
        assert flow["cashflow_per_unit_capital"] == round(-PER_NAME_WEIGHT * rate, 12)
        assert flow["sign_convention"] == "LONG_PAYS_POSITIVE_RATE"
    # funding is a COST on held legs only: a flat span accrues nothing
    flat = PositionSpan(
        symbol="SYM00", signed_weight=0.0, start_ns=stamp, end_ns=span.end_ns
    )
    assert plugin.funding_cashflows_for_spans([flat]) == []
    # a settlement strictly at the span START does not accrue (start < ts)
    early = PositionSpan(
        symbol="SYM00",
        signed_weight=PER_NAME_WEIGHT,
        start_ns=stamp + DAY_NS,
        end_ns=stamp + 2 * DAY_NS,
    )
    assert plugin.funding_cashflows_for_spans([early]) == []


def test_control_funding_cashflows_mirror_the_anchor_with_opposite_sign() -> None:
    """The inverted book pays/receives EXACTLY the anchor's negative."""
    fixture = load_fixture()
    stamp = int(fixture["stamp_ns"])
    universe = list(fixture["symbols"])
    rates = [0.0001, 0.0002, -0.00005]
    settlements = {
        sym: [
            {"kind": "funding", "publish_ts_ns": stamp + k * DAY_NS, "value": r}
            for k, r in enumerate(rates, start=1)
        ]
        for sym in universe
    }
    anchor = _fixture_plugin(arm_id=ANCHOR_ARM, settlements=settlements)
    control = _fixture_plugin(arm_id=CONTROL_ARM, settlements=settlements)
    world, _s, _u = build_world(fixture)
    book_a = compute_targets_at(
        ANCHOR_ARM, bars_by_symbol=world, stamp_ns=stamp, universe=universe
    )
    book_c = compute_targets_at(
        CONTROL_ARM, bars_by_symbol=world, stamp_ns=stamp, universe=universe
    )
    end = stamp + 7 * DAY_NS
    spans_a = [
        PositionSpan(
            symbol=sym,
            signed_weight=float(w),
            start_ns=stamp,
            end_ns=end,
        )
        for sym, w in book_a["weights"]
    ]
    spans_c = [
        PositionSpan(
            symbol=sym,
            signed_weight=float(w),
            start_ns=stamp,
            end_ns=end,
        )
        for sym, w in book_c["weights"]
    ]
    flows_a = anchor.funding_cashflows_for_spans(spans_a)
    flows_c = control.funding_cashflows_for_spans(spans_c)
    assert len(flows_a) == len(flows_c) == 12 * len(rates)
    key = lambda row: (row["publish_ts_ns"], row["symbol"])  # noqa: E731
    flows_a.sort(key=key)
    flows_c.sort(key=key)
    for a, c in zip(flows_a, flows_c):
        assert a["symbol"] == c["symbol"]
        assert a["publish_ts_ns"] == c["publish_ts_ns"]
        assert a["signed_weight"] == -c["signed_weight"]  # exact negation
        assert a["cashflow_per_unit_capital"] == -c["cashflow_per_unit_capital"]
    total_a = sum(f["cashflow_per_unit_capital"] for f in flows_a)
    total_c = sum(f["cashflow_per_unit_capital"] for f in flows_c)
    assert total_c == -total_a


# --------------------------------------------------------------------------- #
# (d) deterministic double generation
# --------------------------------------------------------------------------- #
def test_double_generation_synthetic_world_is_byte_identical() -> None:
    fixture = load_fixture()
    world, stamp, universe = build_world(fixture)
    stamps = [stamp + k * BAR_INTERVAL_NS for k in range(0, 5)]

    def generate() -> str:
        payload = {
            arm: [
                compute_targets_at(
                    arm, bars_by_symbol=world, stamp_ns=t, universe=universe
                )
                for t in stamps
            ]
            for arm in ARM_IDS
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    assert generate() == generate()


@_requires_data
def test_double_generation_real_snapshot_is_byte_identical() -> None:
    payload = evidence_double_generation()
    assert payload["all_byte_identical"] is True
    for arm_id, arm in payload["arms"].items():
        assert arm["records"] == 51, arm_id
        assert arm["generation_1_sha256"] == arm["generation_2_sha256"]


# --------------------------------------------------------------------------- #
# (h) schedule-only feasibility on the REAL snapshot (NO PnL)
# --------------------------------------------------------------------------- #
@_requires_data
def test_schedule_only_feasibility_on_real_snapshot() -> None:
    payload = evidence_schedule_feasibility()
    assert payload["schedule_only"] is True
    assert payload["pnl_computed"] is False
    assert payload["n_schedule_stamps"] == 52
    assert payload["n_effective_stamps"] == 51
    assert payload["fold_member_counts"] == {"F0": 17, "F1": 17, "F2": 17}
    assert payload["purged_stamps_by_fold"] == {
        "F1": ["2026-04-20T00:00:00Z"]
    }
    assert payload["universe_size"] == 19  # 20 staged minus BTCUSDT
    assert payload["all_arms_pass"] is True
    for arm_id, arm in payload["arms"].items():
        assert arm["verdict"] == "PASS", arm_id
        assert arm["n_fail"] == 0
        assert arm["decisions_total"] == 51
        assert arm["decisions_per_fold"] == {"F0": 17, "F1": 17, "F2": 17}
        # >= 15 decisions per fold floor (A9-F measured floors)
        assert min(arm["decisions_per_fold"].values()) >= 15
        # full formation coverage: 18..19 of 19 names eligible at every stamp
        assert arm["n_eligible_min"] >= 13
        # cap/gross invariants observed on the real books
        assert arm["max_abs_weight_observed"] <= 0.30
        assert arm["max_gross_observed"] <= 1.0 + 1e-9
        # turnover estimate and holding durations (counts only, never PnL)
        assert arm["one_way_turnover_total"] > 0.0
        assert arm["n_hold_spans"] > 0
        assert arm["median_holding_days"] >= 3
    # the causal control trades the SAME book as the anchor, sign-flipped:
    # identical turnover, identical eligibility footprint
    a = payload["arms"][ANCHOR_ARM]
    c = payload["arms"][CONTROL_ARM]
    assert a["one_way_turnover_total"] == c["one_way_turnover_total"]
    assert a["n_hold_spans"] == c["n_hold_spans"]


# --------------------------------------------------------------------------- #
# (i) non-vacuous drop-one (pin-exact tie-break + renormalization)
# --------------------------------------------------------------------------- #
def test_drop_one_tie_breaks_are_pin_exact_on_synthetic_books() -> None:
    # all-equal book: earliest stamp wins, lexicographically smallest symbol
    book_a = {"S2": PER_NAME_WEIGHT, "S1": PER_NAME_WEIGHT}
    book_b = {"S9": PER_NAME_WEIGHT, "S3": -PER_NAME_WEIGHT}
    records = [
        {"decision_ns": 100, "weights": [[s, w] for s, w in book_a.items()]},
        {"decision_ns": 200, "weights": [[s, w] for s, w in book_b.items()]},
    ]
    sel = schedule_drop_one(records)
    assert sel["stamp_ns"] == 100  # EARLIEST stamp attaining the max |weight|
    assert sel["symbol"] == "S1"  # lexicographically smallest held
    assert sel["proven_held"] is True
    assert sel["pin"] == DROP_ONE_PIN
    # held-only: an unheld (zero-weight) symbol is never selected
    with pytest.raises(Exception):
        select_drop_one_symbol_at({"S1": 0.0, "S2": 0.0})
    assert select_drop_one_symbol_at({"S1": 0.0, "S2": -0.2}) == "S2"
    # dropping a LONG leaves 5L/6S under the pinned constant-side-gross rule
    six_v_six = {}
    for i in range(LEGS_PER_SIDE):
        six_v_six[f"L{i}"] = PER_NAME_WEIGHT
        six_v_six[f"S{i}"] = -PER_NAME_WEIGHT
    renorm = build_drop_one_book(six_v_six, dropped_symbol="L0")
    assert renorm["dropped_side"] == "long"
    assert len(renorm["longs"]) == LEGS_PER_SIDE - 1
    assert len(renorm["shorts"]) == LEGS_PER_SIDE
    weights = {s: w for s, w in renorm["weights"]}
    assert all(weights[s] == pytest.approx(0.1, abs=1e-12) for s in renorm["longs"])
    assert all(
        weights[s] == pytest.approx(-PER_NAME_WEIGHT, abs=1e-12)
        for s in renorm["shorts"]
    )
    assert renorm["gross"] <= 1.0 + 1e-9
    # dropping a SHORT mirrors it: 6L/5S, shorts at 1/10
    renorm_s = build_drop_one_book(six_v_six, dropped_symbol="S0")
    assert renorm_s["dropped_side"] == "short"
    assert len(renorm_s["longs"]) == LEGS_PER_SIDE
    assert len(renorm_s["shorts"]) == LEGS_PER_SIDE - 1
    assert renorm_s["gross"] <= 1.0 + 1e-9
    # an unheld drop target refuses (non-vacuousness)
    with pytest.raises(Exception):
        build_drop_one_book(six_v_six, dropped_symbol="ZZZ")


@_requires_data
def test_drop_one_real_snapshot_selects_proven_held_max_weight() -> None:
    payload = evidence_drop_one()
    assert payload["non_vacuous"] is True
    assert payload["renormalization_ok"] is True
    assert payload["selection"]["proven_held"] is True
    assert payload["selection"]["pin"] == DROP_ONE_PIN
    assert abs(payload["dropped_symbol_held_abs_weight"] - PER_NAME_WEIGHT) < 1e-12
    renorm = payload["renormalized_book"]
    n_longs, n_shorts = len(renorm["longs"]), len(renorm["shorts"])
    assert sorted((n_longs, n_shorts)) == [LEGS_PER_SIDE - 1, LEGS_PER_SIDE]
    assert renorm["gross"] <= 1.0 + 1e-9


# --------------------------------------------------------------------------- #
# (j) dummy publication dry-run (temporary ledger; ZERO scored metrics)
# --------------------------------------------------------------------------- #
def test_require_temporary_ledger_refuses_non_dryrun_paths(tmp_path) -> None:
    with pytest.raises(Exception):
        require_temporary_ledger(None)
    with pytest.raises(Exception):
        require_temporary_ledger(tmp_path / "ledger.jsonl")  # missing namespace
    with pytest.raises(Exception):
        require_temporary_ledger(tmp_path / "dryrun_wrong_ext.json")
    assert require_temporary_ledger(tmp_path / "dryrun_ok.jsonl").is_absolute()


@_requires_data
def test_dummy_publication_dryrun_refusal_publish_and_replay(tmp_path) -> None:
    ledger = tmp_path / "dryrun_liqepis.jsonl"
    payload = run_dummy_publication_dryrun(ledger_path=ledger)
    assert payload["scored"] is False
    assert payload["real_pnl"] is False
    assert payload["scored_metrics_computed"] == 0
    assert payload["ok"] is True
    assert payload["ledger_path"] == str(ledger)  # temporary, namespaced
    for arm_id, arm in payload["arms"].items():
        traversal = arm["adapter_traversal"]
        assert traversal["n_universe"] == 19
        assert traversal["n_schedule_stamps"] == 52
        assert traversal["n_effective_stamps"] == 51
        assert traversal["fold_labels"] == ["F0", "F1", "F2"]
        assert traversal["fold_members"] == [17, 17, 17]
        assert traversal["dropped_fold_accepted"] is True
        assert traversal["first_stamp_book_symbols"] == 12
        assert traversal["first_stamp_max_abs_weight"] <= 0.30
        assert traversal["force_flat_within_fold"] is True
        assert traversal["n_fills_applied_probe"] == 2
        assert "00:15:00Z" in traversal["declared_execution_lag"]
        # zero-position DUMMY payload is REFUSED (inherited activity guard)
        assert arm["zero_position_refused"] is True
        assert arm["zero_position_stage"] == "REFUSED"
        # out-of-contract stress cell is REFUSED (L-V11-1 superset guard)
        assert arm["out_of_contract_refused"] is True
        assert arm["out_of_contract_stage"] == "REFUSED"
        # the held-position DUMMY payload publishes exactly once ...
        assert arm["dummy_publish_stage"] == "PUBLISHED"
        assert arm["dummy_publish_cell"] == "fee_x1_5_plus2ticks_plus1delay"
        assert arm["dummy_metrics_kind"] == DRYRUN_DUMMY_METRICS_KIND
        # ... and its EXACT replay is an idempotent skip with ZERO counter delta
        assert arm["replay_stage"] == "IDEMPOTENT_REPLAY_SKIPPED"
        assert arm["replay_zero_counter_delta"] is True
    denominators = payload["ledger_denominators"]
    # exactly one DUMMY CELL_RESULT + two refusals per arm; nothing else
    assert denominators["published"] == 3
    assert denominators["observed"] == 6
    assert denominators["observed_total"] == 9


def test_identity_digest_report_matches_recorded_digests() -> None:
    report = frozen_arm_digest_report()
    assert set(report) == set(ARM_IDS) == set(LIQEPIS_ARM_CONFIG_DIGESTS)
    for arm_id, entry in report.items():
        assert entry["match"] is True, arm_id
        assert entry["computed_from_identity"] == entry["recorded_in_freeze"]


def test_gate_runner_encodes_the_preregistered_control_rule() -> None:
    """The falsification wiring lives in the gate runner (evidence e, wiring)."""
    advance = evaluate_family_gate(
        anchor_fold_positive=[True, True, False],
        control_fold_positive=[True, False, False],
        neighbour_fold_positive=[True, True, False],
    )
    assert advance["verdict"] == "FAMILY_ADVANCES_TO_STAGE_A"
    falsified = evaluate_family_gate(
        anchor_fold_positive=[True, True, False],
        control_fold_positive=[True, True, False],
        neighbour_fold_positive=[True, True, False],
    )
    assert falsified["verdict"] == "FALSIFIED_CONTROL_REPRODUCED_TILT_ARTIFACT"
    assert falsified["control_never_promotable"] is True
