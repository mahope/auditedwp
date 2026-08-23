#!/usr/bin/env bash
# DevNotify — Lemon Squeezy setup. Run once when the LS API key is available.
# Usage:  LEMONSQUEEZY_API_KEY=xxx ./ls-setup.sh
# Creates (idempotent-ish): checks existing products first, then creates
# "DevNotify License" at $19 USD one-time and prints the checkout URL.
set -euo pipefail

API="https://api.lemonsqueezy.com/v1"
KEY="${LEMONSQUEEZY_API_KEY:?Set LEMONSQUEEZY_API_KEY}"
AUTH="Authorization: Bearer $KEY"
CT='Content-Type: application/json'
ACCEPT='Accept: application/vnd.api+json'

req() { curl -sf -H "$AUTH" -H "$CT" -H "$ACCEPT" "$@"; }

echo "== 1. Store =="
STORE_ID=$(req "$API/stores" | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d["data"][0]["id"])')
echo "store_id=$STORE_ID"

echo "== 2. Existing products (skip if already created) =="
EXISTING=$(req "$API/products?filter[store_id]=$STORE_ID" | \
  python3 -c 'import json,sys;d=json.load(sys.stdin);print(",".join(x["attributes"]["name"] for x in d["data"]))' || true)
echo "existing: ${EXISTING:-none}"
if echo "$EXISTING" | grep -qi "devnotify"; then
  echo "DevNotify product already exists — nothing to do."
  exit 0
fi

echo "== 3. Create product 'DevNotify License' =="
PRODUCT=$(req -X POST "$API/products" -d '{
  "data": {
    "type": "products",
    "attributes": {
      "name": "DevNotify License",
      "slug": "devnotify-license",
      "description": "Lifetime license for DevNotify — GitHub notifications in your macOS menu bar. One payment, perpetual use of version 1.x including updates.",
      "price": 1900,
      "status": "published",
      "price_formatted": "$19"
    },
    "relationships": {
      "store": { "data": { "type": "stores", "id": "'"$STORE_ID"'" } }
    }
  }
}')
PRODUCT_ID=$(echo "$PRODUCT" | python3 -c 'import json,sys;print(json.load(sys.stdin)["data"]["id"])')
echo "product_id=$PRODUCT_ID"

echo "== 4. Create variant: $19 one-time =="
VARIANT=$(req -X POST "$API/variants" -d '{
  "data": {
    "type": "variants",
    "attributes": { "name": "Lifetime license", "price": 1900, "interval_unit": null, "interval_count": 1 },
    "relationships": {
      "product": { "data": { "type": "products", "id": "'"$PRODUCT_ID"'" } }
    }
  }
}')
VARIANT_ID=$(echo "$VARIANT" | python3 -c 'import json,sys;print(json.load(sys.stdin)["data"]["id"])')
echo "variant_id=$VARIANT_ID"

echo "== 5. Checkout URL =="
CHECKOUT=$(req -X POST "$API/checkouts" -d '{
  "data": {
    "type": "checkouts",
    "attributes": { "custom_price": 1900, "product_options": { "enabled_variants": ['"$VARIANT_ID"'] } },
    "relationships": {
      "store": { "data": { "type": "stores", "id": "'"$STORE_ID"'" } },
      "variant": { "data": { "type": "variants", "id": "'"$VARIANT_ID"'" } }
    }
  }
}')
URL=$(echo "$CHECKOUT" | python3 -c 'import json,sys;print(json.load(sys.stdin)["data"]["attributes"]["url"])')
echo ""
echo "CHECKOUT_URL=$URL"
echo "Next: put this URL into site/devnotify/index.html (replace notify-form block),"
echo "then the same on the 4 subpages, run ./deploy.sh and verify each page."
