#!/bin/bash
# A1 Phase R reproduction chain: re-execute computed arms in the repro tree.
# NO --publish: reproduction re-executes already-observed frozen trials; it
# computes nothing new into any ledger.
FAMILY="$1"; shift
LOG="/c/Users/ROYAL/AppData/Local/Temp/v11_repro_${FAMILY}.log"
for ARM in "$@"; do
  echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] REPRO_START $ARM" >> "$LOG"
  python -u /c/Users/ROYAL/my-quantitative/research/control/v11_run/tools_stronghost/run_v11_cell.py \
    --family "$FAMILY" --arm "$ARM" \
    --exec-root /c/Users/ROYAL/my-quantitative/.worktrees/v11/repro-v11-1 >> "$LOG" 2>&1
  RC=$?
  echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] REPRO_EXIT=$RC $ARM" >> "$LOG"
done
echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] REPRO_DONE $FAMILY" >> "$LOG"
