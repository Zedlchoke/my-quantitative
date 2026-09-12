"""RATES-NG1 D2 novelty-measurement tests.

Three layers (dispatch packet rates-ng1-d2-novelty):

1. Correlation math: Spearman/Pearson on tiny hand-computed series.
2. State builders: synthetic grid/census fixtures with hand-traced
   decision states under the frozen defaults.
3. Artifact law: the committed panel's schema + arithmetic, and the
   P-12 negative test -- NO rho value may appear in any commit-1 file.

Scope law: these tests consume no market data beyond tiny synthetic
fixtures and the committed artifacts; they compute no outcome.
"""

from __future__ import annotations

import json
import math
import os
import re
import sys

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.control.rates_ng1_run.d2 import d2_correlation as dc  # noqa: E402
from research.control.rates_ng1_run.d2 import d2_frozen_defaults as fd  # noqa: E402
from research.control.rates_ng1_run.d2 import d2_states as ds  # noqa: E402
from research.control.rates_ng1_run.d2 import d2_run as dr  # noqa: E402

D2_DIR = os.path.join(REPO_ROOT, "research", "control", "rates_ng1_run",
                      "d2")
PANEL_PATH = os.path.join(D2_DIR, "d2_novelty_panel.json")
RENOTE_PATH = os.path.join(D2_DIR, "d2_feasibility_renote.json")

#: The exact commit-1 file set (P-12): code + frozen defaults + the
#: feasibility re-note.  The panel is commit-2 and must NOT appear.
COMMIT1_FILES = tuple(dr.COMMIT1_CODE_FILES)

#: Every file carried by commit-1, including this test module; all are
#: scanned by the negative no-rho test below.
COMMIT1_SCAN_FILES = COMMIT1_FILES + (
    "tests/test_rates_ng1_d2.py",
)

BASE_SHA = "052e6c0f929adaf54fb3aea4c7d626251398a6b3"


def _instants(session_indices: list[int],
              grid: list[str]) -> list[dict]:
    """Synthetic bookable instants on a synthetic grid: the readable
    bar is the previous grid session (V7 close+1 law)."""
    out = []
    for j in session_indices:
        out.append({
            "decision_session": grid[j],
            "readable_bar_date": grid[j - 1],
            "session_index": j,
        })
    return out


# ------------------------------------------------------------------ #
# 1. Correlation math (hand-computed)
# ------------------------------------------------------------------ #
class TestCorrelationMath:
    def test_pearson_hand_case(self):
        # x=[1,2,3,4], y=[1,3,2,4]: cov terms (x-2.5)(y-2.5):
        # 2.25,-0.25,-0.25,2.25 -> mean 1.0; var each 1.25 -> 0.8.
        assert dc.pearson([1, 2, 3, 4], [1, 3, 2, 4]) == \
            pytest.approx(0.8)

    def test_pearson_perfect(self):
        assert dc.pearson([1, 2, 3], [2, 4, 6]) == pytest.approx(1.0)
        assert dc.pearson([1, 2, 3], [6, 4, 2]) == pytest.approx(-1.0)

    def test_pearson_degenerate(self):
        assert dc.pearson([1, 1, 1], [1, 2, 3]) is None
        assert dc.pearson([1, 2], [1]) is None
        assert dc.pearson([], []) is None

    def test_spearman_hand_case_distinct(self):
        # ranks(y) = [1,3,2,5,4]; Pearson on ranks = 0.8 (hand).
        assert dc.spearman([1, 2, 3, 4, 5], [1, 3, 2, 5, 4]) == \
            pytest.approx(0.8)

    def test_spearman_monotone(self):
        assert dc.spearman([5, 1, 3, 2, 4], [50, 10, 30, 20, 40]) == \
            pytest.approx(1.0)
        assert dc.spearman([1, 2, 3, 4], [8, 6, 4, 2]) == \
            pytest.approx(-1.0)

    def test_average_ranks_ties(self):
        assert dc.average_ranks([1, 1, 2]) == [1.5, 1.5, 3.0]
        assert dc.average_ranks([3, 1, 2, 1]) == [4.0, 1.5, 3.0, 1.5]

    def test_spearman_ties_hand_case(self):
        # x=[1,1,2] -> ranks [1.5,1.5,3]; y=[1,2,3] -> [1,2,3].
        # mean xr=2, mean yr=2; sxy/3=0.5; var xr/3=0.5; var yr/3=2/3
        # -> 0.5 / sqrt(1/3) = 0.5*sqrt(3).
        assert dc.spearman([1, 1, 2], [1, 2, 3]) == \
            pytest.approx(0.5 * math.sqrt(3))

    def test_shadow_screen_unmeasurable_on_constant(self):
        scr = dc.shadow_screen([1.0, 1.0, 1.0, 1.0], [1, 2, 3, 4])
        assert scr["status"] == dc.UNMEASURABLE
        assert scr["spearman"] is None and scr["pearson"] is None
        assert scr["pooled_abs_max"] is None

    def test_shadow_screen_measured_values(self):
        scr = dc.shadow_screen([1, 2, 3, 4, 5], [1, 3, 2, 5, 4])
        assert scr["status"] == dc.MEASURED
        assert scr["n_used"] == 5
        assert scr["spearman"] == pytest.approx(0.8)
        assert scr["pearson"] == pytest.approx(0.8)
        assert scr["pooled_abs_max"] == pytest.approx(0.8)

    def test_pooled_is_abs_max(self):
        scr = dc.shadow_screen([1, 2, 3, 4], [4, 3, 2, 1])
        assert scr["pooled_abs_max"] == pytest.approx(1.0)

    def test_margin_to_ceiling(self):
        assert dc.margin_to_ceiling(0.19) == pytest.approx(0.01)
        assert dc.margin_to_ceiling(0.21) == pytest.approx(-0.01)
        assert dc.margin_to_ceiling(None) is None


# ------------------------------------------------------------------ #
# 2. Verdict law
# ------------------------------------------------------------------ #
def _screens(pooled_by_key: dict, statuses: dict | None = None):
    out = {}
    for k in fd.SHADOW_KEYS:
        if statuses and k in statuses \
                and statuses[k] != dc.MEASURED:
            out[k] = {"status": dc.UNMEASURABLE, "n_used": 0,
                      "spearman": None, "pearson": None,
                      "pooled_abs_max": None,
                      "reason": "insufficient_defined_pairs"}
        else:
            p = pooled_by_key[k]
            out[k] = {"status": dc.MEASURED, "n_used": 100,
                      "spearman": p, "pearson": p,
                      "pooled_abs_max": p, "reason": None}
    return out


class TestVerdictLaw:
    def test_eligible(self):
        s = _screens({k: 0.19 if k == fd.SHADOW_KEYS[0] else 0.05
                      for k in fd.SHADOW_KEYS})
        v = dc.proposal_verdict(s)
        assert v["verdict"] == dc.ELIGIBLE
        assert v["proposal_pooled_abs_rho"] == pytest.approx(0.19)
        assert v["margin_to_ceiling"] == pytest.approx(0.01)
        assert v["unmeasurable_shadows"] == []

    def test_veto_on_ceiling_breach(self):
        s = _screens({k: 0.21 if k == fd.SHADOW_KEYS[0] else 0.05
                      for k in fd.SHADOW_KEYS})
        v = dc.proposal_verdict(s)
        assert v["verdict"] == dc.VETO
        assert v["margin_to_ceiling"] == pytest.approx(-0.01)

    def test_exactly_at_ceiling_is_eligible(self):
        s = _screens({k: 0.2 if k == fd.SHADOW_KEYS[0] else 0.0
                      for k in fd.SHADOW_KEYS})
        assert dc.proposal_verdict(s)["verdict"] == dc.ELIGIBLE

    def test_veto_pending_on_unmeasurable_shadow(self):
        pooled = {k: 0.05 for k in fd.SHADOW_KEYS}
        s = _screens(pooled,
                     statuses={fd.SHADOW_KEYS[2]: dc.UNMEASURABLE})
        v = dc.proposal_verdict(s)
        assert v["verdict"] == dc.VETO_PENDING
        assert v["unmeasurable_shadows"] == [fd.SHADOW_KEYS[2]]
        # never-PASS-by-absence even when measured shadows are tiny
        assert v["margin_to_ceiling"] == pytest.approx(0.15)

    def test_missing_shadow_key_raises(self):
        s = _screens({k: 0.0 for k in fd.SHADOW_KEYS})
        del s[fd.SHADOW_KEYS[0]]
        with pytest.raises(ValueError):
            dc.proposal_verdict(s)


# ------------------------------------------------------------------ #
# 3. State builders on synthetic fixtures (hand-traced)
# ------------------------------------------------------------------ #
class TestShadowDGS10Level:
    def test_rising_and_falling_series(self, monkeypatch):
        monkeypatch.setitem(fd.DGS10_LEVEL, "trailing_window_sessions", 3)
        grid = ["2020-01-0%d" % d for d in range(1, 7)]
        levels = {"2020-01-01": 1.0, "2020-01-02": 2.0,
                  "2020-01-03": 3.0, "2020-01-04": 4.0,
                  "2020-01-05": 5.0, "2020-01-06": 6.0}
        level_fn, _ = ds.build_dgs10_level_lookup(
            [{"date": d, "value": str(v)} for d, v in levels.items()])
        instants = _instants([4, 5], grid)
        got = ds.shadow_dgs10_level_state(grid, instants, level_fn)
        # idx4: bar d4=4, trailing {2,3,4} median 3 -> +1
        # idx5: bar d5=5, trailing {3,4,5} median 4 -> +1
        assert got == [1.0, 1.0]
        levels_desc = {d: 7.0 - v for d, v in levels.items()}
        level_fn2, _ = ds.build_dgs10_level_lookup(
            [{"date": d, "value": str(v)}
             for d, v in levels_desc.items()])
        got2 = ds.shadow_dgs10_level_state(grid, instants, level_fn2)
        # idx4: bar 6-4=2, trailing {4,3,2} median 3 -> -1
        # idx5: bar 6-5=1, trailing {3,2,1} median 2 -> -1
        assert got2 == [-1.0, -1.0]

    def test_stale_level_is_undefined(self, monkeypatch):
        monkeypatch.setitem(fd.DGS10_LEVEL,
                            "max_staleness_calendar_days", 2)
        level_fn, _ = ds.build_dgs10_level_lookup(
            [{"date": "2019-06-03", "value": "2.0"}])
        assert level_fn("2019-06-04") == 2.0
        assert level_fn("2019-06-10") is None


class TestShadowReactionDirection:
    def test_sign_following_windows(self):
        grid = ["2020-01-%02d" % d for d in range(1, 11)]
        levels = {d: float(i + 1) for i, d in enumerate(grid)}
        level_fn, _ = ds.build_dgs10_level_lookup(
            [{"date": d, "value": str(v)} for d, v in levels.items()])
        instants = _instants(list(range(1, 10)), grid)
        got = ds.shadow_reaction_direction_state(
            grid, instants, [5], level_fn)
        # event at session index 5: level(b=grid[4])=5 > level(grid[3])=4
        # -> sign +1 held on sessions 5..9; earlier instants 0.
        assert got == [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0]

    def test_negative_reaction_and_overlap(self):
        grid = ["2020-01-%02d" % d for d in range(1, 11)]
        levels = {d: float(10 - i) for i, d in enumerate(grid)}
        level_fn, _ = ds.build_dgs10_level_lookup(
            [{"date": d, "value": str(v)} for d, v in levels.items()])
        instants = _instants(list(range(1, 10)), grid)
        got = ds.shadow_reaction_direction_state(
            grid, instants, [4, 6], level_fn)
        # event at 4: sign -1 on sessions 4..5; event at 6 overwrites
        # sessions 6..8 (also -1); last-write-wins.
        assert got == [0.0, 0.0, 0.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0]

    def test_flat_reaction_carries_zero(self):
        grid = ["2020-01-%02d" % d for d in range(1, 11)]
        levels = {d: 3.0 for d in grid}
        level_fn, _ = ds.build_dgs10_level_lookup(
            [{"date": d, "value": str(v)} for d, v in levels.items()])
        instants = _instants(list(range(1, 10)), grid)
        got = ds.shadow_reaction_direction_state(
            grid, instants, [5], level_fn)
        assert got == [0.0] * 9


class TestShadowReleaseOrder:
    def _events(self, first_type: str) -> list[dict]:
        return [
            {"announcementDate": "2020-01-02",
             "securityType": first_type, "cusip": "A",
             "auctionDate": "2020-01-05", "issueDate": "2020-01-08",
             "event_index": 0},
            {"announcementDate": "2020-01-06",
             "securityType": "Note", "cusip": "B",
             "auctionDate": "2020-01-08", "issueDate": "2020-01-11",
             "event_index": 1},
        ]

    def test_bill_first_month(self):
        grid = ["2020-01-%02d" % d for d in range(1, 11)]
        instants = _instants([1, 2, 9], grid)
        got = ds.shadow_release_order_state(grid, instants,
                                            self._events("Bill"))
        # first announced event 2020-01-02 (Bill) -> decision session
        # is the first grid session strictly after = index 2.
        assert got == [0.0, 1.0, 1.0]

    def test_coupon_first_month(self):
        grid = ["2020-01-%02d" % d for d in range(1, 11)]
        instants = _instants([1, 2, 9], grid)
        got = ds.shadow_release_order_state(grid, instants,
                                            self._events("Note"))
        assert got == [0.0, -1.0, -1.0]


class TestShadowMomentum63s:
    def test_equal_weight_mean_of_leg_signs(self, monkeypatch):
        monkeypatch.setitem(fd.MOMENTUM_63S, "lookback_sessions", 3)
        grid = ["2020-01-%02d" % d for d in range(1, 6)]
        instants = _instants([4], grid)
        leg_closes = {
            "TLT": {d: float(i + 1) for i, d in enumerate(grid)},
            "IEF": {d: float(10 - i) for i, d in enumerate(grid)},
            "IEI": {d: 5.0 for d in grid},
            "SHY": {d: float(i + 1) for i, d in enumerate(grid)},
        }
        got = ds.shadow_momentum_63s_state(grid, instants, leg_closes)
        # at j=4: bar grid[3]=4, 3 sessions earlier grid[0]=1.
        # TLT +1, IEF -1, IEI 0 (flat), SHY +1 -> mean 0.25.
        assert got == [pytest.approx(0.25)]

    def test_missing_leg_close_is_undefined(self, monkeypatch):
        monkeypatch.setitem(fd.MOMENTUM_63S, "lookback_sessions", 3)
        grid = ["2020-01-%02d" % d for d in range(1, 6)]
        instants = _instants([4], grid)
        leg_closes = {"TLT": {d: 1.0 for d in grid}}
        got = ds.shadow_momentum_63s_state(grid, instants, leg_closes)
        assert got == [None]


class TestShadowDowTue:
    def test_tuesday_clock(self):
        instants = [{"decision_session": d, "readable_bar_date": d,
                     "session_index": 0}
                    for d in ("2019-01-07", "2019-01-08",
                              "2019-01-12", "2019-01-13")]
        got = ds.shadow_dow_tue_state(instants)
        # Mon, Tue, Sat, Sun -> 0, +1, 0, 0
        assert got == [0.0, 1.0, 0.0, 0.0]


class TestProposalA4States:
    GRID6 = ["2020-01-0%d" % d for d in range(1, 7)]

    def _events(self):
        return [
            {"announcementDate": "2019-12-30", "issueDate": "2020-01-04",
             "auctionDate": "2020-01-02", "securityType": "Note",
             "cusip": "A", "event_index": 0},
            {"announcementDate": "2019-12-31", "issueDate": "2020-01-02",
             "auctionDate": "2020-01-03", "securityType": "Bill",
             "cusip": "B", "event_index": 1},
        ]

    def test_a4_p1_concentration_hand_traced(self, monkeypatch):
        monkeypatch.setitem(fd.A4_P1_CONCENTRATION, "k1_sessions", 1)
        monkeypatch.setitem(fd.A4_P1_CONCENTRATION, "k2_sessions", 1)
        grid = self.GRID6
        instants = _instants(list(range(6)), grid)
        got = ds.proposal_state_a4_p1(grid, instants, self._events())
        # k1=k2=1 windows: counts [1,1,2,1,1,0]; median 1.0
        # -> [0,0,+1,0,0,-1]
        assert got == [0.0, 0.0, 1.0, 0.0, 0.0, -1.0]

    def test_a4_p1_pit_filter_excludes_late_announcements(
            self, monkeypatch):
        monkeypatch.setitem(fd.A4_P1_CONCENTRATION, "k1_sessions", 2)
        monkeypatch.setitem(fd.A4_P1_CONCENTRATION, "k2_sessions", 2)
        grid = self.GRID6
        instants = _instants([0], grid)
        events = [{"announcementDate": "2020-01-03",
                   "issueDate": "2020-01-02",
                   "auctionDate": "2020-01-05", "securityType": "Bill",
                   "cusip": "C", "event_index": 2}]
        # announced (decision session idx 2) AFTER decision session 0:
        # the issue date 2020-01-02 must NOT be counted at j=0.
        got = ds.proposal_state_a4_p1(grid, instants, events)
        assert got == [0.0]

    def test_a4_p2_stage_hand_traced(self, monkeypatch):
        monkeypatch.setitem(fd.A4_P2_STAGE, "settlement_era_sessions", 2)
        grid = ["2020-01-0%d" % d for d in range(1, 9)]
        instants = _instants(list(range(8)), grid)
        events = [{"announcementDate": "2019-12-31",
                   "auctionDate": "2020-01-03",
                   "issueDate": "2020-01-06",
                   "securityType": "Note", "cusip": "A",
                   "event_index": 0}]
        got = ds.proposal_state_a4_p2(grid, instants, events)
        # Strictly-after law: ann_j=0 (2019-12-31 -> 01-01), auc_j=3
        # (01-03 -> 01-04), iss_j=6 (01-06 -> 01-07), end_j=8:
        # j0-2 announcement-era -1; j3-5 auction-era 0;
        # j6-7 settlement-era +1 (settlement_era_sessions=2).
        assert got == [-1.0, -1.0, -1.0, 0.0, 0.0, 0.0, 1.0, 1.0]


class TestProposalA5States:
    def test_ols_residual_hand_traced(self):
        got = ds._ols_residual_series([1.0, 2.0, 3.0, 5.0],
                                      [1.0, 2.0, 3.0, 4.0], 3)
        # first three points fit y=x exactly; residual at the fourth
        # is 5 - 4 = 1; earlier instants undefined.
        assert got == [None, None, None, pytest.approx(1.0)]

    def test_ols_degenerate_level_is_undefined(self):
        got = ds._ols_residual_series([2.0, 2.0, 2.0, 4.0],
                                      [2.0, 2.0, 2.0, 2.0], 2)
        assert got == [None, None, None, None]

    def test_a5_p1_double_median_hand_traced(self, monkeypatch):
        monkeypatch.setitem(fd.A5_P1_CURVATURE_GATED_SLOPE,
                            "min_past_points", 2)
        grid = ["2020-01-0%d" % d for d in range(1, 6)]
        # readable bars are grid[0..3] for instants at session_index
        # 1..4; curve values (2 Yr, 10 Yr, 30 Yr) per readable bar:
        curve = {
            "2020-01-01": {"2 Yr": 2.0, "10 Yr": 3.0, "30 Yr": 4.0,
                           "5 Yr": 3.0},
            "2020-01-02": {"2 Yr": 2.0, "10 Yr": 4.0, "30 Yr": 6.0,
                           "5 Yr": 3.0},
            "2020-01-03": {"2 Yr": 2.0, "10 Yr": 5.0, "30 Yr": 8.0,
                           "5 Yr": 3.0},
            "2020-01-04": {"2 Yr": 2.0, "10 Yr": 4.0, "30 Yr": 8.0,
                           "5 Yr": 3.0},
        }
        instants = _instants([1, 2, 3, 4], grid)
        got = ds.proposal_state_a5_p1(grid, instants, curve)
        # Hand trace (min_past=2): slope residuals at instants 3,4 are
        # (6-5)=1 and 6-(2+0.5*4)=2 -> cut_s=1.5; curvature residuals
        # are 0 and 2 -> cut_c=1.0.  Instant 3: 1<1.5 and 0<1.0 -> -1
        # (both below); instant 4: 2>1.5 and 2>1.0 -> +1 (both above).
        assert got == [None, None, pytest.approx(-1.0), pytest.approx(1.0)]

    def test_a5_p2_residual_sign_hand_traced(self, monkeypatch):
        monkeypatch.setitem(fd.A5_P2_FRONT_VS_BELLY, "min_past_points", 2)
        grid = ["2020-01-0%d" % d for d in range(1, 6)]
        curve = {
            "2020-01-01": {"2 Yr": 3.0, "5 Yr": 1.0, "10 Yr": 2.0},
            "2020-01-02": {"2 Yr": 4.0, "5 Yr": 1.0, "10 Yr": 3.0},
            "2020-01-03": {"2 Yr": 8.0, "5 Yr": 1.0, "10 Yr": 4.0},
            "2020-01-04": {"2 Yr": 4.0, "5 Yr": 1.0, "10 Yr": 5.0},
        }
        instants = _instants([1, 2, 3, 4], grid)
        got = ds.proposal_state_a5_p2(instants, curve)
        # raw residuals r=(2,3,7,3) on level (2,3,4,5), y=r, x=level:
        # res(i3)=7-4=3 (fit on (2,2),(3,3)); res(i4)=3-(22/14+5*5/14)
        # = -5/14 (fit on the first three); cut = median(3, -5/14)
        # = 37/28 -> +1 then -1.
        assert got == [None, None, pytest.approx(1.0),
                       pytest.approx(-1.0)]

    def test_a5_p2_degenerate_unmeasurable(self, monkeypatch):
        monkeypatch.setitem(fd.A5_P2_FRONT_VS_BELLY, "min_past_points", 2)
        grid = ["2020-01-0%d" % d for d in range(1, 6)]
        curve = {d: {"2 Yr": 3.0, "5 Yr": 1.0, "10 Yr": 2.0}
                 for d in grid}
        instants = _instants([1, 2, 3, 4], grid)
        got = ds.proposal_state_a5_p2(instants, curve)
        assert all(v is None for v in got)
        scr = dc.shadow_screen(got, [1.0, -1.0, 1.0, -1.0])
        assert scr["status"] == dc.UNMEASURABLE


# ------------------------------------------------------------------ #
# 4. P-12 negative test: commit-1 files contain no rho values
# ------------------------------------------------------------------ #
#: JSON-style result record: a result key immediately followed by a
#: number (a committed rho value would look exactly like this).
_JSON_RESULT_RE = re.compile(
    r'"(spearman|pearson|pooled_abs_max|proposal_pooled_abs_rho|'
    r'margin_to_ceiling)":\s*-?\d')
#: Python assignment of a numeric literal to a result name.
_ASSIGN_RESULT_RE = re.compile(
    r'\b(spearman|pearson|pooled_abs_max|proposal_pooled_abs_rho|'
    r'margin_to_ceiling)\s*=\s*-?\d')


class TestCommit1ContainsNoRhoValues:
    def test_commit1_file_set_is_exactly_the_code_set(self):
        expected = sorted(COMMIT1_FILES)
        for rel in expected:
            assert os.path.isfile(os.path.join(REPO_ROOT, rel)), rel
        # the results artifact must never be a commit-1 file
        assert ("research/control/rates_ng1_run/d2/d2_novelty_panel.json"
                not in COMMIT1_FILES)

    @pytest.mark.parametrize("rel", COMMIT1_SCAN_FILES)
    def test_no_rho_value_patterns(self, rel):
        with open(os.path.join(REPO_ROOT, rel), "r",
                  encoding="utf-8") as fh:
            text = fh.read()
        assert _JSON_RESULT_RE.search(text) is None, rel
        assert _ASSIGN_RESULT_RE.search(text) is None, rel

    def test_renote_json_carries_no_result_keys(self):
        with open(RENOTE_PATH, "r", encoding="utf-8") as fh:
            doc = json.load(fh)

        def _walk(node):
            if isinstance(node, dict):
                for k, v in node.items():
                    assert not re.fullmatch(
                        r"(spearman|pearson|pooled\w*|margin\w*|verdict)",
                        k), k
                    _walk(v)
            elif isinstance(node, list):
                for v in node:
                    _walk(v)

        _walk(doc)

    def test_frozen_defaults_module_declares_the_ceiling_only_as_law(
            self):
        # the ceiling constant is the only allowed rho-adjacent number
        # in commit-1 and must equal the D1 rubric value 0.2.
        assert fd.NOVELTY_ABS_RHO_CEILING == 0.2
        assert fd.CORRELATION_LAW["margin_definition"] == \
            "ceiling_minus_proposal_pooled"


# ------------------------------------------------------------------ #
# 5. Committed panel schema + arithmetic (post commit-2)
# ------------------------------------------------------------------ #
@pytest.mark.skipif(not os.path.isfile(PANEL_PATH),
                    reason="commit-2 panel not present yet")
class TestCommittedPanel:
    @pytest.fixture(scope="class")
    def panel(self):
        with open(PANEL_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def test_schema_and_identity(self, panel):
        assert panel["schema"] == "rates_ng1_run/d2_novelty_panel@1"
        assert panel["cycle_id"] == "RATES-NG1"
        assert panel["task_id"] == "rates-ng1-d2-novelty"
        assert panel["base_sha"] == BASE_SHA
        assert re.fullmatch(r"[0-9a-f]{40}", panel["commit_1_sha256"])
        assert panel["commit_1_sha256"] != BASE_SHA

    def test_commit1_files_unmodified_since_measurement(self, panel):
        for rel, digest in panel["commit1_code_sha256"].items():
            h = dr.sha256_file(os.path.join(REPO_ROOT, rel))
            assert h == digest, rel

    def test_proposals_and_shadow_keys(self, panel):
        assert set(panel["proposals"]) == set(fd.PROPOSAL_IDS)
        for pid, block in panel["proposals"].items():
            assert set(block["shadows"]) == set(fd.SHADOW_KEYS)
            assert block["ceiling"] == pytest.approx(0.2)

    def test_per_shadow_values_and_pooling(self, panel):
        for pid, block in panel["proposals"].items():
            measured_pooled = []
            for key, scr in block["shadows"].items():
                assert scr["status"] in (dc.MEASURED, dc.UNMEASURABLE)
                if scr["status"] == dc.MEASURED:
                    assert scr["n_used"] >= 2
                    for stat in ("spearman", "pearson"):
                        assert -1.0 <= scr[stat] <= 1.0, (pid, key)
                    assert scr["pooled_abs_max"] == pytest.approx(
                        max(abs(scr["spearman"]),
                            abs(scr["pearson"]))), (pid, key)
                    measured_pooled.append(scr["pooled_abs_max"])
                else:
                    assert scr["spearman"] is None
                    assert scr["pearson"] is None
                    assert scr["pooled_abs_max"] is None
                    assert scr["reason"]
            if measured_pooled:
                assert block["proposal_pooled_abs_rho"] == \
                    pytest.approx(max(measured_pooled)), pid

    def test_margins_and_verdict_law(self, panel):
        ceiling = 0.2
        for pid, block in panel["proposals"].items():
            unmeasured = block["unmeasurable_shadows"]
            pooled = block["proposal_pooled_abs_rho"]
            assert block["margin_to_ceiling"] == \
                pytest.approx(ceiling - pooled), pid
            if unmeasured:
                assert block["verdict"] == dc.VETO_PENDING, pid
            elif pooled <= ceiling:
                assert block["verdict"] == dc.ELIGIBLE, pid
            else:
                assert block["verdict"] == dc.VETO, pid

    def test_feasibility_renote_recorded(self, panel):
        ren = panel["feasibility_renote"]
        assert ren["path"].endswith("d2_feasibility_renote.json")
        assert set(ren["per_proposal"]) == set(fd.PROPOSAL_IDS)

    def test_series_health_instants(self, panel):
        n = panel["representation"]["bookable_instants"]
        assert n == 1918
        for pid, health in panel["series_health"]["proposals"].items():
            assert health["n_total"] == n, pid
        for key, health in panel["series_health"]["shadows"].items():
            assert health["n_total"] == n, key

    def test_results_body_digest(self, panel):
        body = {k: v for k, v in panel.items()
                if k not in ("measured_utc", "results_body_sha256")}
        digest = dr.hashlib.sha256(json.dumps(
            body, sort_keys=True, separators=(",", ":"))
            .encode("utf-8")).hexdigest()
        assert digest == panel["results_body_sha256"]
