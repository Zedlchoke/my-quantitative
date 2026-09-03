"""Partition/fold handling, cash/long-only invariants and the structural
sign-flip control test for family A4, on the FROZEN spec, FROZEN calendar
and FROZEN partition with fully synthetic (offline) price series.

Derived slot counts vs the frozen spec: the spec records fold slots
20/28/29 (total 77); the A7 selection freeze (selection_freeze.json,
``o2_erratum``) records "A4 fold-2 slot count 28 vs 29 derivable; totals 77
vs 78 - erratum, minima unaffected (LOW, advisory)".  The calendar-derived
counts below are 20/29/29 = 78, matching the erratum.
"""

from __future__ import annotations

import pytest

from research.stocks_free_v2.family_a4 import (
    control_differs_only_in_ranking_sign,
    build_arm_configs,
    build_decision_slots,
    force_flat_events,
    generate_target_book,
    load_frozen_spec,
)
from tests.stocks_free_v2.family_a4._fixtures import (
    make_inputs,
    real_partition,
    wave_series,
)

RANKABLE_10 = [
    "XLK", "XLE", "XLF", "XLV", "XLI", "XLP", "XLY", "XLU", "XLB", "XLRE",
]


def s0_inputs(s0_sessions):
    tr = wave_series(s0_sessions, RANKABLE_10)
    raw = {
        symbol: {day: value * 0.99 for day, value in series.items()}
        for symbol, series in tr.items()
    }  # raw executable closes differ from the TR signal series
    return make_inputs(
        load_frozen_spec(), s0_sessions, tr, raw, real_partition()
    )


class TestStructuralControl:
    def test_control_differs_only_in_ranking_sign(self, real_spec):
        anchor, neighbour, control = build_arm_configs(real_spec)
        assert control_differs_only_in_ranking_sign(anchor, control)
        # and the neighbour is NOT the control: different score and weighting
        assert neighbour.score != anchor.score
        assert neighbour.weighting != anchor.weighting
        assert neighbour.ranking_sign == anchor.ranking_sign == 1
        assert control.ranking_sign == -1


class TestPartitionSchedule:
    def test_force_flat_events_from_frozen_spec(self, s0_sessions):
        inputs = s0_inputs(s0_sessions)
        assert force_flat_events(inputs) == (
            "2020-09-01", "2023-02-09", "2025-07-24", "2025-07-31",
        )

    def test_valid_decision_counts_vs_partition(self, s0_sessions):
        inputs = s0_inputs(s0_sessions)
        slots = build_decision_slots(inputs)
        valid = [s for s in slots if not s.suppressed]
        per_fold: dict[str, int] = {}
        for slot in valid:
            per_fold[slot.fold_id] = per_fold.get(slot.fold_id, 0) + 1
        # calendar-derived (matches the A7-recorded erratum; spec prose
        # recorded fold2=28/total=77)
        assert per_fold == {
            "S0_FOLD_1": 20, "S0_FOLD_2": 29, "S0_FOLD_3": 29,
        }
        assert len(valid) == 78
        # spec-recorded values are carried in the summary for transparency
        for config in build_arm_configs(inputs.spec)[:1]:
            stream = generate_target_book(inputs, config)
            assert stream.summary["spec_recorded_calendar_slots_s0"] == {
                "fold1": 20, "fold2": 28, "fold3": 29, "total": 77,
            }
            assert stream.summary["decisions_per_fold"] == per_fold

    def test_ramp_suppression_is_nine_warmup_extension_slots(self, s0_sessions):
        inputs = s0_inputs(s0_sessions)
        slots = build_decision_slots(inputs)
        suppressed = [s.decision_date for s in slots if s.suppressed]
        assert suppressed == [
            "2018-04-30", "2018-05-31", "2018-06-29", "2018-07-31",
            "2018-08-31", "2018-09-28", "2018-10-31", "2018-11-30",
            "2018-12-31",
        ]
        # first valid decision is the 2019-01-31 month-end (fill 2019-02-01)
        first_valid = next(s for s in slots if not s.suppressed)
        assert first_valid.decision_date == "2019-01-31"
        assert first_valid.fill_date == "2019-02-01"

    def test_s1_seal_no_date_enters_the_schedule(self, s0_sessions):
        inputs = s0_inputs(s0_sessions)
        for config in build_arm_configs(inputs.spec):
            stream = generate_target_book(inputs, config)
            for entry in stream.entries:
                assert entry.fill_date <= "2025-07-31"
                if entry.decision_date is not None:
                    assert entry.decision_date <= "2025-07-31"
            # last decision is 2025-06-30: the 2025-07-31 month-end would
            # fill 2025-08-01 (sealed S1), so the slot does not exist
            decision_dates = [
                e.decision_date for e in stream.entries
                if e.entry_type == "decision_fill"
            ]
            assert decision_dates[-1] == "2025-06-30"
            assert "2025-07-31" not in decision_dates


class TestForceFlat:
    def test_fold_boundaries_force_flat(self, s0_sessions):
        inputs = s0_inputs(s0_sessions)
        anchor, _n, _c = build_arm_configs(inputs.spec)
        stream = generate_target_book(inputs, anchor)
        flats = [e for e in stream.entries if e.entry_type == "force_flat"]
        flat_dates = [e.fill_date for e in flats]
        # the book is non-empty at each scored end, so each produces an
        # event book; the 2025-07-31 terminal finds it already flat (the
        # 2025-06-30 book was flattened at the 2025-07-24 scored end) and
        # produces no entry (recorded in the summary only)
        assert flat_dates == ["2020-09-01", "2023-02-09", "2025-07-24"]
        assert stream.summary["force_flat_dates"] == [
            "2020-09-01", "2023-02-09", "2025-07-24", "2025-07-31",
        ]
        for flat in flats:
            assert flat.targets == {}
            assert flat.gross == 0.0
            assert flat.cash_weight == 1.0
            assert flat.turnover_one_way > 0.0  # costed one-way exit

    def test_spec_example_june_2025_book_flattened_july_24(self, s0_sessions):
        inputs = s0_inputs(s0_sessions)
        anchor, _n, _c = build_arm_configs(inputs.spec)
        stream = generate_target_book(inputs, anchor)
        june = next(
            e for e in stream.entries
            if e.decision_date == "2025-06-30" and e.entry_type == "decision_fill"
        )
        assert june.fill_date == "2025-07-01"
        flat = next(
            e for e in stream.entries
            if e.entry_type == "force_flat" and e.fill_date == "2025-07-24"
        )
        # the flattening closes exactly the book the June decision opened
        assert flat.turnover_one_way == pytest.approx(june.gross, abs=1e-9)

    def test_fold_restart_from_flat(self, s0_sessions):
        inputs = s0_inputs(s0_sessions)
        anchor, _n, _c = build_arm_configs(inputs.spec)
        stream = generate_target_book(inputs, anchor)
        entries = stream.entries
        for i, entry in enumerate(entries):
            if entry.entry_type == "force_flat":
                if i + 1 >= len(entries):
                    continue  # final force-flat (2025-07-24) ends the stream
                following = entries[i + 1]
                assert following.entry_type == "decision_fill"
                assert following.fill_date > entry.fill_date
                # re-entering from flat: full gross is new turnover
                assert following.turnover_one_way == pytest.approx(
                    following.gross, abs=1e-9
                )

    def test_aug_2020_decision_fills_and_flattens_same_close(self, s0_sessions):
        # fold 1's last slot: decision 2020-08-31 fills 2020-09-01, which is
        # exactly the fold-1 scored end -> the holding is force-flattened at
        # that same session's close (fill entry strictly before the flat)
        inputs = s0_inputs(s0_sessions)
        anchor, _n, _c = build_arm_configs(inputs.spec)
        stream = generate_target_book(inputs, anchor)
        entries = stream.entries
        pair = [
            (i, e)
            for i, e in enumerate(entries)
            if e.fill_date == "2020-09-01"
        ]
        assert [e.entry_type for _i, e in pair] == [
            "decision_fill", "force_flat",
        ]
        (fill_i, fill), (flat_i, flat) = pair
        assert fill.decision_date == "2020-08-31"
        assert fill_i < flat_i
        assert flat.turnover_one_way == pytest.approx(fill.gross, abs=1e-9)

    def test_no_entries_inside_purge_gaps(self, s0_sessions):
        inputs = s0_inputs(s0_sessions)
        anchor, _n, _c = build_arm_configs(inputs.spec)
        stream = generate_target_book(inputs, anchor)
        for purge_window in (
            ("2020-09-02", "2020-09-09"),
            ("2023-02-10", "2023-02-16"),
            ("2025-07-25", "2025-07-31"),
        ):
            for entry in stream.entries:
                assert not (
                    purge_window[0] <= entry.fill_date <= purge_window[1]
                ), f"entry {entry.fill_date} inside purge gap {purge_window}"


class TestBookInvariants:
    def test_long_only_gross_cap_cash_residual_all_arms(self, s0_sessions):
        inputs = s0_inputs(s0_sessions)
        for config in build_arm_configs(inputs.spec):
            stream = generate_target_book(inputs, config)
            assert stream.entries
            for entry in stream.entries:
                for weight in entry.targets.values():
                    assert weight >= 0.0, (config.arm_id, entry.fill_date)
                    assert weight <= 0.35 + 1e-9, (
                        config.arm_id, entry.fill_date, weight
                    )
                assert entry.gross <= 1.0 + 1e-9
                assert abs(entry.cash_weight + entry.gross - 1.0) <= 1e-9
                assert entry.cash_weight >= -1e-9

    def test_gross_is_sum_of_targets(self, s0_sessions):
        inputs = s0_inputs(s0_sessions)
        for config in build_arm_configs(inputs.spec):
            stream = generate_target_book(inputs, config)
            for entry in stream.entries:
                assert entry.gross == pytest.approx(
                    sum(entry.targets.values()), abs=1e-12
                )

    def test_full_rotation_turnover_convention(self, s0_sessions):
        inputs = s0_inputs(s0_sessions)
        anchor, _n, _c = build_arm_configs(inputs.spec)
        stream = generate_target_book(inputs, anchor)
        fills = [e for e in stream.entries if e.entry_type == "decision_fill"]
        # first valid decision enters from flat: one-way turnover = gross 1.0
        assert fills[0].turnover_one_way == pytest.approx(1.0, abs=1e-9)

    def test_neighbour_inverse_vol_weights_differ_from_equal(self, s0_sessions):
        inputs = s0_inputs(s0_sessions)
        _anchor, neighbour, _c = build_arm_configs(inputs.spec)
        n_stream = generate_target_book(inputs, neighbour)
        n_first = next(
            e for e in n_stream.entries if e.entry_type == "decision_fill"
        )
        # with non-degenerate synthetic vols the inverse-vol book is not
        # the equal-weight book (different mechanism lever, same selection
        # universe): distinct per-symbol sigma must move weights off 1/3
        assert any(
            abs(weight - 1.0 / 3.0) > 1e-6
            for weight in n_first.targets.values()
        )
