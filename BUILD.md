# BUILD — Korteste vej til $1 (opdateret 24. august 2026)

## Produkt 1: EUComply Pro ($79/år)
**Status:** Bygget, live, universel. Ventende: LS API-nøgle (forventet i Bitwarden 24/8).

### Præcis plan: 10 minutter fra LS-nøgle til checkout

```bash
# 1. Hent LS API-nøgle fra Bitwarden
#    Log ind på bitwarden.mahope.dk / vault.bitwarden.com
#    Nøglen hedder "Lemon Squeezy API Key"

# 2. Opret produkt via LS API
curl -X POST https://api.lemonsqueezy.com/v1/products \
  -H "Authorization: Bearer $LS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "type": "products",
      "attributes": {
        "name": "EUComply Pro",
        "description": "Daily EU compliance monitoring for any website. Automated GDPR, NIS2, DORA, and EAA checks with dashboard, PDF reports, and email alerts.",
        "price": 79,
        "interval": "year"
      }
    }
  }'

# 3. Opret en variant (price) på produktet
#    Brug product_id fra svaret ovenfor
curl -X POST https://api.lemonsqueezy.com/v1/variants \
  -H "Authorization: Bearer $LS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "type": "variants",
      "attributes": {
        "name": "Standard",
        "price": 7900  # $79 i cent
      },
      "relationships": {
        "product": {
          "data": { "type": "products", "id": "<product_id>" }
        }
      }
    }
  }'

# 4. Opret et checkout-link
curl -X POST https://api.lemonsqueezy.com/v1/checkouts \
  -H "Authorization: Bearer $LS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "type": "checkouts",
      "attributes": {
        "product_options": {
          "name": "EUComply Pro",
          "description": "Automated EU compliance monitoring — daily scans, PDF reports, templates"
        },
        "checkout_data": {
          "custom": {
            "source": "eucomply-pro-page"
          }
        }
      },
      "relationships": {
        "variant": {
          "data": { "type": "variants", "id": "<variant_id>" }
        }
      }
    }
  }'

# 5. Indsæt checkout-URL i kodebasen
#    site/pro/index.html → CHECKOUT_URL = '<url>' (linje 294)
#    Deploy: ./deploy.sh site

# 6. Test med LS sandbox (1 cent test)
#    LS har sandbox-mode: opret en checkout med "test" i data og brug
#    testkort 4242 4242 4242 4242 for at verificere flowet

# 7. Skift til live mode
#    Opret checkout i live-mode. Første rigtige betaling mulig samme dag.
```

**Checklist til når nøglen ligger klar:**
- [ ] Opret produkt i LS
- [ ] Opret variant ($79/yr)
- [ ] Opret checkout link
- [ ] Sæt CHECKOUT_URL i `site/pro/index.html`
- [ ] Test med LS sandbox
- [ ] Deploy
- [ ] Første betaling

### Hvad ER allerede klar (kan testes nu)
- ✅ Pro-side med pris, features, sammenligning — live på auditedwp.pages.dev/pro/
- ✅ CHECKOUT_URL variabel i HTML (linje 294) — klar til at indsætte URL
- ✅ Buy-knap med JS redirect til checkout — klar
- ✅ Garanti ("30-day money-back") — tilføjet 24/8
- ✅ Thank-you side — klar på /pro/thank-you/
- ✅ Daily monitoring engine — bygget og kører
- ✅ 21 blogindlæg til SEO-trafik
- ✅ Domæne eucomply.dev — valgt, forhåndsgodkendt til køb

---

## Produkt 2: "EU Website Compliance Guide 2026" (Amazon KDP ebook)
**Status:** Skrevet, klar til upload. Kræver Mads uploader manuelt (10 min).

### Upload-vejledning (til Mads)
1. Gå til kdp.amazon.com
2. Log ind med Mads' konto
3. Vælg "Create a New Title" → Ebook
4. Upload filen: `eu-website-compliance-guide-2026.docx` (fra `/book/`)
5. Upload omslag: (skal designes — se nedenfor)
6. Sæt pris: $9.99 (KDP Select, 70% royalty)
7. Sæt beskrivelse og 7 søgeord
8. Udgiv

---

## Næste trin (prioriteret)

| # | Hvad | Hvornår | Blokering |
|---|------|---------|-----------|
| 1 | Domæne: eucomply.dev → køb og sæt foran pages.dev | Ventende | "Sig til" |
| 2 | LS-nøgle: opret produkt → checkout → $1 | Samme dag nøglen ligger i Bitwarden | LS API-nøgle |
| 3 | KDP-upload: Mads uploader bogen | Når omslag er på plads | Omslag + Mads' handling |
| 4 | Blog: fortsæt 1/uge | Løbende | Ingen |
| 5 | Chrome extension: opdater LS-licens, udgiv | Efter LS-nøgle | LS-nøgle + Mads' Chrome Web Store-konto |

---

## Budget

| Post | Status | Beløb |
|------|--------|-------|
| Brugt | | **0 kr** |
| Domæne: eucomply.dev | Forhåndsgodkendt, ~$12 | ~90 DKK |
| **Tilbage** | | **~910 kr af 1.000 kr** |