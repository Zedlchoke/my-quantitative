#!/bin/bash
# Build PaperDesk.app in ONE command:
#   ./apps/paperdesk/build_app.sh
# Output: apps/paperdesk/build/PaperDesk-app/PaperDesk.app
# (Electron runtime; chosen over SwiftUI because this machine's Command Line
#  Tools Swift 6.1 toolchain is broken — duplicate SwiftBridging modulemap —
#  while node/npm are healthy; see TOOLCHAIN_BLOCKER_NOTE in research/control.)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

PY=/Users/hoangminhlong/my-quantitative/.venv/bin/python

# 1. deps (idempotent)
if [ ! -d node_modules/electron ]; then
  npm install --no-audit --no-fund
fi

# 2. icon (drawn by Electron's own chromium; resized with sips; packed by iconutil)
if [ ! -f Resources/PaperDeskIcon.icns ]; then
  mkdir -p Resources build/icon.iconset
  npx electron icon_gen.js build/icon_1024.png
  for spec in "16 icon_16x16" "32 icon_16x16@2x" "32 icon_32x32" \
              "64 icon_32x32@2x" "128 icon_128x128" "256 icon_128x128@2x" \
              "256 icon_256x256" "512 icon_256x256@2x" "512 icon_512x512" \
              "1024 icon_512x512@2x"; do
    set -- $spec
    sips -z "$1" "$1" build/icon_1024.png \
      --out "build/icon.iconset/$2.png" >/dev/null
  done
  iconutil -c icns build/icon.iconset -o Resources/PaperDeskIcon.icns
fi

# 3. package (.app with its own Electron runtime, ad-hoc signed by packager)
npx electron-packager . PaperDesk --platform=darwin --arch=arm64 \
  --icon=Resources/PaperDeskIcon.icns --app-bundle-id=com.myquant.paperdesk \
  --app-version=1.0.0 --overwrite --out=build \
  --app-copyright="SPORTS-PAPERTRADE-EXEC-V1 / AMENDMENT_MACOS_APP_UI_V1 / paper money only"

APP="build/PaperDesk-darwin-arm64/PaperDesk.app"
# extra ad-hoc re-sign (packager already signs; keep explicit + verify)
codesign --force --deep -s - "$APP" >/dev/null 2>&1 || true
codesign --verify "$APP" && echo "codesign OK"

echo
echo "built: $HERE/$APP"
echo "run:   open \"$HERE/$APP\""
echo "cli:   \"$APP/Contents/MacOS/PaperDesk\" --self-check-ledger <ledger.jsonl>"
