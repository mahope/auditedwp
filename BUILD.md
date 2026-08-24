# BUILD — Korteste vej til første betalende kunde (rev. 24. august 2026)

## Position

**EUComply Pro ($79/år recurring).** Scanner, worker, Pro-side, CLI, plugin, 27 blogposts, 6+ comparison pages, runtime checkout-detection — alt bygget og live. Venter på LS API-nøgle.

**DevNotify ($19 one-time).** App, site, 52 guides, flip-script klar. Venter på LS.

## Når LS API-nøgle er tilgængelig

```bash
# EUComply Pro — PRIORITET 1 (recurring > one-time)
# Sæt checkout URL secret — ingen deploy nødvendig
wrangler secret put CHECKOUT_URL --name eucomply-scan
# Value: https://eucomply.lemonsqueezy.com/checkout/buy/XXXX

# Verificer
curl -s https://eucomply-scan.mahope-eeb.workers.dev/config | jq .checkoutUrl
# Forventet: "https://eucomply.lemonsqueezy.com/checkout/buy/XXXX"

# Bekræft at Pro-siden skjuler waitlist
curl -s https://auditedwp.pages.dev/pro/ | grep -c 'Join the waitlist'
# Forventet: 0

# Sandbox-testkøb (kort 4242 4242 4242 4242) → verificer licensflow
# Første rigtige kunde → byg videre på dét der virker

# DevNotify — PRIORITET 2
# Kør flip-script (kræver deploy)
./scripts/ls-flip.sh "https://devnotify.lemonsqueezy.com/checkout/buy/XXXX"
./deploy.sh site
```

## Flippet er forberedt

- `scripts/eucomply-flip.sh` — guide til at sætte secret (idempotent)
- `scripts/ls-flip.sh` — DevNotify flip (kræver deploy)
- Pro-siden (site/pro/index.html) — runtime checkout-detektion via `/config` endpoint:
  - Opdaterer `buy-pro-btn` href til checkout URL
  - Skjuler "⏳ Checkout opens on Lemon Squeezy" noten
  - Skjuler `#waitlist` sektionen
  - Alt uden deploy — kun wrangler secret put

## Hvis LS key ikke kommer

Pivot til produkt med indbygget betaling. Chrome Web Store mest sandsynlig (Mads har dev-konto, manuel publish mulig). Alternativ: VS Code marketplace eller helt anden forretningsmodel (affiliate, digitalt produkt på marketplace).