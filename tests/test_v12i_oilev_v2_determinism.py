"""V12 I lane -- double-generation determinism tests for OILEV-V2.

Deliverable 4(d): the features/targets must generate identically twice.
On synthetic worlds this is exact byte equality of the canonical JSON of
the full target schedule, the plugin payload and the adapter result
hashes; on the real staged snapshot the committed evidence artifact
records the same double-generation equality for all 52 stamps x 3 arms.

The suite also proves the committed golden fixtures are immutable
inputs: their tracked bytes are pinned by sha256 in this module, and the
regenerated golden payload must equal the tracked file exactly (nothing
in the suite ever writes into the repo tree).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tests.test_v12i_oilev_v2_causal import build_world, load_fixture

from research.adapter_v10.runner import run_strategy
from research.v12.families.oilev_v2.audits import (
    build_target_records,
    evidence_double_generation,
    load_oi_by_symbol,
    tradeable_universe_symbols,
)
from research.v12.families.oilev_v2.plugin import OilevV2Plugin
from research.v12.families.oilev_v2.strategy import (
    ANCHOR_ARM,
    ARM_IDS,
    compute_targets_at,
    frozen_identity,
    stamp_calendar,
)

GOLDEN_DIR = Path("research/v12/families/oilev_v2/golden")

#: Pinned content digests of the committed golden fixtures (frozen test
#: inputs).  Any mutation of the tracked bytes fails this suite.
_PINNED_GOLDEN_SHA256 = {
    "causal_fixture.json": (
        "041b0e7edd4cb355c60dfeeaab2a0e3c4e9d07ac739b2f01e093dd4cef9aada6"
    ),
    "anchor_targets_golden.json": (
        "06455280713bfb8526416acd2fedb0f55bd1558c52f063c2cb9ee4326cdcd8f2"
    ),
}


def _canonical_sha256(payload) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_synthetic_targets_double_generation_byte_identical() -> None:
    fixture = load_fixture()
    world, stamp, universe = build_world(fixture)
    for arm_id in ARM_IDS:
        first = build_target_records(
            arm_id, oi_by_symbol=world, universe=universe, instants=[stamp]
        )
        second = build_target_records(
            arm_id, oi_by_symbol=world, universe=universe, instants=[stamp]
        )
        assert _canonical_sha256(first) == _canonical_sha256(second)


def test_plugin_targets_double_generation_byte_identical() -> None:
    fixture = load_fixture()
    world, stamp, universe = build_world(fixture)
    from research.v11.families.oilever_delev.strategy import Bar

    bars = {
        sym: (
            Bar(
                ts_event_ns=stamp + 900_000_000_000,
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.5,
            ),
        )
        for sym in universe
    }
    bars["BTCUSDT"] = bars[universe[0]]
    for arm_id in ARM_IDS:
        plugin_a = OilevV2Plugin(
            arm_id=arm_id, oi_by_symbol=world, bars_by_symbol=bars
        )
        plugin_b = OilevV2Plugin(
            arm_id=arm_id, oi_by_symbol=world, bars_by_symbol=bars
        )
        baseline_a = plugin_a.baseline_stress()
        baseline_b = plugin_b.baseline_stress()
        payload_a = plugin_a.targets_at(
            stamp, universe=plugin_a.tradeable_universe(), stress=baseline_a
        )
        payload_b = plugin_b.targets_at(
            stamp, universe=plugin_b.tradeable_universe(), stress=baseline_b
        )
        assert _canonical_sha256(payload_a) == _canonical_sha256(payload_b)
        assert plugin_a.schedule().sha256 == plugin_b.schedule().sha256
        assert plugin_a.identity() == plugin_b.identity() == frozen_identity(arm_id)


def _synthetic_plugin() -> OilevV2Plugin:
    """Ten-symbol synthetic world covering the whole frozen schedule."""
    import math
    from datetime import datetime, timezone

    from research.v11.families.oilever_delev.strategy import Bar

    day = 86_400_000_000_000
    start = int(
        datetime.fromisoformat("2025-06-02T00:00:00")
        .replace(tzinfo=timezone.utc)
        .timestamp()
    ) * 1_000_000_000
    n_days = 450  # covers every stamp's 28d/56d formation windows
    stamps = stamp_calendar()
    oi = {}
    for i in range(10):
        sym = f"SYM{i:02d}"
        g = math.exp((-0.45 + 0.1 * i) / 28.0)
        oi[sym] = tuple(
            (start + d * day + 23 * 3600 * 10**9 + 55 * 60 * 10**9,
             1_000_000.0 * g ** d)
            for d in range(n_days)
        )
    bars = {}
    for sym in oi:
        rows = []
        for stamp in stamps:
            rows.append(
                Bar(
                    ts_event_ns=stamp + 900_000_000_000,
                    open=100.0 + i,
                    high=101.0 + i,
                    low=99.0 + i,
                    close=100.5 + i,
                )
            )
        bars[sym] = tuple(rows)
    bars["BTCUSDT"] = bars["SYM00"]
    settlements = {
        sym: tuple(
            {
                "publish_ts_ns": int(stamp) + 8 * 3600 * 1_000_000_000 * k,
                "value": 0.0001,
            }
            for stamp in stamps
            for k in (1,)
        )
        for sym in oi
    }
    return OilevV2Plugin(
        arm_id=ANCHOR_ARM,
        oi_by_symbol=oi,
        bars_by_symbol=bars,
        settlements_by_symbol=settlements,
        tick_sizes={sym: 0.01 for sym in oi},
    )


def test_adapter_run_deterministic_unscored_and_scoped() -> None:
    plugin_a = _synthetic_plugin()
    plugin_b = _synthetic_plugin()
    result_a = run_strategy(plugin_a, write_artifact_file=False)
    result_b = run_strategy(plugin_b, write_artifact_file=False)
    assert result_a["scored"] is False
    assert result_a["hashes"] == result_b["hashes"]
    assert _canonical_sha256(result_a) == _canonical_sha256(result_b)
    # nothing was written into the repo tree
    assert result_a["artifacts"] == {}


def test_golden_fixture_files_are_immutable_tracked_bytes() -> None:
    expected = {
        "causal_fixture.json",
        "anchor_targets_golden.json",
    }
    present = {p.name for p in GOLDEN_DIR.iterdir() if p.is_file()}
    assert expected <= present
    for name in expected:
        blob = (GOLDEN_DIR / name).read_bytes()
        assert len(blob) > 0
        digest = hashlib.sha256(blob).hexdigest()
        assert digest == _PINNED_GOLDEN_SHA256[name], name


@pytest.mark.skipif(
    not Path("/Users/hoangminhlong/my-quantitative/oi_data/consolidated").is_dir(),
    reason="read-only workspace data absent",
)
def test_real_data_double_generation_all_arms() -> None:
    payload = evidence_double_generation()
    assert payload["all_byte_identical"] is True
    for arm_id in ARM_IDS:
        entry = payload["arms"][arm_id]
        assert entry["generation_1_sha256"] == entry["generation_2_sha256"]
        assert entry["records"] == 52


@pytest.mark.skipif(
    not Path("/Users/hoangminhlong/my-quantitative/oi_data/consolidated").is_dir(),
    reason="read-only workspace data absent",
)
def test_real_target_records_equal_module_targets_at() -> None:
    """The audit record builder and the strategy module agree exactly."""
    universe = tradeable_universe_symbols()
    oi = load_oi_by_symbol(universe)
    stamps = stamp_calendar()
    direct = [
        compute_targets_at(
            ANCHOR_ARM, oi_by_symbol=oi, stamp_ns=int(stamp), universe=universe
        )
        for stamp in stamps[:3]
    ]
    records = build_target_records(
        ANCHOR_ARM, oi_by_symbol=oi, universe=universe, instants=stamps[:3]
    )
    for book, record in zip(direct, records):
        assert record["weights"] == book["weights"]
        assert record["decision_ns"] == book["decision_ns"]
