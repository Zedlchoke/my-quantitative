"""Sprint V2 canonical position-PF regression tests (owner A3).

All fixtures are HAND-CALCULATED (PLAN section 8.2, gate H9
POSITION_PF_REGRESSION_PASS).  Pure functions only -- the backtest engine is
NOT imported.  Covers: mixed winners/losers, winner-only (PF undefined +
``no_losing_positions``), loser-only / near-zero PF, empty set
(``no_trades``), funding flipping a winner into a loser, and the
reconciliation identity sum(positions) == net_pnl == sum(fold nets) at
tolerance 1e-9.
"""

from __future__ import annotations

import pytest

from contracts.protocol import position_pnl_stats
from research.matrix_runner import _position_stats_from_pnls

TOL = 1e-9


# --------------------------------------------------------------------------- #
# Mixed winners/losers -- hand-computed
# --------------------------------------------------------------------------- #
def test_mixed_winners_and_losers_hand_computed():
    # gross_profit = 100 + 60 = 160 ; gross_loss = |-40 + -25.5| = 65.5
    # PF = 160 / 65.5 = 2.4427480916030534... ; net = 94.5 ; trades = 4
    pnls = [100.0, -40.0, 60.0, -25.5]
    stats = position_pnl_stats(pnls)
    assert stats.trades == 4
    assert abs(stats.gross_profit - 160.0) <= TOL
    assert abs(stats.gross_loss - 65.5) <= TOL
    assert abs(stats.net_pnl - 94.5) <= TOL
    assert stats.pf_reason is None
    assert abs(stats.profit_factor - 160.0 / 65.5) <= 1e-12


def test_zero_pnl_positions_count_as_trades_but_neither_win_nor_loss():
    # gp=5, gl=5 -> PF exactly 1.0; the flat trade still counts as a trade.
    stats = position_pnl_stats([5.0, 0.0, -5.0])
    assert stats.trades == 3
    assert abs(stats.gross_profit - 5.0) <= TOL
    assert abs(stats.gross_loss - 5.0) <= TOL
    assert stats.profit_factor == 1.0


def test_pf_sign_convention_negative_gross_loss_is_impossible():
    stats = position_pnl_stats([-10.0, -4.0])
    assert stats.gross_loss == 14.0 and stats.gross_profit == 0.0
    assert stats.profit_factor == 0.0


# --------------------------------------------------------------------------- #
# Winner-only: PF undefined + no_losing_positions (never infinity)
# --------------------------------------------------------------------------- #
def test_winner_only_pf_none_with_reason_no_losing_positions():
    pnls = [10.0, 20.0, 30.0]  # gross_profit=60, gross_loss=0
    for stats in (position_pnl_stats(pnls), _stats_of(_position_stats_from_pnls(pnls))):
        assert stats.trades == 3
        assert abs(stats.gross_profit - 60.0) <= TOL
        assert stats.gross_loss == 0.0
        assert stats.net_pnl == 60.0
        assert stats.profit_factor is None
        assert stats.pf_reason == "no_losing_positions"


def test_winner_only_single_huge_winner_does_not_autopass():
    # A single +1_000_000 winner must stay undefined-PF, not infinite.
    stats = position_pnl_stats([1_000_000.0])
    assert stats.profit_factor is None
    assert stats.pf_reason == "no_losing_positions"


# --------------------------------------------------------------------------- #
# Loser-only and near-total-loss: exact small PFs
# --------------------------------------------------------------------------- #
def test_loser_only_pf_exact_zero():
    # gp=0, gl=42.5 -> PF = 0/42.5 = 0.0 exactly.
    stats = position_pnl_stats([-10.0, -30.0, -2.5])
    assert stats.trades == 3
    assert stats.gross_profit == 0.0
    assert abs(stats.gross_loss - 42.5) <= TOL
    assert stats.profit_factor == 0.0
    assert stats.pf_reason is None


def test_pf_exact_tenth_from_hand_picked_pair():
    # gp=1.25, gl=12.5 -> PF = 0.1 exactly (representable in binary FP).
    stats = position_pnl_stats([1.25, -12.5])
    assert stats.profit_factor == 0.1
    assert abs(stats.net_pnl - (-11.25)) <= TOL


# --------------------------------------------------------------------------- #
# Empty set: everything null + no_trades
# --------------------------------------------------------------------------- #
def test_empty_position_set_is_null_with_no_trades_reason():
    stats = position_pnl_stats([])
    assert stats.trades == 0
    assert stats.gross_profit == 0.0 and stats.gross_loss == 0.0 and stats.net_pnl == 0.0
    assert stats.profit_factor is None
    assert stats.pf_reason == "no_trades"
    as_dict = _position_stats_from_pnls([])
    assert as_dict["profit_factor"] is None and as_dict["pf_reason"] == "no_trades"


# --------------------------------------------------------------------------- #
# Funding flips a winner into a loser (pre/post funding accounting)
# --------------------------------------------------------------------------- #
def test_funding_flips_winner_to_loser_below_one():
    # Pre-funding: [100, -30] -> gp=100, gl=30, PF=3.333... (healthy).
    pre = [100.0, -30.0]
    pre_stats = position_pnl_stats(pre)
    assert pre_stats.profit_factor == pytest.approx(10.0 / 3.0)

    # A -80 USDT funding cashflow lands on the winning position:
    # post-funding [20, -30] -> gp=20, gl=30, PF=0.666... < 1 (edge gone).
    post = [20.0, -30.0]
    post_stats = position_pnl_stats(post)
    assert post_stats.profit_factor < 1.0
    assert post_stats.profit_factor == pytest.approx(2.0 / 3.0)
    assert pre_stats.net_pnl == pytest.approx(70.0)
    assert post_stats.net_pnl == pytest.approx(-10.0)


def test_funding_charge_turns_winner_only_into_all_losers():
    # Pre-funding single winner 50 (PF undefined); funding -60 -> [-10]:
    # winner-only becomes loser-only with PF exactly 0.0.
    assert position_pnl_stats([50.0]).pf_reason == "no_losing_positions"
    post = position_pnl_stats([-10.0])
    assert post.profit_factor == 0.0 and post.pf_reason is None


def test_funding_neutral_case_keeps_accounting_identity():
    # funding_net = 0 leaves every stat untouched (identity, tolerance 1e-9).
    before = position_pnl_stats([40.0, -15.0])
    after = position_pnl_stats([40.0 + 0.0, -15.0 + 0.0])
    assert abs(before.gross_profit - after.gross_profit) <= TOL
    assert abs(before.gross_loss - after.gross_loss) <= TOL
    assert abs((before.profit_factor or 0) - (after.profit_factor or 0)) <= TOL


# --------------------------------------------------------------------------- #
# Reconciliation: sum(positions) == cell net == sum(fold nets), tol 1e-9
# --------------------------------------------------------------------------- #
FOLD_POSITION_PNLS = [
    [12.5, -3.25, 7.75],          # fold 0 net = 17.0
    [-8.125, 21.0625, -1.0],      # fold 1 net = 11.9375
    [4.5, -14.25, 0.0, 33.75],    # fold 2 net = 24.0
]


def test_reconciliation_positions_equal_folds_within_1e_9():
    all_positions = [pnl for fold in FOLD_POSITION_PNLS for pnl in fold]
    fold_nets = [sum(fold) for fold in FOLD_POSITION_PNLS]
    cell = position_pnl_stats(all_positions)

    assert abs(sum(all_positions) - sum(fold_nets)) <= TOL
    assert abs(cell.net_pnl - sum(fold_nets)) <= TOL
    assert cell.trades == sum(len(fold) for fold in FOLD_POSITION_PNLS) == 10
    # Hand-computed aggregates over the 10 positions:
    # gross_profit = 12.5+7.75+21.0625+4.5+33.75 = 79.5625
    # gross_loss   = 3.25+8.125+1.0+14.25        = 26.625
    assert abs(cell.gross_profit - 79.5625) <= TOL
    assert abs(cell.gross_loss - 26.625) <= TOL
    assert abs(cell.profit_factor - 79.5625 / 26.625) <= 1e-12


def test_reconciliation_via_matrix_runner_helper_matches_contract():
    all_positions = [pnl for fold in FOLD_POSITION_PNLS for pnl in fold]
    helper = _position_stats_from_pnls(all_positions)
    contract = position_pnl_stats(all_positions)
    assert helper["trades"] == contract.trades
    assert abs(helper["gross_profit"] - contract.gross_profit) <= TOL
    assert abs(helper["gross_loss"] - contract.gross_loss) <= TOL
    assert abs(helper["net_pnl"] - contract.net_pnl) <= TOL
    assert helper["profit_factor"] == pytest.approx(contract.profit_factor, abs=TOL)
    assert helper["pf_reason"] == contract.pf_reason


def test_runner_helper_dict_shape_is_json_ready():
    helper = _position_stats_from_pnls([2.0, -1.0])
    assert set(helper) == {
        "trades", "gross_profit", "gross_loss", "net_pnl",
        "profit_factor", "pf_reason",
    }
    assert isinstance(helper["trades"], int)
    assert all(
        helper[key] is None or isinstance(helper[key], float)
        for key in ("gross_profit", "gross_loss", "net_pnl", "profit_factor")
    )
    assert helper["pf_reason"] is None


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
class _StatsShim:
    """Attribute view over the runner's dict output for dual-path assertions."""

    def __init__(self, payload: dict):
        self.trades = payload["trades"]
        self.gross_profit = payload["gross_profit"]
        self.gross_loss = payload["gross_loss"]
        self.net_pnl = payload["net_pnl"]
        self.profit_factor = payload["profit_factor"]
        self.pf_reason = payload["pf_reason"]


def _stats_of(payload: dict) -> _StatsShim:
    return _StatsShim(payload)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
