"""conftest — puts adapt_nq/ (and thus the per-family packages) on sys.path.

pytest from the adapt_nq/ root: `.venv/bin/python -m pytest . -q`
"""
import sys
from pathlib import Path

ADAPT_NQ = Path(__file__).resolve().parent
if str(ADAPT_NQ) not in sys.path:
    sys.path.insert(0, str(ADAPT_NQ))

FIXTURES = {
    "f1": ADAPT_NQ / "f1_fomc_era" / "fixtures",
    "f2": ADAPT_NQ / "f2_macro_0730" / "fixtures",
    "f3": ADAPT_NQ / "f3_run_rev" / "fixtures",
    "f4": ADAPT_NQ / "f4_rollwk" / "fixtures",
}


def load_fixture(family_key: str, name: str) -> dict:
    import json
    with open(FIXTURES[family_key] / name, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_expected(family_key: str) -> dict:
    return load_fixture(family_key, "EXPECTED_MANIFEST.json")
