#!/bin/bash
# CHR3F staging watcher: retry on lock-busy, stop on complete or refusal.
set -u
WT="/Users/hoangminhlong/my-quantitative/.worktrees/crypto-historical-replication-3f-v1/integration"
PY="/Users/hoangminhlong/my-quantitative/.venv/bin/python"
RUNNER="$WT/research/control/crypto_historical_replication_3f_v1/stage_all_locked.py"
for i in $(seq 1 500); do
  "$PY" "$RUNNER"
  rc=$?
  echo "[watcher $i] rc=$rc $(date -u +%H:%M:%SZ)"
  if [ $rc -eq 0 ]; then break; fi
  if [ $rc -eq 4 ]; then echo "tracked modifications - manual review needed"; break; fi
  sleep 300
done
echo "[watcher] finished $(date -u +%FT%TZ)"
