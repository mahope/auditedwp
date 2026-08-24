#!/usr/bin/env bash
# DevNotify — flip the landing page from "notify me" to a live LS checkout.
# Usage:  ./scripts/ls-flip.sh "https://devnotify.lemonsqueezy.com/buy/xxxx"
# Idempotent: safe to run twice. Run ./deploy.sh afterwards.
set -euo pipefail
URL="${1:?Usage: ls-flip.sh <checkout-url>}"
cd "$(dirname "$0")/../devnotify-site"

if grep -q 'id="buy-link"' index.html; then
  echo "Already flipped — updating URL only."
  python3 - "$URL" <<'EOF'
import re, sys
url = sys.argv[1]
s = open('index.html').read()
s = re.sub(r'(id="buy-link"\s+href=")[^"]*(")', r'\g<1>' + url + r'\g<2>', s)
open('index.html','w').write(s)
EOF
else
  python3 - "$URL" <<'EOF'
import re, sys
url = sys.argv[1]
s = open('index.html').read()
old_btn = '<button class="btn btn-primary" id="buy-btn" type="button" aria-label="Get notified when DevNotify checkout opens">Buy license — get notified</button>'
new_btn = f'<a class="btn btn-primary" id="buy-link" href="{url}" target="_blank" rel="noopener">Buy license — $19</a>'
assert old_btn in s, "buy button markup not found"
s = s.replace(old_btn, new_btn)

old_form = '<form id="notify-form" style="display:none;'
new_form = '<form id="notify-form" style="display:none;visibility:hidden;'
assert old_form in s, "notify form markup not found"
s = s.replace(old_form, new_form)
open('index.html','w').write(s)
print("flipped OK")
EOF
fi

echo "--- verify ---"
grep -n 'buy-link\|notify-form' index.html | head -5
echo "OK. Now: ./deploy.sh devnotify-site && curl -s https://auditedwp.pages.dev/devnotify/ | grep buy-link"
