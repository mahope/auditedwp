# BUILD — DevNotify: korteste vej til første betalende kunde

## Hvor vi står (iteration 122)

- Produktet er bygget og udgivet: Tauri v2 macOS menu bar app, v0.2.0,
  Apple Silicon + Intel DMG'er, checksum-verificeret, downloadbart fra sitet.
- Landingsside sælger allerede: hvad, hvem, $19, købssektion. 5 SEO-sider live.
- **Den eneste manglende led:** checkout-knappen viser en notify-me-formular
  i stedet for en betalingslink.

## Korteste vej til første betaling

1. **LS API-nøgle** (Bitwarden, ventes 24/8) → opret produkt via API:
   - Navn "DevNotify License", $19 USD one-time.
   - Test-køb gennemført → test-tilstand slås fra.
2. Erstat notify-formularen i `site/devnotify/index.html` med LS checkout-URL:
   - Buy-knap = direkte link. Fjern formularen og dens JS.
   - Samme på alle 5 sider hvor der henvises til #buy.
3. Remote licensvalidering i appen mod LS license API (TODO i lib.rs).
4. Verificér hele købsrejsen som fremmed: landing → buy → checkout →
   licensnøgle på mail → aktivering i app.

## Efter første betaling er mulig — trafik (prioriteret)

1. Flere sammenligningssider (DevNotify vs Octobox/Notifier for GitHub),
   long-tail søgninger om GitHub notifications.
2. Produkttekster klar til steder Mads kan godkende: Product Hunt,
   Hacker News Show HN, relevante subreddits — skrevet færdigt, venter på ja.
3. Sitemap/robots vedligeholdes ved hver ny side.

## Ikke blokeret på andet

Intet. Alt andet arbejde (flere sider, forbedringer) kan fortsætte mens
vi venter på nøglen.
