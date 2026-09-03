"""A7-TERMINAL wave 2: final ledger verification.

verify_append_only on the canonical V11 ledger (6 CELL_RESULT rows), the
denominator split, cross-shard key uniqueness (shard_lot, shard_illiq,
canonical), quarantine keys still excluded, and ILLIQ row digests tied to the
frozen selection_freeze digests + trial-key recompute.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

EXEC = Path(r"C:\Users\ROYAL\my-quantitative\.worktrees\v11\exec-v11-1")
CANON = Path(r"C:\Users\ROYAL\my-quantitative\results\registry\experiments_v11_phase_e.jsonl")
A7 = Path(r"C:\Users\ROYAL\my-quantitative\.worktrees\v11\a7-terminal")

sys.path.insert(0, str(EXEC))
import research.adapter_v10  # noqa: F401,E402
from research.global_ledger import verify_append_only  # noqa: E402
from research.v11.publication_identity import _canonical_json, denominator_split  # noqa: E402

out = {"schema": "a7_terminal_wave2_ledger_v1"}
out["verify_append_only"] = verify_append_only(CANON)

rows = [json.loads(l) for l in CANON.read_text(encoding="utf-8").splitlines() if l.strip()]
cells = [r for r in rows if r.get("kind") == "CELL_RESULT"]
out["n_rows"] = len(rows)
out["n_cell_result"] = len(cells)
out["arms"] = [r["payload"]["arm_id"] for r in cells]
out["families"] = sorted({r["payload"]["family_id"] for r in cells})
out["trial_keys_unique"] = len({r["trial_key_sha256"] for r in cells}) == len(cells)
out["denominator_split"] = denominator_split(rows)

frozen = {}
for c in json.loads((A7 / "research/control/v11_run/selection_freeze.json")
                    .read_text(encoding="utf-8"))["frozen_cells"]:
    frozen[c["arm_id"]] = c["arm_config_digest"]

key_recompute = []
digest_ties = []
for r in cells:
    pl = r["payload"]
    key_recompute.append(
        hashlib.sha256(_canonical_json(pl).encode("utf-8")).hexdigest() == r["trial_key_sha256"])
    digest_ties.append({"arm": pl["arm_id"],
                        "digest_frozen_match": pl["arm_config_digest"] == frozen[pl["arm_id"]]})
out["trial_keys_recomputed_match"] = all(key_recompute)
out["arm_digests_tie_to_freeze"] = all(d["digest_frozen_match"] for d in digest_ties)
out["digest_ties"] = digest_ties

reg = EXEC / "results" / "registry"
shards = {}
for f in sorted(reg.glob("shard_*.jsonl")):
    srows = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    shards[f.name] = sorted(r.get("trial_key_sha256") for r in srows)
out["shards"] = {k: {"n": len(v)} for k, v in shards.items()}
canon_keys = sorted(r["trial_key_sha256"] for r in cells)
lot_keys = shards.get("shard_lot.jsonl", [])
illiq_keys = shards.get("shard_illiq.jsonl", [])
out["shard_lot_keys_equal_canon_subset"] = all(k in canon_keys for k in lot_keys)
out["shard_illiq_keys_equal_canon_subset"] = all(k in canon_keys for k in illiq_keys)
out["cross_shard_unique"] = len(set(lot_keys) & set(illiq_keys)) == 0
out["shard_union_equals_canonical"] = sorted(lot_keys + illiq_keys) == canon_keys

quar = reg / "defective"
q_keys = set()
q_n = 0
for f in sorted(quar.glob("*.jsonl")):
    for l in f.read_text(encoding="utf-8").splitlines():
        if l.strip():
            q_keys.add(json.loads(l).get("trial_key_sha256"))
            q_n += 1
out["quarantine_rows"] = q_n
out["quarantine_keys_absent_from_canonical"] = not (q_keys & set(canon_keys))
print(json.dumps(out, indent=1))
