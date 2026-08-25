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

TMPDIR_LS="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_LS"' EXIT

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
  # API tokens cannot use the /secrets endpoint — patch bindings via settings (multipart) instead
  curl -s "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT/workers/scripts/$worker/settings" \
    -H "Authorization: Bearer $CF_TOKEN" > "$TMPDIR_LS/cf_settings.json"
  python3 - "$url" "$key_name" "$TMPDIR_LS" <<'PYEOF'
import json,sys
url,key,tmp=sys.argv[1],sys.argv[2],sys.argv[3]
s=json.load(open(tmp+'/cf_settings.json'))
b=[x for x in s['result'].get('bindings',[]) if x.get('name')!=key]
b.append({"type":"secret_text","name":key,"text":url})
json.dump({"bindings":b},open(tmp+'/cf_bindings.json','w'))
PYEOF
  curl -s -X PATCH "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT/workers/scripts/$worker/settings" \
    -H "Authorization: Bearer $CF_TOKEN" \
    -F "settings=<$TMPDIR_LS/cf_bindings.json;type=application/json" > "$TMPDIR_LS/cf_patch_result.json"
  python3 -c "import json;d=json.load(open('$TMPDIR_LS/cf_patch_result.json'));assert d['success'], d.get('errors')"
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

# ── ComplianceDocs INDIVIDUAL products → waitlist-eucomply via CHECKOUT_URLS_JSON.
#    Each product page reads checkout_urls[productId] from the waitlist worker's /config.
echo ""
echo "== ComplianceDocs individual documents -> waitlist-eucomply =="
DOCS=("dpa|DPA (Art.28 GDP|GDPR Data Processing Agreement (Art. 28)|A complete controller→processor DPA following GDPR Art. 28, with annex structure, sub-processor terms and EU-hosting clauses.|5900|Single copy"
"nis2|NIS2/DORA Vendor |NIS2/DORA Vendor Clause Set|Audit-trail, incident-reporting and subcontractor clauses you can paste into any supplier contract.|4900|Single copy"
"nda|Mutual NDA Clause|Mutual NDA Clause Set|Balanced mutual NDA including the no-client-contact and IP-clarity clauses agencies actually need.|2900|Single copy"
"eaa|EAA Statement T|EAA Accessibility Statement Template|European Accessibility Act conformance statement template with required disclosures.|3900|Single copy"
"reportk|Client Complian|Client Compliance Report Kit|Monthly/quarterly report templates + change-log format that make your maintenance work look audit-ready.|6900|Single copy")
DOC_MAPS=""
for doc in "${DOCS[@]}"; do
  IFS='|' read -r slug name desc price <<< "$doc"
  create_product "$name" "compliancedocs-$slug" "'$desc'" $price "Single copy"
  VID=$(variant_id_for "$name")
  URL=$(checkout_url_for "$VID" $price)
  echo "checkout $slug: $URL"
  DOC_MAPS="${DOC_MAPS}${slug}:${URL}|"
done
echo "waitlist-eucomply config: $(verify_config https://waitlist-eucomply.mahope-eeb.workers.dev/config)"

# ── Ebook + ComplianceDocs bundle share devnotify-metrics via CHECKOUT_URLS_JSON.
#    These products must NEVER fall back to another product's checkout URL, so
#    they read a per-product map (checkout_urls) instead of the shared scalar.
echo ""
echo "== Ebook (\$14.99 one-time) + ComplianceDocs bundle (\$149) -> devnotify-metrics =="
create_product "EU Website Compliance Guide 2026" "eu-compliance-ebook" \
  '"The Practical Guide to EU Website Compliance — GDPR, NIS2, DORA and EAA explained in plain language for people who run websites. PDF, instant download."' \
  1499 "PDF download"
EBOOK_VID=$(variant_id_for "EU Website Compliance Guide 2026")
EBOOK_URL=$(checkout_url_for "$EBOOK_VID" 1499)
echo "checkout: $EBOOK_URL"

create_product "ComplianceDocs Bundle" "compliancedocs-bundle" \
  '"All ComplianceDocs templates in one bundle: DPA, NIS2 vendor clauses, EAA statement, records of processing. Editable, instant download."' \
  14900 "Bundle"
BUNDLE_VID=$(variant_id_for "ComplianceDocs Bundle")
BUNDLE_URL=$(checkout_url_for "$BUNDLE_VID" 14900)
echo "checkout: $BUNDLE_URL"

# Build the per-product map for waitlist-eucomply (5 docs + bundle)
DOC_MAPS_JSON=$(python3 -c "
import json, sys
pairs = sys.argv[1].rstrip('|').split('|')
m = {}
for p in pairs:
    k, v = p.split(':', 1)
    m[k] = v
m['bundle'] = sys.argv[2]
print(json.dumps(m))
" "$DOC_MAPS" "$BUNDLE_URL")
set_worker_secret "waitlist-eucomply" "$DOC_MAPS_JSON" "CHECKOUT_URLS_JSON"
echo "waitlist-eucomply config: $(verify_config https://waitlist-eucomply.mahope-eeb.workers.dev/config)"

MAP_JSON=$(python3 -c 'import json,sys;print(json.dumps({"ebook":sys.argv[1],"bundle":sys.argv[2]}))' "$EBOOK_URL" "$BUNDLE_URL")
set_worker_secret "devnotify-metrics" "$MAP_JSON" "CHECKOUT_URLS_JSON"
echo "worker config: $(verify_config https://devnotify-metrics.mahope-eeb.workers.dev/config)"

echo ""
echo "DONE. All five products should now take payments."
echo "Verify pages:"
echo "  curl -s https://auditedwp.pages.dev/pro/"
echo "  curl -s https://auditedwp.pages.dev/devnotify/"
echo "  curl -s https://auditedwp.pages.dev/quickconvert/"
echo "  curl -s https://devnotify-metrics.mahope-eeb.workers.dev/config   (ebook + bundle map)"
echo "  curl -s https://waitlist-eucomply.mahope-eeb.workers.dev/config"
