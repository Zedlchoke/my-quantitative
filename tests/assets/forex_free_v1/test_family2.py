"""Synthetic-golden tests for FXFV1-A3-P2 (family-2, late-NY fade).

Scope (F6 family-2): prove the FROZEN mechanism mechanics on hand-built
synthetic fixtures with hand-computed goldens (goldens_family2.py):

  * z-threshold trigger / no-trade / warm-up fail-closed
  * PIT sigma20 (strictly PRIOR rollover-to-rollover closes)
  * Tokyo-open neighbour and sign-flipped continuation causal control
  * flatten-bar clock across BOTH US DST transitions (EST end 21:00Z /
    EDT end 20:00Z, strictly < 17:00 America/New_York)
  * next-allowed-bar fill; S3 delay tier shifts entry exactly one bar
  * exact hand-computed costs at each frozen tier
  * arm digests distinct/stable; double-generation identical canonical
    sha256; idempotent publish (tmp_path)
  * exact-arm dry run: synthetic 2-pair x ~500-hour fixture spanning one
    US DST transition incl. >= 25 prior rollover closes; 3 arms run;
    temporary ledger under gitignored data_raw/forex_free_v1/dryrun/;
    digest asserted; replay adds zero rows; schedule-only feasibility
    (decisions/yr, turnover, cost drag) recorded.

NO real provider data and NO scored PnL anywhere in this module.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

ROOT = Path(__file__).resolve().parents[3]
for p in (str(ROOT), str(Path(__file__).resolve().parent)):
    if p not in sys.path:
        sys.path.insert(0, p)

from research.assets.forex_free_v1 import family2 as f2  # noqa: E402
import goldens_family2 as g  # noqa: E402

UTC = timezone.utc
NY = ZoneInfo("America/New_York")
TKY = ZoneInfo("Asia/Tokyo")
HOUR = timedelta(hours=1)
A = g.SIGMA_A  # 0.001, alternating sigma fixture amplitude


def utc(dt: datetime) -> datetime:
    return dt.astimezone(UTC)


def ny_dt(day: date, hour: int) -> datetime:
    """UTC instant of a whole NY wall-clock hour (EST/EDT per zoneinfo)."""
    return utc(datetime(day.year, day.month, day.day, hour, tzinfo=NY))


def tky_dt(day: date, hour: int) -> datetime:
    return utc(datetime(day.year, day.month, day.day, hour, tzinfo=TKY))


def add_bar(rows, open_dt: datetime, px: float):
    rows.append({
        "datetime": open_dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "open": px, "high": px, "low": px, "close": px,
    })


def prev_weekday(day: date) -> date:
    step = {0: 3, 6: 2}.get(day.weekday(), 1)
    return day - timedelta(days=step)


def prior_weekdays(signal_ny_date: date, n: int) -> list:
    days, d = [], signal_ny_date
    for _ in range(n):
        d = prev_weekday(d)
        days.append(d)
    return list(reversed(days))


def add_prior_close_bars(rows, signal_ny_dates, n=21, a=A, base=1.0):
    """One 16:00-NY-close bar per prior FX trading day (union over the
    signal dates), closes chained by alternating +/-a daily log returns.

    Hand check: any 20 consecutive terms of a strictly alternating +/-a
    sequence hold ten +a and ten -a, so every signal day's trailing 20
    returns have mean 0 and sample stdev a*sqrt(20/19) = GOLDEN_SIGMA20.
    """
    needed = set()
    for d in signal_ny_dates:
        needed.update(prior_weekdays(d, n))
    # deterministic alternating chain over the sorted union:
    px = base
    for i, day in enumerate(sorted(needed)):
        px = px * math.exp(a if i % 2 == 0 else -a)
        add_bar(rows, f2._rollover_utc(day) - 2 * HOUR, px)  # opens 15:00 NY
    return rows


def anchor_session_rows(day: date, p0, closes4, entry, s3_entry, flatten):
    """Bars for one triggered NY-anchor signal day (fail-closed-complete).

    Instants (EST day 2020-02-26 shown; EDT shifts one hour earlier):
      p0 opens 07:00 NY (ends 08:00 = NY open); session bars open 08..11;
      signal bar ends 12:00 NY; entry bar opens 12:00, fills 13:00 NY;
      S3 entry opens 13:00, fills 14:00 NY; flatten bar opens 15:00 NY and
      ends 16:00 NY (21:00Z EST / 20:00Z EDT), strictly < 17:00 NY rollover.
    """
    rows = []
    open_ = ny_dt(day, 8)
    add_bar(rows, open_ - HOUR, p0)
    for k, c in enumerate(closes4):
        add_bar(rows, open_ + k * HOUR, c)
    add_bar(rows, open_ + 4 * HOUR, entry)          # S1/S2 entry bar
    add_bar(rows, open_ + 5 * HOUR, s3_entry)       # S3 delayed entry bar
    add_bar(rows, ny_dt(day, 17) - 2 * HOUR, flatten)  # ends 16:00 NY
    return rows


SIGMA_CLOSES_TRIGGER = (1.0005, 1.0010, 1.0015, 1.0020)          # r = 0.002
SIGMA_CLOSES_SMALL = (1.000125, 1.00025, 1.000375, 1.0005)       # r = 0.0005


@pytest.fixture
def day_a_rows():
    """Wed 2020-02-26 (EST) trigger fixture + 21 prior close bars."""
    rows = add_prior_close_bars([], [date(2020, 2, 26)])
    rows += anchor_session_rows(
        date(2020, 2, 26), p0=1.0, closes4=SIGMA_CLOSES_TRIGGER,
        entry=g.GOLDEN_ENTRY_PX, s3_entry=g.GOLDEN_ENTRY_PX_S3,
        flatten=g.GOLDEN_EXIT_PX,
    )
    return rows


# ---------------------------------------------------------------------------
# load_bars fail-closed validation
# ---------------------------------------------------------------------------


class TestLoadBarsFailClosed:
    def _row(self, ts="2020-02-26T13:00:00Z", px=1.1):
        return {"datetime": ts, "open": px, "high": px, "low": px, "close": px}

    def test_happy_path_sorted(self):
        s = f2.load_bars([self._row("2020-02-26T14:00:00Z"),
                          self._row("2020-02-26T13:00:00Z")])
        assert s.bars[0].open_dt == datetime(2020, 2, 26, 13, tzinfo=UTC)

    def test_duplicate_timestamp(self):
        with pytest.raises(f2.FailClosed, match="duplicate"):
            f2.load_bars([self._row(), self._row()])

    def test_malformed_timestamp(self):
        with pytest.raises(f2.FailClosed, match="malformed"):
            f2.load_bars([self._row(ts="not-a-date")])

    def test_naive_timestamp(self):
        with pytest.raises(f2.FailClosed, match="naive"):
            f2.load_bars([self._row(ts="2020-02-26T13:00:00")])

    def test_non_utc_offset(self):
        with pytest.raises(f2.FailClosed, match="non-UTC"):
            f2.load_bars([self._row(ts="2020-02-26T13:00:00+01:00")])

    def test_off_hour_grid(self):
        with pytest.raises(f2.FailClosed, match="off the H1 hour grid"):
            f2.load_bars([self._row(ts="2020-02-26T13:30:00Z")])

    def test_missing_close_field(self):
        row = self._row()
        del row["close"]
        with pytest.raises(f2.FailClosed, match="missing field"):
            f2.load_bars([row])

    def test_ohlc_inconsistency(self):
        row = self._row()
        row["high"], row["low"] = 1.0, 1.2
        with pytest.raises(f2.FailClosed, match="OHLC"):
            f2.load_bars([row])

    def test_empty(self):
        with pytest.raises(f2.FailClosed, match="empty"):
            f2.load_bars([])


# ---------------------------------------------------------------------------
# z-threshold: trigger / no-trade / warm-up (hand goldens)
# ---------------------------------------------------------------------------


class TestZThreshold:
    def test_trigger_fades_extension(self, day_a_rows):
        direction, reason, info = f2.signal_detail(
            day_a_rows, {"arm_id": "anchor"}, day=date(2020, 2, 26)
        )
        # r = 1.0020/1.0000 - 1 = 0.002; z = 0.002/(0.001*sqrt(20/19))
        #   = 1.9493588689617943 >= 1.0 -> fade -> position -1 (short).
        assert reason == "TRIGGERED"
        assert direction == g.GOLDEN_DIR_ANCHOR == -1
        assert info["r"] == pytest.approx(g.GOLDEN_R_BIG, rel=1e-12)
        assert info["sigma"] == pytest.approx(g.GOLDEN_SIGMA20, rel=1e-9)
        assert info["z"] == pytest.approx(g.GOLDEN_Z_BIG, rel=1e-9)
        assert info["signal_ts"] == "2020-02-26T17:00:00Z"  # 12:00 NY EST

    def test_signal_convenience_wrapper(self, day_a_rows):
        # latest evaluable day on this fixture is 2020-02-26
        assert f2.signal(day_a_rows, {"arm_id": "anchor"}) == -1

    def test_sub_threshold_no_trade(self):
        rows = add_prior_close_bars([], [date(2020, 2, 26)])
        rows += anchor_session_rows(
            date(2020, 2, 26), p0=1.0, closes4=SIGMA_CLOSES_SMALL,
            entry=1.0005, s3_entry=1.0005, flatten=1.0004,
        )
        direction, reason, info = f2.signal_detail(
            rows, {"arm_id": "anchor"}, day=date(2020, 2, 26)
        )
        # r = 0.0005 -> z = 0.48733971724044857 < 1.0 -> gate not met.
        assert direction == 0 and reason == "GATE_NOT_MET"
        assert info["z"] == pytest.approx(g.GOLDEN_Z_SMALL, rel=1e-9)

    def test_warmup_fail_closed(self):
        rows = add_prior_close_bars([], [date(2020, 2, 26)], n=10)
        rows += anchor_session_rows(
            date(2020, 2, 26), p0=1.0, closes4=SIGMA_CLOSES_TRIGGER,
            entry=g.GOLDEN_ENTRY_PX, s3_entry=g.GOLDEN_ENTRY_PX_S3,
            flatten=g.GOLDEN_EXIT_PX,
        )
        direction, reason, info = f2.signal_detail(
            rows, {"arm_id": "anchor"}, day=date(2020, 2, 26)
        )
        # Only 10 prior close bars (< 20 returns) -> NO_TRADE, fail-closed.
        assert direction == 0 and reason == "WARMUP"
        assert info["z"] is None

    def test_missing_signal_bar_fail_closed(self, day_a_rows):
        # drop the 4th NY-session bar (opens 11:00 NY EST = 16:00Z)
        rows = [r for r in day_a_rows if r["datetime"] != "2020-02-26T16:00:00Z"]
        direction, reason, _ = f2.signal_detail(
            rows, {"arm_id": "anchor"}, day=date(2020, 2, 26)
        )
        assert direction == 0 and reason == "MISSING_BAR"


# ---------------------------------------------------------------------------
# PIT sigma20: strictly PRIOR days only (no same-day leakage)
# ---------------------------------------------------------------------------


def test_sigma20_is_pit_no_same_day_leakage(day_a_rows):
    base = f2.signal_detail(day_a_rows, {"arm_id": "anchor"},
                            day=date(2020, 2, 26))
    # Corrupt the SIGNAL DAY's own 16:00-NY close (the flatten bar): if the
    # sigma leaked same-day data, z would move; it must not.
    poisoned = []
    for row in day_a_rows:
        if row["datetime"] == "2020-02-26T20:00:00Z":  # signal-day close bar
            row = dict(row, open=2.0, high=2.0, low=2.0, close=2.0)
        poisoned.append(row)
    corrupt = f2.signal_detail(poisoned, {"arm_id": "anchor"},
                               day=date(2020, 2, 26))
    assert corrupt[2]["sigma"] == pytest.approx(base[2]["sigma"], rel=1e-15)
    assert corrupt[2]["z"] == pytest.approx(base[2]["z"], rel=1e-15)
    assert corrupt[0] == base[0] == -1


# ---------------------------------------------------------------------------
# Fills, flatten clock, DST transitions
# ---------------------------------------------------------------------------


class TestScheduleAndDST:
    def test_next_allowed_bar_fill_and_flatten_est(self, day_a_rows):
        rep = f2.run_arm(day_a_rows, "anchor", 1.0, pair="EUR/USD")
        assert rep["n_trades"] == 1
        fill = rep["fills"][0]
        # signal bar ends 17:00Z; entry bar opens 17:00Z, fills at its close
        assert fill["entry_fill_ts"] == "2020-02-26T18:00:00Z"  # 13:00 NY EST
        assert fill["entry_px"] == g.GOLDEN_ENTRY_PX
        # flatten ends 16:00 NY EST = 21:00Z, strictly < 22:00Z rollover
        assert fill["exit_ts"] == "2020-02-26T21:00:00Z"
        assert fill["exit_px"] == g.GOLDEN_EXIT_PX
        assert fill["rollover_ts"] == "2020-02-26T22:00:00Z"
        assert fill["entry_fill_ts"] < fill["exit_ts"] < fill["rollover_ts"]

    def test_missing_flatten_bar_no_trade(self, day_a_rows):
        rows = [r for r in day_a_rows
                if r["datetime"] != "2020-02-26T20:00:00Z"]
        rep = f2.run_arm(rows, "anchor", 1.0, pair="EUR/USD")
        assert rep["n_trades"] == 0
        day_dec = [d for d in rep["decisions"] if d["day"] == "2020-02-26"]
        assert day_dec[0]["reason"] == "MISSING_BAR"

    @pytest.mark.parametrize("day,open_hour,exit_end,rollover", [
        # spring transition: EST Friday -> EDT Monday (2020-03-08)
        (date(2020, 3, 6), 13, "2020-03-06T21:00:00Z", "2020-03-06T22:00:00Z"),
        (date(2020, 3, 9), 12, "2020-03-09T20:00:00Z", "2020-03-09T21:00:00Z"),
        # fall transition: EDT Friday -> EST Monday (2020-11-01)
        (date(2020, 10, 30), 12, "2020-10-30T20:00:00Z", "2020-10-30T21:00:00Z"),
        (date(2020, 11, 2), 13, "2020-11-02T21:00:00Z", "2020-11-02T22:00:00Z"),
    ])
    def test_flatten_across_both_dst_transitions(self, day, open_hour,
                                                 exit_end, rollover):
        rows = add_prior_close_bars([], [day])
        rows += anchor_session_rows(
            day, p0=1.0, closes4=SIGMA_CLOSES_TRIGGER,
            entry=g.GOLDEN_ENTRY_PX, s3_entry=g.GOLDEN_ENTRY_PX_S3,
            flatten=g.GOLDEN_EXIT_PX,
        )
        rep = f2.run_arm(rows, "anchor", 1.0, pair="EUR/USD")
        assert rep["n_trades"] == 1, (day, rep["decisions"][-1])
        fill = rep["fills"][0]
        # flatten bar END is uniformly 16:00 New York wall clock:
        # 21:00Z in EST weeks, 20:00Z in EDT weeks; strictly < 17:00 NY.
        assert fill["exit_ts"] == exit_end
        assert fill["rollover_ts"] == rollover
        assert fill["exit_ts"] < fill["rollover_ts"]
        assert fill["exit_ts"].endswith(("21:00:00Z", "20:00:00Z"))

    def test_s3_delay_shifts_entry_exactly_one_bar(self, day_a_rows):
        s1 = f2.run_arm(day_a_rows, "anchor", 1.0, pair="EUR/USD")["fills"][0]
        s3 = f2.run_arm(day_a_rows, "anchor", 2.0, pair="EUR/USD")["fills"][0]
        assert s1["delay_events"] == 0 and s3["delay_events"] == 1
        assert s1["entry_open_ts"] == "2020-02-26T17:00:00Z"
        assert s3["entry_open_ts"] == "2020-02-26T18:00:00Z"   # +1 bar
        assert s3["entry_fill_ts"] == "2020-02-26T19:00:00Z"   # 14:00 NY
        assert s3["entry_px"] == g.GOLDEN_ENTRY_PX_S3
        # flatten unchanged, still strictly before the rollover
        assert s3["exit_ts"] == s1["exit_ts"] == "2020-02-26T21:00:00Z"
        assert s3["exit_ts"] < s3["rollover_ts"]

    def test_s3_tier_one_five_has_no_delay(self, day_a_rows):
        s2 = f2.run_arm(day_a_rows, "anchor", 1.5, pair="EUR/USD")["fills"][0]
        assert s2["delay_events"] == 0
        assert s2["entry_fill_ts"] == "2020-02-26T18:00:00Z"


# ---------------------------------------------------------------------------
# Hand-computed costs at each frozen tier
# ---------------------------------------------------------------------------


class TestCosts:
    @pytest.fixture
    def flows(self, day_a_rows):
        out = {}
        for tier in (1.0, 1.5, 2.0):
            rep = f2.run_arm(day_a_rows, "anchor", tier, pair="EUR/USD")
            out[tier] = rep["cashflows"][0]
        return out

    def test_gross_identical_across_tiers_without_delay(self, flows):
        # gross = -(1.0010/1.0025 - 1) = 0.0015/1.0025 = 0.0014962593516209477
        for tier in (1.0, 1.5):
            assert flows[tier]["gross_ret"] == pytest.approx(
                g.GOLDEN_GROSS_ANCHOR, rel=1e-12)

    def test_round_trip_bps_per_tier(self, flows):
        assert flows[1.0]["cost_ret"] == pytest.approx(g.GOLDEN_COST_RT_T1)
        assert flows[1.5]["cost_ret"] == pytest.approx(g.GOLDEN_COST_RT_T2)

    def test_net_returns_hand_computed(self, flows):
        assert flows[1.0]["net_ret"] == pytest.approx(g.GOLDEN_NET_T1, rel=1e-12)
        assert flows[1.5]["net_ret"] == pytest.approx(g.GOLDEN_NET_T2, rel=1e-12)

    def test_tier2_delayed_fill_gross_and_net(self, day_a_rows):
        rep = f2.run_arm(day_a_rows, "anchor", 2.0, pair="EUR/USD")
        cf = rep["cashflows"][0]
        # gross = -(1.0010/1.0022 - 1) = 0.0012/1.0022 = 0.0011973653961279185
        assert cf["gross_ret"] == pytest.approx(g.GOLDEN_GROSS_ANCHOR_S3, rel=1e-12)
        assert cf["cost_ret"] == pytest.approx(g.GOLDEN_COST_RT_T3)
        assert cf["net_ret"] == pytest.approx(g.GOLDEN_NET_T3, rel=1e-12)

    def test_costs_bps_block(self, day_a_rows):
        rep = f2.run_arm(day_a_rows, "anchor", 1.5, pair="EUR/USD")
        assert rep["costs_bps"]["per_side_bps"] == pytest.approx(2.25)
        assert rep["costs_bps"]["round_trip_bps"] == pytest.approx(4.5)
        assert rep["costs_bps"]["total_paid_bps"] == pytest.approx(4.5)


# ---------------------------------------------------------------------------
# Neighbour (Tokyo open) and sign-flipped continuation control
# ---------------------------------------------------------------------------


@pytest.fixture
def day_tky_rows():
    """Tokyo Tue 2020-02-25 session + NY Tuesday flatten + 21 prior closes.

    Sigma anchor date: the signal instant 2020-02-25T04:00:00Z is NY Monday
    23:00 EST, so the frozen 'days strictly before d' rule ends the window
    at Friday 2020-02-21 -- the same PIT construction as the NY anchor.
    """
    rows = add_prior_close_bars([], [date(2020, 2, 24)])
    open_ = tky_dt(date(2020, 2, 25), 9)            # 2020-02-25T00:00:00Z
    add_bar(rows, open_ - HOUR, 1.0)                # Tokyo 08:00 (p0)
    for k, c in enumerate(SIGMA_CLOSES_TRIGGER):
        add_bar(rows, open_ + k * HOUR, c)          # Tokyo 09..12 opens
    add_bar(rows, open_ + 4 * HOUR, g.GOLDEN_ENTRY_PX)   # fills 14:00 Tokyo
    add_bar(rows, open_ + 5 * HOUR, g.GOLDEN_ENTRY_PX_S3)
    add_bar(rows, ny_dt(date(2020, 2, 25), 17) - 2 * HOUR, g.GOLDEN_EXIT_PX)
    return rows


class TestNeighbourAndControl:
    def test_neighbour_same_gate_same_sigma_fade(self, day_tky_rows):
        direction, reason, info = f2.signal_detail(
            day_tky_rows, {"arm_id": "neighbour"}, day=date(2020, 2, 25))
        assert reason == "TRIGGERED" and direction == g.GOLDEN_NEIGHBOUR["direction"]
        assert info["r"] == pytest.approx(g.GOLDEN_NEIGHBOUR["r"], rel=1e-12)
        assert info["z"] == pytest.approx(g.GOLDEN_NEIGHBOUR["z"], rel=1e-9)
        assert info["signal_ts"] == g.GOLDEN_NEIGHBOUR["signal_ts"]

    def test_neighbour_fill_and_ny_flatten(self, day_tky_rows):
        rep = f2.run_arm(day_tky_rows, "neighbour", 1.0, pair="EUR/USD")
        assert rep["n_trades"] == 1
        fill = rep["fills"][0]
        assert fill["entry_fill_ts"] == g.GOLDEN_NEIGHBOUR["entry_fill"]
        # flatten strictly before the 17:00 NY rollover (Tue 22:00Z EST)
        assert fill["exit_ts"] == g.GOLDEN_NEIGHBOUR["exit_end"]
        assert fill["rollover_ts"] == g.GOLDEN_NEIGHBOUR["rollover"]
        assert fill["exit_ts"] < fill["rollover_ts"]

    def test_control_flips_mechanism_sign(self, day_a_rows):
        anchor = f2.run_arm(day_a_rows, "anchor", 1.0, pair="EUR/USD")
        control = f2.run_arm(day_a_rows, "control", 1.0, pair="EUR/USD")
        assert anchor["fills"][0]["direction"] == -1
        assert control["fills"][0]["direction"] == +1
        # identical schedule, flipped cashflow sign:
        assert control["fills"][0]["entry_fill_ts"] == anchor["fills"][0]["entry_fill_ts"]
        assert control["cashflows"][0]["gross_ret"] == pytest.approx(
            g.GOLDEN_GROSS_CONTROL, rel=1e-12)
        # costs are paid on BOTH arms: net_control = -gross - cost
        #     = -(0.0015/1.0025) - 0.0003 = -0.0017962593516209477
        assert control["cashflows"][0]["net_ret"] == pytest.approx(
            g.GOLDEN_GROSS_CONTROL - g.GOLDEN_COST_RT_T1, rel=1e-12)

    def test_bad_config_fails_closed(self, day_a_rows):
        with pytest.raises(f2.FailClosed, match="frozen"):
            f2.signal(day_a_rows, {"arm_id": "anchor", "gate_z": 0.5})
        with pytest.raises(f2.FailClosed, match="unknown arm_id"):
            f2.signal(day_a_rows, {"arm_id": "london"})
        with pytest.raises(f2.FailClosed, match="frozen cells"):
            f2.run_arm(day_a_rows, "anchor", 3.0)


# ---------------------------------------------------------------------------
# Arm identity, determinism, idempotent publish
# ---------------------------------------------------------------------------


class TestIdentityAndPublish:
    def test_three_distinct_stable_arm_digests(self):
        digs = [f2.arm_identity(a) for a in f2.ARM_IDS]
        assert len(set(digs)) == 3
        for a in f2.ARM_IDS:
            assert f2.arm_identity(a) == f2.arm_identity(a)
            assert f2.arm_identity(a, {"arm_id": a}) == f2.arm_identity(a)
        assert all(len(d) == 64 for d in digs)

    def test_double_generation_identical_canonical_sha256(self, day_a_rows):
        r1 = f2.run_arm(day_a_rows, "anchor", 1.0, pair="EUR/USD")
        r2 = f2.run_arm(day_a_rows, "anchor", 1.0, pair="EUR/USD")
        assert r1["canonical_json"] == r2["canonical_json"]
        assert r1["sha256"] == r2["sha256"] == f2.run_digest(json.loads(r1["canonical_json"]))
        # canonical JSON round-trips
        assert json.loads(r1["canonical_json"])["n_trades"] == 1

    def test_publish_idempotent_replay_noop(self, tmp_path):
        ledger = tmp_path / "ledger.jsonl"
        digest = "deadbeef" * 8
        rows = [{"arm_id": "anchor", "n_trades": 1}]
        first = f2.publish(ledger, digest, rows)
        assert first["status"] == "APPENDED"
        assert first["rows_added"] == 2  # header + 1 row
        replay = f2.publish(ledger, digest, rows)
        assert replay["status"] == "REPLAY_NOOP"
        assert replay["rows_added"] == 0
        assert len(ledger.read_text().strip().splitlines()) == 2
        # a different digest appends a new run
        second = f2.publish(ledger, "cafebabe" * 8, rows)
        assert second["status"] == "APPENDED"
        assert len(ledger.read_text().strip().splitlines()) == 4

    def test_publish_corrupt_ledger_fails_closed(self, tmp_path):
        ledger = tmp_path / "ledger.jsonl"
        ledger.write_text("{not json}\n")
        with pytest.raises(f2.FailClosed, match="corrupt ledger"):
            f2.publish(ledger, "a" * 64, [])


# ---------------------------------------------------------------------------
# compute_metrics: dummy finite feasibility metrics
# ---------------------------------------------------------------------------


def test_compute_metrics_finite(day_a_rows):
    reps = [f2.run_arm(day_a_rows, arm, 1.0, pair="EUR/USD")
            for arm in f2.ARM_IDS]
    m = f2.compute_metrics(reps)
    assert m["all_finite"] is True
    assert m["scored"] is False
    assert m["status"] == "DRY_RUN_FEASIBILITY_ONLY"
    for k in ("n_decisions", "n_trades", "decisions_per_year_arm_max",
              "turnover", "total_cost_bps", "mean_gross_ret", "mean_net_ret"):
        assert isinstance(m[k], float) and math.isfinite(m[k])
    assert m["n_trades"] == 2.0          # anchor + control trigger; the
    # Tokyo neighbour has no Tokyo-session bars on this NY-only fixture
    assert m["turnover"] == 4.0          # entry + exit per trade


# ---------------------------------------------------------------------------
# Exact-arm dry run: 2 pairs x ~500 hours spanning one US DST transition
# ---------------------------------------------------------------------------

WARMUP_DAYS = [date(2020, 1, 13) + timedelta(days=i) for i in range(40)]
WARMUP_DAYS = [d for d in WARMUP_DAYS
               if d.weekday() <= 4 and d <= date(2020, 2, 18)]  # 27 weekdays
DENSE_START = datetime(2020, 2, 19, 0, 0, tzinfo=UTC)
DENSE_HOURS = 504                                   # -> 2020-03-12T00:00Z
DRY_PAIRS = ("EUR/USD", "USD/JPY")


def _base_price(i: int, base: float) -> float:
    return base * (1.0 + 0.0002 * math.sin(i / 7.0))


def build_dryrun_fixture(base: float) -> list:
    """Warm-up prefix (27 rollover-close bars, alternating +/-0.001 log
    returns => 25+ prior closes before the dense window) + a continuous
    ~500-hour deterministic price path crossing the 2020-03-08 spring
    forward.  One engineered extension per pair triggers the gate."""
    rows: list = []
    px = base
    for i, day in enumerate(WARMUP_DAYS):
        px = px * math.exp(A if i % 2 == 0 else -A)
        add_bar(rows, f2._rollover_utc(day) - 2 * HOUR, px)
    prices = {}
    for i in range(DENSE_HOURS):
        prices[DENSE_START + i * HOUR] = _base_price(i, base)

    if base == 1.10:  # EUR/USD: engineer NY Wed 2020-03-04 + Tokyo Wed session
        eng_ny = {
            ny_dt(date(2020, 3, 4), 8) - HOUR: 1.1000,       # p0
            ny_dt(date(2020, 3, 4), 8): 1.1013,
            ny_dt(date(2020, 3, 4), 8) + HOUR: 1.1026,
            ny_dt(date(2020, 3, 4), 8) + 2 * HOUR: 1.1039,
            ny_dt(date(2020, 3, 4), 8) + 3 * HOUR: 1.1052,   # p4, r=0.0047
            ny_dt(date(2020, 3, 4), 8) + 4 * HOUR: 1.1055,   # entry, 13:00 NY
            ny_dt(date(2020, 3, 4), 8) + 5 * HOUR: 1.1050,   # S3 entry
            ny_dt(date(2020, 3, 4), 17) - 2 * HOUR: 1.1040,  # flatten 16:00 NY
        }
        eng_tky = {
            tky_dt(date(2020, 3, 4), 9) - HOUR: 1.1000,      # p0 Tokyo 08
            tky_dt(date(2020, 3, 4), 9): 1.1013,
            tky_dt(date(2020, 3, 4), 9) + HOUR: 1.1026,
            tky_dt(date(2020, 3, 4), 9) + 2 * HOUR: 1.1039,
            tky_dt(date(2020, 3, 4), 9) + 3 * HOUR: 1.1052,
            tky_dt(date(2020, 3, 4), 9) + 4 * HOUR: 1.1055,  # fill 14:00 Tokyo
            tky_dt(date(2020, 3, 4), 9) + 5 * HOUR: 1.1050,
        }
        prices.update(eng_ny)
        prices.update(eng_tky)
    else:  # USD/JPY: engineer the same NY extension, scaled
        eng = {
            ny_dt(date(2020, 3, 4), 8) - HOUR: 110.000,
            ny_dt(date(2020, 3, 4), 8): 110.055,
            ny_dt(date(2020, 3, 4), 8) + HOUR: 110.110,
            ny_dt(date(2020, 3, 4), 8) + 2 * HOUR: 110.165,
            ny_dt(date(2020, 3, 4), 8) + 3 * HOUR: 110.220,  # r = 0.002
            ny_dt(date(2020, 3, 4), 8) + 4 * HOUR: 110.275,
            ny_dt(date(2020, 3, 4), 8) + 5 * HOUR: 110.242,
            ny_dt(date(2020, 3, 4), 17) - 2 * HOUR: 110.110,
        }
        prices.update(eng)

    for ts in sorted(prices):
        add_bar(rows, ts, prices[ts])
    return rows


DRY_LEDGER = ROOT / "data_raw" / "forex_free_v1" / "dryrun" / "ledger_family2.jsonl"


def _run_all_arms():
    """Run 3 arms x 2 pairs x 3 tiers over the synthetic fixture."""
    reports = []
    for pair, base in (("EUR/USD", 1.10), ("USD/JPY", 110.0)):
        bars = build_dryrun_fixture(base)
        assert len(bars) == len(WARMUP_DAYS) + DENSE_HOURS  # 27 + 504
        for arm in f2.ARM_IDS:
            for tier in f2.COST_TIERS:
                reports.append(f2.run_arm(bars, arm, tier, pair=pair))
    return reports


def test_exact_arm_dry_run_schedule_only():
    reports = _run_all_arms()
    assert len(reports) == 2 * 3 * 3

    # --- digest: canonical, stable across double generation -------------
    fixture = {
        "warmup_weekdays": len(WARMUP_DAYS),
        "warmup_first": WARMUP_DAYS[0].isoformat(),
        "warmup_last": WARMUP_DAYS[-1].isoformat(),
        "dense_start": "2020-02-19T00:00:00Z",
        "dense_hours": DENSE_HOURS,
        "dense_end_exclusive": "2020-03-12T00:00:00Z",
        "dst_transition": "US spring-forward 2020-03-08 inside window",
        "prior_rollover_closes_available": ">= 25 before first dense day",
    }
    payload = {
        "family_id": f2.FAMILY_ID,
        "proposal_id": f2.PROPOSAL_ID,
        "scope": "F6_FAMILY2_EXACT_ARM_DRYRUN_SCHEDULE_ONLY_NO_SCORING",
        "pairs": list(DRY_PAIRS),
        "arms": list(f2.ARM_IDS),
        "cost_tiers": list(f2.COST_TIERS),
        "fixture": fixture,
    }
    digest1 = f2.run_digest(payload)
    reports2 = _run_all_arms()  # double generation
    digest2 = f2.run_digest(payload)
    assert digest1 == digest2
    canon1 = json.dumps([r["canonical_json"] for r in reports], sort_keys=True)
    canon2 = json.dumps([r["canonical_json"] for r in reports2], sort_keys=True)
    assert canon1 == canon2  # identical canonical sha256 across runs

    # --- every arm produced decisions; engineered days triggered --------
    by = {(r["pair"], r["arm_id"], r["cost_tier"]): r for r in reports}
    for pair in DRY_PAIRS:
        for arm in f2.ARM_IDS:
            rep = by[(pair, arm, 1.0)]
            assert rep["n_decisions"] > 0
            assert all(math.isfinite(float(rep["decisions_per_year"]))
                       for _ in [0])
            assert rep["decisions_per_year"] > 0
        assert by[(pair, "anchor", 1.0)]["n_trades"] >= 1
        assert by[(pair, "control", 1.0)]["n_trades"] >= 1
        # anchor trade on the engineered EST day, DST-exact flatten:
        af = by[(pair, "anchor", 1.0)]["fills"]
        mar4 = [f for f in af if f["day"] == "2020-03-04"]
        assert len(mar4) == 1
        assert mar4[0]["entry_fill_ts"] == "2020-03-04T18:00:00Z"  # 13:00 NY
        assert mar4[0]["exit_ts"] == "2020-03-04T21:00:00Z"        # 16:00 NY
        assert mar4[0]["exit_ts"] < mar4[0]["rollover_ts"]
    nb = by[("EUR/USD", "neighbour", 1.0)]["fills"]
    assert any(f["day"] == "2020-03-04" and
               f["entry_fill_ts"] == "2020-03-04T05:00:00Z" and
               f["exit_ts"] == "2020-03-04T21:00:00Z" for f in nb)

    # --- schedule-only feasibility numbers ------------------------------
    metrics = f2.compute_metrics(reports)
    assert metrics["all_finite"] is True and metrics["scored"] is False
    feasibility = {
        "decisions_per_year_arm_max": metrics["decisions_per_year_arm_max"],
        "turnover_total": metrics["turnover"],
        "total_cost_bps_t1": sum(
            r["costs_bps"]["total_paid_bps"] for r in reports
            if r["cost_tier"] == 1.0),
        "total_cost_bps_t2": sum(
            r["costs_bps"]["total_paid_bps"] for r in reports
            if r["cost_tier"] == 1.5),
        "total_cost_bps_t3": sum(
            r["costs_bps"]["total_paid_bps"] for r in reports
            if r["cost_tier"] == 2.0),
        "n_trades_total_t1": sum(r["n_trades"] for r in reports
                                 if r["cost_tier"] == 1.0),
    }
    # cost drag arithmetic: round trip 3.0/4.5/6.0 bps per trade
    n_t1 = feasibility["n_trades_total_t1"]
    assert feasibility["total_cost_bps_t1"] == pytest.approx(3.0 * n_t1)
    assert feasibility["total_cost_bps_t2"] == pytest.approx(4.5 * n_t1)
    assert feasibility["total_cost_bps_t3"] == pytest.approx(6.0 * n_t1)

    # --- temporary ledger under gitignored data_raw/, idempotent --------
    # The ledger is a synthetic TEMPORARY dry-run artifact (data_raw/ is
    # gitignored); reset it so this test is rerunnable, then prove
    # APPENDED -> identical-digest REPLAY_NOOP idempotency.
    assert "data_raw" in str(DRY_LEDGER)
    if DRY_LEDGER.exists():
        DRY_LEDGER.unlink()
    first = f2.publish(DRY_LEDGER, digest1, [
        {
            "record_kind": "arm_report",
            "pair": r["pair"], "arm_id": r["arm_id"],
            "cost_tier": r["cost_tier"], "arm_digest": r["arm_digest"],
            "n_decisions": r["n_decisions"], "n_trades": r["n_trades"],
            "decisions_per_year": r["decisions_per_year"],
            "turnover": r["turnover"],
            "total_paid_bps": r["costs_bps"]["total_paid_bps"],
            "report_sha256": r["sha256"],
        }
        for r in reports
    ] + [{"record_kind": "feasibility", "metrics": feasibility}])
    assert first["status"] == "APPENDED"
    replay = f2.publish(DRY_LEDGER, digest1, [])
    assert replay["status"] == "REPLAY_NOOP"
    assert replay["rows_added"] == 0

    # ledger survives for the report: reload and count rows
    lines = [json.loads(x) for x in
             DRY_LEDGER.read_text().strip().splitlines()]
    headers = [x for x in lines if x.get("record") == "run_header"
               and x.get("run_digest") == digest1]
    assert len(headers) == 1
    print("\nF6 family-2 dry run digest:", digest1)
    print("F6 family-2 feasibility:", json.dumps(feasibility, sort_keys=True))
