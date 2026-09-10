"""FOREX-FREE-V9 runner + driver tests (frozen families FXFV9-A5-P1 and
FXFV9-A5-P2).

SYNTHETIC hand-computed fixtures ONLY -- no production outcomes, no real
data bytes required (the suite must pass in a fresh twin worktree without
the gitignored staged/price copies), no scored execution anywhere.  The
diagnostic-smoke mode used for the twin test books SYNTHETIC trades from
the deterministic fixture builder; it never reads real conditioning bytes.

Hand-verified fixture comments carry the frozen-mechanics hand tables:
min-hold-blocked hysteresis, the 63-clock cap with immediate next-clock
re-entry, sign-flip exits, the 24-observation OLS trend, and the
switch-exactly-at-vintage mutation property.
"""
import copy
import io
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from bisect import bisect_left
from collections import OrderedDict
from datetime import date, timedelta

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
                                    ".."))
sys.path.insert(0, ROOT)

from research.assets.forex_free_v3 import accounting as K            # noqa: E402
from research.assets.forex_free_v9 import conditioning as C          # noqa: E402
from research.assets.forex_free_v9 import exec_driver_v9 as D        # noqa: E402
from research.assets.forex_free_v9 import family_a5p1_v9 as F1       # noqa: E402
from research.assets.forex_free_v9 import family_a5p2_v9 as F2       # noqa: E402
from research.assets.forex_free_v9 import family_common as FC        # noqa: E402

VENV_PY = sys.executable
DRIVER = os.path.join(ROOT, "research", "assets", "forex_free_v9",
                      "exec_driver_v9.py")
FIXTURE_BUILDER = os.path.join(ROOT, "research", "assets", "forex_free_v9",
                               "synthetic_fixture_v9.py")

SYNTH_ROOT = None
SYNTH_DATA = None
SYNTH_PATHS = None


def setUpModule():
    global SYNTH_ROOT, SYNTH_DATA, SYNTH_PATHS
    SYNTH_ROOT = tempfile.mkdtemp(prefix="v9_tests_synth_")
    SYNTH_DATA = os.path.join(SYNTH_ROOT, "synthetic_data")
    subprocess.run([VENV_PY, FIXTURE_BUILDER, SYNTH_DATA],
                   check=True, capture_output=True)
    SYNTH_PATHS = {
        "price_dir": SYNTH_DATA,
        "cpi_dir": os.path.join(SYNTH_DATA, "cpi"),
        "gb_calendar_path": os.path.join(SYNTH_DATA, "cpi", "calendars",
                                         "gb_cal.json"),
        "ca_calendar_path": os.path.join(SYNTH_DATA, "cpi", "calendars",
                                         "ca_cal_v3.json"),
        "announcement_ledger": os.path.join(SYNTH_DATA, "ledger.jsonl"),
        "s0_start": date(2018, 4, 4), "s0_end": date(2019, 12, 31),
        "enforce_real_grid": False,
    }


def tearDownModule():
    shutil.rmtree(SYNTH_ROOT, ignore_errors=True)


def weekday_grid(start: date, end: date):
    d, out = start, []
    while d <= end:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


# --------------------------------------------------------------- OLS trend #
class TestOlsHandComputed(unittest.TestCase):
    """Hand-computed OLS trend-at-last (the 24/8-obs trailing window)."""

    def test_hand_computed_three_points(self):
        # window [1,2,3]: ybar 2, xbar 1, sxx 2, sxy 2 -> slope 1,
        # fitted at the LAST ordinal (x=2): 2 + 1*(2-1) = 3.0
        self.assertAlmostEqual(C.ols_fitted_last([1.0, 2.0, 3.0]), 3.0,
                               places=12)

    def test_hand_computed_four_points(self):
        # values [1,3,2,5]: ybar 2.75, xbar 1.5, sxx 5.0, sxy 5.5 ->
        # slope 1.1, fitted at x=3: 2.75 + 1.1*1.5 = 4.4
        self.assertAlmostEqual(C.ols_fitted_last([1.0, 3.0, 2.0, 5.0]), 4.4,
                               places=12)

    def test_linear_series_trend_equals_last(self):
        # pi = 0.01*i (perfect line): the fitted value at the last print's
        # period IS the last value -> the surprise vanishes identically
        hist = [0.01 * i for i in range(24)]
        self.assertAlmostEqual(C.ols_fitted_last(hist), 0.23, places=12)

    def test_constant_window_flat_trend(self):
        self.assertAlmostEqual(C.ols_fitted_last([5.0, 5.0, 5.0]), 5.0,
                               places=12)

    def test_window_too_short_fails_closed(self):
        with self.assertRaises(C.DataBlocked):
            C.ols_fitted_last([1.0])

    def test_affine_regressor_invariance(self):
        # the frozen 'trend value at the latest print's period' must not
        # depend on the regressor's affine parametrization (ordinal vs
        # months): compare against an explicit x = 12*i computation
        vals = [0.012, 0.019, 0.024, 0.020, 0.027, 0.031, 0.026, 0.033]
        w = len(vals)
        x_bar = (w - 1) / 2.0
        y_bar = math.fsum(vals) / w
        xs = [12.0 * i for i in range(w)]
        mx = math.fsum(xs) / w
        sxx = math.fsum((x - mx) ** 2 for x in xs)
        sxy = math.fsum((x - mx) * (v - y_bar) for x, v in zip(xs, vals))
        expect = y_bar + (sxy / sxx) * (xs[-1] - mx)
        self.assertAlmostEqual(C.ols_fitted_last(vals), expect, places=12)


# ------------------------------------------------------ table/calendar parse #
class TestLoadersHandComputed(unittest.TestCase):
    def test_parse_month_both_formats(self):
        self.assertEqual(C.parse_month("1988 JAN"), date(1988, 1, 1))
        self.assertEqual(C.parse_month("1914-01"), date(1914, 1, 1))

    def test_add_months_year_boundary(self):
        self.assertEqual(C.add_months(date(2018, 11, 1), 3),
                         date(2019, 2, 1))
        self.assertEqual(C.add_months(date(2018, 1, 1), -12),
                         date(2017, 1, 1))

    def test_placeholder_is_mid_next_month(self):
        self.assertEqual(C.placeholder_release(date(2017, 12, 1)),
                         date(2018, 1, 15))
        self.assertEqual(C.placeholder_release(date(2018, 1, 1)),
                         date(2018, 2, 15))

    def test_gb_calendar_hand_table(self):
        # {"reference_period": "january2018", "release_date_display":
        #  "13 February 2018"} -> print 2018-01 binds at 2018-02-13
        tmp = tempfile.mkdtemp()
        try:
            p = os.path.join(tmp, "gb.json")
            with open(p, "w") as f:
                json.dump([{"reference_period": "january2018",
                            "release_date_display": "13 February 2018"},
                           {"reference_period": "december2019",
                            "release_date_display": "15 January 2020"}], f)
            cal = C.load_gb_calendar(p)
            self.assertEqual(cal[date(2018, 1, 1)], date(2018, 2, 13))
            self.assertEqual(cal[date(2019, 12, 1)], date(2020, 1, 15))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_ca_calendar_reference_is_prior_month(self):
        # StatCan releases month M during M+1: the 2018-03-23 release
        # carries the 2018-02 print
        tmp = tempfile.mkdtemp()
        try:
            p = os.path.join(tmp, "ca.json")
            with open(p, "w") as f:
                json.dump([{"release_date": "2018-03-23",
                            "cpi_products": ["18100004"]}], f)
            cal = C.load_ca_calendar(p)
            self.assertEqual(cal[date(2018, 2, 1)], date(2018, 3, 23))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_ons_table_skips_annual_and_metadata(self):
        # the real staged file carries 8 metadata lines + annual rows
        # ("2013","92.4") + monthly rows ("1988 JAN","48.4")
        tmp = tempfile.mkdtemp()
        try:
            p = os.path.join(tmp, "ons.csv")
            with open(p, "w") as f:
                f.write('"Title","CPI INDEX 00: ALL ITEMS 2015=100"\n'
                        '"CDID","D7BT"\n'
                        '"Release date","19-08-2026"\n'
                        '"2013","92.4"\n'
                        '"2013 DEC","48.3"\n'
                        '"2014 JAN","48.4"\n')
            t = C.load_ons_d7bt(p)
            self.assertEqual(t, {date(2013, 12, 1): 48.3,
                                 date(2014, 1, 1): 48.4})
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_statcan_tidy(self):
        tmp = tempfile.mkdtemp()
        try:
            p = os.path.join(tmp, "ca.csv")
            with open(p, "w") as f:
                f.write("ref_month,index_2002_100\n1914-01,6.0\n2018-02,130.1\n")
            t = C.load_statcan_csv(p)
            self.assertEqual(t[date(1914, 1, 1)], 6.0)
            self.assertEqual(t[date(2018, 2, 1)], 130.1)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_fred_vintaged_both_formats_and_dots(self):
        rows_nested = {"observations": [
            {"realtime_start": "2020-01-01", "realtime_end": "2030-01-01",
             "date": "2019-10-01", "value": "120.5"},
            {"realtime_start": "2020-02-01", "realtime_end": "2030-01-01",
             "date": "2019-10-01", "value": "120.7"},
            {"realtime_start": "2020-01-01", "realtime_end": "2030-01-01",
             "date": "2019-11-01", "value": "."}]}
        tmp = tempfile.mkdtemp()
        try:
            p = os.path.join(tmp, "a.json")
            with open(p, "w") as f:
                json.dump(rows_nested, f)
            by_obs = C.load_fred_vintaged(p)
            self.assertEqual(by_obs[date(2019, 10, 1)],
                             [(date(2020, 1, 1), 120.5),
                              (date(2020, 2, 1), 120.7)])
            self.assertNotIn(date(2019, 11, 1), by_obs)   # "." never a value
            p2 = os.path.join(tmp, "b.json")
            with open(p2, "w") as f:
                json.dump(rows_nested["observations"], f)
            by_obs2 = C.load_fred_vintaged(p2)            # flat list format
            self.assertEqual(C.first_binding_rt(by_obs2[date(2019, 10, 1)]),
                             date(2020, 1, 1))
            # as-of curve: latest realtime_start <= d switches EXACTLY there
            self.assertEqual(C.curve_value(by_obs[date(2019, 10, 1)],
                                           date(2020, 1, 15)), 120.5)
            self.assertEqual(C.curve_value(by_obs[date(2019, 10, 1)],
                                           date(2020, 2, 1)), 120.7)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_fail_closed_on_missing(self):
        with self.assertRaises(C.DataBlocked):
            C.load_fred_vintaged(os.path.join(tempfile.mkdtemp(), "no.json"))
        with self.assertRaises(C.DataBlocked):
            C.load_ons_d7bt(os.path.join(tempfile.mkdtemp(), "no.csv"))


# --------------------------------------- y/y + surprise legs (hand tables) #
class TestPiHandComputed(unittest.TestCase):
    def test_official_monthly_yy(self):
        leg = C.EconomyLeg("GB", "official", "monthly",
                           table={date(2018, 1, 1): 100.0,
                                  date(2019, 1, 1): 110.0})
        pi = leg.pi(date(2019, 1, 1), date(2019, 2, 13))
        self.assertAlmostEqual(pi, math.log(1.1), places=12)
        # denominator print not in the table -> None (carried, fail-closed)
        self.assertIsNone(leg.pi(date(2020, 1, 1), date(2020, 2, 13)))

    def test_official_availability_calendar_then_placeholder(self):
        cal = {date(2018, 1, 1): date(2018, 2, 13)}
        leg = C.EconomyLeg("GB", "official", "monthly",
                           table={date(2018, 1, 1): 100.0}, calendar=cal)
        self.assertEqual(leg.availability(date(2018, 1, 1)),
                         date(2018, 2, 13))            # pinned refinement
        self.assertEqual(leg.availability(date(2017, 12, 1)),
                         date(2018, 1, 15))            # placeholder class

    def test_fred_snapshot_curve_pi_and_revision_switch(self):
        # obs 2017-07 first binds 2017-08-15 at 100.0 (its only vintage).
        # obs 2018-01 first binds 2018-02-14 at 110.0 and is REVISED at the
        # 2018-03-14 vintage to 112.0.  Hand table (snapshot-curve pi):
        #   print 2018-02 (binds 2018-03-14, ON the revision day) computes
        #        y/y from the REVISED 112.0 -> ln(111.0/112.0)
        #   a decision reading obs 2018-01's curve BEFORE 2018-03-14 sees
        #        the first vintage 110.0, AFTER it sees 112.0 (switch at
        #        the vintage, never interpolated);
        #   pi of print 2018-01 is computed ONCE at its own 2018-02-14
        #        snapshot and never recomputed (as-bound).
        rows = {
            date(2017, 1, 1): [(date(2017, 8, 15), 100.0)],
            date(2017, 2, 1): [(date(2017, 8, 15), 105.0)],
            date(2018, 1, 1): [(date(2018, 2, 14), 110.0),
                               (date(2018, 3, 14), 112.0)],
            date(2018, 2, 1): [(date(2018, 3, 14), 111.0)],
        }
        leg = C.EconomyLeg("US", "fred", "monthly", rows_by_obs=rows)
        # y/y of print 2018-02 computed ON the revision day reads the
        # REVISED 112.0 denominator (rt <= d)
        self.assertAlmostEqual(
            leg.pi(date(2018, 2, 1), date(2018, 3, 14)),
            math.log(111.0 / 105.0), places=12)
        # y/y of print 2018-01 read against the pre-revision vintage value
        self.assertAlmostEqual(
            leg.pi(date(2018, 1, 1), date(2018, 2, 20)),
            math.log(110.0 / 100.0), places=12)
        # a LATER snapshot of the same obs curve switches at the vintage
        self.assertAlmostEqual(
            leg.pi(date(2018, 1, 1), date(2018, 3, 20)),
            math.log(112.0 / 100.0), places=12)

    def test_fred_availability_is_first_binding_rt(self):
        rows = {date(2018, 4, 1): [(date(2018, 7, 26), 1.0)]}
        leg = C.EconomyLeg("AU", "fred", "quarterly", rows_by_obs=rows)
        self.assertEqual(leg.availability(date(2018, 4, 1)), date(2018, 7, 26))
        # sham: +7 calendar days exactly
        self.assertEqual(leg.availability(date(2018, 4, 1), 7),
                         date(2018, 8, 2))

    def test_quarterly_yy_is_twelve_months_back(self):
        rows = {date(2018, 4, 1): [(date(2018, 7, 26), 110.0)],
                date(2017, 4, 1): [(date(2017, 7, 20), 100.0)]}
        leg = C.EconomyLeg("AU", "fred", "quarterly", rows_by_obs=rows)
        self.assertAlmostEqual(leg.pi(date(2018, 4, 1), date(2018, 7, 26)),
                               math.log(1.1), places=12)
        self.assertEqual(leg.trend_window(), 8)
        self.assertEqual(
            C.EconomyLeg("GB", "official", "monthly", table={}).trend_window(),
            24)


class TestMutationBindingExactShift(unittest.TestCase):
    """A print arriving k periods late must shift the consumed decision
    exactly k periods (I-Q mutation binding, AX2-C4)."""

    GRID = [d for d in [date(2018, 6, 4) + timedelta(days=i)
                        for i in range(10)] if d.weekday() < 5]

    def _legs(self, rt_for_print):
        rows = {date(2018, 6, 1): [(rt_for_print, 120.0)],
                date(2017, 6, 1): [(date(2017, 1, 1), 100.0)]}
        return OrderedDict((("X", C.EconomyLeg("X", "fred", "monthly",
                                               rows_by_obs=rows)),))

    def test_one_day_late_shifts_one_grid_clock(self):
        grid = self.GRID      # weekdays 2018-06-04(Mon) .. 2018-06-15(Fri)
        print_period = date(2018, 6, 1)

        def event_for(events):
            return next(e for e in events["X"] if e[1] == print_period)

        base = event_for(C.binding_events(self._legs(date(2018, 6, 8)), grid))
        mut = event_for(C.binding_events(self._legs(date(2018, 6, 11)), grid))
        # baseline: print binds at the first grid clock >= 06-08 (Fri);
        # mutated +1 weekday (Mon 06-11) -- availability is 06-08 in base
        # and 06-11 in mut
        self.assertEqual(base[0], date(2018, 6, 8))
        self.assertEqual(mut[0], date(2018, 6, 11))
        # the consumed decision moved EXACTLY k=1 business period (Fri ->
        # Mon on the FX grid), never absorbed, never early
        self.assertEqual(grid.index(mut[0]) - grid.index(base[0]), 1)

    def test_sham_shifts_every_binding_exactly_seven_days(self):
        legs = self._legs(date(2018, 6, 8))
        base = C.binding_events(legs, self.GRID, shift_days=0)
        sham = C.binding_events(legs, self.GRID, shift_days=7)
        for (c0, p0, a0), (c7, p7, a7) in zip(base["X"], sham["X"]):
            self.assertEqual(p0, p7)
            self.assertEqual((a7 - a0).days, 7)
            self.assertGreaterEqual(c7, c0)
            self.assertEqual(c7, self.GRID[bisect_left(self.GRID, a7)])


class TestWalkStatesHandComputed(unittest.TestCase):
    def test_surprise_hand_value_and_window_fill_boundary(self):
        # a CONSTANT y/y table (level multiplies by exp(0.0099) every 12
        # months, so pi = 0.0099 for every print with a full denominator):
        # the trailing-24 OLS trend equals the constant, so the surprise is
        # exactly 0.0 at every print once the 24-print window has filled.
        # Prints 2014-01..2014-12 have no y/y denominator -> pi None.
        # pi values exist from print 2015-01 (i=12); the 24th pi value
        # arrives with print 2016-12 (i=35, placeholder availability
        # 2017-01-15).  Hand table:
        #   grid clock 2016-12-01 / 2017-01-01 -> state None (< 24 values)
        #   grid clock 2017-02-01 -> ALL remaining prints bind at once
        #        (placeholder classes), state = surprise of the latest
        #        print = 0.0 exactly
        #   grid clock 2017-03-01 -> print 2017-01 binds; surprise 0.0
        table = {}
        for i in range(40):
            d = C.add_months(date(2014, 1, 1), i)
            table[d] = 100.0 * math.exp(0.0099 * (i // 12))
        leg = C.EconomyLeg("GB", "official", "monthly", table=table)
        grid = [date(2016, 12, 1), date(2017, 1, 1), date(2017, 2, 1),
                date(2017, 3, 1)]
        states = C.walk_surprise_states(OrderedDict((("GB", leg),)), grid)
        self.assertIsNone(states["GB"][date(2016, 12, 1)])
        self.assertIsNone(states["GB"][date(2017, 1, 1)])
        self.assertAlmostEqual(states["GB"][date(2017, 2, 1)], 0.0, places=12)
        self.assertAlmostEqual(states["GB"][date(2017, 3, 1)], 0.0, places=12)
        # piecewise constancy: the state changes ONLY at binding clocks
        # (the new print's pi is the same constant to float precision)
        pi_states = C.walk_pi_states(OrderedDict((("GB", leg),)), grid)
        self.assertAlmostEqual(pi_states["GB"][date(2017, 2, 1)],
                               pi_states["GB"][date(2017, 3, 1)], places=12)

    def test_surprise_none_before_window_fills(self):
        table = {C.add_months(date(2020, 1, 1), i): 100.0 + i
                 for i in range(10)}
        leg = C.EconomyLeg("GB", "official", "monthly", table=table)
        grid = [C.add_months(date(2021, 1, 1), i) for i in range(4)]
        states = C.walk_surprise_states(OrderedDict((("GB", leg),)), grid)
        for d in grid:
            self.assertIsNone(states["GB"][d])    # window never filled


# ------------------------------------------------- state machine (hand) #
class TestStateMachineHandComputed(unittest.TestCase):
    """Direct FC.simulate_arm walks on hand-computed driver fixtures."""

    PAIR = "GBPUSD"

    @staticmethod
    def _clocks(n):
        return [date(2020, 1, 1) + timedelta(days=i) for i in range(n)]

    def _run(self, zvals, fills_seq, entry=0.25, exit_band=0.15,
             pair="GBPUSD"):
        clocks = self._clocks(len(zvals))
        z = {d: v for d, v in zip(clocks, zvals)}
        fills = {pair: {d: p for d, p in zip(clocks, fills_seq)}}
        return FC.simulate_arm(z, fills, clocks, F1.side_for_driver,
                               pairs=(pair,), entry=entry,
                               exit_band=exit_band)

    def test_scenario_a_min_hold_blocks_hysteresis_hand_verified(self):
        # ---- HAND-VERIFIED (frozen rules: soft exits evaluate only after
        # a 5-binding-clock minimum hold) ----
        # clocks c0..c8, v = [None, +0.40, +0.10, +0.10, +0.10, +0.10,
        #                     +0.10, None, None]
        # c1: |0.40| >= 0.25 -> ENTRY long home (GBPUSD +1).
        # c2..c5: |0.10| <= 0.15 (hysteresis region) BUT hold is 1..4 < 5
        #     -> the exit does NOT fire; the position is HELD.
        # c6: hold = 5 -> hysteresis exit fires; hold_clocks = 5.
        # c7/c8: flat.
        zvals = [None, 0.40, 0.10, 0.10, 0.10, 0.10, 0.10, None, None]
        fills = [1.0, 1.1, 1.1, 1.1, 1.1, 1.1, 1.2, 1.2, 1.2]
        decisions, counts = self._run(zvals, fills)
        self.assertEqual(len(decisions), 1)
        tr = decisions[0]
        self.assertEqual(tr["side"], 1)               # long home = long pair
        self.assertEqual(tr["entry_day"], "2020-01-02")
        self.assertEqual(tr["exit_day"], "2020-01-07")
        self.assertEqual(tr["hold_clocks"], 5)
        self.assertEqual(tr["exit_reason"], "hysteresis")
        self.assertEqual(counts["exits_hysteresis"], 1)
        self.assertEqual(counts["exits_time_cap"], 0)

    def test_scenario_b_63_cap_with_immediate_next_clock_reentry(self):
        # v = +0.30 (in-region, above hysteresis) for c1..c70.
        # Entry at c1 (idx 1).  Cap rule: exit when hold >= 63 -> first true
        # at idx 64 (hold = 63).  Re-entry allowed at the NEXT clock (idx
        # 65, v still >= 0.25).  Second cap exit would be at idx 128, past
        # the grid end (71 clocks) -> terminal close at the last clock.
        zvals = [None] + [0.30] * 70
        fills = [1.0] * 71
        decisions, counts = self._run(zvals, fills)
        self.assertEqual(counts["entries"], 2)
        self.assertEqual(counts["exits_time_cap"], 1)
        self.assertEqual(counts["terminal_closes"], 1)
        self.assertEqual(decisions[0]["exit_reason"], "time_cap")
        self.assertEqual(decisions[0]["hold_clocks"], 63)
        # immediate re-entry at the NEXT clock (never the same clock)
        self.assertEqual(decisions[0]["exit_day"], "2020-03-05")   # idx 64
        self.assertEqual(decisions[1]["entry_day"], "2020-03-06")  # idx 65
        self.assertEqual(decisions[1]["exit_reason"], "terminal")

    def test_scenario_c_sign_flip_exit_after_min_hold(self):
        # entry +0.30 at c1; the driver flips sign at c6 (hold = 5): exit
        # reason "sign_flip" even though |−0.40| > exit band; re-entry at
        # c7 SHORT home (side -1 for GBPUSD on v < 0).
        zvals = [None, 0.30, 0.30, 0.30, 0.30, 0.30, -0.40, -0.40, None]
        fills = [1.0] * 9
        decisions, counts = self._run(zvals, fills)
        self.assertEqual(counts["entries"], 2)
        self.assertEqual(counts["exits_sign_flip"], 1)
        self.assertEqual(decisions[0]["exit_reason"], "sign_flip")
        self.assertEqual(decisions[0]["exit_day"], "2020-01-07")
        self.assertEqual(decisions[1]["side"], -1)    # short home
        self.assertEqual(decisions[1]["entry_day"], "2020-01-08")

    def test_scenario_d_sign_flip_before_min_hold_is_held(self):
        # entry +0.30 at c1; the driver flips at c2 (hold = 1 < 5): NO
        # exit; the position survives until the 63-cap / terminal.
        zvals = [None, 0.30, -0.40, -0.40, -0.40]
        fills = [1.0] * 5
        decisions, counts = self._run(zvals, fills)
        self.assertEqual(counts["entries"], 1)
        self.assertEqual(counts["exits_sign_flip"], 0)
        self.assertEqual(counts["terminal_closes"], 1)

    def test_max_one_position_and_threshold_boundaries(self):
        # persistent activation -> exactly ONE entry (no stacking);
        # |v| == entry (0.25 exactly) activates; |v| == exit band
        # (0.15 exactly) exits (after the min hold); a hair above the band
        # does not.
        z1 = [None] + [0.25] * 10
        d1, c1 = self._run(z1, [1.0] * 11)
        self.assertEqual(c1["entries"], 1)
        self.assertEqual(c1["terminal_closes"], 1)
        z2 = [None, 0.25] + [0.1500001] * 8
        d2, c2 = self._run(z2, [1.0] * 10)
        self.assertEqual(c2["exits_hysteresis"], 0)
        self.assertEqual(c2["terminal_closes"], 1)
        z3 = [None, 0.25, 0.25, 0.25, 0.25, 0.25, 0.15, None]
        d3, c3 = self._run(z3, [1.0] * 8)
        self.assertEqual(c3["exits_hysteresis"], 1)
        self.assertEqual(d3[0]["exit_day"], "2020-01-07")

    def test_direction_map_frozen(self):
        # LONG home on driver >= 0: GBPUSD/AUDUSD/NZDUSD long pair (+1),
        # USDCAD short pair (-1); v < 0 mirrors.
        for pair, expect in (("GBPUSD", 1), ("AUDUSD", 1), ("NZDUSD", 1),
                             ("USDCAD", -1)):
            self.assertEqual(F1.side_for_driver(0.0, pair), expect, pair)
            self.assertEqual(F1.side_for_driver(0.9, pair), expect, pair)
            self.assertEqual(F1.side_for_driver(-0.9, pair), -expect, pair)
        # P2's map is identical (frozen)
        for pair in FC.PAIRS:
            self.assertEqual(F2.side_for_driver(0.4, pair),
                             F1.side_for_driver(0.4, pair))

    def test_missing_entry_fill_skips_without_position(self):
        clocks = self._clocks(4)
        z = {clocks[0]: None, clocks[1]: 0.40, clocks[2]: 0.40,
             clocks[3]: 0.40}
        fills = {"GBPUSD": {clocks[0]: 1.0, clocks[2]: 1.1, clocks[3]: 1.1}}
        decisions, counts = FC.simulate_arm(
            z, fills, clocks, F1.side_for_driver, pairs=("GBPUSD",),
            entry=0.25, exit_band=0.15)
        self.assertEqual(counts["entries_fill_missing"], 1)
        self.assertEqual(counts["entries"], 1)
        self.assertEqual(decisions[0]["entry_day"], clocks[2].isoformat())

    def test_missing_exit_fill_does_not_fabricate_exit(self):
        clocks = self._clocks(9)
        vals = [None, 0.40, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10, None]
        z = {d: v for d, v in zip(clocks, vals)}
        fills = {"GBPUSD": {clocks[0]: 1.0, clocks[1]: 1.1,
                            clocks[7]: 1.2, clocks[8]: 1.2}}
        decisions, counts = FC.simulate_arm(
            z, fills, clocks, F1.side_for_driver, pairs=("GBPUSD",),
            entry=0.25, exit_band=0.15)
        # hand table: entry c1 (idx 1); hysteresis fires from c6 (hold 5)
        # but c6 AND c7... c7 HAS a fill: c6 fires with fill missing
        # (counted, stays open); c7 fires again WITH the fill -> the exit
        # happens at c7, hold 6.
        self.assertEqual(counts["exits_fill_missing"], 1)
        self.assertEqual(len(decisions), 1)
        self.assertEqual(decisions[0]["exit_day"], clocks[7].isoformat())
        self.assertEqual(decisions[0]["hold_clocks"], 6)


# --------------------------------------------------- folds (mechanical) #
class TestFoldSplitDeterminism(unittest.TestCase):
    def test_bounds_mechanical_thirds(self):
        self.assertEqual(FC.fold_bounds(1655), (551, 1103))
        self.assertEqual(FC.fold_bounds(3), (1, 2))
        self.assertEqual(FC.fold_bounds(1), (0, 0))

    def test_fold_assignment(self):
        b = FC.fold_bounds(10)          # (3, 6)
        self.assertEqual([FC.fold_of_index(i, b) for i in range(10)],
                         [1, 1, 1, 2, 2, 2, 3, 3, 3, 3])

    def test_fail_closed(self):
        with self.assertRaises(FC.DataBlocked):
            FC.fold_bounds(0)
        with self.assertRaises(FC.DataBlocked):
            FC.fold_bounds(10, n_folds=4)

    def test_deterministic(self):
        self.assertEqual(FC.fold_bounds(1640), FC.fold_bounds(1640))


# -------------------------------------------------- cost-once + dual book #
def _tiny_ledger(path, rates):
    with open(path, "w") as f:
        for area, rate in sorted(rates.items()):
            f.write(json.dumps({
                "area": area,
                "effective_time_utc": "2018-01-01T00:00:00+00:00",
                "announcement": {"operative_available_time_utc":
                                 "2018-01-01T00:00:00+00:00"},
                "new_value": rate,
            }) + "\n")


def _hand_trade(side=1, entry=1.10, exit_=1.21,
                entry_day="2019-06-03", exit_day="2019-06-05"):
    return {"pair": "GBPUSD", "side": side, "notional_usd": 10000.0,
            "entry_price": entry, "exit_price": exit_,
            "areas": ["GB", "US"],
            "entry_ts": f"{entry_day}T20:00:00+00:00",
            "exit_ts": f"{exit_day}T20:00:00+00:00"}


class TestCostOncePerFill(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.ledger = os.path.join(self.tmp, "l.jsonl")
        _tiny_ledger(self.ledger, {"GB": 1.25, "US": 2.00})
        from research.assets.forex_free_v5.family_a6p1 import (
            LedgerVintageReader, dedupe_ledger_rows, load_ledger_rows)
        self.reader = LedgerVintageReader(
            dedupe_ledger_rows(load_ledger_rows(self.ledger)))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_round_trip_charged_exactly_two_sides(self):
        tr = _hand_trade()
        gross = D.price_pnl_usd(tr)     # 10000*(1.21/1.10-1) = 1000
        self.assertAlmostEqual(gross, 1000.0, places=6)
        for tier in ("1.0", "1.5", "2.0"):
            pnls, skipped = D.book_trades([tr], tier, self.reader,
                                          strict=False)
            self.assertEqual(skipped, 0)
            expected = (gross
                        - 2.0 * K.bps_cost(tr["notional_usd"], float(tier))
                        + D.financing_adjustment_usd(self.reader, tr,
                                                     strict=False))
            self.assertAlmostEqual(pnls[0], expected, places=9)
        # hand-check the tier-2.0 primary: cost 2 x 3.00 = 6.00 USD
        self.assertEqual(K.bps_cost(10000.0, 2.0), 3.0)
        # financing hand-check: GB 1.25 - US 2.00 = -0.75%/yr over the two
        # accrual days [06-03, 06-04): 10000 * -0.0150 / 365
        fin = D.financing_adjustment_usd(self.reader, tr, strict=False)
        self.assertAlmostEqual(fin, 10000.0 * (-0.0150) / 365.0, places=9)

    def test_ladder_rebooks_not_rescales(self):
        tr = _hand_trade()
        p1, _ = D.book_trades([tr], "1.0", self.reader, strict=False)
        p2, _ = D.book_trades([tr], "2.0", self.reader, strict=False)
        c1 = 2.0 * K.bps_cost(10000.0, 1.0)
        c2 = 2.0 * K.bps_cost(10000.0, 2.0)
        self.assertAlmostEqual(p2[0], p1[0] + (c1 - c2), places=9)

    def test_financing_flips_with_side(self):
        a = D.financing_adjustment_usd(self.reader, _hand_trade(side=1),
                                       strict=False)
        b = D.financing_adjustment_usd(self.reader, _hand_trade(side=-1),
                                       strict=False)
        self.assertAlmostEqual(a, -b, places=12)


class TestLopoHandComputed(unittest.TestCase):
    def test_share_hand_computed(self):
        tmp = tempfile.mkdtemp()
        try:
            ledger = os.path.join(tmp, "l.jsonl")
            _tiny_ledger(ledger, {"GB": 1.0, "US": 1.0, "AU": 1.0,
                                  "JP": 1.0})     # zero carry differences
            from research.assets.forex_free_v5.family_a6p1 import (
                LedgerVintageReader, dedupe_ledger_rows, load_ledger_rows)
            reader = LedgerVintageReader(
                dedupe_ledger_rows(load_ledger_rows(ledger)))
            a = _hand_trade(side=1, entry=1.0, exit_=1.005)   # gross +50
            a["pair"] = "AUDUSD"
            a["areas"] = ["AU", "US"]
            b = _hand_trade(side=1, entry=1.0, exit_=0.999)   # gross -10
            b["pair"] = "NZDUSD"
            b["areas"] = ["NZ", "US"]
            share = D.lopo_share([a, b], reader)
            # drop AUDUSD -> [NZ net] = -10 - 6 (tier-2.0 cost) < 0 -> not ok
            # drop NZDUSD -> [AU net] = +50 - 6 > 0 -> ok  => share 0.5
            self.assertEqual(share, 0.5)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


# ------------------------------------------------------------------ gates #
def _all_pass_rec():
    def fold():
        return {"trades": 40, "total_pnl": 30.0, "expectancy": 0.75,
                "pf": 1.4, "gross_positive": 60.0, "populated": True,
                "mdd_usd": 1.0}
    return {
        "base": {"trades": 120, "total_pnl": 100.0, "expectancy": 1.0,
                 "pf": 1.3, "gross_positive": 200.0},
        "price_only_book": {"trades": 120, "total_pnl": 118.0,
                            "expectancy": 1.0, "pf": 1.3},
        "stress": {"1.0": {"total_pnl": 112.0}, "1.5": {"total_pnl": 106.0},
                   "2.0": {"total_pnl": 100.0}},
        "folds": {"1": fold(), "2": fold(), "3": fold()},
        "pair_concentration": {"AUDUSD": 0.2, "GBPUSD": 0.2},
        "break_even_cost_bps": 1.0,
        "dual_book_ok": True,
        "lopo_share": 1.0,
        "usd_drift_diag": {"evaluated": True, "corr": 0.05, "n_days": 60},
        "control_does_not_reproduce": True,
        "decisions": [],
    }


class TestMarginsCompleteness(unittest.TestCase):
    def test_ten_gates_frozen_order_with_margins(self):
        ok, reasons, rows = D.evaluate_gates(_all_pass_rec())
        self.assertEqual(len(rows), 10)
        self.assertEqual([r["gate_id"] for r in rows], list(D.GATE_ORDER))
        for r in rows:
            self.assertEqual(set(["gate_id", "value", "threshold",
                                  "margin"]) <= set(r), True)
        # hand-computed margins on the all-pass record
        expect = [1.0,   # 1  expectancy 1.0 > 0
                  0.2,   # 2  pf 1.3 - 1.10
                  1.0,   # 3  3 positive populated folds - 2
                  0.2,   # 4  0.40 - 0.20
                  0.5,   # 5  1.5 - 1.0 break-even
                  1.0,   # 6  boolean holds
                  1.0,   # 7  all LOPO subsets positive
                  100.0,  # 8  100.0 - 0.0
                  0.25,  # 9  0.30 - |0.05|
                  1.0]   # 10 control does not reproduce
        for r, m in zip(rows, expect):
            self.assertAlmostEqual(r["margin"], m, places=9)
        self.assertTrue(ok)
        self.assertEqual(reasons, [])

    def test_strict_margin_semantics_fail_closed_on_none_and_zero(self):
        # strict margin > 0: margin exactly 0 FAILS; None FAILS
        rec = _all_pass_rec()
        rec["base"]["pf"] = 1.10                  # margin exactly 0 -> fail
        ok, reasons, rows = D.evaluate_gates(rec)
        self.assertFalse(ok)
        self.assertIn("2_pf_ge_1.10: margin 0.0", reasons)
        rec2 = _all_pass_rec()
        rec2["usd_drift_diag"] = {"evaluated": False, "corr": None}
        ok2, reasons2, rows2 = D.evaluate_gates(rec2)
        self.assertFalse(ok2)
        self.assertTrue(any(r["gate_id"].startswith("9_") and
                            r["margin"] is None for r in rows2))

    def test_gate10_fail_closed_without_family_verdict(self):
        rec = _all_pass_rec()
        del rec["control_does_not_reproduce"]     # verdict absent
        ok, _r, rows = D.evaluate_gates(rec)
        self.assertFalse(ok)
        self.assertEqual(rows[9]["value"], 0.0)

    def test_gate10_computed_from_expectancies_when_supplied(self):
        rec = _all_pass_rec()
        ok, _r, rows = D.evaluate_gates(rec, anchor_expectancy=1.0)
        # control expectancy 1.0 >= 0.5 x anchor 1.0 and > 0 => R1 fires
        self.assertEqual(rows[9]["value"], 0.0)
        self.assertFalse(ok)
        rec2 = _all_pass_rec()
        rec2["base"]["expectancy"] = 0.3
        ok2, _r2, rows2 = D.evaluate_gates(rec2, anchor_expectancy=1.0)
        # 0.3 < 0.5 x 1.0 -> control does not reproduce -> gate passes
        self.assertEqual(rows2[9]["value"], 1.0)
        self.assertTrue(ok2)

    def test_dual_book_inversion_fails_gate6(self):
        rec = _all_pass_rec()
        rec["price_only_book"]["expectancy"] = -0.5   # price book inverts
        ok, reasons, rows = D.evaluate_gates(rec)
        self.assertFalse(ok)
        g6 = rows[5]
        self.assertEqual(g6["gate_id"], D.GATE_ORDER[5])
        self.assertEqual(g6["value"], 0.0)
        self.assertEqual(g6["margin"], 0.0)

    def test_falsification_rules_hand_computed(self):
        f = D.falsification_rules(anchor_exp=1.0, neighbour_exp=1.2,
                                  control_exp=0.9)
        self.assertTrue(f["R1_control_reproduces_kill"]["fires"])   # >= 0.5
        self.assertTrue(f["R2_sham_calendar_kill"]["fires"])        # >= 1.0
        self.assertFalse(f["R3_fragility_kill"]["fires"])
        self.assertFalse(f["R4_mechanical_reject"]["fires"])
        f2 = D.falsification_rules(anchor_exp=1.0, neighbour_exp=-0.2,
                                   control_exp=-1.0)
        self.assertFalse(f2["R1_control_reproduces_kill"]["fires"])
        self.assertFalse(f2["R2_sham_calendar_kill"]["fires"])
        self.assertTrue(f2["R3_fragility_kill"]["fires"])  # anchor>0, nb<=0
        f3 = D.falsification_rules(anchor_exp=-0.5, neighbour_exp=0.1,
                                   control_exp=0.1)
        self.assertTrue(f3["R4_mechanical_reject"]["fires"])

    def test_family_cells_stamped_with_verdict_in_collect(self):
        """collect_cells stamps the family-level gate-10 verdict on every
        cell and emits 10 complete margin rows per cell (60 overall)."""
        cells, margins, fals, exps = D.collect_cells(copy.deepcopy(SYNTH_PATHS))
        self.assertEqual(len(cells), 2)
        for fid, arms in cells.items():
            self.assertEqual(set(arms), {"anchor", "neighbour", "control"})
            verdict = not fals[fid]["R1_control_reproduces_kill"]["fires"]
            for arm in arms:
                rec = arms[arm][0]
                self.assertEqual(rec["control_does_not_reproduce"], verdict)
                self.assertEqual(len(margins[f"{fid}:{rec['arm_id']}"]), 10)
            self.assertEqual(set(exps[fid]), {"anchor", "neighbour",
                                              "control"})


# ------------------------------------------------------- arm_config_digest #
class TestArmConfigDigest(unittest.TestCase):
    def test_stable_path_independent_and_arm_distinct(self):
        for family in (F1, F2):
            local = {a: family.arm_config_digest(a) for a in family.ARM_IDS}
            proc = subprocess.run(
                [VENV_PY, "-c",
                 "import sys, json; sys.path.insert(0, %r); "
                 "from research.assets.forex_free_v9 import %s as F; "
                 "print(json.dumps({a: F.arm_config_digest(a) "
                 "for a in F.ARM_IDS}))" % (ROOT, family.__name__.rsplit(
                     ".", 1)[-1])],
                cwd=tempfile.mkdtemp(), capture_output=True, text=True,
                check=True)
            self.assertEqual(json.loads(proc.stdout), local)
            self.assertEqual(len(set(local.values())), 3)  # distinct per arm
            for dgst in local.values():
                self.assertEqual(len(dgst), 64)
                int(dgst, 16)                              # hex sha256
        # the two families' digests are disjoint
        d1 = {F1.arm_config_digest(a) for a in F1.ARM_IDS}
        d2 = {F2.arm_config_digest(a) for a in F2.ARM_IDS}
        self.assertFalse(d1 & d2)

    def test_digest_carried_on_every_decision(self):
        for family in (F1, F2):
            out = family.run_arm("anchor", SYNTH_PATHS)
            dgst = out["meta"]["arm_config_digest"]
            self.assertTrue(out["decisions"])
            for rec in out["decisions"]:
                self.assertEqual(rec["arm_config_digest"], dgst)


# ------------------------------------------------- family runners on fixture #
class TestFamilyRunnersOnFixture(unittest.TestCase):
    OUTCOME_KEYS = {"pnl", "pf", "expectancy", "profit", "return",
                    "returns", "gross_positive", "mdd", "break_even",
                    "concentration", "dual_book", "lopo", "financing"}

    def _walk_no_outcome(self, o):
        if isinstance(o, dict):
            for k, v in o.items():
                self.assertIsNone(
                    next((s for s in self.OUTCOME_KEYS
                          if s in str(k).lower()), None),
                    f"outcome-shaped key in runner output: {k}")
                self._walk_no_outcome(v)
        elif isinstance(o, list):
            for v in o:
                self._walk_no_outcome(v)

    def test_all_six_arms_nonvacuous_and_pnl_free(self):
        for family in (F1, F2):
            for arm in family.ARM_IDS:
                out = family.run_arm(arm, SYNTH_PATHS)
                self.assertGreater(out["meta"]["n_decisions"], 0,
                                   f"{family.FAMILY_ID}:{arm}")
                self._walk_no_outcome(out)

    def test_warmup_zero_full_grid_usable(self):
        days = weekday_grid(date(2018, 4, 4), date(2019, 12, 31))
        out = F1.run_arm("anchor", SYNTH_PATHS)
        m = out["meta"]
        self.assertEqual(m["grid_clocks"], len(days))
        self.assertEqual(m["usable_clocks"], len(days))
        self.assertEqual(m["first_usable_clock"], days[0].isoformat())
        self.assertEqual(m["last_usable_clock"], days[-1].isoformat())

    def test_quarterly_legs_bind_at_mass_vintage(self):
        # the fixture's AU/NZ archives carry a mass-binding vintage class:
        # no AU/NZ print binds before the mass vintage (2018-05-15), so the
        # AUDUSD/NZDUSD anchor entries can start only at/after that clock
        out = F1.run_arm("anchor", SYNTH_PATHS)
        first_au = min(d["entry_day"] for d in out["decisions"]
                       if d["pair"] == "AUDUSD")
        self.assertGreaterEqual(first_au, "2018-05-15")

    def test_sham_neighbour_timing_shifts(self):
        # +7d sham: the neighbour's state path is displaced exactly one
        # week -- the first AUDUSD entry moves by exactly +7 calendar days
        a = F1.run_arm("anchor", SYNTH_PATHS)
        n = F1.run_arm("neighbour", SYNTH_PATHS)
        fa = min(d["entry_day"] for d in a["decisions"]
                 if d["pair"] == "AUDUSD")
        fn = min(d["entry_day"] for d in n["decisions"]
                 if d["pair"] == "AUDUSD")
        self.assertEqual((date.fromisoformat(fn)
                          - date.fromisoformat(fa)).days, 7)

    def test_control_differs_from_anchor(self):
        # the control (US leg removed / level form) is a distinct
        # conditioning path: its (pair, entry) schedule differs
        for family in (F1, F2):
            ka = {(d["pair"], d["entry_day"]) for d in
                  family.run_arm("anchor", SYNTH_PATHS)["decisions"]}
            kc = {(d["pair"], d["entry_day"]) for d in
                  family.run_arm("control", SYNTH_PATHS)["decisions"]}
            self.assertNotEqual(ka, kc)

    def test_fail_closed_on_missing_staged(self):
        paths = dict(SYNTH_PATHS)
        paths["cpi_dir"] = os.path.join(SYNTH_ROOT, "nope")
        with self.assertRaises((F1.DataBlocked, RuntimeError)):
            F1.run_arm("anchor", paths)

    def test_double_run_identical(self):
        for family in (F1, F2):
            a = family.run_arm("anchor", SYNTH_PATHS)
            b = family.run_arm("anchor", SYNTH_PATHS)
            self.assertEqual(json.dumps(a, sort_keys=True),
                             json.dumps(b, sort_keys=True))


# -------------------------------------------------------- dry-run CLI #
class TestDryRunSuppression(unittest.TestCase):
    OUTCOME_KEYS = {"pnl", "pf", "expectancy", "stress", "profit", "return",
                    "returns", "total_pnl", "gross_positive", "mdd",
                    "break_even", "concentration", "dual_book", "lopo",
                    "financing_adjustment"}

    def _walk(self, o, path=""):
        if isinstance(o, dict):
            for k, v in o.items():
                kl = str(k).lower()
                if k != "pnl_suppressed" and any(
                        s in kl for s in self.OUTCOME_KEYS):
                    raise AssertionError(
                        f"outcome-shaped key in dry-run report: {path}.{k}")
                self._walk(v, f"{path}.{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                self._walk(v, f"{path}[{i}]")

    def test_dryrun_report_sanitized_two_families(self):
        buf = io.StringIO()
        old = sys.stdout
        args = type("A", (), {"out": None})()
        try:
            sys.stdout = buf
            rc = D.cmd_dryrun(args, data_paths=copy.deepcopy(SYNTH_PATHS))
        finally:
            sys.stdout = old
        self.assertEqual(rc, 0)
        report = json.loads(buf.getvalue())
        self.assertEqual(report["schema"], "forex_free_v9_dryrun_report_v1")
        self.assertEqual(report["mode"], "dryrun_sanitized")
        self._walk(report)
        self.assertEqual(len(report["families"]), 2)
        for fam in report["families"]:
            self.assertEqual(len(fam["arms"]), 3)
            for arm in fam["arms"]:
                self.assertTrue(arm["pnl_suppressed"])
                self.assertGreater(arm["n_decisions"], 0)
            adequacy = fam["adequacy"]
            self.assertIn("pooled_anchor_entries", adequacy)
            self.assertIn("meets_floor", adequacy)
            self.assertIn("closure_if_unmet", adequacy)
            self.assertEqual(
                adequacy["nonvacuity_floor_pooled_anchor_entries"], 60)
            self.assertEqual(
                adequacy["nonvacuity_floor_anchor_entries_per_fold"], 10)

    def test_dryrun_writes_identical_bytes_on_out(self):
        outs = []
        for i in range(2):
            p = os.path.join(SYNTH_ROOT, f"report_{i}.json")
            args = type("A", (), {"out": p})()
            old = sys.stdout
            try:
                sys.stdout = io.StringIO()
                D.cmd_dryrun(args, data_paths=copy.deepcopy(SYNTH_PATHS))
            finally:
                sys.stdout = old
            outs.append(open(p, "rb").read())
        self.assertEqual(outs[0], outs[1])


class TestScoredRefusal(unittest.TestCase):
    def test_refuses_without_run_contract(self):
        cwd = os.getcwd()
        try:
            os.chdir(tempfile.mkdtemp(prefix="v9_refuse_"))
            proc = subprocess.run([VENV_PY, DRIVER, "scored"],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)
            payload = json.loads(proc.stdout)
            self.assertTrue(payload["refused"])
            self.assertIn("run_contract_file", payload["missing_gates"])
        finally:
            os.chdir(cwd)

    def test_refuses_on_incomplete_contract(self):
        cwd = os.getcwd()
        tmp = tempfile.mkdtemp(prefix="v9_refuse2_")
        try:
            ctl = os.path.join(tmp, "research", "control",
                               "forex_free_v9_run")
            os.makedirs(ctl)
            with open(os.path.join(ctl, "run_contract.json"), "w") as f:
                json.dump({"cycle_id": "FOREX-FREE-V9",
                           "budget": {"used": 0}}, f)
            os.chdir(tmp)
            proc = subprocess.run([VENV_PY, DRIVER, "scored"],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)
            payload = json.loads(proc.stdout)
            self.assertTrue(payload["refused"])
            self.assertIn("s0_launch_authorized", payload["missing_gates"])
            self.assertIn("owner_fresh_go", payload["missing_gates"])
        finally:
            os.chdir(cwd)
            shutil.rmtree(tmp, ignore_errors=True)

    def test_budget_exhausted_refuses(self):
        cwd = os.getcwd()
        tmp = tempfile.mkdtemp(prefix="v9_refuse3_")
        try:
            ctl = os.path.join(tmp, "research", "control",
                               "forex_free_v9_run")
            os.makedirs(ctl)
            with open(os.path.join(ctl, "run_contract.json"), "w") as f:
                json.dump({"cycle_id": "FOREX-FREE-V9",
                           "launch_gate": {"s0_launch_authorized": True,
                                           "a7_prelaunch_verdict":
                                               "FOREX_FREE_V9_S0_LAUNCH_"
                                               "AUTHORIZED",
                                           "owner_go_fresh": True,
                                           "owner_go_phrase":
                                               "GO FOREX V9 SCORED EXECUTION"},
                           "budget": {"used": 1}}, f)
            os.chdir(tmp)
            proc = subprocess.run([VENV_PY, DRIVER, "scored"],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)
            payload = json.loads(proc.stdout)
            # used(1) + 6 cells > 6 planned -> budget exhausted
            self.assertIn("budget", payload["missing_gates"])
        finally:
            os.chdir(cwd)
            shutil.rmtree(tmp, ignore_errors=True)

    def test_launch_gate_reader_reads_launch_gate_block(self):
        """The scored gate reads the run contract's launch_gate.* block with
        the contract's own field names.  Hand-check: the unflipped contract
        yields exactly [s0_launch_authorized, owner_fresh_go]; the flipped
        contract yields no missing keys; cycle_id mismatch is caught."""
        cwd = os.getcwd()
        tmp = tempfile.mkdtemp(prefix="v9_refuse4_")
        try:
            ctl = os.path.join(tmp, "research", "control",
                               "forex_free_v9_run")
            os.makedirs(ctl)
            rc_path = os.path.join(ctl, "run_contract.json")
            with open(rc_path, "w") as f:
                json.dump({"cycle_id": "FOREX-FREE-V9",
                           "budget": {"used": 0},
                           "launch_gate": {
                               "s0_launch_authorized": False,
                               "owner_go_fresh": False,
                               "owner_go_phrase":
                                   "GO FOREX V9 SCORED EXECUTION",
                               "a7_prelaunch_verdict": None}}, f)
            os.chdir(tmp)
            self.assertEqual(D._launch_gate_state(),
                             ["s0_launch_authorized", "owner_fresh_go"])
            flipped = {"cycle_id": "FOREX-FREE-V9",
                       "budget": {"used": 0},
                       "launch_gate": {
                           "s0_launch_authorized": True,
                           "a7_prelaunch_verdict":
                               "FOREX_FREE_V9_S0_LAUNCH_AUTHORIZED",
                           "owner_go_fresh": True,
                           "owner_go_phrase":
                               "GO FOREX V9 SCORED EXECUTION"}}
            with open(rc_path, "w") as f:
                json.dump(flipped, f)
            self.assertEqual(D._launch_gate_state(), [])
            flipped["cycle_id"] = "FOREX-FREE-V8"
            with open(rc_path, "w") as f:
                json.dump(flipped, f)
            self.assertEqual(D._launch_gate_state(), ["cycle_id"])
        finally:
            os.chdir(cwd)
            shutil.rmtree(tmp, ignore_errors=True)

    def test_wrong_go_phrase_or_verdict_refuses(self):
        self.assertIn("owner_fresh_go", self._state_with(
            owner_go_phrase="GO FOREX V8 SCORED EXECUTION"))
        self.assertIn("s0_launch_authorized", self._state_with(
            verdict="FOREX_FREE_V8_S0_LAUNCH_AUTHORIZED"))

    @staticmethod
    def _state_with(owner_go_phrase=None, verdict=None):
        base = {"s0_launch_authorized": True,
                "a7_prelaunch_verdict":
                    "FOREX_FREE_V9_S0_LAUNCH_AUTHORIZED",
                "owner_go_fresh": True,
                "owner_go_phrase": "GO FOREX V9 SCORED EXECUTION"}
        if owner_go_phrase:
            base["owner_go_phrase"] = owner_go_phrase
        if verdict:
            base["a7_prelaunch_verdict"] = verdict
        old = D.RUN_CONTRACT_PATH
        tmp = tempfile.mkdtemp()
        try:
            D.RUN_CONTRACT_PATH = os.path.join(tmp, "run_contract.json")
            with open(D.RUN_CONTRACT_PATH, "w") as f:
                json.dump({"cycle_id": "FOREX-FREE-V9",
                           "budget": {"used": 0},
                           "launch_gate": base}, f)
            return D._launch_gate_state()
        finally:
            D.RUN_CONTRACT_PATH = old
            shutil.rmtree(tmp, ignore_errors=True)

    def test_resolve_mode_alias(self):
        self.assertEqual(D.resolve_mode(None, True), "dryrun")
        self.assertEqual(D.resolve_mode("dryrun", False), "dryrun")
        self.assertEqual(D.resolve_mode("scored", False), "scored")
        self.assertIsNone(D.resolve_mode(None, False))

    def test_stage_spot_never_hardcodes_key(self):
        # the optional staging helper reads keys ONLY from os.environ
        os.environ.pop("TWELVE_DATA_API_KEY", None)
        self.assertIsNone(D.staging_api_key("TWELVE_DATA_API_KEY"))
        os.environ["TWELVE_DATA_API_KEY"] = "test-value-not-a-real-key"
        try:
            self.assertEqual(D.staging_api_key("TWELVE_DATA_API_KEY"),
                             "test-value-not-a-real-key")
        finally:
            os.environ.pop("TWELVE_DATA_API_KEY", None)

    def test_dry_run_flag_cli_on_real_paths(self):
        """--dry-run is an alias of the dryrun positional mode; exercised
        end-to-end only where the gitignored real bytes exist (a fresh twin
        without the local copies skips this smoke -- the synthetic suite
        above already covers the dry-run contract)."""
        spot = os.path.join(ROOT, "data_raw", "forex_free_v9_spot")
        cpi = os.path.join(ROOT, "data_raw", "forex_free_v9_cpi")
        if not (os.path.isdir(spot) and os.path.isdir(cpi)):
            self.skipTest("local real-byte copies absent (gitignored)")
        proc = subprocess.run([VENV_PY, DRIVER, "--dry-run"], cwd=ROOT,
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        report = json.loads(proc.stdout)
        self.assertEqual(report["mode"], "dryrun_sanitized")
        for fam in report["families"]:
            self.assertTrue(fam["adequacy"]["meets_floor"])


# -------------------------------------------------------- twin determinism #
CANON_CONTRACT = {
    "cycle_id": "FOREX-FREE-V9",
    "asset": "forex",
    "multiple_testing_accounting": True,
    "calendar_conditioned": True,
    "confirmatory_entry_declared": False,
    "outputs": {
        "identity": {"persist": True,
                     "artifact": "artifacts/identity.jsonl",
                     "schema_id": "diag/identity@1", "format": "jsonl"},
        "per_period_series": {"persist": True,
                              "artifact": "artifacts/per_period_series.jsonl",
                              "schema_id": "diag/per_period_series@1",
                              "format": "jsonl"},
        "per_symbol_breakdown": {
            "persist": True,
            "artifact": "artifacts/per_symbol_breakdown.jsonl",
            "schema_id": "diag/per_symbol_breakdown@1", "format": "jsonl"},
        "per_fold_breakdown": {"persist": True,
                               "artifact": "artifacts/per_fold_breakdown.jsonl",
                               "schema_id": "diag/per_fold_breakdown@1",
                               "format": "jsonl"},
        "stress_tiers": {"persist": True,
                         "artifact": "artifacts/stress_tiers.jsonl",
                         "schema_id": "diag/stress_tiers@1",
                         "format": "jsonl"},
        "drop_one_inputs": {"persist": True,
                            "artifact": "artifacts/drop_one_inputs.jsonl",
                            "schema_id": "diag/drop_one_inputs@1",
                            "format": "jsonl"},
        "benchmark_context": {"persist": True,
                              "artifact": "artifacts/benchmark_context.jsonl",
                              "schema_id": "diag/benchmark_context@1",
                              "format": "jsonl"},
        "margins_to_fail": {"persist": True,
                            "artifact": "artifacts/margins_to_fail.jsonl",
                            "schema_id": "diag/margins_to_fail@1",
                            "format": "jsonl"},
        "counters": {"persist": True, "artifact": "artifacts/counters.jsonl",
                     "schema_id": "diag/counters@1", "format": "jsonl"},
        "reproduction_inputs": {
            "persist": True, "artifact": "artifacts/reproduction_inputs.jsonl",
            "schema_id": "diag/reproduction_inputs@1", "format": "jsonl"},
    },
    "conditional": {
        "dsr_per_period_series": {
            "applicability": "multiple_testing_accounting",
            "persist": True,
            "artifact": "artifacts/dsr_per_period_series.jsonl",
            "schema_id": "diag/dsr_per_period_series@1", "format": "jsonl"},
        "sham_control_calendar": {
            "applicability": "calendar_conditioned",
            "persist": True,
            "artifact": "artifacts/sham_control_calendar.jsonl",
            "schema_id": "diag/sham_control_calendar@1", "format": "jsonl"},
        "financing_dual_books": {
            "applicability": "asset == 'forex'",
            "persist": True,
            "artifact": "artifacts/financing_dual_books.jsonl",
            "schema_id": "diag/financing_dual_books@1", "format": "jsonl"},
    },
}

CANON_FILE_COUNT = 14      # 10 outputs + 3 conditional + control_rows


class TestTwinDeterminism(unittest.TestCase):
    """Same synthetic inputs from two different working directories must
    re-emit byte-identical artifacts (owner twin-binding directive)."""

    def _smoke_in(self, cwd):
        proc = subprocess.run([VENV_PY, DRIVER, "diagnostic-smoke"],
                              cwd=cwd, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0,
                         msg=f"smoke failed in {cwd}: {proc.stderr[-800:]}")
        art = os.path.join(cwd, "artifacts")
        return {name: open(os.path.join(art, name), "rb").read()
                for name in sorted(os.listdir(art))}

    def test_two_working_directories_byte_identical(self):
        dir_a = tempfile.mkdtemp(prefix="v9_twin_a_")
        dir_b = tempfile.mkdtemp(prefix="v9_twin_b_")
        try:
            art_a = self._smoke_in(dir_a)
            art_b = self._smoke_in(dir_b)
            self.assertEqual(len(art_a), CANON_FILE_COUNT)
            self.assertEqual(sorted(art_a), sorted(art_b))
            for name in sorted(art_a):
                self.assertEqual(art_a[name], art_b[name],
                                 msg=f"artifact not byte-identical: {name}")
            blob = b"".join(art_a[n] for n in sorted(art_a))
            self.assertNotIn(str(dir_a).encode(), blob)   # path independence
            self.assertNotIn(str(dir_b).encode(), blob)
        finally:
            shutil.rmtree(dir_a, ignore_errors=True)
            shutil.rmtree(dir_b, ignore_errors=True)

    def test_emitted_artifacts_carry_canon_fields(self):
        dir_a = tempfile.mkdtemp(prefix="v9_canon_")
        try:
            art = self._smoke_in(dir_a)
            for category, spec in CANON_CONTRACT["outputs"].items():
                name = os.path.basename(spec["artifact"])
                self.assertIn(name, art, category)
                recs = [json.loads(ln) for ln in
                        art[name].decode().splitlines() if ln.strip()]
                self.assertTrue(recs, f"{category} empty")
                self.assertTrue(all(r.get("schema_id") == spec["schema_id"]
                                    for r in recs), category)
            # margins: 10 gates x 6 scored cells (2 families x 3 arms)
            mtf = [json.loads(ln) for ln in
                   art["margins_to_fail.jsonl"].decode().splitlines()
                   if ln.strip()]
            self.assertEqual(len(mtf), 60)
            for r in mtf:
                self.assertIn("gate_id", r)
                self.assertIn("value", r)
                self.assertIn("threshold", r)
                self.assertIn("margin", r)
            # identity rows: one per cell, arm_config_digest carried
            ids = [json.loads(ln) for ln in
                   art["identity.jsonl"].decode().splitlines() if ln.strip()]
            self.assertEqual(len(ids), 6)
            for r in ids:
                self.assertEqual(len(r["arm_config_digest"]), 64)
            # per-period series covers the usable decision grid, one row
            # per clock per arm, none all-null
            pps = [json.loads(ln) for ln in
                   art["per_period_series.jsonl"].decode().splitlines()
                   if ln.strip()]
            by_arm = {}
            for r in pps:
                by_arm.setdefault(r["arm_id"], []).append(r)
            self.assertEqual(len(by_arm), 6)
            for arm_id, rows in by_arm.items():
                self.assertTrue(all(r["returns"] is not None for r in rows),
                                arm_id)
                self.assertEqual(len(rows),
                                 len({r["period"] for r in rows}))
            # the mandatory sham is answered from bytes: the neighbour arms
            # carry the +7d sham calendar id
            scc = [json.loads(ln) for ln in
                   art["sham_control_calendar.jsonl"].decode().splitlines()
                   if ln.strip()]
            self.assertEqual(len(scc), 6)
            for r in scc:
                if r["arm_id"].startswith("neighbour"):
                    self.assertIn("+7d", r["calendar"])
            # control rows carry the control semantics + R1..R4 battery
            ctrl = [json.loads(ln) for ln in
                    art["control_rows.jsonl"].decode().splitlines()
                    if ln.strip()]
            self.assertTrue(any("control_semantics" in r for r in ctrl))
            for fam in ("FXFV9-A5-P1", "FXFV9-A5-P2"):
                self.assertTrue(any(r.get("family_id") == fam and
                                    r.get("rule", "").startswith("R1_")
                                    for r in ctrl), fam)
        finally:
            shutil.rmtree(dir_a, ignore_errors=True)

    def test_fixture_builder_is_byte_deterministic(self):
        d1 = tempfile.mkdtemp(prefix="v9_fix1_")
        d2 = tempfile.mkdtemp(prefix="v9_fix2_")
        try:
            for d in (d1, d2):
                subprocess.run([VENV_PY, FIXTURE_BUILDER, d], check=True,
                               capture_output=True)
            names = sorted(os.listdir(d1))
            self.assertEqual(names, sorted(os.listdir(d2)))
            for name in names:
                p1 = os.path.join(d1, name)
                p2 = os.path.join(d2, name)
                if os.path.isfile(p1):
                    self.assertEqual(open(p1, "rb").read(),
                                     open(p2, "rb").read(), name)
        finally:
            shutil.rmtree(d1, ignore_errors=True)
            shutil.rmtree(d2, ignore_errors=True)

    def test_governance_diagnostic_gate_passes_unchanged(self):
        """The V6/V7/V8 governance machinery (research/governance/
        diagnostic_persistability.py) validates the V9 emission unchanged:
        contract PASS + fresh-sandbox emission with canon content."""
        from research.governance.diagnostic_persistability import (
            smoke_check_twin_rerun, validate_contract)
        verdict, findings = validate_contract(CANON_CONTRACT)
        self.assertEqual(verdict, "DIAGNOSTIC_CONTRACT_PASS", findings)
        verdict, problems = smoke_check_twin_rerun(
            [VENV_PY, DRIVER, "diagnostic-smoke"], CANON_CONTRACT)
        self.assertEqual(verdict, "DIAGNOSTIC_CONTRACT_PASS", problems)


if __name__ == "__main__":
    unittest.main()
