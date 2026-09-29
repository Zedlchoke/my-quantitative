"""pytest bootstrap: put the cycle worktree root on sys.path so that
`from research.btcombo6 import ...` resolves when pytest is invoked from
anywhere."""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
