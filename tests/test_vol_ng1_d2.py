"""VOL-NG1 D2 novelty tests (task vol-ng1-d2-novelty).

Hand-computed correlation + frozen-machine assertions on tiny synthetic
series, fail-closed measurement-law checks, committed-panel schema
checks, and the P-12 negative scan (the code commit must contain NO
rho values).  Per the dispatch packet.

No network, no scoring, no PnL/outcome numbers anywhere: decision-
STATE series only (Q-6).
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.assets.vol_ng1 import feasibility as fb            # noqa: E402
from research.control.vol_ng1_run.d2 import d2_novelty as dn     # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
D2_DIR = REPO_ROOT / "research/control/vol_ng1_run/d2"
PANEL_PATH = D2_DIR / "d2_novelty_panel.json"
D1_GATE_PATH = (REPO_ROOT /
                "research/control/vol_ng1_run/d1/d1_gate.json")
P2_GATE_PATH = (REPO_ROOT /
                "research/control/vol_ng1_run/p2_gate.json")
PROPOSALS_DIR = (REPO_ROOT /
                 "research/control/vol_ng1_run/d1/proposals")

#: commit-1 files (P-12: code before numbers)
COMMIT1_FILES = [
    D2_DIR / "d2_novelty.py",
    D2_DIR / "d2_run.py",
    Path(__file__).resolve(),
]
#: the MEASUREMENT code files: these must never embed a numeric rho
#: literal at all (the test file legitimately carries hand-computed
#: SYNTHETIC fixture constants, guarded instead by the float-literal
#: collision scan below).
CODE_FILES = [D2_DIR / "d2_novelty.py", D2_DIR / "d2_run.py"]


def _weekdays(n: int, start: str = "2020-01-06") -> list[str]:
    d0 = date.fromisoformat(start)
    out: list[str] = []
    d = d0
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _ctx(grid, adj=None, index=None, legs=("VXX",)):
    return {
        "grid": grid,
        "instants": grid,
        "adj": adj or {},
        "index": index or {},
        "leg_subset": legs,
        "proxy_leg": fb.PROXY_LEG,
        "proxy_lookback_sessions": fb.PROXY_LOOKBACK_SESSIONS,
        "proxy_annualization": fb.PROXY_ANNUALIZATION,
    }


# --------------------------------------------------------------------------- #
# correlation law: hand-computed values
# --------------------------------------------------------------------------- #
def test_pearson_perfect_and_inverse():
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert dn.pearson(x, [2.0, 4.0, 6.0, 8.0, 10.0]) == pytest.approx(1.0)
    assert dn.pearson(x, [-1.0, -2.0, -3.0, -4.0, -5.0]) == \
        pytest.approx(-1.0)


def test_pearson_hand_computed_known_value():
    # hand computation: x centered = [-4.5..4.5 step 1] (sum sq 82.5);
    # y centered sum sq 82.5; sum(x*yc) = 77.5 -> r = 77.5/82.5
    x = [float(i) for i in range(1, 11)]
    y = [2.0, 1.0, 4.0, 3.0, 6.0, 5.0, 8.0, 7.0, 10.0, 9.0]
    assert dn.pearson(x, y) == pytest.approx(77.5 / 82.5)


def test_spearman_robust_to_outlier_hand_computed():
    # ranks of x and y are identical -> spearman is exactly 1.0, while
    # the raw pearson is pulled off 1 by the outlier: hand computation
    # xc = [-2,-1,0,1,2] (sum sq 10); yc centered on mean 22:
    # [-21,-20,-19,-18,78] (sum sq 7610); sum(xc*yc) = 200
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [1.0, 2.0, 3.0, 4.0, 100.0]
    assert dn.spearman(x, y) == pytest.approx(1.0)
    assert dn.pearson(x, y) == pytest.approx(200.0 / math.sqrt(76100.0))
    assert dn.pearson(x, y) < 0.99


def test_spearman_ties_average_ranks_hand_computed():
    # average ranks x = [1, 2.5, 2.5, 4]; y = [1, 3, 2, 4]
    # r = 4.5 / sqrt(4.5 * 5.0) = sqrt(0.9)
    r = dn.spearman([1.0, 2.0, 2.0, 4.0], [1.0, 3.0, 2.0, 4.0])
    assert r == pytest.approx(math.sqrt(0.9))


def test_zero_variance_is_none_never_coerced():
    assert dn.pearson([1.0, 1.0, 1.0], [1.0, 2.0, 3.0]) is None
    assert dn.spearman([1.0, 2.0, 3.0], [2.0, 2.0, 2.0]) is None
    assert dn.pooled_abs(None, None) is None
    assert dn.pooled_abs(-0.5, None) == 0.5


def test_pooled_law_max_of_abs():
    assert dn.pooled_abs(0.10, -0.19) == pytest.approx(0.19)
    assert dn.pooled_abs(-0.31, 0.05) == pytest.approx(0.31)


# --------------------------------------------------------------------------- #
# frozen decision machines (hand-computed)
# --------------------------------------------------------------------------- #
def test_bucket4_thresholds_hand_computed():
    b = lambda s: dn.bucket4(s, 0.02, 0.05)  # noqa: E731
    assert b(-0.01) == "inverted"
    assert b(0.0) == "flat"
    assert b(0.019) == "flat"
    assert b(0.02) == "mild"
    assert b(0.049) == "mild"
    assert b(0.05) == "steep"


def test_slope_functional_hand_computed():
    # VIX9D == VIX -> S = 0.5*ln(VIX3M/VIX)
    assert dn.slope_state(100.0, 100.0, 112.0) == \
        pytest.approx(0.5 * math.log(1.12))


def test_min_hold_filter_hand_computed():
    grid = _weekdays(8)
    raw = {d: v for d, v in zip(grid, [1.0, 1.0, 0.0, 1.0,
                                       -1.0, -1.0, -1.0, -1.0])}
    got = dn.min_hold_filter(raw, grid, 3)
    assert [got[d] for d in grid] == [1.0, 1.0, 1.0, 1.0,
                                      -1.0, -1.0, -1.0, -1.0]


def test_min_hold_invalid_passthrough():
    grid = _weekdays(4)
    raw = {grid[0]: 1.0, grid[1]: None, grid[2]: -1.0, grid[3]: -1.0}
    got = dn.min_hold_filter(raw, grid, 5)
    assert got[grid[1]] is None          # INVALID refused, not coerced
    assert got[grid[3]] == 1.0           # change not yet adoptable


def test_second_difference_hand_computed():
    grid = _weekdays(4)
    s = {d: v for d, v in zip(grid, [1.0, 3.0, 2.0, 5.0])}
    got = dn.second_difference(s, grid)
    assert got[grid[0]] is None and got[grid[1]] is None
    assert got[grid[2]] == pytest.approx(2.0 - 2 * 3.0 + 1.0)   # -3
    assert got[grid[3]] == pytest.approx(5.0 - 2 * 2.0 + 3.0)   # 4


def test_regime_by_run_latch_hand_computed():
    grid = _weekdays(9)
    dvals = [None, None, 1.0, 1.0, 1.0, -1.0, 1.0, 1.0, 1.0]
    dser = {d: v for d, v in zip(grid, dvals)}
    got = dn.regime_by_run(dser, grid, 3, 0.0)
    expect = [None, None, None, None, 1.0, 0.0, 0.0, 0.0, 1.0]
    assert [got[d] for d in grid] == expect


def test_debounce_latch_hand_computed():
    grid = _weekdays(9)
    raw = dict(zip(grid, [1.0, 1.0, -1.0, 1.0, -1.0, -1.0,
                          0.0, 0.0, 0.0]))
    got = dn.debounce_latch(raw, grid, 2)
    expect = [1.0, 1.0, 1.0, 1.0, 1.0, -1.0, -1.0, 0.0, 0.0]
    assert [got[d] for d in grid] == expect


def test_debounce_invalid_breaks_candidate_run():
    grid = _weekdays(5)
    raw = {grid[0]: 1.0, grid[1]: -1.0, grid[2]: None,
           grid[3]: -1.0, grid[4]: -1.0}
    got = dn.debounce_latch(raw, grid, 2)
    # the INVALID at g2 breaks the first candidate run (consecutive
    # means consecutive-VALID), so -1 adopts on the g3+g4 run
    assert [got[d] for d in grid] == [1.0, 1.0, None, 1.0, -1.0]


def test_expanding_z_hand_computed():
    grid = _weekdays(4)
    s = {d: v for d, v in zip(grid, [1.0, 2.0, 3.0, 4.0])}
    got = dn.expanding_z(s, grid, 2)
    assert got[grid[0]] is None and got[grid[1]] is None
    # t=2: arr [1,2,3]: mean 2, popstd sqrt(2/3)
    assert got[grid[2]] == pytest.approx(1.0 / math.sqrt(2.0 / 3.0))
    # t=3: arr [1,2,3,4]: mean 2.5, popstd sqrt(5/4)
    assert got[grid[3]] == pytest.approx(1.5 / math.sqrt(1.25))


def test_realized_vol_hand_computed():
    grid = _weekdays(3)
    closes = {grid[0]: 100.0, grid[1]: 100.0, grid[2]: 110.0}
    got = dn.realized_vol(closes, grid, 2, 252.0)
    r = math.log(1.1)
    # population std of [0, r] == r/2, annualized x sqrt(252)
    assert got[grid[2]] == pytest.approx((r / 2.0) * math.sqrt(252.0))
    assert got[grid[0]] is None and got[grid[1]] is None


# --------------------------------------------------------------------------- #
# ancestry shadow reconstructions on synthetic fixtures (hand-computed)
# --------------------------------------------------------------------------- #
def test_shadow_v16_fade_hand_computed():
    grid = _weekdays(10)
    closes = dict(zip(grid, [98.0, 99.0, 100.0, 101.0, 102.0,
                             105.0, 103.0, 100.0, 99.0, 98.0]))
    ctx = _ctx(grid, adj={"VXX": closes})
    got = dn.shadow_v16_close_displace_fade(ctx)
    # g5: window [98..102] mean 100 sd sqrt(2) -> z = 5/sqrt(2) >= 1
    assert got[grid[5]] == pytest.approx(dn.SHORT_VOL)
    # g6: z = (103-101.4)/2.0591... = 0.777 -> flat
    assert got[grid[6]] == pytest.approx(0.0)
    # g7: z = (100-102.2)/1.720465 <= -1
    assert got[grid[7]] == pytest.approx(dn.LONG_VOL)
    assert got[grid[8]] == pytest.approx(dn.LONG_VOL)
    assert got[grid[9]] == pytest.approx(dn.LONG_VOL)
    for d in grid[:5]:
        assert got[d] is None


def test_shadow_v17_level_hand_computed():
    grid = _weekdays(3)
    index = {"VIX": {grid[0]: 18.0, grid[1]: 25.0, grid[2]: 31.0}}
    got = dn.shadow_v17_oi_level(_ctx(grid, index=index))
    assert [got[d] for d in grid] == [dn.SHORT_VOL, 0.0, dn.LONG_VOL]


def test_shadow_dvol_shock_hand_computed():
    grid = _weekdays(10)
    vix = [20.0, 21.5, 21.5, 21.5, 21.5, 20.4, 20.4, 20.4, 20.4, 20.4]
    index = {"VIX": dict(zip(grid, vix))}
    got = dn.shadow_dvol_shock(_ctx(grid, index=index))
    expect = [None, dn.LONG_VOL, dn.LONG_VOL, dn.LONG_VOL, 0.0,
              dn.SHORT_VOL, dn.SHORT_VOL, dn.SHORT_VOL, 0.0, 0.0]
    assert [got[d] for d in grid] == expect


def test_shadow_momentum_hand_computed():
    grid = _weekdays(64)
    up = {d: 100.0 + i for i, d in enumerate(grid)}
    got = dn.shadow_momentum_63s(_ctx(grid, adj={"VXX": up}))
    assert got[grid[62]] is None
    assert got[grid[63]] == pytest.approx(dn.LONG_VOL)  # chase: mom > 0
    down = {d: 200.0 - i for i, d in enumerate(grid)}
    got2 = dn.shadow_momentum_63s(_ctx(grid, adj={"VXX": down}))
    assert got2[grid[63]] == pytest.approx(dn.SHORT_VOL)


def test_shadow_dow_tue_hand_computed():
    grid = _weekdays(7)  # starts Monday 2020-01-06
    assert date.fromisoformat(grid[1]).weekday() == 1   # Tuesday slot
    got = dn.shadow_generic_dow_tue(_ctx(grid))
    expect = [0.0, dn.SHORT_VOL, 0.0, 0.0, 0.0, 0.0, dn.SHORT_VOL]
    assert [got[d] for d in grid] == expect


# --------------------------------------------------------------------------- #
# proposal decision-state builders on synthetic fixtures
# --------------------------------------------------------------------------- #
def _a4_index(grid, vix3m_ratios):
    index = {
        "VIX9D": {d: 100.0 for d in grid},
        "VIX": {d: 100.0 for d in grid},
        "VIX3M": {d: 100.0 * r for d, r in zip(grid, vix3m_ratios)},
    }
    return index


def test_a4p1_state_buckets_and_min_hold_hand_computed():
    grid = _weekdays(8)
    ratios = [1.12, 1.12, 1.00, 1.12, 0.98, 0.98, 0.98, 0.98]
    ctx = _ctx(grid, index=_a4_index(grid, ratios))
    ctx["leg_subset"] = dn.PROPOSAL_LEG_SUBSETS["VOLNG1-A4-P1"]
    state, meta = dn.build_a4p1_state(ctx)
    # raw buckets: steep, steep, flat, steep, inverted x4;
    # h_min=5 -> the flat blip never flips, inversion adopts at i=5
    expect = [1.0, 1.0, 1.0, 1.0, 1.0, -1.0, -1.0, -1.0]
    assert [state[d] for d in grid] == expect
    assert meta["bucket_by_date"][grid[2]] == "flat"
    assert meta["bucket_by_date"][grid[4]] == "inverted"


def test_a4p1_missing_close_is_invalid_not_coerced():
    grid = _weekdays(4)
    index = _a4_index(grid, [1.12, 1.12, 1.12, 1.12])
    del index["VIX3M"][grid[2]]
    ctx = _ctx(grid, index=index)
    state, _ = dn.build_a4p1_state(ctx)
    assert state[grid[2]] is None
    assert state[grid[0]] == pytest.approx(dn.SHORT_VOL)


def test_a4p2_state_acceleration_run_hand_computed():
    grid = _weekdays(8)
    # s_t = 0.5*ln(ratio_t); increments of the ratio chosen so that the
    # second difference of s is a constant +0.001 from t=2 on:
    s = [0.000, 0.001, 0.003, 0.006, 0.010, 0.015, 0.021, 0.028]
    ratios = [math.exp(2.0 * v) for v in s]
    ctx = _ctx(grid, index=_a4_index(grid, ratios))
    ctx["leg_subset"] = dn.PROPOSAL_LEG_SUBSETS["VOLNG1-A4-P2"]
    state, meta = dn.build_a4p2_state(ctx)
    expect = [None, None, None, None,
              dn.SHORT_VOL, dn.SHORT_VOL, dn.SHORT_VOL, dn.SHORT_VOL]
    assert [state[d] for d in grid] == expect
    assert meta["d_by_date"][grid[2]] == pytest.approx(0.001)


def test_a5p1_constant_series_invalid_fail_closed():
    grid = _weekdays(300)
    ctx = _ctx(grid, index={"VIX": {d: 20.0 for d in grid}},
               adj={"VXX": {d: 50.0 for d in grid}})
    ctx["leg_subset"] = dn.PROPOSAL_LEG_SUBSETS["VOLNG1-A5-P1"]
    state, _ = dn.build_a5p1_state(ctx)
    # zero-variance history -> z INVALID everywhere -> no state value
    # is ever coerced (Q-11); the correlation layer drops it
    assert all(state[d] is None for d in grid)


def test_state_distribution_counts():
    grid = _weekdays(4)
    series = {grid[0]: 1.0, grid[1]: 1.0, grid[2]: -1.0, grid[3]: None}
    dist = dn.state_distribution(series, grid)
    assert dist == {"1.0": 2, "-1.0": 1}


# --------------------------------------------------------------------------- #
# measurement law: overlap, statuses, verdicts
# --------------------------------------------------------------------------- #
def test_correlate_identical_series_measured():
    grid = _weekdays(250)
    prop = {d: (1.0 if i % 2 == 0 else -1.0) for i, d in enumerate(grid)}
    shadow = dict(prop)
    row = dn.correlate_on_overlap(prop, shadow, grid)
    assert row["status"] == dn.STATUS_MEASURED
    assert row["spearman"] == pytest.approx(1.0)
    assert row["pearson"] == pytest.approx(1.0)
    assert row["pooled_abs_max"] == pytest.approx(1.0)
    assert row["n_used"] == 250 and row["n_invalid_dropped"] == 0


def test_correlate_drops_invalid_pairs_and_counts():
    grid = _weekdays(250)
    prop = {d: float(i % 3 - 1) for i, d in enumerate(grid)}
    shadow = {d: float((i + 1) % 3 - 1) for i, d in enumerate(grid)}
    shadow[grid[0]] = None
    row = dn.correlate_on_overlap(prop, shadow, grid)
    assert row["n_used"] == 249 and row["n_invalid_dropped"] == 1


def test_correlate_insufficient_overlap_fail_closed():
    grid = _weekdays(10)
    prop = {d: 1.0 for d in grid}
    shadow = {d: 1.0 for d in grid}
    row = dn.correlate_on_overlap(prop, shadow, grid)
    assert row["status"] == dn.STATUS_INSUFFICIENT_OVERLAP
    assert row["spearman"] is None and row["pooled_abs_max"] is None


def test_correlate_constant_shadow_is_degenerate_not_absent():
    grid = _weekdays(250)
    prop = {d: float(i % 2) for i, d in enumerate(grid)}
    shadow = {d: 0.0 for d in grid}
    row = dn.correlate_on_overlap(prop, shadow, grid)
    assert row["status"] == dn.STATUS_DEGENERATE_SHADOW
    assert row["pooled_abs_max"] == 0.0


def test_correlate_constant_proposal_is_proposal_degenerate():
    grid = _weekdays(250)
    prop = {d: 1.0 for d in grid}
    shadow = {d: float(i % 2) for i, d in enumerate(grid)}
    row = dn.correlate_on_overlap(prop, shadow, grid)
    assert row["status"] == dn.STATUS_PROPOSAL_DEGENERATE
    assert row["pooled_abs_max"] is None


def test_proposal_verdict_margin_law():
    margin = 0.20
    ok = {"status": dn.STATUS_MEASURED, "pooled_abs_max": 0.20,
          "note": None}
    assert dn.proposal_verdict([ok])["verdict"] == "ELIGIBLE"
    assert dn.proposal_verdict([ok])["margin_to_gate"] == \
        pytest.approx(0.0)
    over = {"status": dn.STATUS_MEASURED, "pooled_abs_max": 0.2000001,
            "note": None}
    out = dn.proposal_verdict([over])
    assert out["verdict"] == "VETO"
    assert out["margin_to_gate"] < 0
    blocked = {"status": dn.STATUS_UNMEASURABLE, "pooled_abs_max": None,
               "note": "lawful reconstruction refused"}
    out2 = dn.proposal_verdict([ok, blocked])
    assert out2["verdict"] == "VETO_PENDING"
    assert out2["veto_reasons"]


# --------------------------------------------------------------------------- #
# committed-artifact identity (independent of the panel)
# --------------------------------------------------------------------------- #
def test_frozen_margin_constant_exact():
    assert dn.FROZEN_DEFAULTS["margin_abs_rho"] == 0.20
    assert dn.SHADOW_IDS == ("v16_close_displace_fade", "v17_oi_level",
                             "dvol_shock", "momentum_63s",
                             "generic_dow_tue")


def test_proposal_files_match_d1_gate_records():
    d1 = json.loads(D1_GATE_PATH.read_text())
    assert len(d1["proposals"]) == 4
    for rec in d1["proposals"]:
        p = REPO_ROOT / rec["path"]
        assert _sha256(p) == rec["sha256"], rec["proposal_id"]
        doc = json.loads(p.read_text())
        shadows = doc["ancestry_risk_statement"]["kill_candidate_shadows"]
        assert sorted(shadows) == sorted(dn.SHADOW_IDS)


def test_a5_structural_limitation_verbatim():
    for name in ("VOLNG1-A5-P1", "VOLNG1-A5-P2"):
        doc = json.loads(
            (PROPOSALS_DIR / f"{name}.json").read_text())
        assert doc["structural_limitation_p2_gate_c8_verbatim"] == \
            fb.A5_LIMITATION_TEXT


# --------------------------------------------------------------------------- #
# committed-panel schema checks (valid only AFTER the results commit;
# fail closed if the panel is absent -- never skip, never PASS-by-
# absence)
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def panel():
    if not PANEL_PATH.is_file():
        pytest.fail("d2_novelty_panel.json not committed yet: panel "
                    "schema checks are fail-closed (run order: "
                    "commit-1 code, run d2_run.py, commit-2 panel)")
    return json.loads(PANEL_PATH.read_text())


def test_panel_identity_and_law(panel):
    assert panel["schema"] == "vol_ng1_run/d2_novelty_panel@1"
    assert panel["task_id"] == "vol-ng1-d2-novelty"
    assert panel["cycle_id"] == "VOL-NG1"
    assert panel["law"]["margin"] == 0.20
    assert "ELIGIBLE" in panel["law"]["margin_law"]
    assert panel["consumed_via_plane"]["network_reads"] == 0
    assert panel["representation_checks"]["matches_p2_census"] is True
    assert panel["representation_checks"]["bookable_instants"] == 1914


def test_panel_freeze_block_matches_module(panel):
    assert panel["frozen_parameter_freeze"]["defaults"] == \
        dn.FROZEN_DEFAULTS
    assert set(panel["frozen_parameter_freeze"]["shadow_mappings"]) == \
        set(dn.SHADOW_IDS)
    assert panel["git"]["head_sha_code_commit"]


def test_panel_covers_all_proposals_and_shadows(panel):
    pids = sorted(e["proposal_id"] for e in panel["proposals"])
    assert pids == ["VOLNG1-A4-P1", "VOLNG1-A4-P2",
                    "VOLNG1-A5-P1", "VOLNG1-A5-P2"]
    for e in panel["proposals"]:
        ids = [s["shadow_id"] for s in e["shadows"]]
        assert sorted(ids) == sorted(dn.SHADOW_IDS)
        assert e["feasibility_renote"]["instants_exist"] is True
        assert e["feasibility_renote"]["matches_p2_census"] is True


def test_panel_verdicts_consistent_with_margin_law(panel):
    margin = panel["law"]["margin"]
    for e in panel["proposals"]:
        pools = [s["pooled_abs_max"] for s in e["shadows"]
                 if s["pooled_abs_max"] is not None]
        expected_pool = max(pools) if pools else None
        assert e["pooled_abs_max"] == pytest.approx(expected_pool)
        assert e["margin_to_gate"] == \
            pytest.approx(margin - expected_pool)
        blocking = [s for s in e["shadows"]
                    if s["status"] in dn.BLOCKING_STATUSES]
        if blocking:
            assert e["verdict"] == "VETO_PENDING"
        elif expected_pool <= margin:
            assert e["verdict"] == "ELIGIBLE"
        else:
            assert e["verdict"] == "VETO"
        for s in e["shadows"]:
            for k in ("spearman", "pearson"):
                v = s[k]
                if v is not None:
                    assert -1.0 <= v <= 1.0
            assert s["n_used"] <= s["n_bookable_instants"]


def test_panel_citations_match_committed_bytes(panel):
    assert panel["artifact_hashes_cited"]["p2_gate_json_sha256"] == \
        _sha256(P2_GATE_PATH)
    assert panel["artifact_hashes_cited"]["d1_gate_json_sha256"] == \
        _sha256(D1_GATE_PATH)
    corp = REPO_ROOT / "research/assets/vol_ng1/corp_actions.py"
    assert panel["artifact_hashes_cited"]["corp_actions_py_sha256"] == \
        _sha256(corp)
    d1 = json.loads(D1_GATE_PATH.read_text())
    rec = {p["proposal_id"]: p["sha256"] for p in d1["proposals"]}
    for e in panel["proposals"]:
        assert e["sha256"] == rec[e["proposal_id"]]


def test_panel_no_outcome_keys():
    def walk(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                # "no_pnl_*" keys are the panel's own compliance
                # declarations (the Q-6 law stated in words), not
                # outcome metrics; every OTHER outcome-pattern key is
                # a violation.
                if re.match(r"no_pnl", str(k), re.IGNORECASE):
                    continue
                assert not re.search(
                    r"expectanc|pnl|sharpe|sortino|calmar|hit_rate|"
                    r"win_rate|drawdown|profit|cumulative_return",
                    str(k), re.IGNORECASE), f"outcome key at {path}/{k}"
                walk(v, f"{path}/{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, f"{path}[{i}]")
    panel_obj = json.loads(PANEL_PATH.read_text())
    walk(panel_obj)


def test_commit1_files_contain_no_rho_values(panel):
    """P-12 negative scan: no float literal in any commit-1 file
    equals a measured correlation value from the committed panel."""
    measured = set()
    for e in panel["proposals"]:
        for k in ("pooled_abs_max", "margin_to_gate"):
            if e.get(k) is not None:
                measured.add(round(float(e[k]), 9))
        for s in e["shadows"]:
            for k in ("spearman", "pearson", "pooled_abs_max",
                      "margin_to_gate"):
                if s.get(k) is not None:
                    measured.add(round(float(s[k]), 9))
    measured -= {0.0, 1.0, -1.0, 0.2, -0.2}
    assert measured, "panel carried no measurable rho values"
    literal_re = re.compile(r"[+-]?\d+\.\d+")
    for path in COMMIT1_FILES:
        text = path.read_text()
        for tok in literal_re.findall(text):
            val = round(float(tok), 9)
            assert val not in measured, (
                f"commit-1 file {path.name} contains literal {tok} "
                "matching a measured rho (P-12 violation)")
    for path in CODE_FILES:
        text = path.read_text()
        bad = re.search(
            r"(spearman|pearson|pooled_abs_max)\"\s*:\s*[+-]?\d", text)
        assert bad is None, (
            f"commit-1 code file {path.name} embeds a numeric rho "
            "literal")


def test_panel_correlations_recomputable_from_stored_sides(panel):
    """The pooled law must hold per shadow: max(|spearman|, |pearson|)."""
    for e in panel["proposals"]:
        for s in e["shadows"]:
            if s["status"] in (dn.STATUS_MEASURED,
                               dn.STATUS_DEGENERATE_SHADOW):
                vals = [abs(s[k]) for k in ("spearman", "pearson")
                        if s[k] is not None]
                if vals:
                    assert s["pooled_abs_max"] == \
                        pytest.approx(max(vals))
                else:
                    assert s["pooled_abs_max"] == 0.0
