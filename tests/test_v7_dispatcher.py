"""V7P dispatcher contract tests (PLAN section 6.1; agent A3).

Covers the funding_price_divergence routing in
``research.portfolio_runner._signal_family_dispatch``:

* PIT safety -- future daily closes and future funding settlements must
  never influence selection (cutoff is inclusive ``<=``);
* reverse control swaps sides end-to-end INCLUDING the weight sign;
* missing panel input fails closed with reason
  ``divergence_panel_incomplete`` propagated;
* derived diagnostics rows are attached and labeled;
* CLI/env propagation: flags map to PORTFOLIO_SIGNAL_FAMILY, last flag on
  the command line wins, inherited env survives when neither flag is set,
  and a clean-env ``--help`` subprocess keeps default momentum behavior.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

DAY_MS = 86_400_000
DAY_NS = 86_400_000_000_000
# Fixed cutoff: 2023-11-14T22:13:20Z (day-aligned ns stamp).
CUTOFF_NS = 1_700_000_000 * 1_000_000_000
CUTOFF_MS = CUTOFF_NS // 1_000_000

SYMS = ("AAAUSDT", "BBBUSDT", "CCCUSDT", "DDDUSDT")
# Price legs (4 completed closes <= cutoff => 3-day return):
#   AAA .10 > BBB .04 > CCC .02 > DDD -.01
BASE_CLOSES = {
    "AAAUSDT": [100.0, 100.0, 100.0, 110.0],
    "BBBUSDT": [100.0, 100.0, 100.0, 104.0],
    "CCCUSDT": [100.0, 100.0, 100.0, 102.0],
    "DDDUSDT": [100.0, 100.0, 100.0, 99.0],
}
# Funding means over [cutoff-3d, cutoff] (one settlement/day):
#   AAA -.05 < BBB .03 < CCC .06 < DDD .10
BASE_RATES = {
    "AAAUSDT": [-0.05, -0.05, -0.05],
    "BBBUSDT": [0.03, 0.03, 0.03],
    "CCCUSDT": [0.06, 0.06, 0.06],
    "DDDUSDT": [0.10, 0.10, 0.10],
}
BASE_LONGS = ["AAAUSDT", "BBBUSDT"]
BASE_SHORTS = ["CCCUSDT", "DDDUSDT"]


def _daily_closes(extra_future: dict[str, float] | None = None) -> dict:
    """Closes at cutoff-3d..cutoff; optional FUTURE bar at cutoff+1d."""
    closes = {
        sym: [(CUTOFF_NS - (3 - i) * DAY_NS, px)
              for i, px in enumerate(rows)]
        for sym, rows in BASE_CLOSES.items()
    }
    for sym, px in (extra_future or {}).items():
        closes[sym] = [*closes[sym], (CUTOFF_NS + DAY_NS, px)]
    return closes


def _write_bundles(root: Path,
                   extra_future_rate: tuple[str, float] | None = None) -> None:
    for sym, rates in BASE_RATES.items():
        rows = [{"fundingTime": CUTOFF_MS - (3 - i) * DAY_MS,
                 "fundingRate": str(rate)}
                for i, rate in enumerate(rates)]
        if extra_future_rate is not None and extra_future_rate[0] == sym:
            # Settlement AFTER the decision cutoff (would move the mean).
            rows.append({"fundingTime": CUTOFF_MS + DAY_MS // 24,
                         "fundingRate": str(extra_future_rate[1])})
        bundle_dir = root / sym
        bundle_dir.mkdir(parents=True, exist_ok=True)
        (bundle_dir / "funding.json").write_text(json.dumps({
            "requested_start_ms": CUTOFF_MS - 5 * DAY_MS,
            "requested_end_ms": CUTOFF_MS + 2 * DAY_MS,
            "rows": rows,
        }), encoding="utf-8")


@pytest.fixture()
def divergence_env(monkeypatch):
    monkeypatch.setenv("PORTFOLIO_SIGNAL_FAMILY", "funding_price_divergence")


@pytest.fixture()
def family_env_guard():
    """Restore PORTFOLIO_SIGNAL_FAMILY even when code under test mutates
    os.environ DIRECTLY (apply_signal_family_flags bypasses monkeypatch)."""
    sentinel = object()
    original = os.environ.get("PORTFOLIO_SIGNAL_FAMILY", sentinel)
    yield
    if original is sentinel:
        os.environ.pop("PORTFOLIO_SIGNAL_FAMILY", None)
    else:
        os.environ["PORTFOLIO_SIGNAL_FAMILY"] = original


def _dispatch(tmp_path: Path, **kwargs) -> dict:
    from research.portfolio_runner import _signal_family_dispatch

    def _base_fail(**_kw):  # pragma: no cover - base must never run here
        pytest.fail("base momentum fn invoked under divergence family")

    wrapped = _signal_family_dispatch(_base_fail, tmp_path)
    assert wrapped is not _base_fail
    params = {
        "daily_closes": kwargs.pop("daily_closes"),
        "signal_cutoff_ns": kwargs.pop("signal_cutoff_ns", CUTOFF_NS),
        "lookback_days": kwargs.pop("lookback_days", 3),
        "reverse": kwargs.pop("reverse", False),
        **kwargs,
    }
    return wrapped(**params)


def test_baseline_selection_and_weights(tmp_path, divergence_env):
    _write_bundles(tmp_path)
    out = _dispatch(tmp_path, daily_closes=_daily_closes())
    assert out["status"] == "OK"
    # avg_rank/n percentiles: price pct AAA 1.0 > BBB .75 > CCC .5 > DDD .25;
    # funding pct AAA .25 < BBB .5 < CCC .75 < DDD 1.0 =>
    # scores AAA .75 > BBB .25 > CCC -.25 > DDD -.75; +-target_gross/4.
    assert [list(x) for x in out["longs"]] == [["BBBUSDT", 0.2],
                                               ["AAAUSDT", 0.2]]
    assert [list(x) for x in out["shorts"]] == [["DDDUSDT", -0.2],
                                                ["CCCUSDT", -0.2]]


def test_future_daily_close_excluded_from_selection(tmp_path, divergence_env):
    """A later bar that WOULD flip the ranking must be ignored (<= cutoff)."""
    _write_bundles(tmp_path)
    # With the +500% future bar included, DDD would top price ranks and the
    # selection would become longs {AAA, DDD} / shorts {BBB, CCC}.
    out = _dispatch(tmp_path, daily_closes=_daily_closes({"DDDUSDT": 600.0}))
    assert out["status"] == "OK"
    assert sorted(s for s, _ in out["longs"]) == BASE_LONGS
    assert sorted(s for s, _ in out["shorts"]) == BASE_SHORTS


def test_future_funding_excluded_from_selection(tmp_path, divergence_env):
    """Settlements after the cutoff must not move the funding mean."""
    _write_bundles(tmp_path, extra_future_rate=("AAAUSDT", 10.0))
    # Including the +10.0 future rate would push AAA's funding mean to ~+2.46
    # and flip the selection to longs {BBB} + ... / shorts {DDD, AAA}.
    out = _dispatch(tmp_path, daily_closes=_daily_closes())
    assert out["status"] == "OK"
    assert sorted(s for s, _ in out["longs"]) == BASE_LONGS
    assert sorted(s for s, _ in out["shorts"]) == BASE_SHORTS


def test_reverse_swaps_sides_including_sign(tmp_path, divergence_env):
    _write_bundles(tmp_path)
    base = _dispatch(tmp_path, daily_closes=_daily_closes())
    rev = _dispatch(tmp_path, daily_closes=_daily_closes(), reverse=True)
    assert rev["status"] == "OK"
    # Sides swap AND weights negate end-to-end (sign flip included).
    assert [list(x) for x in rev["longs"]] == [
        [s, -w] for s, w in base["shorts"]]
    assert [list(x) for x in rev["shorts"]] == [
        [s, -w] for s, w in base["longs"]]
    assert all(w > 0 for _, w in rev["longs"])
    assert all(w < 0 for _, w in rev["shorts"])


@pytest.mark.parametrize("drop", ["funding_bundle", "close_history"])
def test_missing_input_fails_closed_with_reason(
        tmp_path, divergence_env, drop):
    _write_bundles(tmp_path)
    if drop == "funding_bundle":
        shutil.rmtree(tmp_path / "CCCUSDT")
        closes = _daily_closes()
    else:
        closes = _daily_closes()
        closes["DDDUSDT"] = closes["DDDUSDT"][:2]  # < lookback+1 bars
    out = _dispatch(tmp_path, daily_closes=closes)
    assert out == {"status": "SKIP_INCOMPLETE",
                   "reason_code": "divergence_panel_incomplete"}


def test_derived_diagnostics_row_attached_and_labeled(
        tmp_path, divergence_env):
    _write_bundles(tmp_path)
    out = _dispatch(tmp_path, daily_closes=_daily_closes())
    diag = out["_divergence_diagnostics"]
    assert diag["derived_diagnostics"] is True
    assert diag["signal_cutoff_ns"] == CUTOFF_NS
    per = diag["per_symbol"]["AAAUSDT"]
    assert per["price_return"] == pytest.approx(0.10, abs=1e-12)
    assert per["funding_mean"] == pytest.approx(-0.05, abs=1e-12)
    assert per["price_percentile"] == pytest.approx(1.0)
    assert per["funding_percentile"] == pytest.approx(0.25)
    assert per["score"] == pytest.approx(0.75)
    assert sorted(s for s, _ in diag["selected_longs"]) == BASE_LONGS
    assert sorted(s for s, _ in diag["selected_shorts"]) == BASE_SHORTS


def test_flag_precedence_last_flag_wins(monkeypatch, family_env_guard):
    from research.portfolio_runner import apply_signal_family_flags
    from research.portfolio_runner import build_parser

    monkeypatch.delenv("PORTFOLIO_SIGNAL_FAMILY", raising=False)

    argv = ["--signal-family", "funding_carry", "--strategy-kind", "momentum"]
    apply_signal_family_flags(build_parser().parse_args(argv), argv)
    assert "PORTFOLIO_SIGNAL_FAMILY" not in os.environ

    argv = ["--strategy-kind", "momentum",
            "--signal-family", "funding_price_divergence"]
    apply_signal_family_flags(build_parser().parse_args(argv), argv)
    assert os.environ["PORTFOLIO_SIGNAL_FAMILY"] == "funding_price_divergence"

    argv = ["--strategy-kind=funding_price_divergence",
            "--signal-family=funding_carry"]
    apply_signal_family_flags(build_parser().parse_args(argv), argv)
    assert os.environ["PORTFOLIO_SIGNAL_FAMILY"] == "funding_carry"

    argv = ["--signal-family=none", "--strategy-kind=funding_carry"]
    apply_signal_family_flags(build_parser().parse_args(argv), argv)
    assert os.environ["PORTFOLIO_SIGNAL_FAMILY"] == "funding_carry"


def test_strategy_kind_momentum_unsets_inherited_family(monkeypatch):
    from research.portfolio_runner import apply_signal_family_flags
    from research.portfolio_runner import build_parser

    monkeypatch.setenv("PORTFOLIO_SIGNAL_FAMILY", "funding_price_divergence")
    argv = ["--strategy-kind", "momentum"]
    apply_signal_family_flags(build_parser().parse_args(argv), argv)
    assert "PORTFOLIO_SIGNAL_FAMILY" not in os.environ


def test_no_flag_keeps_inherited_family(monkeypatch):
    """Flagless reproduce/rerun workers must keep the source family."""
    from research.portfolio_runner import apply_signal_family_flags
    from research.portfolio_runner import build_parser

    monkeypatch.setenv("PORTFOLIO_SIGNAL_FAMILY", "funding_price_divergence")
    args = build_parser().parse_args([])
    apply_signal_family_flags(args, [])
    assert os.environ["PORTFOLIO_SIGNAL_FAMILY"] == "funding_price_divergence"


def test_signal_family_none_stays_noop(monkeypatch):
    from research.portfolio_runner import apply_signal_family_flags
    from research.portfolio_runner import build_parser

    monkeypatch.setenv("PORTFOLIO_SIGNAL_FAMILY", "funding_carry")
    argv = ["--signal-family", "none"]
    apply_signal_family_flags(build_parser().parse_args(argv), argv)
    assert os.environ["PORTFOLIO_SIGNAL_FAMILY"] == "funding_carry"


def test_cli_help_default_momentum_smoke():
    """Subprocess smoke: no inherited family => default momentum unchanged.

    Also proves the new flags exist and document their precedence, and that
    an UNSET PORTFOLIO_SIGNAL_FAMILY leaves module import/CLI healthy.
    """
    env = {k: v for k, v in os.environ.items()
           if k != "PORTFOLIO_SIGNAL_FAMILY"}
    proc = subprocess.run(
        [sys.executable, "-m", "research.portfolio_runner", "--help"],
        capture_output=True, text=True, cwd=str(REPO_ROOT), env=env,
        timeout=180,
    )
    assert proc.returncode == 0, proc.stderr
    assert "--strategy-kind" in proc.stdout
    assert "--funding-lookback-days" in proc.stdout
    assert "funding_price_divergence" in proc.stdout
    assert "LAST" in proc.stdout  # precedence documented in help
