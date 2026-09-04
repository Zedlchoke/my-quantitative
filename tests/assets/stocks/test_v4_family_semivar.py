"""V4 family-2 (SFV4-A4-H1-SEMIVARIANCE-SHARE) evidence suite — lane A9.

The 12 required evidence items of PLAN section 9 for this family, one test
class per item.  Discipline, restated so it cannot be missed:

* every real-data test is SCHEDULE-ONLY (real dates and counts from the
  sha256-pinned read-only staged snapshot; every read is S0-bounded — no
  date >= 2025-08-01 is ever read) and computes ZERO returns, ZERO features
  and ZERO PnL from real prices;
* all scored-looking numbers anywhere in this suite live on SYNTHETIC data
  and are dummy metrics (scored=false, real_pnl=false in any artifact);
* all writes go to pytest temporary directories; the canonical ledger and
  the control artifacts are never written by this suite.

Run:  /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest \
      tests/assets/stocks/test_v4_family_semivar.py -q   (from worktree root)
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

import pytest

from research.assets.stocks.factory import (
    CASH_SYMBOL,
    GatedTrialLedger,
    etf_leg_turnover,
    select_drop_one_symbol,
    value_book,
)
from research.stocks_free_v4.family_semivar import (
    ARM_KEY_ANCHOR,
    ARM_KEY_CONTROL,
    ARM_KEY_NEIGHBOUR,
    FAMILY_ID,
    ArmConfig,
    arm_config_digests,
    build_arm_configs,
    build_arm_schedule,
    build_arm_schedule_by_folds,
    clock_anchor_index,
    decision_indices,
    eligibility,
    ew_sector_return,
    feature_value,
    fold_of,
    fold_sessions,
    kappa_frozen,
    next_session,
    rank_symbols,
    schedule_only_feasibility,
    schedules_equal,
    seed_book,
    semivariance_share,
    step_book,
    target_weights,
    total_sum_sq,
)
from research.stocks_free_v4.family_semivar.config import (
    CLOCK_ANCHOR_SESSION,
    CLOCK_STEP_SESSIONS,
    FOLDS,
    LEG_WEIGHT,
    SECTOR_SYMBOLS,
    STATE_WINDOW_ANCHOR,
    STATE_WINDOW_CONTROL,
    STATE_WINDOW_NEIGHBOUR,
)

# --------------------------------------------------------------------------- #
# synthetic calendar + deterministic panels (no randomness anywhere)
# --------------------------------------------------------------------------- #
SYMS = SECTOR_SYMBOLS


def weekday_sessions(start: str, end: str) -> list[str]:
    d = dt.date.fromisoformat(start)
    last = dt.date.fromisoformat(end)
    out = []
    while d <= last:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


#: Synthetic calendar spanning all three frozen folds, with pre-anchor
#: warmup.  The anchor 2018-04-04 is a member; ticks never collide with a
#: fold-end session (verified property of this range).
SYN_SESSIONS = weekday_sessions("2017-06-01", "2025-08-29")


def arithmetic_panel(sessions, syms=SYMS):
    """Deterministic pseudo-returns: r(s, k) = 0.001 * ((7k + 3j) mod 13 - 6).

    Pure arithmetic of the session index and the symbol index — byte-stable
    across runs and machines, no RNG.  Values in [-0.006, 0.006].
    """
    return {
        s: [0.001 * (((7 * k + 3 * j) % 13) - 6) for k in range(len(sessions))]
        for j, s in enumerate(syms)
    }


def periodic_panel(sessions, syms=SYMS):
    """Deterministic 21-session-periodic panel: every tick sees the same
    trailing-window multiset (126 = 6x21, 63 = 3x21), so the ranking is
    frozen in time and the hysteresis book never changes after the seed."""
    return {
        s: [0.001 * (((7 * (k % 21) + 3 * j) % 13) - 6) for k in range(len(sessions))]
        for j, s in enumerate(syms)
    }


def history_by_tick(cfg: ArmConfig, sessions, panel):
    """Trailing completed-return windows (length = state window) per tick."""
    out = []
    w = cfg.state_window_sessions
    for i in decision_indices(sessions):
        if fold_of(sessions[i]) is None:
            continue
        assert i + 1 >= w, "synthetic calendar must carry the warmup runway"
        windows = {s: list(panel[s][i - w + 1: i + 1]) for s in panel}
        out.append((sessions[i], windows))
    return out


def build_both(cfg, sessions, panel):
    hbt = history_by_tick(cfg, sessions, panel)
    return (
        build_arm_schedule(cfg, sessions, hbt),
        build_arm_schedule_by_folds(cfg, sessions, hbt),
    )


CFGS = build_arm_configs()
CFG_A = CFGS[ARM_KEY_ANCHOR]
CFG_N = CFGS[ARM_KEY_NEIGHBOUR]
CFG_C = CFGS[ARM_KEY_CONTROL]


# =========================================================================== #
# 1. hand-computed feature golden
# =========================================================================== #
class Test01FeatureGolden:
    def test_01a_semivariance_share_hand_golden(self):
        # window [0.01, -0.02, 0.03, -0.04]:
        #   SS = 1e-4 + 4e-4 + 9e-4 + 16e-4 = 30e-4
        #   DS = 4e-4 + 16e-4              = 20e-4   ->  S = 20/30 = 2/3
        assert semivariance_share([0.01, -0.02, 0.03, -0.04]) == pytest.approx(2.0 / 3.0)
        # all-positive window: DS = 0 -> S = 0 (maximum upside-heavy)
        assert semivariance_share([0.01, 0.02, 0.03]) == 0.0
        # all-negative window: DS = SS -> S = 1 (maximum downside-heavy)
        assert semivariance_share([-0.01, -0.02]) == 1.0
        # frozen 126-length golden: 120 days +0.001 and 6 days -0.002:
        #   SS = 120x1e-6 + 6x4e-6 = 144e-6 ; DS = 24e-6 -> S = 24/144 = 1/6
        w126 = [0.001] * 120 + [-0.002] * 6
        assert len(w126) == STATE_WINDOW_ANCHOR
        assert semivariance_share(w126) == pytest.approx(1.0 / 6.0)
        assert total_sum_sq(w126) == pytest.approx(144e-6)
        # zero-total window is undefined: fail closed, never guess
        with pytest.raises(Exception):
            semivariance_share([0.0] * 126)

    def test_01b_rank_ties_lex_golden(self):
        # descending by statistic; ties break lexicographically by symbol.
        assert rank_symbols({"B": 0.5, "A": 0.9, "C": 0.5, "D": 0.1}) == \
            ("A", "B", "C", "D")
        # mapping order never matters (determinism contract)
        assert rank_symbols({"D": 0.1, "C": 0.5, "A": 0.9, "B": 0.5}) == \
            ("A", "B", "C", "D")

    def test_01c_seed_book_and_targets_golden(self):
        # Hand windows of length 2 for the 11 frozen sector symbols.
        #   SS/DS per symbol (units 1e-4):
        #     XLB [0.02,-0.02]: SS 8  DS 4  -> S 0.50
        #     XLC [-0.03,-0.01]: SS 10 DS 10 -> S 1.00
        #     XLE [0.04, 0.02]: SS 20 DS 0  -> S 0.00
        #     XLF [-0.02,0.02]: SS 8  DS 4  -> S 0.50
        #     XLI [0.01, 0.01]: SS 2  DS 0  -> S 0.00
        #     XLK [-0.01, 0.0]: SS 1  DS 1  -> S 1.00
        #     XLP [0.0,-0.01]:  SS 1  DS 1  -> S 1.00
        #     XLRE[-0.04,0.03]: SS 25 DS 16 -> S 0.64
        #     XLU [0.03,-0.01]: SS 10 DS 1  -> S 0.10
        #     XLV [-0.01,-0.02]: SS 5 DS 5  -> S 1.00
        #     XLY [0.02, 0.01]: SS 5  DS 0  -> S 0.00
        # Descending S, ties lexicographic:
        #   XLC(1) XLK(2) XLP(3) XLV(4) | XLRE(5) XLB(6) XLF(7) XLU(8) |
        #   XLE(9) XLI(10) XLY(11)
        windows = {
            "XLB": [0.02, -0.02], "XLC": [-0.03, -0.01], "XLE": [0.04, 0.02],
            "XLF": [-0.02, 0.02], "XLI": [0.01, 0.01], "XLK": [-0.01, 0.0],
            "XLP": [0.0, -0.01], "XLRE": [-0.04, 0.03], "XLU": [0.03, -0.01],
            "XLV": [-0.01, -0.02], "XLY": [0.02, 0.01],
        }
        feats = {s: feature_value(w, "SEMIVARIANCE_SHARE") for s, w in windows.items()}
        ranks = rank_symbols(feats)
        assert ranks == (
            "XLC", "XLK", "XLP", "XLV", "XLRE", "XLB", "XLF", "XLU",
            "XLE", "XLI", "XLY",
        )
        state = seed_book(ranks)
        assert {s for s, v in state.items() if v == "LONG"} == \
            {"XLC", "XLK", "XLP", "XLV"}
        assert {s for s, v in state.items() if v == "SHORT"} == \
            {"XLU", "XLE", "XLI", "XLY"}
        tw = target_weights(state)
        for s in ("XLC", "XLK", "XLP", "XLV"):
            assert tw[s] == 0.25
        for s in ("XLU", "XLE", "XLI", "XLY"):
            assert tw[s] == -0.25
        assert tw[CASH_SYMBOL] == 1.0          # net exactly 0 on a 4/4 book
        assert sum(abs(v) for k, v in tw.items() if k != CASH_SYMBOL) == 2.0

    def test_01d_hysteresis_step_golden(self):
        # From the 01c seed, new ranks move XLV from rank 4 to rank 8 and XLB
        # from rank 6 to rank 4:
        #   new order: XLK(1) XLC(2) XLP(3) XLB(4) XLRE(5) XLF(6) XLU(7)
        #              XLV(8) XLE(9) XLI(10) XLY(11)
        # Exits (ascending rank): XLV (LONG, rank 8 >= 8) leaves; |SHORT| = 4
        #   (XLU,XLE,XLI,XLY) so XLV -> FLAT; |LONG| drops to 3.
        #   XLU (SHORT, rank 7) is in the 5-7 buffer -> RETAINED SHORT.
        # Entries: FLAT with rank <= 4: XLB -> LONG (|LONG| 3 < 4) -> 4.
        #   Short band: no FLAT candidate with |SHORT| < 4.
        # Final: LONG {XLK,XLC,XLP,XLB} SHORT {XLU,XLE,XLI,XLY}
        #        FLAT {XLRE,XLF,XLV}; net 0.
        prev = seed_book((
            "XLC", "XLK", "XLP", "XLV", "XLRE", "XLB", "XLF", "XLU",
            "XLE", "XLI", "XLY",
        ))
        new_ranks = (
            "XLK", "XLC", "XLP", "XLB", "XLRE", "XLF", "XLU", "XLV",
            "XLE", "XLI", "XLY",
        )
        state = step_book(prev, new_ranks)
        assert {s for s, v in state.items() if v == "LONG"} == \
            {"XLK", "XLC", "XLP", "XLB"}
        assert {s for s, v in state.items() if v == "SHORT"} == \
            {"XLU", "XLE", "XLI", "XLY"}
        assert {s for s, v in state.items() if v == "FLAT"} == \
            {"XLRE", "XLF", "XLV"}
        tw = target_weights(state)
        assert tw[CASH_SYMBOL] == 1.0

    def test_01e_frozen_constants_pinned(self):
        assert (CFG_A.state_window_sessions,
                CFG_N.state_window_sessions,
                CFG_C.state_window_sessions) == (
            STATE_WINDOW_ANCHOR, STATE_WINDOW_NEIGHBOUR, STATE_WINDOW_CONTROL)
        assert (STATE_WINDOW_ANCHOR, STATE_WINDOW_NEIGHBOUR,
                STATE_WINDOW_CONTROL) == (126, 63, 126)
        assert CFG_A.sort_statistic == "SEMIVARIANCE_SHARE"
        assert CFG_C.sort_statistic == "VARIANCE_LEVEL"
        assert (CLOCK_STEP_SESSIONS, CLOCK_ANCHOR_SESSION) == (21, "2018-04-04")
        assert CFG_A.leg_weight == CFG_N.leg_weight == CFG_C.leg_weight == 0.25
        for cfg in CFGS.values():
            assert cfg.digest == hashlib.sha256(
                json.dumps(cfg.to_payload(), sort_keys=True,
                           separators=(",", ":")).encode()
            ).hexdigest()
        assert len(set(arm_config_digests().values())) == 3


# =========================================================================== #
# 2. PIT / no-lookahead mutation tests
# =========================================================================== #
class Test02PitNoLookahead:
    def test_02a_window_is_exact_trailing_completed(self, ):
        panel = arithmetic_panel(SYN_SESSIONS)
        hbt = history_by_tick(CFG_A, SYN_SESSIONS, panel)
        i0 = clock_anchor_index(SYN_SESSIONS)
        decision, windows = hbt[0]
        assert decision == SYN_SESSIONS[i0]
        for s in SYMS:
            # exactly the W completed returns ENDING at the decision session
            assert windows[s] == panel[s][i0 - 126 + 1: i0 + 1]
            assert len(windows[s]) == 126
        # nothing after the decision session can appear in any window
        for decision, windows in hbt:
            i = SYN_SESSIONS.index(decision)
            for s in SYMS:
                assert windows[s][-1] == panel[s][i]

    def test_02b_future_mutation_cannot_change_past_targets(self):
        panel = arithmetic_panel(SYN_SESSIONS)
        i0 = clock_anchor_index(SYN_SESSIONS)
        mutated = {s: list(rs) for s, rs in panel.items()}
        # mutate sessions strictly AFTER the first decision: inside the gap
        # to the second tick and far beyond
        for k in range(i0 + 1, i0 + 60):
            for s in SYMS:
                mutated[s][k] = 0.5
        d0 = SYN_SESSIONS[i0]
        s1 = build_arm_schedule(CFG_A, SYN_SESSIONS,
                                history_by_tick(CFG_A, SYN_SESSIONS, panel))
        s2 = build_arm_schedule(CFG_A, SYN_SESSIONS,
                                history_by_tick(CFG_A, SYN_SESSIONS, mutated))
        # the trailing window at t is byte-identical under both panels
        w1 = dict(history_by_tick(CFG_A, SYN_SESSIONS, panel))[d0]
        w2 = dict(history_by_tick(CFG_A, SYN_SESSIONS, mutated))[d0]
        assert w1 == w2
        f1 = [f for f in s1.fills if f.decision_session == d0]
        f2 = [f for f in s2.fills if f.decision_session == d0]
        assert len(f1) == len(f2) == 1
        assert f1[0].to_payload() == f2[0].to_payload()
        assert s1.decision_sessions == s2.decision_sessions

    def test_02c_mutation_inside_window_is_visible(self):
        # sensitivity check: a mutation INSIDE the first decision's own
        # trailing window MUST move the control's level statistic (the
        # injected magnitude dominates the tiny panel variances), proving
        # that the 02b invariance assertion has detection power.
        panel = arithmetic_panel(SYN_SESSIONS)
        i0 = clock_anchor_index(SYN_SESSIONS)
        d0 = SYN_SESSIONS[i0]
        hbt = dict(history_by_tick(CFG_C, SYN_SESSIONS, panel))[d0]
        ranks_before = rank_symbols({s: total_sum_sq(hbt[s]) for s in SYMS})
        victim = ranks_before[-1]            # naturally ranked LAST
        mutated = {s: list(rs) for s, rs in panel.items()}
        mutated[victim][i0] = -0.5           # inside the window [i0-125, i0]
        hbt_m = dict(history_by_tick(CFG_C, SYN_SESSIONS, mutated))[d0]
        ranks_after = rank_symbols({s: total_sum_sq(hbt_m[s]) for s in SYMS})
        assert ranks_after[0] == victim      # mutated symbol jumps to rank 1
        assert ranks_before != ranks_after


# =========================================================================== #
# 3. next-allowed-session fill
# =========================================================================== #
class Test03NextSessionFill:
    def test_03a_fills_are_next_session_never_same(self):
        for cfg in CFGS.values():
            sched, _ = build_both(cfg, SYN_SESSIONS, arithmetic_panel(SYN_SESSIONS))
            assert sched.fills, cfg.arm_id
            for f in sched.fills:
                if f.decision_session is None:      # FORCE_FLAT bookkeeping
                    assert f.book_kind == "FORCE_FLAT"
                    continue
                assert f.fill_session != f.decision_session
                assert f.fill_session == next_session(
                    SYN_SESSIONS, f.decision_session)
                # fill and decision never straddle a fold boundary
                assert fold_of(f.fill_session) == fold_of(f.decision_session)
            # the very first decision of S0 (the anchor session) fills the
            # next allowed session, never on 2018-04-04 itself
            first = [f for f in sched.fills if f.decision_session is not None][0]
            assert first.decision_session == "2018-04-04"
            assert first.fill_session == "2018-04-05"


# =========================================================================== #
# 4. deterministic double generation
# =========================================================================== #
class Test04DoubleGeneration:
    def test_04a_two_paths_byte_identical_all_arms(self):
        panel = arithmetic_panel(SYN_SESSIONS)
        for cfg in CFGS.values():
            a, b = build_both(cfg, SYN_SESSIONS, panel)
            assert schedules_equal(a, b), cfg.arm_id
            assert a.canonical_json() == b.canonical_json()
            assert a.schedule_digest == b.schedule_digest

    def test_04b_rebuild_is_byte_stable(self):
        panel = arithmetic_panel(SYN_SESSIONS)
        s1, _ = build_both(CFG_A, SYN_SESSIONS, panel)
        panel_again = arithmetic_panel(SYN_SESSIONS)     # regenerated identically
        s2, _ = build_both(CFG_A, SYN_SESSIONS, panel_again)
        assert s1.schedule_digest == s2.schedule_digest
        # and the payload hashes to the pinned digest of its own bytes
        assert s1.schedule_digest == hashlib.sha256(
            s1.canonical_json().encode("utf-8")).hexdigest()

    def test_04c_periodic_panel_single_generation_across_arms(self):
        for cfg in CFGS.values():
            a, b = build_both(cfg, SYN_SESSIONS, periodic_panel(SYN_SESSIONS))
            assert schedules_equal(a, b)


# =========================================================================== #
# 5. split/dividend/TR correctness (adjusted closes for ALL returns)
# =========================================================================== #
def returns_from_closes(closes):
    return [closes[k] / closes[k - 1] - 1.0 for k in range(1, len(closes))]


class Test05SplitAdjusted:
    def _price_paths(self):
        # economic path: 130 closes growing deterministically (no splits)
        n = 130
        econ = []
        p = 100.0
        for k in range(n):
            econ.append(p)
            p *= 1.0 + 0.001 * (((7 * k) % 13) - 6) / 6.0
        split_at = 60     # 2:1 split effective at index 60
        raw = econ[:split_at] + [x / 2.0 for x in econ[split_at:]]
        # split+dividend ADJUSTED path (the _all convention): pre-split raw
        # closes carry the cumulative factor 0.5
        adjusted = [x * 0.5 for x in raw[:split_at]] + raw[split_at:]
        return econ, raw, adjusted, split_at

    def test_05a_adjusted_path_reproduces_economic_returns_exactly(self):
        econ, raw, adjusted, split_at = self._price_paths()
        r_econ = returns_from_closes(econ)
        r_adj = returns_from_closes(adjusted)
        assert len(r_adj) == len(r_econ)
        # 2 is a power of two, so the adjusted path is EXACTLY the economic
        # return series in IEEE arithmetic — the frozen rule "adjusted (_all)
        # closes for all return computations" is lossless here.
        assert r_adj == r_econ
        # the RAW path is corrupted exactly at the split boundary (~-50%)
        r_raw = returns_from_closes(raw)
        assert r_raw[split_at - 1] < -0.4
        assert abs(r_raw[split_at - 1] - r_econ[split_at - 1]) > 0.4

    def test_05b_synthetic_2_for_1_split_does_not_move_the_feature(self):
        econ, raw, adjusted, _ = self._price_paths()
        r_econ = returns_from_closes(econ)
        r_adj = returns_from_closes(adjusted)
        w = 126
        assert len(r_econ) >= w
        win_econ = r_econ[-w:]
        win_adj = r_adj[-w:]
        assert win_adj == win_econ                     # exact
        # the semivariance-share feature path is unchanged under the split
        assert semivariance_share(win_adj) == semivariance_share(win_econ)
        assert total_sum_sq(win_adj) == total_sum_sq(win_econ)
        # ...while the RAW (unadjusted) path WOULD have moved it
        assert semivariance_share(returns_from_closes(raw)[-w:]) != \
            semivariance_share(win_econ)

    def test_05c_full_split_panel_gives_identical_schedule(self):
        # a 2:1 split applied mid-history to EVERY symbol's raw path leaves
        # the adjusted-close feature path — and hence the whole synthetic
        # schedule — byte-identical to the unsplit run over the same closes.
        panel = arithmetic_panel(SYN_SESSIONS)
        start = {s: 50.0 + 7.0 * j for j, s in enumerate(SYMS)}
        econ_closes = {}
        for s, rs in panel.items():
            cs = [start[s]]
            for r in rs:
                cs.append(cs[-1] * (1.0 + r))
            econ_closes[s] = cs
        split_idx = clock_anchor_index(SYN_SESSIONS) - 40

        def to_returns(cs):
            rs = returns_from_closes(cs)
            return [rs[0]] + rs            # pad back to the session length

        plain_panel = {s: to_returns(cs) for s, cs in econ_closes.items()}
        split_panel = {}
        for s, cs in econ_closes.items():
            # raw market prices halve at the split; the adjusted (_all) path
            # multiplies pre-split closes by the cumulative factor 0.5
            raw = cs[:split_idx] + [c / 2.0 for c in cs[split_idx:]]
            adj = [c * 0.5 for c in raw[:split_idx]] + raw[split_idx:]
            split_panel[s] = to_returns(adj)
        # adjusted accounting reproduces the unsplit return paths EXACTLY
        assert split_panel == plain_panel
        s_plain, _ = build_both(CFG_A, SYN_SESSIONS, plain_panel)
        s_split, _ = build_both(CFG_A, SYN_SESSIONS, split_panel)
        assert s_plain.schedule_digest == s_split.schedule_digest
        # ...and the RAW path would NOT: it injects a ~-50% fake return at
        # every split boundary, so the feature windows differ
        raw_panel = {}
        for s, cs in econ_closes.items():
            raw = cs[:split_idx] + [c / 2.0 for c in cs[split_idx:]]
            raw_panel[s] = to_returns(raw)
        assert raw_panel != plain_panel


# =========================================================================== #
# 6. factor and kappa scale invariance (frozen fallback + trailing-252 OLS)
# =========================================================================== #
class Test06ScaleAndKappa:
    def test_06a_feature_scale_invariance(self):
        w = [0.012, -0.031, 0.007, -0.002, 0.045, -0.05]
        base_share = semivariance_share(w)
        base_level = total_sum_sq(w)
        for c in (10.0, 0.1, 1000.0):
            assert semivariance_share([c * x for x in w]) == \
                pytest.approx(base_share, rel=1e-12)
            assert total_sum_sq([c * x for x in w]) == \
                pytest.approx(base_level * c * c, rel=1e-12)

    def test_06b_decisions_invariant_under_10x_prices(self):
        panel = arithmetic_panel(SYN_SESSIONS)
        scaled = {s: [10.0 * r for r in rs] for s, rs in panel.items()}
        for cfg in CFGS.values():
            s1, _ = build_both(cfg, SYN_SESSIONS, panel)
            s2, _ = build_both(cfg, SYN_SESSIONS, scaled)
            assert s1.decision_sessions == s2.decision_sessions
            assert len(s1.fills) == len(s2.fills)
            for f1, f2 in zip(s1.fills, s2.fills):
                assert f1.fill_session == f2.fill_session
                assert f1.book_kind == f2.book_kind
                assert set(f1.targets) == set(f2.targets)
                for sym, v in f1.targets.items():
                    assert f2.targets[sym] == pytest.approx(v, abs=1e-12)

    def test_06c_kappa_fallback_below_252_scored_sessions(self):
        # frozen: 1.0 FLAT until 252 scored sessions accumulate — regardless
        # of what the data says (a perfect 3.0x relationship is ignored).
        spy = [0.001 * ((k % 7) - 3) for k in range(400)]
        arm = [3.0 * x for x in spy]
        assert kappa_frozen(arm[:251], spy[:251]) == 1.0
        assert kappa_frozen(arm[:10], spy[:10]) == 1.0
        assert kappa_frozen([], []) == 1.0

    def test_06d_kappa_ols_at_252_and_clip(self):
        # arm = 0.5 x SPY exactly: OLS slope 0.5 once 252 sessions exist
        spy = [0.001 * ((k % 7) - 3) for k in range(600)]
        arm_half = [0.5 * x for x in spy]
        assert kappa_frozen(arm_half[:251], spy[:251]) == 1.0
        assert kappa_frozen(arm_half[:252], spy[:252]) == pytest.approx(0.5)
        # beyond 252: trailing window only — a later regime change is seen,
        # an early one is forgotten (last 252 pairs govern)
        arm_late = [0.5 * x for x in spy[:300]] + [2.0 * x for x in spy[300:]]
        assert kappa_frozen(arm_late[:299], spy[:299]) == pytest.approx(0.5)
        assert kappa_frozen(arm_late[300:552], spy[300:552]) == pytest.approx(2.0)
        # clip band [0, 2] (proposal: kappa_t = clip(beta_hat, 0.0, 2.0))
        arm_3x = [3.0 * x for x in spy]
        assert kappa_frozen(arm_3x[:252], spy[:252]) == 2.0
        arm_neg = [-1.0 * x for x in spy]
        assert kappa_frozen(arm_neg[:252], spy[:252]) == 0.0
        # misaligned histories fail closed
        with pytest.raises(Exception):
            kappa_frozen(arm_half[:252], spy[:251])
        # zero-variance SPY window fails closed
        with pytest.raises(Exception):
            kappa_frozen(arm_half[:252], [0.0] * 252)

    def test_06e_ew_sector_factor_golden(self):
        # equal-weight, daily-rebalanced: the plain mean of available returns
        assert ew_sector_return({"XLB": 0.01, "XLC": -0.02}) == pytest.approx(-0.005)
        assert ew_sector_return({"XLB": 0.03}) == 0.03
        # XLC contributes only from inception: pre-inception sessions simply
        # exclude it from the mean
        assert ew_sector_return({s: 0.012 for s in SYMS[:10]}) == pytest.approx(0.012)
        with pytest.raises(Exception):
            ew_sector_return({})

    def test_06f_kappa_scales_with_arm_not_with_price_level(self):
        # scaling BOTH return series by 10x (a 10x price level) leaves the
        # OLS slope unchanged: beta is scale-free
        spy = [0.001 * ((k % 11) - 5) for k in range(252)]
        arm = [0.5 * x for x in spy]
        assert kappa_frozen([10 * a for a in arm], [10 * b for b in spy]) == \
            pytest.approx(kappa_frozen(arm, spy))


# =========================================================================== #
# 7. control != anchor (shape axis vs level axis)
# =========================================================================== #
class Test07ControlNotAnchor:
    def test_07a_control_ranking_differs_golden(self):
        # same hand windows as 01c: share ranking is
        #   XLC XLK XLP XLV | XLRE XLB XLF XLU | XLE XLI XLY
        # while the LEVEL ranking (SS descending, ties lex) is
        #   XLRE(25) XLE(20) XLC(10) XLU(10) XLB(8) XLF(8) XLV(5) XLY(5)
        #   XLI(2) XLK(1) XLP(1)   (units 1e-4)
        windows = {
            "XLB": [0.02, -0.02], "XLC": [-0.03, -0.01], "XLE": [0.04, 0.02],
            "XLF": [-0.02, 0.02], "XLI": [0.01, 0.01], "XLK": [-0.01, 0.0],
            "XLP": [0.0, -0.01], "XLRE": [-0.04, 0.03], "XLU": [0.03, -0.01],
            "XLV": [-0.01, -0.02], "XLY": [0.02, 0.01],
        }
        share_ranks = rank_symbols(
            {s: semivariance_share(w) for s, w in windows.items()})
        level_ranks = rank_symbols(
            {s: total_sum_sq(w) for s, w in windows.items()})
        assert share_ranks == (
            "XLC", "XLK", "XLP", "XLV", "XLRE", "XLB", "XLF", "XLU",
            "XLE", "XLI", "XLY")
        assert level_ranks == (
            "XLRE", "XLE", "XLC", "XLU", "XLB", "XLF", "XLV", "XLY",
            "XLI", "XLK", "XLP")
        # different axis -> different book at the seed
        a_state = seed_book(share_ranks)
        c_state = seed_book(level_ranks)
        assert target_weights(a_state) != target_weights(c_state)
        long_a = {s for s, v in a_state.items() if v == "LONG"}
        long_c = {s for s, v in c_state.items() if v == "LONG"}
        assert long_a != long_c

    def test_07b_control_differs_from_anchor_synthetic_run(self):
        panel = arithmetic_panel(SYN_SESSIONS)
        s_a, _ = build_both(CFG_A, SYN_SESSIONS, panel)
        s_c, _ = build_both(CFG_C, SYN_SESSIONS, panel)
        assert not schedules_equal(s_a, s_c)
        differing = 0
        for fa, fc in zip(s_a.fills, s_c.fills):
            assert fa.fill_session == fc.fill_session     # same clock/fills
            if dict(fa.targets) != dict(fc.targets):
                differing += 1
        assert differing > 0          # the books genuinely diverge

    def test_07c_different_decision_lists_on_real_schedule_dates(self):
        # REAL calendar dates + SYNTHETIC histories (no real return is ever
        # computed): on the real anchored decision sessions the two arms'
        # fill/book lists differ.
        sessions = _real_sessions()
        panel = arithmetic_panel(sessions)
        s_a, _ = build_both(CFG_A, sessions, panel)
        s_c, _ = build_both(CFG_C, sessions, panel)
        assert s_a.decision_sessions == s_c.decision_sessions
        assert s_a.decision_sessions[0] == "2018-04-04"
        assert not schedules_equal(s_a, s_c)
        books_a = [dict(f.targets) for f in s_a.fills if f.decision_session]
        books_c = [dict(f.targets) for f in s_c.fills if f.decision_session]
        assert books_a != books_c


# =========================================================================== #
# 8. cap / gross / net / CASH invariants
# =========================================================================== #
class Test08BookInvariants:
    def test_08a_gross_net_cash_on_every_fill_all_arms(self):
        for panel in (arithmetic_panel(SYN_SESSIONS),
                      periodic_panel(SYN_SESSIONS)):
            for cfg in CFGS.values():
                sched, _ = build_both(cfg, SYN_SESSIONS, panel)
                for f in sched.fills:
                    legs = {s: w for s, w in f.targets.items()
                            if s != CASH_SYMBOL}
                    gross = sum(abs(w) for w in legs.values())
                    net = sum(legs.values())
                    cash = f.targets.get(CASH_SYMBOL)
                    assert gross <= 2.0 + 1e-12
                    assert abs(net) <= 4 * LEG_WEIGHT + 1e-12
                    assert cash == pytest.approx(1.0 - net, abs=1e-12)
                    # every leg is exactly +-0.25 or absent
                    assert all(abs(w) == LEG_WEIGHT for w in legs.values())
                    # CASH is never a held sector leg
                    assert CASH_SYMBOL not in cfg.symbols

    def test_08b_cash_excluded_from_turnover(self):
        # hand case: {AAA: 0.5, CASH: 0.5} -> {AAA: 0.25, BBB: 0.5, CASH: 0.25}
        # hand sum |delta w| over NON-CASH legs = 0.25 + 0.5 = 0.75
        # (the naive CASH-inclusive sum would be 1.00 — forbidden)
        before = {"AAA": 0.5, CASH_SYMBOL: 0.5}
        after = {"AAA": 0.25, "BBB": 0.5, CASH_SYMBOL: 0.25}
        assert etf_leg_turnover(before, after) == 0.75
        # liquidation to all-CASH charges the leg once, not twice
        assert etf_leg_turnover({"AAA": 1.0}, {CASH_SYMBOL: 1.0}) == 1.0

    def test_08c_thin_short_side_net_quarter_is_expected_behavior(self):
        # 10 eligible sectors (XLC unavailable): ranks 1..10, short band
        # ranks 8..10 = 3 legs -> net +0.25, CASH absorbs +1.25 residual.
        # This is the structural mechanism behind the frozen note "9 ticks
        # net +0.25 anchor" in early fold 1 — recorded, never fixed.
        ranks_10 = ("S01", "S02", "S03", "S04", "S05", "S06", "S07",
                    "S08", "S09", "S10")
        state = seed_book(ranks_10)
        longs = [s for s, v in state.items() if v == "LONG"]
        shorts = [s for s, v in state.items() if v == "SHORT"]
        assert len(longs) == 4 and len(shorts) == 3
        tw = target_weights(state)
        assert sum(tw[s] for s in longs + shorts) == pytest.approx(0.25)
        assert tw[CASH_SYMBOL] == pytest.approx(0.75)   # residual 1 - net
        assert sum(abs(w) for s, w in tw.items() if s != CASH_SYMBOL) == \
            pytest.approx(1.75)
        # fewer than 8 eligible cannot form the book: fail closed
        with pytest.raises(Exception):
            seed_book(("S01", "S02", "S03", "S04", "S05", "S06", "S07"))


# =========================================================================== #
# 9. cost-once and turnover convention
# =========================================================================== #
class Test09CostOnceTurnover:
    def test_09a_turnover_equals_hand_abs_delta(self):
        panel = arithmetic_panel(SYN_SESSIONS)
        sched, _ = build_both(CFG_A, SYN_SESSIONS, panel)
        fills = [f for f in sched.fills if f.decision_session is not None]
        assert fills
        current = {CASH_SYMBOL: 1.0}
        for f in sched.fills:
            if f.book_kind == "FORCE_FLAT":
                hand = sum(abs(0.0 - current.get(s, 0.0))
                           for s in current if s != CASH_SYMBOL)
                assert f.turnover_one_way == pytest.approx(hand, abs=1e-12)
                current = {CASH_SYMBOL: 1.0}
                continue
            legs = (set(f.targets) | set(current)) - {CASH_SYMBOL}
            hand = sum(abs(float(f.targets.get(s, 0.0))
                           - float(current.get(s, 0.0))) for s in legs)
            assert f.turnover_one_way == pytest.approx(hand, abs=1e-12)
            assert f.turnover_one_way <= 4.0 + 1e-9   # full-book swap bound
            current = dict(f.targets)

    def test_09b_hysteresis_keeps_turnover_low_under_stable_ranking(self):
        # 21-periodic panel: every tick sees the SAME trailing window, so the
        # book never changes after the seed: per fold exactly ONE decision
        # fill (the seed) + the force-flat; ZERO rebalance fills.
        for cfg in CFGS.values():
            sched, _ = build_both(cfg, SYN_SESSIONS,
                                  periodic_panel(SYN_SESSIONS))
            rebals = [f for f in sched.fills if f.book_kind == "REBAL"]
            assert rebals == [], cfg.arm_id
            seeds = [f for f in sched.fills if f.book_kind == "SEED"]
            flats = [f for f in sched.fills if f.book_kind == "FORCE_FLAT"]
            assert len(seeds) == 3 and len(flats) == 3
            assert all(f.turnover_one_way > 0 for f in seeds)
            # each force-flat liquidates the full 4/4 book: 8 legs x 0.25
            assert all(f.turnover_one_way == pytest.approx(2.0, abs=1e-12)
                       for f in flats), [f.turnover_one_way for f in flats]
            # 90 decision ticks produced only 3 decision fills in total:
            # static weights + hysteresis keep churn structurally low
            assert len(seeds) + len(rebals) == 3

    def test_09c_cost_charged_exactly_once_per_fill(self):
        # canonical factory path, hand-computed: fill at D2 {AAA: 1.0},
        # cost = 1.0 (equity) x 1.0 (turnover) x 10/1e4 = 0.001 charged ONCE;
        # D3 earns +10% on 0.999 -> 1.0989; D5 rebalance to {AAA: 0.5} moves
        # 0.5 of weight -> second cost 1.0989 x 0.5 x 0.001 = 0.00054945.
        sessions = ["2018-01-02", "2018-01-03", "2018-01-04", "2018-01-05"]
        closes = {"AAA": {"2018-01-02": 100.0, "2018-01-03": 100.0,
                          "2018-01-04": 110.0, "2018-01-05": 110.0}}
        entries = [
            {"entry_type": "FILL", "fill_date": "2018-01-03",
             "targets": {"AAA": 1.0}},
            {"entry_type": "FILL", "fill_date": "2018-01-05",
             "targets": {"AAA": 0.5}},
        ]
        result = value_book(entries, closes, {}, {}, sessions, cost_bps=10.0)
        assert len(result.fill_costs) == 2
        assert result.total_cost == pytest.approx(0.001 + 0.00054945, rel=1e-9)
        assert result.fill_costs[0][2] == pytest.approx(0.001, rel=1e-12)
        assert result.fill_costs[1][2] == pytest.approx(0.00054945, rel=1e-9)
        # equity path: 1.0 -> (fill) 0.999 -> 1.0989 -> (fill) 1.09835055
        assert result.equity_curve["2018-01-04"] == pytest.approx(1.0989, rel=1e-12)
        assert result.equity_curve["2018-01-05"] == pytest.approx(1.09835055, rel=1e-12)
        assert result.total_pnl == pytest.approx(0.09835055, rel=1e-9)
        # the cost accumulator equals the fsum of per-fill costs (no
        # double-add): asserted structurally
        assert result.total_cost == pytest.approx(
            sum(c for _, _, c in result.fill_costs), rel=1e-12)


# =========================================================================== #
# real-snapshot read-only helpers (DATES ONLY, S0-bounded, pin-verified)
# =========================================================================== #
from research.stocks_free_v3.authority import (   # noqa: E402  (read-only import)
    SNAPSHOT_PINS,
    SNAPSHOT_STAGING_PATH,
    sha256_file,
)

STAGING = Path(SNAPSHOT_STAGING_PATH)


def _staging_available() -> bool:
    needed = ["SPY_all_p1.json"] + [f"{s}_all_p1.json" for s in SYMS]
    return STAGING.is_dir() and all((STAGING / n).is_file() for n in needed)


def _real_dates(filename: str) -> list[str]:
    """Pin-verified, S0-bounded SESSION DATES only (never a price)."""
    path = STAGING / filename
    actual = sha256_file(path)
    assert actual == SNAPSHOT_PINS[filename], filename
    payload = json.loads(path.read_text(encoding="utf-8"))
    dates = sorted(v["datetime"] for v in payload["values"])
    bounded = [d for d in dates if d <= "2025-07-31"]
    # S1 seal: nothing at or beyond 2025-08-01 is retained or read further
    assert all(d < "2025-08-01" for d in bounded)
    return bounded


_REAL_CACHE: dict[str, list[str]] = {}


def _real_sessions() -> list[str]:
    if "SPY" not in _REAL_CACHE:
        _REAL_CACHE["SPY"] = _real_dates("SPY_all_p1.json")
    return _REAL_CACHE["SPY"]


def _real_symbol_sessions() -> dict[str, list[str]]:
    for s in SYMS:
        if s not in _REAL_CACHE:
            _REAL_CACHE[s] = _real_dates(f"{s}_all_p1.json")
    return {s: _REAL_CACHE[s] for s in SYMS}


# =========================================================================== #
# 10. schedule-only feasibility on the REAL snapshot
# =========================================================================== #


_FEASIBILITY_CACHE: dict | None = None


def _real_feasibility():
    global _FEASIBILITY_CACHE
    if _FEASIBILITY_CACHE is None:
        _FEASIBILITY_CACHE = schedule_only_feasibility(
            _real_sessions(), _real_symbol_sessions())
    return _FEASIBILITY_CACHE


@pytest.mark.skipif(not _staging_available(), reason="staging snapshot absent")
class Test10RealScheduleOnly:
    @pytest.fixture
    def feasibility(self):
        return _real_feasibility()

    def test_10a_real_anchored_clock_and_counts(self, feasibility):
        clock = feasibility["clock"]
        assert clock["anchor_session"] == "2018-04-04"
        assert clock["anchor_index_in_calendar"] == 2076     # pre-S0 runway
        assert clock["calendar_first"] == "2010-01-04"
        assert clock["calendar_last"] <= "2025-07-31"
        counts = {}
        for key, arm in feasibility["arms"].items():
            assert arm["n_decisions_total"] == 87
            assert arm["decisions_total_floor_ok"] is True
            for fold_id, fold in arm["folds"].items():
                counts.setdefault(fold_id, fold["n_decisions"])
                assert fold["n_decisions"] == 29, (key, fold_id)
                assert fold["decisions_per_fold_floor_ok"] is True
                # the global clock anchors every fold to 2018-04-04
                assert fold["decision_sessions"] == sorted(
                    fold["decision_sessions"])
                assert fold["first_decision"] is not None
            # every decision fills at the NEXT allowed session
            for fold in arm["folds"].values():
                for d, f in zip(fold["decision_sessions"],
                                fold["fill_sessions"]):
                    assert f != d
                    assert f == next_session(_real_sessions(), d)
            fold1 = arm["folds"]["S0_FOLD_1"]
            assert fold1["first_decision"] == "2018-04-04"
            assert fold1["first_fill"] == "2018-04-05"
        assert counts == {"S0_FOLD_1": 29, "S0_FOLD_2": 29, "S0_FOLD_3": 29}

    def test_10b_real_warmup_and_xlc_availability(self, feasibility):
        # warmup: every ELIGIBLE symbol has its full state window at every
        # tick; the pre-S0 runway covers the 10 legacy sectors from tick 0
        arm_a = feasibility["arms"]["A"]
        assert arm_a["warmup_available_at_every_tick"] is True
        assert arm_a["min_eligible_sectors_at_any_tick"] == 10   # never < 10
        assert arm_a["folds"]["S0_FOLD_1"]["ticks_below_full_book"] == []
        # XLC availability rule: XLC (inception 2018-06-19) is excluded from
        # ranks until it holds a full 126-session history -> the anchor's
        # thin period is exactly the frozen "9 ticks" of fold 1; full
        # universe from 2019-01-03 (neighbour, 63 sessions: 2018-10-02).
        sym_sessions = _real_symbol_sessions()
        xlc = sym_sessions["XLC"]
        assert xlc[0] == "2018-06-19"
        arm_n = feasibility["arms"]["N"]
        fold1 = arm_a["folds"]["S0_FOLD_1"]
        thin = [t for t, c in zip(fold1["decision_sessions"],
                                  fold1["eligible_count_per_tick"]) if c < 11]
        assert len(thin) == 9                  # frozen expected behavior
        assert thin[0] == "2018-04-04"
        assert arm_a["first_tick_full_universe"] == "2019-01-03"
        assert arm_n["first_tick_full_universe"] == "2018-10-02"
        # the thin ticks hold exactly 10 eligible sectors (the legacy set)
        for t in thin:
            elig = eligibility(sym_sessions, t, 126, SYMS)
            assert len(elig) == 10 and "XLC" not in elig

    def test_10c_real_force_flat_and_fold_discipline(self, feasibility):
        sessions = _real_sessions()
        real = set(sessions)
        for key, arm in feasibility["arms"].items():
            for fold_id, fold in arm["folds"].items():
                # force-flat boundary is the fold end; no decision or fill
                # crosses it
                assert fold["force_flat_session"] == fold["fold_end"]
                assert fold["last_fill"] <= fold["fold_end"]
                assert fold["first_fill"] >= fold["fold_start"]
                for s in fold["decision_sessions"] + fold["fill_sessions"]:
                    assert fold_of(s) == fold_id
                # folds contain only real SPY sessions
                assert all(s in real
                           for s in fold["decision_sessions"])


# =========================================================================== #
# 11. meaningful held-max-weight drop-one
# =========================================================================== #
class Test11DropOne:
    def _synthetic_valuation(self, excluded=None):
        sessions = ["2018-01-02", "2018-01-03", "2018-01-04", "2018-01-05",
                    "2018-01-08", "2018-01-09"]
        closes = {
            "AAA": {"2018-01-02": 100.0, "2018-01-03": 100.0,
                    "2018-01-04": 110.0, "2018-01-05": 110.0,
                    "2018-01-08": 99.0, "2018-01-09": 99.0},
            "BBB": {"2018-01-02": 50.0, "2018-01-03": 50.0,
                    "2018-01-04": 50.0, "2018-01-05": 52.0,
                    "2018-01-08": 52.0, "2018-01-09": 52.0},
        }
        entries = [
            {"entry_type": "FILL", "fill_date": "2018-01-03",
             "targets": {"AAA": 1.0}},
            {"entry_type": "FILL", "fill_date": "2018-01-05",
             "targets": {"AAA": 0.5, "BBB": 0.5}},
        ]
        result = value_book(entries, closes, {}, {}, sessions,
                            cost_bps=10.0, excluded_symbol=excluded)
        return result

    def test_11a_drop_max_contribution_changes_book(self):
        result = self._synthetic_valuation()
        assert result.attribution_residual == pytest.approx(0.0, abs=1e-12)
        contribution = result.symbol_contribution
        assert set(contribution) == {"AAA", "BBB"}
        # AAA: 0.999 x 1.0 x 0.10 = +0.0999 then 0.999 x (110/99 - 1) x 0.5
        # contributions differ in sign and size; the max |contribution| leg
        # is selected deterministically (ties lexicographic)
        weights = {"AAA": 0.5, "BBB": 0.5, CASH_SYMBOL: 0.0}
        drop = select_drop_one_symbol(contribution, weights)
        assert drop in ("AAA", "BBB")
        assert abs(contribution[drop]) == max(abs(v) for v in contribution.values())
        rerun = self._synthetic_valuation(excluded=drop)
        # the book changes MATERIALLY: different symbols, different pnl
        assert rerun.total_pnl != pytest.approx(result.total_pnl, rel=1e-9)
        # and the family pipeline path: dropping one frozen-universe member
        # (deterministically the first short-band leg of the seed ranking)
        # re-seeds a different 4/4 book and different targets
        ranks = tuple(SYMS)
        state_full = seed_book(ranks)
        dropped_leg = sorted(s for s, v in state_full.items()
                             if v == "SHORT")[0]
        state_drop = seed_book(tuple(s for s in ranks if s != dropped_leg))
        assert state_drop != state_full
        assert len([s for s, v in state_drop.items() if v == "SHORT"]) == 3
        assert target_weights(state_drop) != target_weights(state_full)


# =========================================================================== #
# 12. dummy publication / refusal / replay on a TEMP ledger only
# =========================================================================== #
class Test12LedgerDiscipline:
    def test_12a_dummy_publish_replay_refuse_temp_path_only(self, tmp_path):
        canonical = Path("research/control/stocks_free_v4_run/event_log.jsonl")
        before = canonical.read_bytes() if canonical.is_file() else None
        ledger = GatedTrialLedger(str(tmp_path / "ledger.json"))
        assert ledger.path == str(tmp_path / "ledger.json")
        artifact = {
            "kind": "DUMMY_SCHEDULE_ONLY",
            "family_id": FAMILY_ID,
            "arm_id": CFG_A.arm_id,
            "scored": False,
            "real_pnl": False,
            "note": "synthetic fixture artifact; carries no scored metric",
        }
        ledger.compute_recorded("trial.A.synthetic")
        assert ledger.observed == 1            # observed increments once
        published = ledger.publish_result(
            "trial.A.synthetic", artifact, n_fill_events=3, n_held_positions=8)
        assert published is True
        assert ledger.observed == 1            # publication adds no increment
        replay = ledger.publish_result(
            "trial.A.synthetic", artifact, n_fill_events=3, n_held_positions=8)
        assert replay is False                 # replay is zero-delta
        assert ledger.observed == 1
        # refusal on zero positions (and zero fills): refused, never published
        ledger.compute_recorded("trial.empty")
        refused = ledger.publish_result(
            "trial.empty", artifact, n_fill_events=0, n_held_positions=0)
        assert refused is False
        assert ledger.refusals == [
            {"key": "trial.empty",
             "reasons": ["ZERO_FILL_EVENTS", "ZERO_HELD_POSITIONS"]}]
        assert "trial.empty" not in ledger.published_keys
        assert ledger.observed == 2            # compute recorded, publish refused
        ledger.save()
        saved = json.loads((tmp_path / "ledger.json").read_text())
        assert saved["observed"] == 2
        assert sorted(saved["published_keys"]) == ["trial.A.synthetic"]
        assert any(e.get("event") == "PUBLICATION_REFUSED_ZERO_RESULT"
                   for e in saved["entries"])
        assert any(e.get("event") == "REPLAY_ZERO_DELTA"
                   for e in saved["entries"])
        # the canonical ledger was never touched
        after = canonical.read_bytes() if canonical.is_file() else None
        assert before == after
