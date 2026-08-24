#!/usr/bin/env bash
# Package DevNotify Chrome Extension for Chrome Web Store upload
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="${DIR}/devnotify-chrome-extension.zip"
SRC="${DIR}"

echo "==> Packaging DevNotify Chrome extension..."

# Build from source dir — only include files CWS needs
cd "$SRC"

# Files to exclude
EXCLUDES=(
  "generate_icons.py"
  "*.zip"
  ".gitkeep"
)

rm -f "$OUT"

# Build zip
zip -r "$OUT" \
  manifest.json \
  background.js \
  icons/icon-16.png \
  icons/icon-48.png \
  icons/icon-128.png \
  popup/popup.html \
  popup/popup.js \
  -x "${EXCLUDES[@]}"

echo "==> Package created: $OUT"
echo "    Size: $(du -h "$OUT" | cut -f1)"
echo ""
echo "    Next step: Upload to Chrome Web Store Developer Dashboard"
echo "    https://chrome.google.com/webstore/devconsole"
echo ""
echo "    Or via API (when CWS OAuth credentials available in Bitwarden):"
echo "    npx chrome-webstore-upload upload --source $OUT ..."