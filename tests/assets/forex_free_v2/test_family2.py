"""FOREX-FREE-V2 family2 evidence tests (A9 implementation lane, F2-I).

Covers the 12 required evidence groups for FXFV2-A4-P2 "London-AM range break
confirmed by retest-hold":

 1. hand-computed state-machine goldens (range / break / retest-hold / void /
    control complement / neighbour E_B);
 2. hand-computed end-to-end golden (one UP + one DOWN trade, exact prices and
    times, booked through accounting.PositionBook with exact pnl/cost);
 3. PIT / one-event-lag + mutation test;
 4. DST: 2025-03-09, 2025-11-02 (US) and 2025-03-30, 2025-10-26 (EU) --
    London windows and the 16:00-New-York flat stamp at the correct UTC
    (20:00Z EDT / 21:00Z EST), evidenced on the Mondays that carry each
    regime (Sundays have no London-AM session);
 5. forced flat + absent 16:00-NY bar (resolvable early-flat fallback and the
    unresolvable NO_TRADE case);
 6. missing-bar fail-closed (invalid day, no fill-forward);
 7. determinism (identical schedule_digest twice);
 8. governor caps incl. the binding weekly case;
 9. drop-one-pair independence;
10. distinct anchor/neighbour/control digests on an all-three-fire fixture;
11. dummy publication refusal (no authorization => refuse; scored=false =>
    refuse a real publish; only a zero-byte dummy dry-run is allowed);
12. REAL-SNAPSHOT schedule-only frequency audit (NO PnL): all 7 pairs from the
    read-only V1 snapshot, 3 arms at tier 1.0, caps + proposal minimums.

Every expected number is a hand-computed literal with arithmetic comments in
goldens_family2.py.  No network; the real-data test computes COUNTS ONLY and
never touches PnL.
"""
from __future__ import annotations

import datetime as dt
import os
import sys
import unittest

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from research.assets.forex_free_v2 import accounting as ACC  # noqa: E402
from research.assets.forex_free_v2 import data_authority as DA  # noqa: E402
from research.assets.forex_free_v2 import family2 as F  # noqa: E402
from tests.assets.forex_free_v2 import goldens_family2 as G  # noqa: E402

UTC = dt.timezone.utc
TIER = 1.0


# --- helpers ----------------------------------------------------------------------- #
def by_stamp(rows):
    return {b["ts"]: b for b in F._validate_rows("TEST", rows)}


def events_for(rows, day):
    return F._day_events(by_stamp(rows), day)


def entry_dates(trades):
    return sorted(t["entry_ts"][:10] for t in trades)


def assert_caps(trades, pair):
    per_day, per_week = {}, {}
    for t in trades:
        assert t["pair"] == pair
        ts = DA.parse_stamp(t["entry_ts"])
        per_day[ts.date()] = per_day.get(ts.date(), 0) + 1
        week = F.week_monday_utc(ts)
        per_week[week] = per_week.get(week, 0) + 1
    assert max(per_day.values(), default=0) <= 1   # <=1 entry/pair/UTC-day
    assert max(per_week.values(), default=0) <= 3  # <=3 RT/pair/week
    return per_week


# =================================================================================== #
# 1. hand-computed state-machine goldens
# =================================================================================== #
class TestStateMachineGoldens(unittest.TestCase):

    def test_range_break_retest_golden_day1(self):
        day = dt.date(2025, 6, 2)
        ev = events_for(G.day1_up_invalidation(day), day)
        # L_H = max(1.1010, 1.1015, 1.1020, 1.1019) = 1.1020
        # L_L = min(1.1000, 1.1001, 1.1005, 1.1008) = 1.1000
        self.assertEqual((ev["L_H"], ev["L_L"]), (1.1020, 1.1000))
        self.assertFalse(ev["no_break"])
        self.assertFalse(ev["tie"])
        self.assertEqual(ev["side"], 1)                 # high 1.1025 > L_H 1.1020 -> UP
        self.assertEqual(ev["L_B"], 1.1020)             # broken range extreme
        self.assertEqual(ev["E_B"], 1.1025)             # break-bar high (far extreme)
        self.assertEqual(ev["break_ts"], G.U(2025, 6, 2, 11))
        # retest 12:00Z: low 1.1018 <= L_B 1.1020 AND close 1.1026 > 1.1020
        self.assertEqual(ev["anchor_retest_ts"], G.U(2025, 6, 2, 12))
        # neighbour vs E_B: low 1.1018 <= 1.1025 AND close 1.1026 > 1.1025
        self.assertEqual(ev["neigh_retest_ts"], G.U(2025, 6, 2, 12))
        self.assertIsNone(ev["void_ts"])                # close 1.1026 > L_H: no void

    def test_day2_neighbour_only_and_void(self):
        day = dt.date(2025, 6, 3)
        ev = events_for(G.day2_neighbour_void(day), day)
        self.assertEqual((ev["L_H"], ev["L_L"]), (1.1030, 1.1010))
        self.assertEqual((ev["side"], ev["L_B"], ev["E_B"]), (1, 1.1030, 1.1040))
        # 12:00Z bar: low 1.1036 <= E_B 1.1040 and close 1.1042 > 1.1040 -> neighbour;
        # anchor needs low <= L_B 1.1030 but 1.1036 > 1.1030 -> no touch, no fire
        self.assertIsNone(ev["anchor_retest_ts"])
        self.assertEqual(ev["neigh_retest_ts"], G.U(2025, 6, 3, 12))
        # 15:00Z bar: close 1.1028 < L_H 1.1030, before any anchor retest -> VOID
        self.assertEqual(ev["void_ts"], G.U(2025, 6, 3, 15))

    def test_day3_down_break_and_down_retest(self):
        day = dt.date(2025, 6, 4)
        ev = events_for(G.day3_down(day), day)
        self.assertEqual((ev["L_H"], ev["L_L"]), (1.2080, 1.2060))
        self.assertEqual(ev["side"], -1)                # low 1.2055 < L_L 1.2060 -> DOWN
        self.assertEqual((ev["L_B"], ev["E_B"]), (1.2060, 1.2055))  # E_B = break low
        # DOWN retest 12:00Z: high 1.2062 >= L_B 1.2060 AND close 1.2056 < 1.2060
        self.assertEqual(ev["anchor_retest_ts"], G.U(2025, 6, 4, 12))
        # neighbour DOWN vs E_B 1.2055: close 1.2056 < 1.2055 is FALSE -> no fire
        self.assertIsNone(ev["neigh_retest_ts"])
        self.assertIsNone(ev["void_ts"])                # DOWN void needs close > 1.2060

    def test_day4_immediate_void(self):
        day = dt.date(2025, 6, 5)
        ev = events_for(G.day4_void(day), day)
        self.assertEqual((ev["side"], ev["L_B"], ev["E_B"]), (1, 1.1022, 1.1030))
        # 12:00Z close 1.1018 < L_H 1.1022 -> void fires before any retest
        self.assertEqual(ev["void_ts"], G.U(2025, 6, 5, 12))
        self.assertIsNone(ev["anchor_retest_ts"])
        self.assertIsNone(ev["neigh_retest_ts"])

    def test_both_sides_in_one_bar_sign_rule(self):
        day = dt.date(2025, 6, 2)
        # break bar high 1.1030 > L_H 1.1020 AND low 1.0990 < L_L 1.1000;
        # midpoint = (1.1020 + 1.1000) / 2 = 1.1010
        up = events_for(G.both_sides_day(day, G.BOTH_SIDES_UP_CLOSE), day)
        self.assertEqual(up["side"], 1)                 # close 1.1015 > mid 1.1010
        self.assertEqual((up["L_B"], up["E_B"]), (1.1020, 1.1030))
        down = events_for(G.both_sides_day(day, G.BOTH_SIDES_DOWN_CLOSE), day)
        self.assertEqual(down["side"], -1)              # close 1.1005 < mid 1.1010
        self.assertEqual((down["L_B"], down["E_B"]), (1.1000, 1.0990))
        tie = events_for(G.both_sides_day(day, G.BOTH_SIDES_TIE_CLOSE), day)
        self.assertTrue(tie["tie"])                     # close == midpoint exactly
        self.assertEqual(tie["side"], 0)

    def test_exact_tie_day_is_a_no_trade_decision(self):
        sched = F.compute_arm_schedule(
            "anchor", {"EUR/USD": G.weekend_warmup(dt.date(2025, 5, 31))
                       + G.both_sides_day(dt.date(2025, 6, 2), G.BOTH_SIDES_TIE_CLOSE)})
        self.assertEqual(sched["trades"], [])
        self.assertEqual(sched["decisions"], 1)         # tie resolves the day
        self.assertEqual(sched["no_trade_days"], {"TIE_NO_TRADE": 1})

    def test_void_kills_anchor_and_control_takes_the_void(self):
        sched_a = F.compute_arm_schedule(
            "anchor", {"EUR/USD": G.weekend_warmup(dt.date(2025, 5, 31))
                       + G.day4_void(dt.date(2025, 6, 5))})
        self.assertEqual(sched_a["trades"], [])         # void kills the anchor
        self.assertEqual(sched_a["no_trade_days"], {"VOID": 1})
        self.assertEqual(sched_a["decisions"], 1)
        sched_c = F.compute_arm_schedule(
            "control", {"EUR/USD": G.weekend_warmup(dt.date(2025, 5, 31))
                        + G.day4_void(dt.date(2025, 6, 5))})
        # control complement: enters the ORIGINAL break direction (UP) on the void
        self.assertEqual(len(sched_c["trades"]), 1)
        trade = sched_c["trades"][0]
        self.assertEqual(trade["side"], 1)
        self.assertEqual(trade["entry_ts"], "2025-06-05T13:00:00Z")  # void 12:00Z + 1h
        self.assertEqual(trade["exit_reason"], "invalidation")
        self.assertEqual(trade["exit_price"], 1.1006)   # 17:00Z open (see goldens)
        self.assertEqual(trade["exit_ts"], "2025-06-05T17:00:00Z")

    def test_control_retest_first_day_is_a_no_trade_decision(self):
        # day3: anchor retest-hold fires first -> control's day resolves
        # RETEST_HOLD_FIRST (decision, no trade), neighbour NO_RESOLUTION.
        for arm, reasons, trades in (("control", {"RETEST_HOLD_FIRST": 1}, 0),
                                     ("neighbour", {"NO_RESOLUTION": 1}, 0)):
            sched = F.compute_arm_schedule(
                arm, {"EUR/USD": G.weekend_warmup(dt.date(2025, 5, 31))
                      + G.day3_down(dt.date(2025, 6, 4))})
            self.assertEqual(len(sched["trades"]), trades)
            self.assertEqual(sched["no_trade_days"], reasons)
            self.assertEqual(sched["decisions"], 1)


# =================================================================================== #
# 2. end-to-end golden UP + DOWN trades, booked through the accounting kernel
# =================================================================================== #
class TestEndToEndGolden(unittest.TestCase):

    def setUp(self):
        self.sched = F.compute_arm_schedule("anchor", G.four_day_week("EUR/USD"))
        self.by_entry = {t["entry_ts"]: t for t in self.sched["trades"]}

    def test_golden_up_trade_exact(self):
        trade = self.by_entry[G.GOLDEN_UP["entry_ts"]]
        expected = {"trade_id": "family2|anchor|EUR/USD|2025-06-02T13:00:00Z",
                    **G.GOLDEN_UP}
        self.assertEqual(trade, expected)

    def test_golden_down_trade_exact(self):
        trade = self.by_entry[G.GOLDEN_DOWN["entry_ts"]]
        expected = {"trade_id": "family2|anchor|EUR/USD|2025-06-04T13:00:00Z",
                    **G.GOLDEN_DOWN}
        self.assertEqual(trade, expected)

    def test_booked_pnl_and_cost_exact(self):
        book = ACC.PositionBook()
        for golden, side in ((G.GOLDEN_UP, "LONG"), (G.GOLDEN_DOWN, "SHORT")):
            tid = f"family2|anchor|EUR/USD|{golden['entry_ts']}"
            book.open_position(trade_id=tid, pair="EUR/USD", side=side,
                               notional_usd=10000.0, price=golden["entry_price"],
                               ts_utc=golden["entry_ts"], cost_tier=1.0)
            book.close_position(tid, golden["exit_price"], golden["exit_ts"])
        self.assertEqual(len(book.closed_trades), 2)
        up, down = book.closed_trades
        # UP: pnl = +1 * 10000 * (1.1015 / 1.1024 - 1) = 10000 * (-0.0009/1.1024)
        #       = -8.16057979... USD (exact same float ops as the kernel)
        self.assertEqual(up.pnl_usd, 10000.0 * (1.1015 / 1.1024 - 1.0))
        # DOWN: pnl = -1 * 10000 * (1.2064 / 1.2057 - 1) = 10000 * (0.0007/1.2057)
        #       = +5.80590461... USD
        self.assertEqual(down.pnl_usd, -10000.0 * (1.2064 / 1.2057 - 1.0))
        # cost: 1.5 bps/side x tier 1.0 on the 10000 USD-unit notional
        #       = 10000 * 1.5 / 10000 = exactly 1.50 USD per side
        self.assertEqual(up.entry_cost_usd, 1.5)
        self.assertEqual(up.exit_cost_usd, 1.5)
        self.assertEqual(down.entry_cost_usd, 1.5)
        self.assertEqual(down.exit_cost_usd, 1.5)
        self.assertEqual(book.total_cost_usd, 6.0)      # 2 trades x 2 sides x 1.50
        self.assertEqual(up.net_pnl_usd, up.pnl_usd - 3.0)
        self.assertEqual(down.net_pnl_usd, down.pnl_usd - 3.0)
        self.assertEqual(book.pnl_usd_total,
                         10000.0 * (1.1015 / 1.1024 - 1.0)
                         + -10000.0 * (1.2064 / 1.2057 - 1.0))

    def test_no_pnl_fields_anywhere_in_schedule(self):
        forbidden = {"pnl", "pnl_usd", "net", "net_pnl", "cost", "cost_usd",
                     "return", "returns", "gross"}
        for trade in self.sched["trades"]:
            self.assertFalse(forbidden & set(trade), "schedule must carry NO PnL fields")
        self.assertEqual(set(self.sched["trades"][0]),
                         {"trade_id", "pair", "side", "notional_usd", "entry_price",
                          "entry_ts", "decision_ts", "exit_price", "exit_ts",
                          "exit_reason"})

    def test_four_day_arm_ledgers_exact(self):
        ledgers = {}
        for arm in F.ARMS:
            sched = F.compute_arm_schedule(arm, G.four_day_week("EUR/USD"))
            ledgers[arm] = sched
            self.assertEqual(sched["decisions"], 4)     # all four days resolve
        # anchor: trades day1 (retest) + day3 (retest); voided day2/day4
        self.assertEqual(entry_dates(ledgers["anchor"]["trades"]),
                         ["2025-06-02", "2025-06-04"])
        self.assertEqual(ledgers["anchor"]["no_trade_days"], {"VOID": 2})
        # neighbour: trades day1 + day2 (neighbour-only fire); day4 void, day3 unresolved
        self.assertEqual(entry_dates(ledgers["neighbour"]["trades"]),
                         ["2025-06-02", "2025-06-03"])
        self.assertEqual(ledgers["neighbour"]["no_trade_days"],
                         {"VOID": 1, "NO_RESOLUTION": 1})
        # control: trades the two void days (day2 forced-flat, day4 invalidation)
        self.assertEqual(entry_dates(ledgers["control"]["trades"]),
                         ["2025-06-03", "2025-06-05"])
        self.assertEqual(ledgers["control"]["no_trade_days"], {"RETEST_HOLD_FIRST": 2})
        # control day2 golden: forced flat at the 16:00-New-York bar (20:00Z EDT)
        ctrl_day2 = [t for t in ledgers["control"]["trades"]
                     if t["entry_ts"] == G.GOLDEN_CONTROL_DAY2["entry_ts"]][0]
        self.assertEqual(ctrl_day2, {"trade_id": "family2|control|EUR/USD|2025-06-03T16:00:00Z",
                                     "pair": "EUR/USD", "notional_usd": 10000.0,
                                     **G.GOLDEN_CONTROL_DAY2})
        for arm in F.ARMS:
            assert_caps(ledgers[arm]["trades"], "EUR/USD")


# =================================================================================== #
# 3. PIT / one-event lag + mutation
# =================================================================================== #
class TestPITAndMutation(unittest.TestCase):

    def test_one_event_lag_entry_instants(self):
        # decision_ts = decision-bar CLOSE instant (= decision bar-open + 1h),
        # and the tier-1.0 entry bar IS the next H1 bar: entry_ts == decision_ts.
        # Tier 2.0 delays every fill one more event: entry_ts = decision_ts + 1h.
        for tier, lag in ((1.0, dt.timedelta(0)), (2.0, dt.timedelta(hours=1))):
            sched = F.compute_arm_schedule("anchor", G.four_day_week("EUR/USD"),
                                           cost_tier=tier)
            self.assertGreaterEqual(len(sched["trades"]), 1)
            for trade in sched["trades"]:
                decision = DA.parse_stamp(trade["decision_ts"])
                entry = DA.parse_stamp(trade["entry_ts"])
                self.assertEqual(entry - decision, lag, (tier, trade["entry_ts"]))

    def test_mutation_after_entry_cannot_change_forced_flat_schedule(self):
        # On a forced-flat day every bar strictly AFTER the entry bar is read by
        # nothing: entry = decision+1h, exit = the 16:00-NY bar open.  Perturb
        # bars 14:00Z..19:00Z (neither the entry bar nor the flat bar) and the
        # schedule must be byte-identical.
        day = dt.date(2025, 6, 2)
        base_rows = G.weekend_warmup(dt.date(2025, 5, 31)) + G.london_hours_day(day, True)
        perturbed = []
        for b in base_rows:
            if "2025-06-02 14:00:00" <= b["datetime"] <= "2025-06-02 19:00:00":
                b = dict(b, open=2.0, high=2.5, low=1.5, close=2.25)
            perturbed.append(b)
        s1 = F.compute_arm_schedule("anchor", {"EUR/USD": base_rows})
        s2 = F.compute_arm_schedule("anchor", {"EUR/USD": perturbed})
        self.assertEqual(s1["schedule_digest"], s2["schedule_digest"])
        self.assertEqual(s1["trades"], s2["trades"])
        self.assertEqual(s1["trades"][0]["exit_reason"], "forced_flat")

    def test_mutation_of_invalidation_bar_moves_exit_not_entry(self):
        # The decision/ENTRY core is PIT (fixed at the decision bar); only the
        # exit may move, and only per the frozen invalidation law.
        day = dt.date(2025, 6, 2)
        base_rows = G.weekend_warmup(dt.date(2025, 5, 31)) + G.day1_up_invalidation(day)
        perturbed = []
        for b in base_rows:
            if b["datetime"] == "2025-06-02 14:00:00":
                b = dict(b, close=1.1030)  # no longer < L_H 1.1020 -> no invalidation
            perturbed.append(b)
        s1 = F.compute_arm_schedule("anchor", {"EUR/USD": base_rows})
        s2 = F.compute_arm_schedule("anchor", {"EUR/USD": perturbed})
        t1 = s1["trades"][0]
        t2 = [t for t in s2["trades"] if t["entry_ts"] == t1["entry_ts"]][0]
        self.assertEqual((t1["decision_ts"], t1["entry_ts"], t1["entry_price"]),
                         (t2["decision_ts"], t2["entry_ts"], t2["entry_price"]))
        # t1: 14:00Z close 1.1015 < L_H 1.1020 -> exit 15:00Z open 1.1015
        self.assertEqual(t1["exit_ts"], "2025-06-02T15:00:00Z")
        # t2: the 15:00Z bar (close 1.1008 < L_H 1.1020) is now the first
        # invalidating bar -> exit one event later, at 16:00Z open 1.1008
        self.assertEqual(t2["exit_ts"], "2025-06-02T16:00:00Z")
        self.assertEqual(t2["exit_price"], 1.1008)
        self.assertEqual(t2["exit_reason"], "invalidation")
        self.assertNotEqual(s1["schedule_digest"], s2["schedule_digest"])

    def test_missing_entry_bar_is_never_fill_forwarded(self):
        day = dt.date(2025, 6, 2)
        rows = [b for b in G.day1_up_invalidation(day)
                if b["datetime"] != "2025-06-02 13:00:00"]
        sched = F.compute_arm_schedule(
            "anchor", {"EUR/USD": G.weekend_warmup(dt.date(2025, 5, 31)) + rows})
        self.assertEqual(sched["trades"], [])           # signal voided, never queued
        self.assertEqual(sched["decisions"], 1)         # decision counted without trade
        self.assertEqual(sched["no_trade_days"], {"MISSING_ENTRY_BAR": 1})


# =================================================================================== #
# 4. DST transitions
# =================================================================================== #
class TestDST(unittest.TestCase):

    def test_transition_instants_map_correctly(self):
        for day, expected in G.DST_TRANSITION_FLAT_INSTANTS.items():
            # 16:00 America/New_York on each named transition date:
            # 2025-03-09 -> 20:00Z (EDT), 2025-11-02 -> 21:00Z (EST),
            # 2025-03-30 -> 20:00Z (NY already EDT), 2025-10-26 -> 20:00Z (NY still EDT)
            self.assertEqual(DA.flat_bar_instant_utc(day).strftime("%Y-%m-%dT%H:%M:%SZ"),
                             expected)

    def test_london_windows_and_flat_bar_on_regime_mondays(self):
        for monday, london08_hour, entry_ts, inv_exit_ts, flat_ts in G.DST_CASES:
            sat = monday - dt.timedelta(days=2)
            # invalidation variant: exact entry/exit instants per regime
            sched = F.compute_arm_schedule(
                "anchor", {"EUR/USD": G.weekend_warmup(sat)
                           + G.london_hours_day(monday, hold_flat=False)})
            self.assertEqual(sched["warmup_first_evaluable_date"], monday.isoformat())
            trade = sched["trades"][0]
            self.assertEqual(trade["entry_ts"], entry_ts, monday)   # London 14:00 in UTC
            self.assertEqual(trade["exit_ts"], inv_exit_ts, monday)  # invalidation exit
            self.assertEqual(trade["exit_reason"], "invalidation")
            # London 08:00 wall -> the correct UTC hour in every regime
            london08 = F._wall_open_utc(monday, 8)
            self.assertEqual(london08.hour, london08_hour)  # 07Z BST weeks / 08Z GMT weeks
            # forced-flat variant: exit at the 16:00-New-York bar open
            rows = G.weekend_warmup(sat) + G.london_hours_day(monday, hold_flat=True)
            sched2 = F.compute_arm_schedule("anchor", {"EUR/USD": rows})
            trade2 = sched2["trades"][0]
            self.assertEqual(trade2["exit_reason"], "forced_flat", monday)
            self.assertEqual(trade2["exit_ts"], flat_ts, monday)  # 20:00Z EDT / 21:00Z EST
            stamp = flat_ts.replace("T", " ").replace("Z", "")    # td_loader stamp format
            flat_row = [b for b in rows if b["datetime"] == stamp][0]
            self.assertEqual(trade2["exit_price"], flat_row["open"])


# =================================================================================== #
# 5. forced flat + absent 16:00-New-York bar
# =================================================================================== #
class TestForcedFlat(unittest.TestCase):

    def _friday(self, drop):
        if drop is None:
            # the 16:00-New-York bar (20:00Z) is absent on this Friday (weekly
            # close lands exactly at 16:00 NY, so that bar never exists)
            rows = [b for b in G.friday_early_flat_day()
                    if b["datetime"] != "2025-06-06 20:00:00"]
        else:
            rows = G.friday_early_flat_day(drop_after_hour=drop)
        return {"EUR/USD": G.weekend_warmup(dt.date(2025, 5, 31)) + rows}

    def test_absent_flat_bar_with_preceding_bar_early_forced_flat(self):
        # Friday weekly close: the 16:00-New-York bar (20:00Z) does not exist;
        # the latest existing bar between entry (13:00Z) and the flat instant
        # is 19:00Z = London 20:00 BST, hold-variant open 1.1028 -> early
        # forced flat there.
        sched = F.compute_arm_schedule("anchor", self._friday(None))
        self.assertEqual(len(sched["trades"]), 1)
        trade = sched["trades"][0]
        self.assertEqual(trade["exit_reason"], "forced_flat")
        self.assertEqual(trade["exit_ts"], "2025-06-06T19:00:00Z")
        self.assertEqual(trade["exit_price"], 1.1028)
        self.assertEqual(sched["early_forced_flat_count"], 1)

    def test_absent_flat_bar_unresolvable_is_no_trade_fail_closed(self):
        # No bar at all between the entry (13:00Z) and the flat instant: the
        # position can never be flattened -> NO_TRADE, never fill-forward.
        sched = F.compute_arm_schedule("anchor", self._friday(13))
        self.assertEqual(sched["trades"], [])
        self.assertEqual(sched["decisions"], 1)
        self.assertEqual(sched["no_trade_days"], {"MISSING_FLAT_BAR": 1})
        self.assertEqual(sched["early_forced_flat_count"], 0)

    def test_forced_flat_bounds_invalidation_exit(self):
        # Day2 control: no invalidation before 16:00-New-York -> flat at 20:00Z
        # even though later bars exist (never crosses the rollover).
        sched = F.compute_arm_schedule("control", G.four_day_week("EUR/USD"))
        day2 = [t for t in sched["trades"] if t["entry_ts"].startswith("2025-06-03")]
        self.assertEqual(day2[0]["exit_ts"], "2025-06-03T20:00:00Z")
        self.assertEqual(day2[0]["exit_reason"], "forced_flat")


# =================================================================================== #
# 6. missing-bar fail-closed
# =================================================================================== #
class TestMissingBarFailClosed(unittest.TestCase):

    def test_missing_london_am_bar_invalidates_the_whole_day(self):
        day = dt.date(2025, 6, 2)
        rows = [b for b in G.day1_up_invalidation(day)
                if b["datetime"] != "2025-06-02 08:00:00"]  # London 09:00 range bar
        sched = F.compute_arm_schedule(
            "anchor", {"EUR/USD": G.weekend_warmup(dt.date(2025, 5, 31)) + rows})
        self.assertEqual(sched["trades"], [])
        self.assertEqual(sched["decisions"], 0)         # not even a decision
        self.assertEqual(sched["no_trade_days"], {"MISSING_RANGE_BAR": 1})

    def test_missing_range_bar_is_not_rescued_by_later_bars(self):
        # Break and retest bars all present -- still NO_TRADE, no fill-forward.
        day = dt.date(2025, 6, 2)
        rows = [b for b in G.day1_up_invalidation(day)
                if b["datetime"] != "2025-06-02 07:00:00"]  # first range bar gone
        universe = {"EUR/USD": G.weekend_warmup(dt.date(2025, 5, 31)) + rows}
        for arm in F.ARMS:
            sched = F.compute_arm_schedule(arm, universe)
            self.assertEqual(sched["trades"], [])
            self.assertEqual(sched["no_trade_days"], {"MISSING_RANGE_BAR": 1})

    def test_invalid_rows_fail_closed(self):
        good = G.day1_up_invalidation(dt.date(2025, 6, 2))
        with pytest.raises(F.Family2Error):
            F.compute_arm_schedule("anchor", {"EUR/USD": []})
        with pytest.raises(F.Family2Error):
            F.compute_arm_schedule("anchor", {"EUR/USD": good + good[:1]})  # duplicate
        with pytest.raises(F.Family2Error):
            F.compute_arm_schedule("bogus_arm", {"EUR/USD": good})          # bad arm
        with pytest.raises(F.Family2Error):
            F.compute_arm_schedule("anchor", {"EUR/USD": good}, cost_tier=9.0)


# =================================================================================== #
# 7. determinism
# =================================================================================== #
class TestDeterminism(unittest.TestCase):

    def test_identical_digest_twice(self):
        s1 = F.compute_arm_schedule("anchor", G.four_day_week("EUR/USD"))
        s2 = F.compute_arm_schedule("anchor", G.four_day_week("EUR/USD"))
        self.assertEqual(s1, s2)
        self.assertEqual(s1["schedule_digest"], s2["schedule_digest"])
        self.assertRegex(s1["schedule_digest"], r"^[0-9a-f]{64}$")
        # digest is sha256 of the canonical JSON bytes of the fixed record
        record = {k: s1[k] for k in ("family_id", "proposal_id", "arm", "cost_tier",
                                     "decisions", "no_trade_days", "trades")}
        self.assertEqual(s1["schedule_digest"],
                         ACC.sha256_hex(ACC.canonical_json_bytes(record)))

    def test_tier_changes_digest(self):
        s1 = F.compute_arm_schedule("anchor", G.four_day_week("EUR/USD"), cost_tier=1.0)
        s2 = F.compute_arm_schedule("anchor", G.four_day_week("EUR/USD"), cost_tier=2.0)
        self.assertNotEqual(s1["schedule_digest"], s2["schedule_digest"])


# =================================================================================== #
# 8. governor caps (incl. binding case)
# =================================================================================== #
class TestGovernor(unittest.TestCase):

    def test_weekly_cap_binds_and_skips_never_queues(self):
        sched = F.compute_arm_schedule("anchor", G.governor_week("GBP/USD"))
        dates = entry_dates(sched["trades"])
        # week [2025-06-02, 2025-06-09): days 1-3 book (cap = 3 RT);
        # the 4th day is DROPPED (skip, never queue); next Monday books again
        self.assertEqual(dates, ["2025-06-02", "2025-06-03", "2025-06-04", "2025-06-09"])
        self.assertEqual(sched["no_trade_days"], {"WEEKLY_CAP": 1})
        self.assertEqual(sched["decisions"], 5)         # capped day still a decision
        per_week = assert_caps(sched["trades"], "GBP/USD")
        self.assertEqual(max(per_week.values()), 3)     # cap exactly reached

    def test_daily_cap_structural(self):
        sched = F.compute_arm_schedule("anchor", G.four_day_week("EUR/USD"))
        per_day = {}
        for t in sched["trades"]:
            key = (t["pair"], t["entry_ts"][:10])
            per_day[key] = per_day.get(key, 0) + 1
        self.assertTrue(all(v <= 1 for v in per_day.values()))
        self.assertNotIn("DAILY_CAP", sched["no_trade_days"])


# =================================================================================== #
# 9. drop-one-pair independence
# =================================================================================== #
class TestDropOnePair(unittest.TestCase):

    def test_pair_schedules_are_independent(self):
        rows = G.four_day_week("EUR/USD")["EUR/USD"]
        both = F.compute_arm_schedule("anchor", {"EUR/USD": rows, "GBP/USD": rows})
        solo_eur = F.compute_arm_schedule("anchor", {"EUR/USD": rows})
        solo_gbp = F.compute_arm_schedule("anchor", {"GBP/USD": rows})
        eur_full = [t for t in both["trades"] if t["pair"] == "EUR/USD"]
        gbp_full = [t for t in both["trades"] if t["pair"] == "GBP/USD"]
        self.assertEqual(eur_full, solo_eur["trades"])
        self.assertEqual(gbp_full, solo_gbp["trades"])
        self.assertEqual(both["decisions"],
                         solo_eur["decisions"] + solo_gbp["decisions"])
        self.assertEqual(both["trades"],
                         sorted(solo_eur["trades"] + solo_gbp["trades"],
                                key=lambda t: (t["pair"], t["entry_ts"])))


# =================================================================================== #
# 10. distinct digests on an all-three-fire fixture
# =================================================================================== #
class TestThreeArmDistinctDigests(unittest.TestCase):

    def test_all_three_arms_fire_and_digests_differ(self):
        schedules = {arm: F.compute_arm_schedule(arm, G.four_day_week("EUR/USD"))
                     for arm in F.ARMS}
        # every arm fires at least once on the same 4-day fixture
        for arm, sched in schedules.items():
            self.assertGreaterEqual(len(sched["trades"]), 1, arm)
            self.assertEqual(sched["decisions"], 4)     # shared break-day resolutions
        digests = {arm: s["schedule_digest"] for arm, s in schedules.items()}
        self.assertEqual(len(set(digests.values())), 3)  # pairwise distinct
        self.assertEqual(len(schedules["anchor"]["trades"]), 2)
        self.assertEqual(len(schedules["neighbour"]["trades"]), 2)
        self.assertEqual(len(schedules["control"]["trades"]), 2)

    def test_module_identity(self):
        self.assertEqual(F.FAMILY_ID, "family2")
        self.assertEqual(F.PROPOSAL_ID, "FXFV2-A4-P2")
        self.assertEqual(F.ARMS, ("anchor", "neighbour", "control"))


# =================================================================================== #
# 11. dummy publication refusal
# =================================================================================== #
class TestPublicationRefusal(unittest.TestCase):

    def test_no_authorization_refuses_any_publication(self):
        record = {"family_id": F.FAMILY_ID, "arm": "anchor"}
        with tempfile_ledger() as ledger:
            for kwargs in ({"authorization": None, "scored": True, "real_pnl": True},
                           {"authorization": "please", "scored": True, "real_pnl": True},
                           {"authorization": None, "scored": False, "real_pnl": False}):
                with pytest.raises(F.PublicationRefused, match="NO_AUTHORIZATION"):
                    F.authorized_publication(record, ledger, **kwargs)
            self.assertFalse(os.path.exists(ledger))    # zero bytes written

    def test_scored_false_refuses_real_publish(self):
        record = {"family_id": F.FAMILY_ID, "arm": "anchor"}
        with tempfile_ledger() as ledger:
            with pytest.raises(F.PublicationRefused, match="SCORED_FALSE"):
                F.authorized_publication(record, ledger,
                                         authorization=F.AUTHORIZATION_TOKEN,
                                         scored=False, real_pnl=True)
            self.assertFalse(os.path.exists(ledger))
            # dummy dry-run allowed: scored=False, real_pnl=False, ZERO bytes
            verdict = F.authorized_publication(record, ledger,
                                               authorization=F.AUTHORIZATION_TOKEN,
                                               scored=False, real_pnl=False)
            self.assertEqual(verdict["mode"], "dummy_dry_run")
            self.assertEqual(verdict["wrote_bytes"], 0)
            self.assertFalse(os.path.exists(ledger))

    def test_authorized_scored_real_publish_is_once_only(self):
        record = {"family_id": F.FAMILY_ID, "arm": "anchor", "n": 1}
        with tempfile_ledger() as ledger:
            first = F.authorized_publication(record, ledger,
                                             authorization=F.AUTHORIZATION_TOKEN,
                                             scored=True, real_pnl=True)
            self.assertEqual((first["observed_delta"], first["published_now"]), (1, 1))
            self.assertTrue(os.path.exists(ledger))
            replay = F.authorized_publication(record, ledger,
                                              authorization=F.AUTHORIZATION_TOKEN,
                                              scored=True, real_pnl=True)
            self.assertEqual((replay["observed_delta"], replay["published_now"]), (0, 0))


class tempfile_ledger:
    """Temporary ledger path context manager (no file is created up front)."""

    def __enter__(self):
        import tempfile
        self.dir = tempfile.TemporaryDirectory()
        return os.path.join(self.dir.name, "family2_ledger.jsonl")

    def __exit__(self, *exc):
        self.dir.cleanup()
        return False


# =================================================================================== #
# 12. REAL-SNAPSHOT schedule-only frequency audit (NO PnL)
# =================================================================================== #
SNAPSHOT_DATA_ROOT = DA.SNAPSHOT_DATA_ROOT


@unittest.skipUnless(os.path.isdir(SNAPSHOT_DATA_ROOT),
                     f"read-only V1 snapshot not present at {SNAPSHOT_DATA_ROOT}")
class TestRealSnapshotFrequencyAudit(unittest.TestCase):
    """Schedule-only audit over the READ-ONLY V1 snapshot (7 pairs, 3 arms,
    tier 1.0).  COUNTS ONLY: no PnL is computed, printed or asserted."""

    def test_frequency_audit_all_pairs_three_arms(self):
        from research.assets.forex_free_v1 import td_loader
        rows_by_pair = {pair: td_loader.load_pair_h1(pair, SNAPSHOT_DATA_ROOT)[0]
                        for pair in F.PAIR_UNIVERSE}
        self.assertEqual(len(rows_by_pair), 7)
        schedules = {arm: F.compute_arm_schedule(arm, rows_by_pair, cost_tier=1.0)
                     for arm in F.ARMS}

        # frozen proposal minimums (minimum_decisions / minimum_trades_per_cell)
        PER_PAIR_DECISION_MINIMUM = 500      # per_pair_full_sample_minimum
        AGGREGATE_TRADE_MINIMUM = 1800       # full_sample_aggregate_minimum

        counts = {}
        for arm, sched in schedules.items():
            trades = sched["trades"]
            counts[arm] = {"decisions": sched["decisions"], "trades": len(trades),
                           "no_trade_days": sched["no_trade_days"],
                           "digest": sched["schedule_digest"],
                           "warmup_first_evaluable_date": sched["warmup_first_evaluable_date"],
                           "early_forced_flats": sched["early_forced_flat_count"]}
            # caps: <=1 entry/pair/UTC-day, <=3 RT/pair/[Mon 00:00Z week)
            per_day, per_week = {}, {}
            for t in trades:
                ts = DA.parse_stamp(t["entry_ts"])
                per_day[(t["pair"], ts.date())] = per_day.get((t["pair"], ts.date()), 0) + 1
                week = F.week_monday_utc(ts)
                per_week[(t["pair"], week)] = per_week.get((t["pair"], week), 0) + 1
            self.assertLessEqual(max(per_day.values(), default=0), 1, arm)
            self.assertLessEqual(max(per_week.values(), default=0), 3, arm)
            counts[arm]["binding_pair_weeks"] = sum(1 for v in per_week.values() if v == 3)
            counts[arm]["populated_pair_weeks"] = len(per_week)
            counts[arm]["pairs_trading"] = len({t["pair"] for t in trades})
            # proposal minimum: full-sample aggregate trades per arm
            self.assertGreaterEqual(len(trades), AGGREGATE_TRADE_MINIMUM, arm)
            # structural invariant: a decision = one day on which the arm's
            # state machine resolved.  Every reason except MISSING_RANGE_BAR
            # and NO_BREAK (which preclude a resolution) maps to exactly one
            # decision, and each booked trade is one resolved decision day.
            non_decisions = (sched["no_trade_days"].get("MISSING_RANGE_BAR", 0)
                             + sched["no_trade_days"].get("NO_BREAK", 0))
            self.assertEqual(sched["decisions"],
                             len(trades) + sum(sched["no_trade_days"].values())
                             - non_decisions)
            for t in trades:  # schedule-only attestation: NO PnL fields, fixed schema
                self.assertEqual(set(t), {"trade_id", "pair", "side", "notional_usd",
                                          "entry_price", "entry_ts", "decision_ts",
                                          "exit_price", "exit_ts", "exit_reason"})

        # decisions identical across arms (same break days, shared state machine)
        self.assertEqual(schedules["anchor"]["decisions"],
                         schedules["neighbour"]["decisions"])
        self.assertEqual(schedules["anchor"]["decisions"],
                         schedules["control"]["decisions"])

        # per-pair decision floor (anchor arm, full sample)
        per_pair_decisions = {}
        for pair in F.PAIR_UNIVERSE:
            one = F.compute_arm_schedule("anchor", {pair: rows_by_pair[pair]})
            per_pair_decisions[pair] = one["decisions"]
            self.assertGreaterEqual(one["decisions"], PER_PAIR_DECISION_MINIMUM, pair)
        counts["per_pair_decisions_anchor"] = per_pair_decisions

        # direction check: the mechanism is direction-agnostic; both sides appear
        for arm, sched in schedules.items():
            longs = sum(1 for t in sched["trades"] if t["side"] == 1)
            shorts = len(sched["trades"]) - longs
            counts[arm]["longs"], counts[arm]["shorts"] = longs, shorts
            self.assertGreater(longs, 0, arm)
            self.assertGreater(shorts, 0, arm)

        # realized frequency (counts only): RT / pair / week over the traded span
        first = min(DA.parse_stamp(t["entry_ts"]) for t in schedules["anchor"]["trades"])
        last = max(DA.parse_stamp(t["entry_ts"]) for t in schedules["anchor"]["trades"])
        span_weeks = ((last - first).total_seconds() / 86400 + 1) / 7.0
        for arm in F.ARMS:
            counts[arm]["rt_per_pair_per_week"] = round(
                len(schedules[arm]["trades"]) / (len(F.PAIR_UNIVERSE) * span_weeks), 4)
        counts["span_weeks"] = round(span_weeks, 2)
        counts["first_entry"] = first.strftime("%Y-%m-%dT%H:%M:%SZ")
        counts["last_entry"] = last.strftime("%Y-%m-%dT%H:%M:%SZ")
        # lane_report_family2.json carries these counts (schedule-only, no PnL)
        print("\nFAMILY2 REAL-SNAPSHOT SCHEDULE COUNTS:", counts)


if __name__ == "__main__":
    unittest.main()
