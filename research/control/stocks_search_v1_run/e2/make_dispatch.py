"""Generate e2/dispatch.json — the code-freeze manifest the scored run
verifies (content-pinned lane dispatch; no self-referential commit sha).
Controller-only helper, run once before the lane commit."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = ["i_stream_engine.py", "i_amended_legs.py", "equivalence.py",
         "selfcheck.py", "e_stream_run.py", "README.md", "make_dispatch.py"]

manifest = {}
for f in FILES:
    rel = "research/control/stocks_search_v1_run/e2/" + f
    manifest[rel] = hashlib.sha256((HERE / f).read_bytes()).hexdigest()
out = {
    "schema": "stocks_search_v1_e2_dispatch@1",
    "cycle_id": "STOCKS-SEARCH-V1",
    "lane": "ssearch-e2",
    "role": "quant-implementer",
    "branch": "orca/stocks-search-v1-integration",
    "code_freeze": manifest,
    "law": ("the scored run verifies every file above hashes to this "
            "committed manifest and that dispatch.json itself is "
            "committed-unmodified; ANY drift = FROZEN_SHA_MISMATCH and "
            "the scored run refuses"),
    "go_phrase_required": "GO STOCKS SEARCH V1 SCORED EXECUTION",
}
(HERE / "dispatch.json").write_text(
    json.dumps(out, indent=1, sort_keys=True) + "\n")
print("dispatch.json written:",
      json.dumps({k: v[:12] for k, v in manifest.items()}, indent=1))
