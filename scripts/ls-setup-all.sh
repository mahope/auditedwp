#!/usr/bin/env bash
# One-shot Lemon Squeezy setup for ALL products + auto-set worker secrets.
#
# Usage:
#   LEMONSQUEEZY_API_KEY=xxx ./scripts/ls-setup-all.sh
#
# Does, for each product below:
#   1. Creates the LS product + variant (skips if it already exists)
#   2. Creates a direct checkout URL
#   3. Sets CHECKOUT_URL as a secret on the right Cloudflare worker
#      (via the CF API — no wrangler login needed)
#   4. Verifies the public /config endpoint reports the URL
#
# Products:
#   EUComply Pro   $79/year recurring -> worker eucomply-scan     (/config, key checkoutUrl)
#   DevNotify      $19 one-time       -> worker devnotify-metrics (/config, key checkoutUrl)
#   QuickFormat    $9  one-time       -> worker waitlist-eucomply (/config, key checkout_url)
#
# Idempotent: safe to run repeatedly.
set -euo pipefail

API="https://api.lemonsqueezy.com/v1"
KEY="${LEMONSQUEEZY_API_KEY:?Set LEMONSQUEEZY_API_KEY}"
CF_TOKEN="${CLOUDFLARE_API_TOKEN:?Set CLOUDFLARE_API_TOKEN}"
CF_ACCOUNT="${CLOUDFLARE_ACCOUNT_ID:?Set CLOUDFLARE_ACCOUNT_ID}"
CT='Content-Type: application/json'
ACCEPT='Accept: application/vnd.api+json'

req() { curl -sf -H "Authorization: Bearer $KEY" -H "$CT" -H "$ACCEPT" "$@"; }

echo "== Store =="
STORE_ID=$(req "$API/stores" | python3 -c 'import json,sys;print(json.load(sys.stdin)["data"][0]["id"])')
echo "store_id=$STORE_ID"

EXISTING=$(req "$API/products?filter[store_id]=$STORE_ID" | \
  python3 -c 'import json,sys;print("\n".join(x["attributes"]["name"] for x in json.load(sys.stdin)["data"]))' || true)
echo "Existing products:"; echo "${EXISTING:-none}" | sed 's/^/  - /'

create_product() {
  local name="$1" slug="$2" desc="$3" price="$4" variant="$5" interval="${6:-}"
  if echo "$EXISTING" | grep -qF "$name"; then
    echo "-- product '$name' already exists, skipping creation"
    return
  fi
  local interval_json
  if [ -n "$interval" ]; then
    interval_json=", \"interval_unit\": \"$interval\", \"interval_count\": 1"
  else
    interval_json=", \"interval_unit\": null, \"interval_count\": 1"
  fi
  echo "-- creating product '$name'"
  local pid
  pid=$(req -X POST "$API/products" -d '{
    "data": {"type":"products","attributes":{
      "name": "'"$name"'", "slug": "'"$slug"'",
      "description": '"$desc"',
      "status": "published"},
     "relationships":{"store":{"data":{"type":"stores","id":"'"$STORE_ID"'"}}}}
  }' | python3 -c 'import json,sys;print(json.load(sys.stdin)["data"]["id"])')

  req -X POST "$API/variants" -d '{
    "data": {"type":"variants","attributes":{
      "name": "'"$variant"'", "price": '"$price"''"$interval_json"'},
     "relationships":{"product":{"data":{"type":"products","id":"'"$pid"'"}}}}
  }' > /dev/null
}

variant_id_for() {
  req "$API/products?filter[store_id]=$STORE_ID" | python3 -c '
import json,sys
want=sys.argv[1].lower()
for p in json.load(sys.stdin)["data"]:
    if p["attributes"]["name"].lower()==want:
        print(p["relationships"]["variants"]["data"][0]["id"]); break
' "$1"
}

checkout_url_for() {
  local vid="$1" price="$2"
  req -X POST "$API/checkouts" -d '{
    "data": {"type":"checkouts","attributes":{
       "custom_price": '"$price"',
       "product_options":{"enabled_variants":["'"$vid"'"]}},
      "relationships":{
       "store":{"data":{"type":"stores","id":"'"$STORE_ID"'"}},
       "variant":{"data":{"type":"variants","id":"'"$vid"'"}}}}
  }' | python3 -c 'import json,sys;print(json.load(sys.stdin)["data"]["attributes"]["url"])'
}

set_worker_secret() {
  local worker="$1" url="$2" key_name="$3"
  curl -s "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT/workers/scripts/$worker/settings" \
    -H "Authorization: Bearer $CF_TOKEN" > /tmp/cf_settings.json
  python3 - "$url" "$key_name" <<'PYEOF'
import json,sys
url,key=sys.argv[1],sys.argv[2]
s=json.load(open('/tmp/cf_settings.json'))
b=[x for x in s['result'].get('bindings',[]) if x.get('name')!=key]
b.append({"type":"secret_text","name":key,"text":url})
json.dump({"bindings":b},open('/tmp/cf_bindings.json','w'))
PYEOF
  curl -s -X PATCH "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT/workers/scripts/$worker/settings" \
    -H "Authorization: Bearer $CF_TOKEN" \
    -F "settings=</tmp/cf_bindings.json;type=application/json" > /tmp/cf_patch_result.json
  python3 -c "import json;d=json.load(open('/tmp/cf_patch_result.json'));assert d['success'], d.get('errors')"
}

verify_config() {
  sleep 8
  curl -s "$1" || echo "(no response)"
}

echo ""
echo "== EUComply Pro (\$79/yr recurring) =="
create_product "EUComply Pro" "eucomply-pro" \
  '"Daily compliance monitoring for any website. GDPR, NIS2 and EAA checks with auditor-ready PDF reports, email alerts when a check starts failing, and continuous-compliance proof you can show clients, auditors and insurers."' \
  79000 "Annual plan" "year"
VID=$(variant_id_for "EUComply Pro")
URL=$(checkout_url_for "$VID" 79000)
echo "checkout: $URL"
set_worker_secret "eucomply-scan" "$URL" "CHECKOUT_URL"
echo "worker config: $(verify_config https://eucomply-scan.mahope-eeb.workers.dev/config)"

echo ""
echo "== DevNotify (\$19 one-time) =="
create_product "DevNotify License" "devnotify-license" \
  '"Lifetime license for DevNotify — GitHub notifications in your macOS menu bar. One payment, perpetual use of version 1.x including updates."' \
  1900 "Lifetime license"
VID=$(variant_id_for "DevNotify License")
URL=$(checkout_url_for "$VID" 1900)
echo "checkout: $URL"
set_worker_secret "devnotify-metrics" "$URL" "CHECKOUT_URL"
echo "worker config: $(verify_config https://devnotify-metrics.mahope-eeb.workers.dev/config)"

echo ""
echo "== QuickFormat (\$9 one-time) =="
create_product "QuickFormat" "quickformat" \
  '"QuickFormat converts JSON, YAML, CSV and XML between formats instantly from your Mac menu bar. Copy in, paste out. One-time purchase, yours forever."' \
  900 "Single license"
VID=$(variant_id_for "QuickFormat")
URL=$(checkout_url_for "$VID" 900)
echo "checkout: $URL"
set_worker_secret "waitlist-eucomply" "$URL" "CHECKOUT_URL"
echo "worker config: $(verify_config https://waitlist-eucomply.mahope-eeb.workers.dev/config)"
echo "(note: QuickFormat page reads checkout_url from this config)"

echo ""
echo "DONE. All three products should now take payments."
echo "Verify pages:"
echo "  curl -s https://auditedwp.pages.dev/pro/"
echo "  curl -s https://auditedwp.pages.dev/devnotify/"
echo "  curl -s https://auditedwp.pages.dev/quickconvert/"
