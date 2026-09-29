"""BTC-COMBO6 tests: hand-computed expectations on SMALL synthetic 5m panels.

The 102-zip corpus is never touched here (the real dry run covers it);
synthetic worktree roots are built in tmp_path for the data-plane and CLI
end-to-end tests.
"""
from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from research.btcombo6 import combo, data, engine, signals, spec

T0 = pd.Timestamp("2021-01-04T00:00:00Z")
NS5 = 300_000_000_000


# ---------------------------------------------------------------------------
# fixtures / helpers
# ---------------------------------------------------------------------------

def grid_panel(start=T0, n=500, price=100.0):
    ts = pd.date_range(start=start, periods=n, freq="5min", tz="UTC")
    p = np.full(n, float(price))
    return pd.DataFrame({"ts": ts, "o": p, "h": p, "l": p, "c": p, "v": 0.0})


def set_bar(m5, i, o=None, h=None, l=None, c=None):
    for col, val in (("o", o), ("h", h), ("l", l), ("c", c)):
        if val is not None:
            m5.loc[m5.index[i], col] = float(val)
    return m5


def drop_bars(m5, idxs):
    return m5.drop(index=list(idxs)).reset_index(drop=True)


def mk_folds(start=T0, n=2, td=pd.Timedelta(days=1)):
    s = pd.Timestamp(start)
    return [{"fold": f"F{i+1}", "i": i, "start": s + i * td,
             "end": s + (i + 1) * td} for i in range(n)]


def one_decision(ts, enter=True):
    return pd.DataFrame({"decision_ts": pd.DatetimeIndex([pd.Timestamp(ts)]),
                         "enter": [bool(enter)]})


def run(decisions, m5, folds, stress=1.0, funding=None, leg="LEG-1",
        eval_end=None):
    if eval_end is None:
        eval_end = folds[-1]["end"]
    return engine.run_leg(leg, spec.LEGS[leg], decisions, m5, folds=folds,
                          eval_end=eval_end, stress=stress, funding=funding)


def trades_bytes(trades):
    return data.canonical_json(combo.trades_serializable(trades)).encode()


CPS1 = spec.cost_per_side(1.0)   # 6.0 bps -> 0.0006


# ---------------------------------------------------------------------------
# 1. Fill law
# ---------------------------------------------------------------------------

def test_fill_law_next_bar_open_exact_numbers():
    m5 = grid_panel(n=40)
    set_bar(m5, 5, c=100.5)                       # decision bar (state change)
    dec = one_decision(m5.loc[5, "ts"])           # decision at bar 5 open
    set_bar(m5, 6, o=100.0)                       # fill bar opens at 100
    set_bar(m5, 10, h=102.0)                      # TP trigger later
    res = run(dec, m5, mk_folds(n=1, td=pd.Timedelta(days=1)))
    assert len(res["trades"]) == 1
    tr = res["trades"][0]
    # fill at FIRST bar with open_time >= decision_ts + 5min -> bar 6
    assert tr["fill_ts"] == m5.loc[6, "ts"]
    assert tr["fill_px"] == 100.0
    assert tr["qty"] == pytest.approx(10000.0 / 100.0)
    assert tr["entry_fee"] == pytest.approx(10000.0 * CPS1)      # 6.0 USD
    assert tr["exit_ts"] == m5.loc[10, "ts"]
    assert tr["exit_reason"] == "TP"
    assert tr["exit_px"] == pytest.approx(100.0 * 1.01)          # 101
    assert tr["exit_fee"] == pytest.approx(101.0 * 100.0 * CPS1)  # 6.06
    assert tr["gross_pnl"] == pytest.approx(100.0 * (101.0 - 100.0))
    assert tr["net_pnl"] == pytest.approx(100.0 - 6.0 - 6.06)    # 87.94
    assert res["counters"]["entries_deferred"] == 0


def test_fill_law_defers_to_next_present_bar():
    m5 = grid_panel(n=40)
    dec = one_decision(m5.loc[5, "ts"])
    m5 = drop_bars(m5, [6])                       # target fill bar absent
    set_bar(m5, 6, o=100.0)                       # bar 6 (was 7) opens 100
    set_bar(m5, 10, h=102.0)
    res = run(dec, m5, mk_folds(n=1, td=pd.Timedelta(days=1)))
    tr = res["trades"][0]
    # first present bar >= decision+5min is now the old bar 7 (00:35)
    assert tr["fill_ts"] == pd.Timestamp("2021-01-04T00:35:00Z")
    assert res["counters"]["entries_deferred"] == 1


# ---------------------------------------------------------------------------
# 2. TP/SL same-bar pessimism
# ---------------------------------------------------------------------------

def test_same_bar_sl_wins_pessimistic():
    m5 = grid_panel(n=40)
    dec = one_decision(m5.loc[5, "ts"])
    set_bar(m5, 6, o=100.0, h=102.0, l=98.0)      # both TP and SL in fill bar
    res = run(dec, m5, mk_folds(n=1, td=pd.Timedelta(days=1)))
    tr = res["trades"][0]
    assert tr["exit_ts"] == m5.loc[6, "ts"]       # exit in the fill bar itself
    assert tr["exit_reason"] == "SL"
    assert tr["exit_px"] == pytest.approx(99.0)   # SL level (open above it)
    assert tr["gross_pnl"] == pytest.approx(100.0 * (99.0 - 100.0))


# ---------------------------------------------------------------------------
# 3. SL gap-through worst fill
# ---------------------------------------------------------------------------

def test_sl_gap_through_exits_at_open():
    m5 = grid_panel(n=40)
    dec = one_decision(m5.loc[5, "ts"])
    set_bar(m5, 6, o=100.0)
    set_bar(m5, 8, o=97.0, h=97.5, l=96.0, c=96.5)   # opens below SL level
    res = run(dec, m5, mk_folds(n=1, td=pd.Timedelta(days=1)))
    tr = res["trades"][0]
    assert tr["exit_reason"] == "SL_GAP"
    assert tr["exit_ts"] == m5.loc[8, "ts"]
    assert tr["exit_px"] == pytest.approx(97.0)    # min(SL level 99, open 97)
    assert tr["gross_pnl"] == pytest.approx(100.0 * (97.0 - 100.0))


# ---------------------------------------------------------------------------
# 4. Force-flat at fold boundary
# ---------------------------------------------------------------------------

def test_force_flat_at_fold_boundary_attributed_to_closing_fold():
    m5 = grid_panel(n=700)                          # ~2.43 days
    folds = mk_folds(n=2, td=pd.Timedelta(days=1))
    dec1 = one_decision(m5.loc[5, "ts"])            # fills in fold F1
    # fold1 end = 2021-01-05T00:00 -> first bar >= it has index 288
    set_bar(m5, 288, o=105.0)
    res = run(dec1, m5, folds)
    tr = res["trades"][0]
    assert tr["exit_reason"] == "FORCE_FLAT"
    assert tr["exit_ts"] == pd.Timestamp("2021-01-05T00:00:00Z")
    assert tr["exit_px"] == 105.0
    assert tr["fold"] == "F1"                       # attributed to closing fold

    # final fold: boundary == eval_end, bars exist past it (sealed) ->
    # close at the LAST IN-WINDOW bar close (23:55), ts < eval_end.
    dec2 = one_decision(m5.loc[288, "ts"])          # decision at boundary bar
    res2 = run(pd.concat([dec1, dec2], ignore_index=True), m5, folds)
    assert len(res2["trades"]) == 2
    tr2 = res2["trades"][1]
    assert tr2["fold"] == "F2"
    assert tr2["exit_reason"] == "FORCE_FLAT"
    last_in_window = pd.Timestamp("2021-01-05T23:55:00Z")
    assert tr2["exit_ts"] == last_in_window         # open time of last bar
    assert tr2["exit_px"] == float(m5.loc[575, "c"])  # its close (last in-window bar)
    assert tr2["exit_ts"] < folds[-1]["end"]


# ---------------------------------------------------------------------------
# 5. Funding
# ---------------------------------------------------------------------------

def test_funding_window_signs_and_exclusions():
    m5 = grid_panel(n=250)
    dec = one_decision(m5.loc[5, "ts"])             # fill at 00:30 (bar 6)
    set_bar(m5, 6, o=100.0)
    set_bar(m5, 198, h=102.0)                       # TP exit at 16:30 (bar 198)
    events = pd.DataFrame({
        "ts": pd.DatetimeIndex([
            "2021-01-04T00:30:00Z",   # == fill_ts -> excluded (strict >)
            "2021-01-04T08:00:00Z",   # inside
            "2021-01-04T16:00:00Z",   # inside
            "2021-01-04T16:30:00Z",   # == exit_ts -> included (<=)
            "2021-01-04T17:00:00Z",   # after exit -> excluded
        ]),
        "rate": [0.0005, 0.0001, 0.0002, 0.0003, 0.0010],
    })
    res = run(dec, m5, mk_folds(n=1, td=pd.Timedelta(days=1)), funding=events)
    tr = res["trades"][0]
    assert tr["funding"] == pytest.approx((0.0001 + 0.0002 + 0.0003) * 10000.0)
    # positive rate is a COST for longs: net < gross - fees
    assert tr["net_pnl"] == pytest.approx(
        tr["gross_pnl"] - tr["fees"] - (0.0006 * 10000.0))
    # negative rate is a rebate
    neg = pd.DataFrame({"ts": pd.DatetimeIndex(["2021-01-04T08:00:00Z"]),
                        "rate": [-0.0001]})
    res2 = run(dec, m5, mk_folds(n=1, td=pd.Timedelta(days=1)), funding=neg)
    assert res2["trades"][0]["funding"] == pytest.approx(-1.0)
    assert res2["trades"][0]["net_pnl"] == pytest.approx(
        res2["trades"][0]["gross_pnl"] - res2["trades"][0]["fees"] + 1.0)


# ---------------------------------------------------------------------------
# 6. Momentum state-change rule (no re-entry while condition holds)
# ---------------------------------------------------------------------------

def test_momentum_state_change_two_spikes_two_signals():
    m5 = grid_panel(n=300)
    set_bar(m5, 60, c=102.0)
    set_bar(m5, 120, c=103.0)
    dec = signals.leg_decisions("LEG-1", m5, eval_end=T0 + pd.Timedelta(days=3))
    enter = dec[dec["enter"]]
    assert list(enter["decision_ts"]) == [m5.loc[60, "ts"], m5.loc[120, "ts"]]
    # signal at 120 arrives while LONG (trade 1 rides to the fold boundary:
    # highs never reach the TP level) -> discarded before filling; exactly
    # one accepted fill and one closed trade
    res = run(dec, m5, mk_folds(n=1, td=pd.Timedelta(days=1)))
    assert res["counters"]["enter_signals_seen"] == 2
    assert res["counters"]["entries_filled"] == 1
    assert res["counters"]["signals_discarded_while_long"] == 1
    assert len(res["trades"]) == 1
    assert res["trades"][0]["exit_reason"] == "FORCE_FLAT"


def test_momentum_no_reentry_while_condition_holds():
    m5 = grid_panel(n=300)
    for i in range(60, 208):                        # plateau: mom >= 1% for bars 60..107
        m5.loc[i, "c"] = 102.0
    dec = signals.leg_decisions("LEG-1", m5, eval_end=T0 + pd.Timedelta(days=3))
    enter = dec[dec["enter"]]
    assert len(enter) == 1
    assert enter.iloc[0]["decision_ts"] == m5.loc[60, "ts"]
    res = run(dec, m5, mk_folds(n=1, td=pd.Timedelta(days=2)))
    # exactly one entry (still open: no TP/SL and panel ends before the fold
    # boundary -> no closed trade record). While the condition HOLDS no new
    # state-change signal exists at all, so nothing is even discarded: the
    # signal layer enforces "no re-entry while condition stays true".
    assert res["counters"]["entries_filled"] == 1
    assert res["counters"]["signals_discarded_while_long"] == 0
    assert len(res["trades"]) == 0
    assert res["open_at_frame_end"] is not None
    assert res["open_at_frame_end"]["fill_ts"] == m5.loc[61, "ts"]


# ---------------------------------------------------------------------------
# 7. Complete-bucket aggregation
# ---------------------------------------------------------------------------

def test_incomplete_bucket_absent_and_decision_defers():
    m5 = grid_panel(n=600)                          # ~2.08 days
    m5 = drop_bars(m5, [12])                        # hole at 01:00 -> 4h bucket 00:00 incomplete
    agg4 = data.aggregate(m5, "4h")
    assert pd.Timestamp("2021-01-04T00:00:00Z") not in set(agg4["ts"])
    assert pd.Timestamp("2021-01-04T04:00:00Z") in set(agg4["ts"])
    # decision at the 00:00-04:00 bucket close must NOT exist (bucket absent)
    dec = signals.leg_decisions("LEG-2", m5, eval_end=T0 + pd.Timedelta(days=2))
    assert pd.Timestamp("2021-01-04T03:55:00Z") not in set(dec["decision_ts"])
    assert pd.Timestamp("2021-01-04T07:55:00Z") in set(dec["decision_ts"])
    # 15m clock: hole kills its own 15m bucket only
    agg15 = data.aggregate(m5, "15min")
    assert pd.Timestamp("2021-01-04T01:00:00Z") not in set(agg15["ts"])  # contains the hole
    assert pd.Timestamp("2021-01-04T00:45:00Z") in set(agg15["ts"])      # 00:45-01:00 fine
    assert pd.Timestamp("2021-01-04T01:15:00Z") in set(agg15["ts"])      # 01:15-01:30 fine


def test_sma_nan_in_window_makes_signal_ineligible():
    # LEG-2 slow SMA(24h=288 bars): hole inside the trailing window -> spread
    # NaN -> the cross at that bucket close is ineligible.
    # Design: flat 100 for slots 0..599, ramp +0.1/bar from 600. The first
    # up-cross of SMA48-SMA288 fires at the 4h bucket whose sampled last bar
    # is slot 623 (2021-01-06T03:55Z, window 336..623). With slot 600 removed
    # that window is NaN -> no signal; every later spread is already >0 with
    # prev >0 -> no delayed cross either.
    m5 = grid_panel(n=900)
    for i in range(600, 900):
        m5.loc[i, "c"] = 100.0 + (i - 600) * 0.1
    dec_full = signals.leg_decisions("LEG-2", m5, eval_end=T0 + pd.Timedelta(days=4))
    e_full = set(dec_full[dec_full["enter"]]["decision_ts"])
    assert e_full == {pd.Timestamp("2021-01-06T03:55:00Z")}
    holed = drop_bars(m5.copy(), [600])
    dec_hole = signals.leg_decisions("LEG-2", holed, eval_end=T0 + pd.Timedelta(days=4))
    e_hole = set(dec_hole[dec_hole["enter"]]["decision_ts"])
    assert e_hole == set()                          # signal lost to the hole
    assert e_hole.issubset(e_full)


# ---------------------------------------------------------------------------
# 8. No-lookahead truncation replay
# ---------------------------------------------------------------------------

def _wiggle_panel(n=864):
    m5 = grid_panel(n=n)
    rng_prices = 100.0 + np.sin(np.arange(n) / 37.0) * 4.0
    for col in ("o", "h", "l", "c"):
        m5[col] = rng_prices
    # add spikes so the momentum leg trades several times
    for i in range(80, n, 130):
        m5.loc[i, "c"] = m5.loc[i, "c"] + 3.0
    return m5


def test_truncation_replay_prefix_stability():
    m5 = _wiggle_panel()
    folds = mk_folds(n=3, td=pd.Timedelta(days=1))
    dec = signals.leg_decisions("LEG-1", m5, eval_end=folds[-1]["end"])
    full = run(dec, m5, folds)
    assert len(full["trades"]) >= 2
    for k in (60, 150, 288, 400, 600, 863):
        part = m5.iloc[:k].reset_index(drop=True)
        dec_p = signals.leg_decisions("LEG-1", part, eval_end=folds[-1]["end"])
        res_p = run(dec_p, part, folds)
        # trade list is a strict prefix of the full run's list
        assert trades_bytes(res_p["trades"]) == trades_bytes(
            full["trades"][:len(res_p["trades"])])
        # equity curve identical on the common bars
        assert np.allclose(res_p["equity"].to_numpy(),
                           full["equity"].to_numpy()[:len(res_p["equity"])])
    assert trades_bytes(full["trades"]) == trades_bytes(run(dec, m5, folds)["trades"])


# ---------------------------------------------------------------------------
# 9. Determinism
# ---------------------------------------------------------------------------

def test_full_determinism_two_runs_identical_bytes():
    m5 = _wiggle_panel()
    folds = mk_folds(n=3, td=pd.Timedelta(days=1))
    dec = signals.leg_decisions("LEG-1", m5, eval_end=folds[-1]["end"])
    r1 = run(dec, m5, folds, funding=pd.DataFrame({
        "ts": pd.DatetimeIndex(["2021-01-04T08:00:00Z"]), "rate": [0.0001]}))
    r2 = run(dec, m5, folds, funding=pd.DataFrame({
        "ts": pd.DatetimeIndex(["2021-01-04T08:00:00Z"]), "rate": [0.0001]}))
    assert trades_bytes(r1["trades"]) == trades_bytes(r2["trades"])
    m1 = engine.metrics_from(r1["trades"], r1["equity"], 10000.0,
                             fold_names=["F1", "F2", "F3"])
    m2 = engine.metrics_from(r2["trades"], r2["equity"], 10000.0,
                             fold_names=["F1", "F2", "F3"])
    assert data.canonical_json(m1) == data.canonical_json(m2)
    assert r1["equity"].equals(r2["equity"])


# ---------------------------------------------------------------------------
# 10. Dry-mode leak scan
# ---------------------------------------------------------------------------

def test_scan_banned_catches_nested_keys():
    assert combo.scan_banned(json.dumps({"net_pnl": 1.0})) == ["pnl"]
    assert combo.scan_banned(json.dumps({"a": {"deep": {"win_rate": 0.5}}})) == ["win_rate"]
    assert combo.scan_banned(json.dumps({"equity_curve": [1]})) == ["equity"]
    assert combo.scan_banned(json.dumps({"ok": 1, "trades": 2})) == []
    # case-insensitive
    assert combo.scan_banned('{"Net_PNL": 2}') == ["pnl"]


def _make_synthetic_worktree(root: Path):
    kdir = root / spec.KLINE_DIR_REL
    kdir.mkdir(parents=True)
    months = [("2020-12", 31, False), ("2021-01", 31, False),
              ("2021-02", 28, True)]
    for tag, days, header in months:
        y, m = tag.split("-")
        start = pd.Timestamp(f"{y}-{m}-01T00:00:00Z")
        n = days * 288
        t = np.arange(n) * 5 * 60
        base = 100.0 + np.sin(np.arange(n) / 2000.0) * 6.0
        spike = np.zeros(n)
        spike[::1500] = 2.5
        close = base + np.cumsum(spike) * 0.1
        rows = pd.DataFrame({
            "open_time": (start.value // 10**6 + t * 1000),
            "open": close, "high": close + 0.5, "low": close - 0.5,
            "close": close, "volume": 1.0, "close_time": 0, "quote_volume": 0.0,
            "count": 0, "taker_buy_base": 0.0, "taker_buy_quote": 0.0,
            "ignore": 0,
        })
        buf = io.BytesIO()
        rows.to_csv(buf, index=False, header=header)
        with zipfile.ZipFile(kdir / f"kl_{tag}.zip", "w") as z:
            z.writestr(f"BTCUSDT-5m-{tag}.csv", buf.getvalue())
    fdir = root / "research/control/bear_opportunity_recon_2026-09/data_a2"
    fdir.mkdir(parents=True)
    fts = pd.date_range("2020-12-01", "2021-02-28", freq="8h", tz="UTC")
    pd.DataFrame({
        "calc_time": (fts.astype("int64") // 10**6),
        "funding_interval_hours": "8",
        "last_funding_rate": 0.0001,
        "ts": fts,
    }).to_parquet(fdir / "funding_events.parquet")
    return root


def test_dry_cli_end_to_end_sanitized(tmp_path):
    from research.btcombo6 import run_btcombo6
    root = _make_synthetic_worktree(tmp_path)
    rc = run_btcombo6.main(["--mode", "dry", "--worktree-root", str(root)])
    assert rc == 0
    artifact = json.loads((root / spec.DRY_DIR_REL / "btcombo6_dry.json")
                          .read_text())
    text = json.dumps(artifact)
    assert combo.scan_banned(text) == []
    assert set(artifact["legs"]) == set(spec.LEG_IDS)
    assert artifact["replay"]["identical"] is True
    assert artifact["leak_scan_ok"] is True
    assert artifact["fold_calendar"]["eval_end"] == "2025-12-29T00:00:00+00:00"
    # staging manifest + cache written; manifest pins every zip
    manifest = json.loads((root / spec.MANIFEST_REL).read_text())
    assert manifest["schema"] == "btcombo6/data_manifest@1"
    assert len(manifest["klines"]) == 3
    assert (root / spec.M5_CACHE_REL).exists()
    # second invocation: cache path, identical core bytes (digests match)
    core1 = {k: v for k, v in artifact.items()
             if k not in ("generated_utc", "replay")}
    rc2 = run_btcombo6.main(["--mode", "dry", "--worktree-root", str(root)])
    assert rc2 == 0
    artifact2 = json.loads((root / spec.DRY_DIR_REL / "btcombo6_dry.json")
                           .read_text())
    core2 = {k: v for k, v in artifact2.items()
             if k not in ("generated_utc", "replay")}
    assert data.canonical_json(core1) == data.canonical_json(core2)
    assert artifact["corpus_digest"] == artifact2["corpus_digest"]


def test_dry_cli_fails_closed_on_banned_key(tmp_path, monkeypatch):
    from research.btcombo6 import run_btcombo6
    bad = {"schema": "x", "legs": {"LEG-1": {"sneaky_net_pnl": 1}}}
    monkeypatch.setattr(combo, "build_dry", lambda root: {
        **bad, "replay_ok": True,
        "banned_key_scan": {"violations": combo.scan_banned(json.dumps(bad))}})
    rc = run_btcombo6.main(["--mode", "dry", "--worktree-root", str(tmp_path)])
    assert rc == 2
    assert not (tmp_path / spec.DRY_DIR_REL / "btcombo6_dry.json").exists()


# ---------------------------------------------------------------------------
# 11. Sealed tail
# ---------------------------------------------------------------------------

def test_sealed_tail_never_evaluated():
    folds = mk_folds(n=2, td=pd.Timedelta(days=1))
    eval_end = folds[-1]["end"]
    m5 = grid_panel(n=700)
    dec = pd.concat([one_decision(m5.loc[5, "ts"]),
                     one_decision(m5.loc[300, "ts"])], ignore_index=True)
    # poison the sealed tail: absurd prices there must not change anything
    res = run(dec, m5, folds)
    m5_poison = m5.copy()
    m5_poison.loc[696:699, ["o", "h", "l", "c"]] = 1e6
    res_poison = run(dec, m5_poison, folds)
    assert trades_bytes(res["trades"]) == trades_bytes(res_poison["trades"])
    for tr in res["trades"]:
        assert tr["fill_ts"] < eval_end
        assert tr["exit_ts"] < eval_end
    assert res["equity"].index.max() < eval_end
    assert len(res["equity"]) == 576  # bars 2021-01-04T00:00 .. 2021-01-05T23:55
    combo._guard_sealed(res, eval_end)  # must not raise
    forged = {"trades": [dict(res["trades"][0],
                              exit_ts=eval_end)],
              "equity": res["equity"], "leg": "LEG-1",
              "open_at_frame_end": None}
    with pytest.raises(AssertionError):
        combo._guard_sealed(forged, eval_end)


# ---------------------------------------------------------------------------
# 12. Cost stress
# ---------------------------------------------------------------------------

def test_cost_stress_scales_fees_only():
    m5 = grid_panel(n=40)
    set_bar(m5, 5, c=100.5)
    dec = one_decision(m5.loc[5, "ts"])
    set_bar(m5, 6, o=100.0)
    set_bar(m5, 10, h=102.0)
    funding = pd.DataFrame({"ts": pd.DatetimeIndex(["2021-01-04T00:40:00Z"]),
                            "rate": [0.0001]})
    folds = mk_folds(n=1, td=pd.Timedelta(days=1))
    r10 = run(dec, m5, folds, stress=1.0, funding=funding)
    r15 = run(dec, m5, folds, stress=1.5, funding=funding)
    t10, t15 = r10["trades"][0], r15["trades"][0]
    for key in ("fill_ts", "exit_ts", "exit_reason"):
        assert t10[key] == t15[key]
    assert t10["fill_px"] == t15["fill_px"]
    assert t10["exit_px"] == t15["exit_px"]
    assert t10["qty"] == t15["qty"]                 # qty is cost-independent
    assert t15["fees"] == pytest.approx(1.5 * t10["fees"], rel=1e-12)
    assert t15["entry_fee"] == pytest.approx(9.0)
    assert t15["funding"] == t10["funding"]         # funding UNSTRESSED
    assert t15["net_pnl"] == pytest.approx(
        t10["gross_pnl"] - 1.5 * t10["fees"] - t10["funding"], rel=1e-12)


# ---------------------------------------------------------------------------
# 13. Metrics, verdict bars, baselines (pure functions)
# ---------------------------------------------------------------------------

def _metrics_fixture():
    trades = [
        {"leg": "L", "fold": "F1", "net_pnl": 100.0, "fill_ts": 0,
         "exit_ts": 0, "fill_px": 0.0, "exit_px": 0.0, "qty": 0.0,
         "gross_pnl": 0.0, "entry_fee": 0.0, "exit_fee": 0.0, "fees": 0.0,
         "funding": 0.0, "exit_reason": "TP", "signal_ts": 0},
        {"leg": "L", "fold": "F1", "net_pnl": -40.0, "fill_ts": 0,
         "exit_ts": 0, "fill_px": 0.0, "exit_px": 0.0, "qty": 0.0,
         "gross_pnl": 0.0, "entry_fee": 0.0, "exit_fee": 0.0, "fees": 0.0,
         "funding": 0.0, "exit_reason": "SL", "signal_ts": 0},
        {"leg": "L", "fold": "F2", "net_pnl": 10.0, "fill_ts": 0,
         "exit_ts": 0, "fill_px": 0.0, "exit_px": 0.0, "qty": 0.0,
         "gross_pnl": 0.0, "entry_fee": 0.0, "exit_fee": 0.0, "fees": 0.0,
         "funding": 0.0, "exit_reason": "TP", "signal_ts": 0},
    ]
    eq = pd.Series([10000.0, 10100.0, 10060.0, 10070.0, 10070.0])
    return trades, eq


def test_metrics_from_hand_case():
    trades, eq = _metrics_fixture()
    m = engine.metrics_from(trades, eq, 10000.0, fold_names=["F1", "F2"])
    assert m["net_pnl"] == 70.0
    assert m["pf"] == pytest.approx(110.0 / 40.0)
    assert m["trade_count"] == 3
    assert m["max_dd_usd"] == 40.0                 # peak 10100 -> trough 10060
    assert m["per_fold"]["F1"] == {"trades": 2, "net_pnl": 60.0}
    assert m["per_fold"]["F2"] == {"trades": 1, "net_pnl": 10.0}
    assert m["net_positive_folds"] == 2


def test_leg_verdict_vacuity_bar():
    m = {"net_pnl": 5.0, "trade_count": 29}
    v = engine.leg_verdict(m)
    assert v["p1_net_positive"] and v["trade_count_only"] and not v["non_vacuous"]
    v2 = engine.leg_verdict({"net_pnl": -1.0, "trade_count": 30})
    assert not v2["p1_net_positive"] and not v2["trade_count_only"]


def _combo_m(**over):
    m = {"start_capital": 60000.0, "net_pnl": 1000.0, "trade_count": 50,
         "pf": 1.3, "pf_lossless": False,
         "per_fold": {f"F{i}": {"trades": 5, "net_pnl": 100.0}
                      for i in range(1, 11)},
         "net_positive_folds": 8, "max_dd_usd": 10000.0, "max_dd_pct": 1 / 6,
         "equity_end": 61000.0, "combo_net_stress_1_5": 500.0}
    m.update(over)
    return m


def test_combo_verdict_all_pass_and_categories():
    legs = [{"net_pnl": 100.0, "trade_count": 40} for _ in range(6)]
    v = engine.combo_verdict(_combo_m(), legs, 900.0)
    assert v["all_pass"] and v["terminal_outcome"] == "COMBO6_SURVIVOR_CANDIDATE"
    # P4 boundary: drawdown exactly 25% of 60000 passes
    v = engine.combo_verdict(_combo_m(max_dd_usd=15000.0), legs, 900.0)
    assert v["p4_max_dd_le_25pct_of_60k"]
    # no leg passes P1 -> REJECT_ALL
    legs_dead = [{"net_pnl": -1.0, "trade_count": 40} for _ in range(6)]
    v = engine.combo_verdict(_combo_m(net_pnl=-100.0, combo_net_stress_1_5=-5.0),
                             legs_dead, 900.0)
    assert v["terminal_outcome"] == "COMBO6_REJECT_ALL"
    # P7 fail -> NO_INCREMENTAL_VALUE
    v = engine.combo_verdict(_combo_m(), legs, 5000.0)
    assert not v["p7_beats_b1_and_mean_leg"]
    assert v["terminal_outcome"] == "COMBO6_NO_INCREMENTAL_VALUE"
    # P5 fail with P1-P4 pass -> STRESS_FAIL
    v = engine.combo_verdict(_combo_m(combo_net_stress_1_5=-1.0), legs, 900.0)
    assert not v["p5_net_positive_stress_1_5"]
    assert v["terminal_outcome"] == "COMBO6_STRESS_FAIL"
    # P4 fail with P1-P3 pass -> RISK_BAR_FAIL
    v = engine.combo_verdict(_combo_m(max_dd_usd=20000.0), legs, 900.0)
    assert v["terminal_outcome"] == "COMBO6_RISK_BAR_FAIL"
    # P6: one fold > 50% of net -> fail
    pf = {f"F{i}": {"trades": 5, "net_pnl": 100.0} for i in range(1, 11)}
    pf["F3"]["net_pnl"] = 900.0
    v = engine.combo_verdict(_combo_m(per_fold=pf), legs, 900.0)
    assert not v["p6_no_fold_over_50pct_of_net"]
    # vacuous P6 when net <= 0
    v = engine.combo_verdict(_combo_m(net_pnl=-100.0,
                                      combo_net_stress_1_5=-1.0), legs, 900.0)
    assert v["p6_no_fold_over_50pct_of_net"]


def test_best_leg_prior_baseline_selection():
    nets = {
        "LEG-1": {"F1": 10.0, "F2": -5.0, "F3": 1.0},
        "LEG-2": {"F1": 20.0, "F2": 2.0, "F3": -9.0},
        "LEG-3": {"F1": 20.0, "F2": 3.0, "F3": 4.0},
    }
    b3 = engine.best_leg_prior_baseline(nets, ["F1", "F2", "F3"])
    assert b3["chosen_per_fold"]["F1"] == "LEG-1"          # fold 0 default
    # after F1: cumulative LEG-1=10, LEG-2=20, LEG-3=20 -> tie -> LEG-2
    assert b3["chosen_per_fold"]["F2"] == "LEG-2"
    # after F1+F2: LEG-1=5, LEG-2=22, LEG-3=23 -> LEG-3
    assert b3["chosen_per_fold"]["F3"] == "LEG-3"
    assert b3["per_fold_nets"] == {"F1": 10.0, "F2": 2.0, "F3": 4.0}
    assert b3["total_net"] == 16.0


def test_b1_always_long_flat_prices_only_fees():
    m5 = grid_panel(n=300)                    # 25h; eval window = day 1
    folds = mk_folds(n=1, td=pd.Timedelta(days=1))
    b1 = engine.always_long_baseline(m5, folds=folds,
                                     eval_end=folds[-1]["end"], stress=1.0)
    assert b1["net_pnl"] == pytest.approx(-(6.0 + 100.0 * 100.0 * CPS1))
    assert b1["fill_px"] == 100.0 and b1["qty"] == 100.0
    # with 1 day of panel and eval_end = day 2: bars >= eval_end absent ->
    # position open at frame end
    m5_short = grid_panel(n=287)
    b1o = engine.always_long_baseline(m5_short, folds=folds,
                                      eval_end=folds[-1]["end"], stress=1.0)
    assert b1o["open"] is True and b1o["net_pnl"] is None


# ---------------------------------------------------------------------------
# 14. RSI + gap census + fold calendar law
# ---------------------------------------------------------------------------

def test_wilder_rsi_hand_and_limits():
    closes = np.array([1.0, 2.0, 1.0, 2.0, 1.0, 2.0])
    r = signals.wilder_rsi(closes, 2)
    assert np.isnan(r[0]) and np.isnan(r[1])
    assert r[2] == pytest.approx(50.0)
    assert r[3] == pytest.approx(75.0)
    assert r[4] == pytest.approx(37.5)
    assert r[5] == pytest.approx(68.75)
    up = signals.wilder_rsi(np.arange(1.0, 30.0), 20)
    assert np.isnan(up[19]) and up[20] == pytest.approx(100.0)  # all gains
    dn = signals.wilder_rsi(np.arange(30.0, 1.0, -1.0), 20)
    assert np.isnan(dn[19]) and dn[20] == pytest.approx(0.0)    # all losses


def test_gap_census():
    m5 = grid_panel(n=100)
    m5 = drop_bars(m5, [10, 11, 12, 50])      # run of 3 + single
    g = data.gap_census(m5, duplicates_dropped=2)
    assert g["expected_5m_slots"] == 100
    assert g["missing_count"] == 4
    assert g["missing_ratio"] == pytest.approx(0.04)
    assert g["max_missing_run"] == 3
    assert g["duplicate_open_time_dropped"] == 2


def test_fold_calendar_erratum_applied():
    # F1 Monday; every fold Monday-aligned; exactly 26 weeks; EVAL_END is
    # 2025-12-29 (plan §4 prose 2025-12-26 was an arithmetic slip — the
    # programmatic calendar is authoritative per A1 amendment 2026-09-29).
    assert spec.F1_START.day_name() == "Monday"
    assert spec.EVAL_END == pd.Timestamp("2025-12-29T00:00:00Z")
    assert spec.EVAL_END.day_name() == "Monday"
    assert spec.EVAL_END == spec.F1_START + pd.Timedelta(weeks=260)
    for f in spec.FOLDS:
        assert f["end"] - f["start"] == pd.Timedelta(weeks=26)
        assert f["start"].day_name() == "Monday"
    assert spec.STRESS_TIERS == (1.0, 1.5, 2.0)
    assert spec.cost_per_side(1.0) == pytest.approx(6.0 / 1e4)
    assert spec.cost_per_side(1.5) == pytest.approx(9.0 / 1e4)


# ---------------------------------------------------------------------------
# 15. Combo assembly smoke (run_tier on a synthetic multi-week panel)
# ---------------------------------------------------------------------------

def test_run_tier_combo_sums_and_reconciliation():
    n = 190 * 288                                  # 190 days of 5m bars
    m5 = grid_panel(n=n)
    w = 100.0 + np.sin(np.arange(n) / 500.0) * 8.0 + np.arange(n) * 1e-4
    for col in ("o", "h", "l", "c"):
        m5[col] = w
    funding = pd.DataFrame({
        "ts": pd.date_range("2020-12-01", periods=700, freq="8h", tz="UTC"),
        "rate": [0.0001] * 700})
    decisions = combo.build_decisions(m5)
    tier = combo.run_tier(m5, funding, decisions, 1.0)
    legs_net = sum(tier["leg_metrics"][l]["net_pnl"] for l in spec.LEG_IDS)
    assert tier["combo_metrics"]["net_pnl"] == pytest.approx(legs_net)
    assert tier["combo_metrics"]["trade_count"] == sum(
        tier["leg_metrics"][l]["trade_count"] for l in spec.LEG_IDS)
    # fold-1 boundary (2021-07-05) is inside the panel -> fold-1 trades close;
    # a position still open at frame end (panel ends before later fold
    # boundaries) stays open: reconcile only the closed legs.
    closed = [l for l in spec.LEG_IDS
              if tier["leg_results"][l]["open_at_frame_end"] is None]
    assert closed, "expected at least one leg to close all positions"
    for leg in closed:
        m = tier["leg_metrics"][leg]
        assert m["equity_end"] == pytest.approx(10000.0 + m["net_pnl"])
    if len(closed) == len(spec.LEG_IDS):
        assert tier["combo_metrics"]["equity_end"] == pytest.approx(
            60000.0 + legs_net)
    # sealed wall: no equity mark at/after EVAL_END, guards already ran
    assert tier["combo_equity"].index.max() < spec.EVAL_END


def test_scored_payloads_and_ledger_end_to_end(tmp_path):
    root = _make_synthetic_worktree(tmp_path)
    payloads = combo.build_scored_payloads(root)
    assert set(payloads) == set(spec.STRESS_TIERS)
    written = combo.write_scored_artifacts(root, payloads)
    for s in spec.STRESS_TIERS:
        assert written[s].exists()
    ledger = combo.update_ledger(root, payloads)
    rows = [json.loads(x) for x in ledger.read_text().splitlines() if x.strip()]
    headers = [r for r in rows if r["schema"] == "btcombo6/trial_ledger@1"]
    outcomes = [r for r in rows if r["row_type"] == "scored_outcome"]
    assert len(headers) == 1
    assert headers[0]["budget_max_scored_cells"] == 12
    assert headers[0]["freeze_commit"] == "PENDING_FREEZE"
    assert len(outcomes) == 7                        # 6 legs + combo
    assert {r["cell"] for r in outcomes} == set(spec.LEG_IDS) | {"COMBO"}
    assert headers[0]["observed_scored_denominator"] == 7
    # determinism: recompute -> identical content digests
    payloads2 = combo.build_scored_payloads(root)
    for s in spec.STRESS_TIERS:
        assert payloads[s]["content_sha256"] == payloads2[s]["content_sha256"]
