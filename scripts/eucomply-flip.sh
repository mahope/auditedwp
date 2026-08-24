#!/usr/bin/env bash
# EUComply Pro — flip from waitlist to live LS checkout.
# Usage:  ./scripts/eucomply-flip.sh "https://eucomply.lemonsqueezy.com/buy/xxxx"
# Idempotent: safe to run twice. No deploy needed — the page detects checkoutUrl at runtime.
set -euo pipefail
URL="${1:?Usage: eucomply-flip.sh <checkout-url>}"
cd "$(dirname "$0")/.."

echo "=== EUComply Pro flip ==="
echo "Checkout URL: $URL"

# Set the CHECKOUT_URL secret on the worker via wrangler
# The pro page fetches /config at runtime and auto-switches
echo ""
echo "Step 1: Set worker secret"
echo "Run: wrangler secret put CHECKOUT_URL --name eucomply-scan"
echo "Value: $URL"
echo ""
echo "Step 2: Verify"
echo "curl -s https://eucomply-scan.mahope-eeb.workers.dev/config | jq .checkoutUrl"
echo "Expected: \"$URL\""
echo ""
echo "Step 3: Verify on page"
echo "curl -s https://auditedwp.pages.dev/pro/ | grep -c 'Join the waitlist'"
echo "Expected: 0 (waitlist hidden when checkout is live)"
echo ""
echo "The pro page will auto-detect and switch to live checkout."
echo "Waitlist section hides automatically — no deploy needed."