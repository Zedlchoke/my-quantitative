"""A7-TERMINAL item 6: ledger append-only chain, 3 CELL_RESULT, quarantine exclusion.

Runs research.global_ledger.verify_append_only (exec-tree module) on the
canonical V11 ledger, then cross-checks trial keys across the canonical
ledger, family shards and the defective quarantine, and computes the
denominator split with the frozen publication_identity.denominator_split.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

EXEC = Path(r"C:\Users\ROYAL\my-quantitative\.worktrees\v11\exec-v11-1")
CANON = Path(r"C:\Users\ROYAL\my-quantitative\results\registry\experiments_v11_phase_e.jsonl")

sys.path.insert(0, str(EXEC))
import research.adapter_v10  # noqa: F401,E402  (import-order contract)
from research.global_ledger import verify_append_only  # noqa: E402
from research.v11.publication_identity import denominator_split  # noqa: E402

out = {"schema": "a7_terminal_item6_ledger_v1"}

# 1. append-only chain
res = verify_append_only(CANON)
out["verify_append_only"] = res if isinstance(res, (dict, list, bool, str)) else str(res)
out["verify_append_only_raw_type"] = type(res).__name__

# 2. canonical rows
rows = [json.loads(l) for l in CANON.read_text(encoding="utf-8").splitlines() if l.strip()]
cells = [r for r in rows if r.get("kind") == "CELL_RESULT"]
others = [r for r in rows if r.get("kind") != "CELL_RESULT"]
out["n_rows"] = len(rows)
out["n_cell_result"] = len(cells)
out["n_other_rows"] = len(others)
out["cell_trial_keys"] = [r["trial_key_sha256"] for r in cells]
out["trial_keys_unique"] = len({r["trial_key_sha256"] for r in cells}) == len(cells)
out["cell_arm_ids"] = [r.get("payload", {}).get("arm_id") for r in cells]
out["cell_family_ids"] = [r.get("payload", {}).get("family_id") for r in cells]
out["verdicts"] = [r.get("verdict") for r in cells]

# 3. shards + quarantine
reg = EXEC / "results" / "registry"
shard_keys = {}
for f in sorted(reg.glob("shard_*.jsonl")):
    srows = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    shard_keys[f.name] = [r.get("trial_key_sha256") for r in srows]
out["shard_trial_keys"] = shard_keys
quar = {}
for f in sorted((reg / "defective").glob("*.jsonl")):
    qrows = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    quar[f.name] = [
        {
            "trial_key": r.get("trial_key_sha256"),
            "kind": r.get("kind"),
            "arm": r.get("payload", {}).get("arm_id"),
            "n_positions": r.get("payload", {}).get("metrics", {}).get("n_positions")
            if isinstance(r.get("payload", {}).get("metrics"), dict) else None,
        }
        for r in qrows
    ]
out["quarantine"] = quar

canon_keys = {r["trial_key_sha256"] for r in cells}
shard_all = {k for keys in shard_keys.values() for k in keys}
q_keys = {q["trial_key"] for rows_ in quar.values() for q in rows_}
out["quarantine_keys_absent_from_canonical"] = not (q_keys & canon_keys)
out["shard_keys_equal_canonical"] = shard_all == canon_keys
out["quarantine_rows_are_cell_result"] = all(
    q["kind"] == "CELL_RESULT" for rows_ in quar.values() for q in rows_)

# 4. denominator split on canonical rows (kind-bearing rows only)
out["denominator_split"] = denominator_split(rows)
print(json.dumps(out, indent=1, default=str))
