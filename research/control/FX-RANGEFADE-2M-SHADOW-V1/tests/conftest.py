"""Path setup for the Phorec shadow tests (pure-core + HTTP layers)."""
import sys
from pathlib import Path

CYCLE = Path(__file__).resolve().parent.parent
for p in (str(CYCLE / "daemon"), str(CYCLE / "dashboard"), str(CYCLE / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)
