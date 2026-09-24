#!/bin/zsh
# Phorec FX shadow launcher — run from anywhere: <cycle>/launch_phorec.sh
CYCLE="${0:A:h}"
PY="/Users/hoangminhlong/my-quantitative/.venv/bin/python"
nohup "$PY" "$CYCLE/daemon/shadow_daemon.py" >> "$CYCLE/daemon.log" 2>&1 < /dev/null &
echo "daemon pid $!"
nohup "$PY" "$CYCLE/dashboard/serve.py" >> "$CYCLE/dashboard.log" 2>&1 < /dev/null &
echo "dashboard pid $! — http://127.0.0.1:8766"
