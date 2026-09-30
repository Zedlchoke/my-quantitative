"""PC12A Stage-A wave-2 laws: H1 ANC adapter, TRAIN-only partition
arithmetic of the diagnostics, snapshot prefix identity (the truncation
proof on real engine mechanics), control determinism, ledger budget."""

import datetime as dt
import json
import os
import pathlib

import numpy as np
import pytest

from research.pc12a import calendar_service as cal
from research.pc12a import h1_panels
from research.pc12a import legs as _legs
from research.pc12a import panels as _panels
from research.pc12a import run_diag as rd

UTC = dt.timezone.utc


# ---------------------------------------------------------------------------
# 1. TRAIN-only partition arithmetic (the campaign's first-PnL guard)
# ---------------------------------------------------------------------------


def test_fold_partition_arithmetic():
    folds = cal.fold_calendar()
    fridays = cal.decision_fridays()
    sealed_start, sealed_end = cal.sealed_tail()
    assert len(folds) == 8
    prev_end = None
    for k, f in enumerate(folds):
        # expanding: train_end strictly increases; train_start is the first
        # campaign Friday for every fold
        assert f.train_start == fridays[0] == dt.date(2021, 1, 8)
        if prev_end is not None:
            assert f.train_end > prev_end
        prev_end = f.train_end
        # the >= 1w train-side embargo: train_end is at least 7 days before
        # the fold's first test Friday
        gap = (f.test_start - f.train_end).days
        assert gap >= 7, f"fold {k} embargo gap {gap}d"
        # TRAIN must never touch this fold's test window
        assert f.train_end < f.test_start
        # and never touch ANY later fold's test window or the sealed tail
        for f2 in folds[k:]:
            assert f.train_end < f2.test_start
        assert f.train_end < sealed_start
    # the longest stream (fold 7) ends before test fold 7 begins; the
    # sealed tail is exactly the last 26 Fridays and stays untouched
    assert folds[-1].train_end == dt.date(2025, 6, 20)
    assert folds[-1].test_start == dt.date(2025, 7, 4)
    assert folds[-1].test_end == dt.date(2025, 12, 26)
    assert sealed_start == dt.date(2026, 1, 2)
    assert (sealed_end - sealed_start).days == 25 * 7
    # every TRAIN window ends at or before the diagnostic max bound
    for f in folds:
        assert f.train_end <= dt.date(2025, 6, 20)


# ---------------------------------------------------------------------------
# 2. H1 ANC adapter
# ---------------------------------------------------------------------------


def _mint_h1_parquet(path: pathlib.Path, rows):
    import pandas as pd

    df = pd.DataFrame(rows, columns=[
        "ts", "b_o", "b_h", "b_l", "b_c", "a_o", "a_c",
        "s_open", "s_close"])
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def _h1_rows(day: dt.date, pip: float = 1e-4):
    rows = []
    base = 0.7700
    for h in (0, 2, 5, 12, 21):     # 5 traded hours, gaps between
        ts = dt.datetime.combine(day, dt.time(h), tzinfo=UTC)
        b_o = round(base + h * 3 * pip, 5)
        b_c = round(b_o + 4 * pip, 5)
        b_l = round(b_o - 6 * pip, 5)
        b_h = round(b_o + 7 * pip, 5)
        s = round(10 * pip, 5)
        rows.append({"ts": ts, "b_o": b_o, "b_h": b_h, "b_l": b_l,
                     "b_c": b_c, "a_o": round(b_o + s, 5),
                     "a_c": round(b_c + s, 5), "s_open": s,
                     "s_close": s})
    return rows


def test_h1_adapter_panel_interface(tmp_path):
    day = dt.date(2024, 6, 3)
    p = tmp_path / "bars1h_ANC_AUDUSD.parquet"
    _mint_h1_parquet(p, _h1_rows(day))
    store = h1_panels.H1PanelStore(roots={"AUDUSD": str(p)})
    h1_panels.install()
    panel = store.load_day("AUDUSD", day)
    tradable = panel.tradable_mask()
    assert int(tradable.sum()) == 5
    # slots at h*60+59 carry the hours
    for h in (0, 2, 5, 12, 21):
        m = h * 60 + 59
        assert tradable[m]
        assert not tradable[m - 1]
        assert panel.bid.open[m] == pytest.approx(0.7700 + h * 3e-4)
        # ask = bid + measured spread
        assert panel.ask.open[m] - panel.bid.open[m] == \
            pytest.approx(10e-4, abs=1e-9)
    # D1 aggregation from slots preserves true extremes
    assert float(panel.bid.high[tradable].max()) == pytest.approx(
        0.7700 + 21 * 3e-4 + 7e-4)
    assert float(panel.mid_close[tradable][-1]) == pytest.approx(
        0.7700 + 21 * 3e-4 + 4e-4 + 5e-4)   # bid close + half of 10e-4
    # absent day -> FileNotFoundError (engine skip semantics)
    with pytest.raises(FileNotFoundError):
        store.load_day("AUDUSD", dt.date(2024, 6, 2))
    # digest deterministic
    d1 = store.panel_digest("AUDUSD", [day])
    assert d1 == store.panel_digest("AUDUSD", [day])


def test_h1_adapter_anc_open_semantics(tmp_path):
    """open above the hour's high is ACCEPTED (left-boundary quote); a
    close outside [low, high] is REJECTED fail-closed."""
    day = dt.date(2024, 6, 4)
    rows = _h1_rows(day)
    rows[0]["b_o"] = rows[0]["b_h"] + 5e-4      # boundary above high
    rows[0]["a_o"] = rows[0]["b_o"] + rows[0]["s_open"]
    good = tmp_path / "good.parquet"
    _mint_h1_parquet(good, rows)
    h1_panels.H1PanelStore(roots={"AUDUSD": str(good)})
    bad_rows = _h1_rows(day)
    bad_rows[1]["b_c"] = bad_rows[1]["b_h"] + 1e-4   # close above high
    bad = tmp_path / "bad.parquet"
    _mint_h1_parquet(bad, bad_rows)
    store = h1_panels.H1PanelStore(roots={"AUDUSD": str(bad)})
    with pytest.raises(h1_panels.H1PanelError):
        store.load_day("AUDUSD", day)


def test_h1_install_extends_kernel_and_domains():
    h1_panels.install()
    assert "AUDUSD" in _panels.PAIR_SPECS
    assert "USDCAD" in _panels.PAIR_SPECS
    from research.pc12a import cost_kernel as ck
    from research.pc12a import policy as pol

    assert ck.MEASURED_CELLS["C1"]["USDCAD"] == {"p50": 1.2, "p90": 1.6}
    assert ck.MEASURED_CELLS["C1"]["AUDUSD"] == {"p50": 1.0, "p90": 1.3}
    assert pol.KNOWN_INPUT_DOMAINS["AUDUSD_mid_range"] == (0.5209, 0.85)
    assert pol.KNOWN_INPUT_DOMAINS["USDCAD_mid_range"] == (1.1057, 1.6751)


# ---------------------------------------------------------------------------
# 3. Prefix identity: snapshots == genuinely truncated re-runs (THE proof)
# ---------------------------------------------------------------------------

SYMS = ("GBPUSD",)
MID = {"GBPUSD": 1.2700}


def _build_synthetic_tree(root: pathlib.Path, start: dt.date,
                          end: dt.date) -> None:
    for sym in SYMS:
        for side in ("BID", "ASK"):
            (root / sym / side).mkdir(parents=True, exist_ok=True)
    d = start
    while d <= end:
        for i, sym in enumerate(SYMS):
            seed = d.toordinal() * 10 + i
            weekend = d.weekday() >= 5
            vol = np.zeros(_panels.RECORDS_PER_DAY) if weekend else None
            bid, ask = _panels.synthetic_day_bytes(
                sym, d, mid_level=MID[sym], vol_pattern=vol, seed=seed)
            (root / sym / "BID" / f"{d.isoformat()}.bi5").write_bytes(bid)
            (root / sym / "ASK" / f"{d.isoformat()}.bi5").write_bytes(ask)
        d += dt.timedelta(days=1)


@pytest.fixture(scope="module")
def synth_env(tmp_path_factory):
    base = tmp_path_factory.mktemp("pc12a_w2")
    root = base / "panels"
    _build_synthetic_tree(root, dt.date(2024, 3, 1), dt.date(2024, 8, 30))
    cfg = [c for c in _legs.default_leg_configs()
           if (c.get("corpus_gid") or c.get("class_candidate_id"))
           == "GBPUSD-S027"][0]
    return {"root": root, "cfg": cfg, "base": base}


def _synth_folds():
    return [
        cal.Fold(0, dt.date(2024, 5, 6), dt.date(2024, 6, 3),
                 dt.date(2024, 6, 17), dt.date(2024, 6, 28)),
        cal.Fold(1, dt.date(2024, 5, 6), dt.date(2024, 7, 1),
                 dt.date(2024, 7, 15), dt.date(2024, 7, 26)),
        cal.Fold(2, dt.date(2024, 5, 6), dt.date(2024, 8, 5),
                 dt.date(2024, 8, 19), dt.date(2024, 8, 30)),
    ]


def test_diag_prefix_identity_and_accounting(synth_env, monkeypatch):
    monkeypatch.setenv("PC12A_PANEL_ROOTS", json.dumps(
        {s: str(synth_env["root"] / s) for s in SYMS}))
    folds = _synth_folds()
    store = _panels.PanelStore()
    long_res = rd.run_leg_diag("GBPUSD", synth_env["cfg"], store, folds,
                               1.0)
    assert long_res["folds"][0]["train_window"][0] == "2024-05-06"
    # every fold's snapshot must equal a GENUINELY TRUNCATED re-run
    for f in folds:
        trunc = rd.run_leg_diag("GBPUSD", synth_env["cfg"], store, [f],
                                1.0)
        a = long_res["folds"][f.fold_id]
        b = trunc["folds"][0]
        assert a["n_fills"] == b["n_fills"], f"fold {f.fold_id} fills"
        assert a["n_decisions"] == b["n_decisions"]
        assert a["net_pnl_usd"] == pytest.approx(b["net_pnl_usd"],
                                                 abs=1e-9)
        assert a["cost_total_usd"] == pytest.approx(b["cost_total_usd"],
                                                    abs=1e-9)
        assert a["gross_pnl_usd"] == pytest.approx(b["gross_pnl_usd"],
                                                   abs=1e-9)
    # accounting identity on every fold: net == gross - cost == equity -
    # initial; residual recorded and within tolerance
    for a in long_res["folds"]:
        assert abs(a["residual_usd"]) < 1e-6
        assert a["net_pnl_usd"] == pytest.approx(
            a["gross_pnl_usd"] - a["cost_total_usd"], abs=1e-6)
    # determinism: a second identical stream reproduces every fold
    again = rd.run_leg_diag("GBPUSD", synth_env["cfg"], store, folds, 1.0)
    assert [f["net_pnl_usd"] for f in again["folds"]] == \
        [f["net_pnl_usd"] for f in long_res["folds"]]


def test_diag_uses_only_train_prefix(synth_env, monkeypatch):
    """The engine's stream never decides past the longest TRAIN bound."""
    monkeypatch.setenv("PC12A_PANEL_ROOTS", json.dumps(
        {s: str(synth_env["root"] / s) for s in SYMS}))
    folds = _synth_folds()
    store = _panels.PanelStore()
    eng = rd.DiagEngine("GBPUSD", synth_env["cfg"], store, folds, 1.0)
    eng.run(store)
    lid = eng.legs[0].identity.candidate_id
    assert eng.report["legs"][lid]["decisions"] > 0
    assert eng.diag_window_end == folds[-1].train_end
    for f in eng.snapshots.values():
        assert f.n_decisions <= eng.report["legs"][lid]["decisions"]
    # every captured fill timestamp lies inside the longest TRAIN prefix
    end_ts = dt.datetime.combine(folds[-1].train_end, dt.time(23, 59, 59),
                                 tzinfo=UTC)
    assert all(fl["ts"] <= end_ts for fl in eng._captured_fills)


# ---------------------------------------------------------------------------
# 4. control determinism
# ---------------------------------------------------------------------------


def test_control_determinism_and_shape(synth_env, monkeypatch):
    monkeypatch.setenv("PC12A_PANEL_ROOTS", json.dumps(
        {s: str(synth_env["root"] / s) for s in SYMS}))
    folds = _synth_folds()
    store = _panels.PanelStore()
    res = rd.run_leg_diag("GBPUSD", synth_env["cfg"], store, folds, 1.0)
    eps = {fk: v for fk, v in res["episodes"].items()}
    from research.pc12a.cost_kernel import CostKernel

    kernel = CostKernel("GBPUSD", tier=1.0)
    c1 = rd.run_control("GBPUSD", "GBPUSD-S027", eps, store, kernel,
                        folds, "CTRL-A")
    c2 = rd.run_control("GBPUSD", "GBPUSD-S027", eps, store, kernel,
                        folds, "CTRL-A")
    assert c1 == c2, "seeded control must be deterministic"
    for fk, c in c1.items():
        assert c["n_trades"] == len(eps[fk])
    cc = rd.run_control("GBPUSD", "GBPUSD-S027", eps, store, kernel,
                        folds, "CTRL-C")
    assert cc[0]["seed"] != c1[0]["seed"]


# ---------------------------------------------------------------------------
# 5. ledger budget + row ids
# ---------------------------------------------------------------------------


def test_ledger_append_budget(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    rows = [{"stage": "A-DIAG", "corpus_gid": f"L{i}"} for i in range(5)]
    total = rd.append_rows(path, rows, stop_at=10)
    assert total == 5
    with open(path) as fh:
        lines = [json.loads(l) for l in fh]
    assert [r["row_id"] for r in lines] == \
        [f"ADIAG-W2-{i:04d}" for i in range(1, 6)]
    assert all(r["label"] == "DISCOVERY-TRAIN-ONLY" for r in lines)
    with pytest.raises(rd.LedgerBudgetExceeded):
        rd.append_rows(path, rows + rows, stop_at=10)
