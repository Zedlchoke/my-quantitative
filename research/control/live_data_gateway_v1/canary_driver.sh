#!/bin/zsh
# LIVE-DATA-GATEWAY-V1 dual-run canary driver (plan §9.2).
# Leg A: continuous mark comparison >=24h. Leg B: historical equivalence,
# retried every 30 min until PASS (each attempt appends honest evidence).
# Runs detached from any agent session (nohup); kill via the recorded pid.
set -u
WT=/Users/hoangminhlong/my-quantitative/.worktrees/live-data-gateway-v1/integration
PY=/Users/hoangminhlong/my-quantitative/.venv/bin/python
CAN=$WT/research/control/live_data_gateway_v1/canary
mkdir -p "$CAN"
cd "$WT"
echo "driver start $(date -u +%FT%TZ) pid $$" >> "$CAN/driver.log"

nohup "$PY" -m research.live_gateway.canary marks \
  --gateway http://127.0.0.1:8792 \
  --evidence "$CAN/leg_a_marks.jsonl" \
  --interval 30 --duration-s 86400 \
  >> "$CAN/leg_a.nohup.log" 2>&1 &
echo "legA pid $!" >> "$CAN/driver.log"

attempt=0
while [ "${attempt:-0}" -lt 48 ]; do
  attempt=$((attempt + 1))
  "$PY" -m research.live_gateway.canary history \
    --gateway http://127.0.0.1:8792 \
    --evidence "$CAN/leg_b_history.jsonl" \
    >> "$CAN/leg_b.nohup.log" 2>&1
  rc=$?
  echo "legB attempt $attempt rc=$rc $(date -u +%FT%TZ)" >> "$CAN/driver.log"
  if [ "$rc" -eq 0 ]; then
    echo "legB PASS at attempt $attempt" >> "$CAN/driver.log"
    break
  fi
  sleep 1800
done
echo "driver done $(date -u +%FT%TZ)" >> "$CAN/driver.log"
