#!/bin/bash
PY="/Users/hoangminhlong/my-quantitative/.venv/bin/python"
SCRIPT="/Users/hoangminhlong/my-quantitative/.worktrees/illiq-reg-v1/integration/research/control/illiq_reg_v1/full_build_locked.py"
for i in $(seq 1 60); do
  "$PY" "$SCRIPT"
  rc=$?
  echo "[retry $i] rc=$rc $(date -u +%H:%M:%SZ)"
  if [ $rc -eq 0 ]; then break; fi
  sleep 90
done
