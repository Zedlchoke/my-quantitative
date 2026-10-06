"""Journal tests: PIT feature snapshots, AMBIGUOUS_ORDER handling, censoring,
frozen breakeven tolerance, MAE/MFE."""
import datetime as dt
import json
import unittest

from futbt.journal import (FillRecord, JournalRecord, PITViolationError,
                           TradeJournal, validate_feature_snapshot)
from futbt.taxonomy import PolicyError


def _fill(session, price=100.0, qty=1):
    return FillRecord(session=session, local_symbol="ESH6", conid=1,
                      signed_qty=qty, price=price,
                      cost_breakdown={"x": 1}, cost_total_usd=2.24,
                      fill_timing="next_open")


def _record(**kw):
    base = dict(
        trade_id="ES-0001", symbol="ES", decision_session=dt.date(2026, 1, 5),
        entry_decision_reason="breakout", veto_reason=None, direction=1,
        qty=1, entry_fill=_fill(dt.date(2026, 1, 6)),
        exit_fill=_fill(dt.date(2026, 1, 10), qty=-1),
        exit_type="TP", exit_session=dt.date(2026, 1, 10),
        feature_snapshot={"mom10": (0.012, dt.date(2026, 1, 5))},
        gross_pnl_usd=50.0, net_pnl_usd=45.52,
        cost_components_total_usd=4.48,
    )
    base.update(kw)
    return JournalRecord(**base)


class TestFeatureSnapshotPIT(unittest.TestCase):
    def test_ok_with_asof_on_decision_day(self):
        validate_feature_snapshot({"a": (1.0, dt.date(2026, 1, 5))},
                                  dt.date(2026, 1, 5))

    def test_future_asof_rejected(self):
        with self.assertRaisesRegex(PITViolationError, "AFTER"):
            validate_feature_snapshot(
                {"a": (1.0, dt.date(2026, 1, 6))}, dt.date(2026, 1, 5))

    def test_missing_asof_rejected(self):
        with self.assertRaisesRegex(PITViolationError, "no as-of"):
            validate_feature_snapshot({"a": 1.0}, dt.date(2026, 1, 5))

    def test_parallel_asof_key_style(self):
        validate_feature_snapshot(
            {"a": 1.0, "a__asof": dt.date(2026, 1, 4)}, dt.date(2026, 1, 5))

    def test_record_construction_validates_features(self):
        with self.assertRaises(PITViolationError):
            _record(feature_snapshot={"leak": (1.0, dt.date(2026, 1, 7))})


class TestAmbiguousOrder(unittest.TestCase):
    def test_ambiguous_record_never_carries_point_pnl(self):
        j = TradeJournal(breakeven_tolerance_usd=5.0)
        rec = _record(
            exit_type="TP_SL_SAME_BAR", gross_pnl_usd=None, net_pnl_usd=None,
            ambiguity="AMBIGUOUS_ORDER",
            scenario_bounds={"tp_first": 45.0, "sl_first": -60.0})
        j.add(rec)
        self.assertNotIn(rec, j.point_pnl_records())
        self.assertEqual(j.summary()["n_ambiguous"], 1)

    def test_journal_refuses_point_pnl_on_ambiguous(self):
        j = TradeJournal(breakeven_tolerance_usd=5.0)
        with self.assertRaisesRegex(PolicyError, "hit order"):
            j.add(_record(ambiguity="AMBIGUOUS_ORDER",
                          scenario_bounds={"tp_first": 1.0, "sl_first": -1.0}))

    def test_scenario_bounds_must_have_both_keys(self):
        j = TradeJournal(breakeven_tolerance_usd=5.0)
        with self.assertRaisesRegex(PolicyError, "scenario_bounds missing"):
            j.add(_record(exit_type="TP_SL_SAME_BAR", gross_pnl_usd=None,
                          net_pnl_usd=None, ambiguity="AMBIGUOUS_ORDER",
                          scenario_bounds={"tp_first": 1.0}))

    def test_bounds_only_policy_is_default(self):
        j = TradeJournal(breakeven_tolerance_usd=0.0)
        self.assertEqual(j.scenario_policy, "bounds_only")
        with self.assertRaisesRegex(PolicyError, "scenario_policy"):
            TradeJournal(breakeven_tolerance_usd=0.0, scenario_policy="mean")


class TestCensoring(unittest.TestCase):
    def test_censored_record_has_no_resolved_exit(self):
        j = TradeJournal(breakeven_tolerance_usd=0.0)
        rec = _record(exit_type=None, exit_session=None, exit_fill=None,
                      gross_pnl_usd=None, net_pnl_usd=None,
                      right_censored=True)
        j.add(rec)
        self.assertEqual(j.summary()["n_right_censored"], 1)
        with self.assertRaisesRegex(PolicyError, "censored"):
            j.add(_record(right_censored=True))  # censored but TP resolved

    def test_end_of_data_exit_counts_as_censoring_pattern(self):
        j = TradeJournal(breakeven_tolerance_usd=0.0)
        rec = _record(exit_type="END_OF_DATA", exit_session=None,
                      exit_fill=None, gross_pnl_usd=None, net_pnl_usd=None,
                      right_censored=True)
        j.add(rec)
        self.assertEqual(j.summary()["by_exit"].get("END_OF_DATA"), 1)


class TestFrozenBreakevenTolerance(unittest.TestCase):
    def test_frozen_at_construction_and_stamped(self):
        j = TradeJournal(breakeven_tolerance_usd=25.0)
        j.add(_record())
        doc = json.loads(j.to_json())
        self.assertEqual(doc["journal_header"]["breakeven_tolerance_usd_frozen"],
                         25.0)
        # tolerance governs classification; no post-hoc knobs exist
        self.assertEqual(j.assert_breakeven(10.0), "BREAKEVEN_WITHIN_FROZEN_TOLERANCE")
        self.assertEqual(j.assert_breakeven(30.0), "PROFIT")
        self.assertEqual(j.assert_breakeven(-30.0), "LOSS")

    def test_negative_tolerance_refused(self):
        with self.assertRaises(PolicyError):
            TradeJournal(breakeven_tolerance_usd=-1.0)


class TestSummaryDescriptiveOnly(unittest.TestCase):
    def test_summary_has_counts_not_performance(self):
        j = TradeJournal(breakeven_tolerance_usd=0.0)
        j.add(_record())
        j.add(_record(trade_id="ES-0002", veto_reason="cost_too_high",
                      direction=0, qty=0, entry_fill=None, exit_fill=None,
                      exit_type=None, exit_session=None, gross_pnl_usd=None,
                      net_pnl_usd=None, feature_snapshot={}))
        s = j.summary()
        self.assertEqual(s["n_records"], 2)
        self.assertEqual(s["n_vetoed"], 1)
        self.assertEqual(s["by_exit"]["TP"], 1)
        for banned in ("sharpe", "return", "win_rate", "cagr"):
            self.assertNotIn(banned, json.dumps(s).lower())


if __name__ == "__main__":
    unittest.main()
