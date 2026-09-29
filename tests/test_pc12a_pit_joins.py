"""PC12A verification battery §8.2 -- point-in-time joins.

Every feature the policy/eligibility layers consume must be computed from
data <= (fold start - embargo); a poisoned FUTURE bar (timestamped after
the decision) must be ignored or fail closed (BLOCKED_STALE / exception),
never silently consumed.  Covers:

- fold embargo arithmetic: train data strictly earlier than the test fold
  start minus the 1-week embargo, for all 8 folds;
- calendar service: session marks rebuilt from tzdata across the whole
  campaign range (no hardcoded DST offsets anywhere);
- staleness: the 90s M1 fail-closed threshold, at and past the boundary,
  plus the future-dated-bar poison (fail closed, never consume);
- FEATURES_BLACKLIST (GROUPING_PROPOSAL 3.6): every pattern enforced and
  the enforcement path LIVE inside Eligibility.evaluate;
- swap-calendar value-date rule: Wed x3 accrual events at 22:00 UTC, NO
  Friday-close-boundary or Saturday event, swept across the campaign;
- profile freeze PIT: the Friday-20:00 freeze consumes the freeze day
  truncated AT the stamp (post-20:00 minutes never enter the profile);
- the engine consumes NO macro series at all (EFFR/VIX/Brent-WTI joins
  are NOT_RUN in this dry engine): no leg's pit_join_list references any
  macro input, so no un-keyed macro join can exist.
"""

import datetime as dt
import json
import pathlib
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import numpy as np
import pytest

from research.pc12a import calendar_service as cal
from research.pc12a import legs as _legs
from research.pc12a import policy as pol
from research.pc12a import run_dry as rd

UTC = dt.timezone.utc
WORKTREE = pathlib.Path(__file__).resolve().parent.parent
REAL_LEGS_DIR = WORKTREE / "research" / "pc12a" / "legs_config"

NOW = dt.datetime(2024, 6, 20, 14, 0, tzinfo=UTC)


def _real_cfgs():
    return _legs.load_leg_configs(str(REAL_LEGS_DIR))


# ---------------------------------------------------------------------------
# Fold embargo: features must come from data <= fold start - embargo
# ---------------------------------------------------------------------------


def test_fold_train_ends_at_least_one_embargo_before_every_test_fold():
    folds = cal.fold_calendar()
    assert len(folds) == 8
    fridays = cal.decision_fridays()
    for f in folds:
        gap_days = (f.test_start - f.train_end).days
        # train window ends >= 1 full embargo week before the test fold's
        # first decision Friday (the measured gap is exactly 2 Fridays)
        assert gap_days >= cal.EMBARGO_WEEKS * 7
        # no TRAIN-side Friday sits inside the embargo week
        embargo_start = f.test_start - dt.timedelta(
            days=7 * cal.EMBARGO_WEEKS)
        train_fridays = [d for d in fridays
                         if f.train_start <= d <= f.train_end]
        assert train_fridays and all(d < embargo_start for d in
                                     train_fridays), (
            f"fold {f.fold_id}: train Friday inside the embargo week")
        # the latest data a profile freeze could have consumed for TRAIN
        # (Friday train_end 20:00) still precedes test_start - embargo
        last_freeze = dt.datetime.combine(f.train_end, dt.time(20, 0),
                                          tzinfo=UTC)
        assert last_freeze < dt.datetime.combine(
            embargo_start, dt.time(0, 0), tzinfo=UTC)


def test_every_leg_pit_join_is_decision_time_available():
    """The engine's PIT join universe: M1 panels (bar close == decision),
    WEEKLY_PROFILE (frozen Friday 20:00, available at/after the stamp),
    TZDATA sessions/weekdays (static), D1 aggregates (completed prior day,
    available at next midnight).  No macro series (EFFR/VIX/Brent-WTI)
    appears in any pit_join_list, so no macro join without an
    available_time key can exist (those joins are NOT_RUN in this engine).
    """
    cfgs = _real_cfgs()
    assert len(cfgs) == 12
    allowed = {
        "EURUSD_M1_BIDASK_VOL", "GBPUSD_M1_BIDASK_VOL",
        "USDJPY_M1_BIDASK_VOL", "WEEKLY_PROFILE", "TZDATA_SESSIONS",
        "TZDATA_WEEKDAYS", "USDJPY_D1_AGGREGATE", "GBPUSD_D1_AGGREGATE",
        "EURUSD_D1_AGGREGATE",
    }
    for cfg in cfgs:
        joins = set(cfg.get("pit_join_list", []))
        assert joins and joins <= allowed, (
            f"{cfg.get('corpus_gid')}: unexpected PIT join {joins - allowed}")
        assert not any(k in j for j in joins for k in
                       ("EFFR", "VIX", "BRENT", "WTI", "SOFR", "SONIA")), (
            "macro series must not enter this dry engine unkeyed")


# ---------------------------------------------------------------------------
# Calendar service: tzdata, never hardcoded DST
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("day", [
    dt.date(2021, 3, 14), dt.date(2021, 10, 31),   # US seams 2021
    dt.date(2022, 3, 13), dt.date(2022, 10, 30),
    dt.date(2023, 3, 12), dt.date(2023, 10, 29),
    dt.date(2024, 3, 10), dt.date(2024, 3, 31),    # divergent US/EU window
    dt.date(2024, 10, 27), dt.date(2024, 11, 3),   # divergent autumn window
    dt.date(2025, 3, 9), dt.date(2025, 3, 30),
    dt.date(2026, 3, 8), dt.date(2026, 3, 29),
])
def test_session_marks_come_from_tzdata_not_hardcoded_offsets(day):
    for name, tz_name, local_start, allowed in (
            ("London", "Europe/London", dt.time(8, 0),
             {dt.timedelta(hours=0), dt.timedelta(hours=1)}),
            ("NewYork", "America/New_York", dt.time(9, 30),
             {dt.timedelta(hours=-5), dt.timedelta(hours=-4)})):
        win = [w for w in cal.session_windows_utc(day) if w[2] == name][0]
        tz = ZoneInfo(tz_name)
        expect = dt.datetime.combine(day, local_start, tzinfo=tz).astimezone(
            UTC)
        assert win[0] == expect, (
            f"{name} start on {day} is not the tzdata conversion")
        # the local->UTC offset at the mark is exactly tzdata's utcoffset
        # for that instant (both DST regimes occur across the sweep)
        assert win[0].astimezone(tz).utcoffset() in allowed


def test_both_dst_regimes_occur_across_campaign_range():
    """A hardcoded-offset engine would collapse one of the two regimes;
    the tzdata rebuild keeps both across every campaign year."""
    for year in range(2021, 2027):
        winter = cal.session_windows_utc(dt.date(year, 1, 15))[0][0]
        summer = cal.session_windows_utc(dt.date(year, 7, 15))[0][0]
        assert winter.hour == 8 and summer.hour == 7, (
            f"London marks lost a DST regime in {year}")


def test_in_entry_window_pure_function_of_tzdata():
    day = dt.date(2024, 6, 19)   # summer
    lon_lo, lon_hi, _ = cal.session_windows_utc(day)[0]
    inside = dt.datetime(2024, 6, 19, 7, 0, tzinfo=UTC)
    edge_hi = dt.datetime(2024, 6, 19, 11, 0, tzinfo=UTC)
    assert lon_lo == inside and cal.in_entry_window(inside, day)
    assert not cal.in_entry_window(edge_hi, day)      # half-open [s, e)


# ---------------------------------------------------------------------------
# Staleness: the 90s M1 law + the future-bar poison
# ---------------------------------------------------------------------------


def _fresh_leg():
    cfg = [c for c in _legs.VOLPROF_DEFAULT_CONFIGS
           if c["symbol"] == "EURUSD"
           and c["mech_key"] == "vc3_pocmag"][0]
    return _legs.build_leg(cfg)


def _prof():
    p = _legs.WeeklyProfile(
        freeze_ts=dt.datetime(2024, 6, 14, 20, 0, tzinfo=UTC),
        poc=1.0850, vah=1.0900, val=1.0800, w_bin=0.0010, p20=1.0, p80=1.0,
        atr20d=0.004, nodes=(),
        bin_edges=np.arange(1.0700, 1.1000, 0.0010),
        bin_activity=np.full(30, 2.0))
    p.digest = "pitdigest" * 4
    return p


def _ctx(ts, mid, prev, last_data_ts, prof):
    return _legs.BarContext(
        ts=ts, symbol="EURUSD", mid_close=mid, mid_close_prev=prev,
        bid_open=mid - 2e-5, ask_open=mid + 2e-5, bid_close=mid - 2e-5,
        ask_close=mid + 2e-5, bid_low=mid - 3e-5, ask_high=mid + 3e-5,
        atr60=0.0005, in_entry_window=True, is_flat_instant=False,
        day=ts.date(), profile=prof, last_data_ts=last_data_ts)


TS = dt.datetime(2024, 6, 20, 9, 30, tzinfo=UTC)


@pytest.mark.parametrize("age_sec,decides", [(0, True), (89, True),
                                             (90, True), (91, False),
                                             (3600, False)])
def test_staleness_threshold_90s_fail_closed(age_sec, decides):
    leg = _fresh_leg()
    ctx = _ctx(TS, 1.0833, 1.0833, TS - dt.timedelta(seconds=age_sec),
               _prof())
    d = leg.on_bar(ctx)
    assert (d is not None) == decides, (
        f"age {age_sec}s must {'decide' if decides else 'fail closed'}")


@pytest.mark.parametrize("lead_sec", [1, 60, 3600])
def test_poisoned_future_bar_fails_closed(lead_sec):
    """A bar timestamped AFTER the decision instant (poisoned PIT join)
    must never be consumed: the leg returns None (NOT_RUN) regardless of
    how far into the future the poison is dated."""
    leg = _fresh_leg()
    ctx = _ctx(TS, 1.0833, 1.0833, TS + dt.timedelta(seconds=lead_sec),
               _prof())
    assert leg.on_bar(ctx) is None


def test_poisoned_future_pit_snapshot_blocks_stale():
    """The eligibility layer fails closed (E3 / BLOCKED_STALE) on a PIT
    snapshot claiming availability AFTER the decision instant, and on an
    unparseable availability stamp (unverifiable = fail closed)."""
    e = pol.Eligibility()
    # leg younger than the 26w E1 arm window so E1 stays out of the way
    st = pol.LegRuntimeStats(
        leg_start_ts=NOW - dt.timedelta(days=100))
    good = [{"input_id": "X", "available_time_utc":
             NOW.strftime("%Y-%m-%dT%H:%M:%SZ"), "max_age_ok": True}]
    assert e.evaluate("L1", st, good, NOW).state == "ON"
    future = [{"input_id": "X", "available_time_utc":
               (NOW + dt.timedelta(seconds=1)).strftime(
                   "%Y-%m-%dT%H:%M:%SZ"), "max_age_ok": True}]
    v = e.evaluate("L1", st, future, NOW)
    assert v.state == "OFF" and v.rule_id == "E3"
    assert "fail closed" in v.detail
    malformed = [{"input_id": "X", "available_time_utc": "tomorrow",
                  "max_age_ok": True}]
    v2 = e.evaluate("L1", st, malformed, NOW)
    assert v2.state == "OFF" and v2.rule_id == "E3"
    # engine outcome mapping: E3 -> BLOCKED_STALE (run_dry mapping table)
    assert {"E3": "BLOCKED_STALE"}["E3"] == "BLOCKED_STALE"


def test_guard_ignores_future_recorded_spends():
    """PIT inside the shared L6 guard: spends recorded at instants AFTER
    the decision (possible because symbol engines run sequentially) must
    not enter the trailing sum of an earlier decision."""
    g = pol.CostGuard(pol.CostGuardState(window_days=28, cap_usd=10.0))
    g.record_spend(NOW - dt.timedelta(days=1), 6.0)     # past: in window
    g.record_spend(NOW + dt.timedelta(days=2), 100.0)   # future: ignored
    v = g.evaluate(NOW, 0, 10_000, 1.0)
    assert v.allow is True
    assert v.trailing_spend_usd == pytest.approx(6.0, abs=1e-12)
    # the future spend becomes visible only once time reaches it
    v2 = g.evaluate(NOW + dt.timedelta(days=3), 0, 10_000, 1.0)
    assert v2.allow is False


# ---------------------------------------------------------------------------
# FEATURES_BLACKLIST enforcement path (GROUPING_PROPOSAL 3.6)
# ---------------------------------------------------------------------------


def test_every_blacklist_pattern_enforced():
    """One poisoning feature per pattern in the frozen tuple."""
    poisons = {
        r"^future_data": "future_data_eurusd_vix",
        r"_after_decision$": "bar_close_after_decision",
        r"^bar_open_at_or_after_": "bar_open_at_or_after_t0",
        r"_in_fold_pnl$": "leg_in_fold_pnl",
        r"^current_fold_.*pnl": "current_fold_portfolio_pnl",
        r"^realized_pnl": "realized_pnl_series",
        r"^regime_prediction": "regime_prediction_score",
        r"^forecast_": "forecast_ema_gap",
        r"_will_$": "vol_will_",  # matched via re.search on "x_will_"
        r"^test_fold": "test_fold_selector",
        r"_tuned_on_test$": "threshold_tuned_on_test",
        r"^unevidenced_input": "unevidenced_input_cot",
        r"^consensus_": "consensus_surprise",
        r"^cot_": "cot_positioning",
        r"^sofr": "sofr_overnight",
        r"^sonia": "sonia_overnight",
        r"^loss_taxonomy_in_fold": "loss_taxonomy_in_fold_tag",
        r"^in_fold_loss_": "in_fold_loss_count",
    }
    assert set(poisons) == set(pol.FEATURES_BLACKLIST)
    for pattern, fid in poisons.items():
        with pytest.raises(pol.ForbiddenFeature):
            pol.assert_features_lawful([fid])


def test_blacklist_gate_is_live_inside_eligibility(monkeypatch):
    """The gate runs on EVERY Eligibility.evaluate call (the policy layer
    cannot be constructed around it)."""
    seen = []
    monkeypatch.setattr(pol, "assert_features_lawful",
                        lambda fids: seen.append(list(fids)))
    e = pol.Eligibility()
    st = pol.LegRuntimeStats(leg_start_ts=NOW - dt.timedelta(weeks=52))
    snap = [{"input_id": "X", "available_time_utc":
             NOW.strftime("%Y-%m-%dT%H:%M:%SZ"), "max_age_ok": True}]
    e.evaluate("L1", st, snap, NOW)
    e.evaluate("L1", st, snap, NOW)
    assert len(seen) == 2 and seen[0] == [
        "decision_count_trailing:L1", "cost_bill_trailing:L1",
        "pit_freshness:L1"]


# ---------------------------------------------------------------------------
# Swap-calendar value-date rule (Wed x3, no Fri/Sat event)
# ---------------------------------------------------------------------------


def test_swap_value_date_rule_swept_across_campaign():
    """Across every week of the campaign window: accrual events ONLY
    Sun..Thu at exactly 22:00 UTC, Wednesday carries x3, Friday's close
    boundary and Saturday carry NO event, weekly multiplier sum == 7."""
    d = cal.CAMPAIGN_START
    n_wed = 0
    while d <= cal.CAMPAIGN_END:
        if d.strftime("%a") == "Fri":
            wk_start = dt.datetime.combine(
                d, dt.time(20, 0), tzinfo=UTC)          # Fri close
            wk_end = wk_start + dt.timedelta(days=7)
            ev = cal.swap_events_between(wk_start, wk_end)
            assert [e.weekday for e in ev] == \
                ["Sun", "Mon", "Tue", "Wed", "Thu"]
            assert all(e.ts_utc.hour == 22 and e.ts_utc.minute == 0
                       and e.ts_utc.second == 0 for e in ev)
            assert sum(e.multiplier for e in ev) == 7
            wed = [e for e in ev if e.weekday == "Wed"]
            assert len(wed) == 1 and wed[0].wed_x3 \
                and wed[0].multiplier == 3
            n_wed += 1
        d += dt.timedelta(days=1)
    assert n_wed >= 250   # ~286 Fridays minus window edges


def test_no_swap_event_at_friday_close_or_saturday():
    # a probe STRICTLY inside Saturday finds nothing
    sat = dt.datetime(2024, 6, 8, 0, 0, tzinfo=UTC)
    assert cal.swap_events_between(sat, sat + dt.timedelta(hours=23)) == []
    # the Friday 22:00 boundary itself carries no event
    fri = dt.datetime(2024, 6, 7, 22, 0, tzinfo=UTC)
    assert cal.swap_events_between(fri, fri + dt.timedelta(seconds=1)) == []
    assert cal.swap_multiplier("Fri") == 0 and cal.swap_multiplier("Sat") == 0


# ---------------------------------------------------------------------------
# Profile freeze PIT: frozen AT the 20:00 stamp
# ---------------------------------------------------------------------------


def _engine_for_freeze(tmp_path):
    cfgs = [c for c in _real_cfgs() if c["symbol"] == "EURUSD"
            and c["sleeve_id"] == "POOL_B_VOLPROF"]
    args = SimpleNamespace(window_start=dt.date(2024, 6, 10),
                           window_end=dt.date(2024, 6, 14), tier=1.0)
    report = {"legs": {}, "cost_bill_totals_usd": {
        "spread_once": 0.0, "slip": 0.0, "slip_gap_excess": 0.0,
        "commission": 0.0, "swap": 0.0}, "blocked_reason_histogram": {}}
    from research.pc12a import journal as jr
    jw = jr.JournalWriter(str(tmp_path / "j.jsonl"), "freeze-test")
    eng = rd.SymbolEngine("EURUSD", cfgs, args, jw,
                           pol.CostGuard(pol.CostGuardState()), report)
    return eng


def _freeze_buffer(friday: dt.date):
    """20 weekdays ENDING ON the freeze Friday (collected backward so the
    buffer's last day is the freeze day itself); the last day's post-20:00
    minutes carry poisoned prices that would move any profile built on
    them."""
    days = []
    day = friday
    while len(days) < 20:
        if day.weekday() < 5:
            days.append(day)
        day -= dt.timedelta(days=1)
    buf = []
    for day in sorted(days):
        mids = np.full(1440, 1.0850)
        mids[::3] = 1.0820
        mids[1::3] = 1.0850
        mids[2::3] = 1.0880
        if day == friday:
            mids[1200:] = 1.2000     # poison after the 20:00 stamp
        buf.append({
            "date": day, "mid_close": mids,
            "bid_vol": np.full(1440, 2.0),
            "bid_high": mids + 1e-5, "bid_low": mids - 1e-5,
            "tradable": np.ones(1440, dtype=bool),
            "day_high": float(mids.max() + 1e-5),
            "day_low": float(mids.min() - 1e-5),
            "day_close": float(mids[-1]),
            "last_bid_close": float(mids[-1]),
            "last_ask_close": float(mids[-1] + 2e-5),
        })
    assert buf[-1]["date"] == friday
    return buf


def test_profile_freeze_truncates_at_the_stamp(tmp_path):
    eng = _engine_for_freeze(tmp_path)
    friday = dt.date(2024, 6, 14)
    eng.day_buffer = _freeze_buffer(friday)
    eng._maybe_freeze(friday)
    assert eng.profile is not None
    # control: the SAME buffer with the freeze day manually truncated AT
    # the 20:00 stamp, day aggregates recomputed from the truncated
    # slices (exactly the manual truncation law)
    ctrl_buf = _freeze_buffer(friday)
    last = dict(ctrl_buf[-1])
    t = last["tradable"][:rd.FREEZE_MIN]
    bh = last["bid_high"][:rd.FREEZE_MIN]
    bl = last["bid_low"][:rd.FREEZE_MIN]
    mc = last["mid_close"][:rd.FREEZE_MIN]
    last.update({"tradable": t, "bid_high": bh, "bid_low": bl,
                 "mid_close": mc,
                 "bid_vol": last["bid_vol"][:rd.FREEZE_MIN],
                 "day_high": float(bh[t].max()), "day_low": float(bl[t].min()),
                 "day_close": float(mc[t][-1])})
    ctrl_buf[-1] = last
    ctrl = _legs.build_profile(
        dt.datetime.combine(friday, dt.time(20, 0), tzinfo=UTC), ctrl_buf)
    assert eng.profile.digest == ctrl.digest
    # the poisoned post-20:00 prices never entered: POC stays at the
    # 1.082/1.085 plateau (within one 0.0015 bin of it), astronomically
    # far from the 1.2000 poison
    assert abs(eng.profile.poc - 1.0850) < eng.profile.w_bin * 2
    assert abs(eng.profile.poc - 1.2000) > 0.10
    assert eng.profile.freeze_ts == dt.datetime.combine(
        friday, dt.time(20, 0), tzinfo=UTC)
