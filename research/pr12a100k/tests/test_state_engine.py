"""Tests for pr12a100k.state_engine (Lane I1b, PORTFOLIO-ROUTER-12ASSETS-100K-V1).

Six frozen-contract test classes (dispatch packet):
  (1) no-lookahead truncation law (>=30 sampled decision dates 2021-2026 on
      the real panel, byte-identical vs full-panel computation) + a synthetic
      always-run twin;
  (2) V3 10-day rule boundary (decision-9d invisible, decision-10d visible);
  (3) staleness fail-closed => ABSTAIN (injected gaps per variable);
  (4) dwell/merge hand-fixture (expected effective sequence hand-drawn);
  (5) ladder priority (WAR+STRESS+TIGHT all true => WAR_ENERGY);
  (6) determinism (same inputs twice => identical canonical JSON bytes).

Real-data tests skip when the raw store is absent; every other fixture is
synthetic and tiny. No network, no PnL anywhere.
"""

import json
import os
import sys

import numpy as np
import pandas as pd
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

import state_engine as se  # noqa: E402

RAW = os.path.expanduser("~/.my-quantitative-data/pr12a100k/raw")
REAL_PANEL_AVAILABLE = all(
    os.path.isfile(p) for p in se.DEFAULT_PATHS.values())

T, W, R, E, AB = ("TIGHTENING", "WAR_ENERGY", "RISK_STRESS", "EASING",
                  "ABSTAIN")


def friday_ts(date: str) -> pd.Timestamp:
    """Friday 17:00 America/New_York decision timestamp from an ISO date."""
    assert pd.Timestamp(date).dayofweek == 4, f"{date} is not a Friday"
    return se._decision_friday_ts(pd.Timestamp(date))


# ---------------------------------------------------------------------------
# synthetic panel builder
# ---------------------------------------------------------------------------

def synth_panel(end: str, *, effr=None, vix=None, oil=None):
    """Small synthetic MacroPanel.

    ``effr``/``vix``/``oil`` are optional (value, last_date) overrides:
    ``oil`` = (brent, wti) lists aligned on common business days. Defaults
    produce a calm MID/CALM/BASE panel with full window history.
    """
    end_d = pd.Timestamp(end)
    bdays = pd.bdate_range(end_d - pd.Timedelta(days=900), end_d)

    if effr is None:
        e_vals = np.full(400, 0.08)
        e_dates = bdays[-400:]
    else:
        e_dates = effr[0]
        e_vals = effr[1]
    effr_s = pd.Series(e_vals, index=pd.DatetimeIndex(e_dates), name="EFFR")

    if vix is None:
        v_vals = 15.0 + 3.0 * np.sin(np.linspace(0.0, 9.0, 300))
        v_dates = bdays[-300:]
    else:
        v_dates = vix[0]
        v_vals = vix[1]
    vix_s = pd.Series(v_vals, index=pd.DatetimeIndex(v_dates), name="VIX")

    if oil is None:
        o_dates = bdays[-300:]
        # genuinely varying spread: a CONSTANT series ranks p100 under the
        # inclusive percentile convention and would read WAR_ENERGY
        b_vals = 63.0 + np.sin(np.linspace(0.0, 9.0, 300))
        w_vals = np.full(300, 60.0)
    else:
        o_dates, b_vals, w_vals = oil
    brent_s = pd.Series(b_vals, index=pd.DatetimeIndex(o_dates),
                        name="DCOILBRENTEU")
    wti_s = pd.Series(w_vals, index=pd.DatetimeIndex(o_dates),
                      name="DCOILWTICO")
    return se.MacroPanel(effr=effr_s, vix=vix_s, brent=brent_s, wti=wti_s,
                         sources={"synthetic": True})


# ---------------------------------------------------------------------------
# (1) no-lookahead truncation law
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not REAL_PANEL_AVAILABLE,
                    reason="raw macro store not present on this host")
def test_no_lookahead_truncation_real_panel():
    panel = se.build_macro_panel()
    fridays = pd.date_range("2021-01-08", "2026-06-26", freq="7D")
    sampled = [fridays[i] for i in range(0, len(fridays), 9)]
    assert len(sampled) >= 30
    for f in sampled:
        ts = se._decision_friday_ts(f)
        full = se.compute_state(ts, panel)
        trunc = se.compute_state(ts, panel.truncate(ts))
        assert full.to_json() == trunc.to_json(), (
            f"lookahead leak at {ts.isoformat()}: "
            f"{full.to_json()} != {trunc.to_json()}")


def test_no_lookahead_truncation_synthetic():
    # future VIX/oil/effr observations exist past the decision but must not
    # be visible at it
    end = "2026-03-06"  # a Friday
    bdays = pd.bdate_range(pd.Timestamp("2024-01-01"),
                           pd.Timestamp(end) + pd.Timedelta(days=7))
    rng = np.random.default_rng(7)
    v_vals = 15.0 + rng.normal(0, 3.0, len(bdays))
    v_vals[-1] = 55.0  # a post-decision spike that must stay invisible
    panel = synth_panel(
        end,
        vix=(bdays, v_vals),
        oil=(bdays, 63.0 + rng.normal(0, 1.0, len(bdays)),
             60.0 + rng.normal(0, 1.0, len(bdays))),
    )
    ts = friday_ts(end)
    full = se.compute_state(ts, panel)
    trunc = se.compute_state(ts, panel.truncate(ts))
    assert full.to_json() == trunc.to_json()


# ---------------------------------------------------------------------------
# (2) V3 10-day rule boundary
# ---------------------------------------------------------------------------

def test_v3_ten_day_rule_boundary():
    dec = "2026-02-06"                       # Friday decision
    dec_d = pd.Timestamp(dec)
    visible_d = dec_d - pd.Timedelta(days=10)   # Tuesday: <= cutoff
    invisible_d = dec_d - pd.Timedelta(days=9)  # Wednesday: > cutoff
    assert visible_d.dayofweek == 1 and invisible_d.dayofweek == 2

    bdays = pd.bdate_range(dec_d - pd.Timedelta(days=900),
                           dec_d - pd.Timedelta(days=11))
    # window spreads oscillate in [2, 4]; the visible boundary row sits at
    # exactly 3.0 (mid-rank, far from p85)
    spread_pat = 3.0 + np.sin(np.linspace(0.0, 9.0, len(bdays)))
    brent = pd.Series(list(3.0 + spread_pat) + [3.0],
                      index=pd.DatetimeIndex(list(bdays) + [visible_d]),
                      name="DCOILBRENTEU")
    wti = pd.Series(list(np.zeros(len(bdays))) + [0.0],
                    index=pd.DatetimeIndex(list(bdays) + [visible_d]),
                    name="DCOILWTICO")
    # invisible observation with an extreme spread that WOULD flip the band
    # (a .loc enlargement on a fresh label adds the row to the panel; the
    # 10-day rule must make it unreachable)
    brent.loc[invisible_d] = 140.0
    wti.loc[invisible_d] = 0.0

    bdays300 = pd.bdate_range(dec_d - pd.Timedelta(days=900),
                              dec_d - pd.Timedelta(days=11))
    panel = se.MacroPanel(
        effr=pd.Series(np.full(400, 0.08),
                       index=pd.DatetimeIndex(bdays300[-400:]), name="EFFR"),
        vix=pd.Series(np.full(300, 15.0),
                      index=pd.DatetimeIndex(bdays300[-300:]), name="VIX"),
        brent=brent, wti=wti, sources={"synthetic": True})

    res = se.compute_state(friday_ts(dec), panel)
    assert res.vars["v3_spread"] == 3.0          # exactly the visible value
    # sanity: the visible spread sits mid-window (flat ~3.0), nowhere near p85
    assert res.vars["v3_pct"] < 85.0
    assert res.vars["v3_band"] == "BASE"
    assert res.ages_days["v3"] == 10
    # and the invisible obs really would have flipped the band if the rule
    # were off-by-one (its spread is 140 vs window ~3)
    assert 140.0 == brent.loc[invisible_d] - wti.loc[invisible_d]


# ---------------------------------------------------------------------------
# (3) staleness fail-closed => ABSTAIN
# ---------------------------------------------------------------------------

def test_staleness_abstain_per_variable():
    dec = "2026-02-06"
    dec_d = pd.Timestamp(dec)
    bdays = pd.bdate_range(dec_d - pd.Timedelta(days=900), dec_d)

    def make(vix_end=None, effr_end=None, oil_end=None):
        v_dates = bdays if vix_end is None else bdays[bdays <= vix_end]
        e_dates = bdays if effr_end is None else bdays[bdays <= effr_end]
        o_dates = bdays if oil_end is None else bdays[bdays <= oil_end]
        # varying spread AND varying VIX: constant series rank p100 under
        # the inclusive percentile convention (calm control must stay calm)
        b_vals = 3.0 + np.sin(np.linspace(0.0, 9.0, len(o_dates)))
        v_vals = 15.0 + 3.0 * np.sin(np.linspace(0.0, 9.0, len(v_dates)))
        return se.MacroPanel(
            effr=pd.Series(np.full(len(e_dates), 0.08),
                           index=pd.DatetimeIndex(e_dates), name="EFFR"),
            vix=pd.Series(v_vals,
                          index=pd.DatetimeIndex(v_dates), name="VIX"),
            brent=pd.Series(b_vals, index=pd.DatetimeIndex(o_dates),
                            name="DCOILBRENTEU"),
            wti=pd.Series(np.zeros(len(o_dates)),
                          index=pd.DatetimeIndex(o_dates),
                          name="DCOILWTICO"),
            sources={"synthetic": True})

    ts = friday_ts(dec)
    # healthy control
    res = se.compute_state(ts, make())
    assert res.state == AB and not any(res.stale_flags.values())

    # v2 stale: last VIX obs 8 business days before the decision (> 5)
    res = se.compute_state(ts, make(vix_end=dec_d - pd.Timedelta(days=13)))
    assert res.state == AB and res.stale_flags["v2"] is True
    assert res.ages_days["v2"] > 5

    # v1 stale: last EFFR effectiveDate 15 calendar days old (> 10)
    res = se.compute_state(ts, make(effr_end=dec_d - pd.Timedelta(days=15)))
    assert res.state == AB and res.stale_flags["v1"] is True

    # v3 stale: latest usable common observation 30 calendar days old (> 25)
    res = se.compute_state(ts, make(oil_end=dec_d - pd.Timedelta(days=30)))
    assert res.state == AB and res.stale_flags["v3"] is True

    # insufficient history: missing input also => ABSTAIN
    res = se.compute_state(ts, make(vix_end=dec_d - pd.Timedelta(days=300)))
    assert res.state == AB and res.stale_flags["v2"] is True


# ---------------------------------------------------------------------------
# (4) dwell / merge hand fixture
# ---------------------------------------------------------------------------

def test_dwell_hand_fixture():
    candidates = [T, T, W, W, W, R, R, T, AB, T, T, E, E]
    # hand-drawn expectation (13 in, 13 out): init holds; a new state becomes
    # effective at its 2nd consecutive observation; ABSTAIN is effective
    # immediately; after an abstain run the re-entering state again needs
    # 2 consecutive observations (index 9 holds AB, index 10 flips to T).
    expected = [T, T, T, W, W, W, R, R, AB, AB, T, T, E]
    assert se.apply_dwell(candidates) == expected


def test_episode_merge_hand_fixture():
    eff = [W, W, W, T, W, W]     # same-state runs separated by 1 week (<4)
    ids = se._episode_ids(eff)
    assert ids[0] == ids[1] == ids[2] == ids[4] == ids[5] == "EP001"
    assert ids[3] == "EP002"

    # separation of exactly 4 intervening weeks does NOT merge
    eff = [W, W, W, T, T, T, T, W, W]
    ids = se._episode_ids(eff)
    assert ids[0] != ids[7]

    # dwell+merge on the hand fixture of test_dwell_hand_fixture:
    eff = se.apply_dwell([T, T, W, W, W, R, R, T, AB, T, T, E, E])
    ids = se._episode_ids(eff)
    # T run(0-2) and T run(10-12) are separated by 7 intervening weeks: no merge
    assert ids[0] != ids[10]
    assert len(set(ids)) == 6   # six distinct merged episodes


def test_whipsaw_flag():
    eff = [T, E, T, E, T, E, T, E]
    flags = se._whipsaw_flags(eff)
    assert flags[0] is False
    assert flags[-1] is True    # 7 flips in trailing 8 obs > 4
    assert se._whipsaw_flags([T] * 8)[-1] is False


# ---------------------------------------------------------------------------
# (5) ladder priority
# ---------------------------------------------------------------------------

def test_ladder_priority_order():
    assert se.ladder("TIGHT", "STRESS", "WAR") == W
    assert se.ladder("MID", "STRESS", "WAR") == W
    assert se.ladder("EASE", "STRESS", "WAR") == W
    assert se.ladder("TIGHT", "STRESS", "BASE") == R
    assert se.ladder("TIGHT", "CALM", "BASE") == T
    assert se.ladder("EASE", "CALM", "BASE") == E
    assert se.ladder("MID", "CALM", "BASE") == AB


def test_ladder_priority_synthetic_panel_all_three_fire():
    dec = "2026-02-06"
    dec_d = pd.Timestamp(dec)
    bdays = pd.bdate_range(dec_d - pd.Timedelta(days=900), dec_d)
    # V1 TIGHT: EFFR ramps +0.63% over the 63-row window (~+63bp)
    effr = pd.Series(np.linspace(0.0, 1.0, 400),
                     index=pd.DatetimeIndex(bdays[-400:]), name="EFFR")
    # V2 STRESS: latest usable VIX (decision-1d) is the window max
    v_vals = np.full(300, 15.0)
    v_vals[-1] = 40.0
    vix = pd.Series(v_vals, index=pd.DatetimeIndex(bdays[-300:]), name="VIX")
    # V3 WAR: latest visible common spread (decision-10d) is the window max
    o_vals_b = np.full(300, 63.0)
    o_vals_w = np.full(300, 60.0)
    o_dates = bdays[-300:]
    o_dates = o_dates[o_dates <= dec_d - pd.Timedelta(days=10)]
    n = len(o_dates)
    o_vals_b = np.full(n, 63.0)
    o_vals_w = np.full(n, 60.0)
    o_vals_b[-1] = 70.0   # spread 10.0, clearly > flat 3.0 window
    panel = se.MacroPanel(
        effr=effr, vix=vix,
        brent=pd.Series(o_vals_b, index=pd.DatetimeIndex(o_dates),
                        name="DCOILBRENTEU"),
        wti=pd.Series(o_vals_w, index=pd.DatetimeIndex(o_dates),
                      name="DCOILWTICO"),
        sources={"synthetic": True})
    res = se.compute_state(friday_ts(dec), panel)
    assert res.vars["v1_band"] == "TIGHT"
    assert res.vars["v2_band"] == "STRESS"
    assert res.vars["v3_band"] == "WAR"
    assert res.state == W   # WAR_ENERGY wins the tie, frozen priority 1


# ---------------------------------------------------------------------------
# (6) determinism
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not REAL_PANEL_AVAILABLE,
                    reason="raw macro store not present on this host")
def test_determinism_real_panel():
    panel = se.build_macro_panel()
    a = se.compute_state(friday_ts("2022-11-04"), panel)
    b = se.compute_state(friday_ts("2022-11-04"), panel)
    assert a.to_json() == b.to_json()
    # json round-trip stability
    rt = json.loads(a.to_json())
    assert json.dumps(rt, sort_keys=True, separators=(",", ":")) == a.to_json()


def test_determinism_synthetic():
    panel = synth_panel("2026-03-06")
    a = se.compute_state(friday_ts("2026-03-06"), panel)
    b = se.compute_state(friday_ts("2026-03-06"), panel)
    assert a.to_json() == b.to_json()


# ---------------------------------------------------------------------------
# API contract guards
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not REAL_PANEL_AVAILABLE,
                    reason="raw macro store not present on this host")
def test_state_timeline_matches_compute_state():
    panel = se.build_macro_panel()
    fridays = pd.date_range("2021-01-08", "2026-06-26", freq="7D")
    tl = se.state_timeline(panel, [f.date().isoformat() for f in fridays])
    assert len(tl) == 286
    for i in (0, 1, 57, 150, 285):
        ts = se._decision_friday_ts(fridays[i])
        res = se.compute_state(ts, panel)
        row = tl.iloc[i]
        assert row["decision_ts"] == res.decision_ts
        assert row["state"] == res.state
        assert row["effective_state"] == res.effective_state
        assert row["episode_id"] == res.episode_id
        assert bool(row["whipsaw_flag"]) == res.whipsaw_flag
    # determinism of the whole timeline
    tl2 = se.state_timeline(panel, [f.date().isoformat() for f in fridays])
    pd.testing.assert_frame_equal(tl, tl2)


def test_non_friday_rejected():
    panel = synth_panel("2026-03-06")
    with pytest.raises(ValueError):
        se.compute_state("2026-03-09", panel)  # a Monday


def test_result_field_contract():
    panel = synth_panel("2026-03-06")
    res = se.compute_state(friday_ts("2026-03-06"), panel)
    d = res.to_dict()
    assert set(d) == {"decision_ts", "state", "effective_state", "vars",
                      "ages_days", "stale_flags", "whipsaw_flag",
                      "episode_id"}
    assert set(d["vars"]) == {"v1_pm_bp", "v1_band", "v2_pct", "v2_band",
                              "v3_spread", "v3_pct", "v3_band"}
    assert set(d["ages_days"]) == {"v1", "v2", "v3"}
    assert set(d["stale_flags"]) == {"v1", "v2", "v3"}
    assert d["state"] in se.STATES and d["effective_state"] in se.STATES
