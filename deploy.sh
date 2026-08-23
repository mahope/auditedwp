#!/bin/sh
# Deploy AuditedWP site til GitHub Pages.
# Brug: sh deploy.sh
# Sitet er live på https://mahope.github.io/auditedwp/
# Efter push tager GitHub Pages ~30s at bygge/deploye.
cd "$(dirname "$0")"
git add -A
git commit -m "site update $(date +%Y-%m-%d_%H:%M)"
git push origin main
echo "---"
echo "Deployet. Tjek https://github.com/mahope/auditedwp/actions for build-status."
echo "Live URL: https://mahope.github.io/auditedwp/"