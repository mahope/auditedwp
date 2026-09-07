# BUILD — Korteste vej til første betalende kunde

## Status: 26. august 2026

**Primært produkt: Transmute** — Desktop data transformer ($19 one-time)
**Blokering: LS API key i Bitwarden (bw unauthenticated)**

## Korteste vej (når LS kommer)

1. **LS API key** — `bw login` → `bw unlock` → `bw get item lemonsqueezy`
   - Mads: ~2 minutter
   - Når key er hentet: sæt i `~/.hermes/.env` som `LEMON_SQUEEZY_API_KEY`

2. **Opret LS produkter** (via API, 1 script)
   - Transmute Desktop: $19 one-time, 3 aktiveringer
   - Transmute CLI: Free (ingen betaling nødvendig)
   - Afventer: LS key før script kan køres

3. **LS checkout i desktop app** — flip licensgate
   - App'en bruger `checkout_url` fra LS → åbner browser til betaling
   - Efter betaling: LS Webhook → Worker validerer → license key genereres
   - Alt klar i koden, mangler kun LS prod credentials

4. **Tag imod penge** — 10 min efter LS key

### Alternativ (uden LS key): Mads manuel opsætning

Hvis Mads foretrækker manuelt:
- Følg LS-MANUAL.md (20 min, én gang)
- Brug dashboard på app.lemonsqueezy.com
- Opret 6 produkter jf. manualen
- Når produkterne er oprettet: sig til, så 10 min til checkout

## Produkter der er klar til betaling

| Produkt | Pris | Klar? | Blokering |
|---------|------|-------|-----------|
| Transmute Desktop | $19 one-time | App: ✅ / Checkout: ⏳ | LS key |
| EUComply Pro | $79/år | Site: ✅ / Checkout: ⏳ | LS key |
| DeskUptime | Gratis/Pro | Site: ✅ / Checkout: ⏳ | LS key |

## Hvad jeg bygger i ventetid

Indtil LS key er tilgængelig:

| Opgave | Værdi |
|--------|-------|
| **SEO-content/metadata** på transmute guides | Flere besøgende → flere downloads → flere køb når LS kommer |
| **Kvalitetsfixes** (QuickFormat udfasning, broken links, metadata) | Rent site, bedre konvertering |
| **Færdiggør desktop builds** (Linux .deb, Apple notarization) | Bredere platformssupport |
| **Forbedr site/transmute flow** | Større sandsynlighed for download/køb |

Måling: ingen analytics pt (Cloudflare beacon.js er minimal). Første salg er signalet.