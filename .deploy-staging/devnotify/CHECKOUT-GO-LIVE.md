# DevNotify — Checkout Go-Live Runbook

Så snart Lemon Squeezy API-nøglen ligger i Bitwarden, er dette den korteste
vej fra nøgle til første betalende kunde. Estimeret tid: under 1 time.

## 1. Opret produkt i Lemon Squeezy via API

```bash
export LS_API_KEY=<nøglen fra Bitwarden>

# 1a. Store-id
curl https://api.lemonsqueezy.com/v1/v1/stores \
  -H "Authorization: Bearer $LS_API_KEY"

# 1b. Produkt (variant = $19 lifetime license, USD)
curl -X POST https://api.lemonsqueezy.com/v1/v1/products \
  -H "Authorization: Bearer $LS_API_KEY" \
  -H "Content-Type: application/vnd.api+json" \
  -d '{
    "data": {
      "type": "products",
      "attributes": {
        "name": "DevNotify — Lifetime License",
        "slug": "devnotify",
        "description": "GitHub notifications in your macOS menu bar. Unread count at a glance, one click to any PR or issue. 100% local — your token stays on your Mac.",
        "price": 1900,
        "price_currency": "USD",
        "redirect_url": "https://auditedwp.pages.dev/devnotify/download/",
        "test_mode": true
      },
      "relationships": { "store": { "data": { "type": "stores", "id": "<STORE_ID>" } } }
    }
  }'
```

- `test_mode: true` først → gennemfør ét testkøb → sæt til `false`.
- Prisen er i cents: 1900 = $19.

## 2. Hent checkout-URL'en

```bash
curl -X POST https://api.lemonsqueezy.com/v1/v1/checkouts \
  -H "Authorization: Bearer $LS_API_KEY" \
  -H "Content-Type: application/vnd.api+json" \
  -d '{ "data": { "type": "checkouts",
        "attributes": { "custom_price": false, "product_options": { "enabled_variants": [<VARIANT_ID>] } },
        "relationships": { "store": {...}, "variant": { "data": { "type": "variants", "id": "<VARIANT_ID>" } } } } }'
```

Gem `url` og `identifier` fra svaret.

## 3. Indsæt checkout på sitet (2 filer)

**`index.html`** (forsiden, sektionen `<section class="buy" id="buy">`):

```js
const LS_CHECKOUT='https://<store>.lemonsqueezy.com/checkout/buy/<uuid>?embed=1';
// buyBtn.onclick -> window.open(LS_CHECKOUT) eller LS.overlay
```

Erstat notify-form-blokken (markeret med kommentaren
`// When checkout goes live, replace this block`) med overlay-køb:
Lemon Squeezy's overlay-script:

```html
<script src="https://assets.lemonsqueezy.com/lemon.js" defer></script>
<a class="btn btn-primary" href="LS_CHECKOUT_URL">Buy license — $19</a>
```

**`download/index.html`:** ret "Get a license"-linket fra `/devnotify/#buy`
til at pege direkte på checkout.

App'en validerer allerede nøgler mod `api.lemonsqueezy.com/v1/licenses/validate`
(devnotify/src-tauri/src/lib.rs) — ingen kodeændring nødvendig der.

## 4. Test-køb (test_mode)

1. Gennemfør købet med testkortet LS viser.
2. Kopiér licensnøglen fra kvitteringssiden.
3. Indtast nøglen i appen → bekræft at trial-banneret forsvinder.
4. Verificér at nøglen kan aktiveres igen på en anden maskine (aktiveringsgrænse).

## 5. Gå live

1. Sæt produktets `test_mode: false` via PATCH.
2. Erstat checkout-URL med live-versionen i begge HTML-filer.
3. Deploy: `./deploy.sh .deploy-staging`
4. Verificér LIVE indhold (ikke kun HTTP 200):
   ```bash
   curl -s https://auditedwp.pages.dev/devnotify/ | grep -o 'lemonsqueezy[^"]*' | head -3
   ```
5. Opdater STATUS.md: "Checkout live".

## 6. Første rigtige salg

Købsrejsen er allerede bygget: guides → forsiden → $19 → checkout → licens-
mail → app-validering. Det eneste der mangler er trafik — se LAUNCH.md for
teksterne der venter på Mads' godkendelse.
