#!/bin/bash
# A1 Phase E family chain: serial arms, robust exit accounting.
FAMILY="$1"; SHARD="$2"; shift 2
LOG="/c/Users/ROYAL/AppData/Local/Temp/v11_phase_e_${FAMILY}.log"
for ARM in "$@"; do
  echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] START $ARM pid=$$" >> "$LOG"
  python -u /c/Users/ROYAL/my-quantitative/research/control/v11_run/tools_stronghost/run_v11_cell.py \
    --family "$FAMILY" --arm "$ARM" \
    --exec-root /c/Users/ROYAL/my-quantitative/.worktrees/v11/exec-v11-1 \
    --ledger "/c/Users/ROYAL/my-quantitative/.worktrees/v11/exec-v11-1/results/registry/$SHARD.jsonl" \
    --publish >> "$LOG" 2>&1
  RC=$?
  echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] EXIT=$RC $ARM" >> "$LOG"
  if [ $RC -ne 0 ]; then
    echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] CHAIN_ABORT $FAMILY rc=$RC" >> "$LOG"
    exit $RC
  fi
done
echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] CHAIN_DONE $FAMILY" >> "$LOG"
