"""VOL-NG1 I-phase runner machinery (task vol-ng1-i-implementation).

Per-family decision-rule runners for the six frozen selection cells
(2 families x 3 arms), the mandatory control battery, and the Stage-A
R1-R6 fail-closed enforcement scaffolding -- implemented exactly as
declared in the BINDING selection freeze
(research/control/vol_ng1_run/s/selection_freeze.json).

NO scored execution on real data, NO outcome numbers on real data
anywhere in I.  Real-substrate access is limited to structural
plumbing (digests, series lengths, config assembly).  Unit tests run
on SYNTHETIC fixtures only (tests/test_vol_ng1_i.py).
"""

from research.assets.vol_ng1.runners import arms          # noqa: F401
from research.assets.vol_ng1.runners import battery       # noqa: F401
from research.assets.vol_ng1.runners import config        # noqa: F401
from research.assets.vol_ng1.runners import dryrun        # noqa: F401
from research.assets.vol_ng1.runners import evaluator     # noqa: F401

__all__ = ["arms", "battery", "config", "dryrun", "evaluator"]
