#!/bin/sh
# Deploy AuditedWP til Cloudflare Pages (gratis *.pages.dev).
# Forudsætning: npx wrangler er logget ind (kør én gang: npx wrangler login)
# Brug: sh deploy.sh   → https://auditedwp.pages.dev
cd "$(dirname "$0")"
npx wrangler pages deploy . --project-name=auditedwp --branch=main
