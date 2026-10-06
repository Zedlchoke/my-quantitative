"""conftest — puts adapt_fx_eb/ (and thus the per-family packages) on sys.path.

pytest from the adapt_fx_eb/ root: `.venv/bin/python -m pytest . -q`
(mirrors adapt_nq/conftest.py pattern).
"""
import sys
from pathlib import Path

ADAPT_FXEB = Path(__file__).resolve().parent
if str(ADAPT_FXEB) not in sys.path:
    sys.path.insert(0, str(ADAPT_FXEB))

FAMILIES = [
    "f1_london_range",
    "f2_policy_decision",
    "f3_us0830",
    "f4_reopen_gap",
    "f5_cip_overlay",
    "f6_cot_overlay",
    "rmm_roll_migration",
]


def fixtures_dir(family: str) -> Path:
    return ADAPT_FXEB / family / "fixtures"


def load_fixture(family: str, name: str) -> dict:
    import json
    with open(fixtures_dir(family) / name, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_panel(family: str, sym: str) -> dict:
    return load_fixture(family, f"panel_{sym}.json")


def load_expected(family: str) -> dict:
    return load_fixture(family, "EXPECTED_MANIFEST.json")
