"""Path setup for the vendored edge-scanner local_guard tests.

Inserts (1) the vendored module directory so `import local_guard` resolves to
the byte-faithful copy under research/platform_tools/thirdparty/edge-scanner/,
and (2) the worktree root so the tests package itself is importable
(tests.platform_tools.thirdparty.*). Nothing else is added to sys.path.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_WORKTREE_ROOT = _HERE.parents[3]
_VENDOR_DIR = _WORKTREE_ROOT / "research" / "platform_tools" / "thirdparty" / "edge-scanner"

for _p in (str(_WORKTREE_ROOT), str(_VENDOR_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
