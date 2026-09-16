"""STOCKS-NG6 D2 goldens (plans/PLAN_stocks_ng6.md §6/§7, A4 axes 1/2/3/4).

Hand-computed fixtures on synthetic series — no network, no cache, no PnL:
  test_rho_goldens                       Pearson/Spearman + tie-averaged ranks
                                         against hand-computed values.
  test_inventory_hash_pin                the committed inventory hashes to the
                                         constant pinned in the measurement.
  test_inventory_hash_mismatch_refuses   G8: a mutated inventory (or mutated
                                         pinned hash) makes the measurement
                                         REFUSE before touching any data.
  test_event_conditional_vs_cohort_wide  A4 axis 1: a sparse event book's
                                         cohort-wide rho UNDERSTATES the
                                         event-conditional exposure identity
                                         (demonstration fixture, exact values).
  test_bar_and_margin_goldens            the 0.20 R0 bar is immovable: margin
                                         sign flips exactly at veto-firing
                                         |rho|; P-20 self-subsumption 0.98.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-ng6/integration")
_spec = importlib.util.spec_from_file_location(
    "sng6_d2_run", WT / "research/control/stocks_ng6_run/d2/d2_run.py")
d2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(d2)


# ---------------------------------------------------------------- rho goldens

def test_rho_goldens():
    x = np.array([1., 2, 3, 4, 5])
    y = np.array([2., 4, 5, 4, 5])
    # hand: xbar=3, ybar=4, cov=6, sx=sqrt(10), sy=sqrt(6) -> 6/sqrt(60)
    p, n = d2.pearson(x, y)
    assert n == 5
    assert p == pytest.approx(6 / np.sqrt(60), abs=1e-12)
    # hand (ties averaged): y-ranks [1, 2.5, 4.5, 2.5, 4.5]; Pearson of ranks
    # = 7/sqrt(10*9) = 0.7378647873726218 (the 6*Sum d^2 shortcut is NOT valid
    # with ties — the implementation must use Pearson-of-averaged-ranks)
    s, _ = d2.spearman(x, y)
    assert s == pytest.approx(0.7378647873726218, abs=1e-12)
    # no-tie fixture where the shortcut IS exact: Sum d^2 = 20 -> 1 - 120/120
    s2, _ = d2.spearman(np.arange(1., 6), np.array([5., 1, 2, 3, 4]))
    assert s2 == pytest.approx(1 - 6 * 20 / 120, abs=1e-12)
    # tie-averaged ranks golden
    assert d2.rankdata_avg(np.array([1., 2, 2, 3])) == pytest.approx(
        np.array([1., 2.5, 2.5, 4]))
    assert d2.rankdata_avg(np.array([5., 1, 3])) == pytest.approx(np.array([3., 1, 2]))
    # degenerate (zero-variance) input -> None, never a fabricated rho
    assert d2.pearson(np.ones(5), x)[0] is None
    assert d2.spearman(np.ones(5), x)[0] is None


# ---------------------------------------------------------------- inventory pin

def test_inventory_hash_pin():
    raw = (WT / "research/control/stocks_ng6_run/d2/shadow_inventory.json").read_bytes()
    assert d2.sha(raw) == d2.INV_SHA256
    inv = json.loads(raw)
    names = [e["name"] for e in inv["entries"]]
    # contents EXACTLY the plan §6 R0 list (G8: under-enumeration = invalid PASS)
    assert names == [
        "momentum_63s_generic", "momentum_12_1_xsec",
        "reversal_5d_21d_eventconditional", "drawdown_depth_252_eventconditional",
        "dvol_shock_eventconditional", "vol_tercile_and_vol_restricted_event",
        "realized_vol_level", "semivariance_share", "rolling_beta_state",
        "dgs10_level_state", "event_calendar_geometry", "v13_death_event_proximity",
        "ng5_relative_breadth_rotation_state", "dividend_decomposition_divergence",
    ]
    assert inv["bar"].startswith("pooled |rho| > 0.20")
    assert all("construction" in e and "representation" in e and "computed_on" in e
               for e in inv["entries"])


def test_inventory_hash_mismatch_refuses(tmp_path, monkeypatch):
    # (a) loader refuses on a MUTATED file (same name, altered content)
    bad = tmp_path / "shadow_inventory.json"
    good = WT / "research/control/stocks_ng6_run/d2/shadow_inventory.json"
    doc = json.loads(good.read_text())
    doc["bar"] = "pooled |rho| > 0.30 -> R0 veto"  # threshold tamper
    bad.write_text(json.dumps(doc, indent=1) + "\n")
    assert d2.sha(bad.read_bytes()) != d2.INV_SHA256
    monkeypatch.setattr(d2, "INV", bad)
    with pytest.raises(d2.InventoryMismatch):
        d2.load_inventory()
    # (b) a mutated pinned hash refuses BEFORE any lock or data access
    #     (INV is patched to the existing copy; only the pinned constant lies)
    real_out = d2.OUT
    monkeypatch.setattr(d2, "INV_SHA256", "0" * 64)
    monkeypatch.setattr(d2, "OUT", tmp_path / "verdict.json")
    rc = d2.main()
    assert rc == 1
    verdict = json.loads((tmp_path / "verdict.json").read_text())
    assert verdict["verdict"] == "D2_REFUSED_INVENTORY_HASH_MISMATCH"
    assert "G8" in verdict["blocker"] or "committed" in verdict["blocker"]
    monkeypatch.setattr(d2, "OUT", real_out)
    with pytest.raises(d2.InventoryMismatch):
        d2.load_inventory()
    # restore the true constant for any later test in this session
    d2.INV_SHA256 = d2.sha(good.read_bytes())


# --------------------------------------------- event-conditional demonstration

def test_event_conditional_vs_cohort_wide():
    """A4 axis 1: cohort-wide rho understates a sparse event book.

    Construction (exact, no noise inside windows): 20 sparse events in 6000
    name-sessions; book B = 0 except footprints held on [s+1, s+3]; shadow S
    equals B exactly inside event windows [s, s+3] and is seeded noise
    elsewhere. Inside windows Pearson(S, B) = 1 by construction; pooled it
    must be materially smaller — the demonstration that the BINDING
    event-conditional form exists.
    """
    rng = np.random.default_rng(7)
    n = 6000
    B = np.zeros(n)
    S = rng.normal(size=n)
    evmask = np.zeros(n, dtype=bool)
    starts = np.arange(100, 100 + 20 * 290, 290)
    for s in starts:
        evmask[s:s + 4] = True
        B[s + 1:s + 4] = 1.0          # H-style footprint, 0 at decision s
        S[s:s + 4] = B[s:s + 4]       # shadow equals book exactly inside window
    cond = evmask
    cw = d2.rho_record(S, B)
    cond_rec = d2.rho_record(S[cond], B[cond])
    assert cond_rec["pearson"] == pytest.approx(1.0, abs=1e-12)
    assert abs(cw["pearson"]) < 0.20                 # cohort-wide understates
    assert cond_rec["abs_max"] > cw["abs_max"]
    # margins carry the immovable bar (margin is stored rounded to 6 decimals)
    assert cw["margin_to_020"] == pytest.approx(round(0.20 - cw["abs_max"], 6), abs=1e-9)


# ---------------------------------------------------------------- bar goldens

def test_bar_and_margin_goldens():
    # below-bar fixture: hand r = 1/sqrt(17.5*10) = 0.075593 (|rho| < 0.20;
    # rank fixture: y-ranks [3.5,2,6,1,5,3.5], r_s = 4/sqrt(17.5*17) = 0.231755
    # is OVER the bar on the rank side — so use a permutation instead, see below)
    x = np.arange(1., 7)
    y = np.array([3., 2, 5, 1, 4, 3])
    rec = d2.rho_record(x, y)
    # rho_record stores values rounded to 6 decimals — compare the rounded hand value
    assert rec["pearson"] == pytest.approx(round(1 / np.sqrt(175), 6), abs=1e-12)
    # EXACT boundary fixture: y a permutation of 1..6 with Pearson = Spearman
    # = 0.2 EXACTLY (Sum d^2 = 28 -> 1 - 168/210); the bar is strict ('>'),
    # so |rho| = 0.20 does NOT veto and the margin is exactly zero
    yb = np.array([4., 1, 5, 2, 6, 3])
    recb = d2.rho_record(x, yb)
    assert recb["pearson"] == pytest.approx(0.2, abs=1e-12)
    assert recb["spearman"] == pytest.approx(1 - 6 * 28 / 210, abs=1e-12)
    assert recb["abs_max"] <= d2.BAR
    assert recb["margin_to_020"] == 0.0
    # veto-firing fixture: hand r = -2/sqrt(5*4) = -0.447214 (|rho| > 0.20)
    rec2 = d2.rho_record(np.arange(1., 5), np.array([1., -1, 1, -1]))
    assert rec2["pearson"] == pytest.approx(round(-2 / np.sqrt(20), 6), abs=1e-12)
    assert rec2["abs_max"] > d2.BAR
    assert rec2["margin_to_020"] < 0
    # constants are the frozen ones (G9 / P-20)
    assert d2.BAR == 0.20
    assert d2.SELF_SUB_BAR == 0.98
    assert d2.RV_WINDOWS == (20, 60)
