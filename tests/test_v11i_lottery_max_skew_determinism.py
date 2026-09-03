"""Double-generation determinism for V11-SEED-LOTTERY-MAX-SKEW.

Features and the schedule are pure deterministic functions of the injected
completed bars: two independent generations must be BYTE-identical.  The
test runs on the real staged snapshot (when present) and on the synthetic
fixture (always).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from research.v11.families.lottery_max_skew.plugin import (
    ANCHOR_ARM,
    CONTROL_ARM,
    NEIGHBOUR_ARM,
    build_arm_plugin,
)
from research.v11.families.lottery_max_skew.strategy import (
    WINDOW_END_ISO,
    WINDOW_START_ISO,
    build_schedule_instants,
)
from research.v11.families.lottery_max_skew.synthetic import build_synthetic_bars

REPO = Path(__file__).resolve().parents[1]
CATALOG = Path("/Users/hoangminhlong/my-quantitative/catalog_live_crypto")
FUNDING = Path("/Users/hoangminhlong/my-quantitative/funding_data/scan_2026")
REAL_DATA_PRESENT = (CATALOG / "data" / "binance_bar").exists() and FUNDING.exists()


def _sha(payload) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def _generation_digest(arm: str, inputs) -> dict[str, str]:
    """Canonical digest of one full feature+schedule generation for one arm."""
    plugin = build_arm_plugin(arm, inputs)
    baseline = plugin.baseline_stress()
    universe = plugin.universe(baseline)
    schedule = plugin.schedule()
    books = {}
    for instant in schedule.instants:
        book = plugin.targets_at(int(instant), universe=universe, stress=baseline)
        books[str(instant)] = book
    fills = {}
    for instant in schedule.instants:
        records = plugin.fills_at(
            int(instant),
            symbols=sorted(universe)[:4],
            stress=baseline,
        )
        fills[str(instant)] = [r.as_dict() for r in records]
    return {
        "schedule_sha256": schedule.sha256,
        "schedule_clock": schedule.clock,
        "books_sha256": _sha(books),
        "fills_sha256": _sha(fills),
        "universe_sha256": _sha(list(universe)),
    }


def test_double_generation_synthetic_byte_identical() -> None:
    gen_a = {}
    gen_b = {}
    for arm in (ANCHOR_ARM, NEIGHBOUR_ARM, CONTROL_ARM):
        inputs_a, _ = build_synthetic_bars(start_day=20_200, n_days=185)
        inputs_b, _ = build_synthetic_bars(start_day=20_200, n_days=185)
        gen_a[arm] = _generation_digest(arm, inputs_a)
        gen_b[arm] = _generation_digest(arm, inputs_b)
    assert gen_a == gen_b
    assert len({gen_a[arm]["books_sha256"] for arm in gen_a}) == 3


def test_schedule_is_independent_of_inputs_and_stable() -> None:
    inputs, _ = build_synthetic_bars(start_day=20_200, n_days=185)
    plugin = build_arm_plugin(ANCHOR_ARM, inputs)
    frozen = build_schedule_instants()
    assert plugin.schedule().instants == frozen
    assert plugin.schedule().sha256 == plugin.schedule().sha256
    # frozen window anchors
    assert WINDOW_START_ISO == "2025-08-22T00:00:00Z"
    assert WINDOW_END_ISO == "2026-08-21T00:00:00Z"


@pytest.mark.skipif(not REAL_DATA_PRESENT, reason="staged snapshot not mounted")
def test_double_generation_real_snapshot_byte_identical() -> None:
    from research.v11.families.lottery_max_skew.data import get_cached_market_inputs

    inputs = get_cached_market_inputs()
    gen_a = {arm: _generation_digest(arm, inputs) for arm in (ANCHOR_ARM, NEIGHBOUR_ARM, CONTROL_ARM)}
    gen_b = {arm: _generation_digest(arm, inputs) for arm in (ANCHOR_ARM, NEIGHBOUR_ARM, CONTROL_ARM)}
    assert gen_a == gen_b


@pytest.mark.skipif(not REAL_DATA_PRESENT, reason="staged snapshot not mounted")
def test_real_adapter_run_hash_stable_across_two_runs() -> None:
    from research.adapter_v10.runner import run_strategy
    from research.v11.families.lottery_max_skew.data import get_cached_market_inputs

    inputs = get_cached_market_inputs()
    hashes = set()
    for _ in range(2):
        plugin = build_arm_plugin(ANCHOR_ARM, inputs)
        result = run_strategy(plugin, write_artifact_file=False)
        hashes.add(result["hashes"]["result_sha256"])
    assert len(hashes) == 1
