#!/bin/bash
# Phases H+I — REAL runner lifecycle takeover (owner law). Requires the
# launchd-managed precondition (the main e2e battery must NOT be run in
# parallel). Idempotent: reloads the launchd agent itself when absent.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
APP="$HERE/build/PaperDesk-darwin-arm64/PaperDesk.app/Contents/MacOS/PaperDesk"
EV="${1:-$HERE/build/e2e_evidence}"
PY=/Users/hoangminhlong/my-quantitative/.venv/bin/python
REAL_OPS="$HOME/.my-quantitative-data/sports-papertrade-exec-v1/ops"
mkdir -p "$EV"
PASS=0; FAIL=0
ok()   { PASS=$((PASS+1)); echo "[PASS] $*"; }
bad()  { FAIL=$((FAIL+1)); echo "[FAIL] $*"; }
check(){ if [ "$1" = "0" ]; then ok "$2"; else bad "$2"; fi; }

echo "== PRE: launchd-managed runner precondition ="
launchctl print "gui/$(id -u)/com.myquant.sptexec.ops" >/dev/null 2>&1
if [ $? -ne 0 ]; then
  launchctl load "$HOME/Library/LaunchAgents/com.myquant.sptexec.ops.plist"
  sleep 10
fi
launchctl print "gui/$(id -u)/com.myquant.sptexec.ops" >/dev/null 2>&1
check $? "PRE launchd agent loaded"
sleep 12
$PY -c "
import json,sys,datetime
hb=json.load(open('$REAL_OPS/state/heartbeat.json'))
age=(datetime.datetime.utcnow()-datetime.datetime.strptime(hb['ts_utc'],'%Y-%m-%dT%H:%M:%SZ')).total_seconds()
sys.exit(0 if hb.get('pid') and age < 180 else 1)"; check $? "PRE runner heartbeat FRESH"

T0=$(date +%s)
# foreground run (background launches of later instances have shown silent
# early exits under the test harness; foreground is deterministic)
$PY -c "
import json,sys,datetime
hb=json.load(open('$REAL_OPS/state/heartbeat.json'))
age=(datetime.datetime.utcnow()-datetime.datetime.strptime(hb['ts_utc'],'%Y-%m-%dT%H:%M:%SZ')).total_seconds()
sys.exit(0 if hb.get('pid') and age < 180 else 1)"; check $? "H1 runner FRESH pre-quit"
"$APP" --auto-quit 30 --yes >"$EV/phase_h_app.log" 2>&1
HAPP_RC=$?
[ $HAPP_RC -eq 0 ]; check $? "H0 phase-H app ran to graceful quit (rc=0)"
launchctl print "gui/$(id -u)/com.myquant.sptexec.ops" >/dev/null 2>&1
[ $? -ne 0 ]; check $? "H2 launchd agent booted out (no auto-run at login)"
[ -f "$REAL_OPS/control/takeover.json" ]; check $? "H3 takeover record written"
# robust freshness checks (never fooled by stale journal entries)
$PY -c "
import json, sys, datetime
t0 = float('$T0')
rows=[json.loads(l) for l in open('$REAL_OPS/state/incidents.jsonl') if l.strip()]
ss=[r['ts_utc'] for r in rows if r.get('kind')=='SERVICE_STOP']
fresh=[s for s in ss if datetime.datetime.strptime(s,'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc).timestamp() >= t0 - 5]
sys.exit(0 if fresh else 1)"; check $? "H4 fresh SERVICE_STOP journaled (post-script-start)"
$PY -c "
import json, sys, datetime
t0 = float('$T0')
rows=[json.loads(l) for l in open('$REAL_OPS/control/controller_log.jsonl') if l.strip()]
g=[r for r in rows if r.get('event')=='GRACEFUL_STOP_BEGIN'
   and (r.get('detail') or {}).get('source')=='launchd'
   and datetime.datetime.strptime(r['ts_utc'],'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc).timestamp() >= t0 - 5]
sys.exit(0 if g else 1)"; check $? "H4b quit flow journaled with source=launchd"
"$PY" "$HERE/helpers/opslock.py" probe "$REAL_OPS/service.lock" | grep -q FREE
check $? "H5 real service.lock released"

echo "== PHASE I: reopen — app spawns its own runner (launchd now absent) ="
T1=$(date +%s)
"$APP" --auto-quit 40 --yes >"$EV/phase_i_app.log" 2>&1
IRC=$?
[ $IRC -eq 0 ]; check $? "I0 phase-I app ran to graceful quit (rc=0)"
# I1: the app SPAWNED its own runner (fresh SPAWN_CHILD in the controller
# journal after T1 — launchd was already gone, so a child is the only way)
$PY -c "
import json, sys, datetime
t1 = float('$T1')
rows=[json.loads(l) for l in open('$REAL_OPS/control/controller_log.jsonl') if l.strip()]
sp=[r['ts_utc'] for r in rows if r.get('event')=='SPAWN_CHILD'
    and datetime.datetime.strptime(r['ts_utc'],'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc).timestamp() >= t1 - 5]
sys.exit(0 if sp else 1)"; check $? "I1 app spawned its own runner (fresh SPAWN_CHILD)"
$PY -c "
import json, sys, datetime
t1 = float('$T1')
rows=[json.loads(l) for l in open('$REAL_OPS/state/incidents.jsonl') if l.strip()]
ss=[r['ts_utc'] for r in rows if r.get('kind')=='SERVICE_STOP']
fresh=[s for s in ss if datetime.datetime.strptime(s,'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc).timestamp() >= t1 - 5]
sys.exit(0 if fresh else 1)"; check $? "I2 fresh SERVICE_STOP on second quit"

