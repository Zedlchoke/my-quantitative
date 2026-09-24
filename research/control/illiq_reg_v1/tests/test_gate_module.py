"""M0 tests — frozen gate module on hand fixtures (offline, no catalog IO).

Hand-computed fixtures per CLAUDE.md 16.2: golden values, hysteresis
boundaries, no-lookahead mutation, deterministic double generation,
fail-closed empties. Production constants are never re-derived here; they
are pinned to plan SS3.
"""
import datetime as dt
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import gate_module as gm  # noqa: E402


def _dates(*iso):
    return [dt.date.fromisoformat(x) for x in iso]


# --- constants pinned ---------------------------------------------------------

def test_constants_match_plan_ss3():
    assert gm.BAND_ON_S90 == 0.021317
    assert gm.BAND_OFF_S90 == 0.057702
    assert gm.VOL_FLOOR == 0.328930
    assert gm.VOL_OFF == 0.296037
    assert abs(gm.VOL_OFF - gm.VOL_FLOOR * 0.90) < 1e-9
    assert gm.FALSIFICATION_NET_BAR == -0.2947
    assert gm.FALSIFICATION_MDD_BAR == 0.4372
    assert gm.RANDOM_GATE_N == 200
    assert gm.RANDOM_GATE_MIN_RUN == 4
    assert gm.INITIAL_STATE is True


def test_seed_deterministic():
    assert gm.seed_from_cycle_id() == gm.seed_from_cycle_id("ILLIQ-REG-V1")
    assert gm.seed_from_cycle_id("ILLIQ-REG-V1") != gm.seed_from_cycle_id("OTHER")


# --- PIT daily DV share -------------------------------------------------------

def test_daily_dv_share_golden_and_listing_age():
    d = _dates("2024-01-01", "2024-01-02", "2024-01-03")
    # BTC/AAA listed long before the fixture days; NEWUSDT first seen d[1]
    first_day = {"BTCUSDT": dt.date(2023, 1, 1), "AAAUSDT": dt.date(2023, 1, 1),
                 "NEWUSDT": d[1]}
    dv = {
        (d[0], "BTCUSDT"): 100.0, (d[0], "AAAUSDT"): 300.0,
        (d[1], "BTCUSDT"): 100.0, (d[1], "AAAUSDT"): 100.0,
        (d[1], "NEWUSDT"): 10000.0,  # listed < 28d: must be excluded
        (d[2], "BTCUSDT"): 50.0, (d[2], "AAAUSDT"): 50.0,
    }
    share = gm.daily_dv_share(dv, first_day)
    assert math.isclose(share[d[0]], 0.25)
    assert math.isclose(share[d[1]], 0.5)   # NEWUSDT (age 0 < 28) excluded
    assert math.isclose(share[d[2]], 0.5)


def test_daily_dv_share_skips_day_without_btc():
    d = _dates("2024-01-01", "2024-01-02")
    dv = {(d[0], "BTCUSDT"): 0.0, (d[0], "AAAUSDT"): 10.0}
    assert gm.daily_dv_share(dv, {"BTCUSDT": d[0], "AAAUSDT": d[0]},
                             listing_age_days=0) == {}


# --- conc windows + S90 --------------------------------------------------------

def test_conc_mean_window_bounds_exclusive_of_stamp():
    d = _dates("2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04")
    share = {d[0]: 0.1, d[1]: 0.3, d[2]: 0.5, d[3]: 0.9}
    # window [st-2d, st) excludes the stamp value 0.9
    assert math.isclose(gm.conc_mean(share, d[3], 2), 0.4)
    assert gm.conc_mean(share, d[0], 2) is None  # empty -> None, never impute


def test_s90_definition_matches_dossier_code():
    # S90 = CONC(28) - CONC(90) over the same daily-share series
    share = {dt.date(2024, 1, 1) + dt.timedelta(days=i): 0.2 + 0.001 * i
             for i in range(120)}
    st = dt.date(2024, 4, 29)
    expected = (gm.conc_mean(share, st, 28) - gm.conc_mean(share, st, 90))
    assert math.isclose(gm.s90_at(share, st), expected)


# --- rvol30 --------------------------------------------------------------------

def test_rvol30_known_values():
    d = _dates("2024-01-01", "2024-01-02", "2024-01-03")
    closes = {d[0]: 100.0, d[1]: 110.0, d[2]: 100.0}
    # stamp strictly after the last close: window of 2 returns
    st = dt.date(2024, 1, 4)
    a, b = math.log(1.1), math.log(100.0 / 110.0)
    expected = math.sqrt((a ** 2 + b ** 2) / 2) * math.sqrt(365)
    assert math.isclose(gm.rvol30(closes, st, window=2), expected)


def test_rvol30_insufficient_history_is_none():
    d = _dates("2024-01-01", "2024-01-02")
    closes = {d[0]: 1.0, d[1]: 2.0}
    assert gm.rvol30(closes, dt.date(2024, 1, 3), window=30) is None


# --- hysteresis machines -------------------------------------------------------

def test_v1_hysteresis_and_boundaries():
    s = gm.v1_next_state
    assert s(0.06, True) is False          # >= OFF band
    assert s(0.03, False) is False         # between: carry
    assert s(0.03, True) is True           # between: carry
    assert s(0.01, False) is True          # <= ON band
    assert s(gm.BAND_ON_S90, False) is True    # exactly p70 -> ON (<=)
    assert s(gm.BAND_OFF_S90, True) is False   # exactly p90 -> OFF (>=)
    assert s(None, True) is True           # missing observable: carry


def test_v2_hysteresis_and_boundaries():
    s = gm.v2_next_state
    assert s(0.40, False) is True
    assert s(0.31, True) is True           # between floor and floor*0.9: carry
    assert s(0.29, True) is False          # < VOL_OFF
    assert s(gm.VOL_FLOOR, False) is True      # exactly floor -> ON (>=)
    assert s(gm.VOL_OFF, False) is False       # exactly VOL_OFF: not <, carry
    assert s(gm.VOL_OFF, True) is True
    assert s(None, True) is True


def test_gate_walk_and_semantics():
    d1, d2, d3 = _dates("2024-01-01", "2024-01-08", "2024-01-15")
    rows = {d1: (0.0, 0.5), d2: (0.06, None), d3: (0.0, 0.20)}
    walk = gm.gate_walk(rows)
    assert walk[d1].v1_state and walk[d1].v2_state and walk[d1].gated
    assert walk[d2].v1_state is False and walk[d2].gated is False   # V1 OFF
    # V2 carried ON at d2 (None), then 0.20 < VOL_OFF -> OFF at d3
    assert walk[d2].v2_state is True
    assert walk[d3].v2_state is False and walk[d3].gated is False


# --- no-lookahead mutation -----------------------------------------------------

def test_no_lookahead_mutation():
    share = {dt.date(2024, 1, 1) + dt.timedelta(days=i): 0.2
             for i in range(120)}
    closes = {dt.date(2024, 1, 1) + dt.timedelta(days=i): 100.0 + i
              for i in range(120)}
    stamp = dt.date(2024, 4, 1)
    before = (gm.s90_at(share, stamp), gm.rvol30(closes, stamp))
    future = stamp + dt.timedelta(days=7)
    share[future] = 0.999
    closes[future] = 99999.0
    after = (gm.s90_at(share, stamp), gm.rvol30(closes, stamp))
    assert before == after


# --- falsification verdict boundaries -------------------------------------------

def test_falsification_verdict_inclusive_bars():
    assert gm.falsification_verdict(-0.2947, 0.4372)["verdict"] == "PASS_BAR"
    assert gm.falsification_verdict(-0.2948, 0.40)["verdict"] == "FALSIFIED"
    assert gm.falsification_verdict(-0.10, 0.4373)["verdict"] == "FALSIFIED"
    v = gm.falsification_verdict(-0.40, 0.50)
    assert v["net_margin"] == -0.40 - (-0.2947) and v["net_margin"] < 0
    assert v["mdd_margin"] == 0.4372 - 0.50 and v["mdd_margin"] < 0


# --- random gates ----------------------------------------------------------------

def _sample_gate():
    return ([True] * 6 + [False] * 5 + [True] * 7 + [False] * 4 + [True] * 5)


def test_random_gates_preserve_structure():
    gate = _sample_gate()
    perms = gm.random_gate_permutations(gate, n=200, seed=12345)
    assert len(perms) == 200
    toggles = sum(1 for a, b in zip(gate, gate[1:]) if a != b)
    for p in perms:
        assert len(p) == len(gate)
        assert p[0] == gate[0]
        assert sum(1 for a, b in zip(p, p[1:]) if a != b) == toggles
        # run-length decomposition, min run enforced
        runs = [1]
        for a, b in zip(p, p[1:]):
            if a == b:
                runs[-1] += 1
            else:
                runs.append(1)
        assert min(runs) >= gm.RANDOM_GATE_MIN_RUN


def test_random_gates_deterministic_double_generation():
    gate = _sample_gate()
    a = gm.random_gate_permutations(gate, n=50, seed=7)
    b = gm.random_gate_permutations(gate, n=50, seed=7)
    assert a == b
    assert a != gm.random_gate_permutations(gate, n=50, seed=8)


def test_random_gates_infeasible_raises():
    try:
        gm._random_runs(5, 2, 4, __import__("random").Random(1))
    except ValueError:
        return
    raise AssertionError("expected ValueError for infeasible composition")


def test_gate_rank_percentile():
    assert gm.gate_rank_percentile(5.0, [1.0, 2.0, 3.0]) == 100.0
    assert gm.gate_rank_percentile(0.0, [1.0, 2.0, 3.0]) == 0.0
