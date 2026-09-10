"""FOREX-FREE-V8 runner + driver tests (FXFV8-A5-P1, frozen family).

SYNTHETIC hand-computed fixtures ONLY -- no production outcomes, no real
data bytes required (the suite must pass in a fresh twin worktree without
the gitignored staged/price copies), no scored execution anywhere.  The
diagnostic-smoke mode used for the twin test books SYNTHETIC trades from
the deterministic fixture builder; it never reads real conditioning bytes.

Hand-verified fixture comments: TestStateMachineHandComputed carries one
fully hand-checked hysteresis exit path (scenario A) and one fully
hand-checked 21-business-day time-cap exit (scenario B).
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
from collections import OrderedDict
from datetime import date, datetime, timedelta, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)

from research.assets.forex_free_v3 import accounting as K            # noqa: E402
from research.assets.forex_free_v8 import conditioning as C          # noqa: E402
from research.assets.forex_free_v8 import exec_driver_v8 as D        # noqa: E402
from research.assets.forex_free_v8 import family_a5p1_v8 as F        # noqa: E402

VENV_PY = sys.executable
DRIVER = os.path.join(ROOT, "research", "assets", "forex_free_v8",
                      "exec_driver_v8.py")
FIXTURE_BUILDER = os.path.join(ROOT, "research", "assets", "forex_free_v8",
                               "synthetic_fixture_v8.py")

SYNTH_ROOT = None
SYNTH_DATA = None
SYNTH_PATHS = None


def setUpModule():
    global SYNTH_ROOT, SYNTH_DATA, SYNTH_PATHS
    SYNTH_ROOT = tempfile.mkdtemp(prefix="v8_tests_synth_")
    SYNTH_DATA = os.path.join(SYNTH_ROOT, "synthetic_data")
    subprocess.run([VENV_PY, FIXTURE_BUILDER, SYNTH_DATA],
                   check=True, capture_output=True)
    SYNTH_PATHS = {
        "price_dir": SYNTH_DATA,
        "staged_dir": os.path.join(SYNTH_DATA, "staged"),
        "announcement_ledger": os.path.join(SYNTH_DATA, "ledger.jsonl"),
        "s0_start": date(2018, 4, 4), "s0_end": date(2020, 7, 31),
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


# ------------------------------------------------------------------ z-score #
class TestZscoreHandComputed(unittest.TestCase):
    """Hand-computed z (frozen convention: population std, ddof=0)."""

    def test_hand_computed_population_z(self):
        # window [1,2,3], x=2.5: mean 2.0, pop var ((1+0+1)/3)=2/3,
        # z = 0.5 / sqrt(2/3) = 0.6123724356957945...
        z = C.zscore([1.0, 2.0, 3.0], 2.5)
        self.assertAlmostEqual(z, 0.5 / math.sqrt(2.0 / 3.0), places=12)
        self.assertAlmostEqual(z, 0.6123724356957945, places=12)

    def test_zero_dispersion_and_empty_fail_closed(self):
        self.assertIsNone(C.zscore([5.0, 5.0, 5.0], 5.0))
        self.assertIsNone(C.zscore([], 1.0))

    def test_zscore_deterministic_across_calls(self):
        w = [0.5, 1.25, -2.0, 3.75, 1.0, 0.0]
        a = [C.zscore(w, x) for x in (1.0, -0.5, 4.0)]
        b = [C.zscore(list(w), x) for x in (1.0, -0.5, 4.0)]
        self.assertEqual(a, b)


# ------------------------------------------- as-of reconstruction (AX2-C1/C4) #
class TestAsOfReconstructionMutation(unittest.TestCase):
    """switch-exactly-at-vintage + mutation property, hand-computed."""

    def _write_series(self, dirpath, rows):
        os.makedirs(dirpath, exist_ok=True)
        p = os.path.join(dirpath, "X.json")
        with open(p, "w") as f:
            json.dump(rows, f)
        return p

    def test_value_switches_exactly_at_new_vintage(self):
        # obs 2020-01-07 first binds at 01-07 with value 2.0 and is revised
        # by the vintage of 01-10 to 2.5.  Hand table:
        #   decision d        as-of value
        #   2020-01-06        None      (not yet bound)
        #   2020-01-07..09    2.0       (first vintage)
        #   2020-01-10        2.5       (switch EXACTLY at the new vintage)
        #   2020-01-11        2.5
        rows = [{"date": "2020-01-07", "realtime_start": "2020-01-07",
                 "realtime_end": "2020-01-10", "value": "2.0"},
                {"date": "2020-01-07", "realtime_start": "2020-01-10",
                 "realtime_end": "2030-01-01", "value": "2.5"}]
        by_obs, _all = C.load_staged_series(
            self._write_series(tempfile.mkdtemp(), rows))
        r = by_obs[date(2020, 1, 7)]
        self.assertIsNone(C.as_of_value(r, date(2020, 1, 6)))
        self.assertEqual(C.as_of_value(r, date(2020, 1, 7)), 2.0)
        self.assertEqual(C.as_of_value(r, date(2020, 1, 9)), 2.0)
        self.assertEqual(C.as_of_value(r, date(2020, 1, 10)), 2.5)
        self.assertEqual(C.as_of_value(r, date(2020, 1, 11)), 2.5)

    def test_mutation_shifts_binding_exactly_k_clocks(self):
        # grid = weekdays 2020-01-06..2020-01-15 (Jan 6 is a Monday).
        # obs 2020-01-13 (a Monday) with available_time 01-14 binds at the
        # 01-14 clock (first grid clock >= rt; that day's 16:00-NY clock is
        # strictly after the 00:00 available_time -- AX2-C4).  Mutating the
        # available_time +1 day (k=1) must move the consumed value at any
        # decision date EXACTLY one clock later: the 01-14 decision falls
        # back to the carried 5.0 and 6.0 is first consumed at 01-15.
        grid = [date(2020, 1, 6) + timedelta(days=i) for i in range(10)]
        grid = [d for d in grid if d.weekday() < 5]

        def series(rt_for_0113):
            return {"X": {
                date(2020, 1, 6): [(date(2020, 1, 6), 1.0)],
                date(2020, 1, 7): [(date(2020, 1, 7), 2.0)],
                date(2020, 1, 8): [(date(2020, 1, 8), 3.0)],
                date(2020, 1, 9): [(date(2020, 1, 9), 4.0)],
                date(2020, 1, 10): [(date(2020, 1, 10), 5.0)],
                date(2020, 1, 13): [(rt_for_0113, 6.0)],   # mutated print
                date(2020, 1, 14): [(date(2020, 1, 15), 7.0)],
            }}

        base = OrderedDict(series(date(2020, 1, 14)))
        mut = OrderedDict(series(date(2020, 1, 15)))
        r_base = C.AsOfReconstructor(grid, base)
        r_mut = C.AsOfReconstructor(grid, mut)
        # baseline: 6.0 is consumed from the 01-14 clock
        self.assertEqual(r_base.value_at("X", date(2020, 1, 13)), 5.0)
        self.assertEqual(r_base.value_at("X", date(2020, 1, 14)), 6.0)
        # mutation k=1: the 01-14 clock still consumes the carried 5.0 (the
        # decision shifted EXACTLY one period, never absorbed, never early);
        # at 01-15 BOTH late prints bind (01-13 and 01-14 obs) and the
        # consumed print is the latest obs (01-14) with value 7.0.
        self.assertEqual(r_mut.value_at("X", date(2020, 1, 13)), 5.0)
        self.assertEqual(r_mut.value_at("X", date(2020, 1, 14)), 5.0)
        self.assertEqual(r_mut.value_at("X", date(2020, 1, 15)), 7.0)
        # and the binding clock moved exactly one grid clock
        self.assertEqual(r_base.current_obs("X", date(2020, 1, 14)),
                         date(2020, 1, 13))
        self.assertEqual(r_mut.current_obs("X", date(2020, 1, 14)),
                         date(2020, 1, 10))

    def test_obs_beyond_grid_never_consumed(self):
        grid = [date(2020, 1, 6), date(2020, 1, 7), date(2020, 1, 8)]
        series = {"A": {date(2020, 1, 6): [(date(2020, 1, 6), 1.0)],
                        date(2020, 1, 7): [(date(2020, 1, 7), 2.0)]},
                  "B": {date(2020, 1, 9): [(date(2020, 1, 9), 9.0)]}}
        r = C.AsOfReconstructor(grid, series)
        self.assertEqual(r.value_at("A", date(2020, 1, 8)), 2.0)
        self.assertIsNone(r.value_at("B", date(2020, 1, 8)))

    def test_single_snapshot_slope_ax2c2(self):
        # both legs read at the SAME as-of date inside one snapshot
        grid = [date(2020, 1, 6), date(2020, 1, 7)]
        from collections import OrderedDict
        series = OrderedDict({
            "T10YIE": {date(2020, 1, 6): [(date(2020, 1, 6), 2.5)],
                       date(2020, 1, 7): [(date(2020, 1, 7), 2.7)]},
            "T5YIE": {date(2020, 1, 6): [(date(2020, 1, 6), 1.2)],
                      date(2020, 1, 7): [(date(2020, 1, 7), 1.3)]},
        })
        r = C.AsOfReconstructor(grid, series)
        self.assertAlmostEqual(r.slope_at(date(2020, 1, 6),
                                          "T10YIE", "T5YIE"), 1.3, places=12)
        self.assertAlmostEqual(r.slope_at(date(2020, 1, 7),
                                          "T10YIE", "T5YIE"), 1.4, places=12)


# ------------------------------------------------- driver series (as-bound) #
class TestDriverSeriesAsBound(unittest.TestCase):
    def test_history_is_as_bound_never_repulled(self):
        # a revision vintage at 2020-01-10 changes values bound at clocks
        # >= 01-10 only; values bound at earlier clocks are untouched
        grid = [date(2020, 1, 6) + timedelta(days=i) for i in range(8)]
        grid = [d for d in grid if d.weekday() < 5]

        def build(revised):
            rows = {}
            for d in grid:
                lst = [(d, 1.0)]
                if revised and d == date(2020, 1, 10):
                    lst.append((date(2020, 1, 10), 9.0))
                rows[d] = lst
            return C.AsOfReconstructor(grid, {"DGS10": rows})

        r1 = build(False)
        z1, _m1, h1 = F.compute_driver_series(r1, "control",
                                              return_history=True)
        r2 = build(True)
        z2, _m2, h2 = F.compute_driver_series(r2, "control",
                                              return_history=True)
        i = grid.index(date(2020, 1, 10))
        self.assertEqual(h1[:i], h2[:i])        # untouched before the vintage
        self.assertEqual(h2[i], 9.0)            # new vintage binds at its clock
        self.assertEqual(h1[i], 1.0)

    def test_double_run_identical(self):
        numeric, all_dates = F.load_staged_triple(SYNTH_PATHS["staged_dir"])
        grid = F.build_grid(all_dates, SYNTH_PATHS["s0_start"],
                            SYNTH_PATHS["s0_end"])
        recon = C.AsOfReconstructor(grid, numeric)
        za, ma = F.compute_driver_series(recon, "anchor")
        zb, mb = F.compute_driver_series(recon, "anchor")
        self.assertEqual(json.dumps({str(k): v for k, v in za.items()},
                                    sort_keys=True),
                         json.dumps({str(k): v for k, v in zb.items()},
                                    sort_keys=True))
        self.assertEqual(ma["history_len"], mb["history_len"])


# ----------------------------------------------------- state machine (hand) #
class TestStateMachineHandComputed(unittest.TestCase):
    """Direct simulate_arm walks on hand-computed z/fill fixtures."""

    PAIR = "EURUSD"

    @staticmethod
    def _clocks(n):
        return [date(2020, 1, 1) + timedelta(days=i) for i in range(n)]

    def _run(self, zvals, fills_seq, arm="anchor", pair="EURUSD"):
        clocks = self._clocks(len(zvals))
        z = {d: v for d, v in zip(clocks, zvals)}
        fills = {pair: {d: p for d, p in zip(clocks, fills_seq)}}
        return F.simulate_arm(z, fills, clocks, arm, pairs=(pair,))

    def test_scenario_a_hysteresis_exit_hand_verified(self):
        # ---- HAND-VERIFIED hysteresis path (frozen rules) ----
        # clocks c0..c4, arm anchor, pair EURUSD (long pair = short USD).
        #   z   = [None, +1.40, +0.80, +0.30, None]
        #   px  = [1.10,  1.12,  1.11,  1.14, 1.15]
        # c0: z None -> no activation, flat.
        # c1: |1.40| >= 1.0 -> ENTRY; z >= +1 => SHORT USD basket; EURUSD's
        #     long side IS short USD => side = +1 at 1.12.
        # c2: |0.80| > 0.5 -> inside the dead band, position HELD.
        # c3: |0.30| <= 0.5 -> HYSTERESIS EXIT at 1.14 (whichever-first rule:
        #     3 - 1 = 2 held clocks < 21, so the band fired, not the cap).
        # c4: flat again (z None).
        # Expected: exactly one closed trade, hold_clocks = 2.
        decisions, counts = self._run(
            [None, 1.4, 0.8, 0.3, None],
            [1.10, 1.12, 1.11, 1.14, 1.15])
        self.assertEqual(len(decisions), 1)
        tr = decisions[0]
        self.assertEqual(tr["pair"], "EURUSD")
        self.assertEqual(tr["side"], 1)
        self.assertEqual(tr["entry_day"], "2020-01-02")
        self.assertEqual(tr["exit_day"], "2020-01-04")
        self.assertEqual(tr["entry_price"], 1.12)
        self.assertEqual(tr["exit_price"], 1.14)
        self.assertEqual(tr["hold_clocks"], 2)
        self.assertEqual(tr["exit_reason"], "hysteresis")
        self.assertAlmostEqual(tr["entry_z"], 1.4, places=12)
        self.assertAlmostEqual(tr["exit_z"], 0.3, places=12)
        self.assertEqual(counts["entries"], 1)
        self.assertEqual(counts["exits_hysteresis"], 1)
        self.assertEqual(counts["exits_time_cap"], 0)
        self.assertEqual(counts["terminal_closes"], 0)
        # gross sanity of the recorded walk: long entry 1.12 -> exit 1.14
        self.assertGreater(tr["exit_price"] / tr["entry_price"] - 1.0, 0.0)

    def test_scenario_b_21bd_time_cap_exit_hand_verified(self):
        # ---- HAND-VERIFIED 21-business-day time-cap exit ----
        # clocks c0..c25; z = +1.40 at c1..c22 (never inside the band), then
        # +0.70 at c23..c25 (above 0.5: no hysteresis; below 1.0: no
        # re-entry).  Entry at c1 (idx 1).  Cap rule: exit when
        # idx - entry_idx >= 21 -> first true at idx 22 = c22, i.e. exactly
        # 21 clocks after entry; at idx 21 (c21) 21-1=20 < 21 -> still held.
        # Exit at c22 fills at 1.05; reason "time_cap"; hold_clocks = 21.
        zvals = [None] + [1.4] * 22 + [0.7] * 3
        fills = [1.00] * 23 + [1.01, 1.01, 1.01]
        decisions, counts = self._run(zvals, fills)
        self.assertEqual(len(decisions), 1)
        tr = decisions[0]
        self.assertEqual(tr["entry_day"], "2020-01-02")
        self.assertEqual(tr["exit_day"], "2020-01-23")
        self.assertEqual(tr["hold_clocks"], 21)
        self.assertEqual(tr["exit_reason"], "time_cap")
        self.assertEqual(counts["entries"], 1)
        self.assertEqual(counts["exits_time_cap"], 1)
        self.assertEqual(counts["exits_hysteresis"], 0)

    def test_reentry_allowed_at_next_clock(self):
        # c1 enter (1.4) -> c2 hysteresis exit (0.3) -> c3 RE-ENTRY (1.1,
        # the next clock after the exit) -> c4 exit (0.3).  Two round trips.
        decisions, counts = self._run(
            [None, 1.4, 0.3, 1.1, 0.3, None],
            [1.0, 1.1, 1.0, 1.1, 1.0, 1.0])
        self.assertEqual(counts["entries"], 2)
        self.assertEqual(counts["exits_hysteresis"], 2)
        self.assertEqual([d["entry_day"] for d in decisions],
                         ["2020-01-02", "2020-01-04"])
        self.assertEqual([d["exit_day"] for d in decisions],
                         ["2020-01-03", "2020-01-05"])

    def test_max_one_position_no_stack_up(self):
        # activation persists 10 clocks -> exactly ONE entry while the
        # position is open (max one position per pair); terminal close at
        # the end (counted, never dropped).
        zvals = [None] + [1.4] * 10
        fills = [1.0] * 11
        decisions, counts = self._run(zvals, fills)
        self.assertEqual(counts["entries"], 1)
        self.assertEqual(counts["terminal_closes"], 1)
        self.assertEqual(decisions[-1]["exit_reason"], "terminal")
        self.assertEqual(decisions[-1]["exit_day"], "2020-01-11")

    def test_threshold_boundaries_inclusive(self):
        # |z| >= 1.0 activates (z = 1.0 exactly enters); |z| <= 0.5 exits
        # (z = 0.5 exactly is a hysteresis exit at that same clock; a hair
        # above 0.5 keeps the position open).
        d1, c1 = self._run([None, 1.0, 0.6, 0.5, None],
                           [1.0, 1.0, 1.0, 1.0, 1.0])
        self.assertEqual(c1["entries"], 1)
        self.assertEqual(d1[0]["exit_reason"], "hysteresis")
        self.assertEqual(d1[0]["exit_day"], "2020-01-04")
        d2, c2 = self._run([None, 1.0, 0.6, 0.5000001, None],
                           [1.0, 1.0, 1.0, 1.0, 1.0])
        self.assertEqual(c2["exits_hysteresis"], 0)
        self.assertEqual(d2[0]["exit_reason"], "terminal")

    def test_direction_maps_frozen(self):
        # anchor/neighbour: z>=+1 => SHORT USD (EURUSD +1, USDJPY -1);
        # z<=-1 => LONG USD (mirror).  control inverts the basket.
        for arm in ("anchor", "neighbour", "control"):
            inverted = arm == "control"
            self.assertEqual(F.side_for_z(arm, 1.4, "EURUSD"),
                             -1 if inverted else 1, arm)
            self.assertEqual(F.side_for_z(arm, 1.4, "USDJPY"),
                             1 if inverted else -1, arm)
            self.assertEqual(F.side_for_z(arm, -1.4, "EURUSD"),
                             1 if inverted else -1, arm)
            self.assertEqual(F.side_for_z(arm, -1.4, "USDJPY"),
                             -1 if inverted else 1, arm)
        # every USD pair is classified in exactly one basket
        self.assertEqual(F.SHORT_USD_PAIRS | F.LONG_USD_PAIRS, frozenset(F.PAIRS))
        self.assertFalse(F.SHORT_USD_PAIRS & F.LONG_USD_PAIRS)

    def test_missing_entry_fill_skips_without_position(self):
        # c1: activation but NO fill -> counted, never filled, position NOT
        # opened; c2: still active, fill present -> enters there.
        clocks = self._clocks(4)
        z = {clocks[0]: None, clocks[1]: 1.4, clocks[2]: 1.2, clocks[3]: 1.2}
        fills = {"EURUSD": {clocks[0]: 1.0, clocks[2]: 1.1, clocks[3]: 1.1}}
        decisions, counts = F.simulate_arm(z, fills, clocks, "anchor",
                                           pairs=("EURUSD",))
        self.assertEqual(counts["entries_fill_missing"], 1)
        self.assertEqual(counts["entries"], 1)
        self.assertEqual(decisions[0]["entry_day"], clocks[2].isoformat())

    def test_missing_exit_fill_does_not_fabricate_exit(self):
        # c2 hysteresis fires but has no fill -> position STAYS OPEN
        # (counted), exits at the next clock that has both a fill and a
        # live exit condition.
        clocks = self._clocks(5)
        z = {clocks[0]: None, clocks[1]: 1.4, clocks[2]: 0.3,
             clocks[3]: 0.3, clocks[4]: None}
        fills = {"EURUSD": {clocks[0]: 1.0, clocks[1]: 1.1,
                            clocks[3]: 1.2, clocks[4]: 1.2}}
        decisions, counts = F.simulate_arm(z, fills, clocks, "anchor",
                                           pairs=("EURUSD",))
        self.assertEqual(counts["exits_fill_missing"], 1)
        self.assertEqual(len(decisions), 1)
        self.assertEqual(decisions[0]["exit_day"], clocks[3].isoformat())
        self.assertEqual(decisions[0]["hold_clocks"], 2)


# ------------------------------------------------------------------- folds #
class TestFoldSplitDeterminism(unittest.TestCase):
    def test_bounds_mechanical_thirds(self):
        self.assertEqual(F.fold_bounds(1655), (551, 1103))
        self.assertEqual(F.fold_bounds(3), (1, 2))
        self.assertEqual(F.fold_bounds(1), (0, 0))
        self.assertEqual(F.fold_bounds(1640), (546, 1093))

    def test_fold_assignment(self):
        b = F.fold_bounds(10)          # (3, 6)
        self.assertEqual([F.fold_of_index(i, b) for i in range(10)],
                         [1, 1, 1, 2, 2, 2, 3, 3, 3, 3])

    def test_fail_closed(self):
        with self.assertRaises(F.DataBlocked):
            F.fold_bounds(0)
        with self.assertRaises(F.DataBlocked):
            F.fold_bounds(10, n_folds=4)

    def test_deterministic(self):
        self.assertEqual(F.fold_bounds(1640), F.fold_bounds(1640))


# --------------------------------------------------- cost-once + dual book #
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
    return {"pair": "EURUSD", "side": side, "notional_usd": 10000.0,
            "entry_price": entry, "exit_price": exit_,
            "areas": ("EMU", "US"),
            "entry_ts": f"{entry_day}T20:00:00+00:00",
            "exit_ts": f"{exit_day}T20:00:00+00:00"}


class TestCostOncePerFill(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.ledger = os.path.join(self.tmp, "l.jsonl")
        _tiny_ledger(self.ledger, {"EMU": 1.25, "US": 2.00})
        from research.assets.forex_free_v5.family_a6p1 import (
            LedgerVintageReader, dedupe_ledger_rows, load_ledger_rows)
        self.reader = LedgerVintageReader(
            dedupe_ledger_rows(load_ledger_rows(self.ledger)))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_round_trip_charged_exactly_two_sides(self):
        tr = _hand_trade()
        gross = D.price_pnl_usd(tr)                       # 10000*(1.21/1.10-1)
        self.assertAlmostEqual(gross, 1000.0, places=6)
        for tier in ("1.0", "1.5", "2.0"):
            pnls, skipped = D.book_trades([tr], tier, self.reader, strict=False)
            self.assertEqual(skipped, 0)
            # exactly ONE cost charge per fill, two fills per round trip:
            # pnl = gross - 2 * per_side + financing
            expected = (gross
                        - 2.0 * K.bps_cost(tr["notional_usd"], float(tier))
                        + D.financing_adjustment_usd(self.reader, tr,
                                                     strict=False))
            self.assertAlmostEqual(pnls[0], expected, places=9)
        # hand-check the tier-2.0 primary: cost 2 x 3.00 = 6.00 USD
        self.assertEqual(K.bps_cost(10000.0, 2.0), 3.0)
        # financing hand-check: EMU 1.25 - US 2.00 = -0.75%/yr over the two
        # accrual days [06-03, 06-04): 10000 * -0.015 / 365
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


class TestDualBookConsistency(unittest.TestCase):
    def test_price_book_is_tier_invariant(self):
        tr = _hand_trade()
        p = D.price_pnl_usd(tr)
        self.assertAlmostEqual(p, tr["side"] * tr["notional_usd"]
                               * (tr["exit_price"] / tr["entry_price"] - 1.0),
                               places=12)


# ------------------------------------------------------------------- LOPO #
class TestLopoHandComputed(unittest.TestCase):
    def test_share_hand_computed(self):
        tmp = tempfile.mkdtemp()
        try:
            ledger = os.path.join(tmp, "l.jsonl")
            _tiny_ledger(ledger, {"EMU": 1.0, "US": 1.0})   # zero carry diff
            from research.assets.forex_free_v5.family_a6p1 import (
                LedgerVintageReader, dedupe_ledger_rows, load_ledger_rows)
            reader = LedgerVintageReader(
                dedupe_ledger_rows(load_ledger_rows(ledger)))
            a = _hand_trade(side=1, entry=1.0, exit_=1.005)   # gross +50
            a["pair"] = "AUDUSD"
            b = _hand_trade(side=1, entry=1.0, exit_=0.999)   # gross -10
            b["pair"] = "USDJPY"
            b["areas"] = ("US", "JP")
            share = D.lopo_share([a, b], reader)
            # drop AUDUSD -> [JP net] = -10 - 6 (tier-2.0 cost) < 0 -> not ok
            # drop USDJPY -> [AUD net] = +50 - 6 > 0 -> ok  => share 0.5
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
        "pair_concentration": {"AUDUSD": 0.2, "USDJPY": 0.2},
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

    def test_fail_closed_on_none_and_violations(self):
        rec = _all_pass_rec()
        rec["usd_drift_diag"] = {"evaluated": False, "corr": None}
        ok, reasons, rows = D.evaluate_gates(rec)
        self.assertFalse(ok)
        self.assertTrue(any(r["gate_id"].startswith("9_") and
                            r["margin"] is None for r in rows))
        rec2 = _all_pass_rec()
        rec2["base"]["expectancy"] = -0.1          # R4 mechanical reject
        ok2, reasons2, _ = D.evaluate_gates(rec2)
        self.assertFalse(ok2)
        self.assertTrue(any("1_expectancy" in s for s in reasons2))

    def test_dual_book_inversion_fails_gate6(self):
        rec = _all_pass_rec()
        rec["price_only_book"]["expectancy"] = -0.5   # price book inverts
        ok, reasons, rows = D.evaluate_gates(rec)
        self.assertFalse(ok)
        g6 = rows[5]
        self.assertEqual(g6["gate_id"], D.GATE_ORDER[5])
        self.assertEqual(g6["value"], 0.0)
        self.assertEqual(g6["margin"], 0.0)

    def test_control_reproducing_fails_gate10(self):
        rec = _all_pass_rec()
        ok, _r, rows = D.evaluate_gates(rec, anchor_expectancy=1.0)
        # control expectancy 1.0 >= 0.5 x anchor 1.0 and > 0 => R1 fires
        g10 = rows[9]
        self.assertEqual(g10["value"], 0.0)
        self.assertFalse(ok)

    def test_falsification_rules_hand_computed(self):
        f = D.falsification_rules(anchor_exp=1.0, neighbour_exp=1.2,
                                  control_exp=0.9)
        self.assertTrue(f["R1_nominal_shadow_kill"]["fires"])   # 0.9 >= 0.5
        self.assertTrue(f["R2_parameterization_kill"]["fires"]) # 1.2 >= 1.0
        self.assertFalse(f["R3_standardization_fragility_kill"]["fires"])
        self.assertFalse(f["R4_mechanical_reject"]["fires"])
        f2 = D.falsification_rules(anchor_exp=1.0, neighbour_exp=-0.2,
                                   control_exp=-1.0)
        self.assertFalse(f2["R1_nominal_shadow_kill"]["fires"])
        self.assertFalse(f2["R2_parameterization_kill"]["fires"])
        self.assertTrue(f2["R3_standardization_fragility_kill"]["fires"])
        f3 = D.falsification_rules(anchor_exp=-0.5, neighbour_exp=0.1,
                                   control_exp=0.1)
        self.assertTrue(f3["R4_mechanical_reject"]["fires"])


# ------------------------------------------------------- arm_config_digest #
class TestArmConfigDigest(unittest.TestCase):
    def test_stable_path_independent_and_arm_distinct(self):
        local = {a: F.arm_config_digest(a) for a in F.ARM_IDS}
        # recompute from a DIFFERENT working directory (path independence)
        proc = subprocess.run(
            [VENV_PY, "-c",
             "import sys, json; sys.path.insert(0, %r); "
             "from research.assets.forex_free_v8 import family_a5p1_v8 as F; "
             "print(json.dumps({a: F.arm_config_digest(a) "
             "for a in F.ARM_IDS}))" % ROOT],
            cwd=tempfile.mkdtemp(), capture_output=True, text=True,
            check=True)
        self.assertEqual(json.loads(proc.stdout), local)
        self.assertEqual(len(set(local.values())), 3)     # distinct per arm
        for dgst in local.values():
            self.assertEqual(len(dgst), 64)
            int(dgst, 16)                                  # hex sha256

    def test_digest_carried_on_every_decision(self):
        out = F.run_arm("anchor", SYNTH_PATHS)
        dgst = out["meta"]["arm_config_digest"]
        self.assertTrue(out["decisions"])
        for rec in out["decisions"]:
            self.assertEqual(rec["arm_config_digest"], dgst)


# -------------------------------------------------------- family on fixture #
class TestFamilyOnFixture(unittest.TestCase):
    def test_warmup_and_usable_grid(self):
        days = weekday_grid(date(2018, 4, 4), date(2020, 7, 31))
        out = F.run_arm("anchor", SYNTH_PATHS)
        m = out["meta"]
        # every fixture weekday binds (T-legs same-day class) => the first
        # usable clock is the one with 252 binding clocks strictly before,
        # i.e. days[252]; the first 252 binding clocks are burned.
        self.assertEqual(m["grid_clocks"], len(days))
        self.assertEqual(m["binding_clocks_total"], len(days))
        self.assertEqual(m["warmup_burned_clocks"], 252)
        self.assertEqual(m["first_usable_clock"], days[252].isoformat())
        self.assertEqual(m["usable_clock_list"][0], days[252].isoformat())
        self.assertEqual(m["usable_clocks"], len(days) - 252)

    def test_all_arms_nonvacuous_and_neighbour_waits_for_504(self):
        days = weekday_grid(date(2018, 4, 4), date(2020, 7, 31))
        schedules = {}
        for arm in F.ARM_IDS:
            out = F.run_arm(arm, SYNTH_PATHS)
            schedules[arm] = out
            self.assertGreater(out["meta"]["n_decisions"], 0, arm)
            self._walk_no_outcome(out)
        # neighbour z needs 504 bound values => no entry before days[503]
        neigh_first = min(d["entry_day"] for d in
                          schedules["neighbour"]["decisions"])
        self.assertGreaterEqual(neigh_first, days[503].isoformat())
        # anchor first entry is possible from the first usable clock
        anchor_first = min(d["entry_day"] for d in
                           schedules["anchor"]["decisions"])
        self.assertGreaterEqual(anchor_first,
                                schedules["anchor"]["meta"][
                                    "first_usable_clock"])
        # control (DGS10 level driver) does not reproduce the anchor walk
        ka = {(d["pair"], d["entry_day"]) for d in
              schedules["anchor"]["decisions"]}
        kc = {(d["pair"], d["entry_day"]) for d in
              schedules["control"]["decisions"]}
        self.assertNotEqual(ka, kc)

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

    def test_runner_output_is_pnl_free(self):
        for arm in F.ARM_IDS:
            out = F.run_arm(arm, SYNTH_PATHS)
            self._walk_no_outcome(out)

    def test_fail_closed_on_missing_staged(self):
        paths = dict(SYNTH_PATHS)
        paths["staged_dir"] = os.path.join(SYNTH_ROOT, "nope")
        with self.assertRaises(F.DataBlocked):
            F.run_arm("anchor", paths)


# ------------------------------------------------------------ dry-run CLI #
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

    def test_dryrun_report_sanitized_nonvacuous(self):
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
        self.assertEqual(report["schema"], "forex_free_v8_dryrun_report_v1")
        self.assertEqual(report["mode"], "dryrun_sanitized")
        self._walk(report)
        for arm in report["arms"]:
            self.assertTrue(arm["pnl_suppressed"])
            self.assertGreater(arm["n_decisions"], 0)
        adequacy = report["adequacy"]
        # the floors are frozen for the S0-scale census grid; on the small
        # synthetic fixture only the STRUCTURE is asserted (the floors are
        # exercised on the real-byte dry-run smoke, not in this suite)
        self.assertIn("pooled_anchor_entries", adequacy)
        self.assertIn("meets_floor", adequacy)
        self.assertIn("closure_if_unmet", adequacy)

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
            os.chdir(tempfile.mkdtemp(prefix="v8_refuse_"))
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
        tmp = tempfile.mkdtemp(prefix="v8_refuse2_")
        try:
            ctl = os.path.join(tmp, "research", "control",
                               "forex_free_v8_run")
            os.makedirs(ctl)
            with open(os.path.join(ctl, "run_contract.json"), "w") as f:
                json.dump({"cycle_id": "FOREX-FREE-V8",
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
        tmp = tempfile.mkdtemp(prefix="v8_refuse3_")
        try:
            ctl = os.path.join(tmp, "research", "control",
                               "forex_free_v8_run")
            os.makedirs(ctl)
            with open(os.path.join(ctl, "run_contract.json"), "w") as f:
                json.dump({"cycle_id": "FOREX-FREE-V8",
                           "s0_launch_authorized": True,
                           "s0_launch_authorized_verdict":
                               "FOREX_FREE_V8_S0_LAUNCH_AUTHORIZED",
                           "owner_go_fresh": True,
                           "owner_go_phrase": "GO FOREX V8 SCORED EXECUTION",
                           "budget": {"used": 6}}, f)
            os.chdir(tmp)
            proc = subprocess.run([VENV_PY, DRIVER, "scored"],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)
            payload = json.loads(proc.stdout)
            self.assertIn("budget", payload["missing_gates"])
        finally:
            os.chdir(cwd)
            shutil.rmtree(tmp, ignore_errors=True)

    def test_resolve_mode_alias(self):
        self.assertEqual(D.resolve_mode(None, True), "dryrun")
        self.assertEqual(D.resolve_mode("dryrun", False), "dryrun")
        self.assertEqual(D.resolve_mode("scored", False), "scored")
        self.assertIsNone(D.resolve_mode(None, False))

    def test_dry_run_flag_cli_on_real_paths(self):
        """--dry-run is an alias of the dryrun positional mode; exercised
        end-to-end only where the gitignored real bytes exist (a fresh twin
        without the local copies skips this smoke -- the synthetic suite
        above already covers the dry-run contract)."""
        staged = os.path.join(ROOT, "research", "control",
                              "forex_free_v8_run", "staged_vintaged")
        prices = os.path.join(ROOT, "data_raw", "forex_free_v1")
        if not (os.path.isdir(staged) and os.path.isdir(prices)):
            self.skipTest("local real-byte copies absent (gitignored)")
        proc = subprocess.run([VENV_PY, DRIVER, "--dry-run"], cwd=ROOT,
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        report = json.loads(proc.stdout)
        self.assertEqual(report["mode"], "dryrun_sanitized")
        self.assertTrue(report["adequacy"]["meets_floor"])


# -------------------------------------------------------- twin determinism #
CANON_CONTRACT = {
    "cycle_id": "FOREX-FREE-V8",
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
        dir_a = tempfile.mkdtemp(prefix="v8_twin_a_")
        dir_b = tempfile.mkdtemp(prefix="v8_twin_b_")
        try:
            art_a = self._smoke_in(dir_a)
            art_b = self._smoke_in(dir_b)
            self.assertEqual(sorted(art_a), sorted(art_b))
            for name in sorted(art_a):
                self.assertEqual(art_a[name], art_b[name],
                                 msg=f"artifact not byte-identical: {name}")
        finally:
            shutil.rmtree(dir_a, ignore_errors=True)
            shutil.rmtree(dir_b, ignore_errors=True)

    def test_emitted_artifacts_carry_canon_fields(self):
        dir_a = tempfile.mkdtemp(prefix="v8_canon_")
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
            # margins: 10 gates x 3 scored cells, every row complete
            mtf = [json.loads(ln) for ln in
                   art["margins_to_fail.jsonl"].decode().splitlines()
                   if ln.strip()]
            self.assertEqual(len(mtf), 30)
            for r in mtf:
                self.assertIn("gate_id", r)
                self.assertIn("value", r)
                self.assertIn("threshold", r)
                self.assertIn("margin", r)
            # per-period series covers the usable decision grid, one row per
            # clock per arm, none all-null
            pps = [json.loads(ln) for ln in
                   art["per_period_series.jsonl"].decode().splitlines()
                   if ln.strip()]
            by_arm = {}
            for r in pps:
                by_arm.setdefault(r["arm_id"], []).append(r)
            for arm_id, rows in by_arm.items():
                self.assertTrue(all(r["returns"] is not None for r in rows),
                                arm_id)
                self.assertEqual(len(rows),
                                 len({r["period"] for r in rows}))
            # control rows carry the AX2-C8 verdict + R1..R4 battery
            ctrl = [json.loads(ln) for ln in
                    art["control_rows.jsonl"].decode().splitlines()
                    if ln.strip()]
            self.assertTrue(any("ax2_c8" in r for r in ctrl))
            self.assertTrue(any(r.get("rule", "").startswith("R1_")
                                for r in ctrl))
        finally:
            shutil.rmtree(dir_a, ignore_errors=True)

    def test_governance_diagnostic_gate_passes_unchanged(self):
        """The V6/V7 governance machinery (research/governance/
        diagnostic_persistability.py) validates the V8 emission unchanged:
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


def test_launch_gate_reads_launch_gate_block_and_refusal_keys(tmp_path, monkeypatch):
    """F1 remediation (A7 finding F1): the scored gate reads the run
    contract's launch_gate.* block with the contract's own field names.
    Hand-check: a flipped contract yields NO missing keys; the shipped
    (unflipped) contract yields exactly [s0_launch_authorized,
    owner_fresh_go]."""
    import importlib, json, os
    drv = importlib.import_module("research.assets.forex_free_v8.exec_driver_v8")
    rc = json.load(open(os.path.join("research", "control", "forex_free_v8_run", "run_contract.json")))
    monkeypatch.setattr(drv, "RUN_CONTRACT_PATH", str(tmp_path / "run_contract.json"))
    shipped = json.loads(json.dumps(rc))
    with open(tmp_path / "run_contract.json", "w") as f:
        json.dump(shipped, f)
    assert drv._launch_gate_state() == ["s0_launch_authorized", "owner_fresh_go"]
    flipped = json.loads(json.dumps(rc))
    flipped["launch_gate"]["s0_launch_authorized"] = True
    flipped["launch_gate"]["a7_prelaunch_verdict"] = "FOREX_FREE_V8_S0_LAUNCH_AUTHORIZED"
    flipped["launch_gate"]["owner_go_fresh"] = True
    flipped["launch_gate"]["owner_go_phrase"] = "GO FOREX V8 SCORED EXECUTION"
    with open(tmp_path / "run_contract.json", "w") as f:
        json.dump(flipped, f)
    assert drv._launch_gate_state() == []
