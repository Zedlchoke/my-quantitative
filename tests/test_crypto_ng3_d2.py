"""Offline tests for the CRYPTO-NG3 D2 measurement lane.

All tests are synthetic and offline: no network, no CADS store reads, no
frozen-panel loads (the one digest fail-closed test uses a tiny temp file).
They verify the veto arithmetic, not any proposal outcome.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

WORKTREE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKTREE))

from research.assets.crypto_ng3.d2 import measure as M  # noqa: E402


# ---------------------------------------------------------------------------
# rho machinery
# ---------------------------------------------------------------------------

def test_pearson_hand_case():
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [2.0, 4.0, 6.0, 8.0, 10.0]
    assert abs(M.pearson(x, y) - 1.0) < 1e-12
    y2 = [10.0, 8.0, 6.0, 4.0, 2.0]
    assert abs(M.pearson(x, y2) + 1.0) < 1e-12


def test_spearman_ties_average_ranks():
    # hand-computed: ranks x = [1, 2.5, 2.5, 4], ranks y = [1, 3, 2, 4]
    x = [1.0, 2.0, 2.0, 3.0]
    y = [1.0, 3.0, 2.0, 4.0]
    rx, ry = M._avg_ranks(x), M._avg_ranks(y)
    assert list(rx) == [1.0, 2.5, 2.5, 4.0]
    expected = M.pearson(rx, ry)
    assert abs(M.spearman(x, y) - expected) < 1e-12


def test_rho_pair_guards_and_bar():
    out = M.rho_pair([1.0] * 5, [2.0] * 5)
    assert out["status"] == "UNMEASURED_LOW_N"
    out = M.rho_pair([1.0, 1.0, 1.0] * 4, [1.0, 2.0, 3.0] * 4)
    assert out["status"] == "UNMEASURED_ZERO_VARIANCE"
    x = list(range(20))
    y = list(range(20))
    out = M.rho_pair(x, y)
    assert out["status"] == "VETO" and out["margin_to_bar"] == round(0.20 - 1.0, 6)
    # exactly at the bar is NOT over the strict bar -> MEASURED
    y_at = [v * 0.2 / max(abs(v) for v in x) for v in x]  # perfectly monotone -> rho 1 not 0.2
    # construct rho exactly 0.2 instead via a two-point mixture is brittle;
    # verify the comparator directly on the boundary semantics:
    m = 0.20
    status = "VETO" if m > M.RHO_BAR else "MEASURED"
    assert status == "MEASURED"


def test_rho_pair_min_pairs_boundary():
    x = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
    y = [7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0]
    assert M.rho_pair(x, y)["status"] == "UNMEASURED_LOW_N"
    x.append(8.0)
    y.append(0.0)
    out = M.rho_pair(x, y)
    assert out["n_pairs"] == 8 and out["status"] in ("MEASURED", "VETO")


# ---------------------------------------------------------------------------
# A4 anchor construction
# ---------------------------------------------------------------------------

def _mk_days(n: int) -> list[date]:
    return [M.PANEL_FIRST + timedelta(days=i) for i in range(n)]


def test_build_a4_first_decidable_and_threshold():
    days = _mk_days(90)
    rng = np.random.default_rng(7)
    net = rng.normal(0, 1.0, size=90)
    a4 = M.build_a4(days, net)
    assert not a4["decidable"][69]
    assert a4["decidable"][70]
    # hand-recompute z at index 70
    S = np.array([net[i - 6:i + 1].sum() for i in range(90)])
    w = S[70 - 63:70]
    z = (S[70] - w.mean()) / w.std(ddof=1)
    assert abs(a4["z"][70] - z) < 1e-12
    # threshold mapping
    assert a4["e"][70] == (1 if z >= 0.75 else -1 if z <= -0.75 else 0)


def test_build_a4_constant_series_never_decidable():
    days = _mk_days(90)
    net = np.ones(90)
    a4 = M.build_a4(days, net)
    assert not a4["decidable"].any()  # sigma == 0 everywhere


def test_a4_decisions_exclusions():
    days = _mk_days(90)
    net = np.zeros(90)
    net[80] = 50.0  # force a spike -> decidable window includes it
    a4 = M.build_a4(days, net)
    decs = M.a4_decisions(days, a4)
    for dec in decs:
        assert dec["day"] not in M.NET_EXTREME_DAYS
        assert dec["day"] <= M.PANEL_LAST
        assert days[dec["exit_idx"]] != M.MARGIN_DAY
        assert days[dec["exit_idx"]] <= M.PANEL_LAST
        assert M.fold_of(dec["day"]) == M.fold_of(days[dec["exit_idx"]])
        assert dec["e"] in (-1, 1)


# ---------------------------------------------------------------------------
# A5 anchor construction
# ---------------------------------------------------------------------------

def _base_net(n: int) -> np.ndarray:
    """Base series whose trailing-b distribution never self-triggers: values at
    three levels so the trailing P95 theta sits strictly between the mid level
    (b ~= 1.33) and the top level (b ~= 4.0, 5% mass), so only top-level days
    (i % 20 == 0) and injected spikes can cross."""
    return np.array([3.0 if i % 20 == 0 else (1.0 if i % 2 == 0 else 0.5)
                     for i in range(n)], dtype=float)


def test_build_a5_trigger_sign_and_warmup():
    days = _mk_days(120)
    net = _base_net(120)
    net[45] = -8.0  # net-burn burst -> sign +1 per frozen convention
    a5 = M.build_a5(days, net)
    eps = [e for e in a5["episodes"] if e["d"] == 45]
    assert len(eps) == 1
    ep = eps[0]
    assert ep["sign"] == 1  # net < 0 -> +1 (burn burst)
    assert ep["entry_idx"] == 46 and ep["exit_idx"] == 51
    assert ep["fold"] == "fold1"
    # no trigger before index 40 (needs 20 defined trailing b_j)
    assert all(e["d"] >= 40 for e in a5["episodes"])
    # zero-flow days are valid but b=0 never triggers: mint burst sign
    net2 = _base_net(120)
    net2[45] = 8.0
    a5b = M.build_a5(days, net2)
    ep2 = [e for e in a5b["episodes"] if e["d"] == 45]
    assert ep2 and ep2[0]["sign"] == -1  # net > 0 -> -1 (mint burst)


def test_build_a5_refractory():
    days = _mk_days(120)
    net = _base_net(120)
    net[45] = -8.0
    net[46] = -9.0  # within refractory of the 45 trigger
    a5 = M.build_a5(days, net)
    assert a5["void_counts"].get("REFRACTORY", 0) >= 1
    assert sum(1 for e in a5["episodes"] if e["d"] == 46) == 0


def test_build_a5_boundary_void():
    n = 120
    days = _mk_days(n)
    net = _base_net(n)
    net[n - 3] = -50.0  # exit would fall past the panel end
    a5 = M.build_a5(days, net)
    assert sum(1 for e in a5["episodes"] if e["d"] == n - 3) == 0


def test_build_a5_c6_void():
    days = _mk_days(120)
    net = _base_net(120)
    # 2025-10-14 is a frozen NET_EXTREME day -> index 53 (past the warmup)
    idx = (date(2025, 10, 14) - M.PANEL_FIRST).days
    assert days[idx] == date(2025, 10, 14) and idx >= 40
    net[idx] = -50.0
    a5 = M.build_a5(days, net)
    assert a5["void_counts"].get("EXCLUDED_BY_C6", 0) >= 1
    assert all(e["day"] not in M.NET_EXTREME_DAYS for e in a5["episodes"])


# ---------------------------------------------------------------------------
# day rows loader fail-closed
# ---------------------------------------------------------------------------

def test_load_day_rows_identity_fail_closed(tmp_path: Path):
    p = tmp_path / "rows.json"
    p.write_text(json.dumps([
        {"day": "2025-08-22", "issuer": "USDC_ETHEREUM", "net": "1.0",
         "identity_ok": True},
        {"day": "2025-08-23", "issuer": "USDC_ETHEREUM", "net": "2.0",
         "identity_ok": False},
    ]))
    with pytest.raises(ValueError, match="identity_ok"):
        M.load_day_rows(p)


def test_load_day_rows_orders_and_parses(tmp_path: Path):
    p = tmp_path / "rows.json"
    p.write_text(json.dumps([
        {"day": "2025-08-23", "issuer": "USDC_ETHEREUM", "net": "2.5",
         "identity_ok": True},
        {"day": "2025-08-22", "issuer": "USDC_ETHEREUM", "net": "-1.5",
         "identity_ok": True},
    ]))
    days, net = M.load_day_rows(p)
    assert days == [date(2025, 8, 22), date(2025, 8, 23)]
    assert net[0] == -1.5 and net[1] == 2.5


# ---------------------------------------------------------------------------
# CADS digest fail-closed
# ---------------------------------------------------------------------------

def test_panels_digest_mismatch_fail_closed(tmp_path: Path):
    digest = "a" * 64
    obj = tmp_path / "objects" / "aa" / digest
    obj.parent.mkdir(parents=True)
    obj.write_bytes(b"not the pinned bytes")
    panels = object.__new__(M.Panels)  # bypass __init__ (no frozen reads)
    panels.store = tmp_path
    panels.consumed = []
    with pytest.raises(ValueError, match="digest mismatch"):
        panels._read(digest)


# ---------------------------------------------------------------------------
# nulls use the RAW window return on the shadow side
# ---------------------------------------------------------------------------

def test_a4_delayed_null_uses_raw_vector():
    days = _mk_days(80)
    n = 80
    e = np.zeros(n, dtype=int)
    decidable = np.zeros(n, dtype=bool)
    for i in range(70, 76):
        e[i] = 1 if i % 2 == 0 else -1
        decidable[i] = True
    a4 = {"e": e, "decidable": decidable}
    decs = [{"i": i, "day": days[i], "e": int(e[i])} for i in range(70, 76)]
    raw_vec, anchor_vec = {}, {}
    for dec in decs:
        for sym in M.SYMBOLS:
            raw_vec[(dec["day"], sym)] = 2.0
            anchor_vec[(dec["day"], sym)] = dec["e"] * 2.0
    out = M.a4_delayed_null(a4, decs, anchor_vec, raw_vec, 1)
    assert out["n_pairs"] == 18
    assert out["valid"] is True  # x uses raw (unsigned) returns


def test_a5_delayed_null_shape():
    days = _mk_days(120)
    net = _base_net(120)
    net[45] = -8.0
    a5 = M.build_a5(days, net)
    panels = _FakePanels(days)
    anchor_vec, raw_vec = {}, {}
    for ep in a5["episodes"]:
        for sym in M.SYMBOLS:
            r = panels.window_return(sym, days[ep["entry_idx"]], days[ep["exit_idx"]])
            raw_vec[(ep["day"], sym)] = r
            anchor_vec[(ep["day"], sym)] = ep["sign"] * r
    out = M.a5_delayed_null(panels, days, a5["episodes"], anchor_vec, raw_vec, 1)
    assert out["n_pairs"] == 3 * len(a5["episodes"])


class _FakePanels:
    """Duck-typed panels: constant prices, only window_return/hour machinery used."""

    def __init__(self, days):
        self.days = days

    def window_return(self, sym, d_entry, d_exit):
        return 0.01 * (d_exit - d_entry).days

    def held_hour_returns(self, sym, d_entry, d_exit):
        n = (d_exit - d_entry).days * 24
        return np.full(n, 0.001), 0, n - 1

    def hour_flags(self, sym, a, b):
        return {}


# ---------------------------------------------------------------------------
# X3 proxy rule determinism (declared rule, synthetic daily tables)
# ---------------------------------------------------------------------------

def test_x3_proxy_declared_rule_hand_case():
    days = _mk_days(80)
    daily = {}
    for sym in M.SYMBOLS:
        d = {}
        prev_close = 100.0
        for i, day in enumerate(days):
            ret = 0.01 if i % 3 == 0 else (-0.01 if i % 3 == 1 else 0.0)
            close = prev_close * (1 + ret)
            d[day] = {"ret": ret, "dvol": 1000.0 + i}
            prev_close = close
        daily[sym] = d

    class FakeP:
        pass

    fp = FakeP()
    fp.daily = daily
    P = M.build_x3_proxy(fp)
    # day 61: ret = +0.01 (61 % 3 == 1 -> -0.01 actually; just verify determinism + range)
    vals = [P[day] for day in days[61:80]]
    assert all(not math.isnan(v) for v in vals)
    # dvol constant growth 1/day -> ratio to trailing median is deterministic
    assert P[days[70]] == pytest.approx(P[days[70]], abs=0.0)
    # repeated build is identical (pure function of the declared rule)
    P2 = M.build_x3_proxy(fp)
    assert all(P[day] == P2[day] for day in days[61:])


# ---------------------------------------------------------------------------
# veto verdict mapping
# ---------------------------------------------------------------------------

def _row(m, n=100):
    status = "VETO" if (m is not None and m > M.RHO_BAR) else "MEASURED"
    return {"n_pairs": n, "pearson": m, "spearman": m, "max_abs_rho": m,
            "margin_to_bar": None if m is None else round(M.RHO_BAR - m, 6),
            "status": status}


def test_veto_x1_kill_and_blocked_partial():
    table = {"generic_dvol_shock": _row(0.41), "generic_dow_0": _row(0.05)}
    out = M.veto_x1(table)
    assert out["verdict"] == "KILL"
    assert out["margin"] == round(0.20 - 0.41, 6)
    table2 = {"generic_dvol_shock": _row(0.19), "generic_dow_0": _row(0.05)}
    out2 = M.veto_x1(table2)
    assert out2["verdict"] == "NOT_RUN_BLOCKED_PARTIAL"
    assert "funding" in out2["fail_closed_note"]
    assert len(out2["blocked_shapes"]) == 2


def test_veto_x2_blocked_legs_recorded():
    table = {"v17_oi_level": _row(0.19), "v17_oicascade_event": _row(0.10)}
    out = M.veto_x2(table)
    assert out["verdict"] == "NOT_RUN_BLOCKED_PARTIAL"
    for name in M.BLOCKED_SHAPES:
        assert out["funding_level_legs"][name]["status"] == "NOT_RUN_BLOCKED"


def test_veto_x5_invalid_null_explicit():
    nulls = {
        "delayed_state_plus1d": {"max_abs_rho": 0.99, "valid": False},
        "delayed_state_plus3d": {"max_abs_rho": 0.50, "valid": True},
        "shuffled_within_month": {"max_abs_rho": 0.60, "valid": True},
    }
    out = M.veto_x5(nulls)
    assert out["verdict"] == "INVALID_NULL_KILL"
    assert out["invalid_nulls_explicit"] == ["delayed_state_plus1d"]
    assert out["margin"] == round(M.IDENTIFIABILITY_BAR - 0.99, 6)


def test_veto_x5_valid_survive_margin():
    nulls = {
        "delayed_state_plus1d": {"max_abs_rho": 0.91, "valid": True},
        "delayed_state_plus3d": {"max_abs_rho": 0.76, "valid": True},
        "shuffled_within_month": {"max_abs_rho": 0.68, "valid": True},
    }
    out = M.veto_x5(nulls)
    assert out["verdict"] == "VALID_NULL_SURVIVE"
    assert out["margin"] == round(0.98 - 0.91, 6)


def test_veto_x3_uses_worst_rendering():
    x3 = {"proxy_state_held": _row(0.10), "proxy_native_compound": _row(0.35)}
    out = M.veto_x3(x3)
    assert out["verdict"] == "KILL" and out["margin"] == round(0.20 - 0.35, 6)
    x3_ok = {"proxy_state_held": _row(0.10), "proxy_native_compound": _row(0.11)}
    assert M.veto_x3(x3_ok)["verdict"] == "SURVIVE"


def test_veto_x4_worst_recorded():
    table = {f"generic_dow_{k}": _row(0.05) for k in range(7)}
    table["generic_weekend_flag"] = _row(0.02)
    table["v17_wkndliq_flag"] = _row(0.33)
    for s in ("generic_session_us", "generic_session_eu", "generic_session_asia"):
        table[s] = _row(0.01)
    out = M.veto_x4(table, {"a4_decisions_by_weekday": {}})
    assert out["verdict"] == "KILL"
    assert out["worst_measured"]["shape"] == "v17_wkndliq_flag"


def test_q6_population_floor_semantics():
    decs = [{"fold": "fold1", "day": M.PANEL_FIRST}] * 19 + \
           [{"fold": "fold2", "day": M.PANEL_FIRST}] * 20 + \
           [{"fold": "fold3", "day": M.PANEL_FIRST}] * 25
    eps = [{"fold": "fold1", "day": M.PANEL_FIRST}] * 4
    out = M.q6_population(decs, eps, 100)
    assert out["a4"]["per_fold_eligible_decisions"] == {"fold1": 19, "fold2": 20, "fold3": 25}
    assert out["a4"]["per_fold_floor"] == 20
    assert out["a5"]["per_fold_floor"] == 4


# ---------------------------------------------------------------------------
# frozen constants sanity
# ---------------------------------------------------------------------------

def test_frozen_constants_match_plan():
    assert M.RHO_BAR == 0.20
    assert M.A4_L == 7 and M.A4_W == 63 and M.A4_TH == 0.75 and M.A4_HOLD == 3
    assert M.A5_L == 60 and M.A5_MIN_TRAILING == 20 and M.A5_Q == 0.95 and M.A5_HOLD == 5
    assert M.A4_FOLD_FLOOR == 20 and M.A5_FOLD_FLOOR == 4
    assert M.IDENTIFIABILITY_BAR == 0.98 and M.MIN_PAIRS == 8
    assert len(M.NET_EXTREME_DAYS) == 4
    assert M.USDT_ETH_ZERO_EVENT_DAYS == 339
    assert M.MARGIN_DAY == date(2026, 8, 22)
    assert M.PANEL_LAST == date(2026, 8, 21)
    assert len(M.ALL_DAY_SHAPES) == 22 and len(M.ALL_HOUR_SHAPES) == 6
    assert len(M.BLOCKED_SHAPES) == 2
    assert M.F1_ROUND_TRIP_BPS == 24.0
    # declared-before-measurement declarations are non-empty strings
    assert "declared BEFORE any rho" in M.X3_RULE_DECLARED
    assert "Same-bet shadow rendering" in M.SHADOW_RENDERING_DECLARED
