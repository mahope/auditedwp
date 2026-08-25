# BUILD.md — DeskUptime: vejen til første betaling

## Status: ✅ Klar til betaling — venter på LS API key

Alt nedenfor er **forberedt og klar**. Når LS key ligger i Bitwarden, tager hele opsætningen ~10 min.

---

## 1. Hent LS API key

```bash
bw login        # (første gang — ellers `bw unlock`)
bw sync
bw get item "Lemon Squeezy" | jq -r '.fields[] | select(.name=="api_key") | .value'
# → sæt som LS_API_KEY
```

## 2. Opret produkt via LS API

```bash
# Opret produkt "DeskUptime Pro"
curl -s -X POST https://api.lemonsqueezy.com/v1/products \
  -H "Authorization: Bearer $LS_API_KEY" \
  -H "Content-Type: application/vnd.api+json" \
  -d '{
    "data": {
      "type": "products",
      "attributes": {
        "name": "DeskUptime Pro",
        "description": "Desktop website monitor: uptime, SSL, and content-change checks. Runs on your machine, $19 one-time, no subscription.",
        "status": "published"
      }
    }
  }'
```

Gem product_id fra svaret.

## 3. Opret variant (pris)

```bash
curl -s -X POST https://api.lemonsqueezy.com/v1/variants \
  -H "Authorization: Bearer $LS_API_KEY" \
  -H "Content-Type: application/vnd.api+json" \
  -d '{
    "data": {
      "type": "variants",
      "attributes": {
        "name": "Standard License",
        "price": 1900,
        "currency": "USD",
        "status": "published",
        "description": "3 activations per license. All v1.x updates included.",
        "is_lifetime": true
      }
    },
    "relationships": {
      "product": {
        "data": { "type": "products", "id": "<product_id>" }
      }
    }
  }'
```

Gem variant_id.

## 4. Opret checkout-link

```bash
curl -s -X POST https://api.lemonsqueezy.com/v1/checkouts \
  -H "Authorization: Bearer $LS_API_KEY" \
  -H "Content-Type: application/vnd.api+json" \
  -d '{
    "data": {
      "type": "checkouts",
      "attributes": {
        "product_options": {
          "enabled_variants": ["<variant_id>"],
          "redirect_url": "https://deskuptime.com/thanks/"
        }
      },
      "relationships": {
        "store": {
          "data": { "type": "stores", "id": "<store_id>" }
        },
        "variant": {
          "data": { "type": "variants", "id": "<variant_id>" }
        }
      }
    }
  }'
```

Gem `data.attributes.url` — dette er checkout-linket.

## 5. Sæt checkout URL i Config Worker

Worker (`waitlist-eucomply.mahope-eeb.workers.dev`) checker `CHECKOUT_URLS_JSON` environment-variabel.

```bash
# Opdater Worker-miljøvariablen
wrangler secret put CHECKOUT_URLS_JSON
# Indhold: {"deskuptime": "<checkout_url>", "deskuptime-cli": "<maybe_different_variant_url>"}
```

Når Worker returnerer `"checkout_urls":{"deskuptime": "<url>"}`, **erstatter DeskUptime-sidens JavaScript automatisk** "Notify Me"-knappen med "Buy Now — $19" (se `site/deskuptime/index.html` linje ~369-381).

## 6. Opdater JSON-LD

I `site/deskuptime/index.html`, skift:
- `"availability": "https://schema.org/PreOrder"` → `"https://schema.org/InStock"`
- Dato i meta: tilføj `"priceValidUntil"` og `"dateModified"`

## 7. Verificér

```bash
# Tjek at checkout URL returneres fra config
curl -s https://waitlist-eucomply.mahope-eeb.workers.dev/config | jq .checkout_urls.deskuptime

# Verificér at siden nu viser en köbsknap
curl -s https://auditedwp.pages.dev/deskuptime/ | grep -o 'Buy Now'
```

## 8. Opret "Thanks/after-purchase"-side

`site/deskuptime/thanks/index.html`:
- Download-links for desktop app (macOS .dmg, Windows .exe)
- CLI install command
- License key activation instructions
- Support email

---

## Deployment-ordre (når key kommer)

1. Opret produkt via LS API (trin 2-4) — ~5 min
2. Sæt CHECKOUT_URLS_JSON i Worker — ~1 min
3. Opdater JSON-LD og deploy — ~3 min
4. Verificér at Buy Now vises — ~1 min
5. Køb deskuptime.com domæne via Cloudflare Registrar
6. Sæt CNAME på domænet → auditedwp.pages.dev
7. Opdater canonical URL'er til deskuptime.com

**Total: ~10 min til åbnet betaling.**