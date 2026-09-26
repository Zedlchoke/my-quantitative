"""COST/EXECUTION lane tests — ERP1-TRACKA-COHORT-1 / failres-cost.

FAILURE_ROOT_CAUSE_RESEARCH · DIAGNOSTIC_OUTCOME_EXPOSED ·
SINGLE_SOURCE_PANEL · FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK · PAPER_TIER.

Checks the failres-costexec decomposition against the failres-attrib
artifacts committed at base 3b1c29fa:
  1. fold-table summation identities (net = gross + cost; rows vs the
     attribution agg's k-decay k=1.0 and reconciliation per-fold nets;
     RT counts vs the reconciliation RT totals);
  2. the 50-trades-per-pair (seed 20260926) independent recompute of
     gross/cost from the parquet + committed engine charging law
     (SignalPlane semantics), tolerance 0.01 pips.

DIAGNOSTIC ONLY — nothing here is promotable evidence.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

FAILRES = (Path(__file__).resolve().parent.parent)          # .../failres
sys.path.insert(0, str(FAILRES / "scripts"))

import failres_costexec_run as R  # noqa: E402

TOL_PIPS = 0.05          # attribution lane's own reconciliation tolerance
SAMPLE_TOL = 0.01        # this lane's sample-verification tolerance
PAIRS = ("EURUSD", "GBPUSD")
LOSING = {"EURUSD": ("F1", "F2", "F5"), "GBPUSD": ("F3", "F5", "F6")}


def _agg_path(pair):
    return FAILRES / f"failres_attrib_agg_{pair}.json"


# ------------------------------------------------------------ identities --

@pytest.mark.parametrize("pair", PAIRS)
def test_fold_summation_identities(pair):
    rows = R.load_rows(pair)
    agg = json.loads(_agg_path(pair).read_text())
    ft = R.fold_tables(rows)
    recon = agg["reconciliation"]["arms"]["R-DAEMON"]

    n_folded = 0
    net_folded = 0.0
    for f, rec in ft.items():
        # identity 1: net = gross + cost exactly as summed from rows
        assert abs(rec["identity_residual_pips"]) <= TOL_PIPS, (
            f"{pair} {f}: net != gross + cost ({rec})")
        # identity 2: rows-fold net == attribution agg k-decay k=1.0
        assert abs(rec["net_pips"]
                   - agg["k_decay_R-DAEMON"][f]["1.0"]) <= TOL_PIPS
        # identity 3: rows-fold net == attribution recon per-fold net
        assert abs(rec["net_pips"] - recon["per_fold_net"][f]) <= TOL_PIPS
        # identity 4: RT counts match the reconciliation
        assert rec["rt"] == recon["per_fold_rt"][f]
        n_folded += rec["rt"]
        net_folded += rec["net_pips"]

    # identity 5: folded + non-folded (post-F6 panel tail) == full panel
    none_rows = [r for r in rows if r["book"] == "R-DAEMON"
                 and r["fold"] is None]
    total = net_folded + sum(r["net_pips"] for r in none_rows)
    assert abs(total - recon["net_full_panel"]) <= TOL_PIPS
    assert n_folded + len(none_rows) == recon["rt_full_panel"]


@pytest.mark.parametrize("pair", PAIRS)
def test_losing_fold_verdict_arithmetic(pair):
    rows = R.load_rows(pair)
    ft = R.fold_tables(rows)
    for f in LOSING[pair]:
        rec = ft[f]
        assert rec["net_pips"] < 0, f"{pair} {f} is not a losing fold"
        # shares must sum to 1 and the mechanical verdict must follow
        assert abs(rec["cost_share_of_loss"]
                   + rec["gross_share_of_loss"] - 1.0) < 1e-6
        sc, sg = rec["cost_share_of_loss"], rec["gross_share_of_loss"]
        if sc > 0.5 >= sg:
            expect = "COST_DOMINATED"
        elif sg > 0.5 >= sc:
            expect = "GROSS_NEGATIVE"
        else:
            expect = "MIXED"
        assert rec["verdict"] == expect, (
            f"{pair} {f}: verdict {rec['verdict']} != mechanical {expect} "
            f"(shares cost={sc}, gross={sg})")


# ----------------------------------------------------- sample verification--

@pytest.mark.parametrize("pair", PAIRS)
def test_sample_verification_50_trades(pair):
    parquet = R.DERIVED / f"bars1h_ANC_{pair}.parquet"
    if not parquet.exists():
        pytest.skip(f"local parquet copy absent (gitignored data): {parquet}")
    rows = R.load_rows(pair)
    sv = R.recompute_pair(pair, rows)
    assert sv["n_sampled"] == 50
    assert sv["seed"] == 20260926
    assert sv["verdict"] == "PASS", (
        f"{pair}: sample recompute DEVIATION "
        f"max_abs_dev={sv['max_abs_dev_pips']} pips > {SAMPLE_TOL}")
    assert sv["max_abs_dev_pips"] <= SAMPLE_TOL
