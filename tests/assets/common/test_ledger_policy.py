"""Ledger placement contract tests (path policy only, zero runtime writes)."""

from __future__ import annotations

from pathlib import Path

import pytest

import research.assets.common.ledger_policy as ledger_policy
from research.assets.common.ledger_policy import (
    CRYPTO_LEDGER_ROOT,
    FOREX_LEDGER_ROOT,
    GLOBAL_TRIAL_INDEX_PATH,
    STOCKS_LEDGER_ROOT,
    GlobalTrialIndex,
    global_trial_index_path,
    ledger_path_for,
    ledger_root_for,
)


def test_per_asset_class_roots_match_plan_section_14():
    assert ledger_root_for("CRYPTO_PERP") == Path("results") / "registry"
    assert ledger_root_for("US_CASH_EQUITY") == Path("results") / "registry" / "stocks"
    assert ledger_root_for("FX_SPOT") == Path("results") / "registry" / "forex"
    assert CRYPTO_LEDGER_ROOT == Path("results") / "registry"
    assert STOCKS_LEDGER_ROOT == Path("results") / "registry" / "stocks"
    assert FOREX_LEDGER_ROOT == Path("results") / "registry" / "forex"


def test_unknown_asset_class_fails_closed_without_default():
    with pytest.raises(ValueError, match="no ledger root"):
        ledger_root_for("SOMETHING_ELSE")
    with pytest.raises(ValueError, match="asset_class"):
        ledger_root_for("not valid")
    assert "DEFAULT" not in dir(ledger_policy)


def test_ledger_file_paths_are_relative_policy_only():
    path = ledger_path_for("US_CASH_EQUITY", "cells.jsonl")
    assert path == Path("results") / "registry" / "stocks" / "cells.jsonl"
    assert not path.exists()  # policy only: nothing is ever created here
    with pytest.raises(ValueError):
        ledger_path_for("US_CASH_EQUITY", "  ")


def test_single_global_trial_index_is_read_only_interface():
    assert global_trial_index_path() == GLOBAL_TRIAL_INDEX_PATH
    assert "write" not in {name.lower() for name in dir(GlobalTrialIndex)}
    assert "append" not in {name.lower() for name in dir(GlobalTrialIndex)}
    assert "delete" not in {name.lower() for name in dir(GlobalTrialIndex)}
    # The interface cannot be instantiated and exposes only read methods.
    with pytest.raises(TypeError):
        GlobalTrialIndex()  # type: ignore[abstract]
    assert set(GlobalTrialIndex.__abstractmethods__) == {"snapshot", "digest", "count"}
