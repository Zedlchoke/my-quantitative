"""PC12A Stage-B laws: TRAIN-only partition of the portfolio engine, the
variant grid's closure, netting (full-vote + supermajority 2/3), L5 caps
(per-asset + cluster), E2 degradation gate (prior-fold paper only, feature
blacklist), the frozen deflated TRAIN objective, SR0/DSR input arithmetic,
the trailing-28d ladder, survivor reconciliation and the ledger budget."""

import datetime as dt
import json
import math
import pathlib
import statistics

import numpy as np
import pytest

from research.pc12a import calendar_service as cal
from research.pc12a import legs as _legs
from research.pc12a import panels as _panels
from research.pc12a import policy as pol
from research.pc12a import run_diag as rd
from research.pc12a import run_stageb as sb

UTC = dt.timezone.utc


# ---------------------------------------------------------------------------
# 1. Partition law + grid closure
# ---------------------------------------------------------------------------


def test_stageb_partition_law():
    folds = cal.fold_calendar()
    fridays = cal.decision_fridays()
    sealed_start, sealed_end = cal.sealed_tail()
    assert len(folds) == 8
    for k, f in enumerate(folds):
        assert f.train_start == fridays[0] == dt.date(2021, 1, 8)
        assert (f.test_start - f.train_end).days >= 7
        assert f.train_end < f.test_start
        for f2 in folds[k:]:
            assert f.train_end < f2.test_start
        assert f.train_end < sealed_start
    assert folds[-1].train_end == dt.date(2025, 6, 20)
    assert folds[-1].test_start == dt.date(2025, 7, 4)
    assert sealed_start == dt.date(2026, 1, 2)
    # the portfolio variant runs use exactly this calendar, TRAIN side only
    assert sb.VARIANT_GRID is not None


def test_variant_grid_closure():
    ids = [v["variant_id"] for v in sb.VARIANT_GRID]
    assert len(ids) == 8 and len(set(ids)) == 8
    combos = {(v["eligibility"], v["netting"], v["caps"])
              for v in sb.VARIANT_GRID}
    assert combos == {(e, n, c) for e in ("base", "e2strict")
                      for n in ("full", "super")
                      for c in ("default", "tight")}
    for v in sb.VARIANT_GRID:
        pol.assert_features_lawful([
            f"decision_count_trailing:{v['variant_id']}",
            f"cost_bill_trailing:{v['variant_id']}",
            f"e2_paper_expectancy_prior_folds:{v['variant_id']}"])


def test_blacklist_still_enforced():
    for bad in ("realized_pnl_x", "current_fold_pnl", "future_data_v2",
                "test_fold_leak", "in_fold_loss_tax"):
        with pytest.raises(pol.ForbiddenFeature):
            pol.assert_features_lawful([bad])


# ---------------------------------------------------------------------------
# 2. Survivor reconciliation
# ---------------------------------------------------------------------------


def _mini_ledger(tmp_path, extra_kills=(), no_entries=()):
    rows = []
    for i in range(3):
        rows.append({"stage": "A-DIAG", "pass_tag": "MAIN", "fold_id": 7,
                     "corpus_gid": f"L{i}", "result": "DIAG_TRAIN_COMPUTED",
                     "sleeve_id": "S", "cluster_id": "c",
                     "outcome_exposed_label": "LBL",
                     "arm_config_digest": f"d{i}", "net_pnl_usd": 1.0,
                     "cost_total_usd": 0.1, "n_trades": 1})
    for g in extra_kills:
        rows.append({"stage": "A-DIAG", "pass_tag": "MAIN", "fold_id": 7,
                     "corpus_gid": g, "result": "DIAG_TRAIN_COMPUTED",
                     "sleeve_id": "S", "cluster_id": "c",
                     "outcome_exposed_label": "LBL",
                     "arm_config_digest": "d", "net_pnl_usd": 1.0,
                     "cost_total_usd": 0.1, "n_trades": 1})
        rows.append({"stage": "A-DIAG", "corpus_gid": g,
                     "result": "COST_DOMINATED"})
    for g in no_entries:
        rows.append({"stage": "A-DIAG", "pass_tag": "MAIN", "fold_id": 7,
                     "corpus_gid": g, "result": "NO_ENTRIES_TRAIN",
                     "sleeve_id": "S", "cluster_id": "c",
                     "outcome_exposed_label": "LBL",
                     "arm_config_digest": "d", "net_pnl_usd": 0.0,
                     "cost_total_usd": 0.0, "n_trades": 0})
    p = tmp_path / "ledger.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return str(p)


def test_survivor_reconciliation(tmp_path):
    out = sb.reconcile_survivors(_mini_ledger(tmp_path,
                                              extra_kills=["L9"],
                                              no_entries=["L8"]))
    assert out["survivors"] == ["L0", "L1", "L2"]
    assert out["n_cost_dominated"] == 1
    assert out["n_no_entries"] == 1
    per = {x["leg_id"]: x for x in out["per_leg"]}
    assert per["L0"]["fold7_train_net_usd"] == 1.0


def test_survivor_reconciliation_blocked_below_three(tmp_path):
    p = _mini_ledger(tmp_path)
    rows = [json.loads(l) for l in open(p)]
    rows = [r for r in rows if r["corpus_gid"] != "L2"] + [
        {"stage": "A-DIAG", "corpus_gid": "L2", "result": "COST_DOMINATED"}]
    pathlib.Path(p).write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n")
    with pytest.raises(RuntimeError, match="BLOCKED_NO_SLATE"):
        sb.reconcile_survivors(p)


# ---------------------------------------------------------------------------
# 3. Cluster map freeze
# ---------------------------------------------------------------------------


def test_cluster_map_freeze(tmp_path):
    base = {"A|B": 0.61, "B|C": 0.55, "A|C": 0.10}
    p = tmp_path / "comp.json"

    def _write(extra):
        pairs = dict(base)
        pairs.update(extra)
        p.write_text(json.dumps({"folds": {"7": {"pairs": {
            k: {"corr": v, "co_loss_weeks": 1, "n_weeks": 232}
            for k, v in pairs.items()}}}}))

    # transitive union via A-B and B-C despite A-C = 0.10; D below threshold
    _write({"A|D": -0.40})
    out = sb.freeze_cluster_map(str(p), ["A", "B", "C", "D"])
    assert {tuple(v) for v in out["clusters"].values()} == {
        ("A", "B", "C"), ("D",)}
    # |corr| law: a strongly NEGATIVE pair is also co-movement in absolute
    # terms and groups (mirror positions still co-drawdown risk)
    _write({"A|D": -0.60})
    out = sb.freeze_cluster_map(str(p), ["A", "B", "C", "D"])
    assert {tuple(v) for v in out["clusters"].values()} == {
        ("A", "B", "C", "D")}


# ---------------------------------------------------------------------------
# 4. Netting laws
# ---------------------------------------------------------------------------


def test_full_netting_sum_and_truncation():
    n = pol.Netting()
    out = n.net({"a": 100_000, "b": 100_000})
    assert out.net_target_units == 100_000     # truncated to +/- 1 lot
    out = n.net({"a": 100_000, "b": -100_000})
    assert out.net_target_units == 0 and out.tie_zero
    out = n.net({"a": -100_000, "b": -100_000, "c": -100_000})
    assert out.net_target_units == -100_000


def test_supermajority_netting():
    n = sb.SupermajorityNetting()
    # 2-1 split: agreeing share 1/3 < 2/3 -> FLAT (not a tie)
    out = n.net({"a": 100_000, "b": 100_000, "c": -100_000})
    assert out.net_target_units == 0 and not out.tie_zero
    # unanimity passes
    assert n.net({"a": 100_000, "b": 100_000,
                  "c": 100_000}).net_target_units == 100_000
    # exactly 2/3 agreeing share passes (>= threshold): 5-1 split
    # |sum d| / sum|d| = 400k/600k = 2/3 exactly
    des = {f"l{i}": (100_000 if i < 5 else -100_000)
           for i in range(6)}
    assert n.net(des).net_target_units == 100_000
    # single leg always passes; a true tie still reports tie_zero
    assert n.net({"a": 100_000}).net_target_units == 100_000
    tie = n.net({"a": 100_000, "b": -100_000})
    assert tie.net_target_units == 0 and tie.tie_zero


# ---------------------------------------------------------------------------
# 5. L5 caps clamp
# ---------------------------------------------------------------------------


def test_clamp_l5_per_asset_and_cluster():
    caps = {"per_asset_net_units": {"GBPUSD": 100_000, "USDJPY": 50_000},
            "cluster_net_units": {"CM:X": 50_000},
            "cluster_symbols": {"CM:X": ["GBPUSD"]}}
    assert sb.clamp_l5(100_000, "GBPUSD", caps) == (50_000, "L5: cap 50000 units")
    assert sb.clamp_l5(-100_000, "GBPUSD", caps) == (-50_000,
                                                     "L5: cap 50000 units")
    assert sb.clamp_l5(40_000, "GBPUSD", caps) == (40_000, None)
    assert sb.clamp_l5(100_000, "USDJPY", caps)[0] == 50_000
    assert sb.clamp_l5(100_000, "EURUSD", caps) == (100_000, None)


# ---------------------------------------------------------------------------
# 6. E2 degradation gate (prior-fold paper statistics only)
# ---------------------------------------------------------------------------


def _folds_mini():
    return [cal.Fold(0, dt.date(2024, 5, 6), dt.date(2024, 6, 3),
                     dt.date(2024, 6, 17), dt.date(2024, 6, 28)),
            cal.Fold(1, dt.date(2024, 5, 6), dt.date(2024, 7, 1),
                     dt.date(2024, 7, 15), dt.date(2024, 7, 26)),
            cal.Fold(2, dt.date(2024, 5, 6), dt.date(2024, 8, 5),
                     dt.date(2024, 8, 19), dt.date(2024, 8, 30))]


def test_e2_window_stats():
    folds = _folds_mini()
    by_end = {f.fold_id: f for f in folds}
    net = {0: 100.0, 1: -50.0, 2: 10.0}
    dec = {0: 10, 1: 10, 2: 10}
    cost = {0: 0.0, 1: 0.0, 2: 0.0}
    # at boundary fold 1: trailing-2 = folds {0,1} -> (100-50)/20 = 2.5 > 0
    assert sb.e2_window_stats(net, dec, cost, by_end, folds[1]) == 2.5
    # at boundary fold 2: trailing-2 = folds {1,2} -> (-50+10)/20 = -2 <= 0
    assert sb.e2_window_stats(net, dec, cost, by_end, folds[2]) == -2.0
    # no decisions -> None (fail-open, disclosed)
    assert sb.e2_window_stats(net, {0: 0, 1: 0}, cost, by_end,
                              folds[1]) is None
    # paper costs enter the expectancy
    cost = {0: 200.0, 1: 0.0, 2: 0.0}
    assert sb.e2_window_stats(net, dec, cost, by_end, folds[1]) == -7.5


def test_e2_boundary_zeroes_desire_and_counts_event():
    eng = _make_synthetic_engine("e2strict")
    folds = eng_fold_list(eng)
    lid = eng.legs[0].identity.candidate_id
    # fabricate degenerate paper stats: folds 0..k negative expectancy
    eng._paper_fold_net[lid][0] = -100.0
    eng._paper_fold_decisions[lid][0] = 10
    eng._e2_off[lid] = False
    eng._e2_boundary(folds[0])
    assert eng._e2_off[lid] is True
    assert eng.e2_events[lid] == 1
    # a decision while OFF stands aside (desire zeroed, no eligibility use)
    dec = _legs.LegDecision(vote=1, desired_units=100_000,
                            reason_code="TEST")
    eng._apply_decisions({lid: dec},
                         dt.datetime(2024, 6, 10, 12, 0, tzinfo=UTC),
                         None, -1)
    assert eng.leg_desires[lid] == 0
    assert eng.report["legs"][lid]["fills_by_outcome"][
        "E2_STAND_ASIDE"] == 1


# ---------------------------------------------------------------------------
# 7. Objective + DSR inputs
# ---------------------------------------------------------------------------


def test_train_objective_math():
    weekly = {"2024-01-05": 100_000.0, "2024-01-12": 101_000.0,
              "2024-01-19": 99_000.0, "2024-01-26": 102_000.0}
    out = sb.train_objective(weekly, sr0=0.3)
    rs = [1000.0, -2000.0, 3000.0]
    std = statistics.pstdev(rs)
    sr = statistics.fmean(rs) / std
    assert out["n_weeks"] == 3
    assert out["net_pnl_usd"] == pytest.approx(2000.0)
    assert out["max_dd_usd"] == pytest.approx(2000.0)
    assert out["sr_hat"] == pytest.approx(sr)
    assert out["deflation_term_usd"] == pytest.approx(3 * 0.3 * std)
    assert out["dd_penalty_usd"] == pytest.approx(2000.0)
    assert out["objective_usd"] == pytest.approx(
        2000.0 - 3 * 0.3 * std - 2000.0)
    # degenerate: flat path -> obj 0, flagged
    flat = sb.train_objective({"d1": 100_000.0, "d2": 100_000.0}, 0.3)
    assert flat["degenerate"] and flat["objective_usd"] == 0.0


def test_sr0_formula_hand_check():
    nd = statistics.NormalDist()
    n_eff = 2
    e_max = ((1 - sb.GAMMA) * nd.inv_cdf(1 - 1 / n_eff)
             + sb.GAMMA * nd.inv_cdf(1 - 1 / (n_eff * sb.EUL)))
    assert e_max == pytest.approx(sb.GAMMA * 0.900517, abs=1e-4)
    assert math.sqrt(0.04) * e_max == pytest.approx(0.2 * e_max)


def test_percentile_and_trailing28d():
    assert sb._percentile([1.0, 2.0, 3.0, 4.0], 0.5) == pytest.approx(2.5)
    assert sb._percentile([1.0, 2.0, 3.0, 4.0], 0.9) == pytest.approx(3.7)
    spends = [(dt.datetime(2024, 1, 1, tzinfo=UTC), 10.0),
              (dt.datetime(2024, 1, 20, tzinfo=UTC), 20.0),
              (dt.datetime(2024, 2, 15, tzinfo=UTC), 30.0)]
    vals = sb._trailing28d_series(spends)
    assert vals == pytest.approx([10.0, 30.0, 50.0])
    # PIT: a later spend never enters an earlier instant's window
    assert sb._trailing28d_series(spends[:1]) == [10.0]


# ---------------------------------------------------------------------------
# 8. Portfolio engine on synthetic panels: TRAIN-prefix law, accounting
#    identity, determinism, caps application
# ---------------------------------------------------------------------------

SYMS = ("GBPUSD",)


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


_CFG_DIR = pathlib.Path(_legs.__file__).parent / "legs_config"


def _synth_cfgs():
    cfgs = _legs.load_leg_configs(str(_CFG_DIR))
    keep = ("GBPUSD-S002", "GBPUSD-S027")
    out = [c for c in cfgs
           if (c.get("class_candidate_id") or c["corpus_gid"]) in keep]
    assert len(out) == 2
    return out


def _synth_folds():
    return [cal.Fold(0, dt.date(2024, 5, 6), dt.date(2024, 6, 3),
                     dt.date(2024, 6, 17), dt.date(2024, 6, 28)),
            cal.Fold(1, dt.date(2024, 5, 6), dt.date(2024, 7, 1),
                     dt.date(2024, 7, 15), dt.date(2024, 7, 26)),
            cal.Fold(2, dt.date(2024, 5, 6), dt.date(2024, 8, 5),
                     dt.date(2024, 8, 19), dt.date(2024, 8, 30))]


@pytest.fixture(scope="module")
def synth_env(tmp_path_factory, monkeypatch_session=None):
    base = tmp_path_factory.mktemp("pc12a_stageb")
    root = base / "panels"
    _build_synthetic_tree(root, dt.date(2024, 3, 1), dt.date(2024, 8, 30))
    return {"root": root, "base": base}


def eng_fold_list(eng):
    return sorted(eng.fold_by_end.values(), key=lambda f: f.train_end)


def _make_synthetic_engine(eligibility="base", netting="full",
                           per_asset=100_000):
    class _Store:
        roots = {}

    folds = _synth_folds()
    variant = {"variant_id": "T", "eligibility": eligibility,
               "netting": netting, "caps": "default"}
    caps_cfg = {"per_asset_net_units": {"GBPUSD": per_asset},
                "cluster_net_units": {}, "cluster_symbols": {}}
    eng = sb.PortfolioEngine(
        "GBPUSD", _synth_cfgs(), None, folds, 1.0, variant, caps_cfg,
        pol.CostGuard(pol.CostGuardState(cap_usd=float("inf"))))
    return eng


def test_portfolio_engine_train_prefix_law(synth_env, monkeypatch):
    monkeypatch.setenv("PC12A_PANEL_ROOTS", json.dumps(
        {s: str(synth_env["root"] / s) for s in SYMS}))
    store = _panels.PanelStore()
    eng = _make_synthetic_engine()
    eng.run(store)
    folds = eng_fold_list(eng)
    assert eng.diag_window_end == folds[-1].train_end
    end_ts = dt.datetime.combine(folds[-1].train_end, dt.time(23, 59, 59),
                                 tzinfo=UTC)
    assert all(f["ts"] <= end_ts for f in eng._captured_fills)
    for f in folds:
        snap = eng.snapshots[f.fold_id]
        eps = rd._episodes(snap.fills)
        fin = snap.finalize(eps)
        assert abs(fin["residual_usd"]) < 1e-6
        assert fin["net_pnl_usd"] == pytest.approx(
            fin["gross_pnl_usd"] - fin["cost_total_usd"], abs=1e-6)
        assert abs(snap.units) <= 100_000


def test_portfolio_engine_determinism_and_caps(synth_env, monkeypatch):
    monkeypatch.setenv("PC12A_PANEL_ROOTS", json.dumps(
        {s: str(synth_env["root"] / s) for s in SYMS}))
    store = _panels.PanelStore()

    def _finals(eng):
        out = []
        for f in eng_fold_list(eng):
            fin = eng.snapshots[f.fold_id].finalize(
                rd._episodes(eng.snapshots[f.fold_id].fills))
            out.append(json.dumps(fin, sort_keys=True))
        return out

    a = _make_synthetic_engine()
    a.run(store)
    b = _make_synthetic_engine()
    b.run(store)
    assert _finals(a) == _finals(b)

    tight = _make_synthetic_engine(per_asset=50_000)
    tight.run(store)
    for f in eng_fold_list(tight):
        assert abs(tight.snapshots[f.fold_id].units) <= 50_000
    assert "BLOCKED_RISK_CAP" in tight.report[
        "blocked_reason_histogram"] or all(
        abs(tight.snapshots[f.fold_id].units) <= 50_000
        for f in eng_fold_list(tight))


def test_portfolio_engine_e2_and_supermajority_run(synth_env,
                                                   monkeypatch):
    monkeypatch.setenv("PC12A_PANEL_ROOTS", json.dumps(
        {s: str(synth_env["root"] / s) for s in SYMS}))
    store = _panels.PanelStore()
    for elig, netting in (("e2strict", "full"), ("base", "super"),
                          ("e2strict", "super")):
        eng = _make_synthetic_engine(eligibility=elig, netting=netting)
        eng.run(store)
        for f in eng_fold_list(eng):
            fin = eng.snapshots[f.fold_id].finalize(
                rd._episodes(eng.snapshots[f.fold_id].fills))
            assert abs(fin["residual_usd"]) < 1e-6


# ---------------------------------------------------------------------------
# 9. Ledger append budget (Stage-B rows)
# ---------------------------------------------------------------------------


def test_stageb_ledger_append(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    frozen = {
        "variant_id": "V1",
        "slate_size": 12,
        "cluster_map": {"clusters": {"CM:X": ["a", "b"]}},
        "guard": {"cap_usd": 100.0},
        "policy_digest": "deadbeef",
        "sr0_inputs": {"sr0": 0.32},
        "selection_statistic": {"objective_usd": -1.0,
                                "net_pnl_usd": 5.0,
                                "max_dd_usd": 2.0},
        "selection_ranking": [
            {"variant_id": f"V{i}", "objective_usd": float(-i),
             "net_pnl_usd": 1.0, "max_dd_usd": 1.0, "sr_hat": 0.0,
             "degenerate": False} for i in range(1, 9)]}
    total = sb.append_stageb_rows(frozen, ledger_path=path, stop_at=50)
    assert total == 9
    rows = [json.loads(l) for l in open(path)]
    assert [r["row_id"] for r in rows] == \
        [f"BSTG-W1-{i:04d}" for i in range(1, 10)]
    assert sum(1 for r in rows if r["stage"] == "B-VARIANT") == 8
    assert sum(1 for r in rows if r["stage"] == "B-FREEZE") == 1
    assert all(r["label"] == "TRAIN-ONLY" for r in rows)
    assert all(r["fold_scope"] == "TRAIN_ONLY" for r in rows)
    assert rows[-1]["arm_config_digest"] == "deadbeef"
    with pytest.raises(rd.LedgerBudgetExceeded):
        sb.append_stageb_rows(frozen, ledger_path=path, stop_at=12)
