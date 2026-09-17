"""CLI entrypoint for one DATA-EDGE-UNLOCK-V1 venue collector.

ADAPTED from CRYPTO-NG4 lane A8 ``run_one.py`` (branch orca/crypto-ng4-integration).

usage:
  run_one.py <coinbase|kraken|deribit> [--data-root PATH] [--run-dir PATH]
             [--max-seconds N] [--include-deribit-trades]
  run_one.py deribit --census-trades [--census-seconds N]
             [--census-out PATH] [--census-summary PATH]

Detached long-running daemon: nohup/setsid from the lane start procedure;
writes a pidfile, a heartbeat file (every <= 60s, bytes + shape counters,
LESSONS Q-13) and a connection journal under the DATA ROOT runtime dir
(~/.my-quantitative-data/data-edge-unlock-v1/runtime/) — NEVER under
research/ (the CRYPTO-NG4 tracked-PID-file incident).  Raw bytes go under
the frozen content-addressed root
~/.my-quantitative-data/data-edge-unlock-v1/raw/.
Data collector only — public keyless market-data endpoints, no auth, no
orders, no trading endpoints.
"""

from __future__ import annotations

import sys
from pathlib import Path

# make the worktree root importable regardless of process cwd
# (collectors -> data_edge_unlock_v1 -> assets -> research -> <worktree root>)
WORKTREE_ROOT = Path(__file__).resolve().parents[4]
if str(WORKTREE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKTREE_ROOT))

from research.assets.data_edge_unlock_v1.collectors.collector import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
