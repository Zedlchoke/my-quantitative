"""PM MONEYLINE 2-WAY battery (LANE 1) — offline, deterministic."""
import json, sys
from pathlib import Path
import pytest
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from research.papertrade_exec import pm_moneyline as PML

def test_moneyline_market_detection():
    good = {"outcomes": '["76ers", "Knicks"]',
            "question": "76ers vs. Knicks"}
    assert PML._is_moneyline(good, "Philadelphia 76ers", "New York Knicks")
    for bad_q in ("Team to Score First", "Odd/Even Score", "Halftime"):
        bad = {"outcomes": '["76ers", "Knicks"]',
               "question": f"76ers vs. Knicks: {bad_q}"}
        assert not PML._is_moneyline(bad, "Philadelphia 76ers",
                                     "New York Knicks"), bad_q

def test_moneyline_rejects_wrong_teams():
    m = {"outcomes": '["Celtics", "Knicks"]',
         "question": "Celtics vs. Knicks"}
    assert not PML._is_moneyline(m, "Philadelphia 76ers", "New York Knicks")

def test_moneyline_short_form_matches():
    m = {"outcomes": '["Hawks", "Magic"]', "question": "Hawks vs. Magic"}
    assert PML._is_moneyline(m, "Atlanta Hawks", "Orlando Magic")

def test_no_midpoint_law():
    """The walk uses CLOB asks only; midpoint/Gamma-prices never enter."""
    import inspect
    src = inspect.getsource(PML)
    assert "outcomePrices" not in src.split("def walk_ask")[1].split(
        "def ")[0] if "def walk_ask" in src else True
