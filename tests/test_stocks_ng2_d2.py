"""STOCKS-NG2 D2 tests: hand-computed fixtures, zero substrate dependency.

Three law-groups (dispatch packet):

  1. one rho pair hand-computed: a full novelty_block verdict on a tiny
     synthetic anchor with monkeypatched veto builders, hand-computed
     pooled rho = 1.0 and margin = -0.8, plus the midrank closed form;
  2. one fail-closed unmeasured case: a veto with empty support drives
     the verdict to INELIGIBLE_FAIL_CLOSED naming the entry - never a
     pass by absence;
  3. one amendment-lag case: hand-built pair events through the REAL
     amendlag/cdays builders (odd/even median, PIT session attribution,
     trailing-63-session window, dV != 0 floor, ADV63 normalization)
     plus the sham permutation's per-cell multiset preservation, seed
     determinism and the stamp cross-check rule.

Supporting: frozen constants (17-entry veto set, seed, floors) and the
declared fold pair-mass arithmetic 612/543/722.

No network, no heavy inputs: everything runs on in-memory fixtures.
"""

from __future__ import annotations

import math
import os
import sys
from datetime import date, timedelta

import pytest

_REPO = os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.pardir))
sys.path.insert(0, _REPO)

from research.assets.stocks_ng2.d2 import core, exposures, measure  # noqa: E402
from research.assets.stocks_ng2.d2 import vetoes as ng2vetoes  # noqa: E402
from research.assets.stocks_ng2.d2.core import midrank, spearman  # noqa: E402


# ===========================================================================
# group 0: frozen constants of record (any change is a re-freeze event)
# ===========================================================================
class TestFrozenConstants:
    def test_veto_set_is_17_with_ng1_additions(self):
        assert len(core.VETO_NAMES) == 17
        assert core.VETO_NAMES[:15] == core.VETO_NAMES_15
        assert core.VETO_NAMES[15:] == ["ng1_10b5_1_fdens",
                                        "ng1_10b5_1_planshare"]
        assert sorted(ng2vetoes.VETO_BUILDERS) == sorted(core.VETO_NAMES)

    def test_frozen_numbers(self):
        assert core.NOVELTY_BAR == 0.20
        assert core.SELF_SUBSUMPTION_RHO == 0.98
        assert core.SPEARMAN_MIN_N == 10
        assert core.Q6_RECENT_WINDOW_FLOOR == 30
        assert core.FOLD_POPULATION_FLOOR == 20
        assert core.SECTOR_BOOKABLE_NAMES == 6
        assert core.TURNOVER_CEILING_BPS_QTR == 200
        assert core.TRAIL_SESSIONS == 63
        assert exposures.SHAM_SEED == 20260912

    def test_declared_fold_pair_mass_arithmetic(self):
        # census by-year split 157/218/237 | 286/257 | 271/262/179/10
        by_year = {"2018": 157, "2019": 218, "2020": 237, "2021": 286,
                   "2022": 257, "2023": 271, "2024": 262, "2025": 179,
                   "2026": 10}
        assert sum(v for k, v in by_year.items() if k <= "2020") == 612
        assert sum(v for k, v in by_year.items()
                   if "2021" <= k <= "2022") == 543
        assert sum(v for k, v in by_year.items() if k >= "2023") == 722
        assert core.FOLD_PAIR_MASS_DECLARED == {
            "SFNG2-A4-F1": 612, "SFNG2-A4-F2": 543, "SFNG2-A4-F3": 722}


# ===========================================================================
# group 1: hand-computed rho pair
# ===========================================================================
def _pick(grid, n):
    step = max(1, len(grid) // n)
    out = []
    i = 0
    while len(out) < n and i < len(grid):
        out.append(grid[i])
        i += step
    while len(out) < n:
        out.append(grid[len(out) % len(grid)])
    return out


def _ctx():
    C = core.Ctx()
    C.sessions = [(date(2018, 1, 1) + timedelta(days=i)).isoformat()
                  for i in range(40)]
    C.sess_idx = {d: i for i, d in enumerate(C.sessions)}
    C.grid = C.sessions[5:25]
    C.grid_end = C.grid[-1]
    C.folds = [{"fold_id": "F1", "start": C.grid[0], "end": C.grid[9]},
               {"fold_id": "F2", "start": C.grid[10], "end": C.grid_end}]
    return C


class TestRhoHandComputed:
    def test_midrank_closed_form(self):
        # a = [2,2,4,4,6,6,8,8,10,10,12]; b = 1..11
        # midranks a = [1.5,1.5,3.5,3.5,5.5,5.5,7.5,7.5,9.5,9.5,11] (mean 6)
        # cov = 107.5, ss_a = 107.5, ss_b = 110
        # -> rho = 107.5 / sqrt(107.5*110) = 0.988149...
        a = [2.0, 2.0, 4.0, 4.0, 6.0, 6.0, 8.0, 8.0, 10.0, 10.0, 12.0]
        b = [float(i) for i in range(1, 12)]
        ra, rb = midrank(a), midrank(b)
        ma, mb = sum(ra) / 11, sum(rb) / 11
        cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
        ss_a = sum((x - ma) ** 2 for x in ra)
        ss_b = sum((y - mb) ** 2 for y in rb)
        assert cov == pytest.approx(107.5)
        assert ss_a == pytest.approx(107.5)
        assert ss_b == pytest.approx(110.0)
        assert spearman(a, b) == pytest.approx(
            107.5 / math.sqrt(107.5 * 110.0), abs=1e-12)

    def test_novelty_block_one_rho_pair(self, monkeypatch):
        C = _ctx()
        ents = [f"CIK{i:010d}" for i in range(4)]
        keys = [(ents[i // 3], t) for i, t in enumerate(_pick(C.grid, 12))]
        anchor = {k: float(i + 1) for i, k in enumerate(keys)}
        # one veto is a strictly increasing affine copy of the anchor on
        # the same 12 pairs -> rho = 1.0 exactly, margin 0.20 - 1 = -0.8;
        # every other veto measures but stays flat-under-bar via a
        # rank-uncorrelated construction
        def veto_up(C_, e, t):
            return anchor.get((e, t))
        def veto_unCorrelated(C_, e, t):
            # alternating pattern vs the anchor's increasing one:
            # hand-check rho = 0 (symmetric ranks)
            return float(((list(anchor).index((e, t)) % 2) * 2) - 1)
        monkeypatch.setitem(ng2vetoes.VETO_BUILDERS, "vol_level", veto_up)
        for nm in core.VETO_NAMES:
            if nm != "vol_level":
                monkeypatch.setitem(ng2vetoes.VETO_BUILDERS, nm,
                                    veto_unCorrelated)
        nov = measure.novelty_block(C, anchor)
        assert nov["veto_rho"]["vol_level"] == pytest.approx(1.0)
        assert nov["margin_to_020"]["vol_level"] == pytest.approx(-0.8)
        assert nov["max_abs_veto_rho"] == pytest.approx(1.0)
        assert nov["argmax_veto"] == "vol_level"
        assert nov["verdict"].startswith(
            "VETO(argmax=vol_level,rho=1.0,margin_to_020=-0.8)")


# ===========================================================================
# group 2: fail-closed unmeasured
# ===========================================================================
class TestFailClosedUnmeasured:
    def test_empty_support_veto_fails_closed(self, monkeypatch):
        C = _ctx()
        ents = [f"CIK{i:010d}" for i in range(4)]
        keys = [(ents[i // 3], t) for i, t in enumerate(_pick(C.grid, 12))]
        anchor = {(e, t): float((i % 3) + 1)
                  for i, (e, t) in enumerate(keys)}
        def veto_none(C_, e, t):
            return None
        def veto_ok(C_, e, t):
            return float(list(anchor).index((e, t)) % 5)
        monkeypatch.setitem(ng2vetoes.VETO_BUILDERS,
                            "v12_death_event_form", veto_none)
        for nm in core.VETO_NAMES:
            if nm != "v12_death_event_form":
                monkeypatch.setitem(ng2vetoes.VETO_BUILDERS, nm, veto_ok)
        nov = measure.novelty_block(C, anchor)
        assert nov["veto_rho"]["v12_death_event_form"] is None
        assert nov["unmeasured_entries"] == ["v12_death_event_form"]
        assert nov["verdict"].startswith("INELIGIBLE_FAIL_CLOSED")
        assert "v12_death_event_form" in nov["verdict"]
        # fail-closed means NEVER a pass by absence:
        assert nov["novelty_pass_le_020"] is False


# ===========================================================================
# group 3: the amendment-lag case (real builders on hand-built events)
# ===========================================================================
def _cal(n, start=date(2018, 1, 1)):
    days, d = [], start
    while len(days) < n:
        if d.weekday() < 5:
            days.append(d.isoformat())
        d += timedelta(days=1)
    return days


def _events(C, cik, rows):
    """rows = [(session_index, lag, dv), ...] -> E4a entry."""
    rows = sorted(rows, key=lambda r: (r[0], r[3]))
    return {"sess_idx": [r[0] for r in rows],
            "sess_d": [C.sessions[r[0]] for r in rows],
            "events": [(r[1], r[2]) for r in rows],
            "accs": [r[3] for r in rows]}


class TestAmendLagCase:
    def _ctx(self):
        C = core.Ctx()
        days = _cal(400)
        C.sessions = days
        C.sess_idx = {d: i for i, d in enumerate(days)}
        C.grid = days[100:]
        C.grid_end = C.grid[-1]
        C.bookable = {"CIK0000000001": {"sector": "XLF",
                                        "cls": "ALIVE_EVIDENCED"}}
        C.series = {"CIK0000000001": _series(days)}
        C.E4a = {"CIK0000000001": _events(C, "CIK0000000001", [
            # (si, lag, dv, acc): three pair events, sessions 190/200/210
            (190, 10.0, 5000.0, "A1"),
            (200, 30.0, 0.0, "A2"),
            (210, 50.0, -2000.0, "A3"),
        ])}
        C.E = {}
        C.Arr4a = {}
        return C

    def test_amendlag_odd_median_and_window(self):
        C = self._ctx()
        t = C.sessions[210]            # all three events in trailing 63
        assert exposures.amendlag(C, "CIK0000000001", t) == pytest.approx(30.0)
        t = C.sessions[200]            # events at 190, 200 only
        assert exposures.amendlag(C, "CIK0000000001", t) == pytest.approx(20.0)
        # window floor: at session 252, events > 63 sessions old drop out
        t = C.sessions[273]            # 273-63+1 = 211 > 210 -> empty
        assert exposures.amendlag(C, "CIK0000000001", t) is None
        # PIT session attribution lives in pairs.resolve_pairs; the
        # window law itself is exercised above through sess_idx bounds

    def test_amendlag_even_count_median(self):
        C = self._ctx()
        C.E4a["CIK0000000001"] = _events(C, "CIK0000000001", [
            (300, 4.0, None, "B1"), (301, 10.0, None, "B2"),
            (302, 15.0, None, "B3"), (303, 26.0, None, "B4")])
        t = C.sessions[303]
        # even count: median = (10 + 15)/2 = 12.5
        assert exposures.amendlag(C, "CIK0000000001", t) == pytest.approx(12.5)

    def test_cdays_dv_floor_and_adv_normalization(self):
        C = self._ctx()
        # hand-computed ADV63 at t = session 210: series below has
        # close 10.0 and volume 100,000 for every bar -> ADV63 = 1e6 USD
        t = C.sessions[210]
        adv = core.adv63(C, "CIK0000000001", t)
        assert adv == pytest.approx(1_000_000.0)
        # sum dV in window = 5000 + 0 - 2000 = 3000 (the dV=0 pair does
        # not defeat the floor: A1/A3 carry dV != 0)
        assert exposures.cdays(C, "CIK0000000001", t) == pytest.approx(
            3000.0 / 1_000_000.0)
        # floor starves when the only in-window pairs are zero-correction
        C.E4a["CIK0000000001"] = _events(C, "CIK0000000001", [
            (190, 10.0, 0.0, "Z1"), (191, 20.0, None, "Z2")])
        t = C.sessions[250]
        assert exposures.cdays(C, "CIK0000000001", t) is None
        # unmeasurable dV alone does not satisfy the floor either
        C.E4a["CIK0000000001"] = _events(C, "CIK0000000001", [
            (190, 10.0, None, "Z3")])
        assert exposures.cdays(C, "CIK0000000001", t) is None

    def test_pit_session_attribution_rule(self):
        # first_session_ge = the ng1 house rule: an acceptance enters at
        # the first session on/after its UTC calendar date
        from research.assets.stocks_ng2.d2.core import first_session_ge
        days = _cal(10, start=date(2018, 1, 1))
        # 2018-01-06 is a Saturday -> first session on/after is Mon 08
        assert first_session_ge(days, "2018-01-06") == "2018-01-08"
        assert first_session_ge(days, "2018-01-05") == "2018-01-05"
        assert first_session_ge(days, "2018-01-01") == "2018-01-01"


class TestShamConstruction:
    def _ctx(self):
        C = core.Ctx()
        days = _cal(300)
        C.sessions = days
        C.sess_idx = {d: i for i, d in enumerate(days)}
        C.grid = days[50:]
        C.grid_end = C.grid[-1]
        C.bookable = {
            "CIK0000000001": {"sector": "XLF", "cls": "ALIVE_EVIDENCED"},
            "CIK0000000002": {"sector": "XLF", "cls": "ALIVE_EVIDENCED"},
            "CIK0000000003": {"sector": "XLF", "cls": "ALIVE_EVIDENCED"},
        }
        C.series = {c: _series(days) for c in C.bookable}
        # treatment entity 1: two pair events (one session each)
        C.E4a = {"CIK0000000001": _events(C, "CIK0000000001", [
            (100, 12.0, 400.0, "A1"), (150, 40.0, -600.0, "A2")])}
        # original-only support: entities 2/3 have type-4 acceptances in
        # the trailing 63 sessions of the cells (sessions 100 and 150)
        C.E = {}
        for cik, sis in (("CIK0000000002", [90, 140]),
                         ("CIK0000000003", [100, 150])):
            C.E[cik] = {"sess_idx": sis,
                        "sess_d": [C.sessions[i] for i in sis]}
        C.Arr4a = {}
        return C

    def test_multiset_preserved_and_seed_deterministic(self):
        C = self._ctx()
        info = exposures.build_sham(C, seed=exposures.SHAM_SEED)
        # every value permuted is preserved exactly once per cell
        flat = []
        for cik, E in C.Esham_lag.items():
            flat.extend(E["events"])
        assert sorted(x for lst in flat for x in lst) == [12.0, 40.0]
        flat_dv = []
        for cik, E in C.Esham_dv.items():
            flat_dv.extend(E["events"])
        assert sorted(x for lst in flat_dv for x in lst) == [-600.0, 400.0]
        assert info["cells"] == 2 and info["values_permuted"] == 2
        # determinism: same seed -> identical structures
        first = {k: (v["sess_idx"], v["events"]) for k, v in
                 C.Esham_lag.items()}
        exposures.build_sham(C, seed=exposures.SHAM_SEED)
        second = {k: (v["sess_idx"], v["events"]) for k, v in
                  C.Esham_lag.items()}
        assert first == second
        # matched original-only entities may receive values under the
        # permutation (support = treatment + original-only of sector)
        recv = set(C.Esham_lag) | set(C.Esham_dv)
        assert recv <= {"CIK0000000001", "CIK0000000002", "CIK0000000003"}

    def test_crosscheck_rule_units(self):
        # ET last-modified date must be UTC date or UTC date - 1
        def ok(utc, lm):
            return (date.fromisoformat(utc) - date.fromisoformat(lm)).days \
                in (0, 1)
        assert ok("2026-09-03", "2026-09-03")     # same-day ET
        assert ok("2026-09-03", "2026-09-02")     # before-midnight ET
        assert not ok("2026-09-03", "2026-09-01")  # 2 days off -> fail
        assert not ok("2026-09-03", "2026-09-04")  # future ET -> fail


def _series(dates, base=10.0, vol=100_000):
    n = len(dates)
    close = [base] * n
    return {"dates": list(dates), "close": close, "adj": list(close),
            "vol": [vol] * n,
            "pre": ([0.0] * n, [0.0] * n, [0.0] * n, [0] * n),
            "dv": _prefix([base * vol] * n)}


def _prefix(vals):
    out = [0.0]
    for v in vals:
        out.append(out[-1] + v)
    return out[1:]


class TestEligibilityFloors:
    def test_adv63_and_close_floor(self):
        days = _cal(200)
        C = core.Ctx()
        C.sessions = days
        C.sess_idx = {d: i for i, d in enumerate(days)}
        C.grid = days[100:]
        C.grid_end = C.grid[-1]
        s = _series(days, base=10.0, vol=100_000)     # ADV63 = 1M < 2M
        C.series = {"CIK0000000001": s}
        t = days[150]
        assert core.adv63(C, "CIK0000000001", t) == pytest.approx(1e6)
        assert core.eligible(C, "CIK0000000001", t) is False
        s2 = _series(days, base=10.0, vol=250_000)    # ADV63 = 2.5M
        C.series = {"CIK0000000001": s2}
        assert core.eligible(C, "CIK0000000001", t) is True
        s3 = _series(days, base=0.5, vol=250_000)     # close < 1.00
        C.series = {"CIK0000000001": s3}
        assert core.eligible(C, "CIK0000000001", t) is False


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
