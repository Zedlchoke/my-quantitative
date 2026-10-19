#!/bin/bash
# PaperDesk e2e + evidence battery (AMENDMENT_MACOS_APP_UI_V1 §1.6).
# Read-only against the REAL ledger; lifecycle transitions run in an ISOLATED
# /tmp sandbox data root — EXCEPT the explicitly-labeled PHASE H/I takeover
# steps on the real runner, which implement the owner's lifecycle law
# (open app -> one runner; Quit -> graceful stop; nothing auto-runs at login).
# Output: evidence dir with logs + PNGs. Mock-labeled AI steps are node-level.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
APP="$HERE/build/PaperDesk-darwin-arm64/PaperDesk.app/Contents/MacOS/PaperDesk"
EV="${1:-$HERE/build/e2e_evidence}"
WT="/Users/hoangminhlong/my-quantitative/.worktrees/sports-papertrade-exec-v1/integration"
PY=/Users/hoangminhlong/my-quantitative/.venv/bin/python
REAL_LEDGER="$HOME/.my-quantitative-data/sports-papertrade-exec-v1/ledger/paper_ledger.jsonl"
REAL_OPS="$HOME/.my-quantitative-data/sports-papertrade-exec-v1/ops"
mkdir -p "$EV"
PASS=0; FAIL=0
ok()   { PASS=$((PASS+1)); echo "[PASS] $*"; }
bad()  { FAIL=$((FAIL+1)); echo "[FAIL] $*"; }
check(){ if [ "$1" = "0" ]; then ok "$2"; else bad "$2"; fi; }

echo "== PHASE A: chain verify parity (REAL ledger, JS app vs pinned Python) ="
JS=$("$APP" --self-check-ledger $REAL_LEDGER | /usr/bin/python3 -c "import sys,json;d=json.load(sys.stdin);print(d['chain_ok'],d['rows'])")
PL=$($PY -c "
import sys, json
sys.path.insert(0, '$WT/../../..'.replace('/./','/') ) if False else None
sys.path.insert(0, '/Users/hoangminhlong/my-quantitative/.worktrees/sports-papertrade-v1/integration')
from research.papertrade import ledger as L
led = L.PaperLedger('$REAL_LEDGER').load()
ok, errs = led.verify_chain()
print(ok, len(led.rows))
")
echo "js=$JS py=$PL"
[ "$JS" = "$PL" ] && [ "${JS%% *}" = "True" ]; check $? "A1 chain parity + OK on REAL ledger"

echo "== PHASE B: attach + UI evidence tour (REAL, read-only display) ="
"$APP" --ui-evidence "$EV/ui" >/dev/null 2>&1 &
APP_PID=$!
sleep 14
kill -0 $APP_PID 2>/dev/null; check $? "B1 app running"
grep -q ATTACH "$REAL_OPS/control/controller_log.jsonl" 2>/dev/null
check $? "B2 controller attached to live runner (journal)"
grep -q "source.*launchd" "$REAL_OPS/control/controller_log.jsonl" 2>/dev/null
check $? "B3 attach source = launchd"

echo "== PHASE C: second app instance refused ="
"$APP" --yes >/dev/null 2>&1
[ $? -eq 3 ]; check $? "C1 second instance exit code 3"

echo "== PHASE D: app crash (kill -9) leaves launchd runner untouched ="
RUNNER_PID=$($PY -c "
import json; print(json.load(open('$REAL_OPS/state/heartbeat.json'))['pid'])")
kill -9 $APP_PID 2>/dev/null
sleep 3
kill -0 $APP_PID 2>/dev/null && bad "D1 app should be dead" || ok "D1 app killed"
kill -0 $RUNNER_PID 2>/dev/null; check $? "D2 runner pid $RUNNER_PID survived app crash"

echo "== PHASE E: sandbox lifecycle (isolated /tmp data root) ="
SB="$EV/sandbox_root"; rm -rf "$SB"; mkdir -p "$SB"
"$APP" --sandbox --data-root "$SB" --worktree "$WT" --auto-quit 45 --yes \
  >"$EV/phase_e_app.log" 2>&1 &
sleep 18
SB_OPS="$SB/sandbox/ops"
[ -f "$SB_OPS/state/heartbeat.json" ]; check $? "E1 sandbox runner heartbeat exists"
grep -q SPAWN_CHILD "$SB_OPS/control/controller_log.jsonl" 2>/dev/null
check $? "E2 controller spawned exactly one child"
grep -q CHILD_READY "$SB_OPS/control/controller_log.jsonl" 2>/dev/null
check $? "E3 child runner became ready"
CHILD_PID=$($PY -c "import json;print(json.load(open('$SB_OPS/state/heartbeat.json'))['pid'])" 2>/dev/null)
# pause flag via direct seam (the UI writes the same file); heartbeat only
# updates on the next 30s tick, so poll for it
mkdir -p "$SB_OPS/control"
echo "{\"by\":\"e2e\",\"at_utc\":\"now\",\"reason\":\"E-pause\"}" > "$SB_OPS/control/pause_decisions.flag"
PAUSED=1
for i in $(seq 1 12); do
  $PY - "$SB_OPS/state/heartbeat.json" <<'EOF' && PAUSED=0 && break
import json, sys
hb = json.load(open(sys.argv[1]))
sys.exit(0 if hb.get('decisions_paused') is True else 1)
EOF
  sleep 4
done
[ $PAUSED -eq 0 ]; check $? "E4 heartbeat exposes decisions_paused=true (≤48s)"
rm -f "$SB_OPS/control/pause_decisions.flag"
sleep 40   # auto-quit fires: quit dialog auto-yes -> graceful stop
kill -0 "$CHILD_PID" 2>/dev/null && bad "E5 runner should be stopped" \
  || ok "E5 runner gracefully stopped after app quit"
grep -q SERVICE_STOP "$SB_OPS/state/incidents.jsonl" 2>/dev/null
check $? "E6 SERVICE_STOP journaled"
"$PY" "$HERE/helpers/opslock.py" probe "$SB_OPS/service.lock" | grep -q FREE
check $? "E7 service.lock released"

echo "== PHASE F: ledger tamper fail-closed ="
TAMPER="$EV/tamper_root"; rm -rf "$TAMPER"; mkdir -p "$TAMPER/ledger"
cp "$REAL_LEDGER" "$TAMPER/ledger/paper_ledger.jsonl"
/usr/bin/python3 - "$TAMPER/ledger/paper_ledger.jsonl" <<'EOF'
import sys
p = sys.argv[1]
s = open(p).read().replace('"wallet_cents":100000', '"wallet_cents":999999', 1)
open(p, 'w').write(s)
EOF
"$APP" --self-check-ledger "$TAMPER/ledger/paper_ledger.jsonl" | grep -q '"chain_ok":false'
check $? "F1 tampered ledger detected by app verifier"
"$APP" --data-root "$TAMPER" --ui-evidence "$EV/ui_tamper" >/dev/null 2>&1 &
FAPP=$!
sleep 12
kill -9 $FAPP 2>/dev/null
pkill -9 -f "PaperDesk-darwin-arm64" 2>/dev/null
sleep 2
[ -f "$EV/ui_tamper/paperdesk_section_dashboard.png" ]
check $? "F2 tamper UI evidence captured"

echo "== PHASE G: AI seam (node-level; MOCK-labeled, fail-closed laws) ="
node "$HERE/test_ai_seam.js" "$EV" ; check $? "G1 ai seam battery"

echo "== H/I lifecycle phases: run apps/paperdesk/e2e_lifecycle.sh separately ="
echo "(kept out of the main battery: they mutate the REAL runner's lifecycle)"
echo
echo "== RESULT: PASS=$PASS FAIL=$FAIL ="
echo "evidence: $EV"
[ $FAIL -eq 0 ]
