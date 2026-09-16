"""CLI entrypoint for one CRYPTO-NG4 venue collector.

usage: run_one.py <coinbase|kraken|deribit> [--data-root PATH] [--max-seconds N]

Detached long-running daemon: nohup/setpgrp from the start script; writes a
pidfile, a heartbeat file (every <= 60s) and a connection journal under
collectors/run/, raw bytes under the frozen content-addressed root
(contract field 7: ~/.my-quantitative-data/crypto-ng4-ws/raw/).
Data collector only — public market-data endpoints, no auth, no orders.
"""

from __future__ import annotations

import sys
from pathlib import Path

# make the worktree root importable regardless of process cwd
# (collectors -> crypto_ng4_run -> control -> research -> <worktree root>)
WORKTREE_ROOT = Path(__file__).resolve().parents[4]
if str(WORKTREE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKTREE_ROOT))

from research.control.crypto_ng4_run.collectors.collector import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
