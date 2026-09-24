#!/bin/zsh
set -e
CYCLE="${0:A:h}"
APP="$HOME/Applications/Phorec.app"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
# icon từ logo của owner (convert JPEG→PNG một lần, rồi resize từ PNG)
TMPD="$(mktemp -d)"
MASTER="$TMPD/logo.png"
sips -s format png "$CYCLE/dashboard/assets/logo.jpg" --out "$MASTER" >/dev/null
ICONSET="$TMPD/phorec.iconset"
mkdir -p "$ICONSET"
for s in 16 32 128 256 512; do
  sips -z $s $s "$MASTER" --out "$ICONSET/icon_${s}x${s}.png" >/dev/null
  sips -z $((s*2)) $((s*2)) "$MASTER" --out "$ICONSET/icon_${s}x${s}@2x.png" >/dev/null
done
iconutil -c icns "$ICONSET" -o "$APP/Contents/Resources/phorec.icns"
cat > "$APP/Contents/Info.plist" <<'PL'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>Phorec</string>
  <key>CFBundleDisplayName</key><string>Phorec</string>
  <key>CFBundleExecutable</key><string>Phorec</string>
  <key>CFBundleIconFile</key><string>phorec</string>
  <key>CFBundleIdentifier</key><string>vn.phorec.fxshadow</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>1.0</string>
  <key>NSHighResolutionCapable</key><true/>
</dict></plist>
PL
cat > "$APP/Contents/MacOS/Phorec" <<'SH2'
#!/bin/zsh
CYCLE="/Users/hoangminhlong/my-quantitative/.worktrees/fx-rangefade-2m-shadow-v1/research/control/FX-RANGEFADE-2M-SHADOW-V1"
PY="/Users/hoangminhlong/my-quantitative/.venv/bin/python"
# chỉ kill process của CYCLE này (pattern có đường dẫn riêng, không đụng session khác)
pkill -f "$CYCLE/daemon/shadow_daemon.py" 2>/dev/null
pkill -f "$CYCLE/dashboard/serve.py" 2>/dev/null
sleep 1
nohup "$PY" "$CYCLE/daemon/shadow_daemon.py" >> "$CYCLE/daemon.log" 2>&1 < /dev/null &
nohup "$PY" "$CYCLE/dashboard/serve.py" >> "$CYCLE/dashboard.log" 2>&1 < /dev/null &
for i in {1..20}; do
  curl -s -o /dev/null --max-time 2 http://127.0.0.1:8766/state.json && break
  sleep 1
done
open -na "Google Chrome" --args --app=http://127.0.0.1:8766 --window-size=1560,1000
exit 0
SH2
chmod +x "$APP/Contents/MacOS/Phorec"
echo "built $APP"
