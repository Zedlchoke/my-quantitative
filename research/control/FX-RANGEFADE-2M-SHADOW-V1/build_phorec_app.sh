#!/bin/zsh
# Phorec.app builder — PyInstaller + pywebview/WKWebView (owner order 2026-09-24).
#
# Safety laws (owner: "Backup bản cũ có thể phục hồi, build vào vị trí tạm rồi
# thay thế an toàn; quản lý chỉ tiến trình do app sở hữu"):
#   - NO rm -rf of the existing app: the current bundle is MOVED aside to
#     ~/Applications/Phorec-prev-<timestamp>.app (fully restorable by mv back);
#   - build into a TEMP stage dir first, verify the binary answers --check,
#     only then move it into place;
#   - NO pkill anywhere: the app does not own the shadow daemon; the daemon
#     is started/stopped only by launch_phorec.sh / its own operator.
set -e
CYCLE="${0:A:h}"
APP="$HOME/Applications/Phorec.app"
VENV_PY="/Users/hoangminhlong/my-quantitative/.venv/bin/python"
PYI="/Users/hoangminhlong/my-quantitative/.venv/bin/pyinstaller"
STAGE="$CYCLE/dist_phorec_stage"

test -x "$VENV_PY"
test -f "$CYCLE/phorec_app_entry.py"
test -f "$CYCLE/dashboard/index.html"
test -f "$CYCLE/dashboard/assets/logo.jpg"

mkdir -p "$STAGE"

# icon từ logo của owner (JPEG → PNG một lần, rồi icns)
TMPD="$(mktemp -d)"
MASTER="$TMPD/logo.png"
sips -s format png "$CYCLE/dashboard/assets/logo.jpg" --out "$MASTER" >/dev/null
ICONSET="$TMPD/phorec.iconset"
mkdir -p "$ICONSET"
for s in 16 32 128 256 512; do
  sips -z $s $s "$MASTER" --out "$ICONSET/icon_${s}x${s}.png" >/dev/null
  sips -z $((s*2)) $((s*2)) "$MASTER" --out "$ICONSET/icon_${s}x${s}@2x.png" >/dev/null
done
ICON="$TMPD/phorec.icns"
iconutil -c icns "$ICONSET" -o "$ICON"

"$PYI" \
  --name Phorec --windowed --noconfirm --clean \
  --icon "$ICON" \
  --hidden-import webview.platforms.cocoa \
  --add-data "$CYCLE/dashboard/index.html:." \
  --add-data "$CYCLE/dashboard/assets/logo.jpg:." \
  --distpath "$STAGE" --workpath "$STAGE/build" --specpath "$STAGE" \
  "$CYCLE/phorec_app_entry.py"

BUILT="$STAGE/Phorec.app"
test -x "$BUILT/Contents/MacOS/Phorec"

# verify the staged binary answers --check before it replaces anything
"$BUILT/Contents/MacOS/Phorec" --check

if [[ -d "$APP" ]]; then
  STAMP="$(date +%Y%m%d-%H%M%S)"
  BACKUP="$HOME/Applications/Phorec-prev-$STAMP.app"
  mv "$APP" "$BACKUP"
  echo "old app preserved at $BACKUP (mv back to restore)"
fi
mv "$BUILT" "$APP"
echo "built $APP"
echo "note: the app only READS state; the shadow daemon runs independently (launch_phorec.sh)"
