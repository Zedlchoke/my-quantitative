"""Unit tests for the resumable matrix runner (owner: A2).

The walk-forward engine path is exercised end-to-end separately via the Tier 0
CLI self-test (results/matrix artifacts); these tests keep pytest fast and
network-free by injecting fake cell executors.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

import research.matrix_runner as mr
from contracts.protocol import CellStatus


def test_config_map_covers_inventory_with_existing_files():
    assert set(mr.STRATEGY_CONFIG_MAP) == set(mr.INVENTORY)
    for strategy_type, config_path in mr.STRATEGY_CONFIG_MAP.items():
        assert Path(config_path).exists(), f"missing base config for {strategy_type}: {config_path}"


@pytest.mark.parametrize("strategy_type", list(mr.INVENTORY))
def test_build_cell_settings_overrides_universe_catalog_funding(strategy_type):
    _, settings = mr.build_cell_settings(
        strategy_type,
        ("SOLUSDT", "ETHUSDT"),
    )
    assert settings.strategy_type == strategy_type
    assert settings.market.symbols == ("SOLUSDT", "ETHUSDT")
    assert settings.data.catalog_path == "./catalog_live_crypto"
    assert settings.report.funding_data_path == "funding_data/scan_2026"


def test_breakout_base_config_documents_adaptation():
    # config/research_breakout.yaml does not exist; the frozen breakout block
    # lives in the ETH config (see module docstring).
    assert not __import__("pathlib").Path("config/research_breakout.yaml").exists()
    assert mr.STRATEGY_CONFIG_MAP["breakout"] == "config/research_breakout_eth.yaml"


def test_warmup_days_prefers_history_days_with_safe_default():
    class WithDays:
        history_days = 220

    class WithoutDays:
        pass

    class Holder:
        reclaim_mr = WithDays()

    holder_no_attr = object()
    assert mr.warmup_days_for(Holder(), "reclaim_mr") == 220
    assert mr.warmup_days_for(holder_no_attr, "reclaim_mr") == mr.DEFAULT_WARMUP_DAYS
    # Tier 0 caps warmup for the smoke window.
    assert mr.warmup_days_for(Holder(), "reclaim_mr", tier0=True) == mr.TIER0_WARMUP_DAYS


def test_fold_windows_are_chronological_and_disjoint():
    start = pd.Timestamp("2025-08-21T00:00:00Z")
    end = pd.Timestamp("2026-08-21T00:00:00Z")
    windows = mr.fold_windows(start, end, 3)
    assert len(windows) == 3
    assert windows[0][0] == start
    assert windows[-1][1] == end
    for (_, w_end), (n_start, _) in zip(windows, windows[1:]):
        assert w_end == n_start


def test_identity_tuple_is_complete_and_stable(tmp_path):
    plan_a = mr.make_plan(
        "ema_atr",
        "SOLUSDT",
        tier=1,
        folds=3,
        window_start=mr.DECLARED_S0_START,
        window_end=mr.DECLARED_S0_END,
    )
    plan_b = mr.make_plan(
        "ema_atr",
        "SOLUSDT",
        tier=1,
        folds=3,
        window_start=mr.DECLARED_S0_START,
        window_end=mr.DECLARED_S0_END,
    )
    ident_a = plan_a.identity(
        fee_model="maker_taker",
        slippage_model="one_tick_slippage",
        seed=42,
        snapshot_id=mr.data_snapshot_id("./catalog_live_crypto", "SOLUSDT",
                                        mr.DECLARED_S0_START, mr.DECLARED_S0_END),
    )
    ident_b = plan_b.identity(
        fee_model="maker_taker",
        slippage_model="one_tick_slippage",
        seed=42,
        snapshot_id=mr.data_snapshot_id("./catalog_live_crypto", "SOLUSDT",
                                        mr.DECLARED_S0_START, mr.DECLARED_S0_END),
    )
    required = {
        "strategy_type", "symbol", "config_sha256", "data_snapshot_id",
        "split_policy", "fee_model", "slippage_model", "seed",
    }
    assert set(ident_a) == required
    assert plan_a.identity_key(ident_a) == plan_b.identity_key(ident_b)


def _fake_payload(trades: int = 25) -> dict:
    return {
        "window_actual": {"start_utc": "x", "end_utc": "y"},
        "data_bounds": {"first_bar_utc": "a", "last_bar_utc": "b"},
        "snapshot_id": "snap",
        "total_trades": trades,
        "positive_folds": 2,
        "total_pnl": 12.5,
        "pnl_after_funding": 9.25,
        "expectancy_after_funding": 0.05,
        "observations": [],
        "folds": [
            {"fold": i, "trades": trades // 3, "expectancy": 0.01} for i in range(3)
        ],
    }


def test_rerun_reuses_completed_cells_without_executing(tmp_path, monkeypatch):
    calls = []

    def recording_execute(plan):
        calls.append((plan.strategy_type, plan.symbol))
        return _fake_payload()

    monkeypatch.setattr(mr, "execute_cell", recording_execute)

    common = dict(
        matrix_id="m_resume",
        tier=1,
        strategies=["ema_atr"],
        symbols=["SOLUSDT"],
        output_root=tmp_path,
        folds=3,
    )
    first = mr.run_matrix(**common)
    assert first["completed"] == 1 and first["reused"] == 0
    assert calls == [("ema_atr", "SOLUSDT")]

    second = mr.run_matrix(**common)
    assert second["reused"] == 1 and second["completed"] == 0
    assert len(calls) == 1  # executor NOT called again

    index = json.loads((tmp_path / "m_resume" / "index.json").read_text())
    entries = list(index["cells"].values())
    assert entries[0]["status"] == CellStatus.COMPLETED.value
    assert (tmp_path / "m_resume" / "cells" / "ema_atr__SOLUSDT.json").exists()


def test_crashing_cell_is_isolated_as_pipeline_error(tmp_path, monkeypatch):
    def flaky_execute(plan):
        if plan.symbol == "BADUSDT":
            raise RuntimeError("engine exploded")
        return _fake_payload()

    monkeypatch.setattr(mr, "execute_cell", flaky_execute)

    report = mr.run_matrix(
        matrix_id="m_iso",
        tier=1,
        strategies=["ema_atr"],
        symbols=["GOODUSDT", "BADUSDT"],
        output_root=tmp_path,
        folds=3,
    )
    assert report["completed"] == 1
    assert report["pipeline_errors"] == 1
    statuses = {row["cell"]: row["status"] for row in report["results"]}
    assert statuses["cells/ema_atr__BADUSDT.json"] == CellStatus.PIPELINE_ERROR.value
    assert statuses["cells/ema_atr__GOODUSDT.json"] == CellStatus.COMPLETED.value

    bad_artifact = json.loads(
        (tmp_path / "m_iso" / "cells" / "ema_atr__BADUSDT.json").read_text()
    )
    result = bad_artifact["cell_result"]
    assert result["status"] == CellStatus.PIPELINE_ERROR.value
    assert list(result["reason_codes"]) == ["cell_failed_exception"]
    assert "engine exploded" in bad_artifact["error"]

    index = json.loads((tmp_path / "m_iso" / "index.json").read_text())
    assert any(
        e["status"] == CellStatus.PIPELINE_ERROR.value for e in index["cells"].values()
    )


def test_error_cells_are_retried_on_next_run(tmp_path, monkeypatch):
    state = {"fail": True}

    def toggling_execute(plan):
        if state["fail"]:
            raise RuntimeError("transient")
        return _fake_payload()

    monkeypatch.setattr(mr, "execute_cell", toggling_execute)

    common = dict(
        matrix_id="m_retry",
        tier=1,
        strategies=["ema_atr"],
        symbols=["SOLUSDT"],
        output_root=tmp_path,
        folds=3,
    )
    first = mr.run_matrix(**common)
    assert first["pipeline_errors"] == 1

    state["fail"] = False
    second = mr.run_matrix(**common)
    assert second["completed"] == 1 and second["pipeline_errors"] == 0


def test_tier0_plans_use_smoke_window_single_fold_short_warmup():
    start = pd.Timestamp("2026-08-18T00:00:00Z")
    end = pd.Timestamp("2026-08-21T00:00:00Z")
    plan = mr.make_plan(
        "reclaim_mr",
        "ETHUSDT",
        tier=0,
        folds=mr.TIER0_FOLDS,
        window_start=start,
        window_end=end,
    )
    assert plan.folds == 1
    assert plan.warmup_days == mr.TIER0_WARMUP_DAYS
    assert plan.window_end - plan.window_start == pd.Timedelta(days=mr.TIER0_SMOKE_DAYS)
    assert plan.split_policy.startswith("tier0_smoke")


def test_data_snapshot_id_tracks_catalog_symbol_window_not_mtime():
    a = mr.data_snapshot_id(
        "./catalog_live_crypto", "BTCUSDT", mr.DECLARED_S0_START, mr.DECLARED_S0_END
    )
    b = mr.data_snapshot_id(
        "./catalog_live_crypto", "BTCUSDT", mr.DECLARED_S0_START, mr.DECLARED_S0_END
    )
    c = mr.data_snapshot_id(
        "./catalog_other", "BTCUSDT", mr.DECLARED_S0_START, mr.DECLARED_S0_END
    )
    d = mr.data_snapshot_id(
        "./catalog_live_crypto", "BTCUSDT",
        mr.DECLARED_S0_START + pd.Timedelta(days=1), mr.DECLARED_S0_END,
    )
    assert a == b
    assert a != c
    assert a != d
