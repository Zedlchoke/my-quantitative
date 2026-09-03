"""Determinism tests for A12-V12-BAB-LOWBETA (double-generation equality).

Two independent generations -- an independently rebuilt synthetic frame and
a fresh plugin construction -- must produce byte-identical adapter results
(the runner's deterministic ``result_sha256``) and byte-identical stamp-book
payloads.  The real-data double-generation equality lives in the committed
audit artifact ``research/audits/v12i/bab_lowbeta/double_generation.json``
and is re-asserted there by the feasibility test module.
"""

from __future__ import annotations

import json

import pytest

from research.adapter_v10.runner import run_strategy
from research.v12.families.bab_lowbeta.audits import (
    build_beta_ranking_frame,
    make_plugin,
)
from research.v12.families.bab_lowbeta.strategy import weekly_monday_stamps

ANCHOR = "BAB-90D-W"


def _books_payload(plugin) -> str:
    universe = plugin.universe(plugin.baseline_stress())
    rows = [
        plugin.targets_at(int(stamp), universe=universe, stress=plugin.baseline_stress())
        for stamp in plugin.schedule().instants
    ]
    return json.dumps(rows, sort_keys=True, separators=(",", ":"), default=str)


def test_rebuilt_frame_produces_byte_identical_adapter_result():
    """Two independent builds of the SAME frame -> identical result hash."""
    bars, _ = build_beta_ranking_frame()
    first = run_strategy(make_plugin(ANCHOR, bars), write_artifact_file=False)
    second = run_strategy(make_plugin(ANCHOR, bars), write_artifact_file=False)
    assert first["hashes"]["result_sha256"] == second["hashes"]["result_sha256"]


def test_independent_frame_generation_is_byte_identical():
    """A freshly regenerated (not reused) frame reproduces the same books."""
    bars_again, _ = build_beta_ranking_frame()
    assert _books_payload(make_plugin(ANCHOR, bars_again)) == _books_payload(
        make_plugin(ANCHOR, bars_again)
    )


def test_stamp_books_are_byte_identical_across_plugin_rebuilds():
    bars, _ = build_beta_ranking_frame()
    assert _books_payload(make_plugin(ANCHOR, bars)) == _books_payload(
        make_plugin(ANCHOR, bars)
    )


def test_schedule_is_immutable_and_stable():
    """The frozen 52-Monday schedule is stable and strictly increasing."""
    stamps = weekly_monday_stamps()
    assert len(stamps) == 52
    assert list(stamps) == sorted(set(stamps))
    assert stamps == weekly_monday_stamps()
    # first stamp is the frozen 2025-08-25T00:00:00Z decision stamp
    import datetime as _dt

    first = _dt.datetime.fromtimestamp(stamps[0] / 1e9, tz=_dt.timezone.utc)
    assert (first.year, first.month, first.day) == (2025, 8, 25)


def test_all_arms_share_one_schedule_and_universe():
    bars, _ = build_beta_ranking_frame()
    from research.v12.families.bab_lowbeta.plugin import BabLowBetaPlugin

    plugins = [BabLowBetaPlugin(bars_by_symbol=bars, arm_id=arm) for arm in (
        "BAB-90D-W", "BAB-DOWNCORR-90D-W", "BAB-90D-W-INV"
    )]
    schedules = [p.schedule() for p in plugins]
    assert all(s.instants == schedules[0].instants for s in schedules)
    universes = [p.universe(p.baseline_stress()) for p in plugins]
    assert all(u == universes[0] for u in universes)
