"""V13 I lane -- control-cannot-equal-anchor, falsification gate, determinism.

Evidence (e) -- the causal negative control:

* on the differentiating hand world the CTL-FLOW-ONLY book is the EXACT
  inverse of the anchor book (and therefore differs from it everywhere):
  the control longs the highest-turnover tercile and shorts the lowest,
  while the anchor's OI-stock numerator reverses both legs;
* with hand forward returns the control's weekly book return is EXACTLY
  -0.03 where the anchor's is EXACTLY +0.03;
* the preregistered falsification rule (OITD.json item6) is ENCODED for
  the gate runner: ``evaluate_control_gate`` returns
  ``FAMILY_FALSIFIED_CONTROL_REPRODUCES_ANCHOR`` iff BOTH the anchor and
  the control pass their three gates, ``CONTROL_GATE_PASS`` otherwise;
* a control that equals the anchor on any world is detectable and here
  demonstrably absent (world A, where OI is cross-sectionally constant
  and the books coincide, is exactly the mechanical-exposure null the
  control is designed to expose -- documented, not relied upon);

Evidence (d) -- deterministic double generation:

* the full chained target generation for all three arms runs twice from
  independent plugin instances; the canonical JSON (sorted keys, no
  volatile metadata) is byte-identical within each arm (sha256 equality),
  and the payload schema carries no wall-clock field at all.

All data synthetic in this file (the real-snapshot double generation lives
in the real-evidence module); no scored metric is computed.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from tests.v13i_oitd_world import (
    T1_DAY,
    T1_NS,
    merged_world,
    plugin as make_plugin,
    world_a,
    world_b,
)

from research.v13.families.oitd.strategy import (
    ANCHOR_ARM,
    CONTROL_ARM,
    CONTROL_GATE_FALSIFIED,
    CONTROL_GATE_PASS,
    NEIGHBOUR_ARM,
    compute_targets_at,
    evaluate_control_gate,
    signal_scores_at,
)


def _book_return(book, forward_returns):
    return sum(float(w) * forward_returns[str(sym)] for sym, w in book["weights"])


# --------------------------------------------------------------------- #
# (e) control-cannot-equal-anchor on the differentiating world
# --------------------------------------------------------------------- #
def test_control_book_is_the_exact_inverse_of_the_anchor() -> None:
    world = world_b(day_index=T1_DAY, stamp_ns=T1_NS)
    anchor = compute_targets_at(
        ANCHOR_ARM,
        day_turnover_by_symbol=world["day_turnover_by_symbol"],
        stamp_ns=T1_NS,
        universe=world["universe"],
        oi_by_symbol=world["oi_by_symbol"],
        mark_by_symbol=world["mark_by_symbol"],
    )
    control = compute_targets_at(
        CONTROL_ARM,
        day_turnover_by_symbol=world["day_turnover_by_symbol"],
        stamp_ns=T1_NS,
        universe=world["universe"],
    )
    a_weights = {sym: float(w) for sym, w in anchor["weights"]}
    c_weights = {sym: float(w) for sym, w in control["weights"]}
    assert set(a_weights) == set(c_weights)  # same 12 held names...
    for sym in a_weights:
        # ...with every weight exactly negated
        assert c_weights[sym] == pytest.approx(-a_weights[sym], abs=1e-12), sym
    # and therefore the books DIFFER at this stamp (no equality possible)
    assert a_weights != c_weights
    # hand legs: control longs the highest-turnover tercile (group H)
    assert [sym for sym, _w in control["longs"]] == [
        "SYM00",
        "SYM01",
        "SYM02",
        "SYM03",
        "SYM04",
        "SYM05",
    ]
    assert [sym for sym, _w in control["shorts"]] == list(sorted(set(a_weights) - set(
        sym for sym, _w in control["longs"]
    )))


def test_control_book_return_is_the_exact_negation_of_the_anchor() -> None:
    world = world_b(day_index=T1_DAY, stamp_ns=T1_NS)
    anchor = compute_targets_at(
        ANCHOR_ARM,
        day_turnover_by_symbol=world["day_turnover_by_symbol"],
        stamp_ns=T1_NS,
        universe=world["universe"],
        oi_by_symbol=world["oi_by_symbol"],
        mark_by_symbol=world["mark_by_symbol"],
    )
    control = compute_targets_at(
        CONTROL_ARM,
        day_turnover_by_symbol=world["day_turnover_by_symbol"],
        stamp_ns=T1_NS,
        universe=world["universe"],
    )
    anchor_return = _book_return(anchor, world["forward_returns"])
    control_return = _book_return(control, world["forward_returns"])
    # hand truth: +0.03 vs -0.03
    assert anchor_return == pytest.approx(0.03, abs=1e-12)
    assert control_return == pytest.approx(-0.03, abs=1e-12)


def test_control_ranking_is_pure_descending_turnover() -> None:
    world = world_b(day_index=T1_DAY, stamp_ns=T1_NS)
    scores = signal_scores_at(
        CONTROL_ARM,
        day_turnover_by_symbol=world["day_turnover_by_symbol"],
        stamp_ns=T1_NS,
        universe=world["universe"],
    )
    # the control score IS the raw turnover level: longs = argmax
    assert scores["SYM00"] == pytest.approx(1_000_000.0)
    assert scores["SYM17"] == pytest.approx(250_000.0)
    ordered = sorted(scores, key=lambda s: -scores[s])
    assert ordered[:6] == [f"SYM{i:02d}" for i in range(6)]


def test_world_a_is_the_documented_mechanical_null_not_the_control_result() -> None:
    """Cross-sectionally constant OI: anchor == control BY CONSTRUCTION.

    This is the null the causal control exists to expose -- when the OI
    stock carries no cross-sectional information the anchor degenerates
    to the flow sort.  The differentiating world above proves the
    implemented anchor is NOT that degenerate book when OI varies.
    """
    world = world_a()
    anchor = compute_targets_at(
        ANCHOR_ARM,
        day_turnover_by_symbol=world["day_turnover_by_symbol"],
        stamp_ns=T1_NS,
        universe=world["universe"],
        oi_by_symbol=world["oi_by_symbol"],
        mark_by_symbol=world["mark_by_symbol"],
    )
    control = compute_targets_at(
        CONTROL_ARM,
        day_turnover_by_symbol=world["day_turnover_by_symbol"],
        stamp_ns=T1_NS,
        universe=world["universe"],
    )
    a_weights = {sym: float(w) for sym, w in anchor["weights"]}
    c_weights = {sym: float(w) for sym, w in control["weights"]}
    assert a_weights == c_weights  # the degenerate null, documented


# --------------------------------------------------------------------- #
# (e) the preregistered falsification rule, encoded for the gate runner
# --------------------------------------------------------------------- #
def test_preregistered_control_falsification_rule_is_encoded() -> None:
    rule = evaluate_control_gate(anchor_passes=True, control_passes=True)
    assert rule["verdict"] == CONTROL_GATE_FALSIFIED
    assert "pure turnover-level" in rule["rule"] or "turnover" in rule["rule"]
    # anchor passes, control fails at least one gate -> family survives
    assert evaluate_control_gate(anchor_passes=True, control_passes=False)[
        "verdict"
    ] == CONTROL_GATE_PASS
    # anchor itself failing is a DIFFERENT falsification mode (item9.1);
    # the control rule alone never falsifies a failing anchor
    assert evaluate_control_gate(anchor_passes=False, control_passes=True)[
        "verdict"
    ] == CONTROL_GATE_PASS
    assert evaluate_control_gate(anchor_passes=False, control_passes=False)[
        "verdict"
    ] == CONTROL_GATE_PASS


def test_control_gate_verdicts_are_distinct_constants() -> None:
    assert CONTROL_GATE_FALSIFIED == "FAMILY_FALSIFIED_CONTROL_REPRODUCES_ANCHOR"
    assert CONTROL_GATE_PASS == "CONTROL_GATE_PASS"
    assert CONTROL_GATE_PASS != CONTROL_GATE_FALSIFIED


# --------------------------------------------------------------------- #
# (d) deterministic double generation (synthetic, all three arms)
# --------------------------------------------------------------------- #
def _generate_all_arms_twice():
    stamps = [T1_NS, T1_NS + 7 * 86_400_000_000_000, T1_NS + 14 * 86_400_000_000_000]
    world = merged_world(stamps)
    runs = []
    for _run in range(2):
        payloads = {}
        for arm_id in (ANCHOR_ARM, NEIGHBOUR_ARM, CONTROL_ARM):
            p = make_plugin(arm_id, world)
            payloads[arm_id] = [
                p.targets_at(
                    int(stamp), universe=tuple(world["universe"]), stress=p.baseline_stress()
                )
                for stamp in stamps
            ]
        runs.append(payloads)
    return runs


def test_double_generation_byte_identical_all_arms() -> None:
    first, second = _generate_all_arms_twice()
    for arm_id in (ANCHOR_ARM, NEIGHBOUR_ARM, CONTROL_ARM):
        text_first = json.dumps(
            first[arm_id], sort_keys=True, separators=(",", ":"), default=str
        )
        text_second = json.dumps(
            second[arm_id], sort_keys=True, separators=(",", ":"), default=str
        )
        assert text_first == text_second, arm_id
        assert hashlib.sha256(text_first.encode()).hexdigest() == hashlib.sha256(
            text_second.encode()
        ).hexdigest()


def test_payloads_carry_no_volatile_metadata() -> None:
    """No wall-clock field exists anywhere in the generated payloads."""
    first, _second = _generate_all_arms_twice()
    volatile_tokens = ("published_utc", "observed_utc", "generated", "now", "today")
    for arm_id, payloads in first.items():
        text = json.dumps(payloads, sort_keys=True, default=str).lower()
        for token in volatile_tokens:
            assert token not in text, (arm_id, token)


def test_strategy_and_plugin_generation_agree() -> None:
    """The chained plugin book equals the raw module book at the flat start."""
    world = world_b(day_index=T1_DAY, stamp_ns=T1_NS)
    plugin_book = make_plugin(ANCHOR_ARM, world).targets_at(
        T1_NS, universe=tuple(world["universe"]), stress=make_plugin(
            ANCHOR_ARM, world
        ).baseline_stress()
    )
    module_book = compute_targets_at(
        ANCHOR_ARM,
        day_turnover_by_symbol=world["day_turnover_by_symbol"],
        stamp_ns=T1_NS,
        universe=world["universe"],
        oi_by_symbol=world["oi_by_symbol"],
        mark_by_symbol=world["mark_by_symbol"],
    )
    assert json.dumps(plugin_book["weights"], sort_keys=True) == json.dumps(
        module_book["weights"], sort_keys=True
    )
    assert plugin_book["longs"] == module_book["longs"]
    assert plugin_book["shorts"] == module_book["shorts"]
