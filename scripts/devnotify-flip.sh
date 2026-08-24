#!/usr/bin/env bash
# DevNotify — flip from waitlist to live LS checkout.
# Usage:  ./scripts/devnotify-flip.sh "https://devnotify.lemonsqueezy.com/buy/xxxx"
# Idempotent: safe to run twice. No deploy needed — the page detects
# checkoutUrl at runtime via the /config endpoint.
set -euo pipefail
URL="${1:?Usage: devnotify-flip.sh <checkout-url>}"
cd "$(dirname "$0")/.."

echo "=== DevNotify flip ==="
echo "Checkout URL: $URL"

if ! command -v wrangler >/dev/null 2>&1; then
  echo "FEJL: wrangler ikke fundet i PATH"; exit 1
fi

echo ""
echo "Step 1: Set worker secret (CHECKOUT_URL on devnotify-metrics)"
printf '%s' "$URL" | wrangler secret put CHECKOUT_URL --name devnotify-metrics

echo ""
echo "Step 2: Verify worker config"
GOT=$(curl -s https://devnotify-metrics.mahope-eeb.workers.dev/config)
echo "$GOT"
echo "$GOT" | grep -q "$URL" && echo "OK: checkout URL live in /config" || { echo "FEJL: URL matcher ikke"; exit 1; }

echo ""
echo "Step 3: Verify page behavior"
echo "curl -s https://auditedwp.pages.dev/devnotify/ | grep -c 'Buy license — get notified'"
echo "(static HTML still shows waitlist button — runtime JS swaps it to checkout)"
echo ""
echo "Manual check: open https://auditedwp.pages.dev/devnotify/#buy — button should now say 'Buy license — $19' and link to LS."
