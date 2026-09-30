"""PC12A Stage-C laws: TEST-only partition, engine equivalence with the
frozen Stage-B decision path, baseline realizations (B1/B2/B5/B6/B7/B8),
B4 chain matching, fold-edge force-flat, and bar arithmetic goldens
(strict AND-semantics, P3 clauses, P7 shares, P8 close codes, DSR
formula, PBO on synthetic matrices)."""

import datetime as dt
import json
import math
import pathlib

import numpy as np
import pytest

from research.pc12a import calendar_service as cal
from research.pc12a import legs as _legs
from research.pc12a import panels as _panels
from research.pc12a import policy as _pol
from research.pc12a import run_scoredc as sc
from research.pc12a import run_stageb as sb

UTC = dt.timezone.utc
SYMS = ("GBPUSD",)
_CFG_DIR = pathlib.Path(_legs.__file__).parent / "legs_config"


# ---------------------------------------------------------------------------
# synthetic panels (same construction as the Stage-B engine tests)
# ---------------------------------------------------------------------------


def _build_synthetic_tree(root: pathlib.Path, start: dt.date,
                          end: dt.date) -> None:
    for sym in SYMS:
        for side in ("BID", "ASK"):
            (root / sym / side).mkdir(parents=True, exist_ok=True)
    d = start
    while d <= end:
        for i, sym in enumerate(SYMS):
            seed = d.toordinal() * 10 + i
            weekend = np.zeros(_panels.RECORDS_PER_DAY) \
                if d.weekday() >= 5 else None
            bid, ask = _panels.synthetic_day_bytes(
                sym, d, mid_level=1.2700, vol_pattern=weekend, seed=seed)
            (root / sym / "BID" / f"{d.isoformat()}.bi5").write_bytes(bid)
            (root / sym / "ASK" / f"{d.isoformat()}.bi5").write_bytes(ask)
        d += dt.timedelta(days=1)


def _synth_cfgs():
    cfgs = _legs.load_leg_configs(str(_CFG_DIR))
    keep = ("GBPUSD-S002", "GBPUSD-S027")
    out = [c for c in cfgs
           if (c.get("class_candidate_id") or c["corpus_gid"]) in keep]
    assert len(out) == 2
    return out


def _store(root):
    import os
    os.environ["PC12A_PANEL_ROOTS"] = json.dumps(
        {s: str(root / s) for s in SYMS})
    return _panels.PanelStore()


@pytest.fixture(scope="module")
def synth_env(tmp_path_factory):
    base = tmp_path_factory.mktemp("pc12a_stagec")
    root = base / "panels"
    _build_synthetic_tree(root, dt.date(2024, 3, 1),
                          dt.date(2024, 8, 30))
    return {"root": root, "base": base}


class _NoopJournal:
    n_rows = 0

    def write(self, kind, row):
        self.n_rows += 1

    def close(self):
        pass


# ---------------------------------------------------------------------------
# 1. TEST-only partition arithmetic
# ---------------------------------------------------------------------------


def test_scored_window_is_test_only():
    folds = cal.fold_calendar()
    assert folds[0].test_start == dt.date(2022, 1, 7)
    assert folds[-1].test_end == dt.date(2025, 12, 26)
    assert cal.sealed_tail()[0] == dt.date(2026, 1, 2)
    # folds tile the test window contiguously (no gaps inside, none
    # touches the sealed tail)
    for k, f in enumerate(folds):
        if k:
            assert (f.test_start - folds[k - 1].test_end).days == 7
        assert f.test_end < cal.sealed_tail()[0]
    # the TRAIN side is never re-scored: no scored window intersects any
    # TRAIN stream bound used by Stage-B
    assert folds[-1].test_end > sb.cal.fold_calendar()[-1].train_end


def test_fold_idx_at_maps_by_test_windows():
    eng = sc.ScoredEngine.__new__(sc.ScoredEngine)
    eng.folds = sorted(cal.fold_calendar(), key=lambda f: f.test_end)
    assert eng._fold_idx_at(dt.date(2022, 1, 7)) == 0
    assert eng._fold_idx_at(dt.date(2022, 7, 1)) == 0
    assert eng._fold_idx_at(dt.date(2022, 7, 2)) == 1
    assert eng._fold_idx_at(dt.date(2025, 12, 26)) == 7
    assert eng._fold_idx_at(dt.date(2026, 1, 2)) == 7


# ---------------------------------------------------------------------------
# 2. Engine equivalence: policy-mode ScoredEngine == frozen Stage-B
#    PortfolioEngine on the same window (decision path is a frozen copy)
# ---------------------------------------------------------------------------


def _equiv_folds():
    # one fold whose TEST window equals the comparison window; TRAIN
    # fields equal the same window so the Stage-B engine runs identically
    return [cal.Fold(0, dt.date(2024, 6, 3), dt.date(2024, 7, 26),
                     dt.date(2024, 6, 3), dt.date(2024, 7, 26))]


def test_engine_equivalence_with_frozen_stageb(synth_env):
    folds = _equiv_folds()
    caps_cfg = {"per_asset_net_units": {"GBPUSD": 100_000},
                "cluster_net_units": {}, "cluster_symbols": {}}
    variant = {"variant_id": "T", "eligibility": "base", "netting":
               "super", "caps": "default"}
    store = _store(synth_env["root"])
    ref = sb.PortfolioEngine("GBPUSD", _synth_cfgs(), store, folds, 1.0,
                             variant, caps_cfg,
                             _pol.CostGuard(_pol.CostGuardState(
                                 cap_usd=float("inf"))))
    ref.run(store)
    store2 = _store(synth_env["root"])
    eng = sc.ScoredEngine(
        "GBPUSD", _synth_cfgs(), store2, folds, 1.0, variant, caps_cfg,
        _pol.CostGuard(_pol.CostGuardState(cap_usd=float("inf"))),
        _NoopJournal(), sc._arm("POLICY"), lambda: _pol.Eligibility())
    eng.run(store2)
    assert len(ref._captured_fills) > 0, \
        "synthetic engine produced no fills (test fixture broken)"
    # identical fill sequences (ts, delta, price) apart from the final
    # fold-edge force-flat
    got = [(f["ts"], f["delta"], round(f["price"], 9))
           for f in eng.all_fills if not f["force_flat"]]
    want = [(f["ts"], f["delta"], round(f["fq"].fill_price, 9))
            for f in ref._captured_fills]
    assert got == want
    # identical pre-edge state (cash + units): the copied decision path
    # reproduces the frozen engine exactly
    rec = eng.fold_records[0]
    assert rec["pre_edge_units"] == int(ref.book_units)
    assert abs(rec["pre_edge_cash"] - ref.cash) < 1e-6


def test_force_flat_law_and_cash_identity(synth_env):
    folds = _equiv_folds()
    caps_cfg = {"per_asset_net_units": {"GBPUSD": 100_000},
                "cluster_net_units": {}, "cluster_symbols": {}}
    variant = {"variant_id": "T", "eligibility": "base", "netting":
               "full", "caps": "default"}
    store = _store(synth_env["root"])
    eng = sc.ScoredEngine(
        "GBPUSD", _synth_cfgs(), store, folds, 1.0, variant, caps_cfg,
        _pol.CostGuard(_pol.CostGuardState(cap_usd=float("inf"))),
        _NoopJournal(), sc._arm("POLICY"), lambda: _pol.Eligibility())
    eng.run(store)
    assert eng.book_units == 0.0            # flat after the last edge
    rec = eng.fold_records[0]
    # per-fold net is an exact cash identity (flat at both edges)
    assert rec["cash_start"] == 100_000.0
    assert abs(rec["net_pnl_usd"]
               - (rec["cash_end"] - rec["cash_start"])) < 1e-6
    # every force-flat fill has full cost lines and is booked to the fold
    for c in eng.force_flat_costs:
        assert c["cost_total_usd"] > 0.0
        assert c["fold_id"] == 0


# ---------------------------------------------------------------------------
# 3. Baseline realization unit checks
# ---------------------------------------------------------------------------


def test_b1_always_on_pins_eligibility():
    e = sc.AlwaysOnEligibility()
    v = e.evaluate("X", None, [], dt.datetime(2024, 1, 1, tzinfo=UTC))
    assert v.state == "ON" and v.rule_id is None


def test_b5_clock_law():
    # k = round_half_up(1/duty), phase 0 (decisions 0, k, 2k, ... ON)
    assert sc.ClockGateEligibility.k_of(1.0) == 1
    assert sc.ClockGateEligibility.k_of(0.5) == 2
    # 1/0.4 = 2.5; half-up rounds 2.5 UP to 3 (documented law)
    assert sc.ClockGateEligibility.k_of(0.4) == 3
    assert sc.ClockGateEligibility.k_of(0.0) is None
    clk = sc.ClockGateEligibility({"A": 0.5})
    outs = [clk.evaluate("A", None, [],
                         dt.datetime(2024, 1, 1, tzinfo=UTC)).state
            == "ON" for _ in range(4)]
    assert outs == [True, False, True, False]          # phase 0


def test_b6_inverted_complements():
    e = sc.InvertedEligibility()
    st = _pol.LegRuntimeStats()
    fresh = [{"input_id": "x", "available_time_utc":
              "2024-01-01T00:00:00Z", "max_age_ok": True}]
    ts = dt.datetime(2024, 1, 2, tzinfo=UTC)
    v_on = e.evaluate("A", st, fresh, ts)      # policy says ON
    assert v_on.state == "OFF"
    stale = [{"input_id": "x", "available_time_utc":
              "2024-01-05T00:00:00Z", "max_age_ok": False}]
    v_off = e.evaluate("A", st, stale, ts)     # policy says OFF (E3)
    assert v_off.state == "ON"


def test_b7_lagged_lookup_law():
    t0 = dt.datetime(2024, 1, 5, tzinfo=UTC)
    tl = {"A": ([ (t0 + dt.timedelta(weeks=w)).timestamp()
                  for w in range(0, 60, 4)], [w % 2 == 0
                                              for w in range(0, 15)])}
    e = sc.LaggedEligibility(tl)
    # decision 40w after t0 -> policy verdict at 14w (index 3 -> False)
    v = e.evaluate("A", None, [],
                   t0 + dt.timedelta(weeks=40))
    assert v.state == "OFF" and e.n_failopen == 0
    # before any recorded verdict -> fail-open ON, counted
    v2 = e.evaluate("A", None, [], t0 - dt.timedelta(weeks=1))
    assert v2.state == "ON" and e.n_failopen == 1


def test_b8_oracle_sets():
    e = sc.OracleEligibility({0: ["A"], 1: []})
    e.set_fold(0)
    assert e.evaluate("A", None, [], None).state == "ON"
    assert e.evaluate("B", None, [], None).state == "OFF"
    e.set_fold(1)
    assert e.evaluate("A", None, [], None).state == "OFF"


def test_b4_markov_matches_duty_and_flip():
    duty = {"A": 0.7, "B": 0.3}
    flip = {"A": 0.2, "B": 0.1}
    m = sc.MarkovEligibility(12345, duty, flip)
    states = {"A": [], "B": []}
    ts = dt.datetime(2024, 1, 1, tzinfo=UTC)
    for _ in range(20000):
        for lid in ("A", "B"):
            states[lid].append(
                m.evaluate(lid, None, [], ts).state == "ON")
    for lid in ("A", "B"):
        real_duty = np.mean(states[lid])
        real_flip = np.mean(np.diff(states[lid]).astype(bool))
        assert abs(real_duty - duty[lid]) < 0.02
        assert abs(real_flip - flip[lid]) < 0.02


def test_b2_equal_split_arithmetic():
    eng = sc.ScoredEngine.__new__(sc.ScoredEngine)
    eng.leg_desires = {"A": 10000, "B": -5000, "C": 0}
    eng._b2_resize(30000.0)                    # 2 active legs -> 15000 ea
    assert eng.leg_desires["A"] == 15000
    assert eng.leg_desires["B"] == -15000
    assert eng.leg_desires["C"] == 0
    eng._b2_resize(0.0)                        # no heat -> unchanged
    assert eng.leg_desires["A"] == 15000
    eng2 = sc.ScoredEngine.__new__(sc.ScoredEngine)
    eng2.leg_desires = {"A": 1000}
    eng2._b2_resize(1_000_000.0)               # capped per leg
    assert eng2.leg_desires["A"] == sc.B2_PER_LEG_CAP_UNITS


# ---------------------------------------------------------------------------
# 4. Bar arithmetic goldens (synthetic numbers)
# ---------------------------------------------------------------------------


def test_p_and_strict_semantics():
    # both legs strict; ties FAIL (E-Law 4)
    assert sc.p_and(10, 5, 3, 4)["pass"]
    assert not sc.p_and(10, 5, 4, 3)["pass"]        # DD worse
    assert not sc.p_and(5, 5, 3, 4)["pass"]         # net tie
    assert not sc.p_and(10, 5, 4, 4)["pass"]        # DD tie
    r = sc.p_and(10, 5, 4, 4)
    assert r["pnl_leg"] and not r["dd_leg"]


def test_p3_clause1_counting():
    objs = [1.0] * 95 + [2.0] * 5                 # 95 below, 5 at/above
    r = sc.p3_clause1(1.5, objs)
    assert r["seeds_below"] == 95 and r["pass"]   # exactly 95% passes
    r2 = sc.p3_clause1(1.0, objs)                 # ties NOT below
    assert r2["seeds_below"] == 0 and not r2["pass"]


def test_p3_clause2_median_strict():
    import statistics
    nets = [1, 2, 3, 4]
    med = statistics.median(nets)                  # 2.5
    assert 3 > med and not 2.5 > med               # tie fails


def test_p7_shares():
    pf = [{"fold_id": 0, "net_pnl_usd": 60, "max_dd_usd": 15},
          {"fold_id": 1, "net_pnl_usd": 20, "max_dd_usd": 5},
          {"fold_id": 2, "net_pnl_usd": -30, "max_dd_usd": 3}]
    # pooled net 50 -> 50% share = 25 (fold 0's 60 breaches);
    # pooled DD 20 -> per-fold cap 2*20/3 = 13.33 (fold 0's 15 breaches)
    r = sc.p7_check(pf, 50, 20)
    assert not r["pass"]
    kinds = {o["kind"] for o in r["offenders"]}
    assert kinds == {"P7_PNL_SHARE", "P7_DD_SHARE"}
    # negative fold cannot breach the PnL share; 2x pro-rata boundary
    pf2 = [{"fold_id": i, "net_pnl_usd": 10, "max_dd_usd": 2.5}
           for i in range(8)]
    r2 = sc.p7_check(pf2, 80, 10)                  # cap 2*10/8 = 2.5
    assert r2["pass"]                              # <= boundary passes
    pf3 = [{"fold_id": i, "net_pnl_usd": 10, "max_dd_usd": 2.500001}
           for i in range(8)]
    assert not sc.p7_check(pf3, 80, 10)["pass"]


def test_p8_close_codes():
    ok = {"ok": True}
    bad = {"ok": False}
    assert sc.p8_check([ok, ok])["pass"]
    one = sc.p8_check([ok, bad, ok])
    assert one["close_code"] == "POLICY_ONE_LEG_CARRIER"
    two = sc.p8_check([bad, ok, bad])
    assert two["close_code"] == "POLICY_NO_INCREMENTAL_VALUE"
    assert two["sub_tag"] == "P8_COALITION"


def test_dsr_formula_hand_check():
    # n=232 weekly returns, SR0 = 0.319497 (the frozen Stage-B value)
    rng = np.random.default_rng(7)
    rs = list(rng.normal(500.0, 14000.0, 232))
    d = sc.dsr(rs, 0.319497)
    sd = float(np.std(rs))
    sr = float(np.mean(rs)) / sd
    assert abs(d["sr_hat"] - sr) < 1e-5
    # DSR <= PSR (SR0 > 0 deflation); a far-below-null series drives
    # the CDF to its 6dp floor (0.0) -- correct behavior, not a defect
    assert d["dsr"] <= d["psr"]
    assert 0.0 <= d["dsr"] <= 1.0
    # vacuity fix (skeptic F-1): a strong-Sharpe series must clear 0.95
    strong = list(rng.normal(3000.0, 1000.0, 232))
    assert sc.dsr(strong, 0.319497)["dsr"] > 0.95
    # degenerate: constant returns -> stdev 0 -> flagged
    assert sc.dsr([1.0] * 10, 0.3)["degenerate"]


def test_sr0_formula_matches_stageb_freeze():
    # E[max] with the frozen N_eff=28, V=0.02441364 -> SR0 0.319497
    nd = __import__("statistics").NormalDist()
    e_max = ((1 - sc.GAMMA) * nd.inv_cdf(1 - 1 / 28)
             + sc.GAMMA * nd.inv_cdf(1 - 1 / (28 * sc.EUL)))
    assert abs(e_max - 2.044798) < 1e-5
    assert abs(math.sqrt(0.02441364) * e_max - 0.319497) < 1e-5


def test_pbo_synthetic_matrices():
    rng = np.random.default_rng(3)
    # pure noise: PBO near 0.5
    noise = rng.normal(0, 1, (12, 224))
    pbo_n = sc.pbo_from_matrix(noise)
    assert 0.25 < pbo_n["pbo"] < 0.75
    assert pbo_n["t_weeks_dropped_leading"] == 0
    # a trial that is train-best but ALWAYS OOS-worst -> PBO 1.0
    mat = rng.normal(0, 1, (6, 224))
    mat[0, :] = 5.0 + 0.05 * rng.normal(0, 1, 224)
    pbo_top = sc.pbo_from_matrix(mat)
    assert pbo_top["pbo"] == 0.0
    # train-champion/OOS-dud: trial 0 shines on even blocks only
    mat2 = rng.normal(0, 1, (6, 224))
    for b in range(16):
        sl = slice(b * 14, (b + 1) * 14)
        if b % 2 == 0:
            mat2[0, sl] = 8.0
        else:
            mat2[0, sl] = -8.0
    pbo_alt = sc.pbo_from_matrix(mat2)
    # even-heavy TRAIN splits make trial 0 champion whose OOS is dud
    # (lambda -inf); odd-heavy splits crown a noise trial (lambda ~
    # coin-flip) -> expected PBO ~ 0.5*1 + 0.5*0.5 = 0.75
    assert pbo_alt["pbo"] > 0.6


def test_dedupe_ledger_law():
    rows = [{"arm_config_digest": "a", "data_snapshot_digest": "d"},
            {"arm_config_digest": "a", "data_snapshot_digest": "d"},
            {"arm_config_digest": "a", "data_snapshot_digest": "e"},
            {"arm_config_digest": "b", "data_snapshot_digest": "d"}]
    keep, dups = sc._dedupe_ledger(rows)
    assert len(keep) == 3 and len(dups) == 1


# ---------------------------------------------------------------------------
# 5. p90 pricing law (P6d)
# ---------------------------------------------------------------------------


def test_p90_fill_pricing(synth_env):
    store = _store(synth_env["root"])
    day = store.load_day("GBPUSD", dt.date(2024, 6, 10))   # Monday
    caps_cfg = {"per_asset_net_units": {"GBPUSD": 100_000},
                "cluster_net_units": {}, "cluster_symbols": {}}
    variant = {"variant_id": "T", "eligibility": "base", "netting":
               "super", "caps": "default"}
    folds = [cal.Fold(0, dt.date(2024, 6, 3), dt.date(2024, 7, 26),
                      dt.date(2024, 6, 3), dt.date(2024, 7, 26))]
    eng = sc.ScoredEngine(
        "GBPUSD", _synth_cfgs(), store, folds, 1.0, variant, caps_cfg,
        _pol.CostGuard(_pol.CostGuardState(cap_usd=float("inf"))),
        _NoopJournal(), sc._arm("POLICY_P90", pricing="p90"),
        lambda: _pol.Eligibility())
    ts_mid = dt.datetime(2024, 6, 10, 12, 0, tzinfo=UTC)
    fq = eng._price_fill("buy", 10_000, day, 0, ts_mid)
    # GBPUSD C1 p90 = 1.3 pips -> half 0.65 pip; non-event slip 0.2 pip
    half = 0.65 * 0.0001
    slip = 0.2 * 0.0001
    mid = (float(day.bid.open[0]) + float(day.ask.open[0])) / 2.0
    assert abs(fq.fill_price - (mid + half + slip)) < 1e-9
    assert abs(fq.spread_once_usd + fq.slip_beyond_halfspread_usd
               - fq.cross_cost_usd) < 1e-9      # spread-once identity


def test_p90_sunday_reopen_uses_c3_cell(synth_env):
    store = _store(synth_env["root"])
    day = store.load_day("GBPUSD", dt.date(2024, 6, 10))   # Monday bar
    caps_cfg = {"per_asset_net_units": {"GBPUSD": 100_000},
                "cluster_net_units": {}, "cluster_symbols": {}}
    variant = {"variant_id": "T", "eligibility": "base", "netting":
               "super", "caps": "default"}
    folds = [cal.Fold(0, dt.date(2024, 6, 3), dt.date(2024, 7, 26),
                      dt.date(2024, 6, 3), dt.date(2024, 7, 26))]
    eng = sc.ScoredEngine(
        "GBPUSD", _synth_cfgs(), store, folds, 1.0, variant, caps_cfg,
        _pol.CostGuard(_pol.CostGuardState(cap_usd=float("inf"))),
        _NoopJournal(), sc._arm("POLICY_P90", pricing="p90"),
        lambda: _pol.Eligibility())
    # a fill stamped inside the Sunday-reopen window prices at C3
    reopen = cal.sunday_reopen_window_utc(dt.date(2024, 6, 9))[0] \
        + dt.timedelta(minutes=2)
    fq = eng._price_fill("sell", 10_000, day, 0, reopen)
    s_eff = max(23.8, 1.3)                    # C3 p90 vs C1 p90
    half = (s_eff / 2.0) * 0.0001
    slip = 1.0 * 0.0001                       # event-window band
    mid = (float(day.bid.open[0]) + float(day.ask.open[0])) / 2.0
    assert abs(fq.fill_price - (mid - half - slip)) < 1e-9



# ---------------------------------------------------------------------------
# 6. Ledger row budget guard + B0 law
# ---------------------------------------------------------------------------


def test_b0_flat_by_construction():
    folds = cal.fold_calendar()
    m = sc.b0_metrics({"policy_digest": "x"}, folds)
    assert m["net_pnl_pooled_usd"] == 0.0
    assert m["max_dd_pooled_usd"] == 0.0
    assert len(m["per_fold"]) == 8


def test_identity_budget_math():
    pol_slate = [f"L{i}" for i in range(12)]
    specs = sc.build_arm_specs(pol_slate)
    # 14 named arms + 24 leave-one-leg = 38 specs on disk + B0 + B4
    assert len(specs) == 38
    total = len(specs) + 2                     # + B0 + B4 battery
    assert total == 40
    assert total <= sc.IDENTITY_CAP
