"""Sleep until 2026-09-28T20:50Z then run the rollover-window collector.

One-shot helper for lane L-FX (the 17:00 ET / 21:00 UTC rollover window).
Read-only: it only invokes collect_fx_ticks.py. If the machine sleeps
past the window, the collector still runs late and its sanitized output
records the actual UTC window — honest evidence either way.
"""
import subprocess
import sys
import time
from datetime import datetime, timezone

TARGET = datetime(2026, 9, 28, 20, 50, 0, tzinfo=timezone.utc)
COLLECTOR = "/Users/hoangminhlong/my-quantitative/research/control/DATA-FOUNDATION-SIXSOURCE-V1/ibkr_fx/collect_fx_ticks.py"
PY = "/Users/hoangminhlong/my-quantitative/.venv/bin/python"

delta = (TARGET - datetime.now(timezone.utc)).total_seconds()
if delta > 0:
    print(f"sleeping {delta:.0f}s until {TARGET.isoformat()}", flush=True)
    time.sleep(delta)
print("launching rollover_window collector", flush=True)
r = subprocess.run([PY, COLLECTOR, "--seconds", "1800", "--tag", "rollover_window"])
sys.exit(r.returncode)
