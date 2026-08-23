#!/bin/sh
# Deploy site to Cloudflare Pages
# Requires: wrangler login (done once)
# Usage: sh deploy.sh

set -e

echo "=== Deploying AuditedWP to Cloudflare Pages ==="
echo "Project: auditedwp"
echo "Live URL: https://auditedwp.pages.dev"

cd "$(dirname "$0")"

wrangler pages deploy . --project-name=auditedwp

echo ""
echo "=== Done ==="
echo "Live: https://auditedwp.pages.dev"
