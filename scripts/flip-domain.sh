#!/bin/bash
# Flips canonical/OG/sitemap between eucomplypro.com and auditedwp.pages.dev.
# Usage: ./scripts/flip-domain.sh pagesdev   (while CNAME is pending — SEO-safe)
#        ./scripts/flip-domain.sh custom     (after CNAME is live)
set -e
cd "$(dirname "$0")/../site"
MODE="$1"
case "$MODE" in
  pagesdev) FROM="https://eucomplypro.com"; TO="https://auditedwp.pages.dev" ;;
  custom)   FROM="https://auditedwp.pages.dev"; TO="https://eucomplypro.com" ;;
  *) echo "Usage: $0 pagesdev|custom"; exit 1 ;;
esac
# Only touch SEO signals: canonical, og:url, sitemap locs. Leave visible content alone.
grep -rl "$FROM" . --include='*.html' --include='*.xml' | while read -r f; do
  sed -i '' "s|rel=\"canonical\" href=\"$FROM|rel=\"canonical\" href=\"$TO|g; s|property=\"og:url\" content=\"$FROM|property=\"og:url\" content=\"$TO|g; s|<loc>$FROM|<loc>$TO|g" "$f"
done
echo "Done: SEO URLs flipped to $TO"
grep -c "canonical\" href=\"$TO" index.html
