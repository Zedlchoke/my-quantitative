"""conftest — puts adapt_fx_ja/ (and thus the per-family packages) on sys.path.

pytest from the adapt_fx_ja/ root:
  /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest . -q
"""
import sys
from pathlib import Path

ADAPT_FXJA = Path(__file__).resolve().parent
if str(ADAPT_FXJA) not in sys.path:
    sys.path.insert(0, str(ADAPT_FXJA))

FAMILIES = ["jf1_boj_mpm", "jf3_tokyo_morning", "jf2_mof_regime", "rmm_6j_leg",
            "af1_rba", "af3_bimodal", "af4_tick_regime", "rmm_6a_leg"]


def load_fixture(family_dir: str, name: str) -> dict:
    import json
    p = ADAPT_FXJA / family_dir / "fixtures" / name
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_expected(family_dir: str) -> dict:
    return load_fixture(family_dir, "EXPECTED_MANIFEST.json")
