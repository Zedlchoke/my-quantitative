"""A7-TERMINAL item 3: independently recompute the 9 frozen arm_config_digests.

Run from the a7-terminal worktree; imports come from the EXEC tree so the
recomputed digests reflect the frozen family modules that produced the scored
artifacts.  Import-order contract: research.adapter_v10 must be imported
BEFORE any research.v11 module.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

EXEC_TREE = Path(r"C:\Users\ROYAL\my-quantitative\.worktrees\v11\exec-v11-1")
A7_TREE = Path(r"C:\Users\ROYAL\my-quantitative\.worktrees\v11\a7-terminal")

sys.path.insert(0, str(EXEC_TREE))

# Import-order contract: adapter_v10 FIRST.
import research.adapter_v10  # noqa: F401  (must precede research.v11 imports)
_ = research.adapter_v10.__name__  # silence linters; proves import happened
import research.v11.publication_identity as pi  # noqa: E402

from research.v11.publication_identity import arm_config_digest  # noqa: E402
from research.v11.families.lottery_max_skew.plugin import frozen_identity as lot_identity  # noqa: E402
from research.v11.families.illiq_amihud.strategy import build_frozen_identity as illiq_identity  # noqa: E402
from research.v11.families.oilever_delev.strategy import frozen_identity as oilev_identity  # noqa: E402

freeze = json.loads(
    (A7_TREE / "research" / "control" / "v11_run" / "selection_freeze.json").read_text(
        encoding="utf-8"
    )
)

BUILDERS = {
    "V11-SEED-LOTTERY-MAX-SKEW": lot_identity,
    "A8-V11-ILLIQ-AMIHUD": illiq_identity,
    "A8-V11-OILEVER-DELEV": oilev_identity,
}

out = {
    "schema": "a7_terminal_item3_digest_recompute_v1",
    "exec_tree": str(EXEC_TREE),
    "import_order": ["research.adapter_v10", "research.v11.publication_identity", "family builders"],
    "adapter_v10_file": sys.modules["research.adapter_v10"].__file__,
    "publication_identity_file": pi.__file__,
    "rows": [],
}
digests = []
for cell in freeze["frozen_cells"]:
    fam = cell["family"]
    arm = cell["arm_id"]
    ident = BUILDERS[fam](arm)
    mine = arm_config_digest(ident, arm_id=arm)
    digests.append(mine)
    out["rows"].append(
        {
            "family": fam,
            "arm_id": arm,
            "role": cell["role"],
            "recomputed": mine,
            "frozen": cell["arm_config_digest"],
            "match": mine == cell["arm_config_digest"],
        }
    )

out["all_match"] = all(r["match"] for r in out["rows"])
out["pairwise_distinct"] = len(set(digests)) == len(digests)
out["n_digests"] = len(digests)
print(json.dumps(out, indent=1))
