"""Clock, lookahead, ramp, fill-series and digest tests for family A4.

Mandated Z5 areas covered here:
- one-event lag (decision at t uses data through t; fill at the NEXT session);
- no-lookahead structural test (mutating future data leaves earlier
  decisions unchanged);
- ramp suppression (first 253 sessions -> no decisions);
- raw-fill vs TR separation (a distribution gap in the raw series still
  fills at the raw price and never touches features);
- identity/config digest stability + double-generation equality.
"""

from __future__ import annotations

import copy
import datetime as dt
import hashlib

import pytest

from research.assets.stocks.calendar import US_EQUITY_REGULAR_V1
from research.stocks_free_v2.family_a4 import (
    FROZEN_SPEC_FILE_SHA256,
    arm_config_digest,
    build_arm_configs,
    canonical_json,
    compute_symbol_features,
    generate_target_book,
)
from tests.stocks_free_v2.family_a4._fixtures import hand_spec, make_inputs

CALENDAR = US_EQUITY_REGULAR_V1
FORMATION = 252
SKIP = 21


class TestOneEventLag:
    def test_fill_is_next_regular_session(self, hand_inputs):
        anchor, _n, _c = build_arm_configs(hand_inputs.spec)
        stream = generate_target_book(hand_inputs, anchor)
        fills = [e for e in stream.entries if e.entry_type == "decision_fill"]
        assert fills
        for entry in fills:
            expected = CALENDAR.next_session(
                dt.date.fromisoformat(entry.decision_date)
            ).start_utc.date().isoformat()
            assert entry.fill_date == expected
            assert entry.fill_date > entry.decision_date

    def test_first_decision_and_fill_dates(self, hand_inputs):
        anchor, _n, _c = build_arm_configs(hand_inputs.spec)
        stream = generate_target_book(hand_inputs, anchor)
        first = next(
            e for e in stream.entries if e.entry_type == "decision_fill"
        )
        assert first.decision_date == "2019-01-31"  # first month-end with a
        # full 253-session window (spec warmup-extension disclosure)
        assert first.fill_date == "2019-02-01"      # next regular session

    def test_no_same_bar_fill(self, hand_inputs):
        anchor, _n, _c = build_arm_configs(hand_inputs.spec)
        for config in build_arm_configs(hand_inputs.spec):
            stream = generate_target_book(hand_inputs, config)
            for entry in stream.entries:
                if entry.entry_type == "decision_fill":
                    assert entry.fill_date != entry.decision_date


class TestNoLookahead:
    def test_future_tr_mutation_leaves_stream_unchanged(self, hand_inputs):
        anchor, _n, _c = build_arm_configs(hand_inputs.spec)
        baseline = generate_target_book(hand_inputs, anchor)

        mutated_tr = {
            symbol: {
                day: (value * 2.7 if day > "2019-01-31" else value)
                for day, value in series.items()
            }
            for symbol, series in hand_inputs.tr.items()
        }
        mutated = make_inputs(
            hand_inputs.spec,
            hand_inputs.sessions,
            mutated_tr,
            hand_inputs.raw_close,
            hand_inputs.partition,
        )
        after = generate_target_book(mutated, anchor)
        # every decision at/before the mutation point is byte-identical:
        # features at t read bars <= t only, so future bars cannot leak in
        assert baseline.to_canonical_json() == after.to_canonical_json()

    def test_future_raw_mutation_leaves_targets_unchanged(self, hand_inputs):
        anchor, _n, _c = build_arm_configs(hand_inputs.spec)
        baseline = generate_target_book(hand_inputs, anchor)
        mutated_raw = {
            symbol: {
                day: (value * 0.5 if day > "2019-02-15" else value)
                for day, value in series.items()
            }
            for symbol, series in hand_inputs.raw_close.items()
        }
        mutated = make_inputs(
            hand_inputs.spec,
            hand_inputs.sessions,
            hand_inputs.tr,
            mutated_raw,
            hand_inputs.partition,
        )
        after = generate_target_book(mutated, anchor)
        base_fills = [e for e in baseline.entries if e.fill_date <= "2019-02-15"]
        after_fills = [e for e in after.entries if e.fill_date <= "2019-02-15"]
        assert [e.to_canonical_dict() for e in base_fills] == [
            e.to_canonical_dict() for e in after_fills
        ]

    def test_feature_reads_never_touch_bars_after_t(self, hand_inputs):
        # structural: drop every bar strictly after a decision session ->
        # the features at that session are unchanged (mom uses t-21/t-252,
        # sigma uses [t-252, t-21]; only readiness needs bar t itself)
        sessions = hand_inputs.sessions
        index = sessions.index("2019-01-31")
        tr = hand_inputs.tr["AAA"]
        full = compute_symbol_features(
            tr=tr, sessions=sessions, index=index,
            formation_sessions=FORMATION, skip_sessions=SKIP, symbol="AAA",
        )
        truncated_sessions = sessions[: index + 1]  # bars <= t only
        truncated_tr = {d: v for d, v in tr.items() if d <= sessions[index]}
        after = compute_symbol_features(
            tr=truncated_tr, sessions=truncated_sessions, index=index,
            formation_sessions=FORMATION, skip_sessions=SKIP, symbol="AAA",
        )
        assert after.ready is True
        assert after.mom == full.mom
        assert after.sigma == full.sigma
        assert after.mra == full.mra


class TestRampSuppression:
    def test_first_253_sessions_have_no_decisions(self, hand_inputs):
        anchor, _n, _c = build_arm_configs(hand_inputs.spec)
        from research.stocks_free_v2.family_a4 import build_decision_slots

        slots = build_decision_slots(hand_inputs)
        suppressed = [s for s in slots if s.suppressed]
        valid = [s for s in slots if not s.suppressed]
        assert suppressed, "expected warmup-extension slots"
        for slot in suppressed:
            assert slot.decision_index + 1 < 253
            assert slot.suppressed_reason == "INSUFFICIENT_LOOKBACK"
        for slot in valid:
            assert slot.decision_index >= 252  # first full window at idx 252
        # spec ramp: the suppressed slots are exactly the 2018 month-ends
        assert [s.decision_date for s in suppressed] == [
            "2018-04-30", "2018-05-31", "2018-06-29", "2018-07-31",
            "2018-08-31", "2018-09-28", "2018-10-31", "2018-11-30",
            "2018-12-31",
        ]
        # and they produce no entries at all
        stream = generate_target_book(hand_inputs, anchor)
        for entry in stream.entries:
            assert entry.decision_date not in {
                s.decision_date for s in suppressed
            }

    def test_no_truncated_lookback_fallback(self, hand_inputs):
        # at index 251 (2018-12-31) the 253-window does not exist: the
        # feature must be not-ready, never truncated
        sessions = hand_inputs.sessions
        features = compute_symbol_features(
            tr=hand_inputs.tr["AAA"], sessions=sessions, index=251,
            formation_sessions=FORMATION, skip_sessions=SKIP, symbol="AAA",
        )
        assert features.ready is False
        assert features.not_ready_reason == "INSUFFICIENT_LOOKBACK"
        assert features.mom is None and features.sigma is None


class TestRawFillTrSeparation:
    def test_distribution_gap_fills_at_raw_price(self, hand_inputs):
        anchor, _n, _c = build_arm_configs(hand_inputs.spec)
        stream = generate_target_book(hand_inputs, anchor)
        for entry in stream.entries:
            if entry.entry_type != "decision_fill":
                continue
            for symbol, ref in entry.fill_ref_prices.items():
                raw_value = hand_inputs.raw_close[symbol][entry.fill_date]
                tr_value = hand_inputs.tr[symbol][entry.fill_date]
                assert ref == raw_value
                # the fixture's distribution gap (session idx >= 150) makes
                # raw differ from TR on every fill date: fills are RAW, and
                # the gapped series never leaked into features
                if entry.fill_date >= hand_inputs.sessions[150]:
                    assert ref != pytest.approx(tr_value, rel=1e-6)

    def test_gap_does_not_change_targets(self, hand_sessions):
        # identical TR, raw WITHOUT the distribution gap: identical books
        from tests.stocks_free_v2.family_a4._fixtures import (
            hand_partition,
            hand_tr,
            make_inputs,
        )

        anchor, _n, _c = build_arm_configs(hand_spec())
        tr = hand_tr(hand_sessions)
        raw_clean = {
            symbol: dict(series) for symbol, series in tr.items()
        }  # raw == TR (no gap)
        clean = make_inputs(
            hand_spec(), hand_sessions, tr, raw_clean, hand_partition(hand_sessions)
        )
        gapped = make_inputs(
            hand_spec(),
            hand_sessions,
            tr,
            {
                s: {d: v * 0.97 if d >= hand_sessions[150] else v
                    for d, v in series.items()}
                for s, series in tr.items()
            },
            hand_partition(hand_sessions),
        )
        a = generate_target_book(clean, anchor).to_canonical_dict()
        b = generate_target_book(gapped, anchor).to_canonical_dict()
        # only the raw fill reference prices differ; targets identical
        for entry_a, entry_b in zip(a["entries"], b["entries"]):
            assert entry_a["targets"] == entry_b["targets"]
            assert entry_a["gross"] == entry_b["gross"]
            assert entry_a["turnover_one_way"] == entry_b["turnover_one_way"]
            if entry_a["entry_type"] == "decision_fill":
                for symbol, ref in entry_a["fill_ref_prices"].items():
                    assert entry_b["fill_ref_prices"][symbol] == pytest.approx(
                        ref * 0.97, rel=1e-12
                    )


class TestDigestStability:
    def test_frozen_spec_file_bytes_unchanged(self, real_spec):
        from pathlib import Path

        from research.stocks_free_v2.family_a4 import FROZEN_SPEC_REL_PATH

        root = Path(__file__).resolve().parents[3]
        spec_bytes = (root / FROZEN_SPEC_REL_PATH).read_bytes()
        assert hashlib.sha256(spec_bytes).hexdigest() == FROZEN_SPEC_FILE_SHA256

    def test_arm_config_digest_stable_across_double_generation(self, real_spec):
        d1 = arm_config_digest(real_spec)
        d2 = arm_config_digest(copy.deepcopy(load_real_spec_again()))
        assert d1 == d2
        # canonical sha256 over the frozen spec JSON: independent recompute
        assert d1 == hashlib.sha256(
            canonical_json(real_spec).encode("utf-8")
        ).hexdigest()

    def test_digest_recorded_in_module_output(self, hand_inputs):
        anchor, _n, _c = build_arm_configs(hand_inputs.spec)
        stream = generate_target_book(hand_inputs, anchor)
        assert stream.arm_config_digest == arm_config_digest(hand_inputs.spec)
        assert stream.family_id == "A4_XSEC_ETF_RELATIVE_MOMENTUM"
        assert stream.calendar_id == CALENDAR.calendar_id


class TestDoubleGenerationEquality:
    def test_identical_inputs_identical_canonical_json(self, hand_inputs):
        for config in build_arm_configs(hand_inputs.spec):
            first = generate_target_book(hand_inputs, config).to_canonical_json()
            second = generate_target_book(hand_inputs, config).to_canonical_json()
            assert first == second

    def test_rebuilt_inputs_identical_canonical_json(self, hand_sessions):
        from tests.stocks_free_v2.family_a4._fixtures import (
            hand_partition,
            hand_raw,
            hand_spec,
            hand_tr,
            make_inputs,
        )

        for config in build_arm_configs(hand_spec()):
            a = generate_target_book(
                make_inputs(
                    hand_spec(), hand_sessions, hand_tr(hand_sessions),
                    hand_raw(hand_sessions), hand_partition(hand_sessions),
                ),
                config,
            ).to_canonical_json()
            b = generate_target_book(
                make_inputs(
                    hand_spec(), hand_sessions, hand_tr(hand_sessions),
                    hand_raw(hand_sessions), hand_partition(hand_sessions),
                ),
                config,
            ).to_canonical_json()
            assert a == b


def load_real_spec_again() -> dict:
    """Second independent load of the frozen spec (digest stability)."""
    from research.stocks_free_v2.family_a4 import load_frozen_spec

    return load_frozen_spec()
