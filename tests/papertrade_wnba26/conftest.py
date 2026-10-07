import sys
from pathlib import Path

# Expose the ported ledger module (research/papertrade_wnba26/) for flat import
# in tests, mirroring the 2027 PREP lane's module+test layout.
WT_ROOT = Path(__file__).resolve().parents[2]
_PAPERTRADE_DIR = WT_ROOT / "research" / "papertrade_wnba26"
if str(_PAPERTRADE_DIR) not in sys.path:
    sys.path.insert(0, str(_PAPERTRADE_DIR))
