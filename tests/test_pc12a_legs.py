"""PC12A legs: identity tuples, VOLPROF profile construction on a
hand-checkable synthetic buffer, arm trigger behaviour, config round-trip."""

import datetime as dt
import json

import numpy as np
import pytest

from research.pc12a import legs

UTC = dt.timezone.utc


def _day_buffer_entry(date, mids, vols, tradable=None):
    mids = np.asarray(mids, dtype=np.float64)
    vols = np.asarray(vols, dtype=np.float64)
    n = len(mids)
    trad = np.ones(n, dtype=bool) if tradable is None else np.asarray(
        tradable, dtype=bool)
    return {
        "date": date, "mid_close": mids, "bid_vol": vols,
        "bid_high": mids + 1e-5, "bid_low": mids - 1e-5, "tradable": trad,
        "day_high": float(mids.max() + 1e-5), "day_low": float(mids.min()
                                                               - 1e-5),
        "day_close": float(mids[-1]), "last_bid_close": float(mids[-1]),
        "last_ask_close": float(mids[-1] + 2e-5),
    }


def test_identity_tuple_round_trip(tmp_path):
    cfgs = legs.default_leg_configs()
    assert len(cfgs) == 12
    for cfg in cfgs:
        ident = legs.make_identity(cfg)
        assert ident.cycle_id == "PORTFOLIO-COMPOSITE-12ASSETS-100K-V1"
        assert ident.outcome_exposed_label
        assert ident.cluster_id
        assert len(ident.arm_config_digest) == 64
        leg = legs.build_leg(cfg)
        assert leg.identity.candidate_id == ident.candidate_id
    # the 9 VOLPROF candidates carry the frozen class identity fields
    vp = [c for c in cfgs if c["sleeve_id"] == "POOL_B_VOLPROF"]
    assert len(vp) == 9
    assert {c["class_candidate_id"].split("-")[0] for c in vp} == \
        {"VC1", "VC2", "VC3"}
    assert {c["symbol"] for c in vp} == {"EURUSD", "GBPUSD", "USDJPY"}
    # every exemplar carries its outcome-exposed label
    ex = {c["corpus_gid"]: c["outcome_exposed_label"] for c in cfgs
          if c["sleeve_id"] == "POOL_B_TRIAGE"}
    assert ex == {"USDJPY-S001": "FAMILY_HISTORY_NEGATIVE",
                  "GBPUSD-S027": "FAMILY_HISTORY_NEGATIVE",
                  "EURUSD-S009": "F0_INDIVIDUAL_REJECT"}


def test_config_dir_round_trip(tmp_path):
    d = tmp_path / "legs"
    d.mkdir()
    for cfg in legs.default_leg_configs():
        lid = cfg.get("class_candidate_id") or cfg["corpus_gid"]
        (d / f"{lid}.json").write_text(json.dumps(cfg))
    loaded = legs.load_leg_configs(str(d))
    key = lambda c: c.get("class_candidate_id") or c["corpus_gid"]
    assert {key(c) for c in loaded} == {key(c) for c in
                                        legs.default_leg_configs()}
    assert len(loaded) == 12


def test_profile_poc_va_and_bin_width_frozen_construction():
    """20 weekdays x 480 minutes (>= the 360-tradable-minute day rule) at
    three price plateaus with activity masses: 30% at 1.0800, 50% at 1.0850
    (POC), 20% at 1.0900. Hand-checkable."""
    buf = []
    base = dt.date(2024, 5, 3)
    day = base
    while len(buf) < 20:
        if day.weekday() < 5:
            mids, vols = [], []
            for i in range(480):
                level = 1.0800 if i % 3 == 0 else (
                    1.0850 if i % 3 == 1 else 1.0900)
                mids.append(level)
                vols.append(5.0 if i % 3 == 1 else 3.0)
            buf.append(_day_buffer_entry(day, mids, vols))
        day += dt.timedelta(days=1)
    prof = legs.build_profile(dt.datetime(2024, 5, 31, 20, 0, tzinfo=UTC),
                              buf)
    # bin assignment truncates (1.085 - 1.08)/w -- the 1.0850 plateau lands
    # in the bin whose CENTER can sit below 1.0850; POC within one bin
    assert prof.poc == pytest.approx(1.0850, abs=prof.w_bin)
    # greedy VA: POC bin + the heavier adjacent (the 1.0800 plateau, 9600)
    # crosses 70% of the 35,200 window total -> VA = the two lower bins
    assert prof.val == pytest.approx(1.0800, abs=1e-12)
    assert prof.vah == pytest.approx(1.0850, abs=1e-9)
    assert prof.w_bin == pytest.approx(0.0025, abs=1e-12)  # 0.25 x ATR20d
    # percentile thresholds over populated bins
    assert 0.0 <= prof.p20 <= prof.p80


def test_profile_bin_width_quanta_down_to_grid():
    # ATR driven by a fixed 60-pip daily range -> raw W = 0.25*ATR
    buf = []
    day = dt.date(2024, 5, 3)
    while len(buf) < 20:
        if day.weekday() < 5:
            mids = np.full(480, 1.0850)
            mids[::3] = 1.0820
            mids[1::3] = 1.0850
            mids[2::3] = 1.0880
            buf.append(_day_buffer_entry(day, mids,
                                         np.full(480, 2.0)))
        day += dt.timedelta(days=1)
    prof = legs.build_profile(dt.datetime(2024, 5, 31, 20, 0, tzinfo=UTC),
                              buf)
    # quantized DOWN onto the 0.1-pip (1e-5) grid
    assert abs(prof.w_bin / 1e-5 - round(prof.w_bin / 1e-5)) < 1e-9


def _volprof_leg(shape="vc1_vaedge", symbol="EURUSD"):
    cfg = [c for c in legs.VOLPROF_DEFAULT_CONFIGS
           if c["symbol"] == symbol
           and c["mech_key"] == shape][0]
    return legs.build_leg(cfg)


def _ctx(ts, mid_close, mid_prev, atr60=0.0005, in_win=True, prof=None,
         flat=False, bid_low=None, ask_high=None):
    return legs.BarContext(
        ts=ts, symbol="EURUSD", mid_close=mid_close,
        mid_close_prev=mid_prev, bid_open=mid_close - 2e-5,
        ask_open=mid_close + 2e-5, bid_close=mid_close - 2e-5,
        ask_close=mid_close + 2e-5,
        bid_low=bid_low if bid_low is not None else mid_close - 3e-5,
        ask_high=ask_high if ask_high is not None else mid_close + 3e-5,
        atr60=atr60, in_entry_window=in_win, is_flat_instant=flat,
        day=ts.date(), profile=prof, last_data_ts=ts)


def _prof(val=1.0800, vah=1.0900, poc=1.0850, w=0.0010, p20=1.0, p80=3.0):
    p = legs.WeeklyProfile(
        freeze_ts=dt.datetime(2024, 6, 6, 20, 0, tzinfo=UTC),
        poc=poc, vah=vah, val=val, w_bin=w, p20=p20, p80=p80,
        atr20d=0.004, nodes=(1.0870,),
        bin_edges=np.arange(1.0700, 1.1000, w),
        bin_activity=np.full(len(np.arange(1.0700, 1.1000, w)), 2.0))
    p.digest = "testdigest" * 4
    return p


def test_vc1_edge_rejection_triggers():
    leg = _volprof_leg()
    prof = _prof()
    # beyond-edge bins in the fixture profile have activity 2.0 > p20=1.0
    # -> low-acceptance condition FAILS -> no entry
    ts = dt.datetime(2024, 6, 7, 9, 30, tzinfo=UTC)
    d = leg.on_bar(_ctx(ts, 1.0788, 1.0850, prof=prof))
    assert d is None
    # make the beyond-edge region genuinely low-acceptance (p20 above it)
    prof2 = _prof(p20=5.0)
    leg2 = _volprof_leg()
    d2 = leg2.on_bar(_ctx(ts, 1.0788, 1.0850, prof=prof2))
    assert d2 is not None and d2.vote == +1       # long from the lower edge
    assert d2.reason_code == "VC1_EDGE_REJECT_LONG"
    assert d2.desired_units == 10_000
    leg3 = _volprof_leg()
    d3 = leg3.on_bar(_ctx(ts, 1.0913, 1.0850, prof=prof2))
    assert d3 is not None and d3.vote == -1       # short from the upper edge
    assert d3.reason_code == "VC1_EDGE_REJECT_SHORT"
    # previous close OUTSIDE the VA -> no trigger
    leg4 = _volprof_leg()
    assert leg4.on_bar(_ctx(ts, 1.0788, 1.0700, prof=prof2)) is None


def test_vc1_exit_paths():
    leg = _volprof_leg()
    prof = _prof(p20=5.0)
    ts = dt.datetime(2024, 6, 7, 9, 30, tzinfo=UTC)
    leg.on_bar(_ctx(ts, 1.0788, 1.0850, prof=prof))  # enter long
    assert leg.desired_units == 10_000
    # TP at POC cross
    d = leg.on_bar(_ctx(ts + dt.timedelta(minutes=10), 1.0851, 1.0800,
                        prof=prof))
    assert d.vote == 0 and d.reason_code == "TP_POC"
    assert leg.desired_units == 0
    # ATR stop path on a fresh entry
    leg2 = _volprof_leg()
    leg2.on_bar(_ctx(ts, 1.0788, 1.0850, prof=prof))
    stop = leg2.stop_level
    d2 = leg2.on_bar(_ctx(ts + dt.timedelta(minutes=5), 1.0789, 1.0788,
                          prof=prof, bid_low=stop - 1e-6))
    assert d2.reason_code == "ATR_STOP" and d2.vote == 0
    # hard flat at the 19:54 decision instant
    leg3 = _volprof_leg()
    leg3.on_bar(_ctx(ts, 1.0788, 1.0850, prof=prof))
    flat_ts = ts.replace(hour=19, minute=54)
    d3 = leg3.on_bar(_ctx(flat_ts, 1.0800, 1.0800, prof=prof, flat=True))
    assert d3.reason_code == "TIME_STOP_FLAT_1955" and d3.vote == 0
    # cooldown blocks re-entry for 60 minutes
    assert leg3.on_bar(_ctx(flat_ts + dt.timedelta(minutes=30), 1.0788,
                            1.0850, prof=prof)) is None
    assert leg3.on_bar(_ctx(flat_ts + dt.timedelta(minutes=61), 1.0788,
                            1.0850, prof=prof)) is not None


def test_vc2_lvn_traverse_failure():
    leg = _volprof_leg("vc2_lvnfail")
    prof = _prof(p20=5.0)
    ts = dt.datetime(2024, 6, 7, 9, 30, tzinfo=UTC)
    # downward cross of node 1.0870 arms the pending traverse
    assert leg.on_bar(_ctx(ts, 1.0869, 1.0871, prof=prof)) is None
    assert leg.pending_traverse is not None
    # confirm: back above node by >= W_BIN -> long entry
    d = leg.on_bar(_ctx(ts + dt.timedelta(minutes=10), 1.0882, 1.0869,
                        prof=prof))
    assert d is not None and d.vote == +1
    assert d.reason_code == "VC2_LVNFAIL_LONG"
    # traverse confirmation expires after 60 minutes
    leg2 = _volprof_leg("vc2_lvnfail")
    leg2.on_bar(_ctx(ts, 1.0869, 1.0871, prof=prof))
    late = ts + dt.timedelta(minutes=61)
    d2 = leg2.on_bar(_ctx(late, 1.0882, 1.0869, prof=prof))
    assert d2 is None                      # window elapsed, not confirmed


def test_vc3_poc_magnet_deviation():
    leg = _volprof_leg("vc3_pocmag")
    prof = _prof(p80=1.0)                  # current bin >= P80 satisfied
    ts = dt.datetime(2024, 6, 7, 9, 30, tzinfo=UTC)
    # inside VA, >= 3 x ATR60 below POC, parked in an accepted bin
    d = leg.on_bar(_ctx(ts, 1.0833, 1.0833, atr60=0.0005, prof=prof))
    assert d is not None and d.vote == +1 and d.reason_code == "VC3_POCMAG"
    # deviation < 3 ATR60 -> no trigger
    leg2 = _volprof_leg("vc3_pocmag")
    assert leg2.on_bar(_ctx(ts, 1.0840, 1.0840, atr60=0.0005,
                            prof=prof)) is None
    # outside the VA -> no trigger
    leg3 = _volprof_leg("vc3_pocmag")
    assert leg3.on_bar(_ctx(ts, 1.0910, 1.0910, atr60=0.0005,
                            prof=prof)) is None


def test_volprof_staleness_fail_closed():
    leg = _volprof_leg()
    prof = _prof(p20=5.0)
    ts = dt.datetime(2024, 6, 7, 9, 30, tzinfo=UTC)
    ctx = _ctx(ts, 1.0788, 1.0850, prof=prof)
    ctx.last_data_ts = ts - dt.timedelta(seconds=120)   # > 90s stale
    assert leg.on_bar(ctx) is None                 # NOT_RUN, no decision
