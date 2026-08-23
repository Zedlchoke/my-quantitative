"""A1 integration tests: vol_compression_breakout wired into factory + runner."""

from __future__ import annotations

import pandas as pd
import pytest

from contracts.protocol import canonical_json
from research.matrix_runner import (
    VOLCOMP_HYPOTHESIS_CONFIG,
    VOLCOMP_STRATEGY_TYPE,
    build_cell_settings,
    make_plan,
)
from strategy_vol_compression_breakout import VolCompressionBreakoutSettings


def _base_sections():
    from config.settings import load_research_config

    return load_research_config("config/research_baseline_altcoin.yaml")


@pytest.mark.parametrize("variant_index", range(4))
def test_factory_builds_all_grid_combos(variant_index):
    from strategy_factory import build_strategy

    settings = _base_sections()
    combo = VolCompressionBreakoutSettings.parameter_grid()[variant_index]
    instance = build_strategy(
        settings.market,
        settings.risk,
        settings.strategy,
        strategy_type=VOLCOMP_STRATEGY_TYPE,
        mean_reversion=None,
        regime_switch=None,
        breakout=None,
        reclaim_mr=None,
        trend_pullback=None,
        markdown_breakdown=None,
        vol_compression=combo,
        enable_trading=True,
        request_historical_bars=False,
        symbol="ETHUSDT",
    )
    assert type(instance).__name__ == "VolCompressionBreakoutStrategy"
    assert instance.config.squeeze_lookback == combo.squeeze_lookback
    assert instance.config.volume_min_ratio == float(combo.volume_min_ratio)


def test_factory_requires_volcomp_settings():
    from strategy_factory import build_strategy

    settings = _base_sections()
    with pytest.raises(ValueError, match="vol_compression settings are required"):
        build_strategy(
            settings.market,
            settings.risk,
            settings.strategy,
            strategy_type=VOLCOMP_STRATEGY_TYPE,
            mean_reversion=None,
            regime_switch=None,
            breakout=None,
            reclaim_mr=None,
            trend_pullback=None,
            markdown_breakdown=None,
            enable_trading=True,
            request_historical_bars=False,
            symbol="ETHUSDT",
        )


def test_volcomp_settings_provenance_is_candidate_yaml():
    config_path, _ = build_cell_settings(VOLCOMP_STRATEGY_TYPE, ("ETHUSDT",))
    assert config_path == VOLCOMP_HYPOTHESIS_CONFIG


def test_runner_expands_four_distinct_variants():
    window_start = pd.Timestamp("2025-08-21T00:00:00Z")
    window_end = pd.Timestamp("2026-08-21T00:00:00Z")
    plans = [
        make_plan(
            VOLCOMP_STRATEGY_TYPE,
            "ETHUSDT",
            tier=1,
            folds=3,
            window_start=window_start,
            window_end=window_end,
            param_variant=f"v{i}",
        )
        for i in range(4)
    ]
    identities = [
        p.identity(fee_model="maker_taker", slippage_model="one_tick_slippage",
                   seed=42, snapshot_id="snap") for p in plans
    ]
    keys = {canonical_json(i) for i in identities}
    assert len(keys) == 4
    assert {p.param_variant for p in plans} == {"v0", "v1", "v2", "v3"}
    expected_days = max(
        1, -(-VolCompressionBreakoutSettings().warmup_bars() // 96)
    )
    assert all(p.warmup_days >= expected_days for p in plans)


def test_inventory_unchanged_for_existing_matrix():
    from research.matrix_runner import INVENTORY

    assert VOLCOMP_STRATEGY_TYPE not in INVENTORY
    assert len(INVENTORY) == 7
