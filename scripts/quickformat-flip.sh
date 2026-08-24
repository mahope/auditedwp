#!/usr/bin/env bash
# QuickFormat — flip from waitlist/demo mode to live LS checkout.
# Usage:  ./scripts/quickformat-flip.sh "https://quickformat.lemonsqueezy.com/buy/xxxx"
# Idempotent: safe to run twice. No deploy needed — the page detects
# checkoutUrl at runtime via the /config endpoint.
set -euo pipefail
URL="${1:?Usage: quickformat-flip.sh <checkout-url>}"
cd "$(dirname "$0")/.."

echo "=== QuickFormat flip ==="
echo "Checkout URL: $URL"

if ! command -v wrangler >/dev/null 2>&1; then
  echo "FEJL: wrangler ikke fundet i PATH"; exit 1
fi

echo ""
echo "Step 1: Set worker secret (CHECKOUT_URL on eucomply-scan — shared waitlist worker)"
printf '%s' "$URL" | wrangler secret put CHECKOUT_URL --name eucomply-scan

echo ""
echo "Step 2: Verify worker config"
CONFIG=$(curl -s https://eucomply-scan.mahope-eeb.workers.dev/config)
echo "$CONFIG"
echo "$CONFIG" | grep -q "$URL" && echo "OK: checkout URL live on /config" || { echo "FEJL: URL matcher ikke"; exit 1; }

echo ""
echo "Step 3: Verify page behavior"
echo "Open https://auditedwp.pages.dev/quickconvert/ — 'Buy QuickFormat' button should link to LS checkout."
echo ""

echo "Manual check: curl -s https://auditedwp.pages.dev/quickconvert/ | grep -o 'href=\"[^\"]*lemonsqueezy[^\"]*\"'"
echo "If the checkout URL is found, the flip worked."

echo ""
echo "Completed. QuickFormat can now accept payments."